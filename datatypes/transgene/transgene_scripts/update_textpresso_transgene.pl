#!/usr/bin/perl -w

# update cur_transgene based on textpresso data for Andrei.
#
# run every sunday after Arun runs his script on Saturday.  2008 06 27
#
# run every day after Arun runs his script on Saturday.  for Karen.  2009 02 20
#
# 0 4 * * * /home/postgres/work/pgpopulation/textpresso/transgene/update_textpreso_cur_transgene.pl
#
# updated to work for trp_ tables and tfp_transgene table.  2009 04 09
#
# forgot to put $/ back to "\n"   2009 04 13
#
# my ($paper, $tg) = $line =~ m/^(\S+)\s+(.*)$/;  arun changed the format again.  2010 02 27
#
# rewrote to use "," instead of | on trp_reference.  also use trp_objpap_falsepos instead of ObsoleteTg.txt
# (which has been populated into trp_objpap_falsepos and hardcoded hIn1 mIn1 as names to always ignore.
# not writing output to 3 files since not sure anyone's looking at the second file for In transgenes.  
# Need to update this on tazendra when going live with phenote to OA switch.  2010 08 24
#
# live  2010 08 26
#
# wrapped in 
# 0 4 * * * /home/postgres/work/pgpopulation/textpresso/wrapper.sh



use strict;
use diagnostics;
use DBI;
use LWP::Simple;
use Jex;

my $date = &getSimpleDate();
my $timestamp = &getSimpleSecDate();

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $result;

my $directory = '/home/postgres/work/pgpopulation/textpresso/transgene';
chdir($directory) or die "Cannot go to $directory ($!)";


$/ = undef;
my $full_file = 'transgenes_in_regular_papers.out';
open (IN, "<$full_file") or die "Cannot open $full_file : $!";
my $last_data = <IN>;
close (IN) or die "Cannot close $full_file : $!";
$/ = "\n";

my $new_data = get "http://textpresso-dev.caltech.edu/transgene/transgenes_in_regular_papers.out";
# UNCOMMENT THIS
exit if ($last_data eq $new_data);


open (OUT, ">$full_file") or die "Cannot rewrite $full_file : $!";
print OUT $new_data;
close (OUT) or die "Cannot close $full_file : $!";

my (@tlines) = split/\n/, $new_data;
my @pgcommands;

# no longer populate textpresso firstpass tables for this, transgene is not a FP curation field in form.  2010 08 224
#
# my $logfile = $directory . '/logfile.pg';
# open (LOG, ">$logfile") or die "Cannot rewrite $logfile : $!";
#
# push @pgcommands, "DELETE FROM tfp_transgene;";
# foreach my $line (@tlines) {
#   my ($paper, @transgenes) = split/\s+/, $line;
#   if ($paper =~ m/(WBPaper\d+)/) { $paper = $1; }
#   my ($joinkey) = $paper =~ m/WBPaper(\d+)/;
#   push @pgcommands, "INSERT INTO tfp_transgene VALUES ('$joinkey', '$line');";
# } # foreach my $line (@tlines)
# 
# foreach my $command (@pgcommands) {
#   print LOG "$command\n";
#   $result = $dbh->do( $command );
# } # foreach my $command (@pgcommands)
# 
# close (LOG) or die "Cannot close $logfile : $!";


my $outfile  = $directory . '/transgene_textpresso';
my $outfile2 = $directory . '/new_transgene_textpresso';
my $outfile3 = $directory . '/transgene_textpresso.pg';
# open (OUT, ">>$outfile") or die "Cannot create $outfile : $!";
# open (OU2, ">>$outfile2") or die "Cannot create $outfile2 : $!";
# open (OU3, ">>$outfile3") or die "Cannot create $outfile3 : $!";

my %syns;
my %valid;
$result = $dbh->prepare( "SELECT trp_name.trp_name, trp_synonym.trp_synonym FROM trp_name, trp_synonym WHERE trp_name.joinkey = trp_synonym.joinkey;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { 
    my (@syns) = split/ \| /, $row[1];
    $valid{$row[0]}++;
    foreach my $syn (@syns) {
	$valid{$syn}++;
	$syns{$syn} = $row[0]; } }
