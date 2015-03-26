/*
 * Customize as you want ;)
 */

function newPopup(url) {
    pr("newPopup : "+url)
	popupWindow = window.open(url,'popUpWindow','height=700,width=800,left=10,top=10,resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,directories=no,status=no')
}

function callGeomap(){
    db=JSON.stringify('community.db');
    if(is_empty(selections)){
        // jsonparams='["all"]';
        jsonparams='["unique_id"]&unique_id='+egonode[getUrlParam.nodeidparam];
    } else {

        N=getNodesByAtt(catSoc).length;

        nodesA = []
        nodesB = []
        socneigh = []
        for(var i in selections) {
            if(Nodes[i].type==catSoc) nodesA.push(i);
            if(Nodes[i].type==catSem) nodesB.push(i);
        }

        if(nodesA.length==0 && nodesB.length>0) socneigh = getArrSubkeys(opos,"key");
        if(nodesA.length>0 && nodesB.length>0) socneigh = getNeighs(nodesB,bipartiteN2D);

        kSels = {}

        for(var i in nodesA) {
            kSels[nodesA[i]] = 1;
        }
        for(var i in socneigh) {
            kSels[socneigh[i]] = 1;
        }

        k=Object.keys(kSels).length;

        // cats=(categoriesIndex.length);
        // arr={};
        // if(cats==2 && swclickActual=="social") {
        //     N=Object.keys(partialGraph._core.graph.nodes.filter(function(n){return n.type==catSoc})).length;
        //     arr=nodes1;
        // }
        // if(cats==2 && swclickActual=="semantic") {
        //     N=Object.keys(partialGraph._core.graph.nodes.filter(function(n){return n.type==catSem})).length;
        //     arr=nodes2;
        // }
        // if(cats==1)
        //     N=Object.keys(Nodes).length;
    
        // temp=getNeighs(Object.keys(selections),arr);
        // sel_plus_neigh=Object.keys(temp);
        // k=sel_plus_neigh.length;
        // // if(N==k) jsonparams='["all"]';
        pr ("N: "+N+" -  k: "+k)
        if(N==k) jsonparams='["unique_id"]&unique_id='+getUrlParam.nodeidparam;
        else jsonparams=JSON.stringify(Object.keys(kSels));
        
        //jsonparams=JSON.stringify(getSelections());
        //jsonparams = jsonparams.split('&').join('__and__');
    }
    pr('in callGeomap: db='+db+'&query='+jsonparams);
    initiateMap(db,jsonparams,"geomap2/");
    // $("#ctlzoom").hide();
    // $("#CurrentView").hide();
}

function clickInCountry( CC ) {
    // pr("in extras.js: you've clicked "+CC)
    var results = []
    
    for(var i in Nodes) {
        if( !isUndef(Nodes[i].CC) && Nodes[i].CC==CC) results.push(i)
    }

    $.doTimeout(20,function (){

        if(swclickActual=="social") {
            MultipleSelection(results , false); //false-> dont apply deselection algorithm
            return;
        }

        if(swclickActual=="semantic") {
            var oposresults = getNeighs2( results , bipartiteD2N );
            MultipleSelection(oposresults , false);
            return;
        }

    });
}

function callTWJS(){
    //    db=getCurrentDBforCurrentGexf();
    //    db=JSON.stringify(db);
    //    if(is_empty(selections)){
    //        jsonparams='["all"]';
    //    } else {
    //        jsonparams=JSON.stringify(getSelections());
    //        jsonparams = jsonparams.split('&').join('__and__');
    //    }    
    //    pr('in callGeomap: db='+db+'&query='+jsonparams);
    //    initiateMap(db,jsonparams,"geomap/"); //From GEOMAP submod
    $("#ctlzoom").show();
    $("#CurrentView").show();
}

function selectionToMap(){
    db=getCurrentDBforCurrentGexf();
    db=JSON.stringify(db);
    param='geomap/?db='+db+'';
    if(is_empty(selections)){
        newPopup('geomap/?db='+db+'&query=["all"]');
    } else {
        pr("selection to geomap:");
        jsonparams=JSON.stringify(getSelections());
        jsonparams = jsonparams.split('&').join('__and__');
        pr('geomap/?db='+db+'&query='+jsonparams);
        newPopup('geomap/?db='+db+'&query='+jsonparams);
    }
}

