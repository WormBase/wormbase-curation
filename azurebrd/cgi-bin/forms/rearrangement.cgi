#!/usr/bin/perl 

# Form to submit New Rearrangement information.

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
# Changed for dfdp data.  2004 02 12
#
# Changed for rearrangement data.  2004 02 18
#
# Changed for xCn and xTn data.  For Yang Zhao and Paul.  2006 07 17


my $acefile = "/home/azurebrd/public_html/cgi-bin/data/rearrangement.ace";

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
my $user = 'rearrangement_form';	# who sends mail
# my $email = 'ck1@sanger.ac.uk';	# to whom send mail
# my $email = 'cgc@wormbase.org';	# to whom send mail
my $email = 'genenames@wormbase.org';	# to whom send mail 2007 09 19
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = 'New Rearrangement submission';	# subject of mail
my $body = '';			# body of mail
my $ace_body = '';		# body of ace file
my $keith_body = '';		# body to mail but not show in form output

print "Content-type: text/html\n\n";
my $title = 'New Rearrangement submission form';
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
    my @mandatory = qw ( submitter_email rearrangement person_evidence );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{rearrangement} = "Rearrangement";
    $mandatoryName{person_evidence} = "Data Provider";
 
    foreach $_ (@mandatory) {			# check mandatory fields
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($_ eq 'submitter_email') {		# check emails
        unless ($val =~ m/@.+\..+/) { 		# if email doesn't match, warn
          print "<FONT COLOR=red SIZE=+2>$val is not a valid email address.</FONT><BR>";
          $mandatory_ok = 'bad';		# mandatory not right, print to resubmit
        } else { $sender = $val; }
      } elsif ($_ eq 'rearrangement') {
        unless ($val =~ m/^[A-Za-z]+([dD][FPfp]|[cC]|[tT])\d+$/) {
          print "<FONT COLOR=red SIZE=+2>$val is not a valid Rearrangement name.</FONT><BR>";
          $mandatory_ok = 'bad'; }		# mandatory not right, print to resubmit
      } else { 					# check other mandatory fields
	unless ($val) { 			# if there's no value
          print "<FONT COLOR=red SIZE=+2>$mandatoryName{$_} is a mandatory field.</FONT><BR>";
          $mandatory_ok = 'bad'; }		# mandatory not right, print to resubmit
      }
    } # foreach $_ (@mandatory)

    (my $var, my $left_end) = &getHtmlVar($query, 'left_end');
    ($var, my $right_end) = &getHtmlVar($query, 'right_end');
    ($var, my $map) = &getHtmlVar($query, 'map');
    if ($left_end) { if ( ($right_end eq '') || ($map eq '') ) { 
      print "<FONT COLOR=red SIZE=+2>Left end requires Right end and Map.</FONT><BR>"; $mandatory_ok = 'bad'; } }
    if ($right_end) { if ( ($left_end eq '') || ($map eq '') ) { 
      print "<FONT COLOR=red SIZE=+2>Right end requires Left end and Map.</FONT><BR>"; $mandatory_ok = 'bad'; } }

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
      $body .= "$sender from ip $host sends :\n\n";
      my @all_vars = qw ( rearrangement submitter_email person_evidence type locus_phen allele strain phenotype map left_end right_end locus_in clone_in rearr_in locus_out clone_out rearr_out lab comment );
#       my @all_vars = qw ( submitter_email person_evidence rearrangement dfdp_gene dfdp_rearrangement dfdp_clone results genotype date comment );
  
#       my %aceName;
#       $aceName{submitter_email} = 'NULL';	# put in Reference if good, else Remark
#       $aceName{person_evidence} = 'Evidence';
#       $aceName{rearrangement} = 'Rearrangement_2';
#       $aceName{dfdp_gene} = 'Locus_1';
#       $aceName{dfdp_rearrangement} = 'Rearrangement_1';
#       $aceName{dfdp_clone} = 'Clone_1';
#       $aceName{results} = 'Results';
#       $aceName{genotype} = 'Genotype';
#       $aceName{date} = 'Date';
#       $aceName{comment} = 'NULL';

      my %bodyName;				# different tags for jonathan
      $bodyName{submitter_email} = 'Breakpt_EMAIL';
      $bodyName{person_evidence} = 'Breakpt_Data_provider';
      $bodyName{rearrangement} = 'Breakpt_Rearrangement';
      $bodyName{type} = 'type';
      $bodyName{locus_phen} = 'locus_phenotype';
      $bodyName{allele} = 'allele';
      $bodyName{strain} = 'Breakpt_Strain';
      $bodyName{phenotype} = 'phenotype';
      $bodyName{map} = 'Breakpt_Map';
      $bodyName{left_end} = 'Breakpt_Left_End';
      $bodyName{right_end} = 'Breakpt_Right_End';
      $bodyName{locus_in} = 'Breakpt_Positive_locus';
      $bodyName{clone_in} = 'Breakpt_Positive_clone';
      $bodyName{rearr_in} = 'Breakpt_Positive_rearr';
      $bodyName{locus_out} = 'Breakpt_Negative_locus';
      $bodyName{clone_out} = 'Breakpt_Negative_clone';
      $bodyName{rearr_out} = 'Breakpt_Negative_rearr';
      $bodyName{lab} = 'lab';
      $bodyName{comment} = 'comment';

      my ($var, $rearr) = &getHtmlVar($query, 'rearrangement');
      $result = $dbh->do( "INSERT INTO rea_rearr (rea_rearr) VALUES ('$rearr');" );
						# this updated the pg sequence rea_seq to nextval
      $result = $dbh->prepare( "SELECT currval('rea_seq');" );	
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
						# can get currval because last line updated
      my @row = $result->fetchrow;
      $joinkey = $row[0];
