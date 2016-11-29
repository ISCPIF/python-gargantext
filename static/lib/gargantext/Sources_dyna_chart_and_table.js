
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

var PossibleActions = []

var action1 = {
  "id":"to_delete",
  "name": "Delete",
  "color":"red"
}
var action2 = {
  "id":"to_keep",
  "name": "Keep",
  "color":"green"
}

var action3 = {
  "id":"to_group",
  "name": "Group",
  "color":"blue"
}

PossibleActions.push(action1)
PossibleActions.push(action2)
PossibleActions.push(action3)

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
    var UpdateTable = false
    if (action=="changerange") {
        UpdateTable = true;
    }

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

//          STEP 01:
//      Get all the duplicates using the Django-Garg API
var current_docs = {}
var BIS_dict = {}

var url_elems = window.location.href.split("/")
var url_mainIDs = {}
for(var i=0; i<url_elems.length; i++) {
  // if the this element is a number:
  if(url_elems[i]!="" && !isNaN(Number(url_elems[i]))) {
    url_mainIDs[url_elems[i-1]] = Number(url_elems[i]);
  }
}
var theurl = "/api/nodes/"+url_mainIDs["corpus"]+"/children/duplicates?keys=title&limit=9999"
// $.ajax({
//   url: theurl,
//   success: function(data) {
//     bisarray = data.data
//     for(var i in bisarray) {
//         untitlebis = bisarray[i].values
//         BIS_dict[untitlebis[0]] = [bisarray[i].count , 0];// [ total amount , removed ]
//     }
//     pr(BIS_dict)
//     if(Object.keys(BIS_dict).length>0) $("#delAll").css("visibility", "visible"); $("#delAll").show();
//   }
// });





function getRecord(rec_id) {
  return MyTable.data('dynatable').settings.dataset.originalRecords[rec_id];
  // return AjaxRecords[rec_id]
}

function getRecords() {
  return MyTable.data('dynatable').settings.dataset.originalRecords;
}

function transformContent2(rec_id) {
  // pr("\t\ttransformContent2: "+rec_id)
  var elem = AjaxRecords[rec_id];
  var result = {}
  // console.log("\t\t\telement flag : "+elem["flag"])
  if (elem["flag"]) {
    result["id"] = elem["id"]
    result["score"] = '<div class="'+elem["flag"]+'"><i>'+elem["score"]+'</div>'
    result["name"] = '<div class="'+elem["flag"]+'"><i>'+elem["name"]+'</div>'
    result["flag"] = '<input id='+rec_id+' onclick="overRide(this)" type="checkbox" checked/>'
  } else {
    result["id"] = elem["id"]
    result["score"] = elem["score"]
    result["name"] = elem["name"]
    result["flag"] = '<input id='+rec_id+' onclick="overRide(this)" type="checkbox"/>'
  }

  return result;
}

function overRide(elem) {
  var id = elem.id
  var current_flag = $("input[type='radio'][name='radios']:checked").val()
  var this_newflag = (current_flag==AjaxRecords[id]["flag"])?false:current_flag

  console.log("striking: "+id+" | this-elem_flag: "+AjaxRecords[id]["flag"]+" | current_flag: "+current_flag)
  console.log("\t so the new flag is: "+this_newflag)
  AjaxRecords[id]["flag"] = Mark_NGram ( id , AjaxRecords[id]["flag"] , this_newflag );

  MyTable.data('dynatable').dom.update();

}

