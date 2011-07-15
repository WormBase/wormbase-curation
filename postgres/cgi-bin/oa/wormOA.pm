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
  elsif ($datatype eq 'exp') { ($fieldsRef, $datatypesRef) = &initWormExpFields($datatype, $curator_two); }
  elsif ($datatype eq 'gcl') { ($fieldsRef, $datatypesRef) = &initWormGclFields($datatype, $curator_two); }
  elsif ($datatype eq 'gop') { ($fieldsRef, $datatypesRef) = &initWormGopFields($datatype, $curator_two); }
  elsif ($datatype eq 'grg') { ($fieldsRef, $datatypesRef) = &initWormGrgFields($datatype, $curator_two); }
  elsif ($datatype eq 'int') { ($fieldsRef, $datatypesRef) = &initWormIntFields($datatype, $curator_two); }
  elsif ($datatype eq 'mop') { ($fieldsRef, $datatypesRef) = &initWormMopFields($datatype, $curator_two); }
  elsif ($datatype eq 'pic') { ($fieldsRef, $datatypesRef) = &initWormPicFields($datatype, $curator_two); }
  elsif ($datatype eq 'ptg') { ($fieldsRef, $datatypesRef) = &initWormPtgFields($datatype, $curator_two); }
  elsif ($datatype eq 'trp') { ($fieldsRef, $datatypesRef) = &initWormTrpFields($datatype, $curator_two); }
  return( $fieldsRef, $datatypesRef);
} # sub initWormFields

