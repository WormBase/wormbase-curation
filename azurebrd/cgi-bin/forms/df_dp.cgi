#!/usr/bin/perl 

# Form to submit Df/Dp information.

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


my $acefile = "/home/azurebrd/public_html/cgi-bin/data/dfdp.ace";

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
my $user = 'pos_neg_data_form';	# who sends mail
# my $email = 'ck1@sanger.ac.uk';	# to whom send mail
# my $email = 'cgc@wormbase.org';	# to whom send mail
my $email = 'genenames@wormbase.org';	# to whom send mail 2007 09 19
# my $email = 'azurebrd@tazendra.caltech.edu';	# to whom send mail
my $subject = 'Pos_neg_data submission';		# subject of mail
my $body = '';			# body of mail
my $ace_body = '';		# body of ace file
my $keith_body = '';		# body to mail but not show in form output
my $strain_body = '';		# body of strain file

print "Content-type: text/html\n\n";
my $title = 'Deficiency/Duplication mapping data submission Form';
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
    my @mandatory = qw ( submitter_email rearrangement person_evidence results );
    my %mandatoryName;				# hash of field names to print warnings
    $mandatoryName{submitter_email} = "Submitter Email";
    $mandatoryName{rearrangement} = "Rearrangement";
    $mandatoryName{person_evidence} = "Data Provider";
    $mandatoryName{results} = "Results";
 
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

    # must have only one of : gene, rearrangement, clone.
    my $xor = 0;
    my @xor = qw ( dfdp_gene dfdp_rearrangement dfdp_clone );
    foreach $_ (@xor) {
      my ($var, $val) = &getHtmlVar($query, $_);
      if ($val) { $xor++; } }
    unless ($xor == 1) { 
      $mandatory_ok = 'bad';
      print "<FONT COLOR=red SIZE=+2>You must enter data for exactly ONE of Locus, Rearrangement, or Clone.</FONT><BR>"; }

    if ($mandatory_ok eq 'bad') { 
      print "Please click back and resubmit.<P>";
    } else { 					# if email is good, process
      my $result;				# general pg stuff
      my $joinkey;				# the joinkey for pg
      open (OUT, ">>$acefile") or die "Cannot create $acefile : $!";
      my $host = $query->remote_host();		# get ip address
      $body .= "$sender from ip $host sends :\n\n";
      my @all_vars = qw ( submitter_email person_evidence rearrangement dfdp_gene dfdp_rearrangement dfdp_clone results genotype date comment );
#       my @all_vars = qw ( person_evidence submitter_email gene nature_of_allele penetrance partial_penetrance temperature_sensitive loss_of_function gain_of_function paper_evidence lab phenotypic_description sequence genomic assoc_strain species species_other alteration_type mutagen point_mutation_gene transposon_insertion sequence_insertion deletion upstream downstream comment );
  
      my %aceName;
      $aceName{submitter_email} = 'NULL';	# put in Reference if good, else Remark
      $aceName{person_evidence} = 'Evidence';
      $aceName{rearrangement} = 'Rearrangement_2';
      $aceName{dfdp_gene} = 'Locus_1';
      $aceName{dfdp_rearrangement} = 'Rearrangement_1';
      $aceName{dfdp_clone} = 'Clone_1';
      $aceName{results} = 'Results';
      $aceName{genotype} = 'Genotype';
      $aceName{date} = 'Date';
      $aceName{comment} = 'NULL';

      my %bodyName;				# different tags for jonathan
      $bodyName{submitter_email} = '//Df/Dp_EMAIL';
      $bodyName{person_evidence} = 'Df/Dp_Data_provider';
      $bodyName{rearrangement} = 'Df/Dp_Rearrangement_2';
      $bodyName{dfdp_gene} = 'Df/Dp_Gene_1';
      $bodyName{dfdp_rearrangement} = 'Df/Dp_Rearrangement_1';
      $bodyName{dfdp_clone} = 'Df/Dp_Clone_1';
      $bodyName{results} = 'Df/Dp_Results';
      $bodyName{genotype} = 'Df/Dp_Genotype';
      $bodyName{date} = 'Df/Dp_Date';
      $bodyName{comment} = 'Df/Dp_Comment';

      my ($var, $rearr) = &getHtmlVar($query, 'rearrangement');
      $result = $dbh->do( "INSERT INTO dfd_rearr (dfd_rearr) VALUES ('$rearr');" );
						# this updated the pg sequence dfd_seq to nextval
      $result = $dbh->prepare( "SELECT currval('dfd_seq');" );	
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
						# can get currval because last line updated
      my @row = $result->fetchrow;
      $joinkey = $row[0];
#       $joinkey = '12341234';
      print "Df/Dp entry number $joinkey<BR><BR>\n";
#       $body .= "joinkey\t$joinkey\n";
      $ace_body .= "Pos_neg_data : \n";
#         $result = $dbh->do( "INSERT INTO dfd_submitter_email VALUES ('$joinkey', '$sender');" );
      $result = $dbh->do( "INSERT INTO dfd_ip VALUES ('$joinkey', '$host');" );
  
      foreach $_ (@all_vars) { 			# for all fields, check for data and output
        my ($var, $val) = &getHtmlVar($query, $_);
        if ($val =~ m/\S/) { 	# if value entered
          if ($var eq 'dfdp_gene') { $val = lc($val); }		# lowercase genes
          elsif ($var eq 'dfdp_clone') { $val = uc($val); }	# uppercase clones
            # fix D casing of rearrangements
          elsif ($var eq 'dfdp_rearrangement') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	 
          elsif ($var eq 'rearrangement') { $val = lc($val); $val =~ s/[Dd]([a-z]\d+)$/D$1/; }	
          elsif ($var eq 'date') { $val =~ s/\//-/g; }
          else { 1; }

          if ($aceName{$var} ne 'NULL') { $ace_body .= "$aceName{$var}\t\"$val\"\n"; }
	  else { 1; }
          $body .= "$bodyName{$var}\t\"$val\"\n";
          if ($var eq 'person_evidence') { &findName($val); }
          my $pg_table = 'dfd_' . $var;
          $result = $dbh->do( "INSERT INTO $pg_table VALUES ('$joinkey', '$val');" );
        } # if ($val) 
      } # foreach $_ (@vars) 
      $ace_body .= "\n$strain_body";
      my $full_body = $body . "\n" . $ace_body;
      $keith_body .= "\n" . $body . "\n" . $ace_body;
      print OUT "$full_body\n";			# print to outfile
      close (OUT) or die "cannot close $acefile : $!";
      $email .= ", $sender";
      &mailer($user, $email, $subject, $keith_body);	# email the data
      $body =~ s/\n/<BR>\n/mg;
      $ace_body =~ s/\n/<BR>\n/mg;
      print "BODY : <BR>$body<BR><BR>\n";
      print "ACE : <BR>$ace_body<BR><BR>\n";
      print "<P><P><P><H1>Thank you, your info will be updated shortly.</H1>\n";
      print "If you wish to modify your submitted information, please go back and resubmit.<BR><P>\n";
#       print "See all <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/dfdp.ace\">new submissions</A>.<P>\n";

    } # else # unless ($sender =~ m/@.+\..+/)
  } # if ($action eq 'Submit') 
} # sub process


sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"EndOfText";
<p>
<a name="top"></a>
<h1>Deficiency/Duplication mapping data submission Form</h1>

Not all of the boxes have to be filled to submit your data, except the required ones.<p>
<font color="red">Each cross requires a separate form.<br>
Also each locus, about which deletion or duplicaton conclusions can be drawn, requires a separate form.<p> 
One mapping experiment therefore links together one rearrangement with only one locus</font>.<br><br>
If you would like more guidance and further examples click here for <a href="#dfdp">more information</a>.<p>

<a name="perm"></a>
The possible <font color="blue">permutations</font> for the Results line are:<p>
<table border=1 cellpadding=5 vspace=1 hspace=1>
<tr><th align=left>Deficiency</th>
    <th align=left>Duplication</th>
<tr><td align="left" valign=top>
     <menu>
       <li>xDfA deletes geneB
       <li>xDfA does not delete geneB<br><br>
       <li>xDfA includes xDfB
       <li>xDfA does not include xDfB<br><br>
       <li>xDfA overlaps xDfB				
       <li>xDfA does not overlap xDfB<br><br>
       <li>xDfA complements geneB
       <li>xDfA does not complement geneB
	  
     </menu>  
    </td>
    <td align="left" valign=top>
      <menu>
       <li>xDpA includes geneB
       <li>xDpA does not include geneB<br><br>
       <li>xDpA includes xDfB
       <li>xDpA does not include xDfB<br><br>
       
      </menu>
    </td>
</tr>
</table>
</p><hr>

