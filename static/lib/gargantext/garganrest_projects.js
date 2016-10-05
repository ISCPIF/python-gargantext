  /////////////////////////////////////
 ////        AJAX CALLS           ////
/////////////////////////////////////
// c24b 01/06/2016
//      templating +
//      Generic AJAX methods (through API) for project and corpus
//      - get (listing)
//      - create
//      - edit
//      - delete
//      - update
//      - recalculate => API metrics

// utils: templateing cookies, error form, selected checkbox
////////////////////////////////////////////////////////////////////////
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
};

function loadTpl(tpl_id, record){
    //generic function to load a TPL given its tpl_id (#)
    var corpus_tpl 		= $(tpl_id).html();
    corpus_tpl = corpus_tpl.replace(/{count}/g, record.count);
    corpus_tpl = corpus_tpl.replace(/{name}/g, record.name);
    corpus_tpl = corpus_tpl.replace(/{url}/g, record.url);
    corpus_tpl = corpus_tpl.replace(/{status}/g, record.status);
    corpus_tpl = corpus_tpl.replace(/{id}/g, record.id);
    corpus_tpl = corpus_tpl.replace(/{query}/g, record.query);
    corpus_tpl = corpus_tpl.replace(/{source}/g, record.source);
    return corpus_tpl
};

// FORM STATUSES
function addFormStatus(status, form, msg){
  //inform user from error in back throught API
  //alert(form)
  dismiss =  '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>'
  if(status =="error"){
    icon = '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>   '
    msg =  dismiss+icon+msg
    //form
    $(form).addClass("alert-danger")
    //msg div
    msg_div = $(form).children("div#status-form")
    console.log(msg_div)
    msg_div.html(msg)
    msg_div.collapse("show")

  }
  else{
    $(form).collapse("hide")

    window.location.reload()
  }
}
function resetStatusForm(form){
  $(form).removeClass("alert-danger alert-info alert-success");
  $("div#status-form").val("");
  $("div#status-form").collapse("hide");
  //$(form).collapse("hide");
  //window.location.reload()
}
//PAGES STATUSES
function addPageStatus(status, msg){

  dismiss =  '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>'
  if (status == "error"){
    icon = '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>   '
    msg = dismiss+icon+msg
    $('div#status-msg').addClass("alert-danger");
    $('div#status-msg').html(msg);
    $("div#status").collapse("show");
  }
  else if (status == "info"){
    $('div#status-msg').addClass("alert-info");
    icon = '<span class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>   '
    msg = dismiss+icon+msg
    $('div#status-msg').html(msg);
    $("div#status").collapse("show");
    $('div#editor').addClass("hidden");

  }
  else{
    window.location.reload();

  }
}

function selectedUrls(){

  var selected = [];
  $('input:checked').each(function() {
      selected.push($(this).val());
  });
  return selected
};
function selectedIds(){
  //only used for recalc
  var selected = [];
  $('input:checked').each(function() {
      selected.push($(this).data("id"));
  });
  return selected
};
//// GET FROM API
function getProjects(){
    url_ = "/api/projects"
    console.log( ">> get_projects() from api/projects VIEW" );
    $.ajax({
        type: "GET",
        url: url_,
        dataType: "json",
        success : function(data) {
            var _content = "";
            var _count = data.count;
            for(var i in data.records) {
                console.log(data.records[i]);
                var record = data.records[i];
                record.url = "/projects/"+record.id;
                _content += loadTpl("#project_item",record)
            };
            $("#projects").html( _content );
          },
        error: function(data) {
          console.log(data.status, data.responseJSON);
          if (data.status == 404){
            msg = 'You have no projects for now. Click <strong>Add project</strong> to create a new one'
            addPageStatus("info", msg);
            return;
          }
          else{
              msg = data.status+':'+data.responseJSON["detail"]
              addPageStatus("error", msg);
              return;
          }
          },
      });
  };

