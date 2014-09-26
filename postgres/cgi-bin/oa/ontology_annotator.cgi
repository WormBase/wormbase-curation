#!/usr/bin/perl

# phenote-like cgi form

# See the bottom of this file for the POD documentation.  Search for the string '=head'.

# See  oa_old_commented_out_code/  for versions change history and commented-out code.



use strict;
use CGI;
use DBI;
use helperOA;					# &getHtmlVar fromUrlToPostgres
use Tie::IxHash;				# allow hashes ordered by item added
use Encode qw( from_to is_utf8 );

use wormOA;					# config-specific perl module for WormBase MOD (only load one module, the exported subroutines have the same name)
# use testOA;					# config-specific perl module for test MOD (template) (only load one module, the exported subroutines have the same name)

my $configLoaded = 'wormOA';			# which MOD-specific perl module has been loaded
# my $configLoaded = 'testOA';			# which MOD-specific perl module has been loaded


my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my $query = new CGI;

# Autocomplete returns in the format : ''what-someone-types ( id ) [actual-name]''  OR  ''what-someone-types ( id ) '' OR  ''id''
my %fieldIdToValue;			# field_type ; id => "display_value<span style='display: none'>id</span>"
					# field_type can be  $dropdown_type for dropdown / multidropdown  OR  for ontology / multiontology  it can be  $obotable = 'obo_name_' . $ontology_table  for generic obo fields  OR  $ontology_type for specific fields

my $filtersMaxAmount = 5;			# maximum amount of filters
my $newRowMaxAmountNormalOa = 100;		# maximum amount of row that can be created with the New button in normal OA mode
my $newRowMaxAmountBatchUnsafeOa = 1000;	# maximum amount of row that can be created with the New button in batch unsafe OA mode

my $var;

($var, my $action) = &getHtmlVar($query, 'action');

my %fields; 				# tied for order   $fields{app}{id} = 'text';
my %datatypes;				# values that are datatype specific

if ($action) {
  &initFields();
  if ($action eq 'Login !') { &showMain(); }
  elsif ($action eq 'editorFrame') { &showEditor(); }
  elsif ($action eq 'oboFrame') { &showObo(); }
  elsif ($action eq 'controlsFrame') { &showControls(); }
  elsif ($action eq 'tableFrame') { &showTable(); }
  elsif ($action eq 'jsonFieldQuery') { &jsonFieldQuery(); }	
  elsif ($action eq 'autocompleteXHR') { &autocompleteXHR(); }	
  elsif ($action eq 'asyncTermInfo') { &asyncTermInfo(); }	
  elsif ($action eq 'asyncValidValue') { &asyncValidValue(); }	
  elsif ($action eq 'updatePostgresTableField') { &updatePostgresTableField(); }	
  elsif ($action eq 'updatePostgresColumn') { &updatePostgresColumn(); }	
  elsif ($action eq 'newRow') { &newRow(); }	
  elsif ($action eq 'duplicateByPgids') { &duplicateByPgids(); }	
  elsif ($action eq 'deleteByPgids') { &deleteByPgids(); }	
  elsif ($action eq 'checkDataByPgids') { &checkDataByPgids(); }	
} else { &showLogin(); }


### CONTROL FRAME ACTIONS ###

sub checkDataByPgids {					# if checking data, get datatype and pgids to check, then return checks's results
  print "Content-type: text/plain\n\n";
  ($var, my $datatype) = &getHtmlVar($query, 'datatype'); 
  ($var, my $allDataTableIds) = &getHtmlVar($query, 'allDataTableIds');
  my $returnMessage = "";
  if ($datatypes{$datatype}{constraintTablesHaveData}) {
    $returnMessage .= &checkDataInPgTable($datatype, $datatypes{$datatype}{constraintTablesHaveData}, $allDataTableIds); }
  if ($datatypes{$datatype}{constraintSub}) { 
    my $subref = $datatypes{$datatype}{constraintSub}; $returnMessage .= &$subref($allDataTableIds); }
  unless ($returnMessage) { $returnMessage = 'OK'; }
  print $returnMessage;
} # sub checkDataByPgids

sub checkDataInPgTable {
  my ($datatype, $arrayref, $allDataTableIds) = @_;
  my @ids = split/,/, $allDataTableIds; my $joinkeys = join"','", @ids; 
  my @tables = @$arrayref;
  return unless scalar(@tables);			# if there's nothing to check, return
  my %hash;  my $returnMessage = '';
  foreach my $table (@tables) {
    my $pgtable = $datatype . '_' . $table;
    my $result = $dbh->prepare( "SELECT * FROM $pgtable WHERE joinkey IN ('$joinkeys')" );
    $result->execute(); 
    while (my @row = $result->fetchrow()) { 
      if ($row[1]) { $hash{$row[0]}{$table}++; } } }
  foreach my $id (@ids) {
    if ($hash{$id}) {
        my @tablesMissingData;
        foreach my $table (@tables) { unless ($hash{$id}{$table}) { push @tablesMissingData, $fields{$datatype}{$table}{label}; } }
        my $tablesMissingData = join", ", @tablesMissingData;
        if ($tablesMissingData) { 
          $returnMessage .= "Missing data for pgid $id in fields : ${tablesMissingData}.<br/>"; } }
      else { 
        $returnMessage .= "Missing data for pgid $id in all required fields.<br/>"; } }
  return $returnMessage;
} # sub checkDataInPgTable

sub deleteByPgids {					# if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/plain\n\n";
  ($var, my $datatype) = &getHtmlVar($query, 'datatype'); ($var, my $idsToDelete) = &getHtmlVar($query, 'idsToDelete');
  my (@idsToDelete) = split/,/, $idsToDelete;		# get the pgids to delete
  my $returnMessage = '';
  foreach my $origPgid (@idsToDelete) {			# for each pgid to delete
    foreach my $field (keys %{ $fields{$datatype} }) {
      next if ($field eq 'id');				# all datatypes have an 'id' field, but it's not a table
      next if ($fields{$datatype}{$field}{type} eq 'queryonly');	# queryonly fields don't have tables
      my $table = $datatype . '_' . $field;
      my $result = $dbh->prepare( "SELECT joinkey, $table FROM $table WHERE joinkey = '$origPgid'" ); 	
      $result->execute(); my @row = $result->fetchrow(); 
      if ($row[0]) {					# if there is a row for this pgid, as opposed to there being a value, because we want to delete blank '' entries too.  2011 08 31
        my ($isOk) = &updatePostgresByTableJoinkeyNewvalue($table, $origPgid, ''); 
        if ($isOk ne 'OK') { $returnMessage .= $isOk; } } }
  } # foreach my $origPgid (@idsToDuplicate)
  if ($returnMessage) { print $returnMessage; }		# if there are postgres error messages, but this cannot happen because deletes don't throw errors and there are no NULL inserts
    else { print "OK"; }				# delete went OK
} # sub deleteByPgids

sub duplicateByPgids {					# if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/plain\n\n";
  ($var, my $datatype) = &getHtmlVar($query, 'datatype'); 
  ($var, my $idsToDuplicate) = &getHtmlVar($query, 'idsToDuplicate');
  my ($dupPgid) = &getHighestPgid();			# current highest pgid (joinkey)
  if ($dupPgid =~ m/\D/) { print "ERROR: &duplicateByPgids &getHighestPgid returned non-integer $dupPgid\n"; return; }
  my @dupPgids = ();					# which pgids will be the duplicates
  my (@idsToDuplicate) = split/,/, $idsToDuplicate;	# get the pgids to duplicate
  my $returnMessage = '';
  foreach my $origPgid (@idsToDuplicate) {		# for each pgid to duplicate
    $dupPgid++;						# get next highest (blank)
    foreach my $field (keys %{ $fields{$datatype} }) {
      next if ($field eq 'id');				# all datatypes have an 'id' field, but it's not a table
      next if ($fields{$datatype}{$field}{type} eq 'queryonly');	# queryonly fields don't have tables
      my $table = $datatype . '_' . $field;
      my $result = $dbh->prepare( "SELECT $table FROM $table WHERE joinkey = '$origPgid'" ); 	
      $result->execute(); my @row = $result->fetchrow(); 
      if ($row[0]) {					# duplicate if there is data, do not duplicate blank '' entries.  2011 08 31
        my ($isOk) = &updatePostgresByTableJoinkeyNewvalue($table, $dupPgid, $row[0]);
        if ($isOk ne 'OK') { $returnMessage .= $isOk; } } }		# add error messages to returnMessage if not 'OK'
    push @dupPgids, $dupPgid;				# add to list created
  } # foreach my $origPgid (@idsToDuplicate)
  unless ($returnMessage) { $returnMessage = 'OK'; }	# if there are no errors, it's 'OK'
  my $dupPgids = join",", @dupPgids;			# join with ,
  print "$returnMessage\t DIVIDER \t$dupPgids";		# print to result with distinct divider for javascript to split on (in case there's ever a tab in the returnMessage)
} # sub duplicateByPgids

sub newRow {						# if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/plain\n\n";
  ($var, my $newRowAmount) = &getHtmlVar($query, 'newRowAmount');
  ($var, my $datatype)     = &getHtmlVar($query, 'datatype');
  ($var, my $curator_two)  = &getHtmlVar($query, 'curator_two');
  my ($newPgid) = &getHighestPgid();			# current highest pgid (joinkey)
  if ($newPgid =~ m/\D/) { print "ERROR: &newRow &getHighestPgid returned non-integer $newPgid\n"; return; }
  if ($newRowAmount < 2) { $newRowAmount = 1; }		# if there are less than 2 new rows to make, always make at least 1
  my @newPgids = ();					# which pgids will have been created
  my $returnMessage = '';
  for (1 .. $newRowAmount) {				# for each new row to create
    $newPgid++;						# get the next highest pgid
    if ($datatypes{$datatype}{newRowSub}) {		# if there's a subroutine to create a new row for the datatype
      my $subref = $datatypes{$datatype}{newRowSub};
      my ($newPgid_or_returnMessage) = &$subref($newPgid, $curator_two);	# use the subroutine and get a return message
      if ($newPgid_or_returnMessage) {			# if there is a return message and it doesn't contain only digits add to error messages
        if ($newPgid_or_returnMessage !~ m/^\d+$/) { $returnMessage .= $newPgid_or_returnMessage; } } }
    push @newPgids, $newPgid;				# add to list created
  } # for (1 .. $newRowAmount)
  unless ($returnMessage) { $returnMessage = 'OK'; }	# if there are no errors, it's 'OK'
  my $newPgids = join",", @newPgids;			# join with ,
  print "$returnMessage\t DIVIDER \t$newPgids";		# print to result with distinct divider for javascript to split on (in case there's ever a tab in the returnMessage)
} # sub newRow 

# sub newRow {						# if updating postgres table values, update postgres and return OK if ok
#   print "Content-type: text/plain\n\n";
#   ($var, my $datatype) = &getHtmlVar($query, 'datatype');
#   ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
#   my ($newPgid) = &getHighestPgid();			# current highest pgid (joinkey)
#   if ($newPgid =~ m/\D/) { print "ERROR: &newRow &getHighestPgid returned non-integer $newPgid\n"; return; }
#   $newPgid++;
#   my $returnMessage = "ERROR, not a valid datatype\n"; my $newPgid_or_returnMessage = '';
#   if ($datatypes{$datatype}{newRowSub}) { 
#     my $subref = $datatypes{$datatype}{newRowSub}; ($newPgid_or_returnMessage) = &$subref($newPgid, $curator_two); }
#   if ($newPgid_or_returnMessage) { 
#     if ($newPgid_or_returnMessage =~ m/^\d+$/) { $returnMessage = 'OK'; } 
#       else { $returnMessage = $newPgid_or_returnMessage; } }
#   print "$returnMessage\t DIVIDER \t$newPgid";		# print to result with distinct divider for javascript to split on (in case there's ever a tab in the returnMessage)
# } # sub newRow 

sub getHighestPgid {					# get the highest joinkey from the primary tables
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  if ($datatypes{$datatype}{highestPgidTables}) {
      my $pgUnionQuery = "SELECT MAX(joinkey::integer) FROM ${datatype}_" . join" UNION SELECT MAX(joinkey::integer) FROM ${datatype}_", @{ $datatypes{$datatype}{highestPgidTables} };
      my $result = $dbh->prepare( "SELECT max(max) FROM ( $pgUnionQuery ) AS max; " );
      $result->execute(); my @row = $result->fetchrow(); my $highest = $row[0];
      return $highest; }
    else { return "ERROR, no valid datatype for highestPgidTables"; }
} # sub getHighestPgid

### END CONTROL FRAME ACTIONS ###


### UPDATE POSTGRES ###

