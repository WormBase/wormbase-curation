#!/usr/bin/perl 

# display author FP that have author response.

# display links to all journal jfp forms for karen and genetics, all data for Arun

# for textpresso :
# http://tazendra.caltech.edu/~postgres/cgi-bin/journal/journal_all.cgi?action=Show+Data&type=textpresso
# for curators :
# http://tazendra.caltech.edu/~postgres/cgi-bin/journal/journal_all.cgi?action=Show+Data&type=antibody
# (replace antibody with appropriate field)
# replace pmid1841 with doi for live usage.  2009 07 07
#
# remove valid wpa check, since they need to show before we get the xml that makes the wpa valid.
# show doi instead of pmid1841.  2009 07 09
#
# use ~~ as divider for textpresso, only show pre-divider stuff when $type eq 'textpresso'  2009 07 10
#
# some wrong papers have DOI, only show the ones that match doi10.1534/genetics  2009 09 01
#
# removed authors for Karen and Arun  2009 09 29
#
# update from wpa to pap tables, even though they're not live  2010 06 24
#
# point to paper_display.cgi instead of wbpaper_display.cgi  2011 02 10
#
# allow for lower cased table search doi.  2011 09 22
#
# added  afp_gocuration  table, made link to CurateGO in journal_first_pass.cgi  2011 09 30
#
# added  pdf  links, justified left, cellpadding 4.  for Karen.  2012 06 21
#
# get DOIs that exist in textpresso (have 6 digits and .xml) and link to those that are not 
# in postgres.  2013 07 11
#
# for Karen, for Tim Schedl, want to have easy way to display his author FP data, so by default
# this form queries pap_identifier where joinkey in afp_lasttouched.  uses URLs
#   http://tazendra.caltech.edu/~postgres/cgi-bin/author_fp_display.cgi?afp_jfp=jfp
# for journal / old mode
#   http://tazendra.caltech.edu/~postgres/cgi-bin/author_fp_display.cgi?afp_jfp=afp
# for author / new default mode.  2013 08 21
#
# Data link says 'no data' in afp_lasttouched does not have data for the paper.
# PDFs show date from timestamp of pap_electronic_path .  2015 08 06
# 
# link to textpresso html for Karen  2015 09 10
#
# link to textpresso proofs for Karen  2016 01 20
#
# some test papers have low doi numbers, make font colour grey.
# split _temp.pdf into separate column.  2016 01 27



use CGI;
use Fcntl;
use strict;
use Jex;
use DBI;
use LWP::Simple;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my $query = new CGI;

srand;

# my %journalToTwo;
# $journalToTwo{"Genetics"} = 'two555';

my %hash;					# data for papers
my %pap;					# valid papers we care about (have doi)
my %tdoi;					# textpresso dois
my %afpLasttouched;				# paper has been touched

my @data_fields = qw( genesymbol mappingdata seqchange extvariation chemicals newmutant gocuration newstrains newbalancers antibody transgene newsnp newcell );

my $action;
unless ($action = $query->param('action')) {
  $action = 'none'; 
}

if ($action eq 'Ticket') { 
    print "Content-type: text/plain\n\n"; 
  }
  else { 
    &printHeader('Journal Data Display');      # normal form view
    &process();
    &printFooter();
}

sub process {
  if ($action eq 'none') { &firstPage(); }
  elsif ($action eq 'Show Data') { &showData(); }
} # sub process

