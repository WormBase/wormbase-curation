#!/usr/bin/perl 

# Form to submit Community Gene Concise Descriptions

# to get a pmid, then search for title
# http://www.ebi.ac.uk/europepmc/webservices/rest/search/format=xml&query=ext_id:23677347%20src:med
#
# http://wiki.wormbase.org/index.php/Specifications_for_a_Community_Annotation_Form
#
# modified allele.cgi and took parts from the OA.  javascript at 
# ~/public_html/javascript/community_gene_description.js
#
# free (not forced) autocomplete for genes and species.  PMIDs get mapped to titles from ebi and 
# show PMIDs and titles (for Kimberly).  2013 06 02
#
# some cosmetic changes, got rid of yui autocomplete skin for fields to line up, added pmid to wbpaper mappings,
# changed javascript for linebreak to space in textarea fields.  live on 2013 06 05
#
# added  yui json-min.js  to pass back automated / concise / guide  values for WormBase provided description.
# gene and species are now forced ontology values.  when a gene is chosen, concise > automated > no_match 
# description is queried from con_desctype + con_desctext and displayed.  2015 02 04
#
# copied to tazendra.  2015 05 04
#
# added sending confirmation email just to the user when saving data.  2015 05 19
#
# took out species.  to put it back also need to change javascript.  2015 05 21
#
# changed ip to come from header HTTP_X_REAL_IP if it exists.  2016 02 08




use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;
use Tie::IxHash;
use LWP::Simple;
use Net::Domain qw(hostname hostfqdn hostdomain);


my $hostfqdn = hostfqdn();

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $result;

my $saveDir = '/home/azurebrd/public_html/cgi-bin/forms/saves/concise/';


my $query = new CGI;

my %hash;			# data for form
my @fields = qw( load_ip load_time input_person termid_person submitter_email species gene concise_description pmids pmid_titles wb_description wb_description_guide contributed_by contributed_by_guide );

my %mandatory;
$mandatory{"input_person"}++;
$mandatory{"termid_person"}++;
$mandatory{"submitter_email"}++;
# $mandatory{"species"}++;
$mandatory{"gene"}++;
$mandatory{"concise_description"}++;
$mandatory{"pmids"}++;
  

my $title = 'Community Gene Description Submission Form';
my ($header, $footer) = &cshlNew($title);

# $header = "<html><head></head>";
# $footer = "";

# <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css" />	# this makes it look nicer, but messes with the alignment of the input field
my $extra_stuff = << "EndOfText";
<link rel="stylesheet" type="text/css" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" />
<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/fonts/fonts-min.css" />
<link rel="stylesheet" type="text/css" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/yui_edited_autocomplete.css" />
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/yahoo-dom-event/yahoo-dom-event.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/connection/connection-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/datasource/datasource-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/autocomplete/autocomplete-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/json/json-min.js"></script>
<script type="text/javascript" src="http://${hostfqdn}/~azurebrd/javascript/community_gene_description.js"></script>
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




# print "$header\n";		# make beginning of HTML page

my %pmidToWBPaper;		# key pmid digits, value wbpaper digits

&process();			# see if anything clicked
# print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'Submit') {                 &submit('submit');     }
  elsif ($action eq 'Preview') {             &submit('preview');    }
  elsif ($action eq 'Save for Later') {      &submit('save');       }
  elsif ($action eq 'Load') {                &load();               }
  elsif ($action eq 'autocompleteXHR') {     &autocompleteXHR();    }
  elsif ($action eq 'asyncWbdescription') {  &asyncWbdescription(); }
  elsif ($action eq 'pmidToTitle') {         &pmidToTitle();        }
  elsif ($action eq 'asyncTermInfo') {       &asyncTermInfo();      }
#   elsif ($action eq 'instructions') {      &instructions();       }		# no instructions in this form
  else { &frontPage(); }			# show form as appropriate
} # sub process

sub asyncTermInfo {
  print "Content-type: text/plain\n\n";
  (my $var, my $field)   = &getHtmlVar($query, 'field');
  ($var, my $termid)     = &getHtmlVar($query, 'termid');
  if ($field eq 'person') { &getAnyWBPersonTermInfo($termid); }
} # sub asyncTermInfo

sub getAnyWBPersonTermInfo {
  my ($userValue) = @_;
  my $person_id = $userValue; my $standard_name; my $to_print;
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
  print $to_print;
} # sub getAnyWBPersonTermInfo


sub frontPage {
  print "Content-type: text/html\n\n";
  print $header;
  unless ($hash{'termid_person'}) { ($hash{'termid_person'}, $hash{'input_person'}, $hash{'submitter_email'}) = &getUserByIp(); }
  &displayForm();
  print $footer;
} # sub frontPage

