#!/usr/bin/perl

# Curate Yeast Hybrid data

# Store data keying off of the whole Y1H###### instead of grabbing the number
# at the end, because there will be Y2H data eventually, possibly.  2007 03 29
#
# not using wpa tables, no need to switch to pap  2010 06 23




use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate
use LWP::UserAgent;	# getting sanger files for querying
use Ace;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my $query = new CGI;	# new CGI form

my %theHash;		# huge hash for each field with relevant values
my @PG_unique_evi = qw( yh );
my @PG_unique = qw( pcr_bait sequence_bait pcr_target sequence_target experiment_type interactome_type laboratory );	# laboratory has no text
my @PG_multi_text = qw( library directed reference );	# directed has no text
my @PG_multi_evi = qw( bait_over_cds bait_over_gene target_over_cds target_over_gene remark );	# remark has no text


my %phenotypeTerms;	# phenotype name/number info
my %geneInfo;		# gin sequence/synonyms/locus info
my %anatInfo;		# cvs anatomy info data  name/name->number number/number->name
# my %wpaId;		# wpa identifier info	# no longer used
my @gene_evi = qw( Published_as );
my @rem_evi = qw( Curator_confirmed Person_evidence );
# my @evidence = qw( Paper_evidence Published_as Person_evidence Author_evidence Accession_evidence Protein_id_evidence GO_term_evidence Expr_pattern_evidence Microarray_results_evidence RNAi_evidence Gene_regulation_evidence CGC_data_submission Curator_confirmed Inferred_automatically Date_last_updated Feature_evidence Laboratory_evidence);
my @evidence = qw( Paper_evidence Curator_confirmed );
my @phen_anatfunc = qw( Autonomous Nonautonomous Remark );
my @inv_anatfunc = qw( Sufficient Necessary Remark );
my @not_anatfunc = qw( Insufficient Unnecessary Remark );
# my %evidence;		# the evidence hash tags
# my @anatfunc;		# the anatomy function info tags

my $action;

my $badData;		# flag if some data entered does not correspond to existing data

  &printHeader('Yeast Hybrid Curation Form');	# normal form view
  &initializeHash();	# Initialize theHash structure for html names and box sizes
  &process();		# do everything
  &printFooter(); 

sub process {
  (my $var, $action) = &getHtmlVar($query, 'action');
  unless ($action) { $action = ''; &printHtmlForm(); }

  print "ACTION : $action : ACTION<BR>\n"; 
  if ($action eq 'Preview !') { &preview(); } 				# check yh exists, or assign a new one
  elsif ($action =~ 'Add .*? !') { &addBox($action); }			# rewrite form with another remark box
  elsif ($action eq 'Write !') { &write(); } 				# write data to postgres tables
  elsif ($action eq 'Query YH !') { &queryPostgres(); }			# check yh exists and query from postgres
  elsif ($action eq 'Dump All !') { &dumpAll(); } 			# query all data from postgres to hash and write .ace file
} # sub process

