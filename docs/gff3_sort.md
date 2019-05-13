# gff3_sort readme

Sort features in a gff3 file by according to their order on a scaffold, their coordinates on a scaffold, and parent-child relationships.

## Inputs:

1. GFF3 file: Specify the file name with the -g argument

## Outputs:

1. Sorted GFF3 file: Specify the file name with the -og argument
    - All related features (with parent-child relationships) are separated by `###` directives for easier downstream parsing

## Usage:

1. Specify the input, output file names and options using short arguments:
    - `gff3_sort -g example_file/example.gff3 -og example_file/example_sorted.gff`
2. Specify the input, output file names and options using long arguments:
    - `gff3_sort --gff_file example_file/example.gff3 --output_gff example_file/example_sorted.gff`

## Optional arguments:

1. -h, --help
    - show this help message and exit
2. -g GFF_FILE, --gff_file GFF_FILE
    - GFF3 file that you would like to sort.
3. -og OUTPUT_GFF, --output_gff OUTPUT_GFF
    - Sorted GFF3 file
4. -t, SORT_TEMPLATE, --sort_template SORT_TEMPLATE
    -  A file that indicates the sorting order of features within a gene model
5. -i, --isoform_sort
    - Sort multi-isoform gene models by feature type (default: False)
6. -v, --version
    - show program's version number and exit
7. -r, --reference
    - Sort seqID does not end with a number

## Example:

### Sort gff3 file without a sort template file
* example command:

`gff3_sort --gff_file example.gff3 --output_gff example_sort.gff3`

* Input gff3 file:

```shell
LGIB01000001.1  Gnomon  gene    52056   58768   .       +       .       ID=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna1;Parent=gene1
LGIB01000001.1  Gnomon  CDS     52056   52096   .       +       0       ID=cds1;Parent=rna1
LGIB01000001.1  Gnomon  exon    52056   52096   .       +       .       ID=id4;Parent=rna1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna2;Parent=gene1
LGIB01000001.1  Gnomon  CDS     52100   53000   .       +       0       ID=cds2;Parent=rna2
LGIB01000001.1  Gnomon  exon    52056   53000   .       +       .       ID=id19;Parent=rna2
```

* Output gff3 file:

```shell
LGIB01000001.1  Gnomon  gene    52056   58768   .       +       .       ID=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna1;Parent=gene1
LGIB01000001.1  Gnomon  exon    52056   52096   .       +       .       ID=id4;Parent=rna1
LGIB01000001.1  Gnomon  CDS     52056   52096   .       +       0       ID=cds1;Parent=rna1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna2;Parent=gene1
LGIB01000001.1  Gnomon  exon    52056   53000   .       +       .       ID=id19;Parent=rna2
LGIB01000001.1  Gnomon  CDS     52100   53000   .       +       0       ID=cds2;Parent=rna2
```

### Sort gff3 file with a sort template file

* sort template file: A file that indicates the sorting order of features within a gene model. Feature type with the same sorting order should be in the same line and split by space.

```shell
gene pseudogene
mRNA
exon
CDS
```

#### Sort gff3 file without --isoform_sort

* example command:

`gff3_sort --gff_file example.gff3 --sort_template sort_template.txt --output_gff example_sort.gff3`

* Output gff3 file:

```shell
LGIB01000001.1  Gnomon  gene    52056   58768   .       +       .       ID=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna1;Parent=gene1
LGIB01000001.1  Gnomon  exon    52056   52096   .       +       .       ID=id4;Parent=rna1
LGIB01000001.1  Gnomon  CDS     52056   52096   .       +       0       ID=cds1;Parent=rna1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna2;Parent=gene1
LGIB01000001.1  Gnomon  exon    52056   53000   .       +       .       ID=id19;Parent=rna2
LGIB01000001.1  Gnomon  CDS     52100   53000   .       +       0       ID=cds2;Parent=rna2
```

**Note:**

If not all the feature type are documented in the sort template file. gff3_sort will sort features by level(1st-level, 2nd-level, and etc) and then by the order in sort template file.

* sort template file:

```shell
gene pseudogene
CDS
```

* Output gff3 file:

```
LGIB01000001.1  Gnomon  gene    52056   58768   .       +       .       ID=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna1;Parent=gene1
LGIB01000001.1  Gnomon  CDS     52056   52096   .       +       0       ID=cds1;Parent=rna1
LGIB01000001.1  Gnomon  exon    52056   52096   .       +       .       ID=id4;Parent=rna1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna2;Parent=gene1
LGIB01000001.1  Gnomon  CDS     52100   53000   .       +       0       ID=cds2;Parent=rna2
LGIB01000001.1  Gnomon  exon    52056   53000   .       +       .       ID=id19;Parent=rna2
```

#### Sort gff3 file with --isoform_sort

* example command:

`gff3_sort --gff_file example.gff3 --sort_template sort_template.txt --isoform_sort --output_gff example_sort.gff3`

* Output gff3 file:

```shell
LGIB01000001.1  Gnomon  gene    52056   58768   .       +       .       ID=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna1;Parent=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna2;Parent=gene1
LGIB01000001.1  Gnomon  exon    52056   53000   .       +       .       ID=id19;Parent=rna2
LGIB01000001.1  Gnomon  exon    52056   52096   .       +       .       ID=id4;Parent=rna1
LGIB01000001.1  Gnomon  CDS     52056   52096   .       +       0       ID=cds1;Parent=rna1
LGIB01000001.1  Gnomon  CDS     52100   53000   .       +       0       ID=cds2;Parent=rna2
```

**Note:**

If not all the feature type are documented in the sort template file. gff3_sort will sort features by the order in sort template file and then by level(1st-level, 2nd-level, and etc).

* sort template file:

```shell
gene pseudogene
CDS
```

* Output gff3 file:

```
LGIB01000001.1  Gnomon  gene    52056   58768   .       +       .       ID=gene1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna1;Parent=gene1
LGIB01000001.1  Gnomon  CDS     52056   52096   .       +       0       ID=cds1;Parent=rna1
LGIB01000001.1  Gnomon  exon    52056   52096   .       +       .       ID=id4;Parent=rna1
LGIB01000001.1  Gnomon  mRNA    52056   58768   .       +       .       ID=rna2;Parent=gene1
LGIB01000001.1  Gnomon  CDS     52100   53000   .       +       0       ID=cds2;Parent=rna2
LGIB01000001.1  Gnomon  exon    52056   53000   .       +       .       ID=id19;Parent=rna2
```

## Assumptions:

1. Any features without a Parent attribute are 'root' features - the program will insert  directives (lines beginning with ##) above these features.
2. All child features occur after their respective Parent feature, but before new Parent features.
