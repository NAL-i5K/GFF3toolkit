import os
import tempfile
import unittest
import warnings
from collections import defaultdict
from unittest import mock

from gff3tool.lib.gff3_merge import revision


class FakeGff:
    def __init__(self, lines):
        self.lines = lines
        self.features = defaultdict(list)
        self.removed = []
        self.written_output = None
        for line in lines:
            line_id = line.get("attributes", {}).get("ID")
            if line_id:
                self.features[line_id].append(line)

    def collect_descendants(self, line):
        descendants = []
        for child in line.get("children", []):
            descendants.append(child)
            descendants.extend(self.collect_descendants(child))
        return descendants

    def collect_roots(self, line):
        return line.get("roots", [])

    def remove(self, line):
        self.removed.append(line)

    def write(self, output_gff):
        self.written_output = output_gff


def write_revision_file(path, rows):
    header = "\t".join([f"c{i}" for i in range(25)])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(header + "\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")


def build_revision_row(seqid, start, end, strand, feature_type, feature_id, replace_value):
    cols = ["x"] * 25
    cols[6] = seqid
    cols[7] = str(start)
    cols[8] = str(end)
    cols[9] = strand
    cols[10] = feature_type
    cols[12] = feature_id
    cols[24] = replace_value
    return cols


class TestRevisionMain(unittest.TestCase):
    def test_main_propagates_replace_and_adds_exon_for_ncrna(self):
        ncrna = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "chr1\tsrc\tncRNA\t10\t50\t.\t+\t.\tID=tx1",
            "seqid": "chr1",
            "start": 10,
            "end": 50,
            "strand": "+",
            "type": "ncRNA",
            "attributes": {"ID": "tx1", "Parent": ["gene1"]},
            "children": [],
            "parents": [],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "chr1\tsrc\tgene\t1\t100\t.\t+\t.\tID=gene1",
            "seqid": "chr1",
            "start": 1,
            "end": 100,
            "strand": "+",
            "type": "gene",
            "attributes": {"ID": "gene1", "replace": [" OGS0001 "]},
            "children": [ncrna],
        }

        fake_gff = FakeGff([root, ncrna])

        with tempfile.TemporaryDirectory() as tmpdir:
            revision_path = os.path.join(tmpdir, "rev.tsv")
            output_path = os.path.join(tmpdir, "out.gff3")
            report_path = os.path.join(tmpdir, "report.txt")
            write_revision_file(revision_path, rows=[])

            with mock.patch.object(revision, "Gff3", return_value=fake_gff):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    revision.main(
                        gff_file="input.gff3",
                        revision_file=revision_path,
                        output_gff=output_path,
                        report_file=report_path,
                    )

        self.assertNotIn("replace", root["attributes"])
        self.assertEqual(ncrna["attributes"]["replace"], ["OGS0001"])
        exons = [child for child in ncrna["children"] if child["type"] == "exon"]
        self.assertEqual(len(exons), 1)
        self.assertEqual(exons[0]["attributes"]["ID"], "tx1-EXON1")
        self.assertEqual(fake_gff.written_output, output_path)

    def test_main_auto_merges_distinct_non_na_replace_tags(self):
        child1 = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "raw-child1",
            "seqid": "chr1",
            "start": 10,
            "end": 20,
            "strand": "+",
            "type": "mRNA",
            "attributes": {"ID": "txA", "Parent": ["gene1"], "replace": ["A"]},
            "children": [],
            "parents": [],
        }
        child2 = {
            "line_type": "feature",
            "line_index": 2,
            "line_raw": "raw-child2",
            "seqid": "chr1",
            "start": 30,
            "end": 40,
            "strand": "+",
            "type": "mRNA",
            "attributes": {"ID": "txB", "Parent": ["gene1"], "replace": ["B"]},
            "children": [],
            "parents": [],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "raw-root",
            "seqid": "chr1",
            "start": 1,
            "end": 100,
            "strand": "+",
            "type": "gene",
            "attributes": {"ID": "gene1"},
            "children": [child1, child2],
        }

        fake_gff = FakeGff([root, child1, child2])

        with tempfile.TemporaryDirectory() as tmpdir:
            revision_path = os.path.join(tmpdir, "rev.tsv")
            output_path = os.path.join(tmpdir, "out.gff3")
            report_path = os.path.join(tmpdir, "report.txt")
            write_revision_file(revision_path, rows=[])

            with mock.patch.object(revision, "Gff3", return_value=fake_gff):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    revision.main(
                        gff_file="input.gff3",
                        revision_file=revision_path,
                        output_gff=output_path,
                        report_file=report_path,
                        auto=True,
                    )

        self.assertEqual(set(child1["attributes"]["replace"]), {"A", "B"})
        self.assertEqual(set(child2["attributes"]["replace"]), {"A", "B"})

    def test_main_applies_revision_file_replace_by_feature_id(self):
        child = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "raw-child",
            "seqid": "chr2",
            "start": 200,
            "end": 300,
            "strand": "-",
            "type": "mRNA",
            "attributes": {"ID": "tx2", "Parent": ["gene2"]},
            "children": [],
            "parents": [],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "raw-root2",
            "seqid": "chr2",
            "start": 150,
            "end": 350,
            "strand": "-",
            "type": "gene",
            "attributes": {"ID": "gene2"},
            "children": [child],
        }

        fake_gff = FakeGff([root, child])
        row = build_revision_row("chr2", 200, 300, "-", "mRNA", "tx2", "REP-2")

        with tempfile.TemporaryDirectory() as tmpdir:
            revision_path = os.path.join(tmpdir, "rev.tsv")
            output_path = os.path.join(tmpdir, "out.gff3")
            report_path = os.path.join(tmpdir, "report.txt")
            write_revision_file(revision_path, rows=[row])

            with mock.patch.object(revision, "Gff3", return_value=fake_gff):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    revision.main(
                        gff_file="input.gff3",
                        revision_file=revision_path,
                        output_gff=output_path,
                        report_file=report_path,
                    )

        self.assertEqual(child["attributes"]["replace"], ["REP-2"])

    def test_main_matches_revision_by_coordinates_when_ids_differ(self):
        child = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "raw-child",
            "seqid": "chr2",
            "start": 200,
            "end": 300,
            "strand": "-",
            "type": "mRNA",
            "attributes": {"ID": "tx-from-gff", "Parent": ["gene2"]},
            "children": [],
            "parents": [],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "raw-root2",
            "seqid": "chr2",
            "start": 150,
            "end": 350,
            "strand": "-",
            "type": "gene",
            "attributes": {"ID": "gene2"},
            "children": [child],
        }

        fake_gff = FakeGff([root, child])
        row = build_revision_row("chr2", 200, 300, "-", "mRNA", "different-id", "REP-COORD")

        with tempfile.TemporaryDirectory() as tmpdir:
            revision_path = os.path.join(tmpdir, "rev.tsv")
            output_path = os.path.join(tmpdir, "out.gff3")
            report_path = os.path.join(tmpdir, "report.txt")
            write_revision_file(revision_path, rows=[row])

            with mock.patch.object(revision, "Gff3", return_value=fake_gff):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    revision.main(
                        gff_file="input.gff3",
                        revision_file=revision_path,
                        output_gff=output_path,
                        report_file=report_path,
                    )

            with open(report_path, "r", encoding="utf-8") as fh:
                report_text = fh.read()

        self.assertEqual(child["attributes"]["replace"], ["REP-COORD"])
        self.assertIn("Same genomic region, but different IDs", report_text)

    def test_main_user_defined_mode_targets_only_selected_transcripts(self):
        target_child = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "target-child",
            "seqid": "chr3",
            "start": 20,
            "end": 40,
            "strand": "+",
            "type": "mRNA",
            "attributes": {"ID": "tx3", "Parent": ["gene3"]},
            "children": [],
            "parents": [],
        }
        other_child = {
            "line_type": "feature",
            "line_index": 2,
            "line_raw": "other-child",
            "seqid": "chr3",
            "start": 50,
            "end": 80,
            "strand": "+",
            "type": "CDS",
            "attributes": {"ID": "cds3", "Parent": ["tx3"]},
            "children": [],
            "parents": [],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "root3",
            "seqid": "chr3",
            "start": 1,
            "end": 100,
            "strand": "+",
            "type": "gene",
            "attributes": {"ID": "gene3", "replace": [" REP3 "]},
            "children": [target_child, other_child],
        }
        target_child["roots"] = [root]

        fake_gff = FakeGff([root, target_child, other_child])

        with tempfile.TemporaryDirectory() as tmpdir:
            revision_path = os.path.join(tmpdir, "rev.tsv")
            output_path = os.path.join(tmpdir, "out.gff3")
            report_path = os.path.join(tmpdir, "report.txt")
            write_revision_file(revision_path, rows=[])

            with mock.patch.object(revision, "Gff3", return_value=fake_gff):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    revision.main(
                        gff_file="input.gff3",
                        revision_file=revision_path,
                        output_gff=output_path,
                        report_file=report_path,
                        user_defined1=[["mRNA"]],
                    )

        self.assertNotIn("replace", root["attributes"])
        self.assertEqual(target_child["attributes"]["replace"], ["REP3"])
        self.assertNotIn("replace", other_child["attributes"])

    def test_main_does_not_auto_merge_when_any_replace_tag_is_na(self):
        child1 = {
            "line_type": "feature",
            "line_index": 1,
            "line_raw": "raw-child1",
            "seqid": "chr1",
            "start": 10,
            "end": 20,
            "strand": "+",
            "type": "mRNA",
            "attributes": {"ID": "txA", "Parent": ["gene1"], "replace": ["A"]},
            "children": [],
            "parents": [],
        }
        child2 = {
            "line_type": "feature",
            "line_index": 2,
            "line_raw": "raw-child2",
            "seqid": "chr1",
            "start": 30,
            "end": 40,
            "strand": "+",
            "type": "mRNA",
            "attributes": {"ID": "txB", "Parent": ["gene1"], "replace": ["NA"]},
            "children": [],
            "parents": [],
        }
        root = {
            "line_type": "feature",
            "line_index": 0,
            "line_raw": "raw-root",
            "seqid": "chr1",
            "start": 1,
            "end": 100,
            "strand": "+",
            "type": "gene",
            "attributes": {"ID": "gene1"},
            "children": [child1, child2],
        }

        fake_gff = FakeGff([root, child1, child2])

        with tempfile.TemporaryDirectory() as tmpdir:
            revision_path = os.path.join(tmpdir, "rev.tsv")
            output_path = os.path.join(tmpdir, "out.gff3")
            report_path = os.path.join(tmpdir, "report.txt")
            write_revision_file(revision_path, rows=[])

            with mock.patch.object(revision, "Gff3", return_value=fake_gff):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    revision.main(
                        gff_file="input.gff3",
                        revision_file=revision_path,
                        output_gff=output_path,
                        report_file=report_path,
                        auto=True,
                    )

        self.assertEqual(child1["attributes"]["replace"], ["A"])
        self.assertEqual(child2["attributes"]["replace"], ["NA"])


if __name__ == "__main__":
    unittest.main()