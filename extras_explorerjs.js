/*
 * Customize as you want ;)
 */

function newPopup(url) {
	popupWindow = window.open(url,'popUpWindow','height=700,width=800,left=10,top=10,resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,directories=no,status=no')
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

function modify_ngrams( classname ) {
    console.clear()

    var corpus_id = getIDFromURL( "corpus" ) // not used
    var list_id = $("#list_id").val()
    var selected_ngrams = $.extend({}, selections)
    console.log( selected_ngrams )

    if(classname=="delete") {
        CRUD( corpus_id , "/keep" , [] , selected_ngrams , "DELETE" , function(result) {
            console.log(" Delete from Map-list: "+result)
            CRUD( list_id , "" , Object.keys(selected_ngrams).map(Number) , [] , "DELETE", function(result) {
                console.log(" Add to Stop-list "+result)
                cancelSelection(false)
                for(var i in selected_ngrams) {
                    partialGraph.dropNode( i )
                    delete Nodes[i]
                    delete partialGraph._core.graph.nodesIndex[i]
                }
                partialGraph.refresh()
                partialGraph.zoomTo(partialGraph._core.width / 2, partialGraph._core.height / 2, 0.8).draw();
            });
        });
    }

    // if(classname=="group") {
    //     CRUD( corpus_id , "/group" , [] , selected_ngrams , "PUT" , function(result) {
    //         console.log(" GROUP  "+result)
    //         CRUD( corpus_id , "/keep" , [] , selected_ngrams , "PUT" , function(result) {
    //         });
    //     });
    // }
}

function CRUD( parent_id , action , nodes , args , http_method , callback) {
    var the_url = window.location.origin+"/api/node/"+parent_id+"/ngrams"+action+"/"+nodes.join("+");
    the_url = the_url.replace(/\/$/, ""); //remove trailing slash
    console.log( the_url )
    console.log( args )
    if(nodes.length>0 || Object.keys(args).length>0) {
        $.ajax({
          method: http_method,
          url: the_url,
          data: args,
          beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          },
          success: function(data){
                console.log(http_method + " ok!!")
                console.log(nodes)
                console.log(data)
                callback("Success");
          },
          error: function(result) {
              console.log(result)
              callback("Fail");
          }
        });

    } else callback(false);
}
// = = = = = = = = = = = [ Clusters Plugin ] = = = = = = = = = = = // 

    // Execution:    ChangeGraphAppearanceByAtt( true )
    // It scans the existing node-attributes and t keeps only those which are Numeric.
    //  then, add the button in the html with the sigmaUtils.clustersBy(x) listener.
    //TODO: move to ClustersPlugin.js or smntng
    function ChangeGraphAppearanceByAtt( manualflag ) {

        if ( !isUndef(manualflag) && !colorByAtt ) colorByAtt = manualflag;
        if(!colorByAtt) return;

        // Seeing all the possible attributes!
        var AttsDict = {}    
        var Atts_2_Exclude = {}
        var v_nodes = getVisibleNodes();
        for (var i in v_nodes) {
            if(!v_nodes[i].hidden) {

                var id = v_nodes[i].id;

                for(var a in Nodes[id].attributes) {
                    var someatt = Nodes[id].attributes[a]

                    // Identifying the attribute datatype: exclude strings and objects
                    if ( ( typeof(someatt)=="string" && isNaN(Number(someatt)) ) || typeof(someatt)=="object" ) {
                        if (!Atts_2_Exclude[a]) Atts_2_Exclude[a]=0;
                        Atts_2_Exclude[a]++;
                    } 
                }

                var possible_atts = [];
                if (!isUndef(Nodes[id].attributes)) 
                    possible_atts = Object.keys(Nodes[id].attributes)

                if(!isUndef(v_nodes[i].degree))
                    possible_atts.push("degree")
                possible_atts.push("clust_louvain")

                for(var a in possible_atts){
                    if ( !AttsDict[ possible_atts[a] ] ) 
                        AttsDict[ possible_atts[a] ] = 0
                    AttsDict[ possible_atts[a] ] ++;
                } 
                
            }
        }

        for(var i in Atts_2_Exclude) 
            delete AttsDict[i];

        var AttsDict_sorted = ArraySortByValue(AttsDict, function(a,b){
            return b-a
        });

        // console.log( AttsDict_sorted )


        var div_info = "";            

        if( $( ".colorgraph_div" ).length>0 )          
            div_info += '<ul id="colorGraph" class="nav navbar-nav navbar-right">'

        div_info += ' <li class="dropdown">'
        div_info += '<a href="#" class="dropdown-toggle" data-toggle="dropdown">'
        div_info += '        <img title="Set Colors" src="/static/js/libs/img2/colors.png" width="20px"><b class="caret"></b></img>'
        div_info += '</a>'
        div_info += '  <ul class="dropdown-menu">'

        for (var i in AttsDict_sorted) {
            var att_s = AttsDict_sorted[i].key;
            var att_c = AttsDict_sorted[i].value;
            var the_method = "clustersBy"
            if(att_s.indexOf("clust")>-1) the_method = "colorsBy"
            div_info += '<li><a href="#" onclick=\''+the_method+'("'+att_s+'" , "color")\'>By '+att_s+'('+att_c+')'+'</a></li>'
            pr('<li><a href="#" onclick=\''+the_method+'("'+att_s+'" , "color")\'>By '+att_s+'('+att_c+')'+'</a></li>')
        }
        div_info += '  </ul>'
        div_info += ' </li>'

        console.log('$( ".colorgraph_div" ).length')
        console.log($( ".colorgraph_div" ).length)

        if( $( ".colorgraph_div" ).length>0 )   {
            div_info += '</ul>'
            $( div_info ).insertAfter(".colorgraph_div");
            $( ".colorgraph_div" ).remove();
        } else {
            $("#colorGraph").html(div_info)
        }





        div_info = "";            

        if( $( ".sizegraph_div" ).length>0 )          
            div_info += '<ul id="sizeGraph" class="nav navbar-nav navbar-right">'

        div_info += ' <li class="dropdown">'
        div_info += '<a href="#" class="dropdown-toggle" data-toggle="dropdown">'
        div_info += '        <img title="Set Sizes" src="/static/js/libs/img2/NodeSize.png" width="20px"><b class="caret"></b></img>'
        div_info += '</a>'
        div_info += '  <ul class="dropdown-menu">'

        for(var i in AttsDict) {
            if( i.indexOf("clust")>-1 )
                delete AttsDict[i]
        }
        var AttsDict_sorted = ArraySortByValue(AttsDict, function(a,b){
            return b-a
        });

        console.clear()
        console.log( AttsDict_sorted )
        for (var i in AttsDict_sorted) {
            var att_s = AttsDict_sorted[i].key;
            var att_c = AttsDict_sorted[i].value;
            var the_method = "clustersBy"
            if(att_s.indexOf("clust")>-1) the_method = "colorsBy"
            div_info += '<li><a href="#" onclick=\''+the_method+'("'+att_s+'" , "size")\'>By '+att_s+'('+att_c+')'+'</a></li>'
            pr('<li><a href="#" onclick=\''+the_method+'("'+att_s+'" , "size")\'>By '+att_s+'('+att_c+')'+'</a></li>')
        }
        div_info += '<li><a href="#" onclick=\''+"clustersBy"+'("default" , "size")\'>By '+"default"+'('+AttsDict_sorted[0].value+')'+'</a></li>'
        console.log('<li><a href="#" onclick=\''+"clustersBy"+'("default" , "size")\'>By '+"default"+'('+AttsDict_sorted[0].value+')'+'</a></li>' )
        div_info += '  </ul>'
        div_info += ' </li>'

        console.log('$( ".sizegraph_div" ).length')
        console.log($( ".sizegraph_div" ).length)
        

        if( $( ".sizegraph_div" ).length>0 )   {
            div_info += '</ul>'
            $( div_info ).insertAfter(".sizegraph_div");
            $( ".sizegraph_div" ).remove();
        } else {
            $("#sizeGraph").html(div_info)
        }
    }

    // It scans the current visible nodes|edges. It considers n-id and e(s,t,w)
    //  then, it runs external library jLouvain()
    //TODO: move to ClustersPlugin.js or smntng
    function RunLouvain() {

      var node_realdata = []
      var nodesV = getVisibleNodes()
      for(var n in nodesV)
        node_realdata.push( nodesV[n].id )

      var edge_realdata = []
      var edgesV = getVisibleEdges()
      for(var e in edgesV) {
        var st = edgesV[e].id.split(";")
        var info = {
            "source":st[0],
            "target":st[1],
            "weight":edgesV[e].weight
        }
        edge_realdata.push(info)
      }
        var community = jLouvain().nodes(node_realdata).edges(edge_realdata);  
        var results = community();
        for(var i in results)
            Nodes[i].attributes["clust_louvain"]=results[i]
    }

    // Highlight nodes belonging to cluster_i when you click in thecluster_i of the legend
    //TODO: move to ClustersPlugin.js or smntng
    function HoverCluster( ClusterCode ) {
        console.log( ClusterCode )

        var raw = ClusterCode.split("||")
        var Type=raw[0], Cluster=raw[1], clstID=Number(raw[2]);

        var present = partialGraph.states.slice(-1)[0]; // Last
        var type_t0 = present.type;    
        var str_type_t0 = type_t0.map(Number).join("|")
        console.log( "\t"+str_type_t0)


        greyEverything();

        var nodes_2_colour = {};
        var edges_2_colour = {};

        var nodesV = getVisibleNodes()
        for(var i in nodesV) {
            var n = nodesV[i]
            n.forceLabel = false;
            var node = Nodes[n.id]
            if ( node.type==Type && !isUndef(node.attributes[Cluster]) && node.attributes[Cluster]==clstID ) {
                // pr( n.id + " | " + Cluster + " : " + node.attributes[Cluster] )
                nodes_2_colour[n.id] = n.degree;
            }
        }


        for(var s in nodes_2_colour) {
            if(Relations[str_type_t0] && Relations[str_type_t0][s] ) {
                neigh = Relations[str_type_t0][s]
                if(neigh) {
                    for(var j in neigh) {
                        t = neigh[j]
                        if( !isUndef(nodes_2_colour[t]) ) {
                            edges_2_colour[s+";"+t]=true;
                            edges_2_colour[t+";"+s]=true;
                        }
                    }
                }
            }
        }


        for(var i in nodes_2_colour) {
            n = partialGraph._core.graph.nodesIndex[i]
            if(n) {
                n.color = n.attr['true_color'];
                n.attr['grey'] = 0;
            }
        }


        for(var i in edges_2_colour) {
            an_edge = partialGraph._core.graph.edgesIndex[i]
            if(!isUndef(an_edge) && !an_edge.hidden){
                // pr(an_edge)
                an_edge.color = an_edge.attr['true_color'];
                an_edge.attr['grey'] = 0;
            }
        }





        var nodes_2_label = ArraySortByValue(nodes_2_colour, function(a,b){
            return b-a
        });

        for(var n in nodes_2_label) {
            if(n==4) 
                break
            var ID = nodes_2_label[n].key
            partialGraph._core.graph.nodesIndex[ID].forceLabel = true;
        }



        overNodes=true;
        partialGraph.draw()
    }

    // From the cluster information of JSON|GEXF i build the Clusters Legend div.
    //      daclass = "clust_default" | "clust_louvain" | "clust_x" ...
    //TODO: move to ClustersPlugin.js or smntng
    function set_ClustersLegend ( daclass ) {
        //partialGraph.states.slice(-1)[0].LouvainFait = true

        if( daclass=="clust_default" && Clusters.length==0)
            return false;

        $("#legend_for_clusters").removeClass( "my-legend" )
        $("#legend_for_clusters").html("")

        var ClustNB_CurrentColor = {}
        var nodesV = getVisibleNodes()
        for(var i in nodesV) {
            n = nodesV[i]
            color = n.color
            type = Nodes[n.id].type
            clstNB = Nodes[n.id].attributes[daclass]
            ClustNB_CurrentColor[type+"||"+daclass+"||"+clstNB] = color
        }

        LegendDiv = ""
        LegendDiv += '    <div class="legend-title">Map Legend</div>'
        LegendDiv += '    <div class="legend-scale">'
        LegendDiv += '      <ul class="legend-labels">'

        if (daclass=="clust_louvain")
            daclass = "louvain"
        OrderedClustDicts = Object.keys(ClustNB_CurrentColor).sort()
        if( daclass.indexOf("clust")>-1 ) {
            for(var i in OrderedClustDicts) {
                var IDx = OrderedClustDicts[i]
                var raw = IDx.split("||")
                var Type = raw[0]
                var ClustType = raw[1]
                var ClustID = raw[2]
                var Color = ClustNB_CurrentColor[IDx]
                pr ( Color+" : "+ Clusters[Type][ClustType][ClustID] )
                var ColorDiv = '<span style="background:'+Color+';"></span>'
                LegendDiv += '<li onclick=\'HoverCluster("'+IDx+'")\'>'+ColorDiv+ Clusters[Type][ClustType][ClustID]+"</li>"+"\n"
            }
        } else {
            for(var i in OrderedClustDicts) {
                var IDx = OrderedClustDicts[i]
                var Color = ClustNB_CurrentColor[IDx]
                // pr ( Color+" : "+ Clusters[Type][ClustType][ClustID] )
                var ColorDiv = '<span style="background:'+Color+';"></span>'
                LegendDiv += '<li onclick=\'HoverCluster("'+IDx+'")\'>'+ColorDiv+ IDx+"</li>"+"\n"
            }

        }
        LegendDiv += '      </ul>'
        LegendDiv += '    </div>'
        

        $("#legend_for_clusters").addClass( "my-legend" );
        $("#legend_for_clusters").html( LegendDiv )
    }

