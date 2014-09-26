


YAHOO.util.Event.addListener(window, "load", function() {
//   alert("yes");
  var whichPage = document.getElementById("which_page").value;
  if (whichPage === 'displayNumber') {
    if (document.getElementById("author_max_order") !== null) {		// if there are authors
      if ( (document.getElementById("author_max_order").value !== undefined) && (document.getElementById("author_max_order").value !== '') ) {
        initAuthorList();
        setPersonAutocompleteListeners();		// set person autocompletes
    } }
  }
  else if (whichPage === 'personAuthorCuration') {
    if (document.getElementById('two_number_search').value === '') {
      document.getElementById('two_number_search').focus(); }
  }
  else if (whichPage === 'enterNonPmids') {
    if (document.getElementById('redirect_to').value) {
      window.location = document.getElementById('redirect_to').value; }
  }


}); // YAHOO.util.Event.addListener(window, "load", function()


function onAutocompleteItemSelect(oSelf , elItem, oData) {              // if an autocomplete item is selected
  var match = elItem[0]._sName.match(/input_(.*)_(.*?)_(.*?)$/);                     // get the field
  var table = match[1];
  var joinkey = match[2];
  var order = match[3];
  var curator_id = document.getElementById("curator_id").value;
  var newValue = elItem[1].innerHTML; 
//   alert(newValue);
// alert('table ' + table);
// alert('joinkey ' + joinkey);
// alert('order ' + order);
//   alert(elItem[0]._sName);
//   alert(field);
  updatePostgresTableField(table, joinkey, order, curator_id, newValue); 
// alert("oac " + newValue)
} // function onAutocompleteItemSelect(oSelf , elItem, oData)


function setPersonAutocompleteListeners() {		// set person autocompletes
  var arrInputIds = document.getElementById("person_input_ids").value.split(", ");       // split by comma into array
  var curator_id = document.getElementById("curator_id").value;		// new oa needs curator_two  2011 05 26
  for (var i in arrInputIds) {
    var inputId = arrInputIds[i];
    settingAutocompleteListeners = function() {
      var url = "oa/ontology_annotator.cgi?action=autocompleteXHR&field=person&datatype=app&curator_two=" + curator_id + "&";
      var oDS = new YAHOO.util.XHRDataSource(url);                // Use an XHRDataSource
      oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;      // Set the responseType
      oDS.responseSchema = {                                      // Define the schema of the delimited results
          recordDelim: "\n",
          fieldDelim: "\t"
      };
      oDS.maxCacheEntries = 5;                                    // Enable caching

      var inputElement = document.getElementById(inputId);
      var containerElement = document.getElementById("div_Container_" + inputId);
      var forcedOAC = new YAHOO.widget.AutoComplete(inputElement, containerElement, oDS);
      forcedOAC.queryQuestionMark = false;                        // don't add a ? to the url query since it's been built with some other values
      forcedOAC.maxResultsDisplayed = 500;
//       forcedOAC.minQueryLength = 0;					// setting this to zero doesn't allow deletions
      forcedOAC.forceSelection = true;
      forcedOAC.itemSelectEvent.subscribe(onAutocompleteItemSelect);
//       forcedOAC.selectionEnforceEvent.subscribe(onAutocompleteSelectionEnforce);

//       forcedOAC.itemArrowToEvent.subscribe(onAutocompleteItemHighlight);
//       forcedOAC.itemMouseOverEvent.subscribe(onAutocompleteItemHighlight);

      return {
          oDS: oDS,
          forcedOAC: forcedOAC
      }
    }();
  } // for (var id in arrIds)

//   YAHOO.example.BasicRemote = function() {
//       // Use an XHRDataSource
//       var url = "ontology_annotator.cgi?action=autocompleteXHR&field=person&datatype=app&";
//       var oDS = new YAHOO.util.XHRDataSource(url);                // Use an XHRDataSource
//   //     var oDS = new YAHOO.util.XHRDataSource("http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/autocomplete/person_autocomplete.cgi");
//       // Set the responseType
//       oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;
//       // Define the schema of the delimited results
//       oDS.responseSchema = {
//           recordDelim: "\n",
//           fieldDelim: "\t"
//       };
//       // Enable caching
//       oDS.maxCacheEntries = 5;
// 
//       var inputElement = document.getElementById("forcedPersonInput");
//       var containerElement = document.getElementById("forcedPersonContainer");
//   
//       var forcedOAC = new YAHOO.widget.AutoComplete("forcedPersonInput", "forcedPersonContainer", oDS);
//       forcedOAC.maxResultsDisplayed = 20;
//       forcedOAC.minQueryLength = 0;                       // allow searching for nothing (show all)
//   
//       forcedOAC.queryQuestionMark = false;                        // don't add a ? to the url query since it's been built with some other values
//       forcedOAC.maxResultsDisplayed = 500;
//       forcedOAC.forceSelection = true;
//   
//       return {
//           oDS: oDS,
//           forcedOAC: forcedOAC
//       };
//   }();

} // function setPersonAutocompleteListeners()



