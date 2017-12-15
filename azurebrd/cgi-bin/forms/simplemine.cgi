#!/usr/bin/perl 

# Query by list of gene names on text tables.
#
# For Wen, sort of for Chris.  2015 07 30
#
# Don't need to read file to tempfile, just to variable.  2015 12 17
#
# Changed to ftp://caltech.wormbase.org/pub/wormbase/simpleMine/ instead
# of athena for Wen.  Now has dead/live gene status.  2016 05 20
#
# Changed output to be downloadable text file for Chris.  2016 05 20
#
# Change default from blank to 'N.A.' for Concise Description fields. For Wen.  2016 06 03
#
# Changed source of files from ftp to local files in wen's directory.  2016 06 09
#
# Names can map to multiple genes (e.g. A0A0M6VD87), now display all matching WBGenes.  2016 06 15
#
# Individual columns in WBGeneName.csv can have multiple comma-separated names, account for that.  2016 08 04
#
# Had an extra tab in the output, shifting things over.  Also option to download vs html.  2016 08 30
#
# Fixed some formatting with 'not found' having extra row, and entered names with multiple 
# geneIds having their geneData not cleared between geneIds.  2016 10 04
#
# Allow toggling of most columns to show or not show.  2016 04 06
#
# Was skipping first column from files because it just had the WBGene, now using it as a valid data column.  2017 06 16
#
# Wen added a new reference file, GeneReference.csv
# queryListCelegansFile to query from a list of all C elegans genes for Wen.  2017 10 09
#
# 'Set All Checkboxes' checkbox sets state of all checkboxes to match this checkbox, for Chris.
# Concise Description is now an optional set of data, for Chris.  2017 10 11

# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/simplemine.cgi



use Jex;			# untaint, getHtmlVar, cshlNew, getPgDate
use strict;
use diagnostics;
use CGI;
use LWP::UserAgent;		# for variation_nameserver file
use LWP::Simple;		# for simple gets
use DBI;
use Tie::IxHash;


my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $ua = new LWP::UserAgent;


my $query = new CGI;
my $host = $query->remote_host();		# get ip address

# my $base_url = 'http://athena.caltech.edu/fragmine/';	# replaced with ftp 2016 06 03
# my $base_url = 'ftp://caltech.wormbase.org/pub/wormbase/simpleMine/';	# replaced with local files 2016 06 09
my $files_path = '/home/acedb/wen/simplemine/sourceFileWS261/';
my @files = qw( WBGeneName.csv RNAiAllelePheno.csv GeneTissueLifeStage.csv GeneDiseaseHumanOrtholog.csv GeneReference.csv );

&process();                     # see if anything clicked

sub process {                   # see if anything clicked
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'query list') {                     &queryListTextarea(); }
    elsif ($action eq 'query uploaded file') {       &queryListUploadedFile(); }
    elsif ($action eq 'query all C elegans') {       &queryListCelegansFile(); }
    else { &frontPage(); }
}

sub queryListTextarea {
  my ($var, $geneInput)   = &getHtmlVar($query, 'geneInput');
  &queryList($geneInput);
} # sub queryListTextarea

sub queryListUploadedFile {
  my $upload_filehandle = $query->upload("geneNamesFile");
  my $geneInput = '';
  while ( <$upload_filehandle> ) { $geneInput .= $_; }	# add directly to variable, no need for temp file
#   my $date = &getSimpleSecDate() + rand();		# probabilistically unique file
#   my $tempfile = '/tmp/fraqmine_upload_' . $date;	# temporary file location
#   open ( UPLOADFILE, ">$tempfile" ) or die "Cannot create $tempfile : $!";
#   binmode UPLOADFILE;
#   while ( <$upload_filehandle> ) { print UPLOADFILE; }
#   close UPLOADFILE or die "Cannot close $tempfile : $!";
#   $/ = undef;
#   open (IN, "$tempfile") or die "Cannot open $tempfile : $!";
#   my $geneInput = <IN>;
#   close (IN) or die "Cannot close $tempfile : $!";
#   $/ = "\n";
#   if (-e $tempfile) { unlink($tempfile); }		# remove tempfile
  &queryList($geneInput);
} # sub queryListUploadedFile

