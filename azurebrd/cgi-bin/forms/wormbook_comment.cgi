#!/usr/bin/perl 

# Get the number of comments and last postdate for a given wormbook chapter comment 


use LWP::Simple;

use Jex;			# untaint, getHtmlVar, cshlNew
use strict;
use CGI;

my $query = new CGI;

print "Content-type: text/html\n\n";

my ($var, $name) = &getHtmlVar($query, 'name');
# print "$name<BR>\n";

# print "<link rel=\"stylesheet\" href=\"http://dev.wormbook.org/css/article.css\">\n";

# print "<FONT SIZE=0.8em >";
my $page = get"http://www.wormbase.org/forums/index.php?board=32.0";
my $posts = 0;
my $comment = 'N/A';
if ($page =~ m/$name<\/a><\/b>.*?(\d+) Posts in.*?Last post on (.*?), \d{2}:\d{2}:\d{2} [AP]M<br \/>/sg) { $posts = $1; $comment = $2; }
elsif ($page =~ m/$name<\/a><\/b>.*?(\d+) Posts in.*?/msg) { $posts = $1; }
else { 1; } # print "NO MATCH<BR>\n"; 
print "<p font=\"0.8\">\n";
# print "<P style=\"font-family: Verdana, sans-serif; text-align: left; text-decoration: none; float: middle; background: ;font-size: 0.6em; margin: 0px 0px 0px 0px\">\n";
# print "<P style=\"font-family: Verdana, sans-serif; \">\n";
# print "<DIV ID=\"section_locator\">\n";
print "Previous comments: <FONT COLOR=purple>$posts</FONT><BR>\n";
print "Last comment: <FONT COLOR=purple>$comment</FONT><BR>\n";
print "</P>";
# print "</DIV>\n";
print "</FONT>\n";
