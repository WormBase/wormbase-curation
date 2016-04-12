#!/usr/bin/perl 

# Form to submit allele-sequence
#
# changed ip to come from header HTTP_X_REAL_IP if it exists.  2016 02 08




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
# my %mandatoryToClass;
# $mandatoryToClass{'transgene'}  = 'mandatory_method mandatory_method_transgene';
# $mandatoryToClass{'construct'}  = 'mandatory_method mandatory_method_construct';
# my %fieldToClass;
# $fieldToClass{'transgene'}  = 'field_method field_method_transgene';
# $fieldToClass{'construct'}  = 'field_method field_method_construct';

my $title = 'Allele Sequence form';
my ($header, $footer) = &cshlNew($title);
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
    elsif ($action eq 'asyncFieldCheck') {                   &asyncFieldCheck();    }
#     elsif ($action eq 'pmidToTitle') {                       &pmidToTitle();        }
#     elsif ($action eq 'preexistingData') {                   &preexistingData();    }
#     elsif ($action eq 'personPublication') {                 &personPublication();  }
#     elsif ($action eq 'emailFlagFirstpass') {                &emailFlagFirstpass(); }
#     elsif ($action eq 'bogusSubmission') {                   &bogusSubmission();    }
    else {                                                   &showStart();          }
}

sub checkAllele {					# only return allele code warning if both checks fail
  my ($input) = @_;
  my $checkResults = 'ok'; 
  unless ($input) { return $checkResults; }
  my $alleleDesignation = $input; 
  if ($input =~ m/^([a-zA-Z]+)\d+/) { ($alleleDesignation) = $1; }
  ($alleleDesignation) = lc($alleleDesignation);
  $result = $dbh->prepare( "SELECT * FROM obo_data_laboratory WHERE obo_data_laboratory ~ 'Allele_designation: \"$alleleDesignation\"';" );
  $result->execute(); my @row = $result->fetchrow();
  unless ($row[1]) { return qq(<span style='color: red'>WARNING!  The allele code '$alleleDesignation' you have entered is not recognized by WormBase. Please correct the allele code or request a new code by e-mailing <a href='mailto:genenames\@wormbase.org'>genenames\@wormbase.org</a></span>); }
  $result = $dbh->prepare( "SELECT * FROM obo_name_variation WHERE obo_name_variation = '$input';" );
  $result->execute(); my @row = $result->fetchrow();
  unless ($row[1]) { return qq(<span style='color: brown'>Notice: The allele name '$input' that you have entered is not recognized by WormBase. If '$input' is a new allele, please continue your submission and a WormBase curator will contact you to confirm.</span>); }
#   my @warnings;
#   if (scalar @warnings > 0) { $checkResults = join"<br/>\n", @warnings; }
  return $checkResults;
} # sub checkAllele

