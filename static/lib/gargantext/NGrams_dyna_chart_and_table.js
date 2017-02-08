/**
 * @fileoverview
 * Manages behavior of the terms view (at: project/PID/corpus/CID/terms)
 *   - the ngrams table with normal/keep/delete states
 *   - the ngrams groupings
 *   - the score chart
 *
 * MainTableAndCharts() is the entry point. A dynatable is the main UI element.
 *
 * Dynatable uses <thead> for columns and ulWriter() for row formatting.
 *
 * Here, the user can modify DB lists by toggling Ngrams states and
 * save to DB via the API in the functions SaveLocalChanges() and CRUD()
 *
 * Local persistence of states is in AjaxRecord[ngramId].state
 *   (access by ngram ids)
 *
 * Local persistence of groups is in GroupsBuffer (result of modification)
 *
 * Their values are initialized in the functions AfterAjax() and Refresh().
 *
 * The stateIds are described by the System object.
 *   - columns use stateId [0..2]  (miam aka normal, map aka keep, stop aka delete)
 *
 *
 * These states are stored in 3 places :
 *          Original (in *OriginalNG*)
 *          Current (in *AjaxRecords*)
 *          Changes to make (in "FlagsBuffer")
 *
 *          (the crud operations create FlagsBuffer at the last moment by
 *           inspecting the diff of original vs current and infering changes)
 *
 * For the groups it's a little different with only 2 main vars:
 *          Current (in CurrentGroups)
 *          Changes to make (in "GroupsBuffer")
 *
 *          (each user action is enacted in Current and at the same time carried
 *           over to GroupsBuffer)
 *
 * @author
 *   Samuel Castillo (original 2015 work)
 *   Romain Loth
 *           - minor 2016 modifications + doc
 *           - unify table ids with ngram ids
 *           - new api routes + prefetch maplist terms
 *           - simplify UpdateTable
 *           - clarify cruds
 *           - fine-grained "created groups" handling
 *           - local cache for user params
 *
 * @version 1.4
 *
 * @requires jquery.dynatable
 * @requires d3
 */


// =============================================================================
//                      GLOBALS  <=> INTERACTIVE STATUS etc
// =============================================================================

var corpusId = getIDFromURL("corpora")

// current ngram infos (<-> row data)
// ----------------------------------
// from /api/ngramlists/lexmodel?corpus=312
// with some expanding in AfterAjax
var AjaxRecords = {}


// current groups
// --------------
// links and subforms (reverse index)
var CurrentGroups = {"links":{}, "subs":{}}


// table element (+config +events)
// -------------------------------
var MyTable ;


// Need Save Flag  (please modify via toggleNeedSave, not directly)
// ---------------
var _NeedSave = false ;

//  definition of switching statuses for the 3 lists
// --------------------------------------------------
//  mainlist (+ maplist)
//         vs
//      stoplist
var GState = 0      // do we have an open group
var System = {
    // 1: {
    // },
    0: {
        "states" : [ "normal" , "keep" , "delete"] ,
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
            }
        }
    }

}

/**
* inverted mapping useful for state_id lookup
*
* System[GState]["statesD"] = {'normal':0,'keep':1,'delete':2}
*/
for(var i in System[GState]["states"] ) {
    System[GState]["statesD"][ System[GState]["states"][i] ] = Number(i)
}


// System[0]["statesD"]
//          { "normal" , "keep" , "delete" }
//              0          1         2


// DICT BUFFERS FOR MAP/MAIN//STOP SAVING LOGIC
// ----------------------------------------------
var FlagsBuffer = {}

// + 1 for groups
var GroupsBuffer = {'_to_add':{}, '_to_del':{}}

// to_add will have structure like this  { mainformid1 : [array1 of subformids],
//                                         mainformid2 : [array2 of subformids]}

// to_del has same format
// (will be interpreted as couples to remove from DB rows)
//  for instance: _to_del  = {      A1 : [A2, A5],             B1 : [B2] }
//  means to remove 3 DB rows   A1 -- A2   and   A1 -- A5   and B1 -- B2



// GROUP "WINDOWS"
// ----------------
// keeps track of seeGroup() opened frames
var vizopenGroup = {} ;

// (if currently this group is under modification)
// ngramId of mainform + oldSubNgramIds + newSubNgramIds
var activeGroup = {'now_mainform_id':undefined, 'were_mainforms':{}} ;


// CHARTS ELEMENTS
// -----------------
//  D3.js: Interactive timerange variables.
var LineChart = dc.lineChart("#monthly-move-chart");
var volumeChart = dc.barChart("#monthly-volume-chart");

// volumeChart chart limits actualized on dc "filtered" event
var latest,oldest;
var TheBuffer = false

// width of the table in columns, updated after main
var tableSpan ;

// if "print portfolio"  (TODO clarify use)
var corpusesList = {}


// TABLE'S PARAMS' getter
// -----------------------
// Fetch all current user params for sorting, filtering...
// @param aDynatable   (eg: MyTable.data('dynatable'))
function getSelectedParams(aDynatable) {
  var tbsettings = aDynatable.settings.dataset

  var sorting_obj= tbsettings.sorts

  var sort_type = null
  if (sorting_obj) {
    sort_type = Object.keys(sorting_obj).pop()
  }

  // returns a "picklistParams object"
  return {
    'search' : tbsettings.queries['search'],
    'multiw' : tbsettings.queries['my_termtype_filter'],
    'gtlists': tbsettings.queries['my_state_filter'],
    'perpp'  : tbsettings.perPage,
    'sortk'  : sort_type,
    'sortdirec': sorting_obj ? sorting_obj[sort_type] : null,
    'from' : TheBuffer ? TheBuffer[0] : null,
    'to' :   TheBuffer ? TheBuffer[1] : null
  }
}


// =============================================================================
//                            CACHE MANAGEMENT
// =============================================================================
/**
* a local cache to remember active filters and page after reload
*   cf. saveParamsToCache()
*       restoreSettingsFromCache()
*
*   TODO localStorage.clear() after expiry date
*/

window.onbeforeunload = saveParamsToCache;

// always called at page close/quit
// £TODO use url instead of corpusId+'/terms' as prefix
function saveParamsToCache() {

  var params = getSelectedParams(MyTable.data('dynatable'))

  var search_filter_status = params.search
  var state_filter_status = params.gtlists
  var type_filter_status = params.multiw
  var per_page_status = params.perpp
  var sort_type_status = params.sortk
  var sort_direction_status = params.sortdirec
  var from_status = params.from
  var to_status = params.to

  // keys and values are str only so we use path-like keys
  if (search_filter_status) {
    localStorage[corpusId+'/terms/search'] = search_filter_status
  }
  else {
    localStorage.removeItem(corpusId+'/terms/search')
  }

  if (state_filter_status) {
    // console.warn("state_filter_status is set")
    localStorage[corpusId+'/terms/state'] = state_filter_status
  }
  else {
    // console.warn("state_filter_status is NOT set")
    localStorage.removeItem(corpusId+'/terms/state')
  }
  if (type_filter_status) {
    localStorage[corpusId+'/terms/type'] = type_filter_status
  }
  else {
    localStorage.removeItem(corpusId+'/terms/type')
  }

  if (typeof(from_status) != "undefined"
      && typeof(to_status) != "undefined") {
    console.log("saving STAT")
    localStorage[corpusId+'/terms/fromVal'] = from_status
    localStorage[corpusId+'/terms/toVal'] = to_status
  }

  localStorage[corpusId+'/terms/perPage'] = per_page_status
  // localStorage[corpusId+'/terms/page'] = page_status

  localStorage[corpusId+'/terms/sortType'] = sort_type_status
  localStorage[corpusId+'/terms/sortDirection'] = sort_direction_status

  return null;
}

// called after 1st Ajax and given to table init in Main as filtersParams
function restoreSettingsFromCache() {
  // also returns a "picklistParams object"
  return {
    'search' : localStorage[corpusId+'/terms/search'],
    'multiw' : localStorage[corpusId+'/terms/type'],
    'gtlists': localStorage[corpusId+'/terms/state'],
    'perpp'  : localStorage[corpusId+'/terms/perPage'],
    'sortk'  : localStorage[corpusId+'/terms/sortType'],
    'sortdirec':localStorage[corpusId+'/terms/sortDirection'],
    'from':     localStorage[corpusId+'/terms/fromVal'],
    'to':       localStorage[corpusId+'/terms/toVal']
  }
}


