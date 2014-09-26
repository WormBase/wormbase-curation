package helperOA;
require Exporter;

our @ISA	= qw(Exporter);
our @EXPORT	= qw( getPgDate getHtmlVar pad10Zeros pad9Zeros pad8Zeros fromUrlToPostgres );
our $VERSION	= 1.00;

sub getPgDate {					# get the date in postgres format
  my $time = time;				# get time from shell
  my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime($time);	# convert time
  if ($sec < 10) { $sec = "0$sec"; }		# add a zero if needed
  if ($min < 10) { $min = "0$min"; }		# add a zero if needed
  if ($mday < 10) { $mday = "0$mday"; }		# add a zero if needed
  my $sam = $mon + 1;				# get correct month
  if ($sam < 10) { $sam = "0$sam"; }		# add a zero if needed
  $year = 1900 + $year;				# get right year in 4 digit form
  my $todaydate = "${year}-${sam}-${mday}";	# set current date
  my $date = $todaydate . " $hour\:$min\:$sec";	# set final date
  return $date;
} # sub getPgDate

sub untaint {					# untaint data from form
  my $tainted = shift;
  my $untainted;
  if ($tainted eq "") {
    $untainted = "";
  } else { # if ($tainted eq "")
    $tainted =~ s/[^\w\-.,;:?\/\\@#\$\%\^&*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]//g;	
    if ($tainted =~ m/^([\w\-.,;:?\/\\@#\$\%&\^*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]+)$/) {
      $untainted = $1;
    } else {
      die "Bad data Tainted in $tainted";
    }
  } # else # if ($tainted eq "")
  return $untainted;
} # sub untaint

sub getHtmlVar {		# get variables from html form and untaint them
  no strict 'refs';		# need to disable refs to get the values
  my ($query, $var, $err) = @_;	# get the CGI query val, 
				# get the name of the variable to query->param,
				# get whether to display an error if no such variable found
  if ($query->param("$var")) {			# if we got a value
    my $oop = $query->param("$var");		# get the value
    $$var = &untaint($oop);			# untaint and put value under ref
    return ($var, $$var);			# return the variable and value
  } else { # if ($query->param("$var"))		# if no such variable found
    if ($err) {					# if we want error displayed, display error
      print "<FONT COLOR=blue>ERROR : No such variable : $var</FONT><BR>\n"; }
  } # else # if ($query->param("$var"))
} # sub getHtmlVar

sub pad10Zeros {		# take a number and pad to 10 digits
  my $number = shift;
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }		# strip leading zeros
  if ($number < 10) { $number = '000000000' . $number; }
  elsif ($number < 100) { $number = '00000000' . $number; }
  elsif ($number < 1000) { $number = '0000000' . $number; }
  elsif ($number < 10000) { $number = '000000' . $number; }
  elsif ($number < 100000) { $number = '00000' . $number; }
  elsif ($number < 1000000) { $number = '0000' . $number; }
  elsif ($number < 10000000) { $number = '000' . $number; }
  elsif ($number < 100000000) { $number = '00' . $number; }
  elsif ($number < 1000000000) { $number = '0' . $number; }
  return $number;
} # sub pad10Zeros

sub pad9Zeros {		# take a number and pad to 9 digits
  my $number = shift;
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }		# strip leading zeros
  if ($number < 10) { $number = '00000000' . $number; }
  elsif ($number < 100) { $number = '0000000' . $number; }
  elsif ($number < 1000) { $number = '000000' . $number; }
  elsif ($number < 10000) { $number = '00000' . $number; }
  elsif ($number < 100000) { $number = '0000' . $number; }
  elsif ($number < 1000000) { $number = '000' . $number; }
  elsif ($number < 10000000) { $number = '00' . $number; }
  elsif ($number < 100000000) { $number = '0' . $number; }
  return $number;
} # sub pad9Zeros

sub pad8Zeros {		# take a number and pad to 8 digits
  my $number = shift;
  if ($number =~ m/^0+/) { $number =~ s/^0+//g; }		# strip leading zeros
  if ($number < 10) { $number = '0000000' . $number; }
  elsif ($number < 100) { $number = '000000' . $number; }
  elsif ($number < 1000) { $number = '00000' . $number; }
  elsif ($number < 10000) { $number = '0000' . $number; }
  elsif ($number < 100000) { $number = '000' . $number; }
  elsif ($number < 1000000) { $number = '00' . $number; }
  elsif ($number < 10000000) { $number = '0' . $number; }
  return $number;
} # sub pad8Zeros

sub fromUrlToPostgres {
  my $value = shift;
  if ($value =~ m/%2B/) { $value =~ s/%2B/+/g; }		# convert URL plus to literal
  if ($value =~ m/%23/) { $value =~ s/%23/#/g; }		# convert URL pound to literal
  if ($value =~ m/\'/) { $value =~ s/\'/''/g; }			# escape singlequotes
  return $value;
} # sub fromUrlToPostgres


1;


__END__

=head1 NAME

helperOA - extra subroutines used for general purposes by ontology_annotator.cgi and config perl modules.

=head1 SYNOPSIS

    my ($var, $value) = &getHtmlVar($query, $field_name);

    my $date = &getPgDate();

=head1 DESCRIPTION

Some subroutines are commonly used by ontology_annotator.cgi and config-specific perl modules.  This module loads them.

&getHtmlVar  takes as values the CGI $query and the name of the html field to query.  Returns the html field name and its value.

&getPgDate  gets the current timestamp in postgreSQL format.

&pad10Zeros  takes a number, pads to 10 digits, and returns it.

&pad9Zeros  takes a number, pads to 9 digits, and returns it.

&pad8Zeros  takes a number, pads to 8 digits, and returns it.

&fromUrlToPostgres  takes a value passed from a URL and parses to postgres format.