sub initWormAbpFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{abp} }, "Tie::IxHash";
  $fields{abp}{id}{type}                             = 'text';
  $fields{abp}{id}{label}                            = 'pgid';
  $fields{abp}{id}{tab}                              = 'all';
  $fields{abp}{name}{type}                           = 'text';
  $fields{abp}{name}{label}                          = 'Name';
  $fields{abp}{name}{tab}                            = 'all';
  $fields{abp}{gene}{type}                           = 'multiontology';
  $fields{abp}{gene}{label}                          = 'Gene';
  $fields{abp}{gene}{tab}                            = 'all';
  $fields{abp}{gene}{ontology_type}                  = 'WBGene';
  $fields{abp}{clonality}{type}                      = 'dropdown';
  $fields{abp}{clonality}{label}                     = 'Clonality';
  $fields{abp}{clonality}{tab}                       = 'all';
  $fields{abp}{clonality}{dropdown_type}             = 'clonality';
  $fields{abp}{animal}{type}                         = 'dropdown';
  $fields{abp}{animal}{label}                        = 'Animal';
  $fields{abp}{animal}{tab}                          = 'all';
  $fields{abp}{animal}{dropdown_type}                = 'animal';
  $fields{abp}{antigen}{type}                        = 'dropdown';
  $fields{abp}{antigen}{label}                       = 'Antigen';
  $fields{abp}{antigen}{tab}                         = 'all';
  $fields{abp}{antigen}{dropdown_type}               = 'antigen';
  $fields{abp}{peptide}{type}                        = 'bigtext';
  $fields{abp}{peptide}{label}                       = 'Peptide';
  $fields{abp}{peptide}{tab}                         = 'all';
  $fields{abp}{protein}{type}                        = 'bigtext';
  $fields{abp}{protein}{label}                       = 'Protein';
  $fields{abp}{protein}{tab}                         = 'all';
  $fields{abp}{source}{type}                         = 'dropdown';
  $fields{abp}{source}{label}                        = 'Source';
  $fields{abp}{source}{tab}                          = 'all';
  $fields{abp}{source}{dropdown_type}                = 'abpsource';
  $fields{abp}{original_publication}{type}           = 'ontology';
  $fields{abp}{original_publication}{label}          = 'Original Publication';
  $fields{abp}{original_publication}{tab}            = 'all';
  $fields{abp}{original_publication}{ontology_type}  = 'WBPaper';
  $fields{abp}{paper}{type}                          = 'multiontology';
  $fields{abp}{paper}{label}                         = 'Reference';
  $fields{abp}{paper}{tab}                           = 'all';
  $fields{abp}{paper}{ontology_type}                 = 'WBPaper';
  $fields{abp}{remark}{type}                         = 'bigtext';
  $fields{abp}{remark}{label}                        = 'Remark';
  $fields{abp}{remark}{tab}                          = 'all';
  $fields{abp}{other_name}{type}                     = 'bigtext';
  $fields{abp}{other_name}{label}                    = 'Other Name';
  $fields{abp}{other_name}{tab}                      = 'all';
  $fields{abp}{laboratory}{type}                     = 'multiontology';
  $fields{abp}{laboratory}{label}                    = 'Laboratory';
  $fields{abp}{laboratory}{tab}                      = 'all';
  $fields{abp}{laboratory}{ontology_type}            = 'obo';
  $fields{abp}{laboratory}{ontology_table}           = 'laboratory';
  $fields{abp}{other_animal}{type}                   = 'bigtext';
  $fields{abp}{other_animal}{label}                  = 'Other Animal';
  $fields{abp}{other_animal}{tab}                    = 'all';
  $fields{abp}{other_antigen}{type}                  = 'bigtext';
  $fields{abp}{other_antigen}{label}                 = 'Other Antigen';
  $fields{abp}{other_antigen}{tab}                   = 'all';
  $fields{abp}{possible_pseudonym}{type}             = 'bigtext';
  $fields{abp}{possible_pseudonym}{label}            = 'Possible Pseudonym';
  $fields{abp}{possible_pseudonym}{tab}              = 'all';
  $fields{abp}{summary}{type}                        = 'bigtext';
  $fields{abp}{summary}{label}                       = 'Summary';
  $fields{abp}{summary}{tab}                         = 'all';
  $fields{abp}{curator}{type}                        = 'dropdown';
  $fields{abp}{curator}{label}                       = 'Curator';
  $fields{abp}{curator}{tab}                         = 'all';
  $fields{abp}{curator}{dropdown_type}               = 'curator';
  $datatypes{abp}{newRowSub}                         = \&newRowAbp;
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
  $fields{app}{curation_status}{type}                = 'dropdown';
  $fields{app}{curation_status}{label}               = 'Curation Status';
  $fields{app}{curation_status}{tab}                 = 'tab1';
  $fields{app}{curation_status}{dropdown_type}       = 'curationstatus';
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
  $fields{app}{caused_by}{label}                     = 'Caused By';
  $fields{app}{caused_by}{tab}                       = 'tab1';
  $fields{app}{caused_by}{ontology_type}             = 'WBGene';
  $fields{app}{caused_by_other}{type}                = 'text';
  $fields{app}{caused_by_other}{label}               = 'Caused By Other';
  $fields{app}{caused_by_other}{tab}                 = 'tab1';
  $fields{app}{not}{type}                            = 'toggle';
  $fields{app}{not}{label}                           = 'NOT';
  $fields{app}{not}{tab}                             = 'tab2';
  $fields{app}{term}{type}                           = 'ontology';
  $fields{app}{term}{label}                          = 'Phenotype';
  $fields{app}{term}{tab}                            = 'tab2';
  $fields{app}{term}{ontology_type}                  = 'obo';
  $fields{app}{term}{ontology_table}                 = 'phenotype';
  $fields{app}{phen_remark}{type}                    = 'bigtext';
  $fields{app}{phen_remark}{label}                   = 'Phenotype Remark';
  $fields{app}{phen_remark}{tab}                     = 'tab2';
  $fields{app}{phen_remark}{columnWidth}             = '600';
  $fields{app}{molecule}{type}                       = 'multiontology';
  $fields{app}{molecule}{label}                      = 'Molecule';
  $fields{app}{molecule}{tab}                        = 'tab2';
  $fields{app}{molecule}{ontology_type}              = 'Molecule';
  $fields{app}{anat_term}{type}                      = 'multiontology';
  $fields{app}{anat_term}{label}                     = 'Anatomy';
  $fields{app}{anat_term}{tab}                       = 'tab2';
  $fields{app}{anat_term}{ontology_type}             = 'obo';
  $fields{app}{anat_term}{ontology_table}            = 'anatomy';
  $fields{app}{lifestage}{type}                      = 'multiontology';
  $fields{app}{lifestage}{label}                     = 'Life Stage';
  $fields{app}{lifestage}{tab}                       = 'tab2';
  $fields{app}{lifestage}{ontology_type}             = 'obo';
  $fields{app}{lifestage}{ontology_table}            = 'lifestage';
  $fields{app}{suggested}{type}                      = 'text';
  $fields{app}{suggested}{label}                     = 'Suggested';
  $fields{app}{suggested}{tab}                       = 'tab4';
  $fields{app}{suggested_definition}{type}           = 'bigtext';
  $fields{app}{suggested_definition}{label}          = 'Suggested Definition';
  $fields{app}{suggested_definition}{tab}            = 'tab4';
  $fields{app}{child_of}{type}                       = 'multiontology';
  $fields{app}{child_of}{label}                      = 'Child Of';
  $fields{app}{child_of}{tab}                        = 'tab4';
  $fields{app}{child_of}{ontology_type}              = 'obo';
  $fields{app}{child_of}{ontology_table}             = 'phenotype';
  $fields{app}{nature}{type}                         = 'dropdown';
  $fields{app}{nature}{label}                        = 'Allele Nature';
  $fields{app}{nature}{tab}                          = 'tab3';
  $fields{app}{nature}{dropdown_type}                = 'nature';
  $fields{app}{func}{type}                           = 'dropdown';
  $fields{app}{func}{label}                          = 'Functional Change';
  $fields{app}{func}{tab}                            = 'tab3';
  $fields{app}{func}{dropdown_type}                  = 'func';
  $fields{app}{temperature}{type}                    = 'text';
  $fields{app}{temperature}{label}                   = 'Temperature';
  $fields{app}{temperature}{tab}                     = 'tab3';
  $fields{app}{treatment}{type}                      = 'bigtext';
  $fields{app}{treatment}{label}                     = 'Treatment';
  $fields{app}{treatment}{tab}                       = 'tab3';
  $fields{app}{control_isolate}{type}                = 'text';
  $fields{app}{control_isolate}{label}               = 'Control Isolate';
  $fields{app}{control_isolate}{tab}                 = 'tab3';
  $fields{app}{penetrance}{type}                     = 'dropdown';
  $fields{app}{penetrance}{label}                    = 'Penetrance';
  $fields{app}{penetrance}{tab}                      = 'tab3';
  $fields{app}{penetrance}{dropdown_type}            = 'penetrance';
  $fields{app}{percent}{type}                        = 'bigtext';
  $fields{app}{percent}{label}                       = 'Penetrance Remark';
  $fields{app}{percent}{tab}                         = 'tab3';
  $fields{app}{cold_sens}{type}                      = 'toggle_text';
  $fields{app}{cold_sens}{label}                     = 'Cold Sensitive';
  $fields{app}{cold_sens}{tab}                       = 'tab3';
  $fields{app}{cold_sens}{inline}                    = 'cold_degree';
  $fields{app}{cold_degree}{type}                    = 'text';
  $fields{app}{cold_degree}{label}                   = 'Cold Sensitive Degree';
  $fields{app}{cold_degree}{tab}                     = 'tab3';
  $fields{app}{cold_degree}{inline}                  = 'INSIDE_cold_degree';
  $fields{app}{heat_sens}{type}                      = 'toggle_text';
  $fields{app}{heat_sens}{label}                     = 'Heat Sensitive';
  $fields{app}{heat_sens}{tab}                       = 'tab3';
  $fields{app}{heat_sens}{inline}                    = 'heat_degree';
  $fields{app}{heat_degree}{type}                    = 'text';
  $fields{app}{heat_degree}{label}                   = 'Heat Sensitive Degree';
  $fields{app}{heat_degree}{tab}                     = 'tab3';
  $fields{app}{heat_degree}{inline}                  = 'INSIDE_heat_degree';
  $fields{app}{mat_effect}{type}                     = 'dropdown';
  $fields{app}{mat_effect}{label}                    = 'Maternal Effect';
  $fields{app}{mat_effect}{tab}                      = 'tab3';
  $fields{app}{mat_effect}{dropdown_type}            = 'mateffect';
  $fields{app}{pat_effect}{type}                     = 'toggle';
  $fields{app}{pat_effect}{label}                    = 'Paternal Effect';
  $fields{app}{pat_effect}{tab}                      = 'tab3';
  $fields{app}{haplo}{type}                          = 'toggle';
  $fields{app}{haplo}{label}                         = 'Haploinsufficient';
  $fields{app}{haplo}{tab}                           = 'tab3';
  $fields{app}{genotype}{type}                       = 'bigtext';
  $fields{app}{genotype}{label}                      = 'Genotype';
  $fields{app}{genotype}{tab}                        = 'tab5';
  $fields{app}{genotype}{columnWidth}                = '600';
  $fields{app}{intx_desc}{type}                      = 'bigtext';
  $fields{app}{intx_desc}{label}                     = 'Genetic Intx Desc';
  $fields{app}{intx_desc}{tab}                       = 'tab5';
  $fields{app}{intx_desc}{columnWidth}               = '600';
  $fields{app}{nbp}{type}                            = 'bigtext';
  $fields{app}{nbp}{label}                           = 'NBP';
  $fields{app}{nbp}{tab}                             = 'tab5';
  $fields{app}{nbp}{noteditable}                     = 'noteditable';
  $fields{app}{filereaddate}{type}                   = 'text';
  $fields{app}{filereaddate}{label}                  = 'NBP / File Date';
  $fields{app}{filereaddate}{tab}                    = 'tab5';
  $fields{app}{species}{type}                        = 'dropdown';
  $fields{app}{species}{label}                       = 'Species';
  $fields{app}{species}{tab}                         = 'tab5';
  $fields{app}{species}{dropdown_type}               = 'species';
  $fields{app}{laboratory}{type}                     = 'multiontology';
  $fields{app}{laboratory}{label}                    = 'Laboratory Evidence';
  $fields{app}{laboratory}{tab}                      = 'tab5';
  $fields{app}{laboratory}{ontology_type}            = 'obo';
  $fields{app}{laboratory}{ontology_table}           = 'laboratory';
  $fields{app}{entity}{type}                         = 'ontology';
  $fields{app}{entity}{label}                        = 'Entity';
  $fields{app}{entity}{tab}                          = 'tab5';
  $fields{app}{entity}{ontology_type}                = 'obo';
  $fields{app}{entity}{ontology_table}               = 'entity';
  $fields{app}{quality}{type}                        = 'ontology';
  $fields{app}{quality}{label}                       = 'Quality';
  $fields{app}{quality}{tab}                         = 'tab5';
  $fields{app}{quality}{ontology_type}               = 'obo';
  $fields{app}{quality}{ontology_table}              = 'quality';
  $datatypes{app}{constraintSub}                     = \&checkAppConstraints;
  $datatypes{app}{newRowSub}                         = \&newRowApp;
  @{ $datatypes{app}{highestPgidTables} }            = qw( strain rearrangement transgene variation curator );
  return( \%fields, \%datatypes);
} # sub initWormAppFields

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
  $fields{exp}{goid}{type}                           = 'multiontology';
  $fields{exp}{goid}{label}                          = 'GO Term';
  $fields{exp}{goid}{tab}                            = 'tab1';
  $fields{exp}{goid}{ontology_type}                  = 'obo';
  $fields{exp}{goid}{ontology_table}                 = 'goid';
  $fields{exp}{subcellloc}{type}                     = 'bigtext';
  $fields{exp}{subcellloc}{label}                    = 'Subcellular Localization';
  $fields{exp}{subcellloc}{tab}                      = 'tab1';
  $fields{exp}{lifestage}{type}                      = 'multiontology';
  $fields{exp}{lifestage}{label}                     = 'Life Stage';
  $fields{exp}{lifestage}{tab}                       = 'tab1';
  $fields{exp}{lifestage}{ontology_type}             = 'obo';
  $fields{exp}{lifestage}{ontology_table}            = 'lifestage';
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
  $fields{exp}{transgene}{ontology_type}             = 'Transgene';
  $fields{exp}{transgeneflag}{type}                  = 'toggle';
  $fields{exp}{transgeneflag}{label}                 = 'Transgene_Flag';
  $fields{exp}{transgeneflag}{tab}                   = 'tab2';
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
#   $fields{exp}{author}{type}                         = 'text';
#   $fields{exp}{author}{label}                        = 'Author';
#   $fields{exp}{author}{tab}                          = 'tab3';
#   $fields{exp}{date}{type}                           = 'text';
#   $fields{exp}{date}{label}                          = 'Date';
#   $fields{exp}{date}{tab}                            = 'tab3';
#   $fields{exp}{curatedby}{type}                      = 'text';
#   $fields{exp}{curatedby}{label}                     = 'Curated by';
#   $fields{exp}{curatedby}{tab}                       = 'tab3';
  $datatypes{exp}{newRowSub}                         = \&newRowExp;
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
  $fields{gop}{project}{type}                        = 'multiontology';
  $fields{gop}{project}{label}                       = 'Project';
  $fields{gop}{project}{tab}                         = 'all';
  $fields{gop}{project}{ontology_type}               = 'goproject';
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
  $fields{gop}{qualifier}{type}                      = 'dropdown';
  $fields{gop}{qualifier}{label}                     = 'Qualifier';
  $fields{gop}{qualifier}{tab}                       = 'all';
  $fields{gop}{qualifier}{dropdown_type}             = 'goqualifier';
  $fields{gop}{xrefto}{type}                         = 'text';
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
  $fields{gop}{id}{type}                             = 'text';
  $fields{gop}{id}{label}                            = 'pgid';
  $fields{gop}{id}{tab}                              = 'all';
  if ($curator_two eq 'two1823') { $fields{gop}{id}{input_size} = '70'; }
  @{ $datatypes{gop}{constraintTablesHaveData} }     = qw( paper wbgene curator goid goontology goinference dbtype lastupdate );
  @{ $datatypes{gop}{highestPgidTables} }            = qw( wbgene curator );
  $datatypes{gop}{newRowSub}                         = \&newRowGop;
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
  $fields{grg}{name}{type}                           = 'text';
  $fields{grg}{name}{label}                          = 'Name';
  $fields{grg}{name}{tab}                            = 'tab1';
  $fields{grg}{summary}{type}                        = 'bigtext';
  $fields{grg}{summary}{label}                       = 'Summary';
  $fields{grg}{summary}{tab}                         = 'tab1';
  $fields{grg}{antibody}{type}                       = 'multiontology';
  $fields{grg}{antibody}{label}                      = 'Antibody Info';
  $fields{grg}{antibody}{tab}                        = 'tab1';
  $fields{grg}{antibody}{ontology_type}              = 'Antibody';
  $fields{grg}{antibodyremark}{type}                 = 'text';
  $fields{grg}{antibodyremark}{label}                = 'Antibody Remark';
  $fields{grg}{antibodyremark}{tab}                  = 'tab1';
  $fields{grg}{reportergene}{type}                   = 'text';
  $fields{grg}{reportergene}{label}                  = 'Reporter Gene';
  $fields{grg}{reportergene}{tab}                    = 'tab1';
  $fields{grg}{transgene}{type}                      = 'multiontology';
  $fields{grg}{transgene}{label}                     = 'Transgene';
  $fields{grg}{transgene}{tab}                       = 'tab1';
  $fields{grg}{transgene}{ontology_type}             = 'Transgene';
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
  $fields{grg}{allele}{type}                         = 'multiontology';
  $fields{grg}{allele}{label}                        = 'Allele';
  $fields{grg}{allele}{tab}                          = 'tab1';
  $fields{grg}{allele}{ontology_type}                = 'obo';
  $fields{grg}{allele}{ontology_table}               = 'variation';
  $fields{grg}{rnai}{type}                           = 'text';
  $fields{grg}{rnai}{label}                          = 'RNAi';
  $fields{grg}{rnai}{tab}                            = 'tab1';
  $fields{grg}{type}{type}                           = 'multidropdown';
  $fields{grg}{type}{label}                          = 'Type';
  $fields{grg}{type}{tab}                            = 'tab2';
  $fields{grg}{type}{dropdown_type}                  = 'grgtype';
  $fields{grg}{regulationlevel}{type}                = 'multidropdown';
  $fields{grg}{regulationlevel}{label}               = 'Regulation Level';
  $fields{grg}{regulationlevel}{tab}                 = 'tab2';
  $fields{grg}{regulationlevel}{dropdown_type}       = 'regulationlevel';
  $fields{grg}{transregulator}{type}                 = 'multiontology';
  $fields{grg}{transregulator}{label}                = 'Trans Regulator Gene';
  $fields{grg}{transregulator}{tab}                  = 'tab2';
  $fields{grg}{transregulator}{ontology_type}        = 'WBGene';
  $fields{grg}{moleculeregulator}{type}              = 'multiontology';
  $fields{grg}{moleculeregulator}{label}             = 'Molecule Regulator';
  $fields{grg}{moleculeregulator}{tab}               = 'tab2';
  $fields{grg}{moleculeregulator}{ontology_type}     = 'Molecule';
  $fields{grg}{transregulatorseq}{type}              = 'text';				# x wants text instead of gin_sequence 2011 03 16
  $fields{grg}{transregulatorseq}{label}             = 'Trans Regulator Seq';
  $fields{grg}{transregulatorseq}{tab}               = 'tab2';
  $fields{grg}{otherregulator}{type}                 = 'text';
  $fields{grg}{otherregulator}{label}                = 'Other Regulator';
  $fields{grg}{otherregulator}{tab}                  = 'tab2';
  $fields{grg}{transregulated}{type}                 = 'multiontology';
  $fields{grg}{transregulated}{label}                = 'Trans Regulated Gene';
  $fields{grg}{transregulated}{tab}                  = 'tab2';
  $fields{grg}{transregulated}{ontology_type}        = 'WBGene';
  $fields{grg}{transregulatedseq}{type}              = 'text';				# x wants text instead of gin_sequence 2011 03 16
  $fields{grg}{transregulatedseq}{label}             = 'Trans Regulated Seq';
  $fields{grg}{transregulatedseq}{tab}               = 'tab2';
  $fields{grg}{otherregulated}{type}                 = 'text';
  $fields{grg}{otherregulated}{label}                = 'Other Regulated';
  $fields{grg}{otherregulated}{tab}                  = 'tab2';
  $fields{grg}{exprpattern}{type}                    = 'multiontology';
  $fields{grg}{exprpattern}{label}                   = 'Expression Pattern';
  $fields{grg}{exprpattern}{tab}                     = 'tab2';
  $fields{grg}{exprpattern}{ontology_type}           = 'obo';
  $fields{grg}{exprpattern}{ontology_table}          = 'exprpattern';
  $fields{grg}{nodump}{type}                         = 'toggle';
  $fields{grg}{nodump}{label}                        = 'NO DUMP';
  $fields{grg}{nodump}{tab}                          = 'tab2';
  $fields{grg}{result}{type}                         = 'dropdown';
  $fields{grg}{result}{label}                        = 'Result';
  $fields{grg}{result}{tab}                          = 'tab3';
  $fields{grg}{result}{dropdown_type}                = 'regulates';
  $fields{grg}{anat_term}{type}                      = 'multiontology';
  $fields{grg}{anat_term}{label}                     = 'Anatomy Term';
  $fields{grg}{anat_term}{tab}                       = 'tab3';
  $fields{grg}{anat_term}{ontology_type}             = 'obo';
  $fields{grg}{anat_term}{ontology_table}            = 'anatomy';
  $fields{grg}{lifestage}{type}                      = 'multiontology';
  $fields{grg}{lifestage}{label}                     = 'Life Stage';
  $fields{grg}{lifestage}{tab}                       = 'tab3';
  $fields{grg}{lifestage}{ontology_type}             = 'obo';
  $fields{grg}{lifestage}{ontology_table}            = 'lifestage';
  $fields{grg}{subcellloc}{type}                     = 'toggle_text';
  $fields{grg}{subcellloc}{label}                    = 'Subcellular Localization';
  $fields{grg}{subcellloc}{tab}                      = 'tab3';
  $fields{grg}{subcellloc}{inline}                   = 'subcellloc_text';
  $fields{grg}{subcellloc_text}{type}                = 'text';
  $fields{grg}{subcellloc_text}{label}               = 'SCL Text';
  $fields{grg}{subcellloc_text}{tab}                 = 'tab3';
  $fields{grg}{subcellloc_text}{inline}              = 'INSIDE_subcellloc_text';
  $fields{grg}{remark}{type}                         = 'bigtext';
  $fields{grg}{remark}{label}                        = 'Remark';
  $fields{grg}{remark}{tab}                          = 'tab3';
  @{ $datatypes{grg}{constraintTablesHaveData} }     = qw( paper name summary );
  @{ $datatypes{grg}{highestPgidTables} }            = qw( name curator );
  $datatypes{grg}{newRowSub}                         = \&newRowGrg;
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
  $fields{int}{nondirectional}{type}                 = 'toggle';
  $fields{int}{nondirectional}{label}                = 'Non_directional';
  $fields{int}{nondirectional}{tab}                  = 'tab1';
  $fields{int}{type}{type}                           = 'dropdown';
  $fields{int}{type}{label}                          = 'Interaction Type';
  $fields{int}{type}{tab}                            = 'tab1';
  $fields{int}{type}{dropdown_type}                  = 'inttype';
  $fields{int}{geneone}{type}                        = 'multiontology';
  $fields{int}{geneone}{label}                       = 'Effector Gene';
  $fields{int}{geneone}{tab}                         = 'tab1';
  $fields{int}{geneone}{ontology_type}               = 'WBGene';
  $fields{int}{variationone}{type}                   = 'multiontology';
  $fields{int}{variationone}{label}                  = 'Effector Variation';
  $fields{int}{variationone}{tab}                    = 'tab1';
  $fields{int}{variationone}{ontology_type}          = 'obo';
  $fields{int}{variationone}{ontology_table}         = 'variation';
  $fields{int}{transgeneone}{type}                   = 'ontology';
  $fields{int}{transgeneone}{label}                  = 'Effector Transgene Name';
  $fields{int}{transgeneone}{tab}                    = 'tab1';
  $fields{int}{transgeneone}{ontology_type}          = 'Transgene';
  $fields{int}{transgeneonegene}{type}               = 'multiontology';
  $fields{int}{transgeneonegene}{label}              = 'Effector Transgene Gene';
  $fields{int}{transgeneonegene}{tab}                = 'tab1';
  $fields{int}{transgeneonegene}{ontology_type}      = 'WBGene';
  $fields{int}{otheronetype}{type}                   = 'dropdown';
  $fields{int}{otheronetype}{label}                  = 'Effector Other Type';
  $fields{int}{otheronetype}{tab}                    = 'tab1';
  $fields{int}{otheronetype}{dropdown_type}          = 'intothertype';
  $fields{int}{otherone}{type}                       = 'text';
  $fields{int}{otherone}{label}                      = 'Effector Other';
  $fields{int}{otherone}{tab}                        = 'tab1';
  $fields{int}{genetwo}{type}                        = 'multiontology';
  $fields{int}{genetwo}{label}                       = 'Effected Gene';
  $fields{int}{genetwo}{tab}                         = 'tab1';
  $fields{int}{genetwo}{ontology_type}               = 'WBGene';
  $fields{int}{variationtwo}{type}                   = 'multiontology';
  $fields{int}{variationtwo}{label}                  = 'Effected Variation';
  $fields{int}{variationtwo}{tab}                    = 'tab1';
  $fields{int}{variationtwo}{ontology_type}          = 'obo';
  $fields{int}{variationtwo}{ontology_table}         = 'variation';
  $fields{int}{transgenetwo}{type}                   = 'ontology';
  $fields{int}{transgenetwo}{label}                  = 'Effected Transgene Name';
  $fields{int}{transgenetwo}{tab}                    = 'tab1';
  $fields{int}{transgenetwo}{ontology_type}          = 'Transgene';
  $fields{int}{transgenetwogene}{type}               = 'multiontology';
  $fields{int}{transgenetwogene}{label}              = 'Effected Transgene Gene';
  $fields{int}{transgenetwogene}{tab}                = 'tab1';
  $fields{int}{transgenetwogene}{ontology_type}      = 'WBGene';
  $fields{int}{othertwotype}{type}                   = 'dropdown';
  $fields{int}{othertwotype}{label}                  = 'Effected Other Type';
  $fields{int}{othertwotype}{tab}                    = 'tab1';
  $fields{int}{othertwotype}{dropdown_type}          = 'intothertype';
  $fields{int}{othertwo}{type}                       = 'text';
  $fields{int}{othertwo}{label}                      = 'Effected Other';
  $fields{int}{othertwo}{tab}                        = 'tab1';
  $fields{int}{curator}{type}                        = 'dropdown';
  $fields{int}{curator}{label}                       = 'Curator';
  $fields{int}{curator}{tab}                         = 'tab2';
  $fields{int}{curator}{dropdown_type}               = 'curator';
  $fields{int}{paper}{type}                          = 'ontology';
  $fields{int}{paper}{label}                         = 'Paper';
  $fields{int}{paper}{tab}                           = 'tab2';
  $fields{int}{paper}{ontology_type}                 = 'WBPaper';
  $fields{int}{person}{type}                         = 'multiontology';
  $fields{int}{person}{label}                        = 'Person';
  $fields{int}{person}{tab}                          = 'tab2';
  $fields{int}{person}{ontology_type}                = 'WBPerson';
  $fields{int}{rnai}{type}                           = 'text';
  $fields{int}{rnai}{label}                          = 'RNAi';
  $fields{int}{rnai}{tab}                            = 'tab2';
  $fields{int}{phenotype}{type}                      = 'multiontology';
  $fields{int}{phenotype}{label}                     = 'Phenotype';
  $fields{int}{phenotype}{tab}                       = 'tab2';
  $fields{int}{phenotype}{ontology_type}             = 'obo';
  $fields{int}{phenotype}{ontology_table}            = 'phenotype';
  $fields{int}{remark}{type}                         = 'bigtext';
  $fields{int}{remark}{label}                        = 'Remark';
  $fields{int}{remark}{tab}                          = 'tab2';
  $fields{int}{sentid}{type}                         = 'ontology';
  $fields{int}{sentid}{label}                        = 'Sentence ID';
  $fields{int}{sentid}{tab}                          = 'tab2';
  $fields{int}{sentid}{ontology_type}                = 'obo';
  $fields{int}{sentid}{ontology_table}               = 'intsentid';
  $fields{int}{falsepositive}{type}                  = 'toggle';
  $fields{int}{falsepositive}{label}                 = 'False Positive';
  $fields{int}{falsepositive}{tab}                   = 'tab2';
  $datatypes{int}{newRowSub}                         = \&newRowInt;
  @{ $datatypes{int}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormIntFields

sub initWormMopFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{mop} }, "Tie::IxHash";
  $fields{mop}{id}{type}                             = 'text';
  $fields{mop}{id}{label}                            = 'pgid';
  $fields{mop}{id}{tab}                              = 'all';
  $fields{mop}{paper}{type}                          = 'multiontology';
  $fields{mop}{paper}{label}                         = 'WBPaper';
  $fields{mop}{paper}{tab}                           = 'all';
  $fields{mop}{paper}{ontology_type}                 = 'WBPaper';
  $fields{mop}{publicname}{type}                     = 'bigtext';
  $fields{mop}{publicname}{label}                    = 'Public Name';
  $fields{mop}{publicname}{tab}                      = 'all';
  $fields{mop}{synonym}{type}                        = 'bigtext';
  $fields{mop}{synonym}{label}                       = 'Synonyms';
  $fields{mop}{synonym}{tab}                         = 'all';
  $fields{mop}{moleculeuse}{type}                    = 'bigtext';
  $fields{mop}{moleculeuse}{label}                   = 'Molecule Use';
  $fields{mop}{moleculeuse}{tab}                     = 'all';
  $fields{mop}{molecule}{type}                       = 'text';
  $fields{mop}{molecule}{label}                      = 'MeSH / CTD or default';
  $fields{mop}{molecule}{tab}                        = 'all';
  $fields{mop}{chemi}{type}                          = 'text';
  $fields{mop}{chemi}{label}                         = 'CasRN';
  $fields{mop}{chemi}{tab}                           = 'all';
  $fields{mop}{chebi}{type}                          = 'ontology';
  $fields{mop}{chebi}{label}                         = 'ChEBI_ID';
  $fields{mop}{chebi}{tab}                           = 'all';
  $fields{mop}{chebi}{ontology_type}                 = 'obo';
  $fields{mop}{chebi}{ontology_table}                = 'chebi';
  $fields{mop}{kegg}{type}                           = 'text';
  $fields{mop}{kegg}{label}                          = 'Kegg compound (Acc#)';
  $fields{mop}{kegg}{tab}                            = 'all';
  $fields{mop}{smmid}{type}                          = 'text';
  $fields{mop}{smmid}{label}                         = 'SMMID';
  $fields{mop}{smmid}{tab}                           = 'all';
  $fields{mop}{curator}{type}                        = 'dropdown';
  $fields{mop}{curator}{label}                       = 'Curator';
  $fields{mop}{curator}{tab}                         = 'all';
  $fields{mop}{curator}{dropdown_type}               = 'curator';
  $fields{mop}{remark}{type}                         = 'bigtext';
  $fields{mop}{remark}{label}                        = 'Remark';
  $fields{mop}{remark}{tab}                          = 'all';
  $datatypes{mop}{newRowSub}                         = \&newRowMop;
  @{ $datatypes{mop}{highestPgidTables} }            = qw( molecule curator );
  return( \%fields, \%datatypes);
} # sub initWormMopFields

