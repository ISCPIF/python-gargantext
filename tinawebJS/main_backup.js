//  === monitor windows resize === //
var counterrrr=0;
$( window ).resize(function() {
  counterrrr++;
  $("#log").html("redimension nro: "+counterrrr);
  sigmaLimits();
});//  === / monitor windows resize === //




mainfile = (isUndef(getUrlParam.file))?false:true;
//  === [what to do at start] === //
if (mainfile) {

	if(!isUndef(getUrlParam.file)){
	    $.doTimeout(30,function (){

            var filename = getUrlParam.file;
            if( filename.indexOf(".json") > -1 ) {
                bringTheNoise( filename , "mono");
                
            } else {
                listGexfs();
        		parse(getUrlParam.file);
        		nb_cats = scanCategories();  
        		pr("nb_cats: "+nb_cats);
        		
                graphtype=(nb_cats==1)?"mono":"bi";
        		bringTheNoise(getUrlParam.file,graphtype);
        		
        		$.doTimeout(30,function (){
        		    if(!isUndef(gexfDict[getUrlParam.file])){
        		        $("#currentGraph").html(gexfDict[getUrlParam.file]);
        		    } else $("#currentGraph").html(getUrlParam.file);
        		    scanDataFolder();
                    listGexfs();
        		});            
            }
	    });
	} else {
	    window.location.href=window.location.origin+window.location.pathname+"?file="+mainfile;
	}
} //url-mode 
else {

    if(isUndef(getUrlParam.nodeidparam)) {
        pr("do nothing, 'cause don't wanna");
        // pr(getUrlParam.nodeidparam)
        // $('#mainmodal').modal('show');
        // $("#my-text-input").tokenInput("try.json");
        //    pr("doing something 'cause i'm a doer"); mainfile=true;
	    // bringTheNoise("data/140907Syneco.gexf","mono");
        // scanCategories();
    } else {

	    if(getUrlParam.nodeidparam.indexOf("__")===-1){
    		//gexfPath = "php/bridgeClientServer_filter.php?query="+getUrlParam.nodeidparam;
            param=getUrlParam.nodeidparam;
            // pr(param)
            bringTheNoise(param,"filtermode");

	    } else {
    		param=getUrlParam.nodeidparam;
            pr(param)
            bringTheNoise(param,"unique_id");
	    }
    }
}//  === [ / what to do at start ] === //


//just CSS
function sigmaLimits(){
    pr("\t*** sigmaLimits()")
    
    pw=$('#sigma-example').width();
    ph=$('#sigma-example').height();    
    pr("\t\tprevsigma:("+pw+","+ph+")");
    
    sidebar=$('#leftcolumn').width();
    anchototal=$('#fixedtop').width();
    altototal=$('#leftcolumn').height();
    altofixtop=$('#fixedtop').height()
    altodeftop=$('#defaultop').height()
    $('#sigma-example').width(anchototal-sidebar);
    $('#sigma-example').height(altototal-altofixtop-altodeftop-4);
    
    pw=$('#sigma-example').width();
    ph=$('#sigma-example').height();
    pr("\t\tnowsigma:("+pw+","+ph+")");
}

