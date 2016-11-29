/////////////////FORM VALIDATION
function checkFilename(filename){
  if (filename ==  ""){
        $("#filename").next("span.required").collapse("show");
        return false;
  }
  else{
      $("#file").next("span.required").collapse("hide");
      return true;
  }
};
function checkFileSize(filesize, max_size){
  if (filesize > max_size){
        $("span.size").collapse("show");
  }
  else{
      $("span.size").collapse("hide");
  }
};
function checkFileExtension(){
  filename = $('#file').val()
  source_type = $('#source').find(":selected");
  if (filename != "" && source_type.val() !== "0"){
    fextension = filename.substr( (filename.lastIndexOf('.') +1) );
    var formats = source_type.data("format").split(',');
    if ($.inArray(extension, formats) == -1){
        $("span.format").collapse("show");
        return false;
      }
    else{
      $("span.format").collapse("hide");
      return true;
    }
  }
};

//name
$("span.error").collapse("hide");
$('#name').on('input', function() {
  var input=$(this);
  var is_name=input.val();
  if ( is_name.length < 0){
    $("#name").next("span.required").collapse("show");
    $("form-group#name").addClass("error");
  }
  else {

    $("#name").next("span").collapse("hide");
  }
});

//source
$('#source').change(function() {
    $("#source").next("span.required").collapse("hide");
    source_type = $('#source').find(":selected");
    var formats = source_type.data("format").split(',');
    if (formats.length == 0){
      $("#source").next("span.required").collapse("show");

    }
    else{
      $("#source").next("span.required").collapse("hide");
    }
});
//file
var max_size = parseInt($('#file').data("max-size"));
$('#file').change(function() {
    $('#name span').collapse("hide");
    var input=$(this);
    var filename= input.val()

    var filesize = parseInt(this.files[0].size);
    checkFileSize(filesize, max_size);
  });
//console.log("ERRORS?,)
$("#create").bind("click",function(){
  var method = $('#radioBtn').find('a.active').data("title");
  has_error = $("span.error").hasClass("collapse in");
  if (has_error == "true"){
    alert("Invalid Form");
  }
  else{
      if (checkFileExtension() == true){
        //preparePost(method, form)
      }
  }
});
