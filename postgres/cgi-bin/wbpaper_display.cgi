#!/usr/bin/perl -w

# Display WBPaper data

# Preliminary display of wbp_ tables from the demo4 database.  Table columns
# don't necessarily start with wbp_ some tables don't have data.  Allow query
# by either : a number, an author (or substring), a title (or substring).
# 2005 03 04
#
# Added display of PDFs from Daniel's repository by checking against the 
# wbp_identifier table to find cgc and pmid.  
# Added display of wbp_identifier table.
# Merged hardcopy and type table with generic tables, resulting in a display
# with too many n/a entries.  Hopefully can be cleaned up by adding comments
# to all generic tables, putting privacy somewhere else (a different table),
# and merging type id and data in the display (this form) and editor.
# 2005 03 21
#
# Modified for wpa_ tables.  2005 06 29
#
# Refined Number search, explanation text for Author and Title search.
# List all PDFs that could match.
# List all Author connection data (affiliation, possibles, sents, verifieds)
# List electronic and hardcopy status.
# List identifier xrefs.
# List wpa (to see whether the paper at all is valid or not.)  2005 06 30
#
# Use wpa_identifier, not wpa_xref for number search.  2005 07 27
#
# Show merged papers with a red text naming the paper that should be used
# instead.  2005 11 07
#
# Allow search by author_id, for Cecilia  2006 04 20
#
# Added link to WormBase  2006 06 20
#
# Use wpa_ignore instead of cur_comment for displaying the ignorability of a
# paper.  Change wpa_match.pm to insert to cur_comment and wpa_ignore.  2008 10 08
#
# Put the verified timestamp in the display   2009 01 20
#
# Use cfp_curator instead of cur_curator  2009 05 19
#
# Updated to use DBI instead of Pg  2009 09 17


 
use strict;
use CGI;
use Fcntl;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 


my $query = new CGI;

# use Pg;
# my $conn = Pg::connectdb("dbname=testdb");
# die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;

my $frontpage = 1;
my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color


my %type_index;				# hash of possible 7 types of paper
my %electronic_type_index;		# hash of possible 7 types of electronic paper
&populateTypeIndex();	

# my @generic_tables = qw( title publisher journal volume pages year abstract affiliation comments paper );

my @generic_tables = qw( wpa wpa_identifier wpa_title wpa_publisher wpa_journal wpa_volume wpa_pages wpa_year wpa_date_published wpa_fulltext_url wpa_abstract wpa_affiliation wpa_type wpa_ignore wpa_author wpa_hardcopy wpa_comments wpa_editor wpa_nematode_paper wpa_contained_in wpa_contains wpa_keyword wpa_erratum wpa_in_book );


&printHeader('WBPaper Display');
&display();
&printFooter();

sub display {
  my $action;

  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); }
  } else { $frontpage = 0; }

  if ($action eq 'Number !') { &pickNumber(); }
  elsif ($action eq 'Author !') { &pickAuthor(); }
  elsif ($action eq 'Title !') { &pickTitle(); }
  else { 1 }
} # sub display

sub pickNumber {
  my ($oop, $number) = &getHtmlVar($query, 'number');
  unless ($number) { $number = 1; }	# sometimes no number or zero would cause a serverlog error on next line
  print "NUMBER : $number<P>\n";
  my $result = $dbh->prepare( "SELECT wpa_valid FROM wpa WHERE joinkey = '$number' ORDER BY wpa_timestamp DESC;" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow; 
  if ($row[0]) { if ($row[0] eq 'invalid') { 
    my $identifier = ''; $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ '$number' ORDER BY wpa_timestamp;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $identifier = $row[0]; } else { $identifier = ''; } }
    print "<FONT COLOR='red' SIZE=+2>NOT a valid paper";
    if ($identifier) { print ", merged with $identifier"; }
    print ".</FONT><P>\n"; } }
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }
  $result = $dbh->prepare( "SELECT * FROM wpa WHERE wpa = '$number'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  @row = $result->fetchrow;
  if ($row[0]) { &displayOneDataFromKey($number); }
  else { 
    print "There is no exact match for WBPaper $number<BR>\n"; 
    my %xref_type;
    my $result = $dbh->prepare( "SELECT * FROM wpa_identifier; "); 
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my %xref;
    while (my @row = $result->fetchrow) {
      $row[0] =~ s/\D//g;
      $xref{full}{$row[1]}{$row[0]}++;
      my ($xref_type) = $row[1] =~ m/(^\D+)/;
      $xref_type{$xref_type}++;
      $row[1] =~ s/\D//g;
      $xref{num}{$row[1]}{$row[0]}++;
    } # while (my @row = $result->fetchrow)
    my ($number_type) = $number =~ m/^(\D+)/;
    if ($xref_type{$number_type}) { 	# matches type e.g. cgc
      print "There are $xref_type{$number_type} wpa_identifier that match the paper type '$number_type'.<BR>\n";
      if ($xref{full}{$number}) {
        foreach my $joinkey ( sort keys %{ $xref{full}{$number} } ) {
          print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$joinkey&action=Number+%21\">wbpaper id : $joinkey</A><BR>\n"; } } }
    else {				# doesn't match type
      $number =~ s/\D+//g;
      foreach my $joinkey ( sort keys %{ $xref{num}{$number} } ) {
        print "$number matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$joinkey&action=Number+%21\">wbpaper id : $joinkey</A><BR>\n"; } }
  }
} # sub pickNumber

