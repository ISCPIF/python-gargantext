
function get_node_date(node) {
    var hyperdata = node.hyperdata;
    return new Date(
        Number(hyperdata.publication_year),
        Number(hyperdata.publication_month) - 1,
        Number(hyperdata.publication_day)
    );
};

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
    var UpdateTable = false
    if (action=="changerange") {
        UpdateTable = true;
    }

    pr("update table??: "+UpdateTable)

    if ( ! UpdateTable ) return false; //stop whatever you wanted to do.

    var TimeRange = AjaxRecords;

    var dataini = TheBuffer[0];
    var datafin = TheBuffer[1];
    pr("show me the pubs of the selected period")
    // console.log( TheBuffer )
    pr("\tfrom ["+dataini+"] to ["+datafin+"]")

    TimeRange = []
    // console.log("dataini, datafin")
    // console.log(dataini, datafin)
    $.each(AjaxRecords, function(i, node) {
        if (node.date >= dataini && node.date <= datafin) {
            // pr( AjaxRecords[i].date+" : "+AjaxRecords[i].id )
            TimeRange.push(node);
        }
    });
    // console.log(TimeRange)

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
//      remember url elements

var id_from_url = function(nodename) {
    var regex = new RegExp(nodename + '/(\\d+)');
    var result = regex.exec(location.href);
    return result ? result[1] : null;
};
var project_id = id_from_url('projects');
var corpus_id = id_from_url('corpora');



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
var countByTitles = {}  // useful for title duplicates
var countByMeta = {}  //         for title + date + source duplicates
var favorites = {}

function getRecord(rec_id) {
  return MyTable.data('dynatable').settings.dataset.originalRecords[rec_id];
  // return AjaxRecords[rec_id]
}

function getRecords() {
  return MyTable.data('dynatable').settings.dataset.originalRecords;
}

function favstatusToStar (rec_id, boolFavstatus, boolStrike=false){
    var starStr = boolFavstatus ? "glyphicon-star" : "glyphicon-star-empty";
    var styleStr = boolStrike ? "style='text-decoration:line-through'" : "";
    var htmlStr  = "<span class='glyphicon "+starStr+"' "+styleStr ;
        htmlStr += " onclick='toggleFavstatus("+rec_id+")'" ;
        htmlStr += ">" ;
        htmlStr += "</span>" ;
    return htmlStr
}

function toggleFavstatus (rec_id) {
    var doc_id = AjaxRecords[rec_id]["id"]
    var statusBefore = AjaxRecords[rec_id]["isFavorite"]
    var myHttpAction = statusBefore ? 'DELETE' : 'PUT'

    $.ajax({
      url: window.location.origin + '/api/nodes/'+corpus_id+'/favorites?docs='+doc_id,
      type: myHttpAction,
      beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
      },
      success: function(favdata) {
          // it's been toggled in the DB so we toggle locally
          if (statusBefore) delete favorites[doc_id]
          else favorites[doc_id] = true
          AjaxRecords[rec_id]["isFavorite"] = ! statusBefore ;

          // and we reprocess table directly (no need for new ajax of other recs)
          MyTable.data('dynatable').process();
      },
    });
}

function transformContent2(rec_id, trClass) {
  // pr("\t\ttransformContent2: "+rec_id)
  var elem = AjaxRecords[rec_id];
  // pr("\t"+elem.rawtitle)
  var result = {}

  if (elem["del"]) {
    result["id"] = elem["id"]
    result["short_date"] = '<strike>'+elem["short_date"]+'</strike>'
    result["hyperdata.source"] = '<strike><small><i>'+elem["hyperdata"]["source"]+'</small></i></strike>'
    result["docurl"] = '<strike>'+elem["docurl"]+'</strike>'
    result["isFavorite"] = favstatusToStar(rec_id, elem["isFavorite"], boolStrike=true)
    result["rawtitle"] = elem["rawtitle"]
    if (trClass == "normalrow" || trClass == "duplrowdel") {
        result["del"] = '<input id='+rec_id+' class="trash1" onclick="toggleTrashIt(this)" type="checkbox" checked></input>'
    }
    else if (trClass=="duplrowkeep") {
        // forbid deletion for one of the duplicates
        result["del"] = ''
    }
  } else {
    result["id"] = elem["id"]
    result["short_date"] = elem["short_date"]
    result["hyperdata.source"] = '<small><i>'+elem["hyperdata"]["source"]+'</i></small>'
    result["docurl"] = elem["docurl"]
    result["isFavorite"] =  favstatusToStar(rec_id, elem["isFavorite"])
    result["rawtitle"] = elem["rawtitle"]
    if (trClass == "normalrow" || trClass == "duplrowdel") {
        result["del"] = '<input id='+rec_id+' class="trash1" onclick="toggleTrashIt(this)" type="checkbox"></input>'
    }
    else if (trClass=="duplrowkeep") {
        result["del"] = ''
    }
  }
  return result;
}

