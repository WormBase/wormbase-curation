#!/usr/bin/perl -w

# Populate obo_{name|syn|data}_<obotable> tables in postgres based off webpages where the obos are stored.  


use strict;
use diagnostics;
use DBI;
use LWP::Simple;
use LWP;
use Crypt::SSLeay;		# for LWP to get https


my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

# need a directory to store previous results so a cronjob only updates tables when the data is new
my $directory = '/home/postgres/public_html/cgi-bin/oa/scripts/obo_oa_ontologies/';
chdir ($directory) or die "Cannot chdir to $directory : $!";


# put postgres users that should have 'all' access to the table.
my @users_all = ('apache', 'azurebrd', 'cecilia', '"www-data"');

# put postgres users that should have 'select' access to the table.  mainly so they can log on and see the data from a shell, but would probably work if you set the webserver to have select access, it would just give error messages if someone tried to update data.
my @users_select = ('acedb');


# enter obotable - URL hash entries here
my %obos;
$obos{anatomy} = 'http://brebiou.cshl.edu/viewcvs/*checkout*/Wao/WBbt.obo';
$obos{chebi} = 'ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo';
$obos{entity} = 'http://www.berkeleybop.org/ontologies/obo-all/rex/rex.obo';
$obos{goid} = 'http://www.geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo';
$obos{lifestage} = 'http://www.berkeleybop.org/ontologies/obo-all/worm_development/worm_development.obo';
$obos{quality} = 'http://www.berkeleybop.org/ontologies/obo-all/quality/quality.obo';


# uncomment and run only once for each obotable to create the related tables 
# foreach my $obotable (sort keys %obos) { &createTable($obotable); }


$/ = undef;
foreach my $obotable (sort keys %obos) {
  print "getting $obotable\n";
  my $new_data = get $obos{$obotable};
  print "got $obotable\n";
  my $file_name = $directory . 'obo_' . $obotable;
  my $file_data = ""; my $file_date = 0;
  if (-r $file_name) {						# if a file existed from a previous run get the date it was last updated
    open (IN, "<$file_name") or die "Cannot open $file_name : $!";
    $file_data = <IN>;
    close (IN) or die "Cannot close $file_name : $!";
    my ($day, $month, $year, $hour, $minute) = $file_data =~ m/date: (\d+):(\d+):(\d+) (\d+):(\d+)/;
    $file_date = $year . $month . $day . $hour . $minute;
  }
  if ($new_data =~ m/date: (\d+):(\d+):(\d+) (\d+):(\d+)/) {	# if the new file's date is more recent than the last run's date, update postgres table data
    my ($day, $month, $year, $hour, $minute) = $new_data =~ m/date: (\d+):(\d+):(\d+) (\d+):(\d+)/;
    my $new_date = $year . $month . $day . $hour . $minute;
    if ($new_date > $file_date) { &updateData($obotable, $file_name, $new_data); }
  } # if ($new_data =~ m/date: (\d+):(\d+):(\d+) (\d+):(\d+)/)
} # foreach my $obotable (sort keys %obos) 
$/ = "\n";


