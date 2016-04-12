#!/usr/bin/perl 

# Form to submit WikiPathways for WormBase

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
# modified community_gene_description.cgi and allele.cgi.  javascript at 
# ~/public_html/javascript/pathway.js  2013 06 20




use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;
use Tie::IxHash;
use LWP::Simple;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";




my $query = new CGI;


my @all_vars = qw ( firstname lastname submitter_email species gene concise_description pmids pmid_titles );
my %mandatory;
# $mandatory{"firstname"}++;
# $mandatory{"lastname"}++;
# $mandatory{"submitter_email"}++;
# $mandatory{"species"}++;
# $mandatory{"gene"}++;
# $mandatory{"concise_description"}++;
# $mandatory{"pmids"}++;
$mandatory{"name"}++;
$mandatory{"submitter_email"}++;
$mandatory{"pathwaylogin"}++;
$mandatory{"pathwayname"}++;
$mandatory{"pathwayid"}++;
$mandatory{"species"}++;
  

my $title = 'WikiPathways for WormBase Submission Form';
my ($header, $footer) = &cshlNew($title);

# $header = "<html><head></head>";

# <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css" />	# this makes it look nicer, but messes with the alignment of the input field
my $extra_stuff = << "EndOfText";
<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/autocomplete/assets/skins/sam/autocomplete.css" />
<link rel="stylesheet" type="text/css" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" />
<link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.7.0/build/fonts/fonts-min.css" />
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/yahoo-dom-event/yahoo-dom-event.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/connection/connection-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/datasource/datasource-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.7.0/build/autocomplete/autocomplete-min.js"></script>
<script type="text/javascript" src="/~azurebrd/javascript/pathway.js"></script>
<script type="text/JavaScript">
<!--Your browser is not set to be Javascript enabled 
//-->
</script>

<style type="text/css">
#forcedProcessAutoComplete {
    width:30em; /* set width here or else widget will expand to fit its container */
    padding-bottom:2em;
}
</style>

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
$header =~ s/<\/head>/$extra_stuff\n<\/head>/;




# print "$header\n";		# make beginning of HTML page

# my %pmidToWBPaper;		# key pmid digits, value wbpaper digits

&process();			# see if anything clicked
# print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'Submit') {              &submit();          }
  elsif ($action eq 'autocompleteXHR') {  &autocompleteXHR(); }
#   elsif ($action eq 'pmidToTitle') {      &pmidToTitle();     }
#   elsif ($action eq 'instructions') {   &instructions();    }		# no instructions in this form
  else { &frontPage(); }			# show form as appropriate
} # sub process

sub frontPage {
  print "Content-type: text/html\n\n";
  print $header;
  &displayForm();
  print $footer;
} # sub frontPage

sub autocompleteXHR {
  print "Content-type: text/html\n\n";
  my ($var, $words) = &getHtmlVar($query, 'query');
  unless ($words) { ($var, $words) = &getHtmlVar($query, '?query'); }
  ($var, my $field) = &getHtmlVar($query, 'field');
  if ($field eq 'Process') { &autocompleteProcess($words); }
#   if ($field eq 'Gene') { &autocompleteGene($words); }
#   elsif ($field eq 'Species') { &autocompleteSpecies($words); }
} # sub autocompleteXHR

