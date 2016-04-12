#!/usr/bin/perl 

# Form to submit Multi-point information.

# an allele form to make .ace files and email curator
# This version gets headers and footers off of www.wormbase.org with LWP / Jex,
# untaints and gets HTML values with CGI / Jex, sends mail with Mail::Mailer /
# Jex   2002 05 14
#
# Parses data and outputs names of html fields and values (placed in $body) and
# also tried to parse out .ace entries (place in $ace_body).  These are emailed
# and written to the flatfile, then the \n are parsed into <BR>\n for html
# display.  Some html fields don't have a corresponding .ace entry (NULL), so
# they are ignored in the .ace part.  Some are radio buttons that do have an
# entry, so these are part of an if/elsif/else statement that checks if it's one
# of those fields, and gets the appropriate .ace tag from the selected (radio)
# value.  Likewise for Flanking_sequences since they need to specify (left) or
# (right).   2002 11 04
#
# Have more meaningful names for the values of loss/gain_of_function.  Place
# them in Remark specifying loss/gain_of_function.   Parse Allelic_difference
# to [A\/G] format if possible.  2002 11 06
#
# Added penetrance radio and text field.  Added Species radio and text field.
# Added text field for Insertion and Deletion.  Added link to labcore.ace for
# Lab designation.  Rearranged form into Mandatory, Genetic, Physical, Personal
# 2002 11 07
#
# Recessive, Semi_dominant, Dominant, Heat_sensitive, Cold_sensitive no longer
# write vals to .ace file (just tags).  Allele tag no longer has square
# brackets.  2002 11 08
#
# Added Partial to the .ace file.  Parse out line breaks from input.  Put paper
# evidence into Remark for .ace file  2003 03 11
#
# Added Penetrance tag to .ace file if they clicked complete.  Added Reference
# tag if data matches cgc or pmid, otherwise puts it in Remark.  2003 03 12
#
# Added allele to subject line (made ``allele data'' in subject be ``Allele'')  
# 2003 04 15
#
# Changed C. to Caenorhabditis and P. to Pristionchus for Keith.
# Changed Uncharacterized loss_of_function to Uncharacterised_loss_of_function 
# for Keith.
# Added $keith_body variable for parts of body to email but not show on webpage.
# added &findName(); &processAkaSearch(); and &getPgHash(); to find possible
# name matches to the user-submitted name.  2003 08 08
#
# Changed Uncharacterized gain_of_function to Uncharacterised_gain_of_function 
# for Keith.   Added Method tag to be "Allele" unless Deletion or Transposon
# Insertion are chosen under Type of Alterations.  (see $keith_method).  2003 08 14
#
# Changed $keith_method to be "Allele" not "Method" by default, took out the
# words XREF $allele from the Reference tag output.  2003 08 18
#
# Added Mutagen and Isolation.  2004 01 23
#
# Edited for Multi-Point data for Chao-Kung.  2004 02 19
#
# Chao-Kung not in WormBase, changed to cgc@wormbase.org   2004 07 07
#
# If it's spam skip doing anything  2007 08 24



my $acefile = "/home/azurebrd/public_html/cgi-bin/data/multi.ace";

my $firstflag = 1;		# flag if first time around (show form for no data)

# use LWP::Simple;
# use Mail::Mailer;

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $query = new CGI;
my $user = 'multi_form';	# who sends mail
# my $email = 'ck1@sanger.ac.uk';	# to whom send mail
# my $email = 'cgc@wormbase.org';	# to whom send mail
my $email = 'genenames@wormbase.org';	# to whom send mail 2007 09 19
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = 'Multi-point Submission Form';	# subject of mail
my $body = '';			# body of mail
my $ace_body = '';		# body of ace file
my $keith_body = '';		# body to mail but not show in form output

