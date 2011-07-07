#!/usr/bin/perl -w

# Display gene class data

# Get gene_class_info.txt file from Karen's dropbox.  Get mapping of wbgenes to loci (not synonyms).  
# Get concise descriptions from car_concise, convert wbgene to locus, loop through gene classes and
# if the locus matches <word boundary>gene_class<word boundary>, assign to this word boundary.  
# Filter all concise descriptions by frequency and join with html <br> element.
# Display all gene classes, description, gene count (from file), concise count (unique), concise 
# descriptions, lab, rep
# Doesn't loop through all loci because that takes forever.
# For Karen / Uma.  2011 04 22



use strict;
use CGI;
use DBI;
use Jex;
use LWP::Simple;

my $starttime = time;

my $query = new CGI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
my $result;

my %gc;

sub getGc {
  my $gc_url = 'http://dl.dropbox.com/u/5135566/gene_class_info.txt';
  my $gc_data = get( $gc_url );
#   my (@gc_data) = split/\n/, $gc_data;
  my (@gc_data) = split//, $gc_data;
  shift @gc_data; shift @gc_data;		# skip headers
  foreach my $line (@gc_data) {
    my ($gc, $desc, $count, $a, $lab, $rep) = split/\t/, $line;
    $gc{$gc}{desc} = $desc;
    $gc{$gc}{file_gene_count} = $count;
    $gc{$gc}{lab} = $lab;
    $gc{$gc}{rep} = $rep;
  } #foreach my $line (@gc_data)

  my %wbgToLocus;
  $result = $dbh->prepare( "SELECT * FROM gin_locus" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $wbgToLocus{"WBGene$row[0]"} = $row[1]; }

  my %has_concise;
  my %conciseByGc;
  $result = $dbh->prepare( "SELECT * FROM car_concise" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { 
    $has_concise{$row[0]}++; 
    my $locus = $wbgToLocus{$row[0]};
# print "HERE $locus R $row[0] R @row\n";
    next unless $locus;
    my $thisGc = '';
    foreach my $gc (keys %gc) { if ($locus =~ m/\b$gc\b/) { $thisGc = $gc; last; } }
# print "HERE T $thisGc V $row[1] E\n";
    next unless $thisGc;
    $conciseByGc{$thisGc}{$row[1]}++;
  }
  foreach my $gc (sort keys %conciseByGc) {
    my $concise = join"<br />", sort { $conciseByGc{$gc}{$b} <=> $conciseByGc{$gc}{$a} } keys %{ $conciseByGc{$gc} };
    $gc{$gc}{concise} = $concise;
    my $concise_count = scalar keys %{ $conciseByGc{$gc} };
    $gc{$gc}{concise_count} = $concise_count;
  } # foreach my $gc (sort keys %conciseByGc)

  my $count = 0;

#   foreach my $gc (sort keys %gc) {
# #     $count++; last if ($count > 150);
#     my %genes; my @loci; my %concise;
#     $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE gin_locus ~ '$gc'" );	# this takes forever for all gc
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#     while (my @row = $result->fetchrow) {
#       if ($row[1] =~ m/\b$gc\b/) { push @loci, $row[1]; $genes{"WBGene$row[0]"}++; } }
#     next;
#     my $loci = join", ", @loci;
#     $gc{$gc}{loci} = $loci;
#     my $genes = join", ", sort keys %genes;
#     $gc{$gc}{genes} = $genes;
#     my $genes_count = scalar keys %genes;
#     $gc{$gc}{genes_count} = $genes_count;
# #     next if ($genes_count > 1000);
#     $result = $dbh->prepare( "SELECT * FROM car_concise WHERE joinkey IN ('$genes')" );
# #     print "SELECT * FROM car_concise WHERE joinkey IN ('$genes');\n"; 
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#     while (my @row = $result->fetchrow) {
#       $concise{$row[1]}++; }
#     my $concise = join"<br />", sort keys %concise;
#     $gc{$gc}{concise} = $concise;
#     my $concise_count = scalar keys %concise;
#     $gc{$gc}{concise_count} = $concise_count;
#   } # foreach my $gc (sort keys %gc)
}
  

&printHeader('Gene class display');
&display();
&printFooter();

sub display {
  &getGc();
  my $td = "td valign=\"top\" style=\"border-style: dotted\"";
  print "<table border=\"1\">\n";
  print "<tr><$td>gene class</td><$td>gene class description</td><$td>gene count</td><$td>concise count</td><$td>concise descriptions by frequency</td><$td>lab</td><$td>rep</td></tr>\n";
#   foreach my $gc (sort keys %gc) { unless ($gc{$gc}{genes_count}) { $gc{$gc}{genes_count} = 0; } }
#   foreach my $gc (sort { $gc{$b}{genes_count} <=> $gc{$a}{genes_count} } keys %gc) 
  foreach my $gc (sort { $gc{$b}{file_gene_count} <=> $gc{$a}{file_gene_count} } keys %gc) {
    my ($count, $lab, $rep, $loci, $file_gene_count, $genes_count, $concise, $concise_count, $gc_desc) = ('', '', '', '', '', '', '', '', '');
    $count = $gc{$gc}{count};
    $gc_desc = $gc{$gc}{desc};
    $lab = $gc{$gc}{lab};
    $rep = $gc{$gc}{rep};
    $loci = $gc{$gc}{loci};
#     $genes = $gc{$gc}{genes};
    $file_gene_count = $gc{$gc}{file_gene_count};
    if ($gc{$gc}{genes_count}) { $genes_count = $gc{$gc}{genes_count}; }
    if ($gc{$gc}{concise}) { $concise = $gc{$gc}{concise}; }
    if ($gc{$gc}{concise_count}) { $concise_count = $gc{$gc}{concise_count}; }
#     print "<tr><td>$gc</td><td>$count</td><td>$lab</td></tr>\n";
#     print "<tr><td>$gc</td><td>$loci</td><td>$genes</td><td>$lab</td></tr>\n";
    print "<tr><$td>$gc</td><$td>$gc_desc</td><$td>$file_gene_count</td><$td>$concise_count</td><$td>$concise</td><$td>$lab</td><$td>$rep</td></tr>\n";
  }
  print "</table>\n";
}


__END__

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

