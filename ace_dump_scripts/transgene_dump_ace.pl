#!/usr/bin/perl -w

# dump phenote transgene .ace data.
# set cronjob for 6 am fridays for spica to pick it up  2008 10 14
#
# a lot of fields are now multiontology / multidropdown, and need to be split on "," 
# while others still need to be split on | because they're just text with pipes 
# manually entered.  
# added restriction that it must have summary OR remark (for Karen)  2010 08 26
#
# dump Gene tags as multiontology.  2010 09 27
#
# 0 6 * * fri /home/acedb/wen/phenote_transgene/transgene_dump_ace.pl


use strict;
use diagnostics;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my $directory = '/home/acedb/wen/phenote_transgene';
chdir($directory) or die "Cannot go to $directory ($!)";

my $date = &getSimpleDate();
my $outfile = 'transgene.ace.' . $date;
open (OUT, ">$outfile") or die "Cannot open $outfile : $!";
my $outfile2 = 'transgene.ace';
open (OU2, ">$outfile2") or die "Cannot open $outfile2 : $!";

my @tables = qw( name summary driven_by_gene reporter_product other_reporter gene integrated_by particle_bombardment strain map map_paper map_person marker_for marker_for_paper reference remark species synonym driven_by_construct location movie picture objpap_falsepos );

my %hash;

foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM trp_$table ORDER BY trp_timestamp;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
	if ($row[0]) { $hash{$table}{$row[0]} = $row[1]; } }
} # foreach my $table (@tables)

foreach my $joinkey (sort keys %{ $hash{name} }) {
    next if ($hash{objpap_falsepos}{$joinkey});   # skip fail entries  2010 08 26
    next unless ($hash{name}{$joinkey});  # skip deleted ones without name  2008 10 30
    next unless ( ($hash{summary}{$joinkey}) || ($hash{remark}{$joinkey}) );      # skip unless it has either summary or remark (for Karen) 2010 08 26
    print OUT "Transgene : $hash{name}{$joinkey}\n";
    print OU2 "Transgene : $hash{name}{$joinkey}\n";
    if ($hash{summary}{$joinkey}) { &printTag('Summary', $hash{summary}{$joinkey}); }
    if ($hash{driven_by_gene}{$joinkey}) { &printTag('Driven_by_gene', $hash{driven_by_gene}{$joinkey}); }
    if ($hash{reporter_product}{$joinkey}) { &printTag('Reporter_product', $hash{reporter_product}{$joinkey}); }
    if ($hash{other_reporter}{$joinkey}) { &printTag('Other_reporter', $hash{other_reporter}{$joinkey}); }
    if ($hash{gene}{$joinkey}) { &printTag('Gene', $hash{gene}{$joinkey}); }
    if ($hash{integrated_by}{$joinkey}) { &printTag('Integrated_by', $hash{integrated_by}{$joinkey}); }
    if ($hash{particle_bombardment}{$joinkey}) { &printTag('Particle_bombardment', $hash{particle_bombardment}{$joinkey}); }
    if ($hash{strain}{$joinkey}) { &printTag('Strain', $hash{strain}{$joinkey}); }
    if ($hash{map}{$joinkey}) { &printTag('Map', $hash{map}{$joinkey}); }
    if ($hash{map_person}{$joinkey}) { &printTag("Map_evidence\tPerson_evidence", $hash{map_person}{$joinkey}); }
    if ($hash{map_paper}{$joinkey}) { &printTag("Map_evidence\tPaper_evidence", $hash{map_paper}{$joinkey}); }
    if ($hash{marker_for}{$joinkey}) { &printTag('Marker_for', $hash{marker_for}{$joinkey}, $joinkey); }
    if ($hash{reference}{$joinkey}) { &printTag('Reference', $hash{reference}{$joinkey}); }
    if ($hash{remark}{$joinkey}) { &printTag('Remark', $hash{remark}{$joinkey}); }
    if ($hash{species}{$joinkey}) { &printTag('Species', $hash{species}{$joinkey}); }
    if ($hash{synonym}{$joinkey}) { &printTag('Synonym', $hash{synonym}{$joinkey}); }
    if ($hash{driven_by_construct}{$joinkey}) { &printTag('Driven_by_construct', $hash{driven_by_construct}{$joinkey}); }
    if ($hash{location}{$joinkey}) { &printTag('Location', $hash{location}{$joinkey}); }
    if ($hash{movie}{$joinkey}) { &printTag('Movie', $hash{movie}{$joinkey}); }
    if ($hash{picture}{$joinkey}) { &printTag('Picture', $hash{picture}{$joinkey}); }
    print OUT "\n";
    print OU2 "\n";
} # foreach my $joinkey (sort keys %{ $hash{name} })

close (OUT) or die "Cannot close $outfile : $!";
close (OU2) or die "Cannot close $outfile2 : $!";

sub printTag {
    my ($tag, $data, $joinkey) = @_;
    my @data = ();
    if ( ($tag eq 'Gene') || ($tag eq 'Driven_by_gene') || ($tag eq 'Reporter_product') || ($tag eq 'Map') || ($tag eq "Map_evidence\tPerson_evidence") || ($tag eq "Map_evidence\tPaper_evidence") || ($tag eq 'Location') || ($tag eq 'Reference') ) { $data =~ s/^"//; $data =~ s/"$//; (@data) = split/\",\"/, $data; }
    else { (@data) = split/ \| /, $data; }
#   my (@data) = split/,/, $data; 
    foreach my $data (@data) { 
	$data =~ s/\"//g;
	$data =~ s/\n/ /g;          # replace all newlines with spaces  2010 10 29
	$data =~ s/  / /g;          # replace all double spaces with single spaces  2010 10 29
	print OUT "$tag\t\"$data\"\n";
	print OU2 "$tag\t\"$data\"\n";
	if ($tag eq 'Marker_for') { if ($hash{marker_for_paper}{$joinkey}) { &printTag( "Marker_for\t\"$data\"\tPaper_evidence\t", $hash{marker_for_paper}{$joinkey}) ; } } }
} # sub printTag

__END__


    my $result = $conn->exec( "SELECT * FROM one_groups;" );
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
