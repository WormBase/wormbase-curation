#!/usr/bin/perl 

# Form to submit Micropublications

# http://wiki.wormbase.org/index.php/UP#mappings
#
# Some text changed from WormBase to WormBook for Daniela.  2015 11 02
#
# changed ip to come from header HTTP_X_REAL_IP if it exists.  2016 02 08
#
# Some text changed back to WormBase from WormBook for Daniela.  2016 04 19
#
# New possible fields for Antibody and Engineered Allele.  2017 03 14
#
# Some new fields and rearranging of their order.
# Cosmetic changes to required fields to a red * in front.
# No longer display A for anyanatomy, but keep requiring it.  2017 04 27
#
# Added In-situ detection method.  2017 05 05
#
# Added Karen to emails.  2017 05 15
#
# Added and removed raffle stuff for IWM.  2017 06 24




use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;
use Tie::IxHash;
use LWP::Simple;
use File::Basename;		# fileparse
use File::Path qw( make_path );
use File::Copy qw(copy);
use Mail::Sendmail;
use Net::Domain qw(hostname hostfqdn hostdomain);

my $hostname    = hostname();
my $hostdomain  = hostdomain();  unless ($hostdomain) { $hostdomain = 'caltech.edu'; }	# tazendra doesn't have dnsdomainname set
my $hostfqdn    = $hostname . '.' . $hostdomain;
# my $hostfqdn    = hostfqdn();		# tazendra has this set to just the hostname, so it doesn't work

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $result;




my $query = new CGI;
my %fields;
tie %fields, "Tie::IxHash";

my %mandatoryToLabel;
$mandatoryToLabel{'mandatory'}  = '<span style="color: red">*</span>';
# $mandatoryToLabel{'anyanatomy'} = '<span style="color: #06C729">A</span>';	# no longer label them separately since it has its own section  2017 04 27
$mandatoryToLabel{'anyanatomy'} = '';	# no longer label them separately since it has its own section  2017 04 27
$mandatoryToLabel{'internal'}   = '<span style="color: grey">I</span>';
$mandatoryToLabel{'optional'}   = '';
$mandatoryToLabel{'antibody'}   = '';
$mandatoryToLabel{'insitu'}     = '';
$mandatoryToLabel{'allele'}     = '';
$mandatoryToLabel{'transgene'}  = '';
$mandatoryToLabel{'construct'}  = '';
$mandatoryToLabel{'rtpcr'}      = '';
# $mandatoryToLabel{'optional'}   = '<span style="color: black">O</span>';
# $mandatoryToLabel{'transgene'}  = '<span style="color: brown">T</span>';
# $mandatoryToLabel{'construct'}  = '<span style="color: orange">C</span>';
my %mandatoryToClass;
$mandatoryToClass{'transgene'}  = 'mandatory_method mandatory_method_transgene';
$mandatoryToClass{'construct'}  = 'mandatory_method mandatory_method_construct';
$mandatoryToClass{'antibody'}   = 'mandatory_method mandatory_method_antibody';
$mandatoryToClass{'insitu'}     = 'mandatory_method mandatory_method_insitu';
$mandatoryToClass{'allele'}     = 'mandatory_method mandatory_method_allele';
$mandatoryToClass{'rtpcr'}      = 'mandatory_method mandatory_method_rtpcr';
my %fieldToClass;
$fieldToClass{'transgene'}  = 'field_method field_method_transgene';
$fieldToClass{'construct'}  = 'field_method field_method_construct';
$fieldToClass{'antibody'}   = 'field_method field_method_antibody';
$fieldToClass{'allele'}     = 'field_method field_method_allele';
$fieldToClass{'insitu'}     = 'field_method field_method_insitu';
$fieldToClass{'rtpcr'}      = 'field_method field_method_rtpcr';

my $title = 'Micropublication form';
my ($header, $footer) = &cshlNew($title);
# $header = "<html><head></head>";
# $header .= qq(<img src="/~acedb/draciti/Micropublication/uP_logo.png"><br/>\n);		# logo for Daniela
$header .= qq(<span style="font-size: 24pt;">Micropublish gene expression results</span><br/><br/>\n);
# $header .= qq(<img src="http://${hostfqdn}/~acedb/draciti/Micropublication/uP_logo.bmp"><br/>\n);		# logo for Daniela
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
    elsif ($action eq 'Save for Later') {                    &submit('save');       }
    elsif ($action eq 'Load') {                              &load();               }
    elsif ($action eq 'autocompleteXHR') {                   &autocompleteXHR();    }
    elsif ($action eq 'asyncTermInfo') {                     &asyncTermInfo();      }
    else {                                                   &showStart();          }
}

sub asyncTermInfo {
  print "Content-type: text/plain\n\n";
  ($var, my $field)   = &getHtmlVar($query, 'field');
  ($var, my $termid)  = &getHtmlVar($query, 'termid');
  ($var, my $group)   = &getHtmlVar($query, 'group');
  my $matches;

  if ( $fields{$group}{field}{$field}{type} eq 'ontology' ) {
    ($matches) = &getAnyTermInfo($group, $field, $termid); }      # generic obo and specific are different
  print "$matches\n";
} # sub asyncTermInfo

sub getAnyTermInfo {                                                    # call  &getAnySpecificTermInfo  or  &getGenericOboTermInfo  as appropriate
  my ($group, $field, $termid) = @_; my $return_value = '';
  if ($fields{$group}{field}{$field}{ontology_type} eq 'obo') {
      ($return_value) = &getGenericOboTermInfo($group, $field, $termid); }
    else {
#         if ($termid =~ m/\( (.*?) \) /) { $termid = $1; }             # get the id from between the parenthesis
      my $ontology_type = $fields{$group}{field}{$field}{ontology_type};
      ($return_value) = &getAnySpecificTermInfo($ontology_type, $termid); }
  return $return_value;
} # sub getAnyTermInfo

sub getGenericOboTermInfo {
  my ($group, $field, $termid) = @_;
  my $obotable = $fields{$group}{field}{$field}{ontology_table};
  if ($termid =~ m/\[.*?\]$/) { $termid =~ s/\[.*?\]$//; }
#   my $joinkey;
#   if ($termid =~ m/\( (.*?) \) $/) { ($joinkey) = $termid =~ m/\( (.*?) \) $/; }
#     else { $joinkey = $termid; }             # get the joinkey from the drop-down itself
  my $joinkey = $termid;
  if ($joinkey) {
    my $data_table =  'obo_data_' . $obotable;
    $result = $dbh->prepare( "SELECT * FROM $data_table WHERE joinkey = '$joinkey';" );
    $result->execute(); my @row = $result->fetchrow();
    unless ($row[1]) { return ''; }
    my $data = $row[1]; $data =~ s/\n/<br \>\n/g;
    return $data; }
} # sub getGenericOboTermInfo

sub getAnySpecificTermInfo {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'WBGene') {               ($matches) = &getAnyWBGeneTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPerson') {          ($matches) = &getAnyWBPersonTermInfo($userValue); }
  elsif ($ontology_type eq 'WBTransgene') {       ($matches) = &getAnyWBTransgeneTermInfo($userValue); }

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
  elsif ($ontology_type eq 'WBSequence') {      ($matches) = &getAnyWBSequenceTermInfo($userValue); }
  return $matches;
} # sub getAnySpecificTermInfo

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

sub getAnyWBPersonTermInfo {
  my ($userValue) = @_;
  my $person_id = $userValue; my $standard_name; my $to_print;
#   my $standard_name = $userValue; my $person_id; my $to_print;
#   if ($userValue =~ m/(.*?) \( (.*?) \)/) { $standard_name = $1; $person_id = $2; } else { $person_id = $userValue; }
  $person_id =~ s/WBPerson/two/g;
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$person_id' ORDER BY two_timestamp DESC;" );
  $result->execute(); my @row = $result->fetchrow();
  my $joinkey = $row[0]; my %emails; if ($row[2]) { $standard_name = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = '$joinkey';" );
  $result->execute(); while (my @row = $result->fetchrow) { if ($row[2]) { $emails{$row[2]}++; } }
  ($joinkey) = $joinkey =~ m/(\d+)/;
  my $id = 'WBPerson' . $joinkey;
  if ($id) { $to_print .= "id: $id<br />\n"; }
  if ($standard_name) { $to_print .= "name: $standard_name<br />\n"; }
  foreach my $email (sort keys %emails ) {
    $to_print .= "email: <a href=\"javascript:void(0)\" onClick=\"window.open('mailto:$email')\">$email</a><br />\n"; }
  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = '$id' ;" ); $result->execute();
  while (my @row = $result->fetchrow) { if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) {  # all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBPersonTermInfo

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




sub autocompleteXHR {                                           # when typing in an autocomplete field xhr call to this CGI for values
  print "Content-type: text/plain\n\n";
  ($var, my $words) = &getHtmlVar($query, 'query');
  ($var, my $group) = &getHtmlVar($query, 'group');
  ($var, my $field) = &getHtmlVar($query, 'field');
  my $matches;
#   ($words) = lc($words);                                        # search insensitively by lowercasing query and LOWER column values
#   if ( ($fields{$datatype}{$field}{type} eq 'dropdown') || ($fields{$datatype}{$field}{type} eq 'multidropdown') ) {
#        ($matches) = &getAnySimpleAutocomplete($datatype, $field, $words); }
#   elsif ( ($fields{$datatype}{$field}{type} eq 'ontology') || ($fields{$datatype}{$field}{type} eq 'multiontology') ) {
#     if ($fields{$datatype}{$field}{ontology_type} eq 'obo') { ($matches) = &getGenericOboAutocomplete($datatype, $field, $words); }
#       else {
#         if ($configLoaded) {
#           my $ontology_type = $fields{$datatype}{$field}{ontology_type};
#           ($matches) = &getAnySpecificAutocomplete($ontology_type, $words); } } }

  if ( $fields{$group}{field}{$field}{type} eq 'ontology' ) {
    if ($fields{$group}{field}{$field}{ontology_type} eq 'obo') { ($matches) = &getGenericOboAutocomplete($group, $field, $words); }
      else {
        my $ontology_type = $fields{$group}{field}{$field}{ontology_type};
        ($matches) = &getAnySpecificAutocomplete($ontology_type, $words); } }
  print $matches;
} # sub autocompleteXHR

sub getGenericOboAutocomplete {
  my ($group, $field, $words) = @_;
  my $ontology_table = $fields{$group}{field}{$field}{ontology_table};
  my $max_results    = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $limit          = $max_results + 1;
  my $oboname_table  =  'obo_name_' . $ontology_table;
  my $obodata_table  =  'obo_data_' . $ontology_table;
  my $query_modifier = qq(AND joinkey NOT IN (SELECT joinkey FROM $obodata_table WHERE $obodata_table ~ 'is_obsolete') ); 
  if ($field eq 'goidcc') { $query_modifier .= qq(AND joinkey IN (SELECT joinkey FROM obo_data_goid WHERE obo_data_goid ~ 'cellular_component') ); }
  if ($words =~ m/\'/) { $words =~ s/\'/''/g; }
  my $lcwords = lc($words);
  my @tabletypes = qw( name syn data );
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  foreach my $tabletype (@tabletypes) {
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
  if ($ontology_type eq 'WBGene') {             ($matches) = &getAnyWBGeneAutocomplete($words);      }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonAutocomplete($words);    }
  elsif ($ontology_type eq 'WBTransgene') {     ($matches) = &getAnyWBTransgeneAutocomplete($words); }

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

sub getAnyWBGeneAutocomplete {
  my ($words) = @_;
  my $lcwords = lc($words);
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
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
#         $matches{"$row[1] ( $id ) "}++;
#         my $matchData = qq({ "name": "$row[1]", "id": "$id" }); $matches{$matchData}++;
#         my $matchData = qq({ "name": "$row[1] <font size=-4>( $id )</font>", "id": "$id" }); $matches{$matchData}++;
#         my $matchData = qq({ "name": "$row[1] <span style='font-size:.75em'>( $id )</span>", "id": "$id" }); $matches{$matchData}++; 
#         my $matchData = qq({ "eltext": "$row[1] <span style='font-size:.75em'>( $id )</span>", "name: $row[1]", "id": "$id" }); $matches{$matchData}++; 
        my $elementText = qq($row[1] <span style='font-size:.75em'>( $id )</span>);
        my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$id" }); $matches{$matchData}++; 
      }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]' LIMIT $limit;" ); $result2->execute();
        my @row2 = $result2->fetchrow(); 
#         my $locus_name = $row2[1]; unless ($locus_name) { $locus_name = $row[1]; }
        if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) { 
          my $elementText = qq($name <span style='font-size:.75em'>( $id )</span>);
          my $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$id" }); $matches{$matchData}++; }
#         if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') ) { 
#           $matches{"$row[1] ( $id ) \[$name\]"}++;
#           my $matchData = qq({ "name": "$row[1] [$name]", "id": "$id" }); $matches{$matchData}++;
#           my $elementText = qq($name <span style='font-size:.75em'>( $id )</span>);
#           my $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$id" }); $matches{$matchData}++; }
#         if ($table eq 'gin_wbgene') { 
#           $matches{"$name ( $id ) "}++;
#           my $matchData = qq({ "name": "$name", "id": "$id" }); $matches{$matchData}++;
#           my $elementText = qq($name <span style='font-size:.75em'>( $id )</span>);
#           my $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$id" }); $matches{$matchData}++; }
      } # if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') )
    } # while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) )
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND LOWER($table) !~ '^$lcwords' ORDER BY $table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id   = "WBGene" . $row[0];
      my $name = $row[1];
      if ($table eq 'gin_locus') { 
#         $matches{"$row[1] ( $id ) "}++;
#         my $matchData = qq({ "name": "$row[1]", "id": "$id" }); $matches{$matchData}++;
        my $elementText = qq($row[1] <span style='font-size:.75em'>( $id )</span>);
        my $matchData = qq({ "eltext" : "$elementText", "name": "$row[1]", "id": "$id" }); $matches{$matchData}++;
      }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]' LIMIT $limit;" ); $result2->execute();
        my @row2 = $result2->fetchrow(); 
#         my $locus_name = $row2[1]; unless ($locus_name) { $locus_name = $row[1]; }
        my $elementText = qq($name <span style='font-size:.75em'>( $id )</span>);
        my $matchData = qq({ "eltext": "$elementText", "name": "$name", "id": "$id" }); $matches{$matchData}++; }
#         if ( ($table eq 'gin_synonyms')|| ($table eq 'gin_seqname') ) { 
# #           $matches{"$row[1] ( $id ) \[$name\]"}++;
#           my $matchData = qq({ "name": "$row[1] [$name]", "id": "$id" }); $matches{$matchData}++; }
#         if ($table eq 'gin_wbgene') { $matches{"$name ( $id ) "}++; } } 
    } # while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) )
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
#   my $matches = join"\n", keys %matches;
  if (scalar keys %matches >= $max_results) { 
    my $matchData = qq({ "eltext": "<span style='font-style: italic; background-color: yellow;'>More matches exist; please be more specific</span>", "name": "", "id": "invalid value" });
    $t->Replace($max_results - 1, 'no value', $matchData); }
  my $matches = join", ", keys %matches;
  $matches = qq({ "results": [ $matches ] });
  return $matches;

