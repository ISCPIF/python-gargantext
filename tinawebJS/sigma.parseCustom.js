/*
 *Categories example (bigraph):
 *  ISItermsAlexandrePartCountry
 *  Authors
 **/


function parse(gexfPath) {
    var gexfhttp;
    gexfhttp = window.XMLHttpRequest ?
    new XMLHttpRequest() :
    new ActiveXObject('Microsoft.XMLHTTP');

    gexfhttp.open('GET', gexfPath, false);
    gexfhttp.send();
    gexf = gexfhttp.responseXML;
}


function scanCategories() {
    nodesNodes = gexf.getElementsByTagName('nodes');
    for(i=0; i<nodesNodes.length; i++){       
        var nodesNode = nodesNodes[i];  // Each xml node 'nodes' (plural)
        node = nodesNode.getElementsByTagName('node');
        
        for(j=0; j<node.length; j++){
            attvalueNodes = node[j].getElementsByTagName('attvalue');
            for(k=0; k<attvalueNodes.length; k++){
                attvalueNode = attvalueNodes[k];
                attr = attvalueNode.getAttribute('for');
                val = attvalueNode.getAttribute('value');
                // pr(val)
                if (attr=="category") categories[val]=val;
            }
        }
    }
    pr("The categories");
    pr(categories);
    pr("");
    i=0;
    for (var cat in categories) {
        categoriesIndex[i] = cat;
        i++;
    }
    pr("The categoriesIndex");
    pr(categoriesIndex);
    pr("");
    return Object.keys(categories).length;
}