// =============================================================================
//                  ELEMENT CONTROLLERS AND ROW PROCESSORS
// =============================================================================
// Get all projects and corpuses of the user
function GetUserPortfolio() {
    //http://localhost:8000/api/corpusintersection/1a50317a50145
    var project_id = getIDFromURL("projects")
    var corpus_id =  getIDFromURL("corpora")

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
// function printCorpuses() {
//     console.log( "!!!!!!!! in printCorpuses() !!!!!!!! " )
//     pr(corpusesList)
//
//     var selected = $('input[name=optradio]:checked')[0].id.split("_")
//     var sel_p = selected[0], sel_c=selected[1]
//
//     var current_corpus =  getIDFromURL("corpora")
//
//     var selected_corpus = corpusesList[sel_p]["corpuses"][sel_c]["id"]
//     pr("current corpus: "+current_corpus)
//     var the_ids = []
//     the_ids.push( current_corpus )
//     the_ids.push( corpusesList[sel_p]["corpuses"][sel_c]["id"] )
//
//     $("#closecorpuses").click();
//
//     // EXTERNAL CORPUS TO COMPARE:
//     var whichlist = $('input[name=whichlist]:checked').val()
//       var url = window.location.origin+"/api/node/"+selected_corpus+"/ngrams/list/"+whichlist//+"?custom"
//       console.log( url )
//
//
//       GET_( url , function(results, url) {
//           if(Object.keys( results ).length>0) {
//          var sub_ngrams_data = {
//            "ngrams":[],
//            "scores": $.extend({}, OriginalNG.scores)
//          }
//         for(var i in OriginalNG["records"].ngrams) {
//           if( results[ OriginalNG["records"].ngrams[i].id] ) {
//             var a_ngram = OriginalNG["records"].ngrams[i]
//             sub_ngrams_data["records"].push( a_ngram )
//           }
//           // if( results[ OriginalNG["records"][i].id] && OriginalNG["records"][i].name.split(" ").length==1 ) {
//           //   if( OriginalNG["map"][ i ] ) {
//           //     var a_ngram = OriginalNG["records"][i]
//           //     // a_ngram["state"] = System[0]["statesD"]["delete"]
//           //     sub_ngrams_data["ngrams"].push( a_ngram )
//           //   }
//           // }
//         }
//         var result = MainTableAndCharts(sub_ngrams_data , OriginalNG.scores.initial , {})
//           }
//       });
// }


// Updates most global var TheBuffer
// TODO should be distinct from time range (of doc view)
//      and adapt more for freq ranges
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
    console.log("\nFUN Final_UpdateTable()")

    // console.log("AjaxRecords")
    // console.log(AjaxRecords)

    var UpdateTable = false
    if (action=="changerange") {
        UpdateTable = true;
    }
    pr("update table??: "+UpdateTable)

    if ( ! UpdateTable ) return false; //stop whatever you wanted to do.

    var TimeRange = AjaxRecords;

    var dataini = (TheBuffer[0])?TheBuffer[0]:oldest;
    var datafin = (TheBuffer[1])?TheBuffer[1]:latest;
    pr("show me the pubs of the selected score range")
    pr("\tfrom ["+dataini+"] to ["+datafin+"]")

    TimeRange = []
    for (var ngramId in AjaxRecords) {
        if(AjaxRecords[ngramId].score>=dataini && AjaxRecords[ngramId].score<=datafin){
            // pr( AjaxRecords[ngramId].date+" : "+ngramId )
            TimeRange.push(AjaxRecords[ngramId])
        }
    }

    // todo: check if necessary to re-init like this
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

function getRecord(ngramId) {
  return MyTable.data('dynatable').settings.dataset.originalRecords[ngramId];
  // return AjaxRecords[ngramId]
}

function getRecords() {
  return MyTable.data('dynatable').settings.dataset.originalRecords;
}


// GROUPS CONTROLLERS
// ------------------
function saveActiveGroup() {
    var mainform = activeGroup.now_mainform_id
    // console.log("before changes, GroupsBuffer: ", JSON.stringify(GroupsBuffer))
    // console.log("saving mainform to GroupsBuffer: " + mainform)
    // console.log("using the activeGroup:\n  ", JSON.stringify(activeGroup))

    // first free the items that were not kept (in pending no man's land)
    for (var j in activeGroup.new_free) {
        var ngid = activeGroup.new_free[j]
        freeSubform(ngid)
    }

    // £POSSIBLE: ideally add links only if not pre-existing (but otherwise API will do it)


    // save the group (the new array of tgt forms to save is in now_links)
    if (activeGroup.now_links.length) {
        addInCurrentGroups(mainform, activeGroup.now_links)    // -> current status
        GroupsBuffer._to_add[mainform] = activeGroup.now_links // -> changes to make
    }

    // -----------------------------------------------------
    // various consequences

    // also we prefix "*" to the name if not already there
    if (AjaxRecords[mainform].name[0] != '*') {
        AjaxRecords[mainform].name = "*" + AjaxRecords[mainform].name
    }

    // all subforms become deactivated in AjaxRecords
    for (var i in activeGroup.now_links) {
        subformId = activeGroup.now_links[i]
        AjaxRecords[subformId].state = -1
    }

    // the previous mainforms may have old groupings to be marked for deletion
    for (downgradedNgramId in activeGroup.were_mainforms) {
        // (except the one we just saved)
        if (downgradedNgramId != mainform
            // and if it did have a group
            && CurrentGroups.links[downgradedNgramId]) {

            // then we delete the entire ex-group under the ex-mainform

            // 1) for DB
            GroupsBuffer._to_del[downgradedNgramId] = CurrentGroups["links"][downgradedNgramId]

            // 2) locally
            deleteInCurrentGroups(false, downgradedNgramId)
                // arg 1 "false" <=> no need to change subform states
                //                   because these subforms stay subforms
                //                   (but under the new mainform)
                // no arg 3 <=> delete entire group
        }
    }

    // clean group modification zone and buffer and update table
    removeActiveGroupFrameAndUpdate()

    // console.log("after changes, GroupsBuffer: ",GroupsBuffer)

    // mark that there was a change
    if (! _NeedSave) {
        toggleNeedSave()
    }
}

function removeActiveGroupFrameAndUpdate() {
    // no need to restore records:  everything from the frame
    // was in temporary var activeGroup

    // erases now_links and restores empty activeGroup global cache
    activeGroup = {'now_mainform_id':undefined, 'were_mainforms':{}} ;

    // remove the entire top row that was used as group modification zone
    $("#group_box").remove()
    GState=0

    // we also close the open sublists in case some of them don't exist any more
    vizopenGroup = {}

    // reprocess from current record states and params
    var FirstScoreParam = OriginalNG.scores.initial // £TODO use when several scores
    MainTableAndCharts(AjaxRecords, FirstScoreParam , getSelectedParams(MyTable.data('dynatable')),"removeActiveGroupFrameAndUpdate")
}

// for click open/close
function toggleSeeGroup(plusicon, ngramId) {
    // when already open => we close
    if (ngramId in vizopenGroup) {
        $("#subforms-"+ngramId).remove() ;
        delete vizopenGroup[ngramId] ;
        plusicon.classList.remove('glyphicon-triangle-bottom') ;
        plusicon.classList.add('glyphicon-triangle-right') ;
    }
    else {
        var subNgramHtml = seeGroup(ngramId, true) ;
        // we target the html in the mainform term's box
        $( "#box-"+ngramId).append(subNgramHtml) ;

        // change icon
        plusicon.classList.remove('glyphicon-triangle-right') ;
        plusicon.classList.add('glyphicon-triangle-bottom') ;
    }
}

/**
 * shows the ngrams grouped under this ngram
 *
 * called at 'plusicon click' via toggleSeeGroup()
 *     or at table rows rewriting via transformContent()
 *
 * @param ngramId (of the mainform)
 */
function seeGroup ( ngramId , allowChangeFlag) {
    // 1/6 create new element container
    var subNgramHtml = $('<p class="note">') ;
    subNgramHtml.attr("id", "subforms-"+ngramId) ;
    subNgramHtml.css("line-height", 1.2) ;
    subNgramHtml.css('margin-left','.3em') ;
    subNgramHtml.css("margin-top", '.5em') ;


    // 2/6 attach flag open to global state register
    vizopenGroup[ngramId] = true ;

    // 3/6   retrieve names of the grouped ngrams
    var linksNames = [] ;
    if( ngramId in CurrentGroups["links"] ) {
            var thisGroup = CurrentGroups["links"][ngramId]
            for (var i in thisGroup) {
                var subNgramId = thisGroup[i] ;
                linksNames[i] = AjaxRecords[subNgramId].name
            }
    }

    // 4/6 create the "tree" from the names, as html lines
    var htmlMiniTree = drawSublist(linksNames)
    subNgramHtml.append(htmlMiniTree)

    // 5/6 add a "modify group" button
    if (allowChangeFlag) {
        var changeGroupsButton  = '<button style="float:right"' ;
            changeGroupsButton +=        ' title="add/remove contents of groups"' ;
            changeGroupsButton +=        ' onclick="modifyGroup('+ngramId+')">' ;
            changeGroupsButton +=   'modify group' ;
            changeGroupsButton += '</button>' ;
        subNgramHtml.append(changeGroupsButton) ;
    }

    // 6/6  return html snippet (ready for rendering)
    return(subNgramHtml)
}

/*
 * Creates an "ASCIIart" tree from subforms names
 * Exemple:
 *             BEES
 *              ├── bee
 *              ├── honey bee
 *              └── honey bees
 */
function drawSublist (linkNamesArray) {
    var sublistHtml = "" ;
    var last_i = linkNamesArray.length - 1 ;
    for(var i in linkNamesArray) {
        var subNgramName = linkNamesArray[i] ;
        if (i != last_i) {
            sublistHtml += ' ├─── ' + subNgramName + '<br>' ;
        }
        else {
            sublistHtml += ' └─── ' + subNgramName ;
        }
    }
    return sublistHtml
}

// we can create sort functions for ngramIds to use their associated name
// (name lookup uses global var AjaxRecords or any other similar records)
function comparatorNamesInRecords(records) {
    return function(a,b) {
        return records[a].name.localeCompare(records[b].name)
    }
}

function drawActiveGroup (tgtElementId, mainformId, linkIdsArray, ngInfos, newFree) {
    var groupHtml  = '<p id="group_box_mainform">';
        groupHtml +=    mainformSpan(ngInfos[mainformId])
        groupHtml += '  <br> │<br>';
        groupHtml += '</p>';
        // sublist
        groupHtml += '<p id="group_box_content">';

    var last_i = linkIdsArray.length - 1 ;
    for(var i in linkIdsArray.sort(comparatorNamesInRecords(ngInfos))) {
        var subNgramId = linkIdsArray[i] ;
        if (i != last_i) {
            groupHtml += ' ├── ' + subformSpan(ngInfos[subNgramId]) + '<br>' ;
        }
        else {
            groupHtml += ' └── ' + subformSpan(ngInfos[subNgramId]) ;
        }
    }

    // save/cancel buttons
    groupHtml += '\n          <p id="activeGroupButtons">';

    // Ok - No
    var cancelGroupButton  = '<button class="btn btn-danger" onclick="removeActiveGroupFrameAndUpdate()">' ;
        cancelGroupButton +=   'cancel' ;
        cancelGroupButton += '</button>' ;

    var tempoSaveGroupButton  = '<button class="btn btn-info" onclick="saveActiveGroup()">' ;
        tempoSaveGroupButton +=   'done' ;
        tempoSaveGroupButton += '</button>' ;

    groupHtml += cancelGroupButton
    groupHtml += tempoSaveGroupButton

    groupHtml += '<hr><p id="group_box_pending" style="color:grey;">';
    if (newFree.length) {
        groupHtml += 'Unwanted items will become independant terms at finish'
    }
    for (var j in newFree) {
        pendingFormId = newFree[j]
        groupHtml += pendingSubfHtml(ngInfos[pendingFormId])
    }
    groupHtml += '</p>\n'

    // write html to current DOM
    $(tgtElementId).html(groupHtml)
}

// makes each subform's html
function subformSpan( subNgramInfo ) {
    // each item is a new ngram under the group
    span = $('<span/>', {
        text: subNgramInfo.name,
        title: subNgramInfo.id,
        id: 'active-subform-' + subNgramInfo.id,
        class: 'subform'
    })

    // remove button
    var removeButton  = '<span class="note glyphicon glyphicon-minus-sign"'
        removeButton +=   ' title="remove from group"' ;
        removeButton +=   ' onclick="removeSubform('+ subNgramInfo.id +')"></span> &nbsp;'
    span.prepend(removeButton)

    // makes this subform become the mainform
    // var mainformButton  = '<span class="note glyphicon glyphicon-circle-arrow-up"'
    //     mainformButton +=   ' title="upgrade to mainform of this group"'
    //     mainformButton +=   ' onclick="makeMainform('+ subNgramInfo.id +')"></span>&nbsp;'
    // span.prepend(mainformButton)
    return(span[0].outerHTML)
}

// html for new_free subforms
function pendingSubfHtml( subNgramInfo ) {
    // each item is a new ngram in the no man's land between grouped and free status

    // like subformSpan
    var subformHtml  = '<p title="'+subNgramInfo.id+'" id="pending-subform-'+subNgramInfo.id+'" class="pending subform">'
    // like plus_event
    subformHtml += '<span class="note smaller glyphicon glyphicon-plus"'
    subformHtml +=      ' title=\'add "'+subNgramInfo.name+'" back to active group\''
    subformHtml +=      ' color="#FF530D"'
    subformHtml +=      ' onclick="addToGroup('+ subNgramInfo.id +',true)"></span>'
    subformHtml += subNgramInfo.name
    subformHtml += '</p>'
    return(subformHtml)
}

// makes mainform's span
function mainformSpan( ngramInfo ) {
    // each item is a new ngram under the group
    span = $('<span/>', {
        text: ngramInfo.name,
        title: ngramInfo.id,
        id: 'active-mainform-' + ngramInfo.id
    })
    return(span[0].outerHTML)
}

function makeMainform(ngramId) {
    $('#active-subform-'+ngramId).remove()

    // replace now_mainform_id property
    previousMainformId = activeGroup.now_mainform_id
    activeGroup.now_mainform_id = ngramId

    // replace old subform by old mainform in now_links array
    var i = activeGroup.now_links.indexOf(ngramId)
    activeGroup.now_links[i] = previousMainformId

    // if it was previously a subform then:
    //   -> it was not in any of the lists
    if (! (mainform in activeGroup.were_mainforms)) {
        // update records
        AjaxRecords[mainform] = activeGroup.ngraminfo[mainform]
        AjaxRecords[mainform].state = 0

        // update lists (inherits status of previous mainform)
    }


    // NB  if it was previously a subform
    //     then absent from AjaxRecords
    //     => is solved in saveActiveGroup()

    // redraw active group_box_content
    drawActiveGroup(
        '#group_box',
        activeGroup.now_mainform_id,
        activeGroup.now_links,
        activeGroup.ngraminfo,
        activeGroup.new_free
     )
     // and update
     MyTable.data('dynatable').dom.update();
}



// remove the subform from activeGroup (and any older group in CurrentGroups)
// NB do this first at activeGroup save (before CurrentGroups will change)
function freeSubform(ngramId) {

    // we prefix "*" to the name if not already there like for mainform
    if (AjaxRecords[ngramId].name[0] != '*') {
        AjaxRecords[ngramId].name = "*" + AjaxRecords[ngramId].name
    }

    // normal case
    if (AjaxRecords[ngramId].state != -1) {
        // nothing to do:
        // activeGroup removal will reveal untouched element in AjaxRecords

    }
    // special case: if removed form already was a subform it becomes independant
    // (because the old mainform may be remaining in the new group)
    else {
        var oldMainFormId = CurrentGroups["subs"][ngramId]
        // for DB
        if (! GroupsBuffer._to_del[oldMainFormId]) {
            GroupsBuffer._to_del[oldMainFormId] = [ngramId]
        }
        else {
            GroupsBuffer._to_del[oldMainFormId].push(ngramId)
        }
        // local consequences:
	    var subformBecomesFree = true
        deleteInCurrentGroups(subformBecomesFree, oldMainFormId, [ngramId])
        // arg1 true     => the removed subform from the old group
        //                  will get a placeholder score !
        //              and will gets a state (map/del/normal)
        //           (which will also finally trigger DB list change to new state)
    }
}

function removeSubform(ngramId) {
    // element moves from activeGroup.now_links ==> activeGroup.new_free
    // (it's not going to be "freed" until user clicks "Finish")

    // clean now_links array
    var i = activeGroup.now_links.indexOf(ngramId)
    activeGroup.now_links.splice(i,1)
    // clean were_mainforms dict (if key existed)
    delete activeGroup.were_mainforms[ngramId]
    // add to free elements
    activeGroup.new_free.push(ngramId)
    // redraw active group_box_content
    // (will remove the active item and add to pending zone)
    drawActiveGroup(
        '#group_box',
        activeGroup.now_mainform_id,
        activeGroup.now_links,
        activeGroup.ngraminfo,
        activeGroup.new_free
     )
}


/**
 * Effects of deleting a mainform from the current groups (client-side)
 *
 *  => updates the global var CurrentGroups
 *  => optionally triggers assignment of a state to the ex-subforms
 *
 * @param becomesFree boolean  => gets a new inherited AjaxRecords[subformId].state
 *                             => adds placeholder for AjaxRecords[subformId].score
 * @param ngramId of a mainform
 * @param (optional) subforms array of subNgramIds (removes individual links)
 *        if absent: removes the whole group
 */
function deleteInCurrentGroups(becomesFree, mainformId, subforms) {

    var wholeGroup = false
    if (! subforms) {
        console.log("deleteInCurrentGroups: no subforms specified: removing *entire* old group")
	       wholeGroup = true
    }
    var subsToDel = []
    if (wholeGroup) {
        if (typeof CurrentGroups.links[mainformId] != "undefined") {
            subsToDel = CurrentGroups.links[mainformId]
        }
        else {
            subsToDel = []
        }
    }
    else {
        subsToDel = subforms
    }

    // nothing to remove, we return at once
    if (subsToDel.length == 0) {
        return
    }

    if (becomesFree) {
        // ex-subforms can inherit state from their previous mainform
        var implicitState = AjaxRecords[mainformId].state
    }

    // deleting in reverse index
    for (var i in subsToDel) {
        var subformId = subsToDel[i]

        // deleting in "subs"
        delete CurrentGroups.subs[subformId]

        if (becomesFree) {
            AjaxRecords[subformId].state = implicitState
            // consequence:
            //   now OriginalNG.records[subformId].state
            //        is != AjaxRecords[subformId].state
            //   therefore the newly independant forms
            //   will be added to their new wordlist

            AjaxRecords[subformId].score = "NaN (do recount for score ?)"
        }

        // deleting in "links"
        if (! wholeGroup) {
            // remove 1 from links array (indexOf is ok b/c length always small)
            var i = CurrentGroups["links"][mainformId].indexOf(subformId)
            CurrentGroups["links"][mainformId].splice(i,1)

            // if it was the last of this group
            if (CurrentGroups["links"][mainformId].length == 0) {
                delete CurrentGroups["links"][mainformId]
            }

        }
    }

    // deleting in "links" is simpler in this case
    if (wholeGroup) {
        delete CurrentGroups["links"][mainformId]
    }
}



/**
 * Adding links to the current groups (client-side)
 *
 *  => updates the global var CurrentGroups
 *
 * @param mainformId
 * @param subforms array of subNgramIds
 */
function addInCurrentGroups(mainformId, subforms) {
    // console.log("addInCurrentGroups: "+mainformId+"("+JSON.stringify(subforms)+")")
    CurrentGroups["links"][mainformId] = subforms
    for (var i in subforms) {
        var subformId = subforms[i]
        CurrentGroups["subs"][subformId] = mainformId
    }
}

function modifyGroup ( mainFormNgramId ) {
    // create modification container
    //
    var group_html =  '      <tr>\n';
        group_html += '        <td id="group_box" colspan='+tableSpan+'>\n';
     // -------------------------------------------------------------------
     // mainform + sublist + buttons will be added here by drawActiveGroup
     // -------------------------------------------------------------------
        group_html += '        </td>\n';
        group_html += '      </tr>\n';
    $( "#my-ajax-table > thead" ).append(group_html)

    // set global 'grouping in progress' states
    GState = 1 ;
    activeGroup.now_mainform_id = mainFormNgramId ;
    activeGroup.were_mainforms[mainFormNgramId] = true ;
    activeGroup.now_links = [] ;
    // ngraminfo = standard info of records (temporary copy)
    activeGroup.ngraminfo = {}
    activeGroup.ngraminfo[mainFormNgramId] = AjaxRecords[mainFormNgramId] ;
    activeGroup.new_free = []

    // add relevant information from old & new links to activeGroup.now_links
    updateActiveGroupInfo (mainFormNgramId, false)

    // groupBox rendering
    drawActiveGroup(
        '#group_box',
        activeGroup.now_mainform_id,
        activeGroup.now_links,
        activeGroup.ngraminfo,
        activeGroup.new_free
     )

     MyTable.data('dynatable').dom.update();
}


// add new ngramid (and any present subforms) to currently modified group
function addToGroup ( ngramId, pending ) {

    // console.log("FUN addToGroup(" + AjaxRecords[ngramId].name + ")")

    var toOther = true ;
    activeGroup.were_mainforms[ngramId] = true ;

    if (GState == 1) {

        // add this mainform as a new subform
        activeGroup.now_links.push(ngramId)
        activeGroup.ngraminfo[ngramId] = AjaxRecords[ngramId]

        // special case if it comes from 'no man's land'
        if (pending) {
            var i = activeGroup.new_free.indexOf(ngramId)
            activeGroup.new_free.splice(i,1)
        }
        // normal case (item added from table)
        else {
            // also add all its subforms as new subforms
            updateActiveGroupInfo (ngramId, toOther)
        }

        // redraw active group_box_content
        drawActiveGroup(
            '#group_box',
            activeGroup.now_mainform_id,
            activeGroup.now_links,
            activeGroup.ngraminfo,
            activeGroup.new_free
         )

         MyTable.data('dynatable').dom.update();
     }
     else {
         console.warn("ADD2GROUP but no active group")
     }
}

/**
 * subforms from DB have their info in AjaxRecords like everyone, and state = -1
 *
 * here all current infos are copied to activeGroup temporary var
 * (copy will remain until user cancel/finishes group modif)
 *
 * @param ngramId
 * @param toOtherMainform = flag if ngram was a subform of another mainform
 * @param (global) activeGroup = current state struct of modify group dialog
 */
function updateActiveGroupInfo (ngramId, toOtherMainform) {
    // console.log("FUN updateActiveGroupInfo(" + AjaxRecords[ngramId].name + ")")
    // console.log(activeGroup)

    // fill active link info
    for(var i in CurrentGroups["links"][ ngramId ] ) {
        var subId = CurrentGroups["links"][ ngramId ][i] ;
        activeGroup.now_links.push(subId)
        activeGroup.ngraminfo[subId] = AjaxRecords[subId]
    }
}



// LIST MEMBERSHIP CONTROLLERS
// ----------------------------

/**
 * click red, click keep, click normal...
 *
 * @param ngramId - the record's id
 */
function clickngram_action ( ngramId ) {
    // cycle the statuses (0 => 1 => 2 => 0 => etc)
    AjaxRecords[ngramId].state = (AjaxRecords[ngramId].state==(System[0]["states"].length-1))?0:(AjaxRecords[ngramId].state+1);

    // State <=> term color <=> checked colums

    // console.log("click: state after: "+ AjaxRecords[ngramId].state) ;
    MyTable.data('dynatable').dom.update();

    // mark that there was a change
    if (! _NeedSave) {
        toggleNeedSave()
    }
}


/**
 * Click on a checkbox in a row
 *
 * @boxType : 'keep' or 'delete' (resp. maplist and stoplist)
 * @ngramId : corresponding record's id for record.state modifications
 */

function checkBox(boxType, ngramId) {
    // console.log ('CLICK on check box (ngramId = '+ngramId+')') ;
    var currentState = AjaxRecords[ngramId].state ;
    // alert('NGRAM: ' + ngramId + '\n'
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

    // replace old state and color
    AjaxRecords[ngramId].state = targetState ;
    MyTable.data('dynatable').dom.update();

    // mark that there was a change
    if (! _NeedSave) {
        toggleNeedSave()
    }
}


// TABLE WRITERS PROCESSORS
// ------------------------

/**
 * Works for ulWriter. Connects a record's state with table UI outcome.
 *
 * @param ngramId - the id for this ngram record in AjaxRecords
 *
 * Returns <tr> contents:  an array of html contents to be each injected (by
 *                         dynatable) into respective <td> cells of the row
 */
function transformContent(ngramId) {
    var ngram_info = AjaxRecords[ngramId];

    // ex: ngram_info = {
    //             "id":2349,"name":"failure","score":1,"flag":false,
    //             "group_exists":false,"state":0
    //            }

    // result will contain instanciated cell html for each column in dynatable
    var result = {}

    // debug
    // ------
    // console.log(
    //   "transformContent got ngram_info no " + ngramId + ": "
    //   + JSON.stringify(ngram_info)
    // )

    var atts = System[0]["dict"][ System[0]["states"][ngram_info.state] ]
    // avec System[0]["dict"] contenant {"normal":{"id":"normal","name":"Normal","color":"black"},"delete":{"id":"delete","name":"Delete","color":"red"}...}

    // -------------------------------------------
    // prerequisite

    var plus_event = ""
    // define "plus_event" symbol depending on "grouping" status

    // normal situation: button allows to see group contents
    if(GState==0) {
        var plusicon = '' ;
        if (ngramId in vizopenGroup) {
            plusicon = "glyphicon-triangle-bottom"
        } else {
            plusicon = "glyphicon-triangle-right"
        }
        if (ngram_info.group_exists) {
            plus_event  = '<span class="note glyphicon '+plusicon+'"'
        } else {
            plus_event  = '<span class="note glyphicon '+plusicon+' greyed"'
        }
        plus_event +=      ' onclick="toggleSeeGroup(this, '+ ngramId +')"></span>'
    }

    // GState = 1 situation: button allows to add to active group
    // (if previously had addToGroup button clicked)
    if(GState==1 ) {
        if(ngram_info.state!=System[0]["statesD"]["delete"] && ! GroupsBuffer._to_add[ngramId]) { // if deleted and already group, no Up button
            plus_event  = '<span class="note glyphicon glyphicon-plus"'
            plus_event +=      ' color="#FF530D"'
            plus_event +=      ' onclick="addToGroup('+ ngramId +')"></span>'
        }
    }

    // -------------------------------------------
    //         score and name column cells
    // -------------------------------------------

    // <td> score </td>
    // unexpected NaN (£TODO remove: ONLY USEFUL FOR INHERITED BUGGY CORPORA)
    if (! ngram_info["score"]) {
        // score can be undefined or null after group separation
        console.warn('undefined score at content rendering, for', ngramId)
        result["score"] = '<span class="'+atts.id+'">ERROR (recount should fix it)</span>\n'
    }
    // expected NaN
    else if (ngram_info["score"] == "NaN") {
        result["score"] = '<span class="'+atts.id+' note">NaN (do recount for score)</span>\n'
    }
    else {
        result["score"] = '<span class="'+atts.id+'">'+ngram_info["score"]+'</span>\n'
    }

    //                               atts.id (ex: "normal" or "delete" etc)

    // <td> name  </td>     aka   "ngrambox"
    result["name"]  = '<div class="ngrambox" id="box-'+ngramId+'">\n'

    // test allows to make active items 'disappear'
    if (ngramId != activeGroup.now_mainform_id && !(ngramId in activeGroup.were_mainforms)) {

        result["name"] +=   plus_event + '\n'
        result["name"] +=   '<span title="'+ngram_info["id"]+'" class="'+atts.id+'" '
        result["name"] +=         'onclick="clickngram_action('+ngram_info["id"]+')">'
        result["name"] +=      ngram_info["name"] + '\n'
        result["name"] +=   '</span>\n'
        // if curently open we also add #subforms p with the sublist
        if (ngram_info["id"] in vizopenGroup) {
            allowChange = (GState != 1)
            result["name"] += seeGroup(
                                    ngram_info["id"],
                                    allowChange
                                )[0].outerHTML ;
        }
    }
    result["name"] += '</div>\n'


    // -------------------------------------------
    // other optional column cells

    // uncomment if column ngramId (here and in MainTableAndCharts)
    // result["ngramId"] = ngram_info["id"] ;

    // uncomment if column state (here and in MainTableAndCharts)
    // result["state"] = AjaxRecords[ngramId].state

    // -------------------------------------------
    // 2 cells for check box state columns
    // ('will_be_map' and 'will_be_stop')

    map_flag = (AjaxRecords[ngramId].state == 1) ;    // 1 = System[0]["statesD"]["keep"]
    stop_flag = (AjaxRecords[ngramId].state == 2) ;   // 2 = System[0]["statesD"]["delete"]

    // <td> checkbox 1 </td>
    result["will_be_map"]  = '<input type="checkbox" '+(map_flag?'checked ':'')
    result["will_be_map"] +=        'onclick=\'checkBox("keep",this.parentNode.parentNode.getAttribute("ngram-id"))\'>'
    result["will_be_map"] += '</input>'
    // <td> checkbox 2 </td>
    result["will_be_stop"]  = '<input type="checkbox" '+(stop_flag?'checked ':'')
    result["will_be_stop"] +=        'onclick=\'checkBox("delete",this.parentNode.parentNode.getAttribute("ngram-id"))\'>'
    result["will_be_stop"] += '</input>'

    // possible todo: 3 way switch ??
    // par exemple http://codepen.io/pamgriffith/pen/zcntm

    // --------------------------------------------
    // {"name":tdcontent1, "score":tdcontent2, ...}
    return result;
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
 *                   "group_exists":false, "state":0}
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
  // console.log("ulWriter: AjaxRecords["+record.id+"]")
  // console.log(AjaxRecords[record.id])

  //debug
  if( typeof AjaxRecords[record.id] == "undefined") {
      console.warn('/!\\ nothing for ' + record.id)
      return false;
  }
  // erase state <= 0
  else if( AjaxRecords[record.id].state < 0 ) {
      // therefore state -1 ngrams will not be drawn
      return false;
  }

  // Add cells content (values OR custom html) from record
  // -----------------------------------------------------
  cp_rec = transformContent(record.id)
  // -----------------------------------------------------

  // grab the record's attribute for each column
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }

  return '<tr ngram-id='+record.id+'>' + tr + '</tr>';
}

