#!/usr/bin/perl -w

# Display curation status

# Added a flagged and curated column to specify as curated only from the list of
# flagged papers.  2008 05 09
#
# Add links to see all papers that are flagged and not curated by field.  2008 05 09
#
# Toss expr_pattern, use wen's file for expression curated.
# Use phenote interactions int_ tables for geneinteractions.  2008 07 23
#
# Use anatomy_ref file for 5 different types.  For Kimberly.  2008 08 07
#
# Added antibody_ref.  Kimberly.  2008 08 12
#
# &filterNotCurated(); now looks at /home/acedb/karen/gene_priority_list/out.current
# to get the papers from the top 50 genes (by paper count) and mark their links
# green.  for Karen.  2008 09 25
#
# change &filterNotCurated(); match color to #990033 for Karen.  2008 09 26
#
# added &allelePhenotype(); to show stuff Karen wants (all suggested, all names 
# without terms  2008 10 14
#
# don't include things marked as ``FALSE POSITIVE'' in the cur_ tables.  2009 01 29
#
# add antibodies flagged by textpresso and not curated for wen display.  2009 03 02
#
# use cfp_ instead of cur_ tables.  2009 06 04
# changed lots of table names.  2009 06 04
#
# get newmutant svm results into $flagged{newmutant}{$paper} for Jolene.  2009 09 30
#
# exclude false positives from svm results in &populateFlagged()  2009 10 27
#
# had structcorr mistakenly written  structurecorr  2009 11 18
#
# update from wpa to pap tables, even though they're not live yet.  2010 06 23
#
# karen wants her afp flagged fields to be coloured green.  if afp + top50 then
# #ff00ff.  2011 02 25


use strict;
use CGI;
use DBI;
use Jex;
use LWP::Simple;
# use LWP::UserAgent;
# use POSIX qw(ceil);

my $starttime = time;

my $query = new CGI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";


my $frontpage = 1;
my $blue = '#00ffcc';			# redefine blue to a mom-friendly color
my $red = '#ff00cc';			# redefine red to a mom-friendly color


my %theHash;

my %curators;				# $curators{two}{two#} = std_name ; $curators{std}{std_name} = two#
my %byCurator;

my %desc;				# description of fields
my %not_fp;				# not a first pass curation table
my %curated;				# hash of curated data;
my %flagged;				# hash of flagged data;
my %source;				# hash of where the fields get data;
my %papId;				# hash of identifiers;

my $show_lines_later;			# stuff to show later;

@{ $byCurator{'wen'} } = qw( otherexpr antibody transgene marker microarray );

my @giaf = qw( genesymbol extvariation mappingdata genefunc newmutant rnai lsrnai bioprocess );
my @intxn = qw( geneint funccomp geneprod molfunction );
# my @gexpfxn = qw( expression exprpattern generegulation overexpression mosaic site microarray cellcomponent );
my @gexpfxn = qw( otherexpr genereg overexpr mosaic siteaction microarray cellcomponent marker );
# my @pfs = qw( invitro covalent structureinformation molfunction );
my @pfs = qw( invitro covalent structinfo molfunction );
# my @seqdata = qw( structurecorrectionsanger structurecorrectionstlouis sequencechange sequencefeatures massspec ); 
my @seqdata = qw( structcorr seqchange seqfeat massspec ); 
# my @celldata = qw( ablationdata cellfunc cellname );
my @celldata = qw( ablationdata cellfunc );
my @insilico = qw( phylogenetic othersilico );
# my @reagents = qw( chemicals transgene antibody newsnp stlouissnp );
my @reagents = qw( chemicals transgene antibody newsnp );
my @other = qw( nematode humdis comment supplemental );
my @curator = qw( curator );		# only to see what's been flagged

&populatePapId();
&populateDesc();
&populateFlagged();
&populateCurated();



&printHeader('Literature Curation Status Display');
&display();
&printFooter();

sub sort { 1; }

sub populateAllCurated {
  my $good;
  foreach my $paper (sort keys %{ $flagged{curator} }) { 
    my $bad = 0; my $flagged = 0;
    foreach my $field (sort keys %source) {
      if ($flagged{$field}{$paper}) { $flagged++; 
        if ($curated{$field}{$paper}) { 1; } else { $bad++; } } }
    if ($flagged > 0) { unless ($bad) { $good++; } }
  } # foreach my $paper (sort keys %{ $flagged{curator} })
  print "There are $good papers curated for every flagged field that have a source file.<BR>\n";
} # sub populateAllCurated

sub populatePapId {
#   my $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE joinkey IS NOT NULL AND wpa_identifier IS NOT NULL ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
#   while (my @row = $result->fetchrow) { if ($row[3] eq 'valid') { $papId{$row[1]} = $row[0]; } else { delete $papId{$row[1]}; } }
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey IS NOT NULL AND pap_identifier IS NOT NULL ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $papId{$row[1]} = $row[0]; } 
} # sub populatePapId

