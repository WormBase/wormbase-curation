#!/usr/bin/perl -w

# display pap tables's paper data

# The search feature is much more generalized, allowing search on
# any field, and allowing substring matches, as well as case insensitive
# matches (which are substring searches by default).
# 
# Instead of search for a given field, just type in as many different
# fields as you like, with the independent substring / case options, and
# it will search all those things, ranking results with how many matches
# something has.
# 
# So, e.g., searching for year "2001" and author "paul sternb" (case
# insensitive), gives 8 papers with 2 categories matching, and a ton of
# papers that match either "paul sternb" or "2001" below that.
# 
# Typing in anything with a number in the number search will override
# other search parameters and give back that exact paper ID match.
# (padding zeroes for you and excluding non-digit text).
# 
# electronic_path converts to PDF links
# author, gene, and type  show the author name (as well as ID), locus
# name (as well as WBGene), and type name (instead of type index value)
# 
# author information also shows in a separate table the corresponding
# person data, if there's any.
# 
# Toggling on the history display uses the history tables instead of the
# normal tables.  2010 03 01
#
# Cecilia wants no table label, instead order.  wants no curator nor 
# timestamp for ease of copy-pasting.  Moved PDFs to top.  2011 02 04
# 
# Authors were still in table, so put it back the way it was, and have a
# different table row just for author info again.  2011 02 10
#
# Added curation_done for Cecilia.  2011 06 18
#
# If a paper is invalid show what it merged into for Cecilia.  2011 12 22


# sample  http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=00037685



use strict;
use CGI;
use Fcntl;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $query = new CGI;
my $oop;

my $frontpage = 1;
# my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $blue = '#e8f8ff';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color


my %type_index;				# hash of possible 7 types of paper
&populateTypeIndex();	

my @normal_tables = qw( status curation_done type title journal publisher pages volume year month day abstract editor affiliation fulltext_url contained_in identifier remark erratum_in curation_flags author gene );

my %single; my %multi;			# whether tables are single value or multivalue


&populateSingleMultiTableTypes();

# my @generic_tables = qw( title publisher journal volume pages year abstract affiliation comments paper );

# my @generic_tables = qw( wpa wpa_identifier wpa_title wpa_publisher wpa_journal wpa_volume wpa_pages wpa_year wpa_date_published wpa_fulltext_url wpa_abstract wpa_affiliation wpa_type wpa_author wpa_hardcopy wpa_comments wpa_editor wpa_nematode_paper wpa_contained_in wpa_contains wpa_keyword wpa_erratum wpa_in_book );


&printHeader('Paper Display');
&display();
&printFooter();

sub display {
  my $action;

  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); }
  } else { $frontpage = 0; }

  if ($action eq 'Search !') { &search(); }
#   if ($action eq 'Number !') { &pickNumber(); }
#   elsif ($action eq 'Author !') { &pickAuthor(); }
#   elsif ($action eq 'Title !') { &pickTitle(); }
#   else { 1; }
} # sub display

sub displayNumber {
  my ($joinkey, $history) = @_;
  my @aids; my @authors; my %aid_data; my $invalid_flag;
  print "<table border=0>\n";
  print "<tr bgcolor='$blue'><td colspan=5>WBPaper$joinkey</td></tr>\n";
  foreach my $table ("electronic_path", @normal_tables ) {
    my $pg_table = 'pap_' . $table; if ($history eq 'on') { $pg_table = 'h_pap_' . $table; }
#     print "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY pap_order<br />\n" ;
    $result = $dbh->prepare( "SELECT * FROM $pg_table WHERE joinkey = '$joinkey' ORDER BY pap_order" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      $row[0] = $table;
      if ($table eq 'type') { $row[1] = $type_index{$row[1]}; }
        elsif ($table eq 'status') { $invalid_flag = $row[1]; }
        elsif ($table eq 'electronic_path') {
          my ($pdf) = $row[1] =~ m/\/([^\/]*)$/;
          $pdf = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
          $row[1] = "<a href=\"$pdf\">$pdf</a>\n"; }
        elsif ($table eq 'gene') { 
          my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[1]'" );
          $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
          my @row2 = $result2->fetchrow();
          $row[1] = "WBGene$row[1] ($row2[1])"; }
        elsif ($table eq 'author') { 
          push @aids, $row[1];
          my $result2 = $dbh->prepare( "SELECT * FROM pap_author_index WHERE author_id = '$row[1]'" );
          $result2->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
          my @row2 = $result2->fetchrow();
          $aid_data{$row[1]}{index} = $row2[1]; $row[1] .= " ($row2[1])"; 
          push @authors, $row[1];
#           $row[0] = $row[2]; $row[2] = ''; $row[3] = ''; $row[4] = '';	# Cecilia wants no table label, instead order.  wants no curator nor timestamp for ease of copy-pasting  2011 02 04
        }
      my @data; foreach (@row) { if ($_) { push @data, $_; } else { push @data, ""; } }		# some data is undefined
      my $data = join"</td><td>", @data;
      print "<tr bgcolor='$blue'><td>$data</td></tr>\n";
    } # while (my @row = $result->fetchrow)
  } # foreach my $table (@normal_tables, "electronic_path")
  my $authors = join"<br />", @authors;
  print "<tr><td>authors again</td><td>$authors</td></tr>\n";	# for Cecilia to copy-paste
  print "</table><br />";
  if ($invalid_flag) { if ($invalid_flag eq 'invalid') {	# if a paper is invalid show what it merged into for Cecilia  2011 12 22
    my @merged_into;
    $result = $dbh->prepare( "SELECT DISTINCT(joinkey) FROM pap_identifier WHERE pap_identifier = '$joinkey' ORDER BY joinkey" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { push @merged_into, $row[0]; }
    my $merged_into = ' no papers have acquired a merged for this paper in pap_identifier';
    if (scalar @merged_into > 0) { 
      for my $i (0 .. $#merged_into) { 
        $merged_into[$i] = "<a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+%21&data_number=$merged_into[$i]&history=off\">WBPaper$merged_into[$i]</a>"; }
      $merged_into = join", ", @merged_into; $merged_into = ' merged into ' . $merged_into; }
    print "invalid, $merged_into<br />"; } }

  print "<table border=0>\n";
  my @aut_tables = qw( possible sent verified );
  my $aids = join"', '", @aids;
  foreach my $table (@aut_tables) {
#     print "SELECT * FROM pap_author_$table WHERE author_id IN ('$aids');<br />\n";
    $result = $dbh->prepare( "SELECT * FROM pap_author_$table WHERE author_id IN ('$aids');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { 
      $aid_data{$row[0]}{join}{$row[2]}{$table}{time} = $row[4]; 
      $aid_data{$row[0]}{join}{$row[2]}{$table}{data} = $row[1]; }
  } # foreach my $table (@aut_tables)
  print "<tr bgcolor='$blue'><td>aid</td><td>author</td><td>join</td><td>possible</td><td>pos_time</td><td>sent</td><td>verified</td><td>ver_time</td></tr>\n";
  foreach my $aid (@aids) {
    foreach my $join (sort {$a<=>$b} keys %{ $aid_data{$aid}{join} } ) {
      my $author = ''; my $possible = ''; my $pos_time = ''; my $sent = ''; my $verified = ''; my $ver_time = '';
      if ($aid_data{$aid}{index}) { $author = $aid_data{$aid}{index}; }
      if ($aid_data{$aid}{join}{$join}{possible}{data}) { $possible = $aid_data{$aid}{join}{$join}{possible}{data}; }
      if ($aid_data{$aid}{join}{$join}{possible}{time}) { $pos_time = $aid_data{$aid}{join}{$join}{possible}{time}; }
      if ($aid_data{$aid}{join}{$join}{sent}{data}) { $sent = $aid_data{$aid}{join}{$join}{sent}{data}; }
      if ($aid_data{$aid}{join}{$join}{verified}{data}) { $verified = $aid_data{$aid}{join}{$join}{verified}{data}; }
      if ($aid_data{$aid}{join}{$join}{verified}{time}) { $ver_time = $aid_data{$aid}{join}{$join}{verified}{time}; }
      print "<tr bgcolor='$blue'><td>$aid</td><td>$author</td><td>$join</td><td>$possible</td><td>$pos_time</td><td>$sent</td><td>$verified</td><td>$ver_time</td></tr>\n";
    } # foreach my $order (sort {$a<=>$b} keys %{ $aid_data{$aid}{order} } )
  } # foreach my $aid (@aids)
  print "</table>\n";
} # sub displayNumber

sub search {
  my $history = 'off';
  ($oop, my $temp_history) = &getHtmlVar($query, "history");
  if ($temp_history) { $history = $temp_history; }
  print "History display $history E<br />\n"; 

  ($oop, my $number) = &getHtmlVar($query, "data_number");
  if ($number) { 
    if ($number =~ m/(\d+)/) { &displayNumber(&padZeros($1), $history); return; }
      else { print "Not a number in a number search for $number<br />\n"; } }



  my %hash;
  foreach my $table (@normal_tables) {
    ($oop, my $data) = &getHtmlVar($query, "data_$table");
    next unless ($data);	# skip those with search params
    ($oop, my $substring) = &getHtmlVar($query, "substring_$table");
    ($oop, my $case) = &getHtmlVar($query, "case_$table");
    my $operator = '=';
    if ($case eq 'on') { $operator = '~*'; }
    elsif ($substring eq 'on') { $operator = '~'; }
    if ($table eq 'author') {
#       print "SELECT joinkey, pap_author FROM pap_author WHERE pap_author IN (SELECT author_id FROM pap_author_index WHERE pap_author_index $operator '$data')<br />\n";
      print "SELECT pap_author.joinkey, pap_author.pap_author, pap_author_index.pap_author_index FROM pap_author, pap_author_index WHERE pap_author.pap_author = pap_author_index.author_id AND pap_author_index $operator '$data'<br />\n";
      $result = $dbh->prepare( "SELECT pap_author.joinkey, pap_author.pap_author, pap_author_index.pap_author_index FROM pap_author, pap_author_index WHERE pap_author.pap_author = pap_author_index.author_id AND pap_author_index $operator '$data'" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) { 
        $hash{matches}{$row[0]}++; 
        $hash{table}{$table}{$row[0]} = "$row[1] ($row[2])"; } }
    else {
      print "SELECT joinkey, pap_$table FROM pap_$table WHERE pap_$table $operator '$data'<br />\n";
      $result = $dbh->prepare( "SELECT joinkey, pap_$table FROM pap_$table WHERE pap_$table $operator '$data'" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) { 
        $hash{matches}{$row[0]}++; 
        $hash{table}{$table}{$row[0]} = $row[1]; } }
  }

  my %titles;
  my $joinkeys = join"', '", keys %{ $hash{matches} };
  $result = $dbh->prepare( "SELECT * FROM pap_title WHERE joinkey IN ('$joinkeys')" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $titles{$row[0]} = $row[1]; }

  my %matches; 
  foreach my $joinkey (keys %{ $hash{matches} }) {
    my $count = $hash{matches}{$joinkey}; $matches{$count}{$joinkey}++; }
  foreach my $count (reverse sort {$a<=>$b} keys %matches) {
    print "<br />Matches $count<br />\n";
    foreach my $joinkey (sort {$a<=>$b} keys %{ $matches{$count} }) {
      print "<a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+%21&data_number=$joinkey&history=$history\">WBPaper$joinkey</a> $titles{$joinkey} \n";
      foreach my $table (keys %{ $hash{table} }) {
        next unless $hash{table}{$table}{$joinkey};
        my $data_match = $hash{table}{$table}{$joinkey}; 
        if ($table eq 'type') { $data_match = $type_index{$data_match}; }
        print "$table : <font color=\"green\">$data_match</font>\n"; }
      print "<br />\n";
    } # foreach my $joinkey (sort {$a<=>$b} keys %{ $matches{$count} })
  }
} # sub search

sub firstPage {
  my $date = &getDate();
  print "Value : $date<BR>\n";
  print "<form name='form1' method=\"post\" action=\"paper_display.cgi\">\n";
  print "<table border=0 cellspacing=5>\n";
  print "<tr>\n";
  print "<td><input type=submit name=action value=\"Search !\"></td>\n";
  print "<td><input type=\"checkbox\" name=\"history\" value=\"on\">display history (not search history)</td>\n";
  print "</tr>\n";
  foreach my $table ("number", @normal_tables) { 
    my $style = ''; 
    if ( ($table eq 'number') || ($table eq 'status') || ($table eq 'type') ) { $style = 'display: none'; }
    print "<tr><td>$table</td>";
    if ( $table eq 'type' ) {					# for type show dropdown instead of text input
        print "<td><select name=\"data_$table\">\n";
        print "<option value=\"\"></option>\n";
        foreach my $value (sort {$a<=>$b} keys %type_index) {
          print "<option value=\"$value\">$type_index{$value}</option>\n"; }
        print "</select></td>"; }
      else { print "<td><input size=40 name=\"data_$table\"></td>\n"; }	# normal tables have input
    
    print "<td style='$style'><input type=\"checkbox\" value=\"on\" name=\"substring_$table\">substring</td>\n";
    print "<td style='$style'><input type=\"checkbox\" value=\"on\" name=\"case_$table\">case insensitive (automatic substring)</td></tr>\n";
  }
  print "</table>\n";
  print "</form>\n";
} # sub firstPage

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


sub populateTypeIndex {
  my $result = $dbh->prepare( "SELECT * FROM pap_type_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $type_index{$row[0]} = $row[1]; }
  }
#   $result = $dbh->prepare( "SELECT * FROM pap_electronic_type_index;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[0]) { $electronic_type_index{$row[0]} = $row[1]; }
#   }
} # sub populateTypeIndex

sub populateSingleMultiTableTypes {
# unique (single value) tables :  status title journal publisher pages volume year month day pubmed_final primary_data abstract );
  $single{'status'}++;
  $single{'title'}++;
  $single{'journal'}++;
  $single{'publisher'}++;
  $single{'volume'}++;
  $single{'pages'}++;
  $single{'year'}++;
  $single{'month'}++;
  $single{'day'}++;
  $single{'pubmed_final'}++;
  $single{'primary_data'}++;
  $single{'abstract'}++;
  
  # multivalue tables :  editor type author affiliation fulltext_url contained_in gene identifier ignore remark erratum_in internal_comment curation_flags 
  
  $multi{'editor'}++;
  $multi{'type'}++;
  $multi{'author'}++;
  $multi{'affiliation'}++;
  $multi{'fulltext_url'}++;
  $multi{'contained_in'}++;
  $multi{'gene'}++;
  $multi{'identifier'}++;
  $multi{'ignore'}++;
  $multi{'remark'}++;
  $multi{'erratum_in'}++;
  $multi{'internal_comment'}++;
  $multi{'curation_flags'}++;
  $multi{'electronic_path'}++;
  $multi{'author_possible'}++;
  $multi{'author_sent'}++;
  $multi{'author_verified'}++;
} # sub populateSingleMultiTableTypes


__END__

use strict;
use diagnostics;
use DBI;
use Jex;		# filter for Pg

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";



my %tableToTag;
$tableToTag{title}	= 'Title';
$tableToTag{type}	= 'Type';
$tableToTag{journal}	= 'Journal';
$tableToTag{publisher}	= 'Publisher';
$tableToTag{pages}	= 'Page';
$tableToTag{volume}	= 'Volume';
$tableToTag{year}	= 'Publication_date';
$tableToTag{abstract}	= 'Abstract';
$tableToTag{editor}	= 'Editor';
$tableToTag{affiliation}	= 'Affiliation';
$tableToTag{fulltext_url}	= 'URL';
$tableToTag{contained_in}	= 'Contained_in';
$tableToTag{identifier}	= 'Name';
$tableToTag{remark}	= 'Remark';
$tableToTag{erratum_in}	= 'Erratum_in';
$tableToTag{gene}	= 'Gene';
$tableToTag{author}	= 'Author';
$tableToTag{curation_flags}	= 'Curation_pipeline';

my @normal_tables = qw( status type title journal publisher pages volume year month day abstract editor affiliation fulltext_url contained_in identifier remark erratum_in curation_flags author gene );

my %indices;
$result = $dbh->prepare( "SELECT * FROM pap_type_index");	
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $indices{type}{$row[0]} = $row[1]; }