/*  Trash one element
 *   -> strike it
 *   -> move it to Garbage global var
 *
 *   @param boxElem    the html checkbox element that was just (un)checked
 *                     <input id="185" class="trash1" onclick="toggleTrashIt(this)" type="checkbox">
 *
 *   @param doUpdate   optional boolean (default: true)
 *                     possibility to control the dynatable update after trashing
 *                     (set it to false if several operations are done at once)
 */
function toggleTrashIt(boxElem, doUpdate) {
  var id = boxElem.id       // row_id in the table (not ngram_id)
  var val = boxElem.checked

  if (typeof doUpdate == 'undefined') {
      doUpdate = true ;
  }
  // console.log("striking =>", val)
  // console.log("record", AjaxRecords[id])

  AjaxRecords[id]["del"] = val;

  if(val) Garbage[id] = true;
  else delete Garbage[id];
  if(Object.keys(Garbage).length>0) $("#empty-trash").show();
  else $("#empty-trash").hide();

  if (doUpdate) {
      MyTable.data('dynatable').dom.update();
  }
}

// function transformContent(rec_id , header , content) {
//     console.warn("hello transformContent1")
//     if(header=="del") {
//         // pr("\t\ttransformContent1: "+rec_id)
//         if(content==true) return '<input id='+rec_id+' onclick="toggleTrashIt(this)" type="checkbox" checked/>'
//         if(content==false) return '<input id='+rec_id+' onclick="toggleTrashIt(this)" type="checkbox"/>'
//     }
//     else return content;
// }


$("#empty-trash")
.click(function(){

    var ids2trash = []
    for(var i in Garbage) {
      ids2trash.push(AjaxRecords[i].id);
    }

    console.log("ids to the trash:")
    console.log(ids2trash)

    $.ajax({
      url : window.location.origin + "/api/nodes?ids="+ids2trash,
      //data: 'ids:'+JSON.stringify(ids2trash),
      type: 'DELETE',
      beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
      },
      success: function(data) {
        console.log("in #empty-trash")
        console.log(data)
        location.reload();
      },
        error: function(result) {
            console.log("Data not found in #empty-trash");
            console.log(result)
        }
    });
})
.hide();

//generic enough
function ulWriter(rowIndex, record, columns, cellWriter) {

    var trClass = 'normalrow'

    // special case ------------------------------------------------- 8< -------
    // set the tr class to show duplicates in another light
    // normalrow|duplrowdel|duplrowkeep (the last 2 for duplicate case)
    if (dupFlag) {
        // console.log("dupFlag in ulWriter")
        recId = RecDict[record.id]
        if (recId == countByMeta[record.signature]['smallest_id']) {
            trClass = 'duplrowkeep'
        }
        else {
            trClass = 'duplrowdel'
        }
    }
    // -------------------------------------------------------------- 8< -------

  // pr("\tulWriter: "+record.id)
  var tr = '';
  var cp_rec = {}

  if(!MyTable) {
    // £TODO check if ever used
    for(var i in record) {
      cp_rec[i] = transformContent(RecDict[record.id], i , record[i])
    }
  } else {
    // pr("\t\tbfr transf2: rec_id="+record.id+" | arg="+RecDict[record.id])
    cp_rec = transformContent2(RecDict[record.id], trClass)
  }
  // grab the record's attribute for each column
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }

  return '<tr class='+trClass+' node-id='+record.id+'>' + tr + '</tr>';
}


