#!/usr/bin/perl -w

# Checkout phenotypes_assays to curate.
#
# This form is essentially the same as the Phenotype curation form phenotype_curation.cgi
# The ``Save !'' and ``Load !'' buttons also don't work here.  No values have been
# pre-entered, they are all created by curators with the ``Curate !'' button and the 
# pha_seq pg sequence.  Oddly, the Phenotype_assay objects have no names in acedb, so
# they have no names here either.  2003 05 03
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

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $ua = LWP::UserAgent->new;				# not in use
$ua->agent("MinervaPhenotypeAssayCuration/0.1 ");	# not in use

my $blue = '#88ffcc';			# redefine blue to a mom-friendly color
my $red = '#ffaacc';			# redefine red to a mom-friendly color

our @pg_xref = ();                      # array of commands to run through xref

my $query = new CGI;
our @RowOfRow;
my $MaxEntries = 20;

our $default_pgcommand = "SELECT pha_description.joinkey, pha_description.pha_description, pha_reference.pha_reference, pha_checked_out.pha_checked_out, pha_curator.pha_curator FROM pha_description, pha_reference, pha_checked_out, pha_curator WHERE pha_description.joinkey = pha_reference.joinkey AND pha_description.joinkey = pha_checked_out.joinkey AND pha_description.joinkey = pha_curator.joinkey ORDER BY pha_description.joinkey; ";

our $notchecked_pgcommand = "SELECT pha_description.joinkey, pha_description.pha_description, pha_reference.pha_reference, pha_checked_out.pha_checked_out, pha_curator.pha_curator FROM pha_description, pha_reference, pha_checked_out, pha_curator WHERE pha_description.joinkey = pha_reference.joinkey AND pha_description.joinkey = pha_checked_out.joinkey AND pha_description.joinkey = pha_curator.joinkey AND pha_checked_out IS NULL ORDER BY pha_description.joinkey; ";

our $checked_pgcommand = "SELECT pha_description.joinkey, pha_description.pha_description, pha_reference.pha_reference, pha_checked_out.pha_checked_out, pha_curator.pha_curator FROM pha_description, pha_reference, pha_checked_out, pha_curator WHERE pha_description.joinkey = pha_reference.joinkey AND pha_description.joinkey = pha_checked_out.joinkey AND pha_description.joinkey = pha_curator.joinkey AND pha_checked_out IS NOT NULL ORDER BY pha_description.joinkey; ";

our $notcurated_pgcommand = "SELECT pha_description.joinkey, pha_description.pha_description, pha_reference.pha_reference, pha_checked_out.pha_checked_out, pha_curator.pha_curator FROM pha_description, pha_reference, pha_checked_out, pha_curator WHERE pha_description.joinkey = pha_reference.joinkey AND pha_description.joinkey = pha_checked_out.joinkey AND pha_description.joinkey = pha_curator.joinkey AND pha_curator IS NULL ORDER BY pha_description.joinkey; ";

our $curated_pgcommand = "SELECT pha_description.joinkey, pha_description.pha_description, pha_reference.pha_reference, pha_checked_out.pha_checked_out, pha_curator.pha_curator FROM pha_description, pha_reference, pha_checked_out, pha_curator WHERE pha_description.joinkey = pha_reference.joinkey AND pha_description.joinkey = pha_checked_out.joinkey AND pha_description.joinkey = pha_curator.joinkey AND pha_curator IS NOT NULL ORDER BY pha_description.joinkey; ";

# our $default_pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey ORDER BY phe_reference.joinkey; ";
				# default query


my $action;			# what user clicked
my $curator = "";		# initialize curator
my @PGparameters = qw(phenotypeassay_name curator description assayphe
		      specialof generalof consistof partof
		      equivto similarto 
		      comment);		# vals for %theHash

