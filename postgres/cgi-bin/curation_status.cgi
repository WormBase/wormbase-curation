#!/usr/bin/perl -w

# Display curation status results

# Look at caprica's <dates>/ directories and get paper-type-result mappings.  
# Sparked by Karen's frustration without her request.  2011 04 14
# 
# Form redone to store svm values locally in postgres.  For Kimberly and Daniela.
# 2012 07 02
#
# changed hashing structure to sort off of all data structures that have papers
# not just those that have SVM to allow papers that have been curated by not SVMed
# to be displayed.  2012 08 10
#
# if a paper only has a .main then a positive or negative refers to the document.
# what is a .main only depends on what michael says about how they get documents,
# and what kimberly thinks about excel documents and so on.
#
# todo - free text comment ?
# todo - not yet svm in svm analysis
# todo - if by document, show papers/page results by document instead of by paper ?
#
# changed form to not have modifiers when reading svmData nor oaData, all documents
# are compressed into a single paper.  also no svm dates are necessary since we just
# care if something was flagged for any part of the paper or not.  2012 09 13
#
# started adding curation statistics giant table.  2012 10 11
#
# changed curated to validated and added distinction from cur_curdata between 
# negative / positive / curated  putting the values in %validated %valNeg %valPos %valCur
# added further subdivisions of TP -> TP cur / TP not cur ;  Positive not curated
# (vs previous Pos not validated) ;  same with negative FN.  
# changed statistics table header ths to have some forced width.  2012 11 11
#
# curation statistics table options page added to only get chosen datatypes and
# chosen flagging methods.  
# statistics table now has objects curated per curated paper instead of validated paper,
# and has papers curated.  2012 11 12
#
# changed  &getCurationStatisticsAllValPos()  to also get values for
# 'allval pos cur' and 'allval pos ncur' (validated positive curated, 
# validated positive not curated).  2012 11 13
#
# created  &printDescriptionOfLabelPage()  for statistics table label names to link
# to a new window with the description.
# split  &getCurationStatisticsSvm();  into  &getCurationStatisticsSvm();  and
# getCurationStatisticsSvmNd();  to separate SVM and all subsections from 'svmnotdone'
# so that  &listCurationStatisticsPapersPage();  gets the right set only.
# changed  &listCurationStatisticsPapersPage();  so it shows the specific paper page
# inputs with the chosen papers in the textarea and the link's chosen datatype selected.
# changed  &getResults  for the free text commend to have a div and a textarea
# with the div showing by default, toggling to textarea when selected and back to div
# when blurred.  2012 11 14
#
# added intersection rows  curStats{'int'}  for when multiple flagging methods are 
# selected and all of them have a set of papers.
# changed  &listCurationStatisticsPapersPage();  so when calculating 'any' it only
# gets the union of the selected flagging methods instead of all flagging methods.
# added Chris descriptions to labels.  2012 11 15
# 
# Now each datatype has individual values for CFP flagged, AFP flagged,
# Any flagged, Intersection flagged instead of improperly calling them allSame.
# allSame might have been okay for cfp and afp, but not for SVM so not for Any nor
# Intersection, so it's easier to treat them all the same.  In theory we could figure
# out which of those were really flagged if we knew with flags existed when the flagger
# touched it.  
# added Time::HiRes to see what sections of the statistics table take different amount
# of times to load depending on flagging methods and datatypes chosen.  2012 11 16
#
# changed  &processResultDataDuplicateData()  to have a nicer table display.
# added  'notvalidated'  option to  %donPosNegOptions  for values that were mistakenly
# validated but really aren't (leaving blank to mean not to process the value).
# 2012 11 20
#
# %datatypesAfpCfp now maps from the datatype to the afp/cfp table name, to get
# anatomy function stuff.  anatomy function populated into  %oaData  from wbb_ 
# tables.  2012 11 27
#
# changed svm cur_datatype column from geneprod_GO go geneprod.  2012 11 28
#
# cleaned up hashes to be datatype-paper instead of having some paper-datatype.
# now only one subroutine to populate svm data for stats and getResults.
# cur_curdata no longer has cur_paper_modifier column.  2012 12 02
#
# added headers to bottom of statistics table, and a $labelRightFlag to display
# the row labels if there are more than 6 selected datatypes.
# cleaned up commented-out code, indentation, uninitialized values in concatenation.
# 2012 12 03
#
# added Daniela expr picture curation  2012 12 13
# added Daniela 2084 chronogram objects count to other expr.  2012 12 23
# added Daniela 19052 picture objects count to picture.  2012 12 24
#
# added Hinxton people to login page.  2013 04 17
#
# changed premadeComment #2 for Daniela.  2013 06 19
#
# link to documentation for Daniela.  2013 09 24
#
# added "chemicals" to  %datatypesAfpCfp  in  &populateDatatypes 
# and several queries for it to  &populateOaData  since curation of it happens in
# several OAs.  for Karen.  2013 10 02
#
# testing with flatfiles whether topic curation can be just a filter based on 
# list of WBPaper IDs.
# changed  &printSpecificPaperPage  to also do  &printSelectTopics();  which is a
# new dropdown of flatfiles containing WBPaperIDs to filter through instead of 
# specific_papers from the textarea.
# changed  &getResults  to look for select_topic and if so, replace the 
# $specificPapers values with those from the topic flatfile.  also pass on hidden
# the select_topic value for changing to other pages.  2013 11 05
#
# changed  &getResults  so that if there's a $displayOa, show  oa_blank  as a 
# highlighted span like svm high, so that flagged positive and not curated pop 
# out more.  
# changed  &getResults  to filter on specific_papers first and then the results of
# that through select_topic .  
# added  &printSelectTopics  to  &listCurationStatisticsPapersPage  to be able to 
# go from curation statistics table, pick a set through there, and then post-process
# through a topic filter.  
# Both changes were necessary because curators mostly want to pick a datatype, see
# all positive flags not curated, and then filter through the topic set.
# for Chris and Karen.  2013 11 06
# 
# changed  &printSelectTopics  to list topics from pro_ OA tables, based on process
# paper and topicpaperstatus being relevant or unchecked.  topics get the name of the
# process from the prt_processname .
# changed  &getResults  to filter based on papers from the pro_ OA tables, where the
# topicpaperstatus is relevant or unchecked  and the process is the chosen topic
# then get the papers that match the joinkeys from pro_paper.  
# for Chris and Karen, documented and live.  2013 11 07
#
# New  %premadeComments  for Kimberly (okayed by Chris and Daniela).  2014 01 07
#
# Added a new toggle toggle in the topic OA to prevent papers with that toggle from 
# showing up when filtering by topic.  filter out pro_curationstatusomit  for Karen.
# Karen and Kimberly agree that whatever Karen flags is not necessarily what Kimberly
# would want in pap_primary_data so the two things should be separate instead of Karen
# changing pap_primary_data directly.  2014 02 06
# 
# Whend doing topic filtering, Chris no longer wants 'unchecked' papers, only 
# 'relevant'.  Changed corresponding queries under  &printSelectTopics  and  &getResults 
# 2014 06 12
#
# Changed default behaviour, to show all chosen datatypes whether or not they have data.
# Added checkbox 'checkbox_all_datatypes_with_data' that will display data for chosen
# papers for all datatypes only if they have data or flags.  
# &getResults  now for each paper loops datatypes from %datatypes instead of 
# %allPaperData, and if $all_datatypes_with_data_checkbox eq 'all' + there is no data
# in %allPaperData, it will skip displaying it.
# for Chris and Raymond.  2014 07 09
#
# exclude rna_nodump when reading curated data from rna_ tables.  for Chris.  2014 09 10
#
# exclude non_nematode from curatable papers list.  2014 09 25



use strict;
use CGI;
use DBI;
use Jex;
use LWP::Simple;
use Tie::IxHash;                                # allow hashes ordered by item added
use POSIX qw(ceil);
# use Math::Round;				# nearest for percentages
use Math::SigFigs;				# significant figures $new = FormatSigFigs($n, $d);
use Time::HiRes qw ( time );			# replace time with High Resolution version

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $result;

my $query = new CGI;
my $oop;

my $frontpage = 1;

my $curator = '';
my %datatypes; # tie %datatypes, "Tie::IxHash";		# all allowed datatypes, was tieing to separate/order nonSvm vs Svm, but not anymore  2012 11 16
my %datatypesAfpCfp;		# key datatype value is afp_ cfp_ tables's datatype to query (e.g. datatype 'blastomere' maps to 'cellfunc' for [ac]fp_cellfunc)
my %chosenDatatypes;		# selected datatypes to display
my %chosenPapers;		# selected papers to display
my %curatablePapers;		# paper joinkeys that are curatable.  $curatablePapers{joinkey} = valid
my %oaData;			# curator PG data from OA or other pg tables   		$oaData{datatype}{joinkey} = 'positive';
my %curData;			# curator PG data from cur_curdata table       		$curData{datatype}{joinkey}{curator/donposneg/selcomment/txtcomment/timestamp} = value
my %objsCurated;		# datatype-object curated		       		$objsCurated{$datatype}{$objName}++;
my %conflict;			# datatype-paper has curator conflict	       		$conflict{$datatype}{$joinkey}++;
my %validated;			# datatype-paper validated		       		$validated{$datatype}{$joinkey} = $value;
my %valCur;			# datatype-paper validated as curated 	       		$valCur{$datatype}{$joinkey} = $value;
my %valPos;			# datatype-paper validated as positive	       		$valPos{$datatype}{$joinkey} = $value;
my %valNeg;			# datatype-paper validated as negative         		$valNeg{$datatype}{$joinkey} = $value;
my %curStats; tie %curStats, "Tie::IxHash";	# hash of curation statistics		$curStats{'cfp'}{'pos'}{$datatype}{papers}{$joinkey}++; $curStats{'cfp'}{'pos'}{$datatype}{'countPap'} = count; $curStats{'cfp'}{'pos'}{$datatype}{'ratio'}    = ratio;
my %statsHashToLabel;		# curStats in array form to label name
my %statsHashToDescription;	# curStats in array form to description of data
my %cfpData;			# curator FP results from cfp_ tables			$cfpData{$datatype}{$joinkey} = $value;
my %cfpFlagged;			# curator has cfp_curator value for datatype-joinkey  	$cfpFlagged{$datatype}{$joinkey}++;
my %cfpPos;			# curator has cfp value for datatype-joinkey		$cfpPos{$datatype}{$joinkey}++;
my %cfpNeg;			# curator has cfp value for datatype-joinkey		$cfpNeg{$datatype}{$joinkey}++;
my %afpData;			# author FP results from afp_ tables			$afpData{$datatype}{$joinkey} = $value;
my %afpEmailed;			# author has afp_email value				$afpEmail{$joinkey}++;
my %afpFlagged; 		# author has afp_lasttouched value for datatype-joinkey	$afpFlagged{$datatype}{$joinkey}++;
my %afpPos;			# author has afp value for datatype-joinkey		$afpPos{$datatype}{$joinkey}++;
my %afpNeg;			# author has afp value for datatype-joinkey		$afpNeg{$datatype}{$joinkey}++;
my %svmData; 			# svm results by datatype-joinkey			$svmData{$datatype}{$joinkey} = $svmdata;
my %journal;			# pap_journal key is paper joinkey
my %pmid;			# link to ncbi from pap_identifier
my %pdf;			# link to pdf on tazendra from pap_electronic_path
my %curators;		tie %curators, "Tie::IxHash";			# $curators{"two1823"}  = "Juancarlos Chan";
my %donPosNegOptions;	tie %donPosNegOptions, "Tie::IxHash";		# $donPosNegOptions{"pgvalue"} = "displayValue"
my %premadeComments;	tie %premadeComments, "Tie::IxHash";		# $premadeComments{"pgvalue"} = "displayValue"

my $tdDot = qq(<td align="center" style="border-style: dotted">);
my $thDot = qq(<th align="center" style="border-style: dotted">);

&display();



sub display {
  my $action; 
  &printHeader('Curation Status');
  &populateDatatypes();
  &populateCurators();
  &populatePremadeComments(); 
  &populateDonPosNegOptions(); 
  ($oop, $curator) = &getHtmlVar($query, "select_curator");
  if ($curator) { &updateWormCurator($curator); }
  
  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); }
  } else { $frontpage = 0; }

  unless ($action eq 'printDescriptionOfLabelPage') {  
    &printFrontPageLink($action); }			# link to front page in most pages, but not in description page

  if ($action eq 'Get Results') {                          &getResults();                           }
  elsif ($action eq 'Add Results') {                       &addResults();                           }
  elsif ($action eq 'Submit New Results') {                &submitNewResults();                     }
  elsif ($action eq 'Overwrite Selected Results') {        &overwriteSelectedResults();             }
  elsif ($action eq 'Specific Paper Page') {               &printSpecificPaperPage();               }
  elsif ($action eq 'Add Results Page') {                  &printAddResultsPage();                  }
  elsif ($action eq 'Curation Statistics Page') {          &printCurationStatisticsPage();          }
  elsif ($action eq 'Curation Statistics Options Page') {  &printCurationStatisticsOptionsPage();   }
  elsif ($action eq 'listCurationStatisticsPapersPage') {  &listCurationStatisticsPapersPage();     }
  elsif ($action eq 'printDescriptionOfLabelPage') {       &printDescriptionOfLabelPage();          }

  &printFooter();
}

sub printFormOpen {  print qq(<form name='form1' method="post" action="curation_status.cgi">\n); }
sub printFormClose { print qq(</form>\n); }

sub printFrontPageLink { 
  my ($action) = @_;
  if ($action ne 'none') {
    print qq(<b>$action</b> <a href="curation_status.cgi">Back to Main Page</a><br />\n); }
} # sub printFrontPageLink

sub firstPage {
  &printFormOpen();
  print qq(<table border="0">\n);

  my $ip = $query->remote_host();               # get ip address
  my $curator_by_ip = '';
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[0]) { $curator_by_ip = $row[0]; }

  print qq(<tr><td valign="top">Name</td><td><select name="select_curator" size="); print scalar keys %curators; print qq(">\n);
  foreach my $curator_two (keys %curators) {        # display curators in alphabetical (tied hash) order, if IP matches existing ip record, select it
    if ($curator_by_ip eq $curator_two) { print "<option value=\"$curator_two\" selected=\"selected\">$curators{$curator_two}</option>\n"; }
    else { print "<option value=\"$curator_two\">$curators{$curator_two}</option>\n"; } }
  print qq(</select></td></tr>);

  print qq(<tr><td>Check Specific Paper or Topic</td>\n);
  print qq(<td><input type="submit" name="action" value="Specific Paper Page"></td></tr>\n);
  print qq(<tr><td>Enter Curator Results</td>\n);
  print qq(<td><input type="submit" name="action" value="Add Results Page"></td></tr>\n);
  print qq(<tr><td>Curation Statistics</td>\n);
  print qq(<td><input type="submit" name="action" value="Curation Statistics Page"></td>\n);
  print qq(<input type="hidden" name="checkbox_all_datatypes"  value="all">);		# if looking at statistics page from front page use all datatypes
  print qq(<input type="hidden" name="checkbox_all_flagging_methods"  value="all">);	# if looking at statistics page from front page use all flagging methods
  print qq(<td><input type="submit" name="action" value="Curation Statistics Options Page"></td></tr>\n);
  print qq(<tr><td>Documentation</td><td colspan="2"><font size="-1"><a href="http://wiki.wormbase.org/index.php/New_2012_Curation_Status">http://wiki.wormbase.org/index.php/New_2012_Curation_Status</a></font></td></tr>\n);
  print qq(</table>\n);
  &printFormClose();
} # sub firstPage

sub updateWormCurator {                                 # update two_curator_ip for this curator and ip
  my ($curator_two) = @_;
  my $ip = $query->remote_host();               # get ip address
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip' AND joinkey = '$curator_two';" );
  $result->execute;
  my @row = $result->fetchrow;
  unless ($row[0]) {
    $result = $dbh->do( "DELETE FROM two_curator_ip WHERE two_curator_ip = '$ip' ;" );
    $result = $dbh->do( "INSERT INTO two_curator_ip VALUES ('$curator_two', '$ip')" );
} } # sub updateWormCurator


sub printHiddenCurator {
  if ($curator) { 
      print qq(<input type="hidden" name="select_curator"  value="$curator"  ><br />); }
    else { 
      print qq(<br/><span style="color: red">ERROR : you must choose a curator, go </span>\n);
      &printFrontPageLink(); die;  } } 

sub printSpecificPaperPage {
  &printFormOpen();
  &printHiddenCurator();
  &printTextareaSpecificPapers('');
  &printSelectTopics();
  &printCheckboxesDatatype('off');
  &printCheckboxesCurationSources('all');
  &printPaperOptions();
  &printSubmitGetResults();
  &printFormClose();
} # sub printSpecificPaperPage

sub printAddResultsPage {
  &printAddSection('', '', '', '', '', '', '');
} # sub printAddResultsPage

sub listCurationStatisticsPapersPage {
  &printFormOpen();
  &printHiddenCurator();
  my ($papers) = &printListCurationStatisticsPapers();
  &printTextareaSpecificPapers($papers);
  &printSelectTopics();
  &printSubmitGetResults();
  ($oop, my $listDatatype) = &getHtmlVar($query, "listDatatype");
  &printCheckboxesDatatype($listDatatype);
  &printCheckboxesCurationSources('all');
  &printPaperOptions();
  &printSubmitGetResults();
  &printFormClose();
} # sub listCurationStatisticsPapersPage

sub printDescriptionOfLabelPage {
  &printFormOpen();
  &populateStatisticsHashToDescription();
  ($oop, my $method) = &getHtmlVar($query, "method");
  my $description = 'no description for ' . $method;
  if ($statsHashToDescription{$method}) { $description = $statsHashToDescription{$method}; }
  print "$description";
  &printFormClose();
} # sub printDescriptionOfLabelPage

sub getHashLevel {			# given an array of keys, get the hash reference to that level of hash.  e.g. %h @a = qw( 1 2 ) => $h{1}{2}
  my ($hash_ref, $arrayOfKeys_ref) = @_;
  my @arrayOfKeys = @$arrayOfKeys_ref;
  if (scalar @arrayOfKeys == 0) { return $hash_ref; }
  my $subkey = shift @arrayOfKeys;
  my ($desiredHash_ref) = &getHashLevel($hash_ref->{$subkey}, \@arrayOfKeys);
  my %asdf = %$desiredHash_ref;
  return $desiredHash_ref;
} # sub getHashLevel

sub printListCurationStatisticsPapers {
  ($oop, my $listDatatype) = &getHtmlVar($query, "listDatatype");
  ($oop, my $method)   = &getHtmlVar($query, "method");
  $chosenPapers{all}++;
  my @datatypesToShow; push @datatypesToShow, $listDatatype; $chosenDatatypes{$listDatatype}++;
  &populateStatisticsHashToLabel();
  &populateCuratablePapers(); 
  &populateCuratedPapers();
  my @flaggingMethods;						# when calculating any or all methods, only want papers for these flagging methods
  ($oop, my $displayCfp) = &getHtmlVar($query, "checkbox_cfp");
  if ($displayCfp) { &populateCfpData(); push @flaggingMethods, 'checkbox_cfp'; }
  ($oop, my $displayAfp) = &getHtmlVar($query, "checkbox_afp");
  if ($displayAfp) { &populateAfpData(); push @flaggingMethods, 'checkbox_afp'; }
  ($oop, my $displaySvm) = &getHtmlVar($query, "checkbox_svm");
  if ($displaySvm) { &populateSvmData(); push @flaggingMethods, 'checkbox_svm'; }

  if      ($method eq 'afpemailed') {		&getCurationStatisticsAfpEmailed(    \@datatypesToShow ); }
    elsif ($method eq 'afp') {			&getCurationStatisticsAfpFlagged(    \@datatypesToShow ); }
    elsif ($method =~ m/afp neg/) {		&getCurationStatisticsAfpNeg(        \@datatypesToShow ); }
    elsif ($method =~ m/afp pos/) {		&getCurationStatisticsAfpPos(        \@datatypesToShow ); }
    elsif ($method eq 'cfp') {			&getCurationStatisticsCfpFlagged(    \@datatypesToShow ); }
    elsif ($method =~ m/cfp neg/) {		&getCurationStatisticsCfpNeg(        \@datatypesToShow ); }
    elsif ($method =~ m/cfp pos/) {		&getCurationStatisticsCfpPos(        \@datatypesToShow ); }
    elsif ($method eq 'svmnotdone') {		&getCurationStatisticsSvmNd(         \@datatypesToShow ); }
    elsif ($method =~ m/^svm/) {		&getCurationStatisticsSvm(           \@datatypesToShow ); }
    elsif ( ($method =~ m/^any/) ||
            ($method =~ m/^int/) ) {		&getCurationStatisticsSvmNd(         \@datatypesToShow);
                                                &getCurationStatisticsSvm(           \@datatypesToShow);
                                                &getCurationStatisticsAfpEmailed(    \@datatypesToShow);
                                                &getCurationStatisticsAfpFlagged(    \@datatypesToShow);
                                                &getCurationStatisticsAfpPos(        \@datatypesToShow );
                                                &getCurationStatisticsAfpNeg(        \@datatypesToShow );
                                                &getCurationStatisticsCfpFlagged(    \@datatypesToShow);
                                                &getCurationStatisticsCfpPos(        \@datatypesToShow );
                                                &getCurationStatisticsCfpNeg(        \@datatypesToShow );
                                                &getCurationStatisticsAny(           \@datatypesToShow, \@flaggingMethods ); }
    elsif ($method eq 'allcur') {		&getCurationStatisticsAllCurated(    \@datatypesToShow ); }
    elsif ($method eq 'allval') {		&getCurationStatisticsAllVal(        \@datatypesToShow ); }
    elsif ($method =~ m/^allval pos/) {		&getCurationStatisticsAllValPos(     \@datatypesToShow ); }
    elsif ($method =~ m/^allval neg/) {		&getCurationStatisticsAllValNeg(     \@datatypesToShow ); }
    elsif ($method =~ m/^allval conf/) {	&getCurationStatisticsAllValConf(    \@datatypesToShow ); }

  my @arrayOfKeys = split/ /, $method;
  my ($hash_ref) = &getHashLevel(\%curStats, \@arrayOfKeys);
  my $amount = scalar keys %{ $hash_ref->{$listDatatype}{'papers'} };
  my $listDatatypeToPrint = $listDatatype; if ($listDatatypeToPrint eq 'allSame') { $listDatatypeToPrint = ''; }
  print qq($amount papers have $listDatatypeToPrint $statsHashToLabel{$method} :<br />\n);
  my @joinkeys;
  foreach my $joinkey (sort keys %{ $hash_ref->{$listDatatype}{'papers'} }) { 
    push @joinkeys, $joinkey;
    my $link = "curation_status.cgi?select_curator=$curator&specific_papers=WBPaper$joinkey&checkbox_$listDatatype=$listDatatype&checkbox_filteron_primary=on&checkbox_svm=on&checkbox_cfp=on&checkbox_afp=on&checkbox_oa=on&checkbox_cur=on&papers_per_page=10&checkbox_journal=on&checkbox_pmid=on&checkbox_pdf=on&checkbox_primary=on&action=Get+Results";
    print qq(<a href="$link" target="new">$joinkey</a> );
  }
  print qq(<br/><br/>);
  my $joinkeys = join" ", @joinkeys;
  return $joinkeys;
} # sub printListCurationStatisticsPapers

