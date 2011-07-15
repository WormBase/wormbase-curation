package testOA;
require Exporter;

# Test MOD configuration for Ontology Annotator
# 
# See the bottom of this file for the POD documentation.  Search for the string '=head'.



our @ISA        = qw(Exporter);
our @EXPORT     = qw( initModFields loginMod setAnySimpleAutocompleteValues getAnySpecificAutocomplete getAnySpecificValidValue getAnySpecificTermInfo getAnySpecificIdToValue );
our $VERSION    = 1.00;

use strict;
use diagnostics;
use LWP::UserAgent;
use helperOA;		# &getPgDate  &getHtmlVar  &pad10Zeros  &pad8Zeros
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
use Tie::IxHash;


### FIELDS ###

sub initModFields {
  my ($datatype, $curator_two) = @_;
  &initTestFields($datatype, $curator_two); }

sub initTestFields {
  my ($datatype, $curator_two) = @_;
  my $fieldsRef; my $datatypesRef;
  if ($datatype eq 'tst')    { ($fieldsRef, $datatypesRef) = &initTestTstFields($datatype, $curator_two); }
  return( $fieldsRef, $datatypesRef);
} # sub initTestFields

sub initTestTstFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{tst} }, "Tie::IxHash";
  $fields{tst}{id}{type}                             = 'text';
  $fields{tst}{id}{label}                            = 'pgid';
  $fields{tst}{id}{tab}                              = 'tab1';
  $fields{tst}{name}{type}                           = 'text';
  $fields{tst}{name}{label}                          = 'Name';
  $fields{tst}{name}{tab}                            = 'tab1';
  $fields{tst}{animals}{type}                        = 'multidropdown';
  $fields{tst}{animals}{label}                       = 'Animals';
  $fields{tst}{animals}{tab}                         = 'tab1';
  $fields{tst}{animals}{dropdown_type}               = 'animal';
  $fields{tst}{dataflag}{type}                       = 'toggle_text';
  $fields{tst}{dataflag}{label}                      = 'Data';
  $fields{tst}{dataflag}{tab}                        = 'tab1';
  $fields{tst}{dataflag}{inline}                     = 'datatext';
  $fields{tst}{datatext}{type}                       = 'text';
  $fields{tst}{datatext}{label}                      = 'Data Text';
  $fields{tst}{datatext}{tab}                        = 'tab1';
  $fields{tst}{datatext}{inline}                     = 'INSIDE_datatext';
  $fields{tst}{curator}{type}                        = 'dropdown';
  $fields{tst}{curator}{label}                       = 'Curator';
  $fields{tst}{curator}{tab}                         = 'tab1';
  $fields{tst}{curator}{dropdown_type}               = 'curator';
  $fields{tst}{remark}{type}                         = 'bigtext';
  $fields{tst}{remark}{label}                        = 'Remark';
  $fields{tst}{remark}{tab}                          = 'tab1';
  $fields{tst}{nodump}{type}                         = 'toggle';
  $fields{tst}{nodump}{label}                        = 'NO DUMP';
  $fields{tst}{nodump}{tab}                          = 'tab2';
  $fields{tst}{person}{type}                         = 'ontology';
  $fields{tst}{person}{label}                        = 'Lead Author';
  $fields{tst}{person}{tab}                          = 'tab2';
  $fields{tst}{person}{ontology_type}                = 'WBPerson';
  $fields{tst}{otherpersons}{type}                   = 'multiontology';
  $fields{tst}{otherpersons}{label}                  = 'Collaborators';
  $fields{tst}{otherpersons}{tab}                    = 'tab2';
  $fields{tst}{otherpersons}{ontology_type}          = 'WBPerson';
  $fields{tst}{date}{type}                           = 'text';
  $fields{tst}{date}{label}                          = 'Date Published';
  $fields{tst}{date}{tab}                            = 'tab2';
  $fields{tst}{searchnew}{type}                      = 'queryonly';
  $fields{tst}{searchnew}{label}                     = 'Search new';
  $fields{tst}{searchnew}{tab}                       = 'tab2';
  $fields{tst}{searchnew}{queryonlySub}              = \&checkTstQueryonly;
  $datatypes{tst}{newRowSub}                         = \&newRowTst;
  $datatypes{tst}{constraintSub}                     = \&checkTstConstraints;
  @{ $datatypes{tst}{constraintTablesHaveData} }     = qw( name curator date );
  @{ $datatypes{tst}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initTestTstFields

### END FIELDS ###


### NEW ROW ###

sub insertToPostgresTableAndHistory {		# to create new rows, it is easier to have this sub in multiple <mod>OA.pm files than change the database in the helperOA.pm 
  my ($table, $joinkey, $newValue) = @_;
  my $returnValue = '';
  my $result = $dbh->prepare( "INSERT INTO $table VALUES ('$joinkey', '$newValue')" );
  $result->execute() or $returnValue .= "ERROR, failed to insert to $table &insertToPostgresTableAndHistory\n";
  $result = $dbh->prepare( "INSERT INTO ${table}_hst VALUES ('$joinkey', '$newValue')" );
  $result->execute() or $returnValue .= "ERROR, failed to insert to ${table}_hst &insertToPostgresTableAndHistory\n";
  unless ($returnValue) { $returnValue = 'OK'; }
  return $returnValue;
} # sub insertToPostgresTableAndHistory

sub newRowTst {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('tst_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }

### END NEW ROW ###



### CONSTRAINTS ###

sub checkTstConstraints {
  my ($allDataTableIds) = @_;
  my @ids = split/,/, $allDataTableIds; my $joinkeys = join"','", @ids; 
  my $returnMessage = "";
  my $result = $dbh->prepare( "SELECT * FROM tst_date WHERE joinkey IN ('$joinkeys')" );
  $result->execute(); 
  while (my @row = $result->fetchrow()) { if ($row[1]) { 
    my ($isPgTimestamp) = &checkValueIsPgTimestamp($row[1]); 
    if ($isPgTimestamp) { $returnMessage .= "pgid $row[0] : $isPgTimestamp"; } } }
  return $returnMessage;
} # sub checkTstConstraints

sub checkValueIsPgTimestamp {
  my ($val) = @_;
  if ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}\.\d+\-\d{2}$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}\.\d+$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2}$/) { return; }
  else { return "$val not in postgres timestamp format<br />\n"; }
} # sub isPgTimestamp

