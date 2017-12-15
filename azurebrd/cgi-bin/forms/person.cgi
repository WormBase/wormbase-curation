#!/usr/bin/perl -w

# users edit person data.

# new form with javascript in cgi to make it look neater.  2012 05 10
#
# added new label and description for years to old_institution.  2013 02 20
#
# changed disclaimer.  2013 10 24
#
# added orcid and information about it.
# got rid of $domain and made the $cgiPath just be the name of the form.  2013 11 04



use strict;
use CGI;
use Jex;		# &getPgDate; &getSimpleDate;
use DBI;
use Tie::IxHash;


my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $query = new CGI;
my $oop;

my $title = 'Person Update Form';
my ($htmlHeader, $htmlFooter) = &cshlNew($title);


my $frontpage = 1;
# my $blue = '#b8f8ff';			# redefine blue to a mom-friendly color
my $blue = '#e8f8ff';			# redefine blue to a mom-friendly color
# my $blue = 'cyan';			# redefine blue to a mom-friendly color
my $grey = '#d0d0d0';			# redefine grey to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color
my $lines_in_multiline = 10;		# how many extra lines to create
# my $domain = 'http://tazendra.caltech.edu/';
# my $cgiPath = '~azurebrd/cgi-bin/forms/person.cgi';
my $cgiPath = 'person.cgi';

my %curators;                           # $curators{two}{two#} = std_name ; $curators{std}{std_name} = two#

my %selectData; &populateLab(); 

# my @two_tables = qw(email firstname middlename lastname standardname street city state post country institution old_institution mainphone labphone officephone otherphone fax old_email lab oldlab left_field webpage );

# my @normal_tables = qw( firstname middlename lastname standardname aka_firstname aka_middlename aka_lastname email old_email old_email_date street city state post country institution old_institution old_inst_date mainphone labphone officephone otherphone fax pis lab oldlab left_field unable_to_contact privacy webpage usefulwebpage wormbase_comment hide status mergedinto acqmerge comment );
my @normal_tables = qw( email firstname middlename lastname standardname institution street city state post country old_institution mainphone labphone officephone otherphone fax old_email lab oldlab orcid left_field webpage );

my %tableToLabel; my %tableLabelNote; my %multiRow; my %inlineTable; &populateTableParameters();

# my %type_input;				# all inputs are inputs, but usefulwebpage is a checkbox
# foreach ("number", @normal_tables) { $type_input{$_} = 'input'; } 
# $type_input{'usefulwebpage'} = 'checkbox';
# 
# 
# my %lineageDropdowns;
# 
# my %order_type;
# my @single_order = qw( firstname middlename lastname standardname city state post country left_field unable_to_contact hide status mergedinto );
# my @multi_order = qw( street institution old_institution old_inst_date mainphone labphone officephone otherphone fax email old_email old_email_date pis lab oldlab privacy aka_firstname aka_middlename aka_lastname webpage usefulwebpage wormbase_comment acqmerge comment );
# foreach (@single_order) { $order_type{single}{$_}++; }
# foreach (@multi_order) { $order_type{multi}{$_}++; }

# my %min_rows;
# foreach my $table (@normal_tables) { $min_rows{$table} = 1; }
# $min_rows{'street'} = 4;

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

  if ($action eq 'Query') {           &query(); }
  elsif ($action eq 'Display') {      &query(); }
  elsif ($action eq 'Submit') {       &submit(); }
  elsif ($action eq 'unsubscribe') {  &unsubscribe(); }
#   elsif ($action eq 'autocompleteXHR') {  &autocompleteXHR(); }
#   elsif ($action eq 'updatePostgresTableField') { &updatePostgresTableField(); }
#   elsif ($action eq 'updatePostgresLineageData') { &updatePostgresLineageData(); }
#   elsif ($action eq 'Search') { &search(); }
#   elsif ($action eq 'Create New Person') { &createNewPerson(); }
#   elsif ($action eq 'Search Paper') { &searchPaper(); }
#   elsif ($action eq 'Checkout Papers') { &checkoutPapers(); }
#   elsif ($action eq 'Create people from XML') { &createPeopleFromXml(); }
} # sub display


sub unsubscribe {               # allow users to unsubscribe through this  2009 11 24
  # LINK TO UNSUBSCRIBE http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=unsubscribe&two=two1823&passwd=20030207
  # which is the joinkey + the date of the timestamp of the two table stripped of hyphens
  &printHtmlHeader();
  ($oop, my $two) = &getHtmlVar($query, 'two');
  ($oop, my $passwd) = &getHtmlVar($query, 'passwd');
  if ($passwd =~ m/^(\d{4})(\d{2})(\d{2})/) { $passwd = "$1-$2-$3"; }
    else { print "Invalid password<br />\n"; }
  my $result = $dbh->prepare ( "SELECT * FROM two WHERE joinkey = '$two' AND CAST(two_timestamp AS TEXT) ~ '^$passwd';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  if ($row[0]) {
      my $result2 = $dbh->prepare ( "SELECT * FROM two_unsubscribe WHERE joinkey = '$two';" );
      $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row2 = $result2->fetchrow;
      if ($row2[0]) { my $result3 = $dbh->do ( "DELETE FROM two_unsubscribe WHERE joinkey = '$two';" ); }
      my $result4 = $dbh->do ( "INSERT INTO two_unsubscribe VALUES ('$two', 'unsubscribe');" );
      print "<p><font size=+2>Thank you for unsubscribing, you will no longer receive WormBase emails about newsletters, meeting announcement, &c., but you will still get emails about associating your published papers.</font></p>\n"; }
    else { print "Invalid password for WBPerson $two<br>\n"; }
  &printHtmlFooter();
}

