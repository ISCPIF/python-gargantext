

function cancelSelection (fromTagCloud) {
    pr("\t***in cancelSelection");
    highlightSelectedNodes(false); //Unselect the selected ones :D
    opossites = [];
    selections = [];
    //selections.length = 0;
    selections.splice(0, selections.length);
    partialGraph.refresh();
    
    
    //Nodes colors go back to normal
    overNodes=false;
    e = partialGraph._core.graph.edges;
    for(i=0;i<e.length;i++){
            e[i].color = e[i].attr['grey'] ? e[i].attr['true_color'] : e[i].color;
            e[i].attr['grey'] = 0;
    }
    partialGraph.draw(2,1,2);
                
    partialGraph.iterNodes(function(n){
            n.active=false;
            n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
            n.attr['grey'] = 0;
    }).draw(2,1,2);
    //Nodes colors go back to normal
    
    
    if(fromTagCloud==false){
        $("#names").html(""); 
        $("#topPapers").html(""); $("#topPapers").hide();
        $("#opossiteNodes").html("");
        $("#information").html("");
        $("#searchinput").val("");
        $("#switchbutton").hide();
        $("#tips").html(getTips());
    }   
    for(var i in deselections){
        if( !isUndef(partialGraph._core.graph.nodesIndex[i]) ) {
            partialGraph._core.graph.nodesIndex[i].forceLabel=false;
            partialGraph._core.graph.nodesIndex[i].neighbour=false;
        }
    }
    deselections={};
    // leftPanel("close");
    if(swMacro) LevelButtonDisable(true);
    partialGraph.draw();
}

function highlightSelectedNodes(flag){ 
    pr("\t***methods.js:highlightSelectedNodes(flag)"+flag+" selEmpty:"+is_empty(selections))
    if(!is_empty(selections)){          
        for(var i in selections) {
            if(Nodes[i].type==catSoc && swclickActual=="social"){
                node = partialGraph._core.graph.nodesIndex[i];
                node.active = flag;
            }
            else if(Nodes[i].type==catSem && swclickActual=="semantic") {
                node = partialGraph._core.graph.nodesIndex[i];
                node.active = flag;
            }
            else if(swclickActual=="sociosemantic") {
                node = partialGraph._core.graph.nodesIndex[i];
                node.active = flag;
            }
            else break;        
        }
        
    }
}

function alertCheckBox(eventCheck){    
    if(!isUndef(eventCheck.checked)) checkBox=eventCheck.checked;
}

// States:
// A : Macro-Social
// B : Macro-Semantic
// A*: Macro-Social w/selections
// B*: Macro-Semantic w/selections
// a : Meso-Social
// b : Meso-Semantic
// AaBb: Socio-Semantic
function RefreshState(newNOW){

    pr("\t\t\tin RefreshState newNOW:_"+newNOW+"_.")

	if (newNOW!="") {
	    PAST = NOW;
	    NOW = newNOW;
		
		// if(NOW=="a" || NOW=="A" || NOW=="AaBb") {
		// 	$("#category-A").show();
		// }
		// if(NOW=="b" || NOW=="B" || NOW=="AaBb") {
		// 	$("#category-B").show();
		// }
	}

    $("#category-A").hide();
    $("#category-B").hide();  
    // i=0; for(var s in selections) { i++; break;}
    // if(is_empty(selections) || i==0) LevelButtonDisable(true);
    // else LevelButtonDisable(false);

    //complete graphs case
    // sels=getNodeIDs(selections).length
    if(NOW=="A" || NOW=="a") {
    	// N : number of nodes
    	// k : number of ( selected nodes + their neighbors )
    	// s : number of selections
        var N=( Object.keys(Nodes).filter(function(n){return Nodes[n].type==catSoc}) ).length
        var k=Object.keys(getNeighs(Object.keys(selections),nodes1)).length
        var s=Object.keys(selections).length
        pr("in social N: "+N+" - k: "+k+" - s: "+s)
        if(NOW=="A"){
            if( (s==0 || k>=(N-1)) ) {
                LevelButtonDisable(true);
            } else LevelButtonDisable(false);
            if(s==N) LevelButtonDisable(false);
        }

        if(NOW=="a") {
            LevelButtonDisable(false);
        }

        $("#semLoader").hide();
        $("#category-A").show();
        $("#colorGraph").show();
        
    }
    if(NOW=="B" || NOW=="b") {
        var N=( Object.keys(Nodes).filter(function(n){return Nodes[n].type==catSem}) ).length
        var k=Object.keys(getNeighs(Object.keys(selections),nodes2)).length
        var s=Object.keys(selections).length
        pr("in semantic N: "+N+" - k: "+k+" - s: "+s)
        if(NOW=="B") {
            if( (s==0 || k>=(N-1)) ) {
                LevelButtonDisable(true);
            } else LevelButtonDisable(false);
            if(s==N) LevelButtonDisable(false);
        }

        if(NOW=="b") {
            LevelButtonDisable(false);
        }
        if ( semanticConverged ) {
            $("#semLoader").hide();
            $("#category-B").show();
            $.doTimeout(30,function (){
                EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
                NodeWeightFilter ( "#sliderBNodeWeight" , "type" , "NGram" , "size");
                
            });
        } else $("#semLoader").show();

    }
    if(NOW=="AaBb"){
        LevelButtonDisable(true);
        $("#category-A").show();
        $("#category-B").show();
    }

    partialGraph.draw();

}

function pushSWClick(arg){
    swclickPrev = swclickActual;
    swclickActual = arg;
}