### END CONSTRAINTS ###


### QUERY ONLY ###

sub checkTstQueryonly {		# sample query only field with a made-up query.  should filter out joinkeys, and probably order by desc timestamp.
  my ($joinkeys) = @_;							# joinkeys already in dataTable to exclude from query
  return "SELECT joinkey FROM tst_name WHERE joinkey NOT IN ('$joinkeys') AND tst_name ~ 'arIs' ORDER BY tst_timestamp DESC";
} # sub checkTrpQueryonly

### END QUERY ONLY ###



### ONTOLOGY / MULTIONTOLOGY ###

### AUTOCOMPLETE ###

sub setAnySimpleAutocompleteValues {
  my ($ontology_type) = @_;
  my %data;
  if ($ontology_type eq 'curator') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"Juancarlos Chan"} = "Juancarlos Chan ( WBPerson1823 ) ";
    $data{$ontology_type}{name}{"Wen Chen"} = "Wen Chen ( WBPerson101 ) ";
    $data{$ontology_type}{name}{"Jolene Fernandes"} = "Jolene Fernandes ( WBPerson2021 ) ";
    $data{$ontology_type}{name}{"Chris"} = "Chris ( WBPerson2987 ) ";
    $data{$ontology_type}{name}{"Ranjana Kishore"} = "Ranjana Kishore ( WBPerson324 ) ";
    $data{$ontology_type}{name}{"Daniela Raciti"} = "Daniela Raciti ( WBPerson12028 ) ";
    $data{$ontology_type}{name}{"Arun Rangarajan"} = "Arun Rangarajan ( WBPerson4793 ) ";
    $data{$ontology_type}{name}{"Gary Schindelman"} = "Gary Schindelman ( WBPerson557 ) ";
    $data{$ontology_type}{name}{"Kimberly Van Auken"} = "Kimberly Van Auken ( WBPerson1843 ) ";
    $data{$ontology_type}{name}{"Xiaodong Wang"} = "Xiaodong Wang ( WBPerson1760 ) ";
    $data{$ontology_type}{name}{"Karen Yook"} = "Karen Yook ( WBPerson712 ) ";
    $data{$ontology_type}{name}{"Carol Bastiani"} = "Carol Bastiani ( WBPerson48 ) ";
    $data{$ontology_type}{name}{"Keith Bradnam"} = "Keith Bradnam ( WBPerson1971 ) ";
    $data{$ontology_type}{name}{"Chao-Kung Chen"} = "Chao-Kung Chen ( WBPerson1845 ) ";
    $data{$ontology_type}{name}{"Josh Jaffery"} = "Josh Jaffery ( WBPerson5196 ) ";
    $data{$ontology_type}{name}{"Sylvia Martinelli"} = "Sylvia Martinelli ( WBPerson1250 ) ";
    $data{$ontology_type}{name}{"Tuco"} = "Tuco ( WBPerson480 ) ";
    $data{$ontology_type}{name}{"Mary Ann Tuli"} = "Mary Ann Tuli ( WBPerson2970 ) "; }
  elsif ($ontology_type eq 'animal') {
    $data{$ontology_type}{name}{"Rabbit"} = "Rabbit";
    $data{$ontology_type}{name}{"Mouse"} = "Mouse";
    $data{$ontology_type}{name}{"Rat"} = "Rat";
    $data{$ontology_type}{name}{"Guinea_pig"} = "Guinea_pig";
    $data{$ontology_type}{name}{"Chicken"} = "Chicken";
    $data{$ontology_type}{name}{"Goat"} = "Goat";
    $data{$ontology_type}{name}{"Other_animal"} = "Other_animal"; }
  return \%data;
} # sub setAnySimpleAutocompleteValues