// PAGE SELECTION CONTROLLER
// --------------------------
/**
 * Toggle all checkboxes in a column by changing their list in System
 *
 * @boxType : 'keep' or 'delete' (resp. maplist and stoplist)
 * @elem : entire element row with attribute 'ngram-id' (= ngramId)
 *
 * 3-state boxes:
 *  - indeterminate (SOME del SOME map SOME normal) = original state
 *  - check         (ALL del or map)
 *  - uncheck       (NONE --- " ---)
 *    => we get 3 visual expected result
 *       + 3 "vertical" possibilities for each checkall
 *          that combine with the "horizontal" states
 *          of each commanded ngrams (map, stop, miam)
 */

function SelectPage(boxType, boxElem) {
  // debug
  // console.log("\nFUN SelectPage()")

    // real checkAll flags : SOME|ALL|NONE
    var previousColumnSelection = $(boxElem).data("columnSelection") ;
    var newColumnSelection = "" ;

    // we will also need the other "checkall box"
    // - to uncheck "delete" when we check "map" & vice-versa
    // - to make them both "indeterminate" when we restore cached original state
    // - to prevent cacheing if the second column is already cached
    if (boxType == 'keep') { otherBoxId = "delAll" ; }
    else                  { otherBoxId = "mapAll" ; }

    // did we already cache original states ?
    var columnCacheExists = null ;

    // console.log("-------------INCOMING----------------")
    // console.log(boxElem.id)
    // console.log("check:" + $(boxElem).prop("checked"))
    // console.log("indet:" + $(boxElem).prop('indeterminate'))
    // console.log("data:" + previousColumnSelection)


    // toggle column ALL => NONE => SOME => again
    switch (previousColumnSelection) {
        case 'ALL':
            newColumnSelection = "NONE" ;
            columnCacheExists = true ;
            break ;
        case 'NONE':
            newColumnSelection = "SOME" ;
            columnCacheExists = true ;
            break ;
        case 'SOME':
            newColumnSelection = "ALL"  ;
            // probably no cache, except if other column was set
            columnCacheExists = ($("input#"+otherBoxId).data('columnSelection') != 'SOME') ;
            break ;

        default: alert('invalid flag for columnSelection');
    }

    // we'll find the target state for each row in this column
    //    0 = normal = miam
    //    1 = keep   = map
    //    2 = delete = stop
    var stateId = null;

    switch (newColumnSelection) {
        // nothing in the column
        case 'NONE':
            // visual consequences
            $(boxElem).prop('checked', false);
            $(boxElem).prop('indeterminate', false);
            $('#'+otherBoxId).prop('indeterminate', false);
            $('#'+otherBoxId).data('columnSelection', 'NONE');

            // target stateId: 0 for 'normal'
            stateId = 0 ;

            break;

        // the 'indeterminate' case
        case 'SOME':
            // visual consequences
            $(boxElem).prop('checked', false);
            $(boxElem).prop('indeterminate', true);
            $('#'+otherBoxId).prop('indeterminate', true);
            $('#'+otherBoxId).data('columnSelection', 'SOME');

            // target stateId: undef <=> restore original ngram states
            stateId = null ;

            break;

        // all in the column
        case 'ALL':
            // visual consequences
            $(boxElem).prop('checked', true);
            $(boxElem).prop('indeterminate', false);
            $('#'+otherBoxId).prop('indeterminate', false);
            $('#'+otherBoxId).data('columnSelection', 'NONE');

            // target stateId: 1 if boxType == 'keep'
            //                 2 if boxType == 'delete'
            stateId = System[0]["statesD"][boxType] ;

            break;

        default: alert('invalid result for columnSelection');
    }

    // and anyway the other box can't stay checked
    $('#'+otherBoxId).prop('checked', false);

    // console.log("data became:" + newColumnSelection)

  $("table#my-ajax-table tbody tr").each(function (i, row) {
      var ngramId = $(row).attr("ngram-id") ;

      // a cache to restore previous states if unchecked
      if (!columnCacheExists) {
          AjaxRecords[ngramId]["state_buff"] = AjaxRecords[ngramId]["state"] ;
      }

      if (stateId != null) {
          // check all with the requested change
          AjaxRecords[ngramId]["state"] = stateId ;
      }
      else {
          // restore previous states, remove cache
          AjaxRecords[ngramId]["state"] = AjaxRecords[ngramId]["state_buff"] ;
          AjaxRecords[ngramId]["state_buff"] = null ;
      }

  });

  // OK update this table page
  MyTable.data('dynatable').dom.update();

  // and update our own "column situation" storage
  $(boxElem).data('columnSelection', newColumnSelection);

  // mark that there was a change
  if (! _NeedSave) {
      toggleNeedSave()
  }
}


