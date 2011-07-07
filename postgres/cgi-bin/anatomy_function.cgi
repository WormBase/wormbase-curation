#!/usr/bin/perl

# Curate Anatomy Function data

# Working 2007 03 15
#
# Add a textarea for condition, and allow it to be a separate object.
# Format is :
# WBPaper00001254_1
# Genotype "unc-30(e191 ced-3(n717)"
# Reference WBPaper00001254
# Remark "Strain used for blah blah"
# Basically grab the first line for the object name, then attach the rest.  2007 03 22
#
# Just warn about wbbts since cshl cvs won't reflect new terms right away.
# for Raymond  2007 08 23
#
# Changed WBPhenotype to WBPhenotype: from name change in .obo  2008 06 24
#
# use local file updated by cronjob in case cshl is down 
# /home/acedb/cron/wbbt.obo	2008 10 28
#
# Converted from wpa to pap tables, even though they're not live yet.  2010 06 23
#
# Created  &readPhenOnt()  to get from CGI instead of deprecated  CVS.  2010 12 08 


use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate
use LWP::UserAgent;	# getting sanger files for querying
use LWP::Simple;	# get phenotype_ontology_obo.cgi
use Ace;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $query = new CGI;	# new CGI form

my %theHash;		# huge hash for each field with relevant values
my @PGparameters = qw( wbbtf assay phenotype gene involved notinvolved remark reference );


my %phenotypeTerms;	# phenotype name/number info
my %geneInfo;		# gin sequence/synonyms/locus info
my %anatInfo;		# cvs anatomy info data  name/name->number number/number->name
my %papId;		# pap identifier info
my @gene_evi = qw( Published_as );
my @rem_evi = qw( Curator_confirmed Person_evidence );
my @phen_anatfunc = qw( Autonomous Nonautonomous Remark );
my @inv_anatfunc = qw( Sufficient Necessary Remark );
my @not_anatfunc = qw( Insufficient Unnecessary Remark );
# my %evidence;		# the evidence hash tags
# my @anatfunc;		# the anatomy function info tags

my $action;

my $badData;		# flag if some data entered does not correspond to existing data

  &printHeader('Anatomy Function Curation Form');	# normal form view
  &initializeHash();	# Initialize theHash structure for html names and box sizes
  &process();		# do everything
  &printFooter(); 

sub process {
  (my $var, $action) = &getHtmlVar($query, 'action');
  unless ($action) { $action = ''; &printHtmlForm(); }

  print "ACTION : $action : ACTION<BR>\n"; 
  if ($action eq 'Preview !') { &preview(); } 				# check wbbtf exists, or assign a new one
  elsif ($action eq 'Add Assay !') { &addAssay(); } 			# rewrite form with another assay box
  elsif ($action eq 'Add Involved !') { &addInvolved(); } 		# rewrite form with another involved box
  elsif ($action eq 'Add Not Involved !') { &addNotInvolved(); }	# rewrite form with another not involved box
  elsif ($action eq 'Add Remark !') { &addRemark(); }			# rewrite form with another remark box
  elsif ($action eq 'Write !') { &write(); } 				# write data to postgres tables
  elsif ($action eq 'Query WBbtf !') { &queryPostgres(); }		# check wbbtf exists and query from postgres
  elsif ($action eq 'Dump All !') { &dumpAll(); } 			# query all data from postgres to hash and write .ace file
} # sub process

sub dumpAll {
  my $file = 'anat_func.ace';
  my $outfile = '/home/postgres/public_html/cgi-bin/data/' . $file;
  my $url = 'http://tazendra.caltech.edu/~postgres/cgi-bin/data/' . $file;
  print "Started dumping all .ace data to <A HREF=$url>$url</A>.<BR>";
  open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
  my $result = $dbh->prepare( "SELECT wbb_wbbtf FROM wbb_wbbtf ORDER BY wbb_wbbtf DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  my $max_val = '';
  if ($row[0]) { $max_val = $row[0]; } else { $max_val = 0; }
  for my $joinkey (1 .. $max_val) {
    %theHash = ();
    $joinkey = &padZeros($joinkey);
    &populateFromPg($joinkey);
    $theHash{wbbtf}{html_value} = $joinkey;
    my ($acefile) = &getAceFromHash();
    print OUT "$acefile\n\n";
  }
  close (OUT) or die "Cannot close $outfile : $!";
  print "Finished dumping<BR>\n";
} # sub dumpAll

sub queryPostgres {
  my $type = 'wbbtf';
  (my $var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
  my $joinkey = $theHash{$type}{html_value};
  if ($joinkey) {
      my $result = $dbh->prepare( "SELECT wbb_wbbtf FROM wbb_wbbtf WHERE joinkey = '$joinkey';");
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow; 
      if ($row[0]) { 
          &populateFromPg($joinkey);
          &printHtmlForm(); }
        else { 
          print "$joinkey was not found in postgres, please enter an existing WBbtf value.<BR>\n"; 
          &printHtmlForm(); } }
    else {
      print "No WBbtf value, please enter an existing WBbtf value.<BR>\n"; 
      &printHtmlForm(); }
} # sub queryPostgres
  
sub populateFromPg {
  my $joinkey = shift;

  my $type = 'assay';
  my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_order DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1];
  for my $i (1 .. $theHash{$type}{html_value}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row = $result->fetchrow;
    my $g_type = $type . '_' . $i;
    $theHash{$g_type}{html_value} = $row[2]; 
    my $g_type2 = 'cond_' . $i;
    $theHash{$g_type2}{html_value} = $row[3]; }

  my @anats = @phen_anatfunc; push @anats, 'none';
  $type = 'phenotype';
  $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1]; 
  foreach my $anat (@anats) {
    $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$anat' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row = $result->fetchrow;
    if ($row[3]) {
      if ($row[3] eq 'CHECKED') {
          my $g_type_one = $type . '_' . $anat . '_check';
          $theHash{$g_type_one}{html_value} = 'CHECKED'; }
        else { 
          my $g_type_two = $type . '_' . $anat;
          $theHash{$g_type_two}{html_value} = $row[3]; } } }

  my @evi = @gene_evi; push @evi, 'none';
  $type = 'gene';
  $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1]; 
  foreach my $evi (@evi) {
    $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$evi' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row = $result->fetchrow;
    if ($row[3]) {
      my $g_type_two = $type . '_' . $evi;
      $theHash{$g_type_two}{html_value} = $row[3]; } }


  my (@same_types) = qw( involved notinvolved );
  foreach my $type (@same_types) {
  if ($type eq 'involved') { @anats = @inv_anatfunc; push @anats, 'none'; }
    else { @anats = @not_anatfunc; push @anats, 'none'; }
  my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_order DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1];
  for my $i (1 .. $theHash{$type}{html_value}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row = $result->fetchrow;
    my $g_type = $type . '_' . $i;
    $theHash{$g_type}{html_value} = $row[2]; 
    foreach my $anat (@anats) {
      $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$anat' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      @row = $result->fetchrow;
      if ($row[4]) {
        if ($row[4] eq 'CHECKED') {
            my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
            $theHash{$g_type_one}{html_value} = 'CHECKED'; }
          else { 
            my $g_type_two = $type . '_' . $anat . '_' . $i;
            $theHash{$g_type_two}{html_value} = $row[4]; } } } } }

  @evi = @rem_evi; push @evi, 'none';
  $type = 'remark';
  my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_order DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1];
  for my $i (1 .. $theHash{$type}{html_value}) {
    $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    @row = $result->fetchrow;
    my $g_type = $type . '_' . $i;
    $theHash{$g_type}{html_value} = $row[2]; 
    foreach my $evi (@evi) {
      my $g_type2 = $type . '_' . $evi . '_' . $i;
      my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$evi' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      $theHash{$g_type2}{html_value} = $row[4]; } }

  $type = 'reference';
  my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1];
} # sub queryPostgres

