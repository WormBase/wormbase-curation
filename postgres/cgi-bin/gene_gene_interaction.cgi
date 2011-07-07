#!/usr/bin/perl -w

# gene gene interaction form for Xiadong

# gene gene interaction form for Andrei
# 
# Read sentences from flatfile.  By default look at last sentence (joinkey)
# entered in ggi_gene_gene_interaction, and read the next sentence.  Either :
# click on no genes and (No_interaction / Possible_genetic / Possible_non-genetic)
# or click on two genes and click on any other option.  Go back and reselect
# options to enter more than 3 connections / sentence. 
# New option to dump out last 10 sentences with connections.
# New option to search by sentence number.  2006 03 14
#
# Using new source file  2007 01 08
#
# Using new source file  2008 03 10
#
# Added @interaction ``Interaction'' for Xiaodong.  2010 01 20
#
# Using new source file for Xiaodong.  Backed up and wiped out ggi_gene_gene_interactions
# so new dump file will use new set.  
# .ace dumper at /home/acedb/xiaodong/gene_gene_interaction/dump_ggi_ace.pl
# 2009 10 02
# 
# There's extra junk tab now for some reason  2010 08 10


use strict;
use CGI;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $query = new CGI;


my @interaction = qw( No_interaction Interaction Suppression Enhancement Mutual_enhancement Mutual_suppression Synthetic Epistasis Other_Genetic Regulatory Physical_interaction Other_Non-genetic Possible_genetic Possible_non-genetic );

# my $src_file = '/home/postgres/work/pgpopulation/andrei_genegeneinteraction/20060306-secondpass/html_20060307.txt';
# my $src_file = '/home/postgres/work/pgpopulation/andrei_genegeneinteraction/20070108-automatic/ggi_update.filter';
# my $src_file = '/home/postgres/work/pgpopulation/andrei_genegeneinteraction/20080310-newtextpresso/ggi_lines';
my $src_file = '/home/postgres/work/pgpopulation/genegeneinteraction/20091002-xiaodong/ggi_20091002';

&printHeader('gene gene interaction');
&process();
&printFooter();

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  if ($action) {
    if ($action eq "Submit !") { &newEntry(); }
    elsif ($action eq "Dump 10 !") { &dump10(); } 
  }

  my $sentence = 0;
  my $result = $dbh->prepare( "SELECT joinkey FROM ggi_gene_gene_interaction ORDER BY joinkey DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  if ($row[0]) { $sentence = $row[0]; }

  if ($action) { if ($action eq "Search !") { (my $var, $sentence) = &getHtmlVar($query, "sent_search"); $sentence--; } }

  open (IN, "<$src_file") or die "Cannot open $src_file : $!";
  my $sentence_count;
  for ( 1 .. $sentence ) { <IN>; $sentence_count++; }
  print "<FORM METHOD=POST ACTION=http://tazendra.caltech.edu/~postgres/cgi-bin/gene_gene_interaction.cgi>\n";
  print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\">\n"; 
  print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dump last 10 sentences : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Dump 10 !\">\n"; 
  print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Search for sentence : <INPUT NAME=\"sent_search\"><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Search !\"><BR>\n"; 
  print "<TABLE>\n";
  my $line = <IN>;
  for my $box (1 .. 3) {
    &readSentence($sentence, $line, $box); $sentence_count++; }
  while (<IN>) { $sentence_count++; }
  print "</TABLE>\n";
  print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\"><BR>\n"; 
  print "</FORM>\n";
  print "There are $sentence_count sentences in the sourcefile $src_file<BR>\n";
  close (IN) or die "Cannot close $src_file : $!";
} # sub process