function getCorpora(){
    console.log( ">> get_CORPORA() from api/projects/<pid> VIEW" );
    var pathname = window.location.pathname; // Returns path only
    //alert(pathname)
    url_ = "/api"+pathname
    $.ajax({
        type: "GET",
        url: url_,
        success : function(data) {
          project = data.parent;
          corpus_nb = data.count
          corpora = data.records
          //manque another request to serve resources
          resources = getRessources(pathname);

          var _content = "";
          corpora.forEach(function(corpus) {
              //getCorpus() info
              corpus.url = pathname+"/corpora/"+corpus.id
              corpus.count = corpus.documents.length
              //corpus.resources = getCorpusResource(pathname+"/corpora/"+corpus.id)
              _content += loadTpl("#corpus_item", corpus);
              //corpus.status = setInterval( getCorpusStatus(pathname+"/corpora/"+corpus.id), 5000 );
              //corpus.status = getCorpusStatus()
          });
          $("div#corpora").html( _content);
          },
          error: function(data) {
              console.log(data.status, data.responseJSON);
              if (data.status == 404){
                msg = 'You have no corpora for now. Click <strong>Add corpus</strong> to create a new one'
                addPageStatus("info", msg);
                return;
              }
              else{
                  msg = data.status+':'+data.responseJSON["detail"]
                  addPageStatus("error", msg);
                  return;
              }
            },
    });
  };

function getRessources(){
  var pathname = window.location.pathname;
  url_ = "/api"+pathname+"/resources"
  //alert(url_)
}
//// POST TO API



//// PUT AND PATCH TO API
function deleteOne(url, thatButton){

  console.warn("thatButton",thatButton)

  if (typeof thatButton != 'undefined' && thatButton.id) {
    // we just show wait image before ajax
    var $thatButton = $(thatButton)
    var alreadyWaiting = $thatButton.has($('.wait-img-active')).length


    if (! alreadyWaiting ) {
      var previousButtonContent = $thatButton.html()
      var availableWidth = $thatButton.width()
      var $myWaitImg = $('#wait-img').clone()
      $myWaitImg.attr("id", null)
                .attr("class","wait-img-active pull-right")
                .width(availableWidth)
                .css("display", "block") ;
      $thatButton.append($myWaitImg)
    }
  }

  // now the real ajax
  $.ajax({
    url: '/api'+url,
    type: 'delete',
    beforeSend: function(xhr) {
          xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
              },
    success: function(xhr) {
      console.log("SUCCESS!");
      //msg = "Sucessfully deleted"
      //addPageStatus("success", "#editForm", msg);
      window.location.reload()
       },
    error: function(xhr) {
      console.log("FAIL!");
      window.location.reload()
      //console.log(xhr.status);
      //var status = xhr.status;
      //var info = xhr["detail"];
      //var msg = "ERROR deleting project"+ url
      //console.log(msg)
      //addPageStatus("info", msg);
      //window.location.reload();
      },
  });

};

function editOne(url, id, data){
    $.ajax({
    url: '/api'+url+"?"+jQuery.param(data),
    type: 'PUT',
    beforeSend: function(xhr) {
          xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                },
    success: function(response) {
        console.log(response);
        console.log("EDIT SUCCESS!");
        addFormStatus("success", "div#editForm-"+id, response["detail"]);
        window.location.reload()
         },
    error: function(xhr) {
        console.log("EDIT FAIL!")
        var status = xhr.status;
        var info = xhr.responseJSON["detail"];
        var msg = "<strong>ERROR ["+status+"]:</strong>"+ "<p>"+info+"</p>"
        addFormStatus("error", "div#editForm-"+id, msg);
        },
    });
};

function recalculateOne(id){
    $.ajax({
      url: '/api/metrics/'+id,
      type: 'PATCH',
      beforeSend: function(xhr) {
                     xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                },
      success: function(response) {
          console.log("RECALC SUCCESS!");
          window.location.reload();
         },
      error: function(xhr) {
          console.log("RECALC FAIL!")
          console.log(result)
          var status = xhr.status;
          var info = xhr["detail"];
          var msg = "<strong>ERROR ["+status+"]:</strong>"+ "<p>"+info+"</p>"
          //no form error is sent to page status alert
          addPageStatus("error", msg);
        },
    });
};


/////////////////////////////////////////////////
/// PAGE INTERACTION
////////////////////////////////////////////////
//CONTEXTUAL HELP
$(document).on("hover", "button", function(){
  //make tooltip on buttons using title attr
    $(this).tooltip();
});
//MULTIPLE SELECTION ACTION
// checkbox with BUTTON #delete, #edit #refresh

//Activate editor bar
$(document).on('change', 'input[type=checkbox]', function() {
  if ($("input:checkbox:checked").length > 0){
    if (! $("#editor").hasClass("collapse in")){
      $("#editor").collapse("show");
    }
  }

  else{
    if ($("#editor").hasClass("collapse in")){
      $("#editor").collapse("hide");
    }
  }});