function onepartiteExtract(){
    
    var i, j, k;
    //    partialGraph.emptyGraph();
    // Parse Attributes
    // This is confusing, so I'll comment heavily
    var nodesAttributes = [];   // The list of attributes of the nodes of the graph that we build in json
    var edgesAttributes = [];   // The list of attributes of the edges of the graph that we build in json
    var attributesNodes = gexf.getElementsByTagName('attributes');  // In the gexf (that is an xml), the list of xml nodes 'attributes' (note the plural 's')
  
    for(i = 0; i<attributesNodes.length; i++){
        var attributesNode = attributesNodes[i];  // attributesNode is each xml node 'attributes' (plural)
        if(attributesNode.getAttribute('class') == 'node'){
            var attributeNodes = attributesNode.getElementsByTagName('attribute');  // The list of xml nodes 'attribute' (no 's')
            for(j = 0; j<attributeNodes.length; j++){
                var attributeNode = attributeNodes[j];  // Each xml node 'attribute'
        
                var id = attributeNode.getAttribute('id'),
                title = attributeNode.getAttribute('title'),
                type = attributeNode.getAttribute('type');
        
                var attribute = {
                    id:id, 
                    title:title, 
                    type:type
                };
                nodesAttributes.push(attribute);
        
            }
        } else if(attributesNode.getAttribute('class') == 'edge'){
            var attributeNodes = attributesNode.getElementsByTagName('attribute');  // The list of xml nodes 'attribute' (no 's')
            for(j = 0; j<attributeNodes.length; j++){
                var attributeNode = attributeNodes[j];  // Each xml node 'attribute'
        
                var id = attributeNode.getAttribute('id'),
                title = attributeNode.getAttribute('title'),
                type = attributeNode.getAttribute('type');
          
                var attribute = {
                    id:id, 
                    title:title, 
                    type:type
                };
                edgesAttributes.push(attribute);
        
            }
        }
    }
  
    var nodesNodes = gexf.getElementsByTagName('nodes') // The list of xml nodes 'nodes' (plural)

    labels = [];
    minNodeSize=5.00;
    maxNodeSize=5.00;
    numberOfDocs=0;
    numberOfNGrams=0;
    for(i=0; i<nodesNodes.length; i++){
        var nodesNode = nodesNodes[i];  // Each xml node 'nodes' (plural)
        var nodeNodes = nodesNode.getElementsByTagName('node'); // The list of xml nodes 'node' (no 's')

        for(j=0; j<nodeNodes.length; j++){
            var nodeNode = nodeNodes[j];  // Each xml node 'node' (no 's')
      
      
            window.NODE = nodeNode;

            var id = ""+nodeNode.getAttribute('id');
            var label = nodeNode.getAttribute('label') || id;
            
            //viz
            var size=1;
            sizeNodes = nodeNode.getElementsByTagName('size');
            sizeNodes = sizeNodes.length ?
                        sizeNodes :
                        nodeNode.getElementsByTagName('viz:size');
            if(sizeNodes.length>0){
              sizeNode = sizeNodes[0];
              size = parseFloat(sizeNode.getAttribute('value'));
            }
            var x = 100 - 200*Math.random();
            var y = 100 - 200*Math.random();
            var color;
      
            var positionNodes = nodeNode.getElementsByTagName('position');
            positionNodes = positionNodes.length ? 
            positionNodes : 
            nodeNode.getElementsByTagNameNS('*','position');
            if(positionNodes.length>0){
                var positionNode = positionNodes[0];
                x = parseFloat(positionNode.getAttribute('x'));
                y = parseFloat(positionNode.getAttribute('y'));
            }

            var colorNodes = nodeNode.getElementsByTagName('color');
            colorNodes = colorNodes.length ? 
            colorNodes : 
            nodeNode.getElementsByTagNameNS('*','color');
            if(colorNodes.length>0){
                colorNode = colorNodes[0];
                color = '#'+sigma.tools.rgbToHex(parseFloat(colorNode.getAttribute('r')),
                    parseFloat(colorNode.getAttribute('g')),
                    parseFloat(colorNode.getAttribute('b')));
            }
            
            var node = ({
                id:id,
                label:label, 
                size:size, 
                x:x, 
                y:y, 
                type:"",
                attributes:[], 
                color:color
            });  // The graph node
                
            // Attribute values
            var attvalueNodes = nodeNode.getElementsByTagName('attvalue');
            var atts={};
            for(k=0; k<attvalueNodes.length; k++){
                var attvalueNode = attvalueNodes[k];
                var attr = attvalueNode.getAttribute('for');
                var val = attvalueNode.getAttribute('value');
                   // node.attributes.push({
                   //     attr:attr, 
                   //     val:val
                   // });
                atts[attr]=val;
                node.attributes = atts;
            }
            node.id=id;
            node.type = catSoc;
            //if(node.attributes[0].attr=="weight"){
            if(typeof(node.size)==="undefined") node.size=parseInt(node.attributes["weight"]);
            //}
               // if(node.attributes[1].attr=="weight"){
               //     node.size=node.attributes[1].val;
               // }
                
            partialGraph.addNode(id,node);
            labels.push({
                'label' : label,
                'desc'  : node.type
            });
            
            if(parseInt(node.size) < parseInt(minNodeSize)) minNodeSize= node.size;
            if(parseInt(node.size) > parseInt(maxNodeSize)) maxNodeSize= node.size;
            // Create Node
            Nodes[id] = node  // The graph node
            //pr(node);
        }
    }    
    
    //New scale for node size: now, between 2 and 5 instead [1,70]
    for(var it in Nodes){
        Nodes[it].size = 
        desirableNodeSizeMIN+
        (parseInt(Nodes[it].size)-1)*
        ((desirableNodeSizeMAX-desirableNodeSizeMIN)/
            (maxNodeSize-minNodeSize));
        partialGraph._core.graph.nodesIndex[it].size=Nodes[it].size;
    }
    

    var edgeId = 0;
    var edgesNodes = gexf.getElementsByTagName('edges');
    minEdgeWeight=5.0;
    maxEdgeWeight=0.0;
    for(i=0; i<edgesNodes.length; i++){
        var edgesNode = edgesNodes[i];
        var edgeNodes = edgesNode.getElementsByTagName('edge');
        for(j=0; j<edgeNodes.length; j++){
            var edgeNode = edgeNodes[j];
            var source = edgeNode.getAttribute('source');
            var target = edgeNode.getAttribute('target');
            var indice=source+";"+target;
            
            var edge = {
                id:         j,
                sourceID:   source,
                targetID:   target,
                label:      "",
                weight: 1,
                lock: false,
                attributes: []
            };

            var weight = edgeNode.getAttribute('weight');
            if(weight!=undefined){
                edge['weight'] = weight;
            }
            var kind;
            var attvalueNodes = edgeNode.getElementsByTagName('attvalue');
            for(k=0; k<attvalueNodes.length; k++){
                var attvalueNode = attvalueNodes[k];
                var attr = attvalueNode.getAttribute('for');
                var val = attvalueNode.getAttribute('value');
                if(k==1) {
                    kind=val;
                    edge.label=val;
                }
                if(k==3) {
                    edge.weight = val;
                    if(edge.weight < minEdgeWeight) minEdgeWeight= edge.weight;
                    if(edge.weight > maxEdgeWeight) maxEdgeWeight= edge.weight;
                }
                edge.attributes.push({
                    attr:attr, 
                    val:val
                });
            }

            edge.label="nodes1";            
            if(isUndef(nodes1[source])){
                nodes1[source] = {
                    label: Nodes[source].label,
                    neighbours: [],
                    neighboursIndex: {}
                };
                nodes1[source].neighboursIndex[target] = 1;
            } else nodes1[source].neighboursIndex[target] = 1;  

            if( isUndef(nodes1[target]) ){
                nodes1[target] = {
                    label: Nodes[target].label,
                    neighbours: [],
                    neighboursIndex: {}
                };
                nodes1[target].neighboursIndex[source] = 1;
            } else nodes1[target].neighboursIndex[source] = 1;

            Edges[indice] = edge;
            if( isUndef(gete([target+";"+source])) ) partialGraph.addEdge(indice,source,target,edge);
            
        }
    }
    
    for(var n in nodes1) {
    	nodes1[n].neighbours = Object.keys(nodes1[n].neighboursIndex)
    	nodes1[n].neighboursIndex = null;
    	delete nodes1[n].neighboursIndex
    }

}


