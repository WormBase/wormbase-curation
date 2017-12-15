#!/usr/bin/perl

# New for authors to first pass fields

# Added javascript extendable textareas.  Made them hide by default.  Added ``Add information'' link
# to show hidden textareas.  2009 02 28
#
# Changed the link to toggle the hide / show state.  Changed the state to refer to the tr instead
# of the textarea, which allows a close button on the first td or the tr.  Moved the looping javascript
# that hid all textareas into first_pass.js, and have it match a regexp of ^tr on the id of the "tr"s 
# to make sure they're hidden.  2009 03 02
#
# Made subcategories and ToggleHideSubcategories javascript function.  2009 03 07
#
# Lots of description changes.  Added %hash{example}{table} to hide by default and toggle off a ``?''
# to show explanation text.  Added ``Specify'' comment when toggling subcategories on.  2009 03 11
#
# More ordering changes and description and name changes.  2009 03 12
#
# Re-created some tables, renamed some other tables, repopulated data and populated afp_{table}_hst
# for history data.
# Rewrote &writePg(); to delete normal data if there was some, and insert data into history and normal.
# Had to add ``name'' to html elements since CGI.pm can't get them from the ``id'' field.  2009 03 13
#
# Added afp_lasttouched to store when someone last sent data (so as not to check all values to see if 
# someone wrote anything.  Stores ``time'' as an integer.  2009 04 22
#
# Added citation info and congratulations on top.  with &getCitation.  switched from Pg.pm to DBI.pm
# 2009 04 23
#
# extvariation, antibody, and transgene removed since they're happy with textpresso results.  2009 05 14
#
# email Karen when authors use the form.  2009 05 16
#
# wrote &emailCurator if there's $formdata to email data curators that want data.  2009 09 10
#
# only email if no svm results for that paper / type.  2009 09 21
#
# changed some email addresses.  2009 12 03
#
# converted to from wpa to pap tables, even though they're not live.  2010 06 22
#
# removed jolene, added mary ann to newsnp, karen to newmutant and overexpr.  removed genefunc.
# changed ? text for mass spec. 2011 02 09
#
# added daniela for otherexpr  2011 02 10
#
# changed &emailCurator to append the afp_email tables value for Karen / Mary Ann.
# made the afp_email value a field under "other" so users can update their emails (including 
# removing them if they wanted to).
# marker and chemicals go to Karen.  2011 02 17
#
# changed caprica to  131.215.52.209  2012 01 26
#
# added pmids to subject line for non-caltech emails.  2012 03 02
#
# cosmetic changes for Karen since the wormbase redesign messed things up a long time ago.
# for Karen.  2013 01 14
#
# marker goes to karen + daniela now.  for Daniela 2014 03 31
#
# added links to concise description submission form + allele phenotype submission form.
# for Karen.  2015 09 22


# sample at 
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/first_pass.cgi?action=Curate&paper=00000003&passwd=1228446342.8668923



use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use LWP::Simple;
# use Ace;

# use Pg;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

# my $conn = Pg::connectdb("dbname=testdb");
# die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;

my $blue = '#00ffcc';                   # redefine blue to a mom-friendly color
my $red = '#00ffff';                    # redefine red to a mom-friendly color


my $query = new CGI;
my $firstflag = 1;

my %hash;				# cat -> category ;  name -> name ;  exmp -> example
my %name;
my %pgData;				# data already in the pg tables (non _hst)
my @pgTables;				# the postgres tables

# NEW TABLES  matrices (maybe marker) timeaction celegans cnonbristol nonnematode nocuratable  domanal (copy structureinformation)
# RENAME structurecorrectionsanger to structcorr ;  nonntwo to nematode ;
# rgngene to genestudied ;  functionalcomplementation to funccomp ;  structureinformation to structinfo ;
# extractedvariation to extvariation
# 
# 
# my %indent;
# $indent{"antibody"}++;
# $indent{"transgene"}++;
# $indent{"marker"}++;
# $indent{"otherexpression"}++;
# $indent{"newmutant"}++;
# $indent{"rnai"}++;
# $indent{"lsrnai"}++;
# $indent{"overexpr"}++;
# $indent{"chemicals"}++;

# my @cats = qw( gif int gef pfs seq cell sil rgn oth );
my @cats = qw( spe gif gfp int gef rgn pfs seq cell sil oth );
my @spe = qw( celegans cnonbristol nematode nonnematode );
# my @gif = qw( genestudied genesymbol extvariation mappingdata );	# extvariation removed 2009 05 14
my @gif = qw( genestudied genesymbol mappingdata );
my @gfp = qw( phenanalysis mosaic siteaction timeaction humdis );
my @phenanalysis = qw( newmutant rnai lsrnai overexpr chemicals );
my @int = qw( geneint funccomp geneprod );
my @gef = qw( otherexpr microarray genereg seqfeat matrices );
# my @rgn = qw( antibody transgene marker );				# antibody and transgene removed 2009 05 14
my @rgn = qw( marker );
my @pfs = qw( invitro domanal covalent structinfo massspec );
my @seq = qw( structcorr seqchange newsnp );
my @cell = qw( ablationdata cellfunc );
my @sil = qw( phylogenetic othersilico );
my @oth = qw( supplemental nocuratable comment email );
$hash{cat}{spe} = [ @spe ];
$hash{cat}{gif} = [ @gif ];
$hash{cat}{gfp} = [ @gfp ];
$hash{cat}{phenanalysis} = [ @phenanalysis ];
$hash{cat}{int} = [ @int ];
$hash{cat}{gef} = [ @gef ];
$hash{cat}{rgn} = [ @rgn ];
$hash{cat}{pfs} = [ @pfs ];
$hash{cat}{seq} = [ @seq ];
$hash{cat}{cell} = [ @cell ];
$hash{cat}{sil} = [ @sil ];
$hash{cat}{oth} = [ @oth ];
# my @comment = qw( nocuratable comment );
# $hash{cat}{comment} = [ @comment ];


# expression -> Patterns of Gene Expression.  checkbox expands 4 fields below it
# antibodies / transgene / marker / otherexpr
# phenanalysis -> Phenotype Analysis.  checkbox expands 5 fields below it
# newmutant / rnai / lsrnai / overexpr / chemicals

&hashName();


