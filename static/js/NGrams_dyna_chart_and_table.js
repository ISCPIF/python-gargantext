/**
 * @fileoverview
 * Manages behavior of the terms view (at: project/PID/corpus/CID/terms)
 *   - the ngrams table with normal/keep/delete states
 *   - the ngrams groupings
 *   - the score chart
 * 
 * Main_test() is the entry point. A dynatable is the main UI element.
 * 
 * Dynatable uses <thead> for columns and ulWriter() for row formatting.
 * 
 * Here, the user can modify DB lists by toggling Ngrams states and 
 * save to DB via the API in the functions SaveLocalChanges() and CRUD()
 * 
 * Local persistence of states is in AjaxRecord[tableId].state
 *   (access by table ids, *not* ngram ids)
 * 
 * Their values are initialized in the functions AfterAjax() and Refresh().
 * 
 * The stateIds are described by the System object.
 *   - columns use stateId [0..2]  (miam aka normal, map aka keep, stop aka delete)
 *   - stateId 3 is for grouped items (TODO clarify use)
 * 
 * @author
 *   Samuel Castillo (original 2015 work)
 *   Romain Loth (minor 2016 modifications + doc)
 *
 * @version 1.0 beta
 * 
 * @requires jquery.dynatable
 * @requires d3
 */