sub getAnySpecificAutocomplete {
  my ($ontology_type, $words) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {     ($matches) = &getAnyWBPersonAutocomplete($words); }
  return $matches;
} # sub getAnySpecificAutocomplete

sub getAnyWBPersonAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( two_standardname );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );	# match by start of name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      $matches{"$row[2] ( $id ) "}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' ORDER BY $table;" );		# then match anywhere in the name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      $matches{"$row[2] ( $id ) "}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$words' ORDER BY joinkey;" );		# then match by WBPerson number
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      $matches{"$row[2] ( $id ) "}++; }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBPersonAutocomplete

### END AUTOCOMPLETE ###


### VALID VALUE ###

sub getAnySpecificValidValue {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonValidValue($userValue); }
  return $matches;
} # sub getAnySpecificValidValue

sub getAnyWBPersonValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( WBPerson(.*?) \) $/; $joinkey = 'two' . $joinkey; }
  my $table =  'two_standardname';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value' AND joinkey = '$joinkey';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBPersonValidValue

### END VALID VALUE ###


### TERM INFO ### 

sub getAnySpecificTermInfo {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonTermInfo($userValue); }
  return $matches;
} # sub getAnySpecificTermInfo

sub getAnyWBPersonTermInfo {
  my ($userValue) = @_;
  my $standard_name = $userValue; my $person_id; my $to_print;
  if ($userValue =~ m/(.*?) \( (.*?) \)/) { $standard_name = $1; $person_id = $2; } else { $person_id = $userValue; }
  $person_id =~ s/WBPerson/two/g;
  my $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$person_id' ORDER BY two_timestamp DESC;" );
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
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) { 	# all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBPersonTermInfo

### END TERM INFO ### 


### ID TO VALUE ###

sub getAnySpecificIdToValue {			# convert values from postgres values (ids) to what someone types for dataTable display
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'WBPerson') {        ($matches, $fieldIdToValue_ref) = &getAnyWBPersonIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  return ($matches, $fieldIdToValue_ref);
} # sub getAnySpecificIdToValue

sub getAnyWBPersonIdToValue {			# names of people by wbperson id
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $id (@data) {
    my $joinkey = $id; $joinkey =~ s/WBPerson/two/g;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $table =  'two_standardname';
      my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$joinkey' ORDER BY two_order;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[2]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[2]<span style='display: none'>$id</span>\""; 
                     $results{$joinkey} = "\"$row[2]<span style='display: none'>$id</span>\""; } } }
  my $data = join",", sort values %results;
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyWBPersonIdToValue

