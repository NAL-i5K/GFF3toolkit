import os
import tempfile
import unittest
from unittest import mock

from gff3tool.bin import gff3_sort


class _FakeGff:
    def __init__(self, lines, fasta_embedded=None, descendants_map=None):
        self.lines = lines
        self.fasta_embedded = fasta_embedded or {}
        self._descendants_map = descendants_map or {}

    def collect_descendants(self, root):
        root_id = root.get("attributes", {}).get("ID")
        return self._descendants_map.get(root_id, [])


class TestGff3SortMain(unittest.TestCase):
    def test_main_with_sorting_order_uses_recursive_writer(self):
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "chr1\tsrc\tgene\t1\t10\t.\t+\t.\tID=g1\n",
            "seqid": "chr1",
            "start": 1,
            "end": 10,
            "attributes": {"ID": "g1"},
            "children": [],
            "strand": "+",
        }
        seqreg = {
            "line_type": "directive",
            "directive": "##sequence-region",
            "seqid": "chr1",
            "start": 1,
            "end": 100,
            "line_raw": "##sequence-region chr1 1 100\n",
        }
        fake = _FakeGff([seqreg, root])

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sorted.gff3")
            with mock.patch.object(gff3_sort, "Gff3", return_value=fake), \
                mock.patch.object(gff3_sort, "write_out_by_level", return_value=set()) as write_level:
                gff3_sort.main(
                    gff="in.gff3",
                    output=out_path,
                    sorting_order={"gene": 1},
                    isoform_sort=False,
                    logger=mock.Mock(),
                    reference=False,
                )

        write_level.assert_called_once()

    def test_main_with_isoform_sort_writes_type_sorted_model(self):
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "root\n",
            "seqid": "chr1",
            "start": 1,
            "end": 100,
            "attributes": {"ID": "g1"},
            "children": [],
            "strand": "+",
        }
        child = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "child\n",
            "seqid": "chr1",
            "start": 1,
            "end": 100,
            "attributes": {"ID": "tx1", "Parent": ["g1"]},
            "children": [],
            "strand": "+",
        }
        fake = _FakeGff([root, child], descendants_map={"g1": [child]})

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sorted.gff3")
            with mock.patch.object(gff3_sort, "Gff3", return_value=fake), \
                mock.patch.object(gff3_sort, "TypeSort", return_value=[child, root]) as typesort:
                gff3_sort.main(
                    gff="in.gff3",
                    output=out_path,
                    sorting_order={"gene": 1, "mRNA": 2},
                    isoform_sort=True,
                    logger=mock.Mock(),
                    reference=False,
                )

            with open(out_path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()

        typesort.assert_called_once()
        self.assertEqual(lines[0], "child\n")
        self.assertEqual(lines[1], "root\n")

    def test_main_logs_omitted_lines_when_no_roots(self):
        orphan = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "orphan\n",
            "seqid": "chr1",
            "start": 10,
            "end": 20,
            "attributes": {"ID": "tx1", "Parent": ["g_missing"]},
            "children": [],
            "strand": "+",
        }
        fake = _FakeGff([orphan])
        logger = mock.Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sorted.gff3")
            with mock.patch.object(gff3_sort, "Gff3", return_value=fake), \
                mock.patch("builtins.print") as print_mock:
                gff3_sort.main(
                    gff="in.gff3",
                    output=out_path,
                    sorting_order=None,
                    isoform_sort=False,
                    logger=logger,
                    reference=False,
                )

        logger.warning.assert_called_once()
        print_mock.assert_called_once()

    def test_main_writes_embedded_fasta_block(self):
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "root\n",
            "seqid": "chr1",
            "start": 1,
            "end": 10,
            "attributes": {"ID": "g1"},
            "children": [],
            "strand": "+",
        }
        fake = _FakeGff(
            [root],
            fasta_embedded={"chr1": {"header": ">chr1", "seq": "AACCGG"}},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sorted.gff3")
            with mock.patch.object(gff3_sort, "Gff3", return_value=fake):
                gff3_sort.main(
                    gff="in.gff3",
                    output=out_path,
                    sorting_order={"gene": 1},
                    isoform_sort=False,
                    logger=mock.Mock(),
                    reference=False,
                )

            with open(out_path, "r", encoding="utf-8") as handle:
                content = handle.read()

        self.assertIn("##FASTA", content)
        self.assertIn(">chr1\nAACCGG\n", content)


if __name__ == "__main__":
    unittest.main()
