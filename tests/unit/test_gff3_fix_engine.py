import io
import unittest
from collections import defaultdict
from unittest import mock

from gff3tool.lib.gff3_fix import fix


class FakeGff:
    def __init__(self, lines, descendants=None):
        self.lines = lines
        self._descendants = descendants or {}

    def collect_descendants(self, parent):
        return self._descendants.get(id(parent), [])

    def collect_roots(self, line):
        return line.get("roots", [line])


class FakeWritableGff(FakeGff):
    def __init__(self, lines, features=None, fasta_external=None, fasta_embedded=None):
        super().__init__(lines)
        self.features = features or defaultdict(list)
        self.fasta_external = fasta_external or {}
        self.fasta_embedded = fasta_embedded or {}

    def descendants(self, root):
        return root.get("children", [])


class TestGff3FixEngine(unittest.TestCase):
    def test_fasta_dict_to_file_respects_line_limit(self):
        fasta = {"chr1": {"header": ">chr1", "seq": "AACCGGTT"}}
        out = io.StringIO()

        fix.fasta_dict_to_file(fasta, out, line_char_limit=4)

        self.assertEqual(out.getvalue(), ">chr1\nAACC\nGGTT\n")

    def test_fix_attributes_normalizes_and_filters_values(self):
        line = {
            "line_status": "normal",
            "line_raw": "ctg123\tsrc\tgene\t1\t10\t.\t+\t.\t=bad;Name=;Dbxref=A, B;Dbxref=B;Foo=bar;Target=t1 1 20 +",
            "attributes": {},
        }
        gff = FakeGff([line])

        fix.fix_attributes(gff3=gff, error_list=[[1]], logger=mock.Mock())

        attrs = gff.lines[0]["attributes"]
        self.assertEqual(set(attrs["Dbxref"]), {"A%2CB", "B"})
        self.assertEqual(attrs["foo"], "bar")
        self.assertIn("Target", attrs)
        self.assertEqual(attrs["Target"]["target_id"], "t1")
        self.assertEqual(attrs["Target"]["start"], 1)
        self.assertEqual(attrs["Target"]["end"], 20)
        self.assertNotIn("Name", attrs)

    def test_fix_phase_propagates_phase_across_cds(self):
        parent = {"attributes": {"ID": "tx1"}}
        non_cds = {
            "type": "exon",
            "line_index": 0,
            "phase": 0,
        }
        cds1 = {
            "type": "CDS",
            "line_raw": "cds1",
            "line_index": 1,
            "phase": 2,
            "strand": "+",
            "start": 1,
            "end": 3,
            "parents": [[parent]],
        }
        cds2 = {
            "type": "CDS",
            "line_raw": "cds2",
            "line_index": 2,
            "phase": 0,
            "strand": "+",
            "start": 10,
            "end": 12,
            "parents": [[parent]],
        }

        lines = [
            {"line_status": "normal", "phase": 0},
            {"line_status": "normal", "parents": [[parent]], "phase": 2},
            {"line_status": "normal", "parents": [[parent]], "phase": 0},
        ]
        gff = FakeGff(lines=lines, descendants={id(parent): [non_cds, cds1, cds2]})

        fix.fix_phase(
            gff3=gff,
            error_list=[[2]],
            line_num_dict={2: {"Esf0027": "Warning"}},
            logger=mock.Mock(),
        )

        self.assertEqual(gff.lines[0]["phase"], ".")
        self.assertEqual(gff.lines[1]["phase"], 2)
        self.assertEqual(gff.lines[2]["phase"], 2)

    def test_add_gff3_version_inserts_directive_at_top(self):
        lines = [
            {"line_index": 0, "line_raw": "a", "line_status": "normal", "parents": [], "children": []},
            {"line_index": 1, "line_raw": "b", "line_status": "normal", "parents": [], "children": []},
        ]
        gff = FakeGff(lines)

        fix.add_gff3_version(gff3=gff, logger=mock.Mock())

        self.assertEqual(gff.lines[0]["directive"], "##gff-version")
        self.assertEqual(gff.lines[1]["line_index"], 1)
        self.assertEqual(gff.lines[2]["line_index"], 2)

    def test_remove_directive_marks_lines_unknown(self):
        lines = [
            {"line_type": "directive"},
            {"line_type": "directive"},
        ]
        gff = FakeGff(lines)

        fix.remove_directive(gff3=gff, error_list=[[1, 2]], logger=mock.Mock())

        self.assertEqual(gff.lines[0]["line_type"], "unknown")
        self.assertEqual(gff.lines[1]["line_type"], "unknown")

    def test_fix_boundary_updates_parent_and_transcript_ranges(self):
        root = {
            "children": [],
            "start": 1,
            "end": 2,
        }
        child = {
            "children": [
                {"start": 10, "end": 11},
                {"start": 20, "end": 21},
            ],
            "start": 0,
            "end": 0,
        }
        root["children"] = [child]

        gff = FakeGff(lines=[])
        gff.collect_roots = mock.Mock(return_value=[root])

        fix.fix_boundary(gff3=gff, line=child, logger=mock.Mock())

        self.assertEqual(child["start"], 10)
        self.assertEqual(child["end"], 21)
        self.assertEqual(root["start"], 10)
        self.assertEqual(root["end"], 21)

    def test_fix_boundary_skips_removed_lines_in_error_mode(self):
        root = {
            "line_status": "normal",
            "children": [{"children": [{"start": 3, "end": 9}], "start": 0, "end": 0}],
            "start": 1,
            "end": 2,
        }
        line = {"line_status": "removed", "roots": [root]}
        gff = FakeGff(lines=[line])

        fix.fix_boundary(gff3=gff, error_list=[[1]], logger=mock.Mock())

        self.assertEqual(root["start"], 1)
        self.assertEqual(root["end"], 2)

    def test_remove_duplicate_trans_removes_transcript_and_root_when_empty(self):
        root = {"line_status": "normal", "roots": [], "children": []}
        transcript = {"line_status": "normal", "roots": [root], "children": []}
        exon = {"line_status": "normal", "roots": [root], "children": []}
        root["children"] = [transcript]
        gff = FakeGff(lines=[root, transcript, exon], descendants={id(transcript): [exon], id(root): [transcript, exon]})

        fix.remove_duplicate_trans(gff3=gff, error_list=[[1, 2]], logger=mock.Mock())

        self.assertEqual(transcript["line_status"], "removed")
        self.assertEqual(exon["line_status"], "removed")
        self.assertEqual(root["line_status"], "removed")

    def test_delete_model_removes_root_and_all_descendants(self):
        root = {"line_status": "normal", "roots": [], "children": []}
        transcript = {"line_status": "normal", "roots": [root], "children": []}
        cds = {"line_status": "normal", "roots": [root], "children": []}
        root["children"] = [transcript]
        gff = FakeGff(lines=[root, transcript, cds], descendants={id(root): [transcript, cds]})

        fix.delete_model(gff3=gff, error_list=[[2]], logger=mock.Mock())

        self.assertEqual(root["line_status"], "removed")
        self.assertEqual(transcript["line_status"], "removed")
        self.assertEqual(cds["line_status"], "removed")

    def test_pseudogene_relabels_types_and_removes_cds_branch(self):
        root = {"line_status": "normal", "type": "gene", "children": [], "roots": []}
        child = {"line_status": "normal", "type": "mRNA", "children": []}
        exon = {"line_status": "normal", "type": "exon", "children": []}
        cds = {"line_status": "normal", "type": "CDS", "children": []}
        cds_child = {"line_status": "normal", "type": "match_part", "children": []}
        child["children"] = [exon, cds]
        root["children"] = [child]
        line = {"line_status": "normal", "roots": [root]}
        gff = FakeGff(lines=[line], descendants={id(cds): [cds_child]})

        fix.pseudogene(gff3=gff, error_list=[[1]], logger=mock.Mock())

        self.assertEqual(root["type"], "pseudogene")
        self.assertEqual(child["type"], "pseudogenic_transcript")
        self.assertEqual(exon["type"], "pseudogenic_exon")
        self.assertEqual(cds["line_status"], "removed")
        self.assertEqual(cds_child["line_status"], "removed")

    def test_connected_components_groups_pairs(self):
        components = fix.connected_compoents(
            ["tx1", "tx2", "tx3", "tx4"],
            ["tx1 tx2", "tx2 tx3"],
        )

        as_sets = {frozenset(group) for group in components}
        self.assertIn(frozenset(["tx1", "tx2", "tx3"]), as_sets)
        self.assertIn(frozenset(["tx4"]), as_sets)

    def test_write_outputs_sequence_region_features_and_fasta(self):
        root = {
            "line_index": 0,
            "line_status": "normal",
            "line_type": "feature",
            "line_raw": "",
            "parents": [],
            "children": [],
            "seqid": "chr1",
            "source": "src",
            "type": "gene",
            "start": 1,
            "end": 4,
            "score": ".",
            "strand": "+",
            "phase": ".",
            "attributes": {"ID": "gene1", "Name": "gene1"},
        }
        features = defaultdict(list)
        features["gene1"].append(root)
        gff = FakeWritableGff(
            lines=[root],
            features=features,
            fasta_external={"chr1": {"header": ">chr1", "seq": "AACCGG"}},
        )
        out = io.StringIO()

        fix.write(gff3=gff, output_gff=out, embed_fasta=None, fasta_char_limit=3, logger=mock.Mock())
        value = out.getvalue()

        self.assertIn("##sequence-region chr1 1 6\n", value)
        self.assertTrue(
            "chr1\tsrc\tgene\t1\t4\t.\t+\t.\tID=gene1;Name=gene1\n" in value
            or "chr1\tsrc\tgene\t1\t4\t.\t+\t.\tName=gene1;ID=gene1\n" in value
        )
        self.assertIn("###\n", value)
        self.assertIn("##FASTA\n", value)
        self.assertIn(">chr1\nAAC\nCGG\n", value)

    def test_main_dispatches_to_expected_fixers(self):
        gff = object()
        error_dict = {
            "Esf0002": [[1]],
            "Emr0001": [[2]],
            "Esf0020": [[3]],
            "Esf0001": [[4]],
            "Ema0001": [[5]],
            "Ema0006": [[6]],
            "Esf0030": [[7]],
            "Ema0009": [[8]],
            "Emr0002": [[9]],
            "Esf0014": [[10]],
        }

        with mock.patch.object(fix, "delete_model", autospec=True) as delete_model, \
            mock.patch.object(fix, "remove_duplicate_trans", autospec=True) as remove_dup, \
            mock.patch.object(fix, "remove_directive", autospec=True) as remove_dir, \
            mock.patch.object(fix, "pseudogene", autospec=True) as pseudo, \
            mock.patch.object(fix, "fix_boundary", autospec=True) as boundary, \
            mock.patch.object(fix, "fix_phase", autospec=True) as phase, \
            mock.patch.object(fix, "fix_attributes", autospec=True) as attrs, \
            mock.patch.object(fix, "split", autospec=True) as split, \
            mock.patch.object(fix, "merge", autospec=True) as merge, \
            mock.patch.object(fix, "add_gff3_version", autospec=True) as add_version, \
            mock.patch.object(fix, "write", autospec=True) as write:
            fix.main(gff3=gff, output_gff="out.gff3", error_dict=error_dict, line_num_dict={}, logger=mock.Mock())

        delete_model.assert_called_once()
        remove_dup.assert_called_once()
        remove_dir.assert_called_once()
        pseudo.assert_called_once()
        boundary.assert_called_once()
        phase.assert_called_once()
        attrs.assert_called_once()
        split.assert_called_once()
        merge.assert_called_once()
        add_version.assert_called_once()
        write.assert_called_once_with(gff3=gff, output_gff="out.gff3", logger=mock.ANY)


if __name__ == "__main__":
    unittest.main()