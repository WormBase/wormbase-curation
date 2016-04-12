#!/usr/bin/perl 

# Form to submit phenotype data

# Your Name (person ontology)
# Your e-mail address (remember in postgres)
# Enter _one_ pubmed id.  (process to convert to WBPaper if found)
# allele name (wbvar ontology), free text also, after blurring on field show message if not a valid value.
#   Red : WARNING! The allele name that you have entered is not recognized by WormBase.
#   Red : WARNING! The allele code you have entered is not recognized by WormBase. Please correct the allele code or request a new code by e-mailing genenames@wormbase.org .
# Observed Phenotype (ontology, multivalue in separate rows)
#   below box "Browse the Phenotype Ontology here" link to http://www.wormbase.org/tools/ontology_browser
# Can't find your phenotype (please enter a description of your phenotype)
#   two separate boxes, one for suggested term + one for suggested definition.  allow N pairs.  put those in app_suggested + app_suggested_definition
# NOT Observed Phenotype (ontology, multivalue in separate rows)
# Can't find your phenotype (please enter a description of your phenotype)
# Phenotype Comment (one box for all comments)
# optional section for nature / function / penetrance / tempsens
#
# if variation does not map to WBVariation, email Mary Ann
# if pmid does not map to WBPaper, email Kimberly
# if something does not map (phenotype | variation | pmid) set app_nodump + app_needsreview
# for now always set app_needsreview

# on term info fields, onblur clear term info, onfocus load whatever would match there.
# allele field, onblur do checks.

# possible to enter data with blank name, now checking termid_1_person for ~ /WBPerson/
# also blocked specific IP spammer.  2015 09 01
#
# cc: chris + gary + karen.  2015 09 08
#
# changed from allele-phenotype.cgi to phenotype.cgi
# added notice check for transgenes.
# live on tazendra.  2016 01 19
#
# changed ip to come from header HTTP_X_REAL_IP if it exists.  2016 02 05
#
# if there is no rnai, its species should be blank (not generalized for other fields).  2016 02 18



use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;
use Tie::IxHash;
use LWP::Simple;
use File::Basename;		# fileparse
use Mail::Sendmail;
use Net::Domain qw(hostname hostfqdn hostdomain);


my $hostfqdn = hostfqdn();

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $result;




my $query = new CGI;
my %fields;
tie %fields, "Tie::IxHash";
my %dropdown;
tie %dropdown, "Tie::IxHash";

my %mandatoryToLabel;
$mandatoryToLabel{'mandatory'}  = '<span style="color: red">M</span>';
$mandatoryToLabel{'anyanatomy'} = '<span style="color: #06C729">A</span>';
$mandatoryToLabel{'internal'}   = '<span style="color: grey">I</span>';
$mandatoryToLabel{'optional'}   = '';
$mandatoryToLabel{'transgene'}  = '';
$mandatoryToLabel{'construct'}  = '';
# $mandatoryToLabel{'optional'}   = '<span style="color: black">O</span>';
# $mandatoryToLabel{'transgene'}  = '<span style="color: brown">T</span>';
# $mandatoryToLabel{'construct'}  = '<span style="color: orange">C</span>';
my %mandatoryToClass;
$mandatoryToClass{'transgene'}  = 'mandatory_method mandatory_method_transgene';
$mandatoryToClass{'construct'}  = 'mandatory_method mandatory_method_construct';
my %fieldToClass;
$fieldToClass{'transgene'}  = 'field_method field_method_transgene';
$fieldToClass{'construct'}  = 'field_method field_method_construct';

my $title = 'Phenotype form';
my ($header, $footer) = &cshlNew($title);
# $header = "<html><head></head>";
# $header .= qq(<img src="/~acedb/draciti/Micropublication/uP_logo.png"><br/>\n);		# logo for Daniela
# $footer = "</body></html>";
&addJavascriptCssToHeader();


my $var;
($var, my $action) = &getHtmlVar($query, 'action');
unless ($action) { $action = 'showStart'; }			# by default show the start of the form

if ($action) {
  &initFields();
  if ($action eq 'showStart') {                              &showStart();          }
    elsif ($action eq 'Submit') {                            &submit('submit');     }
    elsif ($action eq 'Preview') {                           &submit('preview');    }
#     elsif ($action eq 'Save for Later') {                    &submit('save');       }
#     elsif ($action eq 'Load') {                              &load();               }
    elsif ($action eq 'autocompleteXHR') {                   &autocompleteXHR();    }
    elsif ($action eq 'asyncTermInfo') {                     &asyncTermInfo();      }
#     elsif ($action eq 'pmidToTitle') {                       &pmidToTitle();        }
    elsif ($action eq 'asyncFieldCheck') {                   &asyncFieldCheck();    }
    elsif ($action eq 'preexistingData') {                   &preexistingData();    }
    elsif ($action eq 'personPublication') {                 &personPublication();  }
    elsif ($action eq 'emailFlagFirstpass') {                &emailFlagFirstpass(); }
    elsif ($action eq 'bogusSubmission') {                   &bogusSubmission();    }
    else {                                                   &showStart();          }
}

sub bogusSubmission {
  print "Content-type: text/html\n\n";
  print $header;
  print qq(Thank you. This WormBase phenotype submission has been flagged for removal.<br/>);
  ($var, my $ip)       = &getHtmlVar($query, 'ipAddress');
  ($var, my $pgidsApp) = &getHtmlVar($query, 'pgidsApp');
  ($var, my $pgidsRna) = &getHtmlVar($query, 'pgidsRna');
  my $user             = 'phenotype_form@' . $hostfqdn;	# who sends mail
  my $email = 'cgrove@caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
#   my $email = 'closertothewake@gmail.com';
  my $subject = 'Phenotype form unauthorized or retracted submission';		# subject of mail
  my $body = qq(Unauthorized or retracted submission from $ip with pgidsApp $pgidsApp + pgidsRna $pgidsRna); 
# UNCOMMENT send chris emails
  &mailSendmail($user, $email, $subject, $body);
  print $footer;
} # sub bogusSubmission

sub emailFlagFirstpass {
  print "Content-type: text/html\n\n";
  print $header;
  my ($var, $wbperson)     = &getHtmlVar($query, 'wbperson');	# WBPerson ID
  my ($var, $wbpaper)      = &getHtmlVar($query, 'wbpaper');	# WBPaper ID
  my $user        = 'phenotype_form@' . $hostfqdn;	# who sends mail
  my $email       = 'cgrove@caltech.edu';
#   my $email       = 'closertothewake@gmail.com';
  my $subject     = qq(Phenotype Form: Flag $wbpaper by $wbperson);
  print "Thank you for flagging $wbpaper for phenotype curation.<br/>\n";
# UNCOMMENT send chris emails
  &mailSendmail($user, $email, $subject, $subject);
  print $footer;
} # sub emailFlagFirstpass