sub pmidToTitle {		# given user pmids + previously retrieved pmidTitles, get titles for new pmids not already in pmidTitles list, return new pmidTitles list. also remove from pmidTitles pmids that are not in the pmids list (from a user deletion)
  print "Content-type: text/html\n\n";
  my ($var, $pmids)      = &getHtmlVar($query, 'pmids');		# what user enter as pmids
  ($var, my $pmidTitles) = &getHtmlVar($query, 'pmidTitles');		# what the form has previously processed into PMID <pmid> : title
  my (@pmids) = $pmids =~ m/(\d+)/g; my %pmids; foreach (@pmids) { $pmids{$_}++; }	# pmids are any sets of digits
  my (@matches) = $pmidTitles =~ m/PMID (\d+) : /g;			# previous matches are in the format PMID <pmid> : 
  my @lines = split/PMID /, $pmidTitles;				# split into each <pmid> : <title>
  my $stillWantedPmidTitles = '';					# pmid+titles previously looked up for pmids that are still in the pmids field
  foreach my $line (@lines) { 
    my ($pmid, $title) = $line =~ m/^(\d+) : (.*)$/;			# get the pmid and title
    if ($pmids{$pmid}) { $stillWantedPmidTitles .= "PMID $pmid : $title\n"; }	# if it's still in the pmids list, add to data to display below new matches
  }

  foreach my $matches (@matches) { delete $pmids{$matches}; } 		# if already matched previously, remove from %pmids and don't look up in ebi 
  foreach my $pmid (sort keys %pmids) { 				# for each pmid that doesn't already have a title
    my $ebiData = get "http://www.ebi.ac.uk/europepmc/webservices/rest/search/format=xml&query=ext_id:" . $pmid . "%20src:med";		# get the ebi url
    my $title = 'no title found';					# default to having no title
    if ( $ebiData =~ m/<title>(.*?)<\/title>/sm) { $title = $1; }	# get the title from the xml
    print "PMID $pmid - $title\n"; }					# print the pmid and title in proper format
  print "$stillWantedPmidTitles\n";					# print at the bottom previous matches that are still wanted pmids in the pmids field 
# http://www.ebi.ac.uk/europepmc/webservices/rest/search/format=xml&query=ext_id:23677347%20src:med
} # sub pmidToTitle

sub asyncWbdescription {
  print "Content-type: text/plain\n\n";
#   my ($var, $words) = &getHtmlVar($query, 'query');
#   ($var, my $field) = &getHtmlVar($query, 'field');
#   if ($field eq 'Gene') { &autocompleteGene($words); }
#   elsif ($field eq 'Species') { &autocompleteSpecies($words); }
  my ($var, $wbgene) = &getHtmlVar($query, 'wbgene');
  my %hash; my $persons = 'noperson'; my $joinkeys;
#   $result = $dbh->prepare( "SELECT con_desctype.joinkey, con_desctype.con_desctype, con_desctext.con_desctext, con_person.con_person FROM con_desctype, con_desctext, con_person WHERE con_desctype.joinkey = con_desctext.joinkey AND con_desctype.joinkey = con_person.joinkey AND con_desctype.joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene = '$wbgene');" );
  $result = $dbh->prepare( "SELECT con_desctype.joinkey, con_desctype.con_desctype, con_desctext.con_desctext FROM con_desctype, con_desctext WHERE con_desctype.joinkey = con_desctext.joinkey AND con_desctype.joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene = '$wbgene');" );
  $result->execute();
  while ( my @row = $result->fetchrow() ) {
    $row[2] =~ s/\n/ /g; $row[2] =~ s/\s+/ /g;				# linebreaks mess with JSON, replace can cause extra spaces
    $hash{$row[1]} = $row[2];
  }
  $result = $dbh->prepare( "SELECT con_person.con_person FROM con_person WHERE con_person.joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene = '$wbgene');" ); $result->execute();
  while ( my @row = $result->fetchrow() ) { if ($row[0] =~ m/WBPerson(\d+)/g) { $joinkeys = $row[0]; $joinkeys =~ s/WBPerson/two/g; $joinkeys =~ s/"/'/g; } }
  if ($joinkeys) {
    my @persons;
    $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey IN ($joinkeys);" );
    $result->execute();
    while ( my @row = $result->fetchrow() ) {
      $row[0] =~ s/two/WBPerson/; push @persons, qq($row[2] ( $row[0] ) ); }
    if (scalar @persons > 0) { $persons = join"<br\/>\\n", @persons; }
  } # if ($joinkeys)
  my @jsonData;
  my $concise_guide        = 'Update/edit this description in the box below.';
  my $automated_guide      = 'Update/edit this description in the box below.<br/>This description was generated by scripts based on homology/orthology data and Gene Ontology annotations in WormBase.';
  my $contributed_by_guide = 'Worm community members who wrote/updated this description.';
  my $nomatch_guide   = 'This gene does not yet have a description';
  if ($hash{'Concise_description'}) {        push @jsonData, qq("Concise_description",   "$hash{'Concise_description'}",   "$concise_guide",   "$persons", "$contributed_by_guide");   }
    elsif ($hash{'Automated_description'}) { push @jsonData, qq("Automated_description", "$hash{'Automated_description'}", "$automated_guide", "$persons", "$contributed_by_guide");   }
    else                                   { push @jsonData, qq("No_match",              "&nbsp;",                         "$nomatch_guide",   "$persons", "$contributed_by_guide");   }
  my $jsonData = join",\n", @jsonData;
  print qq([\n$jsonData\n]\n);
#   print "FOUND $wbgene GENE\n";
} # sub asyncWbdescription

sub autocompleteXHR {
  print "Content-type: text/html\n\n";
  my ($var, $words) = &getHtmlVar($query, 'query');
  ($var, my $field) = &getHtmlVar($query, 'field');
  if ($field eq 'Gene') { &autocompleteGene($words); }
  elsif ($field eq 'Species') { &autocompleteSpecies($words); }
  elsif ($field eq 'person') { &autocompletePerson($words); }
} # sub autocompleteXHR

sub autocompleteGene {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $lcwords = lc($words);
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my @tables = qw( gin_locus gin_synonyms gin_seqname gin_wbgene );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBGene" . $row[0];
      if ($table eq 'gin_locus') { $matches{"$row[1] ( $id ) "}++; }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]';" ); $result2->execute();
        my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
        if ( ($table eq 'gin_synonyms')|| ($table eq 'gin_seqname') ) { $matches{"$row[1] ( $id ) \[$name\]"}++; }
        if ($table eq 'gin_wbgene') { $matches{"$name ( $id ) "}++; } }
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND LOWER($table) !~ '^$lcwords' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBGene" . $row[0];
      if ($table eq 'gin_locus') { $matches{"$row[1] ( $id ) "}++; }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) {
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]';" ); $result2->execute();
        my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
        if ( ($table eq 'gin_synonyms')|| ($table eq 'gin_seqname') ) { $matches{"$row[1] ( $id ) \[$name\]"}++; }
        if ($table eq 'gin_wbgene') { $matches{"$name ( $id ) "}++; } } }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more results exists, type more to narrow your search'); }
  my $matches = join"\n", keys %matches;
  print $matches;
} # sub autocompleteGene

