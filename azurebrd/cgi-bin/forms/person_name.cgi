#!/usr/bin/perl

# From to find Person information.

# Take a flatfile.ace of WBPerson numbers with possible
# first middle and last names.  Put into a hash of possible
# combinations of valid names (lowercased).  Get input from
# user and see which WBPerson Numbers match that input.
# 2003 03 17
#
# Changed to use PG for all searches.  Number search gets
# the Standardname.  AkaSearch creates the aka_hash from
# postgres.  PgWild does ~ match using lower() to make the
# search case insensitive.  Implemented priority of search
# paramters (length) for PgWild.  2003 03 25
#
# Added to it diplay from PG display and option to Edit
# by emailing Cecilia.  2003 06 20
#
# Clean up names of fields, take out some fields Cecilia
# didn't want there, made comments a Textarea.  Used 
# subs from paper.cgi and twoeditor.cgi  2003 06 23
#
# Added &checkFields(); to check that email, firstname,
# and lastname have been entered.  2003 06 24
#
# Added institution (keith, cecilia)  2004 04 05
#
# Changed institution to institution and old_institution
# for cecilia  2005 08 22
#
# Added ``Click here to submit : '' instructions next to
# Edit button for Cecilia and Johji Miwa.  2006 03 06
#
# Changed email and added query to top of form.  2006 06 06
#
# Append body of email to file in /home/cecilia/person_form/text_output_from_form
# 2006 06 06
#
# Didn't allow hyphens in emails, fixed now.  2006 06 07
#
# Changed ``Edit'' buttons to ``Preview'' buttons and added a Preview.
# Preview page has an ``Edit'' button which works the same.  2006 06 08
#
# Send confirmation email to user as well as Cecilia.  2006 08 11
#
# Check if data is new or has changed, and mark it so.  2006 10 31
#
# Add standardname to aka_hash  2007 02 27
#
# person_name.cgi used to use Ace.pm and a local copy, it should just use
# Postgres like person.cgi  2007 12 15

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my @two_tables = qw(email firstname middlename lastname standardname street city state post country institution old_institution mainphone labphone officephone otherphone fax old_email lab oldlab left_field aka_firstname aka_middlename aka_lastname webpage );
my @two_simpler = qw(comment );

my $blue = '#00ffcc';                   # redefine blue to a mom-friendly color
my $red = '#00ffff';                    # redefine red to a mom-friendly color


my $query = new CGI;
my $firstflag = 1;

my %flags;				# hack to have flags.

print "Content-type: text/html\n\n";
my $title = 'Person Search Form';
my ($header, $footer) = &cshlNew($title);
print "$header\n";		# make beginning of HTML page

&process();			# see if anything clicked
&displayQuery();		# show query box
print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ( ($action eq 'Query') || ($action eq 'Submit')) {
    (my $oop, my $name) = &getHtmlVar($query, 'name');
    if ($name !~ m/\w/) {	# no action if no name
    } elsif ($name =~ /\d/) { 
      &processPgNumber($name);
    } elsif ($name =~ m/[\*\?]/) { 	# if it has a * or ?
      &processPgWild($name);
    } else { 			# if it doesn't do simple aka hash thing
      my %aka_hash = &getPgHash();
      &processAkaSearch($name, $name, %aka_hash);
    }
  } # if ($action eq 'Query') 
  elsif ($action eq 'Display') {	# show data already in PG
    (my $oop, my $number) = &getHtmlVar($query, 'number');
    $number =~ s/WBPerson//g;
    &displayOneDataFromKey($number);
  } # elsif ($action eq 'Display')
} # sub process