// = = = = = = = = = = = [ / Clusters Plugin ] = = = = = = = = = = = // 


// PHP-mode when you've a cortext db.
function getTopPapers_OriginalVersion(type){
    if(getAdditionalInfo){
        jsonparams=JSON.stringify(getSelections());
        bi=(Object.keys(categories).length==2)?1:0;
        var APINAME = "API_CNRS/"
        //jsonparams = jsonparams.replaceAll("&","__and__");
        jsonparams = jsonparams.split('&').join('__and__');
        //dbsPaths.push(getGlobalDBs());
        thisgexf=JSON.stringify(decodeURIComponent(getUrlParam.file));
        image='<img style="display:block; margin: 0px auto;" src="'+APINAME+'img/ajax-loader.gif"></img>';
        $("#tab-container-top").show();
        $("#topPapers").show();
        $("#topPapers").html(image);
        $.ajax({
            type: 'GET',
            url: APINAME+'info_div.php',
            data: "type="+type+"&bi="+bi+"&query="+jsonparams+"&gexf="+thisgexf+"&index="+field[getUrlParam.file],
            //contentType: "application/json",
            //dataType: 'json',
            success : function(data){ 
                pr(APINAME+'info_div.php?'+"type="+type+"&bi="+bi+"&query="+jsonparams+"&gexf="+thisgexf+"&index="+field[getUrlParam.file]);
                $("#topPapers").html(data);
            },
            error: function(){ 
                pr('Page Not found: getTopPapers');
            }
        });
    }
}