sub personPublication {
  print "Content-type: text/html\n\n";
  print $header;
  my %flaggedPapers;	# paper -> datatype -> counter   paper is the only important thing for being in $relevant, but datatype is important for datatype's curation status
  my $curStatusUrl = 'http://' . $hostfqdn . "/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=newmutant&method=any%20pos%20ncur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on";
#   print qq(URL $curStatusUrl URL);
  my $curStatusData = get $curStatusUrl;
  my ($curStatusJoinkeys) = $curStatusData =~ m/name="specific_papers">(.*?)<\/textarea/;
  my (@paps) = split/\s+/, $curStatusJoinkeys; foreach (@paps) { $flaggedPapers{"WBPaper$_"}{app}++; }
  $curStatusUrl = 'http://' . $hostfqdn . "/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=newmutant&method=allval pos ncur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on";	# any positive not curated
  $curStatusData = get $curStatusUrl;
  ($curStatusJoinkeys) = $curStatusData =~ m/name="specific_papers">(.*?)<\/textarea/;
  (@paps) = split/\s+/, $curStatusJoinkeys; foreach (@paps) { $flaggedPapers{"WBPaper$_"}{app}++; }
  $curStatusUrl = 'http://' . $hostfqdn . "/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=rnai&method=any%20pos%20ncur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on";		# validated positive not curated
  $curStatusData = get $curStatusUrl;
  ($curStatusJoinkeys) = $curStatusData =~ m/name="specific_papers">(.*?)<\/textarea/;
  (@paps) = split/\s+/, $curStatusJoinkeys; foreach (@paps) { $flaggedPapers{"WBPaper$_"}{rna}++; }
  $curStatusUrl = 'http://' . $hostfqdn . "/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=rnai&method=allval pos ncur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on";
  $curStatusData = get $curStatusUrl;
  ($curStatusJoinkeys) = $curStatusData =~ m/name="specific_papers">(.*?)<\/textarea/;
  (@paps) = split/\s+/, $curStatusJoinkeys; foreach (@paps) { $flaggedPapers{"WBPaper$_"}{rna}++; }
  ($var, my $personId)      = &getHtmlVar($query, 'personId');			# WBPerson ID
  ($var, my $personName)    = &getHtmlVar($query, 'personName');		# WBPerson Name
  ($var, my $personEmail)   = &getHtmlVar($query, 'personEmail');		# email address
  my $twonum = $personId; $twonum =~ s/WBPerson/two/;
  print "WormBase Publications for $personName ($personId) :<br/><br/>\n";
  my %aids;
  $result = $dbh->prepare( "SELECT * FROM pap_author_possible WHERE pap_author_possible = '$twonum';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $aids{pos}{$row[0]}{$row[2]}++; }
  my $aids_possible = join"','", sort keys %{ $aids{pos} };
  $result = $dbh->prepare( "SELECT * FROM pap_author_verified WHERE author_id IN ('$aids_possible') AND pap_author_verified ~ 'YES';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $aids{ver}{$row[0]}{$row[2]}++; }
  foreach my $aid (sort keys %{ $aids{pos} }) {
    foreach my $join (sort keys %{ $aids{pos}{$aid} }) {
      if ($aids{pos}{$aid}{$join} && $aids{ver}{$aid}{$join}) { $aids{good}{$aid}++; } } }
  my $aids_good = join"','", sort keys %{ $aids{good} };

  my %paps; my %papJoinkeys;
  $result = $dbh->prepare( "SELECT * FROM pap_author WHERE pap_author IN ('$aids_good');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $paps{"WBPaper$row[0]"}++; $papJoinkeys{$row[0]}++; }
  my $paps = join"','", sort keys %paps;
  my $papJoinkeys = join"','", sort keys %papJoinkeys;
  my %hasApp; my %hasRnai; my %hasWBCurator; my %hasComCurator;
  $result = $dbh->prepare( "SELECT * FROM app_paper WHERE app_paper IN ('$paps') AND joinkey IN (SELECT joinkey FROM app_variation);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasApp{$row[0]} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM app_paper WHERE app_paper IN ('$paps') AND joinkey IN (SELECT joinkey FROM app_transgene);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasApp{$row[0]} = $row[1]; }
  my $pgidHasApp = join"','", sort keys %hasApp;
  $result = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN ('$pgidHasApp') AND app_curator = 'WBPerson29819' AND joinkey NOT IN (SELECT joinkey FROM app_needsreview);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasComCurator{$hasApp{$row[0]}}{app}++; }
  $result = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN ('$pgidHasApp') AND app_curator != 'WBPerson29819' AND joinkey NOT IN (SELECT joinkey FROM rna_nodump);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasWBCurator{$hasApp{$row[0]}}{app}++; }
  $result = $dbh->prepare( "SELECT * FROM rna_paper WHERE rna_paper IN ('$paps') AND joinkey IN (SELECT joinkey FROM rna_name);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasRnai{$row[0]} = $row[1]; }
  my $pgidHasRnai = join"','", sort keys %hasRnai;
  $result = $dbh->prepare( "SELECT * FROM rna_curator WHERE joinkey IN ('$pgidHasRnai') AND rna_curator = 'WBPerson29819' AND joinkey NOT IN (SELECT joinkey FROM rna_needsreview);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasComCurator{$hasRnai{$row[0]}}{rna}++; }
  $result = $dbh->prepare( "SELECT * FROM rna_curator WHERE joinkey IN ('$pgidHasRnai') AND rna_curator != 'WBPerson29819' AND joinkey NOT IN (SELECT joinkey FROM rna_nodump);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasWBCurator{$hasRnai{$row[0]}}{rna}++; }

  my %primary; my %pmids; my %dois; my %title; my %journal; my %year; my %authors; my %aidName;
  $result = $dbh->prepare( "SELECT * FROM pap_primary_data WHERE joinkey IN ('$papJoinkeys') AND pap_primary_data = 'primary';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $primary{"WBPaper$row[0]"} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey IN ('$papJoinkeys') AND pap_identifier ~ 'doi';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $row[1] =~ s/^doi/doi /; $dois{"WBPaper$row[0]"} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey IN ('$papJoinkeys') AND pap_identifier ~ 'pmid';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $pmids{"WBPaper$row[0]"} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_title WHERE joinkey IN ('$papJoinkeys');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $title{"WBPaper$row[0]"} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_journal WHERE joinkey IN ('$papJoinkeys');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $journal{"WBPaper$row[0]"} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_year WHERE joinkey IN ('$papJoinkeys');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $year{"WBPaper$row[0]"} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_author WHERE joinkey IN ('$papJoinkeys');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $aidName{need}{$row[1]}++; }
  my $author_ids = join"','", sort keys %{ $aidName{need} };
  $result = $dbh->prepare( "SELECT * FROM pap_author_index WHERE author_id IN ('$author_ids');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $aidName{name}{$row[0]} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM pap_author WHERE joinkey IN ('$papJoinkeys');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    if ($aidName{name}{$row[1]}) {
      $authors{"WBPaper$row[0]"}{$row[2]} = $aidName{name}{$row[1]}; } }

  my %trs;
  foreach my $paper (sort keys %paps) {
    next unless ($primary{$paper});
    my $relevant = 'not';
    my $pmid; my $doi; my $title; my $journal; my $year; my $authors; my @authors;
    if ($pmids{$paper}) {      $pmid    = $pmids{$paper};   }
    if ($dois{$paper}) {       $doi     = $dois{$paper};    }
    if ($title{$paper}) {      $title   = $title{$paper};   }
    if ($journal{$paper}) {    $journal = $journal{$paper}; }
    if ($year{$paper}) {       $year    = $year{$paper};    }
    foreach my $order (sort {$a<=>$b} keys %{ $authors{$paper} }) { push @authors, $authors{$paper}{$order}; }
    if (scalar @authors > 0) { $authors = join"; ", @authors; }
    my $tr = '<tr>';
    my $pmidForForm = $paper; if ($pmid) { $pmidForForm = $pmid; } elsif ($doi) { $pmidForForm = $doi; }

#   ($var, my $personId)      = &getHtmlVar($query, 'personId');			# WBPerson ID
#   ($var, my $personName)    = &getHtmlVar($query, 'personName');		# WBPerson Name
#   ($var, my $personEmail)   = &getHtmlVar($query, 'personEmail');		# email address
#   ($var, my $pmid)        = &getHtmlVar($query, "input_1_pmid");	# if linking here from personPublication table
#   ($var, my $personName)  = &getHtmlVar($query, "input_1_person");	# if linking here from personPublication table
#   ($var, my $personId)    = &getHtmlVar($query, "termid_1_person");	# if linking here from personPublication table
#   ($var, my $personEmail) = &getHtmlVar($query, "input_1_email");	# if linking here from personPublication table

    my $curation_status   = qq(placeholder, report if seen);
    if ($flaggedPapers{$paper})      { $relevant = 'relevant'; }	# flagged papers are relevant
      elsif ($hasWBCurator{$paper})  { $relevant = 'relevant'; }	# wormbase curated papers are relevant
      elsif ($hasComCurator{$paper}) { $relevant = 'relevant'; }	# user curated papers are relevant
      else {	# not flagged, give link to this form to email Chris that the paper should be flagged
        $curation_status   = qq(<a href='phenotype.cgi?action=emailFlagFirstpass&wbpaper=$paper&wbperson=$personId' target='_blank' style='font-weight: bold; text-decoration: underline;'>flag this for phenotype data</a>); }
   if ($relevant eq 'relevant') {
      my $urlPreexisting  = 'http://' . $hostfqdn .  "/~azurebrd/cgi-bin/forms/phenotype.cgi?action=preexistingData&wbpaper=$paper";
      my %datatypeLabels; $datatypeLabels{app} = 'Allele-Transgene'; $datatypeLabels{rna} = 'RNAi'; 
      my @curation_status;
      foreach my $datatype (sort keys %datatypeLabels) {
        my $datatype_label = '';
        if ($hasWBCurator{$paper}{$datatype}) {       $datatype_label = qq(<a href='$urlPreexisting' target='_blank' style='font-weight: bold; text-decoration: underline;'>$datatypeLabels{$datatype} WormBase curated</a>);     }
          elsif ($hasComCurator{$paper}{$datatype}) { $datatype_label = qq(<a href='$urlPreexisting' target='_blank' style='font-weight: bold; text-decoration: underline;'>$datatypeLabels{$datatype} Curation in progress</a>); }
          elsif ($flaggedPapers{$paper}{$datatype}) { $datatype_label = qq(<a href='phenotype.cgi?action=showStart&input_1_pmid=$pmid&input_1_person=$personName&termid_1_person=$personId&input_1_email=$personEmail' target='_blank' style='font-weight: bold; text-decoration: underline;'>$datatypeLabels{$datatype} Needs curation</a>); }
          else {                                      $datatype_label = qq(<a href='phenotype.cgi?action=emailFlagFirstpass&wbpaper=$paper&wbperson=$personId' target='_blank' style='font-weight: bold; text-decoration: underline;'>flag this for $datatypeLabels{$datatype} phenotype data</a>); }
        if ($datatype_label) {
          push @curation_status, $datatype_label; }
      }
      if (scalar @curation_status > 0) { $curation_status = join"<br/><br/>", @curation_status; }
    }
    $tr .= qq(<td style='width: 120px;'>$curation_status</td>);
    $tr .= qq(<td>$pmid</td>);
    $tr .= qq(<td>$paper</td>);
    $tr .= qq(<td style='width: 90px; max-width: 90px; word-wrap: break-word;'>$doi</td>);
    $tr .= qq(<td>$title</td>);
    $tr .= qq(<td>$journal</td>);
    $tr .= qq(<td>$year</td>);
    $tr .= qq(<td>$authors</td>);
    $tr .= '</tr>';
    push @{ $trs{$relevant} }, $tr;
  } # foreach my $paper (sort keys %paps)

  my $countRelevant = 0; my $countNotrelevant = 0;
  if ($trs{'relevant'}) { $countRelevant    = scalar (@{ $trs{'relevant'} }); }
  if ($trs{'not'})      { $countNotrelevant = scalar (@{ $trs{'not'} });      }

  if ($countRelevant > 20) {
    print qq(<a href="#relevant">$countRelevant papers flagged likely to have phenotype data</a><br/>\n);
    print qq(<a href="#not_relevant">$countNotrelevant papers NOT flagged for phenotype data</a><br/><br/><br/>\n); }

  print qq(<a name="relevant">$countRelevant papers flagged likely to have phenotype data</a><br/>\n);
  print qq(<table border="1" cellpadding="5">);
  print qq(<th>Curation Status</th><th>PubMed ID</th><th>WBPaper ID</th><th>DOI</th><th>Title</th><th>Journal</th><th>Year</th><th>Authors</th>);
  foreach my $tr (@{ $trs{'relevant'} }) { print $tr; }
  print qq(</table><br/><br/>);

  print qq(<a name="not_relevant">$countNotrelevant papers NOT flagged for phenotype data</a><br/>\n);
  print qq(<table border="1" cellpadding="5">);
  print qq(<th>Curation Status</th><th>PubMed ID</th><th>WBPaper ID</th><th>DOI</th><th>Title</th><th>Journal</th><th>Year</th><th>Authors</th>);
  foreach my $tr (@{ $trs{'not'} }) { print $tr; }
  print qq(</table><br/><br/>);
  print $footer;
} # sub personPublication

sub preexistingData {		# given a WBPaper, show data that already exists in postgres
  print "Content-type: text/html\n\n";
  print $header;
  my ($var, $wbpaper)      = &getHtmlVar($query, 'wbpaper');                # what user enter as pmids
  my $pap_link = qq(<a href="http://www.wormbase.org/resources/paper/${wbpaper}#03--10" target="new">$wbpaper</a>);
  print qq(Data for $pap_link<br/><br/>);
  my $tdstyle = qq(style = "padding: 5px;");
  my %pedata; 							# pre existing data in postgres
  my %joinkeys;							# pgids that have an app_paper
  $result = $dbh->prepare( "SELECT joinkey FROM app_paper WHERE app_paper = '$wbpaper';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $joinkeys{$row[0]}++; }
  my $joinkeys = join"','", sort {$a<=>$b} keys %joinkeys;
  my @tables = qw( variation transgene curator communitycurator term not phen_remark nature func penetrance heat_sens cold_sens );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM app_$table WHERE joinkey IN ('$joinkeys') AND joinkey NOT IN (SELECT joinkey FROM app_needsreview) AND joinkey NOT IN (SELECT joinkey FROM app_nodump WHERE app_nodump = 'NO DUMP');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $pedata{app}{$row[0]}{$table} = $row[1]; }
  } # foreach my $table (@tables)
  my %mapToNames;
  $result = $dbh->prepare( "SELECT trp_name.trp_name, trp_publicname.trp_publicname FROM trp_name, trp_publicname WHERE trp_name.joinkey = trp_publicname.joinkey; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $mapToNames{'transgene'}{$row[0]} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM obo_name_variation ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $mapToNames{'variation'}{$row[0]} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM obo_name_phenotype ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $mapToNames{'phenotype'}{$row[0]} = $row[1]; }
  $result = $dbh->prepare( "SELECT * FROM two_standardname ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $row[0] =~ s/two/WBPerson/; $mapToNames{'person'}{$row[0]} = $row[2]; }
  my %sortFilter;						# data sorted by allele name, then observed phenotype name, then not observed phenotype name ; also each group of that could have multiple pgid rows of data.
  foreach my $pgid (sort {$a<=>$b} keys %{ $pedata{app} }) {
    my @data = ();
#     push @data, $pgid;
    my ($curId, $curName, $varId, $allele, $transgeneId, $transgeneName, $rnai, $phObsId, $phObsNa, $phNotId, $phNotNa, $phenRemark, $nature, $func, $penetrance, $cold, $heat) = ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''); 
    if ($pedata{app}{$pgid}{curator}) {  
      $curId = $pedata{app}{$pgid}{curator}; my $curatorType = 'WormBase Curator'; 
      if ($curId eq 'WBPerson29819') {     $curId   = $pedata{app}{$pgid}{communitycurator};   $curatorType = 'Community Curator'; }
      if ($mapToNames{'person'}{$curId}) { $curName = qq($curatorType - $mapToNames{'person'}{$curId}); }  }
    push @data, qq($curName);
    if ($pedata{app}{$pgid}{variation}) {  
      $varId = $pedata{app}{$pgid}{variation};
      if ($mapToNames{'variation'}{$varId}) { $allele = $mapToNames{'variation'}{$varId}; } }
    push @data, $allele;
    if ($pedata{app}{$pgid}{transgene}) {  
      $transgeneId = $pedata{app}{$pgid}{transgene};
      if ($mapToNames{'transgene'}{$transgeneId}) { $transgeneName = $mapToNames{'transgene'}{$transgeneId}; } }
    push @data, $transgeneName;
    push @data, $rnai;
    my $phenSort = 1; my $phenName = '';
    if ($pedata{app}{$pgid}{term}) {  
      my $phenId = $pedata{app}{$pgid}{term};
      if ($mapToNames{'phenotype'}{$phenId}) { $phenName = $mapToNames{'phenotype'}{$phenId}; }
      if ($pedata{app}{$pgid}{not}) { $phNotNa = $phenName; $phNotId = $phenId; $phenSort = 2; }
        else { $phObsNa = $phenName; $phObsId = $phenId; } }
    push @data, $phObsNa; push @data, $phNotNa;
    if ($pedata{app}{$pgid}{phen_remark}) {  
      $phenRemark = $pedata{app}{$pgid}{phen_remark}; }
    push @data, $phenRemark;
    if ($pedata{app}{$pgid}{nature}) {  
      $nature = $pedata{app}{$pgid}{nature};
      if ($dropdown{allelenature}{$nature}) { $nature = $dropdown{allelenature}{$nature}; } }
    push @data, $nature;
    if ($pedata{app}{$pgid}{func}) {  
      $func = $pedata{app}{$pgid}{func};
      if ($dropdown{allelefunction}{$func}) { $func = $dropdown{allelefunction}{$func}; } }
    push @data, $func;
    if ($pedata{app}{$pgid}{penetrance}) {  
      $penetrance = $pedata{app}{$pgid}{penetrance};
      if ($dropdown{penetrance}{$penetrance}) { $penetrance = $dropdown{penetrance}{$penetrance}; } }
    push @data, $penetrance;
    if ($pedata{app}{$pgid}{heat_sens}) { $heat = $pedata{app}{$pgid}{heat_sens}; }
    push @data, $heat;
    if ($pedata{app}{$pgid}{cold_sens}) { $cold = $pedata{app}{$pgid}{cold_sens}; }
    push @data, $cold;
    my $trData = join"</td><td $tdstyle>", @data;
    $trData = qq(<tr><td $tdstyle>$trData</td></tr>);
    push @{ $sortFilter{$allele}{$phenSort}{$phenName} }, $trData;
  } # foreach my $pgid (sort {$a<=>$b} keys %{ $pedata{app} })

  %joinkeys = ();
  $result = $dbh->prepare( "SELECT joinkey FROM rna_paper WHERE rna_paper = '$wbpaper';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $joinkeys{$row[0]}++; }
  $joinkeys = join"','", sort {$a<=>$b} keys %joinkeys;
  @tables = qw( name curator communitycurator phenotype phenotypenot phenremark penetrance );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM rna_$table WHERE joinkey IN ('$joinkeys') AND joinkey NOT IN (SELECT joinkey FROM rna_needsreview) AND joinkey NOT IN (SELECT joinkey FROM rna_nodump WHERE rna_nodump = 'NO DUMP');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $pedata{rna}{$row[0]}{$table} = $row[1]; }
  } # foreach my $table (@tables)
  foreach my $pgid (sort {$a<=>$b} keys %{ $pedata{rna} }) {
    my @data = ();
    my ($curId, $curName, $varId, $allele, $transgeneId, $transgeneName, $rnai, $phObsId, $phObsNa, $phNotId, $phNotNa, $phenRemark, $nature, $func, $penetrance, $cold, $heat) = ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''); 
    if ($pedata{rna}{$pgid}{curator}) {  
      $curId = $pedata{rna}{$pgid}{curator}; my $curatorType = 'WormBase Curator'; 
      if ($curId eq 'WBPerson29819') {     $curId   = $pedata{rna}{$pgid}{communitycurator};   $curatorType = 'Community Curator'; }
      if ($mapToNames{'person'}{$curId}) { $curName = qq($curatorType - $mapToNames{'person'}{$curId}); }  }
    push @data, qq($curName);
    push @data, $allele;
    push @data, $transgeneName;
    my $rnaiLink = '';
    if ($pedata{rna}{$pgid}{name}) {  
      $rnai = $pedata{rna}{$pgid}{name};
      $rnaiLink = qq(<a href="http://www.wormbase.org/species/c_elegans/rnai/${rnai}#0415--10" target="_blank">$rnai</a>); }
    push @data, $rnaiLink;
    my $phenSort = 1; my $phenName = '';
    if ($pedata{rna}{$pgid}{phenotype}) {  
      $pedata{rna}{$pgid}{phenotype} =~ s/"//g;
      my (@phenIds) = split/,/, $pedata{rna}{$pgid}{phenotype};
      my @phenNames;
      foreach my $phenId (@phenIds) {
        if ($mapToNames{'phenotype'}{$phenId}) { push @phenNames, $mapToNames{'phenotype'}{$phenId}; }
          else { push @phenNames, $phenId; } }
      my $phenNames = join", ", @phenNames;
      if ($pedata{rna}{$pgid}{phenotypenot}) { $phNotNa = $phenNames; $phenSort = 2; }
        else { $phObsNa = $phenNames; } }
    push @data, $phObsNa; push @data, $phNotNa;
    if ($pedata{rna}{$pgid}{phenremark}) {  
      $phenRemark = $pedata{rna}{$pgid}{phenremark}; }
    push @data, $phenRemark;
    push @data, $nature;
    push @data, $func;
    if ($pedata{rna}{$pgid}{penetrance}) {  
      $penetrance = $pedata{rna}{$pgid}{penetrance};
      if ($dropdown{penetrance}{$penetrance}) { $penetrance = $dropdown{penetrance}{$penetrance}; } }
    push @data, $penetrance;
    push @data, $heat;
    push @data, $cold;
    my $trData = join"</td><td $tdstyle>", @data;
    $trData = qq(<tr><td $tdstyle>$trData</td></tr>);
    push @{ $sortFilter{$rnai}{$phenSort}{$phenName} }, $trData;
  } # foreach my $pgid (sort {$a<=>$b} keys %{ $pedata{rna} })

  print qq(<table border="1">);
  my @headers = ( 'Curator', 'Allele', 'Transgene', 'RNAi', 'Observed Phenotype', "<span style='color: red;'>Not</span> Observed Phenotype", 'Phenotype Remark', 'Inheritance Pattern', 'Mutation Effect', 'Penetrance', 'Heat Sensitive', 'Cold Sensitive');
  my $thData = join"</th><th $tdstyle>", @headers;
  $thData = qq(<tr><th $tdstyle>$thData</th></tr>);
  print qq($thData);
  foreach my $allele (sort keys %sortFilter) {
    foreach my $phenSort (sort keys %{ $sortFilter{$allele} }) {
      foreach my $phenName (sort keys %{ $sortFilter{$allele}{$phenSort} }) {
        foreach my $trData (@{ $sortFilter{$allele}{$phenSort}{$phenName} }) {
          print qq($trData\n);
        } # foreach my $trData (@{ $sortFilter{$allele}{$phenSort}{$phenName} })
      } # foreach my $phenName (sort keys %{ $sortFilter{$allele}{$phenSort} })
    } # foreach my $phenSort (sort keys %{ $sortFilter{$allele} })
  } # foreach my $allele (sort keys %sortFilter)
  print qq(</table>);
  print $footer;
} # sub preexistingData

sub checkAllele {					# only return allele code warning if both checks fail
  my ($input) = @_;
  my $checkResults = 'ok'; 
  unless ($input) { return $checkResults; }
  my $alleleDesignation = $input; 
  if ($input =~ m/^([a-zA-Z]+)\d+/) { ($alleleDesignation) = $1; }
    else {
      if ($alleleDesignation =~ m/\'/) { $alleleDesignation =~ s/\'/''/g; }
      if ($alleleDesignation =~ m/\(/) { $alleleDesignation =~ s/\(/\\\(/g; }
      if ($alleleDesignation =~ m/\)/) { $alleleDesignation =~ s/\)/\\\)/g; } }
  ($alleleDesignation) = lc($alleleDesignation);
  $result = $dbh->prepare( "SELECT * FROM obo_data_laboratory WHERE obo_data_laboratory ~ 'Allele_designation: \"$alleleDesignation\"';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  unless ($row[1]) { return qq(<span style='color: red'>WARNING!  The allele code '$alleleDesignation' you have entered is not recognized by WormBase. Please correct the allele code or request a new code by e-mailing <a href='mailto:genenames\@wormbase.org'>genenames\@wormbase.org</a></span>); }
  $result = $dbh->prepare( "SELECT * FROM obo_name_variation WHERE obo_name_variation = '$input';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  unless ($row[1]) { return qq(<span style='color: brown'>Notice: The allele name '$input' that you have entered is not recognized by WormBase. If '$input' is a new allele, please continue your submission and a WormBase curator will contact you to confirm.</span>); }
#   my @warnings;
#   if (scalar @warnings > 0) { $checkResults = join"<br/>\n", @warnings; }
  return $checkResults;
} # sub checkAllele

sub checkTransgene {					# check transgene is valid object or give notice
  my ($input) = @_;
  my $checkResults = 'ok'; 
  unless ($input) { return $checkResults; }
  if ($input =~ m/;/) { $input =~ s/;/\\;/g; }
  $result = $dbh->prepare( "SELECT * FROM trp_publicname WHERE trp_publicname = '$input';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  unless ($row[1]) { return qq(<span style='color: brown'>Notice: The transgene name '$input' that you have entered is not recognized by WormBase. If '$input' is a new transgene, please continue your submission and a WormBase curator will contact you to confirm.</span>); }
  return $checkResults;
} # sub checkTransgene

sub checkPmid {					# only return allele code warning if both checks fail
  my ($userInput) = @_;
  my $checkResults = 'ok'; 
  unless ($userInput) { return $checkResults; }
  my $pmid = $userInput;
  if ($pmid =~ m/^\s+/) { $pmid =~ s/^\s+//; }
  if ($pmid =~ m/\s+$/) { $pmid =~ s/\s+$//; }
  if ($userInput =~ m/^pmid:?(\d+)/i) { $pmid = $1; }
  my $wbpaper = '';
  $result = $dbh->prepare( "SELECT joinkey FROM pap_identifier WHERE pap_identifier = 'pmid$pmid';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $wbpaper = "WBPaper$row[0]"; }
  my $queryResults = '';
  my $hasData = 0;
  $result = $dbh->prepare( "SELECT app_variation.app_variation, app_term.app_term FROM app_variation, app_term WHERE app_variation.joinkey = app_term.joinkey AND app_term.joinkey IN (SELECT joinkey FROM app_paper WHERE app_paper = '$wbpaper') AND app_term.joinkey NOT IN (SELECT joinkey FROM app_needsreview) AND app_term.joinkey NOT IN (SELECT joinkey FROM app_nodump WHERE app_nodump = 'NO DUMP');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $hasData++; }
  $result = $dbh->prepare( "SELECT app_transgene.app_transgene, app_term.app_term FROM app_transgene, app_term WHERE app_transgene.joinkey = app_term.joinkey AND app_term.joinkey IN (SELECT joinkey FROM app_paper WHERE app_paper = '$wbpaper') AND app_term.joinkey NOT IN (SELECT joinkey FROM app_needsreview) AND app_term.joinkey NOT IN (SELECT joinkey FROM app_nodump WHERE app_nodump = 'NO DUMP');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $hasData++; }
  $result = $dbh->prepare( "SELECT rna_name.rna_name, rna_phenotype.rna_phenotype FROM rna_name, rna_phenotype WHERE rna_name.joinkey = rna_phenotype.joinkey AND rna_phenotype.joinkey IN (SELECT joinkey FROM rna_paper WHERE rna_paper = '$wbpaper') AND rna_phenotype.joinkey NOT IN (SELECT joinkey FROM rna_needsreview) AND rna_phenotype.joinkey NOT IN (SELECT joinkey FROM rna_nodump WHERE rna_nodump = 'NO DUMP');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $hasData++; }
  if ($hasData) {
    my $url = 'http://' . $hostfqdn . "/~azurebrd/cgi-bin/forms/phenotype.cgi?action=preexistingData&wbpaper=$wbpaper";
    $checkResults = qq(<span style='color: brown'>Notice: The paper you have entered has already been curated for some phenotype data. Please refer to the <a href='$url' target='new' style='font-weight: bold; text-decoration: underline;'>phenotype data summary</a> for this paper. If you believe you have additional phenotype data for this paper, please proceed.</span>); }
  return $checkResults;
} # sub checkPmid

sub asyncFieldCheck {
  print "Content-type: text/plain\n\n";
  ($var, my $field)   = &getHtmlVar($query, 'field');
  ($var, my $input)   = &getHtmlVar($query, 'input');
  my $checkResults = 'ok';
  if ($field eq 'allele') {           ($checkResults) = &checkAllele($input); }
    elsif ($field eq 'transgene') {   ($checkResults) = &checkTransgene($input);   }
    elsif ($field eq 'pmid') {        ($checkResults) = &checkPmid($input);   }
  print "$checkResults";
} # sub asyncFieldCheck

sub asyncTermInfo {
  print "Content-type: text/plain\n\n";
  ($var, my $field)   = &getHtmlVar($query, 'field');
  ($var, my $termid)  = &getHtmlVar($query, 'termid');
  my $matches;

  if ( $fields{$field}{type} eq 'ontology' ) {
      ($matches) = &getAnyTermInfo($field, $termid); }      # generic obo and specific are different
    elsif ($field eq 'pmid') { $matches = &getPmidTermInfo($termid); }

  print "$matches\n";
} # sub asyncTermInfo

sub getAnyTermInfo {                                                    # call  &getAnySpecificTermInfo  or  &getGenericOboTermInfo  as appropriate
  my ($field, $termid) = @_; my $return_value = '';
  if ($fields{$field}{ontology_type} eq 'obo') {
      ($return_value) = &getGenericOboTermInfo($field, $termid); }
    else {
      my $ontology_type = $fields{$field}{ontology_type};
      ($return_value) = &getAnySpecificTermInfo($ontology_type, $termid); }
  return $return_value;
} # sub getAnyTermInfo

sub getGenericOboTermInfo {
  my ($field, $termid) = @_;
  my $obotable = $fields{$field}{ontology_table};
  if ($termid =~ m/\[.*?\]$/) { $termid =~ s/\[.*?\]$//; }
  unless ($termid) { return ''; }
  my $joinkey = $termid;
  if ($joinkey) {
    my $data_table =  'obo_data_' . $obotable;
    $result = $dbh->prepare( "SELECT * FROM $data_table WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
    unless ($row[1]) {
      my $name_table = 'obo_name_' . $obotable;
      $result = $dbh->prepare( "SELECT * FROM $data_table WHERE joinkey IN (SELECT joinkey FROM $name_table WHERE $name_table = '$joinkey');" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow(); }
#     unless ($row[1]) { return ''; }
    unless ($row[1]) { return qq(Term '$termid' is not recognized.); }
    my (@data) = split/\n/, $row[1];
    foreach my $data_line (@data) { 
      if ($data_line =~ /id: WBVar\d+/) {                  $data_line =~ s/(WBVar\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/c_elegans\/variation\/${1}#065--10\" target=\"new\">$1<\/a>/; }
      if ($data_line =~ /gene: "WBGene\d+ /) {             $data_line =~ s/(WBGene\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/c_elegans\/gene\/${1}#0b4--10\" target=\"new\">$1<\/a>/; }
      if ($data_line =~ /id : <\/span> WBPhenotype:\d+/) { $data_line =~ s/(WBPhenotype:\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/all\/phenotype\/${1}#06453--10\" target=\"new\">$1<\/a>/; }
      if ( ($field eq 'strain') && ($data_line =~ /id: [A-Z]+\d+/) ) {               $data_line =~ s/id: ([A-Z]+\d+)/id: <a href=\"http:\/\/www.wormbase.org\/species\/c_elegans\/strain\/${1}#03214--10\" target=\"new\">$1<\/a>/; }
      if ($data_line =~ /^(.*?(?:child|parent) : <\/span> )<a href.*?>(.*?)<\/a>/) { $data_line =~ s/^(.*?(?:child|parent) : <\/span> )<a href.*?>(.*?)<\/a>/${1}${2}/; }	# remove hyperlinks for parent + child (for phenotype)
      next if ($data_line =~ m/<span/);			# some already have bold span in the data
      $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
    my $data = join"<br />\n", @data;
    if ($field eq 'allele') { 
      my ($wbvarid) = $row[1] =~ m/id: (WBVar\d+)/; 
      my $wbvar_link = qq(<a href="http://www.wormbase.org/species/c_elegans/variation/${wbvarid}#065--10" target="new" style="font-weight: bold; text-decoration: underline;">here</a>);
      $data = qq(Click $wbvar_link to see known phenotypes for this allele<br/>\n) . $data; }
    return $data;
  } # if ($joinkey)
} # sub getGenericOboTermInfo

sub getAnySpecificTermInfo {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {          ($matches) = &getAnyWBPersonTermInfo($userValue); }
    elsif ($ontology_type eq 'WBTransgene') {       ($matches) = &getAnyWBTransgeneTermInfo($userValue); }

#   elsif ($ontology_type eq 'WBGene') {               ($matches) = &getAnyWBGeneTermInfo($userValue); }

#   if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyTermInfo($userValue); }
#   elsif ($ontology_type eq 'Concurhst') {       ($matches) = &getAnyConcurhstTermInfo($userValue); }
#   elsif ($ontology_type eq 'Discurhst') {       ($matches) = &getAnyDiscurhstTermInfo($userValue); }
#   elsif ($ontology_type eq 'Ditcurhst') {       ($matches) = &getAnyDitcurhstTermInfo($userValue); }
#   elsif ($ontology_type eq 'Expr') {            ($matches) = &getAnyExprTermInfo($userValue); }
#   elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBConstruct') {     ($matches) = &getAnyWBConstructTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBProcess') {       ($matches) = &getAnyWBProcessTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBRnai') {          ($matches) = &getAnyWBRnaiTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBSeqFeat') {       ($matches) = &getAnyWBSeqFeatTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBSequence') {      ($matches) = &getAnyWBSequenceTermInfo($userValue); }
  return $matches;
} # sub getAnySpecificTermInfo

sub getAnyWBPersonTermInfo {
  my ($userValue) = @_;
  my $person_id = $userValue; my $standard_name; my $to_print;
#   my $standard_name = $userValue; my $person_id; my $to_print;
#   if ($userValue =~ m/(.*?) \( (.*?) \)/) { $standard_name = $1; $person_id = $2; } else { $person_id = $userValue; }
  my $joinkey = $person_id; $joinkey =~ s/WBPerson/two/g;
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$joinkey' ORDER BY two_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  my %emails; if ($row[2]) { $standard_name = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[2]) { $emails{$row[2]}++; } }
  ($joinkey) = $joinkey =~ m/(\d+)/;
  my $id = 'WBPerson' . $joinkey;
  if ($id) { $to_print .= qq(id: <a href="http://www.wormbase.org/resources/person/${person_id}#03--10" target="new">$id</a><br />\n); }
  if ($standard_name) { $to_print .= "name: $standard_name<br />\n"; }
  my $first_email = '';
  foreach my $email (sort keys %emails ) {
    unless ($first_email) { $first_email = $email; }
    $to_print .= "email: <a href=\"javascript:void(0)\" onClick=\"window.open('mailto:$email')\">$email</a><br />\n"; }
  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = '$id' ;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) {  # all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  $to_print = qq(Click <a href="phenotype.cgi?action=personPublication&personId=${person_id}&personName=${standard_name}&personEmail=${first_email}" target="new" style="font-weight: bold; text-decoration: underline;">here</a> to review your publications and see which are in need of phenotype curation<br/>\n) . $to_print;

#   ($var, $personId)      = &getHtmlVar($query, 'personId');		# WBPerson ID
#   ($var, $personName)    = &getHtmlVar($query, 'personName');		# WBPerson Name
#   ($var, $personEmail)   = &getHtmlVar($query, 'personEmail');		# email address
  return $to_print;
} # sub getAnyWBPersonTermInfo

sub getAnyWBTransgeneTermInfo {
  my ($userValue) = @_; my %joinkeys;
  $result = $dbh->prepare( "SELECT * FROM trp_name WHERE trp_name = '$userValue' ORDER BY trp_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( trp_publicname trp_synonym trp_summary );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $userValue<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) {
    my $label = $table; $label =~ s/^trp_//; ($label) = ucfirst($label);
    $to_print .= "${label}: $entry<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { 
    if ($data_line =~ /name: WBTransgene\d+/) {          $data_line =~ s/(WBTransgene\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/all\/transgene\/${1}#0314--10\" target=\"new\">$1<\/a>/; }
    $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBTransgeneTermInfo

sub getPmidTermInfo {               # given user pmids + previously retrieved pmidTitles, get titles for new pmids not already in pmidTitles list, return new pmidTitles list. also remove from pmidTitles pmids that are not in the pmids list (from a user deletion)  This form only uses one pmid so the extra pmids part is not needed, but kept just in case it changes later
  my ($userInput) = @_;
#   my ($var, $userInput)      = &getHtmlVar($query, 'pmids');                # what user enter as pmids
  if ($userInput =~ m/^\s+/) { $userInput =~ s/^\s+//; }
  if ($userInput =~ m/\s+$/) { $userInput =~ s/\s+$//; }
  my $pap_link = $userInput;
  my $pmid     = $userInput;
  my $toPrint  = qq(PubMed ID '$userInput' not recognized.);
  if ($userInput =~ m/^pmid:?(\d+)/i) { $pmid = $1; }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier = 'pmid$pmid';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { 
    my $wbpaper = 'WBPaper' . $row[0];
    $pap_link = qq(<a href="http://www.wormbase.org/resources/paper/${wbpaper}#03--10" target="new">$pmid</a>); }
  my $ebiData = get "http://www.ebi.ac.uk/europepmc/webservices/rest/search/format=xml&query=ext_id:" . $pmid . "%20src:med";         # get the ebi url
  my $title   = ''; my $journal = ''; my $year    = ''; my $authors = '';		# default to having no title
  if ( $ebiData =~ m/<title>(.*?)<\/title>/sm) {               $title   = $1; }       # get the title from the xml
  if ( $ebiData =~ m/<journalTitle>(.*?)<\/journalTitle>/sm) { $journal = $1; }       # get the journal from the xml
  if ( $ebiData =~ m/<pubYear>(.*?)<\/pubYear>/sm) {           $year    = $1; }       # get the year from the xml
  if ( $ebiData =~ m/<authorString>(.*?)<\/authorString>/sm) { $authors = $1; }       # get the authors from the xml
  if ($title || $journal || $year || $authors) {
    $toPrint   = qq(PubMed ID: $pap_link\nTitle: $title\n);
    if ($journal) { $toPrint .= qq(Journal: $journal\n); }
    if ($year) {    $toPrint .= qq(Year: $year\n);       }
    if ($authors) { $toPrint .= qq(Authors: $authors\n); } }
  my (@data) = split/\n/, $toPrint;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  my $toPrint = join"<br />\n", @data;
  return $toPrint;
#   print $toPrint;
} # sub getPmidTermInfo


sub autocompleteXHR {                                           # when typing in an autocomplete field xhr call to this CGI for values
  print "Content-type: text/plain\n\n";
  ($var, my $words) = &getHtmlVar($query, 'query');
  ($var, my $field) = &getHtmlVar($query, 'field');
  my $matches;
  if ( $fields{$field}{type} eq 'ontology' ) {
    if ($fields{$field}{ontology_type} eq 'obo') { ($matches) = &getGenericOboAutocomplete($field, $words); }
      else {
        my $ontology_type = $fields{$field}{ontology_type};
        ($matches) = &getAnySpecificAutocomplete($ontology_type, $words); } }
  print $matches;
} # sub autocompleteXHR

sub getGenericOboAutocomplete {
  my ($field, $words) = @_;
  my $ontology_table  = $fields{$field}{ontology_table};
  my $max_results     = 20;
  # if ($words =~ m/^.{5,}/) { $max_results = 500; }		# Chris doesn't find this useful
  my $limit           = $max_results + 1;
  my $oboname_table   =  'obo_name_' . $ontology_table;
  my $obodata_table   =  'obo_data_' . $ontology_table;
  my $query_modifier  = qq(AND joinkey NOT IN (SELECT joinkey FROM $obodata_table WHERE $obodata_table ~ 'is_obsolete') ); 
  if ($field eq 'goidcc') { $query_modifier .= qq(AND joinkey IN (SELECT joinkey FROM obo_data_goid WHERE obo_data_goid ~ 'cellular_component') ); }
  if ($words =~ m/\'/) { $words =~ s/\'/''/g; }
  if ($words =~ m/\(/) { $words =~ s/\(/\\\(/g; }
  if ($words =~ m/\)/) { $words =~ s/\)/\\\)/g; }
  my $lcwords = lc($words);
  my @tabletypes = qw( name syn data );
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  foreach my $tabletype (@tabletypes) {			# first match all types as exact match (case insensitive)
    my $obotable = 'obo_' . $tabletype . '_' . $ontology_table;
    my $column   = $obotable; if ($tabletype eq 'data') { $column = 'joinkey'; }          # use joinkey for ID instead of data
    $result = $dbh->prepare( "SELECT * FROM $obotable WHERE LOWER($column) = '$lcwords' $query_modifier ORDER BY $column LIMIT $limit;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" });
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM $oboname_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); 
        $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row2 = $result2->fetchrow(); my $name = $row2[1];
        if ($tabletype eq 'syn') { 
          $elementText = qq($row[1] <span style='font-size:.75em'>( $name )</span>);
          $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$row[0]" }); }
        elsif ($tabletype eq 'data') { 
          $elementText = qq($name <span style='font-size:.75em'>( $row[0] )</span>);
          $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$row[0]" }); } }
      $matches{$matchData}++; }
  } # foreach my $tabletype (@tabletypes)
  foreach my $tabletype (@tabletypes) {			# first match all types at the beginning
    my $obotable = 'obo_' . $tabletype . '_' . $ontology_table;
    my $column   = $obotable; if ($tabletype eq 'data') { $column = 'joinkey'; }          # use joinkey for ID instead of data
    $result = $dbh->prepare( "SELECT * FROM $obotable WHERE LOWER($column) ~ '^$lcwords' $query_modifier ORDER BY $column LIMIT $limit;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" });
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM $oboname_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); 
        $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row2 = $result2->fetchrow(); my $name = $row2[1];
        if ($tabletype eq 'syn') { 
          $elementText = qq($row[1] <span style='font-size:.75em'>( $name )</span>);
          $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$row[0]" }); }
        elsif ($tabletype eq 'data') { 
          $elementText = qq($name <span style='font-size:.75em'>( $row[0] )</span>);
          $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$row[0]" }); } }
      $matches{$matchData}++; }
  } # foreach my $tabletype (@tabletypes)
  foreach my $tabletype (@tabletypes) {			# then match all types at the middle
    next if ( $fields{$field}{matchstartonly} eq 'matchstartonly' );	# some fields should only match at the beginning
    my $obotable = 'obo_' . $tabletype . '_' . $ontology_table;
    my $column   = $obotable; if ($tabletype eq 'data') { $column = 'joinkey'; }          # use joinkey for ID instead of data
    $result = $dbh->prepare( "SELECT * FROM $obotable WHERE LOWER($column) ~ '$lcwords' AND LOWER($column) !~ '^$lcwords' $query_modifier ORDER BY $column LIMIT $limit;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" });
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM $oboname_table WHERE joinkey = '$row[0]' LIMIT $max_results;" );
        $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row2 = $result2->fetchrow(); my $name = $row2[1];
        if ($tabletype eq 'syn') { 
          $elementText = qq($row[1] <span style='font-size:.75em'>( $name )</span>);
          $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$row[0]" }); }
        elsif ($tabletype eq 'data') { 
          $elementText = qq($name <span style='font-size:.75em'>( $row[0] )</span>);
          $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$row[0]" }); } }
      $matches{$matchData}++; }
    last if (scalar(keys %matches) >= $max_results);
  } # foreach my $tabletype (@tabletypes)
  if (scalar keys %matches >= $max_results) { 
    my $matchData = qq({ "eltext": "<span style='font-style: italic; background-color: yellow;'>More matches exist; please be more specific</span>", "name": "", "id": "invalid value" }); 
    $t->Replace($max_results - 1, 'no value', $matchData); }
  my $matches = join", ", keys %matches;
  $matches = qq({ "results": [ $matches ] });
  return $matches;
} # sub getGenericOboAutocomplete

sub getAnySpecificAutocomplete {
  my ($ontology_type, $words) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {             ($matches) = &getAnyWBPersonAutocomplete($words);    }
    elsif ($ontology_type eq 'WBTransgene') {     ($matches) = &getAnyWBTransgeneAutocomplete($words); }
#   elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneAutocomplete($words);      }

#   if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyAutocomplete($words); }
#   elsif ($ontology_type eq 'Concurhst') {       ($matches) = &getAnyConcurhstAutocomplete($words); }
#   elsif ($ontology_type eq 'Discurhst') {       ($matches) = &getAnyDiscurhstAutocomplete($words); }
#   elsif ($ontology_type eq 'Ditcurhst') {       ($matches) = &getAnyDitcurhstAutocomplete($words); }
#   elsif ($ontology_type eq 'Expr') {            ($matches) = &getAnyExprAutocomplete($words); }
#   elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeAutocomplete($words); }
#   elsif ($ontology_type eq 'WBConstruct') {     ($matches) = &getAnyWBConstructAutocomplete($words); }
#   elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneAutocomplete($words); }
#   elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionAutocomplete($words); }
#   elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperAutocomplete($words); }
#   elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonAutocomplete($words); }
#   elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureAutocomplete($words); }
#   elsif ($ontology_type eq 'WBProcess') {       ($matches) = &getAnyWBProcessAutocomplete($words); }
#   elsif ($ontology_type eq 'WBRnai') {          ($matches) = &getAnyWBRnaiAutocomplete($words); }
#   elsif ($ontology_type eq 'WBSeqFeat') {       ($matches) = &getAnyWBSeqFeatAutocomplete($words); }
#   elsif ($ontology_type eq 'WBSequence') {      ($matches) = &getAnyWBSequenceAutocomplete($words); }
  return $matches;
} # sub getAnySpecificAutocomplete

sub getAnyWBPersonAutocomplete {
  my ($words) = @_;
  my $max_results     = 20;
  # if ($words =~ m/^.{5,}/) { $max_results = 500; }		# Chris doesn't find this useful
  my $lcwords = lc($words);
  my $limit       = $max_results + 1;
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my @tables = qw( two_standardname );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );      # match by start of name
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );          # then match anywhere in the name
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY joinkey LIMIT $limit;" );               # then match by WBPerson number
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { 
    my $matchData = qq({ "eltext": "<span style='font-style: italic; background-color: yellow;'>More matches exist; please be more specific</span>", "name": "", "id": "invalid value" }); 
    $t->Replace($max_results - 1, 'no value', $matchData); }
  my $matches = join", ", keys %matches;
  $matches = qq({ "results": [ $matches ] });
  return $matches;
} # sub getAnyWBPersonAutocomplete

sub getAnyWBTransgeneAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $lcwords = lc($words);
  my $limit       = $max_results + 1;
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my $table = 'trp_name';                               # can't name trp_name twice, so can't add that to generic @tables below
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' ORDER BY $table LIMIT $limit;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { 
    my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[1] )</span>);
    my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[1]" }); $matches{$matchData}++; 
  }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND LOWER($table) !~ '^$lcwords' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
    my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[1] )</span>);
    my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[1]" }); $matches{$matchData}++; 
  }
  my @tables = qw( trp_publicname trp_synonym );                        # used to have trp_paper, but would get lots of "WBPaperNNN","WBPaperNNN" in the dataTable, which looked misleading.  2010 09 28
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT trp_name.trp_name, ${table}.$table FROM trp_name, $table WHERE trp_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$lcwords' ORDER BY ${table}.$table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT trp_name.trp_name, ${table}.$table FROM trp_name, $table WHERE trp_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$lcwords' AND LOWER(${table}.$table) !~ '^$lcwords' ORDER BY ${table}.$table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" }); $matches{$matchData}++; 
    }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { 
    my $matchData = qq({ "eltext": "more ...", "name": "", "id": "invalid value" }); 
    $t->Replace($max_results - 1, 'no value', $matchData); }
  my $matches = join", ", keys %matches;
  $matches = qq({ "results": [ $matches ] });
  return $matches;
} # sub getAnyWBTransgeneAutocomplete



sub showStart {
  print "Content-type: text/html\n\n";
  print $header;
  print qq(<span style="font-size: 24pt;">Contribute phenotype connections to WormBase</span><br/><br/>\n);
  print qq(<span>We would appreciate your help in adding phenotype data from published papers to WormBase.<br/>Please fill out the form below. <b>Watch a short video tutorial <a style='font-weight: bold; text-decoration: underline;' href="https://www.youtube.com/watch?v=_gd87S1h3zg&feature=youtu.be" target="_blank">here</a> or read the user guide <a style='font-weight: bold; text-decoration: underline;' href="http://wiki.wormbase.org/index.php/Contributing_Phenotype_Connections" target="_blank">here</a></b>.<br/>If you would prefer to fill out a spreadsheet with this information, please download and fill out our<br/><a href="https://dl.dropboxusercontent.com/u/4290782/WormBase_Phenotype_Worksheet.xlsx" target="_blank">WormBase Phenotype Worksheet</a> and e-mail as an attachment to <a href="mailto:curation\@wormbase.org">curation\@wormbase.org</a><br/>If you have any questions, please do not hesitate to contact WormBase at <a href="mailto:help\@wormbase.org">help\@wormbase.org</a></span><br/><br/>\n);
  my $browser = $ENV{HTTP_USER_AGENT};
  if ($browser =~ m/safari/i) { 
    unless ( ($browser =~ m/chrome/i) || ($browser =~ m/firefox/i) ) {
      print qq(Safari users please note: Safari's 'Autofill' feature may not properly populate the name field in this form.<br/><br/>\n); } }
    # initialize originalIP + originalTime, processing uploads requires them. %fields processing will replace with form values from 'hidden' group before upload field(s).
  unless ($fields{hidden}{field}{origip}{inputvalue}{1}) {     $fields{hidden}{field}{origip}{inputvalue}{1}   = $query->remote_host(); }
  unless ($fields{hidden}{field}{origtime}{inputvalue}{1}) {   $fields{hidden}{field}{origtime}{inputvalue}{1} = time;                  }
    # if IP corresponds to an existing user, get person and email data
  unless ($fields{person}{termidvalue}{1}) {
    ( $fields{person}{termidvalue}{1}, $fields{person}{inputvalue}{1}, $fields{email}{inputvalue}{1} ) = &getUserByIp(); }
  ($var, my $pmid)        = &getHtmlVar($query, "input_1_pmid");	# if linking here from personPublication table
  ($var, my $personName)  = &getHtmlVar($query, "input_1_person");	# if linking here from personPublication table
  ($var, my $personId)    = &getHtmlVar($query, "termid_1_person");	# if linking here from personPublication table
  ($var, my $personEmail) = &getHtmlVar($query, "input_1_email");	# if linking here from personPublication table
  if ($pmid) {        $fields{pmid}{inputvalue}{1}    = $pmid;        }
  if ($personName) {  $fields{person}{inputvalue}{1}  = $personName;  }
  if ($personId) {    $fields{person}{termidvalue}{1} = $personId;    }
  if ($personEmail) { $fields{email}{inputvalue}{1}   = $personEmail; }
  &showForm();
  print $footer;
} # sub showStart

sub printEditorDropdown {
#   my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced) = @_;
  my ($i, $field, $colspan) = @_;
  my $inputvalue  = ''; my $termidvalue = ''; my @options = ();
  if ($fields{$field}{inputvalue}{$i})     { $inputvalue  = $fields{$field}{inputvalue}{$i}; }	# previous form value
  if ($fields{$field}{termidvalue}{$i})    { $termidvalue = $fields{$field}{termidvalue}{$i}; }
#   my $td = qq(<td style="min-width: 300px; border-style: solid; border-color: #000000;"><select name="input_${i}_$field" id="input_${i}_$field" style="width: 100%;" >);
#   my $td = qq(<td style="min-width: 300px;"><select name="input_${i}_$field" id="input_${i}_$field" style="width: 100%; background-color: #DDF3F3;" >);
  my $td = qq(<td style="min-width: 300px; max-width: 300px;" colspan="$colspan"><select name="input_${i}_$field" id="input_${i}_$field" style="max-width: 300px; width: 100%; background-color: #E1F1FF;" >);
#   $td .= qq(<option value=""></option>);				# have to specify blank option with terms, since species cannot have blank
  foreach my $value (keys %{ $dropdown{$field} }) {
    my $selected = '';
    if ($fields{$field}{inputvalue}{$i} eq $value) { $selected = qq(selected="selected"); }
    $td .= qq(<option $selected value="$value">$dropdown{$field}{$value}</option>); }
  $td .= qq(</td>\n);
  return $td;
} # printEditorDropdown


sub printEditorText {
#   my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced) = @_;
  my ($i, $field, $colspan) = @_;
  my $inputvalue  = ''; my $termidvalue = ''; my $placeholder = ''; my $readonly = ''; 
  if ($fields{$field}{inputvalue}{$i})     { $inputvalue  = $fields{$field}{inputvalue}{$i}; }	# previous form value
  if ($fields{$field}{termidvalue}{$i})    { $termidvalue = $fields{$field}{termidvalue}{$i}; }
  if ($fields{$field}{example})            { $placeholder = qq(placeholder="$fields{$field}{example}"); }
  if ($fields{$field}{type} eq 'readonly') { $readonly    = qq(readonly="readonly"); }
#   return qq(<td style="min-width: 300px; border-style: solid; border-color: #000000;"><input name="input_${i}_$field" id="input_${i}_$field" style="width: 97%;" $readonly $placeholder value="$inputvalue"></td>\n);
  return qq(<td style="min-width: 300px; max-width: 300px;" colspan="$colspan"><input name="input_${i}_$field" id="input_${i}_$field" style="max-width: 300px; width: 97%; background-color: #E1F1FF;" $readonly $placeholder value="$inputvalue"></td>\n);
} # printEditorText

sub printEditorBigtext {
#   my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $cols_size, $rows_size) = @_;
  my ($i, $field, $colspan) = @_;
  my $inputvalue  = ''; my $termidvalue = ''; my $placeholder = ''; my $readonly = ''; 
  my $cols_size  = '40';
  my $rows_size  = '5';
  if ($fields{$field}{inputvalue}{$i})     { $inputvalue  = $fields{$field}{inputvalue}{$i}; }	# previous form value
  if ($fields{$field}{termidvalue}{$i})    { $termidvalue = $fields{$field}{termidvalue}{$i}; }
  if ($fields{$field}{example})            { $placeholder = qq(placeholder="$fields{$field}{example}"); }
  if ($fields{$field}{type} eq 'readonly') { $readonly    = qq(readonly="readonly"); }
#   my $table_to_print = qq(<td style="min-width: 300px; border-style: solid; border-color: #000000;">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  my $table_to_print = qq(<td style="min-width: 300px; max-width: 300px;" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  $table_to_print .= qq(<input id="input_${i}_$field" name="input_${i}_$field" style="max-width: 300px; width: 97%; background-color: #E1F1FF;" $placeholder value="$inputvalue">\n);
  $table_to_print .= qq(<div id="container_bigtext_${i}_$field"><textarea id="textarea_bigtext_${i}_$field" rows="$rows_size" cols="$cols_size" $placeholder style="display:none">$inputvalue</textarea></div>\n);
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub printEditorBigtext

sub printEditorTextarea {
  my ($i, $field, $colspan) = @_;
  my $inputvalue  = ''; my $termidvalue = ''; my $placeholder = ''; my $readonly = ''; 
  my $cols_size  = '40';
  my $rows_size  = '5';
  if ($fields{$field}{inputvalue}{$i})     { $inputvalue  = $fields{$field}{inputvalue}{$i}; }	# previous form value
  if ($fields{$field}{termidvalue}{$i})    { $termidvalue = $fields{$field}{termidvalue}{$i}; }
  if ($fields{$field}{example})            { $placeholder = qq(placeholder="$fields{$field}{example}"); }
  if ($fields{$field}{type} eq 'readonly') { $readonly    = qq(readonly="readonly"); }
  my $table_to_print = qq(<td style="min-width: 300px; max-width: 300px;" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
#   $table_to_print .= qq(<input id="input_${i}_$field" name="input_${i}_$field" style="width: 97%; background-color: #E1F1FF;" $placeholder value="$inputvalue">\n);
  $table_to_print .= qq(<div id="container_bigtext_${i}_$field"><textarea id="input_${i}_$field" name="input_${i}_$field" rows="$rows_size" cols="$cols_size">$inputvalue</textarea></div>\n);
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub printEditorTextarea


sub printEditorOntology {
  my ($i, $field, $colspan) = @_;
  my $inputvalue  = ''; my $termidvalue = ''; my $placeholder = ''; my $readonly = ''; my $freeForced = 'forced';
  if ($fields{$field}{inputvalue}{$i})     { $inputvalue  = $fields{$field}{inputvalue}{$i}; }	# previous form value
  if ($fields{$field}{termidvalue}{$i})    { $termidvalue = $fields{$field}{termidvalue}{$i}; }
  if ($fields{$field}{example})            { $placeholder = qq(placeholder="$fields{$field}{example}"); }
  if ($fields{$field}{type} eq 'readonly') { $readonly    = qq(readonly="readonly"); }
  if ($fields{$field}{freeForced})         { $freeForced  = $fields{$field}{freeForced}; }

  my $table_to_print = qq(<td style="min-width: 300px; max-width: 300px;" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  $table_to_print .= qq(<span id="container${freeForced}${i}${field}AutoComplete">\n);
  $table_to_print .= qq(<div id="${freeForced}${i}${field}AutoComplete" class="div-autocomplete">\n);
    # when blurring ontology fields, if it's been deleted by user, make the corresponding termid field also blank.
  my $onBlur = qq(if (document.getElementById('input_${i}_$field').value === '') { document.getElementById('termid_${i}_$field').value = ''; });
  $table_to_print .= qq(<input id="input_${i}_$field"  name="input_${i}_$field" value="$inputvalue"  style="max-width: 300px; width: 97%; background-color: #E1F1FF;" $placeholder onBlur="$onBlur">\n);
# HIDE
#   $table_to_print .= qq(<input id="termid_${i}_$field" name="termid_${i}_$field" value="$termidvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<input type="hidden" id="termid_${i}_$field" name="termid_${i}_$field" value="$termidvalue" size="40"          readonly="readonly">\n);
    # ontology fields have html values in input_i_field but are not from autocomplete object, so selectionenforce clears them.  store this parallel value, so if it gets cleared, it gets reloaded
#   $table_to_print .= qq(<input id="loaded_${i}_$field" name="loaded_${i}_$field" value="$inputvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<input type="hidden" id="loaded_${i}_$field" name="loaded_${i}_$field" value="$inputvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<div id="${freeForced}${i}${field}Container"></div></div></span>\n);
  $table_to_print .= qq(</td>\n);
  return $table_to_print;
} # sub printEditorOntology

sub printEditorCheckbox {
  my ($i, $field, $colspan) = @_; my $toReturn = '';
  if ($fields{$field}{type} eq 'checkbox') {
    my $tdColspan = qq(colspan="$colspan"); 
    $toReturn .= qq(<td $tdColspan>);
    $toReturn .= &printEditorJustCheckbox($i, $field);
    $toReturn .= qq(</td>); }
  return $toReturn;
}

sub printEditorJustCheckbox {
  my ($i, $field) = @_; my $toReturn = '';
  if ($fields{$field}{type} eq 'checkbox') {
    my $checked = '';
    if ($fields{$field}{inputvalue}{$i} eq $fields{$field}{label}) { $checked = qq(checked="checked"); }
#     $toReturn = qq(&nbsp;&nbsp;<input type="checkbox" id="input_${i}_$field" name="input_${i}_$field" value="$fields{$field}{label}" $checked>&nbsp; $fields{$field}{label}<br/>\n);
    $toReturn = qq(&nbsp;<input type="checkbox" id="input_${i}_$field" name="input_${i}_$field" value="$fields{$field}{label}" $checked>&nbsp; \n); }
  return $toReturn;
} # sub printEditorJustCheckbox

sub printEditorLabel {
  my ($i, $field) = @_;
  my $label          = $fields{$field}{label};
  my $labelTdColspan = qq(colspan="1"); 
  my $minwidth       = '176px'; if ($fields{$field}{minwidth}) { $minwidth = $fields{$field}{minwidth}; }
  my $fontsize       = ''; if ($fields{$field}{fontsize}) { $fontsize = qq(font-size: $fields{$field}{fontsize};); }
#   my $labelTdStyle   = qq(style="min-width: $minwidth; border-style: solid; border-color: #000000; $fontsize");
  my $labelTdStyle   = qq(style="min-width: $minwidth; $fontsize padding: 0 5px 0 0;");
  my $terminfo       = '';
  if ($fields{$field}{terminfo}) {    
    my $terminfo_text = $fields{$field}{terminfo}; my $terminfo_title = $fields{$field}{terminfo};
    $terminfo_text  =~ s/'/&#8217;/g; $terminfo_text  =~ s/"/&quot;/g; 
    $terminfo_title =~ s/'/&#8217;/g; $terminfo_title =~ s/"/&quot;/g; $terminfo_title =~ s/<.*?>//g;
    $terminfo = qq(<span style="color: #06C729; font-weight: bold;" title="$terminfo_title" onclick="document.getElementById('term_info_box').style.display = ''; document.getElementById('term_info').innerHTML = '$terminfo_text';">?</span>); }
  return qq(<td align="right" $labelTdColspan $labelTdStyle>&nbsp;&nbsp;$label $terminfo</td>);
} # sub printEditorLabel

sub printEditorWarnings {
  my ($i, $field) = @_;
  ($var, my $warningvalue)  = &getHtmlVar($query, "input_warnings_${i}_$field");
  if ($field eq 'person') {				# person field has a notice linking to their publications
    if ($fields{person}{termidvalue}{1}) { 
      my $person_id = $fields{person}{termidvalue}{1}; my $person_name = ''; my $person_email = '';
      if ($fields{person}{inputvalue}{1}) { $person_name  = $fields{person}{inputvalue}{1}; }
      if ($fields{email}{inputvalue}{1})  { $person_email = $fields{email}{inputvalue}{1};  }
      $warningvalue = qq(Click <a href='phenotype.cgi?action=personPublication&personId=${person_id}&personName=${person_name}&personEmail=${person_email}' target='new' style='font-weight: bold; text-decoration: underline;'>here</a> to review your publications and see which are in need of phenotype curation<br/>\n); } }
  my $labelTdColspan = qq(colspan="4"); 
  my $minwidth       = '200px'; if ($fields{$field}{minwidth}) { $minwidth = $fields{$field}{minwidth}; }
#   my $labelTdStyle   = qq(style="display: none; min-width: $minwidth; border-style: solid; border-color: #000000;");
  my $labelTdStyle   = qq(style="display: none; min-width: $minwidth;");
  if ($warningvalue) { $labelTdStyle   = qq(style="min-width: $minwidth;"); }
#   return qq(<td id="tdwarnings_${i}_$field" $labelTdColspan $labelTdStyle>warninggoeshere</td>);
#   return qq(<td id="tdwarnings_${i}_$field" $labelTdColspan $labelTdStyle>$warningvalue</td><input type="hidden" id="input_warnings_${i}_$field" name="input_warnings_${i}_$field" value="$warningvalue">);
  my $toReturn = '';
  $toReturn .= qq(<td id="tdwarnings_${i}_$field" $labelTdColspan $labelTdStyle>$warningvalue</td>);
  $toReturn .= qq(<input type="hidden" id="input_warnings_${i}_$field" size=200 name="input_warnings_${i}_$field" value="$warningvalue">);
#   if ( ($field eq 'pmid') || ($field eq 'allele') ) {
#       $toReturn .= qq(FIELD $field $i<input id="input_warnings_${i}_$field" size=200 name="input_warnings_${i}_$field" value="$warningvalue">); }
#     else {
#       $toReturn .= qq(<input type="hidden" id="input_warnings_${i}_$field" size=200 name="input_warnings_${i}_$field" value="$warningvalue">); }
  return $toReturn;
} # sub printEditorWarnings

sub printArrayEditorHorizontal {
  my (@fields) = @_;
  my $amount      = $fields{$fields[0]}{multi};
  my $showAmount  = 1;
  if ($fields{$fields[0]}{startHidden} eq 'startHidden') { $showAmount = 0; }
  for my $i (1 .. $amount) {
    my $group_style = ''; if ($i > $showAmount) { $group_style = 'display: none'; }
    if ($i < $fields{$fields[0]}{hasdata} + 1 + $showAmount) { $group_style = ''; }
    my $trToPrint = qq(<tr id="group_${i}_${fields[0]}" style="$group_style">\n);
    if ($i == 1) {						# on the first row, show the field information for javascript
      foreach my $field (@fields) {
        $trToPrint .= qq(<input type="hidden" class="fields" value="$field" />\n);
        my $data = '{ ';                                                    # data is { 'tag' : 'value', 'tag2' : 'value2' } format javascript stuff
        foreach my $tag (sort keys %{ $fields{$field} }) {
          my $tag_value = $fields{$field}{$tag};
          next if ($tag eq 'pg');				# hash 
          next if ($tag eq 'terminfo');			# has commas and other bad characters
          if ($tag eq 'radio') { $tag_value = join" ", sort keys %{ $fields{$field}{$tag} }; }
          $data .= "'$tag' : '$tag_value', "; }
        $data .= "'multi' : '$amount', ";
        $data =~ s/, $/ }/;
        $trToPrint .= qq(<input type="hidden" id="data_$field" value="$data" />\n); }
    } # if ($i == 1)
    foreach my $field (@fields) {
       my $td_label .= &printEditorLabel($i, $field);
       my $td_text = '';
       if ($fields{$field}{type} eq 'text') {          $td_text .= &printEditorText($i, $field);     }
         elsif ($fields{$field}{type} eq 'bigtext') {  $td_text .= &printEditorBigtext($i, $field);  }
         elsif ($fields{$field}{type} eq 'textarea') { $td_text .= &printEditorTextarea($i, $field); }
         elsif ($fields{$field}{type} eq 'ontology') { $td_text .= &printEditorOntology($i, $field, 2); }
         elsif ($fields{$field}{type} eq 'dropdown') { $td_text .= &printEditorDropdown($i, $field); }
         elsif ($fields{$field}{type} eq 'checkbox') { $td_text .= &printEditorCheckbox($i, $field); }
       my $td_warnings .= &printEditorWarnings($i, $field);
       $trToPrint .= $td_label; 
       $trToPrint .= $td_text; 
       $trToPrint .= $td_warnings; 
    } # foreach my $field (@fields)
    $trToPrint    .= qq(</tr>\n);
    print $trToPrint;
  } # for my $i (1 .. $amount)
} # sub printArrayEditorHorizontal

sub printArrayEditorNested {
  my (@fields) = @_;
  my $amount      = $fields{$fields[0]}{multi};
  my $showAmount  = 1;
  if ($fields{$fields[0]}{startHidden} eq 'startHidden') { $showAmount = 0; }	# if main field in group starts hidden, whole group starts hidden
  for my $i (1 .. $amount) {
#     foreach my $field (@fields)
    foreach my $j (0 .. $#fields) {
      my $fieldLeader = $fields[0];				# the first field determines whether to show indented fields
      my $field       = $fields[$j];
      if ($fields{$field}{startHidden} eq 'startHidden') { $showAmount = 0; }	# if sub field in group starts hidden, only sub field starts hidden
      my $group_style = ''; if ($i > $showAmount) { $group_style = 'display: none'; }
      my $showThreshold = $fields{$fieldLeader}{hasdata} + 1 + $showAmount; 	# threshold is amount that have data + 1 + amount to show
      if ($fields{$fieldLeader}{hasdata}) { $showThreshold += 1; }		# if field has data, show one more blank one
      if ($i < $showThreshold) { $group_style = ''; }
      my $trToPrint = qq(<tr id="group_${i}_${field}" style="$group_style">\n);
      if ($i == 1) {						# on the first row, show the field information for javascript
          $trToPrint .= qq(<input type="hidden" class="fields" value="$field" />\n);
          my $data = '{ ';                                                    # data is { 'tag' : 'value', 'tag2' : 'value2' } format javascript stuff
          foreach my $tag (sort keys %{ $fields{$field} }) {
            my $tag_value = $fields{$field}{$tag};
# print qq(J $j I $i FIELD $field TAG $tag TV $tag_value E<br>);
            next if ($tag eq 'pg');				# hash 
            next if ($tag eq 'terminfo');			# has commas and other bad characters
            if ($tag eq 'radio') { $tag_value = join" ", sort keys %{ $fields{$field}{$tag} }; }
            $data .= "'$tag' : '$tag_value' -DIVIDER- "; }
          $data .= "'multi' : '$amount', ";
          $data =~ s/ -DIVIDER- $/ }/;
          $trToPrint .= qq(<input type="hidden" id="data_$field" value="$data" />\n); 
      } # if ($i == 1)
      my $td_label .= &printEditorLabel($i, $field);
      my $colspan = 2; my $td_indent = ''; if ($j > 0) { $td_indent .= qq(<td></td>); $colspan = 2; }
      my $td_text = '';
      if ($fields{$field}{type} eq 'text') {          $td_text .= &printEditorText($i, $field, $colspan);     }
        elsif ($fields{$field}{type} eq 'bigtext') {  $td_text .= &printEditorBigtext($i, $field, $colspan);  }
        elsif ($fields{$field}{type} eq 'textarea') { $td_text .= &printEditorTextarea($i, $field, $colspan); }
        elsif ($fields{$field}{type} eq 'ontology') { $td_text .= &printEditorOntology($i, $field, $colspan); }
        elsif ($fields{$field}{type} eq 'dropdown') { $td_text .= &printEditorDropdown($i, $field, $colspan); }
        elsif ($fields{$field}{type} eq 'checkbox') { $td_text .= &printEditorCheckbox($i, $field, $colspan); }
      my $td_warnings .= &printEditorWarnings($i, $field);
      $trToPrint .= $td_indent; 
      $trToPrint .= $td_label; 
      $trToPrint .= $td_text; 
      $trToPrint .= $td_warnings; 
      $trToPrint    .= qq(</tr>\n);
    print $trToPrint;
    } # foreach my $field (@fields)
  } # for my $i (1 .. $amount)
} # sub printArrayEditorNested

# sub printOffset {
#   my $i = 1;
#   my $field = 'allele';
#   print qq(<tr id="group_${i}_${field}">\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(</tr>\n);
#   $field = 'obsphenotype';
#   $field = 'obsphenremark';
#   print qq(<tr id="group_${i}_${field}">\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=2>COL2</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(</tr>\n);
#   print qq(<tr id="group_${i}_${field}">\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=1>COL1</td>\n);
#   print qq(<td colspan=2>COL2</td>\n);
#   print qq(<td colspan=2>COL2</td>\n);
#   print qq(</tr>\n);
# #   my @fields = qw( obsphenotype obsphenremark ); 
# #   my $field = shift @fields;
# #   my $i = 1;
# #   my $showAmount  = 1;
# #   if ($fields{$fields[0]}{startHidden} eq 'startHidden') { $showAmount = 0; }
# #     my $group_style = ''; if ($i > $showAmount) { $group_style = 'display: none'; }
# #     if ($i < $fields{$fields[0]}{hasdata} + 1 + $showAmount) { $group_style = ''; }
# #     my $trToPrint = qq(<tr id="group_${i}_${fields[0]}" style="$group_style">\n);
# #        my $td_label = &printEditorLabel($i, $field);
# #        my $td_text  = &printEditorOntology($i, $field, 2);
# #        $trToPrint .= $td_label; 
# #        $trToPrint .= $td_text; 
# #     $trToPrint    .= qq(</tr>\n);
# #     print $trToPrint;
# #   $field = shift @fields;
# #     my $trToPrint = qq(<tr id="group_${i}_${fields[0]}" style="$group_style">\n);
# #        $trToPrint .= qq(<td></td>);
# #        my $td_label = &printEditorLabel($i, $field);
# #        my $td_text  = &printEditorBigtext($i, $field, 2); 
# #        $trToPrint .= $td_label; 
# #        $trToPrint .= $td_text; 
# #     $trToPrint    .= qq(</tr>\n);
# #     print $trToPrint;
# } # sub printOffset


sub printTrSpacer {          print qq(<tr><td style="border: none;">&nbsp;</td></tr>\n); }

sub printTrHeader {
  my ($header, $colspan, $fontsize, $message, $message_colour, $message_fontsize) = @_;
  print qq(<tr><td colspan="$colspan" style="font-size: $fontsize;">\n);
  my $header_with_javascript = $header;
  if ($header eq 'Optional') {
    $header_with_javascript = qq(<span id="optional_down_span" style="display: none;" onmouseover="this.style.cursor='pointer';" onclick="document.getElementById('optional_down_span').style.display='none'; document.getElementById('optional_right_span').style.display=''; document.getElementById('group_1_allelenature').style.display='none'; document.getElementById('group_1_allelefunction').style.display='none'; document.getElementById('group_1_penetrance').style.display='none'; document.getElementById('group_1_tempsens').style.display='none'; document.getElementById('group_1_genotype').style.display='none'; document.getElementById('group_1_strain').style.display='none'; document.getElementById('group_1_comment').style.display='none'; document.getElementById('group_1_linkotherform').style.display='none'; document.getElementById('group_1_optionalexplain').style.display='none';" ><div id="optional_down_image" style="background-position: -40px 0; background-image: url('http://${hostfqdn}/~azurebrd/images/triangle_down_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_down_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_down_reversed.png)';" onmouseout="document.getElementById('optional_down_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_down_plain.png)';"></div>$header</span>);
    $header_with_javascript .= qq(<span id="optional_right_span" onmouseover="this.style.cursor='pointer';" onclick="document.getElementById('optional_down_span').style.display=''; document.getElementById('optional_right_span').style.display='none'; document.getElementById('group_1_allelenature').style.display=''; document.getElementById('group_1_allelefunction').style.display=''; document.getElementById('group_1_penetrance').style.display=''; document.getElementById('group_1_tempsens').style.display=''; document.getElementById('group_1_genotype').style.display=''; document.getElementById('group_1_strain').style.display=''; document.getElementById('group_1_comment').style.display=''; document.getElementById('group_1_linkotherform').style.display=''; document.getElementById('group_1_optionalexplain').style.display='';" ><div id="optional_right_image" style="background-position: -40px 0; background-image: url('http://${hostfqdn}/~azurebrd/images/triangle_right_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_right_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_right_reversed.png)';" onmouseout="document.getElementById('optional_right_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_right_plain.png)';"></div>$header</span>);
  } # if ($header eq 'Optional')
  my $message_span = '';
  if ($message) { $message_span = qq(<span style="color: $message_colour; font-size: $message_fontsize;">$message</span>); }
  print qq(<span id="header_$header">$header_with_javascript $message_span<span>);
  print qq(</td></tr>\n);
} # sub printTrHeader

sub printPersonField {         printArrayEditorNested('person');                                                                            }
sub printEmailField {          printArrayEditorNested('email');                                                                             }
sub printPmidField {           printArrayEditorNested('pmid');                                                                              }
sub printCloneSeqField {       printArrayEditorNested('cloneseq', 'cloneseqspecies');                                                       }
sub printAlleleField {         printArrayEditorNested('allele');                                                                            }
sub printTransgeneField {      printArrayEditorNested('transgene', 'transgenegene');                                                        }
sub printObsPhenotypeField {   printArrayEditorNested('obsphenotypeterm', 'obsphenotyperemark', 'obsphenotypepersonal');                    }
sub printNotPhenotypeField {   printArrayEditorNested('notphenotypeterm', 'notphenotyperemark', 'notphenotypepersonal');                    }
sub printObsSuggestField {     printArrayEditorNested('obssuggestedterm', 'obssuggesteddef', 'obssuggestedremark', 'obssuggestedpersonal'); }
sub printNotSuggestField {     printArrayEditorNested('notsuggestedterm', 'notsuggesteddef', 'notsuggestedremark', 'notsuggestedpersonal'); }
sub printAlleleNatureField {   printArrayEditorNested('allelenature');                                                                      }
sub printAlleleFunctionField { printArrayEditorNested('allelefunction');                                                                    }
sub printPenetranceField {     printArrayEditorNested('penetrance');                                                                        }
sub printGenotypeField {       printArrayEditorNested('genotype');                                                                          }
sub printStrainField {         printArrayEditorNested('strain');                                                                            }
sub printCommentField {        printArrayEditorNested('comment');                                                                           }
sub printTempSensField {
  my $i = 1; my $field = 'tempsens'; my $showAmount = 1;
  if ($fields{$field}{startHidden} eq 'startHidden') { $showAmount = 0; }
  my $group_style = ''; if ($i > $showAmount) { $group_style = 'display: none'; }
  if ($i < $fields{$field}{hasdata} + 1 + $showAmount) { $group_style = ''; }
  if ($i < $fields{'heatsens'}{hasdata} + 1 + $showAmount) { $group_style = ''; }
  if ($i < $fields{'coldsens'}{hasdata} + 1 + $showAmount) { $group_style = ''; }
  my $trToPrint = qq(<tr id="group_${i}_${field}" style="$group_style">\n);
  my $td_label .= &printEditorLabel($i, $field);
  $trToPrint   .= $td_label; 
  my $tdColspan = qq(colspan="2"); 
  my $minwidth  = '200px'; if ($fields{$field}{minwidth}) { $minwidth = $fields{$field}{minwidth}; }
#   my $tdStyle   = qq(style="min-width: $minwidth; border-style: solid; border-color: #000000;");
  my $tdStyle   = qq(style="min-width: $minwidth;");
  $trToPrint   .= qq(<td $tdColspan $tdStyle>);
  $trToPrint   .= &printEditorJustCheckbox(1, 'heatsens');
  $trToPrint   .= qq($fields{'heatsens'}{label}<br/>);
  $trToPrint   .= &printEditorJustCheckbox(1, 'coldsens');
  $trToPrint   .= qq($fields{'coldsens'}{label}<br/>);
  $trToPrint   .= qq(</td>);
  $trToPrint   .= qq(</tr>\n);
  print $trToPrint;
} # sub printTempSensField
sub printLinkToOtherForm {
  print qq(<tr id="group_1_linkotherform" style="display: none;"><td colspan="7">If you would like to submit molecular details for an allele, please do so <a href="http://www.wormbase.org/submissions/allele_sequence.cgi" target="new" style="font-weight: bold; text-decoration: underline;">here</a></td><tr>); }
sub printOptionalExplanation {
  print qq(<tr id="group_1_optionalexplain" style="display: none;"><td colspan="7">Please note: The following values apply to all allele, RNAi and transgene phenotypes indicated above.</td><tr>); }


sub printPhenontLink {
#   my $labelTdStyle   = qq(style="border-style: solid; border-color: #000000; color: grey; font-size: 10px;");
  my $labelTdStyle   = qq(style="color: grey; font-size: 10px;");
#   print qq(<tr><td></td><td $labelTdStyle>&nbsp;<a href="http://www.wormbase.org/tools/ontology_browser" target="new" style="font-weight: bold; text-decoration: underline;">Browse the Phenotype Ontology</a></td></tr>\n);
#   print qq(<tr><td></td><td $labelTdStyle>&nbsp;<a href="http://juancarlos.wormbase.org/tools/ontology_browser#phenotype" target="new" style="font-weight: bold; text-decoration: underline;">Browse the Phenotype Ontology</a></td></tr>\n);
  print qq(<tr><td></td><td colspan="2" $labelTdStyle>&nbsp;<a href="http://www.wormbase.org/tools/ontology_browser" target="new" style="font-weight: bold; text-decoration: underline;">Browse the Phenotype Ontology</a></td></tr>\n); }
sub printShowObsSuggestLink {
#   my $labelTdStyle   = qq(style="border-style: solid; border-color: #000000; color: grey; font-size: 10px;");
  my $labelTdStyle   = qq(style="color: grey; font-size: 10px;");
#   print qq(<tr id="showObsSuggestTr"><td></td><td $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_obssuggestedterm').style.display = ''; document.getElementById('showObsSuggestTr').style.display = 'none';"</td></tr>\n);
  print qq(<tr id="showObsSuggestTr"><td></td><td colspan="2" $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_obssuggestedterm').style.display = ''; document.getElementById('group_1_obssuggesteddef').style.display = ''; document.getElementById('group_1_obssuggestedremark').style.display = ''; document.getElementById('group_1_obssuggestedpersonal').style.display = ''; document.getElementById('showObsSuggestTr').style.display = 'none';"</td></tr>\n); }
sub printShowNotSuggestLink {
#   my $labelTdStyle   = qq(style="border-style: solid; border-color: #000000; color: grey; font-size: 10px;");
  my $labelTdStyle   = qq(style="color: grey; font-size: 10px;");
#   print qq(<tr id="showNotSuggestTr"><td></td><td $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_notsuggestedterm').style.display = ''; document.getElementById('showNotSuggestTr').style.display = 'none';"</td></tr>\n);
  print qq(<tr id="showNotSuggestTr"><td></td><td colspan="2" $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_notsuggestedterm').style.display = ''; document.getElementById('group_1_notsuggesteddef').style.display = ''; document.getElementById('group_1_notsuggestedremark').style.display = ''; document.getElementById('group_1_notsuggestedpersonal').style.display = ''; document.getElementById('showNotSuggestTr').style.display = 'none';"</td></tr>\n); }

# Can't find your phenotype (please enter a description of your phenotype)
#   two separate boxes, one for suggested term + one for suggested definition.  allow N pairs.  put those in app_suggested + app_suggested_definition

sub getIp {
  my $ip            = $query->remote_host();			# get value for current user IP, not (potentially) loaded IP 
  my %headers = map { $_ => $query->http($_) } $query->http();
  if ($headers{HTTP_X_REAL_IP}) { $ip = $headers{HTTP_X_REAL_IP}; }
  return $ip;
} # sub getIp

sub showForm {
  my $ip = &getIp();
  return if ($ip eq '46.161.41.199');			# spammed 2015 09 01
  return if ($ip eq '188.143.232.32');			# spammed 2016 03 19
  print qq(<form method="post" action="phenotype.cgi" enctype="multipart/form-data">);
  print qq(<div id="term_info_box" style="border: solid; position: fixed; top: 95px; right: 20px; width: 350px; z-index:2; background-color: white;">\n);
#   print qq(<div id="clear_term_info" style="position: fixed; z-index: 3; top: 102px; right: 30px";>&#10008;</div>\n);
#   print qq(<div id="clear_term_info" align="right" onclick="document.getElementById('term_info').innerHTML = '';">clear &#10008;</div>\n);
  print qq(<div id="clear_term_info" align="right" onclick="document.getElementById('term_info_box').style.display = 'none';"><img id="close_term_info_image" src="http://${hostfqdn}/~azurebrd/images/x_plain.png" onmouseover="document.getElementById('close_term_info_image').src='http://${hostfqdn}/~azurebrd/images/x_reversed.png';" onmouseout="document.getElementById('close_term_info_image').src='http://${hostfqdn}/~azurebrd/images/x_plain.png';"></div>\n);
  print qq(<div id="term_info" style="margin: 5px 5px 5px 5px;">Click on green question marks <span style="color: #06C729; font-weight: bold;">?</span> or start typing in a specific field to see more information here.</div>\n);
  print qq(</div>\n);
  &showEditorActions();
  print "<br/><br/>\n";
  print qq(<table border="0"><tr><td style="padding: 0 50px 0 0;">);	# extra table to have some padding to the right of the main table inside
#   print qq(<table border="1" style="border-spacing: 0 50px; padding: 0 50px 0 50px; table-layout: fixed;">);
# HIDE
  print qq(<table border="0">);

  print qq(<tr>);
  print qq(<td colspan="1" style="width: 175px; max-width: 175px; min-width: 175px;">&nbsp;</td>);
  print qq(<td colspan="1" style="width: 175px; max-width: 175px; min-width: 175px;">&nbsp;</td>);
  print qq(<td colspan="1" style="width: 125px; max-width: 125px; min-width: 125px;">&nbsp;</td>);
#   print qq(<td colspan="1">&nbsp;</td>);
#   print qq(<td colspan="1">&nbsp;</td>);
  print qq(<td colspan="1" style="width: 100px;">&nbsp;</td>);
  print qq(<td colspan="1" style="width: 100px;">&nbsp;</td>);
  print qq(<td colspan="1" style="width: 100px;">&nbsp;</td>);
  print qq(<td colspan="1">&nbsp;</td>);
  print qq(</tr>);


  &printPersonField();
  &printEmailField();
  &printPmidField();
  &printTrSpacer();
  &printTrHeader('Genetic Perturbation(s)', '20', '18px', "(one required)", '#ff0000', '13px');
  &printCloneSeqField();
  &printAlleleField();
  &printTransgeneField();
  &printTrSpacer();
  &printTrHeader('Phenotype(s)', '20', '18px', "(one required)", '#ff0000', '13px');
  &printObsPhenotypeField();
  &printPhenontLink();
  &printShowObsSuggestLink();
  &printObsSuggestField();
  &printNotPhenotypeField();
  &printPhenontLink();
  &printShowNotSuggestLink();
  &printNotSuggestField();
  &printTrSpacer();
  &printTrSpacer();
  &printTrHeader('Optional', '20', '18px', "(inheritance pattern, mutation effect, penetrance, temperature sensitivity, genetic background and general comments)", '#aaaaaa', '12px');
  &printOptionalExplanation();
  &printAlleleNatureField();
  &printAlleleFunctionField();
  &printPenetranceField();
  &printTempSensField();
  &printGenotypeField();
  &printStrainField();
  &printCommentField();
  &printLinkToOtherForm();
# #   &printOffset();

#   print qq(<tr><td>&nbsp;</td></tr>\n);
  print qq(</table>);
  print qq(</td></tr></table>);
  print "<br/><br/>\n";
  &showEditorActions();
  print qq(</form>);
} # sub showForm

sub showEditorActions {
#   print qq(<tr><td align="left" colspan="7">\n);
#   print qq(<span style="font-weight: bold; font-size: 12pt">Clicking Submit will email you a confirmation :</span>\n);
#   print qq(<input type="submit" name="action" value="Save for Later" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
  print qq(<input type="submit" name="action" value="Preview" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
#   print qq(<input type="submit" name="action" value="Submit" onclick="return confirm('Are you sure you want to submit?')" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
  print qq(<input type="submit" name="action" value="Submit">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
#   print qq(</td></tr>\n);
#   print qq(<tr><td align="left" colspan="7">&nbsp;</td></tr>\n);
} # sub showEditorActions

sub tableDisplayArray {
  my (@fields) = @_;
  my $formdata = '';
  my $amount      = $fields{$fields[0]}{multi};
  for my $i (1 .. $amount) {
    my $trHasvalue = 0; my $trData = '';
    foreach my $field (@fields) {
      my $label       = $fields{$field}{label};
      my $inputvalue  = $fields{$field}{inputvalue}{$i};
      my $termidvalue = $fields{$field}{termidvalue}{$i};
      my @inputtermidvalue;
      if ($inputvalue) {  push @inputtermidvalue, $inputvalue;  }
      if ($termidvalue) { push @inputtermidvalue, $termidvalue; }
      my $inputtermidvalue = join" -- ", @inputtermidvalue; 
#       if ($label) { $trData .= qq(<td>$label</td><td>$inputtermidvalue</td>\n); }	# if wanted to always add labels without data, sometimes personal communication is confusing.
      if ($inputtermidvalue) { $trData .= qq(<td>$label</td><td style ="overflow: hidden; text-overflow:ellipsis; max-width: 500px;">$inputtermidvalue</td>\n); }	# only add to table row if there's data, to keep confusion between labels and data
      if ($inputtermidvalue) { $trHasvalue++; }	# if input or termid of any field in the field, row has data
    } # foreach my $field (@fields)
      if ($trHasvalue) { $formdata .= qq(<tr>$trData</tr>\n); }
  } # for my $i (1 .. $amount)
  return $formdata;
} # sub tableDisplayArray

sub submit {
  my ($submit_flag) = @_;
  print "Content-type: text/html\n\n";
  print $header;
  print qq(<span style="font-size: 24pt;">Contribute phenotype connections</span><br/><br/>\n);

  foreach my $field (keys %fields) {
    my $amount = $fields{$field}{multi};
    for my $i (1 .. $amount) {
      my ($var, $inputvalue)  = &getHtmlVar($query, "input_${i}_$field");
      ($var, my $termidvalue) = &getHtmlVar($query, "termid_${i}_$field");
      if ($inputvalue) { 
        $fields{$field}{inputvalue}{$i} = $inputvalue;
        if ($i > $fields{$field}{hasdata}) { $fields{$field}{hasdata} = $i; }
      }
      if ($termidvalue) { 
        $fields{$field}{termidvalue}{$i} = $termidvalue;
        if ($i > $fields{$field}{hasdata}) { $fields{$field}{hasdata} = $i; }
      } # if ($termidvalue) 
    } # for my $i (1 .. $amount)
  } # foreach my $field (keys %fields)
  if ($fields{allele}{inputvalue}{1}) {			# sometimes allele names are typed without selecting a wbvariation, but they map to wbvariation
    unless ($fields{allele}{termidvalue}{1}) {
      $result = $dbh->prepare( "SELECT * FROM obo_name_variation WHERE obo_name_variation = '$fields{allele}{inputvalue}{1}';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
      if ($row[0]) { $fields{allele}{termidvalue}{1} = $row[0]; } } }
  unless ($fields{cloneseq}{inputvalue}{1}) {		# if there is no rnai, its species should be blank (not generalized for other fields) 2016 02 18
    $fields{cloneseqspecies}{inputvalue}{1} = ''; $fields{cloneseqspecies}{termidvalue}{1} = ''; }
    
  my $form_data  = qq(<table border="1" cellpadding="5">);
  $form_data    .= &tableDisplayArray('person'); 
  $form_data    .= &tableDisplayArray('email');  
  $form_data    .= &tableDisplayArray('pmid');   
  $form_data    .= &tableDisplayArray('cloneseq', 'cloneseqspecies'); 
  $form_data    .= &tableDisplayArray('allele'); 
  $form_data    .= &tableDisplayArray('transgene', 'transgenegene'); 
  $form_data    .= &tableDisplayArray('obsphenotypeterm', 'obsphenotyperemark', 'obsphenotypepersonal');
  $form_data    .= &tableDisplayArray('notphenotypeterm', 'notphenotyperemark', 'notphenotypepersonal');
  $form_data    .= &tableDisplayArray('obssuggestedterm', 'obssuggesteddef', 'obssuggestedremark', 'obssuggestedpersonal');
  $form_data    .= &tableDisplayArray('notsuggestedterm', 'notsuggesteddef', 'notsuggestedremark', 'notsuggestedpersonal');
  $form_data    .= &tableDisplayArray('allelenature'); 
  $form_data    .= &tableDisplayArray('allelefunction'); 
  $form_data    .= &tableDisplayArray('penetrance');
  $form_data    .= &tableDisplayArray('heatsens');
  $form_data    .= &tableDisplayArray('coldsens');
  $form_data    .= &tableDisplayArray('genotype');
  $form_data    .= &tableDisplayArray('strain');
  $form_data    .= &tableDisplayArray('comment');
  $form_data    .= qq(</table><br/><br/>);

    # on any submission action, update the person / email for the user's IP address
  &updateUserIp( $fields{person}{termidvalue}{1}, $fields{email}{inputvalue}{1} );
    # if the form has no person id, try to load from postgres by ip address
  unless ($fields{person}{termidvalue}{1}) {
    ( $fields{person}{termidvalue}{1}, $fields{person}{inputvalue}{1}, $fields{email}{termidvalue}{1} ) = &getUserByIp(); }

  if ($submit_flag eq 'submit') { 
      my $mandatoryFail = &checkMandatoryFields();
      if ($mandatoryFail) { 
          print $form_data;
          &showForm(); }
        else {
#           &deletePg($fields{origip}{inputvalue}{1}, $fields{origtime}{inputvalue}{1});	# if had save files, this would delete
          my $messageToUser = qq(Dear $fields{person}{inputvalue}{1}, thank you for submitting Phenotype data.<br/>A WormBase curator will be in touch if there are any questions.<br/>);
          print qq($messageToUser<br/>);
          print qq(<br/>$form_data);
          print qq(<br/>Return to the <a href="phenotype.cgi">Phenotype Form</a>.<br/>\n);
          &writePgOaAndEmail($messageToUser, $form_data);
        }
    }
    elsif ($submit_flag eq 'preview') { 
      my $mandatoryFail = &checkMandatoryFields();
#       print qq(<br/><b>Preview -</b> scroll down to continue filling out the form<br/><br/>\n);
      print $form_data;
      print qq(<br/><b>Preview -</b> Please review the data for your submission above. If you would like to make edits, please do so in the form below. If you are finished adding data to the form, please click Submit.<br/><br/>\n);
      &showForm();
    }
#     elsif ($submit_flag eq 'save') { 
#       &deletePg($fields{origip}{inputvalue}{1}, $fields{origtime}{inputvalue}{1});
#       &saveFormData();
#     }
} # sub submit

sub writePgOaAndEmail {		# tacking on email here since need pgids from pg before emailing
  my ($messageToUser, $form_data)   = @_;
  my $paperHistOrig = '';
#   my $ip            = $query->remote_host();			# get value for current user IP, not (potentially) loaded IP 
  my $ip            = &getIp();
  my $timestamp     = &getPgDate();
  my $emailMaryann  = ''; my $emailKimberly = ''; my $emailKaren = '';
  my @newPgidsApp   = ();
  my @newPgidsRna   = ();
  my $pgidApp       = &getHighestPgid('app'); 
  my $pgidRna       = &getHighestPgid('rna'); 
  my $highRnaiId    = &getHighestRnaiId(); 
  my $nodump        = 'NO DUMP';
  my $needsreview   = 'Needs Review';
  my $curator       = 'WBPerson29819';
  my $person        = $fields{person}{termidvalue}{1};
  my $personName    = $fields{person}{inputvalue}{1};
  my $email         = $fields{email}{inputvalue}{1};
  my $pmid          = $fields{pmid}{inputvalue}{1} || '';
  if ($pmid =~ m/^\s+/) { $pmid =~ s/^\s+//; }
  if ($pmid =~ m/\s+$/) { $pmid =~ s/\s+$//; }
  if ($pmid =~ m/^pmid:?(\d+)/i) { $pmid = $1; }
#   if ($pmid) { if ($pmid =~ m/(\d+)/) { ($pmid) = $1; } }	# get just the pmid digits for the match and to store if unrecognized
  my $wbpaperOrig   = ''; my $unregpaperOrig = $pmid;
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier = 'pmid$pmid';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $wbpaperOrig = 'WBPaper' . $row[0]; $unregpaperOrig = ''; }
  if ($wbpaperOrig) {    $paperHistOrig = "$pmid ($wbpaperOrig)"; } 
    else {               $paperHistOrig = "$pmid (no match)"; }
  if ($unregpaperOrig) { $emailKimberly .= qq(PMID "$unregpaperOrig" is new.\n); }
  my %alleles;
  my $amountAllele   = $fields{allele}{multi};
  for my $i (1 .. $amountAllele) {
    my $unregallele = $fields{allele}{inputvalue}{$i}  || '';
    my $variation   = $fields{allele}{termidvalue}{$i} || '';
    next unless ($unregallele);
    my $alleleHist;
    if ($variation) {    $alleleHist = "$unregallele ($variation)"; $unregallele = ''; }
      else {             $alleleHist = "$unregallele (no match)";   $emailMaryann .= qq(Allele "$unregallele" is new.\n); }
    $alleles{$i}{unregallele} = $unregallele;
    $alleles{$i}{variation}   = $variation;
    $alleles{$i}{alleleHist}  = $alleleHist;
  }
  my %transgenes;
  my $amountAllele   = $fields{transgene}{multi};
  for my $i (1 .. $amountAllele) {
    my $unregtransgene = $fields{transgene}{inputvalue}{$i}     || '';
    my $wbtransgene    = $fields{transgene}{termidvalue}{$i}    || '';
    my $transgenegene  = $fields{transgenegene}{inputvalue}{$i} || '';
    next unless ($unregtransgene);
    my $transgeneHist;
    if ($wbtransgene) {  $transgeneHist = "$unregtransgene ($wbtransgene)"; $unregtransgene = ''; }
      else {             $transgeneHist = "$unregtransgene (no match)";     $emailKaren .= qq(Transgene "$unregtransgene" is new.\n); }
    $transgenes{$i}{unregtransgene} = $unregtransgene;
    $transgenes{$i}{wbtransgene}    = $wbtransgene;
    $transgenes{$i}{transgeneHist}  = $transgeneHist;
    $transgenes{$i}{transgenegene}  = $transgenegene;
  }
  my $rnai          = $fields{cloneseq}{inputvalue}{1} || '';
  my $rnaiSpecies   = $fields{cloneseqspecies}{inputvalue}{1} || '';
#   my $unregallele   = $fields{allele}{inputvalue}{1};
#   my $variation     = $fields{allele}{termidvalue}{1} || '';
#   if ($variation) {    $alleleHist = "$unregallele ($variation)"; $unregallele = ''; }
#     else {             $alleleHist = "$unregallele (no match)";   $emailMaryann .= qq(Allele "$unregallele" is new.\n); }
  my $nature        = $fields{allelenature}{inputvalue}{1} || '';
  my $func          = $fields{allelefunction}{inputvalue}{1} || '';
  my $penetrance    = $fields{penetrance}{inputvalue}{1} || '';
  my $comment       = $fields{comment}{inputvalue}{1} || '';
  my $heat_sens     = $fields{heatsens}{inputvalue}{1} || '';
  my $cold_sens     = $fields{coldsens}{inputvalue}{1} || '';
  my $genotype      = $fields{genotype}{inputvalue}{1} || '';
  my $strain        = $fields{strain}{termidvalue}{1} || '';
# TODO strain genotype
  my @historyAppend = ();
# TODO new columns for transgene and rnai, need to change headers, add to new file 'phenotype_history.html'

# write to history file
# IP address
# Timestamp
# Curator Name
# Curator Email
# PGID
# PubMed ID (or text with "(no match)")
# Allele name (or text with "(no match)")
# Phenotype (or text with "(no match)")
# NOT (to flag not observed or suggested not observed phenotypes)
# Allele nature
# Allele function
# Penetrance
# Heat sensitive
# Cold sensitive

# process separate variations and transgenes into separate OA rows with pgid and separate history rows.
# get obsphenotypepersonal (and the 3 others), and if personal do not write paper nor unregpaper but use person for app_person instead

  my $amountObs   = $fields{obsphenotypeterm}{multi};
  for my $i (1 .. $amountObs) {
    my $obssuggesteddefValue      = ''; my $not = '';
    my $obsphenotypetermValue     = $fields{'obsphenotypeterm'}{termidvalue}{$i};
    my $obsphenotypetermName      = $fields{'obsphenotypeterm'}{inputvalue}{$i};
    my $obsphenotyperemarkValue   = $fields{'obsphenotyperemark'}{inputvalue}{$i};
    my $obsphenotypepersonalValue = $fields{'obsphenotypepersonal'}{inputvalue}{$i};
    my $unregpaper = $unregpaperOrig; my $wbpaper = $wbpaperOrig; my $paperHist = $paperHistOrig; my $personEvi = ''; 
    if ($obsphenotypepersonalValue) { $unregpaper = ''; $wbpaper = ''; $paperHist = ''; $personEvi = $person; }
    if ($obsphenotypetermValue) {
      foreach my $i (sort {$a<=>$b} keys %alleles) {
        my $unregallele = $alleles{$i}{unregallele}; my $variation = $alleles{$i}{variation}; my $alleleHist = $alleles{$i}{alleleHist};
        my $transgeneHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregtransgene = ''; my $wbtransgene = ''; my $transgenegene = ''; my $speciesBlank = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$speciesBlank\t$obsphenotypepersonalValue\t$obsphenotypetermName ($obsphenotypetermValue)\t$not\t$obsphenotyperemarkValue\t$obssuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, $nature, $func, $penetrance, $heat_sens, $cold_sens, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'term', $obsphenotypetermValue);
        &writePgField($datatype, $pgidApp, 'phen_remark', $obsphenotyperemarkValue); } 
      foreach my $i (sort {$a<=>$b} keys %transgenes) {	# no nature func heat_sens cold_sens for transgenes
        my $unregtransgene = $transgenes{$i}{unregtransgene}; my $wbtransgene   = $transgenes{$i}{wbtransgene};
        my $transgeneHist  = $transgenes{$i}{transgeneHist};  my $transgenegene = $transgenes{$i}{transgenegene};
        my $alleleHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregallele = ''; my $variation = ''; my $speciesBlank = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$speciesBlank\t$obsphenotypepersonalValue\t$obsphenotypetermName ($obsphenotypetermValue)\t$not\t$obsphenotyperemarkValue\t$obssuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, '', '', $penetrance, '', '', $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'term', $obsphenotypetermValue);
        &writePgField($datatype, $pgidApp, 'phen_remark', $obsphenotyperemarkValue); } 
      if ($rnai) {
        $pgidRna++; push @newPgidsRna, $pgidRna; $highRnaiId++;
        my $rnaiHist = $rnai; my $datatype = 'rna'; my $alleleHist = ''; my $transgeneHist = ''; my $transgenegene = '';
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidRna\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$obsphenotypepersonalValue\t$obsphenotypetermName ($obsphenotypetermValue)\t$not\t$obsphenotyperemarkValue\t$obssuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsRna($pgidRna, $highRnaiId, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $rnai, $rnaiSpecies, $penetrance, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidRna, 'phenotype', $obsphenotypetermValue);
        &writePgField($datatype, $pgidRna, 'phenremark', $obsphenotyperemarkValue); } } }

  my $amountNot   = $fields{notphenotypeterm}{multi};
  for my $i (1 .. $amountNot) {
    my $notsuggesteddefValue      = ''; my $not = 'NOT';
    my $notphenotypetermValue     = $fields{'notphenotypeterm'}{termidvalue}{$i};
    my $notphenotypetermName      = $fields{'notphenotypeterm'}{inputvalue}{$i};
    my $notphenotyperemarkValue   = $fields{'notphenotyperemark'}{inputvalue}{$i};
    my $notphenotypepersonalValue = $fields{'notphenotypepersonal'}{inputvalue}{$i};
    my $unregpaper = $unregpaperOrig; my $wbpaper = $wbpaperOrig; my $paperHist = $paperHistOrig; my $personEvi = ''; 
    if ($notphenotypepersonalValue) { $unregpaper = ''; $wbpaper = ''; $paperHist = ''; $personEvi = $person; }
    if ($notphenotypetermValue) {
      foreach my $i (sort {$a<=>$b} keys %alleles) {
        my $unregallele = $alleles{$i}{unregallele}; my $variation = $alleles{$i}{variation}; my $alleleHist = $alleles{$i}{alleleHist};
        my $transgeneHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregtransgene = ''; my $wbtransgene = ''; my $transgenegene = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$notphenotypepersonalValue\t$notphenotypetermName ($notphenotypetermValue)\t$not\t$notphenotyperemarkValue\t$notsuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, $nature, $func, $penetrance, $heat_sens, $cold_sens, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'term', $notphenotypetermValue);
        &writePgField($datatype, $pgidApp, 'not', 'NOT');
        &writePgField($datatype, $pgidApp, 'phen_remark', $notphenotyperemarkValue); } 
      foreach my $i (sort {$a<=>$b} keys %transgenes) {
        my $unregtransgene = $transgenes{$i}{unregtransgene}; my $wbtransgene   = $transgenes{$i}{wbtransgene};
        my $transgeneHist  = $transgenes{$i}{transgeneHist};  my $transgenegene = $transgenes{$i}{transgenegene};
        my $alleleHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregallele = ''; my $variation = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$notphenotypepersonalValue\t$notphenotypetermName ($notphenotypetermValue)\t$not\t$notphenotyperemarkValue\t$notsuggesteddefValue\t\t\t$penetrance\t$heat_sens\t$cold_sens\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, '', '', $penetrance, '', '', $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'term', $notphenotypetermValue);
        &writePgField($datatype, $pgidApp, 'not', 'NOT');
        &writePgField($datatype, $pgidApp, 'phen_remark', $notphenotyperemarkValue); } 
      if ($rnai) {
        $pgidRna++; push @newPgidsRna, $pgidRna; $highRnaiId++;
        my $rnaiHist = $rnai; my $datatype = 'rna'; my $alleleHist = ''; my $transgeneHist = ''; my $transgenegene = '';
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidRna\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$notphenotypepersonalValue\t$notphenotypetermName ($notphenotypetermValue)\t$not\t$notphenotyperemarkValue\t$notsuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsRna($pgidRna, $highRnaiId, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $rnai, $rnaiSpecies, $penetrance, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidRna, 'phenotype', $notphenotypetermValue);
        &writePgField($datatype, $pgidRna, 'phenotypenot', 'NOT');
        &writePgField($datatype, $pgidRna, 'phenremark', $notphenotyperemarkValue); } } }

  my $amountObsSug   = $fields{obssuggestedterm}{multi};
  for my $i (1 .. $amountObsSug) {
    my $not = '';
    my $obssuggestedtermName      = $fields{'obssuggestedterm'}{inputvalue}{$i};
    my $obssuggesteddefValue      = $fields{'obssuggesteddef'}{inputvalue}{$i};
    my $obssuggestedremarkValue   = $fields{'obssuggestedremark'}{inputvalue}{$i};
    my $obssuggestedpersonalValue = $fields{'obssuggestedpersonal'}{inputvalue}{$i};
    my $unregpaper = $unregpaperOrig; my $wbpaper = $wbpaperOrig; my $paperHist = $paperHistOrig; my $personEvi = ''; 
    if ($obssuggestedpersonalValue) { $unregpaper = ''; $wbpaper = ''; $paperHist = ''; $personEvi = $person; }
    if ($obssuggestedtermName) {
      foreach my $i (sort {$a<=>$b} keys %alleles) {
        my $unregallele = $alleles{$i}{unregallele}; my $variation = $alleles{$i}{variation}; my $alleleHist = $alleles{$i}{alleleHist};
        my $transgeneHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregtransgene = ''; my $wbtransgene = ''; my $transgenegene = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$obssuggestedpersonalValue\t$obssuggestedtermName (no match)\t$not\t$obssuggestedremarkValue\t$obssuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, $nature, $func, $penetrance, $heat_sens, $cold_sens, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'suggested', $obssuggestedtermName);
        &writePgField($datatype, $pgidApp, 'suggested_definition', $obssuggesteddefValue);
        &writePgField($datatype, $pgidApp, 'phen_remark', $obssuggestedremarkValue); } 
      foreach my $i (sort {$a<=>$b} keys %transgenes) {
        my $unregtransgene = $transgenes{$i}{unregtransgene}; my $wbtransgene   = $transgenes{$i}{wbtransgene};
        my $transgeneHist  = $transgenes{$i}{transgeneHist};  my $transgenegene = $transgenes{$i}{transgenegene};
        my $alleleHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregallele = ''; my $variation = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$obssuggestedpersonalValue\t$obssuggestedtermName (no match)\t$not\t$obssuggestedremarkValue\t$obssuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, '', '', $penetrance, '', '', $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'suggested', $obssuggestedtermName);
        &writePgField($datatype, $pgidApp, 'suggested_definition', $obssuggesteddefValue);
        &writePgField($datatype, $pgidApp, 'phen_remark', $obssuggestedremarkValue); } 
      if ($rnai) {
        $pgidRna++; push @newPgidsRna, $pgidRna; $highRnaiId++;
        my $rnaiHist = $rnai; my $datatype = 'rna'; my $alleleHist = ''; my $transgeneHist = ''; my $transgenegene = '';
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidRna\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$obssuggestedpersonalValue\t$obssuggestedtermName (no match)\t$not\t$obssuggestedremarkValue\t$obssuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsRna($pgidRna, $highRnaiId, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $rnai, $rnaiSpecies, $penetrance, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidRna, 'suggested', $obssuggestedtermName);
        &writePgField($datatype, $pgidRna, 'suggested_definition', $obssuggesteddefValue);
        &writePgField($datatype, $pgidRna, 'phenremark', $obssuggestedremarkValue); } } }

  my $amountNotSug   = $fields{notsuggestedterm}{multi};
  for my $i (1 .. $amountNotSug) {
    my $not = 'NOT';
    my $notsuggestedtermName      = $fields{'notsuggestedterm'}{inputvalue}{$i};
    my $notsuggesteddefValue      = $fields{'notsuggesteddef'}{inputvalue}{$i};
    my $notsuggestedremarkValue   = $fields{'notsuggestedremark'}{inputvalue}{$i};
    my $notsuggestedpersonalValue = $fields{'notsuggestedpersonal'}{inputvalue}{$i};
    my $unregpaper = $unregpaperOrig; my $wbpaper = $wbpaperOrig; my $paperHist = $paperHistOrig; my $personEvi = ''; 
    if ($notsuggestedpersonalValue) { $unregpaper = ''; $wbpaper = ''; $paperHist = ''; $personEvi = $person; }
    if ($notsuggestedtermName) {
      foreach my $i (sort {$a<=>$b} keys %alleles) {
        my $unregallele = $alleles{$i}{unregallele}; my $variation = $alleles{$i}{variation}; my $alleleHist = $alleles{$i}{alleleHist};
        my $transgeneHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregtransgene = ''; my $wbtransgene = ''; my $transgenegene = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$notsuggestedpersonalValue\t$notsuggestedtermName (no match)\t$not\t$notsuggestedremarkValue\t$notsuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, $nature, $func, $penetrance, $heat_sens, $cold_sens, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'suggested', $notsuggestedtermName);
        &writePgField($datatype, $pgidApp, 'suggested_definition', $notsuggesteddefValue);
        &writePgField($datatype, $pgidApp, 'not', 'NOT');
        &writePgField($datatype, $pgidApp, 'phen_remark', $notsuggestedremarkValue); } 
      foreach my $i (sort {$a<=>$b} keys %transgenes) {
        my $unregtransgene = $transgenes{$i}{unregtransgene}; my $wbtransgene   = $transgenes{$i}{wbtransgene};
        my $transgeneHist  = $transgenes{$i}{transgeneHist};  my $transgenegene = $transgenes{$i}{transgenegene};
        my $alleleHist = ''; my $rnaiHist = ''; my $datatype = 'app'; my $unregallele = ''; my $variation = '';
        $pgidApp++; push @newPgidsApp, $pgidApp;
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$notsuggestedpersonalValue\t$notsuggestedtermName (no match)\t$not\t$notsuggestedremarkValue\t$notsuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsApp($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, '', '', $penetrance, '', '', $genotype, $strain, $comment);
        &writePgField($datatype, $pgidApp, 'suggested', $notsuggestedtermName);
        &writePgField($datatype, $pgidApp, 'suggested_definition', $notsuggesteddefValue);
        &writePgField($datatype, $pgidApp, 'not', 'NOT');
        &writePgField($datatype, $pgidApp, 'phen_remark', $notsuggestedremarkValue); } 
      if ($rnai) {
        $pgidRna++; push @newPgidsRna, $pgidRna; $highRnaiId++;
        my $rnaiHist = $rnai; my $datatype = 'rna'; my $alleleHist = ''; my $transgeneHist = ''; my $transgenegene = '';
        push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidRna\t$paperHist\t$alleleHist\t$transgeneHist\t$transgenegene\t$rnaiHist\t$rnaiSpecies\t$notsuggestedpersonalValue\t$notsuggestedtermName (no match)\t$not\t$notsuggestedremarkValue\t$notsuggesteddefValue\t\t\t$penetrance\t\t\t$genotype\t$strain\t$comment);
        &writePgRowFieldsRna($pgidRna, $highRnaiId, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $personEvi, $rnai, $rnaiSpecies, $penetrance, $genotype, $strain, $comment);
        &writePgField($datatype, $pgidRna, 'suggested', $notsuggestedtermName);
        &writePgField($datatype, $pgidRna, 'suggested_definition', $notsuggesteddefValue);
        &writePgField($datatype, $pgidRna, 'phenotypenot', 'NOT');
        &writePgField($datatype, $pgidRna, 'phenremark', $notsuggestedremarkValue); } } }

#   my $amountNot   = $fields{notphenotypeterm}{multi};
#   for my $i (1 .. $amountNot) {
#     my $notphenotypetermValue   = $fields{'notphenotypeterm'}{termidvalue}{$i};
#     my $notphenotypetermName    = $fields{'notphenotypeterm'}{inputvalue}{$i};
#     my $notphenotyperemarkValue = $fields{'notphenotyperemark'}{inputvalue}{$i};
#     if ($notphenotypetermValue) {
#       $pgidApp++; push @newPgidsApp, $pgidApp;
#       my $notsuggesteddefValue  = ''; my $not = 'NOT';
#       push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$notphenotypetermName ($notphenotypetermValue)\t$not\t$notphenotyperemarkValue\t$notsuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
#       &writePgRowFields($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
#       &writePgField($pgidApp, 'term', $notphenotypetermValue);
#       &writePgField($pgidApp, 'not', 'NOT');
#       &writePgField($pgidApp, 'phen_remark', $notphenotyperemarkValue); } }

#   my $amountObsSug   = $fields{obssuggestedterm}{multi};
#   for my $i (1 .. $amountObsSug) {
#     my $obssuggestedtermValue   = $fields{'obssuggestedterm'}{inputvalue}{$i};
#     my $obssuggesteddefValue    = $fields{'obssuggesteddef'}{inputvalue}{$i};
#     my $obssuggestedremarkValue = $fields{'obssuggestedremark'}{inputvalue}{$i};
#     if ($obssuggestedtermValue) {
#       $pgidApp++; push @newPgidsApp, $pgidApp; 
#       my $not = '';
#       push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$obssuggestedtermValue (no match)\t$not\t$obssuggestedremarkValue\t$obssuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
#       &writePgRowFields($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
#       &writePgField($pgidApp, 'suggested', $obssuggestedtermValue);
#       &writePgField($pgidApp, 'suggested_definition', $obssuggesteddefValue);
#       &writePgField($pgidApp, 'phen_remark', $obssuggestedremarkValue); } }

#   my $amountNotSug   = $fields{notsuggestedterm}{multi};
#   for my $i (1 .. $amountNotSug) {
#     my $notsuggestedtermValue   = $fields{'notsuggestedterm'}{inputvalue}{$i};
#     my $notsuggesteddefValue    = $fields{'notsuggesteddef'}{inputvalue}{$i};
#     my $notsuggestedremarkValue = $fields{'notsuggestedremark'}{inputvalue}{$i};
#     if ($notsuggestedtermValue) {
#       $pgidApp++; push @newPgidsApp, $pgidApp;
#       my $not = 'NOT';
#       push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgidApp\t$paperHist\t$alleleHist\t$notsuggestedtermValue (no match)\t$not\t$notsuggestedremarkValue\t$notsuggesteddefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
#       &writePgRowFields($pgidApp, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
#       &writePgField($pgidApp, 'not', 'NOT');
#       &writePgField($pgidApp, 'suggested', $notsuggestedtermValue);
#       &writePgField($pgidApp, 'suggested_definition', $notsuggesteddefValue);
#       &writePgField($pgidApp, 'phen_remark', $notsuggestedremarkValue); } }

  my $newPgidsApp = join",", @newPgidsApp;
  my $newPgidsRna = join",", @newPgidsRna;

  my $user = 'phenotype_form@' . $hostfqdn;	# who sends mail
  if ($emailKimberly) {
    my $email       = 'cgrove@caltech.edu, vanauken@caltech.edu';
#     my $email       = 'closertothewake@gmail.com';
    my $subject     = qq(Phenotype Form: Unregistered paper alert);
    $emailKimberly .= qq(New PGIDs in phenotype OA $newPgidsApp\n);
#     print "Email Kimberly $emailKimberly<br/>\n";
# UNCOMMENT send kimberly emails
    &mailSendmail($user, $email, $subject, $emailKimberly);
  }
  if ($emailMaryann) {
    my $email      = 'cgrove@caltech.edu, maryann.tuli@wormbase.org';
#     my $email      = 'closertothewake@gmail.com';
    my $subject    = qq(Phenotype Form: Unregistered variation alert);
    $emailMaryann .= qq(New PGIDs in phenotype OA $newPgidsApp\n);
#     print "Email Mary Ann $emailMaryann<br/>\n";
# UNCOMMENT send kimberly emails
    &mailSendmail($user, $email, $subject, $emailMaryann);
  }
  if ($emailKaren) {
    my $email      = 'cgrove@caltech.edu, karen@wormbase.org';
#     my $email      = 'closertothewake@gmail.com';
    my $subject    = qq(Phenotype Form: Unregistered transgene alert);
    $emailKaren .= qq(New PGIDs in phenotype OA $newPgidsApp\n);
#     print "Email Karen $emailKaren<br/>\n";
# UNCOMMENT send karen emails
    &mailSendmail($user, $email, $subject, $emailKaren);
  }
  my $cc = 'cgrove@caltech.edu, kyook@caltech.edu, garys@caltech.edu';
#   my $email = 'cgrove@caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
#   my $email = 'closertothewake@gmail.com';
#   $email   .= ", $fields{email}{inputvalue}{1}";
  my $email   = "$fields{email}{inputvalue}{1}";
  my $subject = 'Phenotype confirmation';		# subject of mail
  my $body = $messageToUser;					# message to user shown on form
  $body .= qq(Click <a href='http://${hostfqdn}/~azurebrd/cgi-bin/forms/phenotype.cgi?action=bogusSubmission&pgidsApp=$newPgidsApp&pgidsRna=$newPgidsRna&ipAddress=$ip' target='_blank' style='font-weight: bold; text-decoration: underline;'>here</a> if you did not submit this data or if you would like to retract this submission.<br/><br/>\n);	# additional link to report false data
  $body .= $form_data;						# form data
# UNCOMMENT send general emails
  &mailSendmail($user, $email, $subject, $body, $cc);

# uncomment to show history on form output
#   print qq(<table>);
#   print qq(<tr><th>ip</th><th>timestamp</th><th>person</th><th>email</th><th>pgid</th><th>paper</th><th>allele</th><th>transgene</th><th>caused_by</th><th>rnai</th><th>species</th><th>personal</th><th>phenotype</th><th>not</th><th>phenotype remark</th><th>suggested definition</th><th>nature</th><th>func</th><th>penetrance</th><th>heat_sens</th><th>cold_sens</th><th>genotype</th><th>strain</th><th>comment</th></tr>\n);
#   foreach my $line (@historyAppend) {
#     $line =~ s/\t/<\/td><td>/g; 
#     $line = qq(<tr><td>$line</td></tr>\n); 
#     print qq(HISTORY APPEND $line END<br>);					# write whole file over again including new data
#   }
#   print qq(</table>);
# UNCOMMENT FOR HISTORY
  my $outfile = '/home/azurebrd/public_html/cgi-bin/data/phenotype_history.html';
  open (IN, "<$outfile") or die "Cannot open $outfile : $!";
  my $toOutput = <IN>;					# stuff to beginning of data at top of file
  foreach my $line (@historyAppend) {
    $line =~ s/\t/<\/td><td style ="overflow: hidden; text-overflow:ellipsis; max-width: 500px;">/g; 
    $line = qq(<tr><td>$line</td></tr>\n); 
    $toOutput .= $line; 				# append data
  }
  while (my $line = <IN>) { $toOutput .= $line; }	# append previous data and rest of html
  close (IN) or die "Cannot close $outfile : $!";
  open (OUT, ">$outfile") or die "Cannot append to $outfile : $!";
  print OUT $toOutput;					# write whole file over again including new data
  close (OUT) or die "Cannot close $outfile : $!";
} # sub writePgOaAndEmail

sub writePgField {
  my ($datatype, $pgid, $fieldTable, $fieldData) = @_;
  return unless $fieldData;
  my $pgTable = $datatype . '_' . $fieldTable;
  if ($fieldData =~ m/\'/) { $fieldData =~ s/\'/''/g; }                 # escape singlequotes
  my @pgcommands;
  push @pgcommands, qq(INSERT INTO ${pgTable} VALUES ('$pgid', '$fieldData'););
  push @pgcommands, qq(INSERT INTO ${pgTable}_hst VALUES ('$pgid', '$fieldData'););
  foreach my $pgcommand (@pgcommands) {
#     print qq($pgcommand<br/>\n);					# for debugging
# UNCOMMENT TO POPULATE
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
#   print qq(pgid $pgid pgTable $pgTable D $fieldData E<br/>\n);	# for debugging
} # sub writePgField

sub pad8Zeros {         # take a number and pad to 8 digits
  my $number = shift;
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }               # strip leading zeros
  if ($number < 10) { $number = '0000000' . $number; }
  elsif ($number < 100) { $number = '000000' . $number; }
  elsif ($number < 1000) { $number = '00000' . $number; }
  elsif ($number < 10000) { $number = '0000' . $number; }
  elsif ($number < 100000) { $number = '000' . $number; }
  elsif ($number < 1000000) { $number = '00' . $number; }
  elsif ($number < 10000000) { $number = '0' . $number; }
  return $number;
} # sub pad8Zeros
sub getHighestRnaiId {          # look at all rna_name, get the highest number and return
  my $highest = 0;
  my $result = $dbh->prepare( "SELECT rna_name FROM rna_name WHERE rna_name ~ '^WBRNAi'" ); $result->execute();
  while (my @row = $result->fetchrow()) { if ($row[0]) { $row[0] =~ s/WBRNAi//; if ($row[0] > $highest) { $highest = $row[0]; } } }
  return $highest; }

sub writePgRowFieldsRna {
  my ($pgid, $highRnaiId, $nodump, $needsreview, $curator, $communitycurator, $email, $unregpaper, $wbpaper, $personEvi, $rnai, $rnaiSpecies, $penetrance, $genotype, $strain, $comment) = @_;
  my $datatype = 'rna';
  my $rnaiId   = &pad8Zeros($highRnaiId);
  my $wbrnai   = 'WBRNAi' . $rnaiId;
  &writePgField($datatype, $pgid, 'name', $wbrnai);
  &writePgField($datatype, $pgid, 'nodump', $nodump);
  &writePgField($datatype, $pgid, 'needsreview', $needsreview);
  &writePgField($datatype, $pgid, 'curator', $curator);
  &writePgField($datatype, $pgid, 'communitycurator', $communitycurator);
  &writePgField($datatype, $pgid, 'communitycuratoremail', $email);
  &writePgField($datatype, $pgid, 'species', $rnaiSpecies);
  &writePgField($datatype, $pgid, 'unregpaper', $unregpaper);
  &writePgField($datatype, $pgid, 'paper', $wbpaper);
  &writePgField($datatype, $pgid, 'person', $personEvi);
  &writePgField($datatype, $pgid, 'dnatext', $rnai);
  &writePgField($datatype, $pgid, 'penetrance', $penetrance);
  &writePgField($datatype, $pgid, 'genotype', $genotype);
  &writePgField($datatype, $pgid, 'strain', $strain);
  &writePgField($datatype, $pgid, 'remark', $comment);
} # sub writePgRowFieldsRna

sub writePgRowFieldsApp {
  my ($pgid, $nodump, $needsreview, $curator, $communitycurator, $email, $unregpaper, $wbpaper, $personEvi, $unregallele, $variation, $unregtransgene, $wbtransgene, $transgenegene, $nature, $func, $penetrance, $heat_sens, $cold_sens, $genotype, $strain, $comment) = @_;
  my $datatype = 'app';
  &writePgField($datatype, $pgid, 'nodump', $nodump);
  &writePgField($datatype, $pgid, 'needsreview', $needsreview);
  &writePgField($datatype, $pgid, 'curator', $curator);
  &writePgField($datatype, $pgid, 'communitycurator', $communitycurator);
  &writePgField($datatype, $pgid, 'communitycuratoremail', $email);
  &writePgField($datatype, $pgid, 'unregpaper', $unregpaper);
  &writePgField($datatype, $pgid, 'paper', $wbpaper);
  &writePgField($datatype, $pgid, 'person', $personEvi);
  &writePgField($datatype, $pgid, 'unregvariation', $unregallele);
  &writePgField($datatype, $pgid, 'variation', $variation);
  &writePgField($datatype, $pgid, 'unregtransgene', $unregtransgene);
  &writePgField($datatype, $pgid, 'transgene', $wbtransgene);
  &writePgField($datatype, $pgid, 'caused_by_other', $transgenegene);
  &writePgField($datatype, $pgid, 'nature', $nature);
  &writePgField($datatype, $pgid, 'func', $func);
  &writePgField($datatype, $pgid, 'penetrance', $penetrance);
  &writePgField($datatype, $pgid, 'heat_sens', $heat_sens);
  &writePgField($datatype, $pgid, 'cold_sens', $cold_sens);
  &writePgField($datatype, $pgid, 'genotype', $genotype);
  &writePgField($datatype, $pgid, 'strain', $strain);
  &writePgField($datatype, $pgid, 'obj_remark', $comment);
} # sub writePgRowFields

sub getHighestPgid {                                    # get the highest joinkey from the primary tables
  my ($datatype) = @_;
  my @highestPgidTables = qw( strain rearrangement transgene variation curator );
  if ($datatype eq 'rna') { @highestPgidTables = qw( name curator ); }
  my $pgUnionQuery = "SELECT MAX(joinkey::integer) FROM ${datatype}_" . join" UNION SELECT MAX(joinkey::integer) FROM ${datatype}_", @highestPgidTables;
  my $result = $dbh->prepare( "SELECT max(max) FROM ( $pgUnionQuery ) AS max; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow(); my $highest = $row[0];
  return $highest;
} # sub getHighestPgid



sub checkMandatoryFields {
  my $mandatoryFail      = 0;
  my $aphenotypeExists   = 0;
  my $hasAnyPrimaryData  = 0;
  foreach my $field (keys %fields) {
    if ($field eq 'person') { 
      if ($fields{$field}{termidvalue}{1}) {
          unless ($fields{$field}{termidvalue}{1} =~ m/WBPerson/) { $mandatoryFail++; print qq(<span style="color:red">FAIL name has input but no TermID.</span>); } }
#         else { $mandatoryFail++; print qq(<span style="color:red">FAIL</span>); }	# this error message part of regular 'mandatory' check below
    }
    if ($fields{$field}{'mandatory'} eq 'mandatory') {
      unless ($fields{$field}{hasdata}) {
        $mandatoryFail++;
        print qq(<span style="color:red">$fields{$field}{label} is required.</span><br/>\n); } }
    if ($fields{$field}{'mandatory'} eq 'anyprimarydata') {
      if ($fields{$field}{hasdata}) { $hasAnyPrimaryData++; } }
  }
  unless ($hasAnyPrimaryData) {					# one of the primary data fields must have something : allele / transgene / rnai
    $mandatoryFail++;
    print qq(<span style="color:red">At least one genetic perturbation (Allele, Transgene or RNAi Clone / Sequence) is required.</span><br/>\n); }
  unless ( $fields{pmid}{inputvalue}{1} ) {			# if there's no pmid, check all phenotype fields for corresponding personal communication checkbox on
    my @phenFields = qw( obsphenotype obssuggested notphenotype notsuggested );
    my $pmidPersonalFail = 0;
    foreach my $shortfield (@phenFields) {
      my $termField = $shortfield . 'term';
      my $persField = $shortfield . 'personal';
      my $amount    = $fields{$termField}{multi};
      for my $i (1 .. $amount) {
        if ($fields{$termField}{inputvalue}{$i}) { 
          unless ($fields{$persField}{inputvalue}{$i}) { $pmidPersonalFail++; } } } }
    if ($pmidPersonalFail) {
      $mandatoryFail++;
      print qq(<span style="color:red">PMID is required, or all phenotype fields must have the Personal Communication checkbox selected.</span><br/>\n); } }
  unless ( ($fields{obsphenotypeterm}{hasdata}) || ($fields{obssuggestedterm}{hasdata}) || ($fields{notphenotypeterm}{hasdata}) || ($fields{notsuggestedterm}{hasdata}) ) {
    $mandatoryFail++;
    print qq(<span style="color:red">At least one phenotype is required.</span><br/>\n); }
  if ($mandatoryFail > 0) { print qq(<br/><br/>\n); }
  return $mandatoryFail;
} # sub checkMandatoryFields

sub initFields {
#   tie %{ $fields{person}{field} }, "Tie::IxHash";
  $fields{person}{multi}                                      = '1';
  $fields{person}{type}                                       = 'ontology';
  $fields{person}{label}                                      = 'Your Name';
  $fields{person}{ontology_type}                              = 'WBPerson';
#   $fields{person}{haschecks}                                  = 'person';
  $fields{person}{terminfo}                                   = qq(Start typing and select your name from the list of registered WormBase persons and IDs. If you do not have a WBPerson ID, fill out our <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi" target="new">Person Update Form</a>.);
  $fields{person}{example}                                    = 'e.g. Bob Horvitz';
  $fields{person}{mandatory}                                  = 'mandatory';
#   tie %{ $fields{email}{field} }, "Tie::IxHash";
  $fields{email}{multi}                                       = '1';
  $fields{email}{type}                                        = 'text';
  $fields{email}{label}                                       = 'Your E-mail Address';
  $fields{email}{terminfo}                                    = qq(Enter your preferred e-mail address. A confirmation e-mail will be sent to this address upon data submission. If you selected your name from the registered WormBase Persons list in the previous field, your e-mail on file would have been used to populate this field. Feel free to correct this to a different, preferred e-mail address. You will need to update your contact information using the <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi" target="new">Person Update Form</a> if you want us to store this new e-mail address for you.);
  $fields{email}{example}                                     = 'e.g. help@wormbase.org';
  $fields{email}{mandatory}                                   = 'mandatory';
#   tie %{ $fields{pmid}{field} }, "Tie::IxHash";
  $fields{pmid}{multi}                                        = '1';
  $fields{pmid}{type}                                         = 'text';
  $fields{pmid}{label}                                        = 'PubMed ID';
  $fields{pmid}{haschecks}                                    = 'pmid';
  $fields{pmid}{terminfo}                                     = qq(Enter the PubMed ID for the paper in which this phenotype data was published. If your paper does not have a PubMed ID, please enter any unique identifier, like a D.O.I. (e.g. doi 10.1038/ni.2957). If you would like to report a phenotype as an unpublished personal communication, check the box next to 'Personal Communication' under the relevant phenotype.);
  $fields{pmid}{example}                                      = 'e.g. 4366476 (Please enter only one ID)';
  $fields{pmid}{mandatory}                                    = 'pmid';
  $fields{cloneseq}{multi}                                    = '1';
  $fields{cloneseq}{type}                                     = 'bigtext';
  $fields{cloneseq}{label}                                    = 'RNAi Clone(s) or Sequence(s)';
  $fields{cloneseq}{terminfo}                                 = qq(Enter the RNAi clone identity or sequence for any number of RNAi clones or sequences, separated by commas. Note: each phenotype entered will be independently annotated to each RNAi clone rather than annotated to the combination of clones.);
  $fields{cloneseq}{example}                                  = 'e.g. dpl-1 Ahringer clone, xbp-1 ORFeome clone, ATGCTAGCTGA...';
  $fields{cloneseq}{mandatory}                                = 'anyprimarydata';
  $fields{cloneseq}{grouphas}                                 = qq([ cloneseq cloneseqspecies ]);
  $fields{cloneseqspecies}{multi}                             = '1';
  $fields{cloneseqspecies}{startHidden}                       = 'startHidden';
  $fields{cloneseqspecies}{type}                              = 'dropdown';
  $fields{cloneseqspecies}{label}                             = 'Species';
  $fields{cloneseqspecies}{terminfo}                          = qq(Enter the species in which the RNAi experiment was carried out.);
  $fields{cloneseqspecies}{example}                           = 'elegans';
#   tie %{ $fields{allele}{field} }, "Tie::IxHash";
  $fields{allele}{multi}                                      = '10';
  $fields{allele}{type}                                       = 'ontology';
  $fields{allele}{label}                                      = 'Allele';
  $fields{allele}{freeForced}                                 = 'free';
  $fields{allele}{ontology_type}                              = 'obo';
  $fields{allele}{ontology_table}                             = 'variation';
  $fields{allele}{example}                                    = 'e.g. e1000';
  $fields{allele}{haschecks}                                  = 'allele';
  $fields{allele}{terminfo}                                   = qq(Enter the name of an allele for which you are providing phenotype data. Once you have started typing, select an allele from the list of known alleles. If you are entering an allele not recognized by WormBase, continue with your submission and a WormBase curator will contact you if there are any questions.);
  $fields{allele}{matchstartonly}                             = 'matchstartonly';
  $fields{allele}{mandatory}                                  = 'anyprimarydata';
  $fields{allele}{grouphas}                                   = qq([ allele ]);
  $fields{transgene}{multi}                                   = '10';
  $fields{transgene}{type}                                    = 'ontology';
  $fields{transgene}{label}                                   = 'Transgene';
  $fields{transgene}{freeForced}                              = 'free';
  $fields{transgene}{ontology_type}                           = 'WBTransgene';
  $fields{transgene}{example}                                 = 'e.g. ctIs40';
  $fields{transgene}{haschecks}                               = 'allele';
  $fields{transgene}{terminfo}                                = qq(Enter the name of a transgene for which you are providing phenotype data. Once you have started typing, select a transgene from the list of known transgenes. If you are entering a transgene not recognized by WormBase, continue with your submission and a WormBase curator will contact you if there are any questions.);
  $fields{transgene}{matchstartonly}                          = 'matchstartonly';
  $fields{transgene}{mandatory}                               = 'anyprimarydata';
  $fields{transgene}{grouphas}                                = qq([ transgene transgenegene ]);
  $fields{transgenegene}{multi}                               = '10';
  $fields{transgenegene}{startHidden}                         = 'startHidden';
  $fields{transgenegene}{type}                                = 'bigtext';
  $fields{transgenegene}{label}                               = 'Gene Causing Phenotype';
  $fields{transgenegene}{example}                             = 'e.g. dbl-1';
  $fields{transgenegene}{terminfo}                            = qq(Enter the identity of the gene or element within the transgene that is most likely responsible for the phenotype observed.);
#   tie %{ $fields{obsphenotypeterm}{field} }, "Tie::IxHash";
  $fields{obsphenotypeterm}{multi}                            = '10';
  $fields{obsphenotypeterm}{type}                             = 'ontology';
  $fields{obsphenotypeterm}{label}                            = 'Observed Phenotype';
  $fields{obsphenotypeterm}{ontology_type}                    = 'obo';
  $fields{obsphenotypeterm}{ontology_table}                   = 'phenotype';
  $fields{obsphenotypeterm}{example}                          = 'e.g. larval lethal';
  $fields{obsphenotypeterm}{terminfo}                         = qq(For phenotypes observed with the indicated allele(s), RNAi clone(s), or transgene(s), start typing and select a phenotype term from the WormBase Phenotype Ontology. If you are having trouble finding a phenotype, you may browse the phenotype ontology with the link provided.  If you still cannot find a suitable phenotype term, click on the checkbox next to "Can’t find your Phenotype?" and enter your suggested term and a definition in the fields provided.);
  $fields{obsphenotypeterm}{grouphas}                         = qq([ obsphenotypeterm obsphenotyperemark obsphenotypepersonal ]);
#   tie %{ $fields{obsphenotyperemark}{field} }, "Tie::IxHash";
  $fields{obsphenotyperemark}{multi}                          = '10';
  $fields{obsphenotyperemark}{startHidden}                    = 'startHidden';
  $fields{obsphenotyperemark}{type}                           = 'bigtext';
  $fields{obsphenotyperemark}{label}                          = 'Phenotype Remark';
  $fields{obsphenotyperemark}{example}                        = '(optional) e.g. Figure 3, animals die as L2 larvae';
  $fields{obsphenotyperemark}{terminfo}                       = qq(If you would like, provide more information about the phenotype effects of this allele.);
  $fields{obsphenotypepersonal}{multi}                        = '10';
  $fields{obsphenotypepersonal}{startHidden}                  = 'startHidden';
  $fields{obsphenotypepersonal}{type}                         = 'checkbox';
  $fields{obsphenotypepersonal}{label}                        = 'Personal Communication';
  $fields{obsphenotypepersonal}{terminfo}                     = qq(If you would like to report the indicated phenotype as an unpublished personal communication for all indicated alleles, RNAi clones, and transgenes, check this box.);
#   tie %{ $fields{obssuggestedterm}{field} }, "Tie::IxHash";
  $fields{obssuggestedterm}{multi}                            = '10';
  $fields{obssuggestedterm}{startHidden}                      = 'startHidden';
  $fields{obssuggestedterm}{type}                             = 'text';
  $fields{obssuggestedterm}{label}                            = 'Suggest Observed Phenotype';
  $fields{obssuggestedterm}{fontsize}                         = '8pt';
  $fields{obssuggestedterm}{terminfo}                         = qq(Provide the name of a new phenotype term and a brief definition. This phenotype will be annotated to all alleles, RNAi clones, and transgenes you have indicated above.);
  $fields{obssuggestedterm}{grouphas}                         = qq([ obssuggestedterm obssuggesteddef obssuggestedremark obssuggestedpersonal ]);
#   tie %{ $fields{obssuggesteddef}{field} }, "Tie::IxHash";
  $fields{obssuggesteddef}{multi}                             = '10';
  $fields{obssuggesteddef}{type}                              = 'bigtext';
  $fields{obssuggesteddef}{label}                             = 'Suggested Definition';
  $fields{obssuggesteddef}{example}                           = '(optional)';
  $fields{obssuggesteddef}{terminfo}                          = qq(Provide a brief definition for the new phenotype term you entered.);
#   tie %{ $fields{obssuggestedremark}{field} }, "Tie::IxHash";
  $fields{obssuggestedremark}{multi}                          = '10';
  $fields{obssuggestedremark}{type}                           = 'bigtext';
  $fields{obssuggestedremark}{label}                          = 'Phenotype Remark';
  $fields{obssuggestedremark}{example}                        = '(optional) e.g. Figure 3, animals die as L2 larvae';
  $fields{obssuggestedremark}{terminfo}                       = qq(If you would like, provide more information about the phenotype effects of this allele.);
  $fields{obssuggestedpersonal}{multi}                        = '10';
  $fields{obssuggestedpersonal}{type}                         = 'checkbox';
  $fields{obssuggestedpersonal}{label}                        = 'Personal Communication';
  $fields{obssuggestedpersonal}{terminfo}                     = qq(If you would like to report the indicated phenotype as an unpublished personal communication for all indicated alleles, RNAi clones, and transgenes, check this box.);
#   tie %{ $fields{notphenotypeterm}{field} }, "Tie::IxHash";
  $fields{notphenotypeterm}{multi}                            = '10';
  $fields{notphenotypeterm}{type}                             = 'ontology';
  $fields{notphenotypeterm}{label}                            = qq(<span style='color: red;'>Not</span> Observed Phenotype);
  $fields{notphenotypeterm}{ontology_type}                    = 'obo';
  $fields{notphenotypeterm}{ontology_table}                   = 'phenotype';
  $fields{notphenotypeterm}{example}                          = 'e.g. larval lethal';
  $fields{notphenotypeterm}{terminfo}                         = qq(For phenotypes assayed for and determined not to be exhibited by the allele(s), RNAi clone(s), or transgene(s), start typing and select a phenotype term from the WormBase Phenotype Ontology. If you are having trouble finding your phenotype, you may browse the phenotype ontology with the link provided. If you still cannot find a suitable phenotype, click on the checkbox next to "Can’t find your Phenotype?" and enter your suggested term and a definition in the fields provided.");
  $fields{notphenotypeterm}{grouphas}                         = qq([ notphenotypeterm notphenotyperemark notphenotypepersonal ]);
#   tie %{ $fields{notphenotyperemark}{field} }, "Tie::IxHash";
  $fields{notphenotyperemark}{multi}                          = '10';
  $fields{notphenotyperemark}{startHidden}                    = 'startHidden';
  $fields{notphenotyperemark}{type}                           = 'bigtext';
  $fields{notphenotyperemark}{label}                          = 'Phenotype Remark';
  $fields{notphenotyperemark}{example}                        = '(optional) e.g. Figure 3, animals die as L2 larvae';
  $fields{notphenotyperemark}{terminfo}                       = qq(If you would like, provide more information about the phenotype effects of this allele.);
  $fields{notphenotypepersonal}{multi}                        = '10';
  $fields{notphenotypepersonal}{startHidden}                  = 'startHidden';
  $fields{notphenotypepersonal}{type}                         = 'checkbox';
  $fields{notphenotypepersonal}{label}                        = 'Personal Communication';
  $fields{notphenotypepersonal}{terminfo}                     = qq(If you would like to report the indicated phenotype as an unpublished personal communication for all indicated alleles, RNAi clones, and transgenes, check this box.);
#   tie %{ $fields{notsuggestedterm}{field} }, "Tie::IxHash";
  $fields{notsuggestedterm}{multi}                            = '10';
  $fields{notsuggestedterm}{startHidden}                      = 'startHidden';
  $fields{notsuggestedterm}{type}                             = 'text';
  $fields{notsuggestedterm}{label}                            = qq(Suggest <span style='color: red;'>Not</span> Observed Phenotype);
  $fields{notsuggestedterm}{fontsize}                         = '8pt';
  $fields{notsuggestedterm}{terminfo}                         = qq(Provide the name of a new phenotype term and a brief definition. This phenotype will be annotated to all alleles, RNAi clones, and transgenes you have indicated above.);
  $fields{notsuggestedterm}{grouphas}                         = qq([ notsuggestedterm notsuggesteddef notsuggestedremark notsuggestedpersonal ]);
#   tie %{ $fields{notsuggesteddef}{field} }, "Tie::IxHash";
  $fields{notsuggesteddef}{multi}                             = '10';
  $fields{notsuggesteddef}{type}                              = 'bigtext';
  $fields{notsuggesteddef}{label}                             = 'Suggested Definition';
  $fields{notsuggesteddef}{example}                           = '(optional)';
  $fields{notsuggesteddef}{terminfo}                          = qq(Provide a brief definition for the new phenotype term you entered.);
#   tie %{ $fields{notsuggestedremark}{field} }, "Tie::IxHash";
  $fields{notsuggestedremark}{multi}                          = '10';
  $fields{notsuggestedremark}{type}                           = 'bigtext';
  $fields{notsuggestedremark}{label}                          = 'Phenotype Remark';
  $fields{notsuggestedremark}{example}                        = '(optional) e.g. Figure 3, animals die as L2 larvae';
  $fields{notsuggestedremark}{terminfo}                       = qq(If you would like, provide more information about the phenotype effects of this allele.);
  $fields{notsuggestedpersonal}{multi}                        = '10';
  $fields{notsuggestedpersonal}{startHidden}                  = 'startHidden';
  $fields{notsuggestedpersonal}{type}                         = 'checkbox';
  $fields{notsuggestedpersonal}{label}                        = 'Personal Communication';
  $fields{notsuggestedpersonal}{terminfo}                     = qq(If you would like to report the indicated phenotype as an unpublished personal communication for all indicated alleles, RNAi clones, and transgenes, check this box.);
#   tie %{ $fields{allelenature}{field} }, "Tie::IxHash";
  $fields{allelenature}{multi}                                = '1';
  $fields{allelenature}{type}                                 = 'dropdown';
  $fields{allelenature}{label}                                = 'Inheritance Pattern';
  $fields{allelenature}{startHidden}                          = 'startHidden';
  $fields{allelenature}{terminfo}                             = qq(If applicable, choose the inheritance pattern of the allele(s) with respect to the phenotype(s) entered.);
#   tie %{ $fields{allelefunction}{field} }, "Tie::IxHash";
  $fields{allelefunction}{multi}                              = '1';
  $fields{allelefunction}{type}                               = 'dropdown';
  $fields{allelefunction}{label}                              = 'Mutation Effect';
  $fields{allelefunction}{startHidden}                        = 'startHidden';
  $fields{allelefunction}{terminfo}                           = qq(If applicable, choose the functional consequence of the allele(s) with respect to the phenotype(s) entered.);
#   tie %{ $fields{penetrance}{field} }, "Tie::IxHash";
  $fields{penetrance}{multi}                                  = '1';
  $fields{penetrance}{type}                                   = 'dropdown';
  $fields{penetrance}{label}                                  = 'Penetrance';
  $fields{penetrance}{startHidden}                            = 'startHidden';
  $fields{penetrance}{terminfo}                               = qq(If applicable, choose a level of penetrance of the phenotype with respect to the allele(s), RNAi clone(s), or transgene(s) entered.);
#   tie %{ $fields{heatsens}{field} }, "Tie::IxHash";
  $fields{heatsens}{multi}                                    = '1';
  $fields{heatsens}{type}                                     = 'checkbox';
  $fields{heatsens}{label}                                    = 'Heat Sensitive';
#   tie %{ $fields{coldsens}{field} }, "Tie::IxHash";
  $fields{coldsens}{multi}                                    = '1';
  $fields{coldsens}{type}                                     = 'checkbox';
  $fields{coldsens}{label}                                    = 'Cold Sensitive';
#   tie %{ $fields{tempsens}{field} }, "Tie::IxHash";
  $fields{tempsens}{multi}                                    = '1';
  $fields{tempsens}{type}                                     = 'nodata';
  $fields{tempsens}{label}                                    = 'Temperature Sensitive';
  $fields{tempsens}{startHidden}                              = 'startHidden';
  $fields{tempsens}{terminfo}                                 = qq(If applicable, choose a temperature sensitivity of the allele(s) with respect to the phenotype(s) entered.);
  $fields{genotype}{multi}                                    = '1';
  $fields{genotype}{type}                                     = 'bigtext';
  $fields{genotype}{label}                                    = 'Control Genotype';
  $fields{genotype}{startHidden}                              = 'startHidden';
  $fields{genotype}{example}                                  = 'e.g. daf-2(e1370), adIs2122 [lgg-1p::GFP::LGG-1]';
  $fields{genotype}{terminfo}                                 = qq(Enter the genotype of the control strain. Include any pertinent components of the genetic background.);
  $fields{strain}{multi}                                      = '1';
  $fields{strain}{type}                                       = 'ontology';
  $fields{strain}{label}                                      = 'Control Strain';
  $fields{strain}{ontology_type}                              = 'obo';
  $fields{strain}{ontology_table}                             = 'strain';
  $fields{strain}{startHidden}                                = 'startHidden';
  $fields{strain}{example}                                    = 'e.g. N2, CB1370';
  $fields{strain}{terminfo}                                   = qq(Enter the identity of the control strain.);
#   tie %{ $fields{comment}{field} }, "Tie::IxHash";
  $fields{comment}{multi}                                     = '1';
  $fields{comment}{type}                                      = 'textarea';
  $fields{comment}{label}                                     = 'Comment';
  $fields{comment}{startHidden}                               = 'startHidden';

  tie %{ $dropdown{cloneseqspecies} }, "Tie::IxHash";
  $result = $dbh->prepare( "SELECT obo_name_species FROM obo_name_species WHERE obo_name_species !~ 'Homo' ORDER BY obo_timestamp" ); $result->execute(); 
  while (my @row = $result->fetchrow()) {
    $dropdown{cloneseqspecies}{$row[0]}                             = $row[0]; }
  tie %{ $dropdown{allelenature} }, "Tie::IxHash";
  $dropdown{allelenature}{""}                                       = "";
  $dropdown{allelenature}{"Recessive"}                              = "Recessive";
  $dropdown{allelenature}{"Semi_dominant"}                          = "Semi-dominant";
  $dropdown{allelenature}{"Dominant"}                               = "Dominant";
  tie %{ $dropdown{allelefunction} }, "Tie::IxHash";
  $dropdown{allelefunction}{""}                                     = "";
  $dropdown{allelefunction}{"Null"}                                 = "Complete loss of function / null / amorph";
  $dropdown{allelefunction}{"Probable_null_via_phenotype"}          = "Probable complete loss of function / probable null";
  $dropdown{allelefunction}{"Predicted_null_via_sequence"}          = "Predicted complete loss of function / predicted null";
  $dropdown{allelefunction}{"Hypomorph_reduction_of_function"}      = "Partial loss of function / reduction of function / hypomorph";
  $dropdown{allelefunction}{"Loss_of_function_undetermined_extent"} = "Loss of function, undetermined extent";
  $dropdown{allelefunction}{"Probable_hypomorph_via_phenotype"}     = "Probable reduction of function / probable hypomorph";
  $dropdown{allelefunction}{"Predicted_hypomorph_via_sequence"}     = "Predicted reduction of function / predicted hypomorph";
  $dropdown{allelefunction}{"Gain_of_function_undetermined_type"}   = "Gain of function, undetermined type";
  $dropdown{allelefunction}{"Neomorph_gain_of_function"}            = "Neomorph gain of function";
  $dropdown{allelefunction}{"Antimorph_gain_of_function"}           = "Antimorph gain of function";
  $dropdown{allelefunction}{"Hypermorph_gain_of_function"}          = "Hypermorph gain of function";
  $dropdown{allelefunction}{"Dominant_negative_gain_of_function"}   = "Dominant negative gain of function";
  $dropdown{allelefunction}{"Wild_allele"}                          = "Wild allele";
#   $dropdown{allelefunction}{"Loss_of_function"}                 = "Loss of function";
#   $dropdown{allelefunction}{"Hypomorph"}                        = "Hypomorph / Reduction of function";
#   $dropdown{allelefunction}{"Amorph"}                           = "Amorph / Null";
#   $dropdown{allelefunction}{"Uncharacterised_loss_of_function"} = "Uncharacterised loss of function";
#   $dropdown{allelefunction}{"Gain_of_function"}                 = "Gain of function";
#   $dropdown{allelefunction}{"Hypermorph"}                       = "Hypermorph";
#   $dropdown{allelefunction}{"Dominant_negative"}                = "Dominant negative / Antimorph";
#   $dropdown{allelefunction}{"Neomorph"}                         = "Neomorph";
#   $dropdown{allelefunction}{"Uncharacterised_gain_of_function"} = "Uncharacterised gain of function";
#   $dropdown{allelefunction}{"Wild_type"}                        = "Wild type";
#   $dropdown{allelefunction}{"Isoallele"}                        = "Isoallele";
#   $dropdown{allelefunction}{"Mixed"}                            = "Mixed";
  tie %{ $dropdown{penetrance} }, "Tie::IxHash";
  $dropdown{penetrance}{""}                                         = "";
  $dropdown{penetrance}{"Complete"}                                 = "Complete (100%)";
  $dropdown{penetrance}{"High"}                                     = "High (>90%)";
  $dropdown{penetrance}{"Incomplete"}                               = "Incomplete (10%< P <90%)";
  $dropdown{penetrance}{"Low"}                                      = "Low (<10%)";
} # sub initFields


# <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css" />
sub addJavascriptCssToHeader {
  my $extra_stuff = << "EndOfText";
<link rel="stylesheet" type="text/css" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" />
<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/fonts/fonts-min.css" />
<link rel="stylesheet" type="text/css" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/yui_edited_autocomplete.css" />
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/yahoo-dom-event/yahoo-dom-event.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/connection/connection-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/datasource/datasource-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/autocomplete/autocomplete-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/json/json-min.js"></script>
<script type="text/javascript" src="http://${hostfqdn}/~azurebrd/javascript/phenotype.js"></script>
<script type="text/JavaScript">
<!--Your browser is not set to be Javascript enabled
//-->
</script>

<!--// this javascript disables the return key to prevent form submission if someone presses return on an input field
// http://74.125.155.132/search?q=cache:FhzD9ine5fQJ:www.webcheatsheet.com/javascript/disable_enter_key.php+disable+return+on+input+submits+form&cd=6&hl=en&ct=clnk&gl=us
// 2009 12 14-->
<script type="text/javascript">
function stopRKey(evt) {
  var evt = (evt) ? evt : ((event) ? event : null);
  var node = (evt.target) ? evt.target : ((evt.srcElement) ? evt.srcElement : null);
  if ((evt.keyCode == 13) && (node.type=="text"))  {return false;}
}
document.onkeypress = stopRKey;
</script>

EndOfText
  $header =~ s/<\/head>/$extra_stuff\n<\/head>/;
  $header =~ s/<body>/<body class="yui-skin-sam">/;
} # sub addJavascriptCssToHeader

sub updateUserIp {
  my ($wbperson, $submitter_email) = @_;
  my $ip = &getIp();
  my $twonum = $wbperson; $twonum =~ s/WBPerson/two/;
  $result = $dbh->do( "DELETE FROM two_user_ip WHERE two_user_ip = '$ip' ;" );
  $result = $dbh->do( "INSERT INTO two_user_ip VALUES ('$twonum', '$ip', '$submitter_email')" ); 
} # sub updateUserIp

sub getUserByIp {
  my $ip = &getIp();
  my $twonum = ''; my $standardname = ''; my $email = ''; my $wbperson = '';
  $result = $dbh->prepare( "SELECT * FROM two_user_ip WHERE two_user_ip = '$ip';" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $twonum = $row[0]; $email = $row[2]; $wbperson = $row[0]; $wbperson =~ s/two/WBPerson/; }
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$twonum';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[2]) { $standardname = $row[2]; }
  return ($wbperson, $standardname, $email);
} # sub getUserByIp

sub mailSendmail {
  my ($user, $email, $subject, $body, $cc) = @_;
  my %mail;
  $mail{from}           = $user;
  $mail{to}             = $email;
  $mail{cc}             = $cc;
  $mail{subject}        = $subject;
  $mail{body}           = $body;
  $mail{'content-type'} = 'text/html; charset="iso-8859-1"';
# UNCOMMENT TO SEND EMAIL
  sendmail(%mail) || print qq(<span style="color:red">Error, confirmation email failed</span> : $Mail::Sendmail::error<br/>\n);
} # sub mailSendmail

