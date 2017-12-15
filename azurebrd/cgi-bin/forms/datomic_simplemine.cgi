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
#
# Rewrote queries to work off of datomic rest query from Adam's machine.  2016 07 30
#
# Any user entries that are not WBGenes get converted to WBGenes, but it's very very slow.  2016 07 31
#
# Added WormPep from molecularname starting with WP:  2016 08 01


# http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/datomic_simplemine.cgi



use Jex;			# untaint, getHtmlVar, cshlNew, getPgDate
use strict;
use diagnostics;
use CGI;
use LWP::UserAgent;		# for variation_nameserver file
use LWP::Simple;		# for simple gets
use DBI;
use Time::HiRes qw ( time );                    # replace time with High Resolution version



my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

my $ua = new LWP::UserAgent;

my (%DecodeMap, %EncodeMap);
&initEncodeMap();


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
#   my $base_url = 'http://athena.caltech.edu/fragmine/';	# replaced with ftp 2016 06 03
#   my $base_url = 'ftp://caltech.wormbase.org/pub/wormbase/simpleMine/';	# replaced with local files 2016 06 09
  my $files_path = '/home/acedb/wen/simplemine/sourceFile/';
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
#             $geneNameToId{$lcwbgene} = $wbgene;
            $geneNameToId{$lcwbgene}{$wbgene}++;
            foreach my $name (@rest) {
              unless ($name eq 'N.A.') { 
                my $lcname = lc($name);
#                 $geneNameToId{$lcname} = $wbgene;
                $geneNameToId{$lcname}{$wbgene}++; } } }
#           push @{ $dataMap{$wbgene} }, $data;
#           $dataMap{$wbgene} .= qq(\t$data); 
# if ($wbgene eq 'WBGene00002335') { $errMessage .= qq($wbgene FILE $file REST $data\n); }
          $dataMap{$file}{$wbgene} = $data; } }
  } # foreach my $file (@files)
  return ($errMessage, \%dataMap, \%geneNameToId);
} # sub populateFromAthena

# sub queryList {
#   my ($geneInput) = @_;					# gene list from form textarea or uploaded file
# #   print "Content-type: text/html\n\n";
# #   print "Content-type: text/plain\n\n";
#   print qq(Content-type: application/x-download\n);
#   print qq(Content-Disposition: attachment; filename="simplemine_results.txt"\n);
#   print qq(\n);
#   my @files = qw( WBGeneName.csv RNAiAllelePheno.csv GeneTissueLifeStage.csv );
# #   my $geneNameToIdHashref = &populateGeneMap();
# #   my %geneNameToId        = %$geneNameToIdHashref;
#   my ($errMessage, $dataMapHashref, $geneNameToIdHashref) = &populateFromAthena(\@files);
#   my %dataMap          = %$dataMapHashref;
#   my %geneNameToId     = %$geneNameToIdHashref;
#   my ($dataMapHashref) = &populateConcise(\%dataMap);
#   %dataMap             = %$dataMapHashref;
#   my $dataHeader = qq(Your Input\tGene);
#   foreach my $file (@files, "Concise") { $dataHeader .= "\t$dataMap{$file}{header}"; }
#   print qq($dataHeader\n);
#   if ($geneInput =~ m/[^\w\d\.\-\(\)\/]/) { $geneInput =~ s/[^\w\d\.\-\(\)\/]+/ /g; }
#   my (@genes) = split/\s+/, $geneInput;
#   foreach my $geneEntered (@genes) {
#     my ($gene) = lc($geneEntered);
#     my $geneId = 'not found';
#     my $geneData;
#     if ($geneNameToId{$gene}) { 
# #         $geneId = $geneNameToId{$gene};
#         foreach my $geneId (sort keys %{ $geneNameToId{$gene} }) {
#           foreach my $file (@files, "Concise") {
#             if ($dataMap{$file}{$geneId}) {
# # if ($geneId eq 'WBGene00002335') { print qq(LATER $geneId FILE $file REST $dataMap{$file}{$geneId}\n); }
# #               print "$geneEntered\t$geneId\t$dataMap{$geneId}\n";
#                 $geneData .= "\t$dataMap{$file}{$geneId}"; }
#               else {
#                 for (1 .. $dataMap{$file}{count}) { $geneData .= "\tN.A."; } }
#           } # foreach my $file (@files, "Concise")
#           print qq($geneEntered\t$geneId\t$geneData\n);
#         } # foreach my $geneId (sort keys %{ $geneNameToId{$gene} })
#       }
#       else {
#         $geneData = "not found\n";
#         print qq($geneEntered\t$geneId\t$geneData\n); }
# #     print qq($geneEntered\t$geneData\n);
#   } # foreach my $gene (@genes)
# } # sub queryList

