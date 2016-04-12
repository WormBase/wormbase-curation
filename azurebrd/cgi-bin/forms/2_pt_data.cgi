#!/usr/bin/perl

# Form to submit 2 point data information.

# Added pg connections, removed ck's comments about acedb tags from html.  2003 02 14
#
# Moved Mapper: below 2_point_data :  2003 08 08
#
# Made calc_opt and calc_num mandatory fields due to Keith's request.
# (calculation type and calculation count)  Count must have 2 sets of digits.
# 2003 08 09

my $acefile = "/home/azurebrd/public_html/cgi-bin/data/two_point_data.ace";

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
my $user = 'two_point_data_form';	# who sends mail
# my $email = 'ck1@sanger.ac.uk';	# to whom send mail
# my $email = 'cgc@wormbase.org';	# to whom send mail
my $email = 'genenames@wormbase.org';	# to whom send mail 2007 09 19
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = '2_point_data';	# subject of mail
my $body = '';			# body of mail
my $ace_body = '';		# body of ace file
my $strain_body = '';		# body of strain file

print "Content-type: text/html\n\n";
my $title = '2_point_data Data Submission Form';
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
#     my @mandatory = qw ( locus_1 allele_1 locus_2 allele_2 genotype results temperature mapper submitter_email );
    my @mandatory = qw ( locus_1 allele_1 locus_2 allele_2 genotype results temperature mapper submitter_email calc_opt calc_num );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{locus_1} = "Locus 1";
    $mandatoryName{allele_1} = "Allele 1";
    $mandatoryName{locus_2} = "Locus 2";
    $mandatoryName{allele_2} = "Allele 2";
    $mandatoryName{genotype} = "Genotype";
    $mandatoryName{results} = "Results";
    $mandatoryName{temperature} = "Temperature";
    $mandatoryName{mapper} = "Submitter Name";
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{calc_opt} = "Calculation Type";
    $mandatoryName{calc_num} = "Calculation Count";
 
    foreach $_ (@mandatory) {			# check mandatory fields
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($_ eq 'submitter_email') {		# check emails
        unless ($val =~ m/@.+\..+/) { 		# if email doesn't match, warn
          print "<FONT COLOR=red SIZE=+2>$val is not a valid email address.</FONT><BR>";
          $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
        } else { $sender = $val; }
      } elsif ($_ eq 'calc_num') {
        unless ($val =~ m/\d+\D+\d+/) {
          print "<FONT COLOR=red SIZE=+2>$val is not a valid calculation type (2 or more sets of numbers).</FONT><BR>";
          $mandatory_ok = 'bad'; }		# mandatory not right, print to resubmit
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
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
      my $body .= "$sender from ip $host sends :\n\n";

#       my @all_vars = qw ( person_evidence submitter_email gene nature_of_allele penetrance partial_penetrance temperature_sensitive loss_of_function gain_of_function paper_evidence lab phenotypic_description sequence genomic assoc_strain species species_other alteration_type point_mutation_gene transposon_insertion sequence_insertion deletion upstream downstream comment );
#       my @all_vars = qw ( locus_1 allele_1 locus_2 allele_2 genotype results temperature mapper submitter_email calc_opt calc_num calc_distance calc_lower calc_upper lab comment ); # mapper and submitter_email treated separetly
      my @all_vars = qw ( locus_1 allele_1 locus_2 allele_2 genotype results temperature calc_opt calc_num calc_distance calc_lower calc_upper lab comment );

      my %aceName;
      $aceName{locus_1} = 'NULL';			# can't just append, must add with allele_1
      $aceName{allele_1} = 'NULL';			# add with above
      $aceName{locus_2} = 'NULL';	      		# can't just append, must add with allele_2
      $aceName{allele_2} = 'NULL';			# add with above                          ;
      $aceName{genotype} = 'Genotype';
      $aceName{results} = 'Results';
      $aceName{temperature} = 'Temperature';
      $aceName{mapper} = 'Mapper';
      $aceName{submitter_email} = 'NULL';
      $aceName{calc_opt} = 'NULL';			# must add with calc_num
      $aceName{calc_num} = 'NULL';			# add with above
      $aceName{calc_distance} = 'Calc_distance';
      $aceName{calc_lower} = 'Calc_lower_conf';
      $aceName{calc_upper} = 'Calc_upper_conf';
      $aceName{lab} = 'Laboratory';
      $aceName{comment} = 'NULL';

      my ($var, $mapper) = &getHtmlVar($query, 'mapper');	# using mapper as pg key
      unless ($mapper =~ m/\S/) {				# if there's no mapper text
        print "<FONT COLOR='red'>Warning, you have not picked a Mapper</FONT>.<P>\n";
      } else {							# if tpd text, output
        $result = $dbh->do( "INSERT INTO tpd_mapper (tpd_mapper) VALUES ('$mapper');" );
        $result = $dbh->prepare( "SELECT currval('tpd_seq');" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row = $result->fetchrow;
        $joinkey = $row[0];
        print "2_pt_data entry number $joinkey<BR><BR>\n";
        $result = $dbh->do( "INSERT INTO tpd_submitter_email VALUES ('$joinkey', '$sender');" );
        $result = $dbh->do( "INSERT INTO tpd_ip VALUES ('$joinkey', '$host');" );
        $ace_body .= "2_point_data : \n";
        $body .= "mapper\t$mapper\n";
        $ace_body .= "Mapper\t\"$mapper\"\n";
  
        foreach $_ (@all_vars) { 			# for all fields, check for data and output
          my ($var, $val) = &getHtmlVar($query, $_);
          if ($val =~ m/\S/) { 	# if value entered
  
            if ($aceName{$var} ne 'NULL') { $ace_body .= "$aceName{$var}\t\"$val\"\n"; }
	    elsif ($var eq 'locus_1') {
              my ($var, $locus_1) = &getHtmlVar($query, 'locus_1');
              my ($var2, $allele_1) = &getHtmlVar($query, 'allele_1');
	      $locus_1 =~ s///g;
	      $allele_1 =~ s///g;
	      $ace_body .= "Point_1\tLocus_1\t\"$locus_1\"\t\"$allele_1\"\n";
            }
            elsif ($var eq 'allele_1') { 1; }		# do nothing, but append to body
	    elsif ($var eq 'locus_2') {
              my ($var, $locus_2) = &getHtmlVar($query, 'locus_2');
              my ($var2, $allele_2) = &getHtmlVar($query, 'allele_2');
	      $locus_2 =~ s///g;
	      $allele_2 =~ s///g;
	      $ace_body .= "Point_2\tLocus_2\t\"$locus_2\"\t\"$allele_2\"\n";
            }
            elsif ($var eq 'allele_2') { 1; }		# do nothing, but append to body
            elsif ($var eq 'submitter_email') { 1; }	# do nothing, but append to body
	    elsif ($var eq 'calc_opt') {
              my ($var, $calc_opt) = &getHtmlVar($query, 'calc_opt');
              if ($calc_opt) { 
	        $calc_opt =~ s///g;
                my ($var2, $calc_num) = &getHtmlVar($query, 'calc_num');
	        if ($calc_num) {
	          $calc_num =~ s///g;
                  $ace_body .= "Calculation\t$calc_opt\t$calc_num\n";
                } # if ($calc_num)
              } # if ($calc_opt)
            }
            elsif ($var eq 'comment') { 1; }		# do nothing, but append to body
	    else { 1; }
  
            $body .= "$var\t\"$val\"\n";
            my $pg_table = 'tpd_' . $var;
            $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
          } # if ($val) 
        } # foreach $_ (@vars) 
        $ace_body .= "\n$strain_body";
        my $full_body = $body . "\n" . $ace_body;
        print OUT "$ace_body\n";			# print to outfile
        close (OUT) or die "cannot close $acefile : $!";
        $email .= ", $sender";
        &mailer($user, $email, $subject, $full_body);	# email the data
        $body =~ s/\n/<BR>\n/mg;
        $ace_body =~ s/\n/<BR>\n/mg;
        print "BODY : <BR>$body<BR><BR>\n";
        print "ACE : <BR>$ace_body<BR><BR>\n";
        print "<P><P><P><H1>Thank you for your submission.  You will be contacted by WormBase within three working days.</H1>\n";
        print "If you wish to modify your submitted information, please go back and resubmit.<BR><P> See all <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/two_point_data.ace\">new submissions</A>.<P>\n";
      } # else # unless ($genotype =~ m/\S/)
    } # else # unless ($sender =~ m/@.+\..+/)
  } # if ($action eq 'Submit') 
} # sub process



sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";
<html>
  <head>
    <title>2_point_data_submission_form</title>
  </head>

  <body>

<A NAME="form"><H1>2_point_data Data Submission Form :</H1></A>
<B>Please fill out as many fields as possible.  First eleven fields are
required.</B><P>

<HR>

    

<FORM METHOD="POST" ACTION="2_pt_data.cgi">
 
    <TABLE ALIGN="center"> 
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>REQUIRED</B></FONT></TD></TR>
 
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Mapped Locus 1</FONT></I> :</B></TD>
        <TD><Input Type="Text" Name="locus_1" Size="20"></TD>
        <TD>(eg. unc-42)</TD>
        <TD ALIGN="right"><I><FONT COLOR='red'><B>Allele 1</FONT></I> :</B></TD>
        <TD><Input Type="Text" Name="allele_1" Size="20"> </TD>
        <TD>(eg. e270)</TD></TR>
<!--        <TD>(eg. e270) => ace: Locus_1  "unc-42" "e270"<p></TD></TR>-->
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Mapped Locus 2</FONT></I> :</B></TD>
        <TD><Input Type="Text" Name="locus_2" Size="20"></TD>
        <TD>(eg. let-560)</TD>
        <TD ALIGN="right"><I><FONT COLOR='red'><B>Allele 2</FONT></I> :</B></TD>
        <TD><Input Type="Text" Name="allele_2" Size="20"> </TD>
        <TD>(eg. e2658)</TD></TR>
