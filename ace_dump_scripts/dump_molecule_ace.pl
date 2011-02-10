#!/usr/bin/perl -w

# dump mop_ data into Molecule.ace for citace upload  2010 07 31

use strict;
use diagnostics;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my @tables = qw( molecule publicname synonym chemi chebi kegg );
my %hash;
my $result;


my $directory = '/home/acedb/karen/Molecule';
chdir ($directory) or die "Cannot chdir to $directory : $!";

my $outfile = 'Molecule.ace';
open (OUT, ">$outfile") or die "Cannot create $outfile : $!";

foreach my $table (@tables) {
    my $pgtable = 'mop_' . $table;
    $result = $dbh->prepare( "SELECT * FROM $pgtable" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
	if ($row[0]) { $hash{$table}{$row[0]} = $row[1]; } }
}

foreach my $joinkey (sort {$a<=>$b} keys %{ $hash{molecule} }) {
    my ($molecule, $publicname, $syns, $chemi, $chebi, $kegg);
    if ($hash{molecule}{$joinkey}) { $molecule = $hash{molecule}{$joinkey}; }
    next unless $molecule;
    next if ($molecule =~ m/WBMol/);
    print OUT "Molecule : \"$molecule\"\n";
    if ($hash{publicname}{$joinkey}) { print OUT "Public_name\t\"$hash{publicname}{$joinkey}\"\n"; }
    if ($hash{synonym}{$joinkey}) { 
	my (@syns) = split/ \| /, $hash{synonym}{$joinkey};
	foreach my $syn (@syns) { print OUT "Synonym\t\"$syn\"\n"; } }
    print OUT "Database\t\"NLM_MeSH\" \"UID\" \"$molecule\"\n";
    print OUT "Database\t\"CTD\" \"ChemicalID\" \"$molecule\"\n";
    if ($hash{chebi}{$joinkey}) { print OUT "Database\t\"ChEMI\" \"CHEBI_ID\" \"$hash{chebi}{$joinkey}\"\n"; }
    if ($hash{chemi}{$joinkey}) { print OUT "Database\t\"ChemIDplus\" \"$hash{chemi}{$joinkey}\"\n"; }
    if ($hash{kegg}{$joinkey}) { print OUT "Database\t\"KEGG COMPOUND\" \"ACCESSION_NUMBER\" \"$hash{kegg}{$joinkey}\"\n"; }
    print OUT "\n";
} # foreach my $joinkey (sort {$a<=>$b} keys %{ $hash{molecule} })

close (OUT) or die "Cannot close $outfile : $!";

__END__

Molecule : "C087920"
Public_name "beta-selinene"
Database "NLM_MeSH" "UID" "C087920"
Database "CTD"  "ChemicalID" "C087920"
Database "ChemIDplus"  "17066-67-0"
Database "ChEBI" "CHEBI_ID" "10443"
Database "KEGG COMPOUND" "ACCESSION_NUMBER" "C09723"


    my $result = $dbh->prepare( "SELECT * FROM two_comment WHERE two_comment ~ ?" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) {
    if ($row[0]) { 
    $row[0] =~ s/
	//g;
    $row[1] =~ s/
	//g;
    $row[2] =~ s/
	//g;
    print "$row[0]\t$row[1]\t$row[2]\n";
    } # if ($row[0])
} # while (@row = $result->fetchrow)

__END__

    my $result = $dbh->prepare( 'SELECT * FROM two_comment WHERE two_comment ~ ?' );
$result->execute('elegans') or die "Cannot prepare statement: $DBI::errstr\n"; 

$result->execute("doesn't") or die "Cannot prepare statement: $DBI::errstr\n"; 
my $var = "doesn't";
$result->execute($var) or die "Cannot prepare statement: $DBI::errstr\n"; 

my $data = 'data';
unless (is_utf8($data)) { from_to($data, "iso-8859-1", "utf8"); }

my $result = $dbh->do( "DELETE FROM friend WHERE firstname = 'bl\"ah'" );
(also do for INSERT and UPDATE if don't have a variable to interpolate with ? )

can cache prepared SELECTs with $dbh->prepare_cached( &c. );

if ($result->rows == 0) { print "No names matched.\n\n"; }      # test if no return

$result->finish;        # allow reinitializing of statement handle (done with query)
$dbh->disconnect;       # disconnect from DB

http://209.85.173.132/search?q=cache:5CFTbTlhBGMJ:www.perl.com/pub/1999/10/DBI.html+dbi+prepare+execute&cd=4&hl=en&ct=clnk&gl=us

interval stuff : 
SELECT * FROM afp_passwd WHERE joinkey NOT IN (SELECT joinkey FROM afp_lasttouched) AND joinkey NOT IN (SELECT joinkey FROM cfp_curator) AND afp_timestamp < CURRENT_TIMESTAMP - interval '21 days' AND afp_timestamp > CURRENT_TIMESTAMP - interval '28 days';

casting stuff to substring on other types :
SELECT * FROM afp_passwd WHERE CAST (afp_timestamp AS TEXT) ~ '2009-05-14';

to concatenate string to query result :
  SELECT 'WBPaper' || joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid';
to get :
  SELECT DISTINCT(gop_paper_evidence) FROM gop_paper_evidence WHERE gop_paper_evidence NOT IN (SELECT 'WBPaper' || joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid') AND gop_paper_evidence != '';
