#!/usr/bin/perl -w

# Display svm results

# Look at caprica's <dates>/ directories and get paper-type-result mappings.  
# Sparked by Karen's frustration without her request.  2011 04 14


use strict;
use CGI;
use DBI;
use Jex;
use LWP::Simple;

my $starttime = time;

my $query = new CGI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";

my %hash;
my %byPaper;

my %journal;
my $result = $dbh->prepare( "SELECT * FROM pap_journal WHERE pap_journal IS NOT NULL" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) {
  if ($row[0]) { 
    $journal{$row[0]} = $row[1];
  } # if ($row[0])
} # while (@row = $result->fetchrow)



&printHeader('Caprica SVM summary');
&display();
&printFooter();


sub display {
  my $root_url = 'http://caprica.caltech.edu/celegans/svm_results/';
  print "Display of data from date directories from $root_url<br />\n";

  my $count = 0;
  my $root_page = get $root_url;
#   print "R $root_page\n";
  my (@dates) = $root_page =~ m/<a href=\"(\d+\/)\">/g;
  foreach my $date (@dates) {
#     $count++; last if ($count > 4);
    my $date_url = $root_url . $date;
#     print "<a href=$date_url>$date_url</a><br />\n";
    my $date_page = get $date_url;
# print "$date_page\n";
    my (@date_types) = $date_page =~ m/<a href=\"(\w+)\"/g;
    foreach my $date_type (@date_types) {
      my ($type) = $date_type =~ m/^[\d_]+_(\w+)$/;
#       print $type;
      my $date_type_url = $date_url . $date_type;
#       print "<a href=$date_type_url>$date_type_url</a><br />\n";
      my $date_type_results_page = get $date_type_url;
      my (@results) = split/\n/, $date_type_results_page;
      foreach my $result (@results) { 
        if ($result =~ m/\"/) { $result =~ s/\"//g; }
        my ($paper, $flag) = split/\t/, $result;
        next unless ($paper =~ m/^WBPaper/);
        $byPaper{$paper}{$type} = $flag;
        $hash{$type}{$paper} = $flag;
        $hash{all}{$paper}++;
      }
    } # foreach my $type (@types)
    my $fn_date_url = $date_url . 'checkFalseNegatives/';
    my $fn_date_page = get $fn_date_url;
    my (@fn_date_types) = $fn_date_page =~ m/<a href=\"(\w+)\"/g;
    foreach my $fn_date_type (@fn_date_types) {
      my ($type) = $fn_date_type =~ m/^[\d_]+_checkFN_(\w+)$/;
#       print $type;
      my $fn_date_type_url = $fn_date_url . $fn_date_type;
#       print "<a href=$fn_date_type_url>$fn_date_type_url</a><br />\n";
      my $fn_date_type_results_page = get $fn_date_type_url;
      my (@results) = split/\n/, $fn_date_type_results_page;
      foreach my $paper (@results) { 
        next unless ($paper =~ m/^WBPaper/);
        my $flag = 'NEG';
        $byPaper{$paper}{$type} = 'NEG';
        $hash{$type}{$paper} = $flag;
        $hash{all}{$paper}++;
      }
    } # foreach my $type (@types)
  } # foreach my $subdir (@subdirs)

print "journal filter : <input id=\"journal_filter\" onKeyUp=\"filterData('journal_filter')\">\n";
# print "paper filter : <input id=\"paper_filter\" onKeyUp=\"filterData('paper_filter')\"><br /><br />\n";
print "<div id=\"bug\"></div>\n";
  print << "EndOfText";
<script type="text/javascript" language="JavaScript">
function filterData(column) {
  var message = '';
// message += column;
  var columnFilter = document.getElementById(column).value;
//   var journalFilter = document.getElementById('journal_filter').value;
  var regexColumn = new RegExp(columnFilter, "i")
  var arrTd = document.getElementsByTagName("td");
  for (var i = 0; i < arrTd.length; i++) {
    if (arrTd[i].className) {
      var className = arrTd[i].className;
// message += "match className " + className + " ";
      if (className.match(regexColumn)) { arrTd[i].parentNode.style.display = ""; }
        else { arrTd[i].parentNode.style.display = "none"; }
    }
  }
  document.getElementById("bug").innerHTML = message;
//   alert(journal_filter);
}
</script>
EndOfText

  print "<table border=\"1\">\n";
  print "<tr><td style=\"border-style: dotted\">paper</td><td style=\"border-style: dotted\">journal</td><td style=\"border-style: dotted\">data</td></tr>\n";
  foreach my $paper (sort keys %byPaper) {
    print "<tr><td style=\"border-style: dotted\">$paper</td>";
    my ($joinkey) = $paper =~ m/(\d+)/;
    if ($journal{$joinkey}) { print "<td style=\"border-style: dotted\" class=\"$journal{$joinkey}\">$journal{$joinkey}</td>"; } else { print "<td>&nbsp;</td>"; }
    foreach my $type (sort keys %{ $byPaper{$paper} }) {
      next unless ($type);
      my $bgcolor = 'white';
      my $result = $byPaper{$paper}{$type};
      if ($result eq 'high')   { $bgcolor = '#FFa0a0'; }
      if ($result eq 'medium') { $bgcolor = '#FFc8c8'; }
      if ($result eq 'low')    { $bgcolor = '#FFe0e0'; }
      print "<td style=\"border-style: dotted; background-color: $bgcolor\">$type - $result</td>";
    } # foreach my $type (sort keys %{ $byPaper{$paper} })
    print "</tr>\n";
  } # foreach my paper (sort keys %byPaper)
  print "</table>\n";

#   foreach my $type (sort keys %hash) {
#     next unless ($type);
#     next if ($type eq 'all');
# #     print "<a href=\"#$type\">$type<\a> ";
#   }
#   print "<br /><br />\n";

#   print "<table>\n";
#   foreach my $paper (sort keys %{ $hash{all} }) {
# #     print "$paper has been flagged for svm $hash{all}{$paper} times<br />\n";
#     print "<tr><td>$paper</td><td>$hash{all}{$paper}</td></tr>\n";
#   } # foreach my $paper (sort keys %{ $hash{all} })
#   print "</table>\n";

#   print "<br /><br />\n";
#   foreach my $type (sort keys %hash) {
#     next unless ($type);
#     next if ($type eq 'all');
#     print "<a name=\"$type\">Type : $type</a><br />\n";
#     foreach my $paper (sort keys %{ $hash{$type} }) {
#       print "$paper\t$hash{$type}{$paper}<br />\n";
#     }
#     print "<br /><br />\n";
#   } # foreach my $type (sort keys %hash)
}

__END__

#!/usr/bin/perl -w

# sample PG query

use strict;
use diagnostics;
use DBI;
use Encode qw( from_to is_utf8 );

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

