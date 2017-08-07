# gff3-sort.py 

Sort features in a gff3 file by according to their order on a scaffold, their coordinates on a scaffold, and parent-child relationships.

## Inputs:
1. GFF3 file: Specify the file name with the -g argument

## Outputs:
1. Sorted GFF3 file: Specify the file name with the -og argument
    - All related features (with parent-child relationships) are separated by `###` directives for easier downstream parsing

## Usage:
1. Specify the input, output file names and options using short arguments:
    - `python2.7 bin/gff3_sort.py -g example_file/example.gff3 -og example_file/example_sorted.gff`
2. Specify the input, output file names and options using long arguments:
    - `python2.7 bin/gff3_sort.py --gff_file example_file/example.gff3 --output_gff example_file/example_sorted.gff`

## Optional arguments:

1. -h, --help            
    - show this help message and exit
2. -g GFF_FILE, --gff_file GFF_FILE
    - GFF3 file that you would like to sort.
3. -og OUTPUT_GFF, --output_gff OUTPUT_GFF
    - Sorted GFF3 file
4. -v, --version         
    - show program's version number and exit