sub initWormPicFields {
  my ($datatype, $curator_two) = @_;
  my %fields; my %datatypes;
  tie %{ $fields{pic} }, "Tie::IxHash";
  $fields{pic}{id}{type}                             = 'text';
  $fields{pic}{id}{label}                            = 'pgid';
  $fields{pic}{id}{tab}                              = 'all';
  $fields{pic}{name}{type}                           = 'text';
  $fields{pic}{name}{label}                          = 'WBPicture';
  $fields{pic}{name}{tab}                            = 'all';
  $fields{pic}{paper}{type}                          = 'ontology';
  $fields{pic}{paper}{label}                         = 'Reference';
  $fields{pic}{paper}{tab}                           = 'all';
  $fields{pic}{paper}{ontology_type}                 = 'WBPaper';
  $fields{pic}{contact}{type}                        = 'multiontology';
  $fields{pic}{contact}{label}                       = 'Contact';
  $fields{pic}{contact}{tab}                         = 'all';
  $fields{pic}{contact}{ontology_type}               = 'WBPerson';
  $fields{pic}{description}{type}                    = 'bigtext';
  $fields{pic}{description}{label}                   = 'Description';
  $fields{pic}{description}{tab}                     = 'all';
  $fields{pic}{source}{type}                         = 'text';
  $fields{pic}{source}{label}                        = 'Source';
  $fields{pic}{source}{tab}                          = 'all';
  $fields{pic}{croppedfrom}{type}                    = 'ontology';
  $fields{pic}{croppedfrom}{label}                   = 'Cropped_from';
  $fields{pic}{croppedfrom}{tab}                     = 'all';
  $fields{pic}{croppedfrom}{ontology_type}           = 'WBPicture';
  $fields{pic}{exprpattern}{type}                    = 'multiontology';
  $fields{pic}{exprpattern}{label}                   = 'Expression Pattern';
  $fields{pic}{exprpattern}{tab}                     = 'all';
  $fields{pic}{exprpattern}{ontology_type}           = 'obo';
  $fields{pic}{exprpattern}{ontology_table}          = 'exprpattern';
  $fields{pic}{remark}{type}                         = 'bigtext';
  $fields{pic}{remark}{label}                        = 'Remark';
  $fields{pic}{remark}{tab}                          = 'all';
  $fields{pic}{goid}{type}                           = 'multiontology';
  $fields{pic}{goid}{label}                          = 'Cellular_component';
  $fields{pic}{goid}{tab}                            = 'all';
  $fields{pic}{goid}{ontology_type}                  = 'obo';
  $fields{pic}{goid}{ontology_table}                 = 'goid';
  $fields{pic}{anat_term}{type}                      = 'multiontology';
  $fields{pic}{anat_term}{label}                     = 'Anatomy_term';
  $fields{pic}{anat_term}{tab}                       = 'all';
  $fields{pic}{anat_term}{ontology_type}             = 'obo';
  $fields{pic}{anat_term}{ontology_table}            = 'anatomy';
  $fields{pic}{urlaccession}{type}                   = 'text';
  $fields{pic}{urlaccession}{label}                  = 'URL Accession';
  $fields{pic}{urlaccession}{tab}                    = 'all';
  $fields{pic}{person}{type}                         = 'multiontology';
  $fields{pic}{person}{label}                        = 'Person';
  $fields{pic}{person}{tab}                          = 'all';
  $fields{pic}{person}{ontology_type}                = 'WBPerson';
  $fields{pic}{persontext}{type}                     = 'text';
  $fields{pic}{persontext}{label}                    = 'Person Text';
  $fields{pic}{persontext}{tab}                      = 'all';
  $fields{pic}{lifestage}{type}                      = 'multiontology';
  $fields{pic}{lifestage}{label}                     = 'Life Stage';
  $fields{pic}{lifestage}{tab}                       = 'all';
  $fields{pic}{lifestage}{ontology_type}             = 'obo';
  $fields{pic}{lifestage}{ontology_table}            = 'lifestage';
  $fields{pic}{curator}{type}                        = 'dropdown';
  $fields{pic}{curator}{label}                       = 'Curator';
  $fields{pic}{curator}{tab}                         = 'all';
  $fields{pic}{curator}{dropdown_type}               = 'curator';
  $fields{pic}{nodump}{type}                         = 'toggle';
  $fields{pic}{nodump}{label}                        = 'NO DUMP';
  $fields{pic}{nodump}{tab}                          = 'all';
  $fields{pic}{chris}{type}                          = 'toggle';
  $fields{pic}{chris}{label}                         = 'Chris Flag';
  $fields{pic}{chris}{tab}                           = 'all';
  $datatypes{pic}{newRowSub}                         = \&newRowPic;
  @{ $datatypes{pic}{highestPgidTables} }            = qw( name curator );
  return( \%fields, \%datatypes);
} # sub initWormPicFields

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
  @{ $datatypes{ptg}{highestPgidTables} }            = qw( term curator );
  return( \%fields, \%datatypes);
} # sub initWormPtgFields

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
  $fields{trp}{synonym}{type}                        = 'text';
  $fields{trp}{synonym}{label}                       = 'Synonym';
  $fields{trp}{synonym}{tab}                         = 'tab1';
  $fields{trp}{summary}{type}                        = 'bigtext';
  $fields{trp}{summary}{label}                       = 'Summary';
  $fields{trp}{summary}{tab}                         = 'tab1';
  $fields{trp}{driven_by_gene}{type}                 = 'multiontology';
  $fields{trp}{driven_by_gene}{label}                = 'Driven By Gene';
  $fields{trp}{driven_by_gene}{tab}                  = 'tab1';
  $fields{trp}{driven_by_gene}{ontology_type}        = 'WBGene';
  $fields{trp}{reporter_product}{type}               = 'multidropdown';
  $fields{trp}{reporter_product}{label}              = 'Reporter Product';
  $fields{trp}{reporter_product}{tab}                = 'tab1';
  $fields{trp}{reporter_product}{dropdown_type}      = 'reporterproduct';
  $fields{trp}{other_reporter}{type}                 = 'text';			# pipe separated
  $fields{trp}{other_reporter}{label}                = 'Other Reporter';
  $fields{trp}{other_reporter}{tab}                  = 'tab1';
  $fields{trp}{gene}{type}                           = 'multiontology';
  $fields{trp}{gene}{label}                          = 'Gene';
  $fields{trp}{gene}{tab}                            = 'tab1';
  $fields{trp}{gene}{ontology_type}                  = 'WBGene';
  $fields{trp}{coinjection}{type}                    = 'text';
  $fields{trp}{coinjection}{label}                   = 'Coninjection';
  $fields{trp}{coinjection}{tab}                     = 'tab1';
  $fields{trp}{reporter_type}{type}                  = 'dropdown';
  $fields{trp}{reporter_type}{label}                 = 'Reporter Type';
  $fields{trp}{reporter_type}{tab}                   = 'tab1';
  $fields{trp}{reporter_type}{dropdown_type}         = 'trpreportertype';
  $fields{trp}{remark}{type}                         = 'bigtext';
  $fields{trp}{remark}{label}                        = 'Remark';
  $fields{trp}{remark}{tab}                          = 'tab1';
  $fields{trp}{rescues}{type}                        = 'ontology';
  $fields{trp}{rescues}{label}                       = 'Rescues';
  $fields{trp}{rescues}{tab}                         = 'tab2';
  $fields{trp}{rescues}{ontology_type}               = 'obo';
  $fields{trp}{rescues}{ontology_table}              = 'variation';
  $fields{trp}{clone}{type}                          = 'multiontology';
  $fields{trp}{clone}{label}                         = 'Clone';
  $fields{trp}{clone}{tab}                           = 'tab2';
  $fields{trp}{clone}{ontology_type}                 = 'obo';
  $fields{trp}{clone}{ontology_table}                = 'clone';
  $fields{trp}{integration_method}{type}             = 'dropdown';
  $fields{trp}{integration_method}{label}            = 'Integration Method';
  $fields{trp}{integration_method}{tab}              = 'tab2';
  $fields{trp}{integration_method}{dropdown_type}    = 'integrationmethod';
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
  $fields{trp}{paper}{type}                          = 'multiontology';
  $fields{trp}{paper}{label}                         = 'Paper';
  $fields{trp}{paper}{tab}                           = 'tab3';
  $fields{trp}{paper}{ontology_type}                 = 'WBPaper';
  $fields{trp}{person}{type}                         = 'multiontology';
  $fields{trp}{person}{label}                        = 'Person';
  $fields{trp}{person}{tab}                          = 'tab3';
  $fields{trp}{person}{ontology_type}                = 'WBPerson';
  $fields{trp}{marker_for}{type}                     = 'text';
  $fields{trp}{marker_for}{label}                    = 'Marker for';
  $fields{trp}{marker_for}{tab}                      = 'tab3';
  $fields{trp}{marker_for_paper}{type}               = 'multiontology';
  $fields{trp}{marker_for_paper}{label}              = 'Marker for Paper';
  $fields{trp}{marker_for_paper}{tab}                = 'tab3';
  $fields{trp}{marker_for_paper}{ontology_type}      = 'WBPaper';
  $fields{trp}{species}{type}                        = 'text';
  $fields{trp}{species}{label}                       = 'Species';
  $fields{trp}{species}{tab}                         = 'tab3';
  $fields{trp}{driven_by_construct}{type}            = 'text';
  $fields{trp}{driven_by_construct}{label}           = 'Driven by Construct';
  $fields{trp}{driven_by_construct}{tab}             = 'tab3';
  $fields{trp}{searchnew}{type}                      = 'queryonly';
  $fields{trp}{searchnew}{label}                     = 'Search new';
  $fields{trp}{searchnew}{tab}                       = 'tab3';
  $fields{trp}{searchnew}{queryonlySub}              = \&checkTrpQueryonly;
  $fields{trp}{objpap_falsepos}{type}                = 'toggle';
  $fields{trp}{objpap_falsepos}{label}               = 'Fail';
  $fields{trp}{objpap_falsepos}{tab}                 = 'tab3';
  $datatypes{trp}{newRowSub}                         = \&newRowTrp;
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
sub newRowExp {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('exp_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my ($newExprId) = &getHighestExprId(); $newExprId++;
    ($returnValue)  = &insertToPostgresTableAndHistory('exp_name', $newPgid, "Expr$newExprId"); }
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
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('grg_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowInt {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('int_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowMop {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('mop_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') {
    my $molId = &pad8Zeros($newPgid); 
    ($returnValue)  = &insertToPostgresTableAndHistory('mop_molecule', $newPgid, "WBMol:$molId"); }
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
sub newRowPtg {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('ptg_curator', $newPgid, $curator);
  if ($returnValue eq 'OK') { $returnValue = $newPgid; } 
  return $returnValue; }
sub newRowTrp {
  my ($newPgid, $curator_two) = @_; my $curator = $curator_two; $curator =~ s/two/WBPerson/;
  my ($returnValue) = &insertToPostgresTableAndHistory('trp_curator', $newPgid, $curator);
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

sub checkTrpQueryonly {		# sample query only field with a made-up query.  should filter out joinkeys, and probably order by desc timestamp.
  my ($joinkeys) = @_;							# joinkeys already in dataTable to exclude from query
  return "SELECT joinkey FROM trp_name WHERE joinkey NOT IN ('$joinkeys') AND trp_name ~ 'arIs' ORDER BY trp_timestamp DESC";
} # sub checkTrpQueryonly

### END QUERY ONLY ###



### ONTOLOGY / MULTIONTOLOGY ###

### AUTOCOMPLETE ###

sub setAnySimpleAutocompleteValues {
  my ($ontology_type) = @_;
  my %data;
  if ($ontology_type eq 'curator') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"Juancarlos Chan"} = "Juancarlos Chan ( WBPerson1823 ) ";
    $data{$ontology_type}{name}{"Wen Chen"} = "Wen Chen ( WBPerson101 ) ";
    $data{$ontology_type}{name}{"Jolene Fernandes"} = "Jolene Fernandes ( WBPerson2021 ) ";
    $data{$ontology_type}{name}{"Chris"} = "Chris ( WBPerson2987 ) ";
    $data{$ontology_type}{name}{"Snehalata Kadam"} = "Snehalata Kadam ( WBPerson12884 ) ";
    $data{$ontology_type}{name}{"Ranjana Kishore"} = "Ranjana Kishore ( WBPerson324 ) ";
    $data{$ontology_type}{name}{"Daniela Raciti"} = "Daniela Raciti ( WBPerson12028 ) ";
    $data{$ontology_type}{name}{"Arun Rangarajan"} = "Arun Rangarajan ( WBPerson4793 ) ";
    $data{$ontology_type}{name}{"Gary Schindelman"} = "Gary Schindelman ( WBPerson557 ) ";
    $data{$ontology_type}{name}{"Kimberly Van Auken"} = "Kimberly Van Auken ( WBPerson1843 ) ";
    $data{$ontology_type}{name}{"Xiaodong Wang"} = "Xiaodong Wang ( WBPerson1760 ) ";
    $data{$ontology_type}{name}{"Karen Yook"} = "Karen Yook ( WBPerson712 ) ";
    $data{$ontology_type}{name}{"Carol Bastiani"} = "Carol Bastiani ( WBPerson48 ) ";
    $data{$ontology_type}{name}{"Keith Bradnam"} = "Keith Bradnam ( WBPerson1971 ) ";
    $data{$ontology_type}{name}{"Chao-Kung Chen"} = "Chao-Kung Chen ( WBPerson1845 ) ";
    $data{$ontology_type}{name}{"Uhma Ganesan"} = "Uhma Ganesan ( WBPerson13088 ) ";
    $data{$ontology_type}{name}{"Josh Jaffery"} = "Josh Jaffery ( WBPerson5196 ) ";
    $data{$ontology_type}{name}{"Sylvia Martinelli"} = "Sylvia Martinelli ( WBPerson1250 ) ";
    $data{$ontology_type}{name}{"Tuco"} = "Tuco ( WBPerson480 ) ";
    $data{$ontology_type}{name}{"Mary Ann Tuli"} = "Mary Ann Tuli ( WBPerson2970 ) "; }
  elsif ($ontology_type eq 'clonality') {
    $data{$ontology_type}{name}{"Polyclonal"} = "Polyclonal";
    $data{$ontology_type}{name}{"Monoclonal"} = "Monoclonal"; }
  elsif ($ontology_type eq 'animal') {
    $data{$ontology_type}{name}{"Rabbit"} = "Rabbit";
    $data{$ontology_type}{name}{"Mouse"} = "Mouse";
    $data{$ontology_type}{name}{"Rat"} = "Rat";
    $data{$ontology_type}{name}{"Guinea_pig"} = "Guinea_pig";
    $data{$ontology_type}{name}{"Chicken"} = "Chicken";
    $data{$ontology_type}{name}{"Goat"} = "Goat";
    $data{$ontology_type}{name}{"Other_animal"} = "Other_animal"; }
  elsif ($ontology_type eq 'antigen') {
    $data{$ontology_type}{name}{"Peptide"} = "Peptide";
    $data{$ontology_type}{name}{"Protein"} = "Protein";
    $data{$ontology_type}{name}{"Other_antigen"} = "Other_antigen"; }
  elsif ($ontology_type eq 'abpsource') {
    $data{$ontology_type}{name}{"Original_publication"} = "Original_publication";
    $data{$ontology_type}{name}{"No_original_reference"} = "No_original_reference"; }
  elsif ($ontology_type eq 'exprqualifier') {
    $data{$ontology_type}{name}{"Certain"} = "Certain";
    $data{$ontology_type}{name}{"Partial"} = "Partial";
    $data{$ontology_type}{name}{"Uncertain"} = "Uncertain"; }
  elsif ($ontology_type eq 'exprtype') {
    $data{$ontology_type}{name}{"Antibody"} = "Antibody";
    $data{$ontology_type}{name}{"Reporter_gene"} = "Reporter_gene";
    $data{$ontology_type}{name}{"In_Situ"} = "In_Situ";
    $data{$ontology_type}{name}{"RT_PCR"} = "RT_PCR";
    $data{$ontology_type}{name}{"Northern"} = "Northern";
    $data{$ontology_type}{name}{"Western"} = "Western"; }
  elsif ($ontology_type eq 'gclstatus') {
    $data{$ontology_type}{name}{"done"} = "done";
    $data{$ontology_type}{name}{"incomplete"} = "incomplete";
    $data{$ontology_type}{name}{"recheck"} = "recheck"; }
  elsif ($ontology_type eq 'gcltype') {
    $data{$ontology_type}{name}{"molecular"} = "molecular";
    $data{$ontology_type}{name}{"phenotype"} = "phenotype";
    $data{$ontology_type}{name}{"phenotype-function"} = "phenotype-function";
    $data{$ontology_type}{name}{"other"} = "other"; }
  elsif ($ontology_type eq 'goontology') {
    $data{$ontology_type}{name}{"F"} = "F ( mol ) ";
    $data{$ontology_type}{name}{"P"} = "P ( bio ) ";
    $data{$ontology_type}{name}{"C"} = "C ( cell ) "; }
  elsif ($ontology_type eq 'goproject') {
    $data{$ontology_type}{name}{"Reference Genomes"} = "Reference Genomes";
    $data{$ontology_type}{name}{"PAINT"} = "PAINT";
    $data{$ontology_type}{name}{"Variation phenotype2GO"} = "Variation phenotype2GO";
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
    $data{$ontology_type}{name}{"ND"} = "ND";
    $data{$ontology_type}{name}{"IC"} = "IC";
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
    $data{$ontology_type}{name}{"NOT"} = "NOT";
    $data{$ontology_type}{name}{"contributes_to"} = "contributes_to";
    $data{$ontology_type}{name}{"colocalizes_with"} = "colocalizes_with"; }
  elsif ($ontology_type eq 'godbtype') {
    $data{$ontology_type}{name}{"protein"} = "protein";
    $data{$ontology_type}{name}{"gene"} = "gene";
    $data{$ontology_type}{name}{"transcript"} = "transcript";
    $data{$ontology_type}{name}{"complex"} = "complex";
    $data{$ontology_type}{name}{"protein_structure"} = "protein_structure"; }
  elsif ($ontology_type eq 'grgtype') {
    $data{$ontology_type}{name}{"Change_of_localization"} = "Change_of_localization";
    $data{$ontology_type}{name}{"Change_of_expression_level"} = "Change_of_expression_level"; }
  elsif ($ontology_type eq 'regulationlevel') {
    $data{$ontology_type}{name}{"Transcriptional"} = "Transcriptional";
    $data{$ontology_type}{name}{"Post_transcriptional"} = "Post_transcriptional";
    $data{$ontology_type}{name}{"Post_translational"} = "Post_translational"; }
  elsif ($ontology_type eq 'regulates') {
    $data{$ontology_type}{name}{"Positive_regulate"} = "Positive_regulate";
    $data{$ontology_type}{name}{"Negative_regulate"} = "Negative_regulate";
    $data{$ontology_type}{name}{"Does_not_regulate"} = "Does_not_regulate"; }
  elsif ($ontology_type eq 'inttype') {
    $data{$ontology_type}{name}{"Regulatory"} = "Regulatory";
    $data{$ontology_type}{name}{"Suppression"} = "Suppression";
    $data{$ontology_type}{name}{"Enhancement"} = "Enhancement";
    $data{$ontology_type}{name}{"Epistasis"} = "Epistasis";
    $data{$ontology_type}{name}{"Genetic"} = "Genetic";
    $data{$ontology_type}{name}{"No_interaction"} = "No_interaction";
    $data{$ontology_type}{name}{"Predicted_interaction"} = "Predicted_interaction";
    $data{$ontology_type}{name}{"Physical_interaction"} = "Physical_interaction";
    $data{$ontology_type}{name}{"Synthetic"} = "Synthetic";
    $data{$ontology_type}{name}{"Mutual_enhancement"} = "Mutual_enhancement";
    $data{$ontology_type}{name}{"Mutual_suppression"} = "Mutual_suppression"; }
  elsif ($ontology_type eq 'intothertype') {
    $data{$ontology_type}{name}{"Transgene"} = "Transgene";
    $data{$ontology_type}{name}{"Chemical"} = "Chemical"; }
  elsif ($ontology_type eq 'trpreportertype') {
    $data{$ontology_type}{name}{"Transcriptional fusion"} = "Transcriptional fusion";
    $data{$ontology_type}{name}{"Translational fusion"} = "Translational fusion"; }
  elsif ($ontology_type eq 'reporterproduct') {
    tie %{ $data{$ontology_type}{name} }, "Tie::IxHash";
    $data{$ontology_type}{name}{"GFP"} = "GFP";
    $data{$ontology_type}{name}{"YFP"} = "YFP";
    $data{$ontology_type}{name}{"CFP"} = "CFP";
    $data{$ontology_type}{name}{"LacZ"} = "LacZ";
    $data{$ontology_type}{name}{"mCherry"} = "mCherry";
    $data{$ontology_type}{name}{"DsRed"} = "DsRed";
    $data{$ontology_type}{name}{"DsRed2"} = "DsRed2";
    $data{$ontology_type}{name}{"Venus"} = "Venus";
    $data{$ontology_type}{name}{"tdimer2(12)"} = "tdimer2(12)";
    $data{$ontology_type}{name}{"RFP"} = "RFP"; }
  elsif ($ontology_type eq 'integrationmethod') {
    $data{$ontology_type}{name}{"Gamma_ray"} = "Gamma_ray";
    $data{$ontology_type}{name}{"X_ray"} = "X_ray";
    $data{$ontology_type}{name}{"Spontaneous"} = "Spontaneous";
    $data{$ontology_type}{name}{"UV"} = "UV";
    $data{$ontology_type}{name}{"UV"} = "UV";
    $data{$ontology_type}{name}{"MMS mutagenesis"} = "MMS mutagenesis";
    $data{$ontology_type}{name}{"Single copy insertion"} = "Single copy insertion";
    $data{$ontology_type}{name}{"Particle_bombardment"} = "Particle_bombardment"; }
  elsif ($ontology_type eq 'chromosome') {
    $data{$ontology_type}{name}{"I"} = "I";
    $data{$ontology_type}{name}{"II"} = "II";
    $data{$ontology_type}{name}{"III"} = "III";
    $data{$ontology_type}{name}{"IV"} = "IV";
    $data{$ontology_type}{name}{"V"} = "V";
    $data{$ontology_type}{name}{"X"} = "X"; }
  elsif ($ontology_type eq 'curationstatus') {
    $data{$ontology_type}{name}{"happy"} = "happy";
    $data{$ontology_type}{name}{"not_happy"} = "not_happy";
    $data{$ontology_type}{name}{"down_right_disgusted"} = "down_right_disgusted"; }
  elsif ($ontology_type eq 'allelestatus') {
    $data{$ontology_type}{name}{"other"} = "other";
    $data{$ontology_type}{name}{"lost"} = "lost";
    $data{$ontology_type}{name}{"new_gene_assignment"} = "new_gene_assignment"; }
  elsif ($ontology_type eq 'nature') {
#     $data{$ontology_type}{name}{"Recessive"} = "Recessive ( WBnature000001 ) ";
#     $data{$ontology_type}{name}{"Semi_dominant"} = "Semi_dominant ( WBnature000002 ) ";
#     $data{$ontology_type}{name}{"Dominant"} = "Dominant ( WBnature000003 ) ";
    $data{$ontology_type}{name}{"Recessive"} = "Recessive";
    $data{$ontology_type}{name}{"Semi_dominant"} = "Semi_dominant";
    $data{$ontology_type}{name}{"Dominant"} = "Dominant"; }
  elsif ($ontology_type eq 'func') {
#     $data{$ontology_type}{name}{"Amorph"} = "Amorph ( WBfunc000001 ) ";
#     $data{$ontology_type}{name}{"Hypomorph"} = "Hypomorph ( WBfunc000002 ) ";
#     $data{$ontology_type}{name}{"Isoallele"} = "Isoallele ( WBfunc000003 ) ";
#     $data{$ontology_type}{name}{"Uncharacterised_loss_of_function"} = "Uncharacterised_loss_of_function ( WBfunc000004 ) ";
#     $data{$ontology_type}{name}{"Wild_type"} = "Wild_type ( WBfunc000005 ) ";
#     $data{$ontology_type}{name}{"Hypermorph"} = "Hypermorph ( WBfunc000006 ) ";
#     $data{$ontology_type}{name}{"Uncharacterised_gain_of_function"} = "Uncharacterised_gain_of_function ( WBfunc000007 ) ";
#     $data{$ontology_type}{name}{"Neomorph"} = "Neomorph ( WBfunc000008 ) ";
#     $data{$ontology_type}{name}{"Dominant_negative"} = "Dominant_negative ( WBfunc000009 ) ";
#     $data{$ontology_type}{name}{"Mixed"} = "Mixed ( WBfunc000010 ) ";
#     $data{$ontology_type}{name}{"Gain_of_function"} = "Gain_of_function ( WBfunc000011 ) ";
#     $data{$ontology_type}{name}{"Loss_of_function"} = "Loss_of_function ( WBfunc000012 ) ";
    $data{$ontology_type}{name}{"Amorph"} = "Amorph";
    $data{$ontology_type}{name}{"Hypomorph"} = "Hypomorph";
    $data{$ontology_type}{name}{"Isoallele"} = "Isoallele";
    $data{$ontology_type}{name}{"Uncharacterised_loss_of_function"} = "Uncharacterised_loss_of_function";
    $data{$ontology_type}{name}{"Wild_type"} = "Wild_type";
    $data{$ontology_type}{name}{"Hypermorph"} = "Hypermorph";
    $data{$ontology_type}{name}{"Uncharacterised_gain_of_function"} = "Uncharacterised_gain_of_function";
    $data{$ontology_type}{name}{"Neomorph"} = "Neomorph";
    $data{$ontology_type}{name}{"Dominant_negative"} = "Dominant_negative";
    $data{$ontology_type}{name}{"Mixed"} = "Mixed";
    $data{$ontology_type}{name}{"Gain_of_function"} = "Gain_of_function";
    $data{$ontology_type}{name}{"Loss_of_function"} = "Loss_of_function"; }
  elsif ($ontology_type eq 'penetrance') {
# FIX : DELETE THESE OLD STYLE when verified by Karen  2011 05 27
#     $data{$ontology_type}{name}{"Incomplete"} = "Incomplete ( WBpenetrance000001 ) ";
#     $data{$ontology_type}{name}{"Low"} = "Low ( WBpenetrance000002 ) ";
#     $data{$ontology_type}{name}{"High"} = "High ( WBpenetrance000003 ) ";
#     $data{$ontology_type}{name}{"Complete"} = "Complete ( WBpenetrance000004 ) ";
    $data{$ontology_type}{name}{"Incomplete"} = "Incomplete";
    $data{$ontology_type}{name}{"Low"} = "Low";
    $data{$ontology_type}{name}{"High"} = "High";
    $data{$ontology_type}{name}{"Complete"} = "Complete"; }
  elsif ($ontology_type eq 'mateffect') {
    $data{$ontology_type}{name}{"Maternal"} = "Maternal";
    $data{$ontology_type}{name}{"Strictly_maternal"} = "Strictly_maternal";
    $data{$ontology_type}{name}{"With_maternal_effect"} = "With_maternal_effect"; }
  elsif ($ontology_type eq 'species') {
    $data{$ontology_type}{name}{"Caenorhabditis_sp._3"} = "Caenorhabditis_sp._3";
    $data{$ontology_type}{name}{"Panagrellus_redivivus"} = "Panagrellus_redivivus";
    $data{$ontology_type}{name}{"Cruznema_tripartitum"} = "Cruznema_tripartitum";
    $data{$ontology_type}{name}{"Caenorhabditis_brenneri"} = "Caenorhabditis_brenneri";
    $data{$ontology_type}{name}{"Caenorhabditis_japonica"} = "Caenorhabditis_japonica";
    $data{$ontology_type}{name}{"Caenorhabditis_briggsae"} = "Caenorhabditis_briggsae";
    $data{$ontology_type}{name}{"Caenorhabditis_remanei"} = "Caenorhabditis_remanei";
    $data{$ontology_type}{name}{"Pristionchus_pacificus"} = "Pristionchus_pacificus"; }
  return \%data;
} # sub setAnySimpleAutocompleteValues


sub getAnySpecificAutocomplete {
  my ($ontology_type, $words) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyAutocomplete($words); }
  elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeAutocomplete($words); }
  elsif ($ontology_type eq 'Transgene') {       ($matches) = &getAnyTransgeneAutocomplete($words); }
  elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneAutocomplete($words); }
  elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionAutocomplete($words); }
  elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperAutocomplete($words); }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonAutocomplete($words); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureAutocomplete($words); }
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