sub dump10 {
  my $sentence = 0;
  my $result = $dbh->prepare( "SELECT joinkey FROM ggi_gene_gene_interaction ORDER BY joinkey DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; if ($row[0]) { $sentence = $row[0]; } $sentence -= 10;
  open (IN, "<$src_file") or die "Cannot open $src_file : $!";
  for ( 1 .. $sentence ) { <IN>; }
  for my $sent ( ($sentence + 1) .. ($sentence + 10) ) {
    my $sentence = <IN>; 
    print "SENT $sentence\n";
#     print "SELECT * FROM ggi_gene_gene_interaction WHERE joinkey = '$sent';<BR>\n";
    my $result = $dbh->prepare( "SELECT * FROM ggi_gene_gene_interaction WHERE joinkey = '$sent';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { print "$row[2]\t$row[3]\t$row[4]<BR>\n"; }
    print "<P>\n"; }
} # sub dump10


sub newEntry {
  print "You've entered stuff<BR>\n";
  my $badData = 0; my @pgcommands;
  for my $count ( 1 .. 3 ) {
    my ($var, $gene1) = &getHtmlVar($query, "gene_one_$count");
    ($var, my $gene2) = &getHtmlVar($query, "gene_two_$count");
    ($var, my $int) = &getHtmlVar($query, "interaction_$count");
    ($var, my $paps) = &getHtmlVar($query, "paps_$count");
    ($var, my $ggi) = &getHtmlVar($query, "ggi_$count");
    print "Gene1 $gene1 Gene2 $gene2 Interaction $int Paper-Sentence $paps SentenceID $ggi<BR>\n";
    if ($int) {
      if ( ($int eq 'No_interaction') || ($int eq 'Possible_genetic') || ($int eq 'Possible_non-genetic') ) {
          if ( $gene1 || $gene2 ) { print "<FONT COLOR=red>ERROR $int has $gene1 $gene2</FONT><BR>\n"; $badData++; } 
            else { push @pgcommands, "INSERT INTO ggi_gene_gene_interaction VALUES ('$ggi', '$paps', NULL, NULL, '$int', CURRENT_TIMESTAMP);"; } }
        else {
          unless ($gene1) { print "<FONT COLOR=red>ERROR $int has no gene 1</FONT><BR>\n"; $badData++; } 
          unless ($gene2) { print "<FONT COLOR=red>ERROR $int has no gene 2</FONT><BR>\n"; $badData++; } 
          unless ($badData) { push @pgcommands, "INSERT INTO ggi_gene_gene_interaction VALUES ('$ggi', '$paps', '$gene1', '$gene2', '$int', CURRENT_TIMESTAMP);"; } }
    }
  } # for my $count ( 1 .. 3 )
  if ($badData) { print "<FONT COLOR=red>Click BACK, fix the bad data, and resubmit</FONT><P><P>\n"; return; }
    else {
      foreach my $pgcommand (@pgcommands) {
        my $result = $dbh->do( "$pgcommand" );
#         print "COM $pgcommand COM<BR>\n"; 
    } }
  print "<P>\n";
} # sub newEntry

sub readSentence {
  my ($sentence, $line, $count) = @_;
#   my $line = <IN>;
  $sentence++;
#   print "SENT $sentence SENT<BR>\n";
#   print "LINE $line LINE<br />\n";
  my ($line_count, $paps, $genes, $junk, $text) = split/\t/, $line;	# there's extra junk tab now for some reason  2010 08 10
  unless ($line_count == $sentence) { print "<FONT COLOR='red'>ERROR between sentence count in line read $sentence and sentence ID $line_count.</FONT><BR>\n"; }
  my (@genes) = split/, /, $genes;
  print "<TR>\n";
  print "<TD><SELECT NAME=\"gene_one_$count\" SIZE=14>\n";
  print "      <OPTION> </OPTION>\n";
  foreach (@genes) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";
  print "<TD><SELECT NAME=\"gene_two_$count\" SIZE=14>\n";
  print "      <OPTION > </OPTION>\n";
  foreach (@genes) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";
  print "<TD><SELECT NAME=\"interaction_$count\" SIZE=14>\n";
  if ($count == 1) { print "      <OPTION SELECTED>No_interaction</OPTION>\n"; shift @interaction; }
  foreach (@interaction) { print "      <OPTION>$_</OPTION>\n"; }
  if ($count == 1) { unshift @interaction, "No_interaction"; }
  print "    </SELECT></TD>\n ";
  print "<TD>SenteceID $sentence -- $paps<BR><BR>$text</TD>\n";
  print "<INPUT TYPE=HIDDEN NAME=ggi_$count VALUE=\"$sentence\">\n";
  print "<INPUT TYPE=HIDDEN NAME=paps_$count VALUE=\"$paps\">\n";
  print "</TR>\n";
#   return $sentence;
} # sub readSentence