sub processPgWild {
  my $input_name = shift;
  $input_name =~ s/,//g;
  print "<TABLE>\n";
  print "<TR><TD>INPUT</TD><TD>$input_name</TD></TR>\n";
  my @people_ids;
  $input_name =~ s/\*/.*/g;
  $input_name =~ s/\?/./g;
  my @input_parts = split/\s+/, $input_name;
  my %input_parts;
  my %matches;				# keys = wbid, value = amount of matches
  my %filter;
  foreach my $input_part (@input_parts) {
    my @tables = qw (first middle last);
    foreach my $table (@tables) { 
      my $result = $dbh->prepare( "SELECT * FROM two_aka_${table}name WHERE lower(two_aka_${table}name) ~ lower('$input_part');" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      while ( my @row = $result->fetchrow ) { $filter{$row[0]}{$input_part}++; }
      $result = $dbh->prepare( "SELECT * FROM two_${table}name WHERE lower(two_${table}name) ~ lower('$input_part');" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      while ( my @row = $result->fetchrow ) { $filter{$row[0]}{$input_part}++; }
    } # foreach my $table (@tables)
  } # foreach my $input_part (@input_parts)

  foreach my $number (sort keys %filter) {
    foreach my $input_part (@input_parts) {
      if ($filter{$number}{$input_part}) { 
        my $temp = $number; $temp =~ s/two/WBPerson/g; $matches{$temp}++; 
        my $count = length($input_part);
        unless ($input_parts{$temp} > $count) { $input_parts{$temp} = $count; }
      }
    } # foreach my $input_part (@input_parts)
  } # foreach my $number (sort keys %filter)
  
  print "<TR><TD></TD><TD>There are " . scalar(keys %matches) . " match(es).</TD></TR>\n";
  print "<TR></TR>\n";
  print "</TABLE>\n";
  print "<TABLE border=2 cellspacing=5>\n";
  foreach my $person (sort {$matches{$b}<=>$matches{$a} || $input_parts{$b} <=> $input_parts{$a}} keys %matches) { 
#     print "<TR><TD><A HREF=http://www.wormbase.org/db/misc/etree?name=${person};class=Person>$person</A></TD>\n";
    print "<TR><TD><A HREF=http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=Display&number=$person>$person</A></TD>\n";
    print "<TD>has $matches{$person} match(es)</TD><TD>priority $input_parts{$person}</TD></TR>\n";
  } 
  print "</TABLE>\n";
  
  unless (%matches) {
    print "<FONT COLOR=red>Sorry, no person named '$input_name', please try again</FONT><P>\n" if $input_name;
  }
} # sub processPgWild

sub processPgNumber {
  my $input_name = shift;
  if ($input_name =~ /(\d+)/) {   # and search just for number
    my $person = "WBPerson".$1;
    my $joinkey = "two".$1;
    my $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$joinkey';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    my @row = $result->fetchrow; 
    print "PERSON <FONT COLOR=red>$row[2]</FONT> has \n";
#     print "ID <A HREF=http://www.wormbase.org/db/misc/etree?name=${person};class=Person>$person</A>.<BR>\n";
    print "ID <A HREF=http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=Display&number=$person>$person</A>.</BR>\n";
  } # if ($input_name =~ /(\d*)/)
}

sub processAkaSearch {			# get generated aka's and try to find exact match
  my ($name, $name, %aka_hash) = @_;
  my $search_name = lc($name);
  $search_name =~ s/,//g;
  print "<TABLE>\n";
  unless ($aka_hash{$search_name}) { 
    print "<TR><TD>NAME <FONT COLOR=red>$name</FONT> NOT FOUND</TD></TR>\n";
    my @names = split/\s+/, $search_name; $search_name = '';
    foreach my $name (@names) {
      if ($name =~ m/^[a-zA-Z]$/) { $search_name .= "$name "; }
      else { $search_name .= '*' . $name . '* '; }
    }
    &processPgWild($name);
  } else { 
    my %standard_name;
    my $result = $dbh->prepare( "SELECT * FROM two_standardname;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow ) {
      $standard_name{$row[0]} = $row[2];
    } # while (my @row = $result->fetchrow )

    print "<TR><TD colspan=2 align=center>NAME <FONT COLOR=red>$name</FONT> could be : </TD></TR>\n";
    my @stuff = sort {$a <=> $b} keys %{ $aka_hash{$search_name} };
    foreach $_ (@stuff) { 		# add url link
      my $joinkey = 'two'.$_;
      my $person = 'WBPerson'.$_;
#       print "<TR><TD>$standard_name{$joinkey}</TD><TD><A HREF=http://www.wormbase.org/db/misc/etree?name=${person};class=Person>$person</A></TD></TR>\n";
      print "<TR><TD>$standard_name{$joinkey}</TD><TD><A HREF=http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=Display&number=$person>$person</A></TD>\n";
    }

#     my @stuff = keys %{ $aka_hash{$search_name} };
#     foreach (@stuff) { 		# add url link
#       $_ =~ s/two//g;
#       my $person = 'WBPerson'.$_;
#       $_ = "<A HREF=http://www.wormbase.org/db/misc/etree?name=${person};class=Person>$person</A>";
#     }
#     my $stuff = join", ", @stuff;
#     print "<TR><TD>NAME <FONT COLOR=red>$name</FONT> could be : $stuff </TD></TR>\n";
  }
  print "</TABLE>\n";
} # sub processAkaSearch


sub displayQuery {			# show form as appropriate
    print <<"EndOfText";
<FORM METHOD="POST" ACTION="person.cgi">
 
  <TABLE ALIGN="center"> 
    <TR><TD>Please enter the name you would like to search for to edit your information :</TD>
        <TD><Input Type="Text" Name="name" Size="20"></TD>
        <TD><INPUT TYPE="submit" NAME="action" VALUE="Query"></TD></TR>
    <TR>
      <TD> </TD>
<!--      <TD><INPUT TYPE="submit" NAME="action" VALUE="Submit"></TD>-->
    </TR>
  </TABLE>

</FORM>

EndOfText

} # sub displayQuery


sub getPgHash {				# get akaHash from postgres instead of flatfile
  my $result;
  my %filter;
  my %aka_hash;
  
  my @tables = qw (first middle last);
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM two_aka_${table}name WHERE two_aka_${table}name IS NOT NULL AND two_aka_${table}name != 'NULL' AND two_aka_${table}name != '';" );
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
    $result = $dbh->prepare( "SELECT * FROM two_${table}name WHERE two_${table}name IS NOT NULL AND two_${table}name != 'NULL' AND two_${table}name != '';" );
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
#             $possible = "$first"; $aka_hash{$possible}{$person}++;
            $possible = "$middle"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $first"; $aka_hash{$possible}{$person}++;
#             $possible = "$last"; $aka_hash{$possible}{$person}++;
#             $possible = "$last $first"; $aka_hash{$possible}{$person}++;
            $possible = "$last $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last $first $middle"; $aka_hash{$possible}{$person}++;
            $possible = "$last $middle $first"; $aka_hash{$possible}{$person}++;
#             $possible = "$first $last"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "$first $middle $last"; $aka_hash{$possible}{$person}++;
            $possible = "$middle $first $last"; $aka_hash{$possible}{$person}++;
          } # foreach my $middle (sort keys %{ $filter{$person}{middle}} )
        }
      } # foreach my $first (sort keys %{ $filter{$person}{first}} )
    } # foreach my $last (sort keys %{ $filter{$person}{last}} )
  } # foreach my $person (sort keys %filter) 

  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE two_standardname IS NOT NULL AND two_standardname != 'NULL' AND two_standardname != '';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while ( my @row = $result->fetchrow ) {
    if ($row[3]) { 					# if there's a time
      $row[0] =~ s/two//g;				# take out the 'two' from the joinkey
      $row[2] = lc($row[2]);
      $aka_hash{$row[2]}{$row[0]}++; } }		# add standardnames to aka hash		2007 02 27

  return %aka_hash;
} # sub getPgHash