function pr(msg) {
    console.log(msg)
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


var latest,oldest;

var TheBuffer = false

var PossibleActions = [
	{
	  "id":"delete",
	  "name": "Delete",
	  "color":"red"
	}, 
	{
	  "id":"keep",
	  "name": "Keep",
	  "color":"green"
	}, 
	// {
	//   "id":"to_group",
	//   "name": "Group",
	//   "color":"blue"
	// }
]

var GState = 0
var System = {
	// 1: {
	// },
	0: {
		"states" : [ "normal" , "keep" , "delete" , "group"] ,
		"statesD" : {} , // will be inverted map of states
		"dict" : {
			"normal": {
			  "id":"normal",
			  "name": "Normal",
			  "color":"black"
			}, 
			"delete": {
			  "id":"delete",
			  "name": "Delete",
			  "color":"red"
			}, 
			"keep": {
			  "id":"keep",
			  "name": "Keep",
			  "color":"green"
			}, 
			"group": {
			  "id":"group",
			  "name": "MainForm",
			  "color":"white"
			}
		}
	}
	
}


// States : [ "normal" , "keep" , "delete"]


/**
 * inverted mapping useful for state_id lookup
 * 
 * System[GState]["statesD"] = {'normal':0,'keep':1,'delete':2,'group':3}
 */
for(var i in System[GState]["states"] ) {
	System[GState]["statesD"][ System[GState]["states"][i] ] = Number(i)
}

var FlagsBuffer = {}
for(var i in System[GState]["states"]) {
  FlagsBuffer[System[GState]["states"][i]] = {}
}

var corpusesList = {}
var MyTable;
var RecDict={};
var AjaxRecords = []

//      D3.js: Interactive timerange variables.
var LineChart = dc.lineChart("#monthly-move-chart"); 
var volumeChart = dc.barChart("#monthly-volume-chart");


// Get all projects and corpuses of the user
function GetUserPortfolio() {
    //http://localhost:8000/api/corpusintersection/1a50317a50145
    var project_id = getIDFromURL("project")
    var corpus_id =  getIDFromURL("corpus")

    if( Object.keys( corpusesList ).length > 0 ) {
      $('#corpuses').modal('show');
      return true;
    }

    var query_url = window.location.origin+'/api/userportfolio/project/'+project_id+'/corpuses'
    $.ajax({
        type: 'GET',
        url: query_url,
        success : function(data) {
            
            var html_ = ""
            html_ += '<div class="panel-group" id="accordion_">'+"\n"
            html_ += ' <form id="corpuses_form" role="form">'+"\n"
            corpusesList = data;
            for (var k1 in data) {
                var v1 = data[k1]
                html_ += '  <div class="panel panel-default">'+"\n"
                html_ += '   <div class="panel-heading">'+"\n"
                html_ += '    <h4 class="panel-title">'+"\n"
                html_ += '     <a data-toggle="collapse" data-parent="#accordion_" href="#collapse_'+k1+'">'+v1["proj_name"]+'</a>'+"\n"
                html_ += '    </h4>'+"\n"
                html_ += '   </div>'+"\n"
                html_ += '   <div id="collapse_'+k1+'" class="panel-collapse collapse">'+"\n"
                html_ += '    <div class="panel-body">'+"\n"
                html_ += '     <ul>'+"\n"
                for(var c in v1["corpuses"]) {
                    var Ci = v1["corpuses"][c]
                    if( Ci["id"]!= corpus_id) {
                        html_ += '      <li>'+"\n"
                        html_ += '       <div class="radio">'+"\n"
                        html_ += '        <label><input type="radio" id="'+k1+"_"+c+'" name="optradio">'+"\n"
                        html_ += '         <a target="_blank" href="/project/'+k1+'/corpus/'+Ci["id"]+'/">'+Ci["name"] +' ('+Ci["c"]+' docs.)</a>'+"\n"
                        html_ += '        </label>'+"\n"
                        html_ += '       </div>'+"\n"
                        html_ += '     </li>'+"\n"
                    }
                }
                html_ += '     </ul>'+"\n"
                html_ += '    </div>'+"\n"
                html_ += '   </div>'+"\n"
                html_ += '  </div>'+"\n"
            }

            html_ += ' </form>'+"\n"
            html_ += '</div>'+"\n"

            $("#user_portfolio").html( html_ )
            $('#corpuses_form input:radio').change(function() {
               $("#add_corpus_tab").prop("disabled",false)
               var selected = $('input[name=optradio]:checked')[0].id.split("_")
               var sel_p = selected[0], sel_c=selected[1]
               $("#selected_corpus").html( "<center>"+data[sel_p]["proj_name"] + " , " + data[sel_p]["corpuses"][sel_c]["name"]+"</center><br>" )

            });

            $('#corpuses').modal('show');
        },
        error: function(){ 
            pr('Page Not found: TestFunction()');
        }
    });
}

//Getting a corpusB-list and intersecting it with current corpusA-miamlist. 
function printCorpuses() {
    console.log( "!!!!!!!! in printCorpuses() !!!!!!!! " )
    pr(corpusesList)

    var selected = $('input[name=optradio]:checked')[0].id.split("_")
    var sel_p = selected[0], sel_c=selected[1]

    var current_corpus =  getIDFromURL("corpus")

    var selected_corpus = corpusesList[sel_p]["corpuses"][sel_c]["id"]
    pr("current corpus: "+current_corpus)
    var the_ids = []
    the_ids.push( current_corpus )
    the_ids.push( corpusesList[sel_p]["corpuses"][sel_c]["id"] )

    $("#closecorpuses").click();

    // EXTERNAL CORPUS TO COMPARE:
    var whichlist = $('input[name=whichlist]:checked').val()
  	var url = window.location.origin+"/api/node/"+selected_corpus+"/ngrams/list/"+whichlist//+"?custom"
  	console.log( url )


  	GET_( url , function(results) {
  		if(Object.keys( results ).length>0) {
         var sub_ngrams_data = {
           "ngrams":[],
           "scores": $.extend({}, NGrams["main"].scores)
         }
        for(var i in NGrams["main"].ngrams) {
          if( results[ NGrams["main"].ngrams[i].id] ) {
            var a_ngram = NGrams["main"].ngrams[i]
            sub_ngrams_data["ngrams"].push( a_ngram )  
          }
          // if( results[ NGrams["main"].ngrams[i].id] && NGrams["main"].ngrams[i].name.split(" ").length==1 ) {
          //   if( NGrams["map"][ NGrams["main"].ngrams[i].id] ) {
          //     var a_ngram = NGrams["main"].ngrams[i]
          //     // a_ngram["state"] = System[0]["statesD"]["delete"]
          //     sub_ngrams_data["ngrams"].push( a_ngram )  
          //   }
          // }
        }
        var result = Main_test(sub_ngrams_data , NGrams["main"].scores.initial , "filter_all")
  	// 		var sub_ngrams_data = {
  	// 			"ngrams":[],
  	// 			"scores": $.extend({}, NGrams["main"].scores)
  	// 		}

  	// 		if(whichlist=="stop") {
  	// 			for(var r in results) {
  	// 				var a_ngram = results[r]
  	// 				a_ngram["state"] = System[0]["statesD"]["delete"]
  	// 				sub_ngrams_data["ngrams"].push( a_ngram )
  	// 			}
  	// 			var result = Main_test(sub_ngrams_data , NGrams["main"].scores.initial , "filter_stop-list")
  	// 		}

  	// 		if(whichlist=="miam") {
  	// 			for(var i in NGrams["main"].ngrams) {
  	// 				var local_ngram = NGrams["main"].ngrams[i]
  	// 				console.log( local_ngram )
  	// 			}
  	// 			var result = Main_test(sub_ngrams_data , NGrams["main"].scores.initial , "filter_all")
  	// 		}
    	
  		}
  	});
}


function Push2Buffer( NewVal ) {
    if ( TheBuffer == false) {
        if( ! NewVal ) {
            var limits = [ oldest , latest ];
            NewVal = limits;
        }
        console.log( " - - - - - - " )
        console.log( "\tchanging to:" )
        console.log( NewVal )
        TheBuffer = NewVal;
        Final_UpdateTable( "changerange" )
        console.log( "- - - - - - -\n" )
        return 1;
    }

    if ( TheBuffer != false ) {
        var past = TheBuffer[0]+"_"+TheBuffer[1]

        if( ! NewVal ) {
            var limits = [ oldest , latest ];
            NewVal = limits;
        }
        var now = NewVal[0]+"_"+NewVal[1]
        
        if ( past != now ) {
            console.log( " - - - - - - " )
            console.log( "\tchanging to:" )
            console.log( NewVal )
            TheBuffer = NewVal;
            Final_UpdateTable( "changerange" )
            console.log( "- - - - - - -\n" )
        }
        return 1;
    }
}

function Final_UpdateTable( action ) {
    // debug
    // console.log("\nFUN Final_UpdateTable()")
    // (1) Identifying if the button is collapsed:   
    var isCollapsed=false;
    var accordiontext = $("#collapseOne").attr("class")
    if(accordiontext.indexOf("collapse in")>-1) 
        isCollapsed=true;


    var UpdateTable = false
    if ( (action == "click" && !isCollapsed) || (action=="changerange" && isCollapsed) ) {
        UpdateTable = true;
        $("#corpusdisplayer").html("Close Term List")
    } else $("#corpusdisplayer").html("Show Term List")

    pr("update table??: "+UpdateTable)

    if ( ! UpdateTable ) return false; //stop whatever you wanted to do.



    var TimeRange = AjaxRecords;

    var dataini = (TheBuffer[0])?TheBuffer[0]:oldest;
    var datafin = (TheBuffer[1])?TheBuffer[1]:latest;
    pr("show me the pubs of the selected period")
    pr("\tfrom ["+dataini+"] to ["+datafin+"]")
    pr("\tfrom ["+oldest+"] to ["+latest+"]")

    TimeRange = []
    for (var i in AjaxRecords) {
        if(AjaxRecords[i].score>=dataini && AjaxRecords[i].score<=datafin){
            // pr( AjaxRecords[i].date+" : "+AjaxRecords[i].id )
            TimeRange.push(AjaxRecords[i])
        }
    }
    
    MyTable = $('#my-ajax-table').dynatable({
        dataset: {
            records: TimeRange
        },
        features: {
            pushState: false,
            // sort: false
        },
        writers: {
          _rowWriter: ulWriter
          // _cellWriter: customCellWriter
        }
    });
    MyTable.data('dynatable').settings.dataset.originalRecords = []
    MyTable.data('dynatable').settings.dataset.originalRecords = TimeRange;
    
    MyTable.data('dynatable').paginationPage.set(1);
    MyTable.data('dynatable').process();
}

function getRecord(rec_id) {
  return MyTable.data('dynatable').settings.dataset.originalRecords[rec_id];
  // return AjaxRecords[rec_id]
}

function getRecords() {
  return MyTable.data('dynatable').settings.dataset.originalRecords;
}

function save_groups() {
	var groupdiv = "#group_box"
	var gcontent = groupdiv+"_content"
	var count = 0
	var mainform = -1
	var writeflag = ($("#group_box_content").children('span').length>1)?true:false
	$(gcontent).children('span').each(function () {
		var nid = $(this).data("id");
		if (count==0) {
			if(writeflag) {
				// AjaxRecords[RecDict[nid]].name += "*" 
				FlagsBuffer["group"][ nid ] = []
				mainform = nid
	    		AjaxRecords[RecDict[nid]].state = 1
	    		var label = AjaxRecords[RecDict[nid]].name
	    		AjaxRecords[RecDict[nid]].name = (label[0]=="*") ? label : ("*"+label)

	    	} else {
	    		AjaxRecords[RecDict[nid]].state = 0;
	    		// var label = AjaxRecords[RecDict[nid]].name
	    		// AjaxRecords[RecDict[nid]].name = (label[0] == '*') ? label.slice(1) : label.name;
	    	}
	    } else {
			if(writeflag) {
				FlagsBuffer["group"][ mainform ].push( nid )
	    		AjaxRecords[RecDict[nid]].state = -1
			}
	    }
	    count++
	});
	$("#group_box").remove()
	$("#group_flag").remove()
	GState=0
	MyTable.data('dynatable').dom.update();
}

function cancel_groups() {
	var groupdiv = "#group_box"
	var gcontent = groupdiv+"_content"
	$(gcontent).children('span').each(function () {
	    var nid = $(this).data("id");
	    AjaxRecords[RecDict[nid]].state = 0
		var label = AjaxRecords[RecDict[nid]].name
		AjaxRecords[RecDict[nid]].name = (label[0] == '*') ? label.slice(1) : label;
	});
	$("#group_box").remove()
	$("#group_flag").remove()
	GState=0
	MyTable.data('dynatable').dom.update();
}

function add2groupdiv( elem_id ) {
	$('<span/>', {
		"data-id":AjaxRecords[elem_id].id,
		"data-stuff": elem_id,
	    title: 'Click to remove',
	    text: AjaxRecords[elem_id].name,
	    css: {
	    	"cursor":"pointer",
	    	"border": "1px solid blue",
	    	"margin": "3px",
	    	"padding": "3px",
	    }
	})
	.click(function() {
    	AjaxRecords[$(this).data("stuff")].state=0;
    	$(this).remove()
    	// if nothing in group div, then remove it
    	if( $("#group_box_content").children().length==0 ) {
    		$("#group_box").remove()
    		GState=0
    	}
    	MyTable.data('dynatable').dom.update();
	})
	.appendTo('#group_box_content')
	AjaxRecords[elem_id].state=3;// 3: "group" state
}
// new
function add2group ( elem ) {
	if( $("#group_box").length==0 ) {
		var div_name = "#my-ajax-table > thead > tr > th:nth-child(1)"
		var prctg = $(div_name).width()// / $(div_name).parent().width() * 100;
		var group_html =  '      <span class="group_box" style="max-width:'+prctg+'px;" id="group_box">'+'\n';
			group_html += '        <span class="group_box content" id="group_box_content"></span>'+'\n';
			group_html += '      </span>'+'\n';
			group_html += '      <span id="group_flag"></span>'+'\n';
			$(group_html).insertAfter( "#my-ajax-table > thead" )
			$("#group_flag").append  ('<span onclick="save_groups()"> [ Ok</span> - <span onclick="cancel_groups()">No ] </span>')
	}
	GState=1

	var elem_id = $( elem ).data("stuff")
	add2groupdiv( elem_id )
	if( FlagsBuffer["group"][ AjaxRecords[elem_id].id ] ) {
		for(var i in FlagsBuffer["group"][ AjaxRecords[elem_id].id ] ) {
			var nodeid = FlagsBuffer["group"][ AjaxRecords[elem_id].id ][i]
			add2groupdiv ( RecDict[ nodeid ] )
		}
	}

	delete FlagsBuffer["group"][ AjaxRecords[elem_id].id ]

	MyTable.data('dynatable').dom.update();
}


/**
 * click red, click keep, click normal...
 * 
 * @param elem - the table row that contains the term cell
 */
function clickngram_action ( elem ) {
    // local id
	var elem_id = $( elem ).data("stuff") ;
    console.log("click: state before: "+ AjaxRecords[elem_id].state) ;
    
    // cycle the statuses (omitting status 3 = group)
	AjaxRecords[elem_id].state = (AjaxRecords[elem_id].state==(System[0]["states"].length-2))?0:(AjaxRecords[elem_id].state+1);
    
    // State <=> term color <=> checked colums
    
    console.log("\n\nRECORD visible on click --- " + JSON.stringify(AjaxRecords[elem_id])) ;
    
    var ngramId = AjaxRecords[elem_id].id ;
        
    console.log("click: state after: "+ AjaxRecords[elem_id].state) ;
	MyTable.data('dynatable').dom.update();
}

/**
 * Works for ulWriter. Connects a record's state with table UI outcome.
 * 
 * @param rec_id - the local id for this ngram record in AjaxRecords
 */
function transformContent(rec_id) {
  // debug
  // console.log("\nFUN transformContent() !!!!")
	var ngram_info = AjaxRecords[rec_id];
  
  // ex: ngram_info = {
  //             "id":2349,"name":"failure","score":1,"flag":false,
  //             "group_plus":true,"group_blocked":false,"state":0
  //            }
  
  // console.log(
  //   "transformContent got ngram_info no " + rec_id + ": " 
  //   + JSON.stringify(ngram_info)
  // )
    
    
    // result {} contains instanciated column html for dynatables
	var result = {}
	var atts = System[0]["dict"][ System[0]["states"][ngram_info.state] ]
	var plus_event = ""
    
    
    // GState = 1 if previously had add_group
    // it influences state lookup
	if(GState==0 && ngram_info.state!=System[0]["statesD"]["delete"] ) // if deleted, no + button
		plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(+)</a>"
	if(GState==1 ) {
		if(ngram_info.state!=System[0]["statesD"]["delete"] && ngram_info.state!=System[0]["statesD"]["group"]) { // if deleted and already group, no Up button
			plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(▲)</a>"
		}
	}
	
    // uncomment if column tableId
    // result['rec_id'] = rec_id ;
    
    // uncomment if column ngramId
    // result["ngramId"] = ngram_info["id"] ;
    
    // uncomment if column state
    // result["state"] = AjaxRecords[rec_id].state
    
    // -------------------------------------------
    // check box state columns 'will_be_map' and 'will_be_stop'
    
    map_flag = (AjaxRecords[rec_id].state == 1) ;    // 1 = System[0]["statesD"]["keep"]
    stop_flag = (AjaxRecords[rec_id].state == 2) ;   // 2 = System[0]["statesD"]["delete"]
    
    result["will_be_map"] = '<input type="checkbox" onclick="checkBox(\'keep\',this.parentNode.parentNode)" '
                           +(map_flag?'checked':'')
                           +'></input>'
    result["will_be_stop"] = '<input type="checkbox" onclick="checkBox(\'delete\', this.parentNode.parentNode)" '
                           +(stop_flag?'checked':'')
                           +'></input>'
    // possible todo: 3 way switch ?? 
    // par exemple http://codepen.io/pamgriffith/pen/zcntm
    // -------------------------------------------
    
    result["score"] = '<span class="'+atts.id+'">'+ngram_info["score"]+'</span>'
	result["name"] = "<span class=\""+atts.id+
					 "\" onclick=\"clickngram_action(this.parentNode.parentNode)\">"+ngram_info["name"]+"</span>"+
					 plus_event
	return result;
}


/**
 * Click on a checkbox in a row
 * 
 * @boxType : 'keep' or 'delete' (resp. maplist and stoplist)
 * @elem : entire element row with attribute 'data-stuff' (= rec_id)
 */
 
function checkBox(boxType, elem) {
    console.log ('CLICK on check box') ;
    
    var elemId = elem.getAttribute("data-stuff") ;
    var ngramId = AjaxRecords[elemId].id ;
    var currentState = AjaxRecords[elemId].state ;
    // alert('ELEMENT: ' + elemId + '\n'
    //        + 'NGRAM: ' + ngramId + '\n'
    //        + 'CURRENT STATE: ' + currentState) ;
    
    // find out which box
    // if (boxType == 'keep') => affectedState = 1
    // if (boxType == 'delete') => affectedState = 2
    affectedState = System[0]["statesD"][boxType] ;
    
    // turn on if it's not already on
    if (currentState != affectedState) {
        targetState = affectedState
    }
    // otherwise turn the 2 boxes off
    else {
        targetState = 0 ;
    }
    
    // set old state and color
    AjaxRecords[elemId].state = targetState ;
    MyTable.data('dynatable').dom.update();
}

/**
 * "generic enough"
 * 
 * Writes a row for each datum 
 * (function passed to dynatable config "writers" property)
 * @eachData
 * 
 * @param rowIndex: int i++
 * @param record: { "id":1793,"name":"planet","score":1,"flag":false,
 *                   "group_plus":true,"group_blocked":false,
 *                   "state":0}
 * @param columns: constant array 
 *                 (with column template for cellWriter)
 *                 (auto-built from html <thead> elements)
 *              ex: [
 *                  {"index":0,"label":"Terms","id":"name",
 *                   "sorts":["name"],"hidden":false,
 *                   "textAlign":"left","cssClass":false},
 *                  {"index":1,"label":"Score","id":"score",
 *                   "sorts":["score"],"hidden":false,
 *                   "textAlign":"left","cssClass":false}
 *                  ]
 */
function ulWriter(rowIndex, record, columns, cellWriter) {
  // debug
  // console.log("\nFUN ulWriter()")
  var tr = '';
  var cp_rec = {}
  
  if( AjaxRecords[RecDict[record.id]].state < 0 ) {
      return false;
  }
  
  // Add cells content (values OR custom html) from record
  // -----------------------------------------------------
  cp_rec = transformContent(RecDict[record.id])
  
  // console.log("cp_rec" + JSON.stringify(cp_rec))
  // console.log("\n----\nrecord" + JSON.stringify(record))
  
  // grab the record's attribute for each column
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }
  
  // we could directly use record.id (ngram_id) if store states separately
  var data_id = RecDict[record.id]
  return '<tr data-stuff='+data_id+'>' + tr + '</tr>';
}