$result = $dbh->prepare( "SELECT trp_name FROM trp_name;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $valid{$row[0]}++; }


my %obs;

# no longer use flatfile, use trp_objpap_falsepos table (Fail) 2010 08 24
# my $infile = '/home/acedb/wen/phenote_transgene/ObsoleteTg.txt';
# open (IN, "<$infile") or die "Cannot open $infile : $!";
# while (my $line = <IN>) {
#   chomp $line;
#   next unless $line;
#   next if ($line =~ m/^\/\//);
# #   my ($tg, $paper, $comment) = split/\t/, $line;    # wen keeps forgetting tabs
#   my ($tg, $paper);
#   if ($line =~ m/^(\S+)\s+(\S+)/) { $tg = $1; $paper = $2; }
#   $tg =~ s/\s+//g;
#   unless ($paper) { $paper = 'all'; }
#   $obs{$tg}{$paper}++;
# #   print "OBS $tg PAP $paper E\n";
# } # while (my $line = <IN>) {
# close (IN) or die "Cannot close $infile : $!";

$result = $dbh->prepare( "SELECT trp_name.joinkey, trp_name.trp_name, trp_reference.trp_reference FROM trp_name, trp_reference WHERE trp_name.joinkey = trp_reference.joinkey AND trp_name.joinkey IN (SELECT joinkey FROM trp_objpap_falsepos WHERE trp_objpap_falsepos = 'Fail');" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { 
    my (@papers) = split/","/, $row[2];
    foreach my $pap (@papers) { $pap =~ s/\"//g; $obs{$row[1]}{$pap}++; } }
$obs{hIn1}{all}++;
$obs{mIn1}{all}++;


my %tdata;
foreach my $line (@tlines) {
    chomp $line;
#   my ($paper, $tg) = split/  /, $line;
    my ($paper, $tg) = $line =~ m/^(\S+)\s+(.*)$/;        # arun changed the format again  2010 02 27
    ($paper) = $paper =~ m/(WBPaper\d+)/;
#   unless ($tg) { print "-- NO TG $line\n"; }
    my (@tg) = split/\s/, $tg;
    foreach my $tg (@tg) { 
	if ($syns{$tg}) { $tg = $syns{$tg}; }
	next if ($obs{$tg}{'all'});
	next if ($obs{$tg}{$paper});
	$tdata{$tg}{$paper}++; 
    }
} # foreach my $line (@lines)

my %pdata;
$result = $dbh->prepare( "SELECT trp_name.trp_name, trp_reference.trp_reference FROM trp_name, trp_reference WHERE trp_name.joinkey = trp_reference.joinkey;" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { 
    my $tg = $row[0];
#   my (@papers) = split/ | /, $row[1];
    my (@papers) = split/\",\"/, $row[1];
    foreach my $paper (@papers) { $paper =~ s/\"//g; delete $tdata{$tg}{$paper}; } }

foreach my $tg (sort keys %tdata) {
    my (@papers) = sort keys %{ $tdata{$tg} };
#   my $papers = join" | ", @papers;
    if ($papers[0]) {
	if ($valid{$tg}) { &addToTg($tg, \@papers, $timestamp ); }
	elsif ($tg =~ m/In/) { 1; } # print OU2 "$timestamp new $tg in $papers\n"; { # }
	else { &newTg($tg, \@papers, $timestamp ); }
    } # if ($papers)
} # foreach my $paper (sort keys %tdata)

# close (OUT) or die "Cannot close $outfile : $!";
# close (OU2) or die "Cannot close $outfile2 : $!";
# close (OU3) or die "Cannot close $outfile3 : $!";


# print "not same\n";


sub addToTg {
    my ($tg, $arref_papers, $date) = @_;
    my @papers = @$arref_papers; 
    my %papers;
    my $papers = join"\",\"", @papers; $papers = '"' . $papers . '"';
    foreach (@papers) { $papers{$_}++; }
    my @pgcommands;
    print "\nADD to tg $date more papers $tg in $papers\n"; 
#   print OUT "$date more papers $tg in $papers\n"; 
    my %joinkeys;                                 # get all joinkeys that refer to this Tg
    $result = $dbh->prepare( "SELECT * FROM trp_name WHERE trp_name = '$tg';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $joinkeys{$row[0]}++; }
    foreach my $joinkey (keys %joinkeys) {        # for all joinkeys of that Tg
	$result = $dbh->prepare( "SELECT trp_reference FROM trp_reference WHERE joinkey = '$joinkey';" );
	$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
	my @row = $result->fetchrow;
	if ($row[0]) {                              # if there's a reference, append it
	    my (@paps) = split/\",\"/, $row[0]; foreach (@paps) { $_ =~ s/\"//g; $papers{$_}++; }
#       $papers = "$row[0] | $papers"; 
	    (@paps) = sort keys %papers; $papers = join"\",\"", @paps; $papers = '"' . $papers . '"';
	    my $command = "UPDATE trp_reference SET trp_reference = '$papers' WHERE joinkey = '$joinkey';";
	    push @pgcommands, $command;
#       print OU3 "$command -- $date\n";
#       my $result2 = $dbh->do( $command );
	} else {                                    # if new reference, add it
	    my $command = "INSERT INTO trp_reference VALUES ('$joinkey', '$papers');";
	    push @pgcommands, $command;
#       print OU3 "$command -- $date\n";
#       my $result2 = $dbh->do( $command );
	}
	my $command = "INSERT INTO trp_reference_hst VALUES ('$joinkey', '$papers');";
	push @pgcommands, $command;
#     print OU3 "$command -- $date\n";
#     my $result2 = $dbh->do( $command );
    } # foreach my $joinkey (keys %joinkeys)
    foreach my $pgcommand (@pgcommands) {
	print "$pgcommand  -- $date\n";
# UNCOMMENT TO POPULATE PG
	my $result2 = $dbh->do( $pgcommand );
    }
} # sub addToTg

sub newTg {
    my ($tg, $arref_papers, $date) = @_;
    my @papers = @$arref_papers;
    my $papers = join"\",\"", @papers; $papers = '"' . $papers . '"';
    my @pgcommands;
    my $joinkey = 0;
    $result = $dbh->prepare( "SELECT * FROM trp_name;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { if ($row[0] > $joinkey) { $joinkey = $row[0]; } }
    $joinkey++;
    print "\nNEW tg $date new $tg in $papers\n"; 
#   print OUT "$date new $tg in $papers\n"; 
    my $command = "INSERT INTO trp_name VALUES ('$joinkey', '$tg');";
    push @pgcommands, $command;
#   print OU3 "$command -- $date\n";
#   my $result2 = $dbh->do( $command );
    $command = "INSERT INTO trp_name_hst VALUES ('$joinkey', '$tg');";
    push @pgcommands, $command;
#   print OU3 "$command -- $date\n";
#   $result2 = $dbh->do( $command );
    $command = "INSERT INTO trp_reference VALUES ('$joinkey', '$papers');";
    push @pgcommands, $command;
#   print OU3 "$command -- $date\n";
#   $result2 = $dbh->do( $command );
    $command = "INSERT INTO trp_reference_hst VALUES ('$joinkey', '$papers');";
    push @pgcommands, $command;
#   print OU3 "$command -- $date\n";
#   $result2 = $dbh->do( $command );
    $command = "INSERT INTO trp_curator VALUES ('$joinkey', 'WBPerson4793');";
    push @pgcommands, $command;
    $command = "INSERT INTO trp_curator_hst VALUES ('$joinkey', 'WBPerson4793');";
    push @pgcommands, $command;
    foreach my $pgcommand (@pgcommands) {
	print "$pgcommand  -- $date\n";
# UNCOMMENT TO POPULATE PG
	my $result2 = $dbh->do( $pgcommand );
    }
} # sub newTg


__END__

#!/usr/bin/perl -w

# look at textpresso transgene data and update postgres based on that.  
# 2008 10 07
#
# wasn't checking regular names, oops.  2008 10 20
#
#
# update postgres based on value, cron job 
# 0 2 * * mon /home/postgres/work/pgpopulation/transgene/textpresso_transgene/textpresso_transgene.pl
# 2008 10 14
#
# run every day  2009 02 23
# 0 2 * * * /home/postgres/work/pgpopulation/transgene/textpresso_transgene/textpresso_transgene.pl

    use LWP::Simple;
use strict;
use diagnostics;
use Pg;
use Jex;

my $directory = '/home/postgres/work/pgpopulation/transgene/textpresso_transgene';
chdir($directory) or die "Cannot go to $directory ($!)";

my $conn = Pg::connectdb("dbname=testdb");
die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;

my $date = &getSimpleSecDate();


__END__
