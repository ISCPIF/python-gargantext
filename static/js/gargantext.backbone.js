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


var MetadataList = Backbone.Model.extend({
    urlRoot: '/api/nodes/(:/nodeId)/children/metadata',
    defaults: function() {
        return {
            key: '',
            type: 'string',
            values: null,
        };
    }
});

var Filter = Backbone.Model.extend({

    defaults: function() {
        return {
            entity: null,
            key: null,
            transformation: null,
            operator: null,
            value: null
        };
    }

});


var FilterList = Backbone.Collection.extend({

    model: Filter

});


var FilterView = Backbone.View.extend({

    tagName: 'li',
    className: 'filter',
    template: _.template($('#filter-template').html()),
    events: {
        'change select[name=entity]': 'changeEntity',
        'click button.remove': 'clear'
    },

    initialize: function(){
        // this.model.bind('reset', this.render);
        // this.model.bind('change', this.render);
        // this.model.bind('destroy', this.clear);
        // this.render();
    },

    changeEntity: function(){
        alert('CHANGE')
    },

    render: function() {
         // this.$el.html(this.template(this.model.toJSON()));
        this.$el.html(this.template({}));
        return this;
    },

    clear: function() {
        // alert('CLEAR');
        // this.model.invoke('destroy');
        this.model.destroy();
    }

});



var FilterListView = Backbone.View.extend({

    tagName: 'div',
    className: 'filters',
    template: _.template($('#filterlist-template').html()),
    events: {
        'click button.add': 'addOne'
    },

    initialize: function(parameters) {
        this.filterList = new FilterList();
        this.metadataList = new MetadataList({nodeId: parameters.nodeId});
        console.log(this.metadataList.fetch({nodeId: parameters.nodeId}))
        this.listenTo(this.filterList, 'add', this.addOne);
        this.listenTo(this.filterList, 'reset', this.addAll);
        this.listenTo(this.filterList, 'all', this.render);
    },

    render: function() {
        // render template
        var rendered = this.$el.html(this.template({}));
        // return the object
        return this;
    },

    addOne: function(filter){
        var view = new FilterView({model: filter});
        this.$('ul.filters').append(
            view.render(filter).$el
        );
    }

});

