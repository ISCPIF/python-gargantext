
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
	  "id":"to_delete",
	  "name": "Delete",
	  "color":"red"
	}, 
	{
	  "id":"to_keep",
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
	// 	"states" : [ "normal" , "grouped" , "blocked" ] ,	
	// 	"dict" : { 
	// 		"normal": {
	// 		  "id":"normal",
	// 		  "name": "Normal",
	// 		  "color":"black"
	// 		}, 
	// 		"grouped": {
	// 		  "id":"grouped",
	// 		  "name": "MainForm",
	// 		  "color":"white"
	// 		}, 
	// 	}	
	// },
	0: {
		"states" : [ "normal" , "to_delete" , "to_keep" ,"grouped"] ,
		"dict" : { 
			"normal": {
			  "id":"normal",
			  "name": "Normal",
			  "color":"black"
			}, 
			"to_delete": {
			  "id":"to_delete",
			  "name": "Delete",
			  "color":"red"
			}, 
			"to_keep": {
			  "id":"to_keep",
			  "name": "Keep",
			  "color":"green"
			} , 
			"grouped": {
			  "id":"grouped",
			  "name": "MainForm",
			  "color":"white"
			}, 
		}
	}
	
}

for(var i in System[GState]["states"] )
	System[GState]["dict"][ System[GState]["dict"][i] ] = Number(i)
console.log( System )


var FlagsBuffer = {}
for(var i in PossibleActions) {
  FlagsBuffer[PossibleActions[i].id] = {}
}


var MyTable;
var RecDict={};
var AjaxRecords = []

//      D3.js: Interactive timerange variables.
var LineChart = dc.lineChart("#monthly-move-chart"); 
var volumeChart = dc.barChart("#monthly-volume-chart");



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
    // (1) Identifying if the button is collapsed:   
    var isCollapsed=false;
    var accordiontext = $("#collapseOne").attr("class")
    if(accordiontext.indexOf("collapse in")>-1) 
        isCollapsed=true;


    var UpdateTable = false
    if ( (action == "click" && !isCollapsed) || (action=="changerange" && isCollapsed) ) {
        UpdateTable = true;
        $("#corpusdisplayer").html("Close Folder")
    } else $("#corpusdisplayer").html("Open Folder")

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

function group_mode ( elem ) {
	GState=1
	var elem_id = $( elem ).data("stuff")

	$('<span/>', {
		"data-id":AjaxRecords[elem_id].id,
	    text: AjaxRecords[elem_id].name + ":",
	    // css: {
	    // 	"float":"right",
	    // }
	}).appendTo("#group_box_header")

	AjaxRecords[elem_id].state=3;// 3: "grouped" state

	MyTable.data('dynatable').dom.update();
}

function SaveSinonims( gheader , gcontent) {
	console.log("GHEADER:")
	$(gheader).children('span').each(function () {
	    console.log($(this).data("id"));
	});
	console.log("GCONTENT:")
	$(gcontent).children('span').each(function () {
	    console.log($(this).data("id"));
	});
}

$('#group_box_content').bind("DOMSubtreeModified",function(){
	console.log( $(this).has( "span" ).length )
	var groupdiv = "#group_box"
	if($(this).has( "span" ).length>0) {
		$("#save_sinonims").remove();
		$('<button/>', {
			"id":"save_sinonims",
		    text: "Save sinonims",
		    class: "btn btn-info",
		    css: {
		    	"float":"right",
		    }
		})
		.insertAfter(groupdiv)
		.click( function() {
			SaveSinonims(groupdiv+"_header" , groupdiv+"_content")
		})
	}
})

function add2group ( elem ) {
	var elem_id = $( elem ).data("stuff")

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
    	MyTable.data('dynatable').dom.update();
	})
	.appendTo('#group_box_content')


	AjaxRecords[elem_id].state=3;// 3: "grouped" state

	MyTable.data('dynatable').dom.update();
}

function clickngram_action ( elem ) {
	var elem_id = $( elem ).data("stuff")
	AjaxRecords[elem_id].state = (AjaxRecords[elem_id].state==(System[0]["states"].length-2))?0:(AjaxRecords[elem_id].state+1);

	MyTable.data('dynatable').dom.update();
}