my @all_vars = qw( geneA geneB person_evidence submitter_email date genotype combined a_non_b b_non_a lab comment );
#       my @all_vars = qw ( person_evidence submitter_email gene nature_of_allele penetrance partial_penetrance temperature_sensitive loss_of_function gain_of_function paper_evidence lab phenotypic_description sequence genomic assoc_strain species species_other alteration_type mutagen point_mutation_gene transposon_insertion sequence_insertion deletion upstream downstream comment );

print "Content-type: text/html\n\n";
my $title = 'Multi-point Submission Form';
my ($header, $footer) = &cshlNew($title);
print "$header\n";		# make beginning of HTML page

&process();			# see if anything clicked
&display();			# show form as appropriate
print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'Submit') { 
    $firstflag = "";				# reset flag to not display first page (form)

    my $mandatory_ok = 'ok';			# default mandatory is ok
    my $sender = '';
    my @mandatory = qw ( geneA geneB submitter_email person_evidence );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{geneA} = "geneA";
    $mandatoryName{geneB} = "geneB";
    $mandatoryName{person_evidence} = "Data Provider";
 
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
      }
    } # foreach $_ (@mandatory)

    my $spam = 0;                               # if it's spam skip doing anything  2007 08 24
    foreach $_ (@all_vars) {                    # for all fields, check for spam
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val =~ m/\S/) {      # if value entered
        if ($val =~ m/a href/i) {
          my (@spam) = $val =~ m/(a href)/gi;
          foreach my $sp (@spam) { $spam++; } } } }
#     print "SPAM $spam SPAM<BR>\n";
    if ($spam > 0) { print "Ignoring.  This is spam<BR>\n"; return; }


      # check results have data
    my ($var, $comb) = &getHtmlVar($query, 'combined');
    ($var, my $ab) = &getHtmlVar($query, 'a_non_b');
    ($var, my $ba) = &getHtmlVar($query, 'b_non_a');
    if ($comb eq '') {
      if ( ($ab eq '') || ($ba eq '') ) { 
        $mandatory_ok = 'bad'; 
        print "<FONT COLOR=red SIZE=+2>Need to enter either (Combined Results) OR (A-non-B results AND B-non-A results)</FONT><BR>\n"; } }

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
      $body .= "$sender from ip $host sends :\n\n";
  
      my %aceName;
      $aceName{geneA} = 'Locus_A';
      $aceName{geneB} = 'Locus_B';
      $aceName{person_evidence} = 'Mapper';
      $aceName{submitter_email} = 'NULL';
      $aceName{date} = 'Date';
      $aceName{genotype} = 'Genotype';
      $aceName{combined} = 'Combined';
      $aceName{a_non_b} = 'A_non_B';
      $aceName{b_non_a} = 'B_non_A';
      $aceName{lab} = 'Laboratory';
      $aceName{comment} = 'Remark';

      my %bodyName;
      $bodyName{geneA} = 'Multi_pt_GeneA';
      $bodyName{geneB} = 'Multi_pt_GeneB';
      $bodyName{person_evidence} = 'Multi_pt_Data_provider';
      $bodyName{submitter_email} = 'NULL';
      $bodyName{date} = 'Multi_pt_Date';
      $bodyName{genotype} = 'Multi_pt_Genotype';
      $bodyName{combined} = 'Multi_pt_Combined_results';
      $bodyName{a_non_b} = 'Multi_pt_A_non_B_results';
      $bodyName{b_non_a} = 'Multi_pt_B_non_A_results';
      $bodyName{lab} = 'Multi_pt_Laboratory';
      $bodyName{comment} = 'Multi_pt_Comment';
# //Multi_pt_EMAIL : --
# Multi_pt_GeneA : dpy-5
# Multi_pt_GeneB : unc-101
# Multi_pt_Combined_results : dpy-5 32 cfi-1 84 unc-101
# Multi_pt_Comment : data extracted from cgc5226
# Multi_pt_Data_provider : Shaham S
# Multi_pt_data_type : --Multi_pt
# Multi_pt_Genotype : dpy-5 cfi-1 unc-101/ + + + (CB4856)
# Multi_pt_B_non_A_results : lin-17 3 mig-30 21 unc-11
# Multi_pt_A_non_B_results : lin-17 3 mig-30 28 unc-11
# Multi_pt_Date :


      my ($var, $geneA) = &getHtmlVar($query, 'geneA');
      $result = $dbh->do( "INSERT INTO mul_gene (mul_gene) VALUES ('$geneA');" );
						# this updated the pg sequence mul_seq to nextval
      $result = $dbh->prepare( "SELECT currval('mul_seq');" );	
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
						# can get currval because last line updated
      my @row = $result->fetchrow;
      $joinkey = $row[0];
