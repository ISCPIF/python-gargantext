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
    $scope.operators = operators;
    $scope.filters = [];
    $scope.addFilter = function() {
        $scope.filters.push({});
    };
    $scope.removeFilter = function(filterIndex) {
        var filter = $scope.filters[filterIndex];
        $scope.filters.splice(filterIndex, 1);
        console.log($scope.filters);
    };
    $http.get('/api/nodes/39576/children/metadata').success(function(response) {
        $scope.entities = {
            metadata: response.data,
            ngrams: [
                {key:'terms', type:'string'},
                {key:'terms count', type:'integer'}
            ]
        };
    });
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