sub dumpAll {
  my $file = 'yh_curation.ace';
  my $outfile = '/home/postgres/public_html/cgi-bin/data/' . $file;
  my $url = 'http://tazendra.caltech.edu/~postgres/cgi-bin/data/' . $file;
  print "Started dumping all .ace data to <A HREF=$url>$url</A>.<BR>";
  open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
  my $result = $dbh->prepare( "SELECT * FROM yhc_yh ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  my %yhs;
  while (my @row = $result->fetchrow) { $yhs{$row[0]}++; }
  foreach my $joinkey (sort keys %yhs) {
    &populateFromPg($joinkey);
    my ($acefile) = &getAceFromHash();
    print OUT "$acefile\n\n";
  }
  close (OUT) or die "Cannot close $outfile : $!";
  print "Finished dumping<BR>\n";
} # sub dumpAll

sub queryPostgres {
  my $type = 'yh';
  (my $var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
  my $joinkey = $theHash{$type}{html_value}; 
  if ($joinkey) {
      my $result = $dbh->prepare( "SELECT yhc_yh FROM yhc_yh WHERE joinkey = '$joinkey';");
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

  foreach my $type (@PG_unique) {
    my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = 1 ORDER BY yhc_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    my $g_type = $type;
    my $g_type2 = $type . '_text';
    $theHash{$g_type}{html_value} = $row[2]; 
    $theHash{$g_type2}{html_value} = $row[3]; }

  foreach my $type (@PG_unique_evi) {
    my $g_type = $type;
    my @evi = @evidence; push @evi, 'none';
    foreach my $evi (@evi) {
      my $g_type3 = $type . '_' . $evi;
      my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = '1' AND yhc_evitype = '$evi' ORDER BY yhc_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow;
      $theHash{$g_type3}{html_value} = $row[5]; 
      if ($evi eq 'none') { $theHash{$g_type}{html_value} = $row[2]; } } }

  foreach my $type (@PG_multi_text) {
    my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' ORDER BY yhc_order DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1];
    for my $i (1 .. $theHash{$type}{html_value}) {
      $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = '$i' ORDER BY yhc_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow;
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      $theHash{$g_type}{html_value} = $row[2]; 
      $theHash{$g_type2}{html_value} = $row[3]; } }

  foreach my $type (@PG_multi_evi) {
    my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' ORDER BY yhc_order DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow; $theHash{$type}{html_value} = $row[1];
    for my $i (1 .. $theHash{$type}{html_value}) {
      my @evi = @evidence; push @evi, 'none';
      foreach my $evi (@evi) {
        $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = '$i' AND yhc_evitype = '$evi' ORDER BY yhc_timestamp DESC;" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row = $result->fetchrow;
        if ($evi eq 'none') {
          my $g_type = $type . '_' . $i;
          my $g_type2 = $type . '_text_' . $i;
          $theHash{$g_type}{html_value} = $row[2]; 
          $theHash{$g_type2}{html_value} = $row[3]; }
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        $theHash{$g_type3}{html_value} = $row[5]; } } }
} # sub queryPostgres

sub write {
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  print "WRITE $joinkey J<BR>\n";

  foreach my $type (@PG_unique_evi) {
    my $g_type = $type;
    my $val1 = $theHash{$g_type}{html_value}; my $wval1 = $val1;
    my @evi = @evidence; push @evi, 'none';
    foreach my $evi (@evi) {
      my $g_type3 = $type . '_' . $evi;
      my $val3 = $theHash{$g_type3}{html_value}; my $wval3 = $val3;
      my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = '1' AND yhc_evitype = '$evi' ORDER BY yhc_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow;
      my $pg_val1 = ''; if ($row[2]) { $pg_val1 = $row[2]; }
      my $pg_val3 = ''; if ($row[5]) { $pg_val3 = $row[5]; }
      if ( ( ($val1 ne $pg_val1) && ($evi eq 'none') ) || ($val3 ne $pg_val3) ) {
#       if ($val1 ne $pg_val1) { # }
#         if ( ($evi eq 'none') || ($val3 ne $pg_val3) ) { # }				# always write if evidence type is none or the evidence has changed
          if ($val1) { $wval1 = "'$val1'"; } else { $wval1 = 'NULL'; }
          if ($val3) { $wval3 = "'$val3'"; } else { $wval3 = 'NULL'; }
          my $command = "INSERT INTO yhc_$type VALUES ('$joinkey', '1', $wval1, NULL, '$evi', $wval3, CURRENT_TIMESTAMP)";
          my $result2 = $dbh->do( $command );
          print "<FONT COLOR='green'>$command</FONT><BR>\n"; } } }

  foreach my $type (@PG_unique) {
    my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = 1 ORDER BY yhc_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow;
    my $pg_val1 = ''; if ($row[2]) { $pg_val1 = $row[2]; }
    my $pg_val2 = ''; if ($row[3]) { $pg_val2 = $row[3]; }
    my $g_type = $type;
    my $g_type2 = $type . '_text';
    my $val1 = $theHash{$g_type}{html_value}; my $wval1 = $val1;
    my $val2 = $theHash{$g_type2}{html_value}; my $wval2 = $val2;
    if ( ($val1 ne $pg_val1) || ($val2 ne $pg_val2) ) { 
      if ($val1) { $wval1 = "'$val1'"; } else { $wval1 = 'NULL'; }
      if ($val2) { $wval2 = "'$val2'"; } else { $wval2 = 'NULL'; }
      my $command = "INSERT INTO yhc_$type VALUES ('$joinkey', '1', $wval1, $wval2, NULL, NULL, CURRENT_TIMESTAMP)";
      my $result2 = $dbh->do( $command );
      print "<FONT COLOR='green'>$command</FONT><BR>\n"; } }

  foreach my $type (@PG_multi_text) {
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = '$i' ORDER BY yhc_timestamp DESC;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      my @row = $result->fetchrow;
      my $pg_val1 = ''; if ($row[2]) { $pg_val1 = $row[2]; }
      my $pg_val2 = ''; if ($row[3]) { $pg_val2 = $row[3]; }
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      my $val1 = $theHash{$g_type}{html_value}; my $wval1 = $val1;
      my $val2 = $theHash{$g_type2}{html_value}; my $wval2 = $val2;
      if ( ($val1 ne $pg_val1) || ($val2 ne $pg_val2) ) {
        if ($val1) { $wval1 = "'$val1'"; } else { $wval1 = 'NULL'; }
        if ($val2) { $wval2 = "'$val2'"; } else { $wval2 = 'NULL'; }
        my $command = "INSERT INTO yhc_$type VALUES ('$joinkey', '$i', $wval1, $wval2, NULL, NULL, CURRENT_TIMESTAMP)";
        my $result2 = $dbh->do( $command );
        print "<FONT COLOR='green'>$command</FONT><BR>\n"; } } }

  foreach my $type (@PG_multi_evi) {
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      my $val1 = $theHash{$g_type}{html_value}; my $wval1 = $val1;
      my $val2 = $theHash{$g_type2}{html_value}; my $wval2 = $val2;
      my @evi = @evidence; push @evi, 'none';
      foreach my $evi (@evi) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        my $val3 = $theHash{$g_type3}{html_value}; my $wval3 = $val3;
        my $result = $dbh->prepare( "SELECT * FROM yhc_$type WHERE joinkey = '$joinkey' AND yhc_order = '$i' AND yhc_evitype = '$evi' ORDER BY yhc_timestamp DESC;" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row = $result->fetchrow;
        my $pg_val1 = ''; if ($row[2]) { $pg_val1 = $row[2]; }
        my $pg_val2 = ''; if ($row[3]) { $pg_val2 = $row[3]; }
        my $pg_val3 = ''; if ($row[5]) { $pg_val3 = $row[5]; }
        if ( ( ( ($val1 ne $pg_val1) || ($val2 ne $pg_val2) ) && ($evi eq 'none') ) || ($val3 ne $pg_val3) ) {
	  # if the evidence is diff, must write it otherwise, if one of the values is diff and evi is none, must write it
          if ($val1) { $wval1 = "'$val1'"; } else { $wval1 = 'NULL'; }
          if ($val2) { $wval2 = "'$val2'"; } else { $wval2 = 'NULL'; }
          if ($val3) { $wval3 = "'$val3'"; } else { $wval3 = 'NULL'; }
          my $command = "INSERT INTO yhc_$type VALUES ('$joinkey', '$i', $wval1, $wval2, '$evi', $wval3, CURRENT_TIMESTAMP)";
          my $result2 = $dbh->do( $command );
          print "<FONT COLOR='green'>$command</FONT><BR>\n"; } } } }

  print "<P>\n";

  foreach my $key (sort keys %theHash) {
    my $val = $theHash{$key}{html_value};
    print "K $key V <FONT COLOR='green'>$val</FONT> E<BR>\n";
  }

  print "Done writing to postgres.<BR>\n";
} # sub write

sub preview {
  print "<FORM METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/yh_curation.cgi\">\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
#   foreach my $key (sort keys %theHash) {
#     my $val = $theHash{$key}{html_value};
#     print "K $key V <FONT COLOR='green'>$val</FONT> E<BR>\n";
#   }

  my $type = 'yh';
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";

  foreach my $type (@PG_unique) {
    my $g_type = $type;
    my $g_type2 = $type . '_text';
    if ($theHash{$g_type}{html_value}) {
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\">\n"; } }

  foreach my $type (@PG_unique_evi) {
    my $g_type = $type;
    if ($theHash{$g_type}{html_value}) {
      print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi;
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type3\" VALUE=\"$theHash{$g_type3}{html_value}\">\n"; } } }

  foreach my $type (@PG_multi_text) {
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      if ($theHash{$g_type}{html_value}) {
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\">\n"; } } }

  foreach my $type (@PG_multi_evi) {
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      if ($theHash{$g_type}{html_value}) {
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\">\n";
        print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\">\n";
        foreach my $evi (@evidence) {
          my $g_type3 = $type . '_' . $evi . '_' . $i;
          print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$g_type3\" VALUE=\"$theHash{$g_type3}{html_value}\">\n"; } } } }

  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Write !\">\n";
  print "</FORM>\n";

  my ($acefile) = &getAceFromHash();
  if ($acefile =~ m/\n/) { $acefile =~ s/\n/<BR>\n/g; }
  print ".ace preview : <BR><FONT COLOR='green'>$acefile</FONT><BR>\n";
} # sub preview

