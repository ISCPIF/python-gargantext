


SigmaUtils = function () {
    this.nbCats = 0;

    // input = GEXFstring
    this.FillGraph = function( initialState , catDict  , nodes, edges , graph ) {

        print("Filling the graaaaph:")
        print(catDict)
        for(var i in nodes) {
            var n = nodes[i];
            
            if(initialState[catDict[n.type]]) {
                var node = ({
                    id : n.id,
                    label : n.label,
                    size : n.size,
                    color : n.color,
                    type : n.type,
                    x : n.x,
                    y : n.y
                })
                if(n.shape) node.shape = n.shape;
                // console.log(node)
                
                if(Number(n.id)==287) console.log("coordinates of node 287: ( "+n.x+" , "+n.y+" ) ")
                graph.addNode( n.id , node);
                updateSearchLabels( n.id , n.label , n.type);
            }
        }

        var typeNow = initialState.map(Number).join("|")

        for(var i in Relations[typeNow]) {
            s = i;
            for(var j in Relations[typeNow][i]) {
                t = Relations[typeNow][i][j]
                e = Edges[s+";"+t]
                if(e) {
                    if(e.source != e.target) {
                        var edge = ({
                            id : e.id,
                            hidden : false,
                            sourceID : e.source,
                            targetID : e.target,
                            type : e.type,
                            weight : e.weight
                        })
                        graph.addEdge( e.id , e.source , e.target , edge);
                    }
                }
            }
        }
        return graph;
    }// output = sigma graph

}





//for socialgraph
function showMeSomeLabels(N){
        /*======= Show some labels at the beginning =======*/
        minIn=50,
        maxIn=0,
        minOut=50,
        maxOut=0;        
        partialGraph.iterNodes(function(n){
            if(n.hidden==false){
                if(parseInt(n.inDegree) < minIn) minIn= n.inDegree;
                if(parseInt(n.inDegree) > maxIn) maxIn= n.inDegree;
                if(parseInt(n.outDegree) < minOut) minOut= n.outDegree;
                if(parseInt(n.outDegree) > maxOut) maxOut= n.outDegree;
            }
        });
        counter=0;
        n = getVisibleNodes();
        for(i=0;i<n.length;i++) {
            if(n[i].hidden==false){
                if(n[i].inDegree==minIn && n[i].forceLabel==false) {
                    n[i].forceLabel=true;
                    counter++;
                }
                if(n[i].inDegree==maxIn && n[i].forceLabel==false) {
                    n[i].forceLabel=true;
                    counter++;
                }
                if(n[i].outDegree==minOut && n[i].forceLabel==false) {
                    n[i].forceLabel=true;
                    counter++;
                }
                if(n[i].outDegree==maxOut && n[i].forceLabel==false) {
                    n[i].forceLabel=true;
                    counter++;
                }
                if(counter==N) break;
            }
        }
        partialGraph.draw()
        /*======= Show some labels at the beginning =======*/
}

function getnodes(){
    return partialGraph._core.graph.nodes;
}

function getnodesIndex(){
    return partialGraph._core.graph.nodesIndex;
}

function getedges(){
    return partialGraph._core.graph.edges;
}

function getedgesIndex(){
    return partialGraph._core.graph.edgesIndex;
}

function getVisibleEdges() {
	return partialGraph._core.graph.edges.filter(function(e) {
                return !e['hidden'];
    });
}

function getVisibleNodes() {
    return partialGraph._core.graph.nodes.filter(function(n) {
                return !n['hidden'];
    });
}


function getNodesByAtt(att) {
    return partialGraph._core.graph.nodes.filter(function(n) {
                return n['type']==att;
    });
}

function getn(id){
    return partialGraph._core.graph.nodesIndex[id];
}

function gete(id){
    return partialGraph._core.graph.edgesIndex[id];
}


function find(label){
    var results=[];
    var nds=getnodesIndex();
    label=label.toLowerCase()
    for(var i in nds){
        var n=nds[i];
        if(n.hidden==false){
        	var possiblematch=n.label.toLowerCase()
            if (possiblematch.indexOf(label)!==-1) {
                results.push(n);
            }  
        }
    }
    return results;
}

