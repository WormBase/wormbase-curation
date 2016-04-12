#!/usr/bin/perl 

# Form to submit Wild Isolate information.

# a wild isolate form to email genenames@wormbase.org and user.  for Mary Ann.  2011 03 03
#
# some changes for M.A.  2011 03 04
#
# some more changes for M.A.  2011 03 07
# 
# some more changes for M.A.  2011 03 11
# 
# some more changes for M.A.  2011 03 17
#
# some more changes for M.A.  2011 03 18
#
# some more changes for M.A.  2011 03 22
#
# send to genenames@wormbase.org for M.A.  2011 04 05
#
# added freezing history for M.A.  2011 09 09



my $firstflag = 1;		# flag if first time around (show form for no data)

# use LWP::Simple;
# use Mail::Mailer;

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $acefile = "/home/azurebrd/public_html/cgi-bin/data/wild_isolate.ace";


my $query = new CGI;
my $user = 'wild_isolate_form';	# who sends mail
# my $email = 'mt3@sanger.ac.uk';	# to whom send mail 
my $email = 'genenames@wormbase.org';	# to whom send mail 	# send to this address 2011 04 05
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = '[wormbase-genenames] Wild isolate';		# subject of mail
my $body = '';			# body of mail
my $ace_body = '';		# body of ace file


# my @all_vars = qw ( person_evidence submitter_email pos_phenont not_phenont suggest_new gene nature_of_allele penetrance heat_sensitive cold_sensitive hot_temp cold_temp types_of_mutations mutation_info loss_of_function phenotypic_description sequence types_of_alteration alteration_text indel_seq upstream downstream strain species species_other genotype mutagen forward reverse comment );
my @all_vars = qw ( person_evidence submitter_email strain_name species species_other genotype other_name location inbreeding freezing reference gps_one gps_two place landscape substrate assoc_organism life_stage log_population sampled_by isolated_by date comment );
# pos_phenont not_phenont suggest_new gene nature_of_allele penetrance heat_sensitive cold_sensitive hot_temp cold_temp types_of_mutations mutation_info loss_of_function phenotypic_description sequence types_of_alteration alteration_text indel_seq upstream downstream strain species species_other genotype mutagen forward reverse comment
  

print "Content-type: text/html\n\n";
my $title = 'Wild Isolate Data Submission Form';
my ($header, $footer) = &cshlNew($title);

# $header = "<html><head></head>";

my $extra_stuff = << "EndOfText";
<style type="text/css">
body {
	margin:0;
	padding:0;
}
#forcedPhenontAutoComplete {
    width:30em; /* set width here or else widget will expand to fit its container */
    padding-bottom:2em;
}
#notPhenontAutoComplete {
    width:30em; /* set width here or else widget will expand to fit its container */
    padding-bottom:2em;
}
</style>
<link rel="stylesheet" type="text/css" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" />
<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/fonts/fonts-min.css" />
<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css" />
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/yahoo-dom-event/yahoo-dom-event.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/connection/connection-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/datasource/datasource-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/autocomplete/autocomplete-min.js"></script>
<script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/allele_submission.js"></script>
<script type="text/JavaScript">
<!--Your browser is not set to be Javascript enabled 
function change_type_P(form) {
   var sel_idx = form.types_of_alteration.selectedIndex;
   if (sel_idx == 0){
      document.getElementById("seq_input").value="enter mutation details";
      document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
   }
   if (sel_idx == 1){
      document.getElementById("seq_input").value="eg, c to t OR c to ag";
      document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
   }
   if (sel_idx == 2){
      document.getElementById("seq_input").value="eg, Tc1";
      document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
   }   
   if (sel_idx == 3){
      document.getElementById("seq_input").value="enter inserted seq. or coordinates";
      document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
   }
   if (sel_idx == 4){
      document.getElementById("seq_input").value="enter deleted seq. or coordinates";
      document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
   }    
   if (sel_idx == 5){
      document.getElementById("seq_input").value="enter deleted seq. or coordinates";
	  document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="enter inserted seq. or coordinates";
   }
   if (sel_idx == 6){
      document.getElementById("seq_input").value="copy your info here";
      document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
   }   
}
function rollback(){
     document.getElementById("seq_input").value="";
     document.getElementById("indel_input").type="text";
      document.getElementById("indel_input").value="do not use, for insertion + deletion only";
}
function change_type_G(form) {
   var sel_idx = form.types_of_mutations.selectedIndex;
   if (sel_idx == 0){
      document.getElementById("mutation").value="Enter mutation details";
   }
   if (sel_idx == 1){
      document.getElementById("mutation").value="eg, Q(200) to R";
   }
   if (sel_idx == 2){
      document.getElementById("mutation").value="eg, Q(200) -> Amber (Amber_UAG, Ochre_UAA, Opal_UGA)";
   }   
   if (sel_idx == 3){
      document.getElementById("mutation").value="eg, cag -> caa";
   }
   if (sel_idx == 4){
      document.getElementById("mutation").value="please specify";
   }    
   if (sel_idx == 5){
      document.getElementById("mutation").value="please specify";
   }    
}
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

</head>  
EndOfText
# $header =~ s/<\/head>/$extra_stuff\n<\/head>/;	# to add javascript stuff comment this out again




print "$header\n";		# make beginning of HTML page

&process();			# see if anything clicked
&display();			# show form as appropriate
# print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'Submit') {
    $firstflag = "";				# reset flag to not display first page (form)

    my $mandatory_ok = 'ok';			# default mandatory is ok
    my $sender = '';
    my @mandatory = qw ( submitter_email person_evidence strain_name genotype location );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{strain_name} = "Strain name";
    $mandatoryName{person_evidence} = "Submitter Name";
    $mandatoryName{genotype} = "Genotype";
    $mandatoryName{location} = "Location";
 
    my $sender_name = '';
    foreach $_ (@mandatory) {			# check mandatory fields
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($_ eq 'submitter_email') {		# check emails
        unless ($val =~ m/@.+\..+/) { 		# if email doesn't match, warn
          print "<FONT COLOR=red SIZE=+2>$val is not a valid email address.</FONT><BR>";
          $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
        } else { $sender = $val; }
      } else { 					# check other mandatory fields
	unless ($val) { 			# if there's no value
          print "<FONT COLOR=red SIZE=+2>$mandatoryName{$_} is a mandatory field.</FONT><BR>";
          $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
        }
        if ($_ eq 'person_evidence') { $sender_name = $val; }
      }
    } # foreach $_ (@mandatory)

    my ($var, $sp) = &getHtmlVar($query, "species");
    ($var, my $spo) = &getHtmlVar($query, "species_other");
    if ($sp) { if ($sp eq 'Other') { unless ($spo) {
      print "<FONT COLOR=red SIZE=+2>You entered $sp for Species, but did not enter text for the Other Species field.</FONT><BR>";
      $mandatory_ok = 'bad'; } } }
    if ( !$sp && !$spo ) { 
      print "<FONT COLOR=red SIZE=+2>You must enter one of the two species fields.</FONT><BR>";
      $mandatory_ok = 'bad'; }

#     my @one_of_two = qw( species species_other );
#     my $one_of_two_flag = 0;
#     foreach $_ (@one_of_two) {			# check mandatory fields
#       my ($var, $val) = &getHtmlVar($query, $_);
#       if ($val =~ m/./) { $one_of_two_flag++; } }
#     unless ($one_of_two_flag > 0) { 
#       print "<FONT COLOR=red SIZE=+2>You must enter one of the two species fields.</FONT><BR>";
#       $mandatory_ok = 'bad'; }

    my @one_of_two = qw( gps_one gps_two );
    my $one_of_two_flag = 0;
    foreach $_ (@one_of_two) {			# check mandatory fields
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val =~ m/^\s+/) { $val =~ s/^\s+//; } if ($val =~ m/\s+$/) { $val =~ s/\s+$//; }
      if ($val =~ m/[^[0-9\-\.]/) { 
        print "<FONT COLOR=red SIZE=+2>GPS coordinates should be numbers, you entered $val.  Feel free to click back on your browser and resubmit.</FONT><BR>"; }
      if ($val =~ m/./) { $one_of_two_flag++; } }
    if ($one_of_two_flag == 1) { 
      print "<FONT COLOR=red SIZE=+2>If you enter one GPS field, you must enter the other.  Feel free to click back on your browser and resubmit.</FONT><BR>"; }


    my $spam = 0;				# if it's spam skip doing anything  2007 08 24
    foreach $_ (@all_vars) { 			# for all fields, check for spam
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val =~ m/\S/) { 	# if value entered
        if ($val =~ m/a href/i) { 
          my (@spam) = $val =~ m/(a href)/gi;
          foreach my $sp (@spam) { $spam++; } } } }
