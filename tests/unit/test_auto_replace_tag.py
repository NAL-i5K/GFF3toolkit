import os
import tempfile
import unittest
from unittest import mock

from gff3tool.lib.gff3_merge import auto_replace_tag


class _DummyProc:
    def __init__(self, cmd):
        self.cmd = cmd

    def wait(self):
        return 0


class FakeGff:
    def __init__(self, lines):
        self.lines = lines
        self.written_path = None

    def write(self, path):
        self.written_path = path
        with open(path, "w") as fh:
            fh.write("##gff-version 3\n")


def _make_root_with_transcript(root_id, tx_id, has_cds=False):
    child_feature = {
        "line_type": "feature",
        "attributes": {"ID": tx_id, "Parent": [root_id], "replace": ["NA"]},
        "type": "mRNA",
        "children": [],
    }
    if has_cds:
        child_feature["children"].append({"type": "CDS"})
    else:
        child_feature["children"].append({"type": "exon"})

    root = {
        "line_type": "feature",
        "attributes": {"ID": root_id, "replace": ["NA"]},
        "type": "gene",
        "children": [child_feature],
    }
    return [root]


class TestAutoReplaceTag(unittest.TestCase):
    def _fake_popen_factory(self, tmpdir):
        def _fake_popen(cmd, stdout=None):
            if "-out" in cmd:
                out_file = cmd[cmd.index("-out") + 1]
                with open(out_file, "w") as fh:
                    fh.write("")

            if cmd and cmd[0] == "perl":
                script = os.path.basename(cmd[1])
                if script == "create_annotation_summaries_nov21-7.pl":
                    with open(cmd[4], "w") as fh:
                        fh.write("")
                elif script == "find_match.pl":
                    with open(cmd[5], "w") as fh:
                        fh.write("")
                elif script == "gen_spreadsheet.pl":
                    with open(cmd[5], "w") as fh:
                        fh.write("")

            return _DummyProc(cmd)

        return _fake_popen

    def test_main_default_path_runs_extract_and_alignment_pipeline(self):
        gff1 = FakeGff(_make_root_with_transcript("gene1", "tx1", has_cds=False))
        gff2 = FakeGff(_make_root_with_transcript("gene2", "tx2", has_cds=True))

        with tempfile.TemporaryDirectory() as tmpdir:
            gff1_path = os.path.join(tmpdir, "new.gff3")
            gff2_path = os.path.join(tmpdir, "ref.gff3")
            fasta_path = os.path.join(tmpdir, "ref.fa")
            for p in [gff1_path, gff2_path, fasta_path]:
                with open(p, "w") as fh:
                    fh.write("\n")

            with mock.patch.object(auto_replace_tag, "Gff3", autospec=True, side_effect=[gff1, gff2]), \
                mock.patch.object(auto_replace_tag.gff3_to_fasta, "main", autospec=True) as to_fasta_main, \
                mock.patch.object(auto_replace_tag.subprocess, "Popen", side_effect=self._fake_popen_factory(tmpdir)) as popen_mock:
                auto_replace_tag.main(
                    gff1=gff1_path,
                    gff2=gff2_path,
                    fasta=fasta_path,
                    outdir=tmpdir,
                    scode="TEMP",
                    logger=mock.Mock(),
                    all_assign=False,
                    user_defined1=None,
                    user_defined2=None,
                )

            self.assertEqual(to_fasta_main.call_count, 6)
            self.assertTrue(any("makeblastdb" in " ".join(c.args[0]) for c in popen_mock.call_args_list))
            self.assertTrue(any("blastn" in " ".join(c.args[0]) for c in popen_mock.call_args_list))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "check1.txt")))

    def test_main_all_assign_rewrites_gff_and_drops_replace_attrs(self):
        gff1 = FakeGff(_make_root_with_transcript("gene1", "tx1", has_cds=False))
        gff2 = FakeGff(_make_root_with_transcript("gene2", "tx2", has_cds=True))

        with tempfile.TemporaryDirectory() as tmpdir:
            gff1_path = os.path.join(tmpdir, "new.gff3")
            gff2_path = os.path.join(tmpdir, "ref.gff3")
            fasta_path = os.path.join(tmpdir, "ref.fa")
            for p in [gff1_path, gff2_path, fasta_path]:
                with open(p, "w") as fh:
                    fh.write("\n")

            with mock.patch.object(auto_replace_tag, "Gff3", autospec=True, side_effect=[gff1, gff2]), \
                mock.patch.object(auto_replace_tag.gff3_to_fasta, "main", autospec=True), \
                mock.patch.object(auto_replace_tag.subprocess, "Popen", side_effect=self._fake_popen_factory(tmpdir)):
                auto_replace_tag.main(
                    gff1=gff1_path,
                    gff2=gff2_path,
                    fasta=fasta_path,
                    outdir=tmpdir,
                    scode="TEMP",
                    logger=mock.Mock(),
                    all_assign=True,
                    user_defined1=None,
                    user_defined2=None,
                )

            self.assertIsNotNone(gff1.written_path)
            self.assertTrue(gff1.written_path.endswith(os.path.join("tmp", "gff1_mod.gff3")))
            for line in gff1.lines:
                self.assertNotIn("replace", line["attributes"])


if __name__ == "__main__":
    unittest.main()