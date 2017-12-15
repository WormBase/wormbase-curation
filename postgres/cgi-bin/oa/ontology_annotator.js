// See interspersed ScriptDoc documentation.
//
// See  oa_old_commented_out_code/  for versions change history and commented-out code.


/**
 *  Description
 */

/**
 * The ontology_annotator.cgi uses a lot of javascript, most of it from the YUI javascript modules, but all the ontology annotator specific code comes from this file.
 * The ontology_annotator.js is loaded from the ontology_annotator.cgi table frame, and while it could be moved to a different frame, the calls to get variables from html elements would need to be edited.
 *
 */

/**
 *  Global Variables
 * Some variables are static and used at various places. myDataTable is a YUI ScrollingDataTable object used in various places.
 * @param {Object} myDataTable  is the YUI ScrollingDataTable object used to display data in ontology_annotator.cgi table frame.  Constructed by calling  initializeTable(myColumnDefs)  creating it with  myDataTable = new YAHOO.widget.ScrollingDataTable("myContainer", myColumnDefs, myDataSource, { width:"99.5%", height:"100%", draggableColumns:true});
 * @param {Array} myFields  is an array listing all the ontology annotator fields, gotten from all html input elements with class 'fields'.  Initialized by calling  populateMyFields() .
 * @param {Object} fieldsData  is a hash mapping all the ontology annotator fields and options to their values, gotten from all html hidden input elements with id 'data_<field>'.  Initialized by calling  populateMyFields() .
 * @param {String} datatype  is the datatype loaded into the ontology_annotator.cgi , gotten from the editor frame html hidden input element with id 'datatype'.  Initialized from the window load listener.
 * @param {String} curatorTwo  is the id of the curator who loaded into the ontology_annotator.cgi , gotten from the editor frame html hidden input element with id 'curatorTwo'.  Initialized from the window load listener.  curatorTwo is the id of the curator, as opposed to the human name.
 * @param {String} cgiUrl  is the ontology_annotator.cgi , used for constructing all the AJAX calls.
 * @param {String} loadingGifUrl  is the path to the 'loading' image used when there's a postgres query to load data into the dataTable, and in the YUI wait Panel. 
 *
 */


var myDataTable;
var myFields = new Array();			// the data fields, for some reason the elements get replaced by objects when datatable gets created
var fieldsData = new Object();
var datatype;					// two gop app
var curatorTwo;					// who is logged on as two####
var cgiUrl = "ontology_annotator.cgi";
var loadingGifUrl = "images/loading.gif";


/**
 *  Window Load
 */

/**
 * Event Window Load
 * When the window loads an anonymous function is called setting values to global variables and listeners to actions.
 * Call  populateMyFields()  to get list of fields from the editor frame into the array  myFields .
 * Get  datatype  and  curatorTwo  from editor frame html hidden input elements with ids 'datatype' and 'curatorTwo'.
 * For each field in myFields:
 * - get editor frame element 'button_<field>' and add 'click' listener to  assignQueryButtonListenerAjax  to query postgres for the corresponding input to load data.
 * - get editor frame element 'input_<field>'  and add  'blur' listener to  editorInputBlurListener        to update postgres tables and dataTable for the corresponding input ;  skipping fields of type 'bigtext' which are handled later.
 * - get editor frame element 'label_<field>'  and add 'click' listener to  assignEditorLabelTdListener    to toggle corresponding dataTable column hide / show.
 * - get tab from  fieldsData[<field>]["tab"]  and add to  tabs  hash.
 * - for 'ontology'  fieldsData[<field>]["type"]  get editor frame element 'input_<field>'  and add  'click' listener to  asyncTermInfo(field, this.value)  to change the term info in the obo frame.  input fields add data to postgres, datatable, and corresponding select (if appropriate) when blurred.
 * - for 'multiontology' and 'multidropdown'  fieldsData[<field>]["type"]  get editor frame element 'button_remove_<field>'  and add  'click' listener to  removeSelectFieldEntriesListener  to remove values from field's select html element and update postgres table ;  get editor frame element 'select_<field>' and add 'change' listener to load the value into the input field and for 'multiontology' call  asyncTermInfo(field, inputValue)  to change the term info in the obo frame.  multivalue fields load select element into input when changed, load term info into obo frame ;  have a remove button to remove values.
 * - for 'toggle' and 'toggletext'  fieldsData[<field>]["type"]  get editor frame element 'toggle_<field>'  and add  'click' listener to  toggle the value of the field on or off ;  'on' sets the background color 'red' and calls  editorFieldBlur(field, fieldsData[field]["label"])  setting the postgres value to be the label ;  'off' sets the background color 'white' and calls  editorFieldBlur(field, "")  setting the postgres value to be deleted.  toggle fields store the label in postgres and show red when on.
 * - for 'bigtext'  fieldsData[<field>]["type"]  get editor frame element 'input_<field>'  and add  'focus' listener to hide the element, show the corresponding 'textarea_bigtext_<field>', place the 'input_<field>' value into the 'textarea_bigtext_<field>' value, and focus on the 'textarea_bigtext_<field>' element ;  get editor frame element 'textarea_bigtext_<field>'  and add 'blur' listener to hide the element, show the corresponding 'input_<field>' element, place the 'textarea_bigtext_<field>' value into the 'input_<field>' value, and for all fields except for those with  fieldsData[<field>]["noteditable"]  call  editorFieldBlur(field, top.frames['editor'].document.getElementById("input_" + field).value)  to update dataTable and postgres table.  bigtext input fields switch to textareas when focused and back to input fields when blurred.
 * For each tab in  tabs  hash, get editor frame element with id '<tab>'  and add 'click' listener to call  showTab(this.id)  to only show html elements that have class '<tab>' or 'all'.
 * If the datatype has a numeric tab (as opposed to all fields having value 'all'), by default call  showTab("tab" + firstTab);  to show the html elements in the lowest tab.
 * Get editor   frame element 'resetPage'     and add 'click'  listener to call  resetButtonListener               to reload the obo frame, clear the dataTable data, and all editor values.
 * Get controls frame element 'checkData'     and add 'click'  listener to call  checkDataButtonListener           to reload to check dataTable data against datatype constraints.
 * Get controls frame element 'deleteRow'     and add 'click'  listener to call  deleteRowButtonListener           to delete selected dataTable rows from dataTable and postgres tables.
 * Get controls frame element 'newRowAmount'  and add 'click'  listener to call  changeNewRowAmountPromptListener  to set the amount of rows to create when pressing the New button
 * Get controls frame element 'duplicateRow'  and add 'click'  listener to call  duplicateRowButtonListener        to duplicate selected dataTable rows into the dataTable and postgres tables.
 * Get controls frame element 'newRow'        and add 'click'  listener to call  newRowButtonListener              to create new rows in the dataTable and new datatype object in the postgres tables, the amount given by the 'newRowAmount' html element.
 * Get controls frame element 'filtersAmount' and add 'change' listener to call  updateFiltersAmountListener       to show that amount of filter pairs.
 * For each filter pair showing, get control frame element with id 'filterValue<count>'  and add 'keyup' listener to call  filterDataKeyUpListener  to hide dataTable rows that don't have data matching the filter pairs.
 * Get column definitions by looking at each field, setting the key to <field>, sortable to true, resizeable to true, and getting property values from  fieldsData[<field>][<property>] .  columns are entered in order of fields unless the 'columnOrder' property is set.
 * Get <myColumnDefs>, an array of hashes, by looping over all fields in <myFields>, adding for each field a (hash) object with pairs 'key' to field, 'sortable' to true, 'resizable' to true, and each pair from <fieldsData[field]>.  If there is an order property set it at that index in the array, otherwise enter them in order.
 * Initialize dataTable by calling  initializeTable(myColumnDefs) .
 * Initialize the amount of filters by calling  updateFiltersAmount() .
 * Initialize autocomplete listeners for fields of type 'dropdown', 'multidropdown', 'ontology', or 'multiontology'.
 * Initialize  waitPanel  a YUI Panel to show the  loadingGif  when data is loading to the dataTable from a  postgresQueryField(field, userValue, amountRowsToHighlight)  call.  Hide the panel by default and show while waiting for  AJAX  response.
 *
 */


YAHOO.util.Event.addListener(window, "load", function() { 					// on load get fields, assign listeners
  populateMyFields();										// populate myFields array
  datatype = top.frames['editor'].document.getElementById("datatype").value;			// get datatype
  curatorTwo = top.frames['editor'].document.getElementById("curatorTwo").value;		// get curator that is logged on as two####

  var tabs = new Object(); var firstTab = 0;							// hash of tabs used by config, initialize firstTab to zero because it should not show if all tab values are 'all'
  for (var i = 0; i < myFields.length; i++ ) { 							// for each field
    var oElement = top.frames['editor'].document.getElementById("button_" + myFields[i]);	// get the button element to add the listener to
    YAHOO.util.Event.addListener(oElement, "click", assignQueryButtonListenerAjax ); 		// add the listener function

    if ( ( fieldsData[myFields[i]]["type"] !== "textarea" ) && 
         ( fieldsData[myFields[i]]["type"] !== "bigtext"  ) ) {					// input fields update postgres and datatable when blurred, except for bigtext and textarea fields 
        oElement = top.frames['editor'].document.getElementById("input_" + myFields[i]);
        YAHOO.util.Event.addListener(oElement, "blur", editorInputBlurListener ); } 		// add the listener function
    else if ( fieldsData[myFields[i]]["type"] === "textarea" ) {
        oElement = top.frames['editor'].document.getElementById("textarea_" + myFields[i]);
        YAHOO.util.Event.addListener(oElement, "blur", editorTextareaBlurListener ); } 		// add the listener function

    oElement = top.frames['editor'].document.getElementById("label_" + myFields[i]);		// if clicking td of field label, toggle showHide datatable column
    YAHOO.util.Event.addListener(oElement, "click", assignEditorLabelTdListener ); 		// add the listener function

    var tab = fieldsData[myFields[i]]["tab"];							// the tab value
    if ( (! (tab in tabs) ) && (tab !== "all") ) {						// if not already in tabs object, and it's not "all" (skip all)
        if (tab.match(/tab\d+/)) {								// if it matches a number
            var match = tab.match(/tab(\d+)/); var tabNum = parseInt(match[1]);			// get the tab number
            if ( (tabNum > 0) && ( ( firstTab === 0 ) || ( tabNum < firstTab ) ) ) {		// if tab number > 0 (real tab) AND ( firstTab hasn't changed (no values yet), OR we have a lower tab number )
	        firstTab = tabNum; } }								// first tab is this new tab number with a lower value than previous ones
        tabs[tab] = 1; }									// add tab to tabs object hash

    if ( fieldsData[myFields[i]]["type"] === "ontology" ) {					// ontology values load term info when input is field is clicked
      oElement = top.frames['editor'].document.getElementById("input_" + myFields[i]);
      YAHOO.util.Event.addListener(oElement, "click", function() {				// when clicking an ontology input element, async term info
        var match = this.id.match(/input_(.*)/); var field = match[1];				// get the field from the id
        if (this.value) {									// only if there's a value try to get term info
          asyncTermInfo(field, this.value); } }); }						// get term info of input value
    else if ( ( fieldsData[myFields[i]]["type"] === "multiontology" ) || ( fieldsData[myFields[i]]["type"] === "multidropdown" ) ) {
												// if it's a multi-value ontology or dropdown field
      oElement = top.frames['editor'].document.getElementById("button_remove_" + myFields[i]);
      YAHOO.util.Event.addListener(oElement, "click", removeSelectFieldEntriesListener ); 	// add the listener function
      oElement = top.frames['editor'].document.getElementById("select_" + myFields[i]);
      YAHOO.util.Event.addListener(oElement, "change", function() { 				// when clicking an option element, load the value to the input element
          var match = this.id.match(/select_(.*)/); var field = match[1];			// get the field from the id
          var inputValue = '';
          if (this.selectedIndex > -1) { 							// if there's a selected value
              inputValue = this.options[this.selectedIndex].value;				// get the value to put in the input element
              if ( fieldsData[field]["type"] === "multiontology" ) {				// if it is of type multiontology
                  asyncTermInfo(field, inputValue); } }						// get term info of clicked value
          top.frames['editor'].document.getElementById('input_' + field).value = inputValue;	// load option value into input element
      }); }
    else if ( ( fieldsData[myFields[i]]["type"] === "toggle" ) || ( fieldsData[myFields[i]]["type"] === "toggle_text" ) ) {	// if it's a toggle field, toggle between red and white, update datatable with editorFieldBlur
      oElement = top.frames['editor'].document.getElementById("toggle_" + myFields[i]);
      YAHOO.util.Event.addListener(oElement, "click", function() { 				// when clicking a toggle input element, change the background color to red for on and white for off
        if (top.frames['editor'].document.getElementById("input_id").disabled !== true) {	// only change stuff if editor is not disabled (editor being represented by id field)
            var match = this.id.match(/toggle_(.*)/); var field = match[1];			// get the field from the id
            if (top.frames['editor'].document.getElementById("toggle_" + field).style.backgroundColor === "red") {
               editorFieldBlur(field, ""); 
               top.frames['editor'].document.getElementById("toggle_" + field).style.backgroundColor = "white"; }
            else {
               editorFieldBlur(field, fieldsData[field]["label"]); 
               top.frames['editor'].document.getElementById("toggle_" + field).style.backgroundColor = "red"; } } }); }
    else if ( fieldsData[myFields[i]]["type"] === "bigtext" ) {					// if it's a bigtext field
      oElement = top.frames['editor'].document.getElementById("input_" + myFields[i]);
      YAHOO.util.Event.addListener(oElement, "focus", function() { 				// when clicking a bigtext input element, hide input, load data into textarea, show textarea
          var match = this.id.match(/input_(.*)/); var field = match[1];			// get the field from the id
          top.frames['editor'].document.getElementById("input_" + field).style.display = "none"; 
          top.frames['editor'].document.getElementById("textarea_bigtext_" + field).style.display = ""; 
          top.frames['editor'].document.getElementById("textarea_bigtext_" + field).value = top.frames['editor'].document.getElementById("input_" + field).value;
          top.frames['editor'].document.getElementById("textarea_bigtext_" + field).focus(); }); 
      var bigtextElement = top.frames['editor'].document.getElementById("textarea_bigtext_" + myFields[i]);
      YAHOO.util.Event.addListener( bigtextElement, "blur", function() { 			// when blurring a bigtext textarea element, hide textarea, load data into input, show input
          var match = this.id.match(/textarea_bigtext_(.*)/); var field = match[1];		// get the field from the id
          top.frames['editor'].document.getElementById("textarea_bigtext_" + field).style.display = "none"; 
          top.frames['editor'].document.getElementById("input_" + field).style.display = ""; 
          top.frames['editor'].document.getElementById("input_" + field).value = top.frames['editor'].document.getElementById("textarea_bigtext_" + field).value;	// switch value from textarea to input, regardless of whether noteditable or not
          if ( fieldsData[field]["noteditable"] !== "noteditable" ) {				// do not allow postgres editing of noteditable fields (but do allow data changing in the html field)
              editorFieldBlur(field, top.frames['editor'].document.getElementById("input_" + field).value); } }); }
  } // for (var i = 0; i < myFields.length; i++ )

  for (var tab in tabs) {									// for each tab, add a listener to only show only that tab's values
      var oElement = top.frames['editor'].document.getElementById(tab)
      YAHOO.util.Event.addListener(oElement, "click", function() { showTab(this.id); }); }
  if (firstTab) { showTab("tab" + firstTab); }							// by default if there is a first tab (numberic tab) show the lowest tab

  var oElement = top.frames['editor'].document.getElementById("resetPage");
  YAHOO.util.Event.addListener(oElement, "click", resetButtonListener );			// add the listener function
  oElement = top.frames['controls'].document.getElementById("checkData");
  YAHOO.util.Event.addListener(oElement, "click", checkDataButtonListener );			// add the listener function
  oElement = top.frames['controls'].document.getElementById("deleteRow");
  YAHOO.util.Event.addListener(oElement, "click", deleteRowButtonListener );			// add the listener function
  oElement = top.frames['controls'].document.getElementById("duplicateRow");
  YAHOO.util.Event.addListener(oElement, "click", duplicateRowButtonListener );			// add the listener function
  oElement = top.frames['controls'].document.getElementById("newRow");
  YAHOO.util.Event.addListener(oElement, "click", newRowButtonListener );			// add the listener function
  oElement = top.frames['controls'].document.getElementById("newRowAmount");
  YAHOO.util.Event.addListener(oElement, "click", changeNewRowAmountPromptListener );		// add the listener function
  oElement = top.frames['controls'].document.getElementById("filtersAmount");
  YAHOO.util.Event.addListener(oElement, "change", updateFiltersAmountListener );		// add the listener function

  var filtersMaxAmount = top.frames['controls'].document.getElementById("filtersMaxAmount").value;
  for (var filterCount = 1; filterCount < filtersMaxAmount; filterCount++) {
      var filterValueId = 'filterValue' + filterCount;						// generate value id
      oElement = top.frames['controls'].document.getElementById(filterValueId);
      YAHOO.util.Event.addListener(oElement, "keyup", filterDataKeyUpListener );		// add the listener function
  } // for (var filterCount = 1; filterCount < filtersMaxAmount; filterCount++)

  var arrUnorderedFields = [];
  var myColumnDefs = new Array();								// column definitions for data tables
  for (var i = 0; i < myFields.length; i++ ) {							// for each field
    var field = myFields[i];
    var entry = { key:myFields[i], sortable:true, resizeable:true };				// make an entry hash
    for (var property in fieldsData[field]) {							// set extra properties from fieldsData
      entry[property] = fieldsData[field][property]; 
    }
    if (entry["columnOrder"]) {
        var order = parseInt(entry["columnOrder"]);						// get the column order
        myColumnDefs[order] = entry; } 								// add to column definitions array
      else { arrUnorderedFields.push(entry); }							// add to array of fields without specific column order
  }
  for (var i = 0; i < arrUnorderedFields.length; i++ ) { myColumnDefs.push(arrUnorderedFields[i]); }	// for each field without specific column order, add to end of normal myColumnDefs

  initializeTable(myColumnDefs);
  updateFiltersAmount();									// show/hide amount of filters, update datatable based on filters

  setAutocompleteListeners();									// for each ontology field, add autocomplete listener

  var waitPanel = new YAHOO.widget.Panel("wait",  { width:"240px", fixedcenter:true, close:false, draggable:false, modal:true,
  				                    visible:false, effect:{effect:YAHOO.widget.ContainerEffect.FADE, duration:0.5} } );
  waitPanel.setHeader("Loading, please wait...");						// init waitPanel and set header
  waitPanel.setBody('<img src=' + loadingGifUrl + ' />');					// add loading image
  waitPanel.render(top.frames['table'].document.body);						// render on document (table panel)
  top.frames['table'].document.getElementById('wait_c').style.display = "none";			// waitPanel.hide() and waitPanel.show() don't work, so doing this lame thing

}); // YAHOO.util.Event.addListener(window, "load", function() 


