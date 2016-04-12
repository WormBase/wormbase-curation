#!/usr/bin/perl -w

# Table of WBPapers with PMID without a PDF
#
# Just look at the postgreSQL database for table correlation data  2005 06 10
#
# Switched from wpa_xref and wpa_primaryname  to  wpa_identifier and wpa
# respectively.  2005 07 06
#
# Converted to show WBPapers with PMID without a PDF.  2009 05 27 (?)
#
# Converted from wpa to pap tables, although they're not live yet.  2010 06 22

use strict;
use CGI;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

use Jex;

my $query = new CGI;

my %papHash;

# our %pmHash;
# our %cgcHash;
# our %checkedoutHash;
# our %medHash;		# hash of cgc-medline xref
# our %cgcHash;		# hash of cgc-medline xref
# our %wbHash;		# hash of cgc-medline xref

  # connect to the testdb database
my %pap;
my $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid' ORDER BY pap_timestamp ;" ); 
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 

while (my @row = $result->fetchrow) {
  $pap{$row[0]}++; }

my %pdf;
$result = $dbh->prepare( "SELECT * FROM pap_electronic_path ORDER BY pap_timestamp;" ); 
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) {
  $pdf{$row[0]}++; }

my %pmid;
# my $result = $conn->exec( "SELECT wpa_timestamp FROM wpa_xref ORDER BY wpa_timestamp DESC;" ); 
$result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid';" ); 
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) {
  $pmid{$row[0]} = $row[1]; }


# &printHeader('WBPaper Xref Table');			# print the HTML header
&PrintHeader();				# print the HTML header
&display();
# &printFooter();			# print the HTML footer

sub display {
  my $output = ''; my $count = 0;
#   print "<TABLE border=1 cellspacing=5>\n";
#   print "<TR><TD ALIGN=CENTER>WBPaper</TD><TD ALIGN=CENTER>Other</TD></TR>\n";
  foreach my $joinkey (sort keys %pmid) { 
    if ( ($pap{$joinkey}) && (! ($pdf{$joinkey})) ) {
      $count++;
      $output .= "WBPaper$joinkey\t$pmid{$joinkey}\n"; }
  } # foreach $pap_ (sort keys %cgcHash)
  print "There are $count valid WBPapers with PMIDs without a PDF.\n\n$output";
#   print "</TABLE>\n";
} # sub display 



sub PrintHeader {
  print <<"EndOfText";
Content-type: text/plain\n\n
EndOfText
} # sub PrintHeader 