my @evidence_tags = qw(paper_evidence person_evidence author_evidence
                       similarity_evidence pmid_evidence
                       accession_evidence protein_id_evidence
                       cgc_data_submission go_inference_type);

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
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi\">";
  print "<TABLE>\n";
  print "<TR><TD ALIGN=\"right\">Entries / Page :</TD>";
  print "<TD><INPUT NAME=\"entries_page\" SIZE=15 VALUE=\"$MaxEntries\"></TD></TR>";
  print "<TR><TD ALIGN=\"right\">Show Phenotype Assays : </TD><TD><SELECT NAME=\"show_what\" SIZE=5>\n";
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
  print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Phenotype Assay !\"></TD></TR><BR><BR>\n";
  print "</TABLE>\n";
  print "</FORM>\n";
} # sub ChoosePhenotypeAssay


sub process {			# Essentially do everything
  unless ($action = $query->param('action')) {
    $action = 'none'; 
  }

    # if new postgres command or curator chosen
  if ( ($action eq 'Pg !') || ($action eq 'Phenotype Assay !') || ($action eq 'Class') || ($action eq 'Search !') ) {
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
    if (($action eq 'Phenotype Assay !') || ($action eq 'Class')) { $pgcommand = $default_pgcommand; }
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
#     else { print "<FONT COLOR=blue>ERROR : Show Phenotype Assays option in subroutine Process</FONT><BR>\n"; }
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
				# if not a select, just show query box again
        my $result = $dbh->do( "$pgcommand" ); 
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
    &createPhenotypeAssay();
    &printHtmlForm();
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
    if ($theHash{$type}{html_pg_link} eq 'Phenotype Assay') {	# for Phenotype Assays
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi?curator=$curator_temp&show_what=All&action=Phenotype+Assay+%21\" target=NEW>List of $class objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    if ($theHash{$type}{html_pg_link} eq 'Phenotype') {		# for Phenotypes
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?curator=$curator_temp&show_what=All&action=Phenotype+%21\" target=NEW>List of $class objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Anatomy_term') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi?class=$theHash{$type}{html_pg_link}&class_type=Minerva&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Life_stage') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi?class=$theHash{$type}{html_pg_link}&class_type=Minerva&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
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
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi\">\n";
  &getHtml();
  &dealPg();
  print "</FORM>\n";
} # sub commitData {

sub dealPg {
  my @PGtables = qw( checked_out );
  foreach my $param (@PGparameters) { unless ($param eq 'phenotypeassay_name') { push @PGtables, $param; } }
  my $joinkey = $theHash{phenotypeassay_name}{html_value};
  print "<TABLE>\n";
  foreach my $pgtable (@PGtables) {
    my $color = $blue;
    if ($theHash{$pgtable}{html_value}) {	# if main tag has data
      if ($theHash{$pgtable}{pg_update}) {	# UPDATE
        my $result = $dbh->do( "UPDATE pha_$pgtable SET pha_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
        print "<TR BGCOLOR=$color><TD>UPDATE pha_$pgtable SET pha_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\'</TD></TR>\n"; 
        $result = $dbh->do( "UPDATE pha_$pgtable SET pha_$pgtable = '$theHash{$pgtable}{html_value}' WHERE joinkey = '$joinkey';" );
        print "<TR BGCOLOR=$color><TD>UPDATE pha_$pgtable SET pha_$pgtable = \'$theHash{$pgtable}{html_value}\' WHERE joinkey = \'$joinkey\'</TD></TR>\n"; }
      elsif ($theHash{$pgtable}{pg_insert}) {	# INSERT
        $color = $red;
        my $result = $dbh->do( "INSERT INTO pha_$pgtable VALUES ('$joinkey\', '$theHash{$pgtable}{html_value}');" );
        print "<TR BGCOLOR=$color><TD>INSERT INTO pha_$pgtable VALUES (\'$joinkey\', \'$theHash{$pgtable}{html_value}\')</TD></TR>\n"; }
      else { 					# ERROR
        print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
        print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD></TR>\n"; }
    } # if ($theHash{$pgtable}{html_value})
    if ($theHash{$pgtable}{hash_type}) {	# if main tag has a hash type
      if ($theHash{$pgtable}{hash_type} eq 'Evidence') {
        foreach my $evidence_tag (@evidence_tags) {
          my $hash_tag = $pgtable . '_' . $evidence_tag;
          if ($theHash{$hash_tag}{html_value}) {
            $color = $blue;
            if ($theHash{$hash_tag}{pg_update}) {	# UPDATE
              my $result = $dbh->do( "UPDATE pha_evi_$evidence_tag SET pha_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND pha_main_tag = 'pha_$pgtable';" );
              print "<TR BGCOLOR=$color><TD>UPDATE pha_evi_$evidence_tag SET pha_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\' AND pha_main_tag = \'pha_$pgtable\'</TD></TR>\n"; 
              $result = $dbh->do( "UPDATE pha_evi_$evidence_tag SET pha_evi_$evidence_tag = '$theHash{$hash_tag}{html_value}' WHERE joinkey = '$joinkey' AND pha_main_tag = 'pha_$pgtable';" );
              print "<TR BGCOLOR=$color><TD>UPDATE pha_evi_$evidence_tag SET pha_evi_$evidence_tag = \'$theHash{$hash_tag}{html_value}\' WHERE joinkey = \'$joinkey\' AND pha_main_tag = \'pha_$pgtable\'</TD></TR>\n"; }
            elsif ($theHash{$hash_tag}{pg_insert}) {	# INSERT
              $color = $red;
              my $result = $dbh->do( "INSERT INTO pha_evi_$evidence_tag VALUES ('$joinkey', 'pha_$pgtable', '$theHash{$hash_tag}{html_value}');" );
              print "<TR BGCOLOR=$color><TD>INSERT INTO pha_evi_$evidence_tag VALUES (\'$joinkey\', \'pha_$pgtable\', \'$theHash{$hash_tag}{html_value}\')</TD></TR>\n"; }
            else {					# ERROR
              print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD>\n"; }
	  } # if ($theHash{$hash_tag}{html_value})
        } # foreach my $evidence_tag (@evidence_tags)
      } # if ($theHash{$pgtable}{hash_type} eq 'Evidence')
    } # if ($theHash{$pgtable}{hash_type})
  } # foreach my $pgtable (@PGtables)
  foreach my $pg_xref (@pg_xref) {                      # for each command to be exec'ed through xref
    print "<TR BGCOLOR='orange'><TD>$pg_xref</TD></TR>\n";      # display it in orange
    my $result = $dbh->prepare( "$pg_xref" );                     # execute it
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  } # foreach my $pg_xref (@pg_xref)
  print "</TABLE>\n";
  print "<P>The phenotype assay <FONT COLOR=green>$theHash{phenotypeassay_name}{html_value}</FONT> has been Curated by $curator.<BR>\n";
} # sub dealPg

sub preview {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi\">\n";
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
  my $joinkey = $theHash{phenotypeassay_name}{html_value};	# joinkey of entry (which values to check in xref table)
  my $pg_to_check;                      # pg_table xref checks
  my $error_in_xref_creation = '';	# error flag if a value is created via XREF

  if ($type eq 'Phenotype_Assay') {
    $pgtype = 'pha';
    if ($pgtable eq 'specialof') { $pg_to_check = 'pha_generalof'; }
    elsif ($pgtable eq 'generalof') { $pg_to_check = 'pha_specialof'; }
    elsif ($pgtable eq 'consistof') { $pg_to_check = 'pha_partof'; }
    elsif ($pgtable eq 'partof') { $pg_to_check = 'pha_consistof'; }
    elsif ($pgtable eq 'equivto') { $pg_to_check = 'pha_equivto'; }
    elsif ($pgtable eq 'similarto') { $pg_to_check = 'pha_similarto'; } }
  elsif ($type eq 'Phenotype') {
    $pgtype = 'phe';
    if ($pgtable eq 'assayphe') { $pg_to_check = 'phe_assay_type'; } }
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
      if ($type eq 'Phenotype_Assay') {
        print "<TR BGCOLOR=red><TD>XREF</TD><TD>ERROR</TD><TD>$value</TD><TD></TD><TD>Populating a $type named '$value' which does not exist.  Please <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi?curator=$curator&action=Phenotype+Assay+%21\" target=NEW>CREATE</a> it first.</TD></TR>"; }
      elsif ($type eq 'Phenotype') {
        print "<TR BGCOLOR=red><TD>XREF</TD><TD>ERROR</TD><TD>$value</TD><TD></TD><TD>Populating a $type named '$value' which does not exist.  Please <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?curator=$curator&action=Phenotype+%21\" target=NEW>CREATE</a> it first.</TD></TR>"; }
      else {
        print "<TR BGCOLOR=red><TD>XREF</TD><TD>ERROR</TD><TD>$value</TD><TD></TD><TD>Populating something via XREF that does not exist.</TD></TR>"; }
      $error_in_xref_creation++;	# error warning and error flag
      next;				# warning, so go to next set of values
    } # unless ($found_full_entry)

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
      print "<TR BGCOLOR='orange'><TD>XREF</TD><TD>CREATE</TD><TD>$value</TD><TD></TD><TD>INSERT INTO $pg_to_check VALUES ('$value', '$joinkey');</TD></TR>\n";
      push @pg_xref, "INSERT INTO $pg_to_check VALUES ('$value', '$joinkey');" }		# pass to array to exec in &dealPg();
    else {						# if there's data
      if ($found_in_pg) {				# data already matches
        print "<TR BGCOLOR='orange'><TD>XREF</TD><TD></TD><TD>$value</TD><TD></TD><TD>VALUE already in PG</TD></TR>\n"; }
      else {						# new data, append
        print "<TR BGCOLOR='orange'><TD>XREF</TD><TD>UPDATE</TD><TD>$value</TD><TD></TD><TD>UPDATE $pg_to_check SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';</TD></TR>\n";
        print "<TR BGCOLOR='orange'><TD>XREF</TD><TD>UPDATE</TD><TD>$value</TD><TD></TD><TD>UPDATE $pg_to_check SET $pg_to_check = \'${stuff_in_pg_to_alter}|$joinkey\' WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';</TD></TR>\n"; 
        push @pg_xref, "UPDATE $pg_to_check SET con_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';";							# pass to array to exec in &dealPg();
        push @pg_xref, "UPDATE $pg_to_check SET $pg_to_check = \'${stuff_in_pg_to_alter}|$joinkey\' WHERE joinkey = \'$value\' AND $pg_to_check = \'$stuff_in_pg_to_alter\';";					# pass to array to exec in &dealPg();
      }
    } # else # unless ($stuff_in_pg_to_alter)
  } # foreach my $value (@values)

  return $error_in_xref_creation;	# return flag if there were errors
} # sub checkXrefExist

sub getHtml {
  my $there_are_errors_flag = '';
  my @PGtables = qw( checked_out );
  foreach my $param (@PGparameters) { unless ($param eq 'phenotypeassay_name') { push @PGtables, $param; } }
  ($oop, $theHash{phenotypeassay_name}{html_value}) = &getHtmlVar($query, 'phenotypeassay_name');
  my $joinkey = $theHash{phenotypeassay_name}{html_value};
  print "<TABLE>";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"phenotypeassay_name\" VALUE=\"$joinkey\">\n";
  print "<TR><TD></TD><TD>NAME</TD><TD>$joinkey</TD></TR>\n";
  foreach my $pgtable (@PGtables) {
    my $color = $blue;
    ($oop, $theHash{$pgtable}{html_value}) = &getHtmlVar($query, $pgtable);
    if ($theHash{$pgtable}{html_value}) {	# if tag has value
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"$pgtable\" VALUE=\"$theHash{$pgtable}{html_value}\">\n";
      my $result = $dbh->prepare( "SELECT pha_$pgtable FROM pha_$pgtable WHERE joinkey = '$joinkey';");
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my $found;                                # this pha_$pgtable
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
        if ( $theHash{$pgtable}{xref} eq 'Phenotype_Assay' ) {
          my $error_in_xref_creation = &checkXrefExist($pgtable);
          if ($error_in_xref_creation) { $there_are_errors_flag .= "$error_in_xref_creation|"; }
          }
        elsif ( $theHash{$pgtable}{xref} eq 'Phenotype' ) {
          my $error_in_xref_creation = &checkXrefExist($pgtable);
          if ($error_in_xref_creation) { $there_are_errors_flag .= "$error_in_xref_creation|"; }
          }
        else { print "<TR BGCOLOR=red><TD>NOT A VALID XREF TYPE FOR ACEDB</TD></TR>\n"; $there_are_errors_flag .= 'invalidXref|'; }
      } # if ( $theHash{$pgtable}{xref} )
    } # if ($theHash{$pgtable}{html_value})
    if ($theHash{$pgtable}{hash_type}) {
      if ($theHash{$pgtable}{hash_type} eq 'Evidence') {	# if tag has evidence hash
        foreach my $evidence_tag (@evidence_tags) {
          my $hash_tag = $pgtable . '_' . $evidence_tag;
          ($oop, $theHash{$hash_tag}{html_value}) = &getHtmlVar($query, $hash_tag);
          if ($theHash{$hash_tag}{html_value}) {
            $color = $blue;
            print "<INPUT TYPE=\"HIDDEN\" NAME=\"$hash_tag\" VALUE=\"$theHash{$hash_tag}{html_value}\">\n";
            my $result = $dbh->prepare( "SELECT pha_evi_$evidence_tag FROM pha_evi_$evidence_tag WHERE joinkey = '$joinkey' AND pha_main_tag = 'pha_$pgtable';" );
            $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
            my $found;                          # this pha_$pgtable
            while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = ' '; } }
            if ($found) {                       # UPDATE
              print "<TR BGCOLOR=$color><TD>UPDATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              $theHash{$hash_tag}{pg_update}++;
            } else { # if ($found)              # INSERT
              $color = $red;
              print "<TR BGCOLOR=$color><TD>CREATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              $theHash{$hash_tag}{pg_insert}++;
            } # else # if ($found)
          } # if ($theHash{$hash_tag}{html_value})
        } # foreach my $evidence_tag (@evidence_tags)
      } # if ($theHash{$pgtable}{hash_type} eq 'Evidence')
    } # if ($theHash{$pgtable}{hash_type})
  } # foreach my $pgtable (@PGparameters)
  print "</TABLE>";
  return $there_are_errors_flag;                # if there are errors, return flag to not allow button to continue from preview
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
  my $pha_table = shift;                # figure out which table to check for data from
  my $result = $dbh->prepare( "SELECT * FROM pha_$pha_table WHERE joinkey = '$theHash{phenotypeassay_name}{html_value}';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row; my $found;
  while (@row = $result->fetchrow) { if ($row[1]) { $found = $row[0] } else { $found = ' '; } }
    # if there's null or blank data, change it to a space so it will update, not insert
  return $found;
} # sub FindIfPgEntry

