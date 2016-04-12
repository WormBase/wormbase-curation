#!/usr/bin/perl 

# phenotype.cgi - redirect to that page.

use strict;
use CGI;

my $q = new CGI;

print $q->redirect( "http://www.wormbase.org/submissions/phenotype.cgi" );	# 2016 02 09


__END__

# Form to submit allele-phenotype

# need to rewrite this for allele-phenotype
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

my $title = 'Allele Phenotype form';
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
  print qq(Thank you. This WormBase allele-phenotype submission has been flagged for removal.<br/>);
  ($var, my $ip)     = &getHtmlVar($query, 'ipAddress');
  ($var, my $pgids)  = &getHtmlVar($query, 'pgids');
  my $user        = 'allele_phenotype_form@' . $hostfqdn;	# who sends mail
  my $email = 'cgrove@caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
#   my $email = 'closertothewake@gmail.com';
  my $subject = 'Alelle-Phenotype unauthorized submission';		# subject of mail
  my $body = qq(Unauthorized or retracted submission from $ip with pgids $pgids); 
# UNCOMMENT send chris emails
  &mailSendmail($user, $email, $subject, $body);
  print $footer;
} # sub bogusSubmission

sub emailFlagFirstpass {
  print "Content-type: text/html\n\n";
  print $header;
  my ($var, $wbperson)     = &getHtmlVar($query, 'wbperson');	# WBPerson ID
  my ($var, $wbpaper)      = &getHtmlVar($query, 'wbpaper');	# WBPaper ID
  my $user        = 'allele_phenotype_form@' . $hostfqdn;	# who sends mail
  my $email       = 'cgrove@caltech.edu';
#   my $email       = 'closertothewake@gmail.com';
  my $subject     = qq(Allele-Phenotype Form: Flag $wbpaper by $wbperson);
  print "Thank you for flagging $wbpaper for allele-phenotype curation.<br/>\n";
# UNCOMMENT send chris emails
  &mailSendmail($user, $email, $subject, $subject);
  print $footer;
} # sub emailFlagFirstpass

sub personPublication {
  print "Content-type: text/html\n\n";
  print $header;
  my %flaggedPapers;
  my $curStatusUrl = 'http://' . $hostfqdn . "/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=newmutant&method=any%20pos%20ncur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on";
#   print qq(URL $curStatusUrl URL);
  my $curStatusData = get $curStatusUrl;
  my ($curStatusJoinkeys) = $curStatusData =~ m/name="specific_papers">(.*?)<\/textarea/;
  my (@paps) = split/\s+/, $curStatusJoinkeys; foreach (@paps) { $flaggedPapers{"WBPaper$_"}++; }
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
  $result = $dbh->prepare( "SELECT * FROM pap_author_verified WHERE author_id IN ('$aids_possible');" );
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
  my %hasVariation; my %hasWBCurator; my %hasComCurator;
  $result = $dbh->prepare( "SELECT * FROM app_paper WHERE app_paper IN ('$paps') AND joinkey IN (SELECT joinkey FROM app_variation);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasVariation{$row[0]} = $row[1]; }
  my $pgidHasVariation = join"','", sort keys %hasVariation;
  $result = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN ('$pgidHasVariation') AND app_curator = 'WBPerson29819' AND joinkey NOT IN (SELECT joinkey FROM app_needsreview);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasComCurator{$hasVariation{$row[0]}}++; }
  $result = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN ('$pgidHasVariation') AND app_curator != 'WBPerson29819';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hasWBCurator{$hasVariation{$row[0]}}++; }

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

    my $label   = qq(<a href='allele_phenotype.cgi?action=showStart&input_1_pmid=$pmid&input_1_person=$personName&termid_1_person=$personId&input_1_email=$personEmail' target='_blank' style='font-weight: bold; text-decoration: underline;'>Needs curation</a>);
    if ($flaggedPapers{$paper})      { $relevant = 'relevant'; }	# flagged papers are relevant
      elsif ($hasWBCurator{$paper})  { $relevant = 'relevant'; }	# wormbase curated papers are relevant
      elsif ($hasComCurator{$paper}) { $relevant = 'relevant'; }	# user curated papers are relevant
      else {	# not flagged, give link to this form to email Chris that the paper should be flagged
        $label   = qq(<a href='allele_phenotype.cgi?action=emailFlagFirstpass&wbpaper=$paper&wbperson=$personId' target='_blank' style='font-weight: bold; text-decoration: underline;'>flag this for allele-phenotype data</a>); }
    my $urlPreexisting  = 'http://' . $hostfqdn .  "/~azurebrd/cgi-bin/forms/allele_phenotype.cgi?action=preexistingData&wbpaper=$paper";
    if ($hasWBCurator{$paper}) {       $label = qq(<a href='$urlPreexisting' target='_blank' style='font-weight: bold; text-decoration: underline;'>WormBase curated</a>);     }
      elsif ($hasComCurator{$paper}) { $label = qq(<a href='$urlPreexisting' target='_blank' style='font-weight: bold; text-decoration: underline;'>Curation in progress</a>); }
    $tr .= qq(<td style='width: 120px;'>$label</td>);
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
    print qq(<a href="#relevant">$countRelevant papers flagged likely to have allele-phenotype data</a><br/>\n);
    print qq(<a href="#not_relevant">$countNotrelevant papers NOT flagged for allele-phenotype data</a><br/><br/><br/>\n); }

  print qq(<a name="relevant">$countRelevant papers flagged likely to have allele-phenotype data</a><br/>\n);
  print qq(<table border="1" cellpadding="5">);
  print qq(<th>Curation Status</th><th>PubMed ID</th><th>WBPaper ID</th><th>DOI</th><th>Title</th><th>Journal</th><th>Year</th><th>Authors</th>);
  foreach my $tr (@{ $trs{'relevant'} }) { print $tr; }
  print qq(</table><br/><br/>);

  print qq(<a name="not_relevant">$countNotrelevant papers NOT flagged for allele-phenotype data</a><br/>\n);
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
  my @tables = qw( variation curator communitycurator term not phen_remark nature func penetrance heat_sens cold_sens );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM app_$table WHERE joinkey IN ('$joinkeys') AND joinkey NOT IN (SELECT joinkey FROM app_needsreview);" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $pedata{$row[0]}{$table} = $row[1]; }
  } # foreach my $table (@tables)
  my %mapToNames;
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
  foreach my $pgid (sort {$a<=>$b} keys %pedata) { 
    my @data = ();
#     push @data, $pgid;
    my ($curId, $curName, $varId, $allele, $phObsId, $phObsNa, $phNotId, $phNotNa, $phenRemark, $nature, $func, $penetrance, $cold, $heat) = ('', '', '', '', '', '', '', '', '', '', '', '', '', ''); 
    if ($pedata{$pgid}{curator}) {  
      $curId = $pedata{$pgid}{curator}; my $curatorType = 'WormBase Curator'; 
      if ($curId eq 'WBPerson29819') {     $curId   = $pedata{$pgid}{communitycurator};   $curatorType = 'Community Curator'; }
      if ($mapToNames{'person'}{$curId}) { $curName = qq($curatorType - $mapToNames{'person'}{$curId}); }  }
    push @data, qq($curName);
    if ($pedata{$pgid}{variation}) {  
      $varId = $pedata{$pgid}{variation};
      if ($mapToNames{'variation'}{$varId}) { $allele = $mapToNames{'variation'}{$varId}; } }
    push @data, $allele;
    my $phenSort = 1; my $phenName = '';
    if ($pedata{$pgid}{term}) {  
      my $phenId = $pedata{$pgid}{term};
      if ($mapToNames{'phenotype'}{$phenId}) { $phenName = $mapToNames{'phenotype'}{$phenId}; }
      if ($pedata{$pgid}{not}) { $phNotNa = $phenName; $phNotId = $phenId; $phenSort = 2; }
        else { $phObsNa = $phenName; $phObsId = $phenId; } }
    push @data, $phObsNa; push @data, $phNotNa;
    if ($pedata{$pgid}{phen_remark}) {  
      $phenRemark = $pedata{$pgid}{phen_remark}; }
    push @data, $phenRemark;
    if ($pedata{$pgid}{nature}) {  
      $nature = $pedata{$pgid}{nature};
      if ($dropdown{allelenature}{$nature}) { $nature = $dropdown{allelenature}{$nature}; } }
    push @data, $nature;
    if ($pedata{$pgid}{func}) {  
      $func = $pedata{$pgid}{func};
      if ($dropdown{allelefunction}{$func}) { $func = $dropdown{allelefunction}{$func}; } }
    push @data, $func;
    if ($pedata{$pgid}{penetrance}) {  
      $penetrance = $pedata{$pgid}{penetrance};
      if ($dropdown{penetrance}{$penetrance}) { $penetrance = $dropdown{penetrance}{$penetrance}; } }
    push @data, $penetrance;
    if ($pedata{$pgid}{heat_sens}) { $heat = $pedata{$pgid}{heat_sens}; }
    push @data, $heat;
    if ($pedata{$pgid}{cold_sens}) { $cold = $pedata{$pgid}{cold_sens}; }
    push @data, $cold;
    my $trData = join"</td><td $tdstyle>", @data;
    $trData = qq(<tr><td $tdstyle>$trData</td></tr>);
    push @{ $sortFilter{$allele}{$phenSort}{$phenName} }, $trData;
  } # foreach my $pgid (sort {$a<=>$b} keys %pedata)
  print qq(<table border="1">);
  my @headers = ( 'Curator', 'Allele', 'Observed Phenotype', "<span style='color: red;'>Not</span> Observed Phenotype", 'Phenotype Remark', 'Inheritance Pattern', 'Mutation Effect', 'Penetrance', 'Heat Sensitive', 'Cold Sensitive');
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
  $result = $dbh->prepare( "SELECT app_variation.app_variation, app_term.app_term FROM app_variation, app_term WHERE app_variation.joinkey = app_term.joinkey AND app_term.joinkey IN (SELECT joinkey FROM app_paper WHERE app_paper = '$wbpaper') AND app_term.joinkey NOT IN (SELECT joinkey FROM app_needsreview);" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { 
    my $url = 'http://' . $hostfqdn . "/~azurebrd/cgi-bin/forms/allele_phenotype.cgi?action=preexistingData&wbpaper=$wbpaper";
    $checkResults = qq(<span style='color: brown'>Notice: The paper you have entered has already been curated for some allele-phenotype data. Please refer to the <a href='$url' target='new' style='font-weight: bold; text-decoration: underline;'>allele-phenotype data summary</a> for this paper. If you believe you have additional phenotype data for this paper, please proceed.</span>); }
  return $checkResults;
} # sub checkPmid

sub asyncFieldCheck {
  print "Content-type: text/plain\n\n";
  ($var, my $field)   = &getHtmlVar($query, 'field');
  ($var, my $input)   = &getHtmlVar($query, 'input');
  my $checkResults = 'ok';
  if ($field eq 'allele') {      ($checkResults) = &checkAllele($input); }
    elsif ($field eq 'pmid') {   ($checkResults) = &checkPmid($input);   }
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
      if ($data_line =~ /id : <\/span> WBPhenotype:\d+/) { $data_line =~ s/(WBPhenotype:\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/all\/phenotype\/${1}#036--10\" target=\"new\">$1<\/a>/; }
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

#   elsif ($ontology_type eq 'WBGene') {               ($matches) = &getAnyWBGeneTermInfo($userValue); }
#   elsif ($ontology_type eq 'WBTransgene') {       ($matches) = &getAnyWBTransgeneTermInfo($userValue); }

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
#   $to_print = qq(Click <a href="http://www.wormbase.org/resources/person/${person_id}#03--10" target="new" style="font-weight: bold; text-decoration: underline;">here</a> to review your publications and see which are in need of allele-phenotype curation<br/>\n) . $to_print;
  $to_print = qq(Click <a href="allele_phenotype.cgi?action=personPublication&personId=${person_id}&personName=${standard_name}&personEmail=${first_email}" target="new" style="font-weight: bold; text-decoration: underline;">here</a> to review your publications and see which are in need of allele-phenotype curation<br/>\n) . $to_print;

#   ($var, $personId)      = &getHtmlVar($query, 'personId');		# WBPerson ID
#   ($var, $personName)    = &getHtmlVar($query, 'personName');		# WBPerson Name
#   ($var, $personEmail)   = &getHtmlVar($query, 'personEmail');		# email address
  return $to_print;
} # sub getAnyWBPersonTermInfo

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
#   elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneAutocomplete($words);      }
#   elsif ($ontology_type eq 'WBTransgene') {     ($matches) = &getAnyWBTransgeneAutocomplete($words); }

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



sub showStart {
  print "Content-type: text/html\n\n";
  print $header;
#   print qq(<span style="font-size: 24pt; text-decoration: underline;">Allele-Phenotype Form</span><br/><br/>\n);
#   print qq(<span>Welcome to the WormBase Allele-Phenotype form!<br/>We would greatly appreciate any allele-phenotype data that you have for us.<br/>Please fill out the form below.<br/>If you have any questions, please do not hesitate to contact WormBase at <a href="mailto:help\@wormbase.org">help\@wormbase.org</a></span><br/><br/>\n);
  print qq(<span style="font-size: 24pt;">Contribute allele-phenotype connections</span><br/><br/>\n);
  print qq(<span>We would appreciate your help in adding phenotype data from published papers to WormBase.<br/>Please fill out the form below. <b>Watch a short video tutorial <a style='font-weight: bold; text-decoration: underline;' href="https://www.youtube.com/watch?v=_gd87S1h3zg&feature=youtu.be" target="_blank">here</a> or read the user guide <a style='font-weight: bold; text-decoration: underline;' href="http://wiki.wormbase.org/index.php/Contributing_Allele_Phenotype_Connections" target="_blank">here</a></b>.<br/>If you would prefer to fill out a spreadsheet with this information, please download and fill out our<br/><a href="https://dl.dropboxusercontent.com/u/4290782/WormBase_Allele-Phenotype_Worksheet.xlsx" target="_blank">WormBase Allele-Phenotype Worksheet</a> and e-mail as an attachment to <a href="mailto:curation\@wormbase.org">curation\@wormbase.org</a><br/>If you have any questions, please do not hesitate to contact WormBase at <a href="mailto:help\@wormbase.org">help\@wormbase.org</a></span><br/><br/>\n);
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
  $td .= qq(<option value=""></option>);
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
  $table_to_print .= qq(<input id="input_${i}_$field" name="input_${i}_$field" style="width: 97%; background-color: #E1F1FF;" $placeholder value="$inputvalue">\n);
  $table_to_print .= qq(<div id="container_bigtext_${i}_$field"><textarea id="textarea_bigtext_${i}_$field" rows="$rows_size" cols="$cols_size" style="display:none">$inputvalue</textarea></div>\n);
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
  my ($i, $field) = @_; my $toReturn = '';
  if ($fields{$field}{type} eq 'checkbox') {
    my $checked = '';
    if ($fields{$field}{inputvalue}{$i} eq $fields{$field}{label}) { $checked = qq(checked="checked"); }
    $toReturn = qq(&nbsp;&nbsp;<input type="checkbox" id="input_${i}_$field" name="input_${i}_$field" value="$fields{$field}{label}" $checked>&nbsp; $fields{$field}{label}<br/>\n); }
  return $toReturn;
} # sub printEditorCheckbox

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
      $warningvalue = qq(Click <a href='allele_phenotype.cgi?action=personPublication&personId=${person_id}&personName=${person_name}&personEmail=${person_email}' target='new' style='font-weight: bold; text-decoration: underline;'>here</a> to review your publications and see which are in need of allele-phenotype curation<br/>\n); } }
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
    $header_with_javascript = qq(<span id="optional_down_span" style="display: none;" onmouseover="this.style.cursor='pointer';" onclick="document.getElementById('optional_down_span').style.display='none'; document.getElementById('optional_right_span').style.display=''; document.getElementById('group_1_allelenature').style.display='none'; document.getElementById('group_1_allelefunction').style.display='none'; document.getElementById('group_1_penetrance').style.display='none'; document.getElementById('group_1_tempsens').style.display='none'; document.getElementById('group_1_comment').style.display='none'; document.getElementById('group_1_linkotherform').style.display='none'; document.getElementById('group_1_optionalexplain').style.display='none';" ><div id="optional_down_image" style="background-position: -40px 0; background-image: url('../../images/triangle_down_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_down_image').style.backgroundImage='url(../../images/triangle_down_reversed.png)';" onmouseout="document.getElementById('optional_down_image').style.backgroundImage='url(../../images/triangle_down_plain.png)';"></div>$header</span>);
    $header_with_javascript .= qq(<span id="optional_right_span" onmouseover="this.style.cursor='pointer';" onclick="document.getElementById('optional_down_span').style.display=''; document.getElementById('optional_right_span').style.display='none'; document.getElementById('group_1_allelenature').style.display=''; document.getElementById('group_1_allelefunction').style.display=''; document.getElementById('group_1_penetrance').style.display=''; document.getElementById('group_1_tempsens').style.display=''; document.getElementById('group_1_comment').style.display=''; document.getElementById('group_1_linkotherform').style.display=''; document.getElementById('group_1_optionalexplain').style.display='';" ><div id="optional_right_image" style="background-position: -40px 0; background-image: url('../../images/triangle_right_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_right_image').style.backgroundImage='url(../../images/triangle_right_reversed.png)';" onmouseout="document.getElementById('optional_right_image').style.backgroundImage='url(../../images/triangle_right_plain.png)';"></div>$header</span>);
