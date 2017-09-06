# gff-QC.py

## Usage 

gff-QC.py [-h] [-g GFF] [-f FASTA] [-i] [-o OUTPUT] [-v]

## Testing environment

Python 2.7

## Inputs
1. GFF3: Specify the file name with the -g or --gff argument. Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9.
2. Fasta file: Specify the file name with the -f or --fasta argument. This file **must** be the Fasta file that the GFF3 seqids and coordinates refer to. For more information, refer to the [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md).

## Outputs
1. Error report for the input GFF3 file
    * Line_num: Line numbers of the found problematic models in the input GFF3 file.
    * Error_code: Error codes for the found problematic models. Please refer to lib/ERROR/ERROR.py to see the full list of Error_code and the corresponding Error_tag.
        * Error_tag: Detail of the found errors for the problematic models. Please refer to lib/ERROR/ERROR.py to see the full list of Error_code and the corresponding Error_tag.

## Quick start
`python2.7 bin/gff-QC.py -g example_file/example.gff3 -f example_file/reference.fa -o test`

or

`python2.7 bin/gff-QC.py --gff example_file/example.gff3 --fasta example_file/reference.fa --output test`

## Optional arguments

1.  -h, --help            
    - show this help message and exit
2.  -g GFF, --gff GFF     
    - Genome annotation file, gff3 format
3.  -f FASTA, --fasta FASTA
    - Genome sequences, fasta format
4. -i, --initial_phase   Check whether initial CDS phase is 0 (default - no check)
5.  -o OUTPUT, --output OUTPUT
    - output file name (default: report.txt)
6.  -v, --version         
    - show program's version number and exit

## More information
- [gff-QC.py full documentation](https://github.com/NAL-i5K/GFF3toolkit/wiki/Detection-of-GFF3-format-errors)