function transformContent(rec_id) {
	var elem = AjaxRecords[rec_id];
	var result = {}
	var atts = System[0]["dict"][ System[0]["states"][elem.state] ]
	var plus_event = ""
	if(GState==0 && elem.state!=1) // if deleted, no + button
		plus_event = " <a class=\"plusclass\" onclick=\"group_mode(this.parentNode.parentNode)\">(+)</a>"
	if(GState==1 ) {
		if(elem.state!=1 && elem.state!=3) { // if deleted and already grouped, no Up button
			plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(↑)</a>"
		}
	}
	result["id"] = elem["id"]
	result["score"] = '<span class="'+atts.id+'">'+elem["score"]+'</span>'
	result["name"] = "<span class=\""+atts.id+
					 "\" onclick=\"clickngram_action(this.parentNode.parentNode)\">"+elem["name"]+"</span>"+
					 plus_event
	return result;
}


// Affecting the tr element somehow
function overRide(elem) {
  var id = elem.id
  var current_flag = $("input[type='radio'][name='radios']:checked").val()
  var this_newflag = (current_flag==AjaxRecords[id]["flag"])?false:current_flag

  console.log("striking: "+id+" | this-elem_flag: "+AjaxRecords[id]["flag"]+" | current_flag: "+current_flag)
  console.log("\t so the new flag is: "+this_newflag)
  // if(this_newflag)
  //   FlagsBuffer[this_newflag][id] = true;
  // else 
  //   delete FlagsBuffer[ AjaxRecords[id]["flag"] ][id];
  AjaxRecords[id]["flag"] = Mark_NGram ( id , AjaxRecords[id]["flag"] , this_newflag );

  var sum__selected_elems = 0;
  for(var i in FlagsBuffer)
    sum__selected_elems += Object.keys(FlagsBuffer[i]).length;

  console.log("")
  console.log("Current Buffer size: "+sum__selected_elems)
  console.log(FlagsBuffer)

  if ( sum__selected_elems>0 )
    $("#Clean_All, #Save_All").removeAttr("disabled", "disabled");
  else 
    $("#Clean_All, #Save_All").attr( "disabled", "disabled" );

  MyTable.data('dynatable').dom.update();

}

// Here you have to put the weird case of Change from Group-Mode
function DeactivateSelectAll() {
  if( $("#multiple_selection").length>0 )
    $("#multiple_selection")[0].checked = false;

  if( Object.keys(FlagsBuffer["to_group"]).length ){


    $("#savemodal").modal("show").css({
        'margin-top': function () { //vertical centering
            console.log($(".modal-content").height())
            return ($(this).height() / 2);
        }
    });

    console.log("OH OH")
    console.log("There are some nodes in group array!:")
    // $("#to_group").html( Object.keys(FlagsBuffer["to_group"]).join(" , ") );
    var labels = []
    for (var i in FlagsBuffer["to_group"]){
      var fake_id = i
      console.log( AjaxRecords[fake_id] )
      labels.push(AjaxRecords[fake_id].name)
    //   $("#to_group").htm
    }

    $("#to_group").html( '<font color="blue">' + labels.join(" , ") + '</div>' );
  }
}


function Mark_NGram( ngram_id , old_flag , new_flag ) {
  if(new_flag){
    for(var f in FlagsBuffer) {
      if( new_flag==f )
        FlagsBuffer[f][ngram_id] = true;
      else 
        delete FlagsBuffer[f][ngram_id];
    }
  } else {
    delete FlagsBuffer[ old_flag ][ngram_id];
  }
  return new_flag;
}

function GroupNGrams() {
    for (var i in FlagsBuffer["to_group"]){
      console.log( AjaxRecords[i] )
    }  
}

//generic enough
function ulWriter(rowIndex, record, columns, cellWriter) {
  // pr("\tulWriter: "+record.id)
  var tr = '';
  var cp_rec = {}
  // pr("\t\tbfr transf2: rec_id="+record.id+" | arg="+RecDict[record.id])
  cp_rec = transformContent(RecDict[record.id])
  
  // grab the record's attribute for each column
  // console.log("\tin ulWriter:")
  // console.log(record)
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }
  var data_id = RecDict[record.id]
  return '<tr data-stuff='+data_id+'>' + tr + '</tr>';
}