#     print "SPAM $spam SPAM<BR>\n"; 
    if ($spam > 0) { print "Ignoring.  This is spam<BR>\n"; return; }

    if ($mandatory_ok eq 'bad') { 
      print "Please click back on your browser and resubmit.<P>";
    } else { 					# if email is good, process
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
#       $body .= "$sender from ip $host sends :\n\n";	# Mary Ann doesn't want this 2006 05 10

      my %aceName;
      $aceName{strain_name} = 'NULL';
      $aceName{species} = 'NULL';		# check that species_other wasn't filled
      $aceName{species_other} = 'Species';
      $aceName{genotype} = 'Genotype';
      $aceName{other_name} = 'Other_name';
      $aceName{location} = 'Location';
      $aceName{inbreeding} = 'Inbreeding_state';
      $aceName{freezing} = 'Freezing_history';
      $aceName{reference} = 'Reference';
      $aceName{gps_one} = 'NULL';
      $aceName{gps_two} = 'NULL';
      $aceName{place} = 'Place';
      $aceName{landscape} = 'Landscape';
      $aceName{substrate} = 'Substrate';
      $aceName{assoc_organism} = 'Associated Organism';
      $aceName{life_stage} = 'Life_stage';
      $aceName{log_population} = 'Log size of population';
      $aceName{sampled_by} = 'Sampled_by';
      $aceName{isolated_by} = 'NULL';
      $aceName{person_evidence} = 'NULL';
      $aceName{submitter_email} = 'NULL';
      $aceName{date} = 'NULL';
      $aceName{comment} = 'NULL';

      my ($var, $strain_name) = &getHtmlVar($query, 'strain_name');
      unless ($strain_name =~ m/\S/) {			# if there's no allele text
        print "<FONT COLOR='red'>Warning, you have not picked an Allele</FONT>.<P>\n";
      } else {					# if allele text, output
#         print OUT "Allele : [$allele] \n";
#         print "Allele : [$allele]<BR>\n";
#         $result = $dbh->do( "INSERT INTO ale_allele (ale_allele) VALUES ('$allele');" );
# 						# this updated the pg sequence ale_seq to nextval
#         $result = $dbh->prepare( "SELECT currval('ale_seq');" );	
#         $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#         $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
# 						# can get currval because last line updated
#         my @row = $result->fetchrow;
#         $joinkey = $row[0];
#         print "Allele entry number $joinkey<BR><BR>\n";
# 	$allele =~ s///g; $allele =~ s/\n//g; $allele = lc($allele);	# lowercase allele
        $body .= "Strain\t$strain_name\n";
        $ace_body .= "Strain : \"$strain_name\"\n";
# 	my $keith_method = 'Allele';
        $subject .= " : $strain_name";
#         $result = $dbh->do( "INSERT INTO ale_submitter_email VALUES ('$joinkey', '$sender');" );
#         $result = $dbh->do( "INSERT INTO ale_ip VALUES ('$joinkey', '$host');" );
  
# my @all_vars = qw ( person_evidence submitter_email strain_name species species_other genotype location inbreeding gps_one gps_two place landscape substrate assoc_organism life_stage log_population sampled_by isolated_by date );
        foreach my $field (@all_vars) { 			# for all fields, check for data and output
          my ($var, $val) = &getHtmlVar($query, $field);
          if ($val =~ m/\S/) { 	# if value entered

              # $ace_body output varies by field
            if ($aceName{$var} ne 'NULL') {
              $ace_body .= "$aceName{$var}\t\"$val\"\n";
              $body .= "$var\t\"$val\"\n";
#               if ($var eq 'gene') { $val = lc($val); }		# lowercase gene
#               elsif ($var eq 'strain') { $val = uc($val); }	# uppercase strain
#               elsif ($var eq 'sequence') { 
#                 $val =~ s/\..*$//;				# take out anything after . (and .)
#                 $val = uc($val); }				# uppercase sequence
#               else { 1; }
#               if ($var eq 'gene') { $ace_body .= "$aceName{$var}\t\/\/\"$val\"\n"; }	# comment out genes for Mary Ann 2006 05 10
#                 else { $ace_body .= "$aceName{$var}\t\"$val\"\n"; }
            } # if ($aceName{$var} ne 'NULL')

	    elsif ($var eq 'gps_one') { 
              my ($var, $gps_two) = &getHtmlVar($query, 'gps_two');
	      $val =~ s///g; $val =~ s/\n//g;
#               if ($gps_one =~ m/^\s+/) { $gps_one =~ s/^\s+//; } if ($gps_one =~ m/\s+$/) { $gps_one =~ s/\s+$//; }
#               if ($gps_two =~ m/^\s+/) { $gps_two =~ s/^\s+//; } if ($gps_two =~ m/\s+$/) { $gps_two =~ s/\s+$//; }
              $body .= "GPS one\t\"$val\"\n";
	      if ($gps_two) { 
                $body .= "GPS two\t\"$gps_two\"\n";
                $val .= "\"\t\"$gps_two"; }
              $ace_body .= "GPS\t\"$val\"\n";
            }
	    elsif ($var eq 'species') { 
              my ($var, $species_other) = &getHtmlVar($query, 'species_other');
	      $val =~ s///g; $val =~ s/\n//g;
	      unless ($species_other) { $ace_body .= "Species\t\"$val\"\n"; }
              $body .= "Species\t\"$val\"\n";
            }
	    elsif ($var eq 'date') { 
              $body .= "Date\t\"$val\"\n";			# send original, not processed
              if ($val =~ m/^(\d{2})\/(\d{2})\/(\d{4})/) { $val = $3 . '-' . $2 . '-' . $1; }
              $ace_body .= "Date\t\"$val\"\n";
            }
	    elsif ($var eq 'isolated_by') { 
              my ($names) = &findName($val); if ($names) { $val .= " (could be $names)"; }
              $ace_body .= "Isolated_by\t\"$val\"\n";
              $body .= "Isolated_by\t\"$val\"\n";
            }
	    elsif ($var eq 'person_evidence') { 
              my ($names) = &findName($val); if ($names) { $val .= " (could be $names)"; }
#               $ace_body .= "Person_evidence\t\"$val\"\n";	# MA doesn't want this in .ace section
              $body .= "Submitter Name\t\"$val\"\n";
              $body = "Wild isolate submission from $val\n\n" . $body;
            }
	    elsif ($var eq 'submitter_email') { $body .= "Submitter Email\t\"$val\"\n"; }
	    elsif ($var eq 'comment') { $body .= "Comment\t\"$val\"\n"; }
	    else { 1; }

 
#             if ($var eq 'person_evidence') { my ($names) = &findName($val); }
#             next if ($field eq 'pos_phenont');		# jolene does not want these in postgres  2009 06 12
#             next if ($field eq 'not_phenont');		# jolene does not want these in postgres  2009 06 12
#             next if ($field eq 'suggest_new');		# jolene does not want these in postgres  2009 06 12
#             my $pg_table = 'ale_' . $var;
#             $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
          } # if ($val) 
        } # foreach $_ (@vars) 
# 	$ace_body .= "Method\t\"$keith_method\"\n";
#         $ace_body .= "\n$strain_body";
        my $full_body = $body . "\n" . $ace_body;
#         $keith_body .= "\n" . $body . "\n" . $ace_body;
        print OUT "$full_body\n";			# print to outfile
        close (OUT) or die "cannot close $acefile : $!";
#       print "MAIL TO : $sender :<BR>\n"; 
        $email .= ", $sender";
        &mailer($user, $email, $subject, $full_body);	# email the data

#         &mailer($user, $email, $subject, $keith_body);	# email the data
        $body = "Dear $sender_name,\n\nYou have sucessfully submitted the following data to WormBase. You will be contacted by WormBase within three working days.\n\nIf you wish to modify your submitted information, please go back and resubmit.\n" . $body;
        $body =~ s/\n/<BR>\n/mg;
        $ace_body =~ s/\n/<BR>\n/mg;
#         print "BODY : <BR>$body<BR><BR>\n";
        print "$body<BR><BR>\n";
#         print "ACE : <BR>$ace_body<BR><BR>\n";	# don't print Ace to form for Mary Ann 2006 05 10
#         print "<P><P><P><H1>Thank you for your submission.  You will be contacted by WormBase within three working days.</H1>\n";						# put this message in front of body for Mary Ann 2006 05 10
#         print "If you wish to modify your submitted information, please go back and resubmit.<BR><P> See all <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/allele.ace\">new submissions</A>.<P>\n";
        print "If you wish to modify your submitted information, please go back and resubmit.<BR><P>\n";

      } # else # unless ($allele =~ m/\S/)	# this if/then/else should be unnecessary
    } # else # unless ($sender =~ m/@.+\..+/)
  } # if ($action eq 'Submit') 

} # sub process


