#!/usr/bin/perl

# do datomic queries through adam's machine

use strict;
use CGI;
use LWP::Simple;

my $query = new CGI;

my $var;
my (%DecodeMap, %EncodeMap);
&initEncodeMap();


print "Content-type: text/html\n\n";
# print "CGI working.<br/>blah blah<br/>\n";

($var, my $action) = &getHtmlVar($query, 'action');
unless ($action) { $action = 'printForm'; } 

# # my $restQuery = '%5B%3Afind%20%3Fc%20%3Ain%20%24%20%3Awhere%20%5B%3Fc%20%3Agene%2Fid%20%22WBGene00000001%22%5D%5D';
# my $restQuery = qq([:find ?c :in $ :where [?c :gene/id "WBGene00000001"]);
#   
#   print qq(RQ $restQuery RQ<br/>\n);
#   my $encoded = &url_encode($restQuery);
#   print qq(ERQ $encoded ERQ<br/>\n);

if ($action) {
  if ($action eq 'printForm') {                              &printForm();          }
    elsif ($action eq 'datomic query') {                     &restQuery();          }
}


sub printForm {
  my ($restQuery) = @_;
  unless ($restQuery) { $restQuery = ''; }
  print qq(<form method="get">);
  print qq(<textarea rows="18" cols="100"  name="restQuery" id="restQuery">$restQuery</textarea><br/>);
  print qq(<input type="submit" name="action" value="datomic query">);
  print qq(</form><br/>);
}

sub restQuery {
  ($var, my $restQuery) = &getHtmlVar($query, 'restQuery');
  &printForm($restQuery);

  unless ($restQuery) { $restQuery = '%5B%3Afind%20%3Fc%20%3Ain%20%24%20%3Awhere%20%5B%3Fc%20%3Agene%2Fid%20%22WBGene00000001%22%5D%5D'; }
  
#   print qq(RQ $restQuery RQ<br/>);
  my $encodedQuery = &url_encode($restQuery);
#   print qq(ERQ $encodedQuery ERQ<br/>);

# old
#   my $url = 'http://localhost:8000/api/query?q=' . $encodedQuery . '&args=%5B%7B%3Adb%2Falias%20%22dev%2FWS252%22%7D%5D';
#   my $url = 'http://ec2-23-20-57-180.compute-1.amazonaws.com/cgi-bin/azurebrd/datomic.cgi?restQuery=' . $encodedQuery . '&action=datomic+query';

# To use datomic cgi from aws machine
#   my $url = 'http://ec2-52-90-214-72.compute-1.amazonaws.com/cgi-bin/azurebrd/datomic.cgi?restQuery=' . $encodedQuery . '&action=datomic+query';
#   my $awsResult = get $url;
#   my ($restResult) = $awsResult =~ m/REST (.*?) RESULT/ms;

# To use the datomic rest api from aws machine
  my $url = 'http://ec2-52-90-214-72.compute-1.amazonaws.com:8000/api/query?q=' . $encodedQuery . '&args=%5B%7B%3Adb%2Falias%20%22dev%2FWS254%22%7D%5D';	# 2016 07 19
  my $restResult = get $url;

#   print qq(URL $url URL<br/>);
  $restResult =~ s/^\[+//;
  $restResult =~ s/\]+$//;
  my (@entries) = split/\]\s+\[/, $restResult;
  foreach my $entry (@entries) {
    print qq([$entry]<br/>);
  } # foreach my $entry @entries
#   print qq(REST $restResult RESULT<br/>);
} # sub restQuery

sub url_encode {
#     @_ == 1 || Carp::croak(q/Usage: url_encode(octets)/);
    my ($s) = @_;
    utf8::downgrade($s, 1)
      or Carp::croak(q/Wide character in octet string/);
    $s =~ s/([^0-9A-Za-z_.~-])/$EncodeMap{$1}/gs;
    return $s;
}

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

sub getHtmlVar {                # get variables from html form and untaint them
  no strict 'refs';             # need to disable refs to get the values
                                # possibly a better way than this
  my ($query, $var, $err) = @_; # get the CGI query val,
                                # get the name of the variable to query->param,
                                # get whether to display and error if no such
                                # variable found
  unless ($query->param("$var")) {              # if no such variable found
    if ($err) {                 # if we want error displayed, display error
      print "<FONT COLOR=blue>ERROR : No such variable : $var</FONT><BR>\n";
    } # if ($err)
  } else { # unless ($query->param("$var"))     # if we got a value
    my $oop = $query->param("$var");            # get the value
    $$var = &untaint($oop);                     # untaint and put value under ref
    return ($var, $$var);                       # return the variable and value
  } # else # unless ($query->param("$var"))
} # sub getHtmlVar

sub untaint {
  my $tainted = shift;
  my $untainted;
  if ($tainted eq "") {
    $untainted = "";
  } else { # if ($tainted eq "")
    $tainted =~ s/[^\w\-.,;:?\/\\@#\$\%\^&*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]//g;     # added \" for wbpaper_editor's gene evidence data 2005 07 14   added \> and \< for wbpaper_editor's abstract data  2005 12 13
    if ($tainted =~ m/^([\w\-.,;:?\/\\@#\$\%&\^*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]+)$/) {
      $untainted = $1;
    } else {
      die "Bad data Tainted in $tainted";
    }
  } # else # if ($tainted eq "")
  return $untainted;
} # sub untaint

