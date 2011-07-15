#!/usr/bin/perl -w

# create oac_column_<width|order|showhide>  2011 01 28


use strict;
use diagnostics;
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;

# put postgres users that should have 'all' access to the table.
my @users_all = ('apache', 'azurebrd', 'cecilia', '"www-data"');

# put postgres users that should have 'select' access to the table.  mainly so they can log on and see the data from a shell, but would probably work if you set the webserver to have select access, it would just give error messages if someone tried to update data.
my @users_select = ('acedb');

my @tables = qw( width order showhide );
foreach my $table_type (@tables) {
  my $table = 'oac_column_' . $table_type; 
  $result = $dbh->do("DROP TABLE $table; ");
  $result = $dbh->do( "CREATE TABLE $table ( oac_datatype text, oac_table text, oac_curator text, $table text, oac_timestamp timestamp with time zone DEFAULT \"timestamp\"('now'::text) );" );

  $result = $dbh->do( "CREATE INDEX ${table}_idx ON $table USING btree (oac_datatype);" );
  $result = $dbh->do("REVOKE ALL ON TABLE $table FROM PUBLIC; ");
  foreach my $user (@users_select) {
    $result = $dbh->do( "GRANT SELECT ON TABLE $table TO $user; "); }
  foreach my $user (@users_all) {
    $result = $dbh->do( "GRANT ALL ON TABLE $table TO $user; "); }
} # foreach my $table_type (@tables)


__END__


=head1 NAME

create_oac_columns.pl - script to create postgres tables for ontology annotator column tables.


=head1 SYNOPSIS

Edit array of users to grant permission to (both 'select' and 'all'), then run with

  ./create_oac_columns.pl


=head1 DESCRIPTION

The ontology_annotator.cgi requires some postgres tables to store column properties for each curator-datatype-table .  The column properties are:

=over 4

=item * default width in pixels when the dataTable loads.

=item * whether to show or hide a column when the dataTable loads.

=item * the order of the columns when the dataTable loads.

=back

Edit array of postgres database users to grant permission to (both 'select' and 'all'), then run with

  ./create_oac_columns.pl