sub submit {
  &printHtmlHeader();
  ($oop, my $joinkey) = &getHtmlVar($query, 'number');
  unless ($joinkey) { $joinkey = ''; } my $person = $joinkey; $person =~ s/two/WBPerson/;
  my $dataSent = ''; my $dataDiff = '';
  my $tdstyle = qq(align="left" style="border-width: 1px; border-color: black; border-style: dotted;");
  my $tableSent = qq(<table border="0" cellspacing="5"><tr><td $tdstyle colspan=3>all data</td></tr>);
  my $tableDiff = qq(<table border="0" cellspacing="5"><tr><td $tdstyle>field</td><td $tdstyle></td><td $tdstyle>old</td><td $tdstyle>new</td></tr>);
  my @emails;
  foreach my $table (@normal_tables) {
    my $fields_amount = $lines_in_multiline;
    unless ($multiRow{$table}) { $fields_amount = 1; }
    for my $order (1 .. $fields_amount) { 
      my $inputId  = "current_${table}_$order";
      my $hiddenId = "previous_${table}_$order";
      ($oop, my $newData) = &getHtmlVar($query, $inputId);
      ($oop, my $oldData) = &getHtmlVar($query, $hiddenId);
      if ($newData) { 
        $dataSent  .= "$table\t$order\t$newData\n";
        $tableSent .= "<tr><td $tdstyle>$table</td><td $tdstyle>$order</td><td $tdstyle>$newData</td></tr>\n";
        if ($table eq 'email') { push @emails, $newData; } }
      if ($newData ne $oldData) {
        $dataDiff .= "$table\t$order\tOLD $oldData NEW $newData\n";
        $tableDiff .= "<tr><td $tdstyle>$table</td><td $tdstyle>$order</td><td $tdstyle>$oldData</td><td $tdstyle>$newData</td></tr>\n"; }
  } }
  ($oop, my $comment) = &getHtmlVar($query, 'comment');
  $dataSent  .= "comment\t\t$comment\n";
  my $html_comment = $comment; $html_comment =~ s/\n/<br>/g;
  $tableSent .= "<tr><td $tdstyle>comment</td><td $tdstyle></td><td $tdstyle>$html_comment</td></tr>\n";
  print qq(Thank you for submitting this data.<br />\n);
  print qq(Updates will show in the next release of WormBase.<br />\n);
  print qq(The full release schedule is available here:<br />\n);
  print qq(<a href="http://www.wormbase.org/about/release_schedule#01--10">http://www.wormbase.org/about/release_schedule#01--10</a><br/>\n);
  print "$tableSent</table><br/>\n";
  print "$tableDiff</table>";
  my $user = shift @emails;
  my $email = 'cecilia@tazendra.caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
  if ($user) { $email .= ', ' . $user; } else { $user = 'no_email'; }
  my $subject = 'Update From Person Form';
  my $host = $query->remote_host();     # get ip address
  my $body = "From IP $host sends :\n\n";
  $body .= "$dataSent\n";
  if ($joinkey) { $body .= "$person updates :\n$dataDiff\n"; }
  $body .= "\n\nThank you very much for updating your contact information.\n\nUpdates will appear in the next release of WormBase in your WBPerson page under author/Person search http://www.wormbase.org . The full release schedule is available here:\n\nhttp://wiki.wormbase.org/index.php/Release_Schedule\n\nPlease do not hesitate to contact me if you have any questions.\n\nHave a great day,\n\nCecilia";

  &mailer($user, $email, $subject, $body);    # email CGI to user
  &printHtmlFooter();
} # sub submit

sub firstPage {
  &printHtmlHeader();
  &displayFormInstructions();
  &displayForm();
  &printHtmlFooter();
} # sub firstPage

sub displayForm {
  my ($joinkey) = @_;
  unless ($joinkey) { $joinkey = ''; } my $person = $joinkey; $person =~ s/two/WBPerson/;

#   my $entry_data;
#   print "<table style=\"border-style: none;\" border=\"0\" >\n";
  print qq (<table style="border-style: none;" border="0" >\n);
#   my $url = $domain . $cgiPath;
  my $url = $cgiPath;
  print qq( <form name='form1' method="post" action="$url">\n);
  print qq(<input type="hidden" name="number" value="$joinkey"/>\n);
  my $header_bgcolor = '#dddddd'; my $header_color = 'black';
  my $entry_data = "<tr bgcolor='$header_bgcolor'><td>$person</td><td colspan=5><div style=\"color:$header_color\">Person Information</div></td></tr>\n";

  my %pgdata;
  foreach my $table (@normal_tables) {
#     $entry_data .= "<input type=\"hidden\" class=\"fields\" value=\"$table\" \/>\n";
    my $pg_table = 'two_' . $table; 
    $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY two_order" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      next unless ($row[2]);				# skip blank entries
      $pgdata{$table}{highest_order} = $row[1];
      $pgdata{$table}{$row[1]}{data} = $row[2];
      $pgdata{$table}{$row[1]}{row_curator} = $row[3];
      $pgdata{$table}{$row[1]}{timestamp} = $row[4]; }
  } # foreach my $table (@normal_tables)

  foreach my $table (@normal_tables) {
     next if ($inlineTable{$table});
     if ($multiRow{$table}) {
         for my $order (1 .. $lines_in_multiline) { ($entry_data) = &makeTableRow( $entry_data, \%pgdata, $order, $table ); } }
       else {
         ($entry_data) = &makeTableRow( $entry_data, \%pgdata, 1, $table ); }
    if ($tableLabelNote{$table}) { 
      my $note = $tableLabelNote{$table};
      my $note_link = qq( <span id="hide_note_$table"><a href="#" onclick="document.getElementById('note_tr_$table').style.display='none'; return false;">hide</a></span> );
      $entry_data .= qq( <tr id="note_tr_$table" style="display: none;"><td colspan="6">$note_link $note</td></tr> ); }
  } # foreach my $table (@normal_tables)
  print "$entry_data\n";
  print qq(<tr><td>Comment</td><td></td><td colspan="4"><textarea name="comment" rows="8" cols="90" value=""></textarea></td></tr>\n);
  print qq(<tr><td></td><td></td><td><input type="submit" name="action" value="Submit"></td></tr>\n);
  print "</form>\n";
  print "</table>\n";
  print qq(<br />Note: Phone and fax information won't show in your Person report for privacy reasons, but we are collecting the information in case we need to contact you.<br/>We keep old email, old institution, and old registered_lab data for history, please don't remove it when updating your information.<br/>Apologies, our database does not support foreign characters.\n);

#   $tableToLabel{'standardname'}   = 'Your Preferred Name';
#   $tableLabelNote{'lab'}          = 'Please input your P.I. last name to get code';
#   $multiRow{'email'}++;
#   $inlineTable{'middlenname'}++;
} # sub displayForm

