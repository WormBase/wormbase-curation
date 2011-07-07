#!/usr/bin/perl

# Curate Anatomy Term Function
#
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
# Changing form for Anatomy Term.  Changed output files and save files.  2004 01 24
#
# Added AO Inference Type like GO Inference Type, but with different options and 
# .ace output to Remark instead of GO_term.  2004 01 28
#
# Added _comment as an Evidence tag, to deal with comments as Remarks for Raymond.
# 2004 02 02
# 
# Changed @inferences for raymond to : Laser_ablation Genetic_ablation 
# Blastomere_ablation Genetic_mosaic Expression_mosaic   2004 02 24
#
# Changed Remark output that has $goid to say GO_term instead of Remark
# and not say "inferred from"  2004 02 24
#
# Redid tables in postgres so that there is only one table for all of any
# given row of data type (e.g. got_bio_goterm instead of got_bio_goterm1, 
# got_bio_goterm2, etc.) so that an arbitrary amount of columns can be 
# stored.  Copied all anatomy_term data to new tables.  Changed the way
# theHash stores data for these new tables as having an {$i} field 
# corresponding to the got_order column in the pg_tables.  Added 
# $default_columns variable to store the amount of columns that should be
# displayed and a ``Add Column !'' button to insert another column.  When
# updating data must now also check the highest existing column number in
# PG to have updates up to in, and inserts beyond it.  Changed preview,
# write, getHtmlValuesFromForm, printHtmlForm to correspond to new data
# structure.  2004 07 21
#
# Migrated data to ant_ tables, see :
# /home/postgres/work/pgpopulation/anatomy_term/20051014_migrate_postgres
# So changed all  got_  into  ant_  and it should work.  2005 10 14
#
# Changed &getPgGoTerms(); to look at got_goterm instead of ant_goterm 
# (since ant_goterm never existed).  2006 02 03
#
# Added date to .ace output for Raymond.  2006 02 08
#
# Finally added a WBPaper filter for papers.  2006 11 20


use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate
use LWP::UserAgent;	# getting sanger files for querying
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $query = new CGI;	# new CGI form

my %theHash;		# huge hash for each field with relevant values
my @PGparameters;	# array of names of pg values for html, pg, and theHash
my @PGsubparameters;	# array of names of pg values for html, pg, and theHash (add bio cell and mol to each)

my %goTerm;		# the Go Terms in postgres, key id, value name

my %cgcHash;		# hash of cgcs, values pmids
my %pmHash;		# hash of pmids, values cgcs

my %hashLocus;		# hash of Sanger flatfile data for key locus (sequences synonyms)
my %hashSequence;	# hash of Sanger flatfile data for key sequence (protein)

my $curator = '';
my $data_file = '/home/postgres/public_html/cgi-bin/data/go.txt';
my $ace_file = '/home/postgres/public_html/cgi-bin/data/go.ace';			# not used anymore
# my $save_file = "/home/postgres/public_html/cgi-bin/data/go_save_$curator.txt";
			# doesn't double re-interpolate the $curator name once $curator loaded
			# so using this line below

my $default_columns = 4;

&printHeader('Anatomy Term Curation Form');
&initializeHash();	# Initialize theHash structure for html names and box sizes
&process();		# do everything
&printFooter();

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  if ($action eq '') { &printHtmlForm(); }		# Display form, first time, no action
  else { 						# Form Button
    print "ACTION : $action : ACTION<BR>\n"; 
    if ($action eq 'Preview !') { &preview(); } 	# check anatomy_term and curator 
    if ($action eq 'New Entry !') { &write(); } 	# write to postgres (INSERT)
    if ($action eq 'Update !') { &write(); }		# write to postgres (UPDATE)
    if ($action eq 'Query Postgres !') { &query(); }	# query postgres
    if ($action eq 'Add Column !') { &addColumn(); }# query postgres
    if ($action eq 'Reset !') { &reset(); }		# reinitialize %theHash and display form
    if ($action eq 'Save !') { &saveState(); }		# save to file
    if ($action eq 'Load !') { &loadState(); }		# load from file
    if ($action eq 'Options !') { &options(); }		# options menu (empty)
    print "ACTION : $action : ACTION<BR>\n"; 
  } # else # if ($action eq '') { &printHtmlForm(); }
} # sub process

#################  Action SECTION #################

sub options {
  print "<P><B>What would you like ?  Tell Juancarlos.</B><BR><P>\n";
} # sub options

 # 2004 07 20  loadState and saveState don't work because PGparameters split into self and PGsubparameters, and theHash has $i
sub loadState {		# get values from save file and put in %theHash{$type}{html_value} to display
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  &getCurator();					# get the curator from %theHash
  if ($curator eq 'NULL') {				# if no curator, warn			
    print "<FONT COLOR='blue'><B>ERROR : No curator chosen, go back and select one</B></FONT><BR>\n"; 
  } else {						# if curator is good
    undef $/;
    my $save_file = "/home/postgres/public_html/cgi-bin/data/go_save_anatomy_$curator.txt";
    open (SAVE, "<$save_file") or die "cannot open $save_file : $!";
    my $vals_to_save = <SAVE>;
    close SAVE or die "Cannot close $save_file : $!";
    $/ = "\n";
    my @vals_to_save = split/\t/, $vals_to_save;
    foreach my $type (@PGparameters) {
      $theHash{$type}{html_value} = shift @vals_to_save;
      $theHash{$type}{html_value} =~ s/TABREPLACEMENT/\t/g;
    } # foreach my $type (@PGparameters)
    &printHtmlForm();		# Display Html form with loaded values
  } # if ($curator eq 'NULL')
} # sub loadState