// creates a unique string defining the document's metadata: title, source, date
// doc Record => string
// (useful for de-duplication of documents with the same meta)
// format: title--source--date
function metaSignature(docRecord) {
    var keyStr = ""
    keyStr = (docRecord.rawtitle
                +"--"+
              docRecord.hyperdata.source
                +"--"+
              docRecord.hyperdata.publication_date
          )
    return keyStr
}


function Main_test(Data) {

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
    div_table += "\t"+"\t"+'<th width="100px;" data-dynatable-column="short_date">'+"\n"
    div_table += "\t"+"\t"+'<span class="glyphicon glyphicon-calendar"></span> Date</th>'+"\n"
    div_table += "\t"+"\t"+'<th data-dynatable-column="docurl">'+"\n"
    div_table += "\t"+"\t"+'<span class="glyphicon glyphicon-text-size"></span> Title</th>'+"\n"
    div_table += "\t"+"\t"+'<th width="100px;" data-dynatable-column="hyperdata.source">'+"\n"
    div_table += "\t"+"\t"+'<span class="glyphicon glyphicon-book"></span> Source</th>'+"\n"
    div_table += "\t"+"\t"+'<th data-dynatable-column="isFavorite">'+"\n"
    div_table += "\t"+"\t"+'<span class="glyphicon glyphicon-star"></span>'+"\n"
    div_table += "\t"+"\t"+'</th>'+"\n"
    div_table += "\t"+"\t"+'<th data-dynatable-column="del" data-dynatable-no-sort="true">'+"\n"
    div_table += "\t"+"\t"+'<span class="glyphicon glyphicon-trash" style="padding:3 2 0 0"></span>'+"\n"
    div_table += "\t"+"\t"+'<p class="note" style="padding:0 0 1 3">'
    div_table += "\t"+"\t"+"\t"+'<input type="checkbox" id="trashAll"'
    div_table += "\t"+"\t"+"\t"+' onclick="trashAll(this)" title="Check to mark all for trash"></input>'
    div_table += "\t"+"\t"+"\t"+'<label>All page</label>'
    div_table += "\t"+"\t"+'</p>'
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
    // console.log(Data[i]["date"]+"  :  originalRecords["+arr_id+"] <- "+orig_id+" | "+Data[i]["docurl"])
  }

  var t0 = get_node_date(AjaxRecords[0]);
  var t1 = get_node_date(AjaxRecords.slice(-1)[0]);
  oldest = t0;
  latest = t1;
  // console.log('t0, t1')
  // console.log(t0, t1)

  TheBuffer = [t0, t1];
  TheBuffer[0] = new Date(TheBuffer[0].setDate(TheBuffer[0].getDate()-1) );
  TheBuffer[1] = new Date(TheBuffer[1].setDate(TheBuffer[1].getDate()+1) );

  var arrayd3 = []
  $.each(Data, function(i, node) {
      if (node.date) {
          arrayd3.push({
            //   date: get_node_date(node),
            //   dd: node.date,
              month: d3.time.month(node.date),
              dailyvolume: justdates[date],
          });
      }
  });

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

  // console.warn(moveMonths)

  //moveChart:(3)
  var monthlyMoveGroup = moveMonths.group().reduceSum(function (d) {
      return d.dailyvolume;
      //return Math.abs(+d.close - +d.open);
  });

  //volumeChart:(2)
  var volumeByMonthGroup = moveMonths.group().reduceSum(function (d) {
      return d.dailyvolume / 500000;
  });

  //moveChart:(2) (cf. https://dc-js.github.io/dc.js/docs/stock.html#section-14)
  var indexAvgByMonthGroup = moveMonths.group().reduce(
          function (p, v) {
            //   console.log("dc:dimension:reduce:filter_add")
              ++p.nb;
              p.total += v.dailyvolume
              return p;
          },
          function (p, v) {
            //   console.log("dc:dimension:reduce:filter_remove")
              --p.nb;
              p.total -= v.dailyvolume
              return p;
          },
          function () {
            //   console.log("dc:dimension:reduce:init")
              return {total: 0, nb: 0};
          }
  );


  moveChart.width(800)
          .height(150)
          .transitionDuration(1000)
          .margins({top: 10, right: 50, bottom: 25, left: 40})
          .dimension(moveMonths)
          .group(indexAvgByMonthGroup)
          .valueAccessor(function (d) {
              return d.value.total;
          })
          .x(d3.time.scale().domain([t0, t1]))
          .round(d3.time.month.round)
          .xUnits(d3.time.months)
          .elasticY(true)
          .renderHorizontalGridLines(true)
          .brushOn(false)
          .compose([
              dc.lineChart(moveChart)
                      .group(indexAvgByMonthGroup)
                      // here d are already data grouped by month
                      .valueAccessor(function (d) {
                        //   console.log(d)
                          return d.value.total;
                      })
                      .renderArea(true)
                      // orange
                    //   .stack(monthlyMoveGroup, function (d) {
                    //     //   console.log(d)
                    //       return d.value;
                    //   })
                      .title(function (d) {
                          var value = d.data.value.total ? d.data.value.total : d.data.value;
                          if (isNaN(value)) value = 0;
                          return dateFormat(d.data.key) + "\n" + numberFormat(value);
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
          })
          .on("filtered", function (chart) {
              dc.events.trigger(function () {
                  var chartfilt = chart.filter()
                  console.log("lalaal move chart", chartfilt)
                  // tricky part: identifying when the moveChart changes.
                  if(chartfilt) {
                      console.log("chart.filter()")
                      console.log(chartfilt)
                      Push2Buffer (chartfilt)
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
                records: Data,
                sorts : {"date": 1},
                sortTypes: {
                    signature: 'signatureSort',
                    docurl: 'rawtitleSort',
                    'hyperdata.source': 'sourceSort'
                }
              },
              features: {
                pushState: false,
                // prevent default title search which can't do title vs abstract
                search: false,
                sort: true
              },
              inputs: {
                // our own search which differentiates title vs abstract queries
                queries: $('#doubleSearch, #docFilter')
              },
              writers: {
                _rowWriter: ulWriter
                // _cellWriter: customCellWriter
              }
            });

  MyTable.data('dynatable').paginationPage.set(1);
  // MyTable.data('dynatable').process();

  if ( $(".imadiv").length>0 ) return 1;
  $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
  $(".dynatable-record-count").insertAfter(".imadiv")
  $(".dynatable-pagination-links").insertAfter(".imadiv")

//  $('<div class="imadiv"></div>').insertAfter("#my-ajax-table")
//  $(".dynatable-record-count").insertAfter(".imadiv")
//  $(".dynatable-pagination-links").insertAfter(".imadiv")
    // binds a custom filter to our 'doubleSearch' via dynatable.queries.functions
  MyTable.data('dynatable').queries
      .functions['doubleSearch'] = function(record,searchString) {

          // global context
          doAbstractsSearch = $("#searchAB").is(':checked')

          // NB searchString == $("#doubleSearch").val()

          // by default we always decide to search in the title
          matchInTexts = [record.rawtitle]

          // if box is checked we'll also search in the abstracts (todo: via ajax)
          if (doAbstractsSearch) {
              if (typeof record.hyperdata.abstract !== 'undefined') {
                  matchInTexts.push(record.hyperdata.abstract)
              }
          }

          // inspired from the default cf. dynatable.queries.functions['search']
          var contains = false;
          for (i in matchInTexts) {
              matchInText = matchInTexts[i]
              contains = (
                  matchInText.toLowerCase().indexOf(
                      searchString.toLowerCase()
                  ) !== -1
              )
              if (contains) { break; } else { continue; }
          }
          return contains;
        }
    // MyTable.data('dynatable').process();

    // also append another bound filter for duplicates/favorites
    MyTable.data('dynatable').queries
        .functions['docFilter'] = function(record,opt) {
            if      (opt == 'filter_all')  return true
            else if (opt == 'filter_favs') return favorites[record.id]
            else if (opt == 'filter_dupl_all') return (countByMeta[record.signature]['n'] > 1)
        }

    // and set this filter's initial status to 'filter_all'
    MyTable.data('dynatable').settings.dataset.queries['docFilter'] = 'filter_all'


    MyTable.data('dynatable').sorts.functions["rawtitleSort"] = makeAlphaSortFunctionOnProperty('rawtitle')
    MyTable.data('dynatable').sorts.functions["signatureSort"] = makeAlphaSortFunctionOnProperty('signature')
    MyTable.data('dynatable').sorts.functions["sourceSort"] = function sourceSort (rec1,rec2, attr, direction) {
        // like rawtitle but nested property
        if (rec1.hyperdata && rec1.hyperdata.source
            && rec2.hyperdata && rec2.hyperdata.source) {
            // the alphabetic sort
            if (direction == 1) return rec1.hyperdata.source.localeCompare(rec2.hyperdata.source)
            else                return rec2.hyperdata.source.localeCompare(rec1.hyperdata.source)
        }
        else if (rec1.hyperdata && rec1.hyperdata.source) {
            cmp = direction
        }
        else if (rec2.hyperdata && rec2.hyperdata.source) {
            cmp = -direction
        }
        else {
          cmp = 0
        }
        if (cmp == 0)       cmp = RecDict[rec1.id] < RecDict[rec2.id] ? -1 : 1
      }

    // hook on page change
    MyTable.bind('dynatable:page:set', tidyAfterPageSet)

    MyTable.data('dynatable').process();

    // re-apply search function on click
    $('#searchAB').click( function() {
      MyTable.data('dynatable').process();
    });

    // re-apply search function on ENTER
    $("#doubleSearch").keyup(function (e) {
      if (e.keyCode == 13) {
        MyTable.data('dynatable').process();
      }
    })

    // trashAll default position is: off
    $('#trashAll').prop("checked", false)
    // real trashAll states : SOME|ALL|NONE
    $('#trashAll').data("columnSelection", 'SOME')

    return "OK"
}


// select all column "trash"
// --------------------------
/**
 * Toggle all checkboxes in a column by changing their list in System
 *
 * effect => sets the "del" property of all visible records on this page
 *                ------------------
 *           (except if they are of class duplrowkeep)
 * cf more complex original function SelectPage() in NGrams_dyna_chart_and_table
 */

function trashAll() {
    var newColumnState = $("#trashAll").prop('checked')
    // propagate changes to all rows
    $("tbody tr").each(function (i, row) {
        // var nodeId = $(row).attr("node-id") ;
        // var recId = RecDict[nodeId]

        var exceptionUntrashable = row.classList.contains('duplrowkeep')
        if (!exceptionUntrashable) {
            var boxElem = row.getElementsByClassName("trash1")[0]
            var stateBefore = boxElem.checked
            if (stateBefore != newColumnState) {
                // toggle all these rows' boxes
                boxElem.checked = newColumnState
                // and trigger the corresponding action manually
                toggleTrashIt(boxElem, false)
                // false <=> don't update the table each time
            }
        }
    });

    // OK now update this table page
    MyTable.data('dynatable').dom.update();
}

// global flag when duplicates special filter is requested
var dupFlag = false ;

// intercept duplicates query to sort alphabetically **before** duplicates filter
$("#div-table").on("dynatable:queries:added", function(e, qname, qval) {
    // debug
    //console.warn(e)
    // console.warn("add", qname)
    // console.warn("add", qval)
    if (!dupFlag && qname == 'docFilter' && qval == "filter_dupl_all") {
        MyTable.data('dynatable').queries.remove('docFilter')
        // flag to avoid recursion when we'll call this filter again in 4 lines
        dupFlag = true ;
        // the sorting
        MyTable.data('dynatable').sorts.clear();
        MyTable.data('dynatable').sorts.add('signature', 1)
        // now we can add the query
        MyTable.data('dynatable').queries.add('docFilter', qval)
        MyTable.data('dynatable').process();
    }
    else if (qname == 'docFilter' && qval != "filter_dupl_all") {
        dupFlag = false
    }
});

$("#div-table").on("dynatable:queries:removed", function(e, qname, qval) {
    //console.warn(e)
    //console.warn("rm", qname)
    if (qname == 'docFilter') {
        dupFlag = false ;
    }
});


// create a sort function (alphabetic with locale-aware order)
// on any record.property with a str inside (for instance "rawtitle")
function makeAlphaSortFunctionOnProperty(property) {
    return function (rec1,rec2, attr, direction) {
        var cmp = null

        if (rec1[property] && rec2[property]) {
            // the alphabetic sort
            if (direction == 1) cmp = rec1[property].localeCompare(rec2[property])
            else                cmp = rec2[property].localeCompare(rec1[property])
        }
        else if (rec1[property]) {
            cmp = direction
        }
        else if (rec2[property]) {
            cmp = -direction
        }
        else {
          cmp = 0
        }

        // second level sorting on key = id in records array
        // (this one volontarily not reversable by direction
        //  so as to have smallest_id always on top in layout)
        if (cmp == 0)       cmp = RecDict[rec1.id] < RecDict[rec2.id] ? -1 : 1

        return cmp
    }
}

/**
 * tidyAfterPageSet:
 *     -------------
 *    Here we clean vars that become obsolete not at all updates, but only
 *    when page changes (bound to the dynatable event "dynatable:page:set")
 */

function tidyAfterPageSet() {
    // we visually uncheck the 'trashAll' box
    $('input#trashAll').attr('checked', false);
}



// FIRST portion of code to be EXECUTED:
// (3) Get records and hyperdata for paginator
$.ajax({
  url: '/api/nodes?types[]=DOCUMENT&pagination_limit=-1&parent_id='
        + corpus_id
        +'&fields[]=parent_id&fields[]=id&fields[]=name&fields[]=typename&fields[]=hyperdata'
        // +'&hyperdata_filter[]=title&hyperdata_filter[]=source&hyperdata_filter[]=language_iso2'
        +'&hyperdata_filter[]=title&hyperdata_filter[]=source&hyperdata_filter[]=language_iso2&hyperdata_filter[]=abstract'
        +'&hyperdata_filter[]=publication_year&hyperdata_filter[]=publication_month&hyperdata_filter[]=publication_day',
  success: function(maindata){
      // unfortunately favorites info is in a separate request (other nodes)
      $.ajax({
        url: window.location.origin + '/api/nodes/'+corpus_id+'/favorites',
        success: function(favdata){
          // initialize favs lookup
          for (var i in favdata['favdocs']) {
              doc_id = favdata['favdocs'][i]
              favorites[doc_id] = true ;
          }

          // now process the nodes data from 1st request
          $.each(maindata.records, function(i, record){
            var orig_id = parseInt(record.id);
            var arr_id = parseInt(i)
            RecDict[orig_id] = arr_id;
            record.rawtitle = record.name;

            record.isFavorite = false ;
            if (favorites[orig_id]) {
                record.isFavorite = true ;
            }

            // trick to have a clickable title in docurl slot, but could be done in transformContent2
            record.docurl = '<a target="_blank" href="/projects/' + project_id + '/corpora/'+ corpus_id + '/documents/' + record.id + '">' + record.name + '</a>';
            record.date = get_node_date(record);
            record.del = false;
          });

          // loop for stats and locally created/transformed data
          for (var i in maindata.records) {
              var rec = maindata.records[i]
              // initialize countByTitle and countByMeta census
              ourTitle = rec['rawtitle'] ;
              if (countByTitles.hasOwnProperty(ourTitle)) {
                  countByTitles[ourTitle] ++ ;
              }
              else {
                  countByTitles[ourTitle] = 1 ;
              }

              ourSignature = metaSignature(rec)
              if (countByMeta.hasOwnProperty(ourSignature)) {

                  // property n contains the count
                  countByMeta[ourSignature]['n'] ++ ;

                  // no need to check for min rec_id b/c loop in ascending order
              }
              else {
                  countByMeta[ourSignature] = {'n':undefined,
                                               'smallest_id':undefined}
                  countByMeta[ourSignature]['n'] = 1 ;

                  // we also take the min rec_id
                  // (to keep only one exemplar at deduplication)
                  countByMeta[ourSignature]['smallest_id'] = i ;
              }
              // also save record's "meta signature" for later lookup
              rec.signature = ourSignature

              // also create a short version of the date
              rec.short_date = ( rec.hyperdata.publication_year
                                +"/"+
                                 rec.hyperdata.publication_month
                                +"/"+
                                 rec.hyperdata.publication_day
                                )

              // and a bool property for remote search results
              // (will be updated by ajax)
              rec.matched_remote_search = false      // TODO use it

          }

          AjaxRecords = maindata.records; // backup-ing in global variable!

          $("#content_loader").remove();

          var result = Main_test(maindata.records)

          // OK ?
          console.log( result )
        },
      });
  },
});