sub display {
  my $action;
  print "<FORM NAME='form1' METHOD=\"POST\" ACTION=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi\">\n";

  unless ($action = $query->param('action')) {
    $action = 'none';
    if ($frontpage) { &firstPage(); my $endtime = time; my $difftime = $endtime - $starttime; print "<P>Processing took $difftime seconds<BR>\n"; return; }
  } else { $frontpage = 0; }

  if ($action eq 'By Paper !') { &firstPage('paper'); }
  elsif ($action eq 'Filter by Checkbox Any !') { &filterCheckbox('any'); }
  elsif ($action eq 'Filter by Checkbox All !') { &filterCheckbox('all'); }
  elsif ($action eq 'Source Files !') { &sourcefiles(); }
  elsif ($action eq 'fnc') { &filterNotCurated(); }
  elsif ($action eq 'fc') { &filterCurated(); }
  elsif ($action eq 'allele_phenotype') { &allelePhenotype(); }
  elsif ($action eq 'wen !') { &curatorData('wen'); }
  else { 1; }
  print "</FORM>\n";
} # sub display

sub curatorData {
  my $curator = shift;
  my %good_papers;
  print "<TABLE border=1>\n";
  print "<TR><TD>paper</TD>\n";
  foreach my $field (@{ $byCurator{$curator} }) {
#     print "<TD>$field -- $desc{$field}</TD>\n";
    print "<TD>$desc{$field}</TD>\n";	# wen wants short descriptions  2009 02 17
    foreach my $paper (sort keys %{ $flagged{$field} }) { unless ($curated{$field}{$paper}) { $good_papers{$paper}++; } }
  }
  print "</TR>\n";
  foreach my $pap (sort keys %good_papers) { 
    my $name = $pap; # if ($top_50{$pap}) { $name = "<FONT COLOR=\"#990033\">$pap</FONT>"; }
    $pap = "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=By+Paper+%21&paper=$pap\" TARGET=new>$name</A>"; 
    print "<TR><TD>$pap</TD>";
    foreach my $field (@{ $byCurator{$curator} }) {
      my $data = '--';
      if ( ($flagged{$field}{$name}) && ! ($curated{$field}{$name}) ) { $data = 'yes'; }
      print "<TD ALIGN=CENTER>$data</TD>";
    }
    print "</TR>\n";
  }
  print "</TABLE>\n";
  if ($curator eq 'wen') {
    print "Papers with Antibody flagged by Textpresso, but not curated :<br />";
    my ($textpresso_antibody) = get( "http://textpresso-dev.caltech.edu/azurebrd/wen/anti_protein_wen" );
    my (@papers) = $textpresso_antibody =~ m/WBPaper(\d+)/g; my @textpresso_not_curated = ();
    foreach (@papers) { unless ($curated{"antibody"}{$_}) { push @textpresso_not_curated, $_; } }
    my $textpresso_not_curated = join ", ", @textpresso_not_curated; print "$textpresso_not_curated<br />";
  }
} # sub curatorData