#       $joinkey = '1234567';
      print "Multi-point entry number $joinkey<BR><BR>\n";
      $result = $dbh->do( "INSERT INTO mul_ip VALUES ('$joinkey', '$host');" );
  
      foreach $_ (@all_vars) { 			# for all fields, check for data and output
        my ($var, $val) = &getHtmlVar($query, $_);
        if ($val =~ m/\S/) { 	# if value entered
          my $ace_val = $val;
          if ($var eq 'date') { $val =~ s/\//-/g; }	# use hyphen instead of slash for date
	  elsif ( ($var eq 'combined') || ($var eq 'a_non_b') || ($var eq 'b_non_a') ) {
            if ($val =~ m/([a-z]{3}-\d+)\s+(\d+)\s+([a-z]{3}-\d+)\s+(\d+)\s+([a-z]{3}-\d+)/) { 
              $ace_val = "$1\" $2 Locus \"$3\" $4 Locus \"$5"; } }
          elsif ( ($var eq 'geneA') || ($var eq 'geneB') ) { $val = lc($val); }
          else { 1; }
          if ($aceName{$var} ne 'NULL') { $ace_body .= "$aceName{$var}\t\"$ace_val\"\n"; }
	    else { 1; }
          if ($bodyName{$var} ne 'NULL') { $body .= "$bodyName{$var}\t\"$val\"\n"; }
	    else { 1; }
          if ($var eq 'person_evidence') { &findName($val); }
          my $pg_table = 'mul_' . $var;
          $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
        } # if ($val) 
      } # foreach $_ (@vars) 
      my $full_body = $body . "\n" . $ace_body;
      $keith_body .= "\n" . $body . "\n" . $ace_body;
      print OUT "$full_body\n";			# print to outfile
      close (OUT) or die "cannot close $acefile : $!";
#       print "MAIL TO : $sender :<BR>\n"; 
      $email .= ", $sender";
      &mailer($user, $email, $subject, $keith_body);	# email the data
      $body =~ s/\n/<BR>\n/mg;
      $ace_body =~ s/\n/<BR>\n/mg;
      print "BODY : <BR>$body<BR><BR>\n";
      print "ACE : <BR>$ace_body<BR><BR>\n";
      print "<P><P><P><H1>Thank you for your submission.  You will be contacted by WormBase within three working days.</H1>\n";
      print "If you wish to modify your submitted information, please go back and resubmit.<BR><P> <!--See all <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/allele.ace\">new submissions</A>.<P>-->\n";
    } # else # if ($mandatory_ok eq 'bad')
  } # if ($action eq 'Submit') 
} # sub process


sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";

<h1>Multi-point mapping data submission form</h1><p>
<p>This is designed to capture data from 3 point, 4 point, 5 point and n-point mapping experiments.

It is essential to specify Genes A and B.

In the results lines, geneA MUST be the first gene named, geneB MUST be the last gene named with other genes in between.<p>

Not all of the boxes have to be filled to submit your data. Just fill in the relevant ones.<p>

If you would like more guidance and further examples click here for <a href="#multi">more information</a>.

</p>   

