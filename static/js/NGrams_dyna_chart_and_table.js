
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
		"statesD" : {} ,
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

for(var i in System[GState]["states"] ) {
	System[GState]["statesD"][ System[GState]["states"][i] ] = Number(i)
}


var FlagsBuffer = {}
for(var i in System[GState]["states"]) {
  FlagsBuffer[System[GState]["states"][i]] = {}
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

// new
// click red, click keep, click normal...
function clickngram_action ( elem ) {
	var elem_id = $( elem ).data("stuff")
	AjaxRecords[elem_id].state = (AjaxRecords[elem_id].state==(System[0]["states"].length-2))?0:(AjaxRecords[elem_id].state+1);

	MyTable.data('dynatable').dom.update();
}

// function YOLO() {

//   var sum__selected_elems = 0;

//   for(var i in FlagsBuffer["group"])
//   	sum__selected_elems += Object.keys( FlagsBuffer["group"][i] ).length
//   for(var i in FlagsBuffer)
//     sum__selected_elems += Object.keys(FlagsBuffer[i]).length;

//   console.log("")
//   console.log("Current Buffer size: "+sum__selected_elems)
//   console.log(FlagsBuffer)

//   if ( sum__selected_elems>0 )
//     $("#Clean_All, #Save_All").removeAttr("disabled", "disabled");
//   else 
//     $("#Clean_All, #Save_All").attr( "disabled", "disabled" );
// }


// modified
function transformContent(rec_id) {
	var elem = AjaxRecords[rec_id];
	var result = {}
	var atts = System[0]["dict"][ System[0]["states"][elem.state] ]
	var plus_event = ""
	if(GState==0 && elem.state!=System[0]["statesD"]["delete"] ) // if deleted, no + button
		plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(+)</a>"
	if(GState==1 ) {
		if(elem.state!=System[0]["statesD"]["delete"] && elem.state!=System[0]["statesD"]["group"]) { // if deleted and already group, no Up button
			plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(▲)</a>"
		}
	}
	result["id"] = elem["id"]
	result["score"] = '<span class="'+atts.id+'">'+elem["score"]+'</span>'
	result["name"] = "<span class=\""+atts.id+
					 "\" onclick=\"clickngram_action(this.parentNode.parentNode)\">"+elem["name"]+"</span>"+
					 plus_event
	return result;
}

// to delete
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

//generic enough
function ulWriter(rowIndex, record, columns, cellWriter) {
  var tr = '';
  var cp_rec = {}

  if( AjaxRecords[RecDict[record.id]].state < 0 )
  	return false;

  cp_rec = transformContent(RecDict[record.id])
  
  // grab the record's attribute for each column
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }
  var data_id = RecDict[record.id]
  return '<tr data-stuff='+data_id+'>' + tr + '</tr>';
}

