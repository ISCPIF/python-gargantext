// Documentations:
// n3-charts/line-chart



// define operators (for hyperdata filtering, according to the considered type)
var operators = {
    'text': [
        {'label': 'contains',       'key': 'contains'},
        {'label': 'does not contain',   'key': 'doesnotcontain'},
    ],
    'string': [
        {'label': 'starts with',    'key': 'startswith'},
        {'label': 'contains',       'key': 'contains'},
        {'label': 'does not contain',       'key': 'doesnotcontain'},
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
$.each(operators, function(type, type_operators) {
    type_operators.unshift({});
});

// define available periods of time
var periods = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year', 'decade', 'century'];


var strDate = function(date) {
    return date.getFullYear() + '-' +
            ('00' + (date.getMonth() + 1)).slice(-2) + '-' +
            ('00' + date.getDate()).slice(-2) + 'T' +
            ('00' + date.getHours()).slice(-2) + ':' +
            ('00' + date.getMinutes()).slice(-2) + ':' +
            ('00' + date.getSeconds()).slice(-2) + 'Z';
}
var addZero = function(x) {
    return (x<10) ? ('0'+x) : x;
};
var addZeros = function(x, n) {
    x = x.toString();
    return '0000'.substr(0, n - x.length) + x;
};
var groupings = {
    datetime: {
        century: {
            representation: function(x) {return x.toISOString().substr(0, 2) + 'th century'},
            truncate: function(x) {return x.substr(0, 2) + '00-01-01T00:00:00Z';},
            next: function(x) {
                x = new Date(x);
                x.setFullYear(x.getFullYear()+100);
                x.setHours(0);
                return strDate(x);
            },
        },
        decade: {
            representation: function(x) {return x.toISOString().substr(0, 3)} + '0s',
            truncate: function(x) {return x.substr(0, 3) + '0-01-01T00:00:00Z';},
            next: function(x) {
                x = new Date(x);
                x.setFullYear(x.getFullYear() + 10);
                x.setHours(0);
                return strDate(x);
            },
        },
        year: {
            representation: function(x) {return x.toISOString().substr(0, 4)},
            truncate: function(x) {return x.substr(0, 4) + '-01-01T00:00:00Z';},
            next: function(x) {
                var y = parseInt(x.substr(0, 4));
                return addZeros(y + 1, 4) + x.substr(4);
            },
        },
        month: {
            representation: function(x) {return x.toISOString().substr(0, 7)},
            truncate: function(x) {return x.substr(0, 7) + '-01T00:00:00Z';},
            next: function(x) {
                var m = parseInt(x.substr(5, 2));
                if (m == 12) {
                    var y = parseInt(x.substr(0, 4));
                    return addZeros(y + 1, 4) + '-01' + x.substr(7);
                } else {
                    return x.substr(0, 5) + addZero(m + 1) + x.substr(7);
                }
            },
        },
        day: {
            representation: function(x) {return x.toISOString().substr(0, 10)},
            truncate: function(x) {return x.substr(0, 10) + 'T00:00:00Z';},
            next: function(x) {
                x = new Date(x);
                x.setDate(x.getDate() + 1);
                x.setHours(0);
                return strDate(x);
            },
        },
    },
    numeric: {
        unit: {
            representation: function(x) {return x.toString()},
            truncate: function(x) {return Math.round(x)},
            next: function(x) {return x+1;},
        },
    },
};


// Define the application
var gargantext = angular.module('Gargantext', ['n3-charts.linechart', 'ngCookies', 'ngTagsInput']);


// Customize the application's scope
angular.module('Gargantext').run(function($rootScope, $http, $cookies){
    // Access Math library from anywhere in the scope of the application
    $rootScope.Math = Math;
    // Access to an HSB to RGB converter
    $rootScope.getColor = function(i, n){
        var h = .3 + (i / n) % 1;
        var s = .7;
        var v = .8;
        var i = Math.floor(h * 6);
        var f = h * 6 - i;
        var p = v * (1 - s);
        var q = v * (1 - f * s);
        var t = v * (1 - (1 - f) * s);
        var r, g, b;
        switch (i % 6) {
            case 0: r = v; g = t; b = p; break;
            case 1: r = q; g = v; b = p; break;
            case 2: r = p; g = v; b = t; break;
            case 3: r = p; g = q; b = v; break;
            case 4: r = t; g = p; b = v; break;
            case 5: r = v; g = p; b = q; break;
        }
        r = Math.round(255 * r);
        g = Math.round(255 * g);
        b = Math.round(255 * b);
        var color = 'rgb(' + r + ',' + g + ',' + b + ')';
        return color;
    };
    // Access to a range function, very similar to the one available in Python
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
    // Pre-defined stuff
    $rootScope.operators = operators;
    $rootScope.periods = periods;
    // For CSRF token compatibility with Django
    $http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
});


// Controller for datasets
gargantext.controller('DatasetController', function($scope, $http) {

    // are we loading data from the server right now?
    $scope.is_loading = false;

    // initital parameters for the y-axis of the query
    $scope.query_y = {
        'value': 'documents_count',
        'is_relative': false,
        'divided_by': 'total_ngrams_count',
    };

    // filters: corpora retrieval
    $scope.corpora = [];
    if (/^\/projects\/\d+\/corpora\/\d+/.test(location.pathname)) {
        $scope.project_id = parseInt(location.pathname.split('/')[2]);
    } else {
        console.error('The id of the project has to be set.');
    }
    $scope.updateCorpora = function() {
        $http.get('/api/nodes?types[]=CORPUS&parent_id=' + $scope.project_id, {cache: true}).success(function(response){
            $scope.corpora = response.records;
            // Initially set to what is indicated in the URL
            if (/^\/projects\/\d+\/corpora\/\d+/.test(location.pathname)) {
                var corpus_id = parseInt(location.pathname.split('/')[4]);
                $.each($scope.corpora, function(c, corpus) {
                    corpus.is_selected = (corpus.id == corpus_id);
                });
                $scope.updateHyperdataList();
                $scope.updateDataset();
            }
        });
    };
    var getSelectedCorporaIdList = function() {
        var corpus_id_list = [];
        $.each($scope.corpora, function(c, corpus) {
            if (corpus.is_selected) {
                corpus_id_list.push(corpus.id);
            }
        });
        return corpus_id_list;
    }
    $scope.updateCorpora();

    // filters: ngrams
    $scope.getNgrams = function(query) {
        var url = '/api/ngrams?limit=10';
        url += '&contain=' + encodeURI(query);
        url += '&corpus_id=' + getSelectedCorporaIdList().join(',');
        var appendTransform = function(defaults, transform) {
            defaults = angular.isArray(defaults) ? defaults : [defaults];
            return defaults.concat(transform);
        }
        return $http.get(url, {
            cache: true,
            transformResponse: appendTransform($http.defaults.transformResponse, function(value) {
                return value.data;
            })
        });
    };

    // filters: corpora
    $scope.corporaSelectNone = function() {
        $.each($scope.corpora, function(c, corpus){
            corpus.is_selected = false;
        });
        $scope._updateHyperdataList(function() {
            $scope.updateDataset();
        });
    };
    $scope.corporaSelectAll = function() {
        $.each($scope.corpora, function(c, corpus){
            corpus.is_selected = true;
        });
        $scope._updateHyperdataList(function() {
            $scope.updateDataset();
        });
    };

    // filters: hyperdata, according to the considered corpora
    $scope.hyperdataList = [];
    $scope.updateHyperdataTimer = null;
    $scope.setHyperdataList = function(hyperdataList) {
        // add an empty item for each value
        $.each(hyperdataList, function(h, hyperdata) {
            if (hyperdata.values) {
                hyperdata.values.unshift(undefined);
            }
        });
        // do not keep the ones we are not interested into
        var rejectedHyperdata = ['doi', 'volume', 'page', 'count'];
        $scope.hyperdataList = [];
        $.each(hyperdataList, function(h, hyperdata) {
            if (rejectedHyperdata.indexOf(hyperdata.key) == -1) {
                hyperdata.name = hyperdata.key.split('_')[0];
                $scope.hyperdataList.push(hyperdata);
            }
        });
    }
    $scope.updateHyperdataList = function() {
        if ($scope.updateHyperdataTimer) {
            clearTimeout($scope.updateHyperdataTimer);
        }
        $scope.updateHyperdataTimer = setTimeout($scope._updateHyperdataList, 500);
    };
    $scope._updateHyperdataList = function(callback) {
        var corpus_id_list = getSelectedCorporaIdList();
        if (corpus_id_list && corpus_id_list.length) {
            var url = '/api/hyperdata?corpus_id=';
            url += corpus_id_list.join(',');
            $scope.is_loading = true;
            $http.get(url, {cache: true}).success(function(response){
                $scope.is_loading = false;
                $scope.setHyperdataList(response.data);
                if (callback) {
                    callback();
                }
            });
        } else {
            $scope.hyperdataList = [];
        }
    };

    // update the dataset, according to the various filters applied to it
    $scope.updateDatasetTimer = null;
    $scope.updateDataset = function() {
        if ($scope.updateDatasetTimer) {
            clearTimeout($scope.updateDatasetTimer);
        }
        $scope.updateDatasetTimer = setTimeout($scope._updateDataset, 500);
    };
    $scope._updateDataset = function() {
        // parameters
        var parameters = {
            'x': {
                'with_empty': true,
                'resolution': $scope.query_x.resolution,
                'value': 'publication_date',
            },
            'y': {
                'value': $scope.query_y.value,
            },
            'filter': {
            },
            'format': 'json',
        };
        // x: normalization
        if ($scope.query_y.is_relative) {
            parameters.y.divided_by = $scope.query_y.divided_by;
        }
        // filter: ngrams
        if ($scope.query_y.ngrams && $scope.query_y.ngrams.length) {
            parameters.filter.ngrams = [];
            $.each($scope.query_y.ngrams, function(n, ngram) {
                parameters.filter.ngrams.push(ngram.terms)
            })
            console.log($scope.query_y.ngrams);
        }
        // filter : corpora
        parameters.filter.corpora = [];
        corpus_ids = getSelectedCorporaIdList() ;
        for (i in corpus_ids) {
        console.log(corpus_ids);
        parameters.filter.corpora.push(corpus_ids[i]);
        }
        // filter: hyperdata
        parameters.filter.hyperdata = [];
        $.each($scope.hyperdataList, function(h, hyperdata) {
            if ((hyperdata.values || hyperdata.operator) && hyperdata.value) {
                if (hyperdata.values) {
                    hyperdata.operator = '=';
                }
                parameters.filter.hyperdata.push({
                    'key': hyperdata.key,
                    'operator': hyperdata.operator,
                    'value': hyperdata.value
                });
            }
        });
        // retrieve data
        var url = '/api/nodes/' + $scope.project_id + '/histories';
        $scope.is_loading = true;
        $http.post(url, parameters, {cache: true}).success(function(response){
            $scope.is_loading = false;
            // event firing to parent
            $scope.$emit('updateDatasets', {
                response: response,
                dataset_index: $scope.$index,
            });
        });
    };
    $scope.$on('updateDataset', function(e, data) {
        $scope.updateDataset();
    });

});

// Controller for graphs
gargantext.controller('GraphController', function($scope, $http, $element) {


    // initial values
    $scope.query_x = {
        'resolution': 'year'
    };

    // initialization
    $scope.datasets = [{}];
    $scope.options = {
        stacking: false
    };
    $scope.seriesOptions = {
        thicknessNumber: 3,
        thickness: '3px',
        type: 'column',
        striped: false
    };
    $scope.graph = {
        data: [],
        options: {
            axes: {
                x: {key: 'x', type: 'date'},
                y: {key: 'y', type: 'linear'},
            },
            tension: 1.0,
            lineMode: 'linear',
            // tooltip: {mode: 'scrubber', formatter: function(x, y, series) {
            //     var grouping = groupings.datetime[$scope.groupingKey];
            //     return grouping.representation(x) + ' → ' + y;
            // }},
            drawLegend: true,
            drawDots: true,
            columnsHGap: 5
        }
    };

    // add a dataset
    $scope.addDataset = function() {
        $scope.datasets.push({});
    };
    // remove a dataset
    $scope.removeDataset = function(datasetIndex) {
        if ($scope.datasets.length > 1) {
            $scope.datasets.splice(datasetIndex, 1);
            dataset_results.splice(datasetIndex, 1);
            $scope.updateDatasets();
        } else {
            alert('You can not remove the last dataset.')
        }
    };

    // update the datasets (catches the event thrown by children dataset controllers)
    $scope.updateDatasets = function(must_refresh) {
        // refresh all data
        if (must_refresh) {
            $scope.$broadcast('updateDataset');
        }
        // create temporary representation for the result
        var values = {}
        var n = dataset_results.length;
        for (var i=0; i<n; i++) {
            var result = dataset_results[i];
            var key = 'y' + i;
            for (var j=0, m=result.length; j<m; j++) {
                var date = result[j][0];
                var value = result[j][1];
                if (!values[date]) {
                    values[date] = {};
                }
                values[date][key] = value;
            }
        }
        // put that in an array
        var data = [];
        $.each(values, function(date, keys_values) {
            var row = {x: new Date(date)};
            for (var i=0; i<n; i++) {
                var key = 'y' + i;
                row[key] = keys_values[key] || 0;
            }
            data.push(row);
        });
        // sort the array
        data.sort(function(a, b) {
            return (new Date(a.x)).getTime() - (new Date(b.x)).getTime();
        });
        // show time!
        $scope.graph.data = data;
        // update series names
        var series = [];
        for (var i=0; i<n; i++) {
            var seriesElement = {
                id: 'series_'+ i,
                y: 'y'+ i,
                axis: 'y',
                color: $scope.getColor(i, n),
                label: 'Project, corpus, docs|ngrams, terms'
            };
            angular.forEach($scope.seriesOptions, function(value, key) {
                seriesElement[key] = value;
            });
            series.push(seriesElement);
        }
        $scope.graph.options.series = series;
    };
    var dataset_results = [];
    $scope.$on('updateDatasets', function(e, data) {
        // data extraction
        var dataset_index = data.dataset_index;
        var result = data.response.result;
        // update full results array
        while (dataset_results.length < $scope.datasets.length) {
            dataset_results.push([]);
        }
        while (dataset_results.length > $scope.datasets.length) {
            dataset_results.splice(-1, 1);
        }
        dataset_results[dataset_index] = result;
        $scope.updateDatasets();
    });
});