sub display {			# show form as appropriate
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }
  next if ($action eq 'instructions');
  if ($firstflag) { &displayForm(); } 
} # sub display

sub displayForm {
    my $mandatory_font = "<FONT COLOR='red' size='2'>";
    my $normal_font = "<FONT COLOR='black' size='2'>";
    my $tr_blue = "<tr bgcolor='#b0cffa' border='0' cellpadding='0' cellspacing='0'>";
    print << "EndOfText";
<body class="yui-skin-sam">
<script language="JavaScript">
<!--
  function SymError(){
    return true;
  }
  window.onerror = SymError;
  var SymRealWinOpen = window.open;

  function SymWinOpen(url, name, attributes){
  return (new Object());
  }
  window.open = SymWinOpen;
//-->
</script>
<script type="text/javascript">
<!--
  function c(p){location.href=p;return false;}
// -->
</script>

<!-- Email <A HREF="mailto:genenames\@wormbase.org">genenames\@wormbase.org</A> for any questions/problems.-->

<A NAME="form"><H1>Wild Isolate Data Submission Form :</H1></A>
<center>Please enter as much information as possible.<br /><br /><u><b><font color="red">red fields are required</font></u></b><br /><br /><font size=\"2\">If you have a large number of strains to submit please contact
<A HREF="mailto:genenames\@wormbase.org">genenames\@wormbase.org</A> to discuss submission options.</font></center>
<HR>

<form method="post" action="wild_isolate.cgi">
 <table align="center" cellpadding="1" cellspacing="1" border="0">
  <tr>
    <td colspan="2"><table border=0 width="100%" align="center" cellpadding="1" cellspacing="1">
    <!--<td width="34%"><FONT SIZE=+2><B>REQUIRED</B></FONT></td>
    <td width="28%">&nbsp;</td>
    <td width="38%">&nbsp;</td>-->
    <td >&nbsp;</td>
    <td >&nbsp;</td>
    <td >&nbsp;</td>
  </tr>
  <TR>
    <TD ALIGN="right"><U>$mandatory_font<B>Submitter's Name</B></FONT></U><B> :</B> <BR></TD>
    <TD><Input Type="Text" ID="person_evidence" Name="person_evidence" Size="40"></TD>
    <TD><font size="2">Please enter full name, e.g. John Sulston</font></TD>
  </TR>
  <TR>
    <TD ALIGN="right"><U>$mandatory_font<B>Submitter's Email</B></FONT></U><B> :</B> <BR></TD>
    <TD><Input Type="Text" Name="submitter_email" Size="40" Maxlength="40"></TD>
    <TD><font size="2">This is used to confirm receipt.  (for contact purpose)<BR>If you don't get a confirmation email, contact us at webmaster\@wormbase.org</font></TD>
  </TR>
  <tr> 
    <TD ALIGN="right"><U>$mandatory_font<B>Strain name</B></FONT></U><B> :</B> <BR>
    <TD><Input Type="Text" Name="strain_name" Size="40"></TD>
    <TD><font size="2">e.g. JU234</font></TD>
  </tr>
  <tr>
    <td colspan="1" align="right"><U>$mandatory_font<B>Species</FONT></U> :</B></td><td colspan="2">
          <Select Name="species" Size="1">
           <Option Value="" Selected>
           <Option Value="Caenorhabditis elegans">Caenorhabditis elegans</Option>
           <Option Value="Caenorhabditis briggsae">Caenorhabditis briggsae</Option>
           <Option Value="Caenorhabditis brenneri">Caenorhabditis brenneri</Option>
           <Option Value="Caenorhabditis remanei">Caenorhabditis remanei</Option>
           <Option Value="Other">Other</Option>
          </Select>
    	  <!--<Input Type="radio" checked Name="species" Value="Caenorhabditis elegans">C. elegans
          <Input Type="radio" Name="species" Value="other_species">Other -->
     <font size="2"><B>Other Species</FONT> :</B><Input Type="Text" Name="species_other" Size="28"></B></td>
  </tr>
  <tr> 
    <TD ALIGN="right"><U>$mandatory_font<B>Genotype</B></FONT></U><B> :</B> <BR>
    <TD><Input Type="Text" Name="genotype" Size="40"></TD>
    <TD><font size="2">e.g. C. elegans wild isolate.</font></TD>
  </tr>
  <tr> 
    <TD ALIGN="right">$normal_font<B>Other Name</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="other_name" Size="40"></TD>
    <TD><font size="2">e.g. JA2.3</font></TD>
  </tr>
  <tr> 
    <TD ALIGN="right"><U>$mandatory_font<B>Storage Location</B></FONT></U><B> :</B> <BR>
    <TD><Input Type="Text" Name="location" Size="40"></TD>
    <TD><font size="2">Indicates where the strain is stored e.g. JU. If this strain is already stored at the CGC please enter CGC.</font></TD>
  </tr>

  <tr> 
    <TD ALIGN="right">$normal_font<B>Inbreeding State</B><B> :</B></font><BR>
    <TD>
          <Select Name="inbreeding" Size="1">
           <Option Value="" Selected>
           <Option Value="Selfed">Selfed</Option>
           <Option Value="Isofemale">Isofemale</Option>
           <Option Value="Multifemale">Multifemale</Option>
           <Option Value="Inbred">Inbred</Option>
          </Select></TD>
  </tr>
  <tr> 
    <TD ALIGN="right">$normal_font<B>Freezing History</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="freezing" Size="40"></TD>
    <TD><font size="2"></font></TD>
  </tr>
  <tr> 
    <TD ALIGN="right">$normal_font<B>References</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="reference" Size="40"></TD>
    <TD><font size="2">PubMed identifier or WormBase paper e.g.  19071962 or WBPaper00032424</font></TD>
  </tr>
     <TR><td>&nbsp;</td>
     $tr_blue
        <td colspan="3" align="center"><FONT SIZE=+2><B>ISOLATION</B></FONT></td>
      </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>GPS</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="gps_one" Size="15">&nbsp;<Input Type="Text" Name="gps_two" Size="15"></TD>
    <TD><font size="2">e.g. 37.4721 -5.6331  (latitude longitude in decimal format)</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Place</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="place" Size="40"></TD>
    <TD><font size="2">e.g. Le Blanc, France</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Landscape</B><B> :</B></font></td>
    <TD>
          <Select Name="landscape" Size="1">
           <Option Value="" Selected>
           <Option Value="Agricultural_land">Agricultural_land</Option>
           <Option Value="Botanical_garden_zoo">Botanical_garden_zoo</Option>
           <Option Value="Dry_shrubland">Dry_shrubland</Option>
           <Option Value="Wet_shrubland">Wet_shrubland</Option>
           <Option Value="Forest">Forest</Option>
           <Option Value="Oasis">Oasis</Option>
           <Option Value="Rural_garden">Rural_garden</Option>
           <Option Value="Urban_garden">Urban_garden</Option>
           <Option Value="Wild_grassland">Wild_grassland</Option>
          </Select></TD>
     <td></td>
  </tr>
  <tr><td></td></tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Substrate</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="substrate" Size="40"></TD>
    <TD><font size="2">e.g. compost heap; live_arthropod, Oniscus asellus; rotting_stem, banana</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Associated Organism</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="assoc_organism" Size="40"></TD>
    <TD><font size="2">e.g. Bacteria JUb123-125</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Life stage</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="life_stage" Size="40"></TD>
    <TD><font size="2">Stage on day of sampling e.g. dauer. Leave blank if unknown.</font></TD>
  </tr>
  <tr><td></td></tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Log size of population</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="log_population" Size="40"></TD>
    <TD><font size="2">2 if 10-100 individuals in the sample, etc.</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Sampled by</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="sampled_by" Size="40"></TD>
    <TD><font size="2">The person who collected the sample e.g. Ray Hong</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Isolated by</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="isolated_by" Size="40"></TD>
    <TD><font size="2">The person who isolated the worms from the sample e.g. Marie-Anne Felix</font></TD>
  </tr>
  $tr_blue
    <TD ALIGN="right">$normal_font<B>Date of sampling</B></FONT><B> :</B> <BR>
    <TD><Input Type="Text" Name="date" Size="40"></TD>
    <TD><font size="2">dd/mm/yyyy e.g. 23/02/1984</font></TD>
  </tr>

  <TR><td>&nbsp;</td></tr>
  </tr>
    <TD ALIGN="right">$normal_font<B>Comment</B></FONT><B> :</B> <BR>
    <TD colspan="2"><textarea Name="comment" rows="4" cols="40"></textarea></TD>
    <TD></TD>
  </tr>
  <tr>
  <td align="center">Clicking Submit will email you a confirmation :</td>
  <td><input type="submit" name="action" value="Submit">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
   <input name="reset" type="reset" value="Reset">
  </td>
  </tr>
</table>
</table>
</form>

<!--my @all_vars = qw ( person_evidence submitter_email strain_name species species_other genotype location inbreeding gps_one gps_two place landscape assoc_organism life_stage log_population sampled_by isolated_by date );-->

</body>
</html>








EndOfText
}