/**
 *  Populate Fields
 */

/**
 * populateMyFields()
 * Populates the global array  myFields  and global object hash  fieldsData .
 * myFields  has all the ontology annotator fields, gotten from the html input element fields of with class 'fields', in the order they show in the table frame.
 * fieldsData  has mappings for each field to the property values in the format  fieldsData[<field>][<property>] = <value> , gotten from the html elements 'data_<field>' and splitting on comma for pairs then splitting the pairs on <space><colon><space>.
 *
 */

function populateMyFields() {								// populate myFields array based on input fields
  this.myFields = [ ];
  var inputs = document.getElementsByTagName("input");					// get all input fields
  for (var i = 0; i < inputs.length; i++ ) {						// loop through them
    if (inputs[i].className == "fields") { 						// if the class is fields
      var field = inputs[i].value;
      this.myFields.push(field); 							// add to myFields array
      fieldsData[field] = new Object();							// new hash for this field
      if (document.getElementById("data_" + field) ) {					// get data from html
        var arrData = document.getElementById("data_" + field).value.split(", "); 	// split by comma into array
        for (var j in arrData) {							// for each pair
          var match = arrData[j].match(/'(.*?)' : '(.*?)'/);				// get the key and value
          fieldsData[field][match[1]] = match[2]; } }					// set into fieldsData[field]
} } } // function populateMyFields()


/**
 *  Editor Frame
 * The editor frame contains fields for data input, field query buttons to query postgres, a reset button to reset the OA, tabs to pick which fields to show, field labels to toggle dataTable columns showing or hiding.
 *
 */

/**
 *   Query
 * All fields have a query button, clicking the query button makes an AJAX call for postgres data matching the field's input.
 *
 */

/**
 * assignQueryButtonListenerAjax(e)
 * Assigns a listener action for when a field's query button is clicked. 
 * Get the field from the event trigger id.  
 * toggle-type fields get the userValue from the backgroundColor, queryonly fields set a dummy userValue 'queryonly', other fields get the userValue from the input field.
 * If there is a userValue call  postgresQueryField(field, userValue, 0)  to query postgres to populate dataTable.
 *
 */

function assignQueryButtonListenerAjax(e) {							// if query button was clicked
  var fieldstuff = this.id.match(/button_(.*)/);						// this is event (button click)
  var field = fieldstuff[1];									// get the field name from the event id
  var userValue = "";										// userValue is what they entered in matching input
  if ( ( fieldsData[field]["type"] === "toggle" ) || ( fieldsData[field]["type"] === "toggle_text" ) ) {	// toggle fields
      if (top.frames['editor'].document.getElementById("toggle_" + field).style.backgroundColor === "red") { userValue = fieldsData[field]["label"]; } }	// if checked on the backgroundColor is red, and the value is the field's label
  else if ( fieldsData[field]["type"] === "queryonly" ) { userValue = "queryonly"; }		// if it's a queryonly field, assign a dummy value to make a query
  else if ( fieldsData[field]["type"] === "textarea" ) { 					// if it's a textarea field there is no corresponding input field
      userValue = top.frames['editor'].document.getElementById("textarea_" + field).value; }	// userValue is what they entered in matching textarea
  else {											// non toggle fields get their value from input_<field>
      userValue = top.frames['editor'].document.getElementById("input_" + field).value; }	// userValue is what they entered in matching input
  if (userValue === "") { return; }								// don't query if no input

  postgresQueryField(field, userValue, 0); 							// ajax call to query postgres by field and userValue
} // function assignQueryButtonListenerAjax(e)

/**
 * postgresQueryField(field, userValue, amountRowsToHighlight)
 * Queries postgres for a field and userValue with an AJAX query, populates the dataTable at the top and highlights <amountRowsToHighlight> from the top.
 * @param {String} field  is the field / postgres table to query postgres.
 * @param {String} userValue  is the value the curator wants to query postgres for.
 * @param {Integer} amountRowsToHighlight  is the amount of rows from the top to highlight after returning data to the dataTable.
 * Clear all dataTable selections.
 * Clear all input fields and values from the editor frame by calling  clearEditorFields(field) .
 * Define callbacks action for AJAX return.
 * Get all dataTable pgids into a comma-separated string by calling  getAllDataTableIds() .
 * Get maximum amount of records to retrieve from postgres to populate the dataTable from the editor frame html hidden input element with id 'maxPerQuery'.
 * Construct a URL for AJAX data query to the CGI with action 'jsonFieldQuery', passing the <userValue>, <curatorTwo>, <maxPerQuery>, and <allDataTableIds>.
 * Set the obo frame to have a message on what is being queried.
 * Create an html img element with id 'loadingImg' and image <loadingGifUrl>, appending it to the control frame html element with id 'loadingImage'.
 * Show the table frame html element with id 'wait_c' because waitPanel.show() doesn't work for some reason.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 * 
 */

/**
 * callbacks from postgresQueryField
 * Get back AJAX response of return message and jsonData.  Populate dataTable with jsonData and give appropriate messages.
 * On successful return do the following.
 * Parse <o.responseText> with YAHOO.lang.JSON.parse into a <jsonData> array.
 * Shift the first element from the array, it is the <returnedMessage>.
 * Add remaining jsonData to the dataTable.
 * Add <returnedMessage> to the obo frame.
 * If there is no <jsonData> give user a warning of no matches result.
 * Autoset dataTable columns's widths with YUI dataTable method validateColumnWidths().
 * Get html div elements from dataTable that have been newly added by the query. 
 * Add or remove the red_square.jpg to those html div elements depending on whether there's too much data in the cell or not (respectively) by calling  colorMoreCells(divArray) .
 * Since there's an AJAX return, remove the loading image and hide the 'wait_c' html element.
 * If there was data returned, unselect all rows ;  if there are rows to highlight, highlight them ;  load the data from the first row to the editor frame by calling  rowSelectLoadToEditor(recordData) .
 *
 */

function postgresQueryField(field, userValue, amountRowsToHighlight) {				// ajax call to query postgres by field and userValue
  myDataTable.unselectAllRows();								// unselect all datatable rows to keep editor reset from chaging values
  clearEditorFields(field);									// clear editor inputs and values, except for <field>

  var callbacks = {
      success : function (o) {									// Successful XHR response handler 
          var jsonData = [];
          try { jsonData = YAHOO.lang.JSON.parse(o.responseText); }				// Use the JSON Utility to parse the data returned from the server 
          catch (x) { alert("JSON Parse failed!"); return; } 

          var returnedMessage = jsonData.shift().returnMessage;
          myDataTable.addRows(jsonData, 0);							// this is sooooo much faster than one by one
          top.frames['obo'].document.getElementById('myObo').innerHTML = returnedMessage + "<br />";
          if (jsonData.length === 0) { alert("Query for " + userValue+ " on " + field + " found NO MATCHES"); }

          myDataTable.validateColumnWidths();							// it will run this after the callback is done, but the colorMoreCells will fail since heights won't be uneven unless it's validated column widths and rendered (?) the data into the datatable
          var divArray = [ ];									// array of divs in the newly added rows
          var rows = myDataTable.getTbodyEl().getElementsByTagName('tr')			// rows are the body tr elements
          for (var row = 0; row < jsonData.length; row++) {					// for all newly added rows, (change 0 to match addRow if changed)
            var trDivs = rows[row].getElementsByTagName('div');
            for (var div = 0; div < trDivs.length; div++) { divArray.push( trDivs[div] ); }	// add all divs in the row
          } // for (var row = 0; row < jsonData.length; row++)
          colorMoreCells(divArray);								// check and set their overflow
          top.frames['controls'].document.getElementById('loadingImg').parentNode.removeChild(top.frames['controls'].document.getElementById('loadingImg'));	// remove loadingImg element since it has loaded
          top.frames['table'].document.getElementById('wait_c').style.display = "none";		// waitPanel.hide() doesn't work, so doing this lame thing
          if (jsonData.length > 0) { 								// if there was good data added
              myDataTable.unselectAllRows();							// unselect all rows
              if (amountRowsToHighlight > 0) {							// if there are rows to highlight
                  for (var i = 0; i < amountRowsToHighlight; i++) {				// for the amount of rows to hightlight
                      myDataTable.selectRow(myDataTable.getTrEl(i)); } 				// select each of those rows for new / duplicate row
                  var recordData = myDataTable.getRecord(myDataTable.getTrEl(0))._oData;	// get record data of top row
                  rowSelectLoadToEditor(recordData); }						// load row data to editor
          } // if (jsonData.length > 0)
      },
  }; 

  var allDataTableIds = getAllDataTableIds();
  maxPerQuery = top.frames['editor'].document.getElementById("maxPerQuery").value;		// get max values returned per query (too many in the datatable make the browser really slow)

  var sUrl = cgiUrl + "?action=jsonFieldQuery&field="+field+"&userValue="+userValue+"&datatype="+datatype+"&curator_two="+curatorTwo+"&maxPerQuery="+maxPerQuery+"&allDataTableIds="+allDataTableIds;
   
  top.frames['obo'].document.getElementById('myObo').innerHTML = "query for " +userValue+ " on " + field + " ." + sUrl;

  var loadingImgElem = document.createElement("img");						// make img element loadingImg for querying data 
  loadingImgElem.setAttribute("src", loadingGifUrl);
  loadingImgElem.setAttribute("id", "loadingImg");
  top.frames['controls'].document.getElementById('loadingImage').appendChild( loadingImgElem );	// show on control panel div

  top.frames['table'].document.getElementById('wait_c').style.display = "";			// waitPanel.show() doesn't work, so doing this lame thing
			
  YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);					// Make the call to the server for JSON data 
} // function postgresQueryField(field, userValue, amountRowsToHighlight)


/**
 *   Clear Editor
 * Clear all inputs and values for all fields in the editor frame, keeping the <fieldToKeep>
 *
 */

/**
 * clearEditorFields(fieldToKeep)
 * Clear all inputs and values for all fields in the editor frame, keeping the <fieldToKeep>
 * @param {String} fieldToKeep  is the field that should not get cleared.
 * Loop through all fields:
 * - Skip the <fieldToKeep> if it matches the <field> looping through.
 * - Skip if the field type is of type 'queryonly', there is no html element to clear.
 * - Fields of type 'toggle' or 'toggle_text' have toggle fields with an html element 'toggle_<field>' that has its backgroundColor set to 'white'.
 * - Fields of type 'textarea' have an html textarea element 'textarea_<field>' that has its value set to blank ''.
 * - Fields not of type 'toggle' nor 'toggle_text' nor 'textarea' have an html input element 'input_<field>' that has its value set to blank ''.
 * - Fields of type 'multiontology' or 'multidropdown' call  removeSelectAllOptions(<elSel>)  to remove all html option elements from the field's html select element.
 * 
 */

function clearEditorFields(fieldToKeep) {
  for (var i = 0; i < myFields.length; i++ ) { 							// for each field blank editor 
      if (fieldToKeep === myFields[i]) { continue; }						// skip queried field
      if ( fieldsData[myFields[i]]["type"] === "queryonly" ) { continue; }			// skip queryonly fields
      if ( ( fieldsData[myFields[i]]["type"] === "toggle" ) || ( fieldsData[myFields[i]]["type"] === "toggle_text" ) ) {
          top.frames['editor'].document.getElementById("toggle_" + myFields[i]).style.backgroundColor = "white"; }	// set toggle_<field> tds white (blank)
      else if ( fieldsData[myFields[i]]["type"] === "textarea" ) {
          top.frames['editor'].document.getElementById("textarea_" + myFields[i]).value = ''; }	// blank input field
      else {
          top.frames['editor'].document.getElementById("input_" + myFields[i]).value = ''; }	// blank input field
      if ( ( fieldsData[myFields[i]]["type"] === "multiontology" ) || ( fieldsData[myFields[i]]["type"] === "multidropdown" ) ) {
          var elSel = top.frames['editor'].document.getElementById("select_" + myFields[i]); 	// html select element for that field's selected values
          var haveRemoved = removeSelectAllOptions( elSel ); } }				// if it's a multi-value ontology field remove all option elements from corresponding select element
} // function clearEditorFields(fieldToKeep)


