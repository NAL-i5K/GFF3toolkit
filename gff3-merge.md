# gff3-merge.py

## Usage 

gff3-merge.py [-h] [-g1 GFF_FILE1] [-g2 GFF_FILE2] [-f FASTA] [-og OUTPUT_GFF] [-r REPORT_FILE] [-noAuto] [-v]

## Testing environment

1. Python 2.7
2. Perl v5.16.3

## Inputs
1. New or update models in GFF3 format: Specify the file name with the -g1 or --gff_file1 argument. Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9.
2. Reference models in GFF3 format: Specify the file name with the -g2 or --gff_file2 argument. This file **must** be the GFF3 file that the new or update models (-g1) refer to. Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9.
3. Fasta file: Specify the file name with the -f or --fasta argument. This file **must** be the Fasta file that the GFF3 seqids and coordinates refer to. For more information, refer to the [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md).

## Outputs
1. .gff: A merged gff3 file
2. .txt: Merge log file

## Quick start
* Merge the two file with auto-assignment of replace tags (default)
    `python2.7 GFF3toolkit/bin/gff3-merge.py -g1 GFF3toolkit/example_file/gff3-merge_example/new_models.gff3 -g2 GFF3toolkit/example_file/gff3-merge_example/reference.gff3 -f GFF3toolkit/example_file/gff3-merge_example/reference.fa -og merged.gff -r merged_report.txt`

* If your gff files have assigned proper replace tags at column 9 (Format: replace=[Transcript ID]), you could merge the two gff files wihtout auto-assignment of tags.
    `python2.7 GFF3toolkit/bin/gff3-merge.py -g1 GFF3toolkit/example_file/gff3-merge_example/new_models.gff3 -g2 GFF3toolkit/example_file/gff3-merge_example/reference.gff3 -f GFF3toolkit/example_file/gff3-merge_example/reference.fa -og merged.gff -r merged_report.txt -noAuto`

## Optional arguments

1.  -h, --help            
    - show this help message and exit
2.  -og OUTPUT_GFF, --output_gff OUTPUT_GFF
    - The merged GFF3 file (default: merged.gff)
3.  -r REPORT_FILE, --report_file REPORT_FILE
    - Log file for the intergration (default: merge_report.txt)
4.  -noAuto, --auto_assignment
    - Turn off the auto-assignemnt of replace tags, if you have had the replace tags in your update gff (default: Automatically assign replace tags and then merge the gff files)
5.  -v, --version         
    - show program's version number and exit