//DataFolderMode
function getCurrentDBforCurrentGexf(){
    folderID=dataFolderTree["gexf_idfolder"][decodeURIComponent(getUrlParam.file)];
    dbsRaw = dataFolderTree["folders"][folderID];
    dbsPaths=[];
    for(var i in dbsRaw){
        dbs = dbsRaw[i]["dbs"];
        for(var j in dbs){
            dbsPaths.push(i+"/"+dbs[j]);
        }
        break;
    }
    return dbsPaths;
}

//DataFolderMode
function getGlobalDBs(){
    graphdb=dataFolderTree["folders"];
    for(var i in graphdb){
        for(var j in graphdb[i]){
            if(j=="data") {
                maindbs=graphdb[i][j]["dbs"];
                for(var k in maindbs){
                    return jsonparams+"/"+maindbs[k];
                }
            }
        }
    }
}

//DataFolderMode
function getTopPapers(type){
    if(getAdditionalInfo){

        $("#topPapers").show();
    	var img = '<center><img src="'+window.location.origin+'/static/img/ajax-loader.gif" width="30%"></img></center>';
    	$("#topPapers").html(img);
        var pageurl = window.location.href.split("/")
        var cid;
        for(var i in pageurl) {
        	if(pageurl[i]=="corpus") {
        		cid=parseInt(i);
        		break;
        	}
        } 
        var corpus_id = pageurl[cid+1];

        pr("corpus_id: "+ corpus_id);

        var theids = []
        for(var i in selections) {
        	if(!Nodes[i].iscluster) {
        		theids.push(parseInt(Nodes[i].pk))
        	}
        }
        
        pr("the IDs of the selectioons")
        pr(theids)
        $.ajax({
            type: 'GET',
            url: window.location.origin+'/api/tfidf/'+corpus_id+'/'+theids.join("a"),
            //contentType: "application/json",
            //dataType: 'json',
            success : function(data){ 
            	pr(window.location.origin+'/api/tfidf/'+corpus_id+'/'+theids.join("a") )
            	var arraydata = $.parseJSON(data)
            	var output = "<ul style='padding: 0px; margin: 13px;'>"
            	for(var i in arraydata) {
            		var pub = arraydata[i]
            		var gquery = "http://www.google.com/#q="+pub["title"].replace(" "+"+")
            		var getpubAPI = window.location.origin+"/nodeinfo/"+pub["id"]

                    var ifjournal="",ifauthors="",ifkeywords="",ifdate="",iftitle="";

                    if(pub["journal"]) ifjournal = "<br>Published in <a>"+pub["journal"]+"</a>";
                    if(pub["authors"]) {
                        ifauthors = "By "+pub["authors"]+"";
                        if(pub["authors"] == "not found") {
                            if(pub["source"])
                                ifauthors = "By "+pub["source"]+"";
                            else ifauthors = ""
                        } else  ifauthors = ""
                    }
                    if(pub["fields"]) ifkeywords = "<br>Fields: "+pub["fields"];
                    if(pub["publication_date"]) ifdate = "<br>In "+pub["publication_date"].split(" ")[0];
                    
                    var jsstuff = "if(wnws_buffer!=null) {wnws_buffer.close();} "
                    var jsparams = 'height=700,width=800,left=10,top=10,resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,directories=no,status=no'
                    jsstuff += "wnws_buffer = window.open('"+getpubAPI+"', 'popUpWindow' , '"+jsparams+"')";

            		output += "<li><a onclick=\""+jsstuff+"\" target=_blank>"+pub["title"]+"</a>. "+ifauthors+". "+ifjournal+". "+ifkeywords+". "+ifdate+"\n";
            		output += '<a href="'+gquery+'" target=_blank><img title="Query to Google" src="'+window.location.origin+'/static/img/google.png"></img></a>'
            		output +="</li>\n";
            		// for(var j in pub) {
            		// 	if(j!="abstract")
            		// 		output += "<li><b>"+j+"</b>: "+pub[j]+"</li>\n";
            		// }
            		output += "<br>"
            	}
            	output += "</ul>"
                $("#topPapers").html(output);
                $("#topPapers").show();
            },
            error: function(){ 
                pr('Page Not found: getTopPapers()');
            }
        });
    }
}


