// Pre-defined constants
var operators = {
    'text': [
        {'label': 'contains',       'key': 'contains'}
    ],
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
var groupings = {
    datetime: {
        century: {
            truncate: function(x) {return x.substr(0, 2)},
            next: function(x) {x = new Date(x); x.setFullYear(x.getFullYear()+100); return x;},                
        },
        decade: {
            truncate: function(x) {return x.substr(0, 3)},
            next: function(x) {x = new Date(x); x.setFullYear(x.getFullYear()+10); return x;},                
        },
        year: {
            truncate: function(x) {return x.substr(0, 4)},
            next: function(x) {x = new Date(x); x.setFullYear(x.getFullYear()+1); return x;},                
        },
        month: {
            truncate: function(x) {return x.substr(0, 7)},
            next: function(x) {x = new Date(x); x.setMonth(x.getMonth()+1); return x;},                
        },
        day: {
            truncate: function(x) {return x.substr(0, 10)},
            next: function(x) {x = new Date(x); x.setDate(x.getDate()+1); return x;},                
        },
    },
    numeric: {
        unit: {
            truncate: function(x) {return Math.round(x)},
            next: function(x) {return x+1;},
        },
    },
};


// application definition
var gargantext = angular.module('Gargantext', ['n3-charts.linechart']);

// tuning the application's scope
angular.module('Gargantext').run(['$rootScope', function($rootScope){
    $rootScope.Math = Math;
    $rootScope.range = function(min, max, step){
        if (max == undefined){
            max = min;
            min = 0;
        }
        step = step || 1;
        var output = [];
        for (var i=min; i<max; i+=step){
            output.push(i);
        }
        return output;
    };
}]);


gargantext.controller("QueryController", function($scope, $http) {
    // query-specific information
    $scope.filters = [];
    $scope.pagination = {offset:0, limit: 20};
    // results information
    $scope.loading = false;
    $scope.results = [];
    $scope.resultsCount = undefined;
    // corpus retrieval
    $scope.corpora = [];
    $.get('/api/nodes?type=Corpus').success(function(response){
        $scope.corpora = response.data;
        $scope.$apply();
    });
    // update entities depending on the selected corpus
    $scope.updateEntities = function() {
        return true;
        var url = '/api/nodes/' + $scope.corpusId + '/children/metadata';
        $scope.entities = undefined;
        $scope.filters = [];
        $http.get(url).success(function(response){
            $scope.entities = {
                metadata: response.data,
                ngrams: [
                    {key:'terms', type:'string'},
                    {key:'terms count', type:'integer'}
                ]
            };
        });
    };
    // filtering informations retrieval
    $scope.operators = operators;
    // add a filter
    $scope.addFilter = function() {
        $scope.filters.push({});
    };
    // remove a filter
    $scope.removeFilter = function(filterIndex) {
        var filter = $scope.filters[filterIndex];
        $scope.filters.splice(filterIndex, 1);
    };
    // perform a query
    $scope.postQuery = function() {
        if ($scope.corpusId) {
            // change view to loading mode
            $scope.loading = true;
            // query parameters: columns
            var retrieve = {type: 'fields', list: ['id', 'name']};
            // query parameters: pagination
            var pagination = $scope.pagination;
            // query parameters: sort
            var sort = ['name'];
            // query parameters: filters
            var filters = [];
            var keys = ['entity', 'column', 'operator', 'value'];
            for (var i=0, m=$scope.filters.length; i<m; i++) {
                var filter = $scope.filters[i];
                for (var j=0, n=keys.length; j<n; j++) {
                    if (!filter[keys[j]]) {
                        continue;
                    }
                }
                filters.push({
                    field: filter.entity + '.' + filter.column,
                    operator: filter.operator,
                    value: filter.value
                });
            }
            // query URL & body building
            var url = '/api/nodes/' + $scope.corpusId + '/children/queries';
            var query = {
                retrieve: retrieve,
                filters: filters,
                sort: sort,
                pagination: pagination
            };
            // send query to the server
            $http.post(url, query).success(function(response){
                $scope.resultsCount = response.pagination.total;
                $scope.results = response.data;
                $scope.loading = false;
            }).error(function(response){
                console.error(response);
            });
        }
    }
});


gargantext.controller("DatasetController", function($scope, $http) {
    // query-specific information
    $scope.filters = [];
    $scope.pagination = {offset:0, limit: 20};
    // results information
    $scope.loading = false;
    $scope.results = [];
    $scope.resultsCount = undefined;
    // corpus retrieval
    $scope.corpora = [];
    $http.get('/api/nodes?type=Corpus', {cache: true}).success(function(response){
        $scope.corpora = response.data;
    });
    // update entities depending on the selected corpus
    $scope.updateEntities = function() {
        var url = '/api/nodes/' + $scope.corpusId + '/children/metadata';
        $scope.entities = undefined;
        $scope.filters = [];
        $http.get(url, {cache: true}).success(function(response){
            $scope.entities = {
                metadata: response.data,
                ngrams: [
                    {key:'terms', type:'string'},
                    {key:'terms count', type:'integer'}
                ]
            };
        });
        $scope.updateQuery();
    };
    // filtering informations retrieval
    $scope.operators = operators;
    // add a filter
    $scope.addFilter = function() {
        $scope.filters.push({});
    };
    // remove a filter
    $scope.removeFilter = function(filterIndex) {
        var filter = $scope.filters[filterIndex];
        $scope.filters.splice(filterIndex, 1);
    };
    // transmit query parameters to parent elements
    $scope.updateQuery = function() {
        if ($scope.corpusId) {
            // query parameters: sort
            var url = '/api/nodes/' + $scope.corpusId + '/children/queries';
            // filters
            var filters = [];
            var keys = ['entity', 'column', 'operator', 'value'];
            for (var i=0, m=$scope.filters.length; i<m; i++) {
                var filter = $scope.filters[i];
                for (var j=0, n=keys.length; j<n; j++) {
                    if (!filter[keys[j]]) {
                        continue;
                    }
                }
                filters.push({
                    field: filter.entity + '.' + filter.column,
                    operator: filter.operator,
                    value: filter.value
                });
            }
            // event firing to parent(s)
            $scope.$emit('updateDataset', {
                datasetId: $scope.$id,
                url: url,
                filters: filters,
            });
        }
    }
});


gargantext.controller("GraphController", function($scope, $http, $element) {
    // initialization
    $scope.datasets = [{}];
    $scope.queries = {};
    $scope.graph = {
        data: [
            {x: 0, value: 4, otherValue: 14},
            {x: 1, value: 8, otherValue: 1},
            {x: 2, value: 15, otherValue: 11},
            {x: 3, value: 16, otherValue: 147},
            {x: 4, value: 23, otherValue: 87},
            {x: 5, value: 42, otherValue: 45}
        ],
        options: {
            axes: {
                x: {key: 'x', labelFunction: function(value) {return value;}, type: 'linear', min: 0, max: 10, ticks: 2},
                y: {type: 'linear', min: 0, max: 1, ticks: 5},
                y2: {type: 'linear', min: 0, max: 1, ticks: [1, 2, 3, 4]}
            },
            series: [
                {y: 'value', color: 'steelblue', thickness: '2px', type: 'area', striped: true, label: 'Pouet'},
                {y: 'otherValue', axis: 'y2', color: 'lightsteelblue', visible: false, drawDots: true, dotSize: 2}
            ],
            lineMode: 'linear',
            tension: 0.7,
            tooltip: {mode: 'scrubber', formatter: function(x, y, series) {return 'pouet';}},
            drawLegend: true,
            drawDots: true,
            columnsHGap: 5
        }
    };
    // add a dataset
    $scope.addDataset = function() {
        $scope.datasets.push({});
    };
    // perform a query on the server
    $scope.query = function() {
        // reinitialize graph
        $scope.graph.data = [];
        // add all the server request to the queue
        for (var datasetId in $scope.queries) {
            var query = $scope.queries[datasetId];
            var data = {
                filters: query.filters,
                sort: ['metadata.publication_date.day'],
                retrieve: {
                    type: 'aggregates',
                    list: ['count', 'metadata.publication_date.day']
                }
            };
            $http.post(query.url, data, {cache: true}).success(function(response) {
                // values initialization
                var dataset = [];
                var keyX = response.retrieve[0];
                var keyY = response.retrieve[1];
                // data interpolation & transformation
                var xPrev = undefined;
                var rows = response.data;
                for (var i=0, n=rows.length; i<n; i++) {
                    var row = rows[i];
                    var x = row[keyX];
                    var y = new Date(row[keyY]);
                    dataset.push([x, y]);
                }
                // add data to the graph
                // $scope.graph.data.push(dataset);
                $scope.graph.data = dataset;
            }).error(function(response) {
                console.error(response);
            });
        }
        dbg = $scope;
    };
    // update the queries
    $scope.$on('updateDataset', function(e, data) {
        $scope.queries[data.datasetId] = {
            url: data.url,
            filters: data.filters
        };
    });
});