# sub getJournalPapers {
#   my $result = $dbh->prepare( "SELECT * FROM wpa ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'valid') { $wpa{valid}{$row[0]}++; }
#       else { delete $wpa{valid}{$row[0]}; } }
# #   $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ 'pmid1841' ORDER BY wpa_timestamp;" );
#   $result = $dbh->prepare( "SELECT * FROM wpa_identifier WHERE wpa_identifier ~ 'doi10.1534/genetics' ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'valid') { $wpa{ident}{$row[0]} = $row[1]; }
#       else { delete $wpa{ident}{$row[0]}; } }
#   $result = $dbh->prepare( "SELECT * FROM afp_passwd ORDER BY afp_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     $wpa{pass}{$row[0]} = $row[1]; }
#   foreach my $joinkey (sort keys %{ $wpa{ident} } ) {
# #     unless ($wpa{valid}{$joinkey}) { delete $wpa{ident}{$joinkey}; }		# can't check for this, wpa are invalid until we get the XML, but need to show right away
#     unless ($wpa{pass}{$joinkey}) { delete $wpa{ident}{$joinkey}; }
#   }
# }
sub getJournalPapers {
#   my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'doi10.1534/genetics' ;" );
#   my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE LOWER(pap_identifier) ~ 'doi10.1534/g' ;" );
  my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey IN (SELECT joinkey FROM afp_lasttouched);" );
  my ($var, $afp_jfp) = &getHtmlVar($query, 'afp_jfp');
  if ($afp_jfp eq 'jfp') { 
    $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE LOWER(pap_identifier) ~ 'doi10.1534/g' ;" ); }
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $pap{ident}{$row[0]} = $row[1]; }
  my $joinkeys = join"','", sort keys %{ $pap{ident} };
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path WHERE joinkey IN ('$joinkeys') AND pap_electronic_path ~ 'pdf'"); $result->execute;
  while (my @row = $result->fetchrow) {
    my ($data) = &makePdfLinkFromPath($row[1]);
#     $pap{pdf}{$row[0]} = $data; 
    my ($ts) = $row[4] =~ m/^(\d{4}\-\d{2}\-\d{2})/;
    $pap{pdf}{$row[0]}{$data} = qq($ts); 
  }
  $result = $dbh->prepare( "SELECT * FROM afp_passwd ORDER BY afp_timestamp;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    $pap{pass}{$row[0]} = $row[1]; }
  foreach my $joinkey (sort keys %{ $pap{ident} } ) {
    unless ($pap{pass}{$joinkey}) { delete $pap{ident}{$joinkey}; }
  }
}

sub makePdfLinkFromPath {
  my ($path) = shift;
  my ($pdf) = $path =~ m/\/([^\/]*)$/;
  my $link = 'http://tazendra.caltech.edu/~acedb/daniel/' . $pdf;
  my $data = "<a href=\"$link\" target=\"new\">$pdf</a>"; return $data; }

sub showData {
  &getJournalPapers();
  my ($var, $type) = &getHtmlVar($query, 'type');
  &getPaperData();
  print "<table border=\"1\">\n";
  print "<tr><td>DOI</td><td>WBPaperID</td><td>field</td><td>data</td></tr>\n";
  foreach my $joinkey (sort keys %{ $pap{ident} } ) {
    foreach my $field (sort keys %{ $hash{$joinkey} } ) {
      my $show = 0;
      if ( ($type eq 'all') || ($type eq 'textpresso') ) { $show++; }
      elsif ($type eq $field) { $show++; }
      next unless $show;
      my $data = $hash{$joinkey}{$field};
      print "<tr>\n";
      print "<td>$pap{ident}{$joinkey}</td>\n";
      if ($type eq 'textpresso') { 
        if ($data =~ m/~~/) { ($data) = $data =~ m/^(.*?)~~/; }
        print "<td>$joinkey</td>\n"; }
      else {
        my $paper_link = "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?data_number=$joinkey&action=Search+%21";
        print "<td align=\"center\"><a href=\"$paper_link\">$joinkey</a></td>\n"; }
      print "<td>$field</td>\n";
      print "<td>$data</td>\n";
      print "</tr>\n";
    }
  }
  foreach my $doi (sort keys %tdoi) { print qq(In <a href="http://textpresso-dev.caltech.edu/gsa/worm/incoming_xml/?C=M;O=A">textpresso</a> but missing in WormBase : <a href="http://textpresso-dev.caltech.edu/gsa/worm/incoming_xml/${doi}.xml">$doi</a><br/>\n); }
} # sub showData

sub getPaperData {
  foreach my $field (@data_fields) {
    my $table = 'afp_' . $field;
    my $result = $dbh->prepare( "SELECT * FROM $table ORDER BY afp_timestamp;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) {
      if ($pap{ident}{$row[0]}) { $hash{$row[0]}{$field} = $row[1]; }
    }
  } # foreach my $field (@data_fields)
} # sub getPaperData

sub getTextpressoDOIs {
  my $url = 'http://textpresso-dev.caltech.edu/gsa/worm/incoming_xml/?C=M;O=A';
  my $page = get $url;
  my (@dois) = $page =~ m/(\d{6})\.xml/g;
  foreach (@dois) { $tdoi{$_}++; }
  foreach my $joinkey (sort keys %{ $pap{ident} }) {
    my ($doi_extension) = $pap{ident}{$joinkey} =~ m/\.(\d{6})$/;
    if ($tdoi{$doi_extension}) { delete $tdoi{$doi_extension}; }
  }
} # sub getTextpressoDOIs

sub getHasAfpLasttouched {
  my $result = $dbh->prepare( "SELECT * FROM afp_lasttouched;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) {
    $afpLasttouched{$row[0]} = $row[2]; }
} # sub getHasAfpLasttouched

sub firstPage {
  &getJournalPapers();
  &getTextpressoDOIs();
  &getHasAfpLasttouched();
  print "<form method=\"post\" action=\"http://tazendra.caltech.edu/~postgres/cgi-bin/author_fp_display.cgi\">";
  print "<select name=\"type\">\n";
#   print "<option></option>";
  print "<option value=\"all\">all</option>";
  foreach my $field (@data_fields) { 
    print "<option value=\"$field\">$field</option>";
  }
  print "<option value=\"textpresso\">textpresso</option>";
  print "</select>\n";
  my ($var, $afp_jfp) = &getHtmlVar($query, 'afp_jfp');
  unless ($afp_jfp eq 'jfp') { $afp_jfp = 'afp'; }
  print "<input type=\"hidden\" name=\"afp_jfp\" value=\"$afp_jfp\">\n";	# pass whether on afp or jfp mode
  print "<input type=\"submit\" name=\"action\" value=\"Show Data\"><br />\n";
  print qq(<table cellpadding="4">\n);
  print "<tr><td align=\"left\">DOI</td><td align=\"left\">WBPaperID</td><td align=\"left\">data link</td><td align=\"left\">textpresso html</td><td align=\"left\">proofs</td><td align=\"left\">pdf link</td><td align=\"left\">temp pdf</td><td align=\"left\">go link</td></tr>\n";
  my %proofs;
  my $page = get 'http://textpresso-dev.caltech.edu/gsa/worm/proofs/';
  my (@hrefs) = $page =~ m/a href="(.*?)"/g;
  foreach my $href (@hrefs) {
    my ($num) = $href =~ m/(\d+)/;
    $proofs{$num} = $href; }
  foreach my $joinkey (reverse sort keys %{ $pap{ident} } ) {
    my $pdf_link = 'no pdf'; my $temp_pdf_link = 'no temp pdf';
    if ($pap{pdf}{$joinkey}) { 
      my @pdf_links; my @temp_pdf_links;
      foreach my $pdfname (sort keys %{ $pap{pdf}{$joinkey} }) {
        my $timestamp = $pap{pdf}{$joinkey}{$pdfname};
        if ($pdfname =~ m/_temp\.pdf/) { push @temp_pdf_links, qq($timestamp $pdfname); }
          else { push @pdf_links, qq($timestamp $pdfname); } }
      $temp_pdf_link = join"<br/>", @temp_pdf_links;
      $pdf_link = join"<br/>", @pdf_links; }
    print "<tr>\n";
    my ($doiPreExt, $doiExt) = $pap{ident}{$joinkey} =~ m/\.(\d+)\.(\d+)$/;
    my $textcolor = 'black';
    if ($doiPreExt < 109) { $textcolor = 'gray'; }				# grey colour for test papers with low numbers
    if ( ($doiPreExt eq 109) && ($doiExt <= 103473) ) { $textcolor = 'gray'; }	# grey colour for test papers with low numbers
    my $textpressoHtml  = 'http://textpresso-dev.caltech.edu/gsa/worm/html/' . $doiExt . '.html';
    my $journalExt = 'ggg'; if ($pap{ident}{$joinkey} =~ m/\/genetics/) { $journalExt = 'genet'; }
    my $textpressoProof = '';
    if ($proofs{$doiExt}) { $textpressoProof = qq(<a href="http://textpresso-dev.caltech.edu/gsa/worm/proofs/$proofs{$doiExt}">proof</a>); }
    print "<td align=\"left\" style=\"color: $textcolor\">$pap{ident}{$joinkey}</td>\n";
    my $paper_link = "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?data_number=$joinkey&action=Search+%21";
    print "<td align=\"left\"><a href=\"$paper_link\">$joinkey</a></td>\n";
    my $link_text = 'link'; unless ($afpLasttouched{$joinkey}) { $link_text = 'nodata'; }
    my $journal_link = "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/journal/journal_first_pass.cgi?action=Curate&paper=$joinkey&passwd=$pap{pass}{$joinkey}";
    print "<td align=\"left\"><a href=\"$journal_link\">$link_text</a></td>\n";
    print "<td align=\"left\"><a href=\"$textpressoHtml\">html</a></td>\n";	# link to textpresso html for Karen  2015 09 10
    print "<td align=\"left\">$textpressoProof</td>\n";				# link to textpresso proof for Karen  2016 01 20
    print "<td align=\"left\">$pdf_link</td>\n";
    print "<td align=\"left\">$temp_pdf_link</td>\n";
    my $go_journal_link = "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/journal/journal_first_pass.cgi?action=CurateGO&paper=$joinkey&passwd=$pap{pass}{$joinkey}";
    print "<td align=\"left\"><a href=\"$go_journal_link\">link</a></td>\n";
    print "</tr>\n";
  } # foreach my $joinkey (sort keys %{ $pap{ident} } )
  print "<tr><td align=\"left\">DOI</td><td align=\"left\">WBPaperID</td><td align=\"left\">data link</td><td align=\"left\">textpresso html</td><td align=\"left\">proofs</td><td align=\"left\">pdf link</td><td align=\"left\">temp pdf</td><td align=\"left\">go link</td></tr>\n";
  print "</table>\n";
  foreach my $doi (sort keys %tdoi) { print qq(In <a href="http://textpresso-dev.caltech.edu/gsa/worm/incoming_xml/?C=M;O=A">textpresso</a> but missing in WormBase : <a href="http://textpresso-dev.caltech.edu/gsa/worm/incoming_xml/${doi}.xml">$doi</a><br/>\n); }
  print "</form>\n";
} # sub firstPage




sub padZeros {
  my $ticket = shift;
  if ($ticket < 10) { $ticket = '0000000' . $ticket; }
    elsif ($ticket < 100) { $ticket = '000000' . $ticket; }
    elsif ($ticket < 1000) { $ticket = '00000' . $ticket; }
    elsif ($ticket < 10000) { $ticket = '0000' . $ticket; }
    elsif ($ticket < 100000) { $ticket = '000' . $ticket; }
    elsif ($ticket < 1000000) { $ticket = '00' . $ticket; }
    elsif ($ticket < 10000000) { $ticket = '0' . $ticket; }
  return $ticket;
} # sub padZeros

