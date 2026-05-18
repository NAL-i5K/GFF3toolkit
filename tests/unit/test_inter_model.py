import unittest
from unittest import mock

from gff3tool.lib.inter_model import inter_model


class DummyGff:
    def __init__(self, lines=None):
        self.lines = lines or []
        self.line_errors = []

    def add_line_error(self, line, error, log_level=None):
        self.line_errors.append((line, error, log_level))


def _make_feature(line_id, line_index, seqid='chr1'):
    return {
        'line_type': 'feature',
        'line_raw': line_id,
        'line_index': line_index,
        'seqid': seqid,
        'source': '.',
        'type': 'exon',
        'start': 1,
        'end': 10,
        'score': '.',
        'strand': '+',
        'phase': '.',
        'attributes': {'ID': line_id},
        'children': [],
    }


def _make_transcript(tx_id, line_index, child_ids, seqid='chr1'):
    children = [_make_feature(cid, line_index + i + 1, seqid=seqid) for i, cid in enumerate(child_ids)]
    return {
        'line_type': 'feature',
        'line_raw': tx_id,
        'line_index': line_index,
        'seqid': seqid,
        'source': '.',
        'type': 'mRNA',
        'start': 1,
        'end': 10,
        'score': '.',
        'strand': '+',
        'phase': '.',
        'attributes': {'ID': tx_id},
        'children': children,
    }


class TestInterModel(unittest.TestCase):
    def test_check_duplicate_reports_matching_transcripts(self):
        gff = DummyGff()
        tx1 = _make_transcript('tx1', 0, ['ex1'])
        tx2 = _make_transcript('tx2', 10, ['ex2'])

        result = inter_model.check_duplicate(gff, [tx1, tx2])

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['eCode'], 'Emr0001')
        self.assertEqual(len(gff.line_errors), 2)

    def test_check_duplicate_returns_none_for_nonmatching_transcripts(self):
        gff = DummyGff()
        tx1 = _make_transcript('tx1', 0, ['ex1'], seqid='chr1')
        tx2 = _make_transcript('tx2', 10, ['ex2'], seqid='chr2')

        result = inter_model.check_duplicate(gff, [tx1, tx2])

        self.assertIsNone(result)
        self.assertEqual(gff.line_errors, [])

    def test_main_noncanonical_skips_inter_model_checks(self):
        child = _make_transcript('tx1', 1, ['ex1'])
        root = {
            'line_type': 'feature',
            'line_index': 0,
            'attributes': {'ID': 'gene1'},
            'children': [child],
        }
        gff = DummyGff(lines=[root])

        with mock.patch.object(inter_model.function4gff, 'FIX_MISSING_ATTR', autospec=True) as fix_mock, \
            mock.patch.object(inter_model, 'check_duplicate', autospec=True) as dup_mock, \
            mock.patch.object(inter_model, 'check_incorrectly_split_genes', autospec=True) as split_mock:
            result = inter_model.main(gff, 'in.gff3', 'ref.fa', logger=mock.Mock(), noncanonical_gene=True)

        fix_mock.assert_called_once()
        dup_mock.assert_not_called()
        split_mock.assert_not_called()
        self.assertIsNone(result)

    def test_main_canonical_aggregates_detected_errors(self):
        child = _make_transcript('tx1', 1, ['ex1'])
        root = {
            'line_type': 'feature',
            'line_index': 0,
            'attributes': {'ID': 'gene1'},
            'children': [child],
        }
        gff = DummyGff(lines=[root])
        err1 = [{'eCode': 'Emr0001'}]
        err2 = [{'eCode': 'Emr0002'}]

        with mock.patch.object(inter_model.function4gff, 'FIX_MISSING_ATTR', autospec=True), \
            mock.patch.object(inter_model, 'check_duplicate', autospec=True, return_value=err1), \
            mock.patch.object(inter_model, 'check_incorrectly_split_genes', autospec=True, return_value=err2):
            result = inter_model.main(gff, 'in.gff3', 'ref.fa', logger=mock.Mock(), noncanonical_gene=False)

        self.assertEqual(result, err1 + err2)


if __name__ == '__main__':
    unittest.main()
