#!/usr/bin/perl -w

# Edit Concise Description Data
#
# Update Block button needs to be checked for the form to look at the block of data.  
#
# Added href to name's of sections and showed menus at top of each section.
# Added Second + Extra Sentences of Provisional Description
# Fixed error in mailing, wasn't checking each box, was first checking if concise
# description was checked.
# Read Erich's human-readable *LongText* .ace data from 
# /home/postgres/work/pgpopulation/concise_description/annots-27may2004_old-format.ace
# 2004 06 16
#
# Changed data from 3-letter form to WBGene form (manually since it was so little)
# Changed form so that it would find the appropriate joinkey depending on whether
# the gene matched WBGene00000000 format, or 3-letter format (converting joinkey to 
# WBGene format)
# Added &getSangerConversion(); for this purpose to &preview(); &write(); and &query();
# and changed them so they would find the right joinkey.  2004 06 17
#
# Added Person Reference field.  Created &addAnother($type); to see which section
# and add another block for that section.  Created %aceTrans to convert 3-letter pg
# key into form displayable text.  Changed %theHash everywhere to deal with the new
# %theHash structure which has $theHash{$type}{$i} so that $i can be stored in postgres
# to have an arbitrary number of $i in a given table (as opposed to a hardcoded amount
# of tables).  Changed &readable(); to work with new %theHash.  2004 07 28
#
# Fixed error in write(); which was using $val instead of $cur to write the value
# (instead of the curator) to curator subfields in postgres.  2004 08 06
#
# Changed dumpers so they only dump joinkeys that ~ 'WBGene' since there are now 
# entries with curator names _001 to use as ``Save'' entries (for ``Save'' and ``Load''
# buttons).  Make &saveState(); save whatever's checked into postgres entry with
# curatorname_001 as joinkey and WBGene as value for car_lastcurator table.
# Make &loadState(); do reverse and populate checkboxes if there's data for that
# table.  2004 09 22
#
# Fixed some values that were being printed to Html without initializing and
# making the error_log longer.  2005 02 08
#
# Change section ``Other'' to ``Other Description'' get rid of Phenotype section
# for Carol.  2005 04 25
#
# Get data from :
# http://www.sanger.ac.uk/Projects/C_elegans/LOCI/genes2molecular_names.txt
# when querying sanger to also get CDS data (for Erich).
# strip whitespace from front and end of  gene  entered because otherwise it
# will not match sanger data (just cleaning it up).  2005 05 06
#
# Create car_whatever_ref_reference, which stores merge of data from
# car_whatever_ref_paper and car_whatever_ref_person.  Also create
# car_whatever_ref_accession for con and seq. 
# Create Update Last_Verified Timestamp for con to store in postgres last time
# concise_description was verified.
# Still need to update .ace dump and readable and preview to match new tables
# and fields.  for Carol.   2005 05 12
#
# Wrote a .ace preview like the dumper, but this only shows data that has been
# checkmarked to Update Block (or Update Last_verified).  Linked dumper to 
# the new dumper.  2005 06 15
#
# &addAnother() wasn't using &getSangerConversion(); so no entries matched.
# 2005 06 21
#
# Edited &getHtmlValuesFromFrom(); to read concise referenes to
# $theHash{evidences}, to work like the dumper.  2005 06 30
# 
#
# Repopulated reference data with :
# /home/postgres/work/pgpopulation/concise_description/move_paper_person_reference_to_reference_accession/create_and_populate_tables.pl
# Looks okay.  2005 07 05
#
# Switch url to get locally instead of from Sanger.  2005 07 13
#
# Updated to dump using a wrapper.pl that dumps to
# /home/postgres/work/citace_upload/concise/old/concise_dump.date.hour.ace
# and symlinks to /home/postgres/public_html/cgi-bin/data/concise_dump_new.ace
# to match cronjob for Erich.  2005 09 15
#
# Changed &query(); so that if it fails, don't make them click back just 
# assign the gene and show the form.  2005 11 24
#
# After doing a &write(); link out to the gene in the checkout form to grafitti
# and check in.  For Kimberly.  2005 11 28
#
# Created &printHtmlCurators(); which shows all curators that changed the 
# car_con_maindata box (look at car_con_ref_curator) for Kimberly  2005 12 22
#
# Added a car_con_nodump table which checks whether a gene should be dumped of
# not.  Added to &query();, &write(); &getHtmlValuesFromForm(); and &mainPage();
# Created &updatePostgresNoDump(); to check whether there's a new value or if
# the values is different.  Created &printHtmlCheckbox(); to display on the
# form.  2006 01 27
#
# Default to 4 sets of boxes for Kimberly.  When querying data, it's showing
# what is there, but then the update boxes are not checked on (because the data
# is not going to be changed by the curator by default), but when adding another
# box, the form loses the data for all the fields that didn't have a checkbox
# on.  This should be revisited and possibly the form rewritten to work like the
# allele form written for Carol (always look at all data, get all postgres data
# and compare to current entry, then only write changes).  2006 03 01
#
# Capture date of curator_confirmed text_only field for Kimberly.  2006 08 15
#
# Updated to use gin_ postgres values based on nameserver and aceserver
# instead of obsolete loci_all and genes2molecular_names.  2006 12 19
#
# Added link to main curation form after a &write(); to avoid double back
# clicking.  For Ranjana.  2007 01 29
#
# Added Gary  2007 02 01
#
# Added Karen  2010 05 22
#
# created %wbGeneDead to store and display gin_dead / gin_history   2010 08 09
#
# changed  notifyPostgresPreviousCurator  to not email erich, andrei, nor igor.
# 2010 09 09
#
# changed  notifyPostgresPreviousCurator  to not email carol.  also write message
# about curator being retired.  2010 11 08
#
# added snehalvk@caltech.edu / Snehalata Kadam - WBPerson12884   2011 05 10
#
# added hum tables for human disease.
# car_hum_maindata car_hum_ref_curator car_hum_ref_reference car_hum_ref_accession car_hum_last_verified
# Not completely sure everything works correctly, but we'll rewrite this at 
# some point anyway (hopefully soon).  2011 06 03



 
use strict;
use diagnostics;
use CGI;
use Jex;
use LWP;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $query = new CGI;




my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color

my $frontpage = 1;			# show the front page on first load
my $curator;
my @PGsubparameters = qw( seq fpa fpi bio mol exp oth phe );

my %theHash;
my %emails;
my %aceCurators;		# wbpersons referenced anywhere for .ace preview
my %acePapers;			# papers referenced anywhere for .ace preview
my %wbGene;			# sanger gene conversion
my %wbGeneBack;			# sanger gene conversion
my %wbGeneDead;			# is the gene dead 

my %convertToWBPaper;		# key cgc or pmid or whatever, value WBPaper
my %aceTrans;

&printHeader('Concise Description Form');
&initializeHash();              # create complex data structure
&display();
&printFooter();

sub display {
  my $action;
  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); }
  } else { $frontpage = 0; }

  print "ACTION : $action<BR>\n";
  if ($action eq 'Curator !') { &mainPage(); }
  elsif ($action eq 'Preview !') { &preview(); }
  elsif ($action eq 'New Entry !') { &write('new'); }	# write to postgres (INSERT)
  elsif ($action eq 'Update !') { &write('update'); }	# write to postgres (UPDATE)
  elsif ($action eq 'Save !') { &saveState(); }		# write to postgres (SAVE)
  elsif ($action eq 'Load !') { &loadState(); }		# query postgres for entry (LOAD)
  elsif ($action eq 'Query !') { &query('query'); }	# query postgres
#   elsif ($action eq 'Delete !') { &deleteGene('test'); }	# delete data removed at Kimberly's request  2007 05 17
#   elsif ($action eq 'Confirm Delete !') { &deleteGene('confirm'); }	# delete data
  elsif ($action eq 'Dump Postgres !') { &dump(); }	# dump postgres to file
  elsif ($action eq 'Dump Readable !') { &readable(); }	# dump postgres to human readable file
  elsif ($action eq 'Reset !') { &reset(); }		# clear form
  elsif ($action =~ m/Add another (.*?) !/) { &addAnother($1); }	# add another block of data
  print "ACTION : $action<BR>\n";
} # sub display

sub reset {
  &initializeHash();					# Re-initialize %theHash structure for html names and box sizes
  &mainPage();						# Display form (now empty)
} # sub reset

sub addAnother {					# add another block of data by setting hash value
  my $type = shift;					# to add to later on in printHtmlInputs
  &getSangerConversion(); 
  if ($type eq 'Concise Description') { $theHash{con}{num_add}++; }
  elsif ($type eq 'Human Disease Relevance') { $theHash{hum}{num_add}++; }
  elsif ($type eq 'Second + Extra Sentences') { $theHash{ext}{num_add}++; }
  elsif ($type eq 'Sequence Features') { $theHash{seq}{num_add}++; }
  elsif ($type eq 'Functional Pathway') { $theHash{fpa}{num_add}++; }
  elsif ($type eq 'Functional Physical Interaction') { $theHash{fpi}{num_add}++; }
  elsif ($type eq 'Biological Process') { $theHash{bio}{num_add}++; }
  elsif ($type eq 'Molecular Function') { $theHash{mol}{num_add}++; }
  elsif ($type eq 'Expression') { $theHash{exp}{num_add}++; }
  elsif ($type eq 'Other') { $theHash{oth}{num_add}++; }
  elsif ($type eq 'Phenotype') { $theHash{phe}{num_add}++; }
  else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $type NOT a valid Add Column type</B></FONT><BR>\n"; }
  my $hidden_values = &getHtmlValuesFromForm();
  &mainPage();
} # sub addAnother

sub getSangerConversion {
  my @pgtables = qw( gin_protein gin_seqname gin_synonyms gin_locus );	# use seqname instead of sequence for Erich  2007 02 01
  foreach my $table (@pgtables) {                                       # updated to get values from postgres 2006 12 19
    my $result = $dbh->prepare( "SELECT * FROM $table;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      my $wbgene = 'WBGene' . $row[0];
      $wbGene{$row[1]} = $wbgene;
      if ($wbGeneBack{$wbgene}) { $wbGeneBack{$wbgene} .= $row[1]; }
        else { $wbGeneBack{$wbgene} = $row[1]; } } }
  $wbGene{'test-1'} = 'WBGene00000000';
  $wbGeneBack{'WBGene00000000'} = 'test-1';
  my @dead_tables = qw( gin_dead );					# added 2010 08 09
#   my @dead_tables = qw( gin_dead gin_history );
  foreach my $table (@dead_tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $wbGeneDead{$table}{$row[0]} = $row[1]; } }
} # sub getSangerConversion


