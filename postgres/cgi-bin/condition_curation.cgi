#!/usr/bin/perl -w

# Checkout conditions to curate.
#
# This form is essentially the same as the Phenotype curation form phenotype_curation.cgi
# The ``Save !'' and ``Load !'' buttons also don't work here.  17 values from WormBase 
# have been pre-entered, new ones are created by curators with the ``Curate !'' button 
# and the input of a new name (if old name, its values are loaded into the form)
# 2003 05 03
#
# Added XREF capability, by having error checking in &getHtml(); if there's an error the
# Update and New Entry buttons don't show up (since the entries would have trouble with the
# pg entry).  Whenever something could create something via XREF, it uses
# &checkXrefExist($pgtable); checks appropriate XREF table (that is, it looks at the
# _checked_out table to see if something exists, else error that it needs to be created
# which is because potentially two people could be accessing something thinking they are
# both creating it and accessing each other's creation), then looks at the specific XREF
# table that would be inserting a value (that value being the joinkey for the entry being
# edited), then checks if there's something there (else INSERT), in which case it checks
# if any of the entries match (to see if nothing needs to be done because it's already
# there) or if none match and needs to be appended (UPDATE).  pg commands that change
# stuff via XREF are pushed into @pg_xref array, and they are executed at the end of
# &dealPg();  2003 05 23


use strict;
use CGI;
use LWP::Simple;					# not in use
use LWP::UserAgent;					# not in use
use Jex; 	# getHtmlVar, mailer, untaint
use DBI;

  # connect to the testdb database
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $ua = LWP::UserAgent->new;				# not in use
$ua->agent("MinervaConditionCuration/0.1 ");	# not in use

my $blue = '#88ffcc';			# redefine blue to a mom-friendly color
my $red = '#ffaacc';			# redefine red to a mom-friendly color

our @pg_xref = ();			# array of commands to run through xref

my $query = new CGI;
our @RowOfRow;
my $MaxEntries = 20;

# our $default_pgcommand = "SELECT con_description.joinkey, con_description.con_description, con_comment.con_comment, con_checked_out.con_checked_out, con_curator.con_curator FROM con_description, con_comment, con_checked_out, con_curator WHERE con_description.joinkey = con_comment.joinkey AND con_description.joinkey = con_checked_out.joinkey AND con_description.joinkey = con_curator.joinkey ORDER BY con_description.joinkey; ";

our $default_pgcommand = "SELECT con_comment.joinkey, con_comment.con_comment, con_checked_out.con_checked_out, con_curator.con_curator FROM con_comment, con_checked_out, con_curator WHERE con_comment.joinkey = con_checked_out.joinkey AND con_comment.joinkey = con_curator.joinkey ORDER BY con_comment.joinkey; ";
				# default query

our $notchecked_pgcommand = "SELECT con_comment.joinkey, con_comment.con_comment, con_checked_out.con_checked_out, con_curator.con_curator FROM con_comment, con_checked_out, con_curator WHERE con_comment.joinkey = con_checked_out.joinkey AND con_comment.joinkey = con_curator.joinkey AND con_checked_out IS NULL ORDER BY con_comment.joinkey; ";

our $checked_pgcommand = "SELECT con_comment.joinkey, con_comment.con_comment, con_checked_out.con_checked_out, con_curator.con_curator FROM con_comment, con_checked_out, con_curator WHERE con_comment.joinkey = con_checked_out.joinkey AND con_comment.joinkey = con_curator.joinkey AND con_checked_out IS NOT NULL ORDER BY con_comment.joinkey; ";

our $notcurated_pgcommand = "SELECT con_comment.joinkey, con_comment.con_comment, con_checked_out.con_checked_out, con_curator.con_curator FROM con_comment, con_checked_out, con_curator WHERE con_comment.joinkey = con_checked_out.joinkey AND con_comment.joinkey = con_curator.joinkey AND con_curator IS NULL ORDER BY con_comment.joinkey; ";

our $curated_pgcommand = "SELECT con_comment.joinkey, con_comment.con_comment, con_checked_out.con_checked_out, con_curator.con_curator FROM con_comment, con_checked_out, con_curator WHERE con_comment.joinkey = con_checked_out.joinkey AND con_comment.joinkey = con_curator.joinkey AND con_curator IS NOT NULL ORDER BY con_comment.joinkey; ";




my $action;			# what user clicked
my $curator = "";		# initialize curator
my @PGparameters = qw(condition_name curator 
		      lifestage strain preparation temperature
		      genotype other
		      contains containedin precedes follows
		      reference remark
		      comment);		# vals for %theHash

# NOT IN USE, no hashes in ?Condition
# my @evidence_tags = qw(paper_evidence person_evidence author_evidence	# not in use
#                        similarity_evidence pmid_evidence
#                        accession_evidence protein_id_evidence
#                        cgc_data_submission go_inference_type);

my %theHash;			# hash that stores all gene function form related data



my $oop;			# temp variable used for getting HTML values

# files
my $save_file = '/home/postgres/public_html/cgi-bin/data/rnai_curation_save.txt';
				# not in use

&PrintHeader();			# print the HTML header
&initializeHash();		# init hash
&process();			# Do pretty much everything
&display(); 			# Select whether to show selectors for curator name
				# entries / page, and &ShowPgQuery();
&PrintFooter();			# print the HTML footer

sub display {
  if ( !($curator) ) { &ChoosePhenotypeAssay(); }
# 				# if no curator (first loaded), show selectors
#   else { &ShowPgQuery(); }	# if not, offer option to do Pg query instead
} # sub display

sub ChoosePhenotypeAssay {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi\">";
  print "<TABLE>\n";
  print "<TR><TD ALIGN=\"right\">Entries / Page :</TD>";
  print "<TD><INPUT NAME=\"entries_page\" SIZE=15 VALUE=\"$MaxEntries\"></TD></TR>";
  print "<TR><TD ALIGN=\"right\">Show Conditions : </TD><TD><SELECT NAME=\"show_what\" SIZE=5>\n";
  print "<OPTION>All</OPTION>\n";
  print "<OPTION>not Checked out</OPTION>\n";
  print "<OPTION>not Curated</OPTION>\n";
  print "<OPTION>Checked out</OPTION>\n";
  print "<OPTION>Curated</OPTION>\n";
  print "</SELECT></TD></TR>\n";
  print "<TR><TD>Select your Name among : </TD><TD><SELECT NAME=\"curator\" SIZE=8>\n";
  print "<OPTION>Igor Antoshechkin</OPTION>\n";
  print "<OPTION>Carol Bastiani</OPTION>\n";
  print "<OPTION>Raymond Lee</OPTION>\n";
  print "<OPTION>Andrei Petcherski</OPTION>\n";
  print "<OPTION>Erich Schwarz</OPTION>\n";
  print "<OPTION>Paul Sternberg</OPTION>\n";
  print "<OPTION>Kimberly Van Auken</OPTION>\n";
  print "<OPTION>Juancarlos Testing</OPTION>\n";
  print "</SELECT></TD>";
  print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Condition !\"></TD></TR><BR><BR>\n";
  print "</TABLE>\n";
  print "</FORM>\n";
} # sub ChoosePhenotypeAssay


