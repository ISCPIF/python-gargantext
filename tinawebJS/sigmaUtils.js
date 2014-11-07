
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
function getNeighs(sels,arr){ 
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
    if (daclass=="country") {

        CCs = getCountries()
        CCxID = {}
        for(var i in CCs) { 
            code = CCs[i]
            CCxID[code]=parseInt(i);
        }
        pr(CCxID)
        
        var nodes = getVisibleNodes();
        for(var i in nodes) {
            nodes[i].color = Nodes[ nodes[i].id ].color;            
        }

        colorList.sort(function(){ return Math.random()-0.5; }); 
        // pr(colorList);
        for(var i in nodes) {
            cc = Nodes[nodes[i].id]["CC"]
            if( !isUndef( cc ) && cc!="-" ) {
                nodes[i].color = colorList[ CCxID[cc] ];
            }
        }
    }

    if (daclass=="acronym") {

        CCs = getAcronyms()
        CCxID = {}
        for(var i in CCs) { 
            code = CCs[i]
            CCxID[code]=parseInt(i);
        }
        pr(CCxID)
        
        var nodes = getVisibleNodes();
        for(var i in nodes) {
            nodes[i].color = Nodes[ nodes[i].id ].color;            
        }

        colorList.sort(function(){ return Math.random()-0.5; }); 
        // pr(colorList);
        for(var i in nodes) {
            cc = Nodes[nodes[i].id]["ACR"]
            if( !isUndef( cc ) && cc!="-" ) {
                nodes[i].color = colorList[ CCxID[cc] ];
            }
        }

    }


    if (daclass=="default") {
        var nodes = getVisibleNodes();
        for(var i in nodes) {
            nodes[i].color = Nodes[ nodes[i].id ].color;            
        }
    }

    partialGraph.refresh()
    partialGraph.draw();
}


//just for fun
function makeEdgeWeightUndef() {
    for(var e in partialGraph._core.graph.edges) {
        partialGraph._core.graph.edges[e].weight=1;
    }
}