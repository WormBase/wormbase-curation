#!/usr/bin/perl 

# Query by list of gene names on text tables.
#
# For Wen, sort of for Chris.  2015 07 30
#
# Don't need to read file to tempfile, just to variable.  2015 12 17

# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/fraqmine.cgi



use Jex;			# untaint, getHtmlVar, cshlNew, getPgDate
use strict;
use diagnostics;
use CGI;
use LWP::UserAgent;		# for variation_nameserver file
use LWP::Simple;		# for simple gets
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $ua = new LWP::UserAgent;


my $query = new CGI;
my $host = $query->remote_host();		# get ip address

&process();                     # see if anything clicked

sub process {                   # see if anything clicked
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'query list') {                     &queryListTextarea(); }
    elsif ($action eq 'query uploaded file') {       &queryListUploadedFile(); }
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
  my $base_url = 'http://athena.caltech.edu/fragmine/';
#   my $fullHeader = '';
  my %dataMap;
  my %geneNameToId;
  foreach my $file (@files) {
    my $dataUrl = $base_url . $file;
    my $data    = get $dataUrl;
    my (@lines) = split/\n/, $data;
    foreach my $i (0 .. $#lines) {
      my $line = $lines[$i];
      chomp $line;
      my ($wbgene, @rest) = split/\t/, $line;
      my $data = join"\t", @rest;
      if ($i == 0) { 
#           $fullHeader .= $data; 
          my $count = scalar(@rest);
          $dataMap{$file}{header} = $data;
          $dataMap{$file}{count}  = $count;
        }
        else { 
          if ($file eq 'WBGeneName.csv') { 
            my $lcwbgene = lc($wbgene);
            $geneNameToId{$lcwbgene} = $wbgene;
            foreach my $name (@rest) {
              unless ($name eq 'N.A.') { 
                my $lcname = lc($name);
                $geneNameToId{$lcname} = $wbgene; } } }
#           push @{ $dataMap{$wbgene} }, $data;
#           $dataMap{$wbgene} .= qq(\t$data); 
# if ($wbgene eq 'WBGene00002335') { $errMessage .= qq($wbgene FILE $file REST $data\n); }
          $dataMap{$file}{$wbgene} = $data; } }
  } # foreach my $file (@files)
  return ($errMessage, \%dataMap, \%geneNameToId);
} # sub populateFromAthena

sub queryList {
  my ($geneInput) = @_;					# gene list from form textarea or uploaded file
#   print "Content-type: text/html\n\n";
  print "Content-type: text/plain\n\n";
  my @files = qw( WBGeneName.csv RNAiAllelePheno.csv GeneTissueLifeStage.csv );
#   my $geneNameToIdHashref = &populateGeneMap();
#   my %geneNameToId        = %$geneNameToIdHashref;
  my ($errMessage, $dataMapHashref, $geneNameToIdHashref) = &populateFromAthena(\@files);
  my %dataMap          = %$dataMapHashref;
  my %geneNameToId     = %$geneNameToIdHashref;
  my ($dataMapHashref) = &populateConcise(\%dataMap);
  %dataMap             = %$dataMapHashref;
  my $dataHeader = qq(Your Input\tGene);
  foreach my $file (@files, "Concise") { $dataHeader .= "\t$dataMap{$file}{header}"; }
  print qq($dataHeader\n);
  if ($geneInput =~ m/[^\w\d\.\-\(\)\/]/) { $geneInput =~ s/[^\w\d\.\-\(\)\/]+/ /g; }
  my (@genes) = split/\s+/, $geneInput;
  foreach my $geneEntered (@genes) {
    my ($gene) = lc($geneEntered);
    my $geneId = 'not found';
    my $geneData;
    if ($geneNameToId{$gene}) { 
        $geneId = $geneNameToId{$gene};
        foreach my $file (@files, "Concise") {
          if ($dataMap{$file}{$geneId}) {
# if ($geneId eq 'WBGene00002335') { print qq(LATER $geneId FILE $file REST $dataMap{$file}{$geneId}\n); }
#               print "$geneEntered\t$geneId\t$dataMap{$geneId}\n";
              $geneData .= "\t$dataMap{$file}{$geneId}"; }
            else {
              for (1 .. $dataMap{$file}{count}) { $geneData .= "\t"; } }
        } # foreach my $file (@files, "Concise")
        $geneData = qq(${geneId}$geneData);
      }
      else {
        $geneData = "not found\n"; } 
    print qq($geneEntered\t$geneData\n);
  } # foreach my $gene (@genes)
} # sub queryList

sub frontPage {
  print "Content-type: text/html\n\n";
  my $title = 'Fraq Mine';
  my ($header, $footer) = &cshlNew($title);
  print "$header\n";		# make beginning of HTML page
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }
  &showFraqForm();
  print "$footer"; 		# make end of HTML page
} # sub frontPage

sub populateGeneMap {
  my %geneNameToId;
  my @tables = qw( gin_wbgene gin_seqname gin_synonyms gin_locus );
#   my @tables = qw( gin_seqname gin_synonyms gin_locus );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table;" );
    $result->execute();
    while (my @row = $result->fetchrow()) {
      my $id                 = "WBGene" . $row[0];
      my $name               = $row[1];
      my ($lcname)           = lc($name);
      $geneNameToId{$lcname} = $id; } }
  return \%geneNameToId;
} # sub populateGeneMap
 

sub showFraqForm {
  print qq(<h3>FRequently Asked Queries</h3><br/>\n);
  print qq(Gene mappings to gene identifiers, Tissue-LifeStage, RNAi-Phenotype, Allele-Phenotype, ConciseDescription.<br/><br/>);
  print qq(<form method="post" action="fraqmine.cgi" enctype="multipart/form-data">\n);
  my @files = qw( GeneTissueLifeStage ConciseDescription RNAiPhenotype );
  my $select_size = scalar @files;
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