sub process {			# Essentially do everything
  unless ($action = $query->param('action')) {
    $action = 'none'; 
  }

    # if new postgres command or curator chosen
  if ( ($action eq 'Pg !') || ($action eq 'Condition !') || ($action eq 'Class') || ($action eq 'Search !') ) {
      # get $curator not needed for rnai_curation.cgi
    if ( $query->param("curator") ) { $oop = $query->param("curator"); }
    else { $oop = "nodatahere"; }
    $curator = &untaint($oop);
      # get $pgcommand
    my $pgcommand;
    if ( $query->param("pgcommand") ) { $oop = $query->param("pgcommand"); }
    else { $oop = "nodatahere"; }
    $oop =~ s/>/&gt;/g;		# make into code to make through taint check
    $oop =~ s/</&lt;/g;		# make into code to make through taint check
    $pgcommand = &untaint($oop);
    $pgcommand =~ s/&gt;/>/g;	# put back into pg readable
    $pgcommand =~ s/&lt;/</g;	# put back into pg readable
    if (($action eq 'Condition !') || ($action eq 'Class')) { $pgcommand = $default_pgcommand; }
    if ( $query->param("search_term") ) { $oop = $query->param("search_term"); }
    else { $oop = "nodatahere"; }
    my $search_term = &untaint($oop);

      # get show_what (filter of which to show)
    if ( $query->param("show_what") ) { $oop = $query->param("show_what"); }
      else { $oop = "nodatahere"; }
    my $show_what = &untaint($oop);
    if ($show_what eq 'All') { $pgcommand = $default_pgcommand; }
    elsif ($show_what eq 'not Checked out') { $pgcommand = $notchecked_pgcommand; }
    elsif ($show_what eq 'not Curated') { $pgcommand = $notcurated_pgcommand; }
    elsif ($show_what eq 'Checked out') { $pgcommand = $checked_pgcommand; }
    elsif ($show_what eq 'Curated') { $pgcommand = $curated_pgcommand; }
#     else { print "<FONT COLOR=blue>ERROR : Show Conditions option in subroutine Process</FONT><BR>\n"; }
    else { 1; }

      # get $MaxEntries
    if ( $query->param("entries_page") ) { $oop = $query->param("entries_page"); }
    else { $oop = "20"; }
    $MaxEntries = &untaint($oop);
      # get $page number
    if ( $query->param("page") ) { $oop = $query->param("page"); }
    else { $oop = "1"; }
    my $page = &untaint($oop);
      # if page just loaded, and just signed on, use default with good tables
      # and PDF links.

#     if ($action eq 'Search !') {
#          # add into the pgcommand an additional AND to specify the joinkey
#        if ($query->param("search_term_value")) { $oop = $query->param("search_term_value"); }
#          else { $oop = 1; print "<FONT COLOR=blue>ERROR : no paper number chosen</FONT>"; }
#        if ($search_term eq 'name') { $search_term = 'phe_reference.joinkey'; }
#        elsif ($search_term eq 'synonym') { $search_term = 'phe_synonym.phe_synonym'; }
#        elsif ($search_term eq 'reference') { $search_term = 'phe_reference.phe_reference'; }
#        elsif ($search_term eq 'description') { $search_term = 'phe_description.phe_description'; }
#        elsif ($search_term eq 'checked_out') { $search_term = 'phe_checked_out.phe_checked_out'; }
#        elsif ($search_term eq 'curated_by') { $search_term = 'phe_curated_by.phe_curated_by'; }
#        else { $search_term = 1; print "<FONT COLOR=blue>ERROR : Search Term Invalid</FONT>"; }
# 
#        $pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey AND $search_term ~ '" . &untaint($oop) . "' ORDER BY phe_reference.joinkey; ";
#     } # if ($action eq 'Search !')

    if ($pgcommand eq "nodatahere") {
      				# if invalid postgres command
      print "You must enter a valid PG command<BR>\n"; 
    } elsif ($curator eq "nodatahere") {
      print "You must choose a curator name<BR>\n"; 
    } else { # if ($pgcommand eq "nodatahere") 
				# if valid command
				# make query, put in $result
      if ( $pgcommand !~ m/select/i ) {
        my $result = $dbh->do( "$pgcommand" ); 
				# if not a select, just show query box again
        print "PostgreSQL has processed it.<BR>\n";
      } else { # if ( $pgcommand !~ m/select/i ) 
				# if a select, process and display
        &processTable($page, $pgcommand);
      } # else # if ( $pgcommand !~ m/select/i ) 
    } # else # if ($pgcommand eq "nodatahere") 
  } # if ($action eq 'Pg !') 

    # this could be made part of above, if so chosen.
  elsif ($action eq 'Page !') {
    if ( $query->param("curator") ) { $oop = $query->param("curator"); }
    else { $oop = "nodatahere"; }
    $curator = &untaint($oop);
    if ( $query->param("entries_page") ) { $oop = $query->param("entries_page"); } else { $oop = "20"; }
    $MaxEntries = &untaint($oop);
    if ( $query->param("pgcommand") ) { $oop = $query->param("pgcommand"); }
    else { $oop = "nodatahere"; }
    $oop =~ s/>/&gt;/g;		# make into code to make through taint check
    $oop =~ s/</&lt;/g;		# make into code to make through taint check
    my $pgcommand = &untaint($oop);
    $pgcommand =~ s/&gt;/>/g;	# put back into pg readable
    $pgcommand =~ s/&lt;/</g;	# put back into pg readable
    if ( $query->param("page") ) { $oop = $query->param("page"); }
    else { $oop = "1"; }
    my $page = &untaint($oop);
    &processTable($page, $pgcommand);
  } # if ($action eq 'Page !') 

  elsif ( $action eq 'Create !') {	# almost same as Curate but create phenotype from pg sequence
    $curator = &getCuratorFromForm();
    my $valid = &createCondition();	# create a new condition from curator-chosen name
    if ($valid) { &printHtmlForm(); }	# if name is valid, print form
  } # if ( $action eq 'Create !')

  elsif ( ($action eq 'Curate !') || ($action eq 'Query !') ) {
    $curator = &getCuratorFromForm();
    &curatePopulate();
    &printHtmlForm();
  } # if ( ($action eq 'Curate !') || ($action eq 'Query !') )

  elsif ($action eq 'Reset !') {
    $curator = &getCuratorFromForm();
    &printHtmlForm();
  } # elsif ($action eq 'Reset !')

  elsif ($action eq 'Load !') {
    $curator = &getCuratorFromForm();
    &loadState();
  } # elsif ($action eq 'Load')

  elsif ( ($action eq 'Preview !') || ($action eq 'Save !') ) {
    $curator = &getCuratorFromForm();
    if ($action eq 'Preview !') { &preview(); }
    elsif ($action eq 'Save !') { &saveState(); } 
  } # elsif ( ($action eq 'Preview !') && ($action eq 'Save !') )

  elsif ( ($action eq 'Update !') || ($action eq 'New Entry !') ) {
    $curator = &getCuratorFromForm();
    &commitData();
  } # elsif ($action eq 'Preview !')

#   elsif ( $action eq 'Class' ) {
#     $curator = &getCuratorFromForm();
#     &processClassList();
#   } # elsif ( $action eq 'Class' )
} # sub process