sub write {
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  print "WRITE<BR>\n";

  my $type = 'wbbtf';
  my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  my $pg_val = ''; if ($row[1]) { $pg_val = $row[1]; }
  my $val = $theHash{$type}{html_value}; if ($val =~ m/^0+/) { $val =~ s/^0+//g; }
  if ($val ne $pg_val) { 
    $val = "'$val'";
    my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', $val, CURRENT_TIMESTAMP)";
    my $result2 = $dbh->do( $command );
    print "<FONT COLOR='green'>$command</FONT><BR>\n"; }

  $type = 'assay';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    my $val1 = $theHash{$g_type}{html_value};
    my $g_type2 = 'cond_' . $i;
    my $val2 = $theHash{$g_type2}{html_value};
    my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    my $pg_val1 = ''; if ($row[2]) { $pg_val1 = $row[2]; }
    my $pg_val2 = ''; if ($row[3]) { $pg_val2 = $row[3]; }
    if ( ($val1 ne $pg_val1) || ($val2 ne $pg_val2) ) { 
      if ($val1) { $val1 = "'$val1'"; } else { $val1 = 'NULL'; }
      if ($val2) { $val2 = "'$val2'"; } else { $val2 = 'NULL'; }
      my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', '$i', $val1, $val2, CURRENT_TIMESTAMP)";
      my $result2 = $dbh->do( $command );
      print "<FONT COLOR='green'>$command</FONT><BR>\n"; }
  } # for my $i (0 .. $theHash{$type}{html_value})

  my @anats = @phen_anatfunc; push @anats, 'none';
  $type = 'phenotype';
  my $val = $theHash{$type}{html_value}; 
  foreach my $anat (@anats) {
    my $g_type_two = $type . '_' . $anat;
    my $g_type_one = $type . '_' . $anat . '_check';
    my $evi_val = '';
    if ($theHash{$g_type_two}{html_value}) { $evi_val = $theHash{$g_type_two}{html_value}; }
      elsif ($theHash{$g_type_one}{html_value}) { $evi_val = 'CHECKED'; }
    my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$anat' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    my $pg_val = ''; if ($row[1]) { $pg_val = $row[1]; }
    my $pg_evi_val = ''; if ($row[3]) { $pg_evi_val = $row[3]; }
    if ( ($theHash{$type}{html_value} ne $pg_val) || ($evi_val ne $pg_evi_val) ) { 
# print "V $val P $pg_val E<BR>\n";
# print "EV $evi_val P $pg_evi_val E<BR>\n";
      if ($val) { $val = "'$theHash{$type}{html_value}'"; } else { $val = 'NULL'; }
      if ($evi_val) { $evi_val = "'$evi_val'"; } else { $evi_val = 'NULL'; }
      my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', $val, '$anat', $evi_val, CURRENT_TIMESTAMP)";
      my $result2 = $dbh->do( $command );
      print "<FONT COLOR='green'>$command</FONT><BR>\n"; } }

  my @evi = @gene_evi; push @evi, 'none';
  $type = 'gene';
  my $val = $theHash{$type}{html_value}; 
  foreach my $evi (@evi) {
    my $g_type_two = $type . '_' . $evi;
    my $evi_val = '';
    if ($theHash{$g_type_two}{html_value}) { $evi_val = $theHash{$g_type_two}{html_value}; }
    my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$evi' ORDER BY wbb_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    my $pg_val = ''; if ($row[1]) { $pg_val = $row[1]; }
    my $pg_evi_val = ''; if ($row[3]) { $pg_evi_val = $row[3]; }
    if ( ($theHash{$type}{html_value} ne $pg_val) || ($evi_val ne $pg_evi_val) ) { 
      if ($val) { $val = "'$theHash{$type}{html_value}'"; } else { $val = 'NULL'; }
      if ($evi_val) { $evi_val = "'$evi_val'"; } else { $evi_val = 'NULL'; }
      my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', $val, '$evi', $evi_val, CURRENT_TIMESTAMP)";
      my $result2 = $dbh->do( $command );
      print "<FONT COLOR='green'>$command</FONT><BR>\n"; } }

  my (@same_types) = qw( involved notinvolved );
  foreach my $type (@same_types) {
  if ($type eq 'involved') { @anats = @inv_anatfunc; push @anats, 'none'; }
    else { @anats = @not_anatfunc; push @anats, 'none'; }
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    my $val = $theHash{$g_type}{html_value}; 
    foreach my $anat (@anats) {
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      my $evi_val = '';
      if ($theHash{$g_type_two}{html_value}) { $evi_val = $theHash{$g_type_two}{html_value}; }
        elsif ($theHash{$g_type_one}{html_value}) { $evi_val = 'CHECKED'; }
      my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$anat' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow;
      my $pg_val = ''; if ($row[2]) { $pg_val = $row[2]; }
      my $pg_evi_val = ''; if ($row[4]) { $pg_evi_val = $row[4]; }
      if ( ($theHash{$g_type}{html_value} ne $pg_val) || ($evi_val ne $pg_evi_val) ) { 
        if ($val) { $val = "'$theHash{$g_type}{html_value}'"; } else { $val = 'NULL'; }
        if ($evi_val) { $evi_val = "'$evi_val'"; } else { $evi_val = 'NULL'; }
        my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', '$i', $val, '$anat', $evi_val, CURRENT_TIMESTAMP)";
        my $result2 = $dbh->do( $command );
        print "<FONT COLOR='green'>$command</FONT><BR>\n"; } } } }

  @evi = @rem_evi; push @evi, 'none';
  $type = 'remark';
  my $val = $theHash{$type}{html_value}; 
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    my $val = $theHash{$g_type}{html_value}; 
    foreach my $evi (@evi) {
      my $g_type2 = $type . '_' . $evi . '_' . $i;
      my $evi_val = '';
      if ($theHash{$g_type2}{html_value}) { $evi_val = $theHash{$g_type2}{html_value}; }
      my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' AND wbb_evitype = '$evi' AND wbb_order = '$i' ORDER BY wbb_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow;
      my $pg_val = ''; if ($row[2]) { $pg_val = $row[2]; }
      my $pg_evi_val = ''; if ($row[4]) { $pg_evi_val = $row[4]; }
      if ( ($theHash{$g_type}{html_value} ne $pg_val) || ($evi_val ne $pg_evi_val) ) { 
        if ($val) { $val = "'$theHash{$g_type}{html_value}'"; } else { $val = 'NULL'; }
        if ($evi_val) { $evi_val = "'$evi_val'"; } else { $evi_val = 'NULL'; }
        my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', '$i', $val, '$evi', $evi_val, CURRENT_TIMESTAMP)";
        my $result2 = $dbh->do( $command );
        print "<FONT COLOR='green'>$command</FONT><BR>\n"; } } }

  $type = 'reference';
  my $val = $theHash{$type}{html_value}; 
  my $result = $dbh->prepare( "SELECT * FROM wbb_$type WHERE joinkey = '$joinkey' ORDER BY wbb_timestamp DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  my $pg_val = ''; if ($row[1]) { $pg_val = $row[1]; }
  my $val = $theHash{$type}{html_value}; 
  if ($val ne $pg_val) {
    $val = "'$val'";
    my $command = "INSERT INTO wbb_$type VALUES ('$joinkey', $val, CURRENT_TIMESTAMP)";
    my $result2 = $dbh->do( $command );
    print "<FONT COLOR='green'>$command</FONT><BR>\n"; }

  print "Done writing to postgres.<BR>\n";
} # sub write