/**
 * SelectAll: toggle all checkboxes in a row by changing state in System
 * 
 * (new version without the old Delete|Keep radio choice)
 * @boxType : 'keep' or 'delete' (resp. maplist and stoplist)
 * @elem : entire element row with attribute 'data-stuff' (= rec_id)
 */
 
function SelectAll(boxType, boxElem ) {
  // debug
  // console.log("\nFUN SelectAll()")

    // we will need status of the other "check all box"
    if (boxType == 'keep') { otherBoxId = "delAll" ; }
    else                  { otherBoxId = "mapAll" ; }
    
    
    otherWasChecked = $("input#"+otherBoxId).prop('checked') ;
    if (otherWasChecked) {
        // we visually uncheck the other box if necessary
        $('#'+otherBoxId).attr('checked', false);
    }
  
  $("tbody tr").each(function (i, row) {
      var rec_id = $(row).data('stuff') ;     // for old state system
      var ngramId = AjaxRecords[rec_id].id ;  // for future state system (cols)
      
      if(boxElem.checked) {
        // stateId: 1 if boxType == 'keep'
        //          2 if boxType == 'delete'
        var stateId = System[0]["statesD"][boxType] ;
        
        // a buffer to restore previous states if unchecked
        // (except if there was a click on the other 'all' box
        //  b/c then buffer is already filled and we shouldn't redo it)
        if (!otherWasChecked) {
            AjaxRecords[rec_id]["state_buff"] = AjaxRecords[rec_id]["state"] ;
        }
        
        // do the requested change
        AjaxRecords[rec_id]["state"] = stateId ;
      } 
      // restore previous states
      else {
        AjaxRecords[rec_id]["state"] = AjaxRecords[rec_id]["state_buff"] ;
        AjaxRecords[rec_id]["state_buff"] = null ;
      }
  });
  MyTable.data('dynatable').dom.update();
}