function exactfind(label) {
    nds=getnodesIndex();
    for(var i in nds){
        n=nds[i];
        if(!n.hidden){
            if (n.label==label) {
                return n;
            }
        }
    }
    return null;
}


function getNodeLabels(elems){
    var labelss=[]
    for(var i in elems){
        var id=(!isUndef(elems[i].key))?elems[i].key:i
        labelss.push(Nodes[id].label)
    }
    return labelss
}

function getNodeIDs(elems){
    return Object.keys(elems)
}


function getSelections(){    
        params=[];
        for(var i in selections){
            params.push(Nodes[i].label);
        }
        return params;
}


//This receives an array not a dict!
//  i added an excpt... why
function getNeighs(sels,arr) { 
    neighDict={};
    for(var i in sels) {
        id = sels[i]
        if(!isUndef(arr[id])) {
            A=arr[id].neighbours;
            for(var j in A){
                neighDict[A[j]]=1
            }
            neighDict[id]=1;
        }
    }    
    return Object.keys(neighDict);
}//It returns an array not a dict!


//Using bipartiteN2D or bipartiteD2N
//This receives an array not a dict!
function getNeighs2(sels,arr){ 
    neighDict={};
    for(var i in sels) {
        id = sels[i]
        if(!isUndef(arr[id])) {
            A=arr[id].neighbours;
            for(var j in A){
                neighDict[A[j]]=1
            }
            // neighDict[id]=1;
        }
    }    
    return Object.keys(neighDict);
}//It returns an array not a dict!

//to general utils
function getArrSubkeys(arr,id) {
    var result = []
    for(var i in arr) {
        result.push(arr[i][id])
    }
    return result;
}

function getCountries(){
    var nodes = getVisibleNodes();
    
    var countries = {}
    pr("in getCountries")
    for(var i in nodes) {
        theid = nodes[i].id;
        // pr(i)
        // pr(Nodes[theid])
        // pr(theid+" : "+Nodes[theid].attr["CC"]+" , "+nodes[i].attr["ACR"])
        if (Nodes[theid]["CC"]!="-")
            countries[Nodes[theid]["CC"]]=1
        // pr("")
    }
    return Object.keys(countries);
}


function getAcronyms() {
    var nodes = getVisibleNodes();
    var acrs = {}
    pr("in getAcronyms")
    for(var i in nodes) {
        theid = nodes[i].id;
        // pr(i)
        // pr(nodes[i].id+" : "+nodes[i].attr["CC"]+" , "+nodes[i].attr["ACR"])
        if (Nodes[theid]["ACR"]!="-")
            acrs[Nodes[theid]["ACR"]]=1
        // pr("")
    }
    return ( Object.keys(acrs) );
}