sub makeTableRow {
  my ($entry_data, $pgdata_ref, $order, $table) = @_;
  my %pgdata = %$pgdata_ref;
  if ($table eq 'firstname') {
      $entry_data .= &makeTripletHorizontal(\%pgdata, $order, $table, 'middlename', 'lastname', 'Full Name'); }
    elsif ($table eq 'city') {
      $entry_data .= &makeQuadHorizontal(\%pgdata, $order, $table, 'state', 'post', 'country', 'Address'); }
    else {
      $entry_data .= &makeSingleNormal(\%pgdata, $order, $table); }
  return $entry_data;
} # sub makeTableRow

sub makeInputField {
  my ($current_value, $table, $order, $colspan, $rowspan, $class, $td_width, $input_size) = @_;
  unless ($current_value) { $current_value = ''; }
  my $freeForced = 'free';
  my $containerSpanId = "container${freeForced}${table}${order}AutoComplete";
  my $divAutocompleteId = "${freeForced}${table}${order}AutoComplete";
  my $inputId   = "input_${table}_$order";
  my $inputName = "current_${table}_$order";
  my $hiddenId  = "previous_${table}_$order";
  my $divContainerId = "${freeForced}${table}${order}Container";
  my $data = qq( <td width="$td_width" class="$class" rowspan="$rowspan" colspan="$colspan"> );
  if ($current_value) { $data .= qq( <input type="hidden" id="$hiddenId" name="$hiddenId" value="$current_value"> ); }
#   $data   .= qq( <span id="$containerSpanId"> );
#   $data   .= qq( <div id="$divAutocompleteId" class="div-autocomplete"> );
  my $order_plus_one = $order + 1; my $trToShowId = "tr_${table}_${order_plus_one}"; my $onkeyup = '';
  if ($multiRow{$table}) { $onkeyup = qq(onkeyup="if (document.getElementById('$inputId').value !== '') { document.getElementById('$trToShowId').style.display = ''; } return false;"); }
  $data   .= qq( <input id="$inputId" name="$inputName" size="$input_size" value="$current_value" $onkeyup> );
#   $data   .= qq( <div id="$divContainerId"></div></div></span> );
  $data   .= qq(</td>);
  return $data;
} # sub makeInputField