// Save changes to all corpusA-lists 
function SaveLocalChanges() {
  console.log("\nFUN SaveLocalChanges()")
  // console.clear()
  console.log("In SaveChanges()")
  var sum__selected_elems = 0;

  FlagsBuffer["delete"] = {}
  FlagsBuffer["keep"] = {}
  FlagsBuffer["outmap"] = {}
  FlagsBuffer["inmap"] = {}

  for(var id in AjaxRecords) {
    if( NGrams["map"][ AjaxRecords[id]["id"] ] ) {
      if(AjaxRecords[id]["state"]==System[0]["statesD"]["normal"] || AjaxRecords[id]["state"]==System[0]["statesD"]["delete"]) {
        FlagsBuffer["outmap"][ AjaxRecords[id].id ] = true
        if(AjaxRecords[id]["state"]==System[0]["statesD"]["delete"]) {
          FlagsBuffer["delete"][AjaxRecords[id].id] = true
        }
      }
      if(FlagsBuffer["group"][AjaxRecords[id].id] && AjaxRecords[id]["state"]==System[0]["statesD"]["keep"])  {
        FlagsBuffer["inmap"][ AjaxRecords[id].id ] = true
      }
    } else {    
      if(AjaxRecords[id]["state"]==System[0]["statesD"]["keep"]) {
        FlagsBuffer["inmap"][ AjaxRecords[id].id ] = true
      }
      if(AjaxRecords[id]["state"]==System[0]["statesD"]["delete"]) {
        FlagsBuffer["delete"][AjaxRecords[id].id] = true
      }
    }
  }
  // [ = = = = For deleting subforms = = = = ]
  for(var i in NGrams["group"].links) {
    if(FlagsBuffer["delete"][i]) {
      for(var j in NGrams["group"].links[i] ) {
        FlagsBuffer["delete"][NGrams["group"].links[i][j]] = true
      }
      for(var j in FlagsBuffer["delete"][i] ) {
        FlagsBuffer["delete"][FlagsBuffer["delete"][i][j]] = true
      }
    }
    if(FlagsBuffer["inmap"][i]) {
      for(var j in FlagsBuffer["group"][i] ) {
        FlagsBuffer["outmap"][FlagsBuffer["group"][i][j]] = true
      }
    }
  }
  // [ = = = = / For deleting subforms = = = = ]

  console.log(" = = = = = = = = = == ")
  console.log("FlagsBuffer:")
  console.log(JSON.stringify(FlagsBuffer))
  

  var nodes_2del = Object.keys(FlagsBuffer["delete"]).map(Number)
  var nodes_2keep = Object.keys(FlagsBuffer["keep"]).map(Number)
  var nodes_2group = $.extend({}, FlagsBuffer["group"])
  var nodes_2inmap = $.extend({}, FlagsBuffer["inmap"])
  var nodes_2outmap = $.extend({}, FlagsBuffer["outmap"])

   console.log("")
   console.log("")
   console.log(" nodes_2del: ")
   console.log(nodes_2del)
   console.log(" nodes_2keep: ")
   console.log(nodes_2keep)
   console.log(" nodes_2group: ")
   console.log(nodes_2group)
   console.log(" nodes_2inmap: ")
   console.log(nodes_2inmap)
   console.log(" nodes_2outmap: ")
   console.log(nodes_2outmap)
   console.log("")
   console.log("")
  
  var list_id = $("#list_id").val()
  var corpus_id = getIDFromURL( "corpus" ) // not used

  $("#stoplist_content").html()

  // CRUD( list_id , "" , Object.keys(FlagsBuffer["inmap"]).map(Number) , [] , "PUT", function(result) {
  //   console.log( result )
  // });

  $("#Save_All").append('<img width="8%" src="/static/img/ajax-loader.gif"></img>')
  CRUD( corpus_id , "/group" , [] , nodes_2group , "PUT" , function(result) {
   CRUD( corpus_id , "/keep" , [] , nodes_2inmap , "PUT" , function(result) {
     CRUD( corpus_id , "/keep" , [] , nodes_2outmap , "DELETE" , function(result) {
         CRUD( list_id , "" , nodes_2del , [] , "DELETE", function(result) {
          window.location.reload()
         });
     });
   });
  });
}


