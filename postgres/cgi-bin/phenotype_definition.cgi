#!/usr/bin/perl -w

# Suggest Phenotype Definitions to Gary

 


use strict;
use CGI;
use DBI;
use Jex;
# use LWP::UserAgent;
use LWP::Simple;
# use POSIX qw(ceil);



my $query = new CGI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $frontpage = 1;
my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color


my %theHash;
my %obo;
my $suggested_file = '/home/postgres/public_html/cgi-bin/data/phenotype_suggestions.txt';

my %curators;				# $curators{two}{two#} = std_name ; $curators{std}{std_name} = two#

&printHeader('Phenotype Suggestion');
&display();
&printFooter();


### DISPLAY ###

sub display {
  my $action;

  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); return; }
  } else { $frontpage = 0; }

  print "<FORM NAME='form1' METHOD=\"POST\"
ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_definition.cgi\">\n"; my ($oop, $curator) = &getHtmlVar($query, 'curator_name');
  if ($curator) { 
    $theHash{curator} = $curator;
    print "Curator : $curator<P>\n"; 
    print "<INPUT TYPE=\"HIDDEN\" NAME=\"curator_name\" VALUE=\"$theHash{curator}\">\n"; }
  else { print "<FONT COLOR='red'>ERROR : You must choose a curator.<BR>\n"; return; }

  if ($action eq 'Enter New Definitions !') { &newDefinitions(); }
  elsif ($action eq 'Suggest !') { &suggest(); }
  elsif ($action eq 'Guidelines !') { &showGuidelines(); }
  else { 1; }
  print "</FORM>\n";
} # sub display

sub suggest {
  my ($oop, $count) = &getHtmlVar($query, 'amount');
  print "COUNT $count<BR>\n";
  my @data; my @errors;
  for my $i (0 .. $count) { 
    ($oop, my $checked) = &getHtmlVar($query, "check_$i");
    if ($checked) { 
      ($oop, my $id) = &getHtmlVar($query, "id_$i");
      if ($id) { unless ($id =~ m/^\d{7}$/) { push @errors, "$id doesn't have exactly 7 digits"; } }
        else { push @errors, "no id for checkbox $i"; }
      ($oop, my $suggest) = &getHtmlVar($query, "suggest_$i");
      ($oop, my $evidence) = &getHtmlVar($query, "evidence_$i");
      push @data, "$id\t$suggest\t$theHash{curator}\t$evidence"; }
  } # for (0 .. $i)
  print "<P>\n";
  if ($errors[0]) { print "<FONT COLOR=red>ERROR no data submitted :</FONT><BR>\n"; foreach my $error (@errors) { print "$error<BR>\n"; } }
    else { 
      open (OUT, ">>$suggested_file") or die "Cannot append to $suggested_file : $!";
      foreach my $data (@data) {
        print OUT "$data\n";
        print "$data<BR>\n";
      }
      close (OUT) or die "Cannot close $suggested_file : $!";
      my $user = 'phenotype_definition.cgi';
      my $email = 'garys@its.caltech.edu';
#       my $email = 'azurebrd@tazendra.caltech.edu';
      my $subject = "$theHash{curator} suggested phenotype definitions";
      my $body = join"\n", @data;
      &mailer($user, $email, $subject, $body);
    }
} # sub suggest

