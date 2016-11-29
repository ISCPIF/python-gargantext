<script>
  var thequeries = [] ;

  // load the template's value for N scan size
  var querySize = parseInt({{query_size}}) ;

  // TODO if is_admin

  function doTheQuery() {
      if ( $('#submit_thing').prop('disabled') ) return;
      console.log("in doTheQuery:");
      var origQuery = $("#id_name").val()


      var pubmedifiedQuery = {
          query : JSON.stringify(thequeries) ,
          string: origQuery ,
          N : querySize
      } ;
      console.log(pubmedifiedQuery)

      var projectid = window.location.href.split("projects")[1].replace(/\//g, '')//replace all the slashes

      $.ajax({
          // contentType: "application/json",
          url: window.location.origin+"/moissonneurs/pubmed/save/"+projectid,
          data: pubmedifiedQuery,
          type: 'POST',
          beforeSend: function(xhr) {
              xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          },
          success: function(data) {
              console.log("in doTheQuery() Ajax.Success:")
              // console.log(data)
              setTimeout(
                  function() {
                      location.reload();
                  }, 3000);
              },
              error: function(result) {
                  console.log("in doTheQuery(). Data not found");
              }
      });
  }

  function bringDaNoise() {
      var theresults = $("#theresults").html()
      if( theresults && theresults.search("No results")==-1 ) {
          console.log("we've in dynamic mode")
          $("#simpleloader").html('<img width="30px" src="{% static "img/loading-bar.gif" %}"></img>')
          $("#submit_thing").prop('onclick',null);

          var theType = $("#id_type option:selected").html();
          console.log("consoling the type: ")
          console.log(theType)
          if(theType=="Pubmed (XML format)") doTheQuery();
          if(theType=="ISTex") {
              var origQuery = $("#id_name").val()
              console.log("printing the results:")
              console.log(origQuery)
              testISTEX(origQuery.replace(" ","+"), querySize)
          }
      }
      else {
          console.log("we dont have nothing inside results div")
          if ( $("#id_file").is(':visible') ) {
              console.log("we're in upload-file mode")

              var namefield = $("#id_name").val()!=""
              var typefield = $("#id_type").val()!=""
              var filefield = $("#id_file").val()!=""
              if( namefield && typefield && filefield ) {
                  $("#simpleloader").html('<img width="30px" src="{% static "img/loading-bar.gif" %}"></img>')
                  $("#submit_thing").prop('onclick',null);
                  $( "#id_form" ).submit();
              }
          }

      }
  }

  function getGlobalResults(value){
      console.log("in getGlobalResults()")
      // AJAX to django
      var pubmedquery = $("#id_name").val()
      // var Npubs = $("#id_N").val();
      if(pubmedquery=="") return;
      var formData = {query:pubmedquery , N:querySize}
      $("#theresults").html('<img width="30px" src="{% static "img/loading-bar.gif" %}"></img>')
      console.log("disabling "+"#"+value.id)
      $("#"+value.id).prop('onclick',null);

      var theType = $("#id_type option:selected").html();

      if(theType=="Pubmed (XML format)") {
          $.ajax({
              // contentType: "application/json",
              url: window.location.origin+"/moissonneurs/pubmed/query",
              data: formData,
              type: 'POST',
              beforeSend: function(xhr) {
                  xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
              },
              success: function(data) {
                  console.log("SUCCESS")
                  console.log("in getGlobalResults")
                  // console.log(data)
                  console.log("enabling "+"#"+value.id)
                  $("#"+value.id).attr('onclick','getGlobalResults(this);');
                  // $("#submit_thing").prop('disabled' , false)
                  $("#submit_thing").html("Process a {{ query_size }} sample!")

                  thequeries = data
                  var N=0,k=0;

                  for(var i in thequeries) N += thequeries[i].count
                  if( N>0) {
                      $("#theresults").html("<i> <b>"+pubmedquery+"</b>: "+N+" publications in the last 5 years</i><br>")
                      $('#submit_thing').prop('disabled', false);
                  } else {
                      $("#theresults").html("<i>  <b>"+pubmedquery+"</b>: No results!.</i><br>")
                      if(data[0]==false)
                      $("#theresults").html("Pubmed connection error!</i><br>")
                      $('#submit_thing').prop('disabled', true);
                  }

              },
              error: function(result) {
                  $("#theresults").html("Pubmed connection error!</i><br>")
                  $('#submit_thing').prop('disabled', true);
              }
          });
      }

      if(theType=="ISTex") {
          console.log(window.location.origin+"moissonneurs/istex/query")
          $.ajax({
              // contentType: "application/json",
              url: window.location.origin+"/moissonneurs/istex/query",
              data: formData,
              type: 'POST',
              beforeSend: function(xhr) {
                  xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
              },
              success: function(data) {
                  console.log("in getGlobalResults: Ajax(ISTex)")
                  console.log("enabling "+"#"+value.id)
                  $("#"+value.id).attr('onclick','getGlobalResults(this);');
                  // $("#submit_thing").prop('disabled' , false)
                  $("#submit_thing").html("Process a {{ query_size }} sample!")

                  thequeries = data
                  var N=data.length,k=0;
                  // for(var i in thequeries) N += thequeries[i].count
                  if( N>1) {
                      var total = JSON.parse(data).total
                      console.log("N: "+total)
                      $("#theresults").html("<i> <b>"+pubmedquery+"</b>: "+total+" publications.</i><br>")
                      $('#submit_thing').prop('disabled', false);
                  } else {
                      $("#theresults").html("<i>  <b>"+data[0]+"</b></i><br>")
                      $('#submit_thing').prop('disabled', true);
                  }

              },
              error: function(result) {
                  console.log("Data not found");
              }
          });
      }
  }

  // CSS events for selecting one Radio-Input
  function FileOrNotFile( value ) {
      var showfile = JSON.parse(value)
      var theType = $("#id_type option:selected").html();
      // @upload-file events
      if (showfile) {
          console.log("You've clicked the YES")
          $("#id_file").show()
          $('label[for=id_file]').show();
          $("#id_name").attr("placeholder", "");
          $("#scanpubmed").html("")
          $("#theresults").html("")
          $('#submit_thing').prop('disabled', false);
          $( "#id_name" ).on('input',null);
          $("#submit_thing").html('<span class="glyphicon glyphicon-ok" aria-hidden="true" ></span> Process this!')
      }
      // @dynamic-query events
      else {
          console.log("You've clicked the NO")
          $("#id_file").hide()
          $('label[for=id_file]').hide();
          $("#id_name").attr("placeholder", " [ Enter your query here ] ");
          $("#id_name").focus();
          $("#scanpubmed").html('<a class="btn btn-primary">Scan</a>')//+'Get: <input id="id_N" size="2" type="text"></input>')
          $("#theresults").html("")
          $("#submit_thing").prop('disabled' , true)

          $( "#id_name" ).on('input',function(e){
              console.log($(this).val())
              if(theType=="Pubmed (XML format)")
              testPUBMED( $(this).val() )
          });
      }
  }

  //CSS events for changing the Select element
  function CustomForSelect( selected ) {
      // show Radio-Inputs and trigger FileOrNotFile>@upload-file events
      selected = selected.toLowerCase()
      var is_pubmed = (selected.indexOf('pubmed') != -1);
      var is_istex = (selected.indexOf('istex') != -1);
      if (is_pubmed || is_istex) {
          // if(selected=="pubmed") {
          console.log("show the button for: " + selected)
          $("#pubmedcrawl").css("visibility", "visible");
          $("#pubmedcrawl").show();
          $("#file_yes").click();
          $("#submit_thing").html("Process this!")
      }
      // hide Radio-Inputs and trigger @upload-file events
      else {
          console.log("hide the button")
          $("#pubmedcrawl").css("visibility", "hidden");
          $("#id_file").show()
          $('label[for=id_file]').show();
          FileOrNotFile( "true" )
      }
  }

  var LastData = []
  function NSuggest_CreateData(q, data) {
      console.log("in the new NSuggest_CreateData:")
      LastData = data;
      // console.log(LastData)
      console.log("adding class ui-widget")
      $("#id_name").removeClass( "ui-widget" ).addClass( "ui-widget" )
      $( "#id_name" ).autocomplete({
          source: LastData
      });
      return data;
  }

  function testPUBMED( query ) {
      LastData = []
      if(!query || query=="") return;
      var pubmedquery = encodeURIComponent(query)
      $.ajax({
          type: 'GET',
          url: "http://www.ncbi.nlm.nih.gov/portal/utils/autocomp.fcgi?dict=pm_related_queries_2&q="+pubmedquery,
          // data:"db="+db+"&query="+query,
          contentType: "application/json",
          dataType: 'jsonp'
      });
      return false;
  }

  function testISTEX(query,N) {
      console.log("in testISTEX:");
      if(!query || query=="") return;
      var origQuery = query

      var postQuery = { query : query , N: N }

      var projectid = window.location.href.split("projects")[1].replace(/\//g, '')//replace all the slashes

      $.ajax({
          // contentType: "application/json",
          url: window.location.origin+"/moissonneurs/istex/save/"+projectid,
          data: postQuery,
          type: 'POST',
          beforeSend: function(xhr) {
              xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          },
          success: function(data) {
              console.log("ajax_success: in testISTEX()")
              // console.log(data)
              setTimeout(
                  function() {
                      location.reload();
                  }, 5000);
              },
              error: function(result) {
                  console.log("in testISTEX(). Data not found");
              }
          });
      }

</script>