sub getClassList {		# Link to WormBase objects and Minerva objects
  my ($class, $type) = @_;
  print "<TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?class=$class&class_type=WormBase&action=Class\" target=NEW>List of $class objects</a> in <a href=\"http://www.wormbase.org\" target=NEW>WormBase</a>.</TD>\n";

  if ($theHash{$type}{html_pg_link}) {				# if it needs to link to tazendra as well 
    my $curator_temp = $curator; $curator_temp =~ s/ /+/g;
    if ($theHash{$type}{html_pg_link} eq 'Condition') {		# for Conditions
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi?curator=$curator_temp&show_what=All&action=Condition+%21\" target=NEW>List of $class objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    if ($theHash{$type}{html_pg_link} eq 'Phenotype Assay') {	# for Phenotype Assays
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_assay_curation.cgi?curator=$curator_temp&show_what=All&action=Phenotype Assay+%21\" target=NEW>List of $class objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    if ($theHash{$type}{html_pg_link} eq 'Phenotype') {		# for Phenotypes
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?curator=$curator_temp&show_what=All&action=Phenotype+%21\" target=NEW>List of $class objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Anatomy_term') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi?class=$theHash{$type}{html_pg_link}&class_type=Minerva&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Life_stage') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi?class=$theHash{$type}{html_pg_link}&class_type=Minerva&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
#   $theHash{anatomy}{html_pg_link} = 'Anatomy_term';
#   $theHash{life_stage}{html_pg_link} = 'Life_stage';
    else { 1; }
  } # if ($theHash{$class}{html_pg_link})
} # sub getClassList

sub loadState {
  print "THIS DOESN'T WORK YET<BR>\n";
#   &loadFromFile();
#   &displayHtmlCuration();
} # sub loadState

sub saveState {
  print "THIS DOESN'T WORK YET<BR>\n";
#   &getHtml();
#   &displayVars();
#   &saveToFile();
} # sub saveState

sub getCuratorFromForm {
  if ( $query->param("curator") ) { $oop = $query->param("curator"); }
  else { $oop = "nodatahere"; }
  $curator = &untaint($oop);
  return $curator;
} # sub getCuratorFromForm

sub commitData {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi\">\n";
  &getHtml();
  &dealPg();
  print "</FORM>\n";
} # sub commitData {

sub dealPg {
  my @PGtables = qw( checked_out );
  foreach my $param (@PGparameters) { unless ($param eq 'condition_name') { push @PGtables, $param; } }
  my $joinkey = $theHash{condition_name}{html_value};
  print "<TABLE>\n";
  foreach my $pgtable (@PGtables) {
    my $color = $blue;
    if ($theHash{$pgtable}{html_value}) {	# if main tag has data
      if ($theHash{$pgtable}{pg_update}) {	# UPDATE
        my $result = $dbh->do( "UPDATE con_$pgtable SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
        print "<TR BGCOLOR=$color><TD>UPDATE con_$pgtable SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\'</TD></TR>\n"; 
        $result = $dbh->do( "UPDATE con_$pgtable SET con_$pgtable = '$theHash{$pgtable}{html_value}' WHERE joinkey = '$joinkey';" );
        print "<TR BGCOLOR=$color><TD>UPDATE con_$pgtable SET con_$pgtable = \'$theHash{$pgtable}{html_value}\' WHERE joinkey = \'$joinkey\'</TD></TR>\n"; }
      elsif ($theHash{$pgtable}{pg_insert}) {	# INSERT
        $color = $red;
        my $result = $dbh->do( "INSERT INTO con_$pgtable VALUES ('$joinkey\', '$theHash{$pgtable}{html_value}');" );
        print "<TR BGCOLOR=$color><TD>INSERT INTO con_$pgtable VALUES (\'$joinkey\', \'$theHash{$pgtable}{html_value}\')</TD></TR>\n"; }
      else { 					# ERROR
        print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
        print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD></TR>\n"; }
    } # if ($theHash{$pgtable}{html_value})
# NOT IN USE, no hashes in ?Condition
#     if ($theHash{$pgtable}{hash_type}) {	# if main tag has a hash type
#       if ($theHash{$pgtable}{hash_type} eq 'Evidence') {
#         foreach my $evidence_tag (@evidence_tags) {
#           my $hash_tag = $pgtable . '_' . $evidence_tag;
#           if ($theHash{$hash_tag}{html_value}) {
#             $color = $blue;
#             if ($theHash{$hash_tag}{pg_update}) {	# UPDATE
#               my $result = $dbh->do( "UPDATE con_evi_$evidence_tag SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND con_main_tag = 'con_$pgtable';" );
#               print "<TR BGCOLOR=$color><TD>UPDATE con_evi_$evidence_tag SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\' AND con_main_tag = \'con_$pgtable\'</TD></TR>\n"; 
#               $result = $dbh->do( "UPDATE con_evi_$evidence_tag SET con_evi_$evidence_tag = '$theHash{$hash_tag}{html_value}' WHERE joinkey = '$joinkey' AND con_main_tag = 'con_$pgtable';" );
#               print "<TR BGCOLOR=$color><TD>UPDATE con_evi_$evidence_tag SET con_evi_$evidence_tag = \'$theHash{$hash_tag}{html_value}\' WHERE joinkey = \'$joinkey\' AND con_main_tag = \'con_$pgtable\'</TD></TR>\n"; }
#             elsif ($theHash{$hash_tag}{pg_insert}) {	# INSERT
#               $color = $red;
#               my $result = $dbh->do( "INSERT INTO con_evi_$evidence_tag VALUES ('$joinkey', 'con_$pgtable', '$theHash{$hash_tag}{html_value}');" );
#               print "<TR BGCOLOR=$color><TD>INSERT INTO con_evi_$evidence_tag VALUES (\'$joinkey\', \'con_$pgtable\', \'$theHash{$hash_tag}{html_value}\')</TD></TR>\n"; }
#             else {					# ERROR
#               print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
#               print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
#               print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD>\n"; }
# 	  } # if ($theHash{$hash_tag}{html_value})
#         } # foreach my $evidence_tag (@evidence_tags)
#       } # if ($theHash{$pgtable}{hash_type} eq 'Evidence')
#     } # if ($theHash{$pgtable}{hash_type})
  } # foreach my $pgtable (@PGtables)
  foreach my $pg_xref (@pg_xref) {			# for each command to be exec'ed through xref
    print "<TR BGCOLOR='orange'><TD>$pg_xref</TD></TR>\n";	# display it in orange
    my $result = $dbh->do( "$pg_xref" );			# execute it
  } # foreach my $pg_xref (@pg_xref)
  print "</TABLE>\n";
  print "<P>The phenotype assay <FONT COLOR=green>$theHash{condition_name}{html_value}</FONT> has been Curated by $curator.<BR>\n";
} # sub dealPg

sub preview {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator\" VALUE=\"$curator\">\n";
  my $errors_in_data = &getHtml();
#   &displayVars();
  &showButtonChoice($errors_in_data);
  print "</FORM>\n";
} # sub preview

sub checkXrefExist {
  my $pgtable = shift;			# table whose data's xref we want to check
  my $pgtype = '';			# 3-letter pg table set identifier (con for Condition)
  my $type = $theHash{$pgtable}{xref};			# type of xref
  my $value = $theHash{$pgtable}{html_value};		# value being passed in (which joinkeys to check in xref table)
  my $joinkey = $theHash{condition_name}{html_value};	# joinkey of entry (which values to check in xref table)
#   my %found; 	# key joinkey, value values  of query result on pg xref table
  my $pg_to_check;                      # pg_table xref checks
  my $error_in_xref_creation = '';	# error flag if a value is created via XREF

  if ($type eq 'Condition') {		# only Condition type XREFs in Condition model
    $pgtype = 'con';
    if ($pgtable eq 'containedin') { $pg_to_check = 'con_contains'; }		# which table to check xref
    elsif ($pgtable eq 'contains') { $pg_to_check = 'con_containedin'; }	# which table to check xref
    elsif ($pgtable eq 'precedes') { $pg_to_check = 'con_follows'; }		# which table to check xref
    elsif ($pgtable eq 'follows') { $pg_to_check = 'con_precedes'; }		# which table to check xref
  }
  else { 
    print "<TR BGCOLOR=red><TD>XREF</TD><TD></TD><TD></TD><TD></TD><TD>NOT A VALID XREF TYPE FOR ACEDB</TD><TD>$type</TD></TR>\n";
    $error_in_xref_creation++; }	# error warning and error flag

  print "<TR BGCOLOR='yellow'><TD>XREF</TD><TD>$type</TD><TD>$value</TD><TD>$pg_to_check</TD></TR>\n";
					# info message, type of check, type of acedb xref, values entered (to check), pgtable to check

  my @values = ();			# init set of values if many separated by |
  if ($value =~ m/|/) { @values = split/\|/, $value; } else { $values[0] = $value; }	# get values into array
  foreach my $value (@values) {		# for each value entered have to check each one
    $value =~ s/^\s+//g; $value =~ s/\s+$//g;						# strip spaces
    my $found_in_pg = '';		# flag if specific (pipe-separated) curator entered value
					# has an entry in the xref table (as a joinkey) with a (pg)
					# value matching this entry ($joinkey)
    my $stuff_in_pg_to_alter = '';	# if there's already a value in, it needs to be UPDATEd instead of INSERTed

    my $result = $dbh->prepare( "SELECT ${pgtype}_checked_out FROM ${pgtype}_checked_out WHERE joinkey = \'$value\';");	# check XREF entry exists
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my $found_full_entry;		# flag, if entry exists, doesn't need to be created
    while (my @row = $result->fetchrow) { if ($row[0]) { $found_full_entry = $row[0] } else { $found_full_entry = ' '; } }
    unless ($found_full_entry) {	# non-existing XREF, warn
      print "<TR BGCOLOR=red><TD>XREF</TD><TD>ERROR</TD><TD>$value</TD><TD>Populating a $type named '$value' which does not exist.  Please <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi?curator=$curator&action=Condition+%21\" target=NEW>CREATE</a> it first.</TD></TR>";
      $error_in_xref_creation++;	# error warning and error flag
      next;				# warning, so go to next set of values
    } # unless ($found_full_entry)

#     my $result = $dbh->prepare( "SELECT * FROM $pg_to_check WHERE $pg_to_check ~ \'$value\' AND joinkey = \'$joinkey\';" );
    $result = $dbh->prepare( "SELECT * FROM $pg_to_check WHERE joinkey = \'$value\';" );		# check XREF table 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     print "<TR><TD></TD><TD></TD><TD></TD><TD>SELECT * FROM $pg_to_check WHERE joinkey = \'$value\';</TD></TR>\n";
    while (my @row = $result->fetchrow) { 		# get xref values with that joinkey
      if ($row[0]) { 					# if there's a joinkey
        if ($row[1] =~ m/|/) { 				# if there are more than one value (pipe separated)
          my @values_in_xref = split/\|/, $row[1]; 	# split up values into separate values due to | separator
	  foreach my $value_in_xref (@values_in_xref) {	# for each of the values that belong to the chosen joinkey
            $value_in_xref =~ s/^\s+//g; $value_in_xref =~ s/\s+$//g;				# take out spaces
            if ($value_in_xref eq $joinkey) { $found_in_pg = $row[0]; }				# if match, say so
#             if ($value_in_xref eq $value) { print "<TR><TD>MATCH $value_in_xref $value</TD></TR>\n"; $found_in_pg = $row[0]; }
	  } # foreach my $value_in_xref (@values)
        } else { if ($row[1] eq $joinkey) { $found_in_pg = $row[0]; } }	# if only one value, check, if match, say so
	$stuff_in_pg_to_alter = $row[1];		# if there's data, save it to append to it
      } # if ($row[0])
    } # while (my @row = $result->fetchrow)

    unless ($stuff_in_pg_to_alter) {			# if there's no data, need to create
      print "<TR BGCOLOR='orange'><TD>XREF</TD><TD>CREATE</TD><TD>$value</TD><TD>INSERT INTO $pg_to_check VALUES ('$value', '$joinkey');</TD></TR>\n";
      push @pg_xref, "INSERT INTO $pg_to_check VALUES ('$value', '$joinkey');" }		# pass to array to exec in &dealPg();
    else {						# if there's data
      if ($found_in_pg) {				# data already matches
        print "<TR BGCOLOR='orange'><TD>XREF</TD><TD></TD><TD>$value</TD><TD>VALUE already in PG</TD></TR>\n"; }
      else {						# new data, append
        print "<TR BGCOLOR='orange'><TD>XREF</TD><TD>UPDATE</TD><TD>$value</TD><TD>UPDATE $pg_to_check SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';</TD></TR>\n";
        print "<TR BGCOLOR='orange'><TD>XREF</TD><TD>UPDATE</TD><TD>$value</TD><TD>UPDATE $pg_to_check SET $pg_to_check = \'${stuff_in_pg_to_alter}|$joinkey\' WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';</TD></TR>\n"; 
        push @pg_xref, "UPDATE $pg_to_check SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';";							# pass to array to exec in &dealPg();
        push @pg_xref, "UPDATE $pg_to_check SET $pg_to_check = \'${stuff_in_pg_to_alter}|$joinkey\' WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';";					# pass to array to exec in &dealPg();
      }
    } # else # unless ($stuff_in_pg_to_alter)

#       my $result = $dbh->prepare( "SELECT con_$pgtable FROM con_$pgtable WHERE joinkey = '$joinkey';");
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       my $found;                                # this con_$pgtable
#       while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = ' '; } }
#       if ($found)                     # UPDATE

#       $result = $dbh->do( "INSERT INTO con_checked_out VALUES ('$joinkey', '$curator');" );
#       $result = $dbh->do( "INSERT INTO con_curator VALUES ('$joinkey', NULL);" );
#       $result = $dbh->do( "INSERT INTO con_comment VALUES ('$joinkey', 'Created by $curator');" );

#     foreach my $key_in_xref (sort keys %found) {
#       foreach my $value_in_xref ( @{ $found{$key_in_xref} } ) {
#         $value_in_xref =~ s/^\s+//g; $value_in_xref =~ s/\s+$//g;
#         if ($value_in_xref eq $value) { print "<TR><TD>MATCH $value_in_xref $value</TD></TR>\n"; $found = $key_in_xref; }
#       }
#     }
  } # foreach my $value (@values)

# my $found = 'blank';      # temp
#   print "<TR BGCOLOR='yellow'><TD>XREF</TD><TD>$pgtable</TD><TD>$type</TD><TD>$value</TD><TD>$pg_to_check</TD></TR>\n";

#   my @values = ();			# init set of values if many separated by |
#   if ($value =~ m/|/) { @values = split/\|/, $value; } else { $values[0] = $value; }
#   foreach my $value (@values) {
#     my $found = 'new value';
#     foreach my $key_in_xref (sort keys %found) {
#       foreach my $value_in_xref ( @{ $found{$key_in_xref} } ) {
#         if ($value_in_xref eq $value) { print "<TR><TD>MATCH $value_in_xref $value</TD></TR>\n"; $found = $key_in_xref; }
#       }
#     }
#     print "<TR><TD>$joinkey</TD><TD>$value</TD><TD>$found</TD></TR>\n";
#   } # foreach my $value (@values)

#            Relationship    Contains        ?Condition XREF Contained_in
#                            Contained_in    ?Condition XREF Contains
#                            Precedes        ?Condition XREF Follows
#                            Follows         ?Condition XREF Precedes
  return $error_in_xref_creation;	# return flag if there were errors
} # sub checkXrefExist

sub getHtml {
  my $there_are_errors_flag = '';
  my @PGtables = qw( checked_out );
  foreach my $param (@PGparameters) { unless ($param eq 'condition_name') { push @PGtables, $param; } }
  ($oop, $theHash{condition_name}{html_value}) = &getHtmlVar($query, 'condition_name');
  my $joinkey = $theHash{condition_name}{html_value};
  print "<TABLE>";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"condition_name\" VALUE=\"$joinkey\">\n";
  print "<TR><TD></TD><TD>NAME</TD><TD>$joinkey</TD></TR>\n";
  foreach my $pgtable (@PGtables) {
    my $color = $blue;
    ($oop, $theHash{$pgtable}{html_value}) = &getHtmlVar($query, $pgtable);
    if ($theHash{$pgtable}{html_value}) {	# if tag has value
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"$pgtable\" VALUE=\"$theHash{$pgtable}{html_value}\">\n";
      my $result = $dbh->prepare( "SELECT con_$pgtable FROM con_$pgtable WHERE joinkey = '$joinkey';");
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my $found;                                # this con_$pgtable
      while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = ' '; } }
      if ($found) {                     # UPDATE
        print "<TR BGCOLOR=$color><TD>UPDATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>\n";
        $theHash{$pgtable}{pg_update}++;
      } else { # if ($found)            # INSERT
        $color = $red;
        print "<TR BGCOLOR=$color><TD>CREATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>\n";
        $theHash{$pgtable}{pg_insert}++;
      } # else # if ($found)
      if ( $theHash{$pgtable}{xref} ) {         # if there's an XREF
        if ( $theHash{$pgtable}{xref} eq 'Condition' ) {
#           print "<TR><TD></TD><TD>XREF TYPE</TD><TD>$theHash{$pgtable}{xref}</TD></TR>\n";
          my $error_in_xref_creation = &checkXrefExist($pgtable);
	  if ($error_in_xref_creation) { $there_are_errors_flag .= "$error_in_xref_creation|"; }
          }
        else { print "<TR BGCOLOR=red><TD>NOT A VALID XREF TYPE FOR ACEDB</TD></TR>\n"; $there_are_errors_flag .= 'invalidXref|'; }
      } # if ( $theHash{$pgtable}{xref} )
    } # if ($theHash{$pgtable}{html_value})
# NOT IN USE, no hashes in ?Condition
#     if ($theHash{$pgtable}{hash_type}) {
#       if ($theHash{$pgtable}{hash_type} eq 'Evidence') {	# if tag has evidence hash
#         foreach my $evidence_tag (@evidence_tags) {
#           my $hash_tag = $pgtable . '_' . $evidence_tag;
#           ($oop, $theHash{$hash_tag}{html_value}) = &getHtmlVar($query, $hash_tag);
#           if ($theHash{$hash_tag}{html_value}) {
#             $color = $blue;
#             print "<INPUT TYPE=\"HIDDEN\" NAME=\"$hash_tag\" VALUE=\"$theHash{$hash_tag}{html_value}\">\n";
#             my $result = $dbh->prepare( "SELECT con_evi_$evidence_tag FROM con_evi_$evidence_tag WHERE joinkey = '$joinkey' AND con_main_tag = 'con_$pgtable';" );
#             $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#             my $found;                          # this con_$pgtable
#             while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = ' '; } }
#             if ($found) {                       # UPDATE
#               print "<TR BGCOLOR=$color><TD>UPDATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
#               print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
#               $theHash{$hash_tag}{pg_update}++;
#             } else { # if ($found)              # INSERT
#               $color = $red;
#               print "<TR BGCOLOR=$color><TD>CREATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
#               print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
#               $theHash{$hash_tag}{pg_insert}++;
#             } # else # if ($found)
#           } # if ($theHash{$hash_tag}{html_value})
#         } # foreach my $evidence_tag (@evidence_tags)
#       } # if ($theHash{$pgtable}{hash_type} eq 'Evidence')
#     } # if ($theHash{$pgtable}{hash_type})
  } # foreach my $pgtable (@PGparameters)
  print "</TABLE>";
  return $there_are_errors_flag;		# if there are errors, return flag to not allow button to continue from preview
} # sub getHtml

# sub saveToFile {
#   foreach my $val (sort keys %variables) {
#     $variables{$val} =~ s/\t/TABREPLACEMENT/g;
#   } # foreach my $val (sort keys %variables)
#   my $vals_to_save = $variables{pubID} . "\t" . $variables{pdffilename} . "\t" .
# $variables{reference} . "\t" . $variables{rnai} . "\t" . $variables{comment};
#   open (SAVE, ">$save_file") or die "cannot create $save_file : $!";
#     # Saving, not as file, but as list
#   print SAVE "$vals_to_save\n";
#   close SAVE or die "Cannot close $save_file : $!";
# } # sub saveToFile

# sub loadFromFile {
#   undef $/;
#   open (SAVE, "<$save_file") or die "cannot open $save_file : $!";
#   my $vals_to_save = <SAVE>;
#   close SAVE or die "Cannot close $save_file : $!";
#   $/ = "\n";
#   my @vals_to_save = split/\t/, $vals_to_save;
#   foreach (@vals_to_save) { $_ =~ s/TABREPLACEMENT/\t/g; }
#   $variables{pubID} = $vals_to_save[0];
#   $variables{pdffilename} = $vals_to_save[1];
#   $variables{reference} = $vals_to_save[2];
#   $variables{rnai2} = $vals_to_save[3];
#   $variables{comment} = $vals_to_save[4];
# } # sub loadFromFile

sub showButtonChoice {
  my $errors_in_data = shift;
  if ($errors_in_data) { print "There are ERRORS in your data.  Please see the <FONT COLOR=red>RED</FONT> ERROR messages<BR>\n"; return; }
  my $found = &findIfPgEntry('curator'); 
  if ($found) {
    print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update !\">\n";
  } else { # if ($found)
    print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"New Entry !\">\n";
  } # else # if ($found)
} # sub showButtonChoice

sub findIfPgEntry {     # look at postgresql by pubID (joinkey) to see if entry exists
        # use the pubID and the curator table to see if there's an entry already
  my $phe_table = shift;                # figure out which table to check for data from
  my $result = $dbh->prepare( "SELECT * FROM con_$phe_table WHERE joinkey = '$theHash{condition_name}{html_value}';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row; my $found;
  while (@row = $result->fetchrow) { if ($row[1]) { $found = $row[0] } else { $found = ' '; } }
    # if there's null or blank data, change it to a space so it will update, not insert
  return $found;
} # sub FindIfPgEntry

sub createCondition {		# almost same as curatePopulate, 
				# but creates a new Condition from curator value
#   my $result = $dbh->prepare( "SELECT nextval('con_seq');" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   my @row = $result->fetchrow;
#   my $number = $row[0]; my $joinkey;
#   if ($number < 10) { $joinkey = 'WBassay000000' . $number; }
#   elsif ($number < 100) { $joinkey = 'WBassay00000' . $number; }
#   elsif ($number < 1000) { $joinkey = 'WBassay0000' . $number; }
#   elsif ($number < 10000) { $joinkey = 'WBassay000' . $number; }
#   elsif ($number < 100000) { $joinkey = 'WBassay00' . $number; }
#   elsif ($number < 1000000) { $joinkey = 'WBassay0' . $number; }
#   else { $joinkey = 'WBassay' . $number; }
  if ( $query->param("condition_name") ) { $oop = $query->param("condition_name"); }
  else { $oop = "nodatahere"; }
  my $joinkey = &untaint($oop);
  my $valid = 0;			# created invalid by default
  if ($joinkey eq 'nodatahere') { 	# if curator didn't pick a name
    print "You must enter a name for the new Condition<BR>\n"; }
  else {					# if name picked
    $valid = 1;
    my %conditions;			# condition names already in use
    my $result = $dbh->prepare( "SELECT DISTINCT joinkey FROM con_checked_out;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $conditions{$row[0]}++; }
    $theHash{condition_name}{html_value} = $joinkey;
    if ($conditions{$joinkey}) { 	# if condition already created, don't create
      print "<B><FONT COLOR=red>Condition $joinkey has already been created, the values will be loaded</FONT></B><P>\n"; }
    else {				# if condition new, INSERT values
      $result = $dbh->do( "INSERT INTO con_checked_out VALUES ('$joinkey', '$curator');" );
      $result = $dbh->do( "INSERT INTO con_curator VALUES ('$joinkey', NULL);" );
      $result = $dbh->do( "INSERT INTO con_comment VALUES ('$joinkey', 'Created by $curator');" );
#       $result = $dbh->do( "INSERT INTO con_description VALUES ('$joinkey', NULL);" );
      print "You have Created Condition : $theHash{condition_name}{html_value}<BR>\n";
    }
    &loadFromPg();
  }
  return $valid;
} # sub createCondition

sub curatePopulate {
  (my $oop, $theHash{condition_name}{html_value}) = &getHtmlVar($query, 'condition_name');
  my $result = $dbh->do( "UPDATE con_checked_out SET con_checked_out = \'$curator\' WHERE joinkey = \'$theHash{condition_name}{html_value}\';" );
  $result = $dbh->do( "UPDATE con_checked_out SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$theHash{condition_name}{html_value}\';" );
  print "You have Checked Out Condition : $theHash{condition_name}{html_value}<BR>\n";
  &loadFromPg();
} # sub curatePopulate

sub loadFromPg {
  my @PGtables; 
  foreach my $param (@PGparameters) { unless ($param eq 'condition_name') { push @PGtables, $param; } }
  my $joinkey = $theHash{condition_name}{html_value};
  foreach my $pgtable (@PGtables) {
    my $result = $dbh->prepare( "SELECT con_$pgtable FROM con_$pgtable WHERE joinkey = \'$theHash{condition_name}{html_value}\';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    $theHash{$pgtable}{html_value} = $row[0];
# NOT IN USE, no hashes in ?Condition
#     if ($theHash{$pgtable}{hash_type}) {
#       if ($theHash{$pgtable}{hash_type} eq 'Evidence') {
#         foreach my $evidence_tag (@evidence_tags) {
#           my $hash_tag = $pgtable . '_' . $evidence_tag;
#           $result = $dbh->prepare( "SELECT con_evi_$evidence_tag FROM con_evi_$evidence_tag WHERE joinkey = \'$joinkey\' AND con_main_tag = 'con_$pgtable';" );
#           $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#           my @row = $result->fetchrow;
#           $theHash{$hash_tag}{html_value} = $row[0]; } }
#     } # if ($theHash{$pgtable}{hash_type})
  } # foreach my $pgtable (@PGtables)
} # sub loadFromPg


sub processTable {
	# Take in pgcommand from hidden field or from Pg ! button
	# Take in page number from Page ! button or 1 as default
	# Process sql query 
	# Output number of results as well as sql query
	# output page selector as well as selected page results
    my $page = shift; my $pgcommand = shift;
    my $result = $dbh->prepare( "$pgcommand" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row;
    @RowOfRow = ();
    while (@row = $result->fetchrow) {	# loop through all rows returned
      push @RowOfRow, [@row];
    } # while (@row = $result->fetchrow) 

      # identity display
    if ($curator) { print "You claim to be $curator<P>\n"; }

      # show amount of results and compute page things
    print "There are " . ($#RowOfRow+1) . " results to \"$pgcommand\".<BR>\n";
    my $remainder = $#RowOfRow % $MaxEntries;
    my $HighNumber = $#RowOfRow - $remainder;
    my $dividednumber = $HighNumber / $MaxEntries;

#     &showSearch();

    &showCreatePhenotypeAssay();

      # process with this form, select new page, pass hidden values.
    print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi\">";
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator\" VALUE=\"$curator\">\n";
                                # pass curator value in hidden field
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"entries_page\" VALUE=\"$MaxEntries\">\n";
                                # pass entries_page value in hidden field
    print "<TABLE>\n";
    print "<TD>Select your page of " . ($dividednumber + 1) . " : </TD><TD><SELECT NAME=\"page\" SIZE=5> \n"; 
    for my $k ( 1 .. ($dividednumber + 1) ) {
      print "<OPTION>$k</OPTION>\n";
    } # for my $k ( 0 .. $dividednumber ) 
    print "</SELECT></TD><TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Page !\"></TD><BR><BR>\n";
    $pgcommand =~ s/>/&gt;/g;	# turn to code for html not to complain
    $pgcommand =~ s/</&lt;/g;	# turn to code for html not to complain
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"pgcommand\" VALUE=\"$pgcommand\">\n";
				# pass pgcommand value in hidden field
    $pgcommand =~ s/&gt;/>/g;	# turn back for pg not to complain
    $pgcommand =~ s/&lt;/</g;	# turn back for pg not to complain
    print "</TABLE>\n";
    print "</FORM>\n";
    print "<CENTER>\n";
    print "PAGE : $page<BR>\n";

      # show reference table
    print "<TABLE border=1 cellspacing=5>\n";
    print "<TR><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>comment</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curated</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
				# show headers if default
    for my $i ( (($page-1)*$MaxEntries) .. (($page*$MaxEntries)-1) ) {
				# for the amount of entries chosen in the chosen page
      my $row = $RowOfRow[$i];
      if ($row->[0]) {		# if there's an entry
        print "<TR>";
        print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator\" VALUE=\"$curator\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"condition_name\" VALUE=\"$row->[0]\">\n";

        for my $j ( 0 .. $#{$row} ) {
          unless ( ($row->[$j])  ) { print "<TD>&nbsp;</TD>\n"; }	# if nothing there, print a space
            else { print "<TD ALIGN=CENTER>$row->[$j]</TD>\n"; }	# if something there
        } # for my $j ( 0 .. $#{$row} ) 

        print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Curate !\"></TD>\n";
				# show button to ``Curate !''
        print "</FORM>\n";	# close each form
        print "</TR>\n";	# new table row
      } # if ($row->[0]) 	# if there's an entry
    } # for my $i ( 0 .. $#RowOfRow ) 
    print "<TR><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>comment</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curated</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
				# show headers if default
    print "</TABLE>\n";		# close table
    print "PAGE : $page<BR>\n";	# show page number again
    print "</CENTER>\n";
} # sub processTable 

sub showCreatePhenotypeAssay {
  print <<"EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi">
  <TABLE ALIGN=center><TR>
  <TD>Create a new Condition :<BR>(Name is required)</TD>
  <TD><INPUT SIZE=15 NAME="condition_name"></TD>
  <INPUT TYPE="HIDDEN" NAME="curator" VALUE="$curator">
  <TD><INPUT TYPE="submit" NAME="action" VALUE="Create !"></TD>
  </TR></TABLE>
  </FORM>
EndOfText
} # sub showCreatePhenotypeAssay


sub PrintHeader {
  print <<"EndOfText";
Content-type: text/html\n\n

<HTML>
<LINK rel="stylesheet" type="text/css" href="http://www.wormbase.org/stylesheets/wormbase.css">
  
<HEAD>
<TITLE>Condition Checkout / Curation</TITLE>
</HEAD>
  
<BODY bgcolor=#aaaaaa text=#000000 link=cccccc alink=eeeeee vlink=bbbbbb>
<HR>
<CENTER>Documentation <A HREF="http://tazendra.caltech.edu/~postgres/cgi-bin/docs/condition_curation_doc.txt" TARGET=NEW>here</A></CENTER><P>

<!--<CENTER><FONT COLOR=red><B>THIS FORM DOES NOT YET WORK</B></FONT></CENTER><P>-->
EndOfText
} # sub PrintHeader 

sub PrintFooter {
  print "</BODY>\n</HTML>\n";
} # sub PrintFooter 

########## HTML ########## 

sub printHtmlMenu {
  print <<"  EndOfText";
  <CENTER><A HREF="http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi">Site Map</A></CENTER>
  <CENTER><A HREF="http://tazendra.caltech.edu/~postgres/cgi-bin/docs/curationform_doc.cgi">Documentation</A></CENTER>
  <CENTER><A HREF="http://whitney.caltech.edu/~raymond/curation_guidlines.htm">Guidelines</A></CENTER>
  EndOfText
} # sub printHtmlMenu

sub printHtmlForm {		# display the html form
  &printHtmlFormStart();	# beginning of form 
  &printHtmlSection('General Info'); 
  &printHtmlSelectCurators('curator');	# print html select blocks for curators
  &printHtmlInputQuery('condition_name');	# input with Query button
  &printHtmlFormButtonMenu(); 	# buttons of form
  &printHtmlInput('lifestage');
  &printHtmlInput('strain');
  &printHtmlInput('preparation');
  &printHtmlInput('temperature');
  &printHtmlInput('genotype');
  &printHtmlInput('other');
  &printHtmlSection('Relationship');
  &printHtmlInput('contains');
  &printHtmlInput('containedin');		
  &printHtmlInput('precedes');		
  &printHtmlInput('follows');		
  &printHtmlSection('Reference');
  &printHtmlInput('reference');	
  &printHtmlInput('remark');	
  &printHtmlSection('Comments');
  &printHtmlTextarea('comment');
  &printHtmlFormButtonMenu(); 	# buttons of form
  &printHtmlFormEnd();		# ending of form 
} # sub printHtmlForm

sub printHtmlFormStart {	# beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  Please separate multiple entries with a "|" e.g. "AA1|AA6"
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi">
  <TABLE>
  EndOfText
} # sub printHtmlFormStart

sub printHtmlFormButtonMenu {	# buttons of form
  print <<"  EndOfText";
  <TR><TD COLSPAN=2> </TD></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
      <!--<INPUT TYPE="submit" NAME="action" VALUE="Options !">-->
      <INPUT TYPE="submit" NAME="action" VALUE="Save !">
      <INPUT TYPE="submit" NAME="action" VALUE="Load !">
      <INPUT TYPE="submit" NAME="action" VALUE="Reset !"></TD>
  </TR><TR><TD>&nbsp;</TD></TR><TR><TD>&nbsp;</TD></TR>
  EndOfText
} # sub printHtmlFormButtonMenu # buttons of form

sub printHtmlFormEnd {		# ending of form
  print <<"  EndOfText";
  </TABLE>
  </FORM>
  EndOfText
} # sub printHtmlFormEnd

sub printHtmlSection {		# print html sections
  my $text = shift;		# get name of section
  print "\n  "; for (0..12) { print '<TR></TR>'; } print "\n\n";		# divider
  print "  <TR><TD><STRONG><FONT SIZE=+1>$text : </FONT></STRONG></TD></TR>\n";	# section
} # sub printHtmlSection

sub printHtmlInputQuery {	# print html inputs with queries (just pubID)
  my $type = shift;		# get type, use hash for html parts
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; }	# clear NULL
  print <<"  EndOfText";	
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD><TABLE>
      <TR><TD></TD>
        <TD><INPUT NAME="$type" VALUE="$theHash{$type}{html_value}" 
	     SIZE=$theHash{$type}{html_size_main}></TD>
        <TD ALIGN="left"><INPUT TYPE="submit" NAME="action" VALUE="Query !"></TD>
      </TR>
      <TR><TD></TD><TD>$theHash{$type}{html_comment}</TD></TR>
    </TABLE></TD>
  </TR><TR><TD>&nbsp;</TD></TR>
  EndOfText
} # sub printHtmlInputQuery

sub printHtmlInput {		# print html inputs
  my $type = shift;		# get type, use hash for html parts
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; }	# clear NULL
  $theHash{$type}{html_size_main} += 20;	# make input boxes bigger
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} : </STRONG></TD>
    <TD>
      <TABLE>
        <TR>
          <TD> </TD>
          <TD><INPUT NAME="$type" VALUE="$theHash{$type}{html_value}" 
               SIZE=$theHash{$type}{html_size_main}></TD>
        </TR>
  EndOfText
  if ($theHash{$type}{html_comment}) { 		# if comment for html
    print "<TR><TD></TD><TD>$theHash{$type}{html_comment}</TD></TR>"; }
  if ($theHash{$type}{html_class_display}) { 	# if want pop-up display of class list
    &getClassList($theHash{$type}{html_class_display}, $type); }
  if ($theHash{$type}{hash_type}) {
    if ($theHash{$type}{hash_type} eq 'Aspect_info') { &printHtmlAspect($type); }
    if ($theHash{$type}{hash_type} eq 'Evidence') { &printHtmlEvidence($type); }
  }
  print <<"  EndOfText";
      </TABLE>
    </TD>
  </TR>
  EndOfText
  print "  <TR><TD>&nbsp;</TD></TR>";
} # sub printHtmlInput

sub printHtmlEmptyhash {	# print html without box, just hash
  my $type = shift;		# get type, use hash for html parts
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; }	# clear NULL
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD>
      <TABLE>
        <TR>
          <!--<TD><INPUT NAME="html_value_box_$type" TYPE="checkbox" VALUE="yes"></TD>-->
          <TD> </TD><TD> </TD>
  EndOfText
  unless ($theHash{$type}{html_mail_name} eq 'no one') {	
    # if someone to mail, print box and email address
    print <<"    EndOfText";
          <TD><INPUT NAME="html_mail_box_$type" TYPE="checkbox" 
               $theHash{$type}{html_mail_box} VALUE="yes"></TD>
          <TD> <FONT SIZE=-1>E-mail $theHash{$type}{html_mail_name}</FONT></TD>
    EndOfText
  } # unless ($theHash{$type}{html_mail_name} eq 'no one')
  print "        </TR>";
  if ($theHash{$type}{html_class_display}) { 	# if want pop-up display of class list
    &getClassList($theHash{$type}{html_class_display}, $type); }
  if ($theHash{$type}{hash_type}) {
    if ($theHash{$type}{hash_type} eq 'Aspect_info') { &printHtmlAspect($type); }
    if ($theHash{$type}{hash_type} eq 'Evidence') { &printHtmlEvidence($type); }
  }
  print <<"  EndOfText";
      </TABLE>
    </TD>
  </TR>
  <TR><TD>&nbsp;</TD></TR>
  EndOfText
} # sub printHtmlEmptyhash 

sub printHtmlTextarea {		# print html textareas
  my $type = shift;		# get type, use hash for html parts
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; }	# clear NULL
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD>
      <TABLE>
        <TR>
          <!--<TD><INPUT NAME="html_value_box_$type" TYPE="checkbox" VALUE="yes"></TD>-->
          <TD> </TD>
          <TD><TEXTAREA NAME="$type" ROWS=$theHash{$type}{html_size_minor}
               COLS=$theHash{$type}{html_size_main}>$theHash{$type}{html_value}</TEXTAREA></TD>
  EndOfText
  unless ($theHash{$type}{html_mail_name} eq 'no one') {	
    # if someone to mail, print box and email address
    print <<"    EndOfText";
          <TD><INPUT NAME="html_mail_box_$type" TYPE="checkbox" 
               $theHash{$type}{html_mail_box} VALUE="yes"></TD>
          <TD> <FONT SIZE=-1>E-mail $theHash{$type}{html_mail_name}</FONT></TD>
    EndOfText
  } # unless ($theHash{$type}{html_mail_name} eq 'no one')
  print "        </TR>";
  if ($theHash{$type}{html_comment}) { 		# if comment for html
    print "<TR><TD></TD><TD>$theHash{$type}{html_comment}</TD></TR>"; }
  if ($theHash{$type}{html_class_display}) { 	# if want pop-up display of class list
    &getClassList($theHash{$type}{html_class_display}, $type); }
  print <<"  EndOfText";
      </TABLE>
    </TD>
  </TR>
  EndOfText
  print "  <TR><TD>&nbsp;</TD></TR>";
} # sub printHtmlTextarea

# NOT IN USE, no hashes in ?Condition
# sub printHtmlEvidence {
#   my $type = shift;
#   print "    <TR><TD></TD><TD><TABLE cellspacing=5>";
#   foreach my $evidence_tag (@evidence_tags) {
#     if ( ($evidence_tag ne 'paper_evidence') && ($evidence_tag ne 'person_evidence') &&
#          ($evidence_tag ne 'author_evidence') ) { next; }	# skip if none of these 
#     my $hash_tag = $type . '_' . $evidence_tag;
#     unless ($theHash{$hash_tag}{html_value}) { $theHash{$hash_tag}{html_value} = ''; }
#     print <<"    EndOfText";
#         <TR>
#           <TD ALIGN="right">$evidence_tag :</TD>
#           <TD><INPUT NAME="${type}_${evidence_tag}" VALUE="$theHash{$hash_tag}{html_value}"
# 	       SIZE=$theHash{$evidence_tag}{html_size_main}></TD>
#           <!--<TD><TEXTAREA NAME="${type}_${evidence_tag}" ROWS=$theHash{$evidence_tag}{html_size_minor}
#                COLS=$theHash{$evidence_tag}{html_size_main}>$theHash{$hash_tag}{html_value}</TEXTAREA></TD>-->
#     EndOfText
#     if ($theHash{$evidence_tag}{html_comment}) { 		# if comment for html
#       print "<TD>$theHash{$evidence_tag}{html_comment}</TD>"; }
#     print "        </TR>\n";
#   } # foreach my $evidence_tag (@evidence_tags)
#   print "    </TABLE></TD></TR>";
# } # sub printHtmlEvidence

sub printHtmlSelectCurators {   # print html select blocks for curators
  my $type = shift;
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; }	# clear NULL
  my @curators = ('Igor Antoshechkin', 'Carol Bastiani', 'Wen Chen', 'Ranjana Kishore', 'Raymond Lee', 'Andrei Petcherski', 'Erich Schwarz', 'Paul Sternberg', 'Kimberly Van Auken', 'Juancarlos Testing');
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD><TABLE><TR><TD></TD><TD><SELECT NAME="curator" SIZE=1>
      <OPTION selected>$curator</OPTION>
  EndOfText
    # if loaded or queried, show option, otherwise default to '' option
  foreach (@curators) { print "      <OPTION>$_</OPTION>\n"; }
  print "    </SELECT></TD></TR></TABLE></TD></TR><TR><TD>&nbsp;</TD></TR>";
} # sub printHtmlSelectCurators


