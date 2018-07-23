## Background  
The gff3_fix program fixes 30 error types detected by the program [gff3_QC.py](Detection-of-GFF3-format-errors.md). The section 'gff3_fix' lists all error types that currently can be fixed by the gff3_fix.py function (currently 30), including the method used for the fix. (Note that in some cases, this means removing the affected gene model). The section 'Fix function' describes the methods used to fix the error type in question. The section 'Currently no automatic fix available' lists the error types which gff3_fix currently does not handle.

## gff3_fix
|Error code|Error tag|Fix function|
|---|---|---|
Ema0001|Parent feature start and end coordinates exceed those of child features|fix_boundary
Ema0003|This feature is not contained within the parent feature coordinates|fix_boundary
Ema0005|Pseudogene has invalid child feature type|pseudogene
Ema0006|Wrong phase|fix_phase
Ema0007|CDS and parent feature on different strands|delete_model
Ema0009|Incorrectly merged gene parent? Isoforms that do not share coding sequences are found|split
Emr0001|Duplicate transcript found|remove_duplicate_trans
Emr0002|Incorrectly split gene parent?|merge
Esf0001|Feature type may need to be changed to pseudogene|pseudogene
Esf0002|Start/Stop is not a valid 1-based integer coordinate|delete_model
Esf0003|strand information missing|delete_model
Esf0013|White chars not allowed at the start of a line|gff3 parse
Esf0014|##gff-version" missing from the first line|add_gff3_version
Esf0016|##sequence-region seqid may only appear once|remove_directive
Esf0017|Start/End is not a valid integer|delete_model
Esf0018|Start is not less than or equal to end|delete_model
Esf0020|Version is not a valid integer|remove_directive
Esf0021|Unknown directive|remove_directive
Esf0022|Features should contain 9 fields|delete_model
Esf0025|Strand has illegal characters|delete_model
Esf0026|Phase is not 0, 1, or 2, or not a valid integer|fix_phase
Esf0027|Phase is required for all CDS features|fix_phase
Esf0029|Attributes must contain one and only one equal (=) sign|fix_attributes
Esf0030|Empty attribute tag|fix_attributes
Esf0031|Empty attribute value|fix_attributes
Esf0032|Found multiple attribute tags|fix_attributes
Esf0033|Found ", " in a attribute, possible unescaped|fix_attributes
Esf0034|attribute has identical values (count, value)|fix_attributes
Esf0036|Value of a attribute contains unescaped ","|fix_attributes
Esf0041|Unknown reserved (uppercase) attribute|fix_attributes
Esf0041|Unknown reserved (uppercase) attribute|fix_attributes

## Fix function
|fix function|method|
|---|---|
|delete_model|remove the whole model from the original gff3 file|
|remove_duplicate_trans|remove the duplicate transcripts|
|remove_directive|remove the directive|
|pseudogene|remove CDS feature and change the feature type of the other feature: first-level → pseudogene; second-level → pseudogenic_transcript; third-level(exon) → pseudogenic_exon|
|fix_boundary|update the coordinate of the parent by using the minimum and the maximum coordinate of the child feature|
|fix_phase|correct phase by the function `next_phase = (3 - ((CDS['end'] - CDS['start'] + 1 - phase) % 3)) % 3`. Note: If the first CDS segment doesn't have a phase, the initial phase will be 0.|
|fix_attributes|remove empty attribute tag/value; remove the redundant equal sign(=); remove dupliacte attribute; make the first character of the unknown reserved attribute lower case; merge multiple attribute tag and remove the duplicate attribute value; replace `,` with `%2C`| 
|split|split the incorrectly merged transcript from a gene model and generate a new gene model|
|merge|merge the incorrectly split gene model|
|add_gff3_version|Add `##gff-version 3` to the first line of gff3 file|
|gff3 parse|parse the gff3 file; ignore blank line in gff3; remove the white chars at the start of a line|

## Currently no automatic fix available 
|Error code|Error tag|
|---|---|
Ema0002	|Protein sequence contains internal stop codons|
Ema0004	|Incomplete gene feature that should contain at least one mRNA, exon, and CDS|
Ema0008	|Warning for distinct isoforms that do not share any regions|
Emr0003	|Duplicate ID|
Esf0004	|Seqid not found in any ##sequence-region|
Esf0005	|Start is less than the ##sequence-region start|
Esf0006	|End is greater than the ##sequence-region end|
Esf0007	|Seqid not found in the embedded ##FASTA|
Esf0008	|End is greater than the embedded ##FASTA sequence length|
Esf0009	|Found Ns in a feature using the embedded ##FASTA|
Esf0010	|Seqid not found in the external FASTA file|
Esf0011	|End is greater than the external FASTA sequence length|
Esf0012	|Found Ns in a feature using the external FASTA|
Esf0015	|Expecting certain fields in the feature|
Esf0019	|Version is not "3"|
Esf0023	|escape certain characters|
Esf0024	|Score is not a valid floating point number|
Esf0035	|attribute has unresolved forward reference|
Esf0037	|Target attribute should have 3 or 4 values|
Esf0038	|Start/End value of Target attribute is not a valid integer coordinate|
Esf0039	|Strand value of Target attribute has illegal characters|
Esf0040	|Value of Is_circular attribute is not "true"|

