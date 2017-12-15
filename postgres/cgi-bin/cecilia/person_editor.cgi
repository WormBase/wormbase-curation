#!/usr/bin/perl -w

# edit two tables's person data

# added two712, Karen Yook  2011 09 26
#
# added two12028, Daniela Raciti  2011 10 12
#
# changed &showInstitutionEditor to have a javascript link to only show institutions that have data in the institution field.
# changed the paper_editor.js to have that function.  2012 02 03
#
# lab to oldlab  is different from  email to old_email  and intitution to old_institution  so the javascript is not generalized and has field-specific code, which is terrible.  (also old_inst had old_inst_date while old_email has old_email_date, so even more non-generalized).  email / institution / lab now all have a move button instead of just the first two.  2012 06 20
#
# added  Person Statistics  &personStatistics()  to show people created, people invalid, people current, and totals by year-month.  for Paul and Raymond.  2013 02 01
#
# added GD::Graph to generate charts at :
#   /home/postgres/public_html/cgi-bin/cecilia/data/person_editor_valid.png
#   /home/postgres/public_html/cgi-bin/cecilia/data/person_editor_totalvalid.png
# changed  &personStatistics()  to properly (hopefully) get the amount of valid / invalid / any on any given month, and generate totals without just adding in case the person already existed (prevent being counted multiple times for changes in separate months, but will still show someone in valid set and in invalid set if they appear as both types).
# added average valid created per month.  2013 02 02
#
# changed to dynamically create the embedded graphs with a get call to the CGI with &generatePng();  this may fail when the URL gets bigger than a get call can handle.  to switch back don't forget to touch the png files and chmod 666 them.  2012 02 03 
#
# changed  &displayPaper  to show pap_affiliation for iwm abstracts.  2013 07 11
#
# added  two_orcid  and put in editors between oldlab and left_field.  2013 11 04
#
# added  affiliations  from xml to author display when showing a paper.  2014 07 28
#
# xml paths could be in different locations.  2014 09 17
#
# added  &addressByTwos() + &displayAddressByTwos()  to display address + institution data by pasting two#s.  2015 01 15
#
# %author_xml data hashes by firstname + initial, but some papers like 00046310 have multiple authors with the same 'name', so mapping the hash values to arrays and shifting different author matches from it.  2015 01 22
#
# added  lab webpage comment  to set of fields that can be created in person from a paper.  2015 07 09
#
# added  oldpis  as new field for old PIs for Cecilia.  2015 07 12
#
# added  Mary Ann  for Cecilia.  2017 04 04
 


use strict;
use CGI;
use Jex;		# &getPgDate; &getSimpleDate;
use DBI;
use Tie::IxHash;
use Math::SigFigs;                              # significant figures $new = FormatSigFigs($n, $d);
# use GD::Graph::lines;	# generate statistics graphs
use GD::Graph::area;	# generate statistics graphs


# Use all timestamps to use latest to create  Last_verified  date


# my $dbh = DBI->connect ( "dbi:Pg:dbname=devdb", "", "") or die "Cannot connect to database!\n"; 
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $query = new CGI;

my $frontpage = 1;
# my $blue = '#b8f8ff';			# redefine blue to a mom-friendly color
my $blue = '#e8f8ff';			# redefine blue to a mom-friendly color
my $grey = '#d0d0d0';			# redefine grey to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color

my $tdDot = qq(td align="center" style="border-style: dotted; border-color: #007FFF");
my $thDot = qq(th align="center" style="border-style: dotted; border-color: #007FFF");

my %curators;                           # $curators{two}{two#} = std_name ; $curators{std}{std_name} = two#

my @normal_tables = qw( status firstname middlename lastname standardname aka_firstname aka_middlename aka_lastname email old_email old_email_date street city state post country institution old_institution old_inst_date mainphone labphone officephone otherphone fax pis oldpis lab oldlab orcid left_field unable_to_contact privacy webpage usefulwebpage wormbase_comment hide mergedinto acqmerge comment );

my %type_input;				# all inputs are inputs, but usefulwebpage is a checkbox
foreach ("number", @normal_tables) { $type_input{$_} = 'input'; } 
$type_input{'usefulwebpage'} = 'checkbox';

my %lineageDropdowns;

my %order_type;
my @single_order = qw( firstname middlename lastname standardname city state post country left_field unable_to_contact hide status mergedinto );
my @multi_order = qw( street institution old_institution old_inst_date mainphone labphone officephone otherphone fax email old_email old_email_date pis oldpis lab oldlab orcid privacy aka_firstname aka_middlename aka_lastname webpage usefulwebpage wormbase_comment acqmerge comment );
foreach (@single_order) { $order_type{single}{$_}++; }
foreach (@multi_order) { $order_type{multi}{$_}++; }

my %min_rows;
foreach my $table (@normal_tables) { $min_rows{$table} = 1; }
$min_rows{'street'} = 4;

# 1-20 institutions show only top and show next when data in previous street1
# for each institution show
# inst<num>
# street 1-20 (show only top and show next when data in previous)
# city  state  post  county
# institution
# 
# show all authors and their possible association
# for each author, AID, aname
# if already has pap_author_possible data : show two# (and link each to the person editor's person editing page)
# elsif it has new matches to 1 or more two# : show possible matches (and link each to the person editor's person editing page)
# else no existing pap_author_possible data, and 0 matches to existing persons : xml-forename, xml-lastname, <blank>middlename-field, standard_name default forename+ +lastname, inst-dropdown, <blank>email-field, comment-field with WBPaper####, button to create person.  require: lastname, firstname, stdname, institution-field-in-inst#.  New people add to 'two_status' 'Valid', 'two' '<#>'.  Associate to pap_author_possible aid.  Get back two# and replace this whole thing with a <td> to look like the pap_author_possible data (show two# w/link).


# my %dropdowns;
# @{ $dropdowns{status} } = qw( Valid Invalid );

&display();


sub display {
  my $action; my $normal_header_flag = 1;

  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); }
  } else { $frontpage = 0; }

  if ($action eq 'autocompleteXHR') { &autocompleteXHR(); }
  elsif ($action eq 'updatePostgresTableField') { &updatePostgresTableField(); }
  elsif ($action eq 'updatePostgresLineageData') { &updatePostgresLineageData(); }
  elsif ($action eq 'Search') { &search(); }
  elsif ($action eq 'Create New Person') { &createNewPerson(); }
  elsif ($action eq 'Search Paper') { &searchPaper(); }
  elsif ($action eq 'Checkout Papers') { &checkoutPapers(); }
  elsif ($action eq 'Create people from XML') { &createPeopleFromXml(); }
  elsif ($action eq 'Person Statistics') { &personStatistics(); }
  elsif ($action eq 'Address by Twos') { &addressByTwos(); }
  elsif ($action eq 'Display Address by Twos') { &displayAddressByTwos(); }
  elsif ($action eq 'generatePng') { &generatePng(); }
} # sub display

sub autocompleteXHR {
  print "Content-type: text/plain\n\n";
  (my $var, my $words) = &getHtmlVar($query, 'query');
  ($var, my $order) = &getHtmlVar($query, 'order');
  ($var, my $field) = &getHtmlVar($query, 'field');
  my $table = 'two_' . $field; my $column = $table;
  if ($field eq 'number') { $table = 'two_standardname'; $column = 'joinkey'; }
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  ($words) = lc($words);                                        # search insensitively by lowercasing query and LOWER column values
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my $result = $dbh->prepare( "SELECT DISTINCT($column) FROM $table WHERE LOWER($column) ~ '^$words' ORDER BY $column;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[0]"}++; }
  $result = $dbh->prepare( "SELECT DISTINCT($column) FROM $table WHERE LOWER($column) ~ '$words' AND LOWER($column) !~ '^$words' ORDER BY $column;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[0]"}++; }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; print $matches;
} # sub autocompleteXHR