sub allelePhenotype {		# show stuff Karen wants (all suggested, all names without terms  2008 10 14
  my %hash;
  my $result = $dbh->prepare( "SELECT * FROM app_term" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { if ($row[1]) { $hash{term}{$row[0]} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM app_tempname" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { if ($row[1]) { 
    unless ($hash{term}{$row[0]}) { $hash{no_term}{$row[1]}++; }
    $hash{name}{$row[0]} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM app_suggested" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { if ($row[1]) { $hash{sug}{$hash{name}{$row[0]}}++; } }
  my (@sug) = sort keys %{ $hash{sug} };
  my (@no_term) = sort keys %{ $hash{no_term} };
  my $suggested = join", ", @sug;
  my $no_term = join", ", @no_term;
  print "These have no phenotype term : $no_term<BR>\n";
  print "These have suggested terms : $suggested<BR>\n";
} # sub allelePhenotype

sub filterCurated {
  my ($oop, $field) = &getHtmlVar($query, "field");
  my @good_papers = ();
  foreach my $paper (sort keys %{ $flagged{$field} }) { if ($curated{$field}{$paper}) { push @good_papers, $paper; } }
  foreach my $pap (@good_papers) { 
    $pap = "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=By+Paper+%21&paper=$pap\" TARGET=new>$pap</A>"; 
  }
  my $match_count = scalar(@good_papers);
  my $papers = join"\t", @good_papers; print "Flagged and curated <FONT COLOR=green>$field</FONT> MATCHES $match_count papers : $papers<BR>\n";
} # sub filterCurated

sub filterNotCurated {
  my ($oop, $field) = &getHtmlVar($query, "field");
  my $infile = '/home/acedb/karen/gene_priority_list/out.current'; my %top_50;
  open (IN, "<$infile") or die "Cannot open $infile : $!"; my $count = 0;
  while (my $line = <IN>) { $count++; last if ($count > 50); chomp $line;
    my ($gene, $flag, $count, $date, $papers) = split/\t/, $line;
    my @paps = split/, /, $papers; foreach (@paps) { $top_50{$_}++; } }
  close (IN) or die "Cannot close $infile : $!";

  my %afp;			# karen wants her afp flagged fields to be coloured green  2011 02 25
  if ( ($field eq 'newmutant') || ($field eq 'overexpr') ) {
    my $result = $dbh->prepare( "SELECT joinkey FROM afp_$field WHERE afp_$field IS NOT NULL" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
    while (my @row = $result->fetchrow) { $afp{$field}{$row[0]}++; } }

  my @good_papers = ();
  foreach my $paper (sort keys %{ $flagged{$field} }) { unless ($curated{$field}{$paper}) { push @good_papers, $paper; } }
  foreach my $pap (@good_papers) {
    my $name = $pap; 
    if (($afp{$field}{$pap}) && ($top_50{$pap})) { $name = "<FONT COLOR=\"#ff00ff\">$pap</FONT>"; }
    elsif ($top_50{$pap}) { $name = "<FONT COLOR=\"#990033\">$pap</FONT>"; }
    elsif ($afp{$field}{$pap}) { $name = "<FONT COLOR=\"green\">$pap</FONT>"; }
    $pap = "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=By+Paper+%21&paper=$pap\" TARGET=new>$name</A>"; 
  }
  my $match_count = scalar(@good_papers);
  my $papers = join"\t", @good_papers; print "Flagged and non curated <FONT COLOR=green>$field</FONT> MATCHES $match_count papers : $papers<BR>\n";
} # sub filterNotCurated

sub filterCheckbox {
  my $flag = shift; my %checked;
  foreach my $field ( @giaf, @intxn, @gexpfxn, @pfs, @seqdata, @celldata, @insilico, @reagents, @other ) {
    my ($oop, $checked) = &getHtmlVar($query, "${field}_flagged");
    if ($checked) { $checked{flagged}{$field}++; }
    ($oop, $checked) = &getHtmlVar($query, "${field}_curated");
    if ($checked) { $checked{curated}{$field}++; }
  } # foreach my $field ( @giaf, @intxn, @gexpfxn, @pfs, @seqdata, @celldata, @insilico, @reagents, @other )
  print "$flag of :\n"; my $checkbox_count = 0; my %papers;
  foreach my $field (keys %{ $checked{flagged} } ) {
    foreach my $paper (keys %{ $flagged{$field} }) { $papers{$paper}++; }
    print "<FONT COLOR=red>flagged $field</FONT>, \n";
    $checkbox_count++;					# there's a checkbox for this
  } # foreach my $field (keys %{ $checked{$type} } )
  foreach my $field (keys %{ $checked{curated} } ) {
    foreach my $paper (keys %{ $curated{$field} }) { $papers{$paper}++; }
    print "<FONT COLOR=green>curated $field</FONT>, \n";
    $checkbox_count++;					# there's a checkbox for this
  } # foreach my $field (keys %{ $checked{$type} } )
  my @good_papers;
  if ($flag eq 'any') { @good_papers = sort keys %papers; }
  elsif ($flag eq 'all') { foreach my $paper (sort keys %papers) { if ($papers{$paper} == $checkbox_count) { push @good_papers, $paper; } } }
  foreach (@good_papers) { $_ = "<A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=By+Paper+%21&paper=$_\" TARGET=new>$_</A>"; }
  my $match_count = scalar(@good_papers);
  my $papers = join"\t", @good_papers; print "MATCHES $match_count papers : $papers<BR>\n";
  &firstPage();
} # sub filterCheckbox

sub firstPage {
  my $flag = shift; my $paper = '';
  if ($flag) { if ($flag eq 'paper') { (my $oop, $paper) = &getHtmlVar($query, 'paper'); 
    print "Paper Display : <A HREF=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+%21&data_number=$paper\" TARGET=new>$paper</A><BR>\n"; } }
  print "Paper : <INPUT NAME=paper VALUE=\"$paper\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"By Paper !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Filter by Checkbox Any !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Filter by Checkbox All !\">\n";
  print "<INPUT TYPE=submit NAME=action VALUE=\"Source Files !\">\n";
  foreach my $curator (sort keys %byCurator) {
    print "<INPUT TYPE=submit NAME=action VALUE=\"$curator !\">\n";
  } # foreach my $curator (sort keys %byCurator)
  my @blah = keys %{ $flagged{curator} };
  my $curated_valid_papers = scalar @blah;
  print "<BR>$curated_valid_papers have been First-Pass curated (that haven't been reflagged as false positive).<BR>\n";
  &populateAllCurated();
  print "<P>\n";
  print "<TABLE border=1>\n";
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{giaf}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@giaf) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{intxn}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@intxn) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{gexpfxn}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@gexpfxn) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{pfs}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@pfs) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{seqdata}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@seqdata) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{celldata}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@celldata) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{insilico}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@insilico) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{reagents}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@reagents) { &showFieldLine($field, $paper); }
  print "<TR><TD COLSPAN=2><FONT SIZE=+2>$desc{other}</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  foreach my $field (@other) { &showFieldLine($field, $paper); }

  print "<TR><TD COLSPAN=2><FONT SIZE=+2>Hidden</FONT></TD><TD>flagged</TD><TD>flagged<BR>curated</TD><TD>all<BR>curated</TD><TD>flagged<BR>not<BR>curated</TR>\n";
  if ($show_lines_later) { print "$show_lines_later"; }
  print "</TABLE>\n";
} # sub firstPage

