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

    def test_parse_duplicate_gff_version_reports_first_line_requirement_error(self):
        content = "##gff-version 3\n##gff-version 3\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        second = parser.lines[1]
        self.assertEqual(second["directive"], "##gff-version")
        self.assertTrue(any(e["eCode"] == "Esf0014" for e in second["line_errors"]))

    def test_parse_unknown_directive_is_recorded(self):
        content = "##gff-version 3\n##unknown-directive value\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        unknown = parser.lines[1]
        self.assertEqual(unknown["directive"], "##unknown-directive")
        self.assertTrue(any(e["eCode"] == "Esf0021" for e in unknown["line_errors"]))

    def test_parse_reports_missing_gff_version_on_first_line(self):
        content = "chr1\tsrc\tgene\t1\t10\t.\t+\t.\tID=gene1\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        first = parser.lines[0]
        self.assertTrue(any(e["eCode"] == "Esf0014" for e in first["line_errors"]))

    def test_parse_reports_non_integer_gff_version(self):
        content = "##gff-version three\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        line = parser.lines[0]
        self.assertEqual(line["directive"], "##gff-version")
        self.assertTrue(any(e["eCode"] == "Esf0020" for e in line["line_errors"]))

    def test_parse_reports_leading_whitespace_in_line(self):
        content = "##gff-version 3\n chr1\tsrc\tgene\t1\t10\t.\t+\t.\tID=gene1\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        line = parser.lines[1]
        self.assertTrue(any(e["eCode"] == "Esf0013" for e in line["line_errors"]))

    def test_parse_reports_duplicate_non_adjacent_id(self):
        content = (
            "##gff-version 3\n"
            "chr1\tsrc\tgene\t1\t10\t.\t+\t.\tID=gene1\n"
            "# break adjacency\n"
            "chr1\tsrc\tgene\t20\t30\t.\t+\t.\tID=gene1\n"
        )
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        second_gene = parser.lines[3]
        self.assertTrue(any(e["eCode"] == "Emr0003" for e in second_gene["line_errors"]))

    def test_parse_reports_invalid_target_end_and_is_circular_value(self):
        content = (
            "##gff-version 3\n"
            "chr1\tsrc\tmatch\t1\t9\t.\t+\t.\tID=m1;Target=t1 1 x +;Is_circular=false\n"
        )
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        line = parser.lines[1]
        ecodes = {e["eCode"] for e in line["line_errors"]}
        self.assertIn("Esf0038", ecodes)
        self.assertIn("Esf0040", ecodes)

    def test_parse_reports_unknown_reserved_uppercase_attribute(self):
        content = "##gff-version 3\nchr1\tsrc\tgene\t1\t10\t.\t+\t.\tID=gene1;Foo=bar\n"
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        line = parser.lines[1]
        self.assertTrue(any(e["eCode"] == "Esf0041" for e in line["line_errors"]))

    def test_check_phase_flags_inconsistent_cds_strands(self):
        parser = gff3.Gff3()
        parser.lines = [
            {
                "line_type": "feature",
                "type": "CDS",
                "line_index": 0,
                "line_raw": "cds1",
                "attributes": {"Parent": ["tx1"]},
                "strand": "+",
                "start": 1,
                "end": 6,
                "phase": 0,
                "line_errors": [],
            },
            {
                "line_type": "feature",
                "type": "CDS",
                "line_index": 1,
                "line_raw": "cds2",
                "attributes": {"Parent": ["tx1"]},
                "strand": "-",
                "start": 10,
                "end": 15,
                "phase": 0,
                "line_errors": [],
            },
        ]

        parser.check_phase(initial_phase=False)

        self.assertTrue(any(e["eCode"] == "Ema0007" for e in parser.lines[0]["line_errors"]))
        self.assertTrue(any(e["eCode"] == "Ema0007" for e in parser.lines[1]["line_errors"]))

    def test_check_phase_initial_phase_requires_zero_for_single_cds(self):
        parser = gff3.Gff3()
        parser.lines = [
            {
                "line_type": "feature",
                "type": "CDS",
                "line_index": 0,
                "line_raw": "cds1",
                "attributes": {"Parent": ["tx1"]},
                "strand": "+",
                "start": 1,
                "end": 6,
                "phase": 2,
                "line_errors": [],
            }
        ]

        parser.check_phase(initial_phase=True)

        self.assertTrue(any(e["eCode"] == "Ema0006" for e in parser.lines[0]["line_errors"]))

    def test_check_reference_sequence_region_reports_missing_seqid(self):
        parser = gff3.Gff3()
        parser.lines = [
            {
                "line_type": "directive",
                "directive": "##sequence-region",
                "seqid": "chr1",
                "start": 1,
                "end": 10,
                "line_errors": [],
            },
            {
                "line_type": "feature",
                "line_index": 1,
                "line_raw": "chr2\tsrc\tCDS",
                "directive": "",
                "seqid": "chr2",
                "start": 1,
                "end": 5,
                "type": "CDS",
                "line_errors": [],
            },
        ]

        errors = parser.check_reference(sequence_region=True, check_n=False)

        self.assertIn(1, errors)
        self.assertTrue(any(e["eCode"] == "Esf0004" for e in parser.lines[1]["line_errors"]))

    def test_check_reference_embedded_fasta_reports_bounds_and_n_count(self):
        parser = gff3.Gff3()
        parser.fasta_embedded = {"chr1": {"seq": "AANN"}}
        parser.lines = [
            {
                "line_type": "feature",
                "line_index": 0,
                "line_raw": "chr1\tsrc\tCDS",
                "directive": "",
                "seqid": "chr1",
                "start": 1,
                "end": 6,
                "type": "CDS",
                "line_errors": [],
            }
        ]

        errors = parser.check_reference(fasta_embedded=True, allowed_num_of_n=0)

        self.assertIn(0, errors)
        ecodes = {e["eCode"] for e in parser.lines[0]["line_errors"]}
        self.assertIn("Esf0008", ecodes)
        self.assertIn("Esf0009", ecodes)

    def test_check_parent_boundary_fails_when_required_feature_id_missing(self):
        parser = gff3.Gff3()
        parser.lines = [
            {
                "line_index": 0,
                "line_raw": "chr1\tsrc\tgene\t1\t10\t.\t+\t.\t.",
                "line_type": "feature",
                "type": "gene",
                "attributes": {},
                "parents": [],
                "children": [],
            }
        ]

        ok = parser.check_parent_boundary()

        self.assertFalse(ok)

    def test_parse_parent_attribute_deduplicates_values(self):
        content = (
            "##gff-version 3\n"
            "chr1\tsrc\tgene\t1\t100\t.\t+\t.\tID=gene1\n"
            "chr1\tsrc\tmRNA\t1\t100\t.\t+\t.\tID=tx1;Parent=gene1,gene1\n"
        )
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        mrna = parser.lines[2]
        self.assertEqual(set(mrna["attributes"]["Parent"]), {"gene1"})
        self.assertTrue(any(e["eCode"] == "Esf0034" for e in mrna["line_errors"]))

    def test_parse_cds_requires_phase_when_phase_is_dot(self):
        content = (
            "##gff-version 3\n"
            "chr1\tsrc\tCDS\t1\t9\t.\t+\t.\tID=cds1\n"
        )
        parser = gff3.Gff3(gff_file=io.StringIO(content))

        cds = parser.lines[1]
        self.assertTrue(any(e["eCode"] == "Esf0027" for e in cds["line_errors"]))

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

    def test_sequence_returns_none_for_non_feature_line(self):
        parser = gff3.Gff3()
        parser.lines = [{"line_index": 0, "line_type": "directive", "directive": "##gff-version"}]

        seq = parser.sequence(0, reference={"chr1": "AACCGGTT"})

        self.assertIsNone(seq)

    def test_overlap_true_and_false_cases(self):
        parser = gff3.Gff3()
        a = {"seqid": "chr1", "start": 1, "end": 10}
        b = {"seqid": "chr1", "start": 8, "end": 12}
        c = {"seqid": "chr2", "start": 8, "end": 12}

        self.assertTrue(parser.overlap(a, b))
        self.assertFalse(parser.overlap(a, c))

    def test_write_skips_removed_features(self):
        parser = gff3.Gff3()
        root = {
            "line_index": 0,
            "line_type": "feature",
            "line_status": "normal",
            "line_raw": "",
            "seqid": "chr1",
            "source": "src",
            "type": "gene",
            "start": 1,
            "end": 4,
            "score": ".",
            "strand": "+",
            "phase": ".",
            "attributes": {"ID": "gene1"},
            "parents": [],
            "children": [],
        }
        child_removed = {
            "line_index": 1,
            "line_type": "feature",
            "line_status": "removed",
            "line_raw": "",
            "seqid": "chr1",
            "source": "src",
            "type": "mRNA",
            "start": 1,
            "end": 4,
            "score": ".",
            "strand": "+",
            "phase": ".",
            "attributes": {"ID": "tx1", "Parent": ["gene1"]},
            "parents": [[root]],
            "children": [],
        }
        root["children"] = [child_removed]
        parser.lines = [root, child_removed]
        parser.features = {"gene1": [root], "tx1": [child_removed]}
        parser.fasta_external = {"chr1": {"header": ">chr1", "seq": "AACC"}}
        out = io.StringIO()

        parser.write(out, embed_fasta=False)

        value = out.getvalue()
        self.assertIn("##sequence-region chr1 1 4\n", value)
        self.assertIn("ID=gene1", value)
        self.assertNotIn("ID=tx1", value)


if __name__ == "__main__":
    unittest.main()