print "Content-type: text/html\n\n";
my $title = 'Paper Flagging Form';
my ($header, $footer) = &cshlNew($title);
$header =~ s/<\/head>/<link rel="stylesheet" href="http:\/\/tazendra.caltech.edu\/~azurebrd\/stylesheets\/jex.css" \/><script type="text\/javascript" src="http:\/\/tazendra.caltech.edu\/~azurebrd\/javascript\/test.js"><\/script><script type="text\/javascript" src="http:\/\/tazendra.caltech.edu\/~azurebrd\/javascript\/first_pass.js"><\/script>\n<\/head>/;

# my $header = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><HTML><HEAD>';
# $header .= '<link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" /><script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/test.js"></script><script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/first_pass.js"></script>';
# my $footer = '</HTML>';


# $header = '<HTML><HEAD>';
# $header = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><HTML><HEAD>';

# $header .= '</HEAD><BODY onLoad="ShowData()">';
# $header .= '</HEAD><BODY onLoad="cleanForm();">';
# $header .= '</HEAD><BODY>';


# $header =~ s/<\/head>/<link rel="stylesheet" href="http:\/\/tazendra.caltech.edu\/~azurebrd\/stylesheets\/jex.css" \/><script type="text\/javascript" src="http:\/\/tazendra.caltech.edu\/~azurebrd\/cgi-bin\/testing\/javascript\/dynamic_text\/test.js"><\/script>\n<\/head>/;

# $header .= '<SCRIPT type="text/javascript">
# function ShowData() {
#   window.status="Page is loaded";
#   //document.writeln("Page is loaded");
#   //showData.innerHTML = showData.innerHTML + "page is loaded";
#   showData.innerHTML = showData.innerHTML + "<TEXTAREA NAME=textareaBox onKeypress=textareaExpand() rows=1 COLS=80></TEXTAREA><BR>";
#   showData.innerHTML = showData.innerHTML + "<input type=text onKeypress=textInputExpand() name=thebox size=20><BR>";
# //   for (docprop in document) {
# //     showData.innerHTML = showData.innerHTML + docprop + "=";
# //     // showData.innerHTML = showData.innerHTML + eval ("document." + docprop + ")");
# //     // var stuff = eval ("document." + docprop + "");
# //     // showData.innerHTML = showData.innerHTML + stuff;
# //     showData.innerHTML = showData.innerHTML + eval ("document." + docprop + "");
# //     showData.innerHTML = showData.innerHTML + "<BR>";
# //   }
#   //alert("Page is loaded");
# }
# function countLines(strtocount, cols) {
#     var hard_lines = 1;
#     var last = 0;
#     while ( true ) {
#         last = strtocount.indexOf("\n", last+1);
#         hard_lines ++;
#         if ( last == -1 ) break;
#     }
#     var soft_lines = Math.round(strtocount.length / (cols-1));
#     var hard = eval("hard_lines  " + unescape("%3e") + "soft_lines;");
#     if ( hard ) soft_lines = hard_lines;
#     return soft_lines;
# }
# // function cleanForm() {  // use this to set a timeout on all textareas instead of listening for keypress
# //     var the_form = document.forms[0];
# //     for ( var x in the_form ) {
# //         if ( ! the_form[x] ) continue;
# //         if( typeof the_form[x].rows != "number" ) continue;
# //         the_form[x].rows = countLines(the_form[x].value,the_form[x].cols) +1;
# //     }
# //     setTimeout("cleanForm();", 300);
# // }
# function textareaExpand() {
#   document.all.textareaBox.rows = countLines(document.all.textareaBox.value,document.all.textareaBox.cols) ;
# }
# function textInputExpand() {
#   // Code to make the script easier to use //
#   boxValue=document.all.thebox.value.length
# //   boxSize=document.all.thebox.size
#   minNum=20 // Set this to the MINIMUM size you want your box to be.
#   maxNum=100 // Set this to the MAXIMUM size you want your box to be.
#   
#   // Starts the main portion of the script //
#   if (boxValue > maxNum) { }
#   else {
#     if (boxValue > minNum) { document.all.thebox.size = boxValue }
#     else if (boxValue < minNum || boxValue != minNum) { document.all.thebox.size = minNum }
#   }
# }
# // This does not work :
# // Activates the content area if we have the default text
# //   showData.innerHTML = showData.innerHTML + "<TEXTAREA NAME=textareaBox onfocus=activateArea(this) onkeypress=adjustAreaSize(this) rows=1 COLS=80></TEXTAREA><BR>";
# // function activateArea(area) {
# //     if (!area.hasClassName("active")) {
# //         area.setTextValue("");
# //         area.addClassName("active");
# //     }
# // }
# // // Adjusts the size of the text area based on how many lines it has in it
# // function adjustAreaSize(area) {
# //     area.setRows(5);    // Min height, and causes shrink
# //     alert(area.getScrollHeight() + " D " + area.getOffsetHeight());
# //     while (area.getScrollHeight() > area.getOffsetHeight())
# //         area.setRows(area.getRows() + 1);
# // }
# 
# </SCRIPT>';

# <script type="text/javascript" >
# function CreateTextbox()
# {
# var i = 1;
# createTextbox.innerHTML = createTextbox.innerHTML +"<input type=text name='mytext'+ i/>"
# 
# }
# </script>
# </head>
# <body>
# 
# <form name="form" action="post" method="">
# <input type="button" value="clickHere" onClick="CreateTextbox()">
# <div id="createTextbox"></div>
# </form>



# TODO
# make checkboxes for textarea be unclearable if there's text in the textarea
# textareas have a clear button

print "$header\n";		# make beginning of HTML page

&process();			# see if anything clicked
# &displayQuery();		# show query box
print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; &displayTypeTwo(); }

  if ($action eq 'Curate') { &displayTypeTwo(); }
  elsif ($action eq 'Flag') { &gotFlagged(); }
#   elsif ($action eq 'Submit Text') { &gotText(); }
  elsif ($action eq 'nocuratable') { &gotNocuratable(); }
}

sub gotNocuratable {
  my ($paper, $passwd) = &checkPaperPasswd();
  return if ($paper eq 'bad');
#   print "Not a primary research article.<BR>\n";
  print "WormBase curators have now been alerted that your paper is not a  primary research paper.<br /> You do not need to do anything further.<br /> Thank you for your participation!<br />\n";	# changed for Karen  2009 05 16
  &writePg('nocuratable', $paper, "'checked'");		# was missing doublequotes around checked  2009 05 16
  my $time = time;
  &writePg('lasttouched', $paper, "'$time'"); 		# need to show it as curated  2009 05 16
  &messageKaren("$paper is a review");
#   &messageAndrei("$paper is a review");
} # sub gotNocuratable

