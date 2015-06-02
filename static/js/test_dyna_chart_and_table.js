
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
        if(AjaxRecords[i].occs>=dataini && AjaxRecords[i].occs<=datafin){
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
            sort: false
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
var corpusid = window.location.href.split("corpus")[1].replace(/\//g, '')//replace all the slashes
var theurl = "/api/nodes/"+corpusid+"/children/duplicates?keys=title&limit=9999"
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



//          STEP 02:
//      D3.js: Interactive timerange.
var LineChart = dc.lineChart("#monthly-move-chart"); 
var volumeChart = dc.barChart("#monthly-volume-chart");
var dateFormat = d3.time.format("%Y-%m-%d");
var numberFormat = d3.format(".2f");


var MyTable;
var RecDict={};
var AjaxRecords = []
var Garbage = {}

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
  // pr("\t\t\t"+elem.date)
  var result = {}
  if (elem["del"]) {
    result["id"] = elem["id"]
    result["occs"] = '<strike>'+elem["occs"]+'</strike>'
    result["name"] = '<strike>'+elem["name"]+'</strike>'
    result["del"] = '<input id='+rec_id+' onclick="overRide(this)" type="checkbox" checked/>'
  } else {
    result["id"] = elem["id"]
    result["occs"] = elem["occs"]
    result["name"] = elem["name"]
    result["del"] = '<input id='+rec_id+' onclick="overRide(this)" type="checkbox"/>'
  }
  return result;
}

function overRide(elem) {
  var id = elem.id
  var val = elem.checked
  console.log("striking: ")
  console.log(AjaxRecords[id])
  // MyTable.data('dynatable').settings.dataset.originalRecords[id]["del"] = val;
  AjaxRecords[id]["del"] = val;

  if(val) Garbage[id] = true;
  else delete Garbage[id];
  if(Object.keys(Garbage).length>0) $("#move2trash").show();
  else $("#move2trash").hide();
  // console.log(MyTable.data('dynatable').settings.dataset.originalRecords[id])
  MyTable.data('dynatable').dom.update();
}

function transformContent(rec_id , header , content) {
  if(header=="del") {
    // pr("\t\ttransformContent1: "+rec_id)
    if(content==true) return '<input id='+rec_id+' onclick="overRide(this)" type="checkbox" checked/>'
    if(content==false) return '<input id='+rec_id+' onclick="overRide(this)" type="checkbox"/>'
  } else return content;
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
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }
  return '<tr>' + tr + '</tr>';
}


console.log(window.location.href+"/ngrams.json")
$.ajax({
  url: window.location.href+"/ngrams.json",
  success: function(data){

    var DistributionDict = {}
    var arrayd3 = []

    for(var i in data.ngrams) {
    
      var le_ngram = data.ngrams[i]

      var orig_id = le_ngram.id
      var arr_id = parseInt(i)
      RecDict[orig_id] = arr_id;

      var node_info = {
        "id" : le_ngram.id,
        "name": le_ngram.name,
        "occs": le_ngram.scores.occ_uniq,
        "del":false
      }
      AjaxRecords.push(node_info)

      if ( ! DistributionDict[node_info.occs] ) DistributionDict[node_info.occs] = 0;
      DistributionDict[node_info.occs]++;


      // var info = {}
      // info.name = node_info.name
      // info.volume = node_info.occs;
      // arrayd3.push(info)


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

    var ndx = crossfilter();
    ndx.add(DistributionList);

    // x_occs  = ndx.dimension(dc.pluck('x_occ'));
    var x_occs = ndx.dimension(function (d) {
        return d.x_occ;
    });


    // y_frecs = x_occs.group().reduceSum(dc.pluck('y_frec'));
    var y_frecs = x_occs.group().reduceSum(function (d) {
        return d.y_frec;
    });

    // var y_frecs_2  = ndx.dimension(dc.pluck('y_frec'));
    // var x_occs_2 = y_frecs_2.group().reduceSum(dc.pluck('x_occ'));


    console.log("occs: [ "+min_occ+" , "+max_occ+" ] ")
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
      // .elasticY(true)
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
                  return value+" ngrams with occ="+Number(d.key);
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
            .x(d3.scale.linear().domain([min_occ/2,max_occ]))
            .y(d3.scale.sqrt().domain([min_frec/2,max_frec]))
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




      MyTable = $('#my-ajax-table').dynatable({
                  dataset: {
                    records: AjaxRecords
                  },
                  features: {
                    pushState: false,
                    sort: false //i need to fix the sorting function... the current one just sucks
                  },
                  writers: {
                    _rowWriter: ulWriter
                    // _cellWriter: customCellWriter
                  }
                });

      if ( $(".imadiv").length>0 ) return 1;
      $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
      $(".dynatable-record-count").insertAfter(".imadiv")
      $(".dynatable-pagination-links").insertAfter(".imadiv")
    
  }
});