sub queryList {
  my ($var, $output_format) = &getHtmlVar($query, 'output_format');
  ($var, my $show_queries)  = &getHtmlVar($query, 'show_queries');
  unless ($output_format) { $output_format = 'html'; }

  my ($geneInput) = @_;					# gene list from form textarea or uploaded file
  my $restQuery; my $arrayRef;
  if ($output_format eq 'text_download') {
      print qq(Content-type: application/x-download\n);
      print qq(Content-Disposition: attachment; filename="simplemine_results.txt"\n); }
    elsif ($output_format eq 'html') {
      print "Content-type: text/html\n\n"; }
    elsif ($output_format eq 'text') {
      print "Content-type: text/plain\n\n"; }
#   print "Content-type: text/plain\n\n";
  print qq(\n);
  if ($geneInput =~ m/[^\w\d\.\-\(\)\/]/) { $geneInput =~ s/[^\w\d\.\-\(\)\/]+/ /g; }
  my (@genes) = split/\s+/, $geneInput;
  my %wbgenes;
  my %sourceGenes;
  my $needsMapping = '';
  foreach my $sourceGene (@genes) {
    if ($sourceGene =~ m/WBGene\d+/) { $sourceGenes{$sourceGene} = $sourceGene; $wbgenes{$sourceGene}++; }
      else {
        $needsMapping .= <<"EndOfText";
                        [?e :gene/public-name "$sourceGene"]
                        (and [?e :gene/other-name ?o]
                             [?o :gene.other-name/text "$sourceGene"])
                        [?e :gene/molecular-name "$sourceGene"]
EndOfText
        $sourceGenes{$sourceGene} = 'needsValue'; }
  }
  if ($needsMapping) {
    $restQuery = <<"EndOfText";
[:find [?g ...] :in \$ :where
                      (or-join [?e]
$needsMapping
                      )
                      [?e :gene/id ?g]
]
EndOfText
    ($arrayRef) = queryRest($restQuery, $show_queries);
    foreach my $entry (@$arrayRef) {
      my ($wbgene) = $entry =~ m/(WBGene\d+)/;
      $wbgenes{$wbgene}++;
    } # foreach my $entry (@$arrayRef)
  } # if ($needsMapping)


  my $geneOrClause = join('"][?wbggid :gene/id "', sort keys %wbgenes);

  my %data;

# does not work, because if any value doesn't exist, the whole query fails, must separate into each section
#   $restQuery = <<"EndOfText";
# [:find ?genename ?status ?pname ?sname ?mname ?oname :in \$ :where
#                       (or-join [?wbggid]
#                              [?wbggid :gene/id "$geneOrClause"]
#                       )
#                              [?wbggid :gene/id ?genename]
#                              [?wbggid :gene/status ?gsid]
#                              [?gsid :gene.status/status ?statusid]
#                              [?statusid :db/ident ?status]
#                              [?wbggid :gene/sequence-name ?sname]
#                              [?wbggid :gene/public-name ?pname]
#                              [?wbggid :gene/molecular-name ?mname]
#                              [?wbggid :gene/other-name ?onameid]
#                              [?onameid :gene.other-name/text ?oname]
# ]
# EndOfText
# # ["WBGene00003883" :gene.status.status/live "osm-1" "T27B1.1" "CE41845" "CELE_T27B1.1"]
#   ($arrayRef) = queryRest($restQuery);
#   foreach my $entry (@$arrayRef) {
# #     $entry =~ s/^"//; $entry =~ s/"$//;
#     $entry =~ s/"//g;
#     my ($gene, $status, $pubname, $seqname, $molname, $othname) = split/\s+/, $entry;
#     $status =~ s/:gene.status.status\///;
#     $data{$gene}{status}{$status}++;
#     $data{$gene}{pubname}{$pubname}++;
#     $data{$gene}{seqname}{$seqname}++;
#     $data{$gene}{molname}{$molname}++;
#     $data{$gene}{othname}{$othname}++;
#     if      ($sourceGenes{$pubname} eq 'needsValue') { $sourceGenes{$pubname} = $gene; }
#       elsif ($sourceGenes{$seqname} eq 'needsValue') { $sourceGenes{$seqname} = $gene; }
#       elsif ($sourceGenes{$molname} eq 'needsValue') { $sourceGenes{$molname} = $gene; }
#       elsif ($sourceGenes{$othname} eq 'needsValue') { $sourceGenes{$othname} = $gene; }
#   } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?status :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?wbggid :gene/status ?gsid]
                             [?gsid :gene.status/status ?statusid]
                             [?statusid :db/ident ?status]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/"//g;
    my ($gene, $status) = split/\s+/, $entry;
    $status =~ s/:gene.status.status\///;
    $data{$gene}{status}{$status}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?pname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?wbggid :gene/public-name ?pname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $pubname) = split/" "/, $entry;
    $data{$gene}{pubname}{$pubname}++;
    if      ($sourceGenes{$pubname} eq 'needsValue') { $sourceGenes{$pubname} = $gene; }
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?sname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?wbggid :gene/sequence-name ?sname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $seqname) = split/" "/, $entry;
    $data{$gene}{seqname}{$seqname}++;
    if ($sourceGenes{$seqname} eq 'needsValue') { $sourceGenes{$seqname} = $gene; }
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?mname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?wbggid :gene/molecular-name ?mname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $molname) = split/" "/, $entry;
    $data{$gene}{molname}{$molname}++;
    if ($molname =~ m/WP:(.*)/) { $data{$gene}{wormpep}{$1}++; }
    if ($sourceGenes{$molname} eq 'needsValue') { $sourceGenes{$molname} = $gene; }
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?oname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?wbggid :gene/other-name ?onameid]
                             [?onameid :gene.other-name/text ?oname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $othname) = split/" "/, $entry;
    $data{$gene}{othname}{$othname}++;
    if ($sourceGenes{$othname} eq 'needsValue') { $sourceGenes{$othname} = $gene; }
  } # foreach my $entry (@$arrayRef)


  $restQuery = <<"EndOfText";