sub printCurationStatisticsOptionsPage {
  &printFormOpen();
  &printHiddenCurator();
  &printCheckboxesDatatype('all');
  &printCheckboxesCurationSources('flagging');
  print qq(<input type="submit" name="action" value="Curation Statistics Page">\n);
  &printFormClose();
} # sub printCurationStatisticsOptionsPage

sub printCurationStatisticsPage {
  &printFormOpen();
  &printHiddenCurator();
  &printCurationStatisticsTable();
  &printFormClose();
} # sub printCurationStatisticsPage

sub printCurationStatisticsTable {
  my ($showTimes, $startprintCurationStatisticsTable, $start, $end, $diff) = (0, '', '', '', '');
  if ($showTimes) { $startprintCurationStatisticsTable = time; $start = $startprintCurationStatisticsTable; }

  $chosenPapers{all}++;
  my @datatypesToShow;

  &populateStatisticsHashToLabel();

  ($oop, my $all_datatypes_checkbox) = &getHtmlVar($query, "checkbox_all_datatypes");
  unless ($all_datatypes_checkbox) { $all_datatypes_checkbox = ''; }
  ($oop, my $all_datatypes_with_no_data_checkbox) = &getHtmlVar($query, "checkbox_all_datatypes_with_no_data");
  unless ($all_datatypes_with_no_data_checkbox) { $all_datatypes_with_no_data_checkbox = ''; }
  foreach my $datatype (sort keys %datatypes) {		# don't tie %datatypes
    ($oop, my $chosen) = &getHtmlVar($query, "checkbox_$datatype");
    if ($all_datatypes_with_no_data_checkbox eq 'all') { $chosen = $datatype; }	# if all datatypes checkbox was selected, set that datatype's chosen to that datatype
    if ($all_datatypes_checkbox eq 'all') { $chosen = $datatype; }	# if all datatypes checkbox was selected, set that datatype's chosen to that datatype
    if ($chosen) { $chosenDatatypes{$chosen}++; push @datatypesToShow, $datatype; }
  } # foreach my $datatype (sort %datatypes)
  
  my $datatypesToShowAmount = scalar @datatypesToShow;
  my $rowNameTdWidth = '600'; my $datatypeTdWidth = '120'; 
  my $labelRightFlag = 0; if ($datatypesToShowAmount > 6) { $labelRightFlag++; }
  my $tableWidth = $rowNameTdWidth + $datatypesToShowAmount * $datatypeTdWidth;
  if ($labelRightFlag) { $tableWidth = 2 * $rowNameTdWidth + $datatypesToShowAmount * $datatypeTdWidth; }
  print qq(<table width="$tableWidth" class="bordered" border="1">\n);

  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "beforePopulateCuratablePapers   $diff<br>"; }
  &populateCuratablePapers(); 
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "populateCuratablePapers   $diff<br>"; }
  &populateCuratedPapers();
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "populateCuratedPapers   $diff<br>"; }

  my @flaggingMethods;						# when calculating any or all methods, only want papers for these flagging methods
  ($oop, my $displayAll) = &getHtmlVar($query, "checkbox_all_flagging_methods");
  ($oop, my $displayCfp) = &getHtmlVar($query, "checkbox_cfp");
  if ( ($displayAll) || ($displayCfp) ) { &populateCfpData();      push @flaggingMethods, 'checkbox_cfp'; }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "populateCfpData $diff<br>"; }
  ($oop, my $displayAfp) = &getHtmlVar($query, "checkbox_afp");                                     
  if ( ($displayAll) || ($displayAfp) ) { &populateAfpData();      push @flaggingMethods, 'checkbox_afp'; }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "populateAfpData $diff<br>"; }
  ($oop, my $displaySvm) = &getHtmlVar($query, "checkbox_svm");                                     
  if ( ($displayAll) || ($displaySvm) ) { &populateSvmData();      push @flaggingMethods, 'checkbox_svm'; }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "populateSvmData   $diff<br>"; }
  my $flaggingMethods = join"=on&", @flaggingMethods; $flaggingMethods .= '=on';

  &printCurationStatisticsDatatypes(                \@datatypesToShow, $rowNameTdWidth, $datatypeTdWidth, $labelRightFlag);
  &printCurationStatisticsPapersCuratable(          \@datatypesToShow, $labelRightFlag);
  &printCurationStatisticsObjectsCurated(           \@datatypesToShow, $labelRightFlag);
  &printCurationStatisticsObjectsPerPaperCurated(   \@datatypesToShow, $labelRightFlag);

  $curStats{'dividerallval'}{'allSame'}{'countPap'} = 'blank';
  tie %{ $curStats{'allcur'} }, "Tie::IxHash";			# make all section appear in this order by tying it
  tie %{ $curStats{'allval'} }, "Tie::IxHash";			# make all section appear in this order by tying it
  $curStats{'dividerany'}{'allSame'}{'countPap'} = 'blank';
#   tie %{ $curStats{'any'} }, "Tie::IxHash";			# not needed, 'any' only has 'pos'
  tie %{ $curStats{'any'}{'pos'} }, "Tie::IxHash";		# make any section appear in this order by tying it, though it will get populated last
  $curStats{'dividerint'}{'allSame'}{'countPap'} = 'blank';
  tie %{ $curStats{'int'}{'pos'} }, "Tie::IxHash";		# make any section appear in this order by tying it, though it will get populated last

  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "printCurationStatistics Datatypes / Objects   $diff<br>"; }

  &getCurationStatisticsAllCurated(         \@datatypesToShow ); 
  &getCurationStatisticsAllVal(             \@datatypesToShow );  
  &getCurationStatisticsAllValPos(          \@datatypesToShow );  
  &getCurationStatisticsAllValNeg(          \@datatypesToShow );  
  &getCurationStatisticsAllValConf(         \@datatypesToShow );  

  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "getCurationtStatisticsAll   $diff<br>"; }
  if ( ($displayAll) || ($displaySvm) ) { 
    &getCurationStatisticsSvmNd(            \@datatypesToShow );
    &getCurationStatisticsSvm(              \@datatypesToShow ); }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "getStatsSvm   $diff<br>"; }

  if ( ($displayAll) || ($displayAfp) ) { 
    &getCurationStatisticsAfpEmailed(       \@datatypesToShow );
    &getCurationStatisticsAfpFlagged(       \@datatypesToShow );
    &getCurationStatisticsAfpPos(           \@datatypesToShow );
    &getCurationStatisticsAfpNeg(           \@datatypesToShow ); }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "getStatsAfp   $diff<br>"; }

  if ( ($displayAll) || ($displayCfp) ) { 
    &getCurationStatisticsCfpFlagged(       \@datatypesToShow );
    &getCurationStatisticsCfpPos(           \@datatypesToShow );
    &getCurationStatisticsCfpNeg(           \@datatypesToShow ); }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "getStatsCfp   $diff<br>"; }

  &getCurationStatisticsAny(                \@datatypesToShow, \@flaggingMethods ); 
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "getStatsAny   $diff<br>"; }

  my @labelKeys;					# labelKeys will be created here
  my $depth = 0;					# recursion depth into hash
  &recurseCurStats(\%curStats, \@labelKeys, $depth, \@datatypesToShow, $flaggingMethods, $labelRightFlag );
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "recurseCurStats   $diff<br>"; }

  &printCurationStatisticsDatatypes(                \@datatypesToShow, $rowNameTdWidth, $datatypeTdWidth, $labelRightFlag);
  print "</table>\n";
  if ($showTimes) { $end = time; $diff = $end - $startprintCurationStatisticsTable; print "printCurationStatisticsTable $diff<br>"; }
} # sub printCurationStatisticsTable


sub recurseCurStats {					# recurse through %curStats to print row of stats 
  my ($hash, $labelKeys_ref, $depth, $datatypesToShow_ref, $flaggingMethods, $labelRightFlag) =   @_;
  $depth++;						# one level deeper, track for indentation
  my @datatypesToShow = @$datatypesToShow_ref;
  foreach my $key ( keys %{$hash} ){			# each key in that level of %curStats
    my @labelKeys = @$labelKeys_ref;			# build label key by adding to array and joining with tabs
    push @labelKeys, $key;
    my $labelKeys = join" ", @labelKeys; 
    if ($statsHashToLabel{$labelKeys}) { 			# display for levels that have a display label
      print "<tr><td>";
      for (2 .. $depth) { print "&nbsp;&nbsp;&nbsp;&nbsp;"; }	# add indentation
      print qq(<a href="#" onclick="window.open('curation_status.cgi?action=printDescriptionOfLabelPage&method=$labelKeys', 'description', 'height=200,width=300'); return false;">$statsHashToLabel{$labelKeys}</a></td>);		# label
      my $colSpan = 1;
      my @datatypesHaveData; foreach (@datatypesToShow) { push @datatypesHaveData, $_; }	# make copy to avoid messing with this
      if ($hash->{$key}{'allSame'}) { $colSpan = scalar @datatypesToShow; @datatypesHaveData = ( 'allSame' ); }	# if all datatypes have same data show once in big colspan
      foreach my $datatype (@datatypesHaveData) {	# for each chosen datatype that has individual data
        my $tdCellData = '0';
        my $count = $hash->{$key}{$datatype}{'countPap'}; 
        if ($count) { $tdCellData = qq(<a href="curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=$curator&listDatatype=$datatype&method=$labelKeys&$flaggingMethods" target="new">$count</a>); }
        my $ratio = $hash->{$key}{$datatype}{'ratio'} ; 
        if ($ratio) { if ($ratio != 0) { $tdCellData .= " ; ${ratio}%"; } }
        if ($count) { if ($count eq 'blank') { $tdCellData = '&nbsp;'; } }
        print qq(<td colspan="$colSpan">$tdCellData</td>);
      } # foreach my $datatype (@datatypesHaveData)
      if ($labelRightFlag) {
        print "<td>"; for (2 .. $depth) { print "&nbsp;&nbsp;&nbsp;&nbsp;"; }	# add indentation
        print qq(<a href="#" onclick="window.open('curation_status.cgi?action=printDescriptionOfLabelPage&method=$labelKeys', 'description', 'height=200,width=300'); return false;">$statsHashToLabel{$labelKeys}</a></td>); }		# label	
      print "</tr>";
    } # if ($statsHashToLabel{$key})
    if (ref $hash->{$key} eq 'HASH') {
      &recurseCurStats($hash->{$key}, \@labelKeys, $depth, $datatypesToShow_ref, $flaggingMethods, $labelRightFlag); }
  } # foreach my $key ( keys %{$hash} )			# each key in that level of %curStats
} # sub recurseCurStats

