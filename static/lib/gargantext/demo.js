// DEMO
var page = window.location.href
var storage =  window.localStorage;
var steps = [];
var min = 0;
var max = this.steps.length;
var pos = undefined;
var step = undefined;
var start_element = "a#guided_tour"
//here is the targeted_element we want to show
//this.targeted_el = undefined;
//html template
var controller = '<div class="btn-group col-xs-12">'+
      '<div class="col-xs-2"></div>'+
      '<button class="btn btn-sm btn-warning col-xs-3" onclick=end()(storage.pos)><span class="glyphicon glyphicon-step-backward"></span></button>'+
      '<button class="btn btn-sm btn-success col-xs-3" onclick=goNext(storage.pos)><span class="glyphicon glyphicon-step-forward"></span></button>'+
      '<button class="btn btn-sm btn-danger col-xs-3" onclick="endTour();"><span class="glyphicon glyphicon-stop"></span></button>'+
      '<div class="col-xs-1"></div>'+
      '</div>'
  //this.popover_template = 0;
  //this.modal_template = 0;
  //this.toogle_template = 0;
  //this.tooltip_template = 0;
//var match = /^([0-9]{4})-([0-9]{2})-([0-9]{2})$/.exec(str);
//alert(page)
function addStep(step)  {
  console.log("addstep steps", steps);
  console.log("addstep", step["pos"]);
  //steps.splice(steps, step["pos"], step)
  //step["element"] = $(document).find(step["element")

  //console.log($this);
  steps.push(step);
  console.log("addstep steps", steps);
  return steps
}
function buildTour(from_pos) {
  pos = from_pos
  $( ".tour" ).each(function(i) {
    pos++
    console.log(i)
    step = {
                    "element": $(this),
                    "type": "popover",
                    "title": $(this).attr("title"),
                    "content": $(this).attr("content"),
                    "placement": "left",
                    "pos": pos,
                    "page": window.location.href
                  }
    steps = addStep(step);

  });
  console.log(steps)
  max = steps.length
  return steps
}

function removeStep(step) {
      var step_pos = steps.indexOf(step);
      alert(step_pos)
      steps.splice(step, step_pos);
      return steps
}
function showStep(pos){
  step = steps[pos]
  //curr_el = this.steps[pos]["element"];
      //cache position
  storage.pos = pos
  storage.page = page
  storage.element = step["element"]
  //create popover defining it's type
  pop = createPopover(step, "popover")
  step["element"].popover("show")
  $(step["element"]).addClass("active")
  return step
  }
function goNext(pos){
    if (pos >= steps.length){
       return endTour();
    }
    else {

    //get current step
    previous =  steps[pos];
    $(previous["element"]).popover("hide")
    //this.curr.removeClass("curr-step")
    //this.previous.addClass("prev-step")
    console.log(steps)
    pos++
    if (pos >= steps.length){
       return endTour();
    }
    else{
      console.log(pos)
      console.log(steps.length)
      step = steps[pos];
      console.log("curr", step)
      storage.pos = pos

      //this.curr.removeClass("prev-step")
      //storage.element = step["element"]
      $(step["element"]).addClass("curr-step")
      createPopover(step);
      $(step["element"]).popover("show")
      //var this.next = this.steps[pos+1];
      //this.curr.addClass("next-step")
      return step
      }
    }
  }
  function goPrev(pos){
    if (this.curr >= this.min){
      return end()
    }
    next =  steps[pos];
    next["element"].popover("hide")
    //this.next.removeClass("curr-step")
    //this.next.addClass("next-step")
    pos = pos-1
    step = steps[pos];
    storage.pos = pos
    storage.element = step["element"]
    //this.curr.removeClass("prev-step")
    $(step["element"]).addClass("curr-step")
    createPopover(this.curr)
    step["element"].popover("show")
    // var this.previous = this.steps[pos+1];
    //this.next.removeClass("curr-step")
    //this.curr.addClass("next-step")
    return this.curr
  }

  function createPopover(step)  {
    //this.type = step["type"]
    if (step["type"] == "popover"){
      step["element"].popover({
        html:true,
        title : step["title"],
        content: '<p class="text-center">'+step["content"]+'</p>'+ controller,
        container: 'body',
        trigger:"focus",
        placement: step["placement"]
      });
    }
    //console.log("pop", step["popover"])
    return step
  }
  function initTour(){
    $(document).on("click", this.start_element, function () {
      if ($(this).parent().hasClass("active")){
          $(this).parent().removeClass("active");
          endTour();
        }
      else {
      $(this).parent().addClass("active");
      console.log(start_element)
      addStep({
                      "element": $(start_element),
                      "type": "popover",
                      "title": $(start_element).attr("title"),
                      "content": $(start_element).attr("content"),
                      "placement": "bottom",
                      "pos": 0,
                      "page": window.location.href
                    });
      pos = 0;
      console.log(steps);
      showStep(pos);
      pos = storage.pos
      if (pos == undefined){
        return endTour()
      }
      else{
        console.log("start")
      };
      steps = buildTour(pos);
      }
    });
    //$(document).on("click", , function () {
    return steps

  }
  function endTour() {
    storage.pos = undefined
    storage.element = undefined
    $('.popover').popover('hide');
    steps = []
  }
  function startTour(){
    pos = storage.pos
    if (pos == undefined){
      return endTour()
    }
    else{
      console.log("start")
    };
    steps = buildTour(pos);

    // $(document).on("click", "button [data-role='next']", function(e){
    //   alert(pos);
    //   goNext(storage.pos);
    // });
    // $(document).on("click", "button [data-role='prev']", function(e){
    //   alert(pos);
    //   goPrev(storage.pos);
    // });
    // $(document).on("click", "button [data-role='stop']", function(e){
    //    endTour();
    // });
    return steps;
  }