sub makeSelectField {
  my ($current_value, $table, $order, $colspan, $rowspan, $class, $td_width, $select_size) = @_;
  unless ($current_value) { $current_value = ''; }
#   my $freeForced = 'free';
#   my $containerSpanId = "container${freeForced}${table}${order}AutoComplete";
#   my $divAutocompleteId = "${freeForced}${table}${order}AutoComplete";
#   my $divContainerId = "${freeForced}${table}${order}Container";
  my $selectId       = "select_${table}_$order";
  my $selectName     = "current_${table}_$order";
  my $hiddenId       = "previous_${table}_$order";
  my $data = qq( <td width="$td_width" class="$class" rowspan="$rowspan" colspan="$colspan">);
  if ($current_value) { $data .= qq( <input type="hidden" id="$hiddenId" name="$hiddenId" value="$current_value"> ); }

  my $order_plus_one = $order + 1; my $trToShowId = "tr_${table}_${order_plus_one}"; my $onchange = '';
#   if ($multiRow{$table}) { $onchange = qq(onchange="document.getElementById('$trToShowId').style.display = ''; return false;"); }
  if ($multiRow{$table}) { $onchange = qq(onchange="var e = document.getElementById('$selectId'); if (e.options[e.selectedIndex].value !== '') { document.getElementById('$trToShowId').style.display = ''; } return false;"); }	# if multiple rows and select changes to an option with a value, show the next row
  $data   .= qq( <select id="$selectId" name="$selectName" $onchange> );

  if ( ($table eq 'lab') || ($table eq 'oldlab') ) {
    $data .= qq( <option value=""></option> );
    if ($current_value) { $data .= qq( <option value="$current_value" selected="selected">$current_value</option> ); }
    foreach my $repAndLab (sort {lc $a cmp lc $b} keys %{ $selectData{lab} }) {
      $data .= qq( <option value="$repAndLab">$repAndLab</option> ); }
  }
#     foreach my $rep (sort keys %{ $selectData{lab}{repToId} }) { 
#       my $id = $selectData{lab}{repToId}{$rep};
#       $data .= qq( <option value="$id $rep">$rep -- $id</option> ); }
#     foreach my $id (sort keys %{ $selectData{lab}{idToRep} }) { 
#       my $rep = $selectData{lab}{idToRep}{$id};
#       $data .= qq( <option value="$id $rep">$id -- $rep</option> ); }
  $data   .= qq( </select> );
  $data   .= qq(</td>);
  return $data;
} # sub makeSelectField

sub makeSingleNormal {
  my ($pgdata_ref, $order, $table) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '550';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '100';
  my $select_size = '1';
  my $bgcolor = 'white';
  my $data = ''; my $spacer = ''; my $displayToggle = ''; my $trId = "tr_${table}_${order}";
  my $highest_order = $pgdata{$table}{highest_order}; unless ($highest_order) { $highest_order = 0; }
  if ($order > $highest_order + 1) { $spacer = '&nbsp;&nbsp;&nbsp;&nbsp;'; $displayToggle = 'display: none'; }
  if ($pgdata{$table}{$order}{data}) { $data = $pgdata{$table}{$order}{data}; $bgcolor = $blue; }
  if ( ($highest_order > $order) && !($data) ) { return; }	# if deleted entry of lower order than highest order, don't show a blank row while there are still data rows later  2012 08 09
  my $label = $tableToLabel{$table};
  if ($tableLabelNote{$table}) { $label .= " " . qq( <span id="show_note_$table"><a href="#" onclick="document.getElementById('note_tr_$table').style.display=''; return false;">?</a></span> ); }
  my ($td_data) = &makeInputField($data, $table, $order, '4', '1', '', $td_width, $input_size); 
  if ( ($table eq 'lab') || ($table eq 'oldlab') ) {
    ($td_data) = &makeSelectField($data, $table, $order, '4', '1', '', $td_width, $select_size);  }
#   unless ($multiRow{$table}) { $order = ''; }
  $order = '';			# don't display order for Cecilia 2012 07 27
  return qq(<tr id="$trId" bgcolor="$bgcolor" style="$displayToggle"><td>${spacer}$label</td><td>$order</td>$td_data</tr>);
} # sub makeSingleNormal

sub makeQuadHorizontal {
  my ($pgdata_ref, $order, $one_table, $two_table, $three_table, $four_table, $label) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '40';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '20';
  my $bgcolor = 'white';
  my ($one_data, $two_data, $three_data, $four_data);
  my ($td_one_data, $td_two_data, $td_three_data, $td_four_data);
  if ($pgdata{$one_table}{$order}{data}) {   $one_data   = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$two_table}{$order}{data}) {   $two_data   = $pgdata{$two_table}{$order}{data}; }
  if ($pgdata{$three_table}{$order}{data}) { $three_data = $pgdata{$three_table}{$order}{data}; }
  if ($pgdata{$four_table}{$order}{data}) {  $four_data  = $pgdata{$four_table}{$order}{data}; }
  ($td_one_data)   = &makeInputField($one_data, $one_table, $order, '1', '1', '', $td_width, $input_size);
  ($td_two_data)   = &makeInputField($two_data, $two_table, $order, '1', '1', '', $td_width, $input_size);
  ($td_three_data) = &makeInputField($three_data, $three_table, $order, '1', '1', '', $td_width, $input_size);
  ($td_four_data)  = &makeInputField($four_data, $four_table, $order, '1', '1', '', $td_width, $input_size);
  if ($one_table) {   $td_one_data   =~ s/<\/td>$/<br\/>$tableToLabel{$one_table}<\/td>/; }
  if ($two_table) {   $td_two_data   =~ s/<\/td>$/<br\/>$tableToLabel{$two_table}<\/td>/; }
  if ($three_table) { $td_three_data =~ s/<\/td>$/<br\/>$tableToLabel{$three_table}<\/td>/; }
  if ($four_table) {  $td_four_data  =~ s/<\/td>$/<br\/>$tableToLabel{$four_table}<\/td>/; }
  my $spacer = ''; my $displayToggle = ''; my $trId = "tr_${one_table}_${order}";
  if ($order > 1) { $spacer = '&nbsp;&nbsp;&nbsp;&nbsp;'; $displayToggle = 'display: none'; }