sub writePg {
  my ($table, $joinkey, $data) = @_;
  next unless ($data);		# skip if there's no data (NULL is explicitly written)
  my $to_print = $data; if ($to_print eq 'NULL') { $to_print = "is now blank"; }
  unless ($table eq 'lasttouched') {
    print "<span style=\"color:#3366FF; font-family: sans-serif;\">$hash{name}{$table}</span> $to_print<br />\n";
  }
  my @pgcommands = (); my $pgcommand = '';
  $pgcommand = "DELETE FROM afp_$table WHERE joinkey = '$joinkey';" ;	
  push @pgcommands, $pgcommand;		# can't check $pgData{$table} since blank wouldn't show
  $pgcommand = "INSERT INTO afp_$table VALUES ('$joinkey', $data);" ;
  push @pgcommands, $pgcommand;
  $pgcommand = "INSERT INTO afp_${table}_hst VALUES ('$joinkey', $data);" ;
  push @pgcommands, $pgcommand;
  foreach $pgcommand (@pgcommands) {
#     print "$pgcommand<BR>\n";
#     my $result = $conn->exec( $pgcommand );
    my $result = $dbh->do( $pgcommand );

  }
# I THINK THE BELOW IS JUNK  2009 04 06
#   my @row = $result->fetchrow();
# UNCOMMENT THESE TO WRITE TO POSTGRES
#   if ($row[0]) {				# if there was previous data in postgres
#       my $update = 0;
#       if ($data ne 'checked') { $update++; }	# real data, always update
#       elsif ( ($row[1] eq 'checked') && ($data eq 'checked') ) { $update++; }	# was checked and is checked, update to get new timestamp
#       elsif ( ($row[1] ne 'checked') && ($data eq 'checked') ) { $update = 0; }	# was real data and is now checked, ignore, not new data
#       if ($update > 0) {
#         $result = $conn->exec( "UPDATE $table SET $table = '$data' WHERE joinkey = '$joinkey';" );
#         $result = $conn->exec( "UPDATE $table SET afp_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" ); } }
#     else { $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$data');" ); }
} # sub writePg

sub emailComment {
  my ($paper, $formdata) = @_;
  my $user = 'paper_fields.cgi';
  my $email = 'kyook@its.caltech.edu';
  my $subject = "Comment for WBPaper$paper";
  my $body = $formdata;
  &mailer($user, $email, $subject, $body);    # email CGI to user
}

sub gotFlagged {
  my ($paper, $passwd) = &checkPaperPasswd();
  return if ($paper eq 'bad');
  &populatePgData($paper);
  &printForm();
#   print "<INPUT TYPE=HIDDEN NAME=paper VALUE=$paper>\n"; print "<INPUT TYPE=HIDDEN NAME=passwd VALUE=$passwd>\n";
  my $time = time;
  &writePg('lasttouched', $paper, "'$time'"); 

  my ($pmid) = &getPmid($paper);
  my $body = "Paper $paper flagged";
  my %svmData;						# type, paper -> confidence
#   my $url_path = 'http://caprica.caltech.edu/celegans/svm_results/Juancarlos/';
  my $url_path = 'http://131.215.52.209/celegans/svm_results/Juancarlos/';
  my @svmFiles = qw( geneint geneprod_GO genereg rnai );
  foreach my $file (@svmFiles) {
    my $url = $url_path . $file;
    if ($file eq 'geneprod_GO') { $file = 'geneprod'; }		# table is called geneprod
    my $data = get( $url );
    my (@lines) = split/\n/, $data;
    foreach my $line (@lines) { my ($paper, $conf) = split/\t/, $line; ($paper) = $paper =~ m/(\d+)/; $svmData{$file}{$paper} = $conf; } }	# need to only capture joinkey for paper

  (my $oop, my $submitter_email) = &getHtmlVar($query, "email");
  foreach my $table (@pgTables) {		# want to update email value first, doesn't matter if it happens twice
    my ($pgdata) = &getPgData($table, $paper);
    ($oop, my $checked) = &getHtmlVar($query, "${table}_check");
    ($oop, my $formdata) = &getHtmlVar($query, $table);
# print "$table has -=${formdata}=-<br />\n";
    if ($pgdata) {					# there was pg data;  three posibilities, same text data, diff text data, same checkbox, blank checkbox
      next if ($pgdata eq $formdata); 			# no change, skip (same text data)
      if ($formdata) {					# diff formdata, write and move on
        unless ($svmData{$table}{$paper}) { &emailCurator($table, $formdata, $body, $submitter_email, $pmid); }
        &writePg($table, $paper, "'$formdata'"); 
        if ($table eq 'comment') { &emailComment($paper, $formdata); }
        next; } 		
      next if ($pgdata eq $checked);			# no change, skip (same checkbox)
      if ($checked eq '') { &writePg($table, $paper, 'NULL'); }
    } else { 						# new data
      unless ($formdata) { $formdata = $checked; }	# no formdata, copy checked data
      if ($formdata) { 
        unless ($svmData{$table}{$paper}) { &emailCurator($table, $formdata, $body, $submitter_email, $pmid); }
        &writePg($table, $paper, "'$formdata'"); 
}
    }
  } # foreach my $table (@pgTables)
  print "</FORM>\n";
#   &messageCurator($body);				# Xiaodong doesn't want messages  2009 04 24
#   &messageAndrei($body);
  &messageKaren($body);
  print "Thank you for submitting data for this paper.<br />\n";
} # sub gotFlagged

sub messageKaren {
  my $body = shift;
  my $user = 'paper_fields.cgi';
  my $email = 'kyook@its.caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
  my $subject = 'Updated Author Flagging Form';
#   print "$body<BR>\n";
  &mailer($user, $email, $subject, $body);    # email CGI to user
} # sub messageKaren

