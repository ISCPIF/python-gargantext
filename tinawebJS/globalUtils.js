

function pr(msg) {
    console.log(msg);
}

//to general utils
function getClientTime(){
    var totalSec = new Date().getTime() / 1000;
    var d = new Date();
    var hours = d.getHours();
    var minutes = parseInt( totalSec / 60 ) % 60;
    var seconds = (totalSec % 60).toFixed(4);
    var result = (hours < 10 ? "0" + hours : hours) + ":" + (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds  < 10 ? "0" + seconds : seconds);
    return result;
}

function compareNumbers(a, b) {
    return a - b;
}

//python range(a,b) | range(a)
function calc_range(begin, end) {
  if (typeof end === "undefined") {
    end = begin; begin = 0;
  }
  var result = [], modifier = end > begin ? 1 : -1;
  for ( var i = 0; i <= Math.abs(end - begin); i++ ) {
    result.push(begin + i * modifier);
  }
  return result;
}


//to general utils (not used btw)
function cloneObject(source) {
    for (i in source) {
        if (typeof source[i] == 'source') {
            this[i] = new cloneObject(source[i]);
        }
        else{
            this[i] = source[i];
  }
    }
}

function isUndef(variable){
    if(typeof(variable)==="undefined") return true;
    else return false;
}


$.fn.toggleClick = function(){
        methods = arguments, // store the passed arguments for future reference
            count = methods.length; // cache the number of methods 

        //use return this to maintain jQuery chainability
        return this.each(function(i, item){
            // for each element you bind to
            index = 0; // create a local counter for that element
            $(item).click(function(){ // bind a click handler to that element
                return methods[index++ % count].apply(this,arguments); // that when called will apply the 'index'th method to that element
                // the index % count means that we constrain our iterator between 0 and (count-1)
            });
        });
};


getUrlParam = (function () {
    var get = {
        push:function (key,value){
            var cur = this[key];
            if (cur.isArray){
                this[key].push(value);
            }else {
                this[key] = [];
                this[key].push(cur);
                this[key].push(value);
            }
        }
    },
    search = document.location.search,
    decode = function (s,boo) {
        var a = decodeURIComponent(s.split("+").join(" "));
        return boo? a.replace(/\s+/g,''):a;
    };
    search.replace(/\??(?:([^=]+)=([^&]*)&?)/g, function (a,b,c) {
        if (get[decode(b,true)]){
            get.push(decode(b,true),decode(c));
        }else {
            get[decode(b,true)] = decode(c);
        }
    });
    return get;
})();



function ArraySortByValue(array, sortFunc){
    var tmp = [];
    oposMAX=0;
    for (var k in array) {
        if (array.hasOwnProperty(k)) {
            tmp.push({
                key: k, 
                value:  array[k]
            });
            if((array[k]) > oposMAX) oposMAX= array[k];
        }
    }

    tmp.sort(function(o1, o2) {
        return sortFunc(o1.value, o2.value);
    });   
    return tmp;      
}



function ArraySortByKey(array, sortFunc){
    var tmp = [];
    for (var k in array) {
        if (array.hasOwnProperty(k)) {
            tmp.push({
                key: k, 
                value:  array[k]
            });
        }
    }

    tmp.sort(function(o1, o2) {
        return sortFunc(o1.key, o2.key);
    });   
    return tmp;      
}
    

function is_empty(obj) {
    // Assume if it has a length property with a non-zero value
    // that that property is correct.
    if (obj.length && obj.length > 0)    return false;
    if (obj.length && obj.length === 0)  return true;

    for (var key in obj) {
        if (hasOwnProperty.call(obj, key))    return false;
    }
    return true;
}


function getByID(elem) {
    return document.getElementById(elem);
}



function hex2rga(sent_hex) {
    result = []
    hex = ( sent_hex.charAt(0) === "#" ? sent_hex.substr(1) : sent_hex );
    // check if 6 letters are provided
    if (hex.length === 6) {
        result = calculateFull(hex);
        return result;
    }
    else if (hex.length === 3) {
        result = calculatePartial(hex);
        return result;
    }
}

function calculateFull(hex) {
    var r = parseInt(hex.substring(0, 2), 16);
    var g = parseInt(hex.substring(2, 4), 16);
    var b = parseInt(hex.substring(4, 6), 16);
    return [r,g,b];
}


// function for calculating 3 letters hex value
function calculatePartial(hex) {
    var r = parseInt(hex.substring(0, 1) + hex.substring(0, 1), 16);
    var g = parseInt(hex.substring(1, 2) + hex.substring(1, 2), 16);
    var b = parseInt(hex.substring(2, 3) + hex.substring(2, 3), 16);
    return [r,g,b];
}

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