#   unless ($multiRow{$one_table}) { $order = ''; }
  $order = '';			# don't display order for Cecilia 2012 07 27
  return qq(<tr id="$trId" bgcolor="$bgcolor" style="$displayToggle"><td>${spacer}$label</td><td>$order</td>${td_one_data}${td_two_data}${td_three_data}${td_four_data}</tr>\n);
} # sub makeQuadHorizontal

sub makeTripletHorizontal {
  my ($pgdata_ref, $order, $one_table, $two_table, $three_table, $label) = @_;
  my %pgdata = %$pgdata_ref;
  my $td_width = '40';		# there's some weird auto-sizing of the field where it shrinks to nothing if the td doesn't have a size, so min size is 550
  my $input_size = '20'; my $double_input_size = 2 * $input_size;
  my $bgcolor = 'white';
  my ($one_data, $two_data, $three_data);
  my ($td_one_data, $td_two_data, $td_three_data);
  if ($pgdata{$one_table}{$order}{data}) {   $one_data   = $pgdata{$one_table}{$order}{data}; $bgcolor = $blue; }
  if ($pgdata{$two_table}{$order}{data}) {   $two_data   = $pgdata{$two_table}{$order}{data}; }
  if ($pgdata{$three_table}{$order}{data}) { $three_data = $pgdata{$three_table}{$order}{data}; }
  ($td_one_data)   = &makeInputField($one_data, $one_table, $order, '1', '1', '', $td_width, $input_size);
  ($td_two_data)   = &makeInputField($two_data, $two_table, $order, '1', '1', '', $td_width, $input_size);
  ($td_three_data) = &makeInputField($three_data, $three_table, $order, '2', '1', '', $td_width, $double_input_size);
  if ($one_table) {   $td_one_data   =~ s/<\/td>$/<br\/>$tableToLabel{$one_table}<\/td>/; }
  if ($two_table) {   $td_two_data   =~ s/<\/td>$/<br\/>$tableToLabel{$two_table}<\/td>/; }
  if ($three_table) { $td_three_data =~ s/<\/td>$/<br\/>$tableToLabel{$three_table}<\/td>/; }
  my $spacer = ''; my $displayToggle = ''; my $trId = "tr_${one_table}_${order}";
  if ($order > 1) { $spacer = '&nbsp;&nbsp;&nbsp;&nbsp;'; $displayToggle = 'display: none'; }
#   unless ($multiRow{$one_table}) { $order = ''; }
  $order = '';			# don't display order for Cecilia 2012 07 27
  return qq(<tr id="$trId" bgcolor="$bgcolor" style="$displayToggle"><td>${spacer}$label</td><td>$order</td>${td_one_data}${td_two_data}${td_three_data}</tr>\n);
} # sub makeTripletHorizontal

sub displayFormInstructions {
  print "<H1>Add your info (Email, First and Last names are required) :</H1>\n";
  print "Author data is still being kept by WormBase, but its contact data is no longer updated.  WormBase now has Persons, whose contact data will be kept up-to-date, and who are being connected to the proper Authors and Publications.<P>\n";
  print "Please email <a href=mailto:cecilia\@tazendra.caltech.edu>Cecilia</a> if you have any questions, or to send her your data directly.<P>\n";
#   print "If you would rather query to see if we already have your data, you may do so below (and then Edit if some of it needs updating).<P>\n";
  print "Please query to see if we already have your data, you may do so below (and then Edit if some of it needs updating).<p>\n";
  &displayQuery();              # show query box
  print "If you don't get a verification email, email us at help\@wormbase.org<P>\n";
} # sub displayFormInstructions


sub printHtmlHeader {
  print "Content-type: text/html\n\n";
  print $htmlHeader;
}

sub printHtmlFooter {
  print $htmlFooter;
}

# sub printHtmlHeader {
#   print "Content-type: text/html\n\n";
#   my $title = 'Person Editor';
#   my $header = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><HTML><HEAD>';
#   $header .= "<title>$title</title>\n";
#   $header .= "</head>";
#   $header .= '<body>';
#   print $header;
# }