// it receives entire node
function selection(currentNode){
    if(checkBox==false && cursor_size==0) {
        highlightSelectedNodes(false);
        opossites = [];
        selections = [];
        partialGraph.refresh();
    }    
    if(socsemFlag==false){
        if(isUndef(selections[currentNode.id])){
            selections[currentNode.id] = 1;
            if(Nodes[currentNode.id].type==catSoc && !isUndef(bipartiteD2N[currentNode.id])){
                for(i=0;i<bipartiteD2N[currentNode.id].neighbours.length;i++) {
                    if(isUndef(opossites[bipartiteD2N[currentNode.id].neighbours[i]])){
                        opossites[bipartiteD2N[currentNode.id].neighbours[i]]=1;
                    }
                    else {
                        opossites[bipartiteD2N[currentNode.id].neighbours[i]]++;
                    }
                }
            }  
            if(Nodes[currentNode.id].type==catSem){
                if(!isUndef(bipartiteN2D[currentNode.id])){
                    for(i=0;i<bipartiteN2D[currentNode.id].neighbours.length;i++) {
                        if(isUndef(opossites[bipartiteN2D[currentNode.id].neighbours[i]])){
                            opossites[bipartiteN2D[currentNode.id].neighbours[i]]=1;
                        }
                        else opossites[bipartiteN2D[currentNode.id].neighbours[i]]++;
                
                    }
                }
            }
            currentNode.active=true; 
        }
        else {
            delete selections[currentNode.id];        
            markAsSelected(currentNode.id,false);
            if(Nodes[currentNode.id].type==catSoc){
                for(i=0;i<bipartiteD2N[currentNode.id].neighbours.length;i++) {
                    if(isUndef(opossites[bipartiteD2N[currentNode.id].neighbours[i]])) {
                        console.log("lala");
                    }
                    if(opossites[bipartiteD2N[currentNode.id].neighbours[i]]==1){
                        delete opossites[bipartiteD2N[currentNode.id].neighbours[i]];
                    }
                    if(opossites[bipartiteD2N[currentNode.id].neighbours[i]]>1){
                        opossites[bipartiteD2N[currentNode.id].neighbours[i]]--;
                    }
                }
            }    
            if(Nodes[currentNode.id].type==catSem){
                for(i=0;i<bipartiteN2D[currentNode.id].neighbours.length;i++) {
                    if(isUndef(opossites[bipartiteN2D[currentNode.id].neighbours[i]])) {
                        console.log("lala");
                    }
                    if(opossites[bipartiteN2D[currentNode.id].neighbours[i]]==1){
                        delete opossites[bipartiteN2D[currentNode.id].neighbours[i]];
                    }
                    if(opossites[bipartiteN2D[currentNode.id].neighbours[i]]>1){
                        opossites[bipartiteN2D[currentNode.id].neighbours[i]]--;
                    }
                }
            }
        
            currentNode.active=false;
        }
    }
    
    /* ============================================================================================== */
    
    else {
        if(isUndef(selections[currentNode.id])){
            selections[currentNode.id] = 1;
        
            if(Nodes[currentNode.id].type==catSoc){
                for(i=0;i<bipartiteD2N[currentNode.id].neighbours.length;i++) {
                    //opossitesbipartiteD2N[currentNode.id].neighbours[i]];
                    if(isUndef(opossites[bipartiteD2N[currentNode.id].neighbours[i].toString()])){
                        opossites[bipartiteD2N[currentNode.id].neighbours[i]]=1;
                    }
                    else {
                        opossites[bipartiteD2N[currentNode.id].neighbours[i]]++;
                    }
                }
            }    
            if(Nodes[currentNode.id].type==catSem){
                for(i=0;i<nodes2[currentNode.id].neighbours.length;i++) {
                    if(isUndef(opossites[nodes2[currentNode.id].neighbours[i]])){
                        opossites[nodes2[currentNode.id].neighbours[i]]=1;
                    }
                    else opossites[nodes2[currentNode.id].neighbours[i]]++;
                
                }
            }
        
            currentNode.active=true;
        }
        else {
            delete selections[currentNode.id];
            markAsSelected(currentNode.id,false);
            
            if(Nodes[currentNode.id].type==catSoc){
                for(i=0;i<bipartiteD2N[currentNode.id].neighbours.length;i++) {
                    if(isUndef(opossites[bipartiteD2N[currentNode.id].neighbours[i]])) {
                        console.log("lala");
                    }
                    if(opossites[bipartiteD2N[currentNode.id].neighbours[i]]==1){
                        delete opossites[bipartiteD2N[currentNode.id].neighbours[i]];
                    }
                    if(opossites[bipartiteD2N[currentNode.id].neighbours[i]]>1){
                        opossites[bipartiteD2N[currentNode.id].neighbours[i]]--;
                    }
                }
            }    
            if(Nodes[currentNode.id].type==catSem){
                for(i=0;i<nodes2[currentNode.id].neighbours.length;i++) {
                    if(isUndef(opossites[nodes2[currentNode.id].neighbours[i]])) {
                        console.log("lala");
                    }
                    if(opossites[nodes2[currentNode.id].neighbours[i]]==1){
                        delete opossites[nodes2[currentNode.id].neighbours[i]];
                    }
                    if(opossites[nodes2[currentNode.id].neighbours[i]]>1){
                        opossites[nodes2[currentNode.id].neighbours[i]]--;
                    }
                }
            }
        
            currentNode.active=false;
        }
    }
    // partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, 0.8);
    partialGraph.refresh();
}

function getOpossitesNodes(node_id, entireNode) {
    node="";    
    if(entireNode==true) node=node_id;
    else node = partialGraph._core.graph.nodesIndex[node_id];
    if(socsemFlag==true) {
        pr("wtf is this -> if(socsemFlag==true) {");
        cancelSelection(false);
        socsemFlag=false;
    }
    
    if (!node) return null;
    //selection(node);    
    if(categoriesIndex.length==1) selectionUni(node);
    if(categoriesIndex.length==2) selection(node);
    
    opos = ArraySortByValue(opossites, function(a,b){
        return b-a
    });
}

//	tag cloud div
//missing: the graphNGrams javascript
function htmlfied_alternodes(elems) {
    var oppositesNodes=[]
    js1='onclick="graphTagCloudElem(\'';
    js2="');\""
    frecMAX=elems[0].value
    for(var i in elems){
        id=elems[i].key
        frec=elems[i].value
        if(frecMAX==1) fontSize=desirableTagCloudFont_MIN;
        else {
            fontSize=
            desirableTagCloudFont_MIN+
            (frec-1)*
            ((desirableTagCloudFont_MAX-desirableTagCloudFont_MIN)/(frecMAX-1));
        }
        if(!isUndef(Nodes[id])){
            //          js1            js2
            // onclick="graphNGrams('  ');
            htmlfied_alternode = '<span class="tagcloud-item" style="font-size:'+fontSize+'px;" '+js1+id+js2+'>'+ Nodes[id].label+ '</span>';
            oppositesNodes.push(htmlfied_alternode)
        }
    }
    return oppositesNodes
}

// nodes information div
function htmlfied_nodesatts(elems){

    var socnodes=[]
    var semnodes=[]
    for(var i in elems) {

        information=[]

        var id=elems[i]
        var node = Nodes[id]

        if (mainfile) {
            information += '<li><b>' + node.label + '</b></li>';
            for (var i in node.attributes) {
                information += '<li>&nbsp;&nbsp;'+i +" : " + node.attributes[i] + '</li>';
            }
            socnodes.push(information);
        } else {
            if(node.type==catSoc){
                information += '<li><b>' + node.label + '</b></li>';
                if(node.htmlCont==""){
                    if (!isUndef(node.level)) {
                        information += '<li>' + node.level + '</li>';
                    }
                } else {
                    information += '<li>' + $("<div/>").html(node.htmlCont).text() + '</li>';
                }        
                socnodes.push(information)
            }

            if(node.type==catSem){
                information += '<li><b>' + node.label + '</b></li>';
                google='<a href=http://www.google.com/#hl=en&source=hp&q=%20'+node.label.replace(" ","+")+'%20><img src="'+twjs+'img/google.png"></img></a>';
                wiki = '<a href=http://en.wikipedia.org/wiki/'+node.label.replace(" ","_")+'><img src="'+twjs+'img/wikipedia.png"></img></a>';
                flickr= '<a href=http://www.flickr.com/search/?w=all&q='+node.label.replace(" ","+")+'><img src="'+twjs+'img/flickr.png"></img></a>';
                information += '<li>'+google+"&nbsp;"+wiki+"&nbsp;"+flickr+'</li><br>';
                semnodes.push(information)
            }
        }
    }
    return socnodes.concat(semnodes)
}