function initAuthorList() {
  var Dom = YAHOO.util.Dom; 
  var Event = YAHOO.util.Event; 
  var DDM = YAHOO.util.DragDropMgr; 

  YAHOO.example.DDApp = {
      init: function() { 
   
//           var rows=4,i; 
          var i, rows = document.getElementById("author_max_order").value;
          new YAHOO.util.DDTarget("author_list"); 
   
          for (i=1;i<rows+1;i=i+1) { 
              new YAHOO.example.DDList("author_li_" + i); 
          } 
   
//           Event.on("showButton", "click", this.showOrder); 
//           Event.on("switchButton", "click", this.switchStyles); 
      }, 
   
      showOrder: function() { 
          var parseList = function(ul, title) { 
              var items = ul.getElementsByTagName("li"); 
              var out = title + ": "; 
              for (i=0;i<items.length;i=i+1) { 
                  out += items[i].id + " "; 
              } 
              return out; 
          }; 
   
          var ul1=Dom.get("author_list"); 
          alert(parseList(ul1, "List 1") + "\n"); 
   
      }, 
   
//       switchStyles: function() { 
//           Dom.get("ul1").className = "draglist_alt"; 
//           Dom.get("ul2").className = "draglist_alt"; 
//       } 
  }; 

  YAHOO.example.DDList = function(id, sGroup, config) {
   
      YAHOO.example.DDList.superclass.constructor.call(this, id, sGroup, config); 
   
      this.logger = this.logger || YAHOO; 
      var el = this.getDragEl(); 
      Dom.setStyle(el, "opacity", 0.67); // The proxy is slightly transparent 
   
      this.goingUp = false; 
      this.lastY = 0; 
  }; 
   
  YAHOO.extend(YAHOO.example.DDList, YAHOO.util.DDProxy, {
   
      startDrag: function(x, y) { 
          this.logger.log(this.id + " startDrag"); 
   
          // make the proxy look like the source element 
          var dragEl = this.getDragEl(); 
          var clickEl = this.getEl(); 
          Dom.setStyle(clickEl, "visibility", "hidden"); 
   
          dragEl.innerHTML = clickEl.innerHTML; 
   
          Dom.setStyle(dragEl, "color", Dom.getStyle(clickEl, "color")); 
          Dom.setStyle(dragEl, "backgroundColor", Dom.getStyle(clickEl, "backgroundColor")); 
          Dom.setStyle(dragEl, "border", "2px solid gray"); 
      }, 
   
      endDrag: function(e) { 
   
          var srcEl = this.getEl(); 
          var proxy = this.getDragEl(); 
   
          // Show the proxy element and animate it to the src element's location 
          Dom.setStyle(proxy, "visibility", ""); 
          var a = new YAHOO.util.Motion(  
              proxy, {  
                  points: {  
                      to: Dom.getXY(srcEl) 
                  } 
              },  
              0.2,  
              YAHOO.util.Easing.easeOut  
          ) 
          var proxyid = proxy.id; 
          var thisid = this.id; 
   
          // Hide the proxy and show the source element when finished with the animation 
          a.onComplete.subscribe(function() { 
                  Dom.setStyle(proxyid, "visibility", "hidden"); 
                  Dom.setStyle(thisid, "visibility", ""); 
              }); 
          a.animate(); 

          var newOrder = new Array;
          var joinkey = document.getElementById("paper_joinkey").value;
          var curator_id = document.getElementById("curator_id").value;
          var items = Dom.get("author_list").getElementsByTagName("li"); 
//           var out = ": "; 
          for (i=0;i<items.length;i=i+1) { 
              newOrder.push(items[i].value);
//               out += items[i].id + " " + items[i].value + "; "; 
          } 
          var orderForPg = newOrder.join("_TAB_");
          updatePostgresTableField('author_reorder', joinkey, 'new_order', curator_id, orderForPg);
//           alert(out); 
      }, 
   
      onDragDrop: function(e, id) { 
   
          // If there is one drop interaction, the li was dropped either on the list, 
          // or it was dropped on the current location of the source element. 
          if (DDM.interactionInfo.drop.length === 1) { 
   
              // The position of the cursor at the time of the drop (YAHOO.util.Point) 
              var pt = DDM.interactionInfo.point;  
   
              // The region occupied by the source element at the time of the drop 
              var region = DDM.interactionInfo.sourceRegion;  
   
              // Check to see if we are over the source element's location.  We will 
              // append to the bottom of the list once we are sure it was a drop in 
              // the negative space (the area of the list without any list items) 
              if (!region.intersect(pt)) { 
                  var destEl = Dom.get(id); 
                  var destDD = DDM.getDDById(id); 
                  destEl.appendChild(this.getEl()); 
                  destDD.isEmpty = false; 
                  DDM.refreshCache(); 
              } 
   
          } 
      }, 
   
      onDrag: function(e) { 
   
          // Keep track of the direction of the drag for use during onDragOver 
          var y = Event.getPageY(e); 
   
          if (y < this.lastY) { 
              this.goingUp = true; 
          } else if (y > this.lastY) { 
              this.goingUp = false; 
          } 
   
          this.lastY = y; 
      }, 
   
      onDragOver: function(e, id) { 
       
          var srcEl = this.getEl(); 
          var destEl = Dom.get(id); 
   
          // We are only concerned with list items, we ignore the dragover 
          // notifications for the list. 
          if (destEl.nodeName.toLowerCase() == "li") { 
              var orig_p = srcEl.parentNode; 
              var p = destEl.parentNode; 
   
              if (this.goingUp) { 
                  p.insertBefore(srcEl, destEl); // insert above 
              } else { 
                  p.insertBefore(srcEl, destEl.nextSibling); // insert below 
              } 
   
              DDM.refreshCache(); 
          } 
      } 
  }); 

  Event.onDOMReady(YAHOO.example.DDApp.init, YAHOO.example.DDApp, true); 
//   alert("no");
} // function initAuthorList()


