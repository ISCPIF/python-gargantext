

//============================ < NEW BUTTONS > =============================//

function changeType() {
    pr("***swclickActual:"+swclickActual+" , swMacro:"+swMacro);
    
    if(swclickActual=="social") {
        if(swMacro) {
            changeToMacro("semantic");
	        pushSWClick("semantic");
	        RefreshState("B")
        } else {
            //From soc* to SocSem
            if(is_empty(selections)) {
                //soc to SocSem
                changeToMacro("semantic");
                pushSWClick("semantic");
                RefreshState("B")

            } else {
                //soc* to SocSem
                changeToMeso("sociosemantic");
                pushSWClick("sociosemantic");
                RefreshState("AaBb")
            }
        }
        return;
    }

    if(swclickActual=="semantic") {
        if(swMacro) {
        	changeToMacro("social");
	        pushSWClick("social");
	        RefreshState("A");

        } else {

            if(is_empty(selections)) {
                changeToMacro("social");
                pushSWClick("social");
                RefreshState("A");
            } else {
                changeToMeso("sociosemantic");
                pushSWClick("sociosemantic");
                RefreshState("AaBb");
            }
        }
        return;
    }

    if(swclickActual=="sociosemantic") {

    	if(swMacro) {
    		changeToMacro("sociosemantic");
	        pushSWClick("sociosemantic");
	        RefreshState("AaBb")
    	} else {

            if(is_empty(selections)) {
                changeToMacro(swclickPrev);
                pushSWClick(swclickPrev);
                RefreshState(PAST.toUpperCase())
            } else {
              //there is an active selection
                //identify type of the current-selection
                var countTypes = {};
                for(var i in selections) {
                    if( isUndef(countTypes[Nodes[i].type]) )
                        countTypes[Nodes[i].type]=1;
                    else
                        countTypes[Nodes[i].type]++;
                }
                pr("bigraph #selectionsTypes: ")
                pr(countTypes)


                cpCountTypes = Object.keys(countTypes);
                if(cpCountTypes.length==1) {

                    if(cpCountTypes[0]==catSoc) {
                        pushSWClick("social");
                        changeToMeso("social");
                        RefreshState("a");

                    } else {
                        pushSWClick("semantic");
                        changeToMeso("semantic");
                        RefreshState("b");
                    }

                } else {
                  //there is a selection with both kind of nodes
                    //Manually changing the selection, not using MultipleSelection
                    var ndsids = [];
                    for(var i in selections) {
                        if( Nodes[i].type == catSoc )
                            ndsids.push(i);
                    }
                    cancelSelection(false);
                    for(var i in ndsids){
                        nodeid = ndsids[i]
                        getOpossitesNodes(nodeid,false); //false -> just nodeid
                    }
                    pushSWClick("social");
                    changeToMeso("social");
                    RefreshState("a");

                }

            }
    	}

        return;
    }
}

function changeLevel() {
    bf=swclickActual
    pushSWClick(swclickActual);
    pr("swMacro: "+swMacro+" - [swclickPrev: "+bf+"] - [swclickActual: "+swclickActual+"]")

    if(swMacro){
        // Macro Level  --  swMacro:true
	    if(swclickActual=="social") {
	    	changeToMeso("social")
	    	RefreshState("a");
	    }
	    if(swclickActual=="semantic") {
	    	changeToMeso("semantic")
	    	RefreshState("b");
	    }
	    swMacro=false;
        return;

	} else {
        // Meso Level  --  swMacro:false
	    if(swclickActual=="social") {
	    	changeToMacro("social")
	    	RefreshState("A")
	    }
	    if(swclickActual=="semantic") {
	    	changeToMacro("semantic")
	    	RefreshState("B")
	    }
	    swMacro=true;
        return;
	}

}


//============================= </ NEW BUTTONS > =============================//







//=========================== < FILTERS-SLIDERS > ===========================//