$("#Clean_All").click(function(){

	for(var id in AjaxRecords)
		AjaxRecords[id]["state"] = 0;

	$("#group_box").remove()
	GState=0

	MyTable.data('dynatable').dom.update();

	for(var i in FlagsBuffer)
		for(var j in FlagsBuffer[i])
			delete FlagsBuffer[i][j];
  // $("#Clean_All, #Save_All").attr( "disabled", "disabled" );
});

$("#Save_All").click(function(){
  SaveLocalChanges()
});

// For lists, all http-requests
function CRUD( parent_id , action , nodes , args , http_method , callback) {
	var the_url = window.location.origin+"/api/node/"+parent_id+"/ngrams"+action+"/"+nodes.join("+");
	the_url = the_url.replace(/\/$/, ""); //remove trailing slash
	
    // debug
    // console.log("CRUD AJAX => URL: " + the_url + " (" + http_method + ")")
    
    if(nodes.length>0 || Object.keys(args).length>0) {
		$.ajax({
		  method: http_method,
		  url: the_url,
		  data: args,
		  beforeSend: function(xhr) {
		    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
		  },
		  success: function(data){
		  		console.log(http_method + " ok!!")
		        console.log(nodes)
		        console.log(data)
		        callback(true);
		  },
		  error: function(result) {
		      console.log("Data not found in #Save_All");
		      console.log(result)
		      callback(false);
		  }
		});

	} else callback(false);
}



/**
 * 1. Creates the html of the table
 *    => therefore thead for dynatable columns template
 * 2. Fills the AjaxRecords from data 
 *    record.id, record.name, record.score... all except record.state
 *    record.state is initalized in:
 *       - AfterAjax for map items
 *       - ??? for stop items
 * 3. Creates the scores distribution chart over table
 * 4. Set up Search div
 * 
 * @param data: a response from the api/node/CID/ngrams/list/ routes
 * @param initial: initial score type "occs" or "tfidf"
 * @param search_filter: eg 'filter_all' (see SearchFilters.MODE)
 */