// replaced by updatePostgresTableField set to blank newValue
// function deletePostgresTableField(field, order, curator) {
//     var joinkey = document.getElementById("paper_joinkey").value;
//     var callbacks = {
//         success : function (o) {                                // Successful XHR response handler
//             if (o.responseText === 'OK') {                      // it's ok, don't say anything
//               window.location.reload(false);
//             }
//             else { alert("ERROR not OK response for deletion of " + field + " order " + order + " for joinkey " + joinkey + " "); }
//         },
//         failure:function(o) {
//             alert("ERROR delete of " + field + " did not work for joinkey " + joinkey + " and order " + order + "<br>" + o.statusText);
//         },
//     };
//     // Make the call to the server to update postgres
//     var url="paper_editor.cgi";
// //     newValue = newValue.replace(/\n/g, ' ');			// newlines break the get call
//     url=url+"?action=deletePostgresTableField";			// the action
//     url=url+"&field=" + field;				// the field name
//     url=url+"&joinkey="+joinkey;			// the joinkey
//     url=url+"&order="+order;				// the order
//     url=url+"&curator="+curator;			// the curator
//     YAHOO.util.Connect.asyncRequest('GET', url, callbacks);
// }

function updatePostgresTableField(field, joinkey, order, curator, newValue, evi, redirectUrl) {
	// proper YUI way to make a GET ajax call
    var callbacks = {
        success : function (o) {                                // Successful XHR response handler
            if (o.responseText === 'OK') {                      // it's ok, don't say anything
//               Response.Redirect(Request.Url.ToString(), false); 
              if (redirectUrl === undefined) { window.location.reload(false); }		// if undefined value, reload page (default action)
                else if (redirectUrl === 'nothing') { }		// if said 'nothing', don't force reload
                else { window.location = redirectUrl; }		// if there is a url, redirect to it
            }
            else { alert("ERROR not OK response for newValue " + newValue + " did not update for joinkey " + joinkey + " and " + field + ".  got :" + o.responseText + "END o.responseText"); }
        },
        failure:function(o) {
            alert("ERROR newValue " + newValue + " did not update for joinkey " + joinkey + " and " + field + "<br>" + o.statusText);
        },
    };
    // Make the call to the server to update postgres
    var url="paper_editor.cgi";
    newValue = convertDisplayToUrlFormat(newValue);                             // convert <newValue> to URL format by escaping characters
//     newValue = newValue.replace(/\n/g, ' ');			// newlines break the get call
    url=url+"?action=updatePostgresTableField";			// the action
    url=url+"&field=" + field;				// the field name
    url=url+"&joinkey="+joinkey;			// the joinkey
    url=url+"&order="+order;				// the order
    url=url+"&curator="+curator;			// the curator
    url=url+"&newValue="+newValue;			// the text to send in
    if (evi !== undefined) { url=url+"&evi="+evi; }	// the evidence if any
    YAHOO.util.Connect.asyncRequest('GET', url, callbacks);
} // function updatePostgresTableField(pgid, field, newValue)

