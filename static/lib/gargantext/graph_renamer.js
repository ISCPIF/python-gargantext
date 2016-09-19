var coocId = null ;
var coocName = null ;

var graphNameBox = document.getElementById("graph-name")
var changeNameText = 'type name here'

// initial tests
var coocIdMatch = window.location.search.match(/cooc_id=(\d+)/)

if (! coocIdMatch) {
  console.error("could not find cooc_id in url (this graph is not saved in DB yet): can't show the rename input")
  $('#graph-rename').remove()
}
else {
  // we got a real COOCCURRENCES node
  coocId = parseInt(coocIdMatch.pop())

  // check if has a name already
  garganrest.nodes.get(coocId, testName)
}


// HELPER FUNCTIONS
// ----------------
function testName(jsonNode) {
  var aName = jsonNode.name
  // names like "GRAPH EXPLORER COOC (in:4885)" are default so counted as null
  if (! aName || aName.match(/^GRAPH EXPLORER COOC/)) {
    // there's no real name => leave the page editable
    coocName = null
  }
  else {
    // we got a real name => just fill it in the page
    coocName = aName
    showName(coocName, graphNameBox)
  }
  console.warn('coocName for this graph:', coocName)
}

function makeEditable(textElement, callback) {
    var newInput  = '<input id="graphname-edit" type="text"'
      newInput +=   ' value="'+changeNameText+'"';
      newInput +=   ' onfocus="return cleanInput(this)"';
      newInput +=   ' onblur="return refillInput(this)"';
      newInput +=   ' onkeypress="return checkEnterKey(event,submitName,this)"';
      newInput += '></input>';

    textElement.innerHTML = newInput
}
function cleanInput(inputElement) {
  if (inputElement.value == changeNameText) {inputElement.value = ''}
}
function refillInput(inputElement) {
  if (inputElement.value == '') {inputElement.value = changeNameText}
}
// binding for the input submitting
function checkEnterKey(e, callback, element) {
  if(e.which == 13) { callback(element) }
}

function submitName(inputElement) {
  console.warn ("renaming: using coocId =", coocId)

  var newName = inputElement.value

  // the element where we'll show the response
  var messagePopBox = document.getElementById("handmade-popover")
  var messagePopTxt = document.getElementById("handmade-popover-content")

  messagePopBox.classList.remove("hide")
  messagePopTxt.innerHTML = "Submitting..."

  var myData = new FormData();
  myData.append("name", newName)

  console.log("myData.get('name')",myData.get('name'))
  $.ajax({
      url: '/api/nodes/' + coocId ,
      type: 'POST',
      contentType: false,
      processData: false,
      data: myData,
      beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
      },
      success: function(result) {
        messagePopTxt.innerHTML  = '<h5 style="margin:.3em 0 0 0">OK saved !</h5>'
        showName(newName, graphNameBox)
        setTimeout(function(){messagePopBox.classList += ' hide'}, 2000);
      },
      error: function(result) {
        messagePopTxt.innerHTML  = '<span style="color:red">Error:</span>'
        messagePopTxt.innerHTML += '<i>'+result.statusText+'</i>'
        if (result.status == 409) {
          messagePopTxt.innerHTML += '<br/>(name is already taken!)'
        }
        setTimeout(function(){messagePopBox.classList += ' hide'}, 2000);      }
  });
}

function showName(nameStr, target) {
  target.innerHTML = '"'+nameStr+'"'
}
