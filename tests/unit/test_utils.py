import os
import tempfile
import unittest

from gff3tool.lib import utils


class TestUtils(unittest.TestCase):
    def test_remove_files_from_list_removes_existing_and_ignores_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = os.path.join(tmpdir, 'exists.txt')
            missing = os.path.join(tmpdir, 'missing.txt')
            with open(existing, 'w', encoding='utf-8') as handle:
                handle.write('content')

            utils.remove_files_from_list([existing, missing])

            self.assertFalse(os.path.exists(existing))
            self.assertFalse(os.path.exists(missing))


if __name__ == '__main__':
    unittest.main()