sub findName {
  my $name = shift;
  if ($name !~ /\w/) { 	# if not a valid name, don't search
  } elsif ($name =~ /^\d+$/) { 		# if name is just a number, leave same
#   } elsif ($name =~ m/[\*\?]/) { 	# if it has a * or ?
#     &processpgwild($name);		# ignore pgwild for now
  } else { 			# if it doesn't do simple aka hash thing
    my %aka_hash = &getPgHash();
    my ($names) = &processakasearch($name, %aka_hash);
    return $names;
  }
} # sub findName

sub processakasearch {			# get generated aka's and try to find exact match
  my ($name, %aka_hash) = @_;
  my $search_name = lc($name);
  $search_name =~ s/[^ \w\'\-]//g; 
#   print "<table>\n";
  unless ($aka_hash{$search_name}) {
#     print "<tr><td>name <font color=red>$name</font> not found</td></tr>\n";
    my @names = split/\s+/, $search_name; $search_name = '';
    foreach my $name (@names) {
      if ($name =~ m/^[a-za-z]$/) { $search_name .= "$name "; }
      else { $search_name .= '*' . $name . '* '; }
    }
#     &processpgwild($name);	# ignore pgwild for now
  } else {
    my %standard_name;
    my $result = $dbh->prepare ( "select * from two_standardname;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow ) {
      $standard_name{$row[0]} = $row[2];
    } # while (my @row = $result->fetchrow )
    my %names;

#     print "<tr><td colspan=2 align=center>name <font color=red>$name</font> could be : </td></tr>\n";
#     $keith_body .= "name $name could be : \n";		# changed for Mary Ann 2006 05 10
#     $keith_body .= "Allele submission from $name (possibly ";
    my @stuff = sort {$a <=> $b} keys %{ $aka_hash{$search_name} };
    foreach $_ (@stuff) { 		# add url link
      my $joinkey = 'two'.$_;
      my $person = 'WBPerson'.$_;
      $names{"$standard_name{$joinkey} $person"}++;
#       $keith_body .= "\t$standard_name{$joinkey} $person\n";
#       $keith_body .= "\t$standard_name{$joinkey} $person";	# changed for Mary Ann 2006 05 10
#       print "<tr><td>$standard_name{$joinkey}</td><td><a href=http://www.wormbase.org/db/misc/etree?name=${person};class=person>$person</a></td></tr>\n";
    } 
    my @names = keys %names;
    my $names = join ", ", @names;
    return ($names);
#     $keith_body .= ")\n";

  }
#   unless ($keith_body) { 
#     $keith_body .= $name . " has no match, look here for possible matches : \n";
#     $name =~ s/\s+/+/g;
#     $keith_body .= 'http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person_name.cgi?action=Submit&name=' . "$name\n"; }
#   print "</TABLE>\n";
} # sub processakasearch

sub getPgHash {				# get akaHash from postgres instead of flatfile
  my $result;
  my %filter;
  my %aka_hash;
  
  my @tables = qw (first middle last);
  foreach my $table (@tables) { 
    $result = $dbh->prepare ( "SELECT * FROM two_aka_${table}name WHERE two_aka_${table}name IS NOT NULL AND two_aka_${table}name != 'NULL' AND two_aka_${table}name != '';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( my @row = $result->fetchrow ) {
      if ($row[3]) { 					# if there's a time
        my $joinkey = $row[0];
        $row[2] =~ s/^\s+//g; $row[2] =~ s/\s+$//g;	# take out spaces in front and back
        $row[2] =~ s/[\,\.]//g;				# take out commas and dots
        $row[2] =~ s/_/ /g;				# replace underscores for spaces
        $row[2] = lc($row[2]);				# for full values (lowercase it)
        $row[0] =~ s/two//g;				# take out the 'two' from the joinkey
        $filter{$row[0]}{$table}{$row[2]}++;
        my ($init) = $row[2] =~ m/^(\w)/;		# for initials
        $filter{$row[0]}{$table}{$init}++;
      }
    }
    $result = $dbh->prepare ( "SELECT * FROM two_${table}name WHERE two_${table}name IS NOT NULL AND two_${table}name != 'NULL' AND two_${table}name != '';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while ( my @row = $result->fetchrow ) {
      if ($row[3]) { 					# if there's a time
        my $joinkey = $row[0];
        $row[2] =~ s/^\s+//g; $row[2] =~ s/\s+$//g;	# take out spaces in front and back
        $row[2] =~ s/[\,\.]//g;				# take out commas and dots
        $row[2] =~ s/_/ /g;				# replace underscores for spaces
        $row[2] = lc($row[2]);				# for full values (lowercase it)
        $row[0] =~ s/two//g;				# take out the 'two' from the joinkey
        $filter{$row[0]}{$table}{$row[2]}++;
        my ($init) = $row[2] =~ m/^(\w)/;		# for initials
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
            $possible = "$middle"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $first"; $aka_hash{$possible}{$person}++;
            $possible = "$last $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last $first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last $middle $first"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $first $last"; $aka_hash{$possible}{$person}++;
          } # foreach my $middle (sort keys %{ $filter{$person}{middle}} )
        }
      } # foreach my $first (sort keys %{ $filter{$person}{first}} )
    } # foreach my $last (sort keys %{ $filter{$person}{last}} )
  } # foreach my $person (sort keys %filter) 

  return %aka_hash;
} # sub getPgHash