sub queryListCelegansFile {				# from a flat file that Wen generates  2017 10 09
  my $infile = $files_path . 'AllCelegansGenes.txt';
  $/ = undef;
  open (IN, "$infile") or die "Cannot open $infile : $!";
  my $geneInput = <IN>;
  close (IN) or die "Cannot close $infile : $!";
  $/ = "\n";
  &queryList($geneInput);
} # sub queryListUploadedFile

sub populateConcise {
  my ($dataMapHashref)    = @_;
  my %dataMap             = %$dataMapHashref;
  my $file                = 'Concise';
  $dataMap{$file}{header} = qq(Description Type\tDescription Text);
  $dataMap{$file}{count}  = 2;
  my $result = $dbh->prepare( "SELECT con_wbgene.con_wbgene, con_desctype.con_desctype, con_desctext.con_desctext FROM con_desctext, con_desctype, con_wbgene WHERE con_wbgene.joinkey = con_desctype.joinkey AND con_wbgene.joinkey = con_desctext.joinkey AND con_wbgene.joinkey NOT IN (SELECT joinkey FROM con_nodump WHERE con_nodump = 'NO DUMP');" );
  $result->execute();
  my %concise;
  while (my @row = $result->fetchrow()) {
    my $wbgene   = $row[0];
    my $desctype = $row[1];
    my $desctext = $row[2];
    if ($desctext =~ m/\n/) { $desctext =~ s/\n/ /g; }
    $concise{$wbgene}{$desctype} = $desctext;	# only look at concise or automated, only display one, prioritizing concise
  }
  foreach my $wbgene (sort keys %concise) {
    if ($concise{$wbgene}{Concise_description}) {
#         push @{ $dataMap{$wbgene} }, qq($wbgene\tConcise_description\t$concise{$wbgene}{Concise_description});
        $dataMap{$file}{$wbgene} = qq(Concise_description\t$concise{$wbgene}{Concise_description}); }
      elsif ($concise{$wbgene}{Automated_description}) {
#         push @{ $dataMap{$wbgene} }, qq($wbgene\tAutomated_description\t$concise{$wbgene}{Automated_description});
        $dataMap{$file}{$wbgene} = qq(Automated_description\t$concise{$wbgene}{Automated_description}); } }
  return \%dataMap;
} # sub populateConcise


sub populateFromAthena {
  my ($filesHref) = @_;
  my (@files) = @$filesHref;
  my $errMessage;
#   my $fullHeader = '';
  my %dataMap;
  my %geneNameToId;
  foreach my $file (@files) {
#     my $dataUrl = $base_url . $file;			# to get from Athena or ftp
#     my $data    = get $dataUrl;			# to get from Athena or ftp
    my $filepath = $files_path . $file;			# to get from local files
    $/ = undef;
    open (IN, "<$filepath") or die "Cannot open $filepath : $!";
    my $data = <IN>;
    close (IN) or die "Cannot close $filepath : $!";
    $/ = "\n";
    my (@lines) = split/\n/, $data;
    my @columns = ();
    foreach my $i (0 .. $#lines) {
      my $line = $lines[$i];
      chomp $line;
      my ($wbgene, @rest) = split/\t/, $line;
#       my $data = join"\t", @rest;
      if ($i == 0) {
#           $fullHeader .= $data; 
          my $count = scalar(@rest);
#           (@columns) = @rest;
# to keep first column as data from files
          (@columns) = split/\t/, $line;
          $dataMap{$file}{header} = $data;
          $dataMap{$file}{count}  = $count;
        }
        else {
          if ($file eq 'WBGeneName.csv') {
            my $lcwbgene = lc($wbgene);
#             $geneNameToId{$lcwbgene} = $wbgene;
            $geneNameToId{$lcwbgene}{$wbgene}++;
            foreach my $category (@rest) {
              my (@indNames) = split/,/, $category;
              foreach my $name (@indNames) {
                unless ($name eq 'N.A.') { 
                  my $lcname = lc($name);
#                   $geneNameToId{$lcname} = $wbgene;
                  $geneNameToId{$lcname}{$wbgene}++; } } } }
#           $dataMap{$file}{$wbgene} = $data; 

#           my (@data) = split/\t/, $data;
#           for my $i (0 .. $#data) {
#             $dataMap{$columns[$i]}{$wbgene} = $data[$i]; }
# to keep first column as data from files
          my (@data) = split/\t/, $line;
          for my $i (0 .. $#data) {
            $dataMap{$columns[$i]}{$wbgene} = $data[$i]; }

    } }
  } # foreach my $file (@files)
  return ($errMessage, \%dataMap, \%geneNameToId);
} # sub populateFromAthena

