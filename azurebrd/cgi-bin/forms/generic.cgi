#!/usr/bin/perl 

# Generic public tasks. (show ip, verify papers, update obo_ for app_tempname)

# updated ip.cgi to update obo_ tables for Jolene, and verify person connections, replacing 
# confirm_paper.cgi   2010 06 10
# 
# made &showAntibodyData() for Xiaodong to get antibody results from textpresso minus
# first-passed as false-positive minus curated under abp_reference  2010 07 15
#
# made  &addToVariationObo  as a counter to  &updateVariationObo
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=AddToVariationObo
# this only adds new entries to obo_<stuff>_app_tempname (in some 33 seconds), while the 
# latter does a wipe and rewrite in about 55 minutes (timing out on browsers).  2010 08 20
#
# /home/postgres/work/pgpopulation/obo_oa_ontologies/update_obo_oa_ontologies.pl
# call UpdateVariationObo  on 1st of month and  AddToVariationObo  other days of the month.
# (a full update takes too long to run every day)  
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=UpdateVariationObo
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=AddToVariationObo
# 2010 08 23
#
# updated UpdateVariationObo and AddToVariationObo to write to new app_rearrangement,
# app_transgene, app_variation tables (instead of app_tempname).  Also store other information
# based on text files.  2010 09 08
#
# changed  &mailConfirmation()  to have the subject not say WBPersontwo1234, just WBPerson1234.
# Thanks Michael Paulini for pointing it out.  2010 09 16 
#
# changed total_variations.txt file to not have tabs.  2010 09 23
#
# transgene now from transgene OA, not from obo tables off of files in Jo's path.  2010 09 28
#
# added code for new obotables for VariationObo subs, need to delete code for old tables when 
# live.  2011 02 23
#
# removed code for old obotables.  added code for strain and clone.  2011 05 19
#
# changed  &updateVariationObo()  to also populate obo_ geneclass from
# '/home/acedb/karen/Gene_class/Gene_class_term_info.txt';  2011 06 27
#
# changed  &updateVariationObo()  to only update when called by 131.215.52.76 or 127.0.0.1
# 2011 06 28 
#
# changed message to point at release wiki instead of saying 8 weeks nor 4 months.  2011 10 19
#
# added obo_<name|data>_exprcluster for Karen.  2012 01 18
#
# added  &tempVariationObo  &printTempVariationForm  &addTempVariationObo   for Karen or anyone
# to enter new wbvar and publicname to obo_name_variation, obo_data_variation (with a fixed 
# comment and a pgDate timestamp), and to a flatfile /home/azurebrd/public_html/cgi-bin/data/obo_tempfile_variation
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=TempVariationObo
# 2013 10 16  live on tazendra.  2013 10 24
# 
# new sub &pictureByPaper() to display all canopus images for a given paper, for Daniela.  2014 10 16
#
# new subs  &papIdToWBPaper()  and  &convertToWBPaper()  to convert list of identifiers to WBPaperIDs
# for Chris.  did not want mapping of identifier to WBPaper, just the WBPaper.  splits on whitespace, 
# so identifiers with whitespace in them will never match (like "ISBN 0-8493-4048-9").  does not deal
# with commas or pipes, so those will never match either.  2014 12 10
#
# updated  &papIdToWBPaper()  and changed  &convertToWBPaper()  into  &convertPaperIdentifiers()
# for more generic conversion between IDs and optionally displaying titles.  2015 03 05


use Jex;			# untaint, getHtmlVar, cshlNew, getPgDate
use strict;
use diagnostics;
use CGI;
use LWP::UserAgent;		# for variation_nameserver file
use LWP::Simple;		# for simple gets
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $ua = new LWP::UserAgent;


my $query = new CGI;
my $host = $query->remote_host();		# get ip address

&process();                     # see if anything clicked

sub process {                   # see if anything clicked
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'VerifyPaper') {                  &verifyPaper(); }
  elsif ($action eq 'ShowAntibodyData') {          &showAntibodyData(); }
  elsif ($action eq 'UpdateVariationObo') {        &updateVariationObo(); }
  elsif ($action eq 'AddToVariationObo') {         &addToVariationObo(); }
  elsif ($action eq 'TempVariationObo') {          &tempVariationObo(); }
  elsif ($action eq 'AddTempVariationObo') {       &addTempVariationObo(); }
  elsif ($action eq 'ContinentPIs') {              &continentPIs(); }
  elsif ($action eq 'PictureByPaper') {            &pictureByPaper(); }
  elsif ($action eq 'PapIdToWBPaper') {            &papIdToWBPaper(); }
  elsif ($action eq 'ConvertPaperIdentifiers') {   &convertPaperIdentifiers(); }
  elsif ($action eq 'WpaXref') {                   &wpaXref(); }
  elsif ($action eq 'WpaXrefBackwards') {          &wpaXref('backward'); }
  else { &showIp(); }
}



sub showIp {
  print "Content-type: text/html\n\n";
  my $title = 'Your IP';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }
  print "Your IP is : $host<BR>\n";
  print "$footer"; 		# make end of HTML page
} # sub showIp

sub pictureByPaper {				# display all canopus images for a given paper
  print "Content-type: text/html\n\n";
  my ($var, $papid)   = &getHtmlVar($query, 'paperid');
  my ($joinkey) = $papid =~ m/(\d+)/;
  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = 'WBPaper$joinkey' ;" );
  $result->execute();
  while (my @row = $result->fetchrow) { if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) {  # all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; 
    foreach my $line (@lines) { 
      my ($url, $name) = $line =~ m/"([^"]*)".*>(.*)<\/a>/;
      next if ($name =~ m/.txt$/);
      print qq($name<br/><img src="$url"><br />\n); 
  } }
} # sub pictureByPaper