sub autocompleteSpecies {
  my ($words) = @_;
  my $lcwords = lc($words);
  my @species;
  push @species, "Caenorhabditis elegans";
  push @species, "Caenorhabditis briggsae";
  push @species, "Pristionchus pacificus";
  push @species, "Brugia malayi";
  push @species, "Caenorhabditis brenneri";
  push @species, "Caenorhabditis japonica";
  push @species, "Caenorhabditis remanei";
  push @species, "Caenorhabditis sp. 3";
  push @species, "Panagrellus redivivus";
  push @species, "Cruznema tripartitum";
  foreach my $species (@species) { if ($species =~ m/$lcwords/i) { print "$species\n"; } }
} # sub autocompleteSpecies

sub autocompletePerson {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $lcwords = lc($words);
  my $limit       = $max_results + 1;
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my @tables = qw( two_standardname );
  foreach my $table (@tables) {
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );      # match by start of name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
#       my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++;
      $matches{"$row[2] ( $id ) "}++;
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid') ORDER BY $table LIMIT $limit;" );          # then match anywhere in the name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
#       my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++;
      $matches{"$row[2] ( $id ) "}++;
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$lcwords' AND joinkey NOT IN (SELECT joinkey FROM two_status WHERE two_status = 'Invalid' ORDER) BY joinkey LIMIT $limit;" );               # then match by WBPerson number
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $elementText = qq($row[2] <span style='font-size:.75em'>( $id )</span>);
#       my $matchData = qq({ "eltext": "$elementText", "name": "$row[2]", "id": "$id" }); $matches{$matchData}++;
      $matches{"$row[2] ( $id ) "}++;
    }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more results exists, type more to narrow your search'); }
  my $matches = join"\n", keys %matches;
  print $matches;
} # sub autocompletePerson

