#!/usr/bin/perl

# New for curators to first pass fields

# Added javascript extendable textareas.  Made them hide by default.  Added ``Add information'' link
# to show hidden textareas.  2009 02 28
#
# Changed the link to toggle the hide / show state.  Changed the state to refer to the tr instead
# of the textarea, which allows a close button on the first td or the tr.  Moved the looping javascript
# that hid all textareas into first_pass.js, and have it match a regexp of ^tr on the id of the "tr"s 
# to make sure they're hidden.  2009 03 02
#
# Configured authors first_pass.cgi into curator_first_pass.cgi, using a curator_first_pass.js 
# Textareas autoexpand.  Columns can be hidden, textareas resize to conform to resize td space.
# 2009 03 04
#
# Changed TDs to have SPANs since hiding the TD gets rid of the whole cell, while having two sets of
# SPANs per cell, allow toggling of an ``expand / collapse'' set of arrows.  2009 03 05
#
# Created and populated curator, author, and textpresso tables (cfp_ afp_ tfp_), allow for query of them.
# Messed with the style properties of td and table.
# 2009 03 14
#
# Created a curator_first_pass.css to define td.normal and td.header  2009 03 15
#
# Forgot to replace subcats with normal cats.  2009 03 16
#
# Gave id to trs with curator fields.  Created ToggleHideSpan to click the field name arrow
# and hide / show the spans of textpresso / author / curator data.  No longer allow hiding of 
# description column since it's needed to hide / show the rowspans.  2009 03 17
# 
# added ajax call for genestudied, genesymbol, structcorr to get lab or wbgene based off of data 
# typed in a textarea matching a gene, locus, or sequence.  ajax call to :
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi
# 2009 03 19
#
# rewrote spans to have more explicit names for clearer javascript toggling of spans.  if either
# column or row is hidden, that cell's span is hidden.  
# renamed ToggleHideSpan into ToggleHideRowSpans   
# added validation of curator and paper when clicking any submit button.
# added link to wiki for documentation.  2009 03 21
#
# wrote &pgAuthorChecked and &pgCuratorData to write to postgres afp_ and cfp_ tables 
# (respectively, as well as _hst tables) when curator approval or rejection of afp_ 
# data changes, or curator cfp_ data changes.  2009 03 22
#
# Created &sendEmails(); which uses user's email address from two_email in %curators{mail} 
# to send out email to recepients if there's an email recepient, and there's body data
# (a composite of curator, author, and textpresso data), and if the send email checkbox is on.
# Display email text in the Flag return values table.
# Currently emails go to the curator, not the recepient.
# When sending email to structcorr, preprocess data with ajax call to 
# http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi?all=$curator_data&type=structcorr
# and if only HX matches send to 'worm-bug@sanger.ac.uk', if only RW matches, send to
# 'wormticket@watson.wustl.edu', otherwise send to both.
# Changed wbpaper_editor.cgi to have a TestNewForm link to here next to the usual curate link,
# it does not affect wpa_checked_out, might need to implement that later. 
# $result = $conn->exec( "INSERT INTO wpa_checked_out VALUES ( '$theHash{pubID}{html_value}', '$curators{std}{$theHash{curator}{html_value}}', NULL, 'valid', '$curators{std}{$theHash{curator}{html_value}}', CURRENT_TIMESTAMP )" );
# 2009 03 22
#
# Deal with curator tables, created afp_curator table with afp_curatr column instead of 
# regular afp_curator third column because of name conflict and them holding the same data
# anyway.  2009 03 23
#
# created &populateWpaGene(); to get any wbgenes in the curator textarea for genestudied
# and genesymbol, and populate wpa_gene if not already there.  2009 03 24
#
# show full field description when row expanded.  for Kimberly.  
# added &gotPreview to work like &getFlagged, but instead pass values as hidden, don't change 
# postgres, get email in preview mode.  2009 04 02
#
# Display comments in comment link for Karen.  2009 04 03
#
# INSERT into wpa_checked_out.  Form live.  2009 04 06
#
# Flag option in main page and preview page.  (karen)
# Preview and Flag page link to paper display.  (xiaodong, sort of)
# Preview page has textarea to edit curator data.  (jolene)
# Emails now have reference data on body.  (raymond)  2009 04 09
#
# extvariation, antibody, and transgene removed since they're happy with textpresso results.
# changed &sendEmail to skip mailing if the type is rnai and there is no curator data.
# 2009 05 14
#
# converted from Pg.pm to DBI.pm  2009 05 29
#
# TODO (added 2009 07 07) (maybe, make it clearer with Karen first)
# add new : authors, newcell, newbalancers, newstrains,
# put back : extvariation, antibody, transgene
# attach kyook to genesymbol, newsnp
#
# changed from wpa to pap tables, although they're not live yet  2010 06 24
# update &populateReference() to work with pap tables 
# got rid of &populateWpaGene()  since we're not populating those based on genestudied
#   because we're not doing curation anymore, although kimberly seems to want to 
# no longer update wpa_checked_out since it doesn't exist in pap tables, might come 
#   back as a cfp_ table if we bring back FP curation  2010 06 24
#
# brought back gene connections, now into pap_gene with &populatePapGene();
# 2010 07 23
#
# changed email of newsnp to mt3@sanger.ac.uk  2011 02 09
#
# added draciti to otherexpr  2011 02 10






use Jex;			# untaint, getHtmlVar, cshlNew, mailer
use strict;
use CGI;
use DBI;

use Tie::IxHash;
use LWP::Simple;
# use Ace;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 

my $blue = '#00ffcc';                   # redefine blue to a mom-friendly color
my $red = '#00ffff';                    # redefine red to a mom-friendly color


my $query = new CGI;
my $firstflag = 1;

my %hash;				# names of fields
my %name;
my %theHash;				# data in fields

my @pgTables;				# name of all pg tables
my %pgData;				# data in curator pg tables
my %autData;				# data in author pg tables
my %rejData;				# data in author pg tables rejected
my %txtData;				# data in textpresso pg tables

my %curators; tie %{ $curators{name} }, "Tie::IxHash";	# key num, value name

# NEW TABLES  matrices (maybe marker) timeofaction nocuratable
# RENAME structurecorrectionsanger to structurecorrection ;  newsnp to snp

my @cats = qw( spe gif gfp int gef rgn pfs seq cell sil oth );
my @spe = qw( celegans cnonbristol nematode nonnematode );
# my @gif = qw( genestudied genesymbol extvariation mappingdata );	# extvariation removed 2009 05 14
my @gif = qw( genestudied genesymbol mappingdata );
my @gfp = qw( newmutant rnai lsrnai overexpr chemicals mosaic siteaction timeaction genefunc humdis );
# my @phenanalysis = qw( newmutant rnai lsrnai overexpr chemicals );
my @int = qw( geneint funccomp geneprod );
my @gef = qw( otherexpr microarray genereg seqfeat matrices );
# my @rgn = qw( antibody transgene marker );				# antibody and transgene removed 2009 05 14
my @rgn = qw( marker );
my @pfs = qw( invitro domanal covalent structinfo massspec );
my @seq = qw( structcorr seqchange newsnp );
my @cell = qw( ablationdata cellfunc );
my @sil = qw( phylogenetic othersilico );
my @oth = qw( supplemental nocuratable comment );
$hash{cat}{spe} = [ @spe ];
$hash{cat}{gif} = [ @gif ];
$hash{cat}{gfp} = [ @gfp ];
# $hash{cat}{phenanalysis} = [ @phenanalysis ];
$hash{cat}{int} = [ @int ];
$hash{cat}{gef} = [ @gef ];
$hash{cat}{rgn} = [ @rgn ];
$hash{cat}{pfs} = [ @pfs ];
$hash{cat}{seq} = [ @seq ];
$hash{cat}{cell} = [ @cell ];
$hash{cat}{sil} = [ @sil ];
$hash{cat}{oth} = [ @oth ];


print "Content-type: text/html\n\n";
my $title = 'Paper Flagging Form';
# my ($header, $footer) = &cshlNew($title);

my $footer = '</HTML>';
# $header = '<HTML><HEAD>';
my $header = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><HTML><HEAD>';