//missing: getTopPapers for both node types
//considering complete graphs case! <= maybe i should mv it
function updateLeftPanel_fix() {
    pr("\t ** in updateLeftPanel() corrected version** ")
    var namesDIV=''
    var alterNodesDIV=''
    var informationDIV=''

    // var alternodesname=getNodeLabels(opos)

    namesDIV+='<div id="selectionsBox"><h4>';
    namesDIV+= getNodeLabels( selections ).join(', ')//aqui limitar
    namesDIV += '</h4></div>';

    if(opos.length>0) {
	    alterNodesDIV+='<div id="opossitesBox">';//tagcloud
	    alterNodesDIV+= htmlfied_alternodes( opos ).join("\n") 
	    alterNodesDIV+= '</div>';
	}

        // getTopPapers("semantic");

    informationDIV += '<br><h4>Information:</h4><ul>';
    informationDIV += htmlfied_nodesatts( getNodeIDs(selections) ).join("<br>\n")
    informationDIV += '</ul><br>';

    $("#names").html(namesDIV); 
    $("#opossiteNodes").html(alterNodesDIV); 
    $("#information").html(informationDIV);
    $("#tips").html("");
    // $("#topPapers").show();
}

function printStates() {
	pr("\t\t\t\t---------"+getClientTime()+"---------")
	pr("\t\t\t\tswMacro: "+swMacro)
	pr("\t\t\t\tswActual: "+swclickActual+" |  swPrev: "+swclickPrev)
	pr("\t\t\t\tNOW: "+NOW+" |  PAST: "+PAST)
	pr("\t\t\t\tselections: ")
	pr(Object.keys(selections))
	pr("\t\t\t\topposites: ")
	pr(Object.keys(opossites))
	pr("\t\t\t\t------------------------------------")
}

//	just css
//true: button disabled
//false: button enabled
function LevelButtonDisable( TF ){
	$('#changelevel').prop('disabled', TF);
}

//tofix!
function graphTagCloudElem(nodes) {
    pr("in graphTagCloudElem, nodae_id: "+nodes);
    cancelSelection();
    partialGraph.emptyGraph();


    var ndsids=[]
    if(! $.isArray(nodes)) ndsids.push(nodes);
    else ndsids=nodes;

    var voisinage = []
    var vars = []

    node_id = ndsids[0]
    
    if(Nodes[node_id].type==catSoc) {
    	voisinage = nodes1;
    	vars = ["social","a"]
    	$("#colorGraph").show();
    } else {
    	voisinage = nodes2;
    	vars = ["semantic","b"]
    	$("#colorGraph").hide();
    }
 	
    var finalnodes={}

    for (var i in ndsids) {
        node_id = ndsids[i]
    	finalnodes[node_id]=1
    	if(voisinage[node_id]) {
    		for(var j in voisinage[node_id].neighbours) {
    		    id=voisinage[node_id].neighbours[j];
    		    s = node_id;
    		    t = id;
    		    edg1 = Edges[s+";"+t];
    		    if(edg1){
    		        if(!edg1.lock) finalnodes[t] = 1;
    		    }
    		    edg2 = Edges[t+";"+s];
    		    if(edg2){
    		        if(!edg2.lock) finalnodes[t] = 1;
    		    }
    		}
    	}
    }
    for (var Nk in finalnodes) unHide(Nk);
    createEdgesForExistingNodes(vars[0]);

	pushSWClick(vars[0]);
	RefreshState(vars[1]);
	swMacro=false;

	MultipleSelection(ndsids , false);//false-> dont apply deselection algorithm

	$.doTimeout(10,function (){
		fa2enabled=true; partialGraph.startForceAtlas2();
	});

	$('.gradient').css({"background-size":"90px 90px"});
}
      
function updateDownNodeEvent(selectionRadius){
    pr("actualizando eventos downode");
    partialGraph.unbind("downnodes");
    partialGraph.unbind("overnodes");
    partialGraph.unbind("outnodes");
    hoverNodeEffectWhileFA2(selectionRadius);
}


function greyEverything(){
    
    nds = partialGraph._core.graph.nodes.filter(function(n) {
                            return !n['hidden'];
                        });
    for(var i in nds){
            if(!nds[i].attr['grey']){
                nds[i].attr['true_color'] = nds[i].color;
                alphacol = "rgba("+hex2rga(nds[i].color)+",0.5)";
                nds[i].color = alphacol;
            }
            nds[i].attr['grey'] = 1;
    }
    
    eds = partialGraph._core.graph.edges.filter(function(e) {
                            return !e['hidden'];
                        });
    for(var i in eds){
            if(!eds[i].attr['grey']){
                eds[i].attr['true_color'] = eds[i].color;
                eds[i].color = greyColor;
            }
            eds[i].attr['grey'] = 1;
    }

    //		deselect neighbours of previous selection i think
    // for(var i in selections){
    //     if(!isUndef(nodes1[i])){
    //         if(!isUndef(nodes1[i]["neighbours"])){
    //             nb=nodes1[i]["neighbours"];
    //             for(var j in nb){
    //                 deselections[nb[j]]=1;
    //                 partialGraph._core.graph.nodesIndex[nb[j]].forceLabel=true;
    //                 partialGraph._core.graph.nodesIndex[nb[j]].neighbour=true;
    //             }
    //         }
    //     }
    // }
}