sub updatePostgresColumn {				# if updating postgres column config table values, update postgres and return OK if ok
  print "Content-type: text/plain\n\n";
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $table) = &getHtmlVar($query, 'field');
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  ($var, my $column_action) = &getHtmlVar($query, 'column_action');
  ($var, my $newValue) = &getHtmlVar($query, 'newValue');
  my $pgtable = '';
  if ($column_action eq 'columnShowHide') { $pgtable = 'oac_column_showhide'; }
  elsif ($column_action eq 'columnWidth') { $pgtable = 'oac_column_width'; }
  elsif ($column_action eq 'columnOrder') { $pgtable = 'oac_column_order'; }

  my @pgcommands; my $returnValue;
  my $deletePgcommand = "DELETE FROM $pgtable WHERE oac_curator = '$curator_two' AND oac_datatype = '$datatype'";
  if ($table ne 'null') { $deletePgcommand .= " AND oac_table = '$table' "; }		# no table restriction for columnOrder
  push @pgcommands, $deletePgcommand;

  if ( ($column_action eq 'columnWidth') || ($column_action eq 'columnShowHide') ) {
    push @pgcommands, "INSERT INTO $pgtable VALUES ('$datatype', '$table', '$curator_two', '$newValue')"; }
  elsif ($column_action eq 'columnOrder') {
    my (@tables) = split/,/, $newValue;
    for (my $i = 0; $i <= $#tables; $i++) {
      my $insertPgcommand = "INSERT INTO $pgtable VALUES ('$datatype', '$tables[$i]', '$curator_two', '$i')"; 
      push @pgcommands, $insertPgcommand; } }

  foreach my $pgcommand (@pgcommands) { my $result = $dbh->do( $pgcommand ) or $returnValue .= "BAD $pgcommand\n"; }
  if ($returnValue) { print $returnValue; } else { print "OK"; }
} # sub updatePostgresColumn

sub updatePostgresTableField {				# if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/plain\n\n";
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $field) = &getHtmlVar($query, 'field');
  ($var, my $pgid) = &getHtmlVar($query, 'pgid');
  ($var, my $newValue) = &getHtmlVar($query, 'newValue'); unless ($newValue) { $newValue = ''; }	# value passed in is dataTable display format, not in editor display format (with parentheses), it's a more certain parse this way.
  if ( ($fields{$datatype}{$field}{type} eq 'multidropdown') || 
       ($fields{$datatype}{$field}{type} eq 'multiontology') ) {			# newValue is "," separated for multiontology only
      if ($newValue =~ m/span style='display: none'/) {
        my (@matches) = $newValue =~ m/<span style='display: none'>(.*?)<\/span>/g;
        $newValue = join'","', @matches ; $newValue = '"' . $newValue . '"'; } }
    else { if ($newValue =~ m/<span style='display: none'>(.*?)<\/span>/) { $newValue = $1; } }	# no surrounding " for non-multiontology
  my $table = $datatype . '_' . $field;
  my ($isOk) = &updatePostgresByTableJoinkeyNewvalue($table, $pgid, $newValue); 
  if ($isOk) { print $isOk; }
} # sub updatePostgresTableField

sub updatePostgresByTableJoinkeyNewvalue {
  my ($table, $pgid, $newValue) = @_;
  my $returnValue = '';
  if ( ($newValue eq '') || ($newValue eq 'undefined') ) { $newValue = 'NULL'; } 	# value is postgres literal NULL
    else { 
      $newValue = &fromUrlToPostgres($newValue); $newValue = "'$newValue'";		# value is converted to postgres format wrapped in singlequotes
      unless (is_utf8($newValue)) { from_to($newValue, "iso-8859-1", "utf8"); } }	# may have non utf8 stuf that needs conversion.
  my @pgids = (); if ($pgid =~ m/,/) { @pgids = split/,/, $pgid; } else { push @pgids, $pgid; }	# .js batchUnsafeUpdateDataTableValues updates multiple joinkeys at once
  foreach my $joinkey (@pgids) {
    my $result = $dbh->do( "DELETE FROM $table WHERE joinkey = '$joinkey'" );
    $result = $dbh->prepare( "INSERT INTO ${table}_hst VALUES ('$joinkey', $newValue)" ); 
    $result->execute() or $returnValue .= "BAD $joinkey INSERT to ${table}_hst\n";
    unless ($newValue eq 'NULL') {			# only make an entry if there is data
      $result = $dbh->prepare( "INSERT INTO $table VALUES ('$joinkey', $newValue)" ); 
      $result->execute() or $returnValue .= "BAD $joinkey INSERT to $table\n"; } }
  unless ($returnValue) { $returnValue = 'OK'; }
  return $returnValue;
} # sub updatePostgresByTableJoinkeyNewvalue

### END UPDATE POSTGRES ###


### TERM INFO ###

sub asyncTermInfo {
  print "Content-type: text/plain\n\n";
  ($var, my $field) = &getHtmlVar($query, 'field');
  ($var, my $userValue) = &getHtmlVar($query, 'userValue');
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  my $matches;
  if ( ($fields{$datatype}{$field}{type} eq 'ontology') || ($fields{$datatype}{$field}{type} eq 'multiontology') ) {
    ($matches) = &getAnyTermInfo($datatype, $field, $userValue); }	# generic obo and specific are different
  print "$matches\n";
} # sub asyncTermInfo

sub getAnyTermInfo {							# call  &getAnySpecificTermInfo  or  &getGenericOboTermInfo  as appropriate
  my ($datatype, $field, $term_id) = @_; my $return_value = '';
  if ($fields{$datatype}{$field}{ontology_type} eq 'obo') {
       ($return_value) = &getGenericOboTermInfo($datatype, $field, $term_id); }
    else {
      if ($configLoaded) {
        if ($term_id =~ m/\( (.*?) \) /) { $term_id = $1; }		# get the id from between the parenthesis
        my $ontology_type = $fields{$datatype}{$field}{ontology_type};
        ($return_value) = &getAnySpecificTermInfo($ontology_type, $term_id); } }
  return $return_value;
} # sub getAnyTermInfo

