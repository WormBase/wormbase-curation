#!/usr/bin/perl 

# Form to submit gene name information.  

# Does not create output other than email and database entries.  Emails only one
# person.  gene_name AND/OR geneclass_name are mandatory (doesn't need both but
# could have both or either).  2003 12 16
#
# Added tables : ggn_locus_allele ggn_locus_chrom ggn_locus_product ggn_locus_comp
# for Chao-Kung.  2003 12 29
#
# Changed email output to use %emailName instead of %mandatoryName because 
# Chao-Kung said Jonathan wanted different names in the fields.  These are 
# different for provider and submitter_email depending on whether locus or
# geneclass data.  2004 01 06
#
# Append gene name to mailing subject for Mary Ann.  2005 01 12
#
# Changed ``3-letter'' to ``3-letter or 4-letter'' for Anthony.  2005 08 30
#
# Added more 4-letter stuff for Anthony.  Removed the subcontract section about
# Jonathan Hodgkin in the Details section.  2007 06 07
#
# Added the simple spam checking thing.  2007 09 24
#
# Took out a lot of explanation text and put a link to the wiki instead.  For
# Mary Ann 2007 09 27
#
# Changed nomenclature link to wormbase wiki for Raymond.  2012 08 08
#
# Wrote a new script to regenerate Lab data on cronjob.
# 0 4 * * * /home/azurebrd/public_html/sanger/labs.pl  2006 12 05



my $firstflag = 1;		# flag if first time around (show form for no data)

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $query = new CGI;
my $user = 'genename_form';	# who sends mail
# my $email = 'ck1@sanger.ac.uk';	# to whom send mail
# my $email = 'cgc@wormbase.org';	# to whom send mail
my $email = 'genenames@wormbase.org';	# to whom send mail 2007 09 19
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = 'Gene Name Form Data';	# subject of mail
my $body = '';			# body of mail

my $strain_body = '';		# body of strain file

# my @all_vars = qw ( gene_name conf_gene geneclass_name conf_class provider submitter_email corresponding conf_seq locus_desc locus_phen justification geneclass_desc geneclass_phen lab comment );
my @all_vars = qw ( gene_name conf_gene geneclass_name conf_class provider submitter_email corresponding conf_seq locus_desc locus_phen locus_allele locus_chrom locus_product locus_comp justification geneclass_desc geneclass_phen lab comment );

