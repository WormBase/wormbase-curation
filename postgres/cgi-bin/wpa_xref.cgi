#!/usr/bin/perl -w

# Table of primary IDs of WBPapers and corresponding WBPapers, PMIDs, and MEDs.
#
# Just look at the postgreSQL database for table correlation data  2005 06 10
#
# Filter out WBPaper IDs that are not the primary IDs from wpa_primaryname.
# Add option to toggle between one-to-one mapping and one-to-many mapping
# for Ranjana.  2005 06 16
#
# Switched from wpa_xref and wpa_primaryname  to  wpa_identifier and wpa
# respectively.  2005 07 06
#
# Add last_date for ranjana.  2005 07 14
#
# Changed default (one to one) view to show only .txt and not an html table.
# for Erich.  2005 09 30
#
# Changed to pap_ tables, even though they're not live yet.  2010 06 22
#
# Mary Ann uses this, probably other people as well.  2011 06 07



use strict;
use CGI;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $query = new CGI;

# my %wpaHash;
my %papHash;

# our %pmHash;
# our %cgcHash;
# our %checkedoutHash;
# our %medHash;		# hash of cgc-medline xref
# our %cgcHash;		# hash of cgc-medline xref
# our %wbHash;		# hash of cgc-medline xref


my $action = '';

# my $result = $conn->exec( "SELECT wpa_timestamp FROM wpa_identifier ORDER BY wpa_timestamp DESC;" );
my $result = $dbh->prepare( "SELECT pap_timestamp FROM pap_identifier ORDER BY pap_timestamp DESC;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
my @row = $result->fetchrow;
my $date = $row[0];
$date =~ s/\..*$//;


&printHeader('WBPaper Xref Table');			# print the HTML header
&populateHashes();
&display();
&printFooter();			# print the HTML footer

sub display {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wpa_xref.cgi\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"One to One !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"One to Many !\"><P>\n";
  print "</FORM>\n";

  my $action;
  unless ($action = $query->param('action')) { $action = 'none'; } 
  if ( ($action eq 'none') || ($action eq 'One to One !') ) { &normalView(); }
  elsif ($action eq 'One to Many !') { &ranjanaView(); }
  else { print "ERROR :  not a valid choice<BR>\n"; }
} # sub display 

sub ranjanaView {
  print "<TABLE border=1 cellspacing=5>\n";
  print "<TR><TD colspan=2>One to Many View</TD><TD>Last updated $date</TD></TR>\n";
  print "<TR><TD ALIGN=CENTER>WBPaper</TD><TD ALIGN=CENTER>Other</TD></TR>\n";
  foreach my $pap (sort keys %papHash) { 
    foreach my $other (sort keys %{ $papHash{$pap} }) { 
      print "<TR><TD ALIGN=CENTER>WBPaper$pap</TD><TD ALIGN=CENTER>$other</TD></TR>\n";
      $pap = '&nbsp;';
    } # foreach $other (sort keys %{ $papHash{$pap} })
  } # foreach $pap_ (sort keys %cgcHash)
  print "</TABLE>\n";
} # sub ranjanaView

sub normalView {
# firefox takes forever to load this gigantic table (although IE does fine), so taking off the html table stuff  2005 09 30
#   print "<TABLE border=1 cellspacing=5>\n";
#   print "<TR><TD colspan=2>One to One View</TD><TD>Last updated $date</TD></TR>\n";
#   print "<TR><TD ALIGN=CENTER>WBPaper</TD><TD ALIGN=CENTER>Other</TD></TR>\n";
  foreach my $pap (sort keys %papHash) { 
    foreach my $other (sort keys %{ $papHash{$pap} }) { 
#       print "<TR><TD ALIGN=CENTER>WBPaper$pap</TD><TD ALIGN=CENTER>$other</TD></TR>\n";
      print "WBPaper$pap\t$other<BR>\n";
    } # foreach $other (sort keys %{ $papHash{$pap} })
  } # foreach $pap_ (sort keys %cgcHash)
#   print "</TABLE>\n";
} # sub normalView

sub populateHashes {
#   my $result = $dbh->prepare( "SELECT * FROM wpa_xref;" ); 
#   my $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_valid != 'invalid';" ); 
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier ;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row;
  while (@row = $result->fetchrow) {	# loop through all rows returned
    $papHash{$row[0]}{$row[1]}++;
  } # while (my @row = $result->fetchrow) 
#   $result = $dbh->prepare( "SELECT joinkey FROM wpa_primaryname WHERE wpa_primaryname = 'no';" ); 
#   $result = $dbh->prepare( "SELECT joinkey FROM wpa WHERE wpa_valid = 'invalid';" ); 
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (@row = $result->fetchrow) { delete $wpaHash{$row[0]}; }	# delete those that are not primary keys
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
#   my $result = $dbh->prepare( "SELECT * FROM ref_xref;" ); 
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   my @row;
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $cgcHash{$row[0]} = $row[1];
#     $pmHash{$row[1]} = $row[0];
#   } # while (my @row = $result->fetchrow) 
#   $result = $dbh->prepare ( "SELECT * FROM ref_checked_out;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (@row = $result->fetchrow) {
#     $checkedoutHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
#   $result = $dbh->prepare ( "SELECT * FROM ref_xrefmed;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $medHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
#   $result = $dbh->prepare ( "SELECT * FROM ref_xref_cgc;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $cgcHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
#   $result = $dbh->prepare ( "SELECT * FROM ref_ref_xref_wb_oldwb;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (@row = $result->fetchrow) {	# loop through all rows returned
#     $wbHash{$row[0]} = $row[1];
#   } # while (@row = $result->fetchrow)
# } # sub populateHashes