# sub processpgwild {
#   my $input_name = shift;
#   print "<table>\n";
#   print "<tr><td>input</td><td>$input_name</td></tr>\n";
#   my @people_ids;
#   $input_name =~ s/\*/.*/g;
#   $input_name =~ s/\?/./g;
#   my @input_parts = split/\s+/, $input_name;
#   my %input_parts;
#   my %matches;				# keys = wbid, value = amount of matches
#   my %filter;
#   foreach my $input_part (@input_parts) {
#     my @tables = qw (first middle last);
#     foreach my $table (@tables) { 
#       my $result = $dbh->prepare ( "select * from two_aka_${table}name where lower(two_aka_${table}name) ~ lower('$input_part');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while ( my @row = $result->fetchrow ) { $filter{$row[0]}{$input_part}++; }
#       $result = $dbh->prepare ( "select * from two_${table}name where lower(two_${table}name) ~ lower('$input_part');" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#       while ( my @row = $result->fetchrow ) { $filter{$row[0]}{$input_part}++; }
#     } # foreach my $table (@tables)
#   } # foreach my $input_part (@input_parts)
# 
#   foreach my $number (sort keys %filter) {
#     foreach my $input_part (@input_parts) {
#       if ($filter{$number}{$input_part}) { 
#         my $temp = $number; $temp =~ s/two/wbperson/g; $matches{$temp}++; 
#         my $count = length($input_part);
#         unless ($input_parts{$temp} > $count) { $input_parts{$temp} = $count; }
#       }
#     } # foreach my $input_part (@input_parts)
#   } # foreach my $number (sort keys %filter)
#   
#   print "<tr><td></td><td>there are " . scalar(keys %matches) . " match(es).</td></tr>\n";
#   print "<tr></tr>\n";
#   print "</table>\n";
#   print "<table border=2 cellspacing=5>\n";
#   foreach my $person (sort {$matches{$b}<=>$matches{$a} || $input_parts{$b} <=> $input_parts{$a}} keys %matches) { 
#     print "<tr><td><a href=http://www.wormbase.org/db/misc/etree?name=${person};class=person>$person</a></td>\n";
#     print "<td>has $matches{$person} match(es)</td><td>priority $input_parts{$person}</td></tr>\n";
#   } 
#   print "</table>\n";
#   
#   unless (%matches) {
#     print "<font color=red>sorry, no person named '$input_name', please try again</font><p>\n" if $input_name;
#   }
# } # sub processpgwild


__END__
<tr>
  <td width="50%">
    <!--<table width="99%" height="100%" align="center" cellpadding="1" cellspacing="5" bgcolor="#DCDDE7">-->
    <table width="99%" height="100%" align="center" cellpadding="1" cellspacing="5" bgcolor="#B0CFFA">
     <tr>
        <td colspan="3"><FONT SIZE=+2><B>PHYSICAL</B></FONT></td>
     </tr>
     <TR>
       <TD ALIGN="right"><B>Sequence name<br>of gene :</B></TD>
       <TD><Input Type="Text" Name="sequence" Size="37"><BR>
           <font size="1">(CDS, eg., B0303.3)</font></TD>
     </TR>
     <tr>
       <td colspan="3"><B><font color="#330000">Type of alteration <font color="#000000" size="1"></font></B><font size=1 color="black">&nbsp;</font></td>
     </tr>
     <TR>
      <td>
          <Select Name="types_of_alteration" Size=1 onChange="change_type_P(this.form)">
           <Option Value="" Selected>
           <Option Value="Point">Point / dinucleotide mutation
           <Option Value="Transposon">Transposon Insertion
           <Option Value="Insert">Sequence insertion
           <Option Value="Delete">Sequence deletion
           <Option Value="Indel">Deletion + insertion
           <Option Value="Complex">Complex alterations
          </Select></td>
	  <td><Input Type="text" Name="alteration_text" id="seq_input" Size="37" value="Enter mutation details"></td>
     </TR>
     <TR> 
       <TD></TD>
       <TD><Input Type="text" Name="indel_seq" id ="indel_input" Size="37" value="do not use, for insertion + deletion only"></TD>
     </TR>
     <TR>
       <TD colspan="3"><B><font color="#330000">Flanking sequences</font></B><font size=1> (necessary to map allele to the genome)</font></TD>
     </TR>
     <TR>
       <TD align="right"><B>30 bp upstream :</B></TD>
       <TD><Input Type="Text" Name="upstream" Size="37"></TD>
     </TR>
     <TR>
       <TD align="right"><B>30 bp downstream :</B></TD>
       <TD><Input Type="Text" Name="downstream" Size="37"><BR>
           <FONT SIZE=1>It is only necessary to enter longer flanking sequences if 30bp is not a unique sequence e.g. in a highly repetitive or duplicated region.</FONT></TD>
     </TR>
     <tr>
       <td ALIGN="left" colspan="3"><B><font color="#330000">Origin</font></B></td>
     </tr>
     <TR>
       <TD width="42%" ALIGN="right"><B>Strain :</B></TD>
       <TD width="19%" ALIGN="left"><Input Type="text" Name="strain" Size="37"><BR>
       <!--<TD width="39%">--><font size="1">(Strain in which the allele is maintained, eg, TR1417. If CGC strain, genotype can be omitted)<BR></TD>
     </TR>
     <TR> 
       <TD width="42%" ALIGN="right"><B>Genotype :</B></TD>
       <TD width="19%" ALIGN="left"><Input Type="text" Name="genotype" Size="37"><BR>
       <!--<TD width="39%">--><font size="1">(eg, smg-1 (r904) unc-54 (r293) I)</font></td>
     </TR>
     <TR>
       <TD ALIGN="left"><B><font color="#330000">Isolation</font></B></TD>
     </TR>
     <TR>
       <TD align="right"><B>Mutagen :</B></TD>
       <TD><Input Type="Text" Name="mutagen" Size="37"><BR>
       <font size="1">(eg. EMS, ENU, TMP/UV)</font></TD>
     </TR>
     <TR>
       <TD ALIGN="right"><strong>Forward genetics:</strong></TD>
       <TD><Input Type="Text" Name="forward" Size="37"><BR>
       <font size="1">&nbsp;(standard phenotypic screen)</font></TD>
     </TR>
     <TR>
       <TD ALIGN="right"><strong>Reverse genetics:</strong></TD>
       <TD><Input Type="Text" Name="reverse" Size="37"><BR>
       <font size="1">&nbsp;(directed screen for mutations in a particular gene, using eg, PCR or Tilling) </font></TD>
     </TR>
     <TR>
       <td ALIGN="left"><B><font color="#330000">Type of mutation</font></B></td>
       <td colspan="2">&nbsp;</td>
     </TR>
     <TR>
        <TD colspan=3 align="center">
          <Select Name="types_of_mutations" Size=1 onChange="change_type_G(this.form)">
            <Option Value="" Selected>
            <Option Value="Missense">Missense
            <Option Value="Nonsense">Nonsense
            <Option Value="Silent">Silent
            <Option Value="Splice-site">Splice-site
            <Option Value="Frameshift">Frameshift</Select>
          <Input Type="Text" Name="mutation_info" id="mutation" Size="54" value="Enter mutation details">
       	 </TD>
     </TR>
     <TR></TR><TR></TR><TR></TR><TR></TR>
    </table>
  </td>
   <td width="50%">
<!--    <table width="99%" height="100%" align="center" cellpadding="1" cellspacing="5" bgcolor="#FFFF80">-->
    <table width="99%" height="100%" align="center" cellpadding="1" cellspacing="5" bgcolor="#B0CFFA">
      <tr>
        <td colspan="3"><FONT SIZE=+2><B>GENETIC</B></FONT></td>
      </tr>
