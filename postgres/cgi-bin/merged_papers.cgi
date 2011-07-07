#!/usr/bin/perl -w

# Display Merged WBPapers

# Get invalid data from wpa table then find matches from wpa_identifier to find
# out what it's been replaced with, and print both out.  2005 09 15
#
# change from wpa to pap tables, even though they're not live yet.  2010 06 23


 
use strict;
use CGI;
use Jex;
use LWP::UserAgent;
use POSIX qw(ceil);
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $query = new CGI;


my $frontpage = 1;
my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color

&printHeader('Merged WBPapers');
&display();
&printFooter();

sub display {
  my %xrefs;
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ '^00';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    $xrefs{$row[1]}{$row[0]}++; 	# xref, key
  }

#   my %invalid;
#   my $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp;" );
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'invalid') { $invalid{$row[0]}++; }
#       else { delete $invalid{$row[0]}; }
#   } # while (my @row = $result->fetchrow)
# 
#   my %xrefs;
#   $result = $dbh->prepare( "SELECT * FROM wpa_identifier ORDER BY wpa_timestamp;" );
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'valid') { $xrefs{$row[1]}{$row[0]}++; }	# xref, key
#       else { delete $xrefs{$row[1]}{$row[0]}; }
#   } # while (my @row = $result->fetchrow)
  
#   foreach my $joinkey (sort keys %invalid) { # }
  foreach my $joinkey (sort keys %xrefs) {
    my $wbpaper = '';
#     my $thing = 'WBPaper' . $joinkey;
    if ($xrefs{$joinkey}) {
      my @paps = sort keys %{ $xrefs{$joinkey} };
      $wbpaper = join ", ", @paps; }
    print "$joinkey\tis now\t$wbpaper<BR>\n";
  } # foreach my $joinkey (sort keys %invalid)
} # sub display

