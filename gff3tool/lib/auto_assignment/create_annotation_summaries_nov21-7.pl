#!usr/bin/perl -w
use strict;

#This version is updated to output information from the 'Replaced Models' field. If nothing is entered in this field, the default text given is 'nothing entered yet'. 'NA' is entered by the annotator if the model is new/doesn't replace anything. 

###SCRIPT NEEDS TO BE MODIFIED TO ACCOMODATE FEATURES OTHER THAN MRNA AND TRANSCRIPT - PREFERABLY ANYTHING AT THAT LEVEL IN THE SO HIERARCHY
#this version attempts to acccommodate everything that we have...

#gene -> mRNA -> exon/non_canonical_five_prime_splice_site/non_canonical_three_prime_splice_site/CDS -> stop_codon_read_through
#gene -> rRNA -> exon
#pseudogene -> pseudogenic_transcript -> pseudogenic_exon (warn if there are also other child features at this leve, such as non_canonical_five_prime_splice_site/non_canonical_three_prime_splice_site)

#also, want to associate gene models with sequence mods - stop_codon_readthrough (associated w/child of CDS), insertion/deletion/substitution (not associated, based on overlap)
#count number of non-canonical splice sites per model (for awareness' sake - maybe it's a pseudogene?)
#Woud be nice to translate CDS to protein sequence and inform of internal stop codons; another day

#modification 5-1-2015: add gene and transcript IDs to output
#modification 5-22-2015: fixed stop_codon_read_through assessment; added status to output; fixed formatting of indel/substitution output; switched labeling of # introns to #exons

die "

	Example: $0 [gff] [fasta] [out] [species code] [transcripts type set]

" if !@ARGV;

my $gff = shift @ARGV or die;
#need fasta file to identify whether start + stop codons are present in CDS; and to adjust aa sequence length if stop codon is present
my $fasta = shift @ARGV or die;
my $out = shift @ARGV or die;
#species code (e.g. anogla) - needed to generate URL
my $species_code = shift @ARGV or die;
my $transcript_type = shift @ARGV or die;

open ( my $GFF, $gff ) or die;
my %gene_ids = ();
my %transcript_ids = ();
my %aas = ();
my %num_cds_introns = ();
my %CDS = ();
my %CDS_start = ();
my %CDS_stop = ();
my %num_exon_introns = ();
my %cds_true_stop_coordinate = ();
my %CDS_phase = ();
my %stop_codon_readthrough = ();
my %trans_type = ();

open FI, "$transcript_type" or die "[Error] Cannot open $transcript_type.";
while (<FI>){
        chomp $_;
		$_ =~ s/\R//g;
        $trans_type{$_} = $_;
}
close FI;