// PHP-mode when you've a cortext db.
function getTopProposals(type , jsonparams , thisgexf) {

    type = "semantic";
    if(swclickActual=="social") {
        nodesA = []
        nodesB = []
        socneigh = []
        for(var i in selections) {
            if(Nodes[i].type==catSoc) nodesA.push(i);
            if(Nodes[i].type==catSem) nodesB.push(i);
        }

        if(nodesA.length>0 && nodesB.length==0) socneigh = getArrSubkeys(opos,"key");
        if(nodesA.length>0 && nodesB.length>0) socneigh = getNeighs(nodesA,bipartiteD2N);

        kSels = {}

        for(var i in nodesB) {
            kSels[nodesB[i]] = 1;
        }
        for(var i in socneigh) {
            kSels[socneigh[i]] = 1;
        }

        concepts = []
        for(var i in kSels) {
            concepts.push(Nodes[i].label)
        }
        jsonparams=JSON.stringify(concepts);

        jsonparams = jsonparams.split('&').join('__and__');
    }


    image='<img style="display:block; margin: 0px auto;" src="'+"API_pasteur/"+'img/ajax-loader.gif"></img>';
    $("#topProposals").show();
    $("#topProposals").html(image);
    $.ajax({
        type: 'GET',
        url: "API_pasteur/"+'info_div2.php',
        data: "type="+"semantic"+"&query="+jsonparams+"&gexf="+thisgexf,
        //contentType: "application/json",
        //dataType: 'json',
        success : function(data){ 
            pr("API_pasteur/"+'info_div2.php?'+"type="+"semantic"+"&query="+jsonparams+"&gexf="+thisgexf);
            $("#topProposals").html(data);
        },
        error: function(){ 
            pr('Page Not found: getTopProposals');
        }
    });
}



