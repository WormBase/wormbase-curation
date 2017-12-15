#!/usr/bin/perl

# use LWP to hit the OA like the OA does with javascript, to populate new rows and update fields, based on a tab-delimited flatfile.
# doing it this way instead of the old way because this allows use of the OA URLs that create new rows, and can run this script 
# against the sandbox (mangolassi) or live (tazendra).  for Chris and Karen.  2013 11 12
#
# changed to work with updated &newRow in the OA, which allows a  newRowAmount  value to generate a set of pgids.  2013 11 12
#
# was timing out from getting 460 pgids for RNA, so changed it to get them one by one, since the script already takes so long anyway.  2014 06 03
#
# added pgid output to screen.  2014 08 25
#
# usage
# ./populate_oa_tab_file.pl mangolassi 2987 file


use strict;
use Jex;
use LWP::Simple;
use URI::Escape;

my $domain = 'caltech.edu';
my $path = '~postgres/cgi-bin/oa/ontology_annotator.cgi';

my $action = '';
my $curator = '';
my $datatype = '';
my $subdomain = '';
my $baseUrl = '';

my %allowedSubdomains;
my @allowedSubdomains = qw( mangolassi tazendra );
foreach (@allowedSubdomains) { $allowedSubdomains{$_}++; }
my $subDomains = join" | ", @allowedSubdomains;

my %allowedDatatypes;
my @allowedDatatypes = qw( app cns grg int mop pro prt rna trp );
foreach (@allowedDatatypes) { $allowedDatatypes{$_}++; }

my %allowedCurators;
my @allowedCurators = qw( 1823 2987 712 1843 12028 101 324 363 557 1760 2970 38423 );
foreach (@allowedCurators) { $allowedCurators{$_}++; }

my $usage = qq( ./populate_oa_tab_file.pl <server> <wbpersonID> <filename>\n);
my $printUsage = '';

if ($ARGV[0]) { 
    if ($allowedSubdomains{$ARGV[0]}) {
        $subdomain = $ARGV[0]; 
        $baseUrl = 'http://' . $subdomain . '.' . $domain . '/' . $path; }
      else { $printUsage .= qq($ARGV[0] not a valid server, need : $subDomains\n); } }
  else { $printUsage .= qq(Need a server : $subDomains\n); }
if ($ARGV[1]) { 
    my ($num) = $ARGV[1] =~ m/(\d+)/;
    if ($allowedCurators{$num}) { $curator = "two$num"; }
      else { $printUsage .= qq(WBPerson$ARGV[1] not a valid curator, talk to Juancarlos\n); } }
  else { $printUsage .= qq(Need a curator WBPersonID\n);   }
unless ($ARGV[2]) { $printUsage .= qq(Need a tab delimited file\n);   }

if ($printUsage) { print $usage; print $printUsage; die; }