//it is a mess but it works. 
// TODO: refactor this
function markAsSelected(n_id,sel) {
    if(!isUndef(n_id.id)) nodeSel=n_id;
    else nodeSel = partialGraph._core.graph.nodesIndex[n_id];
    
    if(sel) {
        nodeSel.color = nodeSel.attr['true_color'];
        nodeSel.attr['grey'] = 0;
        
        if(categoriesIndex.length==1) {
        	pr("jeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeere")
            if( !isUndef(nodes1[nodeSel.id]) &&
                    !isUndef(nodes1[nodeSel.id].neighbours)
                  ){
                    neigh=nodes1[nodeSel.id].neighbours;/**/
                    for(var i in neigh){

                        vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                        vec.color = vec.attr['true_color'];
                        vec.attr['grey'] = 0;
                        an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                        if(!isUndef(an_edge) && !an_edge.hidden){
                            an_edge.color = an_edge.attr['true_color'];
                            an_edge.attr['grey'] = 0;
                        }
                        an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                        if(!isUndef(an_edge) && !an_edge.hidden){
                            an_edge.color = an_edge.attr['true_color'];
                            an_edge.attr['grey'] = 0;
                        }
                    }
                }
        } // two categories network:
        else {
            if(swclickActual=="social") {
                if(nodeSel.type==catSoc){
                    if( !isUndef(nodes1[nodeSel.id]) &&
                        !isUndef(nodes1[nodeSel.id].neighbours)
                      ){
                        neigh=nodes1[nodeSel.id].neighbours;/**/
                        for(var i in neigh) {


                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {

                                nodeVec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                // vec.color = vec.attr['true_color'];
                                // vec.attr['grey'] = 0;
                                // pr("nodeselected: "+nodeSel.id+"\t"+nodeSel.label+"\t\t||\t\tvecino: "+vec.id+"\t"+vec.label)

                                possibledge1 = partialGraph._core.graph.edgesIndex[nodeVec.id+";"+nodeSel.id]
                                possibledge2 = partialGraph._core.graph.edgesIndex[nodeSel.id+";"+nodeVec.id]

                                an_edge = (!isUndef(possibledge1))?possibledge1:possibledge2;
                                if(!isUndef(an_edge) && !an_edge.hidden) {

                                    //highlight node
                                    // nodeVec.hidden = false;
                                    nodeVec.color = nodeVec.attr['true_color'];
                                    nodeVec.attr['grey'] = 0;

                                    //highlight edge
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;                           
                                }

                                // if ( (NOW=="a" || NOW=="b") && nodeVec.color==grey)
                                //  pr(nodeVec)
                                    // nodeVec.hidden = true

                                // an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                // if(!isUndef(an_edge) && !an_edge.hidden){
                                //     an_edge.color = an_edge.attr['true_color'];
                                //     an_edge.attr['grey'] = 0;
                                // }
                                // an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                // if(!isUndef(an_edge) && !an_edge.hidden){
                                //     an_edge.color = an_edge.attr['true_color'];
                                //     an_edge.attr['grey'] = 0;
                                // }
                            }
                        }
                    }
                } else { 

                    if( !isUndef(bipartiteN2D[nodeSel.id]) &&
                        !isUndef(bipartiteN2D[nodeSel.id].neighbours)
                      ){
                        neigh=bipartiteN2D[nodeSel.id].neighbours;/**/
                        for(var i in neigh){

                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ){                                
                                vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                vec.color = vec.attr['true_color'];
                                vec.attr['grey'] = 0;
                                an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                                an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                            }
                        }
                      }
                }
            }
            if(swclickActual=="semantic") {
                if(nodeSel.type==catSoc){           
                    if( !isUndef(bipartiteD2N[nodeSel.id]) &&
                        !isUndef(bipartiteD2N[nodeSel.id].neighbours)
                      ){
                        neigh=bipartiteD2N[nodeSel.id].neighbours;/**/
                        for(var i in neigh) {

                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {
                                vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                vec.color = vec.attr['true_color'];
                                vec.attr['grey'] = 0;
                                an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                                an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                            }

                        }
                      }
                }
                else {
                    if( !isUndef(nodes2[nodeSel.id]) &&
                        !isUndef(nodes2[nodeSel.id].neighbours)
                      ){
                        neigh=nodes2[nodeSel.id].neighbours;/**/
                        for(var i in neigh){

                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {
                                nodeVec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                // vec.color = vec.attr['true_color'];
                                // vec.attr['grey'] = 0;
                                // pr("nodeselected: "+nodeSel.id+"\t"+nodeSel.label+"\t\t||\t\tvecino: "+vec.id+"\t"+vec.label)

                                possibledge1 = partialGraph._core.graph.edgesIndex[nodeVec.id+";"+nodeSel.id]
                                possibledge2 = partialGraph._core.graph.edgesIndex[nodeSel.id+";"+nodeVec.id]

                                an_edge = (!isUndef(possibledge1))?possibledge1:possibledge2;
                                if(!isUndef(an_edge) && !an_edge.hidden) {

                                	//highlight node
                                	// nodeVec.hidden = false;
    	                            nodeVec.color = nodeVec.attr['true_color'];
    	                            nodeVec.attr['grey'] = 0;

                                	//highlight edge
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;                         	
                                }

                                // if ( (NOW=="a" || NOW=="b") && nodeVec.color==grey)
                                // 	pr(nodeVec)
                                	// nodeVec.hidden = true


                                // vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                // vec.color = vec.attr['true_color'];
                                // vec.attr['grey'] = 0;
                                // an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                // if(!isUndef(an_edge) && !an_edge.hidden){
                                //     an_edge.color = an_edge.attr['true_color'];
                                //     an_edge.attr['grey'] = 0;
                                // }
                                // an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                // if(!isUndef(an_edge) && !an_edge.hidden){
                                //     an_edge.color = an_edge.attr['true_color'];
                                //     an_edge.attr['grey'] = 0;
                                // }
                            }
                        }
                      }
                }
            }
            if(swclickActual=="sociosemantic") {
                if(nodeSel.type==catSoc){  

                    if( !isUndef(nodes1[nodeSel.id]) &&
                        !isUndef(nodes1[nodeSel.id].neighbours)
                      ){
                        neigh=nodes1[nodeSel.id].neighbours;/**/
                        for(var i in neigh){
                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {
                                vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                vec.color = vec.attr['true_color'];
                                vec.attr['grey'] = 0;
                                an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                                an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                            }
                        }   
                    }

                    if( !isUndef(bipartiteD2N[nodeSel.id]) &&
                        !isUndef(bipartiteD2N[nodeSel.id].neighbours)
                      ){
                        neigh=bipartiteD2N[nodeSel.id].neighbours;/**/
                        for(var i in neigh) {
                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {                                
                                vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                vec.color = vec.attr['true_color'];
                                vec.attr['grey'] = 0;
                                an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                                an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                            }
                        }
                      }
                }
                else {                
                    if( !isUndef(nodes2[nodeSel.id]) &&
                        !isUndef(nodes2[nodeSel.id].neighbours)
                      ){
                        neigh=nodes2[nodeSel.id].neighbours;/**/
                        for(var i in neigh) {
                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {
                                vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                vec.color = vec.attr['true_color'];
                                vec.attr['grey'] = 0;
                                an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                                an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                            }
                        }
                    }

                    if( !isUndef(bipartiteN2D[nodeSel.id]) &&
                        !isUndef(bipartiteN2D[nodeSel.id].neighbours)
                      ){
                        neigh=bipartiteN2D[nodeSel.id].neighbours;/**/
                        for(var i in neigh){
                            if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {                                
                                vec = partialGraph._core.graph.nodesIndex[neigh[i]];
                                vec.color = vec.attr['true_color'];
                                vec.attr['grey'] = 0;
                                an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
                                if(!isUndef(an_edge) && !an_edge.hidden){
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                                an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
                                if(!isUndef(an_edge) && !an_edge.hidden) {
                                    an_edge.color = an_edge.attr['true_color'];
                                    an_edge.attr['grey'] = 0;
                                }
                            }
                        }
                    }
                }
            }
    	}
    }
    //    /* Just in case of unselection */
    //    /* Finally I decide not using this unselection. */
    //    /* We just greyEverything and color the selections[] */
    //    else { //   sel=false <-> unselect(nodeSel)
    //                
    //        nodeSel.color = greyColor;
    //        nodeSel.attr['grey'] = 1;
    //        
    //        if(swclickActual=="social") {
    //            if(nodeSel.type==catSoc){
    //                neigh=nodes1[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //            }
    //            else {     
    //                neigh=bipartiteN2D[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //            }
    //        }
    //        if(swclickActual=="semantic") {
    //            if(nodeSel.type==catSoc){   
    //                neigh=bipartiteD2N[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //            }
    //            else {   
    //                neigh=nodes2[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //            }
    //        }
    //        if(swclickActual=="sociosemantic") {
    //            if(nodeSel.type==catSoc){    
    //                neigh=nodes1[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }    
    //                neigh=bipartiteD2N[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //            }
    //            else { 
    //                neigh=nodes2[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //                neigh=bipartiteN2D[nodeSel.id].neighbours;/**/
    //                for(var i in neigh){
    //                    vec = partialGraph._core.graph.nodesIndex[neigh[i]];
    //                    vec.color = greyColor;
    //                    vec.attr['grey'] = 1;
    //                    an_edge=partialGraph._core.graph.edgesIndex[vec.id+";"+nodeSel.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                    an_edge=partialGraph._core.graph.edgesIndex[nodeSel.id+";"+vec.id];
    //                    if(typeof(an_edge)!="undefined" && an_edge.hidden==false){
    //                        an_edge.color = greyColor;
    //                        an_edge.attr['grey'] = 1;
    //                    }
    //                }
    //            }
    //        }
    //    }
}