sub emailCurator {
  my ($table, $formdata, $body, $submitter_email, $pmid) = @_;
  my $email = ''; my $addPmid = 0;
  if ( ($table eq 'rnai') || ($table eq 'lsrnai') ) { $email = 'garys@its.caltech.edu'; }
  elsif ( ($table eq 'geneprod') || ($table eq 'invitro') ) { $email = 'vanauken@its.caltech.edu'; }
  elsif ( ($table eq 'chemicals') || ($table eq 'newmutant') || ($table eq 'overexpr') ) { $email = 'kyook@caltech.edu'; }
  elsif ( ($table eq 'genereg') || ($table eq 'geneint') || ($table eq 'matrices') ) { $email = 'xdwang@its.caltech.edu'; }
  elsif ( ($table eq 'mosaic') || ( $email eq 'siteaction') || ( $email eq 'timeaction') || 
       ( $email eq 'ablationdata') || ( $email eq 'cellfunc') ) {
    $email = 'raymond@its.caltech.edu'; }
  elsif ( $table eq 'otherexpr' ) { $email = 'draciti@caltech.edu'; }
  elsif ( $table eq 'marker') { $email = 'kyook@caltech.edu, draciti@caltech.edu'; }
#   elsif ( $table eq 'extvariation' ) { $email = 'worm-bug@sanger.ac.uk'; $addPmid++; }
  elsif ( $table eq 'newsnp' ) { $email = 'mt3@sanger.ac.uk'; $addPmid++; }
  elsif ( ($table eq 'seqfeat') ) { $email = 'draciti@caltech.edu, worm-bug@sanger.ac.uk'; $addPmid++; }
  elsif ( $table eq 'structcorr' ) { $email = 'seqcur@wormbase.org, worm-bug@sanger.ac.uk'; $addPmid++; }
  elsif ( $table eq 'massspec' ) { $email = 'gary.williams@wormbase.org, worm-bug@sanger.ac.uk'; $addPmid++; }
  elsif ( ( $table eq 'genesymbol' ) || ( $table eq 'mappingdata' ) || ( $table eq 'seqchange' ) ) { $email = 'genenames@wormbase.org'; $addPmid++; }

  if ($email) {
#     $email = 'azurebrd@tazendra.caltech.edu';
    my $user = 'first_pass.cgi'; 
    my $subject = $body . " for $table"; 
    if ($addPmid > 0) { $subject .= " $pmid"; }
    $body = $formdata;
    $body .= "\n\nThese data were submitted from $submitter_email .";
    &mailer($user, $email, $subject, $body);    # email CGI to user
  }
}

sub messageCurator {
  my $body = shift;
  my $user = 'paper_fields.cgi';
  my $email = 'xdwang@its.caltech.edu';
#   my $email = 'jolenef@its.caltech.edu, raymond@its.caltech.edu';
#   my $email = 'azurebrd@tazendra.caltech.edu';
  my $subject = 'Updated Author Flagging Form';
#   print "$body<BR>\n";
  &mailer($user, $email, $subject, $body);    # email CGI to user
} # sub messageAndrei


sub printForm {
  print "<FORM METHOD=POST ACTION=\"first_pass.cgi\">\n";
} # sub printForm

sub checkPaperPasswd {
  (my $oop, my $paper) = &getHtmlVar($query, 'paper');
  ($oop, my $passwd) = &getHtmlVar($query, 'passwd');
  my $result = $dbh->prepare( "SELECT * FROM afp_passwd WHERE joinkey = '$paper' AND afp_passwd = '$passwd';" );
  $result->execute();
  my @row = $result->fetchrow;
# UNCOMMENT THIS TO PUT PASSWORD CHECKING BACK
  unless ($row[0]) { print "Invalid Password<BR>\n"; return "bad"; }
  my $time = time;
# print "TIME $time<BR>\n";
  my $timediff = $time - $passwd;
# UNCOMMENT THIS TO PUT PASSWORD EXPIRY BACK
#   if ($timediff > 604800) { print "Password has expired after 7 days, please email <A HREF=\"mailto:petcherski\@gmail.com\">Andrei</A> for renewal<BR>\n"; return "bad"; }
  return ($paper, $passwd);
} # sub checkPaperPasswd

sub displayTypeTwo {
  my ($paper, $passwd) = &checkPaperPasswd();
  return if ($paper eq 'bad');
  &populatePgData($paper);
  print "<FORM NAME=typeTwoForm METHOD=POST ACTION=\"first_pass.cgi\">\n";
# I THINK THE BELOW IS JUNK  2009 04 06
#   print "<div id=\"showData\"></div>";
#   print "<INPUT TYPE=BUTTON VALUE=\"testing\" onClick=\"ShowData()\"><BR><P>\n";
#   print << "EndOfText";
#   <input type="text" id="txtToHide" onfocus="hide(this.form,1)"/>
#   <textArea id="txtArea" style="overflow:auto;" onblur="hide(this.form,2)"></textArea><br>
# EndOfText
# 
# print '<script type=text/javascript>
# for (docprop in document) {
#   document.writeln(docprop + "=");
#   eval ("document.writeln(document." + docprop + ")");
#   document.writeln("<BR>");
# }
# </script>';
 
  print "<input type=\"hidden\" name=\"paper\" value=\"$paper\" />\n"; 
  print "<input type=\"hidden\" name=\"passwd\" value=\"$passwd\" />\n";
  print "<h1>Congratulations on the publication of your paper!</h1><br/>\n";
  my $citation = &getCitation($paper);
  print qq($citation<br /><br/><br/>\n);
  print "<h2>Please click the box next to the type of data your publication includes.</h2>\n";
  print "Click the \"?\" to find out more about the data type.<br /><br/>";

#   print "<b>If this is a <span style=\"color:red\">Review</span> just click this button and ignore the fields below : </b><input type=\"submit\" id=\"action\" value=\"Review\"><br />\n";
  print "<b>If this is not a primary research article (e.g., this is a review, book chapter, etc.), please click <a href=http:\/\/tazendra.caltech.edu\/~azurebrd\/cgi-bin\/forms\/first_pass.cgi?paper=$paper&passwd=$passwd&action=nocuratable><span style=\"color:chocolate\">here</span></a>.  You may ignore the fields below.  Thank you. </b><br />\n";
  if ($pgData{afp}) { print "<br /><span style=\"color: red\">This paper has already had data submitted, loading it now.  If the submitted data is incorrect, or the paper was incorrectly submitted as a review, you can re-flag this paper with correct data by submitting this form again.</span><br /><br/>\n"; }
  print "<table border=\"0\">";
  foreach my $cat (@cats) {
    print "<td colspan=3><br/><h1 style=\"margin-top: 30; margin-bottom: 10\">$hash{name}{$cat} :</h1></td></tr>\n";
#     print "<td colspan=3><h1>$hash{name}{$cat} :</h1></td></tr>\n";
    foreach my $table (@{ $hash{cat}{$cat} }) { 
      &showTr($table, $paper, "cat", "1");
      if ($hash{cat}{$table}) { 
        foreach my $subcat ( @{ $hash{cat}{$table} } ) { &showTr($subcat, $paper, "subcat", "1"); } 
#         print "</table>";	# close the table that holds subcategories
      }
    }
  } # foreach my $cat (@cats)
  print "</table>";
  print "<P><BR><INPUT TYPE=submit NAME=action VALUE=\"Flag\"><BR>\n";
  print "</FORM>\n";
} # sub displayTypeTwo