$header .= '<link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/jex.css" /><link rel="stylesheet" href="http://tazendra.caltech.edu/~azurebrd/stylesheets/curator_first_pass.css" /><script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/test.js"></script><script type="text/javascript" src="http://tazendra.caltech.edu/~azurebrd/javascript/curator_first_pass.js"></script>';

# $header =~ s/<\/head>/<link rel="stylesheet" href="http:\/\/tazendra.caltech.edu\/~azurebrd\/stylesheets\/jex.css" \/><script type="text\/javascript" src="http:\/\/tazendra.caltech.edu\/~azurebrd\/javascript\/test.js"><\/script><script type="text\/javascript" src="http:\/\/tazendra.caltech.edu\/~azurebrd\/javascript\/first_pass.js"><\/script>\n<\/head>/;

# $header .= '</HEAD><BODY onLoad="ShowData()">';
# $header .= '</HEAD><BODY onLoad="cleanForm();">';
# $header .= '</HEAD><BODY>';



print "$header\n";		# make beginning of HTML page

&populateCurators();
&hashName();


&process();			# see if anything clicked
# &displayQuery();		# show query box
print "$footer"; 		# make end of HTML page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; &displayTypeOne(); }

# UNCOMMENT THESE TO MAKE THEM FUNCTIONAL
  if ($action eq 'Curate') { &displayTypeOne(); }
  elsif ($action eq 'Query') { &displayTypeOne(); }
  elsif ($action eq 'Preview') { &gotPreview(); }
  elsif ($action eq 'Flag') { &gotFlagged(); }
  elsif ($action eq 'See Comments') { &seeComments(); }
  elsif ($action eq 'Review') { &gotReview(); }
  elsif ($action eq 'ListPgTables') { &listPgTables(); }		# for other forms to find all the postgres tables

#   elsif ($action eq 'Submit Text') { &gotText(); }
#   elsif ($action eq 'Testing') { &testing(); }
}

sub testing {
  print "<p><span style=\"font-size:x-large; color:red\">NO, testing</span></p>\n";
}

