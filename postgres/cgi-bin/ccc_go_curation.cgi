#!/usr/bin/perl -w

# ccc go curation for Kimberly

# Read sentences from flatfile.  By default look at last sentence (joinkey)
# entered in ggi_gene_gene_interaction, and read the next sentence.  Either :
# click on no genes and (No_interaction / Possible_genetic / Possible_non-genetic)
# or click on two genes and click on any other option.  Go back and reselect
# options to enter more than 3 connections / sentence. 
# New option to dump out last 10 sentences with connections.
# New option to search by sentence number.  2006 03 14
#
# Adapting for ccc go curation from gene_gene_inteaction.cgi  2007 03 15
#
# Created &addToGo($gene, $paps, $goterm); to add positive data to the GO
# curation got_ tables.  If an entry already exists, enter data, otherwise make
# a link to the go curation form to create the entry (for synonym data and so
# forth).  2007 04 27
#
# Added option of different source files, recreated the ccc_gene_comp_go table
# to allow a ccc_source_file column.  Made a symlink to the directory with the
# source files to make an html link to them in the form.  Will set up a script
# to redo this every week.  2007 07 18
#
# Set src_file_name on options as default value in case it's been changed.
# 2007 08 01
# 
# Fixed showing sentence, which wasn't working from an extra column in the file
# data.  
# Sorting by paper -> sentence -> score, instead of paper -> score -> sentence
# Added a checkbox for ``add to go form data'', and only do &addToGo($gene, $paps,
# $goterm); if the checkbox is checked on.  (for those sentences and not all the
# other ones).
# For Kimberly.  2008 03 07
#
# Added search of paper in source files for Kimberly.  2008 04 10
#
# Broke up sentences to have their own radio buttons for ``goterm''
# curate_radio, instead of separate buttons for those choices, since each
# sentence needed its own.  2008 04 14
#
# Changed to work with phenote tables.  2008 07 30
#
# Read data from /home2/postgres/work/pgpopulation/ccc_gocuration/sentences/
# since the files were taking up too much space. 
# Read in bad proteins and bad components, excluded from already being annotated.
# 2009 05 25
#
# Was adding $src_file_name instead of $ccc_src_file to ccc_gene_comp_go
# ccc_source_file column.
# Was adding marked up link to wormbase dev into ccc_gene_comp_go
# ccc_paper_sentence column.  2010 02 14


use strict;
use CGI;
use DBI;
use Jex;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my $query = new CGI;

my $src_file_name = 'good_senteces_file.20070316.1802';
my $src_directory = '/home2/postgres/work/pgpopulation/ccc_gocuration/sentences/';
my $src_file = $src_directory . $src_file_name;

my %comp_index;		# component to goterm index that have already been added to postgres
&popCompIndex();	# populate %comp_index;

&printHeader('gene component goterm');
&process();
&printFooter();

sub changeSourceFile {
  my ($var, $oop) = &getHtmlVar($query, 'source_file');
  if ($oop) { $src_file_name = $oop; $src_file = $src_directory . $src_file_name; }
} # sub changeSourceFile

