#!/usr/bin/perl -w

# Table of WBGene information based on latest WS on postgres

# For Ranjana.  2010 01 06

use strict;
use CGI;
use DBI;
use Jex;

my $query = new CGI;

my %hash;


  # connect to the testdb database
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 


# my $result = $conn->exec( "SELECT wpa_timestamp FROM wpa_xref ORDER BY wpa_timestamp DESC;" ); 
# my $result = $conn->exec( "SELECT wpa_timestamp FROM wpa_identifier ORDER BY wpa_timestamp DESC;" ); 
# my @row = $result->fetchrow;
# my $date = $row[0];
# $date =~ s/\..*$//;

# my @tables = qw( molname locus seqname protein sequence synonyms variation wbgene );
my @tables = qw( locus synonyms wbgene sequence  );

# &printHeader('WBPaper Xref Table');			# print the HTML header
&PrintHeader();				# print the HTML header
&populateHashes();
&display();
# &printFooter();			# print the HTML footer

sub display {
  print "<TABLE border=1 cellspacing=5>\n";
#   print "<TR><TD ALIGN=CENTER>WBPaper</TD><TD ALIGN=CENTER>Other</TD></TR>\n";
  print "<tr>\n";
#   print "<td>joinkey</td>\n";
  foreach my $table (@tables) { print "<td>$table</td>\n"; }
  print "</tr>\n";
  foreach my $joinkey ( sort keys %{ $hash{exists} } ) {
    print "<tr>\n";
#     print "<td>$joinkey</td>\n";
    foreach my $table (@tables) { 
      print "<td>";
      my @values = ();
      foreach my $thing (sort keys %{ $hash{$table}{$joinkey} } ) { push @values, $thing; }
      my $value = join"<br>", @values;
      print "$value</td>";
    }
    print "</tr>\n";
  } # foreach my $joinkey ( sort keys %{ $hash{exists} } )
#   foreach my $locus (sort keys %wbgHash) { 
#     foreach my $wbgene (sort keys %{ $wbgHash{$locus} }) { 
#       print "$locus\tWBGene$wbgene\n"; } }
#   print "</TABLE>\n";
} # sub display 

sub populateHashes {
  foreach my $table ( @tables ) {
    my $result = $dbh->prepare( "SELECT * FROM gin_$table" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $hash{$table}{$row[0]}{$row[1]}++; $hash{exists}{$row[0]}++; }
  }
} # sub populateHashes 



sub PrintHeader {
#   print <<"EndOfText";
# Content-type: text/plain\n\n
# EndOfText
  print <<"EndOfText";
Content-type: text/html\n\n
EndOfText
# // Last connection made on $date
} # sub PrintHeader 