<!--      <tr>
        <TD ALIGN="left"><B><font color="#330000">Phenotypic description</font></B></TD>
        <TD colspan="3"></TD>
      </tr>
      <TR>
        <TD ALIGN="right"><B>Phenotypic description :<BR><FONT SIZE=-1 COLOR=red>* Required if any data is entered in the below fields</FONT></B></TD>
        <TD><TEXTAREA Name="phenotypic_description" Rows=3 Cols=28></TEXTAREA>
      </TR>-->
      <tr> 
        <td colspan="3"><B>Please enter <font color="#330000">phenotypes</font> that you observed or that you assayed for and did not observe in the appropriate space below.  
<!--           <a href='javascript:window.alert("<p>Welcome to our online allele submission form!</p> \n
   1. ‘Positive  phenotypes’ refer to phenotypes observed by the user. ‘NOT phenotypes’ refer to phenotypes that have been assayed for and not observed.<br/>
   2. Individual phenotype terms can be perused by entering a term name, synonym or ID in the ‘Positive Phenotype’ or ‘NOT Phenotype’ fields (e.g. dumpy, Dpy, WBPhenotype:0000583).  Any phenotype term recorded in the adjacent list field will get annotated by a WormBase curator unless the submitter deletes it prior to submission (see step 3).<br/>
   3. In order to delete a term, select the desired term within the list and hit the ‘Del’ button at the lower right of the corresponding list field.<br/>
   4. The Display of phenotype information field is a non-editable field that displays the current term name, ID, definition, synonyms (if applicable) and its parent-child relationships.<br/>
   5. Users can browse the tree-view of the phenotype ontology by clicking the purple link.<br/>
   6. Details such as temperature sensitivity, allele nature etc. can be entered by clicking the appropriate value from the drop down menu.<br/>
   7. To propose a new term/definition, please enter your comments in the ‘Suggest new term and definition’. If you have any additional suggestions regarding the content or placement of existing phenotype terms within the ontology, please enter your comments in the ‘Suggest new term and definition’ as well.<br/>
   8. Please review your entries and click ‘Submit’ when ready.<br/>
      Thanks for your submission! <br/>
      -Team Phenotype<br/>");'>(view instructions)</a>-->
           <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/allele.cgi?action=instructions" target="new">(view instructions)</a>
</B></td>
      </tr>
      <tr>
        <td colspan="3" align="left">Click <b><u><a href="http://elbrus.caltech.edu/cgi-bin/igor/ontology/ontology.cgi?ontology=phenotype" target="new">here</a></u></b> to browse phenotype ontology</td>
      </tr>
      <tr> 
        <TD ALIGN="right"><B><font color="grey">Display of phenotype information :</B></font></td>
        <td colspan="2"><textarea id="phenontObo" rows="10" cols="50" readonly="readonly"></textarea></td>
      </tr>
      <tr> 
        <TD ALIGN="right" valign="top"><FONT SIZE=-1 COLOR=red>1</FONT> <B>Enter Positive Phenotypes :</B><br />
          <style="font-family: arial;"><i>click del to delete phenotype</i></style>
        </td>
        <td colspan="2" valign="top">
          <span id="containerForcedPhenontAutoComplete">
            <div id="forcedPhenontAutoComplete">
                  <input size="25" id="forcedPhenontInput" type="text" >
                  <div id="forcedPhenontContainer"></div>
            </div></span>
          <input type="hidden" name="pos_phenont" id="pos_phenont">
          <select name="selectPhenont" id="selectPhenont" multiple="multiple" size="0" onchange="PopulatePhenontObo('Phenont', 'select')" >
          </select>
          <input type="button" value="del" onclick="RemoveSelected('Phenont')">
        </td>
      </tr>
      <tr> 
        <TD ALIGN="right" valign="top"><FONT SIZE=-1 COLOR=red>2</FONT> <B>Enter NOT Phenotypes :</b><br />
          <style="font-family: arial;"><i>click del to delete phenotype</i></style>
        </td>
        <td colspan="2" valign="top">
          <span id="containerNotPhenontAutoComplete">
            <div id="notPhenontAutoComplete">
                  <input size="25" id="notPhenontInput" type="text" >
                  <div id="notPhenontContainer"></div>
            </div></span>
          <input type="hidden" name="not_phenont" id="not_phenont">
          <select name="selectNotPhenont" id="selectNotPhenont" multiple="multiple" size="0" onchange="PopulatePhenontObo('NotPhenont', 'select')" >
          </select>
          <input type="button" value="del" onclick="RemoveSelected('NotPhenont')">
        </td>
      </tr>
EndOfText

    print <<"EndOfText";