sub getAnyMoleculeAutocomplete {
  my ($words) = @_;
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( mop_publicname mop_molecule mop_synonym );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0];
      if ($table eq 'mop_molecule') { $matches{"$row[1] ( $id ) "}++; }
        else {
          my $result2 = $dbh->prepare( "SELECT * FROM mop_molecule WHERE joinkey = '$row[0]';" ); $result2->execute();
          my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
          if ($table eq 'mop_molecule') { $matches{"$name ( $id ) "}++; }
            else { $matches{"$row[1] ( $id ) \[$name\]"}++; } }
    }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' AND LOWER($table) !~ '^$words' ORDER BY $table;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0];
      if ($table eq 'mop_molecule') { $matches{"$row[1] ( $id ) "}++; }
        else {
          my $result2 = $dbh->prepare( "SELECT * FROM mop_molecule WHERE joinkey = '$row[0]';" ); $result2->execute();
          my @row2 = $result2->fetchrow(); my $name = $row2[1]; unless ($name) { $name = $row[1]; }
          if ($table eq 'mop_molecule') { $matches{"$name ( $id ) "}++; }
            else { $matches{"$row[1] ( $id ) \[$name\]"}++; } }
    }
    last if (scalar keys %matches >= $max_results);
  } # foreach my $table (@tables)
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

  my @tables = qw( trp_synonym );			# used to have trp_paper, but would get lots of "WBPaperNNN","WBPaperNNN" in the dataTable, which looked misleading.  2010 09 28
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
  if ($words =~ m/^wbinteraction/) { $words =~ s/^wbinteraction//; } 	# strip out the leading wbinteraction so autocomplete works when editing an entry
  my $max_results = 20; if ($words =~ m/^.{5,}/) { $max_results = 500; }
  my %matches; my $t = tie %matches, "Tie::IxHash";	# sorted hash to filter results
  my @tables = qw( int_name );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table ~ '^$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[1];
      $matches{"$id"}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE $table ~ '$words' ORDER BY joinkey;" );
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[1];
      $matches{"$id"}++; }
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
  my @tables = qw( two_standardname );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '^$words' ORDER BY $table;" );	# match by start of name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      $matches{"$row[2] ( $id ) "}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE LOWER($table) ~ '$words' ORDER BY $table;" );		# then match anywhere in the name
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      $matches{"$row[2] ( $id ) "}++; }
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey ~ '$words' ORDER BY joinkey;" );		# then match by WBPerson number
    $result->execute();
    while ( (my @row = $result->fetchrow()) && (scalar keys %matches < $max_results) ) {
      my $id = $row[0]; $id =~ s/two/WBPerson/;
      $matches{"$row[2] ( $id ) "}++; }
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

