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
#
# changed phn_confirmed to have extra column phn_datatype with values 'form' 'rna' 'app' 
# to account for new suggested terms through RNAi OA from rna_ tables.  
# modified  &updateFinalname('Phenotype')  +  &confirm  +  &linePhenote  to handle rna_ 
# data as well as app_ data.  2014 07 18
#
# rewriting all the Phenotype stuff to work with new phn_oadata table instead of old 
# phn_ tables.  2014 10 24
#
# CREATE TABLE phn_oadata ( phenotype text, reject text, comment text, suggested text, suggested_definition text, placeholder text, child_of text, curator text, paper text, entity text, datatype text, pgids text, phn_timestamp timestamp with time zone DEFAULT "timestamp"('now'::text));
# GRANT ALL ON TABLE phn_oadata TO acedb;
# GRANT ALL ON TABLE phn_oadata TO apache;
# GRANT ALL ON TABLE phn_oadata TO azurebrd;
# GRANT ALL ON TABLE phn_oadata TO cecilia;
# GRANT ALL ON TABLE phn_oadata TO "www-data";
#
# also store in postgres the placeholder term in app_term / rna_phenotype.
# sort all tables by timestamp, but use jquery to make previous results sortable.
# also email karen + chris each time gary confirms anything.
# live on tazendra.  2014 10 31
#
# app_entity table removed, so removed from display.  2015 10 08
#
# changed  &showOaTermNoWBPhenotype  to show the curator name, or look at 
# correspoding communitycurator table and get the WBPerson from there. 
# For Chris and Gary.  2016 07 25





use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate mailer
use LWP::UserAgent;	# getting sanger files for querying
use LWP::Simple;	# get the PhenOnt.obo from a cgi
use DBI;


my %curator;
my %phobo;

my %previouslySuggested;	# terms that were previously suggested and exist in phn_oadata

my %pmids;

my $query = new CGI;	# new CGI form
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


# &printHeader('New Objects Curation Form');	# normal form view
  print <<"EndOfText";
Content-type: text/html\n\n

<HTML>
<HEAD>
<LINK rel="stylesheet" type="text/css" href="http://minerva.caltech.edu/~azurebrd/stylesheets/wormbase.css">
<title>New Objects Curation Form</title>
  <script type="text/javascript" src="js/jquery-1.9.1.min.js"></script>
  <script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
  <script type="text/javascript">\$(function() { \$("table").tablesorter({widthFixed: true, widgets: ['zebra']}).tablesorterPager({container: \$("#pager")}); });</script>
</HEAD>

<BODY bgcolor=#aaaaaa text=#000000 link=cccccc alink=eeeeee vlink=bbbbbb>
<HR>
</body></html>

EndOfText