<hr>
<FORM METHOD="POST" ACTION="multi_pt.cgi">
   <FONT SIZE=+2><B>REQUIRED</B></FONT>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>

    <TABLE ALIGN="center"> 
      <TR><TD ALIGN="right"><FONT COLOR='red'><B>GeneA:&nbsp;</FONT></B></TD>
          <TD><Input Type="Text" Name="geneA" Size="50"></TD>
          <TD>(eg. dpy-11)</TD><TD>
      </TR>	  
      <TR><TD ALIGN="right"><FONT COLOR='red'><B>GeneB:&nbsp;</FONT></B></TD>
          <TD><Input Type="Text" Name="geneB" Size="50"></TD>
          <TD>(eg, unc-42)</TD><TD>
      </TR>
      <TR>    
          <TD ALIGN="right"><U><FONT COLOR='red'><B>Data provider</FONT></U> :</B></TD>
          <TD><Input Type="Text" Name="person_evidence" Size="50"></TD> 
          <TD>(eg. Hodgkin JA)</TD>
      </TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>

    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Email</FONT></U> :</B><BR>(please enter for contact purpose)
        <BR>If you don't get a verification email,<BR>email us at webmaster\@wormbase.org</TD>
        <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
    </TABLE>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD></TR><p><p>

    <TABLE ALIGN="center"> 
        <TR><TD ALIGN="right"><B>Date:&nbsp;</B></TD>
            <TD><Input Type="Text" Name="date" Size="50"></TD>
            <TD>(eg, yyyy-mm: 1990-01 or 1995-12)</TD><TD>
        </TR>	
        <TR><TD ALIGN="right"><B>Genotype:&nbsp;</B></TD>
            <TD><TEXTAREA Name="genotype" Rows=4 Cols=41></TEXTAREA></TD>  
            <TD>(eg, her-1(e224)/dpy-11(e1518) unc-42(e270) )</TD><TD>
        </TR>		  	  
      <TR><TD ALIGN="right"><B>Results:&nbsp;</TD>
            <TD ALIGN="left"><font color="blue"><B>either fill in Combined_results, OR preferably,<br>fill in both A_non_B and B_non_A results</font></B></TD>
	</TR><TR></TR><TR></TR>
      <TR bgcolor="#E8EEEE"><TD ALIGN="right"><B>&nbsp;&nbsp;&nbsp;&nbsp;Combined results :&nbsp;</B></TD>
        <TD><Input Type="Text" Name="combined" Size="50"></TD>
        <TD>(e.g. dpy-11 <font color="blue">58</font> her-1 <font color="blue">2</font> unc-42)</TD>
	</TR></TR><TR></TR></TR><TR></TR></TR><TR></TR>
      <TR bgcolor="#DCDDE7"><TD ALIGN="right"><B>&nbsp;&nbsp;&nbsp;&nbsp;A-non-B results :&nbsp;</B></TD>
        <TD><Input Type="Text" Name="a_non_b" Size="50"></TD>
        <TD>(e.g. dpy-11 <font color="blue">27</font> her-1 <font color="blue">0</font> unc-42)</TD> </TR>		
      <TR bgcolor="#DCDDE7"><TD ALIGN="right"><B>&nbsp;&nbsp;&nbsp;&nbsp;B-non-A results :&nbsp;</B></TD>
        <TD><Input Type="Text" Name="b_non_a" Size="50"></TD>
        <TD>(e.g. dpy-11 <font color="blue">31</font> her-1 <font color="blue">2</font> unc-42)</TD>
	</TR>
        <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
        <TD></TR>	      
       </TR>
 <!--       <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
	<TR></TR> <TR></TR> <TR></TR> <TR></TR>
	<TR></TR> <TR></TR> <TR></TR> <TR></TR>-->
  </TABLE>


    <TR><TD><FONT SIZE=+2><B>PERSONAL</B></FONT></TD></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>

    <TABLE ALIGN="center">   
    <TR><TD ALIGN="right"><B>CGC Laboratory designation</B><BR>
           (if known, eg., CB, PS.  <BR>See list 
            <A HREF="http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/labcore.ace">here</A>.)</TD>
        <TD><Input Type="Text" Name="lab" Size="50" Maxlength="3"></TD></TR>
    <TR></TR><TR><TD ALIGN="right"><B>Comment :</B></TD>
        <TD><TEXTAREA Name="comment" Rows=5 Cols=38></TEXTAREA></TD>
        <TD></TD></TR><TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    </TABLE>

    <TABLE ALIGN="center">   	    
    <TR><TD> </TD>
      <TD><INPUT TYPE="submit" NAME="action" VALUE="Submit"><INPUT TYPE="reset"></TD></TR>
    </TABLE>
