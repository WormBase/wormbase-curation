more compare_transgenes.pl 
#!/usr/bin/perl -w

# compare Karen's .txt file with postgres data in trp_ tables.  2011 03 17

# this is necessary for multiontology fields as objects in these fields need to be identifyable by double quotes as well as comma separated, the same goes for f
ields that are multi-dropdown, but when querying and fiddling with data transplants, these double quotes need to be removed so the correct information is actual
ly shown, queryable and available for modification. 

use strict; #to limit the variables used in a script to things that have been defined
use diagnostics; #makes error messages more understandable
use DBI;  #this module says to connect to a database
use Encode qw( from_to is_utf8 ); #this module allows character conversion, needed to convert non-utf8 recognizable things into a utf8 recognizable character

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; #connects to the postgres database called testdb and if cannot 
connect it will die if want to connect from a different machine, need to add tazendra's  IP and my IP to some postgresql config file

my %hash; #a hash to store data from the cgc_transgene.txt file
my %pghash; #hash to store data from postgres


my $result = $dbh->prepare( "SELECT trp_name.trp_name, trp_strain.trp_strain, trp_synonym.trp_synonym, trp_name.joinkey FROM trp_name, trp_strain, trp_synonym W
HERE trp_strain.joinkey = trp_name.joinkey AND trp_synonym.joinkey = trp_name.joinkey" ); #prepares the query, can put any query within the double quotes, joink
ey stands for pgid in postgres, in the OA the joinkey is called pgid
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; #executes the query or tells you the reasons why the query might have died if it didn't wo
rk
while (my @row = $result->fetchrow) { #will grab results one row at a time until there aren't anymore, storing the results in the row variable
  if ($row[0]) { #row[0] refers to the first value from the row of results from the query, in this case that is the value from trp_name, from there, row[1] refe
rs to the second value, trp_strain, etc. these values are being stored in pghash and associated with the trp_name value defined as row[0]. the while loop 'while
(my @row...) keeps this fetch and store action going until there are no more results to fetch. 
    my $transgene_name = $row[0];
    $pghash{$transgene_name}{strain} = $row[1];
    $pghash{$transgene_name}{synonym} = $row[2]; 
    $pghash{$transgene_name}{pgid} = $row[3]; } }

my $infile = 'cgc_transgenes.txt';
my $outfile = 'file_out';
open (IN, "<$infile") or die "Cannot open $infile : $!";#opens a file for reading, pay attention to the direction of <
open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
my $junk = <IN>; $junk = <IN>;  		# get rid of headers by reading the first two lines into a junk variable
while (my $line = <IN>) {
  chomp $line; #chomp gets rid of the line break at the end, note if reading paragraph by paragraph there would still be some line breaks
  my ($strain, $name_syn, $third, @junk) = split/\t/, $line; #takes each line and splits the line at the tabs, so everything between tabs are grouped together, 
in this case there needed to be at least two tabs, if a tab was missing then this script gets grumpy since there would be nothing to put in the variable named t
hird, so if there were more than two tabs (three columns) everything else goes into junk
  print OUT "$strain\n"; #an example of how to use the outfile, again note the direction of the angle bracket above
  if ($name_syn =~ m/^\"+/) { $name_syn =~ s/^\"+//; } #removing double qoutes from the beginning of the string as denoted by ^, introduced by the spreadsheet c
onverting to tab delimited text (if these came from postgres, you would also need to strip them, but you would have to put them back)
  if ($name_syn =~ m/\"+$/) { $name_syn =~ s/\"+$//; } #strip the all double quotes at the end of the string, denoted by $
  if ($third =~ m/^\"+/) { $third =~ s/^\"+//; }#strip all double quotes from the beginning
  if ($third =~ m/\"+$/) { $third =~ s/\"+$//; }#strip all double quotes at the end
  my $name = ''; my $synonym;
  if ($name_syn) { 
    if ($name_syn =~ m/^(.*?)(\[.*)$/) { $name = $1; $synonym = $2; } 
      else { $synonym = $name_syn; } }
  if ( (!$name) && ($third) ) {
    if ($third =~ m/([a-z]+(Is|Ex)\d+)/) { $name = $1; } }
  unless ($name) { print "No name for : $line\n"; next; }
  $hash{$name}{strains}{$strain}++;
  $hash{$name}{synonym}{$synonym}++;
  $hash{$name}{lines}{$line}++;
} # while (my $line = <IN>)
close (IN) or die "Cannot close $infile : $!";

foreach my $name (sort keys %hash) {
  my $strains = join" | ", sort keys %{ $hash{$name}{strains} };
  my $syns = join" | ", sort keys %{ $hash{$name}{synonym} };
  my $lines = join" | ", sort keys %{ $hash{$name}{lines} };
  my $pgstrains = ''; my $pgsyns = '';
  if ($pghash{$name}{strain}) { $pgstrains = $pghash{$name}{strain}; }
  if ($pghash{$name}{synonym}) { $pgsyns = $pghash{$name}{synonym}; }
  my $message = '';
  if ($pghash{$name}{pgid}) { $message .= "In pg $pghash{$name}{pgid}\t"; } else { $message .= "NO PG MATCH\t"; }
#   print "$name\t$strains\t$syns\t$lines\n";
  $message .= "$name\t$strains\t$pgstrains\t$syns\t$pgsyns\t";
  if ($pgstrains ne $strains) { $message .= "Strains different\t"; }
  if ($pgsyns ne $syns) { $message .= "Synonyms different\t"; }
  print "$message\n";
}

__END__



__END__
	match ^(.*?)\[ to get the name.  If no name look at 3rd column	"if no name match in column 2, match to the first ([a-z]+(Is/Ex)\d+) in this column"	
"after getting the name, store all strains / synoyms in separate hashes, and join with <space>|<space>"	"match name with trp_name, get trp_strain and trp_synony
m and output to tab delimited text file the 5 columns"
strain	name + synonym	ignore unless no name in the name column		
NL597	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)] X. Suppressor of activated Gs. sgs-1 also called acy-1.		
NL1236	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)]		
NL1908	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)] X. Suppressor of activated Gs. sgs-1 also called acy-1.		
NL1909	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)]		
NL1921	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)] X. Suppressor of activated Gs. sgs-1 also called acy-1.		
NL1925	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)]		
NL1947	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)] X. Suppressor of activated Gs. sgs-1 also called acy-1.		
NL3231	pkIs296[hsp::gsa1QL; dpy-20(+)]	pkIs296[hsp::gsa1QL; dpy-20(+)] X. Suppressor of activated Gs. sgs-1 also called acy-1. pkIs296[hsp::gsa1QL; dpy-20(+)].
		