### END ID TO VALUE ###

### END ONTOLOGY / MULTIONTOLOGY ###


### LOGIN ###

sub loginMod {
  my ($flag, $ip, $curator_two) = @_;			# get the flag, $ip, and optional $curator_two
  &loginTest($flag, $ip, $curator_two); }

sub loginTest {						# switch for different login subroutines
  my ($flag, $ip, $curator_two) = @_;			# get the flag, $ip, and optional $curator_two
  if ($flag eq 'showModLogin') { &showTestLogin($ip); }
  elsif ($flag eq 'updateModCurator') { &updateTestCurator($ip, $curator_two); }
} # sub loginTest

sub showTestLogin {					# show login curators, datatypes, and Login button
  my ($ip) = @_;
  my $curator_by_ip = '';
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[0]) { $curator_by_ip = $row[0]; }
  my %curator_list; tie %curator_list, "Tie::IxHash";
  $curator_list{"two1823"} = 'Juancarlos Chan';
  $curator_list{"two625"} = 'Paul Sternberg';

  print "<table cellpadding=\"4\">\n";
  print "<tr>\n";
  print "<td valign=\"top\">Name<br /><select name=\"curator_two\" size=" , scalar keys %curator_list , ">\n";
  foreach my $curator_two (keys %curator_list) {	# display curators in alphabetical (tied hash) order, if IP matches existing ip record, select it
    if ($curator_by_ip eq $curator_two) { print "<option value=\"$curator_two\" selected=\"selected\">$curator_list{$curator_two}</option>\n"; }
    else { print "<option value=\"$curator_two\">$curator_list{$curator_two}</option>\n"; } }
  print "</select></td>\n";
  print "<td valign=\"top\">Data Type<br /><select name=\"datatype\" size=\"10\">\n";
  print "<option value=\"tst\">test configuration</option>\n";
  print "</select></td>\n";
  print "<td valign=\"top\"><br /><input type=submit name=action value=\"Login !\"></td>\n";
  print "</tr>\n";
  print "</table>\n";
} # sub showTestLogin

sub updateTestCurator {					# update two_curator_ip for this curator and ip
  my ($ip, $curator_two) = @_;
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip' AND joinkey = '$curator_two';" );
  $result->execute;
  my @row = $result->fetchrow;
  unless ($row[0]) {
    $result = $dbh->do( "DELETE FROM two_curator_ip WHERE two_curator_ip = '$ip' ;" );
    $result = $dbh->do( "INSERT INTO two_curator_ip VALUES ('$curator_two', '$ip')" );
} } # sub updateTestCurator

### END LOGIN ###



__END__


=head1 NAME

testOA - Config file for test OA configurations for test  MOD.


=head1 SYNOPSIS

In ontology_annotator.cgi :

=over 4

=item * add "use testOA;"

=item * add "my $configLoaded = 'testOA';"

=back

In this oa perl module file :

=over 4

=item * if creating a copy of this perl module change the name in the first line 'package testOA;'.

=item * customize  &initTestFields  &showTestLogin  &setAnySimpleAutocompleteValues  &getAnySpecificAutocomplete  &getAnySpecificValidValue  &getAnySpecificTermInfo  &getAnySpecificIdToValue 

=back


=head1 DESCRIPTION

ontology_annotator.cgi has the generic code for any kind of configuration.  Some subroutines need data that is specific to a given datatype / configuration, and modules like this one can be custom-written to appropriately get and display this data.  There are seven groups of subroutines that need to be written :

=over 4

=item * &login<Mod>  switch to call appropriate login-related subroutine

=item * &init<Mod>Fields  initializes the appropriate %fields and %datatypes for the MOD's chosen datatype and curator.

=item * setAnySimpleAutocompleteValues  set values of dropdown or multidropdown for a given ontology_type.

