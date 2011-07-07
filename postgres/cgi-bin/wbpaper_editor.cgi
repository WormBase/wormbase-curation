#!/usr/bin/perl -w

# Edit WBPaper data ;  check out for first-pass curation

# Preliminary display of wbp_ tables from the demo4 database.  Table columns
# don't necessarily start with wbp_ some tables don't have data.  Allow query
# by either : a number, an author (or substring), a title (or substring).
# 2005 03 04
#
# Added display of PDFs from Daniel's repository by checking against the 
# wbp_identifier table to find cgc and pmid.  
# Added display of wbp_identifier table.
# Merged hardcopy and type table with generic tables, resulting in a display
# with too many n/a entries.  Hopefully can be cleaned up by adding comments
# to all generic tables, putting privacy somewhere else (a different table),
# and merging type id and data in the display (this form) and editor.
# 2005 03 21
#
# Modified for wpa_ tables.  2005 06 29
#
# Refined Number search, explanation text for Author and Title search.
# List all PDFs that could match.
# List all Author connection data (affiliation, possibles, sents, verifieds)
# List electronic and hardcopy status.
# List identifier xrefs.
# List wpa (to see whether the paper at all is valid or not.)  2005 06 30
#
# &documentation() written.  2005 07 21
#
# &cdsQueryPage(); and &cdsQuery(); written to allow batch CDS query for Andrei.
# 2005 07 26
#
# use wpa_identifier instead of wpa_xref for number search.  2005 07 27
#
# Added // to Pages documentation.  Added text about abstract editing and 
# WBGene - CDS connections to documentation.  Added 3-letter gene in 
# parenthesis next to WBGene - CDS display.  2005 08 01
#
# Added searches by Journal, Pages, Volume, Year, Abstract.  Documented
# usage.  For Daniel.  2005 08 02
#
# Added a display of all WBPapers broken up into pages (number per page in
# $options{num_per_page}) with the option to &sort("date") &sort("number")
# and &sort("journal").  It displays the page number, sort type, and links
# to each paper showing data for that paper.  Documented usage.  For Daniel.
# 2005 08 03
#
# Added a new wpa_type_index value :  17 -> OTHER  for Ranjana for parsing
# data from Pubmed, for fields that may not match postgres types.  2005 08 03
#
# Fixed updating of @author_types, which was messing up getting the html value
# by changing author_type when inserting the first value into postgres.
# Fixed slowness from get_paper_ace.pm, which was loading type and author
# index data whenever the .pm got loaded, instead of whenever the 
# &getPaper($joinkey); got called.  2005 08 08
#
# Added PMID insertion of new PMIDs to create, or to check pubmed and update
# the entry if it already exists.  If it's ambiguous, it will write to 
# /home/postgres/work/pgpopulation/wpa_papers/wpa_new_wbpaper_tables/perl_wpa_match/manual_check_file.endnote
# and email ranjana and daniel to manually check whether they should be merged
# or created.  Uses &processPubmed(); from wpa_match.pm
# Added Merge / Create section that looks at the same file and allows Merging
# or Creating of a paper using &processForm(); from wpa_match.pm
# Set cronjob to check for CGC updates from Theresa
# 0 3 * * tue,wed,thu,fri,sat /home/postgres/work/pgpopulation/wpa_new_wbpaper_tables/perl_wpa_match/cgc/cgc_to_wpa_with_module.pl
# using &processEndnote(); from wpa_match.pm
# 2005 08 17
#
# Update wpa_valid to have ``misattributed'' instead of ``old''.  for Ranjana.  2005 08 17
#
# Updated form to work as a checkout form by linking to curation.cgi under
# &sortLink($joinkey);
# Updated curation.cgi to work with wbpaper style joinkeys.  2005 08 22
#
# Added Mary Ann Tuli, link to front page and to curate after ``Update Info !''.  2005 09 10
#
# Filter loci_all to read synonyms first, then 3-letter loci, since chs-1 and
# chs-2 are synonyms of each other and overwrite the 3-letter making the entry
# bad.
# Change Display All to sory by Number or Date based on radio button, and
# instead sort by  All papers ;  All papers minus Meeting Abstracts ;  All
# papers minus curated papers.
# Add RNAi flagging/checkout/curation by populating wpa_rnai_curation based on
# ref_checked_out (where ref_checked_out ~ 'RNAi') for Igor.  It just sets as
# flagged since RNAi curation takes place elsewhere.  2005 09 19
#
# Red text at the top if a paper is invalid.
# Remark gets automatically populated by 
# 0 3 * * wed /home/postgres/work/pgpopulation/wpa_new_wbpaper_tables/wpa_remark/populateMerged.pl
# Added wpa_remark to @generic_tables to display.  2005 09 27
#
# Had messed up for loop from 0 .. $skip_num instead of 1 .. $skip_num, so 
# first one wasn't showing.  Fixed to 1 ..  2005 09 29
#
# Affiliation wasn't being captured from not being within singlequotes in pg
# command.  %auth_name was sorting by DESC timestamp, so oldest value was stored
# instead of most recent valid value.  2005 10 12
#
# Created &displayGenericPostgresRow(); which increments the $row_count, and
# diplays the postgres data.  This allows the $history_or_valid flag in
# &displayOneDataFromKey(); to either show data as is queried when showing all
# history data, or to filter invalids out and show only valid data.  2005 10 27
#
# Created &displayGenePostgresRow(); &diplayAuthorTypePostgresRow();
# &displayFullAuthorPostgresRow(); &displayPdfPostgresRow(); to work like
# &displayGenericPostgresRow(); and allow valid / historic toggle of other
# displays.  The author name / possible / sent / verified still show historic
# only, since being a merge of 3 tables it would be unclear what the invalid
# would refer to.  Further, that data should never be invalid, if it's wrong it
# should just be deleted as there is no point in keeping track of errors there.
# 2005 11 04
#
# Added an example for CDS connections to the documentation.
# Pad Zeros for the joinkey when updating info (for postgres).  2005 11 08
#
# &createAuthors(); was creating entries in wpa_author_possible / sent /
# verified without a wpa_join value, which is probably wrong, so no longer
# doing it.  2005 11 22
#
# added option to &sortPapers(cgc); which ignores sort by date option since
# it always sorts by cgc number.  for Theresa  2005 11 23
#
# Change &displayGenericPostgresRow(); to convert " to &quot; > to &gt; and 
# < to &lt;  Also had to change &untaint(); in Jex.pm to allow \> and \< which
# were getting stripped there.  2005 12 13
#
# Allow Published_as evidence tag, for Kimberly.  2006 01 20
#
# Gene display was not working properly because it was keying off of genes,
# instead of a combination of genes + evidence.  Gene data also has tabs in it,
# so need to use TABDIVIDER instead of real tab.  2006 01 23
#
# Added hyphen to Published_as possibility.  2006 02 03
#
# Don't include repeats if a paper's been valid and invalid  2006 02 27
#
# Convert " to &quot; in HIDDEN value of evidence data in genes to allow
# invalidating it.  2006 05 11
#
# Not Curated button now filters out invalid WBPapers as well as meeting
# abstracts.  2006 05 18
#
# Added new wpa_type_index WormBook for Igor and Todd making 18  2006 06 02
#
# No meetings &c. also include email and Gazette abstracts.  for Andrei
# 2006 06 29
#
# Added Anthony Rogers and Xiadong Wang   2006 08 23
#
# Added link to PDF in the editor section for Andrei  2006 09 07
#
# Updated to use gin_locus, gin_synonym, and gyn_sequence based on nameserver
# and aceserver instead of the no-longer-updated loci_all.txt and
# genes2molecular_names.txt  2006 12 22
#
# added option to &sortPapers(c_elegans); which ignores cur_comment for
# functional annotation only.  2007 01 05
#
# wpa_author_index wasn't filter affiliation for apostrophes.  2007 03 08
#
# Added Allele checkout (from Mutant Phenotype i.e. cur_newmutant) and Transgene
# checkout (from Overexpression i.e. cur_overexpression), to work like RNAi
# checkout.  Changed &curateRNAi(); to &curateType('RNAi'); (or Transgene or
# Allele).  Changed &sortRNAi(); to &sortType('RNAi'); &c.  Likewise for
# &sortTypeLink() and &sortTypePage().  Added wpa_trasgene_curation and
# wpa_allele_curation.  New data only looks at one table, not at two (i.e.
# cur_rnai and cur_lsrnai).  For Gary.  2007 05 02
#
# Took out Eimear, added Jolene Fernandes.  2007 06 13
#
# Added Karen Yook.  2007 08 01
#
# Added an option when checking out for Allele or Overexpression to enter
# WBPapers to a list that has been curated for that type, but not necessarily
# been first-pass curated.  When displaying the list for type curation, also
# show these papers from this list.  2007 08 01
#
# Filter spaces was mistakenly replacing all the middle spaces with a single
# space, which got rid of ``correct'' tabs (and other stuff, which was probably
# not correct).  Evidence then expected a space, which now allows for a tab or
# any other \s+
# The word WBPaper is now allowed in the number when searching by number.
# 2007 08 31
#
# When adding to the list of CuratedNoFP, check if it has been first-pass curated, 
# then check if it has appropriate first-pass data, and if it doesn't say ``yes''.
# For Gary and Karen   2007 10 01
#
# pmid was failing if no paper type, would simply say there were no matches for
# that paper type (the lack of it).  2008 04 16
#
# Added &checkboxUpdate('rnai_int_done'); to deal with checkboxes refering to 
# whether RNAi based Interaction has been finished for that paper.  Modified
# RNAi Curation page to display checkboxes if dealing with RNAi.  For Gary
# 2008 05 06  
#
# Switch Chey Loveday with Paul Davis.  2008 07 25
#
# Use wpa_ignore instead of cur_comment for displaying the ignorability of a
# paper.  Change wpa_match.pm to insert to cur_comment and wpa_ignore.  2008 10 08
#
# Allow entering of false positives into cur_ tables ``False Positives !'' by 
# selecting the table from a drop-down menu, and entering the data into a TEXTAREA
# one per line : wbpaper ID, followed by a whitespace, followed by the comment.
# Data going in is the wbpaper ID for joinkey, comment -- curator name for data, 
# current timestamp for timestamp.  For Wen and Xiaodong and whoever.  2009 01 24
#
# Append to data when marking a false positive instead of overwriting.
# Mark it as ``FALSE POSITIVE : comment -- curator'' instead of not explicitly 
# stating that it's a false positive.
# Add ``Show False Positive !'' button to display what's been flagged as a false
# positive.  
# Added a joinkey substring search when displaying all papers for first pass
# checkout.
# For Xiaodong.  2009 01 29
#
# Put pmid abstract confirmation here for Kimberly and Arun.  2009 02 18
#
# When sorting papers for FP checkout, get list of papers from textpreso that
# have body text, and show in grey font if they lack it.  New option to sort
# by not curated and with textpresso body text.  For Karen.   2009 02 24
#
# Added ``TestNewForm'' link next to ``curate'' link when checking out a paper.
# Does not update wpa_checked_out.  2009 03 22
#
# Link live to curator_first_pass.cgi, updates wpa_checked_out.  2009 04 06
#
# udpated &getFirstPassTables() to use curator_first_pass.cgi  2009 04 06
#
# programmatically access list of invalid papers (and no curatable and 
# functional annotation only at 
# http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?curator_name=two1823&action=listInvalidNocuratableFunctional
# by calling &listInvalidNocuratableFunctional();
# 2009 04 07
#
# Converted from Pg.pm to DBI.pm  2009 04 17
#
# show PMID confirmation before entering new pmids for Kimberly only.  2009 04 19
#
# Renamed &sortPapers to &getSortPapers and merged in &getSortPage.  
# Created %sortPapers  which has the info for keys for sorting when checking out papers.
# Created &populateInvalidPapers(); &populateCuratorNotFP(); &populateTextpressoBody();
#   &populateAuthorFP(); &populateAuthorEmailed(); &populatePaperAbstract();
#   &populatePaperWormbook(); &populatePaperReview(); &populatePaperIgnore(); 
#   &populateCurators(); to populate sorting key information to display in paper checkout.
# Created %sortDisplayHash to show color, description, and checked status of each of 
#   the possible filtering keys.
# No longer have sorting by number or timestamp.  No longer have sorting by Curator.
# 2009 04 22
# 
# Added buttons for "Not Curated plus Author plus Textpresso !", "All Papers !"
# "All Minus Abstracts !"  for Daniel mostly.  2009 04 23
#
# When entering alrady curated data, check if row exists and has data (skip), otherwise :
# if row exists and has no data delete main entry.  enter data into main and _hst.  2009 07 14
#
# Added Margaret Duesbury  2009 07 16
#
# Added extvariation to FP and already curated lists.  2009 07 17
#
# select curator by IP if IP has already been used, update two_curator_ip if IP has a 
# different curator.  
# &readCurrentLocus(); took 6-7 seconds.  now querying each wbgene for locus, or using 
# ajax call
# &getPaper($joinkey); took 12 seconds, so moved it to its own button.  2009 09 03
 


use strict;
use CGI;
use Fcntl;
# use Pg;
use DBI;
use Jex;
use LWP::UserAgent;
use LWP::Simple;
use POSIX qw(ceil);
use Tie::IxHash;

use lib qw( /home/postgres/work/citace_upload/papers/old/ );
use get_paper_ace;			# .ace style dumper
# use lib qw( /home/postgres/work/pgpopulation/wpa_new_wbpaper_tables/perl_wpa_match );
use lib qw( /home/postgres/work/pgpopulation/wpa_papers/wpa_new_wbpaper_tables/perl_wpa_match );
use wpa_match qw( processPubmed processLocal processForm );


my $query = new CGI;

# my $conn = Pg::connectdb("dbname=testdb");
# die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "");
if ( !defined $dbh ) { die "Cannot connect to database!\n"; }


my $frontpage = 1;
my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color


my %theHash;

my %curators;				# $curators{two}{two#} = std_name ; $curators{std}{std_name} = two#

my %sortPapers;				# hash of WBPapers sorting info
my %sortDisplayHash; tie %sortDisplayHash, "Tie::IxHash";		# sorted hash of filtering keys when looking at paper for checkout
my %type_index;				# hash of possible 18 types of paper
my %electronic_type_index;		# hash of possible 7 types of electronic paper
&populateTypeIndex();	
my %cdsToGene;				# cds and locus to wbgene conversion from sanger's loci_all.txt and genes2molecular_names.txt
					# cds and locus to wbgene conversion from sanger's nameserver's and cshl's aceserver's data in postgres's gin_ tables
my %auth_name;				# hash of author names by author_id

my %ignore_extras;
my @fptables;				# first pass tables



# my @generic_tables = qw( title publisher journal volume pages year abstract affiliation comments paper );

my @generic_tables = qw( wpa wpa_remark wpa_identifier wpa_title wpa_publisher wpa_journal wpa_volume wpa_pages wpa_year wpa_date_published wpa_fulltext_url wpa_abstract wpa_affiliation wpa_hardcopy wpa_comments wpa_editor wpa_nematode_paper wpa_contained_in wpa_contains wpa_keyword wpa_erratum wpa_in_book wpa_ignore wpa_type wpa_author );
my @author_types = qw(index possible sent verified);

my %options;
my %tables;
&initializeTables();

&display();


### DISPLAY ###

sub display {
  my $action;
  unless ($action = $query->param('action')) { $action = 'none'; }
    else { $frontpage = 0; }

  my $header = '';
  if ($action eq 'abstract_text') { &abstract_text(); return; }
    else { $header = &getHeader('WBPaper Editor'); }

  my ($header1, $header2) = $header =~ m/^(.*?)(<HEAD>.*)$/ms;

#   $header1 .= '<link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" /><link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/curator_first_pass.css" /><script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/test.js"></script><script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/curator_first_pass.js"></script>';
  $header1 .= '<link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" />';
  $header = $header1 . "\n" . $header2;
  print $header;

  print "<CENTER><B><FONT COLOR='RED'>THIS FORM IS NOW DEPRECATED.  ANY CHANGES YOU MAKE HERE WILL BE STORED BUT NOT USED FOR ANYTHING<br/><a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi\">new paper editor</a></B></FONT></CENTER><P>\n";

  print "<CENTER><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?action=Documentation+%21\" TARGET=NEW>Documentation</A></CENTER><P>\n";

  if ($frontpage) { &firstPage(); return; }
  if ($action eq 'Documentation !') { &documentation(); return; }	# doesn't require a curator chosen

  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";
  my ($oop, $curator) = &getHtmlVar($query, 'curator_name');
  if ($curator) { 
    $theHash{curator} = $curator;
    print "Curator : $curator<P>\n"; 
    &updateCurator($curator);
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$theHash{curator}\">\n"; }
  else { print "<FONT COLOR='red'>ERROR : You must choose a curator.<BR>\n"; return; }

  if ($action eq 'Number !') { &pickNumber(); }
  elsif ($action eq 'Show Valid !') { &pickNumber(); }
  elsif ($action eq 'Show History !') { &pickNumber(); }
  elsif ($action eq 'Author !') { &pickAuthor(); }
  elsif ($action eq 'Title !') { &pickTitle(); }
  elsif ($action eq 'Journal !') { &pickJournal(); }
  elsif ($action eq 'Pages !') { &pickPages(); }
  elsif ($action eq 'Volume !') { &pickVolume(); }
  elsif ($action eq 'Year !') { &pickYear(); }
  elsif ($action eq 'Abstract !') { &pickAbstract(); }
  elsif ($action eq 'Enter New Papers !') { &newPapers(); }
  elsif ($action eq 'Confirm Abstracts !') { &confirmAbstracts(); }
  elsif ($action eq 'Merge with this Paper !') { &mergeNewPaper(); }
  elsif ($action eq 'Create New Paper !') { &createNewPaper(); }
  elsif ($action eq 'Enter PMIDs !') { &enterPmids(); }
#   elsif ($action eq 'Display All !') { &getSortPapers("all_papers"); }
#   elsif ($action eq 'Display All !') { &getSortPapers("date"); }
#   elsif ($action eq 'Sort by Date !') { &getSortPapers("date"); }
#   elsif ($action eq 'Sort by Number !') { &getSortPapers("number"); }
#   elsif ($action eq 'Sort by Journal !') { &getSortPapers("journal"); }
  elsif ($action eq 'Sort Papers !') { &getSortPapers("sort_papers"); }
#   elsif ($action eq 'All Papers !') { &getSortPapers("all_papers"); }
#   elsif ($action eq 'No Meetings !') { &getSortPapers("no_meeting"); }
#   elsif ($action eq 'Not Curated !') { &getSortPapers("not_curated"); }
  elsif ($action eq 'Not Curated plus Textpresso !') { &getSortPapers("not_curated_plus_textpresso"); }
  elsif ($action eq 'Not Curated plus Author plus Textpresso !') { &getSortPapers("not_curated_plus_author_plus_textpresso"); }
#   elsif ($action eq 'C elegans !') { &getSortPapers("c_elegans"); }
#   elsif ($action eq 'CGC !') { &getSortPapers("cgc"); }
#   elsif ($action eq 'by Curator !') { &getSortPapers("by_curator"); }
  elsif ($action eq 'Specific Paper !') { &getSortPapers("specific_paper"); }
  elsif ($action eq 'All Papers !') { &getSortPapers("all_papers"); }
  elsif ($action eq 'All Minus Abstracts !') { &getSortPapers("all_minus_abstracts"); }
  elsif ($action eq 'RNAi Curation !') { &sortType('RNAi'); }
  elsif ($action eq 'Overexpression Curation !') { &sortType('Overexpression'); }
  elsif ($action eq 'Allele Curation !') { &sortType('Allele'); }
  elsif ($action eq 'RNAi Curate !') { &curateType('RNAi'); }
  elsif ($action eq 'Everything Curation !') { &sortAll('Everything'); }
  elsif ($action eq 'Overexpression Curate !') { &curateType('Overexpression'); }
  elsif ($action eq 'Allele Curate !') { &curateType('Allele'); }
  elsif ($action eq 'Extra !') { &pickExtra(); }
  elsif ($action eq 'Add Another Author !') { &addAnotherAuthor(); }
  elsif ($action eq 'Create Authors !') { &createAuthors(); }
# not needed anymore since it should auto convert the CDS to a WBGene  2009 09 03
#   elsif ($action eq 'CDS Query Page !') { &cdsQueryPage(); }
#   elsif ($action eq 'CDS Query !') { &cdsQuery(); }
  elsif ($action eq 'Update Info !') { &updateInfo(); }
  elsif ($action eq 'Allele Curated no FP !') { &curatedNoFP('allele'); }
  elsif ($action eq 'Overexpression Curated no FP !') { &curatedNoFP('overexpr'); }
  elsif ($action eq 'RNAi Int Done Checkbox Update !') { &checkboxUpdate('rnai_int_done'); }
  elsif ($action eq 'Already Curated !') { &alreadyCurated(); }
  elsif ($action eq 'Enter Already Curated !') { &enterAlreadyCurated(); }
  elsif ($action eq 'False Positives !') { &falsePositives(); }
  elsif ($action eq 'Enter False Positives !') { &enterFalsePositives(); }
  elsif ($action eq 'Show False Positives !') { &showFalsePositives(); }
  elsif ($action eq 'listInvalidNocuratableFunctional') { &listInvalidNocuratableFunctional(); }
  elsif ($action eq 'See .ace Entry !') { &seeAceEntry(); }
  else { 1; }
  print "</FORM>\n";

  if ($action ne 'abstract_text') { &printFooter(); }
} # sub display

sub curateType {
  my $type = shift;
  &populateCurators();
  my ($oop, $curator) = &getHtmlVar($query, 'curator_name');
  ($oop, my $joinkey) = &getHtmlVar($query, 'wbpaper_number');
  my $two_num = $curators{std}{$curator};
  my $pgtable = 'wpa_' . lc($type) . '_curation';
  if ($type eq 'Overexpression') { $pgtable = 'wpa_transgene_curation'; }
  my $pg_command = "INSERT INTO $pgtable VALUES ('$joinkey', '$two_num', NULL, 'valid', '$two_num', CURRENT_TIMESTAMP); ";
#   my $result = $conn->exec( $pg_command );
  my $result = $dbh->prepare( $pg_command );
  $result->execute;
  print "$pg_command<BR>\n";
  print "$joinkey flagged as curated for $type by $curator .<BR>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"$type Curation !\">\n";
} # sub curateType