function bringTheNoise(pathfile,type){
    
    $("#semLoader").hide();


    // $('.selectpicker').selectpicker();


    //  === get width and height   === //
    sigmaLimits();
    
    //  === sigma canvas resize  with previous values === //
    partialGraph = sigma.init(document.getElementById('sigma-example'))
    .drawingProperties(sigmaJsDrawingProperties)
    .graphProperties(sigmaJsGraphProperties)
    .mouseProperties(sigmaJsMouseProperties);

    //dummy graph (semantic layouting in background)
    otherGraph = sigma.init(document.getElementById('sigma-othergraph'));

    //  ===  resize topbar and tweakbar  === //
    var body=document.getElementsByTagName('body')[0];
    body.style.paddingTop="41px";


    $('.etabs').click(function(){
        $.doTimeout(500,function () {
            $("#opossiteNodes").readmore({maxHeight:200}); 
            $("#sameNodes").readmore({maxHeight:200}); 
        });
    });

    $("#changetype").click(function(){
    	pr("")
    	pr(" ############  changeTYPE click");
		printStates()
        partialGraph.stopForceAtlas2();
        changeType();

        $.doTimeout(500,function (){
            $('.etabs a[href="#tabs1"]').trigger('click');
        });

		printStates()
    	pr(" ############  / changeTYPE click");
    	pr("")
    });


    $("#changelevel").click(function(){
    	pr("")
    	pr(" ############  changeLEVEL click");
    	printStates()

        changeLevel();
        // $("#tabs1").click()

        printStates()
    	pr(" ############  / changeLEVEL click");
    	pr("")
    });

    //  ===  un/hide leftpanel  === //
    $("#aUnfold").click(function(e) {
        //SHOW leftcolumn
        sidebar = $("#leftcolumn");
        fullwidth=$('#fixedtop').width();
        e.preventDefault();
        // $("#wrapper").toggleClass("active");
        if(parseFloat(sidebar.css("right"))<0){            
            $("#aUnfold").attr("class","rightarrow"); 
            sidebar.animate({
                "right" : sidebar.width()+"px"
            }, { duration: 400, queue: false }); 

            $("#ctlzoom").animate({
                    "right": (sidebar.width()+10)+"px"
            }, { duration: 400, queue: false }); 
               
            // $('#sigma-example').width(fullwidth-sidebar.width());
            $('#sigma-example').animate({
                    "width": fullwidth-sidebar.width()+"px"
            }, { duration: 400, queue: false }); 
            setTimeout(function() {
                  partialGraph.resize();
                  partialGraph.refresh();
            }, 400);
        } 
        else {
            //HIDE leftcolumn
            $("#aUnfold").attr("class","leftarrow");
            sidebar.animate({
                "right" : "-" + sidebar.width() + "px"
            }, { duration: 400, queue: false });

            $("#ctlzoom").animate({
                    "right": "0px"
            }, { duration: 400, queue: false }); 

                // $('#sigma-example').width(fullwidth);
            $('#sigma-example').animate({
                    "width": fullwidth+"px"
            },{ duration: 400, queue: false });
            setTimeout(function() {
                  partialGraph.resize();
                  partialGraph.refresh();
            }, 400);
            
        }   
    });


    // $("#statsicon").click(function(){
    //     $('#statsmodal').modal('show');
    // });
    

    //  === start minimap library... currently off  === //
    startMiniMap();
    

    console.log("parsing...");    
    // < === EXTRACTING DATA === >
    if(mainfile) {
        pr("mainfile: "+mainfile)

        if(gexfDict[pathfile]) $("#network").html(gexfDict[pathfile]);
        else $("#network").html(pathfile);

    	// $('#modalloader').modal('show');
	    parse(decodeURIComponent(pathfile));

	    if(type=="mono") {

	    	$("#changetype").hide();

            if( pathfile.indexOf(".json") > -1 ) {
                JSONFile( pathfile )
            } else {
                onepartiteExtract(); 
            }

            pushSWClick("social");

            $("#taboppos").remove();
            $.doTimeout(500,function (){
                $('.etabs a[href="#tabs2"]').trigger('click');
            });

            pr(partialGraph._core.graph.nodes.length)
            pr(partialGraph._core.graph.edges.length)
	    } 

        if(type=="bi")  {

            semanticConverged=true;
            pr("here in fullextract")
            fullExtract();
            pushSWClick("social");
            pr(partialGraph._core.graph.nodes.length)
            pr(partialGraph._core.graph.edges.length)
        }


        partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, 0.8).draw(2,2,2);
        theListeners(); 
        $("#closeloader").click(); 

    } else {
      // 
        var theurl,thedata,thename;

    	$('#modalloader').modal('show');
    	
	    if(type=="unique_id") {
		    pr("bring the noise, case: unique_id");
            pr(getClientTime()+" : DataExt Ini");
            // < === DATA EXTRACTION === >
            theurl = bridge["forNormalQuery"]
            thedata = "unique_id="+getUrlParam.nodeidparam+"&it="+iterationsFA2;
            thename = true;
	    }


        if (type=="filtermode") {
            pr("bring the noise, case: multipleQuery");
            pr(getClientTime()+" : DataExt Ini");
            theurl = bridge["forFilteredQuery"];
            thedata = "query="+getUrlParam.nodeidparam;
            thename = false;
            thedata = thedata.replace("#","_char_");//possible bugfix
        }

        // Assigning name for the network
        if (thename) thename = getUrlParam.nodeidparam.replace(/\_/g, ' ').toUpperCase();
        else {
            elements = []
            queryarray = JSON.parse(getUrlParam.nodeidparam)
            for(var i in queryarray) {
                item = queryarray[i]
                if(Array.isArray(item) && item.length>0) {
                    for(var j in item) elements.push(item[j])
                }
            }
            thename = '"'+elements.join('" , "')+'"';
        }

        SigmaLayouting( theurl , thedata , thename );
    }  
}