print "Content-type: text/html\n\n";
my $title = 'Allele Data Submission Form';
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
    my @mandatory = qw ( submitter_email gene_name provider );
						# geneclass_name check only if no gene_name
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter's Email";
    $mandatoryName{gene_name} = "3-letter or 4-letter Gene name (locus name)";
    $mandatoryName{geneclass_name} = "3-letter or 4-letter Gene class name";
    $mandatoryName{provider} = "Data provider";
    $mandatoryName{justification} = "New Gene Class Name Proposals";
    $mandatoryName{locus_allele} = "Locus Allele";
    $mandatoryName{locus_chrom} = "Locus Chromosome";
    $mandatoryName{locus_product} = "Locus Product";
    $mandatoryName{locus_comp} = "Locus Complementation Data";
    $mandatoryName{conf_gene} = "Confidential Gene name";
    $mandatoryName{conf_class} = "Confidential Gene Class name";
    $mandatoryName{corresponding} = "Corresponding Sequence";
    $mandatoryName{conf_seq} = "Confidential Corresponding Sequence";
    $mandatoryName{locus_desc} = "Locus Description";
    $mandatoryName{locus_phen} = "Locus Phenotype";
    $mandatoryName{geneclass_desc} = "Gene Class Description";
    $mandatoryName{geneclass_phen} = "Gene Class Phenotype";
    $mandatoryName{lab} = "Laboratory";
    $mandatoryName{comment} = "Comment";
    my %emailName;				# hash of field names for email
    $emailName{submitter_email} = "Submitter's Email :";
    $emailName{gene_name} = "Locus_Locus_name :";
    $emailName{geneclass_name} = "GeneClass_Gene_name :";
    $emailName{provider} = "Data provider :";
    $emailName{justification} = "New Gene Class Name Proposals";
    $emailName{locus_allele} = "Locus_Allele :";
    $emailName{locus_chrom} = "Locus_Chromosome :";
    $emailName{locus_product} = "Locus_Gene_Product :";
    $emailName{locus_comp} = "Locus_Complementation_Data :";
    $emailName{conf_gene} = "Confidential Gene name";
    $emailName{conf_class} = "Confidential Gene Class name";
    $emailName{corresponding} = "Locus_Sequence :";
    $emailName{conf_seq} = "Confidential Corresponding Sequence";
    $emailName{locus_desc} = "Locus_Description :";
    $emailName{locus_phen} = "Locus_Phenotype :";
    $emailName{geneclass_desc} = "GeneClass_Description :";
    $emailName{geneclass_phen} = "GeneClass_Phenotype :";
    $emailName{lab} = "GeneClass_Laboratory :";
    $emailName{comment} = "Comment";

 
    foreach $_ (@mandatory) {			# check mandatory fields
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($_ eq 'submitter_email') {		# check emails
        unless ($val =~ m/@.+\..+/) { 		# if email doesn't match, warn
          print "<FONT COLOR=red SIZE=+2>$val is not a valid email address.</FONT><BR>";
          $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
        } else { $sender = $val; }
      } else { 					# check other mandatory fields
	unless ($val) { 			# if there's no value
          if ($_ ne 'gene_name') {		# usually warn and set flag
            print "<FONT COLOR=red SIZE=+2>$mandatoryName{$_} is a mandatory field.</FONT><BR>";
            $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
          } else {				# for gene_name, check geneclass_name
            my ($var, $val) = &getHtmlVar($query, 'geneclass_name');
            if ($val) {				# if there's a geneclass_name, check justification
              my ($var, $val) = &getHtmlVar($query, 'justification');
              unless ($val) { 			# if no justification with geneclass_name, warn and set flag
                print "<FONT COLOR=red SIZE=+2>The \"$mandatoryName{justification}\" field is mandatory when sending a $mandatoryName{geneclass_name}.</FONT><BR>";
                $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
              }
            } else {				# if no geneclass_name value here either warn and set flag
              print "<FONT COLOR=red SIZE=+2>$mandatoryName{gene_name} OR $mandatoryName{geneclass_name} is a mandatory field.</FONT><BR>";
              $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
            } # unless ($val) 
          } # else # if ($_ ne 'gene_name')
        } # unless ($val)
      } # else # if ($_ eq 'submitter_email')
    } # foreach $_ (@mandatory)

    my $spam = 0;                               # if it's spam skip doing anything  2007 09 24
    foreach $_ (@all_vars) {                    # for all fields, check for spam
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val =~ m/\S/) {      # if value entered 
        if ($val =~ m/a href/i) {
          my (@spam) = $val =~ m/(a href)/gi;
          foreach my $sp (@spam) { $spam++; } } } }
#     print "SPAM $spam SPAM<BR>\n";  
    if ($spam > 0) { print "Ignoring.  This is spam<BR>\n"; return; }

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      my $host = $query->remote_host();		# get ip address
#       $body .= "$sender from ip $host sends :\n\n";	# CK doesn't care about the ip
      $body .= "$sender sends :\n\n";
  
      $result = $dbh->do( "INSERT INTO ggn_ip (ggn_ip) VALUES ('$host');" );
						# this updated the pg sequence ggn_seq to nextval
      $result = $dbh->prepare( "SELECT currval('ggn_seq');" );	
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
						# can get currval because last line updated
      my @row = $result->fetchrow;
      $joinkey = $row[0];
      print "Gene name / Gene Class name entry number $joinkey<BR><BR>\n";