sub queryList {
  my ($geneInput) = @_;					# gene list from form textarea or uploaded file
#   print "Content-type: text/html\n\n";
  my ($var, $outputFormat)   = &getHtmlVar($query, 'outputFormat');
  ($var, my $possibleheaders)        = &getHtmlVar($query, 'headers');
  my @possibleheaders = split/\t/, $possibleheaders;
  my @headers;
  foreach my $header (@possibleheaders) {
    ($var, my $headervalue)        = &getHtmlVar($query, $header);
    if ($headervalue) { push @headers, $header; } }
  unless ($outputFormat) { $outputFormat = 'download'; }
  if ($outputFormat eq 'download') {
      print qq(Content-type: application/x-download\n);
      print qq(Content-Disposition: attachment; filename="simplemine_results.txt"\n\n); }
    elsif ($outputFormat eq 'plain') {
      print "Content-type: text/plain\n\n"; }
    elsif ($outputFormat eq 'html') {
      print "Content-type: text/html\n\n"; }
    else {
      print qq(Content-type: application/x-download\n);
      print qq(Content-Disposition: attachment; filename="simplemine_results.txt"\n\n); }
  my $output = '';
#   my $geneNameToIdHashref = &populateGeneMap();
#   my %geneNameToId        = %$geneNameToIdHashref;
  my ($errMessage, $dataMapHashref, $geneNameToIdHashref) = &populateFromAthena(\@files);
  my %dataMap          = %$dataMapHashref;
  my %geneNameToId     = %$geneNameToIdHashref;
  ($var, my $concisedescriptionFlag)        = &getHtmlVar($query, "Concise Description");
  if ($concisedescriptionFlag) {
    ($dataMapHashref)    = &populateConcise(\%dataMap);
    %dataMap             = %$dataMapHashref; }
#   my $dataHeader = qq(Your Input\tGene);
  my $dataHeader = qq(Your Input);
#   foreach my $file (@files, "Concise") { $dataHeader .= "\t$dataMap{$file}{header}"; }
  foreach my $header (@headers) { $dataHeader .= "\t$header"; }
#   foreach my $file ("Concise") {  $dataHeader .= "\t$dataMap{$file}{header}"; }
  if ($concisedescriptionFlag) {
    push @headers, "Concise";
    $dataHeader .= "\t$dataMap{Concise}{header}"; }
  $output .= qq($dataHeader\n);
  if ($geneInput =~ m/[^\w\d\.\-\(\)\/]/) { $geneInput =~ s/[^\w\d\.\-\(\)\/]+/ /g; }
  my (@genes) = split/\s+/, $geneInput;
  my %alreadyEntered;
  foreach my $geneEntered (@genes) {
    my ($gene) = lc($geneEntered);
    next if ($alreadyEntered{$gene});
    $alreadyEntered{$gene}++;
    my $geneId = 'not found';
    my $geneData;
    if ($geneNameToId{$gene}) {
#         $geneId = $geneNameToId{$gene};
        foreach my $geneId (sort keys %{ $geneNameToId{$gene} }) {
          $geneData = '';
          foreach my $header (@headers) {
            if ($dataMap{$header}{$geneId}) {
#                 $geneData .= "\t$header -- $dataMap{$header}{$geneId}";
                $geneData .= "\t$dataMap{$header}{$geneId}"; }
              else {
#                 $geneData .= "\t$header -- N.A.";
                $geneData .= "\tN.A."; }
          } # foreach my $header (@files, "Concise")
#           foreach my $file (@files, "Concise") {
#             if ($dataMap{$file}{$geneId}) {
# # if ($geneId eq 'WBGene00002335') { $output .= qq(LATER $geneId FILE $file REST $dataMap{$file}{$geneId}\n); }
# #               $output .= "$geneEntered\t$geneId\t$dataMap{$geneId}\n";
#                 $geneData .= "\t$dataMap{$file}{$geneId}"; }
#               else {
#                 for (1 .. $dataMap{$file}{count}) { $geneData .= "\tN.A."; } }
#           } # foreach my $file (@files, "Concise")
          $output .= qq(${geneEntered}$geneData\n);
#           $output .= qq($geneEntered\t${geneId}$geneData\n);
        } # foreach my $geneId (sort keys %{ $geneNameToId{$gene} })
      }
      else {
        $geneData = "not found";
        $output .= qq($geneEntered\t$geneId\t$geneData\n); }
#     $output .= qq($geneEntered\t$geneData\n);
  } # foreach my $gene (@genes)
  if ($outputFormat eq 'html') {
    $output =~ s|\t|</td><td>|g;
    $output =~ s|\n|</td></tr>\n<tr><td>|g;
    $output = qq(<table border="1"><tr><td>$output</td></tr></table>); }
  print qq($output);
} # sub queryList