#       $joinkey = '12341234';
      print "Rearrangement entry number $joinkey<BR><BR>\n";
#       $body .= "joinkey\t$joinkey\n";
#       $ace_body .= "Pos_neg_data : \n";
#         $result = $dbh->do( "INSERT INTO rea_submitter_email VALUES ('$joinkey', '$sender');" );
      $result = $dbh->do( "INSERT INTO rea_ip VALUES ('$joinkey', '$host');" );
  
      foreach $_ (@all_vars) { 			# for all fields, check for data and output
        my ($var, $val) = &getHtmlVar($query, $_);
        if ($val =~ m/\S/) { 	# if value entered
          if ($var eq 'rearrangement') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	 
          elsif ($var eq 'map') { $val = uc($val); }	 		# uppercase chromosomes
          elsif ($var eq 'rearr_in') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	 
          elsif ($var eq 'rearr_out') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	 
          elsif ($var eq 'locus_in') { $val = lc($val); }		# lowercase genes
          elsif ($var eq 'locus_out') { $val = lc($val); }		# lowercase genes
          elsif ($var eq 'clone_in') { $val = uc($val); }		# uppercase clones
          elsif ($var eq 'clone_out') { $val = uc($val); }		# uppercase clones
#           elsif ($var eq 'dfdp_clone') { $val = uc($val); }	# uppercase clones
#             # fix D casing of rearrangements
#           elsif ($var eq 'dfdp_rearrangement') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	 
#           elsif ($var eq 'rearrangement') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	
#           elsif ($var eq 'date') { $val =~ s/\//-/g; }
          else { 1; }

#           if ($aceName{$var} ne 'NULL') { $ace_body .= "$aceName{$var}\t\"$val\"\n"; }
#             else { 1; }
          $body .= "$bodyName{$var}\t\"$val\"\n";
          if ($var eq 'person_evidence') { &findName($val); }
          my $pg_table = 'rea_' . $var;
          $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
        } # if ($val) 
      } # foreach $_ (@vars) 
#       my $full_body = $body . "\n" . $ace_body;
#       $keith_body .= "\n" . $body . "\n" . $ace_body;
      $keith_body .= "\n" . $body . "\n";
#       print OUT "$full_body\n";			# print to outfile
      print OUT "$body\n";			# print to outfile
      close (OUT) or die "cannot close $acefile : $!";
      $email .= ", $sender";
      &mailer($user, $email, $subject, $keith_body);	# email the data
      $body =~ s/\n/<BR>\n/mg;
#       $ace_body =~ s/\n/<BR>\n/mg;
      print "BODY : <BR>$body<BR><BR>\n";
#       print "ACE : <BR>$ace_body<BR><BR>\n";
      print "<P><P><P><H1>Thank you for your submission.  You will be contacted by WormBase within three working days.</H1>\n";
      print "If you wish to modify your submitted information, please go back and resubmit.<BR><P>\n";
#       print "See all <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/dfdp.ace\">new submissions</A>.<P>\n";

    } # else # unless ($sender =~ m/@.+\..+/)
  } # if ($action eq 'Submit') 
} # sub process


sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";
<a name="top">
<h2>Please use this form <font color="red">only</font> for reporting <B><font color="blue">new rearrangements</font></B>.</h2>Otherwise , use <a href = "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/df_dp.cgi">Deletion/duplication data submission form</a>, or <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/breakpoint.cgi">Breakpoint data submission form</a>. 
<p><font color="blue">Not all of the boxes have to be filled to submit your data, except the required ones.</font><p>

Sample format: <p>
Rearrangement name: eDf35<br> 
Data provider: Hodgkin JA<br>  
Comment: Induced by attached-X breakage<br> 
Locus inside: vab-14<br></p><hr>