sub filterSpaces {
  my $value = shift;
  if ($value =~ m/^\s+/) { $value =~ s/^\s+//; }
  if ($value =~ m/\s+$/) { $value =~ s/\s+$//; }
#   if ($value =~ m/\s+/) { $value =~ s/\s+/ /g; }	# don't want this, gets rid of tabs 2007 08 31
  return $value;
} # sub filterSpaces

# sub filterForPg {		# in Jex.pm
#   my $value = shift;
#   if ($value =~ m/\'/) { $value =~ s/\'/''/g; }
#   return $value;
# } # sub filterForPg

sub padZeros {
  my $joinkey = shift;
  if ($joinkey =~ m/^0+/) { $joinkey =~ s/^0+//g; }
  if ($joinkey < 10) { $joinkey = '0000000' . $joinkey; }
  elsif ($joinkey < 100) { $joinkey = '000000' . $joinkey; }
  elsif ($joinkey < 1000) { $joinkey = '00000' . $joinkey; }
  elsif ($joinkey < 10000) { $joinkey = '0000' . $joinkey; }
  elsif ($joinkey < 100000) { $joinkey = '000' . $joinkey; }
  elsif ($joinkey < 1000000) { $joinkey = '00' . $joinkey; }
  elsif ($joinkey < 10000000) { $joinkey = '0' . $joinkey; }
  return $joinkey;
} # sub padZeros

sub updateCurator {
  my ($curator) = @_;
  &populateCurators();
  if ($curators{std}{$curator}) { 
    my $joinkey = $curators{std}{$curator};
    my $ip = $query->remote_host(); 
    my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip' AND joinkey = '$joinkey';" );
    $result->execute;
    my @row = $result->fetchrow;
    unless ($row[0]) {
      $result = $dbh->do( "DELETE FROM two_curator_ip WHERE two_curator_ip = '$ip' ;" );
      $result = $dbh->do( "INSERT INTO two_curator_ip VALUES ('$joinkey', '$ip')" );
      print "IP $ip updated for $curator, $joinkey<br />\n"; } } }

sub documentation {
  print "<TABLE border=0 cellspacing=2>\n";
#   print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD>Possible</TD><TD>Sent</TD><TD>Verified</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Front Page</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Curator</TD><TD>Select your name as a curator.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Search parameter</TD><TD>Enter search parameter for any of the three search options, the click the appropriate button, this will only search the parameter that corresponds with the button clicked.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Number</TD><TD>Search for a WBPaper number ; cgc#### ;  pmid######### ;  euwm####### (etc.) ;  or simply a number, which will match if any WBPaper, cgc, pmid, etc. match.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Author</TD><TD>Enter the exact Author name (in a Paper) that you'd like to search for (e.g. ``Sternberg PW'') or just part of it (e.g. ``Sternberg'' or ``PW'').  See  Exact or Substring  below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Title</TD><TD>Enter the exact Title name (in a Paper) that you'd like to search for (e.g. ``dig-1 encodes an adhesion molecule involved in sensory map formation.'') or just part of it (e.g. ``dig-1'' or ``encodes an adhesion molecule'').  See  Exact or Substring  below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Journal</TD><TD>Enter the exact Journal name (in a Paper) that you'd like to search for (e.g. ``Developmental Biology'') or just part of it (e.g. ``Biology'').  See  Exact or Substring  below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Pages</TD><TD>Enter the exact Pages data (in a Paper) that you'd like to search for (e.g. ``403//409'') or just part of it (e.g. ``403'').  See  Exact or Substring  below.<BR>Different pages are separated by ``//''.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Volume</TD><TD>Enter the exact Volume data (in a Paper) that you'd like to search for (e.g. ``118//2'') or just part of it (e.g. ``118'').  See  Exact or Substring  below.<BR>Different volume data are separated by ``//''.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Year</TD><TD>Enter the exact Year data (in a Paper) that you'd like to search for (e.g. ``2005'') or just part of it (e.g. ``200'').  See  Exact or Substring  below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Abstract</TD><TD>Enter the exact Abstract name (in a Paper) that you'd like to search for (e.g. ``Applying a series of techniques intended to induce, detect and isolate lethal and/or sterile temperature-sensitive mutants, specific to the sel f-fertilizing hermaphrodite nematode Caenorhabditis elegans, Bergerac strain, 25 such mutants have been found. Optimal conditions for the application of muta genic treatment and the detection of such mutations are discussed.'') or just part of it (e.g. ``Applying a series of techniques'').  See  Exact or Substring  below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Exact or Substring</TD><TD>This radio toggle works only on Author and Title searches.  The default is a Substring search that will match if any part of the Author/Title matches the search parameter.  The Exact option will match if a full author or a full title matches _exactly_ the parameter you enter.  This is not recommended in general in case there's a typo in the paper or in the search parameter, but in the case of a very wide parameter, this could be useful (e.g.  Exact search of ``Lee RYN'' vs  Substring search of ``Lee'')</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Not Curated plus Textpresso !</TD><TD>By default show all WBPapers that are not curated and are in Textpresso in groups of 20 sorted by descending Date and allow checkout for first pass curation.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>False Positives !</TD><TD>Select a first pass curation table, and enter WBPapers followed by whitespace followed by a comment to set the first pass cfp_ table as a false positive with data being what was there before, FALSE POSITIVE : the comment -- curator name.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Show False Positives !</TD><TD>Select a first pass curation table and show the FALSE POSITIVE matches in that cfp_ table</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Already Curated !</TD><TD>Select a first pass curation table, and enter WBPapers followed by whitespace followed by data to set the first pass cfp_ table as having this data.  If no data, it will write ``checked''.  Will neither overwrite nor append if it already has data, having already been first passed.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>RNAi Curation !</TD><TD>Show all WBPapers with RNAi or Large Screen RNAi data from first-pass curation in groups of 20 sorted by ascending joinkey and allow flagging for RNAi curation.  Option to change entries per page and search for a WBPaper number substring.  Checkboxes to mark a paper as completely curated, then use ``RNAi Int Done Checkbox Update !'' button.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Allele Curation !</TD><TD>Show all WBPapers with Mutant Phenotype data from first-pass curation in groups of 20 sorted by ascending joinkey and allow flagging for Allele curation.  Option to change entries per page and search for a WBPaper number substring.  Option to add WBPapers to a list of Allele curated but not necessarily first-pass curated, also display data from this list intermingled with the first-pass curated list.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Allele Curated no FP !</TD><TD>Add the WBPapers from the box into the list of Papers that have been curated for Allele data but not necessarily been first-pass curated.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Overexpression Curation !</TD><TD>Show all WBPapers with Overexpression data from first-pass curation in groups of 20 sorted by ascending joinkey and allow flagging for Transgene curation.  Option to change entries per page and search for a WBPaper number substring.  Option to add WBPapers to a list of Overexpression curated but not necessarily first-pass curated, also display data from this list intermingled with the first-pass curated list.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Overexpression Curated no FP !</TD><TD>Add the WBPapers from the box into the list of Papers that have been curated for Overexpression data but not necessarily been first-pass curated.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Enter New Papers !</TD><TD>Enter PMIDs to update or create.  Manually check possible matches from new incoming papers from automatic CGC cronjob or PMIDs through this form</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Author Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Author String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Author ID ;  Author Name for the Author ID ;  Title of WBPaper ; Journal of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Title Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Title String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Title of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Journal Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Journal String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Journal Data ;  Title of WBPaper ; Journal of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Pages Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Pages String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Pages Data ;  Title of WBPaper ; Journal of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Volume Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Volume String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Volume Data ;  Title of WBPaper ; Journal of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Year Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Year String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Year Data ;  Title of WBPaper ; Journal of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Abstract Search</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name, and the Abstract String you searched for.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>Count of matches followed by : WBPaper link ;  Abstract Data ;  Title of WBPaper ; Journal of WBPaper.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Sorting / First-pass-checkout Page (from Not Curated plus Textpresso or Sort Papers or Specific Paper)</B></TD></TR>\n";
#   print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name ;  how many entries per page and sorting type ;  how many entries total, the number of pages, and the current page number ;  an option to select a new page number and buttons to choose the type of search.</TD></TR>\n";
#   print "<TR bgcolor='$blue'><TD>Sort Options</TD><TD>Sort by Number or Sort by Date radio button.  Buttons to show All Papers ;  All Papers minus meeting abstracts ;  All papers minus first-pass curated minus meeting abstracts minus obsolete wbpapers ;  All papers minus first-pass curated minus meeting abstracts minus obsolete wbpapers minus papers without Textpresso body text;  CGC papers only sorted by cgc number descending (ignores sort by date radio button) ;  All Papers minus those checked for functional annotation only ;  sorting by Curator only (ignores dataset and shows all papers) ;  sorting by a specific Paper (substring search).</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name ;  option to search for a specific number ;  key and checkboxes to filter results  ;  how many entries total, the number of pages, and the current page number ;  an option to select a new page number.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Sort Options</TD><TD>Red options are by default not showing, check them on to see them  (invalid papers, wpa_ignore papers, wormbook, review, abstracts, authors emailed in the past 7 days).  Other options will only show results that have these categories if checked  (not curated by curator, has textpresso body text, author has first passed it, author has been emailed).</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>A link to the WBPaper number ;  the key sorting values ;  all matching identifiers ;  the journal ;  whether there's a hardcopy ;  a link to all PDFs ;  the title ;  the last curator that checked out the paper ;  the last curator that curated the paper ;  a link to curate that paper.  If the paper lacks Textpresso body text, the font is grey.</TD></TR>\n"; 
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>RNAi-checkout/flagging Page</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Parameters</TD><TD>Display of your Curator name ;  how many entries per page ;  how many entries total, the number of pages, and the current page number ;  an option to select a new page number and buttons to choose the page.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Results</TD><TD>A link to the WBPaper number ; all matching identifiers ;  a link to all PDFs ;  the last curator that first-pass curated the paper ;  the first 40 words of the first-pass rnai curation data ;  the last curator that rnai-curated the paper ;  a link to flag the paper as rnai curated.</TD></TR>\n"; 
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Main Editing Page</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Curator</TD><TD>The curator's name.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Number</TD><TD>The WBPaper number ;  a link to first-pass checkout and curate this WBPaper.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Functional Annotation</TD><TD>If the paper was entered by Erich for functional annotation only, check the cfp_comment entry for the value and display it.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Show Valid / History !</TD><TD>Buttons to display only Valid data or the whole history (valid and invalid).  A line showing which option has been chosen (default is valid).  The author_index, affiliation, possible, sent, and verified always filter out any wpa_author data where wpa_valid is not valid.  The summary of Author Name / Possible / Sent / Verified always shows historic data, since being a mix of 3 data types, it wouldn't be clear which is valid and which invalid.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Main Editing Section Table Menu</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>ID</TD><TD>The postgres identifier for table queries.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Table</TD><TD>The name of the postgres table for that field.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Data</TD><TD>The data values stores in those tables.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Order</TD><TD>Where applicable, the order in which they will be written in the .ace file.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Valid</TD><TD>A checkbox for data that can be valid (checked) or invalid (unchecked).  A drop down menu for data that could be historic (misattributed)</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Update</TD><TD>Check to indicate you'd like to update this data.  Unchecked boxes won't update that row of data.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Curator</TD><TD>Who last curated that data.  If you update this it will attach your WBPerson number, not the one showing.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Timestamp</TD><TD>When this data was last updated.  If you update this it will attach the current timestamp, not the one showing.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Main Editing Section Table Fields</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Existing Lines</TD><TD>Data that already exists in postgres.<BR>To get rid of this data, set the valid checkbox as unchecked, click its Update checkbox, and click the ``Update Info !'' button.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Blank Lines</TD><TD>Blank to allow new data in postgres.<BR>If you are creating new data, enter it here, check its Update checkbox, and click the ``Update Info !'' button.<BR>If you are changing existing data :  Set the valid checkbox of the existing data as unchecked and click its Update checkbox.  Then enter new data in a blank line, leave the valid checkbox checked, and check its Update checkbox.  Then click the ``Update Info !'' button.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>General</TD><TD>Tables that can only have UNIQUE values should only have one entry set as ``valid'', if multiple are set as valid, the latest one will be dumped and an error message will be shown.<BR>Data with multiple Text entries or multiple Objects are separated by ``//''.  e.g. Pages would have a .ace output that looks like : ``Page 1 26'', and a form entry that would look like : ``1//26''.<BR>All field could have comments in acedb, which show in the .ace file after the entry,  e.g.  ``Page 1 26 -C \"Email by Bob\"''.This is represented in postgres by entering it after ``-COMMENT'' e.g. ``1//26 -COMMENT Email by Bob''.  This should be stored in postgres in the wpa_comment table instead of this acedb-style comment.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa</TD><TD>Mainly used to see whether the paper is a valid or invalid paper.  To delete a paper from citace, mark this as invalid.  Also shows who first entered this WBPaper and when.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_identifier</TD><TD>The various Identifiers that correspond to this WBPaper.  e.g. cgc, pmid, med, wbg, wcwm, etc.<BR>These values could a valid value of ``misattributed'' which refers to a historic identifier that no longer exists, but needs to be kept in case someone ever referred to a paper by that now-invalid identifier.  Invalid should rarely be used, and then only for identifiers that should never have been created.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_title</TD><TD>The Title of the Paper.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_publisher</TD><TD>The Publisher of the Paper.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_journal</TD><TD>The Journal of the Paper.  Possibly in the future there will be an index of valid Journal names, which will help reduce the number of Journal names that refer to the same Journal due to different abbreviations in the name.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_volume</TD><TD>The Volume of the Paper.  Volume has a .ace tag that is ``Volume UNIQUE Text Text'', so it could have multiple valid Volumes provided that the first Text is unique.  e.g. a .ace entry with : ``Volume 12 5''  and  ``Volume 12 6''.<BR>Like other fields that can have multiple Text, these are separated by ``//'', e.g. a form entry of ``12//5'' or ``12//6''</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_pages</TD><TD>The Pages of the Paper.  Paper has a .ace tag that is ``Page UNIQUE Text UNIQUE Text'', so it can only have one valid entry.  Like other fields that can have multiple Text, these are separated by ``//'', e.g. a form entry of ``12//5'' or ``12//6''</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_date_published</TD><TD>Not in use and not dumped, but Eimear wanted this.  If the acedb Original Timestamp tag ever gets populated it will be based on the wpa postgres table.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_fulltext_url</TD><TD>Not in use and not dumped, but Eimear wanted this.  I have no clue where in the acedb model this would go.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_abstract</TD><TD>The Abstract of the paper.  In postgres, the full text of the abstract is store.  For .ace output, it refers to a ?LongText object, so it outputs the name of the WBPaper, then creates a LongText object with the same name containing the Abstract data.  e.g.<BR>``Paper : \"WBPaper00000003\"<BR>Abstract \"WBPaper00000003\"<BR><BR>LongText : \"WBPaper00000003\"<BR><BR>Applying a series of techniques intended to induce, detect and isolate lethal and/or sterile temperature-sensitive mutants, specific to the se lf-fertilizing hermaphrodite nematode Caenorhabditis elegans, Bergerac strain, 25 such mutants have been found. Optimal conditions for the application of mu tagenic treatment and the detection of such mutations are discussed.<BR><BR>***LongTextEnd***''.<BR>If you're editing the abstract to have extra genes, you may need to add the WBGene - CDS connections below (a script won't do this automatically).</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_affiliation</TD><TD>The Affiliation of the paper, as opposed to the Affilation of each author, which goes in the Author Affiliation section below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_hardcopy</TD><TD>Whether Wormbase-Caltech has a hardcopy of this WBPaper.  If so, enter ``YES''.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_comments</TD><TD>Any comments you'd like to enter about this WBPaper.  These comments do not have a .ace output, so they will not show in WormBase.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_editor</TD><TD>The editors of the WBPaper.  Separated by comma and a space.  e.g. :  ``VA Borh, BFC Clark, T Stevnsner''.  Generally used inside an ``In_book'' tag rather than a WBPaper itself.  (See wpa_in_book)</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_nematode_paper</TD><TD>Not in use and not dumped.  Whether a WBPaper is a nematode paper.  The acedb model says : ``Nematode_paper ?Species // for flagging worm specific papers, ?Species part is optional''.  If you start using this, let Juancarlos know to change the get_paper_ace.pm to dump the data however you'd like it.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_contained_in</TD><TD>The WBPapers that contain this WBPaper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_contains</TD><TD>The WBPapers that are contained in this WBPaper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_keyword</TD><TD>A Keyword for this WBPaper.  Enter each Keyword in its own line.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_erratum</TD><TD>The postgres ID of the Erratum of this WBPaper.<BR>This is complicated, unless you understand it, talk to Ranjana or Juancarlos about this rather than entering it yourself.<BR>Due to the acedb model saying ``Erratum #Paper'' rather than ``Erratum ?Paper'', erratum data can be recursive, but it had no acedb identifier of its own.  In postgres this is solved by making all errata having the same postgres identifier as the main WBPaper followed by ``.1''  This would allow an erratum of an erratum of an erratum to say, e.g.  ``WBPaper00000003.1.1.1''.  To create an erratum, enter the WBPaper identifier from ID, and check on the Update checkbox, and click the ``Update Info !'' button.  Then return to this page and there will be a link to click.  Click this link and it will open a new window to edit that postgres paper.  Any data entered in that postgres paper will appear under the main WBPaper with an ``Erratum'' tag in front.<BR>WBPersons that have verified they are the Authors / Editors in this Erratum will appear connected to the main WBPaper instead of the Erratum tagged WBPaper because Person - Paper connections are dumped via Person, and acedb cannot crossreference to a hash.<BR>Abstracts attached to Erratum will need an acedb LongText object different from the main WBPaper, since that could also have its own Abstract.  For this purpose, the LongText object created has the same name as the Postgres object (e.g. ``LongText : \"WBPaper00004173.1\"'')</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_in_book</TD><TD>The postgres ID of the In_book of this WBPaper.<BR>This is complicated, unless you understand it, talk to Ranjana or Juancarlos about this rather than entering it yourself.<BR>Due to the acedb model saying ``In_book #Paper'' rather than ``In_book ?Paper'', in_book data can be recursive, but it had no acedb identifier of its own.  In postgres this is solved by making all in_book having the same postgres identifier as the main WBPaper followed by ``.2''  This would allow an in_book of an in_book of an in_book to say, e.g.  ``WBPaper00000003.2.2.2''.  To create an in_book, enter the WBPaper identifier from ID, and check on the Update checkbox, and click the ``Update Info !'' button.  Then return to this page and there will be a link to click.  Click this link and it will open a new window to edit that postgres paper.  Any data entered in that postgres paper will appear under the main WBPaper with an ``In_book'' tag in front.<BR>WBPersons that have verified they are the Authors / Editors in this In_book will appear connected to the main WBPaper instead of the In_book tagged WBPaper because Person - Paper connections are dumped via Person, and acedb cannot crossreference to a hash.<BR>Abstracts attached to In_book will need an acedb LongText object different from the main WBPaper, since that could also have its own Abstract.  For this purpose, the LongText object created has the same name as the Postgres object (e.g. ``LongText : \"WBPaper00004173.2\"'')</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_type</TD><TD>The Type of the WBPaper.<BR>There is a controlled vocabulary for this, which is stored in the postgres table wpa_type_index.  Postgres store the corresponding index number on this table instead of the index values themselves (since they could change).  The drop-down menu shows the values for simplicity for the curator, but the display of entered data shows the index number for completeness.  If you'd like a type that is not in the index, talk to Ranjana and Juancarlos.  For an explanation of each type, talk to Ranjana.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>wpa_author</TD><TD>The Authors of the WBPaper<BR>
Understanding all author data may be complex.  Unless you understand the type of
changes you are making, talk to Ranjana or Cecilia or Juancarlos about this rather than
entering it yourself.<BR>
Author data can have multiple things associated with it, this set of data is for
author order only.  To change author name, author affiliation, add another
author, associate with a possible WBPerson, associate with contacting a possible
WBPerson, or associate with the verification of a possible WBPerson, see
below.<BR>
Author data is stored in an author index to simplify changing subtypes of author
data instead of changing it in all tables.  e.g. if you want to change the name
of author_id 11873, you can change ``Smardon AM'' to ``AM Smardon'' in one
place, rather than changing it in all the associations mentioned above.<BR>The
entered authors display the author_id numbers, and for simplicity show the
corresponding author name in parenthesis.  To alter the order of some authors,
you must enter the author_ids you want to change in the empty boxes (only the
author_ids, not the name in parenthesis), then set the correct order (you may
skip sections of numbers, as long as some are greater than others it will not
create empty authors), the check the Update checkbox.  You must also look at the
previously entered data that is being replaced, check off the Valid checkbox to
set it to invalid, and check on the Update checkbox, otherwise there will be
duplicate orders or duplicate authors.  When ready click the ``Update Info !''
button as usual.<BR>
To delete an author, make that author invalid here, and in the author_index
section below.  In the author_index section because that's where the author data
comes from for .ace dumping.  In here because that's where the first author
comes from for Brief_citation.<BR>
Note : the Author order may not start with ``1'' since those numbers may
correspond to an Erratum or an In_book.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Author Editing Section</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>General</TD<TD>Understanding all author data may be complex.  Unless you understand the type of
changes you are making, talk to Ranjana or Cecilia or Juancarlos about this rather than
entering it yourself.<BR>
Author data can have multiple things associated with it, this set of data is for
author order only.  To change author name, author affiliation, add another
author, associate with a possible WBPerson, associate with contacting a possible
WBPerson, or associate with the verification of a possible WBPerson, see
below.<BR>
Author data is stored in an author index to simplify changing subtypes of author
data instead of changing it in all tables.  e.g. if you want to change the name
of author_id 11873, you can change ``Smardon AM'' to ``AM Smardon'' in one
place, rather than changing it in all the associations mentioned
above.</TD></TR>\n"; 
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Display</TD><TD>A display of all the author names and their corresponding affiliation, followed by a diplay of all author names and their corresponding WBPerson connection data.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Adding Link</TD><TD>A link to create a new Author for this WBPaper.  The link opens in a new window.<BR> This new page shows you the Curator name ;  the postgres ID of the WBPaper ;  the highest author order (so you can start above it if creating a new author) ;  and the highest author ID, so you have an idea what the automatically generate author_id will be for your new authors.<BR>Enter the names, orders, affiliations, and check the Valid (unless for some reason you want to create an invalid author, which will not dump for acedb) and Update checkboxes.  When ready, click the ``Create Authors !'' button.  Then if necessary, you can reload the main editing window to keep making changes, and the new authors will be there.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Affiliation Subsection</TD><TD>The current names in the wpa_author_index, as well as the corresponding affiliation.<BR>To change a name or alter an affiliation, make the appropriate changes in a line with a matching author_id number and check on the Update checkbox.  You must also set other lines with the same author_id to have the Valid checkbox checked off to make that line invalid, and check its Update checkbox to update the value.  When ready click on the ``Update Info !'' button as usual.<BR> To delete an author, make that author invalid here, and in the author section above.  In here because that's where the author data comes from for .ace dumping.  In the wpa_author section above because that's where the first author comes from for Brief_citation.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>WBPerson Subsection</TD><TD>The Authors in a WBPaper are attached to possible WBPersons by Cecilia, then they're contacted, then they verify whether they're the author or not.  This data is stored in the tables wpa_author_possible, wpa_author_sent, and wpa_author_verified.  These three tables have data that could have multiple author_id numbers repeated referring to the same author, connecting different people (since some could reply no, and Cecilia would attach them to someone else).  For this purpose, a separate joinkey is required to connect multiple author_id numbers that are the same.  This is the purpose of the wpa_join column.  The data of the possible column is the postgres joinkey of the WBPerson, that being ``two'' followed by the WBPerson number.  The data of the sent column can be NULL, ``SENT'', or ``NO EMAIL'', but any value could be placed there, although dumping scripts won't deal with other values.  The data of the verified column is either ``YES'' or ``NO'' followed by the standardname of the WBPerson from the two_standardname table.  The verified table is different in that it allows the curator column to be someone other than the current curator, since the verification could be from someone's email or some other source.<BR>To change data, insert the wpa_join value for all three tables, insert the correct values in all three tables, then click on the Valid checkbox and click on the Update checkbox.  Then if any values are no longer valid, click off the Valid checkbox for those values in all three tables, then click on the Update checkbox.  When ready click on on the ``Update Info !'' button as usual.  possible / sent / verified always show History.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Gene - CDS Editing Section</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>General</TD><TD>Papers are connected to WBGenes and CDS.  CDS that were attached to WBPapers have automatically had a WBGene attached to them, so that all CDS are attached to a WBGene.  If a curator would like to attach a CDS to a paper, that curator is responsible for finding out with WBGene it corresponds to and attaching it.  WBGenes may be attached without a CDS, but CDS require a WBGene to be attached.</TD></TR>\n";
#   print "<TR bgcolor='$blue'><TD>Existing Lines</TD><TD>Data that already exists in postgres.  WBGene and CDS are in postgres, data in parenthesis is the 3-letter gene corresponding to the WBGene in the loci_all.txt file.<BR>To get rid of this data, set the valid checkbox as unchecked, click its Update checkbox, and click the ``Update Info !'' button.  WBGenes are grouped together by WBGene in ascending WBGene number order ;  within each group they are sorted by timestamp in descending order, so that the top-most value is the current one.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Existing Lines</TD><TD>Data that already exists in postgres.  WBGene and CDS are in postgres, data in parenthesis is the 3-letter gene corresponding to the WBGene in the gin_locus postgres table based on the nameserver file.<BR>To get rid of this data, set the valid checkbox as unchecked, click its Update checkbox, and click the ``Update Info !'' button.  WBGenes are grouped together by WBGene in ascending WBGene number order ;  within each group they are sorted by timestamp in descending order, so that the top-most value is the current one.</TD></TR>\n";
#   print "<TR bgcolor='$blue'><TD>Blank Lines</TD><TD>Blank to allow new data in postgres.<BR>If you are creating new data, enter it here, check its Update checkbox, and click the ``Update Info !'' button.<BR>If you are changing existing data :  Set the valid checkbox of the existing data as unchecked and click its Update checkbox.  Then enter new data in a blank line, leave the valid checkbox checked, and check its Update checkbox.  Then click the ``Update Info !'' button.<BR>The Gene - CDS data box allows multiple WBGene - CDS entries in the same box.  Enter each WBGene / WBGene - CDS in its own line, and separate the WBGene from the CDS with a space, e.g. ``WBGene00001609 F02A9.6''.  The evidence box allows multiple evidences to be attached to all the WBGene / WBGene - CDS connections.  Enter each evidence it its own line.  Person evidence can be entered either in ``WBPerson \"WBPerson####\"'' format, or simply ``WBPerson####'' format.  Other evidence types need to be entered in the .ace format of ``Author_evidence \"Whoever\"'' or whichever #Evidence tag.<BR>Multiple sets of Gene - CDS boxes and Evidence boxes exist to allow multiple sets of evidence to be attached to different Gene - CDS groups.<BR>WBGenes and CDS are checked against <A HREF=\"http://tazendra.caltech.edu/~azurebrd/sanger/genes2molecular_names.txt\">http://tazendra.caltech.edu/~azurebrd/sanger/genes2molecular_names.txt</A> and <A HREF=\"http://tazendra.caltech.edu/~azurebrd/sanger/loci_all.txt\">http://tazendra.caltech.edu/~azurebrd/sanger/loci_all.txt</A> to make sure they are valid.  3-letter names may be entered and will be converted to WBGenes.<BR>Each WBGene - Evidence / WBGene - CDS - Evidence is separately stored in its own row in postgres, so that when reloading the page after changing data, it will show individually under Existing Lines.<BR>Curator_confirmed for the current curator is automatically attached to any data entered.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Blank Lines</TD><TD>Blank to allow new data in postgres.<BR>If you are creating new data, enter it here, check its Update checkbox, and click the ``Update Info !'' button.<BR>If you are changing existing data :  Set the valid checkbox of the existing data as unchecked and click its Update checkbox.  Then enter new data in a blank line, leave the valid checkbox checked, and check its Update checkbox.  Then click the ``Update Info !'' button.<BR>The Gene - CDS data box allows multiple WBGene - CDS entries in the same box.  Enter each WBGene / WBGene - CDS in its own line, and separate the WBGene from the CDS with a space, e.g. ``WBGene00001609 F02A9.6''.  The evidence box allows multiple evidences to be attached to all the WBGene / WBGene - CDS connections.  Enter each evidence it its own line.  Person evidence can be entered either in ``WBPerson \"WBPerson####\"'' format, or simply ``WBPerson####'' format.  Other evidence types need to be entered in the .ace format of ``Author_evidence \"Whoever\"'' or whichever #Evidence tag.<BR>Multiple sets of Gene - CDS boxes and Evidence boxes exist to allow multiple sets of evidence to be attached to different Gene - CDS groups.<BR>WBGenes and CDS are checked against gin_locus, gin_synonym, and gin_sequence (getting the CDS not the sequence) to make sure they are valid (this data is based on the nameserver for loci, and the aceserver for sequence and synonyms).  3-letter names may be entered and will be converted to WBGenes.<BR>Each WBGene - Evidence / WBGene - CDS - Evidence is separately stored in its own row in postgres, so that when reloading the page after changing data, it will show individually under Existing Lines.<BR>Curator_confirmed for the current curator is automatically attached to any data entered.</TD></TR>\n";
# not needed anymore since it should auto convert the CDS to a WBGene  2009 09 03
#   print "<TR bgcolor='$blue'><TD>CDS Query Link</TD><TD>A link for batch query of CDS to copy-paste into boxes above.  The link opens in a new window.<BR> This new page shows you the Curator name ;  the postgres ID of the WBPaper ;  an html textarea box to input CDS, one CDS per line in box ;  a ``CDS Query !'' button to query once all CDS are in the box.<BR>After clicking the button a result page shows a table of WBGene tab CDS connections that can be copy-pasted into the main editing page's WBGene - CDS connection boxes.  Don't copy-paste any red-coloured error warnings that a CDS was not found.  Also at bottom once again only the WBGene results for ease of copy-pasting</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Electronic Path Editing Section</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>General</TD><TD>The path to the PDF as well as the type of PDF.<BR>This data is generated via script looking at all values in /home/acedb/daniel/Reference/cgc and /home/acedb/daniel/Reference/pubmed.  This section should be unnecessary, but should a PDF end up somewhere else, or with an unexpected format, it can be added here for display.<BR>Like the type and authors, there is an index of the types a PDF can be.  This is stored in wpa_electronic_type_index.  LIBRARY_PDF and TIF_PDF are not text-convertible.  WEB_PDF, HTML_PDF, OCR_PDF, AUTHOR_CONTRIBUTED_PDF, and TEMP_PDF are text-convertible.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Existing Lines</TD><TD>Data that already exists in postgres.<BR>To get rid of this data, set the valid checkbox as unchecked, click its Update checkbox, and click the ``Update Info !'' button.  <BR>These hyperlink to the location of the PDF as a URL so it may be clicked, but show the linux path to the PDF so it may be edited.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Blank Lines</TD><TD>Blank to allow new data in postgres.<BR>If you are creating new data, enter it here, check its Update checkbox, and click the ``Update Info !'' button.<BR>If you are changing existing data :  Set the valid checkbox of the existing data as unchecked and click its Update checkbox.  Then enter new data in a blank line, leave the valid checkbox checked, and check its Update checkbox.  Then click the ``Update Info !'' button.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Updating Script</TD><TD>After manually adding PDFs without using this form, the script at /home/acedb/daniel/linker.pl connects new papers to postgres, makes deleted papers invalid, and emails Daniel.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Update Info Page</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Curator</TD><TD>The curator name</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Change Table</TD><TD>Corresponding to which rows you've chose to update by checking on the Update box, the corresponding values are shown for verification.  If you see a value that should not be there, or a value is missing, go back, refresh, and make the appropriate changes.<BR>If something entered in not valid for .ace output, it will show with a different color background (default magenta) with a warning, and will not be added to postgres.  If a UNIQUE .ace tag has multiple values, it will say so in the .ace preview below.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Postgres Lines</TD><TD>If you are familiar with psql, you can see what commands have been passed to posgres.  If you don't see these, then for some reason the changes have not gone into postgres, and you should contact Juancarlos.  (Refresh the Main Editing page to see if the changes did happen)</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>.ace Preview</TD><TD>What the .ace file will look like for this entry.<BR>Any UNIQUE tags with multiple values will give a warning stating which value was used, but if you know which is correct, editing the wrong value to be invalid would be good.<BR>The .ace file sent for the citace upload does not dump the .ace file previewed.  It instead compares it to previous .ace dump for that object, and writes a .ace file with a paper entry with -D for the tags and values that are no longer there, then write another paper entry inserting the proper values.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Links</TD><TD>To front page, and to curation form to check out this paper for curation.</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Enter New Papers Page</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Curator</TD><TD>The curator name</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Confirm Abstracts box</TD><TD>A cronjob picks up new pubmed xml files that match elegans in the abstract and downloads them every day at 6am.  Display them for Kimberly to approve or reject each of them.  If approved / rejected, move XML to done directory.  If rejected add pmid to rejected_pmids file to avoid re-downloading.  If approved check that PMID doesn't already exist as a WBPaper (updated if so) and create new WBPaper.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>PMID box</TD><TD>Enter PMID numbers, one on each line, then click the ``Enter PMIDs !'' button.  This will take a while to process because it will finish processing all PMIDs before showing the results.  Do not enter more than 100 PMIDs at a time unless it's after 18:00 pacific time (for ncbi robot rules).  There is a 5 second pause between fetching each pmid (for ncbi robot rules).  Result page will display the pmid numbers processed.  For each pmid number it will also show whether it matched and MERGEd a paper ;  matched too many papers and FLAGged to be looked at manually ;  matches some possible paper(s) and FLAGged to be looked at ;  had LOW matching to papers and created them.  Links to Display of that other paper.  This emails Ranjana and Daniel.  There is a ``Not for first-pass curation'' checkbox flag, which is for functional annotations, entering data into cfp_curator, cfp_comment, and wpa_checked_out.</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>Possible Matches</TD><TD>Possible matches are stored in a flatfile in /home/postgres/work/pgpopulation/wpa_papers/wpa_new_wbpaper_tables/perl_wpa_match/manual_check_file.endnote .  This file is opened and all entries are displayed with links to their possible matches (to open in the wbpaper_editor.cgi in a separate window) and ``Merge with this Paper !'' buttons next to each possible match, and a ``Create New Paper !'' button in case it is none of those matched papers.  When ready click the appropriate button and it will process the changes, then reload this page ;  since a entry will have been created or merged, it will no longer show in this display. </TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>PMID abstracts text Page</B></TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>PMID and Abstracts</TD><TD>Tab delimited version of pubmed XML downloaded data, shows pmid and abstract only.  For Textpresso svm markup.  No link, shows only if action=abstract_text</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR bgcolor='$blue'><TD> </TD><TD> </TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "</TABLE>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD><B>Acedb Models</B></TD><TD colspan=6>last updated 2005 07 27</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>?Paper</TD><TD>Original_timestamp</TD><TD>Datetype</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// temporary tag in transition period [krb 040223]</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Name</TD><TD>CGC_name</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>CGC_name_for</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>PMID</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>PMID_for</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Medline_name</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>Medline_name_for</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Meeting_abstract</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>Meeting_abstract_name</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>WBG_abstract</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>WBG_abstract_name</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Old_WBPaper</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>Old_WBPaper_name</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Other_name</TD><TD>?Paper_name</TD><TD>XREF</TD><TD>Other_name_for</TD><TD>&nbsp;</TD><TD>// e.g. agriola etc ...</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Nematode_paper</TD><TD>?Species</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// for flagging worm specific papers, ?Species part is optional</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Erratum</TD><TD>#Paper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Reference</TD><TD>Title</TD><TD>UNIQUE</TD><TD>?Text</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Journal</TD><TD>UNIQUE</TD><TD>?Journal</TD><TD>XREF</TD><TD>Paper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Publisher</TD><TD>UNIQUE</TD><TD>Text</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Editor</TD><TD>?Text</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>//used for books put in as whole objects</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Page</TD><TD>UNIQUE</TD><TD>Text</TD><TD>UNIQUE</TD><TD>Text</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Volume</TD><TD>UNIQUE</TD><TD>Text</TD><TD>Text</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Year</TD><TD>UNIQUE</TD><TD>Int</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>In_book</TD><TD>#Paper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Contained_in</TD><TD>?Paper</TD><TD>XREF</TD><TD>Contains</TD><TD>&nbsp;</TD><TD>// old form</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Author</TD><TD>?Author</TD><TD>XREF</TD><TD>Paper</TD><TD>#Affiliation</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Person</TD><TD>?Person</TD><TD>XREF</TD><TD>Paper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Affiliation</TD><TD>Text</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Authors' affiliation if available</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Brief_citation</TD><TD>UNIQUE</TD><TD>Text</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Abstract</TD><TD>?LongText</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Type</TD><TD>UNIQUE</TD><TD>Text</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>//meaning review, article, chapter, monograph, news, book, meeting_abstract</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Contains</TD><TD>?Paper</TD><TD>XREF</TD><TD>Contained_in</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Refers_to</TD><TD>Gene</TD><TD>?Gene</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Locus</TD><TD>?Locus</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Allele</TD><TD>?Variation</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Rearrangement</TD><TD>?Rearrangement</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Sequence</TD><TD>?Sequence</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>CDS</TD><TD>?CDS</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Transcript</TD><TD>?Transcript</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Pseudogene</TD><TD>?Pseudogene</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD><TD>// new [030801 krb]</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Strain</TD><TD>?Strain</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Clone</TD><TD>?Clone</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Protein</TD><TD>?Protein</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Expr_pattern</TD><TD>?Expr_pattern</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Expr_profile</TD><TD>?Expr_profile</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Cell</TD><TD>?Cell</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Cell_group</TD><TD>?Cell_group</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Life_stage</TD><TD>?Life_stage</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>RNAi</TD><TD>?RNAi</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Transgene</TD><TD>?Transgene</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>GO_term</TD><TD>?GO_term</TD><TD>XREF</TD><TD>Reference</TD><TD>?GO_code</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Operon</TD><TD>?Operon</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Cluster</TD><TD>?Cluster</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Feature</TD><TD>?Feature</TD><TD>XREF</TD><TD>Defined_by_paper</TD><TD>&nbsp;</TD><TD>// added [030424 dl]</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Gene_regulation</TD><TD>?Gene_regulation</TD><TD>XREF</TD><TD>Reference</TD><TD>&nbsp;</TD><TD>// added [030804 krb]</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Microarray_experiment</TD><TD>?Microarray_experiment</TD><TD>XREF</TD><TD>Reference</TD><TD>&nbsp;</TD><TD>// added for Microarray_experiment model</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Anatomy_term</TD><TD>?Anatomy_term</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Antibody</TD><TD>?Antibody</TD><TD>XREF</TD><TD>Reference</TD><TD>#Evidence</TD><TD>// added [031120 krb]</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>SAGE_experiment</TD><TD>?SAGE_experiment</TD><TD>XREF</TD><TD>Reference</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Y2H</TD><TD>?Y2H</TD><TD>XREF</TD><TD>Reference</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>Interaction</TD><TD>?Interaction</TD><TD>XREF</TD><TD>Paper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Keyword</TD><TD>?Keyword</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>#Evidence</TD><TD>Paper_evidence</TD><TD>?Paper</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Data from a Paper</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Published_as</TD><TD>Gene</TD><TD>UNIQUE</TD><TD>?Gene_name</TD><TD>#Evidence</TD><TD>&nbsp;</TD><TD>// .. track other names for the same data</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Person_evidence</TD><TD>?Person</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Data from a Person</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Author_evidence</TD><TD>?Author</TD><TD>UNIQUE</TD><TD>Text</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Data from an Author</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Accession_evidence</TD><TD>?Database</TD><TD>?Accession_number</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Data from a database (NDB/UNIPROT etc [sic])</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Protein_id__evidence</TD><TD>?Text</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Rereference a protein_ID</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>GO_term_evidence</TD><TD>?GO_term</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Rerefence a GO_term</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Expr_pattern_evidence</TD><TD>?Expr_pattern</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Rerefence a Expression pattern</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Microarray_results_evidence</TD><TD>?Microarray_results</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Rerefence a Microarray_result</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>RNAi_evidence</TD><TD>?RNAi</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Rerefence a RNAi knockdown</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Gene_regulation_evidence</TD><TD>?Gene_regulation</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// Rerefence a Gene_regulation interaction</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>CGC_data_submission</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// bless the data as comning [sic] from CGC</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Curator_confirmed</TD><TD>?Person</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// bless the data manually</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD>&nbsp;</TD><TD>Inferred_automatically</TD><TD>Text</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD><TD>// bless the data via a script</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "</TABLE>\n";
} # sub documentation

sub getLocusFromWBGene {
  my $wbgene = shift; my ($joinkey) = $wbgene =~ m/(\d+)/;
  my $result = $dbh->prepare( "SELECT gin_locus FROM gin_locus WHERE joinkey = '$joinkey';" ); $result->execute;
  my @row = $result->fetchrow(); return $row[0];
}

sub displayGenePostgresRow {
  my ($pg_table, $row_count, $row) = @_;
  my @row = split/TABDIVIDER/, $row;
    my $bgcolor = $blue;
    if ($row[1]) {
      if ($row[3] eq 'invalid') { $bgcolor = $red; }
      $row_count++;
      print "<TR bgcolor='$bgcolor'>\n"; 
      print "<TD>$row[1]";
      my ($wbg) = $row[1] =~ m/(WBGene\d+)/;
      unless ($row[1] =~ m/\(/) { my $locus = &getLocusFromWBGene($wbg); print " ($locus)"; }
#       if ($cdsToGene{back}{$wbg}) { print " ($cdsToGene{back}{$wbg})"; }
      print "</TD>\n";
      if ($row[1]) { print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_${row_count}_value\" VALUE=\"$row[1]\">\n"; }
      if ($row[2]) { 
          if ($row[2] =~ m/\"/) { $row[2] =~ s/\"/&quot;/g; }
          print "  <TD>$row[2]</TD>\n";
          print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_${row_count}_order\" VALUE=\"$row[2]\">\n"; }
        else { print "  <TD>&nbsp;</TD>\n"; }
      if ($row[3]) {				# valid
          my $checked = '';  if ($row[3] eq 'valid') { $checked = 'CHECKED'; }
          print "<TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" $checked></TD>\n"; }
        else { print "<TD></TD>\n"; }
      print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 
      print "  <TD>$row[4]</TD>\n";
      if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; } if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
      print "  <TD>$row[5]</TD>\n";
      print "</TR>\n";
    }
  return $row_count;
} # sub displayGenePostgresRow

sub displayGene {
  my ($joinkey, $history_or_valid) = @_;
  my $row_count = 0;
  my $pg_table = 'wpa_gene';
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Gene - CDS</TD><TD>Evidence</TD><TD>Valid</TD><TD>Update</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  if ($history_or_valid eq 'history') {		# to show history simply query in order (timestamp descending) and print
#       my $result = $conn->exec( "SELECT * FROM wpa_gene WHERE joinkey = '$joinkey' ORDER BY wpa_gene, wpa_timestamp DESC;" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE joinkey = '$joinkey' ORDER BY wpa_gene, wpa_timestamp DESC;" );
      $result->execute;
      while (my @row = $result->fetchrow) {
        for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
        my $row = join"TABDIVIDER", @row;						# group together the data to pass (wpa_gene data has tabs so use TABDIVIDER 2006 01 23
        ($row_count) = &displayGenePostgresRow($pg_table, $row_count, $row); } }	# display each data, updating the row_count
    else {						# to show valid data only, get in ascending timestamp order, store in a hash valid data and delete from the hash invalid data then show hash data
      my %rows_to_display;				# hash to store valid data only
#       my $result = $conn->exec( "SELECT * FROM wpa_gene WHERE joinkey = '$joinkey' ORDER BY wpa_gene, wpa_timestamp ;" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE joinkey = '$joinkey' ORDER BY wpa_gene, wpa_timestamp ;" );
      $result->execute;
      while (my @row = $result->fetchrow) {
        for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
        my $row = join"TABDIVIDER", @row;							# group together the data to pass
        if ($row[3] eq 'valid') { $rows_to_display{"$row[1]$row[2]"} = $row; }						# store by order and data the valid data.  need to key off gene and evidence
          else { 
            if ($rows_to_display{$row[1]}) { delete $rows_to_display{"$row[1]$row[2]"}; } 
            if ($rows_to_display{"$row[1]$row[2]"}) { delete $rows_to_display{"$row[1]$row[2]"}; } } }			# delete invalid data if it's been set to valid before
      foreach my $wpa_gene (sort keys %rows_to_display) {								# looking at each data value
        ($row_count) = &displayGenePostgresRow($pg_table, $row_count, $rows_to_display{$wpa_gene}); } }			# display each data, updating the row_count
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_normal_count\" VALUE=\"$row_count\">\n";
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_extra_count\" VALUE=\"$tables{copies}{$pg_table}\">\n";
  for (1 .. $tables{copies}{$pg_table}) {
    $row_count++;
    print "<TR bgcolor='white'>\n";
#     print "  <TD>wpa_gene</TD>\n";
    print "  <TD ALIGN='LEFT'><TEXTAREA NAME=\"${pg_table}_${row_count}_value\" ROWS=8 COLS=60 VALUE=\"\"></TEXTAREA></TD>\n";
    print "  <TD ALIGN='LEFT'><TEXTAREA NAME=\"${pg_table}_${row_count}_order\" ROWS=8 COLS=40 VALUE=\"\"></TEXTAREA></TD>\n";
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" CHECKED></TD>\n"; 
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 
    print "  <TD>$curators{std}{$theHash{curator}}</TD>\n";
    print "  <TD>CURRENT</TD>\n";
    print "</TR>\n";
  }
} # sub displayGene

sub displayFullAuthorPostgresRow {				# show index and affiliation data summary (not for editing)
  my ($row2, $bgcolor) = @_;
  my @row2 = split/\t/, $row2;
  print "<TR bgcolor='$bgcolor'>\n";
  print "<TD>$row2[1]</TD>";
  if ($row2[2]) { print "<TD>$row2[2]</TD>"; }
    else { print "<TD>&nbsp;</TD>"; }
  print "<TR>\n"; 
} # sub displayFullAuthorPostgresRow

sub displayAuthorTypePostgresRow {				# show existing values in postgres for the @author_types
  my ($author_type, $row_count, $row) = @_;
  my @row = split/\t/, $row;
  my $bgcolor = $blue;
  $row_count++;
  if ($row[3] eq 'invalid') { $bgcolor = $red; }
  print "<TR bgcolor='$bgcolor'>\n";
  print "  <TD>$row[0]";
  if ($author_type ne 'index') { if ($auth_name{$row[0]}) { print " ($auth_name{$row[0]})"; } }		# show author name for cecilia
  print "</TD>\n";
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_${row_count}_id\" VALUE=\"$row[0]\">\n";
  unless ($row[1]) { $row[1] = '&nbsp;'; }
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_${row_count}_value\" VALUE=\"$row[1]\">\n";
  print "  <TD>$row[1]</TD>\n"; 
  if ($row[2]) { print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_${row_count}_second\" VALUE=\"$row[2]\">\n"; }
    else { print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_${row_count}_second\" VALUE=\"\">\n"; }
  unless ($row[2]) { $row[2] = '&nbsp;'; }
  print "  <TD ALIGN='CENTER'>$row[2]</TD>\n";

  if ($row[3]) {				# valid
      my $checked = '';  if ($row[3] eq 'valid') { $checked = 'CHECKED'; }
      print "<TD ALIGN='CENTER'><INPUT NAME=\"${author_type}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" $checked></TD>\n"; }
    else { print "<TD></TD>\n"; }

  print "  <TD ALIGN='CENTER'><INPUT NAME=\"${author_type}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 

  print "  <TD>$row[4]</TD>\n";
  if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; } if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
  print "  <TD>$row[5]</TD>\n";

  print "</TR>\n";
  return $row_count;
} # sub displayAuthorTypePostgresRow

sub displayFullAuthor {
  my ($joinkey, $history_or_valid) = @_;
  my %auth_id; my %temp_auth_id;
  %auth_name = ();		# clear auth_name, global because used by &displayAuthorTypePostgresRow();
#   my $result = $conn->exec( "SELECT * FROM wpa_author WHERE joinkey = '$joinkey' ORDER BY wpa_order, wpa_timestamp;" );
  my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE joinkey = '$joinkey' ORDER BY wpa_order, wpa_timestamp;" );
  $result->execute;
  while (my @row = $result->fetchrow) { 				# filter out invalids by throwing into a %temp_auth_id hash, ordered by timestamp deleting invalids
    if ($row[3] eq 'valid') { $temp_auth_id{$row[2]}{$row[1]}++; }	# there's never a point in showing data where the wpa_author is not valid
      else { if ($temp_auth_id{$row[2]}{$row[1]}) { delete $temp_auth_id{$row[2]}{$row[1]}; } } }
  foreach my $order (sort keys %temp_auth_id) { foreach my $auth_id (sort keys %{ $temp_auth_id{$order} }) { $auth_id{$auth_id}++; } }
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD ALIGN=CENTER>Affiliation</TD></TR>\n";
  foreach my $auth_id (sort keys %auth_id) {		# looping through all author_ids
    if ($history_or_valid eq 'history') {		# to show history simply query in order (timestamp descending) and print
#         my $result2 = $conn->exec( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
        my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
        $result2->execute;
        while (my @row2 = $result2->fetchrow) {		# sort in descending timestamp order to diplay all
          for (@row2) { unless ($_) { $_ = ''; } }	# initialize blank row values
          my $row2 = join"\t", @row2;
          my $bgcolor = $blue; if ($row2[3] ne 'valid') { $bgcolor = $red; }
          &displayFullAuthorPostgresRow($row2, $bgcolor); } }
      else {						# to show valid data only, get in ascending timestamp order, store in a hash valid data and delete from the hash invalid data then show hash data
        my %rows_to_display;				# hash to store valid data only
#         my $result2 = $conn->exec( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
        my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
        $result2->execute;
        while (my @row2 = $result2->fetchrow) {
          for (@row2) { unless ($_) { $_ = ''; } }	# initialize blank row values
          my $row2 = join"\t", @row2;
          if ($row2[3] eq 'valid') { $rows_to_display{$row2[0]} = $row2; }							# store by order and data the valid data
            else { if ($rows_to_display{$row2[0]}) { delete $rows_to_display{$row2[0]}; } } }					# delete invalid data if it's been set to valid before
        foreach my $author_id (keys %rows_to_display) { &displayFullAuthorPostgresRow($rows_to_display{$author_id}, $blue); } }	# display each data, since valid always blue
#     my $result2 = $conn->exec( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );	# sort in ascending timestamp order to maintain most recent
    my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );	# sort in ascending timestamp order to maintain most recent
    $result2->execute;
    while (my @row2 = $result2->fetchrow) { if ($row2[3] eq 'valid') { $auth_name{$auth_id} = $row2[1]; } }
  } # foreach my $auth_id (@auth_id)
  print "</TABLE><BR><BR>\n";
  unless ($ignore_extras{$theHash{curator}}) {		# ignore Cecilia's for Ranjana
    print "<TABLE border=0 cellspacing=2>\n";
    print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD>Possible</TD><TD>Sent</TD><TD>Verified</TD></TR>\n";
    foreach my $auth_id (sort keys %auth_id) {		# looping through all author_ids
      my %ceci_hash;
#       my $result2 = $conn->exec( "SELECT * FROM wpa_author_possible WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
      my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_possible WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
      $result2->execute;
      while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{possible} = $row[1]; }
#       $result2 = $conn->exec( "SELECT * FROM wpa_author_sent WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
      $result2 = $dbh->prepare( "SELECT * FROM wpa_author_sent WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
      $result2->execute;
      while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{sent} = $row[1]; }
#       $result2 = $conn->exec( "SELECT * FROM wpa_author_verified WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
      $result2 = $dbh->prepare( "SELECT * FROM wpa_author_verified WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
      $result2->execute;
      while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{verified} = $row[1]; $ceci_hash{$row[2]}{valid} = $row[3]; }
      foreach my $join (sort keys %ceci_hash) {
        my $bgcolor = $blue; if ($ceci_hash{$join}{valid} eq 'invalid') { $bgcolor = $red; }
        my $possible = '&nbsp;'; my $sent = '&nbsp;'; my $verified = '&nbsp;';
        if ($ceci_hash{$join}{possible}) { $possible = $ceci_hash{$join}{possible}; }
        if ($ceci_hash{$join}{sent}) { $sent = $ceci_hash{$join}{sent}; }
        if ($ceci_hash{$join}{verified}) { $verified = $ceci_hash{$join}{verified}; }
        print "<TR bgcolor='$bgcolor'>";
        print "<TD>$auth_name{$auth_id}</TD><TD>$possible</TD><TD>$sent</TD><TD>$verified</TD>";
        print "<TR>\n";
      }
    } # foreach my $auth_id (@auth_id)
    print "</TABLE><BR><BR>\n";
  } # unless ($ignore_extras{$theHash{curator}})
  print "<TABLE border=0 cellspacing=2>\n";
#   foreach my $auth_id (sort keys %auth_id) {
#     print "<TR bgcolor='$blue'>\n";
#     print "<TD>$auth_id</TD>\n";
#     my $result2 = $conn->exec( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
#     my @row2 = $result2->fetchrow;
#     print "<TD>$row2[1]</TD><TD>$row2[2]</TD>";
#     $result2 = $conn->exec( "SELECT * FROM wpa_author_possible WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
#     @row2 = $result2->fetchrow;
#     print "<TD>$row2[1]</TD>";
#     $result2 = $conn->exec( "SELECT * FROM wpa_author_sent WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
#     @row2 = $result2->fetchrow;
#     print "<TD>$row2[1]</TD>";
#     $result2 = $conn->exec( "SELECT * FROM wpa_author_verified WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
#     @row2 = $result2->fetchrow;
#     print "<TD>$row2[1]</TD>";
#     print "<TR>\n";
#   } # foreach my $auth_id (sort keys %auth_id)
  foreach my $author_type (@author_types) {
    if ( ($ignore_extras{$theHash{curator}}) && ($author_type ne 'index') ) { next; }
    my $type = 'wpa_author_' . $author_type;
    my $affi = 'wpa_join';  if ($author_type eq 'index') { $affi = 'Affiliation'; }
    print "<TR><TD>&nbsp;</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>Author ID</TD><TD ALIGN=CENTER>$author_type</TD><TD ALIGN=CENTER>$affi</TD><TD>Valid</TD><TD>Update</TD><TD>Curator</TD><TD>Timestamp</TD>\n"; 
    my $row_count = 0;
    foreach my $auth_id (sort keys %auth_id) {		# looping through all author_ids
      if ( ($author_type ne 'index') || ($history_or_valid eq 'history') ) {		# to show history simply query in order (timestamp descending) and print
											# always show history for possible/sent/verified  2005 11 11
#           my $result2 = $conn->exec( "SELECT * FROM $type WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
          my $result2 = $dbh->prepare( "SELECT * FROM $type WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
          $result2->execute;
          while (my @row = $result2->fetchrow) {
            for (@row) { unless ($_) { $_ = ''; } }			# initialize blank row values
            my $row = join"\t", @row;
            ($row_count) = &displayAuthorTypePostgresRow($author_type, $row_count, $row); } }
        else {
          my %rows_to_display;				# hash to store valid data only
#           my $result2 = $conn->exec( "SELECT * FROM $type WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
          my $result2 = $dbh->prepare( "SELECT * FROM $type WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
          $result2->execute;
          while (my @row = $result2->fetchrow) {
            for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
            my $row = join"\t", @row;
            if ($row[3] eq 'valid') { $rows_to_display{$row[0]} = $row; }							# store by order and data the valid data
              else { if ($rows_to_display{$row[0]}) { delete $rows_to_display{$row[0]}; } } }					# delete invalid data if it's been set to valid before
          foreach my $author_id (keys %rows_to_display) {									# looking at each data value
            ($row_count) = &displayAuthorTypePostgresRow($author_type, $row_count, $rows_to_display{$author_id}); } }		# display each data, updating the row count
      for (1 .. $tables{copies}{$author_type}) {
        $row_count++;
        print "<TR bgcolor='white'>\n";
        print "  <TD>$auth_id</TD>\n";
        print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_${row_count}_id\" VALUE=\"$auth_id\">\n";
        print "  <TD ALIGN='LEFT'><INPUT NAME=\"${author_type}_${row_count}_value\" SIZE=20 VALUE=\"\"></TD>\n";
        if ($author_type eq 'index') { 
            print "  <TD ALIGN='LEFT'><INPUT NAME=\"${author_type}_${row_count}_second\" SIZE=40 VALUE=\"\"></TD>\n"; }
          else { 
            print "  <TD ALIGN='LEFT'><INPUT NAME=\"${author_type}_${row_count}_second\" SIZE=4 VALUE=\"\"></TD>\n"; }
        print "  <TD ALIGN='CENTER'><INPUT NAME=\"${author_type}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" CHECKED></TD>\n"; 

        print "  <TD ALIGN='CENTER'><INPUT NAME=\"${author_type}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 

        if ($author_type eq 'verified') { 
            print "  <TD ALIGN='LEFT'><INPUT NAME=\"${author_type}_${row_count}_curator\" SIZE=10 VALUE=\"$curators{std}{$theHash{curator}}\"></TD>\n"; }
          else { print "  <TD>$curators{std}{$theHash{curator}}</TD>\n"; }
        print "  <TD>CURRENT</TD>\n"; 

        print "</TR>\n";
      } # for (1 .. $tables{copies}{$author_type})
    } # foreach my $auth_id (sort keys %auth_id)
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_normal_count\" VALUE=\"$row_count\">\n";
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${author_type}_extra_count\" VALUE=\"$tables{copies}{$author_type}\">\n";
    if ($author_type eq 'index') { print "</TABLE><BR><BR>\n"; print "<TABLE border=0 cellspacing=2>\n"; }
  } # foreach my $author_type (@author_types)
} # sub displayFullAuthor

sub updateInfo {
#   &readCurrentLocus();		# this took 6-7 seconds, using ajax call instead  2009 09 03
  &populateCurators();
  my ($oop, $joinkey) = &getHtmlVar($query, 'number');
  my $pg_commands = '';
  print "<TABLE border=0 cellspacing=2>\n";
  ($joinkey) = &padZeros($joinkey);
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD COLSPAN=5>ID : $joinkey</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Data</TD><TD>Order</TD><TD>Valid</TD><TD>Row Count</TD><TD>Normal</TD><TD>Update</TD></TR>\n";
  foreach my $pg_table (@generic_tables, 'wpa_electronic_path_type', 'wpa_gene') {
    my ($oop, $normal_count) = &getHtmlVar($query, "${pg_table}_normal_count");
    ($oop, my $extra_count) = &getHtmlVar($query, "${pg_table}_extra_count");
    my $full_count = 0; if ($normal_count) { $full_count += $normal_count; } if ($extra_count) { $full_count += $extra_count; }
    for my $row_count (1 .. $full_count ) {
      ($oop, my $update) = &getHtmlVar($query, "${pg_table}_${row_count}_update");
      if ($update) {
        unless ($normal_count) { $normal_count = 0; }
        my $normal = 'normal'; if ($row_count > $normal_count) { $normal = 'extra'; }
        ($oop, my $value) = &getHtmlVar($query, "${pg_table}_${row_count}_value");
        ($oop, my $valid) = &getHtmlVar($query, "${pg_table}_${row_count}_valid");
        my $order = '';
        if ( ($pg_table eq 'wpa_author') || ($pg_table eq 'wpa_electronic_path_type') || ($pg_table eq 'wpa_gene') ) { ($oop, $order) = &getHtmlVar($query, "${pg_table}_${row_count}_order"); }
          # this is really an order for wpa_author ;  a type for wpa_electronic_path_type ;  and an evidence for wpa_gene
        unless ($valid) { $valid = 'invalid'; }
        if ($pg_table eq 'wpa_abstract') {		# abstracts could have newlines in them
          if ($value =~ m/\n/) { $value =~ s/\n/ /g; if ($value =~ m/\s+/) { $value =~ s/\s+/ /g; } } }
        if ($pg_table eq 'wpa_gene') {
#           my (@values) = split/\n/, $value;
          my @values; my %evidences;
          my (@evidences) = split/\n/, $order; 					# get the evidences, put in a hash, add the current curator as curator evidence to hash so it doesn't appear twice from adding and once from having already been there
          foreach (@evidences) { $evidences{$_}++; }
          my ($twonum) = $curators{std}{$theHash{curator}} =~ m/(\d+)/; my $curevi = "Curator_confirmed \"WBPerson$twonum\""; $evidences{$curevi}++;
          if ( ($value =~ m/^WBGene\d+ *\(.*?\)$/) || ($value =~ m/^WBGene\d+$/) ) { push @values, $value; } 	# values to update are already in this format
           else {								# textarea values get wbgenes from ajax call (borrowed from curator_first_pass genestudied table
             my $ajax = get "http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi?all=$value&type=genestudied";
             (@values) = split/, /, $ajax; 
             foreach my $_ (@values) {						# format each of those into this format
               my ($name, $wbg) = $_ =~ m/^(.*?) \((WBGene\d+)\)/; $_ = "$wbg ($name)"; } }
          foreach my $value (@values) {
            my $pg_value; my $pg_evidence;
            if ($value) { $pg_value = "'$value'"; } else { $pg_value = 'NULL'; }
            foreach my $evidence (sort keys %evidences) {
              ($evidence) = &filterSpaces($evidence);			# clear leading and trailing spaces
              if ($evidence =~ m/^(WBPerson\d+)/) { $evidence =~ s/^(WBPerson\d+)/Person_evidence\t\"$1\"/g; }
              elsif ($evidence =~ m/^Curator_confirmed\s+\"WBPerson\d+\"/) { 1; }	# proper Curator_confirmed format
              elsif ($evidence =~ m/^Person_evidence\s+\"[\w ]+\"/) { 1; }	# proper Author_evidence format
              elsif ($evidence =~ m/^Author_evidence\s+\"[\w ]+\"/) { 1; }	# proper Author_evidence format
              elsif ($evidence =~ m/^Inferred_automatically\s+\"[\.\w ]+\"/) { 1; }	# proper Inferred_automatically format
              elsif ($evidence =~ m/^Published_as\s+\"[\w\-\. ]+\"/) { 1; }		# proper Published_as format	for Kimberly 2006 01 20  Added hyphen 2006 02 03
              else { 
                print "<TR bgcolor=$red><TD>$pg_table</TD><TD>$value</TD><TD>NOT A VALID EVIDENCE TYPE $evidence</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n"; next; }
              print "<TR><TD>$pg_table</TD><TD>$value</TD><TD>$evidence</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n";
              if ($evidence) { $pg_evidence = "'$evidence'"; } else { $pg_evidence = 'NULL'; }
              my $result = $dbh->prepare( "INSERT INTO $pg_table VALUES ('$joinkey', $pg_value, $pg_evidence, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
              $result->execute;
              $pg_commands .= "INSERT INTO $pg_table VALUES ('$joinkey', $pg_value, $pg_evidence, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);<BR>\n"; 
            } # foreach my $evidence (@evidences)
          } # foreach my $value (@values)
        } else {
          if ($pg_table eq 'wpa_author') { if ($value =~ m/\D/) { $value =~ s/\D//g; } }	# only allow digits in wpa_author
          print "<TR><TD>$pg_table</TD><TD>$value</TD><TD>$order</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n";
          unless ($order) { $order = 'NULL'; }
          ($value) = &filterForPg($value);
          if ($value) { $value = "'$value'"; } else { $value = 'NULL'; }
#           my $result = $conn->exec( "INSERT INTO $pg_table VALUES ('$joinkey', $value, $order, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
          my $result = $dbh->prepare( "INSERT INTO $pg_table VALUES ('$joinkey', $value, $order, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
          $result->execute;
          $pg_commands .= "INSERT INTO $pg_table VALUES ('$joinkey', $value, $order, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);<BR>\n";
        }
      } # if ($update)
    } # for (1 .. $normal_count)
  } # foreach my $pg_table (@generic_tables)

  foreach my $author_type (@author_types) {
    my ($oop, $normal_count) = &getHtmlVar($query, "${author_type}_normal_count");
    ($oop, my $extra_count) = &getHtmlVar($query, "${author_type}_extra_count");
    my $full_count = 0; if ($normal_count) { $full_count += $normal_count; } if ($extra_count) { $full_count += $extra_count; }
    for my $row_count (1 .. $full_count ) {
      ($oop, my $update) = &getHtmlVar($query, "${author_type}_${row_count}_update");
      if ($update) {
        my $normal = 'normal'; if ($row_count > $normal_count) { $normal = 'extra'; }
        ($oop, my $second) = &getHtmlVar($query, "${author_type}_${row_count}_second"); 
        ($oop, my $id) = &getHtmlVar($query, "${author_type}_${row_count}_id");
        ($oop, my $value) = &getHtmlVar($query, "${author_type}_${row_count}_value");	# this has trouble sometimes, but don't know why  2005 10 19
        ($oop, my $valid) = &getHtmlVar($query, "${author_type}_${row_count}_valid");
        my $curator = $curators{std}{$theHash{curator}};
        if ( ($author_type eq 'verified') && ($normal eq 'extra') ) { ($oop, $curator) = &getHtmlVar($query, "${author_type}_${row_count}_curator"); }
        unless ($valid) { $valid = 'invalid'; }
        my $pg_author_type = 'wpa_author_' . $author_type;
        unless ($second) { $second = 'NULL'; }
        print "<TR><TD>$pg_author_type</TD><TD>$value</TD><TD>$second</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n";
        ($value) = &filterForPg($value);
        ($second) = &filterForPg($second);
        if ($value) { $value = "'$value'"; } else { $value = 'NULL'; }
        if ($pg_author_type eq 'wpa_author_index') { if ($second ne 'NULL') { $second = "'$second'"; } }	# put affiliation where order would be for index
#         my $result = $conn->exec( "INSERT INTO $pg_author_type VALUES ('$id', $value, $second, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
        my $result = $dbh->prepare( "INSERT INTO $pg_author_type VALUES ('$id', $value, $second, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
        $result->execute;
        $pg_commands .= "INSERT INTO $pg_author_type VALUES ('$id', $value, $second, '$valid', '$curator', CURRENT_TIMESTAMP);<BR>\n";
      } # if ($update)
    } # for (1 .. $normal_count)
  } # foreach my $pg_table (@generic_tables)
  print "</TABLE>\n";
  print "<P>\n";

  print "<input name=\"joinkey\" value=\"$joinkey\">\n";
  print "<input type=submit name=action value=\"See .ace Entry !\"><br />\n";

  print "<P>$pg_commands<P>\n";
  print "<P><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi>Back to first page</A><P>\n";
#   my $temp_curator = $theHash{curator}; $temp_curator =~ s/\s+/+/g;
#   print "<P><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/curation.cgi?curator_name=$temp_curator&action=Curate+%21&wbpaper_number=$joinkey>Curate this paper</A><P>\n";
  &populateCurators();
  my $temp_curator = $theHash{curator}; my $cur_id = $curators{std}{$temp_curator}; $cur_id =~ s/two//; $temp_curator =~ s/\s+/+/g;
  print "<P> <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/curator_first_pass.cgi?html_value_curator=$cur_id&action=Query&html_value_paper=$joinkey>Curate this paper</A><P>";	# link to new curator_first_pass.cgi  2009 04 06
} # sub updateInfo

sub seeAceEntry {
  my ($oop, $joinkey) = &getHtmlVar($query, 'joinkey');
  my ($all_entry, $long_text, $err_text) = &getPaper($joinkey);
  print "<TABLE border=0 cellspacing=2>\n";
  if ($all_entry) {
    print "<TR bgcolor='$blue'><TD bgcolor='white'></TD><TD>.ace file now looks like :</TD></TR>\n";
    if ($all_entry =~ m/\n/) { $all_entry =~ s/\n/<BR>\n/g; }
    print "<TR bgcolor='$blue'><TD bgcolor='white'></TD><TD>$all_entry</TD></TR>\n";
    print "<TR bgcolor='white'><TD bgcolor='white'>&nbsp;</TD></TR>\n"; }
  if ($long_text) {
    print "<TR bgcolor='$blue'><TD bgcolor='white'></TD><TD>LongText entry looks like :</TD></TR>\n";
    if ($long_text =~ m/\n/) { $long_text =~ s/\n/<BR>\n/g; }
    print "<TR bgcolor='$blue'><TD bgcolor='white'></TD><TD>$long_text</TD></TR>\n";
    print "<TR bgcolor='white'><TD bgcolor='white'>&nbsp;</TD></TR>\n"; }
  if ($err_text) {
    print "<TR bgcolor='$blue'><TD bgcolor='white'></TD><TD>Errors in .ace file :</TD></TR>\n";
    if ($err_text =~ m/\n/) { $err_text =~ s/\n/<BR>\n/g; }
    print "<TR bgcolor='$blue'><TD bgcolor='white'></TD><TD>$err_text</TD></TR>\n";
    print "<TR bgcolor='white'><TD bgcolor='white'>&nbsp;</TD></TR>\n"; }
  print "</TABLE>\n";
}

sub displayGenericPostgresRow {					# generalize displaying a @generic_table postgres row might make it easier to separate showing historic and valid
  my ($pg_table, $row_count, $row) = @_;
  my @row = split/\t/, $row;
  my $bgcolor = $blue;
  if ($row[1]) {
    $row_count++;
    if ($row[3] eq 'invalid') { $bgcolor = $red; }
    if ($row[3] eq 'misattributed') { $bgcolor = $red; }
#     print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${row_count}_type\" VALUE=\"$pg_table\">\n";
    print "<TR bgcolor='$bgcolor'>\n";
    print "  <TD>$pg_table</TD>\n";

    my $data = $row[1]; my $aname = '';
    if ($pg_table eq 'wpa_type') { 
      if ($type_index{$data}) { $aname = " ($type_index{$data})"; } }
    elsif ($pg_table eq 'wpa_author') { 
#       my $result = $conn->exec( "SELECT wpa_author_index FROM wpa_author_index WHERE author_id = '$data' ORDER BY wpa_timestamp DESC; ");	# get the latest one 2007 10 24
      my $result = $dbh->prepare( "SELECT wpa_author_index FROM wpa_author_index WHERE author_id = '$data' ORDER BY wpa_timestamp DESC; ");	# get the latest one 2007 10 24
      $result->execute;
      my @row = $result->fetchrow(); if ($row[0]) { $aname = " ($row[0])"; } }
    elsif ( ($pg_table eq 'wpa_erratum') || ($pg_table eq 'wpa_in_book') ) { 
      $aname = " <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$data&action=Extra+%21&extra=$pg_table&curator_name=$theHash{curator}\" TARGET=NEW>link</A>\n"; }
    else { 1; }
    if ($data =~ m/\"/) { $data =~ s/\"/&quot;/g; }		# make sure to pass doublequotes
    if ($data =~ m/\>/) { $data =~ s/\>/&gt;/g; }		# make sure to pass angled brackets
    if ($data =~ m/\</) { $data =~ s/\</&lt;/g; }
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_${row_count}_value\" VALUE=\"$data\">\n";
    print "  <TD>${data}${aname}</TD>\n";

    if ($row[2]) { 
        print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_${row_count}_order\" VALUE=\"$row[2]\">\n"; }
      else { $row[2] = '&nbsp;'; } 		# order
    print "  <TD ALIGN='CENTER'>$row[2]</TD>\n";
    
    if ($row[3]) {				# valid
        if ($pg_table eq 'wpa_identifier') { 
          print "  <TD><SELECT NAME=\"${pg_table}_${row_count}_valid\" SIZE=1>\n";
          print "    <OPTION VALUE=\"$row[3]\" SELECTED>$row[3]</OPTION>\n"; 
          print "    <OPTION VALUE=\"valid\">valid</OPTION>\n"; 
          print "    <OPTION VALUE=\"misattributed\">misattributed</OPTION>\n"; 
          print "    <OPTION VALUE=\"invalid\">invalid</OPTION>\n"; }
        else {
          my $checked = '';  if ($row[3] eq 'valid') { $checked = 'CHECKED'; }
          print "<TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" $checked></TD>\n"; } }
      else { print "<TD></TD>\n"; }

    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 

    print "  <TD>$row[4]</TD>\n";
    if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; } if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
    print "  <TD>$row[5]</TD>\n"; 

    print "</TR>\n";
#     if ($pg_table eq 'wpa_erratum') { $erratum = $row[1]; }
#     if ($pg_table eq 'wpa_in_book') { $in_book = $row[1]; }
  } # if ($row[1])
  return $row_count;
} # sub displayGenericPostgresRow


sub showIgnoreFlag {                # for Cecilia 2008 01 17
  my $joinkey = shift;
#   my $result = $conn->exec( "SELECT * FROM cfp_comment WHERE joinkey = '$joinkey' AND cfp_comment = 'the paper is used for functional annotations';" );
#   my $result = $conn->exec( "SELECT * FROM wpa_ignore WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp;" );
  my $result = $dbh->prepare( "SELECT * FROM wpa_ignore WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp;" );
  $result->execute;
  my %hash; while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $hash{$row[1]}++; } else { delete $hash{$row[1]}; } }
  foreach my $val (sort keys %hash) { print "<FONT SIZE=+2 COLOR=blue>$val<BR><BR></FONT>\n"; }
} # sub showIgnoreFlag

sub displayOneDataFromKey {
  my $wpa_id = shift;
  my ($joinkey) = &padZeros($wpa_id);

#   &readCurrentLocus();
  &populateCurators();
  &showIgnoreFlag($joinkey);
  print "<INPUT TYPE=submit NAME=action VALUE=\"Show Valid !\"> <INPUT TYPE=submit NAME=action VALUE=\"Show History !\"><P>\n";
  my $action; unless ($action = $query->param('action')) { $action = 'none'; }
  my $history_or_valid = 'valid';
  if ($action eq 'Show History !') { $history_or_valid = 'history'; }
  if ($history_or_valid eq 'valid') { print "Showing Valid data only (no history).<P>\n"; }
  elsif ($history_or_valid eq 'history') { print "Showing all history data (valid and invalid, look at timestamps to see what is current).<P>\n"; }
  else { print "Not a valid choice between Valid or History display of data.<P>\n"; }

#   my $result = $conn->exec( "SELECT wpa_valid FROM wpa WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC;" ); my @row = $result->fetchrow;  
  my $result = $dbh->prepare( "SELECT wpa_valid FROM wpa WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC;" ); 
  $result->execute;
  my @row = $result->fetchrow;  
  if ($row[0] eq 'invalid') { my $identifier = '';
#     $result = $conn->exec( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ '$joinkey' ORDER BY wpa_timestamp;" );
    $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ '$joinkey' ORDER BY wpa_timestamp;" );
    $result->execute;
    while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $identifier = $row[0]; } else { $identifier = ''; } }
    print "<FONT COLOR='red' SIZE=+2>NOT a valid paper";
    if ($identifier) { print ", merged with $identifier"; }
    print ".</FONT><P>\n"; }
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"number\" VALUE=\"$joinkey\">\n";
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD COLSPAN=5>ID : $joinkey</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Data</TD><TD>Order</TD><TD>Valid</TD><TD>Update</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n"; 
  my $counter = 0;
  my $erratum = 0; my $in_book = 0;
  my $row_count = 0;
  foreach my $pg_table (@generic_tables) {
    my $row_count = 0;
    if ($history_or_valid eq 'history') {		# to show history simply query in order (timestamp descending) and print
#         my $result = $conn->exec( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY wpa_order, wpa_timestamp DESC;" );
        my $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY wpa_order, wpa_timestamp DESC;" );
        $result->execute;
        while (my @row = $result->fetchrow) {
          for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
          my $row = join"\t", @row;							# group together the data to pass
          ($row_count) = &displayGenericPostgresRow($pg_table, $row_count, $row); } }	# display each data, updating the row_count
      else {						# to show valid data only, get in ascending timestamp order, store in a hash valid data and delete from the hash invalid data then show hash data
        my %rows_to_display;				# hash to store valid data only
#         my $result = $conn->exec( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY wpa_order, wpa_timestamp;" );
        my $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY wpa_order, wpa_timestamp;" );
        $result->execute;
        while (my @row = $result->fetchrow) {
          for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
          my $row = join"\t", @row;
          my $order = 'order'; if ($row[2]) { $order = $row[2]; }								# get the order, necessary for wpa_author
          if ( ($row[3] eq 'valid') || ($pg_table eq 'wpa') ) { $rows_to_display{$order}{$row[1]} = $row; }			# always display wpa since it needs to be possible to validate
            else { if ($rows_to_display{$order}{$row[1]}) { delete $rows_to_display{$order}{$row[1]}; } } }			# delete invalid data if it's been set to valid before
        foreach my $order (sort keys %rows_to_display) {									# looking at each order
          foreach my $row_value (keys %{ $rows_to_display{$order} }) {								# looking at each data value
            ($row_count) = &displayGenericPostgresRow($pg_table, $row_count, $rows_to_display{$order}{$row_value}); } } }	# display each data, updating the row count
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_normal_count\" VALUE=\"$row_count\">\n";
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_extra_count\" VALUE=\"$tables{copies}{$pg_table}\">\n";
    for (1 .. $tables{copies}{$pg_table}) {
      $row_count++;
#       print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${row_count}_type\" VALUE=\"$pg_table\">\n";
      print "<TR bgcolor='white'>\n";
      print "  <TD>$pg_table</TD>\n";
      if ($pg_table eq 'wpa') {
          print "  <TD>&nbsp;</TD>\n"; }
        elsif ($pg_table eq 'wpa_abstract') {
          print "  <TD ALIGN='LEFT'><TEXTAREA NAME=\"${pg_table}_${row_count}_value\" ROWS=8 COLS=60 VALUE=\"\"></TEXTAREA></TD>\n"; }
        elsif ($pg_table eq 'wpa_type') {
          print "  <TD><SELECT NAME=\"${pg_table}_${row_count}_value\" SIZE=1>\n";
          foreach my $type_number (sort {$a<=>$b} keys %type_index) { print "    <OPTION VALUE=\"$type_number\">$type_index{$type_number}</OPTION>\n"; }
          print "  </SELECT>\n"; }
        else {
          print "  <TD ALIGN='LEFT'><INPUT NAME=\"${pg_table}_${row_count}_value\" SIZE=40 VALUE=\"\"></TD>\n"; }
      if ($pg_table eq 'wpa_author') { 
          print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_order\" SIZE=5 VALUE=\"\"></TD>\n"; }
        else { print "  <TD>&nbsp;</TD>\n"; }
      if ($pg_table eq 'wpa_identifier') { 
          print "  <TD><SELECT NAME=\"${pg_table}_${row_count}_valid\" SIZE=1>\n";
          print "    <OPTION VALUE=\"valid\">valid</OPTION>\n"; 
          print "    <OPTION VALUE=\"misattributed\">misattributed</OPTION>\n"; 
          print "    <OPTION VALUE=\"invalid\">invalid</OPTION>\n"; }
        else {
          print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" CHECKED></TD>\n"; }

      print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 

      print "  <TD>$curators{std}{$theHash{curator}}</TD>\n";
      print "  <TD>CURRENT</TD>\n";
      print "</TR>\n";
    } # for (1 .. $tables{copies}{$pg_table})
  } # foreach my $wpa_table (@generic_tables)
  print "</TABLE><BR><BR>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Update Info !\"><P>\n";
  print "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Add+Another+Author+%21&curator_name=$theHash{curator}\" TARGET=NEW>Add Another Author</A>";
  print " You must <FONT COLOR=red>reload</FONT> this page (ctrl-shift-R or shift-reload) after creating new authors with this link.<P>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  &displayFullAuthor($joinkey, $history_or_valid);
  print "</TABLE><BR><BR>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  &displayGene($joinkey, $history_or_valid);
  print "</TABLE>\n";
#   print "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=CDS+Query+Page+%21&curator_name=$theHash{curator}\" TARGET=NEW>CDS Query Page</A><BR><BR>";	# getting rid of this since gene cds should now be automatically populated  2009 09 03
  print "<TABLE border=0 cellspacing=2>\n";
  &getPdfLink($joinkey, $history_or_valid);
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"row_count\" VALUE=\"$row_count\">\n";

  if ($erratum) { print "<TR><TD>&nbsp;</TD></TR><TR><TD>Erratum : </TD></TR>\n"; &displayOneDataFromKey($erratum); }
  if ($in_book) { print "<TR><TD>&nbsp;</TD></TR><TR><TD>In Book : </TD></TR>\n"; &displayOneDataFromKey($in_book); }
  print "</TABLE><BR><BR>\n";
} # sub displayOneDataFromKey

sub displayPdfPostgresRow {
  my ($pg_table, $row_count, $row) = @_;
  my @row = split/\t/, $row; my $bgcolor = $blue;
  if ($row[1]) {
    if ($row[3] eq 'invalid') { $bgcolor = $red; } else { $bgcolor = $blue; }
    $row_count++;
    print "<TR bgcolor='$bgcolor'>\n  <TD>wpa_electronic_path_type</TD>\n";
    my ($pdf) = $row[1] =~ m/\/([^\/]*)$/; my $pdf_link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf; 
    print "<TD><A HREF=\"$pdf_link\">$row[1]</A></TD>\n";	# link to pdf for Andrei  2006 09 07
    if ($row[1]) { print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_${row_count}_value\" VALUE=\"$row[1]\">\n"; }
#     my ($pdf) = $row[1] =~ m/\/([^\/]*)$/;
#     $pdf = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
#     print "<TD><A HREF=$pdf>$pdf</A></TD>\n";
    print "  <TD>$row[2] ($electronic_type_index{$row[2]})</TD>\n";
    if ($row[2]) { print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_${row_count}_order\" VALUE=\"$row[2]\">\n"; }
    if ($row[3]) {				# valid
        my $checked = '';  if ($row[3] eq 'valid') { $checked = 'CHECKED'; }
        print "<TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" $checked></TD>\n"; }
      else { print "<TD></TD>\n"; }
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 
    print "  <TD>$row[4]</TD>\n";
    if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; } if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
    print "  <TD>$row[5]</TD>\n";
    print "</TR>\n";
  }
  return $row_count;
} # sub displayPdfPostgresRow

sub getPdfLink {
  my ($joinkey, $history_or_valid) = @_;
#   my $result = $conn->exec( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ;" );
  my $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ;" );
  $result->execute;
  my $bgcolor = $blue;
  my $row_count = 0;
  my $pg_table = 'wpa_electronic_path_type';
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Link</TD><TD>Type</TD><TD>Valid</TD><TD>Update</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  if ($result->fetchrow) {
    if ($history_or_valid eq 'history') {		# to show history simply query in order (timestamp descending) and print
#         $result = $conn->exec( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC;" );
        $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC;" );
        $result->execute;
        while (my @row = $result->fetchrow) {
          for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
          my $row = join"\t", @row;							# group together the data to pass
          ($row_count) = &displayPdfPostgresRow($pg_table, $row_count, $row); } }	# display each data, updating the row_count
      else {
        my %rows_to_display;				# hash to store valid data only
#         $result = $conn->exec( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp ;" );
        $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp ;" );
        $result->execute;
        while (my @row = $result->fetchrow) {
          for (@row) { unless ($_) { $_ = ''; } }	# initialize blank row values
          my $row = join"\t", @row;							# group together the data to pass
          if ($row[3] eq 'valid') { $rows_to_display{$row[1]} = $row; }						# store by order and data the valid data
            else { if ($rows_to_display{$row[1]}) { delete $rows_to_display{$row[1]}; } } }			# delete invalid data if it's been set to valid before
        foreach my $path (sort keys %rows_to_display) {								# looking at each data value
          ($row_count) = &displayPdfPostgresRow($pg_table, $row_count, $rows_to_display{$path}); } }		# display each data, updating the row_count
  } # if ($result->fetchrow)
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_normal_count\" VALUE=\"$row_count\">\n";
  print "  <INPUT TYPE=\"HIDDEN\" NAME=\"${pg_table}_extra_count\" VALUE=\"$tables{copies}{$pg_table}\">\n";
  for (1 .. $tables{copies}{$pg_table}) {
    $row_count++;
    print "<TR bgcolor='white'>\n  <TD>wpa_electronic_path_type</TD>\n";
    print "  <TD ALIGN='LEFT'><INPUT NAME=\"${pg_table}_${row_count}_value\" SIZE=80 VALUE=\"\"></TD>\n"; 
#     print "  <TD>$electronic_type_index{$row[2]}</TD>\n";
    print "  <TD><SELECT NAME=\"${pg_table}_${row_count}_order\" SIZE=1>\n";
    foreach my $type_number (sort keys %electronic_type_index) { print "    <OPTION VALUE=\"$type_number\">$electronic_type_index{$type_number}</OPTION>\n"; }
    print "  </SELECT>\n"; 
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" CHECKED></TD>\n"; 
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${pg_table}_${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 
    print "  <TD>$curators{std}{$theHash{curator}}</TD>\n";
    print "  <TD>CURRENT</TD>\n";
    print "</TR>\n";
  }
} # sub getPdfLink

### DISPLAY ###


### INVALID PAPER QUERY ###

sub listInvalidNocuratableFunctional {	
    # programmatically access at http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?curator_name=two1823&action=listInvalidNocuratableFunctional
  my %wpas; my $result;			# the joinkeys
#   $result = $conn->exec( "SELECT * FROM wpa ORDER BY wpa_timestamp; "); 
  $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp; "); 
  $result->execute;
  while (my @row = $result->fetchrow) { if ($row[3] eq 'invalid') { $wpas{$row[0]}++; } else { delete $wpas{$row[0]}; } }	# populate most invalid joinkeys for type
#   $result = $conn->exec( "SELECT * FROM cfp_nocuratable ORDER BY cfp_timestamp; "); 
  $result = $dbh->prepare( "SELECT * FROM cfp_nocuratable ORDER BY cfp_timestamp; "); 
  $result->execute;
  while (my @row = $result->fetchrow) { $wpas{$row[0]}++; }	# add no curatable 
#   $result = $conn->exec( "SELECT * FROM cfp_comment WHERE cfp_comment ~ 'unctional annotations' ORDER BY cfp_timestamp; ");	# should this be wpa_ignore, maybe ?
  $result = $dbh->prepare( "SELECT * FROM wpa_ignore WHERE wpa_ignore ~ 'unctional annotation' ORDER BY cfp_timestamp; ");	# changed to wpa_ignore since no more FP 2009 10 19
  $result->execute;
  while (my @row = $result->fetchrow) { $wpas{$row[0]}++; }	# add functional annotations
  foreach my $joinkey (sort {$a<=>$b} keys %wpas) {
    next unless $joinkey =~ m/^0/;
    print "WBPaper$joinkey<BR>\n";
  }
}

### INVALID PAPER QUERY ###



### AUTHOR CREATION ###

sub addAnotherAuthor {
  &populateCurators();
  my ($oop, $number) = &getHtmlVar($query, 'number');
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"number\" VALUE=\"$number\">\n";
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR><TD>WBPaper Number</TD><TD>$number</TD></TR>\n";
  my $order = 0;
#   my $result = $conn->exec( "SELECT wpa_order FROM wpa_author WHERE joinkey = '$number' AND wpa_valid = 'valid' ORDER BY wpa_order DESC; ");
  my $result = $dbh->prepare( "SELECT wpa_order FROM wpa_author WHERE joinkey = '$number' AND wpa_valid = 'valid' ORDER BY wpa_order DESC; ");
  $result->execute;
  my @row = $result->fetchrow;
  if ($row[0]) { $order = $row[0]; }
  print "<TR><TD>Highest Author Order</TD><TD>$order</TD></TR>\n";
#   $result = $conn->exec( "SELECT last_value FROM wpa_author_index_author_id_seq; ");			# index not always maintained, just get last value 2005 09 26
#   $result = $conn->exec( "SELECT author_id FROM wpa_author_index ORDER BY author_id DESC;");
  $result = $dbh->prepare( "SELECT author_id FROM wpa_author_index ORDER BY author_id DESC;");
  $result->execute;
  @row = $result->fetchrow;
  print "<TR><TD>Highest Author ID</TD><TD>$row[0]</TD></TR>\n";

  my $row_count = 0;
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD>Order</TD><TD ALIGN=CENTER>Affiliation</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD><TD>Update</TD>\n";
  for (0 .. 10) {
    $row_count++;
    print "<TR bgcolor='white'>\n";
    print "  <TD ALIGN='LEFT'><INPUT NAME=\"${row_count}_value\" SIZE=20 VALUE=\"\"></TD>\n";
    print "  <TD ALIGN='LEFT'><INPUT NAME=\"${row_count}_order\" SIZE=4 VALUE=\"\"></TD>\n";
    print "  <TD ALIGN='LEFT'><INPUT NAME=\"${row_count}_affiliation\" SIZE=40 VALUE=\"\"></TD>\n"; 
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${row_count}_valid\" TYPE=CHECKBOX VALUE=\"valid\" CHECKED></TD>\n"; 
    print "  <TD>$curators{std}{$theHash{curator}}</TD>\n"; 
    print "  <TD>CURRENT</TD>\n";
    print "  <TD ALIGN='CENTER'><INPUT NAME=\"${row_count}_update\" TYPE=CHECKBOX VALUE=\"YES\"></TD>\n"; 
    print "</TR>\n";
  }
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"row_count\" VALUE=\"$row_count\">\n";
  print "<TR><TD><INPUT TYPE=submit NAME=action VALUE=\"Create Authors !\"></TD></TR>\n";
  print "</TABLE>\n";
} # sub addAnotherAuthor

sub createAuthors {
  &populateCurators();
  my $pg_commands = '';
  my ($oop, $number) = &getHtmlVar($query, 'number');
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"number\" VALUE=\"$number\">\n";
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR><TD>WBPaper Number</TD><TD>$number</TD></TR>\n";
#   my $result = $conn->exec( "SELECT last_value FROM wpa_author_index_author_id_seq; ");		# index not always maintained, just get last value 2005 09 26
#   my $result = $conn->exec( "SELECT author_id FROM wpa_author_index ORDER BY author_id DESC;");
  my $result = $dbh->prepare( "SELECT author_id FROM wpa_author_index ORDER BY author_id DESC;");
  $result->execute;
  my @row = $result->fetchrow;
  print "<TR><TD>Highest Author ID</TD><TD>$row[0]</TD></TR>\n";
  ($oop, my $max_rows) = &getHtmlVar($query, 'row_count');
  print "<TR><TD>Max Rows</TD><TD>$max_rows</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD ALIGN=CENTER>Author Order</TD><TD ALIGN=CENTER>Affiliation</TD><TD ALIGN=CENTER>Valid</TD></TR>\n"; 
  for my $row_count (0 .. $max_rows) {
    my ($oop, $update) = &getHtmlVar($query, "${row_count}_update");
    if ($update eq 'YES') { 
      my $author = ''; my $author_rank = 0; my $auth_affiliation = ''; my $valid = 'invalid';
      ($oop, $author) = &getHtmlVar($query, "${row_count}_value");
      ($oop, $author_rank) = &getHtmlVar($query, "${row_count}_order");
      ($oop, $auth_affiliation) = &getHtmlVar($query, "${row_count}_affiliation"); 
      ($oop, $valid) = &getHtmlVar($query, "${row_count}_valid"); 
      unless ($valid) { $valid = 'invalid'; }
      print "<TR bgcolor='$blue'><TD>$author</TD><TD>$author_rank</TD><TD>$auth_affiliation</TD><TD>$valid</TD></TR>\n"; 
      ($author) = &filterForPg($author);
      if ($auth_affiliation) { 
        ($auth_affiliation) = &filterForPg($auth_affiliation); 
        $auth_affiliation = "'$auth_affiliation'"; }
      else { $auth_affiliation = 'NULL'; }
#       my $result = $conn->exec( "SELECT nextval('wpa_author_index_author_id_seq');");			# index not always maintained, just get last value 2005 09 26
#       my $result = $conn->exec( "SELECT author_id FROM wpa_author_index ORDER BY author_id DESC;");
      my $result = $dbh->prepare( "SELECT author_id FROM wpa_author_index ORDER BY author_id DESC;");
      $result->execute;
      my @row = $result->fetchrow;
      my $auth_joinkey = $row[0]; 
      $auth_joinkey++;
#       $result = $conn->exec( "INSERT INTO wpa_author_index VALUES ('$auth_joinkey', '$author', $auth_affiliation, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);");
      $result = $dbh->prepare( "INSERT INTO wpa_author_index VALUES ('$auth_joinkey', '$author', $auth_affiliation, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);");
      $result->execute;
      $pg_commands .= "INSERT INTO wpa_author_index VALUES ('$auth_joinkey', '$author', $auth_affiliation, 'valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);<BR>\n";
#       $result = $conn->exec( "INSERT INTO wpa_author VALUES ('$number', '$auth_joinkey', $author_rank, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);");
      $result = $dbh->prepare( "INSERT INTO wpa_author VALUES ('$number', '$auth_joinkey', $author_rank, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);");
      $result->execute;
      $pg_commands .= "INSERT INTO wpa_author VALUES ('$number', '$auth_joinkey', $author_rank, 'valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);<BR>\n";
# These are missing wpa_join, so it's probably the wrong thing to do  2005 11 22
#       $result = $conn->exec( "INSERT INTO wpa_author_possible VALUES ('$auth_joinkey', NULL, NULL, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
#       $pg_commands .= "INSERT INTO wpa_author_possible VALUES ('$auth_joinkey', NULL, NULL, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); \");<BR>\n";
#       $result = $conn->exec( "INSERT INTO wpa_author_sent VALUES ('$auth_joinkey', NULL, NULL, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
#       $pg_commands .= "INSERT INTO wpa_author_sent VALUES ('$auth_joinkey', NULL, NULL, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); \");<BR>\n";
#       $result = $conn->exec( "INSERT INTO wpa_author_verified VALUES ('$auth_joinkey', NULL, NULL, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
#       $pg_commands .= "INSERT INTO wpa_author_verified VALUES ('$auth_joinkey', NULL, NULL, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); \");<BR><BR>\n";

    } # if ($update eq 'YES')
  } # for (0 .. $max_rows)
  print "</TABLE>\n";
  print "<P>$pg_commands<P>\n";
  print "Authors have been created, close this window and <FONT COLOR='red'>RELOAD</FONT> the window that linked here to show the newly created authors.<P>\n";
} # sub createAuthors

### AUTHOR CREATION ###


### SORT SECTION ###

sub getFirstPassTables {
  my $tables = get "http://tazendra.caltech.edu/~postgres/cgi-bin/curator_first_pass.cgi?action=ListPgTables";
  (@fptables) = $tables =~ m/PGTABLE : (.*)<br/g;
} # sub getFirstPassTables
  

sub sortAll {
  my ($type) = @_;
  &getFirstPassTables();
#   my ($firstpassTables) = &getFirstPassTables();
#   unless ($firstpassTables) { print "ERROR first pass tables read error for curation.cgi<BR>\n"; return; }
#   my (@fptables) = split/\s+/, $firstpassTables;  
  my %filter; my @filter;
  my @othertables = qw( go exprpattern );
  my @ignore_these_fp_fields = qw( pubID pdffilename curator reference fullauthorname);
  foreach my $fptable (@ignore_these_fp_fields) { $filter{$fptable}++; }
  foreach my $fptable (@fptables) { unless ($filter{$fptable}) { push @filter, $fptable; } }  @fptables = (); foreach my $fptable (@filter) { push @fptables, $fptable; }
  my $divide_by = '5'; my $count = 0; my %showTable;
  print "<TABLE border=0>\n"; 
  print "<TR><TD>Display : </TD></TR>\n"; 
  foreach my $fptable (@fptables, @othertables) { 
    my ($oop, $val) = &getHtmlVar($query, "display$fptable");
    if ($val eq 'checked') { $showTable{$fptable}++; }
    if ($count % $divide_by == 0) { print "<TR>\n"; }
    print "<TD><INPUT TYPE=checkbox NAME=display$fptable VALUE=checked $val> : $fptable</TD>\n"; 
    if ($count % $divide_by == $divide_by) { print "</TR>\n"; } $count++; }
  print "</TABLE>\n";
  &populateCurators();
  my ($oop, $num_per_page) = &getHtmlVar($query, 'num_per_page');
  if ($num_per_page) { $options{num_per_page} = $num_per_page; }	# don't want to zero this if html has no num_per_page data
  ($oop, my $search_joinkey) = &getHtmlVar($query, 'search_joinkey');
  if ($search_joinkey) { ($search_joinkey) = $search_joinkey =~ m/(\d+)/; }
  print "Displaying WBPapers with $type in first-pass, or entered in the list of curated w/o first-pass ;  $options{num_per_page} entries per page.<BR>\n";
  my %wpas; my @wpas; my $result;		# the joinkeys, sorted
#   $result = $conn->exec( "SELECT * FROM wpa ORDER BY wpa_timestamp; "); 
  $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp; "); 
  $result->execute;
  while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $wpas{$row[0]}++; } else { delete $wpas{$row[0]}; } }	# populate most valid joinkeys for type
#   my $cur_table = '';
#   if ($type eq 'Allele') { $cur_table = 'cur_newmutant'; }
#   elsif ($type eq 'Overexpression') { $cur_table = 'cur_overexpression'; }
#   elsif ($type eq 'RNAi') { $cur_table = 'cur_rnai'; }
#   $result = $conn->exec( "SELECT joinkey FROM $cur_table WHERE $cur_table IS NOT NULL AND joinkey ~ '^0'; "); 
#   while (my @row = $result->fetchrow) { $wpas{$row[0]}++; }	# populate most valid joinkeys for type
#   if ($type eq 'RNAi') {
#     $result = $conn->exec( "SELECT joinkey FROM cur_lsrnai WHERE cur_lsrnai IS NOT NULL AND joinkey ~ '^0'; "); 
#     while (my @row = $result->fetchrow) { $wpas{$row[0]}++; } } # populate lsrnai valid joinkeys
  foreach my $joinkey (sort keys %wpas) { push @wpas, $joinkey; }	# put in array for ease of adding list joinkeys with no FP
#   if ( ($type eq 'Overexpression') || ($type eq 'Allele')) {	# box only works for allele & overexpression, not rnai 2007 08 15
#     my ($wpaPointer) = &showCuratedBox($type, @wpas);			# show the box to add more type-curated but not necessarily first-pass curated papers
#     @wpas = @$wpaPointer; }							# also add that list of papers to the list of wpas to display  2007 08 01
  if ($search_joinkey) { 	# if showing all keep the @wpa list, otherwise search for the joinkey in the list  2007 08 15
    %wpas = (); foreach my $wpa (@wpas) { $wpas{$wpa}++; } 	# repopulate %hash based on all valid joinkeys
    @wpas = ();							# reset the wpa list result because looking for one specifically
    if ($wpas{$search_joinkey}) { push @wpas, $search_joinkey; } }	# put in list if found
  
  my ($current_page) = &getSortTypePage(scalar(@wpas), $type);		# get the current page if any, show sorting options
  my $skip_num = ($current_page - 1) * $options{num_per_page};	# skip this many entries based on page
  for (1 .. $skip_num) { shift @wpas; }				# skip them

# #   my $table_menu = "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>first-pass last curator</TD>"; #    don't show last curators  Kimberly and Karen  2008 04 11
#   my $table_menu = "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>PDF</TD>";
#   foreach my $fptable (@fptables) {
# #     if ($showTable{$fptable}) { $table_menu .= "<TD ALIGN=CENTER>$fptable first-pass data</TD><TD ALIGN=CENTER>$fptable last curator</TD><TD ALIGN=CENTER>curate</TD>"; } } # don't show last curators  Kimberly and Karen  2008 04 11
#     if ($showTable{$fptable}) { $table_menu .= "<TD ALIGN=CENTER COLSPAN=2>$fptable<BR>fp - curated</TD>"; } }
#   foreach my $othertable (@othertables) {
#     if ($showTable{$othertable}) { $table_menu .= "<TD ALIGN=CENTER>$othertable</TD>"; } }
#   $table_menu .= "</TR>\n";
  my $table_menu = "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>PDF</TD>";
  foreach my $fptable (@fptables) {
    if ($showTable{$fptable}) { $table_menu .= "<TD ALIGN=CENTER COLSPAN=2>$fptable</TD>"; } }
  foreach my $othertable (@othertables) {
    if ($showTable{$othertable}) { $table_menu .= "<TD ALIGN=CENTER>$othertable</TD>"; } }
  $table_menu .= "</TR>\n";
  $table_menu .= "<TR><TD colspan=3>&nbsp;</TD>";
  foreach my $fptable (@fptables) {
    if ($showTable{$fptable}) { $table_menu .= "<TD ALIGN=CENTER>fp</TD><TD ALIGN=CENTER>curated</TD>"; } }
  foreach my $othertable (@othertables) {
    if ($showTable{$othertable}) { $table_menu .= "<TD ALIGN=CENTER>&nbsp;</TD>"; } }
  print "<TABLE border=1>$table_menu\n";
  for (1 .. $options{num_per_page}) { 
    my $joinkey = shift @wpas; if ($joinkey) { 
      &sortAllLink($joinkey, $type); 
      foreach my $fptable (@fptables) { if ($showTable{$fptable}) { &showSpecific($joinkey, $fptable); } }
      foreach my $othertable (@othertables) { if ($showTable{$othertable}) { 
        if ($othertable eq 'exprpattern') { &showExprpattern($joinkey); } 
        if ($othertable eq 'go') { &showGO($joinkey); } } }
      print "</TR>\n";
  } }		# show paper data and link to it
  print "$table_menu</TABLE>\n";
} # sub sortAll

#   my $pgtable = 'wpa_' . lc($type) . '_curation';
#   if ($type eq 'Overexpression') { $pgtable = 'wpa_transgene_curation'; }
#   my $pg_command = "INSERT INTO $pgtable VALUES ('$joinkey', '$two_num', NULL, 'valid', '$two_num', CURRENT_TIMESTAMP); ";

sub showExprpattern {		# unclear if this is the same as expression	2008 04 03
  my $joinkey = shift; my $data;
  my $infile = '/home/acedb/wen/expr_pattern/ExprCurationStatus.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/^WBPaper$joinkey\t(.*?)$/) { $data .= $1; } }
  close (IN) or die "Cannot close $infile : $!";
  unless ($data) { $data = '&nbsp;'; }
  print "<TD>$data</TD>\n";
} # sub showExprpattern

sub showGO {
  my $joinkey = shift; my %genes;
  my @ontologies = qw( bio cell mol );
  foreach my $ont (@ontologies) {
    my $pgt = 'got_' . $ont . '_paper_evidence'; 
#     my $result = $conn->exec( "SELECT * FROM $pgt WHERE $pgt ~ '$joinkey'" );
    my $result = $dbh->prepare( "SELECT * FROM $pgt WHERE $pgt ~ '$joinkey'" );
    $result->execute;
    while (my @row = $result->fetchrow) { $genes{$row[0]}++; } }
  my @genes = sort keys %genes; my $genes = join", ", @genes; unless ($genes) { $genes = '&nbsp;'; }
  print "<TD>$genes</TD>";
} # sub showGo

sub showSpecific {
  my ($joinkey, $fptable) = @_;
#   my $result = $conn->exec( "SELECT * FROM cfp_$fptable WHERE joinkey = '$joinkey'" );
  my $result = $dbh->prepare( "SELECT * FROM cfp_$fptable WHERE joinkey = '$joinkey'" );
  $result->execute;
#   my @row = $result->fetchrow; my $fpdata = $row[1];  unless ($fpdata) { $fpdata = '&nbsp;'; }
  my @row = $result->fetchrow; my $fpdata = $row[1];  if ($fpdata) { $fpdata = 'yes'; } else { $fpdata = 'no'; }
  print "<TD ALIGN=center>$fpdata</TD>";
#   $result = $conn->exec( "SELECT * FROM wpa_${fptable}_curation WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC;" );
  $result = $dbh->prepare( "SELECT * FROM wpa_${fptable}_curation WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC;" );
  $result->execute;
  @row = $result->fetchrow; my $data = $row[1]; if ($data) { if ($curators{two}{$data}) { $data = $curators{two}{$data}; } } else { $data = '&nbsp;'; }
#   print "<TD>$data</TD>";
  my $is_checked = 'no';
#   if ($fptable eq 'newmutant') { $result = $conn->exec( "SELECT * FROM app_paper WHERE app_paper = 'WBPaper$joinkey';" ); 
  if ($fptable eq 'newmutant') { 
    $result = $dbh->prepare( "SELECT * FROM app_paper WHERE app_paper = 'WBPaper$joinkey';" ); 
    $result->execute;
    my @row = $result->fetchrow(); if ($row[1]) { $is_checked = 'yes'; } }
#   if ( ($fpdata eq '&nbsp;') && ($is_checked eq 'no') ) { $is_checked = 'n/a'; }
  if ( ($fpdata eq 'no') && ($is_checked eq 'no') ) { $is_checked = 'n/a'; }
#   print "<TD><INPUT TYPE=checkbox NAME=${fptable}_$joinkey VALUE=checked $is_checked></TD>";	# no more checkboxes  Kimberly and Karen  2008 04 11
  print "<TD ALIGN=center>$is_checked</TD>";
} # sub showSpecific

sub sortAllLink {			# show paper data and link it
  my ($joinkey, $type) = @_;
  my $temp_curator = $theHash{curator}; $temp_curator =~ s/\s+/+/g;
  my $check_out = "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?curator_name=$temp_curator&action=$type+Curate+%21&wbpaper_number=$joinkey>$type curate</A>";
#   my $result = $conn->exec( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );	# only one value per joinkey, but timestamp in case changed later
  my $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );	# only one value per joinkey, but timestamp in case changed later
  $result->execute;
  my @row = $result->fetchrow; my $last_curator = ''; if ($row[1]) { $last_curator = $curators{two}{$row[1]}; }		# this will work when cur_curator has joinkeys as wbpapers
#   $result = $conn->exec( "SELECT * FROM wpa_checked_out WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_checked_out WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $checked_out = ''; if ($row[1]) { $checked_out = $curators{two}{$row[1]}; }
#   $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  @row = $result->fetchrow; my $title = ''; if ($row[1]) { $title = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $journal = ''; if ($row[1]) { $journal = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_hardcopy WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_hardcopy WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $hardcopy = 'NO'; if ($row[1]) { $hardcopy = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_identifier WHERE joinkey = '$joinkey' ORDER BY wpa_identifier, wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE joinkey = '$joinkey' ORDER BY wpa_identifier, wpa_timestamp DESC" );
  $result->execute;
  my %wpa_id = (); my @wpa_id;			# for a joinkey get all ids sorted by id and descending timestamp (to get latest first, so only get latest to check validity)
  while (my @row = $result->fetchrow) { 	# for each value, check if already gotten, if new check if valid, if valid put in hash
    unless ($wpa_id{$row[1]}) { $wpa_id{$row[1]}++; if ($row[3] eq 'valid') { push @wpa_id, $row[1]; } } }
  my $identifiers = join"<BR>", @wpa_id;
#   $result = $conn->exec( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_electronic_path_type, wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_electronic_path_type, wpa_timestamp DESC" );
  $result->execute;
  my %wpa_path = (); my @wpa_path;			# for a joinkey get all ids sorted by id and descending timestamp (to get latest first, so only get latest to check validity)
  while (my @row = $result->fetchrow) { 	# for each value, check if already gotten, if new check if valid, if valid put in hash
    unless ($wpa_path{$row[1]}) { $wpa_path{$row[1]}++; if ($row[3] eq 'valid') { 
      my ($pdf) = $row[1] =~ m/\/([^\/]*)$/; my $pdf_link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf; $pdf = "<A HREF=$pdf_link>$pdf</A>"; push @wpa_path, $pdf } } }
  my $pdfs = join"<BR>", @wpa_path;
#   print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">$joinkey</A></TD><TD>$identifiers</TD><TD>$pdfs</TD><TD>$last_curator</TD>\n"; #    don't show last curators  Kimberly and Karen  2008 04 11
  print "<TR><TD ALIGN=center><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">$joinkey</A></TD><TD ALIGN=center>$identifiers</TD><TD ALIGN=center>$pdfs</TD>\n"; 
#   my $cur_table = '';
#   if ($type eq 'Allele') { $cur_table = 'cur_newmutant'; }
#   elsif ($type eq 'Overexpression') { $cur_table = 'cur_overexpression'; }
#   elsif ($type eq 'RNAi') { $cur_table = 'cur_rnai'; }
#   $result = $conn->exec( "SELECT * FROM $cur_table WHERE joinkey = '$joinkey' ORDER BY cur_timestamp DESC" );
#   @row = $result->fetchrow; my $type_data = '&nbsp;'; if ($row[1]) { $type_data = $row[1]; }
#   my @type_data = split/\s+/, $type_data; 
#   if (scalar(@type_data>40)) { for my $i (40 .. $#type_data) { $type_data[$i] = ''; } $type_data = join" ", @type_data; $type_data .= ' ... etc.'}
#   if ($type eq 'RNAi') {
#     $result = $conn->exec( "SELECT * FROM cur_lsrnai WHERE joinkey = '$joinkey' ORDER BY cur_timestamp DESC" );
#     @row = $result->fetchrow; my $lsrnai_data = '&nbsp;'; if ($row[1]) { $lsrnai_data = $row[1]; }
#     my @lsrnai_data = split/\s+/, $lsrnai_data; 
#     if (scalar(@lsrnai_data>40)) { for my $i (40 .. $#lsrnai_data) { $lsrnai_data[$i] = ''; } $lsrnai_data = join" ", @lsrnai_data; $lsrnai_data .= ' ... etc.'}
#     $type_data .= '</TD><TD>' . $lsrnai_data; }
#   my $pgtable = 'wpa_' . lc($type) . '_curation';
#   if ($type eq 'Overexpression') { $pgtable = 'wpa_transgene_curation'; }
#   $result = $conn->exec( "SELECT * FROM $pgtable WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
#   @row = $result->fetchrow; my $type_curator = ''; if ($row[1]) { $type_curator = $curators{two}{$row[1]}; }
#   print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">$joinkey</A></TD><TD>$identifiers</TD><TD>$pdfs</TD><TD>$last_curator</TD><TD>$type_data</TD><TD>$type_curator</TD><TD>$check_out</TD></TR>\n"; 
} # sub sortAllLink

sub sortType {
  my ($type) = @_;
  &populateCurators();
  my ($oop, $num_per_page) = &getHtmlVar($query, 'num_per_page');
  if ($num_per_page) { $options{num_per_page} = $num_per_page; }	# don't want to zero this if html has no num_per_page data
  ($oop, my $search_joinkey) = &getHtmlVar($query, 'search_joinkey');
  if ($search_joinkey) { ($search_joinkey) = $search_joinkey =~ m/(\d+)/; }
  print "Displaying WBPapers with $type in first-pass, or entered in the list of curated w/o first-pass ;  $options{num_per_page} entries per page.<BR>\n";
  my %wpas; my @wpas; my $result;		# the joinkeys, sorted
  my $cfp_table = '';
  if ($type eq 'Allele') { $cfp_table = 'cfp_newmutant'; }
  elsif ($type eq 'Overexpression') { $cfp_table = 'cfp_overexpr'; }
  elsif ($type eq 'RNAi') { $cfp_table = 'cfp_rnai'; }
# before adding stuff from a separate list to the results this worked.  now need to populate full list and the look for search result in full list  2007 08 15
#   if ($search_joinkey) { $result = $conn->exec( "SELECT joinkey FROM $cur_table WHERE $cur_table IS NOT NULL AND joinkey ~ '^0' AND joinkey ~ '$search_joinkey'; "); }
#     else { $result = $conn->exec( "SELECT joinkey FROM $cur_table WHERE $cur_table IS NOT NULL AND joinkey ~ '^0'; "); }
#   while (my @row = $result->fetchrow) { $wpas{$row[0]}++; }
#   if ($type eq 'RNAi') {
#     if ($search_joinkey) { $result = $conn->exec( "SELECT joinkey FROM cur_lsrnai WHERE cur_lsrnai IS NOT NULL AND joinkey ~ '^0' AND joinkey ~ '$search_joinkey'; "); }
#       else { $result = $conn->exec( "SELECT joinkey FROM cur_lsrnai WHERE cur_lsrnai IS NOT NULL AND joinkey ~ '^0'; "); }
#     while (my @row = $result->fetchrow) { $wpas{$row[0]}++; } }
#   $result = $conn->exec( "SELECT joinkey FROM $cfp_table WHERE $cfp_table IS NOT NULL AND joinkey ~ '^0'; "); 
  $result = $dbh->prepare( "SELECT joinkey FROM $cfp_table WHERE $cfp_table IS NOT NULL AND joinkey ~ '^0'; "); 
  $result->execute;
  while (my @row = $result->fetchrow) { $wpas{$row[0]}++; }	# populate most valid joinkeys for type
  if ($type eq 'RNAi') {
#     $result = $conn->exec( "SELECT joinkey FROM cfp_lsrnai WHERE cfp_lsrnai IS NOT NULL AND joinkey ~ '^0'; "); 
    $result = $dbh->prepare( "SELECT joinkey FROM cfp_lsrnai WHERE cfp_lsrnai IS NOT NULL AND joinkey ~ '^0'; "); 
    $result->execute;
    while (my @row = $result->fetchrow) { $wpas{$row[0]}++; } } # populate lsrnai valid joinkeys
  foreach my $joinkey (sort keys %wpas) { push @wpas, $joinkey; }	# put in array for ease of adding list joinkeys with no FP
  if ( ($type eq 'Overexpression') || ($type eq 'Allele')) {	# box only works for allele & overexpression, not rnai 2007 08 15
    my ($wpaPointer) = &showCuratedBox($type, @wpas);			# show the box to add more type-curated but not necessarily first-pass curated papers
    @wpas = @$wpaPointer; }							# also add that list of papers to the list of wpas to display  2007 08 01
  if ($theHash{curator} =~ m/Karen/) { @wpas = reverse @wpas; }	# reverse list for Karen only 	2008 06 09
  if ($search_joinkey) { 	# if showing all keep the @wpa list, otherwise search for the joinkey in the list  2007 08 15
    %wpas = (); foreach my $wpa (@wpas) { $wpas{$wpa}++; } 	# repopulate %hash based on all valid joinkeys
    @wpas = ();							# reset the wpa list result because looking for one specifically
    if ($wpas{$search_joinkey}) { push @wpas, $search_joinkey; } }	# put in list if found
  
  my ($current_page) = &getSortTypePage(scalar(@wpas), $type);		# get the current page if any, show sorting options
  my $skip_num = ($current_page - 1) * $options{num_per_page};	# skip this many entries based on page
  for (1 .. $skip_num) { shift @wpas; }				# skip them
  my $table_menu = "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>first-pass last curator</TD><TD ALIGN=CENTER>$type data</TD><TD ALIGN=CENTER>$type last curator</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
  if ($type eq 'RNAi') { $table_menu = "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>first-pass last curator</TD><TD ALIGN=CENTER>$type data</TD><TD ALIGN=CENTER>LS $type data</TD><TD ALIGN=CENTER>$type last curator</TD><TD ALIGN=CENTER>curate</TD><TD>RNAi Int Done ?</TD></TR>\n"; }
  print "<TABLE border=0>$table_menu\n";
  my @joinkeys;
  for (1 .. $options{num_per_page}) { my $joinkey = shift @wpas; if ($joinkey) { &sortTypeLink($joinkey, $type); push @joinkeys, $joinkey; } }		# show paper data and link to it
  print "$table_menu</TABLE>\n"; 
  print "<INPUT TYPE=submit NAME=action VALUE=\"$type Int Done Checkbox Update !\">\n";
  my $joinkeys = join"\t", @joinkeys; print "<INPUT TYPE=\"HIDDEN\" NAME=\"joinkeys\" VALUE=\"$joinkeys\">\n";
} # sub sortType

sub curatedNoFP {			# if adding WBPapers to list of papers that have already been curated for that type but not necessarily first-pass curated
  my $type = shift;
  my $infile = '/home/postgres/public_html/cgi-bin/data/' . $type . '_curated';			# write them to data/type_curated
  $/ = undef;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  my $all_file = <IN>;
  close (IN) or die "Cannot close $infile : $!";
  $/ = "\n";
  my (@allele_curated) = $all_file =~ m/(\d{8})/g;
  my %sort; foreach my $paper (@allele_curated) { $sort{$paper}++; }
  my ($oop, $cfp_nfp) = &getHtmlVar($query, 'curated_not_firstpass');
  my (@cfp_nfp) = $cfp_nfp =~ m/(\d{8})/g;
  foreach my $paper (@cfp_nfp) { $sort{$paper}++; }
  open (OUT, ">$infile") or die "Cannot rewrite $infile : $!";
  foreach my $paper (sort keys %sort) { 
    print OUT "$paper\n"; 
#     my $result = $conn->exec( "SELECT * FROM cfp_curator WHERE joinkey ~ '$paper';" );		# if it has been first-pass curated, check it has first-pass data, if it doesn't say ``yes''. for Gary and Karen 2007 10 01
    my $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE joinkey ~ '$paper';" );		# if it has been first-pass curated, check it has first-pass data, if it doesn't say ``yes''. for Gary and Karen 2007 10 01
    $result->execute;
    my @row = $result->fetchrow;						
    if ($row[1]) { 
      my $cfp_table;
      if ($type eq 'Allele') { $cfp_table = 'cfp_newmutant'; }
      elsif ($type eq 'Overexpression') { $cfp_table = 'cfp_overexpr'; }
      elsif ($type eq 'RNAi') { $cfp_table = 'cfp_rnai'; }
#       $result = $conn->exec( "SELECT * FROM $cfp_table WHERE joinkey ~ '$paper';" );
      $result = $dbh->prepare( "SELECT * FROM $cfp_table WHERE joinkey ~ '$paper';" );
      $result->execute;
      my @row2 = $result->fetchrow;
      unless ($row2[1]) { 
#         $result = $conn->exec( "INSERT INTO $cfp_table VALUES ( '$paper', 'yes' );" ); 
        $result = $dbh->prepare( "INSERT INTO $cfp_table VALUES ( '$paper', 'yes' );" ); 
        $result->execute;
  } } }
  close (OUT) or die "Cannot close $infile : $!";
  my @list = sort keys %sort; my $list = join", ", @list;
  print "The list of Curated w/o First-Pass is now : $list<BR>\n";
} # sub curatedNoFP

sub showCuratedBox {		# show the box to add more type-curated but not necessarily first-pass curated papers also add that list of papers to the list of wpas to display  2007 08 01
  my ($type, @wpas) = @_;
  print "Enter WBPapers curated w/o first-pass (8 digits) :<BR><TEXTAREA NAME=\"curated_not_firstpass\" ROWS=4 COLS=30 VALUE=\"\"></TEXTAREA><BR>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"$type Curated no FP !\">\n";
  $type = lc($type);
  my $infile = '/home/postgres/public_html/cgi-bin/data/' . $type . '_curated';
  $/ = undef;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  my $all_file = <IN>;
  close (IN) or die "Cannot close $infile : $!";
  $/ = "\n";
  my (@allele_curated) = $all_file =~ m/(\d{8})/g;
  my %sort;
  foreach my $wpa (@wpas) { $sort{$wpa}++; }
  foreach my $allele_curated (@allele_curated) { $sort{$allele_curated}++; }
  my @all_allele = sort keys %sort;
  return \@all_allele;
} # sub showCuratedBox

sub sortTypeLink {			# show paper data and link it
  my ($joinkey, $type) = @_;
  my $temp_curator = $theHash{curator}; $temp_curator =~ s/\s+/+/g;
  my $check_out = "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?curator_name=$temp_curator&action=$type+Curate+%21&wbpaper_number=$joinkey>$type curate</A>";
#   my $result = $conn->exec( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );	# only one value per joinkey, but timestamp in case changed later
  my $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );	# only one value per joinkey, but timestamp in case changed later
  $result->execute;
  my @row = $result->fetchrow; my $last_curator = ''; if ($row[1]) { $last_curator = $curators{two}{$row[1]}; }		# this will work when cfp_curator has joinkeys as wbpapers
#   $result = $conn->exec( "SELECT * FROM wpa_checked_out WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_checked_out WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $checked_out = ''; if ($row[1]) { $checked_out = $curators{two}{$row[1]}; }
#   $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $title = ''; if ($row[1]) { $title = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $journal = ''; if ($row[1]) { $journal = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_hardcopy WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_hardcopy WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $hardcopy = 'NO'; if ($row[1]) { $hardcopy = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_identifier WHERE joinkey = '$joinkey' ORDER BY wpa_identifier, wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE joinkey = '$joinkey' ORDER BY wpa_identifier, wpa_timestamp DESC" );
  $result->execute;
  my %wpa_id = (); my @wpa_id;			# for a joinkey get all ids sorted by id and descending timestamp (to get latest first, so only get latest to check validity)
  while (my @row = $result->fetchrow) { 	# for each value, check if already gotten, if new check if valid, if valid put in hash
    unless ($wpa_id{$row[1]}) { $wpa_id{$row[1]}++; if ($row[3] eq 'valid') { push @wpa_id, $row[1]; } } }
  my $identifiers = join"<BR>", @wpa_id;
#   $result = $conn->exec( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_electronic_path_type, wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_electronic_path_type, wpa_timestamp DESC" );
  $result->execute;
  my %wpa_path = (); my @wpa_path;			# for a joinkey get all ids sorted by id and descending timestamp (to get latest first, so only get latest to check validity)
  while (my @row = $result->fetchrow) { 	# for each value, check if already gotten, if new check if valid, if valid put in hash
    unless ($wpa_path{$row[1]}) { $wpa_path{$row[1]}++; if ($row[3] eq 'valid') { 
      my ($pdf) = $row[1] =~ m/\/([^\/]*)$/; my $pdf_link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf; $pdf = "<A HREF=$pdf_link>$pdf</A>"; push @wpa_path, $pdf } } }
  my $pdfs = join"<BR>", @wpa_path;
  my $cfp_table = '';
  if ($type eq 'Allele') { $cfp_table = 'cfp_newmutant'; }
  elsif ($type eq 'Overexpression') { $cfp_table = 'cfp_overexpr'; }
  elsif ($type eq 'RNAi') { $cfp_table = 'cfp_rnai'; }
#   $result = $conn->exec( "SELECT * FROM $cfp_table WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM $cfp_table WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $type_data = '&nbsp;'; if ($row[1]) { $type_data = $row[1]; }
  my @type_data = split/\s+/, $type_data; 
  if (scalar(@type_data>40)) { for my $i (40 .. $#type_data) { $type_data[$i] = ''; } $type_data = join" ", @type_data; $type_data .= ' ... etc.'}
  if ($type eq 'RNAi') {
#     $result = $conn->exec( "SELECT * FROM cfp_lsrnai WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );
    $result = $dbh->prepare( "SELECT * FROM cfp_lsrnai WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );
    $result->execute;
    @row = $result->fetchrow; my $lsrnai_data = '&nbsp;'; if ($row[1]) { $lsrnai_data = $row[1]; }
    my @lsrnai_data = split/\s+/, $lsrnai_data; 
    if (scalar(@lsrnai_data>40)) { for my $i (40 .. $#lsrnai_data) { $lsrnai_data[$i] = ''; } $lsrnai_data = join" ", @lsrnai_data; $lsrnai_data .= ' ... etc.'}
    $type_data .= '</TD><TD>' . $lsrnai_data; }
  my $pgtable = 'wpa_' . lc($type) . '_curation';
  if ($type eq 'Overexpression') { $pgtable = 'wpa_transgene_curation'; }
#   $result = $conn->exec( "SELECT * FROM $pgtable WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM $pgtable WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $type_curator = ''; if ($row[1]) { $type_curator = $curators{two}{$row[1]}; }
  print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">$joinkey</A></TD><TD>$identifiers</TD><TD>$pdfs</TD><TD>$last_curator</TD><TD>$type_data</TD><TD>$type_curator</TD><TD>$check_out</TD>\n";
  if ($type eq 'RNAi') { 
#     $result = $conn->exec( "SELECT * FROM wpa_rnai_int_done WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
    $result = $dbh->prepare( "SELECT * FROM wpa_rnai_int_done WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
    $result->execute;
    @row = $result->fetchrow; my $rnai_int_done = ''; if ($row[1]) { $rnai_int_done = 'checked'; }
    print "<TD ALIGN=CENTER><INPUT NAME=\"int_done_$joinkey\" TYPE=CHECKBOX VALUE=\"checked\" $rnai_int_done></TD>\n"; }
  print "</TR>\n"; 
} # sub sortTypeLink

sub checkboxUpdate {		# deal with checkboxes refering to whether RNAi based Interaction has been finished for that paper  2008 05 06
  my $type = shift;
  if ($type eq 'rnai_int_done') {
    &populateCurators();
    my ($oop, $curator) = &getHtmlVar($query, 'curator_name');
    $curator = $curators{std}{$curator};
    ($oop, my $joinkeys) = &getHtmlVar($query, 'joinkeys');
    my @joinkeys = split/\t/, $joinkeys;
    foreach my $joinkey (@joinkeys) {
      ($oop, my $form_checked) = &getHtmlVar($query, "int_done_$joinkey");
#       print "J $joinkey CHECKED $form_checked J<BR>\n";
#       my $result = $conn->exec( "SELECT * FROM wpa_rnai_int_done WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_rnai_int_done WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
      $result->execute;
      my @row = $result->fetchrow; my $rnai_int_done = ''; if ($row[1]) { $rnai_int_done = 'checked'; }
      if ($form_checked ne $rnai_int_done) { 
        if ($form_checked) { $form_checked = "'$form_checked'"; } else { $form_checked = 'NULL'; }
        my $command = "INSERT INTO wpa_rnai_int_done VALUES ('$joinkey', $form_checked, NULL, 'valid', '$curator');";
#         my $result2 = $conn->exec( $command );
        my $result2 = $dbh->prepare( $command );
        $result2->execute;
        print "$command<BR>\n";
  } } }
} # sub checkboxUpdate


sub getSortTypePage {		# get page and show sorting options, return the chosen current page
  my ($full_count, $type) = @_;
  my ($oop, $current_page) = &getHtmlVar($query, 'sort_page_number');
  unless ($current_page) { $current_page = 1; }			# default to page 1
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";
  my $pages = $full_count/$options{num_per_page}; $pages = ceil($pages);	# ceil is a POSIX function to round up
  print "There are $full_count WBPapers in $pages pages.  You are in page ${current_page}.<BR>\n";
  print "<FONT SIZE=-2>How many entries per page :<INPUT NAME=num_per_page SIZE=4 VALUE=$options{num_per_page}></FONT>\n";
  print "<FONT SIZE=-2>Search for WBPaper# :<INPUT NAME=search_joinkey SIZE=10></FONT><BR>\n";
  print "Select your Page number : <SELECT NAME=\"sort_page_number\" SIZE=1>\n";
#   print "<OPTION>$current_page</OPTION>\n";
  for (1 .. $pages) { 
    print "<OPTION";
    if ($_ eq $current_page) { print " SELECTED"; }
    print ">$_</OPTION>\n"; }
  print "</SELECT>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"$type Curation !\">\n";
  print "<P><BR><P>\n";
  print "</FORM>";
  return $current_page;
} # sub getSortTypePage

sub showFalsePositives {
  print "Curator $theHash{curator}\n";
  my ($var, $table) = &getHtmlVar($query, "fptype");
  print "using table $table<BR>\n";
  print "<TABLE BORDER=1>\n";
#   my $result = $conn->exec( "SELECT * FROM cfp_$table WHERE cfp_$table ~ 'FALSE POSITIVE' ");
  my $result = $dbh->prepare( "SELECT * FROM cfp_$table WHERE cfp_$table ~ 'FALSE POSITIVE' ");
  $result->execute;
  while (my @row = $result->fetchrow) {
    foreach (@row) { $_ = "<TD>$_</TD>"; }
    print "<TR>@row</TR>\n"; 
  } # while (my @row = $result->fetchrow)
  print "</TABLE>\n";
#   ($var, my $data) = &getHtmlVar($query, "false_positives");
#   my (@lines) = split/\n/, $data;
#   foreach my $line (@lines) {
#     my ($wbp, $comment) = ("", "no comment");
#     if ($line =~ m/^\s*?(\S+)\s+(.*)$/) {
#       ($wbp, $comment) = $line =~ m/^\s*?(\S+)\s+(.*)$/; }
#     elsif ($line =~ m/^\s*?(\S+)$/) {
#       ($wbp) = $line =~ m/^\s*?(\S+)$/; }
#     $wbp = lc($wbp);
#     my $paper = '';
#     if ($wbp =~ m/wbpaper(\d+)/) { $paper = $1; }
#     elsif ($wbp =~ m/^(\d+)$/) { $paper = $1; }
#     else { print "<FONT COLOR=red>ERROR, line doesn't start with a WBPaper : $line</FONT>.<BR>\n"; next; }
#     &postgresFalsePositive($table, $paper, $comment);
#   } # foreach my $line (@lines)
} 
sub enterFalsePositives {
  print "Curator $theHash{curator}\n";
  my ($var, $table) = &getHtmlVar($query, "fptype");
  print "using table $table<BR>\n";
  ($var, my $data) = &getHtmlVar($query, "false_positives");
  my (@lines) = split/\n/, $data;
  foreach my $line (@lines) {
    my ($wbp, $comment) = ("", "no comment");
    if ($line =~ m/^\s*?(\S+)\s+(.*)$/) {
      ($wbp, $comment) = $line =~ m/^\s*?(\S+)\s+(.*)$/; }
    elsif ($line =~ m/^\s*?(\S+)$/) {
      ($wbp) = $line =~ m/^\s*?(\S+)$/; }
    $wbp = lc($wbp);
    my $paper = '';
    if ($wbp =~ m/wbpaper(\d+)/) { $paper = $1; }
    elsif ($wbp =~ m/^(\d+)$/) { $paper = $1; }
    else { print "<FONT COLOR=red>ERROR, line doesn't start with a WBPaper : $line</FONT>.<BR>\n"; next; }
    &postgresFalsePositive($table, $paper, $comment);
  } # foreach my $line (@lines)
} # sub enterFalsePositives

sub postgresFalsePositive {
  my ($table, $paper, $comment) = @_;
  ($comment) = &filterForPg($comment);			# replace ' with ''
#   my $result = $conn->exec( "SELECT * FROM cfp_$table WHERE joinkey = '$paper' ");
  my $result = $dbh->prepare( "SELECT * FROM cfp_$table WHERE joinkey = '$paper' ");
  $result->execute;
  my $pgcommand = '';
  my @row = $result->fetchrow();
  if ($row[0]) { 
    $pgcommand = "UPDATE cfp_$table SET cfp_$table = '$row[1] is FALSE POSITIVE : $comment -- $theHash{curator}' WHERE joinkey = '$paper'; ";
#     $result = $conn->exec( $pgcommand );
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
    $pgcommand = "UPDATE cfp_$table SET cfp_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$paper'; ";
#     $result = $conn->exec( $pgcommand );
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
  } else {
    $pgcommand = "INSERT INTO cfp_$table VALUES ('$paper', 'FALSE POSITIVE : $comment -- $theHash{curator}'); ";
#     $result = $conn->exec( $pgcommand );
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
  } 
} # sub postgresFalsePositive

sub falsePositives {
  &populateCurators();
  &getFirstPassTables();
  my %filter;
  foreach my $table (@fptables) { $filter{$table}++; }
  $filter{""}++;
  print "Select a first pass type to mark as false positive : <SELECT NAME=\"fptype\" SIZE=1>\n";
  print "<OPTION>extvariation</OPTION>\n";
  foreach my $table (sort keys %filter) { print "<OPTION>$table</OPTION>\n"; }
  print "</SELECT><BR>\n";
  print "Enter WBPapers and comment (one each per line) : <BR>\n";
  print "<TEXTAREA NAME=\"false_positives\" ROWS=35 COLS=80 VALUE=\"\"></TEXTAREA><BR>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Enter False Positives !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Show False Positives !\"><P>\n";
}

sub alreadyCurated {
  &populateCurators();
  &getFirstPassTables();
  my %filter;
  foreach my $table (@fptables) { $filter{$table}++; }
  $filter{""}++;
  print "Select a first pass type to mark as Already Curated : <SELECT NAME=\"fptype\" SIZE=1>\n";
  print "<OPTION>extvariation</OPTION>\n";
  foreach my $table (sort keys %filter) { print "<OPTION>$table</OPTION>\n"; }
  print "</SELECT><BR>\n";
  print "Enter WBPapers and [optional] data (one each per line) : <BR>\n";
  print "<TEXTAREA NAME=\"already_curated\" ROWS=35 COLS=80 VALUE=\"\"></TEXTAREA><BR>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Enter Already Curated !\"><P>\n";
}
sub enterAlreadyCurated {
  &populateCurators();
  print "Curator $theHash{curator}\n";
  my ($var, $table) = &getHtmlVar($query, "fptype");
  print "using table $table<BR>\n";
  ($var, my $data) = &getHtmlVar($query, "already_curated");
  my (@lines) = split/\n/, $data;
  foreach my $line (@lines) {
    my ($wbp, $data) = ("", "checked");
    if ($line =~ m/^\s*?(\S+)\s+(.*)$/) {
      ($wbp, $data) = $line =~ m/^\s*?(\S+)\s+(.*)$/; }
    elsif ($line =~ m/^\s*?(\S+)$/) {
      ($wbp) = $line =~ m/^\s*?(\S+)$/; }
    $wbp = lc($wbp);
    my $paper = '';
    if ($wbp =~ m/wbpaper(\d+)/) { $paper = $1; }
    elsif ($wbp =~ m/^(\d+)$/) { $paper = $1; }
    else { print "<FONT COLOR=red>ERROR, line doesn't start with a WBPaper : $line</FONT>.<BR>\n"; next; }
    &postgresAlreadyCurated($table, $paper, $data);
  } # foreach my $line (@lines)
} # sub enterAlreadyCurated
sub postgresAlreadyCurated {
  my ($table, $paper, $data) = @_;
  ($data) = &filterForPg($data);			# replace ' with ''
  my $result = $dbh->prepare( "SELECT * FROM cfp_$table WHERE joinkey = '$paper' "); $result->execute;
  my $pgcommand = '';
  my @row = $result->fetchrow();
  if ( ($row[0]) && ($row[1]) ) { 1; 				# if already had data do nothing, already curated.  if someone later wants the new data to overwrite or append, put code here
  } else {
    if ($row[0]) { 						# row exists, but data is blank, so delete entry to create new
      $pgcommand = "DELETE FROM cfp_$table WHERE joinkey = '$paper'; ";
      $result = $dbh->do( $pgcommand );		
      print "PAP $paper REASON $data PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n"; }
    my $cur_id = $curators{std}{$theHash{curator}}; 
    $pgcommand = "INSERT INTO cfp_$table VALUES ('$paper', '$data', '$cur_id'); ";
    $result = $dbh->do( $pgcommand );		# insert into main cfp_ table
    print "PAP $paper REASON $data PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
    $pgcommand = "INSERT INTO cfp_${table}_hst VALUES ('$paper', '$data', '$cur_id'); ";
    $result = $dbh->do( $pgcommand );		# insert into _hst cfp_ table
    print "PAP $paper REASON $data PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
  }
} # sub postgresAlreadyCurated


sub populateInvalidPapers {
  my $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp; ");						# default
  $result->execute;
  while (my @row = $result->fetchrow) {
    $sortPapers{all}{$row[0]}++;
    if ($row[3] eq 'valid') { delete $sortPapers{inv_checked}{$row[0]}; } 
      else { $sortPapers{inv_checked}{$row[0]}++; }
  }
} # sub populateInvalidPapers

sub populatePaperAbstract {
  my $result = $dbh->prepare( "SELECT * FROM wpa_type WHERE wpa_type = '3' OR wpa_type = '4' ORDER BY wpa_timestamp; "); 
  $result->execute;
  my $key = '00010006';
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { $sortPapers{abs_checked}{$row[0]}++ ; } 
      else { delete $sortPapers{abs_checked}{$row[0]}; }
  }
} # sub populatePaperAbstract

sub populatePaperReview {
  my $result = $dbh->prepare( "SELECT * FROM wpa_type WHERE wpa_type = '2' ORDER BY wpa_timestamp; "); 
  $result->execute;
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { $sortPapers{rev_checked}{$row[0]}++; } 
      else { delete $sortPapers{rev_checked}{$row[0]}; }
  }
} # sub populatePaperReview

sub populatePaperWormbook {
  my $result = $dbh->prepare( "SELECT * FROM wpa_type WHERE wpa_type = '18' ORDER BY wpa_timestamp; "); 
  $result->execute;
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { $sortPapers{wor_checked}{$row[0]}++; } 
      else { delete $sortPapers{wor_checked}{$row[0]}; }
  }
} # sub populatePaperWormbook

sub populatePaperIgnore {
  my $result = $dbh->prepare( "SELECT * FROM wpa_ignore ORDER BY wpa_timestamp; "); 
  $result->execute;
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { $sortPapers{ign_checked}{$row[0]}++; } 
      else { delete $sortPapers{ign_checked}{$row[0]}; }
  }
} # sub populatePaperIgnore

sub populateCuratorNotFP {
  my %temp;
  my $result = $dbh->prepare( "SELECT * FROM cfp_curator ; "); $result->execute;
  while (my @row = $result->fetchrow) { $temp{$row[0]}++; }
  foreach my $pap (keys %{ $sortPapers{all} }) { unless ($temp{$pap}) { $sortPapers{cfp_checked}{$pap}++; } }
} # sub populateCuratorNotFP

sub populateAuthorFP {
  my $result = $dbh->prepare( "SELECT * FROM afp_lasttouched ; "); $result->execute;
  while (my @row = $result->fetchrow) { $sortPapers{afp_checked}{$row[0]}++; }
} # sub populateAuthorFP

sub populateTextpressoBody {
  my $page = get("http://textpresso-dev.caltech.edu/azurebrd/textpresso_has_body");
  my (@papers) = $page =~ m/WBPaper(\d+)/g;
  foreach (@papers) { $sortPapers{tfp_checked}{$_}++; }
} # sub populateTextpressoBody

sub populateAuthorEmailed {
  my $time = time;
  my $time7 = $time - 7 * 24 * 60 * 60;		# 7 days ago
  my $result = $dbh->prepare( "SELECT * FROM afp_passwd ; "); $result->execute;
  while (my @row = $result->fetchrow) { 
    if ( ($time7 < $row[1]) && ($row[1] < $time) ) { $sortPapers{ae7_checked}{$row[0]}++; }
    $sortPapers{aem_checked}{$row[0]}++; 
  } 
} # sub populateAuthorEmailed


sub getSortPapers {			# to display all papers in pages, 20 entries per page from $options{num_per_page}
  my $sort_type = shift;		# by default sort_papers

  &populateInvalidPapers();		# this must be first since CuratorNotFP uses ``all'' from it.
  &populateCuratorNotFP();		# these all populate %sortPapers for sorting
  &populateTextpressoBody();
  &populateAuthorFP();
  &populateAuthorEmailed();
  &populatePaperAbstract();
  &populatePaperReview();
  &populatePaperWormbook();
  &populatePaperIgnore();
  &populateCurators();

  $sortDisplayHash{"cfp_checked"}{"color"} = '<span style="color:black">C</span>';
  $sortDisplayHash{"tfp_checked"}{"color"} = '<span style="color:green">T</span>';
  $sortDisplayHash{"afp_checked"}{"color"} = '<span style="color:blue" >A</span>';
  $sortDisplayHash{"aem_checked"}{"color"} = '<span style="color:cyan" >A</span>';
  $sortDisplayHash{"ae7_checked"}{"color"} = '<span style="color:red"  >A</span>';
  $sortDisplayHash{"abs_checked"}{"color"} = '<span style="color:red"  >M</span>';
  $sortDisplayHash{"rev_checked"}{"color"} = '<span style="color:red"  >R</span>';
  $sortDisplayHash{"wor_checked"}{"color"} = '<span style="color:red"  >W</span>';
  $sortDisplayHash{"ign_checked"}{"color"} = '<span style="color:red"  >I</span>';
  $sortDisplayHash{"inv_checked"}{"color"} = '<span style="color:red"  >N</span>';
  $sortDisplayHash{"cfp_checked"}{"desc"} = 'Curator has NOT already first pass curated this <span style="color:#A0A0A0">(checked shows only these)</span>';
  $sortDisplayHash{"tfp_checked"}{"desc"} = 'Textpresso has body text <span style="color:#A0A0A0">(checked shows only these)</span>';
  $sortDisplayHash{"afp_checked"}{"desc"} = 'Author has first passed <span style="color:#A0A0A0">(checked shows only these)</span>';
  $sortDisplayHash{"aem_checked"}{"desc"} = 'Author has been emailed to first pass <span style="color:#A0A0A0">(checked shows only these)</span>';
  $sortDisplayHash{"ae7_checked"}{"desc"} = 'Author has been emailed to first pass in the past 7 days <span style="color:#A0A0A0">(unchecked default excludes)</span>';
  $sortDisplayHash{"abs_checked"}{"desc"} = 'Meeting Abstract or Gazette Abstract <span style="color:#A0A0A0">(unchecked default excludes)</span>';
  $sortDisplayHash{"rev_checked"}{"desc"} = 'Review <span style="color:#A0A0A0">(unchecked default excludes)</span>';
  $sortDisplayHash{"wor_checked"}{"desc"} = 'WormBook <span style="color:#A0A0A0">(unchecked default excludes)</span>';
  $sortDisplayHash{"ign_checked"}{"desc"} = 'Ignore functional annotation or non worm <span style="color:#A0A0A0">(unchecked default excludes)</span>';
  $sortDisplayHash{"inv_checked"}{"desc"} = 'iNvalid paper <span style="color:#A0A0A0">(unchecked default excludes)</span>';
  $sortDisplayHash{"cfp_checked"}{"checked"} = '';
  $sortDisplayHash{"tfp_checked"}{"checked"} = '';
  $sortDisplayHash{"afp_checked"}{"checked"} = '';
  $sortDisplayHash{"aem_checked"}{"checked"} = '';
  $sortDisplayHash{"ae7_checked"}{"checked"} = '';
  $sortDisplayHash{"abs_checked"}{"checked"} = '';
  $sortDisplayHash{"rev_checked"}{"checked"} = '';
  $sortDisplayHash{"wor_checked"}{"checked"} = '';
  $sortDisplayHash{"ign_checked"}{"checked"} = '';
  $sortDisplayHash{"inv_checked"}{"checked"} = '';

  my $oop;
  foreach my $type (keys %sortDisplayHash) { ($oop, $sortDisplayHash{$type}{checked}) = &getHtmlVar($query, $type); }	# get form values
  if ($sort_type eq "not_curated_plus_textpresso") { 						# if only want those, set them
    $sortDisplayHash{"afp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"cfp_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"tfp_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"ae7_checked"}{"checked"} = ''; 
    $sortDisplayHash{"abs_checked"}{"checked"} = ''; 
    $sortDisplayHash{"wor_checked"}{"checked"} = '';
    $sortDisplayHash{"rev_checked"}{"checked"} = ''; 
    $sortDisplayHash{"ign_checked"}{"checked"} = ''; 
    $sortDisplayHash{"inv_checked"}{"checked"} = ''; }  
  elsif ($sort_type eq "not_curated_plus_author_plus_textpresso") {				# if only want those, set them
    $sortDisplayHash{"afp_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"cfp_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"tfp_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"ae7_checked"}{"checked"} = ''; 
    $sortDisplayHash{"abs_checked"}{"checked"} = ''; 
    $sortDisplayHash{"wor_checked"}{"checked"} = '';
    $sortDisplayHash{"rev_checked"}{"checked"} = ''; 
    $sortDisplayHash{"ign_checked"}{"checked"} = ''; 
    $sortDisplayHash{"inv_checked"}{"checked"} = ''; }  
  elsif ($sort_type eq "all_papers") {								# if only want those, set them
    $sortDisplayHash{"afp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"cfp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"tfp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"ae7_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"abs_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"wor_checked"}{"checked"} = 'checked';
    $sortDisplayHash{"rev_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"ign_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"inv_checked"}{"checked"} = 'checked'; }  
  elsif ($sort_type eq "all_minus_abstracts") {								# if only want those, set them
    $sortDisplayHash{"afp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"cfp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"tfp_checked"}{"checked"} = ''; 
    $sortDisplayHash{"ae7_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"abs_checked"}{"checked"} = ''; 
    $sortDisplayHash{"wor_checked"}{"checked"} = 'checked';
    $sortDisplayHash{"rev_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"ign_checked"}{"checked"} = 'checked'; 
    $sortDisplayHash{"inv_checked"}{"checked"} = 'checked'; }  

  ($oop, my $specific_paper) = &getHtmlVar($query, 'specific_paper');				# if user wants a specific paper
  ($specific_paper) = &padZeros($specific_paper);						# pad zeros as needed
  print "Specific Paper : <INPUT NAME=\"specific_paper\" VALUE=\"$specific_paper\">\n";		# take in input
  print "<INPUT TYPE=submit NAME=action VALUE=\"Specific Paper !\"><br /><br />\n";		# get just that paper
  print "<INPUT TYPE=submit NAME=action VALUE=\"Not Curated plus Textpresso !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Not Curated plus Author plus Textpresso !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"All Papers !\">\n";		# get just that paper
  print "<INPUT TYPE=submit NAME=action VALUE=\"All Minus Abstracts !\"><br /><br />\n";		# get just that paper

  print "<table>\n";
  foreach my $type (keys %sortDisplayHash) {							# show table of checkboxes, key information, explanation
    print "<tr><td><input name=\"$type\" type=checkbox value=\"checked\" $sortDisplayHash{$type}{checked}></td>";
    print "<td class=\"padded\" align=\"center\">$sortDisplayHash{$type}{color}</td><td class=\"padded\">$sortDisplayHash{$type}{desc}</td></tr>\n";
  }
  print "</table>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Sort Papers !\"><br />\n";			# click to re-sort by new parameters or page


  my @wpas; my $result;		# the joinkeys, sorted
  foreach my $type (keys %sortDisplayHash) {
    if ( ($type eq 'inv_checked') || ($type eq 'ign_checked') || ($type eq 'wor_checked') || ($type eq 'rev_checked') || ($type eq 'abs_checked') ) {
          # if checked show them, otherwise exclude them by deleting from master list
        unless ($sortDisplayHash{$type}{checked}) { foreach my $pap (keys %{ $sortPapers{$type} }) { delete $sortPapers{all}{$pap}; } } }
      elsif ($type eq 'ae7_checked') {
        next if ( ($sortDisplayHash{aem_checked}{checked}) || ($sortDisplayHash{afp_checked}{checked}) ) ;	
        unless ($sortDisplayHash{$type}{checked}) { foreach my $pap (keys %{ $sortPapers{$type} }) { delete $sortPapers{all}{$pap}; } } }
      else {
        if ($sortDisplayHash{$type}{checked}) { 					# if checked
          foreach my $pap (keys %{ $sortPapers{all} }) { 				# loop through all papers
            unless ($sortPapers{$type}{$pap}) { delete $sortPapers{all}{$pap}; } } } }	# remove from master list if not in required field
  }

  foreach my $paper (sort keys %{ $sortPapers{all} }) { unshift @wpas, $paper;  }	# unshift all the papers into an array in descending order
  if ($sort_type eq 'specific_paper') { @wpas = ( $specific_paper ); }			# if looking for only a specific paper, show only that one

  my $full_count = scalar(@wpas);

  ($oop, my $current_page) = &getHtmlVar($query, 'sort_page_number');			# get current page
  unless ($current_page) { $current_page = 1; }						# default to page 1
  my $skip_num = ($current_page - 1) * $options{num_per_page};				# skip this many entries based on page
  for (1 .. $skip_num) { shift @wpas; }							# skip them
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";
  my $pages = $full_count/$options{num_per_page}; $pages = ceil($pages);		# ceil is a POSIX function to round up
  print "There are $full_count WBPapers in $pages pages.  You are in page ${current_page}.<BR>\n";
  print "Select your Page number : <SELECT NAME=\"sort_page_number\" SIZE=1>\n";	# page selector
  for (1 .. $pages) { 									# for each of the pages
    print "<OPTION";
    if ($_ eq $current_page) { print " SELECTED"; }					# default select the current page
    print ">$_</OPTION>\n"; }
  print "</SELECT><BR>\n";

# got rid of this, haven't incorporated into new code.  2009 04 22
#   ($oop, my $sort_ordering) = &getHtmlVar($query, 'sort_ordering');
#   my $s_number = ''; my $s_date = ''; my $s_journal = '';
#   if ($sort_ordering) { 
#       if ($sort_ordering eq 'number') { $s_number = 'CHECKED'; }
#       elsif ($sort_ordering eq 'date') { $s_date = 'CHECKED'; }
#       else { $s_number = 'CHECKED'; $s_date = ''; $s_journal = ''; } }
#     else { $s_number = 'CHECKED'; }
#   print "All papers only : <INPUT TYPE=submit NAME=action VALUE=\"by Curator !\"><P>\n";
#   print "<INPUT NAME=\"sort_ordering\" TYPE=\"radio\" VALUE=\"number\" $s_number>Sort by Number<BR>\n";
#   print "<INPUT NAME=\"sort_ordering\" TYPE=\"radio\" VALUE=\"date\" $s_date>Sort by Date<BR>\n";
#   print "<P>\n";


  print "<TABLE border=0><TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Key</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>Journal</TD><TD ALIGN=CENTER>Hardcopy</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>Title</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curator</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
  for (1 .. $options{num_per_page}) { my $joinkey = shift @wpas; if ($joinkey) { &sortLink($joinkey); } }		# show paper data and link to it
  print "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Key</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>Journal</TD><TD ALIGN=CENTER>Hardcopy</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>Title</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curator</TD><TD ALIGN=CENTER>curate</TD></TR></TABLE>\n";
  
# old buttons, get rid of later  2009 04 22
#   print "<INPUT TYPE=submit NAME=action VALUE=\"All Papers !\">\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=\"No Meetings !\">\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=\"Not Curated !\">\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=\"Not Curated plus Textpresso !\">\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=\"CGC !\">\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=\"C elegans !\"><BR>\n";
#   print "Specific Paper : <INPUT NAME=\"specific_paper\" >\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=\"Specific Paper !\">\n";
#   print "<P>\n";
  print "</FORM>";
#   return $current_page;
} # sub getSortPapers

sub sortLink {			# show paper data and link it
  my $joinkey = shift;
  my $temp_curator = $theHash{curator}; my $cur_id = $curators{std}{$temp_curator}; $cur_id =~ s/two//; $temp_curator =~ s/\s+/+/g;
#   my $check_out = "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/curation.cgi?curator_name=$temp_curator&action=Curate+%21&wbpaper_number=$joinkey>curate</A>";
  my $check_out .= "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/curator_first_pass.cgi?html_value_curator=$cur_id&action=Query&html_value_paper=$joinkey>curate</A>";	# link to new curator_first_pass.cgi  2009 04 06
#   my $result = $conn->exec( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );	# only one value per joinkey, but timestamp in case changed later
  my $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey' ORDER BY cfp_timestamp DESC" );	# only one value per joinkey, but timestamp in case changed later
  $result->execute;
  my @row = $result->fetchrow; my $last_curator = ''; if ($row[1]) { $last_curator = $curators{two}{$row[1]}; }		# this will work when cur_curator has joinkeys as wbpapers
#   $result = $conn->exec( "SELECT * FROM wpa_checked_out WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_checked_out WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $checked_out = ''; if ($row[1]) { $checked_out = $curators{two}{$row[1]}; }
#   $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $title = ''; if ($row[1]) { $title = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $journal = ''; if ($row[1]) { $journal = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_hardcopy WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_hardcopy WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp DESC" );
  $result->execute;
  @row = $result->fetchrow; my $hardcopy = 'NO'; if ($row[1]) { $hardcopy = $row[1]; }
#   $result = $conn->exec( "SELECT * FROM wpa_identifier WHERE joinkey = '$joinkey' ORDER BY wpa_identifier, wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE joinkey = '$joinkey' ORDER BY wpa_identifier, wpa_timestamp DESC" );
  $result->execute;
  my %wpa_id = (); my @wpa_id;			# for a joinkey get all ids sorted by id and descending timestamp (to get latest first, so only get latest to check validity)
  while (my @row = $result->fetchrow) { 	# for each value, check if already gotten, if new check if valid, if valid put in hash
    unless ($wpa_id{$row[1]}) { $wpa_id{$row[1]}++; if ($row[3] eq 'valid') { push @wpa_id, $row[1]; } } }
  my $identifiers = join"<BR>", @wpa_id;
#   $result = $conn->exec( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_electronic_path_type, wpa_timestamp DESC" );
  $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ORDER BY wpa_electronic_path_type, wpa_timestamp DESC" );
  $result->execute;
  my %wpa_path = (); my @wpa_path;			# for a joinkey get all ids sorted by id and descending timestamp (to get latest first, so only get latest to check validity)
  while (my @row = $result->fetchrow) { 	# for each value, check if already gotten, if new check if valid, if valid put in hash
    unless ($wpa_path{$row[1]}) { $wpa_path{$row[1]}++; if ($row[3] eq 'valid') { 
      my ($pdf) = $row[1] =~ m/\/([^\/]*)$/; my $pdf_link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf; $pdf = "<A HREF=\"$pdf_link\">$pdf</A>"; push @wpa_path, $pdf } } }

  my $pdfs = join"<BR>", @wpa_path;
  my $textpresso_color = 'black'; unless ($sortPapers{tfp_checked}{$joinkey}) { $textpresso_color = 'grey'; }
  my $curationkey = '';							# key of which sorting values apply to that paper
  foreach my $type (keys %sortDisplayHash) {				# for each of those possible keys
    if ($sortPapers{$type}{$joinkey}) {					# if that paper belons
      next if ( ($type eq 'aem_checked') && ( ($sortPapers{ae7_checked}{$joinkey}) || ($sortPapers{afp_checked}{$joinkey}) ) ) ;	# skip if overridden
      next if ( ($type eq 'ae7_checked') && ($sortPapers{afp_checked}{$joinkey}) ) ;							# skip if overridden
      $curationkey .= $sortDisplayHash{$type}{color}; } }		# add to the key
  unless ($sortPapers{tfp_checked}{$joinkey}) { print "<FONT COLOR='grey'>"; }
  print "<TR><TD><FONT COLOR=$textpresso_color><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">$joinkey</A></FONT></TD><TD>$curationkey</TD><TD><FONT COLOR=$textpresso_color>$identifiers</FONT></TD><TD><FONT COLOR=$textpresso_color>$journal</FONT></TD><TD><FONT COLOR=$textpresso_color>$hardcopy</FONT></TD><TD><FONT COLOR=$textpresso_color>$pdfs</FONT></TD><TD><FONT COLOR=$textpresso_color>$title</FONT></TD><TD><FONT COLOR=$textpresso_color>$checked_out</FONT></TD><TD><FONT COLOR=$textpresso_color>$last_curator</FONT></TD><TD><FONT COLOR=$textpresso_color>$check_out</FONT></TD></TR>\n"; 
  unless ($sortPapers{tfp_checked}{$joinkey}) { print "</FONT>"; }
} # sub sortLink

### SORT SECTION ###



### NEW PAPERS SECTION ###

sub newPapers {
  &populateCurators();
  if ( $theHash{curator} =~ m/Kimberly/ ) { &showPMIDConfirmation(); }	# for kimberly on top  2009 04 19
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$theHash{curator}\">\n"; 								# curator
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR><TD>Enter the PMID numbers,<BR>one per line.  e.g. :<BR>\n";
  print "16061202<BR>16055504<BR>16055082<BR>16054097<BR>16054081<BR>16054064</TD>\n";
  print "<TD><TEXTAREA NAME=\"pmids\" ROWS=40 COLS=60 VALUE=\"\"></TEXTAREA></TD>\n";
  print "<TD ALIGN=CENTER>Not for first-pass curation<BR>(functional annotation comment) : <INPUT NAME=\"not_first_pass\" TYPE=CHECKBOX VALUE=\"functional_annotation\"><br />Primary articles : <input name=\"primary\" type=\"checkbox\" value=\"primary\"><BR><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Enter PMIDs !\"></TD></TR>\n";
  print "</TABLE>\n";
  if ( $theHash{curator} !~ m/Kimberly/ ) { &showPMIDConfirmation(); }	# for not kimberly bewow  2009 04 19
  &getPossiblePapers();
} # sub newPapers

sub abstract_text {
  print "Content-type: text/plain\n\n"; 
  my $directory = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads';
  my @read_pmids = <$directory/xml/*>;
  foreach my $infile (@read_pmids) {
    $/ = undef;
    open (IN, "<$infile") or die "Cannot open $infile : $!";
    my $file = <IN>;
    close (IN) or die "Cannot open $infile : $!";
    my ($abstract) = $file =~ /\<AbstractText\>(.+?)\<\/AbstractText\>/i;
    my ($pmid) = $infile =~ m/(\d+)$/;
    print "$pmid\t$abstract\n";
  } 
  $/ = "\n";
}

sub confirmAbstracts {
  &populateCurators();
  my $rejected_file = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/rejected_pmids';
  my $directory = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads';
  my ($oop, $count) = &getHtmlVar($query, 'count');
  for my $i (0 .. $count - 1) {
    ($oop, my $choice) = &getHtmlVar($query, "approve_reject_$i");
    unless ($choice) { $choice = 'ignore'; }
    ($oop, my $pmid) = &getHtmlVar($query, "pmid_$i");
    print "$pmid $choice<BR>\n";
    if ($choice eq 'reject') { 
        open (OUT, ">>$rejected_file") or die "Cannot append to $rejected_file : $!";
        print OUT "$pmid\n";
        close (OUT) or die "Cannot close $rejected_file : $!"; 
        `mv ${directory}/xml/$pmid ${directory}/done/`; }
      elsif ($choice eq 'approve') {
        print "Processing $pmid.<BR><BR>\n";
        my ($link_text) = &processLocal($pmid, $curators{std}{$theHash{curator}}, '');
        `mv ${directory}/xml/$pmid ${directory}/done/`; 
    }
  } # for (0 .. $count)
} # sub confirmAbstracts

sub showPMIDConfirmation {
  my $directory = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads';
  my $rejected_file = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/rejected_pmids';
  my @read_pmids = <$directory/xml/*>;
#   print "<FORM METHOD=POST ACTION=http://tazendra.caltech.edu/~postgres/cgi-bin/pmid_abstracts.cgi>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Confirm Abstracts !\">\n";
  print "<TABLE border=1>\n";
  print "<TR><TD>pmid</TD><td>title</td><td>authors</td><TD>abstract</TD><TD>type</TD><TD>journal</TD><TD>Approve</TD><td>primary</td><TD>Reject</TD></TR>\n";
  my $count = 0;
  foreach my $infile (@read_pmids) {
    $/ = undef;
    open (IN, "<$infile") or die "Cannot open $infile : $!";
    my $file = <IN>;
    close (IN) or die "Cannot open $infile : $!";
    my ($abstract) = $file =~ /\<AbstractText\>(.+?)\<\/AbstractText\>/i;
    my ($type) = $file =~ /\<PublicationType\>(.+?)\<\/PublicationType\>/i;
    my ($journal) = $file =~ /\<MedlineTA\>(.+?)\<\/MedlineTA\>/i;	# show Journal to reject 
    my ($title) = $file =~ /\<ArticleTitle\>(.+?)\<\/ArticleTitle\>/i;	# show article Title to reject 
    my @authors = $file =~ /\<Author.*?\>(.+?)\<\/Author\>/isg;
    my $authors = "";
    foreach (@authors){
      my ($lastname, $initials) = $_ =~ /\<LastName\>(.+?)\<\/LastName\>.+\<Initials\>(.+?)\<\/Initials\>/is;
      $authors .= $lastname . " " . $initials . ', '; }
    $authors =~ s/\W+$//;
    my ($pmid) = $infile =~ m/(\d+)$/;
    my ($doi) = $file =~ /\<ArticleId IdType=\"doi\"\>(.+?)\<\/ArticleId\>/i;
    my $input_buttons = "<TD><INPUT TYPE=RADIO NAME=approve_reject_$count VALUE=approve></TD><td><input type=checkbox name=\"primary_$count\" checked=\"checked\" value=\"primary\"></td>\n<TD><INPUT TYPE=RADIO NAME=approve_reject_$count VALUE=reject></TD>";
    if ($journal eq 'Genetics') { 
        print "<TR bgcolor='$red'>\n"; 					# show Genetics papers in red	2009 07 21
        if ($doi) { $journal .= "<br />$doi"; } 			# show DOI			2009 07 23
          else { $input_buttons = "<td>&nbsp;</td><td><input type=checkbox name=\"primary_$count\" checked=\"checked\" value=\"primary\"></td><td>&nbsp;</td>"; } } # don't show approve / reject	2009 07 23
      else { print "<TR>\n"; }
    print "<TD>$pmid</TD><td>$title</td><td>$authors</td><td>$abstract</td>";
    print "<TD>$type</TD>";
    print "<TD>$journal</TD>";
    print "<INPUT TYPE=HIDDEN NAME=pmid_$count VALUE=$pmid>\n";
    print "$input_buttons\n";
    print "</TR>\n";
    $count++;
  } # foreach my $infile (@read_pmids)
  print "</TABLE>\n";
  print "<INPUT TYPE=HIDDEN NAME=count VALUE=$count>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Confirm Abstracts !\">\n";
#   print "<INPUT TYPE=submit NAME=action VALUE=txt>\n";
  print "</FORM>\n";

} # sub showPMIDConfirmation

sub enterPmids {
  &populateCurators();
  print "EVIDENCE : $curators{std}{$theHash{curator}}<BR>\n";
  my ($oop, $pmids) = &getHtmlVar($query, 'pmids');
  my $not_first_pass = '';				# flag to enter stuff into wpa_checked_out, cur_curator, cur_comment
  ($oop, $not_first_pass) = &getHtmlVar($query, 'not_first_pass');
  my (@pmids) = $pmids =~ m/(\d+)/g;
  my $pmid_list = join"\t", @pmids;
  print "Processing $pmid_list.<BR><BR>\n";
  my ($link_text) = &processPubmed($pmid_list, $curators{std}{$theHash{curator}}, $not_first_pass);
  print "$link_text\n";
} # sub enterPmids


sub mergeNewPaper {	# merge an incoming paper with an existing wbpaper
  my $endnote_file = &readManualEndnote();						# get manual file of possible matches
  my ($entry, $flag, $line, $new_endnote_file) = &getSpecificEntry($endnote_file);	# get specific entry from that file and a copy of the file minus that entry
  my ($oop, $joinkey) = &getHtmlVar($query, 'number_merge');				# get the joinkey of the wbpaper to be merged
  &populateCurators(); my $two_number = $curators{std}{$theHash{curator}};		# get the two number of the curator for evidence
  &processForm($two_number, $joinkey, $flag, 'merge', $line);				# use wpa_match.pm to merge the entry
  print "MERGE $joinkey $entry<BR>\n";
  &updateManualEndnote($new_endnote_file);						# update the flatfile of possible matches to check manually
  &newPapers();										# display the new papers page again to merge another
} # sub mergeNewPaper

sub createNewPaper {	# create an incoming paper as a new wbpaper
  my ($endnote_file) = &readManualEndnote();
  my ($entry, $flag, $line, $new_endnote_file) = &getSpecificEntry($endnote_file);
  &populateCurators(); my $two_number = $curators{std}{$theHash{curator}};
  &processForm($two_number, 'NULL', $flag, 'create', $line);				# use wpa_match.pm to create the entry
  print "CREATE $entry<BR>\n";
  &updateManualEndnote($new_endnote_file);
  &newPapers(); 
} # sub createNewPaper

sub getSpecificEntry {	# depending on which entry a curator clicked, get that entry from the flatfile, and get the flatfile minus that entry to rewrite it
  my $endnote_file = shift; my $new_endnote_file;					# full file, empty copy to have full file minus entry
  my @entries = split/\n/, $endnote_file;
  my ($oop, $entry_count) = &getHtmlVar($query, 'entry_count');				# get the entry count to be changed
  unless ($entry_count) { $entry_count = 0; }						# init to zeroth value if necessary
  my $entry = $entries[$entry_count];							# get entry
  foreach my $each_entry (@entries) { unless ($each_entry eq $entry) { $new_endnote_file .= "$each_entry\n"; } }	# append to flatfile minus entry
  my ($match_type, $matches, $flag, $flag_number, $authors, $title, $journal, $volume, $pages, $year, $abstract, $genes, $type, $entered_by, $entered_when) = split/\t/, $entry;
  my $line = "$flag_number\t$authors\t$title\t$journal\t$volume\t$pages\t$year\t$abstract\t$genes\t$type";
  return ($entry, $flag, $line, $new_endnote_file);					# return values
} # sub getSpecificEntry

sub updateManualEndnote {	# rewrite manual-check endnote file
  my $new_endnote_file = shift; 
#   my $infile = '/home/postgres/work/pgpopulation/wpa_new_wbpaper_tables/perl_wpa_match/manual_check_file.endnote';
  my $infile = '/home/postgres/work/pgpopulation/wpa_papers/wpa_new_wbpaper_tables/perl_wpa_match/manual_check_file.endnote';
  open (IN, ">$infile") or die "Cannot recreate $infile : $!";
  print IN $new_endnote_file;
  close (IN) or die "Cannot close $infile : $!"; 
} # sub updateManualEndnote

sub readManualEndnote {		# read manual-check endnote file
#   my $infile = '/home/postgres/work/pgpopulation/wpa_new_wbpaper_tables/perl_wpa_match/manual_check_file.endnote';
  my $infile = '/home/postgres/work/pgpopulation/wpa_papers/wpa_new_wbpaper_tables/perl_wpa_match/manual_check_file.endnote';
  $/ = undef; open (IN, "<$infile") or die "Cannot open $infile : $!";
  my $endnote_file = <IN>;
  close (IN) or die "Cannot close $infile : $!"; $/ = '';
  return $endnote_file;
} # sub readManualEndnote

sub getPossiblePapers {		# form display of each manual-check entry
  my ($endnote_file) = &readManualEndnote();		# get all entries from file
  my @entries = split/\n/, $endnote_file;
  if ($entries[0]) { print "<CENTER><P><BR><P><FONT COLOR='red'>DON'T USE ANYTHING BELOW HERE UNLESS YOU'RE DANIEL</FONT><BR></CENTER>\n"; }		# show this if there are papers here below  2006 11 08
  print "<TABLE border=1 cellspacing=2>\n";
  my $entry_count = 0;					# number entries to know which one to merge / create
  foreach my $entry (@entries) {
    my ($match_type, $matches, $flag, $flag_number, $authors, $title, $journal, $volume, $pages, $year, $abstract, $genes, $type, $entered_by, $entered_when) = split/\t/, $entry;
    print "<TR bgcolor='$blue'><TD>match_type</TD><TD>$match_type</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>matches</TD><TD>";
    my @matches;
    if ($matches =~ m/\d+/) { (@matches) = $matches =~ m/(\d+)/g; } else { push @matches, $matches; }							# grab all possible joinkeys
    foreach my $match (@matches) { 
      print "</FORM><FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";			# new form for that number
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$theHash{curator}\">\n"; 								# curator
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"entry_count\" VALUE=\"$entry_count\">\n"; 									# number
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"number_merge\" VALUE=\"$match\">\n";										# joinkey
      my $curator = $theHash{curator}; $curator =~ s/\s/+/g;
      print "<A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?curator_name=$curator&action=Number+%21&number=$match TARGET=NEW>$match</A>\n";	# link
      print "<INPUT TYPE=submit NAME=action VALUE=\"Merge with this Paper !\"><BR>\n";									# merge button
    } # foreach my $match (@matches)
    print "</FORM><FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$theHash{curator}\">\n"; 								# curator
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"entry_count\" VALUE=\"$entry_count\">\n"; 									# number
    print "<TR bgcolor='$blue'><TD></TD><TD><INPUT TYPE=submit NAME=action VALUE=\"Create New Paper !\"></TD></TR>\n";					# create button
    print "<TR bgcolor='$blue'><TD>pmid/cgc</TD><TD>$flag</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>pmid/cgc number</TD><TD>$flag_number</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>authors</TD><TD>$authors</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>title</TD><TD>$title</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>journal</TD><TD>$journal</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>volume</TD><TD>$volume</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>pages</TD><TD>$pages</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>year</TD><TD>$year</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>abstract</TD><TD>$abstract</TD></TR>\n";
    if ($flag eq 'cgc') { print "<TR bgcolor='$blue'><TD>genes</TD><TD>$genes</TD></TR>\n"; }		# only cgc has genes
    if ($flag eq 'pmid') { print "<TR bgcolor='$blue'><TD>type</TD><TD>$type</TD></TR>\n"; }		# only pmid has type
    print "<TR bgcolor='$blue'><TD>entered_by</TD><TD>$entered_by</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD>entered_when</TD><TD>$entered_when</TD></TR>\n";
    print "<TR><TD></TD><TD><BR></TD></TR>\n";
    $entry_count++;					# up the number count for next entry
  } # foreach my $entry (@entries) 
  print "</TABLE>\n";
} # sub getPossiblePapers

### NEW PAPERS SECTION ###



### PICK SECTION ###

sub pickExtra {
  my ($oop, $pg_table) = &getHtmlVar($query, 'extra');
  print "PGTABLE $pg_table PG<BR>\n";
  ($oop, my $number) = &getHtmlVar($query, 'number');
  unless ($number) { $number = 1; }	# sometimes no number or zero would cause a serverlog error on next line
  print "NUMBER : $number\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Update Info !\"><P>\n";
#   print "my \$result = \$conn->exec( \"SELECT * FROM $pg_table WHERE $pg_table = '$number'; \"); <BR>\n";
  print "my \$result = \$dbh->prepare( \"SELECT * FROM $pg_table WHERE $pg_table = '$number'; \"); <BR>\n";
#   my $result = $conn->exec( "SELECT * FROM $pg_table WHERE $pg_table = '$number'; ");
  my $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE $pg_table = '$number'; ");
  $result->execute;
  my @row = $result->fetchrow;
  if ($row[0]) { &displayOneDataFromKey($number); }
} # sub pickExtra

sub pickNumber {
  my ($oop, $number) = &getHtmlVar($query, 'number');
  unless ($number) { $number = 1; }	# sometimes no number or zero would cause a serverlog error on next line
  if ($number =~ m/^WBPaper/i) { $number =~ s/^WBPaper//i; }
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"number\" VALUE=\"$number\">\n"; 		# pass number in case want to toggle to Show Valid or Show History
  print "NUMBER : $number\n";
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }
  my $result = $dbh->prepare( "SELECT * FROM wpa WHERE wpa = '$number'; ");
  $result->execute;
  my @row = $result->fetchrow;
  if ($row[0]) { 
    print "<INPUT TYPE=submit NAME=action VALUE=\"Update Info !\">\n";
    my ($joinkey) = &padZeros($number);		# add link to check out for first-pass  2005 09 20
#     my $temp_curator = $theHash{curator}; $temp_curator =~ s/\s+/+/g;
#     print "&nbsp; &nbsp; first-pass <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/curation.cgi?curator_name=$temp_curator&action=Curate+%21&wbpaper_number=$joinkey>curate</A><P>";
    &populateCurators();
    my $temp_curator = $theHash{curator}; my $cur_id = $curators{std}{$temp_curator}; $cur_id =~ s/two//; $temp_curator =~ s/\s+/+/g;
    print "&nbsp; &nbsp; first-pass <A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/curator_first_pass.cgi?html_value_curator=$cur_id&action=Query&html_value_paper=$joinkey>curate</A><P>";	# link to new curator_first_pass.cgi  2009 04 06
    &displayOneDataFromKey($number); 
    print "<INPUT TYPE=submit NAME=action VALUE=\"Update Info !\"><P>\n"; }
  else {
    print "There is no exact match for WBPaper $number<BR>\n"; 
    my %xref_type;
#     my $result = $conn->exec( "SELECT * FROM wpa_identifier; "); 
    my $result = $dbh->prepare( "SELECT * FROM wpa_identifier; "); 
    $result->execute;
    my %xref;
    while (my @row = $result->fetchrow) {
      $row[0] =~ s/\D//g;
      $xref{full}{$row[1]}{$row[0]}++;
      my ($xref_type) = $row[1] =~ m/(^\D+)/;
      unless ($xref_type) { if ($row[1] =~ m/wormbook/) { $xref_type = 'wormbook'; } }
      $xref_type{$xref_type}++;
      $row[1] =~ s/\D//g;
      $xref{num}{$row[1]}{$row[0]}++;
    } # while (my @row = $result->fetchrow)
    my ($number_type) = $number =~ m/^(\D+)/;
# print "NUM $number_type<BR>\n";
    if ($number_type == '') { print "You have not chosen a paper type.<BR>\n"; # try to find matches by number if there is no paper type  2008 04 16
      $number =~ s/\D+//g;
      foreach my $joinkey ( sort keys %{ $xref{num}{$number} } ) {
        print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">wbpaper id : $joinkey</A><BR>\n"; } }
    elsif ($xref_type{$number_type}) { 	# matches type e.g. cgc
      print "There are $xref_type{$number_type} wpa_xref that match the paper type '$number_type'.<BR>\n";
foreach my $
      if ($xref{full}{$number}) {
        foreach my $joinkey ( sort keys %{ $xref{full}{$number} } ) {
          print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">wbpaper id : $joinkey</A><BR>\n"; } } }
    else {				# doesn't match type
      $number =~ s/\D+//g;
      foreach my $joinkey ( sort keys %{ $xref{num}{$number} } ) {
        print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$theHash{curator}\">wbpaper id : $joinkey</A><BR>\n"; } }
  }
} # sub pickNumber

sub pickAuthor {
  my ($oop, $author) = &getHtmlVar($query, 'author');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %authors;
  my %matches;
  print "AUTHOR : $author<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_author_index WHERE wpa_author_index = '$author' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE wpa_author_index = '$author' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $authors{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_author_index WHERE wpa_author_index ~ '$author' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE wpa_author_index ~ '$author' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $authors{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  foreach my $author_id (sort keys %authors) {
#     my $result = $conn->exec( "SELECT * FROM wpa_author WHERE wpa_author = '$author_id' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE wpa_author = '$author_id' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } # foreach my $author_id (sort keys %authors)

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $author.<BR>\n"; }
  else {
    if (scalar(keys %matches) == 1) { print "There is " . scalar(keys %matches) . " $exact_or_sub match : <BR>\n"; }
    else {
      print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
      print "<TABLE border=0><TR><TD>WBPaperID</TD><TD>Author ID</TD><TD>Author Name</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; }
    foreach my $number (sort keys %matches) {
#       my $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      my @row = $result->fetchrow; my $title = $row[1];
#       $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      @row = $result->fetchrow; my $journal = $row[1];
      unless ($journal) { $journal = ''; }
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&curator_name=$theHash{curator}&action=Number+%21\">$number</A></TD><TD>$matches{$number}</TD><TD>$authors{ $matches{$number} } </TD><TD>$title</TD><TD>$journal</TD></TR>\n";
     }
  }
} # sub pickAuthor

sub pickTitle {
  my ($oop, $title) = &getHtmlVar($query, 'title');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "TITLE : $title<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_title WHERE wpa_title = '$title' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE wpa_title = '$title' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_title WHERE wpa_title ~ '$title' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE wpa_title ~ '$title' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $title.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    foreach my $number (sort keys %matches) { 
      print "Matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&action=Number+%21&curator_name=$theHash{curator}\">wbpaper id $number -> title : $matches{$number}</A><BR>\n";
     }
  }
} # sub pickTitle

sub pickJournal {
  my ($oop, $journal) = &getHtmlVar($query, 'journal');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "JOURNAL : $journal<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_journal WHERE wpa_journal = '$journal' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE wpa_journal = '$journal' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_journal WHERE wpa_journal ~ '$journal' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE wpa_journal ~ '$journal' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $journal.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    print "<TABLE border=0><TR><TD>WBPaperID</TD><TD>Journal</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; 
    foreach my $number (sort keys %matches) {
#       my $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      my @row = $result->fetchrow; my $title = $row[1];
#       $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      @row = $result->fetchrow; my $journal = $row[1];
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&curator_name=$theHash{curator}&action=Number+%21\">$number</A></TD><TD>$matches{$number}</TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickJournal

sub pickPages {
  my ($oop, $pages) = &getHtmlVar($query, 'pages');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "PAGES : $pages<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_pages WHERE wpa_pages = '$pages' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_pages WHERE wpa_pages = '$pages' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_pages WHERE wpa_pages ~ '$pages' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_pages WHERE wpa_pages ~ '$pages' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $pages.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    print "<TABLE border=0><TR><TD>WBPaperID</TD><TD>Pages</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; 
    foreach my $number (sort keys %matches) {
#       my $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      my @row = $result->fetchrow; my $title = $row[1];
#       $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      @row = $result->fetchrow; my $journal = $row[1];
      unless ($journal) { $journal = ''; } unless ($title) { $title = ''; }
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&curator_name=$theHash{curator}&action=Number+%21\">$number</A></TD><TD>$matches{$number}</TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickPages

sub pickVolume {
  my ($oop, $volume) = &getHtmlVar($query, 'volume');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "VOLUME : $volume<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_volume WHERE wpa_volume = '$volume' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_volume WHERE wpa_volume = '$volume' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_volume WHERE wpa_volume ~ '$volume' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_volume WHERE wpa_volume ~ '$volume' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $volume.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    print "<TABLE border=0><TR><TD>WBPaperID</TD><TD>Volume</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; 
    foreach my $number (sort keys %matches) {
#       my $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      my @row = $result->fetchrow; my $title = $row[1];
#       $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      @row = $result->fetchrow; my $journal = $row[1];
      unless ($journal) { $journal = ''; } unless ($title) { $title = ''; }
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&curator_name=$theHash{curator}&action=Number+%21\">$number</A></TD><TD>$matches{$number}</TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickVolume

sub pickYear {
  my ($oop, $year) = &getHtmlVar($query, 'year');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "YEAR : $year<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_year WHERE wpa_year = '$year' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_year WHERE wpa_year = '$year' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_year WHERE wpa_year ~ '$year' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_year WHERE wpa_year ~ '$year' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $year.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    print "<TABLE border=0><TR><TD>WBPaperID</TD><TD>Year</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; 
    foreach my $number (sort keys %matches) {
#       my $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      my @row = $result->fetchrow; my $title = $row[1];
#       $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      @row = $result->fetchrow; my $journal = $row[1];
      unless ($journal) { $journal = ''; } unless ($title) { $title = ''; }
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&curator_name=$theHash{curator}&action=Number+%21\">$number</A></TD><TD>$matches{$number}</TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickYear

sub pickAbstract {
  my ($oop, $abstract) = &getHtmlVar($query, 'abstract');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "ABSTRACT : $abstract<P>\n";

  if ($exact_or_sub eq 'exact') {
#     my $result = $conn->exec( "SELECT * FROM wpa_abstract WHERE wpa_abstract = '$abstract' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_abstract WHERE wpa_abstract = '$abstract' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
#     my $result = $conn->exec( "SELECT * FROM wpa_abstract WHERE wpa_abstract ~ '$abstract' ;" );
    my $result = $dbh->prepare( "SELECT * FROM wpa_abstract WHERE wpa_abstract ~ '$abstract' ;" );
    $result->execute;
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $abstract.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    print "<TABLE border=1><TR><TD>WBPaperID</TD><TD>Abstract</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; 
    foreach my $number (sort keys %matches) {
#       my $result = $conn->exec( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      my @row = $result->fetchrow; my $title = $row[1];
#       $result = $conn->exec( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute;
      @row = $result->fetchrow; my $journal = $row[1];
      unless ($journal) { $journal = ''; } unless ($title) { $title = ''; }
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$number&curator_name=$theHash{curator}&action=Number+%21\">$number</A></TD><TD>$matches{$number}</TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickAbstract

### PICK SECTION ###



### FIRST PAGE ###

sub firstPage {
  my $date = &getDate();
  print "Value : $date<BR>\n";
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi\">\n";
  print "<TABLE>\n";
  print "<TR><TD>Select your Name among : </TD><TD><SELECT NAME=\"curator_name\" SIZE=21>\n";

  &populateCurators();
  my $ip = $query->remote_host(); 				# select curator by IP if IP has already been used
  my $curator_by_ip = '';
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[0]) { $curator_by_ip = $row[0]; }
  my @curator_list = ('Juancarlos Chan', 'Wen Chen', 'Paul Davis', 'Margaret Duesbury', 'Ruihua Fang', 'Jolene S. Fernandes', 'Chris', 'Ranjana Kishore', 'Raymond Lee', 'Cecilia Nakamura', 'Tuco', 'Anthony Rogers', 'Gary C. Schindelman', 'Erich Schwarz', 'Paul Sternberg', 'Theresa Stiernagle', 'Mary Ann Tuli', 'Kimberly Van Auken', 'Qinghua Wang', 'Xiaodong Wang', 'Karen Yook');
  foreach my $curator (@curator_list) {				# display curators in alphabetical (array) order, if IP matches existing ip record, select it
    if ($curators{two}{$row[0]} eq $curator) { print "<option selected=\"selected\">$curator</option>\n"; }
    else { print "<OPTION>$curator</OPTION>\n"; } }

# #   print "<OPTION>Igor Antoshechkin</OPTION>\n";
# #   print "<OPTION>Carol Bastiani</OPTION>\n";
#   print "<OPTION>Juancarlos Chan</OPTION>\n";
#   print "<OPTION>Wen Chen</OPTION>\n";
#   print "<OPTION>Paul Davis</OPTION>\n";
#   print "<OPTION>Margaret Duesbury</OPTION>\n";
#   print "<OPTION>Ruihua Fang</OPTION>\n";
#   print "<OPTION>Jolene S. Fernandes</OPTION>\n";
# #   print "<OPTION>Eimear Kenny</OPTION>\n";
#   print "<OPTION>Ranjana Kishore</OPTION>\n";
#   print "<OPTION>Raymond Lee</OPTION>\n";
#   print "<OPTION>Cecilia Nakamura</OPTION>\n";
# #   print "<OPTION>Andrei Petcherski</OPTION>\n";
#   print "<OPTION>Tuco</OPTION>\n";
#   print "<OPTION>Anthony Rogers</OPTION>\n";
#   print "<OPTION>Gary C. Schindelman</OPTION>\n";
#   print "<OPTION>Erich Schwarz</OPTION>\n";
#   print "<OPTION>Paul Sternberg</OPTION>\n";
#   print "<OPTION>Theresa Stiernagle</OPTION>\n";
#   print "<OPTION>Mary Ann Tuli</OPTION>\n";
#   print "<OPTION>Kimberly Van Auken</OPTION>\n";
#   print "<OPTION>Qinghua Wang</OPTION>\n";
#   print "<OPTION>Xiaodong Wang</OPTION>\n";
#   print "<OPTION>Karen Yook</OPTION>\n";
# #   print "<OPTION>Andrei Testing</OPTION>\n";
# #   print "<OPTION>Juancarlos Testing</OPTION>\n";	# Not a valid two_standardname so won't work
  print "</SELECT></TD>\n";
#   print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Curator !\"></TD></TR><BR><BR>\n";
  print "</TABLE>\n";

  print "<TABLE border=1 cellspacing=5>\n";
  print "<TR><TD>Number : <TD><INPUT SIZE=40 NAME=\"number\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Number !\"></TD>\n";
  print "<TD>Enter the wbpaper number for exact match ;  otherwise it will try to match the cgc, pmid, etc. ;  otherwise it will strip the non-number characters and try to match the number.</TR>\n";
  print "<TR><TD>Author : <TD><INPUT SIZE=40 NAME=\"author\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Author !\"></TD>\n";
  print "<TD>Enter an Author and select below whether to find an exact author (e.g. Sternberg PW) or a substring (e.g. Sternberg).  Case sensitive.</TR>\n";
  print "<TR><TD>Title : <TD><INPUT SIZE=40 NAME=\"title\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Title !\"></TD>\n";
  print "<TD>Enter a Title and select below whether to find an exact title (e.g. The pharynx of C. elegans.) or a substring (e.g. pharynx)</TR>\n";
  print "<TR><TD>Journal : <TD><INPUT SIZE=40 NAME=\"journal\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Journal !\"></TD>\n";
  print "<TD>Enter a Journal and select below whether to find an exact journal (e.g. Developmental Biology) or a substring (e.g. Biology)</TR>\n";
  print "<TR><TD>Pages : <TD><INPUT SIZE=40 NAME=\"pages\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Pages !\"></TD>\n";
  print "<TD>Enter Pages and select below whether to find exact pages (e.g. 403//409) or a substring (e.g. 403)</TR>\n";
  print "<TR><TD>Volume : <TD><INPUT SIZE=40 NAME=\"volume\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Volume !\"></TD>\n";
  print "<TD>Enter a Volume and select below whether to find an exact volume (e.g. 118//2) or a substring (e.g. 118)</TR>\n";
  print "<TR><TD>Year : <TD><INPUT SIZE=40 NAME=\"year\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Year !\"></TD>\n";
  print "<TD>Enter a Year and select below whether to find an exact year (e.g. 2005) or a substring (e.g. 200)</TR>\n";
  print "<TR><TD>Abstract : <TD><INPUT SIZE=40 NAME=\"abstract\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Abstract !\"></TD>\n";
  print "<TD>Enter an Abstract and select below whether to find an exact abstract (e.g. Applying a series of techniques intended to induce, detect and isolate lethal and/or sterile temperature-sensitive mutants, specific to the sel f-fertilizing hermaphrodite nematode Caenorhabditis elegans, Bergerac strain, 25 such mutants have been found. Optimal conditions for the application of muta genic treatment and the detection of such mutations are discussed.) or a substring (e.g. Applying a series of techniques)</TR>\n";
  print "<TR><TD>Exact</TD><TD><INPUT NAME=\"exact_or_sub\" TYPE=\"radio\" VALUE=\"exact\"></TD></TR>\n";
  print "<TR><TD>Substring</TD><TD><INPUT NAME=\"exact_or_sub\" TYPE=\"radio\" VALUE=\"substring\" CHECKED></TD></TR>\n";
  print "<TR><TD></TD></TR>\n";
  print "<TR><TD>checkout for first pass</TD><TD ALIGN=CENTER><INPUT TYPE=submit NAME=action VALUE=\"Not Curated plus Textpresso !\"></TD>\n";
  print "<TD COLSPAN=2>flag as false positives <INPUT TYPE=submit NAME=action VALUE=\"False Positives !\">flag as already curated <INPUT TYPE=submit NAME=action VALUE=\"Already Curated !\"></TD></TR>\n";
  print "<TR><TD>checkout for RNAi</TD><TD ALIGN=CENTER><INPUT TYPE=submit NAME=action VALUE=\"RNAi Curation !\"></TD></TR>\n";
  print "<TR><TD>checkout for Allele</TD><TD ALIGN=CENTER><INPUT TYPE=submit NAME=action VALUE=\"Allele Curation !\"></TD></TR>\n";
  print "<TR><TD>checkout for Overexpression</TD><TD ALIGN=CENTER><INPUT TYPE=submit NAME=action VALUE=\"Overexpression Curation !\"></TD></TR>\n";
  print "<TR><TD>checkout for Everything</TD><TD ALIGN=CENTER><INPUT TYPE=submit NAME=action VALUE=\"Everything Curation !\"></TD></TR>\n";
  print "<TR><TD></TD><TD ALIGN=CENTER><INPUT TYPE=submit NAME=action VALUE=\"Enter New Papers !\"></TD></TR>\n";
  print "</FORM>\n";
  print "</TABLE>\n";
} # sub firstPage

### FIRST PAGE ###



### PG HASHES ###

sub populateCurators {
#   my $result = $conn->exec( "SELECT * FROM two_standardname; " );
  my $result = $dbh->prepare( "SELECT * FROM two_standardname; " );
  $result->execute;
  while (my @row = $result->fetchrow) {
    $curators{two}{$row[0]} = $row[2];
    $curators{std}{$row[2]} = $row[0]; 
  } # while (my @row = $result->fetchrow)
} # sub populateCurators

sub populateTypeIndex {
#   my $result = $conn->exec( "SELECT * FROM wpa_type_index;" );
  my $result = $dbh->prepare( "SELECT * FROM wpa_type_index;" );
  $result->execute;
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $type_index{$row[0]} = $row[1]; }
  }
#   $result = $conn->exec( "SELECT * FROM wpa_electronic_type_index;" );
  $result = $dbh->prepare( "SELECT * FROM wpa_electronic_type_index;" );
  $result->execute;
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $electronic_type_index{$row[0]} = $row[1]; }
  }
} # sub populateTypeIndex

### PG HASHES ###



### INITIALIZE ###

sub initializeTables {
  foreach my $tables (@generic_tables) {
    $tables{copies}{$tables} = 1;
  } # foreach my $tables (@generic_tables)
  $tables{copies}{wpa} = 0;
  $tables{copies}{wpa_identifier} = 4;
  $tables{copies}{wpa_keyword} = 5;
  $tables{copies}{wpa_author} = 5;

  foreach my $author_type (@author_types) {
    $tables{copies}{$author_type} = 2;
  } # foreach my $tables (@generic_tables)

  $tables{copies}{wpa_electronic_path_type} = 4;
  $tables{copies}{wpa_gene} = 3;

  $ignore_extras{'Ranjana Kishore'}++;

  $options{"num_per_page"} = 200;
} # sub initializeTables

### INITIALIZE ###


__END__


The Tables
wpa
wpa_identifier
wpa_title
wpa_publisher
wpa_journal
wpa_volume
wpa_pages
wpa_year
wpa_date_published
wpa_fulltext_url
wpa_abstract
wpa_affiliation
wpa_type
wpa_author
wpa_hardcopy
wpa_comments
wpa_editor
wpa_nematode_paper
wpa_contained_in
wpa_contains
wpa_keyword
wpa_erratum
wpa_in_book
wpa_author_possible;
wpa_author_sent;
wpa_author_verified;




wpa_type_index
wpa_author_index
wpa_electronic_type_index
wpa_electronic_path_type
wpa_electronic_path_md5


__DEPRECATED__


### CDS QUERY ###	# not needed anymore since it should auto convert the CDS to a WBGene  2009 09 03

sub cdsQuery {		# batch cds query added to copy-paste into WBGene - CDS boxes  2005 07 26
  &populateCurators();
  &readCurrentLocus();
  my ($oop, $number) = &getHtmlVar($query, 'number');
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"number\" VALUE=\"$number\">\n";
  ($oop, my $cds_value) = &getHtmlVar($query, 'cds_value');
  my @cds = split/\s+/, $cds_value;
  my @wbgene_results;
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR><TD>WBPaper Number</TD><TD>$number</TD></TR>\n";
  print "<TR><TD>&nbsp;</TD></TR>\n";
  foreach my $cds (@cds) {
    print "<TR><TD>";
    if ( $cdsToGene{cds}{$cds} ) { print "$cdsToGene{cds}{$cds}"; push @wbgene_results, $cdsToGene{cds}{$cds}; } 
      else { print "<FONT COLOR=$red>Not a valid CDS $cds</FONT>"; } 
    print "</TD><TD>$cds</TD></TR>\n"; }
  print "</TABLE>\n";
  print "<TABLE><TR><TD>all result wbgenes<\/TD><\/TR>\n";	# also output all results in own column at the bottom for Andrei 2006 09 14
  foreach my $wbg (@wbgene_results) { print "<TR><TD>$wbg</TD></TR>\n"; }
  print "</TABLE>\n";
} # sub cdsQuery

sub cdsQueryPage {
  &populateCurators();
  my ($oop, $number) = &getHtmlVar($query, 'number');
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"number\" VALUE=\"$number\">\n";
  print "WBPaper Number : $number<P>\n";
  print "Enter CDS in box, one per line :<BR>\n<TEXTAREA NAME=\"cds_value\" ROWS=8 COLS=60 VALUE=\"\"></TEXTAREA><BR>\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"CDS Query !\"><P>\n";
} # sub cdsQueryPage

### CDS QUERY ###


sub OLDgetFirstPassTables {
  my $infile = '/home/postgres/public_html/cgi-bin/curation.cgi';
  $/ = undef;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  my $curation_file = <IN>;
  close (IN) or die "Cannot close $infile : $!";
  $/ = "\n";
  if ($curation_file =~ m/\nmy \@PGparameters = qw\((.*?)\);/s) { 
      my $firstpassTables = $1;
      (@fptables) = split/\s+/, $1; }
    else { 
      print "ERROR first pass tables read error for curation.cgi<BR>\n"; }
} # sub OLDgetFirstPassTables


sub OLDsortPapers {			# to display all papers in pages, 20 entries per page from $options{num_per_page}
  &populateTextpressoBody();
  &populateCurators();
  my $sort_type = shift;	# may sort by date (default), number, journal
  print "Displaying all WBPapers, $options{num_per_page} entries per page, sorting by ${sort_type}.<BR>\n";
  my @wpas; my $result;		# the joinkeys, sorted
  my ($oop, $sort_ordering) = &getHtmlVar($query, 'sort_ordering');
  my $order_by = ' ORDER BY joinkey DESC';
  if ($sort_ordering) { if ($sort_ordering eq 'date') { $order_by = ' ORDER BY wpa_timestamp DESC'; } }

  if ($sort_type eq 'all_papers') { 
    my %wpas; 
#     $result = $conn->exec( "SELECT * FROM wpa $order_by; ");						# default
    $result = $dbh->prepare( "SELECT * FROM wpa $order_by; ");						# default
    $result->execute;
    while (my @row = $result->fetchrow) { 			# don't include repeats if a paper's been valid and invalid  2006 02 27
      unless ($wpas{$row[0]}) { push @wpas, $row[0]; } 
      $wpas{$row[0]}++; } }
  elsif ($sort_type eq 'no_meeting') {										# no meetings
    my %bad; 
#     $result = $conn->exec( "SELECT * FROM wpa_type WHERE wpa_type = '3' OR wpa_type = '4' OR wpa_type = '7'; "); 
    $result = $dbh->prepare( "SELECT * FROM wpa_type WHERE wpa_type = '3' OR wpa_type = '4' OR wpa_type = '7'; "); 
    $result->execute;
    while (my @row = $result->fetchrow) { $bad{$row[0]}++; }	# put meeting abstracts in bad hash to exclude
    my %wpas; 
#     $result = $conn->exec( "SELECT * FROM wpa $order_by; ");						# default
    $result = $dbh->prepare( "SELECT * FROM wpa $order_by; ");						# default
    $result->execute;
    while (my @row = $result->fetchrow) {
      unless ( $bad{$row[0]} || $wpas{$row[0]}) { push @wpas, $row[0]; } 
      $wpas{$row[0]}++; } }
  elsif ($sort_type eq 'c_elegans') {										# not functional annotation
    my %bad; 
#     $result = $conn->exec( "SELECT * FROM cfp_comment WHERE cfp_comment = 'the paper is used for functional annotations'; "); 
    $result = $dbh->prepare( "SELECT * FROM cfp_comment WHERE cfp_comment = 'the paper is used for functional annotations'; "); 
    $result->execute;
    while (my @row = $result->fetchrow) { $bad{$row[0]}++; }	# put meeting abstracts in bad hash to exclude
#     $result = $conn->exec( "SELECT * FROM wpa $order_by ; ");	# push into array if not to be excluded
    $result = $dbh->prepare( "SELECT * FROM wpa $order_by ; ");	# push into array if not to be excluded
    $result->execute;
    my %wpas; 
#     $result = $conn->exec( "SELECT * FROM wpa $order_by ; ");	# push into array if not to be excluded
    $result = $dbh->prepare( "SELECT * FROM wpa $order_by ; ");	# push into array if not to be excluded
    $result->execute;
    while (my @row = $result->fetchrow) { 
      unless ($wpas{$row[0]}) { unless ($bad{$row[0]}) { push @wpas, $row[0]; } }
      $wpas{$row[0]}++; } }
  elsif ( ($sort_type eq 'not_curated') || ($sort_type eq 'not_curated_plus_textpresso') ) {		# not curated
    my %bad; 
#     $result = $conn->exec( "SELECT * FROM cfp_curator WHERE joinkey ~ '^0'; "); 
    $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE joinkey ~ '^0'; "); 
    $result->execute;
    while (my @row = $result->fetchrow) { $bad{$row[0]}++; }	# put curated ones in bad hash to exclude
#     $result = $conn->exec( "SELECT * FROM wpa_type WHERE wpa_type = '3' OR wpa_type = '4' OR wpa_type = '7'; ");	# exclude meeting abstracts since those are never curated
    $result = $dbh->prepare( "SELECT * FROM wpa_type WHERE wpa_type = '3' OR wpa_type = '4' OR wpa_type = '7'; ");	# exclude meeting abstracts since those are never curated
    $result->execute;
    while (my @row = $result->fetchrow) { $bad{$row[0]}++; }	# put meeting abstracts in bad hash to exclude
    my %invalid; 
#     $result = $conn->exec( "SELECT * FROM wpa ORDER BY wpa_timestamp ; "); 			# get hash of invalid papers so as not to print those  2006 05 18
    $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp ; "); 			# get hash of invalid papers so as not to print those  2006 05 18
    $result->execute;
    while (my @row = $result->fetchrow) { if ($row[3] eq 'invalid') { $invalid{$row[0]}++; } else { delete $invalid{$row[0]}; } }
#     $result = $conn->exec( "SELECT DISTINCT(joinkey) FROM wpa $order_by ; "); 	# push into array if not to be excluded
    $result = $dbh->prepare( "SELECT DISTINCT(joinkey) FROM wpa $order_by ; "); 	# push into array if not to be excluded
    $result->execute;
    while (my @row = $result->fetchrow) { unless ($bad{$row[0]}) { unless ($invalid{$row[0]}) { push @wpas, $row[0]; } } } 
    if ($sort_type eq 'not_curated_plus_textpresso') {
      my @temp; foreach (@wpas) { if ($textpresso_body{$_}) { push @temp, $_; } } @wpas = @temp; } }
  elsif ($sort_type eq 'cgc') {											# sort by cgcs in descending order
    my %sort; 
#     $result = $conn->exec( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ 'cgc';" );
    $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ 'cgc';" );
    $result->execute;
    while (my @row = $result->fetchrow) { $row[1] =~ s/cgc//g; $row[1] = &padZeros($row[1]); $sort{$row[1]} = $row[0]; }
    foreach my $cgc (reverse sort keys %sort) { push @wpas, $sort{$cgc}; } }
  elsif ($sort_type eq 'by_curator') {										# sort by curators in descending order	2006 08 24
#     $result = $conn->exec( "SELECT * FROM cfp_curator WHERE cfp_curator != 'two480' ORDER BY cfp_curator, cfp_timestamp;" );
    $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE cfp_curator != 'two480' ORDER BY cfp_curator, cfp_timestamp;" );
    $result->execute;
    while (my @row = $result->fetchrow) { push @wpas, $row[0]; } 
#     $result = $conn->exec( "SELECT * FROM cfp_curator WHERE cfp_curator = 'two480' ORDER BY cfp_curator, cfp_timestamp;" );
    $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE cfp_curator = 'two480' ORDER BY cfp_curator, cfp_timestamp;" );
    $result->execute;
    while (my @row = $result->fetchrow) { push @wpas, $row[0]; } }
  elsif ($sort_type eq 'specific_paper') {										# sort by curators in descending order	2006 08 24
    ($oop, my $specific_paper) = &getHtmlVar($query, 'specific_paper');
#     $result = $conn->exec( "SELECT * FROM wpa WHERE joinkey ~ '$specific_paper';" );
    $result = $dbh->prepare( "SELECT * FROM wpa WHERE joinkey ~ '$specific_paper';" );
    $result->execute;
    while (my @row = $result->fetchrow) { push @wpas, $row[0]; } }
  else { 
#     $result = $conn->exec( "SELECT * FROM wpa $order_by; "); 
    $result = $dbh->prepare( "SELECT * FROM wpa $order_by; "); 
    $result->execute;
  }						# default
#   if ($sort_type eq 'number') { $result = $conn->exec( "SELECT * FROM wpa ORDER BY joinkey DESC; "); }
#   elsif ($sort_type eq 'journal') { $result = $conn->exec( "SELECT * FROM wpa_journal ORDER BY wpa_journal ; "); }	# this result will yield less papers since some don't have journal
#   else { $result = $conn->exec( "SELECT * FROM wpa ORDER BY wpa_timestamp DESC; "); }					# date is default
  while (my @row = $result->fetchrow) { push @wpas, $row[0]; }

  my ($current_page) = &getSortPage(scalar(@wpas));		# get the current page if any, show sorting options
  my $skip_num = ($current_page - 1) * $options{num_per_page};	# skip this many entries based on page
  for (1 .. $skip_num) { shift @wpas; }				# skip them
  print "<TABLE border=0><TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Key</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>Journal</TD><TD ALIGN=CENTER>Hardcopy</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>Title</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curator</TD><TD ALIGN=CENTER>curate</TD></TR>\n";
  for (0 .. $options{num_per_page}) { my $joinkey = shift @wpas; if ($joinkey) { &sortLink($joinkey); } }		# show paper data and link to it
  print "<TR><TD ALIGN=CENTER>WBPaperID</TD><TD ALIGN=CENTER>Key</TD><TD ALIGN=CENTER>Identifiers</TD><TD ALIGN=CENTER>Journal</TD><TD ALIGN=CENTER>Hardcopy</TD><TD ALIGN=CENTER>PDF</TD><TD ALIGN=CENTER>Title</TD><TD ALIGN=CENTER>checked out</TD><TD ALIGN=CENTER>last curator</TD><TD ALIGN=CENTER>curate</TD></TR></TABLE>\n";
} # sub OLDsortPapers

sub readCurrentLocus {						# this took too long, using ajax call or psql query for each wbgene instead  2009 09 03
  my ($start) = time;
  my @pgtables = qw( gin_synonyms gin_locus );
  foreach my $table (@pgtables) {				# updated to get values from postgres 2006 12 22
#     my $result = $conn->exec( "SELECT * FROM $table;" );
    my $result = $dbh->prepare( "SELECT * FROM $table;" );
    $result->execute;
    while (my @row = $result->fetchrow) {
      my $wbgene = 'WBGene' . $row[0];
      $cdsToGene{back}{$wbgene} = $row[1]; 
      $cdsToGene{locus}{$row[1]} = $wbgene; } }
#   my $result = $conn->exec( "SELECT * FROM gin_sequence;" );
  my ($end) = time;
  my $load = $end - $start;
  print "LOADED IN $load seconds<br />\n";
  my $result = $dbh->prepare( "SELECT * FROM gin_sequence;" );
  $result->execute;
  while (my @row = $result->fetchrow) {
    my $wbgene = 'WBGene' . $row[0];
    my $sequence = $row[1];
    my $cds = $sequence;					# not the cds yet, have to strip last letter
    if ($cds =~ m/[a-zA-Z]+$/) { $cds =~ s/[a-zA-Z]+$//g; }
    $cdsToGene{cds}{$cds} = $wbgene; }
  my ($end) = time;
  my $load = $end - $start;
  print "LOADED IN $load seconds<br />\n";
} # sub readCurrentLocus


# old way of dealing with wpa_gene under updateInfo, which used &readCurrentLocus(); and took 7 seconds
#           foreach my $value (@values) {
#             my (@evidence_copy) = (@evidences); my $curator_copy = $curators{std}{$theHash{curator}}; my $pg_value; my $pg_evidence;
#             ($value) = &filterSpaces($value);			# clear leading and trailing spaces
#             if ($value =~ m/\s+/) { $value =~ s/\s+/\t/; }	# store separator between wbgene and cds as a tab
#             my ($locus, $cds, $wbgene, $err);
#             if ($value =~ m/^(.*?)\t(.*?)$/) { $locus = $1; $cds = $2; } else { $locus = $value; }
#             if ($locus =~ m/WBGene/) { $value = $locus; }
# #               elsif ($cdsToGene{locus}{$locus}) { $value = $cdsToGene{locus}{$locus}; }		# doesn't store original locus
#               elsif ($cdsToGene{locus}{$locus}) { $value = "$cdsToGene{locus}{$locus}($locus)"; }	# stores original locus in parentheses
#               else { $err .= "Not a valid Locus $locus<BR>\n"; }
#             if ($cds) {
#               if ($cdsToGene{cds}{$cds}) { $value .= "\t$cds"; }
#                 else { $err .= "Not a valid CDS $cds<BR>\n"; } }
#             ($value) = &filterForPg($value);			# replace ' with ''
#             if ($value) { $pg_value = "'$value'"; } else { $pg_value = 'NULL'; }
#             if ($err) { print "<TR bgcolor=$red><TD>$pg_table</TD><TD>$err : $value</TD><TD>$order</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n"; next; }
#             foreach my $evidence ($curator_copy, @evidence_copy) {
#               ($evidence) = &filterSpaces($evidence);			# clear leading and trailing spaces
# #               if ($evidence =~ m/^(two)(\d+)/) { $evidence =~ s/^(two)(\d+)/Curator_confirmed\/\/WBPerson$2/g; }
# #               elsif ($evidence =~ m/^(WBPerson\d+)/) { $evidence =~ s/^(WBPerson\d+)/Person_evidence\/\/$1/g; }
# #               elsif ($evidence =~ m/^Person_evidence\/\/[\w ]+/) { 1; }	# proper Author_evidence format
# #               elsif ($evidence =~ m/^Author_evidence\/\/[\w ]+/) { 1; }	# proper Author_evidence format
# #               elsif ($evidence =~ m/^Inferred_automatically\/\/[\w ]+/) { 1; }	# proper Inferred_automatically format
#               if ($evidence =~ m/^(two)(\d+)/) { $evidence =~ s/^(two)(\d+)/Curator_confirmed \"WBPerson$2\"/g; }
#               elsif ($evidence =~ m/^(WBPerson\d+)/) { $evidence =~ s/^(WBPerson\d+)/Person_evidence\t\"$1\"/g; }
#               elsif ($evidence =~ m/^Person_evidence\s+\"[\w ]+\"/) { 1; }	# proper Author_evidence format
#               elsif ($evidence =~ m/^Author_evidence\s+\"[\w ]+\"/) { 1; }	# proper Author_evidence format
#               elsif ($evidence =~ m/^Inferred_automatically\s+\"[\.\w ]+\"/) { 1; }	# proper Inferred_automatically format
#               elsif ($evidence =~ m/^Published_as\s+\"[\w\-\. ]+\"/) { 1; }		# proper Published_as format	for Kimberly 2006 01 20  Added hyphen 2006 02 03
#               else { 
#                 print "<TR bgcolor=$red><TD>$pg_table</TD><TD>$value</TD><TD>NOT A VALID EVIDENCE TYPE $evidence</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n"; next; }
#               print "<TR><TD>$pg_table</TD><TD>$value</TD><TD>$evidence</TD><TD>$valid</TD><TD>$row_count</TD><TD>$normal</TD><TD>yes</TD></TR>\n";
#               if ($evidence) { $pg_evidence = "'$evidence'"; } else { $pg_evidence = 'NULL'; }
# #               my $result = $conn->exec( "INSERT INTO $pg_table VALUES ('$joinkey', $pg_value, $pg_evidence, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
#               my $result = $dbh->prepare( "INSERT INTO $pg_table VALUES ('$joinkey', $pg_value, $pg_evidence, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP); ");
#               $result->execute;
#               $pg_commands .= "INSERT INTO $pg_table VALUES ('$joinkey', $pg_value, $pg_evidence, '$valid', '$curators{std}{$theHash{curator}}', CURRENT_TIMESTAMP);<BR>\n"; 
#             } # foreach my $evidence (@evidences)
#           } # foreach my $value (@values)