// =============================================================================
//                                  MAIN
// =============================================================================

// MAIN TABLE STATUS CONTROLLERS
// -----------------------------

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


// find all the consequences of changes from MAP => MAIN
// -----------------------------------------------------
// (see forge.iscpif.fr/projects/garg/wiki/Ngram_Lists)

// NB: (MAP => MAIN) also has the consequence that (MAIN || DEL)
// in other words:
//   inmain <==> outdel
//   indel  <==> outmain
// (but we'll keep them distinct in FlagsBuffer for coherence with
//  the distinct API CRUD commands that will be entailed)
function InferCRUDFlags(id, oldState, desiredState, registry) {

    state_skip = -1                              // -1
    state_main = System[0]["statesD"]["normal"]  //  0
    state_map  = System[0]["statesD"]["keep"]    //  1
    state_stop = System[0]["statesD"]["delete"]  //  2


    // thus skips newly grouped items and returns unmodified registry
    if (desiredState != state_skip) {
        // console.log(oldState,"==>",  desiredState)
        // (if was previously in MAP)
        if (oldState === state_map) {
            // console.log("previously in map:" + id + "("+AjaxRecords[id]['name']+")")
            if (desiredState === state_main || desiredState === state_stop) {
                registry["outmap"][ id ] = true
                // (... and some more actions only if is now desired to be in STOP)
                if(desiredState === state_stop) {
                    registry["indel"][id] = true
                    registry["outmain"][id] = true
                }
            }
        }
        // (if previously was in STOP)
        else if (oldState === state_stop) {
            // console.log("previously in stop:" + id + "("+AjaxRecords[id]['name']+")")
            if (desiredState === state_main || desiredState === state_map) {
                registry["outdel"][id] = true
                registry["inmain"][id] = true
                // (... and one more action only if is now desired to be in MAP)
                if(desiredState === state_map) {
                  registry["inmap"][ id ] = true
                }
            }
        }
        // (if previously was under a group)
        else if (oldState === state_skip) {
            if (desiredState === state_main || desiredState === state_map) {
                // console.log("previously hidden in group:" + id + "("+AjaxRecords[id]['name']+")")
                registry["inmain"][id] = true
                // (... and one more action only if is now desired to be in MAP)
                if(desiredState === state_map) {
                  registry["inmap"][ id ] = true
                }
            }
            else if(desiredState === state_stop) {
                registry["indel"][id] = true
            }
        }
        // (if previously was in MAIN)
        else  {
            // console.log("previously in main:" + id + "("+AjaxRecords[id]['name']+")")
            if(desiredState === state_map) {
                registry["inmap"][ id ] = true
            }
            else if(desiredState === state_stop) {
                registry["indel"][id] = true
                registry["outmain"][id] = true
            }
        }
    }
    // console.log("registry")
    // console.log(registry)
    return registry
}