sub OLDprintHtmlHeader {
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

sub populateTableParameters {
  foreach my $table (@normal_tables) { my $label = ucfirst($table); $tableToLabel{$table} = $label; }
  $tableToLabel{'street'}               = 'Address';
  $tableToLabel{'post'}                 = 'City postal code';
  $tableToLabel{'lab'}                  = 'Approved cgc lab code';
  $tableToLabel{'standardname'}         = 'Your Preferred Name';
  $tableToLabel{'old_institution'}      = 'Old Institution + <br/>(Starting and ending years)';
  $tableLabelNote{'institution'}        = 'This tag will appear following our format Name of Institution, City State, Country.<br/>Example: Caltech, Pasadena CA, USA';
  $tableLabelNote{'old_institution'}    = 'This tag will appear following old Institution format Name of Institution, City State, Country. (Starting Year - Ending Year)<br/>Example: City University of New York, Staten Island NY, USA (2000-2004)';
  $tableLabelNote{'lab'}                = 'Please input your P.I. last name to get code';
  $tableLabelNote{'orcid'}              = qq(<br/><a href="http://orcid.org/content/initiative" target="new">Open Researcher and Contributor ID</a><br/>If you'd like to register for an ORCID identifier please follow this link:<br/><a href="https://orcid.org/register" target="new">https://orcid.org/register</a><br/>To search if you already have an ORCID identifier:<br/>
<a href="https://orcid.org/orcid-search/search" target="new">https://orcid.org/orcid-search/search</a><br/>Please enter your ORCID identifier(s) to add them to your WBPerson report.);
  $multiRow{'email'}++;
  $multiRow{'street'}++;
  $multiRow{'institution'}++;
  $multiRow{'old_institution'}++;
  $multiRow{'mainphone'}++;
  $multiRow{'officephone'}++;
  $multiRow{'otherphone'}++;
  $multiRow{'labphone'}++;
  $multiRow{'fax'}++;
  $multiRow{'old_email'}++;
  $multiRow{'lab'}++;
  $multiRow{'oldlab'}++;
  $multiRow{'orcid'}++;
  $multiRow{'webpage'}++;
#   $inlineTable{'firstname'}++;
  $inlineTable{'middlename'}++;
  $inlineTable{'lastname'}++;
#   $inlineTable{'city'}++;
  $inlineTable{'state'}++;
  $inlineTable{'post'}++;
  $inlineTable{'country'}++;
} # sub populateTableParameters

sub populateLab {
  my %names;
  $result = $dbh->prepare( "SELECT * FROM two_lastname   WHERE joinkey IN (SELECT joinkey FROM two_pis) AND two_lastname   != 'NULL'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while(my @row = $result->fetchrow) { $names{last}{$row[0]}   = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_firstname  WHERE joinkey IN (SELECT joinkey FROM two_pis) AND two_firstname  != 'NULL'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while(my @row = $result->fetchrow) { $names{first}{$row[0]}  = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_middlename WHERE joinkey IN (SELECT joinkey FROM two_pis) AND two_middlename != 'NULL'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while(my @row = $result->fetchrow) { $names{middle}{$row[0]} = $row[2]; }

  $result = $dbh->prepare( "SELECT * FROM two_pis WHERE two_pis ~ '[A-Z]'" );	# only letter labs for Cecilia 2016 10 26
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while(my @row = $result->fetchrow) { 
    my $two = $row[0]; my $lab = $row[2];
    my ($first, $last, $middle, $front, $name);
    if ($names{last}{$two}) {    $last = $names{last}{$two}; }
    if ($names{first}{$two}) {   $first = $names{first}{$two}; $front = $first; }
    if ($names{middle}{$two}) {  $middle = $names{middle}{$two}; $front = "$first $middle"; }
    if ($last && $front) { $name = "${last}, $front"; }
      elsif ($last) { $name = $last; } elsif ($front) { $name = $front; }
    $selectData{'lab'}{"$name -- $lab"}++;  
  } # while(my @row = $result->fetchrow)

#   $result = $dbh->prepare( "SELECT * FROM obo_data_laboratory" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while(my @row = $result->fetchrow) {
#     my $rep = '';
#     if ($row[1] =~ m/Representatives: (.*)/) { $rep = $1; }
#     if ($rep) { $selectData{'lab'}{repToId}{$rep} = $row[0]; }
#     $selectData{'lab'}{idToRep}{$row[0]} = $rep;
#   }
} # sub populateLab

sub displayQuery {                      # show form as appropriate
#     my $url = $domain . $cgiPath;
    my $url = $cgiPath;
    print <<"EndOfText";
<FORM METHOD="POST" ACTION="$url">

  <TABLE ALIGN="center">
    <TR><TD><FONT SIZE=+2>Please enter the name you would like to search for to edit your current information :</FONT></TD>
        <TD><Input Type="Text" Name="name" Size="20"></TD>
        <TD><INPUT TYPE="submit" NAME="action" VALUE="Query"></TD></TR>
    <TR>
      <TD> </TD>
<!--      <TD><INPUT TYPE="submit" NAME="action" VALUE="Submit"></TD>-->
    </TR>
  </TABLE>
</FORM>
EndOfText
} # sub displayQuery

sub query {
  ($oop, my $name) = &getHtmlVar($query, 'name');
  ($oop, my $joinkey) = &getHtmlVar($query, 'number');
  if ($joinkey =~ m/WBPerson/) { $joinkey =~ s/WBPerson/two/; }
  &printHtmlHeader();
  if ($joinkey) {
    &displayFormInstructions();
    &displayForm($joinkey);
  } elsif ($name !~ m/\w/) {		# if no number nor name, give error
    print "<b style=\"color: red;font-size: 14pt\">ERROR no name entered for which to query.</b><br />\n";
    &displayFormInstructions();
    &displayForm();
  } elsif ($name =~ /\d/) {
    &processPgNumber($name);
  } elsif ($name =~ m/[\*\?]/) {      # if it has a * or ?
    &processPgWild($name);
  } else {                    # if it doesn't do simple aka hash thing
    &processAkaSearch($name);
  }
  &printHtmlFooter();
} # sub query


sub processPgWild {
  my $input_name = shift;
  print "<TABLE>\n";
  print "<TR><TD>INPUT</TD><TD>$input_name</TD></TR>\n";
  my @people_ids;
  $input_name =~ s/\*/.*/g;
  $input_name =~ s/\?/./g;
  my @input_parts = split/\s+/, $input_name;
  my %input_parts;
  my %matches;                          # keys = wbid, value = amount of matches
  my %filter;
  foreach my $input_part (@input_parts) {
    my @tables = qw (first middle last);
    foreach my $table (@tables) {
      my $result = $dbh->prepare ( "SELECT * FROM two_aka_${table}name WHERE lower(two_aka_${table}name) ~ lower('$input_part');" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      while ( my @row = $result->fetchrow ) { $filter{$row[0]}{$input_part}++; }
      $result = $dbh->prepare ( "SELECT * FROM two_${table}name WHERE lower(two_${table}name) ~ lower('$input_part');" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      while ( my @row = $result->fetchrow ) { $filter{$row[0]}{$input_part}++; }
    } # foreach my $table (@tables)
  } # foreach my $input_part (@input_parts)

  foreach my $number (sort keys %filter) {
    foreach my $input_part (@input_parts) {
      if ($filter{$number}{$input_part}) {
        my $temp = $number; $temp =~ s/two//g; $matches{$temp}++;
        my $count = length($input_part);
        unless ($input_parts{$temp} > $count) { $input_parts{$temp} = $count; }
      }
    } # foreach my $input_part (@input_parts)
  } # foreach my $number (sort keys %filter)

  print "<tr><td></td><td>There are " . scalar(keys %matches) . " match(es).</td></tr>\n";
  print "<tr></tr>\n";
  print "</table>\n";
  print "<table border=0 cellspacing=5>\n";
  foreach my $number (sort {$matches{$b}<=>$matches{$a} || $input_parts{$b} <=> $input_parts{$a}} keys %matches) {
    my $person = "WBPerson".$number;
    my $joinkey = "two".$number;
    my $result = $dbh->prepare ( "SELECT * FROM two_standardname WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow; my $stdname = $row[2];
#     my $url = $domain . $cgiPath;
    my $url = $cgiPath;
    print qq(<tr><td><a href="${url}?action=Query&number=$joinkey">$person</a></td><td>$stdname</td>\n);
#     print "<TR><TD><A HREF=http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=Display&number=$person>$person</A></TD>\n";
    my $matchWord = 'match'; if ($matches{$number} != 1) { $matchWord = 'matches'; }
    print "<TD>has $matches{$number} $matchWord</TD><TD>priority $input_parts{$number}</TD></TR>\n";
  }
  print "</TABLE>\n";

  unless (%matches) {
    print "<FONT COLOR=red>Sorry, no person named '$input_name', please try again</FONT><P>\n" if $input_name;
  }
} # sub processPgWild

sub processAkaSearch {                  # get generated aka's and try to find exact match
  my ($name) = @_;
  my $search_name = lc($name);

  my %aka_hash; my %filter;

  my @tables = qw (first middle last);
  foreach my $table (@tables) {
    $result = $dbh->prepare ( "SELECT * FROM two_aka_${table}name WHERE two_aka_${table}name IS NOT NULL AND two_aka_${table}name != 'NULL' AND two_aka_${table}name != '';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( my @row = $result->fetchrow ) {
      if ($row[3]) {                                    # if there's a curator
        my $joinkey = $row[0];
        $row[2] =~ s/^\s+//g; $row[2] =~ s/\s+$//g;     # take out spaces in front and back
        $row[2] =~ s/[\,\.]//g;                         # take out commas and dots
        $row[2] =~ s/_/ /g;                             # replace underscores for spaces
        $row[2] = lc($row[2]);                          # for full values (lowercase it)
        $row[0] =~ s/two//g;                            # take out the 'two' from the joinkey
        $filter{$row[0]}{$table}{$row[2]}++;
        my ($init) = $row[2] =~ m/^(\w)/;               # for initials
        $filter{$row[0]}{$table}{$init}++;
      }
    }
    $result = $dbh->prepare ( "SELECT * FROM two_${table}name WHERE two_${table}name IS NOT NULL AND two_${table}name != 'NULL' AND two_${table}name != '';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( my @row = $result->fetchrow ) {
      if ($row[3]) {                                    # if there's a curator
        my $joinkey = $row[0];
        $row[2] =~ s/^\s+//g; $row[2] =~ s/\s+$//g;     # take out spaces in front and back
        $row[2] =~ s/[\,\.]//g;                         # take out commas and dots
        $row[2] =~ s/_/ /g;                             # replace underscores for spaces
        $row[2] = lc($row[2]);                          # for full values (lowercase it)
        $row[0] =~ s/two//g;                            # take out the 'two' from the joinkey
        $filter{$row[0]}{$table}{$row[2]}++;
        my ($init) = $row[2] =~ m/^(\w)/;               # for initials
        $filter{$row[0]}{$table}{$init}++;
      }
    }
  } # foreach my $table (@tables)

  my $possible;
  foreach my $person (sort keys %filter) {
    foreach my $last (sort keys %{ $filter{$person}{last}} ) {
      foreach my $first (sort keys %{ $filter{$person}{first}} ) {
        $possible = "$first"; $aka_hash{$possible}{$person}++;
        $possible = "$last"; $aka_hash{$possible}{$person}++;
        $possible = "$last $first"; $aka_hash{$possible}{$person}++;
        $possible = "$first $last"; $aka_hash{$possible}{$person}++;
        if ( $filter{$person}{middle} ) {
          foreach my $middle (sort keys %{ $filter{$person}{middle}} ) {
#             $possible = "$first"; $aka_hash{$possible}{$person}++;
            $possible = "$middle"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $first"; $aka_hash{$possible}{$person}++;
#             $possible = "$last"; $aka_hash{$possible}{$person}++;
#             $possible = "$last $first"; $aka_hash{$possible}{$person}++;
            $possible = "$last $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last $first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last $middle $first"; $aka_hash{$possible}{$person}++;
#             $possible = "$first $last"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $first $last"; $aka_hash{$possible}{$person}++;
          } # foreach my $middle (sort keys %{ $filter{$person}{middle}} )
        }
      } # foreach my $first (sort keys %{ $filter{$person}{first}} )
    } # foreach my $last (sort keys %{ $filter{$person}{last}} )
  } # foreach my $person (sort keys %filter)

  $result = $dbh->prepare ( "SELECT * FROM two_standardname WHERE two_standardname IS NOT NULL AND two_standardname != 'NULL' AND two_standardname != '';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while ( my @row = $result->fetchrow ) {
    if ($row[3]) {                                      # if there's a curator
      $row[0] =~ s/two//g;                              # take out the 'two' from the joinkey
      $row[2] = lc($row[2]);
      $aka_hash{$row[2]}{$row[0]}++; } }                # add standardnames to aka hash         2007 02 27

  print "<table>\n";
  unless ($aka_hash{$search_name}) {
    print "<tr><td>NAME <font color=red>$name</font> NOT FOUND</td></tr>\n";
    my @names = split/\s+/, $search_name; $search_name = '';
    foreach my $name (@names) {
      if ($name =~ m/^[a-zA-Z]$/) { $search_name .= "$name "; }
      else { $search_name .= '*' . $name . '* '; }
    }
    &processPgWild($name);
  } else {
    my %standard_name;
    my $result = $dbh->prepare ( "SELECT * FROM two_standardname;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow ) {
      $standard_name{$row[0]} = $row[2];
    } # while (my @row = $result->fetchrow )

    print "<tr><td colspan=2 align=center>NAME <font color=red>$name</font> could be : </td></tr>\n";
    my @stuff = sort {$a <=> $b} keys %{ $aka_hash{$search_name} };
    foreach $_ (@stuff) {               # add url link
      my $joinkey = 'two'.$_;
      my $person = 'WBPerson'.$_;
      $result = $dbh->prepare ( "SELECT * FROM two_standardname WHERE joinkey = '$joinkey';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow; my $stdname = $row[2];
#       my $url = $domain . $cgiPath;
      my $url = $cgiPath;
      print qq(<tr><td><a href="${url}?action=Query&number=$joinkey">$person</a></td><td>$stdname</td>\n);
#       print "<tr><td>$standard_name{$joinkey}</td><td><a href=http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=Display&number=$person>$person</a></td>\n";
    }
  }
  print "</TABLE>\n";
} # sub processAkaSearch


sub processPgNumber {
  my $input_name = shift;
  if ($input_name =~ /(\d+)/) {   # and search just for number
    my $person = "WBPerson".$1;
    my $joinkey = "two".$1;
    my $result = $dbh->prepare ( "SELECT * FROM two_standardname WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    print "PERSON <FONT COLOR=red>$row[2]</FONT> has \n";
#     my $url = $domain . $cgiPath;
    my $url = $cgiPath;
    print "ID <A HREF=${url}?action=Query&number=$joinkey>$person</A>.</BR>\n";
  } # if ($input_name =~ /(\d*)/)
}



__END__