sub seeComments {
  &printForm();
  print "</form>\n";
  my %comment;
  my $result = $dbh->prepare( "SELECT * FROM afp_comment WHERE afp_comment IS NOT NULL;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $comment{$row[0]}{afp} = $row[1]; }
  my $result = $dbh->prepare( "SELECT * FROM cfp_comment WHERE cfp_comment IS NOT NULL;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $comment{$row[0]}{cfp} = $row[1]; }
  print "<table border=\"1\" cellpadding=\"3\" style=\"border-style: none;\">\n";
  print "<tr><td class=\"normal\">WBPaper</td><td class=\"normal\">Author Comment</td><td class=\"normal\">Curator Comment</td></tr>\n";
  foreach my $joinkey (sort keys %comment) {
    my $cfp = ""; my $afp = "";
    if ($comment{$joinkey}{afp}) { $afp = $comment{$joinkey}{afp}; }
    if ($comment{$joinkey}{cfp}) { $cfp = $comment{$joinkey}{cfp}; }
    print "<tr><td class=\"normal\">$joinkey</td><td class=\"normal\">$afp</td><td class=\"normal\">$cfp</td></tr>\n";
  } # foreach my $joinkey (sort keys %comment)
  print "</table>\n";
} # sub seeComments

sub gotFlagged {		# if Flag pressed
  &printForm();
  my ($oop, $paper) = &getHtmlVar($query, 'html_value_paper');
  ($oop, my $curator) = &getHtmlVar($query, 'html_value_curator');
  print "<input type=hidden name=\"html_value_paper\" value=\"$paper\">\n"; print "<input type=hidden name=\"html_value_curator\" value=\"$curator\">\n";
  print "Paper : <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$paper\" target=new>WBPaper$paper</a><br />\n";
  print "Curator : $curators{name}{$curator}<br />\n";

  my $referenceData = &populateReference($paper);
  my $body = "Paper $paper flagged\n";
  print "<table border=\"1\" cellpadding=\"3\" style=\"border-style: none;\">\n";
  print "<tr><td>table</td><td>textpresso data</td><td>approve author</td><td>author data</td><td>email curator</td><td>curator data</td><td>email</td></tr>\n";
  foreach my $cat (@cats, "comment") {
    foreach my $table (@{ $hash{cat}{$cat} }) { 	# for each table in each cat, get values and display
      ($oop, my $textpresso) = &getHtmlVar($query, "hidden_textpresso_$table");
      ($oop, my $aut_checked) = &getHtmlVar($query, "author_checked_$table");
      ($oop, my $author) = &getHtmlVar($query, "hidden_author_$table");
      if ($author) { 
        if ($aut_checked eq 'on') { $aut_checked = 'approved'; } else { $aut_checked = 'rejected'; }
        &pgAuthorChecked($table, $paper, $curator, $aut_checked); }	# only write data if there is author data
      ($oop, my $cur_checked) = &getHtmlVar($query, "curator_checked_$table");
      ($oop, my $curator_data) = &getHtmlVar($query, "curator_$table");
      &pgCuratorData($table, $paper, $curator, $curator_data);
      ($oop, my $email) = &getHtmlVar($query, "hidden_email_$table");
      if ($author || $curator_data || $textpresso) {
        my $fullemail = '';
        if ($cur_checked && $hash{mail}{$table}) { ($fullemail) = &sendEmail('live', $table, $paper, $curator, $curator_data, $author, $textpresso, $referenceData); }
#         if ( ($table eq 'genesymbol') || ($table eq 'genestudied') ) { &populateWpaGene($curator, $paper, $table, $curator_data); } # No longer using this in new pap tables  2010 06 24
        if ( ($table eq 'genesymbol') || ($table eq 'genestudied') ) { &populatePapGene($curator, $paper, $table, $curator_data); } # Bringing this back for pap_gene for Karen  2010 07 23
        print "<tr><td>$table</td><td>$textpresso</td><td>$aut_checked</td><td>$author</td><td>$cur_checked</td><td>$curator_data</td><td>$fullemail</td></tr>\n";
      }
#       if ( ($checked) || ($table eq 'comment') ) { 
#         &writePg($table, $paper, 'checked');
#         $body .= "$table\tchecked\n";
#         my ($data) = &getPgData($table, $paper);
#         &checkedTable($table, $data); }
    } # foreach my $table (@{ $hash{cat}{$cat} })
  } # foreach my $cat (@cats)
  print "</table>";
  &pgCuratorData('curator', $paper, $curator, "two$curator");	# deal with curator tables
#   print "<P><BR><INPUT TYPE=submit NAME=action VALUE=\"Submit Text\"><BR>\n";
#   print "</FORM>\n";
#   &messageAndrei($body);
  print "</form>\n";
} # sub gotFlagged

sub gotPreview {		# if Preview pressed pass values as hidden, don't change postgres, get email in preview mode.  2009 04 02
  &printForm();
  my ($oop, $paper) = &getHtmlVar($query, 'html_value_paper');
  ($oop, my $curator) = &getHtmlVar($query, 'html_value_curator');
  print "<input type=hidden name=\"html_value_paper\" value=\"$paper\">\n"; print "<input type=hidden name=\"html_value_curator\" value=\"$curator\">\n";
  print "Paper : <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$paper\" target=new>WBPaper$paper</a><br />\n";
  print "Curator : $curators{name}{$curator}<br />\n";
  print "<input type=\"submit\" name=\"action\" VALUE=\"Flag\"><br />\n";

  my $referenceData = &populateReference($paper);
  my $body = "Paper $paper flagged\n";
  print "<table border=\"1\" cellpadding=\"3\" style=\"border-style: none;\">\n";
  print "<tr><td>table</td><td>textpresso data</td><td>approve author</td><td>author data</td><td>email curator</td><td>curator data</td><td>email</td></tr>\n";
  foreach my $cat (@cats, "comment") {
    foreach my $table (@{ $hash{cat}{$cat} }) { 	# for each table in each cat, get values and display
      ($oop, my $textpresso) = &getHtmlVar($query, "hidden_textpresso_$table");
      print "<input type=hidden name=\"hidden_textpresso_$table\" value=\"$textpresso\">\n"; 
      ($oop, my $aut_checked) = &getHtmlVar($query, "author_checked_$table");
      print "<input type=hidden name=\"author_checked_$table\" value=\"$aut_checked\">\n"; 
      ($oop, my $author) = &getHtmlVar($query, "hidden_author_$table");
      print "<input type=hidden name=\"hidden_author_$table\" value=\"$author\">\n"; 
      if ($author) { 
        if ($aut_checked eq 'on') { $aut_checked = 'approved'; } else { $aut_checked = 'rejected'; } }
      ($oop, my $cur_checked) = &getHtmlVar($query, "curator_checked_$table");
      print "<input type=hidden name=\"curator_checked_$table\" value=\"$cur_checked\">\n"; 
      ($oop, my $curator_data) = &getHtmlVar($query, "curator_$table");
#       print "<input type=hidden name=\"curator_$table\" value=\"$curator_data\">\n"; 	# allow textarea editing of curator data instead  2009 04 09
      ($oop, my $email) = &getHtmlVar($query, "hidden_email_$table");
      print "<input type=hidden name=\"hidden_email_$table\" value=\"$email\">\n"; 
      if ($author || $curator_data || $textpresso) {
        my $fullemail = '';
        if ($cur_checked && $hash{mail}{$table}) { ($fullemail) = &sendEmail('preview', $table, $paper, $curator, $curator_data, $author, $textpresso, $referenceData); }
        print "<tr><td>$table</td><td>$textpresso</td><td>$aut_checked</td><td>$author</td><td>$cur_checked</td>";
        print "<td><textarea id=\"curator_$table\" name=\"curator_$table\" cols=\"40\" rows=\"1\" onKeyUp=\"MatchFieldExpandTextarea(\'curator_$table\', \'$table\')\">$curator_data</textarea></td>\n"; 	# allow textarea editing of curator data in preview  2009 04 09
        print "<td>$fullemail</td></tr>\n";
      }
    } # foreach my $table (@{ $hash{cat}{$cat} })
  } # foreach my $cat (@cats)
  print "</table>";
  print "<input type=\"submit\" name=\"action\" VALUE=\"Flag\">\n";
  print "</form>\n";
} # sub gotPreview

sub populateReference {
  my $joinkey = shift;
  my $referenceData = '';
  my %authors;
  my $result = $dbh->prepare( "SELECT * FROM pap_author WHERE joinkey = '$joinkey\' ;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $authors{id}{$row[2]}{$row[1]}++; }       # get author_ids
  foreach my $order (sort keys %{ $authors{id} }) {
    foreach my $aid (sort keys %{ $authors{id}{$order} }) {             # get author names
      my $result = $dbh->prepare( "SELECT * FROM pap_author_index WHERE author_id = '$aid' ;" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
      while (my @row = $result->fetchrow) { $authors{name}{$order}{$row[1]}++; } } }
  foreach my $order (sort keys %{ $authors{name} }) {                   # append to reference
    foreach my $name (sort keys %{ $authors{name}{$order} }) {
      $referenceData .= "\nauthor == $name"; } }
  my @refparams = qw(identifier title journal volume pages year abstract);
  foreach my $pap_table (@refparams) {  # for each pgsql reference data parameter
    my $result = $dbh->prepare( "SELECT * FROM pap_$pap_table WHERE joinkey = '$joinkey\';" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    $referenceData .= "\n$pap_table == ";	# add parameter name to reference info
    while (my @row = $result->fetchrow) {
      if ($row[1]) { $referenceData .= "$row[1]"; } }
  } # foreach $_ (@refparams)
  return $referenceData;
} # sub populateReference

# sub populateWpaReference {
#   my $joinkey = shift;
#   my $referenceData = '';
#   my %authors;
#   my $result = $dbh->prepare( "SELECT * FROM wpa_author WHERE joinkey = '$joinkey\' ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     if ($row[3] eq 'valid') { $authors{id}{$row[2]}{$row[1]}++; }       # get author_ids
#       else { delete $authors{id}{$row[2]}{$row[1]}; } }
#   foreach my $order (sort keys %{ $authors{id} }) {
#     foreach my $aid (sort keys %{ $authors{id}{$order} }) {             # get author names
#       my $result = $dbh->prepare( "SELECT * FROM wpa_author_index WHERE author_id = '$aid' ORDER BY wpa_timestamp;" );
#       $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#       while (my @row = $result->fetchrow) {
#         if ($row[3] eq 'valid') { $authors{name}{$order}{$row[1]}++; }
#           else { delete $authors{name}{$order}{$row[1]}; } } } }
#   foreach my $order (sort keys %{ $authors{name} }) {                   # append to reference
#     foreach my $name (sort keys %{ $authors{name}{$order} }) {
#       $referenceData .= "\nauthor == $name"; } }
#   my @refparams = qw(identifier title journal volume pages year abstract);
#   foreach my $wpa_table (@refparams) {  # for each pgsql reference data parameter
#     my $result = $dbh->prepare( "SELECT * FROM wpa_$wpa_table WHERE joinkey = '$joinkey\';" );
#     $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#     $referenceData .= "\n$wpa_table == ";
#                                         # add parameter name to reference info
#     while (my @row = $result->fetchrow) {
#       if ($row[1]) { $referenceData .= "$row[1]"; }
#     }
#   } # foreach $_ (@refparams)
#   return $referenceData;
# } # sub populateWpaReference

sub populatePapGene {		# get any wbgenes in the curator textarea and populate pap_gene if not already there  2010 07 23
  my ($curator, $paper, $table, $curator_data) = @_;
  $curator_data =~ s/\n/ /g;
  my %pggenes; my $highest_order;
  my $result = $dbh->prepare( "SELECT * FROM pap_gene WHERE joinkey = '$paper' ORDER BY pap_order;" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  while (my @row = $result->fetchrow) { $pggenes{$row[1]}++; $highest_order = $row[2]; }
  my $ajax = get "http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi?all=$curator_data&type=$table";
  my (@pairs) = split", ", $ajax;
  my (@wbgenes) = $ajax =~ m/WBGene(\d+)/g;
  my @commands;
  foreach my $pair (@pairs) {
    my ($manual_data, $wbgene) = $pair =~ m/^(\S+) \(WBGene(\d+)\)/;
    next if ($pggenes{$wbgene});
    $highest_order++;
    my $command = "INSERT INTO pap_gene VALUES ('$paper', '$wbgene', '$highest_order', 'two$curator', CURRENT_TIMESTAMP, 'Inferred_automatically \"from curator first pass cfp_$table\"');";
    push @commands, $command;
    $command = "INSERT INTO h_pap_gene VALUES ('$paper', '$wbgene', '$highest_order', 'two$curator', CURRENT_TIMESTAMP, 'Inferred_automatically \"from curator first pass cfp_$table\"');";
    push @commands, $command;
    $highest_order++;
    $command = "INSERT INTO pap_gene VALUES ('$paper', '$wbgene', '$highest_order', 'two$curator', CURRENT_TIMESTAMP, 'Manually_connected	\"$manual_data\"');";
    push @commands, $command;
    $command = "INSERT INTO h_pap_gene VALUES ('$paper', '$wbgene', '$highest_order', 'two$curator', CURRENT_TIMESTAMP, 'Manually_connected	\"$manual_data\"');";
    push @commands, $command;
  } # foreach my $wbgene (@wbgenes)
  foreach my $command (@commands) {
#     print "$command<br />\n";
# UNCOMMENT TO make live
    $result = $dbh->do( $command );
  } # foreach my $command (@commands)
} # sub populatePapGene

# No longer using this in new pap tables  2010 06 24
# sub populateWpaGene {		# get any wbgenes in the curator textarea and populate wpa_gene if not already there  2009 03 24
#   my ($curator, $paper, $table, $curator_data) = @_;
#   $curator_data =~ s/\n/ /g;
#   my %pggenes;
#   my $result = $dbh->prepare( "SELECT * FROM wpa_gene WHERE joinkey = '$paper' ORDER BY wpa_timestamp;" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) {
#     my ($wbgene) = $row[1] =~ m/(WBGene\d+)/; 
#     if ($row[3] eq 'valid') { $pggenes{$wbgene}++; }
#       else { delete $pggenes{$wbgene}; } }
#   my $ajax = get "http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi?all=$curator_data&type=$table";
#   my (@wbgenes) = $ajax =~ m/(WBGene\d+)/g;
#   foreach my $wbgene (@wbgenes) {
#     next if ($pggenes{$wbgene});
#     my $command = "INSERT INTO wpa_gene VALUES ('$paper', '$wbgene', 'Inferred_automatically \"from curator first pass cfp_$table\"', 'valid', 'two$curator', CURRENT_TIMESTAMP);";
# #     print "$command<br />\n";
# # UNCOMMENT TO make live
#     $result = $dbh->do( $command );
#   } # foreach my $wbgene (@wbgenes)
# } # sub populateWpaGene

sub sendEmail {
  my ($preview, $table, $paper, $curator, $curator_data, $author_data, $textpresso_data, $referenceData) = @_;
  my $body = $curator_data;
  next if ( (!$body) && ($table eq 'rnai') );			# don't email rnai if there's no curator data, for Gary  2009 05 14
  if ($author_data) { 
    if ($body) { $body .= "\n"; }
    $body .= "Author Data : $author_data"; }
  if ($textpresso_data) { 
    if ($body) { $body .= "\n"; }
    $body .= "Author Data : $textpresso_data"; }
  my $recpt  = $hash{mail}{$table};
  my $sender = $curators{mail}{$curator};
  my $subject = "WBPaper$paper : $hash{name}{$table}";
  if ($table eq 'structcorr') { 
    $curator_data =~ s/\n/ /g;
    my $ajax = get "http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi?all=$curator_data&type=structcorr";
    my $bits = 0;
    if ($ajax =~ m/\(HX\)/) { $bits += 1; }	# hinxton
    if ($ajax =~ m/\(RW\)/) { $bits += 2; }	# wash U
    if ($bits == 1) { $recpt = 'worm-bug@sanger.ac.uk'; }
    elsif ($bits == 2) { $recpt = 'wormticket@watson.wustl.edu'; }
    else { 1; }		# keep email the same
    if ($body =~ m/^(.*?);/) { $subject .= " : $1"; }
    elsif ($body =~ m/^(.{30})/) { $subject .= " : $1"; }
    else { $subject .= " : $body"; }
  }
  $body .= "\n\nReference :$referenceData";
  my $body_text = $body; $body_text =~ s/\n/<br \/>\n/g;
  my $text = "To: $recpt<br />\nFrom: $sender<br />\nSubject: $subject<br />\nBody: $body_text\n";
# UNCOMMENT when live
  if ($preview eq 'live') {
    &mailer($sender, $recpt, $subject, $body);		# email to RECEPIENT
#     &mailer($sender, $sender, $subject, $body);			# email to CURATOR
  }
  return $text;
} # sub sendEmail

sub pgAuthorChecked {
  my ($table, $paper, $curator, $aut_checked) = @_;
  my $curator = 'two' . $curator;					# store two\d instead of just \d
  my (@autdata) = &getAutData($table, $paper);				# get what was in postgres
  return if ($aut_checked eq $autdata[4]);				# skip if there is no change to the approve / reject state
  my @pgcommands; my $command;
  $command = "DELETE FROM afp_$table WHERE joinkey = '$autdata[0]';";
  push @pgcommands, $command;						# delete the current afp_ data
  $command = "INSERT INTO afp_$table VALUES ('$autdata[0]', '$autdata[1]', '$autdata[2]', '$curator', '$aut_checked');";
  push @pgcommands, $command;						# insert the new afp_ data
  $command = "INSERT INTO afp_${table}_hst VALUES ('$autdata[0]', '$autdata[1]', '$autdata[2]', '$curator', '$aut_checked');";
  push @pgcommands, $command;						# insert the afp_ _hst data
  foreach $command (@pgcommands) {
#     print "$command<br />\n";
    my $result = $dbh->do( $command );
  }
} # sub pgAuthorChecked

sub pgCuratorData {							# write to cfp tables
  my ($table, $joinkey, $curator, $data) = @_;
  if ($data =~ m/\r\n/) { $data =~ s/\r\n/\n/g; }			# get rid of \r for eq matching with postgres
  if ($data =~ m/\'/) { $data =~ s/\'/''/g; }				# escape '
  my (@pgdata) = &getPgData($table, $joinkey);
  return if ($pgdata[1] eq $data);
  my $curator = 'two' . $curator;					# store two\d instead of just \d
#   print "PGD $pgdata[1] DAT $data END<br />\n";
  my @pgcommands; my $command;
  $command = "DELETE FROM cfp_$table WHERE joinkey = '$joinkey';";
  push @pgcommands, $command;						# delete the current cfp_ data
  $command = "INSERT INTO cfp_$table VALUES ('$joinkey', '$data', '$curator');";
  push @pgcommands, $command;						# insert the new cfp_ data
  $command = "INSERT INTO cfp_${table}_hst VALUES ('$joinkey', '$data', '$curator');";
  push @pgcommands, $command;						# insert the cfp_ _hst data
  foreach $command (@pgcommands) {
#     print "$command<br />\n";
    my $result = $dbh->do( $command );
  }
} # sub pgCuratorData 

sub gotReview {								# write to cfp_nocuratable table
  &printForm();
  print "</form>\n";
  my ($oop, $paper) = &getHtmlVar($query, 'html_value_paper');
  ($oop, my $curator) = &getHtmlVar($query, 'html_value_curator');
  print "Review.<BR>\n";
  &pgCuratorData('nocuratable', $paper, $curator, 'review');		# say review instead of checked (for Gary).  2009 04 20
  &pgCuratorData('curator', $paper, $curator, "two$curator");		# last field needs to be "two$curator", not 'review'  2009 04 07
#   &messageAndrei("$paper is a review");
} # sub gotReview


sub printForm {
  print "<form id=\"typeOneForm\" method=post action=\"curator_first_pass.cgi\" onsubmit=\"return ValidateCuratorPaper()\">\n";
#   print "<form method=\"post\" id=\"typeOneForm\" action=\"curator_first_pass.cgi\">\n";
} # sub printForm

sub printHtmlSelectCuratorsPaper {   # print html select blocks for curators
  print "<table>\n";
  if ($theHash{curator}{html_value} eq 'NULL') { $theHash{curator}{html_value} = ''; }	# clear NULL
  print "<tr><td><b>Curator <span style=\"color:red\">REQUIRED</span></b> :</td>\n";
  print "<td><select id=\"html_value_curator\" name=\"html_value_curator\" SIZE=1>\n";
#   print "      <option selected>$theHash{$type}{html_value}</option>\n";
  foreach (keys %{ $curators{name} }) { 
    my $selected = ''; if ($theHash{curator}{html_value} eq $_) { $selected = ' selected=\"selected\"'; } 
    print "      <option $selected value=\"$_\">$curators{name}{$_}</option>\n"; }
  print "    </select></td></tr>\n";

  print "<tr><td><b>Paper <span style=\"color:red\">REQUIRED</span></b> : </td>\n";
  print "<td><input id=\"html_value_paper\" name=\"html_value_paper\" value=\"$theHash{paper}{html_value}\" SIZE=10></td>\n";
  print "<td><input type=\"submit\" name=\"action\" id=\"action\" value=\"Query\">";
  print "<input type=\"submit\" name=\"action\" VALUE=\"Preview\">";
  print "<input type=\"submit\" name=\"action\" VALUE=\"Flag\"></td>\n";
  print "</tr>\n";
  print "</table>\n";
} # sub printHtmlSelectCuratorsPaper

sub listPgTables {		# for other forms to find all the postgres tables
  &printForm();
  print "</form>\n";
  foreach my $cat (@cats) {
    foreach my $table (@{ $hash{cat}{$cat} }) {
      if ($hash{cat}{$table}) {
        foreach my $subcat ( @{ $hash{cat}{$table} } ) { push @pgTables, $subcat; } }
      else { push @pgTables, $table; } } }
  foreach my $table (@pgTables) { print "PGTABLE : $table<br />\n"; }
}

sub populatePgData {
  my $paper = shift;
  foreach my $cat (@cats) {
    foreach my $table (@{ $hash{cat}{$cat} }) {
      if ($hash{cat}{$table}) {
        foreach my $subcat ( @{ $hash{cat}{$table} } ) { push @pgTables, $subcat; } }
      else { push @pgTables, $table; } } }
  foreach my $table (@pgTables) {
    my (@pgdata) = &getPgData($table, $paper);
    my (@autdata) = &getAutData($table, $paper);
    my (@txtdata) = &getTxtData($table, $paper);
#     if ($pgdata)  { $pgData{cfp}++; $pgData{$table}  = $pgdata; }
#     if ($autdata) { $pgData{afp}++; $autData{$table} = $autdata; }
#     if ($txtdata) { $pgData{tfp}++; $txtData{$table} = $txtdata; }
  } # foreach my $table (@pgTables)
  my (@junk) = &getPgData('curator_hst', $paper);
} # sub populatePgData

sub getTxtData {
  my ($table, $joinkey) = @_;
  my $result = $dbh->prepare( "SELECT * FROM tfp_$table WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow();
  if ($row[1]) { $pgData{tfp}++; $txtData{$table} = $row[1]; }
  return @row;
} # sub getTxtData

sub getAutData {
  my ($table, $joinkey) = @_;
  my $result = $dbh->prepare( "SELECT * FROM afp_$table WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow();
  if ($row[4]) { if ($row[4] eq 'rejected') { $rejData{$table} = 'rejected'; } }	# reject only if rejected (otherwise checkbox on)
  if ($row[1]) { $pgData{afp}++; $autData{$table} = $row[1]; }
  return @row;
} # sub getAutData

sub getPgData {
  my ($table, $joinkey) = @_;
  my $result = $dbh->prepare( "SELECT * FROM cfp_$table WHERE joinkey = '$joinkey';" );
  $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
  my @row = $result->fetchrow();
  if ($row[1]) { $pgData{cfp}++; 
    if ($table eq 'curator_hst') { $row[1] =~ s/two//; $table = 'curator'; }
    $pgData{$table} = $row[1]; }
  return @row;
} # sub getPgData


sub displayTypeOne {
  &printForm();
#   print "<p><span style=\"font-size:x-large; color:red\">NO, testing</span></p>\n";
  print "<p><a href=\"http://www.wormbase.org/wiki/index.php/Texpresso/Author/Curator_interim_form\"><span style=\"font-size:x-large\">Documentation</span></a></p>\n";
  print "<p><b>If this is a <span style=\"color:red\">Review</span> just click this button and ignore the fields below : </b><input type=\"submit\" name=\"action\" id=\"action\" value=\"Review\"><br /></p>\n";

  (my $oop, my $paper) = &getHtmlVar($query, 'html_value_paper');
  unless ($paper) { $paper = '00000003'; } $theHash{paper}{html_value} = $paper;
  &populatePgData($paper);
  ($oop, my $curator) = &getHtmlVar($query, 'html_value_curator');
  if ($curator) { $theHash{curator}{html_value} = $curator; }
  my $send_email = 'checked=\"checked\"'; if ($pgData{curator}) { $send_email = ''; }	# if it has been curated do not send email by default and viceversa
#   print "Last $pgData{curator} curator<br />\n";

#   print "INSERT INTO wpa_checked_out VALUES ( '$paper', 'two$curator', NULL, 'valid', 'two$curator', CURRENT_TIMESTAMP )<br />\n" ;
#   my $result = $dbh->do( "INSERT INTO wpa_checked_out VALUES ( '$paper', 'two$curator', NULL, 'valid', 'two$curator', CURRENT_TIMESTAMP )" );	# check out paper  2009 04 06	# this table is not going to exist in new paper tables, might come back as a cfp_ table if we bring back FP curation  2010 06 24

  printHtmlSelectCuratorsPaper();

  print "Toggle Hide of Column : \n";
#   print "<a href=\"javascript:ToggleHideColSpans(\'description\')\">description</a> ";
  print "<a href=\"javascript:ToggleHideColSpans(\'textpresso\')\">textpresso</a> ";
  print "<a href=\"javascript:ToggleHideColSpans(\'author\')\">author</a> ";
  print "<a href=\"javascript:ToggleHideColSpans(\'curator\')\">curator</a> ";
  print "<a href=\"javascript:ToggleHideColSpans(\'email\')\">email</a><br />";
  print "<table border=\"1\" cellpadding=\"3\" style=\"border-style: none;\">\n";
  foreach my $cat (@cats) {
    &printColumnsTops($cat);
    print "<tr id=\"tr_cat_${cat}\"><td colspan=\"5\" class=\"header\" >$hash{name}{$cat}</td></tr>\n";
    foreach my $table (@{ $hash{cat}{$cat} }) { 
      print "<tr id=\"tr_field_${table}\">\n";
#       print "<td>$table</td>";
      print "<td id=\"td_description_data_$table\" class=\"normal\" valign=\"top\">\n";
      print "<span id=\"span_description_${table}_arrow_right\" title=\"description\">";
      print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowRight.png\" onClick=\"ToggleHideRowSpans(\'$table\')\" \/>";
      print "<a href=\"javascript:alert(\'$hash{name}{$table}\')\">$table</a></span>";
      print "<span id=\"span_description_${table}_arrow_down\">";
      print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideRowSpans(\'$table\')\" \/>";
      print "<a href=\"javascript:alert(\'$hash{name}{$table}\')\">$table</a> <br />$hash{name}{$table}</span></td>\n";	# show full description when row expanded  2009 04 02
#       print "<td id=\"td_description_data_$table\" class=\"normal\" valign=\"top\">\n";
#       print "<span id=\"span_description_${table}_data\"><a href=\"javascript:alert(\'$hash{name}{$table}\')\">$table</a></span></td>";

      my $textpresso_data = "";
      if ($txtData{$table}) { $textpresso_data = $txtData{$table}; }
#       my $textpresso_data = "textpresso data goes here. ";
#       $textpresso_data .= "textpresso data goes here. "; $textpresso_data .= "textpresso data goes here. "; $textpresso_data .= "textpresso data goes here. ";
        # span is first childNodes of parentNode td, used onload to erase span if there is no hidden data (curator_first_pass.js)
      print "<td id=\"td_textpresso_data_$table\" class=\"normal\" valign=\"top\">";
      print "<span id=\"span_textpresso_${table}_data\"><a href=\"javascript:MergeIntoCurator(\'$table\', \'textpresso\')\">merge</a><br />$textpresso_data</span>\n";
      print "<input type=\"hidden\" id=\"hidden_textpresso_$table\" name=\"hidden_textpresso_$table\" value=\"$textpresso_data\" />";	# hidden value for MergeIntoCurator to merge data
      print "</td>\n";

      my $author_data = ''; my $author_print_data = '';		# author print data is what gets printed, needs to replace newline with <br />
      my $approve_check = ''; unless ($rejData{$table}) { $approve_check = 'checked=\"checked\"'; }
#       $author_data .= "author data goes here. "; $author_data .= "author data goes here. "; $author_data .= "author data goes here. ";
      if ($autData{$table}) { $author_print_data = $author_data = $autData{$table}; }
      print "<td id=\"td_author_data_$table\" class=\"normal\" valign=\"top\">";
        # span is first childNodes of parentNode td, used onload to erase span if there is no hidden data (curator_first_pass.js)
      print "<span id=\"span_author_${table}_data\">\n";
      print "<input type=\"checkbox\" id=\"author_checked_$table\" name=\"author_checked_$table\" $approve_check>yes <a href=\"javascript:MergeIntoCurator(\'$table\', \'author\')\">merge</a><br />\n";
      if ($author_print_data =~ m/\n/) { $author_print_data =~ s/\n/<br \/>/g; }
      print "$author_print_data\n";
      print "</span>\n";
      print "<input type=\"hidden\" id=\"hidden_author_$table\" name=\"hidden_author_$table\" value=\"$author_data\" />";		# hidden value for MergeIntoCurator to merge data
      print "</td>\n";

#       my $curator_data = "curator data goes here";
      my $curator_data = "";
      if ($pgData{$table}) { $curator_data = $pgData{$table}; }
      print "<td id=\"td_curator_data_$table\" class=\"normal\" valign=\"top\"><span id=\"span_curator_${table}_data\">\n";
#       if ( ($table eq 'transgene') || ($table eq 'antibody') ) { $send_email = ''; }	# turn off sending email checkbox for those two for Wen and Karen  2009 05 07	# this fields are gone 2009 05 14
      print "<input type=\"checkbox\" id=\"curator_checked_$table\" name=\"curator_checked_$table\" $send_email>send<br />\n";
      if ( ($table eq 'structcorr') || ($table eq 'genestudied') || ($table eq 'genesymbol') ) {
        # these fields can have textarea data match gene information from an ajax call to http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi  2009 03 19
        print "<textarea id=\"curator_$table\" name=\"curator_$table\" cols=\"40\" rows=\"1\" onKeyUp=\"MatchFieldExpandTextarea(\'curator_$table\', \'$table\')\">$curator_data</textarea>\n";
        print "<div id=\"div_curator_$table\" name=\"div_curator_$table\"></div>\n"; }
      else {
          print "<textarea id=\"curator_$table\" name=\"curator_$table\" cols=\"40\" rows=\"1\" onKeyUp=ExpandTextarea(\"curator_$table\")>$curator_data</textarea>\n"; }
      print "</span></td>\n";

      print "<td id=\"td_email_data_$table\" class=\"normal\" valign=\"top\">";
      print "<span id=\"span_email_${table}_data\">$hash{mail}{$table}</span>\n";
      print "<input type=\"hidden\" id=\"hidden_email_$table\" name=\"hidden_email_$table\" value=\"$hash{mail}{$table}\" />";	# hidden value for onLoad to grey out
      print "</td>\n";

      print "</tr>\n";
#       my ($data) = &getPgData($table, $paper);
#       my $checked = ''; if ($pgData{$table}) { $checked = 'checked=\"checked\"'; }
#       print "<INPUT TYPE=checkbox NAME=\"${table}_check\" $checked>$hash{name}{$table} <FONT COLOR=red>$table</FONT><BR>\n"; 
#       print "<INPUT TYPE=checkbox NAME=\"${table}_check\" $checked>$hash{name}{$table} <FONT COLOR=white>$table</FONT><BR>\n"; 
    }
  } # foreach my $cat (@cats)
  print "</table>\n";
  print "<p><br /><input type=\"submit\" name=\"action\" VALUE=\"See Comments\"><br />\n";
  print "<input type=\"submit\" name=\"action\" VALUE=\"Preview\">";
  print "<input type=\"submit\" name=\"action\" VALUE=\"Flag\"><br /></p>\n";
  print "</form>\n";
} # sub displayTypeOne

sub printColumnsTops {
  my $cat = shift;
  print "<tr>\n";
#   print "<td id=\"td_description_top\" class=\"normal\" valign=\"top\">\n";
#   print "<span id=\"span_description_arrow_down\" title=\"description\">";
#   print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'description\')\" \/>";
#   print "</span>";
#   print "<span id=\"span_description_arrow_right\">";
#   print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowRight.png\" onClick=\"ToggleHideColSpans(\'description\')\" \/>";
#   print "Description</span></td>\n";
  print "<td id=\"td_description_top\" class=\"normal\" valign=\"top\">\n";	# no longer collapse description field
  print "<span id=\"span_description_${cat}_arrow_down\">Description</span></td>\n";
  print "<td id=\"td_textpresso_top\" class=\"normal\" valign=\"top\">";
  print "<span id=\"span_textpresso_${cat}_arrow_right\" title=\"textpresso\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowRight.png\" onClick=\"ToggleHideColSpans(\'textpresso\')\" \/>";
  print "</span>";
  print "<span id=\"span_textpresso_${cat}_arrow_down\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'textpresso\')\" \/>";
  print "Textpresso</span></td>\n";
  print "<td id=\"td_author_top\" class=\"normal\" valign=\"top\">";
  print "<span id=\"span_author_${cat}_arrow_right\" title=\"author\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowRight.png\" onClick=\"ToggleHideColSpans(\'author\')\" \/>";
  print "</span>";
  print "<span id=\"span_author_${cat}_arrow_down\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'author\')\" \/>";
  print "Author</span></td>\n";
  print "<td id=\"td_curator_top\" class=\"normal\" valign=\"top\">";
  print "<span id=\"span_curator_${cat}_arrow_right\" title=\"curator\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowRight.png\" onClick=\"ToggleHideColSpans(\'curator\')\" \/>";
  print "</span>";
  print "<span id=\"span_curator_${cat}_arrow_down\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'curator\')\" \/>";
  print "Curator</span></td>\n";
  print "<td id=\"td_email_top\" class=\"normal\" valign=\"top\">\n";
  print "<span id=\"span_email_${cat}_arrow_right\" title=\"email\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowRight.png\" onClick=\"ToggleHideColSpans(\'email\')\" \/>";
  print "</span>";
  print "<span id=\"span_email_${cat}_arrow_down\">";
  print "<img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'email\')\" \/>";
  print "Email</span></td>\n";
#   print "<td id=\"td_author_top\">    <img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'author\')\" \/>";
#   print "<span id=\"span_author_top_right\">Author</span></td>\n";
#   print "<td id=\"td_curator_top\">   <img src=\"http:\/\/tazendra.caltech.edu/~azurebrd/images/arrowDown.png\" onClick=\"ToggleHideColSpans(\'curator\')\" \/>";
#   print "<span id=\"span_curator_top_right\">Curator</span></td></tr>\n";
} # sub printColumnsTops



sub hashName {
  $hash{name}{spe} = 'Species';
  $hash{name}{celegans}    = '<i>C. elegans</i>.';
  $hash{exmp}{celegans}    = 'Please uncheck if you are not reporting data for <i>C. elegans</i>.';
#   $hash{mail}{celegans}    = 'azurebrd@tazendra.caltech.edu';
  $hash{name}{cnonbristol} = '<i>C. elegans</i> other than Bristol.';
#   $hash{exmp}{cnonbristol} = 'Please indicate if data for <i>C. elegans</i> isolates other than N2 (Bristol) are presented in this paper.';
  $hash{exmp}{cnonbristol} = 'Please indicate if <i>C. elegans</i> isolates other than Bristol, such as Hawaiian, CB4855, etc., are presented in this paper.';
  $hash{name}{nematode}    = 'Nematode species other than <i>C. elegans</i>.';
  $hash{exmp}{nematode}    = 'Please indicate if data is presented for any species other than <i>C. elegans</i>, e.g., <i>C. briggsae, Pristionchus pacificus, Brugia malayi,</i> etc.';
  $hash{name}{nonnematode} = 'Non-nematode species.';
  $hash{exmp}{nonnematode} = 'Please indicate if data is presented for any non-nematode species.';

  $hash{name}{gif} = 'Gene Identification and Mapping';
  $hash{name}{genestudied}  = 'Genes studied in this paper.';
  $hash{name2}{genestudied} = 'Relevant Genes.  Please list genes studied in the paper.  Exclude common markers and reporters.';
  $hash{exmp}{genestudied}  = 'Please use text box below to list any genes that were a focus of analysis in this research article.';
#   $hash{name}{genesymbol} = 'Newly cloned Novel Gene Symbol or Gene-CDS link.  E.g., xyz-1 gene was cloned and it turned out to be the same as abc-1 gene.';
  $hash{name}{genesymbol}   = 'Newly cloned gene.';
  $hash{exmp}{genesymbol}   = 'Please indicate if your paper reports a new symbol for a known locus or the name of a newly defined locus.';
  $hash{mail}{genesymbol}   = 'genenames@wormbase.org, vanauken@its.caltech.edu';
  $hash{name}{extvariation} = 'Newly created alleles.';
  $hash{exmp}{extvariation} = 'Please indicate if your paper reports the identification of any allele that doesn\'t exist in WormBase already.';
  $hash{name}{mappingdata}  = 'Genetic mapping data.';
  $hash{exmp}{mappingdata}  = 'Please indicate if your paper contains 3-factor interval mapping data, i.e., genetic data only.  Include Df or Dp data, but no SNP interval mapping.';
  $hash{mail}{mappingdata} = 'genenames@wormbase.org';

  $hash{name}{gfp} = 'Gene Function';
  $hash{name}{phenanalysis} = 'Mutant, RNAi, Overexpression, or Chemical-based Phenotypes.';
  $hash{name}{newmutant}    = 'Allele phenotype analysis.';
  $hash{exmp}{newmutant}    = 'Please indicate if your paper reports any phenotype for a mutant.';
  $hash{mail}{newmutant}    = 'garys@its.caltech.edu, kyook@its.caltech.edu';
  $hash{name}{rnai}   = 'Small-scale RNAi (less than 100 individual experiments).';
  $hash{exmp}{rnai}   = 'Please indicate if your paper reports gene knockdown phenotypes for less than 100 individual RNAi experiments.';
  $hash{mail}{rnai}   = 'garys@its.caltech.edu';
  $hash{name}{lsrnai} = 'Large-scale RNAi (greater than 100 individual experiments).';
  $hash{exmp}{lsrnai} = 'Please indicate if your paper reports gene knockdown phenotypes for more than 100 individual RNAi experiments.';
  $hash{mail}{lsrnai} = 'raymond@its.caltech.edu';
  $hash{name}{overexpr} = 'Overexpression phenotype.';
  $hash{exmp}{overexpr} = 'Please indicate if your paper reports an abnormal phenotype based on the overexpression of a gene or gene construct. E.g., \"...constitutively activated SCD-2(neu*) receptor caused 100% of animals to arrest in the first larval stage (L1)...\"';
  $hash{mail}{overexpr} = 'garys@its.caltech.edu, kyook@its.caltech.edu';
  $hash{name}{chemicals} = 'Chemicals.';
  $hash{exmp}{chemicals} = 'Please indicate if the effects of small molecules, chemicals, or drugs were studied on worms, e.g., paraquat, butanone, benzaldehyde, aldicarb, etc. Mutagens used for the generation of mutants in genetic screens do not need to be indicated.';
  $hash{name}{mosaic} = 'Mosaic analysis.';
  $hash{exmp}{mosaic} = 'Please indicate if your paper reports cell specific gene function based on mosaic analysis, e.g. extra-chromosomal transgene loss in a particular cell lineage leads to loss of mutant rescue, etc.';
  $hash{mail}{mosaic} = 'raymond@its.caltech.edu';
  $hash{name}{siteaction} = 'Tissue or cell site of action.';
  $hash{exmp}{siteaction} = 'Please indicate if your paper reports anatomy (tissue or cell)-specific expression function for a gene.';
  $hash{mail}{siteaction} = 'raymond@its.caltech.edu';
  $hash{name}{timeaction} = 'Time of action.';
  $hash{exmp}{timeaction} = 'Please indicate if your paper reports a temporal requirement for gene function, that is, if gene activity was assayed, for example, through temperature-shift experiments.';
  $hash{mail}{timeaction} = 'raymond@its.caltech.edu';
  $hash{name}{genefunc} = 'Molecular function of a gene product.';
  $hash{exmp}{genefunc} = 'Please indicate if your paper discusses a new function for a known or newly defined gene.';
  $hash{mail}{genefunc} = '';
  $hash{name}{humdis} = 'Homolog of a human disease-associated gene.';
  $hash{exmp}{humdis} = 'Please indicate if genes discussed in your paper are a homolog/ortholog of a human disease-related gene.';
  $hash{mail}{humdis} = 'ranjana@its.caltech.edu';

  $hash{name}{int} = 'Interactions';
  $hash{name}{geneint} = 'Genetic interactions.';
  $hash{exmp}{geneint} = 'Please indicate if your paper reports the analysis of more than one gene at a time, e.g., double, triple, etc. mutants, including experiments where RNAi was concurrent with other RNAi-treatments or mutations.';
  $hash{mail}{geneint} = '';
  $hash{name}{funccomp} = 'Functional complementation.';
  $hash{exmp}{funccomp} = 'Please indicate if your paper reports functional redundancy between separate genes, e.g., the rescue of <i>gen-A</i>, by overexpression of <i>gen-B</i> or any other extragenic sequence.';
  $hash{name}{geneprod} = 'Gene product interaction.';
  $hash{exmp}{geneprod} = 'Please indicate if your paper reports data on protein-protein, RNA-protein, DNA-protein, or Y2H interactions, etc.';
  $hash{mail}{geneprod} = '';

  $hash{name}{gef} = 'Regulation of Gene Expression';
  $hash{name}{otherexpr} = 'New expression pattern for a gene.';
  $hash{exmp}{otherexpr} = 'Please indicate if your paper reports new temporal or spatial (e.g. tissue, subcellular, etc.) data on the pattern of expression of any gene in a wild-type background. You can include: reporter gene analysis, antibody staining, <i>In situ</i> hybridization, RT-PCR, Western or Northern blot data.';
  $hash{mail}{otherexpr} = 'wchen@its.caltech.edu, vanauken@its.caltech.edu, draciti@caltech.edu';
  $hash{name}{microarray} = 'Microarray.';
  $hash{exmp}{microarray} = 'Please indicate if your paper reports any microarray data.';
  $hash{mail}{microarray} = 'wchen@its.caltech.edu';
  $hash{name}{genereg} = 'Alterations in gene expression by genetic or other treatment.';
  $hash{exmp}{genereg} = 'Please indicate if your paper reports changes or lack of changes in gene expression levels or patterns due to genetic background, exposure to chemicals or temperature, or any other experimental treatment.';
  $hash{mail}{genereg} = 'xdwang@its.caltech.edu';
  $hash{name}{seqfeat} = 'Regulatory sequence features.';
  $hash{exmp}{seqfeat} = 'Please indicate if your paper reports any gene expression regulatory elements, e.g., DNA/RNA elements required for gene expression, promoters, introns, UTR\'s, DNA binding sites, etc.';
  $hash{mail}{seqfeat} = 'xdwang@its.caltech.edu, worm-bug@sanger.ac.uk, stlouis@wormbase.org';
  $hash{name}{matrices} = 'Position frequency matrix (PFM) or position weight matrix (PWM).';
  $hash{exmp}{matrices} = 'Please indicate if your paper reports PFMs or PWMs, which are typically used to define regulatory sites in genomic DNA (e.g., bound by transcription factors) or mRNA (e.g., bound by translational factors or miRNA). PFMs define simple nucleotide frequencies, while PWMs are scaled logarithmically against a background frequency.';
  $hash{mail}{matrices} = 'xdwang@its.caltech.edu';

  $hash{name}{rgn} = 'Reagents.';
  $hash{name}{antibody} = '<i>C. elegans</i> antibodies.';
  $hash{exmp}{antibody} = 'Please indicate if your paper reports the use of new or known antibodies created by your lab or someone else\'s lab; do not check this box if antibodies were commercially bought.';
  $hash{mail}{antibody} = 'wchen@its.caltech.edu';
  $hash{name}{transgene} = 'Integrated transgene.';
  $hash{exmp}{transgene} = 'Please indicate if integrated transgenes were used in this paper. If the transgene does not have a canonical name, please list it in the "Add Information" text box.';
  $hash{mail}{transgene} = 'kyook@its.caltech.edu';
  $hash{name}{marker} = 'Transgenes used as tissue markers.';
  $hash{exmp}{marker} = 'Please indicate if reporters (integrated transgenes) were used to mark certain tissues, subcellular structures, or life stages, etc. as a reference point to assay gene function or location.';
  $hash{mail}{marker} = 'kyook@its.caltech.edu, vanauken@its.caltech.edu';

  $hash{name}{pfs} = 'Protein Function and Structure';
  $hash{name}{invitro} = 'Protein analysis <i>in vitro</i>.';
  $hash{exmp}{invitro} = 'Please indicate if your paper reports any <i>in vitro</i> protein analysis such as kinase assays, agonist pharmacological studies, <i>in vitro</i> reconstitution studies, etc.';
  $hash{name}{domanal} = 'Analysis of protein domains.';
  $hash{exmp}{domanal} = 'Please indicate if your paper reports on a function of a particular domain within a protein.';
  $hash{name}{covalent} = 'Covalent modification.';
  $hash{exmp}{covalent} = 'Please indicate if your paper reports on post-translational modifications as assayed by mutagenesis or in vitro analysis.';
  $hash{name}{structinfo} = 'Structural information.';
  $hash{exmp}{structinfo} = 'Please indicate if your paper reports NMR or X-ray crystallographic information.';
#   $hash{mail}{structinfo} = 'worm-bug@sanger.ac.uk, wormticket@watson.wustl.edu';	# no email  2009 05 26
  $hash{name}{massspec} = 'Mass spectrometry.';
  $hash{exmp}{massspec} = 'Please indicate if your paper reports data from any mass spec analysis e.g., LCMS, COSY, HRMS, etc.';
  $hash{mail}{massspec} = 'gw3@sanger.ac.uk, worm-bug@sanger.ac.uk';
  
  $hash{name}{seq} = 'Genome Sequence Data';
  $hash{name}{structcorr} = 'Gene structure correction.';
  $hash{exmp}{structcorr} = 'Please indicate if your paper reports a gene structure that is different from the one in WormBase, e.g., different splice-site, SL1 instead of SL2, etc.';
  $hash{mail}{structcorr} = 'wormticket@watson.wustl.edu, worm-bug@sanger.ac.uk';
  $hash{name}{seqchange} = 'Sequencing mutant alleles.';
  $hash{exmp}{seqchange} = 'Please indicate if your paper reports new sequence data for any mutation.';
  $hash{mail}{seqchange} = 'genenames@wormbase.org';
  $hash{name}{newsnp} = 'New SNPs, not already in WormBase.';
  $hash{exmp}{newsnp} = 'Please indicate if your paper reports a SNP that does not already exist in WormBase.';
  $hash{mail}{newsnp} = 'mt3@sanger.ac.uk';
  
  $hash{name}{cell} = 'Cell Data';
  $hash{name}{ablationdata} = 'Ablation data.';
  $hash{exmp}{ablationdata} = 'Please indicate if your paper reports data from an assay involving any cell or anatomical unit being ablated by laser or by other means (e.g. by expressing a cell-toxic protein).';
  $hash{mail}{ablationdata} = 'raymond@its.caltech.edu';
  $hash{name}{cellfunc} = 'Cell function.';
  $hash{exmp}{cellfunc} = 'Please indicate if your paper reports a function for any anatomical part (e.g., cell, tissue, etc.), which has not been indicated elsewhere on this form.';
  $hash{mail}{cellfunc} = 'raymond@its.caltech.edu';

  $hash{name}{sil} = 'In Silico Data';
  $hash{name}{phylogenetic} = 'Phylogenetic analysis.';
  $hash{exmp}{phylogenetic} = 'Please indicate if your paper reports any phylogenetic analysis.';
  $hash{name}{othersilico}  = 'Other bioinformatics analysis.';
  $hash{exmp}{othersilico}  = 'Please indicate if your paper reports any bioinformatic data not indicated anywhere else on this form.';

#   $hash{name}{rgn} = 'Reagents.';

  $hash{name}{oth} = 'Other';
  $hash{name}{supplemental} = 'Supplemental materials.';
  $hash{exmp}{supplemental} = 'Please indicate if your paper has supplemental material.';
  $hash{mail}{supplemental} = 'qwang@its.caltech.edu';
  $hash{name}{nocuratable}  = 'NONE of the aforementioned data types are in this research article.';
  $hash{exmp}{nocuratable}  = 'Please indicate if none of the above pertains to your paper. Feel free to list the data type most pertinent to your research paper in the "Add information" text area.';
  $hash{name}{comment} = 'Comment.';
  $hash{exmp}{comment} = 'Please feel free to give us feedback for this form or for any other topic pertinent to how we can better extract data from your paper.';
  $hash{mail}{comment} = 'kyook@its.caltech.edu, vanauken@its.caltech.edu';
} # sub hashName

sub populateCurators {
  $curators{name}{''} = '';
  $curators{name}{'101'}  = 'Wen Chen';
  $curators{name}{'2021'} = 'Jolene S. Fernandes';
  $curators{name}{'324'}  = 'Ranjana Kishore';
  $curators{name}{'363'}  = 'Raymond Lee';
  $curators{name}{'480'}  = 'Andrei Petcherski';
  $curators{name}{'557'}  = 'Gary C. Schindelman';
  $curators{name}{'567'}  = 'Erich Schwarz';
  $curators{name}{'625'}  = 'Paul Sternberg';
  $curators{name}{'1843'} = 'Kimberly Van Auken';
  $curators{name}{'1760'} = 'Xiaodong Wang';
  $curators{name}{'712'}  = 'Karen Yook';
  $curators{name}{'1823'} = 'Juancarlos Testing';
  foreach my $id (keys %{ $curators{name} }) { 
    my $joinkey = 'two' . $id;
    my $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = '$joinkey' ORDER BY two_timestamp DESC;" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    my @row = $result->fetchrow();
    if ($row[2]) { $curators{mail}{$id} = $row[2]; } }
} # sub populateCurators


__END__


# my $DB = Ace->connect(-path  =>  '/home/acedb/ts',
#                       -program => '/home/acedb/bin/tace') || die "Connection failure: ",Ace->error;


# sub messageAndrei {
#   my $body = shift;
#   my $user = 'paper_fields.cgi';
#   my $email = 'petcherski@gmail.com';
# #   my $email = 'azurebrd@tazendra.caltech.edu';
#   my $subject = 'Updated Author Flagging Form';
# #   print "$body<BR>\n";
#   &mailer($user, $email, $subject, $body);    # email CGI to user
# } # sub messageAndrei
# 
# sub gotText {
#   my ($paper, $passwd) = &checkPaperPasswd();
#   return if ($paper eq 'bad');
#   my $body = "Paper $paper Text data\n";
#   foreach my $cat (@cats, "comment") {
#     foreach my $table (@{ $hash{cat}{$cat} }) { 
#       (my $oop, my $text) = &getHtmlVar($query, "${table}_text");
#       if ($text) { 
#         &writePg($table, $paper, $text);
#         $body .= "$table :\t$text\n";
#         &textTable($table, $text); }
#     } # foreach my $table (@{ $hash{cat}{$cat} })
#   } # foreach my $cat (@cats)
#   &messageAndrei($body);
# } # sub gotText
# 
# sub gotFlagged {
#   my ($paper, $passwd) = &checkPaperPasswd();
#   return if ($paper eq 'bad');
#   &printForm();
#   print "<INPUT TYPE=HIDDEN NAME=paper VALUE=$paper>\n"; print "<INPUT TYPE=HIDDEN NAME=passwd VALUE=$passwd>\n";
#   (my $oop, my $paper) = &getHtmlVar($query, 'paper');
#   ($oop, my $passwd) = &getHtmlVar($query, 'passwd');
#   print "<INPUT TYPE=HIDDEN NAME=paper VALUE=$paper>\n";
#   print "<INPUT TYPE=HIDDEN NAME=passwd VALUE=$passwd>\n";
#   print "This page is optional. Brief notes that will help curators to locate the data you flagged on the previous page are highly appreciated (e.g.  \"Y2H fig.5\").<P><BR>\n";
# 
#   my $body = "Paper $paper flagged\n";
#   foreach my $cat (@cats, "comment") {
#     foreach my $table (@{ $hash{cat}{$cat} }) { 
#       (my $oop, my $checked) = &getHtmlVar($query, "${table}_check");
#       if ( ($checked) || ($table eq 'comment') ) { 
#         &writePg($table, $paper, 'checked');
#         $body .= "$table\tchecked\n";
#         my ($data) = &getPgData($table, $paper);
#         &checkedTable($table, $data); }
#     } # foreach my $table (@{ $hash{cat}{$cat} })
#   } # foreach my $cat (@cats)
#   print "<P><BR><INPUT TYPE=submit NAME=action VALUE=\"Submit Text\"><BR>\n";
#   print "</FORM>\n";
#   &messageAndrei($body);
# } # sub gotFlagged
# 
# sub textTable {
#   my ($table, $text) = @_;
#   print "$hash{name}{$table} : $text<P>\n"; 
# } # sub textTable
# 
# sub checkedTable {
#   my ($table, $data) = @_;
#   if ($data eq 'checked') { $data = ''; }
#   my $textarea_name = $hash{name}{$table}; if ($hash{name2}{$table}) { $textarea_name = $hash{name2}{$table}; }
#   print "$textarea_name :<BR><TEXTAREA NAME=\"${table}_text\" ROWS=4 COLS=80>$data</TEXTAREA><BR><P>\n"; 
# } # sub checkedTable
# 