sub saveState {		# save values in order of PGparameters, tab delimited
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  &getCurator();					# get the curator from %theHash
  if ($joinkey eq 'NULL') {				# if anatomy_term is NULL (anatomy_term not entered)
    print "<FONT COLOR='blue'><B>ERROR : No anatomy_term chosen, go back and select one</B></FONT><BR>\n"; 
  } elsif ($curator eq 'NULL') {			# if no curator, warn
    print "<FONT COLOR='blue'><B>ERROR : No curator chosen, go back and select one</B></FONT><BR>\n"; 
  } else {						# if anatomy_term and curator are good
    my $vals_to_save;
    foreach my $type (@PGparameters) {
      $theHash{$type}{value} =~ s/\t/TABREPLACEMENT/g;
      if ($theHash{$type}{value} eq 'NULL') { $vals_to_save .= "\t"; }	# if NULL, store blank
      else { $vals_to_save .= "$theHash{$type}{value}\t"; }		# if not NULL, store value
    } # foreach my $type (@PGparameters)
    my $save_file = "/home/postgres/public_html/cgi-bin/data/go_save_anatomy_$curator.txt";
    open (SAVE, ">$save_file") or die "cannot create $save_file : $!";
    print SAVE "$vals_to_save\n";
    close SAVE or die "Cannot close $save_file : $!";
    print "<BR>SAVING TO $save_file<BR>\n";
  } # if ($joinkey eq 'NULL') 				# if anatomy_term is NULL (anatomy_term not entered)
} # sub saveState
 # 2004 07 20  loadState and saveState don't work because PGparameters split into self and PGsubparameters, and theHash has $i

sub addColumn {
  my $column_number;
  (my $var, $column_number) = &getHtmlVar($query, 'column_number');
  if ($column_number) { $default_columns = ++$column_number; }
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  &printHtmlForm();
} # sub addColumns

sub reset {
  &initializeHash();		# Re-initialize %theHash structure for html names and box sizes 
  &printHtmlForm(); 		# Display form (now empty)
} # sub reset

