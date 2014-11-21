
function scanDataFolder(){
        $.ajax({
            type: 'GET',
            url: twjs+'php/DirScan_main.php',
            //data: "type="+type+"&query="+jsonparams,
            //contentType: "application/json",
            //dataType: 'json',
            success : function(data){ 
                console.log(data);
                dataFolderTree=data;
            },
            error: function(){ 
                console.log('Page Not found: updateLeftPanel_uni()');
            }
        });
}

function getGexfPath(v){
	gexfpath=(gexfDictReverse[v])?gexfDictReverse[v]:v;
        return gexfpath;
}

function getGexfLegend(gexfPath){
    legend=(gexfDict[gexfPath])?gexfDict[gexfPath]:gexfPath;
    return legend;
}

function jsActionOnGexfSelector(gexfLegend){
    window.location=window.location.origin+window.location.pathname+"?file="+encodeURIComponent(getGexfPath(gexfLegend));
}

function listGexfs(){
    divlen=$("#gexf").length;
    if(divlen>0) {
        param = JSON.stringify(gexfDict);
        $.ajax({
            type: 'GET',
            url: twjs+'php/listFiles.php',
            //contentType: "application/json",
            //dataType: 'json',
            success : function(data){ 
                html="<select style='width:150px;' ";
                javs='onchange="'+'jsActionOnGexfSelector(this.value);'+'"';
                html+=javs;
                html+=">";
                html+='<option selected>[Select your Graph]</option>';
                for(var i in data){
                    //pr("path: "+data[i]);
                    //pr("legend: "+getGexfLegend(data[i]));
                    //pr("");
                    html+="<option>"+getGexfLegend(data[i])+"</option>";
                }
                html+="</select>";
                $("#gexfs").html(html);
            },
            error: function(){ 
                console.log("Page Not found.");
            }
        }); 
    }   
}
