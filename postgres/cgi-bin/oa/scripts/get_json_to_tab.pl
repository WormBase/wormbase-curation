#!/usr/bin/perl

# take a jsonFieldQuery the OA would make, and convert to tab-delimited file with headers.
# leaves in <span>
# has to strip out tabs, might need to strip out other characters because  [\x00-\x1f\x22\x2f\x5c]  are invalid in JSON strings.
# change $jsonUrl to appropriate query.
# 2014 03 28


use LWP::Simple;
use JSON;
use Encode qw( from_to is_utf8 );


my $json = JSON->new->allow_nonref;

# $/ = undef;
# open (IN, "<sample");
# my $jsonPage = <IN>;
# close (IN);

my $jsonUrl = 'http://tazendra.caltech.edu/~postgres/cgi-bin/oa/ontology_annotator.cgi?action=jsonFieldQuery&field=curator&userValue=Daniela%20Raciti%20%28%20WBPerson12028%20%29%20&datatype=trp&curator_two=two1823&maxPerQuery=99&allDataTableIds=%20HTTP/1.1%22%20200%206585%20%22';
my $jsonPage = get $jsonUrl;

unless (is_utf8($jsonPage)) { from_to($jsonPage, "iso-8859-1", "utf8"); }
$jsonPage =~ s/\t/ /g;								# needed to avoid : invalid character encountered while parsing JSON string

# print "$jsonPage\n\n";

my %dataHash;
my %headers;

my $perl_scalar = $json->decode( $jsonPage );
# my $perl_scalar = $json->loose->decode( $jsonPage );	# loose is not supported in JSON::XS
my @jsonArr = @$perl_scalar;
foreach my $hashRef (@jsonArr) { 
  my %jsonHash = %$hashRef;
  if ($jsonHash{"id"}) {
    my $id = $jsonHash{"id"};
    foreach my $key (sort keys %jsonHash) {
      if ($jsonHash{$key}) { 
        unless ($key eq 'id') { $headers{$key}++; }
        $dataHash{$id}{$key} = $jsonHash{$key}; }
    } # foreach my $key (sort keys %jsonHash)
  } # if ($jsonHash{"id"})
} # foreach my $arr (@jsonArr)

my (@headers) = sort keys %headers; unshift @headers, 'id';
my $header = join"\t", @headers;
print "$header\n";
foreach my $id (sort keys %dataHash) {
  my @arr;
  foreach my $key (@headers) {
    my $data = '';
    if ($dataHash{$id}{$key}) { $data = $dataHash{$id}{$key}; }
    push @arr, $data;
  }
  my $row = join"\t", @arr;
  print "$row\n";
}
