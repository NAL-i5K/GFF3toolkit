gff3tool/bin/gff3_QC.py -g example_file/example.gff3 -f example_file/reference.fa -o error.txt
gff3tool/bin/gff3_fix.py -qc_r error.txt -g example_file/example.gff3 -og corrected.gff3
gff3tool/bin/gff3_merge.py -g1 example_file/new_models.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -r merged_report.txt
gff3tool/bin/gff3_merge.py -g1 example_file/new_models.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -u1 example_file/u1.txt -u2 example_file/u2.txt -r merged_report.txt
gff3tool/bin/gff3_merge.py -g1 example_file/new_models.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -u1 example_file/u1.txt -r merged_report.txt
gff3tool/bin/gff3_merge.py -g1 example_file/new_models.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -u2 example_file/u2.txt -r merged_report.txt
gff3tool/bin/gff3_merge.py -g1 example_file/new_models_w_replace.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -r merged_report.txt -noAuto
gff3tool/bin/gff3_sort.py -g example_file/example.gff3 -og example-sorted.gff3
gff3tool/bin/gff3_to_fasta.py -g example_file/example.gff3 -f example_file/reference.fa -st all -d simple -o test_sequences
