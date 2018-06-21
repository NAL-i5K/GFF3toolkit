#!/usr/bin/perl -w

use strict;

die "

	Comand: $0 [gff] [blast] [species code] [ouput file name] [transcripts type set]
	Exmpale: $0 lepdec_5-26-2015_annotations.gff lepdec_cdna_self_all_-5_50_3.blastn lepdec splited_gene_parent.txt transcripts_type_set.txt

" if !@ARGV;

my ($gff, $blast, $scode, $out, $transcript_type) = @ARGV;


my %gene = ();
my %gene2url = ();
my %id2name = ();
my %id2owner = ();
my $line = 0;
my $typeflag = 0;
my $pid='';
my %trans_type = ();

print "Reading the transcript type file: $transcript_type...\n";
open FI, "$transcript_type" or die "[Error] Cannot open $transcript_type.";
while (<FI>){
        chomp $_;
		$_ =~ s/\R//g;
        $trans_type{$_} = $_;
}
close FI;

print "Reading the gff file: $gff...\n";
open FI, "$gff" or die "[Error] Cannot open $gff.";
while (<FI>){
	$line++;
	chomp $_;
	$_ =~ s/\R//g;
	if ($_ =~ /^#/){next;}
	my @t = split("\t", $_);
        if ($#t != 8){next;}
	if ($t[2] eq "gene"){
		$pid = '';
		if ($t[8] =~ /ID=(.+?);/ or $t[8] =~ /ID=(.+?)$/){
			$pid = $1;
            $id2name{$pid} = $pid;
		}else{
			$pid = 'Unassigned';
            $id2name{$pid} = $pid;
			print "Warnning: $_: Parent ID is missing!!\n";
		}
		my $url = "<https://apollo.nal.usda.gov/".$scode."/jbrowse/?loc=".$t[0].":".$t[3]."..".$t[4]."&tracks=DNA,Annotations,$scode\_current_models>";
		$gene2url{$pid} = $url;
		$typeflag = 0;
	}elsif (defined $trans_type{$t[2]}){
			#if ($typeflag==1){print "Warning: pseudogene has isoforms with mRNA type: $t[8]\n"; next;} #debug 07082015
			if ($t[8] =~ /ID=(.+?);/ || $t[8] =~ /ID=(.+?)$/){
				my $id = $1;
				if ($t[8] =~ /Parent=(.+?);/ || $t[8] =~ /Parent=(.+?)$/){
					my $par = $1;
					if (defined $gene{$par}){
						$gene{$par} .= "\t$id";
					}else{
						$gene{$par} = "$id";
					}
					if ($t[8] =~ /Name=(.+?);/ || $t[8] =~ /Name=(.+?)$/){
						$id2name{$id} = $1;
					}else{
                        #print "Warning: $id: Name is missing!\n";
                        #$id2name{$id} = "Unassigned";
                        $id2name{$id} = $id;
					}
					if ($t[8] =~ /owner=(.+?);/ || $t[8] =~ /owner=(.+?)$/){
						$id2owner{$id} = $1;
                        $id2owner{$pid} = $1;
					}else{
						$id2owner{$id} = 'Unassigned';
                        $id2owner{$pid} = 'Unassigned';
                        #print "Warning: $id: owner is missing!\n";
					}
				}else{
                    #print "Warning: $id: Parent is missing!\n";
                    #next;
                    my $par = $id;
                    if (defined $gene{$par}){
                        print "Warning: duplicate ID: $id!\n";
                        next;
                    }else{
                        $gene{$par} = "$id";
                    }
                    if ($t[8] =~ /Name=(.+?);/ || $t[8] =~ /Name=(.+?)$/){
						$id2name{$id} = $1;
					}else{
                        #print "Warning: $id: Name is missing!\n";
                        #$id2name{$id} = "Unassigned";
                        $id2name{$id} = $id;
					}
					if ($t[8] =~ /owner=(.+?);/ || $t[8] =~ /owner=(.+?)$/){
						$id2owner{$id} = $1;
                        $id2owner{$pid} = $1;
					}else{
						$id2owner{$id} = 'Unassigned';
                        $id2owner{$pid} = 'Unassigned';
                        #print "Warning: $id: owner is missing!\n";
					}



				}
			}else{
				print "Warning: ID is missing!: $_\n";
				next;
			}
		}
}
close FI;

my %idpair = ();
foreach my $e (sort keys %gene){
	my @t = split("\t", $gene{$e});
	my $num = scalar @t;
	if ($#t > 0){
		foreach my $i (0 .. $#t-1){
			foreach my $j ($i+1 .. $#t){
				my @sort = ($t[$i], $t[$j]);
				@sort = sort @sort;
				my $pair = join("\t", @sort);
				$idpair{$pair} = {PAR=>$e,EV=>99,IDN=>0,ALN=>0,BEST=>"NA",NUM=>$num};
			}
		}
	}
}

my %diffparent=();
print "Reading the blast file: $blast...\n";
open FI, "$blast" or die "[Error] Cannot open $blast.";
while (<FI>){
	chomp $_;
	$_ =~ s/\R//g;
	if ($_ =~ /^$/){ print "blast result is empty..."; exit; } # Check whether the blast result is epmpty...
	my @t = split("\t", $_);
	$#t!=11 and next;
	my ($qpar, $qid, $spar, $sid) = ((), (), (), ());
    if ($t[0] !~ /Parent/){
        $t[0] =~ /ID=(.+?)\|/;
        ($qpar, $qid) = ($1, $1);
    }elsif ($t[0] =~ /\|Parent=(.+?)\|ID=(.+?)\|/ or $t[0] =~ /\|Parent=(.+?)\|ID=(.+?)$/){
		($qpar, $qid) = ($1, $2);
	}


    if ($t[1] !~ /Parent/){
        $t[1] =~ /ID=(.+?)\|/;
        ($spar, $sid) = ($1, $1);
    }elsif ($t[1] =~ /\|Parent=(.+?)\|ID=(.+?)\|/ or $t[1] =~ /\|Parent=(.+?)\|ID=(.+?)$/){
		($spar, $sid) = ($1, $2);
	}
    #	print "$qpar, $spar, $qid, $sid\n";
	my @sort = ($qid, $sid);
	@sort = sort @sort;
	my $pair = join("\t", @sort);
	my ($idn,$aln,$ev) = ($t[2],$t[3],$t[10]);

	my $typeflag = 0;
	if (defined $gene{$qpar} and defined $gene{$spar}){ $typeflag=1; } #debug 07082015
	if ($typeflag == 0){ next; }
	if ($qid ne $sid){
		if ($qpar eq $spar){
			if (defined $idpair{$pair}){
#				print "[Debug] $_\n";
				defined $idpair{$pair}->{EV} and $idpair{$pair}->{EV} < $ev and next;
				(defined $idpair{$pair}->{EV} and $idpair{$pair}->{EV} == $ev ) and (defined $idpair{$pair}->{IDN} and $idpair{$pair}->{IDN} > $idn) and next;
				(defined $idpair{$pair}->{EV} and $idpair{$pair}->{EV} == $ev ) and (defined $idpair{$pair}->{IDN} and $idpair{$pair}->{IDN} == $idn) and (defined $idpair{$pair}->{ALN} and $idpair{$pair}->{ALN} > $aln) and next;
				$idpair{$pair}={PAR=>$qpar,EV=>$ev,IDN=>$idn,ALN=>$aln,BEST=>$_,NUM=>$idpair{$pair}->{NUM}};
			}
		}else{
			$idn < 100 and next;
			defined $diffparent{$pair}->{EV} and $diffparent{$pair}->{EV} < $ev and next;
			(defined $diffparent{$pair}->{EV} and $diffparent{$pair}->{EV} == $ev ) and (defined $diffparent{$pair}->{IDN} and $diffparent{$pair}->{IDN} > $idn) and next;
			(defined $diffparent{$pair}->{EV} and $diffparent{$pair}->{EV} == $ev ) and (defined $diffparent{$pair}->{IDN} and $diffparent{$pair}->{IDN} == $idn) and (defined $diffparent{$pair}->{ALN} and $diffparent{$pair}->{ALN} > $aln) and next;
			$diffparent{$pair}={ID=>"$qid\t$sid",PAR=>"$qpar\t$spar",NAME=>"$id2name{$qid}\t$id2name{$sid}", OWNER=>"$id2owner{$qid}\t$id2owner{$sid}",EV=>$ev,IDN=>$idn,ALN=>$aln,BEST=>$_};
		}
	}
}
close FI;

=cut # Export the blast result of gene models with multiple mRNAs.
my ($ecut, $idncut, $alncut) = (0, 101, 99999);
open FO, "> GeneModelwithMultipleIsoforms.txt";
print FO "Gene\tNumber_of_Isoforms\tIsoform1\tIsoform2\turl\tqid\tsid\tidentity\taligned_length\tmismatch\tgap\tq.start\tq.end\ts.start\ts.end\te-value\tbit_score\n";
foreach my $e (sort keys %idpair){
	my $tflag = 0;
	if (defined $gene2url{$idpair{$e}->{PAR}}){
		$tflag++;
	}
	if ($tflag==0){
		print "$e: $idpair{$e}->{PAR}\n";
	}
#	print "$e: \n"; # debug
	print FO "$idpair{$e}->{PAR}\t$idpair{$e}->{NUM}\t$e\t$gene2url{$idpair{$e}->{PAR}}\t$idpair{$e}->{BEST}\n";
	$idpair{$e}->{BEST} eq "NA" and next;
	defined $idpair{$e}->{EV} and $ecut > $idpair{$e}->{EV} and next;
	(defined $idpair{$e}->{EV} and $idpair{$e}->{EV} == $ecut ) and (defined $idpair{$e}->{IDN} and $idncut < $idpair{$e}->{IDN}) and next;
	(defined $idpair{$e}->{EV} and $idpair{$e}->{EV} == $ecut ) and (defined $idpair{$e}->{IDN} and $idpair{$e}->{IDN} == $idncut) and (defined $idpair{$e}->{ALN} and $alncut < $idpair{$e}->{ALN}) and next;
	($ecut, $idncut, $alncut) = ($idpair{$e}->{EV}, $idpair{$e}->{IDN}, $idpair{$e}->{ALN});
}
close FO;
=cut

open FO, "> $out" or die "Cannot open $out";
print FO "Gene_ID1\tGene_ID2\tmRNA_ID1\tmRNA_ID2\tName1\tName2\tOwner1\tOwner2\tGene_region_url\tqid\tsid\tidentity\taligned_length\tmismatch\tgap\tq.start\tq.end\ts.start\ts.end\te-value\tbit_score\n";
foreach my $e (sort keys %diffparent){
	my @pid = split("\t", $diffparent{$e}->{PAR});
	my @t = split("\t", $diffparent{$e}->{BEST});
	$t[0] =~ /(.+?):(\d+)\.\.(\d+):(.)\|/;
	my ($scaf1, $s1, $e1, $d1) = ($1, $2, $3, $4);
	$t[1] =~ /(.+?):(\d+)\.\.(\d+):(.)\|/;
	my ($scaf2, $s2, $e2, $d2) = ($1, $2, $3, $4);

	if ( !defined $gene2url{$pid[0]} ){
	    $gene2url{$pid[0]} = 'Unassigned';
    }


	if ($scaf1 eq $scaf2 && $d1 eq $d2){
		if (($s1 >= $s2 && $s1 <= $e2) || ($s2 >= $s1 && $s2 <= $e1)){
			print FO "$diffparent{$e}->{PAR}\t$diffparent{$e}->{ID}\t$diffparent{$e}->{NAME}\t$diffparent{$e}->{OWNER}\t$gene2url{$pid[0]}\t$diffparent{$e}->{BEST}\n";
		}
	}
}
close FO;

#if ($ecut == 0 && $idncut == 101 && $alncut == 99999){
#	print "[Error] $blast might be empty.\n"; exit;
#}else{
#	print "Suggested cutoff learned from qualified gene models: Evalue ($ecut), Identity ($idncut), Alignment Length ($alncut)\n";
#}


