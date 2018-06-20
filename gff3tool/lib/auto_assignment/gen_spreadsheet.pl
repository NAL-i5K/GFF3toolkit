#!/usr/bin/perl -w

use strict;

die "

	Example: $0 annotations_oruabi-10-13-2015_internal_viewed.txt report.txt report2.txt check1.txt

" if !@ARGV;

my ($summary, $cdshit, $preTranhit, $out) = @ARGV;

my %hit = ();
open FI, "$cdshit";
my $head = <FI>;
while (<FI>){
	chomp $_;
	$_ =~ s/\R//g;
	my @t = split("\t", $_);
	if (defined $hit{$t[2]}){
		$hit{$t[2]} .= ",$t[5]";
	}else{
		$hit{$t[2]} = $t[5];
	}
}
close FI;

my %hit2 = ();
open FI, "$preTranhit";
$head = <FI>;
while (<FI>){
	chomp $_;
	$_ =~ s/\R//g;
	my @t = split("\t", $_);
	if (defined $hit2{$t[2]}){
		$hit2{$t[2]} .= ",$t[5]";
	}else{
		$hit2{$t[2]} = $t[5];
	}
}
close FI;

open FO, "> $out";
my @col = ("gene_name","gene_type","gene_id","gene_comments","gene_status","transcript_owner","transcript_scaffold","transcript_start","transcript_end","transcript_strand","transcript_type","transcript_name","transcript_id","transcript_comments","transcript_status","transcript_URL","stop-codon-present?","start-codon-present?","CDS_start_coordinate","CDS_end_coordinate","#CDS_segments","#exons","has_stop_codon_read_through","transcript_Replaced_model");
my $headline = join("\t", @col);
print FO "$headline\tAuto_assigned_Replaced_Model\n";

open FI, "$summary";
my @tmp = split("\t", <FI>);
chomp @tmp;
my @index = ();
my $tid = ();
my $gid = ();
for my $i (0 .. $#col){
	for my $j (0 .. $#tmp){
		if ($tmp[$j] eq "transcript_id"){ $tid = $j; }
        if ($tmp[$j] eq "gene_id"){ $gid = $j; }
		if ($col[$i] eq $tmp[$j]){ push @index, $j; }
	}
}
while (<FI>){
	chomp $_;
	$_ =~ s/\R//g;
	my @t = split("\t", $_);
	chomp @t;
	my @info = ();
	for my $i (0 .. $#index){
		push @info, $t[$index[$i]];
	}
	if ($info[$#info] =~ /nothing entered yet/){
		my $line = join("\t", @info);
		my $flag = 0;
		if (defined $hit{$t[$tid]}){
			print FO "$line\t$hit{$t[$tid]}\n";
			$flag ++;
		}elsif (defined $hit2{$t[$gid]}){
            print FO "$line\t\n";
            $flag++;
        }
		if ($flag == 0){
			print FO "$line\tNA\n";
		}
	}
}
close FI;
close FO;