function SelectAll( box ) {
  var current_flag = $("input[type='radio'][name='radios']:checked").val()
  $("tbody tr").each(function (i, row) {
      var id = $(row).data('stuff')
      if(box.checked) {
      	AjaxRecords[id]["state_buff"] = AjaxRecords[id]["state"]
      	AjaxRecords[id]["state"] = System[0]["statesD"][current_flag]
      } else {
      	AjaxRecords[id]["state"] = AjaxRecords[id]["state_buff"]
      }
      
  });
  MyTable.data('dynatable').dom.update();
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
	console.clear()
	console.log("click in save all 01")
	var sum__selected_elems = 0;

	FlagsBuffer["delete"] = {}
	FlagsBuffer["keep"] = {}
	FlagsBuffer["outmap"] = {}
	FlagsBuffer["inmap"] = {}

	for(var id in AjaxRecords) {
		if( NGrams["map"][ AjaxRecords[id]["id"] ] ) {
			if(AjaxRecords[id]["state"]==0 || AjaxRecords[id]["state"]==2) {
				FlagsBuffer["outmap"][ AjaxRecords[id].id ] = true
				if(AjaxRecords[id]["state"]==2) {
					FlagsBuffer["delete"][AjaxRecords[id].id] = true
				}
			}
			if(FlagsBuffer["group"][AjaxRecords[id].id] && AjaxRecords[id]["state"]==1)  {
				FlagsBuffer["inmap"][ AjaxRecords[id].id ] = true
			}
		} else {		
			if(AjaxRecords[id]["state"]==1) {
				FlagsBuffer["inmap"][ AjaxRecords[id].id ] = true
			}
			if(AjaxRecords[id]["state"]==2) {
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

	// console.log(" = = = = = = = = = == ")
	// console.log("FlagsBuffer:")
	// console.log(FlagsBuffer)


	var nodes_2del = Object.keys(FlagsBuffer["delete"]).map(Number)
	var nodes_2keep = Object.keys(FlagsBuffer["keep"]).map(Number)
	var nodes_2group = $.extend({}, FlagsBuffer["group"])
	var nodes_2inmap = $.extend({}, FlagsBuffer["inmap"])
	var nodes_2outmap = $.extend({}, FlagsBuffer["outmap"])

	// console.log("")
	// console.log("")
	// console.log(" nodes_2del: ")
	// console.log(nodes_2del)
	// console.log(" nodes_2keep: ")
	// console.log(nodes_2keep)
	// console.log(" nodes_2group: ")
	// console.log(nodes_2group)
	// console.log(" nodes_2inmap: ")
	// console.log(nodes_2inmap)
	// console.log(" nodes_2outmap: ")
	// console.log(nodes_2outmap)
	// console.log("")
	// console.log("")

	var list_id = $("#list_id").val()
	var corpus_id = getIDFromURL( "corpus" ) // not used


	$("#Save_All").append('<img width="8%" src="/static/img/ajax-loader.gif"></img>')
	CRUD( corpus_id , "/group" , [] , nodes_2group , "PUT" , function(result) {
		console.log(" UN ELEFANTE "+result)
		CRUD( corpus_id , "/keep" , [] , nodes_2inmap , "PUT" , function(result) {
			console.log(" DOS ELEFANTES "+result)
			CRUD( corpus_id , "/keep" , [] , nodes_2outmap , "DELETE" , function(result) {
				console.log(" TRES ELEFANTES "+result)
				CRUD( list_id , "" , nodes_2del , [] , "DELETE", function(result) {
					console.log(" CUATRO ELEFANTES "+result)
					window.location.reload()
				});
			});
		});
	});

});

function CRUD( parent_id , action , nodes , args , http_method , callback) {
	var the_url = window.location.origin+"/api/node/"+parent_id+"/ngrams"+action+"/"+nodes.join("+");
	the_url = the_url.replace(/\/$/, ""); //remove trailing slash
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

function Main_test( data , initial , search_filter) {

	console.log("")
	console.log(" = = = = MAIN_TEST: = = = = ")
	console.log("data:")
	console.log(data)
	console.log("initial:")
	console.log(initial)
	console.log("search_filter:")	
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

    AjaxRecords = []
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
        "state": (le_ngram.state)?le_ngram.state:0
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
      Div_PossibleActions += '<input type="radio" id="radio'+action+'" name="radios"  value="'+a.id+'" '+ischecked+'>';
      Div_PossibleActions += '<label style="color:'+a.color+';" for="radio'+action+'">'+a.name+'</label>';
    }
    var Div_SelectAll = ' <input type="checkbox" id="multiple_selection" onclick="SelectAll(this);" /> Select All'
    $(".imadiv").html('<div style="float: left; text-align:left;">'+Div_PossibleActions+Div_SelectAll+'</div><br>');


	$("#filter_search").html( $("#filter_search").html().replace('selected="selected"') );
	$("#"+search_filter).attr( "selected" , "selected" )
	var the_content = $("#filter_search").html();
	$(""+the_content).insertAfter("#dynatable-query-search-my-ajax-table")
    return "OK"
}



function SearchFilters( elem ) {
  var MODE = elem.value;

  if( MODE == "filter_all") {
  	console.clear()
    var result = Main_test( NGrams["main"] , NGrams["main"].scores.initial , MODE)
    console.log( result )

	MyTable.data('dynatable').sorts.clear();
	MyTable.data('dynatable').sorts.add('score', 0) // 1=ASCENDING,
	MyTable.data('dynatable').process();
  }

  if( MODE == "filter_map-list") {
  	console.clear()
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
			var a_ngram = NGrams["stop"][r]
			a_ngram["state"] = System[0]["statesD"]["delete"]
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


var url = [
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/list/miam?custom",
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/list/map",
	window.location.origin+"/api/node/"+corpus_id+"/ngrams/group",
	window.location.origin+"/api/node/"+corpus_id+"/ngrams?format=json&score=tfidf,occs&list=stop&limit=1000",
]



// The AJAX's in cascade:

GET_( url[0] , function(result) {
	// = = = = MIAM = = = = //
	if(result!=false) {
    	NGrams["main"] = {
    		"ngrams": [],
    		"scores": {
		        "initial":"tfidf",
		        "nb_docs":result.length,
		        "orig_nb_ngrams":1,
		        "nb_ngrams":result.length,
		    }
    	}

		for(var i in result) 
			NGrams["main"].ngrams.push(result[i])  

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

    if( Object.keys(NGrams["map"]).length>0 ) {
    	for(var i in NGrams["main"].ngrams) {
    		if(NGrams["map"][NGrams["main"].ngrams[i].id]) {
    			NGrams["main"].ngrams[i]["state"] = System[0]["statesD"]["keep"]
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
}