//    Execution modes:
//	EdgeWeightFilter("#sliderAEdgeWeight", "label" , "nodes1", "weight");
//	EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
function EdgeWeightFilter(sliderDivID , type_attrb , type ,  criteria) {

	if ($(sliderDivID).html()!="") {
		pr("\t\t\t\t\t\t[[ algorithm not applied "+sliderDivID+" ]]")
		return;
	}

	// sliderDivID = "#sliderAEdgeWeight"
	// type = "nodes1"
	// type_attrb = "label"
	// criteria = "weight"

	// sliderDivID = "#sliderBNodeSize"
	// type = "NGram"
	// type_attrb = "type"
	// criteria = "size"

    if(partialGraph._core.graph.edges.length==0) {

        $(sliderDivID).freshslider({
            range: true,
            step:1,
            value:[10, 60],
            enabled: false,
            onchange:function(low, high){
                console.log(low, high);
            }
        });

        return;
    }

    var filterparams = AlgorithmForSliders ( partialGraph._core.graph.edges , type_attrb , type , criteria) 
    var steps = filterparams["steps"]
    var finalarray = filterparams["finalarray"]
    

    var lastvalue=("0-"+(steps-1));

    pushFilterValue( sliderDivID , lastvalue )

    //finished
    $(sliderDivID).freshslider({
        range: true,
        step: 1,
        min:0,
        bgcolor: (type=="nodes1")?"#27c470":"#FFA500" ,
        max:steps-1,
        value:[0,steps-1],
        onchange:function(low, high) {

            var filtervalue = low+"-"+high

            if(filtervalue!=lastFilter[sliderDivID]) {

                $.doTimeout(sliderDivID+"_"+lastFilter[sliderDivID]);

                $.doTimeout( sliderDivID+"_"+filtervalue,300,function () {

                    pr("\nprevious value "+lastvalue+" | current value "+filtervalue)

                    // [ Stopping FA2 ]
                    partialGraph.stopForceAtlas2();
                    // [ / Stopping FA2 ]

                    var t0 = lastvalue.split("-")
                    var mint0=parseInt(t0[0]), maxt0=parseInt(t0[1]), mint1=parseInt(low), maxt1=parseInt(high);
                    var addflag = false;
                    var delflag = false;

                    var iterarr = []


                    if(mint0!=mint1) {
                        if(mint0<mint1) {
                            delflag = true;
                            pr("cotainferior   --||>--------||   a la derecha")
                        }
                        if(mint0>mint1) {
                            addflag = true;
                            pr("cotainferior   --<||--------||   a la izquierda")
                        }
                        iterarr = calc_range(mint0,mint1).sort(compareNumbers);
                    }

                    if(maxt0!=maxt1) {
                        if(maxt0<maxt1) {
                            addflag = true;
                            pr("cotasuperior   ||--------||>--   a la derecha")
                        }
                        if(maxt0>maxt1) {
                            delflag = true;
                            pr("cotasuperior   ||--------<||--   a la izquierda")
                        }
                        iterarr = calc_range(maxt0,maxt1).sort(compareNumbers);
                    }

                    // do the important stuff
                    for( var c in iterarr ) {
                        
                        var i = iterarr[c];
                        ids = finalarray[i]

                        if(i>=low && i<=high) {
                            if(addflag) {
                                // pr("adding "+ids.join())
                                for(var id in ids) {                            
                                    ID = ids[id]
                                    Edges[ID].lock = false;

                                    if(swMacro) {
                                        add1Edge(ID)
                                    } else {
                                        for (var n in partialGraph._core.graph.nodesIndex) {
                                            sid = Edges[ID].sourceID
                                            tid = Edges[ID].targetID
                                            if (sid==n || tid==n) {
                                                if(isUndef(getn(sid))) unHide(sid)
                                                if(isUndef(getn(tid))) unHide(tid)
                                                add1Edge(ID)
                                                // pr("\tADD "+ID)
                                            }
                                        }
                                    }
                                    
                                }
                            }

                        } else {
                            if(delflag) {
                                // pr("deleting "+ids.join())
                                for(var id in ids) {
                                    ID = ids[id]
                                    if(!isUndef(gete(ID)))
                                        partialGraph.dropEdge(ID)
                                    Edges[ID].lock = true;
                                    // pr("\tDEL "+ID)
                                    // pr("removeedge")
                                }
                            }
                        }
                    }

                    if (!is_empty(selections))
                        DrawAsSelectedNodes(selections)


                    partialGraph.refresh()
                    partialGraph.draw()

                    // [ Starting FA2 ]
                    $.doTimeout(30,function(){
                        fa2enabled=true; partialGraph.startForceAtlas2();
                        if(filtervalue.charAt(0)=="0") partialGraph.stopForceAtlas2();
                    });
                    // [ / Starting FA2 ]

                    pr("\t\t\tfilter applied!")

                    lastvalue = filtervalue;
                });
                pushFilterValue( sliderDivID , filtervalue )
            }
            
        }
    });
}