function clustersBy(daclass) {

    cancelSelection(false);
    var v_nodes = getVisibleNodes();
    var min_pow = 0;
    for(var i in v_nodes) {
        var the_node = Nodes[ v_nodes[i].id ]
        var attval = ( isUndef(the_node.attributes) || isUndef(the_node.attributes[daclass]) )? v_nodes[i][daclass]: the_node.attributes[daclass];
        if( !isNaN(parseFloat(attval)) ) { //is float
            while(true) {
                var themult = Math.pow(10,min_pow);
                if(parseFloat(attval)==0.0) break;
                if ( (parseFloat(attval)*themult)<1.0 ) {
                    min_pow++;
                } else break;
            }
        }
    }

    var NodeID_Val = {}
    var real_min = 1000000;
    var real_max = -1;
    var themult = Math.pow(10,min_pow);
    for(var i in v_nodes) {
        var the_node = Nodes[ v_nodes[i].id ]
        var attval = ( isUndef(the_node.attributes) || isUndef(the_node.attributes[daclass]) )? v_nodes[i][daclass]: the_node.attributes[daclass];
        var attnumber = Number(attval);
        var round_number = Math.round(  attnumber*themult ) ;

        NodeID_Val[v_nodes[i].id] = { "round":round_number , "real":attnumber };

        if (round_number<real_min) real_min = round_number;
        if (round_number>real_max) real_max = round_number;
    }



    console.log(" - - - - - - - - -- - - ")
    console.log(real_min)
    console.log(real_max)
    console.log("10^"+min_pow)
    console.log("the mult: "+themult)
    console.log(" - - - - - - - - -- - - ")


    //    [ Scaling node colours(0-255) and sizes(3-5) ]
    var Min_color = 0;
    var Max_color = 255;
    var Min_size = 2;
    var Max_size= 6;
    for(var i in NodeID_Val) {

        var newval_color = Math.round( ( Min_color+(NodeID_Val[i]["round"]-real_min)*((Max_color-Min_color)/(real_max-real_min)) ) );
        var hex_color = rgbToHex(255, (255-newval_color) , 0)
        partialGraph._core.graph.nodesIndex[i].color = hex_color

        var newval_size = Math.round( ( Min_size+(NodeID_Val[i]["round"]-real_min)*((Max_size-Min_size)/(real_max-real_min)) ) );
        partialGraph._core.graph.nodesIndex[i].size = newval_size;
        // pr("real:"+ NodeID_Val[i]["real"] + " | newvalue: "+newval_size)

        partialGraph._core.graph.nodesIndex[i].label = "("+NodeID_Val[i]["real"].toFixed(min_pow)+") "+Nodes[i].label
    }
    //    [ / Scaling node colours(0-255) and sizes(3-5) ]


    partialGraph.refresh();
    partialGraph.draw();


    //    [ Edge-colour by source-target nodes-colours combination ]
    var v_edges = getVisibleEdges();
    for(var e in v_edges) {
        var e_id = v_edges[e].id;
        var a = v_edges[e].source.color;
        var b = v_edges[e].target.color;
        a = hex2rga(a);
        b = hex2rga(b);
        var r = (a[0] + b[0]) >> 1;
        var g = (a[1] + b[1]) >> 1;
        var b = (a[2] + b[2]) >> 1;
        partialGraph._core.graph.edgesIndex[e_id].color = "rgba("+[r,g,b].join(",")+",0.5)";
    }
    //    [ / Edge-colour by source-target nodes-colours combination ]

    if(daclass!="degree")
        set_ClustersLegend ( daclass )

    partialGraph.refresh();
    partialGraph.draw();

}


function colorsBy(daclass) {
    
    pr("")
    pr(" = = = = = = = = = = = = = = = = = ")
    pr(" = = = = = = = = = = = = = = = = = ")
    pr("colorsBy (    "+daclass+"    )")
    pr(" = = = = = = = = = = = = = = = = = ")
    pr(" = = = = = = = = = = = = = = = = = ")
    pr("")

    if(daclass=="clust_louvain") {
        if(!partialGraph.states.slice(-1)[0].LouvainFait) {
            RunLouvain()
            partialGraph.states.slice(-1)[0].LouvainFait = true
        }
    }

    var v_nodes = getVisibleNodes();
    colorList.sort(function(){ return Math.random()-0.5; });

    for(var i in v_nodes) {
        var the_node = Nodes[ v_nodes[i].id ]
        var attval = ( isUndef(the_node.attributes) || isUndef(the_node.attributes[daclass]) )? v_nodes[i][daclass]: the_node.attributes[daclass];
        partialGraph._core.graph.nodesIndex[v_nodes[i].id].color = colorList[ attval ]
    }
    partialGraph.draw();

    //    [ Edge-colour by source-target nodes-colours combination ]
    var v_edges = getVisibleEdges();
    for(var e in v_edges) {
        var e_id = v_edges[e].id;
        var a = v_edges[e].source.color;
        var b = v_edges[e].target.color;
        if (a && b) {
            a = hex2rga(a);
            b = hex2rga(b);
            var r = (a[0] + b[0]) >> 1;
            var g = (a[1] + b[1]) >> 1;
            var b = (a[2] + b[2]) >> 1;
            partialGraph._core.graph.edgesIndex[e_id].color = "rgba("+[r,g,b].join(",")+",0.5)";
        }
    }
    //    [ / Edge-colour by source-target nodes-colours combination ]
    set_ClustersLegend ( daclass )
    partialGraph.refresh();
    partialGraph.draw();
}

//just for fun
function makeEdgeWeightUndef() {
    for(var e in partialGraph._core.graph.edges) {
        partialGraph._core.graph.edges[e].weight=1;
    }
}