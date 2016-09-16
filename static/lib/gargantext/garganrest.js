// check if an object is an array
if (typeof Array.isArray != 'function') {
    Array.isArray = function(stuff) {
        return Object.prototype.toString.call(stuff) == '[object Array]';
    };
}


// CSRF token management for Django
var getCookie = function(name) {
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
}

// Resource class
var Resource = function(url_path) {

    // retrieve one or many items
    this.get = function(criteria, callback) {
        var url = url_path;
        switch (typeof criteria) {
            // get the list, according to the criteria passed as parameters
            case 'object':
                var url_parameters = '';
                $.each(criteria, function(key, value) {
                    if (Array.isArray(value)) {
                        $.each(value, function(i, item) {
                            url_parameters += url_parameters.length ? '&' : '?';
                            url_parameters += encodeURIComponent(key) + '[]=' + encodeURIComponent(item);
                        });
                    } else {
                        url_parameters += url_parameters.length ? '&' : '?';
                        url_parameters += encodeURIComponent(key) + '=' + encodeURIComponent(value);
                    }
                });
                url += url_parameters;
                break;
            // get the list, without paramters
            case 'function':
                callback = criteria;
                break;
            case 'number':
            case 'string':
                url += '/' + criteria;
                break;
        }
        $.ajax({
            url: url,
            type: 'GET',
            beforeSend: function(xhr) {
              xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            },
            success: callback
        });
    };
    // TODO allow also POST with params
    // TODO this.post function(id, criteria OR params, callback)

    // change an item
    this.change = this.update = function(id, callback) {
        $.ajax({
            url: url_path + '/' + id,
            type: 'PATCH',
            beforeSend: function(xhr) {
              xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            },
            success: callback
        });
    };
    // remove an item
    this.delete = this.remove = function(id, callback) {
        $.ajax({
            url: url_path + '/' + id,
            type: 'DELETE',
            beforeSend: function(xhr) {
              xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            },
            success: callback
        });
    };
    // add an item
    this.add = this.append = function(id, callback) {
        $.ajax({
            // todo define id
            url: url_path + '/' + id,
            type: 'POST',
            beforeSend: function(xhr) {
              xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            },
            success: callback
        });
    };
};

var GarganRest = function(base_path, path_list) {
    var that = this;
    $.each(path_list, function(i, path){
        that[path] = new Resource(base_path + path);
    });
};

garganrest = new GarganRest('/api/', ['nodes', 'metrics']);


// var log = function(result){console.log(result);};
// garganrest.nodes.get(log);
// garganrest.nodes.get(167, log);
// garganrest.nodes.delete(167, log);
// garganrest.nodes.get({
//     pagination_offset: 0,
//     pagination_limit: 10,
//     type: ['DOCUMENT'],
//     parent_id: 2,
// }, log);