/**
 *   Editor Label 
 * Field labels on the editor can be clicked to toggle the column to show or hide.  It also makes an AJAX call for postgres to store the user's preference for that datatype-field.
 *
 */

/**
 * assignEditorLabelTdListener(e)
 * Assigns a listener action for when a field's label in the editor frame is clicked.
 * Get the field from the event trigger id. 
 * Call  showHideToggle(field)  to update dataTable column state and postgres table.
 *
 */

function assignEditorLabelTdListener(e) {		// if the td of a field's label was clicked on the editor
  var fieldstuff = this.id.match(/label_(.*)/);		// this is event (button click)
  var field = fieldstuff[1];				// get the field name from the event id
  showHideToggle(field);
} // function assignEditorLabelTdListener(e)		// if the td of a field's label was clicked on the editor

/**
 * showHideToggle(field)
 * Updates dataTable and postgres oac_column_showhide table value.
 * @param {String} field  is the field whose column state should be updated.
 * Get editor frame label td html element with id 'label_<field>' ;  if the corresponding dataTable column is hidden, show it and make the style of the html td element 'black' ;  if it is not hidden, hide it and make the html td element 'grey'.
 * Call  updatePostgresShowHideColumn(field, columnShowHide)  to update the state of the column for that curator-datatype-field in the oac_column_showhide postgres table.
 *
 */

function showHideToggle(field) {
  var thisColumn = myDataTable.getColumn(field);
  columnShowHide = ''; var tdLabel = top.frames['editor'].document.getElementById('label_' + field);
  if (thisColumn.hidden) { myDataTable.showColumn(field); columnShowHide = 'visible'; tdLabel.style.color = "black"; }
    else { myDataTable.hideColumn(field); columnShowHide = 'hidden'; tdLabel.style.color = "grey"; }
  updatePostgresShowHideColumn(field, columnShowHide);
} // function showHideToggle(field)


/**
 *   Multivalue Select Element
 * Multivalue fields have a select element to store its values and a 'remove' button to remove selecte values.
 *
 */

/**
 * removeSelectAllOptions(elSel)
 * Remove all html option elements from a given html select element to clear it.
 * @param {Object} elSel  is the html select element to clear by removing all its options.
 * @return {Boolean}  is the true/false state of whether anything was removed from the html select element.
 * Loop through all <elSel> html option elements, removing them.  If any are removed set <haveRemoved> to true.
 * Resize the html select element to fit the amount of values (none) by calling  resizeSelectField(elSel) .
 * Return <haveRemoved> to pass whether anything was removed or not.
 *
 */

function removeSelectAllOptions(elSel) {	                        	// remove selected option elements from given select element
    var haveRemoved = false; 
    for (var i = elSel.length - 1; i>=0; i--) { elSel.remove(i); haveRemoved = true; } 
    resizeSelectField(elSel);
    return haveRemoved; }

/**
 * resizeSelectField(elSel)
 * Resize the html select element to exactly fit the amount of values it has. 
 * @param {Object} elSel  is the html select element to resize
 * If it has elements set the size to the amount values, otherwise make the size 1.
 *
 */

function resizeSelectField(elSel) { if (elSel.length > 0) { elSel.size = elSel.length; } else { elSel.size = 1; } }


/**
 *   Multivalue Select Remove Button
 * Multivalue fields (multiontology / multidropdown) have an html select element listing all its values.  A 'remove' html button element is needed to remove selected values. 
 *
 */

/**
 * removeSelectFieldEntriesListener(e)
 * Assigns a listener action for when a multivalue field's 'remove' html button element is clicked.
 * Get the field from the event trigger id. 
 * Get the <elSel> html select element from the editor frame element with id 'select_<field>'.
 * Call  removeSelected(elSel)  to remove the selected options.
 * If a value was removed:
 * - Blank out value of the corresponding html input element with id 'input_<field>'.
 * - Get array of rows selected in dataTable.
 * - Call  convertSelectToDatatableValue(field)  to convert <elSel> values to dataTable format.
 * - Call  updateDataTableValues(field, newValue, selectedRows)  to update postgres tables and dataTable.
 *
 */

function removeSelectFieldEntriesListener(e) {					// remove selected option elements from corresponding select element
  var fieldstuff = this.id.match(/button_remove_(.*)/);				// this is event (button click)
  var field = fieldstuff[1];							// get the field name from the event id
  var elSel = top.frames['editor'].document.getElementById("select_" + field); 	// html select element for that field's selected values
  var haveRemoved = removeSelected(elSel);					// remove selected option elements from given select element
  if (haveRemoved === true) {							// if something has been removed
    top.frames['editor'].document.getElementById("input_" + field).value = '';	// blank out corresponding input_ field
    var selectedRows = myDataTable.getSelectedRows();				// get the selectedRows from the datatable
    var newValue = convertSelectToDatatableValue(field)				// get the datatable value based on select element option values
    updateDataTableValues(field, newValue, selectedRows); }			// update selected rows for a given field to have newValue
} // function removeSelectFieldEntriesListener(e)

/**
 * removeSelected(elSel)
 * Remove all selected values from <elSel> html select element.
 * @param {Object} elSel  is the html select element for that field.
 * @return {Boolean}  is the true/false state of whether anything was removed from the html select element.
 * Loop through all <elSel> html option elements, removing any that are selected.  If any are removed set <haveRemoved> to true.
 * Resize the html select element to fit the amount of values (none) by calling  resizeSelectField(elSel) .
 * Return <haveRemoved> to pass whether anything was removed or not.
 *
 */

function removeSelected(elSel) {	                        		// remove selected option elements from given select element
    var haveRemoved = false; 
    for (var i = elSel.length - 1; i>=0; i--) { if (elSel.options[i].selected) { elSel.remove(i); haveRemoved = true; } }
    resizeSelectField(elSel);
    return haveRemoved; }


/**
 *   Tab Buttons
 * When a tab is clicked, show only fields that belong to that tab.
 *
 */

/**
 * showTab(tabClass)
 * When a tab is clicked, show only fields that belong to that tab.
 * @param {String} tabClass  is 'tab<number>' or 'all' from  fieldsData[<field>]["tab"]
 * Get all html tr elements from the editor frame.  Loop through all elements and if the className matches exactly the <tabClass>, display it ;  otherwise hide it.
 *
 */

function showTab(tabClass) {							// show only TRs in this tab
  arrTrs = top.frames['editor'].document.getElementsByTagName("tr");		// get all the trs
  for (var i = 0; i < arrTrs.length; i++) {					// for each of them
    if ( (arrTrs[i].className === tabClass) || 					// if it's the class to show 
         (arrTrs[i].className === 'all') ) { arrTrs[i].style.display = ""; }	// or class has tab set to all, show it
      else { arrTrs[i].style.display = "none"; } }				// otherwise hide it
} // function showTab(tabClass)



/**
 *   Reset Button
 * Resets ontology annotator by reloading obo frame, deleting all rows in dataTable, and clearing editor fields.  Leaves dataTable and control settings.
 *
 */

/**
 * resetButtonListener(e) 
 * Assigns a listener action for when the editor frame's 'Reset' html button element is clicked.
 * Call  resetButton()  to reset the ontology annotator.
 *
 */

function resetButtonListener(e) { resetButton(); }	// resetButton should clear datatable, editor, filters, obo ;  not reload all the frames, because that alters the column order / size.

/**
 * resetButton() 
 * Resets ontology annotator by reloading obo frame, deleting all rows in dataTable, and clearing editor fields.  Leaves dataTable and control settings.
 * Reload obo frame from server, not cache.
 * Delete all rows from dataTable.
 * Clear all input fields and values from the editor frame by calling  clearEditorFields(field) .
 *
 */

function resetButton() {
  top.frames['obo'].window.location.reload(true);	// true reloads from server, not cache
  myDataTable.deleteRows(myDataTable.getRecordSet().getLength() - 1, -1 * myDataTable.getRecordSet().getLength()); 
  clearEditorFields();					// clear all editor inputs and values
} // function resetButton()




/**
 *   Autocomplete Fields
 * Autocomplete fields can be single value or multivalue, and can be 'dropdown' or 'autocomplete'.  Multivalue fields have an html select element to store its value and a button to remove selected values.  'dropdown' fields can have a relatively small amount of values and a button to show all values.  'ontology' fields have term info to show in the obo frame.  
 *
 */

/**
 * setAutocompleteListeners()
 * Autocomplete fields (dropdown / multidropdown / ontology / multiontology) create a YUI AutoComplete object to autocomplete what the user types into the only possible values.  All Autocomplete fields are forced.  Dropdown-type fields (dropdown / multidropdown) have a button to click to show all possible options.
 * Loop through all fields, and if the  fieldsData[<field>][type]  is an autocomplete field (dropdown / multidropdown / ontology / multiontology) set autocomplete listeners by:
 * Construct a URL for AJAX autocomplete query to the CGI with action 'autocompleteXHR', passing the <field>, <datatype>, <curatorTwo>, and '&' for YUI to append the 'query' field with the value the user typed in.
 * Create <oDS> as a new YUI XHRDataSource, passing in the URL ;  with data response of type text ;  delimiting records with newlines (\n) and fields with tabs (\t) ;  and enabling caching because autocomplete values don't change often.
 * All autocompletes force data to be in the ontology, so the container element is gotten from the editor frame html div element with id 'forced<field>Container'.  The input element from the editor frame html input element with id 'input_<field>'.
 * Create <forcedOAC> as a new YUI AutoComplete ;  passing in the <inputElement>, <containerElement>, and <oDS>.  Set 'queryQuestionMark' to 'false' because the URL has been built with other value and already has an '&'.  Set 'maxResultsDisplayed' to '500' because even though most results are limited to 20 by the CGI, some GO config ontology values have hundreds that match on some terms and curatos wants to look at hundreds of them.  Set 'forceSelection' to 'false' because it doesn't seem to work, so using  checkValueIsValidAndUpdate(field, newValue, selectedRows)  instead.
 * If the field is a 'dropdown' or 'multidropdown' or 'ontology' or 'multiontology' also add a 'click' listener to the editor frame html span element with id 'type_<field>', so that when clicked it will focus on the <forcedOAC> input and send a query for blank, which returns all possible values for the field.  Set the 'minQueryLength' to 0 to allow blank queries which return all values.
 * Subscribe a <forcedOAC> itemSelectEvent to call  onAutocompleteItemSelect  to update term information, input field, postgres, and dataTable.
 * Subscribe a <forcedOAC> selectionEnforceEvent to call  onAutocompleteSelectionEnforce  to give message in obo frame about what value was cleared.
 * Subscribe a <forcedOAC> itemArrowToEvent to call  onAutocompleteItemHighlight  to show the value's term info in the obo frame if it is an ontology-type field.
 * Subscribe a <forcedOAC> itemMouseOverEvent to call  onAutocompleteItemHighlight  to show the value's term info in the obo frame if it is an ontology-type field.
 *
 */

function setAutocompleteListeners() {				// for each ontology field, add autocomplete listener
  for (var i = 0; i < myFields.length; i++ ) { 			// for each field
    var field = myFields[i];
    if ( ( fieldsData[field]["type"] === "dropdown" ) || 	// if it's a dropdown field
         ( fieldsData[field]["type"] === "multidropdown" ) || 	// or if it's a multi-value dropdown field
         ( fieldsData[field]["type"] === "ontology" ) || 	// or if it's an ontology field
         ( fieldsData[field]["type"] === "multiontology" ) ) {	// or if it's a multi-value ontology field
       settingAutocompleteListeners = function() {
         var sUrl = cgiUrl + "?action=autocompleteXHR&field=" + field + "&datatype=" + datatype + "&curator_two=" + curatorTwo + "&";	// ajax calls need curator and datatype
         var oDS = new YAHOO.util.XHRDataSource(sUrl);		// Use an XHRDataSource
         oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;	// Set the responseType
         oDS.responseSchema = {					// Define the schema of the delimited results
             recordDelim: "\n",
             fieldDelim: "\t"
         };
         oDS.maxCacheEntries = 5;				// Enable caching
     
         var forcedOrFree = "forced";
         var inputElement = top.frames['editor'].document.getElementById("input_" + field);
         var containerElement = top.frames['editor'].document.getElementById(forcedOrFree + field + "Container");
         var forcedOAC = new YAHOO.widget.AutoComplete(inputElement, containerElement, oDS);
         forcedOAC.queryQuestionMark = false;			// don't add a ? to the sUrl query since it's been built with some other values
         forcedOAC.maxResultsDisplayed = 500;
         forcedOAC.forceSelection = false;
//          if ( ( fieldsData[field]["type"] === "multidropdown" ) || ( fieldsData[field]["type"] === "dropdown" ) ) 	// dropdowns and multidropdowns should allow clicking to show all values
         if ( ( fieldsData[field]["type"] === "multidropdown" ) || ( fieldsData[field]["type"] === "dropdown" ) ||	// dropdowns and multidropdowns should allow clicking to show all values
              ( fieldsData[field]["type"] === "multiontology" ) || ( fieldsData[field]["type"] === "ontology" ) ) {	// ontologies and multiontologies also allow as some dropdowns have converted to obos for cross-form compatibility
             var oElement = top.frames['editor'].document.getElementById('type_'+field);
             YAHOO.util.Event.addListener(oElement, "click", function() { 
                 if (top.frames['editor'].document.getElementById("input_id").disabled !== true) {	// only change stuff if editor is not disabled (editor being represented by id field)
                     forcedOAC.getInputEl().focus();		// put focus on input element to keep widget active
                     forcedOAC.sendQuery(''); } });		// send a blank query to pop the box
             forcedOAC.minQueryLength = 0; }			// allow free autocomplete on these (allow blank)
         forcedOAC.itemSelectEvent.subscribe(onAutocompleteItemSelect);
         forcedOAC.selectionEnforceEvent.subscribe(onAutocompleteSelectionEnforce);	
         forcedOAC.itemArrowToEvent.subscribe(onAutocompleteItemHighlight);
         forcedOAC.itemMouseOverEvent.subscribe(onAutocompleteItemHighlight);
         return {
             oDS: oDS,
             forcedOAC: forcedOAC
         }
       }();
    }; // if ( fieldsData[field]["ontology"] )
  } // for (var i = 0; i < myFields.length; i++ )
} // function setAutocompleteListeners()

/**
 * onAutocompleteItemSelect(oSelf, elItem)
 * Get the value's id, set the obo frame to show the id's term info, set the field input to the value, and blur to call  editorInputBlurListener  to update postgres and the dataTable.
 * @param {Object} oSelf  is the YUI AutoComplete object.
 * @param {Object} elItem  is the html li element selected.
 * Get the <field> by matching on the <elSel> name.
 * Get the user <value> from the <elItem>.
 * Set the editor frame html input element with id 'input_<field>' to have value <value>, focus it, and blur it, to trigger  editorInputBlurListener .
 * If the type is 'ontology' or 'multiontology': 
 * - Initialize <id> as a copy of <value>.
 * - If the value matches as a '^<syn> ( <id> ) [<name>]$' reconstruct it as '<name> ( <id> ) '.
 * - If the value matches as  '( <id> ) ' set the <id> as the matched <id>.
 * - Set the obo frame to a <oboUrl>, the ontology_annotator.cgi with action 'oboFrame', passing the <datatype>, <curatorTwo>, <id>, and <field>.
 *
 */

