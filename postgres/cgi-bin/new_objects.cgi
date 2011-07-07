#!/usr/bin/perl

# See new objects created by curation
#
# Object type / Object Name / Pub / Person / Object remark / Paper remark / Curator
#
# Check transgenes against a list from tra_transgeneinfo that Karen put in
# postgres.  If any allele-phenotype curation mentions a transgene not it that
# list, show in this form for Wen to check and confirm, adding it to the
# tra_transgeneinfo table.
# Do the same for alleles against ali_alleleinfo, but when confirming also put
# data into ali_yesmaryann (for later addition of always showing stuff with
# status info, to filter those she's already approved).  Also show data from
# go_curation in a separate table.  (Alleles may show in both tables)
# 2008 03 01
#
# Added Xiaodong's Gene Regulation data.  2008 03 03
#
# Needed to create a tra_yeswen table, otherwise it would get overwritten by
# Karen's script.  2008 04 09
#
# Add an input box for Transgene for Wen so that she can reassign the names of
# things that are temporary names.  Update postgres values for app_tempname and
# app_tempname_hst (as opposed to adding values to history), and confirm new
# values for both transgene lists.  2008 08 27
#
# Send emails to everyone if confirming phenotypes from allele-phenotype phenote, 
# not just suggested from CGI like before.  2009 01 26
#
# Added Christian A Grove two2987  2010 02 03
#
# No longer want variation section for Jolene or Mary Ann (says Jolene)  2010 06 10
#
# map ``Update Variation !'' variations to WBVarID for Jolene / Mary Ann  2010 05 12
#
# changed from wpa to pap tables, even though they're not live yet.  2010 06 23
#
# wrote  &queryVariation();  and  &searchWBVar();  for Mary Ann to look up curated data
# that mentions WBVariations in OA curation tables (right now only GO and Phenotype)
# 2010 08 26 
#
# changed  &searchWBVar();  to look at app_variation instead of app_tempname after 
# splitting into 4 fields.  2010 09 20
# 
# changed  &queryVariation();  to look at obo_name_app_variaton instead of 
# obo_name_app_tempname.  Display app_person.  2010 09 23
#
# got rid of  allele and transgene, backed up ali_ and tra_ tables to 
# /home/postgres/work/pgpopulation/backup_assorted
# okayed by Wen, Xiaodong, Karen.  2010 09 24
#
# added stuff for grg_ and int_ to show stuff for X + M.A.  2011 03 30



use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate mailer
use LWP::UserAgent;	# getting sanger files for querying
use LWP::Simple;	# get the PhenOnt.obo from a cgi
use DBI;


my %curator;
my %phobo;

my %pmids;

my $query = new CGI;	# new CGI form
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


&printHeader('New Objects Curation Form');	# normal form view
&process();
&printFooter();

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  unless ($action) { $action = ''; }
  if ($action eq '') { &printHtmlMenu(); }		# Display form, first time, no action
  else { 						# Form Button
    print "ACTION : $action : ACTION<BR>\n"; 
#     if ($action eq 'Update Transgene !') { &updateFinalname('Transgene'); }	# table of Transgene data for Wen
#     elsif ($action eq 'Update Variation !') { &updateFinalname('Allele'); }	# table of Variation data for Mary Ann
    if ($action eq 'Update Phenotype !') { &updateFinalname('Phenotype'); }	# table of Variation data for Mary Ann
    elsif ($action eq 'Query Variation !') { &queryVariation(); }		# query for Variation data for Mary Ann
    elsif ($action eq 'Confirm !') { &confirm(); }
    elsif ($action eq 'Suggest !') { &suggest(); }
    print "ACTION : $action : ACTION<BR>\n"; 
  } # else # if ($action eq '') { &printHtmlForm(); }
} # sub process

