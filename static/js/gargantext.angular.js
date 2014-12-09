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



var gargantext = angular.module('Gargantext', []);

gargantext.controller("FilterListController", function($scope, $http) {
    // variables initialization
    $scope.operators = operators;
    $scope.filters = [];
    // queried entities retrieval
    $http.get('/api/nodes/39576/children/metadata').success(function(response) {
        $scope.entities = {
            metadata: response.data,
            ngrams: [
                {key:'terms', type:'string'},
                {key:'terms count', type:'integer'}
            ]
        };
    });
    // add a filter
    $scope.addFilter = function() {
        $scope.filters.push({});
    };
    // remove a filter
    $scope.removeFilter = function(filterIndex) {
        var filter = $scope.filters[filterIndex];
        $scope.filters.splice(filterIndex, 1);
        console.log($scope.filters);
    };
});

gargantext.controller("QueryController", function($scope, $http) {
    // variables initialization
    $scope.operators = operators;
    $scope.query = {
        pagination: {
            offset: 0,
            limit: 20
        },
        retrieve: {
            type: "fields",
            list: ["id", "name"]
        },
        filters: [],
        sort: ["name"]
    };
    $scope.results = [];
    $scope.resultsCount = undefined;
    $scope.corpora = [];
    // corpus retrieval
    $.get('/api/nodes?type=Corpus').success(function(response){
        $scope.corpora = response.data;
    });
    // filtered entities retrieval
    $http.get('/api/nodes/39576/children/metadata').success(function(response){
        $scope.entities = {
            metadata: response.data,
            ngrams: [
                {key:'terms', type:'string'},
                {key:'terms count', type:'integer'}
            ]
        };
    });
    // add a filter
    $scope.addFilter = function() {
        $scope.query.filters.push({});
    };
    // remove a filter
    $scope.removeFilter = function(filterIndex) {
        var filter = $scope.query.filters[filterIndex];
        $scope.query.filters.splice(filterIndex, 1);
    };
    // perform a query
    $scope.postQuery = function() {
        if ($scope.corpusId) {
            var url = '/api/nodes/' + $scope.corpusId + '/children/queries';
            $http.post(url, $scope.query).success(function(response){
                $scope.resultsCount = response.pagination.total;
                $scope.results = response.data;
                console.log(response);
            });
        }
    }
});

// gargantext.controller("FilterController", function($scope, $http) {
//     $scope.operators = operators;
//     $http.get('/api/nodes/39576/children/metadata').success(function(response) {
//         $scope.entities = {
//             metadata: response.data,
//             ngrams: [
//                 {key:'terms', type:'string'},
//                 {key:'terms count', type:'integer'}
//             ]
//         };
//     });
// });