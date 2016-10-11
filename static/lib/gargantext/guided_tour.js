var steps = {}

function nextStep(num) {
  return p[($.inArray(num, p) + 1) % p.length];
}
function previousStep(num) {
  return p[($.inArray(num, p) - 1) % p.length];
}
function buildTour(){
  $(".class").get().forEach(function(entry, index, array) {
    var me = $(this);
    console.log(entry, index, array);
  });
};

modal_tpl = '<div id={modal_id} class="modal">'+
  <!-- Modal content -->
  '<div class="modal-content">'+
  '<span id="cancel" class="close">x</span>'+
  '<span id="ok" class="submit">x</span>'+
  '{modal_content}'
  '</div>'+
'</div>'

function modalFactory(selector, id, content){
  $(selector).attr({  "type": "button"});

};

function popOverFactory(selector, pos, confirmation){
  $(selector).attr({  "type": "button",
                      "data-toggle": "popover",
                      "data-placement": pos,
                      "data-trigger": "toogle",

                    });
  $(selector).popover({
    html:true,
    title: '<h2>'+selector.attr("title")+'</h2>',
    content: '<p class="text-center">'+selector.attr("content")+'</p>'+
    '<div class="btn-group"><button class="btn btn-small btn-info" id="ok">Yes</button>'+
    '<button class="btn btn-small btn-danger" id="close">No</button></div>',
  });
};
