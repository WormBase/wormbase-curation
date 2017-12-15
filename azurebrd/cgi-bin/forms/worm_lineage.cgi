#!/usr/bin/perl 

# Display of Intellectual Lineage information.


use strict;
use diagnostics;
use LWP::Simple;
use JSON;

# use Mail::Mailer;

# my ($header, $footer) = &cshlNew();

use Jex;			# untaint, getHtmlVar, cshlNew
use CGI;
use Fcntl;
use DBI;
    use Clone 'clone';

my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb", "", "") or die "Cannot connect to database!\n"; 
my $result;


my $query       = new CGI;
my $json        = JSON->new->allow_nonref;
my $jsonUrl     = 'http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/wbpersonLineageScaling.json';
my $page        = get $jsonUrl;
my $perl_scalar = $json->decode( $page );         # get the solr data
my %scaling     = %$perl_scalar;                     # decode the solr page into a hash



my $action;			# what user clicked
unless ($action = $query->param('action')) { $action = 'none'; }

my $twonumber = 'all';
my %relationship; my %twos; my %standardname;
my %children; my %parents; my %sideRelations;
# my %scaling; 
# $action = 'lineage';
if ($action eq 'lineage') {
  my ($var, $twonum)        = &getHtmlVar($query, 'twonumber');
  ($var, my $displayOption) = &getHtmlVar($query, 'displayOption');
#   my $layoutName            = 'breadthfirst';
  my $recurseAncestry       = 1;
#   if ($displayOption eq 'direct') {    $layoutName = 'cose';         $recurseAncestry = 0; }
#     elsif ($displayOption eq 'full') { $layoutName = 'breadthfirst'; $recurseAncestry = 1; }
  if ($twonum) {
      my %nodes;
      my %edges;
#       $result = $dbh->prepare( "SELECT * FROM two_lineage WHERE (two_role = 'Phd' OR two_role = 'Postdoc' OR two_role = 'Undergrad' OR two_role = 'Masters' OR two_role = 'Research_staff' OR two_role = 'Lab_visitor' OR two_role = 'Highschool' OR two_role = 'Assistant_professor' OR two_role = 'Undergrad' ) AND joinkey ~ 'two' AND two_number ~ 'two'" );
      $result = $dbh->prepare( "SELECT * FROM two_lineage WHERE (two_role = 'Phd' OR two_role = 'Postdoc' OR two_role = 'Undergrad' OR two_role = 'Masters' OR two_role = 'Research_staff' OR two_role = 'Highschool' OR two_role = 'Undergrad' ) AND joinkey ~ 'two' AND two_number ~ 'two'" );
      $result->execute() or die "Cannot prepare statement: $DBI::errstr\n";
      while (my @row = $result->fetchrow) {
        my ($joinkey, $two_sentname, $two_othername, $two_number, $role, @other) = @row;
        $two_sentname =~ s/\'//g;
        $two_othername =~ s/\'//g;
# next unless ($row[0] =~ m/two2/);
        if ($row[0] =~ m/twotwo/) { $row[0] =~ s/twotwo/two/; }
        if ($row[3] =~ m/twotwo/) { $row[3] =~ s/twotwo/two/; }
#         $twos{'Full'}{$row[0]}++;
#         $twos{'Full'}{$row[3]}++;
#         $twos{'Direct'}{$row[0]}++;
#         $twos{'Direct'}{$row[3]}++;
        my ($parent, $child) = ($joinkey, $two_number);
        if ($role =~ m/with/) { $role =~ s/with//; ($child, $parent) = ($joinkey, $two_number); }
        $children{'Full'}{$parent}{$child}{$role}++; 
        $children{'Direct'}{$parent}{$child}{$role}++; 
        $parents{'Full'}{$child}{$parent}{$role}++; 	# store parents and children for individuals's graph
        $parents{'Direct'}{$child}{$parent}{$role}++; 	# store parents and children for individuals's graph
#         next if ($relationship{$child}{$parent}{$role});                # skip if exists backwards
#         if ($role eq 'Collaborated') { 
#             if ($parent eq $twonum) {     $sideRelations{$parent}{$child}{$role}++; }
#               elsif ($child eq $twonum) { $sideRelations{$child}{$parent}{$role}++; } }
#           else {
#             $relationship{$parent}{$child}{$role}++; 		# if showing full graph, %relationship has all edges
#             $children{'Full'}{$parent}{$child}{$role}++; 
#             $children{'Direct'}{$parent}{$child}{$role}++; 
#             $parents{'Full'}{$child}{$parent}{$role}++; 	# store parents and children for individuals's graph
#             $parents{'Direct'}{$child}{$parent}{$role}++; 	# store parents and children for individuals's graph
#           }
        $nodes{$parent}++; $nodes{$child}++;
      }
# generate this once, then download from .json
#       foreach my $node (sort keys %nodes) { $scaling{$node}++; }
#       my %hasChild;
# # print qq(BLA1\n);
#       foreach my $role (sort keys %edges) {
# next unless ( ($role eq 'Phd') || ($role eq 'Postdoc') || ($role eq 'Undergrad') || ($role eq 'Masters') );
#         while (scalar keys %{ $edges{$role} } > 0) {
# # print qq(WHILE $role\n);
#           foreach my $one (sort keys %{ $edges{$role} }) {
# # print qq(WHILE $role O $one\n);
#             foreach my $two (sort keys %{ $edges{$role}{$one} }) {
# # print qq(WHILE $role O $one T $two\n);
#               unless (scalar keys %{ $edges{$role}{$two}} > 0) {
# #                 if ( ($role eq 'Phd') || ($role eq 'Postdoc') || ($role eq 'Undergrad') || ($role eq 'Masters') ) {
# #                   if ($scaling{$two}) { $scaling{$one} += $scaling{$two}; }
# #                     else { $scaling{$one}++; }
# #                 }
#                 if ($scaling{$two}) { $scaling{$one} += $scaling{$two}; }
#                   else { $scaling{$one}++; }
#                 delete $edges{$role}{$one}{$two};
# # print qq(DELETE $role O $one T $two E\n);
#                 delete $edges{$role}{$two};
# # print qq(DELETE $role T $two E\n);
#                 unless (scalar keys %{ $edges{$role}{$one}} > 0) { delete $edges{$role}{$one}; 
# # print qq(DELETE $role O $one E\n);
# }
# # print qq(R $role O $one T $two E\n);
#               }
#             } # foreach my $two (sort keys %{ $edges{$one} })
#           } # foreach my $one (sort keys %edges)
#         } # while (scalar keys %edges > 0)
#       } # foreach my $role (sort keys %edges)
# # print qq(BLA3\n);
# #       foreach my $node (sort keys %scaling) { print qq($node\t$scaling{$node}\n); } 
    if ($twonum =~ m/two\d+/) {
      %relationship = ();
      %twos = (); $twos{'Direct'}{$twonum}++; $twos{'Full'}{$twonum}++;
#       foreach my $sideRelation (sort keys %{ $sideRelations{$twonum} }) {
#         $twos{$sideRelation}++;
#         foreach my $role (sort keys %{ $sideRelations{$twonum}{$sideRelation} }) {
#           $relationship{$twonum}{$sideRelation}{$role}++; } }
#       &addChildren($twonum, $recurseAncestry);
#       &addParents($twonum, $recurseAncestry);
      &addChildren($twonum, 'Full');
      &addParents($twonum, 'Full');
      &addChildren($twonum, 'Direct');
      &addParents($twonum, 'Direct');
    }

    my $twos = join"','", sort keys %{ $twos{'Full'} };
    $result = $dbh->prepare( "SELECT * FROM two_standardname WHERE joinkey IN ('$twos');" );
    $result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
    while (my @row = $result->fetchrow) { $row[2] =~ s/\'//g; $standardname{$row[0]} = $row[2]; }

    my @colours = ("#0A6314", "#08298A","#B40431","#FF8000", "#00E300","#05C1F0", "#8000FF", "#69088A", "#B58904", "#E02D8A", "#FFFC2E");
    my %roleColour;
    $roleColour{'Phd'}                 = '#B40431';
    $roleColour{'Postdoc'}             = '#00E300';
    $roleColour{'Undergrad'}           = '#00E300';
    $roleColour{'Masters'}             = '#FF8000';
    $roleColour{'Research_staff'}      = '#08298A';
    $roleColour{'Highschool'}          = '#05C1F0';
    $roleColour{'Undergrad'}           = '#B58904';

    my @graphTypes = qw( Direct Full );
    my $code_js = '';
    my %layoutName;
    $layoutName{'Direct'} = 'cose';
    $layoutName{'Full'}   = 'breadthfirst';
    my %elements;
    my %existingRoles;
    foreach my $graphType (@graphTypes) {
      my @nodes; my @edges;
      my $largestScaling = 0;
      foreach my $two (sort keys %{ $twos{$graphType} }) {
        my $wbperson = $two; $wbperson =~ s/two/WBPerson/g;
        unless ($scaling{$wbperson}) { $scaling{$wbperson} = 1; }
        if ($scaling{$wbperson} > $largestScaling) { $largestScaling = $scaling{$wbperson}; } }
      if ($largestScaling == 1) { $largestScaling = 2; }
      foreach my $two (sort keys %{ $twos{$graphType} }) {
        my $wbperson = $two; $wbperson =~ s/two/WBPerson/g;
        my $radius = 25 + log($scaling{$wbperson})/log($largestScaling) * 50;
        my $nodeshape = 'ellipse'; if ($two eq $twonum) { $nodeshape = 'rectangle'; $radius = 100; }
          # ids must have graphType in them, otherwise they're the same nodes in both graphs, and hiding in one will hide in both
        push @nodes, qq({ data: { id: '${graphType}$two', name: '$standardname{$two}', url: 'http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/worm_lineage.cgi?action=lineage&twonumber=$two', radius: '$radius', nodeshape: '$nodeshape', blah: '$two', bleh: '$twonumber' } }); 
      }
      foreach my $source (sort keys %{ $relationship{$graphType} }) {
        foreach my $target (sort keys %{ $relationship{$graphType}{$source} }) { 
          foreach my $role (sort keys %{ $relationship{$graphType}{$source}{$target} }) { 
            my $lineStyle = 'solid'; if ($target eq $twonum) { if ($graphType eq 'Direct') { $lineStyle = 'dashed'; } }
            my $targetArrowShape = 'triangle'; 
            my $colour = '#ccc';
            $colour = $roleColour{$role};
#             if ($role eq 'Phd')            { $colour = 'blue';  }
#             if ($role eq 'Postdoc')        { $colour = 'green'; }
#             if ($role eq 'Masters')        { $colour = 'cyan';  }
#             if ($role eq 'Collaborated')   { $colour = 'yellow';  $targetArrowShape = 'none'; }
#             if ($role eq 'Undergrad')      { $colour = 'red';  }
#             if ($role eq 'Research_staff') { $colour = 'orange';  }
            $existingRoles{$graphType}{$role} = $colour;
#             push @edges, qq({ data: { source: '$source', target: '$target', label: '$role', role: '$role', targetArrowShape: '$targetArrowShape', lineStyle: '$lineStyle', lineColor: '$colour' } });  	# if wanting labels
            push @edges, qq({ data: { source: '${graphType}$source', target: '${graphType}$target', role: '$role', targetArrowShape: '$targetArrowShape', lineStyle: '$lineStyle', lineColor: '$colour' } });  
      } } }
      my $nodes    = join",\n", @nodes; 
      my $edges    = join",\n", @edges; 
      $elements{$graphType} = qq({\n  nodes: [\n$nodes\n], edges: [\n$edges\n] });
    } # foreach my $graphType (@graphTypes)

$code_js .= << "EndOfText";
var jsonExportSaveDirect = '';
var jsonExportSaveFull   = '';
var elementsDirect = $elements{'Direct'};
var elementsFull   = $elements{'Full'};
document.addEventListener('DOMContentLoaded', function(){ // on dom ready
EndOfText

#     foreach my $graphType (@graphTypes) {
# #       if ($graphType eq 'Direct') {    $layoutName = 'cose';         }
# #         elsif ($graphType eq 'Full') { $layoutName = 'breadthfirst'; }
# 
# $code_js .= << "EndOfText";
# // document.addEventListener('DOMContentLoaded', function(){ // on dom ready
# 
# var cyPersonLineage${graphType} = cytoscape({
#   container: document.querySelector('#cy${graphType}'),
#     
#   boxSelectionEnabled: false,
#   autounselectify: true,
#   
#   style: cytoscape.stylesheet()
#     .selector('node')
#       .css({
#         'content': 'data(name)',
#         'text-valign': 'center',
#         'color': 'black',
#         'width': 'data(radius)',
#         'height': 'data(radius)',
#         'shape':'data(nodeshape)',
#         'text-outline-width': 2,
#         'background-color': '#bbb',
#         'text-outline-color': '#bbb',
#         'url' : 'data(url)'
#       })
#     .selector('edge')
#       .css({
#         'label': 'data(label)',
#         'curve-style': 'bezier',
#         'line-style': 'data(lineStyle)',
#         'target-arrow-shape': 'data(targetArrowShape)',
#         'target-arrow-color': 'data(lineColor)',
#         'line-color': 'data(lineColor)',
#         'color': 'data(lineColor)',
#         'width': 5
#       })
#     .selector(':selected')
#       .css({
#         'background-color': 'black',
#         'line-color': 'black',
#         'target-arrow-color': 'black',
#         'source-arrow-color': 'black'
#       })
#     .selector('.faded')
#       .css({
#         'opacity': 0.25,
#         'text-opacity': 0
#       }),
#   elements: $elements{$graphType},
#   layout: {
#     name: '$layoutName{$graphType}',
#     directed: true,
#     padding: 10
#   }
# });
# 
# var elements${graphType} = $elements{$graphType};
# 
# var pos = cyPersonLineage${graphType}.nodes("#$twonum").position();
# cyPersonLineage${graphType}.zoom({
#   level: 1,
#   position: pos
# });
# 
# cyPersonLineage${graphType}.on('taphold', 'node', function(e){
#     var url = this.data('url');
#     window.open(url);
# });
# 
# cyPersonLineage${graphType}.on('tap', 'node', function(e){
#   var node = e.cyTarget; 
#   var neighborhood = node.neighborhood().add(node);
#   
#   cyPersonLineage${graphType}.elements().addClass('faded');
#   neighborhood.removeClass('faded');
# });
# 
# cyPersonLineage${graphType}.on('tap', function(e){
#   if( e.cyTarget === cyPersonLineage${graphType} ){
#   var jsonExport = cyPersonLineage${graphType}.json(); 
#   console.log(jsonExport);
#   document.getElementById('jsonTextarea').innerHtml = jsonExport;
#     cyPersonLineage${graphType}.elements().removeClass('faded');
#   }
# });
# 
# var jsonExportSave${graphType} = '';
# document.getElementById('saveJson${graphType}').onclick = function(event) { 
#   jsonExportSave${graphType} = cyPersonLineage${graphType}.json(); 
#   console.log(cyPersonLineage${graphType}.json());
# };
# 
# document.getElementById('loadJson${graphType}').onclick = function(event) { 
#   cyPersonLineage${graphType}.json( jsonExportSave${graphType} ); 
# //   jsonExportSaveString = JSON.stringify(jsonExportSave);
#   console.log('loading ' + jsonExportSave${graphType});
# }
# 
# // }); // on dom ready
# EndOfText
# 
#     } # foreach my $graphType (@graphTypes)

$code_js .= << "EndOfText";
// document.addEventListener('DOMContentLoaded', function(){ // on dom ready	// })

var cyPersonLineageAll = cytoscape({
  container: document.querySelector('#cyAll'),
    
  boxSelectionEnabled: false,
  autounselectify: true,
  
  style: cytoscape.stylesheet()
    .selector('node')
      .css({
        'content': 'data(name)',
        'text-valign': 'center',
        'color': 'black',
        'width': 'data(radius)',
        'height': 'data(radius)',
        'shape':'data(nodeshape)',
        'text-outline-width': 2,
        'background-color': '#bbb',
        'text-outline-color': '#bbb',
        'url' : 'data(url)'
      })
    .selector('edge')
      .css({
        'label': 'data(label)',
        'role': 'data(role)',
        'curve-style': 'bezier',
        'line-style': 'data(lineStyle)',
        'target-arrow-shape': 'data(targetArrowShape)',
        'target-arrow-color': 'data(lineColor)',
        'line-color': 'data(lineColor)',
        'color': 'data(lineColor)',
        'width': 5
      })
    .selector(':selected')
      .css({
        'background-color': 'black',
        'line-color': 'black',
        'target-arrow-color': 'black',
        'source-arrow-color': 'black'
      })
    .selector('.faded')
      .css({
        'opacity': 0.25,
        'text-opacity': 0
      }),
  elements: $elements{'Direct'},
  layout: {
    name: 'cose',
    directed: true,
    padding: 10
  }
});

var pos = cyPersonLineageAll.nodes("#$twonum").position();
cyPersonLineageAll.zoom({
  level: 1,
  position: pos
});

cyPersonLineageAll.on('taphold', 'node', function(e){
//     var url = this.data('url');
//     window.open(url);
});

cyPersonLineageAll.on('mouseover', 'node', function(e){
//     alert("click and hold to go to this person's page");
});

cyPersonLineageAll.on('tap', 'node', function(e){
    var url = this.data('url');
    window.open(url);
  var node = e.cyTarget; 
  var neighborhood = node.neighborhood().add(node);
  cyPersonLineageAll.elements().addClass('faded');
  neighborhood.removeClass('faded');
//     var node = e.cyTarget;
//     node.qtip({
//                  position: {
//                    my: 'top center',
//                    at: 'bottom center'
//                  },
//                  style: {
//                    classes: 'qtip-bootstrap',
//                    tip: {
//                      width: 16,
//                      height: 8
//                    }
//                  },
//          content: "click and hold to open this person's page",
//          show: {
//             e: e.type,
//             ready: true
//          },
//          hide: {
//             e: 'mouseout unfocus'
//          }
//     }, e);
});

cyPersonLineageAll.on('tap', function(e){
  if( e.cyTarget === cyPersonLineageAll ){
    cyPersonLineageAll.elements().removeClass('faded');
  }
});

// document.getElementById('toggleEdges').onclick = function(event) {
//   cyPersonLineageAll.elements('edge').hide();
// };

document.getElementById('toggleToFullView').onclick = function(event) {
  jsonExportSaveDirect = cyPersonLineageAll.json(); 	// save Full view for loading later
  document.getElementById('directViewTable').style.display = 'none';
  document.getElementById('fullViewTable').style.display   = '';
  if (jsonExportSaveFull === '') {			// if there is no previous save for Full, render from elements
      cyPersonLineageAll.json( { elements: elementsFull } );
      cyPersonLineageAll.elements().layout({ name: 'breadthfirst', directed: true, padding: 10  });
    // for some reason needs to happen twice to render properly
      cyPersonLineageAll.json( { elements: elementsFull } );
      cyPersonLineageAll.elements().layout({ name: 'breadthfirst', directed: true, padding: 10  });
      if (elementsFull.nodes.length > 15) {
        var pos = cyPersonLineageAll.nodes("#Full$twonum").position();
        cyPersonLineageAll.zoom({ level: 1, position: pos }); }
    } else {						// if had previously loaded Full, render from saved json
      cyPersonLineageAll.json( jsonExportSaveFull );
  }
};

document.getElementById('toggleToDirectView').onclick = function(event) {
  jsonExportSaveFull = cyPersonLineageAll.json(); 	// save Full view for loading later
  document.getElementById('directViewTable').style.display = '';
  document.getElementById('fullViewTable').style.display   = 'none';
  for (i = 0; i < arrayOfInputs.length; i++) {
    if (arrayOfInputs[i].type == "checkbox") { arrayOfInputs[i].style.display = ''; } }
  cyPersonLineageAll.json( jsonExportSaveDirect );	// render Direct view from saved json
  updateFromCheckboxes();				// when reloading 'Direct', update based on checkboxes, not sure why they become unhidden
};

      document.getElementById('view_png_button').onclick = function(event) {
        var png64 = cyPersonLineageAll.png({ bg: 'white' });
        document.getElementById('png-export').src = png64;
        document.getElementById('png-export').style.display = '';
        document.getElementById('cyAll').style.display = 'none';
        document.getElementById('view_png_div').style.display = 'none';
        document.getElementById('view_edit_div').style.display = '';
//         document.getElementById('info').text('drag image to desktop, or right-click and save image as');
      };
      document.getElementById('view_edit_button').onclick = function(event) {
        document.getElementById('png-export').style.display = 'none';
        document.getElementById('cyAll').style.display = '';
        document.getElementById('view_png_div').style.display = '';
        document.getElementById('view_edit_div').style.display = 'none';
      };

//       \$jq('#view_png_button').on('click', function(){
//         var png64 = cyPersonLineageAll.png({ bg: 'white' });
//         \$jq('#png-export').attr('src', png64);
//         \$jq('#png-export').show();
//         \$jq('#cyAll').hide();
//         \$jq('#view_png_button').hide();
//         \$jq('#view_edit_button').show();
//         \$jq('#info').text('drag image to desktop, or right-click and save image as');
//       });
//       \$jq('#view_edit_button').on('click', function(){
//         \$jq('#png-export').hide();
//         \$jq('#cyAll').show();
//         \$jq('#weightstate').show();
//         \$jq('#view_png_button').show();
//         \$jq('#view_edit_button').hide();
//       });


// document.getElementById('view_png_button').onclick = function(event) {
//   jsonExportSaveFull = cyPersonLineageAll.json(); 	// save Full view for loading later
//   document.getElementById('directViewTable').style.display = '';
//   document.getElementById('fullViewTable').style.display   = 'none';
//   for (i = 0; i < arrayOfInputs.length; i++) {
//     if (arrayOfInputs[i].type == "checkbox") { arrayOfInputs[i].style.display = ''; } }
//   cyPersonLineageAll.json( jsonExportSaveDirect );	// render Direct view from saved json
//   updateFromCheckboxes();				// when reloading 'Direct', update based on checkboxes, not sure why they become unhidden
// };

  var optionsdiv        = document.getElementById('optionsdiv');
  var arrayOfInputs     = optionsdiv.getElementsByTagName("input");
  var arrayOfCheckboxes = [];
  for (i = 0; i < arrayOfInputs.length; i++) {
    if (arrayOfInputs[i].type == "checkbox") {
      arrayOfCheckboxes.push(arrayOfInputs[i]);
      arrayOfInputs[i].onclick = function(event) { updateFromCheckboxes(); }	// when checkbox is clicked, update based on checkboxes
  } }

  function updateFromCheckboxes() {					// update cytoscape graph based on state of checkboxes
//         console.log('updateFromCheckboxes');
        cyPersonLineageAll.elements('edge').hide();			// hide all edges
        var nodeHash = new Object();					// put nodes here that have an edge that shows
        for (j = 0; j < arrayOfCheckboxes.length; j++) {		// for each checkbox
          if (arrayOfCheckboxes[j].checked) { 				// if the checkbox is checked
            var role = arrayOfCheckboxes[j].value;			// get the role
            var arrayEdges = cyPersonLineageAll.elements('edge');	// get the edges in an array
//             console.log(arrayOfCheckboxes[j].value + ' is checked'); 
            for (k = 0; k < arrayEdges.length; k++) { 			// for each edge
              if (arrayEdges[k].data().role == role) {	 		// if the edge has the checked role
                nodeHash[arrayEdges[k].data().source]++			// add the source node to hash of nodes to show
                nodeHash[arrayEdges[k].data().target]++			// add the target node to hash of nodes to show
                arrayEdges[k].show();					// show the edge
            } }
//             cyPersonLineageAll.elements("edge[label=role]").show();	// can't figure out syntax for role to be there as a variable
          }
        }
        cyPersonLineageAll.elements('node').hide();			// hide all nodes
        cyPersonLineageAll.elements('node').filter(function(i, ele){	// filter on nodes
          if (nodeHash.hasOwnProperty(ele.id())) { 			// if the node is is in the hash of nodes to show
            ele.show();							// show the node
          }
        });
  }


//     if (arrayOfInputs[i].checked) { console.log(arrayOfCheckboxes[i].value + ' is checked'); }
//   };
// function updateEdges() {
//   console.log('updateEdges');
// //   cyPersonLineageAll.elements('edge').hide();
// }

}); // on dom ready
EndOfText
    &printStuff($code_js, $twonum, \%existingRoles);

#     foreach my $node (sort keys %scaling) { print qq('$node': '$scaling{$node}',\n); } 
# foreach my $key (sort keys %jsonHash) { 
#   print qq(KEY $key VAL $jsonHash{$key}<br/>\n);
# } # foreach my $key (sort keys %jsonHash) 

  } # if ($twonum)
} # if ($action eq 'lineage')

sub addParents {
  my ($twonum, $fullOrDirect) = @_;
  foreach my $parent (sort keys %{ $parents{$fullOrDirect}{$twonum} }) {
    $twos{$fullOrDirect}{$parent}++;
#     print qq(TWONUM $twonum PARENT $parent END\n); 
    foreach my $role (sort keys %{ $parents{$fullOrDirect}{$twonum}{$parent} }) {
#     print qq(TWONUM $twonum ADDS $role PARENT $parent END\n); 
      delete $parents{$fullOrDirect}{$twonum}{$parent}{$role};			# prevent going through here again if connection exists through other role
      if (scalar keys %{ $parents{$fullOrDirect}{$twonum}{$parent} } == 0) { delete $parents{$fullOrDirect}{$twonum}{$parent}; }
      if (scalar keys %{ $parents{$fullOrDirect}{$twonum} } == 0) { delete $parents{$fullOrDirect}{$twonum}; }
      $relationship{$fullOrDirect}{$parent}{$twonum}{$role}++; }
# uncomment to recurse ancestry
    if ($fullOrDirect eq 'Full') {
      &addParents($parent, $fullOrDirect);
    }
  }
}

sub addChildren {
  my ($twonum, $fullOrDirect) = @_;
  foreach my $child (sort keys %{ $children{$fullOrDirect}{$twonum} }) {
#     print qq(TWONUM $twonum CHILD $child END\n); 
    $twos{$fullOrDirect}{$child}++;
    foreach my $role (sort keys %{ $children{$fullOrDirect}{$twonum}{$child} }) {
#     print qq(TWONUM $twonum ADDS $role CHILD $child END\n); 
      delete $children{$fullOrDirect}{$twonum}{$child};
      $relationship{$fullOrDirect}{$twonum}{$child}{$role}++; }
# uncomment to recurse descendants
    if ($fullOrDirect eq 'Full') {
      &addChildren($child, $fullOrDirect);
    }
  }
}



# recursion failure from Collaboration here
# TWONUM two533 CHILD two1480 END
# TWONUM two533 CHILD two154 END
# TWONUM two533 CHILD two1952 END
# TWONUM two533 CHILD two2126 END
# TWONUM two533 CHILD two2496 END
# TWONUM two533 CHILD two26122 END
# TWONUM two533 CHILD two36 END
# TWONUM two36 CHILD two3392 END
# TWONUM two36 CHILD two3520 END
# TWONUM two36 CHILD two405 END
# TWONUM two36 CHILD two427 END
# TWONUM two36 CHILD two463 END
# TWONUM two36 CHILD two487 END
# TWONUM two36 CHILD two491 END
# TWONUM two36 CHILD two528 END
# TWONUM two36 CHILD two533 END
# TWONUM two533 CHILD two1480 END




sub printStuff {
  my ($code_js, $twonum, $existingRolesHref) = @_;
  my %existingRoles = %$existingRolesHref;
  my $roleRowsDirect = '';
  foreach my $role (sort keys %{ $existingRoles{'Direct'} }) {
     $roleRowsDirect .= qq(<tr><td valign="center"><input type="checkbox" id="edge${role}" value="$role"" checked="checked"><span style="color: $existingRoles{'Direct'}{$role}">$role</span></td></tr>);
  } # foreach my $role (sort keys %{ $existingRoles{'Direct'} })
  my $roleRowsFull = '';
  foreach my $role (sort keys %{ $existingRoles{'Full'} }) {
     $roleRowsFull .= qq(<tr><td valign="center"><span style="color: $existingRoles{'Full'}{$role}">$role</span></td></tr>);
  } # foreach my $role (sort keys %{ $existingRoles{'Full'} })
#   my $helpRow = qq(<tr><td valign="center"><a href="#" onClick="alert('WB Intellectual Lineage Graph:\\n\\nPerson relationships data are separated into two types: Mentor-mentee \(Post-doc, Phd, etc\). Mentor-mentee relationships are considered transitive and used to make inferences such that mentee&#8217;s mentee is one&#8217;s mentee for the purpose of determining the &quot;karma&quot; of a mentor. More karma is indicated by a bigger person node.\\n\\nThe default view is &quot;Intellectual lineage view&quot; in which all direct and inferred mentors and mentees are shown. In the case of larger graphs, it may be desirable to switch to the &quot;Direct relationships view&quot; One can zoom in and out. Click and hold a node will fire up a new graph \(in a new window\) that sets focus to the clicked node. Another way to switch to a specific person is to change the last part of the URL to their person ID.')">help</a></td></tr>);
  
  my $wbperson = $twonum; $wbperson =~ s/two/WBPerson/;
#   my $helpRow = qq(<a href="#" onClick="alert('Intellectual Lineage Graph:\\n\\nWe present two graphs illustrating intellectual mentoring relationships where nodes represent persons and arrows person-to-person relationships.  A Direct View graph \(shown by default\) shows only direct relationships between the focus person and his/her mentors and between the focus person and the persons he/she mentors. Another Full View graph includes all mentoring relationships that center around the focus person.\\n\\nMentoring relationships include studentship of several levels, high school, college, master&#8217;s, and PhD, as well as postdoctoral fellowship, and research staff employment. Mentoring relationships are considered transitive for the purpose of determining the &quot;karma&quot; of a mentor, such that mentee’s mentee is one’s mentee. More mentees means more karma and is indicated by a bigger person node \(focus node is kept at fixed size\).\\n\\nUsing the mouse or key actions, one can zoom in and out in a graph.  Click a node will fire up a new person page in another tab. In the Direct View graph, one can choose what types of relationships are included in the display. The default is set to all.')">help</a><br/>);
  my $helpRow = qq(<a href="http://wiki.wormbase.org/index.php/UserGuide:Person:Lineage" target="_blank">help</a><br/>);
  my $updateInfoRow = qq(<a href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/person_lineage.cgi?action=Display&number=$twonum" target="new">Add or update</a> your lineage information.<br/>);
  my $viewPngRow = qq(<div id="view_png_div"><button id="view_png_button">Export PNG</button></div><div id="view_edit_div" style="display: none;"><button id="view_edit_button">go back</button><br/>drag image to desktop, or right-click and save image as</div><br/>);
  my $arrowExplanation = qq(Mentor -> Mentee<br/>);
  print << "EndOfText";
Content-type: text/html

<!DOCTYPE html>
<html>
<head>
  <meta charset=utf-8 />
  <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
  <title>Intellectual Lineage Display</title>
<!--  <script src="http://cytoscape.github.io/cytoscape.js/api/cytoscape.js-latest/cytoscape.min.js"></script> latest doesn't work with cose -->
  <script src="http://tazendra.caltech.edu/~azurebrd/javascript/cytoscape.min.2.5.0.js"></script>

<!--  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
  <script src="http://cdnjs.cloudflare.com/ajax/libs/qtip2/2.2.0/jquery.qtip.min.js"></script>
  <link href="http://cdnjs.cloudflare.com/ajax/libs/qtip2/2.2.0/jquery.qtip.min.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.rawgit.com/cytoscape/cytoscape.js-qtip/2.2.5/cytoscape-qtip.js"></script>-->

  <script src="https://cdn.rawgit.com/cpettitt/dagre/v0.7.4/dist/dagre.min.js"></script>
<!--  <script src="http://marvl.infotech.monash.edu/webcola/cola.v3.min.js"></script>
  <script src="https://cdn.rawgit.com/cytoscape/cytoscape.js-cola/1.1.1/cytoscape-cola.js"></script>-->
  <script src="https://cdn.rawgit.com/cytoscape/cytoscape.js-dagre/1.1.2/cytoscape-dagre.js"></script>
<script>$code_js</script>

<style>
body { 
  font: 14px helvetica neue, helvetica, arial, sans-serif;
}

#cyContainer {
  height: 750px;
  width: 950px;
  position: relative;
  float: left;
}
#cyAll {
  height: 750px;
  width: 950px;
  position: relative;
  float: left;
  border: 1px solid #aaa;
  left: 0;
  top: 0;
}
#cyDirect {
  height: 375px;
  width: 395px;
  position: relative;
  float: left;
  border: 1px solid #aaa;
  left: 0;
  top: 0;
}
#cyFull {
  height: 375px;
  width: 395px;
  position: relative;
  float: left;
  border: 1px solid #aaa;
  left: 0;
  top: 0;
}

#info {
  color: #c88;
  font-size: 1em;
  position: absolute;
  z-index: -1;
  left: 1em;
  top: 1em;
}
</style>
</head>
  