#   $matches = qq({ "results": [ { "name": "abc-1", "id": "ID1" }, { "name": "abc-2", "id": "ID2" } ] });
#   print $matches;
} # sub autocompleteXHR

sub getAnyWBPersonAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $lcwords = lc($words);
  my $limit       = $max_results + 1;
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
#   my %invalidPersons;
#   my $result = $dbh->prepare( "SELECT * FROM two_status WHERE two_status = 'Invalid'" ); $result->execute();
#   while (my @row = $result->fetchrow()) { $invalidPersons{$row[0]}++; }
  my @tables = qw( two_standardname );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );      # match by start of name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
#       next if ($invalidPersons{$row[0]});		# skip invalid person objects on this form
#       my $invalid = ''; if ($invalidPersons{$row[0]}) { $invalid = ' INVALID'; }
#       $matches{"$row[2]$invalid ( $id ) "}++;
#       my $matchData = qq({ "name": "$row[2]$invalid", "id": "$id" }); $matches{$matchData}++;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );          # then match anywhere in the name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
#       next if ($invalidPersons{$row[0]});		# skip invalid person objects on this form
#       my $invalid = ''; if ($invalidPersons{$row[0]}) { $invalid = ' INVALID'; }
#       $matches{"$row[2]$invalid ( $id ) "}++;
#       my $matchData = qq({ "name": "$row[2]$invalid", "id": "$id" }); $matches{$matchData}++;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid' ORDER) BY joinkey LIMIT $limit;" );               # then match by WBPerson number
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
#       next if ($invalidPersons{$row[0]});		# skip invalid person objects on this form
#       my $invalid = ''; if ($invalidPersons{$row[0]}) { $invalid = ' INVALID'; }
#       $matches{"$row[2]$invalid ( $id ) "}++;
#       my $matchData = qq({ "name": "$row[2]$invalid", "id": "$id" }); $matches{$matchData}++;
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
#     $matches{"$row[1] ( $row[1] ) "}++; 
    my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[1] )</span>);
    my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[1]" }); $matches{$matchData}++; 
  }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND LOWER($table) !~ '^$lcwords' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
#     $matches{"$row[1] ( $row[1] ) "}++; 
    my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[1] )</span>);
    my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[1]" }); $matches{$matchData}++; 
  }
  my @tables = qw( trp_publicname trp_synonym );                        # used to have trp_paper, but would get lots of "WBPaperNNN","WBPaperNNN" in the dataTable, which looked misleading.  2010 09 28
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT trp_name.trp_name, ${table}.$table FROM trp_name, $table WHERE trp_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$lcwords' ORDER BY ${table}.$table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
#       $matches{"$row[1] ( $row[0] ) "}++; 
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" }); $matches{$matchData}++; 
    }
    $result = $dbh->prepare( "SELECT trp_name.trp_name, ${table}.$table FROM trp_name, $table WHERE trp_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$lcwords' AND LOWER(${table}.$table) !~ '^$lcwords' ORDER BY ${table}.$table LIMIT $limit;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
#       $matches{"$row[1] ( $row[0] ) "}++;
      my $elementText = qq($row[1] <span style='font-size:.75em'>( $row[0] )</span>);
      my $matchData = qq({ "eltext": "$elementText", "name": "$row[1]", "id": "$row[0]" }); $matches{$matchData}++; 
    }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { 
    my $matchData = qq({ "eltext": "<span style='font-style: italic; background-color: yellow;'>More matches exist; please be more specific</span>", "name": "", "id": "invalid value" });
    $t->Replace($max_results - 1, 'no value', $matchData); }
  my $matches = join", ", keys %matches;
  $matches = qq({ "results": [ $matches ] });
  return $matches;
} # sub getAnyWBTransgeneAutocomplete



sub showStart {
  print "Content-type: text/html\n\n";
  print $header;
  my $micropublish_terminfo = 'Micropublication- What is it?<br/>Not all data generated by funded research is incorporated in the scientific literature. This information often includes high quality novel findings and is unfortunately not readily available to the scientific community. This knowledge can instead be shared with the public in the form of an open-access micropublication. Once you submit this data to WormBase, it will be reviewed by one or more experts in the field. If approved, your data will be assigned a stable identifier (DOI), will be available on WormBase, and can be cited by traditional citation methods.';
  print qq(If you have unpublished gene expression data you can <span style="color: #06C729;" onclick="document.getElementById('term_info_box').style.display = ''; document.getElementById('term_info').innerHTML = '$micropublish_terminfo';">micropublish</span> it in WormBase and <a href="http://www.micropublication.org/" target="new">Micropublication:biology</a> by filling the form below.<br/>Your submission will be sent out for peer review and, if accepted, will be assigned a DOI -providing a citable reference.<br/>The form is mostly self explanatory and hints can be found by clicking green question marks.<br/>In the box on the right side of the page you can find additional tips/information that will appear when you start typing in specific fields.<br/>Should you have additional questions you can find guidelines <a href="http://${hostfqdn}/~acedb/draciti/Micropublication/Guidelines.htm" target="new">here</a>.<br/><br/>\n);
    # initialize originalIP + originalTime, processing uploads requires them. %fields processing will replace with form values from 'hidden' group before upload field(s).
  unless ($fields{hidden}{field}{origip}{inputvalue}{1}) {     $fields{hidden}{field}{origip}{inputvalue}{1}   = $query->remote_host(); }
  unless ($fields{hidden}{field}{origtime}{inputvalue}{1}) {   $fields{hidden}{field}{origtime}{inputvalue}{1} = time;                  }
    # if IP corresponds to an existing user, get person and email data
  unless ($fields{person}{field}{person}{termidvalue}{1}) {
    ( $fields{person}{field}{person}{termidvalue}{1}, $fields{person}{field}{person}{inputvalue}{1}, $fields{email}{field}{email}{inputvalue}{1} ) = &getUserByIp(); }
  &showForm();
  print $footer;
} # sub showStart

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
  print qq(<div id="term_info_box" style="border: solid; position: fixed; top: 90px; right: 20px; width: 350px; z-index:2; background-color: white;">);
  print qq(<div id="clear_term_info" align="right" onclick="document.getElementById('term_info_box').style.display = 'none';"><img id="close_term_info_image" src="http://${hostfqdn}/~azurebrd/images/x_plain.png" onmouseover="document.getElementById('close_term_info_image').src='http://${hostfqdn}/~azurebrd/images/x_reversed.png';" onmouseout="document.getElementById('close_term_info_image').src='http://${hostfqdn}/~azurebrd/images/x_plain.png';"></div>\n);
  print qq(<div id="term_info" style="margin: 5px 5px 5px 5px;">Click on <span style="color: #06C729; font-weight: bold;">?</span> green question marks or start typing in a specific field to see more information here.</div></div>\n);
#   print qq(<span style="color: red">*</span> mandatory field. <span style="color: #06C729">A</span> fill at least one of these fields.<br/><br/>\n);
  print qq(<span style="color: red">*</span> mandatory field.<br/><br/>\n);