=item * getAnySpecificAutocomplete  for something that a curator types into an ontology or multiontology field, get autocomplete values that correspond to it.

=item * getAnySpecificValidValue  for a value that a curator selects in an ontology or multiontology field, check if it's valid and return 'true' or 'false'.

=item * getAnySpecificTermInfo  for a value that a curator looks at in an ontology or multiontology field, get the corresponding term information for the OA's obo frame.

=item * getAnySpecificIdToValue  for some stored IDs in an ontology or multiontology field's corresponding postgres table, get the corresponding objects's names (and IDs) to display on the dataTable, as well as update %fieldIdToValue .

=back

When creating a new MOD, must create  &login<Mod>  and optional curator_ip table.

When creating a new datatype, must create  &init<Mod>Fields  and corresponding postgres tables.

When creating a new dropdown / multidropdown, must set values in  &setAnySimpleAutocompleteValues .

When creating a new ontology / multiontology, must set  &getAnySpecificAutocomplete  &getAnySpecificValidValue  &getAnySpecificTermInfo  &getAnySpecificIdToValue  and create appropriate corresponding subroutine for each.

NOTE : If using this as a template for a new MOD OA configuration, you will not have pap_ postgres tables, so the  &getAnySpecific...  subroutines will not work because the tables will not exist.  Look at the wormOA.pm for more examples.

=head2 LOGIN TEST

&loginTest  is the main subroutine called from the ontology_annotator.cgi and calls the appropriate login-related subroutine.  The worm config stores the last IP used by any given curator, this is not necessary for other MODs.

&loginMod  is called by ontology_annotator.cgi  passing in a flag for which subroutine to call, an IP address, and optional curator_two.  It is a generalized function to call  &loginTest  with the same parameters.

&loginTest  is called by  &loginMod  passing in a flag for which subroutine to call, an IP address, and optional curator_two.  It calls  &showTestLogin  or  &updateTestCurator .

&showTestLogin  is called from ontology_annotator.cgi's  &showLogin  passing in the IP of the user.  Displays a selection of curators and datatypes for that MOD, and a Login button 'Login !'.  A postgres table of curator IPs finds the last curator to use that IP and automatically select it ;  this is optional and only necessary is tracking curators by IP.

&updateTestCurator  is called from ontology_annotator.cgi's  &showMain  passing in the IP of the user and the curator_two to update.  Update the postgres table two_curator_ip for this curator_two and IP.  Optional subroutine, unnecessary if not tracking curators by IP.

=head2 INITIALIZE TEST FIELDS

&initTestFields  is the main subroutine called from the ontology_annotator.cgi and calls the appropriate datatype-appropriate initialization subroutine to set field and datatype values.

&initModFields  is called by ontology_annotator.cgi  passing in $datatype and $curator_two and returning values of $fieldsRef and $datatypesRef .  It is a generalized function to call  &initTestFields  with the same parameters.

&initTestFields  is called by  &initModFields  passing in $datatype and $curator_two and returning values of $fieldsRef and $datatypesRef .  A new datatype configuration calls  &initTest<datatype>Fields  passing $datatype and $curator_two and returning values of $fieldsRef and $datatypesRef .

&initTest<datatype>Fields  exist for each specific datatype configuration.  It defines the %fields and %datatypes and returns them to the ontology_annotator.cgi .

%datatypes  stores options for each datatype configuration as a whole, in the format  $datatypes{<datatype>}{<option>} .  It can have these options :

=over 4

=item * highestPgidTables	REQUIRED	array of tables for this config that should have a value to determine the highest used pgid.  Also when doing a &jsonFieldQuery if querying by id use these tables instead.

=item * newRowSub	REQUIRED	pointer to the config-specific sub to create a new row.  Most only insert to postgres table of _curator field, others also to other tables.

=item * constraintSub	OPTIONAL	pointer to the config-specific sub for checks when checking data.  Called by ontology_annotator.cgi by  &checkDataByPgids .  Returns 'OK' or messages with specific problems for specific pgids.

=item * constraintTablesHaveData	OPTIONAL	array of tables for this config.  When checking data, these tables must have data.  Called by ontology_annotator.cgi by  &checkDataByPgids .

