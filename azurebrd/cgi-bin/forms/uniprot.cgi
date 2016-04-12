#!/usr/bin/perl

# Display of curated data with PMIDs for UniProt

# For Raja Mazumder (rm285@georgetown.edu)  2009 05 29
#
# Now only output WBGene \t WBPaper \t PMID  2009 06 02
#
# Changed to pap tables, even though they're not live.  2010 06 22






use Jex;			# untaint, getHtmlVar, cshlNew, mailer
use strict;
use CGI;
use DBI;

use Tie::IxHash;
use LWP::Simple;
# use Ace;

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 


my $blue = '#00ffcc';                   # redefine blue to a mom-friendly color
my $red = '#00ffff';                    # redefine red to a mom-friendly color


my $query = new CGI;

my %hash;				# names of fields
my @pgTables;				# names of tables
my %theHash;				# curated data in fields
my %papHash;				# pap data 
my %papGene;				# paper -> gene

my $title = 'Unitprot Paper Curation Display';
my ($header, $footer) = &cshlNew($title);

print "Content-type: text/plain\n\n";
&hashName();

# foreach my $name (@pgTables) {
# #   print "$hash{name}{$name}<br />\n";
#   my $result = $dbh->prepare( "SELECT * FROM cfp_$name" );
#   $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
#   while (my @row = $result->fetchrow) { $theHash{$row[0]}{$name}++; } # mark the paper / type as having data
# } # foreach my $name (@pgTables) 

my $result = $dbh->prepare( "SELECT * FROM pap_identifier WHERE pap_identifier ~ 'pmid' ORDER BY pap_timestamp" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) { $papHash{pmid}{$row[0]}{$row[1]}++; }

$result = $dbh->prepare( "SELECT * FROM pap_status WHERE pap_status = 'valid' ORDER BY pap_timestamp" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) { $papHash{pap}{$row[0]}++; }

$result = $dbh->prepare( "SELECT * FROM pap_gene ORDER BY pap_timestamp" );
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
while (my @row = $result->fetchrow) { 
#   my ($gene) = $row[1] =~ m/(WBGene\d+)/;
  my $gene = 'WBGene' . $row[1];
  $papGene{$row[0]}{$gene}++; }

# print "UniProt\tPMID\tWBPaperID\tCurated_Data\n";
print "WBGene\tWBPaperID\tPMID\n";
foreach my $joinkey (sort keys %{ $papHash{pap} }) {
  next if ($joinkey eq '00000001');
  next if ($joinkey eq '00000003');
  my $uniprot = '';
  my $pmid = '';
  my $curated = '';
  if ($papHash{pmid}{$joinkey}) {
    foreach my $id (sort keys %{ $papHash{pmid}{$joinkey} }) { 
      if ($pmid) { $pmid .= ", $id"; } else { $pmid = $id; } } }
  foreach my $name (sort keys %{ $hash{name} }) {
    if ($theHash{$joinkey}{$name}) { if ($curated) { $curated .= ", $hash{name}{$name}"; } else { $curated = $hash{name}{$name}; } } }
#   print "$uniprot\tWBPaper$joinkey\t$pmid\t$curated\n";
  foreach my $wbgene (sort keys %{ $papGene{$joinkey} }) {
    print "$wbgene\tWBPaper$joinkey\t$pmid\n";
  } # foreach my $wbgene (sort keys %{ $papGene{$joinkey} })
} # foreach my $joinkey (sort keys %{ $papHash{pap} })



