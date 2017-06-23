# gff3-sort.py 

Sort features in a gff3 file by according to their order on a scaffold, their coordinates on a scaffold, and parent-child relationships.

## Inputs:
1. GFF3 file: Specify the file name with the -g argument

## Outputs:
1. Sorted GFF3 file: Specify the file name with the -og argument
    - All related features (with parent-child relationships) are separated by `###` directives for easier downstream parsing

## Usage:
1. Specify the input, output file names and options using short arguments:
    - `python2.7 gff3-sort.py -g example_file/annotations.gff -og example_file/annotations_sorted.gff`
2. Specify the input, output file names and options using long arguments:
    - `python2.7 gff3-sort.py --gff_file example_file/annotations.gff --output_gff example_file/annotations_sorted.gff`

## Optional arguments:

1. -h, --help            
    - show this help message and exit
2. -g GFF_FILE, --gff_file GFF_FILE
    - GFF3 file that you would like to sort.
3. -og OUTPUT_GFF, --output_gff OUTPUT_GFF
    - Sorted GFF3 file
4. -v, --version         
    - show program's version number and exit
