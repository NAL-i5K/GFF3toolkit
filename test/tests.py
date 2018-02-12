import unittest
from subprocess import check_output, STDOUT
from os import path, remove

ROOT_DIR = path.abspath(path.dirname(path.dirname(__file__)))
BIN_DIR = path.join(ROOT_DIR, 'bin')
EXAMPLE_DIR = path.join(ROOT_DIR, 'example_file')
TEST_DIR = path.join(ROOT_DIR, 'test')


class GFF3_QC_TestCase(unittest.TestCase):
    def test(self):
        output_file_path = path.join(TEST_DIR, 'report.txt')
        try:
            output = check_output(
                [
                    'python', path.join(BIN_DIR, 'gff3_QC.py'),
                    '-g', path.join(EXAMPLE_DIR, 'example.gff3'),
                    '-f', path.join(EXAMPLE_DIR, 'reference.fa'),
                    '-o', output_file_path 
                ],
                stderr=STDOUT)
            with open(output_file_path) as f:
                num_lines = 0
                for line in f:
                    num_lines += 1
            self.assertEqual(num_lines, 22) 
        finally:
            try:
                remove(output_file_path)
            finally:
                pass


if __name__ == '__main__':
    unittest.main()
