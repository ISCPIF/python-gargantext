
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
    console.log( " = = = = = = = = " )
    console.log( "Push2Buffer()" )
    console.log( "\t"+NewVal )
    if ( TheBuffer == false) {
        if( ! NewVal ) {
            // var limits = [ new Date( oldest[0],oldest[1],oldest[2] ) , new Date( latest[0],latest[1],latest[2] ) ];
            var limits = [new Date(oldest[0],oldest[1]-1,oldest[2]), new Date(latest[0],latest[1]-1,latest[2] ) ];
            limits[0] = new Date(limits[0].setDate(limits[0].getDate()-1) );
            limits[1] = new Date(limits[1].setDate(limits[1].getDate()+1) );
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
            var limits = [new Date(oldest[0],oldest[1]-1,oldest[2]), new Date(latest[0],latest[1]-1,latest[2] ) ];
            limits[0] = new Date(limits[0].setDate(limits[0].getDate()-1) );
            limits[1] = new Date(limits[1].setDate(limits[1].getDate()+1) );
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

    var dataini = TheBuffer[0].toISOString().split("T")[0]
    var datafin = TheBuffer[1].toISOString().split("T")[0]
    pr("show me the pubs of the selected period")
    console.log( TheBuffer )
    pr("\tfrom ["+dataini+"] to ["+datafin+"]")

    TimeRange = []
    for (var i in AjaxRecords) {
        if(AjaxRecords[i].date>=dataini && AjaxRecords[i].date<=datafin){
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

var url_elems = window.location.href.split("/")
var url_mainIDs = {}
for(var i=0; i<url_elems.length; i++) {
  // if the this element is a number:
  if(url_elems[i]!="" && !isNaN(Number(url_elems[i]))) {
    url_mainIDs[url_elems[i-1]] = Number(url_elems[i]);
  }
}






//          STEP 02:
//      D3.js: Interactive timerange.
var moveChart = dc.compositeChart("#monthly-move-chart"); 
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
  // pr("\t"+elem.title)
  var result = {}
  if (elem["del"]) {
    result["id"] = elem["id"]
    result["date"] = '<strike>'+elem["date"]+'</strike>'
    result["name"] = '<strike>'+elem["name"]+'</strike>'
    result["del"] = '<input id='+rec_id+' onclick="overRide(this)" type="checkbox" checked/>'
  } else {
    result["id"] = elem["id"]
    result["date"] = elem["date"]
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


$("#move2trash")
.click(function(){

    var ids2trash = []
    for(var i in Garbage) {
      ids2trash.push(AjaxRecords[i].id);
    }

    console.log("ids to the trash:")
    console.log(ids2trash)

    $.ajax({
      url: "/tests/move2trash/",
      data: "nodeids="+JSON.stringify(ids2trash),
      type: 'POST',
      beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
      },
      success: function(data) {
        console.log("in #move2trash")
        console.log(data)
        location.reload();
      },
        error: function(result) {
            console.log("Data not found in #move2trash");
            console.log(result)
        }
    });
})
.hide();

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


function Main_test( Data , SearchFilter ) {

  var DistributionDict = {}
  for(var i in DistributionDict)
    delete DistributionDict[i];
  delete DistributionDict;
  DistributionDict = {}


  $("#div-table").html("")
  $("#div-table").empty();
  var div_table = '<p align="right">'+"\n"
    div_table += '<table id="my-ajax-table" class="table table-bordered">'+"\n"
    div_table += "\t"+'<thead>'+"\n"
    div_table += "\t"+"\t"+'<th width="100px;" data-dynatable-column="date">Date</th>'+"\n"
    div_table += "\t"+"\t"+'<th data-dynatable-column="name">Title</th>'+"\n"
    div_table += "\t"+"\t"+'<th data-dynatable-column="del" data-dynatable-no-sort="true">Trash</th>'+"\n"
    div_table += "\t"+"\t"+'</th>'+"\n"
    div_table += "\t"+'</thead>'+"\n"
    div_table += "\t"+'<tbody>'+"\n"
    div_table += "\t"+'</tbody>'+"\n"
    div_table += '</table>'+"\n"
    div_table += '</p>';
  $("#div-table").html(div_table)

  var justdates = {}
  for(var i in Data) {
    var date = Data[i]["date"];  
    if ( ! justdates[date] ) justdates[date] = 0;
    justdates[date]++;
    // console.log(Data[i]["date"]+"  :  originalRecords["+arr_id+"] <- "+orig_id+" | "+Data[i]["name"])
  }

  var t0 = AjaxRecords[0].date.split("-").map(Number)
  var t1 = AjaxRecords.slice(-1)[0].date.split("-").map(Number)
  oldest = t0;
  latest = t1;

  TheBuffer = [new Date(t0[0],t0[1]-1,t0[2]), new Date(t1[0],t1[1]-1,t1[2] ) ];
  TheBuffer[0] = new Date(TheBuffer[0].setDate(TheBuffer[0].getDate()-1) );
  TheBuffer[1] = new Date(TheBuffer[1].setDate(TheBuffer[1].getDate()+1) );

  var arrayd3 = []
  for(var e in Data) {
      var date = Data[e]["date"]; 
      if(justdates[date]!=false) {
          var info = {}
          info.date = date
          info.dd = dateFormat.parse(date)
          info.month = d3.time.month(info.dd)
          info.volume = justdates[date]
          arrayd3.push(info)
          justdates[date] = false;
      }
  }

  for(var i in justdates)
      delete justdates[i];
  delete justdates;

  var ndx = crossfilter(arrayd3);
  var all = ndx.groupAll();

  //volumeChart:(1)
  //moveChart:(1)
  // monthly index avg fluctuation in percentage
  var moveMonths = ndx.dimension(function (d) {
      return d.month;
  });

  //moveChart:(3)
  var monthlyMoveGroup = moveMonths.group().reduceSum(function (d) {
      return d.volume;
      //return Math.abs(+d.close - +d.open);
  });

  //volumeChart:(2)
  var volumeByMonthGroup = moveMonths.group().reduceSum(function (d) {
      return d.volume / 500000;
  });

  //moveChart:(2)
  var indexAvgByMonthGroup = moveMonths.group().reduce(
          function (p, v) {
              ++p.days;
              p.total += (+v.open + +v.close) / 2;
              p.avg = Math.round(p.total / p.days);
              return p;
          },
          function (p, v) {
              --p.days;
              p.total -= (+v.open + +v.close) / 2;
              p.avg = p.days == 0 ? 0 : Math.round(p.total / p.days);
              return p;
          },
          function () {
              return {days: 0, total: 0, avg: 0};
          }
  );


  moveChart.width(800)
          .height(150)
          .transitionDuration(1000)
          .margins({top: 10, right: 50, bottom: 25, left: 40})
          .dimension(moveMonths)
          .group(indexAvgByMonthGroup)
          .valueAccessor(function (d) {
              return d.value.avg;
          })
          .x(d3.time.scale().domain([new Date(t0[0],t0[1],t0[2]), new Date(t1[0],t1[1],t1[2])]))
          .round(d3.time.month.round)
          .xUnits(d3.time.months)
          .elasticY(true)
          .renderHorizontalGridLines(true)
          .brushOn(false)
          .compose([
              dc.lineChart(moveChart)
                      .group(indexAvgByMonthGroup)
                      .valueAccessor(function (d) {
                          return d.value.avg;
                      })
                      .renderArea(true)
                      .stack(monthlyMoveGroup, function (d) {
                          return d.value;
                      })
                      .title(function (d) {
                          var value = d.value.avg ? d.value.avg : d.value;
                          if (isNaN(value)) value = 0;
                          return dateFormat(d.key) + "\n" + numberFormat(value);
                      })
          ])
          .xAxis();

  volumeChart.width(800)
          .height(100)
          .margins({top: 0, right: 50, bottom: 20, left: 40})
          .dimension(moveMonths)
          .group(volumeByMonthGroup)
          .centerBar(true)
          .gap(0)
          .x(d3.time.scale().domain([TheBuffer[0], TheBuffer[1] ]))
          .round(d3.time.month.round)
          .xUnits(d3.time.months)
          .renderlet(function (chart) {
              chart.select("g.y").style("display", "none");
              moveChart.filter(chart.filter());
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
                  moveChart.focus(chartfilt);
              });
          });

  dc.renderAll();

  MyTable = []
  MyTable = $('#my-ajax-table').dynatable({
              dataset: {
                records: Data
              },
              features: {
                pushState: false,
                // sort: false //i need to fix the sorting function... the current one just sucks
              },
              // inputs: {
              //   queries: $('#searchAB')
              // },
              writers: {
                _rowWriter: ulWriter
                // _cellWriter: customCellWriter
              }
            });

  MyTable.data('dynatable').paginationPage.set(1);
  MyTable.data('dynatable').process();

  if ( $(".imadiv").length>0 ) return 1;
  $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
  $(".dynatable-record-count").insertAfter(".imadiv")
  $(".dynatable-pagination-links").insertAfter(".imadiv")
  
  $("#filter_search").html( $("#filter_search").html().replace('selected="selected"') );
  $("#"+SearchFilter).attr( "selected" , "selected" )

  var the_content = $("#filter_search").html();
  $(""+the_content).insertAfter("#dynatable-query-search-my-ajax-table")


  // $('#searchAB').click( function() {
  //   if($(this).is(':checked')) {
  //       console.log( "Do stuff")
  //       $("#dynatable-query-search-my-ajax-table").keyup(function (e) {
  //         if (e.keyCode == 13) {
  //           console.log("Do stuff: Just pressed ENTER")
  //         }
  //       })
  //   }
  // });
    // MyTable.data('dynatable').settings.inputs.queries = { $('#searchAB') }

  // .insertAfter("#dynatable-query-search-my-ajax-table")
  
  return "OK"
}




function SearchFilters( elem ) {
  var MODE = elem.value;

  if( MODE == "filter_all") {
    var result = Main_test(AjaxRecords , MODE)
    console.log( result )
  }

  if( MODE == "filter_dupl-titles") {

    var getDupl_API = "/api/nodes/"+url_mainIDs["corpus"]+"/children/duplicates?keys=title&limit=9999"
    $.ajax({
      url: getDupl_API,
      success: function(data) {
        bisarray = data.data
        for(var i in bisarray) {
            titlebis = bisarray[i].values
            BIS_dict[titlebis[0]] = true;
        }
        var Duplicates = []
        for(var r in AjaxRecords) {
          if ( BIS_dict[AjaxRecords[r].title] )
            Duplicates.push( AjaxRecords[r] )
        }
        var result = Main_test(Duplicates , MODE)
        console.log( result )

        MyTable.data('dynatable').sorts.clear();
        MyTable.data('dynatable').sorts.add('title', 1) // 1=ASCENDING,
        MyTable.data('dynatable').process();
      }
    });

  }

}





// FIRST portion of code to be EXECUTED:
// (3) Get records and hyperdata for paginator
$.ajax({
  url: '/tests/paginator/corpus/'+url_mainIDs["corpus"],
  success: function(data){
    $("#content_loader").remove()
    for(var i in data.records) {
      var orig_id = parseInt(data.records[i].id)
      var arr_id = parseInt(i)
      RecDict[orig_id] = arr_id;
      data.records[i]["title"] = data.records[i]["name"];
      data.records[i]["name"] = '<a target="_blank" href="/project/'+url_mainIDs["project"]+'/corpus/'+ url_mainIDs["corpus"] + '/document/'+orig_id+'">'+data.records[i]["name"]+'</a>'
      data.records[i]["del"] = false
    }
    AjaxRecords = data.records; // backup-ing in global variable!

    var result = Main_test(data.records , "filter_all")
    console.log( result )
  },
});