//http://communityexplorer.org/explorerjs.html?nodeidparam={%22categorya%22%3A%22Keywords%22%2C%22categoryb%22%3A%22Scholars%22%2C%22tags%22%3A[%22%23resident%22]}


function theListeners(){
    pr("in THELISTENERS");
    // leftPanel("close");
    $("#closeloader").click();//modal.hide doesnt work :c

    cancelSelection(false);        
    $("#tips").html(getTips());
    //$('#sigma-example').css('background-color','white');
    $("#category-B").hide();
    $("#labelchange").hide();
    $("#availableView").hide(); 
    showMeSomeLabels(6);
    initializeMap();
    updateMap();
    updateDownNodeEvent(false);
    partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, 0.8).draw(2,2,2);
    $("#saveAs").click(function() {        
        $('#savemodal').modal('show');
    });
    
    /******************* /SEARCH ***********************/
    $.ui.autocomplete.prototype._renderItem = function(ul, item) {
        var searchVal = $("#searchinput").val();
        var desc = extractContext(item.desc, searchVal);
        // pr("desc:")
        // pr(desc)
        return $('<li onclick=\'var s = "'+item.label+'"; search(s);$("#searchinput").val(strSearchBar);\'></li>')
        .data('item.autocomplete', item)
        .append("<a><span class=\"labelresult\">" + item.label + "</span></a>" )
        .appendTo(ul);
    };

    $('input#searchinput').autocomplete({
        source: function(request, response) {
            matches = [];
            var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
            var results = $.grep(labels, function(e) {
                return matcher.test(e.label); //|| matcher.test(e.desc);
            });
            
            if (!results.length) {
                $("#noresults").text("Pas de résultats");
            } else {
                $("#noresults").empty();
            }
            matches = results.slice(0, maxSearchResults);
            response(matches);
            
        },
        minLength: minLengthAutoComplete
    }); 
   
    $('#searchinput').bind('autocompleteopen', function(event, ui) {
        $(this).data('is_open',true);
    });
    $('#searchinput').bind('autocompleteclose', function(event, ui) {
        $(this).data('is_open',false);
    });
    $("#searchinput").focus(function () {
        if ($(this).val() == strSearchBar) {
            $(this).val('');
        }
    });
    $("#searchinput").blur(function () {
        if ($(this).val() == '') {
            $(this).val(strSearchBar);
        }
    });
    
    // i've a list of coincidences and i press enter like a boss
    $("#searchinput").keydown(function (e) {
        if (e.keyCode == 13 && $("input#searchinput").data('is_open') === true) {
            // Search has several results and you pressed ENTER
            if(!is_empty(matches)) {                
                var coincidences = []
                for(j=0;j<matches.length;j++){
                	coincidences.push(matches[j].id)
                }
                $.doTimeout(30,function (){
                	MultipleSelection(coincidences , true);//true-> apply deselection algorithm
                    $("input#searchinput").val("");
                    $("input#searchinput").autocomplete( "close" );
                });
                //$("input#searchinput").trigger('autocompleteclose');
            }
        }
    });
    
    $("#searchinput").keyup(function (e) {
        if (e.keyCode == 13 && $("input#searchinput").data('is_open') !== true) {
            pr("search KEY UP");
            var exfnd = exactfind( $("#searchinput").val() )

			$.doTimeout(30,function (){
                	MultipleSelection(exfnd.id , true);//true-> apply deselection algorithm
                    $("input#searchinput").val("");
                    $("input#searchinput").autocomplete( "close" );
            });     
        }
    });
    
    $("#searchsubmit").click(function () {
        pr("searchsubmit CLICK");
        var s = $("#searchinput").val();
        search(s);
        $("#searchinput").val("");
    });
    /******************* /SEARCH ***********************/

    // button CENTER
    $("#lensButton").click(function () {
        partialGraph.position(0,0,1);
        partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, 0.8);
        partialGraph.refresh();
        // partialGraph.startForceAtlas2();
    });
    
    $('#sigma-example').dblclick(function(event) {
        pr("in the double click event");

        var targeted = [];
        
        if(cursor_size>0) {
                    //Multiple selection
            x1 = partialGraph._core.mousecaptor.mouseX;
            y1 = partialGraph._core.mousecaptor.mouseY;
            var counter=0;
            var actualSel=[];
            partialGraph.iterNodes(function(n){
                if(!n.hidden){
                    distance = Math.sqrt(
                        Math.pow((x1-parseInt(n.displayX)),2) +
                        Math.pow((y1-parseInt(n.displayY)),2)
                        );
                    if(parseInt(distance)<=cursor_size) {
                        counter++;
                        actualSel.push(n.id);                                
                    }
                }
            });

            targeted = actualSel;

        } else {

            targeted = partialGraph._core.graph.nodes.filter(function(n) {
                    return !!n['hover'];
                }).map(function(n) {
                    return n.id;
            });
        }

        if(!is_empty(targeted)) {
            graphTagCloudElem(targeted); 
        } else {
            if(!is_empty(selections)){
                cancelSelection(false);                
            }
        }
    });
    
    // minimap stuff
    // $("#overview")
    //    .mousemove(onOverviewMove)
    //    .mousedown(startMove)
    //    .mouseup(endMove)
    //    .mouseout(endMove)
    //    .mousewheel(onGraphScroll);
    
    $("#sigma-example")
        .mousemove(function(){
            if(!isUndef(partialGraph)) {
                if(cursor_size>0) trackMouse();
            }
        })
        .contextmenu(function(){
            return false;
        })
        .mousewheel(onGraphScroll)
        .mousedown(function(e){

            //left click!<- normal click
            if(e.which==1){


                var targeted = partialGraph._core.graph.nodes.filter(function(n) {
                    return !!n['hover'];
                }).map(function(n) {
                    return n.id;
                });
                
                partialGraph.dispatch(
                    e['type'] == 'mousedown' ?
                    'downgraph' :
                    'upgraph'
                );

                if(cursor_size>0) {
                    //Multiple selection
                    x1 = partialGraph._core.mousecaptor.mouseX;
                    y1 = partialGraph._core.mousecaptor.mouseY;
                    var counter=0;
                    var actualSel=[];
                    partialGraph.iterNodes(function(n){
                        if(!n.hidden){
                            distance = Math.sqrt(
                                Math.pow((x1-parseInt(n.displayX)),2) +
                                Math.pow((y1-parseInt(n.displayY)),2)
                                );
                            if(parseInt(distance)<=cursor_size) {
                                counter++;
                                actualSel.push(n.id);                                
                            }
                        }
                    });

                    if(checkBox) {

                        var dummyarray = {};
                        for(var i in actualSel) dummyarray[ actualSel[i] ]=1;
                        for(var i in selections) dummyarray[ i ]=1;

                        var countTypes = {};
                        for(var i in dummyarray) {
                            if( isUndef(countTypes[Nodes[i].type]) )
                                countTypes[Nodes[i].type]=1;
                            else
                                countTypes[Nodes[i].type]++;
                        }
                        cancelSelection(false);
                        cpCountTypes = Object.keys(countTypes);
                        if(cpCountTypes.length==1)
                            MultipleSelection(Object.keys(dummyarray) , true);//true-> apply deselection algorithm
                        else
                            MultipleSelection(actualSel , true);//true-> apply deselection algorithm

                    } else MultipleSelection(actualSel , true);//true-> apply deselection algorithm

                    // //The most brilliant way of knowing if an array is empty in the world of JavaScript
                    i=0; for(var s in actualSel) { i++; break;}

                    if(is_empty(actualSel) || i==0){ 
                        pr("cursor radius ON, mouseDown -> selecciones vacias"); 
                        cancelSelection(false);   
                        //$("#names").html("");
                        //$("#opossiteNodes").html("");
                        //$("#information").html("");
                        //$("#topPapers").html("");
                        //$("#tips").html(getTips());
                        //changeButton("unselectNodes");
                        //if(counter>0) graphResetColor();
                    }      

                } else {
                    //Unique Selection
                    partialGraph.dispatch(
                        e['type'] == 'mousedown' ? 'downnodes' : 'upnodes',
                        targeted
                        );
                }      
                
                partialGraph.draw();
                trackMouse();    
                

            }
        });


    $("#zoomSlider").slider({
        orientation: "vertical",
        value: partialGraph.position().ratio,
        min: sigmaJsMouseProperties.minRatio,
        max: sigmaJsMouseProperties.maxRatio,
        range: "min",
        step: 0.1,
        slide: function( event, ui ) {
        	// pr("*******lalala***********")
        	// pr(partialGraph.position().ratio)
        	// pr(sigmaJsMouseProperties.minRatio)
        	// pr(sigmaJsMouseProperties.maxRatio)
            partialGraph.zoomTo(
                partialGraph._core.width / 2, 
                partialGraph._core.height / 2, 
                ui.value);
        }
    });
    
    $("#zoomPlusButton").click(function () {
        partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, partialGraph._core.mousecaptor.ratio * 1.5);
        $("#zoomSlider").slider("value",partialGraph.position().ratio);
        return false;
    });

    $("#zoomMinusButton").click(function () {
        partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, partialGraph._core.mousecaptor.ratio * 0.5);
        $("#zoomSlider").slider("value",partialGraph.position().ratio);
        return false;
    });
    
    $("#edgesButton").click(function () {
        fa2enabled=true;
        if(!isUndef(partialGraph.forceatlas2)) {

            if(partialGraph.forceatlas2.active) {
                partialGraph.stopForceAtlas2();
                partialGraph.draw();
                return;
            } else {
                partialGraph.startForceAtlas2();
                return;
            }

        } else {
            partialGraph.startForceAtlas2();
            return;
        }
        
    });
    

    NodeWeightFilter ( "#sliderANodeWeight" ,  "Document",  "type" ,"size");

    EdgeWeightFilter("#sliderAEdgeWeight", "label" , "nodes1", "weight");


    //finished
    $("#sliderANodeSize").freshslider({
        step:1,
        min:1,
        max:25,
        value:1,
        bgcolor:"#27c470",
        onchange:function(value){
            $.doTimeout(100,function (){
                   partialGraph.iterNodes(function (n) {
                       if(Nodes[n.id].type==catSoc) {
                           n.size = parseFloat(Nodes[n.id].size) + parseFloat((value-1))*0.3;
                           sizeMult[catSoc] = parseFloat(value-1)*0.3;
                       }
                   });
                   partialGraph.draw();
            });
        }
    }); 

    //finished
    $("#sliderBNodeSize").freshslider({
        step:1,
        min:1,
        max:25,
        value:1,
        bgcolor:"#FFA500",
        onchange:function(value){
            $.doTimeout(100,function (){
                   partialGraph.iterNodes(function (n) {
                       if(Nodes[n.id].type==catSem) {
                           n.size = parseFloat(Nodes[n.id].size) + parseFloat((value-1))*0.3;
                           sizeMult[catSem] = parseFloat(value-1)*0.3;
                       }
                   });
                   partialGraph.draw();
            });
        }
    }); 


    //finished
    $("#unranged-value").freshslider({
        step: 1,
        min:cursor_size_min,
        max:cursor_size_max,
        value:cursor_size,
        onchange:function(value){
            // console.log("en cursorsize: "+value);
            cursor_size=value;
            if(cursor_size==0) partialGraph.draw();
        }
    });

}
// extractFromJson()
//      Social Spatialization
//          Semantic Spatialization
function SigmaLayouting( URL, DATA, NAME) {
	pr(URL+"?"+DATA)
    return $.ajax({
        type: 'GET',
        url: URL,
        data: DATA,
        contentType: "application/json",
        dataType: 'jsonp',
        async: true,
        success : function(data) {
        	        pr(data)
                    if(!isUndef(getUrlParam.seed))seed=getUrlParam.seed;
                    extractFromJson(data,seed);

                    // changeToMacro("social");
                    pr(getClientTime()+" : DataExt Fin");
                    // < === DATA EXTRACTED!! === >

                    if(fa2enabled==="off") $("#edgesButton").hide();
                    pushSWClick("social");
                    pr(partialGraph._core.graph.nodes.length)
                    pr(partialGraph._core.graph.edges.length)
                    nbnodes = partialGraph._core.graph.nodes.length
                    if(nbnodes>=400 && nbnodes<1000) {
                        snbnodes = nbnodes+"";
                        cut1 = snbnodes[0];
                        cut2 = snbnodes.length;
                        pr("cut1: "+cut1)
                        pr("cut2: "+cut2)
                        iterationsFA2 = Math.round(iterationsFA2/(cut1/cut2))
                    }
                    if(nbnodes>=1000) iterationsFA2 = 150;
                    pr("iterationsFA2: "+iterationsFA2)

                    $("#network").html(NAME);
                    // < === ASYNCHRONOUS FA2.JS === >

                    pr(getClientTime()+" : Ini FA2");
                    var ForceAtlas2 = new Worker("tinawebJS/asyncFA2.js");
                    ForceAtlas2.postMessage({
                        "nodes": partialGraph._core.graph.nodes,
                        "edges": partialGraph._core.graph.edges,
                        "it":iterationsFA2
                    });
                    ForceAtlas2.addEventListener('message', function(e) {
                        iterations=e.data.it;
                        nds=e.data.nodes;
                        for(var n in nds){
                            id=nds[n].id;
                            x=nds[n].x
                            y=nds[n].y
                            partialGraph._core.graph.nodes[n].x=x;
                            partialGraph._core.graph.nodes[n].y=y;
                            partialGraph._core.graph.nodesIndex[id].x=x
                            partialGraph._core.graph.nodesIndex[id].y=y
                            Nodes[id].x=x;
                            Nodes[id].y=y;
                        }
                        pr("\ttotalIterations: "+iterations)
                        pr(getClientTime()+" : Fin FA2");
                        console.log("Parsing and FA2 complete.");
                        pr("\n=================\n")
                        // < === ASYNCHRONOUS FA2.JS DONE!! === >


                        // [ calculate iterations for semanticgraph ]
                        pr(getClientTime()+" : Ini FA2 for SemanticGraph");
                        var cut1_,cut2_,iterationsFA2_=iterationsFA2;
                        pr(otherGraph._core.graph.nodes.length)
                        pr(otherGraph._core.graph.edges.length)
                        nbnodes = otherGraph._core.graph.nodes.length
                        if(nbnodes>=400 && nbnodes<1000) {
                            snbnodes = nbnodes+"";
                            cut1_ = snbnodes[0];
                            cut2_ = snbnodes.length;
                            pr("cut1 sem: "+cut1_)
                            pr("cut2 sem: "+cut2_)
                            iterationsFA2_ = Math.round(iterationsFA2/(cut1_/cut2_))
                        }
                        if(nbnodes>=1000) iterationsFA2_ = 150;
                        pr("iterationsFA2 sem: "+iterationsFA2_)
                        // [ / calculate iterations for semanticgraph ]


                        // [ semantic layouting ]
                        var ForceAtlas2_ = new Worker("tinawebJS/asyncFA2.js");
                        ForceAtlas2_.postMessage({ 
                            "nodes": otherGraph._core.graph.nodes,
                            "edges": otherGraph._core.graph.edges,
                            "it":iterationsFA2_
                        });
                        ForceAtlas2_.addEventListener('message', function(e) {
                            iterations=e.data.it;
                            nds=e.data.nodes;
                            for(var n in nds){
                                id=nds[n].id;
                                x=nds[n].x
                                y=nds[n].y
                                Nodes[id].x=x;
                                Nodes[id].y=y;
                            }

                            pr("\ttotalIterations: "+iterations)
                            pr(getClientTime()+" : Fin FA2 for SemanticGraph");


                            otherGraph.emptyGraph();
                            otherGraph = null;
                            $("#sigma-othergraph").html("");


                            semanticConverged = true;
                            $("#semLoader").hide();
                            if( NOW=="B" ) { 

                                changeToMacro("semantic");
                                partialGraph.draw();            
                                // $("#sliderBEdgeWeight").html("");
                                // $("#sliderBNodeWeight").html("");
                                $("#category-B").show();
                                EdgeWeightFilter("#sliderBEdgeWeight", "label" , "nodes2", "weight");
                                NodeWeightFilter ( "#sliderBNodeWeight"  , "NGram", "type" , "size");
                                $("#colorGraph").hide();
                            
                                
                            }
    
                            console.log("Parsing and FA2 complete for SemanticGraph.");
                        });
                        // [ / semantic layouting ]



                        theListeners(); 
                    }); 
        },
        error: function(){ 
            pr("Page Not found. parseCustom, inside the IF");
        }
    });

}