sub frontPage {
  print "Content-type: text/html\n\n";
  my $title = 'Simple Mine';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }
  &showFraqForm();
  print "$footer"; 		# make end of HTML page
} # sub frontPage

# sub populateGeneMap {
#   my %geneNameToId;
#   my @tables = qw( gin_wbgene gin_seqname gin_synonyms gin_locus );
# #   my @tables = qw( gin_seqname gin_synonyms gin_locus );
#   foreach my $table (@tables) {
#     my $result = $dbh->prepare( "SELECT * FROM $table;" );
#     $result->execute();
#     while (my @row = $result->fetchrow()) {
#       my $id                 = "WBGene" . $row[0];
#       my $name               = $row[1];
#       my ($lcname)           = lc($name);
#       $geneNameToId{$lcname} = $id; } }
#   return \%geneNameToId;
# } # sub populateGeneMap
 

sub showFraqForm {
  print qq(<h3>Simple Gene Queries</h3><br/>\n);
  print qq(Gene mappings to gene identifiers, Tissue-LifeStage, RNAi-Phenotype, Allele-Phenotype, ConciseDescription.<br/><br/>);
  print qq(<form method="post" action="simplemine.cgi" enctype="multipart/form-data">\n);
#   my $select_size = scalar @files;
#   print qq(Select your datatype :<br>\n);
#   print qq(<select name="sourceFile" size="$select_size">);
#   foreach my $file (@files) {
#     print qq(<option>$file</option>);
#   } # foreach my $file (@files)
#   print qq(</select>\n);
#   print qq(<br/><br/>\n);
#   print qq(Enter list of gene names here (one gene per line, or separate with spaces, not punctuation) :<br/>);
  print qq(Enter list of gene names here :<br/>);
  print qq(<textarea id="geneInput" name="geneInput" rows="20" cols="80"></textarea><br/>\n);
  print qq(<br/><input type="submit" name="action" value="query list"><br/>\n);
  print qq(<br/><br/>\n);
  print qq(Upload a file with gene names :<br/>);
  print qq(<input type="file" name="geneNamesFile" /><br/>);
  print qq(<br/><input type="submit" name="action" value="query uploaded file"><br/>\n);
  print qq(<br/><input type="submit" name="action" value="query all C elegans"><br/>\n);
  print qq(<br/><br/>);
  print qq(<input type="radio" name="outputFormat" value="download" checked="checked"> download<br/>);
  print qq(<input type="radio" name="outputFormat" value="html"> html<br/>);

  print qq(<br/>);
  my %columns;
  tie %columns, "Tie::IxHash";
  foreach my $file (@files) {
    my $filepath = $files_path . $file;			# to get from local files
    open (IN, "<$filepath") or die "Cannot open $filepath : $!";
    my $header = <IN>;
    chomp $header;
    close (IN) or die "Cannot close $filepath : $!";
    my (@columns) = split/\t/, $header;
    foreach (@columns) { $columns{$_}++; } }
  delete $columns{'Gene'};				# not sure why need to delete this
#   $columns{"Concise Description"}++;			# coming from postgres
  my $headers = join"\t", keys %columns;
  print qq(<input type="hidden" name="headers" value="$headers"/>);
  print qq(<input type="checkbox" id="select all" name="select all" value="select all" checked="checked" onclick="var inputs = document.getElementsByTagName('input'); for(var i = 0; i < inputs.length; i++) { if(inputs[i].type == 'checkbox') { inputs[i].checked = document.getElementById('select all').checked; } }"> Set All Checkboxes<br/><br/>);	# set state of all checkboxes to this state
  foreach my $column (keys %columns) {
    print qq(<input type="checkbox" name="$column" value="$column" checked="checked"> $column<br/>); }
  print qq(<input type="checkbox" name="Concise Description" value="Concise Description" checked="checked"> Concise Description<br/>);				# not part of general headers, comes from postgres

  print qq(</form>\n);
} # sub showFraqForm