########## HTML ########## 

########## theHASH ########## 

sub initializeHash {
  # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects.
  # in case of new fields, add to @PGparameters array and create html_field_name entry in %theHash
  # and other %theHash fields as necessary.  if new email address, add to %emails.

  foreach my $field (@PGparameters) {
    $theHash{$field}{html_field_name} = '';		# name for display
    $theHash{$field}{html_value_box} = '';		# checkbox for ``yes'' instead of value
    $theHash{$field}{html_value} = '';			# value for field
    $theHash{$field}{html_mail_box} = 'checked';	# checkbox to mail default mail everyone
    $theHash{$field}{html_mail_name} = 'no one';	# default to mail no one
    $theHash{$field}{html_size_main} = '80';		# default width 80
    $theHash{$field}{html_size_minor} = '4';		# default height 4
  } # foreach my $field (@PGparameters)

# NOT IN USE, no hashes in ?Condition
#   foreach my $field (@evidence_tags) {
#     $theHash{$field}{html_field_name} = '';		# name for display
#     $theHash{$field}{html_value} = '';		# value for field
#     $theHash{$field}{html_size_main} = '40';		# default width 40
#     $theHash{$field}{html_size_minor} = '1';		# default height 1
#   } # foreach my $field (@evidence_tags)

  $theHash{curator}{html_field_name} = 'Curator &nbsp; &nbsp;(REQUIRED)';
  $theHash{condition_name}{html_field_name} = 'Condition Name &nbsp; &nbsp;(REQUIRED)';
  $theHash{reference}{html_field_name} = 'Reference';
  $theHash{reference}{html_size_minor} = '8';		# default height 8 for reference
  $theHash{definition}{html_field_name} = 'Definition';

    # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects
  $theHash{lifestage}{html_field_name} = 'Life Stage';
  $theHash{strain}{html_field_name} = 'Strain';
  $theHash{preparation}{html_field_name} = 'Preparation';
  $theHash{temperature}{html_field_name} = 'Temperature';
  $theHash{genotype}{html_field_name} = 'Genotype';
  $theHash{other}{html_field_name} = 'Other';
  $theHash{contains}{html_field_name} = 'Contains';
  $theHash{containedin}{html_field_name} = 'Contained In';
  $theHash{precedes}{html_field_name} = 'Precedes';
  $theHash{follows}{html_field_name} = 'Follows';
  $theHash{reference}{html_field_name} = 'Reference';
  $theHash{remark}{html_field_name} = 'Remark';
  $theHash{comment}{html_field_name} = 'Comment';

  $theHash{condition_name}{html_comment} = '';
  $theHash{lifestage}{html_comment} = 'e.g. "1-cell embryo"';
  $theHash{strain}{html_comment} = 'e.g. "AA1"';
  $theHash{preparation}{html_comment} = '';
  $theHash{temperature}{html_comment} = '';
  $theHash{genotype}{html_comment} = '';
  $theHash{other}{html_comment} = '';
  $theHash{contains}{html_comment} = 'e.g. Hill_2000_60hr';
  $theHash{containedin}{html_comment} = 'e.g. Hill_2000_60hr';
  $theHash{precedes}{html_comment} = 'e.g. Hill_2000_60hr';
  $theHash{follows}{html_comment} = 'e.g. Hill_2000_60hr';
  $theHash{reference}{html_comment} = 'e.g. [cgc4489]<BR>Defines the condition';
  $theHash{remark}{html_comment} = '';
  $theHash{comment}{html_comment} = 'This field is for postgreSQL only, not acedb';

  $theHash{lifestage}{html_class_display} = 'Life_stage';	# links to WormBase display
  $theHash{strain}{html_class_display} = 'Strain';
  $theHash{reference}{html_class_display} = 'Paper';
  $theHash{contains}{html_class_display} = 'Condition';
  $theHash{containedin}{html_class_display} = 'Condition';
  $theHash{precedes}{html_class_display} = 'Condition';
  $theHash{follows}{html_class_display} = 'Condition';

  $theHash{contains}{html_pg_link} = 'Condition';	# links to PG display
  $theHash{containedin}{html_pg_link} = 'Condition';
  $theHash{precedes}{html_pg_link} = 'Condition';
  $theHash{follows}{html_pg_link} = 'Condition';

  $theHash{contains}{xref} = 'Condition';		# this fields have this kind of xref's in acedb
  $theHash{containedin}{xref} = 'Condition';
  $theHash{precedes}{xref} = 'Condition';
  $theHash{follows}{xref} = 'Condition';

#   $theHash{assayphe}{hash_type} = 'Evidence';		# this fields have this kind of hashes
} # sub initializeHash
  