sub asyncFieldCheck {
  print "Content-type: text/plain\n\n";
  ($var, my $field)   = &getHtmlVar($query, 'field');
  ($var, my $input)   = &getHtmlVar($query, 'input');
  my $checkResults = 'ok';
  if ($field eq 'allele') {      ($checkResults) = &checkAllele($input); }
#     elsif ($field eq 'pmid') {   ($checkResults) = &checkPmid($input);   }	# not on allele-sequence form
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
    $result->execute(); my @row = $result->fetchrow();
    unless ($row[1]) {
      my $name_table = 'obo_name_' . $obotable;
      $result = $dbh->prepare( "SELECT * FROM $data_table WHERE joinkey IN (SELECT joinkey FROM $name_table WHERE $name_table = '$joinkey');" );
      $result->execute(); @row = $result->fetchrow(); }
#     unless ($row[1]) { return ''; }
    unless ($row[1]) { return qq(Term '$termid' is not recognized.); }
    my (@data) = split/\n/, $row[1];
    foreach my $data_line (@data) {
      if ($data_line =~ /id: WBVar\d+/) {                  $data_line =~ s/(WBVar\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/c_elegans\/variation\/${1}#01234567--10\" target=\"new\">$1<\/a>/; }
      if ($data_line =~ /gene: "WBGene\d+ /) {             $data_line =~ s/(WBGene\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/c_elegans\/gene\/${1}#04--10\" target=\"new\">$1<\/a>/; }
      if ($data_line =~ /id : <\/span> WBPhenotype:\d+/) { $data_line =~ s/(WBPhenotype:\d+)/<a href=\"http:\/\/www.wormbase.org\/species\/all\/phenotype\/${1}#036--10\" target=\"new\">$1<\/a>/; }
      if ($data_line =~ /^(.*?(?:child|parent) : <\/span> )<a href.*?>(.*?)<\/a>/) { $data_line =~ s/^(.*?(?:child|parent) : <\/span> )<a href.*?>(.*?)<\/a>/${1}${2}/; }	# remove hyperlinks for parent + child (for phenotype)
      next if ($data_line =~ m/<span/);			# some already have bold span in the data
      $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
    my $data = join"<br />\n", @data;
    if ($field eq 'allele') { 
      my ($wbvarid) = $row[1] =~ m/id: (WBVar\d+)/; 
      my $wbvar_link = qq(<a href="http://www.wormbase.org/species/c_elegans/variation/${wbvarid}#01234567--10" target="new" style="font-weight: bold; text-decoration: underline;">here</a>);
      $data = qq(Click $wbvar_link to see what is known about this allele<br/>\n) . $data; }
    return $data;
  } # if ($joinkey)
} # sub getGenericOboTermInfo

sub getAnySpecificTermInfo {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {               ($matches) = &getAnyWBPersonTermInfo($userValue);    }
    elsif ($ontology_type eq 'WBGene') {            ($matches) = &getAnyWBGeneTermInfo($userValue);      }
#   elsif ($ontology_type eq 'WBTransgene') {       ($matches) = &getAnyWBTransgeneTermInfo($userValue); }
  return $matches;
} # sub getAnySpecificTermInfo

sub getAnyWBPersonTermInfo {
  my ($userValue) = @_;
  my $person_id = $userValue; my $standard_name; my $to_print;
#   my $standard_name = $userValue; my $person_id; my $to_print;
#   if ($userValue =~ m/(.*?) \( (.*?) \)/) { $standard_name = $1; $person_id = $2; } else { $person_id = $userValue; }
  my $joinkey = $person_id; $joinkey =~ s/WBPerson/two/g;
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$joinkey' ORDER BY two_timestamp DESC;" );
  $result->execute(); my @row = $result->fetchrow();
  my %emails; if ($row[2]) { $standard_name = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = '$joinkey';" );
  $result->execute(); while (my @row = $result->fetchrow) { if ($row[2]) { $emails{$row[2]}++; } }
  ($joinkey) = $joinkey =~ m/(\d+)/;
  my $id = 'WBPerson' . $joinkey;
  if ($id) { $to_print .= qq(id: <a href="http://www.wormbase.org/resources/person/${person_id}#03--10" target="new">$id</a><br />\n); }
  if ($standard_name) { $to_print .= "name: $standard_name<br />\n"; }
  my $first_email = '';
  foreach my $email (sort keys %emails ) {
    unless ($first_email) { $first_email = $email; }
    $to_print .= "email: <a href=\"javascript:void(0)\" onClick=\"window.open('mailto:$email')\">$email</a><br />\n"; }
  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = '$id' ;" ); $result->execute();
  while (my @row = $result->fetchrow) { if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) {  # all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
#   $to_print = qq(Click <a href="allele_sequence.cgi?action=personPublication&personId=${person_id}&personName=${standard_name}&personEmail=${first_email}" target="new" style="font-weight: bold; text-decoration: underline;">here</a> to review your publications and see which are in need of allele-sequence curation<br/>\n) . $to_print;

#   ($var, $personId)      = &getHtmlVar($query, 'personId');		# WBPerson ID
#   ($var, $personName)    = &getHtmlVar($query, 'personName');		# WBPerson Name
#   ($var, $personEmail)   = &getHtmlVar($query, 'personEmail');		# email address
  return $to_print;
} # sub getAnyWBPersonTermInfo

sub getAnyWBGeneTermInfo {
  my ($userValue) = @_;
  my ($joinkey) = $userValue =~ m/WBGene(\d+)/; my $to_print;   # has to match a WBGene from the info
  my %syns; my %seqname; my $locus; my $dead;
  $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey = '$joinkey';" ); $result->execute();
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey = '$joinkey';" ); $result->execute();
  while (my @row = $result->fetchrow) { $seqname{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$joinkey';" ); $result->execute();
  my @row = $result->fetchrow(); $locus = $row[1];
  $result = $dbh->prepare( "SELECT * FROM gin_dead WHERE joinkey = '$joinkey';" ); $result->execute();
  @row = $result->fetchrow(); $dead = $row[1];
  if ($userValue) { $to_print .= "id: WBGene$joinkey<br />\n"; }
  my $wormbase_link = "http://www.wormbase.org/species/c_elegans/gene/WBGene$joinkey;class=Gene";
  if ($locus) { $to_print .= "locus: <a target=\"new\" href=\"$wormbase_link\">$locus</a><br />\n"; }
  if ($dead) { $to_print .= "DEAD: $dead<br />\n"; }
  foreach my $seqname (sort keys %seqname) { $to_print .= "sequence name: $seqname<br />\n"; }
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

sub getPmidTermInfo {
  my ($userInput) = @_;
#   my ($var, $userInput)      = &getHtmlVar($query, 'pmids');                # what user enter as pmids
  if ($userInput =~ m/^\s+/) { $userInput =~ s/^\s+//; }
  if ($userInput =~ m/\s+$/) { $userInput =~ s/\s+$//; }
  my $pap_link = $userInput;
  my $pmid     = $userInput;
  my $toPrint  = '';
  if ($userInput) { $toPrint  = qq(PubMed ID '$userInput' not recognized.); }
  if ($userInput =~ m/^pmid:?(\d+)/i) { $pmid = $1; }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier = 'pmid$pmid';" );
  $result->execute(); my @row = $result->fetchrow(); if ($row[0]) { 
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
  my $lcwords = lc($words);
  my @tabletypes = qw( name syn data );
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  foreach my $tabletype (@tabletypes) {			# first match all types as exact match (case insensitive)
    my $obotable = 'obo_' . $tabletype . '_' . $ontology_table;
    my $column   = $obotable; if ($tabletype eq 'data') { $column = 'joinkey'; }          # use joinkey for ID instead of data
    $result = $dbh->prepare( "SELECT * FROM $obotable WHERE LOWER($column) = '$lcwords' $query_modifier ORDER BY $column LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" });
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM $oboname_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); $result2->execute();
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
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" });
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM $oboname_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); $result2->execute();
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
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" });
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM $oboname_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); $result2->execute();
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
    elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneAutocomplete($words);      }
#   elsif ($ontology_type eq 'WBTransgene') {     ($matches) = &getAnyWBTransgeneAutocomplete($words); }
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
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );          # then match anywhere in the name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY joinkey LIMIT $limit;" );               # then match by WBPerson number
    $result->execute();
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



sub showStart {
  print "Content-type: text/html\n\n";
  print $header;
#   print qq(<span style="font-size: 24pt; text-decoration: underline;">Allele-Sequence Form</span><br/><br/>\n);
#   print qq(<span>Welcome to the WormBase Allele-Sequence form!<br/>We would greatly appreciate any allele-sequence data that you have for us.<br/>Please fill out the form below.<br/>If you have any questions, please do not hesitate to contact WormBase at <a href="mailto:help\@wormbase.org">help\@wormbase.org</a></span><br/><br/>\n);
  print qq(<span style="font-size: 24pt;">Contribute allele-sequence details</span><br/><br/>\n);
  print qq(<span>We would appreciate your help in adding allele-sequence data to WormBase.<br/>Please fill out the form below. All fields with a <span style="color: red;">*</span> are required.<br/>If you have any questions, please do not hesitate to contact WormBase at <a href="mailto:genenames\@wormbase.org">genenames\@wormbase.org</a></span><br/><br/>\n);
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
  my $mandatory = '';
  if ($fields{$field}{mandatory}) { $mandatory = '<span style="color: red;">*</span>'; }
  return qq(<td align="right" $labelTdColspan $labelTdStyle>&nbsp;&nbsp;$mandatory $label $terminfo</td>);
} # sub printEditorLabel

sub printEditorWarnings {
  my ($i, $field) = @_;
  ($var, my $warningvalue)  = &getHtmlVar($query, "input_warnings_${i}_$field");
#   if ($field eq 'person') {				# person field has a notice linking to their publications
#     if ($fields{person}{termidvalue}{1}) { 
#       my $person_id = $fields{person}{termidvalue}{1}; my $person_name = ''; my $person_email = '';
#       if ($fields{person}{inputvalue}{1}) { $person_name  = $fields{person}{inputvalue}{1}; }
#       if ($fields{email}{inputvalue}{1})  { $person_email = $fields{email}{inputvalue}{1};  }
#       $warningvalue = qq(Click <a href='allele_sequence.cgi?action=personPublication&personId=${person_id}&personName=${person_name}&personEmail=${person_email}' target='new' style='font-weight: bold; text-decoration: underline;'>here</a> to review your publications and see which are in need of allele-sequence curation<br/>\n); } }
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


sub printTrSpacer {          print qq(<tr><td style="border: none;">&nbsp;</td></tr>\n); }

sub printTrHeader {
  my ($header, $colspan, $fontsize, $message, $message_colour, $message_fontsize) = @_;
  print qq(<tr><td colspan="$colspan" style="font-size: $fontsize;">\n);
  my $header_with_javascript = $header;
  if ($header eq 'Optional') {
    $header_with_javascript = qq(<span id="optional_down_span" style="display: none;" onclick="document.getElementById('optional_down_span').style.display='none'; document.getElementById('optional_right_span').style.display=''; document.getElementById('group_1_allelenature').style.display='none'; document.getElementById('group_1_allelefunction').style.display='none'; document.getElementById('group_1_penetrance').style.display='none'; document.getElementById('group_1_tempsens').style.display='none'; document.getElementById('group_1_comment').style.display='none'; document.getElementById('group_1_linkotherform').style.display='none'; document.getElementById('group_1_optionalexplain').style.display='none';" ><div id="optional_down_image" style="background-position: -40px 0; background-image: url('http://${hostfqdn}/~azurebrd/images/triangle_down_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_down_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_down_reversed.png)';" onmouseout="document.getElementById('optional_down_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_down_plain.png)';"></div>$header</span>);
    $header_with_javascript .= qq(<span id="optional_right_span" onclick="document.getElementById('optional_down_span').style.display=''; document.getElementById('optional_right_span').style.display='none'; document.getElementById('group_1_allelenature').style.display=''; document.getElementById('group_1_allelefunction').style.display=''; document.getElementById('group_1_penetrance').style.display=''; document.getElementById('group_1_tempsens').style.display=''; document.getElementById('group_1_comment').style.display=''; document.getElementById('group_1_linkotherform').style.display=''; document.getElementById('group_1_optionalexplain').style.display='';" ><div id="optional_right_image" style="background-position: -40px 0; background-image: url('http://${hostfqdn}/~azurebrd/images/triangle_right_plain.png'); height: 20px; width:20px; float: left;" onmouseover="document.getElementById('optional_right_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_right_reversed.png)';" onmouseout="document.getElementById('optional_right_image').style.backgroundImage='url(http://${hostfqdn}/~azurebrd/images/triangle_right_plain.png)';"></div>$header</span>);
  } # if ($header eq 'Optional')
  my $message_span = '';
  if ($message) { $message_span = qq(<span style="color: $message_colour; font-size: $message_fontsize;">$message</span>); }
  print qq(<span id="header_$header" style="font-weight: bold;">$header_with_javascript $message_span<span>);
  print qq(</td></tr>\n);
} # sub printTrHeader

sub printPersonField {                   printArrayEditorNested('person');              }
sub printEmailField {                    printArrayEditorNested('email');               }
sub printPmidField {                     printArrayEditorNested('pmid');                }
sub printAlleleField {                   printArrayEditorNested('allele');              }
sub printGeneField {                     printArrayEditorNested('gene');                }
sub printSeqnameField {                  printArrayEditorNested('seqname');             }
sub printTypeAlterationField {           printArrayEditorNested('typealteration');      }
sub printAlterationDetailsField {        printArrayEditorNested('alterationdetails');   }
sub printTypeMutationField {             printArrayEditorNested('typemutation');        }
sub printMutationDetailsField {          printArrayEditorNested('mutationdetails');     }
sub printUpstreamField {                 printArrayEditorNested('upstream');            }
sub printDownstreamField {               printArrayEditorNested('downstream');          }
sub printStrainField {                   printArrayEditorNested('strain');              }
sub printGenotypeField {                 printArrayEditorNested('genotype');            }
sub printMutagenField {                  printArrayEditorNested('mutagen');             }
sub printForwardField {                  printArrayEditorNested('forward');             }
sub printReverseField {                  printArrayEditorNested('reverse');             }
sub printCommentField {                  printArrayEditorNested('comment');             }

sub checkIpBlock {
  my ($ip) = @_;
  $result = $dbh->prepare( "SELECT * FROM frm_ip_block WHERE frm_ip_block = '$ip';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow();
  if ($row[0]) { return 1; } else { return 0; }
} # sub checkIpBlock

sub showForm {
  my $ip = &getIp();
  my ($goodOrBad) = &checkIpBlock($ip);
  return if $goodOrBad;
  print qq(<form method="post" action="allele_sequence.cgi" enctype="multipart/form-data">);
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


  &printTrHeader('General', '20', '16px', "", '#aaaaaa', '12px');
  &printPersonField();
  &printEmailField();
  &printPmidField();
  &printAlleleField();
  &printGeneField();
  &printSeqnameField();
  &printTrSpacer();
  &printTrHeader('Sequence Data', '20', '16px', "", '#aaaaaa', '12px');
  &printTypeAlterationField();
  &printAlterationDetailsField();
  &printTypeMutationField();
  &printMutationDetailsField();
  &printTrHeader('&nbsp;&nbsp;&nbsp;&nbsp;Flanking Sequences', '20', '12px', "", '#aaaaaa', '12px');
  &printUpstreamField();
  &printDownstreamField();
  &printTrSpacer();
  &printTrHeader('Origin', '20', '16px', "", '#aaaaaa', '12px');
  &printStrainField();
  &printGenotypeField();
  &printTrSpacer();
  &printTrHeader('Isolation', '20', '16px', "", '#aaaaaa', '12px');
  &printMutagenField();
  &printForwardField();
  &printReverseField();
  &printTrSpacer();
  &printTrHeader('Comment', '20', '16px', "", '#aaaaaa', '12px');
  &printCommentField();

#   &printObsPhenotypeField();
#   &printPhenontLink();
#   &printShowObsSuggestLink();
#   &printObsSuggestField();
#   &printNotPhenotypeField();
#   &printPhenontLink();
#   &printShowNotSuggestLink();
#   &printNotSuggestField();
#   &printTrSpacer();
#   &printTrSpacer();
#   &printTrHeader('Optional', '20', '18px', "(inheritance pattern, mutation effect, penetrance, temperature sensitivity and general comments)", '#aaaaaa', '12px');
#   &printOptionalExplanation();
#   &printAlleleNatureField();
#   &printAlleleFunctionField();
#   &printPenetranceField();
#   &printTempSensField();
#   &printLinkToOtherForm();
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
  print qq(<span style="font-size: 24pt;">Contribute allele-sequence details</span><br/><br/>\n);

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
      $result->execute(); my @row = $result->fetchrow();
      if ($row[0]) { $fields{allele}{termidvalue}{1} = $row[0]; } } }
    
  my $form_data  = qq(<table border="1" cellpadding="5">);
  $form_data    .= &tableDisplayArray('person'); 
  $form_data    .= &tableDisplayArray('email');  
  $form_data    .= &tableDisplayArray('pmid');   
  $form_data    .= &tableDisplayArray('allele'); 
  $form_data    .= &tableDisplayArray('gene'); 
  $form_data    .= &tableDisplayArray('seqname'); 
  $form_data    .= &tableDisplayArray('typealteration'); 
  $form_data    .= &tableDisplayArray('alterationdetails'); 
  $form_data    .= &tableDisplayArray('typemutation'); 
  $form_data    .= &tableDisplayArray('mutationdetails'); 
  $form_data    .= &tableDisplayArray('upstream'); 
  $form_data    .= &tableDisplayArray('downstream'); 
  $form_data    .= &tableDisplayArray('strain'); 
  $form_data    .= &tableDisplayArray('genotype'); 
  $form_data    .= &tableDisplayArray('mutagen'); 
  $form_data    .= &tableDisplayArray('forward'); 
  $form_data    .= &tableDisplayArray('reverse'); 
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
#           $form_data = qq(Dear $fields{person}{inputvalue}{1}, thank you for submitting Allele-Sequence data.<br/>A WormBase curator will be in touch if there are any questions<br/><br/>) . $form_data;			# prepend thank you message
          my $messageToUser = qq(Dear $fields{person}{inputvalue}{1}, thank you for submitting Allele-Sequence data.<br/>A WormBase curator will be in touch if there are any questions.<br/>);
          print qq($messageToUser<br/>);
          print qq(<br/>$form_data);
          print qq(<br/>Return to the <a href="allele_sequence.cgi">Allele-Sequence Form</a>.<br/>\n);
          my $user = 'allele_sequence_form@' . $hostfqdn;	# who sends mail
#           my $email = 'cgrove@caltech.edu, maryann.tuli@wormbase.org ';
          my $email = 'genenames@wormbase.org';
#           my $email = 'azurebrd@tazendra.caltech.edu';
#           my $email = 'closertothewake@gmail.com';
          $email   .= ", $fields{email}{inputvalue}{1}";
          my $subject = 'Allele-Sequence confirmation';		# subject of mail
          my $body = $messageToUser;					# message to user shown on form
#           $body .= qq(Click <a href='http://${hostfqdn}/~azurebrd/cgi-bin/forms/allele_sequence.cgi?action=bogusSubmission&pgids=$newPgids&ipAddress=$ip' target='_blank' style='font-weight: bold; text-decoration: underline;'>here</a> if you did not submit this data.<br/><br/>\n);	# additional link to report false data
          $body .= $form_data;						# form data
#         UNCOMMENT send general emails
          &mailSendmail($user, $email, $subject, $body);

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




sub checkMandatoryFields {
  my $mandatoryFail    = 0;
  my $aphenotypeExists = 0;
  foreach my $field (keys %fields) {
    if ($fields{$field}{'mandatory'}) { 
      unless ($fields{$field}{hasdata}) { 
        $mandatoryFail++;
        print qq(<span style="color:red">$fields{$field}{label} is mandatory.</span><br/>\n); } } }
# for 'any' fields
#   unless ( ($fields{obsphenotype}{hasdata}) || ($fields{obssuggested}{hasdata}) || ($fields{notphenotype}{hasdata}) || ($fields{notsuggested}{hasdata}) ) {
#         $mandatoryFail++;
#         print qq(<span style="color:red">At least one phenotype is mandatory.</span><br/>\n); }
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
  $fields{pmid}{haschecks}                                    = 'pmid';	# on allele-sequence just to load term info
  $fields{pmid}{terminfo}                                     = qq(Enter the PubMed ID for the paper in which this allele sequence data was published. If your paper does not have a PubMed ID, please enter any unique identifier, like a D.O.I. (e.g. doi 10.1038/ni.2957));
  $fields{pmid}{example}                                      = 'e.g. 4366476 (Please enter only one ID)';
#   $fields{pmid}{mandatory}                                    = 'mandatory';
#   tie %{ $fields{allele}{field} }, "Tie::IxHash";
  $fields{allele}{multi}                                      = '1';
  $fields{allele}{type}                                       = 'ontology';
  $fields{allele}{label}                                      = 'Allele Name';
  $fields{allele}{freeForced}                                 = 'free';
  $fields{allele}{ontology_type}                              = 'obo';
  $fields{allele}{ontology_table}                             = 'variation';
  $fields{allele}{example}                                    = 'e.g. e1000';
  $fields{allele}{haschecks}                                  = 'allele';
  $fields{allele}{terminfo}                                   = qq(Enter the name of a single allele for which you are providing sequence data. Once you have started typing, select an allele from the list of known alleles. If you are entering an allele not recognized by WormBase, continue with your submission and a WormBase curator will contact you to confirm the new allele.);
  $fields{allele}{matchstartonly}                             = 'matchstartonly';
  $fields{allele}{mandatory}                                  = 'mandatory';

#   tie %{ $fields{gene}{field} }, "Tie::IxHash";
  $fields{gene}{multi}                                        = '1';
  $fields{gene}{type}                                         = 'ontology';
  $fields{gene}{label}                                        = 'Gene Name';
  $fields{gene}{example}                                      = 'e.g. lin-3';
  $fields{gene}{mandatory}                                    = 'mandatory';
  $fields{gene}{ontology_type}                                = 'WBGene';
#   tie %{ $fields{seqname}{field} }, "Tie::IxHash";
  $fields{seqname}{multi}                                    = '1';
  $fields{seqname}{type}                                     = 'text';
  $fields{seqname}{label}                                    = 'Sequence Name';
  $fields{seqname}{terminfo}                                 = qq(CDS);
  $fields{seqname}{example}                                  = 'e.g. B0303.3';
#   $fields{seqname}{mandatory}                                = 'mandatory';

#   tie %{ $fields{typealteration}{field} }, "Tie::IxHash";
  $fields{typealteration}{multi}                              = '1';
  $fields{typealteration}{type}                               = 'dropdown';
  $fields{typealteration}{label}                              = 'Type of Alteration';
#   $fields{typealteration}{terminfo}                           = qq(If applicable, choose the inheritance pattern of the allele with respect to the phenotype(s) entered.);
  $fields{typealteration}{mandatory}                          = 'mandatory';
#   tie %{ $fields{alterationdetails}{field} }, "Tie::IxHash";
  $fields{alterationdetails}{multi}                           = '1';
  $fields{alterationdetails}{type}                            = 'text';
  $fields{alterationdetails}{label}                           = 'Alteration Details';
  $fields{alterationdetails}{terminfo}                        = qq(Point: e.g. c to t OR c to ag<br/>Transposon: e.g. Tc1<br/>Sequence insertion: Inserted sequence<br/>Sequence deletion: Leave blank<br/>Deletion + Insertion: Inserted sequence<br/>Complex alterations: Use Comment field);
#   $fields{alterationdetails}{example}                         = '';
#   $fields{alterationdetails}{mandatory}                       = 'mandatory';
#   tie %{ $fields{typemutation}{field} }, "Tie::IxHash";
  $fields{typemutation}{multi}                                = '1';
  $fields{typemutation}{type}                                 = 'dropdown';
  $fields{typemutation}{label}                                = 'Type of Mutation';
#   $fields{typemutation}{terminfo}                             = qq(If applicable, choose the inheritance pattern of the allele with respect to the phenotype(s) entered.);
#   $fields{typemutation}{mandatory}                            = 'mandatory';
#   tie %{ $fields{mutationdetails}{field} }, "Tie::IxHash";
  $fields{mutationdetails}{multi}                             = '1';
  $fields{mutationdetails}{type}                              = 'text';
  $fields{mutationdetails}{label}                             = 'Mutation Details';
  $fields{mutationdetails}{terminfo}                          = qq(Missense: e.g. Q(200)R<br/>Nonsense: e.g. Q(200)Ochre OR W(340)Opal<br/>Silent: e.g. cag -> caa<br/>Splice-site: e.g. gt -> at or ag to aa<br/>Frameshift: Leave blank);
#   $fields{mutationdetails}{example}                           = '';
#   $fields{mutationdetails}{mandatory}                         = 'mandatory';

#   tie %{ $fields{upstream}{field} }, "Tie::IxHash";
  $fields{upstream}{multi}                                    = '1';
  $fields{upstream}{type}                                     = 'text';
  $fields{upstream}{label}                                    = '30 bp upstream';
  $fields{upstream}{terminfo}                                 = qq(It is only necessary to enter longer flanking sequences if 30bp is not a unique sequence e.g. in a highly repetitive or duplicated region.);
#   $fields{upstream}{example}                                  = '';
  $fields{upstream}{mandatory}                                = 'mandatory';
#   tie %{ $fields{downstream}{field} }, "Tie::IxHash";
  $fields{downstream}{multi}                                    = '1';
  $fields{downstream}{type}                                     = 'text';
  $fields{downstream}{label}                                    = '30 bp downstream';
  $fields{downstream}{terminfo}                                 = qq(It is only necessary to enter longer flanking sequences if 30bp is not a unique sequence e.g. in a highly repetitive or duplicated region.);
#   $fields{downstream}{example}                                  = '';
  $fields{downstream}{mandatory}                                = 'mandatory';

#   tie %{ $fields{strain}{field} }, "Tie::IxHash";
  $fields{strain}{multi}                                        = '1';
  $fields{strain}{type}                                         = 'text';
  $fields{strain}{label}                                        = 'Strain';
  $fields{strain}{terminfo}                                     = qq(Strain in which the allele is maintained, e.g. TR1417. If CGC strain, genotype can be omitted);
  $fields{strain}{example}                                      = 'e.g. TR1417';
#   $fields{strain}{mandatory}                                    = 'mandatory';
#   tie %{ $fields{genotype}{field} }, "Tie::IxHash";
  $fields{genotype}{multi}                                      = '1';
  $fields{genotype}{type}                                       = 'text';
  $fields{genotype}{label}                                      = 'Genotype';
#   $fields{genotype}{terminfo}                                   = qq();
  $fields{genotype}{example}                                    = 'e.g. smg-1 (r904) unc-54 (r293) I';
#   $fields{genotype}{mandatory}                                  = 'mandatory';
#   tie %{ $fields{mutagen}{field} }, "Tie::IxHash";
  $fields{mutagen}{multi}                                       = '1';
  $fields{mutagen}{type}                                        = 'text';
  $fields{mutagen}{label}                                       = 'Mutagen';
  $fields{mutagen}{terminfo}                                    = qq();
  $fields{mutagen}{example}                                     = 'e.g. EMS, ENU, TMP/UV';
#   $fields{mutagen}{mandatory}                                   = 'mandatory';
#   tie %{ $fields{forward}{field} }, "Tie::IxHash";
  $fields{forward}{multi}                                       = '1';
  $fields{forward}{type}                                        = 'text';
  $fields{forward}{label}                                       = 'Forward genetics';
#   $fields{forward}{terminfo}                                    = qq(e.g. standard phenotypic screen.);
  $fields{forward}{example}                                     = qq(e.g. standard phenotypic screen);
#   $fields{forward}{mandatory}                                   = 'mandatory';
#   tie %{ $fields{reverse}{field} }, "Tie::IxHash";
  $fields{reverse}{multi}                                       = '1';
  $fields{reverse}{type}                                        = 'text';
  $fields{reverse}{label}                                       = 'Reverse genetics';
  $fields{reverse}{terminfo}                                    = qq(e.g. directed screen for mutations in a particular gene, using e.g. PCR or Tilling);
  $fields{reverse}{example}                                     = 'e.g. PCR';
#   $fields{reverse}{mandatory}                                   = 'mandatory';

#   tie %{ $fields{comment}{field} }, "Tie::IxHash";
  $fields{comment}{multi}                                     = '1';
  $fields{comment}{type}                                      = 'textarea';
  $fields{comment}{label}                                     = 'Comment';
#   $fields{comment}{startHidden}                               = 'startHidden';

  tie %{ $dropdown{typealteration} }, "Tie::IxHash";
  $dropdown{typealteration}{"Point Mutation"}                 = "Point / dinucleotide mutation";
  $dropdown{typealteration}{"Transposon Insertion"}           = "Transposon Insertion";
  $dropdown{typealteration}{"Insertion"}                      = "Sequence insertion";
  $dropdown{typealteration}{"Deletion"}                       = "Sequence deletion";
  $dropdown{typealteration}{"Insertion + Deletion"}           = "Deletion + insertion";
  $dropdown{typealteration}{"Complex Alteration"}             = "Complex alterations";
  tie %{ $dropdown{typemutation} }, "Tie::IxHash";
  $dropdown{typemutation}{"Missense"}                         = "Missense ";
  $dropdown{typemutation}{"Nonsense"}                         = "Nonsense ";
  $dropdown{typemutation}{"Silent"}                           = "Silent ";
  $dropdown{typemutation}{"Splice-site"}                      = "Splice-site ";
  $dropdown{typemutation}{"Frameshift"}                       = "Frameshift ";
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
<script type="text/javascript" src="http://${hostfqdn}/~azurebrd/javascript/allele_sequence.js"></script>
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
#   my $ip = $query->remote_host();			# set value for current user IP, not (potentially) loaded IP 
  my $ip = &getIp();
  my $twonum = $wbperson; $twonum =~ s/WBPerson/two/;
  $result = $dbh->do( "DELETE FROM two_user_ip WHERE two_user_ip = '$ip' ;" );
  $result = $dbh->do( "INSERT INTO two_user_ip VALUES ('$twonum', '$ip', '$submitter_email')" ); 
} # sub updateUserIp

sub getIp {
  my $ip            = $query->remote_host();                    # get value for current user IP, not (potentially) loaded IP
  my %headers = map { $_ => $query->http($_) } $query->http();
  if ($headers{HTTP_X_REAL_IP}) { $ip = $headers{HTTP_X_REAL_IP}; }
  return $ip;
} # sub getIp

sub getUserByIp {
#   my $ip = $query->remote_host();			# get user values based on current user IP, not (potentially) loaded IP
  my $ip = &getIp();
  my $twonum = ''; my $standardname = ''; my $email = ''; my $wbperson = '';
  $result = $dbh->prepare( "SELECT * FROM two_user_ip WHERE two_user_ip = '$ip';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[0]) { $twonum = $row[0]; $email = $row[2]; $wbperson = $row[0]; $wbperson =~ s/two/WBPerson/; }
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$twonum';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[2]) { $standardname = $row[2]; }
  return ($wbperson, $standardname, $email);
} # sub getUserByIp

sub mailSendmail {
  my ($user, $email, $subject, $body) = @_;
  my %mail;
  $mail{from}           = $user;
  $mail{to}             = $email;
  $mail{subject}        = $subject;
  $mail{body}           = $body;
  $mail{'content-type'} = 'text/html; charset="iso-8859-1"';
  sendmail(%mail) || print qq(<span style="color:red">Error, confirmation email failed</span> : $Mail::Sendmail::error<br/>\n);
} # sub mailSendmail


__END__