#         $result = $dbh->do( "INSERT INTO ggn_submitter_email VALUES ('$joinkey', '$sender');" );
#         $result = $dbh->do( "INSERT INTO ggn_ip VALUES ('$joinkey', '$host');" );
  
      foreach $_ (@all_vars) { 			# for all fields, check for data and output
        my ($var, $val) = &getHtmlVar($query, $_);
        if ($var eq 'gene_name') { $subject .= " - $val"; }	# append gene name to subject for Mary Ann 2005 01 12
        if ($val =~ m/\S/) { 	# if value entered
          if ($var eq 'submitter_email') {	# submitter email field different for locus and geneclass
            if ($body =~ m/Locus_Locus_name :/) { 
              $body .= "Locus_Data_provider :\t\"$val\"\n"; }
            if ($body =~ m/GeneClass_Gene_name :/) { 
              $body .= "GeneClass_Data_provider :\t\"$val\"\n"; }
          } elsif ($var eq 'provider') {	# submitter email field different for locus and geneclass
            if ($body =~ m/Locus_Locus_name :/) { 
              $body .= "Locus_EMAIL :\t\"$val\"\n"; }
            if ($body =~ m/GeneClass_Gene_name :/) { 
              $body .= "GeneClass_EMAIL :\t\"$val\"\n"; }
          } else {				# normally just use %emailName value for that field
            $body .= "$emailName{$var}\t\"$val\"\n"; 
	  }
          my $pg_table = 'ggn_' . $var;
          $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
        } # if ($val) 
      } # foreach $_ (@vars) 
      $email .= ", $sender";
      &mailer($user, $email, $subject, $body);	# email the data
      $body =~ s/\n/<BR>\n/mg;
      print "BODY : <BR>$body<BR><BR>\n";
      print "<P><P><P><H1>Thank you for your submission.  You will be contacted by WormBase within three working days.</H1>\n";
      print "If you wish to modify your submitted information, please go back and resubmit.<BR><P>\n";
    } # else # unless ($sender =~ m/@.+\..+/)
  } # if ($action eq 'Submit') 
} # sub process


sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";


<a name="top">
<h1>Gene Name / Gene Class Name Proposal Submission Form</h1></a><p>

Please use this entry only for proposing <B>new gene name</B> or <B>new gene class</B> categories and please remember 
that <b>we need to know your email address</b>, so that we can contact you about your submission.<p>

