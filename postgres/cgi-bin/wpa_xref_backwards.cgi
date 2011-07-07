#!/usr/bin/perl -w

# Table of CGCs, PMIDs, MEDs, etc. and all corresponding WBPaper IDs (primary and old)
#
# Just look at the postgreSQL database for table correlation data  2005 06 10
#
# Switched from wpa_xref and wpa_primaryname  to  wpa_identifier and wpa
# respectively.  2005 07 06
#
# Switched to pap_ tables even though they're not live yet.  2010 06 22

use strict;
use CGI;
use DBI;
use Jex;

my $query = new CGI;

# my %wpaHash;
my %papHash;

# our %pmHash;
# our %cgcHash;
# our %checkedoutHash;
# our %medHash;		# hash of cgc-medline xref
# our %cgcHash;		# hash of cgc-medline xref
# our %wbHash;		# hash of cgc-medline xref

  # connect to the testdb database
# my $conn = Pg::connectdb("dbname=testdb");
# die $$conn->execconn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 


# my $result = $conn->exec( "SELECT wpa_timestamp FROM wpa_xref ORDER BY wpa_timestamp DESC;" ); 
# my $result = $conn->exec( "SELECT wpa_timestamp FROM wpa_identifier ORDER BY wpa_timestamp DESC;" ); 
my $result = $dbh->prepare( "SELECT pap_timestamp FROM pap_identifier ORDER BY pap_timestamp DESC;" ); 
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
my @row = $result->fetchrow;
my $date = $row[0];
$date =~ s/\..*$//;


# &printHeader('WBPaper Xref Table');			# print the HTML header
&PrintHeader();				# print the HTML header
&populateHashes();
&display();
# &printFooter();			# print the HTML footer

sub display {
#   print "<TABLE border=1 cellspacing=5>\n";
#   print "<TR><TD ALIGN=CENTER>WBPaper</TD><TD ALIGN=CENTER>Other</TD></TR>\n";
  foreach my $pap (sort keys %papHash) { 
    foreach my $other (sort keys %{ $papHash{$pap} }) { 
      print "$other\tWBPaper$pap\n";
    } # foreach $other (sort keys %{ $papHash{$pap} })
  } # foreach $pap_ (sort keys %cgcHash)
#   print "</TABLE>\n";
} # sub display 

sub populateHashes {
#   my $result = $conn->exec( "SELECT * FROM wpa_xref;" ); 
#   my $result = $conn->exec( "SELECT * FROM wpa_identifier;" ); 
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row;
  while (@row = $result->fetchrow) {	# loop through all rows returned
    unless ($row[0]) { $row[0] = ''; }
    unless ($row[1]) { $row[1] = ''; }
    $papHash{$row[0]}{$row[1]}++;
  } # while (my @row = $result->fetchrow) 
} # sub populateHashes 

# sub display {
#   print "<TABLE border=1 cellspacing=5>\n";
#   print "<TR><TD ALIGN=CENTER>cgc</TD><TD ALIGN=CENTER>pmid</TD></TR>\n";
#   foreach $_ (sort keys %cgcHash) { 
#     print "<TR><TD ALIGN=CENTER>$_</TD><TD ALIGN=CENTER>$cgcHash{$_}</TD></TR>\n";
#   } # foreach $_ (sort keys %cgcHash)
#   foreach $_ (sort keys %medHash) { 
#     print "<TR><TD ALIGN=CENTER>$_</TD><TD ALIGN=CENTER>$medHash{$_}</TD></TR>\n";
#   } # foreach $_ (sort keys %medHash)
#   foreach $_ (sort keys %cgcHash) { 
#     print "<TR><TD ALIGN=CENTER>$_</TD><TD ALIGN=CENTER>$cgcHash{$_}</TD></TR>\n";
#   } # foreach $_ (sort keys %cgcHash)
#   foreach $_ (sort keys %wbHash) { 
#     print "<TR><TD ALIGN=CENTER>$_</TD><TD ALIGN=CENTER>$wbHash{$_}</TD></TR>\n";
#   } # foreach $_ (sort keys %wbHash)
#   print "</TABLE>\n";
# } # sub display
# 
# sub populateHashes {
#   my $result = $conn->exec( "SELECT * FROM ref_xref;" ); 
#   my @row;
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $cgcHash{$row[0]} = $row[1];
#     $pmHash{$row[1]} = $row[0];
#   } # while (my @row = $result->fetchrow) 
#   $result = $conn->exec ( "SELECT * FROM ref_checked_out;" );
#   while (@row = $result->fetchrow) {
#     $checkedoutHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
#   $result = $conn->exec ( "SELECT * FROM ref_xrefmed;" );
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $medHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
#   $result = $conn->exec ( "SELECT * FROM ref_xref_cgc;" );
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $cgcHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
#   $result = $conn->exec ( "SELECT * FROM ref_ref_xref_wb_oldwb;" );
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $wbHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
# } # sub populateHashes



sub PrintHeader {
  print <<"EndOfText";
Content-type: text/plain\n\n
// Last connection made on $date
EndOfText
} # sub PrintHeader 