</FORM>
<hr>

<a name ="multi">
<h2>Multi-pt examples:</h2><p>

<font color="blue">Example 1:</font><p> 

Mapper: Hodgkin JA<br>
Date: 1982-01<br>
Genotype: her-1(e224)/dpy-11(e1518) unc-42(e270)<br>
GeneA: dpy-11<br>
GeneB: unc-42<br>
A_non_B_results: dpy-11 27 her-1 0 unc-42<br>
B_non_A_results: dpy-11 31 her-1 2 unc-42<p>

<font color="blue">Example 2:</font><p> 

Mapper: Hodgkin JA<br>
Date: 1983-05<br>
Genotype: mor-2(e1125)/unc-5(e53) him-8(e1489) dpy-20(e1282)<br>
GeneA: unc-5<br>
GeneB: dpy-20<br>
Combined_results: unc-5 1 mor-2 7 him-8 2 dpy-20<p>

<font color="blue">Example 3:</font><p>  

Mapper: Hodgkin JA<br>
Date: 1997-12<br>
Genotype: unc-5(e53) dpy-20(e1282)/eP2000 eP2001 eP2002 eP2003<br>
GeneA: unc-5<br>
GeneB: dpy-20<br>
A_non_B_results: unc-5 0 eP2000 13 eP2003 0 eP2001 6 eP2002 1 dpy-20<br>
Comment: polymorphism data<p>

<font color="blue">Example 4:</font><p> 

Note that this example illustrates that the results lines always have
GeneA first and GeneB last, even though it may be known that
the gene of interest is actually located to the left of GeneA or
to the right of GeneB.<p><br>

Mapper : Labouesse M<br>
GeneA : unc-23<br>
GeneB : sma-1<br>
Combined_results : unc-23 50 rdy-2 0 sma-1<br>
B_non_A_results : unc-23 25 rdy-2 0 sma-1<br>
A_non_B_results : unc-23 25 rdy-2 0 sma-1<br>
Comment :  other data show that rdy-2 maps to the right of sma-1<p>
</FORM>
If you have any problems, questions, or comments, please contact <A HREF=\"mailto:gnw\@wormbase.org\">gnw\@wormbase.org</A>
EndOfText

  } # if (firstflag) show form 
} # sub display 