sub updateData {
  my ($obotable, $file_name, $new_data) = @_;
  my @tables = qw( name syn data );				# the three table types: name, synonym, data for term info display
  foreach my $table_type (@tables) {
    my $table = 'obo_' . $table_type . '_' . $obotable;
    print "DELETE FROM $table; \n";
    $result = $dbh->do("DELETE FROM $table; ");			# delete existing postgres table data
  }
  my (@terms) = split/\[Term\]/, $new_data;			# get terms
  my $term = shift @terms;					# junk header

  my %children; 						# for term info's forward and back arrows to work, store children relationship
  if ($obotable eq 'phenotype') {				# sample of creation of parental relationship based on 'is_a:' and 'relationship: part_of' tags in .obo file
    foreach $term (@terms) {
      my ($id) = $term =~ m/\nid: (.*?)\n/;
      my ($name) = $term =~ m/\nname: (.*?)\n/;
      my (@parents) = $term =~ m/is_a: (WBPhenotype:\d+)/g;				# change the ID type for other obotable types
      foreach my $parent (@parents) { $children{$parent}{"$id \! $name"}++; }
      (@parents) = $term =~ m/relationship: part_of (WBPhenotype:\d+)/g;		# change the ID type for other obotable types
      foreach my $parent (@parents) { $children{$parent}{"$id \! $name"}++; }
    }
  }

  foreach $term (@terms) {
    $term =~ s/\\//g;							# strip \ escaped data
    my @syns = ();
    my ($id) = $term =~ m/\nid: (.*?)\n/;
    if ($obotable eq 'chebi') { $id =~ s/CHEBI://; }			# sample of id processing for specific obotables
    my ($name) = $term =~ m/\nname: (.*?)\n/;
    $name =~ s/\"//g; $name =~ s/\'/''/g; 
    if ($term =~ m/\nsynonym: \"(.*?)\"/) {
      (@syns) = $term =~ m/\nsynonym: \"(.*?)\"/g; }
    $term =~ s/^\s+//sg; $term =~ s/\s+$//sg; $term =~ s/\'/''/g; 	# strip leading and trailing spaces, escape singlequotes for postgres
    my $table = 'obo_name_' . $obotable;
    $result = $dbh->do("INSERT INTO $table VALUES( '$id', '$name') ");
    $table = 'obo_data_' . $obotable;

    if ($obotable eq 'chebi') { 					# sample of URL link processing for specific obotables
      $term = 'chebi link: <a href="http://www.ebi.ac.uk/chebi/" target="new">http://www.ebi.ac.uk/chebi/</a>' . "<br />\n" . $term;
      if ($term =~ m/name: (.*)\n/) {
        $term =~ s/name: (.*)\n/name: <a href=\"http:\/\/www.ebi.ac.uk\/chebi\/advancedSearchFT.do?searchString=$1&queryBean.stars=-1\" target=\"new\">$1<\/a>\n/g; } }
    elsif ($obotable eq 'phenotype') {					# sample of obo tree link processing for specific obotables with %children data to travel term info with forward and back arrows
      $term =~ s/is_a:/parent:/g;							# 'is_a:' tags become 'parent:' tags
      $term =~ s/relationship: part_of/parent:/g;					# 'relationship: part_of' tags become 'parent:' tags
      $term =~ s/\nparent/\n<hr>parent/;
      foreach my $child_term (sort keys %{ $children{$id} }) { $term .= "\nchild: $child_term"; } 	# %children terms are added as 'child:' tags
      my $url = "ontology_annotator.cgi?action=oboFrame&obotable=$obotable&term_id=";
      $term =~ s/(WBPhenotype:\d+) \! ([\w ]+)/<a href=\"${url}$1\">$2<\/a>/g;		# change the ID type for other obotable types
    }

    my (@term) = split/\n/, $term;
    foreach my $term_line (@term) { $term_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }		# add span to bold tags in term info
    $term = join"\n", @term;
    $result = $dbh->do("INSERT INTO $table VALUES( '$id', '$term') ");
    $table = 'obo_syn_' . $obotable;
    foreach my $syn (@syns) {
      $syn =~ s/\'/''/g; 
      $result = $dbh->do("INSERT INTO $table VALUES( '$id', '$syn') "); }
  } # foreach $term (@terms)
  open (OUT, ">$file_name") or die "Cannot write to $file_name : $!"; 	# store new data in flatfile for future comparison
  print OUT "$new_data";
  close (OUT) or die "Cannot close $file_name : $!"; 
} # sub updateData


sub createTable {							# create postgres tables for a given obotable
  my ($obotable) = @_;
  my @tables = qw( name syn data );
  foreach my $table_type (@tables) {
    my $table = 'obo_' . $table_type . '_' . $obotable;
    $result = $dbh->do("DROP TABLE $table; ");
    $result = $dbh->do( "CREATE TABLE $table ( joinkey text, $table text, obo_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );
    $result = $dbh->do( "CREATE INDEX ${table}_idx ON $table USING btree (joinkey);" );
    $result = $dbh->do("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
    foreach my $user (@users_select) {
      $result = $dbh->do( "GRANT SELECT ON TABLE $table TO $user; "); }
    foreach my $user (@users_all) {
      $result = $dbh->do( "GRANT ALL ON TABLE $table TO $user; "); }
  } # foreach my $table_type (@tables)
} # sub createTable


__END__


=head1 NAME

update_obo_oa_ontologies.pl - script to create, populate, or update postgres tables for ontology annotator obotables.


=head1 SYNOPSIS

Edit the array of users to grant permission to (both 'select' and 'all'), edit obotable to URL hash entries in %obos hash, add optional code for specific obotable types, then run with

  ./update_obo_oa_ontologies.pl


=head1 DESCRIPTION

The ontology_annotator.cgi allows .obo files to be generically parsed into postgres tables for obotables used in fields of type 'ontology' or 'multiontology'.

.obo data changes routinely, so this script can run on a cronjob to update data when the obo files's 'date:' line has changed.


=head2 SCRIPT REQUIREMENTS

Create a directory to store the last version of each obo file.  Change the path to it in the $directory variable.

Edit array of postgres database users to grant permission to (both 'select' and 'all').

Edit %obos hash for mappings of obotable to URL of .obo file.


=head2 CREATE TABLES

If creating an obotable type for the first time:

=over 4 

=item * comment out all %obos entries that already have tables.

=item * uncomment the lines to  &createTable  for the datatype .

=item * run with

  ./update_obo_oa_ontologies.pl

=item * put the script back the way it was.

=back


=head2 TERM INFO OBO TREE BROWSING

The script can be edited to add custom changes for specific obotables, such as parsing names, IDs, adding URL links in term information, creating obo tree links to browse the term info obo structure.  

When creating obo tree links to browse the term info obo structure:

=over 4 

=item * add conditional to populate %children and change the ID matching.

=item * add conditional to process each term and change the ID matching.

=back

%children are populated by matching on 'is_a:' and 'relationship: part_of' tags in .obo file


=head2 SCRIPT FUNCTION

For each obotable .obo file compare date of downloaded .obo file with date of last .obo file used to populate postgres tables ;  if the date is more recent, delete all data from tables, populate from new file, and write file to flatfile for future comparison.

The downloaded data file is split on '[Term]'.  Id is a match on 'id: ' to the newline.  Name is a match on 'name: ' to the newline.  Synonyms are matches on 'synonym: "<match>"'.  Data is the whole entry.  Data lines are split, for each line the tag is anything up to the first colon, and it has a span html element tag added to bold it.  There is a single entry for a given term id for name and data, but there can be multiple entries for synonyms, one for each synonym.


