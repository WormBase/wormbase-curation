#!/usr/bin/perl

# Track community curation
#
# * PDF links
# * WBPaper ID
# * PubMed ID (WBPaper00001435 is the only example I could find that has two PMIDs and either, or both, is fine)
# * First author Name (if available)
# * First Author WBPerson ID (if available)
# * First Author Email (if available)
# * Corresponding Author(s) Name (pending a new method, yes)
# * Corresponding Author(s) WBPerson ID (pending a new method, yes)
# * Corresponding Author(s) Email(s) (pending a new method, yes)
# * Date e-mailed for allele-phenotype (if at all) (eventually automated by standardized e-mail, but for now could use the "E-mail Sent" button on the filter page, as I mentioned above)
# * E-mail response, free text, manually entered
# * Form response (timestamp or yes/no), automated, meaning someone has made an entry in the Allele-Phenotype form for this paper (could check Phenotype OA for entry for that paper where curator is "Community Curator")
# * Remark, free text
#
# http://wiki.wormbase.org/index.php/Contacting_the_Community

# com_app_emailsent 
# com_app_emailresponse 
# com_app_remark 
# com_app_skip

# Live at some point by 2015 11 20 
# 
# Added skip tables, and looking at  pap_author_corresponding  for Chris and Ranjana.  2015 12 07
#
# new mutant tracker separate column for rnai.  2016 01 19
#
# changed links to www.wormbase.org/submissions  2016 02 10
#
# tracker should map email addresses to WBPerson IDs for Chris.  2016 02 18
#
# emails for newmutant link to phenotype form with pgid field.  2016 02 21
#
# changed newmutant email a bit for Chris.  2016 03 01
#
# changed recent-ness interval to 1 month for Chris.  2016 05 20
#
# skip papers that have been recently emailed to corresponding authors.
# This was an oversight, should have been happening already.  2016 08 22
#
# remove papers that have been curated for RNAi for Chris.  2016 08 23
#
# No longer require papers to have been AFPed first, nor filter out emails that have been AFPed in the last month.
# No longer look at corresponding author data.  If there's a first author, just email the first author.  2017 07 31



use strict;
use CGI;
use Jex;		# printHeader printFooter getHtmlVar getDate getSimpleDate mailer
use LWP::UserAgent;	# getting sanger files for querying
use LWP::Simple;	# get the PhenOnt.obo from a cgi
use DBI;
use Email::Send;
use Email::Send::Gmail;
use Email::Simple::Creator;
use Tie::IxHash;


my %curator;

my $query = new CGI;	# new CGI form
my $result;
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
# my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb;host=131.215.52.76", "", "") or die "Cannot connect to database!\n";

  print <<"EndOfText";
Content-type: text/html\n\n

<HTML>
<HEAD>
<LINK rel="stylesheet" type="text/css" href="http://minerva.caltech.edu/~azurebrd/stylesheets/wormbase.css">
<title>Community Curation Tracker</title>
  <script type="text/javascript" src="js/jquery-1.9.1.min.js"></script>
  <script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
  <script type="text/javascript">\$(document).ready(function() { \$("#sortabletable").tablesorter(); } );</script>
</HEAD>

<BODY bgcolor=#aaaaaa text=#000000 link=cccccc alink=eeeeee vlink=bbbbbb>
<HR>
</body></html>

EndOfText


# &printHeader('Community Curation Tracker');
&process();
&printFooter();

sub process {
  my ($var, $action) = &getHtmlVar($query, 'action');
  unless ($action) { $action = ''; }
  if ($action eq '') { &printHtmlMenu(); }		# Display form, first time, no action
  else { 						# Form Button
    print qq(ACTION : $action : ACTION <a href="community_curation_tracker.cgi">start over</a><br/>\n); 
    if ($action eq 'New Mutant Ready') {                 &readyToGo('app'); }
      if ($action eq 'New Mutant Tracker') {             &tracker('app');   }
      elsif ($action eq 'Concise Description Ready') {   &readyToGo('con');   }	
      elsif ($action eq 'Concise Description Tracker') { &tracker('con');     }	
      elsif ($action eq 'generate email') {              &generateEmail();      }
      elsif ($action eq 'skip paper') {                  &skipPaper();      }
      elsif ($action eq 'send email') {                  &sendEmail();          }
      elsif ($action eq 'ajaxUpdate') {                  &ajaxUpdate();         }
    print "ACTION : $action : ACTION<BR>\n"; 
  } # else # if ($action eq '') { &printHtmlForm(); }
} # sub process