### END AUTOCOMPLETE ###


### VALID VALUE ###

sub getAnySpecificValidValue {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyValidValue($userValue); }
  elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeValidValue($userValue); }
  elsif ($ontology_type eq 'Transgene') {       ($matches) = &getAnyTransgeneValidValue($userValue); }
  elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneValidValue($userValue); }
  elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionValidValue($userValue); }
  elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperValidValue($userValue); }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonValidValue($userValue); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureValidValue($userValue); }
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

sub getAnyMoleculeValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey, $syn) = ('bad', 'bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (\d+) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( (\d+) \) $/; }
  elsif ( $userValue =~ m/^(.*?) \( (\d+) \) \[(\w+)\]$/ ) { ($syn, $joinkey, $value) = $userValue =~ m/^(.*?) \( (\d+) \) \[(\w+)\]$/; }
  my $table =  'mop_molecule';
  my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value' AND joinkey = '$joinkey';" );
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

sub getAnyWBGeneValidValue {
  my ($userValue) = @_;
  my ($value, $joinkey, $syn) = ('bad', 'bad', 'bad');
  if ( $userValue =~ m/^(.*?) \( (.*?) \) $/ ) { ($value, $joinkey) = $userValue =~ m/^(.*?) \( WBGene(.*?) \) $/; }
  elsif ( $userValue =~ m/^(.*?) \( WBGene(\d+) \) \[(.*?)\]$/ ) { ($syn, $joinkey, $value) = $userValue =~ m/^(.*?) \( WBGene(\d+) \) \[(.*?)\]$/; }
  my @tables = qw( gin_locus gin_seqname gin_wbgene );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table WHERE $table = '$value' AND joinkey = '$joinkey';" );
    $result->execute(); my @row = $result->fetchrow();
    if ($row[0]) { return "true"; } }
  return "false";
} # sub getAnyWBGeneValidValue