function onAutocompleteItemSelect(oSelf, elItem) {		// if an autocomplete item is selected 
  var match = elItem[0]._sName.match(/input_(.*)/);		// get the field
  var field = match[1];
  var value = elItem[1].innerHTML;				// get the selected value
  top.frames['editor'].document.getElementById('input_' + field).value = value;		// assign to editor
  top.frames['editor'].document.getElementById('input_' + field).focus();		// focus to trigger editorInputBlurListener
  top.frames['editor'].document.getElementById('input_' + field).blur();		// blur to trigger editorInputBlurListener
  if ( ( fieldsData[field]["type"] === "ontology" ) || 		// if it's an ontology field 
       ( fieldsData[field]["type"] === "multiontology" ) ) {	// or if it's a multi-value ontology field
      var id = value;						// initialize the id to be the value in case there is no match in parentheses later on
      if (value.match(/^(.*?) \( (.*?) \) \[(.*?)\]$/) ) { 		// if it's a synonym convert to "name ( id ) " format
        match = value.match(/^(.*?) \( (.*?) \) \[(.*?)\]$/);
        value = match[3] + " ( " + match[2] + " ) "; }
      if (value.match(/(\( .*? \) )/)) { match = value.match(/(\( (.*?) \) )/); id = match[2]; }	// asyncTermInfo passes generic obo values with "( .* ) ", so this is consistent
      var oboUrl = cgiUrl + "?action=oboFrame&datatype="+datatype+"&curator_two=" + curatorTwo + "&term_id=" + id + "&field=" + field ;	// id has a space at the end, so can't be last value pair in url
      top.frames['obo'].location = oboUrl;
  } // if ( ( fieldsData[field]["type"] === "ontology" ) || ( fieldsData[field]["type"] === "multiontology" ) )
} // function onAutocompleteItemSelect(oSelf , elItem) 


/**
 * onAutocompleteSelectionEnforce(oSelf, sClearedValue)
 * Give message in obo frame about what value was cleared.
 * @param {Object} oSelf  is the YUI AutoComplete object.
 * @param {String} sClearedValue  is the value that was cleared.
 * Give a message in the obo frame html div element with id 'myObo' about which value was cleared by value enforcement.
 * 
 */

function onAutocompleteSelectionEnforce(oSelf, sClearedValue) { top.frames['obo'].document.getElementById('myObo').innerHTML += "cleared " + sClearedValue + " oSelf " + oSelf + " end<br/> "; }


/**
 * onAutocompleteItemHighlight(oSelf , elItem)
 * When highlighting an 'ontology' or 'multiontology' value call  asyncTermInfo(field, value)  to change the term info in the obo frame.
 * @param {Object} oSelf  is the YUI AutoComplete object.
 * @param {Object} elItem  is the html li element highlighted from mouseOver or arrowTo.
 * Get the <field> by matching on the <elSel> name.
 * If the <field> is of type 'ontology' or 'multiontology' call  asyncTermInfo(field, value)  to change the term info in the obo frame.
 * 
 */

function onAutocompleteItemHighlight(oSelf , elItem) {		// if an item is highlighted from arrows or mouseover, populate obo
  var match = elItem[0]._sName.match(/input_(.*)/);		// get the key and value
  var field = match[1];
  var value = elItem[1].innerHTML;
  if ( ( fieldsData[field]["type"] === "ontology" ) || 		// if it's an ontology field 
       ( fieldsData[field]["type"] === "multiontology" ) ) {	// or if it's a multi-value ontology field
     asyncTermInfo(field, value);
   }
} // function onAutocompleteItemHighlight(oSelf , elItem)


/**
 *   Editor Input
 * Editor fields make an automatic AJAX call to update the appropriate postgres data table, postgres history table, and ontology annotator dataTable.  'text' and 'bigtext' fields do it when blurred, 'toggle'-type fields do it when clicked, autocomplete-type fields do it when selected or clicked.
 *
 */

/**
 * editorInputBlurListener(e)
 * Assigns a listener action for when a field's html input element is blurred.
 * Get the field from the event trigger id. 
 * Call  editorFieldBlur(field, newValue)  to update postgres and dataTable.
 *
 */

function editorInputBlurListener(e) {				// editor input blurred, update corresponding values of selected rows
    var fieldstuff = e.target.id.match(/input_(.*)/);		// this is event (button click)
    var field = fieldstuff[1];					// get the field name from the event id
    var newValue = e.target.value;				// the new value from the editor input field
    editorFieldBlur(field, newValue);				// call editorFieldBlur to do all the actions
} // function editorInputBlurListener(e)

/**
 * editorFieldBlur(field, newValue)
 * Updates dataTable and postgres data table values, if appropriate.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field and pgids.
 * Get selected rows from dataTable.
 * Skip field 'id', it has no corresponding postgres table to update and its dataTable column cannot be changed.
 * Skip fields of type 'noteditable', they should not change.
 * Fields of multivalue type (multiontology / multidropdown) check values are valid and update calling  checkValueIsValidAndUpdate(field, newValue, selectedRows) .  Having a blank value doesn't matter, only what is / gets added / gets removed from html select element.  Any autocomplete value needs to be checked before update.
 * Other fields with a blank value update postgres and dataTable by calling  updateDataTableValues(field, newValue, selectedRows) .  Blank values are not valid value when checked, so update normally.
 * Fields of type 'dropdown' or 'ontology' check values are valid and update calling  checkValueIsValidAndUpdate(field, newValue, selectedRows) .  Autocomplete values need to be checked before update.
 * All other fields update postgres and dataTable by calling  updateDataTableValues(field, newValue, selectedRows) .
 *
 */

function editorFieldBlur(field, newValue) {
    var selectedRows = myDataTable.getSelectedRows();
    var validValue = true;						// if a value is valid (might not be for dropdown / ontology / multiontology
    if (field === "id") {  	 					// never allow editing of IDs
    } else if ( fieldsData[field]["noteditable"] === "noteditable" ) {	// do not allow editing of noteditable fields
    } else if ( ( fieldsData[field]["type"] === "multidropdown" ) || 	// if it's a multi-value dropdown field
                ( fieldsData[field]["type"] === "multiontology" ) ) {	// or if it's a multi-value ontology field
        if ( newValue === '' ) { return; }				// skip blank values to prevent adding blanks (which are valid from genericObo) 
        checkValueIsValidAndUpdate(field, newValue, selectedRows);	// check value before updating it
    } else if (newValue === "") {					// always update blank values (except for multivalue fields which have a remove button)
        updateDataTableValues(field, newValue, selectedRows);
    } else if ( ( fieldsData[field]["type"] === "dropdown" ) || 	// if it's a dropdown field
                ( fieldsData[field]["type"] === "ontology" ) ) {	// or if it's an ontology field
        checkValueIsValidAndUpdate(field, newValue, selectedRows);	// check value before updating it
    } else { updateDataTableValues(field, newValue, selectedRows); }	// text fields always update
} // function editorFieldBlur(field)

/**
 * editorTextareaBlurListener(e)
 * Assigns a listener action for when a field's html textarea element is blurred for fields of type 'textarea' but not 'bigtext'.
 * Get the field from the event trigger id. 
 * Call  editorFieldBlur(field, newValue)  to update postgres and dataTable.
 *
 */

function editorTextareaBlurListener(e) {			// editor input blurred, update corresponding values of selected rows
    var fieldstuff = e.target.id.match(/textarea_(.*)/);	// this is event (button click)
    var field = fieldstuff[1];					// get the field name from the event id
    var newValue = e.target.value;				// the new value from the editor input field
    editorFieldBlur(field, newValue);				// call editorFieldBlur to do all the actions
} // function editorTextareaBlurListener(e)


/**
 * checkValueIsValidAndUpdate(field, newValue, selectedRows)
 * Check whether a field's new user value is a proper autocomplete value with an AJAX call.  If it is update postgres tables and dataTable.  If it's not replaced the editor input with the last value selected in the dataTable or blank if there isn't one.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field and pgids.
 * @param {Array} selectedRows  is an array of record ids of selected dataTable rows.
 * Define callbacks action for AJAX return.
 * Call  convertDisplayToUrlFormat(newValue)  to replace any characters to escape with html URL escape characters.
 * Construct a URL for AJAX check to the CGI with action 'asyncValidValue', passing the <field>, <newValue>, <datatype>, and <curatorTwo>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from checkValueIsValidAndUpdate
 * Get back AJAX response of true / false of whether a field's new user value is a proper autocomplete value.  If it is, update postgres tables and dataTable.  If it's not, replace the editor input with the last value selected in the dataTable (or blank if there isn't one).
 * On successful return with <o.responseText> do the following.
 * If <o.responseText> is 'true' call  processValuesForDataTable(field, newValue, selectedRows)  to update postgres tables and dataTable.
 * If <o.responseText> is not 'true' get the current value from the editor frame html input element with id 'input_<field>' ;  if the <newValue> being checked is the same as was in the editor frame (the user hasn't changed the value while the AJAX call returned) ;  if the first selected record is in the dataTable, get the record, replace the html span element with parentheses, and place the value back in the editor field (The new value the user tried is not a valid autocomplete value so put back the previous value) ;  if there is no corresponding dataTable value, clear the editor input by setting the value to blank ''.
 *
 */

function checkValueIsValidAndUpdate(field, newValue, selectedRows) {		// check if a value is valid for that field
    var callbacks = {
        success : function (o) {						// Successful XHR response handler 
            if (o.responseText !== undefined) { 
                if (o.responseText === "true") { 
                    processValuesForDataTable(field, newValue, selectedRows); }	// process values to datatable format and call updateDataTable to update datatable
                else {								// force field to match obo, if it doesn't use first selected record's value
                    var currentValue = top.frames['editor'].document.getElementById("input_" + field).value;	// the value currently in the editor
                    if (currentValue === newValue) {				// if the value in the editor is the one that was being ajax valid checked
                        if (myDataTable.getRecord(selectedRows[0]) !== null) { 	// get oData from first selected record
                              // this is necessary because someone could type to autocomplete, then mouse over a selection and click it, losing editor focus
                              // and starting this ajax call which will return false, but the click will assign a new value to the editor that is correct
                              // and will start another of this ajax call which will return true.  so check the value hasn't change since the first call
                              // if the editor value is the same as the value being checked, then grab the value from the selected data table record
                            var recordData = myDataTable.getRecord(selectedRows[0])._oData;	
                            recordData[field] = recordData[field].replace(/<span style=\'display: none\'>/g, " ( "); 	
                            recordData[field] = recordData[field].replace(/<\/span>/g, " ) "); 
                            top.frames['editor'].document.getElementById("input_" + field).value = recordData[field]; }
                        else {							// set to blank
                            top.frames['editor'].document.getElementById("input_" + field).value = ""; } } }
            }
        },
    }; 
    newValue = convertDisplayToUrlFormat(newValue); 				// convert <newValue> to URL format by escaping characters
    var sUrl = cgiUrl + "?action=asyncValidValue&field="+field+"&userValue="+newValue+"&datatype="+datatype+"&curator_two="+curatorTwo;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks); 
} // function checkValueIsValidAndUpdate(field, newValue, selectedRows)

/**
 * convertDisplayToUrlFormat(value)
 * Convert value from display format to a URL format by converting characters to URL escape characters for making AJAX calls.
 * @param {String} value  is the display value to convert to URL format.
 * @return {String}  is the URL value, having been converted from the display value.
 * If there is a <value>, and it matches a character to escape (+ or #), convert all matches of the character to the html URL escape character.
 *
 */ 