//obsolete au non
function DrawAsSelectedNodes( nodeskeys ) {
    greyEverything(); 
    
    var ndsids=[]
    if( $.isArray(nodeskeys) ) {

    	if(nodeskeys.length==0 && !is_empty(nodeskeys))
    		ndsids = Object.keys(nodeskeys)
    	else
    		ndsids=nodeskeys;

    } else ndsids.push(nodeskeys);

    if(!checkBox) {
        checkBox=true;
        for(var i in ndsids){
            nodeid = ndsids[i]
            markAsSelected(nodeid,true); 
        }
        checkBox=false;
    }
    overNodes=true; 
}

function MultipleSelection(nodes , desalg){

	pr("IN MULTIPLE SELECTION: checkbox="+checkBox)

    var prevsels = selections;

	if(!checkBox) cancelSelection(false);

	greyEverything(); 

	var ndsids=[]
	if(! $.isArray(nodes)) ndsids.push(nodes);
	else ndsids=nodes;

	if(!checkBox) {
		checkBox=true;
        printStates();
        pr("prevsels:")
        pr(Object.keys(prevsels))
        pr("ndsids:")
        pr(ndsids)

        if (desalg && !is_empty(prevsels) ) {
            pr("DOING THE WEIRD ALGORITHM")
            var blacklist = {};
            for(var i in ndsids) {
                ID = ndsids[i];
                if ( prevsels[ID] ) {
                    delete prevsels[ID];
                    blacklist[ID] = true;
                }
            }

            if(Object.keys(blacklist).length>0) {
                tmparr = Object.keys(prevsels);
                for (var i in ndsids) {
                    ID = ndsids[i];
                    if(isUndef(blacklist[ID])) {
                        tmparr.push(ID)
                    }
                }
                ndsids = tmparr;
            }
        } else pr("CASE NOT COVERED")
        

        if (ndsids.length>0) {
    		for(var i in ndsids) {
    		 	nodeid = ndsids[i]
    		 	getOpossitesNodes(nodeid,false); //false -> just nodeid
    		 	markAsSelected(nodeid,true);
    		}
        } else {
            cancelSelection(false);
            partialGraph.draw();
            RefreshState("")
            checkBox=false;
            return;
        }
		checkBox=false;
        
	} else { 
	  //checkbox = true
		cancelSelection(false);
		greyEverything(); 

		for(var i in ndsids){
		 	nodeid = ndsids[i]
		 	getOpossitesNodes(nodeid,false); //false -> just nodeid
		 	markAsSelected(nodeid,true); 
		}
    }

	overNodes=true; 

	partialGraph.draw();

    updateLeftPanel_fix();

    RefreshState("")
}

//test-function
function genericHighlightSelection( nodes ) {

	for( var n in nodes ) {
		pr(n)
	}

        // nodeSel.color = nodeSel.attr['true_color'];
        // nodeSel.attr['grey'] = 0;
        
        //     if(swclickActual=="social") {
        //         if(nodeSel.type==catSoc){
        //             if( !isUndef(nodes1[nodeSel.id]) &&
        //                 !isUndef(nodes1[nodeSel.id].neighbours)
        //               ) {
        //                 neigh=nodes1[nodeSel.id].neighbours;/**/
        //                 for(var i in neigh) {


        //                     if( !isUndef(partialGraph._core.graph.nodesIndex[neigh[i]]) ) {

        //                         nodeVec = partialGraph._core.graph.nodesIndex[neigh[i]];
        //                         possibledge1 = partialGraph._core.graph.edgesIndex[nodeVec.id+";"+nodeSel.id]
        //                         possibledge2 = partialGraph._core.graph.edgesIndex[nodeSel.id+";"+nodeVec.id]
        //                     }
        //                 }
        //             }
        //         }
        //     }
}

function hoverNodeEffectWhileFA2(selectionRadius) { 
    
    partialGraph.bind('downnodes', function (event) {
        var nodeID = event.content;
        if(nodeID.length>0) {

            pr("\t\t\t\t"+nodeID+" -> "+Nodes[nodeID].label);
            pr(getn(nodeID))

            if(cursor_size==0 && !checkBox){
                //Normal click on a node
                $.doTimeout(30,function (){
                    MultipleSelection(nodeID , true);//true-> apply deselection algorithm
                });
            }
            
            if(cursor_size==0 && checkBox){
                //Normal click on a node, but we won't clean the previous selections
			    selections[nodeID] = 1;
                $.doTimeout(30,function (){
                    MultipleSelection( Object.keys(selections) , true );//true-> apply deselection algorithm
                });
            }
        }
    });
}

function graphResetColor(){
    nds = partialGraph._core.graph.nodes.filter(function(x) {
                            return !x['hidden'];
          });
    eds = partialGraph._core.graph.edges.filter(function(x) {
                            return !x['hidden'];
          });
          
    for(var x in nds){
        n=nds[x];
        n.attr["grey"] = 0;
        n.color = n.attr["true_color"];
    }
    
    for(var x in eds){
        e=eds[x];
        e.attr["grey"] = 0;
        e.color = e.attr["true_color"];
    }  
}

