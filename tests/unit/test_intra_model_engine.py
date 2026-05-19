import unittest
from unittest import mock

from gff3tool.lib.intra_model import intra_model


class DummyGff:
    def __init__(self, lines=None):
        self.lines = lines or []
        self.line_errors = []

    def add_line_error(self, line, error, log_level=None):
        self.line_errors.append((line, error, log_level))

    @staticmethod
    def overlap(a, b):
        return not (a["end"] < b["start"] or b["end"] < a["start"])


def _cds(line_index, start, end):
    return {
        "line_type": "feature",
        "line_index": line_index,
        "type": "CDS",
        "start": start,
        "end": end,
        "attributes": {"ID": f"cds{line_index}"},
        "children": [],
    }


class TestIntraModelEngine(unittest.TestCase):
    def test_check_incomplete_flags_gene_without_mrna(self):
        root = {
            "line_type": "feature",
            "line_index": 0,
            "type": "gene",
            "attributes": {"ID": "gene1"},
            "children": [{"type": "exon", "children": []}],
        }
        gff = DummyGff()

        result = intra_model.check_incomplete(gff, root)

        self.assertIsNotNone(result)
        self.assertEqual(result[0]["eCode"], "Ema0004")
        self.assertEqual(len(gff.line_errors), 1)

    def test_check_merged_gene_parent_flags_non_overlapping_isoforms(self):
        tx1 = {
            "line_index": 1,
            "attributes": {"ID": "tx1"},
            "children": [_cds(2, 1, 5)],
        }
        tx2 = {
            "line_index": 3,
            "attributes": {"ID": "tx2"},
            "children": [_cds(4, 20, 30)],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "type": "gene",
            "attributes": {"ID": "gene1"},
            "children": [tx1, tx2],
        }
        gff = DummyGff()

        result = intra_model.check_merged_gene_parent(gff, root)

        self.assertIsNotNone(result)
        self.assertEqual(result[0]["eCode"], "Ema0009")
        self.assertEqual(len(gff.line_errors), 1)

    def test_main_noncanonical_skips_internal_stop_and_isoform_checks(self):
        root = {
            "line_type": "feature",
            "line_index": 0,
            "type": "gene",
            "start": 1,
            "end": 100,
            "attributes": {"ID": "gene1"},
            "children": [],
        }
        gff = DummyGff(lines=[root])

        with mock.patch.object(intra_model.function4gff, "FIX_MISSING_ATTR", autospec=True), \
            mock.patch.object(intra_model, "check_internal_stop", autospec=True) as internal_stop, \
            mock.patch.object(intra_model, "check_distinct_isoform", autospec=True) as distinct_isoform, \
            mock.patch.object(intra_model, "check_merged_gene_parent", autospec=True) as merged_parent:
            intra_model.main(gff=gff, logger=mock.Mock(), noncanonical_gene=True)

        internal_stop.assert_not_called()
        distinct_isoform.assert_not_called()
        merged_parent.assert_not_called()

    def test_main_canonical_collects_reported_errors(self):
        root = {
            "line_type": "feature",
            "line_index": 0,
            "type": "gene",
            "start": 1,
            "end": 100,
            "attributes": {"ID": "gene1"},
            "children": [],
        }
        gff = DummyGff(lines=[root])

        with mock.patch.object(intra_model.function4gff, "FIX_MISSING_ATTR", autospec=True), \
            mock.patch.object(intra_model, "check_pseudo_child_type", autospec=True, return_value=[{"eCode": "Ema0005"}]), \
            mock.patch.object(intra_model, "check_redundant_length", autospec=True, return_value=[{"eCode": "Ema0001"}]), \
            mock.patch.object(intra_model, "check_incomplete", autospec=True, return_value=[{"eCode": "Ema0004"}]), \
            mock.patch.object(intra_model, "check_internal_stop", autospec=True, return_value=[{"eCode": "Ema0002"}]), \
            mock.patch.object(intra_model, "check_distinct_isoform", autospec=True, return_value=[{"eCode": "Ema0008"}]), \
            mock.patch.object(intra_model, "check_merged_gene_parent", autospec=True, return_value=[{"eCode": "Ema0009"}]):
            result = intra_model.main(gff=gff, logger=mock.Mock(), noncanonical_gene=False)

        self.assertEqual([r["eCode"] for r in result], ["Ema0005", "Ema0001", "Ema0004", "Ema0002", "Ema0008", "Ema0009"])


if __name__ == "__main__":
    unittest.main()