function convertDisplayToUrlFormat(value) {
    if (value !== undefined) {							// if there is a display value replace stuff
        if (value.match(/\+/)) { value = value.replace(/\+/g, "%2B"); }		// replace + with escaped +
        if (value.match(/\#/)) { value = value.replace(/\#/g, "%23"); }		// replace # with escaped #
    }
    return value;								// return value in format for URL
} // function convertDisplayToUrlFormat(value)

/**
 * processValuesForDataTable(field, newValue, selectedRows)
 * Convert values to dataTable format and call  updateDataTableValues(field, newValue, selectedRows)  for AJAX call to update postgres tables and dataTable.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field.
 * @param {Array} selectedRows  is an array of record ids of selected dataTable rows, whose pgids should be updated.
 * If the field is a single autocomplete type (dropdown / ontology) replace the <newValue>'s parentheses with an html span element to hide the id in the dataTable.
 * If the field is a multi autocomplete type (multidropdown / multiontology) call  addToSelectField(field, newValue)  to add the value to the corresponding html select element ;  convert the <newValue> to dataTable display format ;  and check if <newValue> is a new value, if it already existed in the html select element there is no need to update, so return.
 * Call  updateDataTableValues(field, newValue, selectedRows)  to update postgres tables and dataTable.
 *
 */

function processValuesForDataTable(field, newValue, selectedRows) {		// process values to datatable format and call updateDataTable to update datatable
    if ( ( fieldsData[field]["type"] === "dropdown" ) || 			// if it's a dropdown field
         ( fieldsData[field]["type"] === "ontology" ) ) {			// or if it's an ontology field
         newValue = newValue.replace(/ \( /g, "<span style='display: none'>"); 	// ontology values need autocomplete to match value loaded into editor, 
         newValue = newValue.replace(/ \) /g, "</span>" ); }			// otherwise focus and blur trigger an onSelectionEnforce event
    else if ( ( fieldsData[field]["type"] === "multiontology" ) || 		// or if it's a multi-value ontology field
              ( fieldsData[field]["type"] === "multidropdown" ) ) {		// or if it's a multi-value dropdown field
         newValue = addToSelectField(field, newValue); 				// add to select element, and get the new value string for the datatable 
         if (newValue === "noChange") { return; } }				// if it hasn't changed, don't alter datatable / postgres
    updateDataTableValues(field, newValue, selectedRows);			// update selected rows for a given field to have newValue
} // function processValuesForDataTable(field, newValue, selectedRows)

/**
 * addToSelectField(field, newValue)
 * If the user's <newValue> is new, add it to the field's html select element and return the element's values in dataTable format, otherwise return 'noChange'.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field and pgids.
 * @return {String}  is 'noChange' if there was no change, or the data in the field's html select element in dataTable format.
 * Get the <elSel> html select element with id 'select_<field>' and remove all html option elements.
 * Convert value from URL format to display format by converting characters from URL escape characters back to normal characters.
 * Check if the <field>'s <newValue> is already in <elSel> by calling  checkValueInSelect(field, newValue, elSel) ;  if not, add it by:
 * - Create a new html option element, setting its text and value to <newValue>, and add it to <elSel>.
 * - Resize <elSel> to fit the amount of values with  resizeSelectField(elSel) .
 * - Blur the corresponding input field with id 'input_<field>' in the editor frame to avoid triggering a manual blur event later.  Set the value to blank ''.
 * - Call  convertSelectToDatatableValue(field)  to convert <elSel> values to dataTable format, and return these values.
 * If the <newValue> already existed in <elSel> return 'noChange'.  Do not clear the html input element because the user might have entered the value to query postgres.
 *
 */

function addToSelectField(field, newValue) {						// add to select element, and get the new value string for the datatable 
    var elSel = top.frames['editor'].document.getElementById("select_" + field);	// elSel is select element for that field
    if (newValue !== undefined) {							// if there is a display value replace stuff
        if (newValue.match(/%2B/)) { newValue = newValue.replace(/%2B/g, "+"); }	// replace escaped + with + for display in cell
        if (newValue.match(/%23/)) { newValue = newValue.replace(/%23/g, "#"); }	// replace escaped + with + for display in cell
    }
    var isInSelectFlag = checkValueInSelect(field, newValue, elSel);			// check if an editor input value is already in the corresponding select element option list
    if (isInSelectFlag === false) {							// if not in select element list, add it
        var elOptNew = document.createElement('option');
        elOptNew.text = newValue; elOptNew.value = newValue;				// set value and text to newValue
        try { elSel.add(elOptNew, null); }  						// standards compliant; doesn't work in IE
        catch(ex) { elSel.add(elOptNew); }  						// IE only
        resizeSelectField(elSel);

        top.frames['editor'].document.getElementById('input_' + field).blur();		// blur to prevent future blur from updating values
        top.frames['editor'].document.getElementById('input_' + field).value = "";	// clear input element for that field
        return convertSelectToDatatableValue(field);					// return datatable value based on select element option values
    } // if (isInSelectFlag === false)
    return "noChange";									// nothing has changed, value already existed
} // function addToSelectField(field, newValue) 

/**
 * checkValueInSelect(field, newValue, elSel)
 * Check if the <newValue> already exists in the field's html select element.  If so return 'true', if not return 'false'.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field and pgids.
 * @param {Object} elSel  is the html select element for that field.
 * @return {Boolean}  is the true/false state of whether a value already existed in an html select element.
 * Loop through all html option elements in <elSel> and if a value matches <newValue> return true.
 * If there was no match return false.
 *
 */

function checkValueInSelect(field, newValue, elSel) {			// check if an editor input value is already in the corresponding select element option list
    for (var i = elSel.length - 1; i>=0; i--) {				// for each of the elements in reverse since most likely added recently
        if (elSel.options[i].value === newValue) { return true; } }	// if new value already in select list, return true
    return false;							// not in select list, return false
} // function checkValueInSelect(field, newValue) 

/**
 * convertSelectToDatatableValue(field)
 * Get a field's corresponding html select element's values in dataTable format.
 * @param {String} field  is the field whose html select element's values should be converted to dataTable format.
 * @return {String}  is the html select element's values in dataTable format.
 * Get the <elSel> html select element with id 'select_<field>' and replace all pairs of parentheses with a set of html select element tags with style display 'none'.
 * If there are values, group all values with doublequote-comma-doublequote, wrap in doublequotes and return.  If there are no values return blank ''.
 *
 */

function convertSelectToDatatableValue(field) {						// return datatable value based on select element option values
    var arrString = new Array;								// store strings converted for datatable here
    var elSel = top.frames['editor'].document.getElementById("select_" + field);	// elSel is select element for that field, for some reason if passed in by addToSelectField, it gets an error later on that elSel.options is undefined
    for (var i = 0; i <= elSel.length - 1; i++) {					// for each option
        var string = elSel.options[i].value.replace(/ \( /g, "<span style='display: none'>"); 	
        string = string.replace(/ \) /g, "</span>" );					// ontology values need to convert id to hidden value for datatable
        arrString.push(string); }							// add string to array
    if (arrString.length > 0) { return '"' + arrString.join('","') + '"'; }		// return datatable-formated string
        else { return; }								// if no values left, return blank
} // function convertSelectToDatatableValue(field) 


/**
 * updateDataTableValues(field, newValue, selectedRows)
 * Update postgres tables and dataTable by directing to the default or batch more for AJAX call.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field.  Autocomplete values are in dataTable display format (with html span elements, not with parentheses)
 * @param {Array} selectedRows  is an array of record ids of selected dataTable rows, whose pgids should be updated.
 * The <displayValue> is the value to display in the dataTable, and it is the same as the userValue to pass through AJAX, but converts URL escapes to normal characters.
 * Get whether the user wants to use normal mode or the batch unsafe mode (which updates postgres, but does not update the dataTable because changing a lot of values is slow) by getting the editor frame html hidden input element with id 'batchUnsafeFlag'.
 * If the batch unsafe flag is selected (originally from the front page of the ontology_annotator.cgi) make changes to postgres tables (only) with an AJAX call by calling  batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue, 'noDataTable') .
//  * If the batch unsafe flag is not selected (default mode) make changes to postgres tables and dataTable with an AJAX call by calling  normalSafeUpdateDataTableValues(field, selectedRows, newValue, displayValue) .
 * If the batch unsafe flag is not selected (default mode) make changes to postgres tables and dataTable with an AJAX call by calling  normalSafeUpdateDataTableValues(field, selectedRows, newValue, displayValue, 'yesDataTable') .
 *
 */

function updateDataTableValues(field, newValue, selectedRows) {						// update selected rows for a given field to have newValue
    var displayValue = newValue;
    var batchUnsafeFlag = top.frames['editor'].document.getElementById("batchUnsafeFlag").value;	// use  normalSafeUpdateDataTableValues  by default, if checked use  batchUnsafeUpdateDataTableValues
//     if (batchUnsafeFlag) { batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue); }
//         else { normalSafeUpdateDataTableValues(field, selectedRows, newValue, displayValue); }
    if (batchUnsafeFlag) { batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue, 'noDataTable' ); }
        else {             batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue, 'yesDataTable'); }
// FUTURE FOR DANIELA  for selectedRows { if (fieldsData[field]["reloadRow"]) }   remove row from dataTable and requery it.
} // function updateDataTableValues(field, newValue, selectedRows)

/**
 * batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue, dataTableFlag)
 * Fast and 'unsafe' mode to batch update data from a lot of <selectedRows> in postgres tables with a single AJAX call, but unsafe because dataTable is not updated and there is a single error message for all errors instead of individual error messages per field-pgid-value update.
 * @param {String} field  is the field whose value should be updated.
 * @param {Array} selectedRows  is an array of record ids of selected dataTable rows, whose pgids should be updated.
 * @param {String} newValue  is the new value for that field in URL format.  Autocomplete values are in dataTable display format (with html span elements, not with parentheses)
 * @param {String} displayValue  is the same new value, but in dataTable display format.  Deprecated -- It is not used because the dataTable is not being updated because  myDataTable.updateCell(record, field, displayValue)  seems to happen quickly, but then the browser hangs for many selected rows.  Kept here in case a future update makes it faster.
 * @param {String} dataTableFlag  is whether or not to do dataTable updates (noDataTable|yesDataTable), which are slow when doing an batchUnsafe, but good when doing normal curation
 * Get all ids from dataTable selected rows and put them in an array <arrPgidsToChange> and hash <hashPgidsChanged>.  
 * If there are pgids to update, join them with comma and update postgres tables and dataTable by calling  updatePostgresTableField(pgidsToChange, field, newValue) .
 * In regular curation mode, for each selected row, if the pgid is in <hashPgidsChanged> get the record and update the dataTable cell to have the <displayValue>.
 *
 */

function batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue, dataTableFlag) {
    var arrPgidsToChange = new Array;						// store strings converted for datatable here
    var hashPgidsChanged = new Object();
    for (var i = 0; i < selectedRows.length; i++) {				// for each selected row in the data table
        var recordData = myDataTable.getRecord(selectedRows[i])._oData;		// get oData from each record
        var tableValue = recordData[field];					// get tableValue for that field
        var pgid = recordData.id;
        if (tableValue !== newValue) { hashPgidsChanged[pgid] = 1; arrPgidsToChange.push(pgid); } }	// if new value is different add to array to change
    if (arrPgidsToChange.length > 0) {						// if there are any pgids to change (otherwise will do updates on blank pgid creating blank joinkey in postgres
        var pgidsToChange = arrPgidsToChange.join(','); 			// get ids to pass to change
        updatePostgresTableField(pgidsToChange, field, newValue, dataTableFlag, selectedRows, hashPgidsChanged); }		// this happens a bit slowly as each row happens separately off of a separate ajax update
} // function batchUnsafeUpdateDataTableValues(field, selectedRows, newValue, displayValue)

/** update the dataTable display of pgids that have changed values in postgres
 * @param {String} dataTableFlag  is whether or not to do dataTable updates (noDataTable|yesDataTable), which are slow when doing an batchUnsafe, but good when doing normal curation
 * @param {String} field  is the field whose value should be updated.
 * @param {String} displayValue  is the new value for that field in URL format.  Autocomplete values are in dataTable display format (with html span elements, not with parentheses)
 * @param {Array} selectedRows  is an array of record ids of selected dataTable rows, whose pgids should be updated.
 * @param {Object} hashPgidsChanged  is a hash of pgids that changed in postgres that need changing in dataTable
 * For each selected row, get the record and pgid, if the pgid changed in postgres (hashPgidsChanged), updateCell that record to the displayValue.
 *
 */

function updateDataTableDisplay(dataTableFlag, field, displayValue, selectedRows, hashPgidsChanged) {
    if (dataTableFlag === 'yesDataTable') {
// KEEP THIS CODE BLOCK in case a future update makes  myDataTable.updateCell  faster.
// looping over selected rows still updates cell by cell which is still really slow
        for (var i = 0; i < selectedRows.length; i++) {				// for each selected row in the data table
            var recordData = myDataTable.getRecord(selectedRows[i])._oData;	// get oData from each record
            var pgid = recordData.id;
            if (pgid in hashPgidsChanged) {
                var record = myDataTable.getRecord(selectedRows[i]);		// get the record
                myDataTable.updateCell(record, field, displayValue);		// update the datatable cell, which leaves the row id the same.  this seems to happen quickly but then hangs for multiple rows at once.  guessing something slow about the way updateCell returns
   } } }
} // function updateDataTableDisplay(dataTableFlag, field, displayValue, selectedRows, hashPgidsChanged)

// /** to update postgres one by one, and update datatables all together.
//  * normalSafeUpdateDataTableValues(field, selectedRows, newValue, displayValue)
//  * Safe and default mode to update data from <selectedRows> one by one with individual AJAX calls to update postgres tables and update dataTable.
//  * @param {String} field  is the field whose value should be updated.
//  * @param {Array} selectedRows  is an array of record ids of selected dataTable rows, whose pgids should be updated.
//  * @param {String} newValue  is the new value for that field in URL format.  Autocomplete values are in dataTable display format (with html span elements, not with parentheses)
//  * @param {String} displayValue  is the same new value, but in dataTable display format.
//  * Get all ids from dataTable selected rows, and if the <newValue> is different from the corresponding dataTable value:
//  * - Call  updatePostgresTableField(pgidsToChange, field, newValue) to update postgres tables.
//  * - Update the dataTable cell to show the <displayValue>.  It's possible for this to happen even if  updatePostgresTableField  fails, but a failure there will give an error message for users to check data.
//  * - Get the html div elements corresponding to this dataTable record.
//  * - Add or remove the red_square.jpg to those html div elements depending on whether there's too much data in the cell or not (respectively) by calling  colorMoreCells(divArray) .
//  *
//  */
// 
// function normalSafeUpdateDataTableValues(field, selectedRows, newValue, displayValue) {
//     for (var i = 0; i < selectedRows.length; i++) {					// for each selected row in the data table
//         var recordData = myDataTable.getRecord(selectedRows[i])._oData;			// get oData from each record
//         var tableValue = recordData[field];						// get tableValue for that field
//         var pgid = recordData.id;
//         if (tableValue !== newValue) {							// if new value is different
//             var record = myDataTable.getRecord(selectedRows[i]);			// get the record
//             updatePostgresTableField(pgid, field, newValue);				// this happens a bit slowly as each row happens separately off of a separate ajax update
//             myDataTable.updateCell(record, field, displayValue);			// update the datatable cell, which leaves the row id the same.  this seems to happen quickly but then hangs for multiple rows at once.  guessing something slow about the way updateCell returns
//             var trId = myDataTable.getTrEl(record).id;					// get the table row id
// 	    var divArray = document.getElementById(trId).getElementsByTagName("div");	// get all divs in that table row
//             colorMoreCells(divArray);							// check and set their overflow
//         } // if (tableValue !== newValue)
//     } // for (var i = 0; i < selectedRows.length; i++)
// } // function normalSafeUpdateDataTableValues(field, selectedRows, newValue, displayValue)


/**
 * updatePostgresTableField(pgid, field, newValue, dataTableFlag, selectedRows, hashPgidsChanged)
 * Update data in postgres data tables with an AJAX call, alerting of any errors.
 * @param {String} pgid  are the comma-separated pgids that should be updated.
 * @param {String} field  is the field whose value should be updated.
 * @param {String} newValue  is the new value for that field in URL format.  Autocomplete values are in dataTable display format (with html span elements, not with parentheses)
 * @param {String} dataTableFlag  is whether or not to do dataTable updates (noDataTable|yesDataTable), which are slow when doing an batchUnsafe, but good when doing normal curation
 * @param {Array} selectedRows  is an array of record ids of selected dataTable rows, whose pgids should be updated.
 * @param {Object} hashPgidsChanged  is a hash of pgids that changed in postgres that need changing in dataTable
 * Disable the form if appropriate by calling  disableForm() .
 * Define callbacks action for AJAX return.
 * Call  convertDisplayToUrlFormat(newValue)  to replace any characters to escape with html URL escape characters.
 * Construct a URL for AJAX postgres update to the CGI with action 'updatePostgresTableField', passing the <pgid>, <field>, <newValue>, <datatype>, and <curatorTwo>.
 * If the value to update is 2000 characters or less, make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions, and store in the server log what the change was.
 * If the value to update is over 2000 characters, make a YAHOO.util.Connect.asyncRequest with method POST to avoid internet explorer 2048 character limit and apache default 8193 character limit.
 *
 */

/**
 * callbacks from updatePostgresTableField
 * Get back AJAX response of 'OK' or error message.  Undisable form if appropriate and warn of any errors in an alert window. 
 * On successful return undisable the form by calling  undisableForm() .  If the response is not 'OK' make an alert window with the <newValue>, <pgid>, <field>, and <o.responseText>.  If the response is 'OK' call  updateDataTableDisplay  to change display of values in dataTable.
 * On failure return undisable the form by calling  undisableForm()  and make an alert window with the <newValue>, <pgid>, <field>, and <o.statusText>.
 * 
 */

function updatePostgresTableField(pgid, field, newValue, dataTableFlag, selectedRows, hashPgidsChanged) {
    disableForm();
    var callbacks = { 
        success : function (o) {				// Successful XHR response handler 
            if (o.responseText === 'OK') { updateDataTableDisplay(dataTableFlag, field, newValue, selectedRows, hashPgidsChanged); }	// update dataTable display
            else { alert("ERROR not OK response for newValue " + newValue + " did not update for pgid " + pgid + " and " + field + " " + o.responseText); }
            undisableForm();
        },
        failure:function(o) {
console.log('failure responseText ' + o.responseText);
            alert("ERROR newValue " + newValue + " did not update for pgid " + pgid + " and " + field + "<br>" + o.statusText);
            undisableForm();
        },
    }; 
    newValue = convertDisplayToUrlFormat(newValue); 		// convert <newValue> to URL format by escaping characters
    if (newValue === undefined) { newValue = ''; }		// if there's no value set it to blank for length below to work
    if (newValue.length > 2000) {				// if more than 2000 characters use post
        var postData = "action=updatePostgresTableField&pgid="+pgid+"&field="+field+"&newValue="+escape(newValue)+"&datatype="+datatype+"&curator_two="+curatorTwo;
        YAHOO.util.Connect.asyncRequest('POST', cgiUrl, callbacks, postData); }	// Make the call to the server to update postgres
    else {							// if less than 2000 characters use get to track user actions in server log
        var sUrl = cgiUrl + "?action=updatePostgresTableField&pgid="+pgid+"&field="+field+"&newValue="+escape(newValue)+"&datatype="+datatype+"&curator_two="+curatorTwo;
        YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks); }	// Make the call to the server to update postgres
} // function updatePostgresTableField(pgid, field, newValue)