sub newDefinitions {
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Suggest !\">\n";
  print "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_definition.cgi?action=Guidelines+%21&curator_name=$theHash{curator}=\" TARGET=new>Guidelines</A><BR><BR>\n";
  my $obofile = get "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/phenotype_ontology_obo.cgi";
  my (@terms) = split/\[Term\]/, $obofile;
  foreach my $term (@terms) {
    if ($term =~ m/id: WBPhenotype:(\d+)/) {
      my $id = $1;
      my ($name) = $term =~ m/name: (\w+)/;
      my ($def) = $term =~ m/def: \"(.*?)\"/;
      unless ($def) { $obo{$id}{name} = $name; }
    }
  } # foreach my $term (@terms)
  my %suggested; my @suggested;
  open (IN, "$suggested_file") or die "Cannot open $suggested_file : $!";
  while (my $line = <IN>) {
    chomp $line;
    my ($id, $sug, $cur, $evi) = split/\t/, $line;
    $suggested{$id}{sug} = $sug;
    $suggested{$id}{evi} = $evi;
  } # while (my $line = <IN>)
  close (IN) or die "Cannot close $suggested_file : $!";
  my $count = 0;
  print "<TABLE border=0 cellspacing=2>\n";
  print "<TR><TD ALIGN=CENTER>id</TD><TD ALIGN=CENTER>name</TD><TD ALIGN=CENTER>suggested definition</TD><TD ALIGN=CENTER>evidence</TD></TR>\n";
  print "<TD><INPUT NAME=\"id_$count\" SIZE=20></TD>\n";
#   print "<TD><INPUT NAME=\"name_$count\" SIZE=60></TD>\n";
  print "<TD>&nbsp;</TD>\n";
#   print "<TD><INPUT NAME=\"suggest_$count\" SIZE=20></TD>\n";
  print "<TD><TEXTAREA NAME=\"suggest_$count\" ROWS=4 COLS=60></TEXTAREA></TD>\n";
  print "<TD><INPUT NAME=\"evidence_$count\" SIZE=20></TD>\n";
  print "<TD ALIGN='CENTER'><INPUT NAME=\"check_$count\" TYPE=CHECKBOX VALUE=\"valid\"></TD>\n"; 
  print "</TR>\n";
  foreach my $id (sort keys %obo) {
    $count++;
    my $name = $obo{$id}{name};
    my $line = '';
    $line .= "<TR><TD>$id</TD><TD>$name</TD>\n";
    $line .= "<TD><TEXTAREA NAME=\"suggest_$count\" ROWS=4 COLS=60>";
    if ($suggested{$id}{sug}) { $line .= "$suggested{$id}{sug}"; }
    $line .= "</TEXTAREA></TD>\n";
#     $line .= "<TD><INPUT NAME=\"suggest_$count\" SIZE=20";
#     if ($suggested{$id}{sug}) { $line .= " VALUE=\"$suggested{$id}{sug}\""; }
#     $line .= "></TD>\n";
    $line .= "<TD><INPUT NAME=\"evidence_$count\" SIZE=20";
    if ($suggested{$id}{evi}) { $line .= " VALUE=\"$suggested{$id}{evi}\""; }
    $line .= "></TD>\n";
    $line .= "<TD ALIGN='CENTER'><INPUT NAME=\"check_$count\" TYPE=CHECKBOX VALUE=\"valid\"></TD>\n"; 
    $line .= "<INPUT TYPE=\"HIDDEN\" NAME=\"id_$count\" VALUE=\"$id\">\n";
    $line .= "</TR>\n";
    if ($suggested{$id}{sug}) { push @suggested, $line; } else { print $line; }
  } # foreach my $id (sort keys %obo)
  print "<TR><TD COLSPAN=4>These already have suggested definitions</TD></TR>\n";
  foreach my $line (@suggested) { print $line; }
  print "</TABLE>\n";
  print "<INPUT TYPE=\"HIDDEN\" NAME=\"amount\" VALUE=\"$count\">\n";
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Suggest !\">\n";
  print "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_definition.cgi?action=Guidelines+%21&curator_name=$theHash{curator}=\" TARGET=new>Guidelines</A><BR><BR>\n";
} # sub newDefinitions


### FIRST PAGE ###

sub firstPage {
  my $date = &getDate();
  print "Value : $date<BR>\n";
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/phenotype_definition.cgi\">\n";
  print "<TABLE>\n";
  print "<TR><TD VALIGN=TOP>Select your Name among : <BR>\n";
  print "<INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Enter New Definitions !\"></TD>\n";
  print "<TD VALIGN=TOP><SELECT NAME=\"curator_name\" SIZE=14>\n";
  print "<OPTION>Igor Antoshechkin</OPTION>\n";
  print "<OPTION>Juancarlos Chan</OPTION>\n";
  print "<OPTION>Wen Chen</OPTION>\n";
  print "<OPTION>Jolene S. Fernandes</OPTION>\n";
  print "<OPTION>Ranjana Kishore</OPTION>\n";
  print "<OPTION>Raymond Lee</OPTION>\n";
  print "<OPTION>Tuco</OPTION>\n";
  print "<OPTION>Gary C. Schindelman</OPTION>\n";
  print "<OPTION>Erich Schwarz</OPTION>\n";
  print "<OPTION>Paul Sternberg</OPTION>\n";
  print "<OPTION>Mary Ann Tuli</OPTION>\n";
  print "<OPTION>Kimberly Van Auken</OPTION>\n";
  print "<OPTION>Xiaodong Wang</OPTION>\n";
  print "<OPTION>Karen Yook</OPTION>\n";
  print "</SELECT></TD>\n";
#   print "<TD><INPUT TYPE=\"submit\" NAME=\"action\" VALUE=\"Enter New Definitions !\"></TD></TR><BR><BR>\n";
  print "<TD>";
  &showGuidelines();
  print "</TD>";
  print "</TABLE>\n";
} # sub firstPage