my $hasError = '';
my $infile = $ARGV[2];
my @lines;
open (IN, "<$infile") or die "Cannot open $infile : $!";
while (my $line = <IN>) {
  next if ($line =~ m/^#/);
  chomp $line;
  push @lines, $line;
} # while (my $line = <IN>)
close (IN) or die "Cannot close $infile : $!";

my $headerLine = shift @lines;
my (@tables) = split/\t/, $headerLine;
foreach my $table (@tables) {
  if ($table =~ m/^([a-z]{3})/) {
    if ($allowedDatatypes{$1}) {
        if ($datatype) { if ($datatype ne $1) { $hasError .= qq(different datatypes $datatype $1\n); } }
          else { $datatype = $1; } }
      else { $hasError .= qq($1 not an allowed Datatype\n); }
  } # if ($table =~ m/^([a-z]{3})/)
  my $url = 'http://' . $subdomain . '.caltech.edu/~postgres/cgi-bin/referenceform.cgi?pgcommand=SELECT+*+FROM+' . $table . '&perpage=1&action=Pg+!';
  my $page = get $url;
  my ($thereAre) = $page =~ m/There are (\d+) results/;
  if ($thereAre == 0) { $hasError .= qq($table has no data in postgres, may not be a valid table\n); }
} # foreach my $table (@tables)
if ($hasError) { print $hasError; die; }

# /~postgres/cgi-bin/oa/ontology_annotator.cgi?action=updatePostgresTableField&pgid=64&field=falsepositive&newValue=False%20Positive&datatype=pro&curator_two=two1823
# ontology_annotator.cgi?action=newRow&datatype=rna&curator_two=two2987

# my @pgids;
# for my $i (0 .. $#lines) {
#   my $url = $baseUrl . '?action=newRow&datatype=' . $datatype . '&curator_two=' . $curator;
# #   print "URL $url\n";
#   my $pageNewLine = get $url;
# #   print "PAGE $pageNewLine PAGE\n";
#   if ($pageNewLine =~ m/OK\t DIVIDER \t(\d+)/) { push @pgids, $1; }
#     else { print "Did not get pgid from $url\n"; die; }
# } # for my $i (0 .. $#lines)
# my $pgids = join",", @pgids;
# print "Created pgids $pgids\n";

# this was timing out with 460 rna entries, so getting them 1 by 1 while processing each line  2014 06 03
# my @pgids;
# my $newRowAmount = scalar(@lines);
# my $url = $baseUrl . '?action=newRow&newRowAmount=' . $newRowAmount . '&datatype=' . $datatype . '&curator_two=' . $curator;
# # print "URL $url\n";
# my $pageNewLine = get $url;
# if ($pageNewLine =~ m/OK\t DIVIDER \t([\d,]+)/) { print "Created pgids $1\n"; (@pgids) = split/,/, $1; }
#   else { print "Did not get pgid(s) from $url\n"; die; }

my @pgidsCreated;
my $nonFatalError = '';
foreach my $j (0 .. $#lines) {
#   my $pgid = $pgids[$j];				# getting pgids in batch was timing out for 460
#   unless ($pgid) { $nonFatalError .= qq(No pgid for inputline from array, skipping $lines[$j]\n); next; }
  my $url = $baseUrl . '?action=newRow&newRowAmount=1&datatype=' . $datatype . '&curator_two=' . $curator;
  my $pageNewLine = get $url;
  my $pgid = '';
  if ($pageNewLine =~ m/OK\t DIVIDER \t([\d,]+)/) { $pgid = $1; }
    else { print "Did not get pgid(s) from $url\n"; die; }
  unless ($pgid) { $nonFatalError .= qq(No pgid, skipping $lines[$j]\n); next; }
  if ($pgid) { print "Creating pgid $pgid for $lines[$j]\n"; push @pgidsCreated, $pgid; }
# print "LINE $line\n";

  my (@data) = split/\t/, $lines[$j];
  for my $i (0 .. $#data) {
    my $table = $tables[$i];
    unless ($table) { $nonFatalError .= qq(No postgres table for field from array, skipping $tables[$i]\n); next; }
    my ($field) = $table =~ m/^${datatype}_(\w+)/;
    unless ($field) { $nonFatalError .= qq(No field for postgres table with $datatype, skipping $table\n); next; }
    my $data = &convertDisplayToUrlFormat($data[$i]);
    my $url = $baseUrl . '?action=updatePostgresTableField&pgid=' . $pgid . '&field=' . $field . '&newValue=' . $data . '&datatype=' . $datatype . '&curator_two=' . $curator;
#     print "URL $url\n";
    my $pageUpdate = get $url;
    unless ($pageUpdate eq 'OK') { $nonFatalError .= qq(Update failed for $pgid changing $table to $data[$i]\n); }
  } # for my $i (0 .. $#data)
} # foreach my $line (@lines)

my $pgidsCreated = join",", @pgidsCreated;
print "PGIDs created $pgidsCreated\n";

if ($nonFatalError) { print $nonFatalError; }


sub convertDisplayToUrlFormat {
  my ($value) = @_;
  if ($value) {                                                  # if there is a display value replace stuff
    ($value) = uri_escape($value);				# escape all with URI::Escape
#     if ($value =~ m/\+/) { $value =~ s/\+/%2B/g; }         # replace + with escaped +
#     if ($value =~ m/\#/) { $value =~ s/\#/%23/g; }         # replace # with escaped #
  }
  return $value;                                                               # return value in format for URL
} # sub convertDisplayToUrlFormat 