sub showIp {
  print "Content-type: text/html\n\n";
  my $title = 'Your IP';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }
  print "Your IP is : $host<BR>\n";
  print "$footer"; 		# make end of HTML page
} # sub showIp

__END__

#   my ($var, $sourceFile)  = &getHtmlVar($query, 'sourceFile');
#   my %dataMap;
#   my $dataHeader;
#   if ($sourceFile eq 'GeneTissueLifeStage') {
#       my $dataUrl = 'http://athena.caltech.edu/GeneTissueLifeStage/GeneTissueLifeStage.csv';
#       my $data    = get $dataUrl;
#       my (@lines) = split/\n/, $data;
#       $dataHeader = shift @lines;
#       foreach my $line (@lines) {
#         chomp $line;
#         my ($wbgene, @rest) = split/\t/, $line;
#         push @{ $dataMap{$wbgene} }, $line; } }
#     elsif ($sourceFile eq 'ConciseDescription') {
#       $dataHeader = qq(Gene ID\tDescription Type\tDescription Text);
#       my $result = $dbh->prepare( "SELECT con_wbgene.con_wbgene, con_desctype.con_desctype, con_desctext.con_desctext FROM con_desctext, con_desctype, con_wbgene WHERE con_wbgene.joinkey = con_desctype.joinkey AND con_wbgene.joinkey = con_desctext.joinkey AND con_wbgene.joinkey NOT IN (SELECT joinkey FROM con_nodump WHERE con_nodump = 'NO DUMP');" );
#       $result->execute();
#       my %concise;
#       while (my @row = $result->fetchrow()) {
#         my $wbgene   = $row[0];
#         my $desctype = $row[1];
#         my $desctext = $row[2];
#         $concise{$wbgene}{$desctype} = $desctext;	# only look at concise or automated, only display one, prioritizing concise
#       }
#       foreach my $wbgene (sort keys %concise) {
#         if ($concise{$wbgene}{Concise_description}) {
#             push @{ $dataMap{$wbgene} }, qq($wbgene\tConcise_description\t$concise{$wbgene}{Concise_description}); }
#           elsif ($concise{$wbgene}{Automated_description}) {
#           push @{ $dataMap{$wbgene} }, qq($wbgene\tAutomated_description\t$concise{$wbgene}{Automated_description}); } } }
#     elsif ($sourceFile eq 'RNAiPhenotype') {
#       my $dirListUrl = 'ftp://ftp.wormbase.org/pub/wormbase/releases/current-development-release/ONTOLOGY/';
#       my $dirList    = get $dirListUrl;
#       my ($filename) = $dirList =~ m/(rnai_phenotypes.WS\d+.wb)/;
#       my $fileUrl    = $dirListUrl . $filename;
#       my $data       = get $fileUrl;
#       my (@lines)    = split/\n/, $data;
#       $dataHeader    = '';	# no header in this file
#       foreach my $line (@lines) {
#         chomp $line;
#         my ($wbgene, @rest) = split/\t/, $line;
#         push @{ $dataMap{$wbgene} }, $line; } }
#     else { print qq(You must select a valid datatype\n\n); }
