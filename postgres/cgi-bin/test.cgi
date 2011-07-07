#!/usr/bin/perl 

# Link all the CGIs from azurebrd and postgres (this page).

# get CGIs from /home/[postgres|azurebrd]/public_html/cgi-bin

# Added Igor's RNAi form at elbrus.caltech.edu  2005 04 14


use LWP::Simple;

use CGI;
use Fcntl;
use strict;


# make beginning of HTML page

print "Content-type: text/html\n\n";
print <<"EndOfText";
<HTML>
<LINK rel="stylesheet" type="text/css" href="http://mangolassi.caltech.edu/~azurebrd/stylesheets/wormbase.css">
<HEAD>
<TITLE>Site Map -- PGSQL display Tazendra</TITLE>
</HEAD>
<BODY bgcolor=#000000 text=#000000 link=#cccccc>
EndOfText
# print "$header";



print "STUFF test STUFF<BR>\n";
`/home/postgres/public_html/cgi-bin/bltest.pl`;
print "STUFF test STUFF<BR>\n";

__END__

my %curation;				# names and urls of curation CGIs
my @pgpdfs = </home/postgres/public_html/cgi-bin/*.cgi>;
my $path = "/home/postgres/public_html/cgi-bin/";

print "General CGIs under postgres :<BR>\n";
print "<TABLE>\n";
foreach $_ (@pgpdfs) {
  chomp;
  $_ =~ m/\/home\/postgres\/public_html\/cgi-bin\/(.*)/;
  my $name = $1;			# name of the cgi
  my $url = "http://mangolassi.caltech.edu/~postgres/cgi-bin/" . $name;	# url to it
  if ($name =~ m/^curation/) { 		# curation forms
    $curation{$name} = $url;
  } elsif ($name eq 'checkout.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'allele_phenotype_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'anatomy_function.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'anatomy_term_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'ccc_go_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'concise_description.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'concise_description_new.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'concise_description_checkout.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'condition_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'gene_gene_interaction.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'go_batch.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'go_curation_new.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'go_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'genefunction.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'paper_gene.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'paper_gene_exclusion.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'paper_locus_exclusion.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'paper_locus.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'phenotype_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'phenotype_assay_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'rnai_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'transgene_curation.cgi') {
    $curation{$name} = $url;
  } elsif ($name eq 'yh_curation.cgi') {
    $curation{$name} = $url;
  } else { 				# general forms
    print "<TR>";
    print "<TD WIDTH=150><A HREF=\"$url\">$name</A></TD>";
    &getLine($path, $name);
    print "<TD>$url</TD>";
    print "</TR>\n";
  } # if ($name =~ m/^curation/) 
} # foreach $_ (@pgpdfs) 
print "</TABLE><BR><HR><BR>\n";


print "Curation Forms :<BR>";
print "<TABLE>\n";
foreach my $name (sort keys %curation) {
    print "<TR>";
    print "<TD WIDTH=150><A HREF=\"$curation{$name}\">$name</A></TD>";
    &getLine($path, $name);
    print "<TD>$curation{$name}</TD>";
    print "</TR>\n";
} # foreach $_ (sort keys %curation)
print "<TR>";
print "<TD WIDTH=150><A HREF=\"http://elbrus.caltech.edu/cgi-bin/igor/rnaitools/rnai_curation\">rnai_curation</A></TD>";
print "<TD></TD><TD WIDTH=400>Igor's RNAi Form</TD><TD></TD>";
print "<TD>http://elbrus.caltech.edu/cgi-bin/igor/rnaitools/rnai_curation</TD>";
print "</TR>\n";
print "</TABLE><BR><HR><BR>\n";

my @azupdfs = </home/azurebrd/public_html/cgi-bin/*.cgi>;
$path = "/home/azurebrd/public_html/cgi-bin/";
print "General CGIs under azurebrd :<BR>\n";
print "<TABLE>\n";
foreach $_ (@azupdfs) {
  chomp;
  $_ =~ m/\/home\/azurebrd\/public_html\/cgi-bin\/(.*)/;
  my $name = $1;			# name of the cgi
  my $url = "http://mangolassi.caltech.edu/~azurebrd/cgi-bin/" . $name;	# url to it
  if ($name =~ m/^curation/) { 		# curation forms
    $curation{$name} = $url;
  } else { 				# general forms
    print "<TR>";
    print "<TD WIDTH=150><A HREF=\"$url\">$name</A></TD>";
    &getLine($path, $name);
    print "<TD>$url</TD>";
    print "</TR>\n";
  } # if ($name =~ m/^curation/) 
} # foreach $_ (@azupdfs) 
print "</TABLE><BR><HR><BR>\n";

my @formpdfs = </home/azurebrd/public_html/cgi-bin/forms/*.cgi>;
$path = "/home/azurebrd/public_html/cgi-bin/forms/";
print "Submission / Update Forms :<BR>\n";
print "<TABLE>\n";
foreach $_ (@formpdfs) {
  chomp;
  $_ =~ m/\/home\/azurebrd\/public_html\/cgi-bin\/forms\/(.*)/;
  my $name = $1;			# name of the cgi
  my $url = "http://mangolassi.caltech.edu/~azurebrd/cgi-bin/forms/" . $name;	# url to it
  if ($name =~ m/^curation/) { 		# curation forms
    $curation{$name} = $url;
  } else { 				# general forms
    print "<TR>";
    print "<TD WIDTH=150><A HREF=\"$url\">$name</A></TD>";
    &getLine($path, $name);
    print "<TD>$url</TD>";
    print "</TR>\n";
  } # if ($name =~ m/^curation/) 
} # foreach $_ (@formpdfs) 
print "</TABLE><BR><HR><BR>\n";

my @quepdfs = </home/azurebrd/public_html/cgi-bin/query_builder/*.cgi>;
$path = "/home/azurebrd/public_html/cgi-bin/query_builder/";
print "Query Builder :<BR>\n";
print "<TABLE>\n";
foreach $_ (@quepdfs) {
  chomp;
  $_ =~ m/\/home\/azurebrd\/public_html\/cgi-bin\/query_builder\/(.*)/;
  my $name = $1;			# name of the cgi
  my $url = "http://mangolassi.caltech.edu/~azurebrd/cgi-bin/query_builder/" . $name;	# url to it
  if ($name =~ m/^curation/) { 		# curation forms
    $curation{$name} = $url;
  } else { 				# general forms
    print "<TR>";
    print "<TD WIDTH=150><A HREF=\"$url\">$name</A></TD>";
    &getLine($path, $name);
    print "<TD>$url</TD>";
    print "</TR>\n";
  } # if ($name =~ m/^curation/) 
} # foreach $_ (@quepdfs) 
print "</TABLE><BR><HR><BR>\n";

my @cecpdfs = </home/postgres/public_html/cgi-bin/cecilia/*.cgi>;
$path = "/home/postgres/public_html/cgi-bin/cecilia/";
print "Cecilia's :<BR>\n";
print "<TABLE>\n";
foreach $_ (@cecpdfs) {
  chomp;
  $_ =~ m/\/home\/postgres\/public_html\/cgi-bin\/cecilia\/(.*)/;
  my $name = $1;			# name of the cgi
  my $url = "http://mangolassi.caltech.edu/~postgres/cgi-bin/cecilia/" . $name;	# url to it
  if ($name =~ m/^curation/) { 		# curation forms
    $curation{$name} = $url;
  } else { 				# general forms
    print "<TR>";
    print "<TD WIDTH=150><A HREF=\"$url\">$name</A></TD>";
    &getLine($path, $name);
    print "<TD>$url</TD>";
    print "</TR>\n";
  } # if ($name =~ m/^curation/) 
} # foreach $_ (@cecpdfs) 
print "</TABLE><BR><HR><BR>\n";

# print "$footer";

print <<"EndOfText";
<BODY></HTML>
EndOfText


sub getLine {
  my ($path, $name) = @_;
  my $file = $path . $name;
  open (IN, "<$file") or die "Cannot open $file : $!";
  <IN>; <IN>; 
  my $line = <IN>;
  $line =~ s/^# //g;
  print "<TD></TD><TD WIDTH=400>$line</TD><TD></TD>";
  close (IN) or die "Cannot close $file : $!";
} # sub getLine
