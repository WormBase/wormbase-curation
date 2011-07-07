#!/usr/bin/perl -w

# Table of loci/synonym to WBGene
#
# From gin_locus and gin_synonyms (for locus)  For Andrei's gene-gene
# interactions processing in textpresso.  2008 03 07

use strict;
use CGI;
use DBI;
use Jex;

my $query = new CGI;

my %wbgHash;


  # connect to the testdb database
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


# my $result = $dbh->prepare( "SELECT wpa_timestamp FROM wpa_xref ORDER BY wpa_timestamp DESC;" ); 
# my $result = $dbh->prepare( "SELECT wpa_timestamp FROM wpa_identifier ORDER BY wpa_timestamp DESC;" ); 
# $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
# my @row = $result->fetchrow;
# my $date = $row[0];
# $date =~ s/\..*$//;


# &printHeader('WBPaper Xref Table');			# print the HTML header
&PrintHeader();				# print the HTML header
&populateHashes();
&display();
# &printFooter();			# print the HTML footer

sub display {
#   print "<TABLE border=1 cellspacing=5>\n";
#   print "<TR><TD ALIGN=CENTER>WBPaper</TD><TD ALIGN=CENTER>Other</TD></TR>\n";
  foreach my $locus (sort keys %wbgHash) { 
    foreach my $wbgene (sort keys %{ $wbgHash{$locus} }) { 
      print "$locus\tWBGene$wbgene\n"; } }
#   print "</TABLE>\n";
} # sub display 

sub populateHashes {
  my $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE gin_syntype = 'locus' ORDER BY gin_timestamp;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {	# loop through all rows returned
    unless ($row[0]) { $row[0] = ''; }
    unless ($row[1]) { $row[1] = ''; }
    $wbgHash{$row[1]}{$row[0]}++;
  } # while (my @row = $result->fetchrow) 
  $result = $dbh->prepare( "SELECT * FROM gin_locus ORDER BY gin_timestamp;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {	# loop through all rows returned
    unless ($row[0]) { $row[0] = ''; }
    unless ($row[1]) { $row[1] = ''; }
    $wbgHash{$row[1]}{$row[0]}++;
  } # while (my @row = $result->fetchrow) 
} # sub populateHashes 



sub PrintHeader {
  print <<"EndOfText";
Content-type: text/plain\n\n
EndOfText
# // Last connection made on $date
} # sub PrintHeader 