$result = $dbh->prepare( "SELECT * FROM pap_author_index");	
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { $indices{author}{$row[0]} = $row[1]; }

$result = $dbh->prepare( "SELECT pap_author_verified.author_id, pap_author_possible.pap_author_possible, pap_author_verified.pap_author_verified FROM pap_author_verified, pap_author_possible WHERE pap_author_verified.pap_author_verified ~ 'YES' AND pap_author_possible.pap_author_possible ~ 'two' AND pap_author_verified.author_id = pap_author_possible.author_id AND pap_author_verified.pap_join = pap_author_possible.pap_join;");
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) { 
  $row[1] =~ s/two/WBPerson/;
  $indices{person}{$row[0]} = $row[1]; }

my %hash; 
foreach my $table (@normal_tables) {
  $result = $dbh->prepare( "SELECT * FROM pap_$table");	
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    unless ($row[2]) { $row[2] = 'NULL'; }
    if ($table eq 'type') { $hash{$table}{$row[0]}{$row[2]}{curator} = $row[3]; }
    elsif ($table eq 'gene') { $hash{$table}{$row[0]}{$row[2]}{evi} = $row[5]; }
    $hash{$table}{$row[0]}{$row[2]}{data} = $row[1]; }
}


my $abstracts;

foreach my $joinkey (sort keys %{ $hash{status} }) {
  next if ($joinkey eq '00000001');
  print "\nPaper : \"WBPaper$joinkey\"\n";
  print "Status\t\"" . ucfirst($hash{status}{$joinkey}{NULL}{data}) . "\"\n";
  next if ($hash{status}{$joinkey}{NULL}{data} ne 'valid');
  foreach my $table (@normal_tables) {
    next if ($table eq 'status');
    next if ($table eq 'month');
    next if ($table eq 'day');
    foreach my $order (sort keys %{ $hash{$table}{$joinkey} }) {
      my $tag = $tableToTag{$table};
      my $data = $hash{$table}{$joinkey}{$order}{data};
      ($data) = &filterAce($data);	# filter here, future changes will have doublequotes and what not that shouldn't be escaped
      if ($table eq 'year') { 
        if ($hash{month}{$joinkey}{NULL}{data}) { 
          my $month = $hash{month}{$joinkey}{NULL}{data};
          if ($month < 10) { $month = "0$month"; }
          $data .= "-$month"; }
        if ($hash{day}{$joinkey}{NULL}{data}) { 
          my $day = $hash{day}{$joinkey}{NULL}{data};
          if ($day < 10) { $day = "0$day"; }
          $data .= "-$day"; }
      }
      elsif ($table eq 'identifier') {  
        if ($data =~ m/^\d{8}$/) { $tag = 'Acquires_merge'; $data = "WBPaper$data"; }
        elsif ($data =~ m/^pmid(\d+)$/) { $tag = "Database\t\"MEDLINE\"\t\"PMID\""; $data = $1; }
      }
      elsif ($table eq 'abstract') {  
        $abstracts .= "Longtext : \"WBPaper$joinkey\"\n\n$data\n\n***LongTextEnd***\n\n\n";
        $data = "WBPaper$joinkey";
      }
      elsif ($table eq 'author') {  
        my $aid = $data;
        next unless ($indices{author}{$aid});		# must have an author
        next unless ($indices{author}{$aid} =~ m/\S/);	# author must have a word in it
unless ($indices{author}{$aid}) { print "ERROR author_id missing $aid in paper WBPaper$joinkey\n"; }
        if ($indices{person}{$aid}) { $data = "$indices{author}{$aid}\"\tPerson\t\"$indices{person}{$aid}"; }
          else { $data = $indices{author}{$aid}; }
      }
      elsif ($table eq 'erratum_in') {  
        $data = 'WBPaper'. $data; 
      }
      elsif ($table eq 'gene') {  
        $data = 'WBGene'. $data;
        if ($hash{$table}{$joinkey}{$order}{evi}) {		# if there's evidence column
          my $evi = $hash{$table}{$joinkey}{$order}{evi};
          unless ($evi =~ m/Manually_connected/) {		# skip evidence for Manually_connected tag not in acedb
            $evi =~ s/\"$//;					# strip out last doublequote for print below
            $data .= "\"\t$evi"; } }				# append closing quote, tab, evi
      }
      elsif ($table eq 'type') {  
        my $curator = $hash{$table}{$joinkey}{$order}{curator};
        $curator =~ s/two/WBPerson/;
        $data = "$indices{type}{$data}\"\tPerson_evidence\t\"$curator";
      }
      elsif ($table eq 'curation_flags') {  
        next unless ($data eq 'Phenotype2GO');
      }
# unless ($data) { print "ERROR NO DATA $tag $joinkey\n"; }
      if ($data) {
        print "$tag\t\"$data\"\n";
      }
    } # foreach my $order (sort keys %{ $hash{$table}{$joinkey} })
  } # foreach my $table (@normal_tables)
  my ($author, $year, $journal, $title);
  if ($hash{author}{$joinkey}{1}{data}) { 
    if ($indices{author}{$hash{author}{$joinkey}{1}{data}}) { 
      $author = $indices{author}{$hash{author}{$joinkey}{1}{data}}; } 
    if ($hash{author}{$joinkey}{2}{data}) { $author .= " et al."; }
  }
  if ($hash{year}{$joinkey}{NULL}{data}) { $year = $hash{year}{$joinkey}{NULL}{data}; }
  if ($hash{journal}{$joinkey}{NULL}{data}) { $journal = $hash{journal}{$joinkey}{NULL}{data}; }
  if ($hash{title}{$joinkey}{NULL}{data}) { $title = $hash{title}{$joinkey}{NULL}{data}; }
  my ($brief_citation) = &getEimearBriefCitation( $author, $year, $journal, $title );
  if ($brief_citation) { print "Brief_citation\t\"$brief_citation\"\n"; }

} # foreach my $joinkey (sort keys %{ $hash{status} })

print "\n\n$abstracts";

  

# special stuff :
# author author_index


# SELECT wpa_author_verified.author_id, wpa_author_possible.wpa_author_possible, wpa_author_verified.wpa_author_verified FROM wpa_author_verified, wpa_author_possible WHERE wpa_author_verified.wpa_author_verified ~ 'YES' AND wpa_author_possible.wpa_author_possible ~ 'two' AND wpa_author_verified.author_id = wpa_author_possible.author_id AND wpa_author_verified.wpa_join = wpa_author_possible.wpa_join;

# special tables :
# gene -> need evidence : joinkey, gene, order, curator, timestamp, evidence
# electronic_path -> from electronic_path_type, which has wpa_type instead of order
# author_index -> author_id instead of joinkey
# author_possible -> author_id instead of joinkey
# author_sent -> author_id instead of joinkey
# author_verified -> author_id instead of joinkey
# type_index -> index, type_id instead of joinkey