//   Execution modes:
// NodeWeightFilter ( "#sliderANodeWeight" ,  "Document" , "type" , "size") 
// NodeWeightFilter ( "#sliderBNodeWeight" ,  "NGram" , "type" , "size") 
function NodeWeightFilter(sliderDivID , type_attrb , type ,  criteria) {

	if ($(sliderDivID).html()!="") {
		pr("\t\t\t\t\t\t[[ algorithm not applied "+sliderDivID+" ]]")
		return;
	}

	// sliderDivID = "#sliderAEdgeWeight"
	// type = "nodes1"
	// type_attrb = "label"
	// criteria = "weight"

	// sliderDivID = "#sliderBNodeSize"
	// type = "NGram"
	// type_attrb = "type"
	// criteria = "size"

    if(partialGraph._core.graph.nodes.length==0) {

        $(sliderDivID).freshslider({
            range: true,
            step:1,
            value:[10, 60],
            enabled: false,
            onchange:function(low, high){
                console.log(low, high);
            }
        });

        return;
    }

    var filterparams = AlgorithmForSliders ( partialGraph._core.graph.nodes , type_attrb , type , criteria) 
    var steps = filterparams["steps"]
    var finalarray = filterparams["finalarray"]
    
    //finished
    $(sliderDivID).freshslider({
        range: true,
        step: 1,
        min:0,
        max:steps-1,
        bgcolor:(type_attrb=="Document")?"#27c470":"#FFA500" ,
        value:[0,steps-1],
        onchange:function(low, high){    
            var filtervalue = low+"-"+high
            
            if(filtervalue!=lastFilter[sliderDivID]) {
                if(lastFilter[sliderDivID]=="-") {
                    pushFilterValue( sliderDivID , filtervalue )
                    return false
                }

                // [ Stopping FA2 ]
                partialGraph.stopForceAtlas2();
                // [ / Stopping FA2 ]

                for(var i in finalarray) {
                    ids = finalarray[i]
                    if(i>=low && i<=high){
                        for(var id in ids) {
                            ID = ids[id]
                            Nodes[ID].lock = false;
                            if(partialGraph._core.graph.nodesIndex[ID])
                                partialGraph._core.graph.nodesIndex[ID].hidden = false;
                        }
                    } else {
                        for(var id in ids) {
                            ID = ids[id]
                            Nodes[ID].lock = true;
                            if(partialGraph._core.graph.nodesIndex[ID])
                                partialGraph._core.graph.nodesIndex[ID].hidden = true;
                        }                     
                    }
                }
                pushFilterValue(sliderDivID,filtervalue)

                if (!is_empty(selections))
                    DrawAsSelectedNodes(selections)

                partialGraph.refresh()
                partialGraph.draw()

                // [ Starting FA2 ]
                $.doTimeout(30,function(){
                    fa2enabled=true; partialGraph.startForceAtlas2()
                    if(filtervalue.charAt(0)=="0") partialGraph.stopForceAtlas2();
                });
                // [ / Starting FA2 ]
            }
            
        }
    });
}