sub getAceFromHash {		# create and return a .ace file based on data in %theHash
  my $acefile = '';
  my $ace_pcrprod = '';
  my $ace_cds = '';
  my $ace_sequence = '';
  my $ace_gene = '';
  my $ace_paper = '';
  my $obj_name = "$theHash{yh}{html_value}";
  $acefile .= "YH : \"$obj_name\"\n";

  my $type = 'pcr_bait';
  my $g_type = $type;
  my $g_type2 = $type . '_text';
  if ($theHash{$g_type}{html_value}) {
    $acefile .= "PCR_bait\t\"$theHash{$g_type}{html_value}\"\n"; 
    if ($theHash{$g_type2}{html_value}) { $ace_pcrprod .= "PCR_product\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
      else { $ace_pcrprod .= "PCR_product\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\n\n"; } }

  $type = 'sequence_bait';
  $g_type = $type;
  if ($theHash{$g_type}{html_value}) {
    $g_type2 = $type . '_text';
    $acefile .= "Sequence_bait\t\"$theHash{$g_type}{html_value}\"\n"; 
    if ($theHash{$g_type2}{html_value}) { $ace_sequence .= "Sequence\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
      else { $ace_sequence .= "Sequence\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\n\n"; } }

  $type = 'pcr_target';
  $g_type = $type;
  if ($theHash{$g_type}{html_value}) {
    $g_type2 = $type . '_text';
    $acefile .= "PCR_target\t\"$theHash{$g_type}{html_value}\"\n"; 
    if ($theHash{$g_type2}{html_value}) { $ace_sequence .= "PCR_product\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
      else { $ace_sequence .= "PCR_product\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\n\n"; } }

  $type = 'sequence_target';
  $g_type = $type;
  if ($theHash{$g_type}{html_value}) {
    $g_type2 = $type . '_text';
    $acefile .= "Sequence_target\t\"$theHash{$g_type}{html_value}\"\n"; 
    if ($theHash{$g_type2}{html_value}) { $ace_sequence .= "Sequence\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
      else { $ace_sequence .= "Sequence\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\n\n"; } }

  $type = 'bait_over_cds';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      next if ($theHash{$g_type}{html_value} eq '');
      my $g_type2 = $type . '_text_' . $i;
      $acefile .= "Bait_overlapping_CDS\t\"$theHash{$g_type}{html_value}\"\n"; 
      if ($theHash{$g_type2}{html_value}) { $ace_cds .= "CDS\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
        else { $ace_cds .= "CDS\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\n\n"; }
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        if ($theHash{$g_type3}{html_value}) { $acefile .= "Bait_overlapping_CDS\t\"$theHash{$g_type}{html_value}\"\t$evi\t\"$theHash{$g_type}{html_value}\"\n"; } } } }
    
  $type = 'bait_over_gene';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      next if ($theHash{$g_type}{html_value} eq '');
      my $g_type2 = $type . '_text_' . $i;
      $acefile .= "Bait_overlapping_gene\t\"$theHash{$g_type}{html_value}\"\n"; 
      if ($theHash{$g_type2}{html_value}) { $ace_gene .= "Gene\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
        else { $ace_gene .= "Gene\t\"$theHash{$g_type}{html_value}\"\nYH_bait\t\"$obj_name\"\n\n"; }
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        if ($theHash{$g_type3}{html_value}) { $acefile .= "Bait_overlapping_gene\t\"$theHash{$g_type}{html_value}\"\t$evi\t\"$theHash{$g_type}{html_value}\"\n"; } } } }
    
  $type = 'target_over_cds';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      next if ($theHash{$g_type}{html_value} eq '');
      my $g_type2 = $type . '_text_' . $i;
      $acefile .= "Target_overlapping_CDS\t\"$theHash{$g_type}{html_value}\"\n"; 
      if ($theHash{$g_type2}{html_value}) { $ace_cds .= "CDS\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
        else { $ace_cds .= "CDS\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\n\n"; }
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        if ($theHash{$g_type3}{html_value}) { $acefile .= "Target_overlapping_CDS\t\"$theHash{$g_type}{html_value}\"\t$evi\t\"$theHash{$g_type}{html_value}\"\n"; } } } }
    
  $type = 'target_over_gene';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      my $g_type2 = $type . '_text_' . $i;
      $acefile .= "Target_overlapping_gene\t\"$theHash{$g_type}{html_value}\"\n"; 
      if ($theHash{$g_type2}{html_value}) { $ace_gene .= "Gene\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
        else { $ace_gene .= "Gene\t\"$theHash{$g_type}{html_value}\"\nYH_target\t\"$obj_name\"\n\n"; }
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        if ($theHash{$g_type3}{html_value}) { $acefile .= "Target_overlapping_gene\t\"$theHash{$g_type}{html_value}\"\t$evi\t\"$theHash{$g_type}{html_value}\"\n"; } } } }

  $type = 'library';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      $g_type2 = $type . '_text_' . $i;
      if ($theHash{$g_type2}{html_value}) { $acefile .= "Library_screened\t\"$theHash{$g_type}{html_value}\"\t\"$theHash{$g_type2}{html_value}\"\n"; }
        else { $acefile .= "Library_screened\t\"$theHash{$g_type}{html_value}\"\n"; } } }

  $type = 'experiment_type';
  if ($theHash{$type}{html_value}) { $acefile .= "Experiment_type\t\"$theHash{$type}{html_value}\"\n"; }

  $type = 'directed';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) { $acefile .= "Directed_Y1H\t\"$theHash{$g_type}{html_value}\"\n"; } }

  $type = 'interactome_type';
  if ($theHash{$type}{html_value}) { $acefile .= "Interactome_type\t\"$theHash{$type}{html_value}\"\n"; }

  $type = 'laboratory';
  if ($theHash{$type}{html_value}) { $acefile .= "From_laboratory\t\"$theHash{$type}{html_value}\"\n"; }

  $type = 'reference';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      my $g_type2 = $type . '_text_' . $i;
      $acefile .= "Reference\t\"$theHash{$g_type}{html_value}\"\n"; 
      if ($theHash{$g_type2}{html_value}) { $ace_paper .= "Paper\t\"$theHash{$g_type}{html_value}\"\nYH\t\"$obj_name\"\t\"$theHash{$g_type2}{html_value}\"\n\n"; }
        else { $ace_paper .= "Paper\t\"$theHash{$g_type}{html_value}\"\nYH\t\"$obj_name\"\n\n"; } } }
    
  $type = 'remark';
  for my $i (1 .. $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    if ($theHash{$g_type}{html_value}) {
      $acefile .= "Remark\t\"$theHash{$g_type}{html_value}\"\n"; 
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        if ($theHash{$g_type3}{html_value}) { $acefile .= "Remark\t\"$theHash{$g_type}{html_value}\"\t$evi\t\"$theHash{$g_type}{html_value}\"\n"; } } } }
    
  if ($acefile) { $acefile .= "\n"; }
  if ($ace_pcrprod) { $acefile .= $ace_pcrprod; }
  if ($ace_sequence) { $acefile .= $ace_sequence; }
  if ($ace_cds) { $acefile .= $ace_cds; }
  if ($ace_gene) { $acefile .= $ace_gene; }
  if ($ace_paper) { $acefile .= $ace_paper; }
  return $acefile;

