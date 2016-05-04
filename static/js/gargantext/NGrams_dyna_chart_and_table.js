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
 * @author
 *   Samuel Castillo (original 2015 work)
 *   Romain Loth
 *           - minor 2016 modifications + doc
 *           - unify table ids with ngram ids
 *
 * @version 1.0 beta
 *
 * @requires jquery.dynatable
 * @requires d3
 */


// =============================================================================
//                      GLOBALS  <=> INTERACTIVE STATUS etc
// =============================================================================


// ngram infos (<-> row data)
// --------------------------
// from /api/ngramlists/lexmodel?corpus=312
// with some expanding in AfterAjax
var AjaxRecords = [] ;


// table element (+config +events)
// -------------------------------
var MyTable ;


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
// 3 main buffers per state (and later additional per target)
for(var i in System[GState]["states"]) {
  FlagsBuffer[System[GState]["states"][i]] = {}
}

// + 1 for groups
GroupsBuffer = {}


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
function printCorpuses() {
    console.log( "!!!!!!!! in printCorpuses() !!!!!!!! " )
    pr(corpusesList)

    var selected = $('input[name=optradio]:checked')[0].id.split("_")
    var sel_p = selected[0], sel_c=selected[1]

    var current_corpus =  getIDFromURL("corpora")

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
        var result = MainTableAndCharts(sub_ngrams_data , NGrams["main"].scores.initial , "filter_all")
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
    console.log("\nFUN Final_UpdateTable()")

    // console.log("AjaxRecords")
    // console.log(AjaxRecords)

    // (1) Identifying if the button is collapsed:
    var isCollapsed=false;
    var tableClass = $("#terms_table").attr("class")

    //\bcollapse\b
    if(tableClass.indexOf(" collapse ")>-1) {
        isCollapsed=true;
    }

    var UpdateTable = false
    if ( (action == "click" && !isCollapsed) || (action=="changerange" && isCollapsed) ) {
        UpdateTable = true;
        $("#corpusdisplayer").html("Close Term List")
    } else $("#corpusdisplayer").html("View by terms")

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
    // pr("saving mainform to GroupsBuffer: " + mainform)

    // the new array to save is in now_links -------------
    GroupsBuffer[mainform] = activeGroup.now_links
    // ---------------------------------------------------

    console.log(AjaxRecords[mainform])

    // also we prefix "*" to the name if not already there
    if (AjaxRecords[mainform].name[0] != '*') {
        AjaxRecords[mainform].name = "*" + AjaxRecords[mainform].name
    }

    // the previous mainforms that became subforms can't stay in the main records
    for (downgradedNgramId in activeGroup.were_mainforms) {
        if (downgradedNgramId != mainform) {

            AjaxRecords[downgradedNgramId].state = -1

            // they go to nodesmemory
            // NGrams.group.nodesmemory = AjaxRecords[downgradedNgramId]
            // delete AjaxRecords[downgradedNgramId]
        }
    }

    // TODO posttest
    // the previous "old" links are now in GroupsBuffer so from now on
    // they'll be searched in AjaxRecords by updateActiveGroupInfo()
    delete NGrams.group.links[mainform]
    for (i in activeGroup.now_links) {
        newLink = activeGroup.now_links[i] ;
        if (activeGroup.ngraminfo[newLink].origin == 'old' || activeGroup.ngraminfo[newLink].origin == 'oldnew') {
            // new AjaxRecords entry from nodesmemory
            AjaxRecords[newLink] = NGrams.group.nodesmemory[newLink]
            delete NGrams.group.nodesmemory[newLink]
            // console.log('oldLinkThatBecameNew: '+AjaxRecords[newLink].name)
        }
    }

    // clean group modification zone and buffer and update table
    removeActiveGroupFrame()
}