sub fromUrlToPostgres {
  my $value = shift;
  if ($value) {
    if ($value =~ m/%2B/) { $value =~ s/%2B/+/g; }                # convert URL plus to literal
    if ($value =~ m/%23/) { $value =~ s/%23/#/g; }                # convert URL pound to literal
    if ($value =~ m/\'/) { $value =~ s/\'/''/g; }                 # escape singlequotes
  }
  return $value;
} # sub fromUrlToPostgres

sub updatePostgresByTableJoinkeyNewvalue {
  my ($field, $joinkey, $order, $newValue, $curator_two) = @_;
# print "F $field J $joinkey O $order N $newValue E<br/>\n";
  my $uid = 'joinkey'; my $sorter = 'two_order';
  my @pgcommands;
# on update  delete from data table and insert ; delete from history table current-10 minutes and insert
  if ($order) { 
      my $command = "DELETE FROM two_$field WHERE $uid = '$joinkey' AND $sorter = '$order'";
      push @pgcommands, $command;
      $command = "DELETE FROM h_two_$field WHERE $uid = '$joinkey' AND $sorter = '$order' AND two_timestamp > now() - interval '10 minutes'";
      push @pgcommands, $command;
      $order = "'$order'"; } 
    else { 
      my $command = "DELETE FROM two_$field WHERE $uid = '$joinkey' AND $sorter IS NULL";
      push @pgcommands, $command;
      $command = "DELETE FROM h_two_$field WHERE $uid = '$joinkey' AND $sorter IS NULL AND two_timestamp > now() - interval '10 minutes'";
      push @pgcommands, $command;
      $order = 'NULL'; }

  if ($newValue) { $newValue = "'$newValue'"; }
    else { $newValue = 'NULL'; }

  my $command = "INSERT INTO h_two_$field VALUES ('$joinkey', $order, $newValue, '$curator_two')";
  push @pgcommands, $command;
  if ($newValue ne 'NULL') {
    $command = "INSERT INTO two_$field VALUES ('$joinkey', $order, $newValue, '$curator_two')";
    push @pgcommands, $command; }

  foreach my $command (@pgcommands) {
#     print "$command<br />\n";
    $result = $dbh->do( $command );
  }
  return "OK";
} # sub updatePostgresByTableJoinkeyNewvalue

sub updatePostgresTableField {                          # if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/html\n\n";
  (my $var, my $field) = &getHtmlVar($query, 'field');
  ($var, my $joinkey) = &getHtmlVar($query, 'joinkey');
  ($var, my $order) = &getHtmlVar($query, 'order');
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  ($var, my $newValue) = &getHtmlVar($query, 'newValue');
  ($newValue) = &fromUrlToPostgres($newValue);

  my $isOk = 'NO';

  ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $joinkey, $order, $newValue, $curator_two);

  if ($isOk eq 'OK') { print "OK"; }
} # sub updatePostgresTableField

sub updatePostgresLineageData {                          # if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/html\n\n";
  (my $var, my $column)   = &getHtmlVar($query, 'column');
  ($var, my $joinkey)     = &getHtmlVar($query, 'joinkey');
  ($var, my $curator_two) = &getHtmlVar($query, 'curator_two');
  ($var, my $newValue)    = &getHtmlVar($query, 'newValue');  ($newValue)  = &fromUrlToPostgres($newValue);
  ($var, my $sentname)    = &getHtmlVar($query, 'sentname');  ($sentname)  = &fromUrlToPostgres($sentname);
  ($var, my $othername)   = &getHtmlVar($query, 'othername'); ($othername) = &fromUrlToPostgres($othername);
  ($var, my $othertwo)    = &getHtmlVar($query, 'othertwo');  ($othertwo)  = &fromUrlToPostgres($othertwo);
  ($var, my $role)        = &getHtmlVar($query, 'role');      ($role)      = &fromUrlToPostgres($role);
  ($var, my $date1)       = &getHtmlVar($query, 'date1');     ($date1)     = &fromUrlToPostgres($date1);
  ($var, my $date2)       = &getHtmlVar($query, 'date2');     ($date2)     = &fromUrlToPostgres($date2);
  ($var, my $sender)      = &getHtmlVar($query, 'sender');    ($sender)    = &fromUrlToPostgres($sender);

  my @pgcommands;
  my $reverse_role = $role; my $reverse_sender = $sender;		# get reverse
  my ($sentname_qual, $othername_qual, $othertwo_qual, $date1_qual, $date2_qual, $role_qual, $reverse_role_qual, $sender_qual, $reverse_sender_qual) = ('','','','','','','','','');
  $joinkey = "'$joinkey'";			# there is always a joinkey
  my $has_some_value = 0;			# only do INSERT if there is something to insert
  if ($sentname) { $sentname_qual = " = '$sentname'"; $sentname = "'$sentname'"; $has_some_value++; }
    else { $sentname_qual = " IS NULL"; $sentname = 'NULL'; }
  if ($othername) { $othername_qual = " = '$othername'"; $othername = "'$othername'"; $has_some_value++; }
    else { $othername_qual = " IS NULL"; $othername = 'NULL'; }
  if ($othertwo) { $othertwo_qual = " = '$othertwo'"; $othertwo = "'$othertwo'"; $has_some_value++; }
    else { $othertwo_qual = " IS NULL"; $othertwo = 'NULL'; }
  if ($date1) { $date1_qual = " = '$date1'"; $date1 = "'$date1'"; $has_some_value++; } 
    else { $date1_qual = " IS NULL"; $date1 = 'NULL'; }
  if ($date2) { $date2_qual = " = '$date2'"; $date2 = "'$date2'"; $has_some_value++; } 
    else { $date2_qual = " IS NULL"; $date2 = 'NULL'; }
  if ($role) { $has_some_value++;  
      if ($reverse_role eq 'Collaborated') { }
        elsif ($reverse_role =~ m/^with/ ) { $reverse_role =~ s/with//g; }
        else { $reverse_role = "with$reverse_role"; }
      $role_qual = " = '$role'"; $role = "'$role'";
      $reverse_role_qual = " = '$reverse_role'"; $reverse_role = "'$reverse_role'"; }
    else { 
      $role_qual = " IS NULL"; $reverse_role_qual = " IS NULL"; 
      $role = 'NULL'; $reverse_role = 'NULL'; }
  if ($sender) { $has_some_value++;  
      if ($reverse_sender =~ m/^REV \- / ) { $reverse_sender =~ s/^REV \- //g; }
        else { $reverse_sender = "REV - $reverse_sender"; }
      $sender_qual = " = '$sender'"; $reverse_sender_qual = " = '$reverse_sender'"; 
      $sender = "'$sender'"; $reverse_sender = "'$reverse_sender'"; }
    else { 
      $sender_qual = " IS NULL"; $reverse_sender_qual = " IS NULL"; 
      $sender = 'NULL'; $reverse_sender = 'NULL'; }
  if ($has_some_value) {				# only delete if there is something to delete
    push @pgcommands, "DELETE FROM two_lineage WHERE joinkey = $joinkey AND two_sentname $sentname_qual AND two_othername $othername_qual AND two_number $othertwo_qual AND two_date1 $date1_qual AND two_date2 $date2_qual AND two_role $role_qual AND two_sender $sender_qual";
    push @pgcommands, "DELETE FROM two_lineage WHERE joinkey $othertwo_qual AND two_sentname $othername_qual AND two_othername $sentname_qual AND two_number = $joinkey AND two_date1 $date1_qual AND two_date2 $date2_qual AND two_role $reverse_role_qual AND two_sender $reverse_sender_qual"; }
  if    ($column eq 'sentname')  { if ($newValue) { $sentname = "'$newValue'"; } else { $sentname = 'NULL'; } }
  elsif ($column eq 'othername') { if ($newValue) { $othername = "'$newValue'"; } else { $othername = 'NULL'; } }
  elsif ($column eq 'othertwo')  { if ($newValue) { $othertwo = "'$newValue'"; } else { $othertwo = 'NULL'; } }
  elsif ($column eq 'date1')     { if ($newValue) { $date1 = "'$newValue'"; } else { $date1 = 'NULL'; } }
  elsif ($column eq 'date2')     { if ($newValue) { $date2 = "'$newValue'"; } else { $date2 = 'NULL'; } }
  elsif ($column eq 'role')      { 
    if ($newValue) { 
        $reverse_role = $newValue;
        if ($reverse_role eq 'Collaborated') { }
          elsif ($reverse_role =~ m/^with/ ) { $reverse_role =~ s/with//g; }
          else { $reverse_role = "with$reverse_role"; }
        $reverse_role = "'$reverse_role'"; $role = "'$newValue'"; }
      else { $role = 'NULL'; $reverse_role = 'NULL'; } }
  elsif ($column eq 'sender')    {
    if ($newValue) {
        $reverse_sender = $newValue;
        if ($reverse_sender =~ m/^REV \- / ) { $reverse_sender =~ s/^REV \- //g; }
          else { $reverse_sender = "REV - $reverse_sender"; }
        $reverse_sender = "'$reverse_sender'"; $sender = "'$newValue'"; }
      else { $sender = 'NULL'; $reverse_sender = 'NULL'; } }
  if ( ($sentname ne 'NULL') || ($othername ne 'NULL') || ($othertwo ne 'NULL') || ($role ne 'NULL') || ($date1 ne 'NULL') || ($date2 ne 'NULL') || ($sender ne 'NULL') ) {		# if any non-joinkey column is not null insert entries
    push @pgcommands, "INSERT INTO two_lineage VALUES ( $joinkey, $sentname, $othername, $othertwo, $role, $date1, $date2, $sender )";
    push @pgcommands, "INSERT INTO two_lineage VALUES ( $othertwo, $othername, $sentname, $joinkey, $reverse_role, $date1, $date2, $reverse_sender )"; }

  foreach my $command (@pgcommands) {
#     print "$command<br />\n";
    $result = $dbh->do( $command );
  }
  print "OK";
} # sub updatePostgresLineageData


sub getHighestJoinkey {
  $result = $dbh->prepare( "SELECT two FROM two ORDER BY two::INTEGER DESC" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); my ($two_number) = $row[0]; return $two_number;
} # sub getHighestJoinkey

sub createNewPerson {
  &printHtmlHeader();
  my ($curator_two) = &getCuratorFromForm();
  my ($two_number) = &getHighestJoinkey();
  $two_number++;
  my $joinkey = 'two' . $two_number;
  print "Will create $joinkey (IF THESE ARE THE RIGHT COMMANDS, TELL JUANCARLOS TO MAKE IT LIVE, IT'S NOT DOING ANYTHING NOW)<br />\n";
  my $url = "person_editor.cgi?curator_two=$curator_two&action=Search&display_or_edit=edit&input_number_1=$joinkey";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"createNewPerson\">";
  print "<input type=\"hidden\" name=\"redirect_to\" id=\"redirect_to\" value=\"$url\">";
  my @pgcommands;
  (@pgcommands) = &addToPgcommandsTwoCreation($two_number, $curator_two, @pgcommands);
  foreach my $command (@pgcommands) {
    print "$command<br />\n";
    $result = $dbh->do( $command );
  } # foreach my $command (@pgcommands)
} # sub createNewPerson


### Search Section ###
 
sub search {
  &printHtmlHeader();
  my ($curator_two) = &getCuratorFromForm();
  (my $var, my $number) = &getHtmlVar($query, "input_number_1");
  if ($number) {
    if ($number =~ m/(\d+)/) { &displayPerson("two$1", $curator_two); return; }
      else { print "Not a number in a number search for $number<br />\n"; } }

  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"searchResults\">";

  my %hash;
  my $order = 1;
  foreach my $table (@normal_tables) {
    ($var, my $data) = &getHtmlVar($query, "input_${table}_${order}");
    next unless ($data);	# skip those with search params
    my $substring = ''; my $case = ''; my $operator = '=';
    ($var, $substring) = &getHtmlVar($query, "substring_$table");
    ($var, $case) = &getHtmlVar($query, "case_$table");
    if ($case eq 'on') { $operator = '~*'; }
    elsif ($substring eq 'on') { $operator = '~'; }
#     print "SELECT joinkey, two_$table FROM two_$table WHERE two_$table $operator '$data'<br />\n";
    $result = $dbh->prepare( "SELECT joinkey, two_$table FROM two_$table WHERE two_$table $operator '$data'" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      $hash{matches}{$row[0]}{$table}++; 
      push @{ $hash{table}{$table}{$row[0]} }, $row[1]; }
  } # foreach my $table (@normal_tables)
  my %matches; 
  my $joinkeys = join"','", keys %{ $hash{matches} }; my %std_name; my %status;
  $result = $dbh->prepare( "SELECT joinkey, two_standardname FROM two_standardname WHERE joinkey IN ('$joinkeys')" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $std_name{$row[0]} = $row[1]; }
  $result = $dbh->prepare( "SELECT joinkey, two_status FROM two_status WHERE joinkey IN ('$joinkeys')" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[1] eq 'Invalid') { $status{$row[0]} = $row[1]; } else { $status{$row[0]} = ''; } }
  foreach my $joinkey (keys %{ $hash{matches} }) {
    my $count = scalar keys %{ $hash{matches}{$joinkey} }; $matches{$count}{$joinkey}++; }
  foreach my $count (reverse sort {$a<=>$b} keys %matches) {
    print "<br />Matches $count<br />\n";
    foreach my $joinkey (sort {$a<=>$b} keys %{ $matches{$count} }) {
      print "<font color=\"red\">$status{$joinkey}</font> ";	# add invalid flag to person search 2012 07 31
      print "<a href=\"person_editor.cgi?curator_two=$curator_two&action=Search&display_or_edit=display&input_number_1=$joinkey\">$joinkey</a>\n";
      print "<font color=\"brown\">$std_name{$joinkey}</font> ";
      foreach my $table (keys %{ $hash{table} }) {
        next unless $hash{table}{$table}{$joinkey};
        my $data_match = join", ", @{ $hash{table}{$table}{$joinkey} }; 
        print "$table : <font color=\"green\">$data_match</font>\n"; }
      print "<br />\n";
    } # foreach my $joinkey (sort {$a<=>$b} keys %{ $matches{$count} })
  } # foreach my $count (reverse sort {$a<=>$b} keys %matches)
  &printFooter();
} # sub search

### End Search Section ###


### Person Editing Section ###

sub displayPerson {
  my ($joinkey, $curator_two) = @_;
  (my $var, my $display_or_edit) = &getHtmlVar($query, "display_or_edit");
  print "<input type=\"hidden\" name=\"person_joinkey\" id=\"person_joinkey\" value=\"$joinkey\">";

  my %display_data;
  my $header_bgcolor = '#dddddd'; my $header_color = 'black';

  print "<table style=\"border-style: none;\" border=\"0\" >\n";
  my $entry_data = "<tr bgcolor='$header_bgcolor'><td>$joinkey</td><td colspan=6><div style=\"color:$header_color\">Person Information</div></td></tr>\n";

  my %pgdata;
  foreach my $table (@normal_tables) {
    $entry_data .= "<input type=\"hidden\" class=\"fields\" value=\"$table\" \/>\n";
    my $pg_table = 'two_' . $table; 
    $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY two_order" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      next unless ($row[2]);				# skip blank entries
      $pgdata{$table}{$row[1]}{highest_order} = $row[1];
      $pgdata{$table}{$row[1]}{data} = $row[2];
      $pgdata{$table}{$row[1]}{row_curator} = $row[3];
      $pgdata{$table}{$row[1]}{timestamp} = $row[4]; }
  } # foreach my $table (@normal_tables)

#   if ($display_or_edit eq 'display') { ($entry_data) = &displayPersonDisplay($joinkey, $curator_two, $entry_data, \%pgdata); }
#     else { ($entry_data) = &displayPersonEditor($joinkey, $curator_two, $entry_data, \%pgdata); }

  my $is_valid = '';			# if person status is Invalid make red to show on toggle href switch  2012 07 30
  if ($pgdata{'status'}{1}{data}) { if ($pgdata{'status'}{1}{data} eq 'Invalid') { $is_valid = qq(<b style="color: red;font-size: 14pt">Invalid : </b>\n); } }

  my $which_page = 'displayPersonEditor'; my $opp_display_or_edit = 'display';
  if ($display_or_edit eq 'display') { $which_page = 'displayPersonDisplay'; $opp_display_or_edit = 'edit'; }
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"$which_page\">";
  my $toggle_url = "person_editor.cgi?curator_two=$curator_two&action=Search&display_or_edit=$opp_display_or_edit&input_number_1=$joinkey";	# add link to person_editor in display mode
  $entry_data .= "$is_valid Switch to <a href=\"$toggle_url\">$opp_display_or_edit</a>.<br />\n";

  foreach my $table (@normal_tables) {
    next if ( ($table eq 'middlename') || ($table eq 'lastname') || ($table eq 'aka_middlename') || ($table eq 'aka_lastname') || 
              ($table eq 'old_inst_date') || ($table eq 'old_email_date') || ($table eq 'usefulwebpage') );
    my $highest_order = 0;
#     if ($table eq 'status') { $entry_data .= "<tr bgcolor='$header_bgcolor'><td colspan=7><div style=\"color:$header_color\">Publication Information</div></td></tr>\n"; }

    foreach my $order (sort {$a<=>$b} keys %{ $pgdata{$table} }) {
      if ($table eq 'firstname') {
        $entry_data .= &makeTripletHorizontal(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'middlename', 'lastname', 'name'); }
      elsif ($table eq 'aka_firstname') {
        $entry_data .= &makeTripletHorizontal(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'aka_middlename', 'aka_lastname', 'aka_name'); }
      elsif ($table eq 'old_email') {
#         $entry_data .= &makeDoubleTimeHorizontal(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'old_email_date', 'old_email');
        $entry_data .= &makeDoubleVertical(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'old_email_date', 'old_email'); }
      elsif ($table eq 'old_institution') {
        $entry_data .= &makeDoubleVertical(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'old_inst_date', 'old_institution'); }
      elsif ($table eq 'webpage') {
        $entry_data .= &makeCheckboxInput(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'usefulwebpage', 'webpage'); }
      else {
        $entry_data .= &makeSingleNormal(\%pgdata, $display_or_edit, $joinkey, $order, $table); }
      if ($order > $highest_order) { $highest_order = $order; }
    } # foreach my $order (sort {$a<=>$b} keys %{ $pgdata{$table} })

    if ($display_or_edit eq 'edit') {					# in edit mode, show extra fields
      if ($order_type{multi}{$table}) { if ($highest_order) { 
        if ($highest_order >= $min_rows{$table}) { $min_rows{$table} = $highest_order+1; } } }	# always make one more row than are for multi value tables
      while ($highest_order < $min_rows{$table}) {						# while there are less rows than should be
        $highest_order++; my $order = $highest_order;
        $pgdata{$table}{$highest_order}{highest_order} = $highest_order;
        if ($table eq 'firstname') {
          $entry_data .= &makeTripletHorizontal(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'middlename', 'lastname', 'name'); }
        elsif ($table eq 'aka_firstname') {
          $entry_data .= &makeTripletHorizontal(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'aka_middlename', 'aka_lastname', 'aka_name'); }
        elsif ($table eq 'old_email') {
#           $entry_data .= &makeDoubleTimeHorizontal(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'old_email_date', 'old_email');
          $entry_data .= &makeDoubleVertical(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'old_email_date', 'old_email'); }
        elsif ($table eq 'old_institution') {
          $entry_data .= &makeDoubleVertical(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'old_inst_date', 'old_institution'); }
        elsif ($table eq 'webpage') {
          $entry_data .= &makeCheckboxInput(\%pgdata, $display_or_edit, $joinkey, $order, $table, 'usefulwebpage', 'webpage'); }
        else {
          $entry_data .= &makeSingleNormal(\%pgdata, $display_or_edit, $joinkey, $order, $table); }
      } # while ($highest_order < $min_rows{$table})
    } # if ($display_or_edit eq 'edit')
  } # foreach my $table (@normal_tables)

  foreach my $table (@normal_tables) {
    my ($highest_order, @junk) = sort {$b<=>$a} keys %{ $pgdata{$table} };
    unless ($highest_order) { $highest_order = 1; }
    print "<input type=\"hidden\" id=\"type_input_$table\" value=\"$type_input{$table}\">\n";
    print "<input type=\"hidden\" id=\"highest_order_$table\" value=\"$highest_order\">\n";
  } # foreach my $table (@normal_tables)

  print "$entry_data\n";
  print "</table>\n";

  print "Switch to <a href=\"$toggle_url\">$opp_display_or_edit</a>.<br />\n";
  &makeLineageDisplay($joinkey, $display_or_edit, $header_bgcolor, $header_color);
  # allow editing of two_sender (in reverse) two_othername two_role two_date1 two_date2 two_sender

} # sub displayPerson

sub makeLineageDisplay {
  my ($joinkey, $display_or_edit, $header_bgcolor, $header_color) = @_;
  &populateLineageDropdowns();
  my $result = $dbh->prepare( "SELECT * FROM two_lineage WHERE joinkey = '$joinkey';" );
#   print "SELECT * FROM two_lineage WHERE joinkey = '$joinkey';<br />" ;
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my $bgcolor = $blue;
  print "<table style=\"border-style: none;\" border=\"0\" >\n";
  print "<tr bgcolor='$header_bgcolor'><td>$joinkey</td><td colspan=7><div style=\"color:$header_color\">Lineage</div></td></tr>\n";
  print "<tr bgcolor='$header_bgcolor'><td>sentname</td><td>othername</td><td>othertwo</td><td>role</td><td>date1</td><td>date2</td><td>sender</td><td>timestamp</td></tr>\n";
  my $lineage_count = 0;
  while (my @row = $result->fetchrow) {
    my ($a, $sentname, $othername, $othertwo, $role, $date1, $date2, $sender, $timestamp) = @row;
    unless ($sentname) { $sentname = ''; } unless ($othername) { $othername = ''; } unless ($othertwo) { $othertwo = ''; }
    unless ($role) { $role = ''; } unless ($date1) { $date1 = ''; } unless ($date2) { $date2 = ''; }
    unless ($sender) { $sender = ''; } unless ($timestamp) { $timestamp = ''; }
    $timestamp =~ s/\.[\d\-]+$//;
    $lineage_count++;
    if ($display_or_edit eq 'edit') { &makeLineageRowEdit($lineage_count, $bgcolor, $joinkey, $sentname, $othername, $othertwo, $role, $date1, $date2, $sender, $timestamp); }
      else { print "<tr bgcolor='$bgcolor'><td>$sentname</td><td>$othername</td><td>$othertwo</td><td>$role</td><td>$date1</td><td>$date2</td><td>$sender</td><td>$timestamp</td></tr>\n"; }
  } # while (my @row = $result->fetchrow)
  if ($display_or_edit eq 'edit') { 
    $bgcolor = 'white'; my $extra_lineage_fields = '5';
    for (1 .. $extra_lineage_fields) {
      $lineage_count++;
      &makeLineageRowEdit($lineage_count, $bgcolor, $joinkey, '', '', '', '', '', '', '', ''); } }
  print "</table>\n";
  print "<input type=\"hidden\" id=\"highest_order_lineage\" value=\"$lineage_count\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"sentname\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"othername\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"othertwo\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"role\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"date1\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"date2\">\n";
  print "<input type=\"hidden\" class=\"lineage_fields\" value=\"sender\">\n";
  print "<input type=\"hidden\" id=\"type_input_sentname\"  value=\"input\">\n";
  print "<input type=\"hidden\" id=\"type_input_othername\" value=\"input\">\n";
  print "<input type=\"hidden\" id=\"type_input_othertwo\"  value=\"input\">\n";
  print "<input type=\"hidden\" id=\"type_input_role\"      value=\"dropdown\">\n";
  print "<input type=\"hidden\" id=\"type_input_date1\"     value=\"dropdown\">\n";
  print "<input type=\"hidden\" id=\"type_input_date2\"     value=\"dropdown\">\n";
  print "<input type=\"hidden\" id=\"type_input_sender\"    value=\"input\">\n";
} # sub makeLineageDisplay

sub makeLineageRowEdit {
  my ($lineage_count, $bgcolor, $joinkey, $sentname, $othername, $othertwo, $role, $date1, $date2, $sender, $timestamp) = @_;
  print "<tr bgcolor='$bgcolor'>";
  &makeLineageInput($lineage_count, $joinkey, $sentname, 'sentname');
  &makeLineageInput($lineage_count, $joinkey, $othername, 'othername');
  &makeLineageInput($lineage_count, $joinkey, $othertwo, 'othertwo');
  &makeLineageDropdown($lineage_count, $joinkey, $role, 'role');
  &makeLineageDropdown($lineage_count, $joinkey, $date1, 'date1');
  &makeLineageDropdown($lineage_count, $joinkey, $date2, 'date2');
  &makeLineageInput($lineage_count, $joinkey, $sender, 'sender');
  print "<td>$timestamp</td>";
  print "</tr>";
} # sub makeLineageRowEdit

sub makeLineageInput {
  my ($lineage_count, $joinkey, $value, $column) = @_;
  unless ($value) { $value = ''; }
  print "<td><input type=\"hidden\" id=\"old_${column}_${lineage_count}\" value=\"$value\">  <input id=\"cur_${column}_${lineage_count}\" value=\"$value\"></td>";
} # sub makeLineageInput

sub makeLineageDropdown {
  my ($lineage_count, $joinkey, $value, $column) = @_;
  unless ($value) { $value = ''; }
  print "<td><input type=\"hidden\" id=\"old_${column}_${lineage_count}\" value=\"$value\">";
  print "<select id=\"cur_${column}_${lineage_count}\" size=\"1\">";
  foreach my $option (keys %{ $lineageDropdowns{$column} }) {
    my $selected = ''; if ($option eq $value) { $selected = 'selected="selected"'; }
    print "<option value=\"$option\" $selected>$lineageDropdowns{$column}{$option}</option>\n"; }
  print "</td>";
} # sub makeLineageDropdown

sub populateLineageDropdowns {
  my @dates = qw( date1 date2 );
  my ($cur_date) = &getSimpleDate();
  foreach my $column (@dates) { 
    tie %{ $lineageDropdowns{$column} }, "Tie::IxHash";
    $lineageDropdowns{$column}{''} = '';
    $lineageDropdowns{$column}{'present'} = 'present';
    my ($year) = $cur_date =~ m/^(\d{4})/;
    while ($year > 1900) {
      $lineageDropdowns{$column}{$year} = $year;
      $year--; } }
  tie %{ $lineageDropdowns{'role'} }, "Tie::IxHash";
  $lineageDropdowns{'role'}{''} = '';
  $lineageDropdowns{'role'}{'withPhd'} = 'I trained as a PhD under';
  $lineageDropdowns{'role'}{'withPostdoc'} = 'I trained as a Postdoc under';
  $lineageDropdowns{'role'}{'withMasters'} = 'I trained as a Masters under';
  $lineageDropdowns{'role'}{'withUndergrad'} = 'I trained as an Undergrad under';
  $lineageDropdowns{'role'}{'withHighschool'} = 'I trained as a High School student under';
  $lineageDropdowns{'role'}{'withSabbatical'} = 'I trained for a Sabbatical under';
  $lineageDropdowns{'role'}{'withLab_visitor'} = 'I trained as a Lab Visitor under';
  $lineageDropdowns{'role'}{'withResearch_staff'} = 'I trained as a Research Staff under';
  $lineageDropdowns{'role'}{'withAssistant_professor'} = 'I trained as an Assistant Professor under';
  $lineageDropdowns{'role'}{'withUnknown'} = 'I trained as an Unknown under';
  $lineageDropdowns{'role'}{'Phd'} = 'I trained this person as a PhD';
  $lineageDropdowns{'role'}{'Postdoc'} = 'I trained this person as a Postdoc';
  $lineageDropdowns{'role'}{'Masters'} = 'I trained this person as a Masters';
  $lineageDropdowns{'role'}{'Undergrad'} = 'I trained this person as an Undergrad';
  $lineageDropdowns{'role'}{'Highschool'} = 'I trained this person as a High School student';
  $lineageDropdowns{'role'}{'Sabbatical'} = 'I trained this person during a Sabbatical';
  $lineageDropdowns{'role'}{'Lab_visitor'} = 'I trained this person as a Lab Visitor';
  $lineageDropdowns{'role'}{'Research_staff'} = 'I trained this person as a Research Staff';
  $lineageDropdowns{'role'}{'Assistant_professor'} = 'I trained this person as an Assistant Professor';
  $lineageDropdowns{'role'}{'Unknown'} = 'I trained this person as an Unknown';
  $lineageDropdowns{'role'}{'Collaborated'} = 'I collaborated with';
} # sub populateLineageDropdowns


sub makeDisplayField {
  my ($current_value, $table, $joinkey, $order, $colspan, $rowspan, $class, $td_width, $input_size) = @_;
  unless ($current_value) { $current_value = ''; }
  if ($table eq 'webpage') { $current_value = "<a href=\"$current_value\" target=\"new\">$current_value</a>"; }
  my $data = "<td width=\"$td_width\" class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\">$current_value</td>";
  return $data;
} # sub makeDisplayField

sub makeInputField {
  my ($current_value, $table, $joinkey, $order, $colspan, $rowspan, $class, $td_width, $input_size) = @_;
  unless ($current_value) { $current_value = ''; }
  my $freeForced = 'free';
  my $containerSpanId = "container${freeForced}${table}${order}AutoComplete";
  my $divAutocompleteId = "${freeForced}${table}${order}AutoComplete";
  my $inputId = "input_${table}_$order";
  my $divContainerId = "${freeForced}${table}${order}Container";
  my $data = "<td width=\"$td_width\" class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\">
  <span id=\"$containerSpanId\">
  <div id=\"$divAutocompleteId\" class=\"div-autocomplete\">
  <input id=\"$inputId\" name=\"$inputId\" size=\"$input_size\" value=\"$current_value\">
  <div id=\"$divContainerId\"></div></div></span>
  </td>";
#    <span id=\"container${freeForced}${table}AutoComplete\">
#    <div id=\"${freeForced}${table}AutoComplete\" class=\"div-autocomplete\">
#    <input id=\"input_$table\" name=\"input_$table\" size=\"$input_size\">
#    <div id=\"${freeForced}${table}Container\"></div></div></span>
  return $data;
} # sub makeInputField

sub makeCheckboxField {
  my ($current_value, $table, $joinkey, $order) = @_;
  my $checked = ''; if ($current_value) { $checked = 'checked="checked"'; }
  my $inputId = "input_${table}_$order";
  my $data = "<input type=\"checkbox\" id=\"$inputId\" name=\"$inputId\" value=\"$table\" $checked>";
  return $data;
} # sub makeCheckboxField

sub makeSingleNormal {
  my ($pgdata_ref, $display_or_edit, $joinkey, $order, $one_table) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '550';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '80';
  my $bgcolor = 'white';
  my ($one_data, $one_row_curator, $one_timestamp, $two_data, $two_row_curator, $two_timestamp) = ('', '', '', '', '', '');
  if ($pgdata{$one_table}{$order}{data}) { $one_data = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$one_table}{$order}{row_curator}) { $one_row_curator = $pgdata{$one_table}{$order}{row_curator}; }
  if ($pgdata{$one_table}{$order}{timestamp}) { $one_timestamp = $pgdata{$one_table}{$order}{timestamp}; $one_timestamp =~ s/\.[\d\-]+$//; $one_timestamp .= "<input type=\"hidden\" id=\"timestamp_${one_table}_${order}\" value=\"$one_timestamp\">"; }
  my $td_one_data = '';
  if ($display_or_edit eq 'edit') {
      ($td_one_data) = &makeInputField($one_data, $one_table, $joinkey, $order, '3', '1', '', $td_width, $input_size); 
      if ( ($bgcolor eq $blue) && ( ($one_table eq 'email') || ($one_table eq 'institution') || ($one_table eq 'lab') ) ) { ($one_table) = &labelAddMoveButton($one_table, $order); } }	# if the table already existed and has a corresponding old table, add a button to move the data
    else {
      ($td_one_data) = &makeDisplayField($one_data, $one_table, $joinkey, $order, '3', '1', '', $td_width, $input_size); }
  if ($bgcolor eq 'white') { $order .= "<input type=\"hidden\" id=\"highest_${one_table}_order\" value=\"$order\">\n"; }	# have an id for the next highest order of the old tables for oldlab
  return "<tr bgcolor='$bgcolor'><td>$one_table</td><td>$order</td>$td_one_data<td style=\"width:12em\">&nbsp; $one_timestamp</td></tr>\n";
} # sub makeSingleNormal

sub labelAddMoveButton {
  my ($table, $order) = @_;
  $table .= " <button onclick=\"moveDataToOldTable('$table', '$order')\">move</button>";
  return $table;
} # sub labelAddMoveButton

sub makeCheckboxInput {
  my ($pgdata_ref, $display_or_edit, $joinkey, $order, $one_table, $two_table, $label) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '550';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '80';
  my $bgcolor = 'white';
  my ($one_data, $one_row_curator, $one_timestamp, $two_data, $two_row_curator, $two_timestamp) = ('', '', '', '', '', '');
  my ($td_one_data, $td_two_data, $two_checkbox);
  if ($pgdata{$one_table}{$order}{data}) { $one_data = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$one_table}{$order}{row_curator}) { $one_row_curator = $pgdata{$one_table}{$order}{row_curator}; }
  if ($pgdata{$one_table}{$order}{timestamp}) { $one_timestamp = $pgdata{$one_table}{$order}{timestamp}; $one_timestamp =~ s/\.[\d\-]+$//; }
  if ($pgdata{$two_table}{$order}{data}) { $two_data = $pgdata{$two_table}{$order}{data}; }
  if ($pgdata{$two_table}{$order}{row_curator}) { $two_row_curator = $pgdata{$two_table}{$order}{row_curator}; }
  if ($pgdata{$two_table}{$order}{timestamp}) { $two_timestamp = $pgdata{$two_table}{$order}{timestamp}; $two_timestamp =~ s/\.[\d\-]+$//; }
  if ($display_or_edit eq 'edit') {
      ($td_one_data) = &makeInputField($one_data, $one_table, $joinkey, $order, '3', '1', '', $td_width, $input_size);
      ($two_checkbox) = &makeCheckboxField($two_data, $two_table, $joinkey, $order);
      return "<tr bgcolor='$bgcolor'><td rowspan=\"1\">$label $two_checkbox</td><td rowspan=\"1\">$order</td>${td_one_data}<td style=\"width:12em\">&nbsp; $one_timestamp</td></tr>\n"; }
    else {
      ($td_one_data) = &makeDisplayField($one_data, $one_table, $joinkey, $order, '2', '1', '', '', $input_size);
      ($td_two_data) = &makeDisplayField($two_data, $two_table, $joinkey, $order, '1', '1', '', '', $input_size);
      return "<tr bgcolor='$bgcolor'><td rowspan=\"1\">$label</td><td rowspan=\"1\">$order</td>${td_one_data}${td_two_data}<td style=\"width:12em\">&nbsp; $one_timestamp</td></tr>\n"; }
} # sub makeCheckboxInput

sub makeTripletHorizontal {
  my ($pgdata_ref, $display_or_edit, $joinkey, $order, $one_table, $two_table, $three_table, $label) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '40';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '20';
  my $bgcolor = 'white';
  my ($one_data, $one_row_curator, $one_timestamp, $two_data, $two_row_curator, $two_timestamp, $three_data, $three_row_curator, $three_timestamp);
  my ($td_one_data, $td_two_data, $td_three_data);
  if ($pgdata{$one_table}{$order}{data}) { $one_data = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$one_table}{$order}{row_curator}) { $one_row_curator = $pgdata{$one_table}{$order}{row_curator}; }
  if ($pgdata{$one_table}{$order}{timestamp}) { $one_timestamp = $pgdata{$one_table}{$order}{timestamp}; $one_timestamp =~ s/\.[\d\-]+$//; }
  if ($pgdata{$two_table}{$order}{data}) { $two_data = $pgdata{$two_table}{$order}{data}; }
  if ($pgdata{$two_table}{$order}{row_curator}) { $two_row_curator = $pgdata{$two_table}{$order}{row_curator}; }
  if ($pgdata{$two_table}{$order}{timestamp}) { $two_timestamp = $pgdata{$two_table}{$order}{timestamp}; $two_timestamp =~ s/\.[\d\-]+$//; }
  if ($pgdata{$three_table}{$order}{data}) { $three_data = $pgdata{$three_table}{$order}{data}; }
  if ($pgdata{$three_table}{$order}{row_curator}) { $three_row_curator = $pgdata{$three_table}{$order}{row_curator}; }
  if ($pgdata{$three_table}{$order}{timestamp}) { $three_timestamp = $pgdata{$three_table}{$order}{timestamp}; $three_timestamp =~ s/\.[\d\-]+$//; }
  if ($display_or_edit eq 'edit') {
      ($td_one_data) = &makeInputField($one_data, $one_table, $joinkey, $order, '1', '1', '', $td_width, $input_size);
      ($td_two_data) = &makeInputField($two_data, $two_table, $joinkey, $order, '1', '1', '', $td_width, $input_size);
      ($td_three_data) = &makeInputField($three_data, $three_table, $joinkey, $order, '1', '1', '', $td_width, $input_size); }
    else {
      if ($one_timestamp) { $one_timestamp = '<br/>' . $one_timestamp; } if ($two_timestamp) { $two_timestamp = '<br/>' . $two_timestamp; } if ($three_timestamp) { $three_timestamp = '<br/>' . $three_timestamp; }
      ($td_one_data) = &makeDisplayField($one_data, $one_table, $joinkey, $order, '1', '1', '', $td_width, $input_size);
      ($td_two_data) = &makeDisplayField($two_data, $two_table, $joinkey, $order, '1', '1', '', $td_width, $input_size);
      ($td_three_data) = &makeDisplayField($three_data, $three_table, $joinkey, $order, '1', '1', '', $td_width, $input_size); }
  if ($one_timestamp) { $td_one_data =~ s/<\/td>$/$one_timestamp<\/td>/; }
  if ($two_timestamp) { $td_two_data =~ s/<\/td>$/$two_timestamp<\/td>/; }
  if ($three_timestamp) { $td_three_data =~ s/<\/td>$/$three_timestamp<\/td>/; }
  return "<tr bgcolor='$bgcolor'><td>$label</td><td>$order</td>${td_one_data}${td_two_data}${td_three_data}</tr>\n";
} # sub makeTripletHorizontal

sub makeDoubleTimeHorizontal {			# not being used
  my ($pgdata_ref, $display_or_edit, $joinkey, $order, $one_table, $two_table, $label) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '40';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '20';
  my $bgcolor = 'white';
  my ($one_data, $one_row_curator, $one_timestamp, $two_data, $two_row_curator, $two_timestamp) = ('', '', '', '', '', '');
  my ($td_one_data, $td_two_data);
  if ($pgdata{$one_table}{$order}{data}) { $one_data = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$one_table}{$order}{row_curator}) { $one_row_curator = $pgdata{$one_table}{$order}{row_curator}; }
  if ($pgdata{$one_table}{$order}{timestamp}) { $one_timestamp = $pgdata{$one_table}{$order}{timestamp}; $one_timestamp =~ s/\.[\d\-]+$//; }
  if ($pgdata{$two_table}{$order}{data}) { $two_data = $pgdata{$two_table}{$order}{data}; }
  if ($pgdata{$two_table}{$order}{row_curator}) { $two_row_curator = $pgdata{$two_table}{$order}{row_curator}; }
  if ($pgdata{$two_table}{$order}{timestamp}) { $two_timestamp = $pgdata{$two_table}{$order}{timestamp}; $two_timestamp =~ s/\.[\d\-]+$//; }
  if ($display_or_edit eq 'edit') {
      ($td_one_data) = &makeInputField($one_data, $one_table, $joinkey, $order, '1', '1', '', $td_width, $input_size);
      ($td_two_data) = &makeInputField($two_data, $two_table, $joinkey, $order, '1', '1', '', $td_width, $input_size); }
    else {
      ($td_one_data) = &makeDisplayField($one_data, $one_table, $joinkey, $order, '1', '1', '', $td_width, $input_size);
      ($td_two_data) = &makeDisplayField($two_data, $two_table, $joinkey, $order, '1', '1', '', $td_width, $input_size); }
  return "<tr bgcolor='$bgcolor'><td>$label</td><td>$order</td>${td_one_data}<td class=\"\" width=\"$td_width\">&nbsp; $one_timestamp</td>${td_two_data}<td style=\"width:$td_width\">&nbsp; $two_timestamp</td></tr>\n";
} # sub makeDoubleTimeHorizontal

sub makeDoubleVertical {
  my ($pgdata_ref, $display_or_edit, $joinkey, $order, $one_table, $two_table, $label) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '550';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '80';
  my $bgcolor = 'white';
  my ($one_data, $one_row_curator, $one_timestamp, $two_data, $two_row_curator, $two_timestamp) = ('', '', '', '', '', '');
  my ($td_one_data, $td_two_data);
  if ($pgdata{$one_table}{$order}{data}) { $one_data = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$one_table}{$order}{row_curator}) { $one_row_curator = $pgdata{$one_table}{$order}{row_curator}; }
  if ($pgdata{$one_table}{$order}{timestamp}) { $one_timestamp = $pgdata{$one_table}{$order}{timestamp}; $one_timestamp =~ s/\.[\d\-]+$//; }
  if ($pgdata{$two_table}{$order}{data}) { $two_data = $pgdata{$two_table}{$order}{data}; }
  if ($pgdata{$two_table}{$order}{row_curator}) { $two_row_curator = $pgdata{$two_table}{$order}{row_curator}; }
  if ($pgdata{$two_table}{$order}{timestamp}) { $two_timestamp = $pgdata{$two_table}{$order}{timestamp}; $two_timestamp =~ s/\.[\d\-]+$//; }
  if ($display_or_edit eq 'edit') {
      ($td_one_data) = &makeInputField($one_data, $one_table, $joinkey, $order, '3', '1', '', $td_width, $input_size);
      ($td_two_data) = &makeInputField($two_data, $two_table, $joinkey, $order, '3', '1', '', $td_width, $input_size); }
    else {
      ($td_one_data) = &makeDisplayField($one_data, $one_table, $joinkey, $order, '3', '1', '', $td_width, $input_size);
      ($td_two_data) = &makeDisplayField($two_data, $two_table, $joinkey, $order, '3', '1', '', $td_width, $input_size); }
  if ($bgcolor eq 'white') { $order .= "<input type=\"hidden\" id=\"highest_${one_table}_order\" value=\"$order\">\n"; }	# have an id for the next highest order of the old tables
  my $entry_data = "<tr bgcolor='$bgcolor'><td rowspan=\"1\">$label</td><td rowspan=\"2\">$order</td>${td_one_data}<td style=\"width:12em\">&nbsp; $one_timestamp</td></tr>\n";
  $entry_data .= "<tr bgcolor='$bgcolor'><td rowspan=\"1\">$two_table</td>${td_two_data}<td style=\"width:12em\">&nbsp; $two_timestamp</td></tr>\n";
} # sub makeDoubleVertical

### End Person Editing Section ###


### Paper Editing Section ###

sub checkoutPapers {
  &printHtmlHeader();
  my ($curator_two) = &getCuratorFromForm();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"checkoutPapers\">";
#   print "What papers to show here ?<br />\n";
#   print "SELECT joinkey FROM pap_curation_flags WHERE pap_curation_flags = 'author_person' AND joinkey NOT IN (SELECT joinkey FROM pap_curation_done WHERE pap_curation_done = 'author_person') ORDER BY joinkey::INTEGER DESC<br />" ;
  $result = $dbh->prepare( "SELECT joinkey FROM pap_curation_flags WHERE pap_curation_flags = 'author_person' AND joinkey NOT IN (SELECT joinkey FROM pap_curation_done WHERE pap_curation_done = 'author_person') ORDER BY joinkey::INTEGER DESC" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my $to_display = '';
  my $count = 0; my $max_papers_to_show = 200;
  while (my @row = $result->fetchrow) {
    $count++; next if ($count > $max_papers_to_show);
    my $url = "person_editor.cgi?curator_two=$curator_two&paper_id=$row[0]&action=Search+Paper";
    $to_display .= "<a href=\"$url\">$row[0]</a><br/>\n";
  }
  print "There are " . scalar($count) . " papers, will only display the highest $max_papers_to_show paper IDs :<br/>";
  print $to_display;
} # sub &checkoutPapers

sub createPeopleFromXml {
  &printHtmlHeader();
  my ($curator_two) = &getCuratorFromForm();

    # add link to checkout more papers, also add link to next WBPaper ID
  (my $var, my $paper_joinkey) = &getHtmlVar($query, "paper_joinkey");
  my $paper_editor_url = "http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=$curator_two&action=Search&data_number=$paper_joinkey";
  print "Creating persons from authors in WBPaper$paper_joinkey <a target=\"new\" href=\"$paper_editor_url\">paper editor link</a>.<br />\n";
  my $prev_paper_joinkey = $paper_joinkey - 1;
  my $prev_url = "person_editor.cgi?curator_two=$curator_two&paper_id=$prev_paper_joinkey&action=Search+Paper";
  print "Checkout previous paper id <a href=\"$prev_url\">WBPaper" . &padZeros($prev_paper_joinkey) . "</a> ";
  my $next_paper_joinkey = $paper_joinkey + 1;
  my $next_url = "person_editor.cgi?curator_two=$curator_two&paper_id=$next_paper_joinkey&action=Search+Paper";
  print "Checkout next paper id <a href=\"$next_url\">WBPaper" . &padZeros($next_paper_joinkey) . "</a> ";
  my $checkout_url = "person_editor.cgi?curator_two=$curator_two&paper_id=&action=Checkout+Papers";
  print "<a href=\"$checkout_url\">checkout page</a>.<br />";
  print "<hr/>\n";

  print "<input type=\"hidden\" name=\"paper_joinkey\" id=\"paper_joinkey\" value=\"$paper_joinkey\">";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"createPeopleFromXml\">";
  print "<input type=\"hidden\" name=\"curator_two\" id=\"curator_two\" value=\"$curator_two\">";
  ($var, my $max_institutions) = &getHtmlVar($query, "max_institutions");
  ($var, my $aids_to_check) = &getHtmlVar($query, "aids_to_check");
  my %inst; my %aids;
  my @inst_tables = qw( institution street city state post country lab webpage comment );
  for my $i (1 .. $max_institutions) {
    foreach my $table (@inst_tables) {
      if ($table eq 'street') {
          for my $j (1 .. 4) {  
            my $extra_order = ($i - 1) * 4 + $j;
            ($var, my $data)    = &getHtmlVar($query, "input_${table}_$extra_order");
            if ($data) {          $inst{$i}{$table}{$j} = $data; } } }
        else {
          ($var, my $data) = &getHtmlVar($query, "input_${table}_$i");
          if ($data) {       $inst{$i}{$table}{1} = $data; } } } }
  my @two_fields = qw( old_inst_choice inst_choice aid highest_join standardname firstname middlename lastname email );
  my @two_tables = qw( standardname firstname middlename lastname email );

  my ($two_number) = &getHighestJoinkey(); 
  my @pgcommands;
  foreach my $i (0 .. $aids_to_check) {
    foreach my $table (@two_fields) {
      ($var, my $data) = &getHtmlVar($query, "${table}_$i");
      if ($data) {       $aids{$i}{$table}{1} = $data; } }
    my $aid = $aids{$i}{aid}{1};
    my $pap_join = 1; if ($aids{$i}{highest_join}{1}) { $pap_join = $aids{$i}{highest_join}{1} + 1; }

    my $aid_error_message = '';
    unless ($aids{$i}{lastname}{1}) { $aid_error_message .= "No lastname chosen for AID $aid<br/>\n"; }
    unless ( ($aids{$i}{inst_choice}{1}) || ($aids{$i}{old_inst_choice}{1}) ) { $aid_error_message .= "No institution nor old institution chosen for AID $aid<br/>\n"; }
    if ($aid_error_message) { print "$aid_error_message<hr/>"; next; }

    my $inst_error_message = ''; my $inst_id = ''; my $old_inst_id = '';
    if ( $aids{$i}{inst_choice}{1} ) { 
      $inst_id = $aids{$i}{inst_choice}{1};
      unless ($inst{$inst_id}{institution}{1}) { $inst_error_message .= "ERROR : Institution $inst_id chosen for Inst, but it has no institution data<br />\n"; } }
    if ( $aids{$i}{old_inst_choice}{1} ) { 
      $old_inst_id = $aids{$i}{old_inst_choice}{1};
      unless ($inst{$old_inst_id}{institution}{1}) { $inst_error_message .= "ERROR : Institution $old_inst_id chosen for old Inst, but it has no institution data<br />\n"; } }
    if ($inst_error_message) { print "$inst_error_message<hr/>"; next; }

    $two_number++;
    my $joinkey = 'two' . $two_number;
    (@pgcommands) = &addToPgcommandsTwoCreation($two_number, $curator_two, @pgcommands);
    foreach my $table (@two_tables) {
      my $order = 1;
      if ($aids{$i}{$table}{$order}) { 
        my $data = $aids{$i}{$table}{$order};
        (@pgcommands) = &addToPgAndHst($table, $joinkey, $order, $data, $curator_two, @pgcommands);
        print "$table : $data<br />\n"; } }
    if ($inst_id) {						# institution data
      foreach my $table (@inst_tables) {
        foreach my $order (sort {$a<=>$b} keys %{ $inst{$inst_id}{$table} }) {
          (@pgcommands) = &addToPgAndHst($table, $joinkey, $order, $inst{$inst_id}{$table}{$order}, $curator_two, @pgcommands);
          print "$table : $order : $inst{$inst_id}{$table}{$order}<br />\n"; } } }
    if ($old_inst_id) {						# old institution data (only get the first institution)
      my $table = 'old_institution'; my $order = 1;
      (@pgcommands) = &addToPgAndHst($table, $joinkey, $order, $inst{$old_inst_id}{'institution'}{$order}, $curator_two, @pgcommands);
      print "$table : $order : $inst{$old_inst_id}{'institution'}{$order}<br />\n";
      my $date = &getPgDate(); $table = 'old_inst_date';	# use current date for old institution date (confirmed by Cecilia)
      (@pgcommands) = &addToPgAndHst($table, $joinkey, $order, $date, $curator_two, @pgcommands);
      print "$table : $order : $date<br />\n"; }
    my $edit_two_url = "person_editor.cgi?curator_two=$curator_two&action=Search&display_or_edit=edit&input_number_1=$joinkey";	# add link to person_editor in edit mode
    print "aid $aid with new join $pap_join to new <a href=\"$edit_two_url\" target=\"new\">$joinkey</a>.<br />\n";
    print "<hr>\n";
  } # foreach my $i (0 .. $aids_to_check)

  my $is_curation_done = 0;
  $result = $dbh->prepare( "SELECT pap_curation_done FROM pap_curation_done WHERE pap_curation_done = 'author_person' AND joinkey = '$paper_joinkey'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); if ($row[0]) { $is_curation_done++; }
  unless ($is_curation_done) {					# if it's not curation_done for author_person, add it
    my $order = 0;
    $result = $dbh->prepare( "SELECT pap_order FROM pap_curation_done WHERE joinkey = '$paper_joinkey' ORDER BY pap_order DESC" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my @row = $result->fetchrow(); if ($row[0]) { $order = $row[0]; }
    $order++;
    push @pgcommands, "INSERT INTO pap_curation_done VALUES ('$paper_joinkey', 'author_person', '$order', '$curator_two')";
    push @pgcommands, "INSERT INTO h_pap_curation_done VALUES ('$paper_joinkey', 'author_person', '$order', '$curator_two')";
  } # unless ($is_curation_done)

  foreach my $pgcommand (@pgcommands) {
    print "$pgcommand<br>\n";
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)

#   ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $joinkey, $order, $newValue, $curator_two);

  print "<input type=\"hidden\" name=\"max_institutions\" value=\"$max_institutions\">\n";
} # sub createPeopleFromXml

sub addToPgcommandsTwoCreation {
  my ($two_number, $curator_two, @pgcommands) = @_;
  my $joinkey = 'two' . $two_number;
  push @pgcommands, "INSERT INTO two VALUES ('$joinkey', '$two_number');";	# table two has no _hst, two_order, nor two_curator
  (@pgcommands) = &addToPgAndHst('status', $joinkey, '1', 'Valid', $curator_two, @pgcommands); 
  return @pgcommands; }

sub addToPgAndHst {
  my ($table, $joinkey, $order, $data, $curator_two, @pgcommands) = @_;
  if ($data) { if ($data =~ m/\'/) { $data =~ s/\'/''/g; } $data = "E'$data'"; } else { $data = 'NULL'; }
  push @pgcommands, "INSERT INTO two_$table VALUES ('$joinkey', $order, $data, '$curator_two')";
  push @pgcommands, "INSERT INTO h_two_$table VALUES ('$joinkey', $order, $data, '$curator_two')";
  return @pgcommands;
} # sub addToPgAndHst

sub searchPaper {
  &printHtmlHeader();
  my ($curator_two) = &getCuratorFromForm();
  my ($var, $paper_id) = &getHtmlVar($query, "paper_id");
  if ($paper_id =~ m/(\d+)/) { &displayPaper(&padZeros($1), $curator_two); return; }
    else { print "Not a number in $paper_id<br />\n"; }
} # sub searchPaper

sub makePdfLinkFromPath {
  my ($path) = shift;
  my ($pdf) = $path =~ m/\/([^\/]*)$/;
  my $link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
  my $data = "<a href=\"$link\" target=\"new\">$pdf</a>"; return $data; }

sub displayPaper {
  my ($joinkey, $curator_two) = @_;
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"displayPaperXml\">";
  my %curation_flags; my $curation_flags;
  $result = $dbh->prepare( "SELECT pap_curation_flags FROM pap_curation_flags WHERE joinkey = '$joinkey'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $curation_flags{$row[0]}++; } $curation_flags = join", ", sort keys %curation_flags;
  if ($curation_flags) { print "<b style=\"color: red;font-size: 14pt\">curation_flags : $curation_flags</b><br />\n"; }
  my %curation_done; my $curation_done;
  $result = $dbh->prepare( "SELECT pap_curation_done FROM pap_curation_done WHERE joinkey = '$joinkey'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $curation_done{$row[0]}++; } $curation_done = join", ", sort keys %curation_done;
  if ($curation_done) { print "<b style=\"color: red;font-size: 14pt\">curation_done : $curation_done</b><br />\n"; }

  my $paper_editor_url = "http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=$curator_two&action=Search&data_number=$joinkey";
  print "WBPaper$joinkey <a target=\"new\" href=\"$paper_editor_url\">paper editor link</a>.<br />\n";
  my $pmid; my %pg_aid;
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey = '$joinkey'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    if ($row[1] =~ m/pmid/) { $pmid = $row[1]; $pmid =~ s/pmid//; $row[1] = "<a href=\"http://www.ncbi.nlm.nih.gov/pubmed/$pmid\" target=\"new\">$row[1]</a>"; }
    print "Identifier : $row[1]<br />\n"; }
  $result = $dbh->prepare( "SELECT * FROM pap_affiliation WHERE joinkey = '$joinkey'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    print "Affiliation : $row[1]<br />\n"; }
  $result = $dbh->prepare( "SELECT pap_electronic_path FROM pap_electronic_path WHERE joinkey = '$joinkey' AND pap_electronic_path IS NOT NULL" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { my ($pdf_link) = &makePdfLinkFromPath($row[0]); print "pdf link : $pdf_link<br />\n"; }
  
  my @aids; 
  $result = $dbh->prepare( "SELECT pap_author FROM pap_author WHERE joinkey = '$joinkey' ORDER BY pap_order" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { push @aids, $row[0]; }
  my $aids = join"','", @aids;
  my @aut_tables = qw( index possible sent verified );
  foreach my $table (@aut_tables) {
    $result = $dbh->prepare( "SELECT * FROM pap_author_$table WHERE author_id IN ('$aids')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { unless ($row[2]) { $row[2] = 1; } $pg_aid{$row[0]}{$table}{$row[2]} = $row[1]; } }

  my $xmldata = ''; my $affiliation = ''; 
  my %xml_authors;			# data from authors by name
  my %xml_authors_found;		# names found, to print ones not found

  if ($pmid) {
      $/ = undef;
      my @xml_paths = qw( /home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/done/ /home/postgres/work/pgpopulation/wpa_papers/wpa_pubmed_final/xml/ );
      my $xmlfile = '';
      foreach my $path (@xml_paths) {
        my $file = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/done/' . $pmid;
        if (-e $file) { $xmlfile = $file; }
      }
      if ($xmlfile) {
          print "pmid $pmid xml found<br />\n";
          open (IN, "<$xmlfile") or die "Cannot open $xmlfile : $!";
          $xmldata = <IN>;
          close (IN) or die "Cannot close $xmlfile : $!";
          $/ = "\n";
          %xml_authors = &getXmlAuthors($xmldata); }
        else { print "NO XML for $pmid\n"; } }
    else { print "<br />No PMID found for WBPaper$joinkey<br />\n"; }
  
  print "<hr>\n";
  print "<form name='form1' method=\"post\" action=\"person_editor.cgi\">\n";
  print "<input type=\"hidden\" name=\"curator_two\" id=\"curator_two\" value=\"$curator_two\">";
  print "<input type=\"hidden\" name=\"paper_joinkey\" id=\"paper_joinkey\" value=\"$joinkey\">";

  my $max_institutions = 100;
  print "<input type=\"hidden\" id=\"max_institutions\" name=\"max_institutions\" value=\"$max_institutions\">\n";
  my @affil_tables = qw( institution street city state post country lab webpage comment );
  for my $i (1 .. $max_institutions) { 
    &showInstitutionEditor($i, $curator_two, \@affil_tables, $affiliation, $max_institutions); }
  foreach my $table (@affil_tables) {
    print "<input type=\"hidden\" class=\"fields\" value=\"$table\" \/>\n";
    print "<input type=\"hidden\" id=\"type_input_$table\" value=\"$type_input{$table}\">\n";
    my $highest_order_table = $max_institutions;
    if ($table eq 'street') { $highest_order_table = $max_institutions * 4; }
    print "<input type=\"hidden\" id=\"highest_order_$table\" value=\"$highest_order_table\">\n"; }

  print "<hr>\n";

#   my %aka_hash = (); # &getAkaHash();
  my %aka_hash = &getAkaHash();

  print "<table border=0 cellspacing=5>\n";
  print "<tr bgcolor=\"$blue\"><td>aid</td><td>author</td><td>possible</td><td>sent</td><td>verified</td><td>standard name</td><td>firstname</td><td>middlename</td><td>lastname</td><td>email</td><td>inst</td><td>old inst</td></tr>\n";
  foreach my $i (0 .. $#aids) {
    my $aid = $aids[$i]; my $aname = $pg_aid{$aid}{index}{'1'};
    my $bgcolor = $blue; my $already_verified = 0;
    my $line = '';
    $line .= "<td><input name=\"aid_$i\" type=\"hidden\" value=\"$aid\">$aid</td>";
    $line .= "<td>$aname</td>";
    $aname =~ s/[\,\.]//g;                         # take out commas and dots
    $aname =~ s/_/ /g;                             # replace underscores for spaces
    my @tables = qw( possible sent verified ); my $highest_join = 0;
    foreach my $table (@tables) {
      my @data = (); 
      foreach my $pap_join (sort {$a<=>$b} keys %{ $pg_aid{$aid}{$table} }) { 
        my $data = $pg_aid{$aid}{$table}{$pap_join};
        if ($table eq 'possible') { push @data, &twonumToLink($data, $curator_two); }
          elsif ($table eq 'verified') { push @data, $data; if ($data =~ m/YES/) { $already_verified++; } }
          else { push @data, $data; }
        if ($pap_join > $highest_join) { $highest_join = $pap_join; } }
      my $data = join"<br />", @data; $line .= "<td>$data</td>\n"; }
    my ($firstname, $middlename, $lastname, $standardname, $affiliation) = ('','','','','');
    if ($xml_authors{$aname}) {				# without this check, the subhash checks create the hash entry
#       if ($xml_authors{$aname}{affiliation}) { $affiliation = $xml_authors{$aname}{affiliation}; $xml_authors_found{$aname}++; }
#       if ($xml_authors{$aname}{lastname}) { $lastname = $xml_authors{$aname}{lastname}; $xml_authors_found{$aname}++; }
#       if ($xml_authors{$aname}{firstname}) { $firstname = $xml_authors{$aname}{firstname}; $xml_authors_found{$aname}++; }
#       if ($xml_authors{$aname}{standardname}) { $standardname = $xml_authors{$aname}{standardname}; $xml_authors_found{$aname}++; }
      if ($xml_authors{$aname}{affiliation}) {  $affiliation  = shift @{ $xml_authors{$aname}{affiliation} };  $xml_authors_found{$aname}++; }
      if ($xml_authors{$aname}{lastname}) {     $lastname     = shift @{ $xml_authors{$aname}{lastname} };     $xml_authors_found{$aname}++; }
      if ($xml_authors{$aname}{firstname}) {    $firstname    = shift @{ $xml_authors{$aname}{firstname} };    $xml_authors_found{$aname}++; }
      if ($xml_authors{$aname}{standardname}) { $standardname = shift @{ $xml_authors{$aname}{standardname} }; $xml_authors_found{$aname}++; } }
    print "<input type=\"hidden\" name=\"highest_join_$i\" value=\"$highest_join\">\n";
    $line .= "<td><input name=\"standardname_$i\" value=\"$standardname\"></td>";
    $line .= "<td><input name=\"firstname_$i\" value=\"$firstname\"></td>";
    $line .= "<td><input name=\"middlename_$i\" value=\"\"></td>";
    $line .= "<td><input name=\"lastname_$i\" value=\"$lastname\"></td>";
    $line .= "<td><input name=\"email_$i\" value=\"\"></td>";
    $line .= "<td><select name=\"inst_choice_$i\" size=\"1\">\n";
    $line .= "<option value=\"\" selected=\"selected\"></option>\n";
    foreach my $i (1 .. $max_institutions) { $line .= "<option value=\"$i\" >Inst$i</option>\n"; }
    $line .= "</select></td>";
    $line .= "<td><select name=\"old_inst_choice_$i\" size=\"1\">\n";
    $line .= "<option value=\"\" selected=\"selected\"></option>\n";
    foreach my $i (1 .. $max_institutions) { $line .= "<option value=\"$i\" >Inst$i</option>\n"; }
    $line .= "</select></td>";
    if ($already_verified) { $bgcolor = $grey; }
    $line = "<tr bgcolor=\"$bgcolor\">" . $line;
    $line .= "</tr><tr bgcolor=\"$bgcolor\">";
    my ($matchCount, $matchTwos) = &matchFullnameToAka($standardname, $firstname, $lastname, \%aka_hash, $curator_two);
    $line .= qq(<td colspan="2" align="right">$matchCount matches</td><td colspan="4">$matchTwos</td><td colspan="6">$affiliation</td>);
    $line .= "</tr>";
    print "$line\n";
  } # foreach my $i (0 .. $#aids)

  print "</table>\n";
  print "<input type=\"hidden\" name=\"aids_to_check\" value=\"$#aids\">\n";
  unless ($curation_done =~ m/author_person/) {		# only show button to create person if it's not done for author_person
    print "<input type=submit name=action value=\"Create people from XML\"><br/>\n"; }

  foreach my $aname (sort keys %xml_authors) {		# list all authors in xml that were not found in current paper
    next unless $aname; next if ($xml_authors_found{$aname});
    my ($firstname, $lastname, $initials) = ('','','','');
    if ($xml_authors{$aname}{lastname}) {  $lastname  = shift @{ $xml_authors{$aname}{lastname} };  }
    if ($xml_authors{$aname}{firstname}) { $firstname = shift @{ $xml_authors{$aname}{firstname} }; }
    if ($xml_authors{$aname}{initials}) {  $initials  = shift @{ $xml_authors{$aname}{initials} };  }
    print "XML author $aname has no match in paper Firstname : $firstname ; Lastname : $lastname ; Initials : $initials<br />\n"; }

  print "</form>\n";
} # sub displayPaper

sub twonumToLink {
  my ($twonum, $curator_two) = @_;
  return "<a target=\"new\" href=\"person_editor.cgi?action=Search&input_number_1=$twonum&curator_two=$curator_two\">$twonum</a>"; }

sub matchFullnameToAka {
  my ($fullname, $forename, $lastname, $aka_hash_ref, $curator_two) = @_;
  my %aka_hash = %$aka_hash_ref;
  my $orig_author = $fullname;
  $fullname = lc($fullname);
  my @two_links;
  if ($aka_hash{$fullname}) {
      foreach my $two (sort keys %{ $aka_hash{$fullname} } ) { 
        push @two_links, &twonumToLink("two$two", $curator_two); } }
  if ( (scalar(@two_links) == 0) &&  ($forename =~ m/ \w$/) ) {
    $forename =~ s/ \w$//; $fullname = "$forename $lastname"; $fullname = lc($fullname);
    if ($aka_hash{$fullname}) {
      foreach my $two (sort keys %{ $aka_hash{$fullname} } ) { 
        push @two_links, &twonumToLink("two$two", $curator_two); } } }
  my $twos = join", ", @two_links;
  my $count = scalar @two_links;
#   return "<td colspan=\"2\" align=\"right\">$count matches</td><td colspan=\"10\">$twos</td>";
  return ($count, $twos);
} # sub matchFullnameToAka

sub getXmlAuthors {
  my ($xmldata) = @_; my %xml_authors;
  my @xml_authors = $xmldata =~ /\<Author.*?\>(.+?)\<\/Author\>/sig;
  foreach my $author_xml (@xml_authors) {
    my ($affiliation) = $author_xml =~ /\<Affiliation\>(.+?)\<\/Affiliation\>/i;
    my ($lastname) = $author_xml =~ /\<LastName\>(.+?)\<\/LastName\>/i;
    my ($initials) = $author_xml =~ /\<Initials\>(.+?)\<\/Initials\>/i;
    my ($forename) = $author_xml =~ /\<ForeName\>(.+?)\<\/ForeName\>/i;
    my $author = $lastname . " " . $initials;
#     $xml_authors{$author}{affiliation} = $affiliation;
#     $xml_authors{$author}{lastname} = $lastname;
#     $xml_authors{$author}{firstname} = $forename;
#     $xml_authors{$author}{initials} = $initials;
#     $xml_authors{$author}{standardname} = "$forename $lastname"; }
    push @{ $xml_authors{$author}{affiliation} },  $affiliation;
    push @{ $xml_authors{$author}{lastname} },     $lastname;
    push @{ $xml_authors{$author}{firstname} },    $forename;
    push @{ $xml_authors{$author}{initials} },     $initials;
    push @{ $xml_authors{$author}{standardname} }, "$forename $lastname"; }
  return %xml_authors; 
} # sub getXmlAuthors

# sub showAuthorXmlEditor {
# # THIS DOESN'T WORK because it shows by XML instead of by aid
# # show all authors and their possible association
# # for each author, AID, aname
# # if already has pap_author_possible data : show two# (and link each to the person editor's person editing page)
# # elsif it has new matches to 1 or more two# : show possible matches (and link each to the person editor's person editing page)
# # else no existing pap_author_possible data, and 0 matches to existing persons : xml-forename, xml-lastname, <blank>middlename-field, standard_name default forename+ +lastname, inst-dropdown, <blank>email-field, comment-field with WBPaper####, button to create person.  require: lastname, firstname, stdname, institution-field-in-inst#.  New people add to 'two_status' 'Valid', 'two' '<#>'.  Associate to pap_author_possible aid.  Get back two# and replace this whole thing with a <td> to look like the pap_author_possible data (show two# w/link).
#   my ($i, $author_xml, $joinkey, $curator_two, $max_institutions, $pg_pap_href, $aka_hash_href) = @_;
#   my %pg_pap = %$pg_pap_href; my %aka_hash = %$aka_hash_href;
#   my ($lastname) = $author_xml =~ /\<LastName\>(.+?)\<\/LastName\>/i;
#   my ($initials) = $author_xml =~ /\<Initials\>(.+?)\<\/Initials\>/i;
#   my ($forename) = $author_xml =~ /\<ForeName\>(.+?)\<\/ForeName\>/i;
#   my $author = $lastname . " " . $initials;
#   my $line = "<tr bgcolor=\"$blue\">";
#   $line .= "<td>$author</td>";
#   if ($pg_pap{$joinkey}{aut}{$author}) {			# $joinkey and $author matches an author_id
#     my $aid = $pg_pap{$joinkey}{aut}{$author};
#     my $fullname = "$forename $lastname";
#     $line .= "<td><input name=\"aid_$i\" type=\"hidden\" value=\"$aid\">$aid</td>";
#     $line .= "<td><input name=\"standard_name_$i\" value=\"$fullname\"></td>";
#     $line .= "<td><input name=\"firstname_$i\" value=\"$forename\"></td>";
#     $line .= "<td><input name=\"middlename_$i\" value=\"\"></td>";
#     $line .= "<td><input name=\"lastname_$i\" value=\"$lastname\"></td>";
#     $line .= "<td><select name=\"inst_choice_$i\" size=\"1\">\n";
#     $line .= "<option value=\"\" selected=\"selected\"></option>\n";
#     foreach my $i (1 .. $max_institutions) { $line .= "<option value=\"$i\" >Inst$i</option>\n"; }
#     $line .= "</select></td>";
#     my $twos = '';
#     my $orig_author = $fullname;
#     $fullname = lc($fullname);
# #     my $count = 0;
# #     my $next = 0;                             # skip flag if there are too many two matches for that fullname
#     my @two_links;
#     if ($aka_hash{$fullname}) {
#         foreach my $two (sort keys %{ $aka_hash{$fullname} } ) { 
#           push @two_links, "<a target=\"new\" href=\"person_editor.cgi?action=Search&input_number_1=two$two&curator_two=$curator_two\">two$two</a>"; } }
# #         my @twos = keys %{ $aka_hash{$fullname} };
# #         $count = scalar(@twos);
# #         if ($count > 20) { print "Author $orig_author @twos\n"; $next++; }
# #         $twos = join", ", @twos; 
#     if ( (scalar(@two_links) == 0) &&  ($forename =~ m/ \w$/) ) {
#       $forename =~ s/ \w$//; $fullname = "$forename $lastname"; $fullname = lc($fullname);
#       if ($aka_hash{$fullname}) {
#         foreach my $two (sort keys %{ $aka_hash{$fullname} } ) { 
#           push @two_links, "<a target=\"new\" href=\"person_editor.cgi?action=Search&input_number_1=two$two&curator_two=$curator_two\">two$two</a>"; } } }
# #         my @twos = keys %{ $aka_hash{$fullname} };
# #         $count = scalar(@twos);
# #         if ($count > 20) { print "Author $orig_author @twos\n"; $next++; }
# #         $twos = join", ", @twos;
# #     next if $next;
#     my $twos = join", ", @two_links;
#     my $count = scalar @two_links;
#     $line .= "</td><td>$count matches</td><td>$twos</td>";
#   } # if ($pg_pap{$joinkey}{aut}{$author})
#   $line .= "</tr>";
#   print "$line\n";
# } # sub showAuthorXmlEditor

sub showInstitutionEditor {
  my ($i, $curator_two, $affil_tables_ref, $affiliation, $max_institutions) = @_;
  my @affil_tables = @$affil_tables_ref;
  my $show_another_institution = ''; my $hide_this_institution = '';
  if ($i < $max_institutions) { 			# link to show another institution if it's not the last one (last cannot show anything else)
    my $html_table_id = $i + 1; $html_table_id = 'table_' . $html_table_id;
    $show_another_institution = "<a href=\"#\" onclick=\"document.getElementById('$html_table_id').style.display = ''; return false\">show another institution</a>"; }
  if ($i > 1) { 					# link to hide this institution if it's not the first one (first must always be there)
    my $html_table_id = 'table_' . $i;
    $hide_this_institution = "<a href=\"#\" onclick=\"document.getElementById('$html_table_id').style.display = 'none'; return false\">hide this institution</a>"; }
  my $show_institutions_with_data_only = qq(<a href="#" onclick="showInstitutionsWithDataOnly(); return false">show institutions with data only</a>);
  my $style = ''; if ($i > 1) { $style = 'display: none'; }
  print "<table border=0 cellspacing=5 id=\"table_$i\" style=\"$style\">\n";
  print "<tr><td>Inst$i</td><td>$curator_two $show_another_institution $hide_this_institution $show_institutions_with_data_only</td></tr>\n";
  my $order = $i; my $input_size = 80; my $colspan = 1;
  foreach my $table (@affil_tables) {
    my $value = ''; if ( ($table eq 'institution') && ($order == 1) ) { $value = $affiliation; }
    if ($table eq 'street') {
        for my $j (1 .. 4) {  
          my $street_order = ($order - 1) * 4 + $j;
          my $table_row_autocomplete = &showEditorText($table, $street_order, $input_size, $colspan, $value);
          print "<tr bgcolor=\"$blue\">$table_row_autocomplete</tr>\n"; } }
      else {
        my $table_row_autocomplete = &showEditorText($table, $order, $input_size, $colspan, $value);
        print "<tr bgcolor=\"$blue\">$table_row_autocomplete</tr>\n"; } }
  print "</table>\n";
} # sub showInstitutionEditor

sub getAkaHash {
  my %filter; my %aka_hash;
  my @tables = qw (first middle last);
  foreach my $table (@tables) {
    $result = $dbh->prepare ( "SELECT * FROM two_aka_${table}name WHERE two_aka_${table}name IS NOT NULL AND two_aka_${table}name != 'NULL' AND two_aka_${table}name != '' AND joinkey IN (SELECT joinkey FROM two_status WHERE two_status = 'Valid');" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( my @row = $result->fetchrow ) {
      my $joinkey = $row[0];
      $row[2] =~ s/^\s+//g; $row[2] =~ s/\s+$//g;     # take out spaces in front and back
      $row[2] =~ s/[\,\.]//g;                         # take out commas and dots
      $row[2] =~ s/_/ /g;                             # replace underscores for spaces
      $row[2] = lc($row[2]);                          # for full values (lowercase it)
      $row[0] =~ s/two//g;                            # take out the 'two' from the joinkey
      $filter{$row[0]}{$table}{$row[2]}++;
      unless ($table eq 'last') {                     # look at initials for first and middle but not last name
        my ($init) = $row[2] =~ m/^(\w)/;             # for initials
        if ($init) { $filter{$row[0]}{$table}{$init}++; } } }
    $result = $dbh->prepare ( "SELECT * FROM two_${table}name WHERE two_${table}name IS NOT NULL AND two_${table}name != 'NULL' AND two_${table}name != '' AND joinkey IN (SELECT joinkey FROM two_status WHERE two_status = 'Valid');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( my @row = $result->fetchrow ) {
      my $joinkey = $row[0];
      $row[2] =~ s/^\s+//g; $row[2] =~ s/\s+$//g;     # take out spaces in front and back
      $row[2] =~ s/[\,\.]//g;                         # take out commas and dots
      $row[2] =~ s/_/ /g;                             # replace underscores for spaces
      $row[2] = lc($row[2]);                          # for full values (lowercase it)
      $row[0] =~ s/two//g;                            # take out the 'two' from the joinkey
      $filter{$row[0]}{$table}{$row[2]}++;
      unless ($table eq 'last') {
        my ($init) = $row[2] =~ m/^(\w)/;             # for initials
        $filter{$row[0]}{$table}{$init}++; } }
  } # foreach my $table (@tables)

  my $possible;
  foreach my $person (sort keys %filter) {
    foreach my $last (sort keys %{ $filter{$person}{last}} ) {
      foreach my $first (sort keys %{ $filter{$person}{first}} ) {
        $possible = "$last $first"; $aka_hash{$possible}{$person}++;
        $possible = "$first $last"; $aka_hash{$possible}{$person}++;
        if ( $filter{$person}{middle} ) {		# Middle name okay if last first middle or first middle last  2007 02 22
          foreach my $middle (sort keys %{ $filter{$person}{middle}} ) {
            $possible = "$last $first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last ${first}$middle"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "${first}$middle $last"; $aka_hash{$possible}{$person}++; } } } } }
  return %aka_hash;
} # sub getAkaHash

### End Paper Editing Section ###


### Person Statistics Section ###

sub personStatistics {
  print "Content-type: text/html\n\n";
  my %stats; my %total; my %isCurrent;				# stats by month-status-joinkey ; total stats by status-joinkey ; current status state for joinkey
  my $result = $dbh->prepare( "SELECT * FROM h_two_status ORDER BY two_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while ( my @row = $result->fetchrow() ) {
    my ($joinkey, $order, $status, $curator, $timestamp) = @row;
    my ($month) = $timestamp =~ m/^(\d\d\d\d\-\d\d)/;
#     next unless ($month =~ m/2007/);				# to test only a subset
    my $isCurrent = ''; if ($isCurrent{$joinkey}) { $isCurrent = $isCurrent{$joinkey}; }
    if ($status ne $isCurrent) {				# only add to stats if status has changed
      $isCurrent{$joinkey} = $status;				# keep track of latest status state
      $stats{$month}{$status}{$joinkey}++;			# stats by month / status / personId
      $stats{$month}{any}{$joinkey}++;				# add an "any" status
    } # if ($status ne $isCurrent)
  } # while ( my @row = $result->fetchrow() )
  print qq(<table style="border-style: none;" border="1" color="blue">);
#   print "<tr><$thDot>Year-Month</td><$thDot>Valid</td><$thDot>Invalid</td><$thDot>Delta Valid</th><$thDot>Total Valid</td><$thDot>Total Invalid</td><$thDot>Total Current Valid</th></tr>\n";
  print "<tr><$thDot>Year-Month</td><$thDot>Valid</td><$thDot>Invalid</td><$thDot>Valid or Invalid</th><$thDot>Total Valid</td><$thDot>Total Invalid</td><$thDot>Total Any</th></tr>\n";
  my $mcount = 0; my @vmonths; my @valid; my @tmonths; my @totalvalid;	# month count (don't use first month for average nor valid graph), arrays for graphs of months vs valid and months vs total valid 
  foreach my $month (sort keys %stats) {				# sort months alphanumerically so total will be inclusive up to current month looping through
    $mcount++;								# track month count
    foreach my $status (sort keys %{ $stats{$month} }) {
      foreach my $joinkey (sort keys %{ $stats{$month}{$status} }) {
        $total{$status}{$joinkey}++;					# add to %total hash for that status (bug, in the total, people will show as both valid and invalid if they're ever each)
        $total{any}{$joinkey}++; } }					# total always keeps track of all values up to that month (since it sorts months alphanumerically
    my $validCount = scalar keys %{ $stats{$month}{Valid} };
    my $invalidCount = scalar keys %{ $stats{$month}{Invalid} };
    my $anyCount = scalar keys %{ $stats{$month}{any} };
    my $totalValid = scalar keys %{ $total{Valid} };
    my $totalInvalid = scalar keys %{ $total{Invalid} };
    my $totalAny = scalar keys %{ $total{any} };
    if ($mcount > 1) { push @vmonths, $month; push @valid, $validCount; }	# graph valid except for first month which has a lot of transferred objects
    push @tmonths, $month; push @totalvalid, $totalValid;			# graph total valid for all months
    print "<tr><$tdDot>$month</td><$tdDot>$validCount</td><$tdDot>$invalidCount</td><$tdDot>$anyCount</td><$tdDot>$totalValid</td><$tdDot>$totalInvalid</td><$tdDot>$totalAny</td></tr>\n";
#     my $deltaValid = $validCount - $invalidCount;
#     $totalValid += $validCount; $totalInvalid += $invalidCount; $totalDeltaValid += $deltaValid;
#     print "<tr><$tdDot>$month</td><$tdDot>$validCount</td><$tdDot>$invalidCount</td><$tdDot>$deltaValid</td><$tdDot>$totalValid</td><$tdDot>$totalInvalid</td><$tdDot>$totalDeltaValid</td></tr>\n";
  } # foreach my $month (sort keys %stats)
  print "<tr><$thDot>Year-Month</td><$thDot>Valid</td><$thDot>Invalid</td><$thDot>Valid or Invalid</th><$thDot>Total Valid</td><$thDot>Total Invalid</td><$thDot>Total Any</th></tr>\n";
  print "</table>";

#     # generate graphs of valid and totalvalid in data/ .png files
#   my @data = (\@vmonths, \@valid);
#   my $xsize = scalar(@vmonths) * 50;
#   my $mygraph = GD::Graph::area->new($xsize, 300);
#   $mygraph->set(
#     x_label     => 'Year-Month',
#     y_label     => 'Valid Persons created',
#     title       => 'Valid Persons created in each Year-Month',
#   ) or warn $mygraph->error;
#   my $myimage = $mygraph->plot(\@data) or warn $mygraph->error;
#   my $validPngFile = '/home/postgres/public_html/cgi-bin/cecilia/data/person_editor_valid.png';
#   open (OUT, ">$validPngFile") or warn "Cannot create $validPngFile : $!";
#   print OUT $myimage->png;
#   close (OUT) or warn "Cannot close $validPngFile : $!";
#   @data = (\@tmonths, \@totalvalid);
#   $xsize = scalar(@tmonths) * 50;
#   $mygraph = GD::Graph::area->new($xsize, 300);
#   $mygraph->set(
#     x_label     => 'Year-Month',
#     y_label     => 'Total Valid Persons',
#     title       => 'Total Valid Persons in each Year-Month',
#   ) or warn $mygraph->error;
#   $myimage = $mygraph->plot(\@data) or warn $mygraph->error;
#   my $totalvalidPngFile = '/home/postgres/public_html/cgi-bin/cecilia/data/person_editor_totalvalid.png';
#   open (OUT, ">$totalvalidPngFile") or warn "Cannot create $totalvalidPngFile : $!";
#   print OUT $myimage->png;
#   close (OUT) or warn "Cannot close $totalvalidPngFile : $!";
#   print qq(<img src="data/person_editor_valid.png"><br/>\n);
#   print qq(<img src="data/person_editor_totalvalid.png"><br/>\n);

  my $xdata = join"|", @vmonths;
  my $ydata = join"|", @valid;
  my $xlabel = 'Year-Month';
  my $ylabel = 'Valid Persons created';
  my $title   = 'Valid Persons created in each Year-Month';
  my $graph_valid = qq(<img src="person_editor.cgi?action=generatePng&xdata=$xdata&ydata=$ydata&xlabel=$xlabel&ylabel=$ylabel&title=$title"><br/>\n);

  $xdata = join"|", @tmonths;
  $ydata = join"|", @totalvalid;
  $xlabel = 'Year-Month';
  $ylabel = 'Total Valid Persons';
  $title   = 'Total Valid Persons in each Year-Month';
  my $graph_totalvalid = qq(<img src="person_editor.cgi?action=generatePng&xdata=$xdata&ydata=$ydata&xlabel=$xlabel&ylabel=$ylabel&title=$title"><br/>\n);

  pop @valid;	# get rid of the current month, which is not yet finished
  my $totalvalidforavg = 0; foreach my $v (@valid) { $totalvalidforavg += $v; } 	# add up all months minus the most recent month
  my $avgvalidcreated = FormatSigFigs($totalvalidforavg / scalar(@valid), 5);		# divide by the number of months added together, and round to 5 sig figs
  print "<br/>$avgvalidcreated Average Valid Created per Month (except for first month and most recent month)<br/><br/>\n";

  print $graph_valid;
  print $graph_totalvalid;

} # sub personStatistics

sub generatePng {
  (my $oop, my $xdata)  = &getHtmlVar($query, 'xdata' );
  ($oop, my $ydata)  = &getHtmlVar($query, 'ydata' );
  ($oop, my $xlabel) = &getHtmlVar($query, 'xlabel');
  ($oop, my $ylabel) = &getHtmlVar($query, 'ylabel');
  ($oop, my $title)  = &getHtmlVar($query, 'title' );
  my @xdata = split/\|/, $xdata;
  my @ydata = split/\|/, $ydata;
  my @data = (\@xdata, \@ydata);
  my $xsize = scalar(@xdata) * 50;
  my $mygraph = GD::Graph::area->new($xsize, 300);
  $mygraph->set(
    x_label     => $xlabel,
    y_label     => $ylabel,
    title       => $title,
  ) or warn $mygraph->error;
  my $myimage = $mygraph->plot(\@data) or warn $mygraph->error;
  print "Content-type: image/png\n\n";
  print $myimage->png;
} # sub generatePng

### End Person Statistics Section ###


### Address by pasting in two numbers Section ###

sub addressByTwos {
  &printHtmlHeader();
  print "<form name='form1' method=\"get\" action=\"person_editor.cgi\">\n";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"addressByTwosInput\">";
  my ($curator_two) = &getCuratorFromForm();
  print "<textarea name=\"twos\" rows=6 cols=60 value=\"\"></textarea></td>\n";
  print "<input type=submit name=action value=\"Display Address by Twos\">\n";
  print "</form>\n";
  &printFooter();
} # sub addressByTwos

sub displayAddressByTwos {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"displayAddressByTwosInput\">";
  my ($curator_two) = &getCuratorFromForm();
  (my $oop, my $twos)  = &getHtmlVar($query, 'twos' );
  my (@twos) = $twos =~ m/(two\d+)/g; my $joinkeys = join"','", @twos;;
  my @tables = qw( street city state post country institution );
  my %data;
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM two_${table} WHERE joinkey IN ('$joinkeys') ORDER BY joinkey, two_order; " );
#     print qq( "SELECT * FROM two_{$table} WHERE joinkey IN ('$joinkeys') ORDER BY joinkey, two_order; " );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
#       print "<tr><td>$row[0]</td><td>$row[1]</td><td>$row[2]</td></tr>\n"; 
      $data{$row[0]}{$table} .= "$row[2]<br/>";
    } # while (my @row = $result->fetchrow)
  } # foreach my $table (@tables)
  print "<table border=0 cellspacing=5>\n";
  foreach my $joinkey (sort keys %data) {
    print qq(<tr><td><a href="person_editor.cgi?curator_two=two1823&paper_id=&action=Search&display_or_edit=edit&input_number_1=$joinkey">$joinkey</a></td>);
    foreach my $table (@tables) {
      print "<td>$data{$joinkey}{$table}</td>";
    } # foreach my $table (@tables)
    print "</tr>";
  } # foreach my $joinkey (sort keys %data)
  print "</table>\n";
  &printFooter();
} # sub displayAddressByTwos

### End Address by pasting in two numbers Section ###


sub firstPage {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"firstPage\">";
  my $date = &getDate();
    # using post instead of get makes a confirmation request when javascript reloads the page after a change.  2010 03 12
  print "<form name='form1' method=\"get\" action=\"person_editor.cgi\">\n";
  print "<table border=0 cellspacing=5>\n";
  print "<tr><td colspan=\"2\">Select your Name : <select name=\"curator_two\" size=\"1\">\n";
  &populateCurators();
  my $ip = $query->remote_host();                               # select curator by IP if IP has already been used
  my $curator_by_ip = '';
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip';" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; my @row = $result->fetchrow;
  if ($row[0]) { $curator_by_ip = $row[0]; }
#   my @curator_list = ('Juancarlos Chan', 'Cecilia Nakamura');
  my @curator_list = ('two1823', 'two1', 'two12028', 'two712', 'two2970');
  foreach my $joinkey (@curator_list) {                         # display curators in alphabetical (array) order, if IP matches existing ip record, select it
    my $curator = $joinkey;
    if ($curators{two}{$curator}) { $curator = $curators{two}{$curator}; }
    if ($joinkey eq $curator_by_ip) { print "<option value=\"$joinkey\" selected=\"selected\">$curator</option>\n"; }
      else { print "<option value=\"$joinkey\" >$curator</option>\n"; } }
  print "</select></td>";
  print "<td colspan=\"2\">Date : $date</td></tr>\n";

  print "<tr><td>&nbsp;</td></tr>\n";

  print "<tr>\n";
  print "<td colspan=\"3\">WBPaperID : <input id=\"paper_id\" name=\"paper_id\" size=\"10\" value=\"\"><input type=submit name=action value=\"Search Paper\">\n";
  print "<input type=submit name=action value=\"Checkout Papers\">\n";
  print "<input type=submit name=action value=\"Person Statistics\">\n";
  print "<input type=submit name=action value=\"Address by Twos\"></td>\n";
  print "<tr>\n";
  print "<td colspan=\"3\"><input type=submit name=action value=\"Create New Person\">\n";
  print "<input type=submit name=action value=\"Search\">\n";
  (my $var, my $display_or_edit) = &getHtmlVar($query, "display_or_edit"); my $display_checked = 'checked="checked"'; my $edit_checked = ''; 
  if ($display_or_edit) { if ($display_or_edit eq 'edit') { $edit_checked = 'checked="checked"'; $display_checked = ''; } }
#       if ($current_value) { if ($current_value eq $value) { $selected = "selected=\"selected\""; $found_value++; } }
  print "<input type=\"radio\" name=\"display_or_edit\" value=\"display\" $display_checked />display\n";
  print "<input type=\"radio\" name=\"display_or_edit\" value=\"edit\" $edit_checked />edit\n";
  print "</td>\n";
#   print "<td><input type=\"checkbox\" name=\"history\" value=\"on\">display history (not search history)</td>\n";
  print "</tr>\n";
  foreach my $table ("number", @normal_tables) {
    my $order = 1; my $input_size = 80; my $colspan = 1;
    my $table_to_print = &showEditorText($table, $order, $input_size, $colspan, '');
    $table_to_print .= "<input type=\"hidden\" class=\"fields\" value=\"$table\" \/>\n";
    $table_to_print .= "<input type=\"hidden\" id=\"type_input_$table\" value=\"$type_input{$table}\">\n";
    $table_to_print .= "<input type=\"hidden\" id=\"highest_order_$table\" value=\"1\">\n";

    print "<tr>";
    print $table_to_print;
    my $style = ''; 
    if ( ($table eq 'number') || ($table eq 'status') ) { $style = 'display: none'; }
#     print "<tr><td>$table</td>";
#     if ( $dropdowns{$table} ) {				# if there are dropdown options for the table
#         my ($td_data) = &makeSelectField('', $table, 0, 0); print $td_data; }
#       else {
#     print "<td><input size=40 name=\"data_$table\"></td>\n"; }
    print "<td style='$style'><input type=\"checkbox\" value=\"on\" name=\"substring_$table\">substring</td>\n";
    print "<td style='$style'><input type=\"checkbox\" value=\"on\" name=\"case_$table\">case insensitive (automatic substring)</td>\n"; 
    print "</tr>\n";
  } # foreach my $table "number", (@normal_tables)

  print "</table>\n";
  print "</form>\n";
  &printFooter();
} # sub firstPage

sub showEditorText {
  my ($table, $order, $input_size, $colspan, $value) = @_;
  my $table_to_print = "<td id=\"label_$table\">$table</td><td width=\"550\" colspan=\"$colspan\">\n";  # there's some weird auto-sizing of the table where it shrinks to nothing if the td doesn't have a size, so min size is 550
#   $table_to_print .= "<input id=\"input_$table\" name=\"input_$table\" size=\"$input_size\">\n";
  my $freeForced = 'free';
  my $containerSpanId = "container${freeForced}${table}${order}AutoComplete";
  my $divAutocompleteId = "${freeForced}${table}${order}AutoComplete";
  my $inputId = "input_${table}_$order";
  my $divContainerId = "${freeForced}${table}${order}Container";
  $table_to_print .= "<span id=\"$containerSpanId\">\n";
  $table_to_print .= "<div id=\"$divAutocompleteId\" class=\"div-autocomplete\">\n";
  $table_to_print .= "<input id=\"$inputId\" name=\"$inputId\" size=\"$input_size\" value=\"$value\">\n";
  $table_to_print .= "<div id=\"$divContainerId\"></div></div></span>\n";
#   $table_to_print .= "<span id=\"container${freeForced}${table}AutoComplete\">\n";
#   $table_to_print .= "<div id=\"${freeForced}${table}AutoComplete\" class=\"div-autocomplete\">\n";
#   $table_to_print .= "<input id=\"input_$table\" name=\"input_$table\" size=\"$input_size\">\n";
#   $table_to_print .= "<div id=\"${freeForced}${table}Container\"></div></div></span>\n";
  $table_to_print .= "</td>\n";
  return $table_to_print;
} # sub showEditorText


sub getCuratorFromForm {
  (my $var, my $curator_two) = &getHtmlVar($query, "curator_two");
  if ($curator_two) { &updateCurator($curator_two); } else { print "ERROR : No curator chosen, using two1<br />\n"; $curator_two = 'two1'; }
  print "<input type=\"hidden\" name=\"curator_two\" id=\"curator_two\" value=\"$curator_two\">";
  return $curator_two;
} # sub getCuratorFromForm

sub populateCurators {
  my $result = $dbh->prepare( "SELECT * FROM two_standardname; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    $curators{two}{$row[0]} = $row[2];
    $curators{std}{$row[2]} = $row[0]; } }

sub updateCurator {
  my ($joinkey) = @_;
  my $ip = $query->remote_host();
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip' AND joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  unless ($row[0]) {
    $result = $dbh->do( "DELETE FROM two_curator_ip WHERE two_curator_ip = '$ip' ;" );
    $result = $dbh->do( "INSERT INTO two_curator_ip VALUES ('$joinkey', '$ip')" );
    print "IP $ip updated for $joinkey<br />\n"; } }


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

sub printHtmlHeader {
  print "Content-type: text/html\n\n";
  my $title = 'Person Editor';
  my $header = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><HTML><HEAD>';
  $header .= "<title>$title</title>\n";

  $header .= '<link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" />';
#   $header .= '<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/fonts/fonts-min.css" />';
  $header .= "<link rel=\"stylesheet\" type=\"text/css\" href=\"http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css\" />";


  $header .= "<style type=\"text/css\">#forcedPersonAutoComplete { width:25em; padding-bottom:2em; } .div-autocomplete { padding-bottom:1.5em; }</style>";

  $header .= '
    <!-- always needed for yui -->
    <script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/yahoo-dom-event/yahoo-dom-event.js"></script>

    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/element/element-min.js"></script>-->

    <!-- for autocomplete calls -->
    <script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/datasource/datasource-min.js"></script>

    <!-- OPTIONAL: Connection Manager (enables XHR for DataSource)	needed for Connect.asyncRequest -->
    <script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/connection/connection-min.js"></script> 

    <!-- Drag and Drop source file --> 
    <script src="http://yui.yahooapis.com/2.7.0/build/dragdrop/dragdrop-min.js" ></script>

    <!-- At least needed for drag and drop easing -->
    <script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/animation/animation-min.js"></script>


    <!-- OPTIONAL: JSON Utility (for DataSource) -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/json/json-min.js"></script>-->

    <!-- OPTIONAL: Get Utility (enables dynamic script nodes for DataSource) -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/get/get-min.js"></script>-->

    <!-- OPTIONAL: Drag Drop (enables resizeable or reorderable columns) -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/dragdrop/dragdrop-min.js"></script>-->

    <!-- OPTIONAL: Calendar (enables calendar editors) -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/calendar/calendar-min.js"></script>-->

    <!-- Source files -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/datatable/datatable-min.js"></script>-->

    <!-- Resize not needed to resize data table, just change div height -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/resize/resize.js"></script> -->

    <!-- autocomplete js -->
    <script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/autocomplete/autocomplete-min.js"></script>

    <!-- container_core js -->
    <!--<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/container/container-min.js"></script>-->

    <!-- form-specific js put this last, since it depends on YUI above -->
    <script type="text/javascript" src="../javascript/person_editor.js"></script>

  ';
  $header .= "</head>";
  $header .= '<body class="yui-skin-sam">';
  print $header;
} # printHtmlHeader

__END__

sub updatePostgresLineageDataTEMP {
  if ($sentname) { $sentname_pair = "two_sentname = '$sentname'"; $sentname = "'$sentname'"; $has_some_value++; }
    else { $sentname_pair = "two_sentname IS NULL"; $sentname = 'NULL'; }
  if ($othername) { $othername_pair = "two_othername = '$othername'"; $othername = "'$othername'"; $has_some_value++; }
    else { $othername_pair = "two_othername IS NULL"; $othername = 'NULL'; }
  if ($othertwo) { $othertwo_pair = "two_othertwo = '$othertwo'"; $othertwo = "'$othertwo'"; $has_some_value++; }
    else { $othertwo_pair = "two_othertwo IS NULL"; $othertwo = 'NULL'; }
  if ($date1) { $date1_pair = "two_date1 = '$date1'"; $date1 = "'$date1'"; $has_some_value++; } 
    else { $date1_pair = "two_date1 IS NULL"; $date1 = 'NULL'; }
  if ($date2) { $date2_pair = "two_date2 = '$date2'"; $date2 = "'$date2'"; $has_some_value++; } 
    else { $date2_pair = "two_date2 IS NULL"; $date2 = 'NULL'; }
  if ($role) {
      $has_some_value++;  
      if ($reverse_role eq 'Collaborated') { }
        elsif ($reverse_role =~ m/^with/ ) { $reverse_role =~ s/with//g; }
        else { $reverse_role = "with$reverse_role"; }
      $role_pair = "two_role = '$role'"; $role = "'$role'";
      $reverse_role_pair = "two_role = '$reverse_role'"; $reverse_role = "'$reverse_role'"; }
    else { 
      $role_pair = "two_role IS NULL"; $reverse_role_pair = "two_role IS NULL"; 
      $role = 'NULL'; $reverse_role = 'NULL'; }
  if ($sender) {
      $has_some_value++;  
      if ($reverse_sender =~ m/^REV \- / ) { $reverse_sender =~ s/^REV \- //g; }
        else { $reverse_sender = "REV - $reverse_sender"; }
      $sender_pair = "two_sender = '$sender'"; $reverse_sender_pair = "two_sender = '$reverse_sender'"; 
      $sender = "'$sender'"; $reverse_sender = "'$reverse_sender'"; }
    else { 
      $sender_pair = "two_sender IS NULL"; $reverse_sender_pair = "two_sender IS NULL"; 
      $sender = 'NULL'; $reverse_sender = 'NULL'; }
  push @pgcommands, "DELETE FROM two_lineage WHERE joinkey = $joinkey AND $sentname_pair AND $othername_pair AND $othertwo_pair AND $date1_pair AND $date2_pair AND $role_pair AND $sender_pair";
} # sub updatePostgresLineageDataTEMP

sub makeSelectField {
  my ($current_value, $table, $order, $is_editable) = @_;
  my $data = "<td colspan=\"3\">";
  if (scalar (@{ $dropdowns{$table} }) > 0) {				# if there are dropdown options for the table
    my $javascript_action = '';
    if ($is_editable eq 'editable') { $javascript_action = " onchange=\"changeSelect('$table', '$order')\""; }
    my $element_name = "data_$table"; if ($order) { $element_name .= "_$order"; }
    $data .= "<select id=\"$element_name\" name=\"$element_name\" $javascript_action>\n";
    my $found_value = '';
    foreach my $value ('', @{ $dropdowns{$table} }) {
      my $selected = "";
      if ($current_value) { if ($current_value eq $value) { $selected = "selected=\"selected\""; $found_value++; } }
      $data .= "<option value=\"$value\" $selected>$value</option>\n"; }
    $data .= "</select>";
    unless ($found_value) { $data .= $current_value; }
  } # if (scalar (@{ $dropdowns{$table} }) > 0)
  $data .= "</td>";
  return $data;
} # sub makeSelectField

sub stub {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"stub\">";
  print "Code not ready yet<br />\n";
  &printFooter();
}

sub paperAuthorPersonGroup {
  &printHtmlHeader();
  &populateCurators();						# for verified yes / no standard name
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  print "<input type=\"hidden\" name=\"curator_id\" id=\"curator_id\" value=\"$curator_id\">";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"paperAuthorPersonGroup\">";

  ($oop, my $two_id) = &getHtmlVar($query, 'two_id');
  ($oop, my $paper_aid_in_group) = &getHtmlVar($query, 'paper_aid_in_group');
  my ($lastnames_arrayref, $all_names_hashref) = &displayPersonInfo($two_id);

  my $category_index_hashref = &populateCategoryIndex();
  my %category_index = %$category_index_hashref;

  my %papers; my %aids; my @papers = split/\t/, $paper_aid_in_group;
  foreach my $paper_aid_color (@papers) {
    my ($joinkey, $aid, $category) = split/, /, $paper_aid_color;
    $aids{$aid}++;
    $papers{$joinkey}{aid} = $aid;
    $papers{$joinkey}{category} = $category;
    $papers{$joinkey}{color} = $category_index{$category}{color}; }
  my (@joinkeys) = sort keys %papers; my $joinkeys = join"', '", @joinkeys;
  my (@aids) = sort keys %aids; my $aids = join"', '", @aids;
 
  my %paper_hash; my @tables = qw( title identifier electronic_path year );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM pap_$table WHERE joinkey IN ('$joinkeys');" );
#     if ($table eq 'identifier') { $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid' AND joinkey IN ('$joinkeys')"); }		# for only pmids, but Cecilia wants all to see abstracts
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      unless ($row[2]) { $row[2] = 0; }
      $paper_hash{$table}{$row[0]}{$row[2]} = $row[1]; } }

  my %aid_hash; my @author_tables = qw( index possible verified );
  foreach my $table (@author_tables) {
    $result = $dbh->prepare( "SELECT * FROM pap_author_$table WHERE author_id IN ('$aids');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      unless ($row[2]) { $row[2] = 0; }
      $aid_hash{$row[0]}{$row[2]}{$table} = $row[1]; } }

  print "<table style=\"border-style: none;\" border=\"1\" >";
  foreach my $joinkey (@joinkeys) {
    my $pap_link = "http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=$curator_id&action=Search&data_number=$joinkey";
    print "<tr><td class=\"normal_odd\" colspan=\"5\"><br/><a href=\"$pap_link\">$joinkey</a></td></tr>\n";
    foreach my $table (@tables) {
      if ($paper_hash{$table}{$joinkey}) {
        foreach my $order (sort {$a<=>$b} keys %{ $paper_hash{$table}{$joinkey} }) {
          my $data = $paper_hash{$table}{$joinkey}{$order};
          my $table_name = $table;
          if ($table eq 'identifier') { if ($data =~ m/pmid/) { ($data) = &makeNcbiLinkFromPmid($data); } }
          elsif ($table eq 'electronic_path') { ($data) = &makePdfLinkFromPath($data); $table_name = 'pdf'; }
          print "<tr><td class=\"normal_odd\" colspan=\"1\">$table_name</td><td class=\"normal_odd\" colspan=\"4\">$data</td></tr>\n"; } } }
    my $aid = $papers{$joinkey}{aid};
    my $color = $papers{$joinkey}{color};
    my $category = $papers{$joinkey}{category};
    my $aid_name = ''; my @entries; my $flag_show_buttons = 1;
    if ($aid_hash{$aid}{0}{index}) { $aid_name = "<span style=\"color: $color\">$aid_hash{$aid}{0}{index}</span>"; }
    foreach my $join (sort {$a<=>$b} keys %{ $aid_hash{$aid} }) {
      next if ($join == 0);				# skip non-existing joins
      my $possible = ''; my $verified = ''; 
      my $alink_color = 'grey';				# possible that do not match current two_id have links in this colour
      if ($aid_hash{$aid}{$join}{possible}) { 
        $possible = $aid_hash{$aid}{$join}{possible}; 
        if ($possible eq $two_id) { $flag_show_buttons = 0; $alink_color = 'blue'; } }		# if possible matches person, it's already connected, don't show buttons
      if ($aid_hash{$aid}{$join}{verified}) { $verified = $aid_hash{$aid}{$join}{verified}; }
      my $on = "YES  $curators{two}{$curator_id}"; my $off = "NO  $curators{two}{$curator_id}";
      my ($td_author_verified) = &makeToggleTripleField($verified, 'author_verified', $aid, $join, $curator_id, 1, 1, 'normal_odd', $on, $off, '');	# make this a toggleTripleField instead of just a display  2010 06 09
      my $entry = "<td class=\"normal_odd\">$join</td><td class=\"normal_odd\"><a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/cecilia/two_display.cgi?action=Number+!&number=$possible\" style=\"color: $alink_color\" target=\"new\">$possible</a></td>$td_author_verified";
      push @entries, $entry; }
    my $lines_count = scalar(@entries); unless ($lines_count) { $lines_count = 1; } my $first_entry = shift @entries; 
    print "<tr><td rowspan=\"$lines_count\" class=\"normal_odd\" colspan=\"1\">author</td><td rowspan=\"$lines_count\" class=\"normal_odd\" colspan=\"1\">$aid_name ($aid)</td>$first_entry</tr>\n";
    foreach my $entry (@entries) { print "<tr>$entry</tr>\n"; }
#     if ($category > 6) { # }				# this didn't help, we're force reloading after button press, so actually need to check if any possible matches instead
    if ($flag_show_buttons) { 
      my @joins = sort {$b<=>$a} keys %{ $aid_hash{$aid} }; my $new_join = $joins[0] + 1;
      print "<tr><td id=\"td_connect_buttons_$aid\" class=\"normal_odd\" colspan=6>\n";
      print "<button onclick=\"updatePostgresTableField('author_possible', '$aid', '$new_join', '$curator_id', '$two_id', '', ''); document.getElementById('td_connect_buttons_$aid').innerHTML = '';\">connect to $two_id, no verification</button>\n";
      print "<button onclick=\"updatePostgresTableField('author_possible', '$aid', '$new_join', '$curator_id', '$two_id', '', 'nothing'); updatePostgresTableField('author_verified', '$aid', '$new_join', '$curator_id', 'YES  $curators{two}{$curator_id}', '', ''); document.getElementById('td_connect_buttons_$aid').innerHTML = '';\">connect to $two_id and verify YES</button>\n";
      print "<button onclick=\"updatePostgresTableField('author_possible', '$aid', '$new_join', '$curator_id', '$two_id', '', 'nothing'); updatePostgresTableField('author_verified', '$aid', '$new_join', '$curator_id', 'NO  $curators{two}{$curator_id}', '', ''); document.getElementById('td_connect_buttons_$aid').innerHTML = '';\">connect to $two_id and verify NO</button>\n";
#       print "<button onclick=\"updatePostgresTableField('author_possible', '$aid', '$new_join', '$curator_id', '$two_id', '', 'nothing');\">connect to $two_id, no verification</button>\n";
#       print "<button>connect to $two_id and verify YES</button> <button>connect to $two_id and verify NO</button></td>
      print "</tr>\n"; }
#         $curate_link = "<a href=\"#\" onclick=\"updatePostgresTableField('curation_flags', '$joinkey', '$order', '$curator_id', 'rnai_curation', '', 'nothing'); document.getElementById('td_curate_$joinkey').innerHTML = '$curators{two}{$curator_id}'; return false\">curate</a>";
  } # foreach my $joinkey (@joinkeys)
  print "</table>";

  &printFooter();
} # sub paperAuthorPersonGroup

sub personAuthorCuration {
  &printHtmlHeader();
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  ($oop, my $two_number_search) = &getHtmlVar($query, 'two_number_search');
  if ($two_number_search) { if ($two_number_search =~ m/(\d+)/) { $two_number_search = $1; } }
    else { $two_number_search = ''; }
  print "<input type=\"hidden\" name=\"curator_id\" id=\"curator_id\" value=\"$curator_id\">\n";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"personAuthorCuration\">\n";
  print "two number : <input id=\"two_number_search\" value=\"$two_number_search\" onblur=\"var url = 'http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=$curator_id&action=Person+Author+Curation&two_number_search=' + document.getElementById('two_number_search').value; window.location = url\"><br />\n";
  if ($two_number_search) { 
    my $two_id = 'two' . $two_number_search;
    my ($lastnames_arrayref, $all_names_hashref) = &displayPersonInfo($two_id);
    &displayPaperAuthorMatchesByPerson($curator_id, $two_id, $lastnames_arrayref, $all_names_hashref); }
  &printFooter();
} # sub personAuthorCuration

sub populateCategoryIndex {
  my %category_index;
  $category_index{1}{desc} = 'Verified YES Cecilia';
  $category_index{2}{desc} = 'Verified YES Raymond';
  $category_index{3}{desc} = 'Verified YES';
  $category_index{4}{desc} = 'Verified NO ';
  $category_index{5}{desc} = 'Verified YES to Other possible (not shown)';
  $category_index{6}{desc} = 'Connected not verified';
  $category_index{7}{desc} = 'Connected to Other not verfied';
  $category_index{8}{desc} = 'Exact Match not connected to anyone';
  $category_index{9}{desc} = 'Last name Match';
  $category_index{1}{color} = '#0000ff';
  $category_index{2}{color} = '#880088';
  $category_index{3}{color} = '#00ff00';
  $category_index{4}{color} = '#ff0000';
  $category_index{5}{color} = '#cdb79e';
#   $category_index{5}{color} = 'NO';
  $category_index{6}{color} = '#ff00cc';
  $category_index{7}{color} = '#aaaa00';
  $category_index{8}{color} = '#00ffcc';
  $category_index{9}{color} = '#000000';
  return \%category_index;
}

sub displayPaperAuthorMatchesByPerson {
  my ($curator_id, $two_id, $lastnames_arrayref, $all_names_hashref) = @_;
  my %all_names = %$all_names_hashref;

  my $category_index_hashref = &populateCategoryIndex();
  my %category_index = %$category_index_hashref;

  print "Color index : ";
  foreach my $cat (sort {$a<=>$b} keys %category_index) {
    my $color = $category_index{$cat}{color};
    my $desc = $category_index{$cat}{desc};
    print "<span style=\"color: $color\">$desc</span> "; }
  print "</br><br/><br/>\n";

my $start = time;

  foreach my $lastname (@$lastnames_arrayref) {
    print "$lastname matches :<br />\n";
    my %category;
    my %aid_names;
    $result = $dbh->prepare( "SELECT * FROM pap_author_index WHERE pap_author_index ~ '^$lastname ' OR pap_author_index ~ ' ${lastname}\$' OR pap_author_index ~ '^${lastname},';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      if ($row[1] =~ m/,/) { $row[1] =~ s/,//g; }
      $aid_names{$row[0]} = $row[1]; }
    my (@aids) = sort keys %aid_names; my $author_ids = join"', '", @aids;
    my %paper;
    $result = $dbh->prepare( "SELECT * FROM pap_author WHERE pap_author IN ('$author_ids') AND joinkey NOT IN (SELECT joinkey FROM pap_curation_flags WHERE pap_curation_flags = 'functional_annotation') ;" );		# papers must be in list of matching author names and not functinal_annotation flag
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $paper{pap_aid}{$row[0]}{$row[1]}++; $paper{aid_pap}{$row[1]}{$row[0]}++; }

    my %possible; my %verified;
    $result = $dbh->prepare( "SELECT * FROM pap_author_possible WHERE author_id IN ('$author_ids');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $possible{$row[0]}{$row[2]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM pap_author_verified WHERE author_id IN ('$author_ids');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $verified{$row[0]}{$row[2]} = $row[1]; }

    foreach my $aid (keys %aid_names) {
      my $cat = 9;
      if ($possible{$aid}) {								# connected to someone
          foreach my $join (keys %{ $possible{$aid} }) {				
            my $possible = $possible{$aid}{$join};
            if ($verified{$aid}{$join}) {
                my $verified = $verified{$aid}{$join};
                if ($possible eq $two_id) {						# connected to this person
                    if ($verified =~ m/^YES/) {						# verified yes
                        if ($verified =~ m/Cecilia/) { $cat = 1; }			# by Cecilia
                        elsif ($verified =~ m/Raymond/) { if ($cat > 2) { $cat = 2; } }	# by Raymond
                        else { if ($cat > 3) { $cat = 3; } } }				# by someone else
                      elsif ($verified =~ m/^NO/) { if ($cat > 4) { $cat = 4; } } }	# verified no
                  else {								# connected to someone else
                    if ($verified =~ m/^YES/) { if ($cat > 5) { $cat = 5; } } } }	# verified yes by someone else
              else {									# not verified
                if ($possible eq $two_id) { if ($cat > 6) { $cat = 6; } }		# connected to this person
                  else { if ($cat > 7) { $cat = 7; } } } } }				# connected to other person
        else {										# not connected to anyone
          my $match_name = $aid_names{$aid};
          if ($match_name =~ m/,/) { $match_name =~ s/,//g; }                           # filter out commas for exact matches
          if ($match_name =~ m/\s+/) { $match_name =~ s/\s+/ /g; }                      # filter out extra spaces for exact matches
          if ($all_names{$match_name}) { if ($cat > 8) { $cat = 8; } } }		# if exact aka/name match to author name
      if ($cat < 5) { $category{done}{$aid} = $cat; }				# store into %category depending on category
        elsif ($cat > 5) { $category{not_done}{$aid} = $cat; }
        else { $category{ignore}{$aid} = $cat; }
    } # foreach my $aid (keys %aid_names)

    foreach my $type ('not_done', 'done') {
      print "<table style=\"border-style: none;\" border=\"1\" >";
      my $cell_data = ''; my @paper_aid_in_group;
      my %paps; my $count = 0; my $start = 1;
      foreach my $aid (keys %{ $category{$type} }) {
        foreach my $paper (keys %{ $paper{aid_pap}{$aid} }) { $paps{$paper}++; } }
      foreach my $joinkey (sort keys %paps) {
        foreach my $aid (keys %{ $paper{pap_aid}{$joinkey} }) {
          if ($category{$type}{$aid}) {
            $count++;
            my $color = $category_index{$category{$type}{$aid}}{color};
            my $pap_link = "http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=$curator_id&action=Search&data_number=$joinkey";
            $cell_data .= "<a style=\"color: $color; text-decoration: none\" href=\"$pap_link\">$joinkey ( $aid $aid_names{$aid} )</a><br />\n";
            push @paper_aid_in_group, "$joinkey, $aid, $category{$type}{$aid}";
#             $cell_data .= "<span style=\"color: $color\">J $joinkey A $aid C $category{$type}{$aid} E</span><br />\n";
            if ($count % 10 == 0) { 							# divisible by 10, make a new set
              &formTrPaperAuthorMatchesByPerson($curator_id, $two_id, \@paper_aid_in_group, $start, $count, $cell_data);
              $start = $count + 1; $cell_data = ''; @paper_aid_in_group = (); } } } }
      if ($cell_data) { &formTrPaperAuthorMatchesByPerson($curator_id, $two_id, \@paper_aid_in_group, $start, $count, $cell_data); }	# still stuff to print, print it out
      print "</table>";
    } # foreach my $type ('not_done', 'done')

#     foreach my $joinkey (sort keys %{ $paper{pap_aid} }) {
#       foreach my $aid (sort keys %{ $paper{pap_aid}{$joinkey} }) {
#         my $color = $category_index{$category{$aid}}{color};
#         print "<span style=\"color: $color\">J $joinkey A $aid C $category{$aid} E</span><br />\n";
#       } # foreach my $aid (sort keys %{ $paper{pap_aid}{$joinkey} })
#     } # foreach my $joinkey (sort keys %{ $paper{pap_aid} })

  } # foreach my $lastname (@$lastnames_arrayref)

  foreach my $all_name (sort keys %all_names) {
    print "Exact name match to $all_name<br />\n";
  } # foreach my $all_name (sort keys %all_names)

my $end = time;
my $diff = $end - $start;
print "$diff seconds<br/>\n";
} # sub displayPaperAuthorMatchesByPerson

sub formTrPaperAuthorMatchesByPerson {		# make a tr and form for a set of paper author matches by person
  my ($curator_id, $two_id, $paper_aid_in_group_arrayref, $start, $count, $cell_data) = @_;
  my $paper_aid_in_group = join"\t", @$paper_aid_in_group_arrayref;
  print "<form name='form1' method=\"get\" action=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi\">\n";
  print "<input type=\"hidden\" name=\"paper_aid_in_group\" value=\"$paper_aid_in_group\">";
  print "<input type=\"hidden\" name=\"two_id\" value=\"$two_id\">";
  print "<input type=\"hidden\" name=\"curator_id\" value=\"$curator_id\">";
  print "<tr><td class=\"normal_odd\">$start to $count</td><td class=\"normal_odd\">$cell_data</td><td class=\"normal_odd\"><input type=\"submit\" name=\"action\" value=\"Paper Author Person Group\"></td></tr>\n";
  print "</form>\n";
} # sub formTrPaperAuthorMatchesByPerson

sub displayPersonInfo {
  my ($two_id) = @_;
  my %hash; my %all_lastnames; my %all_names;
  my @show_tables = qw( institution firstname middlename lastname aka_firstname aka_middlename aka_lastname );
  my %shown; foreach (@show_tables) { $shown{$_}++; }
  my @tables = qw( firstname middlename lastname street city state post country institution mainphone labphone officephone otherphone fax email old_email pis oldpis lab oldlab orcid left_field unable_to_contact privacy aka_firstname aka_middlename aka_lastname apu_firstname apu_middlename apu_lastname webpage );
  my @simple_tables = qw( comment );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM two_$table WHERE joinkey = '$two_id';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      $hash{$table}{$row[1]} = $row[2]; } }
  foreach my $table (@simple_tables) {
    $result = $dbh->prepare( "SELECT * FROM two_$table WHERE joinkey = '$two_id';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      $hash{$table}{1} = $row[2]; } }
  print "<table style=\"border-style: none;\" border=\"1\" >";
  print "<tr><td class=\"normal_even\" colspan=\"4\">$two_id</td></tr>\n";
  foreach my $order (sort {$a<=>$b} keys %{ $hash{institution} }) {
    print "<tr><td class=\"normal_even\" colspan=\"1\">institution</td><td class=\"normal_even\" colspan=\"3\">$hash{institution}{$order}</td></tr>\n"; }
#   print "<tr><td class=\"normal_even\">first</td><td class=\"normal_even\">middle</td><td class=\"normal_even\">last</td>\n";
  foreach my $order (sort {$a<=>$b} keys %{ $hash{lastname} }) {
    my ($first, $middle, $last) = ('', '', '');
    if ($hash{firstname}{$order}) { $first = $hash{firstname}{$order}; }
    if ($hash{middlename}{$order}) { $middle = $hash{middlename}{$order}; }
    if ($hash{lastname}{$order}) { $last = $hash{lastname}{$order}; $all_lastnames{$last}++; }
    my $name = "$first $last"; $all_names{$name}++;
    $name = "$last $first"; $all_names{$name}++;
    if ($middle) {
      $name = "$last $first $middle"; $all_names{$name}++;
      $name = "$first $middle $last"; $all_names{$name}++; }
    print "<tr><td class=\"normal_even\">name</td><td class=\"normal_even\">$first</td><td class=\"normal_even\">$middle</td><td class=\"normal_even\">$last</td></tr>\n"; }
  foreach my $order (sort {$a<=>$b} keys %{ $hash{aka_lastname} }) {
    my ($first, $middle, $last) = ('', '', '');
    if ($hash{aka_firstname}{$order}) { $first = $hash{aka_firstname}{$order}; }
    if ($hash{aka_middlename}{$order}) { $middle = $hash{aka_middlename}{$order}; if ($middle eq 'NULL') { $middle = ''; } }
    if ($hash{aka_lastname}{$order}) { $last = $hash{aka_lastname}{$order}; $all_lastnames{$last}++; }
    my $name = "$first $last"; $all_names{$name}++;
    $name = "$last $first"; $all_names{$name}++;
    if ($middle) {
      $name = "$last $first $middle"; $all_names{$name}++;
      $name = "$first $middle $last"; $all_names{$name}++; }
    print "<tr><td class=\"normal_even\">aka</td><td class=\"normal_even\">$first</td><td class=\"normal_even\">$middle</td><td class=\"normal_even\">$last</td></tr>\n"; }
  print "</table>";
  print "<table id=\"table_secondary_data\" style=\"border-style: none; display: none\" border=\"1\" onclick=\"document.getElementById('link_show').style.display = ''; document.getElementById('table_secondary_data').style.display = 'none';\" >";
  foreach my $table (@tables) {
    next if ($shown{$table});
    foreach my $order (sort {$a<=>$b} keys %{ $hash{$table} }) {
      if ($hash{$table}{$order}) {
        my $data = $hash{$table}{$order}; 
        print "<tr><td class=\"normal_even\">$table</td><td class=\"normal_even\">$data</td></tr>\n"; } } }
  print "</table>";
  print "<a href=\"#\" id=\"link_show\" onclick=\"document.getElementById('link_show').style.display = 'none'; document.getElementById('table_secondary_data').style.display = ''; return false\">show</a>"; 
  print "<br /><br />\n";
  my (@lastnames) = sort keys %all_lastnames;
  return (\@lastnames, \%all_names);
} # sub displayPersonInfo




sub getFirstPassTables {
  my $tables = get "http://tazendra.caltech.edu/~postgres/cgi-bin/curator_first_pass.cgi?action=ListPgTables";
  my (@fptables) = $tables =~ m/PGTABLE : (.*)<br/g;
  return \@fptables; }


sub findDeadGenes {	# for Kimberly to find dead genes and update them in the wbpaper editor.  will need to update to point to paper_editor later.  2010 04 09
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"findDeadGenes\">";
  (my $oop, my $curator_id) = &getHtmlVar($query, 'curator_id');		# this is pointless, will be overridden by two10877 for pubmed
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  print "Genes in pap_gene table that are also in gin_dead<br/>\n";
  print "<table border=1>";
  print "<tr><td>WBPaperID</td><td>WBGene</td><td>Evidence</td><td>Dead status</td></tr>\n";
  $result = $dbh->prepare( "SELECT gin_dead.gin_dead, pap_gene.joinkey, pap_gene.pap_gene, pap_gene.pap_evidence, pap_gene.pap_curator FROM pap_gene, gin_dead WHERE pap_gene.pap_gene = gin_dead.joinkey ORDER BY pap_gene.pap_gene, pap_gene.joinkey;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    print "<tr><td><a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?curator_name=$curator_id&number=$row[1]&action=Number+!\" target=\"new\">$row[1]</a></td><td>$row[2]</td><td>$row[3]</td><td>$row[0]</td></tr>\n";
  } # while (my @row = $result->fetchrow)
  print "</table>";
  &printFooter();
} # sub findDeadGenes

sub enterPmids {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"enterPmids\">";
  (my $oop, my $curator_id) = &getHtmlVar($query, 'curator_id');		# this is pointless, will be overridden by two10877 for pubmed
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  my $functional_flag = ''; my $primary_flag = '';
  ($oop, $functional_flag) = &getHtmlVar($query, 'functional_flag');
  ($oop, $primary_flag) = &getHtmlVar($query, 'primary_flag');

  ($oop, my $pmids) = &getHtmlVar($query, 'pmids');
  my (@pmids) = $pmids =~ m/(\d+)/g;
  my @pairs; 
  foreach my $pmid (@pmids) { 
    push @pairs, "$pmid, $primary_flag"; }
  my $list = join"\t", @pairs;

  my ($link_text) = &processXmlIds($curator_id, $functional_flag, $list);
  $link_text =~ s/\n/<br \/>\n/g;
  print "<br/>$link_text<br/>\n";
  $list =~ s/\t/<br \/>/g;
  print "Processed $curator_id $functional_flag<br/>$list.<br/>\n";
  &printFooter();
} # sub enterPmids

sub confirmAbstracts {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"confirmAbstracts\">";
  my $rejected_file = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/rejected_pmids';
  my $removed_file = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/removed_pmids';
  my $directory = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads';
  my ($oop, $count) = &getHtmlVar($query, 'count');
  my @process_list;
  my @move_queue;
  for my $i (0 .. $count - 1) {
    ($oop, my $choice) = &getHtmlVar($query, "approve_reject_$i");
    unless ($choice) { $choice = 'ignore'; }
    ($oop, my $pmid) = &getHtmlVar($query, "pmid_$i");
    print "$pmid $choice<BR>\n";
    if ($choice eq 'reject') {
# UNCOMMENT THESE
        open (OUT, ">>$rejected_file") or die "Cannot append to $rejected_file : $!";
        print OUT "$pmid\n";
        close (OUT) or die "Cannot close $rejected_file : $!";
# print "REJECT<br />\n";
# print "mv ${directory}/xml/$pmid ${directory}/done/<br/>"; 
        `mv -f ${directory}/xml/$pmid ${directory}/done/`; 
      }
      elsif ($choice eq 'remove') {
        open (OUT, ">>$removed_file") or die "Cannot append to $removed_file : $!";
        print OUT "$pmid\n";
        close (OUT) or die "Cannot close $removed_file : $!";
        `mv -f ${directory}/xml/$pmid ${directory}/done/`; 
      }
      elsif ($choice eq 'approve') {
        my $primary_flag = ""; ($oop, $primary_flag) = &getHtmlVar($query, "primary_$i");		
        push @process_list, "$pmid, $primary_flag";
#         my ($link_text) = &processLocal($pmid, $curators{std}{$theHash{curator}}, '');
# no longer move here, approved stuff gets into @process_list and moved by processXmlIds
#         my $move = "mv -f ${directory}/xml/$pmid ${directory}/done/"; 	# need to force move in ubuntu
#         push @move_queue, $move;
      } }
  my $list = join"\t", @process_list;
# print "LIST $list L<br />\n";
  if ($list) {
    ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');		# this is pointless, will be overridden by two10877 for pubmed
    my $functional_flag = '';
#     &processStuff($list);
    my ($link_text) = &processXmlIds($curator_id, $functional_flag, $list);
    $link_text =~ s/\n/<br \/>\n/g;
    print "<br/>$link_text<br/>\n";
    $list =~ s/\t/<br \/>/g;
    print "Processed $curator_id $functional_flag<br/>$list.<br/>\n"; }
#   foreach my $move (@move_queue) { `$move`; }
# print "CREATED<br>\n";
  &printFooter();
} # sub confirmAbstracts

sub enterNewPapers {
  &printHtmlHeader();
  print "<form name='form1' method=\"post\" action=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi\">\n";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"mergePage\">";
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  print "<input type=\"hidden\" name=\"curator_id\" id=\"curator_id\" value=\"$curator_id\">";
  print "You are $curator_id<br />\n";
  &showEnterPmidBox($curator_id);
  &showConfirmXmlTable($curator_id);
  print "</form>\n";
  &printFooter();
}

sub showConfirmXmlTable {
  my ($curator_id) = @_;
  my $directory = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads';
  my $rejected_file = '/home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/rejected_pmids';
  my @read_pmids = <$directory/xml/*>;
  print "<input type=submit name=action value=\"Confirm Abstracts\">\n";
  print "<table border=1>\n";
  print "<tr><td>pmid</td><td>title</td><td>authors</td><td>abstract</td><td>type</td><td>journal</td><td>Approve</td><td>primary</td></tr>\n";
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
    my $input_buttons = "<td><select size=1 name=approve_reject_$count><option></option><option>approve</option><option>reject</option><option>remove</option></select></td>";
    $input_buttons .= "<td><select size=1 name=primary_$count><option></option><option selected=\"selected\" value=\"primary\">primary</option><option value=\"not_primary\">not_primary</option><option value=\"not_designated\">not_designated</option></select></td>\n";
    if ($journal eq 'Genetics') { 
        print "<TR bgcolor='$red'>\n"; 					# show Genetics papers in red	2009 07 21
        if ($doi) { $journal .= "<br />$doi"; } 			# show DOI			2009 07 23
          else { $input_buttons = "<td>&nbsp;</td><td><input type=checkbox name=\"primary_$count\" checked=\"checked\" value=\"primary\"></td><td>&nbsp;</td>"; } } # don't show approve / reject	2009 07 23
      else { print "<TR>\n"; }
    unless ($abstract) { $abstract = ''; }
    unless ($title) { $title = ''; }
    print "<td>$pmid</td><td>$title</td><td>$authors</td><td>$abstract</td>";
    print "<td>$type</td>";
    print "<td>$journal</td>";
    print "<input type=hidden name=pmid_$count value=$pmid>\n";
    print "$input_buttons\n";
    print "</tr>\n";
    $count++;
  } # foreach my $infile (@read_pmids)
  print "</table>\n";
  print "<input type=hidden name=count value=$count>\n";
  print "<input type=submit name=action value=\"Confirm Abstracts\">\n";
} # sub showConfirmXmlTable

sub showEnterPmidBox {
  my ($curator_id) = @_;
  print "<table border=0 cellspacing=2>\n";
  print "<tr><td>Enter the PMID numbers, one per line.  e.g. :<br/>\n";
  print "16061202<br />16055504<br />16055082<br />\n";
  print "<td><textarea name=\"pmids\" rows=6 cols=60 value=\"\"></textarea></td>\n";
  print "<td align=left><input name=\"functional_flag\" type=checkbox value=\"functional_annotation\">functional annotation flag<br /><select size=1 name=\"primary_flag\"><option value=\"\" selected=\"selected\"></option><option value=\"primary\">primary</option><option value=\"not_primary\">not_primary</option><option value=\"not_designated\">not_designated</option></select><br /><input type=\"submit\" name=\"action\" value=\"Enter PMIDs\"></td></tr>\n";
  print "</table>\n";
} # sub showEnterPmidBox

sub deletePostgresTableField {                          # if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/html\n\n";
  my $uid = 'joinkey'; my $sorter = 'pap_order';
  ($oop, my $field) = &getHtmlVar($query, 'field');
  ($oop, my $joinkey) = &getHtmlVar($query, 'joinkey');
  ($oop, my $order) = &getHtmlVar($query, 'order');
  ($oop, my $curator) = &getHtmlVar($query, 'curator');
  my @pgcommands;
  if ($order) { 
      my $command = "DELETE FROM pap_$field WHERE $uid = '$joinkey' AND $sorter = '$order'";
      push @pgcommands, $command;
      $order = "'$order'"; }
    else { 
      my $command = "DELETE FROM pap_$field WHERE $uid = '$joinkey' AND $sorter IS NULL";
      push @pgcommands, $command;
      $order = 'NULL'; }
  my $command = "INSERT INTO h_pap_$field VALUES ('$joinkey', NULL, $order, '$curator')";
  push @pgcommands, $command;
  foreach my $command (@pgcommands) {
#     print "$command<br />\n";
    $result = $dbh->do( $command );
  }
  print "OK";
}

sub movePdfsToMerged {
  my $joinkey = shift;
# TODO  when clicking here, also move the PDFs into some invalid_paper_pdf/ directory  2010 04 08
}

sub updatePostgresTableField {                          # if updating postgres table values, update postgres and return OK if ok
  print "Content-type: text/html\n\n";
  ($oop, my $field) = &getHtmlVar($query, 'field');
  ($oop, my $joinkey) = &getHtmlVar($query, 'joinkey');
  ($oop, my $order) = &getHtmlVar($query, 'order');
  ($oop, my $curator) = &getHtmlVar($query, 'curator');
  ($oop, my $newValue) = &getHtmlVar($query, 'newValue');
  ($oop, my $evi) = &getHtmlVar($query, 'evi');
  ($newValue) = &filterForPg($newValue);                  # replace ' with ''

  my $isOk = 'NO';

    # if identifier field is acquiring a WBPaperId (exactly 8 digits only), move the PDFs to some merged directory
  if ($field eq 'identifier') {	if ($newValue =~ m/^\d{8}$/) { &movePdfsToMerged($newValue); } }

  if ($field eq 'author_reorder') {	# author order data is special if re-ordering
      ($isOk) = &updatePostgresAuthorReorderField('author', $joinkey, $order, $curator, $newValue); }
    elsif ($field eq 'author_new')  {	# author field data is special	
      ($isOk) = &updatePostgresAuthorNewvalueField('author', $joinkey, $order, $curator, $newValue); }
    elsif ($field eq 'gene')  {		# gene data is special
      if ($evi) {
        ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $joinkey, $order, $curator, $newValue, $evi); }
      elsif ($newValue =~ m/\(WBGene\d+\)/) {
        ($isOk) = &updatePostgresGeneBatchField($field, $joinkey, $order, $curator, $newValue); }
      else {
        ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $joinkey, $order, $curator, ''); } }
    elsif ($field eq 'status')  {	# status can only delete whole paper
      ($isOk) = &deletePaper($joinkey, $curator); }
    elsif ($field eq 'author_possible')  {		# convert AutoComplete value to two#
      ($isOk) = &updatePostgresAuthorPossibleField($field, $joinkey, $order, $curator, $newValue); }
    elsif ($field eq 'author_index')  {			# if change, change author_index, if delete, remove all existence of author_id
      ($isOk) = &updatePostgresAuthorIndexField($field, $joinkey, $order, $curator, $newValue); }
    elsif ( ($field eq 'curation_flags') && ($newValue eq 'rnai_curation') && ($order eq 'new') ) {	# get order and only change if new flag
      ($isOk) = &updatePostgresRnaiCuration($field, $joinkey, $order, $curator, $newValue); }
    else {						# normal fields
      ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $joinkey, $order, $curator, $newValue); }

  if ($isOk eq 'OK') { print "OK"; }
} # sub updatePostgresTableField

sub updatePostgresByTableJoinkeyNewvalue {
  my ($field, $joinkey, $order, $curator, $newValue, $evi) = @_;
# print "F $field J $joinkey O $order C $curator N $newValue E $evi E<br/>\n";
  my $uid = 'joinkey'; my $sorter = 'pap_order';
  if ($field =~ m/author_/) { $uid = 'author_id'; $sorter = 'pap_join'; }
  my @pgcommands;
  if ($order) { 
      my $command = "DELETE FROM pap_$field WHERE $uid = '$joinkey' AND $sorter = '$order'";
      push @pgcommands, $command;
      $order = "'$order'"; } 
    else { 
      my $command = "DELETE FROM pap_$field WHERE $uid = '$joinkey' AND $sorter IS NULL";
      push @pgcommands, $command;
      $order = 'NULL'; }

  if ($newValue) { $newValue = "'$newValue'"; }
    else { $newValue = 'NULL'; }

  my $command = "INSERT INTO h_pap_$field VALUES ('$joinkey', $newValue, $order, '$curator', CURRENT_TIMESTAMP)";
  if ($evi) { 
    if ($evi eq 'merge') { $evi = 'NULL'; } else { $evi = "'$evi'"; $evi =~ s/ESCTAB/\t/g; }	# tabs don't get passed by html/javascript for some reason
    $command = "INSERT INTO h_pap_$field VALUES ('$joinkey', $newValue, $order, '$curator', CURRENT_TIMESTAMP, $evi )"; }
  push @pgcommands, $command;

  if ($newValue ne 'NULL') {
    $command = "INSERT INTO pap_$field VALUES ('$joinkey', $newValue, $order, '$curator', CURRENT_TIMESTAMP)";
    if ($evi) { 
      $command = "INSERT INTO pap_$field VALUES ('$joinkey', $newValue, $order, '$curator', CURRENT_TIMESTAMP, $evi )"; }
    push @pgcommands, $command;  }

  foreach my $command (@pgcommands) {
#     print "$command<br />\n";
    $result = $dbh->do( $command );
  }

#   print "INSERT INTO pap_$field VALUES ('$joinkey', $order, '$curator', '$newValue')<br>" ;
#   my $result = $dbh->do( "INSERT INTO oa_test VALUES ('$joinkey', '$table', '$newValue')" );  # test entering in oa_test table

#   my $result = $dbh->do( "INSERT INTO ${table}_hst VALUES ('$joinkey', '$newValue')" );
#   $result = $dbh->do( "DELETE FROM $table WHERE joinkey = '$joinkey'" );
#   $result = $dbh->do( "INSERT INTO $table VALUES ('$joinkey', '$newValue')" );
  return "OK";
} # sub updatePostgresByTableJoinkeyNewvalue

sub deletePaper {				# to delete a paper by joinkey and curator
  my ($joinkey, $curator) = @_;
  my @pgcommands;
#   $result = $dbh->do( "INSERT INTO pap_status VALUES ('$joinkey', 'invalid', NULL, '$curator')" );
  my $command = "INSERT INTO pap_status VALUES ('$joinkey', 'invalid', NULL, '$curator')" ;
  push @pgcommands, $command;
  my %aids;					# author_ids to potentially delete if not associated with another paper
  foreach my $table (@normal_tables) {
    my $pg_table = 'pap_' . $table; 
    $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY pap_order" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);				# skip blank entries
      my $new_value = 'NULL'; if ($table eq 'status') { $new_value = "'invalid'"; }
      my $order = 'NULL'; my $check_order = 'IS NULL';
      if ($multi{$table}) { $order = "'$row[2]'"; $check_order = "= '$row[2]'"; }
      $command = "INSERT INTO h_${pg_table} VALUES ('$joinkey', $new_value, $order, '$curator')";
      push @pgcommands, $command;
      $command = "DELETE FROM ${pg_table} WHERE joinkey = '$joinkey' AND pap_order $check_order";
      push @pgcommands, $command;
      if ($table eq 'author') { $aids{$row[1]}++; } } }

  foreach my $aid (sort {$a<=>$b} keys %aids) {		# for each author_id in pap_author, check that the author_id doesn't exist in another paper.  if it exists is another paper, remove from %aids, which will delete all pap_author_<stuff> entries for it
    $result = $dbh->prepare( "SELECT * FROM pap_author WHERE joinkey != '$joinkey' AND pap_author = '$aid'" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my @row = $result->fetchrow(); 
    if ($row[0]) { delete $aids{$aid}; } }		# remove from %aids since it exists for another paper
 
  my @aut_tables = qw( author_index author_possible author_sent author_verified );
  foreach my $aid (sort {$a<=>$b} keys %aids) {		# delete from author subtables 
    foreach my $table (@aut_tables) {
      my $pg_table = 'pap_' . $table; 
      $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE author_id = '$aid' ORDER BY pap_join" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) {
        next unless ($row[1]);				# skip blank entries
        my $join = 'NULL'; my $check_join = 'IS NULL';
        if ($multi{$table}) { $join = "'$row[2]'"; $check_join = "= '$row[2]'"; }
        $command = "INSERT INTO h_${pg_table} VALUES ('$aid', NULL, $join, '$curator')";
        push @pgcommands, $command;
        $command = "DELETE FROM ${pg_table} WHERE author_id = '$aid' AND pap_join $check_join";
        push @pgcommands, $command; } } }

  $command = "INSERT INTO pap_status VALUES ('$joinkey', 'invalid', NULL, '$curator')";
  push @pgcommands, $command;				# add an invalid status to the pap_status table

  foreach my $command (@pgcommands) {
#     print "$command<br />\n";
    $result = $dbh->do( $command );
  }
  return "OK";
} # sub deletePaper


sub updatePostgresRnaiCuration {
  my ($field, $joinkey, $order, $curator, $newValue) = @_;
  my $isOk = 'OK';
  my $result = $dbh->prepare( "SELECT * FROM pap_$field WHERE pap_$field = '$newValue' AND joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); if ($row[1]) { return $isOk; }		# value already in, leave it alone
  if ($order eq 'new') {
    my $result = $dbh->prepare( "SELECT * FROM pap_$field WHERE pap_order IS NOT NULL AND joinkey = '$joinkey' ORDER BY pap_order DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my @row = $result->fetchrow(); $order = $row[2] + 1; }
  ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $joinkey, $order, $curator, $newValue);
  return $isOk;
} # sub updatePostgresRnaiCuration

sub updatePostgresGeneBatchField {		# batch genes, normal
  my ($field, $joinkey, $order, $curator, $newValue) = @_;
  my $curator_evidence = $curator; $curator_evidence =~ s/two/WBPerson/;		# store WBPerson in evidence
  my @pgcommands;				# commands for postgres
  my $published_as = '';
  if ($newValue =~ m/ Published_as (.*)$/) { $published_as = $1; }
  my @genes = split/, /, $newValue;		# split values by comma and space
  foreach my $genePair (@genes) {
    my ($name, $wbgene) = $genePair =~ m/^(.*?) \(WBGene(\d+)\)/;	# get the matched name, and the wbgene's ID
    my $command = "INSERT INTO h_pap_gene VALUES ('$joinkey', '$wbgene', '$order', '$curator', CURRENT_TIMESTAMP, 'Curator_confirmed\t\"$curator_evidence\"')";
    push @pgcommands, $command;
    $command = "INSERT INTO pap_gene VALUES ('$joinkey', '$wbgene', '$order', '$curator', CURRENT_TIMESTAMP, 'Curator_confirmed\t\"$curator_evidence\"')";
    push @pgcommands, $command;
    $order++;					# different evidence, so update the order
    $command = "INSERT INTO pap_gene VALUES ('$joinkey', '$wbgene', '$order', '$curator', CURRENT_TIMESTAMP, 'Manually_connected\t\"$name\"')";
    push @pgcommands, $command;
    $command = "INSERT INTO h_pap_gene VALUES ('$joinkey', '$wbgene', '$order', '$curator', CURRENT_TIMESTAMP, 'Manually_connected\t\"$name\"')";
    push @pgcommands, $command;
    $order++;					# multiple genes, so update the order
    if ($published_as) {			# has published_as evidence, make new entry
      $command = "INSERT INTO pap_gene VALUES ('$joinkey', '$wbgene', '$order', '$curator', CURRENT_TIMESTAMP, 'Published_as\t\"$published_as\"')";
      push @pgcommands, $command;
      $command = "INSERT INTO h_pap_gene VALUES ('$joinkey', '$wbgene', '$order', '$curator', CURRENT_TIMESTAMP, 'Published_as\t\"$published_as\"')";
      push @pgcommands, $command;
      $order++; }				# additional entry for published_as
  }
  foreach my $command (@pgcommands) { $result = $dbh->do( $command ); }
  return 'OK';
}

sub updatePostgresAuthorIndexField {

  my ($field, $aid, $order, $curator, $newValue) = @_;
  my $isOk = 'OK';
  if ($newValue) { ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $aid, $order, $curator, $newValue); }
    else {			# there's no new value, it's a delete, remove author_id from pap_author and all subtables
      &updatePostgresByTableJoinkeyNewvalue($field, $aid, $order, $curator, '');
      my $result2 = $dbh->prepare( "SELECT * FROM pap_author WHERE pap_author = '$aid'" );
      $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row2 = $result2->fetchrow) {
        &updatePostgresByTableJoinkeyNewvalue('author', $row2[0], $row2[2], $curator, ''); }
      $result2 = $dbh->prepare( "SELECT * FROM pap_author_possible WHERE author_id = '$aid'" );
      $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row2 = $result2->fetchrow) {
        my $aid = $row2[0]; my $order = $row2[2];	# need to assign variables because @row2 would change before second updatePostgresByTableJoinkeyNewvalue  2011 04 48
        &updatePostgresByTableJoinkeyNewvalue('author_possible', $aid, $order, $curator, '');
        &updatePostgresByTableJoinkeyNewvalue('author_sent', $aid, $order, $curator, '');
        &updatePostgresByTableJoinkeyNewvalue('author_verified', $aid, $order, $curator, ''); }
    }
  return $isOk;
} # sub updatePostgresAuthorIndexField
sub updatePostgresAuthorPossibleField {
  my ($field, $aid, $order, $curator, $newValue) = @_;
  my $isOk = 'OK';
  if ( ($newValue eq '') && ($order =~ m/^\d+$/) ) {	# blank and has order, so blank it
      ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $aid, $order, $curator, $newValue); }
    elsif ($newValue =~ m/WBPerson(\d+)/) { 
      if ($order eq 'new') {
        my $result = $dbh->prepare( "SELECT pap_join FROM pap_author_possible WHERE pap_join IS NOT NULL AND author_id = '$aid' ORDER BY pap_join DESC;" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
        my @row = $result->fetchrow(); $order = $row[0] + 1; }
      $newValue = 'two' . $1;		# convert to two#
      ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $aid, $order, $curator, $newValue); }
    elsif ($newValue =~ m/^two\d+$/) { 			# direct update of two# from connecting by paper person author group
      ($isOk) = &updatePostgresByTableJoinkeyNewvalue($field, $aid, $order, $curator, $newValue); }
    else { 1; } 			# no matching WBPerson value, don't do anything
  return $isOk;
} # sub updatePostgresAuthorPossibleField

sub updatePostgresAuthorNewvalueField {
  my ($field, $joinkey, $order, $curator, $newValue) = @_;
  my @pgcommands;
  my $result = $dbh->prepare( "SELECT pap_author FROM pap_author ORDER BY CAST (pap_author AS integer) DESC" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); my $highest_aid = $row[0];
  my $aid = $highest_aid + 1;
  my $command = "INSERT INTO h_pap_author VALUES ('$joinkey', '$aid', '$order', '$curator')";
  push @pgcommands, $command;
  $command = "INSERT INTO pap_author VALUES ('$joinkey', '$aid', '$order', '$curator')";
  push @pgcommands, $command;
  $command = "INSERT INTO h_pap_author_index VALUES ('$aid', '$newValue', NULL, '$curator')";
  push @pgcommands, $command;
  $command = "INSERT INTO pap_author_index VALUES ('$aid', '$newValue', NULL, '$curator')";
  push @pgcommands, $command;
  foreach my $command (@pgcommands) { $result = $dbh->do( $command ); }
  return 'OK';  
} # sub updatePostgresAuthorNewvalueField

sub updatePostgresAuthorReorderField {		# author field deletes all current values, updates values of current and history tables up to the highest order on current record, entering NULL in history for blank entries
  my ($field, $joinkey, $order, $curator, $newValue) = @_;
  my @pgcommands;
  my $result = $dbh->prepare( "SELECT pap_order FROM pap_author WHERE joinkey = '$joinkey' ORDER BY pap_order DESC" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); my $highest_order = $row[0];
  my (@author_order) = split/_TAB_/, $newValue;
  my $command = "DELETE FROM pap_$field WHERE joinkey = '$joinkey'";	# delete all authors
  push @pgcommands, $command;
  for my $order (1 .. $highest_order ) {
    my $i = $order - 1;
    my $author_value = 'NULL';
    if ($author_order[$i]) { $author_value = "'$author_order[$i]'"; }
#     print "$order\t$author_value<br />\n";
    $command = "INSERT INTO h_pap_$field VALUES ('$joinkey', $author_value, '$order', '$curator')";
    push @pgcommands, $command;
    if ($author_order[$i]) {				# only insert to current table if there are values
      $command = "INSERT INTO pap_$field VALUES ('$joinkey', $author_value, '$order', '$curator')";
      push @pgcommands, $command; } }
  foreach my $command (@pgcommands) { $result = $dbh->do( $command ); }
  return 'OK';  
} # sub updatePostgresAuthorReorderField 


# sub makeAuthorInputField {
#   my ($current_value, $table, $aid, $join, $curator_id, $colspan, $rowspan, $class) = @_;
#   # the $order here is usually the pap_order value of a normal table, but it's the author_id of an author_<stuff> table to server as a unique identifier for the html ids
# #   my $div_display = ""; my $input_display = "none";
# #   if ($current_value eq "NEW") { $div_display = "none"; $input_display = ""; $current_value = ''; }
#   my $data = "<td class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\" onclick=\"toggleDivToInput('$table', '$order')\">
#   <input style=\"display: none\" size=\"40\" id=\"input_${table}_$order\" name=\"input_${table}_$order\" value=\"$current_value\" onblur=\"toggleInputToDiv('$table', '$joinkey', '$order', '$curator_id')\">
#   <div id=\"div_${table}_$order\" name=\"div_${table}_$order\" >$current_value</div></td>";
#   return $data;
# } # sub makeAuthorInputField

sub makeInputField {
  my ($current_value, $table, $joinkey, $order, $curator_id, $colspan, $rowspan, $class) = @_;
  # the $order here is usually the pap_order value of a normal table, but it's the author_id of an author_<stuff> table to server as a unique identifier for the html ids
#   my $div_display = ""; my $input_display = "none";
#   if ($current_value eq "NEW") { $div_display = "none"; $input_display = ""; $current_value = ''; }
  my $data = "<td class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\" onclick=\"toggleDivToInput('$table', '$joinkey', '$order')\">
  <input style=\"display: none\" size=\"40\" id=\"input_${table}_${joinkey}_$order\" name=\"input_${table}_${joinkey}_$order\" value=\"$current_value\" onblur=\"toggleInputToDiv('$table', '$joinkey', '$order', '$curator_id')\">
  <div id=\"div_${table}_${joinkey}_$order\" name=\"div_${table}_${joinkey}_$order\" >$current_value</div></td>";
  return $data;
} # sub makeInputField


#   print "<tr><td colspan=5><div id=\"forcedPersonAutoComplete\">
#         <input id=\"forcedPersonInput\" type=\"text\">
#         <div id=\"forcedPersonContainer\"></div></div></td></tr>";
#       var forcedOAC = new YAHOO.widget.AutoComplete("forcedPersonInput", "forcedPersonContainer", oDS);


sub makeOntologyField {
  my ($current_value, $table, $joinkey, $order, $curator_id, $colspan, $rowspan, $class) = @_;
  my $div_value = $current_value; my $input_value = $current_value;
  my $freeForced = 'forced';
  my $input_id = "input_${table}_${joinkey}_$order";
# in div_table_joinkey_order  make current value something that will match dropdown
  if ( $curators{two}{$current_value} ) { 
    my ($num) = $current_value =~ m/(\d+)/;
    $div_value =  "$curators{two}{$current_value} ( WBPerson$num )";
    $input_value =  "$curators{two}{$current_value}"; } 

  my $data = "<td id=\"td_display_$input_id\" class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\" onclick=\"toggleDivToSpanInput('$table', '$joinkey', '$order')\">

  <div id=\"div_${table}_${joinkey}_$order\" name=\"div_${table}_${joinkey}_$order\" >$div_value</div></td>

  <td id=\"td_AutoComplete_$input_id\" class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\" style=\"display: none\" width=\"400\">
  <div id=\"div_AutoComplete_$input_id\" class=\"div-autocomplete\">
  <input size=\"40\" id=\"$input_id\" name=\"$input_id\" value=\"$input_value\" onblur=\"toggleAcInputToTd('$table', '$joinkey', '$order', '$curator_id')\">
  <div id=\"div_Container_$input_id\"></div></div></td>";

  return ($input_id, $data);
#   <input id=\"input_$table\" name=\"input_$table\" size=\"40\">
} # sub makeOntologyField

sub makeToggleTripleField {
  my ($current_value, $table, $joinkey, $order, $curator_id, $colspan, $rowspan, $class, $one, $two, $three) = @_;
  my $data = "<td class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\" onclick=\"toggleDivTripleToggle('$table', '$joinkey', '$order', '$curator_id', '$one', '$two', '$three')\">
  <div id=\"div_${table}_${joinkey}_$order\" name=\"div_${table}_${joinkey}_$order\" >$current_value</div></td>";
  return $data;
} # sub makeToggleTripleField

sub makeUneditableField {
  my ($current_value, $table, $joinkey, $order, $curator_id, $colspan, $rowspan, $class) = @_;
  my $data = "<td class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\">
  <div id=\"div_${table}_${joinkey}_$order\" name=\"div_${table}_${joinkey}_$order\" >$current_value</div></td>";
  return $data;
} # sub makeUneditableField


# for new genes, two types
# published_as, which when clicked gives input for published_as evidence, then click out give box for locus / gene, then click out to convert into blue row, and clear published_as field
# 3 rows per gene, curator_confirmed, manually_connected, published_as
# batch genes, which when clicked gives textarea, enter lots of loci, show what they match to like curation_FP form genestudied field.  when click out convert each into blue row, clear batch genes.  
# 2 rows per gene, curator_confirmed, manually_connected
sub makeGeneDeleteField {			# for deleting genes, has evidence
  # add confirmation button here TODO  ( or maybe not ? seems good as is  -- 2010 03 26)
  my ($current_value, $table, $joinkey, $order, $curator_id, $evidence) = @_;
  my $name = &getGeneName($current_value);
#   my $data = "<td><input onclick=\"deletePostgresTableField('$table', '$order', '$curator_id'); this.parentNode.parentNode.style.display='none'\" type=\"button\" value=\"delete\" ></td><td>$current_value ( $name )</td><td>$evidence</td>"; 	# replaced deletePostgresTableField with updatePostgresTableField to blank value
  my $data = "<td><input onclick=\"updatePostgresTableField('$table', '$joinkey', '$order', '$curator_id', ''); this.parentNode.parentNode.style.display='none'\" type=\"button\" value=\"delete\" ></td><td>$current_value ( $name )</td><td>$evidence</td>"; 
  return $data;
} # sub makeGeneDeleteField

sub getGeneName {
  my ($current_value) = @_;
  my $name = '';
  my $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$current_value'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); $name = $row[1];
  unless ($name) {
    my $result = $dbh->prepare( "SELECT * FROM gin_sequence WHERE joinkey = '$current_value'" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my @row = $result->fetchrow(); $name = $row[1]; }
  return $name;
} # sub getGeneName

sub getGeneDisplay {
  my ($display_data, $evi) = @_;
  my $name = &getGeneName($display_data); 
  $display_data = "<td>$display_data ( $name )</td><td>$evi</td>";
  return $display_data;
} # sub getGeneDisplay

sub makeGeneTextareaField {		# to enter new genes.  gene textarea field has extra div_gene_display field for now
  my ($current_value, $table, $joinkey, $order, $curator_id, $rows, $cols) = @_;
  my $data = "<td colspan=\"3\" onclick=\"toggleDivToTextarea('$table', '$joinkey', '$order')\">
  <textarea style=\"display: none\" rows=\"$rows\" cols=\"$cols\" id=\"textarea_${table}_$order\" name=\"textarea_${table}_$order\" onKeyUp=\"matchGeneTextarea('$order', 'batch')\" onblur=\"toggleGeneTextareaToDiv('$table', '$joinkey', '$order', '$curator_id')\">$current_value</textarea>
  <div id=\"div_gene_display\" name=\"div_gene_display\"></div>
  <div id=\"div_${table}_$order\" name=\"div_${table}_$order\" >$current_value</div></td>";
  return $data;
} # sub makeGeneTextareaField

sub makeGeneEvidenceField {		# to enter evidence and new genes.  gene evidence field + autocomplete
  my ($current_value, $table, $joinkey, $order, $curator_id, $colspan, $rowspan, $class) = @_;
  my $warning = "<div style=\"color:red\">Are you sure you know how this works ?  If not confirm with Kimberly, if so tell Juancarlos to get rid of this warning.</div><br />\n";
  if ( ($curator_id eq 'two1843') || ($curator_id eq 'two1823') ) { $warning = ''; }	# clear warning for Kimberly and me
  my $data = "
  <td id=\"td_gene_placeholder\" class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\" onclick=\"toggleTdToGeneEvi('$table', '$joinkey', '$order')\"></td>
  <td id=\"td_gene_info\" style=\"display: none\" class=\"$class\" rowspan=\"$rowspan\" colspan=\"$colspan\">
    $warning
    Published_as :
    <input size=\"40\" id=\"input_published_as\" name=\"input_published_as\" value=\"\" onblur=\"verifyEviFocusOnGene('$table', '$joinkey', '$order', '$curator_id')\"><br />
    Gene (or genes if all have the same Published_as evidence) :<br />
    <textarea rows=\"2\" cols=\"40\" id=\"textarea_evi_${table}_$order\" name=\"textarea_evi_${table}_$order\" onKeyUp=\"matchGeneTextarea('$order', 'evi')\" onblur=\"geneEviToDiv('$table', '$joinkey', '$order', '$curator_id')\">$current_value</textarea>
    <div id=\"div_evi_gene_display\" name=\"div_evi_gene_display\"></div>
    <div id=\"display_div_${table}_${joinkey}_$order\" name=\"display_div_${table}_${joinkey}_$order\" >$current_value</div>
  </td>";
  return $data;
} # sub makeGeneEvidenceField 



sub makeStatusField {			# to delete papers
  my ($current_value, $table, $joinkey, $order, $curator_id) = @_;
#   my $data = "<td colspan=\"3\">$current_value <input onclick=\"alert('$table', '$order')\" type=\"button\" value=\"make invalid\"></td>"; 
  my $data = "<td colspan=\"3\">$current_value <input onclick=\"confirmInvalid('$joinkey')\" type=\"button\" value=\"make invalid\"></td>"; 
  return $data;
}


sub makeTextareaField {
  my ($current_value, $table, $joinkey, $order, $curator_id, $rows, $cols) = @_;
  my $data = "<td colspan=\"3\" onclick=\"toggleDivToTextarea('$table', '$joinkey', '$order')\">
  <textarea style=\"display: none\" rows=\"$rows\" cols=\"$cols\" id=\"textarea_${table}_$order\" name=\"textarea_${table}_$order\" onblur=\"toggleTextareaToDiv('$table', '$joinkey', '$order', '$curator_id')\">$current_value</textarea>
  <div id=\"div_${table}_$order\" name=\"div_${table}_$order\" >$current_value</div></td>";
  return $data;
}

sub displayMerge {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"mergePage\">";
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  ($oop, my $acquires_joinkey) = &getHtmlVar($query, 'joinkey');
  ($oop, my $merge_into) = &getHtmlVar($query, 'merge_into');
  my $merge_joinkey = $merge_into;
  if ($merge_into =~ m/(\d+)/) { $merge_joinkey = &padZeros($1); }
  print "C $curator_id J $acquires_joinkey acquires $merge_joinkey <br />\n";
  my %data;
  foreach my $joinkey ($acquires_joinkey, $merge_joinkey) {
    foreach my $table (@normal_tables) {
      $result = $dbh->prepare( "SELECT * FROM pap_$table WHERE joinkey = '$joinkey' ORDER BY pap_order" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) {
        my ($pg_joinkey, $data, $order, $curator, $timestamp, $evi) = @row;
        $data{$table}{$joinkey}{$order}{data} = $data;
        $data{$table}{$joinkey}{$order}{curator} = $curator;
        $data{$table}{$joinkey}{$order}{timestamp} = $timestamp;
        if ($table eq 'gene') { $data{$table}{$joinkey}{$order}{evi} = $evi; }
      }
    } # foreach my $table (@normal_tables)
  } # foreach my $joinkey ($acquires_joinkey, $merge_joinkey)
  my $identifier_highest_order = 0;
  print "<table border=0>\n";
  foreach my $table (@normal_tables) {
    next if ($table eq 'electronic_path');	# skip this for now
    my @data_trs;
    my $original_highest_order = 0;
    foreach my $joinkey ($acquires_joinkey, $merge_joinkey) {
      my $bgcolor = 'white'; my $td_button = "<td></td>";
      if ($curator_id eq 'two1843') { $td_button = "<td>$acquires_joinkey</td><td></td>"; }

      foreach my $order (sort { $a<=>$b } keys %{ $data{$table}{$joinkey} }) {
        my $jsevi = 'merge'; my $evi = '';
        if ($data{$table}{$joinkey}{$order}{evi}) { 
          $evi = $data{$table}{$joinkey}{$order}{evi};
          $jsevi = $data{$table}{$joinkey}{$order}{evi}; $jsevi =~ s/"/&quot;/g; $jsevi =~ s/\t/ESCTAB/g; }	# tabs don't get passed for some reason

        my $data = $data{$table}{$joinkey}{$order}{data};
        my $curator = $data{$table}{$joinkey}{$order}{curator};
        my $timestamp = $data{$table}{$joinkey}{$order}{timestamp}; $timestamp =~ s/\.[\d\-]+$//;
        if ($joinkey eq $acquires_joinkey) {
          if ($table eq 'identifier') { $identifier_highest_order = $order + 1; }	# get highest order of identifier for final merge
          $original_highest_order = $order + 1; }	# get highest order
        if ($joinkey eq $merge_joinkey) {
          $bgcolor = '#ffbbbb'; 
          $td_button = "<td onclick=\"updatePostgresTableField(\'$table\', \'$acquires_joinkey\', \'\', \'$curator_id\', \'$data\'); updatePostgresTableField(\'$table\', \'$merge_joinkey\', \'\', \'$curator_id\', \'\')\">replace</td>";
          if ($multi{$table}) {
            $td_button = "<td onclick=\"updatePostgresTableField(\'$table\', \'$acquires_joinkey\', \'$original_highest_order\', \'$curator_id\', \'$data\'); updatePostgresTableField(\'$table\', \'$merge_joinkey\', \'$order\', \'$curator_id\', \'\')\">merge</td>"; 
            if ($table eq 'gene') {
              $td_button = "<td onclick=\"updatePostgresTableField(\'$table\', \'$acquires_joinkey\', \'$original_highest_order\', \'$curator_id\', \'$data\', \'$jsevi\'); updatePostgresTableField(\'$table\', \'$merge_joinkey\', \'$order\', \'$curator_id\', \'\')\">merge</td>"; } 
} }
        if ($curator_id eq 'two1843') { $td_button = "<td>$merge_joinkey</td>" . $td_button; }
        my $td_display_data = "<td colspan=\"2\">$data</td>";
        if ($table eq 'author') { $td_display_data = &getAidDataForDisplay($data); }
        elsif ($table eq 'type') { $td_display_data = "<td colspan=\"2\">$type_index{$data}</td>"; }
        elsif ($table eq 'gene') { $td_display_data = &getGeneDisplay($data, $evi); } 
        push @data_trs, "<tr bgcolor='$bgcolor'>${td_button}${td_display_data}<td>$order</td><td>$curator</td><td style=\"width:11em\">$timestamp</td></tr>\n";
      } # foreach my $order (sort { $a<=>$b } keys %{ $data{$table}{$joinkey} })
    } # foreach my $joinkey ($acquires_joinkey, $merge_joinkey)
    if ($data_trs[0]) {
      print "<tr bgcolor='#dddddd'><td colspan=7 align=\"center\">$table</td></tr>\n"; 
      foreach my $data_tr (@data_trs) { print "$data_tr"; } }
  } # foreach my $table (@normal_tables)
  print "</table>\n";
  print "<hr/><input type=\"button\" onclick=\"updatePostgresTableField(\'identifier\', \'$acquires_joinkey\', \'$identifier_highest_order\', \'$curator_id\', \'$merge_joinkey\', \'\', \'http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=two1823&action=Search&data_number=$merge_joinkey\');\" value=\"merge WBPaper$merge_into into pap_identifier of WBPaper$acquires_joinkey and review WBPaper$merge_joinkey for deletion\">";
# my $identifier_highest_order = 0;
  &printFooter();
} # sub displayMerge

sub getAidDataForDisplay {
  my $aid = shift;
  my $result2 = $dbh->prepare( "SELECT * FROM pap_author_index WHERE author_id = '$aid'" );
  $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row2 = $result2->fetchrow(); my $name = $row2[1];
  
  my %aid_data;
  my @aut_tables = qw( possible sent verified );
  foreach my $table (@aut_tables) {
    $result = $dbh->prepare( "SELECT * FROM pap_author_$table WHERE author_id = '$aid';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      $aid_data{$row[2]}{$table}{time} = $row[4]; 
      $aid_data{$row[2]}{$table}{data} = $row[1]; } }

  my @entries;
  foreach my $join (sort {$a<=>$b} keys %aid_data ) {
    my $possible = ''; my $pos_time = ''; my $sent = ''; my $verified = ''; my $ver_time = '';
    if ($aid_data{$join}{possible}{data}) { $possible = $aid_data{$join}{possible}{data}; }
    if ($aid_data{$join}{possible}{time}) { $pos_time = $aid_data{$join}{possible}{time}; $pos_time =~ s/ [\:\.\d\-]+$//; }
    if ($aid_data{$join}{sent}{data}) { $sent = $aid_data{$join}{sent}{data}; }
    if ($aid_data{$join}{verified}{data}) { $verified = $aid_data{$join}{verified}{data}; }
    if ($aid_data{$join}{verified}{time}) { $ver_time = $aid_data{$join}{verified}{time}; $ver_time =~ s/ [\:\.[\d\-]+$//; }
    my $entry = "<td class=\"normal_even\">$join</td><td class=\"normal_even\">$possible</td><td class=\"normal_even\">$pos_time</td><td class=\"normal_even\">$sent</td><td class=\"normal_even\">$verified</td><td class=\"normal_even\">$ver_time</td>";
    push @entries, $entry; }

  my $lines_count = scalar(@entries); my $first_entry = shift @entries; 
  my $display_data = "<table style=\"border-style: none;\" border=\"1\" ><tr bgcolor='$blue'><td rowspan=\"$lines_count\" class=\"normal_even\">$aid</td><td rowspan=\"$lines_count\" class=\"normal_even\">$name</td>$first_entry</tr>";
  foreach my $entry (@entries) { $display_data .= "<tr>$entry</tr>\n"; }
  $display_data .= "</table>";

  return "<td colspan=\"2\">$display_data</td>";
} # sub getAidDataForDisplay

sub displayNumber {
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"displayNumber\">";
#   my ($joinkey, $history) = @_;
  my ($joinkey, $curator_id) = @_;
  print "<input type=\"hidden\" name=\"paper_joinkey\" id=\"paper_joinkey\" value=\"$joinkey\">";
  print "<input type=\"hidden\" name=\"curator_id\" id=\"curator_id\" value=\"$curator_id\">";
  my @authors; my %aid_data; my %author_list;
  my %display_data;
  my $header_bgcolor = '#dddddd'; my $header_color = 'black';
  if ($curator_id eq 'two1843') { $header_bgcolor = '#aaaaaa'; $header_color = 'white'; }

#   print "<tr bgcolor='#aaaaaa'><td colspan=5><div style=\"color:white\">Publication Information</div></td></tr>\n";
#   foreach my $table (@normal_tables, "electronic_path") { # }
  foreach my $table (@normal_tables) {
    my $entry_data;
    if ($table eq 'gene') { $entry_data .= "<tr bgcolor='$header_bgcolor'><td colspan=7><div style=\"color:$header_color\">Genes and Curation Flags</div></td></tr>\n"; }
    elsif ($table eq 'status') { $entry_data .= "<tr bgcolor='$header_bgcolor'><td colspan=7><div style=\"color:$header_color\">Publication Information</div></td></tr>\n"; }
    my $table_has_data = 0;
    my $highest_order = 0;
    my $pg_table = 'pap_' . $table; 
#     if ($history eq 'on') { $pg_table = 'h_pap_' . $table; }
#     print "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY pap_order<br />\n" ;
    $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY pap_order" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      $row[0] = $table;
#       if ($table eq 'type') { $row[1] = $type_index{$row[1]}; }
#       if ($table eq 'type') { 
#           ($row[1]) = &makeTypeSelect($row[1], $table, $joinkey, $order, $curator_id); }
      next unless ($row[1]);				# skip blank entries
      $table_has_data++; 				# set flag that there was data
      shift @row;					# don't store joinkey
      my $data = shift @row; my $td_data = $data;
      my $order = shift @row; unless ($order) { $order = ''; }
      if ($multi{$table}) { if ($order > $highest_order) { $highest_order = $order; } }	# get the highest order if in %multi 
      my $row_curator = shift @row;
      my $timestamp = shift @row; $timestamp =~ s/\.[\d\-]+$//;

      if ($table eq 'pubmed_final') { 
          $td_data = "<td colspan=\"3\">$data</td>"; }	# display as is
        elsif ($table eq 'electronic_path') {
          my ($pdf) = $data =~ m/\/([^\/]*)$/;
          $pdf = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
          $td_data = "<td colspan=\"3\"><a href=\"$pdf\">$pdf</a></td>\n"; }
# This is replaced by makeGeneDeleteField
#         elsif ($table eq 'gene') { 
#           my $name = '';
#           my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$data'" );
#           $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#           my @row2 = $result2->fetchrow(); $name = $row[2];
#           $td_data = "WBGene$data ($row2[1])"; }
        elsif ($table eq 'author') { 
          push @authors, $data;
          my $result2 = $dbh->prepare( "SELECT * FROM pap_author_index WHERE author_id = '$data'" );
          $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
          my @row2 = $result2->fetchrow();
          $aid_data{$data}{index} = $row2[1]; 
#           $data .= " ($row2[1])"; 
          $author_list{$order}{name} = $row2[1];
          $author_list{$order}{aid} = $data;
          $author_list{$order}{row_curator} = $row_curator;
          $author_list{$order}{timestamp} = $timestamp; }

#       my @data; foreach (@row) { if ($_) { push @data, $_; } else { push @data, ""; } }		# some data is undefined
#       my $data = join"</td><td>", @data;
      if ( ($table eq 'type') || ($table eq 'curation_flags') || ($table eq 'primary_data') 
                              || ($table eq 'year') || ($table eq 'month') || ($table eq 'day') ) { 
          ($td_data) = &makeSelectField($data, $table, $joinkey, $order, $curator_id); }
        elsif ( ($table eq 'electronic_path') || ($table eq 'pubmed_final') ) { 1; }
#         elsif ( ($table eq 'title') || ($table eq 'gene') ) { ($td_data) = &makeTextareaField($data, $table, $joinkey, $order, $curator_id, "8", "80"); }
        elsif ( ($table eq 'title') ) { ($td_data) = &makeTextareaField($data, $table, $joinkey, $order, $curator_id, "8", "80"); }
        elsif ($table eq 'abstract') { ($td_data) = &makeTextareaField($data, $table, $joinkey, $order, $curator_id, "40", "80"); }
        elsif ($table eq 'status') { ($td_data) = &makeStatusField($data, $table, $joinkey, $order, $curator_id); }
        elsif ($table eq 'gene') { ($td_data) = &makeGeneDeleteField($data, $table, $joinkey, $order, $curator_id, $row[0]); }
        else { ($td_data) = &makeInputField($data, $table, $joinkey, $order, $curator_id, '3', '1', ''); }

      unless ($table eq 'author') {
        $entry_data .= "<tr bgcolor='$blue'><td>$table</td>$td_data<td>$order</td><td>$row_curator</td><td style=\"width:11em\">$timestamp</td></tr>\n"; }
    } # while (my @row = $result->fetchrow)

    if ( ($multi{$table}) || ($table_has_data == 0) ) {
#       next if ($table eq 'author');				# do not allow new authors here
      my $order = ""; if ($multi{$table}) { $order = 1; }	# set default order for non-multi and multi tables
      if ($highest_order) { $order = $highest_order + 1; }
      my $td_data = '';			# default new values are blank
      if ($table eq 'electronic_path') { 1; }			# not an editable field
        elsif ($table eq 'pubmed_final') { 1; }			# not an editable field	# don't display to prevent errors  2010 12 13
        elsif ( ($table eq 'type') || ($table eq 'curation_flags') || ($table eq 'year') || ($table eq 'month') || ($table eq 'day') ) { 
          ($td_data) = &makeSelectField("", $table, $joinkey, $order, $curator_id); 
          $entry_data .= "<tr bgcolor=\"white\"><td>$table</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n"; }
        elsif ($table eq 'gene') { 
          ($td_data) = &makeGeneTextareaField('', $table, $joinkey, $order, $curator_id, "8", "80");
          $entry_data .= "<tr bgcolor=\"white\"><td>$table (batch)</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n";
          ($td_data) = &makeGeneEvidenceField('', $table, $joinkey, $order, $curator_id, '3', '1', '');
          $entry_data .= "<tr bgcolor=\"white\"><td>$table (evi)</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n"; }
        elsif ($table eq 'title') { 
          ($td_data) = &makeTextareaField($td_data, $table, $joinkey, $order, $curator_id, "8", "80");
          $entry_data .= "<tr bgcolor=\"white\"><td>$table</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n"; }
        elsif ($table eq 'abstract') { 
          ($td_data) = &makeTextareaField($td_data, $table, $joinkey, $order, $curator_id, "40", "80");
          $entry_data .= "<tr bgcolor=\"white\"><td>$table</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n"; }
        elsif ($table eq 'author') { 
          ($td_data) = &makeInputField("", 'author_new', $joinkey, $order, $curator_id, '3', '1', '');
          $entry_data .= "<tr bgcolor=\"white\"><td>$table</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n"; }
        else { 
          ($td_data) = &makeInputField("", $table, $joinkey, $order, $curator_id, '3', '1', '');
          $entry_data .= "<tr bgcolor=\"white\"><td>$table</td>$td_data<td>$order</td><td>$curator_id</td><td>current</td></tr>\n"; }
    }
    if ($table eq 'author') { $entry_data = &getAuthorDisplay(\%author_list) . $entry_data; }
    $display_data{$table} = $entry_data;
  } # foreach my $table (@normal_tables)

#   if ( ($curator_id eq 'two1823') || ($curator_id eq 'two1') ) { # }
  if ( $curator_id eq 'two1' ) {
    &displayAuthorPersonSection(\@authors, \%aid_data, $curator_id); 
    &displayMainPaperSection($joinkey, \%display_data); }
  else {
    &displayMainPaperSection($joinkey, \%display_data);
    &displayAuthorPersonSection(\@authors, \%aid_data, $curator_id); }

  if ( ($curator_id eq 'two1823') || ($curator_id eq 'two1843') || ($curator_id eq 'two1') )  {
    print "<tr><td colspan=\"5\">Merge WBPaper <input size=10 name=\"merge_into\" id=\"merge_into\" onblur=\"mergePaper('$joinkey', '$curator_id')\"> into this WBPaper$joinkey <input type=\"button\" onclick=\"mergePaper('$joinkey', '$curator_id')\" value=\"click for merging page\"></td></tr>\n"; }

} # sub displayNumber


sub displayAuthorPersonSection {
  my ($authors_ref, $aid_data_ref, $curator_id) = @_;
  &populateCurators();						# for verified yes / no standard name
  my @person_autocomplete_input_ids;				# ids of input fields for person autocomplete
  my @authors = @$authors_ref;
  my %aid_data = %$aid_data_ref;
  print "<table style=\"border-style: none;\" border=\"1\" >\n";
  my @aut_tables = qw( possible sent verified );
  my $aids = join"', '", @authors;
  foreach my $table (@aut_tables) {
#     print "SELECT * FROM pap_author_$table WHERE author_id IN ('$aids');<br />\n";
    $result = $dbh->prepare( "SELECT * FROM pap_author_$table WHERE author_id IN ('$aids');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      $aid_data{$row[0]}{join}{$row[2]}{$table}{time} = $row[4]; 
      $aid_data{$row[0]}{join}{$row[2]}{$table}{data} = $row[1]; }
  } # foreach my $table (@aut_tables)
  print "<tr bgcolor='$blue'><td class=\"normal_even\">aid</td><td class=\"normal_even\">author</td><td class=\"normal_even\">new</td><td class=\"normal_even\">join</td><td class=\"normal_even\">possible</td><td class=\"normal_even\">pos_time</td><td class=\"normal_even\">sent</td><td class=\"normal_even\">verified</td><td class=\"normal_even\">ver_time</td></tr>\n";
  foreach my $aid (@authors) {
    my @entries;
    my $class = 'normal_even';
    my $author = ''; if ($aid_data{$aid}{index}) { $author = $aid_data{$aid}{index}; }
    foreach my $join (sort {$a<=>$b} keys %{ $aid_data{$aid}{join} } ) {
      my $possible = ''; my $pos_time = ''; my $sent = ''; my $verified = ''; my $ver_time = '';
      if ($aid_data{$aid}{join}{$join}{possible}{data}) { $possible = $aid_data{$aid}{join}{$join}{possible}{data}; }
      if ($aid_data{$aid}{join}{$join}{possible}{time}) { $pos_time = $aid_data{$aid}{join}{$join}{possible}{time}; $pos_time =~ s/ [\:\.\d\-]+$//; }
      if ($aid_data{$aid}{join}{$join}{sent}{data}) { $sent = $aid_data{$aid}{join}{$join}{sent}{data}; }
      if ($aid_data{$aid}{join}{$join}{verified}{data}) { $verified = $aid_data{$aid}{join}{$join}{verified}{data}; }
      if ($aid_data{$aid}{join}{$join}{verified}{time}) { $ver_time = $aid_data{$aid}{join}{$join}{verified}{time}; $ver_time =~ s/ [\:\.[\d\-]+$//; }
#       my ($td_author_possible) = &makeInputField($possible, 'author_possible', $aid, $join, $curator_id, 1, 1, $class); 
      my ($input_id, $td_author_possible) = &makeOntologyField($possible, 'author_possible', $aid, $join, $curator_id, 1, 1, $class);
      push @person_autocomplete_input_ids, $input_id;
      my ($td_author_sent) = &makeUneditableField($sent, 'author_sent', $aid, $join, $curator_id, 1, 1, $class); 
      my ($td_author_verified) = &makeUneditableField($verified, 'author_verified', $aid, $join, $curator_id, 1, 1, $class); 
      if ($possible) {
        my $on = "YES  $curators{two}{$curator_id}"; my $off = "NO  $curators{two}{$curator_id}";
        ($td_author_verified) = &makeToggleTripleField($verified, 'author_verified', $aid, $join, $curator_id, 1, 1, $class, $on, $off, '');  }
      my $entry = "<td class=\"normal_even\">$join</td>$td_author_possible<td class=\"normal_even\">$pos_time</td>${td_author_sent}${td_author_verified}<td class=\"normal_even\">$ver_time</td>";
      push @entries, $entry;
    } # foreach my $join (sort {$a<=>$b} keys %{ $aid_data{$aid}{join} } )
    unless ($entries[0]) {				# if there are no entries already, make a blank one
      my $join = '1';
#       my ($td_author_possible) = &makeInputField('', 'author_possible', $aid, $join, $curator_id, 1, 1, $class); 
      my ($input_id, $td_author_possible) = &makeOntologyField('', 'author_possible', $aid, $join, $curator_id, 1, 1, $class);
      push @person_autocomplete_input_ids, $input_id;
      my ($td_author_sent) = &makeUneditableField('', 'author_sent', $aid, $join, $curator_id, 1, 1, $class); 
      my ($td_author_verified) = &makeUneditableField('', 'author_verified', $aid, $join, $curator_id, 1, 1, $class);	# there cannot be a value under possible, so do not allow verify edit
      my $entry = "<td class=\"normal_even\">$join</td>$td_author_possible<td class=\"normal_even\"></td>${td_author_sent}${td_author_verified}<td class=\"normal_even\"></td>";
      push @entries, $entry; }
    my $lines_count = scalar(@entries); 
    my $first_entry = shift @entries;
    my ($input_id, $td_author_possible_new) = &makeOntologyField('', 'author_possible', $aid, 'new', $curator_id, 1, $lines_count, $class);
    push @person_autocomplete_input_ids, $input_id;
#   my ($current_value, $table, $joinkey, $order, $curator_id, $colspan, $rowspan, $class) = @_;
    my ($td_author_index) = &makeInputField($author, 'author_index', $aid, '', $curator_id, 1, $lines_count, $class); 
#     print "<tr bgcolor='$blue'><td rowspan=\"$lines_count\" class=\"normal_even\">$aid</td>$td_author_index<td rowspan=\"$lines_count\" class=\"normal_even\"><input type=\"button\" value=\"new join\"></td>$first_entry</tr>";
    print "<tr bgcolor='$blue'><td rowspan=\"$lines_count\" class=\"normal_even\">$aid</td>$td_author_index$td_author_possible_new$first_entry</tr>";
    foreach my $entry (@entries) { print "<tr>$entry</tr>\n"; }
    
  } # foreach my $aid (@authors)

#   print "<tr><td colspan=5><div id=\"forcedPersonAutoComplete\">
#         <input id=\"forcedPersonInput\" type=\"text\">
#         <div id=\"forcedPersonContainer\"></div></div></td></tr>";
  print "</table>\n";
  my $person_input_ids = join", ",  @person_autocomplete_input_ids;		# ids of input fields for person autocomplete
  print "<input type=\"hidden\" id=\"person_input_ids\" value=\"$person_input_ids\">";
} # sub displayAuthorPersonSection


sub displayMainPaperSection {
  my ($joinkey, $display_data_ref) = @_;
  my %display_data = %$display_data_ref;
  print "<table border=0>\n";
  print "<tr bgcolor='$blue'><td colspan=7>WBPaper$joinkey</td></tr>\n";
  foreach my $table (@normal_tables) { 
    if ($display_data{$table}) { print $display_data{$table}; } }
  print "</table><br />";
} # sub displayMainPaperSection

sub getAuthorDisplay {
  my ($author_list_ref) = @_;
  my %author_list = %$author_list_ref;
  my @other_row_data; my $highest_order = 0;
  my $ul = "<ul id=\"author_list\" class=\"draglist\">";
  foreach my $order (sort {$a<=>$b} keys %author_list) {
    $highest_order = $order;
    my $name = $author_list{$order}{name};
    my $aid = $author_list{$order}{aid};
    my $curator = $author_list{$order}{row_curator};
    my $timestamp = $author_list{$order}{timestamp};
    $ul .= "<li class=\"list1\" id=\"author_li_$order\" value=\"$aid\">$aid ($name)</li>";
    push @other_row_data, "<td>$order</td><td>$curator</td><td>$timestamp</td>";
  }
  $ul .= "</ul>";
  my $lines_count = scalar(@other_row_data);
  my $first_entry = shift @other_row_data;
  if ($lines_count == 0) { return ''; }			# no authors return blank for section to reorder existing authors
  my $to_return = "<tr bgcolor='$blue'><td rowspan=\"$lines_count\">author</td><td rowspan=\"$lines_count\" colspan=\"3\">$ul</td>$first_entry";
  foreach (@other_row_data) { $to_return .= "<tr bgcolor='$blue'>$_</tr>"; }
  $to_return .= "<input type=\"hidden\" id=\"author_max_order\" value=\"$highest_order\">";
  return $to_return;
} # sub getAuthorDisplay

sub search {
  &printHtmlHeader();
#   my $history = 'off';
#   ($oop, my $temp_history) = &getHtmlVar($query, "history");
#   if ($temp_history) { $history = $temp_history; }
#   print "History display $history<br/>\n"; 

  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  &updateCurator($curator_id);

  ($oop, my $number) = &getHtmlVar($query, "data_number");
  if ($number) { 
#     if ($number =~ m/(\d+)/) { &displayNumber(&padZeros($1), $history); return; }
    if ($number =~ m/(\d+)/) { &displayNumber(&padZeros($1), $curator_id); return; }
      else { print "Not a number in a number search for $number<br />\n"; } }

  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"searchResults\">";

  my %hash;
  foreach my $table (@normal_tables) {
    ($oop, my $data) = &getHtmlVar($query, "data_$table");
    next unless ($data);	# skip those with search params
    my $substring = ''; my $case = ''; my $operator = '=';
    ($oop, $substring) = &getHtmlVar($query, "substring_$table");
    ($oop, $case) = &getHtmlVar($query, "case_$table");
    if ($case eq 'on') { $operator = '~*'; }
    elsif ($substring eq 'on') { $operator = '~'; }
    if ($table eq 'author') {
#       print "SELECT joinkey, pap_author FROM pap_author WHERE pap_author IN (SELECT author_id FROM pap_author_index WHERE pap_author_index $operator '$data')<br />\n";
      print "SELECT pap_author.joinkey, pap_author.pap_author, pap_author_index.pap_author_index FROM pap_author, pap_author_index WHERE pap_author.pap_author = pap_author_index.author_id AND pap_author_index $operator '$data'<br />\n";
      $result = $dbh->prepare( "SELECT pap_author.joinkey, pap_author.pap_author, pap_author_index.pap_author_index FROM pap_author, pap_author_index WHERE pap_author.pap_author = pap_author_index.author_id AND pap_author_index $operator '$data'" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) {
        $hash{matches}{$row[0]}{$table}++; 
        push @{ $hash{table}{$table}{$row[0]} }, "$row[1] ($row[2])"; } }
    else {
      print "SELECT joinkey, pap_$table FROM pap_$table WHERE pap_$table $operator '$data'<br />\n";
      $result = $dbh->prepare( "SELECT joinkey, pap_$table FROM pap_$table WHERE pap_$table $operator '$data'" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) { 
        $hash{matches}{$row[0]}{$table}++; 
        push @{ $hash{table}{$table}{$row[0]} }, $row[1]; } }
  } # foreach my $table (@normal_tables)
  my %matches; 
  foreach my $joinkey (keys %{ $hash{matches} }) {
    my $count = scalar keys %{ $hash{matches}{$joinkey} }; $matches{$count}{$joinkey}++; }
  foreach my $count (reverse sort {$a<=>$b} keys %matches) {
    print "<br />Matches $count<br />\n";
    foreach my $joinkey (sort {$a<=>$b} keys %{ $matches{$count} }) {
#       print "<a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?action=Search&data_number=$joinkey&history=$history\">WBPaper$joinkey</a>\n";
      print "<a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?action=Search&data_number=$joinkey&curator_id=$curator_id\">WBPaper$joinkey</a>\n";
      foreach my $table (keys %{ $hash{table} }) {
        next unless $hash{table}{$table}{$joinkey};
        my $data_match = join", ", @{ $hash{table}{$table}{$joinkey} }; 
        if ($table eq 'type') { $data_match = $type_index{$data_match}; }
        print "$table : <font color=\"green\">$data_match</font>\n"; }
      print "<br />\n";
    } # foreach my $joinkey (sort {$a<=>$b} keys %{ $matches{$count} })
  }
  &printFooter();
} # sub search


sub flagFalsePositives {
  &printHtmlHeader();
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  print "<form name='form1' method=\"post\" action=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi\">\n";
  print "<input type=\"hidden\" name=\"curator_id\" id=\"curator_id\" value=\"$curator_id\">";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"flagFalsePositives\">";
  my ($arrayref) = &getFirstPassTables();
  my @fptables = @$arrayref; my %filter;
  foreach my $table (@fptables) { $filter{$table}++; }
  $filter{""}++; $filter{antibody}++; $filter{extvariation}++;
  print "Select a first pass type to mark as false positive : <select name=\"fptype\" size=1>\n";
  foreach my $table (sort keys %filter) { print "<option value=\"$table\">$table</option>\n"; }
  print "</select><br />\n";

  print "Enter WBPapers and comment (one each per line) : <br/>\n";
  print "<textarea name=\"false_positives\" rows=35 cols=80 value=\"\"></textarea><br/>\n";
  print "<input type=\"submit\" name=\"action\" value=\"Enter False Positives\">\n";
  print "<input type=\"submit\" name=\"action\" value=\"Show False Positives\"><br />\n";

  print "</form>\n";

  &printFooter();
} # sub flagFalsePositives

sub showFalsePositives {
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"showFalsePositives\">";
  my ($var, $table) = &getHtmlVar($query, "fptype");
  print "using table $table<BR>\n";
  print "<table border=1>\n";
  my $result = $dbh->prepare( "SELECT * FROM cfp_$table WHERE cfp_$table ~ 'FALSE POSITIVE' ");
  $result->execute;
  while (my @row = $result->fetchrow) {
    foreach (@row) { $_ = "<td>$_</td>"; }
    print "<tr>@row</tr>\n"; 
  } # while (my @row = $result->fetchrow)
  print "</TABLE>\n";
  &printFooter();
} # sub showFalsePositives

sub enterFalsePositives {
  &populateCurators();						# for false positive comment
  &printHtmlHeader();
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"enterFalsePositives\">";
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
    &postgresFalsePositive($table, $paper, $comment, $curator_id);
  } # foreach my $line (@lines)
  &printFooter();
} # sub enterFalsePositives

sub postgresFalsePositive {
  my ($table, $paper, $comment, $curator_id) = @_;
  ($comment) = &filterForPg($comment);                  # replace ' with ''
  my $result = $dbh->prepare( "SELECT * FROM cfp_$table WHERE joinkey = '$paper' ");
  $result->execute;
  my $pgcommand = '';
  my @row = $result->fetchrow();
  if ($row[0]) {
    $pgcommand = "UPDATE cfp_$table SET cfp_$table = '$row[1] is FALSE POSITIVE : $comment -- $curators{two}{$curator_id}' WHERE joinkey = '$paper'; ";
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
    $pgcommand = "UPDATE cfp_$table SET cfp_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$paper'; ";
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
    $pgcommand = "UPDATE cfp_$table SET cfp_curator = '$curator_id' WHERE joinkey = '$paper'; ";
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
  } else {
    $pgcommand = "INSERT INTO cfp_$table VALUES ('$paper', 'FALSE POSITIVE : $comment -- $curators{two}{$curator_id}', '$curator_id'); ";
    $result = $dbh->prepare( $pgcommand );
    $result->execute;
    print "PAP $paper REASON $comment PSQL <FONT COLOR=green>$pgcommand</FONT><BR>\n";
  }
} # sub postgresFalsePositive

sub makePdfLinkFromPath {
  my ($path) = shift;
  my ($pdf) = $path =~ m/\/([^\/]*)$/;
  my $link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
  my $data = "<a href=\"$link\" target=\"new\">$pdf</a>"; return $data; }
sub makeNcbiLinkFromPmid {
  my $pmid = shift;
  my ($id) = $pmid =~ m/(\d+)/;
  my $link = 'http://www.ncbi.nlm.nih.gov/pubmed/' . $id; 
  my $data = "<a href=\"$link\" target=\"new\">$pmid</a>"; return $data; }

sub rnaiCuration {
  &printHtmlHeader();
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  print "<input type=\"hidden\" name=\"curator_id\" id=\"curator_id\" value=\"$curator_id\">";
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"rnaiCuration\">";

  &populateCurators();						# for verified yes / no standard name

  my $table_menu = "<tr><td align=center>WBPaperID</td><td align=center>Identifiers</td><td align=center>pdf</td><td align=center>RNAi data</td><td align=center>LS RNAi data</td><td align=center>curate</td></tr>\n";
  print "<table border=0>";
  print $table_menu;

  my %rnai; my %idents; my %pdfs; my %curated; # my %highest;
  $result = $dbh->prepare( "SELECT * FROM pap_curation_flags WHERE pap_curation_flags = 'rnai_curation'"); $result->execute;
  while (my @row = $result->fetchrow) { $curated{$row[0]} = $row[3]; }
#   my (@not_joinkeys) = keys %curated;
#   my $not_joinkeys = join"', '", @not_joinkeys;

  my %valid_papers; my $valid_papers;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'"); $result->execute;
  while (my @row = $result->fetchrow) { $valid_papers{$row[0]}++; }
  my (@valid_papers) = keys %valid_papers; $valid_papers = join"', '", @valid_papers;

  $result = $dbh->prepare( "SELECT joinkey, cfp_rnai FROM cfp_rnai WHERE cfp_rnai IS NOT NULL AND joinkey ~ '^0' AND joinkey IN ('$valid_papers'); ");
#   $result = $dbh->prepare( "SELECT joinkey, cfp_rnai FROM cfp_rnai WHERE cfp_rnai IS NOT NULL AND joinkey ~ '^0' AND joinkey NOT IN ('$not_joinkeys'); ");
  $result->execute;
#   while (my @row = $result->fetchrow) { $rnai{$row[0]}{rnai} = $row[1]; }	# populate most valid joinkeys for type
  while (my @row = $result->fetchrow) { $rnai{$row[0]}{rnai}{$row[1]}++; }	# populate most valid joinkeys for type
  $result = $dbh->prepare( "SELECT joinkey, afp_rnai FROM afp_rnai WHERE afp_rnai IS NOT NULL AND joinkey ~ '^0' AND joinkey IN ('$valid_papers'); ");
  $result->execute;
  while (my @row = $result->fetchrow) { $rnai{$row[0]}{rnai}{$row[1]}++; }	# populate most valid joinkeys for type
  $result = $dbh->prepare( "SELECT joinkey, cfp_lsrnai FROM cfp_lsrnai WHERE cfp_lsrnai IS NOT NULL AND joinkey ~ '^0' AND joinkey IN ('$valid_papers'); ");
#   $result = $dbh->prepare( "SELECT joinkey, cfp_lsrnai FROM cfp_lsrnai WHERE cfp_lsrnai IS NOT NULL AND joinkey ~ '^0' AND joinkey NOT IN ('$not_joinkeys'); ");
  $result->execute;
#   while (my @row = $result->fetchrow) { $rnai{$row[0]}{lsrnai} = $row[1]; }	# populate lsrnai valid joinkeys
  while (my @row = $result->fetchrow) { $rnai{$row[0]}{lsrnai}{$row[1]}++; }	# populate lsrnai valid joinkeys
  $result = $dbh->prepare( "SELECT joinkey, afp_lsrnai FROM afp_lsrnai WHERE afp_lsrnai IS NOT NULL AND joinkey ~ '^0' AND joinkey IN ('$valid_papers'); ");
  $result->execute;
  while (my @row = $result->fetchrow) { $rnai{$row[0]}{lsrnai}{$row[1]}++; }	# populate lsrnai valid joinkeys

  my (@joinkeys) = keys %rnai;
  my $joinkeys = join"', '", @joinkeys;

#   $result = $dbh->prepare( "SELECT * FROM pap_curation_flags WHERE joinkey IN ('$joinkeys') AND pap_curation_flags = 'rnai_curation'"); $result->execute;
#   while (my @row = $result->fetchrow) { $curated{$row[0]} = $row[3]; }
#   $result = $dbh->prepare( "SELECT * FROM pap_curation_flags WHERE joinkey IN ('$joinkeys') ORDER BY pap_order"); $result->execute;
#   while (my @row = $result->fetchrow) { $highest{$row[0]} = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid' AND joinkey IN ('$joinkeys')"); $result->execute;
  while (my @row = $result->fetchrow) { 
    my ($data) = &makeNcbiLinkFromPmid($row[1]);
    $idents{$row[0]}{$data}++; }
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path WHERE joinkey IN ('$joinkeys')"); $result->execute;
  while (my @row = $result->fetchrow) { 
    my ($data) = &makePdfLinkFromPath($row[1]);
    $pdfs{$row[0]}{$data}++; }

  my $alignment = 'center';
  foreach my $joinkey (reverse sort keys %rnai) {
    my ($idents, $pdfs, $rnai_data, $lsrnai_data, $curate_link) = ('', '', '', '', '');
#     if ($rnai{$joinkey}{rnai}) { $rnai_data = $rnai{$joinkey}{rnai}; }
#     if ($rnai{$joinkey}{lsrnai}) { $lsrnai_data = $rnai{$joinkey}{lsrnai}; }
    if ($rnai{$joinkey}{rnai}) { 
      my @rnai_data = sort keys %{ $rnai{$joinkey}{rnai} };
      $rnai_data = join" -- ", @rnai_data; }
    if ($rnai{$joinkey}{lsrnai}) { 
      my @rnai_data = sort keys %{ $rnai{$joinkey}{lsrnai} };
      $lsrnai_data = join" -- ", @rnai_data; }
    if ($idents{$joinkey}) { my @idents = sort keys %{ $idents{$joinkey} }; $idents = join"<br/>", @idents; }
    if ($pdfs{$joinkey}) { my @pdfs = reverse sort keys %{ $pdfs{$joinkey} }; $pdfs = join"<br/>", @pdfs; }
    if ($curated{$joinkey}) { $curate_link = $curators{two}{$curated{$joinkey}}; }
      else {
#         my $order = 1; if ($highest{$joinkey}) { $order = $highest{$joinkey} + 1; }
        $curate_link = "<a href=\"#\" onclick=\"updatePostgresTableField('curation_flags', '$joinkey', 'new', '$curator_id', 'rnai_curation', '', 'nothing'); document.getElementById('td_curate_$joinkey').innerHTML = '$curators{two}{$curator_id}'; return false\">curate</a>"; }
    print "<tr>";
    print "<td align=\"$alignment\"><a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=$curator_id&action=Search&data_number=$joinkey\" target=\"new\">$joinkey</a></td>";
    print "<td align=\"$alignment\">$idents</td>";
    print "<td align=\"$alignment\">$pdfs</td>";
    print "<td align=\"$alignment\">$rnai_data</td>";
    print "<td align=\"$alignment\">$lsrnai_data</td>";
    print "<td align=\"$alignment\" id=\"td_curate_$joinkey\">$curate_link</td>";
    print "</tr>";
  } # foreach my $joinkey (reverse sort keys %rnai)
  print $table_menu;

  &printFooter();
} # sub rnaiCuration

sub authorGeneDisplay {			# for Karen
  &printHtmlHeader();
  print "<input type=\"hidden\" name=\"which_page\" id=\"which_page\" value=\"authorGeneDisplay\">";
  ($oop, my $curator_id) = &getHtmlVar($query, 'curator_id');
  unless ($curator_id) { print "ERROR NO CURATOR<br />\n"; return; }
  &updateCurator($curator_id);
  my $who = '';
  if ($curator_id eq 'two712') { $who = 'Karen Yook'; }
  if ($curator_id eq 'two1843') { $who = 'Kimberly Van Auken'; }

  my %data; tie %{ $data{when} }, "Tie::IxHash";

  $result = $dbh->prepare( "SELECT * FROM afp_lasttouched ORDER BY afp_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $data{when}{$row[0]} = $row[2]; }
  my $joinkeys = join"', '", keys %{ $data{when} };

  $result = $dbh->prepare( "SELECT * FROM afp_genestudied ORDER BY afp_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $data{author}{$row[0]} = $row[1]; }

  $result = $dbh->prepare( "SELECT * FROM pap_gene WHERE pap_evidence ~ 'Inferred_automatically' AND joinkey IN ('$joinkeys') ORDER BY pap_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { 
    my $abstract_read = '';
    if ($row[5] =~ m/\"Abstract read (.*?)\"/) { $abstract_read = $1; }
    $data{inferred}{$row[0]}{"WBGene$row[1]($abstract_read)"}{$row[2]}++; }
  $result = $dbh->prepare( "SELECT * FROM pap_gene WHERE (pap_evidence ~ 'Curator_confirmed' OR pap_evidence ~ 'cfp_genestudied') AND joinkey IN ('$joinkeys') ORDER BY pap_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { 
    my $name = &getGeneName($row[1]);
    $data{curator}{$row[0]}{"WBGene$row[1]($name)"}{$row[2]}++; }

# the old tables used to have the name in parenthesis in the gene column, instead of under Manually_connected
#   $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE wpa_evidence ~ 'Inferred_automatically' AND joinkey IN ('$joinkeys') ORDER BY wpa_timestamp" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'valid') { $data{inferred}{$row[0]}{$row[1]}{$row[2]}++; }
#       else { delete $data{inferred}{$row[0]}{$row[1]}{$row[2]}; } }
#   $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE (wpa_evidence ~ 'Curator_confirmed' OR wpa_evidence ~ 'cfp_genestudied') AND joinkey IN ('$joinkeys') ORDER BY wpa_timestamp" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'valid') { $data{curator}{$row[0]}{$row[1]}{$row[2]}++; }
#       else { delete $data{curator}{$row[0]}{$row[1]}{$row[2]}; } }

  print "<table border=1>\n";
  print "<tr bgcolor='$blue'><td class=\"normal_odd\">WBPaper ID</td><td class=\"normal_odd\">author date</td><td class=\"normal_odd\" width=\"30%\">Inferred_automatically</td><td class=\"normal_odd\" width=\"30%\">Author FP</td><td class=\"normal_odd\" width=\"30%\">Curator confirmed</td></tr>\n";
#   foreach my $joinkey (sort {$data{when}{$b} <=> $data{when}{$a}} keys %{ $data{when} })
  foreach my $joinkey (reverse keys %{ $data{when} }) {
    my $author = ''; my $inferred = ''; my $curator = '';
    my $when = $data{when}{$joinkey};
    $when =~ s/\.[\-\d]+$//;
    if ($data{author}{$joinkey}) { 
      $author = $data{author}{$joinkey};
      if ($author =~ m/^(.{1000})/s) { $author = $1 . " ..."; } }
    if ($data{curator}{$joinkey}) { 
      $curator = join", ", sort keys %{ $data{curator}{$joinkey} }; 
      if ($curator =~ m/^(.{1000})/s) { $curator = $1 . " ..."; } }
    if ($data{inferred}{$joinkey}) { 
      $inferred = join", ", sort keys %{ $data{inferred}{$joinkey} }; 
      if ($inferred =~ m/^(.{1000})/s) { $inferred = $1 . " ..."; } }
    print "<tr bgcolor='$blue'>\n";
    print "<td valign=\"top\" class=\"normal_odd\"><a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_editor.cgi?number=$joinkey&action=Number+%21&curator_name=$who\" target=\"new\">$joinkey</a></td>\n";
    print "<td valign=\"top\" class=\"normal_odd\">$when</td>\n";
    print "<td valign=\"top\" class=\"normal_odd\">$inferred</td>\n";
    print "<td valign=\"top\" class=\"normal_odd\">$author</td>\n";
    print "<td valign=\"top\" class=\"normal_odd\">$curator</td>\n";
    print "</tr>\n";
  } # foreach my $joinkey (sort {$data{when}{$a} <=> $data{when}{$b}} keys %{ $data{when} })
  print "</table>\n";
  &printFooter();
} # sub authorGeneDisplay


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
  my ($joinkey) = @_;
  my $ip = $query->remote_host();
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip' AND joinkey = '$joinkey';" );
  $result->execute;
  my @row = $result->fetchrow;
  unless ($row[0]) {
    $result = $dbh->do( "DELETE FROM two_curator_ip WHERE two_curator_ip = '$ip' ;" );
    $result = $dbh->do( "INSERT INTO two_curator_ip VALUES ('$joinkey', '$ip')" );
    print "IP $ip updated for $joinkey<br />\n"; } }

sub populateCurators {
#   my $result = $conn->exec( "SELECT * FROM two_standardname; " );
  my $result = $dbh->prepare( "SELECT * FROM two_standardname; " );
  $result->execute;
  while (my @row = $result->fetchrow) {
    $curators{two}{$row[0]} = $row[2];
    $curators{std}{$row[2]} = $row[0];
  } # while (my @row = $result->fetchrow)
} # sub populateCurators

sub populateMonthIndex {
  $month_index{1} = 'January';
  $month_index{2} = 'February';
  $month_index{3} = 'March';
  $month_index{4} = 'April';
  $month_index{5} = 'May';
  $month_index{6} = 'June';
  $month_index{7} = 'July';
  $month_index{8} = 'August';
  $month_index{9} = 'September';
  $month_index{10} = 'October';
  $month_index{11} = 'November';
  $month_index{12} = 'December';
} # sub populateMonthIndex

sub populateValidPaperIndex {
  my $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $valid_paper_index{$row[0]} = $row[1]; } }
} # sub populateValidPaperIndex

sub populateTypeIndex {
  my $result = $dbh->prepare( "SELECT * FROM pap_type_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $type_index{$row[0]} = $row[1]; }
  }
#   $result = $dbh->prepare( "SELECT * FROM pap_electronic_type_index;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[0]) { $electronic_type_index{$row[0]} = $row[1]; }
#   }
} # sub populateTypeIndex

sub populateSingleMultiTableTypes {
# unique (single value) tables :  status title journal publisher pages volume year month day pubmed_final primary_data abstract );
  $single{'status'}++;
  $single{'title'}++;
  $single{'journal'}++;
  $single{'publisher'}++;
  $single{'volume'}++;
  $single{'pages'}++;
  $single{'year'}++;
  $single{'month'}++;
  $single{'day'}++;
  $single{'pubmed_final'}++;
  $single{'primary_data'}++;
  $single{'abstract'}++;
  
  # multivalue tables :  editor type author affiliation fulltext_url contained_in gene identifier ignore remark erratum_in internal_comment curation_flags 
  
  $multi{'editor'}++;
  $multi{'type'}++;
  $multi{'author'}++;
  $multi{'affiliation'}++;
  $multi{'fulltext_url'}++;
  $multi{'contained_in'}++;
  $multi{'gene'}++;
  $multi{'identifier'}++;
  $multi{'ignore'}++;
  $multi{'remark'}++;
  $multi{'erratum_in'}++;
  $multi{'internal_comment'}++;
  $multi{'curation_flags'}++;
  $multi{'electronic_path'}++;
  $multi{'author_possible'}++;
  $multi{'author_sent'}++;
  $multi{'author_verified'}++;
} # sub populateSingleMultiTableTypes



__END__

use strict;
use diagnostics;
use DBI;
use Jex;		# filter for Pg

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my %tableToTag;
$tableToTag{title}	= 'Title';
$tableToTag{type}	= 'Type';
$tableToTag{journal}	= 'Journal';
$tableToTag{publisher}	= 'Publisher';
$tableToTag{pages}	= 'Page';
$tableToTag{volume}	= 'Volume';
$tableToTag{year}	= 'Publication_date';
$tableToTag{abstract}	= 'Abstract';
$tableToTag{editor}	= 'Editor';
$tableToTag{affiliation}	= 'Affiliation';
$tableToTag{fulltext_url}	= 'URL';
$tableToTag{contained_in}	= 'Contained_in';
$tableToTag{identifier}	= 'Name';
$tableToTag{remark}	= 'Remark';
$tableToTag{erratum_in}	= 'Erratum_in';
$tableToTag{gene}	= 'Gene';
$tableToTag{author}	= 'Author';
$tableToTag{curation_flags}	= 'Curation_pipeline';

my @normal_tables = qw( status type title journal publisher pages volume year month day abstract editor affiliation fulltext_url contained_in identifier remark erratum_in curation_flags author gene );

my %indices;
$result = $dbh->prepare( "SELECT * FROM pap_type_index");	
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $indices{type}{$row[0]} = $row[1]; }

$result = $dbh->prepare( "SELECT * FROM pap_author_index");	
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $indices{author}{$row[0]} = $row[1]; }

$result = $dbh->prepare( "SELECT pap_author_verified.author_id, pap_author_possible.pap_author_possible, pap_author_verified.pap_author_verified FROM pap_author_verified, pap_author_possible WHERE pap_author_verified.pap_author_verified ~ 'YES' AND pap_author_possible.pap_author_possible ~ 'two' AND pap_author_verified.author_id = pap_author_possible.author_id AND pap_author_verified.pap_join = pap_author_possible.pap_join;");
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { 
  $row[1] =~ s/two/WBPerson/;
  $indices{person}{$row[0]} = $row[1]; }

my %hash; 
foreach my $table (@normal_tables) {
  $result = $dbh->prepare( "SELECT * FROM pap_$table");	
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    unless ($row[2]) { $row[2] = 'NULL'; }
    if ($table eq 'type') { $hash{$table}{$row[0]}{$row[2]}{curator} = $row[3]; }
    elsif ($table eq 'gene') { $hash{$table}{$row[0]}{$row[2]}{evi} = $row[5]; }
    $hash{$table}{$row[0]}{$row[2]}{data} = $row[1]; }
}


my $abstracts;

foreach my $joinkey (sort keys %{ $hash{status} }) {
  next if ($joinkey eq '00000001');
  print "\nPaper : \"WBPaper$joinkey\"\n";
  print "Status\t\"" . ucfirst($hash{status}{$joinkey}{NULL}{data}) . "\"\n";
  next if ($hash{status}{$joinkey}{NULL}{data} ne 'valid');
  foreach my $table (@normal_tables) {
    next if ($table eq 'status');
    next if ($table eq 'month');
    next if ($table eq 'day');
    foreach my $order (sort keys %{ $hash{$table}{$joinkey} }) {
      my $tag = $tableToTag{$table};
      my $data = $hash{$table}{$joinkey}{$order}{data};
      ($data) = &filterAce($data);	# filter here, future changes will have doublequotes and what not that shouldn't be escaped
      if ($table eq 'year') { 
        if ($hash{month}{$joinkey}{NULL}{data}) { 
          my $month = $hash{month}{$joinkey}{NULL}{data};
          if ($month < 10) { $month = "0$month"; }
          $data .= "-$month"; }
        if ($hash{day}{$joinkey}{NULL}{data}) { 
          my $day = $hash{day}{$joinkey}{NULL}{data};
          if ($day < 10) { $day = "0$day"; }
          $data .= "-$day"; }
      }
      elsif ($table eq 'identifier') {  
        if ($data =~ m/^\d{8}$/) { $tag = 'Acquires_merge'; $data = "WBPaper$data"; }
        elsif ($data =~ m/^pmid(\d+)$/) { $tag = "Database\t\"MEDLINE\"\t\"PMID\""; $data = $1; }
      }
      elsif ($table eq 'abstract') {  
        $abstracts .= "Longtext : \"WBPaper$joinkey\"\n\n$data\n\n***LongTextEnd***\n\n\n";
        $data = "WBPaper$joinkey";
      }
      elsif ($table eq 'author') {  
        my $aid = $data;
        next unless ($indices{author}{$aid});		# must have an author
        next unless ($indices{author}{$aid} =~ m/\S/);	# author must have a word in it
unless ($indices{author}{$aid}) { print "ERROR author_id missing $aid in paper WBPaper$joinkey\n"; }
        if ($indices{person}{$aid}) { $data = "$indices{author}{$aid}\"\tPerson\t\"$indices{person}{$aid}"; }
          else { $data = $indices{author}{$aid}; }
      }
      elsif ($table eq 'erratum_in') {  
        $data = 'WBPaper'. $data; 
      }
      elsif ($table eq 'gene') {  
        $data = 'WBGene'. $data;
        if ($hash{$table}{$joinkey}{$order}{evi}) {		# if there's evidence column
          my $evi = $hash{$table}{$joinkey}{$order}{evi};
          unless ($evi =~ m/Manually_connected/) {		# skip evidence for Manually_connected tag not in acedb
            $evi =~ s/\"$//;					# strip out last doublequote for print below
            $data .= "\"\t$evi"; } }				# append closing quote, tab, evi
      }
      elsif ($table eq 'type') {  
        my $curator = $hash{$table}{$joinkey}{$order}{curator};
        $curator =~ s/two/WBPerson/;
        $data = "$indices{type}{$data}\"\tPerson_evidence\t\"$curator";
      }
      elsif ($table eq 'curation_flags') {  
        next unless ($data eq 'Phenotype2GO');
      }
# unless ($data) { print "ERROR NO DATA $tag $joinkey\n"; }
      if ($data) {
        print "$tag\t\"$data\"\n";
      }
    } # foreach my $order (sort keys %{ $hash{$table}{$joinkey} })
  } # foreach my $table (@normal_tables)
  my ($author, $year, $journal, $title);
  if ($hash{author}{$joinkey}{1}{data}) { 
    if ($indices{author}{$hash{author}{$joinkey}{1}{data}}) { 
      $author = $indices{author}{$hash{author}{$joinkey}{1}{data}}; } 
    if ($hash{author}{$joinkey}{2}{data}) { $author .= " et al."; }
  }
  if ($hash{year}{$joinkey}{NULL}{data}) { $year = $hash{year}{$joinkey}{NULL}{data}; }
  if ($hash{journal}{$joinkey}{NULL}{data}) { $journal = $hash{journal}{$joinkey}{NULL}{data}; }
  if ($hash{title}{$joinkey}{NULL}{data}) { $title = $hash{title}{$joinkey}{NULL}{data}; }
  my ($brief_citation) = &getEimearBriefCitation( $author, $year, $journal, $title );
  if ($brief_citation) { print "Brief_citation\t\"$brief_citation\"\n"; }

} # foreach my $joinkey (sort keys %{ $hash{status} })

print "\n\n$abstracts";

  

# special stuff :
# author author_index


# SELECT wpa_author_verified.author_id, wpa_author_possible.wpa_author_possible, wpa_author_verified.wpa_author_verified FROM wpa_author_verified, wpa_author_possible WHERE wpa_author_verified.wpa_author_verified ~ 'YES' AND wpa_author_possible.wpa_author_possible ~ 'two' AND wpa_author_verified.author_id = wpa_author_possible.author_id AND wpa_author_verified.wpa_join = wpa_author_possible.wpa_join;

# special tables :
# gene -> need evidence : joinkey, gene, order, curator, timestamp, evidence
# electronic_path -> from electronic_path_type, which has wpa_type instead of order
# author_index -> author_id instead of joinkey
# author_possible -> author_id instead of joinkey
# author_sent -> author_id instead of joinkey
# author_verified -> author_id instead of joinkey
# type_index -> index, type_id instead of joinkey


sub getEimearBriefCitation {
  my ($author, $year, $journal, $title) = @_;
  my $brief_citation = '';
  my $brief_title = '';                     # brief title (70 chars or less)
  if ($title) {
    $title =~ s/"//g;			# some titles properly have doublequotes but don't want them in brief citation
    my @chars = split //, $title;
    if ( scalar(@chars) < 70 ) {
        $brief_title = $title;
    } else {
        my $i = 0;                            # letter counter (want less than 70)
        my $word = '';                        # word to tack on (start empty, add characters)
        while ( (scalar(@chars) > 0) && ($i < 70) ) { # while there's characters, and less than 70 been read
            $brief_title .= $word;            # add the word, because still good (first time empty)
            $word = '';                       # clear word for next time new word is used
            my $char = shift @chars;          # read a character to start / restart check
            while ( (scalar(@chars) > 0) && ($char ne ' ') ) {        # while not a space and still chars
                $word .= $char; $i++;         # build word, add to counter (less than 70)
                $char = shift @chars;         # read a character to check if space
            } # while ($_ ne '')              # if it's a space, exit loop
            $word .= ' ';                     # add a space at the end of the word
        } # while ( (scalar(@chars) > 0) && ($i < 70) )
        $brief_title = $brief_title . "....";
    } }
  if ($author) { if ( length($author) > 0) { $brief_citation .= $author; } }
  if ($year) { 
    if ($year =~ m/ -C .*$/) { $year =~ s/ -C .*$//g; }
    if ( length($year) > 0) { $brief_citation .= " ($year)"; } }
  if ($journal) { 
    $journal =~ s/"//g;			# some journals are messed up and have doublequotes
    if ( length($journal) > 0) { $brief_citation .= " $journal"; } }
  if ($brief_title) { if ( length($brief_title) > 0) { $brief_citation .= " \\\"$brief_title\\\""; } }
  if ($brief_citation) { return $brief_citation; }
} # sub getEimearBriefCitation


sub filterAce {
  my $identifier = shift;
  my $comment = '';
  if ($identifier =~ m/-COMMENT (.*)/) { $comment = $1; $identifier =~ s/-COMMENT .*//; }
  if ($identifier =~ m/HTTP:\/\//i) { $identifier =~ s/HTTP:\/\//PLACEHOLDERASDF/ig; }
  if ($identifier =~ m/\//) { $identifier =~ s/\//\\\//g; }
  if ($identifier =~ m/\"/) { $identifier =~ s/\"/\\\"/g; }
#   if ($identifier =~ m/\\\/\\\//) { $identifier =~ s/\\\/\\\//" "/g; }	# convert // into " " for old pages / volume
  if ($identifier =~ m/\s+$/) { $identifier =~ s/\s+$//; }
  if ($identifier =~ m/PLACEHOLDERASDF/) { $identifier =~ s/PLACEHOLDERASDF/HTTP:\\\/\\\//g; }
  if ($identifier =~ m/;/) { $identifier =~ s/;/\\;/g; }
  if ($identifier =~ m/%/) { $identifier =~ s/%/\\%/g; }
  if ($comment) {
    if ($identifier =~ m/[^"]$/) { $identifier .= "\" "; }
    $identifier .= "-C \"$comment"; }
  return $identifier;
} # sub filterAce


__END__

my %primary_data;		# primary data or not
$primary_data{1} = 'primary';		# Journal_article
$primary_data{11} = 'primary';		# Letter
$primary_data{14} = 'primary';		# Published_erratum
$primary_data{2} = 'not_primary';	# Review
$primary_data{5} = 'not_primary';	# Book_chatper
$primary_data{6} = 'not_primary';	# News
$primary_data{8} = 'not_primary';	# Book
$primary_data{9} = 'not_primary';	# Historical_article
$primary_data{10} = 'not_primary';	# Comment
$primary_data{12} = 'not_primary';	# Monograph
$primary_data{13} = 'not_primary';	# Editorial
$primary_data{15} = 'not_primary';	# Retracted_publication
$primary_data{16} = 'not_primary';	# Technical_report
$primary_data{18} = 'not_primary';	# WormBook
$primary_data{19} = 'not_primary';	# Interview
$primary_data{20} = 'not_primary';	# Lectures
$primary_data{21} = 'not_primary';	# Congresses
$primary_data{22} = 'not_primary';	# Interactive_tutorial
$primary_data{23} = 'not_primary';	# Biography
$primary_data{24} = 'not_primary';	# Directory
$primary_data{3} = 'not_designated';	# Meeting_abstract
$primary_data{4} = 'not_designated';	# Gazette_article
$primary_data{7} = 'not_designated';	# Email
$primary_data{17} = 'not_designated';	# Other


# non-xml to copy over :  abstract  affiliation  author  a/i a/p a/s a/v  contained_in/contains  editor  electronic_path_type -> electronic_path   fulltext_url  gene  identifier  ignore  publisher  remark   rnai_int_done/rnai_curation/transgene_curation/allele_curation -> curation_flags  status
# unless-xml to copy over :  journal  pages  title  volume  year  type  primary_data (based on type)
# ``manual'' add erratum_in/erratum_for


# special tables :
# gene -> need evidence : joinkey, gene, order, curator, timestamp, evidence
# electronic_path -> from electronic_path_type, which has wpa_type instead of order
# author_index -> author_id instead of joinkey
# author_possible -> author_id instead of joinkey
# author_sent -> author_id instead of joinkey
# author_verified -> author_id instead of joinkey
# type_index -> index, type_id instead of joinkey

# author_index author_possible author_sent author_verified electronic_path gene type_index

my @pap_tables = qw( abstract affiliation author contained_in editor fulltext_url identifier ignore journal pages publisher pubmed_final remark title type volume year month day erratum_in internal_comment curation_flags primary_data status );


# &populateStatusIdentifier();

my %idents;
my %all_ids;
$result = $dbh->prepare( "SELECT * FROM pap_identifier" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) {
  $all_ids{$row[0]}{$row[1]}++;
  if ($row[1] =~ m/pmid(\d+)/) { $idents{$1} = $row[0]; }
}


# &populateFromXml();		# populate paper data from pubmed xml
# &populateUnlessXml();		# populate data from wpa for fields that would be gotten from xml
# &populateExtraTypes();	# only run after populateFromXml + populateUnlessXML, populate manual Kimberly data for Type information that is not in XML / unlessXml
# &populateNonXml();		# populate data from wpa for fields that do not exist in xml (and are not special tables)
# &populateAuthorSub();		# populate author index/possible/sent/verified data (special tables)
# &populateGene();		# populate gene data (special table)
# &populateCurationFlags();	# populate curation flags (special table) from rnai_curation / rnai_int_done / p2go
# &populateElectronicPath();	# populate electronic path data (special table)
# &checkAffiliationWrong();	# some affiliation stuff wasn't getting in because of non-utf8 characters
# &getOddJournals();		# not necessary, for Kimberly to extract odd journals
# &populateTypeIndex();		# only run once, to populate type index
# &populateErratum();		# only run once, populate erratum_in table from manual stuff

sub populateCurationFlags {
#   my @curation_flags = qw( rnai_int_done rnai_curation );
  my @curation_flags = qw( rnai_curation );	# got rid of rnai_int_done, not being used 2011 05 03
  
  $result = $dbh->do( "DELETE FROM h_pap_curation_flags" );
  $result = $dbh->do( "DELETE FROM pap_curation_flags" );

  my %hash; my %data;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'");	
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  foreach my $type (@curation_flags) {
    $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );	# in order to store latest timestamp (up to gary what we store ?)
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);	# these two tables are always valid, and data order is always null
      $data{$row[0]}{$type}{curator} = $row[4];
      $data{$row[0]}{$type}{timestamp} = $row[5]; } }

  $data{"00004402"}{"phenotype2GO"}{"curator"} = "two1843";	# manual ranjana / kimberly data
  $data{"00004403"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00004540"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00004651"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00004769"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00005599"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00005654"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00006395"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00024497"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00024925"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00025054"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00026763"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00005736"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00026593"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00028783"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00029254"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00030951"}{"phenotype2GO"}{"curator"} = "two1843";

#   my @data_types = qw( rnai_curation rnai_int_done phenotype2GO );
  my @data_types = qw( rnai_curation phenotype2GO );		# got rid of rnai_int_done, not being used 2011 05 03
  foreach my $joinkey (sort keys %{ $hash{status} }) {
    my $order = 0;
    foreach my $type (@data_types) {
      next unless ($data{$joinkey}{$type}{curator});
      $order++;
      my $curator = $data{$joinkey}{$type}{curator};
      my $timestamp = 'CURRENT_TIMESTAMP';
      if ($data{$joinkey}{$type}{timestamp}) {
        $timestamp = "'$data{$joinkey}{$type}{timestamp}'"; }

#       print "$joinkey\t$type\t$order\t$curator\t$timestamp\n";
      $result = $dbh->do( "INSERT INTO pap_curation_flags VALUES ('$joinkey', '$type', $order, '$curator', $timestamp)" );
      $result = $dbh->do( "INSERT INTO h_pap_curation_flags VALUES ('$joinkey', '$type', $order, '$curator', $timestamp)" );
    }
  } # foreach my $type (@curation_flags)
} # sub populateCurationFlags


sub populateAuthorSub {		# populate author index/possible/sent/verified data (special tables)
  my @subtables = qw( index possible sent verified );

  my %hash;

  foreach my $type (@subtables) {
    $result = $dbh->do( "DROP TABLE h_pap_author_$type" );
    $result = $dbh->do( "DROP TABLE pap_author_$type" );

    my $papt = 'pap_author_' . $type;
    $result = $dbh->do( "CREATE TABLE $papt ( author_id text, $papt text, pap_join integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
    $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (author_id);" );
    $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );
    
    $result = $dbh->do( "CREATE TABLE h_$papt ( author_id text, $papt text, pap_join integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
    $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON $papt USING btree (author_id);" );
    $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );

    $result = $dbh->prepare( "SELECT * FROM wpa_author_$type ORDER BY wpa_timestamp" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);
      unless ($row[2]) { $row[2] = 'NULL'; }
      if ($type eq 'index') { $row[2] = 'NULL'; }
      if ($row[3] eq 'valid') { 
          $hash{$row[0]}{$row[2]}{$type}{$row[1]}{data} = $row[1];
          if ($row[4]) { $hash{$row[0]}{$row[2]}{$type}{$row[1]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$row[0]}{$row[2]}{$type}{$row[1]}{timestamp} = $row[5]; } }
        else { 
          delete $hash{$row[0]}{$row[2]}{$type}{$row[1]}; } }
  }

# print "T $type\n";
  foreach my $author_id (sort keys %hash) {
# int "AID $author_id\n";
    my $count = 0;
    foreach my $join (sort keys %{ $hash{$author_id} }) {
# int "JOIN $join\n";
      my $order = 'NULL';
      if ($join ne 'NULL') { $count++; $order = "'$count'"; }
      foreach my $type (sort keys %{ $hash{$author_id}{$join} }) {
        my $papt = 'pap_author_' . $type;
        my %tempHash;			# a given aid + join will sometimes have multiple data, so only store the latest one by storing by timestamp and getting reverse keys sort
# my @data = keys %{ $hash{$author_id}{$join}{$type} };
# if (scalar(@data) > 1) { print "ERR " . scalar(@data) . " for $author_id $order $type\n"; }
        foreach my $data (sort keys %{ $hash{$author_id}{$join}{$type} }) {
          next unless $data;
          my $curator = $hash{$author_id}{$join}{$type}{$data}{curator};
          my $timestamp = $hash{$author_id}{$join}{$type}{$data}{timestamp};
          my $time = $timestamp; $time =~ s/\D//g; 
          ($data) = &filterForPg($data);
          unless ($curator) { 
            print "NO CURATOR $author_id T $type D $data\n"; 
            $curator = 'two1841'; }
          unless ($timestamp) { 
            print "NO TIMESTAMP $author_id T $type D $data\n"; }
          $tempHash{$timestamp}{curator} = $curator;
          $tempHash{$timestamp}{data} = $data;
#           print "DATA\t$type\t$author_id\t$data\t$order\t$curator\t$timestamp\n";
          $result = $dbh->do( "INSERT INTO h_$papt VALUES ('$author_id', '$data', $order, '$curator', '$timestamp')" );		# enter all (valid) data to history
        }
        foreach my $timestamp (reverse sort keys %tempHash) {	# get the most recent timestamp off of reverse alpha sort
          my $curator = $tempHash{$timestamp}{curator};
          my $data = $tempHash{$timestamp}{data};
#           print "FINAL\t$type\t$author_id\t$data\t$order\t$curator\t$timestamp\n";
          $result = $dbh->do( "INSERT INTO $papt VALUES ('$author_id', '$data', $order, '$curator', '$timestamp')" );			# enter most recent data to current field
          last;				# only get the latest value, so skip all others
        }
  } } } 
} # sub populateAuthorSub

sub populateGene {		# put locus in evidence column "Inferred_manually"
  $result = $dbh->do( "DROP TABLE h_pap_gene" );
  $result = $dbh->do( "DROP TABLE pap_gene" );

  my $papt = 'pap_gene';
  $result = $dbh->do( "CREATE TABLE $papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone , pap_evidence text)" ); 
  $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );
  
  $result = $dbh->do( "CREATE TABLE h_$papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone , pap_evidence text)" ); 
  $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON h_$papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  my $type = 'gene';
  $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    next unless ($row[1]);
    unless ($row[2]) { $row[2] = 'NULL'; }
    my $key = "$row[1]KEY$row[2]";
    if ($row[3] eq 'valid') { 
        $hash{$type}{$row[0]}{$key}{data} = $row[1];
        if ($row[4]) { $hash{$type}{$row[0]}{$key}{curator} = $row[4]; }
        if ($row[5]) { $hash{$type}{$row[0]}{$key}{timestamp} = $row[5]; } }
      else { 
        delete $hash{$type}{$row[0]}{$key}; } }

  my %stuff; 				# use this hash to filter new Manually_connected evidence to store locus where it wasn't Inferred_automatically (instead of in the gene column)
  foreach my $joinkey (sort keys %{ $hash{status} }) {
    foreach my $key (sort keys %{ $hash{$type}{$joinkey} }) {
      my ($genedata, $evi) = split/KEY/, $key;
      my ($geneid) = $genedata =~ m/WBGene(\d+)/;
      next unless ($geneid); 		# there's 3 entries without any data
      my $locus = '';
      if ($genedata =~ m/\(([^\(\)]*?)\)/) {	# if there's a locus (innermost stuff in parenthesis)
        $locus = $1; 
# print "J $joinkey KEY $key G $geneid L $locus E $evi C $hash{$type}{$joinkey}{$key}{curator} T $hash{$type}{$joinkey}{$key}{timestamp} E\n";
        if ($evi =~ m/$locus/) { 		# the locus mentioned in evidence, stays the same
            $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
            $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
          else { # if ($evi =~ m/$locus/)	# locus not in evidence
            if ($evi =~ m/Inferred_automatically\t\"(.*?)\"/) {	# if inferred automatically, add to evidence
                $evi = "Inferred_automatically\t\"$locus $1\"";
                $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
                $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
              else { 				# not inferred automatically, store it
                $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
                $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp};
                $evi = "Manually_connected\t\"$locus\""; 		# and also add manual
                $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
                $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
        } # else # if ($evi =~ m/$locus/)	
      } # if ($genedata =~ m/\((.*?)\)/)
      else {	# if there is no locus, store the entry
        $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
        $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
    } # foreach my $gene_data (sort keys %{ $hash{$type}{$joinkey} })
  } # foreach my $joinkey (sort keys %{ $hash{status} })

  foreach my $joinkey (sort keys %stuff) {
    my $count = 0;
    foreach my $geneid (sort keys %{ $stuff{$joinkey} }) {
      foreach my $evi (sort keys %{ $stuff{$joinkey}{$geneid} }) {
        $count++; my $order = "'$count'";
        my $curator = $stuff{$joinkey}{$geneid}{$evi}{curator};
        my $timestamp = $stuff{$joinkey}{$geneid}{$evi}{timestamp};
        if ($evi ne 'NULL') { $evi = "'$evi'"; }
#         print "GENE\t$joinkey\t$geneid\t$order\t$curator\t$timestamp\t$evi\n";
        $result = $dbh->do( "INSERT INTO pap_gene VALUES ('$joinkey', '$geneid', $order, '$curator', '$timestamp', $evi)" );
        $result = $dbh->do( "INSERT INTO h_pap_gene VALUES ('$joinkey', '$geneid', $order, '$curator', '$timestamp', $evi)" );
      } # foreach my $evi (sort keys %{ $stuff{$joinkey}{$geneid} })
    } # foreach my $geneid (sort keys %{ $stuff{$joinkey} })
  } # foreach my $joinkey (sort keys %stuff)
} # sub populateGene


sub populateElectronicPath {		# should we split locus into another column, strip, or leave as is ?
  $result = $dbh->do( "DROP TABLE h_pap_electronic_path" );
  $result = $dbh->do( "DROP TABLE pap_electronic_path" );

  my $papt = 'pap_electronic_path';
  $result = $dbh->do( "CREATE TABLE $papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
  $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );
  
  $result = $dbh->do( "CREATE TABLE h_$papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
  $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON h_$papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  my $type = 'electronic_path_type';
  $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    next unless ($row[1]);
    if ($row[3] eq 'valid') { 
        $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
        if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
        if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } }
      else { 
        $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
        if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
        if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } } }

  foreach my $joinkey (sort keys %{ $hash{status} }) {
    my $count = 0;
    foreach my $pdf_type (sort keys %{ $hash{$type}{$joinkey} }) {
      foreach my $data (sort keys %{ $hash{$type}{$joinkey}{$pdf_type} }) {
        next unless $data;
        my $curator = $hash{$type}{$joinkey}{$pdf_type}{$data}{curator};
        my $timestamp = $hash{$type}{$joinkey}{$pdf_type}{$data}{timestamp};
        $count++; my $order = "'$count'"; 
        ($data) = &filterForPg($data);
        unless ($curator) { 
#           print "NO CURATOR $joinkey T $type D $data\n"; 
          $curator = 'two1841'; }
#         print "$type\t$joinkey\t$data\t$order\t$curator\t$timestamp\n";
        $result = $dbh->do( "INSERT INTO $papt VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
        $result = $dbh->do( "INSERT INTO h_$papt VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
  } } }
} # sub populateElectronicPath


sub populateNonXml {		# populate tables that have data not in xml (and are not special)
#   my @not_xml_tables = qw( abstract affiliation author contained_in editor fulltext_url ignore publisher remark erratum_in internal_comment curation_flags );	# internal_comment and curation_flags are new tables, erratum_in is currently unclear because wiki says 3 entries, but type 14 says 21 entries, so ignoring it.
  my @not_xml_tables = qw( abstract affiliation author contained_in editor fulltext_url ignore publisher remark );
  foreach my $type (@not_xml_tables) {
#     if ($multi{$type}) { print "MULTI $type\n"; }
    $result = $dbh->do( "DELETE FROM pap_$type;" );
    $result = $dbh->do( "DELETE FROM h_pap_$type;" ); }

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  foreach my $type (@not_xml_tables) {
    $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);
      unless ($row[2]) { $row[2] = 'NULL'; }
      if ($row[3] eq 'valid') { 
          $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } }
        else { 
          $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } } }

    foreach my $joinkey (sort keys %{ $hash{status} }) {
      my $count = 0;
      foreach my $old_order (sort keys %{ $hash{$type}{$joinkey} }) {
        foreach my $data (sort keys %{ $hash{$type}{$joinkey}{$old_order} }) {
          next unless $data;
          my $curator = $hash{$type}{$joinkey}{$old_order}{$data}{curator};
          my $timestamp = $hash{$type}{$joinkey}{$old_order}{$data}{timestamp};
          my $order = "NULL"; 
          if ($single{$type}) { 1; }
            elsif ($multi{$type}) { 
              if ($old_order ne "NULL") { $order = "'$old_order'"; }
                else { $count++; $order = "'$count'"; } }
            else { print "ERR neither single nor multi $type\n"; }
          ($data) = &filterForPg($data);
          unless ($curator) { 
#             print "NO CURATOR $joinkey T $type D $data\n"; 
            $curator = 'two1841'; }
#           print "$type\t$joinkey\t$data\t$order\t$curator\t$timestamp\n";
          $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
          $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
    } } }
  } # foreach my $type (@not_xml_tables)
} # sub populateNonXml

sub populateUnlessXml {		# populate stuff that would normally come from xml for papers that don't have pmid 
  my @unique_ref = qw( title journal volume pages year primary_data type );
#   my @unique_ref = qw( type primary_data );
  foreach my $type (@unique_ref) {
    $result = $dbh->do( "DELETE FROM pap_$type WHERE joinkey IN (SELECT joinkey FROM pap_status WHERE pap_status = 'valid' AND joinkey NOT IN (SELECT joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid'));" );
    $result = $dbh->do( "DELETE FROM h_pap_$type WHERE joinkey IN (SELECT joinkey FROM pap_status WHERE pap_status = 'valid' AND joinkey NOT IN (SELECT joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid'));" ); }

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid' AND joinkey NOT IN (SELECT joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid'); ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  foreach my $type (@unique_ref) {
    next if ($type eq 'primary_data');	# infer this from type
    $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
# if ($row[0] eq '00005120') { print "ROW @row ROW\n"; }
# if ($row[0] eq '00024942') { print "ROW @row ROW\n"; }
      if ($row[3] eq 'valid') { 
          $hash{$type}{$row[0]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{timestamp} = $row[5]; } }
        else { 
          $hash{$type}{$row[0]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{timestamp} = $row[5]; } }
    }

    foreach my $joinkey (sort keys %{ $hash{status} }) {
# if ($joinkey eq '00005120') { print "IN ROW\n"; }
# if ($joinkey eq '00024942') { print "IN ROW\n"; }
      next unless $hash{$type}{$joinkey}{data};
      my $data = $hash{$type}{$joinkey}{data};
      my $curator = $hash{$type}{$joinkey}{curator};
      my $timestamp = $hash{$type}{$joinkey}{timestamp};
# if ($joinkey eq '00005120') { print "DATA $data $curator $timestamp\n"; }
# if ($joinkey eq '00024942') { print "DATA $data $curator $timestamp\n"; }
      my $order = "NULL";
      if ($type eq 'type') { 
        my $primary_data = '';
        if ($primary_data{$data}) { $primary_data = $primary_data{$data}; }
        $order = "'1'";	 
#         print "Joinkey\t$joinkey\tPrimary\t$primary_data\n"; 
        $result = $dbh->do( "INSERT INTO pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', '$timestamp')" );
        $result = $dbh->do( "INSERT INTO h_pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', '$timestamp')" );
      }		# order only exists for type, and is always 1 since there's no previous data
#       if ( ($type eq 'type') && ( ($data ne '3') && ($data ne '4') ) ) { print "NEWTYPE\n"; }
      ($data) = &filterForPg($data);
#       print "$type\t$joinkey\t$data\t$curator\t$timestamp\n";
      $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
      $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
    }
  }
} # sub populateUnlessXml

sub populateFromXml {		# POPULATE SOME REFERENCE FROM XML, not dealing with type
#   my @unique_ref = qw( title journal volume pages year month day affiliation pubmed_final primary_data type );	# kimberly doesn't want affiliation from xml
  my @unique_ref = qw( title journal volume pages year month day pubmed_final primary_data type );
  foreach my $type (@unique_ref) {
    $result = $dbh->do( "DELETE FROM pap_$type;" );
    $result = $dbh->do( "DELETE FROM h_pap_$type;" );
  }

#   my %affi;
#   
#   $result = $dbh->prepare( "SELECT * FROM pap_affiliation" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { $affi{$row[0]} = $row[1]; }

  my %month_to_num;
  $month_to_num{Jan} = '1';
  $month_to_num{Feb} = '2';
  $month_to_num{Mar} = '3';
  $month_to_num{Apr} = '4';
  $month_to_num{May} = '5';
  $month_to_num{Jun} = '6';
  $month_to_num{Jul} = '7';
  $month_to_num{Aug} = '8';
  $month_to_num{Sep} = '9';
  $month_to_num{Oct} = '10';
  $month_to_num{Nov} = '11';
  $month_to_num{Dec} = '12';

  my %type_index;		# type to type_index mapping
  $type_index{"Journal_article"} = '1';  
  $type_index{"Review"} = '2';  
  $type_index{"Meeting_abstract"} = '3';  
  $type_index{"Gazette_article"} = '4';  
  $type_index{"Book_chapter"} = '5';  
  $type_index{"News"} = '6';  
  $type_index{"Email"} = '7';  
  $type_index{"Book"} = '8';  
  $type_index{"Historical_article"} = '9';  
  $type_index{"Comment"} = '10'; 
  $type_index{"Letter"} = '11'; 
  $type_index{"Monograph"} = '12'; 
  $type_index{"Editorial"} = '13'; 
  $type_index{"Published_erratum"} = '14'; 
  $type_index{"Retracted_publication"} = '15'; 
  $type_index{"Technical_report"} = '16'; 
  $type_index{"Other"} = '17'; 
  $type_index{"Wormbook"} = '18'; 
  $type_index{"Interview"} = '19'; 
  $type_index{"Lectures"} = '20'; 
  $type_index{"Congresses"} = '21'; 
  $type_index{"Interactive_tutorial"} = '22'; 
  $type_index{"Biography"} = '23'; 
  $type_index{"Directory"} = '24'; 

  my %specific_type;		# types that don't become "Other" and aren't only Journal_article
  $specific_type{2} = 'Review';
  $specific_type{6} = 'News';
  $specific_type{9} = 'Historical_article';
  $specific_type{10} = 'Comment';
  $specific_type{11} = 'Letter';
  $specific_type{12} = 'Monograph';
  $specific_type{13} = 'Editorial';
  $specific_type{14} = 'Published_erratum';
  $specific_type{15} = 'Retracted_publication';
  $specific_type{16} = 'Technical_report';
  $specific_type{19} = 'Interview';
  $specific_type{20} = 'Lectures';
  $specific_type{21} = 'Congresses';
  $specific_type{22} = 'Interactive_tutorial';
  $specific_type{23} = 'Biography';
  $specific_type{24} = 'Directory';
  
  $/ = undef;
  my (@xml) = </home/postgres/work/pgpopulation/wpa_papers/wpa_pubmed_final/xml/*>;
  my (@done_xml) = </home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/done/*>;
  foreach (@done_xml) { push @xml, $_; }
  foreach my $xml (@xml) {		# foreach xml that we have
    my ($id) = $xml =~ m/\/(\d+)$/;
    open (IN, "<$xml") or die "Cannot open $xml : $!";
    my $xml_data = <IN>;
    close (IN) or die "Cannot close $xml : $!";
    my ($title) = $xml_data =~ /\<ArticleTitle\>(.+?)\<\/ArticleTitle\>/i;
    my ($journal) = $xml_data =~ /<MedlineTA>(.+?)\<\/MedlineTA\>/i;
    my ($pages) = $xml_data =~ /\<MedlinePgn\>(.+?)\<\/MedlinePgn\>/i;
    my ($volume) = $xml_data =~ /\<Volume\>(.+?)\<\/Volume\>/i;
    my $year = ''; my $month = ''; my $day = '';
    if ( $xml_data =~ /\<PubDate\>(.+?)\<\/PubDate\>/i ) {
      my ($PubDate) = $xml_data =~ /\<PubDate\>(.+?)\<\/PubDate\>/i;
      if ( $PubDate =~ /\<Year\>(.+?)\<\/Year\>/i ) { $year = $1; }
      if ( $PubDate =~ /\<Month\>(.+?)\<\/Month\>/i ) { $month = $1; 
        if ($month_to_num{$month}) { $month = $month_to_num{$month}; } }
      if ( $PubDate =~ /\<Day\>(.+?)\<\/Day\>/i ) { $day = $1; } }
    my ($abstract) = $xml_data =~ /\<AbstractText\>(.+?)\<\/AbstractText\>/i;
#     my ($affiliation) = $xml_data =~ /\<Affiliation\>(.+?)\<\/Affiliation\>/i;
    my (@types) = $xml_data =~ /\<PublicationType\>(.+?)\<\/PublicationType\>/gi;
    ($title) = &filterForPg($title);
    ($journal) = &filterForPg($journal);
    ($pages) = &filterForPg($pages);
    ($volume) = &filterForPg($volume);
    ($year) = &filterForPg($year);
    ($month) = &filterForPg($month);
    ($day) = &filterForPg($day);
#     ($affiliation) = &filterForPg($affiliation);
    ($abstract) = &filterForPg($abstract);
    foreach (@types) { ($_) = &filterForPg($_); }
    my $pubmed_final = 'not_final';
    if ($xml_data =~ /\<MedlineCitation Owner=\"NLM\" Status=\"MEDLINE\"\>/) { $pubmed_final = 'final'; }
#   my ($doi) = $page =~ /\<ArticleId IdType=\"doi\"\>(.+?)\<\/ArticleId\>/i; $doi = 'doi' . $doi;
  
    my $curator = 'two10877';		# pubmed
    my $timestamp = 'CURRENT_TIMESTAMP';
  
    unless ($id) { print "XML $xml END\n"; }
  
    if ($idents{$id}) {		# if the pmid maps to a wbpaper joinkey
      my $joinkey = $idents{$id};
#       next unless $affiliation;
#       unless ($affi{$joinkey}) { print "$joinkey\t$id\t$affiliation\n"; }
#     print "Title $joinkey $id $title\n";
      if ($title) {
        $result = $dbh->do( "INSERT INTO pap_title VALUES ('$joinkey', '$title', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_title VALUES ('$joinkey', '$title', NULL, '$curator', $timestamp)" ); }
      if ($journal) {
        $result = $dbh->do( "INSERT INTO pap_journal VALUES ('$joinkey', '$journal', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_journal VALUES ('$joinkey', '$journal', NULL, '$curator', $timestamp)" ); }
      if ($pages) {
        $result = $dbh->do( "INSERT INTO pap_pages VALUES ('$joinkey', '$pages', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_pages VALUES ('$joinkey', '$pages', NULL, '$curator', $timestamp)" ); }
      if ($volume) {
        $result = $dbh->do( "INSERT INTO pap_volume VALUES ('$joinkey', '$volume', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_volume VALUES ('$joinkey', '$volume', NULL, '$curator', $timestamp)" ); }
      if ($year) {
        $result = $dbh->do( "INSERT INTO pap_year VALUES ('$joinkey', '$year', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_year VALUES ('$joinkey', '$year', NULL, '$curator', $timestamp)" ); }
      if ($month) {
        $result = $dbh->do( "INSERT INTO pap_month VALUES ('$joinkey', '$month', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_month VALUES ('$joinkey', '$month', NULL, '$curator', $timestamp)" ); }
      if ($day) {
        $result = $dbh->do( "INSERT INTO pap_day VALUES ('$joinkey', '$day', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_day VALUES ('$joinkey', '$day', NULL, '$curator', $timestamp)" ); }
#       if ($affiliation) {
#         $result = $dbh->do( "INSERT INTO pap_affiliation VALUES ('$joinkey', '$affiliation', NULL, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO h_pap_affiliation VALUES ('$joinkey', '$affiliation', NULL, '$curator', $timestamp)" ); }
      if ($pubmed_final) {
        $result = $dbh->do( "INSERT INTO pap_pubmed_final VALUES ('$joinkey', '$pubmed_final', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_pubmed_final VALUES ('$joinkey', '$pubmed_final', NULL, '$curator', $timestamp)" ); }
      if ($types[0]) {
        my %types;
        foreach my $type (@types) {
            ($type) = ucfirst(lc($type)); $type =~ s/\s+/_/g;
          if ($type_index{$type}) { 
            my $type_id = $type_index{$type};
            $types{$type_id}++;
# print "Joinkey\t$joinkey\tType\t$type\t$type_id\n"; 
          }	# else { $types{17}++; }	# other ????
        } # foreach my $type (@types)
        my $primary_data = '';
        my @actual_types;
        foreach my $type_id (keys %types) { 	# for each type_id, if it's specific, use that type_id
          if ($specific_type{$type_id}) { push @actual_types, $type_id; } }
        unless ($actual_types[0]) { 		# if there are no specific types and it's journal, use that
          if ($types{1}) { push @actual_types, 1; } }
        unless ($actual_types[0]) { 		# if there are no types, use Other
          push @actual_types, 17; }
        my $count = 0;
        foreach my $type_id (@actual_types) {
          $count++;
          $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '$type_id', '$count', '$curator', $timestamp)" );
          $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '$type_id', '$count', '$curator', $timestamp)" );
          if ($primary_data{$type_id}) {		# if there's a primary_data entry for this type_id
            next if $primary_data eq 'primary';		# skip if already primary
            if ($primary_data{$type_id} eq 'primary') { $primary_data = $primary_data{$type_id}; next; }
            next if $primary_data eq 'not_primary';	# skip if already not_primary
            if ($primary_data{$type_id} eq 'not_primary') { $primary_data = $primary_data{$type_id}; next; }
            $primary_data = $primary_data{$type_id};	# assign to not_designated by default
          }
# print "Joinkey\t$joinkey\tTypeID\t$type_id\n"; 
        }
# print "Joinkey\t$joinkey\tPrimary\t$primary_data\n"; 
        $result = $dbh->do( "INSERT INTO pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', $timestamp)" );
      } # if ($type)
    } # if ($idents{$id})
  
#   print "ID $id\n";
  } # foreach my $xml (@xml)
  $/ = "\n";
} # sub populateFromXml

sub populateExtraTypes {
  my %extraBook_chapter;
  $extraBook_chapter{"00002172"}++;
  $extraBook_chapter{"00002244"}++;
  $extraBook_chapter{"00002245"}++;
  $extraBook_chapter{"00002246"}++;
  $extraBook_chapter{"00002247"}++;
  $extraBook_chapter{"00002248"}++;
  $extraBook_chapter{"00002249"}++;
  $extraBook_chapter{"00002250"}++;
  $extraBook_chapter{"00002251"}++;
  $extraBook_chapter{"00002252"}++;
  $extraBook_chapter{"00002253"}++;
  $extraBook_chapter{"00002254"}++;
  $extraBook_chapter{"00002255"}++;
  $extraBook_chapter{"00002256"}++;
  $extraBook_chapter{"00002257"}++;
  $extraBook_chapter{"00002258"}++;
  $extraBook_chapter{"00002259"}++;
  $extraBook_chapter{"00002260"}++;
  $extraBook_chapter{"00002261"}++;
  $extraBook_chapter{"00002262"}++;
  $extraBook_chapter{"00002263"}++;
  $extraBook_chapter{"00002264"}++;
  $extraBook_chapter{"00002265"}++;
  $extraBook_chapter{"00002266"}++;
  $extraBook_chapter{"00002267"}++;
  $extraBook_chapter{"00002268"}++;
  $extraBook_chapter{"00002269"}++;
  $extraBook_chapter{"00024687"}++;
  $extraBook_chapter{"00029144"}++;
  $extraBook_chapter{"00031351"}++;
  $extraBook_chapter{"00032010"}++;

  my %extraBook_chapterAndWormBook;
  $extraBook_chapterAndWormBook{"00027222"}++;
  $extraBook_chapterAndWormBook{"00027223"}++;
  $extraBook_chapterAndWormBook{"00027224"}++;
  $extraBook_chapterAndWormBook{"00027225"}++;
  $extraBook_chapterAndWormBook{"00027226"}++;
  $extraBook_chapterAndWormBook{"00027227"}++;
  $extraBook_chapterAndWormBook{"00027228"}++;
  $extraBook_chapterAndWormBook{"00027229"}++;
  $extraBook_chapterAndWormBook{"00027230"}++;
  $extraBook_chapterAndWormBook{"00027231"}++;
  $extraBook_chapterAndWormBook{"00027232"}++;
  $extraBook_chapterAndWormBook{"00027233"}++;
  $extraBook_chapterAndWormBook{"00027234"}++;
  $extraBook_chapterAndWormBook{"00027235"}++;
  $extraBook_chapterAndWormBook{"00027236"}++;
  $extraBook_chapterAndWormBook{"00027237"}++;
  $extraBook_chapterAndWormBook{"00027238"}++;
  $extraBook_chapterAndWormBook{"00027239"}++;
  $extraBook_chapterAndWormBook{"00027240"}++;
  $extraBook_chapterAndWormBook{"00027241"}++;
  $extraBook_chapterAndWormBook{"00027242"}++;
  $extraBook_chapterAndWormBook{"00027243"}++;
  $extraBook_chapterAndWormBook{"00027244"}++;
  $extraBook_chapterAndWormBook{"00027245"}++;
  $extraBook_chapterAndWormBook{"00027246"}++;
  $extraBook_chapterAndWormBook{"00027247"}++;
  $extraBook_chapterAndWormBook{"00027248"}++;
  $extraBook_chapterAndWormBook{"00027249"}++;
  $extraBook_chapterAndWormBook{"00027250"}++;
  $extraBook_chapterAndWormBook{"00027251"}++;
  $extraBook_chapterAndWormBook{"00027252"}++;
  $extraBook_chapterAndWormBook{"00027253"}++;
  $extraBook_chapterAndWormBook{"00027254"}++;
  $extraBook_chapterAndWormBook{"00027255"}++;
  $extraBook_chapterAndWormBook{"00027256"}++;
  $extraBook_chapterAndWormBook{"00027257"}++;
  $extraBook_chapterAndWormBook{"00027258"}++;
  $extraBook_chapterAndWormBook{"00027259"}++;
  $extraBook_chapterAndWormBook{"00027260"}++;
  $extraBook_chapterAndWormBook{"00027261"}++;
  $extraBook_chapterAndWormBook{"00027262"}++;
  $extraBook_chapterAndWormBook{"00027263"}++;
  $extraBook_chapterAndWormBook{"00027264"}++;
  $extraBook_chapterAndWormBook{"00027265"}++;
  $extraBook_chapterAndWormBook{"00027266"}++;
  $extraBook_chapterAndWormBook{"00027267"}++;
  $extraBook_chapterAndWormBook{"00027268"}++;
#   $extraBook_chapterAndWormBook{"00027269"}++;	# MISSING ?
  $extraBook_chapterAndWormBook{"00027270"}++;
  $extraBook_chapterAndWormBook{"00027271"}++;
  $extraBook_chapterAndWormBook{"00027272"}++;
  $extraBook_chapterAndWormBook{"00027273"}++;
  $extraBook_chapterAndWormBook{"00027274"}++;
  $extraBook_chapterAndWormBook{"00027275"}++;
  $extraBook_chapterAndWormBook{"00027276"}++;
  $extraBook_chapterAndWormBook{"00027277"}++;
  $extraBook_chapterAndWormBook{"00027278"}++;
  $extraBook_chapterAndWormBook{"00027279"}++;
  $extraBook_chapterAndWormBook{"00027280"}++;
  $extraBook_chapterAndWormBook{"00027281"}++;
  $extraBook_chapterAndWormBook{"00027282"}++;
  $extraBook_chapterAndWormBook{"00027283"}++;
  $extraBook_chapterAndWormBook{"00027284"}++;
  $extraBook_chapterAndWormBook{"00027285"}++;
  $extraBook_chapterAndWormBook{"00027286"}++;
  $extraBook_chapterAndWormBook{"00027287"}++;
  $extraBook_chapterAndWormBook{"00027288"}++;
  $extraBook_chapterAndWormBook{"00027289"}++;
  $extraBook_chapterAndWormBook{"00027290"}++;
  $extraBook_chapterAndWormBook{"00027291"}++;
  $extraBook_chapterAndWormBook{"00027292"}++;
  $extraBook_chapterAndWormBook{"00027293"}++;
  $extraBook_chapterAndWormBook{"00027294"}++;
  $extraBook_chapterAndWormBook{"00027295"}++;
  $extraBook_chapterAndWormBook{"00027296"}++;
  $extraBook_chapterAndWormBook{"00027297"}++;
  $extraBook_chapterAndWormBook{"00027298"}++;
  $extraBook_chapterAndWormBook{"00027299"}++;
  $extraBook_chapterAndWormBook{"00027300"}++;
  $extraBook_chapterAndWormBook{"00027301"}++;
  $extraBook_chapterAndWormBook{"00027302"}++;
  $extraBook_chapterAndWormBook{"00027304"}++;
  $extraBook_chapterAndWormBook{"00027305"}++;
  $extraBook_chapterAndWormBook{"00027306"}++;
  $extraBook_chapterAndWormBook{"00027307"}++;
  $extraBook_chapterAndWormBook{"00027309"}++;
  $extraBook_chapterAndWormBook{"00027310"}++;
  $extraBook_chapterAndWormBook{"00027311"}++;
  $extraBook_chapterAndWormBook{"00027312"}++;
  $extraBook_chapterAndWormBook{"00027313"}++;
  $extraBook_chapterAndWormBook{"00027314"}++;
  $extraBook_chapterAndWormBook{"00027315"}++;
  $extraBook_chapterAndWormBook{"00027316"}++;
  $extraBook_chapterAndWormBook{"00027317"}++;
  $extraBook_chapterAndWormBook{"00027318"}++;
  $extraBook_chapterAndWormBook{"00027319"}++;
  $extraBook_chapterAndWormBook{"00029012"}++;
  $extraBook_chapterAndWormBook{"00029016"}++;
  $extraBook_chapterAndWormBook{"00029019"}++;
  $extraBook_chapterAndWormBook{"00029022"}++;
  $extraBook_chapterAndWormBook{"00029033"}++;
  $extraBook_chapterAndWormBook{"00031286"}++;
  $extraBook_chapterAndWormBook{"00031287"}++;
  $extraBook_chapterAndWormBook{"00031288"}++;
  $extraBook_chapterAndWormBook{"00031289"}++;
  $extraBook_chapterAndWormBook{"00031290"}++;
  $extraBook_chapterAndWormBook{"00031291"}++;
  $extraBook_chapterAndWormBook{"00031292"}++;
  $extraBook_chapterAndWormBook{"00031388"}++;
  $extraBook_chapterAndWormBook{"00031293"}++;
  $extraBook_chapterAndWormBook{"00031414"}++;
  $extraBook_chapterAndWormBook{"00031415"}++;
  $extraBook_chapterAndWormBook{"00031646"}++;
  $extraBook_chapterAndWormBook{"00032172"}++;
  $extraBook_chapterAndWormBook{"00032226"}++;
  $extraBook_chapterAndWormBook{"00032944"}++;
  $extraBook_chapterAndWormBook{"00035143"}++;
  $extraBook_chapterAndWormBook{"00035958"}++;

  my %type;
  $result = $dbh->prepare( "SELECT * FROM pap_type" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    $type{$row[1]}{$row[0]}++;
    if ($type{amount}{$row[0]}) {
      if ($type{amount}{$row[0]} < $row[2]) { $type{amount}{$row[0]} = $row[2]; } }
    else { $type{amount}{$row[0]} = $row[2]; }
  }

  my $curator = 'two1843';
  my $timestamp = 'CURRENT_TIMESTAMP';
  foreach my $joinkey (sort {$a<=>$b} keys %extraBook_chapter) {
    my $order = $type{amount}{$joinkey}; 
    if ($type{5}{$joinkey}) { print "Already 5 in $joinkey\n"; }
      else { $order++;
        print "$joinkey\t5\t$order\ttwo1843\tCurrent\n";
#         $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" ); 
    }
  }
  foreach my $joinkey (sort {$a<=>$b} keys %extraBook_chapterAndWormBook) {
    my $order = $type{amount}{$joinkey}; 
    if ($type{5}{$joinkey}) { print "Already 5 in $joinkey\n"; }
      else { $order++;
        print "$joinkey\t5\t$order\ttwo1843\tCurrent\n";
#         $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" ); 
    }
    if ($type{18}{$joinkey}) { print "Already 18 in $joinkey\n"; }
      else { $order++;
        print "$joinkey\t18\t$order\ttwo1843\tCurrent\n";
#         $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '18', $order, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '18', $order, '$curator', $timestamp)" ); 
    }
  }
} # sub populateExtraTypes

sub populateStatusIdentifier {		# TO POPULATE THE TABLES : status, identifier
  foreach my $table (@pap_tables) { 
    $result = $dbh->do( "DELETE FROM h_pap_$table" );
    $result = $dbh->do( "DELETE FROM pap_$table" ); }
  
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{status}{$row[0]}{valid} = 'valid';
        $hash{status}{$row[0]}{data} = $row[1];
        if ($row[4]) { $hash{status}{$row[0]}{curator} = $row[4]; }
        if ($row[5]) { $hash{status}{$row[0]}{timestamp} = $row[5]; } }
      else { 
        $hash{status}{$row[0]}{valid} = 'invalid';
        $hash{status}{$row[0]}{data} = $row[1];
        if ($row[4]) { $hash{status}{$row[0]}{curator} = $row[4]; }
        if ($row[5]) { $hash{status}{$row[0]}{timestamp} = $row[5]; }
#         my (@values) = keys %{ $hash{status}{$row[0]} };
#         if (scalar @values < 1) { delete $hash{status}{$row[0]}; }
      }
  } # while (my @row = $result->fetchrow)
  
  $result = $dbh->prepare( "SELECT * FROM wpa_identifier ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{identifier}{$row[0]}{$row[1]}{curator} = $row[4];
        $hash{identifier}{$row[0]}{$row[1]}{timestamp} = $row[5]; }
      else { delete $hash{identifier}{$row[0]}{$row[1]}; }
  } # while (my @row = $result->fetchrow)

  my $type = 'status';
  foreach my $joinkey (sort keys %{ $hash{$type} }) {
    my $data = $hash{$type}{$joinkey}{data};
    my $valid = $hash{$type}{$joinkey}{valid};
    my $curator = $hash{$type}{$joinkey}{curator};
    my $timestamp = $hash{$type}{$joinkey}{timestamp};
#       print "$joinkey\t$data\t$curator\t$timestamp\n";
    $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$valid', NULL, '$curator', '$timestamp')" );
    $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$valid', NULL, '$curator', '$timestamp')" );
  }

  my %badPmid;			# no xml in pubmed
  $badPmid{'pmid12591608'}++;
  $badPmid{'pmid14532430'}++;
  $badPmid{'pmid14532626'}++;
  $badPmid{'pmid14532629'}++;
  $badPmid{'pmid14532633'}++;
  $badPmid{'pmid14532635'}++;
  $badPmid{'pmid14731937'}++;
  $badPmid{'pmid15577917'}++;
  $badPmid{'pmid15817570'}++;
  $badPmid{'pmid15902193'}++;
  $badPmid{'pmid16551030'}++;
  $badPmid{'pmid16551054'}++;
  $badPmid{'pmid16652241'}++;
  $badPmid{'pmid17154166'}++;
  $badPmid{'pmid17154292'}++;
  $badPmid{'pmid17169184'}++;
  $badPmid{'pmid17407201'}++;
  $badPmid{'pmid18023125'}++;
  $badPmid{'pmid18050406'}++;
  $badPmid{'pmid18050420'}++;
  $badPmid{'pmid18548071'}++;
  $badPmid{'pmid18677322'}++;
  $badPmid{'pmid18692560'}++;
  $badPmid{'pmid18711361'}++;
  $badPmid{'pmid18725909'}++;
  $badPmid{'pmid18841162'}++;
  $badPmid{'pmid94222994'}++;

  
  $type = 'identifier';
  foreach my $joinkey (sort keys %{ $hash{$type} }) {
    next unless ($hash{status}{$joinkey});
    next unless ($hash{status}{$joinkey}{valid} eq 'valid');
    my $order = 0;
    foreach my $data (sort keys %{ $hash{$type}{$joinkey} } ) {
      next unless $data;
      next if ($badPmid{$data});
      $order++;
      my $curator = $hash{$type}{$joinkey}{$data}{curator};
      my $timestamp = $hash{$type}{$joinkey}{$data}{timestamp};
#         print "$joinkey\t$data\t$curator\t$timestamp\n";
      $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$data', '$order', '$curator', '$timestamp')" );
      $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$data', '$order', '$curator', '$timestamp')" );
    }
  }
} # sub populateStatusIdentifier

sub populateErratum {
  my %erratum_in;
  $erratum_in{"00001805"}{"00001892"}++;
  $erratum_in{"00003297"}{"00003344"}++;
  $erratum_in{"00003297"}{"00003456"}++;
  $erratum_in{"00003302"}{"00003457"}++;
  $erratum_in{"00003600"}{"00003688"}++;
  $erratum_in{"00003222"}{"00003750"}++;
  $erratum_in{"00003638"}{"00003800"}++;
  $erratum_in{"00004137"}{"00004301"}++;
  $erratum_in{"00004835"}{"00005285"}++;
  $erratum_in{"00005127"}{"00005304"}++;
  $erratum_in{"00005344"}{"00005412"}++;
  $erratum_in{"00004978"}{"00005701"}++;
  $erratum_in{"00005292"}{"00005746"}++;
  $erratum_in{"00024886"}{"00024897"}++;
  $erratum_in{"00003297"}{"00026886"}++;
  $erratum_in{"00024920"}{"00026902"}++;
  $erratum_in{"00026758"}{"00026911"}++;
  $erratum_in{"00026636"}{"00027056"}++;
  $erratum_in{"00026959"}{"00027096"}++;
  $erratum_in{"00031151"}{"00031373"}++;
  $erratum_in{"00030896"}{"00032419"}++;
  my $curator = 'two1843';
  my $timestamp = 'CURRENT_TIMESTAMP';
  foreach my $joinkey (sort keys %erratum_in) {
    my $order = 0;
    foreach my $erratum_in (sort keys %{ $erratum_in{$joinkey} }) {
      $order++;
      $result = $dbh->do( "INSERT INTO pap_erratum_in VALUES ('$joinkey', '$erratum_in', $order, '$curator', $timestamp)" );
      $result = $dbh->do( "INSERT INTO h_pap_erratum_in VALUES ('$joinkey', '$erratum_in', $order, '$curator', $timestamp)" );
    }
  }
} # sub populateErratum


sub populateTypeIndex {
  $result = $dbh->do( "DELETE FROM h_pap_type_index" );
  $result = $dbh->do( "DELETE FROM pap_type_index" ); 
  
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM wpa_type_index ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{type_index}{$row[0]}{$row[1]}{curator} = $row[4];
        $hash{type_index}{$row[0]}{$row[1]}{timestamp} = $row[5]; }
      else { 
        delete $hash{type_index}{$row[0]}{$row[1]}; 
        my (@values) = keys %{ $hash{type_index}{$row[0]} };
        if (scalar @values < 1) { delete $hash{type_index}{$row[0]}; } } }
  
  foreach my $type (sort keys %hash) {
    foreach my $type_id (sort {$a<=>$b} keys %{ $hash{$type} }) {
      foreach my $data (sort keys %{ $hash{$type}{$type_id} } ) {
        next unless $data;
        my $curator = $hash{$type}{$type_id}{$data}{curator};
        my $timestamp = $hash{$type}{$type_id}{$data}{timestamp};
        print "$type_id\t$data\t$curator\t$timestamp\n";
        $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$type_id', '$data', NULL, '$curator', '$timestamp')" );
        $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$type_id', '$data', NULL, '$curator', '$timestamp')" );
} } } } # sub populateTypeIndex



sub getOddJournals {		# GET list of journals that are in valid papers, but aren't in pubmed
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }
  
  $result = $dbh->prepare( "SELECT * FROM pap_journal" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    $hash{journal}{$row[0]} = $row[1]; 
    $hash{existingjournal}{$row[1]}++; }
  
  $result = $dbh->prepare( "SELECT * FROM wpa_type ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{wpatype}{$row[0]}{$row[1]}++; }
      else { delete $hash{wpatype}{$row[0]}{$row[1]}; }
  } # while (my @row = $result->fetchrow)
  
  $result = $dbh->prepare( "SELECT * FROM wpa_journal ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{wpajournal}{$row[0]}{$row[1]}++; }
      else { delete $hash{wpajournal}{$row[0]}{$row[1]}; }
  } # while (my @row = $result->fetchrow)
  
  
  my %odd_journals;
  foreach my $joinkey (sort keys %{ $hash{status} }) {
    next if ($hash{journal}{$joinkey});
    next unless ($hash{wpatype}{$joinkey}{1});
    if ($hash{wpajournal}{$joinkey}) { 
      foreach my $journal (keys %{ $hash{wpajournal}{$joinkey} }) {
        next if ($hash{existingjournal}{$journal});
        $odd_journals{ $journal }{ $joinkey }++; 
  } } }
  foreach my $odd_journal (sort keys %odd_journals) {
    my @paps;
    foreach my $joinkey ( sort keys %{ $odd_journals{$odd_journal} } ) {
      my @ids = sort keys %{ $all_ids{$joinkey} };
      my $ids = join", ", @ids;
      push @paps, "$joinkey ( $ids )";
    }
    my $count = scalar(@paps);
    my $paps = join"\t", @paps;
    print "$odd_journal\t$count\t$paps\n";
  } # foreach my $odd_journal (sort keys %odd_journals)
} # sub getOddJournals

sub checkAffiliationWrong {
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM pap_affiliation" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{$row[0]} = $row[1]; }

  $/ = undef;
  my (@xml) = </home/postgres/work/pgpopulation/wpa_papers/wpa_pubmed_final/xml/*>;
  my (@done_xml) = </home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/done/*>;
  foreach (@done_xml) { push @xml, $_; }
  foreach my $xml (@xml) {
    my ($id) = $xml =~ m/\/(\d+)$/;
    open (IN, "<$xml") or die "Cannot open $xml : $!";
    my $xml_data = <IN>;
    close (IN) or die "Cannot close $xml : $!";
    my ($affiliation) = $xml_data =~ /\<Affiliation\>(.+?)\<\/Affiliation\>/i;
    next unless $affiliation;
    if ($idents{$id}) {
      my $joinkey = $idents{$id};
      unless ($hash{$joinkey}) { print "$joinkey\t$id\t$affiliation\n"; }
    }
  }
  $/ = "\n";
} # sub checkAffiliationWrong



__END__


# TO CREATE THE TABLES

# foreach my $table (@pap_tables) { 
#   $result = $dbh->do( "DROP TABLE h_pap_$table" );
#   $result = $dbh->do( "DROP TABLE pap_$table" ); }

foreach my $table (@pap_tables) {
  my $papt = 'pap_' . $table;
  $result = $dbh->do( "CREATE TABLE $papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone )" ); 
  $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );

  
  $result = $dbh->do( "CREATE TABLE h_$papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone )" ); 
  $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON h_$papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );
} # foreach my $table (@pap_tables)

__END__


abstract
affiliation
# allele_curation	# not really used
author
author_index
author_possible
author_sent
author_verified
# checked_out		# FP probably, not needed anymore
# comments		# rename as internal_comment 
contained_in
contains
# date_published	# only 5 entries, gone
editor
# electronic_path_md5	# not used
# electronic_path_type	# replaced with electronic path type
electronic_path
# electronic_type_index	# not used ?
# erratum		# gone need erratum_in / erratum_for
fulltext_url		# the URLs are here and dump to remark tag in .ace
gene
# hardcopy
identifier
ignore			# functional annotation only / non worm
# in_book		# gone, replaced by contained_in / contains
journal
# keyword		# need to dump these into static .ace file for constant appending post-dump
# nematode_paper	# possibly taxon in the future, gone for now
pages
publisher
pubmed_final
remark
# rnai_curation		# move into curation flags
# rnai_int_done		# move into curation flags
title
# transgene_curation	# not really used
type
type_index
volume
year

new :
erratum_in
erratum_for
internal_comment	# populate with  comments
curation_flags		# flag for ``Phenotype2GO'' or blank / rnai_curation # got rid of rnai_int_done, not being used 2011 05 03
primary_data		# primary data / no primary data / not designated
status			# replaces wpa for valid / invalid for whole paper

# affiliation in paper model.  also in #affiliation on author tag, but no longer in postgres author data, and not dumped.

__END__

$result = $dbh->do( "DROP VIEW pap_view" ); 
my @old_pap = qw( pap_affiliation pap_contained pap_email pap_journal pap_paper pap_possible pap_type pap_year pap_author pap_contains pap_inbook pap_page pap_pmid pap_title pap_verified pap_volume );
foreach my $table (@old_pap) { $result = $dbh->do( "DROP TABLE $table" ); }

__END__

my @pap_tables = qw( passwd celegans cnonbristol nematode nonnematode genestudied genesymbol extvariation mappingdata newmutant rnai lsrnai overexpr chemicals mosaic siteaction timeaction genefunc humdis geneint funccomp geneprod otherexpr microarray genereg seqfeat matrices antibody transgene marker invitro domanal covalent structinfo massspec structcorr seqchange newsnp ablationdata cellfunc phylogenetic othersilico supplemental nocuratable comment );


my %dataTable = ();
$dataTable{passwd} = 'passwd';
$dataTable{celegans} = '';
$dataTable{cnonbristol} = '';
$dataTable{nematode} = 'nematode';
$dataTable{nonnematode} = '';
$dataTable{genestudied} = 'rgngene';
$dataTable{genesymbol} = 'genesymbol';
$dataTable{extvariation} = '';
$dataTable{mappingdata} = 'mappingdata';
$dataTable{newmutant} = 'newmutant';
$dataTable{rnai} = 'rnai';
$dataTable{lsrnai} = 'lsrnai';
$dataTable{overexpr} = 'overexpression';
$dataTable{chemicals} = 'chemicals';
$dataTable{mosaid} = 'mosaid';
$dataTable{siteaction} = 'site';
$dataTable{timeaction} = '';
$dataTable{genefunc} = 'genefunction';
$dataTable{humdis} = 'humandiseases';
$dataTable{geneint} = 'geneinteractions';
$dataTable{funccomp} = '';			# functionalcomplementation was in cur_ not in afp_ 
$dataTable{geneprod} = 'geneproduct';
$dataTable{otherexpr} = 'expression';
$dataTable{microarray} = 'microarray';
$dataTable{genereg} = 'generegulation';
$dataTable{seqfeat} = 'sequencefeatures';
$dataTable{matrices} = '';
$dataTable{antibody} = 'antibody';
$dataTable{transgene} = 'transgene';
$dataTable{marker} = '';
$dataTable{invitro} = 'invitro';
$dataTable{domanal} = 'structureinformation';
$dataTable{covalent} = 'covalent';
$dataTable{structinfo} = 'structureinformation';
$dataTable{massspec} = 'massspec';
$dataTable{structcorr} = 'structurecorrectionsanger';
$dataTable{seqchange} = 'sequencechange';
$dataTable{newsnp} = 'newsnp';
$dataTable{ablationdata} = 'ablationdata';
$dataTable{cellfunc} = 'cellfunction';
$dataTable{phylogenetic} = 'phylogenetic';
$dataTable{othersilico} = 'othersilico';
$dataTable{supplemental} = 'supplemental';
$dataTable{nocuratable} = 'review';
$dataTable{comment} = 'comment';

# UNCOMMENT to repopulate afp_ tables from original dumps.  2009 03 21
# foreach my $table (@afp_tables) {
#   my $table2 = 'afp_' . $table ;
#   $result = $conn->exec("DROP TABLE $table2; ");
#   $result = $conn->exec( "CREATE TABLE $table2 ( joinkey text, $table2 text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text), afp_curator text, afp_approve text, afp_cur_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE UNIQUE INDEX ${table2}_idx ON $table2 USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table2 FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO cecilia; ");
#   my $table3 = $table . '_hst';
#   $result = $conn->exec("DROP TABLE $table3; ");
#   $result = $conn->exec( "CREATE TABLE $table3 ( joinkey text, $table3 text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text), afp_curator text, afp_approve text, afp_cur_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE INDEX ${table3}_idx ON $table3 USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table3 FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO cecilia; ");
#   if ($dataTable{$table}) { 
#     my $infile = "/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_$dataTable{$table}.pg";
#     open (IN, "<$infile") or die "Cannot open $infile : $!";
#     while (my $line = <IN>) {
#       chomp $line;
#       my ($joinkey, $data, $timestamp) = split/\t/, $line;
#       $data =~ s/\'/''/g;  $data =~ s/\\r\\n/\n/g;	# replace singlequotes and newlines
#       $result = $conn->exec( "INSERT INTO afp_$table VALUES ( '$joinkey', '$data', '$timestamp', NULL, NULL, NULL)" );
#       $result = $conn->exec( "INSERT INTO afp_${table}_hst VALUES ( '$joinkey', '$data', '$timestamp', NULL, NULL, NULL)" );
#     } # while (my $line = <IN>)
#     close (IN) or die "Cannot close $infile : $!";
# #     $result = $conn->exec( "COPY afp_$table FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_$dataTable{$table}.pg'" );
# #     $result = $conn->exec( "COPY afp_${table}_hst FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_$dataTable{$table}.pg'" ); 
#   } # if ($dataTable{$table}) 
# } # foreach my $table (@afp_tables)

# afp_ablationdata.pg               afp_humandiseases.pg              afp_passwd.pg
# afp_antibody.pg                   afp_invitro.pg                    afp_phylogenetic.pg
# afp_cellfunction.pg               afp_lsrnai.pg                     afp_review.pg
# afp_chemicals.pg                  afp_mappingdata.pg                afp_rgngene.pg
# afp_comment.pg                    afp_massspec.pg                   afp_rnai.pg
# afp_covalent.pg                   afp_microarray.pg                 afp_sequencechange.pg
# afp_expression.pg                 afp_mosaic.pg                     afp_sequencefeatures.pg
# afp_genefunction.pg               afp_nematode.pg                   afp_site.pg
# afp_geneinteractions.pg           afp_newmutant.pg                  afp_structurecorrectionsanger.pg
# afp_geneproduct.pg                afp_newsnp.pg                     afp_structureinformation.pg
# afp_generegulation.pg             afp_othersilico.pg                afp_supplemental.pg
# afp_genesymbol.pg                 afp_overexpression.pg             afp_transgene.pg

__END__


my @tables = qw( genesymbol mappingdata genefunction newmutant rnai lsrnai geneinteractions geneproduct expression sequencefeatures generegulation overexpression mosaic site microarray invitro covalent structureinformation structurecorrectionsanger sequencechange massspec ablationdata cellfunction phylogenetic othersilico chemicals transgene antibody newsnp rgngene nematode humandiseases supplemental review comment );

my @newtables = qw( matrices timeaction celegans cnonbristol nematode nonnematode nocuratable domanal structcorr structinfo genestudied extvariation funccomp otherexpr marker siteaction email genefunc geneint geneprod seqfeat genereg overexpr seqchange cellfunc humdis );

my @tomove = qw( rgngene functionalcomplementation structureinformation structurecorrection site timeofaction domainanalysis otherexpression genefunction geneinteractions geneproduct sequencefeatures generegulation overexpression sequencechange cellfunction humandiseases );

my %moveHash;
# to delete
$moveHash{'siteofaction'} = 'siteaction';
$moveHash{'timeofaction'} = 'timeaction';
$moveHash{'domainanalysis'} = 'domanal';
$moveHash{'otherexpression'} = 'otherexpr';
$moveHash{'fxncomp'} = 'funccomp';
$moveHash{'genefunction'} = 'genefunc';
$moveHash{'geneinteractions'} = 'geneint';
$moveHash{'geneproduct'} = 'geneprod';
$moveHash{'sequencefeatures'} = 'seqfeat';
$moveHash{'generegulation'} = 'genereg';
$moveHash{'overexpression'} = 'overexpr';
$moveHash{'sequencechange'} = 'seqchange';
$moveHash{'cellfunction'} = 'cellfunc';
$moveHash{'humandiseases'} = 'humdis';

# foreach my $table (keys %moveHash) {
#   my $result = $conn->exec( "DROP TABLE afp_$table " );
#   $result = $conn->exec( "DROP TABLE afp_${table}_hst " );
# } # foreach my $table (keys %moveHash)

# to move
# $moveHash{'site'} = 'siteaction';
# $moveHash{'overexpression'} = 'overexpr';
# $moveHash{'genefunction'} = 'genefunc';
# $moveHash{'geneinteractions'} = 'geneint';
# $moveHash{'geneproduct'} = 'geneprod';
# $moveHash{'sequencefeatures'} = 'seqfeat';
# $moveHash{'generegulation'} = 'genereg';
# $moveHash{'overexpression'} = 'overexpr';
# $moveHash{'sequencechange'} = 'seqchange';
# $moveHash{'cellfunction'} = 'cellfunc';
# $moveHash{'humandiseases'} = 'humdis';

# foreach my $table (keys %moveHash) {
#   my $new = $moveHash{$table}; $new = 'afp_' . $new;
#   my $result = $conn->exec( "COPY $new FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_${table}.pg'" );
#   $result = $conn->exec( "COPY ${new}_hst FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_${table}.pg'" );
# }

# afp_ablationdata.pg      afp_geneproduct.pg     afp_mosaic.pg          afp_rgngene.pg
# afp_antibody.pg          afp_generegulation.pg  afp_nematode.pg        afp_rnai.pg
# afp_cellfunction.pg      afp_genesymbol.pg      afp_newmutant.pg       afp_sequencechange.pg
# afp_chemicals.pg         afp_humandiseases.pg   afp_newsnp.pg          afp_sequencefeatures.pg
# afp_comment.pg           afp_invitro.pg         afp_othersilico.pg     afp_site.pg
# afp_covalent.pg          afp_lsrnai.pg          afp_overexpression.pg  afp_structurecorrectionsanger.pg
# afp_expression.pg        afp_mappingdata.pg     afp_passwd.pg          afp_structureinformation.pg
# afp_genefunction.pg      afp_massspec.pg        afp_phylogenetic.pg    afp_supplemental.pg
# afp_geneinteractions.pg  afp_microarray.pg      afp_review.pg          afp_transgene.pg



my $table = 'afp_passwd_hst';
my $result = '';

# foreach my $table (@newtables) {
#   $table = 'afp_' . $table ;
#   $result = $conn->exec( "CREATE TABLE $table ( joinkey text, $table text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE UNIQUE INDEX ${table}_idx ON $table USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO cecilia; ");
#   my $table2 = $table . '_hst';
#   $result = $conn->exec( "CREATE TABLE $table2 ( joinkey text, $table2 text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE INDEX ${table2}_idx ON $table2 USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table2 FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO cecilia; ");
# }


# foreach my $table (@tables) {
#   $table = 'afp_' . $table;
#   $result = $conn->exec( "COPY $table TO '/home/postgres/work/pgpopulation/afp_papers/orig_tables/${table}.pg'" );
#   my $table2 = $table . '_hst';
#   $result = $conn->exec( "COPY $table2 FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/${table}.pg'" );
# }

# # my $result = $conn->exec( "DROP TABLE $table" );
# $result = $conn->exec( "CREATE TABLE $table ( joinkey text, $table numeric(17,7), afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
# $result = $conn->exec( "CREATE INDEX ${table}_idx ON $table USING btree (joinkey);" );
# $result = $conn->exec("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO postgres; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO acedb; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO apache; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO azurebrd; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO cecilia; ");
# 
# foreach my $table (@tables) {
#   $table = 'afp_' . $table . '_hst';
# #   $result = $conn->exec( "DROP TABLE $table" );
#   $result = $conn->exec( "CREATE TABLE $table ( joinkey text, $table text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE INDEX ${table}_idx ON $table USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO cecilia; ");
# }

__END__

my $result = $conn->exec( "SELECT * FROM one_groups;" );
while (my @row = $result->fetchrow) {
  if ($row[0]) { 
    $row[0] =~ s///g;
    $row[1] =~ s///g;
    $row[2] =~ s///g;
    print "$row[0]\t$row[1]\t$row[2]\n";
  } # if ($row[0])
} # while (@row = $result->fetchrow)



__DIVIDER__


use strict;
use CGI;
use Fcntl;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 


my $query = new CGI;

# use Pg;
# my $conn = Pg::connectdb("dbname=testdb");
# die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;

my $frontpage = 1;
my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color


my %type_index;				# hash of possible 7 types of paper
my %electronic_type_index;		# hash of possible 7 types of electronic paper
&populateTypeIndex();	

# my @generic_tables = qw( title publisher journal volume pages year abstract affiliation comments paper );

my @generic_tables = qw( wpa wpa_identifier wpa_title wpa_publisher wpa_journal wpa_volume wpa_pages wpa_year wpa_date_published wpa_fulltext_url wpa_abstract wpa_affiliation wpa_type wpa_author wpa_hardcopy wpa_comments wpa_editor wpa_nematode_paper wpa_contained_in wpa_contains wpa_keyword wpa_erratum wpa_in_book );


&printHeader('WBPaper Display');
&display();
&printFooter();

sub display {
  my $action;

  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); }
  } else { $frontpage = 0; }

  if ($action eq 'Number !') { &pickNumber(); }
  elsif ($action eq 'Author !') { &pickAuthor(); }
  elsif ($action eq 'Title !') { &pickTitle(); }
  else { 1 }
} # sub display

sub pickNumber {
  my ($oop, $number) = &getHtmlVar($query, 'number');
  unless ($number) { $number = 1; }	# sometimes no number or zero would cause a serverlog error on next line
  print "NUMBER : $number<P>\n";
  my $result = $dbh->prepare( "SELECT wpa_valid FROM wpa WHERE joinkey = '$number' ORDER BY wpa_timestamp DESC;" );  
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow;
  if ($row[0] eq 'invalid') { 
    my $identifier = ''; $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ '$number' ORDER BY wpa_timestamp;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $identifier = $row[0]; } else { $identifier = ''; } }
    print "<FONT COLOR='red' SIZE=+2>NOT a valid paper, merged with $identifier.</FONT><P>\n"; }
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }
  $result = $dbh->prepare( "SELECT * FROM wpa WHERE wpa = '$number'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  @row = $result->fetchrow;
  if ($row[0]) { &displayOneDataFromKey($number); }
  else { 
    print "There is no exact match for WBPaper $number<BR>\n"; 
    my %xref_type;
    my $result = $dbh->prepare( "SELECT * FROM wpa_identifier; "); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my %xref;
    while (my @row = $result->fetchrow) {
      $row[0] =~ s/\D//g;
      $xref{full}{$row[1]}{$row[0]}++;
      my ($xref_type) = $row[1] =~ m/(^\D+)/;
      $xref_type{$xref_type}++;
      $row[1] =~ s/\D//g;
      $xref{num}{$row[1]}{$row[0]}++;
    } # while (my @row = $result->fetchrow)
    my ($number_type) = $number =~ m/^(\D+)/;
    if ($xref_type{$number_type}) { 	# matches type e.g. cgc
      print "There are $xref_type{$number_type} wpa_identifier that match the paper type '$number_type'.<BR>\n";
      if ($xref{full}{$number}) {
        foreach my $joinkey ( sort keys %{ $xref{full}{$number} } ) {
          print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$joinkey&action=Number+%21\">wbpaper id : $joinkey</A><BR>\n"; } } }
    else {				# doesn't match type
      $number =~ s/\D+//g;
      foreach my $joinkey ( sort keys %{ $xref{num}{$number} } ) {
        print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$joinkey&action=Number+%21\">wbpaper id : $joinkey</A><BR>\n"; } }
  }
} # sub pickNumber

sub pickAuthor {
  my ($oop, $author) = &getHtmlVar($query, 'author');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %authors;
  my %matches;
  print "AUTHOR : $author<P>\n";

  my $table_type = 'wpa_author_index';		# allow search by author_id 2006 04 20
  if ($author =~ m/^\d+$/) { $table_type = 'author_id'; }

  if ($exact_or_sub eq 'exact') {
    my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE $table_type = '$author' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $authors{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
    my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE $table_type ~ '$author' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $authors{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  foreach my $author_id (sort keys %authors) {
    my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE wpa_author = '$author_id' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
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
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      my @row = $result->fetchrow; my $title = $row[1];
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      @row = $result->fetchrow; my $journal = $row[1];
#       print "Matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$number&action=Number+%21\">wbpaper id : $number -> author id : $matches{$number} -> author name : $authors{ $matches{$number} } <BR>title : $title<BR>journal : $journal</A><BR>\n";
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$number&action=Number+%21\">$number</TD><TD>$matches{$number}</TD><TD>$authors{ $matches{$number} } </TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickAuthor

sub pickTitle {
  my ($oop, $title) = &getHtmlVar($query, 'title');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "TITLE : $title<P>\n";

  if ($exact_or_sub eq 'exact') {
    my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE wpa_title = '$title' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
    my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE wpa_title ~ '$title' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $title.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    foreach my $number (sort keys %matches) { 
      print "Matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$number&action=Number+%21\">wbpaper id $number -> title : $matches{$number}</A><BR>\n";
     }
  }
} # sub pickTitle


sub displayNormal { my $data = shift; print "  <TD>$data</TD>\n"; }
sub displayType { 
  my $data = shift; 
  if ($type_index{$data}) { $data = $type_index{$data}; }
  print "  <TD>$data</TD>\n"; 
} # sub displayType
sub displayAuthor { 
  my $data = shift; my $aname = '';
  my $result = $dbh->prepare( "SELECT wpa_author_index FROM wpa_author_index WHERE author_id = '$data' ORDER BY wpa_timestamp DESC; ");	# show the most recent one   2007 10 24
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); if ($row[0]) { $aname = $row[0]; }
  print "  <TD>$data ($aname)</TD>\n";
} # sub displayAuthor 
sub displayFullAuthor {
  my $joinkey = shift;
  my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE joinkey = '$joinkey' ORDER BY wpa_order;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my %auth_id;
  my %auth_name;
  while (my @row = $result->fetchrow) { $auth_id{$row[1]}++; }
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD ALIGN=CENTER>Affiliation</TD></TR>\n";
  foreach my $auth_id (sort keys %auth_id) {
    my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row2 = $result2->fetchrow) {
      $auth_name{$auth_id} = $row2[1];
      print "<TR bgcolor='$blue'>\n";
      print "<TD>$row2[1]</TD>";
      if ($row2[2]) { print "<TD>$row2[2]</TD>"; }
        else { print "<TD>&nbsp;</TD>"; }
      print "<TR>\n"; }
  } # foreach my $auth_id (@auth_id)
  print "</TABLE><BR><BR>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD>Possible</TD><TD>Sent</TD><TD>Verified</TD></TR>\n";
  foreach my $auth_id (sort keys %auth_id) {
    my %ceci_hash;
    my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_possible WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{possible} = $row[1]; }
    $result2 = $dbh->prepare( "SELECT * FROM wpa_author_sent WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{sent} = $row[1]; }
    $result2 = $dbh->prepare( "SELECT * FROM wpa_author_verified WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
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
} # sub displayFullAuthor

sub displayOneDataFromKey {
  my $wpa_id = shift;
  my ($joinkey) = &padZeros($wpa_id);

  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD COLSPAN=5>ID : $joinkey</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Data</TD><TD>Order</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  my $counter = 0;
  my $erratum = 0; my $in_book = 0;
  my $result = $dbh->prepare( "SELECT * FROM cur_curator WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow;
  if ($row[1]) { $row[1] =~ s/two/WBPerson/; print "This paper was first-pass curated by $row[1] on $row[2]<BR>\n"; }
    else { print "This paper has not been first-pass curated.<BR>\n"; }
  
  foreach my $pg_table (@generic_tables) {
    my $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY wpa_order;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my $bgcolor = $blue;
      if ($row[1]) {
        if ($row[3] eq 'invalid') { $bgcolor = $red; }
        if ($row[3] eq 'misattributed') { $bgcolor = $red; }
        print "<TR bgcolor='$bgcolor'>\n  <TD>$pg_table</TD>\n";
        if ($pg_table eq 'wpa_type') { &displayType($row[1]); }
        elsif ($pg_table eq 'wpa_author') { &displayAuthor($row[1]); }
        else { &displayNormal($row[1]); }
        unless ($row[2]) { $row[2] = '&nbsp;'; } print "  <TD>$row[2]</TD>\n";
        print "  <TD>$row[3]</TD>\n";
        print "  <TD>$row[4]</TD>\n";
        if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
        if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
        print "  <TD>$row[5]</TD>\n";
        print "</TR>\n";
        if ($pg_table eq 'wpa_erratum') { $erratum = $row[1]; }
        if ($pg_table eq 'wpa_in_book') { $in_book = $row[1]; }
      } # if ($row[1])
    } # while (my @row = $result->fetchrow)
  } # foreach my $wpa_table (@generic_tables)
  print "</TABLE><BR><BR>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  &displayFullAuthor($joinkey);
  &displayGene($joinkey);
  &getPdfLink($joinkey);

  if ($erratum) { print "<TR><TD>&nbsp;</TD></TR><TR><TD>Erratum : </TD></TR>\n"; &displayOneDataFromKey($erratum); }
  if ($in_book) { print "<TR><TD>&nbsp;</TD></TR><TR><TD>In Book : </TD></TR>\n"; &displayOneDataFromKey($in_book); }
  print "</TABLE><BR><BR>\n";
  print "Link to WormBase : <A HREF=http://www.wormbase.org/db/misc/paper?name=WBPaper$joinkey;class=Paper TARGET=new>WBPaper$joinkey</A><BR>\n";
} # sub displayOneDataFromKey

sub displayGene {
  my ($joinkey) = @_;
  my $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE joinkey = '$joinkey' ORDER BY wpa_gene, wpa_timestamp;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my $row_count = 0;
  my $pg_table = 'wpa_gene';
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Gene - CDS</TD><TD>Evidence</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  while (my @row = $result->fetchrow) {
    my $bgcolor = $blue;
    if ($row[1]) {
      if ($row[3] eq 'invalid') { $bgcolor = $red; }
      $row_count++;
      print "<TR bgcolor='$bgcolor'>\n";
      print "<TD>$row[1]</TD>\n";
      if ($row[2]) { print "  <TD>$row[2]</TD>\n"; } else { print "  <TD>&nbsp;</TD>\n"; }
      print "  <TD>$row[3]</TD>\n";
      print "  <TD>$row[4]</TD>\n";
      if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
      if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
      print "  <TD>$row[5]</TD>\n";
      print "</TR>\n";
    }
  } # while (my $row = $result->fetchrow)
} # sub displayGene


sub getPdfLink {
  my $joinkey = shift;
  my $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my $bgcolor = $blue;
  if ($result->fetchrow) {
    print "<TR><TD>&nbsp;</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Link</TD><TD>Type</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
    $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my $bgcolor = $blue;
      if ($row[1]) {
        if ($row[3] eq 'invalid') { $bgcolor = $red; }
        print "<TR bgcolor='$bgcolor'>\n  <TD>wpa_electronic_path_type</TD>\n";
        my ($pdf) = $row[1] =~ m/\/([^\/]*)$/;
        $pdf = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
        print "<TD><A HREF=$pdf>$pdf</A></TD>\n";
        print "  <TD>$electronic_type_index{$row[2]}</TD>\n";
        print "  <TD>$row[3]</TD>\n";
        print "  <TD>$row[4]</TD>\n";
        if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
        if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
        print "  <TD>$row[5]</TD>\n";
        print "</TR>\n";
      }
    } # while (my $row = $result->fetchrow)
  } # if ($result->fetchrow)
} # sub getPdfLink

sub firstPage {
  my $date = &getDate();
  print "Value : $date<BR>\n";
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi\">\n";
  print "<TABLE border=1 cellspacing=5>\n";
  print "<TR><TD>Number : <TD><INPUT SIZE=40 NAME=\"number\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Number !\"></TD>\n";
  print "<TD>Enter the wbpaper number for exact match ;  otherwise it will try to match the cgc, pmid, etc. ;  otherwise it will strip the non-number characters and try to match the number.</TR>\n";
  print "<TR><TD>Author : <TD><INPUT SIZE=40 NAME=\"author\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Author !\"></TD>\n";
  print "<TD>Enter an Author and select below whether to find an exact author (e.g. Sternberg PW) or a substring (e.g. Sternberg)</TR>\n";
  print "<TR><TD>Title : <TD><INPUT SIZE=40 NAME=\"title\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Title !\"></TD>\n";
  print "<TD>Enter a Title and select below whether to find an exact title (e.g. The pharynx of C. elegans.) or a substring (e.g. pharynx)</TR>\n";
  print "<TR><TD>Exact</TD><TD><INPUT NAME=\"exact_or_sub\" TYPE=\"radio\" VALUE=\"exact\"></TD></TR>\n";
  print "<TR><TD>Substring</TD><TD><INPUT NAME=\"exact_or_sub\" TYPE=\"radio\" VALUE=\"substring\" CHECKED></TD></TR>\n";
  print "</FORM>\n";
  print "</TABLE>\n";
} # sub firstPage

sub populateTypeIndex {
  my $result = $dbh->prepare( "SELECT * FROM wpa_type_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $type_index{$row[0]} = $row[1]; }
  }
  $result = $dbh->prepare( "SELECT * FROM wpa_electronic_type_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $electronic_type_index{$row[0]} = $row[1]; }
  }
} # sub populateTypeIndex





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

