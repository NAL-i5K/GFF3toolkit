import unittest
from collections import defaultdict
from unittest import mock

from gff3tool.lib.function4gff import function4gff


class DummyGff:
    def __init__(self, lines):
        self.lines = lines
        self.features = defaultdict(list)


class TestFunction4Gff(unittest.TestCase):
    def test_random_id_uses_requested_size_and_charset(self):
        rid = function4gff.randomID(size=12, chars="AB")
        self.assertEqual(len(rid), 12)
        self.assertTrue(set(rid).issubset({"A", "B"}))

    def test_fix_missing_attr_sets_owner_and_assigns_id_for_non_required_types(self):
        feature = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "chr1\tsrc\texon\t1\t2\t.\t+\t.\t.",
            "type": "exon",
            "attributes": {},
        }
        gff = DummyGff([feature])
        log = mock.Mock()

        with mock.patch.object(function4gff, "randomID", return_value="RID123"):
            function4gff.FIX_MISSING_ATTR(gff, logger=log)

        self.assertEqual(feature["attributes"]["owner"], "Unassigned")
        self.assertEqual(feature["attributes"]["ID"], "RID123")
        self.assertIn(feature, gff.features["RID123"])

    def test_fix_missing_attr_exits_when_required_id_is_missing(self):
        feature = {
            "line_type": "feature",
            "line_index": 4,
            "line_raw": "chr1\tsrc\tgene\t1\t100\t.\t+\t.\t.",
            "type": "gene",
            "attributes": {},
        }
        gff = DummyGff([feature])
        log = mock.Mock()

        with self.assertRaises(SystemExit):
            function4gff.FIX_MISSING_ATTR(gff, logger=log)

        self.assertTrue(log.error.called)

    def test_feature_sort_orders_by_seqid_numeric_start_and_type_rank(self):
        lines = [
            {
                "seqid": "chr10",
                "start": 5,
                "end": 10,
                "type": "gene",
                "line_raw": "gene_chr10",
            },
            {
                "seqid": "chr2",
                "start": 5,
                "end": 10,
                "type": "mRNA",
                "line_raw": "mrna_chr2",
            },
            {
                "seqid": "chr2",
                "start": 5,
                "end": 10,
                "type": "gene",
                "line_raw": "gene_chr2",
            },
        ]

        sorted_lines = function4gff.featureSort(lines)
        sorted_raw = [line["line_raw"] for line in sorted_lines]
        self.assertEqual(sorted_raw, ["gene_chr2", "mrna_chr2", "gene_chr10"])

    def test_feature_sort_keeps_non_numeric_seqids(self):
        lines = [
            {
                "seqid": "chrX",
                "start": 5,
                "end": 10,
                "type": "gene",
                "line_raw": "gene_chrX",
            },
            {
                "seqid": "chr2",
                "start": 5,
                "end": 10,
                "type": "gene",
                "line_raw": "gene_chr2",
            },
            {
                "seqid": "scaffoldA",
                "start": 5,
                "end": 10,
                "type": "gene",
                "line_raw": "gene_scaffoldA",
            },
        ]

        sorted_lines = function4gff.featureSort(lines)
        sorted_raw = [line["line_raw"] for line in sorted_lines]
        self.assertEqual(sorted_raw, ["gene_chr2", "gene_chrX", "gene_scaffoldA"])

    def test_extract_internal_detected_errors_collects_error_metadata(self):
        line_with_id = {
            "line_index": 9,
            "line_raw": "line-a",
            "attributes": {"ID": "model1"},
            "line_errors": [{"eCode": "E001", "message": "bad model"}],
        }
        line_without_id = {
            "line_index": 15,
            "line_raw": "line-b",
            "attributes": {},
            "line_errors": [{"eCode": "E002", "message": "missing parent", "error_level": "Warning"}],
        }
        gff = DummyGff([line_with_id, line_without_id])

        errors = function4gff.extract_internal_detected_errors(gff)

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0]["ID"], ["model1"])
        self.assertEqual(errors[0]["eCode"], "E001")
        self.assertEqual(errors[0]["error_level"], "Error")
        self.assertEqual(errors[1]["ID"], ["NA"])
        self.assertEqual(errors[1]["error_level"], "Warning")


if __name__ == "__main__":
    unittest.main()