function removeActiveGroupFrame() {
    // erases now_links and restores empty activeGroup global cache
    activeGroup = {'now_mainform_id':undefined, 'were_mainforms':{}} ;

    // remove the entire top row that was used as group modification zone
    $("#group_box").remove()
    GState=0

    // we also close the open sublists in case some of them don't exist any more
    vizopenGroup = {}

    // reprocess from current record states
    MyTable.data('dynatable').dom.update();
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
    // 1/7 create new element container
    var subNgramHtml = $('<p class="note">') ;
    subNgramHtml.attr("id", "subforms-"+ngramId) ;
    subNgramHtml.css("line-height", 1.2) ;
    subNgramHtml.css('margin-left','.3em') ;
    subNgramHtml.css("margin-top", '.5em') ;


    // 2/7 attach flag open to global state register
    vizopenGroup[ngramId] = true ;

    // 3/7   retrieve names of the original (from DB) grouped ngrams
    var oldlinksNames = [] ;
    if( ngramId in NGrams.group.links ) {
        for (var i in NGrams.group.links[ngramId]) {
            var subNgramId = NGrams.group.links[ngramId][i] ;
            oldlinksNames[i] = NGrams.group.nodesmemory[subNgramId].name
        }
    }

    // 4/7   retrieve names of the newly created grouped ngrams
    var newlinksNames = [] ;
    if( ngramId in GroupsBuffer ) {
        for(var i in GroupsBuffer[ ngramId ] ) {
            var subNgramId = GroupsBuffer[ ngramId ][i] ;
            newlinksNames[i] = AjaxRecords[subNgramId].name
        }
    }

    // 5/7 create the "tree" from the names, as html lines
    var htmlMiniTree = drawSublist(oldlinksNames.concat(newlinksNames))
    subNgramHtml.append(htmlMiniTree)

    // 6/7 add a "modify group" button
    if (allowChangeFlag) {
        var changeGroupsButton  = '<button style="float:right"' ;
            changeGroupsButton +=        ' title="add/remove contents of groups"' ;
            changeGroupsButton +=        ' onclick="modifyGroup('+ngramId+')">' ;
            changeGroupsButton +=   'modify group' ;
            changeGroupsButton += '</button>' ;
        subNgramHtml.append(changeGroupsButton) ;
    }

    // 7/7  return html snippet (ready for rendering)
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

function drawActiveGroup (tgtElementId, mainformId, linkIdsArray, ngInfos) {
    var groupHtml  = '<p id="group_box_mainform">';
        groupHtml +=    mainformSpan(ngInfos[mainformId])
        groupHtml += '  <br> │<br>';
        groupHtml += '</p>';
        // sublist
        groupHtml += '<p id="group_box_content">';

    var last_i = linkIdsArray.length - 1 ;
    for(var i in linkIdsArray) {
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
    var cancelGroupButton  = '<button onclick="removeActiveGroupFrame()">' ;
        cancelGroupButton +=   'cancel' ;
        cancelGroupButton += '</button>' ;

    var tempoSaveGroupButton  = '<button onclick="saveActiveGroup()">' ;
        tempoSaveGroupButton +=   'finish' ;
        tempoSaveGroupButton += '</button>' ;

    groupHtml += cancelGroupButton
    groupHtml += tempoSaveGroupButton
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
        id: 'active-subform-' + subNgramInfo.id
    })

    if (subNgramInfo.origin == 'old') {
        span.addClass("oldsubform")
    }
    else if (subNgramInfo.origin == 'new' || subNgramInfo.origin == 'oldnew'){
        span.addClass("usersubform")
    }

    // remove button
    // var removeButton  = '&nbsp;<span class="note glyphicon glyphicon-minus-sign"'
    //     removeButton +=   ' title="remove from group (/!\\ bug: will be unattached if was previously a subform)"' ;
    //     removeButton +=   ' onclick="removeSubform('+ subNgramInfo.id +')"></span>'
    // span.append(removeButton)

    // makes this subform become the mainform
    // var mainformButton  = '&nbsp;<span class="note glyphicon glyphicon-circle-arrow-up"'
    //     mainformButton +=   ' title="upgrade to mainform of this group"'
    //     mainformButton +=   ' onclick="makeMainform('+ subNgramInfo.id +')"></span>'
    // span.append(mainformButton)
    return(span[0].outerHTML)
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
    //   -> it had no entry in AjaxRecords
    //   -> it was not in any of the lists
    if (! (mainform in activeGroup.were_mainforms)) {
        // update records
        delete activeGroup.ngraminfo[mainform].origin
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
        activeGroup.ngraminfo
     )
     // and update
     MyTable.data('dynatable').dom.update();
}


