#!/usr/bin/perl

use strict;

#------------------ Move data under invalid papers -------------
print "This script screen Textpresso output of transgenes, get rid of those already exist in WormBase.\n";
print "Input file 1: WSTg.ace lists all transgenes already in WormBase\n";
print "Input file 2: transgenes_summary.out output file from Textpresso\n";
print "Output file: NewTg.txt\n";

open (IN1, "WSTg.ace") || die "can't open $!";
my ($line, $tg, $i);
my %TgExist;
my %TgPaperCount;
my %TgSummary;

my $TotalNewTg = 0;
my $TotalPriTg = 0;
my @tmp;
my @stuff;

while ($line=<IN1>) {
    chomp($line);
    ($stuff[0], $tg) = split '"', $line;
    $TgExist{$tg} = 1;
}
close(IN1);

open (IN2, "transgenes_summary.out") || die "can't open $!";
open (OUT, ">NewTg.txt") || die "can't open $!";
open (PRI, ">NewTgHighPriority.txt") || die "can't open $!";

while ($line = <IN2>) {
    chomp($line);
    if ($line =~ /^---/) {
        #Do nothing.
        $tg = "";
    } elsif ($line =~ /^WBP/) {
        #Do nothing.
    } else {
        if ($line =~ /Ex/) {
            if ($TgExist{$line}) {
                #Do nothing.
            } else {
                $tg = $line;
                $TotalNewTg++;
                $i = 0;
                @tmp = ();
                print OUT "$tg\n";
                $tmp[$i] = $tg; 
                while ($line ne "----------") {
                    $line = <IN2>;
                    chomp ($line);
                    print OUT "$line\n";
                    $i++;
                    $tmp[$i] = $line;
                }               
                $TgPaperCount{$tg} = $i - 1;
                if ($i > 2) {
		    foreach (@tmp) {
			print PRI "$_\n";
		    }
		    $TotalPriTg++;
                }
            }
        }
    }
}

close(IN2);
close(OUT);

print "$TotalNewTg new Ex transgenes found.\n";
print "$TotalPriTg Ex transgenes have more than 2 paper entries.\n";
