#!/usr/bin/perl

# js redirect to generic.cgi

use CGI;

print <<"EndOfText";
Content-type: text/html

<html>
<script type="text/javascript">
window.location.replace("http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=WpaXref");
</script>
</html>
EndOfText
