#!/usr/bin/perl -w

# dump paper and object data from phenote tables  2008 04 25
#
# updated to get allele->WBGene from http://tazendra.caltech.edu/~azurebrd/var/work/phenote/ws_current.obo
# and output that in some guessed .ace format since Jolene didn't give me one or tell me where from the obo
# to get the mappings.  2010 01 21

use strict;
use diagnostics;
use LWP::Simple;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $obo_file = get "http://tazendra.caltech.edu/~azurebrd/var/work/phenote/ws_current.obo";
my %allele_to_gene;

my (@entries) = split/\[Term\]/, $obo_file;
foreach my $entry (@entries) {
    my $name = '';
    my $gene = '';
  if ($entry =~ m/name:\s+\"(.*?)\"/) { $name = $1; }
  if ($entry =~ m/allele:\s+\"(WBGene\d+)/) { $gene = $1; }
    if ($gene && $name) { $allele_to_gene{$name} = $gene; }
} # foreach my $entry (@entries)

my %hash;
my $result = $dbh->prepare( "SELECT * FROM app_type;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $hash{type}{$row[0]} = $row[1]; }
$result = $dbh->prepare( "SELECT * FROM app_tempname;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $hash{obj}{$row[0]} = $row[1]; }
$result = $dbh->prepare( "SELECT * FROM app_paper;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $hash{paper}{$row[1]}{$row[0]}++; }

foreach my $paper (sort keys %{ $hash{paper} }) {
    next unless ($paper);
    print "Paper : $paper\n";
    foreach my $joinkey (sort keys %{ $hash{paper}{$paper} }) {
	my $type = $hash{type}{$joinkey};
	my $obj = $hash{obj}{$joinkey};
	unless ($type) { print "// ERR no type $joinkey PGDBID\n"; }
	unless ($obj) { print "// ERR no obj $joinkey PGDBID\n"; }
	if ($type && $obj) { 
	    next if ($type =~ m/Multi/);
	    if ($allele_to_gene{$obj}) { print "Gene\t$allele_to_gene{$obj}\n"; }
	    print "$type\t\"$obj\"\tInferred_Automatically\t\"Inferred automatically from curated phenotype\"\n"; }
    
    } # foreach my $joinkey (sort keys %{ $hash{paper}{$paper} })
    print "\n";
} # foreach my $paper (sort keys %{ $hash{paper} })

__END__