#   my $type = 'assay';
#   for my $i (1 .. $theHash{$type}{html_value}) {
#     my $g_type = $type . '_' . $i;
#     if ($theHash{$g_type}{html_value}) { 
#       my $g_type2 = 'cond_' . $i;
#       if ($theHash{$g_type2}{html_value}) { $acefile .= "Assay\t\"$theHash{$g_type}{html_value}\"\tAnatomy_function\t\"$theHash{$g_type2}{html_value}\"\n"; }
#         else { $acefile .= "Assay\t\"$theHash{$g_type}{html_value}\"\n"; } } }
# 
#   $type = 'phenotype';
#   if ($theHash{$type}{html_value}) {
#     my $phenotype = $theHash{$type}{html_value};
#     ($phenotype) = $phenotype =~ m/(WBPhenotype\d+)/;
#     my $has_data = 0;
#     foreach my $anat (@phen_anatfunc) {
#       my $g_type_two = $type . '_' . $anat;
#       my $g_type_one = $type . '_' . $anat . '_check';
#       if ($theHash{$g_type_two}{html_value}) { 
#           my (@lines) = split/\n/, $theHash{$g_type_two}{html_value};
#           foreach my $line (@lines) {
#             if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
#             $acefile .= "Phenotype\t\"$phenotype\"\t$anat\t\"$line\"\n"; $has_data++; } }
#         elsif ($theHash{$g_type_one}{html_value}) { $acefile .= "Phenotype\t\"$phenotype\"\t$anat\n"; $has_data++; } }
#     unless ($has_data) { $acefile .= "Phenotype\t\"$phenotype\"\n"; } }
# 
#   $type = 'gene';
#   if ($theHash{$type}{html_value}) {
#     my $gene = $theHash{$type}{html_value}; 
#     ($gene) = $gene =~ m/(WBGene\d+)/;
#     my $has_data = 0;
#     foreach my $evi (@gene_evi) {
#       my $g_type_two = $type . '_' . $evi;
#       if ($theHash{$g_type_two}{html_value}) { 
#         my (@lines) = split/\n/, $theHash{$g_type_two}{html_value};
#         foreach my $line (@lines) {
#           if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
#           $acefile .= "Gene\t\"$gene\"\t$evi\t\"$line\"\n"; $has_data++; } } }
#     unless ($has_data) { $acefile .= "Gene\t\"$gene\"\n"; } }
# 
#   my (@same_types) = qw( involved notinvolved );
#   foreach my $type (@same_types) {
#     my $tag = ucfirst($type);
#     for my $i (1 .. $theHash{$type}{html_value}) {
#       my $g_type = $type . '_' . $i;
#       if ($theHash{$g_type}{html_value}) {
#         my $val = $theHash{$g_type}{html_value}; 
#         ($val) = $val =~ m/^(WBbt:\d+)/;
#         my $has_data = 0;
#         my @anats = @inv_anatfunc; if ($type eq 'notinvolved') { @anats = @not_anatfunc; }
#         foreach my $anat (@anats) {
#           my $g_type_one = $type . '_' . $anat . '_' . $i . '_check';
#           my $g_type_two = $type . '_' . $anat . '_' . $i;
#           if ($theHash{$g_type_two}{html_value}) { 
#               my (@lines) = split/\n/, $theHash{$g_type_two}{html_value};
#               foreach my $line (@lines) {
#                 if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
#                 $acefile .= "$tag\t\"$val\"\t$anat\t\"$line\"\n"; $has_data++; } }
#             elsif ($theHash{$g_type_one}{html_value}) { $acefile .= "$tag\t\"$val\"\t$anat\n"; $has_data++; } }
#         unless ($has_data) { $acefile .= "$tag\t\"$val\"\n"; } } } }
# 
#   $type = 'remark';
#   my $val = $theHash{$type}{html_value}; 
#   for my $i (1 .. $theHash{$type}{html_value}) {
#     my $g_type = $type . '_' . $i;
#     if ($theHash{$g_type}{html_value}) {
#       my $remark = $theHash{$g_type}{html_value}; 
#       my $has_data = 0;
#       foreach my $evi (@rem_evi) {
#         my $g_type2 = $type . '_' . $evi . '_' . $i;
#         if ($theHash{$g_type2}{html_value}) { 
#           my (@lines) = split/\n/, $theHash{$g_type2}{html_value};
#           foreach my $line (@lines) {
#             if ($line =~ m/\s+$/) { $line =~ s/\s+$//g; }
#             $acefile .= "Remark\t\"$remark\"\t$evi\t\"$line\"\n"; $has_data++; } } }
#       unless ($has_data) { $acefile .= "Remark\t\"$remark\"\n"; } } }
# 
#   $type = 'reference';
#   if ($theHash{$type}{html_value}) {
#     my $ref = $theHash{$type}{html_value};
#     ($ref) = $ref =~ m/^(WBPaper\d+)/;
#     $acefile .= "Reference\t\"$ref\"\n"; }
} # sub getAceFromHash