sub getCurationStatisticsAny {
  my ($datatypesToShow_ref, $flaggingMethods_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my @flaggingMethods = @$flaggingMethods_ref;
  my $methodAmount = scalar @flaggingMethods;
  my $countCuratablePapers = scalar keys %curatablePapers;

  foreach my $datatype (@datatypesToShow) {
    my $countAnyFlagged    = scalar keys %{ $curStats{'any'}{$datatype}{papers} }; my $ratio = 0;
    $curStats{'any'}{$datatype}{'countPap'} = $countAnyFlagged;
    if ($countCuratablePapers > 0) { $ratio = $countAnyFlagged / $countCuratablePapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntFlagged    = scalar keys %{ $curStats{'int'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{$datatype}{'countPap'} = $countIntFlagged;
    if ($countCuratablePapers > 0) { $ratio = $countIntFlagged / $countCuratablePapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPos        = scalar keys %{ $curStats{'any'}{'pos'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{$datatype}{'countPap'}                      = $countAnyPos;
    if ($countAnyFlagged > 0) { $ratio = $countAnyPos / $countAnyFlagged * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPos        = scalar keys %{ $curStats{'int'}{'pos'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{$datatype}{'countPap'} = $countIntPos;
    if ($countIntFlagged > 0) { $ratio = $countIntPos / $countIntFlagged * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosVal     = scalar keys %{ $curStats{'any'}{'pos'}{'val'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'val'}{$datatype}{'countPap'}               = $countAnyPosVal;
    if ($countAnyPos > 0) { $ratio = $countAnyPosVal / $countAnyPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'val'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'val'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'val'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosVal     = scalar keys %{ $curStats{'int'}{'pos'}{'val'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'val'}{$datatype}{'countPap'} = $countIntPosVal;
    if ($countIntPos > 0) { $ratio = $countIntPosVal / $countIntPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosTP      = scalar keys %{ $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{'countPap'}         = $countAnyPosTP;
    if ($countAnyPosVal > 0) { $ratio = $countAnyPosTP / $countAnyPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosTP      = scalar keys %{ $curStats{'int'}{'pos'}{'val'}{'tp'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'val'}{'tp'}{$datatype}{'countPap'}         = $countIntPosTP;
    if ($countIntPosVal > 0) { $ratio = $countIntPosTP / $countIntPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'val'}{'tp'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosTpCur   = scalar keys %{ $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'}  = $countAnyPosTpCur;
    if ($countAnyPosTP > 0) { $ratio = $countAnyPosTpCur / $countAnyPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosTpCur   = scalar keys %{ $curStats{'int'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'}  = $countIntPosTpCur;
    if ($countIntPosTP > 0) { $ratio = $countIntPosTpCur / $countIntPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosTpNC    = scalar keys %{ $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = $countAnyPosTpNC;
    if ($countAnyPosTP > 0) { $ratio = $countAnyPosTpNC / $countAnyPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosTpNC    = scalar keys %{ $curStats{'int'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = $countIntPosTpNC;
    if ($countIntPosTP > 0) { $ratio = $countIntPosTpNC / $countIntPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosFP      = scalar keys %{ $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{'countPap'}         = $countAnyPosFP;
    if ($countAnyPosVal > 0) { $ratio = $countAnyPosFP / $countAnyPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosFP      = scalar keys %{ $curStats{'int'}{'pos'}{'val'}{'fp'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'val'}{'fp'}{$datatype}{'countPap'}         = $countIntPosFP;
    if ($countIntPosVal > 0) { $ratio = $countIntPosFP / $countIntPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'val'}{'fp'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosNV      = scalar keys %{ $curStats{'any'}{'pos'}{'nval'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'nval'}{$datatype}{'countPap'}              = $countAnyPosNV;
    if ($countAnyPos > 0) { $ratio = $countAnyPosNV / $countAnyPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'nval'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'nval'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosNV      = scalar keys %{ $curStats{'int'}{'pos'}{'nval'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'nval'}{$datatype}{'countPap'}              = $countIntPosNV;
    if ($countIntPos > 0) { $ratio = $countIntPosNV / $countIntPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countAnyPosNC      = scalar keys %{ $curStats{'any'}{'pos'}{'ncur'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'any'}{'pos'}{'ncur'}{$datatype}{'countPap'}              = $countAnyPosNC;
    if ($countAnyPos > 0) { $ratio = $countAnyPosNC / $countAnyPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'any'}{'pos'}{'ncur'}{$datatype}{'ratio'}    = $ratio;
    foreach my $joinkey (keys %{ $curStats{'any'}{'pos'}{'ncur'}{$datatype}{papers} }) { 
      if ($curStats{'any'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey} eq $methodAmount) { $curStats{'int'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; } }
    my $countIntPosNC      = scalar keys %{ $curStats{'int'}{'pos'}{'ncur'}{$datatype}{papers} }; $ratio = 0;
    $curStats{'int'}{'pos'}{'ncur'}{$datatype}{'countPap'}              = $countIntPosNC;
    if ($countIntPos > 0) { $ratio = $countIntPosNC / $countIntPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'int'}{'pos'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAny

sub getCurationStatisticsSvmNd {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my %noSvm; 
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %curatablePapers) { unless ($svmData{$datatype}{$joinkey}) { $noSvm{$datatype}{$joinkey}++; } } } 
  my $countCuratablePapers = scalar keys %curatablePapers;
  $curStats{'dividersvm'}{'allSame'}{'countPap'} = 'blank';
  tie %{ $curStats{'svmnotdone'} }, "Tie::IxHash";
  foreach my $datatype (@datatypesToShow) {
    my $countSvmNdPapers = scalar keys %{ $noSvm{$datatype} };
    my $ratio = 0;
    if ($countCuratablePapers > 0) { $ratio = $countSvmNdPapers / $countCuratablePapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $noSvm{$datatype} }) { $curStats{'svmnotdone'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svmnotdone'}{$datatype}{'countPap'} = scalar keys %{ $noSvm{$datatype} };
    $curStats{'svmnotdone'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsSvmNd

sub getCurationStatisticsSvm {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
	# negative : flagged, not validated, validated, true negative, false negative, FN curated, FN not curated, not curated minus validated negative OR not validated + FN not curated
  my %svmNeg; my %svmNegNV; my %svmNegVal; my %svmNegTN; my %svmNegFN; my %svmNegFnCur; my %svmNegFnNC; my %svmNegNC;
	# positive : flagged, not validated, validated, false positive, true positive, TP curated, TP not curated, not curated minus validated negative OR not validated + TP not curated
  my %svmPos; my %svmPosNV; my %svmPosVal; my %svmPosFP; my %svmPosTP; my %svmPosTpCur; my %svmPosTpNC; my %svmPosNC;
  my %svmHig; my %svmHigNV; my %svmHigVal; my %svmHigTP; my %svmHigFP; my %svmHigTpCur; my %svmHigTpNC; my %svmHigNC;
  my %svmMed; my %svmMedNV; my %svmMedVal; my %svmMedTP; my %svmMedFP; my %svmMedTpCur; my %svmMedTpNC; my %svmMedNC;
  my %svmLow; my %svmLowNV; my %svmLowVal; my %svmLowTP; my %svmLowFP; my %svmLowTpCur; my %svmLowTpNC; my %svmLowNC;

  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %{ $svmData{$datatype} }) { 
      my $svmVal = $svmData{$datatype}{$joinkey};
      if ($svmVal eq 'NEG') {
        $svmNeg{$datatype}{$joinkey}++;
        if ($valNeg{$datatype}{$joinkey}) {      $svmNegTN{$datatype}{$joinkey}++; $svmNegVal{$datatype}{$joinkey}++; }
          elsif ($valPos{$datatype}{$joinkey}) { $svmNegFN{$datatype}{$joinkey}++; $svmNegVal{$datatype}{$joinkey}++;
            if ($valCur{$datatype}{$joinkey}) {  $svmNegFnCur{$datatype}{$joinkey}++; }
              else                            {  $svmNegFnNC{$datatype}{$joinkey}++; $svmNegNC{$datatype}{$joinkey}++; } }
          else {                                 $svmNegNV{$datatype}{$joinkey}++; $svmNegNC{$datatype}{$joinkey}++; } }
      elsif ($svmVal eq 'low') {
        $svmPos{$datatype}{$joinkey}++; $svmLow{$datatype}{$joinkey}++;
        if ($valNeg{$datatype}{$joinkey}) {      $svmPosVal{$datatype}{$joinkey}++; $svmPosFP{$datatype}{$joinkey}++;
                                                 $svmLowVal{$datatype}{$joinkey}++; $svmLowFP{$datatype}{$joinkey}++; }
          elsif ($valPos{$datatype}{$joinkey}) { $svmPosVal{$datatype}{$joinkey}++; $svmPosTP{$datatype}{$joinkey}++;
                                                 $svmLowVal{$datatype}{$joinkey}++; $svmLowTP{$datatype}{$joinkey}++;
            if ($valCur{$datatype}{$joinkey}) {  $svmPosTpCur{$datatype}{$joinkey}++; $svmLowTpCur{$datatype}{$joinkey}++; }
              else                            {   $svmPosTpNC{$datatype}{$joinkey}++; $svmPosNC{$datatype}{$joinkey}++;
                                                  $svmLowTpNC{$datatype}{$joinkey}++; $svmLowNC{$datatype}{$joinkey}++; } }
          else {                                  $svmPosNV{$datatype}{$joinkey}++; $svmLowNV{$datatype}{$joinkey}++;
                                                  $svmPosNC{$datatype}{$joinkey}++; $svmLowNC{$datatype}{$joinkey}++; } }
      elsif ($svmVal eq 'medium') { 
        $svmPos{$datatype}{$joinkey}++; $svmMed{$datatype}{$joinkey}++;
        if ($valNeg{$datatype}{$joinkey}) {      $svmPosVal{$datatype}{$joinkey}++; $svmPosFP{$datatype}{$joinkey}++;
                                                 $svmMedVal{$datatype}{$joinkey}++; $svmMedFP{$datatype}{$joinkey}++; }
          elsif ($valPos{$datatype}{$joinkey}) { $svmPosVal{$datatype}{$joinkey}++; $svmPosTP{$datatype}{$joinkey}++;
                                                 $svmMedVal{$datatype}{$joinkey}++; $svmMedTP{$datatype}{$joinkey}++;
            if ($valCur{$datatype}{$joinkey}) {  $svmPosTpCur{$datatype}{$joinkey}++; $svmMedTpCur{$datatype}{$joinkey}++; }
              else                            {   $svmPosTpNC{$datatype}{$joinkey}++; $svmPosNC{$datatype}{$joinkey}++;
                                                  $svmMedTpNC{$datatype}{$joinkey}++; $svmMedNC{$datatype}{$joinkey}++; } }
          else {                                  $svmPosNV{$datatype}{$joinkey}++; $svmMedNV{$datatype}{$joinkey}++;
                                                  $svmPosNC{$datatype}{$joinkey}++; $svmMedNC{$datatype}{$joinkey}++; } }
      elsif ($svmVal eq 'high') { 
        $svmPos{$datatype}{$joinkey}++; $svmHig{$datatype}{$joinkey}++;
        if ($valNeg{$datatype}{$joinkey}) {      $svmPosVal{$datatype}{$joinkey}++; $svmPosFP{$datatype}{$joinkey}++;
                                                 $svmHigVal{$datatype}{$joinkey}++; $svmHigFP{$datatype}{$joinkey}++; }
          elsif ($valPos{$datatype}{$joinkey}) { $svmPosVal{$datatype}{$joinkey}++; $svmPosTP{$datatype}{$joinkey}++;
                                                 $svmHigVal{$datatype}{$joinkey}++; $svmHigTP{$datatype}{$joinkey}++;
            if ($valCur{$datatype}{$joinkey}) {  $svmPosTpCur{$datatype}{$joinkey}++; $svmHigTpCur{$datatype}{$joinkey}++; }
              else                            {   $svmPosTpNC{$datatype}{$joinkey}++; $svmPosNC{$datatype}{$joinkey}++;
                                                  $svmHigTpNC{$datatype}{$joinkey}++; $svmHigNC{$datatype}{$joinkey}++; } }
          else {                                  $svmPosNV{$datatype}{$joinkey}++; $svmHigNV{$datatype}{$joinkey}++;
                                                  $svmPosNC{$datatype}{$joinkey}++; $svmHigNC{$datatype}{$joinkey}++; } }
  } } # foreach my $datatype (@datatypesToShow)

  my $countCuratablePapers = scalar keys %curatablePapers;

  tie %{ $curStats{'svm'} }, "Tie::IxHash";
  tie %{ $curStats{'svm'}{'pos'} }, "Tie::IxHash";
  tie %{ $curStats{'svm'}{'hig'} }, "Tie::IxHash";
  tie %{ $curStats{'svm'}{'med'} }, "Tie::IxHash";
  tie %{ $curStats{'svm'}{'low'} }, "Tie::IxHash";
  tie %{ $curStats{'svm'}{'neg'} }, "Tie::IxHash";
  foreach my $datatype (@datatypesToShow) {
    my $countYesSvmPapers = scalar keys %{ $svmData{$datatype} };
    my $ratio = 0;
    if ($countCuratablePapers > 0) { $ratio = $countYesSvmPapers / $countCuratablePapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmData{$datatype} }) { $curStats{'svm'}{$datatype}{papers}{$joinkey}++;
							  $curStats{'any'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{$datatype}{'countPap'} = scalar keys %{ $svmData{$datatype} };
    $curStats{'svm'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPos = scalar keys %{ $svmPos{$datatype} };
    $ratio = 0;
    if ($countYesSvmPapers > 0) { $ratio = $countSvmPos / $countYesSvmPapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPos{$datatype} }) { $curStats{'svm'}{'pos'}{$datatype}{papers}{$joinkey}++; 
							 $curStats{'any'}{'pos'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{$datatype}{'countPap'} = scalar keys %{ $svmPos{$datatype} };
    $curStats{'svm'}{'pos'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosVal  = scalar keys %{ $svmPosVal{$datatype} };
    $ratio = 0;
    if ($countSvmPos > 0) { $ratio = $countSvmPosVal / $countSvmPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosVal{$datatype} }) { $curStats{'svm'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++;
							    $curStats{'any'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $svmPosVal{$datatype} };
    $curStats{'svm'}{'pos'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosTP  = scalar keys %{ $svmPosTP{$datatype} };
    $ratio = 0;
    if ($countSvmPosVal > 0) { $ratio = $countSvmPosTP / $countSvmPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosTP{$datatype} }) { $curStats{'svm'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++;
 							   $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'val'}{'tp'}{$datatype}{'countPap'} = scalar keys %{ $svmPosTP{$datatype} };
    $curStats{'svm'}{'pos'}{'val'}{'tp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosTpCur  = scalar keys %{ $svmPosTpCur{$datatype} };
    $ratio = 0;
    if ($countSvmPosTP > 0) { $ratio = $countSvmPosTpCur / $countSvmPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosTpCur{$datatype} }) { $curStats{'svm'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $svmPosTpCur{$datatype} };
    $curStats{'svm'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosTpNC  = scalar keys %{ $svmPosTpNC{$datatype} };
    $ratio = 0;
    if ($countSvmPosTP > 0) { $ratio = $countSvmPosTpNC / $countSvmPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosTpNC{$datatype} }) { $curStats{'svm'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++;
							     $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmPosTpNC{$datatype} };
    $curStats{'svm'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosFP  = scalar keys %{ $svmPosFP{$datatype} };
    $ratio = 0;
    if ($countSvmPosVal > 0) { $ratio = $countSvmPosFP / $countSvmPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosFP{$datatype} }) { $curStats{'svm'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++;
							   $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'val'}{'fp'}{$datatype}{'countPap'} = scalar keys %{ $svmPosFP{$datatype} };
    $curStats{'svm'}{'pos'}{'val'}{'fp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosNV  = scalar keys %{ $svmPosNV{$datatype} };
    $ratio = 0;
    if ($countSvmPos > 0) { $ratio = $countSvmPosNV / $countSvmPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosNV{$datatype} }) { $curStats{'svm'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++;
							   $curStats{'any'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $svmPosNV{$datatype} };
    $curStats{'svm'}{'pos'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmPosNC  = scalar keys %{ $svmPosNC{$datatype} };
    $ratio = 0; 
    if ($countSvmPos > 0) { $ratio = $countSvmPosNC / $countSvmPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmPosNC{$datatype} }) { $curStats{'svm'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; 
							   $curStats{'any'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'pos'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmPosNC{$datatype} };
    $curStats{'svm'}{'pos'}{'ncur'}{$datatype}{'ratio'}    = $ratio;


    my $countSvmHig = scalar keys %{ $svmHig{$datatype} };
    $ratio = 0;
    if ($countSvmPos > 0) { $ratio = $countSvmHig / $countSvmPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHig{$datatype} }) { $curStats{'svm'}{'hig'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{$datatype}{'countPap'} = scalar keys %{ $svmHig{$datatype} };
    $curStats{'svm'}{'hig'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigVal  = scalar keys %{ $svmHigVal{$datatype} };
    $ratio = 0;
    if ($countSvmHig > 0) { $ratio = $countSvmHigVal / $countSvmHig * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigVal{$datatype} }) { $curStats{'svm'}{'hig'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $svmHigVal{$datatype} };
    $curStats{'svm'}{'hig'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigTP  = scalar keys %{ $svmHigTP{$datatype} };
    $ratio = 0;
    if ($countSvmHigVal > 0) { $ratio = $countSvmHigTP / $countSvmHigVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigTP{$datatype} }) { $curStats{'svm'}{'hig'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'val'}{'tp'}{$datatype}{'countPap'} = scalar keys %{ $svmHigTP{$datatype} };
    $curStats{'svm'}{'hig'}{'val'}{'tp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigTpCur  = scalar keys %{ $svmHigTpCur{$datatype} };
    $ratio = 0;
    if ($countSvmHigTP > 0) { $ratio = $countSvmHigTpCur / $countSvmHigTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigTpCur{$datatype} }) { $curStats{'svm'}{'hig'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'hig'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $svmHigTpCur{$datatype} };
    $curStats{'svm'}{'hig'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigTpNC  = scalar keys %{ $svmHigTpNC{$datatype} };
    $ratio = 0;
    if ($countSvmHigTP > 0) { $ratio = $countSvmHigTpNC / $countSvmHigTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigTpNC{$datatype} }) { $curStats{'svm'}{'hig'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++;
							     $curStats{'any'}{'hig'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmHigTpNC{$datatype} };
    $curStats{'svm'}{'hig'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigFP  = scalar keys %{ $svmHigFP{$datatype} };
    $ratio = 0;
    if ($countSvmHigVal > 0) { $ratio = $countSvmHigFP / $countSvmHigVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigFP{$datatype} }) { $curStats{'svm'}{'hig'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'val'}{'fp'}{$datatype}{'countPap'} = scalar keys %{ $svmHigFP{$datatype} };
    $curStats{'svm'}{'hig'}{'val'}{'fp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigNV  = scalar keys %{ $svmHigNV{$datatype} };
    $ratio = 0;
    if ($countSvmHig > 0) { $ratio = $countSvmHigNV / $countSvmHig * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigNV{$datatype} }) { $curStats{'svm'}{'hig'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $svmHigNV{$datatype} };
    $curStats{'svm'}{'hig'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmHigNC  = scalar keys %{ $svmHigNC{$datatype} };
    $ratio = 0; 
    if ($countSvmHig > 0) { $ratio = $countSvmHigNC / $countSvmHig * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmHigNC{$datatype} }) { $curStats{'svm'}{'hig'}{'ncur'}{$datatype}{papers}{$joinkey}++; 
							   $curStats{'any'}{'hig'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'hig'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmHigNC{$datatype} };
    $curStats{'svm'}{'hig'}{'ncur'}{$datatype}{'ratio'}    = $ratio;


    my $countSvmMed = scalar keys %{ $svmMed{$datatype} };
    $ratio = 0;
    if ($countSvmPos > 0) { $ratio = $countSvmMed / $countSvmPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMed{$datatype} }) { $curStats{'svm'}{'med'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{$datatype}{'countPap'} = scalar keys %{ $svmMed{$datatype} };
    $curStats{'svm'}{'med'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedVal  = scalar keys %{ $svmMedVal{$datatype} };
    $ratio = 0;
    if ($countSvmMed > 0) { $ratio = $countSvmMedVal / $countSvmMed * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedVal{$datatype} }) { $curStats{'svm'}{'med'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $svmMedVal{$datatype} };
    $curStats{'svm'}{'med'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedTP  = scalar keys %{ $svmMedTP{$datatype} };
    $ratio = 0;
    if ($countSvmMedVal > 0) { $ratio = $countSvmMedTP / $countSvmMedVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedTP{$datatype} }) { $curStats{'svm'}{'med'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'val'}{'tp'}{$datatype}{'countPap'} = scalar keys %{ $svmMedTP{$datatype} };
    $curStats{'svm'}{'med'}{'val'}{'tp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedTpCur  = scalar keys %{ $svmMedTpCur{$datatype} };
    $ratio = 0;
    if ($countSvmMedTP > 0) { $ratio = $countSvmMedTpCur / $countSvmMedTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedTpCur{$datatype} }) { $curStats{'svm'}{'med'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'med'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $svmMedTpCur{$datatype} };
    $curStats{'svm'}{'med'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedTpNC  = scalar keys %{ $svmMedTpNC{$datatype} };
    $ratio = 0;
    if ($countSvmMedTP > 0) { $ratio = $countSvmMedTpNC / $countSvmMedTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedTpNC{$datatype} }) { $curStats{'svm'}{'med'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++;
							     $curStats{'any'}{'med'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmMedTpNC{$datatype} };
    $curStats{'svm'}{'med'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedFP  = scalar keys %{ $svmMedFP{$datatype} };
    $ratio = 0;
    if ($countSvmMedVal > 0) { $ratio = $countSvmMedFP / $countSvmMedVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedFP{$datatype} }) { $curStats{'svm'}{'med'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'val'}{'fp'}{$datatype}{'countPap'} = scalar keys %{ $svmMedFP{$datatype} };
    $curStats{'svm'}{'med'}{'val'}{'fp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedNV  = scalar keys %{ $svmMedNV{$datatype} };
    $ratio = 0;
    if ($countSvmMed > 0) { $ratio = $countSvmMedNV / $countSvmMed * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedNV{$datatype} }) { $curStats{'svm'}{'med'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $svmMedNV{$datatype} };
    $curStats{'svm'}{'med'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmMedNC  = scalar keys %{ $svmMedNC{$datatype} };
    $ratio = 0; 
    if ($countSvmMed > 0) { $ratio = $countSvmMedNC / $countSvmMed * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmMedNC{$datatype} }) { $curStats{'svm'}{'med'}{'ncur'}{$datatype}{papers}{$joinkey}++; 
							   $curStats{'any'}{'med'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'med'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmMedNC{$datatype} };
    $curStats{'svm'}{'med'}{'ncur'}{$datatype}{'ratio'}    = $ratio;


    my $countSvmLow = scalar keys %{ $svmLow{$datatype} };
    $ratio = 0;
    if ($countSvmPos > 0) { $ratio = $countSvmLow / $countSvmPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLow{$datatype} }) { $curStats{'svm'}{'low'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{$datatype}{'countPap'} = scalar keys %{ $svmLow{$datatype} };
    $curStats{'svm'}{'low'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowVal  = scalar keys %{ $svmLowVal{$datatype} };
    $ratio = 0;
    if ($countSvmLow > 0) { $ratio = $countSvmLowVal / $countSvmLow * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowVal{$datatype} }) { $curStats{'svm'}{'low'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $svmLowVal{$datatype} };
    $curStats{'svm'}{'low'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowTP  = scalar keys %{ $svmLowTP{$datatype} };
    $ratio = 0;
    if ($countSvmLowVal > 0) { $ratio = $countSvmLowTP / $countSvmLowVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowTP{$datatype} }) { $curStats{'svm'}{'low'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'val'}{'tp'}{$datatype}{'countPap'} = scalar keys %{ $svmLowTP{$datatype} };
    $curStats{'svm'}{'low'}{'val'}{'tp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowTpCur  = scalar keys %{ $svmLowTpCur{$datatype} };
    $ratio = 0;
    if ($countSvmLowTP > 0) { $ratio = $countSvmLowTpCur / $countSvmLowTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowTpCur{$datatype} }) { $curStats{'svm'}{'low'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'low'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $svmLowTpCur{$datatype} };
    $curStats{'svm'}{'low'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowTpNC  = scalar keys %{ $svmLowTpNC{$datatype} };
    $ratio = 0;
    if ($countSvmLowTP > 0) { $ratio = $countSvmLowTpNC / $countSvmLowTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowTpNC{$datatype} }) { $curStats{'svm'}{'low'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++;
							     $curStats{'any'}{'low'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmLowTpNC{$datatype} };
    $curStats{'svm'}{'low'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowFP  = scalar keys %{ $svmLowFP{$datatype} };
    $ratio = 0;
    if ($countSvmLowVal > 0) { $ratio = $countSvmLowFP / $countSvmLowVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowFP{$datatype} }) { $curStats{'svm'}{'low'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'val'}{'fp'}{$datatype}{'countPap'} = scalar keys %{ $svmLowFP{$datatype} };
    $curStats{'svm'}{'low'}{'val'}{'fp'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowNV  = scalar keys %{ $svmLowNV{$datatype} };
    $ratio = 0;
    if ($countSvmLow > 0) { $ratio = $countSvmLowNV / $countSvmLow * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowNV{$datatype} }) { $curStats{'svm'}{'low'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $svmLowNV{$datatype} };
    $curStats{'svm'}{'low'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmLowNC  = scalar keys %{ $svmLowNC{$datatype} };
    $ratio = 0; 
    if ($countSvmLow > 0) { $ratio = $countSvmLowNC / $countSvmLow * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmLowNC{$datatype} }) { $curStats{'svm'}{'low'}{'ncur'}{$datatype}{papers}{$joinkey}++; 
							   $curStats{'any'}{'low'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'low'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmLowNC{$datatype} };
    $curStats{'svm'}{'low'}{'ncur'}{$datatype}{'ratio'}    = $ratio;


    my $countSvmNeg = scalar keys %{ $svmNeg{$datatype} };
    $ratio = 0;
    if ($countYesSvmPapers > 0) { $ratio = $countSvmNeg / $countYesSvmPapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNeg{$datatype} }) { $curStats{'svm'}{'neg'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{$datatype}{'countPap'} = scalar keys %{ $svmNeg{$datatype} };
    $curStats{'svm'}{'neg'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegVal  = scalar keys %{ $svmNegVal{$datatype} };
    $ratio = 0;
    if ($countSvmNeg > 0) { $ratio = $countSvmNegVal / $countSvmNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegVal{$datatype} }) { $curStats{'svm'}{'neg'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $svmNegVal{$datatype} };
    $curStats{'svm'}{'neg'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegTN  = scalar keys %{ $svmNegTN{$datatype} };
    $ratio = 0;
    if ($countSvmNegVal > 0) { $ratio = $countSvmNegTN / $countSvmNegVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegTN{$datatype} }) { $curStats{'svm'}{'neg'}{'val'}{'tn'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'val'}{'tn'}{$datatype}{'countPap'} = scalar keys %{ $svmNegTN{$datatype} };
    $curStats{'svm'}{'neg'}{'val'}{'tn'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegFN  = scalar keys %{ $svmNegFN{$datatype} };
    $ratio = 0;
    if ($countSvmNegVal > 0) { $ratio = $countSvmNegFN / $countSvmNegVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegFN{$datatype} }) { $curStats{'svm'}{'neg'}{'val'}{'fn'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'val'}{'fn'}{$datatype}{'countPap'} = scalar keys %{ $svmNegFN{$datatype} };
    $curStats{'svm'}{'neg'}{'val'}{'fn'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegFnCur  = scalar keys %{ $svmNegFnCur{$datatype} };
    $ratio = 0;
    if ($countSvmNegFN > 0) { $ratio = $countSvmNegFnCur / $countSvmNegFN * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegFnCur{$datatype} }) { $curStats{'svm'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $svmNegFnCur{$datatype} };
    $curStats{'svm'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegFnNC  = scalar keys %{ $svmNegFnNC{$datatype} };
    $ratio = 0;
    if ($countSvmNegFN > 0) { $ratio = $countSvmNegFnNC / $countSvmNegFN * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegFnNC{$datatype} }) { $curStats{'svm'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmNegFnNC{$datatype} };
    $curStats{'svm'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegNV  = scalar keys %{ $svmNegNV{$datatype} };
    $ratio = 0;
    if ($countSvmNeg > 0) { $ratio = $countSvmNegNV / $countSvmNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegNV{$datatype} }) { $curStats{'svm'}{'neg'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $svmNegNV{$datatype} };
    $curStats{'svm'}{'neg'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countSvmNegNC  = scalar keys %{ $svmNegNC{$datatype} };
    $ratio = 0; 
    if ($countSvmNeg > 0) { $ratio = $countSvmNegNC / $countSvmNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $svmNegNC{$datatype} }) { $curStats{'svm'}{'neg'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'svm'}{'neg'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $svmNegNC{$datatype} };
    $curStats{'svm'}{'neg'}{'ncur'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsSvm


sub getCurationStatisticsAfpNeg {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my %afpNegNV; my %afpNegVal; my %afpNegTN; my %afpNegFN; my %afpNegFnCur; my %afpNegFnNC; my %afpNegNC;
	# negative and : not validated, validated, true negative, false negative, FN curated, FN not curated, not curated minus validated negative OR not validated + FN not curated
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (sort keys %{ $afpNeg{$datatype} }) {
      if ($valNeg{$datatype}{$joinkey}) {      $afpNegTN{$datatype}{$joinkey}++;    $afpNegVal{$datatype}{$joinkey}++; }
        elsif ($valPos{$datatype}{$joinkey}) { $afpNegFN{$datatype}{$joinkey}++;    $afpNegVal{$datatype}{$joinkey}++;
          if ($valCur{$datatype}{$joinkey}) {  $afpNegFnCur{$datatype}{$joinkey}++; }
            else                            {  $afpNegFnNC{$datatype}{$joinkey}++;  $afpNegNC{$datatype}{$joinkey}++; } }
        else {                                 $afpNegNV{$datatype}{$joinkey}++;    $afpNegNC{$datatype}{$joinkey}++; } } }
  tie %{ $curStats{'afp'}{'neg'} }, "Tie::IxHash";
  foreach my $datatype (@datatypesToShow) {
    my $countAfpFlagged   = scalar keys %{ $afpFlagged{$datatype} };
    my $countAfpNeg = scalar keys %{ $afpNeg{$datatype} };
    my $ratio = 0;
    if ($countAfpFlagged > 0) { $ratio = $countAfpNeg / $countAfpFlagged * 100; $ratio = FormatSigFigs($ratio, 2); }	# ($ratio) = &roundToPlaces($ratio, 2); # $ratio = sprintf "%.2f", $ratio;
    foreach my $joinkey (keys %{ $afpNeg{$datatype} }) { $curStats{'afp'}{'neg'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{$datatype}{'countPap'} = scalar keys %{ $afpNeg{$datatype} };
    $curStats{'afp'}{'neg'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegVal  = scalar keys %{ $afpNegVal{$datatype} };
    $ratio = 0;
    if ($countAfpNeg > 0) { $ratio = $countAfpNegVal / $countAfpNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegVal{$datatype} }) { $curStats{'afp'}{'neg'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $afpNegVal{$datatype} };
    $curStats{'afp'}{'neg'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegTN  = scalar keys %{ $afpNegTN{$datatype} };
    $ratio = 0;
    if ($countAfpNegVal > 0) { $ratio = $countAfpNegTN / $countAfpNegVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegTN{$datatype} }) { $curStats{'afp'}{'neg'}{'val'}{'tn'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'val'}{'tn'}{$datatype}{'countPap'} = scalar keys %{ $afpNegTN{$datatype} };
    $curStats{'afp'}{'neg'}{'val'}{'tn'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegFN  = scalar keys %{ $afpNegFN{$datatype} };
    $ratio = 0;
    if ($countAfpNegVal > 0) { $ratio = $countAfpNegFN / $countAfpNegVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegFN{$datatype} }) { $curStats{'afp'}{'neg'}{'val'}{'fn'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'val'}{'fn'}{$datatype}{'countPap'} = scalar keys %{ $afpNegFN{$datatype} };
    $curStats{'afp'}{'neg'}{'val'}{'fn'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegFnCur  = scalar keys %{ $afpNegFnCur{$datatype} };
    $ratio = 0;
    if ($countAfpNegFN > 0) { $ratio = $countAfpNegFnCur / $countAfpNegFN * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegFnCur{$datatype} }) { $curStats{'afp'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $afpNegFnCur{$datatype} };
    $curStats{'afp'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegFnNC  = scalar keys %{ $afpNegFnNC{$datatype} };
    $ratio = 0;
    if ($countAfpNegFN > 0) { $ratio = $countAfpNegFnNC / $countAfpNegFN * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegFnNC{$datatype} }) { $curStats{'afp'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $afpNegFnNC{$datatype} };
    $curStats{'afp'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegNV  = scalar keys %{ $afpNegNV{$datatype} };
    $ratio = 0; 
    if ($countAfpNeg > 0) { $ratio = $countAfpNegNV / $countAfpNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegNV{$datatype} }) { $curStats{'afp'}{'neg'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $afpNegNV{$datatype} };
    $curStats{'afp'}{'neg'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpNegNC  = scalar keys %{ $afpNegNC{$datatype} };
    $ratio = 0; 
    if ($countAfpNeg > 0) { $ratio = $countAfpNegNC / $countAfpNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpNegNC{$datatype} }) { $curStats{'afp'}{'neg'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'neg'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $afpNegNC{$datatype} };
    $curStats{'afp'}{'neg'}{'ncur'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAfpNeg

sub getCurationStatisticsAfpPos {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my %afpPosNV; my %afpPosVal; my %afpPosFP; my %afpPosTP; my %afpPosTpCur; my %afpPosTpNC; my %afpPosNC;
	# positive and : not validated, validated, false positive, true positive, TP curated, TP not curated, not curated minus validated negative OR not validated + TP not curated
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (sort keys %{ $afpPos{$datatype} }) {
      if ($valPos{$datatype}{$joinkey}) {      $afpPosTP{$datatype}{$joinkey}++;     $afpPosVal{$datatype}{$joinkey}++;
          if ($valCur{$datatype}{$joinkey}) {  $afpPosTpCur{$datatype}{$joinkey}++; }
            else                            {   $afpPosTpNC{$datatype}{$joinkey}++;  $afpPosNC{$datatype}{$joinkey}++; } }
        elsif ($valNeg{$datatype}{$joinkey}) { $afpPosFP{$datatype}{$joinkey}++;     $afpPosVal{$datatype}{$joinkey}++; }
        else {                                 $afpPosNV{$datatype}{$joinkey}++;     $afpPosNC{$datatype}{$joinkey}++; } } }
  tie %{ $curStats{'afp'}{'pos'} }, "Tie::IxHash";
  foreach my $datatype (@datatypesToShow) {
    my $countAfpFlagged   = scalar keys %{ $afpFlagged{$datatype} };
    my $countAfpPos = scalar keys %{ $afpPos{$datatype} };
    my $ratio = 0;
    if ($countAfpFlagged > 0) { $ratio = $countAfpPos / $countAfpFlagged * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPos{$datatype} }) {      $curStats{'afp'}{'pos'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{$datatype}{'countPap'}                      = scalar keys %{ $afpPos{$datatype} };
    $curStats{'afp'}{'pos'}{$datatype}{'ratio'}                         = $ratio;

    my $countAfpPosVal  = scalar keys %{ $afpPosVal{$datatype} };
    $ratio = 0;
    if ($countAfpPos > 0) { $ratio = $countAfpPosVal / $countAfpPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosVal{$datatype} }) {   $curStats{'afp'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'val'}{$datatype}{'countPap'}               = scalar keys %{ $afpPosVal{$datatype} };
    $curStats{'afp'}{'pos'}{'val'}{$datatype}{'ratio'}                  = $ratio;

    my $countAfpPosTP  = scalar keys %{ $afpPosTP{$datatype} };
    $ratio = 0;
    if ($countAfpPosVal > 0) { $ratio = $countAfpPosTP / $countAfpPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosTP{$datatype} }) {    $curStats{'afp'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'val'}{'tp'}{$datatype}{'countPap'}         = scalar keys %{ $afpPosTP{$datatype} };
    $curStats{'afp'}{'pos'}{'val'}{'tp'}{$datatype}{'ratio'}            = $ratio;

    my $countAfpPosTpCur  = scalar keys %{ $afpPosTpCur{$datatype} };
    $ratio = 0;
    if ($countAfpPosTP > 0) { $ratio = $countAfpPosTpCur / $countAfpPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosTpCur{$datatype} }) { $curStats{'afp'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'}  = scalar keys %{ $afpPosTpCur{$datatype} };
    $curStats{'afp'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}     = $ratio;

    my $countAfpPosTpNC  = scalar keys %{ $afpPosTpNC{$datatype} };
    $ratio = 0;
    if ($countAfpPosTP > 0) { $ratio = $countAfpPosTpNC / $countAfpPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosTpNC{$datatype} }) {  $curStats{'afp'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $afpPosTpNC{$datatype} };
    $curStats{'afp'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countAfpPosFP  = scalar keys %{ $afpPosFP{$datatype} };
    $ratio = 0;
    if ($countAfpPosVal > 0) { $ratio = $countAfpPosFP / $countAfpPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosFP{$datatype} }) {    $curStats{'afp'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'val'}{'fp'}{$datatype}{'countPap'}         = scalar keys %{ $afpPosFP{$datatype} };
    $curStats{'afp'}{'pos'}{'val'}{'fp'}{$datatype}{'ratio'}            = $ratio;

    my $countAfpPosNV  = scalar keys %{ $afpPosNV{$datatype} }; 
    $ratio = 0;
    if ($countAfpPos > 0) { $ratio = $countAfpPosNV / $countAfpPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosNV{$datatype} }) {    $curStats{'afp'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'nval'}{$datatype}{'countPap'}              = scalar keys %{ $afpPosNV{$datatype} };
    $curStats{'afp'}{'pos'}{'nval'}{$datatype}{'ratio'}                 = $ratio;

    my $countAfpPosNC  = scalar keys %{ $afpPosNC{$datatype} };
    $ratio = 0; 
    if ($countAfpPos > 0) { $ratio = $countAfpPosNC / $countAfpPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $afpPosNC{$datatype} }) {    $curStats{'afp'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'afp'}{'pos'}{'ncur'}{$datatype}{'countPap'}              = scalar keys %{ $afpPosNC{$datatype} };
    $curStats{'afp'}{'pos'}{'ncur'}{$datatype}{'ratio'}                 = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAfpPos

sub getCurationStatisticsAfpFlagged {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my $countAfpEmailed = scalar keys %afpEmailed;
  foreach my $datatype (sort keys %chosenDatatypes) {
    my $countAfpFlagged = scalar keys %{ $afpFlagged{$datatype} };
    foreach my $joinkey (keys %{ $afpFlagged{$datatype} }) { 
      $curStats{'any'}{$datatype}{papers}{$joinkey}++;
      $curStats{'afp'}{$datatype}{papers}{$joinkey}++; } 
    my $ratio = 0;
    if ($countAfpEmailed > 0) { $ratio = $countAfpFlagged / $countAfpEmailed * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'afp'}{$datatype}{'countPap'} = scalar keys %{ $afpFlagged{$datatype} };
    $curStats{'afp'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (sort keys %chosenDatatypes)
} # sub getCurationStatisticsAfpFlagged

sub getCurationStatisticsAfpEmailed {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my $countAfpEmailed      = scalar keys %afpEmailed;
  my $countCuratablePapers = scalar keys %curatablePapers;
  my $ratio = 0;
  if ($countCuratablePapers > 0) { $ratio = $countAfpEmailed / $countCuratablePapers * 100; $ratio = FormatSigFigs($ratio, 2); }
  my $datatype = 'allSame';
  $curStats{'dividerafp'}{$datatype}{'countPap'} = 'blank';
  foreach my $joinkey (keys %afpEmailed) { $curStats{'afpemailed'}{$datatype}{papers}{$joinkey}++; }
  $curStats{'afpemailed'}{$datatype}{'countPap'} = scalar keys %afpEmailed;
  $curStats{'afpemailed'}{$datatype}{'ratio'}    = $ratio;
} # sub getCurationStatisticsAfpEmailed



sub getCurationStatisticsCfpFlagged {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my $countCuratablePapers = scalar keys %curatablePapers;
  foreach my $datatype (sort keys %chosenDatatypes) {
    my $countCfpFlagged      = scalar keys %{ $cfpFlagged{$datatype} };
    my $ratio = 0;
    if ($countCuratablePapers > 0) { $ratio = $countCfpFlagged / $countCuratablePapers * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'dividercfp'}{$datatype}{'countPap'} = 'blank';
    foreach my $joinkey (keys %{ $cfpFlagged{$datatype} }) {
      $curStats{'any'}{$datatype}{papers}{$joinkey}++;
      $curStats{'cfp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{$datatype}{'countPap'} = scalar keys %{ $cfpFlagged{$datatype} };
    $curStats{'cfp'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (sort keys %chosenDatatypes)
} # sub getCurationStatisticsCfpFlagged

sub getCurationStatisticsCfpPos {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my %cfpPosNV; my %cfpPosVal; my %cfpPosFP; my %cfpPosTP; my %cfpPosTpCur; my %cfpPosTpNC; my %cfpPosNC;
	# positive and : not validated, validated, false positive, true positive, TP curated, TP not curated, not curated minus validated negative OR not validated + TP not curated
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (sort keys %{ $cfpPos{$datatype} }) {
      if ($valPos{$datatype}{$joinkey}) {      $cfpPosTP{$datatype}{$joinkey}++; $cfpPosVal{$datatype}{$joinkey}++;
          if ($valCur{$datatype}{$joinkey}) {  $cfpPosTpCur{$datatype}{$joinkey}++; }
            else                            {   $cfpPosTpNC{$datatype}{$joinkey}++; $cfpPosNC{$datatype}{$joinkey}++; } }
        elsif ($valNeg{$datatype}{$joinkey}) { $cfpPosFP{$datatype}{$joinkey}++; $cfpPosVal{$datatype}{$joinkey}++; }
        else {                                 $cfpPosNV{$datatype}{$joinkey}++; $cfpPosNC{$datatype}{$joinkey}++; } } }
  tie %{ $curStats{'cfp'}{'pos'} }, "Tie::IxHash";
  foreach my $datatype (@datatypesToShow) {
    my $countCfpFlagged = scalar keys %{ $cfpFlagged{$datatype} };
    my $countCfpPos = scalar keys %{ $cfpPos{$datatype} };
    my $ratio = 0; 
    if ($countCfpFlagged > 0) { $ratio = $countCfpPos / $countCfpFlagged * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPos{$datatype} }) {      $curStats{'cfp'}{'pos'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{$datatype}{'countPap'}                      = scalar keys %{ $cfpPos{$datatype} };
    $curStats{'cfp'}{'pos'}{$datatype}{'ratio'}                         = $ratio;

    my $countCfpPosVal  = scalar keys %{ $cfpPosVal{$datatype} };
    $ratio = 0;
    if ($countCfpPos > 0) { $ratio = $countCfpPosVal / $countCfpPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosVal{$datatype} }) {   $curStats{'cfp'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'val'}{$datatype}{'countPap'}               = scalar keys %{ $cfpPosVal{$datatype} };
    $curStats{'cfp'}{'pos'}{'val'}{$datatype}{'ratio'}                  = $ratio;

    my $countCfpPosTP  = scalar keys %{ $cfpPosTP{$datatype} };
    $ratio = 0;
    if ($countCfpPosVal > 0) { $ratio = $countCfpPosTP / $countCfpPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosTP{$datatype} }) {    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{$datatype}{'countPap'}         = scalar keys %{ $cfpPosTP{$datatype} };
    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{$datatype}{'ratio'}            = $ratio;

    my $countCfpPosTpCur  = scalar keys %{ $cfpPosTpCur{$datatype} };
    $ratio = 0;
    if ($countCfpPosTP > 0) { $ratio = $countCfpPosTpCur / $countCfpPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosTpCur{$datatype} }) { $curStats{'cfp'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $cfpPosTpCur{$datatype} };
    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpPosTpNC  = scalar keys %{ $cfpPosTpNC{$datatype} };
    $ratio = 0;
    if ($countCfpPosTP > 0) { $ratio = $countCfpPosTpNC / $countCfpPosTP * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosTpNC{$datatype} }) {  $curStats{'cfp'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++;
							      $curStats{'any'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $cfpPosTpNC{$datatype} };
    $curStats{'cfp'}{'pos'}{'val'}{'tp'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpPosFP  = scalar keys %{ $cfpPosFP{$datatype} };
    $ratio = 0;
    if ($countCfpPosVal > 0) { $ratio = $countCfpPosFP / $countCfpPosVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosFP{$datatype} }) {    $curStats{'cfp'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'val'}{'fp'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'val'}{'fp'}{$datatype}{'countPap'}         = scalar keys %{ $cfpPosFP{$datatype} };
    $curStats{'cfp'}{'pos'}{'val'}{'fp'}{$datatype}{'ratio'}            = $ratio;

    my $countCfpPosNV  = scalar keys %{ $cfpPosNV{$datatype} };
    $ratio = 0; 
    if ($countCfpPos > 0) { $ratio = $countCfpPosNV / $countCfpPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosNV{$datatype} }) {    $curStats{'cfp'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'nval'}{$datatype}{'countPap'}              = scalar keys %{ $cfpPosNV{$datatype} };
    $curStats{'cfp'}{'pos'}{'nval'}{$datatype}{'ratio'}                 = $ratio;

    my $countCfpPosNC  = scalar keys %{ $cfpPosNC{$datatype} };
    $ratio = 0; 
    if ($countCfpPos > 0) { $ratio = $countCfpPosNC / $countCfpPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpPosNC{$datatype} }) {    $curStats{'cfp'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; 
							      $curStats{'any'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'pos'}{'ncur'}{$datatype}{'countPap'}              = scalar keys %{ $cfpPosNC{$datatype} };
    $curStats{'cfp'}{'pos'}{'ncur'}{$datatype}{'ratio'}                 = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsCfpPos

sub getCurationStatisticsCfpNeg {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  my %cfpNegNV; my %cfpNegVal; my %cfpNegTN; my %cfpNegFN; my %cfpNegFnCur; my %cfpNegFnNC; my %cfpNegNC;
	# negative and : not validated, validated, true negative, false negative, FN curated, FN not curated, not curated minus validated negative OR not validated + FN not curated
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (sort keys %{ $cfpNeg{$datatype} }) {
      if ($valNeg{$datatype}{$joinkey}) {      $cfpNegTN{$datatype}{$joinkey}++; $cfpNegVal{$datatype}{$joinkey}++; }
        elsif ($valPos{$datatype}{$joinkey}) { $cfpNegFN{$datatype}{$joinkey}++; $cfpNegVal{$datatype}{$joinkey}++;
          if ($valCur{$datatype}{$joinkey}) {  $cfpNegFnCur{$datatype}{$joinkey}++; }
            else                            {   $cfpNegFnNC{$datatype}{$joinkey}++; $cfpNegNC{$datatype}{$joinkey}++; } }
        else {                                 $cfpNegNV{$datatype}{$joinkey}++; $cfpNegNC{$datatype}{$joinkey}++; } } }
  tie %{ $curStats{'cfp'}{'neg'} }, "Tie::IxHash";
  foreach my $datatype (@datatypesToShow) {
    my $countCfpFlagged = scalar keys %{ $cfpFlagged{$datatype} };
    my $countCfpNeg = scalar keys %{ $cfpNeg{$datatype} };
    my $ratio = 0; 
    if ($countCfpFlagged > 0) { $ratio = $countCfpNeg / $countCfpFlagged * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNeg{$datatype} }) { $curStats{'cfp'}{'neg'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{$datatype}{'countPap'} = scalar keys %{ $cfpNeg{$datatype} };
    $curStats{'cfp'}{'neg'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegVal  = scalar keys %{ $cfpNegVal{$datatype} };
    $ratio = 0;
    if ($countCfpNeg > 0) { $ratio = $countCfpNegVal / $countCfpNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegVal{$datatype} }) { $curStats{'cfp'}{'neg'}{'val'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'val'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegVal{$datatype} };
    $curStats{'cfp'}{'neg'}{'val'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegTN  = scalar keys %{ $cfpNegTN{$datatype} };
    $ratio = 0;
    if ($countCfpNegVal > 0) { $ratio = $countCfpNegTN / $countCfpNegVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegTN{$datatype} }) { $curStats{'cfp'}{'neg'}{'val'}{'tn'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'val'}{'tn'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegTN{$datatype} };
    $curStats{'cfp'}{'neg'}{'val'}{'tn'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegFN  = scalar keys %{ $cfpNegFN{$datatype} };
    $ratio = 0;
    if ($countCfpNegVal > 0) { $ratio = $countCfpNegFN / $countCfpNegVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegFN{$datatype} }) { $curStats{'cfp'}{'neg'}{'val'}{'fn'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'val'}{'fn'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegFN{$datatype} };
    $curStats{'cfp'}{'neg'}{'val'}{'fn'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegFnCur  = scalar keys %{ $cfpNegFnCur{$datatype} };
    $ratio = 0;
    if ($countCfpNegFN > 0) { $ratio = $countCfpNegFnCur / $countCfpNegFN * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegFnCur{$datatype} }) { $curStats{'cfp'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegFnCur{$datatype} };
    $curStats{'cfp'}{'neg'}{'val'}{'fn'}{'cur'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegFnNC  = scalar keys %{ $cfpNegFnNC{$datatype} };
    $ratio = 0;
    if ($countCfpNegFN > 0) { $ratio = $countCfpNegFnNC / $countCfpNegFN * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegFnNC{$datatype} }) { $curStats{'cfp'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegFnNC{$datatype} };
    $curStats{'cfp'}{'neg'}{'val'}{'fn'}{'ncur'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegNV  = scalar keys %{ $cfpNegNV{$datatype} };
    $ratio = 0; 
    if ($countCfpNeg > 0) { $ratio = $countCfpNegNV / $countCfpNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegNV{$datatype} }) { $curStats{'cfp'}{'neg'}{'nval'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'nval'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegNV{$datatype} };
    $curStats{'cfp'}{'neg'}{'nval'}{$datatype}{'ratio'}    = $ratio;

    my $countCfpNegNC  = scalar keys %{ $cfpNegNC{$datatype} };
    $ratio = 0; 
    if ($countCfpNeg > 0) { $ratio = $countCfpNegNC / $countCfpNeg * 100; $ratio = FormatSigFigs($ratio, 2); }
    foreach my $joinkey (keys %{ $cfpNegNC{$datatype} }) { $curStats{'cfp'}{'neg'}{'ncur'}{$datatype}{papers}{$joinkey}++; }
    $curStats{'cfp'}{'neg'}{'ncur'}{$datatype}{'countPap'} = scalar keys %{ $cfpNegNC{$datatype} };
    $curStats{'cfp'}{'neg'}{'ncur'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsCfpNeg


sub printCurationStatisticsObjectsCurated {
  my ($datatypesToShow_ref, $labelRightFlag) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  print qq(<tr><td>objects curated</td>);
  foreach my $datatype (@datatypesToShow) {
    my $countObjs = scalar keys %{ $objsCurated{$datatype} };
    if ($datatype eq 'rnai') { 			$countObjs += 59656; }
      elsif ($datatype eq 'otherexpr') {	$countObjs +=  2084; }	# add 2084 for chronograms for Daniela 2013 01 23
      elsif ($datatype eq 'picture') {  	$countObjs += 19052; }	# add 19052 for yanai pictures for Daniela 2013 01 24
    print "<td>$countObjs</td>";
  } # foreach my $datatype (@datatypesToShow)
  if ($labelRightFlag) { print qq(<td>objects curated</td>); }
  print "</tr>";
} # sub printCurationStatisticsObjectsCurated
sub printCurationStatisticsObjectsPerPaperCurated {
  my ($datatypesToShow_ref, $labelRightFlag) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  print qq(<tr><td>objects curated per paper</td>);		# this really means objects curated per curated paper, but Chris wants it labeled like this 2012 11 12
  foreach my $datatype (@datatypesToShow) {
    my $countObjs = scalar keys %{ $objsCurated{$datatype} };
    if ($datatype eq 'rnai') { 			$countObjs += 59656; }
      elsif ($datatype eq 'otherexpr') {	$countObjs +=  2084; }	# add 2084 for chronograms for Daniela 2013 01 23
      elsif ($datatype eq 'picture') {  	$countObjs += 19052; }	# add 19052 for yanai pictures for Daniela 2013 01 24
    my $countPapers = keys %{ $valCur{$datatype} };		# use curated papers, not validated papers
    my $ratio = 0;
    if ($countPapers > 0) { $ratio = $countObjs / $countPapers; $ratio = FormatSigFigs($ratio, 2); } # ($ratio) = &roundToPlaces($ratio, 2);
    print "<td>${ratio}</td>";
  } # foreach my $datatype (@datatypesToShow)
  if ($labelRightFlag) { print qq(<td>objects curated per paper</td>); }
  print "</tr>";
} # sub printCurationStatisticsObjectsPerPaperCurated

sub getCurationStatisticsAllCurated {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %{ $valCur{$datatype} }) { $curStats{'allcur'}{$datatype}{papers}{$joinkey}++; }
    my $count = keys %{ $valCur{$datatype} };
    $curStats{'allcur'}{$datatype}{'countPap'} = $count;
    $curStats{'allcur'}{$datatype}{'ratio'}    = 0;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAllCurated
sub getCurationStatisticsAllValConf {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %{ $conflict{$datatype} }) { $curStats{'allval'}{'conf'}{$datatype}{papers}{$joinkey}++; }
    my $countVal = keys %{ $validated{$datatype} };
    my $countConflict = keys %{ $conflict{$datatype} };
    my $ratio = 0;
    if ($countVal > 0) { $ratio = $countConflict / $countVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'allval'}{'conf'}{$datatype}{'countPap'} = $countConflict;
    $curStats{'allval'}{'conf'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAllValConf
sub getCurationStatisticsAllValNeg {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %{ $valNeg{$datatype} }) { $curStats{'allval'}{'neg'}{$datatype}{papers}{$joinkey}++; }
    my $countVal = keys %{ $validated{$datatype} };
    my $countNeg = keys %{ $valNeg{$datatype} };
    my $ratio = 0;
    if ($countVal > 0) { $ratio = $countNeg / $countVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'allval'}{'neg'}{$datatype}{'countPap'} = $countNeg;
    $curStats{'allval'}{'neg'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAllValNeg
sub getCurationStatisticsAllValPos {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %{ $valPos{$datatype} }) { 
      $curStats{'allval'}{'pos'}{$datatype}{papers}{$joinkey}++; 
      if ($valCur{$datatype}{$joinkey}) { $curStats{'allval'}{'pos'}{'cur'}{$datatype}{papers}{$joinkey}++; }
        else {                            $curStats{'allval'}{'pos'}{'ncur'}{$datatype}{papers}{$joinkey}++; } }
    my $countVal = keys %{ $validated{$datatype} };
    my $countPos = keys %{ $valPos{$datatype} };
    my $ratio = 0;
    if ($countVal > 0) { $ratio = $countPos / $countVal * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'allval'}{'pos'}{$datatype}{'countPap'} = $countPos;
    $curStats{'allval'}{'pos'}{$datatype}{'ratio'}    = $ratio;

    my $countPosCur  = keys %{ $curStats{'allval'}{'pos'}{'cur'}{$datatype}{papers} };
    $ratio = 0; if ($countPos > 0) { $ratio = $countPosCur / $countPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'allval'}{'pos'}{'cur'}{$datatype}{'countPap'}  = $countPosCur;
    $curStats{'allval'}{'pos'}{'cur'}{$datatype}{'ratio'}     = $ratio;

    my $countPosNcur = keys %{ $curStats{'allval'}{'pos'}{'ncur'}{$datatype}{papers} };
    $ratio = 0; if ($countPos > 0) { $ratio = $countPosNcur / $countPos * 100; $ratio = FormatSigFigs($ratio, 2); }
    $curStats{'allval'}{'pos'}{'ncur'}{$datatype}{'countPap'} = $countPosNcur;
    $curStats{'allval'}{'pos'}{'ncur'}{$datatype}{'ratio'}    = $ratio;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAllValPos
sub getCurationStatisticsAllVal {
  my ($datatypesToShow_ref) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  foreach my $datatype (@datatypesToShow) {
    foreach my $joinkey (keys %{ $validated{$datatype} }) { $curStats{'allval'}{$datatype}{papers}{$joinkey}++; }
    my $count = keys %{ $validated{$datatype} };
    $curStats{'allval'}{$datatype}{'countPap'} = $count;
    $curStats{'allval'}{$datatype}{'ratio'}    = 0;
  } # foreach my $datatype (@datatypesToShow)
} # sub getCurationStatisticsAllVal

sub printCurationStatisticsPapersCuratable {
  my ($datatypesToShow_ref, $labelRightFlag) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  print qq(<tr><td>curatable papers</td>);
  my $colspan = scalar @datatypesToShow;
  my $countCuratablePapers = scalar keys %curatablePapers;
  print qq(<td colspan="$colspan">$countCuratablePapers</td>);
  if ($labelRightFlag) { print qq(<td>curatable papers</td>); }
  print qq(</tr>\n);
} # sub printCurationStatisticsPapersCuratable

sub printCurationStatisticsDatatypes {
  my ($datatypesToShow_ref, $rowNameTdWidth, $datatypeTdWidth, $labelRightFlag) = @_;
  my @datatypesToShow = @$datatypesToShow_ref;
  print qq(<tr><th width="$rowNameTdWidth"></th>\n);
  foreach my $datatype (@datatypesToShow) {
    print qq(<th width="$datatypeTdWidth">$datatype</th>\n);
  } # foreach my $datatype (@datatypesToShow) 
  if ($labelRightFlag) { print qq(<th width="$rowNameTdWidth"></th>\n);	}
} # sub printCurationStatisticsDatatypes

sub printCheckboxesDatatype {
  my ($off_all_specific) = @_;		# state can be 'off' all checkboxes off, 'all' all on, or a specific named datatypes
  my %checked;
  foreach my $datatype (sort keys %chosenDatatypes) {
    my $checked_option = '';
    if ($off_all_specific eq 'off') { $checked_option = ''; }
      elsif ($off_all_specific eq 'all') { $checked_option = 'checked="checked"'; }
      elsif ($off_all_specific eq $datatype) { $checked_option = 'checked="checked"'; }
    $checked{$datatype} = $checked_option; }
  print qq(<br/>);
  print qq(datatypes :<br/>\n);
  print qq(<input type="checkbox" name="checkbox_all_datatypes" value="all">all datatypes<br/>\n);
  print qq(<input type="checkbox" name="checkbox_all_datatypes_with_data" value="all">all datatypes (with flag and/or data)<br/>\n);	# for Chris and Raymond, sometimes want all datatypes to show, even if they have neither data nor flags for that datatype
  foreach my $datatype (sort keys %datatypes) { 
    unless ($checked{$datatype}) { $checked{$datatype} = ''; }
    print qq(<input type="checkbox" name="checkbox_$datatype" $checked{$datatype} value="$datatype">$datatype<br/>\n);
  } # foreach my $datatype (sort keys %datatypes) 
  print qq(<br/>);
  print qq(<br/>);
} # sub printCheckboxesDatatype

sub printCheckboxesCurationSources {
  my ($which_checkboxes_to_show) = @_;		#   values can be : all / flagging (curation+validation+flagging vs. flagging_sources)
  print qq(curation sources :<br/>\n);
  if ($which_checkboxes_to_show eq 'all') {
    print qq(<input type="checkbox" name="checkbox_oa"     checked="checked">OA or other postgres<br/>\n);
    print qq(<input type="checkbox" name="checkbox_cur"    checked="checked">Curator uploaded cur_curdata<br/>\n);
  } # if ($which_checkboxes_to_show eq 'all')
  print qq(<input type="checkbox" name="checkbox_svm"      checked="checked">svm flags cur_svmdata<br/>\n);
  print qq(<input type="checkbox" name="checkbox_afp"      checked="checked">author first pass afp_<br/>\n);
  print qq(<input type="checkbox" name="checkbox_cfp"      checked="checked">curator first pass cfp_<br/>\n);
  print qq(<br/>);
} # sub printCheckboxesCurationSources

sub printPaperOptions {
  print qq(papers per page <input name="papers_per_page" value="10"><br/>\n);
  print qq(<input type="checkbox" name="checkbox_journal" checked="checked">show journal<br/>\n);
  print qq(<input type="checkbox" name="checkbox_pmid"    checked="checked">show pmid<br/>\n);
  print qq(<input type="checkbox" name="checkbox_pdf"     checked="checked">show pdf<br/>\n);
  print qq(<br/>);
} # sub printPaperOptions

sub printTextareaSpecificPapers {
  my ($papers_in_textarea) = @_;
  print qq(get specific papers (enter in format WBPaper00001234 or 00001234)<br/>);
  print qq(<textarea rows="4" cols="80" name="specific_papers">$papers_in_textarea</textarea><br/>\n);
  print qq(<br/>);
} # sub printTextareaSpecificPapers

sub printSelectTopics {
  print qq(Filter papers from list through a topic :<br/>);
  print qq(<select name="select_topic">);
  print qq(<option value="none">no topic, use all papers from textarea above</option>\n);
  my %topicIDs; my %topicIdToName;
#   $result = $dbh->prepare( "SELECT DISTINCT(pro_process.pro_process) FROM pro_process, pro_paper, pro_topicpaperstatus WHERE pro_process.joinkey = pro_paper.joinkey AND pro_process.joinkey = pro_topicpaperstatus.joinkey AND (pro_topicpaperstatus.pro_topicpaperstatus = 'unchecked' OR pro_topicpaperstatus.pro_topicpaperstatus = 'relevant') ORDER BY pro_process.pro_process" );
  $result = $dbh->prepare( "SELECT DISTINCT(pro_process.pro_process) FROM pro_process, pro_paper, pro_topicpaperstatus WHERE pro_process.joinkey = pro_paper.joinkey AND pro_process.joinkey = pro_topicpaperstatus.joinkey AND (pro_topicpaperstatus.pro_topicpaperstatus = 'relevant') ORDER BY pro_process.pro_process" );	# Chris no longer wants u nchecked papers, only relevant  2014 06 12
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $topicIDs{$row[0]}++; }
  my $topicIDs = join"','", sort keys %topicIDs;		# for all the topicIDs, get the name from the prt_processname
  $result = $dbh->prepare( "SELECT prt_processid.prt_processid, prt_processname.prt_processname FROM prt_processid, prt_processname WHERE prt_processid.joinkey = prt_processname.joinkey AND prt_processid.prt_processid IN ('$topicIDs')" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $topicIdToName{$row[0]} = $row[1]; }	# map wbprocess ids to their names for dropdown display
  foreach my $topic (sort keys %topicIdToName) { print qq(<option value="$topic $topicIdToName{$topic}">$topic $topicIdToName{$topic}</option>); }
  print qq(</select><br/>);
} # sub printSelectTopics

sub printSubmitGetResults { print qq(<input type="submit" name="action" value="Get Results"><br/>\n); }


sub printAddSection {
  my ($twonumForm, $datatypeForm, $donposnegForm, $paperResultsForm, $selcommentForm, $txtcommentForm) = @_;
  my $selected = '';
  &printFormOpen();
  &printHiddenCurator();
  print qq(Select your datatype :<br/>);
  print qq(<select name="select_datatype">);
  print qq(<option value=""             ></option>\n);
  foreach my $datatype (keys %datatypes) {
    if ($datatype eq $datatypeForm) { $selected = qq(selected="selected"); } else { $selected = ''; }
    print qq(<option value="$datatype" $selected>$datatype</option>\n); }
  print qq(</select><br/>);
  print qq(Select if the data is positive or negative :<br/>);
  my $select_size = scalar keys %donPosNegOptions;
  print qq(<select name="select_donposneg" size="$select_size">);
  foreach my $donposnegValue (keys %donPosNegOptions) {
    if ($donposnegForm eq $donposnegValue) { $selected = qq(selected="selected"); } else { $selected = ''; }
    print qq(<option value="$donposnegValue" $selected>$donPosNegOptions{$donposnegValue}</option>\n); }
  print qq(</select><br/>);
  print qq(Enter paper data here in the format "WBPaper00001234" (paper as a whole) with separate papers in separate lines.<br/>);
  print qq(<textarea name="textarea_paper_results" rows="6" cols="80">$paperResultsForm</textarea><br/>\n);
  print qq(Select your comment (optional) :<br/>);
  print qq(<select name="select_comment">);
  print qq(<option value=""             ></option>\n);
  foreach my $comment (keys %premadeComments) { 
    if ($comment eq $selcommentForm) { $selected = qq(selected="selected"); } else { $selected = ''; }
    print qq(<option value="$comment" $selected>$premadeComments{$comment}</option>\n); }
  print qq(</select><br/>);
  print qq(Enter a free text comment to associate with all papers above (optional) :<br/>);
  print qq(<textarea rows="4" cols="80" name="textarea_comment">$txtcommentForm</textarea><br/>);
  print qq(<input type="submit" name="action" value="Add Results"><br/>\n);
  &printFormClose();
} # sub printAddSection

sub submitNewResults {
  &printFormOpen();
  &printHiddenCurator();
  ($oop, my $trAmount) = &getHtmlVar($query, "trCounter");
  my %papersToAdd;
  my %curatorData;
  for my $i (1 .. $trAmount) {
    ($oop, my $curatorDonposneg)  = &getHtmlVar($query, "select_curator_donposneg_$i");
    next unless $curatorDonposneg;			# skip entries without a curator result for done / positive / negative
    ($oop, my $dropdownCurator)   = &getHtmlVar($query, "select_curator_curator_$i");
    my $activeCurator = $curator; if ($dropdownCurator) { $activeCurator = $dropdownCurator; }	# if a curator was chosen use that, otherwise use logged in curator
    ($oop, my $curatorSelComment) = &getHtmlVar($query, "select_curator_comment_$i");
    ($oop, my $curatorTxtComment) = &getHtmlVar($query, "textarea_curator_comment_$i");
    ($oop, my $joinkey)           = &getHtmlVar($query, "joinkey_$i");
    ($oop, my $datatype)          = &getHtmlVar($query, "datatype_$i");

    $papersToAdd{$datatype}{$joinkey}++;
    $curatorData{$joinkey}{$datatype}{curator}    = $activeCurator;
    $curatorData{$joinkey}{$datatype}{donposneg}  = $curatorDonposneg;
    $curatorData{$joinkey}{$datatype}{selcomment} = $curatorSelComment;
    $curatorData{$joinkey}{$datatype}{txtcomment} = $curatorTxtComment;
  } # for my $i (1 .. $trAmount)
  my %pgData;
  foreach my $datatype (sort keys %papersToAdd) {
    my $joinkeys = join"','", sort keys %{ $papersToAdd{$datatype} };
    my ($pgDatatypeDataRef) = &getPgDataForJoinkeys($joinkeys, $datatype); 
    my %pgDatatypeData = %$pgDatatypeDataRef;
    foreach my $joinkey (keys %pgDatatypeData) {
      foreach my $datatype (keys %{ $pgDatatypeData{$joinkey} }) {
          foreach my $valuetype (keys %{ $pgDatatypeData{$joinkey}{$datatype} }) {
            $pgData{$joinkey}{$datatype}{$valuetype} = $pgDatatypeData{$joinkey}{$datatype}{$valuetype}; } } } }

  my @data; my @duplicateData;
  foreach my $joinkey (sort keys %curatorData) {
    foreach my $datatype (keys %{ $curatorData{$joinkey} }) {
        my $thisCurator  = $curatorData{$joinkey}{$datatype}{curator}; 
        my $donposneg    = $curatorData{$joinkey}{$datatype}{donposneg}; 
        my $selcomment   = $curatorData{$joinkey}{$datatype}{selcomment}; 
        my $txtcomment   = $curatorData{$joinkey}{$datatype}{txtcomment}; 
        my @line; 
        push @line, $joinkey;
        push @line, $datatype;
        push @line, $thisCurator;
        push @line, $donposneg;
        push @line, $selcomment;
        push @line, $txtcomment;
        if ($pgData{$joinkey}{$datatype}) { push @duplicateData, \@line; }
          else { push @data, \@line; }
  } }
  &processResultDataDuplicateData(\@data, \@duplicateData, \%pgData);
  &printFormClose();
} # sub submitNewResults

sub getPgDataForJoinkeys {
  my ($joinkeys, $datatype) = @_;
  my %pgData;
  $result = $dbh->prepare( "SELECT * FROM cur_curdata WHERE cur_datatype = '$datatype' AND cur_paper IN ('$joinkeys')" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    $pgData{$row[0]}{$row[1]}{curator}     = $row[2]; 
    $pgData{$row[0]}{$row[1]}{donposneg}   = $row[3]; 
    $pgData{$row[0]}{$row[1]}{selcomment}  = $row[4];
    $pgData{$row[0]}{$row[1]}{txtcomment}  = $row[5];
    $pgData{$row[0]}{$row[1]}{timestamp}   = $row[6]; }
  return \%pgData;
} # sub getPgDataForJoinkeys

sub processResultDataDuplicateData {
  my ($dataRef, $duplicateDataRef, $pgDataRef) = @_;
  my @data          = @$dataRef;
  my @duplicateData = @$duplicateDataRef;
  my %pgData        = %$pgDataRef;
  print qq(<table border="1">\n);
  print qq(<tr>${thDot}paperId</td>${thDot}datatype</td>${thDot}curator</td>${thDot}value</td>${thDot}selcomment</td>${thDot}textcomment</td></tr>\n);
  foreach my $lineRef (@data) {
    my @line = @$lineRef;
    foreach (@line) { unless ($_) { $_ = ''; } }	# initialize values if none are there
    my $pgvalues = join"','", @line;
    my @pgcommands = ();
    my $pgcommand = "INSERT INTO cur_curdata VALUES ('$pgvalues');";
    push @pgcommands, $pgcommand;
    $pgcommand = "INSERT INTO cur_curdata_hst VALUES ('$pgvalues');";
    push @pgcommands, $pgcommand;
    foreach my $pgcommand (@pgcommands) {
      print qq($pgcommand<br/>\n);
# UNCOMMENT TO POPULATE
      $dbh->do( $pgcommand );
    }
    my $trData = join"</td>$tdDot", @line;
    print qq(<tr>${tdDot}$trData</td></tr>\n);
  } # foreach my $lineRef (@data)
  print qq(</table>\n);
  if (scalar @data > 0) { print "results added<br />\n"; }

  my $overwriteCount = 0;
  foreach my $lineRef (@duplicateData) {		# for data already in postgres, add option to overwrite
    my @line = @$lineRef;
    foreach (@line) { unless ($_) { $_ = ''; } }	# initialize values if none are there
    my ( $joinkey, $datatype, $twonum, $donposneg, $selcomment, $txtcomment ) = @line;
    my ( $curatorPg, $curatorPgName, $donposnegPg, $selcommentPg, $selcommentPgText, $txtcommentPg, $timestampPg ) = ( '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;' );
    my ( $curatorFm, $curatorFmName, $donposnegFm, $selcommentFm, $selcommentFmText, $txtcommentFm, $timestampFm ) = ( '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', '<td>&nbsp;</td>' );
    if ( $pgData{$joinkey}{$datatype}{curator}    ) { $curatorPg    = $pgData{$joinkey}{$datatype}{curator};    $curatorPgName = $curators{$curatorPg}; }
    if ( $pgData{$joinkey}{$datatype}{donposneg}  ) { $donposnegPg  = $pgData{$joinkey}{$datatype}{donposneg};  }
    if ( $pgData{$joinkey}{$datatype}{selcomment} ) { $selcommentPg = $pgData{$joinkey}{$datatype}{selcomment}; $selcommentPgText = $premadeComments{$selcommentPg}; }
    if ( $pgData{$joinkey}{$datatype}{txtcomment} ) { $txtcommentPg = $pgData{$joinkey}{$datatype}{txtcomment}; }
    if ( $pgData{$joinkey}{$datatype}{timestamp}  ) { $timestampPg  = "<td>$pgData{$joinkey}{$datatype}{timestamp};</td>"  }
    if ( $twonum ) { $curatorFm = $twonum;
      if ( $curators{$curatorFm} ) { $curatorFmName   = $curators{$curatorFm}; } }
    if ( $donposneg )  { $donposnegFm  = $donposneg;  }
    if ( $selcomment ) { $selcommentFm = $selcomment;
      if ( $premadeComments{$selcommentFm} ) { $selcommentFmText = $premadeComments{$selcommentFm}; } }
    if ( $txtcomment ) { $txtcommentFm = $txtcomment; }
    my $isDifferent = 0;				# if any of the non-key values has changed, show option to overwrite
    if ($curatorFmName    ne $curatorPgName) {    
        $isDifferent++;
        $curatorFmName = '<td style="background-color:yellow">' . $curatorFmName . '</td>';
        $curatorPgName = '<td style="background-color:yellow">' . $curatorPgName . '</td>'; }
      else {
        $curatorFmName = '<td>' . $curatorFmName . '</td>';
        $curatorPgName = '<td>' . $curatorPgName . '</td>'; }
    if ($donposnegFm  ne $donposnegPg) {
        $isDifferent++;
        $donposnegFm = '<td style="background-color:yellow">' . $donposnegFm . '</td>';
        $donposnegPg = '<td style="background-color:yellow">' . $donposnegPg . '</td>'; }
      else {
        $donposnegFm = '<td>' . $donposnegFm . '</td>';
        $donposnegPg = '<td>' . $donposnegPg . '</td>'; }
    if ($selcommentFmText ne $selcommentPgText) {
        $isDifferent++;
        $selcommentFmText = '<td style="background-color:yellow">' . $selcommentFmText . '</td>';
        $selcommentPgText = '<td style="background-color:yellow">' . $selcommentPgText . '</td>'; }
      else {
        $selcommentFmText = '<td>' . $selcommentFmText . '</td>';
        $selcommentPgText = '<td>' . $selcommentPgText . '</td>'; }
    if ($txtcommentFm ne $txtcommentPg) {
        $isDifferent++;
        $txtcommentFm = '<td style="background-color:yellow">' . $txtcommentFm . '</td>';
        $txtcommentPg = '<td style="background-color:yellow">' . $txtcommentPg . '</td>'; }
      else {
        $txtcommentFm = '<td>' . $txtcommentFm . '</td>';
        $txtcommentPg = '<td>' . $txtcommentPg . '</td>'; }
    next unless ($isDifferent > 0);
    $overwriteCount++;
    print qq(<input type="hidden" name="joinkey_$overwriteCount"       value="$joinkey"  >);
    print qq(<input type="hidden" name="datatype_$overwriteCount"      value="$datatype" >);
    print qq(<input type="hidden" name="twonum_$overwriteCount"        value="$twonum"   >);
    print qq(<input type="hidden" name="donposneg_$overwriteCount"     value="$donposneg"   >);
    print qq(<input type="hidden" name="selcomment_$overwriteCount"    value="$selcomment"  >);
    print qq(<input type="hidden" name="txtcomment_$overwriteCount"    value="$txtcomment"  >);
    print qq(WBPaper$joinkey $datatype : <br/>\n);
    print qq(<table border="1">\n);
    print qq(<tr><th>&nbsp;</th><th>curator</th><th>value</th><th>selcomment</th><th>txtcomment</th><th>timestamp</th></tr>);
    print qq(<tr><td>old</td>${curatorPgName}${donposnegPg}${selcommentPgText}${txtcommentPg}${timestampPg}</tr>\n);
    print qq(<tr><td>new</td>${curatorFmName}${donposnegFm}${selcommentFmText}${txtcommentFm}${timestampFm}</tr>\n);
    print qq(</table>\n);
    print qq(Confirm change <input type="checkbox" name="checkbox_$overwriteCount" value="overwrite"><br/><br/>\n);
  } # foreach my $lineRef (@data)
  if ($overwriteCount > 0) {
    print qq(<input type="hidden" name="overwrite_count" value="$overwriteCount">);
    print qq(<input type="submit" name="action" value="Overwrite Selected Results"><br/>\n); }
} # sub processResultDataDuplicateData

sub addResults {
  &printFormOpen();
  &printHiddenCurator();
  my $errorData = '';
  my %papersToAdd;
  my $twonum = $curator;
  ($oop, my $datatype) = &getHtmlVar($query, "select_datatype");
  unless ($datatype) { $errorData .= "Error : Need to select a datatype.<br/>\n"; }
  ($oop, my $donposneg) = &getHtmlVar($query, "select_donposneg");
  unless ($donposneg) { $errorData .= "Error : Need to select whether result is curated, validated positive, or validated negative.<br/>\n"; }
  ($oop, my $paperResults) = &getHtmlVar($query, "textarea_paper_results");
  if ($paperResults) {
      my @lines = split/\r\n/, $paperResults;
      foreach my $line (@lines) {
        if ($line =~ m/^WBPaper(\S+)$/) { $papersToAdd{$1}++; }
         else { $errorData .= qq(Error bad line : ${line}<br/>\n); }
      } } # foreach my $line (@lines)
    else { $errorData .= "Error : Need to enter at least one paper.<br/>\n"; }
  ($oop, my $selcomment) = &getHtmlVar($query, "select_comment");
  ($oop, my $txtcomment) = &getHtmlVar($query, "textarea_comment");
  if ($errorData) { 				# problem with data, do not allow creation of any data, show form again
      print "$errorData<br />\n"; 
      printAddSection($twonum, $datatype, $donposneg, $paperResults, $selcomment, $txtcomment); }
    else {					# all data is okay, enter data.
      my $joinkeys = join"','", sort keys %papersToAdd;
      my ($pgDataRef) = &getPgDataForJoinkeys($joinkeys, $datatype); 
      my %pgData = %$pgDataRef;

      my @data; my @duplicateData;
      foreach my $joinkey (sort keys %papersToAdd) {
          my @line; 
          push @line, $joinkey;
          push @line, $datatype;
          push @line, $twonum;
          push @line, $donposneg;
          push @line, $selcomment;
          push @line, $txtcomment;
          if ($pgData{$joinkey}{$datatype}) { push @duplicateData, \@line; }
            else { push @data, \@line; }
      } # foreach my $joinkey (sort keys %papersToAdd)
      &processResultDataDuplicateData(\@data, \@duplicateData, \%pgData);
    } # else # if ($errorData)
  &printFormClose();
} # sub addResults

sub overwriteSelectedResults { 
  ($oop, my $overwriteCount) = &getHtmlVar($query, "overwrite_count");
  my @pgcommands;
  for my $i (1 .. $overwriteCount) {
    ($oop, my $overwrite) = &getHtmlVar($query, "checkbox_$i");
    next unless ($overwrite eq 'overwrite');
    ($oop, my $joinkey    ) = &getHtmlVar($query, "joinkey_$i"    );
    ($oop, my $datatype   ) = &getHtmlVar($query, "datatype_$i"   );
    ($oop, my $twonum     ) = &getHtmlVar($query, "twonum_$i"     );
    ($oop, my $donposneg  ) = &getHtmlVar($query, "donposneg_$i"  );
    ($oop, my $selcomment ) = &getHtmlVar($query, "selcomment_$i" );
    ($oop, my $txtcomment ) = &getHtmlVar($query, "txtcomment_$i" );
    unless ($donposneg) { $donposneg = ''; } unless ($selcomment) { $selcomment = ''; } unless ($txtcomment) { $txtcomment = ''; }
    push @pgcommands, qq(DELETE FROM cur_curdata WHERE cur_paper = '$joinkey' AND cur_datatype = '$datatype' AND cur_curator = '$twonum');
    push @pgcommands, qq(INSERT INTO cur_curdata VALUES ('$joinkey', '$datatype', '$twonum', '$donposneg', '$selcomment', '$txtcomment'));
    push @pgcommands, qq(INSERT INTO cur_curdata_hst VALUES ('$joinkey', '$datatype', '$twonum', '$donposneg', '$selcomment', '$txtcomment'));
  } # for my $i (1 .. $overwriteCount)
  foreach my $pgcommand (@pgcommands) {
    print "$pgcommand<br />\n";
# UNCOMMENT TO POPULATE
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
} # sub overwriteSelectedResults

sub getResults {
  &printFormOpen();
  &printHiddenCurator();
  &populateCuratablePapers(); 			# assume for now that we only care about curatable papers

  ($oop, my $all_datatypes_checkbox) = &getHtmlVar($query, "checkbox_all_datatypes");
  unless ($all_datatypes_checkbox) { $all_datatypes_checkbox = ''; }
  ($oop, my $all_datatypes_with_data_checkbox) = &getHtmlVar($query, "checkbox_all_datatypes_with_data");
  unless ($all_datatypes_with_data_checkbox) { $all_datatypes_with_data_checkbox = ''; }
  foreach my $datatype (keys %datatypes) {
    ($oop, my $chosen) = &getHtmlVar($query, "checkbox_$datatype");
    unless ($chosen) { $chosen = ''; }
    if ($all_datatypes_with_data_checkbox eq 'all') { $chosen = $datatype; }	# if all datatypes checkbox was selected, set that datatype's chosen to that datatype
    if ($all_datatypes_checkbox eq 'all') { $chosen = $datatype; }	# if all datatypes checkbox was selected, set that datatype's chosen to that datatype
    print qq(<input type="hidden" name="checkbox_$datatype" value="$chosen">\n);
    if ($chosen) { $chosenDatatypes{$chosen}++; }
  } # foreach my $datatype (keys %datatypes)
  
  ($oop, my $specificPapers) = &getHtmlVar($query, "specific_papers");	# get specified papers
  my %filterPapers; my %specificPapers; my %topicPapers;
  if ($specificPapers) { my (@joinkeys) = $specificPapers =~ m/(\d+)/g; foreach (@joinkeys) { $specificPapers{$_}++; } }
  ($oop, my $topic)          = &getHtmlVar($query, "select_topic");	# if there's a selected topic replace specific papers with those from topic
  unless ($topic) { $topic = 'none'; }
  if ($topic ne 'none') {
    print "using topic $topic<br/>\n";
    my ($topicID) = $topic =~ m/(WBbiopr:\d+)/;				# get the WBProcessID from the topic which includes the name
    print qq(<input type="hidden" name="select_topic" value="$topic">\n);
#     $result = $dbh->prepare( "SELECT DISTINCT(pro_paper.pro_paper) FROM pro_process, pro_paper, pro_topicpaperstatus WHERE pro_process.joinkey = pro_paper.joinkey AND pro_process.joinkey = pro_topicpaperstatus.joinkey AND (pro_topicpaperstatus.pro_topicpaperstatus = 'unchecked' OR pro_topicpaperstatus.pro_topicpaperstatus = 'relevant') AND pro_process.pro_process = '$topicID'" );
#     $result = $dbh->prepare( "SELECT DISTINCT(pro_paper.pro_paper) FROM pro_process, pro_paper, pro_topicpaperstatus WHERE pro_process.joinkey = pro_paper.joinkey AND pro_process.joinkey = pro_topicpaperstatus.joinkey AND (pro_topicpaperstatus.pro_topicpaperstatus = 'unchecked' OR pro_topicpaperstatus.pro_topicpaperstatus = 'relevant') AND pro_process.pro_process = '$topicID' AND pro_process.joinkey NOT IN (SELECT joinkey FROM pro_curationstatusomit)" );	# created a new flag in the topic OA for papers that should be omitted from this filter.  2014 02 06
    $result = $dbh->prepare( "SELECT DISTINCT(pro_paper.pro_paper) FROM pro_process, pro_paper, pro_topicpaperstatus WHERE pro_process.joinkey = pro_paper.joinkey AND pro_process.joinkey = pro_topicpaperstatus.joinkey AND (pro_topicpaperstatus.pro_topicpaperstatus = 'relevant') AND pro_process.pro_process = '$topicID' AND pro_process.joinkey NOT IN (SELECT joinkey FROM pro_curationstatusomit)" );	# created a new flag in the topic OA for papers that should be omitted from this filter.  2014 02 06	# Chris no longer wants unchecked papers, only relevant  2014 06 12
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $row[0] =~ s/WBPaper//; $topicPapers{$row[0]}++; }
  } # if ($topic ne 'none')
  if ($specificPapers && ($topic ne 'none')) {
      foreach (sort keys %specificPapers) { if ($topicPapers{$_}) { $chosenPapers{$_}++; } } }
    elsif ($specificPapers) {
      foreach (sort keys %specificPapers) { $chosenPapers{$_}++; } }
    elsif ($topic ne 'none') {
      foreach (sort keys %topicPapers) { $chosenPapers{$_}++; } }
    else { $chosenPapers{'all'}++; }
  print qq(<input type="hidden" name="specific_papers" value="$specificPapers">\n);

  &populateCurCurData(); 				# always show curator values since they have to be editable

  ($oop, my $displayOa)  = &getHtmlVar($query, "checkbox_oa");    unless ($displayOa) {  $displayOa  = ''; }
  ($oop, my $displayCfp) = &getHtmlVar($query, "checkbox_cfp");   unless ($displayCfp) { $displayCfp = ''; }
  ($oop, my $displayAfp) = &getHtmlVar($query, "checkbox_afp");   unless ($displayAfp) { $displayAfp = ''; }
  ($oop, my $displaySvm) = &getHtmlVar($query, "checkbox_svm");   unless ($displaySvm) { $displaySvm = ''; }
  print qq(<input type="hidden" name="checkbox_oa"  value="$displayOa" >\n);
  print qq(<input type="hidden" name="checkbox_cfp" value="$displayCfp">\n);
  print qq(<input type="hidden" name="checkbox_afp" value="$displayAfp">\n);
  print qq(<input type="hidden" name="checkbox_svm" value="$displaySvm">\n);
  if ($displayOa) {  &populateOaData();  }
  if ($displayCfp) { &populateCfpData(); }
  if ($displayAfp) { &populateAfpData(); }
  if ($displaySvm) { &populateSvmData(); }

  ($oop, my $showJournal) = &getHtmlVar($query, "checkbox_journal");   unless ($showJournal) { $showJournal = ''; }
  ($oop, my $showPmid)    = &getHtmlVar($query, "checkbox_pmid");      unless ($showPmid) {    $showPmid = '';    }
  ($oop, my $showPdf)     = &getHtmlVar($query, "checkbox_pdf");       unless ($showPdf) {     $showPdf = '';     }
  print qq(<input type="hidden" name="checkbox_journal" value="$showJournal">\n);
  print qq(<input type="hidden" name="checkbox_pmid"    value="$showPmid">\n);
  print qq(<input type="hidden" name="checkbox_pdf"     value="$showPdf">\n);

  ($oop, my $papersPerPage) = &getHtmlVar($query, "papers_per_page");
  ($oop, my $pageSelected)  = &getHtmlVar($query, "select_page");
  unless ($papersPerPage) { $papersPerPage = 10; }
  unless ($pageSelected) {  $pageSelected  = 0;  }
  print qq(<input type="hidden" name="papers_per_page" value="$papersPerPage">\n);

  my @headerRow = qw( paperID );
  if ($showJournal) { push @headerRow, "journal"; &populateJournal(); }
  if ($showPmid)    { push @headerRow, "pmid";    &populatePmid();    }
  if ($showPdf)     { push @headerRow, "pdf";     &populatePdf();     }

  my %trs;				# td data for each table row
  my %paperPosNegOkay;			# papers that have positive-negative data okay, so show all svm results for that paper even if a given row isn't positive-negative okay
  my %paperInfo;			# for a joinkey, all the paper information about it to show in a big rowspan for that table row 

  my %allPaperData;			# hash of datatype - joinkey  for all posible queried data structures, to key off from this when there are no svm results for a data structure with data.
  foreach my $datatype (keys %svmData) { foreach my $joinkey (keys %{ $svmData{$datatype} }) { $allPaperData{$joinkey}{$datatype}++; } }
  foreach my $datatype (keys %curData) { foreach my $joinkey (keys %{ $curData{$datatype} }) { $allPaperData{$joinkey}{$datatype}++; } }
  foreach my $datatype (keys %oaData)  { foreach my $joinkey (keys %{  $oaData{$datatype} }) { $allPaperData{$joinkey}{$datatype}++; } }
  foreach my $datatype (keys %cfpData) { foreach my $joinkey (keys %{ $cfpData{$datatype} }) { $allPaperData{$joinkey}{$datatype}++; } }
  foreach my $datatype (keys %afpData) { foreach my $joinkey (keys %{ $afpData{$datatype} }) { $allPaperData{$joinkey}{$datatype}++; } }

  my $trCounter = 0;
  foreach my $joinkey (sort keys %curatablePapers) {			# TODO curatablePapers or allPaperData that have some flag ?
    next unless ($chosenPapers{$joinkey} || $chosenPapers{all});

    push @{ $paperInfo{$joinkey} }, $joinkey;
    my $journal = ''; my $pmid = ''; my $pdf = ''; my $primaryData = '';
    if ($showJournal) { 
      if ($journal{$joinkey}) { $journal = $journal{$joinkey}; }
      push @{ $paperInfo{$joinkey} }, $journal; }
    if ($showPmid) { 
      if ($pmid{$joinkey}) { $pmid = $pmid{$joinkey}; }
      push @{ $paperInfo{$joinkey} }, $pmid; }
    if ($showPdf) {
      if ($pdf{$joinkey}) { $pdf = $pdf{$joinkey}; }
      push @{ $paperInfo{$joinkey} }, $pdf; }

#     foreach my $datatype (sort keys %{ $allPaperData{$joinkey} }) { # } used to default to how only those that have data, now defaults to show all datatypes.  for Chris and Raymond 2014 07 09
    foreach my $datatype (sort keys %datatypes) {
      next unless ($chosenDatatypes{$datatype});			# show only results for selected datatype
      next if ( ($all_datatypes_with_data_checkbox eq 'all') && !($allPaperData{$joinkey}{$datatype}) );	# skip if should only show those with data and has no data.  for Chris and Raymond 2014 07 09
      my @dataRow = ( "$datatype" ); 
      $trCounter++;
      if ($displaySvm) {
        my $svmResult = '';
        if ($svmData{$datatype}{$joinkey}) { $svmResult = $svmData{$datatype}{$joinkey}; }
        my $bgcolor = 'white';
        if ($svmResult eq 'high')      { $bgcolor = '#FFA0A0'; }
        elsif ($svmResult eq 'medium') { $bgcolor = '#FFC8C8'; }
        elsif ($svmResult eq 'low')    { $bgcolor = '#FFE0E0'; }
        $svmResult = qq(<span style="background-color: $bgcolor">$svmResult</span>);
        push @dataRow, $svmResult; 
      } # if ($displaySvm)

      if ($displayCfp) {
        my $cfpResult = '';
        if ($cfpData{$datatype}{$joinkey}) { $cfpResult = $cfpData{$datatype}{$joinkey}; }
        push @dataRow, $cfpResult; 
      }

      if ($displayAfp) {
        my $afpResult = ''; 
        if ($afpData{$datatype}{$joinkey}) { $afpResult = $afpData{$datatype}{$joinkey}; }
        push @dataRow, $afpResult; 
      }

      if ($displayOa) {
#         my $oaResult = 'oa_blank';
        my $oaResult = qq(<span style="background-color: #FFA0A0">oa_blank</span>);	# color like svm high for Chris and Karen for topic curation 2013 11 06
        if ($oaData{$datatype}{$joinkey}) { $oaResult = $oaData{$datatype}{$joinkey}; }
        push @dataRow, $oaResult; 
      }

      my $thisCurator = '';							# curator in cur_curdata for this paper-datatype if it has a value
      if ( $curData{$datatype}{$joinkey}{curator} ) { $thisCurator = $curData{$datatype}{$joinkey}{curator}; }
      my $curatorSelectCurator = qq(<select name="select_curator_curator_$trCounter" size="1">\n<option value=""></option>\n);
      foreach my $curator_two (keys %curators) {        # display curators in alphabetical (tied hash) order, if IP matches existing ip record, select it
        if ($thisCurator eq $curator_two) { $curatorSelectCurator .= qq(<option value="$curator_two" selected="selected">$curators{$curator_two}</option>\n); }
          else {                            $curatorSelectCurator .= qq(<option value="$curator_two">$curators{$curator_two}</option>\n); } }
      $curatorSelectCurator .= qq(</select>);

      $curatorSelectCurator .= qq(<input type="hidden" name="joinkey_$trCounter"  value="$joinkey" >);	# these are required, arbitrarily added here
      $curatorSelectCurator .= qq(<input type="hidden" name="datatype_$trCounter" value="$datatype">);	# these are required, arbitrarily added here
      push @dataRow, $curatorSelectCurator; 

      my $thisDonPosNeg = ''; if ( $curData{$datatype}{$joinkey}{donposneg} ) { $thisDonPosNeg = $curData{$datatype}{$joinkey}{donposneg}; }
      my $curatorSelectDonposneg = qq(<select name="select_curator_donposneg_$trCounter">);
      foreach my $donposneg (keys %donPosNegOptions) {        # display curators in alphabetical (tied hash) order, if IP matches existing ip record, select it
        if ($thisDonPosNeg eq $donposneg) { $curatorSelectDonposneg .= qq(<option value="$donposneg" selected="selected">$donPosNegOptions{$donposneg}</option>\n); }
          else {                            $curatorSelectDonposneg .= qq(<option value="$donposneg"                    >$donPosNegOptions{$donposneg}</option>\n); } }
      $curatorSelectDonposneg .= qq(</select>);
      push @dataRow, $curatorSelectDonposneg; 

      my $thisSelComment = ''; if ( $curData{$datatype}{$joinkey}{selcomment} ) { $thisSelComment = $curData{$datatype}{$joinkey}{selcomment}; }
      my $curatorSelectComment = qq(<select name="select_curator_comment_$trCounter">);
      $curatorSelectComment .= qq(<option value=""             ></option>\n);
      foreach my $comment (keys %premadeComments) { 
        if ($thisSelComment eq $comment) { $curatorSelectComment .= qq(<option value="$comment" selected="selected">$premadeComments{$comment}</option>\n); }
          else {                           $curatorSelectComment .= qq(<option value="$comment"                    >$premadeComments{$comment}</option>\n); } }
      $curatorSelectComment .= qq(</select>);
      push @dataRow, $curatorSelectComment; 

      my $txtcomment = ''; if ( $curData{$datatype}{$joinkey}{txtcomment} ) { $txtcomment = $curData{$datatype}{$joinkey}{txtcomment}; }
      my $shortTxtComment = $txtcomment;  unless ($shortTxtComment) { $shortTxtComment = '&nbsp;'; }
      if ($txtcomment =~ m/^(.{20})/) { $shortTxtComment = $1; $shortTxtComment .= '...'; }
      my $curatorTextareaComment = qq(<div id="div_curator_comment_$trCounter" onclick="document.getElementById('div_curator_comment_$trCounter').style.display = 'none'; document.getElementById('textarea_curator_comment_$trCounter').style.display = ''; document.getElementById('textarea_curator_comment_$trCounter').focus();" >$shortTxtComment</div>\n);
      $curatorTextareaComment .= qq(<textarea rows="4" cols="80" id="textarea_curator_comment_$trCounter" name="textarea_curator_comment_$trCounter" style="display:none" onblur="document.getElementById('div_curator_comment_$trCounter').style.display = ''; document.getElementById('textarea_curator_comment_$trCounter').style.display = 'none'; var divValue = document.getElementById('textarea_curator_comment_$trCounter').value; if (divValue === '') { divValue = '&nbsp;'; } document.getElementById('div_curator_comment_$trCounter').innerHTML = divValue; ">$txtcomment</textarea>\n);
#       $curatorTextareaComment .= qq(<textarea rows="4" cols="80" id="textarea_curator_comment_$trCounter" name="textarea_curator_comment_$trCounter" style="display:none" onblur="document.getElementById('div_curator_comment_$trCounter').style.display = ''; document.getElementById('textarea_curator_comment_$trCounter').style.display = 'none'; document.getElementById('div_curator_comment_$trCounter').innerHTML = document.getElementById('textarea_curator_comment_$trCounter').value.substring(0,20)">$txtcomment</textarea>\n);			# to get the first 20 characters without adding ...
      push @dataRow, $curatorTextareaComment; 

      $paperPosNegOkay{$joinkey}++; 				# all papers always okay for pos/neg since we no longer have pos/neg filtering  2012 11 08

      my $trData = join"</td>$tdDot", @dataRow;
      push @{ $trs{$joinkey} }, qq(${tdDot}$trData</td></tr>\n);
    } # foreach my $datatype (sort keys %datatypes)
  } # foreach my $joinkey (sort keys %curatablePapers)

  print qq(<input type="hidden" name="trCounter" value="$trCounter">);

  my $joinkeysAmount = scalar(keys %paperPosNegOkay);
  my $pagesAmount = ceil($joinkeysAmount / $papersPerPage);
  print qq(Page number <select name="select_page">);
  for my $i (1 .. $pagesAmount) { 
    if ($i == $pageSelected) { print qq(<option selected="selected">$i</option>\n); }
      else { print qq(<option>$i</option>\n); }
  } # for my $i (1 .. $pagesAmount)
  print qq(</select>);
  print qq(<input type="submit" name="action" value="Get Results">\n);
  print qq(amount of papers $joinkeysAmount<br/>\n);
  print qq(<br />\n);

  print qq(<table border="1">\n);
  push @headerRow, "datatype";
  if ($displaySvm)    { push @headerRow, "SVM Prediction"; }
  if ($displayCfp)    { push @headerRow, "cfp value"; }
  if ($displayAfp)    { push @headerRow, "afp value"; }
  if ($displayOa)     { push @headerRow, "oa value";  }
  push @headerRow, "curator"; push @headerRow, "new result"; push @headerRow, "select comment"; push @headerRow, "textarea comment"; 
  my $headerRow = join"</th>$thDot", @headerRow;
  $headerRow = qq(<tr>$thDot) . $headerRow . qq(</th></tr>);
  print qq($headerRow\n);

  my $papCount = 0;
  my $papCountToSkip = 0; my $papToSkip = ($pageSelected - 1 ) * $papersPerPage;
  foreach my $joinkey (sort keys %paperPosNegOkay) {			# from all papers that have good positve-negative values, show all TRs
    $papCountToSkip++; next if ($papCountToSkip <= $papToSkip);		# skip entries until at the proper page
    $papCount++; 
    last if ($papCount > $papersPerPage);
    my $trsInPaperAmount = scalar @{ $trs{$joinkey} };			# amount of rows for a joinkey, make that the rowspan
    my $firstTr = shift @{ $trs{$joinkey} };				# the first table row needs the paper info and rowspan
    my $tdMultiRow = $tdDot; $tdMultiRow =~ s/>$/ rowspan="$trsInPaperAmount">/;	# add the rowspan to the td style
    my $paperInfoTds = join"</td>$tdMultiRow", @{ $paperInfo{$joinkey} };		# make paper info tds from %paperInfo
    print qq(<tr>${tdMultiRow}$paperInfoTds</td>$firstTr\n); 		# print the first row which has paper info
    foreach my $tr (@{ $trs{$joinkey} }) { print qq(<tr>$tr\n); } }	# print other table rows without paper info
  print qq(</table>\n);

  print qq(<input type="submit" name="action" value="Submit New Results"><br/>\n);
    
  &printFormClose();
} # sub getResults


sub populateCuratedPapers {
  my ($showTimes, $start, $end, $diff) = (0, '', '', '');
  if ($showTimes) { $start = time; }
  &populateCurCurData(); 
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "IN populateCuratedPapers  populateCurCurData $diff<br>"; }
  &populateOaData(); 						# $oaData{datatype}{joinkey} = 'positive';
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "IN populateCuratedPapers  populateOaData $diff<br>"; }
  my %allCuratorValues;			# $allCuratorValues{datatype}{joinkey} = 0 | 1+
  foreach my $datatype (sort keys %oaData) { 
    foreach my $joinkey (sort keys %{ $oaData{$datatype} }) { 
      $allCuratorValues{$joinkey}{$datatype}{curated}++; } }		# validated positive and curated 
  foreach my $datatype (sort keys %curData) {
    foreach my $joinkey (sort keys %{ $curData{$datatype} }) {
      $allCuratorValues{$joinkey}{$datatype}{ $curData{$datatype}{$joinkey}{donposneg} }++; } }
  foreach my $joinkey (sort keys %allCuratorValues) {
    next unless ($curatablePapers{$joinkey});
    foreach my $datatype (sort keys %{ $allCuratorValues{$joinkey} }) {
      my @values = keys %{ $allCuratorValues{$joinkey}{$datatype} };
#       if (scalar @values > 1) { $conflict{$datatype}{$joinkey}++; }
#         else { 
#           my $value = shift @values;
#           $validated{$datatype}{$joinkey} = $value;
#           if ($value eq 'curated') {       $valPos{$datatype}{$joinkey} = $value; $valCur{$datatype}{$joinkey} = $value; }
#             elsif ($value eq 'positive') { $valPos{$datatype}{$joinkey} = $value; }
#             elsif ($value eq 'negative') { $valNeg{$datatype}{$joinkey} = $value; } }
      if (scalar @values < 2) {			# only one value, categorize it
          my $value = shift @values;
          $validated{$datatype}{$joinkey} = $value;
          if ($value eq 'curated') {       $valPos{$datatype}{$joinkey} = $value; $valCur{$datatype}{$joinkey} = $value; }
            elsif ($value eq 'positive') { $valPos{$datatype}{$joinkey} = $value; }
            elsif ($value eq 'negative') { $valNeg{$datatype}{$joinkey} = $value; } }
        elsif (scalar @values == 2) {		# only two values, either ok or conflict
            if ( ($allCuratorValues{$joinkey}{$datatype}{'curated'}) && ($allCuratorValues{$joinkey}{$datatype}{'positive'}) ) {	# positive + curated not a conflict, for Chris 2013 06 12
                $valPos{$datatype}{$joinkey} = 'positive'; $valCur{$datatype}{$joinkey} = 'curated'; }
              else { $conflict{$datatype}{$joinkey}++; } }
        else { $conflict{$datatype}{$joinkey}++; }
  } }
  if ($showTimes) { $end = time; $diff = $end - $start; $start = time; print "IN populateCuratedPapers  categorizing hash $diff<br>"; }
} # sub populateCuratedPapers

sub populateCuratablePapers {
  my $query = "SELECT * FROM pap_status WHERE pap_status = 'valid' AND joinkey IN (SELECT joinkey FROM pap_primary_data WHERE pap_primary_data = 'primary') AND joinkey NOT IN (SELECT joinkey FROM pap_curation_flags WHERE pap_curation_flags = 'non_nematode')";
  $result = $dbh->prepare( $query );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $curatablePapers{$row[0]} = $row[1]; }
} # sub populateCuratablePapers

sub populateSvmData {
  # for statistics page
#     $result = $dbh->prepare( "SELECT * FROM cur_svmdata ORDER BY cur_datatype, cur_date" );	# always doing for all datatypes vs looping for chosen takes 4.66vs 2.74 secs
  foreach my $datatype (sort keys %chosenDatatypes) {
    $result = $dbh->prepare( "SELECT * FROM cur_svmdata WHERE cur_datatype = '$datatype' ORDER BY cur_date" );
      # table stores multiple dates for same paper-datatype in case we want to see multiple results later.  if it didn't and we didn't order it would take 2.05 vs 2.74 secs, so not worth changing the way we're storing data
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my $joinkey = $row[0]; my $svmdata = $row[3];
      next unless ($curatablePapers{$row[0]});
      $svmData{$datatype}{$joinkey} = $svmdata; } }
} # sub populateSvmData

sub populateAfpData {
  foreach my $datatype (sort keys %chosenDatatypes) { 
    next unless $datatypesAfpCfp{$datatype};
    my $pgtable_datatype = $datatypesAfpCfp{$datatype};
    $result = $dbh->prepare( "SELECT * FROM afp_$pgtable_datatype" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      next unless ($curatablePapers{$row[0]});
      $afpData{$datatype}{$row[0]} = $row[1]; }
  } # foreach my $datatype (sort keys %chosenDatatypes) 

  $result = $dbh->prepare( "SELECT * FROM afp_email" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    next unless ($curatablePapers{$row[0]});
    $afpEmailed{$row[0]}++; }
  $result = $dbh->prepare( "SELECT * FROM afp_lasttouched" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { 
    next unless ($curatablePapers{$row[0]});
    foreach my $datatype (sort keys %chosenDatatypes) { 
      $afpFlagged{$datatype}{$row[0]}++; } }
  foreach my $datatype (sort keys %chosenDatatypes) { 
    foreach my $joinkey (sort keys %{ $afpFlagged{$datatype} }) {
      if ($afpData{$datatype}{$joinkey}) { $afpPos{$datatype}{$joinkey}++; }
        else { $afpNeg{$datatype}{$joinkey}++; } } }
} # sub populateAfpData

sub populateCfpData {
  foreach my $datatype (sort keys %chosenDatatypes) {
    next unless $datatypesAfpCfp{$datatype};
    my $pgtable_datatype = $datatypesAfpCfp{$datatype};
    $result = $dbh->prepare( "SELECT * FROM cfp_$pgtable_datatype" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      next unless ($curatablePapers{$row[0]});
      $cfpData{$datatype}{$row[0]} = $row[1]; }
  } # foreach my $datatype (sort keys %chosenDatatypes)

  $result = $dbh->prepare( "SELECT * FROM cfp_curator" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    next unless ($curatablePapers{$row[0]});
    foreach my $datatype (sort keys %chosenDatatypes) { 
      $cfpFlagged{$datatype}{$row[0]}++; } }
  foreach my $datatype (sort keys %chosenDatatypes) {
    foreach my $joinkey (sort keys %{ $cfpFlagged{$datatype} }) {
      if ($cfpData{$datatype}{$joinkey}) { $cfpPos{$datatype}{$joinkey}++; }
        else { $cfpNeg{$datatype}{$joinkey}++; } } }

    # picture flags come from expression OA papers that have been curated Daniela 2013 01 17
  $result = $dbh->prepare( "SELECT DISTINCT(exp_paper) FROM exp_paper" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    my (@paps) = $row[0] =~ m/WBPaper(\d+)/g; 
    foreach my $pap (@paps) { $cfpPos{'picture'}{$pap}++; $cfpData{'picture'}{$pap}++; } }	# it is cfp positive and has cfp data
  delete $cfpNeg{'picture'};									# none have been cfp flagged, so the above cfpNeg is wrong
} # sub populateCfpData

sub populateOaData {
  if ($chosenDatatypes{'chemicals'}) {
      # there are 5 source for curated molecules, and 7 sources for papers related to curated molecules, from Karen 2013 11 02
    $result = $dbh->prepare( "SELECT * FROM mop_name WHERE joinkey IN (SELECT joinkey FROM mop_paper WHERE mop_paper IS NOT NULL AND mop_paper != '')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 	# only molecules with papers are curated
    while (my @row = $result->fetchrow) { $objsCurated{'chemicals'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM app_molecule" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      my (@chemicals) = $row[1] =~ m/(WBMol:\d+)/g;
      foreach my $chemical (@chemicals) { $objsCurated{'chemicals'}{$chemical}++; } }
    $result = $dbh->prepare( "SELECT * FROM grg_moleculeregulator" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      my (@chemicals) = $row[1] =~ m/(WBMol:\d+)/g;
      foreach my $chemical (@chemicals) { $objsCurated{'chemicals'}{$chemical}++; } }
    $result = $dbh->prepare( "SELECT * FROM pro_molecule" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      my (@chemicals) = $row[1] =~ m/(WBMol:\d+)/g;
      foreach my $chemical (@chemicals) { $objsCurated{'chemicals'}{$chemical}++; } }
    $result = $dbh->prepare( "SELECT * FROM rna_molecule WHERE joinkey NOT IN (SELECT joinkey FROM rna_nodump)" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      my (@chemicals) = $row[1] =~ m/(WBMol:\d+)/g;
      foreach my $chemical (@chemicals) { $objsCurated{'chemicals'}{$chemical}++; } }

    $result = $dbh->prepare( "SELECT * FROM mop_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
    $result = $dbh->prepare( "SELECT * FROM app_paper WHERE joinkey IN (SELECT joinkey FROM app_molecule WHERE app_molecule IS NOT NULL AND app_molecule != '')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
    $result = $dbh->prepare( "SELECT * FROM grg_paper WHERE joinkey IN (SELECT joinkey FROM grg_moleculeregulator WHERE grg_moleculeregulator IS NOT NULL AND grg_moleculeregulator != '')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
    $result = $dbh->prepare( "SELECT * FROM pro_paper WHERE joinkey IN (SELECT joinkey FROM pro_molecule WHERE pro_molecule IS NOT NULL AND pro_molecule != '')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
    $result = $dbh->prepare( "SELECT * FROM rna_paper WHERE joinkey NOT IN (SELECT joinkey FROM rna_nodump) AND joinkey IN (SELECT joinkey FROM rna_molecule WHERE rna_molecule IS NOT NULL AND rna_molecule != '')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
    $result = $dbh->prepare( "SELECT * FROM int_paper WHERE joinkey IN (SELECT joinkey FROM int_otheronetype WHERE int_otheronetype = 'Chemical')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 	# only those with chemicals are chemical papers, but there are no objects for objects curated  2013 10 02
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
    $result = $dbh->prepare( "SELECT * FROM int_paper WHERE joinkey IN (SELECT joinkey FROM int_othertwotype WHERE int_othertwotype = 'Chemical')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";  	# only those with chemicals are chemical papers, but there are no objects for objects curated  2013 10 02
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'chemicals'}{$paper} = 'curated'; } }
  } # if ($chosenDatatypes{'chemicals'})

  if ($chosenDatatypes{'newmutant'}) {
    $result = $dbh->prepare( "SELECT * FROM app_variation" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'newmutant'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM app_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'newmutant'}{$paper} = 'curated'; } } }
  if ($chosenDatatypes{'overexpr'}) {
    $result = $dbh->prepare( "SELECT * FROM app_transgene" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'overexpr'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM app_paper WHERE joinkey IN (SELECT joinkey FROM app_transgene WHERE app_transgene IS NOT NULL AND app_transgene != '')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'overexpr'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'antibody'}) {
    $result = $dbh->prepare( "SELECT * FROM abp_name" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'antibody'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM abp_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'antibody'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'otherexpr'}) {
    $result = $dbh->prepare( "SELECT * FROM exp_name" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'otherexpr'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM exp_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'otherexpr'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'genereg'}) {
    $result = $dbh->prepare( "SELECT * FROM grg_name" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'genereg'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM grg_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'genereg'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'geneint'}) {
    $result = $dbh->prepare( "SELECT * FROM int_name" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'geneint'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM int_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'geneint'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'rnai'}) {
    $result = $dbh->prepare( "SELECT * FROM rna_name WHERE joinkey NOT IN (SELECT joinkey FROM rna_nodump)" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'rnai'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM rna_paper WHERE joinkey NOT IN (SELECT joinkey FROM rna_nodump)" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'rnai'}{$paper} = 'curated'; } } }


    # these are not in the OA but they're in postgres, so are here
  if ($chosenDatatypes{'picture'}) {
    $result = $dbh->prepare( "SELECT * FROM pic_name" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'picture'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM pic_paper" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'picture'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'blastomere'}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_wbbtf WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Blastomere_isolation')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'blastomere'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM wbb_reference WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Blastomere_isolation')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'blastomere'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'exprmosaic'}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_wbbtf WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Expression_mosaic')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'exprmosaic'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM wbb_reference WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Expression_mosaic')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'exprmosaic'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'geneticablation'}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_wbbtf WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Genetic_ablation')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'geneticablation'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM wbb_reference WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Genetic_ablation')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'geneticablation'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'geneticmosaic'}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_wbbtf WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Genetic_mosaic')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'geneticmosaic'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM wbb_reference WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Genetic_mosaic')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'geneticmosaic'}{$paper} = 'curated'; } } }

  if ($chosenDatatypes{'laserablation'}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_wbbtf WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Laser_ablation')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $objsCurated{'laserablation'}{$row[1]}++; }
    $result = $dbh->prepare( "SELECT * FROM wbb_reference WHERE joinkey IN (SELECT joinkey FROM wbb_assay WHERE wbb_assay = 'Laser_ablation')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my (@papers) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach my $paper (@papers) {
        $oaData{'laserablation'}{$paper} = 'curated'; } } }
} # sub populateOaData

sub populateCurCurData {
  $result = $dbh->prepare( "SELECT * FROM cur_curdata ORDER BY cur_timestamp" );	# in case multiple values get in for a paper-datatype (shouldn't happen), keep the latest
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    next unless ($chosenPapers{$row[0]} || $chosenPapers{all});
    next unless ($chosenDatatypes{$row[1]});
    next if ( ($row[3] eq 'notvalidated') || ($row[3] eq '') );						# skip entries marked as notvalidated
    $curData{$row[1]}{$row[0]}{curator}    = $row[2]; 
    $curData{$row[1]}{$row[0]}{donposneg}  = $row[3]; 
    $curData{$row[1]}{$row[0]}{selcomment} = $row[4];
    $curData{$row[1]}{$row[0]}{txtcomment} = $row[5];
    $curData{$row[1]}{$row[0]}{timestamp}  = $row[6]; }
} # sub populateCurCurData


sub populateJournal {
  $result = $dbh->prepare( "SELECT * FROM pap_journal WHERE pap_journal IS NOT NULL" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[0]) { $journal{$row[0]} = $row[1]; } }
} # sub populateJournal

sub populatePmid {
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my %temp;
  while (my @row = $result->fetchrow) { if ($row[0]) { 
    my ($data) = &makeNcbiLinkFromPmid($row[1]);
    $temp{$row[0]}{$data}++; } }
  foreach my $joinkey (sort keys %temp) {
    my ($pmids) = join"<br/>", keys %{ $temp{$joinkey} };
    $pmid{$joinkey} = $pmids;
  } # foreach my $joinkey (sort keys %temp)
} # sub populatePmid

sub populatePdf {
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path WHERE pap_electronic_path IS NOT NULL");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my %temp;
  while (my @row = $result->fetchrow) {
    my ($data, $isPdf) = &makePdfLinkFromPath($row[1]);
    $temp{$row[0]}{$isPdf}{$data}++; }
  foreach my $joinkey (sort keys %temp) {
    my @pdfs;
    foreach my $isPdf (reverse sort keys %{ $temp{$joinkey} }) { 
      foreach my $pdfLink (sort keys %{ $temp{$joinkey}{$isPdf} }) { 
        push @pdfs, $pdfLink; } }
    my ($pdfs) = join"<br/>", @pdfs;
    $pdf{$joinkey} = $pdfs;
  } # foreach my $joinkey (sort keys %temp)
} # sub populatePdf

sub makePdfLinkFromPath {
  my ($path) = shift;
  my ($pdf) = $path =~ m/\/([^\/]*)$/;
  my $isPdf = 0; if ($pdf =~ m/\.pdf$/) { $isPdf++; }		# kimberly wants .pdf files on top, so need to flag to sort
  my $link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
  my $data = "<a href=\"$link\" target=\"new\">$pdf</a>"; return ($data, $isPdf); }
sub makeNcbiLinkFromPmid {
  my $pmid = shift;
  my ($id) = $pmid =~ m/(\d+)/;
  my $link = 'http://www.ncbi.nlm.nih.gov/pubmed/' . $id;
  my $data = "<a href=\"$link\" target=\"new\">$pmid</a>"; return $data; }


sub populateDatatypes {
  $result = $dbh->prepare( "SELECT DISTINCT(cur_datatype) FROM cur_svmdata " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $datatypesAfpCfp{$row[0]} = $row[0]; }
  $datatypesAfpCfp{'chemicals'}     = 'chemicals';		# added for Karen 2013 10 02
  $datatypesAfpCfp{'blastomere'}    = 'cellfunc';
  $datatypesAfpCfp{'exprmosaic'}    = 'siteaction';
  $datatypesAfpCfp{'geneticmosaic'} = 'mosaic';
  $datatypesAfpCfp{'laserablation'} = 'ablationdata';
  foreach my $datatype (keys %datatypesAfpCfp) { $datatypes{$datatype}++; }
  $datatypes{'geneticablation'}++;
  $datatypes{'picture'}++;			# for Daniela's pictures
} # sub populateDatatypes

sub populateDonPosNegOptions {
  $donPosNegOptions{""}             = "";
  $donPosNegOptions{"curated"}      = "curated and positive";
  $donPosNegOptions{"positive"}     = "validated positive";
  $donPosNegOptions{"negative"}     = "validated negative";
  $donPosNegOptions{"notvalidated"} = "not validated";
} # sub populateDonPosNegOptions

sub populateCurators {
  $curators{"two1823"}   = 'Juancarlos Chan';
  $curators{"two101"}    = 'Wen Chen';
  $curators{"two1983"}   = 'Paul Davis';
  $curators{"two2987"}   = 'Chris Grove';
  $curators{"two3111"}   = 'Kevin Howe';
  $curators{"two324"}    = 'Ranjana Kishore';
  $curators{"two363"}    = 'Raymond Lee';
  $curators{"two1"}      = 'Cecilia Nakamura';
  $curators{"two4055"}   = 'Michael Paulini';
  $curators{"two480"}    = 'Tuco';
  $curators{"two12028"}  = 'Daniela Raciti';
  $curators{"two1847"}   = 'Anthony Rogers';
  $curators{"two557"}    = 'Gary C. Schindelman';
  $curators{"two567"}    = 'Erich Schwarz';
  $curators{"two625"}    = 'Paul Sternberg';
  $curators{"two2970"}   = 'Mary Ann Tuli';
  $curators{"two1843"}   = 'Kimberly Van Auken';
  $curators{"two736"}    = 'Qinghua Wang';
  $curators{"two1760"}   = 'Xiaodong Wang';
  $curators{"two4025"}   = 'Gary Williams';
  $curators{"two712"}    = 'Karen Yook';
} # sub populateCurators
sub populatePremadeComments {
  $premadeComments{"1"}  = "SVM Positive, Curation Negative";
  $premadeComments{"2"}  = "C. elegans as heterologous expression system";
  $premadeComments{"3"}  = "Curated for GO (by WB)";
  $premadeComments{"4"}  = "Curated for GO (by GOA)";
  $premadeComments{"5"}  = "Curated for GO (by IntAct)";
  $premadeComments{"6"}  = "Curated for BioGRID (by WB)";
  $premadeComments{"7"}  = "Curated for BioGRID (by BG)";
  $premadeComments{"8"}  = "Curated for GO (by WB), Curated for BioGRID (by WB)";
  $premadeComments{"9"}  = "Curated for GO (by WB), Curated for BioGRID (by BG)";
  $premadeComments{"10"} = "Curated for GO (by GOA), Curated for BioGRID (by WB)";
  $premadeComments{"11"} = "Curated for GO (by GOA), Curated for BioGRID (by BG)";
  $premadeComments{"12"} = "Curated for GO (by IntAct), Curated for BioGRID (by WB)";
  $premadeComments{"13"} = "Curated for GO (by IntAct), Curated for BioGRID (by BG)";
} # sub populatePremadeComments


sub populateStatisticsHashToDescription {
  $statsHashToDescription{"allcur"}              = 'Papers curated for the indicated data type';
  $statsHashToDescription{"allval"}              = 'Papers confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"allval pos"}          = 'Papers confirmed by a curator to have the indicated data type';
  $statsHashToDescription{"allval pos cur"}      = 'Papers confirmed by a curator to have the indicated data type and curated';
  $statsHashToDescription{"allval pos ncur"}     = 'Papers confirmed by a curator to have the indicated data type but have not yet been curated';
  $statsHashToDescription{"allval neg"}          = 'Papers confirmed by a curator to lack the indicated data type';
  $statsHashToDescription{"allval conf"}         = 'Papers confirmed as both having and not having the indicated data type by two or more curators (in need of resolution)';

  $statsHashToDescription{"any"}                 = 'Papers that have been flagged (positive or negative) by any (at least one) flagging method for the indicated data type';
  $statsHashToDescription{"any pos"}             = 'Papers that have been flagged positive by any (at least one) flagging method for the indicated data type';
  $statsHashToDescription{"any pos val"}         = 'Papers that have been flagged positive by any (at least one) flagging method and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"any pos val tp"}      = 'Papers that have been flagged positive by any (at least one) flagging method and have been confirmed by a curator to lack the data type and, hence, be a false positive (at least for one flagging method)';
  $statsHashToDescription{"any pos val tp cur"}  = 'Papers that have been flagged positive by any (at least one) flagging method and have been confirmed by a curator to have the data type and, hence, be a true positive (at least for one flagging method)';
  $statsHashToDescription{"any pos val tp ncur"} = 'Papers that have been flagged positive by any (at least one) flagging method, have been confirmed by a curator to have the data type and, hence, be a true positive (at least for one flagging method), and have been curated';
  $statsHashToDescription{"any pos val fp"}      = 'Papers that have been flagged positive by any (at least one) flagging method, have been confirmed by a curator to have the data type and, hence, be a true positive (at least for one flagging method), and have not yet been curated';
  $statsHashToDescription{"any pos nval"}        = 'Papers that have been flagged positive by any (at least one) flagging method and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"any pos ncur"}        = 'Papers that have been flagged positive by any (at least one) flagging method and have not been curated (True positives, not curated + Not validated)';

  $statsHashToDescription{"int"}                 = 'Papers that have been flagged (positive or negative) by all flagging methods for the indicated data type';
  $statsHashToDescription{"int pos"}             = 'Papers that have been flagged positive by all flagging methods for the indicated data type';
  $statsHashToDescription{"int pos val"}         = 'Papers that have been flagged positive by all flagging methods and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"int pos val tp"}      = 'Papers that have been flagged positive by all flagging methods and have been confirmed by a curator to have the data type and, hence, be a true positive (for all flagging methods)';
  $statsHashToDescription{"int pos val tp cur"}  = 'Papers that have been flagged positive by all flagging methods, have been confirmed by a curator to have the data type and, hence, be a true positive (for all flagging methods), and have been curated';
  $statsHashToDescription{"int pos val tp ncur"} = 'Papers that have been flagged positive by all flagging methods, have been confirmed by a curator to have the data type and, hence, be a true positive (for all flagging methods), and have not yet been curated';
  $statsHashToDescription{"int pos val fp"}      = 'Papers that have been flagged positive by all flagging methods and have been confirmed by a curator to lack the data type and, hence, be a false positive (for all flagging methods)';
  $statsHashToDescription{"int pos nval"}        = 'Papers that have been flagged positive by all flagging methods and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"int pos ncur"}        = 'Papers that have been flagged positive by all flagging methods and have not been curated (True positives, not curated + Not validated)';

  $statsHashToDescription{"svmnotdone"}          = 'Papers that have not gone through the Support Vector Machine (SVM) pipeline for the indicated data type';
  $statsHashToDescription{"svm"}                 = 'Papers that have gone through the Support Vector Machine (SVM) pipeline for the indicated data type';
  $statsHashToDescription{"svm pos"}             = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low)';
  $statsHashToDescription{"svm pos val"}         = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low) and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm pos val tp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low) and have been confirmed by a curator to have the data type and, hence, be a true positive';
  $statsHashToDescription{"svm pos val tp cur"}  = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low), have been confirmed by a curator to have the data type and, hence, be a true positive, and have been curated';
  $statsHashToDescription{"svm pos val tp ncur"} = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low), have been confirmed by a curator to have the data type and, hence, be a true positive, and have not yet been curated';
  $statsHashToDescription{"svm pos val fp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low) and have been confirmed by a curator to lack the data type and, hence, be a false positive';
  $statsHashToDescription{"svm pos nval"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low) and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm pos ncur"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at any confidence level (high, medium, or low) and have not been curated (True positives, not curated + Not validated)';
  $statsHashToDescription{"svm hig"}             = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence';
  $statsHashToDescription{"svm hig val"}         = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm hig val tp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence and have been confirmed by a curator to have the data type and, hence, be a true positive';
  $statsHashToDescription{"svm hig val tp cur"}  = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence, have been confirmed by a curator to have the data type and, hence, be a true positive, and have been curated';
  $statsHashToDescription{"svm hig val tp ncur"} = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence, have been confirmed by a curator to have the data type and, hence, be a true positive, and have not yet been curated';
  $statsHashToDescription{"svm hig val fp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence and have been confirmed by a curator to lack the data type and, hence, be a false positive';
  $statsHashToDescription{"svm hig nval"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm hig ncur"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at high confidence and have not been curated (True positives, not curated + Not validated)';
  $statsHashToDescription{"svm med"}             = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence';
  $statsHashToDescription{"svm med val"}         = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm med val tp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence and have been confirmed by a curator to have the data type and, hence, be a true positive';
  $statsHashToDescription{"svm med val tp cur"}  = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence, have been confirmed by a curator to have the data type and, hence, be a true positive, and have been curated';
  $statsHashToDescription{"svm med val tp ncur"} = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence, have been confirmed by a curator to have the data type and, hence, be a true positive, and have not yet been curated';
  $statsHashToDescription{"svm med val fp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence and have been confirmed by a curator to lack the data type and, hence, be a false positive';
  $statsHashToDescription{"svm med nval"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm med ncur"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at medium confidence and have not been curated (True positives, not curated + Not validated)';
  $statsHashToDescription{"svm low"}             = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence';
  $statsHashToDescription{"svm low val"}         = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm low val tp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence and have been confirmed by a curator to have the data type and, hence, be a true positive';
  $statsHashToDescription{"svm low val tp cur"}  = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence, have been confirmed by a curator to have the data type and, hence, be a true positive, and have been curated';
  $statsHashToDescription{"svm low val tp ncur"} = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence, have been confirmed by a curator to have the data type and, hence, be a true positive, and have not yet been curated';
  $statsHashToDescription{"svm low val fp"}      = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence and have been confirmed by a curator to lack the data type and, hence, be a false positive';
  $statsHashToDescription{"svm low nval"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm low ncur"}        = 'Papers that have been flagged as positive for the indicated data type by the Support Vector Machine (SVM) at low confidence and have not been curated (True positives, not curated + Not validated)';
  $statsHashToDescription{"svm neg"}             = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM)';
  $statsHashToDescription{"svm neg val"}         = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM) and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm neg val tn"}      = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM) and have been confirmed by a curator to lack the data type and, hence, be a true negative';
  $statsHashToDescription{"svm neg val fn"}      = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM) and have been confirmed by a curator to have the data type and, hence, be a false negative';
  $statsHashToDescription{"svm neg val fn cur"}  = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM), have been confirmed by a curator to have the data type and, hence, be a false negative, and have been curated';
  $statsHashToDescription{"svm neg val fn ncur"} = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM), have been confirmed by a curator to have the data type and, hence, be a false negative, and have not yet been curated';
  $statsHashToDescription{"svm neg nval"}        = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM) and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"svm neg ncur"}        = 'Papers that have been flagged as negative for the indicated data type by the Support Vector Machine (SVM) and have not been curated (True negatives + Not validated)';

  $statsHashToDescription{"afpemailed"}          = 'Papers for which authors have been e-mailed to request that they fill out the Author First Pass (AFP) form';
  $statsHashToDescription{"afp"}                 = 'Papers for which authors have filled out the Author First Pass (AFP) form';
  $statsHashToDescription{"afp pos"}             = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP)';
  $statsHashToDescription{"afp pos val"}         = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP) and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"afp pos val tp"}      = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP) and have been confirmed by a curator to have the data type and, hence, be a true positive';
  $statsHashToDescription{"afp pos val tp cur"}  = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP), have been confirmed by a curator to have the data type and, hence, be a true positive, and have been curated';
  $statsHashToDescription{"afp pos val tp ncur"} = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP), have been confirmed by a curator to have the data type and, hence, be a true positive, and have not yet been curated';
  $statsHashToDescription{"afp pos val fp"}      = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP) and have been confirmed by a curator to lack the data type and, hence, be a false positive';
  $statsHashToDescription{"afp pos nval"}        = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP) and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"afp pos ncur"}        = 'Papers that have been flagged as positive for the indicated data type by Author First Pass (AFP) and have not been curated (True positives, not curated + Not validated)';
  $statsHashToDescription{"afp neg"}             = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP)';
  $statsHashToDescription{"afp neg val"}         = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP) and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"afp neg val tn"}      = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP) and have been confirmed by a curator to lack the data type and, hence, be a true negative';
  $statsHashToDescription{"afp neg val fn"}      = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP) and have been confirmed by a curator to have the data type and, hence, be a false negative';
  $statsHashToDescription{"afp neg val fn cur"}  = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP), have been confirmed by a curator to have the data type and, hence, be a false negative, and have been curated';
  $statsHashToDescription{"afp neg val fn ncur"} = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP), have been confirmed by a curator to have the data type and, hence, be a false negative, and have not yet been curated';
  $statsHashToDescription{"afp neg nval"}        = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP) and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"afp neg ncur"}        = 'Papers that have been flagged as negative for the indicated data type by Author First Pass (AFP) and have not been curated (True negatives + Not validated)';

  $statsHashToDescription{"cfp"}                 = 'Papers for which curators have filled out the Curator First Pass (CFP) form';
  $statsHashToDescription{"cfp pos"}             = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP)';
  $statsHashToDescription{"cfp pos val"}         = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP) and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"cfp pos val tp"}      = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP) and have been confirmed by a curator to have the data type and, hence, be a true positive';
  $statsHashToDescription{"cfp pos val tp cur"}  = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP), have been confirmed by a curator to have the data type and, hence, be a true positive, and have been curated';
  $statsHashToDescription{"cfp pos val tp ncur"} = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP), have been confirmed by a curator to have the data type and, hence, be a true positive, and have not yet been curated';
  $statsHashToDescription{"cfp pos val fp"}      = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP) and have been confirmed by a curator to lack the data type and, hence, be a false positive';
  $statsHashToDescription{"cfp pos nval"}        = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP) and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"cfp pos ncur"}        = 'Papers that have been flagged as positive for the indicated data type by Curator First Pass (CFP) and have not been curated (True positives, not curated + Not validated)';
  $statsHashToDescription{"cfp neg"}             = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP)';
  $statsHashToDescription{"cfp neg val"}         = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP) and have been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"cfp neg val tn"}      = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP) and have been confirmed by a curator to lack the data type and, hence, be a true negative';
  $statsHashToDescription{"cfp neg val fn"}      = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP) and have been confirmed by a curator to have the data type and, hence, be a false negative';
  $statsHashToDescription{"cfp neg val fn cur"}  = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP), have been confirmed by a curator to have the data type and, hence, be a false negative, and have been curated';
  $statsHashToDescription{"cfp neg val fn ncur"} = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP), have been confirmed by a curator to have the data type and, hence, be a false negative, and have not yet been curated';
  $statsHashToDescription{"cfp neg nval"}        = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP) and have not been confirmed by a curator either to have the indicated data type or not';
  $statsHashToDescription{"cfp neg ncur"}        = 'Papers that have been flagged as negative for the indicated data type by Curator First Pass (CFP) and have not been curated (True negatives + Not validated)';
} # sub populateStatisticsHashToDescription

sub populateStatisticsHashToLabel {
  $statsHashToLabel{"allcur"}              = 'Papers curated';
  $statsHashToLabel{"allval"}              = 'Papers validated';
  $statsHashToLabel{"allval pos"}          = 'Papers validated positive';
  $statsHashToLabel{"allval pos cur"}      = 'Papers validated positive curated';
  $statsHashToLabel{"allval pos ncur"}     = 'Papers validated positive not curated';
  $statsHashToLabel{"allval neg"}          = 'Papers validated negative';
  $statsHashToLabel{"allval conf"}         = 'Papers validated conflict';

  $statsHashToLabel{"any"}                 = 'Any flagged';
  $statsHashToLabel{"any pos"}             = 'Any positive';
  $statsHashToLabel{"any pos val"}         = 'Any positive validated';
  $statsHashToLabel{"any pos val tp"}      = 'Any positive validated true  positive';
  $statsHashToLabel{"any pos val tp cur"}  = 'Any positive validated true  positive curated';
  $statsHashToLabel{"any pos val tp ncur"} = 'Any positive validated true  positive not curated';
  $statsHashToLabel{"any pos val fp"}      = 'Any positive validated false positive';
  $statsHashToLabel{"any pos nval"}        = 'Any positive not validated';
  $statsHashToLabel{"any pos ncur"}        = 'Any positive not curated';
#   $statsHashToLabel{"any neg"}        = 'Any negative';		# these are not useful, would be among set of flagged that are not positive
#   $statsHashToLabel{"any neg val"}    = 'Any negative validated';
#   $statsHashToLabel{"any neg val tn"} = 'Any negative validated true  negative';
#   $statsHashToLabel{"any neg val fn"} = 'Any negative validated false negative';
#   $statsHashToLabel{"any neg nval"}   = 'Any negative not validated';

  $statsHashToLabel{"int"}                 = 'Intersection flagged';
  $statsHashToLabel{"int pos"}             = 'Intersection positive';
  $statsHashToLabel{"int pos val"}         = 'Intersection positive validated';
  $statsHashToLabel{"int pos val tp"}      = 'Intersection positive validated true  positive';
  $statsHashToLabel{"int pos val tp cur"}  = 'Intersection positive validated true  positive curated';
  $statsHashToLabel{"int pos val tp ncur"} = 'Intersection positive validated true  positive not curated';
  $statsHashToLabel{"int pos val fp"}      = 'Intersection positive validated false positive';
  $statsHashToLabel{"int pos nval"}        = 'Intersection positive not validated';
  $statsHashToLabel{"int pos ncur"}        = 'Intersection positive not curated';

  $statsHashToLabel{"svmnotdone"}          = 'SVM no svm processed';
  $statsHashToLabel{"svm"}                 = 'SVM has svm';
  $statsHashToLabel{"svm neg"}             = 'SVM negative';
  $statsHashToLabel{"svm neg val"}         = 'SVM negative validated';
  $statsHashToLabel{"svm neg val tn"}      = 'SVM negative validated true  negative';
  $statsHashToLabel{"svm neg val fn"}      = 'SVM negative validated false negative';
  $statsHashToLabel{"svm neg val fn cur"}  = 'SVM negative validated false negative curated';
  $statsHashToLabel{"svm neg val fn ncur"} = 'SVM negative validated false negative not curated';
  $statsHashToLabel{"svm neg nval"}        = 'SVM negative not validated';
  $statsHashToLabel{"svm neg ncur"}        = 'SVM negative not curated';
  $statsHashToLabel{"svm pos"}             = 'SVM positive any';
  $statsHashToLabel{"svm pos val"}         = 'SVM positive any validated';
  $statsHashToLabel{"svm pos val tp"}      = 'SVM positive any validated true  positive';
  $statsHashToLabel{"svm pos val tp cur"}  = 'SVM positive any validated true  positive curated';
  $statsHashToLabel{"svm pos val tp ncur"} = 'SVM positive any validated true  positive not curated';
  $statsHashToLabel{"svm pos val fp"}      = 'SVM positive any validated false positive';
  $statsHashToLabel{"svm pos nval"}        = 'SVM positive any not validated';
  $statsHashToLabel{"svm pos ncur"}        = 'SVM positive any not curated';
  $statsHashToLabel{"svm hig"}             = 'SVM positive high';
  $statsHashToLabel{"svm hig val"}         = 'SVM positive high validated';
  $statsHashToLabel{"svm hig val tp"}      = 'SVM positive high validated true  positive';
  $statsHashToLabel{"svm hig val tp cur"}  = 'SVM positive high validated true  positive curated';
  $statsHashToLabel{"svm hig val tp ncur"} = 'SVM positive high validated true  positive not curated';
  $statsHashToLabel{"svm hig val fp"}      = 'SVM positive high validated false positive';
  $statsHashToLabel{"svm hig nval"}        = 'SVM positive high not validated';
  $statsHashToLabel{"svm hig ncur"}        = 'SVM positive high not curated';
  $statsHashToLabel{"svm med"}             = 'SVM positive medium';
  $statsHashToLabel{"svm med val"}         = 'SVM positive medium validated';
  $statsHashToLabel{"svm med val tp"}      = 'SVM positive medium validated true  positive';
  $statsHashToLabel{"svm med val tp cur"}  = 'SVM positive medium validated true  positive curated';
  $statsHashToLabel{"svm med val tp ncur"} = 'SVM positive medium validated true  positive not curated';
  $statsHashToLabel{"svm med val fp"}      = 'SVM positive medium validated false positive';
  $statsHashToLabel{"svm med nval"}        = 'SVM positive medium not validated';
  $statsHashToLabel{"svm med ncur"}        = 'SVM positive medium not curated';
  $statsHashToLabel{"svm low"}             = 'SVM positive low';
  $statsHashToLabel{"svm low val"}         = 'SVM positive low validated';
  $statsHashToLabel{"svm low val tp"}      = 'SVM positive low validated true  positive';
  $statsHashToLabel{"svm low val tp cur"}  = 'SVM positive low validated true  positive curated';
  $statsHashToLabel{"svm low val tp ncur"} = 'SVM positive low validated true  positive not curated';
  $statsHashToLabel{"svm low val fp"}      = 'SVM positive low validated false positive';
  $statsHashToLabel{"svm low nval"}        = 'SVM positive low not validated';
  $statsHashToLabel{"svm low ncur"}        = 'SVM positive low not curated';

  $statsHashToLabel{"afpemailed"}          = 'AFP emailed';
  $statsHashToLabel{"afp"}                 = 'AFP flagged';
  $statsHashToLabel{"afp neg"}             = 'AFP negative';
  $statsHashToLabel{"afp neg val"}         = 'AFP negative validated';
  $statsHashToLabel{"afp neg val tn"}      = 'AFP negative validated true  negative';
  $statsHashToLabel{"afp neg val fn"}      = 'AFP negative validated false negative';
  $statsHashToLabel{"afp neg val fn cur"}  = 'AFP negative validated false negative curated';
  $statsHashToLabel{"afp neg val fn ncur"} = 'AFP negative validated false negative not curated';
  $statsHashToLabel{"afp neg nval"}        = 'AFP negative not validated';
  $statsHashToLabel{"afp neg ncur"}        = 'AFP negative not curated';
  $statsHashToLabel{"afp pos"}             = 'AFP positive';
  $statsHashToLabel{"afp pos val"}         = 'AFP positive validated';
  $statsHashToLabel{"afp pos val tp"}      = 'AFP positive validated true  positive';
  $statsHashToLabel{"afp pos val tp cur"}  = 'AFP positive validated true  positive curated';
  $statsHashToLabel{"afp pos val tp ncur"} = 'AFP positive validated true  positive not curated';
  $statsHashToLabel{"afp pos val fp"}      = 'AFP positive validated false positive';
  $statsHashToLabel{"afp pos nval"}        = 'AFP positive not validated';
  $statsHashToLabel{"afp pos ncur"}        = 'AFP positive not curated';
#   $statsHashToLabel{"afp pos ncur"}        = 'AFP positive not curated MINUS validated negative';

  $statsHashToLabel{"cfp"}                 = 'CFP flagged';
  $statsHashToLabel{"cfp neg"}             = 'CFP negative';
  $statsHashToLabel{"cfp neg val"}         = 'CFP negative validated';
  $statsHashToLabel{"cfp neg val tn"}      = 'CFP negative validated true  negative';
  $statsHashToLabel{"cfp neg val fn"}      = 'CFP negative validated false negative';
  $statsHashToLabel{"cfp neg val fn cur"}  = 'CFP negative validated false negative curated';
  $statsHashToLabel{"cfp neg val fn ncur"} = 'CFP negative validated false negative not curated';
  $statsHashToLabel{"cfp neg nval"}        = 'CFP negative not validated';
  $statsHashToLabel{"cfp neg ncur"}        = 'CFP negative not curated';
  $statsHashToLabel{"cfp pos"}             = 'CFP positive';
  $statsHashToLabel{"cfp pos val"}         = 'CFP positive validated';
  $statsHashToLabel{"cfp pos val tp"}      = 'CFP positive validated true  positive';
  $statsHashToLabel{"cfp pos val tp cur"}  = 'CFP positive validated true  positive curated';
  $statsHashToLabel{"cfp pos val tp ncur"} = 'CFP positive validated true  positive not curated';
  $statsHashToLabel{"cfp pos val fp"}      = 'CFP positive validated false positive';
  $statsHashToLabel{"cfp pos nval"}        = 'CFP positive not validated';
  $statsHashToLabel{"cfp pos ncur"}        = 'CFP positive not curated';
#   $statsHashToLabel{"cfp pos ncur"}        = 'CFP positive not curated (not validated + TP not curated)';

  $statsHashToLabel{"dividerany"}     = '&nbsp;';
  $statsHashToLabel{"dividerint"}     = '&nbsp;';
  $statsHashToLabel{"dividersvm"}     = '&nbsp;';
  $statsHashToLabel{"dividerafp"}     = '&nbsp;';
  $statsHashToLabel{"dividercfp"}     = '&nbsp;';
} # sub populateStatisticsHashToLabel

__END__
 
for full statistics table with all flagging methods and datatypes
beforePopulateCuratablePapers 0.000336885452270508
populateCuratablePapers 0.218996047973633
IN populateCuratedPapers populateCurCurData 0.00215005874633789
IN populateCuratedPapers populateOA 3.30496501922607
IN populateCuratedPapers categorizing hash 0.0882189273834229
populateCuratedPapers 3.40195512771606
populateCfpData 0.567224979400635
populateAfpData 0.16421103477478
populateSvmData 2.73913407325745
printCurationStatistics Datatypes / Objects 0.00141000747680664
getCurationtStatisticsAll 0.298819065093994
getStatsSvm 6.75205397605896
getStatsAfp 0.695372104644775
getStatsCfp 3.10928511619568
getStatsAny 1.49236798286438
recurseCurStats 3.57693600654602
printCurationStatisticsTable 23.0181729793549