sub pickAuthor {
  my ($oop, $author) = &getHtmlVar($query, 'author');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %authors;
  my %matches;
  print "AUTHOR : $author<P>\n";

  my $table_type = 'wpa_author_index';		# allow search by author_id 2006 04 20
  if ($author =~ m/^\d+$/) { $table_type = 'author_id'; }

  if ($exact_or_sub eq 'exact') {
    my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE $table_type = '$author' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $authors{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
    my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE $table_type ~ '$author' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $authors{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  foreach my $author_id (sort keys %authors) {
    my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE wpa_author = '$author_id' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } # foreach my $author_id (sort keys %authors)

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $author.<BR>\n"; }
  else {
    if (scalar(keys %matches) == 1) { print "There is " . scalar(keys %matches) . " $exact_or_sub match : <BR>\n"; }
    else { 
      print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
      print "<TABLE border=0><TR><TD>WBPaperID</TD><TD>Author ID</TD><TD>Author Name</TD><TD>Title</TD><TD>Journal</TD></TR>\n"; }
    foreach my $number (sort keys %matches) { 
      my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      my @row = $result->fetchrow; my $title = $row[1];
      $result = $dbh->prepare( "SELECT * FROM wpa_journal WHERE joinkey = '$number' AND wpa_valid = 'valid';" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      @row = $result->fetchrow; my $journal = $row[1];
#       print "Matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$number&action=Number+%21\">wbpaper id : $number -> author id : $matches{$number} -> author name : $authors{ $matches{$number} } <BR>title : $title<BR>journal : $journal</A><BR>\n";
      print "<TR><TD><A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$number&action=Number+%21\">$number</TD><TD>$matches{$number}</TD><TD>$authors{ $matches{$number} } </TD><TD>$title</TD><TD>$journal</A></TD></TR>\n";
     }
  }
} # sub pickAuthor

sub pickTitle {
  my ($oop, $title) = &getHtmlVar($query, 'title');
  my ($oop2, $exact_or_sub) = &getHtmlVar($query, 'exact_or_sub');
  my %matches;
  print "TITLE : $title<P>\n";

  if ($exact_or_sub eq 'exact') {
    my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE wpa_title = '$title' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } elsif ($exact_or_sub eq 'substring') { 
    my $result = $dbh->prepare( "SELECT * FROM wpa_title WHERE wpa_title ~ '$title' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $matches{$row[0]} = $row[1]; }
  } else { print "ERROR : Must select Exact or Substring<P>\n"; }

  if ( scalar(keys %matches) == 0 ) {
    print "There are no matches for $title.<BR>\n"; }
  else {
    print "There are " . scalar(keys %matches) . " $exact_or_sub matches : <BR>\n";
    foreach my $number (sort keys %matches) { 
      print "Matches <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi?number=$number&action=Number+%21\">wbpaper id $number -> title : $matches{$number}</A><BR>\n";
     }
  }
} # sub pickTitle

sub padZeros {
  my $joinkey = shift;
  if ($joinkey =~ m/^0+/) { $joinkey =~ s/^0+//g; }
  if ($joinkey < 10) { $joinkey = '0000000' . $joinkey; }
  elsif ($joinkey < 100) { $joinkey = '000000' . $joinkey; }
  elsif ($joinkey < 1000) { $joinkey = '00000' . $joinkey; }
  elsif ($joinkey < 10000) { $joinkey = '0000' . $joinkey; }
  elsif ($joinkey < 100000) { $joinkey = '000' . $joinkey; }
  elsif ($joinkey < 1000000) { $joinkey = '00' . $joinkey; }
  elsif ($joinkey < 10000000) { $joinkey = '0' . $joinkey; }
  return $joinkey;
} # sub padZeros

sub displayNormal { my $data = shift; print "  <TD>$data</TD>\n"; }
sub displayType { 
  my $data = shift; 
  if ($type_index{$data}) { $data = $type_index{$data}; }
  print "  <TD>$data</TD>\n"; 
} # sub displayType
sub displayAuthor { 
  my $data = shift; my $aname = '';
  my $result = $dbh->prepare( "SELECT wpa_author_index FROM wpa_author_index WHERE author_id = '$data' ORDER BY wpa_timestamp DESC; ");	# show the most recent one   2007 10 24
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow(); if ($row[0]) { $aname = $row[0]; }
  print "  <TD>$data ($aname)</TD>\n";
} # sub displayAuthor 
sub displayFullAuthor {
  my $joinkey = shift;
  my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE joinkey = '$joinkey' ORDER BY wpa_order;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my %auth_id;
  my %auth_name;
  while (my @row = $result->fetchrow) { $auth_id{$row[1]}++; }
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD ALIGN=CENTER>Affiliation</TD></TR>\n";
  foreach my $auth_id (sort keys %auth_id) {
    my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE author_id = '$auth_id' ORDER BY wpa_timestamp DESC;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row2 = $result2->fetchrow) {
      $auth_name{$auth_id} = $row2[1];
      print "<TR bgcolor='$blue'>\n";
      print "<TD>$row2[1]</TD>";
      if ($row2[2]) { print "<TD>$row2[2]</TD>"; }
        else { print "<TD>&nbsp;</TD>"; }
      print "<TR>\n"; }
  } # foreach my $auth_id (@auth_id)
  print "</TABLE><BR><BR>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD>Possible</TD><TD>Sent</TD><TD>Verified</TD><TD>Verified Timestamp</TD></TR>\n";
  foreach my $auth_id (sort keys %auth_id) {
    my %ceci_hash;
    my $result2 = $dbh->prepare( "SELECT * FROM wpa_author_possible WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{possible} = $row[1]; }
    $result2 = $dbh->prepare( "SELECT * FROM wpa_author_sent WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{sent} = $row[1]; }
    $result2 = $dbh->prepare( "SELECT * FROM wpa_author_verified WHERE author_id = '$auth_id' ORDER BY wpa_timestamp ;" );
    $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result2->fetchrow) { 
      $ceci_hash{$row[2]}{verified} = $row[1]; $ceci_hash{$row[2]}{valid} = $row[3]; 
      if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
      if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
      $ceci_hash{$row[2]}{vtime} = $row[5];  }
    foreach my $join (sort keys %ceci_hash) {
      my $bgcolor = $blue; if ($ceci_hash{$join}{valid} eq 'invalid') { $bgcolor = $red; }
      my $possible = '&nbsp;'; my $sent = '&nbsp;'; my $verified = '&nbsp;'; my $vtime = '&nbsp;';
      if ($ceci_hash{$join}{possible}) { $possible = $ceci_hash{$join}{possible}; }
      if ($ceci_hash{$join}{sent}) { $sent = $ceci_hash{$join}{sent}; }
      if ($ceci_hash{$join}{verified}) { $verified = $ceci_hash{$join}{verified}; }
      if ($ceci_hash{$join}{vtime}) { $vtime = $ceci_hash{$join}{vtime}; }
      print "<TR bgcolor='$bgcolor'>";
      print "<TD>$auth_name{$auth_id}</TD><TD>$possible</TD><TD>$sent</TD><TD>$verified</TD><TD>$vtime</TD>";
      print "<TR>\n";
    }
  } # foreach my $auth_id (@auth_id)
} # sub displayFullAuthor

sub showIgnoreFlag {                # for Cecilia 2008 01 17
  my $joinkey = shift;
#   my $result = $dbh->prepare( "SELECT * FROM cur_comment WHERE joinkey = '$joinkey' AND cur_comment = 'the paper is used for functional annotations';" );
  my $result = $dbh->prepare( "SELECT * FROM wpa_ignore WHERE joinkey = '$joinkey' ORDER BY wpa_timestamp;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my %hash; while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $hash{$row[1]}++; } else { delete $hash{$row[1]}; } }
  foreach my $val (sort keys %hash) { print "<FONT SIZE=+2 COLOR=blue>$val<BR><BR></FONT>\n"; }
} # sub showIgnoreFlag

sub displayOneDataFromKey {
  my $wpa_id = shift;
  my ($joinkey) = &padZeros($wpa_id);
  &showIgnoreFlag($joinkey);

  print "Link to WormBase : <A HREF=http://www.wormbase.org/db/misc/paper?name=WBPaper$joinkey;class=Paper TARGET=new>WBPaper$joinkey</A><BR><BR>\n";

  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD COLSPAN=5>ID : $joinkey</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Data</TD><TD>Order</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  my $counter = 0;
  my $erratum = 0; my $in_book = 0;
  my $result = $dbh->prepare( "SELECT * FROM cfp_curator WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow;
  if ($row[1]) { $row[1] =~ s/two/WBPerson/; print "This paper was first-pass curated by $row[1] on $row[2]<BR>\n"; }
    else { print "This paper has not been first-pass curated.<BR>\n"; }
  
  foreach my $pg_table (@generic_tables) {
    my $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY wpa_order;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my $bgcolor = $blue;
      if ($row[1]) {
        if ($row[3] eq 'invalid') { $bgcolor = $red; }
        if ($row[3] eq 'misattributed') { $bgcolor = $red; }
        print "<TR bgcolor='$bgcolor'>\n  <TD>$pg_table</TD>\n";
        if ($pg_table eq 'wpa_type') { &displayType($row[1]); }
        elsif ($pg_table eq 'wpa_author') { &displayAuthor($row[1]); }
        else { &displayNormal($row[1]); }
        unless ($row[2]) { $row[2] = '&nbsp;'; } print "  <TD>$row[2]</TD>\n";
        print "  <TD>$row[3]</TD>\n";
        print "  <TD>$row[4]</TD>\n";
        if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
        if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
        print "  <TD>$row[5]</TD>\n";
        print "</TR>\n";
        if ($pg_table eq 'wpa_erratum') { $erratum = $row[1]; }
        if ($pg_table eq 'wpa_in_book') { $in_book = $row[1]; }
      } # if ($row[1])
    } # while (my @row = $result->fetchrow)
  } # foreach my $wpa_table (@generic_tables)
  print "</TABLE><BR><BR>\n";
  print "<TABLE border=0 cellspacing=2>\n";
  &displayFullAuthor($joinkey);
  &displayGene($joinkey);
  &getPdfLink($joinkey);

  if ($erratum) { print "<TR><TD>&nbsp;</TD></TR><TR><TD>Erratum : </TD></TR>\n"; &displayOneDataFromKey($erratum); }
  if ($in_book) { print "<TR><TD>&nbsp;</TD></TR><TR><TD>In Book : </TD></TR>\n"; &displayOneDataFromKey($in_book); }
  print "</TABLE><BR><BR>\n";
} # sub displayOneDataFromKey

sub displayGene {
  my ($joinkey) = @_;
  my $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE joinkey = '$joinkey' ORDER BY wpa_gene, wpa_timestamp;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my $row_count = 0;
  my $pg_table = 'wpa_gene';
  print "<TR><TD>&nbsp;</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Gene - CDS</TD><TD>Evidence</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  while (my @row = $result->fetchrow) {
    my $bgcolor = $blue;
    if ($row[1]) {
      if ($row[3] eq 'invalid') { $bgcolor = $red; }
      $row_count++;
      print "<TR bgcolor='$bgcolor'>\n";
      print "<TD>$row[1]</TD>\n";
      if ($row[2]) { print "  <TD>$row[2]</TD>\n"; } else { print "  <TD>&nbsp;</TD>\n"; }
      print "  <TD>$row[3]</TD>\n";
      print "  <TD>$row[4]</TD>\n";
      if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
      if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
      print "  <TD>$row[5]</TD>\n";
      print "</TR>\n";
    }
  } # while (my $row = $result->fetchrow)
} # sub displayGene


sub getPdfLink {
  my $joinkey = shift;
  my $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my $bgcolor = $blue;
  if ($result->fetchrow) {
    print "<TR><TD>&nbsp;</TD></TR>\n";
    print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Link</TD><TD>Type</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
    $result = $dbh->prepare( "SELECT * FROM wpa_electronic_path_type WHERE joinkey = '$joinkey' ;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      my $bgcolor = $blue;
      if ($row[1]) {
        if ($row[3] eq 'invalid') { $bgcolor = $red; }
        print "<TR bgcolor='$bgcolor'>\n  <TD>wpa_electronic_path_type</TD>\n";
        my ($pdf) = $row[1] =~ m/\/([^\/]*)$/;
        $pdf = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
        print "<TD><A HREF=$pdf>$pdf</A></TD>\n";
        print "  <TD>$electronic_type_index{$row[2]}</TD>\n";
        print "  <TD>$row[3]</TD>\n";
        print "  <TD>$row[4]</TD>\n";
        if ($row[5] =~ m/\-\d{2}$/) { $row[5] =~ s/\-\d{2}$//; }
        if ($row[5] =~ m/\..*$/) { $row[5] =~ s/\..*$//; }
        print "  <TD>$row[5]</TD>\n";
        print "</TR>\n";
      }
    } # while (my $row = $result->fetchrow)
  } # if ($result->fetchrow)
} # sub getPdfLink

sub firstPage {
  my $date = &getDate();
  print "Value : $date<BR>\n";
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/wbpaper_display.cgi\">\n";
  print "<TABLE border=1 cellspacing=5>\n";
  print "<TR><TD>Number : <TD><INPUT SIZE=40 NAME=\"number\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Number !\"></TD>\n";
  print "<TD>Enter the wbpaper number for exact match ;  otherwise it will try to match the cgc, pmid, etc. ;  otherwise it will strip the non-number characters and try to match the number.</TR>\n";
  print "<TR><TD>Author : <TD><INPUT SIZE=40 NAME=\"author\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Author !\"></TD>\n";
  print "<TD>Enter an Author and select below whether to find an exact author (e.g. Sternberg PW) or a substring (e.g. Sternberg)</TR>\n";
  print "<TR><TD>Title : <TD><INPUT SIZE=40 NAME=\"title\"></TD>\n";
  print "<TD><INPUT TYPE=submit NAME=action VALUE=\"Title !\"></TD>\n";
  print "<TD>Enter a Title and select below whether to find an exact title (e.g. The pharynx of C. elegans.) or a substring (e.g. pharynx)</TR>\n";
  print "<TR><TD>Exact</TD><TD><INPUT NAME=\"exact_or_sub\" TYPE=\"radio\" VALUE=\"exact\"></TD></TR>\n";
  print "<TR><TD>Substring</TD><TD><INPUT NAME=\"exact_or_sub\" TYPE=\"radio\" VALUE=\"substring\" CHECKED></TD></TR>\n";
  print "</FORM>\n";
  print "</TABLE>\n";
} # sub firstPage

sub populateTypeIndex {
  my $result = $dbh->prepare( "SELECT * FROM wpa_type_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $type_index{$row[0]} = $row[1]; }
  }
  $result = $dbh->prepare( "SELECT * FROM wpa_electronic_type_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $electronic_type_index{$row[0]} = $row[1]; }
  }
} # sub populateTypeIndex





__END__


The Tables
wpa
wpa_identifier
wpa_title
wpa_publisher
wpa_journal
wpa_volume
wpa_pages
wpa_year
wpa_date_published
wpa_fulltext_url
wpa_abstract
wpa_affiliation
wpa_type
wpa_author
wpa_hardcopy
wpa_comments
wpa_editor
wpa_nematode_paper
wpa_contained_in
wpa_contains
wpa_keyword
wpa_erratum
wpa_in_book
wpa_author_possible;
wpa_author_sent;
wpa_author_verified;




wpa_type_index
wpa_author_index
wpa_electronic_type_index
wpa_electronic_path_type
wpa_electronic_path_md5