sub displayOneDataFromKey {		# display PG data 
  my ($two_key) = 'two' . $_[0];
  print "<TABLE border=1 cellspacing=2>\n";
  print "<TR><TD colspan=4><FONT SIZE=+2><B><A HREF=http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi?action=Editor&number=$two_key>Click here to EDIT</A> if this is your information.</B></FONT></TD></TR>\n";
  my $counter = 0;
  foreach my $two_table (@two_tables) {
    my $result = $dbh->prepare( "SELECT * FROM two_$two_table WHERE joinkey = '$two_key' ORDER BY two_order;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      if ($row[1]) {
        print "<TR bgcolor='$blue'>\n  <TD>$two_table</TD>\n";
        print "  <TD>$row[1]</TD>\n";
        print "  <TD>$row[2]</TD>\n";
        print "  <TD>$row[3]</TD>\n";
        print "</TR>\n";
      } # if ($row[1])
    } # while (my @row = $result->fetchrow)
  } # foreach my $two_table (@two_tables)

  print "</TABLE><BR><BR>\n";
} # sub displayOneDataFromKey

sub displayOneNew {		# show form if new Person being created (first page)
  print "<H1>Add your info (Email, First and Last names are required) :</H1>\n";
  print "Author data is still being kept by WormBase, but its contact data is no longer updated.  WormBase now has Persons, whose contact data will be kept up-to-date, and who are being connected to the proper Authors and Publications.<P>\n";
  print "Please email <a href=mailto:cecilia\@tazendra.caltech.edu>Cecilia</a> if you have any questions, or to send her your data directly.<P>\n";
  print "If you would rather query to see if we already have your data, you may do so below (and then Edit if some of it needs updating).<P>\n";
  &displayQuery();		# show query box
  print "If you don't get a verification email, email us at webmaster\@wormbase.org<P>\n";


  my $two_key = 'NEW';		# default key named NEW

  print "<FORM METHOD=POST ACTION=person.cgi>\n";
  print "<TABLE border=1 cellspacing=2>\n";
  print "<TR><TD colspan=3>Click ``Preview'' to submit : <INPUT TYPE=submit NAME=action VALUE=\"Preview\"></TD></TR>\n";
  my $counter = 0;
  foreach my $two_table (@two_tables) {
    $counter = &makeExtraNew($two_table, $counter, 3); }
  foreach my $two_simpler (@two_simpler) {
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"two_number\" VALUE=\"$two_key\">\n";
    my ($disp_name) = ucfirst $two_simpler;
    print "<TR bgcolor='$red'>\n  <TD>$disp_name</TD>\n";
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"table_$counter\" VALUE=\"$two_simpler\">\n";
    print "  <TD><INPUT SIZE=5 NAME=\"num_$counter\" VALUE=\"1\"></TD>\n";
    print "  <TD><TEXTAREA ROWS=5 COLS=29 NAME=\"val_$counter\"></TEXTAREA></TD>\n";
    $counter++;
    print "</TR>\n"; }
#     $counter = &makeExtraNew($two_simpler, $counter, 3);
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"counter\" VALUE=\"$counter\">\n";
  print "<TR><TD colspan=3>Click ``Preview'' to submit : <INPUT TYPE=submit NAME=action VALUE=\"Preview\"></TD></TR>\n";
  print "</TABLE><BR><BR>\n";
  print "</FORM>\n";
} # sub displayOneNew 