function removeSubform(ngramId) {
    $('#active-subform-'+ngramId).remove()
    if (activeGroup.now_links.length == 1) {
        removeActiveGroupFrame()
    }
    else {
        // clean were_mainforms dict
        delete activeGroup.were_mainforms[ngramId]

        // clean now_links array
        var i = activeGroup.now_links.indexOf(ngramId)
        activeGroup.now_links.splice(i,1)

        // if (activeGroup.ngraminfo[ngramId].origin == 'new') {
        //     AjaxRecords[ngramId].state = 0 ;
        // }

        // redraw active group_box_content
        drawActiveGroup(
            '#group_box',
            activeGroup.now_mainform_id,
            activeGroup.now_links,
            activeGroup.ngraminfo
         )
         // and update
         MyTable.data('dynatable').dom.update();
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
    // ngraminfo = standard info of records + 'origin' property
    activeGroup.ngraminfo = {}
    activeGroup.ngraminfo[mainFormNgramId] = AjaxRecords[mainFormNgramId] ;
    activeGroup.ngraminfo[mainFormNgramId]['origin'] = 'new' ;

    // add relevant information from old & new links to activeGroup.now_links
    updateActiveGroupInfo (mainFormNgramId, false)

    // groupBox rendering
    drawActiveGroup(
        '#group_box',
        activeGroup.now_mainform_id,
        activeGroup.now_links,
        activeGroup.ngraminfo
     )

     MyTable.data('dynatable').dom.update();
}


// add new ngramid (and any present subforms) to currently modified group
function add2group ( ngramId ) {

    // console.log("FUN add2group(" + AjaxRecords[ngramId].name + ")")

    var toOther = true ;
    activeGroup.were_mainforms[ngramId] = true ;

    if (GState == 1) {

        // add this mainform as a new subform
        activeGroup.now_links.push(ngramId)
        activeGroup.ngraminfo[ngramId] = AjaxRecords[ngramId]
        activeGroup.ngraminfo[ngramId].origin = 'new'

        // also add all its subforms as new subforms
        updateActiveGroupInfo (ngramId, toOther)

        // redraw active group_box_content
        drawActiveGroup(
            '#group_box',
            activeGroup.now_mainform_id,
            activeGroup.now_links,
            activeGroup.ngraminfo
         )

         MyTable.data('dynatable').dom.update();
     }
     else {
         console.warn("ADD2GROUP but no active group")
     }

}

/**
 * subforms from DB have their info in a separate NGrams.group.nodesmemory
 *  so here and in saveActiveGroup we need to take it into account
 *
 * TODO: remove this mecanism
 *
 * @param ngramId
 * @param toOtherMainform = flag if ngram was a subform of another mainform
 * @param (global) activeGroup = current state struct of modify group dialog
 */
function updateActiveGroupInfo (ngramId, toOtherMainform) {
    // console.log("FUN updateActiveGroupInfo(" + AjaxRecords[ngramId].name + ")")
    // console.log(activeGroup)

    // fill active link info
    if( ngramId in NGrams.group.links ) {
        for (var i in NGrams.group.links[ngramId]) {
            var subId = NGrams.group.links[ngramId][i] ;
            // ----------- old links (already in DB)
            activeGroup.now_links.push(subId)
            activeGroup.ngraminfo[subId] = NGrams.group.nodesmemory[subId]
            activeGroup.ngraminfo[subId].origin = toOtherMainform ? 'oldnew' : 'old'
        }
    }
    if( ngramId in GroupsBuffer ) {
        for(var i in GroupsBuffer[ ngramId ] ) {
            var subId = GroupsBuffer[ ngramId ][i] ;
            // ----------- new links (not in DB)
            activeGroup.now_links.push(subId)
            activeGroup.ngraminfo[subId] = AjaxRecords[subId]
            activeGroup.ngraminfo[subId].origin = 'new'
        }
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
    // (if previously had add2group button clicked)
    if(GState==1 ) {
        if(ngram_info.state!=System[0]["statesD"]["delete"] && ! GroupsBuffer[ngramId]) { // if deleted and already group, no Up button
            plus_event  = '<span class="note glyphicon glyphicon-plus"'
            plus_event +=      ' color="#FF530D"'
            plus_event +=      ' onclick="add2group('+ ngramId +')"></span>'
        }
    }

    // -------------------------------------------
    //         score and name column cells
    // -------------------------------------------

    // <td> score </td>              atts.id (ex: "normal" or "delete" etc)
    result["score"] = '<span class="'+atts.id+'">'+ngram_info["score"]+'</span>\n'

    // <td> name  </td>     aka   "ngrambox"
    result["name"]  = '<div class="ngrambox" id="box-'+ngramId+'">\n'
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
      console.log('/!\\ nothing for ' + record.id)
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

  $("tbody tr").each(function (i, row) {
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

$("#Save_All").click(function(){
    SaveLocalChanges()
});


// MAIN SAVE + MAIN CREATE TABLE
// -----------------------------

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
    if( NGrams["map"][ id ] ) {
      if(AjaxRecords[id]["state"]==System[0]["statesD"]["normal"] || AjaxRecords[id]["state"]==System[0]["statesD"]["delete"]) {
        FlagsBuffer["outmap"][ id ] = true
        if(AjaxRecords[id]["state"]==System[0]["statesD"]["delete"]) {
          FlagsBuffer["delete"][id] = true
        }
      }
      if(GroupsBuffer[id] && AjaxRecords[id]["state"]==System[0]["statesD"]["keep"])  {
        FlagsBuffer["inmap"][ id ] = true
      }
    } else {
      if(AjaxRecords[id]["state"]==System[0]["statesD"]["keep"]) {
        FlagsBuffer["inmap"][ id ] = true
      }
      if(AjaxRecords[id]["state"]==System[0]["statesD"]["delete"]) {
        FlagsBuffer["delete"][id] = true
      }
    }
  }
  // [ = = = = For deleting subforms = = = = ]

  for(var i in NGrams["group"].links) {
    // i is ngram_id of a group mainNode
    if(FlagsBuffer["delete"][i]) {
      for(var j in NGrams["group"].links[i] ) {
        FlagsBuffer["delete"][NGrams["group"].links[i][j]] = true
      }
      for(var j in FlagsBuffer["delete"][i] ) {
        FlagsBuffer["delete"][FlagsBuffer["delete"][i][j]] = true
      }
    }
    if(FlagsBuffer["inmap"][i]) {
      for(var j in GroupsBuffer[i] ) {
        FlagsBuffer["outmap"][GroupsBuffer[i][j]] = true
      }
    }
  }
  // [ = = = = / For deleting subforms = = = = ]

  // console.log(" = = = = = = = = = == ")
  // console.log("FlagsBuffer:")
  // console.log(JSON.stringify(FlagsBuffer))


  var nodes_2del = Object.keys(FlagsBuffer["delete"]).map(Number)  // main => stop
  var nodes_2keep = Object.keys(FlagsBuffer["keep"]).map(Number)   // ??? stop => main ???
  var nodes_2group = $.extend({}, GroupsBuffer)
  var nodes_2inmap = $.extend({}, FlagsBuffer["inmap"])     //  add to map
  var nodes_2outmap = $.extend({}, FlagsBuffer["outmap"])   //  remove from map

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

  // retrieve node_ids from hidden input
  var mainlist_id = $("#mainlist_id").val()
  var maplist_id  = $("#maplist_id" ).val()
  var stoplist_id = $("#stoplist_id" ).val()
  var groupnode_id = $("#groups_id" ).val()

  // var corpus_id = getIDFromURL( "corpora" )

  $("#stoplist_content").html()

  // The AJAX CRUDs in cascade:

  $("#Save_All").append('<img width="8%" src="/static/img/ajax-loader.gif"></img>')

  // chained CRUD calls
  CRUD_1_AddMap()

  // add some ngrams to maplist
  function CRUD_1_AddMap() {
    console.log("===> AJAX CRUD1 AddMap <===\n") ;
    CRUD( maplist_id , Object.keys(nodes_2inmap), "PUT" , function(success) {
      if (success) {
        CRUD_2_RmMap()             // chained AJAX  1 -> 2
      }
      else {
        console.warn('CRUD error on ngrams add to maplist ('+maplist_id+')')
      }
    });
  }
  // remove some ngrams from maplist
  function CRUD_2_RmMap() {
    console.log("===> AJAX CRUD2 RmMap <===\n") ;
    CRUD( maplist_id , Object.keys(nodes_2outmap), "DELETE" , function(success) {
      if (success) {
        CRUD_3_AddStopRmMain()    // chained AJAX  2 -> 3
      }
      else {
        console.warn('CRUD error on ngrams remove from maplist ('+maplist_id+')')
      }
    });
  }

  // 2 operations going together: add ngrams to stoplist and remove them from mainlist
  function CRUD_3_AddStopRmMain() {
    console.log("===> AJAX CRUD3a+b AddStopRmMain <===\n") ;
    CRUD( stoplist_id , nodes_2del, "PUT" , function(success) {
      if (success) {
        // console.log("OK CRUD 3a add stop")
        CRUD( mainlist_id , nodes_2del, "DELETE" , function(success) {
          if (success) {
            // console.log("OK CRUD 3b rm main")
            CRUD_4()              // chained AJAX  3 -> 4
          }
          else {
            console.warn('CRUD error on ngrams remove from mainlist ('+mainlist_id+')')
          }
        });
      }
      else {
        console.warn('CRUD error on ngrams add to stoplist ('+stoplist_id+')')
      }
    });
  }

  // add to groups reading data from GroupsBuffer
  function CRUD_4() {
      console.log("===> AJAX CRUD4 RewriteGroups <===\n") ;
      GROUPCRUD(groupnode_id, GroupsBuffer, function(success) {
          if (success) {
              window.location.reload() // all 4 CRUDs OK => refresh whole page
          }
          else {
              console.warn('CRUD error on ngrams add to group node ('+groupings_id+')')
          }
      }) ;
  }
}    // end of SaveLocalChanges


// For list modifications (add/delete), all http-requests
function CRUD( list_id , ngram_ids , http_method , callback) {
    // ngramlists/change?node_id=42&ngram_ids=1,2
    var the_url = window.location.origin+"/api/ngramlists/change?list="+list_id+"&ngrams="+ngram_ids.join(",");

    // debug
    // console.log("  ajax target: " + the_url + " (" + http_method + ")")

    if(ngram_ids.length>0) {
        $.ajax({
          method: http_method,
          url: the_url,
            //    data: args,   // currently all data explicitly in the url (like a GET)
          beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          },
          success: function(data){
                console.log("-- CRUD ----------")
                console.log(http_method + " ok!!")
                console.log(JSON.stringify(data))
                console.log("------------------")
                callback(true);
          },
          error: function(result) {
              console.log("-- CRUD ----------")
              console.log("AJAX Error on " + http_method + " " + the_url);
              console.log(result)
              console.log("------------------")
              callback(false);
          }
        });

    } else callback(true);
}


// For group modifications (POST: {mainformA: [subformsA1,A2,A3], mainformB:..})
function GROUPCRUD( groupnode_id , post_data , callback) {
    // ngramlists/change?node_id=42&ngram_ids=1,2
    var the_url = window.location.origin+"/api/ngramlists/groups?node="+groupnode_id;

    // debug
    // console.log("  ajax target: " + the_url + " (" + http_method + ")")

    $.ajax({
      method: 'POST',
      url: the_url,
      data: post_data,  // currently all data explicitly in the url (like a GET)
      beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
      },
      success: function(data){
            console.log("-- GROUPCRUD ----------")
            console.log("POST ok!!")
            console.log(JSON.stringify(data))
            console.log("-----------------------")
            callback(true);
      },
      error: function(result) {
          console.log("-- GROUPCRUD ----------")
          console.log("AJAX Error on POST " + the_url);
          console.log(result)
          console.log("-----------------------")
          callback(false);
      }
    });

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
function MainTableAndCharts( data , initial , search_filter) {

    // debug
    // alert("refresh main")

    console.log("")
    console.log(" = = = = MainTableAndCharts: = = = = ")
    console.log("data:")
    console.log(data)
    console.log("initial:")   //
    console.log(initial)
    console.log("search_filter:")        // eg 'filter_all'
    console.log(search_filter)
    console.log(" = = = = / MainTableAndCharts: = = = = ")
    console.log("")

    // Expected infos in "data.ngrams" should have the form:
    // { "1": { id: "1", name: "réalité",        score: 36  },
    //   "9": { id: "9", name: "pdg",            score: 116 },
    //  "10": { id:"10", name: "infrastructure", score:  12 }  etc. }

    // (see filling of rec_info below)
    // console.log(data.ngrams)

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

      // uncomment for column ngramId (here and in transformContent - l.577)
      // div_table += "\t"+"\t"+'<th data-dynatable-column="ngramId" style="background-color:grey">ngramId</th>'+"\n";

      // uncomment for column stateId (here and in transformContent - l.580)
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
                            + 'Del'
                            + '<p class="note">'
                            + '<input type="checkbox" id="delAll"'
                            + ' onclick="SelectPage(\'delete\',this)" title="Check to select all currently visible terms"></input>'
                            + '<label>All</label>'
                            + '</p>'
                            + '</th>'+"\n" ;
      // main name and score columns
      div_table += "\t"+"\t"+'<th data-dynatable-column="name">Terms</th>'+"\n";
      div_table += "\t"+"\t"+'<th id="score_column_id" data-dynatable-sorts="score" data-dynatable-column="score">Score</th>'+"\n";
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

    var div_stats = "<p>";
    for(var i in data.scores) {
      var value = (!isNaN(Number(data.scores[i])))? Number(data.scores[i]).toFixed(1) : data.scores[i];
      div_stats += i+": "+value+" | "
    }
    div_stats += "</p>"
    $("#stats").html(div_stats)

    AjaxRecords = {}

    for(var id in data.ngrams) {

      // console.log(i)
      // console.log(data.ngrams[i])
      var le_ngram = data.ngrams[id] ;

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
        "group_exists": (le_ngram.id in NGrams.group.links || le_ngram.id in GroupsBuffer),
      }
      // AjaxRecords.push(rec_info)
      AjaxRecords[id] = rec_info

      if ( ! DistributionDict[rec_info.score] ) DistributionDict[rec_info.score] = 0;
      DistributionDict[rec_info.score]++;
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
                // console.log("lalaal moveChart.focus(chartfilt);")
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

    // test if array is enough to restore proper page range
    var ArrayAjaxRecords = [] ;
    var i = 0 ;
    var idmap = {}
    for (ngid in AjaxRecords) {
        ArrayAjaxRecords.push(AjaxRecords[ngid]) ;
        i ++ ;
        idmap[ngid] = i
    }

    MyTable = []
    MyTable = $('#my-ajax-table').dynatable({
                dataset: {
                  records: ArrayAjaxRecords
                },
                features: {
                  pushState: false,
                  // sort: false //i need to fix the sorting function... the current one just sucks
                },
                writers: {
                  _rowWriter: ulWriter
                  // _cellWriter: customCellWriter
                },
                inputs: {
                    queries: $('select#testquery'),
                    queries: $('select#picklistmenu'),
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
    MyTable.data('dynatable').process();

    // hook on page change
    MyTable.bind('dynatable:page:set', tidyAfterPageSetUpdate)

    // hook on any type of update
    MyTable.bind('dynatable:afterUpdate', tidyAfterUpdate)

    // // // $("#score_column_id").children()[0].text = FirstScore
    // // // // MyTable.data('dynatable').process();

    // bind a filter named 'my_state_filter' to dynatable.queries.functions
    MyTable.data('dynatable').queries
        // selects on current state <=> shows only elements of specific list
        // nb: possible value are in {0,1,2} (see terms.html > #picklistmenu)
        .functions['my_state_filter'] = function(record,selectedValue) {
            if (selectedValue == 'reset') {
                return (AjaxRecords[record.id].state >= 0)
            }
            else {
                // return true or false
                return (AjaxRecords[record.id].state == selectedValue)
            }
        }

    // and set this filter's initial status to 'maplist' (aka state == 1)
    MyTable.data('dynatable').settings.dataset.queries['my_state_filter'] = 1 ;
    MyTable.data('dynatable').process();

    // moves pagination over table
    if ( $(".imadiv").length>0 ) return 1;
    $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
    $(".dynatable-record-count").insertAfter(".imadiv")
    $(".dynatable-pagination-links").insertAfter(".imadiv")

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
            callback(data);
        },
        error: function(exception) {
            callback(false);
        }
    })
}

// ######################### AJAX && INIT #########################


// [ = = = = = = = = = = INIT = = = = = = = = = = ]
// http://localhost:8000/api/node/84592/ngrams?format=json&score=tfidf,occs&list=miam
var corpus_id = getIDFromURL( "corpora" )
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




// NEW AJAX x 2

var prefetch_url = window.location.origin+"/api/ngramlists/maplist?corpus="+corpus_id ;
var new_url = window.location.origin+"/api/ngramlists/family?corpus="+corpus_id ;

// faster call: just the maplist, will return first
GET_(prefetch_url, HandleAjax);

// longer call (full list of terms) to return when ready and refresh all data
GET_(new_url, HandleAjax)

function HandleAjax(res) {
    if (res && res.ngraminfos) {

        main_ngrams_objects = {}
        for (var ngram_id in res.ngraminfos) {
            var ngram_tuple = res.ngraminfos[ngram_id]
            main_ngrams_objects[ngram_id] = {
                'id' : ngram_id,         // redundant but for backwards compat
                'name' : ngram_tuple[0],
                'score' : ngram_tuple[1]
            }
        }

        console.log("===> AJAX INIT <===\n" + "source: " + new_url)

        // = = = = MIAM = = = = //
        NGrams["main"] = {
            "ngrams": main_ngrams_objects,
              "scores": {
                "initial":"occs",
                "nb_ngrams":Object.keys(main_ngrams_objects).length,
            }
        } ;

        // = = MAP ALSO STOP = = //
        // 2x(array of ids) ==> 2x(lookup hash)
        NGrams["map"] = {} ;
        for (var i in res.listmembers.maplist) {
            var map_ng_id = res.listmembers.maplist[i] ;
            NGrams["map"][map_ng_id] = true ;
        }

        NGrams["stop"] = {} ;
        for (var i in res.listmembers.stoplist) {
            var stop_ng_id = res.listmembers.stoplist[i] ;
            NGrams["stop"][stop_ng_id] = true ;
        }

        // = = = = GROUP = = = = //
        NGrams["group"] = {
            "links" : res.links ,
            // "nodesmemory" will be filled from "links" in AfterAjax()
            "nodesmemory" : {}
        };

    }
    // console.log('after init NGrams["main"].ngrams')
    // console.log(NGrams["main"].ngrams)

    // cache all DB node_ids
    $("input#mainlist_id").val(res.nodeids['mainlist'])
    $("input#maplist_id" ).val(res.nodeids['maplist'])
    $("input#stoplist_id").val(res.nodeids['stoplist'])
    $("input#groups_id").val(res.nodeids['groups'])
    $("input#scores_id").val(res.nodeids['scores'])
    AfterAjax() ;
}

function AfterAjax() {
  // -------------------------------------------------------------------
  // console.log(JSON.stringify(NGrams))
  // -------------------------------------------------------------------

    // Deleting subforms from the ngrams-table, clean start baby!
    if( Object.keys(NGrams["group"].links).length>0 ) {

        // subforms inventory {  "main":{ all mainform ids } , "sub":{ all subform ids}  }
        var _forms = {  "main":{} , "sub":{}  }
        for(var ngramId in NGrams["group"].links) {
            _forms["main"][ngramId] = true
            for(var i in NGrams["group"].links[ngramId]) {
                var subformId = NGrams["group"].links[ngramId][i]
                // for each subform: true
                _forms["sub"][ subformId ] = true
            }
        }

        // debug:
        // console.log('~~~~~~~~~~~~~> (sub) _forms')
        // console.log( _forms )

        // ------------------------------------------- MAINLIST
        // ngrams_data_ will update NGrams.main.ngrams (with subforms removed)
        var ngrams_data_ = {}
        for(var ngram_id in NGrams["main"].ngrams) {

            // if ngram is subform of another
            if(_forms["sub"][ngram_id]) {
                // move subform info into NGrams.group.nodesmemory
                // ------------------------------------------
                // (subform goes away from new list but info preserved)
                // (useful if we want to see/revive subforms in future)
                NGrams.group.nodesmemory[ngram_id] = NGrams["main"].ngrams[ngram_id]

                // debug:
                // console.log(ngram_id + " ("+NGrams["main"].ngrams[ngram_id].name+") is a subform")
            }
            // normal case
            else {
                // we keep the info untouched in the new obj
                ngrams_data_[ngram_id] = NGrams["main"].ngrams[ngram_id]
            }
        }

        // the new hash of ngrams replaces the old main
        NGrams["main"].ngrams = ngrams_data_;
    }

    // NB: this miamlist will eventually become AjaxRecords
    // debug:
    // console.log('NGrams["main"]')
    // console.log( NGrams["main"] )


    // ----------------------------------------- MAPLIST
    if( Object.keys(NGrams["map"]).length>0 ) {
        for(var ngram_id in NGrams["main"].ngrams) {
            myMiamNgram = NGrams["main"].ngrams[ngram_id]
            if(NGrams["map"][ngram_id]) {
                // keepstateId = 1
                keepstateId = System[0]["statesD"]["keep"]

                // initialize state of maplist items
                myMiamNgram["state"] = keepstateId ;
            }
        }
    }

    // Building the Score-Selector //NGrams["scores"]
    var FirstScore = NGrams["main"].scores.initial
    // TODO scores_div
    //       Recreate possible_scores from some constants (tfidf, occs)
    //       and not from ngrams[0], to keep each ngram's info smaller

    // var possible_scores = Object.keys( NGrams["main"].ngrams[0].scores );
    // var scores_div = '<br><select style="font-size:25px;" class="span1" id="scores_selector">'+"\n";
    // scores_div += "\t"+'<option value="'+FirstScore+'">'+FirstScore+'</option>'+"\n"
    // for( var i in possible_scores ) {
    //   if(possible_scores[i]!=FirstScore) {
    //     scores_div += "\t"+'<option value="'+possible_scores[i]+'">'+possible_scores[i]+'</option>'+"\n"
    //   }
    // }

    // Initializing the Charts and Table ---------------------------------------
    var result = MainTableAndCharts( NGrams["main"] , FirstScore , "filter_all")
    console.log( result ) // OK
    // -------------------------------------------------------------------------

    // see TODO scores_div
    // Listener for onchange Score-Selector
    // scores_div += "<select>"+"\n";
    // $("#ScoresBox").html(scores_div)
    // $("#scores_selector").on('change', function() {
    //   console.log( this.value )
    //   var result = MainTableAndCharts( NGrams["main"] , this.value , "filter_all")
    //   console.log( result )
    //
    // });

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