#     print qq(<div id="optional_down_image" style="display: none; background-position: -40px 0; background-image: url('../../images/triangle_down_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_down_image').style.backgroundImage='url(../../images/triangle_down_reversed.png)';" onmouseout="document.getElementById('optional_down_image').style.backgroundImage='url(../../images/triangle_down_plain.png)';" onclick="document.getElementById('optional_down_image').style.display='none'; document.getElementById('optional_right_image').style.display=''; document.getElementById('group_1_allelenature').style.display='none'; document.getElementById('group_1_allelefunction').style.display='none'; document.getElementById('group_1_penetrance').style.display='none'; document.getElementById('group_1_tempsens').style.display='none'; document.getElementById('group_1_comment').style.display='none'; document.getElementById('group_1_linkotherform').style.display='none'; document.getElementById('group_1_optionalexplain').style.display='none';" ></div>);
#     print qq(<div id="optional_right_image" style="background-position: -40px 0; background-image: url('../../images/triangle_right_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_right_image').style.backgroundImage='url(../../images/triangle_right_reversed.png)';" onmouseout="document.getElementById('optional_right_image').style.backgroundImage='url(../../images/triangle_right_plain.png)';" onclick="document.getElementById('optional_down_image').style.display=''; document.getElementById('optional_right_image').style.display='none'; document.getElementById('group_1_allelenature').style.display=''; document.getElementById('group_1_allelefunction').style.display=''; document.getElementById('group_1_penetrance').style.display=''; document.getElementById('group_1_tempsens').style.display=''; document.getElementById('group_1_comment').style.display=''; document.getElementById('group_1_linkotherform').style.display=''; document.getElementById('group_1_optionalexplain').style.display='';" ></div>);
#     print qq(<img id="optional_down_image" style="display: none; height: 20px; width: 20px;" src="../../images/triangle_down_plain.png" onmouseover="document.getElementById('optional_down_image').src='../../images/triangle_down_reversed.png';" onmouseout="document.getElementById('optional_down_image').src='../../images/triangle_down_plain.png';" onclick="document.getElementById('optional_down_image').style.display='none'; document.getElementById('optional_right_image').style.display=''; document.getElementById('group_1_allelenature').style.display='none'; document.getElementById('group_1_allelefunction').style.display='none'; document.getElementById('group_1_penetrance').style.display='none'; document.getElementById('group_1_tempsens').style.display='none';">);
#     print qq(<img id="optional_right_image" style="height: 20px; width: 20px;" src="../../images/triangle_right_plain.png" onmouseover="document.getElementById('optional_right_image').src='../../images/triangle_right_reversed.png';" onmouseout="document.getElementById('optional_right_image').src='../../images/triangle_right_plain.png';" onclick="document.getElementById('optional_down_image').style.display=''; document.getElementById('optional_right_image').style.display='none'; document.getElementById('group_1_allelenature').style.display=''; document.getElementById('group_1_allelefunction').style.display=''; document.getElementById('group_1_penetrance').style.display=''; document.getElementById('group_1_tempsens').style.display='';">);
  } # if ($header eq 'Optional')
  my $message_span = '';
  if ($message) { $message_span = qq(<span style="color: $message_colour; font-size: $message_fontsize;">$message</span>); }
  print qq(<span id="header_$header">$header_with_javascript $message_span<span>);
  print qq(</td></tr>\n);
} # sub printTrHeader

sub printPersonField {         printArrayEditorNested('person'); }
sub printEmailField {          printArrayEditorNested('email');  }
sub printPmidField {           printArrayEditorNested('pmid');   }
sub printAlleleField {         printArrayEditorNested('allele'); }
sub printObsPhenotypeField {   printArrayEditorNested('obsphenotype', 'obsphenremark'); }
sub printNotPhenotypeField {   printArrayEditorNested('notphenotype', 'notphenremark'); }
sub printObsSuggestField {     printArrayEditorNested('obssuggested', 'obssugdef', 'obssugphenremark'); }
sub printNotSuggestField {     printArrayEditorNested('notsuggested', 'notsugdef', 'notsugphenremark'); }
sub printAlleleNatureField {   printArrayEditorNested('allelenature');   }
sub printAlleleFunctionField { printArrayEditorNested('allelefunction'); }
sub printPenetranceField {     printArrayEditorNested('penetrance');     }
sub printCommentField {        printArrayEditorNested('comment');        }
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
  $trToPrint   .= &printEditorCheckbox(1, 'heatsens');
  $trToPrint   .= &printEditorCheckbox(1, 'coldsens');
  $trToPrint   .= qq(</td>);
  $trToPrint   .= qq(</tr>\n);
  print $trToPrint;
} # sub printTempSensField
sub printLinkToOtherForm {
  print qq(<tr id="group_1_linkotherform" style="display: none;"><td colspan="7">If you would like to submit molecular details for an allele, please do so <a href="http://${hostfqdn}/~azurebrd/cgi-bin/forms/allele_sequence.cgi" target="new" style="font-weight: bold; text-decoration: underline;">here</a></td><tr>); }
sub printOptionalExplanation {
  print qq(<tr id="group_1_optionalexplain" style="display: none;"><td colspan="7">Please note: The following values apply to the selected allele for ALL OBSERVED PHENOTYPES selected above.</td><tr>); }


sub printPhenontLink {
#   my $labelTdStyle   = qq(style="border-style: solid; border-color: #000000; color: grey; font-size: 10px;");
  my $labelTdStyle   = qq(style="color: grey; font-size: 10px;");
#   print qq(<tr><td></td><td $labelTdStyle>&nbsp;<a href="http://www.wormbase.org/tools/ontology_browser" target="new" style="font-weight: bold; text-decoration: underline;">Browse the Phenotype Ontology</a></td></tr>\n);
#   print qq(<tr><td></td><td $labelTdStyle>&nbsp;<a href="http://juancarlos.wormbase.org/tools/ontology_browser#phenotype" target="new" style="font-weight: bold; text-decoration: underline;">Browse the Phenotype Ontology</a></td></tr>\n);
  print qq(<tr><td></td><td colspan="2" $labelTdStyle>&nbsp;<a href="http://www.wormbase.org/tools/ontology_browser" target="new" style="font-weight: bold; text-decoration: underline;">Browse the Phenotype Ontology</a></td></tr>\n); }
