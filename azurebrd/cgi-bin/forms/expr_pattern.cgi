#!/usr/bin/perl 

# Form to submit Expr_pattern information.

# Modeled after allele form.  Currently the .ace tags are not correct, and when
# it writes to a flatfile it mimics the email format, so will possibly be split
# into a flatfile and a .ace file.  2002 12 04
#
# Output changed to be in .ace only format for flat file.  Emails .ace with IP,
# but only flatfiles the .ace file.  2002 12 04
#
# brought back for Daniela to test.  2014 10 08
#
# blocking another IP range for spammers, blocking submissions with https?:// in 
# any data.  2016 02 12


my $acefile = "/home/azurebrd/public_html/cgi-bin/data/expr.ace";


my $firstflag = 1;		# flag if first time around (show form for no data)

# use LWP::Simple;
# use Mail::Mailer;

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;

my $query = new CGI;
my $user = 'expr_form';	# who sends mail
my $email = 'draciti@caltech.edu';		# to whom send mail
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = 'expr pattern data';		# subject of mail
my $body = '';					# body of mail
my $ace_body = "Expr_pattern\t:\t\"ExprXXXX\"\n";	# body of ace file

print "Content-type: text/html\n\n";
my $title = 'Expression Pattern Data Submission Form';
my ($header, $footer) = &cshlNew($title);
print "$header\n";		# make beginning of HTML page

&process();			# see if anything clicked
&display();			# show form as appropriate
print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'Go !') { 
    $firstflag = "";				# reset flag to not display first page (form)

    my $mandatory_ok = 'ok';			# default mandatory is ok
    my $sender = '';
    my @mandatory = qw ( submitter_email person_evidence );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{person_evidence} = "Personal Details";
 
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

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $host = $query->remote_host();		# get ip address
      next if ($host =~ m/194.165.42./);	# spam 2008 12 05
      next if ($host =~ m/89.149.253.27/);	# spam 2008 12 07
      next if ($host =~ m/83.233.30.38/);	# spam 2008 12 15
      next if ($host =~ m/188.143.232/);	# spam 2016 02 12
      my $body .= "$sender from ip $host sends :\n\n";
      my @all_vars = qw ( person_evidence submitter_email confirmed_gene predicted_gene detailed_sequence peptide_sequence other_peptide tissue_summary cell tissue life_stage subcellular_summary reporter_gene immunostaining in_situ northern western rtpcr mammalian other_approach reference_id reference_info pers_comm );
#       my @all_vars = qw ( person_evidence submitter_email gene nature_of_allele penetrance partial_penetrance temperature_sensitive loss_of_function gain_of_function paper_evidence lab phenotypic_description sequence genomic genotype strain species species_other alteration_type point_mutation_gene transposon_insertion sequence_insertion deletion upstream downstream comment );
  
      my %aceName;
      $aceName{person_evidence} = 'Remark	"Name: ';
      $aceName{submitter_email} = 'Remark	"Email: ';
      $aceName{confirmed_gene} = 'Locus	"';
      $aceName{predicted_gene} = 'Sequence	"';
      $aceName{detailed_sequence} = 'Remark	"Detailed Sequence: ';
      $aceName{peptide_sequence} = 'Remark	"Peptide Sequence: ';
      $aceName{other_peptide} = 'Remark	"Other Peptide: ';
      $aceName{tissue_summary} = 'Pattern	"';
      $aceName{cell} = 'Cell	"';
      $aceName{tissue} = 'Cell_group	"';
      $aceName{life_stage} = 'Life_stage	"';
      $aceName{subcellular_summary} = 'Subcellular_localization	"';
      $aceName{reporter_gene} = 'Reporter_gene	"';
      $aceName{immunostaining} = 'Antibody	"';
      $aceName{in_situ} = 'In_situ	"';
      $aceName{northern} = 'Northern	"';
      $aceName{western} = 'Western	"';
      $aceName{rtpcr} = 'RT_PCR	"';
      $aceName{mammalian} = 'Cell_culture	"';
      $aceName{other_approach} = 'Remark	"Other experiment approach: ';
      $aceName{reference_id} = 'Reference	"';
      $aceName{reference_info} = 'Remark	"Reference Info: ';
      $aceName{pers_comm} = 'Remark	"Pers. Comm.: ';

      my $has_url_spam = 0;
      foreach $_ (@all_vars) { 			# for all fields, check for data and output
        my ($var, $val) = &getHtmlVar($query, $_);
        if ($val =~ m/https?:\/\//) { $has_url_spam++; }
        if ($val =~ m/\S/) { 	# if value entered
          if ($aceName{$var} ne 'NULL') { $ace_body .= "$aceName{$var}$val\"\n"; }
        } # if ($val =~ m/\S/) 
      } # foreach $_ (@vars) 
      if ($has_url_spam) { print qq(If you are having a problem with your submission, email draciti AT caltech DOT edu<br/>); }
      next if ($has_url_spam);			# skip submissions with URLs which are considered spam
      my $full_body = $body . "\n" . $ace_body;
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      print OUT "$ace_body\n";			# print to outfile
      close (OUT) or die "cannot close $acefile : $!";
      $email .= ", $sender";
      &mailer($user, $email, $subject, $full_body);	# email the data
      $body =~ s/\n/<BR>\n/mg;
      $ace_body =~ s/\n/<BR>\n/mg;
#       print "BODY : <BR>$body<BR><BR>\n";
      print "$body\n";
      print "$ace_body<BR><BR>\n";
      print "<P><P><P><H1>Thank you, this data was received and will appear
within 2-4 weeks in WS release.</H1>\n";
      print "If you wish to modify your submitted information, please go back and resubmit.<BR><P> See all <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/expr.ace\">new submissions</A>.<P>\n";
    } # else # unless ($sender =~ m/@.+\..+/)
  } # if ($action eq 'Go !') 
} # sub process


sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";


<A NAME="form"><H1>Expression Pattern Data Submission Form :</H1></A>
<B>Please fill out as many fields as possible.  First two fields are required.</B><P>

<HR>


<FORM METHOD="POST" ACTION="expr_pattern.cgi">
  <TABLE>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>REQUIRED</B></FONT></TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Name</FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="person_evidence" Size="50"></TD>
        <TD>e.g. Diana Chen => Name</TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Email</FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
        <TD>e.g. dchen\@nowhere.com => Email
            <BR>If you don't get a verification email, email us at webmaster\@wormbase.org</TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>What is Expressed :</B></FONT></TD></TR>

    <TR><TD ALIGN="left"><B>DNA Sequence :</B><BR>(for all types of experiments)</TD></TR>
    <TR><TD ALIGN="right"><B>Confirmed Gene :</B></TD>
        <TD><Input Type="Text" Name="confirmed_gene" Size="50"></TD>
        <TD>e.g. egl-10, abc-1 => Confirmed Gene</TD></TR>
    <TR><TD ALIGN="right"><B>Predicted Gene :</B></TD>
        <TD><Input Type="Text" Name="predicted_gene" Size="50"></TD>
        <TD>e.g. B0261.2 => Predicted Gene</TD></TR>
    <TR><TD ALIGN="right"><B>Detailed Sequence :</B></TD>
        <TD><Input Type="Text" Name="detailed_sequence" Size="50"></TD>
        <TD>e.g. from nt 14006 to nt 14225 from cosmid C52E4.6 => Detailed Sequence</TD></TR>

    <TR><TD ALIGN="left"><B>Protein Sequence :</B><BR>(for immunostaining or Western)</TD></TR>
    <TR><TD ALIGN="right"><B>Peptide Sequence<BR>(for antibody preparation) :</B></TD>
        <TD><Input Type="Text" Name="peptide_sequence" Size="50"></TD>
        <TD>e.g. NFHGDSISFSFSSA => Peptide Sequence</TD></TR>
    <TR><TD ALIGN="right"><B>Other Peptide :</B></TD>
        <TD><Input Type="Text" Name="other_peptide" Size="50"></TD>
        <TD>e.g. GST-tagged recombinant protein ABC-1 protein expressed from E.  Coli => Other Peptide</TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>Where is the gene Expressed :</B></FONT></TD></TR>

    <TR><TD ALIGN="left"><B>Tissue Distribution :</B></TD></TR>
    <TR><TD ALIGN="right"><B>Summary (Tissue) :</B></TD>
        <TD><Input Type="Text" Name="tissue_summary" Size="50"></TD>
        <TD>e.g. Expressed in HSN, male-specific nervous system and intestine at