sub findPapSourceFile { 
  my ($var, $paper) = &getHtmlVar($query, 'pap_sfile_search');
#   my (@src_files) = </home/postgres/work/pgpopulation/ccc_gocuration/recent_sentences_file.*>;
  my (@src_files) = </home2/postgres/work/pgpopulation/ccc_gocuration/sentences/recent_sentences_file.*>;
  my @good_files;
  foreach my $src_file (reverse @src_files) { 
    $/ = undef;
    open (IN, "<$src_file") or die "Cannot open $src_file : $!";
    my $all_file = <IN>;
    close (IN) or die "Cannot close $src_file : $!";
    if ($all_file =~ m/$paper/) { 
      $src_file =~ s/\/home2\/postgres\/work\/pgpopulation\/ccc_gocuration\/sentence\///g; 
      print "Match for $paper in sourcefile <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/ccc_gocuration/$src_file>$src_file</A><BR>\n"; } }
} # sub findPapSourceFile

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  if ($action) {
    if ($action eq "Submit !") { &newEntry(); }
    elsif ($action eq "Source File !") { &changeSourceFile(); }
#     elsif ($action eq "Already !") { &newEntry('already curated'); }
#     elsif ($action eq "Not GO !") { &newEntry('not go curatable'); }
#     elsif ($action eq "Scrambled Sentence !") { &newEntry('scrambled sentence'); }
#     elsif ($action eq "False Positive !") { &newEntry('false positive'); }
    elsif ($action eq "Dump 10 !") { &dump10(); } 
    elsif ($action eq "Search Pap Source !") { &findPapSourceFile(); } 
  }
  return if ($action eq "Search Pap Source !"); 

  &changeSourceFile();		# always check the sourcefile since it defaults to original list

  my $sentence = 0;

  my $result = $dbh->prepare( "SELECT joinkey FROM ccc_gene_comp_go WHERE ccc_source_file = '$src_file_name' ORDER BY joinkey DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  print "SELECT joinkey FROM ccc_gene_comp_go WHERE ccc_source_file = '$src_file_name' ORDER BY joinkey DESC;\n";
  my @row = $result->fetchrow;
  if ($row[0]) { $sentence = $row[0]; }
#   $sentence = 2617;

  if ($action) { if ($action eq "Search !") { (my $var, $sentence) = &getHtmlVar($query, "sent_search"); $sentence--; } }

  my $sentence_count;
  open (IN, "<$src_file") or die "Cannot open $src_file : $!";
  for ( 1 .. $sentence ) { <IN>; $sentence_count++; }
  my $sent_line = <IN>;
  my ($paper) = $sent_line =~ m/(WBPaper\d+)/;
  my @lines; my $abs = ''; my $title = '';
  push @lines, $sent_line;
  while (my $sent_line = <IN>) {
    if ($sent_line =~ m/\d+\tS \d+ P $paper S/) { push @lines, $sent_line; $sentence_count++; }
    elsif ($sent_line =~ m/ABSTRACT/) { if ($sent_line =~ m/ABSTRACT\t$paper\t(.*?)$/) { $abs = $1; } }
    elsif ($sent_line =~ m/TITLE/) { if ($sent_line =~ m/TITLE\t$paper\t(.*?)$/) { $title = $1; } }
    else { $sentence_count++; }
  } # while (my $sent_line = <IN>)
  close (IN) or die "Cannot close $src_file : $!";
  print "<FORM METHOD=POST ACTION=http://tazendra.caltech.edu/~postgres/cgi-bin/ccc_go_curation.cgi>\n";
  print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\">\n"; 
#   print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Already Curated : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Already !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Not GO curatable : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Not GO !\"><BR>\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;False Positive : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"False Positive !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Scrambled Sentence : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Scrambled Sentence !\"><BR>\n"; 
  print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dump last 10 sentences : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Dump 10 !\">\n"; 
  print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Search for sentence : <INPUT NAME=\"sent_search\"><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Search !\"><BR>\n"; 
  print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Search for paper in source files : <INPUT NAME=\"pap_sfile_search\"><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Search Pap Source !\"><BR>\n"; 
  my $text = "Title : $title<BR>Abstract : $abs<BR>\n";
  $text =~ s/<protein_celegans>(.*?)<\/protein_celegans>/<FONT COLOR='blue'>$1<\/FONT>/g;
  $text =~ s/<genes_arabidopsis>(.*?)<\/genes_arabidopsis>/<FONT COLOR='blue'>$1<\/FONT>/g;
  $text =~ s/<localization_cell_components_082208>(.*?)<\/localization_cell_components_082208>/<FONT COLOR='brown'>$1<\/FONT>/g;
  $text =~ s/<localization_verbs_082208>(.*?)<\/localization_verbs_082208>/<FONT COLOR='green'>$1<\/FONT>/g;
  $text =~ s/<localization_other_082208>(.*?)<\/localization_other_082208>/<FONT COLOR='orange'>$1<\/FONT>/g;
  print $text;
  print "<TABLE>\n";

  my $box = 0;
  foreach my $line (@lines) {
    $line = $src_file_name . "\t" . $line;
    $box++;
    &newReadSentence($line, $box); } 
  print "<INPUT TYPE=HIDDEN NAME=box_count VALUE=\"$box\">\n";
  print "</TABLE>\n";
  print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\"><BR>\n"; 
  print "Enter comments for this sentence here : <TEXTAREA NAME=comment ROWS=4 COLS=80></TEXTAREA><BR>\n";
  print "There are $sentence_count sentences in the sourcefile <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/ccc_gocuration/sentences/$src_file_name>$src_file</A><BR>\n";
#   my (@src_files) = </home/postgres/work/pgpopulation/ccc_gocuration/recent_sentences_file.*>;
  my (@src_files) = </home2/postgres/work/pgpopulation/ccc_gocuration/sentences/recent_sentences_file.*>;
#   my (@tair_src_files) = </home2/postgres/work/pgpopulation/ccc_gocuration/sentences/2008_*>;
  foreach (reverse @src_files) { $_ =~ s/\/home2\/postgres\/work\/pgpopulation\/ccc_gocuration\/sentences\///g; }
#   foreach (reverse @tair_src_files) { $_ =~ s/\/home2\/postgres\/work\/pgpopulation\/ccc_gocuration\/sentences\///g; }
  print "Select a source_file : <SELECT NAME=\"source_file\" SIZE=1>\n";
  if ($src_file_name) { print "<OPTION>$src_file_name</OPTION>\n"; }
  foreach (reverse @src_files) { print "      <OPTION>$_</OPTION>\n"; }
#   foreach (reverse @tair_src_files) { print "      <OPTION>$_</OPTION>\n"; }
  print "      <OPTION>good_senteces_file.20070316.1802</OPTION>\n";
  print "    </SELECT>\n ";
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Source File !\"><BR>\n"; 
  print "</FORM>\n";



#   open (IN, "<$src_file") or die "Cannot open $src_file : $!";
#   my $sentence_count;
#   for ( 1 .. $sentence ) { <IN>; $sentence_count++; }
#   print "<FORM METHOD=POST ACTION=http://tazendra.caltech.edu/~postgres/cgi-bin/ccc_go_curation.cgi>\n";
#   print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Already Curated : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Already !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Not GO curatable : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Not GO !\"><BR>\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;False Positive : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"False Positive !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Scrambled Sentence : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Scrambled Sentence !\"><BR>\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dump last 10 sentences : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Dump 10 !\">\n"; 
#   print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Search for sentence : <INPUT NAME=\"sent_search\"><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Search !\"><BR>\n"; 
#   print "<TABLE>\n";
#   my $line = <IN>;
#   for my $box (1 .. 3) {
#     &readSentence($sentence, $line, $box); } $sentence_count++; 
#   while (<IN>) { $sentence_count++; }
#   print "</TABLE>\n";
#   print "Make connections : <INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Submit !\"><BR>\n"; 
#   print "Enter comments for this sentence here : <TEXTAREA NAME=comment ROWS=4 COLS=80></TEXTAREA><BR>\n";
#   print "There are $sentence_count sentences in the sourcefile <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/ccc_gocuration/$src_file_name>$src_file</A><BR>\n";
#   my (@src_files) = </home/postgres/work/pgpopulation/ccc_gocuration/recent_sentences_file.*>;
#   foreach (reverse @src_files) { $_ =~ s/\/home\/postgres\/work\/pgpopulation\/ccc_gocuration\///g; }
#   print "Select a source_file : <SELECT NAME=\"source_file\" SIZE=1>\n";
#   if ($src_file_name) { print "<OPTION>$src_file_name</OPTION>\n"; }
#   foreach (@src_files) { print "      <OPTION>$_</OPTION>\n"; }
#   print "      <OPTION>good_senteces_file.20070316.1802</OPTION>\n";
#   print "    </SELECT>\n ";
#   print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Source File !\"><BR>\n"; 
#   print "</FORM>\n";
#   close (IN) or die "Cannot close $src_file : $!";
} # sub process

sub dump10 {
  my $sentence = 0;
  my $result = $dbh->prepare( "SELECT joinkey FROM ccc_gene_comp_go WHERE ccc_source_file = '$src_file_name' ORDER BY joinkey DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow; if ($row[0]) { $sentence = $row[0]; } $sentence -= 10;
  open (IN, "<$src_file") or die "Cannot open $src_file : $!";
  for ( 1 .. $sentence ) { <IN>; }
  for my $sent ( ($sentence + 1) .. ($sentence + 10) ) {
    my $sentence = <IN>; 
    print "SENT $sentence\n";
#     print "SELECT * FROM ccc_gene_comp_go WHERE joinkey = '$sent';<BR>\n";
  my $result = $dbh->prepare( "SELECT * FROM ccc_gene_comp_go WHERE ccc_source_file = '$src_file_name' AND joinkey = '$sent';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { print "$row[2]\t$row[3]\t$row[4]<BR>\n"; }
    print "<P>\n"; }
} # sub dump10

sub addToGoCGI {
  my ($gene, $paps, $goterm) = @_;
#   my ($pap) = $paps =~ m/P (WBPaper\d+) S/;
  my ($pap) = $paps =~ m/name=(WBPaper\d+);class=Paper/;
  my $time = &getPgDate();
  $gene = lc($gene);		# now using proteins, so need to lc to get locus 2007 08 07
  my $result = $dbh->prepare( "SELECT * FROM got_locus WHERE got_locus = '$gene'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow;
  if ($row[0]) {		# entry exists, append to it
      my $joinkey = $row[0];
      my %filter_hash;
      my $result = $dbh->prepare( "SELECT * FROM got_cell_goid WHERE joinkey = '$joinkey' ORDER BY got_timestamp;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) {
        if ($row[2]) { $filter_hash{$row[1]} = $row[2]; }
          else { delete $filter_hash{$row[1]}; } }
      my @vals = sort {$a<=>$b} keys %filter_hash;
      my $high_count = pop @vals;
      my $order = $high_count + 1;
      my $result = $dbh->prepare( "SELECT * FROM got_goterm WHERE got_goterm = '$goterm';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      @row = $result->fetchrow;
      unless ($row[0]) { print "<FONT COLOR=red>ERROR $goterm is not a valid GO term</FONT>."; die "$goterm is not a valid GO term : $!"; }
      my $goid = $row[0];
      my @pgcommands = ();
      my $pgcommand = "INSERT INTO got_cell_goterm VALUES ('$joinkey', '$order', '$goterm')";
      push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO got_cell_goid VALUES ('$joinkey', '$order', '$goid')";
      push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO got_cell_paper_evidence VALUES ('$joinkey', '$order', '$pap')";
      push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO got_cell_curator_evidence VALUES ('$joinkey', '$order', 'Kimberly Van Auken')";
      push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO got_cell_goinference VALUES ('$joinkey', '$order', 'IDA')";
      push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO got_cell_dbtype VALUES ('$joinkey', '$order', 'protein')";
      push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO got_cell_lastupdate VALUES ('$joinkey', '$order', '$time')";
      push @pgcommands, $pgcommand;
      foreach my $pgcommand (@pgcommands) {
        my $result = $dbh->prepare( $pgcommand );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
        print "<FONT COLOR=green>$pgcommand</FONT><BR>\n"; } }
    else { print "<FONT SIZE=+2 COLOR=red>$gene has not been curated for GO curation</FONT>, please <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/go_curation.cgi?action=Query+locus+%21&html_value_main_locus=$gene\" TARGET=new>curate for go</A>.<BR>\n"; }
} # sub addToGoCGI

sub addToGoPhenote {
  my ($locus, $paps, $goterm) = @_;
#   my ($pap) = $paps =~ m/P (WBPaper\d+) S/;
#   my ($pap) = $paps =~ m/name=(WBPaper\d+);class=Paper/;
  my ($pap) = $paps =~ m/(WBPaper\d+)/;
  my $time = &getPgDate();
  $locus = lc($locus);		# now using proteins, so need to lc to get locus 2007 08 07
  my $wbgene = '';
  my $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE gin_locus = '$locus';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow; if ($row[0]) { $wbgene = $row[0]; }
  unless ($wbgene) { 
    my $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE gin_synonyms = '$locus';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my @row = $result->fetchrow; if ($row[0]) { $wbgene = $row[0]; } }
  unless ($wbgene) { print "<FONT COLOR=red>ERROR $locus has no WBGene match.  No data entered into go phenote tables.</FONT><BR>\n"; return; }

  my $joinkey = 0;
  $result = $dbh->prepare( "SELECT * FROM gop_wbgene ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[0] > $joinkey) { $joinkey = $row[0]; } }
  $joinkey++;
#   my $result = $dbh->prepare( "SELECT * FROM got_goterm WHERE got_goterm = '$goterm';" );
  $result = $dbh->prepare( "SELECT * FROM obo_name_goid WHERE obo_name_goid = '$goterm';" );	# look at new obo tables for valid terms 2011 06 14
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  @row = $result->fetchrow;
  unless ($row[0]) { print "<FONT COLOR=red>ERROR $goterm is not a valid GO term</FONT>."; die "$goterm is not a valid GO term : $!"; }
  my $goid = $row[0];
  my @pgcommands = ();
  my $pgcommand = "INSERT INTO gop_goid VALUES ('$joinkey', '$goid')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_paper VALUES ('$joinkey', '$pap')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_wbgene VALUES ('$joinkey', 'WBGene$wbgene')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_goontology VALUES ('$joinkey', 'cell')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_curator VALUES ('$joinkey', 'WBPerson1843')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_goinference VALUES ('$joinkey', 'IDA')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_dbtype VALUES ('$joinkey', 'protein')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_lastupdate VALUES ('$joinkey', '$time')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_goid_hst VALUES ('$joinkey', '$goid')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_paper_hst VALUES ('$joinkey', '$pap')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_wbgene_hst VALUES ('$joinkey', 'WBGene$wbgene')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_goontology_hst VALUES ('$joinkey', 'cell')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_curator_hst VALUES ('$joinkey', 'WBPerson1843')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_goinference_hst VALUES ('$joinkey', 'IDA')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_dbtype_hst VALUES ('$joinkey', 'protein')";
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO gop_lastupdate_hst VALUES ('$joinkey', '$time')";
  push @pgcommands, $pgcommand;
  foreach my $pgcommand (@pgcommands) {
    print "<FONT COLOR=green>$pgcommand</FONT><BR>\n";
    $result = $dbh->prepare( $pgcommand );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; }
} # sub addToGoPhenote

sub newEntry {
#   my $goterm = shift;
  print "You've entered stuff : <BR>\n";
  my $badData = 0; my @pgcommands;
  my ($var, my $paps) = &getHtmlVar($query, "paps");
  ($var, my $box_count) = &getHtmlVar($query, "box_count");

  for my $box ( 1 .. $box_count ) {
    ($var, my $sentid) = &getHtmlVar($query, "sentid_$box");
# print "BOX $box S $sentid E<BR>\n";

    ($var, my $comment) = &getHtmlVar($query, "comment");
    if ($comment) { push @pgcommands, "INSERT INTO ccc_comment VALUES ('$sentid', '$comment', CURRENT_TIMESTAMP);"; }

    ($var, my $ccc_src_file) = &getHtmlVar($query, "ccc_src_file");
    ($var, my $goterm) = &getHtmlVar($query, "curate_radio_$box");
#     if ( ($goterm eq 'already curated') || ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) # require already curated to have protein and component  for Kimberly  2009 05 21
    if ( ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) {
      push @pgcommands, "INSERT INTO ccc_gene_comp_go VALUES ('$sentid', '$ccc_src_file', '$paps', NULL, NULL, '$goterm', CURRENT_TIMESTAMP);"; }
    else {
        ($var, my $gene) = &getHtmlVar($query, "gene_$box");
        ($var, my $component) = &getHtmlVar($query, "component_$box");
        unless ( ($goterm eq 'already goterm') || ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) {
          ($var, $goterm) = &getHtmlVar($query, "goterm_$box");
          ($var, my $new_goterm) = &getHtmlVar($query, "new_goterm_$box");
          if ($new_goterm) { $goterm = $new_goterm; &addTerm($component, $new_goterm); } }
    
        print "Gene $gene Component $component GO_term $goterm Paper-Sentence $paps SentenceID $sentid<BR>\n";
        if ($goterm) {
#           unless ( ($goterm eq 'already curated') || ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) # require already curated to have protein and component  for Kimberly  2009 05 21
          unless ( ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) {	# already curated to have protein and component  for Kimberly  2009 05 21
            unless ($gene) { print "<FONT COLOR=red>ERROR $goterm has no gene</FONT><BR>\n"; $badData++; } 
            unless ($component) { print "<FONT COLOR=red>ERROR $goterm has no component</FONT><BR>\n"; $badData++; } 
            unless ($badData) { 
              ($var, my $add_to_go) = &getHtmlVar($query, "add_to_go_$box");
#               if ($add_to_go eq 'checked') { &addToGoCGI($gene, $paps, $goterm); }
              if ($add_to_go eq 'checked') { &addToGoPhenote($gene, $paps, $goterm); }
              push @pgcommands, "INSERT INTO ccc_gene_comp_go VALUES ('$sentid', '$ccc_src_file', '$paps', '$gene', '$component', '$goterm', CURRENT_TIMESTAMP);"; } }
        }
      } } # for my $box ( 1 .. $box_count )
    
  if ($badData) { print "<FONT COLOR=red>Click BACK, fix the bad data, and resubmit</FONT><P><P>\n"; return; }
    else {
      foreach my $pgcommand (@pgcommands) {
        my $result = $dbh->prepare( "$pgcommand" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
        print "<FONT COLOR='green'>$pgcommand</FONT><BR>\n"; } }
  print "<P>\n";
} # sub newEntry

sub addTerm {
  my ($component, $goterm) = @_;
  unless ($comp_index{$component}{$goterm}) {
    print "<FONT COLOR='blue'>Adding</FONT> new <FONT COLOR='orange'>$goterm</FONT> - <FONT COLOR='brown'>$component</FONT> relationship to index<BR>\n";
    my $result = $dbh->do( "INSERT INTO ccc_component_go_index VALUES ('$component', '$goterm');" ); }
} # sub addTerm

sub popCompIndex {
  my $result = $dbh->prepare( "SELECT * FROM ccc_component_go_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $comp_index{$row[0]}{$row[1]}++; }
} # sub popCompIndex

sub newReadSentence {
  my ($line, $box) = @_;
  my ($junk, $src_file, $sentid, $paps, $genes, $components, $text, $badProt, $badComp) = split/\t/, $line;

#   my ($src_file, $line_count, $genes, $components, $text) = split/\t/, $line;
#   my ($paps) = $line_count =~ m/(WBPaper\d+)/;
# print "S $src_file LINE $sentid PAPS $paps GENES $genes COMPONENTS $components TEXT $text E<BR>\n";
  my (@genes) = split/, /, $genes;
  my (@components) = split/, /, $components;
  my %goTerms;
  foreach my $comp (@components) {
    if ($comp_index{$comp}) { foreach my $goterm (keys %{ $comp_index{$comp}}) { $goTerms{$goterm}++; } } }

  $text =~ s/<protein_celegans>(.*?)<\/protein_celegans>/<FONT COLOR='blue'>$1<\/FONT>/g;
  $text =~ s/<genes_arabidopsis>(.*?)<\/genes_arabidopsis>/<FONT COLOR='blue'>$1<\/FONT>/g;
  $text =~ s/<localization_cell_components_082208>(.*?)<\/localization_cell_components_082208>/<FONT COLOR='brown'>$1<\/FONT>/g;
  $text =~ s/<localization_verbs_082208>(.*?)<\/localization_verbs_082208>/<FONT COLOR='green'>$1<\/FONT>/g;
  $text =~ s/<localization_other_082208>(.*?)<\/localization_other_082208>/<FONT COLOR='orange'>$1<\/FONT>/g;
  $text =~ s/<localization_experimental_082208>(.*?)<\/localization_experimental_082208>/<FONT COLOR='orange'>$1<\/FONT>/g;

  print "<TR>\n";
  print "<TD><SELECT NAME=\"gene_$box\" SIZE=12>\n";
  print "      <OPTION> </OPTION>\n";
  foreach (@genes) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";

  print "<TD><SELECT NAME=\"component_$box\" SIZE=12>\n";
  print "      <OPTION > </OPTION>\n";
  foreach (@components) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";

  print "<TD><INPUT NAME=\"new_goterm_$box\" SIZE=30><BR><SELECT NAME=\"goterm_$box\" SIZE=10>\n";
  foreach (sort keys %goTerms) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";


  my $paps_link = $paps;
  if ($paps_link =~ m/WBPaper\d{8}/) { $paps_link =~ s/(WBPaper\d{8})/<A HREF=http:\/\/dev.wormbase.org\/db\/misc\/paper?name=$1;class=Paper TARGET=new>$1<\/A>/g; }			# link paper to dev.wormbase  2007 08 14
  print "<TD>curate<INPUT TYPE=radio NAME=\"curate_radio_$box\" VALUE=\"curate\">&nbsp;&nbsp;";
  print "already curated<INPUT TYPE=radio NAME=\"curate_radio_$box\" VALUE=\"already curated\">&nbsp;&nbsp;";
  print "scrambled sentence<INPUT TYPE=radio NAME=\"curate_radio_$box\" VALUE=\"scrambled sentence\">&nbsp;&nbsp;<BR>";
  print "false positive<INPUT TYPE=radio NAME=\"curate_radio_$box\" VALUE=\"false positive\">&nbsp;&nbsp;";
  print "not go curatable<INPUT TYPE=radio NAME=\"curate_radio_$box\" VALUE=\"not go curatable\">&nbsp;&nbsp;<BR>";
  print "Add To Go : <INPUT NAME=\"add_to_go_$box\" TYPE=CHECKBOX VALUE=\"checked\"><BR>\n";
  print "SentenceID $sentid -- $paps_link<BR>$text<br /><span style=\"color:red\">already done : $badProt $badComp</span></TD>\n";
  print "<INPUT TYPE=HIDDEN NAME=\"sentid_$box\" VALUE=\"$sentid\">\n";
  print "<INPUT TYPE=HIDDEN NAME=paps VALUE=\"$paps\">\n";
  print "<INPUT TYPE=HIDDEN NAME=ccc_src_file VALUE=\"$src_file\">\n";
  print "</TR>\n";
} # sub newReadSentence

sub readSentence {
  my ($sentence, $line, $count) = @_;
  $sentence++;
#   print "SENT $sentence SENT<BR>\n";
#   my ($src_file, $line_count, $paps, $genes, $components, $text) = split/\t/, $line;
  my ($src_file, $line_count, $genes, $components, $text) = split/\t/, $line;
  my ($paps) = $line_count =~ m/(WBPaper\d+)/;
print "S $src_file LINE $line_count PAPS $paps GENES $genes COMPONENTS $components TEXT $text E<BR>\n";
#   unless ($line_count == $sentence) { print "<FONT COLOR='red'>ERROR between sentence count in line read $sentence and sentence ID $line_count.</FONT><BR>\n"; }
  my (@genes) = split/, /, $genes;
  my (@components) = split/, /, $components;
  my %goTerms;
  foreach my $comp (@components) {
    if ($comp_index{$comp}) { foreach my $goterm (keys %{ $comp_index{$comp}}) { $goTerms{$goterm}++; } } }

  $text =~ s/<protein_celegans>(.*?)<\/protein_celegans>/<FONT COLOR='blue'>$1<\/FONT>/g;
  $text =~ s/<genes_arabidopsis>(.*?)<\/genes_arabidopsis>/<FONT COLOR='blue'>$1<\/FONT>/g;
  $text =~ s/<localization_cell_components_012607>(.*?)<\/localization_cell_components_012607>/<FONT COLOR='brown'>$1<\/FONT>/g;
  $text =~ s/<localization_verbs_012607>(.*?)<\/localization_verbs_012607>/<FONT COLOR='green'>$1<\/FONT>/g;
  $text =~ s/<localization_other_012607>(.*?)<\/localization_other_012607>/<FONT COLOR='orange'>$1<\/FONT>/g;
  $text =~ s/<localization_experimental_082208>(.*?)<\/localization_experimental_082208>/<FONT COLOR='orange'>$1<\/FONT>/g;

  print "<TR>\n";
  print "<TD><SELECT NAME=\"gene_$count\" SIZE=12>\n";
  print "      <OPTION> </OPTION>\n";
  foreach (@genes) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";

  print "<TD><SELECT NAME=\"component_$count\" SIZE=12>\n";
  print "      <OPTION > </OPTION>\n";
  foreach (@components) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";

  print "<TD><INPUT NAME=\"new_goterm_$count\" SIZE=30><BR><SELECT NAME=\"goterm_$count\" SIZE=10>\n";
  foreach (sort keys %goTerms) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n ";

  if ($paps =~ m/WBPaper\d{8}/) { $paps =~ s/(WBPaper\d{8})/<A HREF=http:\/\/dev.wormbase.org\/db\/misc\/paper?name=$1;class=Paper TARGET=new>$1<\/A>/g; }			# link paper to dev.wormbase  2007 08 14
  print "<TD>SentenceID $sentence -- $paps<BR><BR>$text</TD>\n";
  print "<INPUT TYPE=HIDDEN NAME=ccc VALUE=\"$sentence\">\n";
  print "<INPUT TYPE=HIDDEN NAME=paps VALUE=\"$paps\">\n";
  print "<INPUT TYPE=HIDDEN NAME=ccc_src_file VALUE=\"$src_file\">\n";
  print "</TR>\n";
} # sub readSentence


__END__

sub newEntry {	# old version
  my $goterm = shift;
  print "You've entered stuff : <BR>\n";
  my $badData = 0; my @pgcommands;
  my ($var, my $paps) = &getHtmlVar($query, "paps");
  ($var, my $ccc) = &getHtmlVar($query, "ccc");
  ($var, my $ccc_src_file) = &getHtmlVar($query, "ccc_src_file");
  if ( ($goterm eq 'already curated') || ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) {
      push @pgcommands, "INSERT INTO ccc_gene_comp_go VALUES ('$ccc', '$ccc_src_file', '$paps', NULL, NULL, '$goterm', CURRENT_TIMESTAMP);"; }
    else {
      for my $count ( 1 .. 3 ) {
        ($var, my $gene) = &getHtmlVar($query, "gene_$count");
        ($var, my $component) = &getHtmlVar($query, "component_$count");
        unless ( ($goterm eq 'already curated') || ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) {
          ($var, $goterm) = &getHtmlVar($query, "goterm_$count");
          ($var, my $new_goterm) = &getHtmlVar($query, "new_goterm_$count");
          if ($new_goterm) { $goterm = $new_goterm; &addTerm($component, $new_goterm); } }
    
#         print "Gene $gene Component $component GO_term $goterm Paper-Sentence $paps SentenceID $ccc<BR>\n";
        if ($goterm) {
          unless ( ($goterm eq 'already curated') || ($goterm eq 'not go curatable') || ($goterm eq 'scrambled sentence') || ($goterm eq 'false positive') ) {
            unless ($gene) { print "<FONT COLOR=red>ERROR $goterm has no gene</FONT><BR>\n"; $badData++; } 
            unless ($component) { print "<FONT COLOR=red>ERROR $goterm has no component</FONT><BR>\n"; $badData++; } 
            unless ($badData) { 
              &addToGo($gene, $paps, $goterm);
              push @pgcommands, "INSERT INTO ccc_gene_comp_go VALUES ('$ccc', '$src_file_name', '$paps', '$gene', '$component', '$goterm', CURRENT_TIMESTAMP);"; } }
        }
      } } # for my $count ( 1 .. 3 ) # else
  ($var, my $comment) = &getHtmlVar($query, "comment");
  if ($comment) { push @pgcommands, "INSERT INTO ccc_comment VALUES ('$ccc', '$comment', CURRENT_TIMESTAMP);"; }
    
  if ($badData) { print "<FONT COLOR=red>Click BACK, fix the bad data, and resubmit</FONT><P><P>\n"; return; }
    else {
      foreach my $pgcommand (@pgcommands) {
        my $result = $conn->exec( "$pgcommand" );
        print "<FONT COLOR='green'>$pgcommand</FONT><BR>\n"; } }
  print "<P>\n";
} # sub newEntry