<body>
  <div id="cyAll"></div>
  <img id="png-export" style="border: 1px solid #ddd; display: none;">
  <div id="optionsdiv" style="z-index: 9999; position: absolute; top: 0; right: 0; width: 200px; border: 1px solid #aaa; background: #e9eef2 none repeat scroll 0 0;">
    <div id="optionsborderdiv" style="border: 10px solid #e9eef2; ">
      $helpRow
      $viewPngRow
      $arrowExplanation
      <table id="directViewTable"><tbody>
        <tr><td valign="center"><a id="toggleToFullView" href="javascript:void(0)">To Full View</a></td></tr>
        $roleRowsDirect
        </tbody></table>
      <table id="fullViewTable" style="display: none;"><tbody>
        <tr><td valign="center"><a id="toggleToDirectView" href="javascript:void(0)">To Direct View</a></td></tr>
        $roleRowsFull
        </tbody></table>
      $updateInfoRow
    </div>
  </div>
</body>
</html>
EndOfText
}

__END__

my $user = 'transgene_form';		# who sends mail
my $email = "wchen\@its.caltech.edu";	# to whom send mail
my $subject = 'transgene data';	# subject of mail
my $body = '';					# body of mail

print "content-type: text/html\n\n";
print "$header\n";		# make beginning of html page

