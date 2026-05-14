import io
import unittest
from collections import defaultdict
from unittest import mock

from gff3tool.lib.gff3_merge import merge


class FakeGroups:
    def __init__(self, **_kwargs):
        self.mapName2ID = {}
        self.info = []
        self.mapType2Log = {
            "other": "OTHER",
            "Delete": "DELETE",
            "simple": "SIMPLE",
            "multi-ref": "MULTI",
        }
        self.id2name = {}
        pgff = _kwargs.get("Pgff")
        if pgff is not None:
            for line in pgff.lines:
                line_id = line.get("attributes", {}).get("ID")
                if line_id:
                    self.id2name[line_id] = line.get("attributes", {}).get("Name", line_id)

    def replacer(self, *_args, **_kwargs):
        root = _args[0]
        for child in root.get("children", []):
            child.setdefault("attributes", {})["replace_type"] = "other"
        return None

    def replacer_multi(self, *_args, **_kwargs):
        return "ok"

    def name2id(self, *_args, **_kwargs):
        return None


class FakeGff:
    def __init__(self, lines):
        self.lines = lines
        self.features = defaultdict(list)
        for line in lines:
            line_id = line.get("attributes", {}).get("ID")
            if line_id:
                self.features[line_id].append(line)
        self.written_output = None

    def collect_roots(self, line):
        return [line]

    def collect_descendants(self, line):
        return line.get("children", [])

    def write(self, output_gff):
        self.written_output = output_gff


class TestMergeMain(unittest.TestCase):
    def _make_root_with_child(self, root_id, child_status="active", child_replace=None):
        if child_replace is None:
            child_replace = ["NA"]

        child = {
            "line_type": "feature",
            "type": "mRNA",
            "line_status": "removed" if child_status == "removed" else "active",
            "line_raw": f"raw-{root_id}-child",
            "attributes": {
                "ID": f"{root_id}-RA",
                "replace": list(child_replace),
            },
            "parents": [],
            "children": [],
        }
        if child_status == "removed":
            child["attributes"]["status"] = "Delete"

        root = {
            "line_type": "feature",
            "type": "gene",
            "attributes": {"ID": root_id},
            "children": [child],
        }
        return root, child

    def test_delete_with_na_replace_raises_system_exit(self):
        wa_root, wa_child = self._make_root_with_child("gene1", child_status="active", child_replace=["NA"])
        other_root, other_child = self._make_root_with_child("gene1", child_status="removed", child_replace=["NA"])

        wa_gff = FakeGff([wa_root, wa_child])
        other_gff = FakeGff([other_root, other_child])

        def fake_gff_factory(gff_file=None, logger=None):
            if gff_file == "WA_sorted.gff":
                return wa_gff
            if gff_file == "other_sorted.gff":
                return other_gff
            raise AssertionError(f"Unexpected gff file: {gff_file}")

        with mock.patch.object(merge.gff3_sort, "main", autospec=True), \
            mock.patch.object(merge.replace_OGS, "Groups", FakeGroups), \
            mock.patch.object(merge, "Gff3", side_effect=fake_gff_factory), \
            mock.patch.object(merge, "remove_files_from_list", autospec=True):
            with self.assertRaises(SystemExit) as cm:
                merge.main(
                    gff_file1="wa.gff3",
                    gff_file2="other.gff3",
                    output_gff="out.gff3",
                    report_fh=io.StringIO(),
                )

        self.assertIn("replace tag for Delete replacement cannot be NA", str(cm.exception))

    def test_main_writes_output_and_cleans_temp_files(self):
        wa_root, wa_child = self._make_root_with_child("geneX", child_status="active", child_replace=["NA"])
        other_root, other_child = self._make_root_with_child("geneY", child_status="active", child_replace=["NA"])

        wa_gff = FakeGff([wa_root, wa_child])
        other_gff = FakeGff([other_root, other_child])

        def fake_gff_factory(gff_file=None, logger=None):
            if gff_file == "WA_sorted.gff":
                return wa_gff
            if gff_file == "other_sorted.gff":
                return other_gff
            raise AssertionError(f"Unexpected gff file: {gff_file}")

        report = io.StringIO()

        with mock.patch.object(merge.gff3_sort, "main", autospec=True), \
            mock.patch.object(merge.replace_OGS, "Groups", FakeGroups), \
            mock.patch.object(merge, "Gff3", side_effect=fake_gff_factory), \
            mock.patch.object(merge, "remove_files_from_list", autospec=True) as rm_files:
            merge.main(
                gff_file1="wa.gff3",
                gff_file2="other.gff3",
                output_gff="final.gff3",
                report_fh=report,
            )

        self.assertEqual(other_gff.written_output, "final.gff3")
        rm_files.assert_called_once_with(["WA_sorted.gff", "other_sorted.gff"])
        report_output = report.getvalue()
        self.assertIn("# Number of WA loci", report_output)
        self.assertIn("Change_log", report_output)
        self.assertIn("OTHER", report_output)

    def test_multi_ref_path_records_multi_ref_transcript_count(self):
        wa_root, wa_child = self._make_root_with_child("geneM", child_status="active", child_replace=["T1"])
        wa_gff = FakeGff([wa_root, wa_child])

        ref_tx1 = {
            "line_type": "feature",
            "type": "mRNA",
            "line_status": "active",
            "line_raw": "raw-ref-tx1",
            "attributes": {"ID": "ref_tx1", "Name": "ref_tx1"},
            "children": [],
            "parents": [],
        }
        ref_tx2 = {
            "line_type": "feature",
            "type": "mRNA",
            "line_status": "active",
            "line_raw": "raw-ref-tx2",
            "attributes": {"ID": "ref_tx2", "Name": "ref_tx2"},
            "children": [],
            "parents": [],
        }
        ref_root = {
            "line_type": "feature",
            "type": "gene",
            "attributes": {"ID": "ref_gene"},
            "children": [ref_tx1, ref_tx2],
        }
        ref_tx1["parents"] = [[ref_root]]
        ref_tx2["parents"] = [[ref_root]]
        other_gff = FakeGff([ref_root, ref_tx1, ref_tx2])

        class GroupsWithTagMap(FakeGroups):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.mapName2ID["T1"] = "ref_tx1"

        def fake_gff_factory(gff_file=None, logger=None):
            if gff_file == "WA_sorted.gff":
                return wa_gff
            if gff_file == "other_sorted.gff":
                return other_gff
            raise AssertionError(f"Unexpected gff file: {gff_file}")

        report = io.StringIO()
        with mock.patch.object(merge.gff3_sort, "main", autospec=True), \
            mock.patch.object(merge.replace_OGS, "Groups", GroupsWithTagMap), \
            mock.patch.object(merge, "Gff3", side_effect=fake_gff_factory), \
            mock.patch.object(merge, "remove_files_from_list", autospec=True):
            merge.main(
                gff_file1="wa.gff3",
                gff_file2="other.gff3",
                output_gff="final.gff3",
                report_fh=report,
            )

        report_output = report.getvalue()
        self.assertIn("ok", report_output)
        self.assertIn("# Number of transcripts with multi-ref replacement: 1", report_output)


if __name__ == "__main__":
    unittest.main()