sub submit {
  my ($submit_flag) = @_;
  print "Content-type: text/html\n\n";
  print $header;
# $mandatory{"firstname"}++;

  my $var;
#   my ($standardname, $wbperson, $submitter_email, $species, $gene, $concise_description, $pmids, $pmid_titles) = ('', '', '', '', '', '', '', '');
#   ($var, $standardname)               = &getHtmlVar($query, 'input_person');	
#   ($var, $wbperson)                   = &getHtmlVar($query, 'termid_person');	
#   ($var, $submitter_email)            = &getHtmlVar($query, 'submitter_email');
#   ($var, $species)                    = &getHtmlVar($query, 'species');	
#   ($var, $gene)                       = &getHtmlVar($query, 'gene');	
#   ($var, $concise_description)        = &getHtmlVar($query, 'concise_description');	
#   ($var, $pmids)                      = &getHtmlVar($query, 'pmids');	
#   ($var, $pmid_titles)                = &getHtmlVar($query, 'pmid_titles');	
  my $user = 'community_gene_description_form';	# who sends mail
  my $email = 'ranjana@caltech.edu, vanauken@caltech.edu';	# to whom send mail 
#   my $email = 'ranjana@caltech.edu, closertothewake@gmail.com';	# to whom send mail 
#   my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
  my $subject = 'Community Gene Description';		# subject of mail
  my $body = '';			# body of mail

  my %fieldToLabel;
  $fieldToLabel{'input_person'}         = "Person";
  $fieldToLabel{'termid_person'}        = "WBPersonID";
  $fieldToLabel{'submitter_email'}      = "Email";
#   $fieldToLabel{'species'}              = "Species";
  $fieldToLabel{'gene'}                 = "Gene";
  $fieldToLabel{'concise_description'}  = "Gene Description";
  $fieldToLabel{'pmids'}                = "PMIDs";
  $fieldToLabel{'pmid_titles'}          = "PMIDs_to_titles";

  my $form_data = '<table cellpadding="6" cellspacing="1" border="1">';		# don't want error messages from later on
  foreach my $field (@fields) {
    (my $var, $hash{$field}) = &getHtmlVar($query, $field);	
    if ($hash{$field}) { 
      if ($fieldToLabel{$field}) {
        $form_data .= qq(<tr><td><span style="font-weight:bold">$fieldToLabel{$field}</span></td><td>$hash{$field}</td></tr>\n);
        $body      .= qq($fieldToLabel{$field} : $hash{$field}\n); } }
  }
  $form_data .= qq(</table><br/><br/>);
  &updateUserIp($hash{'termid_person'}, $hash{'submitter_email'});
  $email .= ", $hash{'submitter_email'}";
      
  if ($submit_flag eq 'submit') {
    my $mandatory_check = &checkMandatoryFields();
    if ($mandatory_check eq 'ok') {
      print qq(<span style="font-size: 14pt">Thank you for your submission, you should get a confirmation email.<br/><a href="community_gene_description.cgi">Go back to form</a></span><br/><br/>\n);
      print $form_data;
      my (@pmids) = $hash{'pmids'} =~ m/(\d+)/g;
      &populatePmidToWBPaper();
      my %pmid_no_wbpaper; my %wbpaper;
      foreach my $pmid (@pmids) { 
        if ($pmidToWBPaper{$pmid}) { 
            $body .= qq(PMID $pmid is WBPaper$pmidToWBPaper{$pmid}\n);
            $wbpaper{$pmidToWBPaper{$pmid}}++; }
          else {
            $pmid_no_wbpaper{$pmid}++;
            $body .= qq(No WBPaper for PMID $pmid\n); } }
      if (keys %wbpaper > 0) {         my $wbpapers     = join'","', sort keys %wbpaper;         $hash{paper} = $wbpapers;            }
      if (keys %pmid_no_wbpaper > 0) { my $pmidunmapped = join' | ', sort keys %pmid_no_wbpaper; $hash{pmidunmapped} = $pmidunmapped; }
      $body = "Thank-you for submitting your gene description to WormBase!\n\n" . $body;
      &mailer($user, $email, $subject, $body);			# email the data
      &deletePg($hash{'load_ip'}, $hash{'load_time'});		# delete saved entry from postgres
#       &writePgOa();						# ranjana + kimberly don't want to write to postgres 2015 05 04
    } else { 
      print $mandatory_check; 
      &getHashFromForm();
      unless ($hash{'termid_person'}) { ($hash{'termid_person'}, $hash{'input_person'}, $hash{'submitter_email'}) = &getUserByIp(); }
      &displayForm();
    }
  }
  elsif ($submit_flag eq 'preview') { 
    my $mandatory_check = &checkMandatoryFields();
    if ($mandatory_check eq 'ok') {
      print qq(<b>Preview</b> : <br/><br/>\n);
      print $form_data;
      print qq(<span style="font-size: 14pt; color: black;">If you would like to change your entries, use the form below, if not, click 'Submit' below the form, to submit your gene description.</span><br/><br/><br/>\n);
    } else { 
      print $mandatory_check; 
    }
    &getHashFromForm();
    unless ($hash{'termid_person'}) { ($hash{'termid_person'}, $hash{'input_person'}, $hash{'submitter_email'}) = &getUserByIp(); }
    &displayForm();
  }
  elsif ($submit_flag eq 'save') { 
    &deletePg($hash{'load_ip'}, $hash{'load_time'});		# delete previously saved entry from postgres
    &saveFormData();
  }

  print $footer;
} # sub submit