sub query {
  &getSangerConversion(); 
  my ($var, $gene) = &getHtmlVar($query, 'html_value_gene');
  if ($gene =~ m/^\s+/) { $gene =~ s/^\s+//g; }
  if ($gene =~ m/\s+$/) { $gene =~ s/\s+$//g; }
  my $joinkey;
  if ($gene =~ m/^WBGene\d{8}/) { $joinkey = $gene; }
    else {
      if ($wbGene{$gene}) { $joinkey = $wbGene{$gene}; }
        else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $gene NOT in sanger list</B></FONT><BR>\n"; next; }
      if ($gene) { print "GENE $gene IS $joinkey<BR>\n"; }
        else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : Need to enter a Gene</B></FONT><BR>\n"; next; } }
  my ($gin_joinkey) = $joinkey =~ m/(\d+)/;				# added 2010 08 09
  if ($wbGeneDead{'gin_dead'}{$gin_joinkey}) { print "WBGene$gin_joinkey has gin_dead as $wbGeneDead{'gin_dead'}{$gin_joinkey}<br />\n"; }
  if ($wbGeneDead{'gin_history'}{$gin_joinkey}) { print "WBGene$gin_joinkey has gin_history as $wbGeneDead{'gin_history'}{$gin_joinkey}<br />\n"; }
  my $result = $dbh->prepare( "SELECT * FROM car_lastcurator WHERE joinkey = \'$joinkey\' ORDER BY car_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; 
  my $found = '';
  $found = $row[1];					# curator from car_lastcurator
  if ($found eq '') { 
#     print "Entry $joinkey not found, please click <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_new.cgi?action=Curator+%21&curator_name=\"$curator\">here</A> and create it.\n"; return; 
    print "Entry $joinkey not found, please create it.<BR>\n"; 	# don't make them click back
    $theHash{gene}{html_value} = $joinkey; 			# just assign the gene
    &mainPage(); }						# and show the form  2005 11 24
  else {
#     print "FOUND $found<BR>\n";
    $theHash{gene}{html_value} = $joinkey; 

    my $result=$dbh->prepare( "SELECT * FROM car_con_nodump WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row=$result->fetchrow; $theHash{nodump}{html_value} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_maindata WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{html_value} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{curator} = $row[1];
#     $result=$dbh->prepare( "SELECT * FROM car_con_ref_paper WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     @row=$result->fetchrow; $theHash{con}{paper} = $row[1];
#     $result=$dbh->prepare( "SELECT * FROM car_con_ref_person WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     @row=$result->fetchrow; $theHash{con}{person} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_reference WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{reference} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_accession WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{accession} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_ext_maindata WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{ext}{html_value} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_ext_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{ext}{curator} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my %filter_curators_hash;
    while (my @row=$result->fetchrow) { 			# capture date for Kimberly  2006 08 15
      if ($row[1]) { my ($date) = $row[2] =~ m/^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2})/; $filter_curators_hash{$row[1]} = $date; } }
#     if (%filter_curators_hash) { my @curators = keys %filter_curators_hash; $theHash{con_text_only}{curators} = join", ", @curators; }
    if (%filter_curators_hash) { 
      foreach my $curator (sort keys %filter_curators_hash) { $theHash{con_text_only}{curators} .= "$curator ($filter_curators_hash{$curator}); "; }
      $theHash{con_text_only}{curators} =~ s/; $//; }

    $result=$dbh->prepare( "SELECT * FROM car_hum_maindata WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{hum}{html_value} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_hum_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{hum}{curator} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_hum_ref_reference WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{hum}{reference} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_hum_ref_accession WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{hum}{accession} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_hum_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter_curators_hash = ();
    while (my @row=$result->fetchrow) { 			# capture date for Kimberly  2006 08 15
      if ($row[1]) { my ($date) = $row[2] =~ m/^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2})/; $filter_curators_hash{$row[1]} = $date; } }
    if (%filter_curators_hash) { 
      foreach my $curator (sort keys %filter_curators_hash) { $theHash{hum_text_only}{curators} .= "$curator ($filter_curators_hash{$curator}); "; }
      $theHash{hum_text_only}{curators} =~ s/; $//; }
  
    foreach my $sub (@PGsubparameters) {
        # get highest row value (not by timestamp because it could have a single row edited later that's not the highest row
      $result = $dbh->prepare( "SELECT * FROM car_${sub}_maindata WHERE joinkey = '$joinkey' ORDER BY car_order DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row=$result->fetchrow; $theHash{$sub}{num_pg} = $row[1];
      if ($theHash{$sub}{num_pg}) {
        for my $i ( 1 .. $theHash{$sub}{num_pg} ) {
          $result = $dbh->prepare( "SELECT * FROM car_${sub}_maindata WHERE joinkey = '$joinkey' AND car_order = $i ORDER BY car_timestamp DESC;" );
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
          my @row=$result->fetchrow;
          $theHash{$sub}{$row[1]}{html_value} = $row[2]; 
  #         my @subtypes = qw( curator paper person );
          my @subtypes = qw( curator reference accession );	# changed boxes for carol 2005 05 12
          foreach my $subtype (@subtypes) {
            if ( ($sub ne 'seq') && ($subtype eq 'accession') ) { next; }	# skip accession if not sequence (which is the only one that has it)
            $result = $dbh->prepare( "SELECT * FROM car_${sub}_ref_$subtype WHERE joinkey = '$joinkey' AND car_order = $i ORDER BY car_timestamp DESC;" );
            $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
            my @row=$result->fetchrow;
            if ($row[2]) { $theHash{$sub}{$row[1]}{$subtype} = $row[2]; }
          } 
      } } # for my $i ( 1 .. $theHash{$sub}{num} )
    } # foreach my $sub (@PGsubparameters)
  
    &mainPage(); 
  } # else # if ($found eq '') 
} # sub query

sub getValueFromPostgres {
  my ($joinkey, $pgtable, $type, $htmltype, $subhash) = @_;
  $pgtable = 'car_' . $pgtable;
#   print "TAB $pgtable<BR>\n";
#   print "SELECT * FROM $pgtable WHERE joinkey = \'$joinkey\' ORDER BY car_timestamp DESC;<BR>\n";
  my $result = $dbh->prepare( "SELECT * FROM $pgtable WHERE joinkey = \'$joinkey\' ORDER BY car_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; 
  my $found = ' ';
  if ($row[1]) { 
    $found = $row[1]; }
  unless ($found) { $found = ' '; }
  $theHash{$type}{$htmltype} = $found;
#   print "FOUND $found<BR>\n";
} # sub getValueFromPostgres

sub loadState {		# load _001 saved data in postgres by curator
  my ($var, $curator) = &getHtmlVar($query, 'curator_name');
  my $joinkey = $curator . '_001';
  my $result = $dbh->prepare( "SELECT * FROM car_lastcurator WHERE joinkey = \'$joinkey\' ORDER BY car_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; 
  my $found = $row[1];					# curator from car_lastcurator
  if ($found eq '') { 
    print "Entry $joinkey not found, you don't have any saved data in postgres for this form.\n"; return; }
  else {
#     print "FOUND $found<BR>\n";
#     $theHash{gene}{html_value} = $joinkey; 
    $theHash{gene}{html_value} = $found; 

    my $result=$dbh->prepare( "SELECT * FROM car_con_maindata WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row=$result->fetchrow; $theHash{con}{html_value} = $row[1];	# put value in hash
    if ($row[1]) { $theHash{con}{html_mail_box} = 'checked'; }		# mark checkbox checked for form in hash
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{curator} = $row[1];
    if ($row[1]) { $theHash{con}{html_mail_box} = 'checked'; }
#     $result=$dbh->prepare( "SELECT * FROM car_con_ref_paper WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     @row=$result->fetchrow; $theHash{con}{paper} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_reference WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{reference} = $row[1];
    if ($row[1]) { $theHash{con}{html_mail_box} = 'checked'; }
#     $result=$dbh->prepare( "SELECT * FROM car_con_ref_person WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     @row=$result->fetchrow; $theHash{con}{person} = $row[1];
    $result=$dbh->prepare( "SELECT * FROM car_con_ref_accession WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{con}{accession} = $row[1];
    if ($row[1]) { $theHash{con}{html_mail_box} = 'checked'; }
    $result=$dbh->prepare( "SELECT * FROM car_ext_maindata WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{ext}{html_value} = $row[1];
    if ($row[1]) { $theHash{ext}{html_mail_box} = 'checked'; }
    $result=$dbh->prepare( "SELECT * FROM car_ext_ref_curator WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row=$result->fetchrow; $theHash{ext}{curator} = $row[1];
    if ($row[1]) { $theHash{ext}{html_mail_box} = 'checked'; }
  
    foreach my $sub (@PGsubparameters) {
        # get highest row value (not by timestamp because it could have a single row edited later that's not the highest row
      $result = $dbh->prepare( "SELECT * FROM car_${sub}_maindata WHERE joinkey = '$joinkey' ORDER BY car_order DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row=$result->fetchrow; $theHash{$sub}{num_pg} = $row[1];
      for my $i ( 1 .. $theHash{$sub}{num_pg} ) {
        $result = $dbh->prepare( "SELECT * FROM car_${sub}_maindata WHERE joinkey = '$joinkey' AND car_order = $i ORDER BY car_timestamp DESC;" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row=$result->fetchrow;
        $theHash{$sub}{$row[1]}{html_value} = $row[2]; 
        if ($row[2]) { $theHash{$sub}{$row[1]}{html_mail_box} = 'checked'; }	# mark checkbox checked for form in hash
#         my @subtypes = qw( curator paper person );
        my @subtypes = qw( curator reference accession );	# changed boxes for carol 2005 05 12
        foreach my $type (@subtypes) {
          if ( ($sub ne 'seq') && ($type eq 'accession') ) { next; }	# skip accession if not sequence (which is the only one that has it)
          $result = $dbh->prepare( "SELECT * FROM car_${sub}_ref_$type WHERE joinkey = '$joinkey' AND car_order = $i ORDER BY car_timestamp DESC;" );
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
          my @row=$result->fetchrow;
          if ($row[2]) { $theHash{$sub}{$row[1]}{$type} = $row[2]; }
          if ($row[2]) { $theHash{$sub}{$row[1]}{html_mail_box} = 'checked'; }
        } 
      } # for my $i ( 1 .. $theHash{$sub}{num} )
    } # foreach my $sub (@PGsubparameters)
  
    &mainPage(); 
  } # else # if ($found eq '')
} # sub loadState

sub saveState {		# save to postgres using curator_001 for joinkey, store wbgene in lastcurator
  &getSangerConversion(); 
  my $hidden_values = &getHtmlValuesFromForm();
  my $field = 'con';
  my $joinkey = $theHash{main}{curator_name};
  $joinkey .= '_001';
  if ($theHash{$field}{html_mail_box}) {
    my $type = 'lastcurator'; my $val = $theHash{main}{curator_name};
    my $gene = $theHash{gene}{html_value}; 
    if ($gene =~ m/^WBGene\d{8}/) { $gene = $gene; }
      else {
        if ($wbGene{$gene}) { $gene = $wbGene{$gene}; }
          else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $gene NOT in sanger list</B></FONT><BR>\n"; next; } }
    print "MAIN CUR $val<BR>\n";
    &updatePostgresFieldTables($joinkey, $type, $gene);	# joinkey curator, store gene in last curator
    $type = 'con_maindata'; $val = $theHash{$field}{html_value};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
    $type = 'con_ref_curator'; my $cur = $theHash{$field}{curator};
    &updatePostgresFieldTables($joinkey, $type, $cur);	# update postgres for all tables
#     $type = 'con_ref_paper'; $val = $theHash{$field}{paper};
    $type = 'con_ref_reference'; $val = $theHash{$field}{reference};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
#     $type = 'con_ref_person'; $val = $theHash{$field}{person};
    $type = 'con_ref_accession'; $val = $theHash{$field}{accession};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
  } # if ($theHash{$field}{html_mail_box})

  $field = 'ext';
  if ($theHash{$field}{html_mail_box}) {
    my $type = 'ext_maindata'; my $val = $theHash{$field}{html_value};
    &updatePostgresFieldTables($joinkey, $type, $val);    # update postgres for all tables
    $type = 'ext_ref_curator'; my $cur = $theHash{$field}{curator};
    &updatePostgresFieldTables($joinkey, $type, $cur);    # update postgres for all tables
  } # if ($theHash{$field}{html_mail_box})

  foreach my $sub (@PGsubparameters) {
    foreach my $i ( sort keys %{ $theHash{$sub}} ) {
      next unless ($i =~ m/^\d+$/) ;
      if ($theHash{$sub}{$i}{html_mail_box}) {	# if box was checked
        my $type = $sub . '_maindata'; my $val = $theHash{$sub}{$i}{html_value};
        &updatePostgresFieldTables($joinkey, $type, $val, $i);	# update postgres for all tables
        $type = $sub . '_ref_curator'; my $cur = $theHash{$sub}{$i}{curator};
        &updatePostgresFieldTables($joinkey, $type, $cur, $i);	# update postgres for all tables
#         $type = $sub . '_ref_paper'; $val = $theHash{$sub}{$i}{paper};
        $type = $sub . '_ref_reference'; $val = $theHash{$sub}{$i}{reference};
        &updatePostgresFieldTables($joinkey, $type, $val, $i);	# update postgres for all tables
#         $type = $sub . '_ref_person'; $val = $theHash{$sub}{$i}{person};
        if ($sub eq 'seq') {
          $type = $sub . '_ref_accession'; $val = $theHash{$sub}{$i}{accession};
          &updatePostgresFieldTables($joinkey, $type, $val, $i); }	# update postgres for all tables
      } # if ($theHash{$sub}{$i}{html_mail_box})
    } # foreach my $i ( sort keys %{ $theHash{$sub}} )
  } # foreach my $sub (@PGsubparameters)
} # sub saveState

sub write {
  my $new_or_update = shift;				# flag whether to add ``UPDATE : '' to subject line
  &getSangerConversion(); 
  my $hidden_values = &getHtmlValuesFromForm();
  my $gene = $theHash{gene}{html_value}; 
  my $joinkey = '';
  if ($gene =~ m/^WBGene\d{8}/) { $joinkey = $gene; }
    else {
      if ($wbGene{$gene}) { $joinkey = $wbGene{$gene}; }
        else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $gene NOT in sanger list</B></FONT><BR>\n"; next; } }
  &updatePostgresNoDump($joinkey, 'con_nodump', $theHash{nodump}{html_value});	# compare postgres and form values of nodump checkbox and add if different
  my $field = 'con';
  if ($theHash{$field}{html_mail_box}) {
    my $type = 'lastcurator'; my $val = $theHash{main}{curator_name};
    print "MAIN CUR $val<BR>\n";
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
    $type = 'con_maindata'; $val = $theHash{$field}{html_value};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
    $type = 'con_ref_curator'; my $cur = $theHash{$field}{curator};
    &notifyPostgresPreviousCurator($type, $cur, $val);	# email previous curator
    &updatePostgresFieldTables($joinkey, $type, $cur);	# update postgres for all tables
#     $type = 'con_ref_paper'; $val = $theHash{$field}{paper};
    $type = 'con_ref_reference'; $val = $theHash{$field}{reference};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
#     $type = 'con_ref_person'; $val = $theHash{$field}{person};
    $type = 'con_ref_accession'; $val = $theHash{$field}{accession};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables

#     $html_type = 'html_value_box_last_verified';
#     my ($var, $val) = &getHtmlVar($query, $html_type);
    $type = 'con_last_verified'; $val = $theHash{con_last_verified}{html_value};
    if ($val) {  
      &updatePostgresFieldTables($joinkey, 'con_last_verified', $val); }    # update postgres for all tables
  } # if ($theHash{$field}{html_mail_box})

  $field = 'hum';
  if ($theHash{$field}{html_mail_box}) {
    my $type = 'lastcurator'; my $val = $theHash{main}{curator_name};
    print "MAIN CUR $val<BR>\n";
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
    $type = 'hum_maindata'; $val = $theHash{$field}{html_value};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
    $type = 'hum_ref_curator'; my $cur = $theHash{$field}{curator};
    &notifyPostgresPreviousCurator($type, $cur, $val);	# email previous curator
    &updatePostgresFieldTables($joinkey, $type, $cur);	# update postgres for all tables
    $type = 'hum_ref_reference'; $val = $theHash{$field}{reference};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables
    $type = 'hum_ref_accession'; $val = $theHash{$field}{accession};
    &updatePostgresFieldTables($joinkey, $type, $val);	# update postgres for all tables

    $type = 'hum_last_verified'; $val = $theHash{hum_last_verified}{html_value};
    if ($val) {  
      &updatePostgresFieldTables($joinkey, 'hum_last_verified', $val); }    # update postgres for all tables
  } # if ($theHash{$field}{html_mail_box})

  $field = 'ext';
  if ($theHash{$field}{html_mail_box}) {
    my $type = 'ext_maindata'; my $val = $theHash{$field}{html_value};
    &updatePostgresFieldTables($joinkey, $type, $val);    # update postgres for all tables
    $type = 'ext_ref_curator'; my $cur = $theHash{$field}{curator};
    &notifyPostgresPreviousCurator($type, $cur, $val);	# email previous curator
    &updatePostgresFieldTables($joinkey, $type, $cur);    # update postgres for all tables
  } # if ($theHash{$field}{html_mail_box})
     
  foreach my $sub (@PGsubparameters) {
    foreach my $i ( sort keys %{ $theHash{$sub}} ) {
      next unless ($i =~ m/^\d+$/) ;
      if ($theHash{$sub}{$i}{html_mail_box}) {	# if box was checked
        my $type = $sub . '_maindata'; my $val = $theHash{$sub}{$i}{html_value};
        &updatePostgresFieldTables($joinkey, $type, $val, $i);	# update postgres for all tables
        $type = $sub . '_ref_curator'; my $cur = $theHash{$sub}{$i}{curator};
        &notifyPostgresPreviousCurator($type, $cur, $val, $i);	# email previous curator
        &updatePostgresFieldTables($joinkey, $type, $cur, $i);	# update postgres for all tables
#         $type = $sub . '_ref_paper'; $val = $theHash{$sub}{$i}{paper};
        $type = $sub . '_ref_reference'; $val = $theHash{$sub}{$i}{reference};
        &updatePostgresFieldTables($joinkey, $type, $val, $i);	# update postgres for all tables
#         $type = $sub . '_ref_person'; $val = $theHash{$sub}{$i}{person};
        if ($sub eq 'seq') {
          $type = $sub . '_ref_accession'; $val = $theHash{$sub}{$i}{accession};
          &updatePostgresFieldTables($joinkey, $type, $val, $i); }	# update postgres for all tables
      } # if ($theHash{$sub}{$i}{html_mail_box})
    } # foreach my $i ( sort keys %{ $theHash{$sub}} )
  } # foreach my $sub (@PGsubparameters)
#   &acePreview();
  my $curator_href = $curator; if ($curator_href =~ m/\s+/) { $curator_href =~ s/\s+/\+/g; }
  print "Click <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_checkout.cgi?curator_name=$curator_href&action=Search+Genes+%21&html_value_search_list=$joinkey\">here</A> for the concise description checkout form to check in / grafitti this paper<BR>\n"; 						# link out to checkout form  2005 11 28
  print "Click <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_new.cgi?action=Curator+%21&curator_name=$curator_href\">here</A> to go back to the curation form.<BR>\n";
  print "WRITE $new_or_update<BR>\n";
} # sub write

sub notifyPostgresPreviousCurator {
    # check the curator drop down menus and compare them to the previous entry (latest), if they
    # differ, then email the previous curator that someone else has written to that block of tables 2004 05 18
  my ($table, $cur, $val, $i) = @_;
  my ($changed_table) = $table =~ m/^(.*?)_/; 
  $changed_table = $aceTrans{$changed_table};
  if ($i) { $changed_table .= " $i"; }
  $table = 'car_' . $table;
  my ($var, $curator) = &getHtmlVar($query, 'curator_name');
  my $joinkey = $theHash{gene}{html_value}; 
  if ($cur ne ' ') { 					# if there's a curator
    my $result = $dbh->prepare( "SELECT $table FROM $table WHERE joinkey = \'$joinkey\' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     print "SELECT $table FROM $table WHERE joinkey = \'$joinkey\' ORDER BY car_timestamp DESC;<BR>\n"; 
    my @row = $result->fetchrow;
    if ($row[0]) {					# if there's a previous curator
							# doesn't matter if curators don't match
#       if ($row[0] ne $cur) { 				# if curators don't match
        my $old_curator;
        if ($row[0] =~ m/Carol/) { $old_curator = 'carol'; }
        elsif ($row[0] =~ m/Erich/) { $old_curator = 'erich'; }
        elsif ($row[0] =~ m/Gary/) { $old_curator = 'gary'; }
        elsif ($row[0] =~ m/Ranjana/) { $old_curator = 'ranjana'; }
        elsif ($row[0] =~ m/Snehalata/) { $old_curator = 'snehalata'; }
        elsif ($row[0] =~ m/Karen/) { $old_curator = 'karen'; }
        elsif ($row[0] =~ m/Kimberly/) { $old_curator = 'kimberly'; }
        elsif ($row[0] =~ m/Paul/) { $old_curator = 'paul'; }
        elsif ($row[0] =~ m/Igor/) { $old_curator = 'igor'; }
        elsif ($row[0] =~ m/Raymond/) { $old_curator = 'raymond'; }
        elsif ($row[0] =~ m/Andrei/) { $old_curator = 'andrei'; }
        elsif ($row[0] =~ m/Wen/) { $old_curator = 'wen'; }
        elsif ($row[0] =~ m/Juancarlos/) { $old_curator = 'azurebrd'; }
        else { $old_curator = 'previous_curator_not_found'; }

        if (($old_curator eq 'carol') || ($old_curator eq 'erich') || ($old_curator eq 'andrei') || ($old_curator eq 'igor')) { 
            print "$old_curator has retired, no email being sent<br />\n"; }
          else {
#             my $user = $cur;
            my $user = $curator;				# want curator that logged on, not curator in block's drop down menu
            my $email = $emails{$old_curator};
            my $subject = "$user has updated $joinkey ($wbGeneBack{$joinkey}) entry in $changed_table in the Concise Description Form.";
            my $body = $val;
            &mailer($user, $email, $subject, $body);
            print "<FONT COLOR='blue'>EMAIL OLD $row[0] NEW $cur $table $changed_table</FONT><BR>\n"; }
#       } # if ($row[0] ne $cur)
    } # if ($row[0])
  } # if ($cur ne ' ')  
} # sub notifyPostgresPreviousCurator

sub updatePostgresNoDump {
  my ($joinkey, $table, $form_val) = @_; my $pg_val = '';
  my $result = $dbh->prepare( "SELECT * FROM car_$table WHERE joinkey = '$joinkey' ORDER BY car_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; if ($row[1]) { $pg_val = $row[1]; }
  if ($pg_val) { 
      if ($form_val) { unless ($pg_val eq $form_val) { &updatePostgresFieldTables($joinkey, $table, $form_val); } }
        else { &updatePostgresFieldTables($joinkey, $table, $form_val); } }
    else {
      if ($form_val) { &updatePostgresFieldTables($joinkey, $table, $form_val); } }
} # sub updatePostgresNoDump

sub updatePostgresFieldTables {
  my ($joinkey, $table, $val, $i) = @_;
  $table = 'car_' . $table;
  if ( ($val ne '') && ($val ne ' ') ) { 
    if ($val =~ m/\'/) { $val =~ s/\'/''/g; }
    if ($i) { 
      my $result = $dbh->do( "INSERT INTO $table VALUES (\'$joinkey\', $i, \'$val\');" );
      print "<FONT COLOR='green'>INSERT INTO $table VALUES (\'$joinkey\', $i, \'$val\');</FONT><BR>"; } 
    else { 
      my $result = $dbh->do( "INSERT INTO $table VALUES (\'$joinkey\', \'$val\');" );
      print "<FONT COLOR='green'>INSERT INTO $table VALUES (\'$joinkey\', \'$val\');</FONT><BR>"; } }
  else { 
    if ($i) {
      my $result = $dbh->do( "INSERT INTO $table VALUES (\'$joinkey\', $i, NULL);" );
      print "<FONT COLOR='green'>INSERT INTO $table VALUES (\'$joinkey\', $i, NULL);</FONT><BR>"; } 
    else {
      my $result = $dbh->do( "INSERT INTO $table VALUES (\'$joinkey\', NULL);" );
      print "<FONT COLOR='green'>INSERT INTO $table VALUES (\'$joinkey\', NULL);</FONT><BR>"; } }
} # sub updatePostgresFieldTables

sub findIfPgEntry {
  my $result = $dbh->prepare( "SELECT * FROM car_lastcurator WHERE joinkey = '$theHash{gene}{html_value}';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my $found;                            # curator from cur_curator
  while (my @row = $result->fetchrow) { $found = $row[1]; if ($found eq '') { $found = ' '; } }
  return $found;
} # sub findIfPgEntry

sub preview {
  &getSangerConversion(); 
  my $hidden_values = &getHtmlValuesFromForm();
  my $errorRequire = &checkRequired();
  my $found = &findIfPgEntry('curator');              # query pg curator table for pubID
  &acePreview();
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_new.cgi\">\n";
  print "$hidden_values<BR>\n";
  if ($found) { print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update !\"><P>\n"; }
    else { print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"New Entry !\"><P>\n"; }
  print "</FORM>\n";
  print "END<br>";
} # sub preview

sub acePreview {
  my %curators;		# anyone who has curated a field gets a mention in concise description person evidence
  my %papers;		# any paper in a curated a field gets a mention in concise description paper evidence

print "ACE PREVIEW<BR>\n";

  my $gene = $theHash{gene}{html_value};
  my $joinkey = '';
  if ($gene =~ m/^WBGene\d{8}/) { $joinkey = $gene; }
    else {
      if ($wbGene{$gene}) { $joinkey = $wbGene{$gene}; } }
  if ($joinkey) {
    %curators = ();
    %papers = ();
    &readConversions();
#     my ($categories) = &getCategories($gene); 
    my ($categories, $ace_delete) = &getCategories($gene); 
    &getConcise($joinkey, $ace_delete);
    print $categories; }
  else {
    print STDERR "$gene is not approved by Sanger\n"; }
} # sub acePreview

sub convertPerson {
  my ($found) = shift;
  $found =~ s/\s+/ /g; $found =~ s/^\s//g; $found =~ s/\s$//g;
  if ($found =~ m/WBPerson\d+/) { return $found; }
  elsif ($found =~ m/Juancarlos/) { $found = 'WBPerson1823'; }
  elsif ($found =~ m/Carol/) { $found = 'WBPerson48'; }
  elsif ($found =~ m/Ranjana/) { $found = 'WBPerson324'; }
  elsif ($found =~ m/Snehalata/) { $found = 'WBPerson12884'; }
  elsif ($found =~ m/Karen/) { $found = 'WBPerson712'; }
  elsif ($found =~ m/Kimberly/) { $found = 'WBPerson1843'; }
  elsif ($found =~ m/Erich/) { $found = 'WBPerson567'; }
  elsif ($found =~ m/Paul/) { $found = 'WBPerson625'; }
  elsif ($found =~ m/Igor/) { $found = 'WBPerson22'; }
  elsif ($found =~ m/Raymond/) { $found = 'WBPerson363'; }
  elsif ($found =~ m/Andrei/) { $found = 'WBPerson480'; }
  elsif ($found =~ m/Wen/) { $found = 'WBPerson101'; }
  elsif ($found =~ m/James Kramer/) { $found = 'WBPerson345'; } 
  elsif ($found =~ m/Massimo Hilliard/) { $found = 'WBPerson258'; } 
  elsif ($found =~ m/Verena Gobel/) { $found = 'WBPerson204'; } 
  elsif ($found =~ m/Graham Goodwin/) { $found = 'WBPerson2104'; }
  elsif ($found =~ m/Thomas Burglin/) { $found = 'WBPerson83'; }  
  elsif ($found =~ m/Thomas Blumenthal/) { $found = 'WBPerson71'; }  
  elsif ($found =~ m/Jonathan Hodgkin/) { $found = 'WBPerson261'; } 
  elsif ($found =~ m/Marie Causey/) { $found = 'WBPerson638'; } 
  elsif ($found =~ m/Mark Edgley/) { $found = 'WBPerson154'; } 
  elsif ($found =~ m/Alison Woollard/) { $found = 'WBPerson699'; } 
  elsif ($found =~ m/Ian Hope/) { $found = 'WBPerson266'; } 
  elsif ($found =~ m/Geraldine Seydoux/) { $found = 'WBPerson575'; } 
  elsif ($found =~ m/Marta Kostrouchova/) { $found = 'WBPerson344'; } 
  elsif ($found =~ m/Malcolm Kennedy/) { $found = 'WBPerson2522'; }
  elsif ($found =~ m/Berndt Mueller/) { $found = 'WBPerson1874'; }
  elsif ($found =~ m/Steven Kleene/) { $found = 'WBPerson327'; } 
  elsif ($found =~ m/Michael Koelle/) { $found = 'WBPerson330'; } 
  elsif ($found =~ m/Giovanni Lesa/) { $found = 'WBPerson365'; } 
  elsif ($found =~ m/Benjamin Leung/) { $found = 'WBPerson366'; } 
  elsif ($found =~ m/Robyn Lints/) { $found = 'WBPerson377'; } 
  elsif ($found =~ m/Leo Liu/) { $found = 'WBPerson381'; } 
  elsif ($found =~ m/Margaret MacMorris/) { $found = 'WBPerson395'; } 
  elsif ($found =~ m/Jacob Varkey/) { $found = 'WBPerson669'; } 
  elsif ($found =~ m/Kim McKim/) { $found = 'WBPerson1264'; } 
  elsif ($found =~ m/Bob Johnsen/) { $found = 'WBPerson1119'; } 
  elsif ($found =~ m/Gerhard Schad/) { $found = 'WBPerson553'; } 
  elsif ($found =~ m/David Baillie/) { $found = 'WBPerson36'; } 
  else { print "<FONT COLOR='red'>ERROR : $found is not a valid curator.</FONT><BR>\n"; }
  $aceCurators{$found}++;	# irrelevant when creating human readable dump
  return $found;
} # sub convertPerson

sub clearReferenceTrail {
  my $cleaning = shift; 
  if ($cleaning =~ m/\s$/) { $cleaning =~ s/\s$//g; }
  if ($cleaning =~ m/\.$/) { $cleaning =~ s/\.$//g; }
  if ($cleaning =~ m/,$/) { $cleaning =~ s/,$//g; }
  return $cleaning;
} # sub clearReferenceTrail

sub getCategories {
  my $gene = shift;
  my $categories = '';

  my $ace_delete = '';
  my %delHash = ();

  foreach my $sub (@PGsubparameters) {
    foreach my $i ( sort keys %{ $theHash{$sub}} ) {
      next unless ($i =~ m/^\d+$/) ;
#       print "$sub $i<BR>\n";
#       if ($theHash{$sub}{$i}{html_value}) { print "SUB $sub I $i MAIN $theHash{$sub}{$i}{html_value}<BR>\n"; }
#       if ($theHash{$sub}{$i}{curator}) { print "SUB $sub I $i CUR $theHash{$sub}{$i}{curator}<BR>\n"; }
#       if ($theHash{$sub}{$i}{paper}) { print "SUB $sub I $i PAP $theHash{$sub}{$i}{paper}<BR>\n"; }
#       if ($theHash{$sub}{$i}{person}) { print "SUB $sub I $i PER $theHash{$sub}{$i}{person}<BR>\n"; }

      if ($theHash{$sub}{$i}{curator}) { 
        my $curator = &convertPerson($theHash{$sub}{$i}{curator});
#         print "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPerson_evidence\t\"$curator\"<BR>\n"; 
        $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPerson_evidence\t\"$curator\"<BR>\n"; }
      if ($theHash{$sub}{$i}{reference}) { 
        my @reference = split/, /, $theHash{$sub}{$i}{reference};
        foreach my $reference (@reference) {
          $reference = &clearReferenceTrail($reference);
          if ($reference =~ m/WBPerson/) {
            my $person = &convertPerson($reference);
            my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPerson_evidence\t\"$person\"<BR>\n"; }
          elsif ( ($reference =~ m/pmid.*_.*/) || ($reference =~ m/cgc.*_.*/) ) {
            my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tGene_regulation_evidence\t\"$reference\"<BR>\n"; }
          elsif ( $reference =~ m/^GO:/ ) {
            my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tGO_term_evidence\t\"$reference\"<BR>\n"; }
          elsif ( $reference =~ m/^Expr/ ) {
            my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tExpr_pattern_evidence\t\"$reference\"<BR>\n"; }
          elsif ( ($reference =~ m/^Aff_/) || ($reference =~ m/^SMD_/) ) {
            my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tMicroarray_results_evidence\t\"$reference\"<BR>\n"; }
          elsif ( $reference =~ m/^WBRNAi/ ) {
            my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tRNAi_evidence\t\"$reference\"<BR>\n"; }
          else {
            if ($reference =~ m/^WB[Pp]aper/) {
              if ($reference =~ m/WBpaper/) { $reference =~ s/WBpaper/WBPaper/g; }	# treat this case for Erich  2007 06 04
              my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
              $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$reference\"<BR>\n"; }
            elsif ($convertToWBPaper{$reference}) {                     # convert to WBPaper or print ERROR
              my $wbpaper = $convertToWBPaper{$reference};
              my $del_line = "-D $aceTrans{$sub}"; $delHash{$del_line}++;
              $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$wbpaper\"<BR>\n"; }
            else { print "// <FONT COLOR='red'>ERROR No conversion for $reference : $gene</FONT><BR>\n"; }
          }
        } # foreach my $reference (@reference)
      } # if ($theHash{$sub}{$i}{reference}) 

      if ($sub eq 'seq') {
        if ($theHash{$sub}{$i}{accession}) { 
          my @accession = split/, /, $theHash{$sub}{$i}{accession};
          foreach my $accession (@accession) {
            $categories .= "$aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tAccession_evidence\t\"$accession\"<BR>\n"; } } }
# replace paper and person with reference and accession for carol  2005 05 12
#       if ($theHash{$sub}{$i}{paper}) { 
#         my @papers = split/, /, $theHash{$sub}{$i}{paper};
#         foreach my $paper (@papers) {
#           $paper =~ s/\.$//g;				# take out extra period at the end of paper
#           $acePapers{$paper}++;
#           if ($paper =~ m/WBPaper/) {
#             $categories .= "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$paper\"<BR>\n"; } 
#           elsif ($convertToWBPaper{$paper}) {
#             $categories .= "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$convertToWBPaper{$paper}\" // $paper<BR>\n"; }
#           else { print "// ERROR NO Convertion for $paper\n"; }
# #           print "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$paper\"<BR>\n"; 
# #           $categories .= "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$paper\"<BR>\n"; 
#         } }
#       if ($theHash{$sub}{$i}{person}) { 
#         my @persons = split/, /, $theHash{$sub}{$i}{person};
#         foreach my $wbperson (@persons) {
#           my $person = &convertPerson($wbperson);
# #           print "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPerson_evidence\t\"$person\"<BR>\n"; 
#           $categories .= "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPerson_evidence\t\"$person\"<BR>\n"; } }
    } # foreach my $i (@{ sort keys %{ $theHash{$sub}} })
  } # foreach my $sub (@PGsubparameters)
  $categories .= "\n";
#   return ($categories);

  foreach my $line (sort keys %delHash) { $ace_delete .= $line . "<BR>\n"; }
  return ($categories, $ace_delete);
} # sub getCategories

sub getConcise {
  my ($gene, $other_ace_delete) = @_;

  my $ace_entry = '';
  my $ace_delete = '';
  my $ace_provisional = '';

  unless ($theHash{con}{html_value}) { print "// <FONT COLOR='red'>ERROR : NO Concise Description for $gene</FONT><BR>\n"; return 0; }
#     $theHash{con}{html_value} = $val;

  my $concise = $theHash{con}{html_value};

  $ace_entry .= "Gene : \"$gene\"<BR>\n";
  $ace_entry .= "Concise_description\t\"$concise\"<BR>\n";
  $ace_delete .= "Gene : \"$gene\"<BR>\n";
  $ace_delete .= "-D Concise_description<BR>\n";

  foreach my $input_field ( sort keys %{ $theHash{evidences} } ) {	# append to print each evidence
    foreach my $evidence_type ( sort keys %{ $theHash{evidences}{$input_field} } ) {
      foreach my $evidence ( sort keys %{ $theHash{evidences}{$input_field}{$evidence_type} } ) {
        unless ($evidence eq 'NODATA') {
          $ace_entry .= "Provisional_description\t\"$concise\"\t$evidence_type\t\"$evidence\"<BR>\n";
          $ace_provisional .= "Provisional_description\t\"$concise\"\t$evidence_type\t\"$evidence\"<BR>\n";
        } } } }

  if ($theHash{extra}) {
    foreach my $line (@{ $theHash{extra} }) {
      if ($line) {                              # only print a line if there's data (don't print if used to be and then replaced with blank)
        $ace_entry .= "Provisional_description\t\"$line.\"<BR>\n";
        $ace_provisional .= "Provisional_description\t\"$line.\"<BR>\n";
      } } }

  if ($theHash{hum}{html_value}) { $ace_entry .= "Human_disease_relevance\t\"$theHash{hum}{html_value}\"<br />\n"; }

  if ($ace_provisional) { $ace_delete .= "-D Provisional_description<BR>\n"; }
  if ($other_ace_delete) { $ace_delete .= $other_ace_delete; }
  print "<P>\n$ace_delete<P>\n$ace_entry";


#   my $field = 'con';
#   my $con = $theHash{$field}{html_value};
#   print "ACE : Gene : \"$wbgene\"<BR>\n"; 
#   print "ACE : Concise_description\t\"$con\"<BR>\n"; 
#   my $curator = &convertPerson($theHash{$field}{curator});
#   foreach my $curator (sort keys %aceCurators) { 
#     if ($curator =~ /\S/) { 
#       print "ACE : Provisional_description\t\"$con\"\tPerson_evidence\t\"$curator\"<BR>\n"; } }

# FIX THIS needs to code for non-papers
#   my $subtype = 'ref1';
#   my @papers = split/, /, $theHash{$field}{$subtype};
#   foreach my $paper (@papers) { $acePapers{$paper}++; }
#   foreach my $paper (sort keys %acePapers) { 
#     if ($paper =~ /\S/) { 
#       $paper =~ s/\.$//g;				# take out extra period at the end of paper
#       if ($paper =~ m/WBPaper/) {
#         print "ACE : Provisional_description\t\"$con\"\tPaper_evidence\t\"$paper\"<BR>\n"; }
#       elsif ($convertToWBPaper{$paper}) {
#         print "ACE : Provisional_description\t\"$con\"\tPaper_evidence\t\"$convertToWBPaper{$paper}\" // $paper<BR>\n"; }
#       else { print "// ERROR NO Convertion for $paper\n"; }
# #           print "ACE : $aceTrans{$sub}\t\"$theHash{$sub}{$i}{html_value}\"\tPaper_evidence\t\"$paper\"<BR>\n"; 
# #       print "ACE : Provisional_description\t\"$con\"\tPaper_evidence\t\"$paper\"<BR>\n"; 
#   } }
} # sub getConcise

sub checkRequired {
  1;							# haven't implemented this
} # sub checkRequired

sub getHtmlValuesFromForm {
  &readConversions();
  my $hidden_values = '';
  my $html_type = 'html_value_gene';
  my $field = 'gene';
  my ($var, $val) = &getHtmlVar($query, $html_type);
  if ($val) { 			# if no gene entered, error
    if ($val =~ m/^\s+/) { $val =~ s/^\s+//g; }
    if ($val =~ m/\s+$/) { $val =~ s/\s+$//g; }
    my $joinkey;
    if ($val =~ m/^WBGene\d{8}/) { $joinkey = $val; }
      else {
        if ($wbGene{$val}) { $joinkey = $wbGene{$val}; }
          else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $val NOT in sanger list</B></FONT><BR>\n"; next; } }
    print "GENE $val IS $joinkey<BR>\n";
    $theHash{$field}{html_value} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_gene\" VALUE=\"$val\">\n"; }
  else {
    print "<FONT SIZE=+2 COLOR='red'><B>ERROR : Need to enter a Gene</B></FONT><BR>\n";
    return; }

  ($var, $curator) = &getHtmlVar($query, 'curator_name');
  $theHash{main}{curator_name} = $curator;
  $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$curator\">\n"; 
  ($var, my $nodump) = &getHtmlVar($query, 'html_value_nodump');	# get nodump value
  $theHash{nodump}{html_value} = $nodump;
  $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_nodump\" VALUE=\"$nodump\">\n"; 

  $html_type = 'html_value_box_con';
  ($var, $val) = &getHtmlVar($query, $html_type);
  if ($val) { 				# if box checked
    $theHash{con}{html_mail_box} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "There is Concise data<BR>\n"; 
    $html_type = 'html_value_con_maindata';
    my ($var, $val) = &getHtmlVar($query, $html_type);
    $theHash{con}{html_value} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
    $html_type = 'html_value_box_con_last_verified';
    ($var, $val) = &getHtmlVar($query, $html_type);
    $theHash{con_last_verified}{html_value} = $val;  unless ($val) { $val = ''; }
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "Concise Description $val<BR>\n";
#     my @subtypes = qw( curator paper person );
    my @subtypes = qw( curator reference accession );	# changed boxes for carol 2005 05 12
    foreach my $subtype ( @subtypes ) {
      $html_type = 'html_value_con_' . $subtype;
      ($var, $val) = &getHtmlVar($query, $html_type);
      $theHash{con}{$subtype} = $val;  unless ($val) { $val = ''; }
#       print "CON $subtype $val<BR>\n"; 
      $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n"; 
      if ($subtype eq 'reference') {			# added $theHash{evidence} to work like concise description dumper.  2005 06 30
        my @references = split/, /, $val;
        foreach my $reference (@references) {
          if ($reference =~ m/\s$/) { $reference =~ s/\s$//g; }
          if ($reference =~ m/\.$/) { $reference =~ s/\.$//g; }
          if ($reference =~ m/,$/) { $reference =~ s/,$//g; }
          if ($reference =~ m/WBPerson/) {
            my $person = &convertPerson($reference);
            $theHash{evidences}{reference}{Person_evidence}{$person}++; }
          elsif ( ($reference =~ m/pmid.*_.*/) || ($reference =~ m/cgc.*_.*/) ) {
            $theHash{evidences}{reference}{Gene_regulation_evidence}{$reference}++; }
          elsif ( $reference =~ m/^GO:/ ) {
            $theHash{evidences}{reference}{GO_term_evidence}{$reference}++; }
          elsif ( $reference =~ m/^Expr/ ) {
            $theHash{evidences}{reference}{Expr_pattern_evidence}{$reference}++; }
          elsif ( ($reference =~ m/^Aff_/) || ($reference =~ m/^SMD_/) ) {
            $theHash{evidences}{reference}{Microarray_results_evidence}{$reference}++; }
          elsif ( $reference =~ m/^WBRNAi/ ) {
            $theHash{evidences}{reference}{RNAi_evidence}{$reference}++; }
          else {
            if ($reference =~ m/^WBPaper/) {
              $theHash{evidences}{reference}{Paper_evidence}{$reference}++; }
            elsif ($convertToWBPaper{$reference}) {                       # convert to WBPaper or print ERROR
              my $wbpaper = $convertToWBPaper{$reference};
              $theHash{evidences}{reference}{Paper_evidence}{$wbpaper}++; }
            else { print "// <FONT COLOR='red'>ERROR No conversion for $reference</FONT><BR>\n"; }
          }
        } # foreach my $reference (@references)
      } # if ($subtype eq 'reference')
    } # foreach my $subtype ( @subtypes )
  } # if ($val)

  $html_type = 'html_value_box_hum';
  ($var, $val) = &getHtmlVar($query, $html_type);
  if ($val) { 				# if box checked
    $theHash{hum}{html_mail_box} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "There is Concise data<BR>\n"; 
    $html_type = 'html_value_hum_maindata';
    my ($var, $val) = &getHtmlVar($query, $html_type);
    $theHash{hum}{html_value} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
    $html_type = 'html_value_box_hum_last_verified';
    ($var, $val) = &getHtmlVar($query, $html_type);
    $theHash{hum_last_verified}{html_value} = $val;  unless ($val) { $val = ''; }
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "Concise Description $val<BR>\n";
#     my @subtypes = qw( curator paper person );
    my @subtypes = qw( curator reference accession );	# changed boxes for carol 2005 05 12
    foreach my $subtype ( @subtypes ) {
      $html_type = 'html_value_hum_' . $subtype;
      ($var, $val) = &getHtmlVar($query, $html_type);
      $theHash{hum}{$subtype} = $val;  unless ($val) { $val = ''; }
#       print "CON $subtype $val<BR>\n"; 
      $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n"; 
      if ($subtype eq 'reference') {
        my @references = split/, /, $val;
        foreach my $reference (@references) {
          if ($reference =~ m/\s$/) { $reference =~ s/\s$//g; }
          if ($reference =~ m/\.$/) { $reference =~ s/\.$//g; }
          if ($reference =~ m/,$/) { $reference =~ s/,$//g; }
          if ($reference =~ m/WBPerson/) {
            my $person = &convertPerson($reference);
            $theHash{evidences}{reference}{Person_evidence}{$person}++; }
          elsif ( ($reference =~ m/pmid.*_.*/) || ($reference =~ m/cgc.*_.*/) ) {
            $theHash{evidences}{reference}{Gene_regulation_evidence}{$reference}++; }
          elsif ( $reference =~ m/^GO:/ ) {
            $theHash{evidences}{reference}{GO_term_evidence}{$reference}++; }
          elsif ( $reference =~ m/^Expr/ ) {
            $theHash{evidences}{reference}{Expr_pattern_evidence}{$reference}++; }
          elsif ( ($reference =~ m/^Aff_/) || ($reference =~ m/^SMD_/) ) {
            $theHash{evidences}{reference}{Microarray_results_evidence}{$reference}++; }
          elsif ( $reference =~ m/^WBRNAi/ ) {
            $theHash{evidences}{reference}{RNAi_evidence}{$reference}++; }
          else {
            if ($reference =~ m/^WBPaper/) {
              $theHash{evidences}{reference}{Paper_evidence}{$reference}++; }
            elsif ($convertToWBPaper{$reference}) {                       # convert to WBPaper or print ERROR
              my $wbpaper = $convertToWBPaper{$reference};
              $theHash{evidences}{reference}{Paper_evidence}{$wbpaper}++; }
            else { print "// <FONT COLOR='red'>ERROR No conversion for $reference</FONT><BR>\n"; }
          }
        } # foreach my $reference (@references)
      } # if ($subtype eq 'reference')
    } # foreach my $subtype ( @subtypes )
  } # if ($val)

    # deal with new (big box for Erich) second sentence and extra sentences for provisional description
  $html_type = 'html_value_box_ext';
  ($var, $val) = &getHtmlVar($query, $html_type);
  if ($val) { 				# if box checked
    $theHash{ext}{html_mail_box} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "There is Extra Provisional data<BR>\n"; 
    $html_type = 'html_value_ext_maindata';
    my ($var, $val) = &getHtmlVar($query, $html_type);
    $theHash{ext}{html_value} = $val;
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "Extra Provisional Description $val<BR>\n";
    $html_type = 'html_value_ext_curator';
    ($var, $val) = &getHtmlVar($query, $html_type);
    $theHash{ext}{curator} = $val;
#     print "EXT curator $val<BR>\n";
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
  } # if ($val) 

  foreach my $sub (@PGsubparameters) {
    my ($var, $number) = &getHtmlVar($query, "${sub}_number"); unless ($number) { $number = 0; }
    $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"${sub}_number\" VALUE=\"$number\">\n";
    for my $i ( 1 .. $number) {
      my $html_type = "html_value_box_$sub$i";
      ($var, $val) = &getHtmlVar($query, $html_type);
# print "GOT sub $sub I $i VAR $var VAL $val<BR>\n";
      if ($val) {				# if box checked
        $theHash{$sub}{$i}{html_mail_box} = $val;
        $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#         print "$sub $i value checked<BR>\n";
        $html_type = "html_value_$sub$i";
        ($var, $val) = &getHtmlVar($query, $html_type);
        $theHash{$sub}{$i}{html_value} = $val;
        $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#         print "$html_type mainvalue $i $val<BR>\n";

#         my @subtypes = qw( curator paper person );
        my @subtypes = qw( curator reference accession );	# changed boxes for carol 2005 05 12
        foreach my $subtype (@subtypes) {    
          if ( ($sub ne 'seq') && ($subtype eq 'accession') ) { next; }	# skip accession if not sequence (which is the only one that has it)
          $html_type = "html_value_$sub${i}_$subtype";
          ($var, $val) = &getHtmlVar($query, $html_type);
          $theHash{$sub}{$i}{$subtype} = $val;
          unless ($val) { $val = ' '; }
          $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#           print "$html_type $i $val<BR>\n";
        } # foreach my $subtype (@subtypes)
      } # if ($val)
    } # for my $i ( 1 .. $number)
  } # foreach my $sub (@PGsubparameters)
  return $hidden_values;
} # sub getHtmlValuesFromForm

sub readable {			# dump human readable (old longtext .ace version)
  my %genes;
  &getSangerConversion(); 
  &readConversions();
  print "This will take about 30 seconds.<BR>\n";
  my $outfile = '/home/postgres/public_html/cgi-bin/data/concise_readable_dump.ace';
  open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
  my $result = $dbh->prepare( "SELECT * FROM car_lastcurator WHERE joinkey ~ 'WBGene' AND joinkey != 'WBGene00000000' ORDER BY car_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    # don't include test entry
  while ( my @row = $result->fetchrow ) { $genes{$row[0]}++; }
  foreach my $gene (sort keys %genes) {
    if ($gene !~ m/^WBGene\d{8}/) {
      if ($wbGene{$gene}) {
        $gene = $wbGene{$gene}; }
      else {
        print STDERR "$gene is not approved by Sanger\n"; next; }
    } # if ($gene !~ m/^WBGene\d{8}/)
    print OUT "Gene : \"$gene\"";
    if ($wbGeneBack{$gene}) { print OUT '    // ' .  $wbGeneBack{$gene}; }
    print OUT "\n";
    $result = $dbh->prepare( "SELECT * FROM car_con_ref_curator WHERE joinkey = '$gene';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my %curators = ();					# filter multiple entries of curator
    while ( my @row = $result->fetchrow ) { $curators{$row[1]}++; }
    foreach my $curator (sort keys %curators) {		# make sure there are no blank curators
      if ($curator) { 
        my $wb_person = &convertPerson($curator);
        print OUT "Provisional_description \"$gene\" Person_evidence \"$wb_person\"\t\/\/ $curator\n"; } }

# No longer want old tables in readable dump (Erich saving me trouble of writing
# the ref_reference and ref_accession dump here)  2005 05 18
#     $result = $dbh->prepare( "SELECT * FROM car_con_ref_person WHERE joinkey = '$gene';" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     my %persons = ();					# filter multiple entries of curator
#     while ( my @row = $result->fetchrow ) { $persons{$row[1]}++; }
#     foreach my $person (sort keys %persons) {		# make sure there are no blank persons
#       if ($person) { 
#         my $wb_person = &convertPerson($person);
#         print OUT "Provisional_description \"$gene\" Person_evidence \"$wb_person\"\t\/\/ $person\n"; } }
#     $result = $dbh->prepare( "SELECT * FROM car_con_ref_paper WHERE joinkey = '$gene' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     my @row = $result->fetchrow; 			# get latest entry only
#     if ($row[1]) {
#       my @papers = split/, /, $row[1];
#       foreach my $paper (@papers) { 
#         $paper =~ s/\.$//g;				# take out extra period at the end of paper
#         if ($paper =~ m/WBPaper/) {
#           print OUT "Provisional_description \"$gene\" Paper_evidence \"$paper\"\n"; }
#         elsif ($convertToWBPaper{$paper}) {
#           print OUT "Provisional_description \"$gene\" Paper_evidence \"$convertToWBPaper{$paper}\"  // $paper\n"; }
#         else { print "// ERROR NO Convertion for $paper\n"; }
# #         print OUT "Provisional_description \"$gene\" Paper_evidence \"\[$paper\]\"\n"; 
#     } }

    my $long_line = '';
    $result = $dbh->prepare( "SELECT * FROM car_con_maindata WHERE joinkey = '$gene' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow; 
    if ($row[1]) { 
      if ($row[1] =~ m/\s+$/) { $row[1] =~ s/\s+$//g; }	# WBGene00006719 has extra stuff at the end that makes the dump fail
      $long_line .= $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM car_ext_maindata WHERE joinkey = '$gene' ORDER BY car_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row = $result->fetchrow; 
    if ($row[1]) { 
      if ($row[1] =~ m/\s+$/) { $row[1] =~ s/\s+$//g; }
      $long_line .= " $row[1]"; }
    if ($long_line) {
      $long_line =~ s// /g; $long_line =~ s/\n/ /g; $long_line =~ s/\s+/ /g;
      print OUT "\nLongText : \"$gene\"\n\n";
      while ($long_line =~ m/.{80}/) {
        if ($long_line =~ m/^\s*(\S.{0,78}\S)\s(.*)$/) {
          print OUT "$1\n";  
          $long_line = $2; }
      } # while ($long_line)
      print OUT "$long_line\n";
      print OUT "\n***LongTextEnd***\n";
    } # if ($row[1])
    print OUT "\n\n";					# divider
  } # foreach my $gene (sort keys %genes)
  close (OUT) or die "Cannot close $outfile : $!";
  print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_readable_dump.ace>Concise Human Readable Dump</A><BR>\n";
} # sub readable

sub dump {			# dump .ace file for citace upload
  print "This takes a long time, please wait around 1 minute for the link to show below.<BR>\n";
  `/home/postgres/work/citace_upload/concise/wrapper.pl`;
#   `/home/postgres/work/citace_upload/concise/get_concise_to_ace_new_evidence_fields.pl > /home/postgres/public_html/cgi-bin/data/concise_dump_new.ace`;
  print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_dump_new.ace>Concise Dump</A><BR>\n";
#   print "This takes a long time, please wait around 3 minutes for the link to show below.<BR>\n";
#   `/home/postgres/work/citace_upload/concise/get_concise_to_ace.pl > /home/postgres/public_html/cgi-bin/data/concise_dump.ace`;
#   print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_dump.ace>Concise Dump</A><BR>\n";
#   my $outfile = '/home/postgres/public_html/cgi-bin/data/concise_dump.ace';
#   open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
#   close (OUT) or die "Cannot close $outfile : $!";
} # sub dump

sub displayOneDataFromKey {
  my $two = shift;
  print "TWO $two<BR>\n";
}

sub readConversions {
#   my $u = "http://tazendra.caltech.edu/~acedb/paper2wbpaper.cgi";
  my $u = "http://tazendra.caltech.edu/~postgres/cgi-bin/wpa_xref_backwards.cgi";
  my $ua = LWP::UserAgent->new(timeout => 30); #instantiates a new user agent
  my $request = HTTP::Request->new(GET => $u); #grabs url
  my $response = $ua->request($request);       #checks url, dies if not valid.
  die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
  my @tmp = split /\n/, $response->content;    #splits by line
  foreach (@tmp) {
    if ($_ =~m/^(.*?)\t(.*?)$/) {
      $convertToWBPaper{$1} = $2; } }
} # sub readConversions


sub mainPage {
  &printHtmlFormStart();
  my ($var, $curator) = &getHtmlVar($query, 'curator_name');
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$curator\">\n"; 
  print "CURATOR : $curator<BR>\n";
  &printHtmlFormButtonMenu();
  &printHtmlSection('Gene');
  &printHtmlInputGene();
  &printHtmlCheckbox('nodump');
#   &printHtmlButton('Delete !');	# removed at Kimberly's request  2007 05 17
  &printHtmlSection('Concise Description');
  &printHtmlTextarea('con');
  &printHtmlRef('con');
  &printHtmlCurators('con');
  &printHtmlTextarea('hum');
  &printHtmlRef('hum');
  &printHtmlCurators('hum');
  &printHtmlTextarea('ext');
  &printHtmlSection('Sequence Features');
  &printHtmlInputs('seq');
  &printHtmlSection('Functional Pathway');
  &printHtmlInputs('fpa');
  &printHtmlSection('Functional Physical Interaction');
  &printHtmlInputs('fpi');
  &printHtmlSection('Biological Process');
  &printHtmlInputs('bio');
  &printHtmlSection('Molecular Function');
  &printHtmlInputs('mol');
  &printHtmlSection('Expression');
  &printHtmlInputs('exp');
  &printHtmlSection('Other Description');
  &printHtmlInputs('oth');
#   &printHtmlSection('Phenotype');
#   &printHtmlInputs('phe');
  &printHtmlFormButtonMenu();
  &printHtmlFormEnd();
} # sub mainPage

sub printHtmlCurators {		# show all curators that changed the car_con_maindata (look at car_con_ref_curator)  2005 12 22
  my ($type) = @_;
  my $field = $type . '_text_only';
  if ($theHash{$field}{curators}) {
    print "<TR><TD ALIGN=right><STRONG>Curator Confirmed :</STRONG></TD>\n
      <TD><TABLE><TR><TD>$theHash{$field}{curators}</TD></TR></TABLE></TD></TR>\n"; }
} # sub printHtmlCurators

sub printHtmlInputs {
  my $grouptype = shift;
  $theHash{$grouptype}{num} = 4;		# changed from 2 to 4 for Kimberly 2006 03 01
  my ($var, $val) = &getHtmlVar($query, "${grouptype}_number"); 
  if ($val) { $theHash{$grouptype}{num} = $val; }
  if ($theHash{$grouptype}{num_pg}) {		# if chosen to query field, make max if higher than existing
    if ($theHash{$grouptype}{num_pg} > $theHash{$grouptype}{num}) { $theHash{$grouptype}{num} = $theHash{$grouptype}{num_pg}; }	}
  if ($theHash{$grouptype}{num_add}) { $theHash{$grouptype}{num}++; }	# if chosen to add field, add field
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"${grouptype}_number\" VALUE=\"$theHash{$grouptype}{num}\">\n"; 
  for my $i ( 1 .. $theHash{$grouptype}{num} ) {
    &printHtmlInput($grouptype, $i); }
  print "<TR><TD></TD><TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add another $aceTrans{$grouptype} !\"></TD></TR>\n";
} # sub printHtmlInputs

sub printHtmlInput {         # print html textareas
  my ($type, $i) = @_;             # get type and number, use hash for html parts
  my $action;
  unless ($action = $query->param('action')) { $action = 'none'; } else { $frontpage = 0; }
  if ($action eq 'Curator !') { (my $var, $theHash{$type}{curator_name}) = &getHtmlVar($query, 'curator_name'); }
  unless ($theHash{$type}{$i}{html_value}) { $theHash{$type}{$i}{html_value} = ''; }      	# clear blank
  if ($theHash{$type}{$i}{html_value} eq 'NULL') { $theHash{$type}{$i}{html_value} = ''; }      # clear NULL
  my $checked = ''; if ($theHash{$type}{$i}{html_mail_box}) { $checked = 'CHECKED'; }
#   unless ( $theHash{$type}{$i}{person} ) { $theHash{$type}{$i}{person} = ''; }		# initialize junk if doesn't exist
#   unless ( $theHash{$type}{$i}{paper} ) { $theHash{$type}{$i}{paper} = ''; }		# initialize junk if doesn't exist
  unless ( $theHash{$type}{$i}{reference} ) { $theHash{$type}{$i}{reference} = ''; }		# initialize junk if doesn't exist
  unless ( $theHash{$type}{$i}{accession} ) { $theHash{$type}{$i}{accession} = ''; }		# initialize junk if doesn't exist
  unless ( $theHash{$type}{$i}{curator} ) { $theHash{$type}{$i}{curator} = ''; }	# initialize junk if doesn't exist
  unless ( $theHash{$type}{timestamp} ) { $theHash{$type}{timestamp} = ''; }
  print <<"  EndOfText";
  <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} $i :</STRONG></TD>
    <TD><TABLE><TR>
          <TD><TEXTAREA NAME="html_value_$type$i" ROWS=$theHash{$type}{html_size_minor}
               COLS=$theHash{$type}{html_size_main}>$theHash{$type}{$i}{html_value}</TEXTAREA></TD>
          <TD>Update Block :<BR><INPUT NAME="html_value_box_$type$i" TYPE="checkbox" $checked VALUE="yes"></TD> <TD></TD>
          <TD><SELECT NAME="html_value_${type}${i}_curator" SIZE=1>
                <OPTION>$theHash{$type}{$i}{curator}</OPTION>
                <OPTION>Carol Bastiani</OPTION>
                <OPTION>Ranjana Kishore</OPTION>
                <OPTION>Snehalata Kadam</OPTION>
                <OPTION>Erich Schwarz</OPTION>
                <OPTION>Gary C. Schindelman</OPTION>
                <OPTION>Kimberly Van Auken</OPTION>
                <OPTION>Karen Yook</OPTION>
                <OPTION>Paul Sternberg</OPTION>
                <OPTION>Igor Antoshechkin</OPTION>
                <OPTION>Raymond Lee</OPTION>
                <OPTION>Andrei Petcherski</OPTION>
                <OPTION>Wen Chen</OPTION>
                <OPTION>Juancarlos Chan</OPTION>
              </SELECT>
              <!--<INPUT NAME="html_timestamp_$type" VALUE="$theHash{$type}{timestamp}">--></TD>
        </TR></TABLE></TD></TR>
  <TR>
    <!--<TD ALIGN="right"><STRONG>Paper References $i :</STRONG></TD> switch to on reference 2005 05 12 for Carol-->
    <TD ALIGN="right"><STRONG><!--$theHash{$type}{html_field_name} -->References $i :</STRONG></TD>
    <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}${i}_reference" VALUE="$theHash{$type}{$i}{reference}"
                              SIZE=$theHash{$type}{html_size_main}></TD></TR>
	       <TR><TD><FONT SIZE=-3>(please enter references separated by a comma and a space.  e.g. ``cgc3, pmid12345678, WBPerson625, GO:xxxxxxx, Expr..., Aff_...., SMD_....., WBRNAixxxxxxxx, [Gene_regulation_evidence] cgc...._......., pmid...._.......'')</FONT>
                       </TD></TR></TABLE></TD></TR>
  EndOfText
#   <!--switch to on reference 2005 05 12 for Carol
#   <TR>
#     <TD ALIGN="right"><STRONG>Person References $i :</STRONG></TD>
#     <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}${i}_person" VALUE="$theHash{$type}{$i}{person}"
#                               SIZE=$theHash{$type}{html_size_main}></TD></TR>
# 	       <TR><TD><FONT SIZE=-3>(please enter WBPersons separated by a comma and a space.  e.g. ``WBPerson625, WBPerson48'')</FONT>
#                        </TD></TR></TABLE></TD></TR>-->
  if ($type eq 'seq') {		# sequence features has accession evidence
    print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>Accession Evidence $i :</STRONG></TD>
    <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}${i}_accession" VALUE="$theHash{$type}{$i}{accession}"
                              SIZE=$theHash{$type}{html_size_main}></TD></TR>
	       <TR><TD><FONT SIZE=-3>(please enter Accession evidence separated by a comma and a space.  e.g. ``SW:xxxxxx, TR:xxxxxx, BP:xxxxxxxx, FLYBASE:xxxxxxxxx, etc.'')</FONT>
                       </TD></TR></TABLE></TD></TR>
  EndOfText
  }
} # sub printHtmlInput

sub printHtmlButton {         # print html checkbox for not dumping
  my $type = shift;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$type :</STRONG></TD>
    <TD>
      <TABLE> <TR> <TD ALIGN="left"><INPUT TYPE="submit" NAME="action" VALUE="$type"></TD></TR> </TABLE>
    </TD>
  </TR>
  EndOfText
} # sub printHtmlButton

sub printHtmlCheckbox {         # print html checkbox for not dumping
  my $type = shift;
  my $checked = '';
  if ($theHash{$type}{html_value}) { 
    if ($theHash{$type}{html_value} eq "$type") { $checked = 'CHECKED'; }
    if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; } }
				# clear NULL
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$type :</STRONG></TD>
    <TD>
      <TABLE> <TR> <TD><INPUT NAME="html_value_$type" TYPE="checkbox" $checked VALUE="$type"></TD> </TR> </TABLE>
    </TD>
  </TR>
  EndOfText
} # sub printHtmlCheckbox

sub printHtmlInputGene {         # print html input for gene
  my $type = 'gene';
  if ($theHash{$type}{html_value}) { if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; } }
				# clear NULL
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>Gene :</STRONG></TD>
    <TD>
      <TABLE>
        <TR>
          <TD><INPUT NAME="html_value_$type" VALUE="$theHash{$type}{html_value}"
                     SIZE=$theHash{$type}{html_size_main}></TD>
          <TD ALIGN="left"><INPUT TYPE="submit" NAME="action" VALUE="Query !"></TD>
          <TD>(3-letter gene, e.g. pie-1)</TD>
        </TR>
      </TABLE>
    </TD>
  </TR>
  EndOfText
} # sub printHtmlInputGene


sub printHtmlRef {
  my $type = shift;             # get type, use hash for html parts
#   unless ( $theHash{$type}{paper} ) { $theHash{$type}{paper} = ''; }		# initialize junk if doesn't exist
#   unless ( $theHash{$type}{person} ) { $theHash{$type}{person} = ''; }		# initialize junk if doesn't exist
  unless ( $theHash{$type}{reference} ) { $theHash{$type}{reference} = ''; }		# initialize junk if doesn't exist
  unless ( $theHash{$type}{accession} ) { $theHash{$type}{accession} = ''; }		# initialize junk if doesn't exist
  my $accession_label = 'Accession Evidence';
  if ($type eq 'hum') { $accession_label = 'Database Information'; }
  print <<"  EndOfText";
  <TR>
    <!--<TD ALIGN="right"><STRONG>Paper References :</STRONG></TD> switch to on reference 2005 05 12 for Carol-->
    <TD ALIGN="right"><STRONG><!--$theHash{$type}{html_field_name} -->Evidence :</STRONG></TD>
    <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}_reference" VALUE="$theHash{$type}{reference}"
                              SIZE=$theHash{$type}{html_size_main}></TD></TR>
	       <TR><TD><FONT SIZE=-3>(please enter references separated by a comma and a space.  e.g. ``cgc3, pmid12345678, WBPerson625, GO:xxxxxxx, Expr..., Aff_...., SMD_....., WBRNAixxxxxxxx, [Gene_regulation_evidence] cgc...._......., pmid...._.......'')</FONT>
                       </TD></TR></TABLE></TD></TR>
  <TR>
    <TD ALIGN="right"><STRONG>$accession_label :</STRONG></TD>
    <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}_accession" VALUE="$theHash{$type}{accession}"
                              SIZE=$theHash{$type}{html_size_main}></TD></TR>
	       <TR><TD><FONT SIZE=-3>(please enter Accession evidence separated by a comma and a space.  e.g. ``SW:xxxxxx, TR:xxxxxx, BP:xxxxxxxx, FLYBASE:xxxxxxxxx, etc.'')</FONT>
                       </TD></TR></TABLE></TD></TR>

  EndOfText
#   <TR>
#     <TD ALIGN="right"><STRONG>Paper References :</STRONG></TD>
#     <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}_paper" VALUE="$theHash{$type}{paper}"
#                               SIZE=$theHash{$type}{html_size_main}></TD></TR>
# 	       <TR><TD><FONT SIZE=-3>(please enter papers separated by a comma and a space.  e.g. ``cgc3, pmid12345678'')</FONT>
#                        </TD></TR></TABLE></TD></TR>
#   <TR>
#     <TD ALIGN="right"><STRONG>Person References :</STRONG></TD>
#     <TD><TABLE><TR><TD><INPUT NAME="html_value_${type}_person" VALUE="$theHash{$type}{person}"
#                               SIZE=$theHash{$type}{html_size_main}></TD></TR>
# 	       <TR><TD><FONT SIZE=-3>(please enter WBPersons separated by a comma and a space.  e.g. ``WBPerson625, WBPerson48'')</FONT>
#                        </TD></TR></TABLE></TD></TR>
} # sub printHtmlRef

sub printHtmlTextarea {         # print html textareas
  my $type = shift;             # get type, use hash for html parts
  my $action;
  unless ($action = $query->param('action')) { $action = 'none'; } else { $frontpage = 0; }
  if ($action eq 'Curator !') { (my $var, $theHash{$type}{curator_name}) = &getHtmlVar($query, 'curator_name'); }
  if ($theHash{$type}{html_value}) { if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; } }      # clear NULL
  my $checked = ''; 
  my $last_checked = ''; 
  if ( ($type eq 'con') || ($type eq 'hum') ) { 
     if ($theHash{"${type}_last_verified"}{html_value}) { $last_checked = 'CHECKED'; }
     $checked = 'CHECKED'; }
  if ($theHash{$type}{html_mail_box}) { $checked = 'CHECKED'; }
  unless ( $theHash{$type}{html_value} ) { $theHash{$type}{html_value} = ''; }		# initialize junk if doesn't exist
  unless ( $theHash{$type}{curator} ) { $theHash{$type}{curator} = ''; }		# initialize junk if doesn't exist
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD>
      <TABLE>
        <TR>
          <TD><TEXTAREA NAME="html_value_${type}_maindata" ROWS=$theHash{$type}{html_size_minor}
               COLS=$theHash{$type}{html_size_main}>$theHash{$type}{html_value}</TEXTAREA></TD>
          <TD>Update Block :<BR><INPUT NAME="html_value_box_$type" TYPE="checkbox" $checked VALUE="yes">
  EndOfText
  if ( ($type eq 'hum') || ($type eq 'con') ) { 	# last_verified only updated if this box is checked
    print "<BR><BR>              Update Last_Verified<BR>Timestamp : <INPUT NAME=\"html_value_box_${type}_last_verified\" TYPE=\"checkbox\" $last_checked VALUE=\"yes\">"; }
  print <<"  EndOfText";
               </TD>
          <TD> </TD>
          <TD><SELECT NAME="html_value_${type}_curator" SIZE=1>
                <OPTION>$theHash{$type}{curator}</OPTION>
                <OPTION>Carol Bastiani</OPTION>
                <OPTION>Ranjana Kishore</OPTION>
                <OPTION>Snehalata Kadam</OPTION>
                <OPTION>Erich Schwarz</OPTION>
                <OPTION>Gary C. Schindelman</OPTION>
                <OPTION>Kimberly Van Auken</OPTION>
                <OPTION>Karen Yook</OPTION>
                <OPTION>Paul Sternberg</OPTION>
                <OPTION>Igor Antoshechkin</OPTION>
                <OPTION>Raymond Lee</OPTION>
                <OPTION>Andrei Petcherski</OPTION>
                <OPTION>Wen Chen</OPTION>
                <OPTION>Juancarlos Chan</OPTION>
              </SELECT>
  EndOfText
  unless ($theHash{$type}{html_last_curator} eq 'no one') {
    # if someone to mail, print box and email address
    print <<"    EndOfText";
<!--          <TD><INPUT NAME="html_mail_box_$type" TYPE="checkbox"
               $theHash{$type}{html_mail_box} VALUE="yes"></TD>-->
          <TD> <FONT SIZE=-1>Last Curator $theHash{$type}{html_last_curator}</FONT></TD>
    EndOfText
  } # unless ($theHash{$type}{html_last_curator} eq 'no one')
  print <<"  EndOfText";
        </TR>
      </TABLE>
    </TD>
  </TR>
  EndOfText
} # sub printHtmlTextarea


sub printHtmlSection {          # print html sections
  my $text = shift;             # get name of section
  print "\n  "; for (0..12) { print '<TR></TR>'; } print "\n\n";                # divider
  print "  <TR><TD></TD><TD>Go to Section : </TD></TR>\n";
  print "  <TR><TD></TD><TD><LI><A href=#Gene>Gene</A>\n";
  print "  <LI><A href=\"#Concise Description\">Concise Description</A>\n";
  print "  <LI><A href=\"#Sequence Features\">Sequence Features</A>\n";
  print "  <LI><A href=\"#Functional Pathway\">Functional Pathway</A>\n";
  print "  <LI><A href=\"#Functional Physical Interaction\">Functional Physical Interaction</A>\n";
  print "  <LI><A href=\"#Biological Process\">Biological Process</A>\n";
  print "  <LI><A href=\"#Molecular Function\">Molecular Function</A>\n";
  print "  <LI><A href=\"#Expression\">Expression</A>\n";
  print "  <LI><A href=\"#Other Description\">Other Description</A>\n";
#   print "  <LI><A href=\"#Phenotype\">Phenotype</A></TD></TR>\n";
  print "  <TR><TD><STRONG><FONT SIZE=+1><A NAME=\"$text\">$text : </A></FONT></STRONG></TD></TR>\n"; # section
} # sub printHtmlSection

sub printHtmlFormEnd {          # ending of form
  print <<"  EndOfText";
  </TABLE>
  </FORM>
  EndOfText
} # sub printHtmlFormEnd

sub printHtmlFormStart {
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_new.cgi">
  <TABLE>
  EndOfText
} # sub printHtmlFormStart

sub printHtmlFormButtonMenu {   # buttons of form
  print <<"  EndOfText";
  <TR><TD COLSPAN=2> </TD></TR>
  <TR></TR> <TR></TR> <TR></TR> <TR></TR> <TR></TR>
  <TR></TR> <TR></TR> <TR></TR> <TR></TR> <TR></TR>
  <TR></TR> <TR></TR> <TR></TR> <TR></TR> <TR></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <INPUT TYPE="submit" NAME="action" VALUE="Dump Postgres !">
        <INPUT TYPE="submit" NAME="action" VALUE="Dump Readable !">
        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !">
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
<!--      <INPUT TYPE="submit" NAME="action" VALUE="Options !">
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Select All E-mail !">
      <INPUT TYPE="submit" NAME="action" VALUE="Select None E-mail !"></TD>-->
  </TR>
  <TR>
    <TD> </TD>
    <TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_dump_new.ace>Latest Concise Dump</A> --- <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_readable_dump.ace>Latest Human Readable Dump</A></TD></TR>
  EndOfText
} # sub printHtmlFormButtonMenu # buttons of form


sub initializeEmails {                  # create email codes and addresses
#   $emails{erich} = 'azurebrd@minerva.caltech.edu';
#   $emails{carol} = 'azurebrd@minerva.caltech.edu';
#   $emails{ranjana} = 'azurebrd@minerva.caltech.edu';
#   $emails{kimberly} = 'azurebrd@minerva.caltech.edu';
#   $emails{azurebrd} = 'azurebrd@minerva.caltech.edu';
  $emails{erich} = 'emsch@its.caltech.edu';
  $emails{gary} = 'garys@its.caltech.edu';
  $emails{carol} = 'bastiani@its.caltech.edu';
  $emails{ranjana} = 'ranjana@its.caltech.edu';
  $emails{snehalata} = 'snehalvk@its.caltech.edu';
  $emails{karen} = 'kyook@its.caltech.edu';
  $emails{kimberly} = 'vanauken@its.caltech.edu';
  $emails{paul} = 'pws@its.caltech.edu';
  $emails{igor} = 'igorant@caltech.edu';
  $emails{raymond} = 'raymond@its.caltech.edu';
  $emails{andrei} = 'agp@its.caltech.edu';
  $emails{wen} = 'wen@athena.caltech.edu';
  $emails{azurebrd} = 'azurebrd@tazendra.caltech.edu';
  $emails{''} = 'no one';               # just in case
                                        # (and flag to not print if irrelevant in textarea)
} # sub initializeEmails

sub initializeAceTrans {
  $aceTrans{con} = "Concise Description";
  $aceTrans{hum} = "Human Disease Relevance";
  $aceTrans{ext} = "Second + Extra Sentences";
  $aceTrans{seq} = "Sequence Features";
  $aceTrans{fpa} = "Functional Pathway";
  $aceTrans{fpi} = "Functional Physical Interaction";
  $aceTrans{bio} = "Biological Process";
  $aceTrans{mol} = "Molecular Function";
  $aceTrans{exp} = "Expression";
  $aceTrans{oth} = "Other";
  $aceTrans{phe} = "Phenotype";
} # sub initializeAceTrans


sub initializeHash {
  # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects.
  # in case of new sub fields, add to @PGsubparameters array and create html_field_name entry in 
  # %theHash and other %theHash fields as necessary.  if new email address, add to %emails.

  &initializeEmails();					# create email codes and addresses
  &initializeAceTrans();				# create ace display tags

  $theHash{gene}{html_size_main} = '15';
  $theHash{gene}{html_value} = '';

  $theHash{hum}{mail_subject} = '';
  $theHash{hum}{curator_name} = '';
  $theHash{hum}{timestamp} = 'Current Timestamp';	# default no timestamp
  $theHash{hum}{html_value_box} = '';			# checkbox for ``yes'' instead of value
  $theHash{hum}{html_value} = '';			# value for field
  $theHash{hum}{html_mail_box} = '';			# no, this value used to check whether curators wants block updated
  $theHash{hum}{html_last_curator} = 'no one';		# default to mail no one
  $theHash{hum}{html_size_main} = '90';			# default width 90
  $theHash{hum}{html_size_minor} = '6';			# default height 6
  $theHash{hum}{html_field_name} = 'Human Disease Relevance';
  $theHash{hum}{mail_to} = '';
  $theHash{hum}{html_mail_name} = "$emails{$theHash{con}{mail_to}}";
  $theHash{hum}{mail_subject} = 'Human Disease Relevance';
  $theHash{hum}{html_value} = '';

  $theHash{ext}{html_field_name} = 'Second + Extra Sentences of Provisional Description';
  $theHash{ext}{mail_to} = '';
  $theHash{ext}{html_mail_name} = "$emails{$theHash{ext}{mail_to}}";
  $theHash{ext}{mail_subject} = 'Second + Extra Sentences of Provisional Description';
  $theHash{ext}{html_last_curator} = 'no one';	# default to mail no one
  $theHash{ext}{html_value} = '';
  $theHash{ext}{html_size_main} = '90';
  $theHash{ext}{html_size_minor} = '40';

  $theHash{con}{mail_subject} = '';
  $theHash{con}{curator_name} = '';
  $theHash{con}{timestamp} = 'Current Timestamp';	# default no timestamp
  $theHash{con}{html_value_box} = '';			# checkbox for ``yes'' instead of value
  $theHash{con}{html_value} = '';			# value for field
  $theHash{con}{html_mail_box} = '';			# no, this value used to check whether curators wants block updated
  $theHash{con}{html_last_curator} = 'no one';		# default to mail no one
  $theHash{con}{html_size_main} = '90';			# default width 90
  $theHash{con}{html_size_minor} = '6';			# default height 6
  $theHash{con}{html_field_name} = 'Concise Description';
  $theHash{con}{mail_to} = '';
  $theHash{con}{html_mail_name} = "$emails{$theHash{con}{mail_to}}";
  $theHash{con}{mail_subject} = 'Concise Description';
  $theHash{con}{html_value} = '';

  foreach my $sub (@PGsubparameters) {
    $theHash{$sub}{html_value} = '';
    $theHash{$sub}{html_size_minor} = '4'; 
    $theHash{$sub}{html_size_main} = '60';
    $theHash{$sub}{timestamp} = 'Current Timestamp';
    $theHash{$sub}{curator} = '';
    $theHash{$sub}{mail_to} = '';
    $theHash{$sub}{html_mail_name} = "$emails{$theHash{$sub}{mail_to}}";
    if ($sub eq 'seq') { $theHash{$sub}{html_field_name} = "Sequence Features"; }
    elsif ($sub eq 'fpa') { $theHash{$sub}{html_field_name} = "Functional Pathway"; }
    elsif ($sub eq 'fpi') { $theHash{$sub}{html_field_name} = "Functional Physical Interaction"; }
    elsif ($sub eq 'bio') { $theHash{$sub}{html_field_name} = "Biological Process"; }
    elsif ($sub eq 'mol') { $theHash{$sub}{html_field_name} = "Molecular Function"; }
    elsif ($sub eq 'exp') { $theHash{$sub}{html_field_name} = "Expression"; }
    elsif ($sub eq 'oth') { $theHash{$sub}{html_field_name} = "Other"; }
    elsif ($sub eq 'phe') { $theHash{$sub}{html_field_name} = "Phenotype"; }
    else { $theHash{$sub}{html_field_name} = "ERROR"; }
  } # foreach my $sub (@PGsubparameters)
} # sub initializeHash


sub firstPage {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_new.cgi\">\n";
  print "<TABLE>\n";
  print "<TR><TD>Select your Name among : </TD><TD><SELECT NAME=\"curator_name\" SIZE=10>\n";
#   print "<OPTION>Igor Antoshechkin</OPTION>\n";
#   print "<OPTION>Carol Bastiani</OPTION>\n";
#   print "<OPTION>Wen Chen</OPTION>\n";
  print "<OPTION>Ranjana Kishore</OPTION>\n";
  print "<OPTION>Snehalata Kadam</OPTION>\n";
#   print "<OPTION>Raymond Lee</OPTION>\n"; 
#   print "<OPTION>Andrei Petcherski</OPTION>\n";
  print "<OPTION>Erich Schwarz</OPTION>\n";
  print "<OPTION>Gary C. Schindelman</OPTION>\n";
#   print "<OPTION>Paul Sternberg</OPTION>\n";
  print "<OPTION>Kimberly Van Auken</OPTION>\n";
  print "<OPTION>Karen Yook</OPTION>\n";
  print "<OPTION>Paul Sternberg</OPTION>\n";
#   print "<OPTION>Igor Antoshechkin</OPTION>\n";
  print "<OPTION>Raymond Lee</OPTION>\n";
#   print "<OPTION>Andrei Petcherski</OPTION>\n";
  print "<OPTION>Wen Chen</OPTION>\n";
  print "<OPTION>Juancarlos Chan</OPTION>\n"; 
  print "</SELECT></TD><TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Curator !\"></TD></TR><BR><BR>\n";
  print "</TABLE>\n"; 
  print "</FORM>\n";
} # sub firstPage


__END__

### DEPRECATED ####

# sub old_part_of_initialize_hash {
#   for my $i (1 .. 4) {					# orthology init
#     $theHash{"ort$i"}{html_field_name} = "Orthology $i";
#     $theHash{"ort$i"}{html_value} = '';
#     $theHash{"ort$i"}{html_size_minor} = '4'; 
#     $theHash{"ort$i"}{html_size_main} = '60';
#     $theHash{"ort$i"}{timestamp} = 'Current Timestamp';
#     $theHash{"ort$i"}{curator_name} = '';
#     $theHash{"ort$i"}{mail_to} = '';
#     $theHash{"ort$i"}{html_mail_name} = "$emails{$theHash{concise}{mail_to}}";
#     $theHash{"ort$i"}{mail_subject} = "Orthology $i";
#     my $subtype = 'ort' . $i . '_ref1';			# next 3 lines for single reference box
#     $theHash{subtype}{html_value} = '';
#     $theHash{$subtype}{html_size_main} = '65'; 
# #     for my $j (1 .. 4) {				# next 4 lines for 4 reference boxes
# #       my $subtype = 'ort' . $i . '_ref' . $j;
# #       $theHash{$subtype}{html_value} = '';
# #       $theHash{$subtype}{html_size_main} = '15'; }
#   }
# 
#   for my $i (1 .. 6) {					# genetic init
#     $theHash{"gen$i"}{html_field_name} = "Genetic $i";
#     $theHash{"gen$i"}{html_value} = '';
#     $theHash{"gen$i"}{html_size_minor} = '4';
#     $theHash{"gen$i"}{html_size_main} = '60';
#     $theHash{"gen$i"}{timestamp} = 'Current Timestamp';
#     $theHash{"gen$i"}{curator_name} = '';
#     $theHash{"gen$i"}{mail_to} = '';
#     $theHash{"gen$i"}{html_mail_name} = "$emails{$theHash{concise}{mail_to}}";
#     $theHash{"gen$i"}{mail_subject} = "Genetic $i";
#     my $subtype = 'gen' . $i . '_ref1';
#     $theHash{subtype}{html_value} = '';
#     $theHash{$subtype}{html_size_main} = '65'; 
# #     for my $j (1 .. 4) {
# #       my $subtype = 'gen' . $i . '_ref' . $j;
# #       $theHash{$subtype}{html_value} = '';
# #       $theHash{$subtype}{html_size_main} = '15'; }
#   }
# 
#   for my $i (1 .. 6) {					# physical init
#     $theHash{"phy$i"}{html_field_name} = "Physical $i";
#     $theHash{"phy$i"}{html_value} = '';
#     $theHash{"phy$i"}{html_size_minor} = '4';
#     $theHash{"phy$i"}{html_size_main} = '60';
#     $theHash{"phy$i"}{timestamp} = 'Current Timestamp';
#     $theHash{"phy$i"}{curator_name} = '';
#     $theHash{"phy$i"}{mail_to} = '';
#     $theHash{"phy$i"}{html_mail_name} = "$emails{$theHash{concise}{mail_to}}";
#     $theHash{"phy$i"}{mail_subject} = "Physical $i";
#     my $subtype = 'phy' . $i . '_ref1';
#     $theHash{subtype}{html_value} = '';
#     $theHash{$subtype}{html_size_main} = '65'; 
# #     for my $j (1 .. 4) {
# #       my $subtype = 'phy' . $i . '_ref' . $j;
# #       $theHash{$subtype}{html_value} = '';
# #       $theHash{$subtype}{html_size_main} = '15'; }
#   }
# 
#   for my $i (1 .. 6) {					# expression init
#     $theHash{"exp$i"}{html_field_name} = "Expression $i";
#     $theHash{"exp$i"}{html_value} = '';
#     $theHash{"exp$i"}{html_size_minor} = '4';
#     $theHash{"exp$i"}{html_size_main} = '60';
#     $theHash{"exp$i"}{timestamp} = 'Current Timestamp';
#     $theHash{"exp$i"}{curator_name} = '';
#     $theHash{"exp$i"}{mail_to} = '';
#     $theHash{"exp$i"}{html_mail_name} = "$emails{$theHash{concise}{mail_to}}";
#     $theHash{"exp$i"}{mail_subject} = "Expression $i";
#     my $subtype = 'exp' . $i . '_ref1';
#     $theHash{subtype}{html_value} = '';
#     $theHash{$subtype}{html_size_main} = '65'; 
# #     for my $j (1 .. 4) {
# #       my $subtype = 'exp' . $i . '_ref' . $j;
# #       $theHash{$subtype}{html_value} = '';
# #       $theHash{$subtype}{html_size_main} = '15'; }
#   }
# 
#   for my $i (1 .. 5) {					# other init
#     $theHash{"oth$i"}{html_field_name} = "Other $i";
#     $theHash{"oth$i"}{html_value} = '';
#     $theHash{"oth$i"}{html_size_minor} = '4';
#     $theHash{"oth$i"}{html_size_main} = '60';
#     $theHash{"oth$i"}{timestamp} = 'Current Timestamp';
#     $theHash{"oth$i"}{curator_name} = '';
#     $theHash{"oth$i"}{mail_to} = '';
#     $theHash{"oth$i"}{html_mail_name} = "$emails{$theHash{concise}{mail_to}}";
#     $theHash{"oth$i"}{mail_subject} = "Other $i";
#     my $subtype = 'oth' . $i . '_ref1';
#     $theHash{subtype}{html_value} = '';
#     $theHash{$subtype}{html_size_main} = '65'; 
# #     for my $j (1 .. 4) {
# #       my $subtype = 'oth' . $i . '_ref' . $j;
# #       $theHash{$subtype}{html_value} = '';
# #       $theHash{$subtype}{html_size_main} = '15'; }
#   }
# } # sub old_part_of_initialize_hash

# sub printHtmlRef16 {
#   my $type = shift;             # get type, use hash for html parts
#   for my $j ( 1 .. 4) {
#   print <<"  EndOfText";
#   <TR>
#     <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} References :</STRONG></TD>
#     <TD>
#       <TABLE>
#         <TR>
#   EndOfText
#     for my $i (1 .. 4) {
#       my $num = ($j * 4) - 4 + $i;
#       my $subtype = $type . '_ref' . $num;
#       print "      <TD><INPUT NAME=\"html_value_$subtype\" VALUE=\"$theHash{$subtype}{html_value}\"\n";
#       print "           SIZE=$theHash{$subtype}{html_size_main}></TD>\n";
#     }
#   print <<"  EndOfText";
#         </TR>
#       </TABLE>
#     </TD>
#   </TR>
#   EndOfText
#   } # for my $j ( 1 .. 4)
# } # sub printHtmlRef16

# sub oldgetCategories {
#   my $categories = '';
#   my $gene = shift;
#   my @categories = qw( ort gen phy exp oth );
#   my %aceTrans;
#   $aceTrans{ort} = 'Orthology';
#   $aceTrans{gen} = 'Genetic_Intxn_or_Pathway_or_Process';
#   $aceTrans{phy} = 'Physical_Intxn';
#   $aceTrans{exp} = 'Expression';
#   $aceTrans{oth} = 'Other';
#   foreach my $cat (@categories) {
#     my $highnum = 6;
#     if ($cat eq 'ort') { $highnum = 4; }
#     elsif ($cat eq 'oth') { $highnum = 5; }
#     for my $i ( 1 .. $highnum ) {
#       my $field = $cat . $i;
#       if ($theHash{$field}{html_value}) { 
#         my $found = $theHash{$field}{html_value};
#         $found =~ s/\s+/ /g; $found =~ s/^\s//g; $found =~ s/\s$//g;
#         my $orthology = $found;
# print "GET CAT<BR>\n";
#         my $curator = &convertPerson($theHash{$field}{curator_name});
#         $categories .= "ACE : $aceTrans{$cat}\t\"$orthology\"\tPerson_evidence\t\"$curator\"<BR>\n"; 
#         my $subtype = $field . '_ref1';
#         my @papers = split/, /, $theHash{$field}{$subtype};
#         foreach my $paper (@papers) {
#           $acePapers{$paper}++;
#           $categories .= "ACE : $aceTrans{$cat}\t\"$orthology\"\tPaper_evidence\t\"$paper\"<BR>\n"; }
#       } # if ($theHash{$field}{html_value})
#     } # for my $i ( 1 .. $highnum )
#   } # foreach my $cat (@categories)
#   $categories .= "\n";
#   return ($categories);
# } # sub oldgetCategories

# sub oldgetHtmlValuesFromForm {
#   my $hidden_values = '';
#   my $html_type = 'html_value_gene';
#   my $field = 'gene';
#   my ($var, $val) = &getHtmlVar($query, $html_type);
#   if ($val) { 			# if no gene entered, error
#     my $joinkey;
#     if ($val =~ m/^WBGene\d{8}/) { $joinkey = $val; }
#       else {
#         if ($wbGene{$val}) { $joinkey = $wbGene{$val}; }
#           else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $val NOT in sanger list</B></FONT><BR>\n"; next; } }
#     print "GENE $val IS $joinkey<BR>\n";
#     $theHash{$field}{html_value} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_gene\" VALUE=\"$val\">\n"; }
#   else {
#     print "<FONT SIZE=+2 COLOR='red'><B>ERROR : Need to enter a Gene</B></FONT><BR>\n";
#     next; }
# 
#   ($var, my $curator) = &getHtmlVar($query, 'curator_name');
#   $theHash{main}{curator_name} = $curator;
#   $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$curator\">\n"; 
# 
#   $html_type = 'html_value_box_concise';
#   $field = 'concise';
#   ($var, $val) = &getHtmlVar($query, $html_type);
#   if ($val) { 				# if box checked
#     $theHash{$field}{html_mail_box} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "There is Concise data<BR>\n"; 
#     $html_type = 'html_value_concise';
#     my ($var, $val) = &getHtmlVar($query, $html_type);
#     $theHash{$field}{html_value} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "Concise Description $val<BR>\n";
#     $html_type = 'html_value_curator_concise';
#     ($var, $val) = &getHtmlVar($query, $html_type);
#     $theHash{$field}{curator_name} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "CUR $val<BR>\n";
# #     $html_type = 'html_timestamp_concise';
# #     ($var, $val) = &getHtmlVar($query, $html_type);
# #     $theHash{$field}{html_timestamp} = $val;
# #     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
# #     print "TIME $val<BR>\n";
#     $html_type = 'html_value_concise_ref1';
#     my $subtype = 'ref1';
#     ($var, $val) = &getHtmlVar($query, $html_type);
#     unless ($val) { $val = ' '; }
#     $theHash{$field}{$subtype} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "REF 1 $val<BR>\n";
# #     for my $j ( 1 .. 16 ) {
# #       $html_type = 'html_value_concise_ref' . $j;
# #       my $subtype = 'ref' . $j;
# #       ($var, $val) = &getHtmlVar($query, $html_type);
# #       unless ($val) { $val = ' '; }
# #       $theHash{$field}{$subtype} = $val;
# #       $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
# #       print "REF $j $val<BR>\n";
# #     }
#   } # if ($val)
# 
#     # deal with new (big box for Erich) second sentence and extra sentences for provisional description
#   $html_type = 'html_value_box_extra_provisional';
#   $field = 'extra_provisional';
#   ($var, $val) = &getHtmlVar($query, $html_type);
#   if ($val) { 				# if box checked
#     $theHash{$field}{html_mail_box} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "There is Extra Provisional data<BR>\n"; 
#     $html_type = 'html_value_extra_provisional';
#     my ($var, $val) = &getHtmlVar($query, $html_type);
#     $theHash{$field}{html_value} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "Extra Provisional Description $val<BR>\n";
#     $html_type = 'html_value_curator_extra_provisional';
#     ($var, $val) = &getHtmlVar($query, $html_type);
#     $theHash{$field}{curator_name} = $val;
#     $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#     print "CUR $val<BR>\n";
#   } # if ($val) 
# 
#   my @categories = qw( ort gen phy exp oth );
#   foreach my $cat (@categories) {
#     for my $i (1 .. 6) {
#       $field = $cat . $i;
#       my $html_type = "html_value_box_$cat$i";
#       ($var, $val) = &getHtmlVar($query, $html_type);
#       if ($val) {				# if box checked
#         $theHash{$field}{html_mail_box} = $val;
#         $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#         print "$cat $i value checked<BR>\n";
#         $html_type = "html_value_$cat$i";
#         ($var, $val) = &getHtmlVar($query, $html_type);
#         $theHash{$field}{html_value} = $val;
#         $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#         print "$cat $i $val<BR>\n";
#         $html_type = "html_value_curator_$cat$i";
#         ($var, $val) = &getHtmlVar($query, $html_type);
#         $theHash{$field}{curator_name} = $val;
#         $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#         print "$html_type $i $val<BR>\n";
# #         $html_type = "html_timestamp_$cat$i";
# #         ($var, $val) = &getHtmlVar($query, $html_type);
# #         $theHash{$field}{html_timestamp} = $val;
# #         $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
# #         print "$html_type $i $val<BR>\n";
#         for my $j (1 .. 4) {
#           my $subtype = $cat . $i . '_ref' . $j;
#           $html_type = "html_value_$subtype";
#           ($var, $val) = &getHtmlVar($query, $html_type);
#           unless ($val) { $val = ' '; }
#           $theHash{$field}{$subtype} = $val;
#           $hidden_values .= "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
#           print "$html_type $i $val<BR>\n";
#         } # for my $j (1 .. 4)
#       } # if ($val)
#     } # for my $i (1 .. 6)
#   } # foreach my $cat (@categories)
#   return $hidden_values;
# } # sub oldgetHtmlValuesFromForm

# sub oldwrite {
#   my $new_or_update = shift;				# flag whether to add ``UPDATE : '' to subject line
#   &getSangerConversion(); 
#   my $hidden_values = &getHtmlValuesFromForm();
#   my $field = 'concise';
#   if ($theHash{$field}{html_mail_box}) {
#     my $type = 'lastcurator'; my $val = $theHash{main}{curator_name};
#     print "MAIN CUR $val<BR>\n";
#     &updatePostgresFieldTables($type, $val);    # update postgres for all tables
#     $type = 'concise'; $val = $theHash{$field}{html_value};
#     &updatePostgresFieldTables($type, $val);    # update postgres for all tables
#     print "$field CUR $theHash{$field}{curator_name}<BR>\n";
#     $type = 'con_curator'; my $cur = $theHash{$field}{curator_name};
#     &notifyPostgresPreviousCurator($type, $cur, $val);	# email previous curator
#     &updatePostgresFieldTables($type, $cur);    # update postgres for all tables
# #     print "$field VAL $theHash{$field}{html_value}<BR>\n";
#       my $j = 1;
#       my $subtype = 'ref' . $j;
#       $type = "con_$subtype"; $val = $theHash{$field}{$subtype};
#       &updatePostgresFieldTables($type, $val);    # update postgres for all tables
# #       print "$field SUB $subtype $theHash{$field}{$subtype}<BR>\n"; 
#   } # if ($theHash{$field}{html_mail_box})
# 
#   $field = 'extra_provisional';
#   if ($theHash{$field}{html_mail_box}) {
#     my $type = 'extra_provisional'; my $val = $theHash{$field}{html_value};
#     &updatePostgresFieldTables($type, $val);    # update postgres for all tables
#     print "$field CUR $theHash{$field}{curator_name}<BR>\n";
#     $type = 'ext_curator'; my $cur = $theHash{$field}{curator_name};
#     &notifyPostgresPreviousCurator($type, $cur, $val);	# email previous curator
#     &updatePostgresFieldTables($type, $cur);    # update postgres for all tables
#   } # if ($theHash{$field}{html_mail_box})
#     
#   my @categories = qw( ort gen phy exp oth );
#   foreach my $cat (@categories) {
#     for my $i (1 .. 6) {				# six is max amount, some have less but won't have box checked
#       $field = $cat . $i;
#       if ($theHash{$field}{html_mail_box}) {		# if box was checked
#         my $type = $field; my $val = $theHash{$field}{html_value};
#         &updatePostgresFieldTables($type, $val);	# update postgres for all tables
# #         print "$field CUR $theHash{$field}{curator_name}<BR>\n";
#         $type = $field . '_curator'; my $cur = $theHash{$field}{curator_name};
#         &notifyPostgresPreviousCurator($type, $cur, $val);	# email previous curator
#         &updatePostgresFieldTables($type, $cur);	# update postgres for all tables
# #         print "$field VAL $theHash{$field}{html_value}<BR>\n";
# #         for my $j (1 .. 4) {				# for each reference
#           my $j = 1;
#           my $subtype = $cat . $i . '_ref' . $j;
#           $type = "$subtype"; $val = $theHash{$field}{$subtype};
#           &updatePostgresFieldTables($type, $val);    # update postgres for all tables
# #           print "$field SUB $subtype $theHash{$field}{$subtype}<BR>\n"; 
# #         } # for my $j (1 .. 4)
#       } # if ($theHash{$field}{html_mail_box})
#     } # for my $i (1 .. 6)
#   } # foreach my $cat (@categories)
#   print "WRITE $new_or_update<BR>\n";
# } # sub oldwrite

# sub oldprintHtmlInputs {
#   my $grouptype = shift;
#   my $num = 6;
# #   print "<TABLE bgcolor='cyan'>\n";
#   if ($grouptype eq 'ort') { $num = 4; } 
#   elsif ($grouptype eq 'oth') { $num = 5; } 
#   else { 1; }
#   for my $i ( 1 .. $num ) {
#     my $type = $grouptype . $i;
#     &printHtmlInput($type);
#   }
# #   print "</TABLE>\n";
# } # sub oldprintHtmlInputs

# sub oldreadable {			# dump human readable (old longtext .ace version)
# # FIX THIS NEED TO CODE FOR non-paper
#   my %genes;
#   &getSangerConversion(); 
#   &readConversions();
#   print "This will take about 30 seconds.<BR>\n";
#   my $outfile = '/home/postgres/public_html/cgi-bin/data/concise_readable_dump.ace';
#   open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
#   my $result = $dbh->prepare( "SELECT * FROM car_lastcurator WHERE joinkey ~ 'WBGene' AND joinkey != 'WBGene00000000' ORDER BY car_timestamp DESC;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     # don't include test entry
#   while ( my @row = $result->fetchrow ) { $genes{$row[0]}++; }
#   foreach my $gene (sort keys %genes) {
# # print "GENE $gene GENE<BR>\n";
# # next if ($gene eq 'WBGene00000000');
#     if ($gene !~ m/^WBGene\d{8}/) {
#       if ($wbGene{$gene}) {
#         $gene = $wbGene{$gene}; }
#       else {
#         print STDERR "$gene is not approved by Sanger\n"; next; }
#     } # if ($gene !~ m/^WBGene\d{8}/)
#     print OUT "Gene : \"$gene\"";
#     if ($wbGeneBack{$gene}) { print OUT '    // ' .  $wbGeneBack{$gene}; }
#     print OUT "\n";
#     $result = $dbh->prepare( "SELECT * FROM car_con_ref_curator WHERE joinkey = '$gene';" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     my %curators = ();					# filter multiple entries of curator
#     while ( my @row = $result->fetchrow ) { $curators{$row[1]}++; }
#     foreach my $curator (sort keys %curators) {		# make sure there are no blank curators
#       if ($curator) { 
#         my $wb_person = &convertPerson($curator);
#         print OUT "Provisional_description \"$gene\" Person_evidence \"$wb_person\"\t\/\/ $curator\n"; } }
#     $result = $dbh->prepare( "SELECT * FROM car_con_ref_person WHERE joinkey = '$gene';" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     my %persons = ();					# filter multiple entries of curator
#     while ( my @row = $result->fetchrow ) { $persons{$row[1]}++; }
#     foreach my $person (sort keys %persons) {		# make sure there are no blank persons
#       if ($person) { 
#         my $wb_person = &convertPerson($person);
#         print OUT "Provisional_description \"$gene\" Person_evidence \"$wb_person\"\t\/\/ $person\n"; } }
#     $result = $dbh->prepare( "SELECT * FROM car_con_ref_paper WHERE joinkey = '$gene' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     my @row = $result->fetchrow; 			# get latest entry only
#     if ($row[1]) {
#       my @papers = split/, /, $row[1];
#       foreach my $paper (@papers) { 
#         $paper =~ s/\.$//g;				# take out extra period at the end of paper
#         if ($paper =~ m/WBPaper/) {
#           print OUT "Provisional_description \"$gene\" Paper_evidence \"$paper\"\n"; }
#         elsif ($convertToWBPaper{$paper}) {
#           print OUT "Provisional_description \"$gene\" Paper_evidence \"$convertToWBPaper{$paper}\"  // $paper\n"; }
#         else { print "// ERROR NO Convertion for $paper\n"; }
# #         print OUT "Provisional_description \"$gene\" Paper_evidence \"\[$paper\]\"\n"; 
#     } }
#     my $long_line = '';
#     $result = $dbh->prepare( "SELECT * FROM car_con_maindata WHERE joinkey = '$gene' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     @row = $result->fetchrow; 
#     if ($row[1]) { 
#       if ($row[1] =~ m/\s+$/) { $row[1] =~ s/\s+$//g; }	# WBGene00006719 has extra stuff at the end that makes the dump fail
#       $long_line .= $row[1]; }
#     $result = $dbh->prepare( "SELECT * FROM car_ext_maindata WHERE joinkey = '$gene' ORDER BY car_timestamp DESC;" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     @row = $result->fetchrow; 
#     if ($row[1]) { 
#       if ($row[1] =~ m/\s+$/) { $row[1] =~ s/\s+$//g; }
#       $long_line .= " $row[1]"; }
#     if ($long_line) {
#       $long_line =~ s// /g; $long_line =~ s/\n/ /g; $long_line =~ s/\s+/ /g;
#       print OUT "\nLongText : \"$gene\"\n\n";
#       while ($long_line =~ m/.{80}/) {
#         if ($long_line =~ m/^\s*(\S.{0,78}\S)\s(.*)$/) {
#           print OUT "$1\n";  
#           $long_line = $2; }
#       } # while ($long_line)
#       print OUT "$long_line\n";
#       print OUT "\n***LongTextEnd***\n";
#     } # if ($row[1])
#     print OUT "\n\n";					# divider
#   } # foreach my $gene (sort keys %genes)
#   close (OUT) or die "Cannot close $outfile : $!";
#   print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_readable_dump.ace>Concise Human Readable Dump</A><BR>\n";
# } # sub oldreadable

# sub getSangerConversionObsolete {
#   # get sanger conversion
#   my $u = "http://tazendra.caltech.edu/~azurebrd/sanger/loci_all.txt";
# #   my $u = "http://www.sanger.ac.uk/Projects/C_elegans/LOCI/loci_all.txt";
#   my $ua = LWP::UserAgent->new(timeout => 30); #instantiates a new user agent
#   print "getting data from $u<BR>\n";
#   my $request = HTTP::Request->new(GET => $u); #grabs url
#   my $response = $ua->request($request);       #checks url, dies if not valid.
#   die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
#   my @tmp = split /\n/, $response->content;    #splits by line
#   foreach (@tmp) {
#     my ($three, $wb) = $_ =~ m/^(.*?),(.*?),/;      # added to convert genes
#     $wbGene{$three} = $wb;			# from 3-letter to WBGene type
#     $wbGeneBack{$wb} = $three;			# from WBGene to 3-letter type
# #     if ($_ =~ m/,([^,]*?) ,CGC approved$/) { # }        # 2004 05 05
#     if ($_ =~ m/,([^,]*?) ,approved$/) {        # 2005 05 06  the CGC was removed at some point
#       my @things = split/ /, $1;
#       foreach my $thing (@things) {
#         if ($thing =~ m/[a-zA-Z][a-zA-Z][a-zA-Z]\-\d+/) { $wbGene{$thing} = $wb; $wbGene{$wb} = $thing; } } }
#   } # foreach (@tmp)
#   print "added data from $u<BR>\n";
#   $wbGene{'test-1'} = 'WBGene00000000';
#   $wbGeneBack{'WBGene00000000'} = 'test-1';
#   $wbGene{'rmrp-1'} = 'WBGene00045095';		# added temporarily for Erich 2006 12 14
#   $wbGeneBack{'WBGene00045095'} = 'rmrp-1';	# added temporarily for Erich 2006 12 14
# 
#   $u = 'http://tazendra.caltech.edu/~azurebrd/sanger/genes2molecular_names.txt';
# #   $u = 'http://www.sanger.ac.uk/Projects/C_elegans/LOCI/genes2molecular_names.txt';
#   print "getting data from $u<BR>\n";
#   $request = HTTP::Request->new(GET => $u); #grabs url
#   $response = $ua->request($request);       #checks url, dies if not valid.
#   die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
#   @tmp = split /\n/, $response->content;    #splits by line
#   foreach (@tmp) {
#     my ($wb, $cds, $three) = $_ =~ m/^(.*?)\t(.*?) (.*?)$/;      # added to convert genes
# # if ($_ =~ m/F54H12/) { print "F54H12 matches $_ line $wb $cds $three blah<BR>\n"; }
#     $wbGene{$cds} = $wb;			# from 3-letter to WBGene type
# # if ($cds =~ m/F54H12/) { print "putting in $cds for $wb<BR>\n"; }
#     $wbGeneBack{$wb} = $cds;			# from WBGene to 3-letter type
#     if ($three) {
#       $wbGene{$three} = $wb;			# from 3-letter to WBGene type
#       $wbGeneBack{$wb} .= ' ' . $three;		# from WBGene to 3-letter type
#     }
#   } # foreach (@tmp)
#   print "added data from $u<BR>\n";
#   print "<P>\n";
# } # sub getSangerConversionObsolete


### Might want this again someday, taken off at Kimberly's request  2007 05 17
# sub deleteGene {
#   my $toggle = shift;
#   &getSangerConversion(); 
#   my ($var, $gene) = &getHtmlVar($query, 'html_value_gene');
#   if ($gene =~ m/^\s+/) { $gene =~ s/^\s+//g; }
#   if ($gene =~ m/\s+$/) { $gene =~ s/\s+$//g; }
#   my $joinkey;
#   if ($gene =~ m/^WBGene\d{8}/) { $joinkey = $gene; }
#     else {
#       if ($wbGene{$gene}) { $joinkey = $wbGene{$gene}; }
#         else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : $gene NOT in sanger list</B></FONT><BR>\n"; next; }
#       if ($gene) { print "GENE $gene IS $joinkey<BR>\n"; }
#         else { print "<FONT SIZE=+2 COLOR='red'><B>ERROR : Need to enter a Gene</B></FONT><BR>\n"; next; } }
#   if ($toggle eq 'test') { 
#       print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/concise_description_new.cgi\">\n";
#       print "<FONT SIZE=+4 COLOR=RED>Are you sure you want to delete this gene : $joinkey ($gene)</FONT><BR> To keep in postgres but away from dumping, instead check on the nodump checkbox and preivew like usual.<br>\n"; 
#       print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_gene\" VALUE=\"$gene\">\n"; 
#       printHtmlButton('Confirm Delete !');
#       print "</FORM>\n"; }
#     elsif ($toggle eq 'confirm') {
#       print "<FONT COLOR=RED>Deleting from postgres this gene : $joinkey ($gene)</FONT><BR>\n"; 
#       my $type = 'lastcurator'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'con_maindata'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'con_ref_curator'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'con_ref_reference'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'con_ref_accession'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'con_last_verified'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'ext_maindata'; &deletePostgresFieldTables($type, $joinkey);
#       $type = 'ext_ref_curator'; &deletePostgresFieldTables($type, $joinkey);
#       foreach my $sub (@PGsubparameters) {
#         $type = $sub . '_maindata'; &deletePostgresFieldTables($type, $joinkey);
#         $type = $sub . '_ref_curator'; &deletePostgresFieldTables($type, $joinkey);
#         $type = $sub . '_ref_reference'; &deletePostgresFieldTables($type, $joinkey);
#         $type = $sub . '_ref_accession'; &deletePostgresFieldTables($type, $joinkey);
#       }
#   }
# } # sub deleteGene
# 
# sub deletePostgresFieldTables {
#   my ($table, $joinkey) = @_;
#   $table = 'car_' . $table;
#   my $result = $dbh->do( "DELETE FROM $table WHERE joinkey = \'$joinkey\';" );
#   print "<FONT COLOR='green'>DELETE FROM $table WHERE joinkey = \'$joinkey\');</FONT><BR>"; 
# } # sub deletePostgresFieldTables