//DELETE MULTI
$(document).on("click","#delete", function(){
      var selected = selectedUrls();
      selected.forEach(function(url) {
        deleteOne(url, this);
      });
    //window.location.reload();
  });

//EDIT MULTI
$(document).on("click","#edit", function(){
      var selected = selectedUrls();
      var statuses = [];
      // selected.forEach(function(url) {
      //   editOne(url, data);
      // });
      //alert("Not Implemented Yet")
  });

//RECALC MULTI
$(document).on("click","#recalculate", function(){
      //alert("Recalculate");
      var selected = selectedIds();
      selected.forEach(function(id) {
          recalculateOne(id);
        });
      window.location.reload();
  });

//UNIQUE action
// button with .delete, .edit, .refresh
// UNIQUE DELETION
$(document).on("click", ".delete", function() {
      var url = $( this ).data("url");
      deleteOne(url, this);
      //window.location.reload();
});

//UNIQUE EDITION
$(document).on("click",".edit", function(){
    var id = $(this).data("id")
    var url = $( this ).data("url")
    console.log(id)
    //newform.collapse("show");
    $('#editForm-'+id).collapse('toggle')

    // $(document).bind('keypress', function(e) {
    //     if(e.keyCode==13){
    //          $('#edit-submit-'+id).trigger('click');
    //      }
    // });

    $("#edit-submit-"+id).on('click', function(){
      //alert(url)

      name = $("input#name-"+id).val()
      data = {"name": name}
      editOne(url, id, data);
      //window.location.reload();
    });
    $("#edit-cancel-"+id).on('click', function(){
      //alert("cancel")
      $('input#name-'+id).val("");
      resetStatusForm("#editForm-"+id);

    });

    $("button").on("click", ".edit", function(){
        $('input#name-'+id).val("");
        resetStatusForm("#editForm-"+id);
    })

})

//UNIQUE RECALC
$(document).on("click",".refresh", function(){
    //alert(refresh)
      //console.log( $(this))
      var id = $(this).data("id")
      //var url = $( this ).data("url")

      recalculateOne(id)
      window.location.reload();

    });
function createProject() {
    //alert("Creating a new project");
    //simple post: with the name
    //onclick inside element because probleme of scope with modal
    //we recover the element by hand for the moment
    var project_name = $(".popover #inputName").val();
    //alert(project_name);
    console.log("Create project #"+project_name);
    console.log("POST /api/projects");
    $.ajax({
        url: '/api/projects',
        type: 'post',
        data: {"name":project_name},
        dataType: 'json',
        beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                },
        success: function(xhr, response) {
            console.log(xhr.status);
            console.log(response["detail"]);
            location.reload();
             },
        error: function(data) {
            //alert(data)
            console.log(data)
            status = data.status;
            info = data.responseJSON["detail"];
            msg = "<strong>ERROR ["+status+"]:</strong>"+ "<p>"+info+"</p>"
            addFormStatus("error","div#createForm", msg)
            },
        })
};

function createCorpus(url, method, form){
    //alert(method)
    //alert(url)
    console.log(form)
    console.log("POST corpus")
    $.ajax({
       url: '/api/'+url+'?method='+method,
       type: 'post',
       async: true,
       contentType: false, // obligatoire pour de l'upload
       processData: false, // obligatoire pour de l'upload
       dataType: 'json', // selon le retour attendu
       data: form,
       cache: false,
       beforeSend: function(xhr) {
             xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
      success: function(data) {
        console.log(data)
        status = data.status;
        info = data["detail"];
        msg = "<strong>OK ["+status+"]:</strong>"+ "<p>"+info+"</p>"
        addFormStatus("success", "form#formCorpus", msg)
          setTimeout(function(){
              $('div#info').slideUp('slow').fadeOut(function() {
                  window.location.reload(true);
              });
          }, 6000);
        },
        error: function(data) {
            console.log(data);
            console.log(data)
            status = data.status;
            info = data.responseJSON["detail"];
            msg = "<strong>ERROR ["+status+"]:</strong>"+ "<p>"+info+"</p>"
            //alert(msg)
            addFormStatus("error","form#formCorpus", msg);
            //$(".collapse").collapse("hide");
            //_content = '<h2><span class="glyphicon glyphicon-remove-circle" aria-hidden="true"></span>Error while creating the corpus.</h2>'
            //$("div#info").append(_content);
            //$("div#info").addClass("alert-danger");
            //$("div#info").collapse("show");
        },
      })
  };