<FORM>
   <FONT SIZE=+2><B>REQUIRED</B></FONT>
    <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR>
    <TABLE ALIGN="center"> 
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Rearrangement name</FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="rearrangement" Size="50"></TD>
        <TD>(eg. eDp10, eDf1)</TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Data provider</FONT></U> :</B></TD>
	<TD><Input Type="Text" Name="person_evidence" Size="50"></TD> 
        <TD>(eg. Hodgkin JA)</TD></TR>
    <TR><TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Email</FONT></U> :</B></TD>
        <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
        <TD>(please enter for contact purpose)
        <BR>If you don't get a verification email,<BR>email us at webmaster\@wormbase.org</TD>

    </TABLE>
    <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR>
    <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR>

    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD></TR><p><p>
    <TABLE ALIGN="center"> 
	<TR><TD ALIGN="right"><B>Type :</B></TD>	
	  <TD><select name="type" size = 1>
		  <option value="deletion">Deletion
		  <option value="Duplication">Duplication
		  <option value="Translocation">Translocation 
		  <option value="Compound">Compound
              </select></TD><TD>(if applicable)</TD>		  
	<TR><TD ALIGN="right"><B>Phenotype description:</B></TD>
	<TD><TEXTAREA Name="locus_phen" Rows=4 Cols=41></TEXTAREA></TEXTAREA></TD>     
        <TD>(if available)</TD><TD></TR>
        <TR><TD ALIGN="right"><B>Allele :</B></TD>
	<TD><Input Type="Text" Name="allele" size="50"></TEXTAREA></TD>     
        <TD>(if available, eg. gk1)</TD>
        <TD></TR>	      
         <TR> 
        <TR><TD ALIGN="right"><B>Strain :</B></TD>
	<TD><Input Type="Text" Name="strain" size="50"></TEXTAREA></TD>     
        <TD>(if available, eg. CB1. If CGC strain, genotype can be omitted)</TD>
        <TD></TR>	      
         <TR> 
        <TD ALIGN="right"><B>Strain genotype :</B></TD>
        <TD ><Input Type="text" Name="phenotype" Size="50"></TD>
        <TD >(eg, smg-1 (r904) unc-54 (r293) I)</td>
        <TR><TR><TR><TR><TR></TR>
        <TR bgcolor="#CCCCFF"><TD ALIGN="left" bgcolor="#CCCCFF"><B>Genetic map position</B></TD></TR>
	<TR bgcolor="#CCCCFF"><TD ALIGN="right" bgcolor="#CCCCFF"><B>&nbsp;&nbsp;&nbsp;&nbsp;Map :</B></TD>
	  <TD><select name="map" size = 1>
		  <option value="" selected>
		  <option value="I">I
		  <option value="II">II
		  <option value="III">III
		  <option value="IV">IV 
		  <option value="V">V
		  <option value="X">X
              </select></TD>
         <!--<TD bgcolor="#CCCCFF"><Input Type="Text" Name="map" Size="50"></TD>-->
         <TD bgcolor="#CCCCFF"></TD></TR>
	<TR bgcolor="#CCCCFF"><TD ALIGN="right" bgcolor="#CCCCFF"><B>&nbsp;&nbsp;&nbsp;&nbsp;Left end :</B></TD>
        <TD bgcolor="#CCCCFF"><Input Type="Text" Name="left_end" Size="50"></TD>
        <TD bgcolor="#CCCCFF">(eg. 25.83)</TD></TR>		
	<TR bgcolor="#CCCCFF"><TD ALIGN="right" bgcolor="#CCCCFF"><B>&nbsp;&nbsp;&nbsp;&nbsp;Right end :</B></TD>
      <TD bgcolor="#CCCCFF"><Input Type="Text" Name="right_end" Size="50"></TD>
        <TD bgcolor="#CCCCFF">(eg. 29.47)</TD></TR>
        <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
	<TR bgcolor="#99CCCC"><TD ALIGN="left" bgcolor="#99CCCC"><B>Positive</B></TD></TR>
	<TR bgcolor="#99CCCC"><TD ALIGN="right" bgcolor="#99CCCC"><B>&nbsp;&nbsp;&nbsp;&nbsp;Locus inside :</B></TD>
        <TD bgcolor="#99CCCC"><Input Type="Text" Name="locus_in" Size="50"></TD>
        <TD bgcolor="#99CCCC">(eg. abc-1)</TD></TR>		
        <TR bgcolor="#99CCCC"><TD ALIGN="right" bgcolor="#99CCCC"><B>&nbsp;&nbsp;&nbsp;&nbsp;Clone inside :</B></TD>
      <TD bgcolor="#99CCCC"><Input Type="Text" Name="clone_in" Size="50"></TD>
        <TD bgcolor="#99CCCC">(eg, a cosmid: C30E9)</TD> </TR>
	<TR bgcolor="#99CCCC"><TD ALIGN="right" bgcolor="#99CCCC"><B>&nbsp;&nbsp;&nbsp;&nbsp;Rearrangement inside :</B></TD>
      <TD bgcolor="#99CCCC"><Input Type="Text" Name="rearr_in" Size="50"></TD>
        <TD bgcolor="#99CCCC">(eg. mDf15)</TD></TR>	      
       </TR><p>
        <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
	<TR><TD ALIGN="left" bgcolor="#FFCCCC"><B>Negative</B></TD></TR>
	<TR><TD ALIGN="right" bgcolor="#FFCCCC"><B>&nbsp;&nbsp;&nbsp;&nbsp;Locus outside :</B></TD>
      <TD bgcolor="#FFCCCC"><Input Type="Text" Name="locus_out" Size="50"></TD>
        <TD bgcolor="#FFCCCC">(eg. xyz-1)</TD></TR>		
	<TR><TD ALIGN="right" bgcolor="#FFCCCC"><B>&nbsp;&nbsp;&nbsp;&nbsp;Clone outside :</B></TD>
      <TD bgcolor="#FFCCCC"><Input Type="Text" Name="clone_out" Size="50"></TD>
        <TD bgcolor="#FFCCCC">(eg, a cosmid: D340F8)</TD></TR>
	<TR><TD ALIGN="right" bgcolor="#FFCCCC"><B>&nbsp;&nbsp;&nbsp;&nbsp;Rearrangement outside :</B></TD>
      <TD bgcolor="#FFCCCC"><Input Type="Text" Name="rearr_out" Size="50"></TD>
        <TD bgcolor="#FFCCCC">(eg. mDf15)</TD></TR>	      
       </TR>
        <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
        <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
	<TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
  </TABLE>

    <TR><TD><FONT SIZE=+2><B>PERSONAL</B></FONT></TD></TR>
    <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR>
    <TABLE ALIGN="center">   
    <TR><TD ALIGN="right"><B>Laboratory designation</B><BR>
           (if known, eg., CB, PS.  <BR>See list 
            <A HREF="http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/labcore.ace">here</A>.)</TD>
        <TD><Input Type="Text" Name="lab" Size="50" Maxlength="3"></TD></TR>
    <TR></TR><TR><TD ALIGN="right"><B>Comment :</B></TD>
        <TD><TEXTAREA Name="comment" Rows=5 Cols=38></TEXTAREA></TD>
        <TD></TD></TR><TR></TR>
    <TR></TR><TR></TR><TR></TR><TR></TR> <TR></TR><TR></TR><TR></TR><TR></TR>
    </TABLE>

    <TABLE ALIGN="center">   	    
    <TR><TD></TD><TD><INPUT TYPE="submit" NAME="action" VALUE="Submit"><INPUT TYPE="reset"></TD></TR>
    </TABLE>
