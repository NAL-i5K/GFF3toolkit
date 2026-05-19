import io
import unittest
from unittest import mock

from gff3tool.bin import gff3_merge


class FakeGff:
    def __init__(self, lines):
        self.lines = lines


def _root_with_child(root_id="gene1", child_id="tx1", replace=None, child_type="mRNA"):
    child_attrs = {"ID": child_id}
    if replace is not None:
        child_attrs["replace"] = replace

    child = {
        "line_type": "feature",
        "line_index": 1,
        "line_raw": f"{child_id}-raw",
        "type": child_type,
        "attributes": child_attrs,
        "children": [],
    }
    root = {
        "line_type": "feature",
        "line_index": 0,
        "line_raw": f"{root_id}-raw",
        "type": "gene",
        "attributes": {"ID": root_id},
        "children": [child],
    }
    return root, child


class TestGff3MergeCore(unittest.TestCase):
    def test_check_replace_returns_false_when_all_children_have_replace(self):
        root, _ = _root_with_child(replace=["NA"])
        gff = FakeGff([root])

        result = gff3_merge.check_replace(gff)

        self.assertFalse(result)

    def test_check_replace_collects_children_missing_replace(self):
        root, child = _root_with_child(replace=None)
        gff = FakeGff([root])

        result = gff3_merge.check_replace(gff)

        self.assertEqual(result, [child])

    def test_check_replace_user_defined_checks_target_type(self):
        root, child = _root_with_child(replace=None, child_type="mRNA")
        gff = FakeGff([root, child])

        result = gff3_merge.check_replace(gff, user_defined1=[["mRNA", "CDS"]])

        self.assertEqual(result, [child])

    def test_main_non_auto_stops_when_replace_missing(self):
        root, child = _root_with_child(replace=None)
        fake_gff = FakeGff([root, child])

        with mock.patch.object(gff3_merge, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(gff3_merge.gff3_merge.merge, "main", autospec=True) as merge_main:
            gff3_merge.main(
                gff_file1="new.gff3",
                gff_file2="ref.gff3",
                fasta="ref.fa",
                report=io.StringIO(),
                output_gff="out.gff3",
                auto=False,
                logger=mock.Mock(),
            )

        merge_main.assert_not_called()

    def test_main_non_auto_calls_merge_when_replace_present(self):
        root, child = _root_with_child(replace=["NA"])
        fake_gff = FakeGff([root, child])

        with mock.patch.object(gff3_merge, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(gff3_merge.gff3_merge.merge, "main", autospec=True) as merge_main:
            gff3_merge.main(
                gff_file1="new.gff3",
                gff_file2="ref.gff3",
                fasta="ref.fa",
                report=io.StringIO(),
                output_gff="out.gff3",
                auto=False,
                logger=mock.Mock(),
            )

        merge_main.assert_called_once()


if __name__ == "__main__":
    unittest.main()