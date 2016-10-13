function popOverFactory(selector, pos, confirmation){
  //Factory for popover indicated by class tour
  // transforming into btn and mapping title and content
  // $(selector).attr({  "type": "button",
  //                     "data-toggle": "popover",
  //                     "data-placement": pos,
  //                     "data-trigger": "toogle",
  //
  //                   });
  $(selector).popover({
    html:true,
    title: '<h1>'+$(selector).attr("title")+'</h1>',
    content: '<p class="text-center">'+$(selector).attr("content")+'</p>'+
    '<div class="btn-group col-sm-12">'+
              '<button class="col-sm-6 btn btn-sm btn-danger" data-role="prev">&laquo; Prev</button>'+
              '<button class="col-sm-6 btn btn-sm  btn-success" data-role="next">Next &raquo;</button>'+
            '</div><br>',
    container: 'body',
    trigger:"toogle",
    placement: pos
  });
  //$('.btn').not(this).popover('hide');
  //$(selector).popover('toggle');
};


var steps = {}

function getStep(element, i){
  steps = $(document).find(".tour")
  console.log("curr", element);

  $(document).on("click", "button[data-role='next']", function(e){
    $(element).popover("hide");
    native_pop = $(element).children()
    native_pop.popover("show");
    i = i+1
    return i
  })
  $(document).on("click", "button[data-role='prev']", function(i){

    $(element).popover("hide");
    native_pop = $(element).children()
    native_pop.popover("show");
    i = i-1
    return i
  })

  element = steps[i]
  popOverFactory(element, "right");
  $(element).popover("show");
  alert(i);
  return [element, i];
}
function nextStep(element, i){
  steps = $(document).find(".tour")
  $(document).on("click", "button[data-role='next']", function(e){
    console.log("curr", element);

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
        "clicked"
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

    popOverFactory(element, "right");
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
      //create the popover
      popOverFactory($(this), "bottom", true);
      //hide the other popover
      $('.popover').not(this).popover('hide');
      //show the popover
      $(this).popover('toggle');
      //buildTour
      curr = $(this)
      i = -1
      //curr, i  = getStep(curr,i)
      curr, i = nextStep(curr, i)
      console.log(i, curr)
      if (i > steps.lenght){
        return false
      }
      if (i == -2){
        return false
      }
      if (curr == "undefined"){
        return false
      }

    }
  })
}