function convertDisplayToUrlFormat(value) {			// need to escape # + ; for the CGI to get it okay 2011 06 30
    if (value !== undefined) {                                                  // if there is a display value replace stuff
        if (value.match(/\+/)) { value = value.replace(/\+/g, "%2B"); }         // replace + with escaped +
        if (value.match(/\;/)) { value = value.replace(/\;/g, "%3B"); }         // replace ; with escaped ;
        if (value.match(/\#/)) { value = value.replace(/\#/g, "%23"); }         // replace # with escaped #
    }
    return value;                                                               // return value in format for URL
} // function convertDisplayToUrlFormat(value)



function matchGeneTextarea(order, type) {
    var geneTextareaValue = document.getElementById('textarea_gene_' + order).value;
    if (type === 'evi') { geneTextareaValue = document.getElementById('textarea_evi_gene_' + order).value; }
  
    var callbacks = {
        success : function (o) {                                // Successful XHR response handler
            if (o.responseText !== undefined) { 
                var displayElement = document.getElementById('div_gene_display');
                if (type === 'evi') { displayElement = document.getElementById('div_evi_gene_display'); }
                displayElement.innerHTML = o.responseText; }
        },
//         failure : function(o) { alert("ERROR did not get call back from gethint.cgi for " + geneTextareaValue + " <br>" + o.responseText+ " <br>" + o.statusText); },		// this error is popping a bit, with o.responseText being undefined, I don't know why
    };
    // Make the call to the server to update postgres
    var url="http://tazendra.caltech.edu/~azurebrd/cgi-bin/testing/javascript/ajax/gethint.cgi";
    var text = geneTextareaValue;	// newlines break the get call
    var text = text.replace(/\n/g, ' ');	// newlines break the get call
    url=url+"?type=genestudied";			// to get genes
    url=url+"&sid="+Math.random();                      // random to prevent browser using a cached page
    url=url+"&all="+text;                               // the text to send in
    if (text !== undefined) {		// sometimes this is blank, maybe because toggleGeneTextareaToDiv gets called first ?
        YAHOO.util.Connect.asyncRequest('GET', url, callbacks);
    }
}


function confirmInvalid(joinkey) {
  var where_to = confirm("You are about to delete ALL reference data associated with WBPaper" + joinkey + " and any associated author objects");
  if (where_to === true) {
    var curator_id = document.getElementById("curator_id").value;
    updatePostgresTableField('status', joinkey, '', curator_id, 'delete');
  } else { alert("catastrophe avoided."); }
} // function confirmInvalid(joinkey)

function mergePaper(joinkey, curator_id) {		// redirect to merge page
  var mergeIntoPaper = document.getElementById('merge_into').value;
  window.location = 'paper_editor.cgi?curator_id=two1823&action=Merge&joinkey=' + joinkey + '&merge_into=' + mergeIntoPaper;
} // function mergePaper(joinkey, curator_id)

function toggleGeneTextareaToDiv(table, joinkey, order, curator_id) {
    var divElement = document.getElementById('div_' + table + '_' + order);
    var textareaElement = document.getElementById('textarea_' + table + '_' + order);
    var dataElement = document.getElementById('div_gene_display');
    divElement.style.display = '';
    textareaElement.style.display = 'none';
    if (divElement.innerHTML !== textareaElement.value) {
        divElement.innerHTML = textareaElement.value;
        updatePostgresTableField(table, joinkey, order, curator_id, dataElement.innerHTML); }
} // function toggleGeneTextareaToDiv(table, order, joinkey, curator_id)

function toggleTdToGeneEvi(table, joinkey, order) {
  document.getElementById('td_gene_placeholder').style.display = 'none';
  document.getElementById('td_gene_info').style.display = '';
  document.getElementById('input_published_as').focus();
}
function verifyEviFocusOnGene(table, joinkey, order, curator_id) {
  var eviElement = document.getElementById('input_published_as');
  if (eviElement.value !== '') { 		// there is some evidence data
    document.getElementById('textarea_evi_' + table + '_' + order).focus(); }
  else { 					// there is no evidence data
    document.getElementById('td_gene_placeholder').style.display = '';
    document.getElementById('td_gene_info').style.display = 'none';
    alert("you must enter a Published_as evidence value, if you don't have one, use gene (batch)"); }
} // function verifyEviFocusOnGene(table, joinkey, order, curator_id)
function geneEviToDiv(table, joinkey, order, curator_id) {
    var geneValue = document.getElementById('div_evi_gene_display').innerHTML; 
    var eviValue = document.getElementById('input_published_as').value;
    var textareaElement = document.getElementById('textarea_evi_' + table + '_' + order);
    var displayDivElement = document.getElementById('display_div_' + table + '_' + joinkey + '_' + order);
    document.getElementById('td_gene_placeholder').style.display = '';
    document.getElementById('td_gene_info').style.display = 'none';
    if (displayDivElement.innerHTML !== textareaElement.value) {	// text changed from what it had before
        if ((geneValue !== '\n') && (geneValue !== '')) { 		// o.responseText is sometimes a newline
            var data = geneValue + ' Published_as ' + eviValue;
            displayDivElement.innerHTML = data;
            updatePostgresTableField(table, joinkey, order, curator_id, data); }
          else { alert('There is no gene value'); } }
} // function geneEviToDiv(table, joinkey, order, curator_id)


function toggleDivToTextarea(table, joinkey, order) {
  document.getElementById('div_' + table + '_' + order).style.display='none'; 
  document.getElementById('textarea_' + table + '_' + order).style.display=''; 
  document.getElementById('textarea_' + table + '_' + order).focus();
}

function toggleTextareaToDiv(table, joinkey, order, curator_id) {
    var divElement = document.getElementById('div_' + table + '_' + order);
    var textareaElement = document.getElementById('textarea_' + table + '_' + order);
    divElement.style.display = '';
    textareaElement.style.display = 'none';
    if (divElement.innerHTML !== textareaElement.value) {
        divElement.innerHTML = textareaElement.value;
        updatePostgresTableField(table, joinkey, order, curator_id, textareaElement.value); }
}

function toggleDivToSpanInput(table, joinkey, order) {
//   document.getElementById('div_' + table + '_' + joinkey + '_' + order).style.display='none'; 
//   document.getElementById('span_AutoComplete_input_' + table + '_' + joinkey + '_' + order).style.display=''; 
  document.getElementById('td_display_input_' + table + '_' + joinkey + '_' + order).style.display='none'; 
  document.getElementById('td_AutoComplete_input_' + table + '_' + joinkey + '_' + order).style.display=''; 
  document.getElementById('input_' + table + '_' + joinkey + '_' + order).focus();
}
function toggleAcInputToTd(table, joinkey, order, curator_id) {		// toggle autocomplete to display (and save data + reload page)
//     alert("toggleAcInputToTd");

  var divContainerElement = document.getElementById('div_Container_input_' + table + '_' + joinkey + '_' + order);
  var arrDivs = divContainerElement.getElementsByTagName("div");	// the first child div (unnamed) has a display status when autocomplete is expanded
  if (arrDivs[0].style.display === '') { 1; } 				// showing autocomplete, don't do anything, wait for user input
    else { 								// autocomplete gone, update to match value
      var divElement = document.getElementById('div_' + table + '_' + joinkey + '_' + order);
      var inputElement = document.getElementById('input_' + table + '_' + joinkey + '_' + order);
      document.getElementById('td_display_input_' + table + '_' + joinkey + '_' + order).style.display=''; 
      document.getElementById('td_AutoComplete_input_' + table + '_' + joinkey + '_' + order).style.display='none'; 
      if (divElement.innerHTML !== inputElement.value) {
          divElement.innerHTML = inputElement.value;
          updatePostgresTableField(table, joinkey, order, curator_id, inputElement.value); } }
}


function toggleDivToInput(table, joinkey, order) {
  document.getElementById('div_' + table + '_' + joinkey + '_' + order).style.display='none'; 
  document.getElementById('input_' + table + '_' + joinkey + '_' + order).style.display=''; 
  document.getElementById('input_' + table + '_' + joinkey + '_' + order).focus();
}

function toggleInputToDiv(table, joinkey, order, curator_id) {
    var divElement = document.getElementById('div_' + table + '_' + joinkey + '_' + order);
    var inputElement = document.getElementById('input_' + table + '_' + joinkey + '_' + order);
    divElement.style.display = '';
    inputElement.style.display = 'none';
    if (divElement.innerHTML !== inputElement.value) {
        divElement.innerHTML = inputElement.value;
        updatePostgresTableField(table, joinkey, order, curator_id, inputElement.value); }
}

function toggleDivTripleToggle(table, joinkey, order, curator_id, one, two, three) {
    var divElement = document.getElementById('div_' + table + '_' + joinkey + '_' + order);
    var setTo = two;							// set two by default
    if (divElement.innerHTML === one) { setTo = two; }			// if one, set two
    else if (divElement.innerHTML === two) { setTo = three; }		// if two, set three
    else if (divElement.innerHTML === three) { setTo = one; }		// if three, set on
    else if (divElement.innerHTML === undefined) { setTo = one; }	// if nothing, set one
    else if (divElement.innerHTML === '') { setTo = one; }		// if nothing, set one
    else { setTo = two; }						// if anything set two (not needed by initialization)
    updatePostgresTableField(table, joinkey, order, curator_id, setTo); 
}


function changeSelect(table, joinkey, order, curator_id) {
    var elSel = document.getElementById('select_' + table + '_' + order);
    for (var i = elSel.length - 1; i>=0; i--) { 
      if (elSel.options[i].selected) { 
        updatePostgresTableField(table, joinkey, order, curator_id, elSel.options[i].value); } }
}