&process();
&printFooter();

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  unless ($action) { $action = ''; }
  if ($action eq '') { &printHtmlMenu(); }		# Display form, first time, no action
  else { 						# Form Button
    print "ACTION : $action : ACTION<BR>\n"; 
    if ($action eq 'Update Phenotype !') {             &updateFinalname('Phenotype'); }	# table of Variation data for Mary Ann
      elsif ($action eq 'Confirm !') {                 &confirm(); }
      elsif ($action eq 'Query Variation !') {         &queryVariation(); }		# query for Variation data for Mary Ann
      elsif ($action eq 'Update Strains !') {          &updateStrains(); }		# suggested strains from dit_ and dis_
      elsif ($action eq 'Commit Strains') {            &commitStrains(); }		# email Ranjana Strain results
    print "ACTION : $action : ACTION<BR>\n"; 
  } # else # if ($action eq '') { &printHtmlForm(); }
} # sub process

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
  if ($type eq 'Phenotype') {
    print <<"    EndOfText";
    <FORM METHOD="POST" ACTION="new_objects.cgi">
    <TABLE border=0>
    <TR>
      <TD COLSPAN=3><B>Update Phenotype : </B></TD>
      <TD><INPUT TYPE="submit" NAME="action" VALUE="Update Phenotype !"></TD>
    <TR>
    </table></form>
    EndOfText
    my $email_body_app_rna = '';
    my $email_body_dis_dit = '';
    ($oop, my $tempname_count) = &getHtmlVar($query, 'tempname_count');
    my $error = 0;
    my @pgcommands;
    for my $i (1 .. $tempname_count) {
# print "BLAH $i<br>";
      my ($phenotype, $reject)   = ('', '');
      ($oop, $phenotype)         = &getHtmlVar($query, "phenotype_$i");
      ($oop, $reject)            = &getHtmlVar($query, "reject_$i");
      ($oop, my $comment)        = &getHtmlVar($query, "comment_$i");
      ($oop, my $suggested)      = &getHtmlVar($query, "suggested_$i");
      ($oop, my $definition)     = &getHtmlVar($query, "suggested_definition_$i");
      ($oop, my $placeholder)    = &getHtmlVar($query, "placeholder_$i");
      ($oop, my $child_of)       = &getHtmlVar($query, "child_of_$i");
      ($oop, my $curator)        = &getHtmlVar($query, "curator_$i");
      ($oop, my $paper)          = &getHtmlVar($query, "paper_$i");
      ($oop, my $entity)         = &getHtmlVar($query, "entity_$i");
      ($oop, my $datatype)       = &getHtmlVar($query, "datatype_$i");
      ($oop, my $pgids)          = &getHtmlVar($query, "pgids_$i");
      if ($phenotype || $reject) { 
        if ( ($datatype eq 'app') || ($datatype eq 'rna') ) {
            $email_body_app_rna .= qq(<tr><td>$phenotype</td><td>$reject</td><td>$comment</td><td>$suggested</td><td>$definition</td><td>$placeholder</td><td>$child_of</td><td>$curator</td><td>$paper</td><td>$entity</td><td>$datatype</td><td>$pgids</td></tr>\n); }
          elsif ( ($datatype eq 'dis') || ($datatype eq 'dit') ) {
            $email_body_dis_dit .= qq(<tr><td>$phenotype</td><td>$reject</td><td>$comment</td><td>$suggested</td><td>$definition</td><td>$placeholder</td><td>$child_of</td><td>$curator</td><td>$paper</td><td>$entity</td><td>$datatype</td><td>$pgids</td></tr>\n); } }
      my (@pgids)                = $pgids =~ m/(\d+)/g;
      if ($pgids =~ m/\'/)       { $pgids      =~ s/\'/''/g; }
      if ($comment =~ m/\'/)     { $comment    =~ s/\'/''/g; }
      if ($suggested =~ m/\'/)   { $suggested  =~ s/\'/''/g; }
      if ($definition =~ m/\'/)  { $definition =~ s/\'/''/g; }
      if ($reject eq 'checked')  { $reject = 'rejected'; }
      if ($phenotype && $reject) { $reject = ''; print "$i has $phenotype and rejected, approving with $phenotype\n"; }
      next unless ($phenotype || $reject);
      my $pgcommand;
      if ($reject) {
          my $pgTable = $datatype . '_suggested';
          if ( ($datatype eq 'dis') || ($datatype eq 'dit') ) { $pgTable = $datatype . '_suggested_phenotype'; }
          foreach my $joinkey (@pgids) { 
            $pgcommand = "DELETE FROM $pgTable WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand;
            $pgcommand = "INSERT INTO ${pgTable}     VALUES ('$joinkey', 'REJECTED $suggested', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand;
            $pgcommand = "INSERT INTO ${pgTable}_hst VALUES ('$joinkey', 'REJECTED $suggested', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand; } }
        elsif ($phenotype) {
          if ( ($datatype eq 'dis') || ($datatype eq 'dit') ) {		# only update suggested table for disease
              my $pgTable = $datatype . '_suggested_phenotype';
              foreach my $joinkey (@pgids) { 
                $pgcommand = "DELETE FROM $pgTable WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand;
                $pgcommand = "INSERT INTO ${pgTable}     VALUES ('$joinkey', 'ACCEPTED $suggested', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand;
                $pgcommand = "INSERT INTO ${pgTable}_hst VALUES ('$joinkey', 'ACCEPTED $suggested', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand; } }
            elsif ( ($datatype eq 'app') || ($datatype eq 'rna') ) { 	# only update phenotype data for variation and rnai, not for disease
              my $pgTable = 'app_term';
              if ($datatype eq 'rna') { $phenotype = '"' . $phenotype . '"'; $pgTable = 'rna_phenotype'; }
              foreach my $joinkey (@pgids) { 
                $pgcommand = "DELETE FROM ${datatype}_suggested WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand;
                $pgcommand = "DELETE FROM $pgTable WHERE joinkey = '$joinkey'"; push @pgcommands, $pgcommand;
                $pgcommand = "INSERT INTO ${pgTable}     VALUES ('$joinkey', '$phenotype', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand;
                $pgcommand = "INSERT INTO ${pgTable}_hst VALUES ('$joinkey', '$phenotype', CURRENT_TIMESTAMP)"; push @pgcommands, $pgcommand; } } }
      if ($phenotype) { $phenotype = "'$phenotype'"; } else { $phenotype = 'NULL'; }
      if ($reject) { $reject = "'$reject'"; } else { $reject = 'NULL'; }
      if ($comment) { $comment = "'$comment'"; } else { $comment = 'NULL'; }
      if ($suggested) { $suggested = "'$suggested'"; } else { $suggested = 'NULL'; }
      if ($definition) { $definition = "'$definition'"; } else { $definition = 'NULL'; }
      if ($placeholder) { $placeholder = "'$placeholder'"; } else { $placeholder = 'NULL'; }
      if ($child_of) { $child_of = "'$child_of'"; } else { $child_of = 'NULL'; }
      if ($curator) { $curator = "'$curator'"; } else { $curator = 'NULL'; }
      if ($paper) { $paper = "'$paper'"; } else { $paper = 'NULL'; }
      if ($entity) { $entity = "'$entity'"; } else { $entity = 'NULL'; }
      if ($datatype) { $datatype = "'$datatype'"; } else { $datatype = 'NULL'; }
      if ($pgids) { $pgids = "'$pgids'"; } else { $pgids = 'NULL'; }
      $pgcommand = qq(INSERT INTO phn_oadata VALUES ($phenotype, $reject, $comment, $suggested, $definition, $placeholder, $child_of, $curator, $paper, $entity, $datatype, $pgids, CURRENT_TIMESTAMP)); 
      push @pgcommands, $pgcommand;
    } # for my $i (1 .. $tempname_count)
    if ($email_body_app_rna) { 
      $email_body_app_rna = qq(<table border="1" style="empty-cells: show"><tr><th>phenotype</th><th>reject</th><th>comment</th><th>suggested</th><th>definition</th><th>placeholder</th><th>child_of</th><th>curator</th><th>paper</th><th>entity</th><th>datatype</th><th>pgids</th></tr>\n) . $email_body_app_rna . qq(</table>\n);
      print qq($email_body_app_rna);
      my $user    = 'new_objects.cgi';
#       my $email   = 'azurebrd@tazendra.caltech.edu';
#       my $email   = 'closertothewake@gmail.com';
      my $email   = 'kyook@caltech.edu, cgrove@caltech.edu';
      my $subject = 'new_object.cgi values confirmed / rejected';
      &mail_simple($user, $email, $subject, $email_body_app_rna);
    } # if ($email_body_app_rna)
    if ($email_body_dis_dit) { 
      $email_body_dis_dit = qq(<table border="1" style="empty-cells: show"><tr><th>phenotype</th><th>reject</th><th>comment</th><th>suggested</th><th>definition</th><th>placeholder</th><th>child_of</th><th>curator</th><th>paper</th><th>entity</th><th>datatype</th><th>pgids</th></tr>\n) . $email_body_dis_dit . qq(</table>\n);
      print qq($email_body_dis_dit);
      my $user    = 'new_objects.cgi';
#       my $email   = 'azurebrd@tazendra.caltech.edu';
#       my $email   = 'closertothewake@gmail.com';
      my $email   = 'ranjana@caltech.edu';
      my $subject = 'new_object.cgi values confirmed / rejected';
      &mail_simple($user, $email, $subject, $email_body_dis_dit);
    } # if ($email_body_dis_dit)
    foreach my $pgcommand (@pgcommands) {
      print qq($pgcommand<br/>\n);
# UNCOMMENT TO POPULATE
      my $result = $dbh->do( $pgcommand );
    } 
  } # if ($type eq 'Phenotype')
} # sub confirm

sub mail_simple {
  my ($user, $email, $subject, $body) = @_;
  my $command = 'sendmail';
  my $mailer = Mail::Mailer->new($command) ;
  $mailer->open({ From    => $user,
                  To      => $email,
                  Subject => $subject,
                  'MIME-Version' => '1.0',
                "Content-type" => 'text/html; charset=ISO-8859-1',
                })
      or die "Can't open: $!\n";
  print $mailer $body;
  $mailer->close();
} # sub mail_simple

sub printHtmlMenu {		# show main menu page
  print <<"  EndOfText";
  <FORM METHOD="POST" ACTION="new_objects.cgi">
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
  <TR><TD><B>OR</B></TD></TR>
  <TR>
    <TD COLSPAN=3><B>Update Strains : </B></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Update Strains !"></TD>
  <TR>
  EndOfText
  print "</TABLE>\n";
  print "</FROM>\n";
} # sub printHtmlMenu


sub queryVariation {
  my %hash; 
  print "<a href=\"new_objects.cgi\">return to query page</a><br/>\n";
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

sub commitStrains {
  my $email_body = '';
  my ($oop, $totalcount)         = &getHtmlVar($query, "count");
  foreach my $count (1 .. $totalcount) {
    ($oop, my $reject)            = &getHtmlVar($query, "reject_$count");
    ($oop, my $approve)           = &getHtmlVar($query, "approve_$count");
    ($oop, my $value)             = &getHtmlVar($query, "value_$count");
    if ($reject) {  $email_body .= qq(Rejected : $value<br/>\n); }
    if ($approve) { $email_body .= qq(Approved : $value<br/>\n); }
  }
  if ($email_body) {
    my $user    = 'new_objects.cgi';
#     my $email   = 'azurebrd@tazendra.caltech.edu';
    my $email   = 'ranjana@caltech.edu, maryann.tuli@wormbase.org';
    my $subject = 'new_object.cgi values confirmed / rejected';
    &mail_simple($user, $email, $subject, $email_body);
  } # if ($email_body)
#   $email_body =~ s/\n/<br\/>/g;
  print qq($email_body);
} # sub commitStrains

sub updateStrains {
  print qq(<br/>);
  print qq(Disease Term OA strains<br/>);
  my $count = 0;
  print qq(<FORM METHOD="POST" ACTION="new_objects.cgi">\n);
  print qq(<INPUT TYPE="submit" NAME="action" VALUE="Commit Strains"><br /><br />\n); 
  print qq(<table border="1">);
  print qq(<tr><th>pgid</th><th>suggested strain</th><th>timestammp</th><th>approve</th><th>reject</th></tr>);
  my $result = $dbh->prepare( "SELECT * FROM dit_suggested_strain ORDER BY dit_timestamp DESC" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    $count++;
    my $data_row = $row[1];
    my (@paps) = $data_row =~ m/WBPaper(\d+)/g;
    foreach my $pap (@paps) {
      my $pap_link = qq(<a href="paper_editor.cgi?curator_id=two2970&action=Search&data_number=$pap" target="_blank">WBPaper$pap</a>);
      $data_row =~ s/WBPaper$pap/$pap_link/g;
    } # foreach my $pap (@paps)
    print qq(<tr><td>$row[0]</td><td>$data_row</td><td>$row[2]</td>);
    print qq(<td><input type=checkbox name="approve_$count"></td>);
    print qq(<td><input type=checkbox name="reject_$count"></td>);
    print qq(<input type=hidden name="value_$count" value="$row[1]">);
    print qq(</tr>\n);
  }
  print qq(</table>);
  print qq(<br/>);
  print qq(Disease OA strains<br/>);
  print qq(<table border="1">);
  print qq(<tr><th>pgid</th><th>suggested strain</th><th>timestammp</th><th>approve</th><th>reject</th></tr>);
  my $result = $dbh->prepare( "SELECT * FROM dis_suggested_strain ORDER BY dis_timestamp DESC" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    $count++;
    print qq(<tr><td>$row[0]</td><td>$row[1]</td><td>$row[2]</td>);
    print qq(<td><input type=checkbox name="approve_$count"></td>);
    print qq(<td><input type=checkbox name="reject_$count"></td>);
    print qq(<input type=hidden name="value_$count" value="$row[1]">);
    print qq(</tr>\n);
  }
  print qq(</table>);
  print qq(<input type=hidden name="count" value="$count">);
  print qq(<br/>);
  print qq(<INPUT TYPE="submit" NAME="action" VALUE="Commit Strains"><br /><br />\n); 
  print qq(</FORM>\n);
} # sub updateStrains

sub updateFinalname {							# get list of $type data for curators to assign a final name
  my $type = shift;							# this should work for rnai, variation (allele), transgene 
  my %good;		# good alleles are in the list
  my %bad;		# bad alleles are alleles that have a tempname and are not good

  print "<FORM METHOD=\"POST\" ACTION=\"new_objects.cgi\">\n";
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm !\"><br /><br />\n"; 

  print qq(<a href="#oadata_rna">Jump to : RNAi-Phenotype data with Suggested Term and no WBPhenotype</a><br/>\n);
  print qq(<a href="#oadata_app">Jump to : Allele-Phenotype data with Suggested Term and no WBPhenotype</a><br/>\n);
  print qq(<a href="#oadata_dis">Jump to : Disease data with Suggested Term and no WBPhenotype</a><br/>\n);
  print qq(<a href="#oadata_dit">Jump to : Disease Term data with Suggested Term and no WBPhenotype</a><br/>\n);
  my @datatypes = qw( rna app dis dit );
  foreach my $datatype (@datatypes) {
    print qq(<a href="#prev_${datatype}_accepted">Jump to : previous data $datatype accepted</a><br/>\n);
    print qq(<a href="#prev_${datatype}_rejected">Jump to : previous data $datatype rejected</a><br/>\n); }
  print qq(<br/>);

  my $line_number = 0;
  if ($type eq 'Phenotype') {
    &populateCurators();
    &populatePhobo();
    my ($tableRna) = &getPhnOaData('rna');
    my ($tableApp) = &getPhnOaData('app');
    my ($tableDis) = &getPhnOaData('dis');
    my ($tableDit) = &getPhnOaData('dit');
    ($line_number) = &showOaTermNoWBPhenotype($line_number, 'dis');
    ($line_number) = &showOaTermNoWBPhenotype($line_number, 'dit');
    ($line_number) = &showOaTermNoWBPhenotype($line_number, 'rna');
    ($line_number) = &showOaTermNoWBPhenotype($line_number, 'app');
    print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm !\"><br /><br />\n"; 
    print $tableRna;
    print $tableApp;
    print $tableDis;
    print $tableDit;
  } # else # if $type eq Allele | Transgene

  print "</TABLE>\n";
  print "<INPUT TYPE=HIDDEN NAME=\"tempname_count\" VALUE=\"$line_number\">$line_number entries<BR>\n";
  print "<INPUT TYPE=HIDDEN NAME=\"type\" VALUE=\"$type\">\n";
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Confirm !\"><BR>\n"; 
  print "</FORM>\n";
} # sub updateFinalname

sub getPhnOaData {
  my ($datatype) = @_;
  my $table = '';
  $table .= qq(<div id="prev_${datatype}_accepted">Previous data $datatype accepted : </div>);
  $table .= qq(<TABLE BORDER="1" style="empty-cells: show">\n); 
  $table .= qq(<thead><tr><th>Confirm</th><th>Reject</th><th>Comment</th><th>Suggested</th><th>Suggested Definition</th><th>Placeholder</th><th>Child Of</th><th>Curator</th><th>Paper Evidence</th><th>Entity</th><th>Datatype</th><th>PGIDs</th><th>timestamp</th></tr></thead><tbody>\n);
  my $result = $dbh->prepare( "SELECT * FROM phn_oadata WHERE datatype = '$datatype' AND phenotype IS NOT NULL ORDER BY phn_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    my ($phenotype, $reject, $comment, $suggested, $definition, $child_of, $curator, $paper, $entity, $datatype, $pgids) = @row;
    $previouslySuggested{$suggested}++;
    my $row = join"</td><td>", @row;
    $table .= qq(<tr><td>$row</td></tr>\n);
  }
  $table .= "</tbody></table><br/><br/>";
  $table .= qq(<div id="prev_${datatype}_rejected">Previous data $datatype rejected : </div>);
  $table .= qq(<TABLE BORDER="1" style="empty-cells: show">\n); 
  $table .= qq(<thead><tr><th>Confirm</th><th>Reject</th><th>Comment</th><th>Suggested</th><th>Suggested Definition</th><th>Placeholder</th><th>Child Of</th><th>Curator</th><th>Paper Evidence</th><th>Entity</th><th>Datatype</th><th>PGIDs</th><th>timestamp</th></tr></thead><tbody>\n);
  my $result = $dbh->prepare( "SELECT * FROM phn_oadata WHERE datatype = '$datatype' AND reject IS NOT NULL ORDER BY phn_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    my ($phenotype, $reject, $comment, $suggested, $definition, $child_of, $curator, $paper, $entity, $datatype, $pgids) = @row;
    $previouslySuggested{$suggested}++;
    my $row = join"</td><td>", @row;
    $table .= qq(<tr><td>$row</td></tr>\n);
  }
  $table .= "</tbody></table><br/><br/>";
  return $table;
} # sub getPhnOaData

sub showOaTermNoWBPhenotype {
  my ($line_number, $datatype) = @_;
  &populateCurators();
  my $query = '';
  if ($datatype eq 'app') {
      print qq(<div id="oadata_app">Allele-Phenotype data with Suggested Term and no WBPhenotype : </div>\n<TABLE BORDER="1" style="empty-cells: show">\n); 
#       print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Placeholder</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Entity</TD><TD>Datatype</TD><TD>PGIDs</TD></TR>\n";
      print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Placeholder</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Datatype</TD><TD>PGIDs</TD></TR>\n";
      $query = qq(SELECT app_suggested.joinkey, app_suggested.app_suggested, app_suggested_definition.app_suggested_definition, app_suggested.app_timestamp FROM app_suggested, app_suggested_definition WHERE app_suggested.app_suggested != '' AND app_suggested.app_suggested IS NOT NULL AND app_suggested_definition.app_suggested_definition IS NOT NULL AND app_suggested.joinkey = app_suggested_definition.joinkey AND app_suggested.app_suggested !~ 'ACCEPTED' AND app_suggested.app_suggested !~ 'REJECTED' ORDER BY app_suggested.app_timestamp;); }
    elsif ($datatype eq 'rna') {
      print qq(<div id="oadata_rna">RNAi-Phenotype data with Suggested Term and no WBPhenotype : </div>\n<TABLE BORDER="1" style="empty-cells: show">\n); 
      print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Placeholder</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Datatype</TD><TD>PGIDs</TD></TR>\n";
      $query = qq(SELECT rna_suggested.joinkey, rna_suggested.rna_suggested, rna_suggested_definition.rna_suggested_definition, rna_suggested.rna_timestamp FROM rna_suggested, rna_suggested_definition WHERE rna_suggested.rna_suggested != '' AND rna_suggested.rna_suggested IS NOT NULL AND rna_suggested_definition.rna_suggested_definition IS NOT NULL AND rna_suggested.joinkey = rna_suggested_definition.joinkey AND rna_suggested.rna_suggested !~ 'ACCEPTED' AND rna_suggested.rna_suggested !~ 'REJECTED' ORDER BY rna_suggested.rna_timestamp;); }
    elsif ($datatype eq 'dis') {
      print qq(<div id="oadata_dis">Disease data with Suggested Term and no WBPhenotype : </div>\n<TABLE BORDER="1" style="empty-cells: show">\n); 
      print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Placeholder</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Datatype</TD><TD>PGIDs</TD></TR>\n";
      $query = qq(SELECT dis_suggested_phenotype.joinkey, dis_suggested_phenotype.dis_suggested_phenotype, dis_suggested_definition.dis_suggested_definition, dis_suggested_phenotype.dis_timestamp FROM dis_suggested_phenotype, dis_suggested_definition WHERE dis_suggested_phenotype.dis_suggested_phenotype != '' AND dis_suggested_phenotype.dis_suggested_phenotype IS NOT NULL AND dis_suggested_definition.dis_suggested_definition IS NOT NULL AND dis_suggested_phenotype.joinkey = dis_suggested_definition.joinkey AND dis_suggested_phenotype.dis_suggested_phenotype !~ 'ACCEPTED' AND dis_suggested_phenotype.dis_suggested_phenotype !~ 'REJECTED' ORDER BY dis_suggested_phenotype.dis_timestamp;); }
    elsif ($datatype eq 'dit') {
      print qq(<div id="oadata_dit">Disease Term data with Suggested Term and no WBPhenotype : </div>\n<TABLE BORDER="1" style="empty-cells: show">\n); 
      print "<TR><TD>Confirm</TD><TD>Reject</TD><TD>Comment</TD><TD>Suggested</TD><TD>Suggested Definition</TD><TD>Placeholder</TD><TD>Child Of</TD><TD>Curator</TD><TD>Paper Evidence</TD><TD>Datatype</TD><TD>PGIDs</TD></TR>\n";
      $query = qq(SELECT dit_suggested_phenotype.joinkey, dit_suggested_phenotype.dit_suggested_phenotype, dit_suggested_definition.dit_suggested_definition, dit_suggested_phenotype.dit_timestamp FROM dit_suggested_phenotype, dit_suggested_definition WHERE dit_suggested_phenotype.dit_suggested_phenotype != '' AND dit_suggested_phenotype.dit_suggested_phenotype IS NOT NULL AND dit_suggested_definition.dit_suggested_definition IS NOT NULL AND dit_suggested_phenotype.joinkey = dit_suggested_definition.joinkey AND dit_suggested_phenotype.dit_suggested_phenotype !~ 'ACCEPTED' AND dit_suggested_phenotype.dit_suggested_phenotype !~ 'REJECTED' ORDER BY dit_suggested_phenotype.dit_timestamp;); }
    else { return; }
# print qq(QUERY $query QUERY<br>);
  my %filter;
  my $result = $dbh->prepare( $query );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $filter{$row[1]}{def}{$row[2]}++; $filter{$row[1]}{pgids}{$row[0]}++; $filter{$row[1]}{timestamp}{$row[3]}++; }
#   foreach my $term (sort keys %filter) { # }			# sort by suggested name alphanumerically
  foreach my $term (sort { $filter{$a}{timestamp} <=> $filter{$b}{timestamp} } keys %filter) {		# sort by most recent timestamp for a given suggested term
#     next if ($phobo{$term}{def});
    $line_number++;
    print qq(<tr>);
    print qq(<INPUT TYPE="hidden" NAME="datatype_$line_number" VALUE="$datatype">);
    print qq(<TD VALIGN=TOP><INPUT NAME="phenotype_$line_number"></TD>\n);
    print qq(<TD VALIGN=TOP>$line_number<INPUT TYPE=checkbox NAME="reject_$line_number" VALUE="checked"></TD>\n);
    print qq(<TD VALIGN=TOP><TEXTAREA NAME="comment_$line_number" ROWS=5 COLS=40></TEXTAREA></TD>\n);
    my @defs; my @pgids;
    foreach my $def (keys %{ $filter{$term}{def} }) { push @defs, $def; }
    my $def = join", ", @defs; 
    foreach my $pgids (sort keys %{ $filter{$term}{pgids} }) { push @pgids, $pgids; }
    my $pgids = join"', '", @pgids; $pgids = "'$pgids'";
    next unless ($pgids); next unless ($def);
    my $exists = ''; 
    if ($phobo{$term}{name}) { $exists .= ' <FONT SIZE=-1>(' . $phobo{$term}{name} . ')</FONT>'; }
    if ($previouslySuggested{$term}) { $exists .= ' <FONT SIZE=-1>( already suggested )</FONT>'; }
#     print "<TR><TD VALIGN=top>$term <FONT SIZE=-1>($phobo{$term}{name})</FONT></TD><TD VALIGN=top>$def</TD>\n";
    print "<TD VALIGN=top>$term$exists</TD><TD VALIGN=top>$def</TD>\n";
    print qq(<INPUT TYPE="hidden" NAME="suggested_$line_number" VALUE="$term">);
    print qq(<INPUT TYPE="hidden" NAME="suggested_definition_$line_number" VALUE="$def">);
    my $placeholderTable = 'term'; 
    if ($datatype eq 'rna') {      $placeholderTable = 'phenotype'; }
      elsif ($datatype eq 'dis') { $placeholderTable = 'phenotypeaffected'; }
      elsif ($datatype eq 'dit') { $placeholderTable = 'phenotypeaffected'; }
    my $result2 = $dbh->prepare( "SELECT * FROM ${datatype}_${placeholderTable} WHERE joinkey IN ($pgids);" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; } 
    my %placeholder = (); foreach my $cur (sort keys %filter2) { if ($cur =~ m/(WBPhenotype:\d+)/) { $placeholder{$1}++; } }
    my @placeholder = sort keys %placeholder; my $placeholder = join", ", @placeholder;
    print qq(<INPUT TYPE="hidden" NAME="placeholder_$line_number" VALUE="$placeholder">);
    foreach my $placeholder (@placeholder) { $placeholder .= " <FONT SIZE=-1>($phobo{$placeholder}{name})</FONT>"; }
    $placeholder = join", ", @placeholder;
    print "<TD VALIGN=TOP>$placeholder</TD>";
    $result2 = $dbh->prepare( "SELECT * FROM ${datatype}_child_of WHERE joinkey IN ($pgids);" );
# print qq(<td>SELECT * FROM ${datatype}_child_of WHERE joinkey IN ($pgids);</td>);
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; } 
    my %child_of = (); foreach my $cur (sort keys %filter2) { if ($cur =~ m/(WBPhenotype:\d+)/) { $child_of{$1}++; } }
    my @child_of = sort keys %child_of; my $child_of = join", ", @child_of;
    print qq(<INPUT TYPE="hidden" NAME="child_of_$line_number" VALUE="$child_of">);
    foreach my $child_of (@child_of) { $child_of .= " <FONT SIZE=-1>($phobo{$child_of}{name})</FONT>"; }
    $child_of = join", ", @child_of;
    print "<TD VALIGN=TOP>$child_of</TD>";
    $result2 = $dbh->prepare( "SELECT * FROM ${datatype}_curator WHERE joinkey IN ($pgids);" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; } 
    my %curatorData = (); foreach my $cur (sort keys %filter2) { if ($cur =~ m/WBPerson(\d+)/) { $curatorData{"two$1"}++; } }
    my @curatorData = sort keys %curatorData;
    my @curatorNamed = map { $curator{joinkey_to_name}{$_} || $_ } @curatorData;
    my $curator = join", ", @curatorNamed;
    if ($curator eq 'two29819') {
      %filter2 = ();
      $result2 = $dbh->prepare( "SELECT * FROM ${datatype}_communitycurator WHERE joinkey IN ($pgids);" );
      $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; }
      my %curatorData = (); foreach my $cur (sort keys %filter2) { if ($cur =~ m/(WBPerson\d+)/) { $curatorData{$1}++; } }
      $curator = join", ", sort keys %curatorData; }
    print "<TD VALIGN=TOP>$curator</TD>";
    print qq(<INPUT TYPE="hidden" NAME="curator_$line_number" VALUE="$curator">);
    my $paper_table = "${datatype}_paper";
    if ($datatype eq 'dis') { $paper_table = 'dis_paperdisrel'; }
    $result2 = $dbh->prepare( "SELECT * FROM $paper_table WHERE joinkey IN ($pgids);" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; }
    my @paper = sort keys %filter2; my $paper = join", ", @paper; 
    print qq(<INPUT TYPE="hidden" NAME="paper_$line_number" VALUE="$paper">);
    print "<TD VALIGN=TOP>$paper</TD>";
#     my $entity = '';
#     if ($datatype eq 'app') {
#       $result2 = $dbh->prepare( "SELECT * FROM app_entity WHERE joinkey IN ($pgids);" );
#       $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       %filter2 = (); while (my @row2 = $result2->fetchrow) { next unless ($row2[1] =~ m/\S/) ; $filter2{$row2[1]}++; }
#       my @entity = sort keys %filter2; $entity = join", ", @entity;
#       print "<TD VALIGN=TOP>$entity</TD>"; }
#     print qq(<INPUT TYPE="hidden" NAME="entity_$line_number" VALUE="$entity">);
    print "<TD VALIGN=TOP>$datatype</TD>";
    print "<TD VALIGN=TOP>$pgids</TD>";
    print qq(<INPUT TYPE="hidden" NAME="datatype_$line_number" VALUE="$datatype">);
    print qq(<INPUT TYPE="hidden" NAME="pgids_$line_number" VALUE="$pgids">);
    print "</TR>\n";
  } # foreach my $term (sort keys %filter)
  print "</TABLE><BR><P><BR>\n";
  return $line_number;
} # sub showOaTermNoWBPhenotype

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

