#!/usr/bin/perl -w

# Checkout phenotypes to curate.
#
# Select how many entries you'd like to see in each page (default 20)
# Select which phenotypes you'd like to filter (all, not checked out, not curated, checked out,
# curated)
# Select your name
# Click ``Phenotype !''
#
# Select your Phenotype and click ``Curate !''
# Alternatively select a different page and click ``Page !''
# Alternatively click whether you'd like to filter your search by finding a given word in the
# name (e.g. abc or b), reference (e.g. laboratory: WH or WH), definition (e.g. Suppressor),
# checked out (someone's name), or curated by (someone's name).  Then type the word you'd like
# to search for.  Then click ``Search !''
#
# The Phenotype Name and Curator will be filled in and should likely stay as they are.
# The Reference and Definition will have some information and you should likely add to it.
# Click ``Preview !''
# Alternatively type a different Phenotype Name and click ``Query !'' which will load those 
# values and check out that phenotype to you.  (Be careful that you don't check out a 
# phenotype that someone else has checked out but not yet curated)
# Alternatively type a completely new Phenotype Name and fill in all the information. 
# (This will create a new entry for checked_out, curator, definition, and reference when
# you click the ``New Entry !'' button in the next page)
#
# A preview page will show you data.  If you typed a completely new Phenotype Name you will
# see (and click) the ``New Entry !'' button.  Otherwise you'll see the ``Update !'' button.
#
# The result page will show you data and let you know that the chosen phenotype has been
# Curated by you.  2003 03 27
#
# Replace definition for description in all queries as definition has essentially become
# description, and definition is deprecated.  2003 04 30	
#
# More changes according to some stuff that Raymond wanted.  Still need to create ?Condition
# and ?Phenotype_Assay curation forms and link to them from this form.  2003 05 01
#
# Added link to Wormbase GO_term Report under go_term comment.  Took out :'s between WBabc
# and the 0000001.  2003 05 15
#
# Readded by uncommenting Attribute of section and changed to input vs textarea by Raymond's
# request.  2003 05 15
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
# use Fcntl;
use LWP::Simple;
use LWP::UserAgent;
use Jex; 	# getHtmlVar, mailer, untaint
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $ua = LWP::UserAgent->new;
$ua->agent("MinervaPhenotypeCuration/0.1 ");

my $blue = '#88ffcc';			# redefine blue to a mom-friendly color
my $red = '#ffaacc';			# redefine red to a mom-friendly color

our @pg_xref = ();			# array of commands to run through xref

my $query = new CGI;
our @RowOfRow;
my $MaxEntries = 20;

our $default_pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey ORDER BY phe_reference.joinkey; ";
				# default query
our $notchecked_pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey AND phe_checked_out IS NULL ORDER BY phe_reference.joinkey; ";

our $notcurated_pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey AND phe_curator IS NULL ORDER BY phe_reference.joinkey; ";

our $checked_pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey AND phe_checked_out IS NOT NULL ORDER BY phe_reference.joinkey; ";

our $curated_pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey AND phe_curator IS NOT NULL ORDER BY phe_reference.joinkey; ";


my $action;			# what user clicked
my $curator = "";		# initialize curator
my @PGparameters = qw(phenotype_name curator reference description 
		      synonym description evidence assay_type assay 
		      assay_condition remark 
		      other go_term anatomy life_stage
		      specialisation_of generalisation_of consist_of 
		      part_of equivalent_to similar_to
		      rnai locus allele strain
		      comment);		# vals for %theHash
my @aspect_tags = qw(type attribute value qualifier);
my @evidence_tags = qw(paper_evidence person_evidence author_evidence 
		       similarity_evidence pmid_evidence 
		       accession_evidence protein_id_evidence 
		       cgc_data_submission go_inference_type);

my %variables;			# hash that stores all gene function form related data

my %theHash;			# TEMP


  # not in use with HTML::Template

my $oop;			# temp variable used for getting HTML values

# files
my $save_file = '/home/postgres/public_html/cgi-bin/data/rnai_curation_save.txt';

&PrintHeader();			# print the HTML header
&initializeHash();		# init hash
&process();			# Do pretty much everything
&display(); 			# Select whether to show selectors for curator name
				# entries / page, and &ShowPgQuery();
&PrintFooter();			# print the HTML footer

sub display {
  if ( !($curator) ) { &ChoosePhenotype(); }
# 				# if no curator (first loaded), show selectors
#   else { &ShowPgQuery(); }	# if not, offer option to do Pg query instead
} # sub display

sub ChoosePhenotype {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi\">";
  print "<TABLE>\n";
  print "<TR><TD ALIGN=\"right\">Entries / Page :</TD>";
  print "<TD><INPUT NAME=\"entries_page\" SIZE=15 VALUE=\"$MaxEntries\"></TD></TR>";
  print "<TR><TD ALIGN=\"right\">Show Phenotypes : </TD><TD><SELECT NAME=\"show_what\" SIZE=5>\n";
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
  print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Phenotype !\"></TD></TR><BR><BR>\n";
  print "</TABLE>\n";
  print "</FORM>\n";
} # sub ChoosePhenotype


sub process {			# Essentially do everything
  unless ($action = $query->param('action')) {
    $action = 'none'; 
  }

    # if new postgres command or curator chosen
  if ( ($action eq 'Pg !') || ($action eq 'Phenotype !') || ($action eq 'Search !') ) {
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
    if ($action eq 'Phenotype !') { $pgcommand = $default_pgcommand; }
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
#     else { print "<FONT COLOR=blue>ERROR : Show Phenotypes option in subroutine Process</FONT><BR>\n"; }
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

    if ($action eq 'Search !') {
         # add into the pgcommand an additional AND to specify the joinkey
       if ($query->param("search_term_value")) { $oop = $query->param("search_term_value"); }
         else { $oop = 1; print "<FONT COLOR=blue>ERROR : no paper number chosen</FONT>"; }
       if ($search_term eq 'name') { $search_term = 'phe_reference.joinkey'; }
       elsif ($search_term eq 'synonym') { $search_term = 'phe_synonym.phe_synonym'; }
       elsif ($search_term eq 'reference') { $search_term = 'phe_reference.phe_reference'; }
       elsif ($search_term eq 'description') { $search_term = 'phe_description.phe_description'; }
       elsif ($search_term eq 'checked_out') { $search_term = 'phe_checked_out.phe_checked_out'; }
       elsif ($search_term eq 'curated_by') { $search_term = 'phe_curated_by.phe_curated_by'; }
       else { $search_term = 1; print "<FONT COLOR=blue>ERROR : Search Term Invalid</FONT>"; }

       $pgcommand = "SELECT phe_reference.joinkey, phe_synonym.phe_synonym, phe_reference.phe_reference, phe_description.phe_description, phe_checked_out.phe_checked_out, phe_curator.phe_curator FROM phe_synonym, phe_reference, phe_description, phe_checked_out, phe_curator WHERE phe_reference.joinkey = phe_synonym.joinkey AND phe_reference.joinkey = phe_description.joinkey AND phe_reference.joinkey = phe_checked_out.joinkey AND phe_reference.joinkey = phe_curator.joinkey AND $search_term ~ '" . &untaint($oop) . "' ORDER BY phe_reference.joinkey; ";
    } # if ($action eq 'Search !')

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
    &createPhenotype();
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

  elsif ( $action eq 'Class' ) {
    $curator = &getCuratorFromForm();
    &processClassList();
  } # elsif ( $action eq 'Class' )
} # sub process


sub getClassList {		# Link to WormBase objects and Minerva objects
  my ($class, $type) = @_;
  print "<TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?class=$class&class_type=WormBase&action=Class\" target=NEW>List of $class objects</a> in <a href=\"http://www.wormbase.org\" target=NEW>WormBase</a>.</TD>\n";


  if ($theHash{$type}{html_pg_link}) {				# if it needs to link to tazendra as well 
    my $curator_temp = $curator;
    $curator_temp =~ s/ /\+/g;
    if ($theHash{$type}{html_pg_link} eq 'Phenotype') {		# for Phenotypes
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?curator=$curator_temp&show_what=All&action=Phenotype+%21\" target=NEW>List of $class objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Anatomy_term') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?class=$theHash{$type}{html_pg_link}&class_type=Minerva&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Life_stage') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi?class=$theHash{$type}{html_pg_link}&class_type=Minerva&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Assay Type') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_assay_curation.cgi?curator=$curator_temp&show_what=All&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
    elsif ($theHash{$type}{html_pg_link} eq 'Assay Condition') {
      print "</TR><TR><TD></TD><TD>See <a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/condition_curation.cgi?curator=$curator_temp&show_what=All&action=Class\" target=NEW>List of $theHash{$type}{html_pg_link} objects</a> in <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/index.cgi\" target=NEW>Minerva</a>.</TD>\n"; }
#   $theHash{assay_type}{html_pg_link} = 'Assay Type';
#   $theHash{assay_condition}{html_pg_link} = 'Assay Condition';
    else { 1; }
  } # if ($theHash{$class}{html_pg_link})
} # sub getClassList

sub processClassList {
  if ( $query->param("class") ) { $oop = $query->param("class"); }
  else { $oop = 'Phenotype'; }
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
    my $result = $dbh->prepare( "SELECT DISTINCT phe_$class FROM phe_$class;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      print "<TR BGCOLOR=$red><TD>$row[0]</TD></TR>\n";
    } # while (my @row = $result->fetchrow)
    print "</TABLE>\n";
  } # elsif ($class eq 'Minerva')
  else { 1; }
} # sub processClassList

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
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi\">\n";
  &getHtml();
#   &displayVars();
  &dealPg();
#   &mailRnai();
  print "</FORM>\n";
} # sub commitData {

