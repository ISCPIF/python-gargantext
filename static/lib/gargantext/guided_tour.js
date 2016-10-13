function popOverFactory(selector, step, pos){
  //Factory for popover indicated by class tour
  var title = $(selector).attr('name');
  var placement = $(selector).attr('placement');
  console.log(title)
  console.log(placement)
  if (title == false || title == undefined) {
    title = "<h1>STEP"+ step +"</h1>"
  }
  if (placement == false || placement == undefined) {
    placement: pos
  }


  $(selector).popover({
    html:true,
    title : title,
    content: '<p class="text-center">'+$(selector).attr("content")+'</p>'+
    '<div class="btn-group col-sm-12">'+
              '<button class="col-sm-6 btn btn-sm btn-danger" data-role="prev">&laquo; Prev</button>'+
              '<button class="col-sm-6 btn btn-sm  btn-success" data-role="next">Next &raquo;</button>'+
            '</div><br>',
    container: 'body',
    trigger:"toogle",
    placement: placement
  });
  //$('.btn').not(this).popover('hide');
  //$(selector).popover('toggle');
}

function nextStep(element, i){
  steps = $(document).find(".tour")
  $(document).on("click", "button[data-role='next']", function(e){
    console.log("curr", element);
    $("div.jumbotron" > "button.popover")
    native_pop = $(element).children()

    //native_pop.addClass("tour")
    native_pop.popover("show");
    //$("div.status-form").appendTo("Enter a name and click on add project")
    //addFormStatus("success","div#createForm", "Enter a name and click on add project")


    $(element).popover("hide");

    active = $.find(".in")
    submit = $(active).find("button")
    if (submit.length >= 1){
      $(document).on("click", submit, function(e){
        i = i+1
        alert("clicked")
      })
    }
    else{
        i = i+1
    }

    // if (active.length > 0){
    //   $("button")
    //   i = i+2
      //native_pop.popover("hide")
      //return [native_pop, i]
      //$(document).on("change keyup paste", function(){
      //  alert("typing...")
      //})
    // }
    // else{
    //   i = i+2
    // }

    element = steps[i]
    console.log("next", element);

    popOverFactory(element, i, "right");
    $(element).popover("show");

    return [element, i];

  });

}

function activateTour(){
  $(document).on("click", "a#guided_tour", function(e){
    if ($(this).parent().hasClass("active")){
        $(this).parent().removeClass("active");
        $(this).popover("hide");
        //$('.popover').popover('hide');
        //$(this).popover("destroy");
    }
    else {
      $(this).parent().addClass("active");
      curr = $(this)
      i =  -1
      //create the popover
      popOverFactory(curr, i, "bottom");
      //hide the other popover
      $('.popover').not(this).popover('hide');
      //show the popover
      $(this).popover('toggle');
      //buildTour
      curr, i = nextStep(curr, i)
      console.log(i, curr)
      if (i > steps.lenght){
        return false
      }

    }
  })
}