/**
 *  Term Info Frame
 * Given an autocomplete field and value, make an AJAX call to get the term info and display it in the obo frame.  Display various messages in the obo frame.
 *
 */

/**
 * asyncTermInfo(field, value)
 * Given an autocomplete <field> and <value>, make an AJAX call to get the term info from postgres and display in the obo frame.
 * @param {String} field  is the field whose term needs info.
 * @param {String} value  is the term that needs info. 
 * Define callbacks action for AJAX return.
 * Call  convertDisplayToUrlFormat(value)  to replace any characters to escape with html URL escape characters.
 * Construct a URL for AJAX term info query to the CGI with action 'asyncTermInfo', passing the <field>, <value>, <datatype>, and <curatorTwo>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from asyncTermInfo
 * Get back AJAX response of term information.  Display in obo frame.
 * On successful return, if there is data set the <o.responseText> to the innerHTML of the obo frame html div element with id 'termInfo'.
 *
 */

function asyncTermInfo(field, value) {
  var callbacks = { 
      success : function (o) {					// Successful XHR response handler 
          if (o.responseText !== undefined) { top.frames['obo'].document.getElementById('termInfo').innerHTML = o.responseText + "<br/> "; } }, }; 
  value = convertDisplayToUrlFormat(value); 			// convert <newValue> to URL format by escaping characters
  var sUrl = cgiUrl + "?action=asyncTermInfo&field="+field+"&userValue="+value+"&datatype="+datatype+"&curator_two="+curatorTwo;
  YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);	// Make the call to the server for term info data 
} // function function asyncTermInfo(field, value)


/**
 *  Control Frame
 * The control frame has controls to:
 * - 'Check_Data'  Check all data in the dataTable against mod-datatype specific constraints.
 * - 'Delete'  Delete all selected dataTable rows from postgres tables and dataTable.
 * - 'Duplicate'  Duplicate selected dataTable rows from postgres tables, query them into the dataTable, and select the new rows.
 * - 'New'  Create a new object entry in postgres tables, query it into the dataTable, and select that new row.
 * - Filtering for N filter pairs to only show records in the dataTable that match a text value in a given / all column(s).
 * 
 */

/**
 * checkDataButtonListener(e)
 * Assigns a listener action for when the control frame's 'Check_Data' html button element is clicked.  Makes an AJAX call passing pgids to check and adds ok message if 'OK', or pop up window if there's a message.
 * Get all dataTable pgids into a comma-separated string by calling  getAllDataTableIds() .
 * If there are no pgids in the dataTable, give a message in the obo frame html div element with id 'myObo', and return.
 * Disable the form if appropriate by calling  disableForm() .
 * Define callbacks action for AJAX return.
 * Construct a URL for AJAX postgres check to the CGI with action 'checkDataByPgids', passing the <datatype>, <curatorTwo>, and <allDataTableIds>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from checkDataButtonListener(e)
 * Get back AJAX response of 'OK' or message to display.  Undisable form if appropriate.
 * On successful return undisable the form by calling  undisableForm() .  If the response is 'OK', give a message in the obo frame html div element with id 'myObo'.  If the response is not 'OK' make a pop up window with innerHTML being the <o.responseText>.
 * On failure return undisable the form by calling  undisableForm()  and make an alert window with <allDataTableIds> and <o.statusText>.
 *
 */

function checkDataButtonListener(e) {						// if check data button was clicked check constraints by passing allDataTableIds to cgi
    var allDataTableIds = getAllDataTableIds();
    if (allDataTableIds === '') { 
        top.frames['obo'].document.getElementById('myObo').innerHTML = "checkData OK, nothing to check."; 
        return; }								// do nothing if nothing to check
    disableForm();
    var callbacks = {
        success : function (o) {						// Successful XHR response handler 
            if (o.responseText === 'OK') {					// result ok, write message
                top.frames['obo'].document.getElementById('myObo').innerHTML = "checkData OK. checked pgids " + allDataTableIds + ".</br>"; }
            else { 								// result not ok, popup window with message
                var popupWindow = window.open("", "mywindow", "location=1,status=1,scrollbars=1,width=400,height=80");
                popupWindow.focus();						// focus on window
                popupWindow.document.body.innerHTML = o.responseText; }		// write response to window
            undisableForm();
        },
        failure:function(o) {
            alert("ERROR failure from call to check data on pgids " + allDataTableIds + " " + o.statusText);
            undisableForm();
        },
    }; 
    var sUrl = cgiUrl + "?action=checkDataByPgids&datatype="+datatype+"&curator_two="+curatorTwo+"&allDataTableIds="+allDataTableIds;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks); 
} // function checkDataButtonListener(e)


/**
 * deleteRowButtonListener(e)
 * Assigns a listener action for when the control frame's 'Delete' html button element is clicked.  Makes an AJAX call passing pgids to delete ;  adds ok message if 'OK' and removes selected rows from dataTable ;  or alert message if there's an error message.
 * Get all pgids from selected dataTable rows into a comma-separated string.
 * If there are no selected row pgids, give a message in the obo frame html div element with id 'myObo', and return.
 * Disable the form if appropriate by calling  disableForm() .
 * Define callbacks action for AJAX return.
 * Construct a URL for AJAX postgres update to the CGI with action 'deleteByPgids', passing the <idsToDelete>, <datatype>, and <curatorTwo>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from deleteRowButtonListener(e)
 * Get back AJAX response of 'OK' or error message to alert.  Undisable form if appropriate.
 * On successful return undisable the form by calling  undisableForm() .  If the response is 'OK', get dataTable selected rows, delete them, and give a message in the obo frame html div element with id 'myObo' about the <idsToDelete> being deleted.  If the response is not 'OK' make an alert message with the <idsToDelete> and <o.responseText>.
 * On failure return undisable the form by calling  undisableForm()  and make an alert window with <idsToDelete> and <o.statusText>.
 *
 */

function deleteRowButtonListener(e) {					// if delete row button was clicked
    var selectedRows = myDataTable.getSelectedRows();
    var idsToDeleteArray = [ ];						// array of ids to delete
    for (var i = 0; i < selectedRows.length; i++) {			// for each selected row
        var id = myDataTable.getRecord(selectedRows[i])._oData.id;	// get id from each record
        idsToDeleteArray.push(id); }					// add id to array to delete
    var idsToDelete = idsToDeleteArray.join(',');
    if (idsToDelete === '') {
        top.frames['obo'].document.getElementById('myObo').innerHTML = "Delete OK, nothing to delete.";
        return; }							// do nothing if nothing to delete
    disableForm();
    var callbacks = { 
        success : function (o) {					// Successful XHR response handler 
            if (o.responseText === 'OK') {
                var selectedRows = myDataTable.getSelectedRows();
                for (var i = 0; i < selectedRows.length; i++) {		// for each selected row
                    myDataTable.deleteRow( selectedRows[i] ); }		// delete it
                top.frames['obo'].document.getElementById('myObo').innerHTML += "OK deleted " + idsToDelete + "</br>"; }
            else { alert("ERROR not OK response for deleting " + idsToDelete + " " + o.responseText); }
            undisableForm();
        },
        failure:function(o) {
            alert("ERROR failure from call to delete pgids " + idsToDelete + " " + o.statusText);
            undisableForm();
        },
    }; 
    var sUrl = cgiUrl + "?action=deleteByPgids&idsToDelete="+idsToDelete+"&datatype="+datatype+"&curator_two="+curatorTwo;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);		// Make the call to the server to update postgres
} // function deleteRowButtonListener(e) 


/**
 * duplicateRowButtonListener(e)
 * Assigns a listener action for when the control frame's 'Duplicate' html button element is clicked.  Makes an AJAX call passing pgids to duplicate ;  adds ok message if 'OK' and newly duplicated rows into dataTable ;  or alert message if there's an error message.
 * Get all pgids from selected dataTable rows into a comma-separated string.
 * If there are no selected row pgids, give a message in the obo frame html div element with id 'myObo', and return.
 * Disable the form if appropriate by calling  disableForm() .
 * Define callbacks action for AJAX return.
 * Construct a URL for AJAX postgres update to the CGI with action 'duplicateByPgids', passing the <idsToDuplicate>, <datatype>, and <curatorTwo>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from duplicateRowButtonListener(e)
 * Get back AJAX response of 'OK<tab> DIVIDER <tab><comma-separated pgids of duplicated rows>', or error message to alert.  Undisable form if appropriate.
 * On successful return undisable the form by calling  undisableForm() .  If the response is 'OK', get comma-separated pgids of duplicated rows, query them from postgres into the dataTable by calling  postgresQueryField('id', arrTextReturned[1], arrIdsReturned.length) , select the newly queried row, and give a message in the obo frame html div element with id 'myObo' about the <idsToDuplicate> being duplicated.  If the response is not 'OK' make an alert window with the response message.  If the <o.responseText> is undefined make an alert window with the <idsToDuplicate> and <o.responseText>.
 * On successful return undisable the form by calling  undisableForm() .  If the response message is 'OK', get pgid of duplicated rows, query pgid from postgres into the dataTable by calling  postgresQueryField('id', arrTextReturned[1], 1) , select the newly queried row, and give a message in the obo frame html div element with id 'myObo' about the pgid being created.  If the response message is not 'OK' make an 

 * On failure return undisable the form by calling  undisableForm()  and make an alert window with <idsToDuplicate> and <o.statusText>.
 *
 */

function duplicateRowButtonListener(e) {					// if duplicate row button was clicked 
    var selectedRows = myDataTable.getSelectedRows();
    var idsToDuplicateArray = [ ];						// array of ids to duplicate
    for (var i = 0; i < selectedRows.length; i++) {				// for each selected row
        var id = myDataTable.getRecord(selectedRows[i])._oData.id;		// get id from each record
        idsToDuplicateArray.push(id); }						// add id to array to duplicate
    var idsToDuplicate = idsToDuplicateArray.join(',');
    if (idsToDuplicate === '') { 
        top.frames['obo'].document.getElementById('myObo').innerHTML = "Duplicate OK, nothing to duplicate."; 
	return; }								// do nothing if nothing to duplicate
    disableForm();
    var callbacks = { 
        success : function (o) {						// Successful XHR response handler 
            if (o.responseText !== undefined) {
                var arrTextReturned = o.responseText.split("\t DIVIDER \t"); 	// split by distinct divider, get returnMessage and data
                if (arrTextReturned[0] === 'OK') {				// if the returnMessage is OK
                    var arrIdsReturned = arrTextReturned[1].split(","); 	// split by comma into array
                    postgresQueryField('id', arrTextReturned[1], arrIdsReturned.length);	// ajax call to query postgres by field 'id' and pgids
                    myDataTable.selectRow(myDataTable.getTrEl(0)); 		// select new rows
                    top.frames['obo'].document.getElementById('myObo').innerHTML += "OK duplicated " + idsToDuplicate + "</br>"; }
                else { alert("ERROR not OK response for duplicateRow " + arrTextReturned[0]); } }
            else { alert("ERROR undefined response for duplicating " + idsToDuplicate + " " + o.responseText); }
            undisableForm();
        },
        failure:function(o) {
            alert("ERROR failure from call to duplicate pgids " + idsToDuplicate + " " + o.statusText);
            undisableForm();
        },
    }; 
    var sUrl = cgiUrl + "?action=duplicateByPgids&idsToDuplicate="+idsToDuplicate+"&datatype="+datatype+"&curator_two="+curatorTwo;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);			// Make the call to the server to update postgres
} // function duplicateRowButtonListener(e)


/**
 * newRowButtonListener(e)
 * Assigns a listener action for when the control frame's 'New' html button element is clicked.  Makes an AJAX call to create a new entry for the datatype ;  adds ok message if 'OK' and newly created row into dataTable ;  or alert message if there's an error message.
 * Disable the form if appropriate by calling  disableForm() .
 * Define callbacks action for AJAX return.
 * Construct a URL for AJAX postgres update to the CGI with action 'newRow', passing the <datatype>, and <curatorTwo>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from newRowButtonListener(e)
 * Get back AJAX response of 'OK<tab> DIVIDER <tab><pgids of new row>', or error message to alert.  Undisable form if appropriate.
 * On successful return undisable the form by calling  undisableForm() .  If the response message is 'OK', get pgid of duplicated rows, query pgid from postgres into the dataTable by calling  postgresQueryField('id', arrTextReturned[1], 1) , select the newly queried row, reset the newRowAmount back to 1, and give a message in the obo frame html div element with id 'myObo' about the pgid being created.  If the response message is not 'OK' make an alert window with the response message.  If the <o.responseText> is undefined make an alert window with the <o.responseText>.
 * On failure return undisable the form by calling  undisableForm()  and make an alert window with <o.statusText>.
 *
 */

function newRowButtonListener(e) {						// if new row button was clicked
    disableForm();
    var callbacks = { 
        success : function (o) {						// Successful XHR response handler 
            if (o.responseText !== undefined) {
                var arrTextReturned = o.responseText.split("\t DIVIDER \t"); 	// split by distinct divider, get returnMessage and data
                if (arrTextReturned[0] === 'OK') {				// if the returnMessage is OK
                    postgresQueryField('id', arrTextReturned[1], 1); 		// ajax call to query postgres by field 'id' and pgid
                    myDataTable.selectRow(myDataTable.getTrEl(0)); 		// select new row
                    top.frames['controls'].document.getElementById("newRowAmount").innerHTML = '1';	// when done creating reset newRowAmount to default 1
                    top.frames['obo'].document.getElementById('myObo').innerHTML += "OK created new row " + arrTextReturned[1] + "</br>"; }
                else { alert("ERROR not OK response for newRow " + arrTextReturned[0]); } }
            else { alert("ERROR undefined response for newRow " + o.responseText); }
            undisableForm();
        },
        failure:function(o) {
            alert("ERROR failure from call to create new row " + o.statusText);
            undisableForm();
        },
    }; 
    var newRowAmount = top.frames['controls'].document.getElementById("newRowAmount").innerHTML;
    var sUrl = cgiUrl + "?action=newRow&newRowAmount="+newRowAmount+"&datatype="+datatype+"&curator_two="+curatorTwo;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);			// Make the call to the server to update postgres
} // function newRowButtonListener(e) 

/**
 *  changeNewRowAmountPromptListener(e)
 *  Assigns a listener action for when the control frame's 'newRowAmount' html span element is clicked.
 *  Call  changeNewRowAmountPrompt()  to prompt the amount the 'newRowAmount' html span element should change to.
 *  
 */

function changeNewRowAmountPromptListener(e) { changeNewRowAmountPrompt(); }

