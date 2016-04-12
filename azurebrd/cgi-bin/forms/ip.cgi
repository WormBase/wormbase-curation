#!/usr/bin/perl 

# Form to find out your IP.



use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;

my $query = new CGI;
my $host = $query->remote_host();		# get ip address

print "Content-type: text/html\n\n";
my $title = 'Your IP';
my ($header, $footer) = &cshlNew($title);
print "$header\n";		# make beginning of HTML page
print "Your IP is : $host<BR>\n";
print "$footer"; 		# make end of HTML page