<I>You may submit new gene name <b>or</b> new gene class name <b>or</b> both.</I><p>
<!--<a href="#details">More information</a> about gene naming conventions is given below.-->
Please read the <!--<a href=http://www.wormbase.org/wiki/index.php/Nomenclature target=new>--><a href=http://www.wormbase.org/about/userguide/nomenclature target=new>nomenclature guidelines</a> for more information on gene naming conventions.
</p>   
<hr>
<FORM>
 
   <FONT SIZE=+2><B>REQUIRED</B></FONT>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TABLE ALIGN="center"> 
   
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>3-letter or 4-letter Gene name (locus name)<FONT COLOR='black'> if submitting gene name</FONT></FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="gene_name" Size="50"></TD>
        <TD>(eg. age-1, eat-20)</TD><TD><input type="checkbox" name="conf_gene" value="YES"><B>Keep confidential?</B></TD></TR>

    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>3-letter or 4-letter Gene class name <FONT COLOR='black'>if submitting gene class name</FONT></FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="geneclass_name" Size="50"></TD>
        <TD>(eg. age, eat)</TD><TD><input type="checkbox" name="conf_class" value="YES"><B>Keep confidential?</B></TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Data provider</FONT></U> :</B></TD>
	<TD><Input Type="Text" Name="provider" Size="50"></TD> 
        <TD>(eg. Hodgkin JA)</TD></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Email</FONT></U> :</B>
           <BR>(Mandatory. Please enter for contact purpose)
           <BR>If you don't get a verification email,<BR>email us at webmaster\@wormbase.org</TD>
        <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
    </TABLE>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>


    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD></TR>
    <TABLE ALIGN="center"> 
   
	<TR><TD ALIGN="right"><B>Corresponding Sequence:</B></TD>
        <TD><Input Type="Text" Name="corresponding" Size="50"></TD>
        <TD>(if available, eg. Y110A7A.10 or M79.1a/b/c, for isoforms)</TD><TD><input type="checkbox" name="conf_seq" value="YES"><B>Keep confidential?</B></TD></TR>	

	<TR><TD ALIGN="right"><B>Locus Description:</B></TD>
	<TD><TEXTAREA Name="locus_desc" Rows=3 Cols=41></TEXTAREA></TD>     
        <TD>(if available)</TD><TD></TR>	

	<TR><TD ALIGN="right"><B>Locus Phenotype:</B></TD>
	<TD><TEXTAREA Name="locus_phen" Rows=3 Cols=41></TEXTAREA></TD>     
        <TD>(if available)</TD><TD></TR>
        
        <TR><TD ALIGN="right"><B>Locus Allele:</B></TD>
        <TD><TEXTAREA Name="locus_allele" Rows=1 Cols=41></TEXTAREA></TD>     
        <TD>(if available)</TD><TD></TR>
  
        <TR><TD ALIGN="right"><B>Locus Chromosome:</B></TD>
        <TD><TEXTAREA Name="locus_chrom" Rows=1 Cols=41></TEXTAREA></TD>     
        <TD>(if available, eg, III)</TD><TD></TR>
  
        <TR><TD ALIGN="right"><B>Locus Gene Product:</B></TD>
        <TD><TEXTAREA Name="locus_product" Rows=1 Cols=41></TEXTAREA></TD>     
        <TD>(if available)</TD><TD></TR>
  
        <TR><TD ALIGN="right"><B>Locus Complementation data:</B></TD>
        <TD><TEXTAREA Name="locus_comp" Rows=3 Cols=41></TEXTAREA></TD>     
        <TD>(if available)</TD><TD></TR>
           
	<TR><TD ALIGN="right"><B>New Gene Class Name Proposals (Explanation and/or justification of 3-letter or 4-letter abbreviation):</B></TD>
        <TD><TEXTAREA Name="justification" Rows=3 Cols=41></TEXTAREA></TD>  
        <TD><FONT color="red">(Mandatory if entering Gene Class Name)</FONT></TD><TD></TR>		
		

	<TR><TD ALIGN="right"><B>Gene Class Description:</B></TD>
        <TD><TEXTAREA Name="geneclass_desc" Rows=3 Cols=41></TEXTAREA></TD>  
        <TD>(if available, e.g., phosphoinositide kinase AdAPter subunit)</TD><TD></TR>	
	 
        <TR><TD ALIGN="right"><B>Gene Class Phenotype:</B></TD>
        <TD><TEXTAREA Name="geneclass_phen" Rows=3 Cols=41></TEXTAREA></TD>  
        <TD>(if available)</TD><TD></TR>

        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
	<TR></TR> <TR></TR> <TR></TR> <TR></TR>
	<TR></TR> <TR></TR> <TR></TR> <TR></TR>
    </TABLE>

  
    
    <TR><TD><FONT SIZE=+2><B>PERSONAL</B></FONT></TD></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>

    <TABLE ALIGN="center">   
    <TR><TD ALIGN="right"><B>Laboratory designation</B><BR>
           (if known, eg., CB, PS.  <BR>See list 
            <!--<A HREF="http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/labcore.ace">here</A>.)</TD>-->
            <A HREF="http://tazendra.caltech.edu/~azurebrd/sanger/labs/labs.ace">here</A>.)</TD>
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

<!--
<hr>
<a href="#top">Top</a><p>
<h3><a name="details">More details</a></h3><p>