function Main_test( data , initial , search_filter) {
    
    // debug
    // alert("refresh main")
    
	console.log("")
	console.log(" = = = = MAIN_TEST: = = = = ")
	console.log("data:")
	console.log(data)
	console.log("initial:")   // 
	console.log(initial)
	console.log("search_filter:")	    // eg 'filter_all'
	console.log(search_filter)
	console.log(" = = = = / MAIN_TEST: = = = = ")
	console.log("")
  

    var DistributionDict = {}
    for(var i in DistributionDict)
        delete DistributionDict[i];
    delete DistributionDict;
    DistributionDict = {}

    var FirstScore = initial;

    var arrayd3 = []

    //  div_table += "\t"+"\t"+"\t"+'<input type="checkbox" id="multiple_selection" onclick="SelectAll(this);" /> Select'+"\n"
    $("#div-table").html("")
    $("#div-table").empty();
    
    // ? TODO move this to terms.html template
    // ----------------------------------------
    var div_table = '<p align="right">'+"\n"
      div_table += '<table id="my-ajax-table" class="table table-bordered table-hover">'+"\n"
      div_table += "\t"+'<thead>'+"\n"
      div_table += "\t"+'<tr>'+"\n"
      // ------------------------------------------------------------------
      // Any <th> defined here will end up in the 'columns' arg of ulWriter
      // ------------------------------------------------------------------
      
      // uncomment for column tableId
      // div_table += "\t"+"\t"+'<th data-dynatable-column="rec_id" style="background-color:grey">local id</th>'+"\n";
      
      // uncomment for column ngramId
      // div_table += "\t"+"\t"+'<th data-dynatable-column="ngramId" style="background-color:grey">ngramId</th>'+"\n";
      
      // uncomment for column stateId
      // div_table += "\t"+"\t"+'<th data-dynatable-column="state" style="background-color:grey">State</th>'+"\n" ;
      
      div_table += "\t"+"\t"+'<th data-dynatable-column="name">Terms</th>'+"\n";
      div_table += "\t"+"\t"+'<th id="score_column_id" data-dynatable-sorts="score" data-dynatable-column="score">Score</th>'+"\n";
      div_table += "\t"+"\t"+'</th>'+"\n";
      // selector columns... not sortable to allow 'click => check all'
      div_table += "\t"+"\t"+'<th data-dynatable-column="will_be_map"'
                            + ' data-dynatable-no-sort="true"'
                            + ' title="Selected terms will appear in the map."'
                            + ' style="width:3em;"'
                            + '>'
                            + 'Map'
                            + '<p class="note">'
                            + '<input type="checkbox" id="mapAll"'
                            + ' onclick="SelectAll(\'keep\',this)" title="Check to select all currently visible terms"></input>'
                            + '<label>All</label>'
                            + '</p>'
                            + '</th>'+"\n" ;
      div_table += "\t"+"\t"+'<th data-dynatable-column="will_be_stop"'
                            + ' data-dynatable-no-sort="true"'
                            + ' title="Selected terms will be removed from all lists."'
                            + ' style="width:3em;"'
                            + '>'
                            + 'Del'
                            + '<p class="note">'
                            + '<input type="checkbox" id="delAll"'
                            + ' onclick="SelectAll(\'delete\',this)" title="Check to select all currently visible terms"></input>'
                            + '<label>All</label>'
                            + '</p>'
                            + '</th>'+"\n" ;
      div_table += "\t"+'</tr>'+"\n";
      div_table += "\t"+'</thead>'+"\n";
      div_table += "\t"+'<tbody>'+"\n";
      div_table += "\t"+"\t"+'<tr><td>a</td><td>a</td><td>a</td><td>a</td></tr>'+"\n";
      div_table += "\t"+'</tbody>'+"\n";
      div_table += '</table>'+"\n";
      div_table += '</p>';
    $("#div-table").html(div_table)

    var div_stats = "<p>";
    for(var i in data.scores) {
      var value = (!isNaN(Number(data.scores[i])))? Number(data.scores[i]).toFixed(1) : data.scores[i];
      div_stats += i+": "+value+" | "
    }
    div_stats += "</p>"
    $("#stats").html(div_stats)

    AjaxRecords = []
    for(var i in data.ngrams) {
    
      var le_ngram = data.ngrams[i] ;
      
      var orig_id = le_ngram.id
      var arr_id = parseInt(i)
      RecDict[orig_id] = arr_id;
      var node_info = {
        "id" : le_ngram.id,
        "name": le_ngram.name,
        "score": le_ngram.scores[FirstScore],//le_ngram.scores.tfidf_sum / le_ngram.scores.occ_uniq,
        "flag":false,
        "group_plus": true,
        "group_blocked": false,
        "state": (le_ngram.state)?le_ngram.state:0,
        
        // rl: 2 new columns showing 'state == map' and 'state == del'
        "will_be_map": null,
        "will_be_stop": null
      }
      AjaxRecords.push(node_info)

      if ( ! DistributionDict[node_info.score] ) DistributionDict[node_info.score] = 0;
      DistributionDict[node_info.score]++;
    }

    console.log(FirstScore)

    // console.log("The Distribution!:")
    // console.log(Distribution)
    var DistributionList = []
    var min_occ=99999,max_occ=-1,min_frec=99999,max_frec=-1;
    for(var i in DistributionDict) {
      var info = {
        "x_occ":Number(i),
        "y_frec": Math.round(((Math.log( DistributionDict[i] ) + 1)))
      }
      DistributionList.push(info)
      if(info.x_occ > max_occ) max_occ = info.x_occ
      if(info.x_occ < min_occ) min_occ = info.x_occ
      if(info.y_frec > max_frec) max_frec = info.y_frec
      if(info.y_frec < min_frec) min_frec = info.y_frec
    }

 //    console.clear()
	// for(var i in DistributionList) {
	// 	// DistributionList[i].x_occ = Math.log( DistributionList[i].x_occ )
	// 	// DistributionList[i].y_frec = Math.log( DistributionList[i].y_frec )+1
	// 	console.log( DistributionList[i] )
	// }

	// return;
    oldest = Number(min_occ);
    latest = Number(max_occ);

    var ndx = false;
    ndx = crossfilter();
    ndx.add(DistributionList);

    // x_occs  = ndx.dimension(dc.pluck('x_occ'));
    var x_occs = ndx.dimension(function (d) {
        return d.x_occ;
    });

    var y_frecs = x_occs.group().reduceSum(function (d) {
        return d.y_frec;
    });

    LineChart
      .width(800)
      .height(150)
      .margins({top: 10, right: 50, bottom: 25, left: 40})
      .group(y_frecs)
      .dimension(x_occs)
      .transitionDuration(500)
      .x(d3.scale.linear().domain([min_occ,max_occ+min_occ]))
      // .y(d3.scale.log().domain([min_frec/2,max_frec*2]))
      .renderArea(true)
      // .valueAccessor(function (d) {
      //     return d.value;
      // })
      
      // .stack(y_frecs, function (d) {
      //     return d.value;
      // })
      // .ordinalColors(d3.scale.category10())
      .elasticY(true)
      // .round(dc.round.floor)
      .renderHorizontalGridLines(true)
      .renderVerticalGridLines(true)
      // .colors('red')
      // .interpolate("monotone")
      // .renderDataPoints({radius: 2, fillOpacity: 0.8, strokeOpacity: 0.8})
      .brushOn(false)
      .title(function (d) {
                  var value = d.value.avg ? d.value.avg : d.value;
                  if (isNaN(value)) value = 0;
                  return value+" ngrams with "+FirstScore+"="+Number(d.key);
              })
      .xAxis();
    LineChart.yAxis().ticks(5)
    LineChart.render()


    volumeChart.width(800)
            .height(100)
            .margins({top: 30, right: 50, bottom: 20, left: 40})
            .dimension(x_occs)
            .group(y_frecs)
            .centerBar(true)
            .gap(5)
            .x(d3.scale.linear().domain([min_occ/2,max_occ+min_occ]))
            .y(d3.scale.sqrt().domain([min_frec/2,max_frec+min_frec]))
            // .elasticY(true)
            // // .round(d3.time.month.round)
            // // .xUnits(d3.time.months)
            .renderlet(function (chart) {
                chart.select("g.y").style("display", "none");
                LineChart.filter(chart.filter());
                console.log("lalaal moveChart.focus(chartfilt);")
            })
            .on("filtered", function (chart) {
                dc.events.trigger(function () {
                    var chartfilt = chart.filter()
                    // tricky part: identifying when the moveChart changes.
                    if(chartfilt) {
                        Push2Buffer ( chart.filter() )
                    } else {
                        if(TheBuffer) {
                            Push2Buffer ( false )
                        }
                    }
                    LineChart.focus(chartfilt);
                });
            })
            .xAxis()
    volumeChart.yAxis().ticks(5)
    volumeChart.render()

    LineChart.filterAll();
    volumeChart.filterAll();
    dc.redrawAll();
    
    MyTable = []
    MyTable = $('#my-ajax-table').dynatable({
                dataset: {
                  records: AjaxRecords
                },
                features: {
                  pushState: false,
                  // sort: false //i need to fix the sorting function... the current one just sucks
                },
                writers: {
                  _rowWriter: ulWriter
                  // _cellWriter: customCellWriter
                }
              })
    
    // MyTable.data('dynatable').settings.dataset.records = []
    // MyTable.data('dynatable').settings.dataset.originalRecords = []
    // MyTable.data('dynatable').settings.dataset.originalRecords = AjaxRecords;
    
    MyTable.data('dynatable').sorts.clear();
    MyTable.data('dynatable').sorts.add('score', 0) // 1=ASCENDING,
    MyTable.data('dynatable').process();
    MyTable.data('dynatable').paginationPage.set(1);
    MyTable.data('dynatable').paginationPerPage.set(20);  // default:10
    // MyTable.data('dynatable').process();
    // MyTable.data('dynatable').sorts.clear();
    MyTable.data('dynatable').process();
    
    // hook on page change
    MyTable.bind('dynatable:page:set', function(){
        // we visually uncheck both 'all' boxes
        $('input#mapAll').attr('checked', false);
        $('input#delAll').attr('checked', false);
    })

    // // // $("#score_column_id").children()[0].text = FirstScore
    // // // // MyTable.data('dynatable').process();

    if ( $(".imadiv").length>0 ) return 1;
    $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
    $(".dynatable-record-count").insertAfter(".imadiv")
    $(".dynatable-pagination-links").insertAfter(".imadiv")


    // Search
	$("#filter_search").html( $("#filter_search").html().replace('selected="selected"') );
	$("#"+search_filter).attr( "selected" , "selected" )
	var the_content = $("#filter_search").html();
	$(""+the_content).insertAfter("#dynatable-query-search-my-ajax-table")
    return "OK"
}


