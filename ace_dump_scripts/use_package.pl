#!/usr/bin/perl

# use the get_paper_ace.pm module from /home/postgres/work/citace_upload/papers/ 
# to dump the papers, abstracts (LongText objects), and errors associated with
# them.  2005 07 13
#
# Change to default get all papers, not just valid ones.  2005 11 10
#
# rewrote module to work with DBI.pm, estimated time is now 537 seconds.  2009 04 23
#
# added :
# `/home/postgres/work/pgpopulation/allele_phenotype/20090514_appnbp/get_recent.pl`;
# to fix nbps before each dump (easier than fixing jolene's phenote java timestamp issue)  2009 08 08
#
# got rid of two files, now all in one file.  Rewrote module for faster dumping.  2010 09 07

use strict;
use Jex;

my $date = &getSimpleSecDate();
my $start_time = time;
# my $estimate_time = time + 157;
# my $estimate_time = time + 80;
# my $estimate_time = time + 306;
# my $estimate_time = time + 537;
# my $estimate_time = time + 912;
my $estimate_time = time + 9;
my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime($estimate_time);             # get time
if ($sec < 10) { $sec = "0$sec"; }    # add a zero if needed
if ($min < 10) { $min = "0$min"; }    # add a zero if needed
print "START $date -> Estimate $hour:$min:$sec\n";

$date = &getSimpleDate();

use lib qw( /home/postgres/work/citace_upload/allele_phenotype/ );
# use get_allele_phenotype_ace;
use get_allele_phenotype_phenote_ace;

my $outfile = 'allele_phenotype.ace.' . $date;
my $strain_file = 'strain_phenotype.ace.' . $date;
# my $outlong = 'abstracts.ace.' . $date;
my $errfile = 'err.out.' . $date;
open (OUT, ">$outfile") or die "Cannot create $outfile : $!\n";
# open (STR, ">$strain_file") or die "Cannot create $strain_file : $!\n";
# open (LON, ">$outlong") or die "Cannot create $outlong : $!\n";
open (ERR, ">$errfile") or die "Cannot create $errfile : $!\n";


# my ($all_entry, $long_text, $err_text) = &getPaper('00000003');
# my ($all_entry, $long_text, $err_text) = &getPaper('valid');
# my ($all_entry, $allstrain_entry, $err_text) = &getAllelePhenotype('all');

my ($all_entry, $err_text) = &getAllelePhenotype('all');
# my ($all_entry, $err_text) = &getAllelePhenotype('WBVar00088030');

# my ($all_entry, $allstrain_entry, $err_text) = &getAllelePhenotype('a83');
# my ($all_entry, $allstrain_entry, $err_text) = &getAllelePhenotype('it129');

# my ($all_entry, $err_text) = &getAllelePhenotype('x13');
# my ($all_entry, $err_text) = &getAllelePhenotype('bx123');
# my ($all_entry, $err_text) = &getAllelePhenotype('tm1821');

print OUT "$all_entry\n";
# print STR "$allstrain_entry\n";
# print LON "$long_text\n";
if ($err_text) { print ERR "$err_text\n"; }

close (OUT) or die "Cannot close $outfile : $!";
# close (STR) or die "Cannot close $strain_file : $!";
# close (LON) or die "Cannot close $outlong : $!";
close (ERR) or die "Cannot close $errfile : $!";

# fix nbps before each dump (easier than fixing jolene's phenote java timestamp issue)  2009 08 08
`/home/postgres/work/pgpopulation/allele_phenotype/20090514_appnbp/get_recent.pl`;

$date = &getSimpleSecDate();
my $end_time = time;
my $diff_time = $end_time - $start_time;
print "DIFF $diff_time\n";
print "END $date\n";
