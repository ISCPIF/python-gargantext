var operators = {
    'string': [
        {'label': 'starts with',    'key': 'startswith'},
        {'label': 'contains',       'key': 'contains'},
        {'label': 'ends with',      'key': 'endswith'},
        {'label': 'is',             'key': '='},
        {'label': 'is before',      'key': '<'},
        {'label': 'is after',       'key': '>'}
    ],
    'integer': [
        {'label': 'is',             'key': '='},
        {'label': 'is lower than',  'key': '<'},
        {'label': 'is higher than', 'key': '>'}
    ],
    'float': [
        {'label': 'is',             'key': '='},
        {'label': 'is lower than',  'key': '<'},
        {'label': 'is higher than', 'key': '>'}
    ],
    'datetime': [
        {'label': 'is',             'key': '='},
        {'label': 'is before',      'key': '<'},
        {'label': 'is after',       'key': '>'}
    ],
};


// MODELS


var Metadata = can.Model({
    findAll: 'GET /api/nodes/{parent}/children/metadata'
});


var QueriedNodeList = can.Model({
    findAll: 'POST /api/nodes/{parent}/children/queries'
});


var Filter = can.Model({
    findAll: function(){
        return $.Deferred().resolve([]);
    },
    findOne: function(){
        return $.Deferred().resolve(undefined);
    },
    update: function(){
        return $.Deferred().resolve();
    },
    destroy: function(){
        return $.Deferred().resolve();
    }
}, {});


//  CONTROLLERS


var FilterController = can.Control.extend({
    'init': function(element, options){        
        this.element = element;
        Filter.findAll({}, function(filter){
            element.append(
                $(can.view('FilterView', {filter: filter}))
            );
        });
        this.element.find('li select[name=entity]').each(function() {
            $(this).change();
        });
    },
    'li select[name=entity] change': 'changeEntity',
    'changeEntity': function(element, event){
        var entityName = this.element.find('select[name=entity]').val();
        element.closest('li')
            .find('span.entity').hide()
            .filter('.' + entityName).show();
        // alert(value);
    }
});

var FilterListController = can.Control.extend({
    'init': function(element, options){        
        this.element = element.html( can.view('FilterListView', options) );
        
        
        // Filter.findAll({}, function(filters){
        //     var el = this.element;
        //     el.html( can.view('filterView', {filters: filters}) )
        // });
        // metadata = Metadata.findAll(parameters);
    },
    'button.create click': function(){
        var filterController =  new FilterController(
            this.element.find('ul.filters')
        );
    },
    'filter': function(filter){
        this.options.filter = filter;
        this.on();
    },
    '{filter} destroyed': function(){
        this.element.hide();
    }
});



// var Query = can.Model({
//     'init'  :   function(parameters) {
//     }
// });