sub populateCurated {
  my $infile = '/home/postgres/public_html/cgi-bin/data/concise_dump_new.ace'; $source{genefunc} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { if ($line =~ m/Paper_evidence\t\"WBPaper(\d{8})\"/) { $curated{genefunc}{$1}++; $curated{geneprod}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/postgres/public_html/cgi-bin/data/go_curation.go.latest';
  $source{cellcomponent} = $infile; $source{bioprocess} = $infile; $source{molfunction} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { 
    if ($line =~ m/WBPaper(\d{8})/) { 
      my $paper = $1;
      if ($line =~ m/\tC\t/) { $curated{cellcomponent}{$paper}++; }
      elsif ($line =~ m/\tP\t/) { $curated{bioprocess}{$paper}++; }
      elsif ($line =~ m/\tF\t/) { $curated{molfunction}{$paper}++; } } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/acedb/wen/expr_pattern/ExprCurationStatus.txt'; $source{otherexpr} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/^WBPaper(\d+)\t.*?$/) { $curated{otherexpr}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/acedb/karen/populate_gin_variation/transgene_summary_reference.txt'; $source{transgene} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/WBPaper(\d+)/) { $curated{transgene}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
#   $infile = '/home/azurebrd/public_html/var/work/phenote/ws_current.obo'; $source{extvariation} = $infile;
  $infile = '/home/acedb/karen/cur_status_sources/vargene_ref.txt'; $source{extvariation} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/WBPaper(\d+)/) { $curated{extvariation}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/acedb/karen/cur_status_sources/microarray_ref.txt'; $source{microarray} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/WBPaper(\d+)/) { $curated{microarray}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/acedb/karen/cur_status_sources/regulation_ref.txt'; $source{genereg} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/WBPaper(\d+)/) { $curated{genereg}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/acedb/karen/cur_status_sources/antibody_ref.txt'; $source{antibody} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/WBPaper(\d+)/) { $curated{antibody}{$1}++; } }
  close (IN) or die "Cannot close $infile : $!";
  $infile = '/home/acedb/karen/cur_status_sources/anatomy_ref.txt'; 
  $source{mosaic} = $infile; $source{siteaction} = $infile; $source{ablationdata} = $infile; $source{cellfunc} = $infile; # $source{cellname} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) { chomp $line; if ($line =~ m/WBPaper(\d+)/) { 
$curated{mosaic}{$1}++; $curated{siteaction}{$1}++; $curated{ablationdata}{$1}++; $curated{cellfunc}{$1}++; 
# $curated{cellname}{$1}++; 
} }
  close (IN) or die "Cannot close $infile : $!";
  my (@suppl) = </home/acedb/daniel/Reference/wb/supplemental/*>;  
  $source{transgene} = '/home/acedb/daniel/Reference/wb/supplemental/';
  foreach my $suppl (@suppl) { if ($suppl =~ m/(\d{8})$/) { $curated{supplemental}{$1}++; } }

  my %gsdata;
  my $result = $dbh->prepare( "SELECT gin_locus.joinkey, gin_locus.gin_locus, gin_sequence.gin_sequence FROM gin_locus, gin_sequence WHERE gin_locus.joinkey = gin_sequence.joinkey; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { my $pair = "$row[1]\t$row[2]"; ($pair) = uc($pair); $gsdata{$pair}++; }
  $result = $dbh->prepare( "SELECT gin_synonyms.joinkey, gin_synonyms.gin_synonyms, gin_sequence.gin_sequence FROM gin_synonyms, gin_sequence WHERE gin_synonyms.joinkey = gin_sequence.joinkey; " );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { my $pair = "$row[1]\t$row[2]"; ($pair) = uc($pair); $gsdata{$pair}++; }
  foreach my $paper (sort keys %{ $flagged{genesymbol} }) {
    my $bad = 0; my $data = $flagged{genesymbol}{$paper}; my (@lines) = split/\n/, $data;
    foreach my $line (@lines) {  my (@groups) = split/\s+/, $line;
      foreach my $group (@groups) {			# groups are grouped by = without spaces
        my @genes; my @sequences;
        if ($group =~ m/([a-z]+\-\d+)/) { (@genes) = $group =~ m/([a-z]+\-\d+)/g; }
        if ($group =~ m/([0-9a-zA-Z]+\.\d+[A-Za-z]?)/) { (@sequences) = $group =~ m/([0-9a-zA-Z]+\.\d+)/g; }
        foreach my $gene (@genes) {
          foreach my $seq (@sequences) {
            my $pair = "$gene\t$seq"; ($pair) = uc($pair);
            unless ($gsdata{$pair}) { $bad++; } } } } }	# paper not fully curated if locus-sequence pair not in postgres
    unless ($bad > 0) { $curated{genesymbol}{$paper}++; } }
  $infile = '/home/postgres/work/pgpopulation/curation_status/genesymbol_maryann'; $source{genesymbol} = $infile;
  open (IN, "<$infile") or die "Cannot open $infile : $!"; my %temp;
  while (my $line = <IN>) { chomp $line; my ($paper) = $line =~ m/(\d{8})$/; $temp{exist}{$paper}++; if ($line =~ m/^[Pp]ending/) { $temp{pending}{$paper}++; } }
  close (IN) or die "Cannot close $infile : $!";
  foreach my $paper (keys %{ $temp{exist} }) { unless ($temp{pending}{$paper}) { $curated{genesymbol}{$paper}++; } }

  $result = $dbh->prepare( "SELECT * FROM app_paper WHERE app_paper IS NOT NULL" ); $source{newmutant} = 'postgres app_paper';
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $row[1] =~ s/WBPaper//; $curated{newmutant}{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM int_paper WHERE int_paper IS NOT NULL" ); $source{geneint} = 'postgres int_paper';
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $row[1] =~ s/WBPaper//; $curated{geneint}{$row[1]}++; }
#   $result = $dbh->prepare( "SELECT * FROM wpa_rnai_curation WHERE wpa_rnai_curation IS NOT NULL" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  $result = $dbh->prepare( "SELECT * FROM pap_curation_flags WHERE pap_curation_flags = 'rnai_curation'" ); 
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  $source{lsrnai} = 'postgres pap_curation_flags = rnai_curation'; $source{rnai} = 'postgres pap_curation_flags = rnai_curation';
  while (my @row = $result->fetchrow) { $curated{rnai}{"$row[0]"}++; $curated{lsrnai}{"$row[0]"}++; }
} # sub populateCurated

sub sourcefiles {
  print "<TABLE border=1>\n";
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{giaf}</FONT></TD></TR>\n";
  foreach my $field (@giaf) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{intxn}</FONT></TD></TR>\n";
  foreach my $field (@intxn) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{gexpfxn}</FONT></TD></TR>\n";
  foreach my $field (@gexpfxn) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{pfs}</FONT></TD></TR>\n";
  foreach my $field (@pfs) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{seqdata}</FONT></TD></TR>\n";
  foreach my $field (@seqdata) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{celldata}</FONT></TD></TR>\n";
  foreach my $field (@celldata) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{insilico}</FONT></TD></TR>\n";
  foreach my $field (@insilico) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{reagents}</FONT></TD></TR>\n";
  foreach my $field (@reagents) { &showSourceLine($field); }
  print "<TR><TD COLSPAN=3><FONT SIZE=+2>$desc{other}</FONT></TD></TR>\n";
  foreach my $field (@other) { &showSourceLine($field); }
  print "</TABLE>\n";
} # sub sourcefiles

sub showSourceLine {
  my $field = shift;
  unless ($source{$field}) { $source{$field} = "&nbsp"; }
  print "<TR><TD>$field</TD><TD>$desc{$field}</TD><TD>$source{$field}</TD></TR>\n";
}


sub populateFlagged {
  my %valid_papers;
#   my $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp" );
  my $result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid'" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow) { $valid_papers{$row[0]}++; }
  foreach my $field ( @giaf, @intxn, @gexpfxn, @pfs, @seqdata, @celldata, @insilico, @reagents, @other, @curator ) {
    unless ($not_fp{$field}) { 
      if ($field eq 'genesymbol') {
        my $result = $dbh->prepare( "SELECT * FROM cfp_$field WHERE cfp_$field ~ '=' AND cfp_$field !~ 'FALSE POSITIVE'" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        while (my @row = $result->fetchrow()) { 
          my $joinkey = $row[0];
          if ($row[0] =~ m/^\d{8}$/) { 1; } else { if ($papId{$row[0]}) { $joinkey = $papId{$row[0]}; } }
          next unless $valid_papers{$joinkey};  
          $flagged{$field}{$joinkey} = $row[1]; } }
      else {
        my $result = $dbh->prepare( "SELECT * FROM cfp_$field WHERE cfp_$field IS NOT NULL AND cfp_$field !~ 'FALSE POSITIVE'" );
        $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
        while (my @row = $result->fetchrow()) { 
          if ($row[0] =~ m/^\d{8}$/) { next unless $valid_papers{$row[0]}; $flagged{$field}{$row[0]}++; } 
            else { if ($papId{$row[0]}) { next unless $valid_papers{$papId{$row[0]}};  $flagged{$field}{$papId{$row[0]}}++; } } } } } }

#   my $variation_file = get "http://dev.textpresso.org/Curator_Related/Karen/allele_rearrangement_transgene.out" ;
  my $variation_file = get "http://dev.textpresso.org/Curator_Related/Karen/alleles" ;
  my (@papers) = $variation_file =~ m/\nWBPaper(\d+)\t/g;
  foreach my $paper (@papers) { next unless $valid_papers{$paper}; $flagged{extvariation}{$paper}++; }
  my $newmutant_file = get "http://caprica.caltech.edu/celegans/svm_results/Juancarlos/newmutant";
  (@papers) = $newmutant_file =~ m/\nWBPaper(\d+)\t/g;
  foreach my $paper (@papers) { next unless $valid_papers{$paper}; $flagged{newmutant}{$paper}++; }

  $result = $dbh->prepare( "SELECT * FROM cfp_newmutant WHERE cfp_newmutant ~ 'FALSE POSITIVE'" );	# remove false positives from svm results
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow()) { delete $flagged{'newmutant'}{$row[0]}; }
  $result = $dbh->prepare( "SELECT * FROM cfp_extvariation WHERE cfp_extvariation ~ 'FALSE POSITIVE'" );	# remove false positives from svm results
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
  while (my @row = $result->fetchrow()) { delete $flagged{'extvariation'}{$row[0]}; }
} # sub populateFlagged

sub showFieldLine {
  my ($field, $filter_paper) = @_; my $flagged = 0; my $curated = 0; my $flgNcur = 0; my $fNotCur = 0;
  if ($filter_paper) { 
      if ($flagged{$field}{$filter_paper}) { $flagged++; 
        if ($curated{$field}{$filter_paper}) { $flgNcur++; } }
      if ($curated{$field}{$filter_paper}) { $curated++; } }
    else {
      if ($flagged{$field}) { foreach my $paper (keys %{ $flagged{$field} }) { $flagged++; 
        if ($curated{$field}{$paper}) { $flgNcur++; } } }
      if ($curated{$field}) { foreach my $paper (keys %{ $curated{$field} }) { $curated++; } } }
  my $line = '';
  my ($oop, $later) = &getHtmlVar($query, "${field}_later");
  unless ($later) { $later = ''; }
  $line .= "<TR><TD><INPUT NAME=\"${field}_later\" TYPE=CHECKBOX VALUE=\"checked\" $later>$field</TD><TD>$desc{$field}</TD>\n";
  my $checked = '';
  ($oop, $checked) = &getHtmlVar($query, "${field}_flagged");
  unless ($checked) { $checked = ''; } unless ($flagged) { $flagged = 0; }
  $line .= "<TD><INPUT NAME=\"${field}_flagged\" TYPE=CHECKBOX VALUE=\"checked\" $checked>$flagged</TD>\n";
  ($oop, $checked) = &getHtmlVar($query, "${field}_curated");
#   unless ($flgNcur) { $flgNcur = 0; } 
#   $line .= "<TD>$flgNcur</TD>\n";
  unless ($checked) { $checked = ''; } unless ($curated) { $curated = ''; }
  if ($flgNcur) { $line .= "<TD> <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=fc&field=$field\">$flgNcur</A></TD>\n"; }
    else { $line .= "<TD>0</TD>\n"; }
  $line .= "<TD><INPUT NAME=\"${field}_curated\" TYPE=CHECKBOX VALUE=\"checked\" $checked>$curated</TD>\n";
  $fNotCur = $flagged - $flgNcur;
  if ($fNotCur) { $line .= "<TD> <A HREF=\"http://tazendra.caltech.edu/~postgres/cgi-bin/curation_status.cgi?action=fnc&field=$field\">$fNotCur</A></TD>\n"; }
    else { $line .= "<TD>0</TD>\n"; }
  $line .= "</TR>\n";
  if ($later) { $show_lines_later .= $line; } else { print $line; }
} # sub showFieldLine

sub populateDesc {
  $not_fp{bioprocess}++;
  $not_fp{molfunction}++;
  $not_fp{cellcomponent}++;
  $not_fp{phylogenetic}++;
  $not_fp{othersilico}++;
  $not_fp{nematode}++;
  $not_fp{extvariation}++;
  
  $desc{giaf} = 'Gene Identity and Function';
  $desc{genesymbol} = 'Novel Gene Symbol or Gene-CDS link (e.g. xyz-1 gene was cloned and it turned out to be the same as abc-1 gene)';
  $desc{extvariation} = 'Arun data from http://dev.textpresso.org/Curator_Related/Karen/allele_rearrangement_transgene.out';
  $desc{mappingdata} = 'Genetic Mapping Data (e.g. 3-factor mapping, deficiency mapping)';
  $desc{genefunc} = 'Gene Function (novel function for a gene (not reported in Wormbase under Concise Description on the Gene page)';
  $desc{newmutant} = 'Mutant Phenotype (novel mutant phenotype is reported in the paper)';
  $desc{rnai} = 'RNAi (small scale, less than 100 individual experiments)';
  $desc{lsrnai} = 'RNAi (large scale >100 individual experiments)';
  $desc{bioprocess} = 'Gene Ontology - Biological Process';
  
  $desc{intxn} = 'Interactions';
  $desc{geneint} = 'Genetic interactions (e.g. daf-16(mu86) suppresses daf-2(e1370), daf-16(RNAi) suppresses daf-2(RNAi))';
  $desc{funccomp} = '?';
  $desc{geneprod} = 'Gene Product Interaction (protein-protein, RNA-protein, DNA-protein interactions, etc.)';
  $desc{molfunction} = 'Gene Ontology - Molecular Function';
  
  $desc{gexpfxn} = 'Gene Expression and Function';
#   $desc{expression} = 'Expression Data (exclude expression data for the reporters used exclusively as markers)';
  $desc{otherexpr} = 'Expression Pattern';	# wen wants short description
#   $desc{exprpattern} = '?';
#   $desc{generegulation} = 'Gene Regulation on Expression Level (e.g. geneA-gfp reporter is mis-expressed in geneB mutant background)';
  $desc{genereg} = 'Expression Pattern';
  $desc{overexpr} = 'Overexpression  (over-expression of a gene that results in a phenotypic change, genetic intractions, etc.)';
  $desc{mosaic} = 'Mosaic Analysis (e.g. extra-chromosomal transgene loss in a particular cell lineage abolishes mutant rescue)'; 
  $desc{siteaction} = 'Site of Action (e.g. tissue/cell specific expression rescues mutant phenotype; RNAi in rrf-1 background determines that the gene acts in the germ line)'; 
  $desc{microarray} = 'Microarray';
  $desc{cellcomponent} = 'Gene Ontology - Cellular Component';
  $desc{marker} = 'Transgene Marker';
  
  $desc{pfs} = 'Protein Function and Structure';
  $desc{invitro} = 'Protein Analysis In Vitro (e.g. kinase assay)';
  $desc{covalent} = 'Covalent Modification (e.g. phosphorylation site is studies via mutagenesis and in vitro assay)';
  $desc{structinfo} = 'Structure Information (e.g. NMR structure, functional domain info for a protein (e.g. removal of the first 50aa causes mislocalization of the protein))'; 
  
  $desc{seqdata} = 'Sequence Data';
  $desc{structcorr} = 'Gene Structure Correction';
  $desc{seqchange} = 'Sequence Change (mutation were sequenced in the paper)';
  $desc{seqfeat} = 'Sequence Features (DNA/RNA elements required for gene expression)';
  $desc{massspec} = 'Mass Spectrometry';
  
  $desc{celldata} = 'Cell Data';
  $desc{ablationdata} = 'Ablation Data (cells were ablated using a laser or by other means (e.g. by expressing a cell-toxic protein))'; 
  $desc{cellfunc} = 'Cell Function (the paper describes new function for a cell)';
#   $desc{cellname} = '?';
  
  $desc{insilico} = 'In Silico Data';
  $desc{phylogenetic} = 'Phylogenetic Analysis';
  $desc{othersilico} = 'Other Silico Data';
  
  $desc{reagents} = 'Reagents';
  $desc{chemicals} = 'Chemicals (typically a small-molecule chemical was used: butanol, prozac, etc.)';
#   $desc{transgene} = 'Transgene (integrated or extra-chromosomal)';
  $desc{transgene} = 'Transgene';	# wen wants short description
#   $desc{antibody} = 'C.elegans Antibodies (Abs were created in the paper, or Abs used were created before elsewhere)';
  $desc{antibody} = 'Antibody';	# wen wants short description
  $desc{newsnp} = 'New SNPs (SNPs that are not in Wormbase)';
#   $desc{stlouissnp} = 'St. Louis';
  
  $desc{other} = 'Other';
  $desc{nematode} = 'Nematode species (there is info about non-C.elegans nematodes)';
  $desc{humdis} = 'Human Diseases (relevant to human diseases, e.g. the gene studied is a ortholog of a human disease gene)';
  $desc{comment} = '?';
  $desc{supplemental} = 'Supplemental data downloaded by Daniel';
} # sub populateDesc

__END__

Name : Literature Curation Status


Gene Identity and Function:  	   	   	   	 
NoData 3   	Novel Gene Symbol or Gene-CDS link (e.g. xyz-1 gene was cloned and it turned out to be the same as abc-1 gene) 	MaryAnn, Kimberly : genesymbol 	Geneace 	 
NoData 4   	? 	No One 	: extractedallelenew 	Geneace? 	 
NoData 5   	Genetic Mapping Data (e.g. 3-factor mapping, deficiency mapping) MaryAnn 	: mappingdata 	Geneace 	 
6	Gene Function (novel function for a gene (not reported in Wormbase under Concise Description on the Gene page) 	Erich 	: genefunction Postgres 	 
	Could have looked at car_con_ref_reference, but would require converting pmid cgc
        Look at http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_dump_new.ace
7	Mutant Phenotype (novel mutant phenotype is reported in the paper) 	Erich, Gary, Karen Jolene 	: newmutant 	Postgres : allele-phenotype phenote table 	 
        Look at app_paper
8	RNAi (small scale, less than 100 individual experiments) Gary 	: rnai 	Postgres: RNAi checkout form 	 
        Look at wpa_rnai_curation
9	RNAi (large scale >100 individual experiments) : 	Raymond, Igor 	: lsrnai 	Postgres: RNAi checkout form 	 
        Look at wpa_rnai_curation
10	Gene Ontology - Biological Process 	  	*Biological Process 	Postgres :GO Biological Process 	 
	http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest	Check for ``P''


11 	Interactions: 	  	  	  	 
NoData	12	Genetic interactions (e.g. daf-16(mu86) suppresses daf-2(e1370), daf-16(RNAi) suppresses daf-2(RNAi)) 	Erich 	: geneinteractions Postgres? J, is this true? 	it is stored in postgres now after juancarlos created the interaction curation form. But the setup has not been tested just yet.
NoData	13	? 	No One 	: functionalcomplementation 	? 	I am thinking of retiring this field. Example of the data that meant to go in: transgenic xyz-1 expression rescues abc-1 mutant. There are few data like this and they can go in gene interaction field.
14	Gene Product Interaction (protein-protein, RNA-protein, DNA-protein interactions, etc.) 	Erich 	: geneproduct 	Postgres? J, is this true? 	my understanding is that erich uses this for functional annotations but we don't actually curate/extract the data
        Look at http://tazendra.caltech.edu/~postgres/cgi-bin/data/concise_dump_new.ace
15	Gene Ontology - Molecular Function 	  	*Molecular function 	Postgres :GO Molecular Function 	 
	http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest	Check for ``F''

16 	Gene Expression and Function: 	  	  	  	 
Wen ?	17	Expression Data (exclude expression data for the reporters used exclusively as markers) 	Wen, Kimberly 	: expression 	Citace 	 
Wen ?	18	? 	? 	: exprpattern 	Wen? 	the same as expression data above
Wen ?	19	Gene Regulation on Expression Level (e.g. geneA-gfp reporter is mis-expressed in geneB mutant background) 	Xiaodong 	: generegulation Citace 	 
NoData	20	Overexpression  (over-expression of a gene that results in a phenotypic change, genetic intractions, etc.) 	Erich, Gary 	: overexpression Postgres? J, is this true? 	my understanding is that erich uses this for functional annotations but we don't actually curate/extract the data
Ray ?	21	Mosaic Analysis (e.g. extra-chromosomal transgene loss in a particular cell lineage abolishes mutant rescue) 	Raymond 	: mosaic Postgres 	 
Ray ?	22	Site of Action (e.g. tissue/cell specific expression rescues mutant phenotype; RNAi in rrf-1 background determines that the gene acts in the germ line) 	Raymond 	: site 	Postgres 	 
Igor ?	23	Microarray 	Igor 	: microarray 	Citace 	 
24	Gene Ontology - Cellular Component 	  	*Cellular component 	Postgres :GO CC 	 
	http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest	Check for ``C''

25 	Protein Function and Structure: 	  	  	  	 
NoData	26	Protein Analysis In Vitro (e.g. kinase assay) 	No One 	: invitro 	? 	not extracted currently
NoData	27	Covalent Modification (e.g. phosphorylation site is studies via mutagenesis and in vitro assay) 	No One 	: covalent 	? 	not extracted currently
NoData	28	Structure Information (e.g. NMR structure, functional domain info for a protein (e.g. removal of the first 50aa causes mislocalization of the protein)) 	No One/CSHL 	: structureinformation 	? 	not extracted currently
29	Gene Ontology - Molecular Function 	  	*Molecular Function 	Postgres :GO Molecular Function 	 
	http://tazendra.caltech.edu/~postgres/cgi-bin/data/go_curation.go.latest	Check for ``F''

30 	Sequence Data: 	  	  	  	 
NoData	31	Gene Structure Correction (Gene Structure is different from the one in Wormbase: e.g. different splice-site, SL1 instead of SL2, etc.) 	Sanger : structurecorrectionsanger 	Geneace
NoData	32	  	St. Louis 	: structurecorrectionstlouis 	St.  Louis 	 
NoData	33	Sequence Change (mutation were sequenced in the paper) 	Mary Ann : sequencechange 	Geneace 	 
NoData	34	Sequence Features (DNA/RNA elements required for gene expression,  ) 	Erich. Sanger, St.Louis 	: sequencefeatures Geneace/Erich/St. Louis 	 
NoData	35	Mass Spectrometry 	Sanger 	: massspec 	Geneace 	 

36 	Cell Data: 	  	  	  	  	 
Ray ?	37	Ablation Data (cells were ablated using a laser or by other means (e.g. by expressing a cell-toxic protein)) 	Raymond 	: ablationdata 	Postgres 	 
Ray ?	38	Cell Function (the paper describes new function for a cell) Raymond 	: cellfunction 	Postgres 	 
Ray ?	39	? 	Raymond 	: cellname 	Postgres 	 

40 	In Silico Data: 	  	  	  	  	 
NoData	41 	  	Phylogenetic Analysis 	? 	? 	? 	not extracted currently
NoData	42 	  	Other Silico Data 	? 	? 	? 	not extracted currently

43 	Reagents: 	  	  	  	  	 
NoData	44	Chemicals (typically a small-molecule chemical was used: butanol, prozac, etc.) 	No One 	: chemicals 	? 	not extracted currently
Wen ?	45	Transgene (integrated or extra-chromosomal) 	Wen 	: transgene 	Citace 	 
Wen ?	46	C.elegans Antibodies (Abs were created in the paper, or Abs used were created before elsewhere) 	Wen 	: antibody 	Citace 	 
NoData	47	New SNPs (SNPs that are not in Wormbase) 	St. Louis : newsnp 	St. Louis 	 
NoData	48	  	St. Louis 	: stlouissnp 	St. Louis 	 


49 	Other: 	  	  	  	 
NoData	50 	  	Nematode species (there is info about non-C.elegans nematodes) ? 	? 	? 	not extracted currently
NoData	51 	  	Human Diseases (relevant to human diseases, e.g. the gene studied is a ortholog of a human disease gene) : 	Ranjana, Karen 	: humandiseases 	? 	 
NoData	52 	  	? 	No One 	: comment 	? 	nothing to extract
NoData	53 	  	? 	Daniel 	: supplemental 	Postgres 	 
NoData	55 	  	  	  	  	  	 
NoData	56 	  	* not a first pass field but requested to be included as part of curation status check 	  	  	  	 


# once a day update local copy of 
# http://www.sanger.au.uk/tmp/Projects/C-elegans/LOCI/genes2molecularnamestest.txt
# use  /home/azurebrd/public_html/sanger/gene_postgres/genes2molecular_names.txt
use gin_sequence gin_locus gin_synonyms
compare cur_genesymbol data with 3-letter name and = sign with gin_locus and
whatever else is in the other side of the = sign to a sequence if it has a .
otherwise to a synonym.  if multiple 3-letter or multiple sequence, check cross
product.  put count number in ``all curated''

# DONE	flag is arun's list
# DONE	all curated would be from the flatfile Karen makes from ws_current
# DONE	make that  /home/acedb/karen/cur_status_sources/vargene_ref.txt instead of ws_current

mappingdata : Kimberly will talk to Mary Ann

expressiondata : Kimberly will talk to Wen

generegulation : Wen could dump a file like she does (Kimberly will ask)

mosaic & site : Kimberly will talk to Raymond 

# DONE	 microarray : Karen will make a dump for Paper -> Microarray_experiment

skip overexpression, PFS, sequencefeatures, massspec, chemicals, comment, supplemental

sequencechange : Kimberly will talk to Mary Ann

CELL : Kimberly will talk to Raymond

antibody : Kimberly will talk to Wen

newsnp : Kimberly will talk to WashU
stlouissnp : Kimberly will talk to StLouis

humandisease : Kimberly will talk to Ranjana
