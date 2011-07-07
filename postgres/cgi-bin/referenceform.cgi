#!/usr/bin/perl -w

# Direct queries to PostgreSQL database with sample and table list.

# Sample query (find most recent cgcs with pdfs)
# SELECT pdf.joinkey, pdf.pdf FROM pdf, cgc WHERE cgc.joinkey = pdf.joinkey AND
# pdf.pdf = '1' ORDER BY cgc.cgc DESC;
#
# updated to display the names of the tables and a sample query to show how
# many have data.
#
# updated to show ``Next Page !'' and ``Previous Page !'' buttons.  &Process()
# updated so if ``Next Page !'' or ``Previous Page !'' chosen, it reads the current
# page, and sets $page appropriately for &ProcessTable($page, $pgcommand);  2002 07 31
#
# create &printPageSelector($dividednumber, $page); to show the menu for 
# selecting a page  2002 07 31
#
# Added an entries per page selector for Andrei  2008 05 07
#
# Converted from Pg.pm to DBI.pm  2009 04 17



use strict;
use CGI;
use Fcntl;
# use HTML::Template;
use lib qw( /usr/lib/perl5/site_perl/5.6.1/i686-linux/ );
# use Pg;
use DBI;

my $query = new CGI;
our @RowOfRow;
my $MaxEntries = 20;
# our $pgcommand;		# my'ed everywhere

# my $conn = Pg::connectdb("dbname=testdb");
# die $conn->errorMessage unless PGRES_CONNECTION_OK eq $conn->status;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "");
if ( !defined $dbh ) { die "Cannot connect to database!\n"; }


# my $HTML_TEMPLATE_ROOT = "/home/postgres/public_html/cgi-bin/";

&PrintHeader();			# print the HTML header
&Process();
#    &PrintPgTable();
&ShowPgQuery();
&PrintFooter();			# print the HTML footer

sub PrintHeader {
  print <<"EndOfText";
Content-type: text/html\n\n

<HTML>
<LINK rel="stylesheet" type="text/css" href="http://www.wormbase.org/stylesheets/wormbase.css">
  
<HEAD>
<TITLE>Reference Data Query</TITLE>
</HEAD>
  
<BODY bgcolor=#aaaaaa text=#000000 link=cccccc alink=eeeeee vlink=bbbbbb>
<HR>
EndOfText
} # sub PrintHeader 

sub PrintFooter {
  print "</BODY>\n</HTML>\n";
} # sub PrintFooter 


sub PrintTableLabels {		# Just a bunch of table down entries
  print "<TR><TD>joinkey</TD><TD>author</TD><TD>title</TD><TD>journal</TD><TD>volume</TD><TD>pages</TD><TD>year</TD><TD>abstract</TD><TD>hardcopy</TD><TD>pdf</TD><TD>html</TD><TD>tif</TD><TD>lib</TD></TR>\n";
} # sub PrintTableLabels 

sub ShowPgQuery {
  print <<"EndOfText";
  <BR>Would you like to make a PostgreSQL Query to the Curation Database ?<BR>
  <FORM METHOD="POST" ACTION="referenceform.cgi">
  <TEXTAREA NAME="pgcommand" ROWS=5 COLS=80></TEXTAREA><BR>
  results per page (type all for all) <INPUT NAME="perpage" VALUE="20">
  <INPUT TYPE="submit" NAME="action" VALUE="Pg !">
  </FORM>
  <BR>These are the names of the curation tables : <BR>
  cur_ablationdata<BR>
  cur_antibody<BR>
  cur_associationequiv<BR>
  cur_associationnew<BR>
  cur_cellfunction<BR>
  cur_cellname<BR>
  cur_comment<BR>
  cur_covalent<BR>
  cur_curator<BR>
  cur_expression<BR>
  cur_extractedallelename<BR>
  cur_extractedallelenew<BR>
  cur_fullauthorname<BR>
  cur_functionalcomplementation<BR>
  cur_genefunction<BR>
  cur_geneinteractions<BR>
  cur_geneproduct<BR>
  cur_generegulation<BR>
  cur_genesymbol<BR>
  cur_genesymbols<BR>
  cur_goodphoto<BR>
  cur_invitro<BR>
  cur_lsrnai<BR>
  cur_mappingdata<BR>
  cur_massspec<BR>
  cur_microarray<BR>
  cur_mosaic<BR>
  cur_newmutant<BR>
  cur_newsnp<BR>
  cur_newsymbol<BR>
  cur_overexpression<BR>
  cur_rnai<BR>
  cur_sequencechange<BR>
  cur_sequencefeatures<BR>
  cur_site<BR>
  cur_stlouissnp<BR>
  cur_structurecorrection<BR>
  cur_structurecorrectionsanger<BR>
  cur_structurecorrectionstlouis<BR>
  cur_structureinformation<BR>
  cur_supplemental<BR>
  cur_synonym<BR>
  cur_transgene<BR>
  <BR>This sample query counts how many entries have data (for transgene) :
  <BR>SELECT * FROM cur_transgene WHERE cur_transgene IS NOT NULL;<BR>

EndOfText
}