<script type="text/javascript">
YAHOO.example.BasicRemote = function() {
    // Use an XHRDataSource
    var oDS = new YAHOO.util.XHRDataSource("http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/autocomplete/phenont_autocomplete.cgi");

    // Set the responseType
    oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;
    // Define the schema of the delimited results
    oDS.responseSchema = {
        recordDelim: "\\n",
        fieldDelim: "\\t"
    };
    oDS.maxCacheEntries = 5;		// Enable caching

    // Instantiate the AutoComplete
    var forcedOAC = new YAHOO.widget.AutoComplete("forcedPhenontInput", "forcedPhenontContainer", oDS);
    forcedOAC.maxResultsDisplayed = 20;
    forcedOAC.forceSelection = true;
    forcedOAC.itemSelectEvent.subscribe(onItemSelect);
    forcedOAC.itemArrowToEvent.subscribe(onItemHighlight);
    forcedOAC.itemMouseOverEvent.subscribe(onItemHighlight);
    return {
        oDS: oDS,
        forcedOAC: forcedOAC
    };
}();
</script>
<script type="text/javascript">
YAHOO.example.BasicRemote = function() {
    // Use an XHRDataSource
    var oDS = new YAHOO.util.XHRDataSource("http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/autocomplete/phenont_autocomplete.cgi");

    // Set the responseType
    oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;
    // Define the schema of the delimited results
    oDS.responseSchema = {
        recordDelim: "\\n",
        fieldDelim: "\\t"
    };
    oDS.maxCacheEntries = 5;		// Enable caching

    // Instantiate the AutoComplete
    var notOAC = new YAHOO.widget.AutoComplete("notPhenontInput", "notPhenontContainer", oDS);
    notOAC.maxResultsDisplayed = 20;
    notOAC.forceSelection = true;
    notOAC.itemSelectEvent.subscribe(onNotSelect);
    notOAC.itemArrowToEvent.subscribe(onNotHighlight);
    notOAC.itemMouseOverEvent.subscribe(onNotHighlight);
    return {
        oDS: oDS,
        notOAC: notOAC
    };
}();
</script>

      <tr> 
        <td colspan="2" valign="top"><b>If you are unable to find the phenotype you are looking for in the phenotype ontology, please suggest a new term and its definition in the section below, <u>OR</u> type ``no phenotype''.</b></td>
      </tr>
      <tr> </tr>
      <tr> 
        <TD ALIGN="right" valign="top"><FONT SIZE=-1 COLOR=red>3</FONT> <B>Suggest new term and definition :</B></td>
        <td colspan="2" valign="top"><textarea name="suggest_new" id="suggest_new" rows="5" cols="50"></textarea></td>
      </tr>
     

      <tr>
        <TD ALIGN="left"><B><font color="#330000">Allele Nature</font></B></TD>
        <td ALIGN="left" colspan="1" ><B>
          <!--Recessive :    <Input Type="radio" Name = "nature_of_allele" Value="recessive">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          Semi-dominant :<Input Type="radio" Name = "nature_of_allele" Value="semi_dominant">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          Dominant :     <Input Type="radio" Name = "nature_of_allele" Value="dominant"></td>-->
          <select name="nature_of_allele">
             <option value="" Selected></option>
             <option value="recessive">Recessive</option>
             <option value="semi_dominant">Semi-dominant</option>
             <option value="dominant">Dominant</option>
          </select></td>
      </tr>
      <tr>
        <TD ALIGN="left"><B><font color="#330000">Allele Function</font></B></TD>
        <td ALIGN="left" colspan="1" ><B>
          <select name="nature_of_allele">
             <option value="" Selected></option>
             <option value="Amorph">Amorph</option>
             <option value="Dominant Negative">Dominant Negative</option>
             <option value="Gain_of_function">Gain_of_function</option>
             <option value="Haplo-insufficient">Haplo-insufficient</option>
             <option value="Hypermorph">Hypermorph</option>
             <option value="Hypomorph">Hypomorph</option>
             <option value="Loss_of_function">Loss_of_function</option>
             <option value="Neomorph">Neomorph</option>
             <option value="Uncharacterised_gain_of_function">Uncharacterised_gain_of_function</option>
             <option value="Uncharacterised_loss_of_function">Uncharacterised_loss_of_function</option>
          </select></td>
      </tr>
      <!--<TR>
        <TD ALIGN="right"><B>Haploinsufficient :</B></TD>
        <TD><Input Type="checkbox" Name="haploinsufficient" Value="haploinsufficient"></TD>
      </TR>
      <TR>
        <TD ALIGN="right"><B>Loss of Function :</B></TD>
        <TD><Select Name="loss_of_function"  Size=1>
             <Option Value="" Selected>
             <Option Value="Uncharacterised_loss_of_function">Uncharacterised_loss_of_function
             <Option Value="Hypomorph">Hypomorph
             <Option Value="Amorph">Amorph
            </Select>
        </TD>
      </TR>
      <TR>
        <TD ALIGN="right"><B>Gain of Function :</B></TD>
        <TD><Select Name="gain_of_function"  Size=1>
             <Option Value="" Selected>
             <Option Value="Uncharacterised_gain_of_function">Uncharacterised_gain_of_function
             <Option Value="Hypermorph">Hypermorph
             <Option Value="Neomorph">Neomorph
             <Option Value="Dominant Negative">Dominant Negative
           </Select>
        </TD>
      </TR>-->
      <tr>
        <TD ALIGN="left"><B><font color="#330000">Penetrance</font></B></TD>
        <td ALIGN="left" colspan="1"><B>
		      <!--Complete :<Input Type="radio" Name="penetrance" Value="complete">
		      Partial :<Input Type="radio" Name="penetrance" Value="partial">-->
          <select name="penetrance">
             <option value="" Selected></option>
	     <option value="complete">Complete</option>
	     <option value="partial">Partial</option>
          </select>
        </td>
      </tr>
      </TR>
      <tr>
        <td ALIGN="left" colspan="1"><B><font color="#330000">Temperature Sensitive</font></B></td>
        <td ALIGN="left" colspan="3"><B>
          <select name="heat_sensitive">
             <option value="" Selected></option>
	     <option value="heat_sensitive">Heat Sensitive</option>
	     <option value="cold_sensitive">Cold Sensitive</option>
          </select>
        </td>
      </tr>
      <!--<TR>
        <TD ALIGN="right"><B>Heat sensitive :</B></TD>
        <TD><Input Type="checkbox" Name="heat_sensitive" Value="heat_sensitive">
            <Input Type="Text" Name="hot_temp" Size="32"><BR>
        <font size="1">(If available. Temp. [Celsius] at which phenotype observed, eg. 12C-15C or 30C)</font></TD>
      </TR>
      <TR>
        <TD ALIGN="right"><B>Cold sensitive :</B></TD>
        <TD><Input Type="checkbox" Name="cold_sensitive" Value="cold_sensitive">
            <Input Type="Text" Name="cold_temp" Size="32"></TD>
      </TR>-->
    </table>
  </td>
  </tr>
  <tr></tr><tr></tr><tr></tr><tr></tr><tr></tr><tr></tr>
  <table>
   <td width="1138" colspan="2" align="center"><div align="center">
     <strong><font color="#000000">Other allele comments: 
     <textarea name="comment" cols="50" rows="3"></textarea>
     </font>     </strong>   </div></td>
  </table>
  <table align="center">
  <td align="center">Clicking Submit will email you a confirmation :
   <input type="submit" name="action" value="Submit" onClick="populateSelectFields()">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
   <input name="reset" type="reset" value="Reset" onClick="rollback()">
  </td>
 </table>
<hr>
<a href="mailto:webmaster\@www.wormbase.org">webmaster\@www.wormbase.org</a><a href="http://www.wormbase.org/copyright.html">&nbsp;&nbsp;&nbsp;Copyright
    Statement</a><a href="http://www.wormbase.org/db/misc/feedback">&nbsp;&nbsp;&nbsp;Send comments or questions to WormBase</a></td> <td class="small" align="right"><a href="http://www.wormbase.org/privacy.html">&nbsp;&nbsp;&nbsp;Privacy Statement</a></td></tr>





 	    elsif ($var eq 'haploinsufficient') {		# haploinsufficient
              my ($var, $haploinsufficient) = &getHtmlVar($query, 'haploinsufficient');
              $ace_body .= "$haploinsufficient\n"; } 
 	    elsif ($var eq 'loss_of_function') {		# loss and gain only show value (which is tag)
              my ($var, $loss_of_function) = &getHtmlVar($query, 'mutation_info');
              $ace_body .= "$loss_of_function\n"; } 
 	    elsif ($var eq 'gain_of_function') {
              my ($var, $gain_of_function) = &getHtmlVar($query, 'mutation_info');
              $ace_body .= "$gain_of_function\n"; } 
 	    elsif ($var eq 'types_of_mutations') {
              my ($var, $mutation_info) = &getHtmlVar($query, 'mutation_info');
              if ( ($mutation_info =~ m/^eg\, /) || ($mutation_info eq 'please specify') ) { $ace_body .= "$val\n"; }
              else { $ace_body .= "$val\t\"$mutation_info\"\n"; } }
