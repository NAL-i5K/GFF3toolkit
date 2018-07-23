# gff3_QC readme

## Usage 

gff3_QC.py [-h] [-g GFF] [-f FASTA] [-noncg] [-i] [-n ALLOWED_NUM_OF_N]   
[-t [CHECK_N_FEATURE_TYPES [CHECK_N_FEATURE_TYPES ...]]] [-o OUTPUT] [-v]

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
`gff3_QC -g example_file/example.gff3 -f example_file/reference.fa -o test`

or

`gff3_QC --gff example_file/example.gff3 --fasta example_file/reference.fa --output test`

## Optional arguments

1.  -h, --help            
    - show this help message and exit
2.  -g GFF, --gff GFF     
    - Genome annotation file, gff3 format
3.  -f FASTA, --fasta FASTA
    - Genome sequences, fasta format
4.  -noncg, --noncanonical_gene 
    - gff3 file is not formatted in the canonical gene model format.  
5.  -i, --initial_phase   
    - Check whether initial CDS phase is 0 (default - no check)
6.  -n ALLOWED_NUM_OF_N, --allowed_num_of_n ALLOWED_NUM_OF_N  
    - Max number of Ns allowed in a feature, anything more will be reported as an error (default: 0)  
7.  -t [CHECK_N_FEATURE_TYPES [CHECK_N_FEATURE_TYPES ...]], --check_n_feature_types [CHECK_N_FEATURE_TYPES [CHECK_N_FEATURE_TYPES ...]]
    - Count the number of Ns in each feature with the type specified, multiple types may be specified, ex: -t CDS exon (default: "CDS")    
8.  -o OUTPUT, --output OUTPUT
    - output file name (default: report.txt)
9.  -v, --version         
    - show program's version number and exit

## More information
- [gff3_QC.py full documentation](Detection-of-GFF3-format-errors.md)
