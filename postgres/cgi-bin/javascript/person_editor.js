// See interspersed ScriptDoc documentation.
//
// See  oa_old_commented_out_code/  for versions change history and commented-out code.


var myFields = new Array();			// the data fields, for some reason the elements get replaced by objects when datatable gets created
var fieldsData = new Object();
var myLineageFields = new Array();		// the fields corresponding to lineage columns
var cgiUrl = "person_editor.cgi";


YAHOO.util.Event.addListener(window, "load", function() { 			// on load get fields, assign listeners
  populateMyFields();								// populate myFields array
  var fields = myFields.join('","')
//   alert(fields);
  setFieldListeners();								// for each ontology field, add autocomplete listener

  var whichPage = document.getElementById("which_page").value;
  if (whichPage === 'createNewPerson') {					// add a redirect to page of newly created person after trying to create it
    if (document.getElementById('redirect_to').value) {
      window.location = document.getElementById('redirect_to').value; }
  }

}); // YAHOO.util.Event.addListener(window, "load", function() 


function populateMyFields() {							// populate myFields array based on input fields
  this.myFields = [ ];
  var inputs = document.getElementsByTagName("input");				// get all input fields
  for (var i = 0; i < inputs.length; i++ ) {					// loop through them
    if (inputs[i].className == "fields") { 					// if the class is fields
      var field = inputs[i].value;
      this.myFields.push(field); 						// add to myFields array
      fieldsData[field] = new Object(); }					// new hash for this field
    else if (inputs[i].className == "lineage_fields") {				// if the class is fields
      var field = inputs[i].value;
      this.myLineageFields.push(field);	}					// add to myFields array
} } // function populateMyFields()


// function toggleDivToInput(field, joinkey, order) {
//   document.getElementById('div_' + field + '_' + joinkey + '_' + order).style.display='none';
//   document.getElementById('input_' + field + '_' + joinkey + '_' + order).style.display='';
//   document.getElementById('input_' + field + '_' + joinkey + '_' + order).focus();
// } // function toggleDivToInput(field, joinkey, order)
// 
// function toggleInputToDiv(field, joinkey, order) {
//     var divElement = document.getElementById('div_' + field + '_' + joinkey + '_' + order);
//     var inputElement = document.getElementById('input_' + field + '_' + joinkey + '_' + order);
//     divElement.style.display = '';
//     inputElement.style.display = 'none';
//     if (divElement.innerHTML !== inputElement.value) {
//         divElement.innerHTML = inputElement.value;
//         updatePostgresTableField(field, joinkey, order, inputElement.value);
//     }
// } // function toggleInputToDiv(field, joinkey, order)

function updatePostgresTableField(field, joinkey, order, newValue) {
    var callbacks = { 
        success : function (o) {				// Successful XHR response handler 
//             if (o.responseText === 'OK') { window.location.reload(false); } 		// reload page if successful, but it's a problem that selecting autocomplete blurs the field before loading the autocomplete value
            if (o.responseText === 'OK') { } 			// it's ok, don't say anything
            else { alert("ERROR not OK response for newValue " + newValue + " did not update for joinkey " + joinkey + " and " + field + " " + o.responseText); }
        },
        failure:function(o) {
            alert("ERROR newValue " + newValue + " did not update for joinkey " + joinkey + " and " + field + "<br>" + o.statusText);
        },
    }; 
    var curatorTwo = document.getElementById('curator_two').value;
    newValue = convertDisplayToUrlFormat(newValue); 		// convert <newValue> to URL format by escaping characters
    var sUrl = cgiUrl + "?action=updatePostgresTableField&joinkey="+joinkey+"&field="+field+"&newValue="+escape(newValue)+"&order="+order+"&curator_two="+curatorTwo;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);	// Make the call to the server to update postgres
} // function updatePostgresTableField(field, joinkey, order, newValue)