sub makeExtraNew {		# create extra inputs for some (most) fields
  my ($two_table, $counter, $amount) = @_;
  if ( ($two_table eq 'firstname') || ($two_table eq 'middlename') || ($two_table eq 'lastname') ||
       ($two_table eq 'standardname') || ($two_table eq 'institution') || ($two_table eq 'old_institution') 
     ) { $amount = 0; }
  if ( ($two_table eq 'city') || ($two_table eq 'state') || ($two_table eq 'post') ||
       ($two_table eq 'country') || ($two_table eq 'pis') || 
       ($two_table eq 'lab') || ($two_table eq 'oldlab') || ($two_table eq 'left_field') || 
       ($two_table eq 'privacy') 
     ) { $amount = 1; }
  my $indent_flag = 0;
  for (0 .. $amount) {
    $indent_flag++;
    print "<TR bgcolor='$red'>\n";
    my ($disp_name) = ucfirst $two_table;
    if ($disp_name eq 'Pis') { $disp_name = 'P I'; }
    if ($disp_name eq 'Standardname') { $disp_name = 'Your Preferred Name'; }
    if ($indent_flag == 1) { print "  <TD>$disp_name</TD>\n"; }
    else { print "  <TD>&nbsp;&nbsp;&nbsp;&nbsp;$disp_name</TD>\n"; }
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"table_$counter\" VALUE=\"$two_table\">\n";
    print "  <TD><INPUT SIZE=5 NAME=\"num_$counter\" VALUE=\"$indent_flag\"></TD>\n";
    print "  <TD><INPUT SIZE=40 NAME=\"val_$counter\" VALUE=\"\"></TD>\n";
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"new_$counter\" VALUE=\"new\">\n";
    $counter++;
    print "</TR>\n";
  } # for (0 .. $amount)
  return $counter;
} # sub makeExtraNew