/**
 *  changeNewRowAmountPrompt()
 *  html prompt for the amount the 'newRowAmount' html span element should change to.
 *  Get the  newRowMaxAmountValue  from the html hidden input element 'newRowMaxAmountValue'.
 *  Give an html prompt requesting a number up to  newRowMaxAmountValue .
 *  If there is a value and it's parseInt value is less than  newRowMaxAmountValue  set the html span element to this new value.
 *  If there is a value and it's parseInt value is not less than  newRowMaxAmountValue  give an error alert message.
 *  
 */

function changeNewRowAmountPrompt() {
    var newRowMaxAmountValue = top.frames['controls'].document.getElementById("newRowMaxAmountValue").value;
    var promptText = "This will change the amount of rows you create with the New button, if you are sure you want to do it, enter a number up to " + newRowMaxAmountValue + " below";
    var newRowAmountValue = prompt(promptText, "");
    if (newRowAmountValue != null) {
        var newRowAmountInteger = parseInt(newRowAmountValue);
        if (newRowAmountInteger <= newRowMaxAmountValue) { top.frames['controls'].document.getElementById("newRowAmount").innerHTML = newRowAmountInteger; }
            else { alert("ERROR : You need a value no higher than " + newRowMaxAmountValue); } }
} // function changeNewRowAmountPrompt()


/**
 * updateFiltersAmountListener(e) 
 * Assigns a listener action for when the control frame's 'filtersAmount' html select element is changed.
 * Call  updateFiltersAmount()  to display that amount of filter pairs of html elements, and filter dataTable based on those filters.
 *
 */
function updateFiltersAmountListener(e) { updateFiltersAmount(); }		// changed amount of filters on select field

/**
 * updateFiltersAmount() 
 * Displays the amount of control frame filter pair html elements showing on the control frame html hidden input element with id 'filtersMaxAmount', then fitlers dataTable based on the showing pairs.
 * Gets the <filtersMaxAmount> from the control frame html hidden input element with id 'filtersMaxAmount'.
 * Gets the <filtersAmount> to display and filter on, from the selected html option element in the control frame html select element with id 'filtersAmount'.
 * Loop through the <filtersMaxAmount> of filters, and if they number less than or equal to / greater than <filtersAmount>, then display / hide the control frame html select element with id 'filterType<count>' and html input element with id 'filterValue<count>'.
 * Call  filterData()  to display the dataTable data based on the displayed filter pairs.
 *
 */

function updateFiltersAmount() {						// get max filters, get chosen amount of filters, show / hide appropriately
  var filtersMaxAmount = top.frames['controls'].document.getElementById("filtersMaxAmount").value;
  var filtersAmount = top.frames['controls'].document.getElementById("filtersAmount").options[top.frames['controls'].document.getElementById("filtersAmount").selectedIndex].value;	// the amount of filters chosen
  for (var filterCount = 1; filterCount <= filtersMaxAmount; filterCount++) {	// for max amount of filters
    if (filterCount <= filtersAmount) {						// if lower or equal than amount chosen, show it
      top.frames['controls'].document.getElementById("filterType" + filterCount).style.display = "";
      top.frames['controls'].document.getElementById("filterValue" + filterCount).style.display = ""; }
    else {									// if greter than amount chosen, hide it
      top.frames['controls'].document.getElementById("filterType" + filterCount).style.display = "none";
      top.frames['controls'].document.getElementById("filterValue" + filterCount).style.display = "none"; } }
  filterData();
} // function updateFiltersAmount()


/**
 * filterData() 
 * Display only dataTable data that matches in the showing filter pairs, for each pair matching the value to the specified field type.
 * Blank out the obo frame html div element with id 'myObo'.
 * Get <records> from dataTable.
 * Gets the <filtersAmount> to display and filter on, from the selected html option element in the control frame html select element with id 'filtersAmount'.
 * Loop through each record.  For each record get the <recordIndex> and loop through each <filtersAmount>:
 * - Get the <filterType> from the control frame html select element with id 'filterType<count>'.
 * - Get the <filterValue> from the control frame html select element with id 'filterValue<count>'.
 * - The <queryValue> is a lowercased <filterValue>.
 * - If <filterType> is 'all' use all values from <myFields>, otherwise use the <filterType>.
 * - Loop through each <filterType> value, matching a lowercased value to <queryValue> ;  if it matches flag the record to show and stop checking other <filterType> values.
 * If there are greater or equal show flags than <filtersAmount> the record matches all filters, so count it in <recordsShown> and display the html tr element containing the <recordIndex> in the dataTable ;  otherwise hide it.
 * Give a message in the obo frame html div element with id 'myObo' about how many records match.
 *
 */

function filterData() {
  top.frames['obo'].document.getElementById('myObo').innerHTML = "";
  var records = myDataTable.getRecordSet().getRecords();
  var recordsShown = 0;

  var filtersAmount = top.frames['controls'].document.getElementById("filtersAmount").options[top.frames['controls'].document.getElementById("filtersAmount").selectedIndex].value;	
										// the amount of filters chosen
  for (var i = 0; i < records.length; i++) {					// for each record (table row)
    var recordIndex = myDataTable.getRecordIndex(records[i]);
    var show = 0;								// show is an integer to compare to amount of filters
    for (var filterCount = 1; filterCount <= filtersAmount; filterCount++) {	// for each filter
      var filterTypeId = 'filterType' + filterCount;
      var filterValueId = 'filterValue' + filterCount;
      filterType = top.frames['controls'].document.getElementById(filterTypeId).value;
      filterValue = top.frames['controls'].document.getElementById(filterValueId).value;
      queryValue = filterValue.toLowerCase();
      var filterTypes = [];							// field types to filter for
      if (filterType !== "all") { filterTypes.push(filterType); }		// just one type
        else { filterTypes = myFields; }					// all the fields 
      for (var j in filterTypes) {						// for each filterType (all or a specific one)
        if (records[i].getData(filterTypes[j]) === null) { top.frames['obo'].document.getElementById('myObo').innerHTML += "ERROR null value in recordIndex : " + recordIndex + " " + i + " " + j + " " + filterTypes[j] + " <br/> "; }	
										// give error message if a record value is null
        var recordCellData = records[i].getData(filterTypes[j]).toLowerCase();
        if ((new RegExp(queryValue)).test(recordCellData)) { show++; break; }	// found a match, this filter passes and should show, no need to look at all other data in record cells.  this allows regular expressions to work for ^ and $
//         if (recordCellData.indexOf(queryValue) !== -1) { show++; break; }	// found a match, this filter passes and should show, no need to look at all other data in record cells
      } // for (var j in filterTypes)
    } // for (var filterCount = 1; filterCount <= filtersAmount; filterCount++)
    if (show >= filtersAmount) { recordsShown++; myDataTable.getTrEl(recordIndex).style.display = ""; }
      else { myDataTable.getTrEl(recordIndex).style.display = "none"; }
  } // for (var i = 0; i < records.length; i++)
  top.frames['obo'].document.getElementById('myObo').innerHTML += recordsShown + " records match.<br/> ";
} // function function filterData()

/**
 * filterDataKeyUpListener(e)
 * Assigns a listener action for when any of the control frame's html input element with id 'filterValue<count>' has a key up (release) action.
 * Call  filterData()  to display the dataTable data based on the displayed filter pairs.
 *
 */

function filterDataKeyUpListener(e) { filterData(); }


/**
 *  Data Table Frame
 * The table frame has a YUI ScrollingDataTable object used to display the curator's working data.
 *
 */

/**
 * initializeTable(myColumnDefs) 
 * Initialize dataTable column properties and action listeners.
 * @param {Array} myColumnDefs  is an array of (hash) objects, listing the fields in the order they should display dataTable columns, and holding key-value pairs of column properties.
 * Create a new YUI LocalDataSource <myDataSource>, set its responseSchema to have fields be a copy of <myFields>.
 * Create <myDataTable> as a new YUI ScrolingDataTable ;  passing its container element the id for the html div element 'myContainer' ;  <myColumnDefs> for column definitions ;  <myDataSource> for data source ;  and config parameters 'width' to '99.5%' to avoid horizontal scrollbar in frame, 'height' to '100%', and 'draggableColumns' to 'true' so columns can be reordered.
 * Call  populateMyFields();  to repopulate <myFields> because creating the scrolling data table changed the data in <myFields> into objects.
 * Call  resizeDataTable();  to resize height of dataTable header div and data row div to the frame height minus 29 pixels so a vertical frame scrollbar won't show.
 * Set listener for 'rowMouseoverEvent' to highlight row.
 * Set listener for 'rowMouseoutEvent' to unhighlight row.
 * Set listener for 'rowClickEvent' to select row.  Set additional listener to call  rowSelectLoadToEditor(recordData)  to load the row's data to the editor frame.
 * Set listener for 'columnReorderEvent' to get the order of the columns by looping through all html a elements in the html div element with id 'myContainer' and sub-looping through all the fields in <myField> to match the  fieldsData[<field>][label]  to the innerHTML of the html a element and adding to an array.  If there are fields in the array, join with comma and update postgres column table by calling  updatePostgresReorderColumn(columnOrder) .
 * Set listener for 'columnResizeEvent' to get all html th elements in the html div element with id 'myContainer', looping through all elements to find the array index <colIndex> of the element matching the target of the object that triggered the listener.  Get all html tr elements in the body of the dataTable and loop to get an array of html div elements <divArray>, and add or remove the red_square.jpg to them depending on whether there's too much data in the cell or not (respectively) by calling  colorMoreCells(divArray) .  Get the field from the column key of the element that triggered the listener, get the new column width for that field column, and update postgres column table by calling  updatePostgresResizeColumn(field, columnWidth) .
 * Loop through all fields ;  if there's a  fieldsData[<field>][columnWidth]  set the field column width to that size ;  if there's a  fieldsData[<field>][columnShowHide]  and the value is 'hidden', hide the field column in the dataTable, and set the editor frame html td element with it 'label_<field>' color to 'grey'.
 *
 */

function initializeTable(myColumnDefs) {						// initialize scrolling data table
  var myDataSource = new YAHOO.util.LocalDataSource([ ]); 
  var dataSourceFields = myFields;
  myDataSource.responseSchema = { fields: dataSourceFields };				// fields match myFields exactly
  myDataTable = new YAHOO.widget.ScrollingDataTable("myContainer", myColumnDefs, myDataSource, { width:"99.5%", height:"100%", draggableColumns:true});	// default height will be resized by resizeDataTable() to include header height;
  populateMyFields();									// somehow the new scrollingdatatable line converts the data in myFields into objects, so need to re-populate myFields array
  resizeDataTable();									// resize new table to be as big as possible without frame scrollbars

  myDataTable.subscribe("rowMouseoverEvent", myDataTable.onEventHighlightRow); 
  myDataTable.subscribe("rowMouseoutEvent", myDataTable.onEventUnhighlightRow); 
  myDataTable.subscribe("rowClickEvent", myDataTable.onEventSelectRow);			// make table rows selectable
  myDataTable.subscribe("rowClickEvent", function(oArgs) {
    var recordData = myDataTable.getRecord(oArgs.target)._oData;			// get record data
    rowSelectLoadToEditor(recordData);							// load row data to editor
  }); 
  myDataTable.subscribe("columnReorderEvent", function(oArgs) {
    var columnOrder = '';
    var arrA = document.getElementById("myContainer").getElementsByTagName("a");
    var arrOrderedFields = [];
    for (colIndex = 0; colIndex < arrA.length; colIndex++) {				// loop through the ths, tracking the column index
      for (var i = 0; i < myFields.length; i++ ) {					// for each field
        var field = myFields[i];
        if (fieldsData[field]["label"] === arrA[colIndex].innerHTML) { arrOrderedFields.push( field ); } } }
    if (arrOrderedFields.length > 0) { columnOrder = arrOrderedFields.join(','); }	// return datatable-formated string
    updatePostgresReorderColumn(columnOrder);
  });
  myDataTable.subscribe("columnResizeEvent", function(oArgs) {
    var colThEl = oArgs.target;								// get the table head element that has been resized
    var colIndex = 0;
    var arrTh = document.getElementById("myContainer").getElementsByTagName("th");
    for (colIndex = 0; colIndex < arrTh.length; colIndex++) {				// loop through the ths, tracking the column index
      if (arrTh[colIndex] === colThEl) { break; } }					// when the resized th is the looping th stop
    var divArray = [ ];									// array of divs in the column
    var rows = myDataTable.getTbodyEl().getElementsByTagName('tr')			// rows are the body tr elements
    for (var row = 0; row < rows.length; row++) {					// for all rows add the column-matching div
      divArray.push( rows[row].getElementsByTagName('div')[colIndex] ); }
    colorMoreCells(divArray);								// check and set their overflow
    var field = oArgs.column.getKey(oArgs.column);
    var columnWidth = myDataTable.getColumn(field).width + '';				// it's an Int, but will later be matched against as if it were a string, so convert to string now
    updatePostgresResizeColumn(field, columnWidth);
  });

  for (var i = 0; i < myFields.length; i++ ) {						// for each field, change column states based on field values
    var field = myFields[i];
    if (fieldsData[field]["columnWidth"]) {
      myDataTable.setColumnWidth(myDataTable.getColumn(field), parseInt(fieldsData[field]["columnWidth"])); }
    if (fieldsData[field]["columnShowHide"]) {
      var tdLabel = top.frames['editor'].document.getElementById('label_' + field);
      if (fieldsData[field]["columnShowHide"] === 'hidden') { myDataTable.hideColumn(field); tdLabel.style.color = "grey"; } }
  }
} // function initializeTable() 


/**
 * resizeDataTable()
 * Resize height of dataTable header div and data row div to the frame height minus 29 pixels so a vertical frame scrollbar won't show.
 * Set <myHeight> to the height of the client minus 29 pixels so the whole dataTable will show without a vertical frame scrollbar.
 * Get all html div elements in the html div element with id 'myContainer'.
 * Loop through all divs and if they have class 'yui-dt-bd' they refer to either the dataTable header, or the dataTable data rows, and their height should be set to <myHeight> to avoid a vertical frame scrollbar.
 *
 */

function resizeDataTable() {								// unfortunately height corresponds to height without headers, so always will need to reduce it by 30 pixels
  var myHeight = document.body.clientHeight - 29; 					// this seems as big as it can be without frame scrollbars
  var divs = document.getElementById("myContainer").getElementsByTagName("div");	// get divs under data table
  for (var i = 0; i < divs.length; i++) {						// if it's a div that holds ether the main table header or the data rows, resize the height based on frame size to avoid a vertical frame scrollbar
    if (divs[i].className == "yui-dt-bd") { divs[i].style.height = myHeight + "px"; } }
} // function resizeDataTable() 


/**
 * getAllDataTableIds
 * Get all dataTable pgids into a comma-separated string.
 * @return {String}  all the pgids corresponding to selected rows, joined in a string with commas.
 * Get all dataTable records, for each of those get the id, join them with comma, and return.
 *
 */

function getAllDataTableIds() {
  var idArray = new Array();						// hash of pg ids loaded to datatable
  var records = myDataTable.getRecordSet().getRecords();
  for (var i = 0; i < records.length; i++) {
      var recordIndex = myDataTable.getRecordIndex(records[i]);
      var recordKey = records[i].getData('id');
      idArray.push(recordKey);  					// add to idArray array
  } // for (var i = 0; i < records.length; i++)
  var allDataTableIds = idArray.join(','); 				// pass to query ids already in datatable, to only get new results
  return allDataTableIds;
} // function getAllDataTableIds()