//   Execution modes:
// AlgorithmForSliders ( partialGraph._core.graph.edges , "label" , "nodes1" , "weight") 
// AlgorithmForSliders ( partialGraph._core.graph.edges , "label" , "nodes2" , "weight") 
// AlgorithmForSliders ( partialGraph._core.graph.nodes , "type" ,  "Document" ,  "size") 
// AlgorithmForSliders ( partialGraph._core.graph.nodes , "type" ,  "NGram" ,  "size") 
function AlgorithmForSliders( elements , type_attrb , type , criteria) {
	// //  ( 1 )
    // // get visible sigma nodes|edges
    elems=elements.filter(function(e) {
                return e[type_attrb]==type;
    });

    // //  ( 2 )
    // // extract [ "edgeID" : edgeWEIGHT ] | [ "nodeID" : nodeSIZE ] 
    // // and save this into edges_weight | nodes_size
    var elem_attrb=[]
    for (var i in elems) {
        e = elems[i]
        id = e.id
        elem_attrb[id]=e[criteria]
        // pr(id+"\t:\t"+e[criteria])
    }
    // pr("{ id : size|weight } ")
    // pr(elem_attrb)

    // //  ( 3 )
    // // order dict edges_weight by edge weight | nodes_size by node size
    var result = ArraySortByValue(elem_attrb, function(a,b){
        return a-b
        //ASCENDENT
    });

    // pr("result: ")
    // pr(result)
    // pr(result.length)
    // // ( 4 )
    // // printing ordered ASC by weigth
    // for (var i in result) {
    //     r = result[i]
    //     idid = r.key
    //     elemattrb = r.value
    //     pr(idid+"\t:\t"+elemattrb)
    //     // e = result[i]
    //     // pr(e[criteria])
    // }
    var N = result.length
    // var magnitude = (""+N).length //order of magnitude of edges|nodes
    // var exponent = magnitude - 1
    // var steps = Math.pow(10,exponent) //    #(10 ^ magnit-1) steps
    // var stepsize = Math.round(N/steps)// ~~(visibledges / #steps)


    //var roundsqrtN = Math.round( Math.sqrt( N ) );
    var steps =  Math.round( Math.sqrt( N ) );
    var stepsize = Math.round( N / steps );

    // pr("-----------------------------------")
    // pr("number of visible nodes|edges: "+N); 
    
    // pr("number of steps : "+steps)
    // pr("size of one step : "+stepsize)
    // pr("-----------------------------------")
    

    var finalarray = []
    var counter=0
    for(var i = 0; i < steps*2; i++) {
        // pr(i)
        var IDs = []
        for(var j = 0; j < stepsize; j++)  {
            if(!isUndef(result[counter])) {
                k = result[counter].key
                // w = result[counter].value
                // pr("\t["+counter+"] : "+w)
                IDs.push(k)
            }
            counter++;
        }
        if(IDs.length==0) break;
        finalarray[i] = IDs
    }
    // pr("finalarray: ")
    return {"steps":finalarray.length,"finalarray":finalarray}
}

//=========================== </ FILTERS-SLIDERS > ===========================//




//============================= < SEARCH > =============================//
function updateSearchLabels(id,name,type){    
    labels.push({
        'id' : id,
        'label' : name, 
        'desc': type
    });
}

function extractContext(string, context) {
    var matched = string.toLowerCase().indexOf(context.toLowerCase());

    if (matched == -1) 
        return string.slice(0, 20) + '...';

    var begin_pts = '...', end_pts = '...';

    if (matched - 20 > 0) {
        var begin = matched - 20;
    } else {
        var begin = 0;
        begin_pts = '';
    }

    if (matched + context.length + 20 < string.length) {
        var end = matched + context.length + 20;
    } else {
        var end = string.length;
        end_pts = '';
    }

    str = string.slice(begin, end);

    if (str.indexOf(" ") != Math.max(str.lastIndexOf(" "), str.lastIndexOf(".")))
        str = str.slice(str.indexOf(" "), Math.max(str.lastIndexOf(" "), str.lastIndexOf(".")));

    return begin_pts + str + end_pts;
}

function searchLabel(string){    
    var id_node = '';
    var n;
    
    nds = partialGraph._core.graph.nodes.filter(function(x){return !x["hidden"]});
    for(var i in nds){
        n = nds[i]
            if (n.label == string) {
                return n;
            }
    }
}

function search(string) {
    var id_node = '';
    var results = find(string)

    var coincd=[]
    for(var i in results) {
        coincd.push(results[i].id)
    }    
    $.doTimeout(30,function (){
        MultipleSelection(coincd , true);
        $("input#searchinput").val("");
        $("input#searchinput").autocomplete( "close" );
    });
}

//============================ < / SEARCH > ============================//