while ( my $line = <$GFF> ){
    chomp $line;
	$line =~ s/\R//g;
#ignore commented lines
    if ( $line =~ /^#/ ){
	next;
    }
#if there's a fasta section at the end of the gff3, skip to the end of the file
    if ( $line =~ /^>/ ){
	last;
    }
    else {
	my @array = split /\t/, $line;
	my @col9 = split /;/, $array[8];
        my $scaffold = $array[0];
	my $strand = $array[6];
        my $start = $array[3];
	my $stop = $array[4];
	my $id = "NA";
	my $owner = "NA";
	my $name= "NA";
	my $symbol="NA";
	my $mod_date="NA";
	my $comments="NA";
	my $status="NA";
	my $parent="NA";
	my $replace = "nothing entered yet";
	foreach my $element (@col9){
	    if ( $element =~ /ID=(.*)/ ){
		$id = $1;
	    }
	    elsif ( $element =~ /owner=(.*)/ ){
		$owner = $1;
	    }
	    elsif ( $element =~ /Name=(.*)/ ){
		$name = $1;
	    }
            elsif ( $element =~ /symbol=(.*)/ ){
                $symbol = $1;
            }
            elsif ( $element =~ /date_last_modified=(.*)/ ){
                $mod_date = $1;
            }
            elsif ( $element =~ /Note=(.*)/ ){
                $comments = $1;
            }
	    elsif ( $element =~ /status=(.*)/ ){
		$status = $1;
	    }
	    elsif ( $element =~ /Parent=(.*)/ ){
		$parent = $1;
	    }
            elsif ( $element =~ /replace=(.*)/ ){
                $replace = $1;
            }
	}
#populate gene/pseudogene  hash
	if ( $array[2] =~ /gene|pseudogene/ ){
#in gene hash, key: id; value: name, SO type, date modified, notes.
	    $gene_ids{$id} = "$name\t$id\t$array[2]\t$mod_date\t$comments\t$replace\t$status";
	}
#populate transcript hash
	elsif ( defined $trans_type{$array[2]} ){
	    if ( defined $gene_ids{$parent} ){
		my $link = "https://apollo.nal.usda.gov/".$species_code."/jbrowse/?loc=".$scaffold."%3A".$start."..".$stop."&tracks=DNA%2CAnnotations%2C".$species_code."_current_models&highlight=";
                $transcript_ids{$id} = "$gene_ids{$parent}\t$owner\t$scaffold\t$start\t$stop\t$strand\t$array[2]\t$name\t$id\t$comments\t$replace\t$status\t$link";
	    }
	    elsif ($parent eq "NA" ){
	        $gene_ids{$parent} = "NA\tNA\tNA\tNA\tNA\tNA\tNA";
            my $link = "https://apollo.nal.usda.gov/".$species_code."/jbrowse/?loc=".$scaffold."%3A".$start."..".$stop."&tracks=DNA%2CAnnotations%2C".$species_code."_current_models&highlight=";
                $transcript_ids{$id} = "$gene_ids{$parent}\t$owner\t$scaffold\t$start\t$stop\t$strand\t$array[2]\t$name\t$id\t$comments\t$replace\t$status\t$link";
        }
	    else {
		warn "parents and children out of synch here:\n$parent\t$id\n";
	    }
	}
#populate transcript_ids hash w sequence mods (top-level, no parents, no children)
	elsif ( $array[2] =~ /deletion|insertion|substitution|transposable_element/ ){
	    my $link = "https://apollo.nal.usda.gov/".$species_code."/jbrowse/?loc=".$scaffold."%3A".$start."..".$stop."&tracks=DNA%2CAnnotations%2C".$species_code."_current_models&highlight=";
	    $transcript_ids{$id} = "NA\t$name\t$array[2]\t$mod_date\tNA\tNA\tNA\t$owner\t$scaffold\t$start\t$stop\t$strand\t$array[2]\tNA\t$id\tNA\tNA\tNA\t$link";
	}
#check for stop codon readthroughs to associate w CDS
        elsif ( $array[2] =~ /stop_codon_read_through/ ){
#assumes that stop_codon_read_through feature comes after CDS feature in gff
	    if ( defined $CDS{$parent} ){
#populate with mRNA ID as key, CDS ID as value
		$stop_codon_readthrough{$CDS{$parent}} = $parent;
		print "stop codon readthrough: id: $id, parent: $parent\n";
	    }
	    else {
		print "couldn't find parent CDS ID $parent of stop_codon_read_through ID $id\n";
	    }
	}
	elsif ( $array[2] =~ /CDS/ ){
            #align CDS feature with transcript parent ID
	    if ( defined $transcript_ids{$parent} ){
		$CDS{$id} = $parent;
#add aa's
		$aas{$parent} += ( abs($start - $stop) +1)/3;
		#count CDS features to derive number of introns
		$num_cds_introns{$parent} += 1;
		#define CDS start and stop coordinate (Hugh Robertson's request); include phase
		if ( defined $CDS_start{$parent} ){
		    if ( $start < $CDS_start{$parent} ){
			$CDS_start{$parent} = $start;
			$CDS_phase{$parent}{$start} = $array[7];
		    }
		    if ( $stop > $CDS_stop{$parent} ){
			$CDS_stop{$parent} = $stop;
			$CDS_phase{$parent}{$stop} = $array[7];
		    }
		}
		else {
		    $CDS_start{$parent} = $start;
		    $CDS_stop{$parent} = $stop;
		    $CDS_phase{$parent}{$start} = $array[7];
		    $CDS_phase{$parent}{$stop} = $array[7];
		}
	    }
#already pre-populate true stop coordinate hash for proper aa length calculaton (accounting for stop codons; complete value in next section. id -> scaf  -> dir -> stop
	    $cds_true_stop_coordinate{$parent}{$scaffold}{$array[6]} = 1;
	}
	elsif ( $array[2] =~ /exon/ ){
	    #define the total number of introns (within CDS and UTRs combined)
	    $num_exon_introns{$parent} += 1;
	}
	elsif ( $array[2] =~ /prime_utr/ ){
	    next;
	}
#grab bag of other features for accounting's sake
	else {
	    print "don't know what to do with feature $id of type $array[2]; not reflected in output\n";
	}
    }
}

#will have to slice out string from last 3 bases of CDS (note that this is specific to Web Apollo coding - not all gff3s code their stop codons as CDS) and see whether it matches stop codons (or their reverse complement, depending on strand)
#TAG, TAA, TGA
close $GFF;


open ( my $FASTA, $fasta ) or die;
my %fasta = ();
my $defline;
while ( my $fline = <$FASTA> ){
    chomp $fline;
	$fline =~ s/\R//g;
    if ( $fline =~ /^>(\S+)/ ){
	$defline = $1;
    }
    else {
	$fasta{$defline} .= $fline;
    }
}