function fullExtract(){
    var i, j, k;
    // Parse Attributes
    // This is confusing, so I'll comment heavily
    var nodesAttributes = [];   // The list of attributes of the nodes of the graph that we build in json
    var edgesAttributes = [];   // The list of attributes of the edges of the graph that we build in json
    var attributesNodes = gexf.getElementsByTagName('attributes');  // In the gexf (that is an xml), the list of xml nodes 'attributes' (note the plural 's')
  
    for(i = 0; i<attributesNodes.length; i++){
        var attributesNode = attributesNodes[i];  // attributesNode is each xml node 'attributes' (plural)
        if(attributesNode.getAttribute('class') == 'node'){
            var attributeNodes = attributesNode.getElementsByTagName('attribute');  // The list of xml nodes 'attribute' (no 's')
            for(j = 0; j<attributeNodes.length; j++){
                var attributeNode = attributeNodes[j];  // Each xml node 'attribute'
        
                var id = attributeNode.getAttribute('id'),
                title = attributeNode.getAttribute('title'),
                type = attributeNode.getAttribute('type');
        
                var attribute = {
                    id:id, 
                    title:title, 
                    type:type
                };
                nodesAttributes.push(attribute);
        
            }
        } else if(attributesNode.getAttribute('class') == 'edge'){
            var attributeNodes = attributesNode.getElementsByTagName('attribute');  // The list of xml nodes 'attribute' (no 's')
            for(j = 0; j<attributeNodes.length; j++){
                var attributeNode = attributeNodes[j];  // Each xml node 'attribute'
        
                var id = attributeNode.getAttribute('id'),
                title = attributeNode.getAttribute('title'),
                type = attributeNode.getAttribute('type');
          
                var attribute = {
                    id:id, 
                    title:title, 
                    type:type
                };
                edgesAttributes.push(attribute);
        
            }
        }
    }
  
    var nodesNodes = gexf.getElementsByTagName('nodes') // The list of xml nodes 'nodes' (plural)
  
    labels = [];
    numberOfDocs=0;
    numberOfNGrams=0;
    for(i=0; i<nodesNodes.length; i++){
        var nodesNode = nodesNodes[i];  // Each xml node 'nodes' (plural)
        var nodeNodes = nodesNode.getElementsByTagName('node'); // The list of xml nodes 'node' (no 's')

        for(j=0; j<nodeNodes.length; j++){
            var nodeNode = nodeNodes[j];  // Each xml node 'node' (no 's')
      
      
            window.NODE = nodeNode;

            var id = nodeNode.getAttribute('id');
            var label = nodeNode.getAttribute('label') || id;
            
            var size=1;
            sizeNodes = nodeNode.getElementsByTagName('size');
            sizeNodes = sizeNodes.length ?
                        sizeNodes :
                        nodeNode.getElementsByTagName('viz:size');
            if(sizeNodes.length>0){
              sizeNode = sizeNodes[0];
              size = parseFloat(sizeNode.getAttribute('value'));
            }
            
            var x = 100 - 200*Math.random();
            var y = 100 - 200*Math.random();
            var color;
      
            var positionNodes = nodeNode.getElementsByTagName('position');
            positionNodes = positionNodes.length ? positionNodes : nodeNode.getElementsByTagNameNS('*','position');
            if(positionNodes.length>0){
                var positionNode = positionNodes[0];
                x = parseFloat(positionNode.getAttribute('x'));
                y = parseFloat(positionNode.getAttribute('y'));
            }

            var colorNodes = nodeNode.getElementsByTagName('color');
            colorNodes = colorNodes.length ? colorNodes : nodeNode.getElementsByTagNameNS('*','color');
            if(colorNodes.length>0){
                colorNode = colorNodes[0];
                color = '#'+sigma.tools.rgbToHex(parseFloat(colorNode.getAttribute('r')),
                    parseFloat(colorNode.getAttribute('g')),
                    parseFloat(colorNode.getAttribute('b')));
            }
            
            var node = ({
                id:id,
                label:label, 
                size:size, 
                x:x, 
                y:y, 
                type:"",
                attributes:[], 
                color:color
            });  // The graph node

            // Attribute values
            var attvalueNodes = nodeNode.getElementsByTagName('attvalue');
            var atts={};
            for(k=0; k<attvalueNodes.length; k++){
                var attvalueNode = attvalueNodes[k];
                var attr = attvalueNode.getAttribute('for');
                var val = attvalueNode.getAttribute('value');
                atts[attr]=val;
                node.attributes = atts;
                /*      Para asignar tamaño a los NGrams    */
                if(atts["category"]===categoriesIndex[1]) {
                    if(typeof(node.size)==="undefined") node.size=parseInt(val).toFixed(2);
                   
                }
                /*      Para asignar tamaño a los NGrams    */
            }




            //console.log(node.attributes);
            nodecat=node.attributes["category"];
            nodew=parseInt(node.attributes["weight"]);
            if( nodecat===categoriesIndex[1]){
                node.type=catSoc;
                node.id = "D::"+node.id;
                node.shape="square";
                numberOfDocs++;
                //node.size=desirableScholarSize;
                if(typeof(node.size)==="undefined") node.size=nodew;
            } else {
                node.type=catSem;
                node.id = "N::"+node.id;
                numberOfNGrams++;
                if(isUndef(node.size)) node.size=nodew;
            }      
            
            if(parseInt(node.size) < parseInt(minNodeSize)) minNodeSize= node.size;
            if(parseInt(node.size) > parseInt(maxNodeSize)) maxNodeSize= node.size;
            // Create Node

            Nodes[node.id] = node  // The graph node
            
            
        }
    }  
    //New scale for node size: now, between 2 and 5 instead [1,70]
    for(var i in Nodes){
        normalizedSize=desirableNodeSizeMIN+(Nodes[i].size-1)*((desirableNodeSizeMAX-desirableNodeSizeMIN)/(parseInt(maxNodeSize)-parseInt(minNodeSize)));
        Nodes[i].size = ""+normalizedSize;
        nodeK = Nodes[i];
        if(Nodes[i].type==catSoc) {
			nodeK.shape="square";
        	partialGraph.addNode(i,nodeK); 
        }
        // pr(nodeK)
    }
    

    //Edges
    var edgeId = 0;
    var edgesNodes = gexf.getElementsByTagName('edges');
    for(i=0; i<edgesNodes.length; i++){
        var edgesNode = edgesNodes[i];
        var edgeNodes = edgesNode.getElementsByTagName('edge');
        for(j=0; j<edgeNodes.length; j++){
            var edgeNode = edgeNodes[j];
            var source = edgeNode.getAttribute('source');
            var target = edgeNode.getAttribute('target');

            source = (Nodes["D::"+source])? ("D::"+source):("N::"+source)
            target = (Nodes["D::"+target])? ("D::"+target):("N::"+target)

            var indice=source+";"+target;
                
            var edge = {
                id:         indice,
                sourceID:   source,
                targetID:   target,
                label:      "",
                weight: 1,
                attributes: []
            };

            var weight = edgeNode.getAttribute('weight');
            if(weight!=undefined){
                edge['weight'] = weight;
            }
            var kind;
            var attvalueNodes = edgeNode.getElementsByTagName('attvalue');
            for(k=0; k<attvalueNodes.length; k++){
                var attvalueNode = attvalueNodes[k];
                var attr = attvalueNode.getAttribute('for');
                var val = attvalueNode.getAttribute('value');

                if(k=="category") {
                    kind=val;
                    edge.label=val;
                }
                if(k==3) {
                    edge.weight = val;
                    if(edge.weight < minEdgeWeight) minEdgeWeight= edge.weight;
                    if(edge.weight > maxEdgeWeight) maxEdgeWeight= edge.weight;
                }
                edge.attributes.push({
                    attr:attr, 
                    val:val
                });
            }
            
            // pr(edge)
            idS=Nodes[edge.sourceID].type;
            idT=Nodes[edge.targetID].type;

            Edges[indice] = edge;
            
            // if(idS==idT)
           	// 	pr(edge.sourceID+"|"+idS+" <-> "+idT+"|"+edge.targetID)

            if(idS==catSoc && idT==catSoc){  
                // pr("anything here?")

                edge.label = "nodes1";

                if(isUndef(nodes1[source])) {
                    nodes1[source] = {
                        label: Nodes[source].label,
                        neighbours: []
                    };                    
                }
                if(isUndef(nodes1[target])) {
                    nodes1[target] = {
                        label: Nodes[target].label,
                        neighbours: []
                    };                    
                }   
                nodes1[source].neighbours.push(target);
                nodes1[target].neighbours.push(source);

                // partialGraph.addEdge(indice,source,target,edge);
            }
            
            
            if(idS==catSem && idT==catSem){ 
                edge.label = "nodes2";

                if(isUndef(nodes2[source])) {
                    nodes2[source] = {
                        label: Nodes[source].label,
                        neighbours: []
                    };                    
                }
                if(isUndef(nodes2[target])) {
                    nodes2[target] = {
                        label: Nodes[target].label,
                        neighbours: []
                    };                    
                }
                nodes2[source].neighbours.push(target);
                nodes2[target].neighbours.push(source);
                
                // otherGraph.addEdge(indice,source,target,edge);
            }
            
            
            if((idS==catSoc && idT==catSem)||(idS==catSem && idT==catSoc)) {
                edge.label = "bipartite";

                s = edge.sourceID

                // // Source is Document
                if(Nodes[s].type == catSoc) {

                    if(isUndef(bipartiteD2N[source])) {
                        bipartiteD2N[source] = {
                            label: Nodes[source].label,
                            neighbours: []
                        };                    
                    }
                    if(isUndef(bipartiteN2D[target])) {
                        bipartiteN2D[target] = {
                            label: Nodes[target].label,
                            neighbours: []
                        };                    
                    }

                    bipartiteD2N[source].neighbours.push(target);
                    bipartiteN2D[target].neighbours.push(source);

                // // Source is NGram
                } else {

                    if(isUndef(bipartiteN2D[source])) {
                        bipartiteN2D[source] = {
                            label: Nodes[source].label,
                            neighbours: []
                        };                    
                    }
                    if(isUndef(bipartiteD2N[target])) {
                        bipartiteD2N[target] = {
                            label: Nodes[target].label,
                            neighbours: []
                        };                    
                    }
                    bipartiteN2D[source].neighbours.push(target);
                    bipartiteD2N[target].neighbours.push(source);
                }
            }

        }
    }
}




