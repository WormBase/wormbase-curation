#!/usr/bin/perl

# receive post from textpresso

use strict;
use warnings FATAL => 'all';
use CGI;

my $query = new CGI;
my $xml = $query->param('POSTDATA');

my $outfile = '/home/postgres/public_html/cgi-bin/data/textpresso_post_data';
open (OUT, ">>$outfile") or die "Cannot append to $outfile : $!";

print $query->header;
print $query->start_html(-title => "POST SERVER RESPONSE");
print $query->span($xml);
print OUT qq($xml\n);
print $query->end_html;
# print STDERR "ReceivePost.cgi finished.\n";

close (OUT) or die "Cannot close $outfile : $!";