sub populatePgData {
  my $paper = shift;
  foreach my $cat (@cats) {
    foreach my $table (@{ $hash{cat}{$cat} }) { 
      if ($hash{cat}{$table}) { 
        foreach my $subcat ( @{ $hash{cat}{$table} } ) { push @pgTables, $subcat; } }  
      else { push @pgTables, $table; } } }
  foreach my $table (@pgTables) {
    my ($pgdata) = &getPgData($table, $paper);
    if ($pgdata) { 
      unless ($table eq 'email') { $pgData{afp}++; }
      $pgData{$table} = $pgdata; }
  } # foreach my $table (@pgTables)
} # sub populatePgData

sub showTr {
  my ($table, $paper, $catOrSubcat, $rowSpan) = @_;
  my $trId = '';
  if ($catOrSubcat eq 'subcat') { $trId = "tr_hidden_$table"; }
  my $left = '';
  if ($catOrSubcat eq 'subcat') { $left = "style=\"left: 20px\""; }
  print "<tr id=\"$trId\" $left>\n";
  my $checked = '';
#   my ($pgdata) = &getPgData($table, $paper);
  my $pgdata = $pgData{$table};
  if ($pgdata) { $checked = 'checked="checked"'; } else { $checked = ''; }
  unless ($pgData{afp}) { if ($table eq 'celegans') { $checked = 'checked="checked"'; } }
  my $td_id = "td_" . $table . '_check';
  if ($hash{cat}{$table}) { 
    my $subcats = join", ", @{ $hash{cat}{$table} };
    $td_id = "td_" . $subcats . '_check';
    $checked .= " onClick=\"ToggleHideSubcategories(\'$subcats\')\""; }
  print "<td id=\"$td_id\" valign=\"top\" rowspan=\"$rowSpan\">";	# assign an id for ToggleHideSubcategories
  my $colspan = 2;					# shown tds with data of categories have a colspan of 2
  if ($catOrSubcat eq 'subcat') { $colspan--; } 	# hidden tds with data of sub-categories have a colspan of 1
  print "<input type=\"checkbox\" name=\"${table}_check\" id=\"${table}_check\" value=\"checked\" $checked /></td><td colspan=\"$colspan\">\n";
  print "<table border=\"0\"><tr><td colspan=\"2\">";		# open a table for description and textarea to be aligned
  print "$hash{name}{$table}";
  if ($hash{exmp}{$table}) { 
      print "  <a href=\"javascript:ToggleHideSpan('example', '$table')\" style=\"color:chocolate\">?</a><span id=\"span_example_$table\">$hash{exmp}{$table}</span>";
  }
  if ($hash{cat}{$table}) { 
      my $subcats = join", ", @{ $hash{cat}{$table} };
      print "  <span id=\"span_specify_$subcats\"><b>Please specify your data type.</b></span>\n"; 
  } else {
      print " <a href=\"javascript:ToggleHideSpan('hidden', '$table')\">Add information</a>."; 
      if ($hash{name3}{$table}) { print qq( $hash{name3}{$table}); }
#       print "<span style=\"color:white\">$table</span>\n"; 
      print "<span id=\"span_hidden_$table\"><br />";
      print "<textarea name=\"$table\" id=\"$table\" style=\"overflow:auto; left:10px\" onKeyUp=DisableCheckboxResizeTextarea(\"$table\") rows=\"4\" cols=\"80\">";
      if ($pgdata ne 'checked') { print "$pgdata"; }
      print "</textarea>";
      print "<a href=\"javascript:ToggleHideSpan('hidden', '$table')\" style=\"vertical-align: top\">x</a>";
      print "</span>\n";
  }
  print "</td></tr></table>";					# close table for description and textarea alignment
  print "</td></tr>\n";
#   print "<tr id=\"tr_hidden_$table\"><td valign=\"top\" align=\"right\" style=\"font-variant: small-caps\"><a href=\"javascript:ToggleHideSpan('hidden', '$table')\">x</a></td>";
#   print "<td><textarea id=\"$table\" style=\"overflow:auto;\" onKeyUp=ExpandTextarea(\"$table\") rows=\"4\" cols=\"80\"></textarea></td></tr>\n";
} # sub showTr