// MAIN SAVE + MAIN CREATE TABLE
// -----------------------------

// Save changes to all corpusA-lists
function SaveLocalChanges() {

  // if there is an activeGroup modification, also finish it and save it
  if (GState == 1) {
      saveActiveGroup()
  }

  // console.clear()
  // console.log("In SaveLocalChanges()")

  // registry with summary of the requested changes with consequences
  // ------------------------------------------------------------------
  // (see InferCRUDFlags)

  FlagsBuffer["outmain"] = {}         // remove from MAINLIST
  FlagsBuffer["inmain"] = {}          //      add to MAINLIST

  FlagsBuffer["outmap"] = {}          // remove from MAPLIST
  FlagsBuffer["inmap"] = {}           //      add to MAPLIST

  FlagsBuffer["outdel"] = {}          // remove from STOPLIST
  FlagsBuffer["indel"] = {}           //      add to STOPLIST


  // LOOP on all mainforms + subforms
  // --------------------------------
  // we use 2 globals to evaluate change-of-state
  //   => OriginalNG for old states (as in DB)
  //   => AjaxRecords for current (desired) states
  for(var id in AjaxRecords) {

    var oldState = OriginalNG["records"][ id ]["state"] ;

    // map and stop not in original states TODO
    if      (OriginalNG["map"][ id ] ) oldState = 1
    else if (OriginalNG["stop"][ id ]) oldState = 2
    else if (typeof oldState == "undefined") {
        console.error('old state in OriginalNG not defined but not map nor stop: (id:' + id +')')
        oldState = 0 ;
    }

    var mainNewState = AjaxRecords[id]["state"] ;

    // update the crud flags buffer according to old/new states and what they entail
    if(oldState != mainNewState) {
        FlagsBuffer = InferCRUDFlags(id, oldState, mainNewState, FlagsBuffer)
    }

    // [ = = = = propagating to subforms = = = = ]

    // if change in mainform list or change in groups
    if(oldState != mainNewState || GroupsBuffer._to_add[id]) {

        // linked nodes
        for (var i in CurrentGroups["links"][id]) {
            var subNgramId = CurrentGroups["links"][id][i] ;

            // todo check (if undefined old state, should add to main too...)
            var subOldState = undefined ;
            if      (OriginalNG["map"][ subNgramId ] ) subOldState = System[0]["statesD"]["keep"]
            else if (OriginalNG["stop"][ subNgramId ]) subOldState = System[0]["statesD"]["delete"]
            else {
                subOldState = System[0]["statesD"]["normal"] ;
                // (special legacy case: subforms can have oldStates == undefined,
                //  then iff target state is != delete, we should add to main too)
                if (mainNewState == System[0]["statesD"]["normal"]
                    || mainNewState == System[0]["statesD"]["map"]) {
                    FlagsBuffer['inmain'][subNgramId] = true
                }
            }

            // update the crud flags buffer with mainNewState (goes to same target state as their mainform)
            FlagsBuffer = InferCRUDFlags(subNgramId, subOldState, mainNewState, FlagsBuffer)
        }
    }
    // [ = = = = / propagating to subforms = = = = ]
  }

  // console.log(" = = = = = = = = = == ")
  // ("FlagsBuffer:")
  // console.log(JSON.stringify(FlagsBuffer))
  // console.warn("GroupsBuffer:")
  // console.log(JSON.stringify(GroupsBuffer))



  // transmit the requested changes to server
  // ----------------------------------------
  // retrieve node_ids from hidden input
  var mainlist_id = $("#mainlist_id").val()
  var maplist_id  = $("#maplist_id" ).val()
  var stoplist_id = $("#stoplist_id" ).val()
  var groupnode_id = $("#groups_id" ).val()

  // var corpus_id = getIDFromURL( "corpora" )

  $("#stoplist_content").html()

  // The AJAX CRUDs in cascade:

  $("#Save_All").append('<img width="8%" src="/static/img/ajax-loader.gif"></img>')

  // trigger chained CRUD calls
  CRUD_1_AddMap()

  // add some ngrams to maplist
  function CRUD_1_AddMap() {
    console.log("AJAX CRUD1 AddMap") ;
    CRUD( maplist_id , Object.keys(FlagsBuffer["inmap"]), "PUT" , function(success) {
      if (success) {
        CRUD_2_RmMap()      // trigger chained AJAX  1 -> 2
      }
      else {
        console.warn('CRUD error on ngrams add to maplist ('+maplist_id+')')
      }
    });
  }
  // remove some ngrams from maplist
  function CRUD_2_RmMap() {
    console.log("AJAX CRUD2 RmMap") ;
    CRUD( maplist_id , Object.keys(FlagsBuffer["outmap"]), "DELETE" , function(success) {
      if (success) {
        CRUD_3_AddMain()    // chained AJAX  2 -> 3
      }
      else {
        console.warn('CRUD error on ngrams remove from maplist ('+maplist_id+')')
      }
    });
  }
  // add some ngrams to mainlist
  function CRUD_3_AddMain() {
    console.log("AJAX CRUD3 AddMain") ;
    CRUD( mainlist_id , Object.keys(FlagsBuffer["inmain"]), "PUT" , function(success) {
      if (success) {
        CRUD_4_RmMain()    // chained AJAX  3 -> 4
      }
      else {
        console.warn('CRUD error on ngrams add to mainlist ('+mainlist_id+')')
      }
    });
  }
  // remove some ngrams from mainlist
  function CRUD_4_RmMain() {
    console.log("AJAX CRUD4 RmMain") ;
    CRUD( mainlist_id , Object.keys(FlagsBuffer["outmain"]), "DELETE" , function(success) {
      if (success) {
        CRUD_5_AddStop()    // chained AJAX  4 -> 5
      }
      else {
        console.warn('CRUD error on ngrams remove from mainlist ('+mainlist_id+')')
      }
    });
  }
  // add some ngrams to stoplist
  function CRUD_5_AddStop() {
    console.log("AJAX CRUD5 AddStop") ;
    CRUD( stoplist_id , Object.keys(FlagsBuffer["indel"]), "PUT" , function(success) {
      if (success) {
        CRUD_6_RmStop()    // chained AJAX  5 -> 6
      }
      else {
        console.warn('CRUD error on ngrams add to stoplist ('+stoplist_id+')')
      }
    });
  }
  // remove some ngrams from stoplist
  function CRUD_6_RmStop() {
    console.log("AJAX CRUD6 RmStop") ;
    CRUD( stoplist_id , Object.keys(FlagsBuffer["outdel"]), "DELETE" , function(success) {
      if (success) {
        CRUD_7_AddGroups()    // chained AJAX  6 -> 7
      }
      else {
        console.warn('CRUD error on ngrams remove from stoplist ('+stoplist_id+')')
      }
    });
  }
  // add to groups reading data from GroupsBuffer
  // (also removes previous groups with same mainforms!)
  function CRUD_7_AddGroups() {
      console.log("AJAX CRUD7 AddGroups") ;
      GROUPCRUDS(groupnode_id, GroupsBuffer._to_add, "PUT" , function(success) {
          if (success) {
              CRUD_8_RmGroups()    // chained AJAX  7 -> 8
          }
          else {
              console.warn('CRUD error on groups modification ('+groupnode_id+')')
          }
      }) ;
  }

  // add to groups reading data from GroupsBuffer
  function CRUD_8_RmGroups() {
      console.log("AJAX CRUD8 RmGroups") ;
      GROUPCRUDS(groupnode_id, GroupsBuffer._to_del, "DELETE", function(success) {
          if (success) {
              window.location.reload() // all 8 CRUDs OK => refresh whole page
          }
          else {
              console.warn('CRUD error on groups removal ('+groupnode_id+')')
          }
      }) ;
  }
}    // end of SaveLocalChanges