function JSONFile( URL ) {


    
    return $.ajax({
        type: 'GET',
        url: URL,
        contentType: "application/json",
        async: true,
        success : function(data) {
            pr("nodes:")
            pr(data.nodes)
            pr("---------")
            pr("links: ")
            pr(data.links)
            if(!isUndef(getUrlParam.seed))seed=getUrlParam.seed;

            parseSimpleJSON(data,seed)
        },
        error: function(){ 
            pr("Page Not found. parseCustom, inside the IF");
        }
    });

}


function parseSimpleJSON( data , seed ) {

    var i, j, k;
    rand=new RVUniformC(seed);                     
    //partialGraph.emptyGraph();
    // Parse Attributes
    // This is confusing, so I'll comment heavily
    var nodesAttributes = [];   // The list of attributes of the nodes of the graph that we build in json
    var edgesAttributes = [];   // The list of attributes of the edges of the graph that we build in json
    //var attributesNodes = gexf.getElementsByTagName('attributes');  // In the gexf (that is an xml), the list of xml nodes 'attributes' (note the plural 's')
    
    var nodesNodes = data.nodes // The list of xml nodes 'nodes' (plural)

    labels = [];
    numberOfDocs=0;
    numberOfNGrams=0;
    
    //Manually assigning ONE category
    categories[catSoc]=catSoc;
    categoriesIndex[0]=catSoc;


    for(var i in nodesNodes) {

        var color, label;
        if(isUndef(nodesNodes[i].color)) color = "#800000";
        if(isUndef(nodesNodes[i].label)) label = "node_"+i;
        
        var node = ({
            id: i ,
            label:label, 
            size:1, 
            x:rand.getRandom(), 
            y:rand.getRandom(), 
            type:catSoc,
            htmlCont:"",
            color:color
        });  // The graph node
        pr(node)
        Nodes[i] = node;
        partialGraph.addNode( i , node );  
    }

    var edgeId = 0;
    var edgesNodes = data.links;
    for(var i in edgesNodes) {
        var source = edgesNodes[i].source;
        var target = edgesNodes[i].target;
        var indice=source+";"+target;

        var edge = {
                id:         indice,
                sourceID:   source,
                targetID:   target,
                lock : false,
                label:      "",
                weight: (edgesNodes[i].w)?edgesNodes[i].w:1
        };

        if(edge.weight < minEdgeWeight) minEdgeWeight= edge.weight;
        if(edge.weight > maxEdgeWeight) maxEdgeWeight= edge.weight;


        idS=Nodes[edge.sourceID].type;
        idT=Nodes[edge.targetID].type;


        if(idS==catSoc && idT==catSoc) {

            edge.label = "nodes1";

            if(isUndef(nodes1[source])) {
                nodes1[source] = {
                    label: Nodes[source].label,
                    neighbours: []
                };                    
            }
            if(isUndef(nodes1[target])) {
                nodes1[target] = {
                    label: Nodes[target].label,
                    neighbours: []
                };                    
            }   
            nodes1[source].neighbours.push(target);
            nodes1[target].neighbours.push(source);


            Edges[indice] = edge;
            partialGraph.addEdge(indice,source,target,edge);
        }
    }


}