[:find ?genename ?field ?accession :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?wbggid :gene/database ?dbid]
                             [?dbid :gene.database/accession ?accession]
                             [?dbid :gene.database/field ?fieldid]
                             [?fieldid :database-field/id ?field]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
#     $entry =~ s/^"//; $entry =~ s/"$//;
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $field, $accession) = split/" "/, $entry;
    if ($field eq 'UniProtAcc') { $data{$gene}{uniprot}{$accession}++;              }
      elsif ($field eq 'TREEFAM_ID') { $data{$gene}{treefam}{$accession}++;         }
      elsif ($field eq 'mRNA') {       $data{$gene}{refseqmrna}{$accession}++;      }
      elsif ($field eq 'protein') {    $data{$gene}{refseqmprotein}{$accession}++;  }
  } # foreach my $entry (@$arrayRef)


  $restQuery = <<"EndOfText";
[:find ?genename ?pname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?xref :rnai.gene/gene ?wbggid]
                             [?rid :rnai/gene ?xref]
                             [?rid :rnai/id ?rnai]
                             [?rid :rnai/phenotype-not-observed ?pid]
                             [?pid :rnai.phenotype-not-observed/phenotype ?pobj]
                             [?pobj :phenotype/id ?phen]
                             [?pobj :phenotype/primary-name ?ppnid]
                             [?ppnid :phenotype.primary-name/text ?pname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $rphenyes) = split/" "/, $entry;
    $data{$gene}{rphenyes}{$rphenyes}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?pname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?xref :rnai.gene/gene ?wbggid]
                             [?rid :rnai/gene ?xref]
                             [?rid :rnai/id ?rnai]
                             [?rid :rnai/phenotype ?pid]
                             [?pid :rnai.phenotype/phenotype ?pobj]
                             [?pobj :phenotype/id ?phen]
                             [?pobj :phenotype/primary-name ?ppnid]
                             [?ppnid :phenotype.primary-name/text ?pname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $rphennot) = split/" "/, $entry;
    $data{$gene}{rphennot}{$rphennot}++;
  } # foreach my $entry (@$arrayRef)


  $restQuery = <<"EndOfText";