sub display2 {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";


<A NAME="form"><H1>Allele Data Submission Form :</H1></A>
<B>Please fill out as many fields as possible.  First three fields are required.</B><P>

<HR>


<FORM METHOD="POST" ACTION="allele.cgi">
  <TABLE>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>REQUIRED</B></FONT></TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Allele</FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="allele" Size="50"></TD>
        <TD>(eg. e53) <!--=&gt; main tag--></TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Name</FONT></U> :</B>
	   <BR>Please enter full name, eg. John Sulston</TD>
        <TD><Input Type="Text" Name="person_evidence" Size="50"></TD>
        <TD><!--=&gt; Author tag (Isolation)?? Need Caltech feedback--></TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Email</FONT></U> :</B>
	   <BR>(please enter for contact purpose)</TD>
        <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
        <TD><!--=&gt; for curator's info--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD></TR>

    <TR><TD ALIGN="right"><B>CGC locus name of gene :</B></TD>
        <TD><Input Type="Text" Name="gene" Size="50"></TD>
        <TD>(if known, eg. aap-1) <!--=&gt; Gene tag--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="left"><B>Nature of Alleles :</B></TD></TR>
    <TR><TD ALIGN="right"><B>Recessive :</B>
	   <Input Type="radio" Name="nature_of_allele" Value="recessive"></TD>
	<TD></TD>
	<TD><!--=&gt; Recessive tag (Description)--></TD></TR>
    <TR><TD ALIGN="right"><B>Semi-dominant :</B>
	   <Input Type="radio" Name="nature_of_allele" Value="semi_dominant"></TD>
        <TD></TD>
	<TD><!--=&gt; Semi_dominant tag (Description)--></TD></TR>
    <TR><TD ALIGN="right"><B>Dominant :</B>
	   <Input Type="radio" Name="nature_of_allele" Value="dominant"></TD>
	<TD></TD>
        <TD><!--=&gt; Dominant tag (Description)--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="left"><B>Penetrance :</B></TD>
	<TD></TD>
	<TD>% animals displaying the phenotype</TD></TR>
    <TR><TD ALIGN="right"><B>Complete :</B>
	   <Input Type="radio" Name="penetrance" Value="complete"></TD>
	<TD></TD>
	<TD></TD></TR>
    <TR><TD ALIGN="right"><B>Partial :</B>
	   <Input Type="radio" Name="penetrance" Value="partial"></TD>
        <TD><Input Type="Text" Name="partial_penetrance" Size="50"></TD>
	<TD></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="left"><B>Temperature Sensitive :</B></TD></TR>
    <TR><TD ALIGN="right"><B>Heat sensitive :</B>
	   <Input Type="radio" Name="temperature_sensitive" Value="heat_sensitive"></TD>
	<TD></TD>
	<TD><!--=&gt; Heat_sensitive tag (Temperature_sensitive)--></TD></TR>
    <TR><TD ALIGN="right"><B>Cold sensitive :</B>
	   <Input Type="radio" Name="temperature_sensitive" Value="cold_sensitive"></TD>
	<TD></TD>
	<TD><!--=&gt; Cold_sensitive tag (Temperature_sensitive)--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR><TR><TD ALIGN="right"><B>Loss of Function :</B></TD>
        <TD><Select Name="loss_of_function"  Size=1>
                   <Option Value="" Selected>Not Applicable
                   <Option Value="Uncharacterised_loss_of_function">Uncharacterised_loss_of_function
                   <Option Value="Haplo-insufficient">Haplo-insufficient
                   <Option Value="Hypomorph">Hypomorph      
                   <Option Value="Null (amorph)">Null (amorph)
            </Select></TD>
        <TD><!--Note: Drop-down option goes to Remark tag, as currently there is no such tag in
            the ?Allele model. Maybe in the future?--></TD></TR><TR></TR>

    <TR></TR><TR><TD ALIGN="right"><B>Gain of Function :</B></TD>
        <TD><Select Name="gain_of_function"  Size=1>
                   <Option Value="" Selected>Not Applicable
                   <Option Value="Uncharacterised_gain_of_function">Uncharacterised_gain_of_function
                   <Option Value="Hypermorph">Hypermorph
                   <Option Value="Neomorph">Neomorph
                   <Option Value="Dominant Negative">Dominant Negative
            </Select></TD>
        <TD><!--Note: Drop-down option goes to Remark tag, as currently there is no such tag in
            the ?Allele model. Maybe in the future?--></TD></TR><TR></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><B>Has this allele been published?</B><BR>If so, where:<BR>
	   (e.g. journal reference, PMID or CGC number. <BR>
	   Please leave blank if unpublished)</TD>
        <TD><Input Type="Text" Name="paper_evidence" Size="50"></TD>
        <TD><!--=&gt; ?? Need Caltech feedback--></TD></TR>
    <TR><TD ALIGN="right"><B>CGC Laboratory designation</B><BR>
	   (if known, eg., CB, PS.  <BR>See list 
	    <A HREF="http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/labcore.ace">here</A>.)</TD>
        <TD><Input Type="Text" Name="lab" Size="50" Maxlength="3"></TD>
        <TD><!--=&gt; Location ?Laboratory XREF Alleles--></TD></TR>

    <TR></TR><TR><TD ALIGN="right"><B>Phenotypic Description :</B></TD>
        <TD><TEXTAREA Name="phenotypic_description" Rows=5 Cols=50></TEXTAREA></TD>
        <TD><!--=&gt; Phenotype tag ?Text--></TD></TR><TR></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>PHYSICAL</B></FONT></TD></TR>
    <TR><TD ALIGN="right"><B>Sequence name of gene :</B></TD>
        <TD><Input Type="Text" Name="sequence" Size="50"></TD>
        <TD>(CDS, eg., B0303.3) <!--=&gt;Sequence tag (Source)--></TD></TR>
    <TR><TD ALIGN="right"><B>Genomic Sequence that contains allele :</B></TD>
        <TD><Input Type="Text" Name="genomic" Size="50"></TD>
        <TD>(eg., B0303) <!--=&gt; for curator's info--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><B>Associated strain :</B></TD>
<!--    <TR><TD ALIGN="left"><B>Associated strain :</B></TD>-->
        <TD><TEXTAREA Name="assoc_strain" Rows=5 Cols=50></TEXTAREA></TD>
        <TD>Please enter the Genotype and Strain number in tab-delimited format. e.g.<BR>
	    Genotype&lt;TAB&gt;Strain# &lt;Enter&gt;<BR></TD></TR><TR></TR>
   
<!--    <TR><TD ALIGN="right"><B>Genotype :</B>
        <TD><Input Type="Text" Name="genotype" Size="50"></TD>
        <TD>(Please enter strain name if known, eg. AA18.  If not please enter both strain name and genotype) <!--=&gt; strain tag</TD></TR>
    <TR><TD ALIGN="right"><B>Strain Name :</B>
        <TD><Input Type="Text" Name="strain" Size="50"></TD>
        <TD></TD></TR>-->

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="left"><B>Species :</B></TD>
	<TD></TD>
	<TD></TD></TR>
    <TR><TD ALIGN="right"><B>Caenorhabditis elegans :</B>
	   <Input Type="radio" checked Name="species" Value="Caenorhabditis elegans"></TD>
	<TD></TD>
	<TD></TD></TR>
    <TR><TD ALIGN="right"><B>Caenorhabditis briggsae :</B>
	   <Input Type="radio" Name="species" Value="Caenorhabditis briggsae"></TD>
	<TD></TD>
	<TD></TD></TR>
    <TR><TD ALIGN="right"><B>Pristionchus pacificus :</B>
	   <Input Type="radio" Name="species" Value="Pristionchus pacificus"></TD>
	<TD></TD>
	<TD></TD></TR>
    <TR><TD ALIGN="right"><B>Other :</B>
	   <Input Type="radio" Name="species" Value="other"></TD>
        <TD><Input Type="Text" Name="species_other" Size="50"></TD>
	<TD></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR><TR><TD ALIGN="left"><B>Isolation :</B></TD></TR>
    <TR><TD align="right"><B>Mutagen :</B></TD>
        <TD><Input Type="Text" Name="mutagen" Size="50"></TD>
        <TD> (eg. EMS, ENU)</TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR><TR><TD ALIGN="left"><B>Type of Alterations :</B></TD></TR>
    <TR><TD align="right"><B>Point mutation/dinucleotide mutation :</B>
           <Input Type="radio" Name="alteration_type" Value="point_mutation"></TD>
        <TD><Input Type="Text" Name="point_mutation_gene" Size="50"></TD>
        <TD> (eg. c to t OR c to ag) <!--=&gt; Allelic_difference tag (Sequence_details)--></TD></TR>
    <TR><TD align="right"><B>Transposon Insertion :</B>
	   <Input Type="radio" Name="alteration_type" Value="transposon_insertion"></TD>
        <TD><Input Type="Text" Name="transposon_insertion" Size="50"></TD>
	<TD>(e.g. Tc1) <!--=&gt; Transposon_insertion tag (Description)--></TD></TR>
    <TR><TD align="right"><B>Sequence Insertion :</B>
	   <Input Type="radio" Name="alteration_type" Value="sequence_insertion"></TD>
        <TD><Input Type="Text" Name="sequence_insertion" Size="50"></TD>
	<TD>(e.g. atctggaacc...) <!--=&gt; Insertion tag (Description)--></TD></TR>
    <TR><TD align="right"><B>Deletion :</B>
	   <Input Type="radio" Name="alteration_type" Value="deletion"></TD>
        <TD><Input Type="Text" Name="deletion" Size="50"></TD>
	<TD>(Please enter deleted sequence) <!--=&gt; Deletion tag (Description)--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD align="right"><B>As many as possible up to 30 bp upstream flanking sequence :</B></TD>
        <TD><Input Type="Text" Name="upstream" Size="50"></TD>
        <TD> <!--=&gt; Flanking_sequences UNIQUE tag Text (left)--></TD></TR>
    <TR><TD align="right"><B>As many as possible up to 30 bp downstream flanking sequence :</B></TD>
        <TD><Input Type="Text" Name="downstream" Size="50"></TD>
        <TD> <!--=&gt; Flanking_sequences UNIQUE tag Text (right)--></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>PERSONAL</B></FONT></TD></TR>

    <TR></TR><TR><TD ALIGN="right"><B>Comment :</B></TD>
        <TD><TEXTAREA Name="comment" Rows=3 Cols=50></TEXTAREA></TD>
        <TD><!--=&gt; for curator's info--></TD></TR><TR></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    
    <TR><TD COLSPAN=2> </TD></TR>
    <TR>
      <TD> </TD>
      <TD><INPUT TYPE="submit" NAME="action" VALUE="Submit">
        <INPUT TYPE="reset"></TD>
    </TR>
  </TABLE>

</FORM>
If you have any problems, questions, or comments, please contact <A HREF=\"mailto:cgc\@wormbase.org\">cgc\@wormbase.org</A>
EndOfText

  } # if (firstflag) show form 
} # sub display2