=back

%fields  stores options for the datatype configuration's individual fields, in the format  $fields{<datatype>}{<field_name>}{<option>} .  It must have a field called 'id' used to store the dataTable's pgid / postgresTables's joinkey.  It must also have a field called 'curator' (or equivalent, such as 'curator_evidence').  It can have these options :

=over 4

=item * type	REQUIRED	the type of field.  Possible values are : text bigtext dropdown multidropdown ontology multiontology toggle toggle_text queryonly

=item * label	REQUIRED	text that shows on the OA editor and dataTable columns.  Editor td has id label_$field.  Should never have the same label for different fields because .js columnReorderEvent uses label value to set order.

=item * tab	REQUIRED	which editor's tab displays the field.  Value can be 'all' or 'tab1', 'tab2', &c.

=item * dropdown_type	DEPENDENT	required for fields of type dropdown or multidropdown.  To specify which values to show for a given dropdown / multidropdown field.  Used by ontology_annotator.cgi for  &getAnySimpleValidValue  &setAnySimpleAutocomplete  &getAnySimpleAutocomplete   IdToValue conversion.

=item * ontology_type	DEPENDENT	required for fields of type ontology or multiontology.  For ontology subroutines to know what type of data to use for an ontology / multiontology.  Can be generic (value 'obo') and use 'obo_' tables, or can be specific and have custom subroutines (e.g. WBGene, WBPerson, WBPaper, Transgene, &c.).  A given ontology_type can be used in different datatypes and/or multiple times in the same datatype.

=item * ontology_table	DEPENDENT	required for fields of type ontology or multiontology that also have ontology_type value 'obo', this determines the specific obo_ table to get values from.

=item * inline	DEPENDENT	required for fields that have multiple fields in the same row.  Can hold the value of the corresponding field that follows, or begin with 'INSIDE_'.  When doing &showEditor, values with 'INSIDE_' get skipped ;  values that are 'toggle_text' show the toggle field and then the corresponding text field.

=item * queryonlySub  DEPENDENT		required for fields of type queryonly.  Pointer to the datatype-field-specific sub to create a custom postgres query for queryonly fields that returns joinkeys.

=item * noteditable	OPTIONAL	flag.  Field can't be edited (affects ontology_annotator.js only).  Values in bigtext field will toggle into the input field, so the editor will change, but values will not update in the datatable, nor change in postgres.

=item * input_size	OPTIONAL	integer.  Html input tag has this size on editor.

=item * placeholder	OPTIONAL	fake field to set the order in the tied hash.  Fields on editor show in order they were entered in the tied %fields hash, this only serves to set the order.

=item * columnWidth	OPTIONAL	integer.  Value to hard-set the width in pixels of the value's dataTable column.

=item * columnOrder	OPTIONAL	integer.  Value to hard-set the array order of the columns in the dataTable.  Never set multiple fields to the same columnOrder or one will not show.

=back

=head2 SET ANY SIMPLE AUTOCOMPLETE VALUES

&setAnySimpleAutocompleteValues  is the only subroutine called from the ontology_annotator.cgi and sets the dropdown values for the appropriate datatype.  Necessary when creating a new dropdown or multidropdown ontology type.

&setAnySimpleAutocompleteValues  is called by ontology_annotator.cgi  passing in the ontology_type and returning a pointer to %data.  Creates a tied %data hash which has all dropdown values in order entered for the given ontology_type.

%data  stores dropdown values for a given ontology_type, in the format  ''$data{<ontology_type>}{name}{<name>} = <value_to_display>''.  value_to_display  can have two formats : ''<name_of_value> ( <id_of_value> ) '' or ''<value>'' depending on whether the ontology_type stores IDs or not, respectively.

=head2 GET ANY SPECIFIC AUTOCOMPLETE

&getAnySpecificAutocomplete  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to get the matching Autocomplete values for that ontology_type.  Used when a curator types full or partial terms into an ontology / multiontology field.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificAutocomplete  is called by ontology_annotator.cgi  passing in the ontology_type and words to autocomplete on, and returning the corresponding matches.  Calls  &getAny<ontology_type>Autocomplete  passing in words to autocomplete on, and returning the corresponding matches.