[:find ?genename ?pname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?xref :variation.gene/gene ?wbggid]
                             [?vid :variation/gene ?xref]
                             [?vid :variation/id ?variation]
                             [?vid :variation/phenotype ?pid]
                             [?pid :variation.phenotype/phenotype ?pobj]
                             [?pobj :phenotype/id ?phen]
                             [?pobj :phenotype/primary-name ?ppnid]
                             [?ppnid :phenotype.primary-name/text ?pname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $vphenyes) = split/" "/, $entry;
    $data{$gene}{vphenyes}{$vphenyes}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?pname :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?xref :variation.gene/gene ?wbggid]
                             [?vid :variation/gene ?xref]
                             [?vid :variation/id ?variation]
                             [?vid :variation/phenotype-not-observed ?pid]
                             [?pid :variation.phenotype-not-observed/phenotype ?pobj]
                             [?pobj :phenotype/id ?phen]
                             [?pobj :phenotype/primary-name ?ppnid]
                             [?ppnid :phenotype.primary-name/text ?pname]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $vphennot) = split/" "/, $entry;
    $data{$gene}{vphennot}{$vphennot}++;
  } # foreach my $entry (@$arrayRef)


  $restQuery = <<"EndOfText";
[:find ?genename ?name :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?gid :expr-pattern.gene/gene ?wbggid]
                             [?exprid :expr-pattern/gene ?gid]
                             (not [?exprid :expr-pattern/epic ])
                             (not [?exprid :expr-pattern/microarray ])
                             [?exprid :expr-pattern/life-stage ?lsref]
                             [?lsref :expr-pattern.life-stage/life-stage ?lsid]
                             [?lsid :life-stage/public-name ?name]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $epls) = split/" "/, $entry;
    $data{$gene}{epls}{$epls}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?name :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?gid :expression-cluster.gene/gene ?wbggid]
                             [?exprid :expression-cluster/gene ?gid]
                             [?exprid :expression-cluster/life-stage ?lsid]
                             [?lsid   :life-stage/public-name ?name]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $gsls) = split/" "/, $entry;
    $data{$gene}{gsls}{$gsls}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?term :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?gid :expr-pattern.gene/gene ?wbggid]
                             [?exprid :expr-pattern/gene ?gid]
                             (not [?exprid :expr-pattern/epic ])
                             (not [?exprid :expr-pattern/microarray ])
                             [?exprid :expr-pattern/anatomy-term ?anatref]
                             [?anatref :expr-pattern.anatomy-term/anatomy-term ?anatid]
                             [?anatid :anatomy-term/term ?termref]
                             [?termref :anatomy-term.term/text ?term]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $epts) = split/" "/, $entry;
    $data{$gene}{epts}{$epts}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?term :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                             [?gid :expression-cluster.gene/gene ?wbggid]
                             [?exprid :expression-cluster/gene ?gid]
                             [?exprid :expression-cluster/anatomy-term ?anatref]
                             [?anatref :expression-cluster.anatomy-term/anatomy-term ?anatid]
                             [?anatid :anatomy-term/term ?termref]
                             [?termref :anatomy-term.term/text ?term]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $gsts) = split/" "/, $entry;
    $data{$gene}{gsts}{$gsts}++;
  } # foreach my $entry (@$arrayRef)

  $restQuery = <<"EndOfText";