//FOR UNI-PARTITE
function selectionUni(currentNode){
    pr("in selectionUni");
    if(checkBox==false && cursor_size==0) {
        highlightSelectedNodes(false);
        opossites = [];
        selections = [];
        partialGraph.refresh();
    }   
    
    if((typeof selections[currentNode.id])=="undefined"){
        selections[currentNode.id] = 1;
        currentNode.active=true;
    }
    else {
        delete selections[currentNode.id];               
        currentNode.active=false;
    }
    //highlightOpossites(nodes1[currentNode.id].neighbours);
    //        currentNode.color = currentNode.attr['true_color'];
    //        currentNode.attr['grey'] = 0;
    //        
    //
   

    partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, 0.8);
    partialGraph.refresh();
}

//JUST ADEME
function camaraButton(){
    $("#PhotoGraph").click(function (){
        
        //canvas=partialGraph._core.domElements.nodes;
        
        
        
        var nodesCtx = partialGraph._core.domElements.nodes;
        /*
        var edgesCtx = document.getElementById("sigma_edges_1").getContext('2d');
        
        var edgesImg = edgesCtx.getImageData(0, 0, document.getElementById("sigma_edges_1").width, document.getElementById("sigma_edges_1").height)
        
        nodesCtx.putImageData(edgesImg,0,0);
        
        
        
        
        //ctx.drawImage(partialGraph._core.domElements.edges,0,0)
        //var oCanvas = ctx;  
  */
        //div = document.getElementById("sigma_nodes_1").getContext('2d');
        //ctx = div.getContext("2d");
        //oCanvas.drawImage(partialGraph._core.domElements.edges,0,0);
        Canvas2Image.saveAsPNG(nodesCtx);
        
        /*
        Canvas2Image.saveAsJPEG(oCanvas); // will prompt the user to save the image as JPEG.   
        // Only supported by Firefox.  
  
        Canvas2Image.saveAsBMP(oCanvas);  // will prompt the user to save the image as BMP.  
  
  
        // returns an <img> element containing the converted PNG image  
        var oImgPNG = Canvas2Image.saveAsPNG(oCanvas, true);     
  
        // returns an <img> element containing the converted JPEG image (Only supported by Firefox)  
        var oImgJPEG = Canvas2Image.saveAsJPEG(oCanvas, true);   
                                                         
        // returns an <img> element containing the converted BMP image  
        var oImgBMP = Canvas2Image.saveAsBMP(oCanvas, true);   
  
  
        // all the functions also takes width and height arguments.   
        // These can be used to scale the resulting image:  
  
        // saves a PNG image scaled to 100x100  
        Canvas2Image.saveAsPNG(oCanvas, false, 100, 100);  
        */
    });
}


//JUST ADEME
function getChatFrame() {    
    content = '<div id="showChat" onclick="showhideChat();"><a href="#" id="aShowChat"> </a></div>';
    content += '<iframe src="'+ircUrl+'"'
    content += 'width="400" height="300"></iframe>';    
    $("#rightcolumn").html(content);
}


//JUST ADEME
function showhideChat(){
    
    cg = document.getElementById("rightcolumn");
    if(cg){
        if(cg.style.right=="-400px"){
            cg.style.right="0px";
        }
        else cg.style.right="-400px";
    }
}


function getTips(){    
    text = 
        "<br>"+
        "Basic Interactions:"+
        "<ul>"+
        "<li>Click on a node to select/unselect and get its information. In case of multiple selection, the button unselect clears all selections.</li>"+
        "<li>The switch button switch allows to change the view type.</li>"+
        "</ul>"+
        "<br>"+
        "Graph manipulation:"+
        "<ul>"+
        "<li>Link and node sizes indicate their strength.</li>"+
        "<li>To fold/unfold the graph (keep only strong links or weak links), use the 'edges filter' sliders.</li>"+
        "<li>To select a more of less specific area of the graph, use the 'nodes filter' slider.</li>"+
        "</ul>"+
        "<br>"+
        "Micro/Macro view:"+
        "<ul>"+
        "<li>To explore the neighborhood of a selection, either double click on the selected nodes, either click on the macro/meso level button. Zoom out in meso view return to macro view.</li>"+
        "<li>Click on the 'all nodes' tab below to view the full clickable list of nodes.</li>"+
        "</ul>";
    $("#tab-container").hide();
    return text;
}



//both obsolete
function closeDialog () {
    $('#windowTitleDialog').modal('hide'); 
}
function okClicked () {
    //document.title = document.getElementById ("xlInput").value;
    closeDialog ();
}