adult stage.  Expressed in AB.p at 4-cell embryo ... => Summary (Tissue)</TD></TR>
    <TR><TD ALIGN="right"><B>Cell :</B></TD>
        <TD><Input Type="Text" Name="cell" Size="50"></TD>
        <TD>e.g. HSNL, HSNR, AB.p => Cell</TD></TR>
    <TR><TD ALIGN="right"><B>Tissue :</B></TD>
        <TD><Input Type="Text" Name="tissue" Size="50"></TD>
        <TD>e.g. male-specific nervous system, intestine => Tissue</TD></TR>
    <TR><TD ALIGN="right"><B>Life Stage :</B></TD>
        <TD><Input Type="Text" Name="life_stage" Size="50"></TD>
        <TD>e.g. adult, embryo (see http... for Life Stage Ontology) => Life Stage</TD></TR>

    <TR><TD ALIGN="left"><B>Subcellular Localization :</B></TD></TR>
    <TR><TD ALIGN="right"><B>Summary (Subcellular) :</B></TD>
        <TD><Input Type="Text" Name="subcellular_summary" Size="50"></TD>
        <TD>e.g. Expressed in cytoplasm ... => Summary (Subcellular)</TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>How were the experiments conducted :</B></FONT></TD></TR>

    <TR><TD ALIGN="right"><B>Reporter_gene :</B></TD>
        <TD><Input Type="Text" Name="reporter_gene" Size="50"></TD>
        <TD>e.g. [abc-1::gfp] and [abc-1::LacZ] translational constructs were
created by inserting nt 12345 - nt 12567 from cosmid A1B2 into pPD95.63 ... => Reporter_gene</TD></TR>
    <TR><TD ALIGN="right"><B>Immunostaining :</B></TD>
        <TD><Input Type="Text" Name="immunostaining" Size="50"></TD>
        <TD>e.g. Polyclonal Rabbit peptide antibody was created by injecting
peptide NFHGDSISFSFSSA into rabbit ... => Immunostaining</TD></TR>
    <TR><TD ALIGN="right"><B>In_situ :</B></TD>
        <TD><Input Type="Text" Name="in_situ" Size="50"></TD>
        <TD>e.g. Using abc-1 cDNA yk12b3 as sense probe ... => In_situ</TD></TR>
    <TR><TD ALIGN="right"><B>Northern :</B></TD>
        <TD><Input Type="Text" Name="northern" Size="50"></TD>
        <TD>e.g. Using 0.9kb BamH1/HindIII fragment from abc-1 cDNA yk12b3 as
probe ... => Northern</TD></TR>
    <TR><TD ALIGN="right"><B>Western :</B></TD>
        <TD><Input Type="Text" Name="western" Size="50"></TD>
        <TD>e.g. Polyclonal Rabbit peptide antibody was created by injecting
peptide NFHGDSISFSFSSA into rabbit ... => Western</TD></TR>
    <TR><TD ALIGN="right"><B>RT-PCR :</B></TD>
        <TD><Input Type="Text" Name="rtpcr" Size="50"></TD>
        <TD>e.g. Using oligo A1 \"ATCGGGACCTTGGC\" and A2 \"GGCGGTTAGCTATAGC\" => RT-PCR</TD></TR>
    <TR><TD ALIGN="right"><B>Mammalian Cell Culture :</B></TD>
        <TD><Input Type="Text" Name="mammalian" Size="50"></TD>
        <TD>e.g. Using COS7 cell transfection.  Expression construct is created
by ... Expression pattern was identified using antibody ... => Mammalian Cell Culture</TD></TR>
    <TR><TD ALIGN="right"><B>Other approach :</B></TD>
        <TD><Input Type="Text" Name="other_approach" Size="50"></TD>
        <TD>Indicate here what it is. => Other approach</TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>Data Source :</B></FONT></TD></TR>

    <TR><TD ALIGN="left"><B>Published Data :</B></TD></TR>
    <TR><TD ALIGN="right"><B>Reference ID :</B></TD>
        <TD><Input Type="Text" Name="reference_id" Size="50"></TD>
        <TD>e.g. CGC5509, PMID13452789, wcwm2002p356, wbg17p8, ... => Reference ID</TD></TR>
    <TR><TD ALIGN="right"><B>Reference Info :</B></TD>
        <TD><Input Type="Text" Name="reference_info" Size="50"></TD>
        <TD>e.g. RYN Lee et all 2002, Development 157, 1234-1245 ... => Reference Info</TD></TR>

    <TR><TD ALIGN="left"><B>Personal Data :</B></TD></TR>
    <TR><TD ALIGN="right"><B>Pers. Comm. :</B></TD>
        <TD><Input Type="Text" Name="pers_comm" Size="50"></TD>
        <TD>e.g. Personal Communication from Diana Chen, Dec 1, 2002 => Pers. Comm.</TD></TR>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    
    <TR><TD COLSPAN=2> </TD></TR>
    <TR>
      <TD> </TD>
      <TD><INPUT TYPE="submit" NAME="action" VALUE="Go !">
        <INPUT TYPE="reset"></TD>
    </TR>
  </TABLE>

</FORM>
If you have any problems, questions, or comments, please contact <A HREF=\"mailto:draciti\@its.caltech.edu\">draciti\@its.caltech.edu</A>
EndOfText

  } # if (firstflag) show form 
} # sub display