// For list modifications (add/delete), all http-requests
function CRUD( list_id , ngram_ids , http_method , callback) {
    // ngramlists/change?node_id=42&ngram_ids=1,2
    // var the_url = window.location.origin+"/api/ngramlists/change?list="+list_id+"&ngrams="+ngram_ids.join(",");
    var the_url = window.location.origin+"/api/ngramlists/change?list="+list_id;

    // debug
    // console.log("  ajax target: " + the_url + " (" + http_method + ")")

    // 2016-10-05 pass PUT and DELETE ngrams in payload as if it was POSTs
    // (to avoid too long urls that trigger Bad Gateway in production)

    var myNgramsData = new FormData();
    myNgramsData.append("ngrams", ngram_ids.join(","))

    if(ngram_ids.length>0) {
        $.ajax({
          method: http_method,
          async: true,
          contentType: false,
          processData: false,
          data: myNgramsData,
          url: the_url,
            //    data: args,   // currently all data explicitly in the url (like a GET)
          beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          },
          success: function(data){
                console.log("-- CRUD ----------")
                console.log(http_method + " ok!!")
                // console.log(JSON.stringify(data))
                // console.log("------------------")
                callback(true);
          },
          error: function(result) {
              console.log("-- CRUD ----------")
              console.error("AJAX Error on " + http_method + " " + the_url);
            //   console.log(result)
            //   console.log("------------------")
              callback(false);
          }
        });

    } else callback(true);
}


// For group modifications
//  @param groupnode_id: the node with the groupings to change
//  @param send_data: {mainformA: [subformsA1,A2,A3], mainformB:..})
//
//  @param http_method:
//         PUT: adds new group rows : groupnode_id -- mainformA -- subformsA1
//                                    groupnode_id -- mainformA -- subformsA2
//                                    groupnode_id -- mainformA -- subformsA3
//                                    groupnode_id -- mainformB -- ....
//
//         DEL: idem but removes the group rows
//
// ex: /api/ngramlists/groups?node=783&3409[]=4745,14691,3730
//
// NB no chained effects

function GROUPCRUDS( groupnode_id , send_data, http_method , callback) {

    // ngramlists/groups?node=9
    var the_url = window.location.origin+"/api/ngramlists/groups?node="+groupnode_id;

    if(Object.keys(send_data).length > 0) {
        // group details go also in the url as additional params
        for (var mainformId in send_data) {
            subformIds = send_data[mainformId]
            if (typeof subformIds != "undefined" && subformIds.constructor == Array) {
                console.log("(ok doing: "+http_method+") for mainform "+mainformId+" with subforms", subformIds)
                the_url = the_url + '&' + mainformId + '[]=' + subformIds.join()
            }
            else {
                console.error("(skipping: "+http_method+") for mainform "+mainformId+" with subforms", subformIds)
            }
        }

        $.ajax({
          method: http_method,
          url: the_url,
          // data: send_data // all data explicitly in the url (like a GET)
                             // because DEL can't consistently support form data

          beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          },
          success: function(data){
                console.log("-- GROUPCRUD ----------")
                console.log(http_method + " ok!!")
             // console.log(JSON.stringify(data))
             // console.log("-----------------------")
                callback(true);
          },
          error: function(result) {
              console.log("-- GROUPCRUD ----------")
              console.error("AJAX Error on " + http_method + " " + the_url);
            //console.log(result)
            //console.log("------------------")
              callback(false);
          }
        });

    } else callback(true);
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
 * 4. Set up Search div and initialize user filter statuses
 *
 * @param ngdata:        OriginalNG['records']
 * @param initial:       initial score type "occs" or "tfidf" => £TODO multiscore
 * @param filtersParams: contains the option values in a "picklistParams object"
 *                       It can be {} or custom/cached keys for init of filters
 */
