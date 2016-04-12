#!/usr/bin/perl

# From to submit Meeting Abstract information.

# for meeting organizers to request authors to send abstract information in a format we can use.
# 2010 02 12
#
# renamed corresponding to presenting.  Added more text from Kimberly.  2010 02 16
#
# changed things for Kimberly and Cecilia, adding more atomized fields.  2010 02 25

# sample
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/meeting_abstracts.cgi?meeting_name=2010+Caenorhabditis+evolution+meeting



use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;
# use Ace;
use DBI;
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my $blue = '#00ffcc';                   # redefine blue to a mom-friendly color
my $red = '#00ffff';                    # redefine red to a mom-friendly color


my $query = new CGI;
my $firstflag = 1;

my %flags;				# hack to have flags.

my $n_authors = '20';			# amount of author fields

my $data_file = '/home/azurebrd/public_html/cgi-bin/data/meeting_abstracts.txt';

print "Content-type: text/html\n\n";
my $title = 'Meeting Abstract Submission Form';
my ($header, $footer) = &cshlNew($title);
print "$header\n";		# make beginning of HTML page

&process();			# see if anything clicked
print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'Submit') {
    open (OUT, ">>$data_file") or die "Cannot append to $data_file : $!";
    my %authors;
    print "Thank you for your Meeting Abstract submission.<br /><br />\n";
    (my $oop, my $meeting_name) = &getHtmlVar($query, 'meeting_name');
    ($oop, my $presenting_name) = &getHtmlVar($query, 'presenting_name');
    ($oop, my $presenting_email) = &getHtmlVar($query, 'presenting_email');
    ($oop, my $title) = &getHtmlVar($query, 'title');
    for my $i (1 .. $n_authors) {
      ($oop, my $author_f) = &getHtmlVar($query, "author_f_$i");
      ($oop, my $author_m) = &getHtmlVar($query, "author_m_$i");
      ($oop, my $author_l) = &getHtmlVar($query, "author_l_$i");
      ($oop, my $author_a) = &getHtmlVar($query, "author_a_$i");
      ($oop, my $person) = &getHtmlVar($query, "person_$i");
      if ($author_l) { $authors{$i}{author} = "$author_f\t$author_m\t$author_l\t$person\t$author_a"; }
#       if ($person) { $authors{$i}{author} .= "$person"; }
    }

    ($oop, my $abstract) = &getHtmlVar($query, 'abstract');
    my $output = '';
    $output .= "Meeting Name\t$meeting_name\n";
    $output .= "Presenting author name\t$presenting_name\n";
    $output .= "Presenting author email\t$presenting_email\n";
    $output .= "Title\t$title\n";
    foreach my $i (sort {$a<=>$b} keys %authors) {
      if ($authors{$i}{author}) { 
        $output .= "Author\t$authors{$i}{author}\n"; }
    }
    $output .= "Abstract\t$abstract\n";
    if ($output =~ m//) { $output =~ s///g; }
    print OUT "$output\n\nDIVIDER\n\n\n";
    close (OUT) or die "Cannot close $data_file : $!";
    $output =~ s/\n/<br \/>/g;
    $output =~ s/\t/ : /g;
    print "$output\n";
  } # if ($action eq 'Query') 
  else {			# by default, no action
    &displayForm();		# display blank form
  }
} # sub process



sub displayForm {
#   print "<p><b>Thank you for submitting your meeting abstract to WormBase.  Using this submission form will expedite getting meeting abstracts into WormBase, allowing us to release abstracts on the WormBase website within a month after the meeting.</b></p>\n";
# 
#   print "<p>Please enter Abstract information, including Authors as they're listed in the abstract.  Optionally look up the WBPerson ID so that we may verify your publication without manually connecting it and sending you a verification email.  The WormBase Person update form is <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi\" target=\"new\">here</a>.</p>\n";
  (my $oop, my $meeting_name) = &getHtmlVar($query, 'meeting_name');

  unless ($meeting_name) { print "This meeting name is not approved, please contact the meeting organizers.<br />\n"; return; }

  print "<p>Thank you for submitting your meeting abstract to WormBase. Using this
submission form will expedite getting meeting abstracts into WormBase,
allowing us to release abstracts on the WormBase website within a month
after the meeting.</p>\n";

  print "<p>Please enter Abstract information, including the title and the Authors,
<b>exactly</b> as they appear in the abstract.</p>\n";

  print "<p>For each author, you may optionally look up the corresponding WormBase
Person ID so that we can verify an author’s publications without manually
connecting it and sending a verification email.  A link to the WormBase
Person ID look-up form is provided below.</p>\n";

  if ($meeting_name eq '2010 Caenorhabditis evolution meeting') {
    print "<p>Meeting: Evolutionary Biology of Caenorhabditis and Other Nematodes<br />\n";
    print "Saturday 5th – Tuesday 8th June 2010 Wellcome Trust Conference<br />\n";
    print "Centre Wellcome Trust Genome Campus, Hinxton, Cambridge<br /></p>\n";
  }


  my $size = "15";	# input size

  print "<form method=post action=meeting_abstracts.cgi>\n";
  print "<input type=\"hidden\" name=\"meeting_name\" value=\"$meeting_name\">\n";
  print "<table border=0 cellspacing=2>\n";
#   print "<tr><td>Meeting Name</td>";
#   if ($meeting_name) { 
#       print "<td colspan=\"3\">$meeting_name</td>\n";
#       print "<input type=\"hidden\" name=\"meeting_name\" value=\"$meeting_name\">\n"; }
#     else {
#       print "<td colspan=\"3\"><input size=\"120\" name=\"meeting_name\"></td>\n"; }
  print "<tr><td colspan=\"1\">Presenting Author Surname</td><td><input size=\"$size\" name=\"presenting_name\"></td>\n";
  print "<td colspan=\"1\" align=\"right\">Presenting Author Email</td><td colspan=\"1\"><input size=\"60\" name=\"presenting_email\"></td></tr>\n";
  print "<tr><td>Title</td><td colspan=\"3\"><input size=\"120\" name=\"title\"></td></tr>\n";
  print "<tr><td>Abstract</td><td colspan=\"3\"><textarea rows=20 cols=100 name=\"abstract\"></textarea></td></tr>\n";
  print "</table><br />\n";
  print "<table border=0 cellspacing=2>\n";
  for my $i (1 .. $n_authors) {
    print "<tr><td>&nbsp;</td></tr>\n";
    print "<tr>";
    print "<td align=\"right\">Author $i Forename</td><td><input size=\"$size\" name=\"author_f_$i\"></td>\n";
    print "<td align=\"right\">Middle Name</td><td><input size=\"$size\" name=\"author_m_$i\"></td>\n";
    print "<td align=\"right\">Surname</td><td><input size=\"$size\" name=\"author_l_$i\"></td>\n";
    print "<td align=\"right\">WBPersonID (Optional)</td><td><input name=\"person_$i\"><a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person.cgi\" target=\"new\">look up</a></td></tr>\n";
    print "<tr><td align=\"right\">Author $i Affiliation</td><td colspan=\"7\"><input size=\"150\" name=\"author_a_$i\"></td></tr>\n";
  }
  
  print "</table><br /><br />\n";
  print "<input type=\"submit\" name=\"action\" value=\"Submit\">\n";
  print "</form>\n";
}

