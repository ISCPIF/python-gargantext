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


function nextStep(element, i){
  steps = $(document).find(".tour")
  $(document).on("click", "button[data-role='next']", function(e){
    console.log("curr", element);
    $(element).popover("hide");
    native_pop = $(element).children()

    native_pop.popover("show");
    i = i+1
    active = $.find(".in")

    if (active.length > 0){
      return [native_pop, i]
    }
    else{
      element = steps[i]
      console.log("next", element);

      popOverFactory(element, "right");
      $(element).popover("show");

      return [element, i];
    }
  });

}
function prevStep(element, i){
  steps = $(document).find(".tour")
  $(document).on("click", "button[data-role='prev']", function(e){
    console.log("curr", element);
    $(element).popover("hide");
    alert(i)
    i = i-1
    alert(i)
    element = steps[i]
    console.log("prev", element);
    console.log("child", $(document).find(".popover"));
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