function extractFromJson(data,seed){
    var i, j, k;
    rand=new RVUniformC(seed);                     
    //partialGraph.emptyGraph();
    // Parse Attributes
    // This is confusing, so I'll comment heavily
    var nodesAttributes = [];   // The list of attributes of the nodes of the graph that we build in json
    var edgesAttributes = [];   // The list of attributes of the edges of the graph that we build in json
    //var attributesNodes = gexf.getElementsByTagName('attributes');  // In the gexf (that is an xml), the list of xml nodes 'attributes' (note the plural 's')
    
    var nodesNodes = data.nodes // The list of xml nodes 'nodes' (plural)
    labels = [];
    numberOfDocs=0;
    numberOfNGrams=0;

    for (var uid in data.ID) egonode[uid] = data.ID[uid]
    
    //Manually assigning categories
    categories[catSoc]=catSoc;
    categories[catSem]=catSem;
    categoriesIndex[0]=catSoc;
    categoriesIndex[1]=catSem;

    for(var i in nodesNodes) {
        if(nodesNodes[i].color) {
            colorRaw = nodesNodes[i].color.split(",");
            color = '#'+sigma.tools.rgbToHex(
                    parseFloat(colorRaw[2]),
                    parseFloat(colorRaw[1]),
                    parseFloat(colorRaw[0]));
                    //Colors inverted... Srsly??
        } else color = "#800000";
        
        var node = ({
            id:i,
            label:nodesNodes[i].label, 
            size:1, 
            x:rand.getRandom(), 
            y:rand.getRandom(), 
            // x:Math.random(),
            // y:Math.random(),
            type:"",
            htmlCont:"",
            color:color
        });  // The graph node
        if(nodesNodes[i].type=="Document"){
            node.htmlCont = nodesNodes[i].content;
            node.type="Document";
            node.shape="square";
            numberOfDocs++;
            node.size=desirableScholarSize;
            node.CC = nodesNodes[i].CC;
            node.ACR = nodesNodes[i].ACR;
        }
        else {
            node.type="NGram";
            numberOfNGrams++;
            node.size=parseInt(nodesNodes[i].term_occ).toFixed(2);
            if(parseInt(node.size) < parseInt(minNodeSize)) minNodeSize= node.size;
            if(parseInt(node.size) > parseInt(maxNodeSize)) maxNodeSize= node.size;
        }
        Nodes[i] = node;
    }

    for(var i in Nodes){
        if(Nodes[i].type=="NGram") {
            normalizedSize=desirableNodeSizeMIN+(Nodes[i].size-1)*((desirableNodeSizeMAX-desirableNodeSizeMIN)/(parseInt(maxNodeSize)-parseInt(minNodeSize)));
            Nodes[i].size = ""+normalizedSize;
            
            nodeK = Nodes[i];
            otherGraph.addNode(i,nodeK);  
        } 
        else {
            partialGraph.addNode(i,Nodes[i]);  
            updateSearchLabels(i,Nodes[i].label,Nodes[i].type);
        }
    }
    
    var edgeId = 0;
    var edgesNodes = data.links;
    for(var i in edgesNodes) {
        var source = edgesNodes[i].s;
        var target = edgesNodes[i].t;
        var indice=source+";"+target;
        
        var edge = {
                id:         indice,
                sourceID:   source,
                targetID:   target,
                lock : false,
                label:      "",
                weight: edgesNodes[i].w
            };
        if(edge.weight < minEdgeWeight) minEdgeWeight= edge.weight;
        if(edge.weight > maxEdgeWeight) maxEdgeWeight= edge.weight;
        Edges[indice] = edge;


        idS=Nodes[edge.sourceID].type;
        idT=Nodes[edge.targetID].type;


        if(idS==catSoc && idT==catSoc){  

            edge.label = "nodes1";

            if(isUndef(nodes1[source])) {
                nodes1[source] = {
                    label: Nodes[source].label,
                    neighbours: []
                };                    
            }
            if(isUndef(nodes1[target])) {
                nodes1[target] = {
                    label: Nodes[target].label,
                    neighbours: []
                };                    
            }   
            nodes1[source].neighbours.push(target);
            nodes1[target].neighbours.push(source);

            // social edges = 1
            Edges[indice].bweight = edgesNodes[i].w;//realweight just in bigraph-weight
            edge.weight = 1; 

            partialGraph.addEdge(indice,source,target,edge);
        }
        
        
        if(idS==catSem && idT==catSem){ 
            edge.label = "nodes2";

            if(isUndef(nodes2[source])) {
                nodes2[source] = {
                    label: Nodes[source].label,
                    neighbours: []
                };                    
            }
            if(isUndef(nodes2[target])) {
                nodes2[target] = {
                    label: Nodes[target].label,
                    neighbours: []
                };                    
            }
            nodes2[source].neighbours.push(target);
            nodes2[target].neighbours.push(source);
        
        	otherGraph.addEdge(indice,source,target,edge);
        }
        
        
        if((idS==catSoc && idT==catSem)||(idS==catSem && idT==catSoc)) {
            edge.label = "bipartite";

            s = edge.sourceID

            // // Source is Document
            if(Nodes[s].type == catSoc) {

                if(isUndef(bipartiteD2N[source])) {
                    bipartiteD2N[source] = {
                        label: Nodes[source].label,
                        neighbours: []
                    };                    
                }
                if(isUndef(bipartiteN2D[target])) {
                    bipartiteN2D[target] = {
                        label: Nodes[target].label,
                        neighbours: []
                    };                    
                }

                bipartiteD2N[source].neighbours.push(target);
                bipartiteN2D[target].neighbours.push(source);

            // // Source is NGram
            } else {

                if(isUndef(bipartiteN2D[source])) {
                    bipartiteN2D[source] = {
                        label: Nodes[source].label,
                        neighbours: []
                    };                    
                }
                if(isUndef(bipartiteD2N[target])) {
                    bipartiteD2N[target] = {
                        label: Nodes[target].label,
                        neighbours: []
                    };                    
                }
                bipartiteN2D[source].neighbours.push(target);
                bipartiteD2N[target].neighbours.push(source);
            }
        }
            
    }
}