sub Process {			# Essentially do everything
  my $action;			# what user clicked
  unless ($action = $query->param('action')) {
    $action = 'none';
  }
  if ($action eq 'Pg !') { 
    my $oop;
    if ( $query->param("pgcommand") ) { $oop = $query->param("pgcommand"); }
    else { $oop = "nodatahere"; }
    $oop =~ s/</&lt;/g; $oop =~ s/>/&gt;/g;
    my $pgcommand = &Untaint($oop);
    $pgcommand =~ s/&lt;/</g; $pgcommand =~ s/&gt;/>/g;
    if ( $query->param("perpage") ) { $oop = $query->param("perpage"); }
      else { $oop = "nodatahere"; }
    $oop =~ s/</&lt;/g; $oop =~ s/>/&gt;/g;
    my $perpage = &Untaint($oop);
    if ($perpage) { 
      if ($perpage =~ m/(\d+)/) { $MaxEntries = $1; } 
      elsif ($perpage =~ m/all/i) { $MaxEntries = 'all'; } }
    if ( $query->param("page") ) { $oop = $query->param("page"); }
    else { $oop = "1"; }
    my $page = &Untaint($oop);
    if ($pgcommand eq "nodatahere") { 
      print "You must enter a valid PG command<BR>\n"; 
    } else { # if ($pgcommand eq "nodatahere") 
#       my $result = $conn->exec( "$pgcommand" ); 
      if ( $pgcommand !~ m/select/i ) {
        my $result = $dbh->do( "$pgcommand" ); 
        print "PostgreSQL has processed it.<BR>\n";
        &ShowPgQuery();
      } else { # if ( $pgcommand !~ m/select/i ) 
#         &PrintTableLabels();
        &ProcessTable($page, $pgcommand);
      } # else # if ( $pgcommand !~ m/select/i ) 
    } # else # if ($pgcommand eq "nodatahere") 
  } # if ($action eq 'Pg !') 

  if ( ($action eq 'Page !') || ($action eq 'Next Page !') || ($action eq 'Previous Page !') ) {
    my $oop; my $page;
    if ( $query->param("pgcommand") ) { $oop = $query->param("pgcommand"); }
    else { $oop = "nodatahere"; }
    $oop =~ s/</&lt;/g; $oop =~ s/>/&gt;/g;
    my $pgcommand = &Untaint($oop);
    $pgcommand =~ s/&lt;/</g; $pgcommand =~ s/&gt;/>/g;
    if ( $query->param("perpage") ) { $oop = $query->param("perpage"); }
      else { $oop = "nodatahere"; }
    $oop =~ s/</&lt;/g; $oop =~ s/>/&gt;/g;
    my $perpage = &Untaint($oop);
    if ($perpage) { 
      if ($perpage =~ m/(\d+)/) { $MaxEntries = $1; } 
      elsif ($perpage =~ m/all/i) { $MaxEntries = 'all'; } }
    if ($action eq 'Page !') {		# if specific page, get the page
      if ( $query->param("page") ) { $oop = $query->param("page"); }
      else { $oop = "1"; }
      $page = &Untaint($oop);
    } # if ($action eq 'Page !')
    if ( ($action eq 'Next Page !') || ($action eq 'Previous Page !') ) {
					# if next or previous, get current and set page appropriately
      if ( $query->param("current_page") ) { $oop = $query->param("current_page"); }
      else { $oop = "1"; }
      $page = &Untaint($oop);
      if ($action eq 'Next Page !') { $page++; }
      if ($action eq 'Previous Page !') { $page--;  }
    } # if ( ($action eq 'Next Page !') || ($action eq 'Previous Page !') )
    &ProcessTable($page, $pgcommand);
  } # if ( ($action eq 'Page !') || ($action eq 'Next Page !') || ($action eq 'Previous Page !') )

} # sub Process