#   print qq(<table border="1">);
# HIDE
  print qq(<table border="0">);
  print qq(<form method="post" action="expr_micropub.cgi" enctype="multipart/form-data">);
  &showEditorActions();
  my $input_size = '60';
  my $cols_size  = '100';
  my $rows_size  = '5';
  my $colspan    = '1';
  my $freeForced = 'forced';
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

        my $mandatoryvalue = ''; my $mandatoryclass = ''; my $fieldclass = ''; my $placeholder = ''; my $terminfo = '';
        if ($fields{$group}{field}{$field}{mandatory}) { 
          $mandatoryclass = 'class="' . $mandatoryToClass{$fields{$group}{field}{$field}{mandatory}} . '"';
          $mandatoryvalue = $mandatoryToLabel{$fields{$group}{field}{$field}{mandatory}}; }
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
          $terminfo = qq(<span style="color: #06C729; font-weight: bold;" title="$terminfo_title" onmouseover="this.style.cursor='pointer'" onclick="document.getElementById('term_info_box').style.display = ''; document.getElementById('term_info').innerHTML = '$terminfo_text';">?</span>); }
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
#   $trToPrint .= qq(<td><input name="mandatory_${count}_$field" id="mandatory_${count}_$field" type="hidden" value="$mandatoryvalue"></td>\n);
        $trToPrint .= qq(<td id="mandatory_${i}_$field" $mandatoryclass>$mandatoryvalue</td>\n);
        $trToPrint .= qq(<td $fieldclass $labelTdColspan $labelTdStyle>&nbsp;&nbsp;$label $terminfo</td>);
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
            my $readonly = '';
            if ($fields{$group}{field}{$field}{type} eq 'readonly') { $readonly = qq(readonly="readonly"); }
            $trToPrint .= qq(<td width="$input_size"><input name="input_${i}_$field" id="input_${i}_$field" $readonly $fieldclass $placeholder value="$inputvalue" style="background-color: #FFFFFF;"></td>\n);
#           my $exampleLabel = ''; 
#           $exampleLabel = qq(<label id="exampleLabel_${i}_$field" for="input_${i}_$field" style="position: absolute; top: 5px; left: 5px; display: inline; z-index: 99;">$fields{$group}{field}{$field}{example}</label>); 
#           $trToPrint .= qq(<td style="position: relative" width="$input_size">$exampleLabel<input name="input_${i}_$field" id="input_${i}_$field" $readonly $fieldclass value="$inputvalue" onClick="alert('pie'); document.getElementById('exampleLabel_${i}_$field').style.display = '';"></td>\n);
        }
      } # foreach my $field (keys %{ $fields{$group}{field} })
#       my $td_term_info = $i . '_terminfo_' . $group;
#       print qq(<td id="$td_term_info" rowspan="20" style="display: none"></td>\n);
      $trToPrint .= qq(</tr>\n);
      unless ($isHiddenField) { print $trToPrint; }
    } # for my $i (1 .. $amount)
  } # foreach my $field (keys %fields)
  print qq(<tr><td>&nbsp;</td></tr>\n);
  print qq(<tr><td>&nbsp;</td></tr>\n);
  &showEditorActions();
  print qq(</form>);
  print qq(</table>);
} # sub showForm