sub dealPg {
  my @PGtables = qw( checked_out );
  foreach my $param (@PGparameters) { unless ($param eq 'phenotype_name') { push @PGtables, $param; } }
  my $joinkey = $theHash{phenotype_name}{html_value};
  print "<TABLE>\n";
  foreach my $pgtable (@PGtables) {
    my $color = $blue;
    if ($theHash{$pgtable}{html_value}) {	# if main tag has data
      if ($theHash{$pgtable}{pg_update}) {	# UPDATE
        my $result = $dbh->do( "UPDATE phe_$pgtable SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" );
        print "<TR BGCOLOR=$color><TD>UPDATE phe_$pgtable SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\'</TD></TR>\n"; 
        $result = $dbh->do( "UPDATE phe_$pgtable SET phe_$pgtable = '$theHash{$pgtable}{html_value}' WHERE joinkey = '$joinkey';" );
        print "<TR BGCOLOR=$color><TD>UPDATE phe_$pgtable SET phe_$pgtable = \'$theHash{$pgtable}{html_value}\' WHERE joinkey = \'$joinkey\'</TD></TR>\n"; }
      elsif ($theHash{$pgtable}{pg_insert}) {	# INSERT
        $color = $red;
        my $result = $dbh->do( "INSERT INTO phe_$pgtable VALUES ('$joinkey\', '$theHash{$pgtable}{html_value}');" );
        print "<TR BGCOLOR=$color><TD>INSERT INTO phe_$pgtable VALUES (\'$joinkey\', \'$theHash{$pgtable}{html_value}\')</TD></TR>\n"; }
      else { 					# ERROR
        print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
        print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD></TR>\n"; }
    } # if ($theHash{$pgtable}{html_value})
    if ($theHash{$pgtable}{hash_type}) {	# if main tag has a hash type
      if ($theHash{$pgtable}{hash_type} eq 'Aspect_info') {	# if hash type is aspect info hash
        foreach my $aspect_tag (@aspect_tags) {			# check each aspect tag
          my $hash_tag = $pgtable . '_' . $aspect_tag;
          if ($theHash{$hash_tag}{html_value}) {		# if hash tag has data
            $color = $blue;
            if ($theHash{$hash_tag}{pg_update}) {	# UPDATE
              my $result = $dbh->do( "UPDATE phe_asp_$aspect_tag SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND phe_main_tag = 'phe_$pgtable';" );
              print "<TR BGCOLOR=$color><TD>UPDATE phe_asp_$aspect_tag SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\' AND phe_main_tag = \'phe_$pgtable\'</TD></TR>\n"; 
              $result = $dbh->do( "UPDATE phe_asp_$aspect_tag SET phe_asp_$aspect_tag = '$theHash{$hash_tag}{html_value}' WHERE joinkey = '$joinkey' AND phe_main_tag = 'phe_$pgtable';" );
              print "<TR BGCOLOR=$color><TD>UPDATE phe_asp_$aspect_tag SET phe_asp_$aspect_tag = \'$theHash{$hash_tag}{html_value}\' WHERE joinkey = \'$joinkey\' AND phe_main_tag = \'phe_$pgtable\'</TD></TR>\n"; }
            elsif ($theHash{$hash_tag}{pg_insert}) {	# INSERT
              $color = $red;
              my $result = $dbh->do( "INSERT INTO phe_asp_$aspect_tag VALUES ('$joinkey', 'phe_$pgtable', '$theHash{$hash_tag}{html_value}');" );
              print "<TR BGCOLOR=$color><TD>INSERT INTO phe_asp_$aspect_tag VALUES (\'$joinkey\', \'phe_$pgtable\', \'$theHash{$hash_tag}{html_value}\')</TD></TR>\n"; }
            else { 					# ERROR
              print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$aspect_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD>\n"; }
	  } # if ($theHash{$hash_tag}{html_value})
        } # foreach my $aspect_tag (@aspect_tags)
      } # if ($theHash{$pgtable}{hash_type} eq 'Aspect_info')
      if ($theHash{$pgtable}{hash_type} eq 'Evidence') {
        foreach my $evidence_tag (@evidence_tags) {
          my $hash_tag = $pgtable . '_' . $evidence_tag;
          if ($theHash{$hash_tag}{html_value}) {
            $color = $blue;
            if ($theHash{$hash_tag}{pg_update}) {	# UPDATE
              my $result = $dbh->do( "UPDATE phe_evi_$evidence_tag SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey' AND phe_main_tag = 'phe_$pgtable';" );
              print "<TR BGCOLOR=$color><TD>UPDATE phe_evi_$evidence_tag SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$joinkey\' AND phe_main_tag = \'phe_$pgtable\'</TD></TR>\n"; 
              $result = $dbh->do( "UPDATE phe_evi_$evidence_tag SET phe_evi_$evidence_tag = '$theHash{$hash_tag}{html_value}' WHERE joinkey = '$joinkey' AND phe_main_tag = 'phe_$pgtable';" );
              print "<TR BGCOLOR=$color><TD>UPDATE phe_evi_$evidence_tag SET phe_evi_$evidence_tag = \'$theHash{$hash_tag}{html_value}\' WHERE joinkey = \'$joinkey\' AND phe_main_tag = \'phe_$pgtable\'</TD></TR>\n"; }
            elsif ($theHash{$hash_tag}{pg_insert}) {	# INSERT
              $color = $red;
              my $result = $dbh->do( "INSERT INTO phe_evi_$evidence_tag VALUES ('$joinkey', 'phe_$pgtable', '$theHash{$hash_tag}{html_value}');" );
              print "<TR BGCOLOR=$color><TD>INSERT INTO phe_evi_$evidence_tag VALUES (\'$joinkey\', \'phe_$pgtable\', \'$theHash{$hash_tag}{html_value}\')</TD></TR>\n"; }
            else {					# ERROR
              print "<TR BGCOLOR=red><TD>ERROR</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$evidence_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              print "<TD></TD><TD>PG Doesn't know whether to INSERT or UPDATE</TD>\n"; }
	  } # if ($theHash{$hash_tag}{html_value})
        } # foreach my $evidence_tag (@evidence_tags)
      } # if ($theHash{$pgtable}{hash_type} eq 'Evidence')
    } # if ($theHash{$pgtable}{hash_type})
  } # foreach my $pgtable (@PGtables)
  foreach my $pg_xref (@pg_xref) {			# for each command to be exec'ed through xref
    print "<TR BGCOLOR='orange'><TD>$pg_xref</TD></TR>\n";	# display it in orange
    my $result = $dbh->prepare( "$pg_xref" );			# execute it
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  } # foreach my $pg_xref (@pg_xref)
  print "</TABLE>\n";
  print "<P>The phenotype <FONT COLOR=green>$theHash{phenotype_name}{html_value}</FONT> has been Curated by $curator.<BR>\n";
} # sub dealPg

sub preview {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator\" VALUE=\"$curator\">\n";
  my $errors_in_data = &getHtml();
#   &displayVars();
  &showButtonChoice($errors_in_data);
  print "</FORM>\n";
} # sub preview

# sub checkXrefExist {
#   my $pgtable = shift;
#   my $type = $theHash{$pgtable}{xref}; 
#   my $value = $theHash{$pgtable}{html_value};
#   my $joinkey = $theHash{phenotype_name}{html_value};
# #   $result = $dbh->do( "UPDATE phe_checked_out SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$theHash{phenotype_name}{html_value}\';" );
#   my $pg_to_check;			# check pg_table
#   if ($type eq 'Phenotype_Assay') {
#     if ($pgtable eq 'assay_type') { $pg_to_check = 'pha_assayphe'; } }
#   elsif ($type eq 'Phenotype') { 
#     if ($pgtable eq 'assay_type') { $pg_to_check = 'pha_assayphe'; }
#     elsif ($pgtable eq 'specialisation_of') { $pg_to_check = 'phe_generalisation_of'; }
#     elsif ($pgtable eq 'generalisation_of') { $pg_to_check = 'phe_specialisation_of'; }
#     elsif ($pgtable eq 'consist_of') { $pg_to_check = 'phe_part_of'; }
#     elsif ($pgtable eq 'part_of') { $pg_to_check = 'phe_consist_of'; }
#     elsif ($pgtable eq 'equivalent_to') { $pg_to_check = 'phe_equivalent_to'; }
#     elsif ($pgtable eq 'similar_to') { $pg_to_check = 'phe_similar_to'; }
#   }
#   else { print "<TR BGCOLOR=red><TD>NOT A VALID XREF TYPE FOR ACEDB</TD><TD>$type</TD></TR>\n"; }
#   my $result = $dbh->prepare( "SELECT * FROM $pg_to_check WHERE $pg_to_check ~ \'$joinkey\' AND joinkey = \'$value\';" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
# my $found = 'pie';	# temp
#   while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = 'ood '; } }
#   
#   print "<TR><TD>$joinkey</TD><TD>$pgtable</TD><TD>$type</TD><TD>$value</TD><TD>$pg_to_check</TD><TD>$found</TD></TR>\n";
# } # sub checkXrefExist

sub checkXrefExist {
  my $pgtable = shift;			# table whose data's xref we want to check
  my $pgtype = '';			# 3-letter pg table set identifier (con for Condition)
  my $type = $theHash{$pgtable}{xref};			# type of xref
  my $value = $theHash{$pgtable}{html_value};		# value being passed in (which joinkeys to check in xref table)
  my $joinkey = $theHash{phenotype_name}{html_value};	# joinkey of entry (which values to check in xref table)
  my $pg_to_check;                      # pg_table xref checks
  my $error_in_xref_creation = '';	# error flag if a value is created via XREF

#   $theHash{assay_type}{xref} = 'Phenotype_Assay';	# this fields have this kind of xref's in acedb
#   $theHash{specialisation_of}{xref} = 'Phenotype';
#   $theHash{generalisation_of}{xref} = 'Phenotype';
#   $theHash{consist_of}{xref} = 'Phenotype';
#   $theHash{part_of}{xref} = 'Phenotype';
#   $theHash{equivalent_to}{xref} = 'Phenotype';
#   $theHash{similar_to}{xref} = 'Phenotype';

  if ($type eq 'Phenotype_Assay') {
    $pgtype = 'pha';
    if ($pgtable eq 'assay_type') { $pg_to_check = 'pha_assayphe'; } }
  elsif ($type eq 'Phenotype') { 
    $pgtype = 'phe';
    if ($pgtable eq 'specialisation_of') { $pg_to_check = 'phe_generalisation_of'; }
    elsif ($pgtable eq 'generalisation_of') { $pg_to_check = 'phe_specialisation_of'; }
    elsif ($pgtable eq 'consist_of') { $pg_to_check = 'phe_part_of'; }
    elsif ($pgtable eq 'part_of') { $pg_to_check = 'phe_consist_of'; }
    elsif ($pgtable eq 'equivalent_to') { $pg_to_check = 'phe_equivalent_to'; }
    elsif ($pgtable eq 'similar_to') { $pg_to_check = 'phe_similar_to'; } }
#   else { print "<TR BGCOLOR=red><TD>NOT A VALID XREF TYPE FOR ACEDB</TD><TD>$type</TD></TR>\n"; }
#   if ($type eq 'Condition') {		# only Condition type XREFs in Condition model
#     $pgtype = 'con';
#     if ($pgtable eq 'containedin') { $pg_to_check = 'con_contains'; }		# which table to check xref
#     elsif ($pgtable eq 'contains') { $pg_to_check = 'con_containedin'; }	# which table to check xref
#     elsif ($pgtable eq 'precedes') { $pg_to_check = 'con_follows'; }		# which table to check xref
#     elsif ($pgtable eq 'follows') { $pg_to_check = 'con_precedes'; }		# which table to check xref
#   }
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
  foreach my $param (@PGparameters) { unless ($param eq 'phenotype_name') { push @PGtables, $param; } }
  ($oop, $theHash{phenotype_name}{html_value}) = &getHtmlVar($query,'phenotype_name');
  my $joinkey = $theHash{phenotype_name}{html_value};
  print "<TABLE>";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"phenotype_name\" VALUE=\"$joinkey\">\n";
  print "<TR><TD></TD><TD>NAME</TD><TD>$joinkey</TD></TR>\n";
  foreach my $pgtable (@PGtables) {
    my $color = $blue;
    ($oop, $theHash{$pgtable}{html_value}) = &getHtmlVar($query, $pgtable);
    if ($theHash{$pgtable}{html_value}) {	# if tag has value
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"$pgtable\" VALUE=\"$theHash{$pgtable}{html_value}\">\n";
      my $result = $dbh->prepare( "SELECT phe_$pgtable FROM phe_$pgtable WHERE joinkey = '$joinkey';");
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my $found;                                # this phe_$pgtable
      while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = ' '; } }
      if ($found) {                     # UPDATE
        print "<TR BGCOLOR=$color><TD>UPDATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>\n";
        $theHash{$pgtable}{pg_update}++;
      } else { # if ($found)            # INSERT
        $color = $red;
        print "<TR BGCOLOR=$color><TD>CREATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>\n";
        $theHash{$pgtable}{pg_insert}++;
      } # else # if ($found)
      if ( $theHash{$pgtable}{xref} ) {		# if there's an XREF
        if ( $theHash{$pgtable}{xref} eq 'Phenotype_Assay' ) {
#           print "<TR><TD></TD><TD>XREF TYPE</TD><TD>$theHash{$pgtable}{xref}</TD></TR>\n";
          my $error_in_xref_creation = &checkXrefExist($pgtable);
          if ($error_in_xref_creation) { $there_are_errors_flag .= "$error_in_xref_creation|"; }
          }
        elsif ( $theHash{$pgtable}{xref} eq 'Phenotype' ) {
#           print "<TR><TD></TD><TD>XREF TYPE</TD><TD>$theHash{$pgtable}{xref}</TD></TR>\n";
          my $error_in_xref_creation = &checkXrefExist($pgtable);
          if ($error_in_xref_creation) { $there_are_errors_flag .= "$error_in_xref_creation|"; }
          }
        else { print "<TR BGCOLOR=red><TD>NOT A VALID XREF TYPE FOR ACEDB</TD></TR>\n"; $there_are_errors_flag .= 'invalidXref|'; }
      } # if ( $theHash{$pgtable}{xref} )
#   $theHash{assay_type}{xref} = 'Phenotype_Assay';
#   $theHash{specialisation_of}{xref} = 'Phenotype';
    } # if ($theHash{$pgtable}{html_value})
    if ($theHash{$pgtable}{hash_type}) {
      if ($theHash{$pgtable}{hash_type} eq 'Aspect_info') {	# if tag has aspect hash
        foreach my $aspect_tag (@aspect_tags) {
          my $hash_tag = $pgtable . '_' . $aspect_tag;
          ($oop, $theHash{$hash_tag}{html_value}) = &getHtmlVar($query, $hash_tag);
          if ($theHash{$hash_tag}{html_value}) {
            $color = $blue;
            print "<INPUT TYPE=\"HIDDEN\" NAME=\"$hash_tag\" VALUE=\"$theHash{$hash_tag}{html_value}\">\n";
            my $result = $dbh->prepare( "SELECT phe_asp_$aspect_tag FROM phe_asp_$aspect_tag WHERE joinkey = '$joinkey' AND phe_main_tag = 'phe_$pgtable';" );
            $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
            my $found;                          # this phe_$pgtable
            while (my @row = $result->fetchrow) { if ($row[0]) { $found = $row[0] } else { $found = ' '; } }
            if ($found) {                       # UPDATE
              print "<TR BGCOLOR=$color><TD>UPDATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$aspect_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              $theHash{$hash_tag}{pg_update}++;
            } else { # if ($found)              # INSERT
              $color = $red;
              print "<TR BGCOLOR=$color><TD>CREATE</TD><TD>$pgtable</TD><TD>$theHash{$pgtable}{html_value}</TD>";
              print "<TD>$aspect_tag</TD><TD>$theHash{$hash_tag}{html_value}</TD>\n";
              $theHash{$hash_tag}{pg_insert}++;
            } # else # if ($found)
          } # if ($theHash{$hash_tag}{html_value})
        } # foreach my $aspect_tag (@aspect_tags)
      } # if ($theHash{$pgtable}{hash_type} eq 'Aspect_info')
      if ($theHash{$pgtable}{hash_type} eq 'Evidence') {	# if tag has evidence hash
        foreach my $evidence_tag (@evidence_tags) {
          my $hash_tag = $pgtable . '_' . $evidence_tag;
          ($oop, $theHash{$hash_tag}{html_value}) = &getHtmlVar($query, $hash_tag);
          if ($theHash{$hash_tag}{html_value}) {
            $color = $blue;
            print "<INPUT TYPE=\"HIDDEN\" NAME=\"$hash_tag\" VALUE=\"$theHash{$hash_tag}{html_value}\">\n";
            my $result = $dbh->prepare( "SELECT phe_evi_$evidence_tag FROM phe_evi_$evidence_tag WHERE joinkey = '$joinkey' AND phe_main_tag = 'phe_$pgtable';" );
            $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
            my $found;                          # this phe_$pgtable
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

sub getHtmlOld {
  if ($action eq 'Preview !') { print "<TABLE>"; }
  foreach my $type (@PGparameters) {
    ($oop, $theHash{$type}{html_value}) = &getHtmlVar($query, $type);
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
    if ($theHash{$type}{html_value}) {
      unless ($theHash{$type}{hash_type}) {  
        if ($action eq 'Preview !') { 
          print "<TR><TD>$type</TD>";
          print "<TD><FONT COLOR = green>$theHash{$type}{html_value}</FONT></TD></TR>\n"; }
      } else { # unless ($theHash{$type}{hash_type}) 
        if ($theHash{$type}{hash_type} eq 'Aspect_info') {
          foreach my $aspect_tag (@aspect_tags) {
            my $hash_tag = $type . '_' . $aspect_tag;
            ($oop, $theHash{$hash_tag}{html_value}) = &getHtmlVar($query, $hash_tag);
            print "<INPUT TYPE=\"HIDDEN\" NAME=\"$hash_tag\" VALUE=\"$theHash{$hash_tag}{html_value}\">\n";
            if ($theHash{$hash_tag}{html_value}) {
              if ($action eq 'Preview !') { 
                print "<TR><TD>$type</TD>";
                print "<TD><FONT COLOR = green>$theHash{$type}{html_value}</TD>\n";
	        print "<TD>$aspect_tag</TD><TD><FONT COLOR = green>$theHash{$hash_tag}{html_value}</FONT></TD></TR>\n"; } 
            } # if ($theHash{$hash_tag}{html_value})
          } # foreach my $aspect_tag (@aspect_tags)
        } # if ($theHash{$type}{hash_type} eq 'Aspect_info')
        if ($theHash{$type}{hash_type} eq 'Evidence') {
          foreach my $evidence_tag (@evidence_tags) {
            my $hash_tag = $type . '_' . $evidence_tag;
            ($oop, $theHash{$hash_tag}{html_value}) = &getHtmlVar($query, $hash_tag);
            print "<INPUT TYPE=\"HIDDEN\" NAME=\"$hash_tag\" VALUE=\"$theHash{$hash_tag}{html_value}\">\n";
            if ($theHash{$hash_tag}{html_value}) {
              if ($action eq 'Preview !') { 
                print "<TR><TD>$type</TD>";
                print "<TD><FONT COLOR = green>$theHash{$type}{html_value}</TD>\n";
	        print "<TD>$evidence_tag</TD><TD><FONT COLOR = green>$theHash{$hash_tag}{html_value}</FONT></TD></TR>\n"; }
            } # if ($theHash{$hash_tag}{html_value})
          } # foreach my $evidence_tag (@evidence_tags)
        } # if ($theHash{$type}{hash_type} eq 'Evidence')
      } # else # unless ($theHash{$type}{hash_type}) 
    } # if ($theHash{$type}{html_value})
  } # foreach my $type (@PGparameters)
  if ($action eq 'Preview !') { print "</TABLE>"; }
} # sub getHtmlOld

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
  my $result = $dbh->prepare( "SELECT * FROM phe_$phe_table WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row; my $found;
  while (@row = $result->fetchrow) { if ($row[1]) { $found = $row[0] } else { $found = ' '; } }
    # if there's null or blank data, change it to a space so it will update, not insert
  return $found;
} # sub FindIfPgEntry


# sub queryPG {
#   ($oop, $variables{pubID}) = &getHtmlVar($query, 'pubID');
#   ($oop, $variables{pdffilename}) = &getHtmlVar($query, 'pdffilename');
#   ($oop, $variables{reference}) = &getHtmlVar($query, 'reference');
#   my $result = $dbh->prepare ( "SELECT * FROM cur_rnai WHERE joinkey = \'$variables{pubID}\';" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   my @row = $result->fetchrow;
#   $variables{rnai2} = $row[1];
#   $result = $dbh->prepare ( "SELECT * FROM cur_comment WHERE joinkey = \'$variables{pubID}\';" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   @row = $result->fetchrow;
#   $variables{comment} = $row[1];
# } # sub queryPG


sub createPhenotype {	# almost same as curatePopulate, but creates a new phenotype from pg sequence
  my $result = $dbh->prepare( "SELECT nextval('phe_seq');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  my $number = $row[0]; my $joinkey;
  if ($number < 10) { $joinkey = 'WBphenotype000000' . $number; }
  elsif ($number < 100) { $joinkey = 'WBphenotype00000' . $number; }
  elsif ($number < 1000) { $joinkey = 'WBphenotype0000' . $number; }
  elsif ($number < 10000) { $joinkey = 'WBphenotype000' . $number; }
  elsif ($number < 100000) { $joinkey = 'WBphenotype00' . $number; }
  elsif ($number < 1000000) { $joinkey = 'WBphenotype0' . $number; }
  else { $joinkey = 'WBphenotype' . $number; }
  $theHash{phenotype_name}{html_value} = $joinkey;
  $result = $dbh->do( "INSERT INTO phe_checked_out VALUES ('$joinkey', '$curator');" );
  $result = $dbh->do( "INSERT INTO phe_curator VALUES ('$joinkey', NULL);" );
  $result = $dbh->do( "INSERT INTO phe_reference VALUES ('$joinkey', 'Created by $curator');" );
  $result = $dbh->do( "INSERT INTO phe_description VALUES ('$joinkey', NULL);" );
  print "You have Created Phenotype : $theHash{phenotype_name}{html_value}<BR>\n";
  &loadFromPg();
} # sub createPhenotype

sub curatePopulate {
  (my $oop, $theHash{phenotype_name}{html_value}) = &getHtmlVar($query, 'phenotype_name');
  my $result = $dbh->do( "UPDATE phe_checked_out SET phe_checked_out = \'$curator\' WHERE joinkey = \'$theHash{phenotype_name}{html_value}\';" );
  $result = $dbh->do( "UPDATE phe_checked_out SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = \'$theHash{phenotype_name}{html_value}\';" );
  print "You have Checked Out Phenotype : $theHash{phenotype_name}{html_value}<BR>\n";
#   $result = $dbh->prepare( "SELECT phe_reference FROM phe_reference WHERE joinkey = \'$theHash{phenotype_name}{html_value}\';" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   my @row = $result->fetchrow;
#   $theHash{reference}{html_value} = $row[0];
#   $result = $dbh->prepare( "SELECT phe_definition FROM phe_definition WHERE joinkey = \'$theHash{phenotype_name}{html_value}\';" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   @row = $result->fetchrow;
#   $theHash{definition}{html_value} = $row[0];
  &loadFromPg();
} # sub curatePopulate

sub loadFromPg {
  my @PGtables; 
  foreach my $param (@PGparameters) { unless ($param eq 'phenotype_name') { push @PGtables, $param; } }
  my $joinkey = $theHash{phenotype_name}{html_value};
  foreach my $pgtable (@PGtables) {
    my $result = $dbh->prepare( "SELECT phe_$pgtable FROM phe_$pgtable WHERE joinkey = \'$theHash{phenotype_name}{html_value}\';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    $theHash{$pgtable}{html_value} = $row[0];
    if ($theHash{$pgtable}{hash_type}) {
      if ($theHash{$pgtable}{hash_type} eq 'Aspect_info') { 
        foreach my $aspect_tag (@aspect_tags) {
          my $hash_tag = $pgtable . '_' . $aspect_tag;
          $result = $dbh->prepare( "SELECT phe_asp_$aspect_tag FROM phe_asp_$aspect_tag WHERE joinkey = \'$joinkey\' AND phe_main_tag = 'phe_$pgtable';" );
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
          my @row = $result->fetchrow;
          $theHash{$hash_tag}{html_value} = $row[0]; } }
      if ($theHash{$pgtable}{hash_type} eq 'Evidence') {
        foreach my $evidence_tag (@evidence_tags) {
          my $hash_tag = $pgtable . '_' . $evidence_tag;
          $result = $dbh->prepare( "SELECT phe_evi_$evidence_tag FROM phe_evi_$evidence_tag WHERE joinkey = \'$joinkey\' AND phe_main_tag = 'phe_$pgtable';" );
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
          my @row = $result->fetchrow;
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

    &showSearch();

    &showCreatePhenotype();

      # process with this form, select new page, pass hidden values.
    print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi\">";
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
    print "<TR><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>synonym</TD><TD ALIGN=CENTER>reference</TD><TD ALIGN=CENTER>description</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curated</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
				# show headers if default
    for my $i ( (($page-1)*$MaxEntries) .. (($page*$MaxEntries)-1) ) {
				# for the amount of entries chosen in the chosen page
      my $row = $RowOfRow[$i];
      if ($row->[0]) {		# if there's an entry
        print "<TR>";
        print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator\" VALUE=\"$curator\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"phenotype_name\" VALUE=\"$row->[0]\">\n";

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
    print "<TR><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>synonym</TD><TD ALIGN=CENTER>reference</TD><TD ALIGN=CENTER>description</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curated</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
				# show headers if default
    print "</TABLE>\n";		# close table
    print "PAGE : $page<BR>\n";	# show page number again
    print "</CENTER>\n";
} # sub processTable 

sub showCreatePhenotype {
  print <<"EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi">
  <TABLE ALIGN=center><TR>
  <TD>Create a new Phenotype :</TD>
  <INPUT TYPE="HIDDEN" NAME="curator" VALUE="$curator">
  <TD><INPUT TYPE="submit" NAME="action" VALUE="Create !"></TD>
  </TR></TABLE>
  </FORM>
EndOfText
} # sub showCreatePhenotype

sub showSearch {		# look for a specific number
  print <<"EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi">
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


sub PrintHeader {
  print <<"EndOfText";
Content-type: text/html\n\n

<HTML>
<LINK rel="stylesheet" type="text/css" href="http://www.wormbase.org/stylesheets/wormbase.css">
  
<HEAD>
<TITLE>Phenotype Checkout / Curation</TITLE>
</HEAD>
  
<BODY bgcolor=#aaaaaa text=#000000 link=cccccc alink=eeeeee vlink=bbbbbb>
<HR>
<CENTER>Documentation <A HREF="http://tazendra.caltech.edu/~postgres/cgi-bin/docs/phenotype_curation_doc.txt" TARGET=NEW>here</A></CENTER><P>
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
  &printHtmlInputQuery('phenotype_name');	# input with Query button
#   &printHtmlTextarea('reference');	# raymond doesn't want this
#   &printHtmlTextarea('definition');	# raymond doesn't want this
  &printHtmlFormButtonMenu(); 	# buttons of form
#   &printHtmlTextarea('synonym');	# raymond wants input not textarea
  &printHtmlInput('synonym');
#   &printHtmlTextarea('description');	# raymond wants input not textarea
  &printHtmlInput('description');
#   &printHtmlTextarea('evidence');	# raymond doesn't want textarea for evidence
  &printHtmlEmptyhash('evidence');
  &printHtmlInput('assay_type');
  &printHtmlInput('assay_condition');
#   &printHtmlTextarea('assay_type');		# raymond wants input not textare
#   &printHtmlTextarea('assay');	# raymond doesn't want this
#   &printHtmlTextarea('assay_condition');	# raymond wants input not textarea
  &printHtmlTextarea('remark');
  &printHtmlSection('Aspect Affected');
#   &printHtmlTextarea('other');		# raymond wants input not textarea
#   &printHtmlTextarea('go_term');		# raymond wants input not textarea
#   &printHtmlTextarea('anatomy');		# raymond wants input not textarea
#   &printHtmlTextarea('life_stage');		# raymond wants input not textarea
#   &printHtmlSection('Related Phenotypes');	# raymond wants input not textarea
#   &printHtmlTextarea('specialisation_of');	# raymond wants input not textarea
#   &printHtmlTextarea('generalisation_of');	# raymond wants input not textarea
#   &printHtmlTextarea('consist_of');		# raymond wants input not textarea
#   &printHtmlTextarea('part_of');		# raymond wants input not textarea
#   &printHtmlTextarea('equivalent_to');	# raymond wants input not textarea
#   &printHtmlTextarea('similar_to');		# raymond wants input not textarea
  &printHtmlInput('other');
  &printHtmlInput('go_term');		
  &printHtmlInput('anatomy');		
  &printHtmlInput('life_stage');		
  &printHtmlSection('Related Phenotypes');	
  &printHtmlInput('specialisation_of');	
  &printHtmlInput('generalisation_of');	
  &printHtmlInput('consist_of');		
  &printHtmlInput('part_of');		
  &printHtmlInput('equivalent_to');	
  &printHtmlInput('similar_to');		
  &printHtmlSection('Attribute of');	
  &printHtmlInput('rnai');
  &printHtmlInput('locus');
  &printHtmlInput('allele');
  &printHtmlInput('strain');
#   &printHtmlSection('Attribute of');		# raymond wants input not textarea
#   &printHtmlTextarea('rnai');			# raymond wants input not textarea
#   &printHtmlTextarea('locus');		# raymond wants input not textarea
#   &printHtmlTextarea('allele');		# raymond wants input not textarea
#   &printHtmlTextarea('strain');		# raymond wants input not textarea
  &printHtmlSection('Comments');
  &printHtmlTextarea('comment');
  &printHtmlFormButtonMenu(); 	# buttons of form
  &printHtmlFormEnd();		# ending of form 
} # sub printHtmlForm

sub printHtmlFormStart {	# beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi">
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
  if ($theHash{$type}{hash_type}) {
    if ($theHash{$type}{hash_type} eq 'Aspect_info') { &printHtmlAspect($type); }
    if ($theHash{$type}{hash_type} eq 'Evidence') { &printHtmlEvidence($type); }
  }
  print "  <TR><TD>&nbsp;</TD></TR>";
} # sub printHtmlTextarea

sub printHtmlEvidence {
  my $type = shift;
  print "    <TR><TD></TD><TD><TABLE cellspacing=5>";
  foreach my $evidence_tag (@evidence_tags) {
    if ( ($evidence_tag ne 'paper_evidence') && ($evidence_tag ne 'person_evidence') &&
         ($evidence_tag ne 'author_evidence') ) { next; }	# skip if none of these 
    my $hash_tag = $type . '_' . $evidence_tag;
    unless ($theHash{$hash_tag}{html_value}) { $theHash{$hash_tag}{html_value} = ''; }
    print <<"    EndOfText";
        <TR>
          <TD ALIGN="right">$evidence_tag :</TD>
          <TD><INPUT NAME="${type}_${evidence_tag}" VALUE="$theHash{$hash_tag}{html_value}"
	       SIZE=$theHash{$evidence_tag}{html_size_main}></TD>
          <!--<TD><TEXTAREA NAME="${type}_${evidence_tag}" ROWS=$theHash{$evidence_tag}{html_size_minor}
               COLS=$theHash{$evidence_tag}{html_size_main}>$theHash{$hash_tag}{html_value}</TEXTAREA></TD>-->
        </TR>
    EndOfText
  } # foreach my $evidence_tag (@evidence_tags)
  print "    </TABLE></TD></TR>";
} # sub printHtmlEvidence

sub printHtmlAspect {
  my $type = shift;
  print "    <TR><TD></TD><TD><TABLE cellspacing=5>";
  my @aspect_tags = qw(type attribute value qualifier);
  if ($type eq 'go_term') { @aspect_tags = qw(value qualifier); }
  if ($type eq 'anatomy') { @aspect_tags = qw(attribute value qualifier); }
  if ($type eq 'life_stage') { @aspect_tags = qw(attribute value qualifier); }
  foreach my $aspect_tag (@aspect_tags) {
    print <<"    EndOfText";
        <TR>
          <TD ALIGN="right">$aspect_tag :</TD>
          <TD><SELECT NAME="${type}_${aspect_tag}" SIZE=1>
              <OPTION> </OPTION>
    EndOfText
    my $hash_tag = $type . '_' . $aspect_tag;
    unless ($theHash{$hash_tag}{html_value}) { $theHash{$hash_tag}{html_value} = ''; }
    my $result = $dbh->prepare( "SELECT DISTINCT phe_asp_$aspect_tag FROM phe_asp_$aspect_tag;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {	# get list of aspect_tags and show in select
      unless ($theHash{$hash_tag}{html_value} eq $row[0]) { 
        print "              <OPTION>$row[0]</OPTION>\n"; }
      else {
        print "              <OPTION selected>$row[0]</OPTION>\n"; 
        $theHash{$hash_tag}{html_value} = ''; } }	# empty so as not to print to textarea
    print <<"    EndOfText";
              </SELECT></TD>
              <TD><INPUT NAME="${type}_${aspect_tag}" VALUE="$theHash{$hash_tag}{html_value}"
	           SIZE=$theHash{$aspect_tag}{html_size_main}></TD>
          <!--<TD><TEXTAREA NAME="${type}_${aspect_tag}" ROWS=$theHash{$aspect_tag}{html_size_minor}
               COLS=$theHash{$aspect_tag}{html_size_main}>$theHash{$hash_tag}{html_value}</TEXTAREA></TD>-->
        </TR>
    EndOfText
  } # foreach my $aspect_tag (@aspect_tags)
  print "    </TABLE></TD></TR>";
} # sub printHtmlAspect

sub printHtmlSelectCurators {   # print html select blocks for curators
  my $type = shift;
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
  foreach my $field (@aspect_tags) {
    $theHash{$field}{html_field_name} = '';		# name for display
    $theHash{$field}{html_value} = '';			# value for field
    $theHash{$field}{html_size_main} = '40';		# default width 40
    $theHash{$field}{html_size_minor} = '1';		# default height 1
  } # foreach my $field (@aspect_tags)

  $theHash{curator}{html_field_name} = 'Curator &nbsp; &nbsp;(REQUIRED)';
  $theHash{phenotype_name}{html_field_name} = 'Phenotype Name &nbsp; &nbsp;(REQUIRED)';
  $theHash{reference}{html_field_name} = 'Reference';
  $theHash{reference}{html_size_minor} = '8';		# default height 8 for reference
  $theHash{definition}{html_field_name} = 'Definition';

    # initialize the html field name, mailing codes, html mailing addresses, and mailing subjects
  $theHash{synonym}{html_field_name} = 'Synonym';
  $theHash{description}{html_field_name} = 'Description';
  $theHash{evidence}{html_field_name} = 'Evidence';
  $theHash{assay_type}{html_field_name} = 'Assay Type';
  $theHash{assay}{html_field_name} = 'Assay';
  $theHash{assay_condition}{html_field_name} = 'Assay Condition';
  $theHash{remark}{html_field_name} = 'Remark';
  $theHash{other}{html_field_name} = 'Other';
  $theHash{go_term}{html_field_name} = 'GO Term';
  $theHash{anatomy}{html_field_name} = 'Anatomy';
  $theHash{life_stage}{html_field_name} = 'Life Stage';
  $theHash{specialisation_of}{html_field_name} = 'Specialisation of';
  $theHash{generalisation_of}{html_field_name} = 'Generalisation of';
  $theHash{consist_of}{html_field_name} = 'Consists of';
  $theHash{part_of}{html_field_name} = 'Part of';
  $theHash{equivalent_to}{html_field_name} = 'Equivalent to';
  $theHash{similar_to}{html_field_name} = 'Similar to';
  $theHash{rnai}{html_field_name} = 'RNAi';
  $theHash{locus}{html_field_name} = 'Locus';
  $theHash{allele}{html_field_name} = 'Allele';
  $theHash{strain}{html_field_name} = 'Strain';
  $theHash{comment}{html_field_name} = 'Comment';

  $theHash{phenotype_name}{html_comment} = 'WBphenotypeXXXXXXX, unique stable ID';
  $theHash{synonym}{html_comment} = 'All fields that are not UNIQUE can have
multiple entries separated by a "|".<BR>e.g. "Eat|Pie"';
  $theHash{description}{html_comment} = 'e.g. feeding abnormal, synopsis; use succinct free text<BR>e.g. "Eat worms often appear pale under dissecting scope, have slowed growth rate,<BR>and abnormal pharyngeal pumping behavior visible under DIC".<BR><FONT COLOR=red>UNIQUE</FONT> in acedb.';
  $theHash{evidence}{html_comment} = 'e.g. Paper_evidence [cgc1709]';
  $theHash{assay_type}{html_comment} = 'e.g. WBassayXXXXXXX, defined elsewhere<BR><FONT COLOR=red>UNIQUE</FONT> in acedb.';
  $theHash{assay}{html_comment} = 'currently in use, to be deprecated by Assay_type';
  $theHash{assay_condition}{html_comment} = 'e.g. cgc4489_adult<BR><FONT COLOR=red>UNIQUE</FONT> in acedb.';
  $theHash{remark}{html_comment} = '';
#   $theHash{remark}{html_comment} = 'comments for postgreSQL only';	# this doesn't seem right
#   $theHash{remark}{html_comment} = 'e.g. "Eat worms often appear pale under dissecting scope, have slowed growth rate,<BR>and abnormal pharyngeal pumping behavior visible under DIC".';
  $theHash{other}{html_comment} = 'e.g. feeding, use only if not defined in other categories already<BR>For the options below, either select a choice from the drop-down list,<BR>or create a new choice by leaving drop-down empty and typing in the input box.';
  $theHash{go_term}{html_comment} = 'e.g. GO:0000001<BR>See <a href="http://www.wormbase.org/db/ontology/goterm" target=NEW>List of GO_term objects</a> in <a href="http://www.wormbase.org" target=NEW>WormBase</a> Report.';
  $theHash{anatomy}{html_comment} = 'There are no objects yet.';
  $theHash{life_stage}{html_comment} = 'e.g. 1.5-fold embryo';
  $theHash{specialisation_of}{html_comment} = 'e.g. WBphenotype0000001, NOT "abc"<BR>denote ISA relationship';
  $theHash{generalisation_of}{html_comment} = 'e.g. WBphenotype0000001, NOT "abc"<BR>denote ISA relationship';
  $theHash{consist_of}{html_comment} = 'e.g. WBphenotype0000001, NOT "abc"<BR>denote PARTOF relationship';
  $theHash{part_of}{html_comment} = 'e.g. WBphenotype0000001, NOT "abc"<BR>denote PARTOF relationship';
  $theHash{equivalent_to}{html_comment} = 'e.g. WBphenotype0000001, NOT "abc"';
  $theHash{similar_to}{html_comment} = 'e.g. WBphenotype0000001, NOT "abc"';
  $theHash{rnai}{html_comment} = '';
  $theHash{locus}{html_comment} = '';
  $theHash{allele}{html_comment} = '';
  $theHash{strain}{html_comment} = '';
  $theHash{comment}{html_comment} = 'This field is for postgreSQL only, not acedb';

  $theHash{assay_type}{html_class_display} = 'Phenotype_assay';	# links to WormBase Display
  $theHash{assay_condition}{html_class_display} = 'Condition';
  $theHash{go_term}{html_class_display} = 'GO_term';
  $theHash{anatomy}{html_class_display} = 'Anatomy_term';
  $theHash{life_stage}{html_class_display} = 'Life_stage';
  $theHash{specialisation_of}{html_class_display} = 'Phenotype';
  $theHash{generalisation_of}{html_class_display} = 'Phenotype';
  $theHash{consist_of}{html_class_display} = 'Phenotype';
  $theHash{part_of}{html_class_display} = 'Phenotype';
  $theHash{equivalent_to}{html_class_display} = 'Phenotype';
  $theHash{similar_to}{html_class_display} = 'Phenotype';
  $theHash{rnai}{html_class_display} = 'RNAi';
  $theHash{locus}{html_class_display} = 'Locus';
  $theHash{allele}{html_class_display} = 'Allele';
  $theHash{strain}{html_class_display} = 'Strain';

  $theHash{specialisation_of}{html_pg_link} = 'Phenotype';	# links to PG display
  $theHash{generalisation_of}{html_pg_link} = 'Phenotype';
  $theHash{consist_of}{html_pg_link} = 'Phenotype';
  $theHash{part_of}{html_pg_link} = 'Phenotype';
  $theHash{equivalent_to}{html_pg_link} = 'Phenotype';
  $theHash{similar_to}{html_pg_link} = 'Phenotype';
  $theHash{anatomy}{html_pg_link} = 'Anatomy_term';
  $theHash{life_stage}{html_pg_link} = 'Life_stage';
  $theHash{assay_type}{html_pg_link} = 'Assay Type';
  $theHash{assay_condition}{html_pg_link} = 'Assay Condition';

  $theHash{other}{hash_type} = 'Aspect_info';		# this fields have this kind of hashes
  $theHash{go_term}{hash_type} = 'Aspect_info';
  $theHash{anatomy}{hash_type} = 'Aspect_info';
  $theHash{life_stage}{hash_type} = 'Aspect_info';
  $theHash{evidence}{hash_type} = 'Evidence';

  $theHash{assay_type}{xref} = 'Phenotype_Assay';	# this fields have this kind of xref's in acedb
#  $theHash{assay_condition}{xref} = 'Condition';	# this is not xref'ed
  $theHash{specialisation_of}{xref} = 'Phenotype';
  $theHash{generalisation_of}{xref} = 'Phenotype';
  $theHash{consist_of}{xref} = 'Phenotype';
  $theHash{part_of}{xref} = 'Phenotype';
  $theHash{equivalent_to}{xref} = 'Phenotype';
  $theHash{similar_to}{xref} = 'Phenotype';
} # sub initializeHash
  
########## theHASH ########## 





# Hi Juancarlos,
# 
# to begin our jamboree on curating phenotypes, i'd like to have a curation
# form. per our group meeting discussion two weeks ago, i think the form
# should optimally support easy data entry and the use of controlled
# vocabulary.
# 
# you already have a nice format for collaboration among curators to pick
# phenotypes to curate. to expand from that, in stead of having a big box to
# enter free text, we need to have more atomized and user friendly fields.
# 
# attached is a phenotype and related models file, the curation form should
# be constructed based on the models because we'll dump data out from
# CurationDB into .ace files.
# 
# here're some ideas:
# 
# 1. leftmost tags are major headings, such that
# 
#  Aspect_affected
#   Other [box for data entry]
#   GO_term [box for data entry]
#   ...
# 
# 2. where it says CV, provide a drop down list that list all that have been
# entered for the curator to chose from, and provide a box for
# new entry should the curator does not like any of the existing ones. this
# list should be updated dynamically based on what's been saved in the
# database.
# 
# 3. show notes (what comes after // in the models) on the form itself to
# guide data entry.
# 
# 4. where there's a hash (#), expand it into a full list of fields for
# data entry.
# 
# 5. where there's an object field (?xxx), allow an ace query (on a popup
# web page) to get at objects already present (in current WS) in that class.


# ?Phenotype	//WBphenotype:XXXXXXX, unique stable ID
# Synonym	?Text					//e.g. Eat
# Description UNIQUE ?Text				//e.g. feeding abnormal, synopsis; use succinct free text
# Aspect_affected	Other ?Text #Aspect_info	//e.g. feeding, use only if not defined in other categories already, CV
# 		GO_term ?GO_term XREF Phenotype #Aspect_info
# 		Anatomy ?Anatomy_term XREF Phenotype #Aspect_info
# 		Life_stage ?Life_stage XREF Phenotype #Aspect_info
# Evidence #Evidence					//e.g. Paper_evidence [cgc1709]
# Assay_type UNIQUE ?Phenotype_Assay XREF Assay_phenotype	//WBassay:XXXXXXX, defined elsewhere
# Assay      UNIQUE ?Text				//currently in use, to be deprecated by Assay_type
# Assay_condition UNIQUE ?Condition
# Remark ?Text						//e.g. "Eat worms often appear..."
# Related_phenotypes Specialisation_of ?Phenotype XREF Generalisation_of	//denote ISA relationship
#                    Generalisation_of ?Phenotype XREF Specialisation_of	//denote ISA relationship
#                    Consist_of ?Phenotype XREF Part_of				//denote PARTOF relationship
#                    Part_of ?Phenotype XREF Consiste_of			//denote PARTOF relationship
#                    Equivalent_to ?Phenotype XREF Equivalent_to
#                    Similar_to ?Phenotype XREF Similar_to
# Attribute_of       RNAi ?RNAi XREF Phenotype
#                    Locus ?Locus XREF Controlled_phenotype
# //                   GO_term ?GO_term XREF Phenotype #Evidence //remove, never been used as of WS98
#                    Allele ?Allele XREF Controlled_phenotype
#                    Strain ?Strain XREF Phenotype
# 
# 
# #Aspect_info
# Type ?Text	//behavior, histochemistry, CV (controlled vocabulary)
# Attribute Text	//rate, length, color, CV
# Value Text	//blue, abnormal, CV
# Qualifier Text	//sometimes, frequently, light, dark, CV
# 
# 
# //Existing model, never used, modified
# ?Phenotype_Assay							//WBassay:XXXXXXX, to be ontologized
# Description ?Text							//Visual-dissecting scope; Visual-DIC, CV
# Assay_phenotype ?Phenotype XREF Assay_type #Evidence
# Related_asaay Specialisation_of ?Phenotype_Assay XREF Generalisation_of	//denote ISA relationship
#               Generalisation_of ?Phenotype_Assay XREF Specialisation_of	//denote ISA relationship
#               Consist_of ?Phenotype_Assay XREF Part_of			//denote PARTOF relationship
#               Part_of ?Phenotype_Assay XREF Consiste_of			//denote PARTOF relationship
#               Equivalent_to ?Phenotype_Assay XREF Equivalent_to
#               Similar_to ?Phenotype_Assay XREF Similar_to
# 
# 
# //Existing model, modified, partial
# ?Allele
# Description Controlled_phenotype ?Phenotype XREF Allele #Evidence
# 
# 
# //Existing model, modified, partial
# ?Strain
# Phenotype ?Phenotype XREF Strain #Evidence
# 
# //Existing model, modified, partial
# ?Life_stage
# Attribute_of Phenotype ?Phenotype XREF Life_stage
# 
# 
# //Existing model, unmodified
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



# sub getClassList {
#   my $chosen_option = shift;
#   print <<"  EndOfText";
#   <TD></TD><TD>
#   <form target = "new" method="post" action="http://www.wormbase.org/db/searches/query" enctype="application/x-www-form-urlencoded">
#     <select name="class">
#       <OPTION selected>$chosen_option</OPTION>
#       <option value="Alignment">Alignment</option>
#       <option value="Allele">Allele</option>
#       <option value="Author">Author</option>
#       <option value="Briggsae_genomic">Briggsae_genomic</option>
#       <option value="Briggsae_loci">Briggsae_loci</option>
#       <option value="Briggsae_predicted">Briggsae_predicted</option>
#       <option value="cDNA_Sequence">cDNA_Sequence</option>
#       <option value="Cell">Cell</option>
#       <option value="Clone">Clone</option>
#       <option value="Condition">Condition</option>
#       <option value="Database">Database</option>
#       <option value="Deletion_allele">Deletion_allele</option>
#       <option value="Expr_pattern">Expr_pattern</option>
#       <option value="Expr_profile">Expr_profile</option>
#       <option value="Feature">Feature</option>
#       <option value="Feature_data">Feature_data</option>
#       <option value="Genetic_map">Genetic_map</option>
#       <option value="Gene_Class">Gene_Class</option>
#       <option value="Gene_name">Gene_name</option>
#       <option value="Genome_Sequence">Genome_Sequence</option>
#       <option value="GO_term">GO_term</option>
#       <option value="Grid">Grid</option>
#       <option value="Homol_data">Homol_data</option>
#       <option value="Insertion_allele">Insertion_allele</option>
#       <option value="Journal">Journal</option>
#       <option value="KeySet">KeySet</option>
#       <option value="KO_allele">KO_allele</option>
#       <option value="Laboratory">Laboratory</option>
#       <option value="Lineage">Lineage</option>
#       <option value="Locus">Locus</option>
#       <option value="Map">Map</option>
#       <option value="Method">Method</option>
#       <option value="Model">Model</option>
#       <option value="Motif">Motif</option>
#       <option value="NDB_Sequence">NDB_Sequence</option>
#       <option value="nematode_ESTs">nematode_ESTs</option>
#       <option value="Oligo">Oligo</option>
#       <option value="Other_Locus">Other_Locus</option>
#       <option value="Paper">Paper</option>
#       <option value="PCR_product">PCR_product</option>
#       <option value="Person">Person</option>
#       <option value="Person_name">Person_name</option>
#       <option value="Phenotype">Phenotype</option>
#       <option value="Phenotype_assay">Phenotype_assay</option>
#       <option value="Predicted_gene">Predicted_gene</option>
#       <option value="Protein">Protein</option>
#       <option value="Rearrangement">Rearrangement</option>
#       <option value="Restrict_enzyme">Restrict_enzyme</option>
#       <option value="RNAi">RNAi</option>
#       <option value="Sequence">Sequence</option>
#       <option value="Sequence_map">Sequence_map</option>
#       <option value="SK_map">SK_map</option>
#       <option value="Strain">Strain</option>
#       <option value="Substitution_allele">Substitution_allele</option>
#       <option value="Tag">Tag</option>
#       <option value="Transcript">Transcript</option>
#       <option value="Transgene">Transgene</option>
#       <option value="Transposon">Transposon</option>
#       <option value="Tree">Tree</option>
#       <option value="Url">Url</option>
#       <option value="UTR">UTR</option>
#       <option value="View">View</option>
#       <option value="Wormpep">Wormpep</option>
#     </select>
#     <input type="submit" name=".submit" value="See all Objects" />
#   </form></TD>
#   EndOfText
# } # sub getClassList

# sub displayVars {		# NOT NEEDED
#   $curator = &getCuratorFromForm();
#   print "Curator : $curator<BR>\n";
#   print "Phenotype Name : $theHash{phenotype_name}{html_value}<BR>\n";
#   print "<INPUT TYPE=\"HIDDEN\" NAME=\"phenotype_name\" VALUE=\"$theHash{phenotype_name}{html_value}\">\n";
#   print "<FONT COLOR = green>Reference : $theHash{reference}{html_value}</FONT><BR>\n";
#   print "<INPUT TYPE=\"HIDDEN\" NAME=\"reference\" VALUE=\"$theHash{reference}{html_value}\">\n";
#   print "<FONT COLOR = green>Definition : $theHash{definition}{html_value}</FONT><BR>\n";
#   print "<INPUT TYPE=\"HIDDEN\" NAME=\"definition\" VALUE=\"$theHash{definition}{html_value}\">\n";
#   print "<FONT COLOR = green>Comment : $theHash{comment}{html_value}</FONT><BR>\n";
#   print "<INPUT TYPE=\"HIDDEN\" NAME=\"comment\" VALUE=\"$theHash{comment}{html_value}\">\n";
# } # sub displayVars

# sub mailRnai {
#   my $user = 'rnai_curation';
# #   my $email = 'azurebrd@minerva.caltech.edu, bounce@minerva.caltech.edu';
# #   my $email = 'ranjana@eysturoy.caltech.edu, emsch@its.caltech.edu';
#   my $email = 'raymond@its.caltech.edu';
#   my $subject = 'rnai only curation';
#   my $body = '';
#   $body .= "Curator : $curator\n";
#   $body .= "PubID : $variables{pubID}\n";
#   $body .= "pdffilename : $variables{pdffilename}\n";
#   $body .= "Reference : $variables{reference}\n\n";
#   $body .= "Rnai : $variables{rnai}\n";
#   $body .= "Comment : $variables{comment}\n";
#   &mailer($user, $email, $subject, $body);
# } # sub mailRnai

sub dealPgOld {
  my $found = &findIfPgEntry('curator'); 
  if ($found) {					# do UPDATEs (Update !)
    my $result = $dbh->do( "UPDATE phe_reference SET phe_reference = '$theHash{reference}{html_value}' WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
    $result = $dbh->do( "UPDATE phe_reference SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
    $result = $dbh->do( "UPDATE phe_definition SET phe_definition = '$theHash{definition}{html_value}' WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
    $result = $dbh->do( "UPDATE phe_definition SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
    $result = $dbh->do( "UPDATE phe_curator SET phe_curator = '$curator' WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
    $result = $dbh->do( "UPDATE phe_curator SET phe_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$theHash{phenotype_name}{html_value}';" );
  } else {					# do INSERTs (New Entry !)
    my $result = $dbh->do( "INSERT INTO phe_curator VALUES ('$theHash{phenotype_name}{html_value}', '$curator', CURRENT_TIMESTAMP);" );
    $result = $dbh->do( "INSERT INTO phe_checked_out VALUES ('$theHash{phenotype_name}{html_value}', '$curator', CURRENT_TIMESTAMP);" );
    $result = $dbh->do( "INSERT INTO phe_reference VALUES ('$theHash{phenotype_name}{html_value}', '$theHash{reference}{html_value}', CURRENT_TIMESTAMP);" );
    $result = $dbh->do( "INSERT INTO phe_definition VALUES ('$theHash{phenotype_name}{html_value}', '$theHash{definition}{html_value}', CURRENT_TIMESTAMP);" );
  } # else # if ($found) 
  print "<P>The phenotype <FONT COLOR=green>$theHash{phenotype_name}{html_value}</FONT> has been Curated by $curator.<BR>\n";
} # sub dealPgOld

# sub ShowPgQuery {		# textarea box to make pgsql queries
#   print <<"EndOfText";
#   <BR>Would you like to make a PostgreSQL Query to the Curation Database ?<BR>
#   <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi">
#   <TEXTAREA NAME="pgcommand" ROWS=5 COLS=80></TEXTAREA><BR>
#   <INPUT TYPE="HIDDEN" NAME="curator_name" VALUE="$curator">
#   <INPUT TYPE="submit" NAME="action" VALUE="Pg !">
#   </FORM>
# EndOfText
# } # sub ShowPgQuery

sub displayHtmlCuration {
  print <<"EndOfText";
<A NAME="form"><H1>Add your entries : </H1></A><BR>

<FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_curation.cgi">

<!--<INPUT TYPE="HIDDEN" NAME="curator_name" VALUE="$curator">-->

<TABLE>
<TR>
  <TD ALIGN="right"><STRONG>Phenotype Name :</STRONG></TD>
  <TD><TABLE><TR><TD><INPUT NAME="phenotype_name" VALUE="$variables{phenotype_name}" SIZE=40></TD><TD><INPUT TYPE="submit" NAME="action" VALUE="Query !"></TR></TABLE></TD>
</TR>

<TR>
  <TD ALIGN="right"><STRONG>Curator :</STRONG></TD>
  <TD><TABLE><TR><TD><INPUT NAME="curator" VALUE="$curator" SIZE=40></TD></TR></TABLE></TD>
</TR>

<TR>
  <TD ALIGN="right"><STRONG>Reference :</STRONG></TD>
  <TD><TABLE></TD><TD><TEXTAREA NAME="reference" ROWS=5 COLS=80>$variables{reference}</TEXTAREA></TD></TR></TABLE></TD>
</TR>

<TR>
  <TD ALIGN="right"><STRONG>Defintion :</TD>
  <TD><TABLE></TD><TD><TEXTAREA NAME="definition" ROWS=10 COLS=80>$variables{definition}</TEXTAREA></TD></TR></TABLE></TD>
</TR>

<TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>


<TR><TD COLSPAN=2> </TD></TR>
<TR>
  <TD> </TD>
  <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
    <!--<INPUT TYPE="submit" NAME="action" VALUE="Save !">
    <INPUT TYPE="submit" NAME="action" VALUE="Load !">-->
    <INPUT TYPE="reset" VALUE="Reset !"></TD>
</TR>
</TABLE>

</FORM>
EndOfText
} # sub displayHtmlCuration