sub ProcessTable {
	# Take in pgcommand from hidden field or from Pg ! button
	# Take in page number from Page ! button or 1 as default
	# Process sql query 
	# Output number of results as well as sql query
	# output page selector as well as selected page results
    my $page = shift; my $pgcommand = shift;
#     my $result = $conn->exec( "$pgcommand" ); 
    my $result = $dbh->prepare( "$pgcommand" ); 
    $result->execute;
    my @row;
    @RowOfRow = ();
    while (@row = $result->fetchrow) {	# loop through all rows returned
      push @RowOfRow, [@row];
    } # while (@row = $result->fetchrow) 
    print "There are @{ [ $#RowOfRow + 1 ] } results to \"$pgcommand\".<BR>\n";

    if ($MaxEntries eq 'all') { 
        print "<TABLE border=1 cellspacing=5>\n";
        foreach my $i (0 .. $#RowOfRow) {
          print "<TR>";
          my $row = $RowOfRow[$i];
          for my $j ( 0 .. $#{$row} ) {
            print "<TD>$row->[$j]</TD>\n";
          } # for my $j ( 0 .. $#{$row} ) 
          print "</TR>\n";
        } # foreach my $row (@RowOfRow)
        print "</TABLE>\n"; }
      else {
        my $remainder = $#RowOfRow % $MaxEntries;
        my $HighNumber = $#RowOfRow - $remainder;
        my $dividednumber = $HighNumber / $MaxEntries;
        print "<FORM METHOD=\"POST\" ACTION=\"referenceform.cgi\">";
        &printPageSelector($dividednumber, $page);		# select page, next page, or previous page
        print "<INPUT TYPE=\"hidden\" NAME=\"pgcommand\" VALUE=\"$pgcommand\">\n";
        print "<INPUT TYPE=\"hidden\" NAME=\"perpage\" VALUE=\"$MaxEntries\">\n";
        print "<CENTER>\n";
        print "PAGE : $page<BR>\n";
        print "<TABLE border=1 cellspacing=5>\n";
        for my $i ( (($page-1)*$MaxEntries) .. (($page*$MaxEntries)-1) ) {
          print "<TR>";
          my $row = $RowOfRow[$i];
          for my $j ( 0 .. $#{$row} ) {
            print "<TD>$row->[$j]</TD>\n";
          } # for my $j ( 0 .. $#{$row} ) 
          print "</TR>\n";
        } # for my $i ( 0 .. $#RowOfRow ) 
        print "</TABLE>\n";
        print "PAGE : $page<BR>\n";
        print "</CENTER>\n";
        &printPageSelector($dividednumber, $page);		# select page, next page, or previous page
        print "</FORM>\n"; }
} # sub ProcessTable 

sub printPageSelector {			# part of the form, select page, next page, or previous page
    my ($dividednumber, $page) = @_;
    print "<TABLE>\n";
    print "<TD>Select your page of " . ($dividednumber + 1) . " : </TD><TD><SELECT NAME=\"page\" SIZE=5> \n"; 
    for my $k ( 1 .. ($dividednumber + 1) ) {
      print "<OPTION>$k</OPTION>\n";
    } # for my $k ( 0 .. $dividednumber ) 
    print "</SELECT></TD><TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Page !\"></TD><BR><BR>\n";

      # pass current page for previous and next
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"current_page\" VALUE=\"$page\">\n";	
      # unless last page, show ``Next Page !'' option.  unless first page, show ``Previous Page !'' option
    unless ($page == "@{ [ ($dividednumber + 1) ] }" ) { print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Next Page !\"></TD>\n"; }
    unless ($page == 1) { print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Previous Page !\"></TD>\n"; }
    print "</TABLE>\n";
} # sub printPageSelector


sub Untaint {
  my $tainted = shift;
  my $untainted;
  $tainted =~ s/[^\w\-.,;:?\/\\@#\$\%\^&*(){}[\]+=!~|' \t\n\r\f]//g;
  if ($tainted =~ m/^([\w\-.,;:?\/\\@#\$\%&\^*(){}[\]+=!~|' \t\n\r\f]+)$/) {
    $untainted = $1;
  } else {
    die "Bad data in $tainted";
  }
  return $untainted;
} # sub Untaint 


__END__ 

### DEPRECATED ###

# sub PrintPgTable {
#   my @ary;
# #   Pg::doQuery($conn, "select * from testreference where lib = '1'", \@ary);
#   Pg::doQuery($conn, "select * from testreference", \@ary);
#   print "<CENTER><TABLE border=1 cellspacing=5>\n";
#   &PrintTableLabels();
# #   my $result = $conn->exec( "SELECT * FROM testreference where lib = '1';" ); 
#   my $result = $conn->exec( "SELECT * FROM testreference;" ); 
#   my @row;
#   while (@row = $result->fetchrow) {	# loop through all rows returned
# # if ( ($row[0] =~ m/^cgc100/) || ($row[0] =~ m/^cgc200/) || ($row[0] =~ m/^cgc12/) ) {
#     if ($row[3] =~ m/Nature/) {
#       print "<TR>";
#       foreach $_ (@row) {
#         print "<TD>${_}&nbsp;</TD>\n";		# print the value returned
#       }
#       print "</TR>\n";
#     }
#   } # while (@row = $result->fetchrow) 
# #   for my $i ( 0 .. $#ary ) {
# #     print "<TR>";
# #     for my $j ( 0 .. $#{$ary[$i]} ) {
# #       print "<TD>$ary[$i][$j]</TD>";
# #     } # for my $j ( 0 .. $#{$ary[$i]} ) 
# #     print "</TR>\n";
# #   } # for my $i ( 0 .. $#ary ) 
#   &PrintTableLabels();
#   print "</TABLE></CENTER>\n";
# } # sub PrintPgTable 