sub suggest {
  my ($oop, $suggested) = &getHtmlVar($query, 'suggested');
  ($oop, my $definition) = &getHtmlVar($query, 'definition');
  ($oop, my $childof) = &getHtmlVar($query, 'childof');
  ($oop, my $curator) = &getHtmlVar($query, 'curator');
  ($oop, my $evidence) = &getHtmlVar($query, 'evidence');
  my $joinkey = 0;
  my $result = $dbh->prepare( "SELECT joinkey FROM phn_suggested WHERE joinkey ~ '^0' ORDER BY joinkey DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; if ($row[0]) { $joinkey = $row[0]; } $joinkey++;
  ($joinkey) = &padZeros($joinkey);
  if ($suggested) { my $pgcommand = "INSERT INTO phn_suggested VALUES ('$joinkey', '$suggested', CURRENT_TIMESTAMP);"; my $result2 = $dbh->do( $pgcommand ); }
  if ($definition) { my $pgcommand = "INSERT INTO phn_definition VALUES ('$joinkey', '$definition', CURRENT_TIMESTAMP);"; my $result2 = $dbh->do( $pgcommand ); }
  if ($childof) { my $pgcommand = "INSERT INTO phn_childof VALUES ('$joinkey', '$childof', CURRENT_TIMESTAMP);"; my $result2 = $dbh->do( $pgcommand ); }
  if ($curator) { my $pgcommand = "INSERT INTO phn_curator VALUES ('$joinkey', '$curator', CURRENT_TIMESTAMP);"; my $result2 = $dbh->do( $pgcommand ); }
  if ($evidence) { my $pgcommand = "INSERT INTO phn_evidence VALUES ('$joinkey', '$evidence', CURRENT_TIMESTAMP);"; my $result2 = $dbh->do( $pgcommand ); }
#   print "J $joinkey S $suggested D $definition C $childof C $curator E $evidence END<BR>\n";
  print "Entry $joinkey for term $suggested has been entered.  You can now see it under the section ``Data suggested through this CGI''.<BR>\n";
} # sub suggest

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

sub confirm {
  my ($oop, $type) = &getHtmlVar($query, 'type');
#   print "T $type T<BR>\n";
  if ($type eq 'Phenotype') {
    ($oop, my $tempname_count) = &getHtmlVar($query, 'tempname_count');
    my $error = 0;
    for my $i (1 .. $tempname_count) {
      ($oop, my $term) = &getHtmlVar($query, "term_$i"); 
      if ($term) { unless ($term =~ m/WBPhenotype\:\d+/) { print "<FONT COLOR=red> ERROR line $i $term is not a valid phenotype</FONT><BR>\n"; $error++; } } }
    last if $error;
    for my $i (1 .. $tempname_count) {
      ($oop, my $term) = &getHtmlVar($query, "term_$i");
      ($oop, my $reject) = &getHtmlVar($query, "reject_$i");
      if ($reject eq 'checked') { $term = 'rejected'; }
      next unless $term;
      ($oop, my $joinkey) = &getHtmlVar($query, "joinkey_$i");
      ($oop, my $suggested) = &getHtmlVar($query, "suggested_$i");
      ($oop, my $comment) = &getHtmlVar($query, "comment_$i");
      my $email = ''; my %emails;
      my @joinkeys; 
      if ($joinkey) { push @joinkeys, $joinkey; }
        else { 
          my $result = $dbh->prepare( "SELECT * FROM app_suggested WHERE app_suggested = '$suggested';" );
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
          my %filter; while (my @row = $result->fetchrow) { $filter{$row[0]}++; } foreach my $key (sort {$a<=>$b} keys %filter) { push @joinkeys, $key; } }
      foreach my $joinkey (@joinkeys) {
        print "J $joinkey Confirm $term Comment $comment END<BR>\n";
        my @pgcommands;
        my $pgcommand = "INSERT INTO phn_confirmed VALUES ('$joinkey', '$term', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand;
        if ($comment) { $pgcommand = "INSERT INTO phn_comment VALUES ('$joinkey', '$comment', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand; }
        if ($joinkey =~ m/^0/) { 		# from CGI, not phenote (send email)
          my $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey IN (SELECT phn_curator FROM phn_curator WHERE joinkey = '$joinkey'); ");		# had the joinkey set to 00000001 instead of $joinkey 2008 10 20
          $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
          while (my @row = $result->fetchrow) { $emails{$row[2]}++; }
        } # if ($joinkey =~ m/^0/) 		# from CGI, not phenote (send email)
        else {					# from phenote, not CGI 
          $pgcommand = "INSERT INTO app_suggested_hst VALUES ('$joinkey', NULL, CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand;
          $pgcommand = "DELETE FROM app_suggested WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand;
          if ($term =~ m/WBPhenotype\:\d+/) {
            my $result = $dbh->prepare( "SELECT * FROM app_term WHERE joinkey = '$joinkey';" );
            $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
            my @row = $result->fetchrow(); 
            if ($row[0]) {
                $pgcommand = "UPDATE app_term SET app_term = '$term' WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand;
                $pgcommand = "UPDATE app_term SET app_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand; }
              else { $pgcommand = "INSERT INTO app_term VALUES ('$joinkey', '$term', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand; }
            $pgcommand = "INSERT INTO app_term_hst VALUES ('$joinkey', '$term', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand; }
        } # else # from phenote, not CGI
        foreach my $pgcommand (@pgcommands) { 
          print "<FONT COLOR=cyan SIZE=-2>$pgcommand<BR></FONT>\n"; 
          my $result2 = $dbh->do( $pgcommand );
        }
      } # foreach my $joinkey (@joinkeys)
      if ($joinkey =~ m/^0/) { my @emails = keys %emails; $email = join", ", @emails; }
        else { ($oop, $email) = &getHtmlVar($query, "email_$i"); }
      my $subject = "$term : suggested phenotype $suggested";
      my $body = "Email : $email<BR>\nsuggested : $suggested<BR>\nterm : $term<BR>\ncomment : $comment";
      print "$body<BR>\n"; $body =~ s/<BR>//g;
      my $user = "new_objects.cgi";
      if ($email) { &mailer($user, $email, $subject, $body); }
    } # for my $i (1 .. $tempname_count)
  }
#   else {		# don't care about allele or transgene anymore  (xiaodong, wen, karen) 2010 09 24
#     ($oop, my $tempname_count) = &getHtmlVar($query, 'tempname_count');
#     for my $i (1 .. $tempname_count) {
#       ($oop, my $checked) = &getHtmlVar($query, "checked_$i");
#       ($oop, my $new) = &getHtmlVar($query, "new_$i");
#       if ( ($new) || ($checked eq 'checked') ) {
#         ($oop, my $tempname) = &getHtmlVar($query, "tempname_$i");
#         if ($type eq 'Allele') { 
#           my $pgcommand = "INSERT INTO ali_alleleinfo VALUES ('$tempname', NULL, NULL, CURRENT_TIMESTAMP);";
# #           print "$pgcommand<BR>\n";
#           my $result2 = $dbh->do( $pgcommand );
#           $pgcommand = "INSERT INTO ali_yesmaryann VALUES ('$tempname', CURRENT_TIMESTAMP);";
# #           print "$pgcommand<BR>\n";
#           $result2 = $dbh->do( $pgcommand );
#         } elsif ($type eq 'Transgene') { 
#           if ($new) { 
#             my $pgcommand = "UPDATE app_tempname SET app_tempname = '$new' WHERE app_tempname = '$tempname';";
#             my $result2 = $dbh->do( $pgcommand );
#             $pgcommand = "UPDATE app_tempname_hst SET app_tempname_hst = '$new' WHERE app_tempname_hst = '$tempname';";
#             $result2 = $dbh->do( $pgcommand );
#             $tempname = $new; }
#           my $pgcommand = "INSERT INTO tra_transgeneinfo VALUES ('$tempname', NULL, NULL, CURRENT_TIMESTAMP);";
# #           print "$pgcommand<BR>\n";
#           my $result2 = $dbh->do( $pgcommand );
#           $pgcommand = "INSERT INTO tra_yeswen VALUES ('$tempname', CURRENT_TIMESTAMP);";
# #           print "$pgcommand<BR>\n";
#           $result2 = $dbh->do( $pgcommand );
#         }
#         print "I $i C $checked T $tempname<BR>\n";
#       }
#     } # for my $i (1 .. $tempname_count)
#     print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi\">\n";
#     print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update Variation !\"></TD><BR>\n";
#     print "</FORM>\n";
#   } # else # if ($type eq 'Phenotype')
} # sub confirm

sub printHtmlMenu {		# show main menu page
  print <<"  EndOfText";
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi">
  <TABLE border=0>
<!-- no longer want transgene section for Wen or Xiaodong   2010 09 24
  <TR>
    <TD COLSPAN=3><B>Update Transgene : </B></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Update Transgene !"></TD>
  <TR>
  <TR><TD><B>OR</B></TD></TR> -->
<!-- no longer want variation section for Jolene or Mary Ann (says Jolene)  2010 06 10
  <TR>
    <TD COLSPAN=3><B>Update Variation : </B></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Update Variation !"></TD>
  <TR>
  <TR><TD><B>OR</B></TD></TR>-->
  <TR>
    <TD COLSPAN=3><B>Update Phenotype : </B></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Update Phenotype !"></TD>
  <TR>
  <TR><TD><B>OR</B></TD></TR>
  <TR>
    <TD COLSPAN=3><B>Query Variation : </B></TD>
    <TD><textarea rows=5 cols=40 name=variations></textarea><br /><INPUT TYPE="submit" NAME="action" VALUE="Query Variation !"></TD>
  <TR>
  EndOfText
  print "</TABLE>\n";

#   my %exists; my %curated;
#   my $result = $dbh->prepare( "SELECT joinkey FROM ale_allele;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { $exists{$row[0]}++; }
#   $result = $dbh->prepare( "SELECT joinkey FROM ale_curated;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { if ($exists{$row[0]}) { delete $exists{$row[0]}; } }
#   if (scalar keys %exists) { print "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi?action=See%20Submissions\">There are " . scalar(keys %exists) . " entries from allele submission form to curate.</A><BR>\n"; }

  print "</FROM>\n";
} # sub printHtmlMenu


sub queryVariation {
  my %hash; 
  print "<a href=\"http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi\">return to query page</a><br/>\n";
  print "<br />\n";
#   my $result = $dbh->prepare( "SELECT * FROM obo_name_app_variation;" ); 		# old tables  2011 03 30
  my $result = $dbh->prepare( "SELECT * FROM obo_name_variation;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{id_to_name}{$row[0]} = $row[1]; $hash{name_to_id}{$row[1]} = $row[0]; }
  my ($junk, $variations) = &getHtmlVar($query, 'variations');
  my (@vars) = split/\W/, $variations; foreach (@vars) { $_ =~ s/\W//g; }
  foreach my $var (@vars) {
    next unless ($var);
    my $id = '';
    if ($hash{id_to_name}{$var}) { $id = $var; }
    elsif ($hash{name_to_id}{$var}) { $id = $hash{name_to_id}{$var}; }
    unless ($id) { print "<span style=\"color:red\">$var does not match a WBVariation</span> from obo_name_app_variation please update data based on nameserver using this <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=AddToVariationObo\" target=\"new\">link</a> and try again.<br /><br /><br />\n"; next; }
    print "search for : $id ( $hash{id_to_name}{$id} )<br />\n";
    &searchWBVar($id, \%hash); }
} # sub queryVariation
 
sub searchWBVar {
  my ($id, $hash_ref) = @_;
  my %idtn = %$hash_ref;

  &populateCurators();

  # this doesn't work because it requires all tables to have a value.
#   my $result = $dbh->prepare( " SELECT app_tempname.joinkey, app_tempname.app_tempname, app_remark.app_remark, app_paper.app_paper, app_curator.app_curator FROM app_tempname, app_paper, app_curator, app_remark WHERE app_tempname.joinkey = app_remark.joinkey AND app_tempname.joinkey = app_curator.joinkey AND app_tempname.joinkey = app_paper.joinkey AND app_tempname.joinkey IN ( SELECT joinkey FROM app_tempname WHERE app_tempname ~ '$id' ) ;" ); 
  my %pgids;
#   my $result = $dbh->prepare( "SELECT joinkey FROM app_tempname WHERE app_tempname ~ '$id' ;" ); 
  my $result = $dbh->prepare( "SELECT joinkey FROM app_variation WHERE app_variation ~ '$id' ;" ); 	# changed from tempname to variation after splitting into 4 fields.  2010 09 20
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $pgids{$row[0]}++; }
  my $joinkeys = join"','", keys %pgids; 
  if ($joinkeys) {
#      my %hash; my @fields = qw( tempname obj_remark paper person curator allele_status ); my %entries;	# tempname now split into 4 fields  2010 09 24
     my %hash; my @fields = qw( variation obj_remark paper person curator allele_status ); my %entries;
     foreach my $field (@fields) {
       $result = $dbh->prepare( " SELECT * FROM app_$field WHERE joinkey IN ('$joinkeys');" ); 
       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
       while (my @row = $result->fetchrow) { 
#          if ($field =~ m/tempname/) { if ($idtn{id_to_name}{$row[1]}) { $row[1] .= ' ( ' . $idtn{id_to_name}{$row[1]} . ' )'; } }	# tempname now split into 4 fields  2010 09 24
         if ($field =~ m/variation/) { if ($idtn{id_to_name}{$row[1]}) { $row[1] .= ' ( ' . $idtn{id_to_name}{$row[1]} . ' )'; } }
         if ($field =~ m/curator/) { $row[1] =~ s/WBPerson/two/; $row[1] = $curator{joinkey_to_name}{$row[1]}; }
         $hash{$field}{$row[0]} = $row[1]; } }
     foreach my $pgid (sort keys %pgids) {
       my @entry = (); push @entry, $pgid;
       foreach my $field (@fields) { if ($hash{$field}{$pgid}) { push @entry, $hash{$field}{$pgid}; } else { push @entry, ""; } }
       my $entry = join"</td><td>", @entry; 
       $entry = "<tr bgcolor=\"ccffff\"><td>$entry</td></tr>\n";
       $entries{$entry}++; }
     if (keys %entries) {
       my $colspan = scalar(@fields); $colspan++;
       print "<table><tr bgcolor=\"ccffff\"><td colspan=\"$colspan\">Phenotype results</td></tr>\n";
       print "<tr bgcolor=\"ccffff\"><td>pgid</td><td>Variation</td><td>Object Remark</td><td>Paper</td><td>Person</td><td>Curator</td><td>Allele Status</td></tr>\n";
       foreach my $entry (sort keys %entries) { print $entry; }
       print "</table><br />\n"; } }
    else { print "No match in Phenotype curation<br />\n"; }

  %pgids = ();
  $result = $dbh->prepare( "SELECT joinkey FROM gop_with_wbvariation WHERE gop_with_wbvariation ~ '$id' ;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $pgids{$row[0]}++; }
  my $joinkeys = join"','", keys %pgids; 
  if ($joinkeys) {
     my %hash; my @fields = qw( with_wbvariation paper_evidence curator_evidence ); my %entries;
     foreach my $field (@fields) {
       $result = $dbh->prepare( " SELECT * FROM gop_$field WHERE joinkey IN ('$joinkeys');" ); 
       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
       while (my @row = $result->fetchrow) { 
         if ($field =~ m/with_wbvariation/) { 
           my (@ids) = $row[1] =~ m/\"(.*?)\"/g; my @values;
           foreach my $id (@ids) { if ($idtn{id_to_name}{$id}) { push @values, "$id ( $idtn{id_to_name}{$id} )"; } }
           $row[1] = join"<br />", @values; }
         if ($field =~ m/curator/) { $row[1] =~ s/WBPerson/two/; $row[1] = $curator{joinkey_to_name}{$row[1]}; }
         $hash{$field}{$row[0]} = $row[1]; } }
     foreach my $pgid (sort keys %pgids) {
       my @entry = (); push @entry, $pgid;
       foreach my $field (@fields) { if ($hash{$field}{$pgid}) { push @entry, $hash{$field}{$pgid}; } else { push @entry, ""; } }
       my $entry = join"</td><td>", @entry; 
       $entry = "<tr bgcolor=\"ccffff\"><td>$entry</td></tr>\n";
       $entries{$entry}++; }
     if (keys %entries) {
       my $colspan = scalar(@fields); $colspan++;
       print "<table><tr bgcolor=\"ccffff\"><td colspan=\"$colspan\">GO results</td></tr>\n";
       print "<tr bgcolor=\"ccffff\"><td>pgid</td><td>with Variation</td><td>Paper</td><td>Curator</td></tr>\n";
       foreach my $entry (sort keys %entries) { print $entry; }
       print "</table><br />\n"; } }
    else { print "No match in GO curation<br />\n"; }

  %pgids = ();
  $result = $dbh->prepare( "SELECT joinkey FROM grg_allele WHERE grg_allele ~ '$id' ;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $pgids{$row[0]}++; }
  my $joinkeys = join"','", keys %pgids; 
  if ($joinkeys) {
     my %hash; my @fields = qw( allele transregulator paper curator ); my %entries;
     foreach my $field (@fields) {
       $result = $dbh->prepare( " SELECT * FROM grg_$field WHERE joinkey IN ('$joinkeys');" ); 
       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
       while (my @row = $result->fetchrow) { 
         if ($field =~ m/allele/) {
           my (@ids) = $row[1] =~ m/\"(.*?)\"/g; my @values;
           foreach my $id (@ids) { if ($idtn{id_to_name}{$id}) { push @values, "$id ( $idtn{id_to_name}{$id} )"; } }
           $row[1] = join"<br />", @values; }
         if ($field =~ m/curator/) { $row[1] =~ s/WBPerson/two/; $row[1] = $curator{joinkey_to_name}{$row[1]}; }
         $hash{$field}{$row[0]} = $row[1]; } }
     foreach my $pgid (sort keys %pgids) {
       my @entry = (); push @entry, $pgid;
       foreach my $field (@fields) { if ($hash{$field}{$pgid}) { push @entry, $hash{$field}{$pgid}; } else { push @entry, ""; } }
       my $entry = join"</td><td>", @entry; 
       $entry = "<tr bgcolor=\"ccffff\"><td>$entry</td></tr>\n";
       $entries{$entry}++; }
     if (keys %entries) {
       my $colspan = scalar(@fields); $colspan++;
       print "<table><tr bgcolor=\"ccffff\"><td colspan=\"$colspan\">Gene Regulation results</td></tr>\n";
       print "<tr bgcolor=\"ccffff\"><td>pgid</td><td>grg_allele</td><td>grg_transregulator</td><td>grg_paper</td><td>grg_curator</td></tr>\n";
       foreach my $entry (sort keys %entries) { print $entry; }
       print "</table><br />\n"; } }
    else { print "No match in Gene Regulation curation<br />\n"; }

  %pgids = ();
  $result = $dbh->prepare( "SELECT joinkey FROM int_variationone WHERE int_variationone ~ '$id' ;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $pgids{$row[0]}++; }
  $result = $dbh->prepare( "SELECT joinkey FROM int_variationtwo WHERE int_variationtwo ~ '$id' ;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $pgids{$row[0]}++; }
  my $joinkeys = join"','", keys %pgids; 
  if ($joinkeys) {
     my %hash; my @fields = qw( name variationone geneone variationtwo genetwo paper curator ); my %entries;
     foreach my $field (@fields) {
       $result = $dbh->prepare( " SELECT * FROM int_$field WHERE joinkey IN ('$joinkeys');" ); 
       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
       while (my @row = $result->fetchrow) { 
         if ($field =~ m/variation/) {
           my (@ids) = $row[1] =~ m/\"(.*?)\"/g; my @values;
           foreach my $id (@ids) { if ($idtn{id_to_name}{$id}) { push @values, "$id ( $idtn{id_to_name}{$id} )"; } }
           $row[1] = join"<br />", @values; }
         if ($field =~ m/curator/) { $row[1] =~ s/WBPerson/two/; $row[1] = $curator{joinkey_to_name}{$row[1]}; }
         $hash{$field}{$row[0]} = $row[1]; } }
     foreach my $pgid (sort keys %pgids) {
       my @entry = (); push @entry, $pgid;
       foreach my $field (@fields) { if ($hash{$field}{$pgid}) { push @entry, $hash{$field}{$pgid}; } else { push @entry, ""; } }
       my $entry = join"</td><td>", @entry; 
       $entry = "<tr bgcolor=\"ccffff\"><td>$entry</td></tr>\n";
       $entries{$entry}++; }
     if (keys %entries) {
       my $colspan = scalar(@fields); $colspan++;
       print "<table><tr bgcolor=\"ccffff\"><td colspan=\"$colspan\">Interaction results</td></tr>\n";
       print "<tr bgcolor=\"ccffff\"><td>pgid</td><td>int_name</td><td>int_variationone</td><td>int_geneone</td><td>int_variationtwo</td><td>int_genetwo</td><td>grg_paper</td><td>grg_curator</td></tr>\n";
       foreach my $entry (sort keys %entries) { print $entry; }
       print "</table><br />\n"; } }
    else { print "No match in Interaction curation<br />\n"; }

  print "<br /><br />\n";
} # sub searchWBVar

sub updateFinalname {							# get list of $type data for curators to assign a final name
  my $type = shift;							# this should work for rnai, variation (allele), transgene 
  my %good;		# good alleles are in the list
  my %bad;		# bad alleles are alleles that have a tempname and are not good

  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi\">\n";

  my $line_number = 0;
  if ($type eq 'Phenotype') {
    &populateCurators();
    &populatePhobo();

    print "Suggest data through this CGI :<BR>\n";
    print "<TABLE BORDER=1>\n"; 
    print "<TR><TD>Suggested Term</TD><TD>Suggested Definition</TD><TD>Child Of</TD><TD>Curator</TD><TD>Evidence</TD></TR>\n";
    print "<TD VALIGN=TOP><INPUT NAME=suggested SIZE=50></TD>";
    print "<TD VALIGN=TOP><TEXTAREA ROWS=5 COLS=40 NAME=definition></TEXTAREA>";
    print "<TD VALIGN=TOP><TEXTAREA ROWS=5 COLS=40 NAME=childof></TEXTAREA>";
    print "<TD VALIGN=TOP><SELECT NAME=curator SIZE=6>";
    foreach my $name (sort keys %{ $curator{name_to_joinkey} }) { print "<OPTION VALUE=$curator{name_to_joinkey}{$name}>$name</OPTION>"; }
    print "</TD>";
    print "<TD VALIGN=TOP><TEXTAREA ROWS=5 COLS=40 NAME=evidence></TEXTAREA>";
    print "</TABLE>\n";
    print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Suggest !\"><BR><P><BR>\n"; 

    my %phn;
    my $result = $dbh->prepare( "SELECT * FROM phn_confirmed;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'confirmed'}{$row[0]} = $row[1]; }
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    $result = $dbh->prepare( "SELECT * FROM phn_comment;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'comment'}{$row[0]} = $row[1]++; }
    $result = $dbh->prepare( "SELECT * FROM phn_suggested;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'suggested'}{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM phn_definition;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'definition'}{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM phn_childof;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'childof'}{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM phn_curator;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'curator'}{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM phn_evidence;" ); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $phn{'evidence'}{$row[0]} = $row[1]; }
    print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm !\"><BR>\n"; 
    print "Data suggested through this CGI :<BR>\n";
    print "<TABLE BORDER=1>\n"; 
    print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Child Of</TD><TD>Curator</TD><TD>Evidence</TD></TR>\n";
    my $to_confirm_cgi = ''; my $confirmed_cgi = '';
    foreach my $joinkey (sort keys %{ $phn{suggested} }) {
      my ($suggested, $definition, $childof, $curator, $evidence);
      if ($phn{suggested}{$joinkey}) { $suggested = $phn{suggested}{$joinkey}; }
      if ($phn{definition}{$joinkey}) { $definition = $phn{definition}{$joinkey}; }
      if ($phn{childof}{$joinkey}) { $childof = $phn{childof}{$joinkey}; }
      if ($phn{curator}{$joinkey}) { $curator = $phn{curator}{$joinkey}; $curator =~ s/two/WBPerson/g; }
      if ($phn{evidence}{$joinkey}) { $evidence = $phn{evidence}{$joinkey}; }
      my $to_print = "<TR>";
      if ($phn{'confirmed'}{$joinkey}) { 
          $to_print .= "<TD VALIGN=TOP>$phn{confirmed}{$joinkey}</TD>\n";
          $to_print .= "<TD VALIGN=TOP>$phn{comment}{$joinkey}</TD>\n"; }
        else {
          $line_number++;
          $to_print .= "<TD VALIGN=TOP><INPUT NAME=\"term_$line_number\"></TD>\n";
          $to_print .= "<INPUT TYPE=HIDDEN NAME=\"joinkey_$line_number\" VALUE=\"$joinkey\">\n";
          $to_print .= "<TD VALIGN=TOP>$line_number<INPUT TYPE=checkbox NAME=\"reject_$line_number\" VALUE=checked></TD>\n";
          $to_print .= "<TD VALIGN=TOP><TEXTAREA NAME=\"comment_$line_number\" ROWS=5 COLS=40></TEXTAREA></TD>\n"; }
      $to_print .= "<TD VALIGN=TOP>$suggested</TD>\n";
      $to_print .= "<INPUT TYPE=HIDDEN NAME=\"suggested_$line_number\" VALUE=\"$suggested\">\n";
      $to_print .= "<TD VALIGN=TOP>$definition</TD>\n";
      $to_print .= "<TD VALIGN=TOP>$childof</TD>\n";
      $to_print .= "<TD VALIGN=TOP>$curator</TD>\n";
      $to_print .= "<TD VALIGN=TOP>$evidence</TD>\n";
      $to_print .= "</TR>\n";
      if ($phn{'confirmed'}{$joinkey}) { $confirmed_cgi .= $to_print; } else { $to_confirm_cgi .= $to_print; }
    } # foreach my $joinkey (sort keys %{ $phn{suggested} })
    print $to_confirm_cgi;
    print "</TABLE>\n";

    print "<P>Allele-Phenotype curation data :<TABLE BORDER=1>\n"; 
    print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Entity</TD></TR>\n";
    ($line_number, my $to_print) = &linePhenote('app_suggested', $line_number);
    print $to_print;
    print "</TABLE><BR><P><BR>\n";

    &showPhenoteTermNoDefinition();  

    print "<P>Confirmed Allele-Phenotype curation data :<TABLE BORDER=1>\n"; 
    print "<TR><TD>Confirm</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Entity</TD></TR>\n";
    ($line_number, my $to_print) = &linePhenote('phn_confirmed', $line_number);
    print $to_print;
    print "</TABLE><BR><P><BR>\n";

    print "Confirmed data suggested through this CGI :<BR>\n";
    print "<TABLE BORDER=1>\n"; 
    print "<TR><TD>Confirm</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Child Of</TD><TD>Curator</TD><TD>Evidence</TD></TR>\n";
    print $confirmed_cgi;
    print "</TABLE>\n";

#   } else {			# if $type eq Allele | Transgene # don't care about allele or transgene anymore  (xiaodong, wen, karen) 2010 09 24
#        
#     my %name_to_id;				# map to WBVarID for Jolene / Mary Ann  2010 05 12
#     my $map_file = '/home/acedb/work/allele_phenotype/varIDs_pub_name';
#     open (IN, "<$map_file") or die "Cannot open $map_file for variation ID to name mappings : $!";
#     while (my $line = <IN>) { chomp $line; my ($id, $name) = split/\t/, $line; $name_to_id{$name} = $id; }
#     close (IN) or die "Cannot close $map_file for variation ID to name mappings : $!";
# 
#     print "<P>Allele-Phenotype curation data :<TABLE BORDER=1>\n"; 
#     if ($type eq 'Allele') {
#       &populatePmids();
#       my $result = $dbh->prepare( "SELECT * FROM ali_alleleinfo;" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $good{allele}{$row[0]}++; }
#       $result = $dbh->prepare( "SELECT * FROM ali_yesmaryann;" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $good{allele}{$row[0]}++; $good{maryann}{$row[0]}++; }
#       $result = $dbh->prepare( "SELECT * FROM app_tempname WHERE joinkey IN (SELECT joinkey FROM app_type WHERE app_type = 'Allele');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { unless ($good{allele}{$row[1]}) { $bad{allele}{$row[1]}++; } }
#       $result = $dbh->prepare( "SELECT * FROM app_tempname WHERE joinkey IN (SELECT joinkey FROM app_allele_status WHERE app_allele_status != '') ;" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { unless ($good{maryann}{$row[1]}) { $bad{allele}{$row[1]}++; } }
#     } elsif ($type eq 'Transgene') {
#       my $result = $dbh->prepare( "SELECT * FROM tra_transgeneinfo;" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $good{allele}{$row[0]}++; }
#       $result = $dbh->prepare( "SELECT * FROM tra_yeswen;" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $good{allele}{$row[0]}++; }
#       $result = $dbh->prepare( "SELECT * FROM app_tempname WHERE joinkey IN (SELECT joinkey FROM app_type WHERE app_type = 'Transgene');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { unless ($good{allele}{$row[1]}) { $bad{allele}{$row[1]}++; } }
#     }
#     print "<TR><TD>Confirm</TD><TD>temp name</TD><TD>ID</TD><TD>WBPaper</TD><TD>WBPerson</TD><TD>Object Remark</TD><TD>Paper Remark</TD><TD>Allele Status</TD><TD>Curator</TD></TR>\n";
#     foreach my $allele (sort keys %{ $bad{allele} }) {
#       my $allele_info = '';
#       $line_number++;
#       $allele_info .= "<TR><TD><INPUT NAME=\"checked_$line_number\" TYPE=\"checkbox\" VALUE=\"checked\">";
#       if ($type eq 'Transgene') { $allele_info .= "<INPUT NAME=\"new_$line_number\">"; }
#       $allele_info .= "</TD><TD>$allele</TD>";
#       my $obj_id = ''; if ($name_to_id{$allele}) { $obj_id = $name_to_id{$allele}; }
#       $allele_info .= "<TD>$obj_id</TD>";
#       my $result = $dbh->prepare( "SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele';" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       my @joinkeys; while (my @row = $result->fetchrow) { push @joinkeys; $row[0]; }
#       my %app_data;
# 
#       $result = $dbh->prepare( "SELECT * FROM app_paper WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $app_data{paper}{$row[1]}++; }
#       my @paper_data = keys %{ $app_data{paper} };
#       foreach my $paper (@paper_data) { if ($pmids{$paper}) { $paper .= " ($pmids{$paper})"; } }
#       my $paper_data = join", ", @paper_data; unless ($paper_data) { $paper_data = '&nbsp;'; }
#       foreach my $paper (@paper_data) {
#         $result = $dbh->prepare( "SELECT * FROM app_paper_remark WHERE joinkey = '$paper';" );
#         $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#         while (my @row = $result->fetchrow) { $app_data{paper_remark}{$row[1]}++; } }
#       my @paper_remark_data = keys %{ $app_data{paper_remark} };
#       my $paper_remark_data = join"<BR>", @paper_remark_data; unless ($paper_remark_data) { $paper_remark_data = '&nbsp;'; }
# 
#       $result = $dbh->prepare( "SELECT * FROM app_person WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $app_data{person}{$row[1]}++; }
#       my @person_data = keys %{ $app_data{person} };
#       my $person_data = join", ", @person_data; unless ($person_data) { $person_data = '&nbsp;'; }
#       $person_data =~ s/\"//g; $person_data =~ s/,/,<BR>/g;
# 
# #       $result = $dbh->prepare( "SELECT * FROM app_strain WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
# #       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
# #       while (my @row = $result->fetchrow) { $app_data{strain}{$row[1]}++; }
# #       my @strain_data = keys %{ $app_data{strain} };
# #       my $strain_data = join", ", @strain_data; unless ($strain_data) { $strain_data = '&nbsp;'; }
# # 
# #       $result = $dbh->prepare( "SELECT * FROM app_genotype WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
# #       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
# #       while (my @row = $result->fetchrow) { $app_data{genotype}{$row[1]}++; }
# #       my @genotype_data = keys %{ $app_data{genotype} };
# #       my $genotype_data = join", ", @genotype_data; unless ($genotype_data) { $genotype_data = '&nbsp;'; }
# 
#       $result = $dbh->prepare( "SELECT * FROM app_obj_remark WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $app_data{obj_remark}{$row[1]}++; }
#       my @obj_remark_data = keys %{ $app_data{obj_remark} };
#       my $obj_remark_data = join", ", @obj_remark_data; unless ($obj_remark_data) { $obj_remark_data = '&nbsp;'; }
# 
#       $result = $dbh->prepare( "SELECT * FROM app_allele_status WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $app_data{allele_status}{$row[1]}++; }
#       my @allele_status_data = keys %{ $app_data{allele_status} };
#       my $allele_status_data = join", ", @allele_status_data; unless ($allele_status_data) { $allele_status_data = '&nbsp;'; }
# 
#       $result = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN (SELECT joinkey FROM app_tempname WHERE app_tempname = '$allele');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while (my @row = $result->fetchrow) { $app_data{curator}{$row[1]}++; }
#       my @curator_data = keys %{ $app_data{curator} };
#       my $curator_data = join", ", @curator_data; unless ($curator_data) { $curator_data = '&nbsp;'; }
#       $curator_data =~ s/\"//g;
#       if ($curator_data =~ m/WBcurator(\d+)/) {	# append name or email to WBcurators for wen 2008 03 24
#         my (@twos) = $curator_data =~ m/WBcurator(\d+)/g;
#         foreach my $two (@twos) {
#           my $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = 'two$two';" );
#           $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#           my $emails; my %emails;
#           while (my @row = $result->fetchrow) { $emails{$row[2]}++; $emails++; }
#           if ($emails) { my @emails = keys %emails; $emails = join", ", @emails; }
#             else {
#               my $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = 'two$two';" );
#               $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#               while (my @row = $result->fetchrow) { $emails{$row[1]}++; $emails++; }
#               if ($emails) { my @emails = keys %emails; $emails = join", ", @emails; } }
#           $curator_data =~ s/(WBcurator$two)/$1 ($emails)/g; } }
# 
#       $allele_info .= "<INPUT TYPE=HIDDEN NAME=\"tempname_$line_number\" VALUE=\"$allele\">\n";
#       $allele_info .= "<TD>$paper_data</TD>";
#       $allele_info .= "<TD>$person_data</TD>";
# #       $allele_info .= "<TD>$strain_data</TD>";
# #       $allele_info .= "<TD>$genotype_data</TD>";
#       $allele_info .= "<TD>$obj_remark_data</TD>";
#       $allele_info .= "<TD>$paper_remark_data</TD>";
#       $allele_info .= "<TD>$allele_status_data</TD>";
#       $allele_info .= "<TD>$curator_data</TD>";
#       $allele_info .= "</TR>\n";
#       print "$allele_info\n";
#     } # foreach my $allele (sort keys %{ $bad{allele} })
# 
#     if ($type eq 'Allele') { 	# check go data for alleles only
#       my @got_types = qw(bio cell mol);
#       my %got_data;
#       foreach my $type (@got_types) {
#         my $result = $dbh->prepare( "SELECT * FROM got_${type}_with ORDER BY got_timestamp;" );
#         $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#         while (my @row = $result->fetchrow) { $got_data{$type}{$row[0]}{$row[1]} = $row[2]; }
#       }
#       foreach my $type (@got_types) {
#         foreach my $wbgene (sort keys %{ $got_data{$type} }) {
#           foreach my $order (sort keys %{ $got_data{$type}{$wbgene} }) {
#             my $data = $got_data{$type}{$wbgene}{$order};
#             if ($data =~ m/^WB:.*?([a-z]+\d+).*?/g) { 
#               my @data;
#               if ($data =~ m/\|/) { @data = split/\|/, $data; } else { push @data, $data; }
#               foreach my $data (@data) {
#                 if ($data =~ m/\b([a-z]+\d+)\b/) { my $allele = $1; 
#                   unless ($good{allele}{$allele}) { $bad{fromgo}{$allele}{$type}{$wbgene}{$order}++; 
# #                     print "T $type G $wbgene O $order D $allele<BR>\n";
#                 } }
#       } } } } }
#       print "</TABLE>\n";
# 
#       print "<P>GO curation data :<TABLE BORDER=1>\n"; 
#       print "<TR><TD>Confirm</TD><TD>temp name</TD><TD>WBGene</TD><TD>WBPaper</TD><TD>WBPerson</TD><TD>Curator</TD></TR>\n";
#       foreach my $allele (sort keys %{ $bad{fromgo} }) {
#         my %data; my %genes;
#         foreach my $type (sort keys %{ $bad{fromgo}{$allele} }) {
#           foreach my $gene (sort keys %{ $bad{fromgo}{$allele}{$type} }) {
#             $genes{$gene}++;
#             foreach my $order (sort keys %{ $bad{fromgo}{$allele}{$type}{$gene} }) {
#               my $result = $dbh->prepare( "SELECT * FROM got_${type}_paper_evidence WHERE joinkey = '$gene' AND got_order = '$order' ORDER BY got_timestamp DESC;");
#               $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#               my @row = $result->fetchrow();
#               $data{paper}{$row[2]}++;
#               $result = $dbh->prepare( "SELECT * FROM got_${type}_person_evidence WHERE joinkey = '$gene' AND got_order = '$order' ORDER BY got_timestamp DESC;");
#               $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#               @row = $result->fetchrow();
#               $data{person}{$row[2]}++;
#               $result = $dbh->prepare( "SELECT * FROM got_${type}_curator_evidence WHERE joinkey = '$gene' AND got_order = '$order' ORDER BY got_timestamp DESC;");
#               $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#               @row = $result->fetchrow();
#               $data{curator}{$row[2]}++;
#         } } }
#         my @genes = keys %genes; 
#         my $wbgene = join", ", @genes; unless ($wbgene) { $wbgene = '&nbsp;'; }
#         my @curator_data = keys %{ $data{curator} };
#         my $curator_data = join", ", @curator_data; unless ($curator_data) { $curator_data = '&nbsp;'; }
#         my @person_data = keys %{ $data{person} };
#         my $person_data = join", ", @person_data; unless ($person_data) { $person_data = '&nbsp;'; }
#         my @paper_data = keys %{ $data{paper} };
#         foreach my $paper (@paper_data) { if ($pmids{$paper}) { $paper .= " ($pmids{$paper})"; } }
#         my $paper_data = join", ", @paper_data; unless ($paper_data) { $paper_data = '&nbsp;'; } $paper_data =~ s/,/<BR>/g;
#         $line_number++;
#         print "<TR><TD><INPUT NAME=\"checked_$line_number\" TYPE=\"checkbox\" VALUE=\"checked\">";
#         print "<TD>$allele</TD><TD>$wbgene</TD>";
#         print "<INPUT TYPE=HIDDEN NAME=\"tempname_$line_number\" VALUE=\"$allele\">\n";
#         print "<TD>$paper_data</TD>";
#         print "<TD>$person_data</TD>";
#         print "<TD>$curator_data</TD>";
#         print "</TR>\n";
#       } 
#       print "</TABLE>\n";
# 
#       my $infile = '/home/acedb/xiaodong/gene_regulation_new_objects/check_new_allele';
#       $/ = '';
#       open (IN, "<$infile") or die "Cannot open $infile : $!";
#       while (my $entry = <IN>) {
#         if ($entry =~ m/\nAllele\s+\"(.*)\"/) {
#           my $allele = $1;
#           unless ($good{allele}{$allele}) { 
#             $bad{fromgenereg}{$allele}{object}++;
#              if ($entry =~ m/\nTrans_regulated_gene\s+\"(.*)\"/) { $bad{fromgenereg}{$allele}{gene}{$1}++; }
#              if ($entry =~ m/\nReference\s+\"(.*)\"/) { $bad{fromgenereg}{$allele}{paper}{$1}++; } } } }
#       close (IN) or die "Cannot close $infile : $!";
#       $/ = "\n";
#       print "<P>Gene Regulation data :<TABLE BORDER=1>\n"; 
#       print "<TR><TD>Confirm</TD><TD>temp name</TD><TD>WBGene</TD><TD>WBPaper</TD><TD>Curator</TD></TR>\n";
#       foreach my $allele (sort keys %{ $bad{fromgenereg} }) {
#         my @gene_data = keys %{ $bad{fromgenereg}{$allele}{gene} };
#         my $gene_data = join", ", @gene_data; unless ($gene_data) { $gene_data = '&nbsp;'; }
#         my @paper_data = keys %{ $bad{fromgenereg}{$allele}{paper} };
#         foreach my $paper (@paper_data) { if ($pmids{$paper}) { $paper .= " ($pmids{$paper})"; } }
#         my $paper_data = join", ", @paper_data; unless ($paper_data) { $paper_data = '&nbsp;'; }
#         $line_number++;
#         print "<TR><TD><INPUT NAME=\"checked_$line_number\" TYPE=\"checkbox\" VALUE=\"checked\">";
#         print "<INPUT TYPE=HIDDEN NAME=\"tempname_$line_number\" VALUE=\"$allele\">\n";
#         print "<TD>$allele</TD><TD>$gene_data</TD><TD>$paper_data</TD><TD>Xiaodong Wang</TD>\n";
#         print "</TR>\n";
#       } # foreach my $allele (sort keys %{ $bad{fromgenereg} })
#       print "</TABLE>\n";
#     } # if ($type eq 'Allele') 

  } # else # if $type eq Allele | Transgene

  print "</TABLE>\n";
  print "<INPUT TYPE=HIDDEN NAME=\"tempname_count\" VALUE=\"$line_number\">$line_number entries<BR>\n";
  print "<INPUT TYPE=HIDDEN NAME=\"type\" VALUE=\"$type\">\n";
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm !\"><BR>\n"; 
  print "</FORM>\n";
} # sub updateFinalname


sub showPhenoteTermNoDefinition {
  my %filter;
  print "Allele-Phenotype data with Phenotype and no definition : <TABLE BORDER=1>\n"; 
  print "<TR><TD>Term</TD><TD>Suggested Definition</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Entity</TD></TR>\n";
  my $result = $dbh->prepare( " SELECT app_term.joinkey, app_term.app_term, app_suggested_definition.app_suggested_definition FROM app_term, app_suggested_definition WHERE app_term.app_term IS NOT NULL AND app_suggested_definition.app_suggested_definition IS NOT NULL AND app_term.joinkey = app_suggested_definition.joinkey ; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $filter{$row[1]}{def}{$row[2]}++; $filter{$row[1]}{pgdbid}{$row[0]}++; }
  foreach my $term (sort keys %filter) {
    next if ($phobo{$term}{def});
    my @defs; my @pgdbid;
    foreach my $def (keys %{ $filter{$term}{def} }) { push @defs, $def; }
    my $def = join", ", @defs; 
    foreach my $pgdbid (keys %{ $filter{$term}{pgdbid} }) { push @pgdbid, $pgdbid; }
    my $pgdbid = join"', '", @pgdbid; $pgdbid = "'$pgdbid'";
    next unless ($pgdbid); next unless ($def);
    print "<TR><TD VALIGN=top>$term <FONT SIZE=-1>($phobo{$term}{name})</FONT></TD><TD VALIGN=top>$def</TD>\n";
    my $result2 = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN ($pgdbid);" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; } my %emails = (); my %twos = ();
    foreach my $cur (sort keys %filter2) { if ($cur =~ m/WBcurator(\d+)/) { my $two = $1; $twos{$two}++; } }
    my @twos = sort keys %twos; my $twos = join", WBPerson", @twos;
    print "<TD VALIGN=TOP>WBPerson$twos</TD>";
    $result2 = $dbh->prepare( "SELECT * FROM app_paper WHERE joinkey IN ($pgdbid);" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; }
    my @paper = sort keys %filter2; my $paper = join"<BR><BR>", @paper; 
    print "<TD VALIGN=TOP>$paper</TD>";
    $result2 = $dbh->prepare( "SELECT * FROM app_entity WHERE joinkey IN ($pgdbid);" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; }
    my @entity = sort keys %filter2; my $entity = join"<BR><BR>", @entity; 
    print "<TD VALIGN=TOP>$entity</TD>";
    print "</TR>\n";
  } # foreach my $term (sort keys %filter)
  print "</TABLE><BR><P><BR>\n";
} # sub showPhenoteTermNoDefinition

sub linePhenote {
  my ($table, $line_number) = @_;
  my %sug; my %filter; my $to_print = '';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey !~ '^0' AND $table IS NOT NULL;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $sug{$row[1]}++; }
  foreach my $sug (sort keys %sug) {
    next unless ($sug);
    $to_print .= "<TR>";
    if ($table eq 'app_suggested') {
        $line_number++;
        $to_print .= "<TD VALIGN=TOP><INPUT NAME=\"term_$line_number\"></TD>\n";
        $to_print .= "<TD VALIGN=TOP>$line_number<INPUT TYPE=checkbox NAME=\"reject_$line_number\" VALUE=checked></TD>\n";
        $to_print .= "<TD VALIGN=TOP><TEXTAREA NAME=\"comment_$line_number\" ROWS=5 COLS=40></TEXTAREA></TD>\n";
        $to_print .= "<TD VALIGN=TOP>$sug</TD>";
        $to_print .= "<INPUT TYPE=HIDDEN NAME=\"suggested_$line_number\" VALUE=\"$sug\">\n"; }
      else {
        $result = $dbh->prepare( "SELECT * FROM phn_confirmed WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; }
        my @confirmed = sort keys %filter; my $confirmed = join"<BR><BR>", @confirmed; 
        $result = $dbh->prepare( "SELECT * FROM phn_comment WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; }
        my @comment = sort keys %filter; my $comment = join"<BR><BR>", @comment; 
        $to_print .= "<TD VALIGN=TOP>$confirmed</TD>\n";
        $to_print .= "<TD VALIGN=TOP>$comment</TD>\n";
        $to_print .= "<TD VALIGN=TOP>$sug</TD>"; }
    $result = $dbh->prepare( "SELECT * FROM app_suggested_definition WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; }
    my @sd = sort keys %filter; my $sugdef = join"<BR><BR>", @sd; 
    $to_print .= "<TD VALIGN=TOP>$sugdef</TD>";
    $result = $dbh->prepare( "SELECT * FROM app_child_of WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; } my @co = ();
    foreach my $co (sort keys %filter) {
      my (@phen) = split/,/, $co;
      foreach my $phen (@phen) { $phen =~ s/\"//g; $phen .= " <FONT SIZE=-1>($phobo{$phen}{name})</FONT>"; }
      $co = join", ", @phen; push @co, $co; }
    my $childof = join"<BR><BR>", @co; 
    $to_print .= "<TD VALIGN=TOP>$childof</TD>";
    $result = $dbh->prepare( "SELECT * FROM app_curator WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; } my %emails = (); my %twos = ();
    foreach my $cur (sort keys %filter) {
      if ($cur =~ m/WBcurator(\d+)/) { 
        my $two = $1; $twos{$two}++; my $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = 'two$two';" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        while (my @row = $result->fetchrow) { $emails{$row[2]}++; } } }
    my @emails = sort keys %emails; my $emails = join", ", @emails;
    my @twos = sort keys %twos; my $twos = join", WBPerson", @twos;
    $to_print .= "<TD VALIGN=TOP>WBPerson$twos</TD>";
#     if ($table eq 'app_suggested') { $to_print .= "<INPUT TYPE=HIDDEN NAME=\"email_$line_number\" VALUE=\"$emails\">\n"; }
    $to_print .= "<INPUT TYPE=HIDDEN NAME=\"email_$line_number\" VALUE=\"$emails\">\n"; 
    $result = $dbh->prepare( "SELECT * FROM app_paper WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; }
    my @paper = sort keys %filter; my $paper = join"<BR><BR>", @paper; 
    $to_print .= "<TD VALIGN=TOP>$paper</TD>";
    $result = $dbh->prepare( "SELECT * FROM app_entity WHERE joinkey IN (SELECT joinkey FROM $table WHERE joinkey !~ '^0' AND $table = '$sug');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter = (); while (my @row = $result->fetchrow) { next unless ($row[1] =~ m/\S/) ; $filter{$row[1]}++; }
    my @entity = sort keys %filter; my $entity = join"<BR><BR>", @entity; 
    $to_print .= "<TD VALIGN=TOP>$entity</TD>";
    $to_print .= "</TR>\n";
  } # foreach my $sug (sort keys %sug)
  return ($line_number, $to_print);
} # sub linePhenote

sub populatePmids {
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid' ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { my $key = 'WBPaper' . $row[0]; $pmids{$key} = $row[1]; }
} # sub populatePmids

sub populatePhobo {
  my $obofile = get "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/phenotype_ontology_obo.cgi";
  my (@entries) = split/\n\n/, $obofile;
  foreach my $para (@entries) {
    next unless ($para =~ m/id:/);
    my ($id) = $para =~ m/id: (WBPhenotype:\d+)/;
    my ($name) = $para =~ m/name: (.*)\n/;
    my ($def) = $para =~ m/def: \"(.*?)\"/;
    $phobo{$id}{name} = $name;
    $phobo{$id}{def} = $def; }
#   my $directory = '/home/postgres/work/citace_upload/allele_phenotype/temp';
#   chdir($directory) or die "Cannot go to $directory ($!)";
#   `cvs -d /var/lib/cvsroot checkout PhenOnt`;
#   my $file = $directory . '/PhenOnt/PhenOnt.obo';
#   $/ = "";
#   open (IN, "<$file") or die "Cannot open $file : $!";
#   while (my $para = <IN>) { 
#     next unless ($para =~ m/id:/);
#     my ($id) = $para =~ m/id: (WBPhenotype:\d+)/;
#     my ($name) = $para =~ m/name: (.*)\n/;
#     my ($def) = $para =~ m/def: \"(.*?)\"/;
#     $phobo{$id}{name} = $name;
#     $phobo{$id}{def} = $def; }
#   close (IN) or die "Cannot close $file : $!";
#   $directory .= '/PhenOnt';
#   `rm -rf $directory`;
} # sub populatePhobo

sub populateCurators {
  $curator{name_to_joinkey}{"Igor Antoshechkin"} = 'two22';
  $curator{name_to_joinkey}{"Juancarlos Chan"} = 'two1823';
  $curator{name_to_joinkey}{"Wen Chen"} = 'two101';
  $curator{name_to_joinkey}{"Paul Davis"} = 'two1983';
  $curator{name_to_joinkey}{"Jolene S. Fernandes"} = 'two2021';
  $curator{name_to_joinkey}{"Chris"} = 'two2987';
  $curator{name_to_joinkey}{"Ranjana Kishore"} = 'two324';
  $curator{name_to_joinkey}{"Raymond Lee"} = 'two363';
  $curator{name_to_joinkey}{"Cecilia Nakamura"} = 'two1';
  $curator{name_to_joinkey}{"Tuco"} = 'two480';
  $curator{name_to_joinkey}{"Anthony Rogers"} = 'two1847';
  $curator{name_to_joinkey}{"Gary C. Schindelman"} = 'two557';
  $curator{name_to_joinkey}{"Erich Schwarz"} = 'two567';
  $curator{name_to_joinkey}{"Paul Sternberg"} = 'two625';
  $curator{name_to_joinkey}{"Mary Ann Tuli"} = 'two2970';
  $curator{name_to_joinkey}{"Kimberly Van Auken"} = 'two1843';
  $curator{name_to_joinkey}{"Qinghua Wang"} = 'two736';
  $curator{name_to_joinkey}{"Xiaodong Wang"} = 'two1760';
  $curator{name_to_joinkey}{"Karen Yook"} = 'two712';
  $curator{joinkey_to_name}{'two22'} = "Igor Antoshechkin";
  $curator{joinkey_to_name}{'two1823'} = "Juancarlos Chan";
  $curator{joinkey_to_name}{'two101'} = "Wen Chen";
  $curator{joinkey_to_name}{'two1983'} = "Paul Davis";
  $curator{joinkey_to_name}{'two2021'} = "Jolene S. Fernandes";
  $curator{joinkey_to_name}{'two2987'} = "Chris";
  $curator{joinkey_to_name}{'two324'} = "Ranjana Kishore";
  $curator{joinkey_to_name}{'two363'} = "Raymond Lee";
  $curator{joinkey_to_name}{'two1'} = "Cecilia Nakamura";
  $curator{joinkey_to_name}{'two480'} = "Tuco";
  $curator{joinkey_to_name}{'two1847'} = "Anthony Rogers";
  $curator{joinkey_to_name}{'two557'} = "Gary C. Schindelman";
  $curator{joinkey_to_name}{'two567'} = "Erich Schwarz";
  $curator{joinkey_to_name}{'two625'} = "Paul Sternberg";
  $curator{joinkey_to_name}{'two2970'} = "Mary Ann Tuli";
  $curator{joinkey_to_name}{'two1843'} = "Kimberly Van Auken";
  $curator{joinkey_to_name}{'two736'} = "Qinghua Wang";
  $curator{joinkey_to_name}{'two1760'} = "Xiaodong Wang";
  $curator{joinkey_to_name}{'two712'} = "Karen Yook";
} # sub populateCurators



__END__


DEPRECATED

sub getFinalnameLine {							# get a table row of type data
  my ($tempname, $final, $paper, $line_number) = @_;
#   my $line = "<FORM METHOD=POST ACTION=http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi>\n";
  my $line = "<INPUT TYPE=HIDDEN NAME=\"tempname_$line_number\" VALUE=\"$tempname\">\n";
  $line .= "<TR><TD>$tempname</TD><TD><INPUT NAME=\"final_$line_number\" VALUE=$final></TD>\n";
  my $paper_link = $paper; if ($paper =~ m/(\d{8})/) { $paper_link = $1; }
  if ($paper_link) { my $result = $dbh->prepare( "SELECT wpa_identifier FROM wpa_identifier WHERE joinkey ~ '$paper_link' AND wpa_identifier ~ 'pmid';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow; if ($row[0]) { $paper .= '(' . $row[0] . ')'; } }		# add pmid for Mary Ann  2005 11 22
  $line .= "<TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?action=Number+%21&number=$paper_link TARGET=new>$paper</A>&nbsp;</TD>\n";
  $line .= "<TD><A HREF=http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi?action=Get+Data+%21&tempname=$tempname TARGET=new>Get Data</A></TD>\n";
  $line .= "<TD><INPUT NAME=\"checked_$line_number\" TYPE=\"checkbox\" VALUE=\"checked\">";
#   $line .= "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm Final Name !\"></TD></TR>\n"; 
#   $line .= "</FORM>\n";
  return $line;
} # sub getFinalnameLine


# from updateFinalname
#   my ($var, $page) = &getHtmlVar($query, 'page');
#   unless ($page) { $page = 0; } else { $page--; }			# subtract from page to count arrays from zero
#   my %rnai; my %final; my %paper; my @rnai; my @final; my @nofinal;
#   my $result = $dbh->prepare( "SELECT * FROM alp_type WHERE alp_type = '$type'; ");
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { $rnai{$row[0]}++; }
#   $result = $dbh->prepare( "SELECT * FROM alp_finalname ORDER BY alp_timestamp; ");
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { $final{$row[0]} = $row[1]; }
#   $result = $dbh->prepare( "SELECT * FROM alp_paper ORDER BY alp_timestamp; ");
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { if ($row[2]) { $paper{$row[0]} = $row[2]; } }
#   print "<TABLE BORDER=1>\n";
#   print "<TR><TD>temp name</TD><TD>final name</TD><TD>WBPaper</TD><TD>Get text data</TD><TD>Confirm final name</TD></TR>\n";
#   my $withfinal = ''; my $withoutfinal = '';				# entries with finalname / without finalname for printing
#   foreach my $tempname (sort { $paper{$a} <=> $paper{$b} } keys %rnai) {	# sort by papers for Mary Ann 2005 12 06
#     if ($final{$tempname}) { push @final, $tempname; }			# store finals and no finals in an array
#       else { push @nofinal, $tempname; } }
#   if ($type eq 'Allele') { 	# for Mary Ann only show those without Final name in two groups, older than a day and recent 2006 10 23
#     @final = (); 							# don't show final names for Variation for Mary Ann
#     my %nofinal = ();  foreach my $nofinal (@nofinal) { $nofinal{$nofinal}++; }	# put in hash to check if should store them
#     my @first; my @second; @nofinal = ();				# order nofinals in two groups for Mary Ann (one day recent, and older)
#     $result = $dbh->prepare( " SELECT * FROM alp_type WHERE alp_type = 'Allele' AND alp_timestamp > ( SELECT date_trunc('second', now())-'1 days'::interval ) ORDER BY joinkey; " );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     while (my @row = $result->fetchrow) { if ($nofinal{$row[0]}) { push @first, $row[0]; } }	# those recent than one day in alphabetical order
#     $result = $dbh->prepare( " SELECT * FROM alp_type WHERE alp_type = 'Allele' AND alp_timestamp <= ( SELECT date_trunc('second', now())-'1 days'::interval ) ORDER BY joinkey; " );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#     while (my @row = $result->fetchrow) { if ($nofinal{$row[0]}) { push @second, $row[0]; } }	# those older than one day in alphabetical order
#     foreach (@first) { push @nofinal, $_; } foreach (@second) { push @nofinal, $_; }	# put them back in nofinal array for display
#   } # if ($type eq 'Allele') 
#   my $nofinals = scalar(@nofinal);					# entries without a final name
#   my $per_page = 20;							# entries per page
#   my $pages = 1 + (scalar (@final) / $per_page) + (scalar (@nofinal) / $per_page);		# find out how many pages there are
#   for (1 .. ($page * $per_page)) { if (@nofinal) { shift @nofinal; } else { shift @final; } }	# depending on the page, skip entries from nofinal and then from final
#   for my $line_number (1 .. $per_page) {
#     my $tempname;							# grab the tempname from nofinal or final as appropriate
#     if (@nofinal) { $tempname = shift @nofinal; }
#       elsif (@final) { $tempname = shift @final; }
#       else { next; }
#     my $line = &getFinalnameLine($tempname, $final{$tempname}, $paper{$tempname}, $line_number);	# generate the line
#     if ($final{$tempname}) { $withfinal .= $line; }			# put it with final or without final as appropriate
#       else { $withoutfinal .= $line; } }
# 
#   $page++;								# add back the subtracted one for displaying the page number counting from 1
#   print "<FORM METHOD=POST ACTION=http://tazendra.caltech.edu/~postgres/cgi-bin/new_objects.cgi>\n";
#   print "<INPUT TYPE=HIDDEN NAME=per_page VALUE=$per_page>\n";
#   print "<INPUT TYPE=HIDDEN NAME=pages VALUE=$pages>\n";
#   print "<INPUT TYPE=HIDDEN NAME=type VALUE=$type>\n";
#   print "Select another page : <SELECT NAME=\"page\" SIZE=1>\n";
#   foreach (1 .. $pages) { if ($_ == $page) { print "      <OPTION SELECTED>$_</OPTION>\n"; } else { print "      <OPTION>$_</OPTION>\n"; } }
#   print "    </SELECT>\n";
#   if ($type eq 'RNAi') { print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update RNAi !\">\n"; }
#   elsif ($type eq 'Transgene') { print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update Trasgene !\">\n"; }
#   elsif ($type eq 'Allele') { print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Update Variation !\">\n"; }
#   print " (and click this button)<BR><BR>\n";
#   print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm Final Name !\"><BR>\n"; 
#   print "$withoutfinal<TR><TD colspan=5><FONT COLOR=green>The following already have been curated and already have a final name.</FONT></TD></TR>$withfinal";
#   print "</TABLE>\n";
#   print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm Final Name !\"><BR>\n"; 
#   print "</FORM>\n";
# end from updateFinalname