function SelectAll( the_checkbox ) {
  var current_flag = $("input[type='radio'][name='radios']:checked").val()
  $("tbody tr").each(function (i, row) {
      var id = $(row).data('stuff')
      // AjaxRecords[id]["flag"] = (the_checkbox.checked)?the_flag:false;
      

      var this_newflag = (the_checkbox.checked)?current_flag:false;

      // console.log("striking: "+id+" | this-elem_flag: "+AjaxRecords[id]["flag"]+" | current_flag: "+current_flag)
      // console.log("\t so the new flag is: "+this_newflag)

      AjaxRecords[id]["flag"] = Mark_NGram ( id , AjaxRecords[id]["flag"] , this_newflag );



  });
  MyTable.data('dynatable').dom.update();
}


$("#Clean_All").click(function(){

  for(var id in AjaxRecords)
    AjaxRecords[id]["flag"] = false;

  MyTable.data('dynatable').dom.update();

  for(var i in FlagsBuffer)
    for(var j in FlagsBuffer[i])
      delete FlagsBuffer[i][j];

  $("#Clean_All, #Save_All").attr( "disabled", "disabled" );

});

$("#Save_All").click(function(){
  console.log("click in save all 01")
  var sum__selected_elems = 0;
  var poubelle = []
  for(var i in FlagsBuffer) {
    if (Object.keys(FlagsBuffer[i]).length==0) 
      poubelle.push(i)
    sum__selected_elems += Object.keys(FlagsBuffer[i]).length;
  }
  console.log("click in save all 02")
  for(var i in poubelle)
    delete FlagsBuffer[poubelle[i]];
  console.log("click in save all 03, sum:"+sum__selected_elems)
  if ( sum__selected_elems>0 ) {
    console.log("")
    console.log("Do the ajax conexion with API and send this array to be processed:")
    for(var i in FlagsBuffer) {
      var real_ids = []
      for (var j in FlagsBuffer[i])
        real_ids.push( AjaxRecords[j].id );

      FlagsBuffer[i] = real_ids
    
    }
    console.log(FlagsBuffer)
    var list_id = $("#list_id").val()
    // '/annotations/lists/'+list_id+'/ngrams/108642'

    console.log(window.location.origin+'/lists/'+list_id+"/ngrams/"+real_ids.join("+"))
    console.log(real_ids)
      $.ajax({
        method: "DELETE",
        url: window.location.origin+'/annotations/lists/'+list_id+"/ngrams/"+real_ids.join("+"),
        beforeSend: function(xhr) {
          xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
        success: function(data){
              console.log(data)
              location.reload()
        },
        error: function(result) {
            console.log("Data not found in #Save_All");
            console.log(result)
        }
      });
    // console.log("")
  }

});



function Main_test( data , initial) {


    var DistributionDict = {}
    for(var i in DistributionDict)
        delete DistributionDict[i];
    delete DistributionDict;
    DistributionDict = {}

    AjaxRecords = []

    var FirstScore = initial;

    var arrayd3 = []

    //  div_table += "\t"+"\t"+"\t"+'<input type="checkbox" id="multiple_selection" onclick="SelectAll(this);" /> Select'+"\n"
    $("#div-table").html("")
    $("#div-table").empty();
    var div_table = '<p align="right">'+"\n"
      div_table += '<table id="my-ajax-table" class="table table-bordered table-hover">'+"\n"
      div_table += "\t"+'<thead>'+"\n"
      div_table += "\t"+"\t"+'<th data-dynatable-column="name">Terms</th>'+"\n"
      div_table += "\t"+"\t"+'<th id="score_column_id" data-dynatable-sorts="score" data-dynatable-column="score">Score</th>'+"\n"
      div_table += "\t"+"\t"+'</th>'+"\n"
      div_table += "\t"+'</thead>'+"\n"
      div_table += "\t"+'<tbody>'+"\n"
      div_table += "\t"+'</tbody>'+"\n"
      div_table += '</table>'+"\n"
      div_table += '</p>';
    $("#div-table").html(div_table)

    

    var div_stats = "<p>";
    for(var i in data.scores) {
      var value = (!isNaN(Number(data.scores[i])))? Number(data.scores[i]).toFixed(1) : data.scores[i];
      div_stats += i+": "+value+" | "
    }
    div_stats += "</p>"
    $("#stats").html(div_stats)


    for(var i in data.ngrams) {
    
      var le_ngram = data.ngrams[i]

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
        "state": 0
      }
      AjaxRecords.push(node_info)

      if ( ! DistributionDict[node_info.score] ) DistributionDict[node_info.score] = 0;
      DistributionDict[node_info.score]++;
    }

    // console.log("The Distribution!:")
    // console.log(Distribution)
    var DistributionList = []
    var min_occ=99999,max_occ=-1,min_frec=99999,max_frec=-1;
    for(var i in DistributionDict) {
      var info = {
        "x_occ":Number(i),
        "y_frec":DistributionDict[i]
      }
      DistributionList.push(info)
      if(info.x_occ > max_occ) max_occ = info.x_occ
      if(info.x_occ < min_occ) min_occ = info.x_occ
      if(info.y_frec > max_frec) max_frec = info.y_frec
      if(info.y_frec < min_frec) min_frec = info.y_frec
    }

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

    console.log("scores: [ "+min_occ+" , "+max_occ+" ] ")
    console.log("frecs: [ "+min_frec+" , "+max_frec+" ] ")


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
              // .bind("dynatable:afterUpdate",  function(e, rows) {
              //   $(e.target).children("tbody").children().each(function(i) {
              //      $(this).click(function(){
              //        var row_nodeid = $(this).data('stuff')
              //        var elem = { "id":row_nodeid , "checked":false }
              //        overRide(elem); //Select one row -> select one ngram

              //       });
              //   });
              // });

    // MyTable.data('dynatable').settings.dataset.records = []
    // MyTable.data('dynatable').settings.dataset.originalRecords = []
    // MyTable.data('dynatable').settings.dataset.originalRecords = AjaxRecords;
    
    MyTable.data('dynatable').sorts.clear();
    MyTable.data('dynatable').sorts.add('score', 0) // 1=ASCENDING,
    MyTable.data('dynatable').process();
    MyTable.data('dynatable').paginationPage.set(1);
    // MyTable.data('dynatable').process();
    // MyTable.data('dynatable').sorts.clear();
    MyTable.data('dynatable').process();

    // // // $("#score_column_id").children()[0].text = FirstScore
    // // // // MyTable.data('dynatable').process();

    if ( $(".imadiv").length>0 ) return 1;
    $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
    $(".dynatable-record-count").insertAfter(".imadiv")
    $(".dynatable-pagination-links").insertAfter(".imadiv")



    var Div_PossibleActions = ""
    for(var action in PossibleActions) {
      var a = PossibleActions[action];
      var ischecked = (Number(action)==0)?"checked":"";
      Div_PossibleActions += '<input type="radio" id="radio'+action+'" name="radios" onclick="DeactivateSelectAll();" value="'+a.id+'" '+ischecked+'>';
      Div_PossibleActions += '<label style="color:'+a.color+';" for="radio'+action+'">'+a.name+'</label>';
    }
    var Div_SelectAll = ' <input type="checkbox" id="multiple_selection" onclick="SelectAll(this);" /> Select All'
    $(".imadiv").html('<div style="float: left; text-align:left;">'+Div_PossibleActions+Div_SelectAll+'</div><br>');


    return "OK"
}