sub autocompleteProcess {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $lcwords = lc($words);
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my @tables = qw( prt_processname );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' ORDER BY $table;" );
#     print qq( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' ORDER BY $table;" <br/>);
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBProcess"; my $name = $row[1];
      my $result2 = $dbh->prepare( "SELECT * FROM prt_processid WHERE joinkey = '$row[0]';" ); $result2->execute();
      my @row2 = $result2->fetchrow(); $id = $row2[1];
      $matches{"$name ( $id ) "}++;
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$lcwords' AND LOWER($table) !~ '^$lcwords' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBProcess"; my $name = $row[1];
      my $result2 = $dbh->prepare( "SELECT * FROM prt_processid WHERE joinkey = '$row[0]';" ); $result2->execute();
      my @row2 = $result2->fetchrow(); $id = $row2[1];
      $matches{"$name ( $id ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more results exist, type more to narrow your search'); }
  my $matches = join"\n", keys %matches;
  print $matches;
} # sub autocompleteProcess


sub submit {
  print "Content-type: text/html\n\n";
  print $header;
# $mandatory{"firstname"}++;
  my $mandatoryFail = '';
  foreach my $field (sort keys %mandatory) {
    my ($var, $value)                  = &getHtmlVar($query, $field);	
    unless ($value) { $mandatoryFail .= "$field "; } }
  if ($mandatoryFail) { 
      print qq(<b><font color="red">You failed to enter data in mandatory fields : $mandatoryFail</font></b><br/>\n);
      &displayForm(); }
    else {
      my $var;
#       my ($firstname, $lastname, $submitter_email, $species, $gene, $concise_description, $pmids, $pmid_titles) = ('', '', '', '', '', '', '', '');
#       ($var, $firstname)                  = &getHtmlVar($query, 'firstname');	
#       ($var, $lastname)                   = &getHtmlVar($query, 'lastname');	
#       ($var, $submitter_email)            = &getHtmlVar($query, 'submitter_email');
#       ($var, $species)                    = &getHtmlVar($query, 'species');	
#       ($var, $gene)                       = &getHtmlVar($query, 'gene');	
#       ($var, $concise_description)        = &getHtmlVar($query, 'concise_description');	
#       ($var, $pmids)                      = &getHtmlVar($query, 'pmids');	
#       ($var, $pmid_titles)                = &getHtmlVar($query, 'pmid_titles');	
      my ($name, $submitter_email, $pathwaylogin, $pathwayname, $pathwayid, $species, $associatedprocess, $suggestedprocess, $comment) = ('', '', '', '', '', '', '', '', '');
      ($var, $name)                       = &getHtmlVar($query, 'name');	
      ($var, $submitter_email)            = &getHtmlVar($query, 'submitter_email');
      ($var, $pathwaylogin)               = &getHtmlVar($query, 'pathwaylogin');
      ($var, $pathwayname)                = &getHtmlVar($query, 'pathwayname');
      ($var, $pathwayid)                  = &getHtmlVar($query, 'pathwayid');
      ($var, $species)                    = &getHtmlVar($query, 'species');	
      ($var, $associatedprocess)          = &getHtmlVar($query, 'associatedprocess');
      ($var, $suggestedprocess)           = &getHtmlVar($query, 'suggestedprocess');
      ($var, $comment)                    = &getHtmlVar($query, 'comment');
      my $user = 'pathway_cgi_form';	# who sends mail
      my $email = 'karen@wormbase.org';	# to whom send mail 2013 06 19
#       my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
      my $subject = 'WikiPathway Form Submission';		# subject of mail
      my $body = '';			# body of mail
#       if ($firstname) 			{ $body .= "Firstname : $firstname\n"; }
#       if ($lastname) 				{ $body .= "Lastname : $lastname\n"; }
#       if ($submitter_email) 			{ $body .= "Email : $submitter_email\n"; }
#       if ($species) 				{ $body .= "Species : $species\n"; }
#       if ($gene) 				{ $body .= "Gene : $gene\n"; }
#       if ($concise_description) 		{ $body .= "Concise_description : $concise_description\n"; }
#       if ($pmids) 				{ $body .= "PMIDs : $pmids\n"; }
#       if ($pmid_titles) 			{ $body .= "PMIDs_to_titles : $pmid_titles\n"; }
#       my (@pmids) = $pmids =~ m/(\d+)/g;
#       &populatePmidToWBPaper();
#       foreach my $pmid (@pmids) { 
#         unless ($pmidToWBPaper{$pmid}) { $body .= qq(No WBPaper for $pmid\n); } } 
      if ($name) 				{ $body .= "Name : $name\n"; }
      if ($submitter_email) 			{ $body .= "Email : $submitter_email\n"; }
      if ($pathwaylogin) 			{ $body .= "Pathway login : $pathwaylogin\n"; }
      if ($pathwayname) 			{ $body .= "Pathway name : $pathwayname\n"; }
      if ($pathwayid) 				{ $body .= "Pathway id : $pathwayid\n"; }
      if ($species) 				{ $body .= "Species : $species\n"; }
      if ($associatedprocess) 			{ $body .= "Associated process : $associatedprocess\n"; }
      if ($suggestedprocess) 			{ $body .= "Suggested process : $suggestedprocess\n"; }
      if ($comment)	 			{ $body .= "Comment : $comment\n"; }
      $email .= ", $submitter_email";
      
      &mailer($user, $email, $subject, $body);	# email the data
      
      print qq(Thank you for your submission, you should get a confirmation email.  <a href="pathway.cgi">Go back to form</a>);
    }

  print $footer;
} # sub submit


sub displayForm {			# show form as appropriate
  my $var;
#   my ($name, $firstname, $lastname, $submitter_email, $species, $gene, $concise_description, $pmids, $pmid_titles) = ('', '', '', '', '', '', '', '', '');
  my ($name, $submitter_email, $pathwaylogin, $pathwayname, $pathwayid, $species, $associatedprocess, $suggestedprocess, $comment) = ('', '', '', '', '', '', '', '', '');
  ($var, $name)                       = &getHtmlVar($query, 'name');	
  ($var, $submitter_email)            = &getHtmlVar($query, 'submitter_email');
  ($var, $pathwaylogin)               = &getHtmlVar($query, 'pathwaylogin');
  ($var, $pathwayname)                = &getHtmlVar($query, 'pathwayname');
  ($var, $pathwayid)                  = &getHtmlVar($query, 'pathwayid');
  ($var, $species)                    = &getHtmlVar($query, 'species');
  ($var, $associatedprocess)          = &getHtmlVar($query, 'associatedprocess');
  ($var, $suggestedprocess)           = &getHtmlVar($query, 'suggestedprocess');
  ($var, $comment)                    = &getHtmlVar($query, 'comment');
#   ($var, $firstname)                  = &getHtmlVar($query, 'firstname');	
#   ($var, $lastname)                   = &getHtmlVar($query, 'lastname');	
#   ($var, $species)                    = &getHtmlVar($query, 'species');	
#   ($var, $gene)                       = &getHtmlVar($query, 'gene');	
#   ($var, $concise_description)        = &getHtmlVar($query, 'concise_description');	
#   ($var, $pmids)                      = &getHtmlVar($query, 'pmids');	
#   ($var, $pmid_titles)                = &getHtmlVar($query, 'pmid_titles');	

  my $selectProcess = '';
  if ($associatedprocess) { 
    if ($associatedprocess =~ m/\|$/) { $associatedprocess =~ s/\|$//; }
    $selectProcess = $associatedprocess;
    $selectProcess =~ s/\|/<\/option><option>/g;
    $selectProcess = '<option>' . $selectProcess . '</option>'; }
  

  print << "EndOfText";
<body class="yui-skin-sam">

<A NAME="form"><H1>WikiPathways for WormBase Submission Form :</H1></A>
<!--Please enter as much information as possible. Email <A HREF="mailto:genenames\@wormbase.org">genenames\@wormbase.org</A> for any questions/problems.<br />--><!--<center><b><font color="red"><u>All fields are required</u></font></b></center>-->
<font size="2"><br/>
Please use this page to enter a pathway you created or updated for WormBase approval.<br/> Once your pathway has been approved it can be feature on the WormBase Portal of WkiPathways or the WormBase Process Pages.<br/>
Email <a href="mailto:karen\@wormbase.org">karen\@wormbase.org</a> for any questions/problems.<br/>
<span style="color:red">red fields are required</span><br/><br/></font>

<form method="post" action="pathway.cgi">
 <table width="100%" height="100%" align="center" cellpadding="1" cellspacing="1">
  <!--<tr>
    <td width="34%"><FONT SIZE=+2><B>REQUIRED</B></FONT></td>
  </tr>-->

  <TR>
    <TD ALIGN="right"><FONT COLOR='red'><B>Your name</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" ID="name" Name="name" value="$name" Size="50"></TD>
    <!--<TD><font size="1">(Please enter full name, eg. Sulston, John)</font></TD>-->
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='red'><B>Your e-mail address</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="250" value="$submitter_email"></TD>
    <!--<TD><font size="1">(for contact purpose)</font><BR>If you don't get a confirmation email, contact us at webmaster\@wormbase.org</TD>-->
  </TR>

  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='red'><B>Your WikiPathway User name</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" Name="pathwaylogin" Size="50" Maxlength="250" value="$pathwaylogin"></TD>
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='red'><B>WikiPathway Pathway Name</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" Name="pathwayname" Size="50" Maxlength="250" value="$pathwayname"></TD>
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='red'><B>WikiPathway Pathway ID or URL</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" Name="pathwayid" Size="50" Maxlength="250" value="$pathwayid"></TD>
  </TR>

  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='red'><B>Species</FONT> :</B> <BR></TD>
    <TD><select Name="species" Size="1">
    <option>Caenorhabditis elegans</option>
    <option>Caenorhabditis sp. 3</option>
    <option>Caenorhabditis sp. 5</option>
    <option>Caenorhabditis sp. 11</option>
    <option>Caenorhabditis angaria</option>
    <option>Caenorhabditis brenneri</option>
    <option>Caenorhabditis briggsae</option>
    <option>Caenorhabditis japonica</option>
    <option>Caenorhabditis remanei</option>
    <option>Ascaris suum</option>
    <option>Brugia malayi</option>
    <option>Bursaphelenchus xylophilus</option>
    <option>Cruznema tripartitum</option>
    <option>Haemonchus contortus</option>
    <option>Heterorhabditis bacteriophora</option>
    <option>Loa loa</option>
    <option>Meloidogyne hapla</option>
    <option>Meloidogyne incognita</option>
    <option>Panagrellus redivivus</option>
    <option>Pristionchus pacificus</option>
    <option>Strongyloides ratti</option>
    <option>Trichinella spiralis</option>
    <option>Other - Add in Comment below</option>
    </select>
    </TD>
  </TR>

  <!--<tr>
    <td width="34%"><FONT SIZE=+2><B>OTHER INFORMATION</B></FONT></td>
  </tr>-->

  <TR>
    <TD width="220" ALIGN="right" VALIGN="top"><FONT COLOR='black'><B>WBProcess(es)</FONT> :</B> <BR></TD>
    <!--<TD><Input Type="Text" Name="associatedprocess" Size="50" Maxlength="50" value="associatedprocess"></TD>-->
    <td colspan="2" valign="top">
      <span id="containerForcedProcessAutoComplete">
        <div id="forcedProcessAutoComplete">
              <input size="25" id="forcedProcessInput" type="text" >
              <div id="forcedProcessContainer"></div>
        </div></span>
      <input type="hidden" name="associatedprocess" id="associatedprocess">
      <select name="selectProcess" id="selectProcess" multiple="multiple" size="0" >$selectProcess</select>
      <!--<select name="selectPhenont" id="selectPhenont" multiple="multiple" size="0" onchange="PopulatePhenontObo('Phenont', 'select')" ></select>-->
      <br/><input type="button" value="del" onclick="RemoveSelected('Process')">click del to delete selected process(es)
    </td>
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='black'><B>Suggest new WBProcess(es) and Definition</FONT> :</B> <BR></TD>
    <td colspan="1"><textarea id="suggestedprocess" name="suggestedprocess" rows="10" cols="50" >$suggestedprocess</textarea></td>
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='black'><B>Comments</FONT> :</B> <BR></TD>
    <td colspan="1"><textarea id="comment" name="comment" rows="10" cols="50" >$comment</textarea></td>
  </TR>

  <table align="center">
  <td align="center">Clicking Submit will email you a confirmation :
   <input type="submit" name="action" value="Submit" onClick="populateSelectFields()">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
   <!--<input name="reset" type="reset" value="Reset" onClick="rollback()">-->
  </td>
  </table>
 </table>
</form>

<!--
<hr>
<a href="mailto:webmaster\@www.wormbase.org">webmaster\@www.wormbase.org</a><a href="http://www.wormbase.org/copyright.html">&nbsp;&nbsp;&nbsp;Copyright
    Statement</a><a href="http://www.wormbase.org/db/misc/feedback">&nbsp;&nbsp;&nbsp;Send comments or questions to WormBase</a></td> <td class="small" align="right"><a href="http://www.wormbase.org/privacy.html">&nbsp;&nbsp;&nbsp;Privacy Statement</a></td></tr>-->
</body>
</html>

EndOfText
} # sub displayForm


__END__

 <!-- <tr>
    <td colspan="2"><table border="0" width="100%" align="center" cellpadding="4" cellspacing="1">
    <td width="34%"><FONT SIZE=+2><B>REQUIRED</B></FONT></td>
    <td width="28%">&nbsp;</td>
    <td width="38%">&nbsp;</td>
    <td >&nbsp;</td>
    <td >&nbsp;</td>
    <td >&nbsp;</td>
  </tr>-->

  <TR>
    <TD ALIGN="right"><FONT COLOR='black'><B>Enter your first name</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" ID="firstname" Name="firstname" value="$firstname" Size="50"></TD>
    <!--<TD><font size="1">(Please enter full name, eg. Sulston, John)</font></TD>-->
  </TR>
  <TR>
    <TD ALIGN="right"><FONT COLOR='black'><B>Enter your last name</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" ID="lastname" Name="lastname" value="$lastname" Size="50"></TD>
    <!--<TD><font size="1">(Please enter full name, eg. Sulston, John)</font></TD>-->
  </TR>
  <TR>
    <TD width="220" ALIGN="right"><FONT COLOR='black'><B>Enter a contact E-mail address</FONT> :</B> <BR></TD>
    <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50" value="$submitter_email"></TD>
    <!--<TD><font size="1">(for contact purpose)</font><BR>If you don't get a confirmation email, contact us at webmaster\@wormbase.org</TD>-->
  </TR>
  <tr> 
    <TD valign="center" align="right"><FONT COLOR='black'><B>Choose a species</FONT> :</B> <BR>
    <!--<TD><Input Type="Text" Name="species" Size="50"></TD>-->
    <td>
      <!--<Input Type="Text" Name="gene" Size="37">-->
      <span id="containerForcedSpeciesAutoComplete">
        <div id="forcedSpeciesAutoComplete">
              <input size="50" name="species" id="Species" type="text" value="$species">
              <div id="forcedSpeciesContainer"></div>
        </div></span></td>
    <td>&nbsp;&nbsp;</td>
    <TD><font size="2">Start typing in a species name. The form will auto-complete the text and present a list of species below the box. Click anywhere on the species you want to enter that species name in the box. If you cannot find the species in the drop-down, please enter it manually.</font></TD>
  </tr>
  <tr>
    <TD valign="center" align="right"><B>Choose a gene :</B></TD>
    <td>
      <!--<Input Type="Text" Name="gene" Size="37">-->
      <span id="containerForcedGeneAutoComplete">
        <div id="forcedGeneAutoComplete">
              <input size="50" name="gene" id="Gene" type="text" value="$gene">
              <div id="forcedGeneContainer"></div>
        </div></span></td>
    <td>&nbsp;&nbsp;</td>
    <td><font size="2">Enter a gene name (e.g., abc-1). Sequence names (e.g., AC3.4) and WBGene IDs (e.g., WBGene00000011) are allowed. If the gene you begin typing matches a valid WormBase gene name, then a list of possible matches will be presented below the box. To select a gene, click anywhere on the name of that gene and it will be entered into the box. If you cannot find the gene in the drop-down, please enter it manually.</font></td>
  </tr>

  <tr> 
    <TD ALIGN="right"><B>Write a concise description for the gene you've chosen :</B></font></td>
    <td colspan="1"><textarea id="concisedescription" name="concise_description" rows="10" cols="50" >$concise_description</textarea></td>
    <td>&nbsp;&nbsp;</td>
    <TD><font size="2">Please see guidelines on writing a concise description: <a href="http://wiki.wormbase.org/index.php/How_WormBase_writes_a_concise_description" target="new">http://wiki.wormbase.org/index.php/How_WormBase_writes_a_concise_description</a></font></TD>
  </tr>

  <tr> 
    <TD ALIGN="right"><B>Enter the PMID of a published paper reference :</B></td>
    <td colspan="1"><textarea name="pmids" id="pmids" rows="4" cols="50" >$pmids</textarea></td>
    <td>&nbsp;&nbsp;</td>
    <TD><font size="2">Please enter a single PMID identifier per line (e.g., PMID:4366476). Please note that WormBase will not accept meeting abstracts, gazette articles or personal communications as references. </font></TD>
  </tr>
  <tr> 
    <TD ALIGN="right"><B><font color="grey">Display of PMID titles found :</B></font></td>
    <td colspan="3"><textarea name="pmid_titles" id="pmidTitles" rows="10" cols="150" readonly="readonly">$pmid_titles</textarea></td>
  </tr>

sub autocompleteGene {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my $lcwords = lc($words);
  my %matches; my $t = tie %matches, "Tie::IxHash";     # sorted hash to filter results
  my @tables = qw( gin_locus gin_synonyms gin_seqname gin_wbgene );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$lcwords' ORDER BY $table;" );
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


sub populatePmidToWBPaper {
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid';" );
  $result->execute();
  while ( my @row = $result->fetchrow() ) { my ($num) = $row[1] =~ m/(\d+)/; $pmidToWBPaper{$num} = $row[0]; }
} # sub populatePmidToWBPaper

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
    print "PMID $pmid : $title\n"; }					# print the pmid and title in proper format
  print "$stillWantedPmidTitles\n";					# print at the bottom previous matches that are still wanted pmids in the pmids field 
# http://www.ebi.ac.uk/europepmc/webservices/rest/search/format=xml&query=ext_id:23677347%20src:med
} # sub pmidToTitle

sub instructions {
  print "Content-type: text/html\n\n";
  print $header;
    print << "EndOfText";
<p>Welcome to our online allele submission form!</p> \n
<p>1. <b>Positive  phenotypes</b> refer to phenotypes observed by the user. <b>NOT phenotypes</b> refer to phenotypes that have been assayed for and not observed.</p>
<p>2. Individual phenotype terms can be perused by entering a term name, synonym or ID in the <b>Positive Phenotype</b> or <b>NOT Phenotype</b> fields (e.g. dumpy, Dpy, WBPhenotype:0000583).  Any phenotype term recorded in the adjacent list field will get annotated by a WormBase curator unless the submitter deletes it prior to submission (see step 3).</p>
<p>3. In order to delete a term, select the desired term within the list and hit the ‘Del’ button at the lower right of the corresponding list field.</p>
<p>4. The Display of phenotype information field is a non-editable field that displays the current term name, ID, definition, synonyms (if applicable) and its parent-child relationships.</p>
<p>5. Users can browse the tree-view of the phenotype ontology by clicking the <font color=\"purple\">purple</font> link.</p>
<p>6. Details such as temperature sensitivity, allele nature etc. can be entered by clicking the appropriate value from the drop down menu.</p>
<p>7. To propose a new term/definition, please enter your comments in the <b>Suggest new term and definition</b>. If you have any additional suggestions regarding the content or placement of existing phenotype terms within the ontology, please enter your comments in the <b>Suggest new term and definition</b> as well.</p>
<p>8. Please review your entries and click <b>Submit</b> when ready.</p>
<p>Thanks for your submission! </p>
<p>-Team Phenotype</p>
EndOfText
  print $footer;
} # sub instructions

sub OLDsubmit {
  print "Content-type: text/html\n\n";
  print $header;
    $firstflag = "";				# reset flag to not display first page (form)

    my $mandatory_ok = 'ok';			# default mandatory is ok
    my $sender = '';
    my @mandatory = qw ( submitter_email allele firstname lastname );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{allele} = "Allele";
    $mandatoryName{firstname} = "First Name";
    $mandatoryName{lastname} = "Last Name";
 
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
        if ($_ eq 'firstname') { $sender_name = $val; }
      }
    } # foreach $_ (@mandatory)
    my @one_of_three = qw( pos_phenont not_phenont suggest_new );
    my $one_of_three_flag = 0;
    foreach $_ (@one_of_three) {			# check mandatory fields
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val =~ m/./) { $one_of_three_flag++; } }
    unless ($one_of_three_flag > 0) { 
      print "<FONT COLOR=red SIZE=+2>You must enter one of the three phenotype fields (see *).</FONT><BR>";
      $mandatory_ok = 'bad'; }


    my $spam = 0;				# if it's spam skip doing anything  2007 08 24
    foreach $_ (@all_vars) { 			# for all fields, check for spam
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val =~ m/\S/) { 	# if value entered
        if ($val =~ m/a href/i) { 
          my (@spam) = $val =~ m/(a href)/gi;
          foreach my $sp (@spam) { $spam++; } } } }
    if ($spam > 0) { print "Ignoring.  This is spam<BR>\n"; return; }

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $acefile = "/home/azurebrd/public_html/cgi-bin/data/allele.ace";
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
#       $body .= "$sender from ip $host sends :\n\n";	# Mary Ann doesn't want this 2006 05 10

      my %aceName;
      $aceName{allele} = 'Allele';
      $aceName{gene} = 'Gene';
      $aceName{sequence} = 'Sequence';
      $aceName{types_of_alteration} = 'NULL';
      $aceName{alteration_text} = 'NULL';
      $aceName{indel_seq} = 'NULL';
      $aceName{genotype} = 'NULL';
      $aceName{strain} = 'Strain';
      $aceName{species} = 'NULL';		# check that species_other wasn't filled
      $aceName{species_other} = 'Species';
      $aceName{mutagen} = 'Mutagen';		# Mutagen  2004 01 23
      $aceName{upstream} = 'NULL';		# Flanking_sequences (left)
      $aceName{downstream} = 'NULL';		# Flanking_sequences (right)
      $aceName{nature_of_allele} = 'NULL';	# Recessive / Semi_dominant / Dominant
      $aceName{penetrance} = 'NULL';
      $aceName{heat_sensitive} = 'NULL';	# Heat_sensitive / Cold_sensitive
      $aceName{cold_sensitive} = 'NULL';	# Heat_sensitive / Cold_sensitive
      $aceName{hot_temp} = 'NULL';	
      $aceName{cold_temp} = 'NULL';
      $aceName{types_of_mutations} = 'NULL';
      $aceName{mutation_info} = 'NULL';
      $aceName{haploinsufficient} = 'NULL';	
      $aceName{loss_of_function} = 'NULL';	
      $aceName{gain_of_function} = 'NULL';
      $aceName{phenotypic_description} = 'Phenotype';
      $aceName{forward} = 'Forward_genetics';
      $aceName{reverse} = 'Reverse_genetics';
      $aceName{firstname} = 'NULL';
      $aceName{lastname} = 'NULL';
      $aceName{submitter_email} = 'NULL';
      $aceName{comment} = 'Remark';

      my ($var, $allele) = &getHtmlVar($query, 'allele');
      unless ($allele =~ m/\S/) {			# if there's no allele text
        print "<FONT COLOR='red'>Warning, you have not picked an Allele</FONT>.<P>\n";
      } else {					# if allele text, output
        $result = $dbh->do( "INSERT INTO ale_allele (ale_allele) VALUES ('$allele');" );
						# this updated the pg sequence ale_seq to nextval
        $result = $dbh->prepare( "SELECT currval('ale_seq');" );	
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
						# can get currval because last line updated
        my @row = $result->fetchrow;
        $joinkey = $row[0];
        print "Allele entry number $joinkey<BR><BR>\n";
	$allele =~ s///g; $allele =~ s/\n//g; $allele = lc($allele);	# lowercase allele
        $body .= "allele\t$allele\n";
        $subject .= " : $allele";
        $result = $dbh->do( "INSERT INTO ale_ip VALUES ('$joinkey', '$host');" );
  
        foreach my $field (@all_vars) { 			# for all fields, check for data and output
          my ($var, $val) = &getHtmlVar($query, $field);
          if ($val =~ m/\S/) { 	# if value entered

            if ($aceName{$var} ne 'NULL') {
              if ($var eq 'gene') { $val = lc($val); }		# lowercase gene
              elsif ($var eq 'strain') { $val = uc($val); }	# uppercase strain
              elsif ($var eq 'sequence') { 
                $val =~ s/\..*$//;				# take out anything after . (and .)
                $val = uc($val); }				# uppercase sequence
              else { 1; }
            } # if ($aceName{$var} ne 'NULL')
	    else { 1; }

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
 
            next if ($field eq 'pos_phenont');		# jolene does not want these in postgres  2009 06 12
            next if ($field eq 'not_phenont');		# jolene does not want these in postgres  2009 06 12
            next if ($field eq 'suggest_new');		# jolene does not want these in postgres  2009 06 12
            my $pg_table = 'ale_' . $var;
            $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
          } # if ($val) 
        } # foreach $_ (@vars) 
        print OUT "$body\n";			# print to outfile
        close (OUT) or die "cannot close $acefile : $!";
        $email .= ", $sender";
        &mailer($user, $email, $subject, $body);	# email the data
        $body = "Dear $sender_name,\n\nYou have sucessfully submitted the following data to WormBase. You will be contacted by WormBase within three working days.\n\nIf you wish to modify your submitted information, please go back and resubmit.\n" . $body;
        $body =~ s/\n/<BR>\n/mg;
        print "$body<BR><BR>\n";
        print "If you wish to modify your submitted information, please go back and resubmit.<BR><P>\n";
      } # else # unless ($allele =~ m/\S/)	# this if/then/else should be unnecessary
    } # else # unless ($sender =~ m/@.+\..+/)
  print $footer;
} # sub OLDsubmit