sub writePgOa {
#   my @fields = qw( load_ip load_time input_person termid_person submitter_email species gene concise_description pmids pmid_titles wb_description wb_description_guide contributed_by contributed_by_guide );
  my %fieldToPgTable;
  $fieldToPgTable{termid_person}       = 'con_person';
  $fieldToPgTable{submitter_email}     = 'con_email';
#   $fieldToPgTable{species}             = 'con_species';
  $fieldToPgTable{gene}                = 'con_wbgene';
  $fieldToPgTable{concise_description} = 'con_desctext';
  $fieldToPgTable{paper}               = 'con_paper';
  $fieldToPgTable{pmidunmapped}        = 'con_pmidunmapped';
  $fieldToPgTable{curator}             = 'con_curator';
  $fieldToPgTable{desctype}            = 'con_desctype';
  $fieldToPgTable{curhistory}          = 'con_curhistory';
  $fieldToPgTable{lastupdate}          = 'con_lastupdate';
  $fieldToPgTable{nodump}              = 'con_nodump';
  $fieldToPgTable{usersubmission}      = 'con_usersubmission';
  $fieldToPgTable{needsreview}         = 'con_needsreview';
  my %multiFields;
  $multiFields{paper}                  = 'multiontology';
  $multiFields{termid_person}          = 'multiontology';
  my $pgid = &getHighestPgid(); $pgid++;
  my $date = &getPgDate();
  $hash{lastupdate}                    = $date;
  $hash{desctype}                      = 'Concise_description';
  $hash{curator}                       = 'WBPerson324';
  $hash{curhistory}                    = $pgid;
  $hash{nodump}                        = 'NO DUMP';
  $hash{usersubmission}                = 'User Submission';
  $hash{needsreview}                   = 'Needs Review';
  my @pgcommands;
  foreach my $field (sort keys %fieldToPgTable) {
    my $pgtable = $fieldToPgTable{$field};
    my $data    = $hash{$field};
    next unless ($data);
    if ($field eq 'gene') {     ($data) = $data =~ m/(WBGene\d+)/; }
    if ($multiFields{$field}) {  $data  = '"' . $data . '"';       }
    push @pgcommands, qq(INSERT INTO $pgtable VALUES ('$pgid', '$data'););
    push @pgcommands, qq(INSERT INTO ${pgtable}_hst VALUES ('$pgid', '$data'););
#     print "FIELD $field PG $pgtable PGID $pgid DATA $data<br/>\n";
  }
  foreach my $pgcommand (@pgcommands) {
#     print qq(PG $pgcommand PG<br/>\n);
# UNCOMMENT TO POPULATE
#     $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
} # sub writePgOa

sub getHighestPgid {                                    # get the highest joinkey from the primary tables
  my @highestPgidTables = qw( wbgene curator desctype ); my $datatype = 'con';
  my $pgUnionQuery = "SELECT MAX(joinkey::integer) FROM ${datatype}_" . join" UNION SELECT MAX(joinkey::integer) FROM ${datatype}_", @highestPgidTables;
  my $result = $dbh->prepare( "SELECT max(max) FROM ( $pgUnionQuery ) AS max; " );
  $result->execute(); my @row = $result->fetchrow(); my $highest = $row[0];
  return $highest;
} # sub getHighestPgid



sub deletePg {
  my ($user_ip, $time) = @_;
  my $pgcommand = qq(DELETE FROM frm_user_save WHERE frm_user_ip = '$user_ip' AND frm_time = '$time');
#   print qq($pgcommand<br/>\n);
  $dbh->do( $pgcommand );
} # sub deletePg

# CREATE TABLE frm_user_save (
#     frm_user_ip text,
#     frm_time integer,
#     frm_datatype text,
#     frm_field text,
#     frm_data text,
#     frm_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone
# );

sub saveFormData {
  my %hash;
  my $time = time;
#   my $ip   = $query->remote_host();
  my $ip = &getIp();
#   my $saveDir = '/home/azurebrd/public_html/cgi-bin/forms/saves/concise/';
#   my $filename = $ip . '-' . $time;		# use time for unique saves later
  my $filename = $ip;
  my $datatype = 'concise';
#   my $saveFile = $saveDir . $filename;
#   print qq($saveFile<br/>);
#   open (OUT, ">$saveFile") or die "Cannot create $saveFile : $!";
  my @pgcommands;
  foreach my $field (@fields) {
    (my $var, $hash{$field})               = &getHtmlVar($query, $field);	
    if ($hash{$field}) {
      push @pgcommands, qq(INSERT INTO frm_user_save VALUES ('$ip', '$time', '$datatype', '$field', '$hash{$field}'));
#       $hash{$field} =~ s/\n/LINEBREAK/g;
#       print OUT qq($field\t$hash{$field}\n);
    } # if ($hash{$field})
  } # foreach my $field (@fields)
#   close (OUT) or die "Cannot close $saveFile : $!";
  foreach my $pgcommand (@pgcommands) {
#     print qq($pgcommand<br/>\n);
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
  my $saveUrl = 'http://' . $hostfqdn . "/~azurebrd/cgi-bin/forms/community_gene_description.cgi?action=Load&user_ip=$ip&time=$time";

  print qq(<span style="font-size: 14pt">Please use this <a href="$saveUrl">link</a> to continue the submission.</span><br/>\n);
  if ($hash{'submitter_email'}) {
    print qq(<span style="font-size: 14pt">This <a href="$saveUrl">link</a> has also been emailed to you, if you would like to continue at a later date.</span><br/>\n);
    my $email   = $hash{'submitter_email'};
    my $user    = 'community_gene_description_form';	# who sends mail
    my $subject = 'Link for WormBase Community Gene Description form';
    my $gene    = 'no gene chosen';     if ($hash{'gene'})    { $gene    = $hash{'gene'};    $gene =~ s/\s+$//; }	# strip trailing space from ontology
#     my $species = 'no species chosen';  if ($hash{'species'}) { $species = $hash{'species'};                    }
    my $date    = &getPgDate();
    my $body    = qq(Please continue your submission through the WormBase Community Gene Description form, for $gene, saved on $date, with this link: $saveUrl\n\nThank-you\nWormBase);
    &mailer($user, $email, $subject, $body);			# email the data
  }
} # sub saveFormData

sub getHashFromPg {
  my $datatype = 'concise';
  my ($var, $ip)                  = &getHtmlVar($query, 'user_ip');	
  ($var, my $time)                = &getHtmlVar($query, 'time');	
  my $saveUrl = "community_gene_description.cgi?action=Load&user_ip=$ip&time=$time";
  print qq(Loading data from <a href="$saveUrl">link</a><br/><br/>\n);
  $result = $dbh->prepare( "SELECT frm_field, frm_data FROM frm_user_save WHERE frm_user_ip = '$ip' AND frm_time = '$time' AND frm_datatype = '$datatype';" );
  $result->execute();
  my $foundSomething = 0;
  while ( my @row = $result->fetchrow() ) { $hash{$row[0]} = $row[1]; $foundSomething++; }
  if ($foundSomething) { $hash{'load_ip'} = $ip; $hash{'load_time'} = $time; }
    else { print qq(There was no data for your link, you may have already submitted it, or have an error in the link.<br/><br/>); }
} # sub getHashFromPg

sub load {
  print "Content-type: text/html\n\n";
  print $header;
  &getHashFromPg();
  &displayForm();
  print $footer;
} # sub load

sub checkMandatoryFields {
  my $mandatoryFail = '';
  foreach my $field (sort keys %mandatory) {
    my ($var, $value)                  = &getHtmlVar($query, $field);	
    unless ($value) { $mandatoryFail .= "$field "; } }
  if ($mandatoryFail) { 
      return qq(<b><font size="+2" color="red">You failed to enter data in mandatory fields : $mandatoryFail</font></b><br/>\n); }
    else { return 'ok'; }
} # sub checkMandatoryFields

sub populatePmidToWBPaper {
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid';" );
  $result->execute();
  while ( my @row = $result->fetchrow() ) { my ($num) = $row[1] =~ m/(\d+)/; $pmidToWBPaper{$num} = $row[0]; }
} # sub populatePmidToWBPaper


sub updateUserIp {
  my ($wbperson, $submitter_email) = @_;
#   my $ip = $query->remote_host();
  my $ip = &getIp();
  my $twonum = $wbperson; $twonum =~ s/WBPerson/two/;
  $result = $dbh->prepare( "SELECT * FROM two_user_ip WHERE two_user_ip = '$ip';" );
  $result->execute;
  my @row = $result->fetchrow;
  unless ($row[0]) {
    $result = $dbh->do( "DELETE FROM two_user_ip WHERE two_user_ip = '$ip' ;" );
    $result = $dbh->do( "INSERT INTO two_user_ip VALUES ('$twonum', '$ip', '$submitter_email')" ); }
}

sub getIp {
  my $ip            = $query->remote_host();                    # get value for current user IP, not (potentially) loaded IP
  my %headers = map { $_ => $query->http($_) } $query->http();
  if ($headers{HTTP_X_REAL_IP}) { $ip = $headers{HTTP_X_REAL_IP}; }
  return $ip;
} # sub getIp

sub getUserByIp {
#   my $ip = $query->remote_host();
  my $ip = &getIp();
  my $twonum = ''; my $standardname = ''; my $email = ''; my $wbperson = '';
  $result = $dbh->prepare( "SELECT * FROM two_user_ip WHERE two_user_ip = '$ip';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[0]) { $twonum = $row[0]; $email = $row[2]; $wbperson = $row[0]; $wbperson =~ s/two/WBPerson/; }
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$twonum';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[2]) { $standardname = $row[2]; }
  return ($wbperson, $standardname, $email);
} # sub getUserByIp

sub getHashFromForm {
  foreach my $field (@fields) {
    (my $var, $hash{$field})               = &getHtmlVar($query, $field);	
  } # foreach my $field (@fields)
  unless ($hash{'wb_description'})        { $hash{'wb_description'}       = '&nbsp;';                      }	# need to have something in the div for vertical borders
  unless ($hash{'wb_description_guide'})  { $hash{'wb_description_guide'} = 'Select a gene to load data.'; }
  unless ($hash{'contributed_by_guide'})  { 
    if ($hash{'contributed_by'}) {
      $hash{'contributed_by_guide'} = 'Worm community members who wrote/updated this description.'; } }
  unless ($hash{'contributed_by'})        { $hash{'contributed_by'}       = '';                      }	
} # sub getHashFromForm

sub displayForm {			# show form as appropriate

#   my ($standardname, $wbperson, $submitter_email, $species, $gene, $concise_description, $pmids, $pmid_titles, $wb_description, $wb_description_guide, $contributed_by, $contributed_by_guide) = ('', '', '', '', '', '', '', '', '', '', '', '');
# 
# #   ($var, $firstname)                  = &getHtmlVar($query, 'firstname');	
# #   ($var, $lastname)                   = &getHtmlVar($query, 'lastname');	
#   ($var, $standardname)               = &getHtmlVar($query, 'input_person');	
#   ($var, $wbperson)                   = &getHtmlVar($query, 'termid_person');	
#   ($var, $submitter_email)            = &getHtmlVar($query, 'submitter_email');
#   ($var, $species)                    = &getHtmlVar($query, 'species');	
#   ($var, $gene)                       = &getHtmlVar($query, 'gene');	
#   ($var, $concise_description)        = &getHtmlVar($query, 'concise_description');	
#   ($var, $pmids)                      = &getHtmlVar($query, 'pmids');	
#   ($var, $pmid_titles)                = &getHtmlVar($query, 'pmid_titles');	
#   ($var, $wb_description)             = &getHtmlVar($query, 'wb_description');	
#   ($var, $wb_description_guide)       = &getHtmlVar($query, 'wb_description_guide');	
#   unless ($wb_description)            { $wb_description       = '&nbsp;';                      }	# need to have something in the div for vertical borders
#   unless ($wb_description_guide)      { $wb_description_guide = 'Select a gene to load data.'; }
#   ($var, $contributed_by)             = &getHtmlVar($query, 'contributed_by');	
#   ($var, $contributed_by_guide)       = &getHtmlVar($query, 'contributed_by_guide');	
#   unless ($contributed_by)            { $contributed_by       = '&nbsp;';                      }	# need to have something in the div for vertical borders
#   unless ($contributed_by_guide)      { $contributed_by_guide = 'WormBase users who contributed to this description.'; }
# 
#   unless ($wbperson) {
#     ($wbperson, $standardname, $submitter_email) = &getUserByIp();
#   } # unless ($wbperson)


#   <TR>
#     <TD ALIGN="right"><FONT COLOR='black'><B>Enter your first name</FONT> :</B> <BR></TD>
#     <TD><input Type="Text" ID="firstname" Name="firstname" value="$firstname" Size="50"></TD>
#     <!--<TD><font size="1">(Please enter full name, eg. Sulston, John)</font></TD>-->
#   </TR>
#   <TR>
#     <TD ALIGN="right"><FONT COLOR='black'><B>Enter your last name</FONT> :</B> <BR></TD>
#     <TD><input Type="Text" ID="lastname" Name="lastname" value="$lastname" Size="50"></TD>
#     <!--<TD><font size="1">(Please enter full name, eg. Sulston, John)</font></TD>-->
#   </TR>
  print << "EndOfText";
<body class="yui-skin-sam">

<A NAME="form"><H1>Community Gene Description Submission Form :</H1></A><br/><br/>
<!--Please enter as much information as possible. Email <A HREF="mailto:genenames\@wormbase.org">genenames\@wormbase.org</A> for any questions/problems.<br />-->
<b><font size="+2">All fields with a <span style="color: red;">*</span> are required</font></b>

<form method="post" action="community_gene_description.cgi">
 <div id="term_info_box" style="display: none; border: solid; position: fixed; top: 120px; right: 20px; width: 350px; z-index:2; background-color: white;"><div id="term_info" style="margin: 5px 5px 5px 5px;">Term Information</div></div>

 <input type="hidden" name="load_ip" id="load_ip" value="$hash{'load_ip'}"></input>
 <input type="hidden" name="load_time" id="load_time" value="$hash{'load_time'}"></input>

 <!--<table border="1" width="100%" height="100%" align="center" cellpadding="1" cellspacing="1">-->
 <table border="0" align="center" cellpadding="5" cellspacing="1" style="max-width: 1040px; width: 1040px;">
  <tr>
    <td colspan="1" style="width: 270px; max-width: 270px; min-width: 270px;"><!--<table border="0" width="100%" align="center" cellpadding="6" cellspacing="1">-->
    </td>
    <td style="max-width: 444px; width: 444px;">&nbsp;</td>
    <td  style="width: 350px; max-width: 350px; min-width: 350px;">&nbsp;</td>
    <!--<td width="34%"><FONT SIZE=+2><B>REQUIRED</B></FONT></td>
    <td width="28%">&nbsp;</td>
    <td width="38%">&nbsp;</td>-->
<!--    <td >&nbsp;</td>
    <td >&nbsp;</td>-->
  </tr>

  <TR>
    <TD valign="center" align="right" colspan="1"><B>Your name <span style="color: red;">*</span></B></TD>
    <td valign="center">
      <span id="containerForcedpersonAutoComplete">
        <div id="forcedpersonAutoComplete">
              <input size="50" name="input_person" id="input_person" type="text" value="$hash{'input_person'}" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" onBlur="if (document.getElementById('input_person').value === '') { document.getElementById('termid_person').value = ''; }">
              <div id="forcedpersonContainer"></div>
        </div></span></td>
    <td align="left" colspan="1"><font size="2" color="#3B3B3B">Start typing in your name and choose from the drop-down.</font></td>
  </TR>
  <TR>
    <TD ALIGN="right"><FONT COLOR='black'><B>WBPerson ID</FONT></B> <BR></TD>
    <TD><input Type="Text" ID="termid_person" Name="termid_person" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'termid_person'}" Size="50" readonly="readonly"></TD>
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='black'><B>Your e-mail address</FONT> <span style="color: red;">*</span></B> <BR></TD>
    <TD><input Type="Text" Name="submitter_email" Size="50" Maxlength="50" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'submitter_email'}"></TD>
  </TR>
<!--
  <tr> 
    <TD valign="center" align="right"><FONT COLOR='black'><B>Choose a species</FONT> :</B></td>
    <td valign="center">
      <span id="containerForcedSpeciesAutoComplete">
        <div id="forcedSpeciesAutoComplete">
              <input size="50" name="species" id="input_Species" type="text" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'species'}">
              <div id="forcedSpeciesContainer"></div>
        </div></span></td>
    <TD><font size="2" color="#3B3B3B">Start typing in the name of a species and choose from the drop-down.</font></TD>
  </tr>-->
  <tr>
    <TD valign="center" align="right"><B>Choose a gene <span style="color: red;">*</span></B></TD>
    <td valign="center">
      <span id="containerForcedGeneAutoComplete">
        <div id="forcedGeneAutoComplete">
              <input size="50" name="gene" id="input_Gene" type="text" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'gene'}">
              <div id="forcedGeneContainer"></div>
        </div></span></td>
    <td><font size="2" color="#3B3B3B">Start typing in a gene and choose from the drop-down.</font></td>
  </tr>
  <tr> 
    <TD valign="center" align="right"><B><font color="black">WormBase provided description</font></B></TD>
    <TD valign="center" align="left" style="width: 0px;">
       <input type="hidden" name="wb_description" id="wbDescription" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'wb_description'}"></input>
       <div id="wbDescriptionDiv" style="border: 1px solid #D4D4CA; padding: 5px; background-color: #E1F1FF;">$hash{'wb_description'}</div></TD>
    <TD valign="center" align="left"><font size="2" color="#3B3B3B"><span id="wbDescriptionGuideSpan">$hash{'wb_description_guide'}</span></font><input type="hidden" name="wb_description_guide" id="wbDescriptionGuide" value="$hash{'wb_description_guide'}"></input></TD>
  </tr>
  <tr> 
    <TD valign="center" align="right"><B><font color="black">Previously contributed by</font></B></TD>
    <TD valign="center" align="left" style="width: 0px;">
       <input type="hidden" name="contributed_by" id="contributedBy" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'contributed_by'}"></input>
       <div id="contributedByDiv" style="border: 1px solid #D4D4CA; padding: 5px; background-color: #E1F1FF;">$hash{'contributed_by'}</div></TD>
    <TD valign="center" align="left"><font size="2" color="#3B3B3B"><span id="contributedByGuideSpan">$hash{'contributed_by_guide'}</span></font><input type="hidden" name="contributed_by_guide" id="contributedByGuide" style="max-width: 444px; width: 99%; background-color: #E1F1FF;" value="$hash{'contributed_by_guide'}"></input></TD>
  </tr>
  <tr> 
    <TD ALIGN="right"><B>New gene description <span style="color: red;">*</span></B></font></td>
    <td colspan="1"><textarea id="concisedescription" name="concise_description" rows="10" cols="100" style="max-width: 444px; width: 99%; background-color: #E1F1FF;">$hash{'concise_description'}</textarea></td>
    <TD><font size="2" color="#3B3B3B">Edit the description in this box, or write a new description.<br/>Guidelines on what to include are <span style="font-weight: bold; text-decoration: underline;"><a href="http://wiki.wormbase.org/index.php/How_WormBase_writes_a_concise_description" target="new">here</a></span>.</font></TD>
  </tr>

  <tr> 
    <TD ALIGN="right"><B>PubMed identifier of a paper reference <span style="color: red;">*</span></B></td>
    <td colspan="1"><textarea name="pmids" id="pmids" rows="5" cols="100" style="max-width: 444px; width: 99%; background-color: #E1F1FF;">$hash{'pmids'}</textarea></td>
    <TD><font size="2" color="#3B3B3B">Enter a single PubMed identifier per line (e.g., PMID:4366476 or 4366476).<br/>Title/s of the paper/s entered will appear below.<br/>WormBase will not accept abstracts, Worm Breeder's Gazette articles, or personal communications as references.</font></TD>
  </tr>
  <tr> 
    <TD ALIGN="right"><B><font color="black">Display of PubMed titles found</B></font></td>
    <td colspan="1"><textarea name="pmid_titles" id="pmidTitles" rows="10" cols="100" readonly="readonly" style="max-width: 444px; width: 99%; background-color: #E1F1FF;">$hash{'pmid_titles'}</textarea></td>
  </tr>

  <tr><td></td></tr>
  <tr><td></td></tr>
  <tr><td></td>
  <td align="left" colspan="2"><b>Clicking Submit will email you a confirmation :</b>
   <input type="submit" name="action" style="background: #E1F1FF;" value="Save for Later" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
   <input type="submit" name="action" style="background: #E1F1FF;" value="Preview" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
   <input type="submit" name="action" style="background: #E1F1FF;" value="Submit" >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  </td>
  </tr>
 </table>
</form>

</body>
</html>

EndOfText
#    <!--<input name="reset" type="reset" value="Reset" onClick="rollback()">-->
# <!--
# <hr>
# <a href="mailto:webmaster\@www.wormbase.org">webmaster\@www.wormbase.org</a><a href="http://www.wormbase.org/copyright.html">&nbsp;&nbsp;&nbsp;Copyright
#     Statement</a><a href="http://www.wormbase.org/db/misc/feedback">&nbsp;&nbsp;&nbsp;Send comments or questions to WormBase</a></td> <td class="small" align="right"><a href="http://www.wormbase.org/privacy.html">&nbsp;&nbsp;&nbsp;Privacy Statement</a></td></tr>-->
} # sub displayForm


__END__

CREATE TABLE frm_user_save (
    frm_user_ip text,
    frm_time integer,
    frm_datatype text,
    frm_field text,
    frm_data text,
    frm_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone
);

