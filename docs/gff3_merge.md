# gff3_merge.py

## Usage 

gff3_merge.py [-h] [-g1 GFF_FILE1] [-g2 GFF_FILE2] [-f FASTA] [-og OUTPUT_GFF] [-r REPORT_FILE] [-noAuto] [-v]

## Testing environment

1. Python 2.7
2. Perl v5.16.3

## Inputs
1. GFF3 file with new or modified annotations, to be merged into GFF3 file 2. Specify the file name with the -g1 or --gff_file1 argument. Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9. If replace tags are present (see below), these tags **must** refer to transcript/mRNA model IDs in the reference GFF3 file, specified by -g2. 
2. Reference models in GFF3 format: Specify the file name with the -g2 or --gff_file2 argument. The models from -g1 will be merged into this file, replacing models in -g2. Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9. If the reference GFF3 file contains gene models with multiple isoforms, please review the section "[Odd use cases](https://github.com/NAL-i5K/GFF3toolkit/wiki/Merge-two-GFF3-files#odd-use-cases)" below prior to running the program.
3. Fasta file: Specify the file name with the -f or --fasta argument. This file **must** be the Fasta file that the GFF3 seqids and coordinates in both GFF3 files refer to. For more information, refer to the [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md).

## Outputs
1. .gff: A merged gff3 file
2. .txt: Merge log file

## Quick start
* Merge the two files with auto-assignment of replace tags (default)
    `python2.7 GFF3toolkit/bin/gff3_merge.py -g1 GFF3toolkit/example_file/new_models.gff3 -g2 GFF3toolkit/example_file/reference.gff3 -f GFF3toolkit/example_file/reference.fa -og merged.gff -r merged_report.txt`

* If your GFF3 files have proper replace tags at column 9 (Format: replace=[Transcript ID]), you can merge the two GFF3 files without auto-assignment of replace tags.
    `python2.7 GFF3toolkit/bin/gff3_merge.py -g1 GFF3toolkit/example_file/new_models.gff3 -g2 GFF3toolkit/example_file/reference.gff3 -f GFF3toolkit/example_file/reference.fa -og merged.gff -r merged_report.txt -noAuto`

## Optional arguments

1.  -h, --help            
    - show this help message and exit
2.  -og OUTPUT_GFF, --output_gff OUTPUT_GFF
    - The merged GFF3 file (default: merged.gff)
3.  -r REPORT_FILE, --report_file REPORT_FILE
    - Log file for the integration (default: merge_report.txt)
4.  -noAuto, --auto_assignment
    - Turn off the auto-assignment of replace tags, if you have had the replace tags in your update gff (default: Automatically assign replace tags and then merge the gff files)
5.  -v, --version         
    - show program's version number and exit

## More information 
- [gff3_merge.py full documentation](https://github.com/NAL-i5K/GFF3toolkit/wiki/Merge-two-GFF3-files)