// Just for Garg
function genericGetTopPapers(theids , corpus_id , thediv) {
    if(getAdditionalInfo) {
        $("#"+thediv).show();
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
                    //  if(j!="abstract")
                    //      output += "<li><b>"+j+"</b>: "+pub[j]+"</li>\n";
                    // }
                    output += "<br>"
                }
                output += "</ul>"
                $("#"+thediv).html(output);
                $("#"+thediv).show();

                // $('#tab-container-top').easytabs({updateHash:false});

                
            },
            error: function(){ 
                pr('Page Not found: getTopPapers()');
            }
        });
    }
}

// Just for Garg: woops, override
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
                theids.push(parseInt(Nodes[i].id))
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
                // pr(window.location.origin+'/api/tfidf/'+corpus_id+'/'+theids.join("a") )
                // var arraydata = $.parseJSON(data)
                var output = "<ul style='padding: 0px; margin: 13px;'>"
                for(var i in data) {
                    var pub = data[i]
                    if(pub["title"]) {
                        var gquery = "http://www.google.com/#q="+pub["title"].replace(" "+"+")

                        var url_elems = window.location.href.split("/")
                        var url_mainIDs = {}
                        for(var i=0; i<url_elems.length; i++) {
                          if(url_elems[i]!="" && !isNaN(Number(url_elems[i]))) {
                            url_mainIDs[url_elems[i-1]] = Number(url_elems[i]);
                          }
                        }
                        var getpubAPI = window.location.origin+'/project/'+url_mainIDs["project"]+'/corpus/'+ url_mainIDs["corpus"] + '/document/'+pub["id"]
                        

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
                        //  if(j!="abstract")
                        //      output += "<li><b>"+j+"</b>: "+pub[j]+"</li>\n";
                        // }
                        output += "<br>"
                    }
                }
                output += "</ul>"
                $("#tab-container-top").show();
                // $('#tab-container-top').easytabs({updateHash:false});
                $("#topPapers").html(output);
            },
            error: function(){ 
                pr('Page Not found: getTopPapers()');
            }
        });


        // for(var i in corpusesList) {
        //     var c_id = i;
        //     var text = corpusesList[i]["name"]
        //     console.log(theid+" : "+text)
        //     genericGetTopPapers(theids , c_id , ("top_"+text) )
        // }
    }
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
// Just for Garg
function printCorpuses() {
    console.clear()
    console.log( "!!!!!!!! in printCorpuses() !!!!!!!! " )
    pr(corpusesList)

    var selected = $('input[name=optradio]:checked')[0].id.split("_")
    var sel_p = selected[0], sel_c=selected[1]
    
    var pageurl = window.location.href.split("/")
    var cid;
    for(var i in pageurl) {
        if(pageurl[i]=="corpus") {
            cid=parseInt(i);
            break;
        }
    } 
    var current_corpus = pageurl[cid+1];

    pr("corpus id, selected: "+corpusesList[sel_p]["corpuses"][sel_c]["id"])
    pr("current corpus: "+current_corpus)
    var the_ids = []
    the_ids.push( current_corpus )
    the_ids.push( corpusesList[sel_p]["corpuses"][sel_c]["id"] )

    $("#closecorpuses").click();

    var thenodes = []
    for(var i in partialGraph._core.graph.nodes) {
        thenodes.push(partialGraph._core.graph.nodes[i].id)
    }
    console.log( thenodes )
    $.ajax({
        type: 'GET',
        url: window.location.origin+'/api/corpusintersection/'+the_ids.join("a"),
        data: "nodeids="+JSON.stringify(thenodes),
        type: 'POST',
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
        success : function(data){
            console.log( "!!!!!!!! in printCorpuses() AJAX!!!!!!!! " )
        
            for(var i in Nodes) {
                if(data[i])
                    Nodes[i].attributes["inter"] = data[i]
                else
                    Nodes[i].attributes["inter"] = 0
            }
            cancelSelection(false)
            ChangeGraphAppearanceByAtt(true)

            console.log("YOLOYOLYOLYOYKOYYKYOY")
            clustersBy("inter" , "color")
            clustersBy("inter" , "size")

            
        },
        error: function(xhr, status, error) {
          var err = eval("(" + xhr.responseText + ")");
          console.log(err.Message);
        }
    });

    // $("#tab-container-top").html("");
    // var string = ""
    // string += "<ul class='etabs'>"+"\n";
    // string += "\t"+"<li id='tabmed' class='tab active'><a href='#tabs3'>Main Pubs</a></li>"+"\n";
    // for(var i in corpusesList) {
    //     var text = corpusesList[i]["name"]
    //     var c = corpusesList[i]["id"]
    //     string += "\t"+"<li id='tab_"+text+"' class='tab'><a href='#tabs"+c+"'>"+text+" Pubs</a></li>"+"\n";
    // }
    
    // string += "</ul>"+"\n";
    // string += "<div class='panel-container'>"+"\n";
    // string += "\t"+'<div id="tabs3">'+"\n";
    // string += "\t\t"+'<div id="topPapers"></div>'+"\n";
    // string += "\t"+'</div>'+"\n";


    // for(var i in corpusesList) {
    //     var text = corpusesList[i]["name"]
    //     var c = corpusesList[i]["id"]
    //     string += "\t"+'<div id="tabs'+c+'">'+"\n";
    //     string += "\t\t"+'<div id="top_'+text+'"></div>'+"\n";
    //     string += "\t"+'</div>'+"\n";
    // }
    // string += "</div>"+"\n";
    // $("#tab-container-top").html(string);
    // console.log(string)
    // console.log(" - - -- -- - ")
    // console.log(corpusesList)



    // var theids = []
    // var pageurl = window.location.href.split("/")
    // var cid;
    // for(var i in pageurl) {
    //     if(pageurl[i]=="corpus") {
    //         cid=parseInt(i);
    //         break;
    //     }
    // } 
    // var corpus_id = pageurl[cid+1];

    // theids.push( corpus_id )


    // for(var corpora in corpusesList) {
    //     console.log("other corpus_id:")
    //     console.log( corpora )
    //     theids.push( corpora )
    //     break
    // }

    // console.log("the two corpuses:")
    // console.log( theids )
}

