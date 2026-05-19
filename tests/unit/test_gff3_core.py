import io
import unittest
from unittest import mock

from gff3tool.lib.gff3 import gff3


class TestGff3Core(unittest.TestCase):
    def test_complement_and_translate(self):
        self.assertEqual(gff3.complement("TAGCtagc"), "ATCGATCG")
        self.assertEqual(gff3.translate("atgtttNNNtaa"), "MF*")

    def test_fasta_file_to_dict_from_file_object(self):
        fasta = io.StringIO(">seq1 desc\natgc\n>seq2\nNNaa\n")
        fasta.name = "in-memory.fa"

        result, count = gff3.fasta_file_to_dict(fasta)

        self.assertEqual(count, 2)
        self.assertIn("seq1", result)
        self.assertEqual(result["seq1"]["seq"], "ATGC")
        self.assertEqual(result["seq2"]["seq"], "NNAA")

    def test_fasta_dict_to_file_writes_wrapped_lines(self):
        out = io.StringIO()
        fasta_dict = {
            "seq1": {"header": ">seq1", "seq": "ATGCAA"},
        }

        gff3.fasta_dict_to_file(fasta_dict, out, line_char_limit=3)

        self.assertEqual(out.getvalue(), ">seq1\nATG\nCAA\n")

    def test_collect_descendants_and_roots(self):
        parser = gff3.Gff3()
        root = {"attributes": {"ID": "gene1"}, "children": [], "parents": []}
        child = {"attributes": {"ID": "tx1", "Parent": ["gene1"]}, "children": [], "parents": [[root]]}
        grandchild = {"attributes": {"ID": "cds1", "Parent": ["tx1"]}, "children": [], "parents": [[child]]}
        child["children"] = [grandchild]
        root["children"] = [child]

        descendants = parser.collect_descendants(root)
        roots = parser.collect_roots(grandchild)

        self.assertEqual(descendants, [child, grandchild])
        self.assertEqual(roots, [root])

    def test_add_line_error_records_message(self):
        parser = gff3.Gff3()
        line = {"line_index": 0, "line_raw": "chr1\tsrc\tgene"}
        err = {"error_type": "TEST", "message": "problem"}

        parser.add_line_error(line, err)

        self.assertIn("line_errors", line)
        self.assertEqual(line["line_errors"][0], err)

    def test_check_unresolved_parents_resolves_known_feature_ids(self):
        parser = gff3.Gff3()
        parent = {"line_index": 0, "children": []}
        child = {"line_index": 1, "parents": [], "children": []}
        parser.features = {"gene1": [parent]}
        parser.unresolved_parents = {"gene1": [child], "missing": [child]}

        parser.check_unresolved_parents()

        self.assertEqual(child["parents"], [[parent]])
        self.assertIn(child, parent["children"])

    def test_check_parent_boundary_detects_bounds_violation(self):
        parser = gff3.Gff3()
        parent = {
            "start": 10,
            "end": 20,
            "seqid": "chr1",
            "attributes": {"ID": "gene1"},
        }
        child = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "child",
            "seqid": "chr1",
            "type": "mRNA",
            "start": 1,
            "end": 30,
            "attributes": {"ID": "tx1", "Parent": ["gene1"]},
            "parents": [[parent]],
            "line_errors": [],
        }
        parser.lines = [child]

        ok = parser.check_parent_boundary()

        self.assertTrue(ok)
        self.assertTrue(any(e.get("eCode") == "Ema0003" for e in child["line_errors"]))

    def test_check_reference_external_fasta_reports_oob_and_n_count(self):
        parser = gff3.Gff3()
        line = {
            "line_type": "feature",
            "directive": "",
            "line_index": 0,
            "line_raw": "chr1\tsrc\tCDS\t1\t6",
            "seqid": "chr1",
            "start": 1,
            "end": 6,
            "type": "CDS",
            "line_errors": [],
            "parents": [],
            "attributes": {"ID": "cds1"},
        }
        parser.lines = [line]
        parser.fasta_external = {
            "chr1": {"seq": "NNNN"},
        }

        errors = parser.check_reference(fasta_external=True, allowed_num_of_n=0)

        self.assertIn(0, errors)
        ecodes = {e["eCode"] for e in line["line_errors"]}
        self.assertIn("Esf0011", ecodes)
        self.assertIn("Esf0012", ecodes)

    def test_parse_sequence_region_invalid_end_keeps_start_value(self):
        content = "##gff-version 3\n##sequence-region chr1 1 bad\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        line = parser.lines[1]
        self.assertEqual(line["directive"], "##sequence-region")
        self.assertEqual(line["start"], 1)
        self.assertEqual(line["end"], "bad")
        self.assertTrue(any(e["eCode"] == "Esf0017" for e in line["line_errors"]))

    def test_descendants_and_ancestors_graph_helpers(self):
        parser = gff3.Gff3()
        root = {"line_index": 0, "children": [], "parents": [], "line_type": "feature"}
        child = {"line_index": 1, "children": [], "parents": [[root]], "line_type": "feature"}
        grandchild = {"line_index": 2, "children": [], "parents": [[child]], "line_type": "feature"}
        root["children"] = [child]
        child["children"] = [grandchild]
        parser.lines = [root, child, grandchild]

        self.assertEqual([ld["line_index"] for ld in parser.descendants(root)], [1, 2])
        self.assertEqual([ld["line_index"] for ld in parser.ancestors(grandchild)], [1, 0])

    def test_adopt_moves_children_to_new_parent(self):
        parser = gff3.Gff3()
        old_parent = {
            "line_index": 0,
            "attributes": {"ID": "old"},
            "children": [],
            "parents": [],
            "line_type": "feature",
        }
        new_parent = {
            "line_index": 1,
            "attributes": {"ID": "new"},
            "children": [],
            "parents": [],
            "line_type": "feature",
        }
        child = {
            "line_index": 2,
            "attributes": {"ID": "c1", "Parent": ["old"]},
            "children": [],
            "parents": [[old_parent]],
            "line_type": "feature",
        }
        old_parent["children"] = [child]
        parser.lines = [old_parent, new_parent, child]
        parser.features = {"old": [old_parent], "new": [new_parent], "c1": [child]}

        moved = parser.adopt("old", "new")

        self.assertEqual([c["line_index"] for c in moved], [2])
        self.assertEqual(old_parent["children"], [])
        self.assertEqual(new_parent["children"], [child])
        self.assertEqual(child["attributes"]["Parent"], ["new"])

    def test_remove_marks_roots_and_descendants(self):
        parser = gff3.Gff3()
        root = {
            "line_index": 0,
            "children": [],
            "parents": [],
            "line_type": "feature",
            "line_status": "normal",
            "attributes": {"ID": "gene1"},
        }
        child = {
            "line_index": 1,
            "children": [],
            "parents": [[root]],
            "line_type": "feature",
            "line_status": "normal",
            "attributes": {"ID": "tx1"},
        }
        root["children"] = [child]
        parser.lines = [root, child]

        parser.remove(child)

        self.assertEqual(root["line_status"], "removed")
        self.assertEqual(child["line_status"], "removed")

    def test_type_tree_builds_parent_child_types(self):
        parser = gff3.Gff3()
        root = {
            "line_index": 0,
            "line_type": "feature",
            "type": "gene",
            "parents": [],
            "children": [],
        }
        child = {
            "line_index": 1,
            "line_type": "feature",
            "type": "mRNA",
            "parents": [[root]],
            "children": [],
        }
        root["children"] = [child]
        parser.lines = [root, child]

        tree = parser.type_tree()

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0].value, "gene")
        self.assertEqual(sorted(c.value for c in tree[0].children), ["mRNA"])

    def test_sequence_supports_fasta_dict_reference_shape(self):
        parser = gff3.Gff3()
        parser.lines = [
            {
                "line_index": 0,
                "line_type": "feature",
                "seqid": "chr1",
                "start": 2,
                "end": 5,
                "strand": "+",
            }
        ]

        seq = parser.sequence(0, reference={"chr1": {"seq": "AACCGGTT"}})

        self.assertEqual(seq, "ACCG")

    def test_sequence_keeps_backward_compat_for_plain_string_reference(self):
        parser = gff3.Gff3()
        parser.lines = [
            {
                "line_index": 0,
                "line_type": "feature",
                "seqid": "chr1",
                "start": 1,
                "end": 4,
                "strand": "-",
            }
        ]

        seq = parser.sequence(0, reference={"chr1": "AACCGGTT"})

        self.assertEqual(seq, "GGTT")


if __name__ == "__main__":
    unittest.main()