function convertDisplayToUrlFormat(value) {
    if (value !== undefined) {							// if there is a display value replace stuff
        if (value.match(/\+/)) { value = value.replace(/\+/g, "%2B"); }		// replace + with escaped +
        if (value.match(/\#/)) { value = value.replace(/\#/g, "%23"); }		// replace # with escaped #
    }
    return value;								// return value in format for URL
} // function convertDisplayToUrlFormat(value)

function moveDataToOldTable(field, order) {					// some tables have data tables and corresponding old data and old timestamp tables, this moves it from data to the old tables and deletes from data table.  2011 08 31
  var joinkey = document.getElementById("person_joinkey").value;
  var tsId = 'timestamp_' + field + '_' + order;
  var timestamp = document.getElementById(tsId).value;
  var valueId = 'input_' + field + '_' + order;
  var value = document.getElementById(valueId).value;
  var oldField = 'old_' + field; 
  if (field === 'lab') { oldField = 'oldlab'; }
  var oldOrderId = 'highest_' + oldField + '_order';
  var highestOldOrder = document.getElementById(oldOrderId).value;
//   alert("joinkey " + joinkey + " field " + field + " order " + order + " value " + value + " timestamp " + timestamp + " highestOldOrder " + highestOldOrder);
  updatePostgresTableField(oldField, joinkey, highestOldOrder, value);
  updatePostgresTableField(field, joinkey, order, '');
  if ( (field === 'institution') || (field === 'email') ) {			// these have a corresponding date to transfer
    var oldTsField = oldField + '_date'; if (field === 'institution') { oldTsField = 'old_inst_date'; }
    updatePostgresTableField(oldTsField, joinkey, highestOldOrder, timestamp); }
//   window.location.reload(false);	// cannot reload because it will not get back ajax responses
} // function moveDataToOldTable(e)

function editorCheckboxClickListener(e) {                           // editor input blurred, update corresponding values of selected rows
    var fieldstuff = e.target.id.match(/input_(.*)_(.*)/);           // this is event (button click)
    var field = fieldstuff[1];                                  // get the field name from the event id
    var order = fieldstuff[2];                                  // get the field name from the event id
    var newValue = e.target.value;                              // the new value from the editor input field
    if (e.target.checked === false) { newValue = ''; }
// alert('newValue ' + newValue + ' changed ' + field + ' f o ' + order + ' state ' + state + ' end');
    editorFieldBlur(field, order, newValue);                           // call editorFieldBlur to do all the actions
} // function editorCheckboxClickListener(e)

function editorInputBlurListener(e) {                           // editor input blurred, update corresponding values of selected rows
    var fieldstuff = e.target.id.match(/input_(.*)_(.*)/);           // this is event (button click)
    var field = fieldstuff[1];                                  // get the field name from the event id
    var order = fieldstuff[2];                                  // get the field name from the event id
    var newValue = e.target.value;                              // the new value from the editor input field
// alert('newValue ' + newValue + ' changed ' + field + ' f o ' + order + ' end');
    editorFieldBlur(field, order, newValue);                           // call editorFieldBlur to do all the actions
} // function editorInputBlurListener(e)

function editorFieldBlur(field, order, newValue) {
  var joinkey = document.getElementById("person_joinkey").value;
  updatePostgresTableField(field, joinkey, order, newValue);
//   alert("field " + field + " order " + order + " joinkey " + joinkey + " newValue " + newValue + " end");	// do not uncomment this, the alert will pop before the selected autocomplete value goes into the input field, which makes the newValue be the partially typed entry
} // function editorFieldBlur(field)

function lineageInputBlurListener(e) {                           // editor input blurred, update corresponding values of selected rows
  var fieldstuff = e.target.id.match(/cur_(.*)_(.*)/);           // this is event (button click)
  var column = fieldstuff[1];                                  // get the column name from the event id
  var order = fieldstuff[2];                                  // get the field name from the event id
  var newValue = e.target.value;                              // the new value from the editor input field
// alert('newValue ' + newValue + ' changed ' + column + ' f o ' + order + ' end');
  var oldValue = document.getElementById("old_" + column + "_" + order).value;
  if (oldValue !== newValue) { lineageUpdate(column, newValue, oldValue, order); }
} // function editorInputBlurListener(e)

function lineageDropdownChangeListener(e) {                           // editor input blurred, update corresponding values of selected rows
  var fieldstuff = e.target.id.match(/cur_(.*)_(.*)/);           // this is event (button click)
  var column = fieldstuff[1];                                  // get the column name from the event id
  var order = fieldstuff[2];                                  // get the field name from the event id
  var newValue = ''; var oElement = document.getElementById("cur_" + column + "_" + order);
  if (oElement.selectedIndex > -1) {                                                        // if there's a selected value
    newValue = oElement.options[oElement.selectedIndex].value; }  
// alert('newValue ' + newValue + ' changed ' + column + ' f o ' + order + ' end');
  var oldValue = document.getElementById("old_" + column + "_" + order).value;
  if (oldValue !== newValue) { lineageUpdate(column, newValue, oldValue, order); }
} // function editorDropdownChangeListener(e)

function lineageUpdate(column, newValue, oldValue, order) {
  var joinkey = document.getElementById("person_joinkey").value;
//   alert('newValue ' + newValue + ' oldValue ' + oldValue + ' changed ' + column + ' f o ' + order + ' end');
  var urlParams = '';
  for (var i = 0; i < myLineageFields.length; i++ ) { 		// for each lineage field
    var pairColumn = myLineageFields[i];
    var pairValue = document.getElementById("old_" + pairColumn + "_" + order).value;
    pairValue = convertDisplayToUrlFormat(pairValue); 		// convert <pairValue> to URL format by escaping characters
    urlParams += '&' + pairColumn + '=' + pairValue;
  }  
//   alert(urlParams + ' newValue ' + newValue + ' oldValue ' + oldValue + ' changed ' + column + ' f o ' + order + ' end');
  updatePostgresLineageData(column, joinkey, order, newValue, urlParams);
  document.getElementById("old_" + column + "_" + order).value = newValue;	// set new value to the old hidden input for future change
} // function lineageUpdate(column, newValue, oldValue, order)

function updatePostgresLineageData(column, joinkey, order, newValue, urlParams) {
    var callbacks = { 
        success : function (o) {				// Successful XHR response handler 
//             if (o.responseText === 'OK') { window.location.reload(false); } 		// reload page if successful, but it's a problem that reloading the page doesn't change the select dropdown values, and full reloading sets the page to the top
            if (o.responseText === 'OK') { } 			// it's ok, don't say anything
            else { alert("ERROR not OK response for lineage update " + newValue + " did not update for joinkey " + joinkey + " and " + column + " and " + order + " " + o.responseText); }
        },
        failure:function(o) {
            alert("ERROR newValue " + newValue + " did not update lineage for joinkey " + joinkey + " and " + column + " and " + order + "<br>" + o.statusText);
        },
    }; 
    var curatorTwo = document.getElementById('curator_two').value;
    newValue = convertDisplayToUrlFormat(newValue); 		// convert <newValue> to URL format by escaping characters
    var sUrl = cgiUrl + "?action=updatePostgresLineageData&joinkey="+joinkey+"&column="+column+"&newValue="+escape(newValue)+"&curator_two="+curatorTwo+urlParams;
    YAHOO.util.Connect.asyncRequest('GET', sUrl, callbacks);	// Make the call to the server to update postgres
} // function updatePostgresLineageData(column, joinkey, urlParams, newValue)

function setFieldListeners() {				// for each ontology field, add autocomplete listener
  var toAlert;
  for (var i = 0; i < myLineageFields.length; i++ ) { 		// for each lineage field
    var field = myLineageFields[i];
    if (document.getElementById("type_input_" + field) === null) { alert( "no type_input " + field ); }
    var typeInput = document.getElementById("type_input_" + field).value;
    if (document.getElementById("highest_order_lineage") === null) { alert( "no highest_order " + field ); }
    var highestOrder = document.getElementById("highest_order_lineage").value;
    for (var order = 1; order < parseInt(highestOrder) + 1; order++ ) { 	// for each order
      var oElement = document.getElementById("cur_" + field + "_" + order);
      if (typeInput === 'input') {
        YAHOO.util.Event.addListener(oElement, "blur", lineageInputBlurListener ); }		// add the listener function
      else if (typeInput === 'dropdown') {
        YAHOO.util.Event.addListener(oElement, "change", lineageDropdownChangeListener ); }	// add the listener function
    } // for (var order = 1; order < parseInt(highestOrder) + 1; order++ )	// for each order
  } // for (var i = 0; i < myLineageFields.length; i++ ) 	// for each lineage field

  for (var i = 0; i < myFields.length; i++ ) { 			// for each field
    var field = myFields[i];
    if (document.getElementById("type_input_" + field) === null) { alert( "no type_input " + field ); }
    var typeInput = document.getElementById("type_input_" + field).value;
    if (document.getElementById("highest_order_" + field) === null) { alert( "no highest_order " + field ); }
    var highestOrder = document.getElementById("highest_order_" + field).value;
// toAlert += "field " + field + " highestOrder " + highestOrder + " " + " typeInput " + typeInput + " ";
    for (var order = 1; order < parseInt(highestOrder) + 1; order++ ) { 	// for each order
      var inputElement = document.getElementById("input_" + field + "_" + order);
      if (inputElement === null) { continue; }

        // Editor Blur Listener
      if ( document.getElementById("which_page").value === 'displayPersonEditor' ) {
        var oElement = document.getElementById("input_" + myFields[i] + "_" + order);
// toAlert += "field " + field + " order " + order + "\n";
        if (typeInput === 'input') {
            YAHOO.util.Event.addListener(oElement, "blur", editorInputBlurListener ); }	// add the listener function
          else if (typeInput === 'checkbox') {
            YAHOO.util.Event.addListener(oElement, "click", editorCheckboxClickListener ); }
      } // if ( document.getElementById("which_page").value === 'displayPersonEditor' )

        // Autocomplete Listener
      if (typeInput === 'input') {				// input fields have autocomplete
        settingAutocompleteListeners = function() {
// toAlert += "SAL field " + field + " order " + order + " ";
          var sUrl = cgiUrl + "?action=autocompleteXHR&field=" + field + "&order=" + order + "&";	// ajax calls need curator and datatype
          var oDS = new YAHOO.util.XHRDataSource(sUrl);		// Use an XHRDataSource
          oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;	// Set the responseType
          oDS.responseSchema = {					// Define the schema of the delimited results
              recordDelim: "\n",
              fieldDelim: "\t"
          };
          oDS.maxCacheEntries = 5;				// Enable caching
          var forcedOrFree = "free";
//           var inputElement = document.getElementById("input_" + field);
//           var containerElement = document.getElementById(forcedOrFree + field + "Container");
          var inputElement = document.getElementById("input_" + field + "_" + order);
          var containerElement = document.getElementById(forcedOrFree + field + order + "Container");
          var forcedOAC = new YAHOO.widget.AutoComplete(inputElement, containerElement, oDS);
          forcedOAC.queryQuestionMark = false;			// don't add a ? to the sUrl query since it's been built with some other values
          forcedOAC.maxResultsDisplayed = 500;
          forcedOAC.forceSelection = false;
//           toAlert += "field " + field + " order " + order + " ";
          forcedOAC.itemSelectEvent.subscribe(onAutocompleteItemSelect);
          return {
              oDS: oDS,
              forcedOAC: forcedOAC
          }
        }();
      } // if (typeInput === 'input')
    } // for (var order = 0; order < highestOrder; order++ )
  } // for (var i = 0; i < myFields.length; i++ ) 		// for each field
//   alert(toAlert);
} // function setFieldListeners()

function onAutocompleteItemSelect(oSelf, elItem) {		// if an autocomplete item is selected 
  var match = elItem[0]._sName.match(/input_(.*)_(.*)/);		// get the field
  var field = match[1];						// get the field name from the event id
  var order = match[2];						// get the field name from the event id
  document.getElementById('input_' + field + '_' + order).focus();		// focus to trigger editorInputBlurListener
  document.getElementById('input_' + field + '_' + order).blur();		// blur to trigger editorInputBlurListener
//   alert("field " + field + " order " + order + " end");	
} // function onAutocompleteItemSelect(oSelf , elItem) 

function showInstitutionsWithDataOnly() {
  var maxInstitutions = document.getElementById("max_institutions").value;
  for (var i = 2; i < maxInstitutions; i++ ) {			// loop through them, but not the first one, that should always show
    if (document.getElementById("input_institution_"+i).value !== "") { document.getElementById('table_'+i).style.display = ""; }	// if it has no institution data, hide the table
      else { document.getElementById("table_"+i).style.display = "none"; } }  	// if it has institution data, show the table
} // function showInstitutionsWithDataOnly()
