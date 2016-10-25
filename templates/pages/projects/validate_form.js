  console.log(errors)

  errors.forEach(function(err) {
      div = err[0].split(" ")
      logs = []
      logs.push(div[0])
      if (err[1] == false)
      {
        alert(div[0])

        //$(div[0]).parent().addClass("alert danger error");

        $(div[0]).next(div[1]).collapse("show");

        //$(div[0]).find(div[1]).collapse("show")
      }
      else
      {
        $("<span class='glyphicon glyphicon-ok' aria-hidden='true'>").appendTo(div[0])
      }
  });
  return errors
};
function checkInput(source){
  if (source.val().length > 0){
    return true
  }
  else {
    return false
  }
}
function checkSourceFormat(){
  source = $("select#source").find(':selected')
  if (source.val() != '') {
    console.log(source)
    source_data = source.data("format")
    alert(source_data)
    formats = source_data.split(',');
    alert(formats);
    extension = $("#file").val().substr( (filename.lastIndexOf('.') +1) );
    if ($.inArray(extension, formats) == -1){
        //$("span.format").collapse("show");
        return false;
      }
    else{
      //$("span.format").collapse("hide");
      return true;
    }
  }
  return true
}
function checkFileSize(filesize, max_size){
  if (filesize > max_size){
        return true
  }
  else{
      return false
  }
};


  //ADD CORPUS FORM
  //     //source
  //     $('#source').change(function() {
  //         $("#source").next("span.required").collapse("hide");
  //         source_type = $('#source').find(":selected");
  //         var formats = source_type.data("format").split(',');
  //         if (formats.length == 0){
  //           $("#source").next("span.required").collapse("show");
  //
  //         }
  //         else{
  //           $("#source").next("span.required").collapse("hide");
  //         }
  //     });
  //     //file
    // var max_size = parseInt($('#file').data("max-size"));
    // $('#file').change(function() {
    //        var filesize = parseInt(this.files[0].size);
    //        if( filesize > max_size){
    //          alert("Upload file can't exceed 1 Mo because Gargantext would have an indigestion. Consult the special diet of Gargantext in our FAQ")
    //          $("#file").empty();
    //        };
    // });
  //
  //
  // });
  $("#create").bind("click",function(){
      var method = $('#radioBtn').find('a.active').data("title");
      errors = checkForm()
      if (has_error == "true"){
        alert("Invalid Form");
      }
      else{
        alert("OK")
          //if (checkFileExtension() == true){
            //preparePost(method, form)
          //}
      }
    });
