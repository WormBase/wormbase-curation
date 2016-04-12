package wormOA;
require Exporter;

# WormBase MOD configuration for Ontology Annotator
# 
# See the bottom of this file for the POD documentation.  Search for the string '=head'.



our @ISA        = qw(Exporter);
our @EXPORT     = qw( initModFields loginMod setAnySimpleAutocompleteValues getAnySpecificAutocomplete getAnySpecificValidValue getAnySpecificTermInfo getAnySpecificIdToValue );
our $VERSION    = 1.00;

use strict;
use diagnostics;
use LWP::UserAgent;
use helperOA;		# &getPgDate  &getHtmlVar  &pad10Zeros  &pad8Zeros
use DBI;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n";
use Tie::IxHash;


### FIELDS ###

sub initModFields {
  my ($datatype, $curator_two) = @_;
  &initWormFields($datatype, $curator_two); }

sub initWormFields {
  my ($datatype, $curator_two) = @_;
  my $fieldsRef; my $datatypesRef;
  if ($datatype eq 'abp')    { ($fieldsRef, $datatypesRef) = &initWormAbpFields($datatype, $curator_two); }
  elsif ($datatype eq 'app') { ($fieldsRef, $datatypesRef) = &initWormAppFields($datatype, $curator_two); }
  elsif ($datatype eq 'cns') { ($fieldsRef, $datatypesRef) = &initWormCnsFields($datatype, $curator_two); }
  elsif ($datatype eq 'con') { ($fieldsRef, $datatypesRef) = &initWormConFields($datatype, $curator_two); }
  elsif ($datatype eq 'dis') { ($fieldsRef, $datatypesRef) = &initWormDisFields($datatype, $curator_two); }
  elsif ($datatype eq 'dit') { ($fieldsRef, $datatypesRef) = &initWormDitFields($datatype, $curator_two); }
  elsif ($datatype eq 'exp') { ($fieldsRef, $datatypesRef) = &initWormExpFields($datatype, $curator_two); }
  elsif ($datatype eq 'gcl') { ($fieldsRef, $datatypesRef) = &initWormGclFields($datatype, $curator_two); }
  elsif ($datatype eq 'gop') { ($fieldsRef, $datatypesRef) = &initWormGopFields($datatype, $curator_two); }
  elsif ($datatype eq 'grg') { ($fieldsRef, $datatypesRef) = &initWormGrgFields($datatype, $curator_two); }
  elsif ($datatype eq 'int') { ($fieldsRef, $datatypesRef) = &initWormIntFields($datatype, $curator_two); }
  elsif ($datatype eq 'mop') { ($fieldsRef, $datatypesRef) = &initWormMopFields($datatype, $curator_two); }
  elsif ($datatype eq 'mov') { ($fieldsRef, $datatypesRef) = &initWormMovFields($datatype, $curator_two); }
  elsif ($datatype eq 'pic') { ($fieldsRef, $datatypesRef) = &initWormPicFields($datatype, $curator_two); }
  elsif ($datatype eq 'pro') { ($fieldsRef, $datatypesRef) = &initWormProFields($datatype, $curator_two); }
  elsif ($datatype eq 'prt') { ($fieldsRef, $datatypesRef) = &initWormPrtFields($datatype, $curator_two); }
  elsif ($datatype eq 'ptg') { ($fieldsRef, $datatypesRef) = &initWormPtgFields($datatype, $curator_two); }
  elsif ($datatype eq 'rna') { ($fieldsRef, $datatypesRef) = &initWormRnaFields($datatype, $curator_two); }
  elsif ($datatype eq 'sqf') { ($fieldsRef, $datatypesRef) = &initWormSqfFields($datatype, $curator_two); }
  elsif ($datatype eq 'trp') { ($fieldsRef, $datatypesRef) = &initWormTrpFields($datatype, $curator_two); }
  return( $fieldsRef, $datatypesRef);
} # sub initWormFields

sub initWormAbpFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{abp} }, "Tie::IxHash";
  $fields{abp}{id}{type}                             = 'text';
  $fields{abp}{id}{label}                            = 'pgid';
  $fields{abp}{id}{tab}                              = 'tab1';
  $fields{abp}{name}{type}                           = 'text';
  $fields{abp}{name}{label}                          = 'Name';
  $fields{abp}{name}{tab}                            = 'tab1';
  $fields{abp}{gene}{type}                           = 'multiontology';
  $fields{abp}{gene}{label}                          = 'Gene';
  $fields{abp}{gene}{tab}                            = 'tab1';
  $fields{abp}{gene}{ontology_type}                  = 'WBGene';
  $fields{abp}{clonality}{type}                      = 'dropdown';
  $fields{abp}{clonality}{label}                     = 'Clonality';
  $fields{abp}{clonality}{tab}                       = 'tab1';
  $fields{abp}{clonality}{dropdown_type}             = 'clonality';
  $fields{abp}{animal}{type}                         = 'dropdown';
  $fields{abp}{animal}{label}                        = 'Animal';
  $fields{abp}{animal}{tab}                          = 'tab1';
  $fields{abp}{animal}{dropdown_type}                = 'animal';
  $fields{abp}{antigen}{type}                        = 'dropdown';
  $fields{abp}{antigen}{label}                       = 'Antigen';
  $fields{abp}{antigen}{tab}                         = 'tab1';
  $fields{abp}{antigen}{dropdown_type}               = 'antigen';
  $fields{abp}{peptide}{type}                        = 'bigtext';
  $fields{abp}{peptide}{label}                       = 'Peptide';
  $fields{abp}{peptide}{tab}                         = 'tab1';
  $fields{abp}{protein}{type}                        = 'bigtext';
  $fields{abp}{protein}{label}                       = 'Protein';
  $fields{abp}{protein}{tab}                         = 'tab1';
  $fields{abp}{source}{type}                         = 'dropdown';
  $fields{abp}{source}{label}                        = 'Source';
  $fields{abp}{source}{tab}                          = 'tab1';
  $fields{abp}{source}{dropdown_type}                = 'abpsource';
  $fields{abp}{original_publication}{type}           = 'ontology';
  $fields{abp}{original_publication}{label}          = 'Original Publication';
  $fields{abp}{original_publication}{tab}            = 'tab1';
  $fields{abp}{original_publication}{ontology_type}  = 'WBPaper';
  $fields{abp}{paper}{type}                          = 'multiontology';
  $fields{abp}{paper}{label}                         = 'Reference';
  $fields{abp}{paper}{tab}                           = 'tab1';
  $fields{abp}{paper}{ontology_type}                 = 'WBPaper';
  $fields{abp}{remark}{type}                         = 'bigtext';
  $fields{abp}{remark}{label}                        = 'Remark';
  $fields{abp}{remark}{tab}                          = 'tab1';
  $fields{abp}{other_name}{type}                     = 'bigtext';
  $fields{abp}{other_name}{label}                    = 'Other Name';
  $fields{abp}{other_name}{tab}                      = 'tab1';
  $fields{abp}{laboratory}{type}                     = 'multiontology';
  $fields{abp}{laboratory}{label}                    = 'Laboratory';
  $fields{abp}{laboratory}{tab}                      = 'tab1';
  $fields{abp}{laboratory}{ontology_type}            = 'obo';
  $fields{abp}{laboratory}{ontology_table}           = 'laboratory';
  $fields{abp}{other_animal}{type}                   = 'bigtext';
  $fields{abp}{other_animal}{label}                  = 'Other Animal';
  $fields{abp}{other_animal}{tab}                    = 'tab1';
  $fields{abp}{other_antigen}{type}                  = 'bigtext';
  $fields{abp}{other_antigen}{label}                 = 'Other Antigen';
  $fields{abp}{other_antigen}{tab}                   = 'tab1';
  $fields{abp}{possible_pseudonym}{type}             = 'bigtext';
  $fields{abp}{possible_pseudonym}{label}            = 'Possible Pseudonym';
  $fields{abp}{possible_pseudonym}{tab}              = 'tab1';
  $fields{abp}{summary}{type}                        = 'bigtext';
  $fields{abp}{summary}{label}                       = 'Summary';
  $fields{abp}{summary}{tab}                         = 'tab1';
  $fields{abp}{curator}{type}                        = 'dropdown';
  $fields{abp}{curator}{label}                       = 'Curator';
  $fields{abp}{curator}{tab}                         = 'tab1';
  $fields{abp}{curator}{dropdown_type}               = 'curator';
  $fields{abp}{humandoid}{type}                      = 'multiontology';
  $fields{abp}{humandoid}{label}                     = 'Antibody for disease';
  $fields{abp}{humandoid}{tab}                       = 'tab2';
  $fields{abp}{humandoid}{ontology_type}             = 'obo';
  $fields{abp}{humandoid}{ontology_table}            = 'humando';
  $fields{abp}{diseasepaper}{type}                   = 'multiontology';
  $fields{abp}{diseasepaper}{label}                  = 'Disease Paper';
  $fields{abp}{diseasepaper}{tab}                    = 'tab2';
  $fields{abp}{diseasepaper}{ontology_type}          = 'WBPaper';
  $datatypes{abp}{newRowSub}                         = \&newRowAbp;
  $datatypes{abp}{label}                             = 'antibody';
  @{ $datatypes{abp}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormAbpFields

sub initWormAppFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{app} }, "Tie::IxHash";
  $fields{app}{id}{type}                             = 'text';
  $fields{app}{id}{label}                            = 'pgid';
  $fields{app}{id}{tab}                              = 'tab1';
  $fields{app}{curator}{type}                        = 'dropdown';
  $fields{app}{curator}{label}                       = 'Curator';
  $fields{app}{curator}{tab}                         = 'tab1';
  $fields{app}{curator}{dropdown_type}               = 'curator';
  $fields{app}{paper}{type}                          = 'ontology';
  $fields{app}{paper}{label}                         = 'Pub';
  $fields{app}{paper}{tab}                           = 'tab1';
  $fields{app}{paper}{ontology_type}                 = 'WBPaper';
  $fields{app}{person}{type}                         = 'multiontology';
  $fields{app}{person}{label}                        = 'Person';
  $fields{app}{person}{tab}                          = 'tab1';
  $fields{app}{person}{ontology_type}                = 'WBPerson';
  $fields{app}{term}{type}                           = 'ontology';
  $fields{app}{term}{label}                          = 'Phenotype';
  $fields{app}{term}{tab}                            = 'all';
  $fields{app}{term}{ontology_type}                  = 'obo';
  $fields{app}{term}{ontology_table}                 = 'phenotype';
  $fields{app}{not}{type}                            = 'toggle';
  $fields{app}{not}{label}                           = 'NOT';
  $fields{app}{not}{tab}                             = 'all';
  $fields{app}{phen_remark}{type}                    = 'bigtext';
  $fields{app}{phen_remark}{label}                   = 'Phenotype Remark';
  $fields{app}{phen_remark}{tab}                     = 'all';
  $fields{app}{phen_remark}{columnWidth}             = '600';
  $fields{app}{variation}{type}                      = 'ontology';
  $fields{app}{variation}{label}                     = 'Variation';
  $fields{app}{variation}{tab}                       = 'tab1';
  $fields{app}{variation}{ontology_type}             = 'obo';
  $fields{app}{variation}{ontology_table}            = 'variation';
  $fields{app}{transgene}{type}                      = 'ontology';
  $fields{app}{transgene}{label}                     = 'Transgene';
  $fields{app}{transgene}{tab}                       = 'tab1';
  $fields{app}{transgene}{ontology_type}             = 'Transgene';
  $fields{app}{strain}{type}                         = 'text';
  $fields{app}{strain}{label}                        = 'Strain';
  $fields{app}{strain}{tab}                          = 'tab1';
  $fields{app}{rearrangement}{type}                  = 'ontology';
  $fields{app}{rearrangement}{label}                 = 'Rearrangement';
  $fields{app}{rearrangement}{tab}                   = 'tab1';
  $fields{app}{rearrangement}{ontology_type}         = 'obo';
  $fields{app}{rearrangement}{ontology_table}        = 'rearrangement';
  $fields{app}{obj_remark}{type}                     = 'text';
  $fields{app}{obj_remark}{label}                    = 'Object Remark';
  $fields{app}{obj_remark}{tab}                      = 'tab1';
  $fields{app}{allele_status}{type}                  = 'dropdown';
  $fields{app}{allele_status}{label}                 = 'Allele Status';
  $fields{app}{allele_status}{tab}                   = 'tab1';
  $fields{app}{allele_status}{dropdown_type}         = 'allelestatus';
  $fields{app}{caused_by}{type}                      = 'ontology';
  $fields{app}{caused_by}{label}                     = 'Caused By Gene';
  $fields{app}{caused_by}{tab}                       = 'tab1';
  $fields{app}{caused_by}{ontology_type}             = 'WBGene';
  $fields{app}{caused_by_other}{type}                = 'text';
  $fields{app}{caused_by_other}{label}               = 'Caused By Other';
  $fields{app}{caused_by_other}{tab}                 = 'tab1';
  $fields{app}{suggested}{type}                      = 'text';
  $fields{app}{suggested}{label}                     = 'Suggested';
  $fields{app}{suggested}{tab}                       = 'tab2';
  $fields{app}{suggested_definition}{type}           = 'bigtext';
  $fields{app}{suggested_definition}{label}          = 'Suggested Definition';
  $fields{app}{suggested_definition}{tab}            = 'tab2';
  $fields{app}{child_of}{type}                       = 'multiontology';
  $fields{app}{child_of}{label}                      = 'Child Of';
  $fields{app}{child_of}{tab}                        = 'tab2';
  $fields{app}{child_of}{ontology_type}              = 'obo';
  $fields{app}{child_of}{ontology_table}             = 'phenotype';
  $fields{app}{goprocess}{type}                      = 'multiontology';
  $fields{app}{goprocess}{label}                     = 'GO Process';
  $fields{app}{goprocess}{tab}                       = 'tab2';
  $fields{app}{goprocess}{ontology_type}             = 'obo';
  $fields{app}{goprocess}{ontology_table}            = 'goidprocess';
  $fields{app}{goprocessquality}{type}               = 'multiontology';
  $fields{app}{goprocessquality}{label}              = 'GO P Quality';
  $fields{app}{goprocessquality}{tab}                = 'tab2';
  $fields{app}{goprocessquality}{ontology_type}      = 'obo';
  $fields{app}{goprocessquality}{ontology_table}     = 'quality';
  $fields{app}{gofunction}{type}                     = 'multiontology';
  $fields{app}{gofunction}{label}                    = 'GO Function';
  $fields{app}{gofunction}{tab}                      = 'tab2';
  $fields{app}{gofunction}{ontology_type}            = 'obo';
  $fields{app}{gofunction}{ontology_table}           = 'goidfunction';
  $fields{app}{gofunctionquality}{type}              = 'multiontology';
  $fields{app}{gofunctionquality}{label}             = 'GO F Quality';
  $fields{app}{gofunctionquality}{tab}               = 'tab2';
  $fields{app}{gofunctionquality}{ontology_type}     = 'obo';
  $fields{app}{gofunctionquality}{ontology_table}    = 'quality';
  $fields{app}{gocomponent}{type}                    = 'multiontology';
  $fields{app}{gocomponent}{label}                   = 'GO Component';
  $fields{app}{gocomponent}{tab}                     = 'tab2';
  $fields{app}{gocomponent}{ontology_type}           = 'obo';
  $fields{app}{gocomponent}{ontology_table}          = 'goidcomponent';
  $fields{app}{gocomponentquality}{type}             = 'multiontology';
  $fields{app}{gocomponentquality}{label}            = 'GO C Quality';
  $fields{app}{gocomponentquality}{tab}              = 'tab2';
  $fields{app}{gocomponentquality}{ontology_type}    = 'obo';
  $fields{app}{gocomponentquality}{ontology_table}   = 'quality';
#   $fields{app}{entity}{type}                         = 'ontology';
#   $fields{app}{entity}{label}                        = 'Entity';
#   $fields{app}{entity}{tab}                          = 'tab2';
#   $fields{app}{entity}{ontology_type}                = 'obo';
#   $fields{app}{entity}{ontology_table}               = 'entity';
#   $fields{app}{quality}{type}                        = 'ontology';
#   $fields{app}{quality}{label}                       = 'Quality';
#   $fields{app}{quality}{tab}                         = 'tab2';
#   $fields{app}{quality}{ontology_type}               = 'obo';
#   $fields{app}{quality}{ontology_table}              = 'quality';
  $fields{app}{anatomy}{type}                        = 'multiontology';
  $fields{app}{anatomy}{label}                       = 'Anatomy';
  $fields{app}{anatomy}{tab}                         = 'tab3';
  $fields{app}{anatomy}{ontology_type}               = 'obo';
  $fields{app}{anatomy}{ontology_table}              = 'anatomy';
  $fields{app}{anatomyquality}{type}                 = 'multiontology';
  $fields{app}{anatomyquality}{label}                = 'Anatomy Quality';
  $fields{app}{anatomyquality}{tab}                  = 'tab3';
  $fields{app}{anatomyquality}{ontology_type}        = 'obo';
  $fields{app}{anatomyquality}{ontology_table}       = 'quality';
  $fields{app}{lifestage}{type}                      = 'multiontology';
  $fields{app}{lifestage}{label}                     = 'Life Stage';
  $fields{app}{lifestage}{tab}                       = 'tab3';
  $fields{app}{lifestage}{ontology_type}             = 'obo';
  $fields{app}{lifestage}{ontology_table}            = 'lifestage';
  $fields{app}{lifestagequality}{type}               = 'multiontology';
  $fields{app}{lifestagequality}{label}              = 'Life Stage Quality';
  $fields{app}{lifestagequality}{tab}                = 'tab3';
  $fields{app}{lifestagequality}{ontology_type}      = 'obo';
  $fields{app}{lifestagequality}{ontology_table}     = 'quality';
  $fields{app}{molaffected}{type}                    = 'multiontology';
  $fields{app}{molaffected}{label}                   = 'Molecule Affected';
  $fields{app}{molaffected}{tab}                     = 'tab3';
  $fields{app}{molaffected}{ontology_type}           = 'Molecule';
  $fields{app}{molaffectedquality}{type}             = 'multiontology';
  $fields{app}{molaffectedquality}{label}            = 'Mol Aff Quality';
  $fields{app}{molaffectedquality}{tab}              = 'tab3';
  $fields{app}{molaffectedquality}{ontology_type}    = 'obo';
  $fields{app}{molaffectedquality}{ontology_table}   = 'quality';
  $fields{app}{molecule}{type}                       = 'multiontology';
  $fields{app}{molecule}{label}                      = 'Affected By Molecule';
  $fields{app}{molecule}{tab}                        = 'tab3';
  $fields{app}{molecule}{ontology_type}              = 'Molecule';
  $fields{app}{pathogen}{type}                       = 'multiontology';
  $fields{app}{pathogen}{label}                      = 'Affected By Pathogen';
  $fields{app}{pathogen}{tab}                        = 'tab3';
  $fields{app}{pathogen}{ontology_type}              = 'obo';
  $fields{app}{pathogen}{ontology_table}             = 'ncbitaxonid';
  $fields{app}{nature}{type}                         = 'dropdown';
  $fields{app}{nature}{label}                        = 'Allele Nature';
  $fields{app}{nature}{tab}                          = 'tab4';
  $fields{app}{nature}{dropdown_type}                = 'nature';
  $fields{app}{func}{type}                           = 'dropdown';
  $fields{app}{func}{label}                          = 'Functional Change';
  $fields{app}{func}{tab}                            = 'tab4';
  $fields{app}{func}{dropdown_type}                  = 'func';
  $fields{app}{temperature}{type}                    = 'text';
  $fields{app}{temperature}{label}                   = 'Temperature';
  $fields{app}{temperature}{tab}                     = 'tab4';
  $fields{app}{treatment}{type}                      = 'bigtext';
  $fields{app}{treatment}{label}                     = 'Treatment';
  $fields{app}{treatment}{tab}                       = 'tab4';
  $fields{app}{control_isolate}{type}                = 'text';
  $fields{app}{control_isolate}{label}               = 'Control Isolate';
  $fields{app}{control_isolate}{tab}                 = 'tab4';
  $fields{app}{penetrance}{type}                     = 'dropdown';
  $fields{app}{penetrance}{label}                    = 'Penetrance';
  $fields{app}{penetrance}{tab}                      = 'tab4';
  $fields{app}{penetrance}{dropdown_type}            = 'penetrance';
  $fields{app}{percent}{type}                        = 'bigtext';
  $fields{app}{percent}{label}                       = 'Penetrance Remark';
  $fields{app}{percent}{tab}                         = 'tab4';
  $fields{app}{cold_sens}{type}                      = 'toggle_text';
  $fields{app}{cold_sens}{label}                     = 'Cold Sensitive';
  $fields{app}{cold_sens}{tab}                       = 'tab4';
  $fields{app}{cold_sens}{inline}                    = 'cold_degree';
  $fields{app}{cold_degree}{type}                    = 'text';
  $fields{app}{cold_degree}{label}                   = 'Cold Sensitive Degree';
  $fields{app}{cold_degree}{tab}                     = 'tab4';
  $fields{app}{cold_degree}{inline}                  = 'INSIDE_cold_degree';
  $fields{app}{heat_sens}{type}                      = 'toggle_text';
  $fields{app}{heat_sens}{label}                     = 'Heat Sensitive';
  $fields{app}{heat_sens}{tab}                       = 'tab4';
  $fields{app}{heat_sens}{inline}                    = 'heat_degree';
  $fields{app}{heat_degree}{type}                    = 'text';
  $fields{app}{heat_degree}{label}                   = 'Heat Sensitive Degree';
  $fields{app}{heat_degree}{tab}                     = 'tab4';
  $fields{app}{heat_degree}{inline}                  = 'INSIDE_heat_degree';
  $fields{app}{mat_effect}{type}                     = 'dropdown';
  $fields{app}{mat_effect}{label}                    = 'Maternal Effect';
  $fields{app}{mat_effect}{tab}                      = 'tab4';
  $fields{app}{mat_effect}{dropdown_type}            = 'mateffect';
  $fields{app}{pat_effect}{type}                     = 'toggle';
  $fields{app}{pat_effect}{label}                    = 'Paternal Effect';
  $fields{app}{pat_effect}{tab}                      = 'tab4';
  $fields{app}{haplo}{type}                          = 'toggle';
  $fields{app}{haplo}{label}                         = 'Haploinsufficient';
  $fields{app}{haplo}{tab}                           = 'tab4';
  $fields{app}{parentstrain}{type}                   = 'multiontology';
  $fields{app}{parentstrain}{label}                  = 'Parent Strain';
  $fields{app}{parentstrain}{tab}                    = 'tab5';
  $fields{app}{parentstrain}{ontology_type}          = 'obo';
  $fields{app}{parentstrain}{ontology_table}         = 'strain';
  $fields{app}{rescuedby}{type}                      = 'multiontology';
  $fields{app}{rescuedby}{label}                     = 'Rescued By';
  $fields{app}{rescuedby}{tab}                       = 'tab5';
  $fields{app}{rescuedby}{ontology_type}             = 'Transgene';
  $fields{app}{complements}{type}                    = 'multiontology';
  $fields{app}{complements}{label}                   = 'Complements';
  $fields{app}{complements}{tab}                     = 'tab5';
  $fields{app}{complements}{ontology_type}           = 'obo';
  $fields{app}{complements}{ontology_table}          = 'variation';
  $fields{app}{not_complement}{type}                 = 'multiontology';
  $fields{app}{not_complement}{label}                = 'Does Not Complement';
  $fields{app}{not_complement}{tab}                  = 'tab5';
  $fields{app}{not_complement}{ontology_type}        = 'obo';
  $fields{app}{not_complement}{ontology_table}       = 'variation';
  $fields{app}{genotype}{type}                       = 'bigtext';
  $fields{app}{genotype}{label}                      = 'Genotype';
  $fields{app}{genotype}{tab}                        = 'tab5';
  $fields{app}{genotype}{columnWidth}                = '600';
  $fields{app}{flaggeneticintxn}{type}               = 'toggle';
  $fields{app}{flaggeneticintxn}{label}              = 'Flag Genetic Intxn';
  $fields{app}{flaggeneticintxn}{tab}                = 'tab5';
  $fields{app}{intx_desc}{type}                      = 'bigtext';
  $fields{app}{intx_desc}{label}                     = 'Genetic Intx Desc';
  $fields{app}{intx_desc}{tab}                       = 'tab5';
  $fields{app}{intx_desc}{columnWidth}               = '600';
  $fields{app}{flaggenereg}{type}                    = 'toggle';
  $fields{app}{flaggenereg}{label}                   = 'Flag Gene Reg';
  $fields{app}{flaggenereg}{tab}                     = 'tab5';
  $fields{app}{nbp}{type}                            = 'bigtext';
  $fields{app}{nbp}{label}                           = 'NBP';
  $fields{app}{nbp}{tab}                             = 'tab6';
#   $fields{app}{nbp}{disabled}                        = 'disabled';
  $fields{app}{nbp}{noteditable}                     = 'noteditable';
  $fields{app}{filereaddate}{type}                   = 'text';
  $fields{app}{filereaddate}{label}                  = 'NBP / File Date';
  $fields{app}{filereaddate}{tab}                    = 'tab6';
#   $fields{app}{species}{type}                        = 'dropdown';
#   $fields{app}{species}{label}                       = 'Species';
#   $fields{app}{species}{tab}                         = 'tab6';
#   $fields{app}{species}{dropdown_type}               = 'species';
  $fields{app}{laboratory}{type}                     = 'multiontology';
  $fields{app}{laboratory}{label}                    = 'Laboratory Evidence';
  $fields{app}{laboratory}{tab}                      = 'tab6';
  $fields{app}{laboratory}{ontology_type}            = 'obo';
  $fields{app}{laboratory}{ontology_table}           = 'laboratory';
  $fields{app}{legacyinfo}{type}                     = 'bigtext';
  $fields{app}{legacyinfo}{label}                    = 'Legacy Info';
  $fields{app}{legacyinfo}{tab}                      = 'tab6';
  $fields{app}{easescore}{type}                      = 'dropdown';
  $fields{app}{easescore}{label}                     = 'ES';
  $fields{app}{easescore}{tab}                       = 'tab6';
  $fields{app}{easescore}{dropdown_type}             = 'easescore';
  $fields{app}{mmateff}{type}                        = 'dropdown';
  $fields{app}{mmateff}{label}                       = 'ME';
  $fields{app}{mmateff}{tab}                         = 'tab6';
  $fields{app}{mmateff}{dropdown_type}               = 'mmateff';
  $fields{app}{hmateff}{type}                        = 'dropdown';
  $fields{app}{hmateff}{label}                       = 'HME';
  $fields{app}{hmateff}{tab}                         = 'tab6';
  $fields{app}{hmateff}{dropdown_type}               = 'hmateff';
  $fields{app}{communitycurator}{type}               = 'ontology';
  $fields{app}{communitycurator}{label}              = 'Community Curator';
  $fields{app}{communitycurator}{tab}                = 'tab6';
  $fields{app}{communitycurator}{ontology_type}      = 'WBPerson';
  $fields{app}{communitycuratoremail}{type}          = 'text';
  $fields{app}{communitycuratoremail}{label}         = 'Community Curator Email';
  $fields{app}{communitycuratoremail}{tab}           = 'tab6';
  $fields{app}{unregpaper}{type}                     = 'text';
  $fields{app}{unregpaper}{label}                    = 'Unregistered Paper';
  $fields{app}{unregpaper}{tab}                      = 'tab6';
  $fields{app}{unregvariation}{type}                 = 'text';
  $fields{app}{unregvariation}{label}                = 'Unregistered Variation';
  $fields{app}{unregvariation}{tab}                  = 'tab6';
  $fields{app}{unregtransgene}{type}                 = 'text';
  $fields{app}{unregtransgene}{label}                = 'Unregistered Transgene';
  $fields{app}{unregtransgene}{tab}                  = 'tab6';
#   $fields{app}{curation_status}{type}                = 'dropdown';
#   $fields{app}{curation_status}{label}               = 'Curation Status';
#   $fields{app}{curation_status}{tab}                 = 'tab6';
#   $fields{app}{curation_status}{dropdown_type}       = 'curationstatus';
  $fields{app}{nodump}{type}                         = 'toggle';
  $fields{app}{nodump}{label}                        = 'NO DUMP';
  $fields{app}{nodump}{tab}                          = 'tab6';
  $fields{app}{needsreview}{type}                    = 'toggle';
  $fields{app}{needsreview}{label}                   = 'Needs Review';
  $fields{app}{needsreview}{tab}                     = 'tab6';

  $datatypes{app}{constraintSub}                     = \&checkAppConstraints;
  $datatypes{app}{newRowSub}                         = \&newRowApp;
  $datatypes{app}{label}                             = 'phenotype';
  @{ $datatypes{app}{highestPgidTables} }            = qw( strain rearrangement transgene variation curator );
  return( \%fields, \%datatypes);
} # sub initWormAppFields

sub initWormCnsFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{cns} }, "Tie::IxHash";
  $fields{cns}{id}{type}                             = 'text';
  $fields{cns}{id}{label}                            = 'pgid';
  $fields{cns}{id}{tab}                              = 'tab1';
  $fields{cns}{name}{type}                           = 'text';
  $fields{cns}{name}{label}                          = 'Name';
  $fields{cns}{name}{tab}                            = 'tab1';
  $fields{cns}{summary}{type}                        = 'bigtext';
  $fields{cns}{summary}{label}                       = 'Summary';
  $fields{cns}{summary}{tab}                         = 'all';
  $fields{cns}{constructionsummary}{type}            = 'bigtext';
  $fields{cns}{constructionsummary}{label}           = 'Construction Details';
  $fields{cns}{constructionsummary}{tab}             = 'all';
  $fields{cns}{curator}{type}                        = 'dropdown';
  $fields{cns}{curator}{label}                       = 'Curator';
  $fields{cns}{curator}{tab}                         = 'tab1';
  $fields{cns}{curator}{dropdown_type}               = 'curator';
  $fields{cns}{person}{type}                         = 'multiontology';
  $fields{cns}{person}{label}                        = 'Person';
  $fields{cns}{person}{tab}                          = 'tab1';
  $fields{cns}{person}{ontology_type}                = 'WBPerson';
  $fields{cns}{publicname}{type}                     = 'text';
  $fields{cns}{publicname}{label}                    = 'Public Name';
  $fields{cns}{publicname}{tab}                      = 'tab1';
  $fields{cns}{othername}{type}                      = 'text';
  $fields{cns}{othername}{label}                     = 'Other Name';
  $fields{cns}{othername}{tab}                       = 'tab1';
#   $fields{cns}{newtransgene}{type}                   = 'text';
#   $fields{cns}{newtransgene}{label}                  = 'New Transgene';
#   $fields{cns}{newtransgene}{tab}                    = 'tab1';
#   $fields{cns}{merge}{type}                          = 'text';
#   $fields{cns}{merge}{label}                         = 'Merge';
#   $fields{cns}{merge}{tab}                           = 'tab1';
  $fields{cns}{merge}{type}                          = 'ontology';
  $fields{cns}{merge}{label}                         = 'Merge Into';
  $fields{cns}{merge}{tab}                           = 'tab1';
  $fields{cns}{merge}{ontology_type}                 = 'WBConstruct';
  $fields{cns}{nodump}{type}                         = 'toggle';
  $fields{cns}{nodump}{label}                        = 'NO DUMP';
  $fields{cns}{nodump}{tab}                          = 'tab1';
  $fields{cns}{micropublication}{type}               = 'toggle';
  $fields{cns}{micropublication}{label}              = 'Micropublication';
  $fields{cns}{micropublication}{tab}                = 'tab1';
  $fields{cns}{paper}{type}                          = 'multiontology';
  $fields{cns}{paper}{label}                         = 'Paper';
  $fields{cns}{paper}{tab}                           = 'tab1';
  $fields{cns}{paper}{ontology_type}                 = 'WBPaper';
  $fields{cns}{drivenbygene}{type}                   = 'multiontology';
  $fields{cns}{drivenbygene}{label}                  = 'Driven By Gene';
  $fields{cns}{drivenbygene}{tab}                    = 'tab2';
  $fields{cns}{drivenbygene}{ontology_type}          = 'WBGene';
  $fields{cns}{gene}{type}                           = 'multiontology';
  $fields{cns}{gene}{label}                          = 'Gene';
  $fields{cns}{gene}{tab}                            = 'tab2';
  $fields{cns}{gene}{ontology_type}                  = 'WBGene';
#   $fields{cns}{reporter}{type}                       = 'multidropdown';
  $fields{cns}{reporter}{type}                       = 'multiontology';
  $fields{cns}{reporter}{label}                      = 'Reporter';
  $fields{cns}{reporter}{tab}                        = 'tab2';
#   $fields{cns}{reporter}{dropdown_type}              = 'reporterproduct';
  $fields{cns}{reporter}{ontology_type}              = 'obo';
  $fields{cns}{reporter}{ontology_table}             = 'cnsreporter';
  $fields{cns}{otherreporter}{type}                  = 'text';
  $fields{cns}{otherreporter}{label}                 = 'Other Reporter';
  $fields{cns}{otherreporter}{tab}                   = 'tab2';
  $fields{cns}{purificationtag}{type}                = 'multidropdown';
  $fields{cns}{purificationtag}{label}               = 'Purification Tag';
  $fields{cns}{purificationtag}{tab}                 = 'tab2';
  $fields{cns}{purificationtag}{dropdown_type}       = 'purification';
  $fields{cns}{recombinationsite}{type}              = 'multidropdown';
  $fields{cns}{recombinationsite}{label}             = 'Recombination Site';
  $fields{cns}{recombinationsite}{tab}               = 'tab2';
  $fields{cns}{recombinationsite}{dropdown_type}     = 'recombination';
#   $fields{cns}{constructtype}{type}                  = 'dropdown';
  $fields{cns}{constructtype}{type}                  = 'ontology';
  $fields{cns}{constructtype}{label}                 = 'Construct Type';
  $fields{cns}{constructtype}{tab}                   = 'tab2';
#   $fields{cns}{constructtype}{dropdown_type}         = 'cnsconstructtype';
  $fields{cns}{constructtype}{ontology_type}         = 'obo';
  $fields{cns}{constructtype}{ontology_table}        = 'cnsconstructtype';
  $fields{cns}{selectionmarker}{type}                = 'text';
  $fields{cns}{selectionmarker}{label}               = 'Selection Marker';
  $fields{cns}{selectionmarker}{tab}                 = 'tab2';
  $fields{cns}{feature}{type}                        = 'ontology';
  $fields{cns}{feature}{label}                       = 'Feature';
  $fields{cns}{feature}{tab}                         = 'tab2';
  $fields{cns}{feature}{ontology_type}               = 'WBSeqFeat';
#   $fields{cns}{feature}{ontology_type}               = 'obo';
#   $fields{cns}{feature}{ontology_table}              = 'feature';
  $fields{cns}{threeutr}{type}                       = 'multiontology';
  $fields{cns}{threeutr}{label}                      = "3 UTR";
  $fields{cns}{threeutr}{tab}                        = 'tab2';
  $fields{cns}{threeutr}{ontology_type}              = 'WBGene';
  $fields{cns}{fwdprimer}{type}                      = 'bigtext';
  $fields{cns}{fwdprimer}{label}                     = 'FWD Primer';
  $fields{cns}{fwdprimer}{tab}                       = 'tab3';
  $fields{cns}{revprimer}{type}                      = 'bigtext';
  $fields{cns}{revprimer}{label}                     = 'REV Primer';
  $fields{cns}{revprimer}{tab}                       = 'tab3';
  $fields{cns}{dna}{type}                            = 'bigtext';
  $fields{cns}{dna}{label}                           = 'DNA Text';
  $fields{cns}{dna}{tab}                             = 'tab3';
  $fields{cns}{proposedfeature}{type}                = 'text';
  $fields{cns}{proposedfeature}{label}               = 'Proposed Seq Feature';
  $fields{cns}{proposedfeature}{tab}                 = 'tab3';
  $fields{cns}{genewithfeature}{type}                = 'ontology';
  $fields{cns}{genewithfeature}{label}               = 'Feature Gene';
  $fields{cns}{genewithfeature}{tab}                 = 'tab3';
  $fields{cns}{genewithfeature}{ontology_type}       = 'WBGene';
  $fields{cns}{clone}{type}                          = 'multiontology';
  $fields{cns}{clone}{label}                         = 'Clone';
  $fields{cns}{clone}{tab}                           = 'tab3';
  $fields{cns}{clone}{ontology_type}                 = 'obo';
  $fields{cns}{clone}{ontology_table}                = 'clone';
  $fields{cns}{laboratory}{type}                     = 'multiontology';
  $fields{cns}{laboratory}{label}                    = 'Laboratory';
  $fields{cns}{laboratory}{tab}                      = 'tab3';
  $fields{cns}{laboratory}{ontology_type}            = 'obo';
  $fields{cns}{laboratory}{ontology_table}           = 'laboratory';
  $fields{cns}{assoctransgene}{type}                 = 'text';
  $fields{cns}{assoctransgene}{label}                = 'Used for Transgene';
  $fields{cns}{assoctransgene}{tab}                  = 'tab3';
  $fields{cns}{coinjectedwith}{type}                 = 'text';
  $fields{cns}{coinjectedwith}{label}                = 'Coinjected with';
  $fields{cns}{coinjectedwith}{tab}                  = 'tab3';
  $fields{cns}{integrationmethod}{type}              = 'ontology';
  $fields{cns}{integrationmethod}{label}             = 'Integration Method';
  $fields{cns}{integrationmethod}{tab}               = 'tab3';
  $fields{cns}{integrationmethod}{ontology_type}     = 'obo';
  $fields{cns}{integrationmethod}{ontology_table}    = 'integrationmethod';
  $fields{cns}{strain}{type}                         = 'text';
  $fields{cns}{strain}{label}                        = 'Strain';
  $fields{cns}{strain}{tab}                          = 'tab3';
  $fields{cns}{remark}{type}                         = 'bigtext';
  $fields{cns}{remark}{label}                        = 'Remark';
  $fields{cns}{remark}{tab}                          = 'tab3';
  $fields{cns}{humandoid}{type}                      = 'multiontology';
  $fields{cns}{humandoid}{label}                     = 'Disease';
  $fields{cns}{humandoid}{tab}                       = 'tab4';
  $fields{cns}{humandoid}{ontology_type}             = 'obo';
  $fields{cns}{humandoid}{ontology_table}            = 'humando';
  $fields{cns}{diseasepaper}{type}                   = 'multiontology';
  $fields{cns}{diseasepaper}{label}                  = 'Disease Paper';
  $fields{cns}{diseasepaper}{tab}                    = 'tab4';
  $fields{cns}{diseasepaper}{ontology_type}          = 'WBPaper';
  $datatypes{cns}{newRowSub}                         = \&newRowCns;
  $datatypes{cns}{label}                             = 'construct';
  @{ $datatypes{cns}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormCnsFields

sub initWormConFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{con} }, "Tie::IxHash";
  if ($curator_two eq 'two1823') { $fields{con}{id}{placeholder} = ''; }
  $fields{con}{wbgene}{type}                         = 'ontology';
  $fields{con}{wbgene}{label}                        = 'WBGene';
  $fields{con}{wbgene}{tab}                          = 'all';
  $fields{con}{wbgene}{ontology_type}                = 'WBGene';
#   $fields{con}{species}{type}                        = 'dropdown';
  $fields{con}{species}{type}                        = 'ontology';
  $fields{con}{species}{label}                       = 'Species';
  $fields{con}{species}{tab}                         = 'all';
#   $fields{con}{species}{dropdown_type}               = 'species';
  $fields{con}{species}{ontology_type}               = 'obo';
  $fields{con}{species}{ontology_table}              = 'species';
  $fields{con}{curator}{type}                        = 'dropdown';
  $fields{con}{curator}{label}                       = 'Curator';
  $fields{con}{curator}{tab}                         = 'all';
  $fields{con}{curator}{dropdown_type}               = 'curator';
  $fields{con}{curhistory}{type}                     = 'ontology';
  $fields{con}{curhistory}{label}                    = 'Curator History';
  $fields{con}{curhistory}{tab}                      = 'all';
  $fields{con}{curhistory}{ontology_type}            = 'Concurhst';
  $fields{con}{desctype}{type}                       = 'dropdown';
  $fields{con}{desctype}{label}                      = 'Description Type';
  $fields{con}{desctype}{tab}                        = 'all';
  $fields{con}{desctype}{dropdown_type}              = 'condescription';
  $fields{con}{desctext}{type}                       = 'textarea';
  $fields{con}{desctext}{label}                      = 'Description Text';
  $fields{con}{desctext}{tab}                        = 'all';
  $fields{con}{desctext}{cols_size}                  = '90';
  $fields{con}{desctext}{rows_size}                  = '12';
#   $fields{con}{master}{type}                         = 'toggle';
#   $fields{con}{master}{label}                        = 'Master';
#   $fields{con}{master}{tab}                          = 'all';
  $fields{con}{nodump}{type}                         = 'toggle';
  $fields{con}{nodump}{label}                        = 'NO DUMP';
  $fields{con}{nodump}{tab}                          = 'all';
#   $fields{con}{usersubmission}{type}                 = 'toggle';
#   $fields{con}{usersubmission}{label}                = 'User Submission';
#   $fields{con}{usersubmission}{tab}                  = 'all';
#   $fields{con}{needsreview}{type}                    = 'toggle';
#   $fields{con}{needsreview}{label}                   = 'Needs Review';
#   $fields{con}{needsreview}{tab}                     = 'all';
  $fields{con}{paper}{type}                          = 'multiontology';
  $fields{con}{paper}{label}                         = 'Reference';
  $fields{con}{paper}{tab}                           = 'all';
  $fields{con}{paper}{ontology_type}                 = 'WBPaper';
#   $fields{con}{pmidunmapped}{type}                   = 'bigtext';
#   $fields{con}{pmidunmapped}{label}                  = 'Unmapped PMIDs';
#   $fields{con}{pmidunmapped}{tab}                    = 'all';
  $fields{con}{accession}{type}                      = 'text';
  $fields{con}{accession}{label}                     = 'Accession Evidence';
  $fields{con}{accession}{tab}                       = 'all';
  $fields{con}{inferredauto}{type}                   = 'bigtext';
  $fields{con}{inferredauto}{label}                  = 'Inferred Automatically';
  $fields{con}{inferredauto}{tab}                    = 'all';
  $fields{con}{lastupdate}{type}                     = 'text';
  $fields{con}{lastupdate}{label}                    = 'Last Updated';
  $fields{con}{lastupdate}{tab}                      = 'all';
  $fields{con}{comment}{type}                        = 'bigtext';
  $fields{con}{comment}{label}                       = 'Comment';
  $fields{con}{comment}{tab}                         = 'all';
  $fields{con}{comment}{cols_size}                   = '100';
  $fields{con}{id}{type}                             = 'text';
  $fields{con}{id}{label}                            = 'pgid';
  $fields{con}{id}{tab}                              = 'all';
  $fields{con}{person}{type}                         = 'multiontology';
  $fields{con}{person}{label}                        = 'Person';
  $fields{con}{person}{tab}                          = 'all';
  $fields{con}{person}{ontology_type}                = 'WBPerson';
#   $fields{con}{email}{type}                          = 'text';
#   $fields{con}{email}{label}                         = 'email';
#   $fields{con}{email}{tab}                           = 'all';
  $fields{con}{exprtext}{type}                       = 'text';
  $fields{con}{exprtext}{label}                      = 'Expression Pattern';
  $fields{con}{exprtext}{tab}                        = 'all';
  $fields{con}{rnai}{type}                           = 'text';
  $fields{con}{rnai}{label}                          = 'RNAi';
  $fields{con}{rnai}{tab}                            = 'all';
#   $fields{con}{genereg}{type}                        = 'text';		# removed for Kimberly and Ranjana 2013 03 05
#   $fields{con}{genereg}{label}                       = 'Gene Regulation';
#   $fields{con}{genereg}{tab}                         = 'all';
  $fields{con}{microarray}{type}                     = 'text';
  $fields{con}{microarray}{label}                    = 'Microarray';
  $fields{con}{microarray}{tab}                      = 'all';
  $datatypes{con}{newRowSub}                         = \&newRowCon;
  $datatypes{con}{label}                             = 'concise';
  @{ $datatypes{con}{constraintTablesHaveData} }     = qw( wbgene curator desctype desctext lastupdate );
  @{ $datatypes{con}{highestPgidTables} }            = qw( wbgene curator desctype );
  return( \%fields, \%datatypes);
} # sub initWormConFields

sub initWormDisFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{dis} }, "Tie::IxHash";
  if ($curator_two eq 'two1823') { $fields{dis}{id}{placeholder} = ''; }
  $fields{dis}{wbgene}{type}                         = 'ontology';
  $fields{dis}{wbgene}{label}                        = 'WBGene';
  $fields{dis}{wbgene}{tab}                          = 'all';
  $fields{dis}{wbgene}{ontology_type}                = 'WBGene';
  $fields{dis}{curator}{type}                        = 'dropdown';
  $fields{dis}{curator}{label}                       = 'Curator';
  $fields{dis}{curator}{tab}                         = 'all';
  $fields{dis}{curator}{dropdown_type}               = 'curator';
  $fields{dis}{curhistory}{type}                     = 'ontology';
  $fields{dis}{curhistory}{label}                    = 'Curator History';
  $fields{dis}{curhistory}{tab}                      = 'all';
  $fields{dis}{curhistory}{ontology_type}            = 'Discurhst';
  $fields{dis}{humandoid}{type}                      = 'multiontology';
  $fields{dis}{humandoid}{label}                     = 'Experimental Model for';
  $fields{dis}{humandoid}{tab}                       = 'all';
  $fields{dis}{humandoid}{ontology_type}             = 'obo';
  $fields{dis}{humandoid}{ontology_table}            = 'humando';
  $fields{dis}{paperexpmod}{type}                    = 'multiontology';
  $fields{dis}{paperexpmod}{label}                   = 'Paper for Exp Mod';
  $fields{dis}{paperexpmod}{tab}                     = 'all';
  $fields{dis}{paperexpmod}{ontology_type}           = 'WBPaper';
  $fields{dis}{dbexpmod}{type}                       = 'text';
  $fields{dis}{dbexpmod}{label}                      = 'OMIM disease for Exp Mod';
  $fields{dis}{dbexpmod}{tab}                        = 'all';
  $fields{dis}{lastupdateexpmod}{type}               = 'text';
  $fields{dis}{lastupdateexpmod}{label}              = 'Last Updated for Exp Mod';
  $fields{dis}{lastupdateexpmod}{tab}                = 'all';
#   $fields{dis}{species}{type}                        = 'dropdown';
  $fields{dis}{species}{type}                        = 'ontology';
  $fields{dis}{species}{label}                       = 'Species';
  $fields{dis}{species}{tab}                         = 'all';
#   $fields{dis}{species}{dropdown_type}               = 'species';
  $fields{dis}{species}{ontology_type}               = 'obo';
  $fields{dis}{species}{ontology_table}              = 'species';
  $fields{dis}{diseaserelevance}{type}               = 'textarea';
  $fields{dis}{diseaserelevance}{label}              = 'Disease relevance';
  $fields{dis}{diseaserelevance}{tab}                = 'all';
  $fields{dis}{diseaserelevance}{cols_size}          = '60';
  $fields{dis}{diseaserelevance}{rows_size}          = '12';
  $fields{dis}{paperdisrel}{type}                    = 'multiontology';
  $fields{dis}{paperdisrel}{label}                   = 'Paper for Disease Rel';
  $fields{dis}{paperdisrel}{tab}                     = 'all';
  $fields{dis}{paperdisrel}{ontology_type}           = 'WBPaper';
  $fields{dis}{dbdisrel}{type}                       = 'text';
  $fields{dis}{dbdisrel}{label}                      = 'OMIM disease for Disease Rel';
  $fields{dis}{dbdisrel}{tab}                        = 'all';
  $fields{dis}{genedisrel}{type}                     = 'text';
  $fields{dis}{genedisrel}{label}                    = 'OMIM gene for Disease Rel';
  $fields{dis}{genedisrel}{tab}                      = 'all';
  $fields{dis}{lastupdatedisrel}{type}               = 'text';
  $fields{dis}{lastupdatedisrel}{label}              = 'Last Updated for Disease Rel';
  $fields{dis}{lastupdatedisrel}{tab}                = 'all';
  $fields{dis}{comment}{type}                        = 'bigtext';
  $fields{dis}{comment}{label}                       = 'Comment';
  $fields{dis}{comment}{tab}                         = 'all';
  $fields{dis}{comment}{cols_size}                   = '100';
  $fields{dis}{id}{type}                             = 'text';
  $fields{dis}{id}{label}                            = 'pgid';
  $fields{dis}{id}{tab}                              = 'all';
  $datatypes{dis}{newRowSub}                         = \&newRowDis;
  $datatypes{dis}{label}                             = 'disease';
  @{ $datatypes{dis}{constraintTablesHaveData} }     = qw( wbgene curator humandoid paperexpmod species diseaserelevance paperdisrel lastupdatedisrel );
  @{ $datatypes{dis}{highestPgidTables} }            = qw( wbgene curator );
  return( \%fields, \%datatypes);
} # sub initWormDisFields

sub initWormDitFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{dit} }, "Tie::IxHash";
  if ($curator_two eq 'two1823') { $fields{dit}{id}{placeholder} = ''; }
  $fields{dit}{doterm}{type}                         = 'ontology';
  $fields{dit}{doterm}{label}                        = 'DO Term';
  $fields{dit}{doterm}{tab}                          = 'all';
  $fields{dit}{doterm}{ontology_type}                = 'obo';
  $fields{dit}{doterm}{ontology_table}               = 'humando';
  $fields{dit}{curator}{type}                        = 'dropdown';
  $fields{dit}{curator}{label}                       = 'Curator';
  $fields{dit}{curator}{tab}                         = 'all';
  $fields{dit}{curator}{dropdown_type}               = 'curator';
  $fields{dit}{curhistory}{type}                     = 'ontology';
  $fields{dit}{curhistory}{label}                    = 'Curator History';
  $fields{dit}{curhistory}{tab}                      = 'all';
  $fields{dit}{curhistory}{ontology_type}            = 'Ditcurhst';
#   $fields{dit}{species}{type}                        = 'dropdown';
  $fields{dit}{species}{type}                        = 'ontology';
  $fields{dit}{species}{label}                       = 'Species';
  $fields{dit}{species}{tab}                         = 'all';
#   $fields{dit}{species}{dropdown_type}               = 'species';
  $fields{dit}{species}{ontology_type}               = 'obo';
  $fields{dit}{species}{ontology_table}              = 'species';
  $fields{dit}{wormmodeldesc}{type}                  = 'textarea';
  $fields{dit}{wormmodeldesc}{label}                 = 'Worm Model Description';
  $fields{dit}{wormmodeldesc}{tab}                   = 'all';
  $fields{dit}{wormmodeldesc}{cols_size}             = '60';
  $fields{dit}{wormmodeldesc}{rows_size}             = '12';
  $fields{dit}{paper}{type}                          = 'multiontology';
  $fields{dit}{paper}{label}                         = 'Paper';
  $fields{dit}{paper}{tab}                           = 'all';
  $fields{dit}{paper}{ontology_type}                 = 'WBPaper';
  $fields{dit}{lastupdate}{type}                     = 'text';
  $fields{dit}{lastupdate}{label}                    = 'Last Updated';
  $fields{dit}{lastupdate}{tab}                      = 'all';
  $fields{dit}{comment}{type}                        = 'bigtext';
  $fields{dit}{comment}{label}                       = 'Comment';
  $fields{dit}{comment}{tab}                         = 'all';
  $fields{dit}{comment}{cols_size}                   = '100';
  $fields{dit}{id}{type}                             = 'text';
  $fields{dit}{id}{label}                            = 'pgid';
  $fields{dit}{id}{tab}                              = 'all';
  $datatypes{dit}{newRowSub}                         = \&newRowDit;
  $datatypes{dit}{label}                             = 'disease term';
  @{ $datatypes{dit}{constraintTablesHaveData} }     = qw( doterm curator species wormmodeldesc paper lastupdate );
  @{ $datatypes{dit}{highestPgidTables} }            = qw( doterm curator );
  return( \%fields, \%datatypes);
} # sub initWormDitFields

sub initWormExpFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{exp} }, "Tie::IxHash";
  $fields{exp}{id}{type}                             = 'text';
  $fields{exp}{id}{label}                            = 'pgid';
  $fields{exp}{id}{tab}                              = 'tab1';
  $fields{exp}{name}{type}                           = 'text';
  $fields{exp}{name}{label}                          = 'Expr Pattern';
  $fields{exp}{name}{tab}                            = 'tab1';
  $fields{exp}{paper}{type}                          = 'multiontology';
  $fields{exp}{paper}{label}                         = 'Reference';
  $fields{exp}{paper}{tab}                           = 'tab1';
  $fields{exp}{paper}{ontology_type}                 = 'WBPaper';
  $fields{exp}{gene}{type}                           = 'multiontology';
  $fields{exp}{gene}{label}                          = 'Gene';
  $fields{exp}{gene}{tab}                            = 'tab1';
  $fields{exp}{gene}{ontology_type}                  = 'WBGene';
  $fields{exp}{endogenous}{type}                     = 'toggle';
  $fields{exp}{endogenous}{label}                    = 'Endogenous';
  $fields{exp}{endogenous}{tab}                      = 'tab1';
  $fields{exp}{relanatomy}{type}                     = 'dropdown';
  $fields{exp}{relanatomy}{label}                    = 'Rel Anatomy';
  $fields{exp}{relanatomy}{tab}                      = 'tab1';
  $fields{exp}{relanatomy}{dropdown_type}            = 'relanatomy';
  $fields{exp}{anatomy}{type}                        = 'multiontology';
  $fields{exp}{anatomy}{label}                       = 'Anatomy';
  $fields{exp}{anatomy}{tab}                         = 'tab1';
  $fields{exp}{anatomy}{ontology_type}               = 'obo';
  $fields{exp}{anatomy}{ontology_table}              = 'anatomy';
  $fields{exp}{qualifier}{type}                      = 'dropdown';
  $fields{exp}{qualifier}{label}                     = 'Qualifier';
  $fields{exp}{qualifier}{tab}                       = 'tab1';
  $fields{exp}{qualifier}{dropdown_type}             = 'exprqualifier';
  $fields{exp}{qualifiertext}{type}                  = 'bigtext';
  $fields{exp}{qualifiertext}{label}                 = 'Qualifier Text';
  $fields{exp}{qualifiertext}{tab}                   = 'tab1';
  $fields{exp}{qualifierls}{type}                    = 'multiontology';
  $fields{exp}{qualifierls}{label}                   = 'Qualifier LS';
  $fields{exp}{qualifierls}{tab}                     = 'tab1';
  $fields{exp}{qualifierls}{ontology_type}           = 'obo';
  $fields{exp}{qualifierls}{ontology_table}          = 'lifestage';
  $fields{exp}{goid}{type}                           = 'multiontology';
  $fields{exp}{goid}{label}                          = 'GO Term';
  $fields{exp}{goid}{tab}                            = 'tab1';
  $fields{exp}{goid}{ontology_type}                  = 'obo';
  $fields{exp}{goid}{ontology_table}                 = 'goid';
  $fields{exp}{granatomy}{type}                      = 'multiontology';
  $fields{exp}{granatomy}{label}                     = 'GR Anatomy';
  $fields{exp}{granatomy}{tab}                       = 'tab1';
  $fields{exp}{granatomy}{ontology_type}             = 'obo';
  $fields{exp}{granatomy}{ontology_table}            = 'anatomy';
  $fields{exp}{grlifestage}{type}                    = 'multiontology';
  $fields{exp}{grlifestage}{label}                   = 'GR LS';
  $fields{exp}{grlifestage}{tab}                     = 'tab1';
  $fields{exp}{grlifestage}{ontology_type}           = 'obo';
  $fields{exp}{grlifestage}{ontology_table}          = 'lifestage';
  $fields{exp}{relcellcycle}{type}                   = 'dropdown';
  $fields{exp}{relcellcycle}{label}                  = 'Rel Cell Cycle';
  $fields{exp}{relcellcycle}{tab}                    = 'tab1';
  $fields{exp}{relcellcycle}{dropdown_type}          = 'relcellcycle';
  $fields{exp}{grcellcycle}{type}                    = 'multiontology';
  $fields{exp}{grcellcycle}{label}                   = 'GR Cell Cycle';
  $fields{exp}{grcellcycle}{tab}                     = 'tab1';
  $fields{exp}{grcellcycle}{ontology_type}           = 'obo';
  $fields{exp}{grcellcycle}{ontology_table}          = 'goid';
  $fields{exp}{subcellloc}{type}                     = 'bigtext';
  $fields{exp}{subcellloc}{label}                    = 'Subcellular Localization';
  $fields{exp}{subcellloc}{tab}                      = 'tab1';
  $fields{exp}{rellifestage}{type}                   = 'dropdown';
  $fields{exp}{rellifestage}{label}                  = 'Rel Life Stage';
  $fields{exp}{rellifestage}{tab}                    = 'tab1';
  $fields{exp}{rellifestage}{dropdown_type}          = 'rellifestage';
  $fields{exp}{lifestage}{type}                      = 'multiontology';
  $fields{exp}{lifestage}{label}                     = 'Life Stage';
  $fields{exp}{lifestage}{tab}                       = 'tab1';
  $fields{exp}{lifestage}{ontology_type}             = 'obo';
  $fields{exp}{lifestage}{ontology_table}            = 'lifestage';
#   $fields{exp}{species}{type}                        = 'dropdown';
  $fields{exp}{species}{type}                        = 'ontology';
  $fields{exp}{species}{label}                       = 'Species';
  $fields{exp}{species}{tab}                         = 'tab1';
#   $fields{exp}{species}{dropdown_type}               = 'species';
  $fields{exp}{species}{ontology_type}               = 'obo';
  $fields{exp}{species}{ontology_table}              = 'species';
  $fields{exp}{exprtype}{type}                       = 'multidropdown';
  $fields{exp}{exprtype}{label}                      = 'Type';
  $fields{exp}{exprtype}{tab}                        = 'tab2';
  $fields{exp}{exprtype}{dropdown_type}              = 'exprtype';
  $fields{exp}{antibodytext}{type}                   = 'bigtext';
  $fields{exp}{antibodytext}{label}                  = 'Antibody_Text';
  $fields{exp}{antibodytext}{tab}                    = 'tab2';
  $fields{exp}{reportergene}{type}                   = 'bigtext';
  $fields{exp}{reportergene}{label}                  = 'Reporter Gene';
  $fields{exp}{reportergene}{tab}                    = 'tab2';
  $fields{exp}{insitu}{type}                         = 'bigtext';
  $fields{exp}{insitu}{label}                        = 'In Situ';
  $fields{exp}{insitu}{tab}                          = 'tab2';
  $fields{exp}{rtpcr}{type}                          = 'bigtext';
  $fields{exp}{rtpcr}{label}                         = 'RT PCR';
  $fields{exp}{rtpcr}{tab}                           = 'tab2';
  $fields{exp}{northern}{type}                       = 'bigtext';
  $fields{exp}{northern}{label}                      = 'Northern';
  $fields{exp}{northern}{tab}                        = 'tab2';
  $fields{exp}{western}{type}                        = 'bigtext';
  $fields{exp}{western}{label}                       = 'Western';
  $fields{exp}{western}{tab}                         = 'tab2';
  $fields{exp}{pictureflag}{type}                    = 'toggle';
  $fields{exp}{pictureflag}{label}                   = 'Picture_Flag';
  $fields{exp}{pictureflag}{tab}                     = 'tab2';
  $fields{exp}{antibody}{type}                       = 'multiontology';
  $fields{exp}{antibody}{label}                      = 'Antibody_Info';
  $fields{exp}{antibody}{tab}                        = 'tab2';
  $fields{exp}{antibody}{ontology_type}              = 'Antibody';
  $fields{exp}{antibodyflag}{type}                   = 'toggle';
  $fields{exp}{antibodyflag}{label}                  = 'Antibody_Flag';
  $fields{exp}{antibodyflag}{tab}                    = 'tab2';
  $fields{exp}{pattern}{type}                        = 'bigtext';
  $fields{exp}{pattern}{label}                       = 'Pattern';
  $fields{exp}{pattern}{tab}                         = 'tab2';
  $fields{exp}{remark}{type}                         = 'bigtext';
  $fields{exp}{remark}{label}                        = 'Remark';
  $fields{exp}{remark}{tab}                          = 'tab2';
  $fields{exp}{transgene}{type}                      = 'multiontology';
  $fields{exp}{transgene}{label}                     = 'Transgene';
  $fields{exp}{transgene}{tab}                       = 'tab2';
  $fields{exp}{construct}{type}                      = 'multiontology';
  $fields{exp}{construct}{label}                     = 'Construct';
  $fields{exp}{construct}{tab}                       = 'tab2';
  $fields{exp}{construct}{ontology_type}             = 'WBConstruct';
  $fields{exp}{transgene}{ontology_type}             = 'Transgene';
  $fields{exp}{transgeneflag}{type}                  = 'toggle';
  $fields{exp}{transgeneflag}{label}                 = 'Transgene_Flag';
  $fields{exp}{transgeneflag}{tab}                   = 'tab2';
  $fields{exp}{seqfeature}{type}                     = 'multiontology';
  $fields{exp}{seqfeature}{label}                    = 'Sequence Feature';
  $fields{exp}{seqfeature}{tab}                      = 'tab2';
  $fields{exp}{seqfeature}{ontology_type}            = 'WBSeqFeat';
#   $fields{exp}{seqfeature}{ontology_type}            = 'obo';		# 2014 10 01 using sqf_ tables instead of obo_*_feature tables
#   $fields{exp}{seqfeature}{ontology_table}           = 'feature';
  $fields{exp}{curator}{type}                        = 'dropdown';
  $fields{exp}{curator}{label}                       = 'Curator';
  $fields{exp}{curator}{tab}                         = 'tab2';
  $fields{exp}{curator}{dropdown_type}               = 'curator';
  $fields{exp}{nodump}{type}                         = 'toggle';
  $fields{exp}{nodump}{label}                        = 'NO DUMP';
  $fields{exp}{nodump}{tab}                          = 'tab2';
  $fields{exp}{protein}{type}                        = 'text';
  $fields{exp}{protein}{label}                       = 'Protein Description';
  $fields{exp}{protein}{tab}                         = 'tab3';
  $fields{exp}{clone}{type}                          = 'multiontology';
  $fields{exp}{clone}{label}                         = 'Clone';
  $fields{exp}{clone}{tab}                           = 'tab3';
  $fields{exp}{clone}{ontology_type}                 = 'obo';
  $fields{exp}{clone}{ontology_table}                = 'clone';
  $fields{exp}{strain}{type}                         = 'multiontology';
  $fields{exp}{strain}{label}                        = 'Strain';
  $fields{exp}{strain}{tab}                          = 'tab3';
  $fields{exp}{strain}{ontology_type}                = 'obo';
  $fields{exp}{strain}{ontology_table}               = 'strain';
  $fields{exp}{sequence}{type}                       = 'text';
  $fields{exp}{sequence}{label}                      = 'Sequence';
  $fields{exp}{sequence}{tab}                        = 'tab3';
  $fields{exp}{movieurl}{type}                       = 'text';
  $fields{exp}{movieurl}{label}                      = 'Movie URL';
  $fields{exp}{movieurl}{tab}                        = 'tab3';
  $fields{exp}{laboratory}{type}                     = 'multiontology';
  $fields{exp}{laboratory}{label}                    = 'Laboratory';
  $fields{exp}{laboratory}{tab}                      = 'tab3';
  $fields{exp}{laboratory}{ontology_type}            = 'obo';
  $fields{exp}{laboratory}{ontology_table}           = 'laboratory';
  $fields{exp}{variation}{type}                      = 'multiontology';
  $fields{exp}{variation}{label}                     = 'Variation';
  $fields{exp}{variation}{tab}                       = 'tab3';
  $fields{exp}{variation}{ontology_type}             = 'obo';
  $fields{exp}{variation}{ontology_table}            = 'variation';
#   $fields{exp}{author}{type}                         = 'text';
#   $fields{exp}{author}{label}                        = 'Author';
#   $fields{exp}{author}{tab}                          = 'tab3';
#   $fields{exp}{date}{type}                           = 'text';
#   $fields{exp}{date}{label}                          = 'Date';
#   $fields{exp}{date}{tab}                            = 'tab3';
#   $fields{exp}{curatedby}{type}                      = 'text';
#   $fields{exp}{curatedby}{label}                     = 'Curated by';
#   $fields{exp}{curatedby}{tab}                       = 'tab3';
  $fields{exp}{contact}{type}                        = 'ontology';
  $fields{exp}{contact}{label}                       = 'Contact';
  $fields{exp}{contact}{tab}                         = 'tab4';
  $fields{exp}{contact}{ontology_type}               = 'WBPerson';
  $fields{exp}{email}{type}                          = 'text';
  $fields{exp}{email}{label}                         = 'Email';
  $fields{exp}{email}{tab}                           = 'tab4';
  $fields{exp}{coaut}{type}                          = 'multiontology';
  $fields{exp}{coaut}{label}                         = 'Co-authors';
  $fields{exp}{coaut}{tab}                           = 'tab4';
  $fields{exp}{coaut}{ontology_type}                 = 'WBPerson';
  $fields{exp}{micropublication}{type}               = 'toggle';
  $fields{exp}{micropublication}{label}              = 'Micropublication';
  $fields{exp}{micropublication}{tab}                = 'tab4';
  $fields{exp}{funding}{type}                        = 'bigtext';
  $fields{exp}{funding}{label}                       = 'Funding';
  $fields{exp}{funding}{tab}                         = 'tab4';
  $datatypes{exp}{newRowSub}                         = \&newRowExp;
  $datatypes{exp}{label}                             = 'exprpat';
  @{ $datatypes{exp}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormExpFields

sub initWormGclFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{gcl} }, "Tie::IxHash";
  $fields{gcl}{id}{type}                             = 'text';
  $fields{gcl}{id}{label}                            = 'pgid';
  $fields{gcl}{id}{tab}                              = 'all';
  $fields{gcl}{curator}{type}                        = 'dropdown';
  $fields{gcl}{curator}{label}                       = 'Curator';
  $fields{gcl}{curator}{tab}                         = 'all';
  $fields{gcl}{curator}{dropdown_type}               = 'curator';
  $fields{gcl}{name}{type}                           = 'ontology';
  $fields{gcl}{name}{label}                          = 'Gene_class';
  $fields{gcl}{name}{tab}                            = 'all';
  $fields{gcl}{name}{ontology_type}                  = 'obo';
  $fields{gcl}{name}{ontology_table}                 = 'geneclass';
  $fields{gcl}{summary}{type}                        = 'bigtext';
  $fields{gcl}{summary}{label}                       = 'Summary';
  $fields{gcl}{summary}{tab}                         = 'all';
  $fields{gcl}{paper}{type}                          = 'multiontology';
  $fields{gcl}{paper}{label}                         = 'WBPaper';
  $fields{gcl}{paper}{tab}                           = 'all';
  $fields{gcl}{paper}{ontology_type}                 = 'WBPaper';
  $fields{gcl}{othersource}{type}                    = 'bigtext';
  $fields{gcl}{othersource}{label}                   = 'Other Source';
  $fields{gcl}{othersource}{tab}                     = 'all';
  $fields{gcl}{sumstatus}{type}                      = 'dropdown';
  $fields{gcl}{sumstatus}{label}                     = 'Summary status';
  $fields{gcl}{sumstatus}{tab}                       = 'all';
  $fields{gcl}{sumstatus}{dropdown_type}             = 'gclstatus';
  $fields{gcl}{type}{type}                           = 'dropdown';
  $fields{gcl}{type}{label}                          = 'Type of gene_class';
  $fields{gcl}{type}{tab}                            = 'all';
  $fields{gcl}{type}{dropdown_type}                  = 'gcltype';
  @{ $datatypes{gcl}{highestPgidTables} }            = qw( name curator );
  $datatypes{gcl}{newRowSub}                         = \&newRowGcl;
  $datatypes{gcl}{label}                             = 'gene class';
  return( \%fields, \%datatypes);
} # sub initWormGclFields


sub initWormGopFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{gop} }, "Tie::IxHash";
  if ($curator_two eq 'two1823') { $fields{gop}{id}{placeholder} = ''; }
  $fields{gop}{paper}{type}                          = 'ontology';
  $fields{gop}{paper}{label}                         = 'Paper';
  $fields{gop}{paper}{tab}                           = 'all';
  $fields{gop}{paper}{ontology_type}                 = 'WBPaper';
  $fields{gop}{wbgene}{type}                         = 'ontology';
  $fields{gop}{wbgene}{label}                        = 'WBGene';
  $fields{gop}{wbgene}{tab}                          = 'all';
  $fields{gop}{wbgene}{ontology_type}                = 'WBGene';
  $fields{gop}{project}{type}                        = 'multidropdown';
  $fields{gop}{project}{label}                       = 'Project';
  $fields{gop}{project}{tab}                         = 'all';
  $fields{gop}{project}{dropdown_type}               = 'goproject';
  $fields{gop}{curator}{type}                        = 'dropdown';
  $fields{gop}{curator}{label}                       = 'Curator';
  $fields{gop}{curator}{tab}                         = 'all';
  $fields{gop}{curator}{dropdown_type}               = 'curator';
  $fields{gop}{goontology}{type}                     = 'dropdown';
  $fields{gop}{goontology}{label}                    = 'GO';
  $fields{gop}{goontology}{tab}                      = 'all';
  $fields{gop}{goontology}{dropdown_type}            = 'goontology';
  $fields{gop}{goontology}{columnWidth}              = '20';
  $fields{gop}{goid}{type}                           = 'ontology';
  $fields{gop}{goid}{label}                          = 'GO Term';
  $fields{gop}{goid}{tab}                            = 'all';
  $fields{gop}{goid}{ontology_type}                  = 'obo';
  $fields{gop}{goid}{ontology_table}                 = 'goid';
  $fields{gop}{goinference}{type}                    = 'dropdown';
  $fields{gop}{goinference}{label}                   = 'EC';
  $fields{gop}{goinference}{tab}                     = 'all';
  $fields{gop}{goinference}{dropdown_type}           = 'goinference';
  $fields{gop}{accession}{type}                      = 'multidropdown';
  $fields{gop}{accession}{label}                     = 'Accession Number';
  $fields{gop}{accession}{tab}                       = 'all';
  $fields{gop}{accession}{dropdown_type}             = 'goaccession';
  $fields{gop}{with_wbgene}{type}                    = 'multiontology';
  $fields{gop}{with_wbgene}{label}                   = 'With WBGene';
  $fields{gop}{with_wbgene}{tab}                     = 'all';
  $fields{gop}{with_wbgene}{ontology_type}           = 'WBGene';
  $fields{gop}{with_wbvariation}{type}               = 'multiontology';
  $fields{gop}{with_wbvariation}{label}              = 'With WBVariation';
  $fields{gop}{with_wbvariation}{tab}                = 'all';
  $fields{gop}{with_wbvariation}{ontology_type}      = 'obo';
  $fields{gop}{with_wbvariation}{ontology_table}     = 'variation';
  $fields{gop}{with}{type}                           = 'text';
  $fields{gop}{with}{label}                          = 'With Other';
  $fields{gop}{with}{tab}                            = 'all';
  $fields{gop}{with_rnai}{type}                      = 'multiontology';
  $fields{gop}{with_rnai}{label}                     = 'With RNAi';
  $fields{gop}{with_rnai}{tab}                       = 'all';
  $fields{gop}{with_rnai}{ontology_type}             = 'WBRnai';
  $fields{gop}{with_phenotype}{type}                 = 'multiontology';
  $fields{gop}{with_phenotype}{label}                = 'With Phenotype';
  $fields{gop}{with_phenotype}{tab}                  = 'all';
  $fields{gop}{with_phenotype}{ontology_type}        = 'obo';
  $fields{gop}{with_phenotype}{ontology_table}       = 'phenotype';
  $fields{gop}{qualifier}{type}                      = 'dropdown';
  $fields{gop}{qualifier}{label}                     = 'Qualifier';
  $fields{gop}{qualifier}{tab}                       = 'all';
  $fields{gop}{qualifier}{dropdown_type}             = 'goqualifier';
  $fields{gop}{xrefto}{type}                         = 'bigtext';
  $fields{gop}{xrefto}{label}                        = 'Xref to';
  $fields{gop}{xrefto}{tab}                          = 'all';
  $fields{gop}{dbtype}{type}                         = 'dropdown';
  $fields{gop}{dbtype}{label}                        = 'Object';
  $fields{gop}{dbtype}{tab}                          = 'all';
  $fields{gop}{dbtype}{dropdown_type}                = 'godbtype';
  $fields{gop}{protein}{type}                        = 'text';
  $fields{gop}{protein}{label}                       = 'Gene Product';
  $fields{gop}{protein}{tab}                         = 'all';
  $fields{gop}{comment}{type}                        = 'text';
  $fields{gop}{comment}{label}                       = 'Comment';
  $fields{gop}{comment}{tab}                         = 'all';
  $fields{gop}{lastupdate}{type}                     = 'text';
  $fields{gop}{lastupdate}{label}                    = 'Last Updated';
  $fields{gop}{lastupdate}{tab}                      = 'all';
  $fields{gop}{falsepositive}{type}                  = 'toggle';
  $fields{gop}{falsepositive}{label}                 = 'False Positive';
  $fields{gop}{falsepositive}{tab}                   = 'all';
  $fields{gop}{id}{type}                             = 'text';
  $fields{gop}{id}{label}                            = 'pgid';
  $fields{gop}{id}{tab}                              = 'all';
  if ($curator_two eq 'two1823') { $fields{gop}{id}{input_size} = '70'; }
  @{ $datatypes{gop}{constraintTablesHaveData} }     = qw( paper wbgene curator goid goontology goinference dbtype lastupdate );
  @{ $datatypes{gop}{highestPgidTables} }            = qw( wbgene curator );
  $datatypes{gop}{newRowSub}                         = \&newRowGop;
  $datatypes{gop}{label}                             = 'go';
  return( \%fields, \%datatypes);
} # sub initWormGopFields

sub initWormGrgFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{grg} }, "Tie::IxHash";
  $fields{grg}{id}{type}                             = 'text';
  $fields{grg}{id}{label}                            = 'pgid';
  $fields{grg}{id}{tab}                              = 'tab1';
  $fields{grg}{curator}{type}                        = 'dropdown';
  $fields{grg}{curator}{label}                       = 'Curator';
  $fields{grg}{curator}{tab}                         = 'tab1';
  $fields{grg}{curator}{dropdown_type}               = 'curator';
  $fields{grg}{paper}{type}                          = 'ontology';
  $fields{grg}{paper}{label}                         = 'Reference';
  $fields{grg}{paper}{tab}                           = 'tab1';
  $fields{grg}{paper}{ontology_type}                 = 'WBPaper';
  $fields{grg}{intid}{type}                          = 'ontology';
  $fields{grg}{intid}{label}                         = 'Interaction ID';
  $fields{grg}{intid}{tab}                           = 'tab1';
  $fields{grg}{intid}{ontology_type}                 = 'WBInteraction';
  $fields{grg}{name}{type}                           = 'text';
  $fields{grg}{name}{label}                          = 'Name';
  $fields{grg}{name}{tab}                            = 'tab1';
  $fields{grg}{summary}{type}                        = 'bigtext';
  $fields{grg}{summary}{label}                       = 'Summary';
  $fields{grg}{summary}{tab}                         = 'tab1';
  $fields{grg}{insitu}{type}                         = 'toggle_text';
  $fields{grg}{insitu}{label}                        = 'In Situ';
  $fields{grg}{insitu}{tab}                          = 'tab1';
  $fields{grg}{insitu}{inline}                       = 'insitu_text';
  $fields{grg}{insitu_text}{type}                    = 'text';
  $fields{grg}{insitu_text}{label}                   = 'IS Text';
  $fields{grg}{insitu_text}{tab}                     = 'tab1';
  $fields{grg}{insitu_text}{inline}                  = 'INSIDE_insitu_text';
  $fields{grg}{northern}{type}                       = 'toggle_text';
  $fields{grg}{northern}{label}                      = 'Northern';
  $fields{grg}{northern}{tab}                        = 'tab1';
  $fields{grg}{northern}{inline}                     = 'northern_text';
  $fields{grg}{northern_text}{type}                  = 'text';
  $fields{grg}{northern_text}{label}                 = 'N Text';
  $fields{grg}{northern_text}{tab}                   = 'tab1';
  $fields{grg}{northern_text}{inline}                = 'INSIDE_northern_text';
  $fields{grg}{western}{type}                        = 'toggle_text';
  $fields{grg}{western}{label}                       = 'Western';
  $fields{grg}{western}{tab}                         = 'tab1';
  $fields{grg}{western}{inline}                      = 'western_text';
  $fields{grg}{western_text}{type}                   = 'text';
  $fields{grg}{western_text}{label}                  = 'W Text';
  $fields{grg}{western_text}{tab}                    = 'tab1';
  $fields{grg}{western_text}{inline}                 = 'INSIDE_western_text';
  $fields{grg}{rtpcr}{type}                          = 'toggle_text';
  $fields{grg}{rtpcr}{label}                         = 'RT PCR';
  $fields{grg}{rtpcr}{tab}                           = 'tab1';
  $fields{grg}{rtpcr}{inline}                        = 'rtpcr_text';
  $fields{grg}{rtpcr_text}{type}                     = 'text';
  $fields{grg}{rtpcr_text}{label}                    = 'RP Text';
  $fields{grg}{rtpcr_text}{tab}                      = 'tab1';
  $fields{grg}{rtpcr_text}{inline}                   = 'INSIDE_rtpcr_text';
  $fields{grg}{othermethod}{type}                    = 'toggle_text';
  $fields{grg}{othermethod}{label}                   = 'Other Method';
  $fields{grg}{othermethod}{tab}                     = 'tab1';
  $fields{grg}{othermethod}{inline}                  = 'othermethod_text';
  $fields{grg}{othermethod_text}{type}               = 'text';
  $fields{grg}{othermethod_text}{label}              = 'OM Text';
  $fields{grg}{othermethod_text}{tab}                = 'tab1';
  $fields{grg}{othermethod_text}{inline}             = 'INSIDE_othermethod_text';
#   $fields{grg}{rnai}{type}                           = 'text';
#   $fields{grg}{rnai}{label}                          = 'RNAi';
#   $fields{grg}{rnai}{tab}                            = 'tab1';
  $fields{grg}{rnai}{type}                           = 'multiontology';
  $fields{grg}{rnai}{label}                          = 'RNAi';
  $fields{grg}{rnai}{tab}                            = 'tab1';
  $fields{grg}{rnai}{ontology_type}                  = 'WBRnai';
  $fields{grg}{fromrnai}{type}                       = 'toggle';
  $fields{grg}{fromrnai}{label}                      = 'From RNAi';
  $fields{grg}{fromrnai}{tab}                        = 'tab1';
  $fields{grg}{nodump}{type}                         = 'toggle';
  $fields{grg}{nodump}{label}                        = 'NO DUMP';
  $fields{grg}{nodump}{tab}                          = 'tab1';

  $fields{grg}{antibody}{type}                       = 'multiontology';
  $fields{grg}{antibody}{label}                      = 'Antibody Info';
  $fields{grg}{antibody}{tab}                        = 'tab2';
  $fields{grg}{antibody}{ontology_type}              = 'Antibody';
  $fields{grg}{antibodyremark}{type}                 = 'text';
  $fields{grg}{antibodyremark}{label}                = 'Antibody Remark';
  $fields{grg}{antibodyremark}{tab}                  = 'tab2';
  $fields{grg}{reportergene}{type}                   = 'text';
  $fields{grg}{reportergene}{label}                  = 'Reporter Gene';
  $fields{grg}{reportergene}{tab}                    = 'tab2';
  $fields{grg}{transgene}{type}                      = 'multiontology';
  $fields{grg}{transgene}{label}                     = 'Transgene';
  $fields{grg}{transgene}{tab}                       = 'tab2';
  $fields{grg}{transgene}{ontology_type}             = 'Transgene';
  $fields{grg}{construct}{type}                      = 'multiontology';
  $fields{grg}{construct}{label}                     = 'Construct';
  $fields{grg}{construct}{tab}                       = 'tab2';
  $fields{grg}{construct}{ontology_type}             = 'WBConstruct';
  $fields{grg}{transregulatorallele}{type}           = 'multiontology';
  $fields{grg}{transregulatorallele}{label}          = 'Trans Regulator Allele';
  $fields{grg}{transregulatorallele}{tab}            = 'tab2';
  $fields{grg}{transregulatorallele}{ontology_type}  = 'obo';
  $fields{grg}{transregulatorallele}{ontology_table} = 'variation';
  $fields{grg}{cisregulatorallele}{type}             = 'multiontology';
  $fields{grg}{cisregulatorallele}{label}            = 'Cis Regulator Allele';
  $fields{grg}{cisregulatorallele}{tab}              = 'tab2';
  $fields{grg}{cisregulatorallele}{ontology_type}    = 'obo';
  $fields{grg}{cisregulatorallele}{ontology_table}   = 'variation';
  $fields{grg}{rearrangement}{type}                  = 'multiontology';
  $fields{grg}{rearrangement}{label}                 = 'Rearrangement';
  $fields{grg}{rearrangement}{tab}                   = 'tab2';
  $fields{grg}{rearrangement}{ontology_type}         = 'obo';
  $fields{grg}{rearrangement}{ontology_table}        = 'rearrangement';
  $fields{grg}{exprpattern}{type}                    = 'multiontology';
  $fields{grg}{exprpattern}{label}                   = 'Expression Pattern';
  $fields{grg}{exprpattern}{tab}                     = 'tab2';
  $fields{grg}{exprpattern}{ontology_type}           = 'Expr';
#   $fields{grg}{exprpattern}{ontology_type}           = 'obo';
#   $fields{grg}{exprpattern}{ontology_table}          = 'exprpattern';

  $fields{grg}{type}{type}                           = 'multidropdown';
  $fields{grg}{type}{label}                          = 'Type';
  $fields{grg}{type}{tab}                            = 'tab3';
  $fields{grg}{type}{dropdown_type}                  = 'grgtype';
  $fields{grg}{sentid}{type}                         = 'ontology';
  $fields{grg}{sentid}{label}                        = 'Sentence ID';
  $fields{grg}{sentid}{tab}                          = 'tab3';
  $fields{grg}{sentid}{ontology_type}                = 'obo';
  $fields{grg}{sentid}{ontology_table}               = 'intsentid';
  $fields{grg}{regulationlevel}{type}                = 'multidropdown';
  $fields{grg}{regulationlevel}{label}               = 'Regulation Level';
  $fields{grg}{regulationlevel}{tab}                 = 'tab3';
  $fields{grg}{regulationlevel}{dropdown_type}       = 'regulationlevel';
  $fields{grg}{transregulator}{type}                 = 'multiontology';
  $fields{grg}{transregulator}{label}                = 'Trans Regulator Gene';
  $fields{grg}{transregulator}{tab}                  = 'tab3';
  $fields{grg}{transregulator}{ontology_type}        = 'WBGene';
  $fields{grg}{moleculeregulator}{type}              = 'multiontology';
  $fields{grg}{moleculeregulator}{label}             = 'Molecule Regulator';
  $fields{grg}{moleculeregulator}{tab}               = 'tab3';
  $fields{grg}{moleculeregulator}{ontology_type}     = 'Molecule';
  $fields{grg}{transregulatorseq}{type}              = 'multiontology';	# x wants text instead of gin_sequence 2011 03 16 # want multiontology 2012 03 28
  $fields{grg}{transregulatorseq}{label}             = 'Trans Regulator Seq';
  $fields{grg}{transregulatorseq}{tab}               = 'tab3';
  $fields{grg}{transregulatorseq}{ontology_type}     = 'WBSequence';
  $fields{grg}{cisregulatorfeature}{type}            = 'multiontology';
  $fields{grg}{cisregulatorfeature}{label}           = 'Cis Regulator Feature';
  $fields{grg}{cisregulatorfeature}{tab}             = 'tab3';
  $fields{grg}{cisregulatorfeature}{ontology_type}   = 'WBSeqFeat';
#   $fields{grg}{cisregulatorfeature}{ontology_type}   = 'obo';
#   $fields{grg}{cisregulatorfeature}{ontology_table}  = 'feature';
  $fields{grg}{otherregulator}{type}                 = 'text';
  $fields{grg}{otherregulator}{label}                = 'Other Regulator';
  $fields{grg}{otherregulator}{tab}                  = 'tab3';
  $fields{grg}{transregulated}{type}                 = 'multiontology';
  $fields{grg}{transregulated}{label}                = 'Trans Regulated Gene';
  $fields{grg}{transregulated}{tab}                  = 'tab3';
  $fields{grg}{transregulated}{ontology_type}        = 'WBGene';
  $fields{grg}{cisregulated}{type}                   = 'multiontology';
  $fields{grg}{cisregulated}{label}                  = 'Cis Regulated Gene';
  $fields{grg}{cisregulated}{tab}                    = 'tab3';
  $fields{grg}{cisregulated}{ontology_type}          = 'WBGene';
  $fields{grg}{transregulatedseq}{type}              = 'multiontology';	# x wants text instead of gin_sequence 2011 03 16 # want multiontology 2012 03 28
  $fields{grg}{transregulatedseq}{label}             = 'Trans Regulated Seq';
  $fields{grg}{transregulatedseq}{tab}               = 'tab3';
  $fields{grg}{transregulatedseq}{ontology_type}     = 'WBSequence';
  $fields{grg}{otherregulated}{type}                 = 'text';
  $fields{grg}{otherregulated}{label}                = 'Other Regulated';
  $fields{grg}{otherregulated}{tab}                  = 'tab3';
  $fields{grg}{pos_anatomy}{type}                    = 'multiontology';
  $fields{grg}{pos_anatomy}{label}                   = 'Positive Anatomy';
  $fields{grg}{pos_anatomy}{tab}                     = 'tab4';
  $fields{grg}{pos_anatomy}{ontology_type}           = 'obo';
  $fields{grg}{pos_anatomy}{ontology_table}          = 'anatomy';
  $fields{grg}{pos_lifestage}{type}                  = 'multiontology';
  $fields{grg}{pos_lifestage}{label}                 = 'Positive Life Stage';
  $fields{grg}{pos_lifestage}{tab}                   = 'tab4';
  $fields{grg}{pos_lifestage}{ontology_type}         = 'obo';
  $fields{grg}{pos_lifestage}{ontology_table}        = 'lifestage';
  $fields{grg}{pos_scl}{type}                        = 'toggle_text';
  $fields{grg}{pos_scl}{label}                       = 'Positive SCL';
  $fields{grg}{pos_scl}{tab}                         = 'tab4';
  $fields{grg}{pos_scl}{inline}                      = 'pos_scltext';
  $fields{grg}{pos_scltext}{type}                    = 'text';
  $fields{grg}{pos_scltext}{label}                   = 'Positive SCL Text';
  $fields{grg}{pos_scltext}{tab}                     = 'tab4';
  $fields{grg}{pos_scltext}{inline}                  = 'INSIDE_pos_scltext';
  $fields{grg}{neg_anatomy}{type}                    = 'multiontology';
  $fields{grg}{neg_anatomy}{label}                   = 'Negative Anatomy';
  $fields{grg}{neg_anatomy}{tab}                     = 'tab4';
  $fields{grg}{neg_anatomy}{ontology_type}           = 'obo';
  $fields{grg}{neg_anatomy}{ontology_table}          = 'anatomy';
  $fields{grg}{neg_lifestage}{type}                  = 'multiontology';
  $fields{grg}{neg_lifestage}{label}                 = 'Negative Life Stage';
  $fields{grg}{neg_lifestage}{tab}                   = 'tab4';
  $fields{grg}{neg_lifestage}{ontology_type}         = 'obo';
  $fields{grg}{neg_lifestage}{ontology_table}        = 'lifestage';
  $fields{grg}{neg_scl}{type}                        = 'toggle_text';
  $fields{grg}{neg_scl}{label}                       = 'Negative SCL';
  $fields{grg}{neg_scl}{tab}                         = 'tab4';
  $fields{grg}{neg_scl}{inline}                      = 'neg_scltext';
  $fields{grg}{neg_scltext}{type}                    = 'text';
  $fields{grg}{neg_scltext}{label}                   = 'Negative SCL Text';
  $fields{grg}{neg_scltext}{tab}                     = 'tab4';
  $fields{grg}{neg_scltext}{inline}                  = 'INSIDE_neg_scltext';
  $fields{grg}{not_anatomy}{type}                    = 'multiontology';
  $fields{grg}{not_anatomy}{label}                   = 'Does Not Anatomy';
  $fields{grg}{not_anatomy}{tab}                     = 'tab4';
  $fields{grg}{not_anatomy}{ontology_type}           = 'obo';
  $fields{grg}{not_anatomy}{ontology_table}          = 'anatomy';
  $fields{grg}{not_lifestage}{type}                  = 'multiontology';
  $fields{grg}{not_lifestage}{label}                 = 'Does Not Life Stage';
  $fields{grg}{not_lifestage}{tab}                   = 'tab4';
  $fields{grg}{not_lifestage}{ontology_type}         = 'obo';
  $fields{grg}{not_lifestage}{ontology_table}        = 'lifestage';
  $fields{grg}{not_scl}{type}                        = 'toggle_text';
  $fields{grg}{not_scl}{label}                       = 'Does Not SCL';
  $fields{grg}{not_scl}{tab}                         = 'tab4';
  $fields{grg}{not_scl}{inline}                      = 'not_scltext';
  $fields{grg}{not_scltext}{type}                    = 'text';
  $fields{grg}{not_scltext}{label}                   = 'Does Not SCL Text';
  $fields{grg}{not_scltext}{tab}                     = 'tab4';
  $fields{grg}{not_scltext}{inline}                  = 'INSIDE_not_scltext';
  $fields{grg}{result}{type}                         = 'dropdown';
  $fields{grg}{result}{label}                        = 'No Subdata Result';
  $fields{grg}{result}{tab}                          = 'tab4';
  $fields{grg}{result}{dropdown_type}                = 'grgresult';

  $fields{grg}{remark}{type}                         = 'bigtext';
  $fields{grg}{remark}{label}                        = 'Remark';
  $fields{grg}{remark}{tab}                          = 'tab4';
  @{ $datatypes{grg}{constraintTablesHaveData} }     = qw( paper name summary );
  @{ $datatypes{grg}{highestPgidTables} }            = qw( name curator );
  $datatypes{grg}{newRowSub}                         = \&newRowGrg;
  $datatypes{grg}{label}                             = 'genereg';
  return( \%fields, \%datatypes);
} # sub initWormGrgFields

sub initWormIntFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{int} }, "Tie::IxHash";
  $fields{int}{id}{type}                             = 'text';
  $fields{int}{id}{label}                            = 'pgid';
  $fields{int}{id}{tab}                              = 'tab1';
  $fields{int}{name}{type}                           = 'ontology';
  $fields{int}{name}{label}                          = 'Interaction ID';
  $fields{int}{name}{tab}                            = 'tab1';
  $fields{int}{name}{ontology_type}                  = 'WBInteraction';
  $fields{int}{curator}{type}                        = 'dropdown';
  $fields{int}{curator}{label}                       = 'Curator';
  $fields{int}{curator}{tab}                         = 'tab1';
  $fields{int}{curator}{dropdown_type}               = 'curator';
#   $fields{int}{nondirectional}{type}                 = 'toggle';
#   $fields{int}{nondirectional}{label}                = 'Non_directional';
#   $fields{int}{nondirectional}{tab}                  = 'tab1';
  $fields{int}{process}{type}                        = 'multiontology';
  $fields{int}{process}{label}                       = 'Process';
  $fields{int}{process}{tab}                         = 'tab1';
  $fields{int}{process}{ontology_type}               = 'WBProcess';
  $fields{int}{database}{type}                       = 'text';
  $fields{int}{database}{label}                      = 'Database field accession number';
  $fields{int}{database}{tab}                        = 'tab1';
  $fields{int}{paper}{type}                          = 'ontology';
  $fields{int}{paper}{label}                         = 'Paper';
  $fields{int}{paper}{tab}                           = 'tab1';
  $fields{int}{paper}{ontology_type}                 = 'WBPaper';
  $fields{int}{person}{type}                         = 'multiontology';
  $fields{int}{person}{label}                        = 'Person';
  $fields{int}{person}{tab}                          = 'tab1';
  $fields{int}{person}{ontology_type}                = 'WBPerson';
  $fields{int}{type}{type}                           = 'dropdown';
  $fields{int}{type}{label}                          = 'Interaction Type';
  $fields{int}{type}{tab}                            = 'tab1';
  $fields{int}{type}{dropdown_type}                  = 'inttype';
  $fields{int}{summary}{type}                        = 'bigtext';
  $fields{int}{summary}{label}                       = 'Interaction Summary';
  $fields{int}{summary}{tab}                         = 'tab1';
  $fields{int}{remark}{type}                         = 'bigtext';
  $fields{int}{remark}{label}                        = 'Remark';
  $fields{int}{remark}{tab}                          = 'tab1';
  $fields{int}{phenotype}{type}                      = 'multiontology';
  $fields{int}{phenotype}{label}                     = 'Interaction Phenotype(s)';
  $fields{int}{phenotype}{tab}                       = 'tab1';
  $fields{int}{phenotype}{ontology_type}             = 'obo';
  $fields{int}{phenotype}{ontology_table}            = 'phenotype';
  $fields{int}{nodump}{type}                         = 'toggle';
  $fields{int}{nodump}{label}                        = 'NO DUMP';
  $fields{int}{nodump}{tab}                          = 'tab1';

  $fields{int}{detectionmethod}{type}                = 'multidropdown';
  $fields{int}{detectionmethod}{label}               = 'Physical Interaction Detection Method';
  $fields{int}{detectionmethod}{tab}                 = 'tab2';
  $fields{int}{detectionmethod}{dropdown_type}       = 'intphysdetmethod';
  $fields{int}{library}{type}                        = 'text';
  $fields{int}{library}{label}                       = 'Library screened and Times found';
  $fields{int}{library}{tab}                         = 'tab2';
  $fields{int}{laboratory}{type}                     = 'ontology';
  $fields{int}{laboratory}{label}                    = 'From Laboratory';
  $fields{int}{laboratory}{tab}                      = 'tab2';
  $fields{int}{laboratory}{ontology_type}            = 'obo';
  $fields{int}{laboratory}{ontology_table}           = 'laboratory';
  $fields{int}{company}{type}                        = 'text';
  $fields{int}{company}{label}                       = 'From Company';
  $fields{int}{company}{tab}                         = 'tab2';
  $fields{int}{pcrbait}{type}                        = 'multiontology';
  $fields{int}{pcrbait}{label}                       = 'PCR Bait';
  $fields{int}{pcrbait}{tab}                         = 'tab2';
  $fields{int}{pcrbait}{ontology_type}               = 'obo';
  $fields{int}{pcrbait}{ontology_table}              = 'pcrproduct';
  $fields{int}{pcrtarget}{type}                      = 'multiontology';
  $fields{int}{pcrtarget}{label}                     = 'PCR Target';
  $fields{int}{pcrtarget}{tab}                       = 'tab2';
  $fields{int}{pcrtarget}{ontology_type}             = 'obo';
  $fields{int}{pcrtarget}{ontology_table}            = 'pcrproduct';
  $fields{int}{pcrnondir}{type}                      = 'multiontology';
  $fields{int}{pcrnondir}{label}                     = 'Non-directional PCR(s)';
  $fields{int}{pcrnondir}{tab}                       = 'tab2';
  $fields{int}{pcrnondir}{ontology_type}             = 'obo';
  $fields{int}{pcrnondir}{ontology_table}            = 'pcrproduct';
  $fields{int}{sequencebait}{type}                   = 'text';
  $fields{int}{sequencebait}{label}                  = 'Sequence Bait';
  $fields{int}{sequencebait}{tab}                    = 'tab2';
  $fields{int}{sequencetarget}{type}                 = 'text';
  $fields{int}{sequencetarget}{label}                = 'Sequence Target(s)';
  $fields{int}{sequencetarget}{tab}                  = 'tab2';
  $fields{int}{sequencenondir}{type}                 = 'text';
  $fields{int}{sequencenondir}{label}                = 'Non-directional Sequence(s)';
  $fields{int}{sequencenondir}{tab}                  = 'tab2';
  $fields{int}{featurebait}{type}                    = 'multiontology';
  $fields{int}{featurebait}{label}                   = 'Feature Bait';
  $fields{int}{featurebait}{tab}                     = 'tab2';
  $fields{int}{featurebait}{ontology_type}           = 'WBSeqFeat';
#   $fields{int}{featurebait}{ontology_type}           = 'obo';
#   $fields{int}{featurebait}{ontology_table}          = 'feature';
  $fields{int}{featuretarget}{type}                  = 'multiontology';
  $fields{int}{featuretarget}{label}                 = 'Feature Target';
  $fields{int}{featuretarget}{tab}                   = 'tab2';
  $fields{int}{featuretarget}{ontology_type}         = 'WBSeqFeat';
#   $fields{int}{featuretarget}{ontology_type}         = 'obo';
#   $fields{int}{featuretarget}{ontology_table}        = 'feature';
  $fields{int}{cdsbait}{type}                        = 'text';
  $fields{int}{cdsbait}{label}                       = 'Bait Overlapping CDS';
  $fields{int}{cdsbait}{tab}                         = 'tab2';
  $fields{int}{cdstarget}{type}                      = 'text';
  $fields{int}{cdstarget}{label}                     = 'Target Overlapping CDS(s)';
  $fields{int}{cdstarget}{tab}                       = 'tab2';
  $fields{int}{cdsnondir}{type}                      = 'text';
  $fields{int}{cdsnondir}{label}                     = 'Non-directional Overlapping CDS(s)';
  $fields{int}{cdsnondir}{tab}                       = 'tab2';
  $fields{int}{proteinbait}{type}                    = 'text';
  $fields{int}{proteinbait}{label}                   = 'Bait Overlapping Protein';
  $fields{int}{proteinbait}{tab}                     = 'tab2';
  $fields{int}{proteintarget}{type}                  = 'text';
  $fields{int}{proteintarget}{label}                 = 'Target Overlapping Protein(s)';
  $fields{int}{proteintarget}{tab}                   = 'tab2';
  $fields{int}{proteinnondir}{type}                  = 'text';
  $fields{int}{proteinnondir}{label}                 = 'Non-directional Overlapping Protein(s)';
  $fields{int}{proteinnondir}{tab}                   = 'tab2';
  $fields{int}{genebait}{type}                       = 'ontology';
  $fields{int}{genebait}{label}                      = 'Bait Overlapping Gene';
  $fields{int}{genebait}{tab}                        = 'tab2';
  $fields{int}{genebait}{ontology_type}              = 'WBGene';
  $fields{int}{genetarget}{type}                     = 'multiontology';
  $fields{int}{genetarget}{label}                    = 'Target Overlapping Gene';
  $fields{int}{genetarget}{tab}                      = 'tab2';
  $fields{int}{genetarget}{ontology_type}            = 'WBGene';
  $fields{int}{antibody}{type}                       = 'multiontology';
  $fields{int}{antibody}{label}                      = 'Antibody';
  $fields{int}{antibody}{tab}                        = 'tab2';
  $fields{int}{antibody}{ontology_type}              = 'Antibody';
  $fields{int}{antibodyremark}{type}                 = 'text';
  $fields{int}{antibodyremark}{label}                = 'Antibody Remark';
  $fields{int}{antibodyremark}{tab}                  = 'tab2';

  $fields{int}{genenondir}{type}                     = 'multiontology';
  $fields{int}{genenondir}{label}                    = 'Non-directional Gene(s)';
  $fields{int}{genenondir}{tab}                      = 'tab3';
  $fields{int}{genenondir}{ontology_type}            = 'WBGene';
  $fields{int}{geneone}{type}                        = 'multiontology';
  $fields{int}{geneone}{label}                       = 'Effector Gene(s)';
  $fields{int}{geneone}{tab}                         = 'tab3';
  $fields{int}{geneone}{ontology_type}               = 'WBGene';
  $fields{int}{genetwo}{type}                        = 'multiontology';
  $fields{int}{genetwo}{label}                       = 'Affected Gene(s)';
  $fields{int}{genetwo}{tab}                         = 'tab3';
  $fields{int}{genetwo}{ontology_type}               = 'WBGene';
  $fields{int}{variationnondir}{type}                = 'multiontology';
  $fields{int}{variationnondir}{label}               = 'Non-directional Variation(s)';
  $fields{int}{variationnondir}{tab}                 = 'tab3';
  $fields{int}{variationnondir}{ontology_type}       = 'obo';
  $fields{int}{variationnondir}{ontology_table}      = 'variation';
  $fields{int}{variationone}{type}                   = 'multiontology';
  $fields{int}{variationone}{label}                  = 'Effector Variation(s)';
  $fields{int}{variationone}{tab}                    = 'tab3';
  $fields{int}{variationone}{ontology_type}          = 'obo';
  $fields{int}{variationone}{ontology_table}         = 'variation';
  $fields{int}{variationtwo}{type}                   = 'multiontology';
  $fields{int}{variationtwo}{label}                  = 'Affected Variation(s)';
  $fields{int}{variationtwo}{tab}                    = 'tab3';
  $fields{int}{variationtwo}{ontology_type}          = 'obo';
  $fields{int}{variationtwo}{ontology_table}         = 'variation';

  $fields{int}{moleculenondir}{type}                 = 'multiontology';
  $fields{int}{moleculenondir}{label}                = 'Non-directional Molecule';
  $fields{int}{moleculenondir}{tab}                  = 'tab3';
  $fields{int}{moleculenondir}{ontology_type}        = 'Molecule';
  $fields{int}{moleculeone}{type}                    = 'multiontology';
  $fields{int}{moleculeone}{label}                   = 'Effector Molecule';
  $fields{int}{moleculeone}{tab}                     = 'tab3';
  $fields{int}{moleculeone}{ontology_type}           = 'Molecule';
  $fields{int}{moleculetwo}{type}                    = 'multiontology';
  $fields{int}{moleculetwo}{label}                   = 'Affected Molecule';
  $fields{int}{moleculetwo}{tab}                     = 'tab3';
  $fields{int}{moleculetwo}{ontology_type}           = 'Molecule';
#   $fields{int}{intravariationone}{type}              = 'multiontology';
#   $fields{int}{intravariationone}{label}             = 'Intragenic Effector Variation(s)';
#   $fields{int}{intravariationone}{tab}               = 'tab3';
#   $fields{int}{intravariationone}{ontology_type}     = 'obo';
#   $fields{int}{intravariationone}{ontology_table}    = 'variation';
#   $fields{int}{intravariationtwo}{type}              = 'multiontology';
#   $fields{int}{intravariationtwo}{label}             = 'Intragenic Affected Variation(s)';
#   $fields{int}{intravariationtwo}{tab}               = 'tab3';
#   $fields{int}{intravariationtwo}{ontology_type}     = 'obo';
#   $fields{int}{intravariationtwo}{ontology_table}    = 'variation';
#   $fields{int}{deviation}{type}                      = 'bigtext';
#   $fields{int}{deviation}{label}                     = 'Deviation from expectation';
#   $fields{int}{deviation}{tab}                       = 'tab4';
#   $fields{int}{neutralityfxn}{type}                  = 'dropdown';
#   $fields{int}{neutralityfxn}{label}                 = 'Neutrality function';
#   $fields{int}{neutralityfxn}{tab}                   = 'tab4';
#   $fields{int}{neutralityfxn}{dropdown_type}         = 'intneutralityfxn';
  $fields{int}{rearrnondir}{type}                    = 'multiontology';
  $fields{int}{rearrnondir}{label}                   = 'Non-directional Rearrangement(s)';
  $fields{int}{rearrnondir}{tab}                     = 'tab4';
  $fields{int}{rearrnondir}{ontology_type}           = 'obo';
  $fields{int}{rearrnondir}{ontology_table}          = 'rearrangement';
  $fields{int}{rearrone}{type}                       = 'multiontology';
  $fields{int}{rearrone}{label}                      = 'Effector Rearrangement(s)';
  $fields{int}{rearrone}{tab}                        = 'tab4';
  $fields{int}{rearrone}{ontology_type}              = 'obo';
  $fields{int}{rearrone}{ontology_table}             = 'rearrangement';
  $fields{int}{rearrtwo}{type}                       = 'multiontology';
  $fields{int}{rearrtwo}{label}                      = 'Affected Rearrangement(s)';
  $fields{int}{rearrtwo}{tab}                        = 'tab4';
  $fields{int}{rearrtwo}{ontology_type}              = 'obo';
  $fields{int}{rearrtwo}{ontology_table}             = 'rearrangement';
  $fields{int}{rnai}{type}                           = 'multiontology';
  $fields{int}{rnai}{label}                          = 'RNAi';
  $fields{int}{rnai}{tab}                            = 'tab4';
  $fields{int}{rnai}{ontology_type}                  = 'WBRnai';
  $fields{int}{lsrnai}{type}                         = 'text';
  $fields{int}{lsrnai}{label}                        = 'Large scale RNAi';
  $fields{int}{lsrnai}{tab}                          = 'tab4';
  $fields{int}{exprpattern}{type}                    = 'multiontology';
  $fields{int}{exprpattern}{label}                   = 'Expression Pattern';
  $fields{int}{exprpattern}{tab}                     = 'tab4';
  $fields{int}{exprpattern}{ontology_type}           = 'Expr';
  $fields{int}{transgene}{type}                      = 'multiontology';
  $fields{int}{transgene}{label}                     = 'Transgene(s)';
  $fields{int}{transgene}{tab}                       = 'tab4';
  $fields{int}{transgene}{ontology_type}             = 'Transgene';
  $fields{int}{construct}{type}                      = 'multiontology';
  $fields{int}{construct}{label}                     = 'Construct';
  $fields{int}{construct}{tab}                       = 'tab4';
  $fields{int}{construct}{ontology_type}             = 'WBConstruct';
  $fields{int}{othernondir}{type}                    = 'text';
  $fields{int}{othernondir}{label}                   = 'Non-directional Other';
  $fields{int}{othernondir}{tab}                     = 'tab4';
#   $fields{int}{otheronetype}{type}                   = 'dropdown';
#   $fields{int}{otheronetype}{label}                  = 'Effector Other Type';
#   $fields{int}{otheronetype}{tab}                    = 'tab4';
#   $fields{int}{otheronetype}{dropdown_type}          = 'intothertype';
  $fields{int}{otherone}{type}                       = 'text';
  $fields{int}{otherone}{label}                      = 'Effector Other';
  $fields{int}{otherone}{tab}                        = 'tab4';
#   $fields{int}{othertwotype}{type}                   = 'dropdown';
#   $fields{int}{othertwotype}{label}                  = 'Affected Other Type';
#   $fields{int}{othertwotype}{tab}                    = 'tab4';
#   $fields{int}{othertwotype}{dropdown_type}          = 'intothertype';
  $fields{int}{othertwo}{type}                       = 'text';
  $fields{int}{othertwo}{label}                      = 'Affected Other';
  $fields{int}{othertwo}{tab}                        = 'tab4';

#   $fields{int}{transgeneone}{type}                   = 'ontology';
#   $fields{int}{transgeneone}{label}                  = 'Effector Transgene Name';
#   $fields{int}{transgeneone}{tab}                    = 'tab3';
#   $fields{int}{transgeneone}{ontology_type}          = 'Transgene';
#   $fields{int}{transgeneonegene}{type}               = 'multiontology';
#   $fields{int}{transgeneonegene}{label}              = 'Effector Transgene Gene';
#   $fields{int}{transgeneonegene}{tab}                = 'tab3';
#   $fields{int}{transgeneonegene}{ontology_type}      = 'WBGene';
#   $fields{int}{transgenetwo}{type}                   = 'ontology';
#   $fields{int}{transgenetwo}{label}                  = 'Effected Transgene Name';
#   $fields{int}{transgenetwo}{tab}                    = 'tab3';
#   $fields{int}{transgenetwo}{ontology_type}          = 'Transgene';
#   $fields{int}{transgenetwogene}{type}               = 'multiontology';
#   $fields{int}{transgenetwogene}{label}              = 'Effected Transgene Gene';
#   $fields{int}{transgenetwogene}{tab}                = 'tab3';
#   $fields{int}{transgenetwogene}{ontology_type}      = 'WBGene';

  $fields{int}{confidence}{type}                     = 'text';
  $fields{int}{confidence}{label}                    = 'Confidence description';
  $fields{int}{confidence}{tab}                      = 'tab5';
  $fields{int}{pvalue}{type}                         = 'text';
  $fields{int}{pvalue}{label}                        = 'P-value';
  $fields{int}{pvalue}{tab}                          = 'tab5';
  $fields{int}{loglikelihood}{type}                  = 'text';
  $fields{int}{loglikelihood}{label}                 = 'Log-likelihood score';
  $fields{int}{loglikelihood}{tab}                   = 'tab5';
  $fields{int}{throughput}{type}                     = 'toggle';
  $fields{int}{throughput}{label}                    = 'High_throughput';
  $fields{int}{throughput}{tab}                      = 'tab5';
  $fields{int}{sentid}{type}                         = 'ontology';
  $fields{int}{sentid}{label}                        = 'Sentence ID';
  $fields{int}{sentid}{tab}                          = 'tab5';
  $fields{int}{sentid}{ontology_type}                = 'obo';
  $fields{int}{sentid}{ontology_table}               = 'intsentid';
  $fields{int}{falsepositive}{type}                  = 'toggle';
  $fields{int}{falsepositive}{label}                 = 'False Positive';
  $fields{int}{falsepositive}{tab}                   = 'tab5';
  $datatypes{int}{newRowSub}                         = \&newRowInt;
  $datatypes{int}{label}                             = 'interaction';
  @{ $datatypes{int}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormIntFields

sub initWormMopFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{mop} }, "Tie::IxHash";
  $fields{mop}{id}{type}                             = 'text';
  $fields{mop}{id}{label}                            = 'pgid';
  $fields{mop}{id}{tab}                              = 'tab1';
  $fields{mop}{curator}{type}                        = 'dropdown';
  $fields{mop}{curator}{label}                       = 'Curator';
  $fields{mop}{curator}{tab}                         = 'tab1';
  $fields{mop}{curator}{dropdown_type}               = 'curator';
  $fields{mop}{paper}{type}                          = 'multiontology';
  $fields{mop}{paper}{label}                         = 'WBPaper';
  $fields{mop}{paper}{tab}                           = 'all';
  $fields{mop}{paper}{ontology_type}                 = 'WBPaper';
  $fields{mop}{name}{type}                           = 'text';
  $fields{mop}{name}{label}                          = 'Name';
  $fields{mop}{name}{tab}                            = 'tab1';
  $fields{mop}{publicname}{type}                     = 'bigtext';
  $fields{mop}{publicname}{label}                    = 'Public Name';
  $fields{mop}{publicname}{tab}                      = 'all';
  $fields{mop}{synonym}{type}                        = 'bigtext';
  $fields{mop}{synonym}{label}                       = 'Synonyms';
  $fields{mop}{synonym}{tab}                         = 'tab1';
  $fields{mop}{molecule}{type}                       = 'text';
  $fields{mop}{molecule}{label}                      = 'MeSH / CTD';
  $fields{mop}{molecule}{tab}                        = 'tab1';
  $fields{mop}{chemi}{type}                          = 'text';
  $fields{mop}{chemi}{label}                         = 'CasRN';
  $fields{mop}{chemi}{tab}                           = 'tab1';
  $fields{mop}{chebi}{type}                          = 'ontology';
  $fields{mop}{chebi}{label}                         = 'ChEBI_ID';
  $fields{mop}{chebi}{tab}                           = 'tab1';
  $fields{mop}{chebi}{ontology_type}                 = 'obo';
  $fields{mop}{chebi}{ontology_table}                = 'chebi';
  $fields{mop}{kegg}{type}                           = 'text';
  $fields{mop}{kegg}{label}                          = 'Kegg compound (Acc#)';
  $fields{mop}{kegg}{tab}                            = 'tab1';
  $fields{mop}{smmid}{type}                          = 'text';
  $fields{mop}{smmid}{label}                         = 'SMID-DB';
  $fields{mop}{smmid}{tab}                           = 'tab1';
  $fields{mop}{inchi}{type}                          = 'text';
  $fields{mop}{inchi}{label}                         = 'InChi(standard)';
  $fields{mop}{inchi}{tab}                           = 'tab1';
  $fields{mop}{inchikey}{type}                       = 'text';
  $fields{mop}{inchikey}{label}                      = 'InChi key';
  $fields{mop}{inchikey}{tab}                        = 'tab1';
  $fields{mop}{smiles}{type}                         = 'text';
  $fields{mop}{smiles}{label}                        = 'SMILES';
  $fields{mop}{smiles}{tab}                          = 'tab1';
  $fields{mop}{molformula}{type}                     = 'text';
  $fields{mop}{molformula}{label}                    = 'Formula';
  $fields{mop}{molformula}{tab}                      = 'tab1';
  $fields{mop}{iupac}{type}                          = 'text';
  $fields{mop}{iupac}{label}                         = 'IUPAC';
  $fields{mop}{iupac}{tab}                           = 'tab1';
  $fields{mop}{exactmass}{type}                      = 'text';
  $fields{mop}{exactmass}{label}                     = 'Exact mass';
  $fields{mop}{exactmass}{tab}                       = 'tab1';

  $fields{mop}{remark}{type}                         = 'bigtext';
  $fields{mop}{remark}{label}                        = 'Remark';
  $fields{mop}{remark}{tab}                          = 'tab1';
  $fields{mop}{moleculeuse}{type}                    = 'bigtext';
  $fields{mop}{moleculeuse}{label}                   = 'Molecule Use';
  $fields{mop}{moleculeuse}{tab}                     = 'tab2';
#   $fields{mop}{gotarget}{type}                       = 'multiontology';
#   $fields{mop}{gotarget}{label}                      = 'GO target';
#   $fields{mop}{gotarget}{tab}                        = 'tab2';
#   $fields{mop}{gotarget}{ontology_type}              = 'obo';
#   $fields{mop}{gotarget}{ontology_table}             = 'goid';
#   $fields{mop}{genetarget}{type}                     = 'multiontology';
#   $fields{mop}{genetarget}{label}                    = 'Gene target';
#   $fields{mop}{genetarget}{tab}                      = 'tab2';
#   $fields{mop}{genetarget}{ontology_type}            = 'WBGene';
#   $fields{mop}{classification}{type}                 = 'dropdown';
#   $fields{mop}{classification}{label}                = 'Classified as';
#   $fields{mop}{classification}{tab}                  = 'tab2';
#   $fields{mop}{classification}{dropdown_type}        = 'mopclassification';
#   $fields{mop}{source}{type}                         = 'dropdown';
#   $fields{mop}{source}{label}                        = 'Source';
#   $fields{mop}{source}{tab}                          = 'tab2';
#   $fields{mop}{source}{dropdown_type}                = 'mopsource';
#   $fields{mop}{species}{type}                        = 'ontology';
#   $fields{mop}{species}{label}                       = 'Species';
#   $fields{mop}{species}{tab}                         = 'tab2';
#   $fields{mop}{species}{ontology_type}               = 'obo';
#   $fields{mop}{species}{ontology_table}              = 'species';
#   $fields{mop}{role}{type}                           = 'dropdown';
#   $fields{mop}{role}{label}                          = 'Role';
#   $fields{mop}{role}{tab}                            = 'tab2';
#   $fields{mop}{role}{dropdown_type}                  = 'moprole';
  $fields{mop}{biorole}{type}                          = 'dropdown';
  $fields{mop}{biorole}{label}                         = 'BioRole';
  $fields{mop}{biorole}{tab}                           = 'tab2';
  $fields{mop}{biorole}{dropdown_type}                 = 'mopbiorole';
  $fields{mop}{bioroletext}{type}                      = 'text';
  $fields{mop}{bioroletext}{label}                     = 'BioRole Text';
  $fields{mop}{bioroletext}{tab}                       = 'tab2';
  $fields{mop}{essentialfor}{type}                     = 'ontology';
  $fields{mop}{essentialfor}{label}                    = 'EssentialForSpecies';
  $fields{mop}{essentialfor}{tab}                      = 'tab2';
  $fields{mop}{essentialfor}{ontology_type}            = 'obo';
  $fields{mop}{essentialfor}{ontology_table}           = 'species';
  $fields{mop}{status}{type}                           = 'dropdown';
  $fields{mop}{status}{label}                          = 'Status';
  $fields{mop}{status}{tab}                            = 'tab2';
  $fields{mop}{status}{dropdown_type}                  = 'mopstatus';
  $fields{mop}{detctmethod}{type}                      = 'dropdown';
  $fields{mop}{detctmethod}{label}                     = 'DetectionMethod';
  $fields{mop}{detctmethod}{tab}                       = 'tab2';
  $fields{mop}{detctmethod}{dropdown_type}             = 'mopdetctmethod';
  $fields{mop}{otherdetctmethod}{type}                 = 'text';
  $fields{mop}{otherdetctmethod}{label}                = 'OtherDetectionMethod';
  $fields{mop}{otherdetctmethod}{tab}                  = 'tab2';
  $fields{mop}{extrctmethod}{type}                     = 'dropdown';
  $fields{mop}{extrctmethod}{label}                    = 'ExtractionMethod';
  $fields{mop}{extrctmethod}{tab}                      = 'tab2';
  $fields{mop}{extrctmethod}{dropdown_type}            = 'mopextrctmethod';
  $fields{mop}{otherextrctmethod}{type}                = 'text';
  $fields{mop}{otherextrctmethod}{label}               = 'OtherExtractionMethod';
  $fields{mop}{otherextrctmethod}{tab}                 = 'tab2';
  $fields{mop}{chemicalsynthesis}{type}                = 'toggle';
  $fields{mop}{chemicalsynthesis}{label}               = 'Chemical Synthesis';
  $fields{mop}{chemicalsynthesis}{tab}                 = 'tab2';
  $fields{mop}{nonbiosource}{type}                     = 'text';
  $fields{mop}{nonbiosource}{label}                    = 'NonSpeciesSource';
  $fields{mop}{nonbiosource}{tab}                      = 'tab2';
  $fields{mop}{endogenousin}{type}                     = 'ontology';
  $fields{mop}{endogenousin}{label}                    = 'Endogenous in';
  $fields{mop}{endogenousin}{tab}                      = 'tab2';
  $fields{mop}{endogenousin}{ontology_type}            = 'obo';
  $fields{mop}{endogenousin}{ontology_table}           = 'ncbitaxonid';

  $datatypes{mop}{newRowSub}                         = \&newRowMop;
  $datatypes{mop}{label}                             = 'molecule';
  @{ $datatypes{mop}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormMopFields

sub initWormMovFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{mov} }, "Tie::IxHash";
  $fields{mov}{id}{type}                             = 'text';
  $fields{mov}{id}{label}                            = 'pgid';
  $fields{mov}{id}{tab}                              = 'all';
  $fields{mov}{name}{type}                           = 'text';
  $fields{mov}{name}{label}                          = 'Name';
  $fields{mov}{name}{tab}                            = 'all';
  $fields{mov}{paper}{type}                          = 'ontology';
  $fields{mov}{paper}{label}                         = 'WBPaper';
  $fields{mov}{paper}{tab}                           = 'all';
  $fields{mov}{paper}{ontology_type}                 = 'WBPaper';
  $fields{mov}{source}{type}                         = 'text';
  $fields{mov}{source}{label}                        = 'Source';
  $fields{mov}{source}{tab}                          = 'all';
  $fields{mov}{description}{type}                    = 'bigtext';
  $fields{mov}{description}{label}                   = 'Description';
  $fields{mov}{description}{tab}                     = 'all';
  $fields{mov}{rnai}{type}                           = 'text';		# citaceMinus objects, no plan to curate to rnaiOA objects - Daniela 2012 10 15
  $fields{mov}{rnai}{label}                          = 'RNAi';
  $fields{mov}{rnai}{tab}                            = 'all';
  $fields{mov}{exprpattern}{type}                    = 'multiontology';
  $fields{mov}{exprpattern}{label}                   = 'Expression Pattern';
  $fields{mov}{exprpattern}{tab}                     = 'all';
  $fields{mov}{exprpattern}{ontology_type}           = 'Expr';
  $fields{mov}{dbinfo}{type}                         = 'text';
  $fields{mov}{dbinfo}{label}                        = 'DB_INFO';
  $fields{mov}{dbinfo}{tab}                          = 'all';
  $fields{mov}{variation}{type}                      = 'multiontology';
  $fields{mov}{variation}{label}                     = 'Variation';
  $fields{mov}{variation}{tab}                       = 'all';
  $fields{mov}{variation}{ontology_type}             = 'obo';
  $fields{mov}{variation}{ontology_table}            = 'variation';
  $fields{mov}{remark}{type}                         = 'bigtext';
  $fields{mov}{remark}{label}                        = 'Remark';
  $fields{mov}{remark}{tab}                          = 'all';
  $fields{mov}{curator}{type}                        = 'dropdown';
  $fields{mov}{curator}{label}                       = 'Curator';
  $fields{mov}{curator}{tab}                         = 'all';
  $fields{mov}{curator}{dropdown_type}               = 'curator';
  $datatypes{mov}{newRowSub}                         = \&newRowMov;
  $datatypes{mov}{label}                             = 'movie';
  @{ $datatypes{mov}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormMovFields

sub initWormPicFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{pic} }, "Tie::IxHash";
  $fields{pic}{id}{type}                             = 'text';
  $fields{pic}{id}{label}                            = 'pgid';
  $fields{pic}{id}{tab}                              = 'tab1';
  $fields{pic}{name}{type}                           = 'text';
  $fields{pic}{name}{label}                          = 'WBPicture';
  $fields{pic}{name}{tab}                            = 'all';
  $fields{pic}{paper}{type}                          = 'ontology';
  $fields{pic}{paper}{label}                         = 'Reference';
  $fields{pic}{paper}{tab}                           = 'all';
  $fields{pic}{paper}{ontology_type}                 = 'WBPaper';
  $fields{pic}{contact}{type}                        = 'ontology';
  $fields{pic}{contact}{label}                       = 'Contact';
  $fields{pic}{contact}{tab}                         = 'tab1';
  $fields{pic}{contact}{ontology_type}               = 'WBPerson';
  $fields{pic}{description}{type}                    = 'bigtext';
  $fields{pic}{description}{label}                   = 'Description';
  $fields{pic}{description}{tab}                     = 'all';
  $fields{pic}{source}{type}                         = 'text';
  $fields{pic}{source}{label}                        = 'Source';
  $fields{pic}{source}{tab}                          = 'tab1';
  $fields{pic}{croppedfrom}{type}                    = 'ontology';
  $fields{pic}{croppedfrom}{label}                   = 'Cropped_from';
  $fields{pic}{croppedfrom}{tab}                     = 'tab1';
  $fields{pic}{croppedfrom}{ontology_type}           = 'WBPicture';
  $fields{pic}{exprpattern}{type}                    = 'multiontology';
  $fields{pic}{exprpattern}{label}                   = 'Expression Pattern';
  $fields{pic}{exprpattern}{tab}                     = 'tab1';
  $fields{pic}{exprpattern}{ontology_type}           = 'Expr';
#   $fields{pic}{exprpattern}{ontology_type}           = 'obo';
#   $fields{pic}{exprpattern}{ontology_table}          = 'exprpattern';
  $fields{pic}{process}{type}                        = 'multiontology';
  $fields{pic}{process}{label}                       = 'Topic';
  $fields{pic}{process}{tab}                         = 'tab1';
  $fields{pic}{process}{ontology_type}               = 'WBProcess';
  $fields{pic}{remark}{type}                         = 'bigtext';
  $fields{pic}{remark}{label}                        = 'Remark';
  $fields{pic}{remark}{tab}                          = 'tab1';
  $fields{pic}{goid}{type}                           = 'multiontology';
  $fields{pic}{goid}{label}                          = 'Cellular_component';
  $fields{pic}{goid}{tab}                            = 'tab1';
  $fields{pic}{goid}{ontology_type}                  = 'obo';
  $fields{pic}{goid}{ontology_table}                 = 'goid';
  $fields{pic}{anat_term}{type}                      = 'multiontology';
  $fields{pic}{anat_term}{label}                     = 'Anatomy_term';
  $fields{pic}{anat_term}{tab}                       = 'tab1';
  $fields{pic}{anat_term}{ontology_type}             = 'obo';
  $fields{pic}{anat_term}{ontology_table}            = 'anatomy';
  $fields{pic}{urlaccession}{type}                   = 'text';
  $fields{pic}{urlaccession}{label}                  = 'URL Accession';
  $fields{pic}{urlaccession}{tab}                    = 'tab1';
  $fields{pic}{person}{type}                         = 'multiontology';
  $fields{pic}{person}{label}                        = 'Person';
  $fields{pic}{person}{tab}                          = 'tab1';
  $fields{pic}{person}{ontology_type}                = 'WBPerson';
  $fields{pic}{persontext}{type}                     = 'text';
  $fields{pic}{persontext}{label}                    = 'Person Text';
  $fields{pic}{persontext}{tab}                      = 'tab1';
  $fields{pic}{lifestage}{type}                      = 'multiontology';
  $fields{pic}{lifestage}{label}                     = 'Life Stage';
  $fields{pic}{lifestage}{tab}                       = 'tab1';
  $fields{pic}{lifestage}{ontology_type}             = 'obo';
  $fields{pic}{lifestage}{ontology_table}            = 'lifestage';
#   $fields{pic}{species}{type}                        = 'dropdown';
  $fields{pic}{species}{type}                        = 'ontology';
  $fields{pic}{species}{label}                       = 'Species';
  $fields{pic}{species}{tab}                         = 'tab1';
#   $fields{pic}{species}{dropdown_type}               = 'species';
  $fields{pic}{species}{ontology_type}               = 'obo';
  $fields{pic}{species}{ontology_table}              = 'species';
  $fields{pic}{curator}{type}                        = 'dropdown';
  $fields{pic}{curator}{label}                       = 'Curator';
  $fields{pic}{curator}{tab}                         = 'all';
  $fields{pic}{curator}{dropdown_type}               = 'curator';
  $fields{pic}{nodump}{type}                         = 'toggle';
  $fields{pic}{nodump}{label}                        = 'NO DUMP';
  $fields{pic}{nodump}{tab}                          = 'tab1';
  $fields{pic}{chris}{type}                          = 'toggle';
  $fields{pic}{chris}{label}                         = 'Chris Flag';
  $fields{pic}{chris}{tab}                           = 'tab1';
  $fields{pic}{phenotype}{type}                      = 'multiontology';
  $fields{pic}{phenotype}{label}                     = 'Phenotype';
  $fields{pic}{phenotype}{tab}                       = 'tab2';
  $fields{pic}{phenotype}{ontology_type}             = 'obo';
  $fields{pic}{phenotype}{ontology_table}            = 'phenotype';
  $fields{pic}{variation}{type}                      = 'ontology';
  $fields{pic}{variation}{label}                     = 'Allele';
  $fields{pic}{variation}{tab}                       = 'tab2';
  $fields{pic}{variation}{ontology_type}             = 'obo';
  $fields{pic}{variation}{ontology_table}            = 'variation';
  $fields{pic}{wbgene}{type}                         = 'multiontology';
  $fields{pic}{wbgene}{label}                        = 'Gene';
  $fields{pic}{wbgene}{tab}                          = 'tab2';
  $fields{pic}{wbgene}{ontology_type}                = 'WBGene';
  $fields{pic}{email}{type}                          = 'text';
  $fields{pic}{email}{label}                         = 'Email';
  $fields{pic}{email}{tab}                           = 'tab2';
  $fields{pic}{coaut}{type}                          = 'multiontology';
  $fields{pic}{coaut}{label}                         = 'Co-authors';
  $fields{pic}{coaut}{tab}                           = 'tab2';
  $fields{pic}{coaut}{ontology_type}                 = 'WBPerson';
  $fields{pic}{micropublication}{type}               = 'toggle';
  $fields{pic}{micropublication}{label}              = 'Micropublication';
  $fields{pic}{micropublication}{tab}                = 'tab2';
  $datatypes{pic}{newRowSub}                         = \&newRowPic;
  $datatypes{pic}{label}                             = 'picture';
  @{ $datatypes{pic}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormPicFields

sub initWormProFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{pro} }, "Tie::IxHash";

  $fields{pro}{id}{type}                             = 'text';
  $fields{pro}{id}{label}                            = 'pgid';
  $fields{pro}{id}{tab}                              = 'tab1';
  $fields{pro}{curator}{type}                        = 'dropdown';
  $fields{pro}{curator}{label}                       = 'Curator';
  $fields{pro}{curator}{tab}                         = 'tab1';
  $fields{pro}{curator}{dropdown_type}               = 'curator';
  $fields{pro}{paper}{type}                          = 'ontology';
  $fields{pro}{paper}{label}                         = 'WBPaper';
  $fields{pro}{paper}{tab}                           = 'tab1';
  $fields{pro}{paper}{ontology_type}                 = 'WBPaper';
  $fields{pro}{paperprimarystatus}{type}             = 'text';
  $fields{pro}{paperprimarystatus}{label}            = 'Paper Primary Status';
  $fields{pro}{paperprimarystatus}{tab}              = 'tab1';
  $fields{pro}{paperprimarystatus}{disabled}         = 'disabled';
  $fields{pro}{topicpaperstatus}{type}               = 'dropdown';
  $fields{pro}{topicpaperstatus}{label}              = 'Topic Paper Status';
  $fields{pro}{topicpaperstatus}{tab}                = 'tab1';
  $fields{pro}{topicpaperstatus}{dropdown_type}      = 'topicpaperstatus';
  $fields{pro}{process}{type}                        = 'ontology';
  $fields{pro}{process}{label}                       = 'Topic';
  $fields{pro}{process}{tab}                         = 'tab1';
  $fields{pro}{process}{ontology_type}               = 'WBProcess';
#   $fields{pro}{goid}{type}                           = 'multiontology';	# removed and moved to prt_
#   $fields{pro}{goid}{label}                          = 'GO_term';
#   $fields{pro}{goid}{tab}                            = 'tab1';
#   $fields{pro}{goid}{ontology_type}                  = 'obo';
#   $fields{pro}{goid}{ontology_table}                 = 'goid';
  $fields{pro}{wbgene}{type}                         = 'multiontology';
  $fields{pro}{wbgene}{label}                        = 'Gene';
  $fields{pro}{wbgene}{tab}                          = 'tab1';
  $fields{pro}{wbgene}{ontology_type}                = 'WBGene';
  $fields{pro}{phenotype}{type}                      = 'multiontology';
  $fields{pro}{phenotype}{label}                     = 'Phenotype';
  $fields{pro}{phenotype}{tab}                       = 'tab1';
  $fields{pro}{phenotype}{ontology_type}             = 'obo';
  $fields{pro}{phenotype}{ontology_table}            = 'phenotype';
  $fields{pro}{molecule}{type}                       = 'multiontology';
  $fields{pro}{molecule}{label}                      = 'Molecule';
  $fields{pro}{molecule}{tab}                        = 'tab1';
  $fields{pro}{molecule}{ontology_type}              = 'Molecule';
  $fields{pro}{sentid}{type}                         = 'ontology';
  $fields{pro}{sentid}{label}                        = 'Sentence ID';
  $fields{pro}{sentid}{tab}                          = 'tab1';
  $fields{pro}{sentid}{ontology_type}                = 'obo';
  $fields{pro}{sentid}{ontology_table}               = 'prosentid';
  $fields{pro}{falsepositive}{type}                  = 'toggle';
  $fields{pro}{falsepositive}{label}                 = 'False Positive';
  $fields{pro}{falsepositive}{tab}                   = 'tab1';
  $fields{pro}{anatomy}{type}                        = 'multiontology';
  $fields{pro}{anatomy}{label}                       = 'Anatomy_term';
  $fields{pro}{anatomy}{tab}                         = 'tab2';
  $fields{pro}{anatomy}{ontology_type}               = 'obo';
  $fields{pro}{anatomy}{ontology_table}              = 'anatomy';
  $fields{pro}{lifestage}{type}                      = 'multiontology';
  $fields{pro}{lifestage}{label}                     = 'Life_stage';
  $fields{pro}{lifestage}{tab}                       = 'tab2';
  $fields{pro}{lifestage}{ontology_type}             = 'obo';
  $fields{pro}{lifestage}{ontology_table}            = 'lifestage';
  $fields{pro}{taxon}{type}                          = 'multiontology';
  $fields{pro}{taxon}{label}                         = 'Taxon';
  $fields{pro}{taxon}{tab}                           = 'tab2';
  $fields{pro}{taxon}{ontology_type}                 = 'obo';
  $fields{pro}{taxon}{ontology_table}                = 'taxon';
  $fields{pro}{exprcluster}{type}                    = 'multiontology';
  $fields{pro}{exprcluster}{label}                   = 'Expression_cluster';
  $fields{pro}{exprcluster}{tab}                     = 'tab2';
  $fields{pro}{exprcluster}{ontology_type}           = 'obo';
  $fields{pro}{exprcluster}{ontology_table}          = 'exprcluster';
  $fields{pro}{construct}{type}                      = 'multiontology';
  $fields{pro}{construct}{label}                     = 'Marker Construct';
  $fields{pro}{construct}{tab}                       = 'tab2';
  $fields{pro}{construct}{ontology_type}             = 'WBConstruct';
#   $fields{pro}{humdisease}{type}                     = 'text';			# TO CHANGE
#   $fields{pro}{humdisease}{label}                    = 'Human_disease';
#   $fields{pro}{humdisease}{tab}                      = 'tab3';
  $fields{pro}{humdisease}{type}                     = 'multiontology';
  $fields{pro}{humdisease}{label}                    = 'Human_disease';
  $fields{pro}{humdisease}{tab}                      = 'tab3';
  $fields{pro}{humdisease}{ontology_type}            = 'obo';
  $fields{pro}{humdisease}{ontology_table}           = 'humando';
  $fields{pro}{topicdiagram}{type}                   = 'toggle_text';
  $fields{pro}{topicdiagram}{label}                  = 'Topic Diagram';
  $fields{pro}{topicdiagram}{tab}                    = 'tab3';
  $fields{pro}{topicdiagram}{inline}                 = 'figurenumber';
  $fields{pro}{figurenumber}{type}                   = 'text';
  $fields{pro}{figurenumber}{label}                  = 'Figure Number';
  $fields{pro}{figurenumber}{tab}                    = 'tab3';
  $fields{pro}{figurenumber}{inline}                 = 'INSIDE_figurenumber';
#   $fields{pro}{picture}{type}                        = 'multiontology';	# removed and replaced with topicdiagram and figurenumber
#   $fields{pro}{picture}{label}                       = 'Picture';
#   $fields{pro}{picture}{tab}                         = 'tab3';
#   $fields{pro}{picture}{ontology_type}               = 'WBPicture';
  $fields{pro}{movie}{type}                          = 'text';			# TO CHANGE
  $fields{pro}{movie}{label}                         = 'Movie';
  $fields{pro}{movie}{tab}                           = 'tab3';
  $fields{pro}{pathwaydb}{type}                      = 'bigtext';		# TO CHANGE
  $fields{pro}{pathwaydb}{label}                     = 'Pathway Database';
  $fields{pro}{pathwaydb}{tab}                       = 'tab3';
  $fields{pro}{remark}{type}                         = 'bigtext';
  $fields{pro}{remark}{label}                        = 'Remark';
  $fields{pro}{remark}{tab}                          = 'tab3';
  $fields{pro}{curationstatusomit}{type}             = 'toggle';
  $fields{pro}{curationstatusomit}{label}            = 'Curation Status Omit';
  $fields{pro}{curationstatusomit}{tab}              = 'tab3';
  $datatypes{pro}{newRowSub}                         = \&newRowPro;
  $datatypes{pro}{label}                             = 'topic';
  @{ $datatypes{pro}{highestPgidTables} }            = qw( process curator );

  return( \%fields, \%datatypes);
} # sub initWormProFields

sub initWormPrtFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{prt} }, "Tie::IxHash";
  $fields{prt}{id}{type}                             = 'text';
  $fields{prt}{id}{label}                            = 'pgid';
  $fields{prt}{id}{tab}                              = 'tab1';
  $fields{prt}{curator}{type}                        = 'dropdown';
  $fields{prt}{curator}{label}                       = 'Curator';
  $fields{prt}{curator}{tab}                         = 'tab1';
  $fields{prt}{curator}{dropdown_type}               = 'curator';
  $fields{prt}{processid}{type}                      = 'text';
  $fields{prt}{processid}{label}                     = 'WBbioprID';
  $fields{prt}{processid}{tab}                       = 'all';
  $fields{prt}{processname}{type}                    = 'text';
  $fields{prt}{processname}{label}                   = 'Process Name';
  $fields{prt}{processname}{tab}                     = 'all';
  $fields{prt}{summary}{type}                        = 'bigtext';
  $fields{prt}{summary}{label}                       = 'Summary';
  $fields{prt}{summary}{tab}                         = 'tab1';
  $fields{prt}{othername}{type}                      = 'bigtext';
  $fields{prt}{othername}{label}                     = 'Other_name';
  $fields{prt}{othername}{tab}                       = 'tab1';
  $fields{prt}{goid}{type}                           = 'multiontology';
  $fields{prt}{goid}{label}                          = 'GO_term';
  $fields{prt}{goid}{tab}                            = 'all';
  $fields{prt}{goid}{ontology_type}                  = 'obo';
  $fields{prt}{goid}{ontology_table}                 = 'goid';
  $fields{prt}{relation}{type}                       = 'ontology';
  $fields{prt}{relation}{label}                      = 'WBro_relation';
  $fields{prt}{relation}{tab}                        = 'tab2';
  $fields{prt}{relation}{ontology_type}              = 'obo';
  $fields{prt}{relation}{ontology_table}             = 'topicrelations';
  $fields{prt}{relprocess}{type}                     = 'multiontology';
  $fields{prt}{relprocess}{label}                    = 'Related_process';
  $fields{prt}{relprocess}{tab}                      = 'tab2';
  $fields{prt}{relprocess}{ontology_type}            = 'WBProcess';
  $fields{prt}{specialisationof}{type}               = 'multiontology';
  $fields{prt}{specialisationof}{label}              = 'Specialisation_of';
  $fields{prt}{specialisationof}{tab}                = 'all';
  $fields{prt}{specialisationof}{ontology_type}      = 'WBProcess';
  $fields{prt}{generalisationof}{type}               = 'multiontology';
  $fields{prt}{generalisationof}{label}              = 'Generalisation_of';
  $fields{prt}{generalisationof}{tab}                = 'all';
  $fields{prt}{generalisationof}{ontology_type}      = 'WBProcess';
  $fields{prt}{remark}{type}                         = 'bigtext';
  $fields{prt}{remark}{label}                        = 'Remark';
  $fields{prt}{remark}{tab}                          = 'all';
  $fields{prt}{paper}{type}                          = 'multiontology';
  $fields{prt}{paper}{label}                         = 'WBPaper';
  $fields{prt}{paper}{tab}                           = 'tab1';
  $fields{prt}{paper}{ontology_type}                 = 'WBPaper';
  $fields{prt}{nodump}{type}                         = 'toggle';
  $fields{prt}{nodump}{label}                        = 'NO DUMP';
  $fields{prt}{nodump}{tab}                          = 'tab1';
  $datatypes{prt}{newRowSub}                         = \&newRowPrt;
  $datatypes{prt}{label}                             = 'process term';
  @{ $datatypes{prt}{highestPgidTables} }            = qw( processid curator );
  return( \%fields, \%datatypes);
} # sub initWormPrtFields

sub initWormPtgFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{ptg} }, "Tie::IxHash";
  $fields{ptg}{id}{type}                             = 'text';
  $fields{ptg}{id}{label}                            = 'pgid';
  $fields{ptg}{id}{tab}                              = 'all';
  $fields{ptg}{term}{type}                           = 'ontology';
  $fields{ptg}{term}{label}                          = 'Phenotype';
  $fields{ptg}{term}{tab}                            = 'all';
  $fields{ptg}{term}{ontology_type}                  = 'obo';
  $fields{ptg}{term}{ontology_table}                 = 'phenotype';
  $fields{ptg}{goid}{type}                           = 'ontology';
  $fields{ptg}{goid}{label}                          = 'GO Term';
  $fields{ptg}{goid}{tab}                            = 'all';
  $fields{ptg}{goid}{ontology_type}                  = 'obo';
  $fields{ptg}{goid}{ontology_table}                 = 'goid';
  $fields{ptg}{curator}{type}                        = 'dropdown';
  $fields{ptg}{curator}{label}                       = 'Curator';
  $fields{ptg}{curator}{tab}                         = 'all';
  $fields{ptg}{curator}{dropdown_type}               = 'curator';
  $fields{ptg}{lastupdate}{type}                     = 'text';
  $fields{ptg}{lastupdate}{label}                    = 'Last Updated';
  $fields{ptg}{lastupdate}{tab}                      = 'all';
  $datatypes{ptg}{newRowSub}                         = \&newRowPtg;
  $datatypes{ptg}{label}                             = 'transgene';
  @{ $datatypes{ptg}{highestPgidTables} }            = qw( term curator );
  return( \%fields, \%datatypes);
} # sub initWormPtgFields

sub initWormRnaFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{rna} }, "Tie::IxHash";
  $fields{rna}{id}{type}                             = 'text';
  $fields{rna}{id}{label}                            = 'pgid';
  $fields{rna}{id}{tab}                              = 'tab1';
  $fields{rna}{name}{type}                           = 'text';
  $fields{rna}{name}{label}                          = 'Name';
  $fields{rna}{name}{tab}                            = 'tab1';
  $fields{rna}{paper}{type}                          = 'ontology';
  $fields{rna}{paper}{label}                         = 'Paper';
  $fields{rna}{paper}{tab}                           = 'tab1';
  $fields{rna}{paper}{ontology_type}                 = 'WBPaper';
#   $fields{rna}{laboratory}{type}                     = 'multiontology';	# removed from OA kept in postgres and dumper 2015 09 01
#   $fields{rna}{laboratory}{label}                    = 'Laboratory';
#   $fields{rna}{laboratory}{tab}                      = 'tab1';
#   $fields{rna}{laboratory}{ontology_type}            = 'obo';
#   $fields{rna}{laboratory}{ontology_table}           = 'laboratory';
#   $fields{rna}{date}{type}                           = 'text';	# removed from OA kept in postgres and dumper 2015 09 01
#   $fields{rna}{date}{label}                          = 'Date';
#   $fields{rna}{date}{tab}                            = 'tab1';
  $fields{rna}{curator}{type}                        = 'dropdown';
  $fields{rna}{curator}{label}                       = 'Curator';
  $fields{rna}{curator}{tab}                         = 'tab1';
  $fields{rna}{curator}{dropdown_type}               = 'curator';
  $fields{rna}{pcrproduct}{type}                     = 'multiontology';
  $fields{rna}{pcrproduct}{label}                    = 'PCR Product';
  $fields{rna}{pcrproduct}{tab}                      = 'tab1';
  $fields{rna}{pcrproduct}{ontology_type}            = 'obo';
  $fields{rna}{pcrproduct}{ontology_table}           = 'pcrproduct';
  $fields{rna}{dnatext}{type}                        = 'bigtext';
  $fields{rna}{dnatext}{label}                       = 'DNA text';
  $fields{rna}{dnatext}{tab}                         = 'tab1';
#   $fields{rna}{sequence}{type}                       = 'text';	# removed from OA kept in postgres and dumper 2015 09 01
#   $fields{rna}{sequence}{label}                      = 'Sequence';
#   $fields{rna}{sequence}{tab}                        = 'tab1';
  $fields{rna}{strain}{type}                         = 'ontology';
  $fields{rna}{strain}{label}                        = 'Strain';
  $fields{rna}{strain}{tab}                          = 'tab1';
  $fields{rna}{strain}{ontology_type}                = 'obo';
  $fields{rna}{strain}{ontology_table}               = 'strain';
  $fields{rna}{genotype}{type}                       = 'bigtext';
  $fields{rna}{genotype}{label}                      = 'Genotype';
  $fields{rna}{genotype}{tab}                        = 'tab1';
  $fields{rna}{treatment}{type}                      = 'bigtext';
  $fields{rna}{treatment}{label}                     = 'Treatment';
  $fields{rna}{treatment}{tab}                       = 'tab1';
  $fields{rna}{temperature}{type}                    = 'text';
  $fields{rna}{temperature}{label}                   = 'Temperature';
  $fields{rna}{temperature}{tab}                     = 'tab1';
  $fields{rna}{deliverymethod}{type}                 = 'multidropdown';
  $fields{rna}{deliverymethod}{label}                = 'Delivery Method';
  $fields{rna}{deliverymethod}{tab}                  = 'tab1';
  $fields{rna}{deliverymethod}{dropdown_type}        = 'deliverymethod';
#   $fields{rna}{species}{type}                        = 'dropdown';
  $fields{rna}{species}{type}                        = 'ontology';
  $fields{rna}{species}{label}                       = 'Species';
  $fields{rna}{species}{tab}                         = 'tab1';
#   $fields{rna}{species}{dropdown_type}               = 'species';
  $fields{rna}{species}{ontology_type}               = 'obo';
  $fields{rna}{species}{ontology_table}              = 'species';
  $fields{rna}{remark}{type}                         = 'bigtext';
  $fields{rna}{remark}{label}                        = 'Remark';
  $fields{rna}{remark}{tab}                          = 'tab1';
  $fields{rna}{phenotype}{type}                      = 'multiontology';
  $fields{rna}{phenotype}{label}                     = 'Phenotype Observed';
  $fields{rna}{phenotype}{tab}                       = 'all';
  $fields{rna}{phenotype}{ontology_type}             = 'obo';
  $fields{rna}{phenotype}{ontology_table}            = 'phenotype';
  $fields{rna}{phenotypenot}{type}                   = 'toggle';
  $fields{rna}{phenotypenot}{label}                  = 'NOT';
  $fields{rna}{phenotypenot}{tab}                    = 'all';
  $fields{rna}{phenremark}{type}                     = 'bigtext';
  $fields{rna}{phenremark}{label}                    = 'Phenotype Remark';
  $fields{rna}{phenremark}{tab}                      = 'all';
  $fields{rna}{suggested}{type}                      = 'text';
  $fields{rna}{suggested}{label}                     = 'Phenotype Suggestion';
  $fields{rna}{suggested}{tab}                       = 'tab2';
  $fields{rna}{suggested_definition}{type}           = 'bigtext';
  $fields{rna}{suggested_definition}{label}          = 'Suggested Definition';
  $fields{rna}{suggested_definition}{tab}            = 'tab2';
  $fields{rna}{child_of}{type}                       = 'multiontology';
  $fields{rna}{child_of}{label}                      = 'Child Of';
  $fields{rna}{child_of}{tab}                        = 'tab2';
  $fields{rna}{child_of}{ontology_type}              = 'obo';
  $fields{rna}{child_of}{ontology_table}             = 'phenotype';
  $fields{rna}{molecule}{type}                       = 'multiontology';
  $fields{rna}{molecule}{label}                      = 'Affected By Molecule';
  $fields{rna}{molecule}{tab}                        = 'tab2';
  $fields{rna}{molecule}{ontology_type}              = 'Molecule';
  $fields{rna}{penfromto}{type}                      = 'text';
  $fields{rna}{penfromto}{label}                     = 'Penetrance From To';
  $fields{rna}{penfromto}{tab}                       = 'tab2';
  $fields{rna}{penetrance}{type}                     = 'dropdown';
  $fields{rna}{penetrance}{label}                    = 'Penetrance';
  $fields{rna}{penetrance}{tab}                      = 'tab2';
  $fields{rna}{penetrance}{dropdown_type}            = 'penetrance';
#   $fields{rna}{penincomplete}{type}                  = 'toggle';
#   $fields{rna}{penincomplete}{label}                 = 'Penetrance Incomplete';
#   $fields{rna}{penincomplete}{tab}                   = 'tab2';
#   $fields{rna}{penlow}{type}                         = 'toggle';
#   $fields{rna}{penlow}{label}                        = 'Penetrance Low';
#   $fields{rna}{penlow}{tab}                          = 'tab2';
#   $fields{rna}{penhigh}{type}                        = 'toggle';
#   $fields{rna}{penhigh}{label}                       = 'Penetrance High';
#   $fields{rna}{penhigh}{tab}                         = 'tab2';
#   $fields{rna}{pencomplete}{type}                    = 'toggle';
#   $fields{rna}{pencomplete}{label}                   = 'Penetrance Complete';
#   $fields{rna}{pencomplete}{tab}                     = 'tab2';
  $fields{rna}{quantfromto}{type}                    = 'text';
  $fields{rna}{quantfromto}{label}                   = 'Quantity From To';
  $fields{rna}{quantfromto}{tab}                     = 'tab2';
  $fields{rna}{quantdesc}{type}                      = 'bigtext';
  $fields{rna}{quantdesc}{label}                     = 'Quantity Description';
  $fields{rna}{quantdesc}{tab}                       = 'tab2';
  $fields{rna}{heatsens}{type}                       = 'toggle';
  $fields{rna}{heatsens}{label}                      = 'Heat Sensitive';
  $fields{rna}{heatsens}{tab}                        = 'tab2';
  $fields{rna}{coldsens}{type}                       = 'toggle';
  $fields{rna}{coldsens}{label}                      = 'Cold Sensitive';
  $fields{rna}{coldsens}{tab}                        = 'tab2';
#   $fields{rna}{phenotypenot}{type}                   = 'multiontology';
#   $fields{rna}{phenotypenot}{label}                  = 'NOT';
#   $fields{rna}{phenotypenot}{tab}                    = 'tab2';
#   $fields{rna}{phenotypenot}{ontology_type}          = 'obo';
#   $fields{rna}{phenotypenot}{ontology_table}         = 'phenotype';

  $fields{rna}{anatomy}{type}                        = 'multiontology';
  $fields{rna}{anatomy}{label}                       = 'Anatomy';
  $fields{rna}{anatomy}{tab}                         = 'tab3';
  $fields{rna}{anatomy}{ontology_type}               = 'obo';
  $fields{rna}{anatomy}{ontology_table}              = 'anatomy';
  $fields{rna}{anatomyquality}{type}                 = 'multiontology';
  $fields{rna}{anatomyquality}{label}                = 'Anatomy Quality';
  $fields{rna}{anatomyquality}{tab}                  = 'tab3';
  $fields{rna}{anatomyquality}{ontology_type}        = 'obo';
  $fields{rna}{anatomyquality}{ontology_table}       = 'quality';
  $fields{rna}{lifestage}{type}                      = 'multiontology';
  $fields{rna}{lifestage}{label}                     = 'Life Stage';
  $fields{rna}{lifestage}{tab}                       = 'tab3';
  $fields{rna}{lifestage}{ontology_type}             = 'obo';
  $fields{rna}{lifestage}{ontology_table}            = 'lifestage';
  $fields{rna}{lifestagequality}{type}               = 'multiontology';
  $fields{rna}{lifestagequality}{label}              = 'Life Stage Quality';
  $fields{rna}{lifestagequality}{tab}                = 'tab3';
  $fields{rna}{lifestagequality}{ontology_type}      = 'obo';
  $fields{rna}{lifestagequality}{ontology_table}     = 'quality';
  $fields{rna}{molaffected}{type}                    = 'multiontology';
  $fields{rna}{molaffected}{label}                   = 'Molecule Affected';
  $fields{rna}{molaffected}{tab}                     = 'tab3';
  $fields{rna}{molaffected}{ontology_type}           = 'Molecule';
  $fields{rna}{molaffectedquality}{type}             = 'multiontology';
  $fields{rna}{molaffectedquality}{label}            = 'Mol Aff Quality';
  $fields{rna}{molaffectedquality}{tab}              = 'tab3';
  $fields{rna}{molaffectedquality}{ontology_type}    = 'obo';
  $fields{rna}{molaffectedquality}{ontology_table}   = 'quality';
  $fields{rna}{goprocess}{type}                      = 'multiontology';
  $fields{rna}{goprocess}{label}                     = 'GO Process';
  $fields{rna}{goprocess}{tab}                       = 'tab3';
  $fields{rna}{goprocess}{ontology_type}             = 'obo';
  $fields{rna}{goprocess}{ontology_table}            = 'goidprocess';
  $fields{rna}{goprocessquality}{type}               = 'multiontology';
  $fields{rna}{goprocessquality}{label}              = 'GO P Quality';
  $fields{rna}{goprocessquality}{tab}                = 'tab3';
  $fields{rna}{goprocessquality}{ontology_type}      = 'obo';
  $fields{rna}{goprocessquality}{ontology_table}     = 'quality';
  $fields{rna}{gofunction}{type}                     = 'multiontology';
  $fields{rna}{gofunction}{label}                    = 'GO Function';
  $fields{rna}{gofunction}{tab}                      = 'tab3';
  $fields{rna}{gofunction}{ontology_type}            = 'obo';
  $fields{rna}{gofunction}{ontology_table}           = 'goidfunction';
  $fields{rna}{gofunctionquality}{type}              = 'multiontology';
  $fields{rna}{gofunctionquality}{label}             = 'GO F Quality';
  $fields{rna}{gofunctionquality}{tab}               = 'tab3';
  $fields{rna}{gofunctionquality}{ontology_type}     = 'obo';
  $fields{rna}{gofunctionquality}{ontology_table}    = 'quality';
  $fields{rna}{gocomponent}{type}                    = 'multiontology';
  $fields{rna}{gocomponent}{label}                   = 'GO Component';
  $fields{rna}{gocomponent}{tab}                     = 'tab3';
  $fields{rna}{gocomponent}{ontology_type}           = 'obo';
  $fields{rna}{gocomponent}{ontology_table}          = 'goidcomponent';
  $fields{rna}{gocomponentquality}{type}             = 'multiontology';
  $fields{rna}{gocomponentquality}{label}            = 'GO C Quality';
  $fields{rna}{gocomponentquality}{tab}              = 'tab3';
  $fields{rna}{gocomponentquality}{ontology_type}    = 'obo';
  $fields{rna}{gocomponentquality}{ontology_table}   = 'quality';
  $fields{rna}{fromgenereg}{type}                    = 'toggle';
  $fields{rna}{fromgenereg}{label}                   = 'From Genereg';
  $fields{rna}{fromgenereg}{tab}                     = 'tab4';
  $fields{rna}{flaggenereg}{type}                    = 'toggle';
  $fields{rna}{flaggenereg}{label}                   = 'Flag Gene Reg';
  $fields{rna}{flaggenereg}{tab}                     = 'tab4';
  $fields{rna}{flaggeneticintxn}{type}               = 'toggle';
  $fields{rna}{flaggeneticintxn}{label}              = 'Flag Genetic Intxn';
  $fields{rna}{flaggeneticintxn}{tab}                = 'tab4';
  $fields{rna}{person}{type}                         = 'multiontology';
  $fields{rna}{person}{label}                        = 'Person Evidence';
  $fields{rna}{person}{tab}                          = 'tab4';
  $fields{rna}{person}{ontology_type}                = 'WBPerson';
  $fields{rna}{historyname}{type}                    = 'text';
  $fields{rna}{historyname}{label}                   = 'History Name';
  $fields{rna}{historyname}{tab}                     = 'tab4';
  $fields{rna}{movie}{type}                          = 'bigtext';
  $fields{rna}{movie}{label}                         = 'Movie';
  $fields{rna}{movie}{tab}                           = 'tab4';
  $fields{rna}{database}{type}                       = 'text';
  $fields{rna}{database}{label}                      = 'Database';
  $fields{rna}{database}{tab}                        = 'tab4';
  $fields{rna}{exprprofile}{type}                    = 'text';
  $fields{rna}{exprprofile}{label}                   = 'Expression Profile';
  $fields{rna}{exprprofile}{tab}                     = 'tab4';
  $fields{rna}{communitycurator}{type}               = 'ontology';
  $fields{rna}{communitycurator}{label}              = 'Community Curator';
  $fields{rna}{communitycurator}{tab}                = 'tab4';
  $fields{rna}{communitycurator}{ontology_type}      = 'WBPerson';
  $fields{rna}{communitycuratoremail}{type}          = 'text';
  $fields{rna}{communitycuratoremail}{label}         = 'Community Curator Email';
  $fields{rna}{communitycuratoremail}{tab}           = 'tab4';
  $fields{rna}{unregpaper}{type}                     = 'text';
  $fields{rna}{unregpaper}{label}                    = 'Unregistered Paper';
  $fields{rna}{unregpaper}{tab}                      = 'tab4';
  $fields{rna}{nodump}{type}                         = 'toggle';
  $fields{rna}{nodump}{label}                        = 'NO DUMP';
  $fields{rna}{nodump}{tab}                          = 'tab4';
  $fields{rna}{needsreview}{type}                    = 'toggle';
  $fields{rna}{needsreview}{label}                   = 'Needs Review';
  $fields{rna}{needsreview}{tab}                     = 'tab4';
  $datatypes{rna}{newRowSub}                         = \&newRowRna;
  $datatypes{rna}{label}                             = 'rnai';
  @{ $datatypes{rna}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormRnaFields

sub initWormSqfFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{sqf} }, "Tie::IxHash";
  $fields{sqf}{id}{type}                             = 'text';
  $fields{sqf}{id}{label}                            = 'pgid';
  $fields{sqf}{id}{tab}                              = 'tab1';
  $fields{sqf}{name}{type}                           = 'ontology';
  $fields{sqf}{name}{label}                          = 'Name';
  $fields{sqf}{name}{tab}                            = 'tab1';
  $fields{sqf}{name}{ontology_type}                  = 'WBSeqFeat';
  $fields{sqf}{publicname}{type}                     = 'text';
  $fields{sqf}{publicname}{label}                    = 'Public Name';
  $fields{sqf}{publicname}{tab}                      = 'tab1';
  $fields{sqf}{othername}{type}                      = 'text';
  $fields{sqf}{othername}{label}                     = 'Other Name';
  $fields{sqf}{othername}{tab}                       = 'tab1';
  $fields{sqf}{description}{type}                    = 'bigtext';
  $fields{sqf}{description}{label}                   = 'Description';
  $fields{sqf}{description}{tab}                     = 'tab1';
#   $fields{sqf}{species}{type}                        = 'dropdown';
  $fields{sqf}{species}{type}                        = 'ontology';
  $fields{sqf}{species}{label}                       = 'Species';
  $fields{sqf}{species}{tab}                         = 'tab1';
#   $fields{sqf}{species}{dropdown_type}               = 'species';
  $fields{sqf}{species}{ontology_type}               = 'obo';
  $fields{sqf}{species}{ontology_table}              = 'species';
  $fields{sqf}{deprecated}{type}                     = 'bigtext';
  $fields{sqf}{deprecated}{label}                    = 'Deprecated';
  $fields{sqf}{deprecated}{tab}                      = 'tab1';
  $fields{sqf}{paper}{type}                          = 'multiontology';
  $fields{sqf}{paper}{label}                         = 'Paper';
  $fields{sqf}{paper}{tab}                           = 'tab1';
  $fields{sqf}{paper}{ontology_type}                 = 'WBPaper';
  $fields{sqf}{person}{type}                         = 'multiontology';
  $fields{sqf}{person}{label}                        = 'Person';
  $fields{sqf}{person}{tab}                          = 'tab1';
  $fields{sqf}{person}{ontology_type}                = 'WBPerson';
  $fields{sqf}{analysis}{type}                       = 'text';
  $fields{sqf}{analysis}{label}                      = 'Analysis';
  $fields{sqf}{analysis}{tab}                        = 'tab1';
  $fields{sqf}{method}{type}                         = 'dropdown';
  $fields{sqf}{method}{label}                        = 'Method';
  $fields{sqf}{method}{tab}                          = 'tab2';
  $fields{sqf}{method}{dropdown_type}                = 'seqfeatmethod';
  $fields{sqf}{soterm}{type}                         = 'ontology';
  $fields{sqf}{soterm}{label}                        = 'SO';
  $fields{sqf}{soterm}{tab}                          = 'tab2';
  $fields{sqf}{soterm}{ontology_type}                = 'obo';
  $fields{sqf}{soterm}{ontology_table}               = 'soid';
  $fields{sqf}{dnatext}{type}                        = 'bigtext';
  $fields{sqf}{dnatext}{label}                       = 'DNA text';
  $fields{sqf}{dnatext}{tab}                         = 'tab2';
  $fields{sqf}{flanka}{type}                         = 'text';
  $fields{sqf}{flanka}{label}                        = 'Flanking Sequence A';
  $fields{sqf}{flanka}{tab}                          = 'tab2';
  $fields{sqf}{flankb}{type}                         = 'text';
  $fields{sqf}{flankb}{label}                        = 'Flanking Sequence B';
  $fields{sqf}{flankb}{tab}                          = 'tab2';
  $fields{sqf}{target}{type}                         = 'text';
  $fields{sqf}{target}{label}                        = 'Mapping Target';
  $fields{sqf}{target}{tab}                          = 'tab2';
  $fields{sqf}{sequence}{type}                       = 'text';
  $fields{sqf}{sequence}{label}                      = 'Sequence';
  $fields{sqf}{sequence}{tab}                        = 'tab2';
#   $fields{sqf}{mergedinto}{type}                     = 'text';
#   $fields{sqf}{mergedinto}{label}                    = 'Merged Into';
#   $fields{sqf}{mergedinto}{tab}                      = 'tab2';
  $fields{sqf}{mergedinto}{type}                     = 'ontology';
  $fields{sqf}{mergedinto}{label}                    = 'Merged Into';
  $fields{sqf}{mergedinto}{tab}                      = 'tab2';
  $fields{sqf}{mergedinto}{ontology_type}            = 'WBSeqFeat';
  $fields{sqf}{curator}{type}                        = 'dropdown';
  $fields{sqf}{curator}{label}                       = 'Curator';
  $fields{sqf}{curator}{tab}                         = 'tab2';
  $fields{sqf}{curator}{dropdown_type}               = 'curator';
  $fields{sqf}{wbgene}{type}                         = 'multiontology';
  $fields{sqf}{wbgene}{label}                        = 'readOnly WBGene';
  $fields{sqf}{wbgene}{tab}                          = 'tab3';
  $fields{sqf}{wbgene}{ontology_type}                = 'WBGene';
  $fields{sqf}{cds}{type}                            = 'text';
  $fields{sqf}{cds}{label}                           = 'readOnly CDS';
  $fields{sqf}{cds}{tab}                             = 'tab3';
  $fields{sqf}{operon}{type}                         = 'text';
  $fields{sqf}{operon}{label}                        = 'readOnly Operon';
  $fields{sqf}{operon}{tab}                          = 'tab3';
  $fields{sqf}{construct}{type}                      = 'multiontology';
  $fields{sqf}{construct}{label}                     = 'readOnly Construct';
  $fields{sqf}{construct}{tab}                       = 'tab3';
  $fields{sqf}{construct}{ontology_type}             = 'WBConstruct';
  $fields{sqf}{boundbyproduct}{type}                 = 'multiontology';
  $fields{sqf}{boundbyproduct}{label}                = 'Bound By Product Of';
  $fields{sqf}{boundbyproduct}{tab}                  = 'tab3';
  $fields{sqf}{boundbyproduct}{ontology_type}        = 'WBGene';
  $fields{sqf}{trascriptionfactor}{type}             = 'text';
  $fields{sqf}{trascriptionfactor}{label}            = 'Transcription Factor';
  $fields{sqf}{trascriptionfactor}{tab}              = 'tab3';
  $fields{sqf}{confidential}{type}                   = 'bigtext';
  $fields{sqf}{confidential}{label}                  = 'Confidential Remark';
  $fields{sqf}{confidential}{tab}                    = 'tab3';
  $fields{sqf}{remark}{type}                         = 'bigtext';
  $fields{sqf}{remark}{label}                        = 'Remark';
  $fields{sqf}{remark}{tab}                          = 'tab3';
  $fields{sqf}{score}{type}                          = 'text';
  $fields{sqf}{score}{label}                         = 'Score';
  $fields{sqf}{score}{tab}                           = 'tab3';
  $datatypes{sqf}{newRowSub}                         = \&newRowSqf;
  $datatypes{sqf}{label}                             = 'Sequence Feature';
  @{ $datatypes{sqf}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormSqfFields

sub initWormTrpFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{trp} }, "Tie::IxHash";
  $fields{trp}{id}{type}                             = 'text';
  $fields{trp}{id}{label}                            = 'pgid';
  $fields{trp}{id}{tab}                              = 'tab1';
  $fields{trp}{name}{type}                           = 'text';
  $fields{trp}{name}{label}                          = 'Name';
  $fields{trp}{name}{tab}                            = 'tab1';
  $fields{trp}{publicname}{type}                     = 'text';
  $fields{trp}{publicname}{label}                    = 'Public Name';
  $fields{trp}{publicname}{tab}                      = 'all';
  $fields{trp}{synonym}{type}                        = 'text';
  $fields{trp}{synonym}{label}                       = 'Synonym';
  $fields{trp}{synonym}{tab}                         = 'tab1';
  $fields{trp}{summary}{type}                        = 'bigtext';
  $fields{trp}{summary}{label}                       = 'Summary';
  $fields{trp}{summary}{tab}                         = 'tab1';
  $fields{trp}{construct}{type}                      = 'multiontology';
  $fields{trp}{construct}{label}                     = 'Construct';
  $fields{trp}{construct}{tab}                       = 'tab1';
  $fields{trp}{construct}{ontology_type}             = 'WBConstruct';
  $fields{trp}{coinjectionconstruct}{type}           = 'multiontology';
  $fields{trp}{coinjectionconstruct}{label}          = 'Coinjection Construct';
  $fields{trp}{coinjectionconstruct}{tab}            = 'tab1';
  $fields{trp}{coinjectionconstruct}{ontology_type}  = 'WBConstruct';
  $fields{trp}{coinjection}{type}                    = 'text';
  $fields{trp}{coinjection}{label}                   = 'Coinjection';
  $fields{trp}{coinjection}{tab}                     = 'tab1';
  $fields{trp}{constructionsummary}{type}            = 'bigtext';
  $fields{trp}{constructionsummary}{label}           = 'Construction Summary';
  $fields{trp}{constructionsummary}{tab}             = 'tab1';
  $fields{trp}{mergedinto}{type}                     = 'ontology';		# TODO create this new table for what an duplicated invalid transgene merges into
  $fields{trp}{mergedinto}{label}                    = 'Merged Into';
  $fields{trp}{mergedinto}{tab}                      = 'tab1';
  $fields{trp}{mergedinto}{ontology_type}            = 'Transgene';
  $fields{trp}{paper}{type}                          = 'multiontology';
  $fields{trp}{paper}{label}                         = 'Paper';
  $fields{trp}{paper}{tab}                           = 'tab1';
  $fields{trp}{paper}{ontology_type}                 = 'WBPaper';

  $fields{trp}{integratedfrom}{type}                 = 'ontology';
  $fields{trp}{integratedfrom}{label}                = 'Integrated From';
  $fields{trp}{integratedfrom}{tab}                  = 'tab2';
  $fields{trp}{integratedfrom}{ontology_type}        = 'Transgene';
#   $fields{trp}{integration_method}{type}             = 'dropdown';
#   $fields{trp}{integration_method}{label}            = 'Integration Method';
#   $fields{trp}{integration_method}{tab}              = 'tab2';
#   $fields{trp}{integration_method}{dropdown_type}    = 'integrationmethod';
  $fields{trp}{integration_method}{type}             = 'ontology';
  $fields{trp}{integration_method}{label}            = 'Integration Method';
  $fields{trp}{integration_method}{tab}              = 'tab2';
  $fields{trp}{integration_method}{ontology_type}    = 'obo';
  $fields{trp}{integration_method}{ontology_table}   = 'integrationmethod';
  $fields{trp}{variation}{type}                      = 'ontology';
  $fields{trp}{variation}{label}                     = 'Corresponding Variation';
  $fields{trp}{variation}{tab}                       = 'tab2';
  $fields{trp}{variation}{ontology_type}             = 'obo';
  $fields{trp}{variation}{ontology_table}            = 'variation';
  $fields{trp}{map}{type}                            = 'multidropdown';
  $fields{trp}{map}{label}                           = 'Map';
  $fields{trp}{map}{tab}                             = 'tab2';
  $fields{trp}{map}{dropdown_type}                   = 'chromosome';
  $fields{trp}{map_paper}{type}                      = 'multiontology';
  $fields{trp}{map_paper}{label}                     = 'Map Paper';
  $fields{trp}{map_paper}{tab}                       = 'tab2';
  $fields{trp}{map_paper}{ontology_type}             = 'WBPaper';
  $fields{trp}{map_person}{type}                     = 'multiontology';
  $fields{trp}{map_person}{label}                    = 'Map Person';
  $fields{trp}{map_person}{tab}                      = 'tab2';
  $fields{trp}{map_person}{ontology_type}            = 'WBPerson';
  $fields{trp}{laboratory}{type}                     = 'multiontology';
  $fields{trp}{laboratory}{label}                    = 'Laboratory';
  $fields{trp}{laboratory}{tab}                      = 'tab2';
  $fields{trp}{laboratory}{ontology_type}            = 'obo';
  $fields{trp}{laboratory}{ontology_table}           = 'laboratory';
  $fields{trp}{strain}{type}                         = 'text';
  $fields{trp}{strain}{label}                        = 'Strain';
  $fields{trp}{strain}{tab}                          = 'tab2';
  $fields{trp}{curator}{type}                        = 'dropdown';
  $fields{trp}{curator}{label}                       = 'Curator';
  $fields{trp}{curator}{tab}                         = 'tab3';
  $fields{trp}{curator}{dropdown_type}               = 'curator';
  $fields{trp}{marker_for}{type}                     = 'text';
  $fields{trp}{marker_for}{label}                    = 'Marker for';
  $fields{trp}{marker_for}{tab}                      = 'tab3';
  $fields{trp}{marker_for_paper}{type}               = 'multiontology';
  $fields{trp}{marker_for_paper}{label}              = 'Marker for Paper';
  $fields{trp}{marker_for_paper}{tab}                = 'tab3';
  $fields{trp}{marker_for_paper}{ontology_type}      = 'WBPaper';
  $fields{trp}{humandoid}{type}                      = 'multiontology';
  $fields{trp}{humandoid}{label}                     = 'Disease';
  $fields{trp}{humandoid}{tab}                       = 'tab3';
  $fields{trp}{humandoid}{ontology_type}             = 'obo';
  $fields{trp}{humandoid}{ontology_table}            = 'humando';
  $fields{trp}{diseasepaper}{type}                   = 'multiontology';
  $fields{trp}{diseasepaper}{label}                  = 'Disease Paper';
  $fields{trp}{diseasepaper}{tab}                    = 'tab3';
  $fields{trp}{diseasepaper}{ontology_type}          = 'WBPaper';
#   $fields{trp}{species}{type}                        = 'text';
#   $fields{trp}{species}{label}                       = 'Species';
  $fields{trp}{species}{type}                        = 'ontology';
  $fields{trp}{species}{label}                       = 'Species';
  $fields{trp}{species}{tab}                         = 'tab3';
  $fields{trp}{species}{ontology_type}               = 'obo';
  $fields{trp}{species}{ontology_table}              = 'species';
#   $fields{trp}{searchnew}{type}                      = 'queryonly';		# leave this here as sample of how to use queryonly fields
#   $fields{trp}{searchnew}{label}                     = 'Search new';
#   $fields{trp}{searchnew}{tab}                       = 'tab3';
#   $fields{trp}{searchnew}{queryonlySub}              = \&checkTrpQueryonly;
  $fields{trp}{objpap_falsepos}{type}                = 'toggle';
  $fields{trp}{objpap_falsepos}{label}               = 'Fail';
  $fields{trp}{objpap_falsepos}{tab}                 = 'tab3';
  $fields{trp}{remark}{type}                         = 'bigtext';
  $fields{trp}{remark}{label}                        = 'Remark';
  $fields{trp}{remark}{tab}                          = 'tab3';
  $fields{trp}{cgcremark}{type}                      = 'bigtext';
  $fields{trp}{cgcremark}{label}                     = 'CGC Remark';
  $fields{trp}{cgcremark}{tab}                       = 'tab3';
  $fields{trp}{person}{type}                         = 'multiontology';
  $fields{trp}{person}{label}                        = 'Person';
  $fields{trp}{person}{tab}                          = 'tab3';
  $fields{trp}{person}{ontology_type}                = 'WBPerson';
  $datatypes{trp}{newRowSub}                         = \&newRowTrp;
  $datatypes{trp}{label}                             = 'transgene';
  @{ $datatypes{trp}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormTrpFields

### END FIELDS ###


### NEW ROW ###

sub insertToPostgresTableAndHistory {		# to create new rows, it is easier to have this sub in multiple <mod>OA.pm files than change the database in the helperOA.pm 
  my ($table, $joinkey, $newValue) = @_;
  my $returnValue = '';
  my $result = $dbh->prepare( "INSERT INTO $table VALUES ('$joinkey', '$newValue')" );
  $result->execute() or $returnValue .= "ERROR, failed to insert to $table &insertToPostgresTableAndHistory\n";
  $result = $dbh->prepare( "INSERT INTO ${table}_hst VALUES ('$joinkey', '$newValue')" );
  $result->execute() or $returnValue .= "ERROR, failed to insert to ${table}_hst &insertToPostgresTableAndHistory\n";
  unless ($returnValue) { $returnValue = 'OK'; }
  return $returnValue;
} # sub insertToPostgresTableAndHistory

sub getHighestExprId {		# look at all exp_name, get the highest number and return
  my $highest = 0;
  my $result = $dbh->prepare( "SELECT exp_name FROM exp_name WHERE exp_name ~ '^Expr'" ); $result->execute(); 
  while (my @row = $result->fetchrow()) { if ($row[0]) { $row[0] =~ s/Expr//; if ($row[0] > $highest) { $highest = $row[0]; } } }
  return $highest; }
sub getHighestPrtId {		# look at all prt_name, get the highest number and return
  my $highest = 0;
  my $result = $dbh->prepare( "SELECT prt_processid FROM prt_processid WHERE prt_processid ~ '^WBbiopr:'" ); $result->execute(); 
  while (my @row = $result->fetchrow()) { if ($row[0]) { $row[0] =~ s/WBbiopr://; if ($row[0] > $highest) { $highest = $row[0]; } } }
  return $highest; }
sub getHighestRnaiId {		# look at all exp_name, get the highest number and return
  my $highest = 0;
  my $result = $dbh->prepare( "SELECT rna_name FROM rna_name WHERE rna_name ~ '^WBRNAi'" ); $result->execute(); 
  while (my @row = $result->fetchrow()) { if ($row[0]) { $row[0] =~ s/WBRNAi//; if ($row[0] > $highest) { $highest = $row[0]; } } }
  return $highest; }
sub getNewIntId {		# make sure to change the interaction ticket form if we change the format of the interaction IDs 
  my ($curator) = @_;
  my $result = $dbh->prepare( "SELECT * FROM int_index ORDER BY int_index::INTEGER DESC;" ); $result->execute(); 
  my @row = $result->fetchrow(); my $highest = $row[1]; my $newNumber = $highest + 1; my $intId = &pad9Zeros($newNumber); my $returnValue = '';
  $result = $dbh->prepare( "INSERT INTO int_index VALUES ('$intId', '$newNumber', '$curator')" );
  $result->execute() or $returnValue .= "ERROR, failed to insert to int_index &getNewIntId\n";
  unless ($returnValue) { $returnValue = $intId; }
  return $returnValue; }

sub newRowAbp {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('abp_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowApp {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('app_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowCns {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('cns_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $cnsId = &pad8Zeros($newPgid);
    ($returnValue)  = &insertToPostgresTableAndHistory('cns_name', $newPgid, "WBCnstr$cnsId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; }
  return $returnValue; }
sub newRowCon {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('con_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $date = &getPgDate(); my $notOk = '';
    ($returnValue)  = &insertToPostgresTableAndHistory('con_lastupdate', $newPgid, $date); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    ($returnValue)  = &insertToPostgresTableAndHistory('con_curhistory', $newPgid, $newPgid); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    if ($notOk) { $returnValue = $notOk; } }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowDis {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('dis_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $date = &getPgDate(); my $notOk = '';
    ($returnValue)  = &insertToPostgresTableAndHistory('dis_lastupdateexpmod', $newPgid, $date); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    ($returnValue)  = &insertToPostgresTableAndHistory('dis_lastupdatedisrel', $newPgid, $date); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    ($returnValue)  = &insertToPostgresTableAndHistory('dis_curhistory', $newPgid, $newPgid); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    if ($notOk) { $returnValue = $notOk; } }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowDit {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('dit_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $date = &getPgDate(); my $notOk = '';
    ($returnValue)  = &insertToPostgresTableAndHistory('dit_lastupdate', $newPgid, $date); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    ($returnValue)  = &insertToPostgresTableAndHistory('dit_curhistory', $newPgid, $newPgid); 
    unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
    if ($notOk) { $returnValue = $notOk; } }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowExp {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('exp_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my ($newExprId) = &getHighestExprId(); $newExprId++;
    ($returnValue)  = &insertToPostgresTableAndHistory('exp_name', $newPgid, "Expr$newExprId"); }
  if ($returnValue eq 'OK') {
    my $endogenous = 'Endogenous';
    ($returnValue)  = &insertToPostgresTableAndHistory('exp_endogenous', $newPgid, $endogenous); }
  if ($returnValue eq 'OK') {
    my $part_of = 'part_of';
    ($returnValue)  = &insertToPostgresTableAndHistory('exp_relanatomy', $newPgid, $part_of); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; }
  return $returnValue; }
sub newRowGcl {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('gcl_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowGop {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('gop_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $date = &getPgDate();
    ($returnValue)  = &insertToPostgresTableAndHistory('gop_lastupdate', $newPgid, $date); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowGrg {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/; my $notOk = '';
  my ($returnValue) = &insertToPostgresTableAndHistory('grg_curator', $newPgid, $curator);
  unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
  my ($newIntId) = &getNewIntId($curator_two);							# get new intId 
  unless ($newIntId =~ m/^\d+$/) { $notOk .= $newIntId; }					# if not an int_index joinkey it's an error
  ($returnValue)  = &insertToPostgresTableAndHistory('grg_intid', $newPgid, "WBInteraction$newIntId");	# add to interaction id
  unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
  if ($notOk) { $returnValue = $notOk; }							# if error, return error message
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowInt {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/; my $notOk = '';
  my ($returnValue) = &insertToPostgresTableAndHistory('int_curator', $newPgid, $curator);	# add curator
  unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
  my ($newIntId) = &getNewIntId($curator_two);							# get new intId 
  unless ($newIntId =~ m/^\d+$/) { $notOk .= $newIntId; }					# if not an int_index joinkey it's an error
  ($returnValue)  = &insertToPostgresTableAndHistory('int_name', $newPgid, "WBInteraction$newIntId");	# add to interaction name
  unless ($returnValue eq 'OK') { $notOk .= $returnValue; }
  if ($notOk) { $returnValue = $notOk; }							# if error, return error message
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 					# if it's ok, return newPgid
  return $returnValue; }
sub newRowMop {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('mop_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $molId = &pad8Zeros($newPgid); 
    ($returnValue)  = &insertToPostgresTableAndHistory('mop_name', $newPgid, "WBMol:$molId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowMov {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('mov_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $movId = &pad10Zeros($newPgid);
    ($returnValue)  = &insertToPostgresTableAndHistory('mov_name', $newPgid, "WBMovie$movId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowPic {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('pic_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $picId = &pad10Zeros($newPgid);
    ($returnValue)  = &insertToPostgresTableAndHistory('pic_name', $newPgid, "WBPicture$picId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowPro {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('pro_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $topicpaperstatus = 'relevant';
    ($returnValue)  = &insertToPostgresTableAndHistory('pro_topicpaperstatus', $newPgid, $topicpaperstatus); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowPrt {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('prt_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my ($newPrtId) = &getHighestPrtId(); $newPrtId++;
    my $prtId = &pad8Zeros($newPrtId); 
    ($returnValue)  = &insertToPostgresTableAndHistory('prt_processid', $newPgid, "WBbiopr:$prtId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; }
  return $returnValue; }
sub newRowPtg {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('ptg_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowRna {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('rna_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my ($newRnaiId) = &getHighestRnaiId(); $newRnaiId++;
    my $rnaiId = &pad8Zeros($newRnaiId); 
    ($returnValue)  = &insertToPostgresTableAndHistory('rna_name', $newPgid, "WBRNAi$rnaiId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; }
  return $returnValue; }
sub newRowSqf {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('sqf_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $sqfId = &pad8Zeros($newPgid);
    ($returnValue)  = &insertToPostgresTableAndHistory('sqf_name', $newPgid, "WBsf$sqfId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; }
  return $returnValue; }
sub newRowTrp {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('trp_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $trpId = &pad8Zeros($newPgid);
    ($returnValue)  = &insertToPostgresTableAndHistory('trp_name', $newPgid, "WBTransgene$trpId"); }
  if ($returnValue eq 'OK') { $returnValue = $newPgid; }
  return $returnValue; }

### END NEW ROW ###



### CONSTRAINTS ###

sub checkGopConstraints {
  my ($allDataTableIds) = @_;
  my @ids = split/,/, $allDataTableIds; my $joinkeys = join"','", @ids; 
  my $returnMessage = "";
  my $result = $dbh->prepare( "SELECT * FROM gop_lastupdate WHERE joinkey IN ('$joinkeys')" );
  $result->execute(); 
  while (my @row = $result->fetchrow()) { if ($row[1]) { 
    my ($isPgTimestamp) = &checkValueIsPgTimestamp($row[1]); 
    if ($isPgTimestamp) { $returnMessage .= "pgid $row[0] : $isPgTimestamp"; } } }
  return $returnMessage;
} # sub checkGopConstraints

sub checkValueIsPgTimestamp {
  my ($val) = @_;
  if ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}\.\d+\-\d{2}$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}\.\d+$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}$/) { return; }
  elsif ($val =~ m/^\d{4}\-\d{2}\-\d{2}$/) { return; }
  else { return "$val not in postgres timestamp format<br />\n"; }
} # sub isPgTimestamp

sub checkAppConstraints {
  my ($allDataTableIds) = @_;
  my @ids = split/,/, $allDataTableIds; my $joinkeys = join"','", @ids; 
  my $returnMessage = ""; my %hash;
  my @tables = qw( term nbp variation transgene strain rearrangement );
  foreach my $table (@tables) {
    my $pgtable = 'app_' . $table;
    my $result = $dbh->prepare( "SELECT * FROM $pgtable WHERE joinkey IN ('$joinkeys')" );
    $result->execute(); 
    while (my @row = $result->fetchrow()) { 
      if ($row[1]) { $hash{$row[0]}{$table}++; } } }
  foreach my $pgid (@ids) {
    if ($hash{$pgid}{term}) { 1; }					# ok, has phenotype
      elsif ( ($hash{$pgid}{nbp}) && ($hash{$pgid}{variation}) ) { 1; }	# ok has variation and has nbp
      else { $returnMessage .= "$pgid has neither phenotype term, nor both nbp and variation.<br/>\n"; }
    my $count = 0;
    if ($hash{$pgid}{variation}) { $count++; }
    if ($hash{$pgid}{transgene}) { $count++; }
    if ($hash{$pgid}{strain}) { $count++; }
    if ($hash{$pgid}{rearrangement}) { $count++; }
    if ($count != 1) { $returnMessage .= "$pgid has $count different types instead of exactly one.<br/>\n"; } }
  unless ($returnMessage) { $returnMessage = 'OK'; }
  return $returnMessage;
} # sub checkAppConstraints

### END CONSTRAINTS ###


### QUERY ONLY ###

# leaving this here as a sample if needed in the future
# sub checkTrpQueryonly {		# sample query only field with a made-up query.  should filter out joinkeys, and probably order by desc timestamp.
#   my ($joinkeys) = @_;							# joinkeys already in dataTable to exclude from query
#   return "SELECT joinkey FROM trp_name WHERE joinkey NOT IN ('$joinkeys') AND trp_name ~ 'arIs' ORDER BY trp_timestamp DESC";
# } # sub checkTrpQueryonly

### END QUERY ONLY ###



### ONTOLOGY / MULTIONTOLOGY ###

### AUTOCOMPLETE ###

sub setAnySimpleAutocompleteValues {
  my ($ontology_type) = @_;
  my %data;
  if ($ontology_type eq 'curator') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"Juancarlos Chan"}    = "Juancarlos Chan ( WBPerson1823 ) ";
    $data{$ontology_type}{name}{"Wen Chen"}           = "Wen Chen ( WBPerson101 ) ";
    $data{$ontology_type}{name}{"Chris"}              = "Chris ( WBPerson2987 ) ";
    $data{$ontology_type}{name}{"John DeModena"}      = "John DeModena ( WBPerson133 ) ";
    $data{$ontology_type}{name}{"James Done"}         = "James Done ( WBPerson17622 ) ";
    $data{$ontology_type}{name}{"Kevin Howe"}         = "Kevin Howe ( WBPerson3111 ) ";
    $data{$ontology_type}{name}{"Snehalata Kadam"}    = "Snehalata Kadam ( WBPerson12884 ) ";
    $data{$ontology_type}{name}{"Ranjana Kishore"}    = "Ranjana Kishore ( WBPerson324 ) ";
    $data{$ontology_type}{name}{"Raymond Lee"}        = "Raymond Lee ( WBPerson363 ) ";
    $data{$ontology_type}{name}{"Yuling Li"}          = "Yuling Li ( WBPerson11187 ) ";
    $data{$ontology_type}{name}{"Daniela Raciti"}     = "Daniela Raciti ( WBPerson12028 ) ";
    $data{$ontology_type}{name}{"Arun Rangarajan"}    = "Arun Rangarajan ( WBPerson4793 ) ";
    $data{$ontology_type}{name}{"Gary Schindelman"}   = "Gary Schindelman ( WBPerson557 ) ";
    $data{$ontology_type}{name}{"Mary Ann Tuli"}      = "Mary Ann Tuli ( WBPerson2970 ) "; 
    $data{$ontology_type}{name}{"Kimberly Van Auken"} = "Kimberly Van Auken ( WBPerson1843 ) ";
    $data{$ontology_type}{name}{"Xiaodong Wang"}      = "Xiaodong Wang ( WBPerson1760 ) ";
    $data{$ontology_type}{name}{"Karen Yook"}         = "Karen Yook ( WBPerson712 ) ";
    $data{$ontology_type}{name}{"Community Curator"}  = "Community Curator ( WBPerson29819 ) ";
    $data{$ontology_type}{name}{"Unknown Curator"}    = "Unknown Curator ( WBPerson13481 ) ";
    $data{$ontology_type}{name}{"Igor Antoshechkin"}  = "Igor Antoshechkin ( WBPerson22 ) ";
    $data{$ontology_type}{name}{"Carol Bastiani"}     = "Carol Bastiani ( WBPerson48 ) ";
    $data{$ontology_type}{name}{"Keith Bradnam"}      = "Keith Bradnam ( WBPerson1971 ) ";
    $data{$ontology_type}{name}{"Chao-Kung Chen"}     = "Chao-Kung Chen ( WBPerson1845 ) ";
    $data{$ontology_type}{name}{"Paul Davis"}         = "Paul Davis ( WBPerson1983 ) ";
    $data{$ontology_type}{name}{"Jolene Fernandes"}   = "Jolene Fernandes ( WBPerson2021 ) ";
    $data{$ontology_type}{name}{"Uhma Ganesan"}       = "Uhma Ganesan ( WBPerson13088 ) ";
    $data{$ontology_type}{name}{"Josh Jaffery"}       = "Josh Jaffery ( WBPerson5196 ) ";
    $data{$ontology_type}{name}{"Sylvia Martinelli"}  = "Sylvia Martinelli ( WBPerson1250 ) ";
    $data{$ontology_type}{name}{"Tuco"}               = "Tuco ( WBPerson480 ) ";
    $data{$ontology_type}{name}{"Erich Schwarz"}      = "Erich Schwarz ( WBPerson567 ) ";
    $data{$ontology_type}{name}{"Gary Williams"}      = "Gary Williams ( WBPerson4025 ) "; }
  elsif ($ontology_type eq 'clonality') {
    $data{$ontology_type}{name}{"Polyclonal"} = "Polyclonal";
    $data{$ontology_type}{name}{"Monoclonal"} = "Monoclonal"; }
  elsif ($ontology_type eq 'animal') {
    $data{$ontology_type}{name}{"Rabbit"}       = "Rabbit";
    $data{$ontology_type}{name}{"Mouse"}        = "Mouse";
    $data{$ontology_type}{name}{"Rat"}          = "Rat";
    $data{$ontology_type}{name}{"Guinea_pig"}   = "Guinea_pig";
    $data{$ontology_type}{name}{"Chicken"}      = "Chicken";
    $data{$ontology_type}{name}{"Goat"}         = "Goat";
    $data{$ontology_type}{name}{"Other_animal"} = "Other_animal"; }
  elsif ($ontology_type eq 'antigen') {
    $data{$ontology_type}{name}{"Peptide"}       = "Peptide";
    $data{$ontology_type}{name}{"Protein"}       = "Protein";
    $data{$ontology_type}{name}{"Other_antigen"} = "Other_antigen"; }
  elsif ($ontology_type eq 'abpsource') {
    $data{$ontology_type}{name}{"Original_publication"}  = "Original_publication";
    $data{$ontology_type}{name}{"No_original_reference"} = "No_original_reference"; }
  elsif ($ontology_type eq 'condescription') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"Concise_description"}             = "Concise_description";
    $data{$ontology_type}{name}{"Automated_description"}           = "Automated_description";
#     $data{$ontology_type}{name}{"Human_disease_relevance"}         = "Human_disease_relevance";	# moved to disease OA  2013 01 25
    $data{$ontology_type}{name}{"Provisional_description"}         = "Provisional_description";
    $data{$ontology_type}{name}{"Sequence_features"}               = "Sequence_features";
    $data{$ontology_type}{name}{"Functional_pathway"}              = "Functional_pathway";
    $data{$ontology_type}{name}{"Functional_physical_interaction"} = "Functional_physical_interaction";
    $data{$ontology_type}{name}{"Biological_process"}              = "Biological_process";
    $data{$ontology_type}{name}{"Molecular_function"}              = "Molecular_function";
    $data{$ontology_type}{name}{"Expression"}                      = "Expression";
    $data{$ontology_type}{name}{"Other_description"}               = "Other_description"; }
  elsif ($ontology_type eq 'exprqualifier') {
    $data{$ontology_type}{name}{"NOT"}       = "NOT";
    $data{$ontology_type}{name}{"Certain"}   = "Certain";
    $data{$ontology_type}{name}{"Partial"}   = "Partial";
    $data{$ontology_type}{name}{"Uncertain"} = "Uncertain"; }
  elsif ($ontology_type eq 'exprtype') {
    $data{$ontology_type}{name}{"Antibody"}                        = "Antibody";
    $data{$ontology_type}{name}{"Cis_regulatory_element"}          = "Cis_regulatory_element";
    $data{$ontology_type}{name}{"Reporter_gene"}                   = "Reporter_gene";
    $data{$ontology_type}{name}{"In_Situ"}                         = "In_Situ";
    $data{$ontology_type}{name}{"RT_PCR"}                          = "RT_PCR";
    $data{$ontology_type}{name}{"EPIC"}                            = "EPIC";
    $data{$ontology_type}{name}{"Northern"}                        = "Northern";
    $data{$ontology_type}{name}{"Western"}                         = "Western"; }
  elsif ($ontology_type eq 'gclstatus') {
    $data{$ontology_type}{name}{"done"} = "done";
    $data{$ontology_type}{name}{"incomplete"} = "incomplete";
    $data{$ontology_type}{name}{"recheck"} = "recheck"; }
  elsif ($ontology_type eq 'gcltype') {
    $data{$ontology_type}{name}{"molecular"}          = "molecular";
    $data{$ontology_type}{name}{"phenotype"}          = "phenotype";
    $data{$ontology_type}{name}{"phenotype-function"} = "phenotype-function";
    $data{$ontology_type}{name}{"other"}              = "other"; }
  elsif ($ontology_type eq 'goontology') {
    $data{$ontology_type}{name}{"F"} = "F ( mol ) ";
    $data{$ontology_type}{name}{"P"} = "P ( bio ) ";
    $data{$ontology_type}{name}{"C"} = "C ( cell ) "; }
  elsif ($ontology_type eq 'goproject') {
    $data{$ontology_type}{name}{"Reference Genomes"}           = "Reference Genomes";
    $data{$ontology_type}{name}{"PAINT"}                       = "PAINT";
    $data{$ontology_type}{name}{"RNAi Phenotype2GO"}           = "RNAi Phenotype2GO";
    $data{$ontology_type}{name}{"Variation phenotype2GO"}      = "Variation phenotype2GO";
    $data{$ontology_type}{name}{"Human Disease Gene Ortholog"} = "Human Disease Gene Ortholog"; }
  elsif ($ontology_type eq 'goinference') {
    $data{$ontology_type}{name}{"IDA"} = "IDA";
    $data{$ontology_type}{name}{"IEA"} = "IEA";
    $data{$ontology_type}{name}{"IEP"} = "IEP";
    $data{$ontology_type}{name}{"IGI"} = "IGI";
    $data{$ontology_type}{name}{"IMP"} = "IMP";
    $data{$ontology_type}{name}{"IPI"} = "IPI";
    $data{$ontology_type}{name}{"ISS"} = "ISS";
    $data{$ontology_type}{name}{"NAS"} = "NAS";
    $data{$ontology_type}{name}{"ND"}  = "ND";
    $data{$ontology_type}{name}{"IC"}  = "IC";
    $data{$ontology_type}{name}{"TAS"} = "TAS";
    $data{$ontology_type}{name}{"RCA"} = "RCA";
    $data{$ontology_type}{name}{"EXP"} = "EXP";
    $data{$ontology_type}{name}{"ISA"} = "ISA";
    $data{$ontology_type}{name}{"ISO"} = "ISO";
    $data{$ontology_type}{name}{"ISM"} = "ISM";
    $data{$ontology_type}{name}{"IGC"} = "IGC"; }
  elsif ($ontology_type eq 'goaccession') {
    $data{$ontology_type}{name}{"GO_REF:0000011"} = "Hidden Markov Models ( GO_REF:0000011 ) ";
    $data{$ontology_type}{name}{"GO_REF:0000012"} = "Pairwise alignment ( GO_REF:0000012 ) ";
    $data{$ontology_type}{name}{"GO_REF:0000015"} = "Use of the ND evidence code for GO terms ( GO_REF:0000015 ) ";
    $data{$ontology_type}{name}{"GO_REF:0000033"} = "Annotation inferences using phylogenetic trees ( GO_REF:0000033 ) ";
    $data{$ontology_type}{name}{"GO_REF:0000024"} = "Curator sequence analysis for ISS ( GO_REF:0000024 ) "; }
  elsif ($ontology_type eq 'goqualifier') {
    $data{$ontology_type}{name}{"NOT"}              = "NOT";
    $data{$ontology_type}{name}{"involved_in"}      = "involved_in";
    $data{$ontology_type}{name}{"enables"}          = "enables";
    $data{$ontology_type}{name}{"part_of"}          = "part_of";
    $data{$ontology_type}{name}{"contributes_to"}   = "contributes_to";
    $data{$ontology_type}{name}{"colocalizes_with"} = "colocalizes_with"; }
  elsif ($ontology_type eq 'godbtype') {
    $data{$ontology_type}{name}{"protein"}           = "protein";
    $data{$ontology_type}{name}{"gene"}              = "gene";
    $data{$ontology_type}{name}{"transcript"}        = "transcript";
    $data{$ontology_type}{name}{"complex"}           = "complex";
    $data{$ontology_type}{name}{"protein_structure"} = "protein_structure"; }
  elsif ($ontology_type eq 'grgtype') {
    $data{$ontology_type}{name}{"Change_of_localization"}     = "Change_of_localization";
    $data{$ontology_type}{name}{"Change_of_expression_level"} = "Change_of_expression_level"; }
  elsif ($ontology_type eq 'grgresult') {
    $data{$ontology_type}{name}{"Positive_regulate"}     = "Positive_regulate";
    $data{$ontology_type}{name}{"Negative_regulate"}     = "Negative_regulate";
    $data{$ontology_type}{name}{"Does_not_regulate"}     = "Does_not_regulate"; }
  elsif ($ontology_type eq 'regulationlevel') {
    $data{$ontology_type}{name}{"Transcriptional"}      = "Transcriptional";
    $data{$ontology_type}{name}{"Post_transcriptional"} = "Post_transcriptional";
    $data{$ontology_type}{name}{"Post_translational"}   = "Post_translational"; }
  elsif ($ontology_type eq 'regulates') {
    $data{$ontology_type}{name}{"Positive_regulate"} = "Positive_regulate";
    $data{$ontology_type}{name}{"Negative_regulate"} = "Negative_regulate";
    $data{$ontology_type}{name}{"Does_not_regulate"} = "Does_not_regulate"; }
  elsif ($ontology_type eq 'inttype') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"Physical"}                                      = "Physical ( Physical ) ";
    $data{$ontology_type}{name}{"Predicted"}                                     = "Predicted ( Predicted ) ";
    $data{$ontology_type}{name}{"Genetic - Genetic Interaction"}                 = "Genetic - Genetic Interaction ( Genetic_interaction ) ";
    $data{$ontology_type}{name}{"Genetic - Negative genetic"}                    = "Genetic - Negative genetic ( Negative_genetic ) ";
    $data{$ontology_type}{name}{"Genetic - Synthetic"}                           = "Genetic - Synthetic ( Synthetic ) ";
    $data{$ontology_type}{name}{"Genetic - Enhancement"}                         = "Genetic - Enhancement ( Enhancement ) ";
    $data{$ontology_type}{name}{"Genetic - Unilateral enhancement"}              = "Genetic - Unilateral enhancement ( Unilateral_enhancement ) ";
    $data{$ontology_type}{name}{"Genetic - Mutual enhancement"}                  = "Genetic - Mutual enhancement ( Mutual_enhancement ) ";
    $data{$ontology_type}{name}{"Genetic - Positive genetic"}                    = "Genetic - Positive genetic ( Positive_genetic ) ";
    $data{$ontology_type}{name}{"Genetic - Suppression"}                         = "Genetic - Suppression ( Suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Complete suppression"}                = "Genetic - Complete suppression ( Complete_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Partial suppression"}                 = "Genetic - Partial suppression ( Partial_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Unilateral suppression"}              = "Genetic - Unilateral suppression ( Unilateral_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Complete unilateral suppression"}     = "Genetic - Complete unilateral suppression ( Complete_unilateral_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Partial unilateral suppression"}      = "Genetic - Partial unilateral suppression ( Partial_unilateral_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Mutual suppression"}                  = "Genetic - Mutual suppression ( Mutual_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Complete mutual suppression"}         = "Genetic - Complete mutual suppression ( Complete_mutual_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Partial mutual suppression"}          = "Genetic - Partial mutual suppression ( Partial_mutual_suppression ) ";
    $data{$ontology_type}{name}{"Genetic - Asynthetic"}                          = "Genetic - Asynthetic ( Asynthetic ) ";
    $data{$ontology_type}{name}{"Genetic - Suppression/Enhancement"}             = "Genetic - Suppression/Enhancement ( Suppression_enhancement ) ";
    $data{$ontology_type}{name}{"Genetic - Epistasis"}                           = "Genetic - Epistasis ( Epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Positive epistasis"}                  = "Genetic - Positive epistasis ( Positive_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Maximal epistasis"}                   = "Genetic - Maximal epistasis ( Maximal_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Minimal epistasis"}                   = "Genetic - Minimal epistasis ( Minimal_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Neutral epistasis"}                   = "Genetic - Neutral epistasis ( Neutral_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Qualitative epistasis"}               = "Genetic - Qualitative epistasis ( Qualitative_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Opposing epistasis"}                  = "Genetic - Opposing epistasis ( Opposing_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Quantitative epistasis"}              = "Genetic - Quantitative epistasis ( Quantitative_epistasis ) ";
#     $data{$ontology_type}{name}{"Genetic - Suppression/Epistasis"}               = "Genetic - Suppression/Epistasis ( Suppression_epistasis ) ";
#     $data{$ontology_type}{name}{"Genetic - Agonistic/Epistasis"}                 = "Genetic - Agonistic/Epistasis ( Agonistic_epistasis ) ";
#     $data{$ontology_type}{name}{"Genetic - Antagonistic/Epistasis"}              = "Genetic - Antagonistic/Epistasis ( Antagonistic_epistasis ) ";
    $data{$ontology_type}{name}{"Genetic - Neutral genetic"}                     = "Genetic - Neutral genetic ( Neutral_genetic ) ";
    $data{$ontology_type}{name}{"Genetic - Oversuppression"}                     = "Genetic - Oversuppression ( Oversuppression ) ";
    $data{$ontology_type}{name}{"Genetic - Unilateral oversuppression"}          = "Genetic - Unilateral oversuppression ( Unilateral_oversuppression ) ";
    $data{$ontology_type}{name}{"Genetic - Mutual oversuppression"}              = "Genetic - Mutual oversuppression ( Mutual_oversuppression ) ";
#     $data{$ontology_type}{name}{"Genetic - Complex oversuppression"}             = "Genetic - Complex oversuppression ( Complex_oversuppression ) ";
    $data{$ontology_type}{name}{"Genetic - Oversuppression/Enhancement"}         = "Genetic - Oversuppression/Enhancement ( Oversuppression_enhancement ) ";
    $data{$ontology_type}{name}{"Genetic - Phenotype bias"}                      = "Genetic - Phenotype bias ( Phenotype_bias ) ";
#     $data{$ontology_type}{name}{"Genetic - Biased suppression"}                  = "Genetic - Biased suppression ( Biased_suppression ) ";
#     $data{$ontology_type}{name}{"Genetic - Biased enhancement"}                  = "Genetic - Biased enhancement ( Biased_enhancement ) ";
#     $data{$ontology_type}{name}{"Genetic - Complex phenotype bias"}              = "Genetic - Complex phenotype bias ( Complex_phenotype_bias ) ";
    $data{$ontology_type}{name}{"Genetic - No_interaction"}                      = "Genetic - No_interaction ( No_interaction ) "; }
#     $data{$ontology_type}{name}{"Physical"}                    = "Physical";
#     $data{$ontology_type}{name}{"Predicted"}                   = "Predicted";
#     $data{$ontology_type}{name}{"Genetic_interaction"}         = "Genetic - Genetic Interaction";
#     $data{$ontology_type}{name}{"Negative_genetic"}            = "Genetic - Negative genetic";
#     $data{$ontology_type}{name}{"Synthetic"}                   = "Genetic - Synthetic";
#     $data{$ontology_type}{name}{"Enhancement"}                 = "Genetic - Enhancement";
#     $data{$ontology_type}{name}{"Unilateral_enhancement"}      = "Genetic - Unilateral enhancement";
#     $data{$ontology_type}{name}{"Mutual_enhancement"}          = "Genetic - Mutual enhancement";
#     $data{$ontology_type}{name}{"Suppression"}                 = "Genetic - Suppression";
#     $data{$ontology_type}{name}{"Unilateral_suppression"}      = "Genetic - Unilateral suppression";
#     $data{$ontology_type}{name}{"Mutual_suppression"}          = "Genetic - Mutual suppression";
#     $data{$ontology_type}{name}{"Asynthetic"}                  = "Genetic - Asynthetic";
#     $data{$ontology_type}{name}{"Suppression_enhancement"}     = "Genetic - Suppression/Enhancement";
#     $data{$ontology_type}{name}{"Epistasis"}                   = "Genetic - Epistasis";
#     $data{$ontology_type}{name}{"Maximal_epistasis"}           = "Genetic - Maximal epistasis";
#     $data{$ontology_type}{name}{"Minimal_epistasis"}           = "Genetic - Minimal epistasis";
#     $data{$ontology_type}{name}{"Suppression_epistasis"}       = "Genetic - Suppression/Epistasis";
#     $data{$ontology_type}{name}{"Agonistic_epistasis"}         = "Genetic - Agonistic/Epistasis";
#     $data{$ontology_type}{name}{"Antagonistic_epistasis"}      = "Genetic - Antagonistic/Epistasis";
#     $data{$ontology_type}{name}{"Oversuppression"}             = "Genetic - Oversuppression";
#     $data{$ontology_type}{name}{"Unilateral_oversuppression"}  = "Genetic - Unilateral oversuppression";
#     $data{$ontology_type}{name}{"Mutual_oversuppression"}      = "Genetic - Mutual oversuppression";
#     $data{$ontology_type}{name}{"Complex_oversuppression"}     = "Genetic - Complex oversuppression";
#     $data{$ontology_type}{name}{"Oversuppression_enhancement"} = "Genetic - Mutual Oversuppression/Enhancement";
#     $data{$ontology_type}{name}{"Phenotype_bias"}              = "Genetic - Phenotype bias";
#     $data{$ontology_type}{name}{"Biased_suppression"}          = "Genetic - Biased suppression";
#     $data{$ontology_type}{name}{"Biased_enhancement"}          = "Genetic - Biased enhancement";
#     $data{$ontology_type}{name}{"Complex_phenotype_bias"}      = "Genetic - Complex phenotype bias";
#     $data{$ontology_type}{name}{"No_interaction"}              = "Genetic - No_interaction";
  elsif ($ontology_type eq 'intphysdetmethod') {
    $data{$ontology_type}{name}{"Affinity_capture_luminescence"}          = "Affinity_capture_luminescence";
    $data{$ontology_type}{name}{"Affinity_capture_MS"}                    = "Affinity_capture_MS";
    $data{$ontology_type}{name}{"Affinity_capture_RNA"}                   = "Affinity_capture_RNA";
    $data{$ontology_type}{name}{"Affinity_capture_Western"}               = "Affinity_capture_Western";
    $data{$ontology_type}{name}{"Cofractionation"}                        = "Cofractionation";
    $data{$ontology_type}{name}{"Colocalization"}                         = "Colocalization";
    $data{$ontology_type}{name}{"Copurification"}                         = "Copurification";
    $data{$ontology_type}{name}{"DNase_I_footprinting"}                   = "DNase_I_footprinting";
    $data{$ontology_type}{name}{"Fluorescence_resonance_energy_transfer"} = "Fluorescence_resonance_energy_transfer";
    $data{$ontology_type}{name}{"Protein_fragment_complementation_assay"} = "Protein_fragment_complementation_assay";
    $data{$ontology_type}{name}{"Yeast_two_hybrid"}                       = "Yeast_two_hybrid";
    $data{$ontology_type}{name}{"Biochemical_activity"}                   = "Biochemical_activity";
    $data{$ontology_type}{name}{"Cocrystal_structure"}                    = "Cocrystal_structure";
    $data{$ontology_type}{name}{"Far_western"}                            = "Far_western";
    $data{$ontology_type}{name}{"Protein_peptide"}                        = "Protein_peptide";
    $data{$ontology_type}{name}{"Protein_RNA"}                            = "Protein_RNA";
    $data{$ontology_type}{name}{"Reconstituted_complex"}                  = "Reconstituted_complex";
    $data{$ontology_type}{name}{"Yeast_one_hybrid"}                       = "Yeast_one_hybrid";
    $data{$ontology_type}{name}{"Directed_yeast_one_hybrid"}              = "Directed_yeast_one_hybrid";
    $data{$ontology_type}{name}{"Chromatin_immunoprecipitation"}          = "Chromatin_immunoprecipitation";
    $data{$ontology_type}{name}{"Electrophoretic_mobility_shift_assay"}   = "Electrophoretic_mobility_shift_assay"; }
#   elsif ($ontology_type eq 'intothertype') {
#     $data{$ontology_type}{name}{"Transgene"}       = "Transgene";
#     $data{$ontology_type}{name}{"Chemical"}        = "Chemical"; }
  elsif ($ontology_type eq 'intneutralityfxn') {
    $data{$ontology_type}{name}{"Multiplicative"}  = "Multiplicative";
    $data{$ontology_type}{name}{"Additive"}        = "Additive";
    $data{$ontology_type}{name}{"Minimal"}         = "Minimal"; }
#   elsif ($ontology_type eq 'trpreportertype') {
#     $data{$ontology_type}{name}{"Transcriptional fusion"} = "Transcriptional fusion";
#     $data{$ontology_type}{name}{"Translational fusion"}   = "Translational fusion"; }
#   elsif ($ontology_type eq 'cnsconstructtype') {
#     $data{$ontology_type}{name}{"Chimera"}                             = "Chimera";
#     $data{$ontology_type}{name}{"Domain_swap"}                         = "Domain_swap";
#     $data{$ontology_type}{name}{"Engineered_mutation"}                 = "Engineered_mutation";
#     $data{$ontology_type}{name}{"Fusion"}                              = "Fusion";
#     $data{$ontology_type}{name}{"Complex"}                             = "Complex";
#     $data{$ontology_type}{name}{"Transcriptional_fusion"}              = "Transcriptional_fusion";
#     $data{$ontology_type}{name}{"Translational_fusion"}                = "Translational_fusion ";
#     $data{$ontology_type}{name}{"Nterminal_translational_fusion"}      = "Nterminal_translational_fusion";
#     $data{$ontology_type}{name}{"Cterminal_translational_fusion"}      = "Cterminal_translational_fusion";
#     $data{$ontology_type}{name}{"Internal_coding_fusion"}              = "Internal_coding_fusion"; }
  elsif ($ontology_type eq 'recombination') {
    $data{$ontology_type}{name}{"LoxP"}                      = "LoxP";
    $data{$ontology_type}{name}{"FRT"}   		     = "FRT"; }
  elsif ($ontology_type eq 'purification') {
    $data{$ontology_type}{name}{"Histone H2B"}               = "Histone H2B";
    $data{$ontology_type}{name}{"FLAG"}                      = "FLAG";
    $data{$ontology_type}{name}{"HA-tag"}                    = "HA-tag";
    $data{$ontology_type}{name}{"MYC/c-myc"}                 = "MYC/c-myc";
    $data{$ontology_type}{name}{"Stag"}                      = "Stag"; 
    $data{$ontology_type}{name}{"AviTag"}                    = "AviTag";
    $data{$ontology_type}{name}{"TAP"}   		     = "TAP"; }
#   elsif ($ontology_type eq 'reporterproduct') {
#     tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
#     $data{$ontology_type}{name}{"GFP"}                       = "GFP";
#     $data{$ontology_type}{name}{"GFP(S65C)"}                 = "GFP(S65C)";
#     $data{$ontology_type}{name}{"dGFP(destabilized GFP)"}    = "dGFP(destabilized GFP)";
#     $data{$ontology_type}{name}{"EGFP"}                      = "EGFP";
#     $data{$ontology_type}{name}{"pGFP(photoactivated GFP)"}  = "pGFP(photoactivated GFP)";
#     $data{$ontology_type}{name}{"YFP"}                       = "YFP";
#     $data{$ontology_type}{name}{"EYFP"}                      = "EYFP";
#     $data{$ontology_type}{name}{"BFP"}                       = "BFP";
#     $data{$ontology_type}{name}{"CFP"}                       = "CFP";
#     $data{$ontology_type}{name}{"Cerulian"}                  = "Cerulian";
#     $data{$ontology_type}{name}{"RFP"}                       = "RFP";
#     $data{$ontology_type}{name}{"mRFP"}                      = "mRFP";
#     $data{$ontology_type}{name}{"tagRFP"}                    = "tagRFP";
#     $data{$ontology_type}{name}{"mCherry"}                   = "mCherry";
#     $data{$ontology_type}{name}{"wCherry"}                   = "wCherry";
#     $data{$ontology_type}{name}{"tdTomato"}                  = "tdTomato";
#     $data{$ontology_type}{name}{"mStrawberry"}               = "mStrawberry";
#     $data{$ontology_type}{name}{"DsRed"}                     = "DsRed";
#     $data{$ontology_type}{name}{"DsRed2"}                    = "DsRed2";
#     $data{$ontology_type}{name}{"Venus"}                     = "Venus";
#     $data{$ontology_type}{name}{"YC2.1 (yellow cameleon)"}   = "YC2.1 (yellow cameleon)";
#     $data{$ontology_type}{name}{"YC12.12 (yellow cameleon)"} = "YC12.12 (yellow cameleon)";
#     $data{$ontology_type}{name}{"YC3.60 (yellow cameleon)"}  = "YC3.60 (yellow cameleon)";
#     $data{$ontology_type}{name}{"Yellow cameleon"}           = "Yellow cameleon";
#     $data{$ontology_type}{name}{"Dendra"}                    = "Dendra";
#     $data{$ontology_type}{name}{"Dendra2"}                   = "Dendra2";
#     $data{$ontology_type}{name}{"tdimer2(12)/dimer2"}        = "tdimer2(12)/dimer2";
#     $data{$ontology_type}{name}{"GCaMP"}                     = "GCaMP";
#     $data{$ontology_type}{name}{"mkate2"}                    = "mkate2";
#     $data{$ontology_type}{name}{"Luciferase"}                = "Luciferase";
#     $data{$ontology_type}{name}{"LacI"}                      = "LacI";
#     $data{$ontology_type}{name}{"LacO"}                      = "LacO";
#     $data{$ontology_type}{name}{"LacZ"}                      = "LacZ";
# #     $data{$ontology_type}{name}{"Histone H2B"}               = "Histone H2B";
# #     $data{$ontology_type}{name}{"His-tag"}                   = "His-tag";
# #     $data{$ontology_type}{name}{"FLAG"}                      = "FLAG";
# #     $data{$ontology_type}{name}{"HA-tag"}                    = "HA-tag";
# #     $data{$ontology_type}{name}{"MYC/c-myc"}                 = "MYC/c-myc";
# #     $data{$ontology_type}{name}{"Stag"}                      = "Stag"; 
#   }
  elsif ($ontology_type eq 'integrationmethod') {
#     $data{$ontology_type}{name}{"Gamma_ray"}                      = "Gamma_ray";
#     $data{$ontology_type}{name}{"X_ray"}                          = "X_ray";
#     $data{$ontology_type}{name}{"Spontaneous"}                    = "Spontaneous";
#     $data{$ontology_type}{name}{"UV"}                             = "UV";
#     $data{$ontology_type}{name}{"4,5',8-trimethylpsoralen (TMP)"} = "4,5',8-trimethylpsoralen (TMP)";
#     $data{$ontology_type}{name}{"MMS mutagenesis"}                = "MMS mutagenesis";
#     $data{$ontology_type}{name}{"Single copy insertion"}          = "Single copy insertion";
#     $data{$ontology_type}{name}{"Particle_bombardment"}           = "Particle_bombardment";
    $data{$ontology_type}{name}{"Gamma_irradiation"}            = "Gamma_irradiation";
    $data{$ontology_type}{name}{"X-ray"}                        = "X-ray";
    $data{$ontology_type}{name}{"Spontaneous"}                  = "Spontaneous";
    $data{$ontology_type}{name}{"UV"}                           = "UV";
    $data{$ontology_type}{name}{"UV_TMP"}                       = "UV_TMP";
    $data{$ontology_type}{name}{"MMS_mutagenesis"}              = "MMS_mutagenesis";
    $data{$ontology_type}{name}{"Single_copy_insertion"}        = "Single_copy_insertion";
    $data{$ontology_type}{name}{"Particle_bombardment"}         = "Particle_bombardment";
    $data{$ontology_type}{name}{"EMS_mutagenesis"}              = "EMS_mutagenesis"; }
  elsif ($ontology_type eq 'chromosome') {
    $data{$ontology_type}{name}{"I"}   = "I";
    $data{$ontology_type}{name}{"II"}  = "II";
    $data{$ontology_type}{name}{"III"} = "III";
    $data{$ontology_type}{name}{"IV"}  = "IV";
    $data{$ontology_type}{name}{"V"}   = "V";
    $data{$ontology_type}{name}{"X"}   = "X"; }
  elsif ($ontology_type eq 'topicpaperstatus') {
    $data{$ontology_type}{name}{"unchecked"}            = "unchecked";
    $data{$ontology_type}{name}{"relevant"}             = "relevant";
    $data{$ontology_type}{name}{"irrelevant"}           = "irrelevant"; }
  elsif ($ontology_type eq 'curationstatus') {
    $data{$ontology_type}{name}{"happy"}                = "happy";
    $data{$ontology_type}{name}{"not_happy"}            = "not_happy";
    $data{$ontology_type}{name}{"down_right_disgusted"} = "down_right_disgusted"; }
  elsif ($ontology_type eq 'allelestatus') {
    $data{$ontology_type}{name}{"other"}                = "other";
    $data{$ontology_type}{name}{"lost"}                 = "lost";
    $data{$ontology_type}{name}{"new_gene_assignment"}  = "new_gene_assignment"; }
  elsif ($ontology_type eq 'easescore') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"ES0_Impossible_to_score"}        = "ES0_Impossible_to_score";
    $data{$ontology_type}{name}{"ES1_Very_hard_to_score"}         = "ES1_Very_hard_to_score";
    $data{$ontology_type}{name}{"ES2_Difficult_to_score"}         = "ES2_Difficult_to_score";
    $data{$ontology_type}{name}{"ES3_Easy_to_score"}              = "ES3_Easy_to_score"; }
  elsif ($ontology_type eq 'mmateff') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"ME0_Mating_not_successful"}      = "ME0_Mating_not_successful";
    $data{$ontology_type}{name}{"ME1_Mating_rarely_successful"}   = "ME1_Mating_rarely_successful";
    $data{$ontology_type}{name}{"ME2_Mating_usually_successful"}  = "ME2_Mating_usually_successful";
    $data{$ontology_type}{name}{"ME3_Mating_always_successful"}   = "ME3_Mating_always_successful"; }
  elsif ($ontology_type eq 'hmateff') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"HME0_Mating_not_successful"}     = "HME0_Mating_not_successful";
    $data{$ontology_type}{name}{"HME1_Mating_rarely_successful"}  = "HME1_Mating_rarely_successful";
    $data{$ontology_type}{name}{"HME2_Mating_usually_successful"} = "HME2_Mating_usually_successful";
    $data{$ontology_type}{name}{"HME3_Mating_always_successful"}  = "HME3_Mating_always_successful"; }
  elsif ($ontology_type eq 'nature') {
#     $data{$ontology_type}{name}{"Recessive"} = "Recessive ( WBnature000001 ) ";
#     $data{$ontology_type}{name}{"Semi_dominant"} = "Semi_dominant ( WBnature000002 ) ";
#     $data{$ontology_type}{name}{"Dominant"} = "Dominant ( WBnature000003 ) ";
    $data{$ontology_type}{name}{"Recessive"}     = "Recessive";
    $data{$ontology_type}{name}{"Semi_dominant"} = "Semi_dominant";
    $data{$ontology_type}{name}{"Dominant"}      = "Dominant"; }
  elsif ($ontology_type eq 'func') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
#     $data{$ontology_type}{name}{"Loss_of_function"}                 = "Loss_of_function";
#     $data{$ontology_type}{name}{"Hypomorph"}                        = "Hypomorph";
#     $data{$ontology_type}{name}{"Amorph"}                           = "Amorph";
#     $data{$ontology_type}{name}{"Uncharacterised_loss_of_function"} = "Uncharacterised_loss_of_function";
#     $data{$ontology_type}{name}{"Gain_of_function"}                 = "Gain_of_function";
#     $data{$ontology_type}{name}{"Hypermorph"}                       = "Hypermorph";
#     $data{$ontology_type}{name}{"Dominant_negative"}                = "Dominant_negative";
#     $data{$ontology_type}{name}{"Neomorph"}                         = "Neomorph";
#     $data{$ontology_type}{name}{"Uncharacterised_gain_of_function"} = "Uncharacterised_gain_of_function";
#     $data{$ontology_type}{name}{"Wild_type"}                        = "Wild_type";
#     $data{$ontology_type}{name}{"Isoallele"}                        = "Isoallele";
#     $data{$ontology_type}{name}{"Mixed"}                            = "Mixed"; 
    $data{$ontology_type}{name}{"Null"}                                 = "Null";
    $data{$ontology_type}{name}{"Probable_null_via_phenotype"}          = "Probable_null_via_phenotype";
    $data{$ontology_type}{name}{"Predicted_null_via_sequence"}          = "Predicted_null_via_sequence";
    $data{$ontology_type}{name}{"Hypomorph_reduction_of_function"}      = "Hypomorph_reduction_of_function";
    $data{$ontology_type}{name}{"Loss_of_function_undetermined_extent"} = "Loss_of_function_undetermined_extent";
    $data{$ontology_type}{name}{"Probable_hypomorph_via_phenotype"}     = "Probable_hypomorph_via_phenotype";
    $data{$ontology_type}{name}{"Predicted_hypomorph_via_sequence"}     = "Predicted_hypomorph_via_sequence";
    $data{$ontology_type}{name}{"Gain_of_function_undetermined_type"}   = "Gain_of_function_undetermined_type";
    $data{$ontology_type}{name}{"Neomorph_gain_of_function"}            = "Neomorph_gain_of_function";
    $data{$ontology_type}{name}{"Antimorph_gain_of_function"}           = "Antimorph_gain_of_function";
    $data{$ontology_type}{name}{"Hypermorph_gain_of_function"}          = "Hypermorph_gain_of_function";
    $data{$ontology_type}{name}{"Dominant_negative_gain_of_function"}   = "Dominant_negative_gain_of_function";
    $data{$ontology_type}{name}{"Wild_allele"}                          = "Wild_allele"; }
  elsif ($ontology_type eq 'penetrance') {
    $data{$ontology_type}{name}{"Incomplete"} = "Incomplete";
    $data{$ontology_type}{name}{"Low"}        = "Low";
    $data{$ontology_type}{name}{"High"}       = "High";
    $data{$ontology_type}{name}{"Complete"}   = "Complete"; }
  elsif ($ontology_type eq 'mateffect') {
    $data{$ontology_type}{name}{"Maternal"}             = "Maternal";
    $data{$ontology_type}{name}{"Strictly_maternal"}    = "Strictly_maternal";
    $data{$ontology_type}{name}{"With_maternal_effect"} = "With_maternal_effect"; }
  elsif ($ontology_type eq 'relanatomy') {
    $data{$ontology_type}{name}{"part_of"}                    = "part_of"; }
  elsif ($ontology_type eq 'rellifestage') {
    $data{$ontology_type}{name}{"happens_during"}             = "happens_during";
    $data{$ontology_type}{name}{"part_of"}                    = "part_of"; }
  elsif ($ontology_type eq 'relcellcycle') {
    $data{$ontology_type}{name}{"exists_during"}              = "exists_during";
    $data{$ontology_type}{name}{"dependent_on"}               = "dependent_on";
    $data{$ontology_type}{name}{"happens_during"}             = "happens_during";
    $data{$ontology_type}{name}{"independent_of"}             = "independent_of";
    $data{$ontology_type}{name}{"part_of"}                    = "part_of"; }
#   elsif ($ontology_type eq 'species') {
#     $data{$ontology_type}{name}{"Caenorhabditis elegans"}     = "Caenorhabditis elegans";
#     $data{$ontology_type}{name}{"Caenorhabditis sp. 3"}       = "Caenorhabditis sp. 3";
#     $data{$ontology_type}{name}{"Panagrellus redivivus"}      = "Panagrellus redivivus";
#     $data{$ontology_type}{name}{"Cruznema tripartitum"}       = "Cruznema tripartitum";
#     $data{$ontology_type}{name}{"Caenorhabditis brenneri"}    = "Caenorhabditis brenneri";
#     $data{$ontology_type}{name}{"Caenorhabditis japonica"}    = "Caenorhabditis japonica";
#     $data{$ontology_type}{name}{"Caenorhabditis briggsae"}    = "Caenorhabditis briggsae";
#     $data{$ontology_type}{name}{"Caenorhabditis remanei"}     = "Caenorhabditis remanei";
#     $data{$ontology_type}{name}{"Pristionchus pacificus"}     = "Pristionchus pacificus";
#     $data{$ontology_type}{name}{"Brugia malayi"}              = "Brugia malayi";
#     $data{$ontology_type}{name}{"Strongyloides stercoralis"}  = "Strongyloides stercoralis";
#     $data{$ontology_type}{name}{"Homo sapiens"}               = "Homo sapiens"; }
#   elsif ($ontology_type eq 'mopclassification') {
#     $data{$ontology_type}{name}{"Carbohydrate"}               = "Carbohydrate";
#     $data{$ontology_type}{name}{"Sugar"}                      = "Sugar";
#     $data{$ontology_type}{name}{"Polysaccharide"}             = "Polysaccharide";
#     $data{$ontology_type}{name}{"Lipid"}                      = "Lipid";
#     $data{$ontology_type}{name}{"Protein"}                    = "Protein";
#     $data{$ontology_type}{name}{"Amino_acid"}                 = "Amino_acid";
#     $data{$ontology_type}{name}{"Nucleic_acid"}               = "Nucleic_acid";
#     $data{$ontology_type}{name}{"Toxin"}                      = "Toxin";
#     $data{$ontology_type}{name}{"Drug"}                       = "Drug"; }
#   elsif ($ontology_type eq 'mopsource') {
#     tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
#     $data{$ontology_type}{name}{"Endogenous"}                 = "Endogenous";
#     $data{$ontology_type}{name}{"Exogenous"}                  = "Exogenous";
#     $data{$ontology_type}{name}{"Pharmaceutical"}             = "Pharmaceutical";
#     $data{$ontology_type}{name}{"Industrial"}                 = "Industrial"; }
#   elsif ($ontology_type eq 'moprole') {
#     $data{$ontology_type}{name}{"Metabolite"}                 = "Metabolite";
#     $data{$ontology_type}{name}{"Regulatory"}                 = "Regulatory";
#     $data{$ontology_type}{name}{"Structural"}                 = "Structural"; }
  elsif ($ontology_type eq 'mopbiorole') {
    $data{$ontology_type}{name}{"Metabolite"}                 = "Metabolite"; 
    $data{$ontology_type}{name}{"Regulator"}                  = "Regulator";
    $data{$ontology_type}{name}{"Structural_component"}       = "Structural_component";
    $data{$ontology_type}{name}{"Cofactor"}                   = "Cofactor";
    $data{$ontology_type}{name}{"Activator"}                  = "Activator";
    $data{$ontology_type}{name}{"Inhibitor"}                  = "Inhibitor";
    $data{$ontology_type}{name}{"Product"}                    = "Product";
    $data{$ontology_type}{name}{"Substrate"}                  = "Substrate";
    $data{$ontology_type}{name}{"Ligand"}                     = "Ligand";
    $data{$ontology_type}{name}{"Receptor"}                   = "Receptor"; }
  elsif ($ontology_type eq 'mopstatus') {
    $data{$ontology_type}{name}{"Detected"}                   = "Detected";
    $data{$ontology_type}{name}{"Predicted"}                  = "Predicted"; }
  elsif ($ontology_type eq 'mopdetctmethod') {
    $data{$ontology_type}{name}{"HR-MAS-NMR"}                 = "HR-MAS-NMR";
    $data{$ontology_type}{name}{"GC-MS"}                      = "GC-MS";
    $data{$ontology_type}{name}{"LC-MS"}                      = "LC-MS";
    $data{$ontology_type}{name}{"LC-Coularray"}               = "LC-Coularray";
    $data{$ontology_type}{name}{"NMR"}                        = "NMR";
    $data{$ontology_type}{name}{"MALDI-MS"}                   = "MALDI-MS";
    $data{$ontology_type}{name}{"HPLC-UV"}                    = "HPLC-UV";
    $data{$ontology_type}{name}{"shotgun lipidomics"}         = "shotgun lipidomics"; }
  elsif ($ontology_type eq 'mopextrctmethod') {
    $data{$ontology_type}{name}{"MeOH/CHCl3"}                 = "MeOH/CHCl3";
    $data{$ontology_type}{name}{"MeOH/MTBE"}                  = "MeOH/MTBE";
    $data{$ontology_type}{name}{"EtOH"}                       = "EtOH";
    $data{$ontology_type}{name}{"phosphate buffer"}           = "phosphate buffer";
    $data{$ontology_type}{name}{"80% MeOH"}                   = "80% MeOH";
    $data{$ontology_type}{name}{"ACN/0.1M NaCl"}              = "ACN/0.1M NaCl";
    $data{$ontology_type}{name}{"mobile phase"}               = "mobile phase";
    $data{$ontology_type}{name}{"M9 buffer"}                  = "M9 buffer";
    $data{$ontology_type}{name}{"MeOH"}                       = "MeOH";
    $data{$ontology_type}{name}{"exometabolome"}              = "exometabolome";
    $data{$ontology_type}{name}{"MeOH/Chloroform"}            = "MeOH/Chloroform";
    $data{$ontology_type}{name}{"5% trichloroacetic acid"}    = "5% trichloroacetic acid"; }
  elsif ($ontology_type eq 'deliverymethod') {
    $data{$ontology_type}{name}{"Bacterial_feeding"}          = "Bacterial_feeding";
    $data{$ontology_type}{name}{"Injection"}                  = "Injection";
    $data{$ontology_type}{name}{"Soaking"}                    = "Soaking";
    $data{$ontology_type}{name}{"Transgene_expression"}       = "Transgene_expression"; }
  elsif ($ontology_type eq 'seqfeatmethod') {
    $data{$ontology_type}{name}{"binding_site"}               = "binding_site";
    $data{$ontology_type}{name}{"binding_site_region"}        = "binding_site_region";
    $data{$ontology_type}{name}{"enhancer"}                   = "enhancer";
    $data{$ontology_type}{name}{"history_feature"}            = "history_feature";
    $data{$ontology_type}{name}{"regulatory_region"}          = "regulatory_region"; 
    $data{$ontology_type}{name}{"TF_binding_site"}            = "TF_binding_site";
    $data{$ontology_type}{name}{"TF_binding_site_region"}     = "TF_binding_site_region"; 
    $data{$ontology_type}{name}{"silencer"}                   = "silencer";
    $data{$ontology_type}{name}{"NC_conserved_region"}        = "NC_conserved_region"; }
  return \%data;
} # sub setAnySimpleAutocompleteValues


sub getAnySpecificAutocomplete {
  my ($ontology_type, $words) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyAutocomplete($words); }
  elsif ($ontology_type eq 'Concurhst') {       ($matches) = &getAnyConcurhstAutocomplete($words); }
  elsif ($ontology_type eq 'Discurhst') {       ($matches) = &getAnyDiscurhstAutocomplete($words); }
  elsif ($ontology_type eq 'Ditcurhst') {       ($matches) = &getAnyDitcurhstAutocomplete($words); }
  elsif ($ontology_type eq 'Expr') {            ($matches) = &getAnyExprAutocomplete($words); }
  elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeAutocomplete($words); }
  elsif ($ontology_type eq 'Transgene') {       ($matches) = &getAnyTransgeneAutocomplete($words); }
  elsif ($ontology_type eq 'WBConstruct') {     ($matches) = &getAnyWBConstructAutocomplete($words); }
  elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneAutocomplete($words); }
  elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionAutocomplete($words); }
  elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperAutocomplete($words); }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonAutocomplete($words); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureAutocomplete($words); }
  elsif ($ontology_type eq 'WBProcess') {       ($matches) = &getAnyWBProcessAutocomplete($words); }
  elsif ($ontology_type eq 'WBRnai') {          ($matches) = &getAnyWBRnaiAutocomplete($words); }
  elsif ($ontology_type eq 'WBSeqFeat') {       ($matches) = &getAnyWBSeqFeatAutocomplete($words); }
  elsif ($ontology_type eq 'WBSequence') {      ($matches) = &getAnyWBSequenceAutocomplete($words); }
  return $matches;
} # sub getAnySpecificAutocomplete

sub getAnyAntibodyAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( abp_name );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0];
      $matches{"$row[1]"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0];
      $matches{"$row[1]"}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyAntibodyAutocomplete

sub getAnyConcurhstAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( con_curator );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT joinkey FROM $table WHERE LOWER(joinkey) ~ '^$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[0]"}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyConcurhstAutocomplete

sub getAnyDiscurhstAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( dis_curator );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT joinkey FROM $table WHERE LOWER(joinkey) ~ '^$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[0]"}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyDiscurhstAutocomplete

sub getAnyDitcurhstAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( dit_curator );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT joinkey FROM $table WHERE LOWER(joinkey) ~ '^$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[0]"}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyDitcurhstAutocomplete

sub getAnyExprAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( exp_name );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0];
      $matches{"$row[1]"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0];
      $matches{"$row[1]"}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyExprAutocomplete

sub getAnyMoleculeAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my $table = 'mop_name';				# can't name mop_name twice, so can't add that to generic @tables below
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }

  my @tables = qw( mop_publicname mop_molecule mop_synonym );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT mop_name.mop_name, ${table}.$table FROM mop_name, $table WHERE mop_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    $result = $dbh->prepare( "SELECT mop_name.mop_name, ${table}.$table FROM mop_name, $table WHERE mop_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$words' AND LOWER(${table}.$table) !~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
#   foreach my $table (@tables) {
#     my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
#     $result->execute();
#     while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
#       my $id = $row[0];
#       if ($table eq 'mop_molecule') { $matches{"$row[1] ( $id ) "}++; }
#         else {
#           my $result2 = $dbh->prepare( "SELECT * FROM mop_molecule WHERE joinkey = '$row[0]';" ); $result2->execute();
#           my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
#           if ($table eq 'mop_molecule') { $matches{"$name ( $id ) "}++; }
#             else { $matches{"$row[1] ( $id ) \[$name\]"}++; } }
#     }
#     $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
#     $result->execute();
#     while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
#       my $id = $row[0];
#       if ($table eq 'mop_molecule') { $matches{"$row[1] ( $id ) "}++; }
#         else {
#           my $result2 = $dbh->prepare( "SELECT * FROM mop_molecule WHERE joinkey = '$row[0]';" ); $result2->execute();
#           my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
#           if ($table eq 'mop_molecule') { $matches{"$name ( $id ) "}++; }
#             else { $matches{"$row[1] ( $id ) \[$name\]"}++; } }
#     }
#     last if (scalar keys %matches >= $max_results);
#   } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyMoleculeAutocomplete

sub getAnyTransgeneAutocomplete {			# autocomplete on OA config that has multiple values per row
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# could have multiple joinkeys, so need tied hash instead of normal array
  my $table = 'trp_name';				# can't name trp_name twice, so can't add that to generic @tables below
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }

  my @tables = qw( trp_publicname trp_synonym );			# used to have trp_paper, but would get lots of "WBPaperNNN","WBPaperNNN" in the dataTable, which looked misleading.  2010 09 28
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT trp_name.trp_name, ${table}.$table FROM trp_name, $table WHERE trp_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    $result = $dbh->prepare( "SELECT trp_name.trp_name, ${table}.$table FROM trp_name, $table WHERE trp_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$words' AND LOWER(${table}.$table) !~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub sub getAnyTransgeneAutocomplete

sub getAnyWBConstructAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my $table = 'cns_name';				# can't name cns_name twice, so can't add that to generic @tables below
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }

  my @tables = qw( cns_publicname cns_othername cns_summary );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT cns_name.cns_name, ${table}.$table FROM cns_name, $table WHERE cns_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    $result = $dbh->prepare( "SELECT cns_name.cns_name, ${table}.$table FROM cns_name, $table WHERE cns_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$words' AND LOWER(${table}.$table) !~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBConstructAutocomplete

sub getAnyWBGeneAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( gin_locus gin_synonyms gin_seqname gin_wbgene );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBGene" . $row[0];
      if ($table eq 'gin_locus') { $matches{"$row[1] ( $id ) "}++; }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) { 
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]';" ); $result2->execute();
        my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
        if ( ($table eq 'gin_synonyms')|| ($table eq 'gin_seqname') ) { $matches{"$row[1] ( $id ) \[$name\]"}++; }
        if ($table eq 'gin_wbgene') { $matches{"$name ( $id ) "}++; } }
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBGene" . $row[0];
      if ($table eq 'gin_locus') { $matches{"$row[1] ( $id ) "}++; }
      if ( ($table eq 'gin_synonyms') || ($table eq 'gin_seqname') || ($table eq 'gin_wbgene') ) { 
        my $result2 = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$row[0]';" ); $result2->execute();
        my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
        if ( ($table eq 'gin_synonyms')|| ($table eq 'gin_seqname') ) { $matches{"$row[1] ( $id ) \[$name\]"}++; }
        if ($table eq 'gin_wbgene') { $matches{"$name ( $id ) "}++; } } }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches;
  return $matches;
} # sub getAnyWBGeneAutocomplete

sub getAnyWBInteractionAutocomplete {
  my ($words) = @_;
  if ($words =~ m/^wbinteraction/i) { $words =~ s/^wbinteraction//i; } 	# strip out the leading wbinteraction so autocomplete works when editing an entry
#   my $result = $dbh->prepare( "SELECT * FROM int_index ORDER BY int_index::INTEGER DESC;" ); $result->execute(); 

  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( int_index );						# master record of interactions in int_index not int_name nor grg_intid
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '^$words' ORDER BY joinkey;" ); $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"WBInteraction$row[0]"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$words' ORDER BY joinkey;" ); $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"WBInteraction$row[0]"}++; }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBInteractionAutocomplete

sub getAnyWBPaperAutocomplete {
  my ($words) = @_;
  if ($words =~ m/^wbpaper/) { $words =~ s/^wbpaper//; } 		# strip out the leading wbpaper so autocomplete works when editing an entry
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( pap_status );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '^$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBPaper" . $row[0];
      $matches{"$id"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = "WBPaper" . $row[0];
      $matches{"$id"}++; }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBPaperAutocomplete

sub getAnyWBPersonAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my %invalidPersons;
  my $result = $dbh->prepare( "SELECT * FROM two_status WHERE two_status = 'Invalid'" ); $result->execute();
  while (my @row = $result->fetchrow()) { $invalidPersons{$row[0]}++; }
  my @tables = qw( two_standardname );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );	# match by start of name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $invalid = ''; if ($invalidPersons{$row[0]}) { $invalid = ' INVALID'; }
      $matches{"$row[2]$invalid ( $id ) "}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' ORDER BY $table;" );		# then match anywhere in the name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $invalid = ''; if ($invalidPersons{$row[0]}) { $invalid = ' INVALID'; }
      $matches{"$row[2]$invalid ( $id ) "}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$words' ORDER BY joinkey;" );		# then match by WBPerson number
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      my $invalid = ''; if ($invalidPersons{$row[0]}) { $invalid = ' INVALID'; }
      $matches{"$row[2]$invalid ( $id ) "}++; }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBPersonAutocomplete

sub getAnyWBPictureAutocomplete {			# autocomplete on OA config that has multiple values per row
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my $result;

  my @tables = qw( pic_source );			# match on pic_source first, then on pic_name ID
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT pic_name.pic_name, ${table}.$table FROM pic_name, $table WHERE pic_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    $result = $dbh->prepare( "SELECT pic_name.pic_name, ${table}.$table FROM pic_name, $table WHERE pic_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$words' AND LOWER(${table}.$table) !~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)

  my $table = 'pic_name';				# can't name pic_name twice, so can't add that to generic @tables
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }

  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub sub getAnyWBPictureAutocomplete

sub getAnyWBProcessAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my $table = 'prt_processid';				# can't name prt_processid twice, so can't add that to generic @tables below
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }

  my @tables = qw( prt_processname prt_othername );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT prt_processid.prt_processid, ${table}.${table} FROM prt_processid, $table WHERE ${table}.joinkey IN (SELECT joinkey FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table) AND prt_processid.joinkey = ${table}.joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    $result = $dbh->prepare( "SELECT prt_processid.prt_processid, ${table}.${table} FROM prt_processid, $table WHERE ${table}.joinkey IN (SELECT joinkey FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table) AND prt_processid.joinkey = ${table}.joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBProcessAutocomplete

sub getAnyWBRnaiAutocomplete {
  my ($words) = @_;
  if ($words =~ m/^wbrnai/i) { $words =~ s/^wbrnai//i; } 	# strip out the leading wbrnai so autocomplete works when editing an entry
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( rna_name );						# master record of rnais in rna_name
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table ~ '^$words' ORDER BY joinkey;" ); $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1]"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE $table ~ '$words' ORDER BY joinkey;" ); $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1]"}++; }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBRnaiAutocomplete

sub getAnyWBSeqFeatAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my $table = 'sqf_name';				
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }
  $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
  $result->execute();
  while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[1] ) "}++; }

  my @tables = qw( sqf_publicname sqf_othername );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT sqf_name.sqf_name, ${table}.$table FROM sqf_name, $table WHERE sqf_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    $result = $dbh->prepare( "SELECT sqf_name.sqf_name, ${table}.$table FROM sqf_name, $table WHERE sqf_name.joinkey = ${table}.joinkey AND LOWER(${table}.$table) ~ '$words' AND LOWER(${table}.$table) !~ '^$words' ORDER BY ${table}.$table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1] ( $row[0] ) "}++; }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBSeqFeatAutocomplete

sub getAnyWBSequenceAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( gin_sequence );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY joinkey;" ); $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1]"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' ORDER BY joinkey;" ); $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) { $matches{"$row[1]"}++; }
    last if (scalar keys %matches >= $max_results);
  }
  if (scalar keys %matches >= $max_results) { $t->Replace($max_results - 1, 'no value', 'more ...'); }
  my $matches = join"\n", keys %matches; return $matches;
} # sub getAnyWBSequenceAutocomplete


### END AUTOCOMPLETE ###


### VALID VALUE ###

sub getAnySpecificValidValue {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyValidValue($userValue); }
  elsif ($ontology_type eq 'Concurhst') {       ($matches) = &getAnyConcurhstValidValue($userValue); }
  elsif ($ontology_type eq 'Discurhst') {       ($matches) = &getAnyDiscurhstValidValue($userValue); }
  elsif ($ontology_type eq 'Ditcurhst') {       ($matches) = &getAnyDitcurhstValidValue($userValue); }
  elsif ($ontology_type eq 'Expr') {            ($matches) = &getAnyExprValidValue($userValue); }
  elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeValidValue($userValue); }
  elsif ($ontology_type eq 'Transgene') {       ($matches) = &getAnyTransgeneValidValue($userValue); }
  elsif ($ontology_type eq 'WBConstruct') {     ($matches) = &getAnyWBConstructValidValue($userValue); }
  elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneValidValue($userValue); }
  elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionValidValue($userValue); }
  elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperValidValue($userValue); }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonValidValue($userValue); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureValidValue($userValue); }
  elsif ($ontology_type eq 'WBProcess') {       ($matches) = &getAnyWBProcessValidValue($userValue); }
  elsif ($ontology_type eq 'WBRnai') {          ($matches) = &getAnyWBRnaiValidValue($userValue); }
  elsif ($ontology_type eq 'WBSeqFeat') {       ($matches) = &getAnyWBSeqFeatValidValue($userValue); }
  elsif ($ontology_type eq 'WBSequence') {      ($matches) = &getAnyWBSequenceValidValue($userValue); }
  return $matches;
} # sub getAnySpecificValidValue

sub getAnyAntibodyValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?)$/ ) { $value = $1; }
  my $table =  'abp_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyAntibodyValidValue

sub getAnyConcurhstValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?)$/ ) { $value = $1; }
  my $table =  'con_curator';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyConcurhstValidValue

sub getAnyDiscurhstValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?)$/ ) { $value = $1; }
  my $table =  'dis_curator';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyDiscurhstValidValue

sub getAnyDitcurhstValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?)$/ ) { $value = $1; }
  my $table =  'dit_curator';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyDitcurhstValidValue

sub getAnyExprValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?)$/ ) { $value = $1; }
  my $table =  'exp_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyExprValidValue

sub getAnyMoleculeValidValue {
  my ($userValue) = @_;
#   my ($value, $joinkey, $syn) = ('bad', 'bad', 'bad');
#   if ( $userValue =~ m/^(.*?) \( (\d+) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( (\d+) \) $/; }
#   elsif ( $userValue =~ m/^(.*?) \( (\d+) \) \[([\w:]+)\]$/ ) { ($syn, $joinkey, $value) = $userValue =~ m/^(.*?) \( (\d+) \) \[([\w:]+)\]$/; }
#   my $table =  'mop_molecule';
#   my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value' AND joinkey = '$joinkey';" );
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*) \) $/; }
  my $table = 'mop_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );	# no joinkey here, not using IDs
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyMoleculeValidValue

sub getAnyTransgeneValidValue {
  my ($userValue) = @_;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*) \) $/; }
  my $table = 'trp_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );	# no joinkey here, not using IDs
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyTransgeneValidValue

sub getAnyWBConstructValidValue {
  my ($userValue) = @_;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*) \) $/; }
  my $table =  'cns_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyConstructValidValue

sub getAnyWBGeneValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey, $syn) = ('bad', 'bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( WBGene(.*?) \) $/; }
  elsif ( $userValue =~ m/^(.*?) \( WBGene(\d+) \) \[(.*?)\]$/ ) { ($syn, $joinkey, $value) = $userValue =~ m/^(.*?) \( WBGene(\d+) \) \[(.*?)\]$/; }
  my @tables = qw( gin_locus gin_seqname gin_wbgene gin_synonyms );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value' AND joinkey = '$joinkey';" );
    $result->execute(); my @row = $result->fetchrow();
    if ($row[0]) { return "true"; } }
  return "false";
} # sub getAnyWBGeneValidValue

sub getAnyWBInteractionValidValue {
  my ($userValue) = @_;
  $userValue =~ s/^WBInteraction//; 	# strip out the leading wbinteraction because int_index only holds the numbers but the IDs have the whole term
  my $joinkey = 'bad';
  my $result = $dbh->prepare( "SELECT * FROM int_index WHERE joinkey = '$userValue';" ); $result->execute();
  my @row = $result->fetchrow();	# master record of interactions in int_index not int_name nor grg_intid
  if ($row[0]) { return "true"; }
  return "false";
} # sub getAnyWBInteractionValidValue

sub getAnyWBPaperValidValue {
  my ($userValue) = @_;
  my $joinkey = 'bad';
  if ( $userValue =~ m/^WBPaper(\d{8})$/ ) { ($joinkey) = $userValue =~ m/^WBPaper(\d{8})$/; }
  my $result = $dbh->prepare( "SELECT * FROM pap_status WHERE joinkey = '$joinkey';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBPaperValidValue

sub getAnyWBPersonValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( WBPerson(.*?) \) $/; $joinkey = 'two' . $joinkey; }
  my $table =  'two_standardname';
  if ($value =~ m/\'/) { $value =~ s/\'/''/g; }
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value' AND joinkey = '$joinkey';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBPersonValidValue

sub getAnyWBPictureValidValue {
  my ($userValue) = @_;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*) \) $/; }
  my $table = 'pic_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );	# no joinkey here, not using IDs
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBPictureValidValue

sub getAnyWBProcessValidValue {
  my ($userValue) = @_;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*) \) $/; }
  my $table = 'prt_processid';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );	# no joinkey here, not using IDs
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBProcessValidValue

sub getAnyWBRnaiValidValue {
  my ($userValue) = @_;
  my $joinkey = 'bad';
  my $result = $dbh->prepare( "SELECT * FROM rna_name WHERE rna_name = '$userValue';" ); $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; }
  return "false";
} # sub getAnyWBRnaiValidValue

sub getAnyWBSeqFeatValidValue {
  my ($userValue) = @_;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*) \) $/; }
  my $table =  'sqf_name';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value';" );
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBSeqFeatValidValue

sub getAnyWBSequenceValidValue {
  my ($userValue) = @_;
  my $table = 'gin_sequence';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$userValue';" );	# no joinkey here, not using IDs
  $result->execute();
  my @row = $result->fetchrow();
  if ($row[0]) { return "true"; } 
  return "false";
} # sub getAnyWBSequenceValidValue

### END VALID VALUE ###


### TERM INFO ### 

sub getAnySpecificTermInfo {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyTermInfo($userValue); }
  elsif ($ontology_type eq 'Concurhst') {       ($matches) = &getAnyConcurhstTermInfo($userValue); }
  elsif ($ontology_type eq 'Discurhst') {       ($matches) = &getAnyDiscurhstTermInfo($userValue); }
  elsif ($ontology_type eq 'Ditcurhst') {       ($matches) = &getAnyDitcurhstTermInfo($userValue); }
  elsif ($ontology_type eq 'Expr') {            ($matches) = &getAnyExprTermInfo($userValue); }
  elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeTermInfo($userValue); }
  elsif ($ontology_type eq 'Transgene') {       ($matches) = &getAnyTransgeneTermInfo($userValue); }
  elsif ($ontology_type eq 'WBConstruct') {     ($matches) = &getAnyWBConstructTermInfo($userValue); }
  elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneTermInfo($userValue); }
  elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureTermInfo($userValue); }
  elsif ($ontology_type eq 'WBProcess') {       ($matches) = &getAnyWBProcessTermInfo($userValue); }
  elsif ($ontology_type eq 'WBRnai') {          ($matches) = &getAnyWBRnaiTermInfo($userValue); }
  elsif ($ontology_type eq 'WBSeqFeat') {       ($matches) = &getAnyWBSeqFeatTermInfo($userValue); }
  elsif ($ontology_type eq 'WBSequence') {      ($matches) = &getAnyWBSequenceTermInfo($userValue); }
  return $matches;
} # sub getAnySpecificTermInfo

sub getAnyAntibodyTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_;
  my $joinkey; my $to_print;
  my $name; my $origpub; my $laboratory;
  my $result = $dbh->prepare( "SELECT * FROM abp_name WHERE abp_name = '$userValue' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $joinkey = $row[0]; } }
  $result = $dbh->prepare( "SELECT * FROM abp_original_publication WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $origpub = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM abp_laboratory WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $laboratory = $row[1]; } }

  $to_print .= "pgid: <span style=\"font-weight: bold\">$joinkey</span><br />\n";
  $to_print .= "antibody: $userValue<br />\n";
  if ($origpub) { 
    my ($joinkey) = $origpub =~ m/WBPaper(\d+)/; $to_print .= "Original Publication: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; }
  if ($laboratory) { $to_print .= "Laboratory : $laboratory<br />\n"; }
  $to_print .= "<hr>\n";
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyAntibodyTermInfo

sub getAnyConcurhstTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_;
  my $joinkey; my $to_print;
  my $name; my %curators; my %twoToStdname;
  my $result = $dbh->prepare( "SELECT * FROM con_curator_hst WHERE joinkey = '$userValue' ORDER BY con_timestamp;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { 
    my $timestamp = $row[2]; $row[1] =~ s/WBPerson/two/;
    if ($timestamp =~ m/^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2})/) { $curators{all}{$row[1]}++; $curators{time}{$1}{$row[1]}++; } } }
  my $twos = join"','", keys %{ $curators{all} };
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey IN ('$twos')" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $twoToStdname{$row[0]} = $row[2]; } }

  $to_print .= "pgid: <span style=\"font-weight: bold\">$userValue</span><br />\n";
  foreach my $timestamp (sort keys %{ $curators{time} }) {
    foreach my $two (sort keys %{ $curators{time}{$timestamp} }) {
      if ($twoToStdname{$two}) { $two = $twoToStdname{$two}; }
      $to_print .= "curator : $two $timestamp<br />\n"; } }
  $to_print .= "<hr>\n";
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getConcurhstTermInfo

sub getAnyDiscurhstTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_;
  my $joinkey; my $to_print;
  my $name; my %curators; my %twoToStdname;
  my $result = $dbh->prepare( "SELECT * FROM dis_curator_hst WHERE joinkey = '$userValue' ORDER BY dis_timestamp;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { 
    my $timestamp = $row[2]; $row[1] =~ s/WBPerson/two/;
    if ($timestamp =~ m/^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2})/) { $curators{all}{$row[1]}++; $curators{time}{$1}{$row[1]}++; } } }
  my $twos = join"','", keys %{ $curators{all} };
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey IN ('$twos')" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $twoToStdname{$row[0]} = $row[2]; } }

  $to_print .= "pgid: <span style=\"font-weight: bold\">$userValue</span><br />\n";
  foreach my $timestamp (sort keys %{ $curators{time} }) {
    foreach my $two (sort keys %{ $curators{time}{$timestamp} }) {
      if ($twoToStdname{$two}) { $two = $twoToStdname{$two}; }
      $to_print .= "curator : $two $timestamp<br />\n"; } }
  $to_print .= "<hr>\n";
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getDiscurhstodyTermInfo

sub getAnyDitcurhstTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_;
  my $joinkey; my $to_print;
  my $name; my %curators; my %twoToStdname;
  my $result = $dbh->prepare( "SELECT * FROM dit_curator_hst WHERE joinkey = '$userValue' ORDER BY dit_timestamp;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { 
    my $timestamp = $row[2]; $row[1] =~ s/WBPerson/two/;
    if ($timestamp =~ m/^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2})/) { $curators{all}{$row[1]}++; $curators{time}{$1}{$row[1]}++; } } }
  my $twos = join"','", keys %{ $curators{all} };
  $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey IN ('$twos')" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $twoToStdname{$row[0]} = $row[2]; } }

  $to_print .= "pgid: <span style=\"font-weight: bold\">$userValue</span><br />\n";
  foreach my $timestamp (sort keys %{ $curators{time} }) {
    foreach my $two (sort keys %{ $curators{time}{$timestamp} }) {
      if ($twoToStdname{$two}) { $two = $twoToStdname{$two}; }
      $to_print .= "curator : $two $timestamp<br />\n"; } }
  $to_print .= "<hr>\n";
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getDitcurhstodyTermInfo

sub getAnyExprTermInfo {		# get term info for expr pattern objects from exp_ tables, while converting some IDs to names and others to IDs + names + synonyms
  my ($userValue) = @_;
  my $joinkeys; my $to_print; my %joinkeys;
  my $name; my $subcellloc; my $reportergene; my $insitu; my $rtpcr; my $northern; my $western; my $antibody_text; my $antibody; my $pattern; my $transgene; my $paper; my $qualifier = ''; my $qualifiertext = '';
  my $genes; my %genes; my $anats; my %anats; my $goids; my %goids; my $lifestages; my %lifestages;
  my $result = $dbh->prepare( "SELECT * FROM exp_name WHERE exp_name = '$userValue' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $joinkeys{$row[0]}++; } }
  $joinkeys = join"','", keys %joinkeys;
  $result = $dbh->prepare( "SELECT * FROM exp_subcellloc WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $subcellloc = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_reportergene WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $reportergene = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_insitu WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $insitu = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_rtpcr WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $rtpcr = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_northern WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $northern = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_western WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $western = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_antibodytext WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $antibody_text = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_antibody WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $antibody = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_pattern WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $pattern = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_transgene WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $transgene = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_paper WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $paper = $row[1]; } }
#   $result = $dbh->prepare( "SELECT * FROM exp_qualifier WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
#   while (my @row = $result->fetchrow) { if ($row[0]) { $qualifier = $row[1]; } }
#   $result = $dbh->prepare( "SELECT * FROM exp_qualifiertext WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
#   while (my @row = $result->fetchrow) { if ($row[0]) { $qualifiertext = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM exp_gene WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) {
    my (@genes) = $row[1] =~ m/WBGene(\d+)/g;
    foreach my $gene (@genes) {
      my $gene_row = "Gene : WBGene$gene"; 
      my @tables = qw( gin_locus gin_seqname gin_synonyms );
      foreach my $table (@tables) {
        my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$gene';" ); $result2->execute(); 
        while (my @row2 = $result2->fetchrow) { $gene_row .= ", $row2[1]"; } } 
      $gene_row .= "<br />\n"; 
      $genes{$gene_row}++; } } }
  $genes = join"", sort keys %genes;
  $result = $dbh->prepare( "SELECT * FROM exp_anatomy WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) {
    my (@anats) = $row[1] =~ m/(WBbt:\d+)/g;
    foreach my $anat (@anats) {
      my $anat_name = ''; my $qualifier = ''; my $qualifiertext = '';
      my $result2 = $dbh->prepare( "SELECT * FROM obo_name_anatomy WHERE joinkey = '$anat';" ); $result2->execute(); 
      my @row2 = $result2->fetchrow(); if ($row2[1]) { $anat_name = $row2[1]; }
      my $result3 = $dbh->prepare( "SELECT * FROM exp_qualifier WHERE joinkey = '$row[0]';" ); $result3->execute(); 
      my @row3 = $result3->fetchrow(); if ($row3[1]) { $qualifier = $row3[1]; }
      my $result4 = $dbh->prepare( "SELECT * FROM exp_qualifiertext WHERE joinkey = '$row[0]';" ); $result4->execute(); 
      my @row4 = $result4->fetchrow(); if ($row4[1]) { $qualifiertext = $row4[1]; }
      $anats{"Anatomy_term : \"$anat_name is $anat\" $qualifier $qualifiertext<br />\n"}++; } } }
  $anats = join"", sort keys %anats;
  $result = $dbh->prepare( "SELECT * FROM exp_goid WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) {
    my (@goids) = $row[1] =~ m/(GO:\d+)/g;
    foreach my $goid (@goids) {
      my $goid_name = '';
      my $result2 = $dbh->prepare( "SELECT * FROM obo_name_goid WHERE joinkey = '$goid';" ); $result2->execute(); 
      my @row2 = $result2->fetchrow(); if ($row2[1]) { $goid_name = $row2[1]; }
      $goids{"GO_term : \"$goid\" $goid_name<br />\n"}++;  } } }
  $goids = join"", sort keys %goids;
  $result = $dbh->prepare( "SELECT * FROM exp_lifestage WHERE joinkey IN ('$joinkeys') ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) {
    my (@lifestages) = $row[1] =~ m/(WBls:\d+)/g;
    foreach my $lifestage (@lifestages) {
      my $lifestage_name = '';
      my $result2 = $dbh->prepare( "SELECT * FROM obo_name_lifestage WHERE joinkey = '$lifestage';" ); $result2->execute(); 
      my @row2 = $result2->fetchrow(); if ($row2[1]) { $lifestage_name = $row2[1]; }
      $lifestages{"Life_stage : \"$lifestage_name\"<br />\n"}++;  } } }
  $lifestages = join"", sort keys %lifestages;

#   $to_print .= "pgid: <span style=\"font-weight: bold\">$joinkey</span><br />\n";
  $to_print .= "Expr id: $userValue<br />\n";
  if ($genes) { $to_print .= "$genes"; }
  if ($anats) { $to_print .= "$anats"; }
  if ($goids) { $to_print .= "$goids"; }
  if ($subcellloc) { $to_print .= "Subcellular Localization : $subcellloc<br />\n"; }
  if ($lifestages) { $to_print .= "$lifestages"; }
  if ($antibody_text) { $to_print .= "Antibody_text : $antibody_text<br />\n"; }
  if ($reportergene) { $to_print .= "Reporter Gene : $reportergene<br />\n"; }
  if ($insitu) { $to_print .= "In_Situ : $insitu<br />\n"; }
  if ($rtpcr) { $to_print .= "RT_PCR : $rtpcr<br />\n"; }
  if ($northern) { $to_print .= "Northern : $northern<br />\n"; }
  if ($western) { $to_print .= "Western : $western<br />\n"; }
  if ($antibody) { $to_print .= "Antibody_info : $antibody<br />\n"; }
  if ($pattern) { $to_print .= "Pattern : $pattern<br />\n"; }
  if ($transgene) { $to_print .= "Trangene : $transgene<br />\n"; }
  if ($paper) { $to_print .= "Reference : $paper<br />\n"; }
  $to_print .= "<hr>\n";
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyExprTermInfo

sub getAnyMoleculeTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_; my $objId; my $joinkey = '';
#   if ($userValue =~ m/\( (\d+) \)/) { $joinkey = $1; } else { $joinkey = $userValue; }	# when autocomplete had the pgid for molecules
  if ($userValue =~ m/\( (\d+) \)/) { $objId = $1; } else { $objId = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM mop_name WHERE mop_name = '$objId' ORDER BY mop_timestamp DESC;" );
  $result->execute(); my @row = $result->fetchrow(); $joinkey = $row[0];	# each wbmol objid can only have one pgid
  my $to_print;
  my $wbmolid; my $molecule_name; my $publicname; my $synonyms; my $chemi; my $chebi; my $kegg; my $remark; my $paper; my $curator;
  $result = $dbh->prepare( "SELECT * FROM mop_name WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $wbmolid = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_molecule WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $molecule_name = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_publicname WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $publicname = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_synonym WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $synonyms = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_chemi WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $chemi = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_chebi WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $chebi = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_kegg WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $kegg = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_remark WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $remark = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_paper WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $paper = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM mop_curator WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
  @row = $result->fetchrow(); { if ($row[0]) { my ($cur_id) = $row[1] =~ m/(\d+)/; 
    my $result2 = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = 'two$cur_id' ;" ); $result2->execute(); my @row2 = $result2->fetchrow(); $curator = $row2[2]; } }

#   $to_print .= "pgid: <span style=\"font-weight: bold\">$joinkey</span><br />\n";
  $to_print .= "wbmolid: <span style=\"font-weight: bold\">$wbmolid</span><br />\n";
  $to_print .= "molecule: $molecule_name<br />\n";
  $to_print .= "public name: $publicname<br />\n";
  if ($synonyms) {
    my @syns = split/ \| /, $synonyms;
    foreach my $syn (@syns) { $to_print .= "synonym: \"$syn\"<br />\n"; } }
  $to_print .= "CTD: <a href=\"http://ctd.mdibl.org/detail.go?type=chem&acc=$molecule_name\" target=\"new\">$molecule_name</a><br />\n";
  $to_print .= "NLM_MeSH: <a href=\"http://www.nlm.nih.gov/cgi/mesh/2010/MB_cgi?field=uid&term=$molecule_name\" target=\"new\">$molecule_name</a><br />\n";
  if ($chebi) { $to_print .= "ChEBI: <a href=\"http://www.ebi.ac.uk/chebi/advancedSearchFT.do?searchString=$chebi\" target=\"new\">$chebi</a><br />\n"; }
  if ($kegg) { $to_print .= "KEGG: <a href=\"http://www.genome.jp/dbget-bin/www_bget?cpd:$kegg\" target=\"new\">$kegg</a><br />\n"; }
  if ($chemi) { $to_print .= "ChemIDplus: <a href=\"http://www.ncbi.nlm.nih.gov/sites/entrez?term=${chemi}~[synonym]&cmd=search&db=pcsubstance\" target=\"new\">$chemi</a><br />\n"; }
  if ($paper) { my @papers = split/","/, $paper; foreach my $pap (@papers) { my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
  if ($curator) { $to_print .= "Curator: $curator<br />\n"; }
  if ($remark) { $to_print .= "Remark: $remark<br />\n"; }
  $to_print .= "<hr>\n";
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyMoleculeTermInfo

sub getAnyTransgeneTermInfo {
  my ($userValue) = @_; my %joinkeys;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
    else { $value = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM trp_name WHERE trp_name = '$value' ORDER BY trp_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( trp_mergedinto trp_publicname trp_synonym trp_paper trp_summary trp_remark trp_reporter_type trp_driven_by_gene );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $value<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) { 
    if ($table eq 'trp_paper') { 
        my @papers = split/","/, $entry; foreach my $pap (@papers) { 
          my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
      elsif ($table eq 'trp_driven_by_gene') { 
        my (@genes) = $entry =~ m/WBGene(\d+)/g;
        foreach my $gene (@genes) {
          my $gene_row = "trp_driven_by_gene: WBGene$gene"; 
          my @tables = qw( gin_locus gin_seqname gin_synonyms );
          foreach my $table (@tables) {
            my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$gene';" ); $result2->execute(); 
            while (my @row2 = $result2->fetchrow) { $gene_row .= ", $row2[1]"; } } 
          $gene_row .= "<br />\n"; 
          $to_print .= "$gene_row"; } }
      else { $to_print .= "${table}: $entry<br />\n"; } } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyTransgeneTermInfo

sub getAnyWBConstructTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_; my %joinkeys;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
    else { $value = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM cns_name WHERE cns_name = '$value' ORDER BY cns_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( publicname othername summary constructtype remark constructionsummary );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM cns_$table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $value<br />\n";
  foreach my $table (@tables) {
    foreach my $entry (sort keys %{ $info{$table} }) { 
      $to_print .= "${table}: $entry<br />\n"; } }
  $result = $dbh->prepare( "SELECT * FROM trp_publicname WHERE joinkey IN (SELECT joinkey FROM trp_construct WHERE trp_construct ~ '$value');" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $to_print .= "transgene: $row[1]<br />\n"; }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBConstructTermInfo

sub getAnyWBGeneTermInfo {
  my ($userValue) = @_;
  my ($joinkey) = $userValue =~ m/WBGene(\d+)/; my $to_print;	# has to match a WBGene from the info
  my %syns; my $locus; my $dead; my $species;
  my $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey = '$joinkey';" ); $result->execute(); 
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey = '$joinkey';" ); $result->execute(); 
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$joinkey';" ); $result->execute(); 
  my @row = $result->fetchrow(); $locus = $row[1];
  $result = $dbh->prepare( "SELECT * FROM gin_dead WHERE joinkey = '$joinkey';" ); $result->execute(); 
  @row = $result->fetchrow(); $dead = $row[1];
  $result = $dbh->prepare( "SELECT * FROM gin_species WHERE joinkey = '$joinkey';" ); $result->execute(); 
  @row = $result->fetchrow(); $species = $row[1];
  if ($userValue) { $to_print .= "id: WBGene$joinkey<br />\n"; }
#   my $dev_link = "http://dev.wormbase.org/db/gene/gene?name=WBGene$joinkey;class=Gene";
#   if ($locus) { $to_print .= "locus: <a target=\"new\" href=\"$dev_link\">$locus</a><br />\n"; }
  my $wormbase_link = "http://www.wormbase.org/species/c_elegans/gene/WBGene$joinkey;class=Gene";
  if ($locus) { $to_print .= "locus: <a target=\"new\" href=\"$wormbase_link\">$locus</a><br />\n"; }
  if ($species) { $to_print .= "species: $species<br />\n"; }
  if ($dead) { $to_print .= "DEAD: $dead<br />\n"; }
  foreach my $syn (sort keys %syns) { $to_print .= "synonym: $syn<br />\n"; }

  $result = $dbh->prepare( "SELECT * FROM con_desctext WHERE joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene ~ 'WBGene$joinkey') AND joinkey IN (SELECT joinkey FROM con_desctype WHERE con_desctype = 'Concise_description')" ); $result->execute(); @row = $result->fetchrow(); 
  if ($row[1]) { $to_print .= "Concise description: $row[1]<br />\n"; }
  $result = $dbh->prepare( "SELECT * FROM con_desctext WHERE joinkey IN (SELECT joinkey FROM con_wbgene WHERE con_wbgene ~ 'WBGene$joinkey') AND joinkey IN (SELECT joinkey FROM con_desctype WHERE con_desctype = 'Automated_concise_description')" ); $result->execute(); @row = $result->fetchrow(); 
  if ($row[1]) { $to_print .= "Automated_concise description: $row[1]<br />\n"; }
  $result = $dbh->prepare( "SELECT * FROM dis_diseaserelevance WHERE joinkey IN (SELECT joinkey FROM dis_wbgene WHERE dis_wbgene ~ 'WBGene$joinkey')" ); $result->execute(); @row = $result->fetchrow(); 
  if ($row[1]) { $to_print .= "Disease relevance : $row[1]<br />\n"; }

  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBGeneTermInfo

sub getAnyWBInteractionTermInfo {
  my ($userValue) = @_;
  my $to_print = "id: $userValue\n";
  my ($from_int_name, $from_grg_intid) = (0, 0);
  my $result = $dbh->prepare( "SELECT joinkey FROM int_name WHERE int_name = '$userValue';" ); $result->execute(); 	# all interaction objects have a single pgid so this is overkill
  my @row = $result->fetchrow(); { if ($row[0]) { $from_int_name++; } }
  $result = $dbh->prepare( "SELECT joinkey FROM grg_intid WHERE grg_intid = '$userValue';" ); $result->execute(); 	# some gene regulation objects have multiple pgids, but this might switch to only one pgid
  @row = $result->fetchrow(); { if ($row[0]) { $from_grg_intid++; } }

  if ($from_grg_intid) {
    $to_print .= "Source: Gene Regulation OA\n"; }

  elsif ($from_int_name) {
    $to_print .= "Source: Interaction OA\n";
    my $result = $dbh->prepare( "SELECT int_paper FROM int_paper WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 	# all interaction objects have a single pgid so this is overkill
    my @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Paper: $row[0]\n"; } }
    $result = $dbh->prepare( "SELECT int_type FROM int_type WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Interaction Type: $row[0]\n"; } }

    $result = $dbh->prepare( "SELECT int_genenondir FROM int_genenondir WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); if ($row[0]) {
      my %gene_to_locus; my (@genes) = $row[0] =~ m/WBGene(\d+)/g;
      if (scalar(@genes)) {
        my @tables = qw( gin_synonyms gin_seqname gin_locus ); my $genes = join"','", @genes;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$genes' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $gene_to_locus{$row2[0]} = $row2[1]; } }
        my @genes_line;
        foreach my $genejoinkey (@genes) { 
          if ($gene_to_locus{$genejoinkey}) { push @genes_line, $gene_to_locus{$genejoinkey}; } 
            else { push @genes_line, "WBGene$genejoinkey"; } }
        my $genes_line = join", ", @genes_line;
        $to_print .= "Non-directional Gene: $genes_line\n"; } }
    $result = $dbh->prepare( "SELECT int_variationnondir FROM int_variationnondir WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) {
      my %wbvar_to_name; my (@variations) = $row[0] =~ m/(WBVar\d+)/g;
      if (scalar(@variations)) {
        my @tables = qw( obo_name_variation ); my $variations = join"','", @variations;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$variations' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $wbvar_to_name{$row2[0]} = $row2[1]; } }
        my @vars_line;
        foreach my $varid (@variations) { 
          if ($wbvar_to_name{$varid}) { push @vars_line, $wbvar_to_name{$varid}; } 
            else { push @vars_line, "$varid"; } }
        my $vars_line = join", ", @vars_line;
        $to_print .= "Non-directional Variation: $vars_line\n"; } } }
  
    $result = $dbh->prepare( "SELECT int_geneone FROM int_geneone WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); if ($row[0]) {
      my %gene_to_locus; my (@genes) = $row[0] =~ m/WBGene(\d+)/g;
      if (scalar(@genes)) {
        my @tables = qw( gin_synonyms gin_seqname gin_locus ); my $genes = join"','", @genes;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$genes' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $gene_to_locus{$row2[0]} = $row2[1]; } }
        my @genes_line;
        foreach my $genejoinkey (@genes) { 
          if ($gene_to_locus{$genejoinkey}) { push @genes_line, $gene_to_locus{$genejoinkey}; } 
            else { push @genes_line, "WBGene$genejoinkey"; } }
        my $genes_line = join", ", @genes_line;
        $to_print .= "Effector Gene: $genes_line\n"; } }
    $result = $dbh->prepare( "SELECT int_variationone FROM int_variationone WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) {
      my %wbvar_to_name; my (@variations) = $row[0] =~ m/(WBVar\d+)/g;
      if (scalar(@variations)) {
        my @tables = qw( obo_name_variation ); my $variations = join"','", @variations;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$variations' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $wbvar_to_name{$row2[0]} = $row2[1]; } }
        my @vars_line;
        foreach my $varid (@variations) { 
          if ($wbvar_to_name{$varid}) { push @vars_line, $wbvar_to_name{$varid}; } 
            else { push @vars_line, "$varid"; } }
        my $vars_line = join", ", @vars_line;
        $to_print .= "Effector Variation: $vars_line\n"; } } }
    $result = $dbh->prepare( "SELECT int_intravariationone FROM int_intravariationone WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) {
      my %wbvar_to_name; my (@variations) = $row[0] =~ m/(WBVar\d+)/g;
      if (scalar(@variations)) {
        my @tables = qw( obo_name_variation ); my $variations = join"','", @variations;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$variations' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $wbvar_to_name{$row2[0]} = $row2[1]; } }
        my @vars_line;
        foreach my $varid (@variations) { 
          if ($wbvar_to_name{$varid}) { push @vars_line, $wbvar_to_name{$varid}; } 
            else { push @vars_line, "$varid"; } }
        my $vars_line = join", ", @vars_line;
        $to_print .= "Effector Intragenic Variation: $vars_line\n"; } } }
#     $result = $dbh->prepare( "SELECT int_transgeneone FROM int_transgeneone WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
#     @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Effector Transgene Name: $row[0]\n"; } }
#     $result = $dbh->prepare( "SELECT int_transgeneonegene FROM int_transgeneonegene WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
#     @row = $result->fetchrow(); { if ($row[0]) { 
#       my %gene_to_locus; my (@genes) = $row[0] =~ m/WBGene(\d+)/g;
#       if (scalar(@genes)) {
#         my @tables = qw( gin_synonyms gin_seqname gin_locus ); my $genes = join"','", @genes;
#         foreach my $table (@tables) {
#           my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$genes' );" ); $result2->execute();
#           while (my @row2 = $result2->fetchrow) { $gene_to_locus{$row2[0]} = $row2[1]; } }
#         my @genes_line;
#         foreach my $genejoinkey (@genes) { 
#           if ($gene_to_locus{$genejoinkey}) { push @genes_line, $gene_to_locus{$genejoinkey}; } 
#             else { push @genes_line, "WBGene$genejoinkey"; } }
#         my $genes_line = join", ", @genes_line;
#         $to_print .= "Effector Transgene Gene: $genes_line\n"; } } }
    $result = $dbh->prepare( "SELECT int_otheronetype FROM int_otheronetype WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Effector Other Type: $row[0]\n"; } }
    $result = $dbh->prepare( "SELECT int_otherone FROM int_otherone WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Effector Other: $row[0]\n"; } }
  
    $result = $dbh->prepare( "SELECT int_genetwo FROM int_genetwo WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); if ($row[0]) {
      my %gene_to_locus; my (@genes) = $row[0] =~ m/WBGene(\d+)/g;
      if (scalar(@genes)) {
        my @tables = qw( gin_synonyms gin_seqname gin_locus ); my $genes = join"','", @genes;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$genes' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $gene_to_locus{$row2[0]} = $row2[1]; } }
        my @genes_line;
        foreach my $genejoinkey (@genes) { 
          if ($gene_to_locus{$genejoinkey}) { push @genes_line, $gene_to_locus{$genejoinkey}; } 
            else { push @genes_line, "WBGene$genejoinkey"; } }
        my $genes_line = join", ", @genes_line;
        $to_print .= "Affected Gene: $genes_line\n"; } }
    $result = $dbh->prepare( "SELECT int_variationtwo FROM int_variationtwo WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) {
      my %wbvar_to_name; my (@variations) = $row[0] =~ m/(WBVar\d+)/g;
      if (scalar(@variations)) {
        my @tables = qw( obo_name_variation ); my $variations = join"','", @variations;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$variations' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $wbvar_to_name{$row2[0]} = $row2[1]; } }
        my @vars_line;
        foreach my $varid (@variations) { 
          if ($wbvar_to_name{$varid}) { push @vars_line, $wbvar_to_name{$varid}; } 
            else { push @vars_line, "$varid"; } }
        my $vars_line = join", ", @vars_line;
        $to_print .= "Affected Variation: $vars_line\n"; } } }
    $result = $dbh->prepare( "SELECT int_intravariationtwo FROM int_intravariationtwo WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) {
      my %wbvar_to_name; my (@variations) = $row[0] =~ m/(WBVar\d+)/g;
      if (scalar(@variations)) {
        my @tables = qw( obo_name_variation ); my $variations = join"','", @variations;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$variations' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $wbvar_to_name{$row2[0]} = $row2[1]; } }
        my @vars_line;
        foreach my $varid (@variations) { 
          if ($wbvar_to_name{$varid}) { push @vars_line, $wbvar_to_name{$varid}; } 
            else { push @vars_line, "$varid"; } }
        my $vars_line = join", ", @vars_line;
        $to_print .= "Affected Intragenic Variation: $vars_line\n"; } } }
#     $result = $dbh->prepare( "SELECT int_transgenetwo FROM int_transgenetwo WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
#     @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Affected Transgene Name: $row[0]\n"; } }
#     $result = $dbh->prepare( "SELECT int_transgenetwogene FROM int_transgenetwogene WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
#     @row = $result->fetchrow(); { if ($row[0]) { 
#       my %gene_to_locus; my (@genes) = $row[0] =~ m/WBGene(\d+)/g;
#       if (scalar(@genes)) {
#         my @tables = qw( gin_synonyms gin_seqname gin_locus ); my $genes = join"','", @genes;
#         foreach my $table (@tables) {
#           my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$genes' );" ); $result2->execute();
#           while (my @row2 = $result2->fetchrow) { $gene_to_locus{$row2[0]} = $row2[1]; } }
#         my @genes_line;
#         foreach my $genejoinkey (@genes) { 
#           if ($gene_to_locus{$genejoinkey}) { push @genes_line, $gene_to_locus{$genejoinkey}; } 
#             else { push @genes_line, "WBGene$genejoinkey"; } }
#         my $genes_line = join", ", @genes_line;
#         $to_print .= "Affected Transgene Gene: $genes_line\n"; } } }
    $result = $dbh->prepare( "SELECT int_othertwotype FROM int_othertwotype WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Affected Other Type: $row[0]\n"; } }
    $result = $dbh->prepare( "SELECT int_othertwo FROM int_othertwo WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Affected Other: $row[0]\n"; } }
  
    $result = $dbh->prepare( "SELECT int_transgene FROM int_transgene WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Transgene Names: $row[0]\n"; } }
    $result = $dbh->prepare( "SELECT int_phenotype FROM int_phenotype WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { 
      my %phenotype_to_name; my (@phenotypes) = $row[0] =~ m/(WBPhenotype:\d+)/g;
      if (scalar(@phenotypes)) {
        my @tables = qw( obo_name_phenotype ); my $phenotypes = join"','", @phenotypes;
        foreach my $table (@tables) {
          my $result2 = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ( '$phenotypes' );" ); $result2->execute();
          while (my @row2 = $result2->fetchrow) { $phenotype_to_name{$row2[0]} = $row2[1]; } }
        my @phenotype_line;
        foreach my $varid (@phenotypes) { 
          if ($phenotype_to_name{$varid}) { push @phenotype_line, "$varid $phenotype_to_name{$varid}"; } 
            else { push @phenotype_line, "$varid"; } }
        my $phenotype_line = join", ", @phenotype_line;
        $to_print .= "Interaction Phenotype: $phenotype_line\n"; } } }
    $result = $dbh->prepare( "SELECT int_remark FROM int_remark WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { $to_print .= "Interaction Remark: $row[0]\n"; } }
    $result = $dbh->prepare( "SELECT * FROM int_curator WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
    @row = $result->fetchrow(); { if ($row[0]) { my ($cur_id) = $row[1] =~ m/(\d+)/; 
      my $result2 = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = 'two$cur_id' ;" ); $result2->execute(); my @row2 = $result2->fetchrow(); my $curator = $row2[2]; $to_print .= "Curator: $curator\n"; } }
  } # if ($from_int_name)

  else {
    $to_print .= "Source: Interaction exists, but neither in Interaction nor GeneRegulation OA\n"; }

  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"<br />\n", @data;
  return $to_print;
} # sub getAnyWBInteractionTermInfo

sub getAnyWBPaperTermInfo {
  my ($userValue) = @_;
  my ($joinkey) = $userValue =~ m/(\d+)/; my $to_print;
  my %title; my %ids; my %pdfs; my %journal; my %year; my %primary; my %type; my %type_index; my %non_nematode; my $status = ''; my %merged_into;
  my $result = $dbh->prepare( "SELECT * FROM pap_status WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $status = $row[1]; } }
  if ($status eq 'invalid') { 
    $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier = '$joinkey' ;" );
    $result->execute(); 
    while (my @row = $result->fetchrow) { if ($row[0]) { $merged_into{$row[0]}++; } }
    my @merged_into = sort keys %merged_into; my $merged_into = join", ", @merged_into;
    $to_print .= "status: <span style=\"color:red\">Invalid paper, merged into $merged_into.</span><br />\n"; }
  $result = $dbh->prepare( "SELECT * FROM pap_title WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) {
      $title{$row[0]}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $ids{$row[0]}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_journal WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $journal{$row[0]}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_year WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $year{$row[0]}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_primary_data WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $primary{$row[0]}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_type_index ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $type_index{$row[0]} = $row[1]; } }
  $result = $dbh->prepare( "SELECT * FROM pap_type WHERE joinkey = '$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { if ($type_index{$row[1]}) { $type{$row[0]}{$type_index{$row[1]}}++; } } }
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path WHERE joinkey = '$joinkey' ORDER BY pap_timestamp;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pdfs{$row[0]}{$row[1]}++; } }
  $result = $dbh->prepare( "SELECT * FROM pap_curation_flags WHERE joinkey = '$joinkey' AND pap_curation_flags = 'non_nematode';" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $non_nematode{$row[0]}{$row[1]}++; } }
  my %pap_transgene; my %trp_temp;
  $result = $dbh->prepare( "SELECT * FROM trp_name WHERE trp_name.joinkey IN (SELECT joinkey FROM trp_paper WHERE trp_paper ~ 'WBPaper$joinkey') ;" );	# query from trp_ tables instead of flatfiles
#   $result = $dbh->prepare( " SELECT trp_name.trp_name, trp_publicname.trp_publicname, trp_synonym.trp_synonym, trp_summary.trp_summary FROM trp_name, trp_publicname, trp_synonym, trp_summary WHERE trp_name.joinkey = trp_publicname.joinkey AND trp_name.joinkey = trp_synonym.joinkey AND trp_name.joinkey = trp_summary.joinkey AND trp_name.joinkey IN (SELECT joinkey FROM trp_paper WHERE trp_paper ~ 'WBPaper$joinkey') ;" );	# this won't work if any of the fields are missing
  $result->execute(); 
  while (my @row = $result->fetchrow) { $trp_temp{trp_name}{$row[0]} = $row[1]; }
  my $trp_keys = join"','", sort keys %{ $trp_temp{trp_name} }; my @trp_tables = qw( trp_publicname trp_summary trp_construct );
  foreach my $trp_table (@trp_tables) { 
    $result = $dbh->prepare( "SELECT * FROM $trp_table WHERE joinkey IN ('$trp_keys')" ); $result->execute(); 
    while (my @row = $result->fetchrow) { $trp_temp{$trp_table}{$row[0]} = $row[1]; } }
  foreach my $trp_key (sort keys %{ $trp_temp{trp_name} }) { 
    my @data; push @data, $trp_temp{trp_name}{$trp_key};
    foreach my $trp_table (@trp_tables) { if ($trp_temp{$trp_table}{$trp_key}) { push @data, $trp_temp{$trp_table}{$trp_key}; } }
    my $trp_data = join"\t", @data; 
    $pap_transgene{$joinkey}{$trp_data}++; }
  my %pap_construct; my %cns_temp;
  $result = $dbh->prepare( "SELECT * FROM cns_name WHERE cns_name.joinkey IN (SELECT joinkey FROM cns_paper WHERE cns_paper ~ 'WBPaper$joinkey') ;" );	# query from cns_ tables instead of flatfiles
  $result->execute(); 
  while (my @row = $result->fetchrow) { $cns_temp{cns_name}{$row[0]} = $row[1]; }
  my $cns_keys = join"','", sort keys %{ $cns_temp{cns_name} }; my @cns_tables = qw( cns_publicname cns_summary cns_newtransgene );
  foreach my $cns_table (@cns_tables) { 
    $result = $dbh->prepare( "SELECT * FROM $cns_table WHERE joinkey IN ('$cns_keys')" ); $result->execute(); 
    while (my @row = $result->fetchrow) { $cns_temp{$cns_table}{$row[0]} = $row[1]; } }
  foreach my $cns_key (sort keys %{ $cns_temp{cns_name} }) { 
    my @data; push @data, $cns_temp{cns_name}{$cns_key};
    foreach my $cns_table (@cns_tables) { if ($cns_temp{$cns_table}{$cns_key}) { push @data, $cns_temp{$cns_table}{$cns_key}; } }
    my $cns_data = join"\t", @data; 
    $pap_construct{$joinkey}{$cns_data}++; }

#       if ($row[1] =~ m/WBGene(\d+)/) { my $wbgene = $1; $expr{$joinkey}{$row[0]}{$wbgene}++; $expr_genes{$wbgene}++; }
#         else { $expr{$joinkey}{$row[0]}{nomatch}++; } } }
#   my $infile = '/home/acedb/karen/populate_gin_variation/transgene_summary_reference.txt';
#   open (IN, "$infile") or die "Cannot open $infile : $!";
#   my $junk = <IN>;
#   while (my $line = <IN>) {
#     chomp $line;
#     next unless ($line =~ m/WBPaper$joinkey/);
#     my ($transgene, $reference, $summary) = split/\t/, $line;
#     my $data = "$transgene\t$summary"; $data =~ s/\"//g; $pap_transgene{$joinkey}{$data}++; }
#   close (IN) or die "Cannot close $infile : $!";
  my %expr; my %expr_genes; my %gene_to_locus;
#   $result = $dbh->prepare( "SELECT * FROM obo_data_exprpattern WHERE obo_data_exprpattern ~ 'WBPaper$joinkey' ;" );
  $result = $dbh->prepare( " SELECT exp_name.exp_name, exp_gene.exp_gene FROM exp_name, exp_gene WHERE exp_name.joinkey = exp_gene.joinkey AND exp_name.joinkey IN (SELECT joinkey FROM exp_paper WHERE exp_paper ~ 'WBPaper$joinkey') ;" );	# query from exp_ tables instead of obo_
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) {
      if ($row[1] =~ m/WBGene(\d+)/) { my $wbgene = $1; $expr{$joinkey}{$row[0]}{$wbgene}++; $expr_genes{$wbgene}++; }
        else { $expr{$joinkey}{$row[0]}{nomatch}++; } } }
  my @expr_genes = keys %expr_genes;
  if (scalar(@expr_genes)) {
    my $expr_genes = join"','", @expr_genes;
    $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey IN ( '$expr_genes' );" ); $result->execute();
    while (my @row = $result->fetchrow) { $gene_to_locus{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey IN ( '$expr_genes' );" ); $result->execute();
    while (my @row = $result->fetchrow) { $gene_to_locus{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey IN ( '$expr_genes' );" ); $result->execute();
    while (my @row = $result->fetchrow) { $gene_to_locus{$row[0]} = $row[1]; } }
  my %pap_genes; 
  $result = $dbh->prepare( "SELECT pap_gene FROM pap_gene WHERE joinkey = '$joinkey'" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $pap_genes{$row[0]}++; } }
  my @pap_genes = keys %pap_genes;
  if (scalar(@pap_genes)) {
    my $pap_genes = join"','", @pap_genes;
    $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey IN ( '$pap_genes' );" ); $result->execute();
    while (my @row = $result->fetchrow) { $gene_to_locus{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey IN ( '$pap_genes' );" ); $result->execute();
    while (my @row = $result->fetchrow) { $gene_to_locus{$row[0]} = $row[1]; }
    $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey IN ( '$pap_genes' );" ); $result->execute();
    while (my @row = $result->fetchrow) { $gene_to_locus{$row[0]} = $row[1]; } }

  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = 'WBPaper$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }

  my $paper_url = "http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey";
  $to_print .= "id: <span style=\"font-weight: bold\"><a href=\"$paper_url\" target=\"new\">WBPaper$joinkey</a></span><br />\n";
  $to_print .= "name: WBPaper$joinkey<br />\n";
  if ($title{$joinkey}) {
      my (@title) = keys %{ $title{$joinkey} };
      my $title = $title[0];
      if ($title =~ m/\"/) { $title =~ s/\"/\\\"/g; }
      if ($title =~ m/\n/) { $title =~ s/\n//g; }
      my $wb_link = "http://wormbase.org/db/misc/paper?name=WBPaper$joinkey;class=Paper";
      $to_print .= "title: <a target=\"new\" href=\"$wb_link\">$title</a><br />\n"; }
  foreach my $pdf (sort keys %{ $pdfs{$joinkey} }) {
    ($pdf) = $pdf =~ m/\/([^\/]*)$/; my $pdf_link = '/~acedb/daniel/' . $pdf;
    $to_print .= "pdf: <a target=\"new\" href=\"$pdf_link\">$pdf</a><br />\n"; }
  foreach my $syn (sort keys %{ $ids{$joinkey} }) {
    if ($syn =~ m/^pmid(\d+)/) { my $url = 'http://www.ncbi.nlm.nih.gov/pubmed/' . $1; $syn =~ s/pmid/PMID:/g; $syn = qq(<a href="$url" target="new">$syn</a>); }
      elsif ($syn =~ m/^doi(.*)/) { my $url = 'http://dx.doi.org/' . $1; $syn = qq(<a href="$url" target="new">$syn</a>); }
    $to_print .= "synonym: \"$syn\"<br />\n"; }
  # to link to paper editor
#   my $query = new CGI;
#   (my $var, my $curator_two) = &getHtmlVar($query, 'curator_two');
#   my $url = 'http://tazendra.caltech.edu/~postgres/cgi-bin/paper_editor.cgi?curator_id=' . $curator_two . '&action=Search&data_number=' . $joinkey;
#   $to_print .= qq(paper_editor : <a href="$url" target="new">edit on tazendra</a><br />\n);
  foreach my $type (sort keys %{ $type{$joinkey} }) {
    $to_print .= "type: \"$type\"<br />\n"; }
  foreach my $primary (sort keys %{ $primary{$joinkey} }) {
    $to_print .= "primary: \"$primary\"<br />\n"; }
  foreach my $non_nematode (sort keys %{ $non_nematode{$joinkey} }) {
    $to_print .= "non_nematode: \"$non_nematode\"<br />\n"; }
  my (@year) = sort keys %{ $year{$joinkey} }; my (@journal) = sort keys %{ $journal{$joinkey} };
  if (scalar(@year) > 1) { $to_print .= "ERROR : multiple years @year<br />\n"; }
    elsif (scalar(@year) > 0) { $to_print .= "Year: $year[0]<br />\n"; }
    else { $to_print .= "Year: BLANK<br />\n"; }
  my $journal_has_permission = 'No &#10008;';
  if (scalar(@journal) > 1) { $to_print .= "ERROR : multiple journals @journal<br />\n"; }
    elsif (scalar(@journal) > 0) { 
      $to_print .= "Journal: $journal[0]<br />\n"; 
      my %journal_has_permission;			# for image_overview below
      my $infile = '/home/acedb/draciti/picture_curatable/journal_with_permission';
      open (IN, "$infile") or die "Cannot open $infile : $!";
      while (my $line = <IN>) { chomp $line; $journal_has_permission{$line}++; }
      close (IN) or die "Cannot close $infile : $!";
      if ($journal_has_permission{$journal[0]}) { $journal_has_permission = 'Yes &#10003;'; } }
    else { $to_print .= "Journal: BLANK<br />\n"; }
  $to_print .= "<hr>\n";
  foreach my $transgene (sort keys %{ $pap_transgene{$joinkey}}) { $to_print .= "transgene: $transgene<br />\n"; }
  foreach my $construct (sort keys %{ $pap_construct{$joinkey}}) { $to_print .= "construct: $construct<br />\n"; }
  foreach my $expr (sort keys %{ $expr{$joinkey}}) {
    my $expr_line = "expr: $expr";
    foreach my $wbgene (sort keys %{ $expr{$joinkey}{$expr} }) {
      if ($wbgene eq 'nomatch') { $expr_line .= " No WBGene match"; }
        else { $expr_line .= " WBGene$wbgene";
               if ($gene_to_locus{$wbgene}) { $expr_line .= " $gene_to_locus{$wbgene}"; } } }
    $to_print .= "$expr_line<br />\n"; }
  if (scalar keys %{ $picturesource{$joinkey} } > 0) {
    $to_print .= qq(image_overview: <a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/generic.cgi?action=PictureByPaper&paperid=$joinkey" target="new">click to see all images</a><br />\n); }
  $to_print .= "Journal_image_permission: $journal_has_permission<br />\n";
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) { 	# all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
  foreach my $wbgene (sort keys %pap_genes) { 
    $to_print .= "gene: WBGene$wbgene"; if ($gene_to_locus{$wbgene}) { $to_print .= " $gene_to_locus{$wbgene}"; } $to_print .= "<br />\n"; }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBPaperTermInfo

sub getAnyWBPersonTermInfo {
  my ($userValue) = @_;
  my $standard_name = $userValue; my $person_id; my $to_print;
  if ($userValue =~ m/(.*?) \( (.*?) \)/) { $standard_name = $1; $person_id = $2; } else { $person_id = $userValue; }
  $person_id =~ s/WBPerson/two/g;
  my $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = '$person_id' ORDER BY two_timestamp DESC;" );
  $result->execute(); my @row = $result->fetchrow();
  my $joinkey = $row[0]; my %emails; if ($row[2]) { $standard_name = $row[2]; }
  $result = $dbh->prepare( "SELECT * FROM two_email WHERE joinkey = '$joinkey';" );
  $result->execute(); while (my @row = $result->fetchrow) { if ($row[2]) { $emails{$row[2]}++; } }
  ($joinkey) = $joinkey =~ m/(\d+)/; 
  my $id = 'WBPerson' . $joinkey;
  if ($id) { $to_print .= "id: $id<br />\n"; }
  if ($standard_name) { $to_print .= "name: $standard_name<br />\n"; }
  foreach my $email (sort keys %emails ) {
    $to_print .= "email: <a href=\"javascript:void(0)\" onClick=\"window.open('mailto:$email')\">$email</a><br />\n"; }
  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = '$id' ;" ); $result->execute(); 
  while (my @row = $result->fetchrow) { if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) { 	# all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBPersonTermInfo

sub getAnyWBPictureTermInfo {
  my ($userValue) = @_; my %joinkeys;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
    else { $value = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM pic_name WHERE pic_name = '$value' ORDER BY pic_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( pic_source pic_paper );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $value<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) { 
    if ($table eq 'pic_paper') { 
        my @papers = split/","/, $entry; foreach my $pap (@papers) { 
          my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
      else { $to_print .= "${table}: $entry<br />\n"; } } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBPictureTermInfo

sub getAnyWBProcessTermInfo {
  my ($userValue) = @_; my %joinkeys;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
    else { $value = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM prt_processid WHERE prt_processid = '$value' ORDER BY prt_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( prt_processname prt_othername prt_summary prt_paper );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $value<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) { 
    if ($table eq 'prt_paper') { 
        my @papers = split/","/, $entry; foreach my $pap (@papers) { 
          my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
      else { $to_print .= "${table}: $entry<br />\n"; } } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBProcessTermInfo

sub getAnyWBRnaiTermInfo {
  my ($userValue) = @_; my %joinkeys;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
    else { $value = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM rna_name WHERE rna_name = '$value' ORDER BY rna_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; my @tables = qw( rna_paper rna_curator rna_nodump );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "id: $value<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) { 
    if ($table eq 'rna_curator') {
        my ($cur_id) = $entry =~ m/(\d+)/; 
        my $result2 = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = 'two$cur_id' ;" ); $result2->execute(); my @row2 = $result2->fetchrow(); $to_print .= "Curator : $row2[2]\n"; }
      elsif ($table eq 'rna_paper') { 
        my @papers = split/","/, $entry; foreach my $pap (@papers) { 
          my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
      else { $to_print .= "${table}: $entry<br />\n"; } } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBRnaiTermInfo

sub getAnyWBSeqFeatTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_; my %joinkeys;
  my ($typed_term, $value) = ('bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($typed_term, $value) = $userValue =~ m/^(.*?) \( (.*?) \) $/; }
    else { $value = $userValue; }
  my $result = $dbh->prepare( "SELECT * FROM sqf_name WHERE sqf_name = '$value' ORDER BY sqf_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $joinkeys{$row[0]}++; }
  my $joinkeys = join("','", keys %joinkeys);
  my %info; tie %info, "Tie::IxHash";
  my @tables = qw( publicname othername description dnatext species paper wbgene boundbyproduct trascriptionfactor method analysis );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM sqf_$table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my @int_tables = qw( int_featurebait int_featuretarget );
  foreach my $table (@int_tables) {
    $result = $dbh->prepare( "SELECT int_name FROM int_name WHERE joinkey IN (SELECT joinkey FROM $table WHERE $table ~ '$value');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[0]) { $info{$table}{$row[0]}++; } } }
  my @grg_tables = qw( grg_cisregulatorfeature );
  foreach my $table (@grg_tables) {
    $result = $dbh->prepare( "SELECT grg_intid FROM grg_intid WHERE joinkey IN (SELECT joinkey FROM $table WHERE $table ~ '$value');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[0]) { $info{$table}{$row[0]}++; } } }
  my @exp_tables = qw( exp_seqfeature );
  foreach my $table (@exp_tables) {
    $result = $dbh->prepare( "SELECT exp_name FROM exp_name WHERE joinkey IN (SELECT joinkey FROM $table WHERE $table ~ '$value');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[0]) { $info{$table}{$row[0]}++; } } }
  my $to_print = "name: $value<br />\n";
  foreach my $table (keys %info) {
    foreach my $entry (sort keys %{ $info{$table} }) { 
      $to_print .= "${table}: $entry<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBSeqFeatTermInfo

sub getAnyWBSequenceTermInfo {
  my ($userValue) = @_; my %genes;
  my $result = $dbh->prepare( "SELECT * FROM gin_sequence WHERE gin_sequence = '$userValue' ORDER BY gin_timestamp DESC;" );
  $result->execute(); while ( my @row = $result->fetchrow() ) { $genes{"WBGene$row[0]"}++; }
  my $to_print = "id: $userValue<br />\nname: $userValue<br />\n";
  foreach my $gene (sort keys %genes) { $to_print .= "gene: $gene<br />\n"; }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBSequenceTermInfo

### END TERM INFO ### 


### ID TO VALUE ###

sub getAnySpecificIdToValue {			# convert values from postgres values (ids) to what someone types for dataTable display
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {            $matches = $userValue; }	# antibody name is the ID
  elsif ($ontology_type eq 'Concurhst') {        $matches = $userValue; }	# concise description curator history name is the ID
  elsif ($ontology_type eq 'Discurhst') {        $matches = $userValue; }	# disease curator history name is the ID
  elsif ($ontology_type eq 'Ditcurhst') {        $matches = $userValue; }	# disease term curator history name is the ID
  elsif ($ontology_type eq 'Expr') {             $matches = $userValue; }	# expr name is the ID
  elsif ($ontology_type eq 'Molecule') {         $matches = $userValue; }	# molecule wbid is the ID
#   elsif ($ontology_type eq 'Molecule') {        ($matches, $fieldIdToValue_ref) = &getAnyMoleculeIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'Transgene') {       ($matches, $fieldIdToValue_ref) = &getAnyTransgeneIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
#   elsif ($ontology_type eq 'WBConstruct') {      $matches = $userValue; }	# construct is the ID
  elsif ($ontology_type eq 'WBConstruct') {     ($matches, $fieldIdToValue_ref) = &getAnyWBConstructIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBGene') {          ($matches, $fieldIdToValue_ref) = &getAnyWBGeneIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBInteraction') {    $matches = $userValue; }	# interaction name is the ID
  elsif ($ontology_type eq 'WBPaper') {          $matches = $userValue; }	# paper name is the ID
  elsif ($ontology_type eq 'WBPerson') {        ($matches, $fieldIdToValue_ref) = &getAnyWBPersonIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches, $fieldIdToValue_ref) = &getAnyWBPictureIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBProcess') {       ($matches, $fieldIdToValue_ref) = &getAnyWBProcessIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBRnai') {           $matches = $userValue; }	# rnai name is the ID
  elsif ($ontology_type eq 'WBSeqFeat') {        $matches = $userValue; }	# sequence feature name is the ID
  elsif ($ontology_type eq 'WBSequence') {       $matches = $userValue; }	# sequence name is the ID
  return ($matches, $fieldIdToValue_ref);
} # sub getAnySpecificIdToValue

# molecules are now stored as wbmolIDs instead of the previous pgids.
# sub getAnyMoleculeIdToValue {			# molecule object names (not publicname)
#   my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
#   my %fieldIdToValue = %$fieldIdToValue_ref;
#   $userValue =~ s/\"//g;			# strip doublequotes
#   my (@data) = split/,/, $userValue; my %results;
#   foreach my $id (@data) {
#     my $joinkey = $id;
#     if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
#     else {
#       my $table =  'mop_molecule';
#       my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$joinkey' ;" );
#       $result->execute(); my @row = $result->fetchrow();
#       if ($row[1]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[1]<span style='display: none'>$id</span>\""; 
#                      $results{$joinkey} = "\"$row[1]<span style='display: none'>$id</span>\""; } } }
#   my $data = join",", sort values %results;
#   if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
#   return ($data, \%fieldIdToValue);
# } # sub getAnyMoleculeIdToValue

sub getAnyTransgeneIdToValue {			# molecule object names (not publicname)
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $name (@data) {
    my $joinkey = $name;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $table = 'trp_name';
      my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$name' ;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; 
                     $results{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; } } }
  my $data = join",", sort values %results;
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyTransgeneIdToValue
sub getAnyWBConstructIdToValue {			# process object names (not publicname)
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $name (@data) {
    my $joinkey = $name;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $result = $dbh->prepare( "SELECT * FROM cns_publicname WHERE joinkey IN (SELECT joinkey FROM cns_name WHERE cns_name = '$name') ;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; 
                     $results{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; }
        else {       $fieldIdToValue{$ontology_type}{$joinkey} = "\"$name<span style='display: none'>$name</span>\"";
                     $results{$joinkey} = "\"$name<span style='display: none'>$name</span>\""; } } }
  my $data = join",", sort values %results;	# this always joins even if there's only one value for ontology
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyWBConstructIdToValue
sub getAnyWBGeneIdToValue {			# names of loci by wbgene id
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_; $userValue =~ s/WBGene//g; $userValue =~ s/\"//g;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $id (@data) {
    my $joinkey = $id;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $value = '';
      my $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$id';" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { $value = $row[1]; }
        else { 
          $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey = '$id';" );	# allow value to show a sequence if no locus 2010 08 09
          $result->execute(); my @row = $result->fetchrow();
          if ($row[1]) { $value = $row[1]; }
            else { 
              $result = $dbh->prepare( "SELECT * FROM gin_wbgene WHERE joinkey = '$id';" );	# allow value to show a wbgene if exists/existed 2011 03 25
              $result->execute(); my @row = $result->fetchrow();
              if ($row[1]) { $value = $row[1]; } } }
      if ($value) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$value<span style='display: none'>WBGene$id</span>\""; 
                    $results{$joinkey} = "\"$value<span style='display: none'>WBGene$id</span>\""; } } }
  my $data = join",", sort values %results;
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyWBGeneIdToValue
sub getAnyWBPersonIdToValue {			# names of people by wbperson id
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $id (@data) {
    my $joinkey = $id; $joinkey =~ s/WBPerson/two/g;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $table =  'two_standardname';
      my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$joinkey' ORDER BY two_order;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[2]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[2]<span style='display: none'>$id</span>\""; 
                     $results{$joinkey} = "\"$row[2]<span style='display: none'>$id</span>\""; } } }
  my $data = join",", sort values %results;
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyWBPersonIdToValue
sub getAnyWBPictureIdToValue {			# picture object names (not publicname)
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $name (@data) {
    my $joinkey = $name;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $result = $dbh->prepare( "SELECT * FROM pic_source WHERE joinkey IN (SELECT joinkey FROM pic_name WHERE pic_name = '$name') ;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; 
                     $results{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; } } }
  my $data = join",", sort values %results;	# this always joins even if there's only one value for ontology
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyWBPictureIdToValue
sub getAnyWBProcessIdToValue {			# process object names (not publicname)
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $name (@data) {
    my $joinkey = $name;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $result = $dbh->prepare( "SELECT * FROM prt_processname WHERE joinkey IN (SELECT joinkey FROM prt_processid WHERE prt_processid = '$name') ;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; 
                     $results{$joinkey} = "\"$row[1]<span style='display: none'>$name</span>\""; } } }
  my $data = join",", sort values %results;	# this always joins even if there's only one value for ontology
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyWBProcessIdToValue

### END ID TO VALUE ###

### END ONTOLOGY / MULTIONTOLOGY ###


### LOGIN ###

sub loginMod { 
  my ($flag, $ip, $curator_two) = @_;			# get the flag, $ip, and optional $curator_two
  &loginWorm($flag, $ip, $curator_two); }

sub loginWorm {						# switch for different login subroutines
  my ($flag, $ip, $curator_two) = @_;			# get the flag, $ip, and optional $curator_two
  if ($flag eq 'showModLogin') { &showWormLogin($ip); }
  elsif ($flag eq 'updateModCurator') { &updateWormCurator($ip, $curator_two); }
} # sub loginWorm

sub showWormLogin {					# show login curators, datatypes, and Login button
  my ($ip) = @_;
  my $curator_by_ip = '';
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip';" ); $result->execute; my @row = $result->fetchrow;
  if ($row[0]) { $curator_by_ip = $row[0]; }
  my %curator_list; tie %curator_list, "Tie::IxHash";
#   $curator_list{"two22"}    = 'Igor Antoshechkin';
  $curator_list{"two1823"}  = 'Juancarlos Chan';
  $curator_list{"two101"}   = 'Wen Chen';
  $curator_list{"two1983"}  = 'Paul Davis';
  $curator_list{"two133"}   = 'John DeModena';
  $curator_list{"two17622"} = 'James Done';
#   $curator_list{"two9133"}  = 'Margaret Duesbury';	# Mary Ann said to remove her.  2012 03 26
#   $curator_list{"two8679"}  = 'Ruihua Fang';
  $curator_list{"two2021"}  = 'Jolene S. Fernandes';
#   $curator_list{"two13088"} = 'Uhma Ganesan';
  $curator_list{"two2987"}  = 'Chris';
  $curator_list{"two12884"} = 'Snehalata Kadam';
  $curator_list{"two324"}   = 'Ranjana Kishore';
  $curator_list{"two363"}   = 'Raymond Lee';
  $curator_list{"two1"}     = 'Cecilia Nakamura';
  $curator_list{"two480"}   = 'Tuco';
  $curator_list{"two12028"} = 'Daniela Raciti';
  $curator_list{"two1847"}  = 'Anthony Rogers';
  $curator_list{"two557"}   = 'Gary C. Schindelman';
  $curator_list{"two567"}   = 'Erich Schwarz';
  $curator_list{"two625"}   = 'Paul Sternberg';
#   $curator_list{"two627"}   = 'Theresa Stiernagle';
  $curator_list{"two2970"}  = 'Mary Ann Tuli';
  $curator_list{"two1843"}  = 'Kimberly Van Auken';
  $curator_list{"two736"}   = 'Qinghua Wang';
  $curator_list{"two1760"}  = 'Xiaodong Wang';
  $curator_list{"two712"}   = 'Karen Yook'; 

  print "<table cellpadding=\"4\">\n";
  print "<tr>\n";
  print "<td valign=\"top\">Name<br /><select name=\"curator_two\" size=" , scalar keys %curator_list , ">\n";
  foreach my $curator_two (keys %curator_list) {	# display curators in alphabetical (tied hash) order, if IP matches existing ip record, select it
    if ($curator_by_ip eq $curator_two) { print "<option value=\"$curator_two\" selected=\"selected\">$curator_list{$curator_two}</option>\n"; }
    else { print "<option value=\"$curator_two\">$curator_list{$curator_two}</option>\n"; } }
  print "</select></td>\n";

  my %datatype_list; tie %datatype_list, "Tie::IxHash";
  $datatype_list{"abp"} = "antibody";
  $datatype_list{"con"} = "concise";
  $datatype_list{"cns"} = "construct";
  $datatype_list{"dis"} = "disease";
  $datatype_list{"dit"} = "disease term";
  $datatype_list{"exp"} = "exprpat";
  $datatype_list{"gcl"} = "gene class";
  $datatype_list{"gop"} = "go";
  $datatype_list{"grg"} = "genereg";
  $datatype_list{"int"} = "interaction";
  $datatype_list{"mop"} = "molecule";
  $datatype_list{"mov"} = "movie";
  $datatype_list{"app"} = "phenotype";
  $datatype_list{"pic"} = "picture";
  $datatype_list{"prt"} = "process term";
  $datatype_list{"rna"} = "rnai";
  $datatype_list{"pro"} = "topic";
  $datatype_list{"sqf"} = "seq feature";
  $datatype_list{"trp"} = "transgene";
  my $datatype_list_size = scalar keys %datatype_list;

  print qq(<td valign="top">Data Type<br /><select name="datatype" size="$datatype_list_size">\n);
  foreach my $threecode (keys %datatype_list) { print qq(<option value="$threecode">$datatype_list{$threecode}</option>\n); }
  print qq(</select></td>\n);
  print "<td valign=\"top\"><br /><input type=submit name=action value=\"Login !\"></td>\n";
  print "</tr>\n";
  print "</table>\n";
} # sub showWormLogin

sub updateWormCurator {					# update two_curator_ip for this curator and ip
  my ($ip, $curator_two) = @_;
  my $result = $dbh->prepare( "SELECT * FROM two_curator_ip WHERE two_curator_ip = '$ip' AND joinkey = '$curator_two';" );
  $result->execute;
  my @row = $result->fetchrow;
  unless ($row[0]) {
    $result = $dbh->do( "DELETE FROM two_curator_ip WHERE two_curator_ip = '$ip' ;" );
    $result = $dbh->do( "INSERT INTO two_curator_ip VALUES ('$curator_two', '$ip')" );
} } # sub updateWormCurator

### END LOGIN ###



__END__


=head1 NAME

wormOA - Config file for worm OA configurations for WormBase MOD.


=head1 SYNOPSIS

In ontology_annotator.cgi :

=over 4

=item * add "use wormOA;" 

=item * add "my $configLoaded = 'wormOA';" 

=back

In this oa perl module file :

=over 4

=item * if creating a copy of this perl module change the name in the first line 'package wormOA;'.

=item * customize  &initModFields  &showModLogin  &setAnySimpleAutocompleteValues  &getAnySpecificAutocomplete  &getAnySpecificValidValue  &getAnySpecificTermInfo  &getAnySpecificIdToValue 

=back


=head1 DESCRIPTION

ontology_annotator.cgi has the generic code for any kind of configuration.  Some subroutines need data that is specific to a given datatype / configuration, and modules like this one can be custom-written to appropriately get and display this data.  There are seven groups of subroutines that need to be written :

=over 4

=item * &login<Mod>  switch to call appropriate login-related subroutine

=item * &init<Mod>Fields  initializes the appropriate %fields and %datatypes for the MOD's chosen datatype and curator.

=item * setAnySimpleAutocompleteValues  set values of dropdown or multidropdown for a given ontology_type.

=item * getAnySpecificAutocomplete  for something that a curator types into an ontology or multiontology field, get autocomplete values that correspond to it.

=item * getAnySpecificValidValue  for a value that a curator selects in an ontology or multiontology field, check if it's valid and return 'true' or 'false'.

=item * getAnySpecificTermInfo  for a value that a curator looks at in an ontology or multiontology field, get the corresponding term information for the OA's obo frame.

=item * getAnySpecificIdToValue  for some stored IDs in an ontology or multiontology field's corresponding postgres table, get the corresponding objects's names (and IDs) to display on the dataTable, as well as update %fieldIdToValue .

=back

When creating a new MOD, must create  &login<Mod>  and optional curator_ip table.

When creating a new datatype, must create  &init<Mod>Fields  and corresponding postgres tables.

When creating a new dropdown / multidropdown, must set values in  &setAnySimpleAutocompleteValues .

When creating a new ontology / multiontology, must set  &getAnySpecificAutocomplete  &getAnySpecificValidValue  &getAnySpecificTermInfo  &getAnySpecificIdToValue  and create appropriate corresponding subroutine for each.


=head2 LOGIN WORM

&loginWorm  is the main subroutine called from the ontology_annotator.cgi and calls the appropriate login-related subroutine.  The worm config stores the last IP used by any given curator, this is not necessary for other MODs.

&loginMod  is called by ontology_annotator.cgi  passing in a flag for which subroutine to call, an IP address, and optional curator_two.  It is a generalized function to call  &loginWorm  with the same parameters.

&loginWorm  is called by  &loginMod  passing in a flag for which subroutine to call, an IP address, and optional curator_two.  It calls  &showWormLogin  or  &updateWormCurator .

&showWormLogin  is called from ontology_annotator.cgi's  &showLogin  passing in the IP of the user.  Displays a selection of curators and datatypes for that MOD, and a Login button 'Login !'.  A postgres table of curator IPs finds the last curator to use that IP and automatically select it ;  this is optional and only necessary is tracking curators by IP.  

&updateWormCurator  is called from ontology_annotator.cgi's  &showMain  passing in the IP of the user and the curator_two to update.  Update the postgres table two_curator_ip for this curator_two and IP.  Optional subroutine, unnecessary if not tracking curators by IP.

=head2 INITIALIZE WORM FIELDS

&initWormFields  is the main subroutine called from the ontology_annotator.cgi and calls the appropriate datatype-appropriate initialization subroutine to set field and datatype values.

&initModFields  is called by ontology_annotator.cgi  passing in $datatype and $curator_two and returning values of $fieldsRef and $datatypesRef .  It is a generalized function to call  &initWormFields  with the same parameters.

&initWormFields  is called by  &initModFields  passing in $datatype and $curator_two and returning values of $fieldsRef and $datatypesRef .  A new datatype configuration calls  &initWorm<datatype>Fields  passing $datatype and $curator_two and returning values of $fieldsRef and $datatypesRef .  

&initWorm<datatype>Fields  exist for each specific datatype configuration.  It defines the %fields and %datatypes and returns them to the ontology_annotator.cgi .  

%datatypes  stores options for each datatype configuration as a whole, in the format  $datatypes{<datatype>}{<option>} .  It can have these options :

=over 4

=item * highestPgidTables	REQUIRED	array of tables for this config that should have a value to determine the highest used pgid.  Also when doing a &jsonFieldQuery if querying by id use these tables instead.

=item * label	REQUIRED	label to show in Editor frame which configuration has been selected.

=item * newRowSub	REQUIRED	pointer to the config-specific sub to create a new row.  Most only insert to postgres table of _curator field, others also to other tables.

=item * constraintSub	OPTIONAL	pointer to the config-specific sub for checks when checking data.  Called by ontology_annotator.cgi by  &checkDataByPgids .  Returns 'OK' or messages with specific problems for specific pgids.

=item * constraintTablesHaveData	OPTIONAL	array of tables for this config.  When checking data, these tables must have data.  Called by ontology_annotator.cgi by  &checkDataByPgids .

=back

%fields  stores options for the datatype configuration's individual fields, in the format  $fields{<datatype>}{<field_name>}{<option>} .  It must have a field called 'id' used to store the dataTable's pgid / postgresTables's joinkey.  It must also have a field called 'curator'.  It can have these options :

=over 4

=item * type	REQUIRED	the type of field.  Possible values are : text bigtext dropdown multidropdown ontology multiontology toggle toggle_text queryonly

=item * label	REQUIRED	text that shows on the OA editor and dataTable columns.  Editor td has id label_$field.  Should never have the same label for different fields because .js columnReorderEvent uses label value to set order.

=item * tab	REQUIRED	which editor's tab displays the field.  Value can be 'all' or 'tab1', 'tab2', &c.

=item * dropdown_type	DEPENDENT	required for fields of type dropdown or multidropdown.  To specify which values to show for a given dropdown / multidropdown field.  Used by ontology_annotator.cgi for  &getAnySimpleValidValue  &setAnySimpleAutocomplete  &getAnySimpleAutocomplete   IdToValue conversion.

=item * ontology_type	DEPENDENT	required for fields of type ontology or multiontology.  For ontology subroutines to know what type of data to use for an ontology / multiontology.  Can be generic (value 'obo') and use 'obo_' tables, or can be specific and have custom subroutines (e.g. WBGene, WBPerson, WBPaper, Transgene, &c.).  A given ontology_type can be used in different datatypes and/or multiple times in the same datatype.

=item * ontology_table	DEPENDENT	required for fields of type ontology or multiontology that also have ontology_type value 'obo', this determines the specific obo_ table to get values from.

=item * inline	DEPENDENT	required for fields that have multiple fields in the same row.  Can hold the value of the corresponding field that follows, or begin with 'INSIDE_'.  When doing &showEditor, values with 'INSIDE_' get skipped ;  values that are 'toggle_text' show the toggle field and then the corresponding text field.

=item * queryonlySub  DEPENDENT		required for fields of type queryonly.  Pointer to the datatype-field-specific sub to create a custom postgres query for queryonly fields that returns joinkeys.

=item * noteditable	OPTIONAL	flag.  Field can't be edited (affects ontology_annotator.js only).  Values in bigtext field will toggle into the input field, so the editor will change, but values will not update in the datatable, nor change in postgres.  A bit obsolete with 'disabled' option, but useful if need to copy-paste.

=item * disabled   	OPTIONAL	flag.  Field can't be edited (prevents editing html with disabled flag).

=item * input_size	OPTIONAL	integer.  Html input tag has this size on editor.

=item * cols_size	OPTIONAL	integer.  Html textarea tag has this cols size on editor.

=item * rows_size	OPTIONAL	integer.  Html textarea tag has this rows size on editor.

=item * placeholder	OPTIONAL	fake field to set the order in the tied hash.  Fields on editor show in order they were entered in the tied %fields hash, this only serves to set the order.

=item * columnWidth	OPTIONAL	integer.  Value to hard-set the width in pixels of the value's dataTable column.

=item * columnOrder	OPTIONAL	integer.  Value to hard-set the array order of the columns in the dataTable.  Never set multiple fields to the same columnOrder or one will not show.

=back

=head2 SET ANY SIMPLE AUTOCOMPLETE VALUES

&setAnySimpleAutocompleteValues  is the only subroutine called from the ontology_annotator.cgi and sets the dropdown values for the appropriate datatype.  Necessary when creating a new dropdown or multidropdown ontology type.

&setAnySimpleAutocompleteValues  is called by ontology_annotator.cgi  passing in the ontology_type and returning a pointer to %data.  Creates a tied %data hash which has all dropdown values in order entered for the given ontology_type.

%data  stores dropdown values for a given ontology_type, in the format  ''$data{<ontology_type>}{name}{<name>} = <value_to_display>''.  value_to_display  can have two formats : ''<name_of_value> ( <id_of_value> ) '' or ''<value>'' depending on whether the ontology_type stores IDs or not, respectively.

=head2 GET ANY SPECIFIC AUTOCOMPLETE

&getAnySpecificAutocomplete  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to get the matching Autocomplete values for that ontology_type.  Used when a curator types full or partial terms into an ontology / multiontology field.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificAutocomplete  is called by ontology_annotator.cgi  passing in the ontology_type and words to autocomplete on, and returning the corresponding matches.  Calls  &getAny<ontology_type>Autocomplete  passing in words to autocomplete on, and returning the corresponding matches.

&getAny<ontology_type>Autocomplete  exists for each specific ontology_type.  It queries the appropriate postgres tables to find corresponding values.  Most of these subroutines return 20 ontology values, but if there are 5 or more characters to search the results expands to 500.  Most also search for a case-insensitive match beginning with the search terms, then if there aren't yet max_results it appends results from a case-insensitive match of the search terms where the terms do not match at the beginning.  If there are more than max_results values, the last results is replaced with 'more ...'.  Results are joined by a newline and returned.  Most tables searched are the appropriate name table for the ontology_type, but it could also be an ID field or synonym field or anything else.  The format of each autocomplete value can be  ''<value>'' if it can only match on a value, or ''<name_of_value> ( <id_of_value> ) '' if it can match on a name or an ID, or ''<name_of_match> ( <id_of_value> ) [name_of_id]'' if it can match on a synonym, ID, or name of term.

=head2 GET ANY SPECIFIC VALID VALUE

&getAnySpecificValidValue  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to check that a value is valid for that ontology_type.  Used when a curator selects a value in an ontology or multiontology field.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificValidValue  is called by ontology_annotator.cgi  passing in the ontology_type and userValue to check validity on, and returning 'true' or 'false' as appropriate.  Calls  &getAny<ontology_type>ValidValue  passing in the userValue and returning 'true' or 'false'.

&getAny<ontology_type>ValidValue  exists for each specific ontology_type.  It queries the appropriate postgres tables to check if the userValue is a valid value for the ontology_type.  If it is valid, returns 'true', otherwise returns 'false'.

=head2 GET ANY SPECIFIC TERM INFO

&getAnySpecificTermInfo  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to get the term information for the given ontology value, to display in the OA's obo frame.  Used when a curator clicks, mouses over, or arrows to a value from an ontology / multiontology field.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificTermInfo  is called by ontology_annotator.cgi  passing in the ontology_type and userValue to get term info of, and returning a variable containing the term information to display in the OA's obo frame.  Calls  &getAny<ontology_type>TermInfo  passing in the userValue, and returning the term information to display.

&getAny<ontology_type>TermInfo  exists for each specific ontology_type.  It queries the appropriate postgres tables (or flatfiles) to get the term information to display.  Most information has a tag name and colon in a bold html span, followed by the information.  As appropriate there might be html hr dividers.  Any type of html links or embedded images or practically any html could be displayed here.

=head2 GET ANY SPECIFIC ID TO VALUE

&getAnySpecificIdToValue  is the main subroutine called from the ontology_annotator.cgi and calls the ontology_type-appropriate subroutine to add to the %fieldIdToValue hash, which converts ID into  ''name<span style='display: none'>id</span>''.  Used when displaying dataTable data from a postgres query of &jsonFieldQuery in the main CGI.  Necessary when creating a new ontology or multiontology type.

&getAnySpecificIdToValue  is called by ontology_annotator.cgi  passing in the ontology_type, %fields's type, pointer to existing %fieldIdToValue, and IDs from postgres table data from which to get the id to value mappings ;  and returning a variable containing the display values of each of the ontology_type's passed IDs, and a pointer to the updated %fieldIdToValue .  Calls &getAny<ontology_type>IdToValue, passing in the ontology_type, %fields's type, pointer to %fieldIdToValue hash, IDs from postgres table data ;  and returning a variable with the display values of the corresponding IDs, and a pointer to the updated %fieldIdToValue .

&getAny<ontology_type>IdToValue  exists for each specific ontology_type.  It splits the postgres data table's values into separate IDs, and for each ID, it checks against the %fieldIdToValue hash.  If it already exists, it adds it to the %results hash.  If it doesn't, it queries against the appropriate postgres tables and generates a new value to display, adding it to %results and to $fieldIdToValue{$ontology_type}.  %results values are joined by commas into a $data variable to return.  If the %fields's type is ontology, the leading and trailing doublequotes are stripped (doublequotes are necessary for multiontology).  $data and a pointer to the updated %fieldIdToValue are returned.  The format of %results is  ''$results{<joinkey>} = "<display_value><span style='display: none'><id></span>"''  where <span> tags are html tags, and <display_value> and <id> are real values.



