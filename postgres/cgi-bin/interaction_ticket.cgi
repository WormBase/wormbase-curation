#!/usr/bin/perl 

# get a new Interaction ticket (new ID)

# populate from interaction_acedb_dump_20080222.ace
# a list of all interaction IDs that exist in WB into a table that stores them
# as number.  as requested, for the amount requested, populate a hash with those
# values, then loop from 1 to highest value to get an array of numbers not in
# the hash, and for the amount requested shift values or created new values if
# the array becomes empty, and display the count, new ticket number, and curator
# requesting it.  2008 02 29
# 
# no longer fill in gaps data after switching to interaction OA  2010 11 29
#
# updated ID to 500000 and changed form to work like it did in mangolassi sandbox,
# but with DBI instead of Pg.pm  2011 01 06


use CGI;
use Fcntl;
use strict;
use Jex;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 


my $query = new CGI;

my %intxn;
my @intxn;
my $highest_intxn;

my $action;
unless ($action = $query->param('action')) {
  $action = 'none'; 
}

if ($action eq 'Ticket !') { 
    print "Content-type: text/plain\n\n"; 
    &getTickets(); }
  else { 
    &printHeader('Interaction Ticket');      # normal form view
    &process();
    &printFooter();
}

sub process {
  if ($action eq 'none') { &firstPage(); }
} # sub process

sub getTickets {
  &populateIntxn();
  my ($oop, $tickets) = &getHtmlVar($query, 'tickets');
  ($oop, my $curator) = &getHtmlVar($query, 'curator');
  unless ($curator) { print "ERROR : you must choose a curator name\n"; return; }
#   print "T $tickets T\n";
  for my $counter (1 .. $tickets) {
#     print "C $counter C\n";
    my ($ticket) = &getNewTicket();
    my $pad_ticket = &padZeros($ticket);
    print "COUNT $counter\tTICKET WBInteraction$pad_ticket\tCURATOR $curator\n";
    my $command = "INSERT INTO int_index VALUES ('$pad_ticket', '$ticket', '$curator');";
    my $result = $dbh->do( $command );
#     print "$command\n";
  }
} # sub getTickets

sub padZeros {
  my $ticket = shift;
  if ($ticket < 10) { $ticket = '000000' . $ticket; }
    elsif ($ticket < 100) { $ticket = '00000' . $ticket; }
    elsif ($ticket < 1000) { $ticket = '0000' . $ticket; }
    elsif ($ticket < 10000) { $ticket = '000' . $ticket; }
    elsif ($ticket < 100000) { $ticket = '00' . $ticket; }
    elsif ($ticket < 1000000) { $ticket = '0' . $ticket; }
  return $ticket;
} # sub padZeros

sub populateIntxn {
  my $pre_pad_to = 7000; 	# fill tickets up to 7000
  my $result = $dbh->prepare( "SELECT * FROM int_index;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow()) { 
    $intxn{$row[1]}++; 
    if ($highest_intxn < $row[1]) { $highest_intxn = $row[1]; } }
#   my $really_high = 999999999;
  my $really_high = $highest_intxn;
  for my $count (1 .. $pre_pad_to) { 1; }		# ignore these tickets
  for my $count ($pre_pad_to .. $really_high) {
    unless ($intxn{$count}) { push @intxn, $count; } }
} # sub populateIntxn

sub getNewTicket {
  $highest_intxn++; return $highest_intxn; 
# no longer fill in gaps data after switching to interaction OA  2010 11 29
#   if (scalar(@intxn) > 0) { my $ticket = shift @intxn; return $ticket; }
#     else { $highest_intxn++; return $highest_intxn; }

#   my $really_high = 999999999;
#   for my $count (1 .. $really_high) {
# # print "C $count T\n";
#     unless ($intxn{$count}) { $intxn{$count}++; return $count; } }
} # sub getNewTicket

sub firstPage {
  print "<FORM METHOD=\"POST\" ACTION=\"interaction_ticket.cgi\">";
  print "<TABLE>\n";
  print "<TR><TD>Select your Name among : </TD><TD ALIGN=\"right\"><SELECT NAME=\"curator\" SIZE=4>\n";
  print "<OPTION VALUE=\"two22\">Igor Antoshechkin</OPTION>\n";
  print "<OPTION VALUE=\"two480\">Andrei Petcherski</OPTION>\n";
  print "<OPTION VALUE=\"two557\">Gary Schindelman</OPTION>\n";
  print "<OPTION VALUE=\"two1823\">Juancarlos Testing</OPTION>\n";
  print "</SELECT></TD></TR>";
  print "<TR><TD ALIGN=\"right\">How many tickets would you like :</TD>";
  print "<TD ALIGN=\"right\"><INPUT NAME=tickets VALUE=1 SIZE=10>\n";
  print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Ticket !\"></TD></TR><BR><BR>\n";
  print "</TABLE>\n";
  print "</FORM>\n";
} # sub ChoosePhenotypeAssay



__END__
