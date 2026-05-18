import unittest
from collections import defaultdict
from unittest import mock

from gff3tool.lib import id_processor


class DummyGFF:
    def __init__(self, line_count=0):
        self.lines = [{} for _ in range(line_count)]
        self.features = defaultdict(list)
        self.removed = []

    def remove(self, model):
        self.removed.append(model)

    def collect_descendants(self, line):
        descendants = []
        for child in line.get("children", []):
            descendants.append(child)
            descendants.extend(self.collect_descendants(child))
        return descendants


class TestIdProcessor(unittest.TestCase):
    def _build_nested_model(self, root_id="LOC0001"):
        utr = {
            "type": "UTR",
            "attributes": {"ID": "utr1", "Parent": [f"{root_id}-RA-exon"], "Name": "utr1"},
            "parents": [],
            "children": [],
            "line_index": 2,
        }
        exon = {
            "type": "exon",
            "attributes": {"ID": f"{root_id}-RA-exon", "Parent": [f"{root_id}-RA"], "Name": f"{root_id}-RA-exon"},
            "parents": [],
            "children": [utr],
            "line_index": 1,
        }
        transcript = {
            "type": "mRNA",
            "attributes": {"ID": f"{root_id}-RA", "Parent": [root_id], "Name": f"{root_id}-RA"},
            "parents": [],
            "children": [exon],
            "line_index": 0,
        }
        root = {
            "type": "gene",
            "attributes": {"ID": root_id, "Name": root_id},
            "children": [transcript],
            "line_index": 0,
        }
        transcript["parents"] = [[root]]
        exon["parents"] = [[transcript]]
        utr["parents"] = [[exon]]
        return root

    def test_idgenerator_zero_pads_and_increments(self):
        result = id_processor.idgenerator("GENE", 9, 4)
        self.assertEqual(result["ID"], "GENE0010")
        self.assertEqual(result["maxnum"], 10)

    def test_simple_id_replace_updates_numeric_portion(self):
        model = {"type": "mRNA", "attributes": {"ID": "ID0001-RA"}}
        id_processor.simpleIDreplace(model, "ID0123")
        self.assertEqual(model["attributes"]["ID"], "ID0123-RA")

    def test_simple_id_replace_assigns_id_when_missing(self):
        model = {"type": "gene", "attributes": {}}
        id_processor.simpleIDreplace(model, "LOC0007")
        self.assertEqual(model["attributes"]["ID"], "LOC0007gene")

    def test_new_parent_model_sets_id_name_and_line_index(self):
        oldmodel = {
            "attributes": {"ID": "old1", "Name": "old1"},
            "children": [{"attributes": {"ID": "child"}}],
            "line_index": 3,
        }
        gff = DummyGFF(line_count=5)

        new_model = id_processor.newParentModel(oldmodel, "new1", gff)

        self.assertEqual(new_model["attributes"]["ID"], "new1")
        self.assertEqual(new_model["attributes"]["Name"], "new1")
        self.assertEqual(new_model["line_index"], 5)
        self.assertEqual(new_model["children"], [])

    def test_new_child_model_resets_parent_links_and_children(self):
        ochild = {
            "type": "mRNA",
            "attributes": {"ID": "LOC0001-RA", "Parent": ["old_parent"], "Name": "LOC0001-RA"},
            "parents": [[{"attributes": {"ID": "old_parent"}}]],
            "children": [{"attributes": {"ID": "LOC0001-RA-exon"}}],
            "line_index": 0,
        }
        gff = DummyGFF(line_count=8)

        nchild = id_processor.newChildModel(ochild, "LOC0002", gff)

        self.assertEqual(nchild["line_index"], 8)
        self.assertEqual(nchild["parents"], [])
        self.assertEqual(nchild["attributes"]["Parent"], [])
        self.assertEqual(nchild["attributes"]["ID"], "LOC0002-RA")
        self.assertEqual(nchild["attributes"]["Name"], "LOC0002-RA")
        self.assertEqual(nchild["children"], [])

    def test_idprocessing_removes_models_marked_removed(self):
        root = {
            "line_type": "feature",
            "attributes": {"ID": "LOC0001"},
            "children": [],
        }
        removed_model = {
            "line_type": "feature",
            "attributes": {"ID": "LOC0002", "modified_track": "removed"},
            "children": [],
        }
        gff = DummyGFF()
        gff.lines = [root, removed_model]

        id_processor.IDprocessing(gff)

        self.assertEqual(gff.removed, [removed_model])
        self.assertNotIn("modified_track", removed_model["attributes"])

    def test_idprocessing_calls_newnreplace_for_merge_track(self):
        child = {"attributes": {"ID": "LOC0003-RA"}, "children": []}
        model = {
            "line_type": "feature",
            "attributes": {"ID": "LOC0003", "modified_track": "geneA_s1_geneB_s2"},
            "children": [child],
        }
        root = {
            "line_type": "feature",
            "attributes": {"ID": "LOC0001"},
            "children": [child],
        }
        gff = DummyGFF()
        gff.lines = [root, model]

        with mock.patch.object(id_processor, "idgenerator", return_value={"ID": "LOC0004", "maxnum": 4}) as gen_mock, \
            mock.patch.object(id_processor, "newNreplaceModel", autospec=True) as replace_mock:
            id_processor.IDprocessing(gff)

        gen_mock.assert_called_once_with("LOC", 3, 4)
        replace_mock.assert_called_once_with(model, "LOC0004", gff)

    def test_idprocessing_calls_newnreplace_for_split_track(self):
        child = {"attributes": {"ID": "LOC0005-RA"}, "children": []}
        model = {
            "line_type": "feature",
            "attributes": {"ID": "LOC0005", "modified_track": "geneX.s1"},
            "children": [child],
        }
        root = {
            "line_type": "feature",
            "attributes": {"ID": "LOC0001"},
            "children": [child],
        }
        gff = DummyGFF()
        gff.lines = [root, model]

        with mock.patch.object(id_processor, "idgenerator", return_value={"ID": "LOC0006", "maxnum": 6}) as gen_mock, \
            mock.patch.object(id_processor, "newNreplaceModel", autospec=True) as replace_mock:
            id_processor.IDprocessing(gff)

        gen_mock.assert_called_once_with("LOC", 5, 4)
        replace_mock.assert_called_once_with(model, "LOC0006", gff)

    def test_ncbi_naming_system_assigns_root_child_and_cds_attributes(self):
        cds = {
            "line_type": "feature",
            "type": "CDS",
            "attributes": {"ID": "LOC0001-RA-CDS"},
            "children": [],
        }
        mrna = {
            "line_type": "feature",
            "type": "mRNA",
            "attributes": {"ID": "LOC0001-RA", "Parent": ["LOC0001"], "Name": "product name"},
            "children": [cds],
        }
        cds["attributes"]["Parent"] = ["LOC0001-RA"]
        root = {
            "line_type": "feature",
            "type": "gene",
            "attributes": {"ID": "LOC0001"},
            "children": [mrna],
        }
        gff = DummyGFF()
        gff.lines = [root, mrna, cds]

        id_processor.ncbiNamingSystem(gff, "TAG")

        self.assertEqual(root["attributes"]["locus_tag"], "TAG_LOC0001")
        self.assertEqual(mrna["attributes"]["transcript_id"], "LOC0001-RA")
        self.assertEqual(mrna["attributes"]["protein_id"], "LOC0001-PA")
        self.assertEqual(cds["attributes"]["transcript_id"], "LOC0001-RA")
        self.assertEqual(cds["attributes"]["protein_id"], "LOC0001-PA")
        self.assertEqual(cds["attributes"]["product"], "product name")

    def test_new_model_threads_nested_descendants_into_new_graph(self):
        oldmodel = self._build_nested_model("LOC0001")
        gff = DummyGFF()

        with mock.patch("builtins.print"):
            id_processor.newModel(oldmodel, "LOC0002", gff)

        self.assertIn("LOC0002", gff.features)
        new_root = gff.features["LOC0002"][0]
        self.assertEqual(new_root["attributes"]["ID"], "LOC0002")
        self.assertEqual(len(new_root["children"]), 1)
        self.assertEqual(new_root["children"][0]["attributes"]["Parent"], ["LOC0002"])
        generated_utr = [line for line in gff.lines if line.get("type") == "UTR" and "LOC0002" in line["attributes"].get("ID", "")]
        self.assertTrue(generated_utr)

    def test_general_new_model_uses_eof_index_when_id_already_exists(self):
        oldmodel = self._build_nested_model("LOC0003")
        gff = DummyGFF(line_count=2)
        gff.features["LOC0003"].append({"attributes": {"ID": "LOC0003"}})

        with mock.patch("builtins.print"):
            id_processor.general_newModel(oldmodel, gff)

        new_root = gff.lines[2]
        self.assertEqual(new_root["attributes"]["ID"], "2")
        self.assertIn("2", gff.features)
        self.assertTrue(new_root["children"])

    def test_new_nreplace_model_replaces_old_model_and_removes_original(self):
        oldmodel = self._build_nested_model("LOC0007")
        gff = DummyGFF()

        with mock.patch("builtins.print"):
            id_processor.newNreplaceModel(oldmodel, "LOC0008", gff)

        self.assertIn(oldmodel, gff.removed)
        self.assertIn("LOC0008", gff.features)
        self.assertEqual(gff.features["LOC0008"][0]["attributes"]["ID"], "LOC0008")


if __name__ == "__main__":
    unittest.main()