sub hashName {
  $hash{name}{spe} = 'Species';
  $hash{name}{celegans}    = '<i>C. elegans</i>.';
  $hash{exmp}{celegans}    = 'Please uncheck if you are not reporting data for <i>C. elegans</i>.';
#   $hash{mail}{celegans}    = 'azurebrd@tazendra.caltech.edu';
  $hash{name}{cnonbristol} = '<i>C. elegans</i> other than N2 (Bristol).';
  $hash{exmp}{cnonbristol} = 'Please indicate if data for <i>C. elegans</i> isolates other than N2 (Bristol) are presented in this paper.';
  $hash{name}{nematode}    = 'Nematode species other than <i>C. elegans</i>.';
  $hash{exmp}{nematode}    = 'Please indicate if data is presented for any species other than <i>C. elegans</i>, e.g., <i>C. briggsae, Pristionchus pacificus, Brugia malayi,</i> etc.';
  $hash{name}{nonnematode} = 'Non-nematode species.';
  $hash{exmp}{nonnematode} = 'Please indicate if data is presented for any non-nematode species.';

  $hash{name}{gif} = 'Gene Identification and Mapping';
  $hash{name}{genestudied}  = 'Genes studied in this paper.';
  $hash{name2}{genestudied} = 'Relevant Genes.  Please list genes studied in the paper.  Exclude common markers and reporters.';
  $hash{exmp}{genestudied}  = 'Please use text box below to list any genes that were a focus of analysis in this research article.';
#   $hash{name}{genesymbol} = 'Newly cloned Novel Gene Symbol or Gene-CDS link.  E.g., xyz-1 gene was cloned and it turned out to be the same as abc-1 gene.';
  $hash{name}{genesymbol}   = 'Newly cloned gene.';
  $hash{exmp}{genesymbol}   = 'Please indicate if your paper reports a new symbol for a known locus or the name of a newly defined locus.';
  $hash{mail}{genesymbol}   = 'genenames@wormbase.org, vanauken@its.caltech.edu';
  $hash{name}{extvariation} = 'Newly created alleles.';
  $hash{exmp}{extvariation} = 'Please indicate if your paper reports the identification of any allele that doesn\'t exist in WormBase already.';
  $hash{name}{mappingdata}  = 'Genetic mapping data.';
  $hash{exmp}{mappingdata}  = 'Please indicate if your paper contains 3-factor interval mapping data, i.e., genetic data only.  Include Df or Dp data, but no SNP interval mapping.';
  $hash{mail}{mappingdata} = 'genenames@wormbase.org';

  $hash{name}{gfp} = 'Gene Function';
  $hash{name}{phenanalysis} = 'Mutant, RNAi, Overexpression, or Chemical-based Phenotypes.';
  $hash{name}{newmutant}    = 'Allele phenotype analysis.';
  $hash{exmp}{newmutant}    = 'Please indicate if your paper reports any phenotype for a mutant.';
  $hash{mail}{newmutant}    = 'emsch@its.caltech.edu, garys@its.caltech.edu, jolenef@its.caltech.edu';
  $hash{name}{rnai}   = 'Small-scale RNAi (less than 100 individual experiments).';
  $hash{exmp}{rnai}   = 'Please indicate if your paper reports gene knockdown phenotypes for less than 100 individual RNAi experiments.';
  $hash{mail}{rnai}   = 'garys@its.caltech.edu';
  $hash{name}{lsrnai} = 'Large-scale RNAi (greater than 100 individual experiments).';
  $hash{exmp}{lsrnai} = 'Please indicate if your paper reports gene knockdown phenotypes for more than 100 individual RNAi experiments.';
  $hash{mail}{lsrnai} = 'raymond@its.caltech.edu';
  $hash{name}{overexpr} = 'Overexpression phenotype.';
  $hash{exmp}{overexpr} = 'Please indicate if your paper reports an abnormal phenotype based on the overexpression of a gene or gene construct. E.g., \"...constitutively activated SCD-2(neu*) receptor caused 100% of animals to arrest in the first larval stage (L1)...\"';
  $hash{mail}{overexpr} = 'emsch@its.caltech.edu, garys@its.caltech.edu, jolenef@its.caltech.edu';
  $hash{name}{chemicals} = 'Chemicals.';
  $hash{exmp}{chemicals} = 'Please indicate if the effects of small molecules, chemicals, or drugs were studied on worms, e.g., paraquat, butanone, benzaldehyde, aldicarb, etc. Mutagens used for the generation of mutants in genetic screens do not need to be indicated.';
  $hash{name}{mosaic} = 'Mosaic analysis.';
  $hash{exmp}{mosaic} = 'Please indicate if your paper reports cell specific gene function based on mosaic analysis, e.g. extra-chromosomal transgene loss in a particular cell lineage leads to loss of mutant rescue, etc.';
  $hash{mail}{mosaic} = 'raymond@its.caltech.edu';
  $hash{name}{siteaction} = 'Tissue or cell site of action.';
  $hash{exmp}{siteaction} = 'Please indicate if your paper reports anatomy (tissue or cell)-specific expression function for a gene.';
  $hash{mail}{siteaction} = 'raymond@its.caltech.edu';
  $hash{name}{timeaction} = 'Time of action.';
  $hash{exmp}{timeaction} = 'Please indicate if your paper reports a temporal requirement for gene function.';
  $hash{mail}{timeaction} = 'raymond@its.caltech.edu';
  $hash{name}{genefunc} = 'Molecular function of a gene product.';
  $hash{exmp}{genefunc} = 'Please indicate if your paper discusses a new function for a known or newly defined gene.';
  $hash{mail}{genefunc} = 'emsch@its.caltech.edu';
  $hash{name}{humdis} = 'Homolog of a human disease-associated gene.';
  $hash{exmp}{humdis} = 'Please indicate if genes discussed in your paper are a homolog/ortholog of a human disease-related gene.';
  $hash{mail}{humdis} = 'ranjana@its.caltech.edu';

  $hash{name}{int} = 'Interactions';
  $hash{name}{geneint} = 'Genetic interactions.';
  $hash{exmp}{geneint} = 'Please indicate if your paper reports the analysis of more than one gene at a time, e.g., double, triple, etc. mutants, including experiments where RNAi was concurrent with other RNAi-treatments or mutations.';
  $hash{mail}{geneint} = 'emsch@its.caltech.edu';
  $hash{name}{funccomp} = 'Functional complementation.';
  $hash{exmp}{funccomp} = 'Please indicate if your paper reports functional redundancy between separate genes, e.g., the rescue of <i>gen-A</i>, by overexpression of <i>gen-B</i> or any other extragenic sequence.';
  $hash{name}{geneprod} = 'Gene product interaction.';
  $hash{exmp}{geneprod} = 'Please indicate if your paper reports data on protein-protein, RNA-protein, DNA-protein, or Y2H interactions, etc.';
  $hash{mail}{geneprod} = 'emsch@its.caltech.edu';

  $hash{name}{gef} = 'Regulation of Gene Expression';
  $hash{name}{otherexpr} = 'New expression pattern for a gene.';
  $hash{exmp}{otherexpr} = 'Please indicate if your paper reports new temporal or spatial (e.g. tissue, subcellular, etc.) data on the pattern of expression of any gene in a wild-type background. You can include: reporter gene analysis, antibody staining, <i>In situ</i> hybridization, RT-PCR, Western or Northern blot data.';
  $hash{mail}{otherexpr} = 'wchen@its.caltech.edu, vanauken@its.caltech.edu';
  $hash{name}{microarray} = 'Microarray.';
  $hash{exmp}{microarray} = 'Please indicate if your paper reports any microarray data.';
  $hash{mail}{microarray} = 'wchen@its.caltech.edu';
  $hash{name}{genereg} = 'Alterations in gene expression by genetic or other treatment.';
  $hash{exmp}{genereg} = 'Please indicate if your paper reports changes or lack of changes in gene expression levels or patterns due to genetic background, exposure to chemicals or temperature, or any other experimental treatment.';
  $hash{mail}{genereg} = 'xdwang@its.caltech.edu';
  $hash{name}{seqfeat} = 'Regulatory sequence features.';
  $hash{exmp}{seqfeat} = 'Please indicate if your paper reports any gene expression regulatory elements, e.g., DNA/RNA elements required for gene expression, promoters, introns, UTR\'s, DNA binding sites, etc.';
  $hash{mail}{seqfeat} = 'xdwang@its.caltech.edu, worm-bug@sanger.ac.uk, stlouis@wormbase.org';
  $hash{name}{matrices} = 'Position frequency matrix (PFM) or position weight matrix (PWM).';
  $hash{exmp}{matrices} = 'Please indicate if your paper reports PFMs or PWMs, which are typically used to define regulatory sites in genomic DNA (e.g., bound by transcription factors) or mRNA (e.g., bound by translational factors or miRNA). PFMs define simple nucleotide frequencies, while PWMs are scaled logarithmically against a background frequency.';
  $hash{mail}{matrices} = 'xdwang@its.caltech.edu, emsch@its.caltech.edu';

  $hash{name}{rgn} = 'Reagents.';
  $hash{name}{antibody} = '<i>C. elegans</i> antibodies.';
  $hash{exmp}{antibody} = 'Please indicate if your paper reports the use of new or known antibodies created by your lab or someone else\'s lab; do not check this box if antibodies were commercially bought.';
  $hash{mail}{antibody} = 'wchen@its.caltech.edu';
  $hash{name}{transgene} = 'Integrated transgene.';
  $hash{exmp}{transgene} = 'Please indicate if integrated transgenes were used in this paper. If the transgene does not have a canonical name, please list it in the "Add Information" text box.';
  $hash{mail}{transgene} = 'wchen@its.caltech.edu';
  $hash{name}{marker} = 'Transgenes used as tissue markers.';
  $hash{exmp}{marker} = 'Please indicate if reporters (integrated transgenes) were used to mark certain tissues, subcellular structures, or life stages, etc. as a reference point to assay gene function or location.';
  $hash{mail}{transgene} = 'wchen@its.caltech.edu, vanauken@its.caltech.edu';

  $hash{name}{pfs} = 'Protein Function and Structure';
  $hash{name}{invitro} = 'Protein analysis <i>in vitro</i>.';
  $hash{exmp}{invitro} = 'Please indicate if your paper reports any <i>in vitro</i> protein analysis such as kinase assays, agonist pharmacological studies, <i>in vitro</i> reconstitution studies, etc.';
  $hash{name}{domanal} = 'Analysis of protein domains.';
  $hash{exmp}{domanal} = 'Please indicate if your paper reports on a function of a particular domain within a protein.';
  $hash{name}{covalent} = 'Covalent modification.';
  $hash{exmp}{covalent} = 'Please indicate if your paper reports on post-translational modifications as assayed by mutagenesis or in vitro analysis.';
  $hash{name}{structinfo} = 'Structural information.';
  $hash{exmp}{structinfo} = 'Please indicate if your paper reports NMR or X-ray crystallographic information.';
#   $hash{mail}{structinfo} = 'worm-bug@sanger.ac.uk, wormticket@watson.wustl.edu';	# no email  2009 05 26
  $hash{name}{massspec} = 'Mass spectrometry.';
  $hash{exmp}{massspec} = 'Please indicate if your paper reports data from any mass spec analysis e.g., LCMS, COSY, HRMS, etc.';
  $hash{mail}{massspec} = 'gw3@sanger.ac.uk, worm-bug@sanger.ac.uk';
  
  $hash{name}{seq} = 'Genome Sequence Data';
  $hash{name}{structcorr} = 'Gene structure correction.';
  $hash{exmp}{structcorr} = 'Please indicate if your paper reports a gene structure that is different from the one in WormBase, e.g., different splice-site, SL1 instead of SL2, etc.';
  $hash{mail}{structcorr} = 'wormticket@watson.wustl.edu, worm-bug@sanger.ac.uk';
  $hash{name}{seqchange} = 'Sequencing mutant alleles.';
  $hash{exmp}{seqchange} = 'Please indicate if your paper reports new sequence data for any mutation.';
  $hash{mail}{seqchange} = 'genenames@wormbase.org';
  $hash{name}{newsnp} = 'New SNPs, not already in WormBase.';
  $hash{exmp}{newsnp} = 'Please indicate if your paper reports a SNP that does not already exist in WormBase.';
  $hash{mail}{newsnp} = 'dblasiar@watson.wustl.edu, tbieri@watson.wustl.edu';
  
  $hash{name}{cell} = 'Cell Data';
  $hash{name}{ablationdata} = 'Ablation data.';
  $hash{exmp}{ablationdata} = 'Please indicate if your paper reports data from an assay involving any cell or anatomical unit being ablated by laser or by other means (e.g. by expressing a cell-toxic protein).';
  $hash{mail}{ablationdata} = 'raymond@its.caltech.edu';
  $hash{name}{cellfunc} = 'Cell function.';
  $hash{exmp}{cellfunc} = 'Please indicate if your paper reports a function for any anatomical part (e.g., cell, tissue, etc.), which has not been indicated elsewhere on this form.';
  $hash{mail}{cellfunc} = 'raymond@its.caltech.edu';

  $hash{name}{sil} = 'In Silico Data';
  $hash{name}{phylogenetic} = 'Phylogenetic analysis.';
  $hash{exmp}{phylogenetic} = 'Please indicate if your paper reports any phylogenetic analysis.';
  $hash{name}{othersilico}  = 'Other bioinformatics analysis.';
  $hash{exmp}{othersilico}  = 'Please indicate if your paper reports any bioinformatic data not indicated anywhere else on this form.';

#   $hash{name}{rgn} = 'Reagents.';

  $hash{name}{oth} = 'Other';
  $hash{name}{supplemental} = 'Supplemental materials.';
  $hash{exmp}{supplemental} = 'Please indicate if your paper has supplemental material.';
  $hash{mail}{supplemental} = 'qwang@its.caltech.edu';
  $hash{name}{nocuratable}  = 'NONE of the aforementioned data types are in this research article.';
  $hash{exmp}{nocuratable}  = 'Please indicate if none of the above pertains to your paper. Feel free to list the data type most pertinent to your research paper in the "Add information" text area.';
  $hash{name}{comment} = 'Comment.';
  $hash{exmp}{comment} = 'Please feel free to give us feedback for this form or for any other topic pertinent to how we can better extract data from your paper.';
  $hash{mail}{comment} = 'kyook@its.caltech.edu, vanauken@its.caltech.edu';

my @cats = qw( spe gif gfp int gef rgn pfs seq cell sil oth );
my @spe = qw( celegans cnonbristol nematode nonnematode );
# my @gif = qw( genestudied genesymbol extvariation mappingdata );	# extvariation removed 2009 05 14
my @gif = qw( genestudied genesymbol mappingdata );
my @gfp = qw( newmutant rnai lsrnai overexpr chemicals mosaic siteaction timeaction genefunc humdis );
# my @phenanalysis = qw( newmutant rnai lsrnai overexpr chemicals );
my @int = qw( geneint funccomp geneprod );
my @gef = qw( otherexpr microarray genereg seqfeat matrices );
# my @rgn = qw( antibody transgene marker );				# antibody and transgene removed 2009 05 14
my @rgn = qw( marker );
my @pfs = qw( invitro domanal covalent structinfo massspec );
my @seq = qw( structcorr seqchange newsnp );
my @cell = qw( ablationdata cellfunc );
my @sil = qw( phylogenetic othersilico );
my @oth = qw( supplemental nocuratable comment );
$hash{cat}{spe} = [ @spe ];
$hash{cat}{gif} = [ @gif ];
$hash{cat}{gfp} = [ @gfp ];
# $hash{cat}{phenanalysis} = [ @phenanalysis ];
$hash{cat}{int} = [ @int ];
$hash{cat}{gef} = [ @gef ];
$hash{cat}{rgn} = [ @rgn ];
$hash{cat}{pfs} = [ @pfs ];
$hash{cat}{seq} = [ @seq ];
$hash{cat}{cell} = [ @cell ];
$hash{cat}{sil} = [ @sil ];
$hash{cat}{oth} = [ @oth ];

  foreach my $cat (@cats) {
    foreach my $table (@{ $hash{cat}{$cat} }) {
      if ($hash{cat}{$table}) {
        foreach my $subcat ( @{ $hash{cat}{$table} } ) { push @pgTables, $subcat; } }
      else { push @pgTables, $table; } } }
} # sub hashName