function transformContent(rec_id , header , content) {
  if(header=="flag") {
    // pr("\t\ttransformContent1: "+rec_id)
    if(content==true) return '<input id='+rec_id+' onclick="overRide(this)" type="checkbox" checked/>'
    if(content==false) return '<input id='+rec_id+' onclick="overRide(this)" type="checkbox"/>'
  } else return content;
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


//generic enough
function ulWriter(rowIndex, record, columns, cellWriter) {
  // pr("\tulWriter: "+record.id)
  var tr = '';
  var cp_rec = {}
  if(!MyTable) {
    for(var i in record) {
      cp_rec[i] = transformContent(RecDict[record.id], i , record[i])
    }
  } else {
    // pr("\t\tbfr transf2: rec_id="+record.id+" | arg="+RecDict[record.id])
    cp_rec = transformContent2(RecDict[record.id])
  }
  // grab the record's attribute for each column
  // console.log("\tin ulWriter:")
  // console.log(record)
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }
  var data_id = RecDict[record.id]
  return '<tr data-stuff='+data_id+'>' + tr + '</tr>';
}





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
      div_table += "\t"+"\t"+'<th data-dynatable-column="name"><span class="glyphicon glyphicon-text-size"></span> Title</th>'+"\n"
      div_table += "\t"+"\t"+'<th data-dynatable-column="score" data-dynatable-sorts="score">No. Pubs</th>'+"\n"
      // div_table += "\t"+"\t"+'<th id="score_column_id" data-dynatable-sorts="score" data-dynatable-column="score">Score</th>'+"\n"
      div_table += "\t"+"\t"+'</th>'+"\n"
      div_table += "\t"+'</thead>'+"\n"
      div_table += "\t"+'<tbody>'+"\n"
      div_table += "\t"+'</tbody>'+"\n"
      div_table += '</table>'+"\n"
      div_table += '</p>';
    $("#div-table").html(div_table)


    // $("#stats").html(div_stats)


    var ID = 0
    console.log("Filling 'AjaxRecords' from argument 'data'")
    for(var i in data) {
      console.log(" >>" + i)

      // var le_ngram = data.ngrams[i]

      var orig_id = ID
      var arr_id = parseInt(ID)
      RecDict[orig_id] = arr_id;

      var url_title = encodeURIComponent(i)//.replace(" ","+")
      // url_title = i.replace(" ","+")
      var node_info = {
        "id" : ID,
        "name" : '<a target=_blank href="http://search.iscpif.fr/?categories=general&q='+url_title+'">'+i+'</a>',
        "score": data[i],
      }
      AjaxRecords.push(node_info)

      if ( ! DistributionDict[node_info.score] ) DistributionDict[node_info.score] = 0;
      DistributionDict[node_info.score]++;

      ID++;
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
                  var value = d.data.value.avg ? d.data.value.avg : d.data.value;
                  if (isNaN(value)) value = 0;
                  return value+" sources with "+Number(d.key)+" publications";
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
            })
            .on("filtered", function (chart) {
                dc.events.trigger(function () {
                    var chartfilt = chart.filter()
                    console.log("lalaal move chart", chartfilt)
                    // tricky part: identifying when the moveChart changes.
                    if(chartfilt) {
                        Push2Buffer ( chartfilt )
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
              });


    console.log("After table 1")
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
    console.log("After table 2")

    // // // $("#score_column_id").children()[0].text = FirstScore
    // // // // MyTable.data('dynatable').process();

    if ( $(".imadiv").length>0 ) return 1;
    $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
    $(".dynatable-record-count").insertAfter(".imadiv")
    $(".dynatable-pagination-links").insertAfter(".imadiv")

//    $('<div class="imadiv"></div>').insertAfter("#my-ajax-table")
//    $(".dynatable-record-count").insertAfter(".imadiv")
//    $(".dynatable-pagination-links").insertAfter(".imadiv")

    console.log("After table 3")
    return "OK"
}



console.log(window.location.href)

// match corpus_id in the url
var corpus_id ;
rematch = window.location.href.match(/corpora\/(\d+)\/sources\/?$/)
if (rematch) {
    corpus_id = rematch[1] ;
    $.ajax({
      url: window.location.origin
            + "/api/nodes/"
            + corpus_id
            + "/facets?hyperfield=source",
      success: function(data){


        console.log(data)
        $("#content_loader").remove()
        // // Initializing the Charts and Table
        var result = Main_test( data.by.source , "FirstScore" )
        console.log( result )

        $("#content_loader").remove()

      }
    });
}
