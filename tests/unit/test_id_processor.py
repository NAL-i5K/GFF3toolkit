import unittest

from gff3tool.lib import id_processor


class DummyGFF:
    def __init__(self, line_count=0):
        self.lines = [{} for _ in range(line_count)]


class TestIdProcessor(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