########## theHASH ########## 

# ?Condition Life_stage      ?Life_stage
#            Strain          ?Strain // added for Microarry_result [030127 krb]
#            Preparation     ?Text // added for Microarray_result [030127 krb]
#            Temperature     Int
#            Genotype        ?Text
#            Other           ?Text
#            Relationship    Contains        ?Condition XREF Contained_in
#                            Contained_in    ?Condition XREF Contains
#                            Precedes        ?Condition XREF Follows
#                            Follows         ?Condition XREF Precedes
#            Reference       ?Paper  //Defines the condition.
#            Remark          ?Text



sub showSearch {		# look for a specific number
  print <<"EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi">
  <TABLE><TR>
  <TD>Search for a specific term :</TD>
  <TD><INPUT NAME="search_term" TYPE="radio" VALUE="name" CHECKED>name<BR>
  <INPUT NAME="search_term" TYPE="radio" VALUE="synonym">synonym<BR>
  <INPUT NAME="search_term" TYPE="radio" VALUE="reference">reference<BR>
  <INPUT NAME="search_term" TYPE="radio" VALUE="description">description<BR>
  <INPUT NAME="search_term" TYPE="radio" VALUE="checked_out">checked out<BR>
  <INPUT NAME="search_term" TYPE="radio" VALUE="curated_by">curated by</TD>
  <TD><INPUT NAME="search_term_value" SIZE=40></TD>
  <INPUT TYPE="HIDDEN" NAME="curator" VALUE="$curator">
  <TD><INPUT TYPE="submit" NAME="action" VALUE="Search !"></TD>
  </TR></TABLE>
  </FORM>
EndOfText
} # sub showSearch