function SearchFilters( elem ) {
  var MODE = elem.value;

  if( MODE == "filter_all") {
    var result = Main_test( NGrams["main"] , NGrams["main"].scores.initial , MODE)
    console.log( result )

	MyTable.data('dynatable').sorts.clear();
	MyTable.data('dynatable').sorts.add('score', 0) // 1=ASCENDING,
	MyTable.data('dynatable').process();
  }

  if( MODE == "filter_map-list") {
  	console.log("ngrams_map:")
  	console.log(NGrams["map"])

  	var sub_ngrams_data = {
  		"ngrams":[],
  		"scores": $.extend({}, NGrams["main"].scores)
  	}
    for(var r in NGrams["main"].ngrams) {
    	if ( NGrams["map"][NGrams["main"].ngrams[r].id] ) {
    		var a_ngram = NGrams["main"].ngrams[r]
			a_ngram["state"] = System[0]["statesD"]["keep"]
    		sub_ngrams_data["ngrams"].push( a_ngram )
    	}
    }

    var result = Main_test(sub_ngrams_data , NGrams["main"].scores.initial , MODE)
    console.log( result )
    // MyTable.data('dynatable').sorts.clear();
    // MyTable.data('dynatable').sorts.add('score', 0) // 1=ASCENDING,
    // MyTable.data('dynatable').process();
  }
    

  if( MODE == "filter_stop-list") {
  	console.log( NGrams["stop"] )
  	if(Object.keys(NGrams["stop"]).length>0) {
		var sub_ngrams_data = {
			"ngrams":[],
			"scores": $.extend({}, NGrams["main"].scores)
		}
		for(var r in NGrams["stop"]) {
			var a_ngram = NGrams["stop"][r] ;
            // deletestateId = 2
            var deletestateId = System[0]["statesD"]["delete"] ;
			a_ngram["state"] = deletestateId ;

			sub_ngrams_data["ngrams"].push( a_ngram )
            
		}
		var result = Main_test(sub_ngrams_data , NGrams["main"].scores.initial , MODE)
		console.log( result )
  	}
  }

}