sub getEimearBriefCitation {
  my ($author, $year, $journal, $title) = @_;
  my $brief_citation = '';
  my $brief_title = '';                     # brief title (70 chars or less)
  if ($title) {
    $title =~ s/"//g;			# some titles properly have doublequotes but don't want them in brief citation
    my @chars = split //, $title;
    if ( scalar(@chars) < 70 ) {
        $brief_title = $title;
    } else {
        my $i = 0;                            # letter counter (want less than 70)
        my $word = '';                        # word to tack on (start empty, add characters)
        while ( (scalar(@chars) > 0) && ($i < 70) ) { # while there's characters, and less than 70 been read
            $brief_title .= $word;            # add the word, because still good (first time empty)
            $word = '';                       # clear word for next time new word is used
            my $char = shift @chars;          # read a character to start / restart check
            while ( (scalar(@chars) > 0) && ($char ne ' ') ) {        # while not a space and still chars
                $word .= $char; $i++;         # build word, add to counter (less than 70)
                $char = shift @chars;         # read a character to check if space
            } # while ($_ ne '')              # if it's a space, exit loop
            $word .= ' ';                     # add a space at the end of the word
        } # while ( (scalar(@chars) > 0) && ($i < 70) )
        $brief_title = $brief_title . "....";
    } }
  if ($author) { if ( length($author) > 0) { $brief_citation .= $author; } }
  if ($year) { 
    if ($year =~ m/ -C .*$/) { $year =~ s/ -C .*$//g; }
    if ( length($year) > 0) { $brief_citation .= " ($year)"; } }
  if ($journal) { 
    $journal =~ s/"//g;			# some journals are messed up and have doublequotes
    if ( length($journal) > 0) { $brief_citation .= " $journal"; } }
  if ($brief_title) { if ( length($brief_title) > 0) { $brief_citation .= " \\\"$brief_title\\\""; } }
  if ($brief_citation) { return $brief_citation; }
} # sub getEimearBriefCitation


sub filterAce {
  my $identifier = shift;
  my $comment = '';
  if ($identifier =~ m/-COMMENT (.*)/) { $comment = $1; $identifier =~ s/-COMMENT .*//; }
  if ($identifier =~ m/HTTP:\/\//i) { $identifier =~ s/HTTP:\/\//PLACEHOLDERASDF/ig; }
  if ($identifier =~ m/\//) { $identifier =~ s/\//\\\//g; }
  if ($identifier =~ m/\"/) { $identifier =~ s/\"/\\\"/g; }
#   if ($identifier =~ m/\\\/\\\//) { $identifier =~ s/\\\/\\\//" "/g; }	# convert // into " " for old pages / volume
  if ($identifier =~ m/\s+$/) { $identifier =~ s/\s+$//; }
  if ($identifier =~ m/PLACEHOLDERASDF/) { $identifier =~ s/PLACEHOLDERASDF/HTTP:\\\/\\\//g; }
  if ($identifier =~ m/;/) { $identifier =~ s/;/\\;/g; }
  if ($identifier =~ m/%/) { $identifier =~ s/%/\\%/g; }
  if ($comment) {
    if ($identifier =~ m/[^"]$/) { $identifier .= "\" "; }
    $identifier .= "-C \"$comment"; }
  return $identifier;
} # sub filterAce


__END__

my %primary_data;		# primary data or not
$primary_data{1} = 'primary';		# Journal_article
$primary_data{11} = 'primary';		# Letter
$primary_data{14} = 'primary';		# Published_erratum
$primary_data{2} = 'not_primary';	# Review
$primary_data{5} = 'not_primary';	# Book_chatper
$primary_data{6} = 'not_primary';	# News
$primary_data{8} = 'not_primary';	# Book
$primary_data{9} = 'not_primary';	# Historical_article
$primary_data{10} = 'not_primary';	# Comment
$primary_data{12} = 'not_primary';	# Monograph
$primary_data{13} = 'not_primary';	# Editorial
$primary_data{15} = 'not_primary';	# Retracted_publication
$primary_data{16} = 'not_primary';	# Technical_report
$primary_data{18} = 'not_primary';	# WormBook
$primary_data{19} = 'not_primary';	# Interview
$primary_data{20} = 'not_primary';	# Lectures
$primary_data{21} = 'not_primary';	# Congresses
$primary_data{22} = 'not_primary';	# Interactive_tutorial
$primary_data{23} = 'not_primary';	# Biography
$primary_data{24} = 'not_primary';	# Directory
$primary_data{3} = 'not_designated';	# Meeting_abstract
$primary_data{4} = 'not_designated';	# Gazette_article
$primary_data{7} = 'not_designated';	# Email
$primary_data{17} = 'not_designated';	# Other


# non-xml to copy over :  abstract  affiliation  author  a/i a/p a/s a/v  contained_in/contains  editor  electronic_path_type -> electronic_path   fulltext_url  gene  identifier  ignore  publisher  remark   rnai_int_done/rnai_curation/transgene_curation/allele_curation -> curation_flags  status
# unless-xml to copy over :  journal  pages  title  volume  year  type  primary_data (based on type)
# ``manual'' add erratum_in/erratum_for


# special tables :
# gene -> need evidence : joinkey, gene, order, curator, timestamp, evidence
# electronic_path -> from electronic_path_type, which has wpa_type instead of order
# author_index -> author_id instead of joinkey
# author_possible -> author_id instead of joinkey
# author_sent -> author_id instead of joinkey
# author_verified -> author_id instead of joinkey
# type_index -> index, type_id instead of joinkey

# author_index author_possible author_sent author_verified electronic_path gene type_index

my @pap_tables = qw( abstract affiliation author contained_in editor fulltext_url identifier ignore journal pages publisher pubmed_final remark title type volume year month day erratum_in internal_comment curation_flags primary_data status );


# &populateStatusIdentifier();

my %idents;
my %all_ids;
$result = $dbh->prepare( "SELECT * FROM pap_identifier" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
while (my @row = $result->fetchrow) {
  $all_ids{$row[0]}{$row[1]}++;
  if ($row[1] =~ m/pmid(\d+)/) { $idents{$1} = $row[0]; }
}


# &populateFromXml();		# populate paper data from pubmed xml
# &populateUnlessXml();		# populate data from wpa for fields that would be gotten from xml
# &populateExtraTypes();	# only run after populateFromXml + populateUnlessXML, populate manual Kimberly data for Type information that is not in XML / unlessXml
# &populateNonXml();		# populate data from wpa for fields that do not exist in xml (and are not special tables)
# &populateAuthorSub();		# populate author index/possible/sent/verified data (special tables)
# &populateGene();		# populate gene data (special table)
# &populateCurationFlags();	# populate curation flags (special table) from rnai_curation / rnai_int_done / p2go
# &populateElectronicPath();	# populate electronic path data (special table)
# &checkAffiliationWrong();	# some affiliation stuff wasn't getting in because of non-utf8 characters
# &getOddJournals();		# not necessary, for Kimberly to extract odd journals
# &populateTypeIndex();		# only run once, to populate type index
# &populateErratum();		# only run once, populate erratum_in table from manual stuff

sub populateCurationFlags {
  my @curation_flags = qw( rnai_int_done rnai_curation );
  
  $result = $dbh->do( "DELETE FROM h_pap_curation_flags" );
  $result = $dbh->do( "DELETE FROM pap_curation_flags" );

  my %hash; my %data;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'");	
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  foreach my $type (@curation_flags) {
    $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );	# in order to store latest timestamp (up to gary what we store ?)
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);	# these two tables are always valid, and data order is always null
      $data{$row[0]}{$type}{curator} = $row[4];
      $data{$row[0]}{$type}{timestamp} = $row[5]; } }

  $data{"00004402"}{"phenotype2GO"}{"curator"} = "two1843";	# manual ranjana / kimberly data
  $data{"00004403"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00004540"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00004651"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00004769"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00005599"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00005654"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00006395"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00024497"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00024925"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00025054"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00026763"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00005736"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00026593"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00028783"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00029254"}{"phenotype2GO"}{"curator"} = "two1843";
  $data{"00030951"}{"phenotype2GO"}{"curator"} = "two1843";

  my @data_types = qw( rnai_curation rnai_int_done phenotype2GO );
  foreach my $joinkey (sort keys %{ $hash{status} }) {
    my $order = 0;
    foreach my $type (@data_types) {
      next unless ($data{$joinkey}{$type}{curator});
      $order++;
      my $curator = $data{$joinkey}{$type}{curator};
      my $timestamp = 'CURRENT_TIMESTAMP';
      if ($data{$joinkey}{$type}{timestamp}) {
        $timestamp = "'$data{$joinkey}{$type}{timestamp}'"; }

#       print "$joinkey\t$type\t$order\t$curator\t$timestamp\n";
      $result = $dbh->do( "INSERT INTO pap_curation_flags VALUES ('$joinkey', '$type', $order, '$curator', $timestamp)" );
      $result = $dbh->do( "INSERT INTO h_pap_curation_flags VALUES ('$joinkey', '$type', $order, '$curator', $timestamp)" );
    }
  } # foreach my $type (@curation_flags)
} # sub populateCurationFlags


sub populateAuthorSub {		# populate author index/possible/sent/verified data (special tables)
  my @subtables = qw( index possible sent verified );

  my %hash;

  foreach my $type (@subtables) {
    $result = $dbh->do( "DROP TABLE h_pap_author_$type" );
    $result = $dbh->do( "DROP TABLE pap_author_$type" );

    my $papt = 'pap_author_' . $type;
    $result = $dbh->do( "CREATE TABLE $papt ( author_id text, $papt text, pap_join integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
    $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (author_id);" );
    $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
    $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );
    
    $result = $dbh->do( "CREATE TABLE h_$papt ( author_id text, $papt text, pap_join integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
    $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON $papt USING btree (author_id);" );
    $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
    $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );

    $result = $dbh->prepare( "SELECT * FROM wpa_author_$type ORDER BY wpa_timestamp" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);
      unless ($row[2]) { $row[2] = 'NULL'; }
      if ($type eq 'index') { $row[2] = 'NULL'; }
      if ($row[3] eq 'valid') { 
          $hash{$row[0]}{$row[2]}{$type}{$row[1]}{data} = $row[1];
          if ($row[4]) { $hash{$row[0]}{$row[2]}{$type}{$row[1]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$row[0]}{$row[2]}{$type}{$row[1]}{timestamp} = $row[5]; } }
        else { 
          delete $hash{$row[0]}{$row[2]}{$type}{$row[1]}; } }
  }

# print "T $type\n";
  foreach my $author_id (sort keys %hash) {
# int "AID $author_id\n";
    my $count = 0;
    foreach my $join (sort keys %{ $hash{$author_id} }) {
# int "JOIN $join\n";
      my $order = 'NULL';
      if ($join ne 'NULL') { $count++; $order = "'$count'"; }
      foreach my $type (sort keys %{ $hash{$author_id}{$join} }) {
        my $papt = 'pap_author_' . $type;
        my %tempHash;			# a given aid + join will sometimes have multiple data, so only store the latest one by storing by timestamp and getting reverse keys sort
# my @data = keys %{ $hash{$author_id}{$join}{$type} };
# if (scalar(@data) > 1) { print "ERR " . scalar(@data) . " for $author_id $order $type\n"; }
        foreach my $data (sort keys %{ $hash{$author_id}{$join}{$type} }) {
          next unless $data;
          my $curator = $hash{$author_id}{$join}{$type}{$data}{curator};
          my $timestamp = $hash{$author_id}{$join}{$type}{$data}{timestamp};
          my $time = $timestamp; $time =~ s/\D//g; 
          ($data) = &filterForPg($data);
          unless ($curator) { 
            print "NO CURATOR $author_id T $type D $data\n"; 
            $curator = 'two1841'; }
          unless ($timestamp) { 
            print "NO TIMESTAMP $author_id T $type D $data\n"; }
          $tempHash{$timestamp}{curator} = $curator;
          $tempHash{$timestamp}{data} = $data;
#           print "DATA\t$type\t$author_id\t$data\t$order\t$curator\t$timestamp\n";
          $result = $dbh->do( "INSERT INTO h_$papt VALUES ('$author_id', '$data', $order, '$curator', '$timestamp')" );		# enter all (valid) data to history
        }
        foreach my $timestamp (reverse sort keys %tempHash) {	# get the most recent timestamp off of reverse alpha sort
          my $curator = $tempHash{$timestamp}{curator};
          my $data = $tempHash{$timestamp}{data};
#           print "FINAL\t$type\t$author_id\t$data\t$order\t$curator\t$timestamp\n";
          $result = $dbh->do( "INSERT INTO $papt VALUES ('$author_id', '$data', $order, '$curator', '$timestamp')" );			# enter most recent data to current field
          last;				# only get the latest value, so skip all others
        }
  } } } 
} # sub populateAuthorSub

sub populateGene {		# put locus in evidence column "Inferred_manually"
  $result = $dbh->do( "DROP TABLE h_pap_gene" );
  $result = $dbh->do( "DROP TABLE pap_gene" );

  my $papt = 'pap_gene';
  $result = $dbh->do( "CREATE TABLE $papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone , pap_evidence text)" ); 
  $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );
  
  $result = $dbh->do( "CREATE TABLE h_$papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone , pap_evidence text)" ); 
  $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON h_$papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  my $type = 'gene';
  $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    next unless ($row[1]);
    unless ($row[2]) { $row[2] = 'NULL'; }
    my $key = "$row[1]KEY$row[2]";
    if ($row[3] eq 'valid') { 
        $hash{$type}{$row[0]}{$key}{data} = $row[1];
        if ($row[4]) { $hash{$type}{$row[0]}{$key}{curator} = $row[4]; }
        if ($row[5]) { $hash{$type}{$row[0]}{$key}{timestamp} = $row[5]; } }
      else { 
        delete $hash{$type}{$row[0]}{$key}; } }

  my %stuff; 				# use this hash to filter new Manually_connected evidence to store locus where it wasn't Inferred_automatically (instead of in the gene column)
  foreach my $joinkey (sort keys %{ $hash{status} }) {
    foreach my $key (sort keys %{ $hash{$type}{$joinkey} }) {
      my ($genedata, $evi) = split/KEY/, $key;
      my ($geneid) = $genedata =~ m/WBGene(\d+)/;
      next unless ($geneid); 		# there's 3 entries without any data
      my $locus = '';
      if ($genedata =~ m/\(([^\(\)]*?)\)/) {	# if there's a locus (innermost stuff in parenthesis)
        $locus = $1; 
# print "J $joinkey KEY $key G $geneid L $locus E $evi C $hash{$type}{$joinkey}{$key}{curator} T $hash{$type}{$joinkey}{$key}{timestamp} E\n";
        if ($evi =~ m/$locus/) { 		# the locus mentioned in evidence, stays the same
            $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
            $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
          else { # if ($evi =~ m/$locus/)	# locus not in evidence
            if ($evi =~ m/Inferred_automatically\t\"(.*?)\"/) {	# if inferred automatically, add to evidence
                $evi = "Inferred_automatically\t\"$locus $1\"";
                $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
                $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
              else { 				# not inferred automatically, store it
                $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
                $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp};
                $evi = "Manually_connected\t\"$locus\""; 		# and also add manual
                $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
                $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
        } # else # if ($evi =~ m/$locus/)	
      } # if ($genedata =~ m/\((.*?)\)/)
      else {	# if there is no locus, store the entry
        $stuff{$joinkey}{$geneid}{$evi}{curator} = $hash{$type}{$joinkey}{$key}{curator};
        $stuff{$joinkey}{$geneid}{$evi}{timestamp} = $hash{$type}{$joinkey}{$key}{timestamp}; }
    } # foreach my $gene_data (sort keys %{ $hash{$type}{$joinkey} })
  } # foreach my $joinkey (sort keys %{ $hash{status} })

  foreach my $joinkey (sort keys %stuff) {
    my $count = 0;
    foreach my $geneid (sort keys %{ $stuff{$joinkey} }) {
      foreach my $evi (sort keys %{ $stuff{$joinkey}{$geneid} }) {
        $count++; my $order = "'$count'";
        my $curator = $stuff{$joinkey}{$geneid}{$evi}{curator};
        my $timestamp = $stuff{$joinkey}{$geneid}{$evi}{timestamp};
        if ($evi ne 'NULL') { $evi = "'$evi'"; }
#         print "GENE\t$joinkey\t$geneid\t$order\t$curator\t$timestamp\t$evi\n";
        $result = $dbh->do( "INSERT INTO pap_gene VALUES ('$joinkey', '$geneid', $order, '$curator', '$timestamp', $evi)" );
        $result = $dbh->do( "INSERT INTO h_pap_gene VALUES ('$joinkey', '$geneid', $order, '$curator', '$timestamp', $evi)" );
      } # foreach my $evi (sort keys %{ $stuff{$joinkey}{$geneid} })
    } # foreach my $geneid (sort keys %{ $stuff{$joinkey} })
  } # foreach my $joinkey (sort keys %stuff)
} # sub populateGene


sub populateElectronicPath {		# should we split locus into another column, strip, or leave as is ?
  $result = $dbh->do( "DROP TABLE h_pap_electronic_path" );
  $result = $dbh->do( "DROP TABLE pap_electronic_path" );

  my $papt = 'pap_electronic_path';
  $result = $dbh->do( "CREATE TABLE $papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
  $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );
  
  $result = $dbh->do( "CREATE TABLE h_$papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone)" ); 
  $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON h_$papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  my $type = 'electronic_path_type';
  $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    next unless ($row[1]);
    if ($row[3] eq 'valid') { 
        $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
        if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
        if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } }
      else { 
        $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
        if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
        if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } } }

  foreach my $joinkey (sort keys %{ $hash{status} }) {
    my $count = 0;
    foreach my $pdf_type (sort keys %{ $hash{$type}{$joinkey} }) {
      foreach my $data (sort keys %{ $hash{$type}{$joinkey}{$pdf_type} }) {
        next unless $data;
        my $curator = $hash{$type}{$joinkey}{$pdf_type}{$data}{curator};
        my $timestamp = $hash{$type}{$joinkey}{$pdf_type}{$data}{timestamp};
        $count++; my $order = "'$count'"; 
        ($data) = &filterForPg($data);
        unless ($curator) { 
#           print "NO CURATOR $joinkey T $type D $data\n"; 
          $curator = 'two1841'; }
#         print "$type\t$joinkey\t$data\t$order\t$curator\t$timestamp\n";
        $result = $dbh->do( "INSERT INTO $papt VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
        $result = $dbh->do( "INSERT INTO h_$papt VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
  } } }
} # sub populateElectronicPath


sub populateNonXml {		# populate tables that have data not in xml (and are not special)
#   my @not_xml_tables = qw( abstract affiliation author contained_in editor fulltext_url ignore publisher remark erratum_in internal_comment curation_flags );	# internal_comment and curation_flags are new tables, erratum_in is currently unclear because wiki says 3 entries, but type 14 says 21 entries, so ignoring it.
  my @not_xml_tables = qw( abstract affiliation author contained_in editor fulltext_url ignore publisher remark );
  foreach my $type (@not_xml_tables) {
#     if ($multi{$type}) { print "MULTI $type\n"; }
    $result = $dbh->do( "DELETE FROM pap_$type;" );
    $result = $dbh->do( "DELETE FROM h_pap_$type;" ); }

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'; ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  foreach my $type (@not_xml_tables) {
    $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
      next unless ($row[1]);
      unless ($row[2]) { $row[2] = 'NULL'; }
      if ($row[3] eq 'valid') { 
          $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } }
        else { 
          $hash{$type}{$row[0]}{$row[2]}{$row[1]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{$row[2]}{$row[1]}{timestamp} = $row[5]; } } }

    foreach my $joinkey (sort keys %{ $hash{status} }) {
      my $count = 0;
      foreach my $old_order (sort keys %{ $hash{$type}{$joinkey} }) {
        foreach my $data (sort keys %{ $hash{$type}{$joinkey}{$old_order} }) {
          next unless $data;
          my $curator = $hash{$type}{$joinkey}{$old_order}{$data}{curator};
          my $timestamp = $hash{$type}{$joinkey}{$old_order}{$data}{timestamp};
          my $order = "NULL"; 
          if ($single{$type}) { 1; }
            elsif ($multi{$type}) { 
              if ($old_order ne "NULL") { $order = "'$old_order'"; }
                else { $count++; $order = "'$count'"; } }
            else { print "ERR neither single nor multi $type\n"; }
          ($data) = &filterForPg($data);
          unless ($curator) { 
#             print "NO CURATOR $joinkey T $type D $data\n"; 
            $curator = 'two1841'; }
#           print "$type\t$joinkey\t$data\t$order\t$curator\t$timestamp\n";
          $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
          $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
    } } }
  } # foreach my $type (@not_xml_tables)
} # sub populateNonXml

sub populateUnlessXml {		# populate stuff that would normally come from xml for papers that don't have pmid 
  my @unique_ref = qw( title journal volume pages year primary_data type );
#   my @unique_ref = qw( type primary_data );
  foreach my $type (@unique_ref) {
    $result = $dbh->do( "DELETE FROM pap_$type WHERE joinkey IN (SELECT joinkey FROM pap_status WHERE pap_status = 'valid' AND joinkey NOT IN (SELECT joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid'));" );
    $result = $dbh->do( "DELETE FROM h_pap_$type WHERE joinkey IN (SELECT joinkey FROM pap_status WHERE pap_status = 'valid' AND joinkey NOT IN (SELECT joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid'));" ); }

  my %hash;
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid' AND joinkey NOT IN (SELECT joinkey FROM pap_identifier WHERE pap_identifier ~ 'pmid'); ");
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }

  foreach my $type (@unique_ref) {
    next if ($type eq 'primary_data');	# infer this from type
    $result = $dbh->prepare( "SELECT * FROM wpa_$type ORDER BY wpa_timestamp" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) {
# if ($row[0] eq '00005120') { print "ROW @row ROW\n"; }
# if ($row[0] eq '00024942') { print "ROW @row ROW\n"; }
      if ($row[3] eq 'valid') { 
          $hash{$type}{$row[0]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{timestamp} = $row[5]; } }
        else { 
          $hash{$type}{$row[0]}{data} = $row[1];
          if ($row[4]) { $hash{$type}{$row[0]}{curator} = $row[4]; }
          if ($row[5]) { $hash{$type}{$row[0]}{timestamp} = $row[5]; } }
    }

    foreach my $joinkey (sort keys %{ $hash{status} }) {
# if ($joinkey eq '00005120') { print "IN ROW\n"; }
# if ($joinkey eq '00024942') { print "IN ROW\n"; }
      next unless $hash{$type}{$joinkey}{data};
      my $data = $hash{$type}{$joinkey}{data};
      my $curator = $hash{$type}{$joinkey}{curator};
      my $timestamp = $hash{$type}{$joinkey}{timestamp};
# if ($joinkey eq '00005120') { print "DATA $data $curator $timestamp\n"; }
# if ($joinkey eq '00024942') { print "DATA $data $curator $timestamp\n"; }
      my $order = "NULL";
      if ($type eq 'type') { 
        my $primary_data = '';
        if ($primary_data{$data}) { $primary_data = $primary_data{$data}; }
        $order = "'1'";	 
#         print "Joinkey\t$joinkey\tPrimary\t$primary_data\n"; 
        $result = $dbh->do( "INSERT INTO pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', '$timestamp')" );
        $result = $dbh->do( "INSERT INTO h_pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', '$timestamp')" );
      }		# order only exists for type, and is always 1 since there's no previous data
#       if ( ($type eq 'type') && ( ($data ne '3') && ($data ne '4') ) ) { print "NEWTYPE\n"; }
      ($data) = &filterForPg($data);
#       print "$type\t$joinkey\t$data\t$curator\t$timestamp\n";
      $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
      $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$data', $order, '$curator', '$timestamp')" );
    }
  }
} # sub populateUnlessXml