sub preview {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/anatomy_function.cgi\">\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  my $joinkey = &getJoinkey($joinkey); 
  foreach my $key (sort keys %theHash) {
    my $val = $theHash{$key}{html_value};
#     print "K $key V <FONT COLOR='green'>$val</FONT> E<BR>\n";
  }

  my $type = 'assay';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
    my $g_type2 = 'cond_' . $i;
    if ($theHash{$g_type2}{html_value} =~ m/\"/) { $theHash{$g_type2}{html_value} =~ s/\"/&quot;/g; }	# need to allow doublequotes  2007 03 22
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\">\n";
  } # for my $i (0 .. $theHash{$type}{html_value})

  $type = 'phenotype';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  foreach my $anat (@phen_anatfunc) {
    my $g_type_two = $type . '_' . $anat;
    my $g_type_one = $type . '_' . $anat . '_check';
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type_one\" VALUE=\"$theHash{$g_type_one}{html_value}\">\n";
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type_two\" VALUE=\"$theHash{$g_type_two}{html_value}\">\n"; }

  $type = 'gene';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  foreach my $evi (@gene_evi) {
    my $g_type = $type . '_' . $evi;
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n"; }

  $type = 'involved';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
    foreach my $anat (@inv_anatfunc) {
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type_one\" VALUE=\"$theHash{$g_type_one}{html_value}\">\n";
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type_two\" VALUE=\"$theHash{$g_type_two}{html_value}\">\n"; }
  } # for my $i (0 .. $theHash{$type}{html_value})

  $type = 'notinvolved';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
    foreach my $anat (@not_anatfunc) {
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type_one\" VALUE=\"$theHash{$g_type_one}{html_value}\">\n";
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type_two\" VALUE=\"$theHash{$g_type_two}{html_value}\">\n"; }
  } # for my $i (0 .. $theHash{$type}{html_value})

  $type = 'remark';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
    foreach my $evi (@rem_evi) {
      my $g_type2 = $type . '_' . $evi . '_' . $i;
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\">\n"; }
  } # for my $i (0 .. $theHash{$type}{html_value})

  my $type = 'reference';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
 
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Write !\">\n";
  print "</FORM>\n";

  my ($acefile) = &getAceFromHash();
  if ($acefile =~ m/\n/) { $acefile =~ s/\n/<BR>\n/g; }
  print ".ace preview : <BR><FONT COLOR='green'>$acefile</FONT><BR>\n";
} # sub preview