// Just for Garg
function GetUserPortfolio() {
    //http://localhost:8000/api/corpusintersection/1a50317a50145
    var pageurl = window.location.href.split("/")
    var pid;
    for(var i in pageurl) {
        if(pageurl[i]=="project") {
            pid=parseInt(i);
            break;
        }
    } 
    var project_id = pageurl[pid+1];

    var cid;
    for(var i in pageurl) {
        if(pageurl[i]=="corpus") {
            cid=parseInt(i);
            break;
        }
    } 
    var corpus_id = pageurl[cid+1];

    if( Object.keys( corpusesList ).length > 0 )
        return true;

    var query_url = window.location.origin+'/api/userportfolio/project/'+project_id+'/corpuses'
    $.ajax({
        type: 'GET',
        url: query_url,
        success : function(data) {
            
            var html_ = ""
            html_ += '<div class="panel-group" id="accordion">'+"\n"
            html_ += ' <form id="corpuses_form" role="form">'+"\n"
            corpusesList = data;
            for (var k1 in data) {
                var v1 = data[k1]
                html_ += '  <div class="panel panel-default">'+"\n"
                html_ += '   <div class="panel-heading">'+"\n"
                html_ += '    <h4 class="panel-title">'+"\n"
                html_ += '     <a data-toggle="collapse" data-parent="#accordion" href="#collapse_'+k1+'">'+v1["proj_name"]+'</a>'+"\n"
                html_ += '    </h4>'+"\n"
                html_ += '   </div>'+"\n"
                html_ += '   <div id="collapse_'+k1+'" class="panel-collapse collapse">'+"\n"
                html_ += '    <div class="panel-body" style="input[type=radio] {display: none;}">'+"\n"
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


        },
        error: function(){ 
            pr('Page Not found: TestFunction()');
        }
    });
}

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

function getTips(){   
    param='';

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
    $("#tab-container-top").hide();
    return text;
}