sub displayOneEditFromKey {	# form to edit queried data
  print "<H1>Add your info (Email, First and Last names are required) :</H1>\n";
  print "Please email <a href=mailto:cecilia\@tazendra.caltech.edu>Cecilia</a> if you have any questions, or to send her your data directly.<P>\n";
  my ($two_key) = shift;
  print "<FORM METHOD=POST ACTION=person.cgi>\n";
  print "<TABLE border=1 cellspacing=2>\n";
  print "<TR><TD><INPUT TYPE=submit NAME=action VALUE=\"Preview\"></TD></TR>\n";
  my $counter = 0;
  foreach my $two_table (@two_tables) {
    my $result = $dbh->prepare( "SELECT * FROM two_$two_table WHERE joinkey = '$two_key';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"two_number\" VALUE=\"$two_key\">\n";
    while (my @row = $result->fetchrow) {
      if ($row[1]) {
        my ($disp_name) = ucfirst $two_table;
        if ($disp_name eq 'Pis') { $disp_name = 'P I'; }
        if ($disp_name eq 'Standardname') { $disp_name = 'Your Preferred Name'; }
        if ($two_table eq 'middlename') { $flags{middlename}++; }
        print "<TR bgcolor='$blue'>\n  <TD>$disp_name</TD>\n";
        print "  <INPUT TYPE=\"HIDDEN\" NAME=\"table_$counter\" VALUE=\"$two_table\">\n";
        print "  <TD><INPUT SIZE=5 NAME=\"num_$counter\" VALUE=\"$row[1]\"></TD>\n";
        print "  <TD><INPUT SIZE=40 NAME=\"val_$counter\" VALUE=\"$row[2]\"></TD>\n";
        $counter++;
        print "</TR>\n";
      } # if ($row[1])
    } # while (my @row = $result->fetchrow)
    $counter = &makeExtraFields($two_table, $counter, 2, $two_key);
  } # foreach my $two_table (@two_tables)

  foreach my $two_simpler (@two_simpler) {
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"two_number\" VALUE=\"$two_key\">\n";
    my ($disp_name) = ucfirst $two_simpler;
    print "<TR bgcolor='$red'>\n  <TD>$disp_name</TD>\n";
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"table_$counter\" VALUE=\"$two_simpler\">\n";
    print "  <TD><INPUT SIZE=5 NAME=\"num_$counter\" VALUE=\"1\"></TD>\n";
    print "  <TD><TEXTAREA ROWS=5 COLS=29 NAME=\"val_$counter\"></TEXTAREA></TD>\n";
    $counter++;
    print "</TR>\n";
  } # foreach my $two_simpler (@two_simpler)

  print "<INPUT TYPE=\"HIDDEN\" NAME=\"counter\" VALUE=\"$counter\">\n";
  print "<TR><TD><INPUT TYPE=submit NAME=action VALUE=\"Preview\"></TD></TR>\n";
  print "</TABLE><BR><BR>\n";
  print "</FORM>\n";
} # sub displayOneEditFromKey

sub makeExtraFields {		# create extra inputs for some (most) fields
  my ($two_table, $counter, $amount, $two_key) = @_;
  next if ($two_table eq 'firstname');
  next if ($two_table eq 'lastname');
  next if ($two_table eq 'standardname');
  next if ($two_table eq 'institution');
  next if ($two_table eq 'old_institution');
  next if (($two_table eq 'middlename') && ($flags{middlename}));
  if ( ($two_table eq 'city') || ($two_table eq 'state') || ($two_table eq 'post') ||
       ($two_table eq 'country') || ($two_table eq 'pis') || 
       ($two_table eq 'lab') || ($two_table eq 'oldlab') || ($two_table eq 'left_field') || 
       ($two_table eq 'privacy') || ($two_table eq 'middlename') 
     ) { $amount = 0; }
  my $indent_flag = 0;
  for (0 .. $amount) {
    $indent_flag++;
    print "<TR bgcolor='$red'>\n";
    my ($disp_name) = ucfirst $two_table;
    if ($disp_name eq 'Pis') { $disp_name = 'P I'; }
    if ($disp_name eq 'Standardname') { $disp_name = 'Your Preferred Name'; }
    if ($indent_flag == 1) { print "  <TD>$disp_name</TD>\n"; }
    else { print "  <TD>&nbsp;&nbsp;&nbsp;&nbsp;$disp_name</TD>\n"; }
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"table_$counter\" VALUE=\"$two_table\">\n";
    print "  <TD><INPUT SIZE=5 NAME=\"num_$counter\" VALUE=\"\"></TD>\n";
    print "  <TD><INPUT SIZE=40 NAME=\"val_$counter\" VALUE=\"\"></TD>\n";
    print "  <INPUT TYPE=\"HIDDEN\" NAME=\"new_$counter\" VALUE=\"new\">\n";
    $counter++;
    print "</TR>\n";
  } # for (0 .. $amount)
  return $counter;
} # sub makeExtraFields


sub preview {
  print "<FORM METHOD=POST ACTION=person.cgi>\n";
  my $oop;                              # initialize $oop
  if ($query->param('two_number')) { $oop = $query->param('two_number'); }
    else { $oop = 'nodatahere'; }
  my $two_number = untaint($oop);
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"two_number\" VALUE=\"$two_number\">\n";
  if ($query->param('counter')) { $oop = $query->param('counter'); }
    else { $oop = 'nodatahere'; }
  my $counter = untaint($oop);
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"counter\" VALUE=\"$counter\">\n";
  print "<FONT SIZE=+2><B>You've entered the following information.  If this information is correct
click ``Edit'', otherwise click ``Back'' on your browser and edit that
information.<INPUT TYPE=submit NAME=action VALUE=\"Edit\"></B></FONT><P>\n";
  if ($counter & $two_number) {         # check we've got a number and data
    print "<TABLE border=2 cellspacing=5>\n";
    for (my $i=0; $i<$counter; $i++) {
      if ($query->param("table_$i")) { $oop = $query->param("table_$i"); }
        else { $oop = 'nodatahere'; }
      my $table = untaint($oop);
      print "  <INPUT TYPE=\"HIDDEN\" NAME=\"table_$i\" VALUE=\"$table\">\n";
      if ($query->param("num_$i")) { $oop = $query->param("num_$i"); }
        else { $oop = 'nodatahere'; }
      my $num = untaint($oop);
      print "  <INPUT TYPE=\"HIDDEN\" NAME=\"num_$i\" VALUE=\"$num\">\n";
      if ($query->param("val_$i")) { $oop = $query->param("val_$i"); }
        else { $oop = 'nodatahere'; }
      my $val = untaint($oop);
      print "  <INPUT TYPE=\"HIDDEN\" NAME=\"val_$i\" VALUE=\"$val\">\n";
      unless ( ($val eq 'nodatahere') || ($val eq 'NULL') ) {
        print "<TR><TD>$table</TD><TD>$num</TD><TD>$val</TD></TR>\n"; }
    } # for (my $i=0; $i<$counter; $i++)
    print "</TABLE>\n";
  } # if ($counter & $two_number)
  print "</FORM>\n";
} # sub preview

sub mailCeciliaData {
  my $sender_email = shift;
#   my $user = 'Person_Form_Minerva <cecilia@tazendra.caltech.edu>';
  my $user = $sender_email;
  my $email = $sender_email . ', cecilia@tazendra.caltech.edu';
  my $subject = 'Update From Person Form';
  my $host = $query->remote_host();	# get ip address
  my $body = "From IP $host sends :\n\n";

  my $oop;                              # initialize $oop
  if ($query->param('two_number')) { $oop = $query->param('two_number'); }
    else { $oop = 'nodatahere'; }
  my $two_number = untaint($oop);
  if ($query->param('counter')) { $oop = $query->param('counter'); }
    else { $oop = 'nodatahere'; }
  my $counter = untaint($oop);
  print "<FONT SIZE=+2><B>Thank you for submitting this data :</B></FONT><P>\n";
  if ($counter & $two_number) {         # check we've got a number and data
    print "<TABLE border=2 cellspacing=5>\n";
    for (my $i=0; $i<$counter; $i++) {
      if ($query->param("table_$i")) { $oop = $query->param("table_$i"); }
        else { $oop = 'nodatahere'; }
      my $table = untaint($oop);
      if ($query->param("num_$i")) { $oop = $query->param("num_$i"); }
        else { $oop = 'nodatahere'; }
      my $num = untaint($oop);
      if ($query->param("val_$i")) { $oop = $query->param("val_$i"); }
        else { $oop = 'nodatahere'; }
      my $val = untaint($oop);
      unless ($val eq 'nodatahere') {
        print "<TR><TD>$table</TD><TD>$num</TD><TD>$val</TD></TR>\n"; 
        $body .= "$table\t$num\t$val\n"; 
        my $result = $dbh->prepare( "SELECT * FROM two_$table WHERE joinkey = '$two_number' AND two_order = '$num' ORDER BY two_timestamp DESC;" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        my @row = $result->fetchrow;
        if ($row[2]) { if ($row[2] ne $val) { $body .= "* CHANGED FROM $row[2] TO $val\n"; } }
          else { $body .= "* NEW $table\t$num\t$val\n"; }
      }
    } # for (my $i=0; $i<$counter; $i++)
    print "</TABLE>\n";
    $subject = $two_number . " $subject";
    $body .= "\n\nYour updated profile will show in our next upload, (approx 6 weeks) in our Home Page :\nhttp://www.wormbase.org/\nunder Author/Person search.";
    &mailer($user, $email, $subject, $body);    # email CGI to user
  } # if ($counter & $two_number)

  my $outfile = '/home/cecilia/person_form/text_output_from_form';
  open (OUT, ">>$outfile") or die "Cannot append to $outfile : $!";
  print OUT "$body\n\n";
  close (OUT) or die "Cannot close to $outfile : $!";
} # mailCeciliaData

sub checkFields {
  my $sender_email = '';
  my $oop;                              # initialize $oop
  my $ok_flag = '';			# flag to return all good
  my %hash_user_data;			# HoA with user data (not ordered by user numbers)
  if ($query->param('two_number')) { $oop = $query->param('two_number'); }
    else { $oop = 'nodatahere'; }
  my $two_number = untaint($oop);
  if ($query->param('counter')) { $oop = $query->param('counter'); }
    else { $oop = 'nodatahere'; }
  my $counter = untaint($oop);
  if ($counter & $two_number) {         # check we've got a number and data
#     print "<TABLE border=2 cellspacing=5>\n";
    for (my $i=0; $i<$counter; $i++) {
      if ($query->param("table_$i")) { $oop = $query->param("table_$i"); }
        else { $oop = 'nodatahere'; }
      my $table = untaint($oop);
      if ($query->param("num_$i")) { $oop = $query->param("num_$i"); }
        else { $oop = 'nodatahere'; }
      my $num = untaint($oop);
      if ($query->param("val_$i")) { $oop = $query->param("val_$i"); }
        else { $oop = 'nodatahere'; }
      my $val = untaint($oop);
      push @{ $hash_user_data{$table} }, $val;
#       unless ($val eq 'nodatahere') {
#         print "<TR><TD>$table</TD><TD>$num</TD><TD>$val</TD></TR>\n"; 
#       }
    } # for (my $i=0; $i<$counter; $i++)
#     print "</TABLE>\n";
  } # if ($counter & $two_number)
  if ($hash_user_data{firstname}[0] ne 'nodatahere') { 
    unless ($hash_user_data{firstname} =~ m/\w/) { $ok_flag = 'bad'; print "<FONT COLOR=red>Bad first name</FONT><BR>\n"; }
  } else { $ok_flag = 'bad'; print "<FONT COLOR=red>Bad first name</FONT><BR>\n";  }
  if ($hash_user_data{lastname}[0] ne 'nodatahere') { 
    unless ($hash_user_data{lastname} =~ m/\w/) { $ok_flag = 'bad'; print "<FONT COLOR=red>Bad last name</FONT><BR>\n"; }
  } else { $ok_flag = 'bad'; print "<FONT COLOR=red>Bad last name</FONT><BR>\n"; }
  my $email_flag;
  foreach my $email (@{ $hash_user_data{email} }) {
    if ($email) { 
      if ($email =~ m/[\w\-]+\@[\-\w]+\.[\w+\-]/) { $email_flag = 'good'; $sender_email = $email; } } 
  }
  unless ($email_flag) { $ok_flag = 'bad'; print "<FONT COLOR=red>Bad email address</FONT><BR>\n"; }
  if ($ok_flag eq 'bad') { print "<FONT COLOR=red><B>Please click your browser's back button and resubmit.</B></FONT><BR>\n"; }
  return ($ok_flag, $sender_email);
} # sub checkFields