<!--        <TD>(eg. e2658) => ace: Locus_2  "let-560" "e2658"</TD></TR>-->
    <TR></TR>
    <TR></TR>
    <TR></TR>
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Genotype</FONT></I> :</B></TD>
        <TD COLSPAN=2><Input Type="Text" Name="genotype" Size="50"></TD>
        <TD COLSPAN=3>(eg. unc-42(e270) let-560(e1658) / + + V)</TD><TD></TR>
<!--        <TD COLSPAN=3>(eg. unc-42(e270) let-560(e1658) / + + V) => Genotype tag</TD><TD></TR>-->
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Results</FONT></I> :</B></TD>
        <TD COLSPAN=2><TEXTAREA Name="results" Rows=4 Cols=38></TEXTAREA></TD>
        <TD COLSPAN=3>(eg. 7 Unc, 242 WT)</TD></TR>
<!--        <TD COLSPAN=3>(eg. 7 Unc, 242 WT) => Results tag (value is free text)</TD></TR>-->
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Temperature</FONT></I> :</B></TD>
        <TD COLSPAN=2><Input Type="Text" Name="temperature" Size="50"></TD>
        <TD COLSPAN=3>(Celcius)</TD></TR>
<!--        <TD COLSPAN=3>(Celcius) => Temperature tag</TD></TR>-->
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Submitter's Name</FONT></I> :</B>
           <BR>Please enter full name, eg. John Sulston</TD>
        <TD COLSPAN=2><Input Type="Text" Name="mapper" Size="50"></TD>
        <TD COLSPAN=3></TD></TR>
<!--        <TD COLSPAN=3>=> Mapper tag</TD></TR>-->
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Submitter's Email</FONT></I> :</B>
           <BR>(please enter for contact purpose)</TD>
        <TD COLSPAN=2><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
        <TD COLSPAN=3>If you don't get a verification email, email us at webmaster\@www.wormbase.org</TD></TR>