sub showGuidelines {
  print "Guidelines for writing definitions (we've included examples below)<BR>";
  print "<BR>";
  print "1. Make the definition species-unbiased, the ontology needs to accommodate nematodes other than C. elegans var. Bristol (N2); in most cases this is easily dealt with by using \"....compared to control animals\" rather than compared to \"normal\" or \"wild-type\" See example A.<BR>";
  print "<BR>";
  print "2. Check that the definition encompasses all of its children terms.<BR>";
  print "See example B.<BR>";
  print "<BR>";
  print "3. Where possible, please include the WBPaperID or other source ID (i.e. WormBook, GO term ID term, etc.) with your definition. Your WBPersonID will be appended to the definition through the submission form.<BR>";
  print "<BR>";
  print "4. Consider higher level/parent terms as a source for definition design. See Example B.<BR>";
  print "<BR>";
  print "5. If you notice it missing, please add a synonym or common name term a term as a note to your definition.<BR>";
  print "<BR>";
  print "6. Please avoid writing definitions that only repeat the words in the term name. See example C.<BR>";
  print "<BR>";
  print "<BR>";
  print "Examples:<BR>";
  print "<BR>";
  print "A. WBPhenotype:0001728 mating_plug_production_abnormal<BR>";
  print "DEF \"Males differ from control animals in their ability to form copulatory plugs.\"<BR>";
  print "<BR>";
  print "B. The physiology_abnormal term has 4 direct children terms:<BR>";
  print "cell_physiology_abnormal, organ_system_physiology_abnormal,<BR>";
  print "organism_physiology_abnormal and<BR>";
  print "pericellular_component_physiology_abnormal<BR>";
  print "<BR>";
  print "Acceptable terms for a parent and child in this branch are as follows:<BR>";
  print "<BR>";
  print "WBPhenotype:0000519 physiology_abnormal<BR>";
  print "DEF: \"Animals exhibit deviations in any physical or chemical process required for the cell, tissue, organ system or organism to carry out its normal function and activities or be able to perceive and respond to stimuli.\"<BR>";
  print "<BR>";
  print "WBPhenotype:0000536 cell_physiology_abnormal<BR>";
  print "DEF: \"Animals exhibit deviations at the cellular level, but not necessarily restricted to a single cell, in any physical or chemical process required for the cell to carry out its normal function and activities or be able to perceive and respond to stimuli.\"<BR>";
  print "<BR>";
  print "C. BAD vs. GOOD definitions  for WBPhenotype:0000406 lumpy<BR>";
  print "<BR>";
  print "BAD definitions:<BR>";
  print "	DEF: \"Animals are lumpy\" or<BR>";
  print "	DEF: \"Animals have lumps\"<BR>";
  print "<BR>";
  print "GOOD definition:<BR>";
  print "	DEF: \"Animals contain protrusions or bumps on their exterior.\"<BR>";
  print "<BR>\n";
} # sub showGuidelines

### FIRST PAGE ###


sub filterSpaces {
  my $value = shift;
  if ($value =~ m/^\s+/) { $value =~ s/^\s+//; }
  if ($value =~ m/\s+$/) { $value =~ s/\s+$//; }
#   if ($value =~ m/\s+/) { $value =~ s/\s+/ /g; }	# don't want this, gets rid of tabs 2007 08 31
  return $value;
} # sub filterSpaces

sub filterForPg {
  my $value = shift;
  if ($value =~ m/\'/) { $value =~ s/\'/''/g; }
  return $value;
} # sub filterForPg

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


__END__