function MainTableAndCharts( ngdata , initial , filtersParams, callerLabel) {

    // debug
    // alert("refresh main")

    // console.log("")
    // console.log(" = = = = MainTableAndCharts: = = = = ")
    // console.log("ngdata:")
    // console.log(ngdata)
    // console.log("initial:")   //
    // console.log(initial)
    console.log("filtersParams:")        // eg {'lists': filter_all'}
    if(typeof(filtersParams) != 'undefined') {console.log(filtersParams)} else {console.log('pas de params')}
    console.log("callerLabel:")
    if(typeof(callerLabel) != 'undefined') {console.log(callerLabel)} else {console.log('pas de callerLabel')}
    // console.log(" = = = = / MainTableAndCharts: = = = = ")
    // console.log("")

    // Expected infos in "ngdata" should have the form:
    // { "1": { id: "1", name: "réalité",        score: 36  },
    //   "9": { id: "9", name: "pdg",            score: 116 },
    //  "10": { id:"10", name: "infrastructure", score:  12 }  etc. }

    // (see filling of rec_info below)
    // console.log(ngdata)

    var DistributionDict = {}
    for(var i in DistributionDict)
        delete DistributionDict[i];
    delete DistributionDict;
    DistributionDict = {}

    var FirstScore = initial;

    var arrayd3 = []

    //  div_table += "\t"+"\t"+"\t"+'<input type="checkbox" id="multiple_selection" onclick="SelectPage(this);" /> Select'+"\n"
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

      // uncomment for column ngramId (here and in transformContent - l.1134)
      // div_table += "\t"+"\t"+'<th data-dynatable-column="ngramId" style="background-color:grey">ngramId</th>'+"\n";

      // uncomment for column stateId (here and in transformContent - l.1137)
      // div_table += "\t"+"\t"+'<th data-dynatable-column="state" style="background-color:grey">State</th>'+"\n" ;

      // selector columns... not sortable to allow 'click => check all'
      div_table += "\t"+"\t"+'<th data-dynatable-column="will_be_map"'
                            + ' data-dynatable-no-sort="true"'
                            + ' title="Selected terms will appear in the map."'
                            + ' style="width:3em;"'
                            + '>'
                            + 'Map'
                            + '<p class="note">'
                            + '<input type="checkbox" id="mapAll"'
                            + ' onclick="SelectPage(\'keep\',this)" title="Check to select all currently visible terms"></input>'
                            + '<label>All</label>'
                            + '</p>'
                            + '</th>'+"\n" ;
      div_table += "\t"+"\t"+'<th data-dynatable-column="will_be_stop"'
                            + ' data-dynatable-no-sort="true"'
                            + ' title="Selected terms will be removed from all lists."'
                            + ' style="width:3em;"'
                            + '>'
                            + 'Stop'
                            + '<p class="note">'
                            + '<input type="checkbox" id="delAll"'
                            + ' onclick="SelectPage(\'delete\',this)" title="Check to select all currently visible terms"></input>'
                            + '<label>All</label>'
                            + '</p>'
                            + '</th>'+"\n" ;
      // main name and score columns
      div_table += "\t"+"\t"+'<th data-dynatable-column="name">Terms</th>'+"\n";
      div_table += "\t"+"\t"+'<th id="score_column_id" data-dynatable-sorts="score" data-dynatable-column="score">Occurences (nb)</th>'+"\n";
      div_table += "\t"+"\t"+'</th>'+"\n";
      div_table += "\t"+'</tr>'+"\n";
      div_table += "\t"+'</thead>'+"\n";
      div_table += "\t"+'<tbody>'+"\n";
      div_table += "\t"+"\t"+'<tr><td>a</td><td>a</td><td>a</td><td>a</td></tr>'+"\n";
      div_table += "\t"+'</tbody>'+"\n";
      div_table += '</table>'+"\n";
      div_table += '</p>';
    $("#div-table").html(div_table)

    // width of the table in columns
    tableSpan = $("#div-table th").length ;

    // indeterminate: only visual
    $('#delAll').prop("indeterminate", true)
    $('#mapAll').prop("indeterminate", true)

    // real checkAll states : SOME|ALL|NONE
    $('#delAll').data("columnSelection", 'SOME')
    $('#mapAll').data("columnSelection", 'SOME')

    // var div_stats = "<p>";
    // for(var i in ngscores) {
    //   var value = (!isNaN(Number(ngscores[i])))? Number(ngscores[i]).toFixed(1) : ngscores[i];
    //   div_stats += i+": "+value+" | "
    // }
    // div_stats += "</p>"
    // $("#stats").html(div_stats)

    // NB will be transformed into ArrayAjaxRecords for dynatable pagination
    AjaxRecords = {}

    for(var id in ngdata) {

      // console.log(i)
      // console.log(ngdata[i])
      var le_ngram = ngdata[id] ;

      // INIT records
      // one record <=> one line in the table + ngram states
      var rec_info = {
        "id" : le_ngram.id,
        "name": le_ngram.name,
        "score": le_ngram.score,
        "flag":false,
        // "state": 0
        "state": (le_ngram.state)?le_ngram.state:0,

        // properties enabling to see old and new groups
        "group_exists": (le_ngram.id in CurrentGroups["links"])
      }

      // temporary fix for scores out of broken groups
      // useful for corpora imported during the 'falsefalsefalse' bug period
      // (between 2016-05-23   and   2016-06-07)
      if (
          (typeof le_ngram.score == "undefined" || le_ngram.score == null)
           && (typeof le_ngram.state == "undefined" || (le_ngram.state != 2 && le_ngram.state != -1))
            ) {
          console.warn("no score for:" + le_ngram.id, le_ngram.name)
      }

      // AjaxRecords.push(rec_info)
      AjaxRecords[id] = rec_info

      // now ngram.score will be the key (=> X value) ...
      var xkey ;
      if (! isNumeric(rec_info.score)) {
          xkey = 0
      }
      else {
          xkey = rec_info.score
      }

      // ... and we count how often an ngram got it (=> Y value)
      if ( ! DistributionDict[xkey] ) {
          DistributionDict[xkey] = 1;
      }
      else {
          DistributionDict[xkey]++;
      }

    }

    // console.log(FirstScore)

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
    //     // DistributionList[i].x_occ = Math.log( DistributionList[i].x_occ )
    //     // DistributionList[i].y_frec = Math.log( DistributionList[i].y_frec )+1
    //     console.log( DistributionList[i] )
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
    .dimension(x_occs)
    .group(y_frecs)
    .x(d3.scale.linear().domain([min_occ,max_occ+min_occ]))
      .width(800)
      .height(150)
      .margins({top: 10, right: 50, bottom: 25, left: 40})
      .transitionDuration(500)
      .y(d3.scale.log().domain([min_frec/2,max_frec*2]))
      .renderArea(true)
    //   .valueAccessor(function (d) {
    //       console.log(d)
    //       if(isNumeric(d)) {
    //           return d.value;
    //       }
    //       else return 0 ;
    //   })

    //   .ordinalColors(d3.scale.category10())
      .elasticY(true)
      // .round(dc.round.floor)
      .renderHorizontalGridLines(true)
      .renderVerticalGridLines(true)
      // .colors('red')
      // .interpolate("monotone")
      // .renderDataPoints({radius: 2, fillOpacity: 0.8, strokeOpacity: 0.8})
      .brushOn(false)
      .rangeChart(volumeChart)
      .title(function (d) {
          if (isNaN(d.data.value))  {
              console.warn(JSON.stringify(d))
          }
          // exemple d here:
          // Object {
          //            x:2698,        y:1,
          //         layer:0,y0:0,
          //         data:{key:2698, value:1}
          //        }
                  var value = d.y;
                  if (isNaN(value)) value = 0;
                  return value+" ngrams with "+FirstScore+"="+Number(d.key);
              })
      .xAxis();
    LineChart.yAxis().ticks(5)
    LineChart.render()


    // selectable barchart
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
            // ------------------------------------------------------
            // main hook between Chart => Buffer => Final_UpdateTable
            // ------------------------------------------------------
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

    // expose selection brush
    var ourBrush = volumeChart.brush()

    // --------------------------
    // DYNATABLE initialization
    // --------------------------
    // writes in the app scope var MyTable
    MyTable = []
    MyTable = $('#my-ajax-table').dynatable({
                dataset: {
                  // from AjaxRecords => array (to maintain proper page range)
                  records: makeRecordArray(AjaxRecords),
                  sortTypes: {
                      "score": 'NumOrNaNSort'
                  },
                  perPageOptions: [20,50,100,200]
                },
                features: {
                  pushState: false,
                },
                writers: {
                  _rowWriter: ulWriter
                  // _cellWriter: customCellWriter
                },
                inputs: {
                    queries: $('select#picklistmenu, select#picktermtype'),
                }
            })

    // /!\ settings.dataset.originalRecords will be set to ArrayAjaxRecords (in lib)

    // sorts on numbers but allows NaN (and puts them as highest)
    // ----------------------------------------------------------
    MyTable.data('dynatable').sorts.functions["NumOrNaNSort"] = function NumOrNaNSort (rec1,rec2, attr, direction) {
        if (typeof direction == "undefined") {
            return 0
        }
        score1Numeric = (typeof rec1.score == 'number')
        score2Numeric = (typeof rec2.score == 'number')

        // if (rec1.state == -1 || rec2.state == -1) {
        //     console.warn("Programming error: can't process inactive items in sort")
        //     return (rec1.name < rec2.name) ? direction : (-direction)
        // }

        // we'll assume both records have active states
        if (score1Numeric && score2Numeric) {
            return direction * (rec2.score - rec1.score)
        }
        else if (score1Numeric) {
            return direction
        }
        else if (score2Numeric) {
            return -direction
        }
        // when both records have non numeric values => alpha sort
        else {
            return (rec1.name < rec2.name) ? direction : (-direction)
        }
    }

    // hook on page change
    MyTable.bind('dynatable:page:set', tidyAfterPageSetUpdate)

    // hook on any type of update
    MyTable.bind('dynatable:afterUpdate', tidyAfterUpdate)

    // £TODO multiscore
    // // // $("#score_column_id").children()[0].text = FirstScore
    // // // // MyTable.data('dynatable').process();

    // bind a filter named 'my_state_filter' to dynatable.queries.functions
    MyTable.data('dynatable').queries
        // selects on current state <=> shows only elements of specific list
        // (see terms.html > #picklistmenu)
        .functions['my_state_filter'] = function(record,selectedValue) {
            if (selectedValue == 'reset') {
                // return (AjaxRecords[record.id].state >= 0)
                return true
            }
            // for states, possible value are in {0,1,2}
            else {
              // return true or false
              return (AjaxRecords[record.id].state == selectedValue)
            }
        }

    // second filter named 'my_termtype_filter' for gargantext lists (map, )
    MyTable.data('dynatable').queries
        .functions['my_termtype_filter'] = function(record,selectedValue) {
            if (selectedValue == 'reset') {
                return true
            }
            else if (selectedValue == 'mono') {
                // one-word terms aka monograms aka monolexical terms
                return (AjaxRecords[record.id]['name'].indexOf(" ") == -1)
            }
            else if (selectedValue == 'multi') {
                // MWE aka multigrams aka polylexical terms
                return (AjaxRecords[record.id]['name'].indexOf(" ") != -1)
            }
        }

    // and set these filters' initial status
    var MyTablesQueries = MyTable.data('dynatable').settings.dataset.queries

    MyTablesQueries['my_state_filter'] = filtersParams.gtlists || 'reset' ;
    MyTablesQueries['my_termtype_filter'] = filtersParams.multiw || 'reset' ;

    // set main text-search value
    MyTablesQueries['search'] = filtersParams.search || ''

    // set table pagination
    MyTable.data('dynatable').paginationPage.set(1);
    MyTable.data('dynatable').paginationPerPage.set(filtersParams.perpp || 50) ;

    // also set sorts
    MyTable.data('dynatable').sorts.clear();

    MyTable.data('dynatable').sorts.add( filtersParams.sortk || "score",
                                         filtersParams.sortdirec || 1
                                         // 1=DESCENDING,
                                       )

    // go ! ------------------------------
    MyTable.data('dynatable').process();
    // -----------------------------------

    // moves pagination over table
    // £TODO pagination copy instead (hard!)
    if ( $(".imadiv").length>0 ) return 1;
    $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
    $(".dynatable-record-count").insertAfter(".imadiv")
    $(".dynatable-pagination-links").insertAfter(".imadiv")

//    $('<div class="imadiv"></div>').insertAfter("#my-ajax-table")
//    $(".dynatable-record-count").insertAfter(".imadiv")
//    $(".dynatable-pagination-links").insertAfter(".imadiv")

    // restore chart filters
    if (typeof(filtersParams.from) != 'undefined'
        && typeof(filtersParams.to) != 'undefined'
        && ! (filtersParams.from == null)
        && ! (filtersParams.to == null)) {

      var fromVal = filtersParams.from
      var toVal = filtersParams.to

      if (fromVal != oldest || toVal != latest) {
        // volumeChart.filterAll()               // re-init
        placeBrush(ourBrush, fromVal, toVal)
        // placeBrush also does volumeChart.filter([fromVal, toVal]) and Push2Buffer
      }
    }


    return "OK"
}


// =============================================================================
//                               SUBROUTINES
// =============================================================================


// This function is connected to a "Test" button in the html
// place here anything you want to test
function doATest() {
    console.log("v----------- TEST -----------v")
    MyTable.data('dynatable').queries.add('group_exists',true);
    MyTable.data('dynatable').process();
    console.log("^---------- /TEST -----------^")
}

