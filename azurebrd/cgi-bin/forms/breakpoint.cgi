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
# Changed for breakpoint data.  2004 02 26
#
# Chao-Kung not in WormBase, changed to cgc@wormbase.org   2004 07 07
#
# Changed for xTn and xCn data like the rearrangemment form.  2006 07 17


my $acefile = "/home/azurebrd/public_html/cgi-bin/data/breakpoint.ace";

my $firstflag = 1;		# flag if first time around (show form for no data)

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use Fcntl;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $query = new CGI;
my $user = 'breakpoint_form';	# who sends mail
# my $email = 'ck1@sanger.ac.uk';	# to whom send mail
# my $email = 'cgc@wormbase.org';	# to whom send mail
my $email = 'genenames@wormbase.org';	# to whom send mail 2007 09 19
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = 'New Breakpoint submission';	# subject of mail
my $body = '';			# body of mail
my $ace_body = '';		# body of ace file
my $keith_body = '';		# body to mail but not show in form output

print "Content-type: text/html\n\n";
my $title = 'New Breakpoint submission form';
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

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
      $body .= "$sender from ip $host sends :\n\n";
      my @all_vars = qw ( rearrangement person_evidence submitter_email positive negative comment );
#       my @all_vars = qw ( rearrangement submitter_email person_evidence type locus_phen allele strain phenotype map left_end right_end locus_in clone_in rearr_in locus_out clone_out rearr_out lab comment );
  
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
      $bodyName{positive} = 'Breakpt_Positive';
      $bodyName{negative} = 'Breakpt_Negative';
      $bodyName{comment} = 'comment';

      my ($var, $rearr) = &getHtmlVar($query, 'rearrangement');
      $result = $dbh->do( "INSERT INTO bre_rearr (bre_rearr) VALUES ('$rearr');" );
						# this updated the pg sequence bre_seq to nextval
      $result = $dbh->prepare( "SELECT currval('bre_seq');" );	
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
						# can get currval because last line updated
      my @row = $result->fetchrow;
      $joinkey = $row[0];
#       $joinkey = '12341234';
      print "Breakpoint entry number $joinkey<BR><BR>\n";
#       $body .= "joinkey\t$joinkey\n";
#       $ace_body .= "Pos_neg_data : \n";
#         $result = $dbh->do( "INSERT INTO bre_submitter_email VALUES ('$joinkey', '$sender');" );
      $result = $dbh->do( "INSERT INTO bre_ip VALUES ('$joinkey', '$host');" );
  
      foreach $_ (@all_vars) { 			# for all fields, check for data and output
        my ($var, $val) = &getHtmlVar($query, $_);
        if ($val =~ m/\S/) { 	# if value entered
          if ($var eq 'rearrangement') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	 
          elsif ($var eq 'positive') { $val = uc($val); }	 	# uppercase positive
          elsif ($var eq 'negative') { $val = uc($val); }	 	# uppercase negative
          else { 1; }

          $body .= "$bodyName{$var}\t\"$val\"\n";
          if ($var eq 'person_evidence') { &findName($val); }
          my $pg_table = 'bre_' . $var;
          $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
        } # if ($val) 
      } # foreach $_ (@vars) 
      $keith_body .= "\n" . $body . "\n";
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

<A NAME="form"><H1>Breakpoint Data Submission Form :</H1></A>
<center>
</center>
<HR>
<P>Example format:</P>

<font color="#006699">Rearrangement</font>: eDf35<br>
<font color="#006699">Data_provider</font>: Hodgkin JA <br>
<font color="#006699">Negative_clone</font>: AH51 <br>
<font color="#006699">Positive_clone</font>: AH29 <br>
<font color="#006699">Breakpt_Comment</font>: Primer pair from left end of AH13 fails to amplify on eDf35 DNA, <br>
primer pair from right end of AH13 does amplify on eDf35 DNA.<br>
<hr>
<form>
 <table width="90%" height="275" cellpadding="1" cellspacing="1">  
  <TR><td width="32%"><FONT SIZE=+2><B>REQUIRED</B></FONT></td>
      <td colspan="2">&nbsp;</td> </tr>  
  <tr> <TD ALIGN="right">&nbsp;</TD> <TD>&nbsp;</TD> <TD>&nbsp;</TD> </tr>
  <tr>
    <TD ALIGN="right"><U><FONT COLOR='red'><B>Rearrangement</B></FONT></U><B> :</B></TD>
    <TD width="30%"><Input Type="Text" Name="rearrangement" Size="50"></TD>
    <TD width="38%">(e.g. mcDf1)</font></TD> </tr>
  <TR>
    <TD ALIGN="right"><U><FONT COLOR='red'><B>Data provider</B></FONT></U><B> :</B></TD>
    <TD><Input Type="Text" Name="person_evidence" Size="50"> </TD>
    <TD>(Please enter full name, eg. Sulston, John)</font></TD> </TR>
  <TR>
    <TD ALIGN="right"><U><FONT COLOR='red'><B>Submitter's Email</B></FONT></U><B> :</B></TD>
    <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>
    <TD>(for contact purpose)</font><BR>If you don't get a verification email, email us at webmaster\@wormbase.org</TD> </TR>
  <TR> <TD ALIGN="right">&nbsp;</TD> <TD>&nbsp;</TD> <TD>&nbsp;</TD> </TR>
  <tr> <td colspan="3"><FONT SIZE=+2><B>MAPPING DATA</B></FONT></td> </tr>
  <tr> <td colspan="3">&nbsp;</td> </tr>
  <tr>
    <td align="right">Positive clone : </td>
    <td><input type="text" Name="positive" size="50" ></td>
    <td>(e.g. AH13)</td> </tr>
  <tr>
    <td align="right">Negative clone : </td>
    <td><input type="text" Name="negative" size="50"></td>
    <td>(e.g. T28H11)</td> </tr>
  <tr> <td align="right">&nbsp;</td> <td>&nbsp;</td> <td>&nbsp;</td> </tr>
  <tr> <td><FONT SIZE=+2><b>PERSONAL</b></FONT></td> <td>&nbsp;</td> <td>&nbsp;</td> </tr>
  <tr> <td>&nbsp;</td> <td>&nbsp;</td> <td>&nbsp;</td> </tr>
    <TR></TR><TR><TD ALIGN="right">Comment :</TD>
        <TD><TEXTAREA Name="comment" Rows=4 Cols=47></TEXTAREA></TD>
        <TD></TD></TR><TR></TR>
    <TR><TD></TD><TD><INPUT TYPE="submit" NAME="action" VALUE="Submit"><INPUT TYPE="reset"></TD></TR>
 </table>
</form>
EndOfText

  } # if (firstflag) show form 
} # sub display

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