function createEdgesForExistingNodes (typeOfNodes) {
    
	if(typeOfNodes=="social") typeOfNodes="Scholars"
	if(typeOfNodes=="semantic") typeOfNodes="Keywords"
	if(typeOfNodes=="sociosemantic") typeOfNodes="Bipartite"

    existingNodes = partialGraph._core.graph.nodes;



    if( categoriesIndex.length==1 ) {

        var pairdict = {}
        for(var n in existingNodes) {
            ID = existingNodes[n].id;
            vois = nodes1[ID].neighbours;

            for(var v in vois) {
                pair = [ parseInt(ID) , parseInt(vois[v]) ].sort(compareNumbers)
                pairdict [ pair[0]+";"+pair[1] ] = 1
            }
        }

        for (var e in pairdict) {

            edge = "";
            if(isUndef(Edges[e])) {
                E = e.split(";")
                edge = E[1]+";"+E[0];
            } else edge=e;

            E = edge.split(";")
            if( getn(E[0]) && getn(E[1]) )
                unHide(edge)

            // pr("antes:"+e+"\t|\tdespues:"+edge)
            // pr("\t\t\t\t\t----- decision final "+edge)
            // unHide(edge)
        }

        return;
    }



    if(typeOfNodes=="Bipartite"){
        for(i=0; i < existingNodes.length ; i++){
            for(j=0; j < existingNodes.length ; j++){
                
                i1=existingNodes[i].id+";"+existingNodes[j].id;                    
                i2=existingNodes[j].id+";"+existingNodes[i].id;                    
                    
                indexS1 = existingNodes[i].id;
                indexT1 = existingNodes[j].id; 
                    
                indexS2 = existingNodes[j].id;  
                indexT2 = existingNodes[i].id;     

                if(!isUndef(Edges[i1]) && !isUndef(Edges[i2])){
                    if(Edges[i1].weight > Edges[i2].weight ){
                        unHide(indexS1+";"+indexT1);
                    }
                    if(Edges[i1].weight < Edges[i2].weight){
                        unHide(indexS2+";"+indexT2);
                    }
                    if(Edges[i1].weight == Edges[i2].weight){
                        if(Edges[i1].label!="bipartite") {  /*danger*/   
                            if( isUndef(partialGraph._core.graph.edgesIndex[indexS1+";"+indexT1]) &&
                                isUndef(partialGraph._core.graph.edgesIndex[indexT1+";"+indexS1]) ){
                                unHide(indexS1+";"+indexT1);
                            }
                        }
                    }
                        
                        
                }
                else {
                    if(!isUndef(Edges[i1])){// && Edges[i1].label=="bipartite"){
                        //I've found a source Node
                        unHide(indexS1+";"+indexT1);
                    }
                    if(!isUndef(Edges[i2])){// && Edges[i2].label=="bipartite"){
                        //I've found a target Node
                        unHide(indexS2+";"+indexT2);
                    }
                }
            }            
        }
    }
    else {  
        for(i=0; i < existingNodes.length ; i++){
            for(j=(i+1); j < existingNodes.length ; j++){
                    
                i1=existingNodes[i].id+";"+existingNodes[j].id; 
                i2=existingNodes[j].id+";"+existingNodes[i].id; 

                // pr("Edges[i1]:")
                // pr(Edges[i1])
                
                // pr("Edges[i2]:")
                // pr(Edges[i2])
                // pr(".")
                // pr(".")

                // if(!isUndef(Edges[i1]) && !isUndef(Edges[i2]) && i1!=i2){
                    
                //         if(typeOfNodes=="Scholars") { 
                //             if(Edges[i1].label=="nodes1" && Edges[i2].label=="nodes1"){                              
                //                 pr(Edges[i1])
                //                 if(Edges[i1].weight > Edges[i2].weight){
                //                     unHide(i1);
                //                 }
                //                 if(Edges[i1].weight < Edges[i2].weight){
                //                     unHide(i2);
                //                 }
                //                 if(Edges[i1].weight == Edges[i2].weight){
                //                     unHide(i1);
                //                 }  
                //             }
                //         }
                //         if(typeOfNodes=="Keywords") { 
                //             if(Edges[i1].label=="nodes2" && Edges[i2].label=="nodes2"){ 
                //                 pr(Edges[i1]);
                //                 if(Edges[i1].weight > Edges[i2].weight){
                //                     unHide(i1);
                //                 }
                //                 if(Edges[i1].weight < Edges[i2].weight){
                //                     unHide(i2);
                //                 }
                //                 if(Edges[i1].weight == Edges[i2].weight){
                //                     unHide(i1);
                //                 }
                //             }
                //         }
                // }
                // else {
                    e=(!isUndef(Edges[i1]))?Edges[i1]:Edges[i2]
                    if(!isUndef(e)){
                        if(typeOfNodes=="Scholars" && e.label=="nodes1") unHide(e.id)
                        if(typeOfNodes=="Keywords" && e.label=="nodes2") unHide(e.id) 
                    }
                // }
            }  
        }  
    }
}

function hideEverything(){
    pr("\thiding all");
    nodeslength=0;
    for(var n in partialGraph._core.graph.nodesIndex){
        partialGraph._core.graph.nodesIndex[n].hidden=true;
    }
    for(var e in partialGraph._core.graph.edgesIndex){
        partialGraph._core.graph.edgesIndex[e].hidden=true;
    }
    overNodes=false;//magic line!
    pr("\tall hidded");
    //Remember that this function is the analogy of EmptyGraph
    //"Saving node positions" should be applied in this function, too.
}

function unHide(id){
	// pr("unhide "+id)
    id = ""+id;
    if(id.split(";").length==1) {
    // i've received a NODE
        if(!isUndef(getn(id))) return;
        if(Nodes[id]) {
            var tt = Nodes[id].type
            var anode = ({
                id:id,
                label: Nodes[id].label, 
                size: (parseFloat(Nodes[id].size)+sizeMult[tt])+"", 
                x: Nodes[id].x, 
                y: Nodes[id].y,
                hidden:  (Nodes[id].lock)?true:false,
                type: Nodes[id].type,
                color: Nodes[id].color,
                shape: Nodes[id].shape
            });  // The graph node

            if(!Nodes[id].lock) {
                updateSearchLabels(id,Nodes[id].label,Nodes[id].type);
                nodeslength++;
            }
            
            partialGraph.addNode(id,anode);
            return;
        }
    }
    else {// It's an edge!
        //visibleEdges.push(id);
        if(!isUndef(gete(id))) return;
        if(Edges[id] && !Edges[id].lock){

            var anedge = {
                id:         id,
                sourceID:   Edges[id].sourceID,
                targetID:   Edges[id].targetID,
                lock : false,
                label:      Edges[id].label,
                weight: (swMacro && (iwantograph=="sociosemantic"))?Edges[id].bweight:Edges[id].weight
            };

        	partialGraph.addEdge(id , anedge.sourceID , anedge.targetID , anedge);
            return;
        }
    }
}

function pushFilterValue(filtername,arg){
	lastFilter[filtername] = arg;
}

function add1Edge(ID) {	
	if(gete(ID)) return;
	var s = Edges[ID].sourceID
	var t = Edges[ID].targetID
    var edge = {
        id:         ID,
        sourceID:   s,
        targetID:   t,
        label:      Edges[ID].label,
        weight: Edges[ID].weight,
        hidden : false
    };

    if(getn(s) && getn(t)) {

        partialGraph.addEdge(ID,s,t,edge);
        
        if(!isUndef(getn(s))) {
            partialGraph._core.graph.nodesIndex[s].x = Nodes[s].x
            partialGraph._core.graph.nodesIndex[s].y = Nodes[s].y
        }
        if(!isUndef(getn(t))) {
            partialGraph._core.graph.nodesIndex[t].x = Nodes[t].x
            partialGraph._core.graph.nodesIndex[t].y = Nodes[t].y
        }   
    }
}


//obsolete au non
function hideElem(id){
    if(id.split(";").length==1){
        //updateSearchLabels(id,Nodes[id].label,Nodes[id].type);
        partialGraph._core.graph.nodesIndex[id].hidden=true;
    }
    else {// It's an edge!
        partialGraph._core.graph.edgesIndex[id].hidden=true;
        // partialGraph._core.graph.edgesIndex[id].dead=true;
    }
}

//obsolete au non
function unHideElem(id){
    if(id.split(";").length==1){
        //updateSearchLabels(id,Nodes[id].label,Nodes[id].type);
        partialGraph._core.graph.nodesIndex[id].hidden=false;
    }
    else {// It's an edge!
        partialGraph._core.graph.edgesIndex[id].hidden=false;
        // partialGraph._core.graph.edgesIndex[id].dead=false;
    }
}

