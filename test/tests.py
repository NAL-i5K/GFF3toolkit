import unittest
from subprocess import check_output, STDOUT
from os import path, remove

ROOT_DIR = path.abspath(path.dirname(path.dirname(__file__)))
BIN_DIR = path.join(ROOT_DIR, 'bin')
EXAMPLE_DIR = path.join(ROOT_DIR, 'example_file')
TEST_DIR = path.join(ROOT_DIR, 'test')


class GFF3_QC_TestCase(unittest.TestCase):
    def test(self):
        output_file_path = path.join(TEST_DIR, 'report_gff3_QC.txt')
        try:
            output = check_output(
                [
                    'python', path.join(BIN_DIR, 'gff3_QC.py'),
                    '-g', path.join(EXAMPLE_DIR, 'example.gff3'),
                    '-f', path.join(EXAMPLE_DIR, 'reference.fa'),
                    '-o', output_file_path
                ],
                stderr=STDOUT)
            self.assertTrue(output)
            with open(output_file_path) as f:
                num_lines = 0
                for _ in f:
                    num_lines += 1
            #  header + expected number of errors caught
            self.assertEqual(num_lines, 22)
        finally:
            try:
                remove(output_file_path)
            finally:
                pass


class GFF3_Sort_TestCase(unittest.TestCase):
    def test(self):
        input_file_path = path.join(EXAMPLE_DIR, 'example.gff3')
        output_file_path = path.join(TEST_DIR, 'example_sorted.gff3')
        try:
            output = check_output(
                [
                    'python', path.join(BIN_DIR, 'gff3_sort.py'),
                    '-g', input_file_path,
                    '-og', output_file_path
                ],
                stderr=STDOUT)
            self.assertTrue(output)
            with open(input_file_path) as f:
                input_num_lines = 0
                for line in f:
                    if not line.startswith('#'):
                        input_num_lines += 1
            with open(output_file_path) as f:
                output_num_lines = 0
                for line in f:
                    if not line.startswith('#'):
                        output_num_lines += 1
            # number of lines of output file should be the same
            # as orginal ones
            self.assertEqual(output_num_lines, input_num_lines)
        finally:
            try:
                remove(output_file_path)
            finally:
                pass


if __name__ == '__main__':
    unittest.main()