<FORM>
   <FONT SIZE=+2><B>REQUIRED</B></FONT>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>

    <TABLE ALIGN="center"> 
      <TR><TD ALIGN="right"><U><FONT COLOR="red"><B>Submitter's Email</B></FONT></U>:&nbsp;
           <BR>(please enter for contact purpose)<BR>If you don't get a verification email,<BR>email us at webmaster\@wormbase.org</TD>
          <TD><Input Type="Text" Name="submitter_email" Size="50" Maxlength="50"></TD>		
      </TR> 
      <TR><TD ALIGN="right"><U><FONT COLOR="red"><B>Data provider</B></FONT></U>:&nbsp;</TD>
	<TD><Input Type="Text" Name="person_evidence" Size="50"></TD> 
        <TD>(eg. Hodgkin JA)</TD>
      </TR>
      <TR><TD ALIGN="right"><U<FONT COLOR="red"><B>Rearrangement</B></FONT></U>:&nbsp;</TD>
        <TD><Input Type="Text" Name="rearrangement" Size="50"></TD> 
        <TD>(eg. mcDf1, qDp2)</TD><TD>
      </TR> <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR bgcolor="#DCDDE7"><TD ALIGN="right"><B>Deletion or duplication</B></TD>
        <TD><B><font color="blue">( fill in only one of the three for each experiment )</font></B></TD>	  
      </TR>
      <TR bgcolor="#DCDDE7"><TD ALIGN="right" bgcolor="#DCDDE7"><B>&nbsp;&nbsp;&nbsp;&nbsp;Locus :</B></TD>
        <TD bgcolor="#DCDDE7"><Input Type="Text" Name="dfdp_gene" Size="50"></TD>
        <TD bgcolor="#DCDDE7">(if concerns a locus, eg. unc-119)</TD>
      </TR>
      <TR bgcolor="#DCDDE7"><TD ALIGN="right" bgcolor="#DCDDE7"><B>&nbsp;&nbsp;&nbsp;&nbsp;Rearrangement :</B></TD>
        <TD bgcolor="#DCDDE7"><Input Type="Text" Name="dfdp_rearrangement" Size="50"></TD>
        <TD bgcolor="#DCDDE7">(if concerns a 2nd rearrangement)</TD>
      </TR>		

      <TR bgcolor="#DCDDE7"><TD ALIGN="right" bgcolor="#DCDDE7"><B>&nbsp;&nbsp;&nbsp;&nbsp;Clone :</B></TD>
        <TD bgcolor="#DCDDE7"><Input Type="Text" Name="dfdp_clone" Size="50"></TD>
        <TD bgcolor="#DCDDE7">(if concerns a clone, eg. B0334)</TD>
      </TR> <TR></TR> <TR></TR> <TR></TR> <TR></TR><TR></TR><TR></TR>

      <TR><TD ALIGN="right" ><B>Results:&nbsp;</B></TD><TD><Input Type="text" Name="results"Size="50" ></TD>
          <TD>(eg. sDf3 deletes unc-303 <br>or see the <a href="#perm">permutations</a> on top)</TD><TD></TR>
      </TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    </TABLE>

    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    <TR></TR> <TR></TR> <TR></TR> <TR></TR>

    <TR><TD><FONT SIZE=+2><B>GENETIC</B></FONT></TD></TR><p><p>

    <TABLE ALIGN="center"> 
      <TR><TD ALIGN="right"><B>Genotype :</B></TD>
       	  <TD><TEXTAREA Name="genotype" Rows=4 Cols=48></TEXTAREA></TEXTAREA></TD>     
          <TD>(if available)<br>(eg, unc-42(e270)<br>her-1(e224)/dpy-11(e1518))</TD>
      </TR>

      <TR><TD ALIGN="right"><B>Date : (format yyyy-mm)&nbsp;</B></TD><TD><input type="text" name="date"Size="50" ></TD>
          <TD>(if available, e.g. 2004-01)</TD><TD>
      </TR>
      <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    </TABLE>

    <TR><TD><FONT SIZE=+2><B>PERSONAL</B></FONT></TD></TR><p><p>

    <TABLE ALIGN="center"> 
      <TR><TD ALIGN="right"><B>Comment :</B></TD>
       	  <TD><TEXTAREA Name="comment" Rows=4 Cols=48></TEXTAREA></TEXTAREA></TD>     
          <TD>(if available)</TD><TD>
      </TR>
      <TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR><TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
      <TR></TR> <TR></TR> <TR></TR> <TR></TR>
    </TABLE>

    <TABLE ALIGN="center">   	    
    <TR><TD> </TD>
      <TD><INPUT TYPE="submit" NAME="action" VALUE="Submit"><INPUT TYPE="reset"></TD></TR>
    </TABLE>
</FORM>
<hr>


<a name ="dfdp"></a>
<h2>Deficiency/Duplication Examples:</h2><p>

<font color="blue">Example 1:</font><p>

Mapper: Hodgkin JA<br>
Date: 1978-09<br>
Genotype: eDf1(e1405)/her-1(e1518) unc-42(e270) sma-1(e30) XO<br>
Locus: her-1<br>
Results: eDf1 does not delete her-1 ! see above for allowed list<br><p>

<font color="blue">Example 2:</font><p>

Mapper: Hodgkin JA<br>
Date: 1994-01<br>
Rearrangement: eDf100<br>
Locus: cm12c12<br>
Results: eDf100 deletes cm04g11<br>
Comment: cm04g11 is a cDNA hybridising to Y38B9 and Y4C6 on the polytene grid, assayed by PCR.<p>


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