sub getAnyWBInteractionValidValue {
  my ($userValue) = @_;
  my $joinkey = 'bad';
  my $result = $dbh->prepare( "SELECT * FROM int_name WHERE int_name = '$userValue';" );
  $result->execute();
  my @row = $result->fetchrow();
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

### END VALID VALUE ###


### TERM INFO ### 

sub getAnySpecificTermInfo {
  my ($ontology_type, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {           ($matches) = &getAnyAntibodyTermInfo($userValue); }
  elsif ($ontology_type eq 'Molecule') {        ($matches) = &getAnyMoleculeTermInfo($userValue); }
  elsif ($ontology_type eq 'Transgene') {       ($matches) = &getAnyTransgeneTermInfo($userValue); }
  elsif ($ontology_type eq 'WBGene') {          ($matches) = &getAnyWBGeneTermInfo($userValue); }
  elsif ($ontology_type eq 'WBInteraction') {   ($matches) = &getAnyWBInteractionTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPaper') {         ($matches) = &getAnyWBPaperTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPerson') {        ($matches) = &getAnyWBPersonTermInfo($userValue); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches) = &getAnyWBPictureTermInfo($userValue); }
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

sub getAnyMoleculeTermInfo {		# get term info for molecule objects from mop_ tables
  my ($userValue) = @_; my $joinkey;
  if ($userValue =~ m/\( (\d+) \)/) { $joinkey = $1; } else { $joinkey = $userValue; }
  my $to_print;
  my $molecule_name; my $publicname; my $synonyms; my $chemi; my $chebi; my $kegg; my $remark; my $paper; my $curator;
  my $result = $dbh->prepare( "SELECT * FROM mop_molecule WHERE joinkey = '$joinkey' ;" ); $result->execute(); 
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
  my @row = $result->fetchrow(); { if ($row[0]) { my ($cur_id) = $row[1] =~ m/(\d+)/; 
    my $result2 = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = 'two$cur_id' ;" ); $result2->execute(); my @row2 = $result2->fetchrow(); $curator = $row2[2]; } }

  $to_print .= "pgid: <span style=\"font-weight: bold\">$joinkey</span><br />\n";
  $to_print .= "molecule: $molecule_name<br />\n";
  $to_print .= "public name: $publicname<br />\n";
  my @syns = split/ \| /, $synonyms;
  foreach my $syn (@syns) { $to_print .= "synonym: \"$syn\"<br />\n"; }
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
  my %info; my @tables = qw( trp_synonym trp_paper trp_summary );
  foreach my $table (@tables) { 
    $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey IN ('$joinkeys');" );
    $result->execute(); while (my @row = $result->fetchrow) { if ($row[1]) { $info{$table}{$row[1]}++; } } }
  my $to_print = "name: $value<br />\n";
  foreach my $table (@tables) { foreach my $entry (sort keys %{ $info{$table} }) { 
    if ($table eq 'trp_paper') { 
        my @papers = split/","/, $entry; foreach my $pap (@papers) { 
          my ($joinkey) = $pap =~ m/WBPaper(\d+)/; $to_print .= "Paper: <a href=\"/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!&data_number=$joinkey\" target=\"new\">WBPaper$joinkey</a><br />\n"; } }
      else { $to_print .= "${table}: $entry<br />\n"; } } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyTransgeneTermInfo

sub getAnyWBGeneTermInfo {
  my ($userValue) = @_;
  my ($joinkey) = $userValue =~ m/WBGene(\d+)/; my $to_print;	# has to match a WBGene from the info
  my %syns; my $locus; my $dead;
  my $result = $dbh->prepare( "SELECT * FROM gin_synonyms WHERE joinkey = '$joinkey';" ); $result->execute(); 
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_seqname WHERE joinkey = '$joinkey';" ); $result->execute(); 
  while (my @row = $result->fetchrow) { $syns{$row[1]}++; }
  $result = $dbh->prepare( "SELECT * FROM gin_locus WHERE joinkey = '$joinkey';" ); $result->execute(); 
  my @row = $result->fetchrow(); $locus = $row[1];
  $result = $dbh->prepare( "SELECT * FROM gin_dead WHERE joinkey = '$joinkey';" ); $result->execute(); 
  @row = $result->fetchrow(); $dead = $row[1];
  if ($userValue) { $to_print .= "id: WBGene$joinkey<br />\n"; }
  my $dev_link = "http://dev.wormbase.org/db/gene/gene?name=WBGene$joinkey;class=Gene";
  if ($locus) { $to_print .= "locus: <a target=\"new\" href=\"$dev_link\">$locus</a><br />\n"; }
  if ($dead) { $to_print .= "DEAD: $dead<br />\n"; }
  foreach my $syn (sort keys %syns) {
    $to_print .= "synonym: $syn<br />\n"; }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"\n", @data;
  return $to_print;
} # sub getAnyWBGeneTermInfo

sub getAnyWBInteractionTermInfo {
  my ($userValue) = @_;
  my $to_print = "id: $userValue\n";
  my $result = $dbh->prepare( "SELECT * FROM int_curator WHERE joinkey IN (SELECT joinkey FROM int_name WHERE int_name = '$userValue');" ); $result->execute(); 
  my @row = $result->fetchrow(); { if ($row[0]) { my ($cur_id) = $row[1] =~ m/(\d+)/; 
    my $result2 = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey = 'two$cur_id' ;" ); $result2->execute(); my @row2 = $result2->fetchrow(); my $curator = $row2[2]; $to_print .= "Curator: $curator<br />\n"; } }
  my (@data) = split/\n/, $to_print;
  foreach my $data_line (@data) { $data_line =~ s/^(.*?):/<span style=\"font-weight: bold\">$1 : <\/span>/; }
  $to_print = join"<br />\n", @data;
  return $to_print;
} # sub getAnyWBInteractionTermInfo

sub getAnyWBPaperTermInfo {
  my ($userValue) = @_;
  my ($joinkey) = $userValue =~ m/(\d+)/; my $to_print;
  my %title; my %ids; my %pdfs; my %journal; my %year;
  my $result = $dbh->prepare( "SELECT * FROM pap_title WHERE joinkey = '$joinkey' ;" );
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
  $result = $dbh->prepare( "SELECT * FROM pap_electronic_path WHERE joinkey = '$joinkey' ORDER BY pap_timestamp;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $pdfs{$row[0]}{$row[1]}++; } }
  my %pap_transgene;
  my $infile = '/home/acedb/karen/populate_gin_variation/transgene_summary_reference.txt';
  open (IN, "$infile") or die "Cannot open $infile : $!";
  my $junk = <IN>;
  while (my $line = <IN>) {
    chomp $line;
    next unless ($line =~ m/WBPaper$joinkey/);
    my ($transgene, $reference, $summary) = split/\t/, $line;
    my $data = "$transgene\t$summary"; $data =~ s/\"//g; $pap_transgene{$joinkey}{$data}++; }
  close (IN) or die "Cannot close $infile : $!";
  my %expr; my %expr_genes; my %gene_to_locus;
  $result = $dbh->prepare( "SELECT * FROM obo_data_exprpattern WHERE obo_data_exprpattern ~ 'WBPaper$joinkey' ;" );
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

  my %picturesource;
  $result = $dbh->prepare( "SELECT obo_data_picturesource FROM obo_data_picturesource WHERE joinkey = 'WBPaper$joinkey' ;" );
  $result->execute(); 
  while (my @row = $result->fetchrow) {
    if ($row[0]) { $picturesource{$joinkey}{$row[0]}++; } }

  $to_print .= "id: <span style=\"font-weight: bold\">WBPaper$joinkey</span><br />\n";
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
    if ($syn =~ m/pmid/) { $syn =~ s/pmid/PMID:/g; }
    $to_print .= "synonym: \"$syn\"<br />\n"; }
  my (@year) = sort keys %{ $year{$joinkey} }; my (@journal) = sort keys %{ $journal{$joinkey} };
  if (scalar(@year) > 1) { $to_print .= "ERROR : multiple years @year<br />\n"; }
    elsif (scalar(@year) > 0) { $to_print .= "Year: $year[0]<br />\n"; }
    else { $to_print .= "Year: BLANK<br />\n"; }
  if (scalar(@journal) > 1) { $to_print .= "ERROR : multiple journals @journal<br />\n"; }
    elsif (scalar(@journal) > 0) { $to_print .= "Journal: $journal[0]<br />\n"; }
    else { $to_print .= "Journal: BLANK<br />\n"; }
  $to_print .= "<hr>\n";
  foreach my $transgene (sort keys %{ $pap_transgene{$joinkey}}) { $to_print .= "transgene: $transgene<br />\n"; }
  foreach my $expr (sort keys %{ $expr{$joinkey}}) {
    my $expr_line = "expr: $expr";
    foreach my $wbgene (sort keys %{ $expr{$joinkey}{$expr} }) {
      if ($wbgene eq 'nomatch') { $expr_line .= " No WBGene match"; }
        else { $expr_line .= " WBGene$wbgene";
               if ($gene_to_locus{$wbgene}) { $expr_line .= " $gene_to_locus{$wbgene}"; } } }
    $to_print .= "$expr_line<br />\n"; }
  foreach my $picturesource (sort keys %{ $picturesource{$joinkey}}) { 	# all this obo data is in one entry, so split and print with <br /> 2010 12 06
    my (@lines) = split/\n/, $picturesource; foreach my $line (@lines) { $to_print .= "$line<br />\n"; } }
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

### END TERM INFO ### 


### ID TO VALUE ###

sub getAnySpecificIdToValue {			# convert values from postgres values (ids) to what someone types for dataTable display
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_; my $matches = '';
  if ($ontology_type eq 'Antibody') {            $matches = $userValue; }	# antibody name is the ID
  elsif ($ontology_type eq 'Molecule') {        ($matches, $fieldIdToValue_ref) = &getAnyMoleculeIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'Transgene') {       ($matches, $fieldIdToValue_ref) = &getAnyTransgeneIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBGene') {          ($matches, $fieldIdToValue_ref) = &getAnyWBGeneIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBInteraction') {    $matches = $userValue; }	# interaction name is the ID
  elsif ($ontology_type eq 'WBPaper') {          $matches = $userValue; }	# paper name is the ID
  elsif ($ontology_type eq 'WBPerson') {        ($matches, $fieldIdToValue_ref) = &getAnyWBPersonIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  elsif ($ontology_type eq 'WBPicture') {       ($matches, $fieldIdToValue_ref) = &getAnyWBPictureIdToValue($ontology_type, $type, $fieldIdToValue_ref, $userValue); }
  return ($matches, $fieldIdToValue_ref);
} # sub getAnySpecificIdToValue

sub getAnyMoleculeIdToValue {			# molecule object names (not publicname)
  my ($ontology_type, $type, $fieldIdToValue_ref, $userValue) = @_;
  my %fieldIdToValue = %$fieldIdToValue_ref;
  $userValue =~ s/\"//g;			# strip doublequotes
  my (@data) = split/,/, $userValue; my %results;
  foreach my $id (@data) {
    my $joinkey = $id;
    if ($fieldIdToValue{$ontology_type}{$joinkey}) { $results{$joinkey} = $fieldIdToValue{$ontology_type}{$joinkey}; }
    else {
      my $table =  'mop_molecule';
      my $result = $dbh->prepare( "SELECT * FROM $table WHERE joinkey = '$joinkey' ;" );
      $result->execute(); my @row = $result->fetchrow();
      if ($row[1]) { $fieldIdToValue{$ontology_type}{$joinkey} = "\"$row[1]<span style='display: none'>$id</span>\""; 
                     $results{$joinkey} = "\"$row[1]<span style='display: none'>$id</span>\""; } } }
  my $data = join",", sort values %results;
  if ( $type eq 'ontology' ) { $data =~ s/^\"//; $data =~ s/\"$//; }	# strip quotes for ontology, keep for multiontology
  return ($data, \%fieldIdToValue);
} # sub getAnyMoleculeIdToValue
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
sub getAnyWBPictureIdToValue {			# molecule object names (not publicname)
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
  $curator_list{"two1823"} = 'Juancarlos Chan';
  $curator_list{"two101"} = 'Wen Chen';
  $curator_list{"two1983"} = 'Paul Davis';
  $curator_list{"two9133"} = 'Margaret Duesbury';
  $curator_list{"two8679"} = 'Ruihua Fang';
  $curator_list{"two2021"} = 'Jolene S. Fernandes';
  $curator_list{"two13088"} = 'Uhma Ganesan';
  $curator_list{"two2987"} = 'Chris';
  $curator_list{"two12884"} = 'Snehalata Kadam';
  $curator_list{"two324"} = 'Ranjana Kishore';
  $curator_list{"two363"} = 'Raymond Lee';
  $curator_list{"two1"} = 'Cecilia Nakamura';
  $curator_list{"two480"} = 'Tuco';
  $curator_list{"two12028"} = 'Daniela Raciti';
  $curator_list{"two1847"} = 'Anthony Rogers';
  $curator_list{"two557"} = 'Gary C. Schindelman';
  $curator_list{"two567"} = 'Erich Schwarz';
  $curator_list{"two625"} = 'Paul Sternberg';
  $curator_list{"two627"} = 'Theresa Stiernagle';
  $curator_list{"two2970"} = 'Mary Ann Tuli';
  $curator_list{"two1843"} = 'Kimberly Van Auken';
  $curator_list{"two736"} = 'Qinghua Wang';
  $curator_list{"two1760"} = 'Xiaodong Wang';
  $curator_list{"two712"} = 'Karen Yook'; 

  print "<table cellpadding=\"4\">\n";
  print "<tr>\n";
  print "<td valign=\"top\">Name<br /><select name=\"curator_two\" size=" , scalar keys %curator_list , ">\n";
  foreach my $curator_two (keys %curator_list) {	# display curators in alphabetical (tied hash) order, if IP matches existing ip record, select it
    if ($curator_by_ip eq $curator_two) { print "<option value=\"$curator_two\" selected=\"selected\">$curator_list{$curator_two}</option>\n"; }
    else { print "<option value=\"$curator_two\">$curator_list{$curator_two}</option>\n"; } }
  print "</select></td>\n";
  print "<td valign=\"top\">Data Type<br /><select name=\"datatype\" size=\"10\">\n";
  print "<option value=\"abp\">antibody</option>\n";
  print "<option value=\"exp\">exprpat</option>\n";
  print "<option value=\"gcl\">gene class</option>\n";
  print "<option value=\"gop\">go</option>\n";
  print "<option value=\"grg\">genereg</option>\n";
  print "<option value=\"int\">interaction</option>\n";
  print "<option value=\"mop\">molecule</option>\n";
#   print "<option value=\"two\">people</option>\n";
  print "<option value=\"app\">phenotype</option>\n";
  print "<option value=\"pic\">picture</option>\n";
  print "<option value=\"trp\">transgene</option>\n";
  print "</select></td>\n";
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

=item * noteditable	OPTIONAL	flag.  Field can't be edited (affects ontology_annotator.js only).  Values in bigtext field will toggle into the input field, so the editor will change, but values will not update in the datatable, nor change in postgres.

=item * input_size	OPTIONAL	integer.  Html input tag has this size on editor.

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




