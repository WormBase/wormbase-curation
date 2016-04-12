#!/usr/bin/perl

# Check out and display PhenOnt.obo  

# for carol  2006 12 07
#
# changed cvs to be from spica, not local.  gary and raymond migrated cvs to spica.  2010 05 26
#
# spica moved, cvs file now just a file, not whole PhenOnt/ directory  2013 07 08





use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate

my $query = new CGI;	# new CGI form

print "Content-type: text/plain\n\n";

my ($oop, $short) = &getHtmlVar($query, 'short');
if (defined ($short)) { 
  print <<"EndOfText";
format-version: 1.2
date: 25:03:2008 14:52
saved-by: garys
auto-generated-by: OBO-Edit 1.002
subsetdef: phenotype_slim_wb "WB phenotype slim"
synonymtypedef: three_letter_name "Short_name" BROAD
default-namespace: C_elegans_phenotype_ontology


[Term]
id: WBPhenotype0000000
name: chromosome_instability
is_a: WBPhenotype0000585 ! cell_homeostasis_metabolism_abnormal


[Term]
id: WBPhenotype0000001
name: body_posture_abnormal
def: "Characteristic sinusoidal body posture is altered." [WB:cab]
subset: phenotype_slim_wb
is_a: WBPhenotype0000525 ! organism_behavior_abnormal
EndOfText
}

else {


my $directory = '/home/postgres/work/citace_upload/allele_phenotype/temp';
chdir($directory) or die "Cannot go to $directory ($!)";
`/home/azurebrd/public_html/cgi-bin/forms/helper/spica_cvs.sh`;	# this shell script just calls the next two commented out lines since perl has trouble with the @spica part.  2010 05 26
# export CVSROOT=':pserver:anonymous@spica.caltech.edu:/PhenOnt'	# new commands with spica move 2013 07 08
# /usr/bin/cvs co PhenOnt.obo

# `export CVSROOT=':pserver:anonymous@spica.caltech.edu:/cvs'`;	# this doesnt work from perl
# `cvs checkout PhenOnt`;
# `cvs -d /var/lib/cvsroot checkout PhenOnt`;			# this was when tazendra hosted cvs
# my $file = $directory . '/PhenOnt/PhenOnt.obo';
my $file = $directory . '/PhenOnt.obo';				# new location with spica move 2013 07 08
$/ = "";
open (IN, "<$file") or die "Cannot open $file : $!";
while (my $para = <IN>) { print "$para\n"; }
close (IN) or die "Cannot close $file : $!";
$directory .= '/PhenOnt';
# `rm -rf $directory`;
`rm -rf $file`;		# just the file now 2013 07 08

}