sub getGenericOboTermInfo {
  my ($datatype, $field, $userValue) = @_;
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  my $obotable = $fields{$datatype}{$field}{ontology_table};
  if ($userValue =~ m/\[.*?\]$/) { $userValue =~ s/\[.*?\]$//; }
  my $joinkey; 
  if ($userValue =~ m/\( (.*?) \) $/) { ($joinkey) = $userValue =~ m/\( (.*?) \) $/; } 
    else { $joinkey = $userValue; }		# get the joinkey from the drop-down itself
  if ($joinkey) {
    my $data_table =  'obo_data_' . $obotable;
    my $result = $dbh->prepare( "SELECT * FROM $data_table WHERE joinkey = '$joinkey';" );
    $result->execute(); my @row = $result->fetchrow();
    unless ($row[1]) { return ''; }
    my $data = $row[1]; $data =~ s/\n/<br \>\n/g;
    if ($data =~ m/action=oboFrame/) { $data =~ s/action=oboFrame/action=oboFrame&field=${field}&datatype=${datatype}&curator_two={$curator_two}/g; }	# storing in obo_data_<obotable> the link to action=oboFrame, but need to pass datatype, field, and curator_two so substituting it here.
    return $data; }
} # sub getGenericOboTermInfo

### END TERM INFO ###

### VALID VALUE ###

sub asyncValidValue {
  print "Content-type: text/plain\n\n";
  ($var, my $field) = &getHtmlVar($query, 'field');
  ($var, my $userValue) = &getHtmlVar($query, 'userValue');
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  my $matches;
  if ( ($fields{$datatype}{$field}{type} eq 'dropdown') || ($fields{$datatype}{$field}{type} eq 'multidropdown') ) {
     ($matches) = &getAnySimpleValidValue($datatype, $field, $userValue); }
  elsif ( ($fields{$datatype}{$field}{type} eq 'ontology') || ($fields{$datatype}{$field}{type} eq 'multiontology') ) {
    if ($fields{$datatype}{$field}{ontology_type} eq 'obo') {
         ($matches) = &getGenericOboValidValue($datatype, $field, $userValue); }
      else {
        if ($configLoaded) {
          my $ontology_type = $fields{$datatype}{$field}{ontology_type};
          ($matches) = &getAnySpecificValidValue($ontology_type, $userValue); } } }
  print $matches;
} # sub asyncValidValue

sub getAnySimpleValidValue {
  my ($datatype, $field, $userValue) = @_; 
  unless ($userValue) { return "false"; }
  my $dropdown_type = $fields{$datatype}{$field}{dropdown_type};
  my %data;
  if ($configLoaded) {
    my $data_ref = &setAnySimpleAutocompleteValues($dropdown_type);
    %data = %$data_ref; }
  foreach my $name (keys %{ $data{$dropdown_type}{name} }) {
    if ($userValue eq $data{$dropdown_type}{name}{$name}) { return "true"; } } 
  return "false";
} # sub getAnySimpleValidValue

sub getGenericOboValidValue {
  my ($datatype, $field, $userValue) = @_;
  my $ontology_table = $fields{$datatype}{$field}{ontology_table};
  my ($value, $joinkey, $syn) = ('bad', 'bad', 'bad');
  unless ($userValue) { return "true"; }
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
  elsif ( $userValue =~ m/^(.*?) \( (.*?) \) \[(.*?)\]$/ ) { ($syn, $joinkey, $value) = $userValue =~ m/^(.*?) \( (.*?) \) \[(.*?)\]$/; }
  my $obotable =  'obo_name_' . $ontology_table;
  $value = &fromUrlToPostgres($value);				# value is converted to postgres format wrapped in singlequotes
  my $result = $dbh->prepare( "SELECT * FROM $obotable WHERE $obotable = '$value' AND joinkey = '$joinkey';" ); $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getGenericOboValidValue

### END VALID VALUE ###


### AUTOCOMPLETE ###

sub autocompleteXHR {						# when typing in an autocomplete field xhr call to this CGI for values
  print "Content-type: text/plain\n\n";
  ($var, my $words) = &getHtmlVar($query, 'query');
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $field) = &getHtmlVar($query, 'field');
  my $matches;
  ($words) = lc($words);					# search insensitively by lowercasing query and LOWER column values
  if ( ($fields{$datatype}{$field}{type} eq 'dropdown') || ($fields{$datatype}{$field}{type} eq 'multidropdown') ) {
       ($matches) = &getAnySimpleAutocomplete($datatype, $field, $words); }
  elsif ( ($fields{$datatype}{$field}{type} eq 'ontology') || ($fields{$datatype}{$field}{type} eq 'multiontology') ) {
    if ($fields{$datatype}{$field}{ontology_type} eq 'obo') { ($matches) = &getGenericOboAutocomplete($datatype, $field, $words); }
      else {
        if ($configLoaded) {
          my $ontology_type = $fields{$datatype}{$field}{ontology_type};
          ($matches) = &getAnySpecificAutocomplete($ontology_type, $words); } } }
  print $matches;
} # sub autocompleteXHR 

sub getGenericOboAutocomplete {
  my ($datatype, $field, $words) = @_;
  my $ontology_table = $fields{$datatype}{$field}{ontology_table};
  my $max_results = 30; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  if ($words =~ m/\'/) { $words =~ s/\'/''/g; }
  my @tabletypes = qw( name syn data );
  my %matches; tie %matches, "Tie::IxHash";			# sorted hash to filter results
  my $primary_table =  'obo_name_' . $ontology_table;
  foreach my $tabletype (@tabletypes) {
    my $obotable = 'obo_' . $tabletype . '_' . $ontology_table;
    my $column = $obotable; if ($tabletype eq 'data') { $column = 'joinkey'; }		# use joinkey for ID instead of data
    my $result = $dbh->prepare( "SELECT * FROM $obotable WHERE LOWER($column) ~ '^$words' ORDER BY $column LIMIT $max_results;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $match = "$row[1] ( $row[0] ) ";
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) { 
        my $result2 = $dbh->prepare( "SELECT * FROM $primary_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); $result2->execute();
        my @row2 = $result2->fetchrow(); my $name = $row2[1];
        if ($tabletype eq 'syn') { $match .= "[$name]"; }
        elsif ($tabletype eq 'data') { $match = "$name ( $row[0] ) "; } }
      $matches{$match}++; }
    $result = $dbh->prepare( "SELECT * FROM $obotable WHERE LOWER($column) ~ '$words' AND LOWER($column) !~ '^$words' ORDER BY $column LIMIT $max_results;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar(keys %matches) < $max_results) ) {
      my $match = "$row[1] ( $row[0] ) ";
      if ( ($tabletype eq 'syn') || ($tabletype eq 'data') ) { 
        my $result2 = $dbh->prepare( "SELECT * FROM $primary_table WHERE joinkey = '$row[0]' LIMIT $max_results;" ); $result2->execute();
        my @row2 = $result2->fetchrow(); my $name = $row2[1];
        if ($tabletype eq 'syn') { $match .= "[$name]"; }
        elsif ($tabletype eq 'data') { $match = "$name ( $row[0] ) "; } }
      $matches{$match}++; }
    last if (scalar(keys %matches) >= $max_results);
  } # foreach my $tabletype (@tabletypes)
  my (@matches) = keys %matches;
  if (scalar(@matches) >= $max_results) { $matches[$#matches] = 'more ...'; }
  my $matches = join"\n", @matches;
  return $matches;
} # sub getGenericOboAutocomplete 


sub getAnySimpleAutocomplete {
  my ($datatype, $field, $words) = @_;
  my $max_results = 40; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my @matches;
  my $dropdown_type = $fields{$datatype}{$field}{dropdown_type};
  my %data;
  if ($configLoaded) {
    my $data_ref = &setAnySimpleAutocompleteValues($dropdown_type);
    %data = %$data_ref; }
  foreach my $name (keys %{ $data{$dropdown_type}{name} }) {
    my $lcname = lc($name);
    my $returnValue = $data{$dropdown_type}{name}{$name}; 		# return name and ID
    if ($lcname =~ m/$words/) { push @matches, $returnValue; }
  } # foreach my $name (keys %{ $data{$dropdown_type}{name} })
  if (scalar(@matches) >= $max_results) { $matches[$#matches] = 'more ...'; }
  my $matches = join"\n", @matches; return $matches;
} # sub getAnySimpleAutocomplete

### END AUTOCOMPLETE ###


### JSON DATA ###

sub jsonFieldQuery {					# json query to make it easier to append values (instead of recreating datatable each time)
  print "Content-type: text/plain\n\n";
  ($var, my $userValue) = &getHtmlVar($query, 'userValue');
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $field) = &getHtmlVar($query, 'field');
  ($var, my $maxPerQuery) = &getHtmlVar($query, 'maxPerQuery');
  ($var, my $allDataTableIds) = &getHtmlVar($query, 'allDataTableIds'); unless ($allDataTableIds) { $allDataTableIds = ''; }

  foreach my $label (keys %{ $fields{$datatype} }) {	# $label is any of field, $field is the user's field to query on
    if ( $fields{$datatype}{$label}{'type'} ) { 
      my $type = $fields{$datatype}{$label}{'type'}; 
      if ( ($type eq 'multidropdown') || ($type eq 'dropdown') ) {			# set fieldIdToValue for dropdown values
        my $dropdown_type = $fields{$datatype}{$label}{dropdown_type};			# $label is any of the usual $field value
        my %data;
        if ($configLoaded) {
          my $data_ref = &setAnySimpleAutocompleteValues($dropdown_type);
          %data = %$data_ref; }
        foreach my $dropdown_type (keys %data) {
          foreach my $name (keys %{ $data{$dropdown_type}{name} }) {
            my $autocompleteValue = $data{$dropdown_type}{name}{$name};
            $autocompleteValue =~ s/ \( /<span style='display: none'>/;
            $autocompleteValue =~ s/ \) /<\/span>/;					# hide the ID in a display none span
            my $id = $data{$dropdown_type}{name}{$name};
            if ($id =~ m/\( (.*?) \)/) { $id = $1; }
            $fieldIdToValue{$dropdown_type}{$id} = $autocompleteValue; } } } } } 	# get just the name vs. get the name and hide the value in a span

  my $column = "${datatype}_$field";							# column may not always be table based
  my @pgtables; my @pgqueries;

  if ($field eq 'id') {									# generic way to get from %datatypes {highestPgidTables}
      if ($datatypes{$datatype}{highestPgidTables}) {
          foreach my $pgtable ( @{ $datatypes{$datatype}{highestPgidTables} } ) { push @pgtables, "${datatype}_${pgtable}"; }
          $column = 'joinkey'; }
        else { return "ERROR, no valid datatype for highestPgidTables"; } }
    else { push @pgtables, "${datatype}_$field"; }

  my @ids = split/,/, $allDataTableIds; my $joinkeys = join"','", @ids; 
  if ($userValue =~ m/\( (.*?) \)/) { $userValue = $1; }
  foreach my $pgtable (@pgtables) {
    if ( ($fields{$datatype}{$field}{type} eq 'multidropdown') || ($fields{$datatype}{$field}{type} eq 'multiontology') ) {	# if it's multidropdown or multiontology, it's an exact value that must have " around it in the DB
      my $queryValue = '"' . $userValue . '"';
      push @pgqueries, "SELECT * FROM $pgtable WHERE $column ~ '$queryValue' AND joinkey NOT IN ( '$joinkeys' ) ORDER BY ${datatype}_timestamp DESC"; }
    elsif ( ($fields{$datatype}{$field}{type} eq 'dropdown') || ($fields{$datatype}{$field}{type} eq 'ontology') ) {		# if it's dropdown or ontology, it's an exact value that must match exactly in the DB
      push @pgqueries, "SELECT * FROM $pgtable WHERE $column = '$userValue' AND joinkey NOT IN ( '$joinkeys' ) ORDER BY ${datatype}_timestamp DESC"; }
    else {															# non-object-restricted fields
      if ($userValue !~ m/.../) {				# if input is less than 3 values, search for exact match
        push @pgqueries, "SELECT * FROM $pgtable WHERE $column = '$userValue' AND joinkey NOT IN ( '$joinkeys' ) ORDER BY ${datatype}_timestamp DESC"; }
      else { push @pgqueries, "SELECT * FROM $pgtable WHERE $column ~ '$userValue' AND joinkey NOT IN ( '$joinkeys' ) ORDER BY ${datatype}_timestamp DESC"; } } }

  if ($fields{$datatype}{$field}{type} eq 'queryonly') {	# queryonly fields don't have postgres tables, get custom query from queryonlySub pointer
    @pgqueries = (); my $pgquery = '';				# replace irrelevant queries in @pgqueries hash
    if ($fields{$datatype}{$field}{queryonlySub}) { my $subref = $fields{$datatype}{$field}{queryonlySub}; $pgquery = &$subref($joinkeys); }
    if ($pgquery) { push @pgqueries, $pgquery; } }		# if there's an appropriate query, add to @pgqueries

  my %joinkeys; 						# good joinkeys, limited by maxPerQuery and timestamp order
  my %all_joinkeys; 						# all results to get a count of how many
  my %hash;							# stores the data for json return
  my $resultCount = 0;						# result count for all queries, not for each query (outside foreach @pgqueries loop)
  foreach my $pgquery (@pgqueries) {
    my $result = $dbh->prepare( $pgquery );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      if ($row[0]) {						# only checks for joinkey, not for data, which would allow querying for blank or NULL if that was permissible.
         $resultCount++; $all_joinkeys{$row[0]}++; 		# count results found, add to all_joinkeys found
         if ( ( ($maxPerQuery) && ($resultCount <= $maxPerQuery) ) || ( !$maxPerQuery ) ) { $joinkeys{$row[0]}++; } } } }	# if less than max wanted (or max wanted is blank), add to joinkeys
  $joinkeys = join"', '", sort {$a<=>$b} keys %joinkeys;
  my @temp = keys %all_joinkeys; my $count_all_result = scalar( @temp );
  my $returnMessage = "Query for $userValue on field $field found $count_all_result new values.";
  if ( ($maxPerQuery) && ($count_all_result > $maxPerQuery) ) { $returnMessage .= " Restricted to $maxPerQuery values returned."; } 
  unless ($joinkeys) { if ( ($field eq 'id') && ($userValue =~ m/,/) ) { 
    $joinkeys = $userValue; $joinkeys =~ s/,/', '/g; } }	# allow query by joinkey of multiple IDs for autoquery off of duplicating rows

  foreach my $field (keys %{ $fields{$datatype} } ) {
    next if ($field eq 'id');
    next if ($fields{$datatype}{$field}{type} eq 'queryonly');
    my $pgtable = "${datatype}_$field";
    my $result = $dbh->prepare( "SELECT * FROM $pgtable WHERE joinkey IN ('$joinkeys')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my $data = '';
      $hash{$row[0]}{'id'} = $row[0]; 				# set the id field rather than query separately for it, this redundantly happens for all tables instead of an arbitrary one, could be made minisculely faster by optimizing this
      $data = &getTableDisplayData($datatype, $field, $row[1]);
      $hash{$row[0]}{$field} = $data; } 
  } # foreach my $field (keys %{ $fields{$datatype} } )
  my @jsonRows;
  push @jsonRows, qq({ "returnMessage" : "$returnMessage" });
  foreach my $joinkey (sort {$a<=>$b} keys %hash) {
    my @dataRow;
    foreach my $field (keys %{ $fields{$datatype} }) {
      my $value = ''; if ($hash{$joinkey}{$field}) { $value = $hash{$joinkey}{$field}; }
      push @dataRow, qq("$field" : "$value"); }
    my $dataRow = join", ", @dataRow;
    push @jsonRows, qq({ $dataRow });
  } # foreach my $joinkey (sort keys %hash)
  my $jsonRows = join",\n", @jsonRows;
  print qq([\n$jsonRows\n]\n);
# the following code has extra commas after the final entry in a set, which javascript can parse but perl cannot.  2014 03 28
#   print "[\n";
#   print "{ \"returnMessage\" : \"$returnMessage\" },\n";
#   foreach my $joinkey (sort {$a<=>$b} keys %hash) {
#     print "{ ";
#     foreach my $field (keys %{ $fields{$datatype} }) {
#       my $value = ''; if ($hash{$joinkey}{$field}) { $value = $hash{$joinkey}{$field}; }
#       print "\"$field\" : \"$value\", "; }
#     print "},\n";
#   } # foreach my $joinkey (sort keys %hash)
#   print "]\n";
} # sub jsonFieldQuery 

sub getTableDisplayData {			# given a pg data entry, get back the names insted of the stored IDs
  my ($datatype, $field, $data) = @_;

  if ( ($fields{$datatype}{$field}{type} eq 'dropdown') || ($fields{$datatype}{$field}{type} eq 'multidropdown') ) {
    my $dropdown_type = $fields{$datatype}{$field}{dropdown_type};
    if ($fieldIdToValue{$dropdown_type}{$data}) { $data = $fieldIdToValue{$dropdown_type}{$data}; } 	# if it's a match, use the value
      elsif ($fields{$datatype}{$field}{type} eq 'multidropdown') {					# if it's multidropdown, loop through entered values and convert
        ($data) = &getAnyMultidropdownIdToValue($dropdown_type, $data); } }

  elsif ( ($fields{$datatype}{$field}{type} eq 'ontology') || ($fields{$datatype}{$field}{type} eq 'multiontology') ) {
    if ($fields{$datatype}{$field}{ontology_type} eq 'obo') {
         ($data) = &getGenericOboIdToValue($datatype, $field, $data); }
      else {
        if ($configLoaded) {
          my $ontology_type = $fields{$datatype}{$field}{ontology_type};
          my $type = $fields{$datatype}{$field}{type};			# need to know if ontology or multiontology to get values with or wo doublequotes
          ($data, my $fieldIdToValue_ref) = &getAnySpecificIdToValue($ontology_type, $type, \%fieldIdToValue, $data);
          %fieldIdToValue = %$fieldIdToValue_ref; } } }			# passing-rewriting %fieldIdToValue so when returning a lot of dataTable rows a given object doesn't have to be converted multiple times (each time it shows up)
  
  $data = &parseJson($data);						# parse for Json
  return $data;
} # sub getTableDisplayData

sub getGenericOboIdToValue {			# convert generic obo values from postgres values (ids) to what someone types for dataTable display
  my ($datatype, $field, $data) = @_;
  my $ontology_table = $fields{$datatype}{$field}{ontology_table};
  my $obotable = 'obo_name_' . $ontology_table;
  $data =~ s/\"//g;				# strip doublequotes
  my $original_data = $data;	
  my (@data) = split/,/, $data; my %results;
  foreach my $id (@data) {
    if ($fieldIdToValue{$obotable}{$id}) { $results{$id} = $fieldIdToValue{$obotable}{$id}; }
    else {
      my $result = $dbh->prepare( "SELECT * FROM $obotable WHERE joinkey = '$id';" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { 
        my $datatableValue = "$row[1]<span style='display: none'>$row[0]</span>"; 
        if ( $fields{$datatype}{$field}{'type'} eq 'multiontology' ) { $datatableValue = '"' . $datatableValue . '"'; }
        $fieldIdToValue{$obotable}{$id} = $datatableValue;
        $results{$id} = $datatableValue; } } }
  $data = join",", sort values %results;
  return $data;
} # sub getGenericOboIdToValue

sub getAnyMultidropdownIdToValue {		# convert multidropdown postgres values (ids) to what someone types for dataTable display
  my ($dropdown_type, $data) = @_;
  my (@data) = split/,/, $data; my %results;
  foreach my $id (@data) { $id =~ s/\"//g; 
    if ($fieldIdToValue{$dropdown_type}{$id}) { $results{$id} = $fieldIdToValue{$dropdown_type}{$id}; } }
  $data = join"\",\"", sort values %results; $data = '"' . $data . '"';
  return $data;
} # sub getAnyMultidropdownIdToValue

sub parseJson {					# escape some xml characters
  my $data = shift;
  if ($data) { 
    if ($data =~ m/\n/s) { $data =~ s/\n/ /sg; }
    if ($data =~ m/"/) { $data =~ s/"/\\"/g; }
    if ($data =~ m//) { $data =~ s///g; }
  }
  return $data;
} # sub parseJson

### END JSON DATA ###


### SHOW HTML ###
 
sub showMain {
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  ($var, my $max_per_query) = &getHtmlVar($query, 'max_per_query');
  ($var, my $batch_unsafe_flag) = &getHtmlVar($query, 'batch_unsafe_flag');
  unless ($max_per_query) { $max_per_query = ''; }
  unless ($batch_unsafe_flag) { $batch_unsafe_flag = ''; }
  my $ip = $query->remote_host();
  if ($configLoaded) { &loginMod('updateModCurator', $ip, $curator_two); }
  print "Content-type: text/html\n\n";
  my $datatypeLabel = $datatype; 		# put the datatype Label on the html title
  if ($datatypes{$datatype}{label}) { $datatypeLabel = uc($datatypes{$datatype}{label}); }
  print "<html>\n<head><title>$datatypeLabel Ontology Annotator</title></head>\n";
  print "<frameset id=\"frameset1\" rows=\"50%,50%\">\n";
  print "  <frameset cols=\"55%,45%\">\n";
  print "    <frame name=\"editor\" src=\"ontology_annotator.cgi?action=editorFrame&datatype=$datatype&curator_two=$curator_two&max_per_query=$max_per_query&batch_unsafe_flag=$batch_unsafe_flag\">\n";
  print "    <frame name=\"obo\" src=\"ontology_annotator.cgi?action=oboFrame\">\n";
  print "  </frameset>\n";
  print "  <frameset rows=\"40px,*\" frameborder=\"no\">\n";
  print "  <frame name=\"controls\" src=\"ontology_annotator.cgi?action=controlsFrame&datatype=$datatype&curator_two=$curator_two&batch_unsafe_flag=$batch_unsafe_flag\">\n";
  print "  <frame name=\"table\" src=\"ontology_annotator.cgi?action=tableFrame&datatype=$datatype&curator_two=$curator_two\">\n";
  print "  </frameset>\n";
  print "</frameset>\n";
  print "</html>\n";
} # sub showMain

sub showEditor {
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  ($var, my $max_per_query) = &getHtmlVar($query, 'max_per_query');
  ($var, my $batch_unsafe_flag) = &getHtmlVar($query, 'batch_unsafe_flag');
  print "Content-type: text/html\n\n";
  print "<html>\n<head>\n";
  # need autocomplete css for autocomplete.  need ontology_annotator.css for div autocomplete.
  print << "EndOfText";
    <!--CSS file (default YUI Sam Skin) --> 
    <!--<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css" />-->
    <link rel="stylesheet" type="text/css" href="yui/2.7.0/autocomplete.css" />
    <link rel="stylesheet" type="text/css" href="ontology_annotator.css" />
EndOfText
  print "</head>\n";
  my $bgcolor = '#EDF5FF'; my $default_input_size = 60; my $inline_input_size = 20; my $border_style_curator = 'ridge'; 
  unless ($max_per_query) { $max_per_query = ''; }
  if ($batch_unsafe_flag) { $bgcolor = 'yellow'; } else { $batch_unsafe_flag = ''; }
  print "<body bgcolor=\"$bgcolor\" class=\"yui-skin-sam\">\n";
  print "<input type=\"hidden\" id=\"datatype\" value=\"$datatype\" \/>\n";
  print "<input type=\"hidden\" id=\"curatorTwo\" value=\"$curator_two\" \/>\n";
  print "<input type=\"hidden\" id=\"maxPerQuery\" value=\"$max_per_query\" \/>\n";
  print "<input type=\"hidden\" id=\"batchUnsafeFlag\" value=\"$batch_unsafe_flag\" \/>\n";

  my %tabs;
  my $table_to_print = '';
  $table_to_print .= "<table>\n";

  foreach my $field (keys %{ $fields{$datatype} }) {
    my $freeForced = 'forced'; my $span_type = ""; my $field_type = ""; my $border_style = "none"; my $tab = ""; my $disabled = ""; my $inline_field = ""; my $input_size = $default_input_size; my $colspan = 3; my $cols_size = ""; my $rows_size = "";
    if ($fields{$datatype}{$field}{'input_size'}) { $input_size   = $fields{$datatype}{$field}{'input_size'}; }
    if ($fields{$datatype}{$field}{'rows_size'})  { $rows_size    = $fields{$datatype}{$field}{'rows_size'};  }
    if ($fields{$datatype}{$field}{'cols_size'})  { $cols_size    = $fields{$datatype}{$field}{'cols_size'};  }
    if ($fields{$datatype}{$field}{'type'})       { $field_type   = $fields{$datatype}{$field}{'type'};       }
    if ($fields{$datatype}{$field}{'tab'})        { $tab          = $fields{$datatype}{$field}{'tab'}; $tabs{$tab}++; }
    if ($fields{$datatype}{$field}{'disabled'})   { $disabled     = qq(disabled = "disabled" );   }		# some fields can be disabled
    if ($fields{$datatype}{$field}{'inline'})     { $inline_field = $fields{$datatype}{$field}{'inline'}; $input_size = $inline_input_size; $colspan = 1; }	# inline fields have extra tds, so need smaller input size and only one colspan to allow more tds.

    next if ($inline_field =~ m/^INSIDE_/);			# these are printed when the field they're INSIDE of are printed

    $table_to_print .= "<tr class=\"$tab\">\n";
    $table_to_print .= &generateEditorLabelTd($field, $datatype);
    if ($field_type eq 'text') {  
      $span_type = ''; $border_style = "none"; 
      $table_to_print .= &showEditorText($field, $datatype, $input_size, $colspan, $disabled); }
    elsif ($field_type eq 'bigtext') {
      $span_type = ''; $border_style = "none"; 
      $table_to_print .= &showEditorBigtext($field, $datatype, $input_size, $cols_size, $rows_size, $colspan, $disabled); }
    elsif ($field_type eq 'textarea') {
      $span_type = ''; $border_style = "none"; 
      $table_to_print .= &showEditorTextarea($field, $datatype, $input_size, $cols_size, $rows_size, $colspan, $disabled); }
    elsif ($field_type eq 'dropdown') { 
      $span_type = '&or;'; $border_style = $border_style_curator;
      $table_to_print .= &showEditorDropdown($field, $datatype, $input_size, $colspan, $freeForced); }
    elsif ($field_type eq 'multidropdown') { 
      $span_type = '&or;'; $border_style = $border_style_curator; 
      $table_to_print .= &showEditorMultidropdown($field, $datatype, $input_size, $span_type, $border_style, $colspan, $freeForced); }
    elsif ($field_type eq 'ontology') { 
      $span_type = '&and;'; $border_style = $border_style_curator; 
      $table_to_print .= &showEditorOntology($field, $datatype, $input_size, $colspan, $freeForced); }
    elsif ($field_type eq 'multiontology') { 
      $span_type = '&and;'; $border_style = $border_style_curator; 
      $table_to_print .= &showEditorMultiontology($field, $datatype, $input_size, $span_type, $border_style, $colspan, $freeForced); }
    elsif ($field_type eq 'queryonly') {  
      $span_type = ''; $border_style = "none"; 
      $table_to_print .= &showEditorQueryonly($field, $datatype, $colspan); }
    elsif ($field_type eq 'toggle') {  
      $span_type = ''; $border_style = "none"; 
      $table_to_print .= &showEditorToggle($field, $datatype, $colspan); }
    elsif ($field_type eq 'toggle_text') {  	# text field in toggle text is small and descriptor large because of tds in multidropdown / multiontology for remove button
      $span_type = ''; $border_style = "none"; $colspan = 1;
      $table_to_print .= &showEditorToggle($field, $datatype, $colspan); 
      $table_to_print .= &generateEditorLabelTd($inline_field, $datatype);
      $table_to_print .= &showEditorText($inline_field, $datatype, $input_size, $colspan, $disabled); }	# button should query off of toggle, not text
    unless ( ($field_type eq 'multidropdown') || ($field_type eq 'multiontology') ) { 		# query button except for multiontology / multidropdown, which have their own in showEditorMultiontology showEditorMultidropdown
      $table_to_print .= &generateEditorSpantypeQuerybuttonTds($field, $border_style, $span_type); }
    $table_to_print .= "</tr>\n";
  } # foreach my $field (keys %{ $fields{$datatype} })
  $table_to_print .= "</table>\n";

  print "<div style=\"font-weight: bold\" id=\"editor_title\">Editor";
  if ($datatypes{$datatype}{label}) { print " " . uc($datatypes{$datatype}{label}); }
  print "<button style=\"float: right\" id=\"resetPage\">Reset</button>\n";
  foreach my $tab (sort keys %tabs) {
    next if ($tab eq 'all');
    print "<button id=\"$tab\">$tab</button>\n";
  }
  if ($batch_unsafe_flag) {
    my $batchUnsafeWarningText = "Warning, changes you make will do a single ajax update to postgres and give an all or nothing error message, but will NOT update the dataTable display below.";
    print "<span style=\"color:red\" id=\"batchUnsafeWarning\" title=\"$batchUnsafeWarningText\" onClick=\"alert('$batchUnsafeWarningText')\";>Invisible Mode</span>\n"; }
  print "</div>";

  print "$table_to_print";
  print "</body></html>\n";
} # sub showEditor


sub showEditorBigtext {
  my ($field, $datatype, $input_size, $cols_size, $rows_size, $colspan, $disabled) = @_;
  unless ($cols_size) { $cols_size = $input_size; }
  unless ($rows_size) { $rows_size = '20'; }
  my $table_to_print = "<td width=\"150\" colspan=\"$colspan\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 150
  $table_to_print .= "<input id=\"input_$field\" name=\"input_$field\" $disabled size=\"$input_size\">\n";
  $table_to_print .= "<div id=\"container_bigtext_$field\"><textarea id=\"textarea_bigtext_$field\" rows=\"$rows_size\" cols=\"$cols_size\" style=\"display:none\"></textarea></div>\n"; 
#   $table_to_print .= "<div id=\"container_bigtext_$field\"><textarea id=\"textarea_bigtext_$field\" rows=\"$rows_size\" cols=\"$cols_size\" ></textarea></div>\n"; 
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorBigtext

sub showEditorTextarea {
  my ($field, $datatype, $input_size, $cols_size, $rows_size, $colspan, $disabled) = @_;
  unless ($cols_size) { $cols_size = $input_size; }
  unless ($rows_size) { $rows_size = '20'; }
  my $table_to_print = "<td width=\"150\" colspan=\"$colspan\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 150
  $table_to_print .= "<div id=\"container_textarea_$field\"><textarea id=\"textarea_$field\" $disabled rows=\"$rows_size\" cols=\"$cols_size\" style=\"display:\"></textarea></div>\n"; 
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorTextarea

sub showEditorText {
  my ($field, $datatype, $input_size, $colspan, $disabled) = @_;
  my $table_to_print = "<td width=\"150\" colspan=\"$colspan\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 150
  $table_to_print .= "<input id=\"input_$field\" name=\"input_$field\" $disabled size=\"$input_size\">\n";
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorText

sub showEditorQueryonly {
  my ($field, $datatype, $colspan) = @_;
  my $width = $colspan / 4 * 100; $width .= '%';
  my $table_to_print = "<td id=\"queryonly_$field\" style=\"empty-cells:show; background-color: white\" width=\"$width\" colspan=\"$colspan\" align=\"center\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorQueryonly

sub showEditorToggle {
  my ($field, $datatype, $colspan) = @_;
  my $width = $colspan / 4 * 100 ; $width .= '%';
  my $table_to_print = "<td id=\"toggle_$field\" style=\"empty-cells:show; border-style:ridge; border-color: grey; background-color: white\" height=\"1\" width=\"$width\" colspan=\"$colspan\" align=\"center\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorToggle

sub showEditorDropdown {
  my ($field, $datatype, $input_size, $colspan, $freeForced) = @_;
  my $table_to_print = "<td width=\"150\" colspan=\"$colspan\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 150
  $table_to_print .= "<span id=\"container${freeForced}${field}AutoComplete\">\n";
  $table_to_print .= "<div id=\"${freeForced}${field}AutoComplete\" class=\"div-autocomplete\">\n"; 
  $table_to_print .= "<input id=\"input_$field\" name=\"input_$field\" size=\"$input_size\">\n";
  $table_to_print .= "<div id=\"${freeForced}${field}Container\"></div></div></span>\n"; 
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorDropdown

sub showEditorMultidropdown {
  my ($field, $datatype, $input_size, $span_type, $border_style, $colspan, $freeForced) = @_;
  my $tab = $fields{$datatype}{$field}{'tab'}; 
  my $table_to_print = &showEditorOntology($field, $datatype, $input_size, $colspan, $freeForced);
  $table_to_print .= &generateEditorSpantypeQuerybuttonTds($field, $border_style, $span_type);
  $table_to_print .= "</tr><tr class=\"$tab\"><td></td><td colspan=\"2\"><select id=\"select_$field\" size=\"1\" multiple=\"multiple\" style=\"min-width: 20em\"></select></td><td><button id=\"button_remove_$field\">remove</button></td>\n";	# changed to size 1 from 2 after .js resize added
  return $table_to_print;
} # sub showEditorMultidropdown

sub showEditorOntology {
  my ($field, $datatype, $input_size, $colspan, $freeForced) = @_;
  my $table_to_print = "<td width=\"150\" colspan=\"$colspan\">\n";	# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 150
  $table_to_print .= "<span id=\"container${freeForced}${field}AutoComplete\">\n";
  $table_to_print .= "<div id=\"${freeForced}${field}AutoComplete\" class=\"div-autocomplete\">\n"; 
  $table_to_print .= "<input id=\"input_$field\" name=\"input_$field\" size=\"$input_size\">\n";
  $table_to_print .= "<div id=\"${freeForced}${field}Container\"></div></div></span>\n"; 
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorOntology

sub showEditorMultiontology {
  my ($field, $datatype, $input_size, $span_type, $border_style, $colspan, $freeForced) = @_;
  my $tab = $fields{$datatype}{$field}{'tab'}; 
  my $table_to_print = &showEditorOntology($field, $datatype, $input_size, $colspan, $freeForced);
  $table_to_print .= &generateEditorSpantypeQuerybuttonTds($field, $border_style, $span_type);
  $table_to_print .= "</tr><tr class=\"$tab\"><td></td><td colspan=\"2\"><select id=\"select_$field\" size=\"1\" multiple=\"multiple\" style=\"min-width: 20em\"></select></td><td><button id=\"button_remove_$field\">remove</button></td>\n";	# changed to size 1 from 2 after .js resize added
  return $table_to_print;
} # sub showEditorMultiontology

sub generateEditorSpantypeQuerybuttonTds {
  my ($field, $border_style, $span_type) = @_;
  my $spantype_querybutton_tds = "<td><span id=\"type_$field\" style=\"border-style:$border_style; border-color: grey\">$span_type</span></td>\n";
  $spantype_querybutton_tds .= "<td><button id=\"button_$field\">query</button></td>";
  return $spantype_querybutton_tds;
} # sub generateEditorSpantypeQuerybuttonTds

sub generateEditorLabelTd {
  my ($field, $datatype) = @_;
  unless ( $fields{$datatype}{$field}{'label'} ) { return "<td>ERROR NO $field FIELD</td>"; }
  my $label = $fields{$datatype}{$field}{'label'}; 
  return "<td id=\"label_$field\">$label</td>";
} # sub generateEditorLabelTd


sub showObo {
  print "Content-type: text/html\n\n";
  ($var, my $text) = &getHtmlVar($query, 'text'); unless ($text) { $text = ''; }
  ($var, my $term_id) = &getHtmlVar($query, 'term_id'); my $term_data = '';
  ($var, my $datatype) = &getHtmlVar($query, 'datatype'); 
  ($var, my $field) = &getHtmlVar($query, 'field');
  ($var, my $obotable) = &getHtmlVar($query, 'obotable');
  if ($term_id) { 
    ($term_data) = &getAnyTermInfo($datatype, $field, $term_id);	# generic obo and specific are different
    my $element_id = "input_$field";
    my ($term_name) = $term_data =~ m/>name : <\/span>\s+(.*?)<br/; 
    unless ($term_name) { $term_name = ''; }				# some term info has no name
    if ($term_name =~ m/<a[^>]*>(.*?)<\/a>/) { $term_name = $1; }	# some names have a links, get only the name
    my $ac_value = "$term_name ( $term_id ) ";
    my $links = "<font size=+4>";
    $links .= "<span style=\"color: blue;  border-style:solid; border-color: grey\" onClick=\"history.go(-1)\">&lArr;</a></span>&nbsp;";
    $links .= "<span style=\"color: blue;  border-style:solid; border-color: grey\" onClick=\"history.go(1)\" >&rArr;</a></span>&nbsp;";
      # set the autocomplete value on the input element, focus, and blur (triggering editorInputBlurListener, which checks the value and populates the datatable
    $links .= "<span style=\"color: green; border-style:solid; border-color: grey\" onClick=\"top.frames['editor'].document.getElementById('$element_id').value = '$ac_value'; top.frames['editor'].document.getElementById('$element_id').focus(); top.frames['editor'].document.getElementById('$element_id').blur(); \" >&radic;</a></span>";
    $links .= "</font><br /><br />";
    $term_data =~ s/name : <\/span>(.*?)<br/name : $1<\/span><br/;	# bold term name
    $term_data = $links . $term_data;
  }
  print "<html>\n<body bgcolor=\"white\">\n";
  print "<b>Term information</b><br/>\n";
  print "$text<br />\n";
  print "<div id=\"termInfo\" name=\"termInfo\">$term_data</div>\n";	# show term info from obo
  print "<div id=\"myObo\"></div>\n";					# show stuff for development like queries and urls called
  print "</body>\n</html>";
} # sub showObo

sub showControls {
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $batch_unsafe_flag) = &getHtmlVar($query, 'batch_unsafe_flag');
  print "Content-type: text/html\n\n";
  print "<html>\n<body bgcolor=\"white\">\n";
  print "<div id=\"loadingImage\"></div>\n";				# to show stuff when loading from query
  my $newRowMaxAmount = $newRowMaxAmountNormalOa;			# get the maximum around of new rows that can be created based on normal OA or batch_unsafe
  if ($batch_unsafe_flag eq 'true') { $newRowMaxAmount = $newRowMaxAmountBatchUnsafeOa; }
  print "<input id=\"newRowMaxAmountValue\" value=\"$newRowMaxAmount\" type=\"hidden\">";	# pass the maximum amount of rows that can be created to javascript
  print "<span id=\"newRowAmount\">1</span>\n";				# how many new rows will be created by pressing the New button
  print "<button id=\"newRow\">New</button>\n";
  print "<button id=\"duplicateRow\">Duplicate</button>\n";
  print "<button id=\"deleteRow\">Delete</button>\n";
  print "<button id=\"checkData\">Check_Data</button>\n";
  print "Filters : \n";
  print "<input type=\"hidden\" id=\"filtersMaxAmount\" value=\"$filtersMaxAmount\" \/>\n";
  print "<select id=\"filtersAmount\" name=\"filtersAmount\" size=\"1\">\n";
  for my $fAmount (1 .. $filtersMaxAmount) { print "<option value=\"$fAmount\">$fAmount</option>\n"; }
  print "</select>\n";
  for my $fAmount (1 .. $filtersMaxAmount) { 
    print "<select id=\"filterType$fAmount\" name=\"filterType$fAmount\" size=\"1\">\n";
    print "<option value=\"all\">all</option>\n";
    foreach my $field (keys %{ $fields{$datatype} }) { print "<option value=\"$field\">$field</option>\n"; }
    print "</select>\n";
    print "<input id=\"filterValue$fAmount\" name=\"filterValue$fAmount\" size=\"20\">\n"; }
  print "</body>\n</html>\n";
} # sub showControls

sub showTable {
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  print "Content-type: text/html\n\n";
  print "<html>\n<head>\n";
  print << "EndOfText";
    <!--CSS file (default YUI Sam Skin) --> 
    <link rel="stylesheet" type="text/css" href="yui/2.7.0/datatable.css" />
    <link rel="stylesheet" type="text/css" href="yui/2.7.0/autocomplete.css" />

    <!-- override free height and visible overflow -->
    <link type="text/css" rel="stylesheet" href="ontology_annotator.css">

    <!-- yui .js -->
    <script type="text/javascript" src="yui/2.7.0/yahoo-dom-event.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/element-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/datasource-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/json-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/connection-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/get-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/dragdrop-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/calendar-min.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/datatable.js"></script> 
    <script type="text/javascript" src="yui/2.7.0/autocomplete-min.js"></script>
    <script type="text/javascript" src="yui/2.7.0/container-min.js"></script> 

    <!-- form-specific js -->
    <script type="text/javascript" src="ontology_annotator.js"></script> 
EndOfText

  print "</head>\n";
  print "<body class=\"yui-skin-sam\" bgcolor=\"white\" style=\"padding: 0; margin: 0\" onResize=\"resizeDataTable();\">\n";
  foreach my $field (keys %{ $fields{$datatype} }) {
    print "<input type=\"hidden\" class=\"fields\" value=\"$field\" \/>\n";
    my $data = '{ ';							# data is { 'tag' : 'value', 'tag2' : 'value2' } format javascript stuff
    foreach my $tag (sort keys %{ $fields{$datatype}{$field} }) { $data .= "'$tag' : '$fields{$datatype}{$field}{$tag}', "; }
    $data =~ s/, $/ }/;
    print "<input type=\"hidden\" id=\"data_$field\" value=\"$data\" \/>\n"; }
  print "<div id=\"myContainer\"></div>\n";
  print "</body>\n</html>\n";
} # sub showTable

sub showLogin {								# if there's no curator $action, show a login page
  print "Content-type: text/html\n\n";
  print "<html>\n<head><title>Ontology Annotator</title></head>\n";
  print "<body>\n";
  print "<form name='form1' method=\"get\" action=\"ontology_annotator.cgi\">\n";
  my $ip = $query->remote_host(); 					# select curator by IP if IP has already been used
  if ($configLoaded) { &loginMod('showModLogin', $ip); }
  print "<table cellpadding=\"4\">\n";
  print "<tr><td colspan=\"3\" valign=\"top\">Max results per query <input name=\"max_per_query\" value=\"100\"></td></tr>\n";
  print "<tr><td colspan=\"3\" valign=\"top\">Invisible / Batch mode <input name=\"batch_unsafe_flag\" type=\"checkbox\" value=\"true\"></td></tr>\n";
  print "</table>\n";
  print "</form>\n";
  print "</body>\n</html>\n";
} # sub showLogin

### END SHOW HTML ###


### FIELDS ###

sub initFields {
  ($var, my $datatype) = &getHtmlVar($query, 'datatype');
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  return unless ($datatype && $curator_two);
  if ($configLoaded) {
    my ($fieldsRef, $datatypesRef) = &initModFields($datatype, $curator_two); 
    %fields = %$fieldsRef;
    %datatypes = %$datatypesRef; }
  my $result = $dbh->prepare( "SELECT * FROM oac_column_width WHERE oac_datatype = '$datatype' AND oac_curator = '$curator_two'" );
  $result->execute(); while (my @row = $result->fetchrow) { $fields{$datatype}{$row[1]}{'columnWidth'} = $row[3]; }
  $result = $dbh->prepare( "SELECT * FROM oac_column_order WHERE oac_datatype = '$datatype' AND oac_curator = '$curator_two'" );
  $result->execute(); while (my @row = $result->fetchrow) { $fields{$datatype}{$row[1]}{'columnOrder'} = $row[3]; }
  $result = $dbh->prepare( "SELECT * FROM oac_column_showhide WHERE oac_datatype = '$datatype' AND oac_curator = '$curator_two'" );
  $result->execute(); while (my @row = $result->fetchrow) { $fields{$datatype}{$row[1]}{'columnShowHide'} = $row[3]; }
} # sub initFields

### END FIELDS ###


__END__


=head1 NAME

ontology_annotator.cgi - Main file with code for ontology_annotator.  CGI for curators to load and make curations through a web browser (tested with Mozilla's Firefox).


=head1 SYNOPSIS

Place on webserver with ontology_annotator.css, ontology_annotator.js, helperOA.pm, yui/ and images/ directories, and MOD-specific perl module (e.g. testOA.pm , wormOA.pm).  Create appropriate MOD-specific perl module for your MOD, in that module add settings for each datatype to curate, and create a postgres table for each datatypes's fields.  Requires web server, CGI, and postgreSQL.


=head1 DESCRIPTION

CGI file for curators to load through a web browser.  When using for a new MOD, create a MOD-specific perl module (see testOA.pm for template and instructions, or wormOA.pm for example and instructions).  In this file add to :

=over 4

=item * add "use testOA;" (only add one module, the exported subroutines have the same name)

=item * add "my $configLoaded = 'testOA';"

=back


=head2 FILES

ontology_annotator.css  REQUIRED has the css properties to display one row in each dataTable, show red squares in dataTable cells that have data not showing, extra padding on autocomplete results div html elements.

ontology_annotator.js  REQUIRED has all the Ontology Annotator-specific javascript code.

helperOA.pm  REQUIRED perl module that has helper subroutines for the main CGI and MOD-specific perl modules.  Get and untaint form variables.  Get timestamps in postgres format.

yui/  REQUIRED directory to hold local copies of the necessary YUI's .js files.  YUI's website is fast and reliable, but just in case keep a local copy.

images/  REQUIRED directory to hold necessary images.  The red square for dataTable cells with more data than showing.  Loading image when querying.

MOD-specific perl modules.  REQUIRED.  See testOA.pm, wormOA.pm for examples.

docs/  OPTIONAL directory to hold html files documenting how scripts, modules, and the CGI work.  Generated by  scripts/generateDocs.pl .

scripts/  OPTIONAL directory to hold perl scripts to generate tables, update ontologies, generate documentation.


=head2 POSTGRES TABLES

There are general postgres tables required for all MODs and datatypes, for curator settings.  There are datatype-specific postgres tables for each MOD's datatypes's field.  See below for specific formats.

Be sure to GRANT ALL on each table to postgres and the webserver user.

Note: It's very likely that a different flavor of SQL may be used with minor code change, but this has not been tested.


=head3 GENERAL POSTGRES TABLES

For the OA to remember a given curator-datatype-field dataTable column's width, order, and whether it should show or be hidden, these tables are required :

=over 4

=item * oac_column_width  columns oac_datatype, oac_table, oac_curator, oac_column_width, oac_timestamp .  The oac_timestamp column is a timestamp with default now, all others are text.  The column width is the width in pixels that a dataTable column should have when loading.  YUI's datatable scripts will still resize is as data gets queries, added, or edited.  When a curator resizes a column, its corresponding value is updated here.

=item * oac_column_order  columns oac_datatype, oac_table, oac_curator, oac_column_order, oac_timestamp .  The oac_timestamp column is a timestamp with default now, all others are text.  The order of the columns are the default order when loaded, which is different from the order of the fields in the OA's editor frame.  When a curator reorders a column, all the columns's corresponding orders are updated here.

=item * oac_column_showhide  columns oac_datatype, oac_table, oac_curator, oac_column_showhide, oac_timestamp .  The oac_timestamp column is a timestamp with default now, all others are text.  dataType columns can be toggled to show or hide by clicking on the corresponding field name in the OA's editor frame (when hidden the text will be grey, when showing the text will be black) ;  this table stores whether to show or hide each column when the dataTable is first loaded.  When a curator toggles a column to hide or show, its corresponding state is updated here.

=back

If some MOD really doesn't want this,  &updatePostgresColumn  could probably be edited to only do this for specific  $configLoaded , and this code change would have to be propagated to other MODs.

create_oac_columns.pl  is a script to delete and re-create these column postgres tables.


=head3 DATATYPE POSTGRES TABLES

When creating a new datatype, each field should have its own postgres table and postgres history table.  The datatype by convention is a three-letter code.  The format of each table would be '<datatype>_<field name>' and for history tables '<datatype>_<field name>_hst', so e.g. : 'app_term' 'app_term_hst', 'int_variationone' 'int_variationone_hst', 'trp_driven_by_gene' 'trp_driven_by_gene_hst'.  

Columns are  joinkey, <table_name>, <datatype>_timestamp .  The <datatype>_timestamp column is a timestamp with default now, all others are text.  The <table_name> column is the same as the name of the table.  e.g. the table app_term  has columns named  joinkey, app_term, app_timestamp ;  and app_term_hst  has columns named  joinkey, app_term_hst, app_timestamp .

There are four different ways of storing data :

=over 4

=item * text and textarea and bigtext types store text straight.

=item * toggle type store the label of the field shown on the editor for true, and '' for false.

=item * dropdown and ontology types store the ID of the chosen value.

=item * multidropdown and multiontology types store the IDs of the chosen values, surrounded by doublequotes and comma-separated.  (for this reason avoid having IDs with doublequotes in them)

=back

create_datatype_tables.pl  is a script to create postgres data tables and history tables for a given datatype and tables.


=head3 OBO POSTGRES TABLES

When creating an ontology or multiontology field, a set of custom subroutines can be created in the MOD-specific perl module (called by  &getAnySpecific...), or the local  &getGenericObo... subroutines, which work off generic obo_ tables in postgres.  To use the latter subroutines, in the MOD-specific perl module, set the fields's  %fields  to have  'ontology_type' = 'obo'  and  'ontology_table' = '<name of ontology type>' .  The name of the ontology type is lowercase by convention.  These two values are set to all fields that use that given ontology for the same MOD ;  multiple datatypes can use it, and/or multiple fields in the same datatype.  Also to use these subroutines, create 3 tables for each set of ontologies :

=over 4 

=item * obo_name_<name of ontology type>  columns joinkey, <table_name>, obo_timestamp .  The obo_timestamp column is a timestamp with default now, all others are text.  This table's key is the object ID, the value is the name of the object.  An object can only have one entry for a given joinkey in this table.

=item * obo_syn_<name of ontology type>  column joinkey, <table_name>, obo_timestamp .  The obo_timestamp column is a timestamp with default now, all others are text.  This table's key is the object ID, the value is the synonym of the object.  An object could have multiple synonyms, so it could have multiple entries for the same joinkey in this table.

=item * obo_data_<name of ontology type>  column joinkey, <table_name>, obo_timestamp .  The obo_timestamp column is a timestamp with default now, all others are text.  This table's key is the object ID, the value is the data of the object to show in the OA's term info frame.  An object can only have one set of data to show, so it can only have one entry for a given joinkey in this table.  The data here will show almost exactly as stored, so html markup is stored here directly ;  the exception is that newlines are replaced with '<br />\n' in the  &getGenericOboTermInfo .  By convention tag names and a colon are wrapped in a '<span style="font-weight: bold">'.  Sections can be divided with a '<hr>'.  Links and embedded images can be linked here.

=back

update_obo_oa_ontologies.pl  is a script to download generic .obo files and update these 3 tables for each corresponding obo ontology type.


=head2 GLOBALS

=head3 OA GLOBALS

$configLoaded  is a variable to specify which MOD-specific perl module has been loaded.  Refer to appropriate subroutine in  &asyncTermInfo  &asyncValidValue  &autocompleteXHR  &getTableDisplayData  &showLogin  &showMain  &initFields .

$filtersMaxAmount  is the amount of filters to put in the OA's control frame.  This could be stored in a postgres table at some point, and code rewritten for it.  The control frame shows one filter by default, and more can be shown by changing the number in the dropdown.

$newRowMaxAmountNormalOa  is the amount of new rows to create when pressing the 'New' button in the normal OA.

$newRowMaxAmountBatchUnsafeOa  is the amount of new rows to create when pressing the 'New' button in the batch unsafe OA.

%fieldIdToValue  is a hash to map IDs of data in postgres to what should be displayed in the dataTable when querying.  When a query will load a lot of values into the dataTable it's wasteful to query each ID to displayValue conversion multiple times for a single ID, so the values are stored in this hash and not re-queried if they already exist.  The first key is the dropdown_type for dropdown / multidropdown fields ;  for ontology / multiontology fields with simple obo_ tables, it's the 'obo_name_<ontology_table> ;  for ontology / multiontology fields with a custom specific lookup, it's the ontology type.  The second key is the ID of the value.  The value of the hash is what should be displayed, "display_value<span style='display: none'>id</span>" ;  the display_value is usually the name of the object, but it could be the ID in cases like WBPapers ;  the id is the ID of the object ;  the <span>s are html element tags to keep the id hidden in the dataTable display, and are used for getting the IDs in the cell when a dataTable row is clicked and they should be loaded to the OA's editor frame's corresponding fields (some display_values map to multiple IDs in some datatypes).

%fields  stores options for the datatype configuration's individual fields, in the format  $fields{<datatype>}{<field_name>}{<option>} .  Its values are initialized from the MOD-specific perl module, and returned here.

%datatypes  stores options for each datatype configuration as a whole, in the format  $datatypes{<datatype>}{<option>} .  Its values are initialized from the MOD-specific perl module, and returned here.

=head3 OTHER  GLOBALS

$dbh  is the DBI database handle for postgreSQL queries.

$query  is the CGI query object.

$var  is a placeholder variable when getting values from the form.

$action  is the action performed by the curator on the form.


=head2 SUBROUTINES


=head3 LOGIN SUBROUTINE

&showLogin  if there's no curator $action, show a login page, call  &initFields  and the appropriate subroutine for the curator's  $action .  &showLogin  has an html form that gets the login options from the MOD-specific perl module, and also shows gives options for  max_per_query  and  batch_unsafe_flag .  max_per_query  is the maximum amount of entries to get from postgres when querying for previously curated data ;  returning too many entries would slow down or freeze the browser depending on the user's computer and the amount of entries ;  a curator can query multiple times to keep getting more values.  batch_unsafe_flag  is a toggle for the javascript to use the  batchUnsafeUpdateDataTableValues  function instead of the defaul  normalSafeUpdateDataTableValues ;  the normal way sends an AJAX call for each row to change, gives individual errors, and updates the dataTable as appropriate ;  the  batch_unsafe  way is a faster way to update multiple postgres entries / dataTable rows, with a single AJAX call for all of them, a single error for all entries, and does not reflect changes in the dataTable ; if this value is toggled, the OA's editor frame has a different background and warning text.


=head3 INITIALIZATION SUBROUTINE

&initFields  calls the MOD-specific subroutine to initialize %fields and %datatypes for that curator-datatype.  It also queries the oac_ postgres tables for that curator-datatype.


=head3 SHOW MAIN SUBROUTINE

&showMain  gets the login variables, IP address, calls the MOD-specific login subroutine, and creates an html page with four frames :

=over 4

=item * 'editor' frame, calling action 'editorFrame' and passing all variables.

=item * 'obo' frame, calling action 'oboFrame'. 

=item * 'controls' frame, calling action 'controlsFrame' and passing the chosen 'datatype' and 'curator_two'.

=item * 'table' frame, calling action 'tableFrame' and passing the chosen 'datatype' and 'curator_two'.

=back


=head3 SHOW EDITOR SUBROUTINES

&showEditor  shows the OA editor frame.  Gets user values and makes hidden inputs for the ontology_annotator.js to get them as needed.  If the  batch_unsafe_flag  is set, the background color of the frame is different.  Creates an html table, and for each %fields's datatype field, it sets some variables :

=over 4

=item * $freeForced  is a flag for whether an dropdown / multidropdown / ontology / multiontology should force values or allow anything that doesn't match in them.  By default all are forced.

=item * $span_type  has the html character to display for dropdown / multidropdown (&and), ontology / multiontology (&or), others display nothing.  This value shows between the input and the query button.  dropdown / multidropdown values can have the html characer clicked to see all possible values.

=item * $field_type  is the  $fields{<datatype>}{<field>}{'type'} .  Depending on the type, a different  &showEditor...  subroutine is called.

=item * $border_style  is the type of border the $span_type html character should have to make it look like a button.

=item * $tab  is the  $fields{<datatype>}{<field>}{'tab'} .  It also adds to  %tabs  which keeps track of how many tabs should be displayed.  The html tr element has a class $tab to determine whether to show that table row depending on which tab has been clicked.

=item * $inline_field  is the  $fields{<datatype>}{<field>}{'inline'} .  Fields that begin with 'INSIDE_' are skipped, because they are the second or later field to display inline. 

=item * $input_size  is the  $fields{<datatype>}{<field>}{'input_size'} .  This is the size of the html input element.  There is a default input size and default input size for inline fields.

=item * $cols_size  is the  $fields{<datatype>}{<field>}{'cols_size'} .  This is the cols size of the html textarea element.

=item * $rows_size  is the  $fields{<datatype>}{<field>}{'rows_size'} .  This is the rows size of the html textarea element.

=item * $colspan  is the size of the html colspan.  By default it is 3, allowing inline fields to have a size of 1 for labels and inputs.

=back

and creates a table row, calling  &generateEditorLabelTd  to generate and append the field's label to the row, then depending on the  $field_type  it calls the appropriate  &showEditor...  subroutine(s) to create the html elements to display in the table.  Fields that are neither multidropdown nor multiontology also generate and print the value from  &generateEditorSpantypeQuerybuttonTds , because these fields are a single table row so their creation subroutines don't add this.  Creates a 'Reset' button that floats right, which calls  ontology_annotator.cgi  function  resetButton  which reloads the obo frame, removes all rows from the dataTable, and blanks all editor values.  Shows the configuration loaded from $datatypes{$datatype}{label}.  Creates a tab html button for each tab in %tabs which when clicked shows only table rows corresponding to that tab.  If  batch_unsafe_flag  is set, a warning text is displayed in an html span element.

If the  $field_type  corresponds to something that should show multiple fields in one row, $colspan changes to more values will fit, and the appropriate separate  &showEditor...  subroutines are called.

&generateEditorLabelTd  generates an html td element, passing in the field and datatype, and returning the td generated td element.  Gets <label> from  $fields{<datatype>}{<field>}{'label'} .  Creates a td element with id 'label_<field>' and <label> for text, the returns it.

&generateEditorSpantypeQuerybuttonTds  generates two html td elements, passing in the field, border_style, and span_type ;  and returning the created td elements.  The first td element has a span with id 'type_<field>', html style's border-style <border_style> and border-color 'grey', and text of <span_type>.  The second td element has a button with id 'button_<field>' and text 'query'.

&showEditorText  creates an html td element for normal input fields, passing in the field, datatype, input_size, and colspan ;  and returning the created td element.  Creates a td element of fixed 150 width, colspan <colspan>, and an input field with id 'input_<field>' and size <input_size>.  The width is fixed because of some auto-sizing to nothing if there is no size. 

&showEditorTextarea  is like  &showEditorText  but is a textarea instead of an input html element.

&showEditorBigtext  is like  &showEditorText  but has an additional html div element with id 'container_bigtext_<field>', which contains a textarea with id 'textarea_bigtext_<field>', with rows <rows_size> or 20 if no value given, cols <cols_size> or <input_size> if no value given, and default style 'display:none'.  When the input field is clicked, the ontology_annotator.js transfers the value to the textarea, hides the input, and shows the textarea.  When blurring the textarea, the ontology_annotator.js transfers the value to the input, hides the textarea, and shows the input.  This allows editing and seeing a large amount of text in a textarea, but normally only seeing a smaller input that takes up less space.

&showEditorQueryonly  creates an html td element for query only fields, passing in the field, datatype, colspan ;  and returning the created td element.  Creates a td element with id 'queryonly_<field>', colspan <colspan>, align 'center', and width of <colspan> / 3 * 100% which makes it take up the full width.  When queried  jsonFieldQuery  gets the custom query from  $fields{<datatype>}{<field>}{queryonlySub} instead of the field's non-existent postgres table.

&showEditorToggle  creates an html td element for query only fields, passing in the field, datatype, colspan ;  and returning the created td element.  Creates a td element with id 'toggle_<field>', colspan <colspan>, align 'center', and width of <colspan> / 3 * 100% which makes it take up the full width.  Background color is 'white' to show 'false' and when clicked,  ontology_annotator.js  toggles the background color to 'red' to show 'true'.

&showEditorDropdown  creates an html td element for dropdown fields, passing in the field, datatype, input_size, colspan, freeForced ;  and returning the created td element.  Creates a td element of fixed width 150 and colspan <colspan> containing an html span of id 'container<freeForced><field>AutoComplete', used by YUI to create autocomplete fields.  This span contains an html div element with id '<freeForced><field>AutoComplete' and class 'div-autocomplete', which contains an html input element with id 'input_<field>' and size <input_size>, and another html div element with id '<freeForced><field>Container'.  Anything typed in the input field will have the  ontology_annotator.js  make an AJAX call to the CGI with action 'autocompleteXHR' to get matching values for the corresponding datatype-field-curator, and display them in the container div.  Dropdown fields can click the span_type to pass a blank as the query value, returning all values for that datatype-field-curator.

&showEditorOntology  is identical to  &showEditorDropdown  but has a separate subroutine, should the display need to become different.  The  ontology_annotator.js  does not set the span_type to query for all values, since ontology fields have too many values for this to be practical.

&showEditorMultidropdown  creates html td and tr elements for multidropdown fields, passing in the field, datatype, input_size, span_type, colspan, freeForced ;  and returning the created td and tr elements.  Gets <tab> from  $fields{<datatype>}{<field>}{'tab'} .  Generates a dropdown td element with  &showEditorDropdown .  Generates html span_type and query button with  &generateEditorSpantypeQuerybuttonTds .  Closes the html tr element.  Creates a new html tr element with class <tab>.   Adds to it a blank html td element for indentation to show it is part of the same field despite being a new row.  Adds to it another html td element containing an html select element with id 'select_<field>' of size 1 allowing multiple values to be selected.  Adds another html td element, containing an html button with id 'button_remove_<field>' and label 'remove'.  When adding a new value in the autocomplete input element,  ontology_annotator.js  adds it to the select element, and resizes the select element to a size equal to the elements in the field so all values always show in it.  Clicking the remove button calls  ontology_annotator.js  removeSelectFieldEntriesListener  which removes all selected values from the select element and resizes the select element to a size equal to the elements in the select field so it takes up no more space than needed to show all values.

&showEditorMultiontology  is identical to  &showEditorMultidropdown  but has a separate subroutine, should the display need to become different.  The  ontology_annotator.js  does not set the span_type to query for all values, since ontology fields have too many values for this to be practical.


=head3 SHOW OBO SUBROUTINES

&showObo  shows the OA obo / term information frame.  Gets text, term_id, datatype, field, obotable from the form.  Creates an html div element with id 'termInfo' with <term_data> as text.  Creates an html div element with id 'myObo' as a placeholder for debugging messages.  The <term_data> comes from  &getAnyTermInfo .  The ac_value is the '<term_name> ( <term_id> ) ' from <term_data>.  Links are created and added at the top :  an arrow left (html &lArr; character) to go back a frame ;  an arrow right (html &rArr; character) to go forward a frame ;  a "check mark" (html &radic; character) to set the value of the 'input_<field>' to <ac_value>, focus, and blur (to trigger the  ontology_annotator.js  blur action to update postgres and the dataTable.  The value of the name tag is moved inside the span to bold it.

&getAnyTermInfo  generates term_data, passing in datatype, field, term_id ;  and returning the term data.  If the field's ontology_type is 'obo', it calls  &getGenericOboTermInfo  to get data from generic postgres obo_ tables.  Otherwise it checks the  $configLoaded  and calls the MOD-specific subroutine to get term info ;  if any are loaded it calls  &getAnySpecificTermInfo .

&getGenericOboTermInfo  generates term_data from generic postgres obo_ tables, passing in datatype, field, userValue ;  and returning the term data.  Gets the curator from the form.  Get the obotable from $fields{<datatype>}{<field>}{'ontology_table'} .  Gets the obo_ joinkey from the userValue.  Query postgres obo_data_<obotable>.  Return blank '' if there is no data.  Replace newlines with html br elements + newlines.  If the data has 'action=oboFrame', globally replace it with same + "field=<field>&datatype=<datatype>&curator_two=<curator>", which is necessary to have the proper values in the obo frame when traveling forward and back, and selecting a value.  Return 


=head3 SHOW CONTROLS SUBROUTINE

&showControls  shows the OA controls frame.

Gets the datatype from the form.  

Creates an html div element with id 'loadingImage' to hold the image when loading data from a postgres query.  

Creates a hidden html input element with id 'newRowMaxAmountValue' that stores the maximum amount of new rows to create with the 'New' button.  This value is  $newRowMaxAmountNormalOa  by default, or  $newRowMaxAmountBatchUnsafeOa  if the  $batch_unsafe_flag  is set to 'true'.

Creates an html span element with id 'newRowAmount' with default value 1, to determine the amount of rows that will be created when pressing the button 'New'  ;  when clicked the  ontology_annotator.js  calls  changeNewRowAmountPromptListener  which gives a prompt to enter a value up to  $newRowMaxAmount .

Creates an html button element with id 'newRow' to create a new dataTable row ;  when clicked the  ontology_annotator.js  calls  newRowButtonListener  which does an AJAX call to the CGI with action 'newRow', creating and getting a new pgid / joinkey, then doing another AJAX call to the CGI with action  jsonFieldQuery  passing the new pgid and getting the created row to load and highlight in the dataTable.  

Creates an html button element with id 'duplicateRow' to create a new dataTable row for each dataTable row that is selected, all values except for pgid / joinkey are duplicated ;  when clicked the  ontology_annotator.js  calls  duplicateRowButtonListener  which does an AJAX call to the CGI with action 'duplicateByPgids', getting the newly created pgids, doing another AJAX call to the CGI with action  jsonFieldQuery  passing the new pgids and getting the created rows to load and highlight in the dataTable.  

Creates an html button element with id 'deleteRow' to delete selected dataTable rows ;  when clicked the  ontology_annotator.js  calls  deleteRowButtonListener  which does an AJAX call to the CGI with action 'deleteByPgids', deleting the entries from the postgres tables and from the dataTable.

Creates an html button element with id 'checkData' to optionally check data in the dataTable against datatype-specific constraints ;  when clicked the  ontology_annotator.js  calls  checkDataButtonListener  which does an AJAX call to the CGI with action 'checkDataByPgids', if return values are not 'OK', a popup window is openend and focused, loading the messages from the return value.

Creates a hidden html input element with id 'filtersMaxAmount' that stores the maximum amount of filters.

Creates an html select element with id 'filtersAmount', and options 1 through the maximum amount of filters.  When the form loads or this value changes, the  ontology_annotator.js  calls  updateFiltersAmount  which shows only that amount of filtering pairs (see next paragraph).

For the maximum amount of filters, creates pairs of html elements.  An html select element with id 'filterType<count>' with options 'all' and each of the fields from $fields{<datatype>}.  An html input element with id 'filterValue<count>' for the curator's text to filter on.  When something is typed into an input, the  ontology_annotator.js  will show only the dataTable rows that contain the typed text in the corresponding 'filterType<count>' column.


=head3 SHOW TABLE SUBROUTINE

&showTable  shows the OA dataTable frame.  This frame loads all the required .css and .js files into the html head element ;  when reloading the form, be sure to reload this frame to update those files.

Gets the datatype from the form.

The html body element needs to have class 'yui-skin-sam'.  When resized, the  ontology_annotator.js  calls  resizeDataTable  which sets the height of html div elements with class 'yui-dt-bd', because they tend to be too big and create scrollbars.

For each field from $fields{<datatype>}, create an html input element of class 'fields' with value <field>.  For each field's tag, get data from $fields{<datatype>}{<field>}{<tag>} and create "'<tag>' : '<data>'" pairs to join with commas, and store in an html input field with id 'data_<field>'.  The  ontology_annotator.js  looks up all the fields from the inputs of class 'fields', and gets the  fieldsData  from each field's 'data_<field>' html input element.


=head3 JSON FIELD QUERY SUBROUTINES

&jsonFieldQuery  generates a text page for returning AJAX queries for postgres data.  Gets userValue, datatype, field, maxPerQuery, allDataTableIds from form ;  and returns JSON of return message and entries for data for each postgres joinkey / dataTable row.   userValue is what to query for, datatype is the datatype to query for, field is the datatype's field to query on, maxPerQuery is the maximum rows to return, allDataTableIds are the joinkeys already in the dataTable that should be skipped when querying.  Fields of type dropdown or multidropdown check the MOD-specific perl module for the subroutine to have their values added to  $fieldType{<dropdown_type>}{<id>} = <autocomplete_value>  where the autocomplete_value has the id hidden in a 'display: none' html span element, for loading into the dataTable.  The pgtable to query is the '<datatype>_<field>', but if the field is 'id', it should instead query the tables from $datatypes{<datatype>}{highestPgidTables} .  For each table to query :  If the field type is multiontology or multidropdown, the value to query should have doublequotes around it ;  query for the userValue on the table where the joinkey is not already in the dataTable in descending timestamp order.  If the field type is ontology or dropdown ;  query for the userValue on the table where the joinkey is not already in the dataTable in descending timestamp order.  If the field type is neither, and the userValue to query has three or more characters, do an exact query ;  if it has less than three characters do a substring query ;  query for the userValue on the table where the joinkey is not already in the dataTable in descending timestamp order.  If the field type is queryonly, remove the crafted queries, because queryonly fields do not correspond to postgres tables, and instead get the postgres query from  $fields{<datatype>}{<field>}{queryonlySub} .  Query postgres for those queries, and get the joinkeys / pgids, ignoring results over the maxPerQuery limit ;  create returnMessage of values the query found.  For each $fields{<datatype>} that has a postgres table, query for the data corresponding to the joinkeys to return, filtering the data through  &getTableDisplayData  and storing it in  $hash{<joinkey>}{<field>} .  Print to text page JSON format representation of hash, with the returnMessage as the first entry, and each joinkey's data as the next entries.

&getTableDisplayData  converts data to proper JSON-format data, and if appropriate to the MOD-specific perl module adds any specific ontology or multiontology to the %fieldIdToValue.  Passes in datatype, field, data ;  and returns formatted data.  If the field is of type dropdown or multidropdown, get the dropdown_type from  $fields{<datatype>}{<field>}{dropdown_type} ;  if data exists in  $fieldIdToValue{<dropdown_type>}{<data>}  use that as the data value.  If the field is of type multiontology or ontology, and the field's ontology_type is 'obo', call  &getGenericOboIdToValue ;  otherwise check  $configLoaded  and call the appropriate subroutine ;  if any are loaded it calls  &getAnySpecificIdToValue  and updates  %fieldIdToValue from values there.  Any data is cleaned through  &parseJson .

&getGenericOboIdToValue  converts generic obo values from postgres values (ids) to what someone types for dataTable display, passing in datatype, field, data ;  and returning the parsed data.  Get ontology_table from  $fields{<datatype>}{<field>}{ontology_table} .  Get obotable as 'obo_name_<ontology_table>'.  Strip data of doublequotes (if an Id has a doublequote the lookup here will fail), split user data on commas in case it's multiontology data, and for each id :  Check if it has already been looked up in  $fieldIdToValue{<obotable>}{<id>} , using that value if so ;  otherwise query the postgres table <obotable> for a joinkey of value <id>, and if matching create a value being the postgres table value + an html span element with style 'display: none' containing the <id> / joinkey ;  if the field's type is multiontology add surrounding doublequotes ;  assign this id-value pair to  $fieldIdToValue{<obotable>}{<id>} for future lookup, and to the results to return.  Join results with commas and return.

&getAnyMultidropdownIdToValue  converts multidropdown postgres values (ids) to what someone types for dataTable display, passing in dropdown_type and data ;  and returning the parsed data.  Strip data of doublequotes (if an Id has a doublequote the lookup here will fail), split user data on commas in case it's multidropdown data, and for each id :  Check if it has already been looked up in  $fieldIdToValue{<dropdown_type>}{<id>} , using that value if so.  Join results with doublequote-comma-doublequote, wrap in doublequotes, and return.

&parseJson  escapes some xml characters, passing in data and returning the cleaned data.  Newlines are globally replaced with spaces.  Doublequotes are espaced with backslashes.  Literal newlines are stipped.


=head3 AUTOCOMPLETE SUBROUTINES

&autocompleteXHR  generates a text page for returning AJAX queries for autocompletion fields.  From the form gets datatype, field, and words from the default YUI autocomplete field 'query' ;  and prints rows of autocomplete values for the container html div element.  Words are lower cased.  If the field type is dropdown or multidropdown call  &getAnySimpleAutocomplete .  If the field type is ontology or multiontology, and the field's ontology_type is 'obo', call  &getGenericOboAutocomplete ;  otherwise check  $configLoaded  and call the appropriate subroutine ;  if any are loaded it calls  &getAnySpecificAutocomplete .  Print result matches.

&getAnySimpleAutocomplete  generates ordered autocomplete matches for dropdown or multidropdown fields, passing in datatype, field, words ;  and returning the result matches.  Get dropdown_type from  $fields{<datatype>}{<field>}{dropdown_type} .  max_results is the maximum amount of autocomplete objects to return, by default it is 40, but if there are 5 or more characters typed it becomes 500 to match with &getGenericOboAutocomplete.  Call the MOD-specific perl module subroutine to get the values for the dropdown_type.  Return matching values.

&getGenericOboAutocomplete  generates autocomplete matches from generic postgres obo_ tables, passing in datatype, field, words ;  and returning the result matches.  Get ontology_table from  $fields{<datatype>}{<field>}{ontology_table} .  max_results is the maximum amount of autocomplete objects to return, by default it is 30, but if there are 5 or more characters typed it becomes 500 because some GO ontologies have hundreds of terms with the same words.  Singlequotes are escaped for postgres queries.  The three tabletypes of postgres obo_ tables are name (id to name mapping), syn (id to synonyms), data (id to full data for term info display).  Results are stored in a tied hash to maintain order.  For each tabletype obotable is 'obo_<tabletype>_<ontology_table>'.  The column to match on is the table name, but for tabletype 'data' query the joinkey column.  Query the table matching the column for lower cased values starting with <words>, sorted by column, with a limit of max_results to avoid getting too many results that won't show anyway.  Get up to max_results, getting the data as '<data> ( <id> ) '.  If the tabletype is 'syn' or 'data' query the name tabletype to get the object's name.  If the tabletype is 'syn' append a '[<name>]' ;  if the tabletype is 'data', replace the match with '<name> ( <id> ) '.  Query again the same way matching for the word anywhere in the field except for in the beginning.  If there are more matches than max_results replace the last value with 'more ...' to let the user know there are more values.  Return matches.


=head3 ASYNC TERM INFO SUBROUTINE

&asyncTermInfo  generates a text page for returning AJAX queries for term information of fields of type ontology or multiontology.  From the form gets datatype, field, userValue ;  and prints term information for the termInfo html div element of the OA's obo frame.  Calls  &getAnyTermInfo  (see  SHOW OBO SUBROUTINES ).


=head3 ASYNC VALID VALUE SUBROUTINES

&asyncValidValue  generates a text page for returning AJAX queries to check if an autocomplete value is valid.  From the form gets datatype, field, userValue ;  and prints whether it is 'OK' or has an error message.  If the field type is dropdown or multidropdown call  &getAnySimpleValidValue .  If the field type is ontology or multiontology, and the field's ontology_type is 'obo', call  &getGenericOboValidValue ;  otherwise check  $configLoaded  and call the appropriate subroutine ;  if any are loaded it calls  &getAnySpecificValidValue .  Print result matches.

&getAnySimpleValidValue  checks whether a value exists in a dropdown or multidropdown fields, passing in datatype, field, userValue ;  and returning 'true' or 'false'.  Get dropdown_type from  $fields{<datatype>}{<field>}{dropdown_type} .  Call the MOD-specific perl module subroutine to set the values for the dropdown_type, then loop through them returning 'true' if found, returning false if there is no match.

&getGenericOboValidValue  checks whether a value exists in a generic postgres obo_ tables, passing in datatype, field, userValue ;  and returning 'true' or 'false'.  Get ontology_table from  $fields{<datatype>}{<field>}{ontology_table} .  Get obotable as 'obo_name_<ontology_table>'.  Get the value and joinkey from the userValue.  Convert userValue from URL to postgres format with  &fromUrlToPostgres  for postgres query.  If both joinkey and value have an entry in the postgre obotable return 'true', otherwise return 'false'.


=head3 UPDATE POSTGRES TABLE FIELD SUBROUTINES

&updatePostgresTableField  generates a text page for returning AJAX updates, called when an editor field is blurred, to update corresponding postgres tables.  From the form gets datatype, field, pgid, newValue ;  and prints 'OK' if successful or error message.  If the field's type is multiontology or multidropdown get the ids from within the html span elements, join them with doublequotes, and wrap them in doublequotes ;  otherwise if the field has an html span element, get the id from within it ;  otherwise the value stays the same.  The postgres table is '<datatype>_<field>', call  &updatePostgresByTableJoinkeyNewvalue  and print whether it is 'OK' or has an error message.

&updatePostgresByTableJoinkeyNewvalue  updates postgres data tables for a given table and pgids, passing in table, pgid, newValue ;  and returning 'OK' if successful or error message.  Convert newValue from URL to postgres format with  &fromUrlToPostgres  for postgres command, wrap in singlequotes, and convert to utf8 if it is not ;  if there's no newValue set it to NULL.  ontology_annotator.js  has a  batchUnsafeUpdateDataTableValues  mode to update multiple table entries at once for multiple pgids, so split on comma to get array of pgids.  For each pgid delete that pgid's entry from the main table, insert NULL or value into the postgres history table, and if there's a value insert into the postgres data table.  If there are errors return them, otherwise return 'OK'.


=head3 UPDATE POSTGRES COLUMN SUBROUTINE

&updatePostgresColumn  generates a text page for returning AJAX updates, called when a dataTable column setting changes, to update corresponding postgres tables.  From the form gets datatype, table, curator, column action, newValue ;  and prints 'OK' if successful or error message.  Set the pgtable depending on the column action.  Delete from the table for the curator, datatype, and table.  For columnWidth and columnShowHide insert new value.  For columnOrder get the tables in order and insert them with count.  Print whether it is 'OK' or has an error message.


=head3 NEW ROW SUBROUTINES

&newRow  generates a text page for returning AJAX updates of new datatype object creation of dataTable / postgres table data.  From the form gets amount of rows to create, datatype, and curator ;  and prints whether the creation is 'OK' or has an error message.  Get the highest used pgid from  &getHighestPgid .  If it's not a digit give an error.  If there are less than 2 rows to create, make 1 row.  For each row to create get a new pgid, if there's a  newRowSub  for the datatype use it, if there are errors (non digits response) add them to list to print, add created pgids to list of created pgids.  If there are errors print them, otherwise print 'OK' ;  followed by distinct divider for  ontology_annotator.js  newRowButtonListener  to separate data ;  followed by the pgids created with comma-separation.

&getHighestPgid  gets the highest used pgid from the postgres tables, passing in the datatype ;  and returning the highest pgid.  Gets the postgres tables to check from  $datatypes{<datatype>}{highestPgidTables}  and queries for the highest joinkey as an integer, returning it, or gives an error message.


=head3 DUPLICATE BY PGIDS SUBROUTINE

&duplicateByPgids  generates a text page for returning AJAX updates of duplications of dataTable / postgres table data.  From the form gets datatype and idsToDuplicate ;  and prints whether the duplications are 'OK' or have an error message, as well as a distinct divider and the newly duplicated pgids.  Get the highest used pgid from  &getHighestPgid (see  NEW ROW SUBROUTINES ).  If it's not a digit give an error.  Split idsToDuplicate on comma to get array of pgids.  For each pgid get a new pgid to create and loop through each datatype's field, skipping 'id' field and fields of type 'queryonly', making the postgres table as '<datatype>_<field>', querying the pgid to duplicate for data, and if it has data calling  &updatePostgresByTableJoinkeyNewvalue  on the table, new pgid, and retrieved data.  If there are errors print them, otherwise print 'OK' ;  followed by distinct divider for  ontology_annotator.js  duplicateRowButtonListener  to separate data ;  followed by comma-joined duplicated pgids.


=head3 DELETE BY PGIDS SUBROUTINE

&deleteByPgids  generates a text page for returning AJAX updates of deletions from dataTable / postgres table data.  From the form gets datatype and idsToDelete ;  and prints whether the deletions are 'OK' or have an error message.  Split idsToDelete on comma to get array of pgids.  For each pgid loop through each datatype's field, skipping 'id' field and fields of type 'queryonly', making the postgres table as '<datatype>_<field>', querying it for a row with that pgid, and if it has some call  &updatePostgresByTableJoinkeyNewvalue  on the table, pgid, and blank '' data.  If there are errors print them, otherwise print 'OK'.  This should never print anything because postgres deletes don't give errors and NULL inserts are skipped.


=head3 CHECK DATA BY PGIDS SUBROUTINES

&checkDataByPgids  generates a text page for returning AJAX queries to check if dataTable data passes tests for the datatype ;  one test can be whether specific tables require data, the other is for custom constraints (e.g. a field's data fits a format, or any of N fields have data).  From the form gets datatype, allDataTableIds ;  and prints whether it is 'OK' or has an error message.  Checks  $datatypes{<datatype>}{constraintTablesHaveData}  to see if there is a list of tables that must have data for the datatype, calling  &checkDataInPgTable .  Checks  $datatypes{$datatype}{constraintSub}  to see if there is a special constraint subroutine for additional checks, calling it.  If either check gets an error message, print the error message(s), otherwise print 'OK'.

&checkDataInPgTable  checks whether all pgids in the dataTable have data for a list of tables for the datatype, passing in datatype, arrayref, and allDataTableIds ;  and returning any error messages or blank ''.  arrayref is the reference to the array of tables that should have data in  $datatypes{<datatype>}{constraintTablesHaveData} .  allDataTableIds are the comma-separated pgids passed in from the AJAX call to  &checkDataByPgids .  Gets list of ids by splitting on comma, creates joinkeys by joining on singlequote-comma-singlequote for postgres query.  If arrayref has no tables returns (blank).  For each table makes the postgres table as '<datatype>_<table>', querying the table and joinkeys, hashing all joinkeys and tables.  For each pgid to check, if there's no hash entry adds error to returnMessage ;  otherwise checks each table for id-table in the hash, if there's no value add to list of tablesMissingData, then add all pgid-tablesMissingData to returnMessage.  Return returnMessage.