sub processClassList {
  if ( $query->param("class") ) { $oop = $query->param("class"); }
  else { $oop = 'Condition'; }
  my $class = &untaint($oop);

  if ( $query->param("class_type") ) { $oop = $query->param("class_type"); }
  else { $oop = 'WormBase'; }
  my $class_type = &untaint($oop);

  if ($class_type eq 'WormBase') {
    my $req = HTTP::Request->new(POST => 'http://www.wormbase.org/db/searches/query');
    $req->content_type('application/x-www-form-urlencoded');
    $req->content("class=$class");
  
    # Pass request to the user agent and get a response back
    my $res = $ua->request($req);
  
    # Check the outcome of the response
    if ($res->is_success) {
      print $res->content;
    } else {
      print "Bad luck this time\n";
    }
  } # if ($class_type eq 'WormBase')
  elsif ($class_type eq 'Minerva') {
    print "Class $class on Minerva has the following data : <BR>\n";
    print "<TABLE>\n";
    $class = lc($class);
    my $result = $dbh->prepare( "SELECT DISTINCT con_$class FROM con_$class;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      print "<TR BGCOLOR=$red><TD>$row[0]</TD></TR>\n";
    } # while (my @row = $result->fetchrow)
    print "</TABLE>\n";
  } # elsif ($class eq 'Minerva')
  else { 1; }
} # sub processClassList