/**
 * placeBrush cf. http://bl.ocks.org/timelyportfolio/5c136de85de1c2abb6fc:
 *     -----------
 *  Adds the brush (aka "chart's selection zone") programmatically
 *  (for instance at initialize if we want to restore previous selection)
 */
function placeBrush(myBrush, min, max) {

  // define our brush extent
  myBrush.extent([min, max])

  // now draw the brush to match our extent
  myBrush(d3.select(".brush"));

  // now fire the brushstart, brushmove, and brushend events
  myBrush.event(d3.select(".brush"))
}

/**
 * tidyAfterUpdate:
 *     -----------
 *    Here we clean all our vars that become obsolete when any update occurs
 *    (this function is bound to the dynatable event "dynatable:afterUpdate")
 */
function tidyAfterUpdate(event) {
    // debug:
    // console.log("event") ;
    // console.log(event) ;

    // CLEAR ALL FLAGS AND GLOBAL VARS HERE
    // currently nothing to do
}


/**
 * tidyAfterPageSet:
 *     -------------
 *    Here we convert AjaxRecords to an array
 */
function makeRecordArray(recordsDict) {
    var recArray = []
    for (ngid in recordsDict) {
        // must filter inactive forms for pagination/number of items to work right
        if (recordsDict[ngid]['state'] != -1) {
            recArray.push(recordsDict[ngid]) ;
        }
    }
    return recArray
}


/**
 * tidyAfterPageSet:
 *     -------------
 *    Here we clean vars that become obsolete not at all updates, but only
 *    when page changes (bound to the dynatable event "dynatable:page:set")
 */

function tidyAfterPageSetUpdate() {

    // (1)
    // SelectPage keeps cache of column states but
    // a new page is new ngrams in their own lists

    // we visually uncheck both 'all' boxes
    $('input#delAll').attr('checked', false);
    $('input#mapAll').attr('checked', false);

    // indeterminate: only visual
    $('#delAll').prop("indeterminate", true)
    $('#mapAll').prop("indeterminate", true)

    // real checkAll states : SOME|ALL|NONE
    $('#delAll').data("columnSelection", 'SOME')
    $('#mapAll').data("columnSelection", 'SOME')

    // (2)
    // page change must've closed all group's minilists so we blank open states
    vizopenGroup = {}
}


function pr(msg) {
    console.log(msg)
}

function isNumeric(n) {
  return (!isNaN(parseFloat(n)) && isFinite(n))
}

// this turns ON the NeedSave flag and the corresponding visual
// (it can only go back OFF with a save action via page reload)
function toggleNeedSave() {

    var icons = $(".needsaveicon")
    var boxes = $('.savediv')
    var topButton = $('#ImportListOrSaveAll')
    var botButton = $('#Save_All_Bottom')

    // change the status icons
    icons.removeClass("glyphicon-floppy-saved");
    icons.removeClass("glyphicon-import");
    icons.addClass("glyphicon-exclamation-sign");
    icons.css("color","red");
    icons.css("font-size","120%");

    // give new text to the hybrid save/import button
    topButton.html("<b>Save all changes</b>")

    // save_divs get a new tooltip title
    boxes.prop('title', "Click to save all changes to DB")

    // activate the buttons
    topButton.prop('disabled', false) ;
    topButton.removeClass("btn-warning");
    topButton.addClass("btn-success");

    botButton.prop('disabled', false) ;
    botButton.removeClass("btn-muted");
    botButton.addClass("btn-success");

    // bind the onclick events (it also replaces the default import onclick for the hybrid button)
    topButton.attr("onclick","SaveLocalChanges()");
    botButton.attr("onclick","SaveLocalChanges()");

    // toggle the global var ON
    _NeedSave = true
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
            callback(data, url);
        },
        error: function(exception) {
            callback(false, url);
        }
    })
}

// ######################### AJAX && INIT #########################


// [ = = = = = = = = = = INIT = = = = = = = = = = ]
// http://localhost:8000/api/node/84592/ngrams?format=json&score=tfidf,occs&list=miam
var corpus_id = getIDFromURL( "corpora" )
var OriginalNG = {
    "records" : {},
    "stop" : {},
    "map" : {},
    "scores" : {},
    "links" : {}
}


// MAIN AJAX

var prefetch_url = window.location.origin+"/api/ngramlists/maplist?corpus="+corpus_id ;
var final_url = window.location.origin+"/api/ngramlists/family?corpus="+corpus_id ;

// faster call: just the maplist, will return first
// 2016-05-13: deactivated because it causes a lag before the table is updated
//             FIXME: probably because of != nb of records ?
// GET_(prefetch_url, HandleAjax);

// longer call (full list of terms) to return when ready and refresh all data
GET_(final_url, HandleAjax)

function HandleAjax(res, sourceUrl) {
    //TODO unify with AfterAjax
    if (res && res.ngraminfos) {

        // = = = = MIAM = = = = //
        OriginalNG["records"] = {}
        for (var ngram_id in res.ngraminfos) {
            var ngram_tuple = res.ngraminfos[ngram_id]
            OriginalNG["records"][ngram_id] = {
                'id' : ngram_id,         // redundant but for backwards compat
                'name' : ngram_tuple[0],

                // 'NaN' is our standard for re-reading un-recounted corpora
                'score' : ngram_tuple[1] ? ngram_tuple[1] : 'NaN',

                // state 0 temporary default: for non-main items, it'll be updated to -1, 1 or 2
                'state' : 0
            }
        }


        OriginalNG["scores"] = {
                "initial":"occs",
                "nb_ngrams":Object.keys(OriginalNG["records"]).length,
            }

        // = = MAP ALSO STOP = = //
        // 2x(array of ids) ==> 2x(lookup hash)
        OriginalNG["map"] = {} ;
        for (var i in res.listmembers.maplist) {
            var map_ng_id = res.listmembers.maplist[i] ;
            OriginalNG["map"][map_ng_id] = true ;
        }

        OriginalNG["stop"] = {} ;
        for (var i in res.listmembers.stoplist) {
            var stop_ng_id = res.listmembers.stoplist[i] ;
            OriginalNG["stop"][stop_ng_id] = true ;
        }

        // = = = = GROUP = = = = //
        // they go directly to "Current" var (we need not keep the original situation)
        CurrentGroups["links"] = res.links ;

    }
    // console.log('after init OriginalNG["records"]')
    // console.log(OriginalNG["records"])

    // cache all DB node_ids
    $("input#mainlist_id").val(res.nodeids['mainlist'])
    $("input#maplist_id" ).val(res.nodeids['maplist'])
    $("input#stoplist_id").val(res.nodeids['stoplist'])
    $("input#groups_id").val(res.nodeids['groups'])
    $("input#scores_id").val(res.nodeids['scores'])
    AfterAjax(sourceUrl) ;
}


// unpack ajax values, read table settings from cache if any, and run Main
function AfterAjax(sourceUrl) {
  // -------------------------------------------------------------------
  // console.log(JSON.stringify(OriginalNG))
  // -------------------------------------------------------------------

  state_skip = -1                              // -1
  state_main = System[0]["statesD"]["normal"]  //  0
  state_map  = System[0]["statesD"]["keep"]    //  1
  state_stop = System[0]["statesD"]["delete"]  //  2

  // ----------------------------------------- MAPLIST

  if( Object.keys(OriginalNG["map"]).length>0 ) {
      for(var ngram_id in OriginalNG["map"]) {
          myNgramInfo = OriginalNG["records"][ngram_id]
          if (typeof myNgramInfo == "undefined") {
              console.error("record of ngram " + ngram_id + " was undefined")
          }
          else {
              // initialize state of maplist items
              myNgramInfo["state"] = state_map ;
          }
      }
  }

  // ----------------------------------------- STOPLIST

  if( Object.keys(OriginalNG["stop"]).length>0 ) {
      for(var ngram_id in OriginalNG["stop"]) {
          myNgramInfo = OriginalNG["records"][ngram_id]
          if (typeof myNgramInfo == "undefined") {
              console.error("record of ngram " + ngram_id + " is undefined")
          }
          else {
              // initialize state of stoplist items
              myNgramInfo["state"] = state_stop ;
          }
      }
  }

    // Deactivating subforms from the ngrams-table, clean start baby!
    if( Object.keys(CurrentGroups["links"]).length>0 ) {
        // init global actualized subform inventory (reverse index of links)
        // (very useful to find what to change if group is split)
        for(var ngramId in CurrentGroups["links"]) {
            for(var i in CurrentGroups["links"][ngramId]) {
                var subformId = CurrentGroups["links"][ngramId][i]
                // for each subform: mainform
                CurrentGroups["subs"][ subformId ] = ngramId
            }
        }

        // use it to deactivate <=> hidden state for all them subforms
        for (var subNgramId in CurrentGroups["subs"]) {

            // will allow us to distinguish it from mainlist items that
            // have default original state (in InferCRUDFlags)
            OriginalNG['records'][subNgramId]['state'] = state_skip
        }
    }


    // Building the Score-Selector //OriginalNG["scores"]
    var FirstScore = OriginalNG.scores.initial
    // TODO scores_div multiscore
    //       Recreate possible_scores from some constants (tfidf, occs)
    //       and not from ngrams[0], to keep each ngram's info smaller

    // var possible_scores = Object.keys( OriginalNG["main"].ngrams[0].scores );
    // var scores_div = '<br><select style="font-size:25px;" class="span1" id="scores_selector">'+"\n";
    // scores_div += "\t"+'<option value="'+FirstScore+'">'+FirstScore+'</option>'+"\n"
    // for( var i in possible_scores ) {
    //   if(possible_scores[i]!=FirstScore) {
    //     scores_div += "\t"+'<option value="'+possible_scores[i]+'">'+possible_scores[i]+'</option>'+"\n"
    //   }
    // }

    // show only map (option = 1, good for waiting if async records)
    // or all terms (option = "reset")

    // table settings for filters etc.
    var configIfAny = {}
    configIfAny = restoreSettingsFromCache()

    // configIfAny.gtlists = (sourceUrl == final_url) ? "reset" : "1"  // condition useful for prefetch

    // Initializing the Charts and Table ---------------------------------------
    var result = MainTableAndCharts(OriginalNG["records"], FirstScore , configIfAny, "AfterAjax") ;

    console.log( result ) // OK
    // -------------------------------------------------------------------------

    $("#content_loader").remove()

}