sub createPhenotypeAssay {	# almost same as curatePopulate, 
				# but creates a new phenotype assay from pg sequence
  my $result = $dbh->prepare( "SELECT nextval('pha_seq');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  my $number = $row[0]; my $joinkey;
  if ($number < 10) { $joinkey = 'WBassay000000' . $number; }
  elsif ($number < 100) { $joinkey = 'WBassay00000' . $number; }
  elsif ($number < 1000) { $joinkey = 'WBassay0000' . $number; }
  elsif ($number < 10000) { $joinkey = 'WBassay000' . $number; }
  elsif ($number < 100000) { $joinkey = 'WBassay00' . $number; }
  elsif ($number < 1000000) { $joinkey = 'WBassay0' . $number; }
  else { $joinkey = 'WBassay' . $number; }
  $theHash{phenotypeassay_name}{html_value} = $joinkey;
  $result = $dbh->do( "INSERT INTO pha_checked_out VALUES ('$joinkey', '$curator');" );
  $result = $dbh->do( "INSERT INTO pha_curator VALUES ('$joinkey', NULL);" );
  $result = $dbh->do( "INSERT INTO pha_reference VALUES ('$joinkey', 'Created by $curator');" );
  $result = $dbh->do( "INSERT INTO pha_description VALUES ('$joinkey', NULL);" );
  print "You have Created Phenotype Assay : $theHash{phenotypeassay_name}{html_value}<BR>\n";
  &loadFromPg();
} # sub createPhenotypeAssay

sub curatePopulate {
  (my $oop, $theHash{phenotypeassay_name}{html_value}) = &getHtmlVar($query, 'phenotypeassay_name');
  my $result = $dbh->do( "UPDATE pha_checked_out SET pha_checked_out = \'$curator\' WHERE joinkey = \'$theHash{phenotypeassay_name}{html_value}\';" );
  $result = $dbh->do( "UPDATE pha_checked_out SET pha_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$theHash{phenotypeassay_name}{html_value}\';" );
  print "You have Checked Out Phenotype Assay : $theHash{phenotypeassay_name}{html_value}<BR>\n";
  &loadFromPg();
} # sub curatePopulate

sub loadFromPg {
  my @PGtables; 
  foreach my $param (@PGparameters) { unless ($param eq 'phenotypeassay_name') { push @PGtables, $param; } }
  my $joinkey = $theHash{phenotypeassay_name}{html_value};
  foreach my $pgtable (@PGtables) {
    my $result = $dbh->prepare( "SELECT pha_$pgtable FROM pha_$pgtable WHERE joinkey = \'$theHash{phenotypeassay_name}{html_value}\';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    $theHash{$pgtable}{html_value} = $row[0];
    if ($theHash{$pgtable}{hash_type}) {
      if ($theHash{$pgtable}{hash_type} eq 'Evidence') {
        foreach my $evidence_tag (@evidence_tags) {
          my $hash_tag = $pgtable . '_' . $evidence_tag;
          $result = $dbh->prepare( "SELECT pha_evi_$evidence_tag FROM pha_evi_$evidence_tag WHERE joinkey = \'$joinkey\' AND pha_main_tag = 'pha_$pgtable';" );
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#           print "BLAH \$result = \$dbh->prepare( \"SELECT pha_evi_$evidence_tag FROM pha_evi_$evidence_tag WHERE joinkey = \'$joinkey\' AND pha_main_tag = 'pha_$pgtable';\" );<BR>\n";
          my @row = $result->fetchrow;
# print "LOADED $pgtable BLAH $hash_tag $row[0]<BR>\n";
          $theHash{$hash_tag}{html_value} = $row[0]; } }
    } # if ($theHash{$pgtable}{hash_type})
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
    print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi\">";
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
    print "<TR><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>description</TD><TD ALIGN=CENTER>reference</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curated</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
				# show headers if default
    for my $i ( (($page-1)*$MaxEntries) .. (($page*$MaxEntries)-1) ) {
				# for the amount of entries chosen in the chosen page
      my $row = $RowOfRow[$i];
      if ($row->[0]) {		# if there's an entry
        print "<TR>";
        print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator\" VALUE=\"$curator\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"phenotypeassay_name\" VALUE=\"$row->[0]\">\n";

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
    print "<TR><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>description</TD><TD ALIGN=CENTER>reference</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curated</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
				# show headers if default
    print "</TABLE>\n";		# close table
    print "PAGE : $page<BR>\n";	# show page number again
    print "</CENTER>\n";
} # sub processTable 

sub showCreatePhenotypeAssay {
  print <<"EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi">
  <TABLE ALIGN=center><TR>
  <TD>Create a new Phenotype Assay :</TD>
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
<TITLE>Phenotype Assay Checkout / Curation</TITLE>
</HEAD>
  
<BODY bgcolor=#aaaaaa text=#000000 link=cccccc alink=eeeeee vlink=bbbbbb>
<HR>
<CENTER>Documentation <A HREF="http://tazendra.caltech.edu/~postgres/cgi-bin/docs/phenotype_assay_curation_doc.txt" TARGET=NEW>here</A></CENTER><P>

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
  &printHtmlInputQuery('phenotypeassay_name');	# input with Query button
  &printHtmlFormButtonMenu(); 	# buttons of form
  &printHtmlInput('description');
#   &printHtmlEmptyhash('evidence');
  &printHtmlInput('assayphe');
  &printHtmlSection('Related Assay');
  &printHtmlInput('specialof');
  &printHtmlInput('generalof');		
  &printHtmlInput('consistof');		
  &printHtmlInput('partof');		
  &printHtmlInput('equivto');	
  &printHtmlInput('similarto');	
  &printHtmlSection('Comments');
  &printHtmlTextarea('comment');
  &printHtmlFormButtonMenu(); 	# buttons of form
  &printHtmlFormEnd();		# ending of form 
} # sub printHtmlForm

sub printHtmlFormStart {	# beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  Please separate multiple entries with a "|" e.g. "WBPerson625|WBPerson567"
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi">
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

sub printHtmlEvidence {
  my $type = shift;
  print "    <TR><TD></TD><TD><TABLE cellspacing=5>";
  foreach my $evidence_tag (@evidence_tags) {
#     if ( ($evidence_tag ne 'paper_evidence') && ($evidence_tag ne 'person_evidence') &&
#          ($evidence_tag ne 'author_evidence') ) { next; }	# skip if none of these 
    my $hash_tag = $type . '_' . $evidence_tag;
    unless ($theHash{$hash_tag}{html_value}) { $theHash{$hash_tag}{html_value} = ''; }
    print <<"    EndOfText";
        <TR>
          <TD ALIGN="right">$evidence_tag :</TD>
          <TD><INPUT NAME="${type}_${evidence_tag}" VALUE="$theHash{$hash_tag}{html_value}"
	       SIZE=$theHash{$evidence_tag}{html_size_main}></TD>
          <!--<TD><TEXTAREA NAME="${type}_${evidence_tag}" ROWS=$theHash{$evidence_tag}{html_size_minor}
               COLS=$theHash{$evidence_tag}{html_size_main}>$theHash{$hash_tag}{html_value}</TEXTAREA></TD>-->
    EndOfText
    if ($theHash{$evidence_tag}{html_comment}) { 		# if comment for html
      print "<TD>$theHash{$evidence_tag}{html_comment}</TD>"; }
    print "        </TR>\n";
  } # foreach my $evidence_tag (@evidence_tags)
  print "    </TABLE></TD></TR>";
} # sub printHtmlEvidence

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
  foreach my $field (@evidence_tags) {
    $theHash{$field}{html_field_name} = '';		# name for display
    $theHash{$field}{html_value} = '';			# value for field
    $theHash{$field}{html_size_main} = '40';		# default width 40
    $theHash{$field}{html_size_minor} = '1';		# default height 1
  } # foreach my $field (@evidence_tags)

  $theHash{curator}{html_field_name} = 'Curator &nbsp; &nbsp;(REQUIRED)';
  $theHash{phenotypeassay_name}{html_field_name} = 'Phenotype Assay Name &nbsp; &nbsp;(REQUIRED)';
  $theHash{reference}{html_field_name} = 'Reference';
  $theHash{reference}{html_size_minor} = '8';		# default height 8 for reference
  $theHash{definition}{html_field_name} = 'Definition';

    # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects
  $theHash{description}{html_field_name} = 'Description';
  $theHash{assayphe}{html_field_name} = 'Assay Phenotype';
  $theHash{specialof}{html_field_name} = 'Specialisation of';
  $theHash{generalof}{html_field_name} = 'Generalisation of';
  $theHash{consistof}{html_field_name} = 'Consists of';
  $theHash{partof}{html_field_name} = 'Part of';
  $theHash{equivto}{html_field_name} = 'Equivalent to';
  $theHash{similarto}{html_field_name} = 'Similar to';
  $theHash{comment}{html_field_name} = 'Comment';

  $theHash{phenotypeassay_name}{html_comment} = 'WBassayXXXXXXX, unique stable ID';
  $theHash{description}{html_comment} = 'Visual-dissecting scope; Visual-DIC, CV.';
  $theHash{assayphe}{html_comment} = '';
  $theHash{specialof}{html_comment} = 'e.g. WBassay0000001<BR>denote ISA relationship';
  $theHash{generalof}{html_comment} = 'e.g. WBassay0000001<BR>denote ISA relationship';
  $theHash{consistof}{html_comment} = 'e.g. WBassay0000001<BR>denote PARTOF relationship';
  $theHash{partof}{html_comment} = 'e.g. WBassay0000001<BR>denote PARTOF relationship';
  $theHash{equivto}{html_comment} = 'e.g. WBassay0000001<BR>';
  $theHash{similarto}{html_comment} = 'e.g. WBassay0000001<BR>';
  $theHash{comment}{html_comment} = 'This field is for postgreSQL only, not acedb';
  $theHash{paper_evidence}{html_comment} = 'e.g. [cgc3]';
  $theHash{person_evidence}{html_comment} = 'e.g. WBPerson625';
  $theHash{author_evidence}{html_comment} = 'e.g. Sternberg PW';

  $theHash{assayphe}{html_class_display} = 'Phenotype';	# links to WormBase Display
  $theHash{specialof}{html_class_display} = 'Phenotype_assay';
  $theHash{generalof}{html_class_display} = 'Phenotype_assay';
  $theHash{consistof}{html_class_display} = 'Phenotype_assay';
  $theHash{partof}{html_class_display} = 'Phenotype_assay';
  $theHash{equivto}{html_class_display} = 'Phenotype_assay';
  $theHash{similarto}{html_class_display} = 'Phenotype_assay';

  $theHash{assayphe}{html_pg_link} = 'Phenotype';	# links to PG display
  $theHash{specialof}{html_pg_link} = 'Phenotype Assay';
  $theHash{generalof}{html_pg_link} = 'Phenotype Assay';
  $theHash{consistof}{html_pg_link} = 'Phenotype Assay';
  $theHash{partof}{html_pg_link} = 'Phenotype Assay';
  $theHash{equivto}{html_pg_link} = 'Phenotype Assay';
  $theHash{similarto}{html_pg_link} = 'Phenotype Assay';

  $theHash{assayphe}{xref} = 'Phenotype';		# this fields have this kind of xref's in acedb
  $theHash{specialof}{xref} = 'Phenotype_Assay';
  $theHash{generalof}{xref} = 'Phenotype_Assay';
  $theHash{consistof}{xref} = 'Phenotype_Assay';
  $theHash{partof}{xref} = 'Phenotype_Assay';
  $theHash{equivto}{xref} = 'Phenotype_Assay';
  $theHash{similarto}{xref} = 'Phenotype_Assay';

  $theHash{assayphe}{hash_type} = 'Evidence';		# this fields have this kind of hashes
} # sub initializeHash
  
########## theHASH ########## 



# ?Phenotype_Assay        //WBassay:XXXXXXX, to be ontologized
# Description ?Text       //Visual-dissecting scope; Visual-DIC, CV
# Assay_phenotype ?Phenotype XREF Assay_type #Evidence
# Related_asaay Specialisation_of ?Phenotype_Assay XREF Generalisation_of //denote ISA relationship
#               Generalisation_of ?Phenotype_Assay XREF Specialisation_of //denote ISA relationship
#               Consist_of ?Phenotype_Assay XREF Part_of  //denote PARTOF relationship
#               Part_of ?Phenotype_Assay XREF Consiste_of //denote PARTOF relationship
#               Equivalent_to ?Phenotype_Assay XREF Equivalent_to
#               Similar_to ?Phenotype_Assay XREF Similar_to

sub showSearch {		# look for a specific number
  print <<"EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi">
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
  else { $oop = 'Phenotype Assay'; }
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
    my $result = $dbh->prepare( "SELECT DISTINCT pha_$class FROM pha_$class;" ); 
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