/**
 * colorMoreCells(divArray)
 * For the html div elements passed in, see if there's more data than can show and add the red_square.jpg or remove it as appropriate.
 * @param {Array} divArray  is an array of all the html div elements in the dataTable that need color check.
 * Loop through all html div elements to color, and for those of class 'yui-dt-liner' do the following:
 * If the scrollHeight is not the same as the clientHeight, add to the html div element the class 'hidden-overflow-data' to show the red_square.jpg from the ontology_annotator.css .
 * If they are the same, remove it instead.
 *
 */

function colorMoreCells(divArray) {						// cells that have hidden data in overflow should have different background
  for (var i = 0, len = divArray.length; i < len; ++i) { 
      if (YAHOO.util.Dom.hasClass(divArray[i], "yui-dt-liner") ) {		// if it has the class has yui-dt-liner
          if (divArray[i].scrollHeight !== divArray[i].clientHeight) {		// if overflow is overwritten to hidden, comparing scrollHeight and clientHeight checks if there's overflow
              if (!( YAHOO.util.Dom.hasClass(divArray[i], 'hidden-overflow-data') )) {
                  YAHOO.util.Dom.addClass(divArray[i], "hidden-overflow-data"); } }
          else {
              if ( YAHOO.util.Dom.hasClass(divArray[i], 'hidden-overflow-data') ) {
                  YAHOO.util.Dom.removeClass(divArray[i], 'hidden-overflow-data'); } }
  } }
} // function colorMoreCells(divArray)


/**
 * rowSelectLoadToEditor(recordData)
 * Load last selected dataTable <recordData> into the editor frame's inputs and values.
 * @param {Object} recordData  is the YAHOO.widget.Record object to load into the editor frame's inputs and values.
 * Loop through all fields, get the value from  recordData[<field>] and depending on the  fieldsData[<field>][type]  load differently.
 * Skip all fields that are 'queryonly', they have nothing to load.
 * Autocomplete fields (dropdown / ontology / multidropdown / multiontology) convert the html span element into parentheses.
 * MultiAutocomplete fields call  populateSelectFieldFromDatatable(<field>, <value>)  to populate the html select element.
 * Toggle-type fields set the 'toggle_<field>' element background color to 'red' for data and 'white' for no data.
 * Textarea fields sets the 'textarea_<field>' html textarea element to <value>3
 * Bigtext fields sets the 'textarea_bigtext_<field>' html textarea element to blank '', and 'input_<field>' html input element to <value>.
 * All fields get the value of 'input_<field>' html input element set to <value>.
 *
 */

function rowSelectLoadToEditor(recordData) {					// load row data to editor
//     var pgid = recordData.id;						// temp to debug some editor field values not getting replaced with blanks  2014 02 20
//     top.frames['obo'].document.getElementById('termInfo').innerHTML = 'PGID to load : ' + pgid + ' END<br/>';
    for (var i = 0; i < myFields.length; i++ ) {				// for each field set the editor input to the row's cell's value
        var value = recordData[myFields[i]];
        if (value === undefined) { value = ''; }				// if there is no value in the dataTable, set it to blank, otherwise sometimes deditor won't replace value with blank because it's undefined 
//         top.frames['obo'].document.getElementById('termInfo').innerHTML += myFields[i] + ' value : ' + value + ' END<br/>';	// temp to debug some editor field values not getting replaced with blanks  2014 02 20
        if ( fieldsData[myFields[i]]["type"] === "queryonly" ) { continue; }	// skip queryonly fields
        if ( ( fieldsData[myFields[i]]["type"] === "dropdown" ) || 		// if it's a dropdown field
             ( fieldsData[myFields[i]]["type"] === "multidropdown" ) ||		// or if it's a multi-value dropdown field
             ( fieldsData[myFields[i]]["type"] === "ontology" ) || 		// or if it's an ontology field
             ( fieldsData[myFields[i]]["type"] === "multiontology" ) ) {	// or if it's a multi-value ontology field
             value = value.replace(/<span style=\'display: none\'>/g, " ( "); 	// ontology values need autocomplete to match value loaded into editor, otherwise focus and blur trigger an onSelectionEnforce event
             value = value.replace(/<\/span>/g, " ) "); 
        }
        if ( ( fieldsData[myFields[i]]["type"] === "multiontology" ) || ( fieldsData[myFields[i]]["type"] === "multidropdown" ) ) {
										// if it's a multi-value ontology or dropdown field clear input, select, populate based on value
            populateSelectFieldFromDatatable(myFields[i], value); }
        else if ( ( fieldsData[myFields[i]]["type"] === "toggle" ) || ( fieldsData[myFields[i]]["type"] === "toggle_text" ) ) {		
										// toggle fields need to change color of value
            if (value !== "") { 
                top.frames['editor'].document.getElementById("toggle_" + myFields[i]).style.backgroundColor = "red"; }
            else {
                top.frames['editor'].document.getElementById("toggle_" + myFields[i]).style.backgroundColor = "white"; } }
        else if ( fieldsData[myFields[i]]["type"] === "textarea" ) {
            top.frames['editor'].document.getElementById("textarea_" + myFields[i]).value = value; }	// load input
        else if ( fieldsData[myFields[i]]["type"] === "bigtext" ) {
            top.frames['editor'].document.getElementById("textarea_bigtext_" + myFields[i]).value = '';	// clear textarea
            top.frames['editor'].document.getElementById('input_' + myFields[i]).value = value; }	// load input
        else {
            top.frames['editor'].document.getElementById('input_' + myFields[i]).value = value; }	// load input
    } // for (var i = 0; i < myFields.length; i++ )
} // function rowSelectLoadToEditor(recordData)

/**
 * populateSelectFieldFromDatatable(field, value)
 * Load <value> into the <field>'s corresponding html select element, and clear the corresponding html input element.
 * @param {String} field  is the field whose corresponding html select element should load values.
 * @param {String} value  has the comma-separated data to load into the html select element.
 * Set the 'input_<field>' value to blank ''.
 * Get the 'select_<field>' html select element and remove all html option elements.
 * Strip out leading and trailing doublequotes from value, split on comma to get individual values.
 * For each individual value create an html option element with that for text and value and append to the html select element.
 * Resize the html select element to fit the amount of values by calling  resizeSelectField(elSel) .
 *
 */

function populateSelectFieldFromDatatable(field, value) {				// get datatable-style value and populate corresponding select element options list
    top.frames['editor'].document.getElementById('input_' + field).value = "";		// clear input element for that field
    var elSel = top.frames['editor'].document.getElementById("select_" + field);	// elSel is select element for that field
// if (field === "person") { top.frames['obo'].document.getElementById('myObo').innerHTML += "field " + field + " value " +  value + " end<br/> "; }
    for (var i = elSel.length - 1; i>=0; i--) { elSel.remove(i); }			// clear select element
    if (value === "") { return; }			 				// nothing to add if no value
    value = value.replace(/^\"/, ""); 	value = value.replace(/\"$/, ""); 		// strip surrounding doublequotes
    var arrData = new Array;								// new array to store values
    if (value.match(/","/)) { arrData = value.split('","'); }				// split by  doublequote comma doublequote  into array
    else { arrData.push(value); }							// if just one value, push it
   
    for (var i = 0; i < arrData.length; i++) { 						// for each data value from datatable
        var elOptNew = document.createElement('option');				// new option
        elOptNew.text = arrData[i]; elOptNew.value = arrData[i];			// set value and text to corresponding value
        try { elSel.add(elOptNew, null); }  						// standards compliant; doesn't work in IE
        catch(ex) { elSel.add(elOptNew); }  						// IE only
    } // for (var i = 0; i < arrData.length; i++)
    resizeSelectField(elSel);
} // function populateSelectFieldFromDatatable(field, value)


/**
 *   DataTable Column
 * Changing the state of dataTable columns automatically store the state for the curator-datatype-field in the corresponding oac_column_<type> postgres table.  The types to store are order of fields, show-hide column state, and column's width in pixels.
 *
 */

/**
 * updatePostgresReorderColumn(columnOrder)
 * @param {String} columnOrder  is a comma-separated string with the fields in column order.
 * Calls  updatePostgresColumn(columnOrder, null, 'columnOrder')  to update the column order in postgres.
 *
 */

/**
 * updatePostgresShowHideColumn(field, columnState)
 * @param {String} field  is the field whose column state should be updated.
 * @param {String} columnState  is a string stating whether the new column state is 'visible' or 'hidden'.
 * Calls  updatePostgresColumn(columnState, field, 'columnShowHide')  to update the show-hide column state in postgres.
 *
 */

/**
 * updatePostgresResizeColumn(field, columnWidth)
 * @param {String} field  is the field whose column state should be updated.
 * @param {String} columnState  is a string (converted earlier from an Int) with the new column width in pixels.
 * Calls  updatePostgresColumn(columnWidth, field, 'columnWidth')  to update the column width in postgres.
 *
 */

function updatePostgresReorderColumn(columnOrder) { 		updatePostgresColumn(columnOrder, null, 'columnOrder'); }
function updatePostgresShowHideColumn(field, columnState) {	updatePostgresColumn(columnState, field, 'columnShowHide'); }
function updatePostgresResizeColumn(field, columnWidth) { 	updatePostgresColumn(columnWidth, field, 'columnWidth'); }

/**
 * updatePostgresColumn(newValue, field, columnAction)
 * @param {String} newValue  is the new value for the column's column action.
 * @param {String} field  is the field whose column state should be updated.
 * @param {String} columnAction  is the type of column action taken, to specify which postgres table to update.
 * Disable the form if appropriate by calling  disableForm() .
 * Define callbacks action for AJAX return.
 * Call  convertDisplayToUrlFormat(newValue)  to replace any characters to escape with html URL escape characters.
 * Construct a URL for AJAX postgres update to the CGI with action 'updatePostgresColumn', passing the <columnAction>, <datatype>, <curatorTwo>, <field>, and <newValue>.
 * Make a YAHOO.util.Connect.asyncRequest with method GET to the constructed URL with callbacks actions.
 *
 */

/**
 * callbacks from updatePostgresColumn
 * Get back AJAX response of 'OK' or error message.  Undisable form if appropriate and warn of any errors in an alert window. 
 * On successful return undisable the form by calling  undisableForm() .  If the response is not 'OK' make an alert window with the <field>, <columnAction>, <newValue>, <curatorTwo>, and <o.responseText>.
 * On failure return undisable the form by calling  undisableForm()  and make an alert window with the <field>, <columnAction>, <newValue>, <curatorTwo>, and <o.statusText>.
 *
 */

function updatePostgresColumn(newValue, field, columnAction) {
    disableForm();
    var callbacks = {
        success : function (o) {				// Successful XHR response handler 
            if (o.responseText === 'OK') { } 			// it's ok, don't say anything
            else { alert("ERROR not OK response for column setting change field " + field + " columnAction " + columnAction + " newValue " + newValue + " curatorTwo " + curatorTwo + " o.responseText " + o.responseText); }
            undisableForm();
        },
        failure:function(o) {
            alert("ERROR failure for column setting change field " + field + " columnAction " + columnAction + " newValue " + newValue + " curatorTwo " + curatorTwo + "<br>" + o.statusText);
            undisableForm();
        },
    }; 
    newValue = convertDisplayToUrlFormat(newValue); 		// convert <newValue> to URL format by escaping characters
    var sUrl = cgiUrl + "?action=updatePostgresColumn&column_action="+columnAction+"&datatype="+datatype+"&curator_two="+curatorTwo+"&field="+field+"&newValue="+escape(newValue);
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);	// Make the call to the server to update postgres
} // function updatePostgresColumn(curatorTwo, newValue, field, columnAction)



/**
 *  Disable Form
 */

/**
 * disableForm()
 * This used to disable the dataTable, editor, and controls ;  but it was removed curators complained that when updating multiple rows in normal mode the dataTable would 'flash' because of the quick disabling (greying out) and undisabling (normal).
 *
 */

function disableForm() {							// disable myDataTable, input fields of editor, controls
// KEEP THIS CODE BLOCK in case curators ever want disabling back
//     myDataTable.disable();
//     for (var i = 0; i < myFields.length; i++ ) {								// for all fields
//         if (top.frames['editor'].document.getElementById('input_' + myFields[i])) {				// if there's an input field
//             top.frames['editor'].document.getElementById('input_' + myFields[i]).disabled = true; } }	// disable input field
//   top.frames['controls'].document.getElementById('newRow').disabled = true;
//   top.frames['controls'].document.getElementById('duplicateRow').disabled = true;
//   top.frames['controls'].document.getElementById('deleteRow').disabled = true;
//   top.frames['controls'].document.getElementById('checkData').disabled = true;
//   top.frames['controls'].document.getElementById("filtersAmount").disabled = true;
//   var filtersMaxAmount = top.frames['controls'].document.getElementById("filtersMaxAmount").value;
//   for (var filterCount = 1; filterCount <= filtersMaxAmount; filterCount++) {				// for max amount of filters
//       top.frames['controls'].document.getElementById("filterValue" + filterCount).disabled = true;
//       top.frames['controls'].document.getElementById("filterType" + filterCount).disabled = true; }
} // function disableForm()

/**
 * undisableForm()
 * This used to undisable the dataTable, editor, and controls ;  but it was removed curators complained that when updating multiple rows in normal mode the dataTable would 'flash' because of the quick disabling (greying out) and undisabling (normal).
 *
 */

function undisableForm() {							// undisable myDataTable, input fields of editor, controls
// KEEP THIS CODE BLOCK in case curators ever want undisabling back
//     myDataTable.undisable();
//     for (var i = 0; i < myFields.length; i++ ) {								// for all fields
//         if (top.frames['editor'].document.getElementById('input_' + myFields[i])) {				// if there's an input field
//             top.frames['editor'].document.getElementById('input_' + myFields[i]).disabled = false; } }	// undisable input field
//   top.frames['controls'].document.getElementById('newRow').disabled = false;
//   top.frames['controls'].document.getElementById('duplicateRow').disabled = false;
//   top.frames['controls'].document.getElementById('deleteRow').disabled = false;
//   top.frames['controls'].document.getElementById('checkData').disabled = false;
//   top.frames['controls'].document.getElementById("filtersAmount").disabled = false;
//   var filtersMaxAmount = top.frames['controls'].document.getElementById("filtersMaxAmount").value;
//   for (var filterCount = 1; filterCount <= filtersMaxAmount; filterCount++) {				// for max amount of filters
//       top.frames['controls'].document.getElementById("filterValue" + filterCount).disabled = false;
//       top.frames['controls'].document.getElementById("filterType" + filterCount).disabled = false; }
} // function undisableForm()



// END

// DEPRECATED FUNCTIONS THAT COULD BE USEFUL LATER
// this was used to get the current date to set the lastupdate field in the GO config.
// function getSimpleDate() {
//     var currentTime = new Date()
//     var month = currentTime.getMonth() + 1
//     var day = currentTime.getDate()
//     var year = currentTime.getFullYear()
//     if (month < 10) { month = '0' + month; }
//     if (day < 10) { day = '0' + day; }
//     return year + '-' + month + '-' + day;
// }

// this was used for checking data to count number of objects in dataTable for paper and nbp, and is no longer needed now that checkDataButtonListener(e) does an AJAX call instead.
// Object.size = function(obj) {			// get the size of a hash (amount of keys)
//     var size = 0, key;
//     for (key in obj) {
//         if (obj.hasOwnProperty(key)) size++;
//     }
//     return size;
// };
