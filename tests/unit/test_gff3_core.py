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