function changeToMeso(iwannagraph) { 

    labels=[]

    iwantograph=iwannagraph;//just a mess

    partialGraph.emptyGraph();

    pr("changing to Meso-"+iwannagraph);

    if(iwannagraph=="social") {
        if(!is_empty(selections)) {
            
            if(swclickPrev=="social") {

                var finalnodes={}
                for(var i in selections) {
                   finalnodes[i]=1
                   if(nodes1[i]) {
                       for(var j in nodes1[i].neighbours) {
                            id=nodes1[i].neighbours[j];
                            s = i;
                            t = id;
                            edg1 = Edges[s+";"+t];
                            if(edg1){
                                // pr("\tunhide "+edg1.id)
                                if(!edg1.lock){
                                    finalnodes[t] = 1;
                                }
                            }
                            edg2 = Edges[t+";"+s];
                            if(edg2){
                                // pr("\tunhide "+edg2.id)
                                if(!edg2.lock){
                                    finalnodes[t] = 1;
                                }
                            }
                       }
                   }
                }
                for (var Nk in finalnodes) unHide(Nk);
                createEdgesForExistingNodes(iwannagraph);/**/   
            }

            if(swclickPrev=="semantic") {

                var finalnodes={}
                for(var i in selections) {
                    if(Nodes[i].type==catSem){
                        for(var j in opossites) {
                            // unHide(j);
                            finalnodes[j] = 1;
                        }
                    }
                    else {
                        // unHide(i);
                        finalnodes[i]=1;
                        if(nodes1[i]) {
                            neigh=nodes1[i].neighbours;
                            for(var j in neigh) {
                                // unHide(neigh[j]);
                                finalnodes[neigh[j]] = 1;
                            }
                        }
                    }
                }
                for (var Nk in finalnodes) unHide(Nk);
                createEdgesForExistingNodes(iwannagraph);/**/   
            }

            if(swclickPrev=="sociosemantic") { 

                var finalnodes={}

                for(var i in selections) {
                    if(Nodes[i].type==catSoc){
                        // unHide(i);
                        finalnodes[i] = 1;
                        if(nodes1[i]) {
                            for(var j in nodes1[i].neighbours) { 
                                id=nodes1[i].neighbours[j];
                                // unHide(id);
                                finalnodes[id] = 1;
                            }
                        }
                        // createEdgesForExistingNodes(iwannagraph);
                    }
                    if(Nodes[i].type==catSem){
                        for(var j in opossites) {
                            // unHide(j);
                            finalnodes[j] = 1;
                        }
                    }
                }
                for (var Nk in finalnodes) unHide(Nk);
                createEdgesForExistingNodes(iwannagraph);
            }
        }
        
        // EdgeWeightFilter("#sliderAEdgeWeight", "label" , "nodes1", "weight");
        $("#colorGraph").show();
    }

    if(iwannagraph=="sociosemantic") {

        if(!is_empty(selections) && !is_empty(opossites)){

            for(var i in selections) {
                unHide(i);
            }
                
            for(var i in opossites) {
                unHide(i);
            }
                
            createEdgesForExistingNodes(iwannagraph);

            socsemFlag=true;
        }
        
        // EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
        // NodeWeightFilter ( "#sliderBNodeWeight" , "type" , "NGram" , "size") 
        // EdgeWeightFilter("#sliderAEdgeWeight", "label" , "nodes1", "weight");
        $("#colorGraph").hide();
    }
     
    if(iwannagraph=="semantic") {
        if(!is_empty(opossites)){
            // hideEverything()
            //pr("2. swclickPrev: "+swclickPrev+" - swclickActual: "+swclickActual);

            var finalnodes = {}
            if(swclickPrev=="semantic") {



                var finalnodes={}
                for(var i in selections) {
                   finalnodes[i]=1
                   if(nodes2[i]) {
                       for(var j in nodes2[i].neighbours) {
                            id=nodes2[i].neighbours[j];
                            s = i;
                            t = id;
                            edg1 = Edges[s+";"+t];
                            if(edg1){
                                // pr("\tunhide "+edg1.id)
                                if(!edg1.lock){
                                    finalnodes[t] = 1;
                                }
                            }
                            edg2 = Edges[t+";"+s];
                            if(edg2){
                                // pr("\tunhide "+edg2.id)
                                if(!edg2.lock){
                                    finalnodes[t] = 1;
                                }
                            }
                       }
                   }
                }

                for (var Nk in finalnodes) unHide(Nk);
                createEdgesForExistingNodes(iwannagraph);/**/   

                // for(var i in selections) {
                //     // unHide(i);
                //     finalnodes[i] = 1;
                //     if(nodes2[i]) {
                //         neigh=nodes2[i].neighbours;
                //         for(var j in neigh) {
                //             // unHide(neigh[j]);
                //             finalnodes[neigh[j]] = 1;
                //         }
                //     }
                // }
                // for (var Nk in finalnodes) unHide(Nk);
                // createEdgesForExistingNodes(iwannagraph);
            }
            if(swclickPrev=="social") {  
                var finalnodes = {}          
                for(var i in selections) {
                    if(Nodes[i].type==catSoc){
                        for(var j in opossites) {
                            // unHide(j);
                            finalnodes[j] = 1;
                        }
                    } else {
                        // unHide(i);
                        finalnodes[i] = 1;
                        if(nodes2[i]) {
                            neigh=nodes2[i].neighbours;
                            for(var j in neigh) {
                                // unHide(neigh[j]);
                                finalnodes[neigh[j]] = 1;
                            }
                        }
                    }
                }
                for (var Nk in finalnodes) unHide(Nk);
                createEdgesForExistingNodes(iwannagraph);
            }
            if(swclickPrev=="sociosemantic") {
                var finalnodes = {}                     
                for(var i in selections) {
                    if(Nodes[i].type==catSoc){                        
                        for(var j in opossites) {
                            // unHide(j);
                            finalnodes[i] = 1;
                        }
                    }
                    if(Nodes[i].type==catSem){                        
                        // unHide(i);//sneaky bug!
                        finalnodes[i] = 1;
                        if(nodes2[i]) {
                            for(var j in nodes2[i].neighbours) { 
                                id=nodes2[i].neighbours[j];
                                // unHide(id);
                                finalnodes[id] = 1;
                            }
                        }
                    }
                }  
                for (var Nk in finalnodes) unHide(Nk);
                createEdgesForExistingNodes(iwannagraph);              
            }
        }
        
        // EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
        // NodeWeightFilter ( "#sliderBNodeWeight" , "type" , "NGram" , "size") 
        $("#colorGraph").hide();
    }

    fa2enabled=true; partialGraph.startForceAtlas2();

    MultipleSelection(Object.keys(selections) , false);//false-> dont apply deselection algorithm

    $('.gradient').css({"background-size":"90px 90px"});
}