sub findName {
  my $name = shift;
  if ($name !~ /\w/) { 	# if not a valid name, don't search
  } elsif ($name =~ /^\d+$/) { 		# if name is just a number, leave same
  } else { 			# if it doesn't do simple aka hash thing
    my %aka_hash = &getPgHash();
    &processakasearch($name, %aka_hash);
  }
} # sub findName

sub processakasearch {			# get generated aka's and try to find exact match
  my ($name, %aka_hash) = @_;
  my $search_name = lc($name);
  unless ($aka_hash{$search_name}) { 
    my @names = split/\s+/, $search_name; $search_name = '';
    foreach my $name (@names) {
      if ($name =~ m/^[a-za-z]$/) { $search_name .= "$name "; }
      else { $search_name .= '*' . $name . '* '; }
    }
  } else { 
    my %standard_name;
    my $result = $dbh->prepare ( "select * from two_standardname;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow ) {
      $standard_name{$row[0]} = $row[2];
    } # while (my @row = $result->fetchrow )

    $keith_body .= "name $name could be : \n";
    my @stuff = sort {$a <=> $b} keys %{ $aka_hash{$search_name} };
    foreach $_ (@stuff) { 		# add url link
      my $joinkey = 'two'.$_;
      my $person = 'wbperson'.$_;
      $keith_body .= "\t$standard_name{$joinkey} $person\n";
    }
  }
  unless ($keith_body) { 
    $keith_body .= $name . " has no match, look here for possible matches : \n";
    $name =~ s/\s+/+/g;
    $keith_body .= 'http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person_name.cgi?action=Submit&name=' . "$name\n"; }
} # sub processAkaSearch

sub getPgHash {				# get akaHash from postgres instead of flatfile
  my $result;
  my %filter;
  my %aka_hash;
  
  my @tables = qw (first middle last);
  foreach my $table (@tables) { 
    $result = $dbh->prepare ( "SELECT * FROM two_aka_${table}name WHERE two_aka_${table}name IS NOT NULL AND two_aka_${table}name != 'NULL' AND two_aka_${table}name != '';" );
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