# 	    elsif ($var eq 'assoc_strain') {
#               my ($var, $assoc_strain) = &getHtmlVar($query, 'assoc_strain');
#               if ($assoc_strain) {
#                 my @pairs = split /\n/, $assoc_strain;
#                 foreach (@pairs) {
#                   my ($genotype, $strain) = split/\t/, $_;
# 		  $strain =~ s///g;
# 	          $ace_body .= "Strain\t\"$strain\"\n";
# 	          $strain_body .= "Strain : \"$strain\"\n";
# 	          $strain_body .= "Genotype\t\"$genotype\"\n";
# 	          $strain_body .= "Allele\t\"$allele\"\n\n";
#                 }
#               }
#             }
#             elsif ($var eq 'paper_evidence') {
#               my ($var, $paper_evidence) = &getHtmlVar($query, 'paper_evidence');
#               if ( ($paper_evidence =~ m/cgc/) || ($paper_evidence =~ m/pmid/) ) {
# #                 $ace_body .= "Reference\t\"$paper_evidence\" XREF $allele\n";
#                 $ace_body .= "Reference\t\"$paper_evidence\"\n";
#               } elsif ( ($paper_evidence =~ m/CGC/) || ($paper_evidence =~ m/PMID/) ) {
#                 $paper_evidence =~ s/CGC/cgc/g; $paper_evidence =~ s/PMID/pmid/g;
# #                 $ace_body .= "Reference\t\"$paper_evidence\" XREF $allele\n";
#                 $ace_body .= "Reference\t\"$paper_evidence\"\n";
#               } else { $ace_body .= "Remark\t\"$paper_evidence\"\n"; }
#             }
            elsif ($var eq 'penetrance') {
              my ($var, $penetrance) = &getHtmlVar($query, 'penetrance');
              if ($penetrance eq 'complete') { 
                $ace_body .= "Penetrance\t\"Complete\"\n";
              }
            }
	    elsif ($var eq 'species') { 
              my ($var, $species_other) = &getHtmlVar($query, 'species_other');
	      $val =~ s///g; $val =~ s/\n//g;
	      unless ($species_other) { $ace_body .= "Species\t\"$val\"\n"; }
            }
            elsif ($var eq 'types_of_alteration') {
              my ($var, $alteration_text) = &getHtmlVar($query, 'alteration_text');
              if ( ($alteration_text =~ m/^eg\, /) || ($alteration_text =~ m/^enter /) ) { $ace_body .= "$val\n"; }
              else { 		# if real data entered
                my ($var, $types_of_alteration) = &getHtmlVar($query, 'types_of_alteration');
                if ($types_of_alteration eq 'Point') { 
                  $ace_body .= "Substitution\t\"$alteration_text\"\n"; 
                  $ace_body .= "Method\t\"Substitution_allele\"\n"; }
                elsif ($types_of_alteration eq 'Transposon') { 
                  my ($var, $alteration_text) = &getHtmlVar($query, 'alteration_text');
                  $ace_body .= "Transposon_insertion\t\"$alteration_text\"\n"; 
                  $alteration_text = lc($alteration_text);
                  if ($alteration_text =~ m/tc/) {
                    $ace_body .= "Method\t\"Transposon_insertion\"\n"; }
                  elsif ($alteration_text =~ m/mos/) {
                    $ace_body .= "Method\t\"Mos_insertion\"\n"; }
                  else {
                    $ace_body .= "Method\t\"Unknown\"\n"; } }
                elsif ($types_of_alteration eq 'Insert') { 
                  $ace_body .= "Insertion\t\"$alteration_text\"\n"; 
                  $ace_body .= "Method\t\"Insertion_allele\"\n"; }
                elsif ($types_of_alteration eq 'Delete') { 
                  $ace_body .= "Deletion\t\"$alteration_text\"\n"; 
                  $ace_body .= "Method\t\"Deletion_allele\"\n"; }
                elsif ($types_of_alteration eq 'Indel') { 
                  my ($var, $indel_seq) = &getHtmlVar($query, 'indel_seq');
                  $ace_body .= "Deletion_with_insertion\t\"$indel_seq\"\n"; 
                  $ace_body .= "Method\t\"Deletion_and_insertion_allele\"\n"; }
                elsif ($types_of_alteration eq 'Complex') { 
                  $ace_body .= "Method\t\"Allele\"\n"; }
                else {
                  $ace_body .= "Method\t\"Unknown\"\n"; }
              } # else # if ( ($alteration_text =~ m/^eg\, /) || ($alteration_text =~ m/^enter /) )
            } # elsif ($var eq 'types_of_alteration')
#             elsif ($var eq 'point_mutation_gene') { 1; }	# do nothing, but append to body
#             elsif ($var eq 'transposon_insertion') { 1; }	# do nothing, but append to body
#             elsif ($var eq 'sequence_insertion') { 1; }	# do nothing, but append to body
#             elsif ($var eq 'deletion') { 1; }		# do nothing, but append to body
#             elsif ($var eq 'alteration_type') { 
#               my ($var, $alteration_type) = &getHtmlVar($query, 'alteration_type');
#               if ($alteration_type eq 'point_mutation_gene') {
#                 my $ace_val = $val;
#                 if ($ace_val =~ m/([aAcCtTgG]+) [tT][oO] ([aAcCtTgG]+)/) { 
#                   my $first = uc($1); my $second = uc($2);
#                   $ace_val = '[' . $first . '\/' . $second . ']'; 
#                 }
# 	          $ace_val =~ s///g; $ace_val =~ s/\n//g;
#                 $ace_body .= "Allelic_difference\t\"$ace_val\"\n";
#               }
#               elsif ($alteration_type eq 'transposon_insertion') {
#                 my ($var, $transposon_insertion) = &getHtmlVar($query, 'transposon_insertion');
# 	        $transposon_insertion =~ s///g; $transposon_insertion =~ s/\n//g;
# 	        $ace_body .= "Transposon_insertion\t\"$transposon_insertion\"\n";
# 		$keith_method = 'Transposon_insertion';
#               }
#               elsif ($alteration_type eq 'sequence_insertion') {
#                 my ($var, $sequence_insertion) = &getHtmlVar($query, 'sequence_insertion');
# 	        $ace_body .= "Insertion\n";
# 	        $val = substr($sequence_insertion, 0, 30);
# 	         $val =~ s///g; $val =~ s/\n//g;
# 	        $ace_body .= "Remark\t\"Insertion sequence: $val\"\n";
#               }
#               elsif ($alteration_type eq 'deletion') {
#                 my ($var, $deletion) = &getHtmlVar($query, 'deletion');
# 	        $ace_body .= "Deletion\n";
# 	        $val = substr($deletion, 0, 30);
# 	        $val =~ s///g; $val =~ s/\n//g;
# 	        $ace_body .= "Deletion\t\"Deleted sequence: $val\"\n";
# 		$keith_method = 'Deletion_allele';
#               }
# 	    } # elsif ($var eq 'alteration_type')	# append to ace entry if proper
	    elsif ($var eq 'nature_of_allele') {
	      if ($val eq 'recessive') { $ace_body .= "Recessive\n"; }
	      elsif ($val eq 'semi_dominant') { $ace_body .= "Semi_dominant\n"; }
	      elsif ($val eq 'dominant') { $ace_body .= "Dominant\n"; }
	      else { print "ERROR : $var and $val don't have a matching Ace tag<BR>\n"; }
	    }					# append to ace entry if proper
	    elsif ($var eq 'heat_sensitive') {
              my ($var, $hot_temp) = &getHtmlVar($query, 'hot_temp');
              $ace_body .= "Heat_sensitive\t\"$hot_temp\"\n"; 
            }
	    elsif ($var eq 'cold_sensitive') { 
              my ($var, $cold_temp) = &getHtmlVar($query, 'cold_temp');
              $ace_body .= "Cold_sensitive\t\"$cold_temp\"\n"; 
	    }					# append to ace entry if proper
	    elsif ($var eq 'upstream') {		# now includes downstream for .ace
              my $flanking_seq = $val;
              my ($var, $val) = &getHtmlVar($query, 'downstream');
              $flanking_seq .= "\"\t\"" . $val;
	      $flanking_seq =~ s///g; $flanking_seq =~ s/\n//g;
	      $ace_body .= "Flanking_sequences\t\"$flanking_seq\"\n"; 
	    }					# append to ace entry if proper
            elsif ($field eq 'pos_phenont') { $ace_body .= "Positive Phenotype\t$val\n"; }
            elsif ($field eq 'not_phenont') { $ace_body .= "NOT Phenotype\t$val\n"; }
            elsif ($field eq 'suggest_new') { $ace_body .= "Suggested Phenotype\t$val\n"; }







              # normal $body output for email mostly straightforward
            if ($var eq 'indel_seq') { 1; }	# ignore indel_seq deal under types_of_alteration
            elsif ($var eq 'alteration_text') { 1; }	# ignore indel_seq deal under types_of_alteration
            elsif ($var eq 'types_of_alteration') {
              my ($var, $alteration_text) = &getHtmlVar($query, 'alteration_text');
                if ($val eq 'Point') { $body .= "Substitution\t\"$alteration_text\"\n"; }
                elsif ($val eq 'Transposon') { $body .= "Transposon_insertion\t\"$alteration_text\"\n"; }
                elsif ($val eq 'Insert') { $body .= "Insertion\t\"$alteration_text\"\n"; }
                elsif ($val eq 'Delete') { $body .= "Deletion\t\"$alteration_text\"\n"; }
                elsif ($val eq 'Complex') { $body .= "Complex\t\"$alteration_text\"\n"; }
                elsif ($val eq 'Indel') { 
                  my ($var, $indel_seq) = &getHtmlVar($query, 'indel_seq');
                  $body .= "Deletion\t\"$alteration_text\"\n"; 
                  $body .= "Insertion\t\"$indel_seq\"\n"; }
                else { $body .= "$var\t\"$val\"\n"; } }
            elsif ($var eq 'mutation_info') {	# ignore mutation info if used didn't change data
              if ($val eq 'Enter mutation details') { 1; } }
            else { $body .= "$var\t\"$val\"\n"; }	# output most fields normally