sub query {		# check postgres for anatomy_term, then get values from postgres 
			# and put in %theHash{$type}{html_value} for display
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  my $found = &findIfPgEntry("$joinkey");		# if anatomy_term, check if already in Pg
  unless ($found) { 					# if not found
    if ($joinkey eq 'NULL') {				# if anatomy_term is NULL (anatomy_term not entered)
      print "<FONT COLOR='blue'><B>ERROR : No anatomy_term chosen, go back and select one</B></FONT><BR>\n"; 
    } else {						# if anatomy_term not in postgres
      print "<FONT COLOR='blue'><B>ERROR : No previous entry for $joinkey</B></FONT><BR>\n";
    } # if ($joinkey eq 'NULL')
  } else {						# if anatomy_term found
    foreach my $type (@PGparameters) {
      my $result = $dbh->prepare( "SELECT * FROM ant_$type WHERE joinkey = '$joinkey';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      while (my @row = $result->fetchrow) { 
        my $val = &filterToPrintHtml("$row[1]");	# turn value to Html
        $theHash{$type}{html_value} = $val; 		# put value in %theHash
      } # while (my @row = $result->fetchrow) 
    } # foreach my $type (@PGparameters)

    foreach my $type (@PGsubparameters) {
      my @subtypes = qw( bio_ cell_ mol_ );
      foreach my $subt ( @subtypes ) {
        my $type = $subt . $type;
        my $result = $dbh->prepare( "SELECT * FROM ant_$type WHERE joinkey = '$joinkey';" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        while (my @row = $result->fetchrow) { 
          my $val = &filterToPrintHtml("$row[2]");	# turn value to Html
          $theHash{$type}{$row[1]}{html_value} = $val; 	# put value in %theHash
          if ($row[1] > $default_columns) { $default_columns = $row[1]; }
        } # while (my @row = $result->fetchrow) 
      } # foreach my $subt ( @subtypes )
    } # foreach my $type (@PGsubparameters)
    &printHtmlForm();
  } # else # unless ($found) 
} # sub query

sub write {		# write to postgres (INSERT or UPDATE as required) and flatfile
  my ($var, $column_number) = &getHtmlVar($query, 'column_number');	# get column number
  if ($column_number) { $default_columns = $column_number; }		# pass column number
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"column_number\" VALUE=\"$default_columns\">\n";
  open (OUT, ">>$data_file") or die "Cannot append to $data_file : $!";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  my $found = &findIfPgEntry("$joinkey");		# if anatomy_term, check if already in Pg
  foreach my $type (@PGparameters) {			# for all normal values for PG
    unless ($theHash{$type}{value} eq '') {
      if ($theHash{$type}{value} eq 'NULL') {		# enter NULLs in postgres
        if ($found) {					# if already in postgres, update data and timestamp
          my $result = $dbh->do( "UPDATE ant_$type SET ant_$type = NULL WHERE joinkey = '$joinkey';" );
          my $result = $dbh->do( "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
#           print "UPDATE ant_$type SET ant_$type = NULL WHERE joinkey = \'$joinkey\'\';<BR>\n";
#           print "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\'\';<BR>\n";
        } else {					# if not in postgres, enter data and timestamp
          my $result = $dbh->do( "INSERT INTO ant_$type VALUES ('$joinkey', NULL, CURRENT_TIMESTAMP);" );
#           print "<FONT COLOR='red'>my \$result = \$dbh->do( \"INSERT INTO ant_$type VALUES ('$joinkey', NULL, CURRENT_TIMESTAMP);\" );</FONT><BR>\n";
        } # if ($found)
      } else { # if ($theHash{$type}{value} eq 'NULL')	# enter values in postgres
        my $value = &filterForPostgres($theHash{$type}{value});
        if ($found) {					# if already in postgres, update data and timestamp
          my $result = $dbh->do( "UPDATE ant_$type SET ant_$type = '$value' WHERE joinkey = '$joinkey';" );
          my $result = $dbh->do( "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
#           print "<FONT COLOR='green'>my \$result = \$dbh->do( \"UPDATE ant_$type SET ant_$type = '$value' WHERE joinkey = '$joinkey';\" );</FONT><BR>\n";
#           print "<FONT COLOR='green'>my \$result = \$dbh->do( \"UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';\" );</FONT><BR>\n";
        } else {					# if not in postgres, enter data and timestamp
          my $result = $dbh->do( "INSERT INTO ant_$type VALUES ('$joinkey', '$value', CURRENT_TIMESTAMP);" );
#           print "<FONT COLOR='green'>my \$result = \$dbh->do( \"INSERT INTO ant_$type VALUES ('$joinkey', '$value', CURRENT_TIMESTAMP);\" );</FONT><BR>\n";
        } # if ($found)
      } # else # if ($theHash{$type}{value} eq 'NULL')
#       print "$type : $theHash{$type}{value}<BR>\n"; 
      print OUT "$type\t$theHash{$type}{value}\n"; } }
  foreach my $type (@PGsubparameters) {			# for all triplicate values for PG
    my @subtypes = qw( bio_ cell_ mol_ );
    foreach my $subt ( @subtypes ) {
      my $type = $subt . $type;
      for my $i (1 .. $default_columns) {			# for each of the three possible entries
        unless ($theHash{$type}{$i}{value} eq '') {
          my $highest_in_pg = &findHighestPgNumber($joinkey, $type);	# get highest number for that joinkey and table
#         print "HIGHEST $type $highest_in_pg<BR>\n";
          if ($theHash{$type}{$i}{value} eq 'NULL') {		# enter NULLs in postgres
            if ( ($found) && ($i <= $highest_in_pg) ) {		# if already in postgres, update data and timestamp
              my $result = $dbh->do( "UPDATE ant_$type SET ant_$type = NULL WHERE joinkey = '$joinkey' AND ant_order = '$i';" );
              my $result = $dbh->do( "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND ant_order = '$i';" );
#               print "UPDATE ant_$type SET ant_$type = NULL WHERE joinkey = \'$joinkey\' AND ant_order = \'$i\';<BR>\n";
#               print "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\' AND ant_order = \'$i\';<BR>\n";
            } else {					# if not in postgres, enter data and timestamp
              my $result = $dbh->do( "INSERT INTO ant_$type VALUES ('$joinkey', $i, NULL, CURRENT_TIMESTAMP);" );
#               print "<FONT COLOR='red'>my \$result = \$dbh->do( \"INSERT INTO ant_$type VALUES ('$joinkey', $i, NULL, CURRENT_TIMESTAMP);\" );</FONT><BR>\n";
            } # if ($found)
          } else { # if ($theHash{$type}{$i}{value} eq 'NULL')	# enter values in postgres
            my $value = &filterForPostgres($theHash{$type}{$i}{value});
            if ( ($found) && ($i <= $highest_in_pg) ) {		# if already in postgres, update data and timestamp
              my $result = $dbh->do( "UPDATE ant_$type SET ant_$type = '$value' WHERE joinkey = '$joinkey' AND ant_order = '$i';" );
              my $result = $dbh->do( "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND ant_order = '$i';" );
#               print "<FONT COLOR='green'>my \$result = \$dbh->do( \"UPDATE ant_$type SET ant_$type = '$value' WHERE joinkey = '$joinkey' AND ant_order = \'$i\';\" );</FONT><BR>\n";
#               print "<FONT COLOR='green'>my \$result = \$dbh->do( \"UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND ant_order = \'$i\';\" );</FONT><BR>\n";
            } else {					# if not in postgres, enter data and timestamp
              my $result = $dbh->do( "INSERT INTO ant_$type VALUES ('$joinkey', $i, '$value', CURRENT_TIMESTAMP);" );
#               print "<FONT COLOR='green'>my \$result = \$dbh->do( \"INSERT INTO ant_$type VALUES ('$joinkey', $i, '$value', CURRENT_TIMESTAMP);\" );</FONT><BR>\n";
            } # if ($found)
          } # else # if ($theHash{$type}{$i}{value} eq 'NULL')
#           print "$type $i : $theHash{$type}{$i}{value}<BR>\n"; 
          print OUT "$type $i\t$theHash{$type}{$i}{value}\n"; } } } }
    
# OLD WAY TO DEAL WITH
#   foreach my $type (sort keys %theHash) {
#     unless ( ($theHash{$type}{value} eq '') && ($theHash{$type}{1}{value} eq '') ) {
# #       print "HASH : $type : $theHash{$type}{value}<BR>\n";
#       my $highest_in_pg = &findHighestPgNumber($joinkey, $type);	# get highest number for that joinkey and table
#       print "HIGHEST $type $highest_in_pg<BR>\n";
#       if ($theHash{$type}{value} eq 'NULL') {		# enter NULLs in postgres
#         if ($found) {					# if already in postgres, update data and timestamp
# #           my $result = $dbh->do( "UPDATE ant_$type SET ant_$type = NULL WHERE joinkey = '$joinkey';" );
# #           my $result = $dbh->do( "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
#           print "UPDATE ant_$type SET ant_$type = NULL WHERE joinkey = \'$joinkey\';<BR>\n";
#           print "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\';<BR>\n";
#         } else {					# if not in postgres, enter data and timestamp
# #           my $result = $dbh->do( "INSERT INTO ant_$type VALUES ('$joinkey', NULL, CURRENT_TIMESTAMP);" );
#           print "<FONT COLOR='red'>my \$result = \$dbh->do( \"INSERT INTO ant_$type VALUES ('$joinkey', NULL, CURRENT_TIMESTAMP);\" );</FONT><BR>\n";
#         } # if ($found)
#       } else { # if ($theHash{$type}{value} eq 'NULL')	# enter values in postgres
#         my $value = &filterForPostgres($theHash{$type}{value});
#         if ($found) {					# if already in postgres, update data and timestamp
# #           my $result = $dbh->do( "UPDATE ant_$type SET ant_$type = '$value' WHERE joinkey = '$joinkey';" );
#           print "my \$result = \$dbh->do( \"UPDATE ant_$type SET ant_$type = '$value' WHERE joinkey = '$joinkey';\" );<BR>\n";
# #           my $result = $dbh->do( "UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
#           print "my \$result = \$dbh->do( \"UPDATE ant_$type SET ant_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';\" );<BR>\n";
#         } else {					# if not in postgres, enter data and timestamp
# #           my $result = $dbh->do( "INSERT INTO ant_$type VALUES ('$joinkey', '$value', CURRENT_TIMESTAMP);" );
# #           print "<FONT COLOR='green'>my \$result = \$dbh->do( \"INSERT INTO ant_$type VALUES ('$joinkey', '$value', CURRENT_TIMESTAMP);\" );</FONT><BR>\n";
#         } # if ($found)
#       } # else # if ($theHash{$type}{value} eq 'NULL')
#       print OUT "$type\t$theHash{$type}{value}\n";
#     } # unless ($theHash{$type}{value} eq '')
#   } # foreach $_  (sort keys %theHash)

  my $date = &getDate();
  print "$date<BR><BR>\n\n";
  print OUT "$date\n\n";
  close (OUT) or die "Cannot close $data_file : $!";

  &populateXref();
  &outputAce();
} # sub write

sub preview {		# preview page.  pass form with hidden values for all values of html.
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/anatomy_term_curation.cgi\">\n";
  my ($var, $column_number) = &getHtmlVar($query, 'column_number');	# get column number
  if ($column_number) { $default_columns = $column_number; }		# pass column number
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"column_number\" VALUE=\"$default_columns\">\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  &getCurator();					# get the curator from %theHash
  if ($joinkey eq 'NULL') { 				# if no anatomy_term, warn
    print "<FONT COLOR='blue'><B>ERROR : No anatomy_term chosen, go back and select one</B></FONT><BR>\n"; 
  } elsif ($curator eq 'NULL') {			# if no curator, warn
    print "<FONT COLOR='blue'><B>ERROR : No curator chosen, go back and select one</B></FONT><BR>\n"; 
  } else {						# if anatomy_term, show ``New Entry !'' button
    my $found = &findIfPgEntry("$joinkey");		# if anatomy_term, check if already in Pg
    if ($found) {					# if already in pg, show ``Update !'' button
      print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update !\"><BR>\n";
      print "<FONT SIZE=8 COLOR=red>This UPDATEs a previous entry, OVERWRITING data</FONT>\n";
    } else {						# if new, show ``New Entry !'' button
      print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"New Entry !\">\n";
    } # else # if ($found)
  } # if ($joinkey eq 'NULL') 
  print "</FORM>";
} # sub preview

sub getHtmlValuesFromForm {	# read PGparameters value from html form, then display to html
  &getPgGoTerms();					# from postgres tables updated twice a month
  foreach my $type (@PGparameters) {			# for all non-triplicate values for PG
      my $html_type = 'html_value_main_' . $type;
      my ($var, $val) = &getHtmlVar($query, $html_type);
      if ($val) { 					# if there is a value
        $theHash{$type}{value} = $val;		# put it in theHash
        $theHash{$type}{html_value} = $val;		# put it in theHash for html
        $val = &filterToPrintHtml($val);			# filter Html to print it
        print "$type : $val<BR>";	 			# print it
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
      } else {						# if there is no value
        $theHash{$type}{value} = 'NULL';			# put NULL in theHash
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"\">\n";
      } # else # if ($val) 
  } # foreach my $type (@PGparameters) 
  foreach my $type (@PGsubparameters) {			# for all triplicate values for PG
    my @subtypes = qw( bio_ cell_ mol_ );
    foreach my $subt ( @subtypes ) {
      my $type = $subt . $type;
      for my $i (1 .. $default_columns) {			# for each of the three possible entries
        my $html_type = 'html_value_main_' . $type . $i;  # if has columns, add column number to it
# print "HTMLTYPE $html_type<BR>\n";
        my ($var, $val) = &getHtmlVar($query, $html_type);
        if ($val) { 					# if there is a value
# print "TYPE $type I $i VAL $val<BR>\n";
          $theHash{$type}{$i}{value} = $val;		# put it in theHash
          $theHash{$type}{$i}{html_value} = $val;		# put it in theHash for html
print "theHash $type $i html_value $val<BR>\n";
          $val = &filterToPrintHtml($val);			# filter Html to print it
          print "$type $i : $val";	 			# print it
          if ($type =~ m/paper_evidence/) { print "&nbsp;&nbsp;<A HREF=\"http://www.wormbase.org/db/misc/paper?name=%5B$val%5D;class=Paper\">Check WormBase</A>"; } # link paper to WormBase
          print "<BR>\n";
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
              if ($goTerm{$goTerm}) { print "$type : You've entered <FONT COLOR='green'>$goTerm</FONT> which corresponds to <FONT COLOR='green'>$goTerm{$goTerm}</FONT><BR>\n"; } # print what's been chosen and what it is
                else { print "$type : You've entered <FONT COLOR='red'>$goTerm</FONT> which doesn't match anything in Postgres<BR>\n"; }
            } # foreach my $goTerm (@goTerms)
          } # if ($type =~ m/goid/) 
          print "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"$val\">\n";
        } else {						# if there is no value
          $theHash{$type}{$i}{value} = 'NULL';			# put NULL in theHash
          print "<INPUT TYPE=\"HIDDEN\" NAME=\"$html_type\" VALUE=\"\">\n";
        } # else # if ($val) 
      } # for my $i (1 .. $max)
    } # foreach my $subt ( @subtypes )
  } # foreach my $type (@PGsubparamenters)
  return $theHash{anatomy_term}{value};			# return the joinkey
} # sub getHtmlValuesFromForm

sub getPgGoTerms {
  my $result = $dbh->prepare( "SELECT * FROM got_goterm;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $goTerm{$row[0]} = $row[1]; }
} # sub getPgGoTerms

sub getCurator {					# get the curator and convert for save file
  $curator = $theHash{curator}{value};			# get the curator
  if ($curator =~ m/Juancarlos/) { $curator = 'azurebrd'; }
  elsif ($curator =~ m/Raymond/) { $curator = 'raymond'; }
#   elsif ($curator =~ m/Carol/) { $curator = 'carol'; }
#   elsif ($curator =~ m/Ranjana/) { $curator = 'ranjana'; }
#   elsif ($curator =~ m/Kimberly/) { $curator = 'kimberly'; }
#   elsif ($curator =~ m/Erich/) { $curator = 'erich'; } 
  else { 1; }
} # sub getCurator

sub findHighestPgNumber {	# check postgres for highest column in entry 
  my ($joinkey, $type) = @_;
  my $result = $dbh->prepare( "SELECT ant_order FROM ant_$type WHERE joinkey = '$joinkey' ORDER BY ant_order DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  return $row[0];
} # sub findHighestPgNumber

sub findIfPgEntry {	# check postgres for anatomy_term entry already in
  my $joinkey = shift;
  my $result = $dbh->prepare( "SELECT * FROM ant_anatomy_term WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
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

sub filterToPrintHtml {	# filter values for printing html
  my $val = shift;
  $val =~ s/\&/&amp;/g;				# filter out ampersands first
  $val =~ s/\"/&quot;/g;			# filter out double quotes
  $val =~ s/\</&lt;/g;				# filter out open angle brackets
  $val =~ s/\>/&gt;/g;				# filter out close angle brackets
  return $val;
} # sub filterToPrintHtml

#################  Action SECTION #################

#################  Formatting SECTION #################

sub outputAce {
  unless ($theHash{curator}{value}) { print "<FONT COLOR=red>ERROR No Curator Chosen.</FONT><BR>\n"; return; }
  else { 
    if ($theHash{curator}{value} =~ m/Raymond/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_anatomy_raymond.ace'; }
#     if ($theHash{curator}{value} =~ m/Ranjana/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_ranjana.ace'; }
#     elsif ($theHash{curator}{value} =~ m/Carol/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_carol.ace'; }
#     elsif ($theHash{curator}{value} =~ m/Kimberly/) { $ace_file = '/home/postgres/public_html/cgi-bin/data/go_kimberly.ace'; }
#     elsif ($theHash{curator}{value} =~ m/Erich/) {$ace_file = '/home/postgres/public_html/cgi-bin/data/go_erich.ace'; }
    elsif ($theHash{curator}{value} =~ m/Juancarlos/) {$ace_file = '/home/postgres/public_html/cgi-bin/data/go_anatomy_juancarlos.ace'; }
    else { print "<FONT COLOR=red>ERROR Not a valid Curator Chosen.</FONT><BR>\n"; return; }
  }
  open (ACE, ">>$ace_file") or die "Cannot append to $ace_file : $!";
  unless ($theHash{anatomy_term}{value}) {             # no sequences, say so
    print "<FONT COLOR='red'>WARNING : no anatomy_term for $theHash{anatomy_term}{value}</FONT><BR>\n";
  } else { # unless ($theHash{anatomy_term})    # if sequence, then
    my $ace_entry = '';                                 # initialize entry
    my @ontology = qw(bio cell mol);
    for my $ontology (@ontology) {                      # for each of the three ontologies
      for my $i (1 .. $default_columns) {                              # for each of the three possible entries
        my $goid_tag = $ontology . '_goid';
        if ($theHash{$goid_tag}{$i}{value} ne 'NULL') {
          my $goid = $theHash{$goid_tag}{$i}{value};
          $goid =~ s/^\s+//g; $goid =~ s/\s+$//g;
          if ($goid =~ m/^\d+$/) { $goid = 'GO:' . $goid; }	# and add the GO: tag

          my @evidence_tags = qw( _goinference _goinference_two _aoinference _comment );      # the inference types
          foreach my $ev_tag (@evidence_tags) {                 # for each of the inference types
            my $evidence_tag = $ontology . $ev_tag;        # get evidence tag
            if ($theHash{$evidence_tag}{$i}{value} ne 'NULL') {
              my $inference = $theHash{$evidence_tag}{$i}{value};   # the inference type
              $inference =~ s/ --.*$//g;

              my $tag = $ontology . '_paper_evidence';
              my $db_reference = '';				# paper id number
              if ($theHash{$tag}{$i}{value} ne 'NULL') {
                if ($theHash{$tag}{$i}{value} !~ m/[ ,]/) {		# and it's just one paper, print it
                  $db_reference = $theHash{$tag}{$i}{value};
                  if ($db_reference =~ m/WBPaper\d{8}/) { 1; }
                    else { 
                      my ($number) = $db_reference =~ m/(\d+)/;
                      if ($number > 10000) {
                        my $key = 'pmid' . $number;
                        $db_reference = '[' . $pmHash{$key} . ']'; } }
#                   $ace_entry .= "GO_term\t\"$goid\"\tPaper_evidence\t\"[$db_reference]\"\n";
                  if ($ev_tag eq '_aoinference') {
#                     $ace_entry .= "Remark\t\"$goid inferred from $inference\"\tPaper_evidence\t\"[$db_reference]\"\n"; 
                    $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
                  elsif ($ev_tag eq '_comment') {
                    $ace_entry .= "Remark\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
                  else {
                    $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
#                   $ace_entry .= "GO_term\t\"$goid\"\tPaper_evidence\t\"[$theHash{$tag}{$i}{value}]\"\n";
                } else { 
                  my @papers = split /, /, $theHash{$tag}{$i}{value};
                  foreach my $paper (@papers) {			# print separate papers
                    $db_reference = $paper;
                    if ($db_reference =~ m/WBPaper\d{8}/) { 1; }
                      else {
                        my ($number) = $db_reference =~ m/(\d+)/;
                        if ($number > 10000) {
                          my $key = 'pmid' . $number;
      		          if ($pmHash{$key}) { $db_reference = $pmHash{$key}; }	} 	# if there's a cgc, write cgc else leave the same
                        $db_reference =~ s/\[//g;		# take out brackets so that they are not entered twice
                        $db_reference =~ s/\]//g;		# take out brackets so that they are not entered twice
                        $db_reference = '[' . $db_reference . ']'; }
                    if ($ev_tag eq '_aoinference') {
                      $ace_entry .= "Remark\t\"$goid\"\t\"$inference\"\n"; }
                    elsif ($ev_tag eq '_comment') {
                      $ace_entry .= "Remark\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
                    else {
#                       $ace_entry .= "Remark\t\"$goid inferred from $inference\"\tPaper_evidence\t\"[$db_reference]\"\n";
                      $ace_entry .= "Remark\t\"$goid\"\t\"$inference\"\tPaper_evidence\t\"$db_reference\"\n"; }
                  } # foreach my $paper (@papers)
                } # else # if ($theHash{$tag}{$i}{value} !~ m/[ ,]/)
              } # if ($theHash{$tag}{$i}{value})
    
              $tag = $ontology . '_person_evidence';
              if ($theHash{$tag}{$i}{value} ne 'NULL') {
                if ($theHash{$tag}{$i}{value} =~ m/ishore/) {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"WBPerson324\"\n";
                } elsif ($theHash{$tag}{$i}{value} =~ m/ee/) {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"WBPerson363\"\n";
                } elsif ($theHash{$tag}{$i}{value} =~ m/chwarz/) {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"WBPerson567\"\n";
                } else {
                  $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tPerson_evidence\t\"$theHash{$tag}{$i}{value}\"\n";
                }
              } # if ($theHash{$tag}{$i}{value})
    
# 2004 07 20 noticed not using similarity for a while
#               $tag = $ontology . '_similarity' . $i;
#               if ($theHash{$tag}{$i}{value} ne 'NULL') {
#                 $ace_entry .= "GO_term\t\"$goid\"\t\"$inference\"\tProtein_id_evidence\t\"$theHash{$tag}{$i}{value}\"\n";
#               } # if ($theHash{$tag}{$i}{value})

            } # if ($theHash{$evidence_tag}{$i}{value})
          } # foreach my $ev_tag (@evidence_tags) 
        } # if ($theHash{$goid_tag}{$i}{value} ne 'NULL')
      } # for my $i (1 .. $default_columns)
    } # for my $ontology (@ontology)
    $ace_entry .= "\n";                                 # add separator

    my $date = &getPgDate(); 
    print ACE '//' . "$date\n";		# add date for Raymond  2006 02 08
    print ACE "Anatomy_term : \"WBbt:$theHash{anatomy_term}{value}\"\n";
    print ACE $ace_entry;
#     if ($theHash{sequence}{value} eq 'no') {       # if no entry, use the Gene (locus)
#       print ACE "Locus : \"$theHash{locus}{value}\"\n";
#       print ACE $ace_entry;
#     } else { # if ($theHash{sequence}{value})      # if there's a sequence
#       if ($theHash{sequence}{value} !~ m/[ ,]/) {  # and it's just one sequence, print it
#         print ACE "CDS : \"$theHash{sequence}{value}\"\n";	# changed Sequence to CDS
#         print ACE $ace_entry;
#       } else { # if ($theHash{sequence}{value} !~ m/[ ,]/)
#                                                         # if it's many sequences, print for each
#         my @sequences = split /, /, $theHash{sequence}{value};
#         foreach my $seq (@sequences) {                  # print separate sequences
#           print ACE "CDS : \"$seq\"\n";			# changed Sequence to CDS
#           print ACE $ace_entry;
#         } # foreach my $seq (@sequences)
#       } # else # if ($theHash{sequence}{value} !~ m/[ ,]/)
#     } # else # if ($theHash{sequence}{value})
  } # else # if ($theHash{sequence}{value})
  close (ACE) or die "Cannot close $ace_file : $!";
  $ace_file =~ s/^.*public_html//g;
#   print "See all ace.ace <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/data/go.ace\">data</A>.<BR>";
  print "See all ace.ace <A HREF=\"http://tazendra.caltech.edu/~postgres$ace_file\">data</A>.<BR>";
} # sub outputAce

sub populateXref {              # if not found, get ref_xref data to try to find alternate
  my $result = $dbh->prepare( "SELECT * FROM ref_xref;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { # loop through all rows returned
    $cgcHash{$row[0]} = $row[1];        # hash of cgcs, values pmids
    $pmHash{$row[1]} = $row[0];         # hash of pmids, values cgcs
  } # while (my @row = $result->fetchrow)
} # sub populateXref


#################  Formatting SECTION #################

#################  HTML SECTION #################

sub printHtmlForm {	# Show the form 
  &printHtmlFormStart();
  &printHtmlSection('GO_annotation');
  &printHtmlSelectCurators('curator');		# print html select blocks for curators
#   &printHtmlInputQuery('locus');        	# input with Query button
#   &printHtmlInput('sequence');        	
#   &printHtmlInput('synonym');        
# #   &printHtmlTextarea('sequence');
#   &printHtmlTextarea('protein');
  &printHtmlInputQuery('anatomy_term');        	# input with Query button
#   &printHtmlTextarea('anatomy_term');
  &printHtmlSection('Biological Process');
  &printHtmlTextareaBlock('bio_goterm');
  &printHtmlTextareaBlock('bio_goid');
  &printHtmlTextareaBlock('bio_paper_evidence');
#   &printHtmlTextareaBlock('bio_person_evidence');
#   &printHtmlTextareaBlock('bio_goinference');
  &printHtmlSelectBlock('bio_goinference');
  &printHtmlSelectBlock('bio_goinference_two');
  &printHtmlSelect2Block('bio_aoinference');
#   &printHtmlTextareaBlock('bio_similarity');
  &printHtmlTextareaBlock('bio_comment');
  &printHtmlSection('Cellular Component');
  &printHtmlTextareaBlock('cell_goterm');
  &printHtmlTextareaBlock('cell_goid');
  &printHtmlTextareaBlock('cell_paper_evidence');
#   &printHtmlTextareaBlock('cell_person_evidence');
#   &printHtmlTextareaBlock('cell_goinference');
  &printHtmlSelectBlock('cell_goinference');
  &printHtmlSelectBlock('cell_goinference_two');
  &printHtmlSelect2Block('cell_aoinference');
#   &printHtmlTextareaBlock('cell_similarity');
  &printHtmlTextareaBlock('cell_comment');
  &printHtmlSection('Molecular Function');
  &printHtmlTextareaBlock('mol_goterm');
  &printHtmlTextareaBlock('mol_goid');
  &printHtmlTextareaBlock('mol_paper_evidence');
#   &printHtmlTextareaBlock('mol_person_evidence');
#   &printHtmlTextareaBlock('mol_goinference');
  &printHtmlSelectBlock('mol_goinference');
  &printHtmlSelectBlock('mol_goinference_two');
  &printHtmlSelect2Block('mol_aoinference');
#   &printHtmlTextareaBlock('mol_similarity');
  &printHtmlTextareaBlock('mol_comment');
#   &printHtmlSection('Provisional Description');
#   &printHtmlTextarea('provisional');
#   &printHtmlTextarea('pro_paper_evidence');
  &printHtmlFormEnd();
} # sub printHtmlForm

sub printHtmlSection {          # print html sections
  my $text = shift;             # get name of section
  print "\n  "; for (0..12) { print '<TR></TR>'; } print "\n\n";                # divider
  print "  <TR><TD><STRONG><FONT SIZE=+1>$text : </FONT></STRONG></TD></TR>\n"; # section
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"column_number\" VALUE=\"$default_columns\">\n";
} # sub printHtmlSection

sub printHtmlInputQuery {       # print html inputs with queries (just pubID)
  my $type = shift;             # get type, use hash for html parts
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  
         SIZE=$theHash{$type}{html_size_main}></TD>
    <TD ALIGN="left"><INPUT TYPE="submit" NAME="action" VALUE="Query Postgres !"></TD>
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
  for my $i (1 .. $default_columns) {
    my $type = $main_type . $i;
    print "    <TD><TEXTAREA NAME=\"html_value_main_$type\" ROWS=$theHash{$main_type}{html_size_minor}
                  COLS=$theHash{$main_type}{html_size_main}>$theHash{$main_type}{$i}{html_value}</TEXTAREA></TD>\n";
  } # for my $i (1 .. $default_columns)
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlTextareaBlock 

sub printHtmlSelectCurators {	# print html select blocks for curators
  my $type = shift;
#   my @curators = ('Carol Bastiani', 'Ranjana Kishore', 'Erich Schwarz', 'Kimberly Van Auken', 'Juancarlos Testing');
  my @curators = ('Raymond Lee', 'Juancarlos Testing');
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
  EndOfText
  print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
  print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n";
    # if loaded or queried, show option, otherwise default to '' option
  foreach (@curators) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD>\n";
  print "    <TD ALIGN=left><INPUT TYPE=submit NAME=action VALUE=\"Add Column !\"></TD>\n  </TR>\n";
} # sub printHtmlSelectCurators

sub printHtmlSelectBlock {	# print html select blocks for inference type (set of three)
				# e.g. : &printHtmlSelectBlock('bio_goinference');
  my $main_type = shift;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $default_columns) {
    my $type = $main_type . $i;
    my @inferences = (' ', 'IDA -- Inferred from Direct Assay','IEA -- Inferred from Electronic
Annotation','IEP -- Inferred from Expression Pattern','IGI -- Inferred from Genetic
Interaction','IMP -- Inferred from Mutant Phenotype','IPI -- Inferred from Physical
Interaction','ISS -- Inferred from Sequence or structural Similarity','NAS -- Non-traceable Author
Statement','ND -- No Biological Data Available','IC -- Inferred by Curator','TAS -- Traceable Author
Statement');
    print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$main_type}{$i}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@inferences) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
  } # for my $i (1 .. $default_columns)
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlSelectBlock

sub printHtmlSelect2Block {	# print html select blocks for AO inference type (set of three)
				# e.g. : &printHtmlSelectBlock('bio_aoinference');
  my $main_type = shift;
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$main_type}{html_field_name} :</STRONG></TD>
  EndOfText
  for my $i (1 .. $default_columns) {
    my $type = $main_type . $i;
    my @inferences = (' ', 'Laser_ablation', 'Genetic_ablation', 'Blastomere_ablation', 'Genetic_mosaic', 'Expression_mosaic');		# new types for raymond 2004 02 24
#     my @inferences = (' ', 'molecular mosaics, tissue-specific expression', 'ablation by laser', 'genetic mosaics, loss of duplication', 'genetic mosaics, loss of transgene', 'in vitro assay', 'ablation by cell death gene');
    print "    <TD><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
    print "      <OPTION selected>$theHash{$main_type}{$i}{html_value}</OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@inferences) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n";
  } # for my $i (1 .. $default_columns)
  print <<"  EndOfText";
  </TR>
  EndOfText
} # sub printHtmlSelectBlock

sub printHtmlFormStart {        # beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/anatomy_term_curation.cgi">
  <TABLE>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <!--<INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !">-->
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR>
  EndOfText
} # sub printHtmlFormStart

sub printHtmlFormEnd {          # ending of form
  print <<"  EndOfText";
  <TR><TD COLSPAN=2> </TD></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <!--<INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !">-->
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR>
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

  @PGparameters = qw(curator anatomy_term);
  @PGsubparameters = qw( goterm goid paper_evidence person_evidence goinference
                         goinference_two aoinference comment);

#   @PGparameters = qw(curator anatomy_term
#                      bio_goterm bio_goid bio_paper_evidence bio_person_evidence bio_goinference
#                      bio_goinference_two bio_aoinference bio_similarity bio_comment
#                      cell_goterm cell_goid cell_paper_evidence cell_person_evidence cell_goinference 
#                      cell_goinference_two cell_aoinference cell_similarity cell_comment
#                      mol_goterm mol_goid mol_paper_evidence mol_person_evidence mol_goinference
#                      mol_goinference_two mol_aoinference mol_similarity mol_comment
#                     );

#   @PGparameters = qw(curator anatomy_term
#                      bio_goterm1 bio_goterm2 bio_goterm3 bio_goterm4
#                      bio_goid1 bio_goid2 bio_goid3 bio_goid4 
#                      bio_paper_evidence1 bio_paper_evidence2 bio_paper_evidence3 bio_paper_evidence4 
#                      bio_person_evidence1 bio_person_evidence2 bio_person_evidence3 bio_person_evidence4 
#                      bio_goinference1 bio_goinference2 bio_goinference3 bio_goinference4
#                      bio_goinference_two1 bio_goinference_two2 bio_goinference_two3 bio_goinference_two4
#                      bio_aoinference1 bio_aoinference2 bio_aoinference3 bio_aoinference4
#                      bio_similarity1 bio_similarity2 bio_similarity3 bio_similarity4
#                      bio_comment1 bio_comment2 bio_comment3 bio_comment4 
#                      cell_goterm1 cell_goterm2 cell_goterm3 cell_goterm4 
#                      cell_goid1 cell_goid2 cell_goid3 cell_goid4  
#                      cell_paper_evidence1 cell_paper_evidence2 cell_paper_evidence3 cell_paper_evidence4  
#                      cell_person_evidence1 cell_person_evidence2 cell_person_evidence3 cell_person_evidence4 
#                      cell_goinference1 cell_goinference2 cell_goinference3 cell_goinference4 
#                      cell_goinference_two1 cell_goinference_two2 cell_goinference_two3 cell_goinference_two4 
#                      cell_aoinference1 cell_aoinference2 cell_aoinference3 cell_aoinference4 
#                      cell_similarity1 cell_similarity2 cell_similarity3 cell_similarity4 
#                      cell_comment1 cell_comment2 cell_comment3 cell_comment4 
#                      mol_goterm1 mol_goterm2 mol_goterm3 mol_goterm4 
#                      mol_goid1 mol_goid2 mol_goid3 mol_goid4  
#                      mol_paper_evidence1 mol_paper_evidence2 mol_paper_evidence3 mol_paper_evidence4  
#                      mol_person_evidence1 mol_person_evidence2 mol_person_evidence3 mol_person_evidence4 
#                      mol_goinference1 mol_goinference2 mol_goinference3 mol_goinference4 
#                      mol_goinference_two1 mol_goinference_two2 mol_goinference_two3 mol_goinference_two4 
#                      mol_aoinference1 mol_aoinference2 mol_aoinference3 mol_aoinference4 
#                      mol_similarity1 mol_similarity2 mol_similarity3 mol_similarity4 
#                      mol_comment1 mol_comment2 mol_comment3 mol_comment4 
#                      provisional pro_paper_evidence
#                     );

  foreach my $field (@PGparameters) {
    $theHash{$field}{html_field_name} = '';
    $theHash{$field}{html_value} = '';
    $theHash{$field}{html_size_main} = '40';            # default width 40
    $theHash{$field}{html_size_minor} = '2';            # default height 2
  } # foreach my $field (@PGparameters)

  foreach my $field (@PGsubparameters) {
    my @subtypes = qw( bio_ cell_ mol_ );
    foreach my $subt ( @subtypes ) {
      my $field = $subt . $field;
      $theHash{$field}{html_field_name} = '';
      $theHash{$field}{html_value} = '';
      $theHash{$field}{html_size_main} = '40';            # default width 40
      $theHash{$field}{html_size_minor} = '2';            # default height 2
    } # foreach my $subt ( @subtypes )
  } # foreach my $field (@PGsubparameters)

  $theHash{curator}{html_field_name} = 'Curator';
  $theHash{anatomy_term}{html_field_name} = 'Anatomy ID (7 digits)';

    # individually create the section names for the tags for the html 
    # (these are not part of the general intialization in the foreach loop above)
  $theHash{bio_goterm}{html_field_name} = 'GO Term';
  $theHash{bio_goid}{html_field_name} = 'GO ID';
  $theHash{bio_paper_evidence}{html_field_name} = 'Paper Evidence (check it exists in <A HREF="http://www.wormbase.org/db/misc/paper?name=;class=Paper">WormBase</A>)';
  $theHash{bio_person_evidence}{html_field_name} = 'Person Evidence';
  $theHash{bio_goinference}{html_field_name} = 'GO Inference Type';
  $theHash{bio_goinference_two}{html_field_name} = 'GO Inference Type 2';
  $theHash{bio_aoinference}{html_field_name} = 'AO Inference Type';
#   $theHash{bio_similarity}{html_field_name} = 'Protein ID Evidence';
  $theHash{bio_comment}{html_field_name} = 'Comment';

  $theHash{cell_goterm}{html_field_name} = 'GO Term';
  $theHash{cell_goid}{html_field_name} = 'GO ID';
  $theHash{cell_paper_evidence}{html_field_name} = 'Paper Evidence (check it exists in <A HREF="http://www.wormbase.org/db/misc/paper?name=;class=Paper">WormBase</A>)';
  $theHash{cell_person_evidence}{html_field_name} = 'Person Evidence';
  $theHash{cell_goinference}{html_field_name} = 'GO Inference Type';
  $theHash{cell_goinference_two}{html_field_name} = 'GO Inference Type 2';
  $theHash{cell_aoinference}{html_field_name} = 'AO Inference Type';
#   $theHash{cell_similarity}{html_field_name} = 'Protein ID Evidence';
  $theHash{cell_comment}{html_field_name} = 'Comment';

  $theHash{mol_goterm}{html_field_name} = 'GO Term';
  $theHash{mol_goid}{html_field_name} = 'GO ID';
  $theHash{mol_paper_evidence}{html_field_name} = 'Paper Evidence (check it exists in <A HREF="http://www.wormbase.org/db/misc/paper?name=;class=Paper">WormBase</A>)';
  $theHash{mol_person_evidence}{html_field_name} = 'Person Evidence';
  $theHash{mol_goinference}{html_field_name} = 'GO Inference Type';
  $theHash{mol_goinference_two}{html_field_name} = 'GO Inference Type 2';
  $theHash{mol_aoinference}{html_field_name} = 'AO Inference Type';
#   $theHash{mol_similarity}{html_field_name} = 'Protein ID Evidence';
  $theHash{mol_comment}{html_field_name} = 'Comment';

#   $theHash{provisional}{html_field_name} = 'Provisional Description';
#   $theHash{pro_paper_evidence}{html_field_name} = 'Paper Evidence (check it exists in <A HREF="http://www.wormbase.org/db/misc/paper?name=;class=Paper">WormBase</A>)';
} # sub initializeHash

#################  HASH SECTION #################