&getAny<ontology_type>Autocomplete  exists for each specific ontology_type.  It queries the appropriate postgres tables to find corresponding values.  Most of these subroutines return 20 ontology values, but if there are 5 or more characters to search the results expands to 500.  Most also search for a case-insensitive match beginning with the search terms, then if there aren't yet max_results it appends results from a case-insensitive match of the search terms where the terms do not match at the beginning.  If there are more than max_results values, the last results is replaced with 'more ...'.  Results are joined by a newline and returned.  Most tables searched are the appropriate name table for the ontology_type, but it could also be an ID field or synonym field or anything else.  The format of each autocomplete value can be  ''<value>'' if it can only match on a value, or ''<name_of_value> ( <id_of_value> ) '' if it can match on a name or an ID, or ''<name_of_match> ( <id_of_value> ) [name_of_id]'' if it can match on a synonym, ID, or name of term.

=head2 GET ANY SPECIFIC VALID VALUE

&getAnySpecificValidValue  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to check that a value is valid for that ontology_type.  Used when a curator selects a value in an ontology or multiontology field.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificValidValue  is called by ontology_annotator.cgi  passing in the ontology_type and userValue to check validity on, and returning 'true' or 'false' as appropriate.  Calls  &getAny<ontology_type>ValidValue  passing in the userValue and returning 'true' or 'false'.

&getAny<ontology_type>ValidValue  exists for each specific ontology_type.  It queries the appropriate postgres tables to check if the userValue is a valid value for the ontology_type.  If it is valid, returns 'true', otherwise returns 'false'.

=head2 GET ANY SPECIFIC TERM INFO

&getAnySpecificTermInfo  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to get the term information for the given ontology value, to display in the OA's obo frame.  Used when a curator clicks, mouses over, or arrows to a value from an ontology / multiontology field.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificTermInfo  is called by ontology_annotator.cgi  passing in the ontology_type and userValue to get term info of, and returning a variable containing the term information to display in the OA's obo frame.  Calls  &getAny<ontology_type>TermInfo  passing in the userValue, and returning the term information to display.

&getAny<ontology_type>TermInfo  exists for each specific ontology_type.  It queries the appropriate postgres tables (or flatfiles) to get the term information to display.  Most information has a tag name and colon in a bold html span, followed by the information.  As appropriate there might be html hr dividers.  Any type of html links or embedded images or practically any html could be displayed here.

=head2 GET ANY SPECIFIC ID TO VALUE

&getAnySpecificIdToValue  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to add to the %fieldIdToValue hash, which converts ID into  ''name<span style='display: none'>id</span>''.  Used when displaying dataTable data from a postgres query of &jsonFieldQuery in the main CGI.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificIdToValue  is called by ontology_annotator.cgi  passing in the ontology_type, %fields's type, pointer to existing %fieldIdToValue, and IDs from postgres table data from which to get the id to value mappings ;  and returning a variable containing the display values of each of the ontology_type's passed IDs, and a pointer to the updated %fieldIdToValue .  Calls &getAny<ontology_type>IdToValue, passing in the ontology_type, %fields's type, pointer to %fieldIdToValue hash, IDs from postgres table data ;  and returning a variable with the display values of the corresponding IDs, and a pointer to the updated %fieldIdToValue .

&getAny<ontology_type>IdToValue  exists for each specific ontology_type.  It splits the postgres data table's values into separate IDs, and for each ID, it checks against the %fieldIdToValue hash.  If it already exists, it adds it to the %results hash.  If it doesn't, it queries against the appropriate postgres tables and generates a new value to display, adding it to %results and to $fieldIdToValue{$ontology_type}.  %results values are joined by commas into a $data variable to return.  If the %fields's type is ontology, the leading and trailing doublequotes are stripped (doublequotes are necessary for multiontology).  $data and a pointer to the updated %fieldIdToValue are returned.  The format of %results is  ''$results{<joinkey>} = "<display_value><span style='display: none'><id></span>"''  where <span> tags are html tags, and <display_value> and <id> are real values.




