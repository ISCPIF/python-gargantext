function popOverFactory(selector, pos, confirmation){
  //Factory for popover indicated by class tour
  // transforming into btn and mapping title and content
  $(selector).attr({  "type": "button",
                      "data-toggle": "popover",
                      "data-placement": pos,
                      "data-trigger": "toogle",

                    });
  $(selector).popover({
    html:true,
    title: '<h1>'+selector.attr("title")+'</h1>',
    content: '<p class="text-center">'+selector.attr("content")+'</p>'+
    '<div class="btn-group col-sm-12">'+
              '<button class="col-sm-6 btn btn-sm btn-danger" data-role="prev">&laquo; Prev</button>'+
              '<button class="col-sm-6 btn btn-sm  btn-success" data-role="next">Next &raquo;</button>'+
            '</div><br>',
    container: 'body',
    trigger:"toogle"
  });
  //$('.btn').not(this).popover('hide');
  //$(selector).popover('toggle');
};


var steps = {}

function nextStep(p, val) {
  return p[($.inArray(val, p) + 1) % p.length];
}
function previousStep(p, num) {
  return p[($.inArray(val, p) - 1) % p.length];
}
function activateTour(){
  $(document).on("click", "a#guided_tour", function(e){
    if ($(this).parent().hasClass("active")){
        $(this).parent().removeClass("active");

        //$(this).popover("hide");
        $('.popover').popover('hide');
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
      //buildTour()
      steps = $(document).find(".tour")
      console.log(steps)
      $(".tour").each(function(i, obj, steps){
          popOverFactory($(this), "right", true)
          $(this).popover("show");

        })
      }
  })};