sub printHtmlTextareaBoxless {		# print html textareas
  my $type = shift;		# get type, use hash for html parts
  if ($theHash{$type}{html_value} eq 'NULL') { $theHash{$type}{html_value} = ''; }	# clear NULL
  print <<"  EndOfText";
  <TR>
    <TD ALIGN="right"><STRONG>$theHash{$type}{html_field_name} :</STRONG></TD>
    <TD>
      <TABLE>
        <TR>
          <TD> </TD>
          <TD> </TD>
          <TD><TEXTAREA NAME="$type" ROWS=$theHash{$type}{html_size_minor}
               COLS=$theHash{$type}{html_size_main}>$theHash{$type}{html_value}</TEXTAREA></TD>
  EndOfText
  unless ($theHash{$type}{html_mail_name} eq 'no one') {	
    # if someone to mail, print box and email address
    print <<"    EndOfText";
          <TD><INPUT NAME="html_mail_box_$type" TYPE="checkbox" 
               $theHash{$type}{html_mail_box} VALUE="yes"></TD>
          <TD> <FONT SIZE=-1>E-mail $theHash{$type}{html_mail_name}</FONT></TD>
    EndOfText
  } # unless ($theHash{$type}{html_mail_name} eq 'no one')
  print <<"  EndOfText";
        </TR>
      </TABLE>
    </TD>
  </TR>
  EndOfText
} # sub printHtmlTextareaBoxless