sub getCitation {
  my ($joinkey) = @_;  my %title; my %journal; my %year;
  my $result = $dbh->prepare( "SELECT * FROM pap_title WHERE joinkey = '$joinkey' ORDER BY pap_timestamp;" );
  $result->execute();
  while ( my @row = $result->fetchrow() ) {
    $title{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM pap_journal WHERE joinkey = '$joinkey' ORDER BY pap_timestamp;" );
  $result->execute();
  while ( my @row = $result->fetchrow() ) {
    $journal{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM pap_year WHERE joinkey = '$joinkey' ORDER BY pap_timestamp;" );
  $result->execute();
  while ( my @row = $result->fetchrow() ) {
    $year{$row[1]}++; }
  my (@titles) = keys %title; my (@journals) = keys %journal; my (@year) = keys %year; 
  my $citation = "<span style=\"font-size: 105%; font-weight: bold; font-style: italic\">\"$titles[0]\" <span style=\"font-style: italic\">$journals[0],</span> $year[0]</span>";
  return $citation;
} # sub getTitle

sub getPgData {
  my ($table, $joinkey) = @_;
  my $result = $dbh->prepare( "SELECT * FROM afp_$table WHERE joinkey = '$joinkey';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[1]) { return $row[1]; }
  return;
} # sub getPgData

sub getPmid {
  my $paper = shift; my %pmids; my $pmids = 'no pmid';
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey = '$paper' AND pap_identifier ~ 'pmid';" );
  $result->execute();
  while (my @row = $result->fetchrow() ) { $pmids{$row[1]}++; }
  my @pmids = keys %pmids; if (scalar @pmids > 0) { $pmids = join", ", @pmids; }
  return $pmids;
} # sub getPmid

sub hashName {
  $hash{name}{spe} = 'Species';
  $hash{name}{celegans}    = '<i>C. elegans</i>.';
  $hash{exmp}{celegans}    = 'Please uncheck if you are not reporting data for <i>C. elegans</i>.';
  $hash{name}{cnonbristol} = '<i>C. elegans</i> other than Bristol.';
#   $hash{exmp}{cnonbristol} = 'Please indicate if data for <i>C. elegans</i> isolates other than N2 (Bristol) are presented in this paper.';
  $hash{exmp}{cnonbristol} = 'Please indicate if <i>C. elegans</i> isolates other than Bristol, such as Hawaiian, CB4855, etc., are used in your paper.';	# changed 2009 07 06
  $hash{name}{nematode}    = 'Nematode species other than <i>C. elegans</i>.';
  $hash{exmp}{nematode}    = 'Please indicate if data is presented for any species other than <i>C. elegans</i>, e.g., <i>C. briggsae, Pristionchus pacificus, Brugia malayi,</i> etc.';
  $hash{name}{nonnematode} = 'Non-nematode species.';
  $hash{exmp}{nonnematode} = 'Please indicate if data is presented for any non-nematode species.';

  $hash{name}{gif} = 'Gene Identification and Mapping';
  $hash{name}{genestudied}  = 'Genes studied in this paper.';
  $hash{name2}{genestudied} = 'Relevant Genes.  Please list genes studied in the paper.  Exclude common markers and reporters.';
  $hash{name3}{genestudied} = '<a style="color:#C11B17;" href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/community_gene_description.cgi" target="new">Update concise descriptions for these genes.</a>';
  $hash{exmp}{genestudied}  = 'Please use text box below to list any genes that were a focus of analysis in this research article.';
#   $hash{name}{genesymbol} = 'Newly cloned Novel Gene Symbol or Gene-CDS link.  E.g., xyz-1 gene was cloned and it turned out to be the same as abc-1 gene.';
  $hash{name}{genesymbol}   = 'Newly cloned gene.';
  $hash{name3}{genesymbol}  = '<a style="color:#C11B17;" href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/community_gene_description.cgi" target="new">Submit a concise description for this gene.</a>';
  $hash{exmp}{genesymbol}   = 'Please indicate if your paper reports a new symbol for a known locus or the name of a newly defined locus.';
#   $hash{name}{extvariation} = 'Newly created alleles.';
#   $hash{exmp}{extvariation} = 'Please indicate if your paper reports the identification of any allele that doesn\'t exist in WormBase already.';
  $hash{name}{mappingdata}  = 'Genetic mapping data.';
  $hash{exmp}{mappingdata}  = 'Please indicate if your paper contains 3-factor interval mapping data, i.e., genetic data only.  Include Df or Dp data, but no SNP interval mapping.';

  $hash{name}{gfp} = 'Gene Function';
  $hash{name}{phenanalysis} = 'Mutant, RNAi, Overexpression, or Chemical-based Phenotypes.';
  $hash{name}{newmutant}    = 'Single allele phenotype result (please include allele when reporting a phenotype)';
  $hash{name3}{newmutant}   = 'OR <a style="color:#C11B17;" href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/allele_phenotype.cgi" target="new">submit allele-phenotype data.</a>';
  $hash{exmp}{newmutant}    = 'Please indicate if your paper reports any phenotypes.';
  $hash{name}{rnai}   = 'Small-scale RNAi (less than 100 individual experiments).';
  $hash{exmp}{rnai}   = 'Please indicate if your paper reports gene knockdown phenotypes for less than 100 individual RNAi experiments.';
  $hash{name}{lsrnai} = 'Large-scale RNAi (greater than 100 individual experiments).';
  $hash{exmp}{lsrnai} = 'Please indicate if your paper reports gene knockdown phenotypes for more than 100 individual RNAi experiments.';
  $hash{name}{overexpr} = 'Overexpression phenotype.';
  $hash{exmp}{overexpr} = 'Please indicate if your paper reports an abnormal phenotype based on the overexpression of a gene or gene construct. E.g., \"...constitutively activated SCD-2(neu*) receptor caused 100% of animals to arrest in the first larval stage (L1)...\"';
  $hash{name}{chemicals} = 'Chemicals.';
  $hash{exmp}{chemicals} = 'Please indicate if the effects of small molecules, chemicals, or drugs were studied on worms, e.g., paraquat, butanone, benzaldehyde, aldicarb, etc. Mutagens used for the generation of mutants in genetic screens do not need to be indicated.';
  $hash{name}{mosaic} = 'Mosaic analysis.';
  $hash{exmp}{mosaic} = 'Please indicate if your paper reports cell specific gene function based on mosaic analysis, e.g. extra-chromosomal transgene loss in a particular cell lineage leads to loss of mutant rescue, etc.';
  $hash{name}{siteaction} = 'Tissue or cell site of action.';
  $hash{exmp}{siteaction} = 'Please indicate if your paper reports anatomy (tissue or cell)-specific expression function for a gene.';
  $hash{name}{timeaction} = 'Time of action.';
  $hash{exmp}{timeaction} = 'Please indicate if your paper reports a temporal requirement for gene function, that is, if gene activity was assayed, for example, through temperature-shift experiments.';
#   $hash{name}{genefunc} = 'Molecular function of a gene product.';
#   $hash{exmp}{genefunc} = 'Please indicate if your paper discusses a new function for a known or newly defined gene.';
  $hash{name}{humdis} = 'Homolog of a human disease-associated gene.';
  $hash{exmp}{humdis} = 'Please indicate if genes discussed in your paper are a homolog/ortholog of a human disease-related gene.';

  $hash{name}{int} = 'Interactions';
  $hash{name}{geneint} = 'Genetic interactions.';
  $hash{exmp}{geneint} = 'Please indicate if your paper reports the analysis of more than one gene at a time, e.g., double, triple, etc. mutants, including experiments where RNAi was concurrent with other RNAi-treatments or mutations.';
  $hash{name}{funccomp} = 'Functional complementation.';
  $hash{exmp}{funccomp} = 'Please indicate if your paper reports functional redundancy between separate genes, e.g., the rescue of <i>gen-A</i>, by overexpression of <i>gen-B</i> or any other extragenic sequence.';
  $hash{name}{geneprod} = 'Gene product interaction.';
  $hash{exmp}{geneprod} = 'Please indicate if your paper reports data on protein-protein, RNA-protein, DNA-protein, or Y2H interactions, etc.';

  $hash{name}{gef} = 'Regulation of Gene Expression';
  $hash{name}{otherexpr} = 'New expression pattern for a gene.';
  $hash{exmp}{otherexpr} = 'Please indicate if your paper reports new temporal or spatial (e.g. tissue, subcellular, etc.) data on the pattern of expression of any gene in a wild-type background. You can include: reporter gene analysis, antibody staining, <i>In situ</i> hybridization, RT-PCR, Western or Northern blot data.';
  $hash{name}{microarray} = 'Microarray.';
  $hash{exmp}{microarray} = 'Please indicate if your paper reports any microarray data.';
  $hash{name}{genereg} = 'Alterations in gene expression by genetic or other treatment.';
  $hash{exmp}{genereg} = 'Please indicate if your paper reports changes or lack of changes in gene expression levels or patterns due to genetic background, exposure to chemicals or temperature, or any other experimental treatment.';
  $hash{name}{seqfeat} = 'Regulatory sequence features.';
  $hash{exmp}{seqfeat} = 'Please indicate if your paper reports any gene expression regulatory elements, e.g., DNA/RNA elements required for gene expression, promoters, introns, UTR\'s, DNA binding sites, etc.';
  $hash{name}{matrices} = 'Position frequency matrix (PFM) or position weight matrix (PWM).';
  $hash{exmp}{matrices} = 'Please indicate if your paper reports PFMs or PWMs, which are typically used to define regulatory sites in genomic DNA (e.g., bound by transcription factors) or mRNA (e.g., bound by translational factors or miRNA). PFMs define simple nucleotide frequencies, while PWMs are scaled logarithmically against a background frequency.';

  $hash{name}{rgn} = 'Reagents.';
  $hash{name}{antibody} = '<i>C. elegans</i> antibodies.';
  $hash{exmp}{antibody} = 'Please indicate if your paper reports the use of new or known antibodies created by your lab or someone else\'s lab; do not check this box if antibodies were commercially bought.';
  $hash{name}{transgene} = 'Integrated transgene.';
  $hash{exmp}{transgene} = 'Please indicate if integrated transgenes were used in this paper. If the transgene does not have a canonical name, please list it in the "Add Information" text box.';
  $hash{name}{marker} = 'Transgenes used as tissue markers.';
  $hash{exmp}{marker} = 'Please indicate if reporters (integrated transgenes) were used to mark certain tissues, subcellular structures, or life stages, etc. as a reference point to assay gene function or location.';

  $hash{name}{pfs} = 'Protein Function and Structure';
  $hash{name}{invitro} = 'Protein analysis <i>in vitro</i>.';
  $hash{exmp}{invitro} = 'Please indicate if your paper reports any <i>in vitro</i> protein analysis such as kinase assays, agonist pharmacological studies, <i>in vitro</i> reconstitution studies, etc.';
  $hash{name}{domanal} = 'Analysis of protein domains.';
  $hash{exmp}{domanal} = 'Please indicate if your paper reports on a function of a particular domain within a protein.';
  $hash{name}{covalent} = 'Covalent modification.';
  $hash{exmp}{covalent} = 'Please indicate if your paper reports on post-translational modifications as assayed by mutagenesis or in vitro analysis.';
  $hash{name}{structinfo} = 'Structural information.';
  $hash{exmp}{structinfo} = 'Please indicate if your paper reports NMR or X-ray crystallographic information.';
  $hash{name}{massspec} = 'Mass spectrometry.';
  $hash{exmp}{massspec} = 'Please indicate if your paper reports data from any mass spec analysis e.g., LCMS, COSY, HRMS, etc. Keywords: mass spectrometry, peptide, (and any one of the following:) MASCOT, SEQUEST, X!Tandem, OMSSA, MassMatrix';
  
  $hash{name}{seq} = 'Genome Sequence Data';
  $hash{name}{structcorr} = 'Gene structure correction.';
  $hash{exmp}{structcorr} = 'Please indicate if your paper reports a gene structure that is different from the one in WormBase, e.g., different splice-site, SL1 instead of SL2, etc.';
  $hash{name}{seqchange} = 'Sequencing mutant alleles.';
  $hash{exmp}{seqchange} = 'Please indicate if your paper reports new sequence data for any mutation.';
  $hash{name}{newsnp} = 'New SNPs, not already in WormBase.';
  $hash{exmp}{newsnp} = 'Please indicate if your paper reports a SNP that does not already exist in WormBase.';
  
  $hash{name}{cell} = 'Cell Data';
  $hash{name}{ablationdata} = 'Ablation data.';
  $hash{exmp}{ablationdata} = 'Please indicate if your paper reports data from an assay involving any cell or anatomical unit being ablated by laser or by other means (e.g. by expressing a cell-toxic protein).';
  $hash{name}{cellfunc} = 'Cell function.';
  $hash{exmp}{cellfunc} = 'Please indicate if your paper reports a function for any anatomical part (e.g., cell, tissue, etc.), which has not been indicated elsewhere on this form.';

  $hash{name}{sil} = 'In Silico Data';
  $hash{name}{phylogenetic} = 'Phylogenetic analysis.';
  $hash{exmp}{phylogenetic} = 'Please indicate if your paper reports any phylogenetic analysis.';
  $hash{name}{othersilico}  = 'Other bioinformatics analysis.';
  $hash{exmp}{othersilico}  = 'Please indicate if your paper reports any bioinformatic data not indicated anywhere else on this form.';

#   $hash{name}{rgn} = 'Reagents.';

  $hash{name}{oth} = 'Other';
  $hash{name}{supplemental} = 'Supplemental materials.';
  $hash{exmp}{supplemental} = 'Please indicate if your paper has supplemental material.';
  $hash{name}{nocuratable}  = 'NONE of the aforementioned data types are in this research article.';
  $hash{exmp}{nocuratable}  = 'Please indicate if none of the above pertains to your paper. Feel free to list the data type most pertinent to your research paper in the "Add information" text area.';
  $hash{name}{comment} = 'Any feedback ?';
  $hash{exmp}{comment} = 'Please feel free to give us feedback for this form or for any other topic pertinent to how we can better extract data from your paper.';
  $hash{name}{email} = 'Contact e-mail';
  $hash{exmp}{email} = 'This e-mail address will be used to contact you if there are any further questions. If this is not your e-mail address please add it now.';
} # sub hashName

__END__


# my $DB = Ace->connect(-path  =>  '/home/acedb/ts',
#                       -program => '/home/acedb/bin/tace') || die "Connection failure: ",Ace->error;

sub displayTypeOne {
  my ($paper, $passwd) = &checkPaperPasswd();
  return if ($paper eq 'bad');
  &printForm();
  print "<INPUT TYPE=HIDDEN NAME=paper VALUE=$paper>\n"; print "<INPUT TYPE=HIDDEN NAME=passwd VALUE=$passwd>\n";
  print "<B>If this is a <FONT COLOR=red>Review</FONT> just click this button and ignore the fields below : </B><INPUT TYPE=submit NAME=action VALUE=\"Review\"><BR><P>\n";
  foreach my $cat (@cats) {
    print "<H1>$hash{name}{$cat} :</H1><P>\n";
    foreach my $table (@{ $hash{cat}{$cat} }) { 
      my ($data) = &getPgData($table, $paper);
      if ($data) { $data = 'checked'; }
#       print "<INPUT TYPE=checkbox NAME=\"${table}_check\" $data>$hash{name}{$table} <FONT COLOR=red>$table</FONT><BR>\n"; 
#       if ($curatorOnly{$table}) { print "<FONT COLOR=red>Only curators will see this line : </FONT>\n"; }
      print "<INPUT TYPE=checkbox NAME=\"${table}_check\" $data>$hash{name}{$table} <FONT COLOR=white>$table</FONT><BR>\n"; 
    }
  } # foreach my $cat (@cats)
  print "<P><BR><INPUT TYPE=submit NAME=action VALUE=\"Flag\"><BR>\n";
  print "</FORM>\n";
} # sub displayTypeOne


sub OLDwritePg {
  my ($table, $joinkey, $data) = @_;
  next unless ($data);		# skip if there's no data
  $table = 'afp_' . $table;
  my $result = $conn->exec( "SELECT * FROM $table WHERE joinkey = '$joinkey';" );
  my @row = $result->fetchrow();
# UNCOMMENT THESE TO WRITE TO POSTGRES
#   if ($row[0]) {				# if there was previous data in postgres
#       my $update = 0;
#       if ($data ne 'checked') { $update++; }	# real data, always update
#       elsif ( ($row[1] eq 'checked') && ($data eq 'checked') ) { $update++; }	# was checked and is checked, update to get new timestamp
#       elsif ( ($row[1] ne 'checked') && ($data eq 'checked') ) { $update = 0; }	# was real data and is now checked, ignore, not new data
#       if ($update > 0) {
#         $result = $conn->exec( "UPDATE $table SET $table = '$data' WHERE joinkey = '$joinkey';" );
#         $result = $conn->exec( "UPDATE $table SET afp_timestamp = CURRENT_TIMESTAMP WHERE joinkey = '$joinkey';" ); } }
#     else { $result = $conn->exec( "INSERT INTO $table VALUES ('$joinkey', '$data');" ); }
} # sub OLDwritePg

sub messageAndrei {
  my $body = shift;
  my $user = 'paper_fields.cgi';
  my $email = 'petcherski@gmail.com';
#   my $email = 'azurebrd@tazendra.caltech.edu';
  my $subject = 'Updated Author Flagging Form';
#   print "$body<BR>\n";
#   &mailer($user, $email, $subject, $body);    # email CGI to user
} # sub messageAndrei

sub gotText {
  my ($paper, $passwd) = &checkPaperPasswd();
  return if ($paper eq 'bad');
  my $body = "Paper $paper Text data\n";
  foreach my $cat (@cats, "comment") {
    foreach my $table (@{ $hash{cat}{$cat} }) { 
      (my $oop, my $text) = &getHtmlVar($query, "${table}_text");
      if ($text) { 
        &writePg($table, $paper, $text);
        $body .= "$table :\t$text\n";
        &textTable($table, $text); }
    } # foreach my $table (@{ $hash{cat}{$cat} })
  } # foreach my $cat (@cats)
  &messageAndrei($body);
} # sub gotText

sub OLDgotFlagged {
  my ($paper, $passwd) = &checkPaperPasswd();
  return if ($paper eq 'bad');
  &printForm();
  print "<INPUT TYPE=HIDDEN NAME=paper VALUE=$paper>\n"; print "<INPUT TYPE=HIDDEN NAME=passwd VALUE=$passwd>\n";
  (my $oop, my $paper) = &getHtmlVar($query, 'paper');
  ($oop, my $passwd) = &getHtmlVar($query, 'passwd');
  print "<INPUT TYPE=HIDDEN NAME=paper VALUE=$paper>\n";
  print "<INPUT TYPE=HIDDEN NAME=passwd VALUE=$passwd>\n";
  print "This page is optional. Brief notes that will help curators to locate the data you flagged on the previous page are highly appreciated (e.g.  \"Y2H fig.5\").<P><BR>\n";

  my $body = "Paper $paper flagged\n";
  foreach my $cat (@cats, "comment") {
    foreach my $table (@{ $hash{cat}{$cat} }) { 
      (my $oop, my $checked) = &getHtmlVar($query, "${table}_check");
      if ( ($checked) || ($table eq 'comment') ) { 
        &writePg($table, $paper, 'checked');
        $body .= "$table\tchecked\n";
        my ($data) = &getPgData($table, $paper);
        &checkedTable($table, $data); }
    } # foreach my $table (@{ $hash{cat}{$cat} })
  } # foreach my $cat (@cats)
  print "<P><BR><INPUT TYPE=submit NAME=action VALUE=\"Submit Text\"><BR>\n";
  print "</FORM>\n";
  &messageAndrei($body);
} # sub OLDgotFlagged

sub textTable {
  my ($table, $text) = @_;
  print "$hash{name}{$table} : $text<P>\n"; 
} # sub textTable

sub checkedTable {
  my ($table, $data) = @_;
  if ($data eq 'checked') { $data = ''; }
  my $textarea_name = $hash{name}{$table}; if ($hash{name2}{$table}) { $textarea_name = $hash{name2}{$table}; }
  print "$textarea_name :<BR><TEXTAREA NAME=\"${table}_text\" ROWS=4 COLS=80>$data</TEXTAREA><BR><P>\n"; 
} # sub checkedTable


