#!/usr/bin/perl

# Batch annotate GO data


# curate multiple genes to same 
#     paper - required
#     person 
#     curator - required
#     lastupdate
#     loci- required
#   but you could have multiples of    
#     genes
#     go term - required
#     go id - required
#     db obj type- required
# 
# and different 
#   go evi	- required
#   with
#   qualifier
#   comment
# 
# 1	you put in paper, person, curator, lastupdate, genes
# 2	pick ``big box'' for go term / go id
# 3	in small boxes show a column for each gene above
# 4	curate those columns
# 5	pick another ``big box'' for go term / go id
# 	repeat from 3
# at any time could add more genes at the top, then refresh to add that gene's columns
# display all big boxes and columns at the same time
# 
# 
# paper 1
# person 2
# curator ranjana
# genes - gene1 gene2 gene3 gene4
# 
# go term - something
# go id - 00001
# 
# gene1	gene2	gene3	gene4	gene5
# evi1	evi2	evi3	
# gp1	gp2	gp3	
# all1	all2	
# 
# 
# paper 1
# person 2
# curator ranjana
# 
# go term - something2
# go id - 00002
# 
# gene1	gene2	gene3	gene4
# evi5	evi6	evi7	
# gp5	gp6	gp7	
# all5	all6	
# 
# 
# go term - 3
# gene1	gene2	gene3	gene4
# evi9	evi10	evi11	evi12

# Updated to parse GO data to /home/postgres/public_html/cgi-bin/data/go.go as in 
# the parser at /home/postgres/work/get_stuff/go_curation/go/go_pg_to_go.pl
# Ace data to /home/postgres/public_html/cgi-bin/data/go.ace as in the parser at
# /home/postgres/work/get_stuff/go_curation/ace/go_pg_to_ace.pl  2002 09 09
#
# Updated to split the ace file around comma and space for papers to have own .ace 
# entries.  Updated to have a $ontology . '_goinference_two' . $i; entry as well as
# the usual one without _two.  Updated to have 4th set for everything.  2002 10 09
#
# Changed Similarity Evidence to Protein ID Evidence for HTML and .ace output
# 2002 10 15
#
# Changed &outputGo() to not get values if they are NULL   2002 10 17
#
# Added two more fields (provisional and pro_paper_description) in their own section
# at end of form, added tables to pg, created &outputPro() to output those fields to
# their own .ace file   2003 01 13
#
# Added entries to got_provisional and got_pro_paper_evidence with NULL values and 
# joinkey as that of got_locus to match potential UPDATE queries.   
# Changed outputPro to have last name first, then first initial.  Fixed bad output
# of pro_paper_evidence.  2003 01 15
#
# Changed &outputAce() to make Paper_evidence be CGC if exists   2003 02 12
#
# Added ' ' to @inferences to clear entries when updating   2003 02 13
# Changed the &outputAce() to get the inference type and output with the inference
# in each GO_term instead of in its own line  2003 02 13
#
# Changed &outputAce(); to get the cgc number from paper evidence if pmid number is
# greater than 10000 instead of it matches PMID:\d+  2002 02 24
#
# Changed &outputAce(); to get the WBPerson instead of the Author (Kishore or Schwarz)
# Filtered spaces out of goids.  2003 02 25
#
# Added a got_synonym table (for synonym to sequence) to pg.  Added a 
# &printHtmlInput('synonym'); for it.  Fixed &printHtmlInput(); since it wasn't
# being used before.  Changed Sequence to use &printHtmlInput(); instead of a
# text block.
# Changed &outputGo(); to include an extra $db (WB) at the end.
# Changed &outputAce(); to output in old format.  2003 02 27
#
# Commented out the textareablocks for person evidence and protein id.
# Filtered out spaces at end and beginning of paper evidence.  2003 03 24
#
# Changed &outputAce(); by commenting out the non-$inference lines and uncommenting
# the $inference lines (as well as the block of text marked to comment/uncomment).
# Changed &outputGo(); to allow for abstracts by checking if paper evidence data
# starts with [wm or [wbg or wm or wbg.  2003 04 08
#
# Added Kimberly to form.  2003 08 19
#
# If paper field has [ at the beginning, it implies that it's a cgc paper, so add
# to go.go output WB: in front.
# If there are two GO Inference types, go.go should repeat data in separate line,
# so have created $evidence2 variable, and if non-blank, then prints another line
# with $evidence2 instead of $evidence to go.go.  2003 08 22
#
# Added Query Sanger search (and replaced Query with Query Postgres) to look at 
# flatfiles based on locus to find sequence, synonym, and protein.  2003 08 26
#
# Had forgotten to create go_save_kimberly.txt, done now.
# Created go_ranjana.go go_ranjana.ace go_provisional_ranjana.ace (and same for
# kimberly, erich, juancarlos) and changes to those in &outputGo(); &outputAce();
# and &outputPro(); (as well as error message if no curator)  2003 09 10
#
# Added Carol to form.  2003 09 13
#
# Filter out extra brackets from outputAce(); paper entries.
# Pipe separate synonyms instead of , or , space.  2003 10 08
#
# Changed outputGo :
# PMIDs are entered in the format :
#   pmid:xxxxxxx
#   which then gets converted to PMID:xxxxxxx
# CGCs are entered in the format :
#   cgcxxxx
#   which then gets brackets around it and converted to pmid
# all others are having brackets placed around them
# 2003 12 09
#
# For preview page added link to WormBase for all paper_evidence fields (their data)
# 2003 12 16
#
# Changed Sequence to CDS for ACE output.  2004 01 20
#
# 8 columns instead of 4.  All write to postgres.
# New fields with and qualifier write to 8th and 4th column in go output.
# db_object_type selectable instead of default to gene. (default protein again)
# 11th column takes data from sequence box directly instead of trying to
# find a something.number (this may be wrong).  2004 02 06
#
# Added check of which protein is used to write with corresponding sequence
# for Ranjana  2004 02 24
# 
# Entries from $with and $with2 should be separated by |'s instead of spaces
# for Carols  2004 02 24
#
# Changed &write(); by creating &createOldAce($joinkey); which loads old values 
# from PG to %theHash if $found that the entry already exists, makes an $oldAce 
# from these hash values with &makeAce();, and reloads %theHash from the form 
# values.  pass $oldAce to &outputAce($oldAce); then rerun &makeAce to create
# $newAce, then if $oldAce exists, &findDiff($oldAce, $newAce) to see what's 
# different and create -D file (via &checkLines passing the entry being created, 
# the type (CDS vs Locus), the ace object name, and references to the hashes 
# which hold oldAce and newAce data)
# Basically, outputAce creates -D file if entry already exists, instead of
# writing the whole .ace again.  2004 03 18
#
# Separate with and with2 data with | and add WB: to the beginning of each
# of the separated entries.  For Carol.  2004 04 17
#
# Changed &outputGo(); so that if more than one paper is selected (comma separated)
# it will create multiple lines with those different papers.  For Kimberly, Carol,
# and Ranjana.  2004 04 20
#
# Moved initialization of my $cgc in &outputGo() to be inside the foreach loop
# created yesterday for separated paper entries in a single box, this way pmid's
# don't get the previous cgc appended to them.  2004 04 21
#
# Added WBGene field for Ranjana, .ace output now uses Gene instead of CDS or Sequence
# when it's available.  2004 07 15
#
# Updated &querySanger(); to look for ``approved'' instead of ``CGC approved'', allow
# an extra ``1'' in a new 3rd column, and filter out stuff in parenthesis from the 
# sequence column.  2004 08 09
#
# Added WBPaper convertion, added qualifier colocalizes_with to old form, since this
# form's been in progress for so long.  2004 09 02
#
# The default number of columns is 3.  You can add more columns to all
# three types by clicking the ``Add Column !'' button which adds another
# column.  (When querying, if there are more columns's worth of data
# than columns in the form, the form will expand to match the amount of
# data.  It will not shrink to match data, so it's better to Query from
# the original form's state rather than from a column number greater
# than 3)
# 
# Changed the Query buttons to be a single Query button, which queries
# Sanger, then if a field doesn't have data, it overwrites it with
# Postgres data (Which might be bad in the case that Sanger deletes
# something that was entered into Postgres.  Comments ?) and loads the
# rest of the form with Postgres data.
# 
# Created new tables in postgres, migrated the data, and rewrote the
# form to deal with the new tables.  They now keep a history of all
# changes.
# 
# DB_object_type moved from a single for whole entry, to one for each
# Qualifier.  Based on whether it's protein, gene, or transcript, it
# outputs to the second column of the GO file the protein id, wbgene id,
# and sequences (respectively).
# 
# Discussed loading big wb file into postgres so that it can be dumped
# with a button (like concise description) and will work on it with
# Ranjana.   2004 09 09
#
# Make .ace output have single entries for each .ace entry so -D lines and
# normal lines are each in their own .ace entry for Ranjana and Raymond.
#
# Fixed createOldAce, was storing into html_value instead of value, and
# was getting data from old tables instead of new ones, and wasn't 
# stopping after reading the last (1st) of the latest entry (was reading
# all entries, DESC, so was ending up with the oldest instead of newest)
# 2004 09 28
#
# ugh.  had forgotten to great pg tables for dbtype and dbtype_two under
# got_cell_ got_mol_ and got_bio_  done now.  2004 10 12
#
# Changed querySanger to no longer look at accession file for protein
# data since it's also in loci_all.txt  Changed so if it fails to find
# the loci_all.txt file it keeps going and warns that it failed instead
# of dying.  2004 10 27
#
# Added a ``Dump .go !'' button to call up script 
# /home/postgres/work/get_stuff/for_ranjana/go_curation_dumper/go_curation_go_dumper.pl
# which creates both :
# http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest
# http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.withcurator.latest
# for Ranjana.  2005 01 26
#
# Changed &query(); and &querySanger(); so that &querySanger($joinkey); requires
# knowing the $joinkey.  &query(); split into &queryLocus(); and &queryWBGene();
# which get the $joinkey (from form, or get wbgene from form, check vs
# got_wbgene, then get joinkey from postgres) then pass to &query($joinkey)
# which is the same as before.  2005 02 09
#
# Changed &saveState(); and &loadState(); to deal with each column of general
# data and store it in a separate row of the save file.  (So it can tell how
# many columns the form has).  2005 03 24
#
# Comment out Options button.  for Ranjana.  2005 05 12
#
# Look at local copy of loci_all.txt  2005 06 27
#
# Fixed &getHtmlValuesFromForm(); because it was converting multiple papers
# in paper_evidence properly, but it wasn't passing them on, it was only passing
# the last value in the array of papers.  2005 06 29
#
# Added Josh Jaffery to form for Kimberly.  2006 07 11
#
# Commented out the Dump .go button since it points to an old script and isn't
# used anymore.  for Ranjana  2006 08 01
#
# use go_curation_go.pm based on :
# /home/acedb/ranjana/citace_upload/go_curation/go_curation_go_dumper.pl
# for previewing .go output  for Ranjana  2006 08 03
#
# Moved .go preview to &write(); since it was previewing postgres data before
# updating postgres.  Changed it from tab-delimited text to a table with
# borders.  for Ranjana.  2006 08 07
#
# Updated to use gin_ postgres tables instead of loci_all since that's no longer
# updated.  2006 12 19
#
# Created and added new protein fields for every dbtype field to override the
# general Gene Product (protein) field in case they're different.  2007 01 25
#
# Added a horizontal view for Kimberly.  2007 01 25


# Converted from go_curation.cgi into a go_batch.cgi to batch enter (enter only)
# a set of loci connecting to the same set of GO IDs  2007 06 17
#
# Was failing to write to person_evidence curator_evidence and paper_evidence
# (the _evidence) was missing in the INSERTs  2007 11 07




use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate
use LWP::UserAgent;	# getting sanger files for querying
use LWP;
use lib qw( /home/acedb/ranjana/citace_upload/go_curation/ );
use go_curation_go;	# the .go output perl module
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";




my $query = new CGI;	# new CGI form

my %theHash;		# huge hash for each field with relevant values

my %convertToWBPaper;	# key cgc or pmid or whatever, value WBPaper
my %goTerm;		# the Go Terms in postgres, key id, value name

my @genParams = qw( curator loci paper person lastupdate );
# my @ontology = qw( bio cell mol );
my @ontology = qw( bio );
# my @column_types = qw( goterm goid paper_evidence person_evidence curator_evidence goinference dbtype protein with qualifier goinference_two dbtype_two protein_two with_two qualifier_two comment lastupdate );
my @groupParams = qw( goterm goid dbtype );
my @multParams = qw( goinference with qualifier comment );

my %reqParams; $reqParams{curator}++; $reqParams{loci}++; $reqParams{paper}++; $reqParams{goterm}++; $reqParams{goid}++; $reqParams{dbtype}++; $reqParams{goinference}++;	# required data

&printHeader('Go Batch ENTRY (only Entry) Form');
# print "<CENTER><FONT SIZE=+4 COLOR=red>UNDER CONSTRUCTION, do NOT use</FONT></CENTER><BR>\n";
print "<FONT COLOR=red SIZE=+2>If something changes in main GO curation, notify about possible problems here</FONT><BR>\n";
&initializeHash();	# Initialize theHash structure for html names and box sizes
&process();		# do everything
&printFooter();


sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  if ($action eq '') { &printHtmlForm(); }		# Display form, first time, no action
  else { 						# Form Button
    print "ACTION : $action : ACTION<BR>\n"; 
    if ($action eq 'Preview !') { &preview(); } 	# check loci and curator 
    elsif ($action eq 'New Entry !') { &write(); } 	# write to postgres (INSERT)
    elsif ($action eq 'Reset !') { &reset(); }		# reinitialize %theHash and display form
    elsif ($action eq 'Add Big Boxes !') { &addGroup(); }               
    elsif ($action eq 'More Boxes !') { &addMult(); }  
    elsif ($action eq 'Update Loci !') { &updateLoci(); }  
    print "ACTION : $action : ACTION<BR>\n"; 
  } # else # if ($action eq '') { &printHtmlForm(); }
} # sub process

#################  Action SECTION #################

sub reset {
  &initializeHash();		# Re-initialize %theHash structure for html names and box sizes 
  &printHtmlForm(); 		# Display form (now empty)
} # sub reset

sub updateLoci {
#   print "UPDATE LOCI <BR>\n";
  my $joinkey = &getHtmlValuesFromForm();               # populate %theHash and get joinkey
  &printHtmlForm();
} # sub addMult

sub addMult {
#   print "ADD MULT <BR>\n";
  my $joinkey = &getHtmlValuesFromForm();               # populate %theHash and get joinkey
  $theHash{horiz_mult}{html_value}++;
  &printHtmlForm();
} # sub addMult

sub addGroup {
#   print "ADD GROUP <BR>\n";
  my $joinkey = &getHtmlValuesFromForm();               # populate %theHash and get joinkey
  $theHash{group_mult}{html_value}++;
  &printHtmlForm();
} # sub addGroup

sub preview { 
#   print "PREVIEW<BR>\n";
  my $joinkey = &getHtmlValuesFromForm();               # populate %theHash and get joinkey
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/go_batch.cgi\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"group_mult\" VALUE=\"$theHash{group_mult}{html_value}\">\n";

  my $error_in_data; 
  foreach my $type (@genParams) {
    if ($theHash{$type}{html_value}) { 
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
      print "$type : $theHash{$type}{html_value}<BR>\n"; }
    if ($reqParams{$type}) { 
      unless ($theHash{$type}{html_value}) { print "<FONT COLOR=red>ERROR no $type chosen.</FONT><BR>\n"; $error_in_data++; } } }
  for my $i (1 .. $theHash{group_mult}{html_value}) {
    my $skip_box = 0;
    foreach my $type (@groupParams) {
      my $tstype = $type . '_' . $i . '_1';
      if ($theHash{$tstype}{html_value}) { 
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$tstype\" VALUE=\"$theHash{$tstype}{html_value}\">\n";
        print "$type $i : $theHash{$tstype}{html_value}<BR>\n"; }
      if ($reqParams{$type}) { unless ($theHash{$tstype}{html_value}) { print "<FONT COLOR=orange>WARNING no $type in <FONT COLOR=green>box $i</FONT> chosen.  box $i will be ignored.</FONT><BR>\n"; $skip_box++; } } }
    next if ($skip_box);
    foreach my $ontology (@ontology) {			# loop through each of three ontology types
      for my $j (1 .. $theHash{horiz_mult}{html_value}) {
        unless ($theHash{"wbgene_1_$j"}{html_value}) { print "<FONT COLOR=orange>WARNING no wbgene in <FONT COLOR=green>column $j</FONT> chosen.  column $j will be ignored.</FONT><BR>\n"; next; }
        foreach my $type (@multParams) {
          my $tstype = $ontology . '_' . $type . '_' . $i . '_' . $j;
          if ($theHash{$tstype}{html_value}) { 
            print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$tstype\" VALUE=\"$theHash{$tstype}{html_value}\">\n";
            print "$type $i $j : $theHash{$tstype}{html_value}<BR>\n"; }
          if ($reqParams{$type}) { unless ($theHash{$tstype}{html_value}) { print "<FONT COLOR=orange>WARNING no $type in <FONT COLOR=green>column $j of box $i</FONT> chosen.  column $j, box $i will be ignored.</FONT><BR>\n"; } } } } } }

  unless ($error_in_data) { print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"New Entry !\">\n"; }
  print "</FORM>";
} # sub preview 

sub write { 
  my $joinkey = &getHtmlValuesFromForm();               # populate %theHash and get joinkey
  my %addInfo;						# columns with WBGene that should add gene / locus / sequence / synonym / protein data
  foreach my $type (@genParams) {
    if ($theHash{$type}{html_value}) { 
      print "$type : $theHash{$type}{html_value}<BR>\n"; }
    if ($reqParams{$type}) { 
      unless ($theHash{$type}{html_value}) { print "<FONT COLOR=red>ERROR no $type chosen.</FONT><BR>\n"; } } }
  for my $i (1 .. $theHash{group_mult}{html_value}) {
    my $skip_box = 0;
    foreach my $type (@groupParams) {
      my $tstype = $type . '_' . $i . '_1';
      if ($reqParams{$type}) { unless ($theHash{$tstype}{html_value}) { $skip_box++; 
        print "<FONT COLOR=orange>WARNING no $type in <FONT COLOR=green>box $i</FONT> chosen.  box $i will be ignored.</FONT><BR>\n"; } } }
    next if ($skip_box);
    foreach my $ontology (@ontology) {			# loop through each of three ontology types
      for my $j (1 .. $theHash{horiz_mult}{html_value}) {
        my $skip_column = 0;
        unless ($theHash{"wbgene_1_$j"}{html_value}) { $skip_column++;
          print "<FONT COLOR=orange>WARNING no wbgene in <FONT COLOR=green>column $j</FONT> chosen.  column $j will be ignored.</FONT><BR>\n"; }
        foreach my $type (@multParams) {
          my $tstype = $ontology . '_' . $type . '_' . $i . '_' . $j;
          if ($reqParams{$type}) { unless ($theHash{$tstype}{html_value}) { $skip_column++; 
            print "<FONT COLOR=orange>WARNING no $type in <FONT COLOR=green>column $j of box $i</FONT> chosen.  column $j, box $i will be ignored.</FONT><BR>\n"; } } }
        next if ($skip_column);
        $addInfo{$j}++;
        my $joinkey = $theHash{"wbgene_1_$j"}{html_value};
        my ($got_order) = &findIfPgEntry($joinkey);
        $got_order++;
        foreach my $type (@genParams) {
          next if ($type eq 'loci');
          if ($theHash{$type}{html_value}) {
            my $table = 'got_' . $ontology . '_' . $type;
            if ( ($type eq 'paper') || ($type eq 'person') || ($type eq 'curator') ) {
              $table = 'got_' . $ontology . '_' . $type . '_evidence'; }
            my $pgcommand = "INSERT INTO $table VALUES ('$joinkey', '$got_order', '$theHash{$type}{html_value}');";
            my $result = $dbh->do( "$pgcommand" );
            print "$type $i 1 : $theHash{$type}{html_value}<BR><FONT COLOR='blue'>$pgcommand</FONT><BR>\n"; } }
        foreach my $type (@groupParams) {
          my $tstype = $type . '_' . $i . '_1';
          if ($theHash{$tstype}{html_value}) { 
            my $table = 'got_' . $ontology . '_' . $type;
            my $pgcommand = "INSERT INTO $table VALUES ('$joinkey', '$got_order', '$theHash{$tstype}{html_value}');";
            my $result = $dbh->do( "$pgcommand" );
            print "$type $i 1 : $theHash{$tstype}{html_value}<BR><FONT COLOR='blue'>$pgcommand</FONT><BR>\n"; } }
        foreach my $type (@multParams) {
          my $tstype = $ontology . '_' . $type . '_' . $i . '_' . $j;
          if ($theHash{$tstype}{html_value}) { 
            my $table = 'got_' . $ontology . '_' . $type;
            my $pgcommand = "INSERT INTO $table VALUES ('$joinkey', '$got_order', '$theHash{$tstype}{html_value}');";
            my $result = $dbh->do( "$pgcommand" );
            print "$type $i $j : $theHash{$tstype}{html_value}<BR><FONT COLOR='blue'>$pgcommand</FONT><BR>\n"; } }
  } } }
  foreach my $j (sort keys %addInfo) {
    print "COL $j COL<BR>\n";
    &updateIfDiff($theHash{"wbgene_1_$j"}{html_value}, 'wbgene', $theHash{"wbgene_1_$j"}{html_value});
    &updateIfDiff($theHash{"wbgene_1_$j"}{html_value}, 'locus', $theHash{"locus_1_$j"}{html_value});
    &updateIfDiff($theHash{"wbgene_1_$j"}{html_value}, 'sequence', $theHash{"sequence_1_$j"}{html_value});
    &updateIfDiff($theHash{"wbgene_1_$j"}{html_value}, 'protein', $theHash{"protein_1_$j"}{html_value});
    &updateIfDiff($theHash{"wbgene_1_$j"}{html_value}, 'synonym', $theHash{"synonym_1_$j"}{html_value});
  } # foreach my $j (sort keys %addInfo)
} # sub write