#id -> scaf -> dir -> 1 (should be populated with true stop coordinate
#code to determine whether stop codon is present in CDS and calculate true aa sequence length
#WIP: STILL NO CODE TO INCORPORATE PHASE
foreach my $cds ( keys %cds_true_stop_coordinate ){
    foreach my $scafkey ( keys %{$cds_true_stop_coordinate{$cds}} ){
	if ( defined $fasta{$scafkey} ){
	    foreach my $dirkey ( keys %{$cds_true_stop_coordinate{$cds}{$scafkey}} ){
		if ( $dirkey eq "+" ){
		    #for forward strand, stop coordinate in CDS_stop is true stop coordinate, and coordinate in CDS_start is true start coordinate
		    my $forward_stop = $CDS_stop{$cds};
		    my $stop_slice = substr( $fasta{$scafkey}, ($forward_stop -3), 3);
		    if ( $stop_slice =~ /^TAG$|^TAA$|^TGA$/ ){
			my $newlength1 =$aas{$cds} -1;
			$aas{$cds} = "$newlength1\ty";
		    }
		    else {
			$aas{$cds} = "$aas{$cds}\tn";
			print "transcript $cds (forward strand) does not have a stop codon: $stop_slice\n";
		    }
                    my $forward_start =$CDS_start{$cds};
		    my $start_slice = substr($fasta{$scafkey}, ($forward_start -1), 3);
		    if ( $start_slice =~ /^ATG$/ ){
#if ATG is present, add info that start codon is present in CDS to amino acid length hash
			$aas{$cds} .= "\ty";
		    }
		    else {
			$aas{$cds} .= "\tn";
			print "transcript $cds (forward strand) does not have a start codon: $start_slice\n";
		    }
		}
		elsif ( $dirkey eq "-" ){
		    #for reverse strand,  coordinate in CDS_start is true stop coordinate
		    my $reverse_stop =$CDS_start{$cds};
		    my $reverse_stop_slice = substr( $fasta{$scafkey}, ($reverse_stop -1 ), 3);
		    if ( $reverse_stop_slice =~ /^CTA$|^TTA$|^TCA$/ ){
			my $newlength = $aas{$cds} -1;
			$aas{$cds} = "$newlength\ty";
		    }
		    else {
			$aas{$cds} = "$aas{$cds}\tn";
			print "transcript $cds (reverse strand) does not have a stop codon: $reverse_stop_slice\n";
		    }
		    my $reverse_start = $CDS_stop{$cds};
		    my $reverse_start_slice = substr( $fasta{$scafkey}, ($reverse_start -3 ), 3);
		    if ( $reverse_start_slice =~ /^CAT$/ ){
			#if ATG is present, add info that start codon is present in CDS to amino acid length hash
                        $aas{$cds} .= "\ty";
		    }
		    else {
			$aas{$cds} .= "\tn";
			print "transcript $cds (reverse strand) does not have a start codon: $reverse_start_slice\n";
		    }
		}
		else {
		    $aas{$cds} = "NA\tNA\tNA";
		}
	    }
#	    }
	}
    }
}


open ( my $OUT, ">$out" ) or die;
#print out header
print $OUT "gene_name\tgene_id\tgene_type\tgene_creation_date\tgene_comments\tgene_replaced_model\tgene_status\ttranscript_owner\ttranscript_scaffold\ttranscript_start\ttranscript_end\ttranscript_strand\ttranscript_type\ttranscript_name\ttranscript_id\ttranscript_comments\ttranscript_Replaced_model\ttranscript_status\ttranscript_URL\t#amino_acids\tstop-codon-present?\tstart-codon-present?\tCDS_start_coordinate\tCDS_end_coordinate\t#CDS_segments\t#exons\thas_stop_codon_read_through\n";
foreach my $key (keys %transcript_ids ){
#add information from CDS and exon hashes
##NEED CONDITION FOR AASAND CDS START STOP IF TRANSCRIPT TYPE IS NOT MRNA - think I covered this with a band-aid by  subbing in 'NA'. Should probably build in a better check for failing to meet conditions
#if it has exons
    if ( defined $num_exon_introns{$key} ){
#if it has CDS
	if ( defined $aas{$key} and defined $CDS_start{$key} and defined $CDS_stop{$key} ){
#if it has a readthrough stop codon
	    if ( defined $stop_codon_readthrough{$key} ){
		print $OUT "$transcript_ids{$key}\t$aas{$key}\t$CDS_start{$key}\t$CDS_stop{$key}\t$num_cds_introns{$key}\t$num_exon_introns{$key}\thas_readthrough_stop_codon\n";
	    }
	    else {
                print $OUT "$transcript_ids{$key}\t$aas{$key}\t$CDS_start{$key}\t$CDS_stop{$key}\t$num_cds_introns{$key}\t$num_exon_introns{$key}\tNA\n";
	    }
	}
#if it doesn't have CDS
	else {
	    print $OUT "$transcript_ids{$key}\tNA\tNA\tNA\tNA\tNA\tNA\t$num_exon_introns{$key}\tNA\n";
	}
    }
#if it doesn't have exons
    else {
	print $OUT "$transcript_ids{$key}\tNA\tNA\tNA\tNA\tNA\tNA\tNA\tNA\n";
    }
}