&process();			# see if anything clicked
&display();			# show form as appropriate
print "$footer"; 		# make end of html page

sub process {			# see if anything clicked
  my $action;			# what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'go !') { 
    $firstflag = "";		# reset flag to not display first page (form)
    open (out, ">>$acefile") or die "cannot create $acefile : $!";
    my @vars = qw(transgene summary driven_by_locus driven_by_sequence gfp lacz other_reporter worm_gene worm_sequence author email clone injected_into_cgc_strain injected_into integrated_by location strain map phenotype rescue cgc_number other_id reference remark);
    foreach $_ (@vars) { 
      my ($var, $val) = &gethtmlvar($query, $_);
      if ($val =~ m/\s/) { 	# if value entered
        if ($_ eq 'email') {	
          $email .= ', ' . $val; }
        if ($_ eq 'transgene') {	# print main tag if transgene
          print out "@{[ucfirst($var)]} : [$val] \n";
          print "@{[ucfirst($var)]} : [$val]<br>\n";
          $body .= "@{[ucfirst($var)]} : [$val]\n";
        } # if ($_ eq 'transgene')
        print out "@{[ucfirst($var)]} \"$val\" \n";
        print "@{[ucfirst($var)]} \"$val\" <br>\n";
        $body .= "@{[ucfirst($var)]} \"$val\"\n";
      } # if ($val) 
    } # foreach $_ (@vars) 
    print out "\n";		# divider for outfile
    close (out) || die "cannot close $acefile : $!";
    &mailer($user, $email, $subject, $body);	# email wen the data
    print "<p><p><p><h1>thank you, your info will be updated shortly.</h1>\n";
    print "if you wish to modify your submitted information, please go back and resubmit.<br><p> see all <a href=\"http://tazendra.caltech.edu/~azurebrd/cgi-bin/data/transgene.ace\">new submissions</a>.<p>\n";
  } # if ($action eq 'go !') 
} # sub process