sub ajaxUpdate {				# update field's pgtable data
  my ($var, $papid)          = &getHtmlVar($query, 'papid');
  ($var, my $datatype)       = &getHtmlVar($query, 'datatype');
  ($var, my $field)          = &getHtmlVar($query, 'field');
  ($var, my $value)          = &getHtmlVar($query, 'value');
  $value =~ s/\'/''/g;
  my @pgcommands;
  push @pgcommands, qq(DELETE FROM com_${datatype}_${field} WHERE joinkey = '$papid';);
  push @pgcommands, qq(INSERT INTO com_${datatype}_${field} VALUES ( '$papid', '$value'););
  push @pgcommands, qq(INSERT INTO com_${datatype}_${field}_hst VALUES ( '$papid', '$value'););
  foreach my $pgcommand (@pgcommands) {
#     print qq($pgcommand<br/>);
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
} # sub ajaxUpdate

sub sendEmail {
  my ($var, $papid)          = &getHtmlVar($query, 'papid');
  ($var, my $emailaddress)   = &getHtmlVar($query, 'email');
  ($var, my $subject)        = &getHtmlVar($query, 'subject');
  ($var, my $body)           = &getHtmlVar($query, 'body');
  ($var, my $datatype)       = &getHtmlVar($query, 'datatype');
  my $sender = 'outreach@wormbase.org';
  my $replyto = 'curation@wormbase.org';
  print qq(send email to $emailaddress<br/>from $sender<br/>replyto $replyto<br/>subject $subject<br/>body $body<br/>);
  my $email = Email::Simple->create(
    header => [
        From       => 'outreach@wormbase.org',
        'Reply-to' => 'curation@wormbase.org',
        To         => "$emailaddress",
        Subject    => "$subject",
    ],
    body => "$body",
  );

  my $passfile = '/home/postgres/insecure/outreachwormbase';
  open (IN, "<$passfile") or die "Cannot open $passfile : $!";
  my $password = <IN>; chomp $password;
  close (IN) or die "Cannot close $passfile : $!";
  my $sender = Email::Send->new(
    {   mailer      => 'Gmail',
        mailer_args => [
           username => 'outreach@wormbase.org',
           password => "$password",
        ]
    }
  );
  eval { $sender->send($email) };
  die "Error sending email: $@" if $@;
  my @pgcommands;
  push @pgcommands, qq(DELETE FROM com_${datatype}_emailsent WHERE joinkey = '$papid';);
  push @pgcommands, qq(INSERT INTO com_${datatype}_emailsent VALUES ( '$papid', '$emailaddress'););
  push @pgcommands, qq(INSERT INTO com_${datatype}_emailsent_hst VALUES ( '$papid', '$emailaddress'););
  foreach my $pgcommand (@pgcommands) {
#     print qq($pgcommand<br/>);
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
  print qq(<a href="community_curation_tracker.cgi">back to start</a><br/>);
} # sub sendEmail

#     print qq(<input type="hidden" name="papid"    value="$pap" />\n);
#     print qq(<input type="hidden" name="pmids"    value="$pmids" />\n);
#     print qq(<input type="hidden" name="aidname"  value="$aids{$aid}{name}"/>\n);
#     print qq(<input type="hidden" name="anames"   value="$personName"/>\n);
#     print qq(<input type="hidden" name="atwos"    value="$person"/>\n);
#     print qq(<input type="hidden" name="aemails"  value="$emails"/>\n);
#     print qq(<input type="hidden" name="cnames"   value="$cName"/>\n);
#     print qq(<input type="hidden" name="ctwos"    value="$cTwo"/>\n);
#     print qq(<input type="hidden" name="cemails"  value="$cEmail"/>\n);
#     print qq(<input type="hidden" name="pnames"   value="$pName"/>\n);
#     print qq(<input type="hidden" name="ptwos"    value="$pTwo"/>\n);
#     print qq(<input type="hidden" name="pemails"  value="$pEmail"/>\n);
#     print qq(<input type="hidden" name="pdfs"     value="$pdfs"/>\n);
#     print qq(<input type="hidden" name="datatype" value="app"/>\n);
# 
# 
#     my $submit = '';
#     if ( ($pmids) && ($emails || $cEmail) ) { $submit = qq(<input type="submit" name="action" value="generate email">\n); }
# #     print qq(<tr><td>$submit</td><td>WBPaper$pap\t</td><td>$pmids</td><td>$aids{$aid}{name}\t</td><td>$personName\t</td><td>$person\t</td><td>$emails\t</td><td>$cName</td><td>$cTwo</td><td>$cEmail</td><td>$pdfs</td></tr>\n); 

sub skipPaper {
  my ($var, $papid    ) = &getHtmlVar($query, 'papid');
  ($var, my $datatype ) = &getHtmlVar($query, 'datatype');
  my @pgcommands;
  push @pgcommands, qq(DELETE FROM com_${datatype}_skip WHERE joinkey = '$papid';);
  push @pgcommands, qq(INSERT INTO com_${datatype}_skip VALUES ( '$papid', 'skip'););
  push @pgcommands, qq(INSERT INTO com_${datatype}_skip_hst VALUES ( '$papid', 'skip'););
  foreach my $pgcommand (@pgcommands) {
#     print qq($pgcommand<br/>);
    $dbh->do( $pgcommand );
  } # foreach my $pgcommand (@pgcommands)
  &tracker($datatype);  
} 

sub generateEmail {
  my ($var, $papid      ) = &getHtmlVar($query, 'papid');
  ($var, my $pmids      ) = &getHtmlVar($query, 'pmids');
  ($var, my $aidname    ) = &getHtmlVar($query, 'aidname');
  ($var, my $anames     ) = &getHtmlVar($query, 'anames');
  ($var, my $atwos      ) = &getHtmlVar($query, 'atwos');
  ($var, my $aemails    ) = &getHtmlVar($query, 'aemails');
  ($var, my $cnames     ) = &getHtmlVar($query, 'cnames');
  ($var, my $ctwos      ) = &getHtmlVar($query, 'ctwos');
  ($var, my $cemails    ) = &getHtmlVar($query, 'cemails');
  ($var, my $afpnames   ) = &getHtmlVar($query, 'afpnames');
  ($var, my $afptwos    ) = &getHtmlVar($query, 'afptwos');
  ($var, my $afpemails  ) = &getHtmlVar($query, 'afpemails');
  ($var, my $pdfnames   ) = &getHtmlVar($query, 'pdfnames');
  ($var, my $pdftwos    ) = &getHtmlVar($query, 'pdftwos');
  ($var, my $pdfemails  ) = &getHtmlVar($query, 'pdfemails');
  ($var, my $pdfs       ) = &getHtmlVar($query, 'pdfs');
  ($var, my $genes      ) = &getHtmlVar($query, 'genes');
  ($var, my $datatype   ) = &getHtmlVar($query, 'datatype');
#   ($var, my $aggemails) = &getHtmlVar($query, 'aggemails');
# print qq(DT $datatype EM $aemails CE $cemails E<br>);
  my (@pmids) = $pmids =~ m/(\d+)/g;
  my @sorted_pmids = sort {$b<=>$a} @pmids;
  my $pmid = shift @sorted_pmids;
  print qq(<form method="post" action="community_curation_tracker.cgi"\n>);
  print qq(<input type="hidden" name="papid"   value="$papid" />\n);

  print qq(<table style="border-style: none;" border="1">);
#   print qq(<tr><td>WBPaper</td><td>pmids</td><td>first author initials</td><td>first author's person name</td><td>first author's person id</td><td>first author's person emails</td><td>corresponding author name</td><td>corresponding person</td><td>corresponding email</td><td>pdf author name</td><td>pdf person</td><td>pdf email</td><td>pdfs</td></tr>\n); 
  my $row = qq(<tr><td>WBPaper$papid\t</td><td>$pmids</td><td>$pdfs</td><td>$aidname\t</td><td>$anames\t</td><td>$atwos\t</td><td>$aemails\t</td><td>$cnames</td><td>$ctwos</td><td>$cemails</td><td>$afpnames</td><td>$afptwos</td><td>$afpemails</td><td>$pdfnames</td><td>$pdftwos</td><td>$pdfemails</td></tr></table>\n); 
  if ($datatype eq 'con') { $row = qq(<tr><td>WBPaper$papid\t</td><td>$pmids</td><td>$pdfs</td><td>$genes</td><td>$aidname\t</td><td>$anames\t</td><td>$atwos\t</td><td>$aemails\t</td><td>$cnames</td><td>$ctwos</td><td>$cemails</td><td>$afpnames</td><td>$afptwos</td><td>$afpemails</td><td>$pdfnames</td><td>$pdftwos</td><td>$pdfemails</td></tr></table>\n); }
  print qq($row);
#   print qq(PMID $pmid 1AUT $aemails<br/>);
#   print qq(AFP $cemails, PDF $pemails<br/>);
#   print qq(AFP $ctwos, PDF $ptwos<br/>);
#   print qq(PAPID $papid END<br/>);
  my %names; tie %names, "Tie::IxHash";
  my @nameSources = ($cnames, $pdfnames, $afpnames, $anames);
  if ($anames) { @nameSources = ( $anames ); }		# if there's first author name, only use that one  2017 07 21
  foreach my $nameSource (@nameSources) {
    $nameSource =~ s/<.*?>//g;
    my (@names) = split/, /, $nameSource;
    foreach my $name (@names) { $names{$name}++; } }
  my $names = join", ", keys %names;
#   print qq(N $names AN $anames CN $cnames PN $pnames E<br/>\n);
  my @emails; my %emails; tie %emails, "Tie::IxHash";
  if ($aemails) {
      my (@aemails) = split/, /, $aemails;
      foreach my $email (@aemails) { $emails{$email}++; } }
    else {
      my %oldEmails;
      my @checkEmails = (); push @checkEmails, $cemails; push @checkEmails, $afpemails; push @checkEmails, $pdfemails;
      foreach my $emailset (@checkEmails) {
        my (@spans) = split/, /, $emailset;
        foreach my $span (@spans) {
          if ($span =~ m/>(.*?)</) {			# some emails in spans
              my ($email) = $span =~m/>(.*?)</;
              if ( $span =~m/color: black/ ) { $emails{$email}++; }
                elsif ( $span =~m/color: orange/ ) { $oldEmails{$email}++; } }
            else { $emails{$span}++; } } }			# other are just emails
      foreach my $oldEmail (sort keys %oldEmails) {
        my @emails;
        $result = $dbh->prepare( "SELECT joinkey FROM two_old_email WHERE two_old_email = '$oldEmail';" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
        my @row = $result->fetchrow(); my $two = $row[0];
        $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = '$two' ORDER BY two_timestamp DESC;" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
        @row = $result->fetchrow(); my $email = $row[2] || 'no current email';
        if ($row[2]) { $emails{$email}++; }
        print qq(old email $oldEmail is person : '$two' with email : '${email}'<br/>);
      } # foreach my $oldEmail (sort keys %oldEmails)
#       if ($cemails) { push @emails, $cemails; }
#       if ($pemails) { push @emails, $pemails; }
    } # else # if ($aemails)
  
  my $email = join", ", keys %emails; 
#   if ($aggemails) { $email = $aggemails; }
  my $ncbiurl = 'http://www.ncbi.nlm.nih.gov/pubmed/' . $pmid . '?report=docsum&format=text';
  my $ncbidata = get($ncbiurl);
  my ($body) = $ncbidata =~ m/1: (.*?)\s*<\/pre>/s;
  my $subject; my $author;
  if ($datatype eq 'app') {
      $subject = 'Contribute phenotype data to WormBase';
      $author = 'Author'; if ($email =~ m/,/) { $author = 'Author(s)'; }
      if ($names) { $author = $names; }
      $body = qq(Dear $author,\n\nIn an effort to improve WormBase's coverage of phenotypes, we are requesting your assistance to annotate nematode phenotypes from the following paper:\n\n$body\n\nWormBase would greatly appreciate if you, or any of the other authors, could take a moment to contribute phenotype connections using our simple web-based tool:\n\nhttp://www.wormbase.org/submissions/phenotype.cgi?input_1_pmid=${pmid}\n\nIf you have any questions, comments or concerns, please let us know.\n\nThank you so much!\n\nBest regards,\n\nThe WormBase Phenotype Team);
    }
    elsif ($datatype eq 'con') {
      $subject = 'WormBase request for community curation of gene descriptions ';
      $author = 'Author'; if ($email =~ m/,/) { $author = 'Author(s)'; }
      if ($names) { $author = $names; }
      $body = qq(Dear $author,\n\nIn an effort to keep the gene descriptions in WormBase updated, we are requesting your assistance either to update an existing gene description or write a new gene description if none exists, for any genes studied in your publication: \n\n$body\n\nGene descriptions appear in the 'Overview' widget on WormBase gene pages. We would greatly appreciate if you, or any of the other authors, could use our simple web-based tool, to either write or update gene descriptions:\n\nhttp://www.wormbase.org/submissions/community_gene_description.cgi\n\nIf you have any questions, comments or concerns, please let us know.\n\nThank you so much!\n\nBest regards,\n\nThe WormBase Gene Description Team);
    }
  print qq(<input type="hidden" name="datatype" value="$datatype"/>\n);
  print qq(<table>);
  print qq(<tr><td>Email</td>  <td><input name="email"   value="$email"   size="100"/></td></tr>\n);
  print qq(<tr><td>Subject</td><td><input name="subject" value="$subject" size="100"/></td></tr>\n);
  print qq(<tr><td>Body</td>   <td><textarea name="body" rows="30" cols="90">$body</textarea></td></tr>\n);
  print qq(<tr><td>Submit</td> <td><input type="submit" name="action" value="send email"></td></tr>\n);
  print qq(</table>);
  print qq(</form>);
} # sub generateEmail


sub readyToGo {
  my ($datatype) = @_;
#   ($var, my $datatype)       = &getHtmlVar($query, 'datatype');

  my %pap;
  my %recentemail;			# email addresses sent in the last month
  my %recentpeople;			# people with an email addresses sent in the last month
  my %email;
  my %two;
  my %com;
  my %gin;

  my $pdfEmailUrl = 'http://tazendra.caltech.edu/~postgres/out/email_pdf_afp';
  my $pdfEmailFile = get $pdfEmailUrl;
  my (@lines) = split/\n/, $pdfEmailFile;
  foreach my $line (@lines) { 
    my ($pap, $email, $afpEmail, $source) = split/\t/, $line;
    $email{pdf}{$pap} = $email; }
  
  $result = $dbh->prepare( "SELECT * FROM com_${datatype}_skip" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { 
      $com{$row[0]}{skip} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM com_${datatype}_emailsent" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { 
      $com{$row[0]}{date}  = $row[2]; 
      $com{$row[0]}{email} = $row[1]; } }

  $result = $dbh->prepare( "SELECT * FROM afp_email WHERE afp_email IS NOT NULL;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { my ($lcemail) = lc($row[1]); $email{afp}{$row[0]} = $lcemail; } }
  $result = $dbh->prepare( "SELECT * FROM two_email" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { my ($lcemail) = lc($row[2]); $email{two}{$lcemail} = $row[0]; } }
  $result = $dbh->prepare( "SELECT * FROM two_old_email" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { my ($lcemail) = lc($row[2]); $email{old}{$lcemail} = $row[0]; } }
  $result = $dbh->prepare( "SELECT * FROM two_standardname" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $two{name}{$row[0]} = $row[2]; } }
  
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{valid}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_pubmed_final WHERE pap_pubmed_final = 'final'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{pubmedfinal}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_type WHERE pap_type = '1'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{journalarticle}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $row[1] =~ s/pmid//; $pap{$row[0]}{pmid}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{pdf}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_primary_data WHERE pap_primary_data = 'primary';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{primary}++; } }

  $result = $dbh->prepare( "SELECT * FROM com_app_emailsent WHERE com_timestamp > current_date - interval '1 months' " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { 
#     $recentemail{pap}{app}{$row[0]}++; 
    if ($row[1]) { ($row[1]) = lc($row[1]);
      my (@recentemails) = split/\s+/, $row[1];
      foreach my $recentemail (@recentemails) {
        $recentemail =~ s/,//g; $recentemail{email}{app}{$recentemail}++; } } }
  $result = $dbh->prepare( "SELECT * FROM com_con_emailsent WHERE com_timestamp > current_date - interval '1 months' " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { 
#     $recentemail{pap}{con}{$row[0]}++; 
    if ($row[1]) { ($row[1]) = lc($row[1]);
      my (@recentemails) = split/\s+/, $row[1];
      foreach my $recentemail (@recentemails) {
        $recentemail =~ s/,//g; $recentemail{email}{con}{$recentemail}++; } } }
# No longer filter out emails that have been AFPed in the last month.  2017 07 31
#   $result = $dbh->prepare( "SELECT * FROM afp_email WHERE afp_timestamp > current_date - interval '1 months' " );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) { 
# #     $recentemail{pap}{afp}{$row[0]}++; 
#     if ($row[1]) { ($row[1]) = lc($row[1]);
#       my (@recentemails) = split/\s+/, $row[1];
#       foreach my $recentemail (@recentemails) {
#         $recentemail =~ s/,//g; $recentemail{email}{afp}{$recentemail}++; } } }
  foreach my $type (sort keys %{ $recentemail{email} }) {
    foreach my $email (sort keys %{ $recentemail{email}{$type} }) {
      if ( $email{old}{$email} ) { $recentpeople{$email{old}{$email}}++; }
      if ( $email{two}{$email} ) { $recentpeople{$email{two}{$email}}++; } } }

  $result = $dbh->prepare( "SELECT * FROM ${datatype}_paper WHERE ${datatype}_paper ~ 'WBPaper'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) {
      my (@paps) = $row[1] =~ m/WBPaper(\d+)/g;
      foreach (@paps) { $pap{$_}{curated}++; } } }

  if ($datatype eq 'app') {
    my $urlAnyFlaggedNCur = 'http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=newmutant&method=any%20pos%20ncur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on';
    my $dataAnyFlaggedNCur = get $urlAnyFlaggedNCur;
    my (@papers) = $dataAnyFlaggedNCur =~ m/specific_papers=WBPaper(\d+)/g;
    foreach (@papers) { $pap{$_}{flaggeddatatype}++; }

      # remove papers that have been curated for RNAi for Chris.  2016 08 23
    my $urlRnaiCurated = 'http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=listCurationStatisticsPapersPage&select_curator=two1823&listDatatype=rnai&method=allcur&checkbox_cfp=on&checkbox_afp=on&checkbox_str=on&checkbox_svm=on';
    my $dataRnaiCurated = get $urlRnaiCurated;
    my (@rnaiPapers) = $dataRnaiCurated =~ m/specific_papers=WBPaper(\d+)/g;
    foreach (@rnaiPapers) { 
      if ($pap{$_}{flaggeddatatype}) {
        delete $pap{$_}{flaggeddatatype}; } }
  } # if ($datatype eq 'app')

  if ($datatype eq 'con') {
    my %toWBGene;
    $result = $dbh->prepare( "SELECT * FROM gin_locus ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      if ($row[0]) { 
        $toWBGene{$row[1]} = $row[0];
        $gin{$row[0]}      = $row[1]; } }
    my $urlTextpressoPap  = 'http://textpresso-dev.caltech.edu/concise_descriptions/textpresso/textpresso_papers_results_genes.txt';
    my $dataTextpressoPap = get $urlTextpressoPap;
    my (@lines) = split/\n/, $dataTextpressoPap;
    foreach my $line (@lines) {
      my ($paper, $loci) = split/\t/, $line;
      if ($paper =~ m/WBPaper(\d{8})/) {
        my $pap = $1; 
        $pap{$pap}{flaggeddatatype}++;
        $loci =~ s/\(.*?\)//g;
        my (@loci) = split/\s+/, $loci;
        foreach my $locus (@loci) {
          my $wbgene = $locus; if ($toWBGene{$locus}) { $wbgene = $toWBGene{$locus}; }
          $pap{$pap}{gene}{$wbgene}++; } }
    } # foreach my $line (@lines)
  } # if ($datatype eq 'con')
  
  
  
  my %filter;
  foreach my $pap (sort keys %pap) {
    next unless ($pap{$pap}{flaggeddatatype});
    next unless ($pap{$pap}{valid});
    next unless ($pap{$pap}{primary});
    next unless ($pap{$pap}{pubmedfinal});
    next unless ($pap{$pap}{journalarticle});
    next unless ($pap{$pap}{pdf});
#     next unless ($email{afp}{$pap});		# paper must have been AFPed first	# Chris no longer wants this restriction 2017 07 31

#     next if ($pap{$pap}{email});
    next if ($com{$pap}{email});		# already emailed in com_<datatype>_emailsent
    next if ($com{$pap}{skip}); 		# already flagged to skip in com_<datatype>_skip
    next if ($pap{$pap}{done});
    next if ($pap{$pap}{curated});
    $filter{$pap}++;
  } # foreach my $pap (sort keys %pap)
  
  my %twoEmail;
  $result = $dbh->prepare( "SELECT * FROM two_email ORDER BY joinkey, two_order" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { push @{ $twoEmail{$row[0]} }, $row[2]; } }
  
  # foreach my $pap (sort keys %filter) { print qq($pap\n); } 
  
  my %aids;
  my $joinkeys = join"','", sort keys %filter;
  $result = $dbh->prepare( "SELECT * FROM pap_author WHERE joinkey IN ('$joinkeys') ORDER BY pap_order::INTEGER DESC;" );	# get most recent aid last for loop
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{aid}{$row[2]} = $row[1]; $aids{$row[1]}{any}++; } }
  my $aids = join"','", sort {$a<=>$b} keys %aids;
  $result = $dbh->prepare( "SELECT * FROM pap_author_index WHERE author_id IN ('$aids');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $aids{$row[0]}{name} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM pap_author_possible WHERE author_id IN ('$aids');" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ( ($row[1]) && ($row[0]) ) { 
      next unless ($twoEmail{$row[1]});
      $aids{$row[0]}{two}{$row[2]} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM pap_author_verified WHERE author_id IN ('$aids') AND pap_author_verified ~ 'YES';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { 
      $aids{$row[0]}{ver} = $row[2]; } }
# Chris no longer wants corresponding author data looked at  2017 07 17
#   $result = $dbh->prepare( "SELECT * FROM pap_author_corresponding WHERE author_id IN ('$aids');" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[0]) { 
#       $aids{$row[0]}{cor} = $row[1]; } }
    
  my $countThreshold = 100;
  print qq(Showing most recent $countThreshold entries<br/>\n);
  print qq(<table style="border-style: none;" border="1" >\n);
  

  my $header = qq(<tr><th>generate</th><th>skip</th><th>WBPaper</th><th>pmids</th><th>pdfs</th><th>first author initials</th><th>first author's person name</th><th>first author's person id</th><th>first author's person emails</th><th>corresponding author name</th><th>corresponding person</th><th>corresponding email</th><th>afp author name</th><th>afp person</th><th>afp email</th><th>pdf author name</th><th>pdf person</th><th>pdf email</th></tr>\n); 
  if ($datatype eq 'con') { $header = qq(<tr><th>generate</th><th>skip</th><th>WBPaper</th><th>pmids</th><th>pdfs</th><th>genes</th><th>first author initials</th><th>first author's person name</th><th>first author's person id</th><th>first author's person emails</th><th>corresponding author name</th><th>corresponding person</th><th>corresponding email</th><th>afp author name</th><th>afp person</th><th>afp email</th><th>pdf author name</th><th>pdf person</th><th>pdf email</th></tr>\n); }
  print $header;
  my $count = 0;
  foreach my $pap (reverse sort keys %filter) {
    my $pmids = join", ", sort keys %{ $pap{$pap}{pmid} };
    my @pdfs;
    foreach my $path (sort keys %{ $pap{$pap}{pdf} }) {
      my ($pdfname) = $path =~ m/\/([^\/]*?)$/;
      my $url = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdfname;
      my $link = qq(<a href='$url' target='new'>$pdfname</a>);
      push @pdfs, $link; }
    my $pdfs = join" ", @pdfs;
    my $recentlyEmailed = 0;
    my ($two, $personName, $person, $emails) = ('', '', '', '');
    my $aidFirstAuthor = ''; if ($pap{$pap}{aid}{1}) { $aidFirstAuthor = $pap{$pap}{aid}{1}; }
# if ($pap eq '00046127') { print "AFA $aidFirstAuthor PAP $pap E<br>"; }
    my @cEmails; my @cTwos; my @cNames;
    my ($cEmail, $cTwo, $cName) = ('', '', '');	# generate from afp_email the person id and name
    foreach my $order (sort {$a<=>$b} keys %{ $pap{$pap}{aid} }) {
# if ($pap eq '00046127') { print "ORDER $order PAP $pap E<br>"; }
      my $aid = $pap{$pap}{aid}{$order};
# if ($pap eq '00046127') { print "ORDER $order AID $aid PAP $pap E<br>"; }
      if ($aids{$aid}{ver}) {
        my $join = $aids{$aid}{ver}; 
# if ($pap eq '00046127') { print "VER JOIN $join ORDER $order AID $aid PAP $pap E<br>"; }
        if ($aids{$aid}{two}{$join}) {
# if ($pap eq '00046127') { print "AID two $aid HERE<br>"; }
          if ($aid eq $aidFirstAuthor) {
# if ($pap eq '00046127') { print "AID AFA $aid HERE<br>"; }
            $two         = $aids{$aid}{two}{$join};
            $personName  = $two{name}{$two}; 
            $person      = $two; $person =~ s/two/WBPerson/;
            $emails      = join", ", @{ $twoEmail{$two} }; }
          if ($recentpeople{$two}) { $recentlyEmailed++; }
          if ($aids{$aid}{cor}) {
            my $cTwo         = $aids{$aid}{two}{$join};
            my $cPersonName  = $two{name}{$cTwo}; 
            my $cEmails      = join", ", @{ $twoEmail{$cTwo} };
            if ( !($emails) && ($recentpeople{$cTwo}) )  { $recentlyEmailed++; }	# if corresponding person was recently emailed and there is no fa->person->email, skip the row  2017 08 03
            push @cEmails, $cEmails;
            push @cTwos,   $cTwo;
            push @cNames,  $cPersonName;
          }
        }
      }
    }
    $cEmail = join", ", @cEmails;
    $cTwo   = join", ", @cTwos;
    $cName  = join", ", @cNames;
# if ($pap eq '00046127') { print qq(PAP $pap CEM $cEmail E<br>); }
    my %categories;
    $categories{good}{color} = 'black';
    $categories{old}{color}  = 'orange';
    $categories{bad}{color}  = 'red';
    my ($afpEmail, $afpTwo, $afpName) = ('', '', '');	# generate from afp_email the person id and name
    my ($pdfEmail, $pdfTwo, $pdfName) = ('', '', '');	# generate from pdf extraction
    unless ($cEmail) {
      if ($email{afp}{$pap}) {
        my %twos; my %emails;
        my @emails; my @twos; my @names;
        my (@afpemails) = split/\s+/, $email{afp}{$pap};
        foreach my $afpemail (@afpemails) {
          my ($two, $name) = ('', '');
          $afpemail =~ s/,//g;
          if ($recentemail{email}{afp}{$afpemail}) { $recentlyEmailed++; }	# to filter by emails recently emailed
          if ($recentemail{email}{app}{$afpemail}) { $recentlyEmailed++; }	# to filter by emails recently emailed
          if ($recentemail{email}{con}{$afpemail}) { $recentlyEmailed++; }	# to filter by emails recently emailed
          if ($email{two}{$afpemail}) {
              $two   = $email{two}{$afpemail}; 
#               if ($recentpeople{$two}) { $recentlyEmailed++; }	# 2017 07 18 no longer prevent showing on the list from an afp email having been emailed
              if ( !($emails) && ($recentemail{email}{app}{$afpemail}) ) { $recentlyEmailed++; }	# 2017 08 03 if no fa->person->email check afpemail has not been emailed recently for this pipeline
              $emails{good}{$afpemail} = $two; 
              $twos{good}{$two}++; }
            elsif ($email{old}{$afpemail}) {
              $two   = $email{old}{$afpemail}; 
#               if ($recentpeople{$two}) { $recentlyEmailed++; }	# 2017 07 18 no longer prevent showing on the list from an afp email having been emailed
              if ( !($emails) && ($recentemail{email}{app}{$afpemail}) ) { $recentlyEmailed++; }	# 2017 08 03 if no fa->person->email check afpemail has not been emailed recently for this pipeline
              $emails{old}{$afpemail} = $two; 
              $twos{old}{$two}++; }
            else {
              $emails{bad}{$afpemail} = 'nowbperson'; }
        }
        foreach my $afpemail (@afpemails) {
          $afpemail =~ s/,//g;
          foreach my $category (sort keys %categories) {
            my $color = $categories{$category}{color} || 'yellow';
            if ($emails{$category}{$afpemail}) {
              my $two = $emails{$category}{$afpemail} || ''; push @emails, qq(<span style='color: $color'>$afpemail</span>);
              if ($two ne 'nowbperson') {
                my $wbperson = $two; $wbperson =~ s/two/WBPerson/g; push @twos, qq(<span style='color: $color'>$wbperson</span>);
                if ($two{name}{$two}) { push @names, qq(<span style='color: $color'>$two{name}{$two}</span>);} } } } }
        $afpEmail = join", ", @emails;
        $afpTwo   = join", ", @twos;
        $afpName  = join", ", @names;
      }
      if ($email{pdf}{$pap}) {
        my %twos; my %emails;
        my @emails; my @twos; my @names;
        my (@pdfemails) = split/\s+/, $email{pdf}{$pap};
        foreach my $pdfemail (@pdfemails) {
          my ($two, $name) = ('', '');
          $pdfemail =~ s/,//g;
          if ($email{two}{$pdfemail}) {
              $two   = $email{two}{$pdfemail}; 
#               if ($recentpeople{$two}) { $recentlyEmailed++; }	# 2017 07 18 no longer prevent showing on the list from an pdf email having been emailed
              if ( !($emails) && ($recentemail{email}{app}{$pdfemail}) ) { $recentlyEmailed++; }	# 2017 08 03 if no fa->person->email check pdfemail has not been emailed recently for this pipeline
              $emails{good}{$pdfemail} = $two; 
              $twos{good}{$two}++; }
            elsif ($email{old}{$pdfemail}) {
              $two   = $email{old}{$pdfemail}; 
#               if ($recentpeople{$two}) { $recentlyEmailed++; }	# 2017 07 18 no longer prevent showing on the list from an pdf email having been emailed
              if ( !($emails) && ($recentemail{email}{app}{$pdfemail}) ) { $recentlyEmailed++; }	# 2017 08 03 if no fa->person->email check pdfemail has not been emailed recently for this pipeline
              $emails{old}{$pdfemail} = $two; 
              $twos{old}{$two}++; }
            else {
              $emails{bad}{$pdfemail} = 'nowbperson'; }
        }
        foreach my $pdfemail (@pdfemails) {
          $pdfemail =~ s/,//g;
          foreach my $category (sort keys %categories) {
            my $color = $categories{$category}{color} || 'yellow';
            if ($emails{$category}{$pdfemail}) {
              my $two = $emails{$category}{$pdfemail} || ''; push @emails, qq(<span style='color: $color'>$pdfemail</span>);
              if ($two ne 'nowbperson') {
                my $wbperson = $two; $wbperson =~ s/two/WBPerson/g; push @twos, qq(<span style='color: $color'>$wbperson</span>);
                if ($two{name}{$two}) { push @names, qq(<span style='color: $color'>$two{name}{$two}</span>);} } } } }
        $pdfEmail = join", ", @emails;
        $pdfTwo   = join", ", @twos;
        $pdfName  = join", ", @names;
      }
    }
    next if ($recentlyEmailed);						# to filter by emails recently emailed
#     my $genes = join"<br/>", sort keys %{ $pap{$pap}{gene} };
    my @genes;
    foreach my $wbgene (sort keys %{ $pap{$pap}{gene} }) {
      my $locus = ''; if ($gin{$wbgene}) { $locus = $gin{$wbgene}; }
      push @genes, qq(WBGene$wbgene,$locus); }
    my $genes = join"<br/>", @genes;
    my $submitButton = ''; my $skipButton = '';
    if ( ($pmids) && ($emails || $cEmail || $afpEmail || $pdfEmail) ) {
      print qq(<form method="post" action="community_curation_tracker.cgi"\n>);
      print qq(<input type="hidden" name="papid"      value="$pap" />\n);
      print qq(<input type="hidden" name="pmids"      value="$pmids" />\n);
      print qq(<input type="hidden" name="aidname"    value="$aids{$aidFirstAuthor}{name}"/>\n);
      print qq(<input type="hidden" name="anames"     value="$personName"/>\n);
      print qq(<input type="hidden" name="atwos"      value="$person"/>\n);
      print qq(<input type="hidden" name="aemails"    value="$emails"/>\n);
      print qq(<input type="hidden" name="cnames"     value="$cName"/>\n);
      print qq(<input type="hidden" name="ctwos"      value="$cTwo"/>\n);
      print qq(<input type="hidden" name="cemails"    value="$cEmail"/>\n);
      print qq(<input type="hidden" name="afpnames"   value="$afpName"/>\n);
      print qq(<input type="hidden" name="afptwos"    value="$afpTwo"/>\n);
      print qq(<input type="hidden" name="afpemails"  value="$afpEmail"/>\n);
      print qq(<input type="hidden" name="pdfnames"   value="$pdfName"/>\n);
      print qq(<input type="hidden" name="pdftwos"    value="$pdfTwo"/>\n);
      print qq(<input type="hidden" name="pdfemails"  value="$pdfEmail"/>\n);
      print qq(<input type="hidden" name="pdfs"       value="$pdfs"/>\n);
      print qq(<input type="hidden" name="genes"      value="$genes"/>\n);
      print qq(<input type="hidden" name="datatype"   value="$datatype"/>\n);
      $submitButton = qq(<input type="submit" name="action" value="generate email">\n); 
      $skipButton   = qq(<input type="submit" name="action" value="skip paper">\n); 

      my $row = qq(<tr><td>$submitButton</td><td>$skipButton</td><td>WBPaper$pap\t</td><td>$pmids</td><td>$pdfs</td><td>$aids{$aidFirstAuthor}{name}\t</td><td>$personName\t</td><td>$person\t</td><td>$emails\t</td><td>$cName</td><td>$cTwo</td><td>$cEmail</td><td>$afpName</td><td>$afpTwo</td><td>$afpEmail</td><td>$pdfName</td><td>$pdfTwo</td><td>$pdfEmail</td></tr>\n);
      if ($datatype eq 'con') { $row = qq(<tr><td>$submitButton</td><td>$skipButton</td><td>WBPaper$pap\t</td><td>$pmids</td><td>$pdfs</td><td>$genes</td><td>$aids{$aidFirstAuthor}{name}\t</td><td>$personName\t</td><td>$person\t</td><td>$emails\t</td><td>$cName</td><td>$cTwo</td><td>$cEmail</td><td>$afpName</td><td>$afpTwo</td><td>$afpEmail</td><td>$pdfName</td><td>$pdfTwo</td><td>$pdfEmail</td></tr>\n); }
      print qq($row);
      print qq(</form>);
      $count++; last if ($count > $countThreshold);
    }
  }
  print qq(<table>);
#   print qq(COUNT $count found<br/>\n);
} # sub readyToGo

sub tracker {
  my ($datatype) = @_;
#   ($var, my $datatype)       = &getHtmlVar($query, 'datatype');

  my %pap;
  my %com;
  my %gin;
  my %emailToPerson;

  $result = $dbh->prepare( "SELECT joinkey, LOWER(two_old_email) FROM two_old_email" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[1]) { $row[0] =~ s/two/WBPerson/; $emailToPerson{$row[1]} = $row[0]; } }
  $result = $dbh->prepare( "SELECT joinkey, LOWER(two_email) FROM two_email" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { if ($row[1]) { $row[0] =~ s/two/WBPerson/; $emailToPerson{$row[1]} = $row[0]; } }
  
  $result = $dbh->prepare( "SELECT * FROM com_${datatype}_emailsent" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { 
      $com{$row[0]}{date}  = $row[2]; 
      my (@emails) = split/,/, $row[1];
      my @emailPersons = ();
      foreach my $email (@emails) { $email =~ s/\s+//g; my $lcemail = lc($email); push @emailPersons, qq($email \($emailToPerson{$lcemail}\)); }
      my $emailPersons = join", ", @emailPersons;
      $com{$row[0]}{email} = $emailPersons; } }
  $result = $dbh->prepare( "SELECT * FROM com_${datatype}_emailresponse" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $com{$row[0]}{response} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM com_${datatype}_remark" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $com{$row[0]}{remark} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM com_${datatype}_skip" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $com{$row[0]}{skip} = $row[1]; } }
  
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $row[1] =~ s/pmid//; $pap{$row[0]}{pmid}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pap{$row[0]}{pdf}{$row[1]}++; } }
  
  if ($datatype eq 'app') {
    $result = $dbh->prepare( "SELECT * FROM app_paper WHERE app_paper ~ 'WBPaper' AND joinkey IN (SELECT joinkey FROM app_curator WHERE app_curator = 'WBPerson29819')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      if ($row[0]) {
        my (@paps) = $row[1] =~ m/WBPaper(\d+)/g;
        foreach (@paps) { $pap{$_}{communityCurated}{app}++; } } }
    $result = $dbh->prepare( "SELECT * FROM rna_paper WHERE rna_paper ~ 'WBPaper' AND joinkey IN (SELECT joinkey FROM rna_curator WHERE rna_curator = 'WBPerson29819')" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      if ($row[0]) {
        my (@paps) = $row[1] =~ m/WBPaper(\d+)/g;
        foreach (@paps) { $pap{$_}{communityCurated}{rna}++; } } }
  } # if ($datatype eq 'app')
  if ($datatype eq 'con') {
    my %toWBGene;
    $result = $dbh->prepare( "SELECT * FROM gin_locus ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      if ($row[0]) { 
        $toWBGene{$row[1]} = $row[0];
        $gin{$row[0]}      = $row[1]; } }
    my $urlTextpressoPap  = 'http://textpresso-dev.caltech.edu/concise_descriptions/textpresso/textpresso_papers_results_genes.txt';
    my $dataTextpressoPap = get $urlTextpressoPap;
    my (@lines) = split/\n/, $dataTextpressoPap;
    foreach my $line (@lines) {
      my ($paper, $loci) = split/\t/, $line;
      if ($paper =~ m/WBPaper(\d{8})/) {
        my $pap = $1; 
        $pap{$pap}{flaggeddatatype}++;
        $loci =~ s/\(.*?\)//g;
        my (@loci) = split/\s+/, $loci;
        foreach my $locus (@loci) {
          my $wbgene = $locus; if ($toWBGene{$locus}) { $wbgene = $toWBGene{$locus}; }
          $pap{$pap}{gene}{$wbgene}++; } }
    } # foreach my $line (@lines)
    $result = $dbh->prepare( "SELECT con_paper.joinkey, con_paper.con_paper, con_wbgene.con_wbgene FROM con_paper, con_wbgene WHERE con_paper.joinkey = con_wbgene.joinkey AND con_paper ~ 'WBPaper' AND con_paper.joinkey IN (SELECT joinkey FROM con_person WHERE con_person IS NOT NULL)" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      if ($row[0]) {
        my (@paps) = $row[1] =~ m/WBPaper(\d+)/g;
        foreach (@paps) { $pap{$_}{communityCurated}{$row[2]}++; } } }
  } # if ($datatype eq 'con')

  my %filter;
  foreach my $pap (sort keys %pap) {
    next unless ($com{$pap}{email});
    $filter{$pap}++;
  } # foreach my $pap (sort keys %pap)

  foreach my $pap (sort keys %com) {			# get all skipped papers to show on tracker
    if ($com{$pap}{skip}) { $filter{$pap}++; } }
  
  print qq(<table id="sortabletable" style="border-style: none;" border="1">\n);
#   print qq(<thead><tr><th>email response</th><th>remark</th><th>recently e-mailed</th><th>allele-phenotype email date</th><th>email addresses sent request</th><th>community curated</th><th>WBPaper</th><th>pmids</th><th>author names</th><th>person names</th><th>person</th><th>emails</th><th>corresponding author name</th><th>corresponding person</th><th>corresponding email</th><th>pdfs</th></tr></thead><tbody>\n); 
  my $header = qq(<thead><tr><th>email response</th><th>remark</th><th>allele-phenotype email date</th><th>email addresses sent request</th><th>community curated app</th><th>community curated rna</th><th>WBPaper</th><th>pmids</th><th>pdfs</th></tr></thead><tbody>\n); 
   if ($datatype eq 'con') { $header = qq(<thead><tr><th>email response</th><th>remark</th><th>concise email date</th><th>email addresses sent request</th><th>community curated</th><th>WBPaper</th><th>pmids</th><th>pdfs</th><th>genes</th></tr></thead><tbody>\n); }
  print qq($header);
  foreach my $pap (reverse sort keys %filter) {
    my $pmids = join", ", sort keys %{ $pap{$pap}{pmid} };
    my @pdfs;
    foreach my $path (sort keys %{ $pap{$pap}{pdf} }) {
      my ($pdfname) = $path =~ m/\/([^\/]*?)$/;
      my $url = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdfname;
      my $link = qq(<a href="$url" target="new">$pdfname</a>);
      push @pdfs, $link; }
    my $pdfs = join" ", @pdfs;
    print qq(<form method="post" action="community_curation_tracker.cgi"\n>);
    print qq(<input type="hidden" name="pmids"   value="$pmids" />\n);
    my $communityCurated     = 'NOT'; 
    my $communityCuratedRnai = 'NOT'; 
    if ($datatype eq 'app') {
      if ($pap{$pap}{communityCurated}{app}) { $communityCurated     = 'curated'; }
      if ($pap{$pap}{communityCurated}{rna}) { $communityCuratedRnai = 'curated'; } }
    if ($datatype eq 'con') {
      if (scalar keys %{ $pap{$pap}{communityCurated}} > 0) {
        my @genes;
        foreach my $wbgene (sort keys %{ $pap{$pap}{communityCurated} }) {
          $wbgene =~ s/WBGene//;
          my $locus = ''; if ($gin{$wbgene}) { $locus = $gin{$wbgene}; }
          push @genes, qq(WBGene$wbgene,$locus); }
        $communityCurated = join"<br/>", @genes; } }
    if ($com{$pap}{skip}) { $communityCurated = 'skip'; }
    my $textareacols = '40';
    my $response = ''; if ($com{$pap}{response}) { $response = $com{$pap}{response}; }
    my $responseAjaxUrl = "community_curation_tracker.cgi?action=ajaxUpdate&papid=$pap&field=emailresponse&datatype=$datatype&value=";
    my $responseInput = qq(<input name="response" id="${pap}_inputresponse" value="$response" onfocus="document.getElementById('${pap}_inputresponse').style.display = 'none'; document.getElementById('${pap}_textarearesponse').style.display = ''; document.getElementById('${pap}_textarearesponse').focus(); "/>);
    my $responseTextarea = qq(<textarea id="${pap}_textarearesponse" rows="5" cols="$textareacols" style="display:none;" onblur="document.getElementById('${pap}_inputresponse').style.display = ''; document.getElementById('${pap}_textarearesponse').style.display = 'none'; var inputValue = document.getElementById('${pap}_inputresponse').value; var textareaValue = document.getElementById('${pap}_textarearesponse').value; if (inputValue !== textareaValue) { document.getElementById('${pap}_inputresponse').value = textareaValue; var ajaxUrl = '${responseAjaxUrl}' + document.getElementById('${pap}_textarearesponse').value; \$.ajax({ url: ajaxUrl }); }" >$response</textarea>);
    my $remark = ''; if ($com{$pap}{remark}) { $remark = $com{$pap}{remark}; }
    my $remarkAjaxUrl = "community_curation_tracker.cgi?action=ajaxUpdate&papid=$pap&field=remark&datatype=$datatype&value=";
    my $remarkInput = qq(<input name="remark" id="${pap}_inputremark" value="$remark" onfocus="document.getElementById('${pap}_inputremark').style.display = 'none'; document.getElementById('${pap}_textarearemark').style.display = ''; document.getElementById('${pap}_textarearemark').focus(); "/>);
    my $remarkTextarea = qq(<textarea id="${pap}_textarearemark" rows="5" cols="$textareacols" style="display:none;" onblur="document.getElementById('${pap}_inputremark').style.display = ''; document.getElementById('${pap}_textarearemark').style.display = 'none'; var inputValue = document.getElementById('${pap}_inputremark').value; var textareaValue = document.getElementById('${pap}_textarearemark').value; if (inputValue !== textareaValue) { document.getElementById('${pap}_inputremark').value = textareaValue; var ajaxUrl = '${remarkAjaxUrl}' + document.getElementById('${pap}_textarearemark').value; \$.ajax({ url: ajaxUrl }); }" >$remark</textarea>);
    my $emailedDate      = ''; if ($com{$pap}{date}) {  ($emailedDate)    = $com{$pap}{date} =~ m/^([\d\-]{10})/;  }
    my $emailedAddresses = ''; if ($com{$pap}{email}) { $emailedAddresses = $com{$pap}{email}; }
    my $genes = '';
    if ($datatype eq 'con') {
      my @genes;
      foreach my $wbgene (sort keys %{ $pap{$pap}{gene} }) {
        my $locus = ''; if ($gin{$wbgene}) { $locus = $gin{$wbgene}; }
        push @genes, qq(WBGene$wbgene,$locus); }
        $genes = join"<br/>", @genes; }
    my $row = qq(<tr><td>${responseInput}${responseTextarea}</td><td>${remarkInput}${remarkTextarea}</td><td>$emailedDate</td><td>$emailedAddresses</td><td>$communityCurated</td><td>$communityCuratedRnai</td><td>WBPaper$pap\t</td><td>$pmids</td><td>$pdfs</td></tr>\n); 
    if ($datatype eq 'con') { $row = qq(<tr><td>${responseInput}${responseTextarea}</td><td>${remarkInput}${remarkTextarea}</td><td>$emailedDate</td><td>$emailedAddresses</td><td>$communityCurated</td><td>WBPaper$pap\t</td><td>$pmids</td><td>$pdfs</td><td>$genes</td></tr>\n); }
    print qq($row);
    print qq(</form>);
  }
  print qq(</tbody></table>);
} # sub tracker
  
sub asdf {
  1;
}

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

sub printHtmlMenu {		# show main menu page
  print <<"  EndOfText";
  <FORM METHOD="POST" ACTION="community_curation_tracker.cgi">
  <TABLE border=0>
  <TR>
    <TD COLSPAN=3><B>New Mutant : </B></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="New Mutant Ready"></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="New Mutant Tracker"></TD>
  </TR>
  <TR>
    <TD COLSPAN=3><B>Concise Description : </B></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Concise Description Ready"></TD>
    <TD><INPUT TYPE="submit" NAME="action" VALUE="Concise Description Tracker"></TD>
  </TR>
<!--
  <TR><TD><B>OR</B></TD></TR>
  <TR>
    <TD COLSPAN=3><B>Query Variation : </B></TD>
    <TD><textarea rows=5 cols=40 name=variations></textarea><br /><INPUT TYPE="submit" NAME="action" VALUE="Query Variation !"></TD>
  </TR>-->
  EndOfText
  print "</TABLE>\n";
  print "</FROM>\n";
} # sub printHtmlMenu


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