function getIDFromURL( item ) {
	var pageurl = window.location.href.split("/")
	var cid;
	for(var i in pageurl) {
	    if(pageurl[i]==item) {
	        cid=parseInt(i);
	        break;
	    }
	} 
	return pageurl[cid+1];
}

// For lists, only GET requests
function GET_( url , callback ) {
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        success : function(data, textStatus, jqXHR) { 
        	callback(data.data);
        },
        error: function(exception) { 
            callback(false);
        }
    })
}

// [ = = = = = = = = = = INIT = = = = = = = = = = ]
// http://localhost:8000/api/node/84592/ngrams?format=json&score=tfidf,occs&list=miam
var corpus_id = getIDFromURL( "corpus" )
var NGrams = {
	"group" : {},
	"stop" : {}, 
	"main" : {},
	"map" : {},
	"scores" : {}
}

$("#corpusdisplayer").hide()
// if( $("#share_button").length==0 ) {
//   $("#ImportList").remove()
// }


var url = [
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/list/miam?custom",
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/list/map",
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/group",
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/list/stop?custom",
	// window.location.origin+"/api/node/"+corpus_id+"/ngrams?format=json&score=tfidf,occs&list=stop&limit=1000", //doesnt work right now
]



// The AJAX's in cascade:

GET_( url[0] , function(result) {
	// = = = = MIAM = = = = //
	if(result!=false) {
  	NGrams["main"] = {
  		"ngrams": [],
  		"scores": {
	        "initial":"occs",
	        "nb_docs":result.length,
	        "orig_nb_ngrams":1,
	        "nb_ngrams":result.length,
	    }
  	}

    var occs_sum = 0
		for(var i in result) {
			NGrams["main"].ngrams.push(result[i])  
      occs_sum += result[i].scores.occs
    }
    if(occs_sum==0)
      NGrams["main"]["scores"]["initial"] = "tfidf";

	}
	// = = = = /MIAM = = = = //
	
	GET_( url[1] , function(result) {
		// = = = = MAP = = = = //
		if(result!=false) {
			NGrams["map"] = result 
		}
		// = = = = /MAP = = = = //

		GET_( url[2] , function(result) {
			// = = = = GROUP = = = = //
			if(result!=false) {
				NGrams["group"] = result 
			}
			// = = = = /GROUP = = = = //

	    	AfterAjax()
			GET_( url[3] , function(result) {
				// = = = = STOP = = = = //
				for(var i in result) {
		    		NGrams["stop"][result[i].id] = result[i]
		    	}
				// = = = = /STOP = = = = //
			});
		});
	});
});



function AfterAjax() {
  // debug
  // console.log("\nFUN AfterAjax()")
	// // Deleting subforms from the ngrams-table, clean start baby!
    if( Object.keys(NGrams["group"].links).length>0 ) {

    	var _forms = {  "main":{} , "sub":{}  }
    	for(var i in NGrams["group"].links) {
    		_forms["main"][i] = true
    		for(var j in NGrams["group"].links[i]) {
    			_forms["sub"][ NGrams["group"].links[i][j] ] = true
    		}
    	}
    	var ngrams_data_ = []
    	for(var i in NGrams["main"].ngrams) {
    		if(_forms["sub"][NGrams["main"].ngrams[i].id]) {
    			NGrams["group"]["nodes"][NGrams["main"].ngrams[i].id] = NGrams["main"].ngrams[i]
    		} else {
    			// if( _forms["main"][ NGrams["main"].ngrams[i].id ] )
    			// 	NGrams["main"].ngrams[i].name = "*"+NGrams["main"].ngrams[i].name
    			ngrams_data_.push( NGrams["main"].ngrams[i] )
    		}
    	}
    	NGrams["main"].ngrams = ngrams_data_;
    }
    
    
    // initialize state of maplist items
    if( Object.keys(NGrams["map"]).length>0 ) {
    	for(var i in NGrams["main"].ngrams) {
            myMiamNgram = NGrams["main"].ngrams[i]
    		if(NGrams["map"][myMiamNgram.id]) {
                // keepstateId = 1
                keepstateId = System[0]["statesD"]["keep"]
                myMiamNgram["state"] = keepstateId ;
    		}
    	}
    }

    // Building the Score-Selector //NGrams["scores"]
    var FirstScore = NGrams["main"].scores.initial
    var possible_scores = Object.keys( NGrams["main"].ngrams[0].scores );
    var scores_div = '<br><select style="font-size:25px;" class="span1" id="scores_selector">'+"\n";
    scores_div += "\t"+'<option value="'+FirstScore+'">'+FirstScore+'</option>'+"\n"
    for( var i in possible_scores ) {
      if(possible_scores[i]!=FirstScore) {
        scores_div += "\t"+'<option value="'+possible_scores[i]+'">'+possible_scores[i]+'</option>'+"\n"
      }
    }
    // Initializing the Charts and Table
    console.log( NGrams["main"] )
    var result = Main_test( NGrams["main"] , FirstScore , "filter_all")
    console.log( result )

    // Listener for onchange Score-Selector
    scores_div += "<select>"+"\n";
    $("#ScoresBox").html(scores_div)
    $("#scores_selector").on('change', function() {
      console.log( this.value )
      var result = Main_test( NGrams["main"] , this.value , "filter_all")
      console.log( result )

    });

    $("#corpusdisplayer").show()
    $("#content_loader").remove()
    $("#corpusdisplayer").click()


    $(".nav-tabs a").click(function(e){
      e.preventDefault();
      $(this).tab('show');
    });
    $('.nav-tabs a').on('shown.bs.tab', function(event){
        var x = $(event.target).text();         // active tab
        var y = $(event.relatedTarget).text();  // previous tab
        $(".act span").text(x);
        $(".prev span").text(y);
    });

}