function changeToMacro(iwannagraph) {
    labels=[]
    pr("CHANGING TO Macro-"+iwannagraph);

    iwantograph=iwannagraph;//just a mess

    partialGraph.emptyGraph();

    if ( iwannagraph=="semantic" && !semanticConverged ) {

        partialGraph.draw();
        partialGraph.refresh();
        
        $("#semLoader").show();

        return;

    }

    //iwantograph Social OR Semantic
    if(iwannagraph!="sociosemantic") {
    	socsemFlag=false;
        category = (iwannagraph=="social")?catSoc:catSem;
        pr("CHANGING TO Macro-"+iwannagraph+" __ [category: "+category+"] __ [actualsw: "+swclickActual+"] __ [prevsw: "+swclickPrev+"]")
        //show semantic nodes
        for(var n in Nodes) {                
            if(Nodes[n].type==category){
                unHide(n);
            }                
        } // and semantic edges

        createEdgesForExistingNodes(iwannagraph);

        if(iwannagraph=="social") showMeSomeLabels(6);
        swMacro=true;

        if (!is_empty(selections))
        	$.doTimeout(10,function (){
        		chosenones=(PAST=="a"||PAST=="b")?selections:opossites;
        		MultipleSelection(Object.keys(chosenones) , false)//false-> dont apply deselection algorithm
        	});

    } else {
        //iwantograph socio-semantic
        for(var n in Nodes) unHide(n);

        for(var e in Edges) {  
            if(Edges[e].label=="nodes1" || Edges[e].label=="nodes2"){

                st=e.split(";");
                if(Edges[st[0]+";"+st[1]] && Edges[st[1]+";"+st[0]] &&
                   Edges[st[0]+";"+st[1]].hidden==true &&
                   Edges[st[1]+";"+st[0]].hidden==true
                    ){
                    if(Edges[st[0]+";"+st[1]].weight == Edges[st[1]+";"+st[0]].weight){
                        unHide(st[0]+";"+st[1]);
                    }
                    else {
                        if(Edges[st[0]+";"+st[1]].weight > Edges[st[1]+";"+st[0]].weight){
                            unHide(st[0]+";"+st[1]);
                        }
                        else {
                            unHide(st[1]+";"+st[0]);
                        }
                    }
                }                
            }
            if(Edges[e].label=="bipartite"){
                unHide(e);
            }
        }

        if (!is_empty(selections))
            MultipleSelection(Object.keys(selections) , false);//false-> dont apply deselection algorithm
    }

    $.doTimeout(30,function (){

        if(iwannagraph=="social") {
            // EdgeWeightFilter("#sliderAEdgeWeight", "label" , "nodes1", "weight");
            $("#colorGraph").show();      
        }

        if(iwannagraph=="semantic") {
            // EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
            // NodeWeightFilter ( "#sliderBNodeWeight" , "type" , "NGram" , "size") 
            $("#colorGraph").hide();              
        
            
        }

        if(iwannagraph=="sociosemantic") {
            // EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
            // NodeWeightFilter ( "#sliderBNodeWeight" , "type" , "NGram" , "size") 
            // EdgeWeightFilter("#sliderAEdgeWeight", "label" , "nodes1", "weight");
            $("#colorGraph").hide();        
        }
    });

    // fa2enabled=true; partialGraph.startForceAtlas2();

    $('.gradient').css({"background-size":"40px 40px"});

    var activefilterscount=0;
    for(var i in lastFilter) { 

    	if(iwannagraph=="social" && i.indexOf("sliderA")!=-1 )
    		if(lastFilter[i].charAt(0)!="0")
    			activefilterscount++;

    	if(iwannagraph=="semantic" && i.indexOf("sliderb")!=-1) 
    		if(lastFilter[i].charAt(0)!="0")
    			activefilterscount++;

    	if(iwannagraph=="sociosemantic")
    		if(lastFilter[i].charAt(0)!="0")
    			activefilterscount++;
    }

    // for 1 second, activate FA2 if there is any filter applied
    if(activefilterscount>0) {
    	partialGraph.startForceAtlas2();
    	$.doTimeout(2000,function (){
    		partialGraph.stopForceAtlas2()
    	});
    }
}

function highlightOpossites (list){/*here*/
    for(var n in list){
        if(!isUndef(partialGraph._core.graph.nodesIndex[n])){
            partialGraph._core.graph.nodesIndex[n].active=true;
        }
    }
}

function saveGraph() {
    
    size = getByID("check_size").checked
    color = getByID("check_color").checked
    atts = {"size":size,"color":color}

    if(getByID("fullgraph").checked) {
        saveGEXF ( getnodes() , getedges() , atts);
    }

    if(getByID("visgraph").checked) {
        saveGEXF ( getVisibleNodes() , getVisibleEdges(), atts )
    }

    $("#closesavemodal").click();
}

function saveGEXF(nodes,edges,atts){
    gexf = '<?xml version="1.0" encoding="UTF-8"?>\n';
    gexf += '<gexf xmlns="http://www.gexf.net/1.1draft" xmlns:viz="http://www.gephi.org/gexf/viz" version="1.1">\n';
    gexf += '<graph defaultedgetype="undirected" type="static">\n';
    gexf += '<attributes class="node" type="static">\n';
    gexf += ' <attribute id="0" title="category" type="string">  </attribute>\n';
    gexf += ' <attribute id="1" title="country" type="float">    </attribute>\n';
    //gexf += ' <attribute id="2" title="content" type="string">    </attribute>\n';
    //gexf += ' <attribute id="3" title="keywords" type="string">   </attribute>\n';
    //gexf += ' <attribute id="4" title="weight" type="float">   </attribute>\n';
    gexf += '</attributes>\n';
    gexf += '<attributes class="edge" type="float">\n';
    gexf += ' <attribute id="6" title="type" type="string"> </attribute>\n';
    gexf += '</attributes>\n';
    gexf += "<nodes>\n";

    for(var n in nodes){    
        
        gexf += '<node id="'+nodes[n].id+'" label="'+nodes[n].label+'">\n';
        gexf += ' <viz:position x="'+nodes[n].x+'"    y="'+nodes[n].y+'"  z="0" />\n';
        if(atts["color"]) gexf += ' <viz:size value="'+nodes[n].size+'" />\n';
        if(atts["color"]) {
            col = hex2rga(nodes[n].color);
            gexf += ' <viz:color r="'+col[0]+'" g="'+col[1]+'" b="'+col[2]+'" a="1"/>\n';
        }    
        gexf += ' <attvalues>\n';
        gexf += ' <attvalue for="0" value="'+nodes[n].type+'"/>\n';
        gexf += ' <attvalue for="1" value="'+Nodes[nodes[n].id].CC+'"/>\n';
        gexf += ' </attvalues>\n';
        gexf += '</node>\n';
    }
    gexf += "\n</nodes>\n";
    gexf += "<edges>\n";    
    cont = 1;
    for(var e in edges){
        gexf += '<edge id="'+cont+'" source="'+edges[e].source.id+'"  target="'+edges[e].target.id+'" weight="'+edges[e].weight+'">\n';
        gexf += '<attvalues> <attvalue for="6" value="'+edges[e].label+'"/></attvalues>';
        gexf += '</edge>\n';
        cont++;
    }
    gexf += "\n</edges>\n</graph>\n</gexf>";
    uriContent = "data:application/octet-stream," + encodeURIComponent(gexf);
    newWindow=window.open(uriContent, 'neuesDokument');
}

function saveGraphIMG(){
        
        var strDownloadMime = "image/octet-stream"
        
        var nodesDiv = partialGraph._core.domElements.nodes;
        var nodesCtx = nodesDiv.getContext("2d");

        var edgesDiv = partialGraph._core.domElements.edges;
        var edgesCtx = edgesDiv.getContext("2d");


        var hoverDiv = partialGraph._core.domElements.hover;
        var hoverCtx = hoverDiv.getContext("2d");

        var labelsDiv = partialGraph._core.domElements.labels;
        var labelsCtx = labelsDiv.getContext("2d");

        nodesCtx.drawImage(hoverDiv,0,0);
        nodesCtx.drawImage(labelsDiv,0,0);
        edgesCtx.drawImage(nodesDiv,0,0);

        var strData = edgesDiv.toDataURL("image/png");
        document.location.href = strData.replace("image/png", strDownloadMime)
}