sub display {			# show form as appropriate
  if ($firstflag) { # if first or bad, show form 
    print <<"endoftext";
<a name="form"><h1>new transgene data submission :</h1></a>

use this form for reporting new transgene data.<br><br>
we only accept integrated transgenic lines.<br><br>
if you don't know or don't have something, leave the field
blank.<br><br>
<!--if you have any problems or questions, please email me.<br><br>-->

<hr>

<form method="post" action="transgene.cgi">
<table>

<tr>
<td align="left"><b>transgene : </b></td>
</tr>

<tr>
<td align="right"><b>transgene :</b></td>
<td><table><input name="transgene" value="" size=30></table></td>
<td>e.g. : syis17</td>
</tr>

<tr></tr> <tr></tr> <tr></tr> <tr></tr> 
<tr></tr> <tr></tr> <tr></tr> <tr></tr>

<tr>
<td align="left"><b>transgene composition : </b></td>
</tr>

<tr>
<td align="right"><b>summary :</b></td>
<td><table><input name="summary" value="" size=30></table></td>
<td>e.g : [hsp16-2::goa-1(q205l)\; dpy-20(+)]. ...</td>
</tr>

<tr>
<td align="right"><b>driven by locus :</b></td>
<td><table><input name="driven_by_locus" value="" size=30></table></td>
<td>e.g. : hsp16b</td>
</tr>

<tr>
<td align="right"><b>driven by sequence :</b></td>
<td><table><input name="driven_by_sequence" value="" size=30></table></td>
<td>e.g. : zk863.1</td>
</tr>

<tr>
<td align="right"><b>drives gfp :</b></td>
<td><table><input name="gfp" value="" size=30></table></td>
</tr>

<tr>
<td align="right"><b>drives lacz :</b></td>
<td><table><input name="lacz" value="" size=30></table></td>
</tr>

<tr>
<td align="right"><b>drives other reporter : </b></td>
<td><table><input name="other_reporter" value="" size=30></table></td>
<td>e.g. : ha tag ...</td>
</tr>

<tr>
<td align="right"><b>drives worm gene :</b></td>
<td><table><input name="worm_gene" value="" size=30></table></td>
<td>e.g. : goa-1, with q205l mutation ...</td>
</tr>

<tr>
<td align="right"><b>drives worm sequence :</b></td>
<td><table><input name="worm_sequence" value="" size=30></table></td>
<td>e.g. : zk863.1 ...</td>
</tr>

<tr></tr> <tr></tr> <tr></tr> <tr></tr> 
<tr></tr> <tr></tr> <tr></tr> <tr></tr>

<tr>
<td align="left"><b>isolation : </b></td>
</tr>

<tr>
<td align="right"><b>author : </b></td>
<td><table><input name="author" value="" size=30></table></td>
</tr>

<tr>
<td align="right"><b>email : </b></td>
<td><table><input name="email" value="" size=30></table></td>
<td>if you don't get a verification email, email us at webmaster\@wormbase.org</td>
</tr>

<tr>
<td align="right"><b>clone :</b></td>
<td><table><input name="clone" value="" size=30></table></td>
<td>e.g. : zk863</td>
</tr>

<tr>
<td align="right"><b>injected into cgc strain :</b></td>
<td><table><input name="injected_into_cgc_strain" value="" size=30></table></td>
<td>e.g. : ps99</td>
</tr>

<tr>
<td align="right"><b>injected into :</b></td>
<td><table><input name="injected_into" value="" size=30></table></td>
<td>e.g. : goa-1(n363); dpy-20(e1282)...</td>
</tr>

<tr>
<td align="right"><b>integrated by :</b></td>
<td><table><input name="integrated_by" value="" size=30></table></td>
<td>e.g. : x_ray</td>
</tr>

<tr>
<td align="right"><b>location :</b></td>
<td><table><input name="location" value="" size=30></table></td>
<td>e.g. : ps</td>
</tr>

<tr>
<td align="right"><b>strain :</b></td>
<td><table><input name="strain" value="" size=30></table></td>
<td>e.g. : ps3351</td>
</tr>

<tr></tr> <tr></tr> <tr></tr> <tr></tr>
<tr></tr> <tr></tr> <tr></tr> <tr></tr>

<tr>
<td align="left"><b>related information : </b></td>
</tr>

<tr>
<td align="right"><b>map :</b></td>
<td><table><input name="map" value="" size=30></table></td>
<td>e.g. : chromosome iv, tightly linked to...</td>
</tr>

<tr>
<td align="right"><b>phenotype :</b></td>
<td><table><input name="phenotype" value="" size=30></table></td>
<td>e.g. : unc, egl, let. animals paralyzed ...</td>
</tr>

<tr>
<TD ALIGN="right"><b>Rescue :</b></TD>
<TD><TABLE><INPUT NAME="rescue" VALUE="" SIZE=30></TABLE></TD>
<TD>e.g. : goa-1(n363)</TD>
</TR>

<TR></TR> <TR></TR> <TR></TR> <TR></TR> 
<TR></TR> <TR></TR> <TR></TR> <TR></TR>

<TR>
<TD ALIGN="left"><b>Data Source : </b></TD>
<TD></TD>
<TD> (where curators can confirm the data)</TD>
</TR>

<TR>
<TD ALIGN="right"><b>CGC Number :</b></TD>
<TD><TABLE><INPUT NAME="CGC_number" VALUE="" SIZE=30></TABLE></TD>
<TD>e.g. : 4501</TD>
</TR>

<TR>
<TD ALIGN="right"><b>Other ID :</b></TD>
<TD><TABLE><INPUT NAME="Other_ID" VALUE="" SIZE=30></TABLE></TD>
<TD>e.g. : PMID11134024, or medline ...</TD>
</TR>

<TR>
<TD ALIGN="right"><b>Reference Info :</b></TD>
<TD><TABLE><INPUT NAME="Reference" VALUE="" SIZE=30></TABLE></TD>
<TD>e.g. : Science 274, 113-115 ...</TD>
</TR>

<TR></TR> <TR></TR> <TR></TR> <TR></TR> 
<TR></TR> <TR></TR> <TR></TR> <TR></TR>

<TR>
<TD ALIGN="right"><b>Remark :</b></TD>
<TD><TABLE><INPUT NAME="remark" VALUE="" SIZE=30></TABLE></TD>
<TD>Write comments here</TD>
</TR>

<!--
<TR>
<TD ALIGN="right"><b>Comment :</b></TD>
<TD><TABLE><INPUT NAME="comment" VALUE="" SIZE=30></TABLE></TD>
</TR>-->

<TR><TD COLSPAN=2> </TD></TR>
<TR>
<TD> </TD>
<TD><INPUT TYPE="submit" NAME="action" VALUE="Go !">
    <INPUT TYPE="reset"></TD>
</TR>
</TABLE>

</FORM>
If you have any problems, questions, or comments, please email <A HREF=\"mailto:wchen\@its.caltech.edu\">wchen\@its.caltech.edu</A>
EndOfText

  } # if (firstflag) show form 
} # sub display