[:find ?genename ?c ?p :in \$ :where
                      (or-join [?wbggid]
                             [?wbggid :gene/id "$geneOrClause"]
                      )
                             [?wbggid :gene/id ?genename]
                      [?wbggid  :gene/concise-description ?oc]
                      [?oc :gene.concise-description/text ?c]
                      [?wbggid  :gene/provisional-description ?op]
                      [?op :gene.provisional-description/text ?p]
]
EndOfText
  ($arrayRef) = queryRest($restQuery, $show_queries);
  foreach my $entry (@$arrayRef) {
    $entry =~ s/^"//; $entry =~ s/"$//;
    my ($gene, $c, $p) = split/" "/, $entry;
    $data{$gene}{concise}{$c}++;
    $data{$gene}{provisional}{$p}++;
  } # foreach my $entry (@$arrayRef)




  if ($output_format eq 'html') { print qq(<table>); }
  print qq(Your Input\tGene\tPublic Name\tStatus\tSequence Name\tWormPep\tUniprot\tTreeFam\tRefSeq_mRNA\tRefSeq_protein\tRNAi Phenotype Observed\tRNAi Phenotype Not Observed\tAllele Phenotype Observed\tAllele Phenotype Not Observed\tExpr_pattern Tissue\tGenomic Study Tissue\tExpr_pattern LifeStage\tGenomic Study LifeStage\tConcise Description\tProvisional Description\n);
#   print qq(Your Input\tGene\tPublic Name\tStatus\tSequence Name\tUniprot\tTreeFam\tRefSeq_mRNA\tRefSeq_protein\tRNAi Phenotype Observed\tRNAi Phenotype Not Observed\tAllele Phenotype Observed\tAllele Phenotype Not Observed\tExpr_pattern Tissue\tGenomic Study Tissue\tExpr_pattern LifeStage\tGenomic Study LifeStage\tConcise Description\tProvisional Description\n);
#   foreach my $geneId (sort keys %wbgenes) {
  foreach my $sourceGene (@genes) {
    my $output = "$sourceGene\thas no WBGene";
    if ($sourceGenes{$sourceGene} ne 'needsValue') {
      my $geneId = $sourceGenes{$sourceGene};
      my ($status) = join",", sort keys %{ $data{$geneId}{status} };
      my ($pubname) = join",", sort keys %{ $data{$geneId}{pubname} };
      my ($seqname) = join",", sort keys %{ $data{$geneId}{seqname} };
      my ($wormpep) = join",", sort keys %{ $data{$geneId}{wormpep} };
      my ($molname) = join",", sort keys %{ $data{$geneId}{molname} };
      my ($othname) = join",", sort keys %{ $data{$geneId}{othname} };
      my ($uniprot) = join",", sort keys %{ $data{$geneId}{uniprot} };
      my ($treefam) = join",", sort keys %{ $data{$geneId}{treefam} };
      my ($refseqmrna) = join",", sort keys %{ $data{$geneId}{refseqmrna} };
      my ($refseqprotein) = join",", sort keys %{ $data{$geneId}{refseqprotein} };
      my ($rphenyes) = join",", sort keys %{ $data{$geneId}{rphenyes} };
      my ($rphennot) = join",", sort keys %{ $data{$geneId}{rphennot} };
      my ($vphenyes) = join",", sort keys %{ $data{$geneId}{vphenyes} };
      my ($vphennot) = join",", sort keys %{ $data{$geneId}{vphennot} };
      my ($epts) = join",", sort keys %{ $data{$geneId}{epts} };
      my ($gsts) = join",", sort keys %{ $data{$geneId}{gsts} };
      my ($epls) = join",", sort keys %{ $data{$geneId}{epls} };
      my ($gsls) = join",", sort keys %{ $data{$geneId}{gsls} };
      my ($concise)     = join",", sort keys %{ $data{$geneId}{concise} };
      my ($provisional) = join",", sort keys %{ $data{$geneId}{provisional} };
      $output = qq($sourceGene\t$geneId\t$status\t$pubname\t$seqname\t$wormpep\t$molname\t$othname\t$uniprot\t$treefam\t$refseqmrna\t$refseqprotein\t$rphenyes\t$rphennot\t$vphenyes\t$vphennot\t$epts\t$gsts\t$epls\t$gsls\t$concise\t$provisional);
    }
    if ( ($output_format eq 'text') || ($output_format eq 'text_download') ) { print qq($output\n); }
      elsif ($output_format eq 'html') {
        $output =~ s/\t/<\/td><td>/g;
        print qq(<tr><td>$output</td></tr>\n); }
  } # foreach my $geneId (sort keys %wbgenes)
  if ($output_format eq 'html') { print qq(</table>); }
} # sub queryList