<!--        <TD COLSPAN=3>=> for curator's info</TD></TR>-->

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD></TR>
<!--    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD><TD colspan=4><FONT SIZE=-2>These fields can be calculated by us from your<BR>primary data, but if you fill them in as you believe<BR>they should be that may help resolve any<BR>ambiguities or misunderstandings.</FONT></TD></TR>-->

   
    <TR></TR><TR><TD ALIGN="right"><I><FONT COLOR='red'><B>Calculation type:</B></I></FONT></TD>
        <TD COLSPAN=2><Select Name="calc_opt"  Size=1>
                   <Option Value="One_recombinant" Selected>One_recombinant
                   <Option Value="Tested">Tested
                   <Option Value="Full">Full
                   <Option Value="Selected">Selected      
                   <Option Value="One_all">One_all
                   <Option Value="Direct">Direct
                   <Option Value="Dom_one">Dom_one
                   <Option Value="Complex_mixed">Complex mixed
                   <Option Value="Backcross">Backcross
                   <Option Value="Dom_semi">Dom_semi
                   <Option Value="Recs_all">Recs_all
                   <Option Value="One_let">One_let
                   <Option Value="Sex_one">Sex_one
                   <Option Value="Dom_let">Dom_let
                   <Option Value="Back_one">Back one      
                   <Option Value="Dom_selected">Dom_selected
                   <Option Value="Sex_full">Sex_full
                   <Option Value="Selected_trans">Slected Trans
                   <Option Value="Sex_cis">Sex_cis
            </Select></TD>
        <TD COLSPAN=1><I><FONT COLOR='red'><B>Count: </B></I></FONT></TD>
	<TD COLSPAN=2><Input Type="Text" Name="calc_num" Size="50"></TD></TR>
        <TR><TD></TD><TD COLSPAN=2>Choose one of the 19 types - <A href="2_pt_help.html">HELP</A></TD><TD COLSPAN=3>(eg. 727  900 if choose one_recombinant;<p>928  9  8  326 if choose Full)

<!--   => Drop-down option goes to Calculation tag<p> => Ace format: eg.  One_recombinant  727 99-->

        </TD></TR> 
        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
        <TR><TD ALIGN="right"><B>Estimated Distance :</B></TD>
            <TD COLSPAN=2><Input Type="Text" Name="calc_distance" Size="50"></TD>
            <TD COLSPAN=3>(eg. 19.969999)  This can be calculated by us from your primary data, but if you fill it in as you believe it should be, that may help resolve any ambiguities or misunderstandings.</TD></TR>
<!--            <TD COLSPAN=3>(eg. 19.969999) => Calc_distance (?) tag</TD></TR>-->
<!--        <TR></TR> <TR></TR> <TR></TR> <TR></TR>
        <TR><TD ALIGN="right"><B>Confidence :</B></TD></TR>
        <TR><TD ALIGN="right">Lower Confidence :</TD>
            <TD COLSPAN=2><Input Type="Text" Name="calc_lower" Size="50"></TD>
            <TD COLSPAN=3>(eg. 15.760000)</TD></TR>          -->
<!--            <TD COLSPAN=3>(eg. 15.760000) => Calc_lower_conf tag</TD></TR>-->
<!--        <TR><TD ALIGN="right">Upper Confidence :</TD>
            <TD COLSPAN=2><Input Type="Text" Name="calc_upper" Size="50"></TD>
            <TD COLSPAN=3>(eg. 24.650000)</TD></TR>        -->
<!--            <TD COLSPAN=3>(eg. 24.650000) => Calc_upper_conf tag</TD></TR>-->
  
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
  

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
  
    <TR><TD><FONT SIZE=+2><B>PERSONAL</B></FONT></TD></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR><TD ALIGN="right"><B>Laboratory designation</B><BR>
           (if known, eg., CB, SP.  <BR>See list 
            <A HREF="http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/labcore.ace">here</A>.)</TD>
        <TD COLSPAN=2><Input Type="Text" Name="lab" Size="50" Maxlength="3"></TD>
        <TD COLSPAN=3></TD></TR>
<!--        <TD COLSPAN=3>=> Laboratory tag</TD></TR>-->
  
    <TR></TR><TR><TD ALIGN="right"><B>Comment :</B></TD>
        <TD COLSPAN=2><TEXTAREA Name="comment" Rows=5 Cols=38></TEXTAREA></TD>
        <TD COLSPAN=3></TD></TR><TR></TR>
<!--        <TD COLSPAN=3>=> for curator's info</TD></TR><TR></TR>-->

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
If you have any problems, questions, or comments, please contact <A HREF=\"mailto:gnw\@wormbase.org\">gnw\@wormbase.org</A>

<!-- Created: Tue Nov 19 12:51:54 GMT 2002 -->
<!-- hhmts start -->
<!--Last modified: Tue Nov 19 22:28:10 GMT Standard Time 2002-->
<!-- hhmts end -->
  </body>
</html>

EndOfText

  } # if (firstflag) show form 
} # sub display
