# gff3_to_fasta

Extract sequences from specific regions of genome based on gff file.

## Usage

gff3_to_fasta.py [-h] [-g GFF] [-f FASTA] [-st SEQUENCE_TYPE] [-d DEFLINE] [-o OUTPUT_PREFIX] [-noQC] [-v]

## Testing enviroment
1. Python 2.7

## Required inputs
1. GFF3: specify the file name with the -g argument
2. Fasta file: specify the file name with the -f argument. This file **must** be the Fasta file that the GFF3 seqids and coordinates refer to. For more information, refer to the [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md).
3. Output prefix: specify with the -o argument. All resulting fasta files will contain this prefix. 

## Outputs
1. Fasta formatted sequence file based on the gff3 file.

## Example command
1. Specify the input, output file names and options using short arguments:
    - `python2.7 bin/gff3_to_fasta.py -g example_file/example.gff3 -f example_file/reference.fa -st all -d simple -o test_sequences`

## Optional arguments
    
1. -h, --help            
    - show this help message and exit
2. -g GFF, --gff GFF     
    - Genome annotation file in GFF3 format
3. -f FASTA, --fasta FASTA
    - Genome sequences in FASTA format
4. -st SEQUENCE_TYPE, --sequence_type SEQUENCE_TYPE
    - Type of sequences you would like to extract: 
        * "all" - FASTA files for all types of sequences listed below;
        * "gene" - gene sequence for each record;
        * "exon" - exon sequence for each record;
        * "pre_trans" - genomic region of a transcript model (premature transcript);
        * "trans" - spliced transcripts (only exons included);
        * "cds" - coding sequences;
        * "pep" - peptide sequences.
5. -d DEFLINE, --defline DEFLINE
    - Defline format in the output FASTA file:
        * "simple" - only ID is shown in the defline;
        * "complete" - complete information of the feature is shown in the defline.
6. -o OUTPUT_PREFIX, --output_prefix OUTPUT_PREFIX
    - Prefix of output file name
7. -noQC, --quality_control
    - Specify this option if you do not want to excute quality control for gff file. (default: QC is executed)
8. -v, --version        
    - Show program version number and exit