sub getAceFromHash {		# create and return a .ace file based on data in %theHash
  my $acefile = '';
  my $obj_name = "WBbtf$theHash{wbbtf}{html_value}";
  $acefile .= "Anatomy_function : \"$obj_name\"\n";

  my $other_acefile = '';

  my $type = 'assay';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) { 
      my $g_type2 = 'cond_' . $i;
      if ($theHash{$g_type2}{html_value}) { 	# parse condition into a separate object  2007 03 22
#           $acefile .= "Assay\t\"$theHash{$g_type}{html_value}\"\tAnatomy_function\t\"$theHash{$g_type2}{html_value}\"\n";
          my $condition = $theHash{$g_type2}{html_value};
          my ($cond_obj) = $condition =~ m/^(.*?)\s*\n/;
          $other_acefile .= "Condition : $condition\n\n";
          $acefile .= "Assay\t\"$theHash{$g_type}{html_value}\"\t\"$cond_obj\"\n"; }
        else { $acefile .= "Assay\t\"$theHash{$g_type}{html_value}\"\n"; } } }

  $type = 'phenotype';
  if ($theHash{$type}{html_value}) {
    my $phenotype = $theHash{$type}{html_value};
    ($phenotype) = $phenotype =~ m/(WBPhenotype:\d+)/;
    my $has_data = 0;
    foreach my $anat (@phen_anatfunc) {
      my $g_type_two = $type . '_' . $anat;
      my $g_type_one = $type . '_' . $anat . '_check';
      if ($theHash{$g_type_two}{html_value}) { 
          my (@lines) = split/\n/, $theHash{$g_type_two}{html_value};
          foreach my $line (@lines) {
            if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
            $acefile .= "Phenotype\t\"$phenotype\"\t$anat\t\"$line\"\n"; $has_data++; } }
        elsif ($theHash{$g_type_one}{html_value}) { $acefile .= "Phenotype\t\"$phenotype\"\t$anat\n"; $has_data++; } }
    unless ($has_data) { $acefile .= "Phenotype\t\"$phenotype\"\n"; } }

  $type = 'gene';
  if ($theHash{$type}{html_value}) {
    my $gene = $theHash{$type}{html_value}; 
    ($gene) = $gene =~ m/(WBGene\d+)/;
    my $has_data = 0;
    foreach my $evi (@gene_evi) {
      my $g_type_two = $type . '_' . $evi;
      if ($theHash{$g_type_two}{html_value}) { 
        my (@lines) = split/\n/, $theHash{$g_type_two}{html_value};
        foreach my $line (@lines) {
          if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
          $acefile .= "Gene\t\"$gene\"\t$evi\t\"$line\"\n"; $has_data++; } } }
    unless ($has_data) { $acefile .= "Gene\t\"$gene\"\n"; } }

  my (@same_types) = qw( involved notinvolved );
  foreach my $type (@same_types) {
    my $tag = ucfirst($type);
    if ($tag eq 'Notinvolved') { $tag = 'Not_involved'; }
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $g_type = $type . '_' . $i;
      if ($theHash{$g_type}{html_value}) {
        my $val = $theHash{$g_type}{html_value}; 
        ($val) = $val =~ m/^(WBbt:\d+)/;
        my $has_data = 0;
        my @anats = @inv_anatfunc; if ($type eq 'notinvolved') { @anats = @not_anatfunc; }
        foreach my $anat (@anats) {
          my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
          my $g_type_two = $type . '_' . $anat . '_' . $i;
          if ($theHash{$g_type_two}{html_value}) { 
              my (@lines) = split/\n/, $theHash{$g_type_two}{html_value};
              foreach my $line (@lines) {
                if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
                $acefile .= "$tag\t\"$val\"\t$anat\t\"$line\"\n"; $has_data++; } }
            elsif ($theHash{$g_type_one}{html_value}) { $acefile .= "$tag\t\"$val\"\t$anat\n"; $has_data++; } }
        unless ($has_data) { $acefile .= "$tag\t\"$val\"\n"; } } } }

  $type = 'remark';
  my $val = $theHash{$type}{html_value}; 
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      my $remark = $theHash{$g_type}{html_value}; 
      my $has_data = 0;
      foreach my $evi (@rem_evi) {
        my $g_type2 = $type . '_' . $evi . '_' . $i;
        if ($theHash{$g_type2}{html_value}) { 
          my (@lines) = split/\n/, $theHash{$g_type2}{html_value};
          foreach my $line (@lines) {
            if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
            $acefile .= "Remark\t\"$remark\"\t$evi\t\"$line\"\n"; $has_data++; } } }
      unless ($has_data) { $acefile .= "Remark\t\"$remark\"\n"; } } }

  $type = 'reference';
  if ($theHash{$type}{html_value}) {
    my $ref = $theHash{$type}{html_value};
    ($ref) = $ref =~ m/^(WBPaper\d+)/;
    $acefile .= "Reference\t\"$ref\"\n"; }

  if ($other_acefile) { $acefile .= "\n$other_acefile"; } 
    
  return $acefile;
} # sub getAceFromHash

sub getJoinkey {
  my $joinkey = shift;
  if ($joinkey eq 'no joinkey') {
      $joinkey = &getNewJoinkey();
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_wbbtf\" VALUE=\"$joinkey\">\n";
      print "No WBbtf value, next highest value, $joinkey, chosen.<BR>\n"; }
    else {
      my $result = $dbh->prepare( "SELECT wbb_wbbtf FROM wbb_wbbtf WHERE joinkey = '$joinkey';");
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow; 
      if ($row[0]) { 
          print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_wbbtf\" VALUE=\"$joinkey\">\n";
          print "WBbtf value $joinkey already in postgres, <FONT COLOR='red'>will overwrite</FONT>.<BR>\n"; }
        else { 
          my $old_joinkey = $joinkey;
          $joinkey = &getNewJoinkey();
          print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_wbbtf\" VALUE=\"$joinkey\">\n";
          print "WBbtf value $old_joinkey does not exist ;  next highest value, $joinkey, chosen.<BR>\n"; } }
  $theHash{wbbtf}{html_value} = $joinkey;
  return $joinkey;
} # sub getJoinkey