sub convertPaperIdentifiers {
  print "Content-type: text/html\n\n";
  my $title = 'Convert pap_identifier to WBPaper';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my %maps; my @paps; my @bads;
  $result = $dbh->prepare( "SELECT * FROM pap_title;" ); $result->execute();
  while (my @row = $result->fetchrow) { $maps{papToData}{title}{"WBPaper$row[0]"} = $row[1]; }
  my @prefixes = qw( pmid doi );
  $result = $dbh->prepare( "SELECT * FROM pap_identifier;" ); $result->execute();
  while (my @row = $result->fetchrow) { 
    foreach my $prefix (@prefixes) {
      my ($identifier) = lc($row[1]);
      if ($identifier =~ m/$prefix(.*)/) {
        $maps{papToData}{wbpaper}{"WBPaper$row[0]"}    = "WBPaper$row[0]";
        $maps{papToData}{$prefix}{"WBPaper$row[0]"}    = $1;
        $maps{papToId}{$prefix}{"WBPaper$row[0]"}      = $1;
        $maps{papToId}{$prefix}{$row[0]}               = $1;
        $maps{idToPap}{$prefix}{$1}                    = "WBPaper$row[0]";
        $maps{idToPap}{$prefix}{$identifier}           = "WBPaper$row[0]"; } } }
  my ($var, $pap_identifiers)   = &getHtmlVar($query, 'pap_identifiers');
  ($var, my $identifier_type)   = &getHtmlVar($query, 'identifier_type');
  my (@pap_identifiers) = split/\s+/, $pap_identifiers;

  my @output_types = qw( wbpaper pmid doi title);
  my @table_header = (); my $table_header;
  foreach my $output_type (@output_types) {
    ($var, my $output_type_chosen)   = &getHtmlVar($query, "output_$output_type");
    if ($output_type_chosen eq $output_type) { push @table_header, $output_type; } }
#   $table_header = join"\t", @table_header; push @paps, $table_header;
  $table_header = join"</td><td>", @table_header; push @paps, $table_header;
  foreach my $pap_identifier (@pap_identifiers) {
    ($pap_identifier) = lc($pap_identifier);
    my @row_output;
    my $wbpaper = '';
    if ($identifier_type eq 'wbpaper') { ($wbpaper) = $pap_identifier =~ m/(\d+)/; $wbpaper = 'WBPaper' . $wbpaper; }
      else { 
        if ($maps{idToPap}{$identifier_type}{$pap_identifier}) { $wbpaper = $maps{idToPap}{$identifier_type}{$pap_identifier}; }
          else { push @bads, $pap_identifier; next; } }
    my $row_has_data = 0;
    foreach my $output_type (@output_types) {
      ($var, my $output_type_chosen)   = &getHtmlVar($query, "output_$output_type");
      next unless ($output_type_chosen eq $output_type);
      if ($maps{papToData}{$output_type}{$wbpaper}) { push @row_output, $maps{papToData}{$output_type}{$wbpaper}; $row_has_data++; }
        else { push @row_output, ""; }
    } # foreach my $output_type (@output_types)
    if ($row_has_data > 0) { 
#         my $row_output = join"\t", @row_output; push @paps, $row_output;
        my $row_output = join"</td><td>", @row_output; push @paps, $row_output;
      }
      else { push @bads, $pap_identifier; }
  } # foreach my $pap_identifier (@pap_identifiers)

  print qq(<table border="1">);
  foreach my $pap (@paps) { print "<tr><td>$pap</td></tr>\n"; }
  print qq(</table>);
  if (scalar @bads > 0) {
    print qq(<br/>The following identifiers didn't map to a WBPaperID :<br/>\n);
    foreach my $bad (@bads) { print "$bad<br/>\n"; } }
  print "$footer"; 		# make end of HTML page
} # sub convertPaperIdentifiers

sub papIdToWBPaper {
  print "Content-type: text/html\n\n";
  my $title = 'Convert pap_identifier to WBPaper';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  print qq(<form method="post" action="generic.cgi">\n);
  my @identifier_types = qw( wbpaper pmid doi );
  my %identifier_labels;
  $identifier_labels{wbpaper} = 'WBPaper00012345 or simply 00012345';
  $identifier_labels{pmid}    = 'pmid12345678 or simply 12345678';
  $identifier_labels{doi}     = '10.1534/genetics.113.157685';
  print qq(Type of IDs for source (what you paste in)<br/>\n);
  foreach my $identifier_type (@identifier_types) {
    print qq(<input type="radio" NAME="identifier_type" VALUE="$identifier_type"> $identifier_type &nbsp; ( enter as $identifier_labels{$identifier_type} ).<br/>\n); }
#   print qq(Paper Identifiers (ids without prefix nor leading zeros will be treated as pmid)\n);
  print qq(<br/>Enter source IDs here :<br/>\n);
  print qq(<textarea id="pap_identifiers" name="pap_identifiers" rows="20" cols="80"></textarea><br/>\n);
  print qq(<br/>Click here to reset the box with source IDs <button type="button" onclick="document.getElementById('pap_identifiers').value='';">reset source IDs</button><br/>\n);
  print qq(<br/>Select types of output :<br/>\n);
  foreach my $identifier_type (@identifier_types, "title") {
    print qq(<input type="checkbox" NAME="output_$identifier_type" VALUE="$identifier_type"> $identifier_type<br/>\n); }
  print qq(<br/><input type="submit" NAME="action" VALUE="ConvertPaperIdentifiers"><br/>\n);
  print qq(</form>\n);
  print "$footer"; 		# make end of HTML page
} # sub papIdToWBPaper

sub wpaXref {			# replace wpa_xref.cgi and wpa_xref_backwards.cgi  for Kimberly for Nicole Washington  2013 12 06
  my ($viewFlag) = @_;
  if ($viewFlag eq 'backward') { print "Content-type: text/plain\n\n"; }
    else { print "Content-type: text/html\n\n"; }
  my %papHash;
  $result = $dbh->prepare( "SELECT * FROM pap_identifier ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $papHash{$row[0]}{$row[1]}++; }
  foreach my $pap (sort keys %papHash) {
    foreach my $other (sort keys %{ $papHash{$pap} }) {
      if ($viewFlag eq 'backward') { print "$other\tWBPaper$pap\n"; }
        else { print "WBPaper$pap\t$other<BR>\n"; }
  } }
} # sub wpaXref

sub showAntibodyData {
  print "Content-type: text/html\n\n";
  my $title = 'Antibody textpresso data minus FP minus curated';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my %fp; my %curated; my @results;
  $result = $dbh->prepare( "SELECT joinkey FROM cfp_antibody WHERE LOWER(cfp_antibody ) ~ 'false positive';" ); $result->execute;
  while (my @row = $result->fetchrow) { $fp{$row[0]}++; }
  $result = $dbh->prepare( "SELECT DISTINCT(abp_reference) FROM abp_reference;" ); $result->execute;
  while (my @row = $result->fetchrow) { 
    my (@entries) = $row[0] =~ m/(\d+)/g;
    foreach my $entry (@entries) { $curated{$entry}++; } }
  my $url = "http://textpresso-dev.caltech.edu/azurebrd/wen/anti_protein_wen";
  my $textpresso_data = get $url;
  my (@lines) = split/\n/, $textpresso_data;
  foreach my $line (@lines) {
    my ($id) = $line =~ m/WBPaper(\d+)\t/;
    unless ($fp{$id} || $curated{$id}) { push @results, "$line<br />"; } }
  print "There are " . scalar(@results) . " entries from $url MINUS curated in abp_reference MINUS flagged as FALSE POSITIVE in cfp_antibody<br /><br />\n";
  foreach my $line (@results) { print $line; }
  print "$footer"; 		# make end of HTML page
} # sub showAntibodyData

sub verifyPaper {
  print "Content-type: text\/html\n\n<html><head><title>Confirm Author-Paper-Person Connections</title>\n</head>\n";        # don't resize window  2009 03 17
#  print "Content-type: text\/html\n\n<html><head><title>Confirm Author-Paper-Person Connections</title>\n<script>window.resizeTo(320, 150);</script></head>\n";

  my ($two, $aid, $pap_join, $curator, $yes_no);
  if ($query->param('two_number')) { $two = $query->param('two_number'); }
  if ($query->param('aid')) { $aid = $query->param('aid'); }
  if ($query->param('pap_join')) { $pap_join = $query->param('pap_join'); }
  if ($query->param('yes_no')) { $yes_no = $query->param('yes_no'); }
  if ($two) {
    $result = $dbh->prepare( "SELECT two_standardname FROM two_standardname WHERE joinkey = '$two';" ); $result->execute;
    my @row = $result->fetchrow;
    if ($row[0]) { $curator = $row[0]; } }
  my $error = 0;
  unless ($two) { print "ERROR, no WBPerson number : $aid, $pap_join<BR>\n"; $error++; }
  unless ($aid) { print "ERROR, no AuthorID number : $two, $pap_join<BR>\n"; $error++; }
  unless ($pap_join) { print "ERROR, no pap_join number : $two, $aid<BR>\n"; $error++; }
  unless ($curator) { print "ERROR, no Curator Standardname : $two, $aid, $pap_join<BR>\n"; $error++; }
  unless ($yes_no) { print "ERROR, no selection for Yours or Not Yours : $two, $aid, $pap_join<BR>\n"; $error++; }
  if ($error) { die "Improper selections on single connection\n"; }

  if ($curator =~ m/\"/) { $curator =~ s/\"/\\\"/g; }                   # escape double quotes for postgres and html display
  if ($curator =~ m/\'/) { $curator =~ s/\'/''/g; }                     # escape single quotes for postgres and html display

#   my $command = "INSERT INTO wpa_author_verified VALUES ($aid, '$yes_no $curator', $pap_join, 'valid', '$two', CURRENT_TIMESTAMP);";
  my @pgcommands;
  my $command = "DELETE FROM pap_author_verified WHERE author_id ='$aid' AND pap_join = $pap_join;";
  push @pgcommands, $command;
  $command = "INSERT INTO pap_author_verified VALUES ($aid, '$yes_no $curator', $pap_join, '$two', CURRENT_TIMESTAMP);";
  push @pgcommands, $command;
  $command = "INSERT INTO h_pap_author_verified VALUES ($aid, '$yes_no $curator', $pap_join, '$two', CURRENT_TIMESTAMP);";
  push @pgcommands, $command;

  foreach my $command (@pgcommands) {
    $result = $dbh->do( $command );               # uncomment this for sub to work
    print "<!--$command<BR>-->\n";
  }
  print "Thank you for connecting this paper as $yes_no<BR>\n";
  &mailConfirmation($two, $curator);

  print "</html>";
} # sub verifyPaper

sub mailConfirmation {
  my ($two, $std_name) = @_;
  $result = $dbh->prepare( "SELECT two_email FROM two_email WHERE joinkey = '$two' ORDER BY two_timestamp DESC;" );
  $result->execute;
  my @row = $result->fetchrow;
#   my $email = "$row[0], cecnak\@gmail.com";
  my $email = "$row[0]";			# Cecilia doesn't want copies of these email anymore  2011 05 25
  my $user = 'cecilia@tazendra.caltech.edu';
  my $wbperson = $two; $wbperson =~ s/two/WBPerson/;
#   my $subject = "${wbperson}, thank you for updating your Author Person Paper connection";	# changed pre-emptively for Cecilia and Paul  2011 05 19
  my $subject = "Thank you for updating your Author Person Paper connection";
#   my $std_name = 'C. elegans researcher';
  my $body = "Dear $std_name :\n\n";
  $body .= $row[0] . ' Thank you very much for helping associate your C. elegans and other nematodes publications and
abstracts.

Updates will appear in the next release of WormBase in your WBPerson page under author/Person search http://www.wormbase.org . The full release schedule is available here:

http://www.wormbase.org/about/Release_Schedule

Please do not hesitate to contact me if you have any questions.

Have a great day.

Cecilia';
    # Added a file to only email confirmations if they haven't confirmed within the last 86400 seconds  2006 10 02
  my $data_file = '/home/postgres/public_html/cgi-bin/data/confirm_paper_mailing.txt';
  my %time_hash;
  open (IN, "<$data_file") or die "Cannot open $data_file : $!";
  while (<IN>) { chomp; my ($file_two, $time) = split/\t/, $_; $time_hash{$file_two} = $time; }
  close (IN) or die "Cannot close $data_file : $!";
  my $time = time;
  my $mail_stuff = 1;						# by default mail confimation
  my ($only_num) = $two; $only_num =~ s/two//; 
  if ($time_hash{$only_num}) {
    my $diff = $time - $time_hash{$only_num};
    if ($diff < 86400) { $mail_stuff = 0; } }			# less than a day
  if ($mail_stuff) {
    &mailer($user, $email, $subject, $body);			# email letter
    $time_hash{$only_num} = $time;
    open (OUT, ">$data_file") or die "Cannot create $data_file : $!";
    foreach my $only_num (sort keys %time_hash) { print OUT "$only_num\t$time_hash{$only_num}\n"; }
    close (OUT) or die "Cannot close $data_file : $!";
  }
} # sub mailConfirmation

sub continentPIs {				# get all pis, their standardnames, labs, and countries, sorting by continent
  print "Content-type: text/html\n\n";
  my $title = 'PIs and Labs by continent';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $ctcRef = &populateContinents();
  my %countryToContinent = %$ctcRef;
  my %pis; my %joinkeys; my %numToCountry; my %numToStdname; 
  $result = $dbh->prepare( "SELECT * FROM two_pis" ); $result->execute;
  while (my @row = $result->fetchrow) { $pis{$row[0]}{$row[2]}++; }
  my @joinkeys = sort keys %pis; my $joinkeys = join"','", @joinkeys;
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey IN ('$joinkeys')" ); $result->execute;
  while (my @row = $result->fetchrow) { $numToStdname{$row[0]} = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_country WHERE joinkey IN ('$joinkeys')" ); $result->execute;
  my %badCountry; my %byContinent;
  while (my @row = $result->fetchrow) {
    my $country = $row[2]; my $twonum = $row[0];
    $numToCountry{$twonum} = $country;
    if ($countryToContinent{$country}) { $byContinent{$countryToContinent{$country}}{$twonum}++; }
      else { $badCountry{$country}++; }
  } # while (my @row = $result->fetchrow)

  print "<table>\n";
  foreach my $continent (sort keys %byContinent) {
    print "<tr><td><br/></td></tr>\n";
    print "<tr><td>$continent<br/></td></tr>\n";
    foreach my $twonum (sort keys %{ $byContinent{$continent} }) {
      my $personLink = $twonum;
      $personLink =~ s|^two|http://www.wormbase.org/resources/person/WBPerson|;
      my $country = $numToCountry{$twonum};
      my $stdname = $numToStdname{$twonum};
      my @labs    = sort keys %{ $pis{$twonum} }; 
      foreach (@labs) { $_ = '<a href="http://www.wormbase.org/resources/laboratory/' . $_ . '">' . $_ . '</a>'; }
      my $labs = join", ", @labs;
      print qq(<tr><td><a href="$personLink">$stdname</a></td><td>$labs</td><td>$country</td></tr>\n);
    } # foreach my $twonum (sort keys %{ $byContinent{$continent} })
  } # foreach my $continent (sort keys %byContinent)
  print "</table>\n";

  foreach my $country (sort keys %badCountry) {
    print "This country not accounted for in continent list : $country<br/>\n";
  } # foreach my $country (sort keys %badCountry)
  print "$footer"; 		# make end of HTML page
} # sub continentPIs


sub populateContinents {
  my %africa; my %europe; my %asia; my %namerica; my %samerica; my %oceania;

  $europe{'England'}++;
  $europe{'England, UK'}++;
  $europe{'Scotland, UK'}++;
  $europe{'The Netherlands'}++;
  $europe{'UK'}++;

  $asia{'Hong Kong'}++;
  $asia{'Korea'}++;
  $asia{'P. R. China'}++;
  $asia{'P.R. China'}++;
  $asia{'PRC'}++;
  $asia{'R.O.C.'}++;
  $asia{"People's Republic of China"}++;
  $asia{'Republic of Korea'}++;
  $asia{'Republic of Singapore'}++;
  $asia{'South Korea'}++;
  $asia{'Taiwan'}++;

  $namerica{'U. S. A.'}++;
  $namerica{'U.S.A.'}++;
  $namerica{'USA'}++;
  $namerica{'United States of America'}++;

  $africa{'Algeria'}++;
  $africa{'Angola'}++;
  $africa{'Benin'}++;
  $africa{'Botswana'}++;
  $africa{'Burkina'}++;
  $africa{'Burundi'}++;
  $africa{'Cameroon'}++;
  $africa{'Cape Verde'}++;
  $africa{'Central African Republic'}++;
  $africa{'Chad'}++;
  $africa{'Comoros'}++;
  $africa{'Congo'}++;
  $africa{'Congo, Democratic Republic of'}++;
  $africa{'Djibouti'}++;
  $africa{'Egypt'}++;
  $africa{'Equatorial Guinea'}++;
  $africa{'Eritrea'}++;
  $africa{'Ethiopia'}++;
  $africa{'Gabon'}++;
  $africa{'Gambia'}++;
  $africa{'Ghana'}++;
  $africa{'Guinea'}++;
  $africa{'Guinea-Bissau'}++;
  $africa{'Ivory Coast'}++;
  $africa{'Kenya'}++;
  $africa{'Lesotho'}++;
  $africa{'Liberia'}++;
  $africa{'Libya'}++;
  $africa{'Madagascar'}++;
  $africa{'Malawi'}++;
  $africa{'Mali'}++;
  $africa{'Mauritania'}++;
  $africa{'Mauritius'}++;
  $africa{'Morocco'}++;
  $africa{'Mozambique'}++;
  $africa{'Namibia'}++;
  $africa{'Niger'}++;
  $africa{'Nigeria'}++;
  $africa{'Rwanda'}++;
  $africa{'Sao Tome and Principe'}++;
  $africa{'Senegal'}++;
  $africa{'Seychelles'}++;
  $africa{'Sierra Leone'}++;
  $africa{'Somalia'}++;
  $africa{'South Africa'}++;
  $africa{'South Sudan'}++;
  $africa{'Sudan'}++;
  $africa{'Swaziland'}++;
  $africa{'Tanzania'}++;
  $africa{'Togo'}++;
  $africa{'Tunisia'}++;
  $africa{'Uganda'}++;
  $africa{'Zambia'}++;
  $africa{'Zimbabwe'}++;

  $asia{'Afghanistan'}++;
  $asia{'Bahrain'}++;
  $asia{'Bangladesh'}++;
  $asia{'Bhutan'}++;
  $asia{'Brunei'}++;
  $asia{'Burma'}++;
  $asia{'Myanmar'}++;
  $asia{'Cambodia'}++;
  $asia{'China'}++;
  $asia{'East Timor'}++;
  $asia{'India'}++;
  $asia{'Indonesia'}++;
  $asia{'Iran'}++;
  $asia{'Iraq'}++;
  $asia{'Israel'}++;
  $asia{'Japan'}++;
  $asia{'Jordan'}++;
  $asia{'Kazakhstan'}++;
  $asia{'Korea, North'}++;
  $asia{'Korea, South'}++;
  $asia{'Kuwait'}++;
  $asia{'Kyrgyzstan'}++;
  $asia{'Laos'}++;
  $asia{'Lebanon'}++;
  $asia{'Malaysia'}++;
  $asia{'Maldives'}++;
  $asia{'Mongolia'}++;
  $asia{'Nepal'}++;
  $asia{'Oman'}++;
  $asia{'Pakistan'}++;
  $asia{'Philippines'}++;
  $asia{'Qatar'}++;
  $asia{'Russian Federation'}++;
  $asia{'Saudi Arabia'}++;
  $asia{'Singapore'}++;
  $asia{'Sri Lanka'}++;
  $asia{'Syria'}++;
  $asia{'Tajikistan'}++;
  $asia{'Thailand'}++;
  $asia{'Turkey'}++;
  $asia{'Turkmenistan'}++;
  $asia{'United Arab Emirates'}++;
  $asia{'Uzbekistan'}++;
  $asia{'Vietnam'}++;
  $asia{'Yemen'}++;

  $europe{'Albania'}++;
  $europe{'Andorra'}++;
  $europe{'Armenia'}++;
  $europe{'Austria'}++;
  $europe{'Azerbaijan'}++;
  $europe{'Belarus'}++;
  $europe{'Belgium'}++;
  $europe{'Bosnia and Herzegovina'}++;
  $europe{'Bulgaria'}++;
  $europe{'Croatia'}++;
  $europe{'Cyprus'}++;
  $europe{'Czech Republic'}++;
  $europe{'Denmark'}++;
  $europe{'Estonia'}++;
  $europe{'Finland'}++;
  $europe{'France'}++;
  $europe{'Georgia'}++;
  $europe{'Germany'}++;
  $europe{'Greece'}++;
  $europe{'Hungary'}++;
  $europe{'Iceland'}++;
  $europe{'Ireland'}++;
  $europe{'Italy'}++;
  $europe{'Latvia'}++;
  $europe{'Liechtenstein'}++;
  $europe{'Lithuania'}++;
  $europe{'Luxembourg'}++;
  $europe{'Macedonia'}++;
  $europe{'Malta'}++;
  $europe{'Moldova'}++;
  $europe{'Monaco'}++;
  $europe{'Montenegro'}++;
  $europe{'Netherlands'}++;
  $europe{'Norway'}++;
  $europe{'Poland'}++;
  $europe{'Portugal'}++;
  $europe{'Romania'}++;
  $europe{'San Marino'}++;
  $europe{'Serbia'}++;
  $europe{'Slovakia'}++;
  $europe{'Slovenia'}++;
  $europe{'Spain'}++;
  $europe{'Sweden'}++;
  $europe{'Switzerland'}++;
  $europe{'Ukraine'}++;
  $europe{'United Kingdom'}++;
  $europe{'Vatican City'}++;

  $namerica{'Antigua and Barbuda'}++;
  $namerica{'Bahamas'}++;
  $namerica{'Barbados'}++;
  $namerica{'Belize'}++;
  $namerica{'Canada'}++;
  $namerica{'Costa Rica'}++;
  $namerica{'Cuba'}++;
  $namerica{'Dominica'}++;
  $namerica{'Dominican Republic'}++;
  $namerica{'El Salvador'}++;
  $namerica{'Grenada'}++;
  $namerica{'Guatemala'}++;
  $namerica{'Haiti'}++;
  $namerica{'Honduras'}++;
  $namerica{'Jamaica'}++;
  $namerica{'Mexico'}++;
  $namerica{'Nicaragua'}++;
  $namerica{'Panama'}++;
  $namerica{'Saint Kitts and Nevis'}++;
  $namerica{'Saint Lucia'}++;
  $namerica{'Saint Vincent and the Grenadines'}++;
  $namerica{'Trinidad and Tobago'}++;
  $namerica{'United States'}++;

  $oceania{'Australia'}++;
  $oceania{'Fiji'}++;
  $oceania{'Kiribati'}++;
  $oceania{'Marshall Islands'}++;
  $oceania{'Micronesia'}++;
  $oceania{'Nauru'}++;
  $oceania{'New Zealand'}++;
  $oceania{'Palau'}++;
  $oceania{'Papua New Guinea'}++;
  $oceania{'Samoa'}++;
  $oceania{'Solomon Islands'}++;
  $oceania{'Tonga'}++;
  $oceania{'Tuvalu'}++;
  $oceania{'Vanuatu'}++;

  $samerica{'Argentina'}++;
  $samerica{'Bolivia'}++;
  $samerica{'Brazil'}++;
  $samerica{'Chile'}++;
  $samerica{'Colombia'}++;
  $samerica{'Ecuador'}++;
  $samerica{'Guyana'}++;
  $samerica{'Paraguay'}++;
  $samerica{'Peru'}++;
  $samerica{'Suriname'}++;
  $samerica{'Uruguay'}++;
  $samerica{'Venezuela'}++;

  my %countryToContinent;
  foreach my $country (sort keys %africa)   { $countryToContinent{$country} = 'Africa'; }
  foreach my $country (sort keys %europe)   { $countryToContinent{$country} = 'Europe'; }
  foreach my $country (sort keys %asia)     { $countryToContinent{$country} = 'Asia'; }
  foreach my $country (sort keys %namerica) { $countryToContinent{$country} = 'N America'; }
  foreach my $country (sort keys %samerica) { $countryToContinent{$country} = 'S America'; }
  foreach my $country (sort keys %oceania)  { $countryToContinent{$country} = 'Oceania'; }

  return \%countryToContinent;
} # sub populateContinents


sub tempVariationObo {
  print "Content-type: text/html\n\n";
  my $title = 'Add new temporary variation to obo_ tables and flatfile';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $obotempfile = '/home/azurebrd/public_html/cgi-bin/data/obo_tempfile_variation';
  unless (-e $obotempfile) { print "ERROR no obo_tempfile_variation to write to at $obotempfile<br/>"; print $footer; return; }
  &printTempVariationForm();
#   my $action;                   # what user clicked
#   unless ($action = $query->param('action')) { $action = 'none'; }
#   print "Your IP is : $host<BR>\n";
  print "$footer"; 		# make end of HTML page
} # sub tempVariationObo

sub addTempVariationObo {
  print "Content-type: text/html\n\n";
  my $title = 'Add new temporary variation to obo_ tables and flatfile';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $obotempfile = '/home/azurebrd/public_html/cgi-bin/data/obo_tempfile_variation';
  unless (-e $obotempfile) { print "ERROR no obo_tempfile_variation to write to at $obotempfile<br/>"; print $footer; return; }
  my $error_message = '';
  my ($var, $varidnamebatch)   = &getHtmlVar($query, 'varidnamebatch');
#   my ($var, $varid)   = &getHtmlVar($query, 'varid');
#   ($var, my $pubname) = &getHtmlVar($query, 'pubname');
  my (@entries) = split/\n/, $varidnamebatch;
  foreach my $entry (@entries) { 
    my $entry_error = '';
    my ($pubname, $varid) = split/\s+/, $entry;
    if ($varid) {
        $varid =~ s/\s+//g;
        unless ($varid =~ m/^WBVar\d{8}$/) { $entry_error .= "$varid does not match WBVar and 8 digits<br/>\n"; } }
      else   { $entry_error .= "No var id<br/>"; }
    if ($pubname) {
        $pubname =~ s/\s+//g;
#         unless ($pubname =~ m/^[A-Za-z]{1,3}\d{1,5}$/) { $error_message .= "$pubname does not match 1-3 letters and 1-5 digits<br/>\n"; }
        unless ($pubname =~ m/^([A-Za-z]{1,3}\d{1,6}){1,2}$/) { $entry_error .= "$pubname does not match 1 or 2 sets of 1-3 letters and 1-6 digits<br/>\n"; } }
      else   { $entry_error .= "No public name<br/>"; }
#     if ($entry_error) { &printTempVariationForm($entry_error, $varid, $pubname); print $footer; return; }
    $result = $dbh->prepare( "SELECT * FROM obo_name_variation WHERE joinkey = '$varid';" ); $result->execute;
    my @row = $result->fetchrow(); 
    if ($row[0]) { $entry_error .= qq($varid already exists associated to $row[1]<br/>\n); }
    $result = $dbh->prepare( "SELECT * FROM obo_name_variation WHERE obo_name_variation = '$pubname';" ); $result->execute;
    @row = $result->fetchrow(); 
    if ($row[0]) { $entry_error .= qq($pubname already exists associated to $row[0]<br/>\n); }
#     if ($entry_error) { &printTempVariationForm($entry_error, $varid, $pubname); print $footer; return; }
    if ($entry_error) { $error_message .= $entry_error; next; }
    my $pgDate = &getPgDate();
    my $comment = qq(added through generic.cgi, not updated by geneace yet);
    open (OUT, ">>$obotempfile") or die "Cannot append to $obotempfile : $!";
    print OUT qq($varid\t$pubname\t$pgDate\t$comment\n);
    close (OUT) or die "Cannot append to $obotempfile : $!";
    my $terminfo = qq(id: $varid\nname: "$pubname"\ntimestamp: "$pgDate"\ncomment: "$comment");
    $result = $dbh->do( "INSERT INTO obo_name_variation VALUES('$varid', '$pubname');" );
    $result = $dbh->do( "INSERT INTO obo_data_variation VALUES('$varid', '$terminfo');" );
    print "Added $pgDate $varid $pubname to obo_name_variation and obo_data_variation<br/>\n";
  }
  if ($error_message) { &printTempVariationForm($error_message, '', ''); }
  print "$footer"; 		# make end of HTML page
} # sub addTempVariationObo

sub printTempVariationForm {
  my ($error_message, $varid, $pubname) = @_;
  if ($error_message) { print qq(<span style="color: red">ERROR :<br/>$error_message<br/></span>\n); }
  unless ($varid) { $varid = ''; } unless ($pubname) { $pubname = ''; }
  print qq(<form method="post" action="generic.cgi">\n);
  print qq(Public name SPACE WBVarID in separate rows<br/>Example:<br/>tn1455 WBVar02143955<br/>tn1455 WBVar02143955<br/>tn1409 WBVar02143956<br/>tn1408 WBVar02143957<br/>tn1431 WBVar02143958<br/>tn1392 WBVar02143959<br/><textarea name="varidnamebatch" rows="8" cols="80"></textarea><br/>\n);
#   print qq(WBVarID <input name="varid" value="$varid"><br/>\n);
#   print qq(Public name <input name="pubname" value="$pubname"><br/>\n);
  print qq(<input type="submit" NAME="action" VALUE="AddTempVariationObo"><br/>\n);
  print qq(</form>\n);
} # sub printTempVariationForm


__END__

&addToVariationObo  and  &updateVariationObo  are now obsolete, replaced by cronjob update_obo_oa_ontologies.pl calling script nightly_geneace.pl  to temporarily add WBVarID values, instead of adding on nameserver, add them here through  &tempVariationObo

sub OBSOLETEaddToVariationObo {
  my $start_time = time;
  &printHeader('Update obo_ tables only appending new entries for Variation from Nameserver and WS dumps');
  my %pg_data;
#   my $result = $dbh->prepare( "SELECT joinkey FROM obo_name_app_variation WHERE joinkey ~ 'WBVar';" ); $result->execute;
  my $result = $dbh->prepare( "SELECT joinkey FROM obo_name_variation WHERE joinkey ~ 'WBVar';" ); $result->execute;
  while (my @row = $result->fetchrow) { $pg_data{$row[0]}++; }

  my $jo_path = '/home/acedb/jolene/WS_AQL_queries/';
  my %junk_variation;		# junk variations are total variations minus latest set of real variations from Variation_gene.txt   These junk vars are excluded from going into obo_ when getting all values from nameserver.
  my $all_ws_variation_file = $jo_path . 'total_variations.txt';
  open(IN, "<$all_ws_variation_file") or die "Cannot open $all_ws_variation_file : $!";
#   while (my $line = <IN>) { chomp $line; my ($junk) = $line =~ m/\"(.*?)\"\t/; $junk_variation{$junk}++; } 	# no more tabs in total variation files
  while (my $line = <IN>) { chomp $line; my ($junk) = $line =~ m/^\"(.*?)\"$/; $junk_variation{$junk}++; } 
  close(IN) or die "Cannot open $all_ws_variation_file : $!";
  
  my $infile = $jo_path . 'Variation_gene.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) {
    if ($line =~ m/\"(.*?)\"\t\"(WBGene\d+)\"\t\"(.*?)\"/) {
      my ($varid, $gene) = $line =~ m/^\"(.*?)\"\t\"(WBGene\d+)\"/;
      if ($junk_variation{$varid}) { delete $junk_variation{$varid}; } }
    elsif ($line =~ m/\"(.*?)\"/) { 
      if ($junk_variation{$1}) { delete $junk_variation{$1}; } } }
  close (IN) or die "Cannot close $infile : $!";
  
  my %var_data;			# to get name and dead when writing data
  my $url = 'http://www.sanger.ac.uk/cgi-bin/Projects/C_elegans/nameserver_json.pl?domain=Variation';
  print "downloading from $url<br /><br />\n";
  my $request = HTTP::Request->new(GET => $url); #grabs url
  my $response = $ua->request($request);       #checks url, dies if not valid.
  unless ($response-> is_success) { print "nameserver not responding\n"; }
  my $variation_nameserver_file = $response->content;	# LWP::Simple fails for some reason

  my @pgcommands;
  $variation_nameserver_file =~ s/^\[\n\s+\[\n//s;
  $variation_nameserver_file =~ s/\n\s+\]\n\]//s;
  my @var_entries = split/\n\s+\],\n\s+\[\n\s+/, $variation_nameserver_file;
  foreach my $entry (@var_entries) {
    my (@lines) = split/\n/, $entry;
    my ($id) = $lines[0] =~ m/(WBVar\d+)/;
    next unless $id;					# skip entries without an id (there are a couple for some reason)  2011 10 26
    next if ($junk_variation{$id});
    next if ($pg_data{$id});
    next if ($lines[3] =~ m/\"0\"/);                    # skip dead variations for Karen  2011 08 01
    my ($name) = $lines[2] =~ m/\"(.*)\",/; $name =~ s/^\s+//; 
    unless ($name) { $name = $id; }			# everything should have a name, so use id if there isn't, Karen  2011 10 26
    next if ($name =~ m/^gk\d\d\d\d\d\d/);
    next if ($name =~ m/deBono/);
#     my ($dead) = $lines[3] =~ m/\"([10])\"/;		# skipping dead variations don't enter dead tag
#     my $pgcommand = "INSERT INTO obo_name_app_variation VALUES ('$id', '$name', CURRENT_TIMESTAMP);";	# DELETE this when new OA is live (add "my" below)
#     push @pgcommands, $pgcommand;
    my $pgcommand = "INSERT INTO obo_name_variation VALUES ('$id', '$name', CURRENT_TIMESTAMP);";
    push @pgcommands, $pgcommand;
    my $data = "id: $id\nname: \"$name\"\n";
#     $data .= "allele: \"$line\" []";
#     if ($dead) { $data .= "dead: \"dead\"\n"; }		# skipping dead variations don't enter dead tag 2013 02 04
    if ($data =~ m/\'/) { $data =~ s/\'/''/g; }	# escape '
    if ($data =~ m/\\/) { 			# \ have to be escaped in E'' quote
        $data =~ s/\\/\\\\/g; 
        $data = "E'" . $data . "'"; }
      else { $data = "'" . $data . "'"; }
#     $pgcommand = "INSERT INTO obo_data_app_variation VALUES ('$id', $data, CURRENT_TIMESTAMP);";	# DELETE this when new OA is live
#     push @pgcommands, $pgcommand;
    $pgcommand = "INSERT INTO obo_data_variation VALUES ('$id', $data, CURRENT_TIMESTAMP);";
    push @pgcommands, $pgcommand;
  }
  if (scalar (@pgcommands > 1)) { 		# only wipe and repopulate if there's something to enter
    print "data parsed, writing to postgres<br /><br />\n";
    foreach my $pgcommand (@pgcommands) {
#       print "$pgcommand<br />\n";
      $dbh->do( $pgcommand );
    } # foreach my $pgcommand (@pgcommands)
  }
  my $end_time = time;
  my $diff_time = $end_time - $start_time;
  print "This took $diff_time seconds<br />\n";
  &printFooter();
} # sub OBSOLETEaddToVariationObo

sub OBSOLETEupdateVariationObo {
  &printHeader('Update obo_ tables for Variation from Nameserver and WS dumps');

  my $host = $query->remote_host();		# get ip address
  if ( ($host ne '127.0.0.1') && ($host ne '131.215.52.76') ) { 
    print "Your IP is $host<br />\n";
    print "You should wget this from the acedb account on tazendra<br/>";
    &printFooter(); return; }
  

  my %hash;

  my $jo_path = '/home/acedb/jolene/WS_AQL_queries/';

  my %junk_variation;		# junk variations are total variations minus latest set of real variations from Variation_gene.txt   These junk vars are excluded from going into obo_ when getting all values from nameserver.
  my $all_ws_variation_file = $jo_path . 'total_variations.txt';
  open(IN, "<$all_ws_variation_file") or die "Cannot open $all_ws_variation_file : $!";
  while (my $line = <IN>) {
    chomp $line;
#     my ($junk) = $line =~ m/\"(.*?)\"\t/;	# no more tabs in total variation file
    my ($junk) = $line =~ m/^\"(.*?)\"$/;
    $junk_variation{$junk}++;
  } # while (my $line = <IN>)
  close(IN) or die "Cannot open $all_ws_variation_file : $!";
  
# my $infile = 'Variation_gene.txt';
  my $infile = $jo_path . 'Variation_gene.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
# my $junk = <IN>;	# no longer expecting a junk line
  while (my $line = <IN>) {
    chomp $line;
    if ($line =~ m/\"(.*?)\"\t\"(WBGene\d+)\"\t\"(.*?)\"/) {
#       my ($varid, $gene, $name, $pub) = $line =~ m/\"(.*?)\"\t\"(WBGene\d+)\"\t\"(.*?)\"\t\"(.*?)\"/;
      $line =~ s/\"//g;
      my ($varid, @stuff) = split/\t/, $line; 
      my @gs; foreach (@stuff) { if ($_) { push @gs, $_; } } 
      my $data = join"\t", @stuff;	# get good stuff, not blanks
      $data = 'other: "' . $data . '"' . "\n";
      if ($junk_variation{$varid}) { delete $junk_variation{$varid}; }
      $hash{variation}{$varid}{$data}++; }
    elsif ($line =~ m/\"(.*?)\"/) { 
      if ($junk_variation{$1}) { delete $junk_variation{$1}; }
      $hash{variation}{$1}{blank}++; }
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $infile : $!";
  
#   foreach my $id (sort keys %junk_variation) { print "JUNK $id JUNK\n"; }
  my %var_data;			# to get name and dead when writing data
  my $url = 'http://www.sanger.ac.uk/cgi-bin/Projects/C_elegans/nameserver_json.pl?domain=Variation';
#   my $url = 'http://tazendra.caltech.edu/~azurebrd/var/work/nameserverVariation_temp';
  print "downloading from $url<br /><br />\n";
  my $request = HTTP::Request->new(GET => $url); #grabs url
  my $response = $ua->request($request);       #checks url, dies if not valid.
  unless ($response-> is_success) { print "nameserver not responding\n"; }
  my $variation_nameserver_file = $response->content;	# LWP::Simple fails for some reason

  $variation_nameserver_file =~ s/^\[\n\s+\[\n//s;
  $variation_nameserver_file =~ s/\n\s+\]\n\]//s;
  my @var_entries = split/\n\s+\],\n\s+\[\n\s+/, $variation_nameserver_file;
  foreach my $entry (@var_entries) {
    my (@lines) = split/\n/, $entry;
    my ($id) = $lines[0] =~ m/(WBVar\d+)/;
    next if ($junk_variation{$id});
    next if ($lines[3] =~ m/\"0\"/);                    # skip dead variations for Karen  2011 08 01
    my ($name) = $lines[2] =~ m/\"(.*)\",/; if ($name) { $name =~ s/^\s+//; }
    next if ($name =~ m/^gk\d\d\d\d\d\d/);
    next if ($name =~ m/deBono/);
    my ($dead) = $lines[3] =~ m/\"([10])\"/;
    $var_data{$id}{name} = $name;
    $var_data{$id}{dead} = !$dead;
    $hash{variation}{$id}{""}++; 
  }

  $infile = '/home/acedb/karen/Gene_class/Gene_class_term_info.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  my %gene_class; my %gc_tag;
  $gc_tag{'name'} = 'Gene_class';
  $gc_tag{'desc'} = 'Description';
  $gc_tag{'lab'} = 'Laboratory';
  $gc_tag{'genecount'} = 'Number of gene members';
  $gc_tag{'conccount'} = 'Number of gene concise desc';
  $gc_tag{'clonecount'} = 'Number of genes in class cloned';
  $gc_tag{'goterm'} = 'Associated GO terms';
  while (my $line = <IN>) {
    chomp $line;
    my ($name, $desc, $lab, $genecount, $conccount, $clonecount, $goterm) = split/\t/, $line; my $id;
    if ($name =~ m/\"/) { $name =~ s/\"//g; }
    $id = $name; 
    $name = "<a href=\"http://www.wormbase.org/db/gene/gene_class?name=$id;class=Gene_class\" target=\"new\">$id</a>";
    $gene_class{$id}{name}{$name}++;
    if ($goterm)     { 
      $goterm =~ s/\"//g; 
      $goterm = "<a href=\"http://www.wormbase.org/db/ontology/gene?name=$goterm;class=GO_term\" target=\"new\">$goterm</a>";
      $gene_class{$id}{goterm}{$goterm}++; }
    if ($desc)       { $desc =~ s/\"//g;   $gene_class{$id}{desc}{$desc}++; }
    if ($lab)        { $lab =~ s/\"//g;    $gene_class{$id}{lab}{$lab}++; }
    if ($genecount)  {                     $gene_class{$id}{genecount}{$genecount}++; }
    if ($conccount)  {                     $gene_class{$id}{conccount}{$conccount}++; }
    if ($clonecount) {                     $gene_class{$id}{clonecount}{$clonecount}++; }
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $infile : $!";
  foreach my $id (sort keys %gene_class) {
    next unless $id;
    foreach my $col (sort keys %{ $gene_class{$id} }) {
      my $tag = $gc_tag{$col};
      my $data = join", ", sort keys %{ $gene_class{$id}{$col} };
      my $stuff = "$tag: $data\n";
      $hash{geneclass}{$id}{$stuff}++;
    } # foreach my $col (sort keys %{ $gene_class{$id} })
  } # foreach my $id (sort keys %gene_class)
  
# transgenes now from transgene OA, not this file.  2010 09 28
#   $infile = $jo_path . 'transgene_summary.txt';
#   open (IN, "<$infile") or die "Cannot open $infile : $!";
# # my $junk = <IN>;	# no longer expecting a junk line
#   while (my $line = <IN>) {
#     chomp $line;
#     if ($line =~ m/\"(.*?)\"\t\"(WBPaper\d+)\"\t\"(.*?)\"/) {
#       my ($transgene, $paper, $summary) = $line =~ m/\"(.*?)\"\t\"(WBPaper\d+)\"\t\"(.*?)\"/;
#       $summary = 'summary: "' . $summary . '"' . "\n";
#       $hash{transgene}{$transgene}{$summary}++; }
#     elsif ($line =~ m/\"(.*?)\"/) { $hash{transgene}{$1}{blank}++; }
#   } # while (my $line = <IN>)
#   close (IN) or die "Cannot close $infile : $!";

  $infile = $jo_path . 'rearr_simple.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  # my $junk = <IN>;
  while (my $line = <IN>) {
    chomp $line;
    if ($line =~ m/^\"(.*?)\"\t\"(.*?)\"/) {
#     my ($allele, $gene, $pub) = $line =~ m/\"(.*?)\"\t\"(WBGene\d+)\"\t\"(.*?)\"/;
#       my ($rearrangement, $stuff) = $line =~ m/\"(.*?)\"\t\"(.*)\"/;	# this was getting bad names when no chromosome
      $line =~ s/\"//g;
      my ($rearrangement, @stuff) = split/\t/, $line; 
      my @gs; foreach (@stuff) { if ($_) { push @gs, $_; } } 
      my $stuff = join"\t", @stuff;	# get good stuff, not blanks
      $stuff = 'other: "' . $stuff . '"' . "\n";
      $hash{rearrangement}{$rearrangement}{$stuff}++; }
    elsif ($line =~ m/^\"(.*?)\"/) { $hash{rearrangement}{$1}{blank}++; }
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $infile : $!";

  $infile = $jo_path . 'clone_info.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  # my $junk = <IN>;
  while (my $line = <IN>) {
    chomp $line;
    if ($line =~ m/^\"(.*?)\"\t\"(.*?)\"/) {
      $line =~ s/\"//g;
      my ($clone, @stuff) = split/\t/, $line; 
      my @gs; foreach (@stuff) { if ($_) { push @gs, $_; } } 
      my $stuff = join"\t", @stuff;	# get good stuff, not blanks
      $stuff = 'other: "' . $stuff . '"' . "\n";
      $hash{clone}{$clone}{$stuff}++; }
    elsif ($line =~ m/^\"(.*?)\"/) { $hash{clone}{$1}{blank}++; }
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $infile : $!";

  $infile = $jo_path . 'strains.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  # my $junk = <IN>;
  while (my $line = <IN>) {
    chomp $line;
    if ($line =~ m/^\"(.*?)\"\t\"(.*?)\"/) {
      $line =~ s/\"//g;
      my ($strain, @stuff) = split/\t/, $line; 
      my @gs; foreach (@stuff) { if ($_) { push @gs, $_; } } 
      my $stuff = join"\t", @stuff;	# get good stuff, not blanks
      $stuff = 'other: "' . $stuff . '"' . "\n";
      $hash{strain}{$strain}{$stuff}++; }
    elsif ($line =~ m/^\"(.*?)\"/) { $hash{strain}{$1}{blank}++; }
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $infile : $!";

  $infile = $jo_path . 'expr_cluster.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) {
    chomp $line;
    my ($name, $description, $paper, $remark) = split/\t/, $line; 
    $name =~ s/^\"//; $name =~ s/\"$//;
    if ($description) { $description =~ s/^\"//; $description =~ s/\"$//; $hash{exprcluster}{$name}{"description: $description\n"}++; }
    if ($paper)       { $paper =~ s/^\"//;       $paper =~ s/\"$//;       $hash{exprcluster}{$name}{"paper: $paper\n"}++;             }
    if ($remark)      { $remark =~ s/^\"//;      $remark =~ s/\"$//;      $hash{exprcluster}{$name}{"remark: $remark\n"}++;           }
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $infile : $!";


  my @pgcommands;
  foreach my $type (sort keys %hash) {
#     next unless ($type eq 'exprcluster');		# to only populate a given set
    foreach my $object_id (sort keys %{ $hash{$type} }) {
      my $other_data = '';
      foreach my $odata (sort keys %{ $hash{$type}{$object_id} }) { unless ($odata eq 'blank') { $other_data .= "$odata"; } }
      my $name = $object_id;
      if ($var_data{$object_id}{name}) { $name = $var_data{$object_id}{name}; }
#       print OUT "[Term]\nid: $object_id\n";
      my $data = "id: $object_id\n";
      $name =~ s/\\/\\\\/g;			# \ need to be escaped in name for some reason
#       print OUT "name: \"$name\"\n";
      $data .= "name: \"$name\"\n";
      if ($var_data{$object_id}{dead}) { 
#         print OUT "dead: \"dead\"\n"; 
        $data .= "dead: \"dead\"\n"; }
      foreach my $type (%{ $hash{$object_id} }) {
        foreach my $line (sort keys %{ $hash{$object_id}{$type} }) {
          if ($line) {
#             print OUT "$type: \"$line\" []\n";
            $data .= "$type: \"$line\" []"; } } }
      $data .= $other_data;
      $data =~ s/\n$//;
#       print OUT "\n";
#       my $pgcommand = "INSERT INTO obo_name_app_$type VALUES ('$object_id', '$name', CURRENT_TIMESTAMP);";	# DELETE this when new OA is live (add "my" below)
#       push @pgcommands, $pgcommand;
      my $pgcommand = "INSERT INTO obo_name_$type VALUES ('$object_id', '$name', CURRENT_TIMESTAMP);";
      push @pgcommands, $pgcommand;
      if ($data =~ m/\'/) { $data =~ s/\'/''/g; }	# escape '
      if ($data =~ m/\\/) { 			# \ have to be escaped in E'' quote
          $data =~ s/\\/\\\\/g; 
          $data = "E'" . $data . "'"; }
        else { $data = "'" . $data . "'"; }
#       $pgcommand = "INSERT INTO obo_data_app_$type VALUES ('$object_id', $data, CURRENT_TIMESTAMP);";	# DELETE this when new OA is live
#       push @pgcommands, $pgcommand;
      $pgcommand = "INSERT INTO obo_data_$type VALUES ('$object_id', $data, CURRENT_TIMESTAMP);";
      push @pgcommands, $pgcommand;
    } # foreach my $object_id (sort keys %{ $hash{$type} })
  } # foreach my $type (sort keys %hash)
  
  if (scalar (@pgcommands > 1)) { 		# only wipe and repopulate if there's something to enter
    print "data parsed, writing to postgres<br /><br />\n";
    $dbh->do( "DELETE FROM obo_name_variation;" );
    $dbh->do( "DELETE FROM obo_data_variation;" );
    $dbh->do( "DELETE FROM obo_name_rearrangement;" );
    $dbh->do( "DELETE FROM obo_data_rearrangement;" );
    $dbh->do( "DELETE FROM obo_name_strain;" );
    $dbh->do( "DELETE FROM obo_data_strain;" );
    $dbh->do( "DELETE FROM obo_name_clone;" );
    $dbh->do( "DELETE FROM obo_data_clone;" );
    $dbh->do( "DELETE FROM obo_name_geneclass;" );
    $dbh->do( "DELETE FROM obo_data_geneclass;" );
    $dbh->do( "DELETE FROM obo_name_exprcluster;" );
    $dbh->do( "DELETE FROM obo_data_exprcluster;" );
    foreach my $pgcommand (@pgcommands) {
      print "$pgcommand<br />\n";		# 504 gateway time-out unless stuff is printing to webpage, it takes some 20 minutes and can't disable timeout in wget or LWP::UserAgent
      $dbh->do( $pgcommand );
    } # foreach my $pgcommand (@pgcommands)
  } # if (scalar (@pgcommands > 1))
#   close (OUT) or die "Cannot close $outfile : $!";

#   print "Thanks for updating the variation / rearrangement / transgene OA autocomplete data based on four files in $jo_path and $url<br />\n";
  print "Thanks for updating the variation / rearrangement OA autocomplete data based on four files in $jo_path and $url<br />\n";

  &printFooter();
} # sub OBSOLETEupdateVariationObo

