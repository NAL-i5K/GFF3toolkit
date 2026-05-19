import unittest
from unittest import mock

from gff3tool.lib.gff3_fix import fix


class FakeGff:
    def __init__(self, lines, descendants=None):
        self.lines = lines
        self._descendants = descendants or {}

    def collect_descendants(self, parent):
        return self._descendants.get(id(parent), [])


class TestGff3FixEngine(unittest.TestCase):
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