sub getNewJoinkey {
  my $result = $dbh->prepare( "SELECT wbb_wbbtf FROM wbb_wbbtf ORDER BY wbb_wbbtf DESC;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my @row = $result->fetchrow;
  my $joinkey = '';
  if ($row[0]) { $joinkey = $row[0]; } else { $joinkey = 0; }
  $joinkey++;
  $joinkey = &padZeros($joinkey);
  return $joinkey;
} # sub getNewJoinkey

sub padZeros {
  my $joinkey = shift;
  if ($joinkey =~ m/^0+/) { $joinkey =~ s/^0+//g; }
  if ($joinkey < 10) { $joinkey = '000' . $joinkey; }
  elsif ($joinkey < 100) { $joinkey = '00' . $joinkey; }
  elsif ($joinkey < 1000) { $joinkey = '0' . $joinkey; }
  return $joinkey; 
} # sub padZeros


sub addNotInvolved {
  print "ADD Not Involved <BR>\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  $theHash{notinvolved}{html_value}++; 
  &printHtmlForm();
} # sub addInvolved

sub addInvolved {
  print "ADD Involved <BR>\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  $theHash{involved}{html_value}++; 
  &printHtmlForm();
} # sub addInvolved

sub addRemark {
  print "ADD Remark <BR>\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  $theHash{remark}{html_value}++; 
  &printHtmlForm();
} # sub addInvolved

sub addAssay {
  print "ADD Assay <BR>\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  $theHash{assay}{html_value}++; 
  &printHtmlForm();
} # sub addMult

sub getHtmlValuesFromForm {	# read PGparameters value from html form, then display to html
  &getGeneInfo();		# populate %geneInfo
  &getAnatInfo();		# populate %anatInfo
#   &readCvs(); 			# populate %phenotypeTerms
  &readPhenOnt(); 			# populate %phenotypeTerms
  &getWpaIdentifier();		# populate %papId

  my $type = 'wbbtf';
  (my $var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");

  $type = 'assay';
  ($var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    ($var, $theHash{$g_type}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type");
    my $g_type2 = 'cond_' . $i;
    ($var, $theHash{$g_type2}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type2");
  } # for my $i (0 .. $theHash{$type}{html_value})

  $type = 'phenotype';
  ($var, my $val) = &getHtmlVar($query, "html_value_main_$type");
  if ($val) {
      if ($val =~ m/WBPhenotype:\d+ \(.*?\)/)  { 1; }	# is in proper format to begin with
        elsif ($phenotypeTerms{term}{$val}) { $val = "$phenotypeTerms{term}{$val} ($val)"; } 	# it's a name, put in proper format
        elsif ( ($val =~ m/WBPhenotype:(\d+)/) || ($val =~ m/^(\d+)$/) ) { 	# it's a number, put in proper format
          my $phenkey = "WBPhenotype:$1";
          if ($phenotypeTerms{number}{$phenkey}) { $val = "$phenkey ($phenotypeTerms{number}{$phenkey})"; }
          else { print "<FONT COLOR='red'>ERROR $val is not a valid WBPhenotype</FONT><BR>\n"; $badData++; } }
        else { print "<FONT COLOR='red'>ERROR $val is not a valid WBPhenotype</FONT><BR>\n"; $badData++; }
      $theHash{$type}{html_value} = $val; }
    else { $theHash{$type}{html_value} = ''; }
  foreach my $anat (@phen_anatfunc) {
    my $g_type_two = $type . '_' . $anat;
    my $g_type_one = $type . '_' . $anat . '_check';
    ($var, $theHash{$g_type_one}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type_one");
    ($var, $theHash{$g_type_two}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type_two"); }

  $type = 'gene';
  ($var, $val) = &getHtmlVar($query, "html_value_main_$type");
  if ($val) {
      if ($geneInfo{back}{$val}) {  					# it's a locus or synonym, put all possible values in comma-separated format
          my $genekey = $geneInfo{back}{$val};
          my @vals = keys %{ $geneInfo{gene}{$genekey} }; my $vals = join", ", @vals;
          $val = "WBGene$genekey ($vals)"; }
        elsif ( ($val =~ m/WBGene(\d+)/) || ($val =~ m/^(\d+)$/) ) { 	# it's a number, put in proper format
          my $genekey = $1;
          if ($geneInfo{gene}{$genekey}) { 
            my @vals = keys %{ $geneInfo{gene}{$genekey} }; my $vals = join", ", @vals;
            $val = "WBGene$genekey ($vals)"; }
          else { print "<FONT COLOR='red'>ERROR $val is not a valid WBGene</FONT><BR>\n"; $badData++; } }
        else { print "<FONT COLOR='red'>ERROR $val is not a valid WBGene</FONT><BR>\n"; $badData++; }
      $theHash{$type}{html_value} = $val; }
    else { $theHash{$type}{html_value} = ''; }
  foreach my $evi (@gene_evi) {
    my $g_type = $type . '_' . $evi;
    ($var, $theHash{$g_type}{html_value}) = &getHtmlVar($query, "html_value_main_$g_type"); }

  $type = 'involved';
  ($var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    ($var, $val) = &getHtmlVar($query, "html_value_main_$g_type");
    if ($val) {
        if ($val =~ m/WBbt:\d+ \(.*?\)/) { 1; }	# is in proper format to begin with
          elsif ($anatInfo{name}{$val}) { $val = "WBbt:$anatInfo{name}{$val} ($val)"; } 	# it's a name, put in proper format
          elsif ( ($val =~ m/WBbt:(\d+)/) || ($val =~ m/^(\d+)$/) ) { 	# it's a number, put in proper format
            my $anatkey = $1;
            $val = "WBbt:$anatkey ($anatInfo{number}{$anatkey})"; 
            unless ($anatInfo{number}{$anatkey}) { print "<FONT COLOR='red'>WARNING $val is not a valid WBbt</FONT><BR>\n"; } }	 # just warn since cshl cvs won't reflect new terms right away 2007 08 23
          else { print "<FONT COLOR='red'>WARNING $val is not a valid WBbt</FONT><BR>\n"; }
        $theHash{$g_type}{html_value} = $val; }
      else { $theHash{$g_type}{html_value} = ''; }
    foreach my $anat (@inv_anatfunc) {
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      ($var, $theHash{$g_type_one}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type_one"); 
      ($var, $theHash{$g_type_two}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type_two"); }
  } # for my $i (0 .. $theHash{$type}{html_value})

  $type = 'notinvolved';
  ($var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    ($var, $val) = &getHtmlVar($query, "html_value_main_$g_type");
    if ($val) {
        if ($val =~ m/WBbt:\d+ \(.*?\)/) { 1; }	# is in proper format to begin with
          elsif ($anatInfo{name}{$val}) { $val = "WBbt:$anatInfo{name}{$val} ($val)"; } 	# it's a name, put in proper format
          elsif ( ($val =~ m/WBbt:(\d+)/) || ($val =~ m/^(\d+)$/) ) { 	# it's a number, put in proper format
            my $anatkey = $1;
            $val = "WBbt:$anatkey ($anatInfo{number}{$anatkey})";
            unless ($anatInfo{number}{$anatkey}) { print "<FONT COLOR='red'>WARNING $val is not a valid WBbt</FONT><BR>\n"; } }	# just warn since cshl cvs won't reflect new terms right away 2007 08 23
          else { print "<FONT COLOR='red'>WARNING $val is not a valid WBbt</FONT><BR>\n"; }
        $theHash{$g_type}{html_value} = $val; }
      else { $theHash{$g_type}{html_value} = ''; }
    foreach my $anat (@not_anatfunc) {
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      ($var, $theHash{$g_type_one}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type_one");
      ($var, $theHash{$g_type_two}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type_two"); }
  } # for my $i (0 .. $theHash{$type}{html_value})

  $type = 'remark';
  ($var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    ($var, $theHash{$g_type}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type");
    foreach my $evi (@rem_evi) {
      my $g_type2 = $type . '_' . $evi . '_' . $i;
      ($var, $theHash{$g_type2}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type2"); }
  } # for my $i (0 .. $theHash{$type}{html_value})

  my $type = 'reference';
  ($var, $val) = &getHtmlVar($query, "html_value_main_$type");
  if ($val) {
      if ($val =~ m/WBPaper\d+/) { 1; }		# in proper format
        elsif ($val =~ m/^(\d+)$/) { $val = "WBPaper$1"; }		# add WBPaper if just number
        elsif ( $papId{$val} ) { $val = 'WBPaper' . $papId{$val}; }	# convert identifer to pap
        else { print "<FONT COLOR='red'>ERROR $val is not a valid WBPaper</FONT><BR>\n"; $badData++; }
      $theHash{$type}{html_value} = $val; }
    else { $theHash{$type}{html_value} = ''; }
  
  my $joinkey = 'no joinkey';
  if ($theHash{wbbtf}{html_value}) { $joinkey = $theHash{wbbtf}{html_value}; }
  return $joinkey;
} # sub getHtmlValuesFromForm 


#################  HTML SECTION #################

sub printHtmlAssay {
  my @ao_code = qw( Blastomere_isolation Expression_mosaic Genetic_ablation Genetic_mosaic Laser_ablation );
  my $type = 'assay';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . "_" . $i;
#     print "    <TD ALIGN=left><FONT SIZE-=2 COLOR=green>$type</FONT><BR><SELECT NAME=\"html_value_main_$g_type\" SIZE=1>\n";
    print "    <TD ALIGN=left><SELECT NAME=\"html_value_main_$g_type\" SIZE=1>\n";
    if ($theHash{$g_type}{html_value}) { 
      if ($theHash{$g_type}{html_value} =~ m/\"/) { $theHash{$g_type}{html_value} =~ s/\"/&quot;/g; } 
      print "      <OPTION selected>$theHash{$g_type}{html_value}</OPTION>\n"; }
    print "      <OPTION > </OPTION>\n";
      # if loaded or queried, show option, otherwise default to '' option
    foreach (@ao_code) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n ";
    my $g_type2 = 'cond_' . $i;
    print "<TD align=right>Condition</TD><TD><TEXTAREA NAME=\"html_value_main_$g_type2\" COLS=40 ROWS=3>$theHash{$g_type2}{html_value}</TEXTAREA></TD></TR>\n";
#     print "<TD align=right>Condition</TD><TD><INPUT NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\"></TD></TR>\n";
  } # for my $1 (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add Assay !\"></TD></TR>\n";
} # sub printHtmlAssay

sub printHtmlPhenotype {
  my $type = 'phenotype';
  print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} :</STRONG></TD>";
  print "<TD><INPUT NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\"  SIZE=$theHash{$type}{html_size_main}></TD>\n";
  foreach my $anat (@phen_anatfunc) {
    my $checked = '';
    my $g_type_two = $type . '_' . $anat;
    my $g_type_one = $type . '_' . $anat . '_check';
    if ($theHash{$g_type_one}{html_value}) { $checked = 'CHECKED'; }
    print "<TR><TD align=right><FONT SIZE-=2 COLOR=green>$anat</FONT><INPUT NAME=\"html_value_main_$g_type_one\" TYPE=\"checkbox\" $checked $theHash{$g_type_one}{html_value} VALUE=\"checked\"</TD><TD colspan=6><TEXTAREA NAME=\"html_value_main_$g_type_two\" COLS=80 ROWS=$theHash{$type}{html_size_minor}>$theHash{$g_type_two}{html_value}</TEXTAREA></TD></TR>\n";
  } # foreach my $anat (@phen_anatfunc)
} # sub printHtmlPhenotype

sub printHtmlGene {
  my $type = 'gene';
  print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} :</STRONG></TD>";
  print "<TD><INPUT NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n";
  my @gene_evi = qw( Published_as );
  foreach my $evi (@gene_evi) {
    my $g_type = $type . '_' . $evi;
    print "<TD><FONT SIZE-=2 COLOR=green>$evi</FONT><BR><TEXTAREA NAME=\"html_value_main_$g_type\" SIZE=$theHash{$type}{html_size_main}>$theHash{$g_type}{html_value}</TEXTAREA></TD>\n";
  } # foreach my $evi (@gene_evi)
  print "  </TR>\n";
} # sub printHtmlPhenotype

sub printHtmlInvolved {
  my $type = 'involved';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . '_' . $i;
    print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\"  SIZE=$theHash{$type}{html_size_main}></TD></TR>\n";
    foreach my $anat (@inv_anatfunc) {
      my $checked = '';
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      print "<TR><TD align=right><FONT SIZE-=2 COLOR=green>$anat</FONT><INPUT NAME=\"html_value_main_$g_type_one\" TYPE=\"checkbox\" $checked $theHash{$g_type_one}{html_value} VALUE=\"checked\"></TD><TD colspan=6><TEXTAREA NAME=\"html_value_main_$g_type_two\" COLS=80 ROWS=$theHash{$type}{html_size_minor}>$theHash{$g_type_two}{html_value}</TEXTAREA></TD></TR>\n";
    } # foreach my $anat (@inv_anatfunc)
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add Involved !\"></TD></TR>\n";
} # sub printHtmlInvolved

sub printHtmlNotInvolved {
  my $type = 'notinvolved';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . '_' . $i;
    print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\"  SIZE=$theHash{$type}{html_size_main}></TD></TR>\n";
    foreach my $anat (@not_anatfunc) {
      my $checked = '';
      my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
      my $g_type_two = $type . '_' . $anat . '_' . $i;
      print "<TR><TD align=right><FONT SIZE-=2 COLOR=green>$anat</FONT><INPUT NAME=\"html_value_main_$g_type_one\" TYPE=\"checkbox\" $checked $theHash{$g_type_one}{html_value} VALUE=\"checked\"></TD><TD colspan=6><TEXTAREA NAME=\"html_value_main_$g_type_two\" COLS=80 ROWS=$theHash{$type}{html_size_minor}>$theHash{$g_type_two}{html_value}</TEXTAREA></TD></TR>\n";
    } # foreach my $anat (@not_anatfunc)
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add Not Involved !\"></TD></TR>\n";
} # sub printHtmlNotInvolved

sub printHtmlRemark {
  my $type = 'remark';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . '_' . $i;
    print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n";
    my @rem_evi = qw( Curator_confirmed Person_evidence );
    foreach my $evi (@rem_evi) {
      my $g_type2 = $type . '_' . $evi . '_' . $i;
      print "<TD><FONT SIZE-=2 COLOR=green>$evi</FONT><BR><TEXTAREA NAME=\"html_value_main_$g_type2\" >$theHash{$g_type2}{html_value}</TEXTAREA></TD>\n";
    } # foreach my $evi (@rem_evi)
    print "</TR>\n";
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add Remark !\"></TD></TR>\n";
} # sub printHtmlRemark


sub printHtmlForm {	# Show the form 
  &printHtmlFormStart();

  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_assay\" VALUE=\"$theHash{assay}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_involved\" VALUE=\"$theHash{involved}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_notinvolved\" VALUE=\"$theHash{notinvolved}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_remark\" VALUE=\"$theHash{remark}{html_value}\">\n";
  &printHtmlInputQuery('wbbtf','20', 'Query WBbtf');        		# 20 characters
  &printHtmlAssay();
  &printHtmlPhenotype();
  &printHtmlGene();
  &printHtmlInvolved();
  &printHtmlNotInvolved();
  &printHtmlRemark();
  &printHtmlInputH('reference','20');        		# 20 characters
  &printHtmlFormEnd();
} # sub printHtmlForm

sub printHtmlInputQuery {		# print html inputs with queries
  my ($type, $size, $message) = @_;	# get type, use hash for html parts
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  unless ($size) { $size = 25; }
  if ($theHash{$type}{html_size_main}) { $size = $theHash{$type}{html_size_main}; }
  if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
  print <<"  EndOfText";
    <TR><TD align='right'><B>$type :</B></TD><TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  SIZE=$theHash{$type}{html_size_main}></TD>
    <TD ALIGN="left"><INPUT TYPE="submit" NAME="action" VALUE="$message !"></TD></TR>
  EndOfText
} # sub printHtmlInputQuery

sub printHtmlInputH {            # print html inputs
  my ($type, $size) = @_;             # get type, use hash for html parts
  if ($size) { $theHash{$type}{html_size_main} = $size; }
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value}) { if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } }
  if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
  print <<"  EndOfText";
    <TR><TD align='right'><B>$type :</B></TD><TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  SIZE=$theHash{$type}{html_size_main}></TD></TR>
  EndOfText
} # sub printHtmlInputH

sub printHtmlFormStart {        # beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/anatomy_function.cgi">
  <TABLE>
  <TR><TD COLSPAN=2> </TD></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !">
        <INPUT TYPE="submit" NAME="action" VALUE="Dump All !"><!--
        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !">
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !">--></TD>
  </TR>
  </TABLE>
  <TABLE>
  <TR><TD></TD></TR><TR><TD></TD></TR> <TR><TD></TD></TR><TR><TD></TD></TR> 
  EndOfText
} # sub printHtmlFormStart

sub printHtmlFormEnd {          # ending of form
  print <<"  EndOfText";
  <TR><TD COLSPAN=2> </TD></TR>
  <TR>
    <TD> </TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Preview !"><!--
        <INPUT TYPE="submit" NAME="action" VALUE="Save !">
        <INPUT TYPE="submit" NAME="action" VALUE="Load !">
        <INPUT TYPE="submit" NAME="action" VALUE="Reset !">--></TD>
  </TR>
  </TABLE>
  </FORM>
  EndOfText
} # sub printHtmlFormEnd

#################  HTML SECTION #################

#################  HASH SECTION #################

sub initializeHash {
  %theHash = ();

  $theHash{assay}{html_value} = 1;	# default number of assay rows
  $theHash{involved}{html_value} = 1;	# default number of involved rows
  $theHash{notinvolved}{html_value} = 1;	# default number of not involved rows
  $theHash{remark}{html_value} = 1;	# default number of remark rows

  $theHash{assay}{html_label} = 'Assay';
  $theHash{phenotype}{html_label} = 'Phenotype';
  $theHash{gene}{html_label} = 'Gene';
  $theHash{involved}{html_label} = 'Involved';
  $theHash{notinvolved}{html_label} = 'Not Involved';
  $theHash{remark}{html_label} = 'Remark';
  $theHash{reference}{html_label} = 'Reference';

  foreach my $type (@PGparameters) {
    $theHash{$type}{html_size_main} = 20;
    $theHash{$type}{html_size_minor} = 1;
  } # foreach my $type (@PGparameters)

# #   $evidence{Paper_evidence}++;
#   $evidence{Published_as}++;
#   $evidence{Person_evidence}++;
#   $evidence{Author_evidence}++;
# #   $evidence{Accession_evidence}++;
# #   $evidence{Protein_id_evidence}++;
# #   $evidence{GO_term_evidence}++;
# #   $evidence{Expr_pattern_evidence}++;
# #   $evidence{Microarray_results_evidence}++;
# #   $evidence{RNAi_evidence}++;
# #   $evidence{Gene_regulation_evidence}++;
# #   $evidence{CGC_data_submission}++;
#   $evidence{Curator_confirmed}++;
# #   $evidence{Inferred_automatically}++;
# #   $evidence{Date_last_updated}++;
# #   $evidence{Feature_evidence}++;
# #   $evidence{Laboratory_evidence}++;

#   @anatfunc = qw( Autonomous Nonautonomous Sufficient Insufficient Necessary Unnecessary Remark );

} # sub initializeHash

#################  HASH SECTION #################

sub readPhenOnt {
  my ($phenont_data) = get( "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/phenotype_ontology_obo.cgi" );
  my (@paras) = split/\n\n/, $phenont_data;
  foreach my $para (@paras) {
    if ($para =~ m/id: WBPhenotype:(\d+).*?\bname: (\w+)/s) { 
      my $term = $2; my $number = 'WBPhenotype:' . $1;
      $phenotypeTerms{term}{$term} = $number;
      $phenotypeTerms{number}{$number} = $term; } }
} # sub readPhenOnt

# file is no longer in cvs  2010 12 08
# sub readCvs {
#   my $directory = '/home/postgres/work/citace_upload/allele_phenotype/temp';
#   chdir($directory) or die "Cannot go to $directory ($!)";
#   `cvs -d /var/lib/cvsroot checkout PhenOnt`;
#   my $file = $directory . '/PhenOnt/PhenOnt.obo';
#   $/ = "";
#   open (IN, "<$file") or die "Cannot open $file : $!";
#   while (my $para = <IN>) { 
#     if ($para =~ m/id: WBPhenotype:(\d+).*?\bname: (\w+)/s) { 
#       my $term = $2; my $number = 'WBPhenotype:' . $1;
#       $phenotypeTerms{term}{$term} = $number;
#       $phenotypeTerms{number}{$number} = $term; } }
#   close (IN) or die "Cannot close $file : $!";
#   $directory .= '/PhenOnt';
#   `rm -rf $directory`;
# #   foreach my $term (sort keys %{ $phenotypeTerms{term} }) { print "T $term N $phenotypeTerms{term}{$term} E<BR>\n"; }
# } # sub readCvs

sub getGeneInfo {
  my $result = $dbh->prepare( "SELECT * FROM gin_sequence;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $geneInfo{gene}{$row[0]}{$row[1]}++; $geneInfo{back}{$row[1]} = $row[0]; }
  $result = $dbh->prepare( "SELECT * FROM gin_synonyms;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $geneInfo{gene}{$row[0]}{$row[1]}++; $geneInfo{back}{$row[1]} = $row[0]; }
  $result = $dbh->prepare( "SELECT * FROM gin_locus;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $geneInfo{gene}{$row[0]}{$row[1]}++; $geneInfo{back}{$row[1]} = $row[0]; }
} # sub getGeneInfo

sub getWpaIdentifier {
#   my $result = $dbh->prepare( "SELECT * FROM wpa_identifier ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { 
#     if ($row[3] eq 'valid') { $wpaId{$row[1]} = $row[0]; }
#       else { delete $wpaId{$row[1]}; } }
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    $papId{$row[1]} = $row[0]; }
} # sub getWpaIdentifier

sub getAnatInfo {
#   my $u = 'http://brebiou.cshl.edu/viewcvs/*checkout*/Wao/WBbt.obo?rev=HEAD&content-type=text/plain';	# FIX PUT THIS BACK WHEN READY
# #   my $u = 'http://tazendra.caltech.edu/~azurebrd/sanger/wbbt/wbbt.obo';		# temp storage of wbbt.obo for quick debugging
#   my $ua = LWP::UserAgent->new(timeout => 30); #instantiates a new user agent
#   my $request = HTTP::Request->new(GET => $u); #grabs url
#   my $response = $ua->request($request);       #checks url, dies if not valid.
#   unless ($response-> is_success) { print "CSHL Site is down, $u won't work<BR>\n"; }
#   die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
#   my (@entries) = split/\[Term\]/, $response->content;
  my $file = '/home/acedb/cron/wbbt.obo';	# use local file updated by cronjob in case cshl is down  2008 10 28
  $/ = undef;
  open (IN, "<$file") or die "Cannot open $file : $!";
  my $file_cont = <IN>;
  close (IN) or die "Cannot close $file : $!";
  my (@entries) = split/\[Term\]/, $file_cont;
  foreach my $entry (@entries) {
    if ($entry =~ m/id: WBbt:(\d+)\s*\nname: (.*?)\n/) {
      $anatInfo{name}{$2} = $1;
      $anatInfo{number}{$1} = $2; } }
} # sub getAnatInfo

__END__

anatomy_term ontology here :
http://brebiou.cshl.edu/viewcvs/*checkout*/Wao/WBbt.obo?rev=HEAD&content-type=text/plain

//name shall be "WBbtf0001"
?Anatomy_function       Assay ?AO_code XREF Anatomy_function ?Condition
                        Phenotype UNIQUE ?Phenotype XREF Anatomy_function #Anatomy_function_info
                        Gene UNIQUE ?Gene XREF Anatomy_function #Evidence //use Published_as tag
                        Body_part Involved ?Anatomy_term XREF Anatomy_function #Anatomy_function_info
                                  Not_involved ?Anatomy_term XREF Anatomy_function_not #Anatomy_function_info
                        Remark Text #Evidence
                        Reference UNIQUE ?Paper XREF Anatomy_function


#Anatomy_function_info  Autonomous Text
                        Nonautonomous Text
                        Sufficient Text
                        Insufficient Text
                        Necessary Text
                        Unnecessary Text
                        Remark Text

//AO_code
//Blastomere_isolation
//Expression_mosaic
//Genetic_ablation
//Genetic_mosaic
//Laser_ablation


http://brebiou.cshl.edu/viewcvs/Wao/WBbt.obo
the important lines are:
id: WBbt:0001001
name: AB