sub printShowObsSuggestLink {
#   my $labelTdStyle   = qq(style="border-style: solid; border-color: #000000; color: grey; font-size: 10px;");
  my $labelTdStyle   = qq(style="color: grey; font-size: 10px;");
#   print qq(<tr id="showObsSuggestTr"><td></td><td $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_obssuggested').style.display = ''; document.getElementById('showObsSuggestTr').style.display = 'none';"</td></tr>\n);
  print qq(<tr id="showObsSuggestTr"><td></td><td colspan="2" $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_obssuggested').style.display = ''; document.getElementById('group_1_obssugdef').style.display = ''; document.getElementById('group_1_obssugphenremark').style.display = ''; document.getElementById('showObsSuggestTr').style.display = 'none';"</td></tr>\n); }
sub printShowNotSuggestLink {
#   my $labelTdStyle   = qq(style="border-style: solid; border-color: #000000; color: grey; font-size: 10px;");
  my $labelTdStyle   = qq(style="color: grey; font-size: 10px;");
#   print qq(<tr id="showNotSuggestTr"><td></td><td $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_notsuggested').style.display = ''; document.getElementById('showNotSuggestTr').style.display = 'none';"</td></tr>\n);
  print qq(<tr id="showNotSuggestTr"><td></td><td colspan="2" $labelTdStyle>&nbsp;Can't find your Phenotype? &nbsp;<input type="checkbox" onclick="document.getElementById('group_1_notsuggested').style.display = ''; document.getElementById('group_1_notsugdef').style.display = ''; document.getElementById('group_1_notsugphenremark').style.display = ''; document.getElementById('showNotSuggestTr').style.display = 'none';"</td></tr>\n); }

# Can't find your phenotype (please enter a description of your phenotype)
#   two separate boxes, one for suggested term + one for suggested definition.  allow N pairs.  put those in app_suggested + app_suggested_definition

sub showForm {
  my $ip            = $query->remote_host();			# get value for current user IP, not (potentially) loaded IP 
  return if ($ip eq '46.161.41.199');			# spammed 2015 09 01
  print qq(<form method="post" action="allele_phenotype.cgi" enctype="multipart/form-data">);
  print qq(<div id="term_info_box" style="border: solid; position: fixed; top: 95px; right: 20px; width: 350px; z-index:2; background-color: white;">\n);
#   print qq(<div id="clear_term_info" style="position: fixed; z-index: 3; top: 102px; right: 30px";>&#10008;</div>\n);
#   print qq(<div id="clear_term_info" align="right" onclick="document.getElementById('term_info').innerHTML = '';">clear &#10008;</div>\n);
#   print qq(<div id="clear_term_info" align="right" onclick="document.getElementById('term_info').innerHTML = '';"><img id="close_term_info_image" src="../../images/x_plain.png" onmouseover="document.getElementById('close_term_info_image').src='../../images/x_reversed.png';" onmouseout="document.getElementById('close_term_info_image').src='../../images/x_plain.png';"></div>\n);
  print qq(<div id="clear_term_info" align="right" onclick="document.getElementById('term_info_box').style.display = 'none';"><img id="close_term_info_image" src="../../images/x_plain.png" onmouseover="document.getElementById('close_term_info_image').src='../../images/x_reversed.png';" onmouseout="document.getElementById('close_term_info_image').src='../../images/x_plain.png';"></div>\n);
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
  &printAlleleField();
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
  &printTrHeader('Optional', '20', '18px', "(inheritance pattern, mutation effect, penetrance, temperature sensitivity and general comments)", '#aaaaaa', '12px');
  &printOptionalExplanation();
  &printAlleleNatureField();
  &printAlleleFunctionField();
  &printPenetranceField();
  &printTempSensField();
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
      if ($inputvalue) { push @inputtermidvalue, $inputvalue; }
      if ($termidvalue) { push @inputtermidvalue, $termidvalue; }
      my $inputtermidvalue = join" -- ", @inputtermidvalue; 
      if ($label) { $trData .= qq(<td>$label</td><td>$inputtermidvalue</td>\n); }
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
  print qq(<span style="font-size: 24pt;">Contribute allele-phenotype connections</span><br/><br/>\n);

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
    
  my $form_data  = qq(<table border="1" cellpadding="5">);
  $form_data    .= &tableDisplayArray('person'); 
  $form_data    .= &tableDisplayArray('email');  
  $form_data    .= &tableDisplayArray('pmid');   
  $form_data    .= &tableDisplayArray('allele'); 
  $form_data    .= &tableDisplayArray('obsphenotype', 'obsphenremark');
  $form_data    .= &tableDisplayArray('notphenotype', 'notphenremark');
  $form_data    .= &tableDisplayArray('obssuggested', 'obssugdef', 'obssugphenremark');
  $form_data    .= &tableDisplayArray('notsuggested', 'notsugdef', 'notsugphenremark');
  $form_data    .= &tableDisplayArray('allelenature'); 
  $form_data    .= &tableDisplayArray('allelefunction'); 
  $form_data    .= &tableDisplayArray('penetrance');
  $form_data    .= &tableDisplayArray('heatsens');
  $form_data    .= &tableDisplayArray('coldsens');
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
#           $form_data = qq(Dear $fields{person}{inputvalue}{1}, thank you for submitting Allele-Phenotype data.<br/>A WormBase curator will be in touch if there are any questions<br/><br/>) . $form_data;			# prepend thank you message
          my $messageToUser = qq(Dear $fields{person}{inputvalue}{1}, thank you for submitting Allele-Phenotype data.<br/>A WormBase curator will be in touch if there are any questions.<br/>);
          print qq($messageToUser<br/>);
          print qq(<br/>$form_data);
          print qq(<br/>Return to the <a href="allele_phenotype.cgi">Allele-Phenotype Form</a>.<br/>\n);
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
  my ($paperHist, $alleleHist) = ('', '');
  my $ip            = $query->remote_host();			# get value for current user IP, not (potentially) loaded IP 
  my $timestamp     = &getPgDate();
  my $emailMaryann  = ''; my $emailKimberly = '';
  my @newPgids      = ();
  my $pgid          = &getHighestPgid(); 
  my $nodump        = 'NO DUMP';
  my $needsreview   = 'Needs Review';
  my $curator       = 'WBPerson29819';
  my $person        = $fields{person}{termidvalue}{1};
  my $personName    = $fields{person}{inputvalue}{1};
  my $email         = $fields{email}{inputvalue}{1};
  my $pmid          = $fields{pmid}{inputvalue}{1};
  if ($pmid =~ m/^\s+/) { $pmid =~ s/^\s+//; }
  if ($pmid =~ m/\s+$/) { $pmid =~ s/\s+$//; }
  if ($pmid =~ m/^pmid:?(\d+)/i) { $pmid = $1; }
#   if ($pmid) { if ($pmid =~ m/(\d+)/) { ($pmid) = $1; } }	# get just the pmid digits for the match and to store if unrecognized
  my $wbpaper       = ''; my $unregpaper = $pmid;
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier = 'pmid$pmid';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { $wbpaper = 'WBPaper' . $row[0]; $unregpaper = ''; }
  if ($wbpaper) {      $paperHist = "$pmid ($wbpaper)"; } 
    else {             $paperHist = "$pmid (no match)"; }
  if ($unregpaper) { $emailKimberly .= qq(PMID "$unregpaper" is new.\n); }
  my $unregallele   = $fields{allele}{inputvalue}{1};
  my $variation     = $fields{allele}{termidvalue}{1} || '';
  my $alleleHist    = '';
  if ($variation) {    $alleleHist = "$unregallele ($variation)"; $unregallele = ''; }
    else {             $alleleHist = "$unregallele (no match)";   $emailMaryann .= qq(Allele "$unregallele" is new.\n); }
  my $nature        = $fields{allelenature}{inputvalue}{1} || '';
  my $func          = $fields{allelefunction}{inputvalue}{1} || '';
  my $penetrance    = $fields{penetrance}{inputvalue}{1} || '';
  my $comment       = $fields{comment}{inputvalue}{1} || '';
  my $heat_sens     = $fields{heatsens}{inputvalue}{1} || '';
  my $cold_sens     = $fields{coldsens}{inputvalue}{1} || '';
  my @historyAppend = ();

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
  my $amountObs   = $fields{obsphenotype}{multi};
  for my $i (1 .. $amountObs) {
    my $obsphenotypeValue  = $fields{'obsphenotype'}{termidvalue}{$i};
    my $obsphenotypeName   = $fields{'obsphenotype'}{inputvalue}{$i};
    my $obsphenremarkValue = $fields{'obsphenremark'}{inputvalue}{$i};
    if ($obsphenotypeValue) {
      $pgid++; push @newPgids, $pgid;
      my $obssugdefValue     = ''; my $not = '';
      push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgid\t$paperHist\t$alleleHist\t$obsphenotypeName ($obsphenotypeValue)\t$not\t$obsphenremarkValue\t$obssugdefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
      &writePgRowFields($pgid, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
      &writePgField($pgid, 'term', $obsphenotypeValue);
      &writePgField($pgid, 'phen_remark', $obsphenremarkValue); } }
  my $amountNot   = $fields{notphenotype}{multi};
  for my $i (1 .. $amountNot) {
    my $notphenotypeValue  = $fields{'notphenotype'}{termidvalue}{$i};
    my $notphenotypeName   = $fields{'notphenotype'}{inputvalue}{$i};
    my $notphenremarkValue = $fields{'notphenremark'}{inputvalue}{$i};
    if ($notphenotypeValue) {
      $pgid++; push @newPgids, $pgid;
      my $notsugdefValue     = ''; my $not = 'NOT';
      push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgid\t$paperHist\t$alleleHist\t$notphenotypeName ($notphenotypeValue)\t$not\t$notphenremarkValue\t$notsugdefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
      &writePgRowFields($pgid, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
      &writePgField($pgid, 'term', $notphenotypeValue);
      &writePgField($pgid, 'not', 'NOT');
      &writePgField($pgid, 'phen_remark', $notphenremarkValue); } }
  my $amountObsSug   = $fields{obssuggested}{multi};
  for my $i (1 .. $amountObsSug) {
    my $obssuggestedValue     = $fields{'obssuggested'}{inputvalue}{$i};
    my $obssugdefValue        = $fields{'obssugdef'}{inputvalue}{$i};
    my $obssugphenremarkValue = $fields{'obssugphenremark'}{inputvalue}{$i};
    if ($obssuggestedValue) {
      $pgid++; push @newPgids, $pgid; 
      my $not = '';
      push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgid\t$paperHist\t$alleleHist\t$obssuggestedValue (no match)\t$not\t$obssugphenremarkValue\t$obssugdefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
      &writePgRowFields($pgid, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
      &writePgField($pgid, 'suggested', $obssuggestedValue);
      &writePgField($pgid, 'suggested_definition', $obssugdefValue);
      &writePgField($pgid, 'phen_remark', $obssugphenremarkValue); } }
  my $amountNotSug   = $fields{obssuggested}{multi};
  for my $i (1 .. $amountNotSug) {
    my $notsuggestedValue     = $fields{'notsuggested'}{inputvalue}{$i};
    my $notsugdefValue        = $fields{'notsugdef'}{inputvalue}{$i};
    my $notsugphenremarkValue = $fields{'notsugphenremark'}{inputvalue}{$i};
    if ($notsuggestedValue) {
      $pgid++; push @newPgids, $pgid;
      my $not = 'NOT';
      push @historyAppend, qq($ip\t$timestamp\t$person ($personName)\t$email\t$pgid\t$paperHist\t$alleleHist\t$notsuggestedValue (no match)\t$not\t$notsugphenremarkValue\t$notsugdefValue\t$nature\t$func\t$penetrance\t$heat_sens\t$cold_sens\t$comment);
      &writePgRowFields($pgid, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment);
      &writePgField($pgid, 'not', 'NOT');
      &writePgField($pgid, 'suggested', $notsuggestedValue);
      &writePgField($pgid, 'suggested_definition', $notsugdefValue);
      &writePgField($pgid, 'phen_remark', $notsugphenremarkValue); } }
  my $newPgids = join",", @newPgids;

  my $user = 'allele_phenotype_form@' . $hostfqdn;	# who sends mail
  if ($emailKimberly) {
    my $email       = 'cgrove@caltech.edu, vanauken@caltech.edu';
#     my $email       = 'closertothewake@gmail.com';
    my $subject     = qq(Allele-Phenotype Form: Unregistered paper alert);
    $emailKimberly .= qq(New PGIDs in allele-phenotype OA $newPgids\n);
#     print "Email Kimberly $emailKimberly<br/>\n";
# UNCOMMENT send kimberly emails
    &mailSendmail($user, $email, $subject, $emailKimberly);
  }
  if ($emailMaryann) {
    my $email      = 'cgrove@caltech.edu, maryann.tuli@wormbase.org';
#     my $email      = 'closertothewake@gmail.com';
    my $subject    = qq(Allele-Phenotype Form: Unregistered variation alert);
    $emailMaryann .= qq(New PGIDs in allele-phenotype OA $newPgids\n);
#     print "Email Mary Ann $emailMaryann<br/>\n";
# UNCOMMENT send kimberly emails
    &mailSendmail($user, $email, $subject, $emailMaryann);
  }
  my $cc = 'cgrove@caltech.edu, kyook@caltech.edu, garys@caltech.edu';
#   my $email = 'cgrove@caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
#   my $email = 'closertothewake@gmail.com';
#   $email   .= ", $fields{email}{inputvalue}{1}";
  my $email   = "$fields{email}{inputvalue}{1}";
  my $subject = 'Allele-Phenotype confirmation';		# subject of mail
  my $body = $messageToUser;					# message to user shown on form
  $body .= qq(Click <a href='http://${hostfqdn}/~azurebrd/cgi-bin/forms/allele_phenotype.cgi?action=bogusSubmission&pgids=$newPgids&ipAddress=$ip' target='_blank' style='font-weight: bold; text-decoration: underline;'>here</a> if you did not submit this data or if you would like to retract this submission.<br/><br/>\n);	# additional link to report false data
  $body .= $form_data;						# form data
# UNCOMMENT send general emails
  &mailSendmail($user, $email, $subject, $body, $cc);

#   my $header = qq(<tr><th>ip</th><th>timestamp</th><th>person</th><th>email</th><th>pgid</th><th>paper</th><th>allele</th><th>phenotype</th><th>not</th><th>phenotype remark</th><th>suggested definition</th><th>nature</th><th>func</th><th>penetrance</th><th>heat_sens</th><th>cold_sens</th><th>comment</th></tr>\n);
  my $outfile = '/home/azurebrd/public_html/cgi-bin/data/allele_phenotype_history.html';
  open (IN, "<$outfile") or die "Cannot open $outfile : $!";
  my $toOutput = <IN>;					# stuff to beginning of data at top of file
  foreach my $line (@historyAppend) {
    $line =~ s/\t/<\/td><td>/g; 
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
  my ($pgid, $fieldTable, $fieldData) = @_;
  return unless $fieldData;
  my $pgTable = 'app_' . $fieldTable;
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

sub writePgRowFields {
  my ($pgid, $nodump, $needsreview, $curator, $person, $email, $unregpaper, $wbpaper, $unregallele, $variation, $nature, $func, $penetrance, $heat_sens, $cold_sens, $comment) = @_;
  &writePgField($pgid, 'nodump', $nodump);
  &writePgField($pgid, 'needsreview', $needsreview);
  &writePgField($pgid, 'curator', $curator);
  &writePgField($pgid, 'communitycurator', $person);
  &writePgField($pgid, 'communitycuratoremail', $email);
  &writePgField($pgid, 'unregpaper', $unregpaper);
  &writePgField($pgid, 'paper', $wbpaper);
  &writePgField($pgid, 'unregvariation', $unregallele);
  &writePgField($pgid, 'variation', $variation);
  &writePgField($pgid, 'nature', $nature);
  &writePgField($pgid, 'func', $func);
  &writePgField($pgid, 'penetrance', $penetrance);
  &writePgField($pgid, 'heat_sens', $heat_sens);
  &writePgField($pgid, 'cold_sens', $cold_sens);
  &writePgField($pgid, 'obj_remark', $comment);
} # sub writePgRowFields

sub getHighestPgid {                                    # get the highest joinkey from the primary tables
  my @highestPgidTables = qw( strain rearrangement transgene variation curator ); my $datatype = 'app';
  my $pgUnionQuery = "SELECT MAX(joinkey::integer) FROM ${datatype}_" . join" UNION SELECT MAX(joinkey::integer) FROM ${datatype}_", @highestPgidTables;
  my $result = $dbh->prepare( "SELECT max(max) FROM ( $pgUnionQuery ) AS max; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow(); my $highest = $row[0];
  return $highest;
} # sub getHighestPgid



sub checkMandatoryFields {
  my $mandatoryFail    = 0;
  my $aphenotypeExists = 0;
  foreach my $field (keys %fields) {
    if ($field eq 'person') { 
      if ($fields{$field}{termidvalue}{1}) {
          unless ($fields{$field}{termidvalue}{1} =~ m/WBPerson/) { $mandatoryFail++; print qq(<span style="color:red">FAIL</span>); } }
        else { $mandatoryFail++; print qq(<span style="color:red">FAIL</span>); }
    }
    if ($fields{$field}{'mandatory'}) { 
      unless ($fields{$field}{hasdata}) {
        $mandatoryFail++;
        print qq(<span style="color:red">$fields{$field}{label} is mandatory.</span><br/>\n); } } }
  unless ( ($fields{obsphenotype}{hasdata}) || ($fields{obssuggested}{hasdata}) || ($fields{notphenotype}{hasdata}) || ($fields{notsuggested}{hasdata}) ) {
        $mandatoryFail++;
        print qq(<span style="color:red">At least one phenotype is mandatory.</span><br/>\n); }
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
  $fields{pmid}{terminfo}                                     = qq(Enter the PubMed ID for the paper in which this phenotype data was published. If your paper does not have a PubMed ID, please enter any unique identifier, like a D.O.I. (e.g. doi 10.1038/ni.2957));
  $fields{pmid}{example}                                      = 'e.g. 4366476 (Please enter only one ID)';
  $fields{pmid}{mandatory}                                    = 'mandatory';
#   tie %{ $fields{allele}{field} }, "Tie::IxHash";
  $fields{allele}{multi}                                      = '1';
  $fields{allele}{type}                                       = 'ontology';
  $fields{allele}{label}                                      = 'Allele Name';
  $fields{allele}{freeForced}                                 = 'free';
  $fields{allele}{ontology_type}                              = 'obo';
  $fields{allele}{ontology_table}                             = 'variation';
  $fields{allele}{example}                                    = 'e.g. e1000';
  $fields{allele}{haschecks}                                  = 'allele';
  $fields{allele}{terminfo}                                   = qq(Enter the name of a single allele for which you are providing phenotype data. Once you have started typing, select an allele from the list of known alleles. If you are entering an allele not recognized by WormBase, continue with your submission and a WormBase curator will contact you to confirm the new allele.);
  $fields{allele}{matchstartonly}                             = 'matchstartonly';
  $fields{allele}{mandatory}                                  = 'mandatory';
#   tie %{ $fields{obsphenotype}{field} }, "Tie::IxHash";
  $fields{obsphenotype}{multi}                                = '10';
  $fields{obsphenotype}{type}                                 = 'ontology';
  $fields{obsphenotype}{label}                                = 'Observed Phenotype';
  $fields{obsphenotype}{ontology_type}                        = 'obo';
  $fields{obsphenotype}{ontology_table}                       = 'phenotype';
  $fields{obsphenotype}{example}                              = 'e.g. larval lethal';
  $fields{obsphenotype}{terminfo}                             = qq(For phenotypes observed with this allele, start typing and select a phenotype term from the WormBase Phenotype Ontology. If you are having trouble finding a phenotype, you may browse the phenotype ontology with the link provided. If you still cannot find a suitable phenotype term, click on the checkbox next to "Can’t find your Phenotype?" and enter your suggested term and a definition in the fields provided.);
  $fields{obsphenotype}{grouphas}                             = qq([ obsphenotype obsphenremark ]);
#   tie %{ $fields{obsphenremark}{field} }, "Tie::IxHash";
  $fields{obsphenremark}{multi}                               = '10';
  $fields{obsphenremark}{startHidden}                         = 'startHidden';
  $fields{obsphenremark}{type}                                = 'bigtext';
  $fields{obsphenremark}{label}                               = 'Phenotype Remark';
  $fields{obsphenremark}{example}                             = '(optional)';
  $fields{obsphenremark}{terminfo}                            = qq(If you would like, provide more information about the phenotype effects of this allele.);
#   tie %{ $fields{obssuggested}{field} }, "Tie::IxHash";
  $fields{obssuggested}{multi}                                = '10';
  $fields{obssuggested}{startHidden}                          = 'startHidden';
  $fields{obssuggested}{type}                                 = 'text';
  $fields{obssuggested}{label}                                = 'Suggest Observed Phenotype';
  $fields{obssuggested}{fontsize}                             = '8pt';
  $fields{obssuggested}{terminfo}                             = qq(Provide the name of a new phenotype term and a brief definition. This phenotype will be annotated to the allele you have selected.);
  $fields{obssuggested}{grouphas}                             = qq([ obssuggested obssugdef obssugphenremark ]);
#   tie %{ $fields{obssugdef}{field} }, "Tie::IxHash";
  $fields{obssugdef}{multi}                                   = '10';
  $fields{obssugdef}{type}                                    = 'bigtext';
  $fields{obssugdef}{label}                                   = 'Suggested Definition';
  $fields{obssugdef}{example}                                 = '(optional)';
  $fields{obssugdef}{terminfo}                                = qq(Provide a brief definition for the new term you entered.);
#   tie %{ $fields{obssugphenremark}{field} }, "Tie::IxHash";
  $fields{obssugphenremark}{multi}                            = '10';
  $fields{obssugphenremark}{type}                             = 'bigtext';
  $fields{obssugphenremark}{label}                            = 'Phenotype Remark';
  $fields{obssugphenremark}{example}                          = '(optional)';
  $fields{obssugphenremark}{terminfo}                         = qq(If you would like, provide more information about the phenotype effects of this allele.);
#   tie %{ $fields{notphenotype}{field} }, "Tie::IxHash";
  $fields{notphenotype}{multi}                                = '10';
  $fields{notphenremark}{startHidden}                         = 'startHidden';
  $fields{notphenotype}{type}                                 = 'ontology';
  $fields{notphenotype}{label}                                = qq(<span style='color: red;'>Not</span> Observed Phenotype);
  $fields{notphenotype}{ontology_type}                        = 'obo';
  $fields{notphenotype}{ontology_table}                       = 'phenotype';
  $fields{notphenotype}{example}                              = 'e.g. larval lethal';
  $fields{notphenotype}{terminfo}                             = qq(For phenotypes assayed for and determined not to be exhibited by this allele, start typing and select a phenotype term from the WormBase Phenotype Ontology. If you are having trouble finding your phenotype, you may browse the phenotype ontology with the link provided. If you still cannot find a suitable phenotype, click on the checkbox next to "Can’t find your Phenotype?" and enter your suggested term and a definition in the fields provided.);
  $fields{notphenotype}{grouphas}                             = qq([ notphenotype notphenremark ]);
#   tie %{ $fields{notphenremark}{field} }, "Tie::IxHash";
  $fields{notphenremark}{multi}                               = '10';
  $fields{notphenremark}{type}                                = 'bigtext';
  $fields{notphenremark}{label}                               = 'Phenotype Remark';
  $fields{notphenremark}{example}                             = '(optional)';
  $fields{notphenremark}{terminfo}                            = qq(If you would like, provide more information about the phenotype effects of this allele.);
#   tie %{ $fields{notsuggested}{field} }, "Tie::IxHash";
  $fields{notsuggested}{multi}                                = '10';
  $fields{notsuggested}{startHidden}                          = 'startHidden';
  $fields{notsuggested}{type}                                 = 'text';
  $fields{notsuggested}{label}                                = qq(Suggest <span style='color: red;'>Not</span> Observed Phenotype);
  $fields{notsuggested}{fontsize}                             = '8pt';
  $fields{notsuggested}{terminfo}                             = qq(Provide the name of a new phenotype term and a brief definition. This phenotype will be annotated to the allele you have selected.);
  $fields{notsuggested}{grouphas}                             = qq([ notsuggested notsugdef notsugphenremark ]);
#   tie %{ $fields{notsugdef}{field} }, "Tie::IxHash";
  $fields{notsugdef}{multi}                                   = '10';
  $fields{notsugdef}{type}                                    = 'bigtext';
  $fields{notsugdef}{label}                                   = 'Suggested Definition';
  $fields{notsugdef}{example}                                 = '(optional)';
  $fields{notsugdef}{terminfo}                                = qq(Provide a brief definition for the new term you entered.);
#   tie %{ $fields{notsugphenremark}{field} }, "Tie::IxHash";
  $fields{notsugphenremark}{multi}                            = '10';
  $fields{notsugphenremark}{type}                             = 'bigtext';
  $fields{notsugphenremark}{label}                            = 'Phenotype Remark';
  $fields{notsugphenremark}{example}                          = '(optional)';
  $fields{notsugphenremark}{terminfo}                         = qq(If you would like, provide more information about the phenotype effects of this allele.);
#   tie %{ $fields{allelenature}{field} }, "Tie::IxHash";
  $fields{allelenature}{multi}                                = '1';
  $fields{allelenature}{type}                                 = 'dropdown';
  $fields{allelenature}{label}                                = 'Inheritance Pattern';
  $fields{allelenature}{startHidden}                          = 'startHidden';
  $fields{allelenature}{terminfo}                             = qq(If applicable, choose the inheritance pattern of the allele with respect to the phenotype(s) entered.);
#   tie %{ $fields{allelefunction}{field} }, "Tie::IxHash";
  $fields{allelefunction}{multi}                              = '1';
  $fields{allelefunction}{type}                               = 'dropdown';
  $fields{allelefunction}{label}                              = 'Mutation Effect';
  $fields{allelefunction}{startHidden}                        = 'startHidden';
  $fields{allelefunction}{terminfo}                           = qq(If applicable, choose the functional consequence of the allele with respect to the phenotype(s) entered.);
#   tie %{ $fields{penetrance}{field} }, "Tie::IxHash";
  $fields{penetrance}{multi}                                  = '1';
  $fields{penetrance}{type}                                   = 'dropdown';
  $fields{penetrance}{label}                                  = 'Penetrance';
  $fields{penetrance}{startHidden}                            = 'startHidden';
  $fields{penetrance}{terminfo}                               = qq(If applicable, choose a level of penetrance of the phenotype with respect to the allele entered.);
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
  $fields{tempsens}{terminfo}                                 = qq(If applicable, choose a temperature sensitivity of the allele with respect to the phenotype(s) entered.);
#   tie %{ $fields{comment}{field} }, "Tie::IxHash";
  $fields{comment}{multi}                                     = '1';
  $fields{comment}{type}                                      = 'textarea';
  $fields{comment}{label}                                     = 'Comment';
  $fields{comment}{startHidden}                               = 'startHidden';

  tie %{ $dropdown{allelenature} }, "Tie::IxHash";
  $dropdown{allelenature}{"Recessive"}                              = "Recessive";
  $dropdown{allelenature}{"Semi_dominant"}                          = "Semi-dominant";
  $dropdown{allelenature}{"Dominant"}                               = "Dominant";
  tie %{ $dropdown{allelefunction} }, "Tie::IxHash";
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
<script type="text/javascript" src="/~azurebrd/javascript/allele_phenotype.js"></script>
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
  my $ip = $query->remote_host();			# set value for current user IP, not (potentially) loaded IP 
  my $twonum = $wbperson; $twonum =~ s/WBPerson/two/;
  $result = $dbh->do( "DELETE FROM two_user_ip WHERE two_user_ip = '$ip' ;" );
  $result = $dbh->do( "INSERT INTO two_user_ip VALUES ('$twonum', '$ip', '$submitter_email')" ); 
} # sub updateUserIp

sub getUserByIp {
  my $ip = $query->remote_host();			# get user values based on current user IP, not (potentially) loaded IP
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
  sendmail(%mail) || print qq(<span style="color:red">Error, confirmation email failed</span> : $Mail::Sendmail::error<br/>\n);
} # sub mailSendmail


# sub printGenericEditorDropdown {
#   my ($field) = @_;
#   my $amount = $fields{$field}{multi};
#   for my $i (1 .. $amount) {
#     my $group_style = ''; if ($i > 1) { $group_style = 'display: none'; }
#     if ($i < $fields{$field}{hasdata} + 2) { $group_style = ''; }
#     my $trToPrint = qq(<tr id="group_${i}_${field}" style="$group_style">\n);
#     my $td_label .= &printEditorLabel($i, $field);
#     my $td_text  .= &printEditorDropdown($i, $field);
#     $trToPrint   .= $td_label; 
#     $trToPrint   .= $td_text; 
#     $trToPrint   .= qq(</tr>\n);
#     print $trToPrint;
#   } # for my $i (1 .. $amount)
# } # sub printGenericEditorDropdown
# 
# sub printGenericEditorOntology {
#   my ($field) = @_;
#   my $amount = $fields{$field}{multi};
#   for my $i (1 .. $amount) {
#     my $group_style = ''; if ($i > 1) { $group_style = 'display: none'; }
#     if ($i < $fields{$field}{hasdata} + 2) { $group_style = ''; }
#     my $trToPrint = qq(<tr id="group_${i}_${field}" style="$group_style">\n);
#     if ($i == 1) {						# on the first row, show the field information for javascript
#       $trToPrint .= qq(<input type="hidden" class="fields" value="$field" />\n);
#       my $data = '{ ';                                                    # data is { 'tag' : 'value', 'tag2' : 'value2' } format javascript stuff
#       foreach my $tag (sort keys %{ $fields{$field} }) {
#         my $tag_value = $fields{$field}{$tag};
#         next if ($tag eq 'pg');				# hash 
#         next if ($tag eq 'terminfo');			# has commas and other bad characters
#         if ($tag eq 'radio') { $tag_value = join" ", sort keys %{ $fields{$field}{$tag} }; }
#         $data .= "'$tag' : '$tag_value', "; }
#       $data .= "'multi' : '$amount', ";
#       $data =~ s/, $/ }/;
#       $trToPrint .= qq(<input type="hidden" id="data_$field" value="$data" />\n);
#     } # if ($i == 1)
#     my $td_label .= &printEditorLabel($i, $field);
#     my $td_text  .= &printEditorOntology($i, $field);
#     $trToPrint   .= $td_label; 
#     $trToPrint   .= $td_text; 
#     $trToPrint   .= qq(</tr>\n);
#     print $trToPrint;
#   } # for my $i (1 .. $amount)
# } # sub printGenericEditorOntology
# 
# sub printGenericEditorText {
#   my ($field) = @_;
#   my $amount = $fields{$field}{multi};
#   for my $i (1 .. $amount) {
#     my $group_style = ''; if ($i > 1) { $group_style = 'display: none'; }
#     if ($i < $fields{$field}{hasdata} + 2) { $group_style = ''; }
#     my $trToPrint = qq(<tr id="group_${i}_${field}" style="$group_style">\n);
#     my $td_label .= &printEditorLabel($i, $field);
#     my $td_text  .= &printEditorText($i, $field);
#     $trToPrint   .= $td_label; 
#     $trToPrint   .= $td_text; 
#     $trToPrint   .= qq(</tr>\n);
#     print $trToPrint;
#   } # for my $i (1 .. $amount)
# } # sub printGenericEditorText

__END__

sub pmidToTitle {               # given user pmids + previously retrieved pmidTitles, get titles for new pmids not already in pmidTitles list, return new pmidTitles list. also remove from pmidTitles pmids that are not in the pmids list (from a user deletion)  This form only uses one pmid so the extra pmids part is not needed, but kept just in case it changes later
  print "Content-type: text/html\n\n";
#   my ($var, $pmids)      = &getHtmlVar($query, 'pmids');                # what user enter as pmids
#   ($var, my $pmidTitles) = &getHtmlVar($query, 'pmidTitles');           # what the form has previously processed into PMID <pmid> : title
#   my (@pmids) = $pmids =~ m/(\d+)/g; my %pmids; foreach (@pmids) { $pmids{$_}++; }      # pmids are any sets of digits
#   my (@matches) = $pmidTitles =~ m/PMID (\d+) : /g;                     # previous matches are in the format PMID <pmid> :
#   my @lines = split/PMID /, $pmidTitles;                                # split into each <pmid> : <title>
#   my $stillWantedPmidTitles = '';                                       # pmid+titles previously looked up for pmids that are still in the pmids field
#   foreach my $line (@lines) {
#     my ($pmid, $title) = $line =~ m/^(\d+) : (.*)$/;                    # get the pmid and title
#     if ($pmids{$pmid}) { $stillWantedPmidTitles .= "PMID $pmid : $title\n"; }   # if it's still in the pmids list, add to data to display below new matches
#   }
# 
#   foreach my $matches (@matches) { delete $pmids{$matches}; }           # if already matched previously, remove from %pmids and don't look up in ebi
#   foreach my $pmid (sort keys %pmids) {                                 # for each pmid that doesn't already have a title
  my ($var, $userInput)      = &getHtmlVar($query, 'pmids');                # what user enter as pmids
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
  print $toPrint;
#     print "PMID $pmid - $title\n";                                    # print the pmid and title in proper format
#   } # foreach my $pmid (sort keys %pmids)
#   print "$stillWantedPmidTitles\n";                                     # print at the bottom previous matches that are still wanted pmids in the pmids field
# http://www.ebi.ac.uk/europepmc/webservices/rest/search/format=xml&query=ext_id:23677347%20src:med
} # sub pmidToTitle


# sub deletePg {		# if submitting or over-saving loaded data, get rid of the previous save
#   my ($user_ip, $time) = @_;
#   my $pgcommand = qq(DELETE FROM frm_user_save WHERE frm_user_ip = '$user_ip' AND frm_time = '$time');
#   print qq($pgcommand<br/>\n);
# UNCOMMENT if need to save and load data on this form
# #   $dbh->do( $pgcommand );
# } # sub deletePg

sub initFieldsOLD {
  tie %{ $fields{hidden}{field} }, "Tie::IxHash";
  $fields{hidden}{multi}                                                     = '1';
  $fields{hidden}{field}{origip}{type}                                       = 'hidden';
  $fields{hidden}{field}{origtime}{type}                                     = 'hidden';
#   tie %{ $fields{exprid}{field} }, "Tie::IxHash";
#   $fields{exprid}{multi}                                                     = '1';
#   $fields{exprid}{field}{exprid}{type}                                       = 'readonly';
#   $fields{exprid}{field}{exprid}{label}                                      = 'WB Expr ID';
#   $fields{exprid}{field}{exprid}{group}                                      = 'exprid';
#   $fields{exprid}{field}{exprid}{mandatory}                                  = 'mandatory';
#   $fields{exprid}{field}{exprid}{oamulti}{'exp'}                             = 'single';
#   $fields{exprid}{field}{exprid}{oamulti}{'pic'}                             = 'multi';
#   $fields{exprid}{field}{exprid}{pg}{'exp'}                                  = 'name';
#   $fields{exprid}{field}{exprid}{pg}{'pic'}                                  = 'exprpattern';
#   $fields{exprid}{field}{exprid}{defaultvalue}                               = 'new';
# #   for (1 .. $fields{exprid}{multi}) {
# #     $fields{exprid}{field}{exprid}{inputvalue}{$_}                                = 'new'; }
  tie %{ $fields{person}{field} }, "Tie::IxHash";
  $fields{person}{multi}                                                     = '1';
  $fields{person}{field}{person}{type}                                       = 'ontology';
  $fields{person}{field}{person}{label}                                      = 'Your Name';
  $fields{person}{field}{person}{group}                                      = 'person';
  $fields{person}{field}{person}{terminfo}                                   = qq(If you do not have a WBPerson ID please <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi" target="new">contact</a> WormBase to have one assigned.);
  $fields{person}{field}{person}{mandatory}                                  = 'mandatory';
  $fields{person}{field}{person}{oamulti}                                    = 'multi';
  $fields{person}{field}{person}{ontology_type}                              = 'WBPerson';
  $fields{person}{field}{person}{pg}{'pic'}                                  = 'contact';
  $fields{person}{field}{person}{pg}{'exp'}                                  = 'contact';
  $fields{person}{field}{person}{pg}{'cns'}                                  = 'person';
  tie %{ $fields{email}{field} }, "Tie::IxHash";
  $fields{email}{multi}                                                      = '1';
  $fields{email}{field}{email}{type}                                         = 'text';
  $fields{email}{field}{email}{label}                                        = 'Your e-mail address';
  $fields{email}{field}{email}{example}                                      = 'help@wormbase.org';
  $fields{email}{field}{email}{group}                                        = 'email';
  $fields{email}{field}{email}{mandatory}                                    = 'mandatory';
  $fields{email}{field}{email}{oamulti}                                      = 'single';
  $fields{email}{field}{email}{pg}{'pic'}                                    = 'email';
  $fields{email}{field}{email}{pg}{'exp'}                                    = 'email';
  tie %{ $fields{coaut}{field} }, "Tie::IxHash";
  $fields{coaut}{multi}                                                      = '10';
  $fields{coaut}{field}{coaut}{type}                                         = 'ontology';
  $fields{coaut}{field}{coaut}{label}                                        = 'Co-authors';
  $fields{coaut}{field}{coaut}{example}                                      = 'Who else contributed?';
  $fields{coaut}{field}{coaut}{group}                                        = 'coaut';
  $fields{coaut}{field}{coaut}{mandatory}                                    = 'optional';
  $fields{coaut}{field}{coaut}{oamulti}                                      = 'multi';
  $fields{coaut}{field}{coaut}{ontology_type}                                = 'WBPerson';
  $fields{coaut}{field}{coaut}{pg}{'pic'}                                    = 'coaut';
  $fields{coaut}{field}{coaut}{pg}{'exp'}                                    = 'coaut';
  tie %{ $fields{laboratory}{field} }, "Tie::IxHash";
  $fields{laboratory}{multi}                                                 = '10';
#   $fields{laboratory}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{laboratory}{field}{laboratory}{type}                               = 'ontology';
  $fields{laboratory}{field}{laboratory}{label}                              = 'Laboratory';
  $fields{laboratory}{field}{laboratory}{group}                              = 'laboratory';
  $fields{laboratory}{field}{laboratory}{terminfo}                           = 'Start typing the PI name and select an entry from the list.  Click <a href="mailto:genenames@wormbase.org">here</a> to request a lab designation.';
  $fields{laboratory}{field}{laboratory}{mandatory}                          = 'mandatory';
#   $fields{laboratory}{field}{laboratory}{supergroup}                         = 'construct';
  $fields{laboratory}{field}{laboratory}{oamulti}                            = 'multi';
  $fields{laboratory}{field}{laboratory}{ontology_type}                      = 'obo';
  $fields{laboratory}{field}{laboratory}{ontology_table}                     = 'laboratory';
  $fields{laboratory}{field}{laboratory}{pg}{'cns'}                          = 'laboratory';
  $fields{laboratory}{field}{laboratory}{pg}{'exp'}                          = 'laboratory';
  tie %{ $fields{funding}{field} }, "Tie::IxHash";
  $fields{funding}{multi}                                                    = '1';
  $fields{funding}{field}{funding}{type}                                     = 'bigtext';
  $fields{funding}{field}{funding}{label}                                    = 'Funding';
  $fields{funding}{field}{funding}{group}                                    = 'funding';
  $fields{funding}{field}{funding}{terminfo}                                 = 'Example: "This work was supported by the National Human Genome Research Institute of the National Institutes of Health [ grant number HGxxxxxx-xx ] and the Wellcome Trust [ grant number xxxxxx ]."';
  $fields{funding}{field}{funding}{mandatory}                                = 'mandatory';
  $fields{funding}{field}{funding}{oamulti}                                  = 'single';
  $fields{funding}{field}{funding}{pg}{'exp'}                                = 'funding';
  tie %{ $fields{species}{field} }, "Tie::IxHash";
  $fields{species}{multi}                                                    = '1';
  $fields{species}{field}{species}{type}                                     = 'ontology';
  $fields{species}{field}{species}{label}                                    = 'Species';
  $fields{species}{field}{species}{example}                                  = 'Ex: Caenorhabditis elegans';
  $fields{species}{field}{species}{group}                                    = 'species';
  $fields{species}{field}{species}{terminfo}                                 = 'obo';
  $fields{species}{field}{species}{mandatory}                                = 'mandatory';
  $fields{species}{field}{species}{oamulti}                                  = 'single';
  $fields{species}{field}{species}{ontology_type}                            = 'obo';
  $fields{species}{field}{species}{ontology_table}                           = 'species';
  $fields{species}{field}{species}{pg}{'exp'}                                = 'species';
  $fields{species}{field}{species}{pg}{'pic'}                                = 'species';
  tie %{ $fields{imageupload}{field} }, "Tie::IxHash";
  $fields{imageupload}{multi}                                                = '1';
  $fields{imageupload}{field}{imageupload}{type}                             = 'upload';
  $fields{imageupload}{field}{imageupload}{label}                            = 'Choose an image (jpg format)';
  $fields{imageupload}{field}{imageupload}{group}                            = 'imageupload';
  $fields{imageupload}{field}{imageupload}{terminfo}                         = 'Each submission should have an image depicting the localization of a reporter gene fusion. The image should be at high resolution as it will be used as evidence of expression and should be unequivocally interpreted by a reviewer.  When necessary, arrows and labels to facilitate interpretation should be added. You can submit more than one image for one specific expression pattern by creating a panel as if you were generating a figure for a research article. Remember that the reporter should be the same for all images. Click <a href="http://mangolassi.caltech.edu/~acedb/draciti/Micropublication/Guidelines.htm">here</a> to see full guidelines.';
  $fields{imageupload}{field}{imageupload}{mandatory}                        = 'mandatory';
  $fields{imageupload}{field}{imageupload}{oamulti}                          = 'single';
  $fields{imageupload}{field}{imageupload}{upload_type}                      = 'jpg';
  $fields{imageupload}{field}{imageupload}{pg}{'pic'}                        = 'source';
  tie %{ $fields{gene}{field} }, "Tie::IxHash";
  $fields{gene}{multi}                                                       = '1';
  $fields{gene}{field}{gene}{type}                                           = 'ontology';
  $fields{gene}{field}{gene}{label}                                          = 'Expression Pattern for Gene';
  $fields{gene}{field}{gene}{example}                                        = 'Ex: lin-3';
  $fields{gene}{field}{gene}{group}                                          = 'gene';
  $fields{gene}{field}{gene}{mandatory}                                      = 'mandatory';
  $fields{gene}{field}{gene}{ontology_type}                                  = 'WBGene';
  $fields{gene}{field}{gene}{oamulti}                                        = 'multi';
  $fields{gene}{field}{gene}{pg}{'exp'}                                      = 'gene';

  tie %{ $fields{spacertransgene}{field} }, "Tie::IxHash";
  $fields{spacertransgene}{multi}                                            = '1';
  $fields{spacertransgene}{field}{spacertransgene}{type}                     = 'spacer';
  $fields{spacertransgene}{field}{spacertransgene}{label}                    = 'Which reporter fusion did you use?';
  $fields{spacertransgene}{field}{spacertransgene}{group}                    = 'spacertransgene';
  $fields{spacertransgene}{field}{spacertransgene}{mandatory}                = 'optional';
  $fields{spacertransgene}{field}{spacertransgene}{fontsize}                 = '12pt';
  $fields{spacertransgene}{field}{spacertransgene}{height}                   = '50px';

  tie %{ $fields{spacertransgenemore}{field} }, "Tie::IxHash";
  $fields{spacertransgenemore}{multi}                                        = '1';
  $fields{spacertransgenemore}{field}{spacertransgenemore}{type}             = 'spacer';
  $fields{spacertransgenemore}{field}{spacertransgenemore}{label}            = qq(Click on Existing transgene and type the name of it if the reporter fusion was already described or select New Transgene if you wish to submit a new construct);
  $fields{spacertransgenemore}{field}{spacertransgenemore}{group}            = 'spacertransgenemore';
  $fields{spacertransgenemore}{field}{spacertransgenemore}{mandatory}        = 'optional';
  $fields{spacertransgenemore}{field}{spacertransgenemore}{fontsize}         = '8pt';

  tie %{ $fields{method}{field} }, "Tie::IxHash";
  $fields{method}{multi}                                                     = '1';
  $fields{method}{field}{method}{type}                                       = 'radio';
  $fields{method}{field}{method}{label}                                      = 'Existing OR New Transgene';
  $fields{method}{field}{method}{group}                                      = 'method';
  $fields{method}{field}{method}{mandatory}                                  = 'mandatory';
  tie %{ $fields{method}{field}{method}{radio} }, "Tie::IxHash";
  $fields{method}{field}{method}{radio}{transgene}                           = 'Existing Transgene';
  $fields{method}{field}{method}{radio}{construct}                           = 'New Transgene';
#   $fields{method}{field}{method}{oamulti}                                  = 'single';
#   $fields{method}{field}{method}{pg}{'cns'}                                = 'method';

  tie %{ $fields{transgene}{field} }, "Tie::IxHash";
  $fields{transgene}{multi}                                                  = '10';
#   $fields{transgene}{class}                                                  = [ 'method', 'method_transgene' ];
  $fields{transgene}{field}{transgene}{type}                                 = 'ontology';
  $fields{transgene}{field}{transgene}{label}                                = 'Transgene used';
  $fields{transgene}{field}{transgene}{example}                              = 'Ex: syIs107';
  $fields{transgene}{field}{transgene}{group}                                = 'transgene';
  $fields{transgene}{field}{transgene}{mandatory}                            = 'transgene';
  $fields{transgene}{field}{transgene}{supergroup}                           = 'transgene';
  $fields{transgene}{field}{transgene}{oamulti}                              = 'multi';
  $fields{transgene}{field}{transgene}{ontology_type}                        = 'WBTransgene';
  $fields{transgene}{field}{transgene}{pg}{'exp'}                            = 'transgene';

#   tie %{ $fields{cnstrid}{field} }, "Tie::IxHash";
#   $fields{cnstrid}{multi}                                                    = '1';
# #   $fields{cnstrid}{class}                                                    = [ 'method', 'method_construct' ];
#   $fields{cnstrid}{field}{cnstrid}{type}                                     = 'readonly';
#   $fields{cnstrid}{field}{cnstrid}{label}                                    = 'WB Construct ID';
#   $fields{cnstrid}{field}{cnstrid}{group}                                    = 'cnstrid';
#   $fields{cnstrid}{field}{cnstrid}{mandatory}                                = 'mandatory';
#   $fields{cnstrid}{field}{cnstrid}{supergroup}                               = 'construct';
#   $fields{cnstrid}{field}{cnstrid}{oamulti}{'exp'}                           = 'multi';
#   $fields{cnstrid}{field}{cnstrid}{oamulti}{'cns'}                           = 'text';
#   $fields{cnstrid}{field}{cnstrid}{pg}{'exp'}                                = 'construct';
#   $fields{cnstrid}{field}{cnstrid}{pg}{'cns'}                                = 'name';
#   $fields{cnstrid}{field}{cnstrid}{defaultvalue}                             = 'new';
  tie %{ $fields{summary}{field} }, "Tie::IxHash";
  $fields{summary}{multi}                                                    = '1';
#   $fields{summary}{class}                                                    = [ 'method', 'method_construct' ];
  $fields{summary}{field}{summary}{type}                                     = 'text';
  $fields{summary}{field}{summary}{label}                                    = 'Genotype';
  $fields{summary}{field}{summary}{example}                                  = 'Ex: lin-3&#58;&#58;GFP';
  $fields{summary}{field}{summary}{group}                                    = 'summary';
  $fields{summary}{field}{summary}{mandatory}                                = 'construct';
  $fields{summary}{field}{summary}{supergroup}                               = 'construct';
  $fields{summary}{field}{summary}{oamulti}                                  = 'single';
  $fields{summary}{field}{summary}{pg}{'cns'}                                = 'summary';
  tie %{ $fields{cnssummary}{field} }, "Tie::IxHash";
  $fields{cnssummary}{multi}                                                 = '1';
#   $fields{cnssummary}{class}                                                 = [ 'method', 'method_construct' ];
  $fields{cnssummary}{field}{cnssummary}{type}                               = 'bigtext';
  $fields{cnssummary}{field}{cnssummary}{label}                              = 'Construction Details';
  $fields{cnssummary}{field}{cnssummary}{group}                              = 'cnssummary';
  $fields{cnssummary}{field}{cnssummary}{terminfo}                           = qq(Example: [pkd-2::GFP] translational fusion. The pkd-2-GFP plasmid was made using plasmid pPD95.75 as parent vector, and a fusion of a long range PCR fragment of genomic pkd-2 (promoter and 5'-end) with a 3'-end fragment derived from yk219e1 to produce a 7.153-kb fusion containing the full-length pkd-2 gene.);
  $fields{cnssummary}{field}{cnssummary}{mandatory}                          = 'construct';
  $fields{cnssummary}{field}{cnssummary}{supergroup}                         = 'construct';
  $fields{cnssummary}{field}{cnssummary}{oamulti}                            = 'single';
  $fields{cnssummary}{field}{cnssummary}{pg}{'cns'}                          = 'constructionsummary';
  tie %{ $fields{dna}{field} }, "Tie::IxHash";
  $fields{dna}{multi}                                                        = '10';
#   $fields{dna}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{dna}{field}{dna}{type}                                             = 'bigtext';
  $fields{dna}{field}{dna}{label}                                            = 'DNA sequence';
  $fields{dna}{field}{dna}{group}                                            = 'dna';
  $fields{dna}{field}{dna}{terminfo}                                         = qq(Enter the DNA sequence used to drive reporter expression -excluding backbone vector and reporter itself. If you used a translational fusion, please add all pertinent DNA sequence in the box. If you want to enter 2 non-contiguous DNA sequences please enter the first one in the DNA sequence box. Once you will click outside the box a new DNA sequence field will appear, you can then enter the second sequence.  If you have primers you can use the Wormbase e-PCR tool located <a href="http://www.wormbase.org/tools/epcr" target="new">here</a>.);
  $fields{dna}{field}{dna}{mandatory}                                        = 'construct';
  $fields{dna}{field}{dna}{supergroup}                                       = 'construct';
  $fields{dna}{field}{dna}{oamulti}                                          = 'pipe';
  $fields{dna}{field}{dna}{pg}{'cns'}                                        = 'dna';
  tie %{ $fields{threeutr}{field} }, "Tie::IxHash";
  $fields{threeutr}{multi}                                                   = '10';
  $fields{threeutr}{field}{threeutr}{type}                                   = 'ontology';
  $fields{threeutr}{field}{threeutr}{label}                                  = "3' UTR";
  $fields{threeutr}{field}{threeutr}{example}                                = 'Ex: unc-54';
  $fields{threeutr}{field}{threeutr}{group}                                  = 'threeutr';
  $fields{threeutr}{field}{threeutr}{mandatory}                              = 'optional';
  $fields{threeutr}{field}{threeutr}{supergroup}                             = 'construct';
  $fields{threeutr}{field}{threeutr}{ontology_type}                          = 'WBGene';
  $fields{threeutr}{field}{threeutr}{oamulti}                                = 'multi';
  $fields{threeutr}{field}{threeutr}{pg}{'cns'}                              = 'threeutr';
  tie %{ $fields{reporter}{field} }, "Tie::IxHash";
  $fields{reporter}{multi}                                                   = '10';
#   $fields{reporter}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{reporter}{field}{reporter}{type}                                   = 'ontology';
  $fields{reporter}{field}{reporter}{label}                                  = 'Reporter';
  $fields{reporter}{field}{reporter}{example}                                = 'Ex: GFP';
  $fields{reporter}{field}{reporter}{group}                                  = 'reporter';
  $fields{reporter}{field}{reporter}{terminfo}                               = 'obo';
  $fields{reporter}{field}{reporter}{mandatory}                              = 'construct';
  $fields{reporter}{field}{reporter}{supergroup}                             = 'construct';
  $fields{reporter}{field}{reporter}{oamulti}                                = 'multi';
  $fields{reporter}{field}{reporter}{ontology_type}                          = 'obo';
  $fields{reporter}{field}{reporter}{ontology_table}                         = 'cnsreporter';
  $fields{reporter}{field}{reporter}{pg}{'cns'}                              = 'reporter';
  tie %{ $fields{clone}{field} }, "Tie::IxHash";
  $fields{clone}{multi}                                                      = '10';
#   $fields{clone}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{clone}{field}{clone}{type}                                         = 'ontology';
  $fields{clone}{field}{clone}{label}                                        = 'Backbone Vector';
  $fields{clone}{field}{clone}{example}                                      = 'Ex: pPD107.94';
  $fields{clone}{field}{clone}{group}                                        = 'clone';
  $fields{clone}{field}{clone}{mandatory}                                    = 'optional';
  $fields{clone}{field}{clone}{supergroup}                                   = 'construct';
  $fields{clone}{field}{clone}{oamulti}                                      = 'multi';
  $fields{clone}{field}{clone}{ontology_type}                                = 'obo';
  $fields{clone}{field}{clone}{ontology_table}                               = 'clone';
  $fields{clone}{field}{clone}{pg}{'cns'}                                    = 'clone';
  tie %{ $fields{cnstype}{field} }, "Tie::IxHash";
  $fields{cnstype}{multi}                                                    = '1';
#   $fields{cnstype}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{cnstype}{field}{cnstype}{type}                                     = 'ontology';
  $fields{cnstype}{field}{cnstype}{label}                                    = 'Fusion Type';
  $fields{cnstype}{field}{cnstype}{example}                                  = 'Ex: Transcriptional_fusion';
  $fields{cnstype}{field}{cnstype}{group}                                    = 'cnstype';
  $fields{cnstype}{field}{cnstype}{terminfo}                                 = 'obo';
  $fields{cnstype}{field}{cnstype}{mandatory}                                = 'construct';
  $fields{cnstype}{field}{cnstype}{supergroup}                               = 'construct';
  $fields{cnstype}{field}{cnstype}{oamulti}                                  = 'multi';
  $fields{cnstype}{field}{cnstype}{ontology_type}                            = 'obo';
  $fields{cnstype}{field}{cnstype}{ontology_table}                           = 'cnsconstructtype';
  $fields{cnstype}{field}{cnstype}{pg}{'cns'}                                = 'cnstype';
  tie %{ $fields{cnspubname}{field} }, "Tie::IxHash";
  $fields{cnspubname}{multi}                                                 = '1';
#   $fields{cnspubname}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{cnspubname}{field}{cnspubname}{type}                               = 'text';
  $fields{cnspubname}{field}{cnspubname}{label}                              = 'Transgene Name';
  $fields{cnspubname}{field}{cnspubname}{example}                            = 'Ex: adEx1288';
  $fields{cnspubname}{field}{cnspubname}{group}                              = 'cnspubname';
  $fields{cnspubname}{field}{cnspubname}{terminfo}                           = qq(Please assign a name to your transgene using your lab's allele designation, and Ex, Is or Si for extrachromosomal, integrated, and single site insertions, respectively  i.e., otEx103, utIs18, oxSi48);
  $fields{cnspubname}{field}{cnspubname}{mandatory}                          = 'construct';
  $fields{cnspubname}{field}{cnspubname}{supergroup}                         = 'construct';
  $fields{cnspubname}{field}{cnspubname}{oamulti}                            = 'single';
  $fields{cnspubname}{field}{cnspubname}{pg}{'cns'}                          = 'cnspubname';
  tie %{ $fields{remark}{field} }, "Tie::IxHash";
  $fields{remark}{multi}                                                     = '1';
  $fields{remark}{field}{remark}{type}                                       = 'bigtext';
  $fields{remark}{field}{remark}{label}                                      = 'Construct Comments';
  $fields{remark}{field}{remark}{group}                                      = 'remark';
  $fields{remark}{field}{remark}{mandatory}                                  = 'optional';
  $fields{remark}{field}{remark}{supergroup}                                 = 'construct';
  $fields{remark}{field}{remark}{oamulti}                                    = 'single';
  $fields{remark}{field}{remark}{pg}{'cns'}                                  = 'remark';
#   tie %{ $fields{assoctransgene}{field} }, "Tie::IxHash";
#   $fields{assoctransgene}{multi}                                             = '1';
#   $fields{assoctransgene}{field}{assoctransgene}{type}                       = 'text';
#   $fields{assoctransgene}{field}{assoctransgene}{label}                      = 'Associated Transgene';
#   $fields{assoctransgene}{field}{assoctransgene}{group}                      = 'assoctransgene';
#   $fields{assoctransgene}{field}{assoctransgene}{mandatory}                  = 'optional';
#   $fields{assoctransgene}{field}{assoctransgene}{supergroup}                 = 'construct';
#   $fields{assoctransgene}{field}{assoctransgene}{oamulti}                    = 'single';
#   $fields{assoctransgene}{field}{assoctransgene}{pg}{'cns'}                  = 'assoctransgene';
  tie %{ $fields{strain}{field} }, "Tie::IxHash";
  $fields{strain}{multi}                                                     = '1';
  $fields{strain}{field}{strain}{type}                                       = 'text';
  $fields{strain}{field}{strain}{label}                                      = 'Strain';
  $fields{strain}{field}{strain}{group}                                      = 'strain';
  $fields{strain}{field}{strain}{mandatory}                                  = 'optional';
  $fields{strain}{field}{strain}{supergroup}                                 = 'construct';
  $fields{strain}{field}{strain}{oamulti}                                    = 'single';
  $fields{strain}{field}{strain}{pg}{'cns'}                                  = 'strain';
  tie %{ $fields{coinjectedwith}{field} }, "Tie::IxHash";
  $fields{coinjectedwith}{multi}                                             = '1';
  $fields{coinjectedwith}{field}{coinjectedwith}{type}                       = 'text';
  $fields{coinjectedwith}{field}{coinjectedwith}{label}                      = 'Coinjected with';
  $fields{coinjectedwith}{field}{coinjectedwith}{group}                      = 'coinjectedwith';
  $fields{coinjectedwith}{field}{coinjectedwith}{mandatory}                  = 'optional';
  $fields{coinjectedwith}{field}{coinjectedwith}{supergroup}                 = 'construct';
  $fields{coinjectedwith}{field}{coinjectedwith}{oamulti}                    = 'single';
  $fields{coinjectedwith}{field}{coinjectedwith}{pg}{'cns'}                  = 'coinjectedwith';
  tie %{ $fields{cnssumextra}{field} }, "Tie::IxHash";
  $fields{cnssumextra}{multi}                                                = '1';
  $fields{cnssumextra}{field}{cnssumextra}{type}                             = 'text';
  $fields{cnssumextra}{field}{cnssumextra}{label}                            = 'Injection Concentration';
  $fields{cnssumextra}{field}{cnssumextra}{group}                            = 'cnssumextra';
  $fields{cnssumextra}{field}{cnssumextra}{mandatory}                        = 'optional';
  $fields{cnssumextra}{field}{cnssumextra}{supergroup}                       = 'construct';
  $fields{cnssumextra}{field}{cnssumextra}{oamulti}                          = 'single';
  $fields{cnssumextra}{field}{cnssumextra}{pg}{'cns'}                        = 'coinjectedwith';
  tie %{ $fields{integratedby}{field} }, "Tie::IxHash";
  $fields{integratedby}{multi}                                               = '1';
  $fields{integratedby}{field}{integratedby}{type}                           = 'ontology';
  $fields{integratedby}{field}{integratedby}{label}                          = 'Integrated by';
  $fields{integratedby}{field}{integratedby}{example}                        = 'Ex: Particle_bombardment';
  $fields{integratedby}{field}{integratedby}{group}                          = 'integratedby';
  $fields{integratedby}{field}{integratedby}{mandatory}                      = 'optional';
  $fields{integratedby}{field}{integratedby}{supergroup}                     = 'construct';
  $fields{integratedby}{field}{integratedby}{oamulti}                        = 'multi';
  $fields{integratedby}{field}{integratedby}{ontology_type}                  = 'obo';
  $fields{integratedby}{field}{integratedby}{ontology_table}                 = 'integrationmethod';
  $fields{integratedby}{field}{integratedby}{pg}{'cns'}                      = 'integrationmethod';

# Where and when did you observe expression? 
  tie %{ $fields{spacerlocalization}{field} }, "Tie::IxHash";
  $fields{spacerlocalization}{multi}                                         = '1';
  $fields{spacerlocalization}{field}{spacerlocalization}{type}               = 'spacer';
  $fields{spacerlocalization}{field}{spacerlocalization}{label}              = 'Where and when did you observe expression?';
  $fields{spacerlocalization}{field}{spacerlocalization}{group}              = 'spacerlocalization';
  $fields{spacerlocalization}{field}{spacerlocalization}{mandatory}          = 'optional';
  $fields{spacerlocalization}{field}{spacerlocalization}{fontsize}           = '12pt';
  $fields{spacerlocalization}{field}{spacerlocalization}{height}             = '50px';
  tie %{ $fields{spacerlocalizationmore}{field} }, "Tie::IxHash";
  $fields{spacerlocalizationmore}{multi}                                     = '1';
  $fields{spacerlocalizationmore}{field}{spacerlocalizationmore}{type}       = 'spacer';
  $fields{spacerlocalizationmore}{field}{spacerlocalizationmore}{label}      = qq(Enter one tissue/cell per line. Click for more info.);
  $fields{spacerlocalizationmore}{field}{spacerlocalizationmore}{group}      = 'spacerlocalizationmore';
  $fields{spacerlocalizationmore}{field}{spacerlocalizationmore}{terminfo}   = qq(Enter one tissue/cell per line.<br/>If temporal information is known and tightly linked to the cell, add anatomy information and developmental stage in the same line.<br/>For example: expression in the anchor cell during the L3 larval stage: Select Anchor cell and L3 larva Ce in the same line.<br/>If the temporal and spatial information are independent please add the terms in separate lines.<br/>For example: expressed in the intestine (life stage unspecified) and anchor cell (life stage unspecified) and expressed generally (tissue unspecified) from embryogenesis to L3 larvae.<br/>Select in separate lines intestine, anchor cell, embryo Ce in one line, L1 larva Ce, L2 larva Ce, and L3 larva Ce.<br/>If you want to describe subcellular localization in a specific cell, enter the data in the subcellular localization field and the cell in the 'In tissue/cell' field'.<br/>For example: Expressed in intestinal cells nuclei.<br/>Choose nucleus and intestinal cell);
  $fields{spacerlocalizationmore}{field}{spacerlocalizationmore}{mandatory}  = 'optional';
  $fields{spacerlocalizationmore}{field}{spacerlocalizationmore}{fontsize}   = '8pt';

  tie %{ $fields{certain}{field} }, "Tie::IxHash";
  $fields{certain}{multi}                                                    = '10';
  $fields{certain}{field}{ceranatomy}{type}                                  = 'ontology';
  $fields{certain}{field}{ceranatomy}{label}                                 = 'Certainly Expressed in';
  $fields{certain}{field}{ceranatomy}{example}                               = 'Ex: pharynx';
  $fields{certain}{field}{ceranatomy}{group}                                 = 'certain';
  $fields{certain}{field}{ceranatomy}{terminfo}                              = 'Gene A was observed to be expressed in cell Y';
  $fields{certain}{field}{ceranatomy}{mandatory}                             = 'anyanatomy';
  $fields{certain}{field}{ceranatomy}{oamulti}                               = 'multi';
  $fields{certain}{field}{ceranatomy}{ontology_type}                         = 'obo';
  $fields{certain}{field}{ceranatomy}{ontology_table}                        = 'anatomy';
  $fields{certain}{field}{ceranatomy}{pg}{'pic'}                             = 'anat_term';
  $fields{certain}{field}{ceranatomy}{pg}{'exp'}                             = 'anatomy';
  $fields{certain}{field}{cerlifestage}{type}                                = 'ontology';
  $fields{certain}{field}{cerlifestage}{label}                               = 'During';
  $fields{certain}{field}{cerlifestage}{example}                             = 'Ex: embryo Ce';
  $fields{certain}{field}{cerlifestage}{group}                               = 'certain';
  $fields{certain}{field}{cerlifestage}{mandatory}                           = 'anyanatomy';
  $fields{certain}{field}{cerlifestage}{oamulti}                             = 'multi';
  $fields{certain}{field}{cerlifestage}{ontology_type}                       = 'obo';
  $fields{certain}{field}{cerlifestage}{ontology_table}                      = 'lifestage';
  $fields{certain}{field}{cerlifestage}{pg}{'pic'}                           = 'lifestage';
  $fields{certain}{field}{cerlifestage}{pg}{'exp'}                           = 'qualifierls';
  $fields{certain}{field}{cerlifestage}{minwidth}                            = '50px';
  $fields{certain}{field}{cergoidcc}{type}                                   = 'ontology';
  $fields{certain}{field}{cergoidcc}{label}                                  = 'Subcellular localization';
  $fields{certain}{field}{cergoidcc}{example}                                = 'Ex: nucleus';
  $fields{certain}{field}{cergoidcc}{group}                                  = 'certain';
  $fields{certain}{field}{cergoidcc}{mandatory}                              = 'anyanatomy';
  $fields{certain}{field}{cergoidcc}{oamulti}                                = 'multi';
  $fields{certain}{field}{cergoidcc}{ontology_type}                          = 'obo';
  $fields{certain}{field}{cergoidcc}{ontology_table}                         = 'goid';		# special action on autocomplete
  $fields{certain}{field}{cergoidcc}{pg}{'pic'}                              = 'goid';
  $fields{certain}{field}{cergoidcc}{pg}{'exp'}                              = 'goid';
  $fields{certain}{field}{cergoidcc}{minwidth}                               = '145px';
#   $fields{certain}{field}{cerqualifier}{type}                                = 'readonly';
#   $fields{certain}{field}{cerqualifier}{label}                               = 'Qualifier';
#   $fields{certain}{field}{cerqualifier}{group}                               = 'certain';
#   $fields{certain}{field}{cerqualifier}{oamulti}                             = 'single';
#   $fields{certain}{field}{cerqualifier}{pg}{'exp'}                           = 'qualifier';
#   for (1 .. $fields{certain}{multi}) {
#     $fields{certain}{field}{cerqualifier}{inputvalue}{$_}                         = 'Certain'; }
  tie %{ $fields{partial}{field} }, "Tie::IxHash";
  $fields{partial}{multi}                                                    = '10';
  $fields{partial}{field}{paranatomy}{type}                                  = 'ontology';
  $fields{partial}{field}{paranatomy}{label}                                 = 'Partially Expressed in';
  $fields{partial}{field}{paranatomy}{group}                                 = 'partial';
  $fields{partial}{field}{paranatomy}{terminfo}                              = qq(Gene A was observed to be expressed in some cells of a group of cells that include Y.<br/>Example 1: "Expressed in 4-5 pairs of amphid neurons." You should select amphid neuron in the 'Partially Expressed in' box.<br/>Example 2: "Expressed in the anterior intestine." Select Intestine in the 'Partially Expressed in' box.);
  $fields{partial}{field}{paranatomy}{mandatory}                             = 'anyanatomy';
  $fields{partial}{field}{paranatomy}{oamulti}                               = 'multi';
  $fields{partial}{field}{paranatomy}{ontology_type}                         = 'obo';
  $fields{partial}{field}{paranatomy}{ontology_table}                        = 'anatomy';
  $fields{partial}{field}{paranatomy}{pg}{'pic'}                             = 'anat_term';
  $fields{partial}{field}{paranatomy}{pg}{'exp'}                             = 'anatomy';
  $fields{partial}{field}{parlifestage}{type}                                = 'ontology';
  $fields{partial}{field}{parlifestage}{label}                               = 'During';
  $fields{partial}{field}{parlifestage}{group}                               = 'partial';
  $fields{partial}{field}{parlifestage}{mandatory}                           = 'anyanatomy';
  $fields{partial}{field}{parlifestage}{oamulti}                             = 'multi';
  $fields{partial}{field}{parlifestage}{ontology_type}                       = 'obo';
  $fields{partial}{field}{parlifestage}{ontology_table}                      = 'lifestage';
  $fields{partial}{field}{parlifestage}{oamulti}                             = 'single';
  $fields{partial}{field}{parlifestage}{pg}{'pic'}                           = 'lifestage';
  $fields{partial}{field}{parlifestage}{pg}{'exp'}                           = 'qualifierls';
  $fields{partial}{field}{parlifestage}{minwidth}                            = '50px';
  $fields{partial}{field}{pargoidcc}{type}                                   = 'ontology';
  $fields{partial}{field}{pargoidcc}{label}                                  = 'Subcellular localization';
  $fields{partial}{field}{pargoidcc}{example}                                = 'Ex: nucleus';
  $fields{partial}{field}{pargoidcc}{group}                                  = 'partial';
  $fields{partial}{field}{pargoidcc}{mandatory}                              = 'anyanatomy';
  $fields{partial}{field}{pargoidcc}{oamulti}                                = 'multi';
  $fields{partial}{field}{pargoidcc}{ontology_type}                          = 'obo';
  $fields{partial}{field}{pargoidcc}{ontology_table}                         = 'goid';		# special action on autocomplete
  $fields{partial}{field}{pargoidcc}{pg}{'pic'}                              = 'goid';
  $fields{partial}{field}{pargoidcc}{pg}{'exp'}                              = 'goid';
  $fields{partial}{field}{pargoidcc}{minwidth}                               = '145px';
#   $fields{partial}{field}{parqualifier}{type}                                = 'readonly';
#   $fields{partial}{field}{parqualifier}{label}                               = 'Qualifier';
#   $fields{partial}{field}{parqualifier}{group}                               = 'partial';
#   $fields{partial}{field}{parqualifier}{pg}{'exp'}                           = 'qualifier';
#   for (1 .. $fields{partial}{multi}) {
#     $fields{partial}{field}{parqualifier}{inputvalue}{$_}                         = 'Partial'; }
  tie %{ $fields{uncertain}{field} }, "Tie::IxHash";
  $fields{uncertain}{multi}                                                  = '10';	# ucr just for three letter consistency
  $fields{uncertain}{field}{ucranatomy}{type}                                = 'ontology';
  $fields{uncertain}{field}{ucranatomy}{label}                               = 'Possibly Expressed in';
  $fields{uncertain}{field}{ucranatomy}{group}                               = 'uncertain';
  $fields{uncertain}{field}{ucranatomy}{terminfo}                            = qq(Gene A was sometimes observed to be expressed in cell Y OR Gene A was observed to be expressed in a cell that could be Y.<br/>Example 1: "Occasional expression of DDL-2 in one adult intestinal cell." You should select intestinal cell in the 'Possibly expressed in' box.<br/>Example 2: "Expression was observed less frequently in the PVPL/R interneurons." You should select PVPL and PVPR in the 'Possibly expressed in' box.);
  $fields{uncertain}{field}{ucranatomy}{mandatory}                           = 'anyanatomy';
  $fields{uncertain}{field}{ucranatomy}{oamulti}                             = 'multi';
  $fields{uncertain}{field}{ucranatomy}{ontology_type}                       = 'obo';
  $fields{uncertain}{field}{ucranatomy}{ontology_table}                      = 'anatomy';
  $fields{uncertain}{field}{ucranatomy}{pg}{'pic'}                           = 'anat_term';
  $fields{uncertain}{field}{ucranatomy}{pg}{'exp'}                           = 'anatomy';
  $fields{uncertain}{field}{ucrlifestage}{type}                              = 'ontology';
  $fields{uncertain}{field}{ucrlifestage}{label}                             = 'During';
  $fields{uncertain}{field}{ucrlifestage}{group}                             = 'uncertain';
  $fields{uncertain}{field}{ucrlifestage}{mandatory}                         = 'anyanatomy';
  $fields{uncertain}{field}{ucrlifestage}{oamulti}                           = 'multi';
  $fields{uncertain}{field}{ucrlifestage}{ontology_type}                     = 'obo';
  $fields{uncertain}{field}{ucrlifestage}{ontology_table}                    = 'lifestage';
  $fields{uncertain}{field}{ucrlifestage}{pg}{'pic'}                         = 'lifestage';
  $fields{uncertain}{field}{ucrlifestage}{pg}{'exp'}                         = 'qualifierls';
  $fields{uncertain}{field}{ucrlifestage}{minwidth}                          = '50px';
  $fields{uncertain}{field}{ucrgoidcc}{type}                                 = 'ontology';
  $fields{uncertain}{field}{ucrgoidcc}{label}                                = 'Subcellular localization';
  $fields{uncertain}{field}{ucrgoidcc}{example}                              = 'Ex: nucleus';
  $fields{uncertain}{field}{ucrgoidcc}{group}                                = 'uncertain';
  $fields{uncertain}{field}{ucrgoidcc}{mandatory}                            = 'anyanatomy';
  $fields{uncertain}{field}{ucrgoidcc}{oamulti}                              = 'multi';
  $fields{uncertain}{field}{ucrgoidcc}{ontology_type}                        = 'obo';
  $fields{uncertain}{field}{ucrgoidcc}{ontology_table}                       = 'goid';		# special action on autocomplete
  $fields{uncertain}{field}{ucrgoidcc}{pg}{'pic'}                            = 'goid';
  $fields{uncertain}{field}{ucrgoidcc}{pg}{'exp'}                            = 'goid';
  $fields{uncertain}{field}{ucrgoidcc}{minwidth}                             = '145px';
#   $fields{uncertain}{field}{ucrqualifier}{type}                              = 'readonly';
#   $fields{uncertain}{field}{ucrqualifier}{label}                             = 'Qualifier';
#   $fields{uncertain}{field}{ucrqualifier}{group}                             = 'uncertain';
#   $fields{uncertain}{field}{ucrqualifier}{oamulti}                           = 'single';
#   $fields{uncertain}{field}{ucrqualifier}{pg}{'exp'}                         = 'qualifier';
#   for (1 .. $fields{uncertain}{multi}) {
#     $fields{uncertain}{field}{ucrqualifier}{inputvalue}{$_}                       = 'Uncertain'; }
  tie %{ $fields{not}{field} }, "Tie::IxHash";
  $fields{not}{multi}                                                        = '10';
  $fields{not}{field}{notanatomy}{type}                                    = 'ontology';
  $fields{not}{field}{notanatomy}{label}                                   = 'Not Expressed in';
  $fields{not}{field}{notanatomy}{group}                                   = 'not';
  $fields{not}{field}{notanatomy}{mandatory}                               = 'anyanatomy';
  $fields{not}{field}{notanatomy}{oamulti}                                 = 'multi';
  $fields{not}{field}{notanatomy}{ontology_type}                           = 'obo';
  $fields{not}{field}{notanatomy}{ontology_table}                          = 'anatomy';
  $fields{not}{field}{notanatomy}{pg}{'pic'}                               = 'anat_term';
  $fields{not}{field}{notanatomy}{pg}{'exp'}                               = 'anatomy';
  $fields{not}{field}{notlifestage}{type}                                  = 'ontology';
  $fields{not}{field}{notlifestage}{label}                                 = 'During';
  $fields{not}{field}{notlifestage}{group}                                 = 'not';
  $fields{not}{field}{notlifestage}{mandatory}                             = 'anyanatomy';
  $fields{not}{field}{notlifestage}{oamulti}                               = 'multi';
  $fields{not}{field}{notlifestage}{ontology_type}                         = 'obo';
  $fields{not}{field}{notlifestage}{ontology_table}                        = 'lifestage';
  $fields{not}{field}{notlifestage}{pg}{'pic'}                             = 'lifestage';
  $fields{not}{field}{notlifestage}{pg}{'exp'}                             = 'qualifierls';
  $fields{not}{field}{notlifestage}{minwidth}                              = '50px';
  $fields{not}{field}{notgoidcc}{type}                                     = 'ontology';
  $fields{not}{field}{notgoidcc}{label}                                    = 'Subcellular localization';
  $fields{not}{field}{notgoidcc}{example}                                  = 'Ex: nucleus';
  $fields{not}{field}{notgoidcc}{group}                                    = 'not';
  $fields{not}{field}{notgoidcc}{mandatory}                                = 'anyanatomy';
  $fields{not}{field}{notgoidcc}{oamulti}                                  = 'multi';
  $fields{not}{field}{notgoidcc}{ontology_type}                            = 'obo';
  $fields{not}{field}{notgoidcc}{ontology_table}                           = 'goid';		# special action on autocomplete
  $fields{not}{field}{notgoidcc}{pg}{'pic'}                                = 'goid';
  $fields{not}{field}{notgoidcc}{pg}{'exp'}                                = 'goid';
  $fields{not}{field}{notgoidcc}{minwidth}                                 = '145px';
#   $fields{not}{field}{notqualifier}{type}                                  = 'readonly';
#   $fields{not}{field}{notqualifier}{label}                                 = 'Qualifier';
#   $fields{not}{field}{notqualifier}{group}                                 = 'not';
#   $fields{not}{field}{notqualifier}{oamulti}                               = 'single';
#   $fields{not}{field}{notqualifier}{pg}{'exp'}                             = 'qualifier';
#   for (1 .. $fields{not}{multi}) {
#     $fields{not}{field}{notqualifier}{inputvalue}{$_}                           = 'NOT'; }

#   tie %{ $fields{subcell}{field} }, "Tie::IxHash";
#   $fields{subcell}{multi}                                                    = '10';
#   $fields{subcell}{field}{goidcc}{type}                                      = 'ontology';
#   $fields{subcell}{field}{goidcc}{label}                                     = 'Subcellular localization';
#   $fields{subcell}{field}{goidcc}{example}                                   = 'Ex: nucleus';
#   $fields{subcell}{field}{goidcc}{group}                                     = 'subcell';
#   $fields{subcell}{field}{goidcc}{mandatory}                                 = 'anyanatomy';
#   $fields{subcell}{field}{goidcc}{oamulti}                                   = 'multi';
#   $fields{subcell}{field}{goidcc}{ontology_type}                             = 'obo';
#   $fields{subcell}{field}{goidcc}{ontology_table}                            = 'goid';		# special action on autocomplete
#   $fields{subcell}{field}{goidcc}{pg}{'pic'}                                 = 'goid';
#   $fields{subcell}{field}{goidcc}{pg}{'exp'}                                 = 'goid';
#   $fields{subcell}{field}{goidanatomy}{type}                                 = 'ontology';
#   $fields{subcell}{field}{goidanatomy}{label}                                = 'In tissue/cell';
#   $fields{subcell}{field}{goidanatomy}{example}                              = 'Ex: pharynx';
#   $fields{subcell}{field}{goidanatomy}{group}                                = 'subcell';
#   $fields{subcell}{field}{goidanatomy}{mandatory}                            = 'anyanatomy';
#   $fields{subcell}{field}{goidanatomy}{oamulti}                              = 'multi';
#   $fields{subcell}{field}{goidanatomy}{ontology_type}                        = 'obo';
#   $fields{subcell}{field}{goidanatomy}{ontology_table}                       = 'anatomy';
#   $fields{subcell}{field}{goidanatomy}{pg}{'pic'}                            = 'anat_term';
#   $fields{subcell}{field}{goidanatomy}{pg}{'exp'}                            = 'anatomy';
# #   $fields{subcell}{field}{goidqualifier}{type}                               = 'readonly';
# #   $fields{subcell}{field}{goidqualifier}{label}                              = 'Qualifier';
# #   $fields{subcell}{field}{goidqualifier}{group}                              = 'subcell';
# #   $fields{subcell}{field}{goidqualifier}{oamulti}                            = 'single';
# #   $fields{subcell}{field}{goidqualifier}{pg}{'exp'}                          = 'qualifier';
# #   for (1 .. $fields{subcell}{multi}) {
# #     $fields{subcell}{field}{goidqualifier}{inputvalue}{$_}                        = 'Certain'; }

  tie %{ $fields{description}{field} }, "Tie::IxHash";
  $fields{description}{multi}                                                = '1';
  $fields{description}{field}{description}{type}                             = 'bigtext';
  $fields{description}{field}{description}{label}                            = 'Pattern description';
  $fields{description}{field}{description}{group}                            = 'description';
  $fields{description}{field}{description}{terminfo}                         = q[Provide a comprehensive description of what you observed as if you were writing a paragraph for gene expression for a research article. In case you used arrows and labels in the image you provided, please explain what they are pointing to. Here a couple of pattern descriptions taken from the literature: 1): 'Strong snf-12 expression was observed in the epidermis of C. elegans throughout development. Expression is also seen in vulval cells, in the excretory cell, in the seam cells, and in the amphid and phasmid socket cells.' 2):' Expression of aipl-1 was initially detected in embryos at the comma to 1.5-fold stages (310-350 min after first cell division) in the neurons, the intestine, and the body wall muscle. In older embryos, expression of GFP is gradually diminished in the body wall muscle, while it persisted in the neurons and intestine. In adult worms, expression of GFP was detected in the intestine, the spermatheca, and some of the head neurons.];
  $fields{description}{field}{description}{mandatory}                        = 'mandatory';
  $fields{description}{field}{description}{oamulti}                          = 'single';
  $fields{description}{field}{description}{pg}{'pic'}                        = 'description';
  $fields{description}{field}{description}{pg}{'exp'}                        = 'pattern';
  tie %{ $fields{comments}{field} }, "Tie::IxHash";
  $fields{comments}{multi}                                                   = '1';
  $fields{comments}{field}{comments}{type}                                   = 'bigtext';
  $fields{comments}{field}{comments}{label}                                  = 'Comments';
  $fields{comments}{field}{comments}{group}                                  = 'comments';
  $fields{comments}{field}{comments}{mandatory}                              = 'optional';
  $fields{comments}{field}{comments}{oamulti}                                = 'single';
  $fields{comments}{field}{comments}{pg}{'pic'}                              = 'remark';
  $fields{comments}{field}{comments}{pg}{'exp'}                              = 'remark';

  tie %{ $fields{disclaimer}{field} }, "Tie::IxHash";
  $fields{disclaimer}{multi}                                                 = '1';
  $fields{disclaimer}{field}{disclaimer}{type}                               = 'checkbox';
  $fields{disclaimer}{field}{disclaimer}{label}                              = 'Disclaimer';
  $fields{disclaimer}{field}{disclaimer}{group}                              = 'disclaimer';
  $fields{disclaimer}{field}{disclaimer}{mandatory}                          = 'mandatory';
  $fields{disclaimer}{field}{disclaimer}{checkboxtext}                       = 'I declare to the best of my knowledge that the experiment is reproducible and that I will make the construct available upon request.';
  $fields{disclaimer}{field}{disclaimer}{checkboxvalue}                      = 'Agree that I declare to the best of my knowledge that the experiment is reproducible and that I will make the construct available upon request.';
#   $fields{disclaimer}{field}{disclaimer}{colspan}                            = 4;
  $fields{disclaimer}{field}{disclaimer}{colspan}                            = 6;
#   tie %{ $fields{nodump}{field} }, "Tie::IxHash";
#   $fields{nodump}{multi}                                                     = '1';
#   $fields{nodump}{field}{nodump}{type}                                       = 'readonly';
#   $fields{nodump}{field}{nodump}{label}                                      = 'No Dump';
#   $fields{nodump}{field}{nodump}{group}                                      = 'nodump';
#   $fields{nodump}{field}{nodump}{oamulti}                                    = 'single';
#   $fields{nodump}{field}{nodump}{pg}{'exp'}                                  = 'nodump';
#   $fields{nodump}{field}{nodump}{pg}{'pic'}                                  = 'nodump';
#   $fields{nodump}{field}{nodump}{pg}{'cns'}                                  = 'nodump';
#   for (1 .. $fields{nodump}{multi}) {
#     $fields{nodump}{field}{nodump}{inputvalue}{$_}                                = 'NO DUMP'; }
#   tie %{ $fields{curator}{field} }, "Tie::IxHash";
#   $fields{curator}{multi}                                                    = '1';
#   $fields{curator}{field}{curator}{type}                                     = 'readonly';
#   $fields{curator}{field}{curator}{label}                                    = 'Curator';
#   $fields{curator}{field}{curator}{group}                                    = 'curator';
#   $fields{curator}{field}{curator}{oamulti}                                  = 'single';
#   $fields{curator}{field}{curator}{pg}{'exp'}                                = 'curator';
#   $fields{curator}{field}{curator}{pg}{'pic'}                                = 'curator';
#   $fields{curator}{field}{curator}{pg}{'cns'}                                = 'curator';
#   for (1 .. $fields{curator}{multi}) {
#     $fields{curator}{field}{curator}{inputvalue}{$_}                              = 'WBPerson12028'; }
#   tie %{ $fields{micropublication}{field} }, "Tie::IxHash";
#   $fields{micropublication}{multi}                                           = '1';
#   $fields{micropublication}{field}{micropublication}{type}                   = 'readonly';
#   $fields{micropublication}{field}{micropublication}{label}                  = 'Micropublication';
#   $fields{micropublication}{field}{micropublication}{group}                  = 'micropublication';
#   $fields{micropublication}{field}{micropublication}{oamulti}                = 'single';
#   $fields{micropublication}{field}{micropublication}{pg}{'exp'}              = 'micropublication';
#   $fields{micropublication}{field}{micropublication}{pg}{'pic'}              = 'micropublication';
#   $fields{micropublication}{field}{micropublication}{pg}{'cns'}              = 'micropublication';
#   for (1 .. $fields{micropublication}{multi}) {
#     $fields{micropublication}{field}{micropublication}{inputvalue}{$_}            = 'Micropublication'; }
#   tie %{ $fields{exprtype}{field} }, "Tie::IxHash";
#   $fields{exprtype}{multi}                                                   = '1';
#   $fields{exprtype}{field}{exprtype}{type}                                   = 'readonly';
#   $fields{exprtype}{field}{exprtype}{label}                                  = 'Reporter Gene';
#   $fields{exprtype}{field}{exprtype}{group}                                  = 'exprtype';
#   $fields{exprtype}{field}{exprtype}{oamulti}                                = 'single';
#   $fields{exprtype}{field}{exprtype}{pg}{'exp'}                              = 'exprtype';
#   for (1 .. $fields{exprtype}{multi}) {
#     $fields{exprtype}{field}{exprtype}{inputvalue}{$_}                            = 'Reporter_gene'; }
#   tie %{ $fields{construct}{field} }, "Tie::IxHash";
#   $fields{construct}{multi}                                                  = '1';
#   $fields{construct}{field}{construct}{type}                                 = 'readonly';
#   $fields{construct}{field}{construct}{label}                                = 'New Construct';
#   $fields{construct}{field}{construct}{group}                                = 'construct';
#   $fields{construct}{field}{construct}{oamulti}                              = 'multi';
#   $fields{construct}{field}{construct}{pg}{'exp'}                            = 'construct';
#   for (1 .. $fields{construct}{multi}) {
#     $fields{construct}{field}{construct}{inputvalue}{$_}                          = 'new'; }
} # sub initFields

sub processUpload {
  my ($group, $i, $field, $label) = @_;
  my $input = "input_${i}_$field";
  ($var, my $filename)            = &getHtmlVar($query, "input_${i}_$field");	# newly chosen image
  ($var, my $previewfilename)     = &getHtmlVar($query, "termid_${i}_$field");	# previously chosen image (from preview or save/load)

  if ($filename) {								# there's a new image, process it
      my $upload_dir = '/home2/azurebrd/public_html/cgi-bin/uploads';
      my $ip   = $fields{hidden}{field}{origip}{inputvalue}{1};
      my $time = $fields{hidden}{field}{origtime}{inputvalue}{1};
      $filename = $ip . '_' . $time;						# replace filename with ip_time
#       my ( $name, $path, $extension ) = fileparse ( $filename, '..*' );
#       $filename = $name . $extension;
#       $filename =~ tr/ /_/;
#   my $safe_filename_characters    = "a-zA-Z0-9_.-";
#       $filename =~ s/[^$safe_filename_characters]//g;
#       if ( $filename =~ /^([$safe_filename_characters]+)$/ ) { $filename = $1; } else { die "Filename contains invalid characters"; }
      if ($previewfilename) { my $replacedfile = "$upload_dir/$previewfilename"; if (-e $replacedfile) { unlink ($replacedfile); } }
      my $upload_filehandle = $query->upload("input_${i}_$field");
      open ( UPLOADFILE, ">$upload_dir/$filename" ) or die "Cannot create  : $!";
      binmode UPLOADFILE;
      while ( <$upload_filehandle> ) { print UPLOADFILE; }
      close UPLOADFILE or die "Cannot close $upload_dir/$filename : $!";
      my $imageUrl = "http://mangolassi.caltech.edu/~azurebrd/cgi-bin/uploads/$filename";
      $fields{$group}{field}{$field}{termidvalue}{$i} = $filename;
#       return qq(<td>$label</td><td>$i</td><td><img width="400" src="$imageUrl"></td>\n);
      return qq(<td>$label</td><td><img width="400" src="$imageUrl"></td>\n); }
    elsif ($previewfilename) {							# there used to be an image, use that
      my $imageUrl = "http://mangolassi.caltech.edu/~azurebrd/cgi-bin/uploads/$previewfilename";
      $fields{$group}{field}{$field}{termidvalue}{$i} = $previewfilename;
#       return qq(<td>$label</td><td>$i</td><td><img width="400" src="$imageUrl"></td>\n);
      return qq(<td>$label</td><td><img width="400" src="$imageUrl"></td>\n); }
    else { return(''); }
} # sub processUpload


sub load {
  print "Content-type: text/html\n\n";
  print $header;
  &getHashFromPg();
  &showForm();
  print $footer;
} # sub load

sub getHashFromPg {
  my $datatype = 'allele_phenotype';
  my ($var, $ip)                  = &getHtmlVar($query, 'user_ip');
  ($var, my $time)                = &getHtmlVar($query, 'time');
  my $saveUrl = "allele_phenotype.cgi?action=Load&user_ip=$ip&time=$time";
  print qq(Loading data from <a href="$saveUrl">link</a><br/><br/>\n);
  $result = $dbh->prepare( "SELECT frm_field, frm_data FROM frm_user_save WHERE frm_user_ip = '$ip' AND frm_time = '$time' AND frm_datatype = '$datatype';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my $foundSomething = 0;
  while ( my @row = $result->fetchrow() ) { 
    $foundSomething++;
    my ($group, $field, $count, $dataField) = split/\t/, $row[0];
    $fields{$group}{field}{$field}{$dataField}{$count} = $row[1]; }
  if ($foundSomething) { 
      $fields{hidden}{field}{origip}{inputvalue}{1} = $ip;
      $fields{hidden}{field}{origtime}{inputvalue}{1} = $time; }
    else { print qq(There was no data for your link, you may have already submitted it, or have an error in the link.<br/><br/>); }
} # sub getHashFromPg

sub saveFormData {
  my $datatype = 'allele_phenotype';
  my $ip   = $fields{hidden}{field}{origip}{inputvalue}{1};
  my $time = $fields{hidden}{field}{origtime}{inputvalue}{1};
  my @dataFields = qw( inputvalue termidvalue );
  my @pgcommands;
  foreach my $group (keys %fields) {
    my $amount = $fields{$group}{multi};
    for my $i (1 .. $amount) {
      foreach my $field (keys %{ $fields{$group}{field} }) {
        foreach my $dataField (@dataFields) {
          if ($fields{$group}{field}{$field}{$dataField}{$i}) { 
            my $fieldInfo = qq($group\t$field\t$i\t$dataField);
            my $value = $fields{$group}{field}{$field}{$dataField}{$i};
            push @pgcommands, qq(INSERT INTO frm_user_save VALUES ('$ip', '$time', '$datatype', '$fieldInfo', '$value')); } } } } }
  foreach my $pgcommand (@pgcommands) {
#     print qq($pgcommand<br/>\n);
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
  my $saveUrl = "allele_phenotype.cgi?action=Load&user_ip=$ip&time=$time";
  print qq(Bookmark this <a href="$saveUrl">link</a> to load it in the future.<br/>\n);
} # sub saveFormData




sub showFormOLD {
  print qq(<div style="border: solid; position: fixed; top: 95px; right: 20px; width: 350px; z-index:2; background-color: white;"><div id="term_info" style="margin: 5px 5px 5px 5px;">Click on green question marks or start typing in a specific field to see more information here.</div></div>\n);
  &showEditorActions();
#   print qq(Should you have additional questions you can find guidelines <a href="/~acedb/draciti/Micropublication/Guidelines.htm" target="new">here</a>.<br/><br/>\n);
#   print qq(<span style="color: red">M</span> mandatory field. <span style="color: #06C729">A</span> fill at least one of these fields.<br/><br/>\n);
#   print qq(<table border="1">);
# HIDE
  print qq(<table border="0">);
  print qq(<form method="post" action="allele_phenotype.cgi" enctype="multipart/form-data">);
  my $input_size = '60';
  my $cols_size  = '100';
  my $rows_size  = '5';
  my $colspan    = '1';
  my $freeForced = 'forced';

  &printPerson();

#   tie %{ $fields{person}{field} }, "Tie::IxHash";
#   $fields{person}{multi}                                                     = '1';
#   $fields{person}{field}{person}{type}                                       = 'ontology';
#   $fields{person}{field}{person}{label}                                      = 'Your Name';
#   $fields{person}{field}{person}{group}                                      = 'person';
#   $fields{person}{field}{person}{terminfo}                                   = qq(If you do not have a WBPerson ID please <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi" target="new">contact</a> WormBase to have one assigned.);
#   $fields{person}{field}{person}{mandatory}                                  = 'mandatory';
#   $fields{person}{field}{person}{oamulti}                                    = 'multi';
#   $fields{person}{field}{person}{ontology_type}                              = 'WBPerson';
#   $fields{person}{field}{person}{pg}{'pic'}                                  = 'contact';
#   $fields{person}{field}{person}{pg}{'exp'}                                  = 'contact';
#   $fields{person}{field}{person}{pg}{'cns'}                                  = 'person';
#   tie %{ $fields{email}{field} }, "Tie::IxHash";
#   $fields{email}{multi}                                                      = '1';
#   $fields{email}{field}{email}{type}                                         = 'text';
#   $fields{email}{field}{email}{label}                                        = 'Your e-mail address';
#   $fields{email}{field}{email}{example}                                      = 'help@wormbase.org';
#   $fields{email}{field}{email}{group}                                        = 'email';
#   $fields{email}{field}{email}{mandatory}                                    = 'mandatory';
#   $fields{email}{field}{email}{oamulti}                                      = 'single';
#   $fields{email}{field}{email}{pg}{'pic'}                                    = 'email';
#   $fields{email}{field}{email}{pg}{'exp'}                                    = 'email';

# #   tie %{ $fields{person}{field} }, "Tie::IxHash";
#   $fields{person}{multi}                                      = '1';
#   $fields{person}{type}                                       = 'ontology';
#   $fields{person}{label}                                      = 'Your Name';
#   $fields{person}{terminfo}                                   = qq(If you do not have a WBPerson ID please <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi" target="new">contact</a> WormBase to have one assigned.);
#   $fields{person}{mandatory}                                  = 'mandatory';
#   $fields{person}{oamulti}                                    = 'multi';
#   $fields{person}{ontology_type}                              = 'WBPerson';
#   $fields{person}{pg}{'app'}                                  = 'contact';
# #   tie %{ $fields{email}{field} }, "Tie::IxHash";
#   $fields{email}{multi}                                       = '1';
#   $fields{email}{type}                                        = 'text';
#   $fields{email}{label}                                       = 'Your e-mail address';
#   $fields{email}{example}                                     = 'bob@example.com';
#   $fields{email}{group}                                       = 'email';
#   $fields{email}{mandatory}                                   = 'mandatory';
#   $fields{email}{oamulti}                                     = 'single';
#   $fields{email}{pg}{'app'}                                   = 'email';

#   foreach my $field (keys %fields) {
#     my $amount = $fields{$field}{multi};
#     for my $i (1 .. $amount) {
#       my $group_style = ''; if ($i > 1) { $group_style = 'display: none'; }
#       if ($i < $fields{$field}{hasdata} + 2) { $group_style = ''; }
#       my $isHiddenField = 0;
#       my $trToPrint = qq(<tr id="group_${i}_${field}" style="$group_style">\n);
# 
#         my $fieldclass = ''; my $placeholder = ''; my $terminfo = '';
# #         my $mandatoryvalue = ''; my $mandatoryclass = '';
# #         if ($fields{$field}{mandatory}) { 
# #           $mandatoryclass = 'class="' . $mandatoryToClass{$fields{$field}{mandatory}} . '"';
# #           $mandatoryvalue = $mandatoryToLabel{$fields{$field}{mandatory}}; }
# 
#         my $label = $fields{$field}{label};
#         my $labelTdColspan = qq(colspan="1"); 
#         my $minwidth = '200px'; if ($fields{$field}{minwidth}) { $minwidth = $fields{$field}{minwidth}; }
#         my $labelTdStyle = qq(style="min-width:$minwidth");
#         $trToPrint .= qq(<td $fieldclass $labelTdColspan $labelTdStyle>&nbsp;&nbsp;$label $terminfo</td>);
#         my $inputvalue  = ''; my $termidvalue = ''; 
#         if ($fields{$field}{defaultvalue})    { $inputvalue  = $fields{$field}{defaultvalue}; }	# default value
#         if ($fields{$field}{inputvalue}{$i})  { $inputvalue  = $fields{$field}{inputvalue}{$i}; }	# previous form value
#         if ($fields{$field}{termidvalue}{$i}) { $termidvalue = $fields{$field}{termidvalue}{$i}; }
# 
#         if ($i == 1) {						# on the first row, show the field information for javascript
#           $trToPrint .= qq(<input type="hidden" class="fields" value="$field" />\n);
#           my $data = '{ ';                                                    # data is { 'tag' : 'value', 'tag2' : 'value2' } format javascript stuff
#           foreach my $tag (sort keys %{ $fields{$field} }) {
#             my $tag_value = $fields{$field}{$tag};
#             next if ($tag eq 'pg');				# hash 
#             next if ($tag eq 'terminfo');			# has commas and other bad characters
#             if ($tag eq 'radio') { $tag_value = join" ", sort keys %{ $fields{$field}{$tag} }; }
#             $data .= "'$tag' : '$tag_value', "; }
#           $data .= "'multi' : '$amount', ";
#           $data =~ s/, $/ }/;
#           $trToPrint .= qq(<input type="hidden" id="data_$field" value="$data" />\n);
#         } # if ($i == 1)
# 
# #         $trToPrint .= qq(<td id="mandatory_${i}_$field" $mandatoryclass>$mandatoryvalue</td>\n);
#         if ($fields{$field}{colspan}) { $colspan = $fields{$field}{colspan}; }
#         my $group = $field;
#         if ($fields{$field}{type} eq 'ontology') { 
#             my $td_ontology = &showEditorOntology($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced);
#             $trToPrint .= $td_ontology; }
#           elsif ($fields{$field}{type} eq 'bigtext') { 
#             my $td_bigtext .= &showEditorBigtext($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $cols_size, $rows_size );
#             $trToPrint .= $td_bigtext; }
#           elsif ($fields{$field}{type} eq 'upload') { 
#             my $td_upload .= &showEditorUpload($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
#             $trToPrint .= $td_upload; }
#           elsif ($fields{$field}{type} eq 'radio') { 
#             my $td_radio .= &showEditorRadio($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
#             $trToPrint .= $td_radio; }
#           elsif ($fields{$field}{type} eq 'checkbox') { 
#             my $td_checkbox .= &showEditorCheckbox($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
#             $trToPrint .= $td_checkbox; }
#           elsif ($fields{$field}{type} eq 'hidden') { 
#             $isHiddenField++;
#             print qq(<input name="input_${i}_$field" id="input_${i}_$field" type="hidden" value="$inputvalue">\n); }
#           elsif ($fields{$field}{type} eq 'spacer') { 1; }		# not a real field
#           else {
#             my $td_text .= &showEditorText($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
#             $trToPrint .= $td_text; }
# 
#       $trToPrint .= qq(</tr>\n);
#       unless ($isHiddenField) { print $trToPrint; }
#   } }

  foreach my $group (keys %fields) {
    my $amount = $fields{$group}{multi};
    for my $i (1 .. $amount) {
      my $group_style = ''; if ($i > 1) { $group_style = 'display: none'; }
      if ($i < $fields{$group}{hasdata} + 2) { $group_style = ''; }
#       my @class; my $class = '';
#       if ( $fields{$group}{class} ) { 
#         foreach (@{ $fields{$group}{class} } ) { push @class, $_; } }
#       if (scalar @class > 0) { $class = join " ", @class; $class = qq(class="$class"); }
      my $isHiddenField = 0;
#       my $trToPrint = qq(<tr id="group_${i}_${group}" $class style="$group_style">\n);
      my $trToPrint = qq(<tr id="group_${i}_${group}" style="$group_style">\n);
# TO HIDE, don't show group and counter
#       $trToPrint   .= qq(<td>$group $i</td>\n);
      foreach my $field (keys %{ $fields{$group}{field} }) {
        if ($i == 1) {						# on the first row, show the field information for javascript
          $trToPrint .= qq(<input type="hidden" class="fields" value="$field" />\n);
          my $data = '{ ';                                                    # data is { 'tag' : 'value', 'tag2' : 'value2' } format javascript stuff
          foreach my $tag (sort keys %{ $fields{$group}{field}{$field} }) {
            my $tag_value = $fields{$group}{field}{$field}{$tag};
            next if ($tag eq 'pg');				# hash 
            next if ($tag eq 'terminfo');			# has commas and other bad characters
            if ($tag eq 'radio') { $tag_value = join" ", sort keys %{ $fields{$group}{field}{$field}{$tag} }; }
            $data .= "'$tag' : '$tag_value', "; }
          $data .= "'multi' : '$amount', ";
          $data =~ s/, $/ }/;
#   $fields{method}{field}{method}{group}                                      = 'method';
#   tie %{ $fields{method}{field}{method}{radio} }, "Tie::IxHash";
#   $fields{method}{field}{method}{radio}{transgene}                           = 'Existing Transgene';
#   $fields{method}{field}{method}{radio}{construct}                           = 'New Transgene';
          $trToPrint .= qq(<input type="hidden" id="data_$field" value="$data" />\n);
#           print qq(<input type="hidden" id="$field" value="$group"/>\n); 
        } # if ($i == 1)

        my $fieldclass = ''; my $placeholder = ''; my $terminfo = '';
#         my $mandatoryvalue = ''; my $mandatoryclass = ''; 
#         if ($fields{$group}{field}{$field}{mandatory}) { 
#           $mandatoryclass = 'class="' . $mandatoryToClass{$fields{$group}{field}{$field}{mandatory}} . '"';
#           $mandatoryvalue = $mandatoryToLabel{$fields{$group}{field}{$field}{mandatory}}; }
        if ($fields{$group}{field}{$field}{supergroup}) { 
          $fieldclass = 'class="' . $fieldToClass{$fields{$group}{field}{$field}{supergroup}} . '"'; }
        if ($fields{$group}{field}{$field}{example})  { $placeholder = qq(placeholder="$fields{$group}{field}{$field}{example}"); }
        if ($fields{$group}{field}{$field}{terminfo}) {    
          my $terminfo_text = $fields{$group}{field}{$field}{terminfo}; my $terminfo_title = $fields{$group}{field}{$field}{terminfo};
          if ($fields{$group}{field}{$field}{terminfo} eq 'obo') {
            my $obo_table = $fields{$group}{field}{$field}{ontology_type} . '_name_' . $fields{$group}{field}{$field}{ontology_table};
            $result = $dbh->prepare( "SELECT $obo_table FROM $obo_table ORDER BY $obo_table" ); $result->execute(); my @terminfo_text;
            while (my @row = $result->fetchrow()) { push @terminfo_text, $row[0]; } 
            $terminfo_title = join"\n",    @terminfo_text;
            $terminfo_text  = join"<br/>", @terminfo_text; }
          $terminfo_text  =~ s/'/&#8217;/g; $terminfo_text  =~ s/"/&quot;/g; 
          $terminfo_title =~ s/'/&#8217;/g; $terminfo_title =~ s/"/&quot;/g; $terminfo_title =~ s/<.*?>//g;
          $terminfo = qq(<span style="color: #06C729; font-weight: bold;" title="$terminfo_title" onclick="document.getElementById('term_info').innerHTML = '$terminfo_text';">?</span>); }
        my $label = $fields{$group}{field}{$field}{label};

        my $inputvalue  = ''; my $termidvalue = ''; 
        if ($fields{$group}{field}{$field}{defaultvalue})    { $inputvalue  = $fields{$group}{field}{$field}{defaultvalue}; }	# default value
        if ($fields{$group}{field}{$field}{inputvalue}{$i})  { $inputvalue  = $fields{$group}{field}{$field}{inputvalue}{$i}; }	# previous form value
        if ($fields{$group}{field}{$field}{termidvalue}{$i}) { $termidvalue = $fields{$group}{field}{$field}{termidvalue}{$i}; }
        my $labelTdColspan = qq(colspan="1"); 
#         my $labelTdStyle = '';
        my $minwidth = '200px'; if ($fields{$group}{field}{$field}{minwidth}) { $minwidth = $fields{$group}{field}{$field}{minwidth}; }
        my $labelTdStyle = qq(style="min-width:$minwidth");
        if ($fields{$group}{field}{$field}{type} eq 'spacer') {
          my @styleAttributes = ( 'vertical-align: bottom', 'font-weight: bold' );
           if ($fields{$group}{field}{$field}{height})   { push @styleAttributes, qq(height: $fields{$group}{field}{$field}{height}); }
           if ($fields{$group}{field}{$field}{fontsize}) { push @styleAttributes, qq(font-size: $fields{$group}{field}{$field}{fontsize}); }
           my $styleAttributes = join"; ", @styleAttributes;
           $labelTdStyle = qq(style="$styleAttributes");
#            $labelTdColspan = qq(colspan="6");
           $labelTdColspan = qq(colspan="8"); }
#         $trToPrint .= qq(<td $fieldclass $labelTdColspan $labelTdStyle>&nbsp;&nbsp;$label $terminfo</td>);
        $trToPrint .= qq(<td $fieldclass $labelTdColspan $labelTdStyle>&nbsp;&nbsp;$label $terminfo</td>);
#         $trToPrint .= qq(<td id="mandatory_${i}_$field" $mandatoryclass>$mandatoryvalue</td>\n);
        if ($fields{$group}{field}{$field}{colspan}) { $colspan = $fields{$group}{field}{$field}{colspan}; }
        if ($fields{$group}{field}{$field}{type} eq 'ontology') { 
            my $td_ontology = &showEditorOntology($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced);
            $trToPrint .= $td_ontology; }
          elsif ($fields{$group}{field}{$field}{type} eq 'bigtext') { 
            my $td_bigtext .= &showEditorBigtext($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $cols_size, $rows_size );
            $trToPrint .= $td_bigtext; }
          elsif ($fields{$group}{field}{$field}{type} eq 'upload') { 
            my $td_upload .= &showEditorUpload($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
            $trToPrint .= $td_upload; }
          elsif ($fields{$group}{field}{$field}{type} eq 'radio') { 
            my $td_radio .= &showEditorRadio($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
            $trToPrint .= $td_radio; }
          elsif ($fields{$group}{field}{$field}{type} eq 'checkbox') { 
            my $td_checkbox .= &showEditorCheckbox($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
            $trToPrint .= $td_checkbox; }
          elsif ($fields{$group}{field}{$field}{type} eq 'hidden') { 
            $isHiddenField++;
            print qq(<input name="input_${i}_$field" id="input_${i}_$field" type="hidden" value="$inputvalue">\n); }
          elsif ($fields{$group}{field}{$field}{type} eq 'spacer') { 1; }		# not a real field
          else {
            my $td_text .= &showEditorText($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder);
            $trToPrint .= $td_text; }
      } # foreach my $field (keys %{ $fields{$group}{field} })
#       my $td_term_info = $i . '_terminfo_' . $group;
#       print qq(<td id="$td_term_info" rowspan="20" style="display: none"></td>\n);
      $trToPrint .= qq(</tr>\n);
      unless ($isHiddenField) { print $trToPrint; }
    } # for my $i (1 .. $amount)
  } # foreach my $field (keys %fields)

  print qq(<tr><td>&nbsp;</td></tr>\n);
  print qq(<tr><td>&nbsp;</td></tr>\n);
  print qq(</form>);
  print qq(</table>);
  &showEditorActions();
} # sub showFormOLD


sub showEditorCheckbox {						# only for disclaimer so far
  my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder) = @_;
  my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  my $checkboxvalue = $fields{$group}{field}{$field}{checkboxvalue};
  my $checkboxtext  = $fields{$group}{field}{$field}{checkboxtext};
  my $checked       = ''; if ($inputvalue eq $checkboxvalue) { $checked = qq(checked="checked"); }
  $table_to_print  .= qq(<input type="checkbox" id="checkbox_${i}_${field}" name="input_${i}_$field" value="$checkboxvalue" $fieldclass $checked/> $checkboxtext<br/>);
  $table_to_print   .= "</td>\n";
  return $table_to_print;
} # sub showEditorCheckbox

sub showEditorRadio {
  my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder) = @_;
  my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
#   if ( $termidvalue ) {							# termid_<i>_<field> holds a previously uploaded file
#     $table_to_print .= qq(chosen upload <input name="termid_${i}_$field" id="termid_${i}_$field" readonly="readonly" value="$termidvalue"> select new to replace : \n); }
  foreach my $radio_value (keys %{ $fields{$group}{field}{$field}{radio} }) {
    my $radio_label = $fields{$group}{field}{$field}{radio}{$radio_value};
    my $checked     = ''; if ($inputvalue eq $radio_value) { $checked = qq(checked="checked"); }
    $table_to_print   .= qq(<input type="radio" id="radio_${i}_${field}_$radio_value" name="input_${i}_$field" value="$radio_value" $fieldclass $checked/>$radio_label<br/>);	# input_<i>_<field> is for new or replacement upload
  }
  $table_to_print   .= "</td>\n";
  return $table_to_print;
} # sub showEditorRadio

sub showEditorUpload {
  my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder) = @_;
  my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300

  if ( $termidvalue ) {							# termid_<i>_<field> holds a previously uploaded file
#     $table_to_print .= qq(chosen upload <input name="termid_${i}_$field" id="termid_${i}_$field" readonly="readonly" value="$termidvalue">);
    $table_to_print .= qq(<input type="hidden" name="termid_${i}_$field" id="termid_${i}_$field" readonly="readonly" value="$termidvalue">);
    $table_to_print .= qq(select new to replace : \n); }
  $table_to_print   .= qq(<input type="file" id="input_${i}_$field" name="input_${i}_$field" $fieldclass />);	# input_<i>_<field> is for new or replacement upload
  $table_to_print   .= "</td>\n";
  return $table_to_print;
} # sub showEditorUpload

sub showEditorBigtext {
  my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $cols_size, $rows_size) = @_;
  unless ($cols_size) { $cols_size = $input_size; }
  unless ($rows_size) { $rows_size = '20'; }
  my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  $table_to_print .= qq(<input id="input_${i}_$field" name="input_${i}_$field" size="$input_size" value="$inputvalue" $fieldclass>\n);
  $table_to_print .= qq(<div id="container_bigtext_${i}_$field"><textarea id="textarea_bigtext_${i}_$field" rows="$rows_size" cols="$cols_size" style="display:none">$inputvalue</textarea></div>\n);
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorBigtext

sub showEditorText {
  my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced) = @_;
  my $readonly = ''; if ($fields{$group}{field}{$field}{type} eq 'readonly') { $readonly = qq(readonly="readonly"); }
  my $inputsize = qq(size="40"); if ($fields{$group}{field}{$field}{inputsize}) { $inputsize = qq(size="$fields{$group}{field}{$field}{inputsize}"); }
  return qq(<td width="$input_size"><input name="input_${i}_$field" id="input_${i}_$field" $inputsize $readonly $fieldclass $placeholder value="$inputvalue"></td>\n);
} # sub showEditorText

sub showEditorOntology {
  my ($count, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced) = @_;
  $input_size -= 20;
#   my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  my $table_to_print = qq(<td style="min-width:300px" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  $table_to_print .= qq(<span id="container${freeForced}${count}${field}AutoComplete">\n);
  $table_to_print .= qq(<div id="${freeForced}${count}${field}AutoComplete" class="div-autocomplete">\n);
    # when blurring ontology fields, if it's been deleted by user, make the corresponding termid field also blank.
  my $onBlur = qq(if (document.getElementById('input_${count}_$field').value === '') { document.getElementById('termid_${count}_$field').value = ''; });
  $table_to_print .= qq(<input id="input_${count}_$field"  name="input_${count}_$field" value="$inputvalue"  size="$input_size" $fieldclass $placeholder onBlur="$onBlur">\n);
# HIDE
#   $table_to_print .= qq(<input id="termid_${count}_$field" name="termid_${count}_$field" value="$termidvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<input type="hidden" id="termid_${count}_$field" name="termid_${count}_$field" value="$termidvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<div id="${freeForced}${count}${field}Container"></div></div></span>\n);
  $table_to_print .= qq(</td>\n);
  return $table_to_print;
} # sub showEditorOntology

sub getAnyWBGeneTermInfo {
  my ($userValue) = @_;
  my ($joinkey) = $userValue =~ m/WBGene(\d+)/; my $to_print;   # has to match a WBGene from the info
  my %syns; my $locus; my $dead;
  $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey = '$joinkey';" ); $result->execute();
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey = '$joinkey';" ); $result->execute();
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$joinkey';" ); $result->execute();
  my @row = $result->fetchrow(); $locus = $row[1];
  $result = $dbh->prepare( "SELECT * FROM gin_dead WHERE joinkey = '$joinkey';" ); $result->execute();
  @row = $result->fetchrow(); $dead = $row[1];
  if ($userValue) { $to_print .= "id: WBGene$joinkey<br />\n"; }
  my $wormbase_link = "http://www.wormbase.org/species/c_elegans/gene/WBGene$joinkey;class=Gene";
  if ($locus) { $to_print .= "locus: <a target=\"new\" href=\"$wormbase_link\">$locus</a><br />\n"; }
  if ($dead) { $to_print .= "DEAD: $dead<br />\n"; }
  foreach my $syn (sort keys %syns) { $to_print .= "synonym: $syn<br />\n"; }

  $result = $dbh->prepare( "SELECT * FROM con_desctext WHERE joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene ~ 'WBGene$joinkey') AND joinkey IN (SELECT joinkey FROM con_desctype WHERE con_desctype = 'Concise_description')" ); $result->execute(); @row = $result->fetchrow();
  if ($row[1]) { $to_print .= "Concise description: $row[1]<br />\n"; }
  $result = $dbh->prepare( "SELECT * FROM con_desctext WHERE joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene ~ 'WBGene$joinkey') AND joinkey IN (SELECT joinkey FROM con_desctype WHERE con_desctype = 'Automated_concise_description')" ); $result->execute(); @row = $result->fetchrow();
  if ($row[1]) { $to_print .= "Automated_concise description: $row[1]<br />\n"; }
  $result = $dbh->prepare( "SELECT * FROM dis_diseaserelevance WHERE joinkey IN (SELECT joinkey FROM dis_wbgene WHERE dis_wbgene ~ 'WBGene$joinkey')" ); $result->execute(); @row = $result->fetchrow();
  if ($row[1]) { $to_print .= "Disease relevance : $row[1]<br />\n"; }

  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBGeneTermInfo

sub getAnyWBTransgeneTermInfo {
  my ($userValue) = @_; my %joinkeys;
  $result = $dbh->prepare( "SELECT * FROM trp_name WHERE trp_name = '$userValue' ORDER BY trp_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( trp_mergedinto trp_publicname trp_synonym trp_paper trp_summary trp_remark trp_reporter_type trp_driven_by_gene );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $userValue<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) {
    if ($table eq 'trp_paper') {
        my @papers = split/","/, $entry; foreach my $pap (@papers) {
          my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
      elsif ($table eq 'trp_driven_by_gene') {
        my (@genes) = $entry =~ m/WBGene(\d+)/g;
        foreach my $gene (@genes) {
          my $gene_row = "trp_driven_by_gene: WBGene$gene";
          my @tables = qw( gin_locus gin_seqname gin_synonyms );
          foreach my $table (@tables) {
            my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$gene';" ); $result2->execute();
            while (my @row2 = $result2->fetchrow) { $gene_row .= ", $row2[1]"; } }
          $gene_row .= "<br />\n";
          $to_print .= "$gene_row"; } }
      else { 
        my $label = $table; $label =~ s/^trp_//; ($label) = ucfirst($label);
        $to_print .= "${label}: $entry<br />\n"; } } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBTransgeneTermInfo

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

sub getAnyWBGeneAutocomplete {
  my ($words) = @_;
  my $lcwords = lc($words);
  my $max_results     = 40;
  # if ($words =~ m/^.{5,}/) { $max_results = 500; }		# Chris doesn't find this useful
  my $limit       = $max_results + 1;
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my @tables = qw( gin_locus gin_synonyms gin_seqname gin_wbgene );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' ORDER BY $table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id   = "WBGene" . $row[0];
      my $name = $row[1];
      if ($table eq 'gin_locus') { 
        my $elementText = qq($row[1] <span style='font-size:.75em'>( $id )</span>);
        my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$id" }); $matches{$matchData}++; 
      }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]' LIMIT $limit;" ); $result2->execute();
        my @row2 = $result2->fetchrow(); 
        if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) { 
          my $elementText = qq($name <span style='font-size:.75em'>( $id )</span>);
          my $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$id" }); $matches{$matchData}++; }
      } # if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') )
    } # while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) )
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND LOWER($table) !~ '^$lcwords' ORDER BY $table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id   = "WBGene" . $row[0];
      my $name = $row[1];
      if ($table eq 'gin_locus') { 
        my $elementText = qq($row[1] <span style='font-size:.75em'>( $id )</span>);
        my $matchData = qq({ "eltext" : "$elementText", "name": "$row[1]", "id": "$id" }); $matches{$matchData}++;
      }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]' LIMIT $limit;" ); $result2->execute();
        my @row2 = $result2->fetchrow(); 
        my $elementText = qq($name <span style='font-size:.75em'>( $id )</span>);
        my $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$id" }); $matches{$matchData}++; }
    } # while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) )
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { 
    my $matchData = qq({ "eltext": "more ...", "name": "", "id": "invalid value" }); 
    $t->Replace($max_results - 1, 'no value', $matchData); }
  my $matches = join", ", keys %matches;
  $matches = qq({ "results": [ $matches ] });
  return $matches;
} # sub getAnyWBGeneAutocomplete