sub queryRest {
  my ($restQuery, $show_queries) = @_;
  my ($start, $end, $diff) = ('', '', '');
  if ($show_queries) { $start = time; }
    my $encodedQuery = &url_encode($restQuery);
    my $url = 'http://ec2-52-90-214-72.compute-1.amazonaws.com:8000/api/query?q=' . $encodedQuery . '&args=%5B%7B%3Adb%2Falias%20%22dev%2FWS254%22%7D%5D';        # 2016 07 19
    my $restResult = get $url;
    $restResult =~ s/^\[+//;
    $restResult =~ s/\]+$//;
    my (@entries) = split/\]\s+\[/, $restResult;
  if ($show_queries) { 
    $end = time; 
    $diff = $end - $start;
    print qq($diff seconds : $restQuery<br/>\n);
  }
  return \@entries;
#     foreach my $entry (@entries) {
#       print qq([$entry]<br/>);
#     } # foreach my $entry @entries
}

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
  print qq(<form method="post" action="datomic_simplemine.cgi" enctype="multipart/form-data">\n);
  print qq(Output format<br/>\n);
  print qq(<input type="radio" name="output_format" value="html" checked="checked"> Html output<br/>);
  print qq(<input type="radio" name="output_format" value="text_download"> Text Download output<br/><br/>);
  print qq(Show Queries <input type="checkbox" name="show_queries" checked="checked"><br/><br/>);
  print qq(<h3>Simple Gene Queries</h3><br/>\n);
  print qq(Gene mappings to gene identifiers, Tissue-LifeStage, RNAi-Phenotype, Allele-Phenotype, ConciseDescription.<br/><br/>);
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

sub initEncodeMap {
    for my $ord (0..255) {
        my $chr = pack 'C', $ord;
        my $hex = sprintf '%.2X', $ord;
        $DecodeMap{lc $hex} = $chr;
        $DecodeMap{uc $hex} = $chr;
        $DecodeMap{sprintf '%X%x', $ord >> 4, $ord & 15} = $chr;
        $DecodeMap{sprintf '%x%X', $ord >> 4, $ord & 15} = $chr;
        $EncodeMap{$chr} = '%' . $hex;
    }
    $EncodeMap{"\x20"} = '%20';
#     $EncodeMap{"+"} = '%20';
}
sub url_encode {
#     @_ == 1 || Carp::croak(q/Usage: url_encode(octets)/);
    my ($s) = @_;
    utf8::downgrade($s, 1)
      or Carp::croak(q/Wide character in octet string/);
    $s =~ s/([^0-9A-Za-z_.~-])/$EncodeMap{$1}/gs;
    return $s;
}


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