sub showEditorActions {
  print qq(<tr><td align="left" colspan="7">\n);
  print qq(<span style="font-weight: bold; font-size: 12pt">Clicking Submit will email you a confirmation :</span>\n);
  print qq(<input type="submit" name="action" value="Save for Later" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
  print qq(<input type="submit" name="action" value="Preview" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
  print qq(<input type="submit" name="action" value="Submit" onclick="return confirm('Are you sure you want to submit?')" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n);
  print qq(</td></tr>\n);
} # sub showEditorActions

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
  $table_to_print   .= qq(<input type="file" id="input_${i}_$field" name="input_${i}_$field" $fieldclass style="background-color: #FFFFFF;" />);	# input_<i>_<field> is for new or replacement upload
  $table_to_print   .= "</td>\n";
  return $table_to_print;
} # sub showEditorUpload

sub showEditorBigtext {
  my ($i, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $cols_size, $rows_size) = @_;
  unless ($cols_size) { $cols_size = $input_size; }
  unless ($rows_size) { $rows_size = '20'; }
  my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  $table_to_print .= qq(<input id="input_${i}_$field" name="input_${i}_$field" size="$input_size" value="$inputvalue" $fieldclass $placeholder style="background-color: #FFFFFF;">\n);
  $table_to_print .= qq(<div id="container_bigtext_${i}_$field"><textarea id="textarea_bigtext_${i}_$field" rows="$rows_size" cols="$cols_size" style="display:none">$inputvalue</textarea></div>\n);
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorBigtext

sub showEditorOntology {
  my ($count, $field, $group, $inputvalue, $termidvalue, $input_size, $colspan, $fieldclass, $placeholder, $freeForced) = @_;
  $input_size -= 20;
#   my $table_to_print = qq(<td width="300" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  my $table_to_print = qq(<td style="min-width:300px;" colspan="$colspan">\n);     # there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 300
  $table_to_print .= qq(<span id="container${freeForced}${count}${field}AutoComplete">\n);
  $table_to_print .= qq(<div id="${freeForced}${count}${field}AutoComplete" class="div-autocomplete">\n);
    # when blurring ontology fields, if it's been deleted by user, make the corresponding termid field also blank.
  my $onBlur = qq(if (document.getElementById('input_${count}_$field').value === '') { document.getElementById('termid_${count}_$field').value = ''; });
  $table_to_print .= qq(<input id="input_${count}_$field"  name="input_${count}_$field" value="$inputvalue"  size="$input_size" $fieldclass $placeholder style="background-color: #FFFFFF;" onBlur="$onBlur">\n);
# HIDE
#   $table_to_print .= qq(<input id="termid_${count}_$field" name="termid_${count}_$field" value="$termidvalue" size="40"          readonly="readonly">\n);
    # ontology fields have html values in input_i_field but are not from autocomplete object, so selectionenforce clears them.  store this parallel value, so if it gets cleared, it gets reloaded
  $table_to_print .= qq(<input type="hidden" id="termid_${count}_$field" name="termid_${count}_$field" value="$termidvalue" size="40"          readonly="readonly">\n);
#   $table_to_print .= qq(<input id="loaded_${count}_$field" name="loaded_${count}_$field" value="$inputvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<input type="hidden" id="loaded_${count}_$field" name="loaded_${count}_$field" value="$inputvalue" size="40"          readonly="readonly">\n);
  $table_to_print .= qq(<div id="${freeForced}${count}${field}Container"></div></div></span>\n);
  $table_to_print .= qq(</td>\n);
  return $table_to_print;
} # sub showEditorOntology

sub submit {
  my ($submit_flag) = @_;
  print "Content-type: text/html\n\n";
  print $header;
  my $tempImageFilename = '';				# temp file for preview and save-for-later
  my $form_data  = qq(<table border="0" cellpadding="5">);
  foreach my $group (keys %fields) {
    my $amount = $fields{$group}{multi};
    for my $i (1 .. $amount) {
#       my $group_style = ''; if ($i > 1) { $group_style = 'display: none'; }
#       print qq(<tr id="group_${i}_${group}" style="$group_style"><td>$group $i</td>\n);
      my $trHasvalue;					# row has data, needs to be shown
      my $trData;
      foreach my $field (keys %{ $fields{$group}{field} }) {
        my $label = $fields{$group}{field}{$field}{label};
        if ($fields{$group}{field}{$field}{type} eq 'upload') {
#             my ($filename, $imageUrl) = &processUpload($group, $i, $field, $label); 
#             my ($addToTr) = &processUpload($group, $i, $field, $label); 
            ($tempImageFilename) = &processUpload($group, $i, $field, $label); 
            if ($tempImageFilename) {
              $fields{$group}{field}{$field}{termidvalue}{$i} = $tempImageFilename;
              my $imageUrl = "http://" . $hostfqdn . "/~acedb/draciti/Micropublication/uploads/temp/$tempImageFilename";
              $trData .= qq(<td>$label</td><td><img width="400" src="$imageUrl"></td>\n); $trHasvalue++; } }
          else {
            my ($var, $inputvalue)  = &getHtmlVar($query, "input_${i}_$field");
            ($var, my $termidvalue) = &getHtmlVar($query, "termid_${i}_$field");
            my @inputtermidvalue;				# input + termid values
            if ($inputvalue) { 
              push @inputtermidvalue, $inputvalue;
              $fields{$group}{field}{$field}{inputvalue}{$i} = $inputvalue;
              if ($i > $fields{$group}{hasdata}) { $fields{$group}{hasdata} = $i; }
            }
            if ($termidvalue) { 
              unless ($termidvalue eq $inputtermidvalue[0]) {	# only add the ID if it's different from the name
                push @inputtermidvalue, $termidvalue; }
              $fields{$group}{field}{$field}{termidvalue}{$i} = $termidvalue;
              if ($i > $fields{$group}{hasdata}) { $fields{$group}{hasdata} = $i; }
            } # if ($termidvalue) 
            my $inputtermidvalue = join" -- ", @inputtermidvalue; 
#             if ($label) { $trData .= qq(<td>$label</td><td>$i</td><td>$inputtermidvalue</td>\n); }
            if ($label) { $trData .= qq(<td>$label</td><td>$inputtermidvalue</td>\n); }
            if ($inputtermidvalue) { $trHasvalue++; }	# if input or termid of any field in the group, row has data
          }
      } # foreach my $field (keys %{ $fields{$group}{field} })
      if ($trHasvalue) {
        $form_data .= qq(<tr>$trData</tr>\n); }
    } # for my $i (1 .. $amount)
  } # foreach my $group (keys %fields)
  $form_data  .= qq(</table><br/><br/>);

    # on any submission action, update the person / email for the user's IP address
  &updateUserIp( $fields{person}{field}{person}{termidvalue}{1}, $fields{email}{field}{email}{inputvalue}{1} );
    # if the form has no person id, try to load from postgres by ip address
  unless ($fields{person}{field}{person}{termidvalue}{1}) {
    ( $fields{person}{field}{person}{termidvalue}{1}, $fields{person}{field}{person}{inputvalue}{1}, $fields{email}{field}{email}{termidvalue}{1} ) = &getUserByIp(); }

  if ($submit_flag eq 'submit') { 
      my $mandatoryFail = &checkMandatoryFields();
      if ($mandatoryFail) { 
          print $form_data;
          &showForm(); }
        else {
          &deletePg($fields{hidden}{field}{origip}{inputvalue}{1}, $fields{hidden}{field}{origtime}{inputvalue}{1});
          $form_data = qq(Dear $fields{person}{field}{person}{inputvalue}{1}, thank you for submitting gene expression data. Your submission will be sent for peer-review. We will contact you after the evaluation is completed. If you have additional questions, please contact the <a href="mailto:contact\@micropublication.org">Micropublication Team</a>.<br/><br/>) . $form_data;			# prepend thank you message
          print qq(<br/>$form_data);
          print qq(<br/>Return to the <a href="expr_micropub.cgi">Micropublication Form</a>.);
          my $user = 'micropublication_form@tazendra.caltech.edu';	# who sends mail
          my $email = 'daniela.raciti@micropublication.org, karen.yook@micropublication.org';
#           my $email = 'draciti@caltech.edu, kyook@caltech.edu';
#           my $email = 'draciti@caltech.edu';
#           my $email = 'closertothewake@gmail.com';
#           my $email = 'azurebrd@tazendra.caltech.edu';
          $email   .= ", $fields{email}{field}{email}{inputvalue}{1}";
          my $subject = 'Micropublication confirmation';		# subject of mail
          my $body = $form_data . qq(<br/>\nIP ) . $query->remote_host();
# UNCOMMENT TO PROCESS
          &mailSendmail($user, $email, $subject, $body);
          &renameImageFile($tempImageFilename, $fields{person}{field}{person}{termidvalue}{1});
#           &writeFlatfile();						# write log to flatfile for raffle options
#           &writePg();							# not ready to write to postgres 2015 11 02
        }
    }
    elsif ($submit_flag eq 'preview') { 
      my $mandatoryFail = &checkMandatoryFields();
      print qq(<br/><b>Preview -</b> scroll down to continue filling out the form<br/><br/>\n);
      print $form_data;
      print qq(<br/><b>Preview -</b> Please review the data for your submission above. If you would like to make edits, please do so in the form below. If you are finished adding data to the form, please click Submit.<br/><br/>\n);
      &showForm();
    }
    elsif ($submit_flag eq 'save') { 
      &deletePg($fields{hidden}{field}{origip}{inputvalue}{1}, $fields{hidden}{field}{origtime}{inputvalue}{1});
      &saveFormData();
    }
} # sub submit

# sub writeFlatfile {
#   my $timestamp  = &getPgDate(); 
#   my $email      = $fields{email}{field}{email}{inputvalue}{1};
#   my $personname = $fields{person}{field}{person}{inputvalue}{1};
#   my $wbperson   = $fields{person}{field}{person}{termidvalue}{1};
#   my $raffle     = $fields{raffle}{field}{raffle}{inputvalue}{1};
#   my $historyFile = '/home/azurebrd/public_html/cgi-bin/data/expr_micropub.data';
#   open (OUT, ">>$historyFile") or die "Cannot append to $historyFile : $!";
#   print OUT qq($timestamp\t$raffle\t$wbperson\t$personname\t$email\n);
#   close (OUT) or die "Cannot close $historyFile : $!";
# } # sub writeFlatfile

sub writePg {							# not ready to write to postgres 2015 11 02
  my %curPgid = '';
  my @highestPgidTables = qw( name curator ); my @datatypes = qw(cns exp pic);
  foreach my $datatype (@datatypes) {
    my $pgUnionQuery = "SELECT MAX(joinkey::integer) FROM ${datatype}_" . join" UNION SELECT MAX(joinkey::integer) FROM ${datatype}_", @highestPgidTables;
    my $result = $dbh->prepare( "SELECT max(max) FROM ( $pgUnionQuery ) AS max; " );
    $result->execute(); my @row = $result->fetchrow(); my $highest = $row[0]; $curPgid{$datatype} = $highest; }
  foreach my $group (keys %fields) {
# print qq(group $group G<br>);
    my $amount = $fields{$group}{multi};
    foreach my $field (keys %{ $fields{$group}{field} }) {
      foreach my $oadatatype (keys %{ $fields{$group}{field}{$field}{pg} }) {
# print "G $group F $field OAD $oadatatype E<br>";
        foreach my $oatablename (keys %{ $fields{$group}{field}{$field}{pg}{$oadatatype} }) {
          my $pgtype  = $fields{$group}{field}{$field}{pg}{$oadatatype}{$oatablename};
# print "G $group F $field OAD $oadatatype PGT $pgtype E<br>";
          my $pgtable = ${oadatatype} . '_' . ${oatablename};
          my @pgdata; my $pgdata = '';
          for my $i (1 .. $amount) {
            if ( ($pgtype eq 'multiontology') || ($pgtype eq 'ontology') || ($pgtype eq 'upload') ) {
                if ($fields{$group}{field}{$field}{termidvalue}{$i}) {
# if ($group eq 'ceranatomy') { print qq(getting $group $field $i -> $fields{$group}{field}{$field}{termidvalue}{$i} END<br/>); }
# print qq(getting $group $field $i -> $fields{$group}{field}{$field}{termidvalue}{$i} END<br/>); 
                  push @pgdata, $fields{$group}{field}{$field}{termidvalue}{$i}; } }
              elsif ( ($pgtype eq 'multiontology') || ($pgtype eq 'ontology') ) {
                if ($fields{$group}{field}{$field}{inputvalue}{$i}) {
                  push @pgdata, $fields{$group}{field}{$field}{inputvalue}{$i}; } }
              elsif ( ($pgtype eq 'multiontology') || ($pgtype eq 'ontology') ) {
                push @pgdata, qq(invalid pgtype $pgtype for $group $field $i); }
          } # for my $i (1 .. $amount)
          if ($pgtype eq 'multiontology')                             { $pgdata = join'","', @pgdata; if ($pgdata) { $pgdata = '"' . $pgdata . '"'; } }
            elsif ( ($pgtype eq 'ontology') || ($pgtype eq 'image') ) { $pgdata = shift @pgdata;    }
            else                                                      { $pgdata = join'|', @pgdata; }
          if ($pgdata) {
            my $pgid = $curPgid{$oadatatype};
            print qq(INSERT INTO $pgtable VALUES ('$pgid', '$pgdata');<br/>);
          } # if ($pgdata)
        } # foreach my $oatablename (keys %{ $fields{$group}{field}{$field}{pg}{$oadatatype} })
      } # foreach my $oadatatype (keys %{ $fields{$group}{field}{$field}{pg} })
    } # foreach my $field (keys %{ $fields{$group}{field} })
  } # foreach my $group (keys %fields)

#   $fields{person}{field}{person}{pg}{'pic'}{'contact'}                       = 'ontology';
#   $fields{person}{field}{person}{pg}{'exp'}{'contact'}                       = 'ontology';
#   $fields{person}{field}{person}{pg}{'cns'}{'person'}                        = 'multiontology';
} # sub writePg

sub renameImageFile {					# move file to directory under WBPerson ID
							# for now just copying, later should figure out how to rename and change image source
  my ($tempImageFilename, $wbperson) = @_;
  my $tempFile  = "/home2/acedb/public_html/draciti/Micropublication/uploads/temp/$tempImageFilename";
  my $final_upload_dir = '/home2/acedb/public_html/draciti/Micropublication/uploads/Expression/' . $wbperson;
  unless (-d $final_upload_dir) { 
    make_path $final_upload_dir or die "Failed to create path: $final_upload_dir"; 
    my $mode = "0777"; 
    chmod oct($mode), $final_upload_dir;		# make directories have global permission, so acedb can remove them
  }
  my $finalFile = &getPgDate(); $finalFile =~ s/[\-:]//g; $finalFile =~ s/ /_/g; 
  my $pic_source = $finalFile . '.jpg';
  $fields{imageupload}{field}{imageupload}{termidvalue}{1} = $pic_source;
  $finalFile = $final_upload_dir . '/' . $finalFile . '.jpg';
  copy $tempFile, $finalFile;
  my $mode = "0666"; 
  chmod oct($mode), $tempFile;				# make tempfiles world readable only on submission, cronjob can delete from acedb account
  chmod oct($mode), $finalFile;				# make files editable by acedb account
#   print qq(COPY $tempFile TO $finalFile E<br>\n);
} # sub renameImageFile

sub checkMandatoryFields {
  my $mandatoryFail = 0;
  my $radioTranCons = 0;
  if ($fields{method}{field}{method}{inputvalue}{1}) { $radioTranCons = $fields{method}{field}{method}{inputvalue}{1}; }
  my $anyanatomyHasSomething = 0;
  foreach my $group (keys %fields) {
    my $amount = $fields{$group}{multi};
    foreach my $field (keys %{ $fields{$group}{field} }) {
      my $fieldLabel    = $fields{$group}{field}{$field}{label};
      my $fieldType     = $fields{$group}{field}{$field}{type};
      my $mandatoryFlag = $fields{$group}{field}{$field}{mandatory};
      my $dataKey       = 'inputvalue';
      if ( ($fieldType eq 'upload') || ($fieldType eq 'ontology') ) { $dataKey = 'termidvalue'; }
      my $needCheckFlag = 0;
      if ($mandatoryFlag eq 'mandatory') { $needCheckFlag++; }
      if ( ( ($mandatoryFlag eq 'construct') || ($mandatoryFlag eq 'transgene') || ($mandatoryFlag eq 'insitu') || ($mandatoryFlag eq 'antibody') || ($mandatoryFlag eq 'allele') ) && ($radioTranCons eq $mandatoryFlag) ) { $needCheckFlag++; }
      if ($needCheckFlag) {
        unless (scalar keys %{ $fields{$group}{field}{$field}{$dataKey} } > 0) {
          $mandatoryFail++;
          print qq(<span style="color:red">$fieldLabel is mandatory.</span><br/>\n); } }
      if ($mandatoryFlag eq 'anyanatomy') {
        if (scalar keys %{ $fields{$group}{field}{$field}{$dataKey} } > 0) { $anyanatomyHasSomething++; } }
  } }
  unless ($anyanatomyHasSomething) {
    $mandatoryFail++;
    print qq(<span style="color:green">At least one location of time of expression is required</span><br/>\n); }
  if ($mandatoryFail > 0) { print qq(<br/><br/>\n); }
  return $mandatoryFail;
} # sub checkMandatoryFields

sub load {
  print "Content-type: text/html\n\n";
  print $header;
  &getHashFromPg();
  &showForm();
  print $footer;
} # sub load

sub getHashFromPg {
  my $datatype = 'micropublication';
  my ($var, $ip)                  = &getHtmlVar($query, 'user_ip');
  ($var, my $time)                = &getHtmlVar($query, 'time');
  my $saveUrl = "expr_micropub.cgi?action=Load&user_ip=$ip&time=$time";
  print qq(Loading data from <a href="$saveUrl">link</a><br/><br/>\n);
  $result = $dbh->prepare( "SELECT frm_field, frm_data FROM frm_user_save WHERE frm_user_ip = '$ip' AND frm_time = '$time' AND frm_datatype = '$datatype';" );
  $result->execute();
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
  my $datatype = 'micropublication';
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
#   my $saveUrl = "expr_micropub.cgi?action=Load&user_ip=$ip&time=$time";
#   print qq(Bookmark this <a href="$saveUrl">link</a> to load it in the future.<br/>\n);
  my $saveUrl = 'http://' . $hostfqdn . "/~azurebrd/cgi-bin/forms/expr_micropub.cgi?action=Load&user_ip=$ip&time=$time";

  print qq(Please use this <a href="$saveUrl">link</a> to continue the submission.<br/>\n);
  if ($fields{email}{field}{email}{inputvalue}{1}) {
    print qq(The <a href="$saveUrl">link</a> has also been emailed to you, if you would like to continue at a later date.<br/>\n);
    my $email   = $fields{email}{field}{email}{inputvalue}{1};
    my $user    = 'micropublication_form';    # who sends mail
    my $subject = 'Link for WormBase Micropublication form';
    my $gene    = 'no gene chosen';     
    if ($fields{gene}{field}{gene}{inputvalue}{1}) { $gene = $fields{gene}{field}{gene}{inputvalue}{1}; }
    my $date    = &getPgDate();
    my $body    = qq(Please continue your submission through the WormBase Micropublication form, for $gene, saved on $date, with this link: $saveUrl\n\nThank you\nWormBase/WormBase team);
    &mailer($user, $email, $subject, $body);                    # email the data
  }

} # sub saveFormData

sub deletePg {
  my ($user_ip, $time) = @_;
  my $pgcommand = qq(DELETE FROM frm_user_save WHERE frm_user_ip = '$user_ip' AND frm_time = '$time');
#   print qq($pgcommand<br/>\n);
  $dbh->do( $pgcommand );
} # sub deletePg

sub processUpload {
  my ($group, $i, $field, $label) = @_;
  my $input = "input_${i}_$field";
  ($var, my $filename)            = &getHtmlVar($query, "input_${i}_$field");	# newly chosen image
  ($var, my $previewfilename)     = &getHtmlVar($query, "termid_${i}_$field");	# previously chosen image (from preview or save/load)

# TODO when doing submit, rename file to WBPerson_time
  if ($filename) {								# there's a new image, process it
#       my $upload_dir = '/home2/azurebrd/public_html/cgi-bin/uploads';
      my $upload_dir = '/home2/acedb/public_html/draciti/Micropublication/uploads/temp';
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
      return $filename;
#       $fields{$group}{field}{$field}{termidvalue}{$i} = $filename;
# #       my $imageUrl = "http://" . $hostfqdn . "/~azurebrd/cgi-bin/uploads/$filename";
#       my $imageUrl = "http://" . $hostfqdn . "/~acedb/draciti/Micropublication/uploads/temp/$filename";
# #       return qq(<td>$label</td><td>$i</td><td><img width="400" src="$imageUrl"></td>\n);
#       return qq(<td>$label</td><td><img width="400" src="$imageUrl"></td>\n); 
    }
    elsif ($previewfilename) {							# there used to be an image, use that
      return $previewfilename;
#       $fields{$group}{field}{$field}{termidvalue}{$i} = $previewfilename;
# #       my $imageUrl = "http://" . $hostfqdn . "/~azurebrd/cgi-bin/uploads/$previewfilename";
#       my $imageUrl = "http://" . $hostfqdn . "/~acedb/draciti/Micropublication/uploads/temp/$previewfilename";
# #       return qq(<td>$label</td><td>$i</td><td><img width="400" src="$imageUrl"></td>\n);
#       return qq(<td>$label</td><td><img width="400" src="$imageUrl"></td>\n); 
    }
    else { return(''); }
} # sub processUpload

sub initFields {
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

#   tie %{ $fields{raffle}{field} }, "Tie::IxHash";
#   $fields{raffle}{multi}                                                     = '1';
#   $fields{raffle}{field}{raffle}{type}                                       = 'radio';
#   $fields{raffle}{field}{raffle}{label}                                      = 'Choose one of the following';
#   $fields{raffle}{field}{raffle}{group}                                      = 'raffle';
#   $fields{raffle}{field}{raffle}{mandatory}                                  = 'mandatory';
#   tie %{ $fields{raffle}{field}{raffle}{radio} }, "Tie::IxHash";
#   $fields{raffle}{field}{raffle}{radio}{testdata}                            = 'Test data (for raffle only)';
#   $fields{raffle}{field}{raffle}{radio}{realdata}                            = 'REAL DATA (worth 10 raffle entries)';

  tie %{ $fields{person}{field} }, "Tie::IxHash";
  $fields{person}{multi}                                                     = '1';
  $fields{person}{field}{person}{type}                                       = 'ontology';
  $fields{person}{field}{person}{label}                                      = 'Your Name';
  $fields{person}{field}{person}{group}                                      = 'person';
  $fields{person}{field}{person}{terminfo}                                   = qq(If you do not have a WBPerson ID please <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi" target="new">contact</a> WormBase to have one assigned.);
  $fields{person}{field}{person}{mandatory}                                  = 'mandatory';
#   $fields{person}{field}{person}{oamulti}                                    = 'multi';
  $fields{person}{field}{person}{ontology_type}                              = 'WBPerson';
  $fields{person}{field}{person}{pg}{'pic'}{'contact'}                       = 'ontology';
  $fields{person}{field}{person}{pg}{'exp'}{'contact'}                       = 'ontology';
  $fields{person}{field}{person}{pg}{'cns'}{'person'}                        = 'multiontology';
  tie %{ $fields{email}{field} }, "Tie::IxHash";
  $fields{email}{multi}                                                      = '1';
  $fields{email}{field}{email}{type}                                         = 'text';
  $fields{email}{field}{email}{label}                                        = 'Your e-mail address';
  $fields{email}{field}{email}{example}                                      = 'bob@example.com';
  $fields{email}{field}{email}{group}                                        = 'email';
  $fields{email}{field}{email}{mandatory}                                    = 'mandatory';
#   $fields{email}{field}{email}{oamulti}                                      = 'single';
  $fields{email}{field}{email}{pg}{'pic'}{'email'}                           = 'text';
  $fields{email}{field}{email}{pg}{'exp'}{'email'}                           = 'text';
  tie %{ $fields{coaut}{field} }, "Tie::IxHash";
  $fields{coaut}{multi}                                                      = '10';
  $fields{coaut}{field}{coaut}{type}                                         = 'ontology';
  $fields{coaut}{field}{coaut}{label}                                        = 'Co-authors';
  $fields{coaut}{field}{coaut}{example}                                      = 'Who else contributed?';
  $fields{coaut}{field}{coaut}{group}                                        = 'coaut';
  $fields{coaut}{field}{coaut}{mandatory}                                    = 'optional';
#   $fields{coaut}{field}{coaut}{oamulti}                                      = 'multi';
  $fields{coaut}{field}{coaut}{ontology_type}                                = 'WBPerson';
  $fields{coaut}{field}{coaut}{pg}{'pic'}{'coaut'}                           = 'multiontology';
  $fields{coaut}{field}{coaut}{pg}{'exp'}{'coaut'}                           = 'multiontology';
  tie %{ $fields{laboratory}{field} }, "Tie::IxHash";
  $fields{laboratory}{multi}                                                 = '10';
#   $fields{laboratory}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{laboratory}{field}{laboratory}{type}                               = 'ontology';
  $fields{laboratory}{field}{laboratory}{label}                              = 'Laboratory';
  $fields{laboratory}{field}{laboratory}{group}                              = 'laboratory';
  $fields{laboratory}{field}{laboratory}{terminfo}                           = 'Start typing the PI name and select an entry from the list.  Click <a href="mailto:genenames@wormbase.org">here</a> to request a lab designation.';
  $fields{laboratory}{field}{laboratory}{mandatory}                          = 'mandatory';
#   $fields{laboratory}{field}{laboratory}{supergroup}                         = 'construct';
#   $fields{laboratory}{field}{laboratory}{oamulti}                            = 'multi';
  $fields{laboratory}{field}{laboratory}{ontology_type}                      = 'obo';
  $fields{laboratory}{field}{laboratory}{ontology_table}                     = 'laboratory';
  $fields{laboratory}{field}{laboratory}{pg}{'cns'}{'laboratory'}            = 'multiontology';
  $fields{laboratory}{field}{laboratory}{pg}{'exp'}{'laboratory'}            = 'multiontology';
  tie %{ $fields{funding}{field} }, "Tie::IxHash";
  $fields{funding}{multi}                                                    = '1';
  $fields{funding}{field}{funding}{type}                                     = 'bigtext';
  $fields{funding}{field}{funding}{label}                                    = 'Funding';
  $fields{funding}{field}{funding}{group}                                    = 'funding';
  $fields{funding}{field}{funding}{terminfo}                                 = 'Example: "This work was supported by the National Human Genome Research Institute of the National Institutes of Health [ grant number HGxxxxxx-xx ] and the Wellcome Trust [ grant number xxxxxx ]."';
  $fields{funding}{field}{funding}{mandatory}                                = 'mandatory';
#   $fields{funding}{field}{funding}{oamulti}                                  = 'single';
  $fields{funding}{field}{funding}{pg}{'exp'}{'funding'}                     = 'bigtext';
  tie %{ $fields{species}{field} }, "Tie::IxHash";
  $fields{species}{multi}                                                    = '1';
  $fields{species}{field}{species}{type}                                     = 'ontology';
  $fields{species}{field}{species}{label}                                    = 'Species';
  $fields{species}{field}{species}{example}                                  = 'Ex: Caenorhabditis elegans';
  $fields{species}{field}{species}{group}                                    = 'species';
  $fields{species}{field}{species}{terminfo}                                 = 'obo';
  $fields{species}{field}{species}{mandatory}                                = 'mandatory';
#   $fields{species}{field}{species}{oamulti}                                  = 'single';
  $fields{species}{field}{species}{ontology_type}                            = 'obo';
  $fields{species}{field}{species}{ontology_table}                           = 'species';
  $fields{species}{field}{species}{pg}{'exp'}{'species'}                     = 'ontology';
  $fields{species}{field}{species}{pg}{'pic'}{'species'}                     = 'ontology';
  tie %{ $fields{imageupload}{field} }, "Tie::IxHash";
  $fields{imageupload}{multi}                                                = '1';
  $fields{imageupload}{field}{imageupload}{type}                             = 'upload';
  $fields{imageupload}{field}{imageupload}{label}                            = 'Choose an image (jpg format)';
  $fields{imageupload}{field}{imageupload}{group}                            = 'imageupload';
  $fields{imageupload}{field}{imageupload}{terminfo}                         = 'Each submission should have an image depicting the localization of a reporter gene fusion. The image should be at high resolution as it will be used as evidence of expression and should be unequivocally interpreted by a reviewer.  When necessary, arrows and labels to facilitate interpretation should be added. You can submit more than one image for one specific expression pattern by creating a panel as if you were generating a figure for a research article. Remember that the reporter should be the same for all images. Click <a href="/~acedb/draciti/Micropublication/Guidelines.htm">here</a> to see full guidelines.';
  $fields{imageupload}{field}{imageupload}{mandatory}                        = 'mandatory';
#   $fields{imageupload}{field}{imageupload}{oamulti}                          = 'single';
  $fields{imageupload}{field}{imageupload}{upload_type}                      = 'jpg';
  $fields{imageupload}{field}{imageupload}{pg}{'pic'}{'source'}              = 'upload';
  tie %{ $fields{gene}{field} }, "Tie::IxHash";
  $fields{gene}{multi}                                                       = '1';
  $fields{gene}{field}{gene}{type}                                           = 'ontology';
  $fields{gene}{field}{gene}{label}                                          = 'Expression Pattern for Gene';
  $fields{gene}{field}{gene}{example}                                        = 'Ex: lin-3';
  $fields{gene}{field}{gene}{group}                                          = 'gene';
  $fields{gene}{field}{gene}{mandatory}                                      = 'mandatory';
  $fields{gene}{field}{gene}{ontology_type}                                  = 'WBGene';
#   $fields{gene}{field}{gene}{oamulti}                                        = 'multi';
  $fields{gene}{field}{gene}{pg}{'exp'}{'gene'}                              = 'multiontology';

  tie %{ $fields{description}{field} }, "Tie::IxHash";
  $fields{description}{multi}                                                = '1';
  $fields{description}{field}{description}{type}                             = 'bigtext';
  $fields{description}{field}{description}{label}                            = 'Pattern description';
  $fields{description}{field}{description}{group}                            = 'description';
  $fields{description}{field}{description}{terminfo}                         = q[Provide a comprehensive description of what you observed as if you were writing a paragraph for gene expression for a research article. In case you used arrows and labels in the image you provided, please explain what they are pointing to. Here a couple of pattern descriptions taken from the literature: 1): 'Strong snf-12 expression was observed in the epidermis of C. elegans throughout development. Expression is also seen in vulval cells, in the excretory cell, in the seam cells, and in the amphid and phasmid socket cells.' 2):' Expression of aipl-1 was initially detected in embryos at the comma to 1.5-fold stages (310-350 min after first cell division) in the neurons, the intestine, and the body wall muscle. In older embryos, expression of GFP is gradually diminished in the body wall muscle, while it persisted in the neurons and intestine. In adult worms, expression of GFP was detected in the intestine, the spermatheca, and some of the head neurons.];
  $fields{description}{field}{description}{mandatory}                        = 'mandatory';
#   $fields{description}{field}{description}{oamulti}                          = 'single';
  $fields{description}{field}{description}{pg}{'pic'}{'description'}         = 'bigtext';
  $fields{description}{field}{description}{pg}{'exp'}{'pattern'}             = 'bigtext';

  tie %{ $fields{spacertransgene}{field} }, "Tie::IxHash";
  $fields{spacertransgene}{multi}                                            = '1';
  $fields{spacertransgene}{field}{spacertransgene}{type}                     = 'spacer';
  $fields{spacertransgene}{field}{spacertransgene}{label}                    = 'Detection Method';
#   $fields{spacertransgene}{field}{spacertransgene}{label}                    = 'Which reporter fusion did you use?';
  $fields{spacertransgene}{field}{spacertransgene}{group}                    = 'spacertransgene';
  $fields{spacertransgene}{field}{spacertransgene}{mandatory}                = 'optional';
  $fields{spacertransgene}{field}{spacertransgene}{fontsize}                 = '12pt';
  $fields{spacertransgene}{field}{spacertransgene}{height}                   = '50px';

#   tie %{ $fields{spacertransgenemore}{field} }, "Tie::IxHash";
#   $fields{spacertransgenemore}{multi}                                        = '1';
#   $fields{spacertransgenemore}{field}{spacertransgenemore}{type}             = 'spacer';
#   $fields{spacertransgenemore}{field}{spacertransgenemore}{label}            = qq(Click on Existing transgene and type the name of it if the reporter fusion was already described or select New Transgene if you wish to submit a new construct);
#   $fields{spacertransgenemore}{field}{spacertransgenemore}{group}            = 'spacertransgenemore';
#   $fields{spacertransgenemore}{field}{spacertransgenemore}{mandatory}        = 'optional';
#   $fields{spacertransgenemore}{field}{spacertransgenemore}{fontsize}         = '8pt';

  tie %{ $fields{method}{field} }, "Tie::IxHash";
  $fields{method}{multi}                                                     = '1';
  $fields{method}{field}{method}{type}                                       = 'radio';
#   $fields{method}{field}{method}{label}                                      = 'Existing OR New Transgene';
  $fields{method}{field}{method}{label}                                      = 'Choose one of the following';
  $fields{method}{field}{method}{group}                                      = 'method';
  $fields{method}{field}{method}{mandatory}                                  = 'mandatory';
  tie %{ $fields{method}{field}{method}{radio} }, "Tie::IxHash";
  $fields{method}{field}{method}{radio}{antibody}                            = 'Antibody';
  $fields{method}{field}{method}{radio}{insitu}                              = '<i>In-situ</i> hybridization';
  $fields{method}{field}{method}{radio}{allele}                              = 'Genome Editing';
  $fields{method}{field}{method}{radio}{transgene}                           = 'Existing Transgene';
  $fields{method}{field}{method}{radio}{construct}                           = 'New Transgene';
  $fields{method}{field}{method}{radio}{rtpcr}                               = 'RT-PCR';
#   $fields{method}{field}{method}{oamulti}                                  = 'single';
#   $fields{method}{field}{method}{pg}{'cns'}                                = 'method';

  tie %{ $fields{antibody}{field} }, "Tie::IxHash";
  $fields{antibody}{multi}                                                   = '1';
  $fields{antibody}{field}{antibody}{type}                                   = 'bigtext';
  $fields{antibody}{field}{antibody}{label}                                  = 'Antibody used';
  $fields{antibody}{field}{antibody}{example}                                = 'Ex: anti-lin-3';
  $fields{antibody}{field}{antibody}{group}                                  = 'antibody';
  $fields{antibody}{field}{antibody}{mandatory}                              = 'antibody';
  $fields{antibody}{field}{antibody}{supergroup}                             = 'antibody';
  $fields{antibody}{field}{antibody}{terminfo}                               = 'Please enter the WormBase antibody name if the antibody was already described, e.g. [cgc3007]:lin-39 or enter full details if you raised the antibodies in your lab, e.g.: "Anti-LRK-1 rabbit polyclonal antiserum was raised against thesynthetic polypeptide, CDDGELPITSSSHMKGR, corresponding to the sequence within the ROC-COR domain ofLRK-1. The antiserum was then affinity-purified."';
#   $fields{antibody}{field}{antibody}{pg}{'exp'}{'antibody'}                  = 'bigtext';	# bigtext field but OA table has multiontology

  tie %{ $fields{insitu}{field} }, "Tie::IxHash";
  $fields{insitu}{multi}                                                     = '1';
  $fields{insitu}{field}{insitu}{type}                                       = 'bigtext';
  $fields{insitu}{field}{insitu}{label}                                      = '<i>In-situ</i> details';
  $fields{insitu}{field}{insitu}{example}                                    = 'Ex: smFISH';
  $fields{insitu}{field}{insitu}{group}                                      = 'insitu';
  $fields{insitu}{field}{insitu}{mandatory}                                  = 'insitu';
  $fields{insitu}{field}{insitu}{supergroup}                                 = 'insitu';
  $fields{insitu}{field}{insitu}{terminfo}                                   = 'Example of experimental details appended to a whole mount ISH: Fluorescein labelled riboprobe made by in vitro transcription from T7 promoter using PCR product as template.  Primers for PCR-- sense strand primer 354  C07B5A2  AAA TCG AGT TGG ACG CTA TC antisense primer with T7 promoter (in brackets) 9  C07B5T2   [TAA TAC GAC TCA CTA TAG] GCG ATT GGT CAG CAT TCT TC. Example of experimental details appended to a Single molecule FISH experiment: smFISH was performed as described (Raj et al., 2008). In short, synchronized L1 animals were fixed using 4% formaldehyde and 70% ethanol. Hybridization was done for > 12 h at 30 °C in the dark. Oligonucleotide probes were designed using a specific algorithm (www.singlemoleculefish.com) and chemically coupled to Cy5 (mig-21 probe).';

  tie %{ $fields{allele}{field} }, "Tie::IxHash";
  $fields{allele}{multi}                                                     = '1';
  $fields{allele}{field}{allele}{type}                                       = 'bigtext';
  $fields{allele}{field}{allele}{label}                                      = 'Engineered Allele';
  $fields{allele}{field}{allele}{example}                                    = 'Ex: lect-2(dz249)[lect-2::mNG^3xFlag])II';
  $fields{allele}{field}{allele}{group}                                      = 'allele';
  $fields{allele}{field}{allele}{mandatory}                                  = 'allele';
  $fields{allele}{field}{allele}{supergroup}                                 = 'allele';
#   $fields{allele}{field}{allele}{terminfo}                                 = 'No';
#   $fields{allele}{field}{allele}{pg}{'exp'}{'variation'}      = 'bigtext';	# bigtext field but OA table has multiontology


  tie %{ $fields{transgene}{field} }, "Tie::IxHash";
  $fields{transgene}{multi}                                                  = '10';
#   $fields{transgene}{class}                                                  = [ 'method', 'method_transgene' ];
  $fields{transgene}{field}{transgene}{type}                                 = 'ontology';
  $fields{transgene}{field}{transgene}{label}                                = 'Transgene used';
  $fields{transgene}{field}{transgene}{example}                              = 'Ex: syIs107';
  $fields{transgene}{field}{transgene}{group}                                = 'transgene';
  $fields{transgene}{field}{transgene}{mandatory}                            = 'transgene';
  $fields{transgene}{field}{transgene}{supergroup}                           = 'transgene';
#   $fields{transgene}{field}{transgene}{oamulti}                              = 'multi';
  $fields{transgene}{field}{transgene}{ontology_type}                        = 'WBTransgene';
  $fields{transgene}{field}{transgene}{pg}{'exp'}{'transgene'}               = 'multiontology';

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
#   $fields{summary}{field}{summary}{oamulti}                                  = 'single';
  $fields{summary}{field}{summary}{pg}{'cns'}{'summary'}                     = 'bigtext';
  tie %{ $fields{cnssummary}{field} }, "Tie::IxHash";
  $fields{cnssummary}{multi}                                                 = '1';
#   $fields{cnssummary}{class}                                                 = [ 'method', 'method_construct' ];
  $fields{cnssummary}{field}{cnssummary}{type}                               = 'bigtext';
  $fields{cnssummary}{field}{cnssummary}{label}                              = 'Construction Details';
  $fields{cnssummary}{field}{cnssummary}{group}                              = 'cnssummary';
  $fields{cnssummary}{field}{cnssummary}{terminfo}                           = qq(Example: [pkd-2::GFP] translational fusion. The pkd-2-GFP plasmid was made using plasmid pPD95.75 as parent vector, and a fusion of a long range PCR fragment of genomic pkd-2 (promoter and 5'-end) with a 3'-end fragment derived from yk219e1 to produce a 7.153-kb fusion containing the full-length pkd-2 gene.);
  $fields{cnssummary}{field}{cnssummary}{mandatory}                          = 'construct';
  $fields{cnssummary}{field}{cnssummary}{supergroup}                         = 'construct';
#   $fields{cnssummary}{field}{cnssummary}{oamulti}                            = 'single';
  $fields{cnssummary}{field}{cnssummary}{pg}{'cns'}{'constructionsummary'}   = 'bigtext';
  tie %{ $fields{dna}{field} }, "Tie::IxHash";
  $fields{dna}{multi}                                                        = '10';
#   $fields{dna}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{dna}{field}{dna}{type}                                             = 'bigtext';
  $fields{dna}{field}{dna}{label}                                            = 'DNA sequence';
  $fields{dna}{field}{dna}{group}                                            = 'dna';
  $fields{dna}{field}{dna}{terminfo}                                         = qq(Enter the DNA sequence used to drive reporter expression -excluding backbone vector and reporter itself. If you used a translational fusion, please add all pertinent DNA sequence in the box. If you want to enter 2 non-contiguous DNA sequences please enter the first one in the DNA sequence box. Once you will click outside the box a new DNA sequence field will appear, you can then enter the second sequence.  If you have primers you can use the WormBase e-PCR tool located <a href="http://www.wormbase.org/tools/epcr" target="new">here</a>.);
  $fields{dna}{field}{dna}{mandatory}                                        = 'construct';
  $fields{dna}{field}{dna}{supergroup}                                       = 'construct';
#   $fields{dna}{field}{dna}{oamulti}                                          = 'pipe';
  $fields{dna}{field}{dna}{pg}{'cns'}{'dna'}                                 = 'bigtext';
  tie %{ $fields{threeutr}{field} }, "Tie::IxHash";
  $fields{threeutr}{multi}                                                   = '10';
  $fields{threeutr}{field}{threeutr}{type}                                   = 'ontology';
  $fields{threeutr}{field}{threeutr}{label}                                  = "3' UTR";
  $fields{threeutr}{field}{threeutr}{example}                                = 'Ex: unc-54';
  $fields{threeutr}{field}{threeutr}{group}                                  = 'threeutr';
  $fields{threeutr}{field}{threeutr}{mandatory}                              = 'optional';
  $fields{threeutr}{field}{threeutr}{supergroup}                             = 'construct';
  $fields{threeutr}{field}{threeutr}{ontology_type}                          = 'WBGene';
#   $fields{threeutr}{field}{threeutr}{oamulti}                                = 'multi';
  $fields{threeutr}{field}{threeutr}{pg}{'cns'}{'threeutr'}                  = 'multiontology';
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
#   $fields{reporter}{field}{reporter}{oamulti}                                = 'multi';
  $fields{reporter}{field}{reporter}{ontology_type}                          = 'obo';
  $fields{reporter}{field}{reporter}{ontology_table}                         = 'cnsreporter';
  $fields{reporter}{field}{reporter}{pg}{'cns'}{'reporter'}                  = 'multiontology';
  tie %{ $fields{clone}{field} }, "Tie::IxHash";
  $fields{clone}{multi}                                                      = '10';
#   $fields{clone}{class}                                                        = [ 'method', 'method_construct' ];
  $fields{clone}{field}{clone}{type}                                         = 'ontology';
  $fields{clone}{field}{clone}{label}                                        = 'Backbone Vector';
  $fields{clone}{field}{clone}{example}                                      = 'Ex: pPD107.94';
  $fields{clone}{field}{clone}{group}                                        = 'clone';
  $fields{clone}{field}{clone}{mandatory}                                    = 'optional';
  $fields{clone}{field}{clone}{supergroup}                                   = 'construct';
#   $fields{clone}{field}{clone}{oamulti}                                      = 'multi';
  $fields{clone}{field}{clone}{ontology_type}                                = 'obo';
  $fields{clone}{field}{clone}{ontology_table}                               = 'clone';
  $fields{clone}{field}{clone}{pg}{'cns'}{'clone'}                           = 'multiontology';
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
#   $fields{cnstype}{field}{cnstype}{oamulti}                                  = 'multi';
  $fields{cnstype}{field}{cnstype}{ontology_type}                            = 'obo';
  $fields{cnstype}{field}{cnstype}{ontology_table}                           = 'cnsconstructtype';
  $fields{cnstype}{field}{cnstype}{pg}{'cns'}{'constructtype'}               = 'ontology';
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
#   $fields{cnspubname}{field}{cnspubname}{oamulti}                            = 'single';
#   $fields{cnspubname}{field}{cnspubname}{pg}{'cns'}                          = 'cnspubname';	# FIX NOT A PG TABLE
  tie %{ $fields{remark}{field} }, "Tie::IxHash";
  $fields{remark}{multi}                                                     = '1';
  $fields{remark}{field}{remark}{type}                                       = 'bigtext';
  $fields{remark}{field}{remark}{label}                                      = 'Construct Comments';
  $fields{remark}{field}{remark}{group}                                      = 'remark';
  $fields{remark}{field}{remark}{mandatory}                                  = 'optional';
  $fields{remark}{field}{remark}{supergroup}                                 = 'construct';
#   $fields{remark}{field}{remark}{oamulti}                                    = 'single';
  $fields{remark}{field}{remark}{pg}{'cns'}{'remark'}                        = 'bigtext';
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
#   $fields{strain}{field}{strain}{oamulti}                                    = 'single';
  $fields{strain}{field}{strain}{pg}{'cns'}{'strain'}                        = 'text';
  tie %{ $fields{coinjectedwith}{field} }, "Tie::IxHash";
  $fields{coinjectedwith}{multi}                                             = '1';
  $fields{coinjectedwith}{field}{coinjectedwith}{type}                       = 'text';
  $fields{coinjectedwith}{field}{coinjectedwith}{label}                      = 'Coinjected with';
  $fields{coinjectedwith}{field}{coinjectedwith}{group}                      = 'coinjectedwith';
  $fields{coinjectedwith}{field}{coinjectedwith}{mandatory}                  = 'optional';
  $fields{coinjectedwith}{field}{coinjectedwith}{supergroup}                 = 'construct';
#   $fields{coinjectedwith}{field}{coinjectedwith}{oamulti}                    = 'single';
  $fields{coinjectedwith}{field}{coinjectedwith}{pg}{'cns'}{'coinjectedwith'} = 'text';
  tie %{ $fields{cnssumextra}{field} }, "Tie::IxHash";
  $fields{cnssumextra}{multi}                                                = '1';
  $fields{cnssumextra}{field}{cnssumextra}{type}                             = 'text';
  $fields{cnssumextra}{field}{cnssumextra}{label}                            = 'Injection Concentration';
  $fields{cnssumextra}{field}{cnssumextra}{group}                            = 'cnssumextra';
  $fields{cnssumextra}{field}{cnssumextra}{mandatory}                        = 'optional';
  $fields{cnssumextra}{field}{cnssumextra}{supergroup}                       = 'construct';
#   $fields{cnssumextra}{field}{cnssumextra}{oamulti}                          = 'single';
  $fields{cnssumextra}{field}{cnssumextra}{pg}{'cns'}{'constructionsummary'} = 'bigtext';
  tie %{ $fields{integratedby}{field} }, "Tie::IxHash";
  $fields{integratedby}{multi}                                               = '1';
  $fields{integratedby}{field}{integratedby}{type}                           = 'ontology';
  $fields{integratedby}{field}{integratedby}{label}                          = 'Integrated by';
  $fields{integratedby}{field}{integratedby}{example}                        = 'Ex: Particle_bombardment';
  $fields{integratedby}{field}{integratedby}{group}                          = 'integratedby';
  $fields{integratedby}{field}{integratedby}{terminfo}                       = 'obo';
  $fields{integratedby}{field}{integratedby}{mandatory}                      = 'optional';
  $fields{integratedby}{field}{integratedby}{supergroup}                     = 'construct';
#   $fields{integratedby}{field}{integratedby}{oamulti}                        = 'multi';
  $fields{integratedby}{field}{integratedby}{ontology_type}                  = 'obo';
  $fields{integratedby}{field}{integratedby}{ontology_table}                 = 'integrationmethod';
  $fields{integratedby}{field}{integratedby}{pg}{'cns'}{'integrationmethod'} = 'ontology';

# Where and when did you observe expression? 
  tie %{ $fields{spacerlocalization}{field} }, "Tie::IxHash";
  $fields{spacerlocalization}{multi}                                         = '1';
  $fields{spacerlocalization}{field}{spacerlocalization}{type}               = 'spacer';
#   $fields{spacerlocalization}{field}{spacerlocalization}{label}              = 'Where and when did you observe expression?';
  $fields{spacerlocalization}{field}{spacerlocalization}{label}              = qq(Where and when did you observe expression? <span style='color: red; font-size: 13px;'>(one required)</span>);
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
#   $fields{certain}{field}{ceranatomy}{oamulti}                               = 'multi';
  $fields{certain}{field}{ceranatomy}{ontology_type}                         = 'obo';
  $fields{certain}{field}{ceranatomy}{ontology_table}                        = 'anatomy';
  $fields{certain}{field}{ceranatomy}{pg}{'pic'}{'anat_term'}                = 'multiontology';
  $fields{certain}{field}{ceranatomy}{pg}{'exp'}{'anatomy'}                  = 'multiontology';
  $fields{certain}{field}{cerlifestage}{type}                                = 'ontology';
  $fields{certain}{field}{cerlifestage}{label}                               = 'During';
  $fields{certain}{field}{cerlifestage}{example}                             = 'Ex: embryo Ce';
  $fields{certain}{field}{cerlifestage}{group}                               = 'certain';
  $fields{certain}{field}{cerlifestage}{mandatory}                           = 'anyanatomy';
#   $fields{certain}{field}{cerlifestage}{oamulti}                             = 'multi';
  $fields{certain}{field}{cerlifestage}{ontology_type}                       = 'obo';
  $fields{certain}{field}{cerlifestage}{ontology_table}                      = 'lifestage';
  $fields{certain}{field}{cerlifestage}{pg}{'pic'}{'lifestage'}              = 'multiontology';
  $fields{certain}{field}{cerlifestage}{pg}{'exp'}{'qualifierls'}            = 'multiontology';
  $fields{certain}{field}{cerlifestage}{minwidth}                            = '50px';
  $fields{certain}{field}{cergoidcc}{type}                                   = 'ontology';
  $fields{certain}{field}{cergoidcc}{label}                                  = 'Subcellular localization';
  $fields{certain}{field}{cergoidcc}{example}                                = 'Ex: nucleus';
  $fields{certain}{field}{cergoidcc}{group}                                  = 'certain';
  $fields{certain}{field}{cergoidcc}{mandatory}                              = 'anyanatomy';
#   $fields{certain}{field}{cergoidcc}{oamulti}                                = 'multi';
  $fields{certain}{field}{cergoidcc}{ontology_type}                          = 'obo';
  $fields{certain}{field}{cergoidcc}{ontology_table}                         = 'goid';		# special action on autocomplete
  $fields{certain}{field}{cergoidcc}{pg}{'pic'}{'goid'}                      = 'multiontology';
  $fields{certain}{field}{cergoidcc}{pg}{'exp'}{'goid'}                      = 'multiontology';
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
#   $fields{partial}{field}{paranatomy}{oamulti}                               = 'multi';
  $fields{partial}{field}{paranatomy}{ontology_type}                         = 'obo';
  $fields{partial}{field}{paranatomy}{ontology_table}                        = 'anatomy';
  $fields{partial}{field}{paranatomy}{pg}{'pic'}{'anat_term'}                = 'multiontology';
  $fields{partial}{field}{paranatomy}{pg}{'exp'}{'anatomy'}                  = 'multiontology';
  $fields{partial}{field}{parlifestage}{type}                                = 'ontology';
  $fields{partial}{field}{parlifestage}{label}                               = 'During';
  $fields{partial}{field}{parlifestage}{group}                               = 'partial';
  $fields{partial}{field}{parlifestage}{mandatory}                           = 'anyanatomy';
#   $fields{partial}{field}{parlifestage}{oamulti}                             = 'multi';
  $fields{partial}{field}{parlifestage}{ontology_type}                       = 'obo';
  $fields{partial}{field}{parlifestage}{ontology_table}                      = 'lifestage';
  $fields{partial}{field}{parlifestage}{pg}{'pic'}{'lifestage'}              = 'multiontology';
  $fields{partial}{field}{parlifestage}{pg}{'exp'}{'qualifierls'}            = 'multiontology';
  $fields{partial}{field}{parlifestage}{minwidth}                            = '50px';
  $fields{partial}{field}{pargoidcc}{type}                                   = 'ontology';
  $fields{partial}{field}{pargoidcc}{label}                                  = 'Subcellular localization';
  $fields{partial}{field}{pargoidcc}{example}                                = 'Ex: nucleus';
  $fields{partial}{field}{pargoidcc}{group}                                  = 'partial';
  $fields{partial}{field}{pargoidcc}{mandatory}                              = 'anyanatomy';
#   $fields{partial}{field}{pargoidcc}{oamulti}                                = 'multi';
  $fields{partial}{field}{pargoidcc}{ontology_type}                          = 'obo';
  $fields{partial}{field}{pargoidcc}{ontology_table}                         = 'goid';		# special action on autocomplete
  $fields{partial}{field}{pargoidcc}{pg}{'pic'}{'goid'}                      = 'multiontology';
  $fields{partial}{field}{pargoidcc}{pg}{'exp'}{'goid'}                      = 'multiontology';
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
#   $fields{uncertain}{field}{ucranatomy}{oamulti}                             = 'multi';
  $fields{uncertain}{field}{ucranatomy}{ontology_type}                       = 'obo';
  $fields{uncertain}{field}{ucranatomy}{ontology_table}                      = 'anatomy';
  $fields{uncertain}{field}{ucranatomy}{pg}{'pic'}{'anat_term'}              = 'multiontology';
  $fields{uncertain}{field}{ucranatomy}{pg}{'exp'}{'anatomy'}                = 'multiontology';
  $fields{uncertain}{field}{ucrlifestage}{type}                              = 'ontology';
  $fields{uncertain}{field}{ucrlifestage}{label}                             = 'During';
  $fields{uncertain}{field}{ucrlifestage}{group}                             = 'uncertain';
  $fields{uncertain}{field}{ucrlifestage}{mandatory}                         = 'anyanatomy';
#   $fields{uncertain}{field}{ucrlifestage}{oamulti}                           = 'multi';
  $fields{uncertain}{field}{ucrlifestage}{ontology_type}                     = 'obo';
  $fields{uncertain}{field}{ucrlifestage}{ontology_table}                    = 'lifestage';
  $fields{uncertain}{field}{ucrlifestage}{pg}{'pic'}{'lifestage'}            = 'multiontology';
  $fields{uncertain}{field}{ucrlifestage}{pg}{'exp'}{'qualifierls'}          = 'multiontology';
  $fields{uncertain}{field}{ucrlifestage}{minwidth}                          = '50px';
  $fields{uncertain}{field}{ucrgoidcc}{type}                                 = 'ontology';
  $fields{uncertain}{field}{ucrgoidcc}{label}                                = 'Subcellular localization';
  $fields{uncertain}{field}{ucrgoidcc}{example}                              = 'Ex: nucleus';
  $fields{uncertain}{field}{ucrgoidcc}{group}                                = 'uncertain';
  $fields{uncertain}{field}{ucrgoidcc}{mandatory}                            = 'anyanatomy';
#   $fields{uncertain}{field}{ucrgoidcc}{oamulti}                              = 'multi';
  $fields{uncertain}{field}{ucrgoidcc}{ontology_type}                        = 'obo';
  $fields{uncertain}{field}{ucrgoidcc}{ontology_table}                       = 'goid';		# special action on autocomplete
  $fields{uncertain}{field}{ucrgoidcc}{pg}{'pic'}{'goid'}                    = 'multiontology';
  $fields{uncertain}{field}{ucrgoidcc}{pg}{'exp'}{'goid'}                    = 'multiontology';
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
#   $fields{not}{field}{notanatomy}{oamulti}                                 = 'multi';
  $fields{not}{field}{notanatomy}{ontology_type}                           = 'obo';
  $fields{not}{field}{notanatomy}{ontology_table}                          = 'anatomy';
  $fields{not}{field}{notanatomy}{pg}{'pic'}{'anat_term'}                  = 'multiontology';
  $fields{not}{field}{notanatomy}{pg}{'exp'}{'anatomy'}                    = 'multiontology';
  $fields{not}{field}{notlifestage}{type}                                  = 'ontology';
  $fields{not}{field}{notlifestage}{label}                                 = 'During';
  $fields{not}{field}{notlifestage}{group}                                 = 'not';
  $fields{not}{field}{notlifestage}{mandatory}                             = 'anyanatomy';
#   $fields{not}{field}{notlifestage}{oamulti}                               = 'multi';
  $fields{not}{field}{notlifestage}{ontology_type}                         = 'obo';
  $fields{not}{field}{notlifestage}{ontology_table}                        = 'lifestage';
  $fields{not}{field}{notlifestage}{pg}{'pic'}{'lifestage'}                = 'multiontology';
  $fields{not}{field}{notlifestage}{pg}{'exp'}{'qualifierls'}              = 'multiontology';
  $fields{not}{field}{notlifestage}{minwidth}                              = '50px';
  $fields{not}{field}{notgoidcc}{type}                                     = 'ontology';
  $fields{not}{field}{notgoidcc}{label}                                    = 'Subcellular localization';
  $fields{not}{field}{notgoidcc}{example}                                  = 'Ex: nucleus';
  $fields{not}{field}{notgoidcc}{group}                                    = 'not';
  $fields{not}{field}{notgoidcc}{mandatory}                                = 'anyanatomy';
#   $fields{not}{field}{notgoidcc}{oamulti}                                  = 'multi';
  $fields{not}{field}{notgoidcc}{ontology_type}                            = 'obo';
  $fields{not}{field}{notgoidcc}{ontology_table}                           = 'goid';		# special action on autocomplete
  $fields{not}{field}{notgoidcc}{pg}{'pic'}{'goid'}                        = 'multiontology';
  $fields{not}{field}{notgoidcc}{pg}{'exp'}{'goid'}                        = 'multiontology';
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


  tie %{ $fields{spacerpublicationdetails}{field} }, "Tie::IxHash";
  $fields{spacerpublicationdetails}{multi}                                       = '1';
  $fields{spacerpublicationdetails}{field}{spacerpublicationdetails}{type}       = 'spacer';
  $fields{spacerpublicationdetails}{field}{spacerpublicationdetails}{label}      = 'Publication Details';
  $fields{spacerpublicationdetails}{field}{spacerpublicationdetails}{group}      = 'spacerpublicationdetails';
  $fields{spacerpublicationdetails}{field}{spacerpublicationdetails}{mandatory}  = 'optional';
  $fields{spacerpublicationdetails}{field}{spacerpublicationdetails}{fontsize}   = '12pt';
  $fields{spacerpublicationdetails}{field}{spacerpublicationdetails}{height}     = '50px';

  tie %{ $fields{title}{field} }, "Tie::IxHash";
  $fields{title}{multi}                                                      = '1';
  $fields{title}{field}{title}{type}                                         = 'bigtext';
  $fields{title}{field}{title}{label}                                        = 'Title of the Submission';
  $fields{title}{field}{title}{group}                                        = 'title';
  $fields{title}{field}{title}{example}                                      = qq(Ex: ina-1 expression in the somatic gonad);
  $fields{title}{field}{title}{mandatory}                                    = 'mandatory';
  $fields{title}{field}{title}{pg}{'cns'}{'constructionsummary'}             = 'bigtext';

  tie %{ $fields{acknowledgement}{field} }, "Tie::IxHash";
  $fields{acknowledgement}{multi}                                            = '1';
  $fields{acknowledgement}{field}{acknowledgement}{type}                     = 'bigtext';
  $fields{acknowledgement}{field}{acknowledgement}{label}                    = 'Acknowledgements';
  $fields{acknowledgement}{field}{acknowledgement}{group}                    = 'acknowledgement';
  $fields{acknowledgement}{field}{acknowledgement}{mandatory}                = 'optional';

  tie %{ $fields{reviewer}{field} }, "Tie::IxHash";
  $fields{reviewer}{multi}                                                   = '1';
  $fields{reviewer}{field}{reviewer}{type}                                   = 'ontology';
  $fields{reviewer}{field}{reviewer}{label}                                  = 'Suggested Reviewer';
  $fields{reviewer}{field}{reviewer}{group}                                  = 'reviewer';
  $fields{reviewer}{field}{reviewer}{mandatory}                              = 'optional';
  $fields{reviewer}{field}{reviewer}{ontology_type}                          = 'WBPerson';

  tie %{ $fields{comments}{field} }, "Tie::IxHash";
  $fields{comments}{multi}                                                   = '1';
  $fields{comments}{field}{comments}{type}                                   = 'bigtext';
  $fields{comments}{field}{comments}{label}                                  = 'Comments';
  $fields{comments}{field}{comments}{group}                                  = 'comments';
  $fields{comments}{field}{comments}{mandatory}                              = 'optional';
#   $fields{comments}{field}{comments}{oamulti}                                = 'single';
  $fields{comments}{field}{comments}{pg}{'pic'}{'remark'}                    = 'bigtext';
  $fields{comments}{field}{comments}{pg}{'exp'}{'remark'}                    = 'bigtext';

  tie %{ $fields{disclaimer}{field} }, "Tie::IxHash";
  $fields{disclaimer}{multi}                                                 = '1';
  $fields{disclaimer}{field}{disclaimer}{type}                               = 'checkbox';
  $fields{disclaimer}{field}{disclaimer}{label}                              = 'Disclaimer';
  $fields{disclaimer}{field}{disclaimer}{group}                              = 'disclaimer';
  $fields{disclaimer}{field}{disclaimer}{mandatory}                          = 'mandatory';
  $fields{disclaimer}{field}{disclaimer}{checkboxtext}                       = qq(I/we declare to the best of my/our knowledge that the experiment is reproducible; that the submission has been approved by all authors; and that the submission has been approved by the laboratory's Principal Investigator. The author(s) declare no conflict of interest.);
  $fields{disclaimer}{field}{disclaimer}{checkboxvalue}                      = qq(I/we declare to the best of my/our knowledge that the experiment is reproducible; that the submission has been approved by all authors; and that the submission has been approved by the laboratory's Principal Investigator. The author(s) declare no conflict of interest.);
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
<script type="text/javascript" src="http://${hostfqdn}/~azurebrd/javascript/expr_micropub.js"></script>
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