sub updateIfDiff {
  my ($joinkey, $table, $value) = @_;
  $table = 'got_' . $table;
  my $result = $dbh->prepare( "SELECT $table FROM $table WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; 
  if ($row[0] ne $value) { 
    my $pgcommand = "INSERT INTO $table VALUES ('$joinkey', '$value');";
    my $result2 = $dbh->do( $pgcommand );
    print "<FONT COLOR='blue'>$pgcommand</FONT><BR>\n";
  }
} # sub updateIfDiff

sub findIfPgEntry {	# check postgres for wbgene entry already in
  my $joinkey = shift;
  my $result = $dbh->prepare( " SELECT got_order FROM got_bio_goid WHERE joinkey = '$joinkey' ORDER BY got_order DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  unless ($row[0]) { $row[0] = 0; }
  return $row[0];
} # sub findIfPgEntry

sub getHtmlValuesFromForm {	
  &readConvertions();
  &getPgGoTerms();					# from postgres tables updated twice a month
  (my $var, $theHash{group_mult}{html_value} ) = &getHtmlVar($query, 'group_mult');
  foreach my $type (@genParams) {
    my ($var, $val) = &getHtmlVar($query, "html_value_main_$type");
    $theHash{$type}{html_value} = $val;
    if ($val) { if ($type eq 'paper') { $theHash{$type}{html_value} = &convertToWBPaper($val); } } }
  &getLocusData($theHash{loci}{html_value});
  foreach my $type (@groupParams) {
    for my $i (1 .. $theHash{group_mult}{html_value}) {
      my $tstype = $type . '_' . $i . '_1';
      my ($var, $val) = &getHtmlVar($query, "html_value_main_$tstype");
      $theHash{$tstype}{html_value} = $val; 
      if ($type =~ m/goid/) { if ($val) { &convertGoID($val, $i); } } } }
  foreach my $type (@multParams) {
    foreach my $ontology (@ontology) {			# loop through each of three ontology types
      for my $i (1 .. $theHash{group_mult}{html_value}) {
        for my $j (1 .. $theHash{horiz_mult}{html_value}) {
          my $tstype = $ontology . '_' . $type . '_' . $i . '_' . $j;
          my ($var, $val) = &getHtmlVar($query, "html_value_main_$tstype");
          $theHash{$tstype}{html_value} = $val; } } } }
} # sub getHtmlValuesFromForm

sub convertToWBPaper {
  my $paper = shift;
  if ($paper =~ m/PMID:/) { $paper =~ s/PMID:/pmid/g; }
  if ($paper !~ m/WBPaper/) { if ($convertToWBPaper{$paper}) { $paper = $convertToWBPaper{$paper}; } }
  return $paper;
} # sub convertToWBPaper

sub convertGoID {
  my ($goid, $box_count) = @_;
  ($goid) = $goid =~ m/(\d+)/;
  $goid =~ s/^0+//g;				# take off leading zeroes
  if ($goid < 10) { $goid = '000000' . $goid; }	# and add appropriate number of zeroes
  elsif ($goid < 100) { $goid = '00000' . $goid; }
  elsif ($goid < 1000) { $goid = '0000' . $goid; }
  elsif ($goid < 10000) { $goid = '000' . $goid; }
  elsif ($goid < 100000) { $goid = '00' . $goid; }
  elsif ($goid < 1000000) { $goid = '0' . $goid; }
  $goid = 'GO:' . $goid;			# and add the GO: tag
  my $tstype = 'goid_' . $box_count . '_1';
  $theHash{$tstype}{html_value} = $goid;
  if ($goTerm{$goid}) { 
    $tstype = 'goterm_' . $box_count . '_1';
    $theHash{$tstype}{html_value} = $goTerm{$goid};
    print "You've entered <FONT COLOR='green'>$goid</FONT> which corresponds to <FONT COLOR='green'>$goTerm{$goid}</FONT><BR>\n"; }
} # sub convertGoID

sub getLocusData {
  my $loci = shift;
  my (@loci) = split/,/, $theHash{loci}{html_value};
  my $count = 0;
  foreach my $locus (@loci) { 
    $count++;
    $locus =~ s/\s+//g;
    my $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE gin_locus = '$locus';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    my $joinkey = $row[0];
    $theHash{"locus_1_$count"}{html_value} = $locus; 
    unless ($joinkey) { print "<FONT COLOR='red'>Not a valid Gene match for $locus</FONT><BR>\n"; next; }
    $theHash{"wbgene_1_$count"}{html_value} = 'WBGene' . $joinkey; 
    my @prots; my @seqs; my @syns;
    $result = $dbh->prepare( "SELECT * FROM gin_sequence WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { push @seqs, $row[1]; }
    $theHash{"sequence_1_$count"}{html_value} = join ", ", @seqs;
    $result = $dbh->prepare( "SELECT * FROM gin_protein WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { push @prots, $row[1]; }
    $theHash{"protein_1_$count"}{html_value} = join ", ", @prots;
    $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { push @syns, $row[1]; }
    $theHash{"synonym_1_$count"}{html_value} = join ", ", @syns;
  }
  $theHash{horiz_mult}{html_value} = $count;
} # sub getLocusData


#################  Action SECTION #################

#################  HTML SECTION #################

sub printHtmlForm {	# Show the form 
# my @genParams = qw( curator loci paper person lastupdate );
# my @groupParams = qw( goterm goid dbtype );
# my @multParams = qw( goinference with qualifier comment );
  &printHtmlFormStart();
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"horiz_mult\" VALUE=\"$theHash{horiz_mult}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"group_mult\" VALUE=\"$theHash{group_mult}{html_value}\">\n";
  &printHtmlSelectCurators('curator');        
  &printHtmlInputQuery('loci', 'Update Loci !');        
  &printHtmlInput('paper');        
  &printHtmlInput('person');        
  &printHtmlInput('lastupdate');        
#   &printHtmlInputBlock('locus');
#   &printHtmlInputBlock('wbgene');
#   &printHtmlInputBlock('sequence');
#   &printHtmlInputBlock('synonym');
#   &printHtmlInputBlock('protein');
  &printHtmlTextBlock('locus');
  &printHtmlTextBlock('wbgene');
  &printHtmlTextBlock('sequence');
  &printHtmlTextBlock('synonym');
  &printHtmlTextBlock('protein');
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add Big Boxes !\"></TD></TR>\n";
  print "</TR></TABLE><TABLE border=2>";
  for my $i (1 .. $theHash{group_mult}{html_value}) {
    print "<TR><TD><TABLE>\n";
#     &printHtmlTextarea('goterm', $i);
    &printHtmlText('goterm', $i);
    &printHtmlTextarea('goid', $i);
    &printHtmlSelectType('dbtype', $i);
    print "</TR></TABLE><TABLE>\n";
#     print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"More Boxes !\"></TD></TR>\n"; 
    &printHtmlSection('Biological Process');
    &printHtmlTextBlock('locus');
    &printHtmlSelectBlock('bio_goinference', $i);
    &printHtmlTextareaBlock('bio_with', $i);
    &printHtmlSelectQualifierBlock('bio_qualifier', $i);
    &printHtmlTextareaBlock('bio_comment', $i);
#     print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"More Boxes !\"></TD></TR>\n"; 
    print "</TABLE></TR></TD>\n";
  } # for my $i (1 .. $group_mult)
  print "</TABLE>\n";
  &printHtmlFormEnd();
} # sub printHtmlForm

sub printHtmlInputQuery {       # print html inputs with queries (just pubID)
  my ($type, $message) = @_;             # get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  
         SIZE=$theHash{$type}{html_size_main}></TD>
    <TD ALIGN="left"><INPUT TYPE="submit" NAME="action" VALUE="$message"></TD>
  </TR> 
  EndOfText
} # sub printHtmlInputQuery

sub printHtmlInput {            # print html inputs
  my $type = shift;             # get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  
         SIZE=$theHash{$type}{html_size_main}></TD>
  </TR>
  EndOfText
} # sub printHtmlInput

sub printHtmlInputBlock {	# print html input blocks (sets of three)
  my $main_type = shift;	# get type, use hash for html parts
  print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>\n";
  for my $i (1 .. $theHash{horiz_mult}{html_value}) {
    my $ts_type = $main_type . '_1_' . $i;
    print"    <TD><INPUT NAME=\"html_value_main_$ts_type\" VALUE=\"$theHash{$ts_type}{html_value}\"  
                  SIZE=$theHash{$ts_type}{html_size_main}></TD>\n";
  } # for my $i (1 .. $theHash{horiz_mult}{html_value})
  print "</TR>\n";
} # sub printHtmlInputBlock 

sub printHtmlText {	# print html input blocks (sets of three)
  my ($main_type, $group_count) = @_;	# get type, use hash for html parts
  print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>\n";
  my $ts_type = $main_type . '_' . $group_count . '_1';
  print"    <TD>$theHash{$ts_type}{html_value}<INPUT TYPE=HIDDEN NAME=\"html_value_main_$ts_type\" VALUE=\"$theHash{$ts_type}{html_value}\"></TD>\n";
  print "</TR>\n";
} # sub printHtmlText 

sub printHtmlTextBlock {	# print html input blocks (sets of three)
  my $main_type = shift;	# get type, use hash for html parts
  print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>\n";
  for my $i (1 .. $theHash{horiz_mult}{html_value}) {
    my $ts_type = $main_type . '_1_' . $i;
    print"    <TD>$theHash{$ts_type}{html_value}<INPUT TYPE=HIDDEN NAME=\"html_value_main_$ts_type\" VALUE=\"$theHash{$ts_type}{html_value}\"></TD>\n";
  } # for my $i (1 .. $theHash{horiz_mult}{html_value})
  print "</TR>\n";
} # sub printHtmlTextBlock 

sub printHtmlSection {          # print html sections
  my $text = shift;             # get name of section
  print "\n  "; for (0..12) { print '<TR></TR>'; } print "\n\n";                # divider
  print "  <TR><TD><STRONG><FONT SIZE=+1>$text : </FONT></STRONG></TD></TR>\n"; # section
} # sub printHtmlSection

sub printHtmlTextarea {         # print html textareas
  my ($type, $group_count) = @_;             # get type, use hash for html parts
  my $tstype = $type . '_' . $group_count . '_1';
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD><TEXTAREA NAME="html_value_main_$tstype" ROWS=$theHash{$type}{html_size_minor}
                  COLS=$theHash{$type}{html_size_main}>$theHash{$tstype}{html_value}</TEXTAREA></TD>
  </TR>
  EndOfText
} # sub printHtmlTextarea

sub printHtmlTextareaBlock {	# print html textarea blocks (sets of three)
				# e.g. : &printHtmlTextareaBlock('bio_goterm');
  my ($type, $group_count) = @_;	# get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText

  for my $i (1 .. $theHash{horiz_mult}{html_value}) {
    my $tstype = $type . '_' . $group_count . '_' . $i;
    print"    <TD><TEXTAREA NAME=\"html_value_main_$tstype\" ROWS=$theHash{$type}{html_size_minor}
                  COLS=$theHash{$type}{html_size_main}>$theHash{$tstype}{html_value}</TEXTAREA></TD>\n";
  } # for my $i (1 .. $theHash{horiz_mult}{html_value})
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlTextareaBlock 

sub printHtmlSelectType {	# print html select blocks for curators
  my ($type, $group_count) = @_;
  my @types = ('', 'protein', 'gene', 'transcript', 'complex', 'protein_structure');
  my $tstype = $type . '_' . $group_count . '_1';
  my ($var, $action) = &getHtmlVar($query, 'action');
    # first time or query sanger, no action, protein
  if ( ($action eq '') || ($action eq 'Query Sanger !') ) { $theHash{$tstype}{html_value} = 'gene'; }	
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  print "    <TD><SELECT NAME=\"html_value_main_$tstype\" SIZE=1>\n";
  print "      <OPTION selected>$theHash{$tstype}{html_value}</OPTION>\n";
    # if loaded or queried, show option, otherwise default to '' option
  foreach (@types) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n  </TR>\n";
} # sub printHtmlSelectType

sub printHtmlSelectCurators {	# print html select blocks for curators	# no longer using this 2006 02 25
  my $type = shift;
  my @curators = ('', 'Carol Bastiani', 'Josh Jaffery', 'Ranjana Kishore', 'Erich Schwarz', 'Kimberly Van Auken', 'Juancarlos Testing');
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
  print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n";
    # if loaded or queried, show option, otherwise default to '' option
  foreach (@curators) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n  </TR>\n";
} # sub printHtmlSelectCurators

sub printHtmlSelectBlock {	# print html select blocks for inference type (set of three)
				# e.g. : &printHtmlSelectBlock('bio_goinference');
  my ($type, $group_count) = @_;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $theHash{horiz_mult}{html_value}) {
#     my $type = $main_type . $i;
    my $tstype = $type . '_' . $group_count . '_' . $i;
#     my @inferences = (' ', 'IDA -- Inferred from Direct Assay','IEA -- Inferred from Electronic Annotation','IEP -- Inferred from Expression Pattern','IGI -- Inferred from Genetic Interaction','IMP -- Inferred from Mutant Phenotype','IPI -- Inferred from Physical Interaction','ISS -- Inferred from Sequence or structural Similarity','NAS -- Non-traceable Author Statement','ND -- No Biological Data Available','IC -- Inferred by Curator','TAS -- Traceable Author Statement');
    my @choices = ();
    if ($type =~ m/inference/) { @choices = (' ', 'IDA','IEA','IEP','IGI','IMP','IPI','ISS','NAS','ND','IC','TAS', 'RCA'); }
    elsif ($type =~ m/dbtype/) { @choices = ('', 'protein', 'gene', 'transcript', 'complex', 'protein_structure'); }
    elsif ($type =~ m/curator_evidence/) { @choices = ('', 'Carol Bastiani', 'Josh Jaffery', 'Ranjana Kishore', 'Raymond Lee', 'Erich Schwarz', 'Kimberly Van Auken', 'Juancarlos Testing'); }
    else { @choices = ('not a valid choice type in printHtmlSelectBlock $type' ); }
#     my @inferences = (' ', 'IDA','IEA','IEP','IGI','IMP','IPI','ISS','NAS','ND','IC','TAS');
    print "    <TD><SELECT NAME=\"html_value_main_$tstype\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$tstype}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@choices) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
  } # for my $i (1 .. $theHash{horiz_mult}{html_value})
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlSelectBlock

sub printHtmlSelectQualifierBlock {	# print html select blocks for inference type (set of three)
					# e.g. : &printHtmlQualifierBlock('bio_goinference');
#   my $main_type = shift;
  my ($type, $group_count) = @_;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $theHash{horiz_mult}{html_value}) {
#     my $type = $main_type . $i;
    my $tstype = $type . '_' . $group_count . '_' . $i;
    my @qualifiers = (' ', 'NOT', 'contributes_to', 'colocalizes_with');	# added colocalizes_with for kimberly 2004 08 24
    print "    <TD><SELECT NAME=\"html_value_main_$tstype\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$tstype}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@qualifiers) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
  } # for my $i (1 .. $theHash{horiz_mult}{html_value})
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlQualifierBlock

sub printHtmlFormStart {        # beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/go_batch.cgi">
  <TABLE>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <!--<INPUT TYPE="submit" NAME="action" VALUE="Options !">--><BR>
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Add Column !"><BR>-->
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Dump .go !"><BR> shouldn't have been using this for a while  2006 08 01-->
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !"><BR> no longer using this 2006 02 27-->
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR>
  <TR>
    <TD> </TD>
<!--    <TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest>Latest .go Dump</A></TD></TR>-->
  EndOfText
} # sub printHtmlFormStart

sub printHtmlFormEnd {          # ending of form
  print <<"  EndOfText";
  <TR><TD COLSPAN=2> </TD></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <!--<INPUT TYPE="submit" NAME="action" VALUE="Options !">--><BR>
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Add Column !"><BR>-->
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Dump .go !"><BR> shouldn't have been using this for a while  2006 08 01-->
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !"><BR> no longer using this 2006 02 27-->
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR>
  <TR>
    <TD> </TD>
<!--    <TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest>Latest .go Dump</A></TD></TR>-->
  </TABLE>
  </FORM>
  EndOfText
} # sub printHtmlFormEnd

#################  HTML SECTION #################



#################  HASH SECTION #################

sub initializeHash {
  # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects.
  # in case of new fields, add to @PGparameters array and create html_field_name entry in %theHash
  # and other %theHash fields as necessary.  if new email address, add to %emails.

  $theHash{horiz_mult}{html_value} = 2; # default number of phenotype / suggested boxes
  $theHash{group_mult}{html_value} = 1; # default groups of curators, etc. giant tables

  foreach my $ontology (@ontology) {		# loop through each of three ontology types
    for my $i (1 .. $theHash{horiz_mult}{html_value}) {
      my $field = $ontology . '_' . $i;
      $theHash{$field}{html_field_name} = '';
      $theHash{$field}{html_value} = '';
      $theHash{$field}{html_size_main} = '20';            # default width 40
      $theHash{$field}{html_size_minor} = '2';            # default height 2
    }
    $theHash{"goterm"}{html_field_name} = 'GO Term';
    $theHash{"goid"}{html_field_name} = 'GO ID';
    $theHash{"dbtype"}{html_field_name} = 'DB_Object_Type';
    $theHash{"${ontology}_goterm"}{html_field_name} = 'GO Term';
    $theHash{"${ontology}_goid"}{html_field_name} = 'GO ID';
#     $theHash{"${ontology}_paper_evidence"}{html_field_name} = 'Paper Evidence<BR>(check it exists <BR>in <A HREF="http://www.wormbase.org/db/misc/paper?name=;class=Paper">WormBase</A>)';
#     $theHash{"${ontology}_person_evidence"}{html_field_name} = 'Person Evidence';
#     $theHash{"${ontology}_curator_evidence"}{html_field_name} = 'Curator Evidence';
    $theHash{"${ontology}_goinference"}{html_field_name} = 'GO Evidence';
    $theHash{"${ontology}_dbtype"}{html_field_name} = 'DB_Object_Type';
    $theHash{"${ontology}_protein"}{html_field_name} = 'Gene Product (Protein)';
    $theHash{"${ontology}_with"}{html_field_name} = 'with';
    $theHash{"${ontology}_qualifier"}{html_field_name} = 'Qualifier';
#     $theHash{"${ontology}_goinference_two"}{html_field_name} = 'GO Evidence 2';
#     $theHash{"${ontology}_dbtype_two"}{html_field_name} = 'DB_Object_Type 2';
#     $theHash{"${ontology}_protein_two"}{html_field_name} = 'Gene Product (Protein) 2';
#     $theHash{"${ontology}_with_two"}{html_field_name} = 'with 2';
#     $theHash{"${ontology}_qualifier_two"}{html_field_name} = 'Qualifier 2';
#     $theHash{"${ontology}_similarity"}{html_field_name} = 'Protein ID Evidence';
    $theHash{"${ontology}_comment"}{html_field_name} = 'Comment';
#     $theHash{"${ontology}_lastupdate"}{html_field_name} = 'Timestamp Column<BR>Last Updated e.g.<BR>``2006-11-01 16:05:42\'\'';
  } # foreach my $ontology (@ontology)


  foreach my $field (@genParams) {
    $theHash{$field}{html_field_name} = '';
    $theHash{$field}{html_value} = '';
    $theHash{$field}{html_size_main} = '20';            # default width 40
    $theHash{$field}{html_size_minor} = '2';            # default height 2
  } # foreach my $field (@genParams)

  $theHash{curator}{html_field_name} = 'Curator';
  $theHash{loci}{html_field_name} = 'Loci';
  $theHash{locus}{html_field_name} = 'Locus';
  $theHash{paper}{html_field_name} = 'Paper';
  $theHash{person}{html_field_name} = 'Person';
  $theHash{lastupdate}{html_field_name} = 'Timestamp Column<BR>Last Updated e.g.<BR>``2006-11-01 16:05:42\'\'';
  $theHash{sequence}{html_field_name} = 'Sequence';
  $theHash{synonym}{html_field_name} = 'Synonym';
  $theHash{wbgene}{html_field_name} = 'WBGene';
  $theHash{protein}{html_field_name} = 'Gene Product (Protein)';

} # sub initializeHash

#################  HASH SECTION #################


sub readConvertions {
  my $u = "http://tazendra.caltech.edu/~acedb/paper2wbpaper.txt";
  my $ua = LWP::UserAgent->new(timeout => 30); #instantiates a new user agent
  my $request = HTTP::Request->new(GET => $u); #grabs url
  my $response = $ua->request($request);       #checks url, dies if not valid.
  die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
  my @tmp = split /\n/, $response->content;    #splits by line
  foreach (@tmp) {
    if ($_ =~m/^(.*?)\t(.*?)$/) {
      $convertToWBPaper{$1} = $2; } }
} # sub readConvertions

sub getPgGoTerms {
  my $result = $dbh->prepare( "SELECT * FROM got_goterm;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $goTerm{$row[0]} = $row[1]; }
} # sub getPgGoTerms


__END__ 

# curate multiple genes to same 
#     paper 
#     person 
#     curator 
#     lastupdate
#     locus
#   but you could have multiples of    
#     genes
#     go term 
#     go id 
#     db obj type
# 
# and different 
#   go evi	- required
#   gene product
#   with
#   qualifier
#   comment

sub printHtmlForm {	# Show the form 
# my @genParams = qw( curator locus paper person lastupdate );
# my @groupParams = qw( goterm goid dbtype );
# my @multParams = qw( goinference protein with qualifier comment );
  &printHtmlFormStart();
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"horiz_mult\" VALUE=\"$theHash{horiz_mult}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"group_mult\" VALUE=\"$theHash{group_mult}{html_value}\">\n";
#   print "<INPUT TYPE=\"HIDDEN\" NAME=\"hide_or_not\" VALUE=\"$theHash{hide_or_not}{html_value}\">\n";
  &printHtmlSection('BATCH GO_annotation');
# #   &printHtmlSelectCurators('curator');		# print html select blocks for curators # moved curators to columns 2006 02 25
#   &printHtmlInputQuery('wbgene');        	# input with Query button
#   &printHtmlInputQuery('locus');        	# input with Query button
#   &printHtmlInput('sequence');        	
#   &printHtmlInput('synonym');        
  &printHtmlSelectCurators('curator');        
  &printHtmlInput('locus');        
  &printHtmlInput('paper');        
  &printHtmlInput('person');        
  &printHtmlInput('lastupdate');        
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add Big Boxes !\"></TD></TR>\n";
  print "</TR></TABLE><TABLE border=2>";
  for my $i (1 .. $theHash{group_mult}{html_value}) {
    print "<TR><TD><TABLE>\n";

# my @groupParams = qw( goterm goid dbtype );
#     &printHtmlInput('wbgene');        
#     &printHtmlTextarea('sequence');
    &printHtmlTextarea('bio_goterm');
    &printHtmlTextarea('bio_goid');
    &printHtmlSelectType('bio_dbtype');
#     &printHtmlSelectType('dbtype');        	# not main in new form 2004 08 11
    print "</TR></TABLE><TABLE>\n";
    print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"More Boxes !\"></TD></TR>\n"; 
    &printHtmlSection('Biological Process');
#     &printHtmlTextareaBlock('bio_goterm');
#     &printHtmlTextareaBlock('bio_goid');
#     &printHtmlSelectBlock('bio_dbtype');

#     &printHtmlTextareaBlock('bio_paper_evidence');
#     &printHtmlTextareaBlock('bio_person_evidence');
#     &printHtmlSelectBlock('bio_curator_evidence');
    &printHtmlSelectBlock('bio_goinference');
    &printHtmlTextareaBlock('bio_protein');
    &printHtmlTextareaBlock('bio_with');
    &printHtmlSelectQualifierBlock('bio_qualifier');
    &printHtmlTextareaBlock('bio_comment');
#     &printHtmlTextareaBlock('bio_lastupdate');
#     &printHtmlSection('Cellular Component');
#     &printHtmlTextareaBlock('cell_goterm');
#     &printHtmlTextareaBlock('cell_goid');
#     &printHtmlSelectBlock('cell_dbtype');
#     &printHtmlTextareaBlock('cell_paper_evidence');
#     &printHtmlTextareaBlock('cell_person_evidence');
#     &printHtmlSelectBlock('cell_curator_evidence');
#     &printHtmlSelectBlock('cell_goinference');
#     &printHtmlTextareaBlock('cell_protein');
#     &printHtmlTextareaBlock('cell_with');
#     &printHtmlSelectQualifierBlock('cell_qualifier');
#     &printHtmlSelectBlock('cell_goinference_two');
#     &printHtmlSelectBlock('cell_dbtype_two');
#     &printHtmlTextareaBlock('cell_protein_two');
#     &printHtmlTextareaBlock('cell_with_two');
#     &printHtmlSelectQualifierBlock('cell_qualifier_two');
#     &printHtmlTextareaBlock('cell_comment');
#     &printHtmlTextareaBlock('cell_lastupdate');
#     &printHtmlSection('Molecular Function');
#     &printHtmlTextareaBlock('mol_goterm');
#     &printHtmlTextareaBlock('mol_goid');
#     &printHtmlSelectBlock('mol_dbtype');
#     &printHtmlTextareaBlock('mol_paper_evidence');
#     &printHtmlTextareaBlock('mol_person_evidence');
#     &printHtmlSelectBlock('mol_curator_evidence');
#     &printHtmlSelectBlock('mol_goinference');
#     &printHtmlTextareaBlock('mol_protein');
#     &printHtmlTextareaBlock('mol_with');
#     &printHtmlSelectQualifierBlock('mol_qualifier');
#     &printHtmlSelectBlock('mol_goinference_two');
#     &printHtmlSelectBlock('mol_dbtype_two');
#     &printHtmlTextareaBlock('mol_protein_two');
#     &printHtmlTextareaBlock('mol_with_two');
#     &printHtmlSelectQualifierBlock('mol_qualifier_two');
#     &printHtmlTextareaBlock('mol_comment');
#     &printHtmlTextareaBlock('mol_lastupdate');
    

    print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"More Boxes !\"></TD></TR>\n"; 
    print "</TABLE></TR></TD>\n";
  } # for my $i (1 .. $group_mult)
  print "</TABLE>\n";
  &printHtmlFormEnd();
} # sub printHtmlForm



my %goTerm;		# the Go Terms in postgres, key id, value name

my %cgcHash;		# hash of cgcs, values pmids
my %pmHash;		# hash of pmids, values cgcs

my %convertToWBPaper;	# key cgc or pmid or whatever, value WBPaper

my $error_in_data = 0;	# flag if any data is wrong


my $curator = '';
my $data_file = '/home/postgres/public_html/cgi-bin/data/go.txt';
my $ace_file = '/home/postgres/public_html/cgi-bin/data/go.ace';			# not used anymore
my $go_file = '/home/postgres/public_html/cgi-bin/data/go.go';				# not used anymore
my $pro_file = '/home/postgres/public_html/cgi-bin/data/provisional_description.ace';	# not used anymore
# my $save_file = "/home/postgres/public_html/cgi-bin/data/go_save_$curator.txt";
			# doesn't double re-interpolate the $curator name once $curator loaded
			# so using this line below

# my $max_columns;	# create number of columns to show by default, define in &initializeHash();
my @ontology = qw( bio cell mol );
my @column_types = qw( goterm goid paper_evidence person_evidence curator_evidence goinference dbtype protein with qualifier goinference_two dbtype_two protein_two with_two qualifier_two comment lastupdate );

&printHeader('Go Curation Form');
# print "<CENTER><FONT SIZE=+4 COLOR=red>UNDER CONSTRUCTION, do NOT use</FONT></CENTER><BR>\n";
# print "<FONT COLOR=red SIZE=+4>Under Construction don't use new fields yet</FONT><BR>\n";
&initializeHash();	# Initialize theHash structure for html names and box sizes
&process();		# do everything
&printFooter();

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  if ($action eq '') { &printHtmlForm(); }		# Display form, first time, no action
  else { 						# Form Button
    print "ACTION : $action : ACTION<BR>\n"; 
    if ($action eq 'Preview !') { &preview(); } 	# check locus and curator 
    if ($action eq 'New Entry !') { &write(); } 	# write to postgres (INSERT)
    if ($action eq 'Update !') { &write(); }		# write to postgres (UPDATE)
    if ($action eq 'Query locus !') { &queryLocus(); }		# query postgres.  also queries sanger and overwrites with postgres values.  2004 09 09
    if ($action eq 'Query wbgene !') { &queryWBGene(); }	# query postgres.  also queries sanger and overwrites with postgres values.  2004 09 09
#     if ($action eq 'Query Sanger !') { &querySanger(); }# query sanger.  no longer an option since Query queries sanger and postgres 2004 09 09
    if ($action eq 'Reset !') { &reset(); }		# reinitialize %theHash and display form
#     if ($action eq 'Save !') { &saveState(); }		# save to file	# no longer using this 2006 02 27
#     if ($action eq 'Load !') { &loadState(); }		# load from file	# no longer using this 2006 02 27
    if ($action eq 'Options !') { &options(); }		# options menu (empty)
    if ($action eq 'Add Column !') { &addColumn(); }	# addColumn to max_columns
    if ($action eq 'Dump .go !') { &dump(); }	# dump postgres to file
    print "ACTION : $action : ACTION<BR>\n"; 
  } # else # if ($action eq '') { &printHtmlForm(); }
} # sub process

#################  Action SECTION #################

sub addColumn {						# see how many columns there are, and make there be 1 more 
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  $max_columns++;
  &printHtmlForm();					# show the form again, with the same data
}

sub options {
  print "<P><B>What would you like ?  Tell Juancarlos.</B><BR><P>\n";
} # sub options


sub reset {
  &initializeHash();		# Re-initialize %theHash structure for html names and box sizes 
  &printHtmlForm(); 		# Display form (now empty)
} # sub reset

sub querySanger {
  my ($locus_or_gene, $val) = @_;
  my $locus_flag = 0; my $wbgene_flag = 0;
  my $joinkey = $val;

  my $joinkey_in_form = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey from form, which is useless since won't joinkey if querying by wbgene

# OBSOLETE, no longer updating loci_all  2006 12 19
#   my $ua = LWP::UserAgent->new(timeout => 30);	# instantiates a new user agent
#   my $url_locus = 'http://tazendra.caltech.edu/~azurebrd/sanger/loci_all.txt';
#   my $request = HTTP::Request->new(GET => $url_locus);	# grabs url
#   my $response = $ua->request($request);	# checks url, dies if not valid.
#   print "Error while getting ", $response->request->uri," -- ", $response->status_line, "<BR>\nABORTING QUERY SANGER<BR>\n" unless $response-> is_success;
#   my @lines = split /\n/, $response->content;	# splits by line
#   foreach (@lines) {
#     next unless ($_ =~ m/approved$/);		# ignore those not CGC approved  2004 08 09, doesn't say CGC anymore
#     my @fields = split/,/, $_;			# split by commas
#     my $locus = shift @fields;			# get the locus
#     if ($locus_flag) {
#       unless ($locus eq $joinkey) { next; } }	# only get the value if the locus matches the line of Sanger's loci_all.txt
#     my $wbgene = shift @fields;			# get the wbgene (get it out of the way)
#     if ($wbgene_flag) {
#       unless ($wbgene eq $joinkey) { next; } }	# only get the value if the wbgene matches the line of Sanger's loci_all.txt
#     my $junkone = shift @fields;		# 2004 08 09, has an extra 1 in there
#     my $allsequence = shift @fields;		# get the sequences, space separated
#     my @proteins = $allsequence =~ m/\(.*?\)/g; # grab proteins
#     foreach (@proteins) { s/\(WP://g; s/\)//g; }        # filter out non-protein stuff
#     $theHash{protein}{html_value} = join ", ", @proteins;
#     $allsequence =~ s/\(.*?\)//g;		# filter out stuff in parenthesis
#     my @sequences = split/\s+/, $allsequence;	# get sequences into array
#     $theHash{sequence}{html_value} = join ", ", @sequences;
#     shift @fields; shift @fields; 		# get rid of 2 informationless fields
#     pop @fields;				# fields now has synonyms, having gotten rid of all else
#     my $synonyms = join ", ", @fields;
#     $synonyms =~ s/\s+$//g; $synonyms =~ s/^\s+//g; $synonyms =~ s/\s+/, /g;
#     $theHash{synonym}{html_value} = "$synonyms";# put value in %theHash
#     $theHash{wbgene}{html_value} = $wbgene;
#     $theHash{locus}{html_value} = $locus;	# must assign locus now  2005 10 14
#   } # foreach (@lines)

  if ($locus_or_gene eq 'locus') { 
      my $result = $conn->exec( "SELECT * FROM gin_locus WHERE gin_locus = '$val';" );
      my @row = $result->fetchrow;
      $joinkey = $row[0];
    }
    else { 
      $joinkey =~ s/WBGene//g; }
  my $result = $conn->exec( "SELECT * FROM gin_locus WHERE joinkey = '$joinkey';" );
  my @row = $result->fetchrow;
  if ($row[0]) { $theHash{wbgene}{html_value} = 'WBGene' . $row[0]; }
    else { $theHash{wbgene}{html_value} = $val; }		# if there's no match return the original value  2007 02 13
  if ($joinkey eq '00000000') { $theHash{wbgene}{html_value} = 'WBGene00000000'; }	# test value
  $theHash{locus}{html_value} = $row[1];
  my @prots; my @seqs; my @syns;
  $result = $conn->exec( "SELECT * FROM gin_sequence WHERE joinkey = '$joinkey';" );
  while (my @row = $result->fetchrow) { push @seqs, $row[1]; }
  $theHash{sequence}{html_value} = join ", ", @seqs;
  $result = $conn->exec( "SELECT * FROM gin_protein WHERE joinkey = '$joinkey';" );
  while (my @row = $result->fetchrow) { push @prots, $row[1]; }
  $theHash{protein}{html_value} = join ", ", @prots;
  $result = $conn->exec( "SELECT * FROM gin_synonyms WHERE joinkey = '$joinkey';" );
  while (my @row = $result->fetchrow) { push @syns, $row[1]; }
  $theHash{synonym}{html_value} = join ", ", @syns;

  (my $var, $val) = &getHtmlVar($query, 'html_value_main_curator');
  if ($val) { $theHash{curator}{html_value} = $val; }
  print "J $theHash{wbgene}{html_value} J<BR>\n";;
  return $theHash{wbgene}{html_value};
} # sub querySanger


sub queryWBGene {	# query by wbgene
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  &query('wbgene', $joinkey);
}

sub queryLocus {	# query by locus
  my $html_type = 'html_value_main_locus';
  my ($var, $val) = &getHtmlVar($query, $html_type);
  my $result = $conn->exec( "SELECT * FROM got_locus WHERE got_locus = '$val' ORDER BY got_timestamp DESC;" );
  my @row = $result->fetchrow;
  if ($row[0]) {
    my $joinkey = $row[0];
    $theHash{wbgene}{html_value} = $joinkey;
    &query('wbgene', $joinkey); }
  else { &query('locus', $val); }
} # sub queryLocus

sub query {		# check postgres for locus, then get values from postgres 
			# and put in %theHash{$type}{html_value} for display
			# check sanger first, then override with postgres values unless postgres has no value  2004 09 09
  my ($locus_or_gene, $val) = @_;
  my ($joinkey) = &querySanger($locus_or_gene, $val);	# query sanger after getting joinkey, or i think &getHtmlValuesFromForm could overwrite values  2004 09 28
  my $found = &findIfPgEntry("$joinkey");		# if wbgene, check if already in Pg
  unless ($found) { 					# if not found
    if ($joinkey eq 'NULL') {				# if wbgene is NULL (wbgene not entered)
      print "<FONT COLOR='blue'><B>ERROR : No wbgene chosen, go back and select one</B></FONT><BR>\n"; 
    } else {						# if wbgene not in postgres
      print "<FONT COLOR='blue'><B>No previous entry for $joinkey in Postgres</B></FONT><BR>\n";
      &printHtmlForm();
    } # if ($joinkey eq 'NULL')
  } else {						# if wbgene found
    foreach my $type (@PGparameters) {
      unless ($theHash{$type}{html_value}) {		# if there's no sanger value, get value from postgres  2004 09 09
        my $result = $conn->exec( "SELECT * FROM got_$type WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;" );
#       while (my @row = $result->fetchrow) { 
        my @row = $result->fetchrow;
        my $val = &filterToPrintHtml("$row[1]");	# turn value to Html
        if ($val) { if ($val =~ m/\S/) { $theHash{$type}{html_value} = $val; } }	# put value in %theHash if there's a value in postgres, overwriting sanger value
#       } # while (my @row = $result->fetchrow) 
      } # unless ($theHash{$type}{html_value})
    } # foreach my $type (@PGparameters)
    foreach my $ontology (@ontology) {		# loop through each of three ontology types
      foreach my $column_type (@column_types) {
        my $type = $ontology . '_' . $column_type;
        my $result = $conn->exec( "SELECT * FROM got_$type WHERE joinkey = '$joinkey' ORDER BY got_timestamp ;" );
#         print "SELECT * FROM got_$type WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;<BR>\n";
        while (my @row = $result->fetchrow) {
          my $val = &filterToPrintHtml("$row[2]");	# turn value to Html
          my $temp_type = $type . $row[1];
          $theHash{$temp_type}{html_value} = $val;	# put value in %theHash
          if ($row[1] > $max_columns) { $max_columns = $row[1]; }	# reassign column number if querying lots of data
#           if ($row[1] == 1) { last; }
        }
    } }
    &printHtmlForm();
  } # else # unless ($found) 
} # sub query

sub createOldAce {
  my $joinkey = shift;
  foreach my $type (@PGparameters) {
    my $result = $conn->exec( "SELECT * FROM got_$type WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;" );
    my @row = $result->fetchrow;
    my $val = &filterToPrintHtml("$row[1]");		# turn value to Html
    my $temp_type = $type;
    $theHash{$temp_type}{value} = $val; }		# put value in %theHash 
  my @allparameters = ();
  foreach my $ontology (@ontology) {			# loop through each of three ontology types
    foreach my $column_type (@column_types) {
        my $field = $ontology . '_' . $column_type;
        push @allparameters, $field } }
  foreach my $type (@allparameters) {			# temporarily populate the hash with old values
    my $result = $conn->exec( "SELECT * FROM got_$type WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;" );
    while (my @row = $result->fetchrow) { 
      my $val = &filterToPrintHtml("$row[2]");		# turn value to Html
      my $temp_type = $type . $row[1];
      $theHash{$temp_type}{value} = $val;		# put value in %theHash
      if ($row[1] == 1) { last; }			# stop if get to first column, don't want to get all data, just latest
    } # while (my @row = $result->fetchrow) 
  } # foreach my $type (@PGparameters)
  my $oldAce = &makeAce();				# create ace entry with old values
  $joinkey = &getHtmlValuesFromForm('noprint'); 	# repopulate %theHash with good values, don't print to CGI again
  return $oldAce;
} # sub createOldAce

sub write {		# write to postgres (INSERT or UPDATE as required) and flatfile
  &readConvertions();
  &populateXref();
  open (OUT, ">>$data_file") or die "Cannot append to $data_file : $!";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  my $found = &findIfPgEntry("$joinkey");		# if wbgene, check if already in Pg
  my $oldAce = '';
  if ($found) { $oldAce = &createOldAce($joinkey); }
  foreach my $type (sort keys %theHash) {
    my ($table, $order) = $type =~ m/^(.*?)(\d+)/;
    unless ($table) { 					# if not a multi-order type table
      unless ($theHash{$type}{value}) { next; } 	# skip if no data
      $table = $type; }					# assign table if some kind of value there
    $table = 'got_' . $table;
    unless ($theHash{$type}{value} eq '') {
      if ($theHash{$type}{value} eq 'NULL') {		# enter NULLs in postgres
        if ($order) {
          my $result2 = $conn->exec( "SELECT * FROM $table WHERE joinkey = '$joinkey' AND got_order = '$order' ORDER BY got_timestamp DESC;" );
          my @row2 = $result2->fetchrow;
          if ($row2[0]) { 				# data existed in that box
            if ($row2[2]) {	 			# was not null, now null, change
#               print "my \$result = \$conn->exec( \"INSERT INTO $table VALUES ('$joinkey', '$order', NULL);\" );<BR>\n"; 
              my $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$order', NULL);" ); } }
        } else {
          my $result2 = $conn->exec( "SELECT * FROM $table WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;" );
          my @row2 = $result2->fetchrow;
          if ($row2[0]) { 				# data existed in that box
            if ($row2[1]) {	 			# was not null, now null, change
#               print "my \$result = \$conn->exec( \"INSERT INTO $table VALUES ('$joinkey', NULL);\" );<BR>\n";
              my $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', NULL);" ); } } }
      } else { # if ($theHash{$type}{value} eq 'NULL')	# enter values in postgres
        my $value = &filterForPostgres($theHash{$type}{value});
        if ($order) {
          my $result2 = $conn->exec( "SELECT * FROM $table WHERE joinkey = '$joinkey' AND got_order = '$order' ORDER BY got_timestamp DESC;" );
          my @row2 = $result2->fetchrow;
          if ($row2[0]) { 				# data existed in that box
              if ($row2[2]) { if ($row2[2] ne $value) { 	# is different, so change
#                 print "my \$result = \$conn->exec( \"INSERT INTO $table VALUES ('$joinkey', '$order', '$value');\" );<BR>\n";
                my $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$order', '$value');" ); } } }
            else {					# no data previously in box, create
#               print "my \$result = \$conn->exec( \"INSERT INTO $table VALUES ('$joinkey', '$order', '$value');\" );<BR>\n"; 
              my $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$order', '$value');" ); }
        } else {
          my $result2 = $conn->exec( "SELECT * FROM $table WHERE joinkey = '$joinkey' ORDER BY got_timestamp DESC;" );
          my @row2 = $result2->fetchrow;
          if ($row2[0]) { 				# data existed in that box
              if ($row2[1]) { if ($row2[1] ne $value) { 	# is different, so change
#                 print "my \$result = \$conn->exec( \"INSERT INTO $table VALUES ('$joinkey', '$value');\" );<BR>\n";
                my $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$value');" ); } } }
            else {					# no data previously in box, create
#               print "my \$result = \$conn->exec( \"INSERT INTO $table VALUES ('$joinkey', '$value');\" );<BR>\n";
              my $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$value');" ); }
        }
      } # else # if ($theHash{$type}{value} eq 'NULL')
      print OUT "$type\t$theHash{$type}{value}\n";
    } # unless ($theHash{$type}{value} eq '')
  } # foreach $_  (sort keys %theHash)

  my $date = &getDate();
  print "$date<BR><BR>\n\n";
#   print OUT "$date\n\n";
  close (OUT) or die "Cannot close $data_file : $!";

#   &outputAce($oldAce);	# don't need this anymore (Ranjana)  2006 02 28
  print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/go_curation.cgi>Go Back to the Beginning</A><BR>\n"; 

  my ($go_preview) = &get_go($joinkey);			# use go_curation_go perl module to preview the go output
  $go_preview =~ s/\n/<\/TD><\/TR>\n<TR><TD>/g;
  $go_preview =~ s/\t/<\/TD><TD>\n/g;
  print "<P><TABLE border=1><TR><TD COLSPAN=15>.go preview<\/TD><\/TR>\n<TR><TD>$go_preview<\/TD><\/TR><P>\n";
} # sub write

sub preview {		# preview page.  pass form with hidden values for all values of html.
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/go_curation.cgi\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"max_columns\" VALUE=\"$max_columns\">\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey

# I think &makeAce is not in sync with the current dumper, so I don't think it's
# dumping properly, so I'm commenting out the .ace section of the preview below.  2006 02 25
#   my $oldAce = '';
#   $oldAce = &createOldAce($joinkey); 
#   my $newAce = &makeAce();
#   $oldAce =~ s/\n/<BR>\n/g;
#   $newAce =~ s/\n/<BR>\n/g;
#   print "<P>OLD ACE $oldAce<BR>\n";
#   print "NEW ACE $newAce<BR>\n";

  &getCurator();					# get the curator from %theHash
  if ($joinkey eq 'NULL') { 				# if no wbgene, warn
    print "<FONT COLOR='blue'><B>ERROR : No wbgene chosen, go back and select one</B></FONT><BR>\n"; 
  } elsif ($curator eq 'NULL') {			# if no curator, warn
    print "<FONT COLOR='blue'><B>ERROR : No curator chosen, go back and select one</B></FONT><BR>\n"; 
  } elsif ( $error_in_data ) { 1; 			# error in data (currently curators in columns missing)
  } else {						# if wbgene, show ``New Entry !'' button
    my $found = &findIfPgEntry("$joinkey");		# if wbgene, check if already in Pg
    if ($found) {					# if already in pg, show ``Update !'' button
      print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update !\">\n";
    } else {						# if new, show ``New Entry !'' button
      print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"New Entry !\">\n";
    } # else # if ($found)
  } # if ($joinkey eq 'NULL') 
  print "</FORM>";

} # sub preview

sub getHtmlValuesFromForm {	# read PGparameters value from html form, then display to html
  my $print_flag = shift;
  &readConvertions();
  &getPgGoTerms();					# from postgres tables updated twice a month
  my @allparameters = @PGparameters;
  foreach my $ontology (@ontology) {			# loop through each of three ontology types
    foreach my $column_type (@column_types) {
      for my $i (1 .. $max_columns) {			# loop through each column allowed
        my $field = $ontology . '_' . $column_type . $i;
        push @allparameters, $field } } }
  foreach my $type (@allparameters) {			# for all values for PG
    my $html_type = 'html_value_main_' . $type;
    my ($var, $val) = &getHtmlVar($query, $html_type);
    if ($val) { 					# if there is a value
      $theHash{$type}{value} = $val;			# put it in theHash for postgres (?)
      $theHash{$type}{html_value} = $val;		# put it in theHash for webpage
      $val = &filterToPrintHtml($val);			# filter Html to print it
      unless ($print_flag) {                            # print stuff unless repopulating hash after reading postgres for oldAce
        print "$type : $val";				# print it
        if ($type =~ m/paper_evidence/) {
          my @papers; my @wbpapers;			# split into separate paper links
          if ($val =~ m/, /) { @papers = split/, /, $val; } else { push @papers, $val; }
          foreach my $paper (@papers) {			# get convertion from Eimear's file  2004 09 27
            if ($paper =~ m/PMID:/) { $paper =~ s/PMID:/pmid/g; }
            if ($paper !~ m/WBPaper/) {
                if ($convertToWBPaper{$paper}) { 
                    $val = $convertToWBPaper{$paper};
                    push @wbpapers, $val; } 
                  else { $val = $paper; push @wbpapers, $val; } }
              else { $val = $paper; push @wbpapers, $val; }
            print " -- $paper is <A HREF=\"http://www.wormbase.org/db/misc/paper?name=$val;class=Paper\">$val</A>"; } 
          $val = join", ", @wbpapers;
        } # if ($type =~ m/paper_evidence/)		# link paper to WormBase
        print "<BR>\n"; }                               # print stuff unless repopulating hash after reading postgres for oldAce
#       unless ($print_flag) {				# print stuff unless repopulating hash after reading postgres for oldAce
#         print "$type : $val";	 			# print it
#         if ($type =~ m/paper_evidence/) { print "&nbsp;&nbsp;<A HREF=\"http://www.wormbase.org/db/misc/paper?name=%5B$val%5D;class=Paper\">Check WormBase</A>"; }	# link paper to WormBase
#         print "<BR>\n"; }				# print stuff unless repopulating hash after reading postgres for oldAce
      if ($type =~ m/goid/) {				# if it's a go id, check postgres 
        my @goTerms = $val =~ m/(\d+)/g;		# get the numbers
        foreach my $goTerm (@goTerms) {			# for each of those, find the matches and output
          $goTerm =~ s/^0+//g;				# take off leading zeroes
          if ($goTerm < 10) { $goTerm = '000000' . $goTerm; }	# and add appropriate number of zeroes
          elsif ($goTerm < 100) { $goTerm = '00000' . $goTerm; }
          elsif ($goTerm < 1000) { $goTerm = '0000' . $goTerm; }
          elsif ($goTerm < 10000) { $goTerm = '000' . $goTerm; }
          elsif ($goTerm < 100000) { $goTerm = '00' . $goTerm; }
          elsif ($goTerm < 1000000) { $goTerm = '0' . $goTerm; }
          $goTerm = 'GO:' . $goTerm;			# and add the GO: tag
          unless ($print_flag) {			# print stuff unless repopulating hash after reading postgres for oldAce
            if ($goTerm{$goTerm}) { print "$type : You've entered <FONT COLOR='green'>$goTerm</FONT> which corresponds to <FONT COLOR='green'>$goTerm{$goTerm}</FONT><BR>\n"; }		# print what's been chosen and what it is
              else { print "$type : You've entered <FONT COLOR='red'>$goTerm</FONT> which doesn't match anything in Postgres<BR>\n"; } }
        } # foreach my $goTerm (@goTerms)
      } # if ($type =~ m/goid/) 
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
    } else {						# if there is no value
      $theHash{$type}{value} = 'NULL';			# put NULL in theHash
      $theHash{$type}{html_value} = '';			# put blank in theHash for webpage
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"\">\n";
    } # else # if ($val) 
  } # foreach my $type (@allparameters) 

  foreach my $ontology (@ontology) {			# loop through each of three ontology types
    for my $i (1 .. $max_columns) {			# loop through each column allowed
      my $type = $ontology . '_' . 'goid' . $i;
      my $goid_value = $theHash{$type}{value};		# get goid value for that column
      if ($goid_value ne 'NULL') { 			# if it has data (a goid)
        $type = $ontology . '_' . 'curator_evidence' . $i;
        my $curator_evidence = $theHash{$type}{value};	# get the curator evidence for that column
        if ($curator_evidence eq 'NULL') { 		# if there isn't curator evidence
          $error_in_data++;				# flag it as bad data
          print "<FONT COLOR=red>ERROR : No curator evidence for GO ID $goid_value</FONT><BR>\n"; }	# show error message
  } } }

#   return $theHash{locus}{value};			# return the joinkey
  return $theHash{wbgene}{value};			# return the joinkey changed to wbgene for Kimberly 2005 10 14
} # sub getHtmlValuesFromForm

sub getPgGoTerms {
  my $result = $conn->exec( "SELECT * FROM got_goterm;" );
  while (my @row = $result->fetchrow) { $goTerm{$row[0]} = $row[1]; }
} # sub getPgGoTerms

sub getCurator {					# get the curator and convert for save file
  $curator = $theHash{curator}{value};			# get the curator
  if ($curator =~ m/Juancarlos/) { $curator = 'azurebrd'; }
  elsif ($curator =~ m/Carol/) { $curator = 'carol'; }
  elsif ($curator =~ m/Ranjana/) { $curator = 'ranjana'; }
  elsif ($curator =~ m/Kimberly/) { $curator = 'kimberly'; }
  elsif ($curator =~ m/Erich/) { $curator = 'erich'; } 
  elsif ($curator =~ m/Josh/) { $curator = 'josh'; } 
  else { 1; }
} # sub getCurator

sub findIfPgEntry {	# check postgres for wbgene entry already in
  my $joinkey = shift;
#   my $result = $conn->exec( "SELECT * FROM got_locus WHERE joinkey = '$joinkey';" );
  my $result = $conn->exec( "SELECT * FROM got_wbgene WHERE joinkey = '$joinkey';" );
  my @row; my $found;
  while (@row = $result->fetchrow) { $found = $row[1]; if ($found eq '') { $found = ' '; } }
    # if there's null or blank data, change it to a space so it will update, not insert
  return $found;
} # sub findIfPgEntry

sub filterForPostgres {	# filter values for postgres
  my $value = shift;
  $value =~ s/\'/\\\'/g;
  return $value;
} # sub filterForPostgres

# in Jex.pm
# sub filterToPrintHtml {	# filter values for printing html
#   my $val = shift;
#   $val =~ s/\&/&amp;/g;				# filter out ampersands first
#   $val =~ s/\"/&quot;/g;			# filter out double quotes
#   $val =~ s/\</&lt;/g;				# filter out open angle brackets
#   $val =~ s/\>/&gt;/g;				# filter out close angle brackets
#   return $val;
# } # sub filterToPrintHtml

#################  Action SECTION #################

#################  Formatting SECTION #################

sub dump {			# dump .ace file for citace upload
#   print "This takes a long time, please wait around 3 minutes for the link to show below.<BR>\n";
  `/home/postgres/work/get_stuff/for_ranjana/go_curation_dumper/go_curation_go_dumper.pl`;
#   `/home/postgres/work/citace_upload/concise/get_concise_to_ace.pl > /home/postgres/public_html/cgi-bin/data/concise_dump.ace`;
  print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest>Latest .go Dump</A><BR>\n";
} # sub dump

sub outputAce {			# don't need this anymore (Ranjana)  2006 02 28
  my ($oldAce) = @_;
  unless ($theHash{curator}{value}) { print "<FONT COLOR=red>ERROR No Curator Chosen.</FONT><BR>\n"; return; }
  else { 
    if ($theHash{curator}{value} =~ m/Ranjana/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_ranjana.ace'; }
    elsif ($theHash{curator}{value} =~ m/Carol/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_carol.ace'; }
    elsif ($theHash{curator}{value} =~ m/Kimberly/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_kimberly.ace'; }
    elsif ($theHash{curator}{value} =~ m/Erich/) {$ace_file = '/home/postgres/public_html/cgi-bin/data/go_erich.ace'; }
    elsif ($theHash{curator}{value} =~ m/Juancarlos/) {$ace_file = '/home/postgres/public_html/cgi-bin/data/go_juancarlos.ace'; }
    else { print "<FONT COLOR=red>ERROR Not a valid Curator Chosen.</FONT><BR>\n"; return; }
  }

  my $ace_entry;
  my $newAce = &makeAce();
  unless ($oldAce) { $ace_entry = $newAce; }
    else { $ace_entry = &findDiff($oldAce, $newAce); }

  open (ACE, ">>$ace_file") or die "Cannot append to $ace_file : $!";
  print ACE $ace_entry;
  close (ACE) or die "Cannot close $ace_file : $!";

#   print "OLDACE $oldAce OLDACE<BR>\n";
#   print "NEWACE $newAce NEWACE<BR>\n";
#   print "ACEENT $ace_entry ACEENT<BR>\n";

  $ace_file =~ s/^.*public_html//g;
  print "See all ace.ace <A HREF=\"http://tazendra.caltech.edu/~postgres$ace_file\">data</A>.<BR>";
} # sub outputAce

sub findDiff {
  my $ace_entry;
  my %old_hash; my %new_hash;
  my $type = '';		# can only be CDS or Locus
  my ($oldAce, $newAce) = @_;
  my (@oldEntries) = split/\n\n/, $oldAce;
  foreach my $oldEnt (@oldEntries) { 
    if ($oldEnt =~ m/Locus : \"([^\"]+)\"/) { $old_hash{$1} = $oldEnt; $type = 'Locus'; }
    if ($oldEnt =~ m/Gene : \"([^\"]+)\"/) { $old_hash{$1} = $oldEnt; $type = 'Gene'; }
    if ($oldEnt =~ m/CDS : \"([^\"]+)\"/) { $old_hash{$1} = $oldEnt; $type = 'CDS'; } }
  my (@newEntries) = split/\n\n/, $newAce;
  foreach my $newEnt (@newEntries) { 
    if ($newEnt =~ m/Locus : \"([^\"]+)\"/) { $new_hash{$1} = $newEnt; }
    if ($newEnt =~ m/Gene : \"([^\"]+)\"/) { $new_hash{$1} = $newEnt; }
    if ($newEnt =~ m/CDS : \"([^\"]+)\"/) { $new_hash{$1} = $newEnt; } }

  foreach my $new_entry (sort {$a <=> $b} keys %new_hash) {
    unless ($old_hash{$new_entry}) { $ace_entry .= "$new_hash{$new_entry}"; next; }
#     unless ($new_hash{$new_entry} eq $old_hash{$new_entry}) {  
#       my %cit_lines; my %pg_lines;
#       my $lines_to_print = '';
#       my @cit_lines = split/\n/, $old_hash{$new_entry};
#       my @pg_lines = split/\n/, $new_hash{$new_entry};
#       foreach (@cit_lines) { $cit_lines{$_}++; }
#       foreach (@pg_lines) { $pg_lines{$_}++; }
#       foreach my $pg_line (sort keys %pg_lines) { if ($cit_lines{$pg_line}) { delete $pg_lines{$pg_line}; delete $cit_lines{$pg_line}; } }
#       foreach my $cit_line (sort keys %cit_lines) { $lines_to_print .= "-D $cit_line\n"; }
#       foreach my $pg_line (sort keys %pg_lines) { $lines_to_print .= "$pg_line\n"; }
#       if ($lines_to_print) { $ace_entry .= "$type : \"$new_entry\"\n$lines_to_print\n"; }
#     }
    unless ($new_hash{$new_entry} eq $old_hash{$new_entry}) {  $ace_entry = &checkLines($ace_entry, $type, $new_entry, \%old_hash, \%new_hash); }
  } # foreach my $new_entry (sort keys %new_hash)
  return $ace_entry;
} # sub findDiff

sub checkLines {
  my ($ace_entry, $type, $num, $old_hash_ref, $new_hash_ref) = @_;
  my %cit_lines; my %pg_lines;
  my $lines_to_print = '';
  my @cit_lines = split/\n/, $$old_hash_ref{$num};	# dereference hash ref
  my @pg_lines = split/\n/, $$new_hash_ref{$num};	# dereference hash ref
  foreach (@cit_lines) { $cit_lines{$_}++; }
  foreach (@pg_lines) { $pg_lines{$_}++; }
  foreach my $pg_line (sort keys %pg_lines) { if ($cit_lines{$pg_line}) { delete $pg_lines{$pg_line}; delete $cit_lines{$pg_line}; } }
#   foreach my $cit_line (sort keys %cit_lines) { $lines_to_print .= "-D $cit_line\n"; }
#   foreach my $pg_line (sort keys %pg_lines) { $lines_to_print .= "$pg_line\n"; }
#   if ($lines_to_print) { $ace_entry .= "$type : \"$num\"\n$lines_to_print\n"; }
    # Changed to create .ace entry for each change instead of multiple -D and entries in single .ace entry for Ranjana / Raymond  2004 09 28
  foreach my $cit_line (sort keys %cit_lines) { $ace_entry .= "$type : \"$num\"\n-D $cit_line\n\n"; }
  foreach my $pg_line (sort keys %pg_lines) { $ace_entry .= "$type : \"$num\"\n$pg_line\n\n"; }
  return $ace_entry;
} # sub checkLines

sub makeAce {
  unless ($theHash{sequence}{value}) {             # no sequences, say so
    print "<FONT COLOR='red'>WARNING : no sequence for $theHash{locus}{value}</FONT><BR>\n";
  } else { # unless ($theHash{sequence})    # if sequence, then
    my $ace_entry = '';                                 # initialize entry
    for my $ontology (@ontology) {                      # for each of the three ontologies
      for my $i (1 .. $max_columns) {                              # for each of the three possible entries
        my $goid_tag = $ontology . '_goid' . $i;
        if ($theHash{$goid_tag}{value} ne 'NULL') {
          my $goid = $theHash{$goid_tag}{value};
          $goid =~ s/^\s+//g; $goid =~ s/\s+$//g;
# print "GOID $goid GOID<BR>\n";

          my @evidence_tags = qw( _goinference _goinference_two );      # the inference types
          foreach my $ev_tag (@evidence_tags) {                 # for each of the inference types
            my $evidence_tag = $ontology . $ev_tag . $i;        # get evidence tag
            if ( ($theHash{$evidence_tag}{value} ne 'NULL')  && ($theHash{$evidence_tag}{value} ne '') ) {
              my $inference = $theHash{$evidence_tag}{value};   # the inference type
              $inference =~ s/ --.*$//g;
# print "INF $inference INF<BR>\n";
              my $tag = $ontology . '_paper_evidence' . $i;
              my $db_reference = '';				# paper id number
              if ( ($theHash{$tag}{value} ne 'NULL') && ($theHash{$tag}{value} ne '') ) {
# print "TAG $tag VALUE -=$theHash{$tag}{value}=-<BR>\n"; 
                if ($theHash{$tag}{value} !~ m/, /) {		# and it's just one paper, print it
                  $db_reference = $theHash{$tag}{value};
# these numbers no longer imply pmid with wbpaper entries
#                   my ($number) = $db_reference =~ m/(\d+)/;
#                   if ($number > 10000) {
#                     my $key = 'pmid' . $number;
#                     $db_reference = $pmHash{$key};
#                   }
#                   $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"[$db_reference]\"\n";
                  if ($db_reference =~ m/WBPaper/) {
# print "1GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"<BR>\n"; 
                    $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
                  elsif ($convertToWBPaper{$db_reference}) {
# print "2GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$convertToWBPaper{$db_reference}\"<BR>\n"; 
                    $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$convertToWBPaper{$db_reference}\"\n"; }
                  else { print STDERR "NO Convertion for $db_reference\n"; }
                } else { 					# if it's multiple papers
                  my @papers = split /, /, $theHash{$tag}{value};
                  foreach my $paper (@papers) {			# print separate papers
                      $db_reference = $paper;
                      my ($number) = $db_reference =~ m/(\d+)/;
                      if ($number > 10000) {
                        my $key = 'pmid' . $number;
			if ($pmHash{$key}) { $db_reference = $pmHash{$key}; }	# if there's a cgc, write cgc else leave the same
                      }
	              $db_reference =~ s/\[//g;		# take out brackets so that they are not entered twice
	              $db_reference =~ s/\]//g;		# take out brackets so that they are not entered twice
#                       $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"[$db_reference]\"\n";
                      if ($db_reference =~ m/WBPaper/) {
# print "3GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"<BR>\n"; 
                        $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
                      elsif ($convertToWBPaper{$db_reference}) {
# print "4GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$convertToWBPaper{$db_reference}\"<BR>\n"; 
                        $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$convertToWBPaper{$db_reference}\"\n"; }
                      else { print STDERR "NO Convertion for $db_reference\n"; }
                  } # foreach my $paper (@papers)
                } # else # if ($theHash{$tag}{value} !~ m/ ,/)
              } # if ($theHash{$tag}{value})

# FIX THIS NEED TO ADD CURATOR EVIDENCE
    
              $tag = $ontology . '_person_evidence' . $i;
              if ( ($theHash{$tag}{value} ne 'NULL') && ($theHash{$tag}{value} ne '') ) {
# print "TAG2 VALUE -=$theHash{$tag}{value}=-<BR>\n"; 
                if ($theHash{$tag}{value} =~ m/ishore/) {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"WBPerson324\"\n";
                } elsif ($theHash{$tag}{value} =~ m/chwarz/) {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"WBPerson567\"\n";
                } else {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"$theHash{$tag}{value}\"\n";
                }
              } # if ($theHash{$tag}{value})
    
# deleted 2004 11 18 since not in form
#               $tag = $ontology . '_similarity' . $i;
#               if ( ($theHash{$tag}{value} ne 'NULL') && ($theHash{$tag}{value} ne '') ) {
# # print "TAG3 VALUE -=$theHash{$tag}{value}=-<BR>\n"; 
#                 $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tProtein_id_evidence\t\"$theHash{$tag}{value}\"\n";
#               } # if ($theHash{$tag}{value})

            } # if ($theHash{$evidence_tag}{value})
          } # foreach my $ev_tag (@evidence_tags) 
        } # if ($theHash{$goid_tag}{value} ne 'NULL')
      } # for my $i (1 .. $max_columns)
    } # for my $ontology (@ontology)
    $ace_entry .= "\n";                                 # add separator
# print "ACE ENT $ace_entry<BR><BR>\n";

    if ($theHash{wbgene}{value} =~ m/WBGene\d{8}/) {		# if wbgene entry, use the WBGene
      $ace_entry = "Gene : \"$theHash{wbgene}{value}\"\n$ace_entry"; }
    elsif ($theHash{sequence}{value} eq 'no') {		# if no entry, use the Gene (locus)
#       print ACE "Locus : \"$theHash{locus}{value}\"\n";
      $ace_entry = "Locus : \"$theHash{locus}{value}\"\n$ace_entry";
#       print ACE $ace_entry;
    } else { # if ($theHash{sequence}{value})		# if there's a sequence
      if ($theHash{sequence}{value} !~ m/[ ,]/) {	# and it's just one sequence, print it
#         print ACE "CDS : \"$theHash{sequence}{value}\"\n";	# changed Sequence to CDS
        $ace_entry = "CDS : \"$theHash{sequence}{value}\"\n$ace_entry";		# changed Sequence to CDS
#         print ACE $ace_entry;
      } else { # if ($theHash{sequence}{value} !~ m/[ ,]/)	# if it's many sequences, print for each
        my @sequences = split /, /, $theHash{sequence}{value};
        my $temp_entry = '';
        foreach my $seq (@sequences) {                  # print separate sequences
          $temp_entry .= "CDS : \"$seq\"\n$ace_entry";	# changed Sequence to CDS
#           print ACE "CDS : \"$seq\"\n";
#           print ACE $ace_entry;
        } # foreach my $seq (@sequences)
        $ace_entry = $temp_entry;
      } # else # if ($theHash{sequence}{value} !~ m/[ ,]/)
    } # else # if ($theHash{sequence}{value})
    return $ace_entry;
  } # else # unless ($theHash{sequence}{value})
} # sub makeAce


sub populateXref {              # if not found, get ref_xref data to try to find alternate
  my $result = $conn->exec( "SELECT * FROM ref_xref;" );
  while (my @row = $result->fetchrow) { # loop through all rows returned
    $cgcHash{$row[0]} = $row[1];        # hash of cgcs, values pmids
    $pmHash{$row[1]} = $row[0];         # hash of pmids, values cgcs
  } # while (my @row = $result->fetchrow)
} # sub populateXref

sub readConvertions {
  my $u = "http://tazendra.caltech.edu/~acedb/paper2wbpaper.txt";
  my $ua = LWP::UserAgent->new(timeout => 30); #instantiates a new user agent
  my $request = HTTP::Request->new(GET => $u); #grabs url
  my $response = $ua->request($request);       #checks url, dies if not valid.
  die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
  my @tmp = split /\n/, $response->content;    #splits by line
  foreach (@tmp) {
    if ($_ =~m/^(.*?)\t(.*?)$/) {
      $convertToWBPaper{$1} = $2; } }
} # sub readConvertions


#################  Formatting SECTION #################

#################  HTML SECTION #################

sub printHtmlForm {	# Show the form 
  &printHtmlFormStart();
  &printHtmlSection('GO_annotation');
#   &printHtmlSelectCurators('curator');		# print html select blocks for curators # moved curators to columns 2006 02 25
  &printHtmlInputQuery('wbgene');        	# input with Query button
  &printHtmlInputQuery('locus');        	# input with Query button
  &printHtmlInput('sequence');        	
  &printHtmlInput('synonym');        
#   &printHtmlInput('wbgene');        
#   &printHtmlTextarea('sequence');
  &printHtmlTextarea('protein');
#   &printHtmlSelectType('dbtype');        	# not main in new form 2004 08 11
  my $host = $query->remote_host();         # get ip address
#   print "HOST $host HOST<BR>\n";
  if ($host eq '131.215.52.82') {		# orthogonalize for Kimberly 2007 01 25
#   if ($host eq '131.215.52.76') { # } 		
    &printHtmlHorizontal('bio');
    &printHtmlHorizontal('cell');
    &printHtmlHorizontal('mol');
  }
  else {
    &printHtmlSection('Biological Process');
    &printHtmlTextareaBlock('bio_goterm');
    &printHtmlTextareaBlock('bio_goid');
    &printHtmlTextareaBlock('bio_paper_evidence');
    &printHtmlTextareaBlock('bio_person_evidence');
    &printHtmlSelectBlock('bio_curator_evidence');
    &printHtmlSelectBlock('bio_goinference');
    &printHtmlSelectBlock('bio_dbtype');
    &printHtmlTextareaBlock('bio_protein');
    &printHtmlTextareaBlock('bio_with');
    &printHtmlSelectQualifierBlock('bio_qualifier');
    &printHtmlSelectBlock('bio_goinference_two');
    &printHtmlSelectBlock('bio_dbtype_two');
    &printHtmlTextareaBlock('bio_protein_two');
    &printHtmlTextareaBlock('bio_with_two');
    &printHtmlSelectQualifierBlock('bio_qualifier_two');
    &printHtmlTextareaBlock('bio_comment');
    &printHtmlTextareaBlock('bio_lastupdate');
    &printHtmlSection('Cellular Component');
    &printHtmlTextareaBlock('cell_goterm');
    &printHtmlTextareaBlock('cell_goid');
    &printHtmlTextareaBlock('cell_paper_evidence');
    &printHtmlTextareaBlock('cell_person_evidence');
    &printHtmlSelectBlock('cell_curator_evidence');
    &printHtmlSelectBlock('cell_goinference');
    &printHtmlSelectBlock('cell_dbtype');
    &printHtmlTextareaBlock('cell_protein');
    &printHtmlTextareaBlock('cell_with');
    &printHtmlSelectQualifierBlock('cell_qualifier');
    &printHtmlSelectBlock('cell_goinference_two');
    &printHtmlSelectBlock('cell_dbtype_two');
    &printHtmlTextareaBlock('cell_protein_two');
    &printHtmlTextareaBlock('cell_with_two');
    &printHtmlSelectQualifierBlock('cell_qualifier_two');
    &printHtmlTextareaBlock('cell_comment');
    &printHtmlTextareaBlock('cell_lastupdate');
    &printHtmlSection('Molecular Function');
    &printHtmlTextareaBlock('mol_goterm');
    &printHtmlTextareaBlock('mol_goid');
    &printHtmlTextareaBlock('mol_paper_evidence');
    &printHtmlTextareaBlock('mol_person_evidence');
    &printHtmlSelectBlock('mol_curator_evidence');
    &printHtmlSelectBlock('mol_goinference');
    &printHtmlSelectBlock('mol_dbtype');
    &printHtmlTextareaBlock('mol_protein');
    &printHtmlTextareaBlock('mol_with');
    &printHtmlSelectQualifierBlock('mol_qualifier');
    &printHtmlSelectBlock('mol_goinference_two');
    &printHtmlSelectBlock('mol_dbtype_two');
    &printHtmlTextareaBlock('mol_protein_two');
    &printHtmlTextareaBlock('mol_with_two');
    &printHtmlSelectQualifierBlock('mol_qualifier_two');
    &printHtmlTextareaBlock('mol_comment');
    &printHtmlTextareaBlock('mol_lastupdate');
  }
  &printHtmlFormEnd();
} # sub printHtmlForm

sub printHtmlHorizontal {				# horizontal view for a section
  my $type = shift;
  if ($type eq 'bio') { &printHtmlSection('Biological Process'); }
  elsif ($type eq 'cell') { &printHtmlSection('Cellular Component'); }
  elsif ($type eq 'mol') { &printHtmlSection('Molecular Function'); }
  print "<TR>\n";
  &printHtmlHeaderCell($type, '_goterm'); 
  &printHtmlHeaderCell($type, '_goid'); 
  &printHtmlHeaderCell($type, '_paper_evidence'); 
  &printHtmlHeaderCell($type, '_person_evidence'); 
  &printHtmlHeaderCell($type, '_curator_evidence'); 
  &printHtmlHeaderCell($type, '_goinference'); 
  &printHtmlHeaderCell($type, '_dbtype'); 
  &printHtmlHeaderCell($type, '_protein'); 
  &printHtmlHeaderCell($type, '_with'); 
  &printHtmlHeaderCell($type, '_qualifier'); 
  &printHtmlHeaderCell($type, '_goinference_two'); 
  &printHtmlHeaderCell($type, '_dbtype_two'); 
  &printHtmlHeaderCell($type, '_protein_two'); 
  &printHtmlHeaderCell($type, '_with_two'); 
  &printHtmlHeaderCell($type, '_qualifier_two'); 
  &printHtmlHeaderCell($type, '_comment'); 
  &printHtmlHeaderCell($type, '_lastupdate'); 
  print "</TR>\n";
  for my $i (1 .. $max_columns) {
    print "<TR>\n";
    &printHtmlTextareaCell($type, '_goterm', $i); 
    &printHtmlTextareaCell($type, '_goid', $i); 
    &printHtmlTextareaCell($type, '_paper_evidence', $i); 
    &printHtmlTextareaCell($type, '_person_evidence', $i); 
    &printHtmlSelectCell($type, '_curator_evidence', $i);
    &printHtmlSelectCell($type, '_goinference', $i);
    &printHtmlSelectCell($type, '_dbtype', $i);
    &printHtmlTextareaCell($type, '_protein', $i); 
    &printHtmlTextareaCell($type, '_with', $i); 
    &printHtmlSelectCell($type, '_qualifier', $i);
    &printHtmlSelectCell($type, '_goinference_two', $i);
    &printHtmlSelectCell($type, '_dbtype_two', $i);
    &printHtmlTextareaCell($type, '_protein_two', $i); 
    &printHtmlTextareaCell($type, '_with_two', $i); 
    &printHtmlSelectCell($type, '_qualifier_two', $i);
    &printHtmlTextareaCell($type, '_comment', $i); 
    &printHtmlTextareaCell($type, '_lastupdate', $i); 
    print "</TR>\n";
  } # for my $i (1 .. $max_columns)
} # sub printHtmlHorizontal

sub printHtmlHeaderCell {					# horizontal view for a section header
  my ($type, $subtype) = @_;
  my $main_type = $type . $subtype;
  print "  <TD ALIGN=\"center\"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>\n";
} # sub printHtmlHeaderCell

sub printHtmlTextareaCell {					# horizontal view for a textarea cell
  my ($type, $subtype, $i) = @_;
  my $fulltype = $type . $subtype . $i;
  print"    <TD><TEXTAREA NAME=\"html_value_main_$fulltype\" ROWS=$theHash{$fulltype}{html_size_minor}
                COLS=$theHash{$fulltype}{html_size_main}>$theHash{$fulltype}{html_value}</TEXTAREA></TD>\n";
} # sub printHtmlTextareaCell

sub printHtmlSelectCell {					# print html select Block for horizontal display
  my ($type, $subtype, $i) = @_;
    my $fulltype = $type . $subtype . $i;
    my @choices = ();
    if ($fulltype =~ m/inference/) { @choices = (' ', 'IDA','IEA','IEP','IGI','IMP','IPI','ISS','NAS','ND','IC','TAS', 'RCA'); }
    elsif ($fulltype =~ m/dbtype/) { @choices = ('', 'protein', 'gene', 'transcript', 'complex', 'protein_structure'); }
    elsif ($fulltype =~ m/qualifier/) { @choices = (' ', 'NOT', 'contributes_to', 'colocalizes_with'); }		# added colocalizes_with for kimberly 2004 08 24
    elsif ($fulltype =~ m/curator_evidence/) { @choices = ('', 'Carol Bastiani', 'Josh Jaffery', 'Ranjana Kishore', 'Raymond Lee', 'Erich Schwarz', 'Kimberly Van Auken', 'Juancarlos Testing'); }
    else { @choices = ('not a valid choice type in printHtmlSelectBlock $fulltype' ); }
    print "    <TD><SELECT NAME=\"html_value_main_$fulltype\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$fulltype}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@choices) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
} # sub printHtmlSelectCell

sub printHtmlSection {          # print html sections
  my $text = shift;             # get name of section
  print "\n  "; for (0..12) { print '<TR></TR>'; } print "\n\n";                # divider
  print "  <TR><TD><STRONG><FONT SIZE=+1>$text : </FONT></STRONG></TD></TR>\n"; # section
} # sub printHtmlSection

sub printHtmlInputQuery {       # print html inputs with queries (just pubID)
  my $type = shift;             # get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  
         SIZE=$theHash{$type}{html_size_main}></TD>
    <TD ALIGN="left"><!--<INPUT TYPE="submit" NAME="action" VALUE="Query Sanger !"><BR>-->
                     <INPUT TYPE="submit" NAME="action" VALUE="Query $type !"></TD>
  </TR> 
  EndOfText
} # sub printHtmlInputQuery

sub printHtmlInput {            # print html inputs
  my $type = shift;             # get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  
         SIZE=$theHash{$type}{html_size_main}></TD>
  </TR>
  EndOfText
} # sub printHtmlInput

sub printHtmlTextarea {         # print html textareas
  my $type = shift;             # get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD><TEXTAREA NAME="html_value_main_$type" ROWS=$theHash{$type}{html_size_minor}
                  COLS=$theHash{$type}{html_size_main}>$theHash{$type}{html_value}</TEXTAREA></TD>
  </TR>
  EndOfText
} # sub printHtmlTextarea

sub printHtmlTextareaBlock {	# print html textarea blocks (sets of three)
				# e.g. : &printHtmlTextareaBlock('bio_goterm');
  my $main_type = shift;	# get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $max_columns) {
    my $type = $main_type . $i;
    print"    <TD><TEXTAREA NAME=\"html_value_main_$type\" ROWS=$theHash{$type}{html_size_minor}
                  COLS=$theHash{$type}{html_size_main}>$theHash{$type}{html_value}</TEXTAREA></TD>\n";
  } # for my $i (1 .. $max_columns)
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlTextareaBlock 

sub printHtmlSelectCurators {	# print html select blocks for curators	# no longer using this 2006 02 25
  my $type = shift;
  my @curators = ('Carol Bastiani', 'Josh Jaffery', 'Ranjana Kishore', 'Erich Schwarz', 'Kimberly Van Auken', 'Juancarlos Testing');
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
  print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n";
    # if loaded or queried, show option, otherwise default to '' option
  foreach (@curators) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n  </TR>\n";
} # sub printHtmlSelectCurators

sub printHtmlSelectType {	# print html select blocks for curators
  my $type = shift;
  my @types = ('', 'protein', 'gene', 'transcript', 'complex', 'protein_structure');
  my ($var, $action) = &getHtmlVar($query, 'action');
    # first time or query sanger, no action, protein
  if ( ($action eq '') || ($action eq 'Query Sanger !') ) { $theHash{$type}{html_value} = 'protein'; }	
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
  print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n";
    # if loaded or queried, show option, otherwise default to '' option
  foreach (@types) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n  </TR>\n";
} # sub printHtmlSelectType

sub printHtmlSelectBlock {	# print html select blocks for inference type (set of three)
				# e.g. : &printHtmlSelectBlock('bio_goinference');
  my $main_type = shift;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $max_columns) {
    my $type = $main_type . $i;
#     my @inferences = (' ', 'IDA -- Inferred from Direct Assay','IEA -- Inferred from Electronic
# Annotation','IEP -- Inferred from Expression Pattern','IGI -- Inferred from Genetic
# Interaction','IMP -- Inferred from Mutant Phenotype','IPI -- Inferred from Physical
# Interaction','ISS -- Inferred from Sequence or structural Similarity','NAS -- Non-traceable Author
# Statement','ND -- No Biological Data Available','IC -- Inferred by Curator','TAS -- Traceable Author
# Statement');
    my @choices = ();
    if ($main_type =~ m/inference/) { @choices = (' ', 'IDA','IEA','IEP','IGI','IMP','IPI','ISS','NAS','ND','IC','TAS', 'RCA'); }
    elsif ($main_type =~ m/dbtype/) { @choices = ('', 'protein', 'gene', 'transcript', 'complex', 'protein_structure'); }
    elsif ($main_type =~ m/curator_evidence/) { @choices = ('', 'Carol Bastiani', 'Josh Jaffery', 'Ranjana Kishore', 'Raymond Lee', 'Erich Schwarz', 'Kimberly Van Auken', 'Juancarlos Testing'); }
    else { @choices = ('not a valid choice type in printHtmlSelectBlock $main_type' ); }
#     my @inferences = (' ', 'IDA','IEA','IEP','IGI','IMP','IPI','ISS','NAS','ND','IC','TAS');
    print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@choices) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
  } # for my $i (1 .. $max_columns)
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlSelectBlock

sub printHtmlSelectQualifierBlock {	# print html select blocks for inference type (set of three)
					# e.g. : &printHtmlQualifierBlock('bio_goinference');
  my $main_type = shift;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $max_columns) {
    my $type = $main_type . $i;
    my @qualifiers = (' ', 'NOT', 'contributes_to', 'colocalizes_with');	# added colocalizes_with for kimberly 2004 08 24
    print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@qualifiers) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
  } # for my $i (1 .. $max_columns)
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlQualifierBlock

sub printHtmlFormStart {        # beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/go_curation.cgi">
  <INPUT TYPE="HIDDEN" NAME="max_columns" VALUE="$max_columns">
  <TABLE>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <!--<INPUT TYPE="submit" NAME="action" VALUE="Options !">--><BR>
        <INPUT TYPE="submit" NAME="action" VALUE="Add Column !"><BR>
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Dump .go !"><BR> shouldn't have been using this for a while  2006 08 01-->
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !"><BR> no longer using this 2006 02 27-->
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR>
  <TR>
    <TD> </TD>
    <TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest>Latest .go Dump</A></TD></TR>
  EndOfText
} # sub printHtmlFormStart

sub printHtmlFormEnd {          # ending of form
  print <<"  EndOfText";
  <TR><TD COLSPAN=2> </TD></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <!--<INPUT TYPE="submit" NAME="action" VALUE="Options !">--><BR>
        <INPUT TYPE="submit" NAME="action" VALUE="Add Column !"><BR>
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Dump .go !"><BR> shouldn't have been using this for a while  2006 08 01-->
<!--        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !"><BR> no longer using this 2006 02 27-->
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR>
  <TR>
    <TD> </TD>
    <TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest>Latest .go Dump</A></TD></TR>
  </TABLE>
  </FORM>
  EndOfText
} # sub printHtmlFormEnd

#################  HTML SECTION #################

#################  HASH SECTION #################

sub initializeHash {
  # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects.
  # in case of new fields, add to @PGparameters array and create html_field_name entry in %theHash
  # and other %theHash fields as necessary.  if new email address, add to %emails.

  my ($var, $val) = &getHtmlVar($query, 'max_columns');
  if ($val) { $max_columns = $val; }
  else { $max_columns = 3; }

#   @PGparameters = qw(curator locus sequence synonym protein wbgene);
  @PGparameters = qw(locus sequence synonym protein wbgene);
  foreach my $ontology (@ontology) {		# loop through each of three ontology types
    for my $i (1 .. $max_columns) {		# loop through each column allowed
      my $field = $ontology . '_' . $i;
      $theHash{$field}{html_field_name} = '';
      $theHash{$field}{html_value} = '';
      $theHash{$field}{html_size_main} = '20';            # default width 40
      $theHash{$field}{html_size_minor} = '2';            # default height 2
    }
    $theHash{"${ontology}_goterm"}{html_field_name} = 'GO Term';
    $theHash{"${ontology}_goid"}{html_field_name} = 'GO ID';
    $theHash{"${ontology}_paper_evidence"}{html_field_name} = 'Paper Evidence<BR>(check it exists <BR>in <A HREF="http://www.wormbase.org/db/misc/paper?name=;class=Paper">WormBase</A>)';
    $theHash{"${ontology}_person_evidence"}{html_field_name} = 'Person Evidence';
    $theHash{"${ontology}_curator_evidence"}{html_field_name} = 'Curator Evidence';
    $theHash{"${ontology}_goinference"}{html_field_name} = 'GO Evidence 1';
    $theHash{"${ontology}_dbtype"}{html_field_name} = 'DB_Object_Type 1';
    $theHash{"${ontology}_protein"}{html_field_name} = 'Gene Product (Protein) 1';
    $theHash{"${ontology}_with"}{html_field_name} = 'with 1';
    $theHash{"${ontology}_qualifier"}{html_field_name} = 'Qualifier 1';
    $theHash{"${ontology}_goinference_two"}{html_field_name} = 'GO Evidence 2';
    $theHash{"${ontology}_dbtype_two"}{html_field_name} = 'DB_Object_Type 2';
    $theHash{"${ontology}_protein_two"}{html_field_name} = 'Gene Product (Protein) 2';
    $theHash{"${ontology}_with_two"}{html_field_name} = 'with 2';
    $theHash{"${ontology}_qualifier_two"}{html_field_name} = 'Qualifier 2';
#     $theHash{"${ontology}_similarity"}{html_field_name} = 'Protein ID Evidence';
    $theHash{"${ontology}_comment"}{html_field_name} = 'Comment';
    $theHash{"${ontology}_lastupdate"}{html_field_name} = 'Timestamp Column<BR>Last Updated e.g.<BR>``2006-11-01 16:05:42\'\'';
  } # foreach my $ontology (@ontology)


  foreach my $field (@PGparameters) {
    $theHash{$field}{html_field_name} = '';
    $theHash{$field}{html_value} = '';
    $theHash{$field}{html_size_main} = '20';            # default width 40
    $theHash{$field}{html_size_minor} = '2';            # default height 2
  } # foreach my $field (@PGparameters)

  $theHash{curator}{html_field_name} = 'Curator';
  $theHash{locus}{html_field_name} = 'Locus';
  $theHash{sequence}{html_field_name} = 'Sequence';
  $theHash{synonym}{html_field_name} = 'Synonym';
  $theHash{wbgene}{html_field_name} = 'WBGene';
  $theHash{protein}{html_field_name} = 'Gene Product (Protein)';
#   $theHash{dbtype}{html_field_name} = 'DB_Object_Type';

} # sub initializeHash

#################  HASH SECTION #################