Gene naming in <i>C. elegans</i> is supervised by Jonathan Hodgkin at
University of Oxford, England<!--, as part of a subcontract for the <a href="http://www.cbs.umn.edu/CGC/CGChomepage.htm">Caenorhabditis Genetics Center</a> (CGC), which is based at the University
of Minnesota and funded by the NIH National Center for Research
Resources--><!--.
</p>

<p>
Proposed three-letter or four-letter new gene names should preferably be registered with the CGC
before publication.  This helps to ensure conformity with standard
nomenclature, to avoid duplicated, unnecessary or inappropriate gene
names, and to update the relevant databases.<br>
Submitted information will be treated <b>CONFIDENTIALLY</b>.
</p>

<p>
If further help is needed, please contact the curator :
<br><strong>Dr Jonathan Hodgkin</strong>
<br>CGC Map and Nomenclature Curator
<br>(Caenorhabditis Genetics Center Subcontract)
<br>Genetics Unit, Dept of Biochemistry.
<br>University of Oxford.
<br>South Parks Road.
<br>OXFORD OX1 3QU  England 
<br>Telephone (+44) 01865 275317
<br>Fax   (+44) 01865 275318 
<br>e-mail  <a href="mailto:jah\@bioch.ox.ac.uk, cgc\@wormbase.org">CGC & WormBase</a>
</p>

<p>
In the standard nomenclature for <i>Caenorhabditis elegans</i>, genes
are given names consisting of three or four italicized letters, a hyphen, and
an italicized Arabic number, e.g., dpy-5 or let-37 or mlc-3. The gene
name may be followed by an italicized Roman numeral, to indicate the
linkage group on which the gene maps, e.g., dpy-5 I or let-37 X or
mlc-3 III.
</p>

<p>
For genes defined by mutation, the gene names refer to the mutant
phenotype originally detected or most easily scored: dumpy (dumpy) in
the case of dpy-5, and lethal (lethal) in the case of let-37.
</p>

<p>
For genes defined by cloning on the basis of sequence similarity, or
by analysis of genomic sequence, the gene name refers to the predicted
protein product or RNA product: myosin light chain in the case of
mlc-3, superoxide dismutase in the case of sod-1, ribosomal RNA in the
case of rrn-1.
</p>

<p>
Genes with related properties are usually given the same three or four letter
name and different numbers. For example, there are three known myosin
light chain genes: mlc-1, mlc-2, mlc-3, and more than twenty different
dumpy genes: dpy-1, dpy-2, dpy-3, and so on.
</p>

<p>
Sequences that are predicted to be genes from sequence data alone,
using GENEFINDER, are initially named by the C. elegans Mapping and
Sequencing Consortium on the basis of the sequenced cosmid, plus a
number. For example, the genes predicted for the cosmid T05G3 are
called T05G3.1, T05G3.2, etc. (numbered in arbitrary order of
definition). Such names can be superseded by standard 3-letter or 
4-letter names when this becomes appropriate. Thus, R13F6.3 has been 
given the name srg-12 (for Serpentine Receptor, class G). 
</p>

<p>
Gene names including c (for Caenorhabditis), ce (for C. elegans), n
(for nematode) or w (for worm) are discouraged.  The optional prefix
Ce- can be added to the gene name, if it is important to specify the
organism of origin.  For example, Ce-snt-1 defines the C. elegans
synaptotagmin gene.
</p>

<p>
A summary of current recommendations for genetic nomenclature in <i>Caenorhabditis elegans</i> 
can be found </a><a href="http://biosci.umn.edu/CGC/Nomenclature/nomenguid.htm">here</a>.
</p>    -->
<!-- Created: Tue Nov 19 12:51:54 GMT 2002 -->
<!-- hhmts start -->
<!-- Last modified: Tue Dec  9 10:19:33 GMT 2003 -->
<!-- hhmts end -->
<!--
<P>
If you have any problems, questions, or comments, please contact <A HREF=\"mailto:cgc\@wormbase.org\">cgc\@wormbase.org</A>-->
EndOfText

  } # if (firstflag) show form 
} # sub display


