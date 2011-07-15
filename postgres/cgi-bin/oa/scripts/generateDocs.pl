#!/usr/bin/perl

# generate documentation for ontology annotator-specific perl-based and javascript code.

use strict;
use Tie::IxHash;


my $directory = '/home/postgres/public_html/cgi-bin/oa/';
chdir ($directory) or die "Cannot chdir to $directory : $!";

`pod2html ontology_annotator.cgi > docs/ontology_annotator_CGI.html`;
`pod2html wormOA.pm > docs/wormOA.html`;
`pod2html testOA.pm > docs/testOA.html`;
`pod2html helperOA.pm > docs/helperOA.html`;
`pod2html scripts/create_oac_columns.pl > docs/create_oac_columns.html`;
`pod2html scripts/create_datatype_tables.pl > docs/create_datatype_tables.html`;
`pod2html scripts/update_obo_oa_ontologies.pl > docs/update_obo_oa_ontologies.html`;
`pod2html scripts/generateDocs.pl > docs/generateDocs.html`;
`rm pod2htmd.tmp`;
`rm pod2htmi.tmp`;



$/ = undef;
my $js_file = 'ontology_annotator.js';
open (IN, "<$js_file") or die "Cannot open $js_file : $!";
my $js_data = <IN>;
close (IN) or die "Cannot close $js_file : $!";
$/ = "\n";
if ($js_data =~ m/</) { $js_data =~ s/</&lt;/g; }
if ($js_data =~ m/>/) { $js_data =~ s/>/&gt;/g; }

my $to_print = "<html><body>\n";
my $links_to_sections = '';
my %sections; tie %sections, "Tie::IxHash";
my $documentation = '';
my $current_depth = 0;

my (@paras) = $js_data =~ m/\n\/\*\*\s*?\n(.*?)\n \*\//sg;
foreach my $para (@paras) {
  my (@lines) = split/\n/, $para;
  if ($lines[0] =~ m/^ \* ( +)\w/) { 
    my $spaces = $1; my (@count) = split//, $spaces; my $count = scalar(@count);
    my $line = shift @lines;
    $line =~ s/^ \* ?//;
    if ($count == '1') { $documentation .= "<hr>\n"; }	# add an <hr> before <h1> headers.
    if ($current_depth < $count) { $links_to_sections .= "<ul>\n"; $current_depth = $count; }
    elsif ($current_depth > $count) { $links_to_sections .= "</ul>\n"; $current_depth = $count; }
    my $section = $line; $section =~ s/ /_/g;
    $links_to_sections .= "<li><a href=\"#$section\">$line</a></li>\n";
    $documentation .= "<h$count><a name=\"$section\">$line</a></h$count>"; }
  $documentation .= "<p>\n";
  foreach my $line (@lines) {
    $line =~ s/^ \* ?//;
    if ($line) { $documentation .= "$line<br />\n"; }
  } # foreach my $line (@lines)
  $documentation .= "</p>\n\n";
} # foreach my $para (@paras)
for (1 .. $current_depth) { $links_to_sections .= "</ul>\n"; }
$to_print .= $links_to_sections;
$to_print .= $documentation;
$to_print .= '</body></html>';

my $doc_file = 'docs/ontology_annotator_JS.html';
open (OUT, ">$doc_file") or die "Cannot create $doc_file : $!";
print OUT $to_print;
close (OUT) or die "Cannot close $doc_file : $!";


__END__


=head1 NAME

generateDocs.pl - script to generate documentation for ontology annotator-specific javascript, perl scripts, perl modules, and main perl CGI.


=head1 SYNOPSIS

Run with

  ./generateDocs.pl


=head1 DESCRIPTION

The ontology_annotator.cgi uses multiple custom perl modules, scripts, a perl CGI, and a javascript module.  This script calls pod2html from the shell to generate documentation for perl-based files ;  and reads ontology_annotator.js to generate documentation to an html file based on the /* * */ paragraph comments, converting < > to &lt; &gt;, putting paragraphs in <p> and lines in <br>.

Run with

  ./generateDocs.pl