function SearchFilters( elem ) {
  var MODE = elem.value;

  if( MODE == "filter_all") {
    var result = Main_test(AjaxRecords , MODE)
    console.log( result )
    return ;
  }



  // if( MODE == "filter_stoplist") {


  // }

  // if( MODE == "filter_miamlist") {


  // }

}

console.log(window.location.href+"/ngrams.json")
$.ajax({
  url: window.location.href+"/ngrams.json",
  success: function(data){

    // Building the Score-Selector
    var FirstScore = data.scores.initial
    var possible_scores = Object.keys( data.ngrams[0].scores );
    var scores_div = '<br><select style="font-size:25px;" class="span1" id="scores_selector">'+"\n";
    scores_div += "\t"+'<option value="'+FirstScore+'">'+FirstScore+'</option>'+"\n"
    for( var i in possible_scores ) {
      if(possible_scores[i]!=FirstScore) {
        scores_div += "\t"+'<option value="'+possible_scores[i]+'">'+possible_scores[i]+'</option>'+"\n"
      }
    }
    // Initializing the Charts and Table
    var result = Main_test( data , FirstScore )
    console.log( result )


    // Listener for onchange Score-Selector
    scores_div += "<select>"+"\n";
    $("#ScoresBox").html(scores_div)
    $("#scores_selector").on('change', function() {
      console.log( this.value )
      var result = Main_test( data , this.value )
      console.log( result )
    });



  }
});