sub addBox {
  my $action = shift;
  my ($type) = $action =~ m/Add (.*?) \!/;
  print "ADD $type <BR>\n";
  my $joinkey = &getHtmlValuesFromForm(); 		# populate %theHash and get joinkey
  $theHash{$type}{html_value}++; 
  &printHtmlForm();
} # sub addInvolved

sub getHtmlValuesFromForm {	# read PGparameters value from html form, then display to html
#   &getGeneInfo();		# populate %geneInfo
#   &getWpaIdentifier();		# populate %wpaId

  my $type = 'yh';
  (my $var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");

  foreach my $type (@PG_unique) {
    my $g_type = $type;
    my $g_type2 = $type . '_text';
    ($var, $theHash{$g_type}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type");
    ($var, $theHash{$g_type2}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type2");
  } # foreach my $type (@PG_unique)

  foreach my $type (@PG_unique_evi) {
    my $g_type = $type;
    ($var, $theHash{$g_type}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type");
    foreach my $evi (@evidence) {
      my $g_type3 = $type . '_' . $evi;
      ($var, $theHash{$g_type3}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type3"); }
  } # foreach my $type (@PG_unique_evi)

  foreach my $type (@PG_multi_text) {
    ($var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      ($var, $theHash{$g_type}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type");
      ($var, $theHash{$g_type2}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type2");
    } # for my $i (1 .. $theHash{$type}{html_value})
  } # foreach my $type (@PG_multi_text)

  foreach my $type (@PG_multi_evi) {
    ($var, $theHash{$type}{html_value} ) = &getHtmlVar($query, "html_value_main_$type");
    for my $i (1 .. $theHash{$type}{html_value}) {
      my $g_type = $type . '_' . $i;
      my $g_type2 = $type . '_text_' . $i;
      ($var, $theHash{$g_type}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type");
      ($var, $theHash{$g_type2}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type2");
      foreach my $evi (@evidence) {
        my $g_type3 = $type . '_' . $evi . '_' . $i;
        ($var, $theHash{$g_type3}{html_value} ) = &getHtmlVar($query, "html_value_main_$g_type3"); }
    } # for my $i (1 .. $theHash{$type}{html_value})
  } # foreach my $type (@PG_multi_evi)

  my $joinkey = 'no joinkey';
  if ($theHash{yh}{html_value}) { $joinkey = $theHash{yh}{html_value}; } 
  return $joinkey;
} # sub getHtmlValuesFromForm 


#################  HTML SECTION #################

sub printHtmlForm {	# Show the form 
  &printHtmlFormStart();

  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_assay\" VALUE=\"$theHash{assay}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_involved\" VALUE=\"$theHash{involved}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_notinvolved\" VALUE=\"$theHash{notinvolved}{html_value}\">\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_remark\" VALUE=\"$theHash{remark}{html_value}\">\n";
  &printHtmlInputEviQuery('yh', 'Query YH');        		# 20 characters
#   &printHtmlAssay();
#   &printHtmlPhenotype();
#   &printHtmlGene();
#   &printHtmlInvolved();
#   &printHtmlNotInvolved();
#   &printHtmlRemark();
#   &printHtmlInputH('reference','20');        		# 20 characters
  &printHtmlInputText('pcr_bait');
  &printHtmlInputText('sequence_bait');
  &printHtmlMultiEvi('bait_over_cds');
  &printHtmlMultiEvi('bait_over_gene');
  &printHtmlInputText('pcr_target');
  &printHtmlInputText('sequence_target');
  &printHtmlMultiEvi('target_over_cds');
  &printHtmlMultiEvi('target_over_gene');
  &printHtmlMultiSelectText('library');
  &printHtmlSelect('experiment_type');
  &printHtmlMulti('directed');
  &printHtmlSelect('interactome_type');
  &printHtmlInputH('laboratory');
  &printHtmlMultiText('reference');
  &printHtmlMultiEvi('remark');
  &printHtmlFormEnd();
} # sub printHtmlForm

sub printHtmlInputQuery {		# print html inputs with queries
  my ($type, $size, $message) = @_;	# get type, use hash for html parts
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  unless ($size) { $size = 25; }
  if ($theHash{$type}{html_size_main}) { $size = $theHash{$type}{html_size_main}; }
  if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
  print <<"  EndOfText";
    <TR><TD align='right'><B>$type :</B></TD><TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  SIZE=$size></TD>
        <TD align='left'><INPUT TYPE="submit" NAME="action" VALUE="$message !"></TD></TR>
  EndOfText
} # sub printHtmlInputQuery

sub printHtmlInputEviQuery {
  my ($type, $message) = @_;	# get type, use hash for html parts
  print "<TR><TD ALIGN=\"right\"><STRONG>$type :</STRONG></TD>";
  my $g_type = $type;
  my $g_type2 = $type . '_text';
  unless ($theHash{$g_type2}{html_value}) { $theHash{$g_type2}{html_value} = 'Y1H'; }
  print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n";
  print "<TD align='left'><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"$message !\"></TD></TR>\n";
  foreach my $evi (@evidence) {
    my $g_type3 = $type . '_' . $evi;
    print "<TR><TD align=right><FONT SIZE-=2 COLOR=green>$evi</FONT></TD><TD COLSPAN=6><TEXTAREA COLS=80 ROWS=1 NAME=\"html_value_main_$g_type3\" >$theHash{$g_type3}{html_value}</TEXTAREA></TD></TR>\n";
  } # foreach my $evi (@evidence)
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add $type !\"></TD></TR>\n";
} # sub printHtmlInputEviQuery

sub printHtmlInputH {            # print html inputs
  my ($type, $size) = @_;             # get type, use hash for html parts
  if ($size) { $theHash{$type}{html_size_main} = $size; }
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value}) { if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } }
  if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
  if ($type eq 'laboratory') { unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = 'VL'; } }
  print <<"  EndOfText";
    <TR><TD align='right'><B>$type :</B></TD><TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  SIZE=$theHash{$type}{html_size_main}></TD></TR>
  EndOfText
} # sub printHtmlInputH

sub printHtmlInputText {            # print html inputs
  my ($type, $size) = @_;             # get type, use hash for html parts
  if ($size) { $theHash{$type}{html_size_main} = $size; }
#   unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
#   if ($theHash{$type}{html_value}) { if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } }
#   if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
  my $g_type = $type;
  my $g_type2 = $type . '_text';
  unless ($theHash{$g_type2}{html_value}) { $theHash{$g_type2}{html_value} = 'Y1H'; }
  print "<TR><TD align='right'><B>$type :</B></TD><TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n";
  print "<TD><INPUT NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD></TR>\n";
#   print <<"  EndOfText";
#     <TR><TD align='right'><B>$type :</B></TD><TD><INPUT NAME="html_value_main_$type" VALUE="$theHash{$type}{html_value}"  SIZE=$theHash{$type}{html_size_main}></TD></TR>
#   EndOfText
} # sub printHtmlInputText

sub printHtmlMultiEvi {
  my $type = shift;
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . '_' . $i;
    my $g_type2 = $type . '_text_' . $i;
    unless ($theHash{$g_type2}{html_value}) { $theHash{$g_type2}{html_value} = 'Y1H'; }
    print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n";
    unless ($type eq 'remark') { print "<TD><INPUT NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n"; }	# remark has no text
    print "</TR>\n";
    foreach my $evi (@evidence) {
      my $g_type3 = $type . '_' . $evi . '_' . $i;
      print "<TR><TD align=right><FONT SIZE-=2 COLOR=green>$evi</FONT></TD><TD COLSPAN=6><TEXTAREA COLS=80 ROWS=1 NAME=\"html_value_main_$g_type3\" >$theHash{$g_type3}{html_value}</TEXTAREA></TD></TR>\n";
    } # foreach my $evi (@evidence)
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add $type !\"></TD></TR>\n";
} # sub printHtmlMultiEvi

sub printHtmlMulti {
  my $type = shift;
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . '_' . $i;
    print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD></TR>\n";
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add $type !\"></TD></TR>\n";
} # sub printHtmlMulti

sub printHtmlMultiText {
  my $type = shift;
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    print "<TR><TD ALIGN=\"right\"><STRONG>$theHash{$type}{html_label} $i :</STRONG></TD>";
    my $g_type = $type . '_' . $i;
    my $g_type2 = $type . '_text_' . $i;
    unless ($type eq 'library') { unless ($theHash{$g_type2}{html_value}) { $theHash{$g_type2}{html_value} = 'Y1H'; } }
    if ($type eq 'reference') { unless ($theHash{$g_type}{html_value}) { $theHash{$g_type}{html_value} = 'WBPaper00027683'; } }
    print "<TD><INPUT NAME=\"html_value_main_$g_type\" VALUE=\"$theHash{$g_type}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD>\n";
    print "<TD><INPUT NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD></TR>\n";
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add $type !\"></TD></TR>\n";
} # sub printHtmlMultiText

sub printHtmlSelect {
  my ($type, $size) = @_;             # get type, use hash for html parts
  if ($size) { $theHash{$type}{html_size_main} = $size; }
  unless ($theHash{$type}{html_value}) { $theHash{$type}{html_value} = ''; }
  if ($theHash{$type}{html_value}) { if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } }
  if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
  my @experiment_type = qw( Y2H Y1H );
  my @interactome_type = qw( Interactome_core_1 Interactome_core_2 Interactome_noncore );
  print "    <TR><TD align=right><STRONG>$theHash{$type}{html_label} </STRONG></TD><TD ALIGN=left><SELECT NAME=\"html_value_main_$type\" SIZE=1>\n";
  if ($theHash{$type}{html_value}) { 
    if ($theHash{$type}{html_value} =~ m/\"/) { $theHash{$type}{html_value} =~ s/\"/&quot;/g; } 
    print "      <OPTION selected>$theHash{$type}{html_value}</OPTION>\n"; }
  print "      <OPTION > </OPTION>\n"; # if loaded or queried, show option, otherwise default to '' option
  if ($type eq 'experiment_type') { foreach (@experiment_type) { print "      <OPTION>$_</OPTION>\n"; } }
    elsif ($type eq 'interactome_type') { foreach (@interactome_type) { print "      <OPTION>$_</OPTION>\n"; } }
    else { 1; }
  print "    </SELECT></TD></TR>\n ";
} # sub printHtmlSelect

sub printHtmlMultiSelectText {
  my $type = shift;
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"html_value_main_$type\" VALUE=\"$theHash{$type}{html_value}\">\n";
  for my $i (1 ..  $theHash{$type}{html_value}) {
    my $g_type = $type . '_' . $i;
    my $g_type2 = $type . '_text_' . $i;
    my @library_screen = ('AD-wrmcDNA library', 'AD-TF mini-library');
    print "    <TR><TD align=right><STRONG>$theHash{$type}{html_label} </STRONG></TD><TD ALIGN=left><SELECT NAME=\"html_value_main_$g_type\" SIZE=1>\n";
    if ($theHash{$g_type}{html_value}) { 
      if ($theHash{$g_type}{html_value} =~ m/\"/) { $theHash{$g_type}{html_value} =~ s/\"/&quot;/g; } 
      print "      <OPTION selected>$theHash{$g_type}{html_value}</OPTION>\n"; }
    print "      <OPTION > </OPTION>\n"; # if loaded or queried, show option, otherwise default to '' option
    foreach (@library_screen) { print "      <OPTION>$_</OPTION>\n"; }
    print "    </SELECT></TD>\n ";
    print "<TD><INPUT NAME=\"html_value_main_$g_type2\" VALUE=\"$theHash{$g_type2}{html_value}\" SIZE=$theHash{$type}{html_size_main}></TD></TR>\n";
  } # for my $i (1 ..  $theHash{$type}{html_value})
  print "<TR><TD align=right><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Add $type !\"></TD></TR>\n";
} # sub printHtmlSelect

sub printHtmlFormStart {        # beginning of form
  print <<"  EndOfText";
  <A NAME="form"><H1>Add your entries : </H1></A>
  <FORM METHOD="POST" ACTION="http://tazendra.caltech.edu/~postgres/cgi-bin/yh_curation.cgi">
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

  $theHash{remark}{html_value} = 1;	# default number of remark rows
  $theHash{bait_over_cds}{html_value} = 1;
  $theHash{bait_over_gene}{html_value} = 1;
  $theHash{target_over_cds}{html_value} = 1;
  $theHash{target_over_gene}{html_value} = 1;
  $theHash{directed}{html_value} = 1;
  $theHash{reference}{html_value} = 1;
  $theHash{library}{html_value} = 1;

  $theHash{bait_over_cds}{html_label} = 'Bait Overlapping CDS';
  $theHash{bait_over_gene}{html_label} = 'Bait Overlapping Gene';
  $theHash{target_over_cds}{html_label} = 'Target Overlapping CDS';
  $theHash{target_over_gene}{html_label} = 'Target Overlapping Gene';
  $theHash{assay}{html_label} = 'Assay';
  $theHash{phenotype}{html_label} = 'Phenotype';
  $theHash{gene}{html_label} = 'Gene';
  $theHash{involved}{html_label} = 'Involved';
  $theHash{notinvolved}{html_label} = 'Not Involved';
  $theHash{remark}{html_label} = 'Remark';
  $theHash{reference}{html_label} = 'Reference';
  $theHash{directed}{html_label} = 'Directed Y1H';
  $theHash{reference}{html_label} = 'Reference';
  $theHash{library}{html_label} = 'Library Screened';
  $theHash{experiment_type}{html_label} = 'Experiment Type';
  $theHash{interactome_type}{html_label} = 'Interactome Type';

  foreach my $type ( @PG_multi_evi, @PG_unique_evi, @PG_unique, @PG_multi_text ) {
    $theHash{$type}{html_size_main} = 40;
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

sub readCvs {
  my $directory = '/home/postgres/work/citace_upload/allele_phenotype/temp';
  chdir($directory) or die "Cannot go to $directory ($!)";
  `cvs -d /var/lib/cvsroot checkout PhenOnt`;
  my $file = $directory . '/PhenOnt/PhenOnt.obo';
  $/ = "";
  open (IN, "<$file") or die "Cannot open $file : $!";
  while (my $para = <IN>) { 
    if ($para =~ m/id: WBPhenotype(\d+).*?\bname: (\w+)/s) { 
      my $term = $2; my $number = 'WBPhenotype' . $1;
      $phenotypeTerms{term}{$term} = $number;
      $phenotypeTerms{number}{$number} = $term; } }
  close (IN) or die "Cannot close $file : $!";
  $directory .= '/PhenOnt';
  `rm -rf $directory`;
#   foreach my $term (sort keys %{ $phenotypeTerms{term} }) { print "T $term N $phenotypeTerms{term}{$term} E<BR>\n"; }
} # sub readCvs

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

# no longer used
# sub getWpaIdentifier {
#   my $result = $dbh->prepare( "SELECT * FROM wpa_identifier ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { 
#     if ($row[3] eq 'valid') { $wpaId{$row[1]} = $row[0]; }
#       else { delete $wpaId{$row[1]}; } }
# } # sub getWpaIdentifier

sub getAnatInfo {
  my $u = 'http://brebiou.cshl.edu/viewcvs/*checkout*/Wao/WBbt.obo?rev=HEAD&content-type=text/plain';	# FIX PUT THIS BACK WHEN READY
#   my $u = 'http://tazendra.caltech.edu/~azurebrd/sanger/wbbt/wbbt.obo';		# temp storage of wbbt.obo for quick debugging
  my $ua = LWP::UserAgent->new(timeout => 30); #instantiates a new user agent
  my $request = HTTP::Request->new(GET => $u); #grabs url
  my $response = $ua->request($request);       #checks url, dies if not valid.
  unless ($response-> is_success) { print "CSHL Site is down, $u won't work<BR>\n"; }
  die "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
  my (@entries) = split/\[Term\]/, $response->content;
  foreach my $entry (@entries) {
    if ($entry =~ m/id: WBbt:(\d+)\s*\nname: (.*?)\n/) {
      $anatInfo{name}{$2} = $1;
      $anatInfo{number}{$1} = $2; } }
} # sub getAnatInfo


__END__

pcr_bait
sequence_bait
pcr_target
sequence_target
bait_over_cds
bait_over_gene
target_over_cds
target_over_gene
remark
directed
reference
library
experiment_type
interactome_type

my @PG_multi_evi = qw( bait_over_cds bait_over_gene target_over_cds target_over_gene remark );	# remark has no text
my @PG_unique = qw( pcr_bait sequence_bait pcr_target sequence_target experiment_type interactome_type laboratory );	# laboratory has no text
my @PG_multi_text = qw( library directed reference );	# directed has no text

    Interactor Bait PCR_bait UNIQUE ?PCR_product XREF YH_bait
                    Sequence_bait UNIQUE ?Sequence XREF YH_bait
               Target PCR_target UNIQUE ?PCR_product XREF YH_target
                      Sequence_target UNIQUE ?Sequence XREF YH_target
    Experiment_type    UNIQUE    Y2H
                                 Y1H
    Interactome_type UNIQUE  Interactome_core_1
                             Interactome_core_2
                             Interactome_noncore

    Directed_Y1H Text
    Reference ?Paper XREF YH

    Library_screened Text    INT //wrmcDNA or TF libraries    times_found

                    Bait_overlapping_CDS ?CDS XREF YH_bait #Evidence
                    Bait_overlapping_gene ?Gene XREF YH_bait #Evidence
                      Target_overlapping_CDS ?CDS XREF YH_target #Evidence
                      Target_overlapping_gene ?Gene XREF YH_target #Evidence
    Remark ?Text #Evidence

?YH Evidence #Evidence
    Interactor Bait PCR_bait UNIQUE ?PCR_product XREF YH_bait
                    Sequence_bait UNIQUE ?Sequence XREF YH_bait
                    Bait_overlapping_CDS ?CDS XREF YH_bait #Evidence
                    Bait_overlapping_gene ?Gene XREF YH_bait #Evidence
               Target PCR_target UNIQUE ?PCR_product XREF YH_target
                      Sequence_target UNIQUE ?Sequence XREF YH_target
                      Target_overlapping_CDS ?CDS XREF YH_target #Evidence
                      Target_overlapping_gene ?Gene XREF YH_target #Evidence
    Library_screened Text    INT //wrmcDNA or TF libraries    times_found
    Experiment_type    UNIQUE    Y2H
                                 Y1H
    Directed_Y1H Text
    Interactome_type UNIQUE  Interactome_core_1
                             Interactome_core_2
                             Interactome_noncore
    Origin From_laboratory UNIQUE ?Laboratory
    Reference ?Paper XREF YH
    Remark ?Text #Evidence

?PCR_product
        YH_bait    ?YH  XREF PCR_bait Text//Y1H or Y2H for merged YH model
        YH_target  ?YH  XREF PCR_target Text

?CDS
        YH_bait   ?YH XREF Bait_overlapping_CDS Text// Y1H or Y2H for merged YH model
        YH_target ?YH XREF Target_overlapping_CDS Text

?Sequence
        YH_bait   ?YH XREF Sequence_bait Text //Y1H or Y2H for merged YH model
        YH_target ?YH XREF Sequence_target Text

?Gene
        YH_bait   ?YH XREF Bait_overlapping_gene   Text//Y1H or Y2H for merged YH model
        YH_target ?YH XREF Target_overlapping_gene Text//Y1H or Y2H for merged YH model  

?Paper
        YH  ?YH XREF Reference Text//for merged YeastHybrid model


__END__