sub populateFromXml {		# POPULATE SOME REFERENCE FROM XML, not dealing with type
#   my @unique_ref = qw( title journal volume pages year month day affiliation pubmed_final primary_data type );	# kimberly doesn't want affiliation from xml
  my @unique_ref = qw( title journal volume pages year month day pubmed_final primary_data type );
  foreach my $type (@unique_ref) {
    $result = $dbh->do( "DELETE FROM pap_$type;" );
    $result = $dbh->do( "DELETE FROM h_pap_$type;" );
  }

#   my %affi;
#   
#   $result = $dbh->prepare( "SELECT * FROM pap_affiliation" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { $affi{$row[0]} = $row[1]; }

  my %month_to_num;
  $month_to_num{Jan} = '1';
  $month_to_num{Feb} = '2';
  $month_to_num{Mar} = '3';
  $month_to_num{Apr} = '4';
  $month_to_num{May} = '5';
  $month_to_num{Jun} = '6';
  $month_to_num{Jul} = '7';
  $month_to_num{Aug} = '8';
  $month_to_num{Sep} = '9';
  $month_to_num{Oct} = '10';
  $month_to_num{Nov} = '11';
  $month_to_num{Dec} = '12';

  my %type_index;		# type to type_index mapping
  $type_index{"Journal_article"} = '1';  
  $type_index{"Review"} = '2';  
  $type_index{"Meeting_abstract"} = '3';  
  $type_index{"Gazette_article"} = '4';  
  $type_index{"Book_chapter"} = '5';  
  $type_index{"News"} = '6';  
  $type_index{"Email"} = '7';  
  $type_index{"Book"} = '8';  
  $type_index{"Historical_article"} = '9';  
  $type_index{"Comment"} = '10'; 
  $type_index{"Letter"} = '11'; 
  $type_index{"Monograph"} = '12'; 
  $type_index{"Editorial"} = '13'; 
  $type_index{"Published_erratum"} = '14'; 
  $type_index{"Retracted_publication"} = '15'; 
  $type_index{"Technical_report"} = '16'; 
  $type_index{"Other"} = '17'; 
  $type_index{"Wormbook"} = '18'; 
  $type_index{"Interview"} = '19'; 
  $type_index{"Lectures"} = '20'; 
  $type_index{"Congresses"} = '21'; 
  $type_index{"Interactive_tutorial"} = '22'; 
  $type_index{"Biography"} = '23'; 
  $type_index{"Directory"} = '24'; 

  my %specific_type;		# types that don't become "Other" and aren't only Journal_article
  $specific_type{2} = 'Review';
  $specific_type{6} = 'News';
  $specific_type{9} = 'Historical_article';
  $specific_type{10} = 'Comment';
  $specific_type{11} = 'Letter';
  $specific_type{12} = 'Monograph';
  $specific_type{13} = 'Editorial';
  $specific_type{14} = 'Published_erratum';
  $specific_type{15} = 'Retracted_publication';
  $specific_type{16} = 'Technical_report';
  $specific_type{19} = 'Interview';
  $specific_type{20} = 'Lectures';
  $specific_type{21} = 'Congresses';
  $specific_type{22} = 'Interactive_tutorial';
  $specific_type{23} = 'Biography';
  $specific_type{24} = 'Directory';
  
  $/ = undef;
  my (@xml) = </home/postgres/work/pgpopulation/wpa_papers/wpa_pubmed_final/xml/*>;
  my (@done_xml) = </home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/done/*>;
  foreach (@done_xml) { push @xml, $_; }
  foreach my $xml (@xml) {		# foreach xml that we have
    my ($id) = $xml =~ m/\/(\d+)$/;
    open (IN, "<$xml") or die "Cannot open $xml : $!";
    my $xml_data = <IN>;
    close (IN) or die "Cannot close $xml : $!";
    my ($title) = $xml_data =~ /\<ArticleTitle\>(.+?)\<\/ArticleTitle\>/i;
    my ($journal) = $xml_data =~ /<MedlineTA>(.+?)\<\/MedlineTA\>/i;
    my ($pages) = $xml_data =~ /\<MedlinePgn\>(.+?)\<\/MedlinePgn\>/i;
    my ($volume) = $xml_data =~ /\<Volume\>(.+?)\<\/Volume\>/i;
    my $year = ''; my $month = ''; my $day = '';
    if ( $xml_data =~ /\<PubDate\>(.+?)\<\/PubDate\>/i ) {
      my ($PubDate) = $xml_data =~ /\<PubDate\>(.+?)\<\/PubDate\>/i;
      if ( $PubDate =~ /\<Year\>(.+?)\<\/Year\>/i ) { $year = $1; }
      if ( $PubDate =~ /\<Month\>(.+?)\<\/Month\>/i ) { $month = $1; 
        if ($month_to_num{$month}) { $month = $month_to_num{$month}; } }
      if ( $PubDate =~ /\<Day\>(.+?)\<\/Day\>/i ) { $day = $1; } }
    my ($abstract) = $xml_data =~ /\<AbstractText\>(.+?)\<\/AbstractText\>/i;
#     my ($affiliation) = $xml_data =~ /\<Affiliation\>(.+?)\<\/Affiliation\>/i;
    my (@types) = $xml_data =~ /\<PublicationType\>(.+?)\<\/PublicationType\>/gi;
    ($title) = &filterForPg($title);
    ($journal) = &filterForPg($journal);
    ($pages) = &filterForPg($pages);
    ($volume) = &filterForPg($volume);
    ($year) = &filterForPg($year);
    ($month) = &filterForPg($month);
    ($day) = &filterForPg($day);
#     ($affiliation) = &filterForPg($affiliation);
    ($abstract) = &filterForPg($abstract);
    foreach (@types) { ($_) = &filterForPg($_); }
    my $pubmed_final = 'not_final';
    if ($xml_data =~ /\<MedlineCitation Owner=\"NLM\" Status=\"MEDLINE\"\>/) { $pubmed_final = 'final'; }
#   my ($doi) = $page =~ /\<ArticleId IdType=\"doi\"\>(.+?)\<\/ArticleId\>/i; $doi = 'doi' . $doi;
  
    my $curator = 'two10877';		# pubmed
    my $timestamp = 'CURRENT_TIMESTAMP';
  
    unless ($id) { print "XML $xml END\n"; }
  
    if ($idents{$id}) {		# if the pmid maps to a wbpaper joinkey
      my $joinkey = $idents{$id};
#       next unless $affiliation;
#       unless ($affi{$joinkey}) { print "$joinkey\t$id\t$affiliation\n"; }
#     print "Title $joinkey $id $title\n";
      if ($title) {
        $result = $dbh->do( "INSERT INTO pap_title VALUES ('$joinkey', '$title', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_title VALUES ('$joinkey', '$title', NULL, '$curator', $timestamp)" ); }
      if ($journal) {
        $result = $dbh->do( "INSERT INTO pap_journal VALUES ('$joinkey', '$journal', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_journal VALUES ('$joinkey', '$journal', NULL, '$curator', $timestamp)" ); }
      if ($pages) {
        $result = $dbh->do( "INSERT INTO pap_pages VALUES ('$joinkey', '$pages', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_pages VALUES ('$joinkey', '$pages', NULL, '$curator', $timestamp)" ); }
      if ($volume) {
        $result = $dbh->do( "INSERT INTO pap_volume VALUES ('$joinkey', '$volume', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_volume VALUES ('$joinkey', '$volume', NULL, '$curator', $timestamp)" ); }
      if ($year) {
        $result = $dbh->do( "INSERT INTO pap_year VALUES ('$joinkey', '$year', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_year VALUES ('$joinkey', '$year', NULL, '$curator', $timestamp)" ); }
      if ($month) {
        $result = $dbh->do( "INSERT INTO pap_month VALUES ('$joinkey', '$month', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_month VALUES ('$joinkey', '$month', NULL, '$curator', $timestamp)" ); }
      if ($day) {
        $result = $dbh->do( "INSERT INTO pap_day VALUES ('$joinkey', '$day', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_day VALUES ('$joinkey', '$day', NULL, '$curator', $timestamp)" ); }
#       if ($affiliation) {
#         $result = $dbh->do( "INSERT INTO pap_affiliation VALUES ('$joinkey', '$affiliation', NULL, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO h_pap_affiliation VALUES ('$joinkey', '$affiliation', NULL, '$curator', $timestamp)" ); }
      if ($pubmed_final) {
        $result = $dbh->do( "INSERT INTO pap_pubmed_final VALUES ('$joinkey', '$pubmed_final', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_pubmed_final VALUES ('$joinkey', '$pubmed_final', NULL, '$curator', $timestamp)" ); }
      if ($types[0]) {
        my %types;
        foreach my $type (@types) {
            ($type) = ucfirst(lc($type)); $type =~ s/\s+/_/g;
          if ($type_index{$type}) { 
            my $type_id = $type_index{$type};
            $types{$type_id}++;
# print "Joinkey\t$joinkey\tType\t$type\t$type_id\n"; 
          }	# else { $types{17}++; }	# other ????
        } # foreach my $type (@types)
        my $primary_data = '';
        my @actual_types;
        foreach my $type_id (keys %types) { 	# for each type_id, if it's specific, use that type_id
          if ($specific_type{$type_id}) { push @actual_types, $type_id; } }
        unless ($actual_types[0]) { 		# if there are no specific types and it's journal, use that
          if ($types{1}) { push @actual_types, 1; } }
        unless ($actual_types[0]) { 		# if there are no types, use Other
          push @actual_types, 17; }
        my $count = 0;
        foreach my $type_id (@actual_types) {
          $count++;
          $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '$type_id', '$count', '$curator', $timestamp)" );
          $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '$type_id', '$count', '$curator', $timestamp)" );
          if ($primary_data{$type_id}) {		# if there's a primary_data entry for this type_id
            next if $primary_data eq 'primary';		# skip if already primary
            if ($primary_data{$type_id} eq 'primary') { $primary_data = $primary_data{$type_id}; next; }
            next if $primary_data eq 'not_primary';	# skip if already not_primary
            if ($primary_data{$type_id} eq 'not_primary') { $primary_data = $primary_data{$type_id}; next; }
            $primary_data = $primary_data{$type_id};	# assign to not_designated by default
          }
# print "Joinkey\t$joinkey\tTypeID\t$type_id\n"; 
        }
# print "Joinkey\t$joinkey\tPrimary\t$primary_data\n"; 
        $result = $dbh->do( "INSERT INTO pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', $timestamp)" );
        $result = $dbh->do( "INSERT INTO h_pap_primary_data VALUES ('$joinkey', '$primary_data', NULL, '$curator', $timestamp)" );
      } # if ($type)
    } # if ($idents{$id})
  
#   print "ID $id\n";
  } # foreach my $xml (@xml)
  $/ = "\n";
} # sub populateFromXml

sub populateExtraTypes {
  my %extraBook_chapter;
  $extraBook_chapter{"00002172"}++;
  $extraBook_chapter{"00002244"}++;
  $extraBook_chapter{"00002245"}++;
  $extraBook_chapter{"00002246"}++;
  $extraBook_chapter{"00002247"}++;
  $extraBook_chapter{"00002248"}++;
  $extraBook_chapter{"00002249"}++;
  $extraBook_chapter{"00002250"}++;
  $extraBook_chapter{"00002251"}++;
  $extraBook_chapter{"00002252"}++;
  $extraBook_chapter{"00002253"}++;
  $extraBook_chapter{"00002254"}++;
  $extraBook_chapter{"00002255"}++;
  $extraBook_chapter{"00002256"}++;
  $extraBook_chapter{"00002257"}++;
  $extraBook_chapter{"00002258"}++;
  $extraBook_chapter{"00002259"}++;
  $extraBook_chapter{"00002260"}++;
  $extraBook_chapter{"00002261"}++;
  $extraBook_chapter{"00002262"}++;
  $extraBook_chapter{"00002263"}++;
  $extraBook_chapter{"00002264"}++;
  $extraBook_chapter{"00002265"}++;
  $extraBook_chapter{"00002266"}++;
  $extraBook_chapter{"00002267"}++;
  $extraBook_chapter{"00002268"}++;
  $extraBook_chapter{"00002269"}++;
  $extraBook_chapter{"00024687"}++;
  $extraBook_chapter{"00029144"}++;
  $extraBook_chapter{"00031351"}++;
  $extraBook_chapter{"00032010"}++;

  my %extraBook_chapterAndWormBook;
  $extraBook_chapterAndWormBook{"00027222"}++;
  $extraBook_chapterAndWormBook{"00027223"}++;
  $extraBook_chapterAndWormBook{"00027224"}++;
  $extraBook_chapterAndWormBook{"00027225"}++;
  $extraBook_chapterAndWormBook{"00027226"}++;
  $extraBook_chapterAndWormBook{"00027227"}++;
  $extraBook_chapterAndWormBook{"00027228"}++;
  $extraBook_chapterAndWormBook{"00027229"}++;
  $extraBook_chapterAndWormBook{"00027230"}++;
  $extraBook_chapterAndWormBook{"00027231"}++;
  $extraBook_chapterAndWormBook{"00027232"}++;
  $extraBook_chapterAndWormBook{"00027233"}++;
  $extraBook_chapterAndWormBook{"00027234"}++;
  $extraBook_chapterAndWormBook{"00027235"}++;
  $extraBook_chapterAndWormBook{"00027236"}++;
  $extraBook_chapterAndWormBook{"00027237"}++;
  $extraBook_chapterAndWormBook{"00027238"}++;
  $extraBook_chapterAndWormBook{"00027239"}++;
  $extraBook_chapterAndWormBook{"00027240"}++;
  $extraBook_chapterAndWormBook{"00027241"}++;
  $extraBook_chapterAndWormBook{"00027242"}++;
  $extraBook_chapterAndWormBook{"00027243"}++;
  $extraBook_chapterAndWormBook{"00027244"}++;
  $extraBook_chapterAndWormBook{"00027245"}++;
  $extraBook_chapterAndWormBook{"00027246"}++;
  $extraBook_chapterAndWormBook{"00027247"}++;
  $extraBook_chapterAndWormBook{"00027248"}++;
  $extraBook_chapterAndWormBook{"00027249"}++;
  $extraBook_chapterAndWormBook{"00027250"}++;
  $extraBook_chapterAndWormBook{"00027251"}++;
  $extraBook_chapterAndWormBook{"00027252"}++;
  $extraBook_chapterAndWormBook{"00027253"}++;
  $extraBook_chapterAndWormBook{"00027254"}++;
  $extraBook_chapterAndWormBook{"00027255"}++;
  $extraBook_chapterAndWormBook{"00027256"}++;
  $extraBook_chapterAndWormBook{"00027257"}++;
  $extraBook_chapterAndWormBook{"00027258"}++;
  $extraBook_chapterAndWormBook{"00027259"}++;
  $extraBook_chapterAndWormBook{"00027260"}++;
  $extraBook_chapterAndWormBook{"00027261"}++;
  $extraBook_chapterAndWormBook{"00027262"}++;
  $extraBook_chapterAndWormBook{"00027263"}++;
  $extraBook_chapterAndWormBook{"00027264"}++;
  $extraBook_chapterAndWormBook{"00027265"}++;
  $extraBook_chapterAndWormBook{"00027266"}++;
  $extraBook_chapterAndWormBook{"00027267"}++;
  $extraBook_chapterAndWormBook{"00027268"}++;
#   $extraBook_chapterAndWormBook{"00027269"}++;	# MISSING ?
  $extraBook_chapterAndWormBook{"00027270"}++;
  $extraBook_chapterAndWormBook{"00027271"}++;
  $extraBook_chapterAndWormBook{"00027272"}++;
  $extraBook_chapterAndWormBook{"00027273"}++;
  $extraBook_chapterAndWormBook{"00027274"}++;
  $extraBook_chapterAndWormBook{"00027275"}++;
  $extraBook_chapterAndWormBook{"00027276"}++;
  $extraBook_chapterAndWormBook{"00027277"}++;
  $extraBook_chapterAndWormBook{"00027278"}++;
  $extraBook_chapterAndWormBook{"00027279"}++;
  $extraBook_chapterAndWormBook{"00027280"}++;
  $extraBook_chapterAndWormBook{"00027281"}++;
  $extraBook_chapterAndWormBook{"00027282"}++;
  $extraBook_chapterAndWormBook{"00027283"}++;
  $extraBook_chapterAndWormBook{"00027284"}++;
  $extraBook_chapterAndWormBook{"00027285"}++;
  $extraBook_chapterAndWormBook{"00027286"}++;
  $extraBook_chapterAndWormBook{"00027287"}++;
  $extraBook_chapterAndWormBook{"00027288"}++;
  $extraBook_chapterAndWormBook{"00027289"}++;
  $extraBook_chapterAndWormBook{"00027290"}++;
  $extraBook_chapterAndWormBook{"00027291"}++;
  $extraBook_chapterAndWormBook{"00027292"}++;
  $extraBook_chapterAndWormBook{"00027293"}++;
  $extraBook_chapterAndWormBook{"00027294"}++;
  $extraBook_chapterAndWormBook{"00027295"}++;
  $extraBook_chapterAndWormBook{"00027296"}++;
  $extraBook_chapterAndWormBook{"00027297"}++;
  $extraBook_chapterAndWormBook{"00027298"}++;
  $extraBook_chapterAndWormBook{"00027299"}++;
  $extraBook_chapterAndWormBook{"00027300"}++;
  $extraBook_chapterAndWormBook{"00027301"}++;
  $extraBook_chapterAndWormBook{"00027302"}++;
  $extraBook_chapterAndWormBook{"00027304"}++;
  $extraBook_chapterAndWormBook{"00027305"}++;
  $extraBook_chapterAndWormBook{"00027306"}++;
  $extraBook_chapterAndWormBook{"00027307"}++;
  $extraBook_chapterAndWormBook{"00027309"}++;
  $extraBook_chapterAndWormBook{"00027310"}++;
  $extraBook_chapterAndWormBook{"00027311"}++;
  $extraBook_chapterAndWormBook{"00027312"}++;
  $extraBook_chapterAndWormBook{"00027313"}++;
  $extraBook_chapterAndWormBook{"00027314"}++;
  $extraBook_chapterAndWormBook{"00027315"}++;
  $extraBook_chapterAndWormBook{"00027316"}++;
  $extraBook_chapterAndWormBook{"00027317"}++;
  $extraBook_chapterAndWormBook{"00027318"}++;
  $extraBook_chapterAndWormBook{"00027319"}++;
  $extraBook_chapterAndWormBook{"00029012"}++;
  $extraBook_chapterAndWormBook{"00029016"}++;
  $extraBook_chapterAndWormBook{"00029019"}++;
  $extraBook_chapterAndWormBook{"00029022"}++;
  $extraBook_chapterAndWormBook{"00029033"}++;
  $extraBook_chapterAndWormBook{"00031286"}++;
  $extraBook_chapterAndWormBook{"00031287"}++;
  $extraBook_chapterAndWormBook{"00031288"}++;
  $extraBook_chapterAndWormBook{"00031289"}++;
  $extraBook_chapterAndWormBook{"00031290"}++;
  $extraBook_chapterAndWormBook{"00031291"}++;
  $extraBook_chapterAndWormBook{"00031292"}++;
  $extraBook_chapterAndWormBook{"00031388"}++;
  $extraBook_chapterAndWormBook{"00031293"}++;
  $extraBook_chapterAndWormBook{"00031414"}++;
  $extraBook_chapterAndWormBook{"00031415"}++;
  $extraBook_chapterAndWormBook{"00031646"}++;
  $extraBook_chapterAndWormBook{"00032172"}++;
  $extraBook_chapterAndWormBook{"00032226"}++;
  $extraBook_chapterAndWormBook{"00032944"}++;
  $extraBook_chapterAndWormBook{"00035143"}++;
  $extraBook_chapterAndWormBook{"00035958"}++;

  my %type;
  $result = $dbh->prepare( "SELECT * FROM pap_type" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    $type{$row[1]}{$row[0]}++;
    if ($type{amount}{$row[0]}) {
      if ($type{amount}{$row[0]} < $row[2]) { $type{amount}{$row[0]} = $row[2]; } }
    else { $type{amount}{$row[0]} = $row[2]; }
  }

  my $curator = 'two1843';
  my $timestamp = 'CURRENT_TIMESTAMP';
  foreach my $joinkey (sort {$a<=>$b} keys %extraBook_chapter) {
    my $order = $type{amount}{$joinkey}; 
    if ($type{5}{$joinkey}) { print "Already 5 in $joinkey\n"; }
      else { $order++;
        print "$joinkey\t5\t$order\ttwo1843\tCurrent\n";
#         $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" ); 
    }
  }
  foreach my $joinkey (sort {$a<=>$b} keys %extraBook_chapterAndWormBook) {
    my $order = $type{amount}{$joinkey}; 
    if ($type{5}{$joinkey}) { print "Already 5 in $joinkey\n"; }
      else { $order++;
        print "$joinkey\t5\t$order\ttwo1843\tCurrent\n";
#         $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '5', $order, '$curator', $timestamp)" ); 
    }
    if ($type{18}{$joinkey}) { print "Already 18 in $joinkey\n"; }
      else { $order++;
        print "$joinkey\t18\t$order\ttwo1843\tCurrent\n";
#         $result = $dbh->do( "INSERT INTO h_pap_type VALUES ('$joinkey', '18', $order, '$curator', $timestamp)" );
#         $result = $dbh->do( "INSERT INTO pap_type VALUES ('$joinkey', '18', $order, '$curator', $timestamp)" ); 
    }
  }
} # sub populateExtraTypes

sub populateStatusIdentifier {		# TO POPULATE THE TABLES : status, identifier
  foreach my $table (@pap_tables) { 
    $result = $dbh->do( "DELETE FROM h_pap_$table" );
    $result = $dbh->do( "DELETE FROM pap_$table" ); }
  
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{status}{$row[0]}{valid} = 'valid';
        $hash{status}{$row[0]}{data} = $row[1];
        if ($row[4]) { $hash{status}{$row[0]}{curator} = $row[4]; }
        if ($row[5]) { $hash{status}{$row[0]}{timestamp} = $row[5]; } }
      else { 
        $hash{status}{$row[0]}{valid} = 'invalid';
        $hash{status}{$row[0]}{data} = $row[1];
        if ($row[4]) { $hash{status}{$row[0]}{curator} = $row[4]; }
        if ($row[5]) { $hash{status}{$row[0]}{timestamp} = $row[5]; }
#         my (@values) = keys %{ $hash{status}{$row[0]} };
#         if (scalar @values < 1) { delete $hash{status}{$row[0]}; }
      }
  } # while (my @row = $result->fetchrow)
  
  $result = $dbh->prepare( "SELECT * FROM wpa_identifier ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{identifier}{$row[0]}{$row[1]}{curator} = $row[4];
        $hash{identifier}{$row[0]}{$row[1]}{timestamp} = $row[5]; }
      else { delete $hash{identifier}{$row[0]}{$row[1]}; }
  } # while (my @row = $result->fetchrow)

  my $type = 'status';
  foreach my $joinkey (sort keys %{ $hash{$type} }) {
    my $data = $hash{$type}{$joinkey}{data};
    my $valid = $hash{$type}{$joinkey}{valid};
    my $curator = $hash{$type}{$joinkey}{curator};
    my $timestamp = $hash{$type}{$joinkey}{timestamp};
#       print "$joinkey\t$data\t$curator\t$timestamp\n";
    $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$valid', NULL, '$curator', '$timestamp')" );
    $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$valid', NULL, '$curator', '$timestamp')" );
  }

  my %badPmid;			# no xml in pubmed
  $badPmid{'pmid12591608'}++;
  $badPmid{'pmid14532430'}++;
  $badPmid{'pmid14532626'}++;
  $badPmid{'pmid14532629'}++;
  $badPmid{'pmid14532633'}++;
  $badPmid{'pmid14532635'}++;
  $badPmid{'pmid14731937'}++;
  $badPmid{'pmid15577917'}++;
  $badPmid{'pmid15817570'}++;
  $badPmid{'pmid15902193'}++;
  $badPmid{'pmid16551030'}++;
  $badPmid{'pmid16551054'}++;
  $badPmid{'pmid16652241'}++;
  $badPmid{'pmid17154166'}++;
  $badPmid{'pmid17154292'}++;
  $badPmid{'pmid17169184'}++;
  $badPmid{'pmid17407201'}++;
  $badPmid{'pmid18023125'}++;
  $badPmid{'pmid18050406'}++;
  $badPmid{'pmid18050420'}++;
  $badPmid{'pmid18548071'}++;
  $badPmid{'pmid18677322'}++;
  $badPmid{'pmid18692560'}++;
  $badPmid{'pmid18711361'}++;
  $badPmid{'pmid18725909'}++;
  $badPmid{'pmid18841162'}++;
  $badPmid{'pmid94222994'}++;

  
  $type = 'identifier';
  foreach my $joinkey (sort keys %{ $hash{$type} }) {
    next unless ($hash{status}{$joinkey});
    next unless ($hash{status}{$joinkey}{valid} eq 'valid');
    my $order = 0;
    foreach my $data (sort keys %{ $hash{$type}{$joinkey} } ) {
      next unless $data;
      next if ($badPmid{$data});
      $order++;
      my $curator = $hash{$type}{$joinkey}{$data}{curator};
      my $timestamp = $hash{$type}{$joinkey}{$data}{timestamp};
#         print "$joinkey\t$data\t$curator\t$timestamp\n";
      $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$joinkey', '$data', '$order', '$curator', '$timestamp')" );
      $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$joinkey', '$data', '$order', '$curator', '$timestamp')" );
    }
  }
} # sub populateStatusIdentifier

sub populateErratum {
  my %erratum_in;
  $erratum_in{"00001805"}{"00001892"}++;
  $erratum_in{"00003297"}{"00003344"}++;
  $erratum_in{"00003297"}{"00003456"}++;
  $erratum_in{"00003302"}{"00003457"}++;
  $erratum_in{"00003600"}{"00003688"}++;
  $erratum_in{"00003222"}{"00003750"}++;
  $erratum_in{"00003638"}{"00003800"}++;
  $erratum_in{"00004137"}{"00004301"}++;
  $erratum_in{"00004835"}{"00005285"}++;
  $erratum_in{"00005127"}{"00005304"}++;
  $erratum_in{"00005344"}{"00005412"}++;
  $erratum_in{"00004978"}{"00005701"}++;
  $erratum_in{"00005292"}{"00005746"}++;
  $erratum_in{"00024886"}{"00024897"}++;
  $erratum_in{"00003297"}{"00026886"}++;
  $erratum_in{"00024920"}{"00026902"}++;
  $erratum_in{"00026758"}{"00026911"}++;
  $erratum_in{"00026636"}{"00027056"}++;
  $erratum_in{"00026959"}{"00027096"}++;
  $erratum_in{"00031151"}{"00031373"}++;
  $erratum_in{"00030896"}{"00032419"}++;
  my $curator = 'two1843';
  my $timestamp = 'CURRENT_TIMESTAMP';
  foreach my $joinkey (sort keys %erratum_in) {
    my $order = 0;
    foreach my $erratum_in (sort keys %{ $erratum_in{$joinkey} }) {
      $order++;
      $result = $dbh->do( "INSERT INTO pap_erratum_in VALUES ('$joinkey', '$erratum_in', $order, '$curator', $timestamp)" );
      $result = $dbh->do( "INSERT INTO h_pap_erratum_in VALUES ('$joinkey', '$erratum_in', $order, '$curator', $timestamp)" );
    }
  }
} # sub populateErratum


sub populateTypeIndex {
  $result = $dbh->do( "DELETE FROM h_pap_type_index" );
  $result = $dbh->do( "DELETE FROM pap_type_index" ); 
  
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM wpa_type_index ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{type_index}{$row[0]}{$row[1]}{curator} = $row[4];
        $hash{type_index}{$row[0]}{$row[1]}{timestamp} = $row[5]; }
      else { 
        delete $hash{type_index}{$row[0]}{$row[1]}; 
        my (@values) = keys %{ $hash{type_index}{$row[0]} };
        if (scalar @values < 1) { delete $hash{type_index}{$row[0]}; } } }
  
  foreach my $type (sort keys %hash) {
    foreach my $type_id (sort {$a<=>$b} keys %{ $hash{$type} }) {
      foreach my $data (sort keys %{ $hash{$type}{$type_id} } ) {
        next unless $data;
        my $curator = $hash{$type}{$type_id}{$data}{curator};
        my $timestamp = $hash{$type}{$type_id}{$data}{timestamp};
        print "$type_id\t$data\t$curator\t$timestamp\n";
        $result = $dbh->do( "INSERT INTO pap_$type VALUES ('$type_id', '$data', NULL, '$curator', '$timestamp')" );
        $result = $dbh->do( "INSERT INTO h_pap_$type VALUES ('$type_id', '$data', NULL, '$curator', '$timestamp')" );
} } } } # sub populateTypeIndex



sub getOddJournals {		# GET list of journals that are in valid papers, but aren't in pubmed
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{status}{$row[0]}++; }
  
  $result = $dbh->prepare( "SELECT * FROM pap_journal" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { 
    $hash{journal}{$row[0]} = $row[1]; 
    $hash{existingjournal}{$row[1]}++; }
  
  $result = $dbh->prepare( "SELECT * FROM wpa_type ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{wpatype}{$row[0]}{$row[1]}++; }
      else { delete $hash{wpatype}{$row[0]}{$row[1]}; }
  } # while (my @row = $result->fetchrow)
  
  $result = $dbh->prepare( "SELECT * FROM wpa_journal ORDER BY wpa_timestamp" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) {
    if ($row[3] eq 'valid') { 
        $hash{wpajournal}{$row[0]}{$row[1]}++; }
      else { delete $hash{wpajournal}{$row[0]}{$row[1]}; }
  } # while (my @row = $result->fetchrow)
  
  
  my %odd_journals;
  foreach my $joinkey (sort keys %{ $hash{status} }) {
    next if ($hash{journal}{$joinkey});
    next unless ($hash{wpatype}{$joinkey}{1});
    if ($hash{wpajournal}{$joinkey}) { 
      foreach my $journal (keys %{ $hash{wpajournal}{$joinkey} }) {
        next if ($hash{existingjournal}{$journal});
        $odd_journals{ $journal }{ $joinkey }++; 
  } } }
  foreach my $odd_journal (sort keys %odd_journals) {
    my @paps;
    foreach my $joinkey ( sort keys %{ $odd_journals{$odd_journal} } ) {
      my @ids = sort keys %{ $all_ids{$joinkey} };
      my $ids = join", ", @ids;
      push @paps, "$joinkey ( $ids )";
    }
    my $count = scalar(@paps);
    my $paps = join"\t", @paps;
    print "$odd_journal\t$count\t$paps\n";
  } # foreach my $odd_journal (sort keys %odd_journals)
} # sub getOddJournals

sub checkAffiliationWrong {
  my %hash;
  
  $result = $dbh->prepare( "SELECT * FROM pap_affiliation" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $hash{$row[0]} = $row[1]; }

  $/ = undef;
  my (@xml) = </home/postgres/work/pgpopulation/wpa_papers/wpa_pubmed_final/xml/*>;
  my (@done_xml) = </home/postgres/work/pgpopulation/wpa_papers/pmid_downloads/done/*>;
  foreach (@done_xml) { push @xml, $_; }
  foreach my $xml (@xml) {
    my ($id) = $xml =~ m/\/(\d+)$/;
    open (IN, "<$xml") or die "Cannot open $xml : $!";
    my $xml_data = <IN>;
    close (IN) or die "Cannot close $xml : $!";
    my ($affiliation) = $xml_data =~ /\<Affiliation\>(.+?)\<\/Affiliation\>/i;
    next unless $affiliation;
    if ($idents{$id}) {
      my $joinkey = $idents{$id};
      unless ($hash{$joinkey}) { print "$joinkey\t$id\t$affiliation\n"; }
    }
  }
  $/ = "\n";
} # sub checkAffiliationWrong



__END__


# TO CREATE THE TABLES

# foreach my $table (@pap_tables) { 
#   $result = $dbh->do( "DROP TABLE h_pap_$table" );
#   $result = $dbh->do( "DROP TABLE pap_$table" ); }

foreach my $table (@pap_tables) {
  my $papt = 'pap_' . $table;
  $result = $dbh->do( "CREATE TABLE $papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone )" ); 
  $result = $dbh->do( "CREATE INDEX ${papt}_idx ON $papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE $papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE $papt TO cecilia;" );

  
  $result = $dbh->do( "CREATE TABLE h_$papt ( joinkey text, $papt text, pap_order integer, pap_curator text, pap_timestamp timestamp with time zone DEFAULT ('now'::text)::timestamp without time zone )" ); 
  $result = $dbh->do( "CREATE INDEX h_${papt}_idx ON h_$papt USING btree (joinkey);" );
  $result = $dbh->do( "REVOKE ALL ON TABLE h_$papt FROM PUBLIC;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO postgres;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO acedb;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO apache;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO azurebrd;" );
  $result = $dbh->do( "GRANT ALL ON TABLE h_$papt TO cecilia;" );
} # foreach my $table (@pap_tables)

__END__


abstract
affiliation
# allele_curation	# not really used
author
author_index
author_possible
author_sent
author_verified
# checked_out		# FP probably, not needed anymore
# comments		# rename as internal_comment 
contained_in
contains
# date_published	# only 5 entries, gone
editor
# electronic_path_md5	# not used
# electronic_path_type	# replaced with electronic path type
electronic_path
# electronic_type_index	# not used ?
# erratum		# gone need erratum_in / erratum_for
fulltext_url		# the URLs are here and dump to remark tag in .ace
gene
# hardcopy
identifier
ignore			# functional annotation only / non worm
# in_book		# gone, replaced by contained_in / contains
journal
# keyword		# need to dump these into static .ace file for constant appending post-dump
# nematode_paper	# possibly taxon in the future, gone for now
pages
publisher
pubmed_final
remark
# rnai_curation		# move into curation flags
# rnai_int_done		# move into curation flags
title
# transgene_curation	# not really used
type
type_index
volume
year

new :
erratum_in
erratum_for
internal_comment	# populate with  comments
curation_flags		# flag for ``Phenotype2GO'' or blank / rnai_curation / rnai_int_done
primary_data		# primary data / no primary data / not designated
status			# replaces wpa for valid / invalid for whole paper

# affiliation in paper model.  also in #affiliation on author tag, but no longer in postgres author data, and not dumped.

__END__

$result = $dbh->do( "DROP VIEW pap_view" ); 
my @old_pap = qw( pap_affiliation pap_contained pap_email pap_journal pap_paper pap_possible pap_type pap_year pap_author pap_contains pap_inbook pap_page pap_pmid pap_title pap_verified pap_volume );
foreach my $table (@old_pap) { $result = $dbh->do( "DROP TABLE $table" ); }

__END__

my @pap_tables = qw( passwd celegans cnonbristol nematode nonnematode genestudied genesymbol extvariation mappingdata newmutant rnai lsrnai overexpr chemicals mosaic siteaction timeaction genefunc humdis geneint funccomp geneprod otherexpr microarray genereg seqfeat matrices antibody transgene marker invitro domanal covalent structinfo massspec structcorr seqchange newsnp ablationdata cellfunc phylogenetic othersilico supplemental nocuratable comment );


my %dataTable = ();
$dataTable{passwd} = 'passwd';
$dataTable{celegans} = '';
$dataTable{cnonbristol} = '';
$dataTable{nematode} = 'nematode';
$dataTable{nonnematode} = '';
$dataTable{genestudied} = 'rgngene';
$dataTable{genesymbol} = 'genesymbol';
$dataTable{extvariation} = '';
$dataTable{mappingdata} = 'mappingdata';
$dataTable{newmutant} = 'newmutant';
$dataTable{rnai} = 'rnai';
$dataTable{lsrnai} = 'lsrnai';
$dataTable{overexpr} = 'overexpression';
$dataTable{chemicals} = 'chemicals';
$dataTable{mosaid} = 'mosaid';
$dataTable{siteaction} = 'site';
$dataTable{timeaction} = '';
$dataTable{genefunc} = 'genefunction';
$dataTable{humdis} = 'humandiseases';
$dataTable{geneint} = 'geneinteractions';
$dataTable{funccomp} = '';			# functionalcomplementation was in cur_ not in afp_ 
$dataTable{geneprod} = 'geneproduct';
$dataTable{otherexpr} = 'expression';
$dataTable{microarray} = 'microarray';
$dataTable{genereg} = 'generegulation';
$dataTable{seqfeat} = 'sequencefeatures';
$dataTable{matrices} = '';
$dataTable{antibody} = 'antibody';
$dataTable{transgene} = 'transgene';
$dataTable{marker} = '';
$dataTable{invitro} = 'invitro';
$dataTable{domanal} = 'structureinformation';
$dataTable{covalent} = 'covalent';
$dataTable{structinfo} = 'structureinformation';
$dataTable{massspec} = 'massspec';
$dataTable{structcorr} = 'structurecorrectionsanger';
$dataTable{seqchange} = 'sequencechange';
$dataTable{newsnp} = 'newsnp';
$dataTable{ablationdata} = 'ablationdata';
$dataTable{cellfunc} = 'cellfunction';
$dataTable{phylogenetic} = 'phylogenetic';
$dataTable{othersilico} = 'othersilico';
$dataTable{supplemental} = 'supplemental';
$dataTable{nocuratable} = 'review';
$dataTable{comment} = 'comment';

# UNCOMMENT to repopulate afp_ tables from original dumps.  2009 03 21
# foreach my $table (@afp_tables) {
#   my $table2 = 'afp_' . $table ;
#   $result = $conn->exec("DROP TABLE $table2; ");
#   $result = $conn->exec( "CREATE TABLE $table2 ( joinkey text, $table2 text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text), afp_curator text, afp_approve text, afp_cur_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE UNIQUE INDEX ${table2}_idx ON $table2 USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table2 FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO cecilia; ");
#   my $table3 = $table . '_hst';
#   $result = $conn->exec("DROP TABLE $table3; ");
#   $result = $conn->exec( "CREATE TABLE $table3 ( joinkey text, $table3 text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text), afp_curator text, afp_approve text, afp_cur_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE INDEX ${table3}_idx ON $table3 USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table3 FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table3 TO cecilia; ");
#   if ($dataTable{$table}) { 
#     my $infile = "/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_$dataTable{$table}.pg";
#     open (IN, "<$infile") or die "Cannot open $infile : $!";
#     while (my $line = <IN>) {
#       chomp $line;
#       my ($joinkey, $data, $timestamp) = split/\t/, $line;
#       $data =~ s/\'/''/g;  $data =~ s/\\r\\n/\n/g;	# replace singlequotes and newlines
#       $result = $conn->exec( "INSERT INTO afp_$table VALUES ( '$joinkey', '$data', '$timestamp', NULL, NULL, NULL)" );
#       $result = $conn->exec( "INSERT INTO afp_${table}_hst VALUES ( '$joinkey', '$data', '$timestamp', NULL, NULL, NULL)" );
#     } # while (my $line = <IN>)
#     close (IN) or die "Cannot close $infile : $!";
# #     $result = $conn->exec( "COPY afp_$table FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_$dataTable{$table}.pg'" );
# #     $result = $conn->exec( "COPY afp_${table}_hst FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_$dataTable{$table}.pg'" ); 
#   } # if ($dataTable{$table}) 
# } # foreach my $table (@afp_tables)

# afp_ablationdata.pg               afp_humandiseases.pg              afp_passwd.pg
# afp_antibody.pg                   afp_invitro.pg                    afp_phylogenetic.pg
# afp_cellfunction.pg               afp_lsrnai.pg                     afp_review.pg
# afp_chemicals.pg                  afp_mappingdata.pg                afp_rgngene.pg
# afp_comment.pg                    afp_massspec.pg                   afp_rnai.pg
# afp_covalent.pg                   afp_microarray.pg                 afp_sequencechange.pg
# afp_expression.pg                 afp_mosaic.pg                     afp_sequencefeatures.pg
# afp_genefunction.pg               afp_nematode.pg                   afp_site.pg
# afp_geneinteractions.pg           afp_newmutant.pg                  afp_structurecorrectionsanger.pg
# afp_geneproduct.pg                afp_newsnp.pg                     afp_structureinformation.pg
# afp_generegulation.pg             afp_othersilico.pg                afp_supplemental.pg
# afp_genesymbol.pg                 afp_overexpression.pg             afp_transgene.pg

__END__


my @tables = qw( genesymbol mappingdata genefunction newmutant rnai lsrnai geneinteractions geneproduct expression sequencefeatures generegulation overexpression mosaic site microarray invitro covalent structureinformation structurecorrectionsanger sequencechange massspec ablationdata cellfunction phylogenetic othersilico chemicals transgene antibody newsnp rgngene nematode humandiseases supplemental review comment );

my @newtables = qw( matrices timeaction celegans cnonbristol nematode nonnematode nocuratable domanal structcorr structinfo genestudied extvariation funccomp otherexpr marker siteaction email genefunc geneint geneprod seqfeat genereg overexpr seqchange cellfunc humdis );

my @tomove = qw( rgngene functionalcomplementation structureinformation structurecorrection site timeofaction domainanalysis otherexpression genefunction geneinteractions geneproduct sequencefeatures generegulation overexpression sequencechange cellfunction humandiseases );

my %moveHash;
# to delete
$moveHash{'siteofaction'} = 'siteaction';
$moveHash{'timeofaction'} = 'timeaction';
$moveHash{'domainanalysis'} = 'domanal';
$moveHash{'otherexpression'} = 'otherexpr';
$moveHash{'fxncomp'} = 'funccomp';
$moveHash{'genefunction'} = 'genefunc';
$moveHash{'geneinteractions'} = 'geneint';
$moveHash{'geneproduct'} = 'geneprod';
$moveHash{'sequencefeatures'} = 'seqfeat';
$moveHash{'generegulation'} = 'genereg';
$moveHash{'overexpression'} = 'overexpr';
$moveHash{'sequencechange'} = 'seqchange';
$moveHash{'cellfunction'} = 'cellfunc';
$moveHash{'humandiseases'} = 'humdis';

# foreach my $table (keys %moveHash) {
#   my $result = $conn->exec( "DROP TABLE afp_$table " );
#   $result = $conn->exec( "DROP TABLE afp_${table}_hst " );
# } # foreach my $table (keys %moveHash)

# to move
# $moveHash{'site'} = 'siteaction';
# $moveHash{'overexpression'} = 'overexpr';
# $moveHash{'genefunction'} = 'genefunc';
# $moveHash{'geneinteractions'} = 'geneint';
# $moveHash{'geneproduct'} = 'geneprod';
# $moveHash{'sequencefeatures'} = 'seqfeat';
# $moveHash{'generegulation'} = 'genereg';
# $moveHash{'overexpression'} = 'overexpr';
# $moveHash{'sequencechange'} = 'seqchange';
# $moveHash{'cellfunction'} = 'cellfunc';
# $moveHash{'humandiseases'} = 'humdis';

# foreach my $table (keys %moveHash) {
#   my $new = $moveHash{$table}; $new = 'afp_' . $new;
#   my $result = $conn->exec( "COPY $new FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_${table}.pg'" );
#   $result = $conn->exec( "COPY ${new}_hst FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/afp_${table}.pg'" );
# }

# afp_ablationdata.pg      afp_geneproduct.pg     afp_mosaic.pg          afp_rgngene.pg
# afp_antibody.pg          afp_generegulation.pg  afp_nematode.pg        afp_rnai.pg
# afp_cellfunction.pg      afp_genesymbol.pg      afp_newmutant.pg       afp_sequencechange.pg
# afp_chemicals.pg         afp_humandiseases.pg   afp_newsnp.pg          afp_sequencefeatures.pg
# afp_comment.pg           afp_invitro.pg         afp_othersilico.pg     afp_site.pg
# afp_covalent.pg          afp_lsrnai.pg          afp_overexpression.pg  afp_structurecorrectionsanger.pg
# afp_expression.pg        afp_mappingdata.pg     afp_passwd.pg          afp_structureinformation.pg
# afp_genefunction.pg      afp_massspec.pg        afp_phylogenetic.pg    afp_supplemental.pg
# afp_geneinteractions.pg  afp_microarray.pg      afp_review.pg          afp_transgene.pg



my $table = 'afp_passwd_hst';
my $result = '';

# foreach my $table (@newtables) {
#   $table = 'afp_' . $table ;
#   $result = $conn->exec( "CREATE TABLE $table ( joinkey text, $table text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE UNIQUE INDEX ${table}_idx ON $table USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO cecilia; ");
#   my $table2 = $table . '_hst';
#   $result = $conn->exec( "CREATE TABLE $table2 ( joinkey text, $table2 text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE INDEX ${table2}_idx ON $table2 USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table2 FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table2 TO cecilia; ");
# }


# foreach my $table (@tables) {
#   $table = 'afp_' . $table;
#   $result = $conn->exec( "COPY $table TO '/home/postgres/work/pgpopulation/afp_papers/orig_tables/${table}.pg'" );
#   my $table2 = $table . '_hst';
#   $result = $conn->exec( "COPY $table2 FROM '/home/postgres/work/pgpopulation/afp_papers/orig_tables/${table}.pg'" );
# }

# # my $result = $conn->exec( "DROP TABLE $table" );
# $result = $conn->exec( "CREATE TABLE $table ( joinkey text, $table numeric(17,7), afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
# $result = $conn->exec( "CREATE INDEX ${table}_idx ON $table USING btree (joinkey);" );
# $result = $conn->exec("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO postgres; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO acedb; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO apache; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO azurebrd; ");
# $result = $conn->exec("GRANT ALL ON TABLE $table TO cecilia; ");
# 
# foreach my $table (@tables) {
#   $table = 'afp_' . $table . '_hst';
# #   $result = $conn->exec( "DROP TABLE $table" );
#   $result = $conn->exec( "CREATE TABLE $table ( joinkey text, $table text, afp_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
#   $result = $conn->exec( "CREATE INDEX ${table}_idx ON $table USING btree (joinkey);" );
#   $result = $conn->exec("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO postgres; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO acedb; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO apache; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO azurebrd; ");
#   $result = $conn->exec("GRANT ALL ON TABLE $table TO cecilia; ");
# }

__END__

my $result = $conn->exec( "SELECT * FROM one_groups;" );
while (my @row = $result->fetchrow) {
  if ($row[0]) { 
    $row[0] =~ s///g;
    $row[1] =~ s///g;
    $row[2] =~ s///g;
    print "$row[0]\t$row[1]\t$row[2]\n";
  } # if ($row[0])
} # while (@row = $result->fetchrow)



__DIVIDER__


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

my @generic_tables = qw( wpa wpa_identifier wpa_title wpa_publisher wpa_journal wpa_volume wpa_pages wpa_year wpa_date_published wpa_fulltext_url wpa_abstract wpa_affiliation wpa_type wpa_author wpa_hardcopy wpa_comments wpa_editor wpa_nematode_paper wpa_contained_in wpa_contains wpa_keyword wpa_erratum wpa_in_book );


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
  if ($row[0] eq 'invalid') { 
    my $identifier = ''; $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ '$number' ORDER BY wpa_timestamp;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $identifier = $row[0]; } else { $identifier = ''; } }
    print "<FONT COLOR='red' SIZE=+2>NOT a valid paper, merged with $identifier.</FONT><P>\n"; }
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
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>Author Name</TD><TD>Possible</TD><TD>Sent</TD><TD>Verified</TD></TR>\n";
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
    while (my @row = $result2->fetchrow) { $ceci_hash{$row[2]}{verified} = $row[1]; $ceci_hash{$row[2]}{valid} = $row[3]; }
    foreach my $join (sort keys %ceci_hash) {
      my $bgcolor = $blue; if ($ceci_hash{$join}{valid} eq 'invalid') { $bgcolor = $red; }
      my $possible = '&nbsp;'; my $sent = '&nbsp;'; my $verified = '&nbsp;';
      if ($ceci_hash{$join}{possible}) { $possible = $ceci_hash{$join}{possible}; }
      if ($ceci_hash{$join}{sent}) { $sent = $ceci_hash{$join}{sent}; }
      if ($ceci_hash{$join}{verified}) { $verified = $ceci_hash{$join}{verified}; }
      print "<TR bgcolor='$bgcolor'>";
      print "<TD>$auth_name{$auth_id}</TD><TD>$possible</TD><TD>$sent</TD><TD>$verified</TD>";
      print "<TR>\n";
    }
  } # foreach my $auth_id (@auth_id)
} # sub displayFullAuthor

sub displayOneDataFromKey {
  my $wpa_id = shift;
  my ($joinkey) = &padZeros($wpa_id);

  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR bgcolor='$blue'><TD bgcolor='white'>&nbsp;</TD><TD COLSPAN=5>ID : $joinkey</TD></TR>\n";
  print "<TR bgcolor='$blue'><TD ALIGN=CENTER>table</TD><TD ALIGN=CENTER>Data</TD><TD>Order</TD><TD>Valid</TD><TD>Curator</TD><TD>Timestamp</TD></TR>\n";
  my $counter = 0;
  my $erratum = 0; my $in_book = 0;
  my $result = $dbh->prepare( "SELECT * FROM cur_curator WHERE joinkey = '$joinkey';" );
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
  print "Link to WormBase : <A HREF=http://www.wormbase.org/db/misc/paper?name=WBPaper$joinkey;class=Paper TARGET=new>WBPaper$joinkey</A><BR>\n";
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