</FORM>

<hr>

<a href="#top">Top</a><p>
If you have any problems, questions, or comments, please contact <A HREF=\"mailto:gnw\@wormbase.org\">gnw\@wormbase.org</A>
EndOfText

  } # if (firstflag) show form 
} # sub display

sub findName {
  my $name = shift;
  if ($name !~ /\w/) { 	# if not a valid name, don't search
  } elsif ($name =~ /^\d+$/) { 		# if name is just a number, leave same
#   } elsif ($name =~ m/[\*\?]/) { 	# if it has a * or ?
#     &processpgwild($name);		# ignore pgwild for now
  } else { 			# if it doesn't do simple aka hash thing
    my %aka_hash = &getPgHash();
    &processakasearch($name, %aka_hash);
  }
} # sub findName

sub processakasearch {			# get generated aka's and try to find exact match
  my ($name, %aka_hash) = @_;
  my $search_name = lc($name);
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
    while (my @row = $result->fetchrow ) {
      $standard_name{$row[0]} = $row[2];
    } # while (my @row = $result->fetchrow )

#     print "<tr><td colspan=2 align=center>name <font color=red>$name</font> could be : </td></tr>\n";
    $keith_body .= "name $name could be : \n";
    my @stuff = sort {$a <=> $b} keys %{ $aka_hash{$search_name} };
    foreach $_ (@stuff) { 		# add url link
      my $joinkey = 'two'.$_;
      my $person = 'wbperson'.$_;
      $keith_body .= "\t$standard_name{$joinkey} $person\n";
#       print "<tr><td>$standard_name{$joinkey}</td><td><a href=http://www.wormbase.org/db/misc/etree?name=${person};class=person>$person</a></td></tr>\n";
    }

  }
  unless ($keith_body) { 
    $keith_body .= $name . " has no match, look here for possible matches : \n";
    $name =~ s/\s+/+/g;
    $keith_body .= 'http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person_name.cgi?action=Submit&name=' . "$name\n"; }
#   print "</TABLE>\n";
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

