(function($) {


    $.fn.graphIt = function(_width, _height) {

        // Settings: ways to group data
        var groupings = this.groupings = {
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
        
        // Main container
        var container = $('<div>').addClass('graphit-container').appendTo( this.first() );


        var data;

        var method;
        var chartObject;

        var width, height;

        container.feed = function(_data) {
            data = _data;
            var dimensions = data[0].length;
        };
        container.resize = function(_width, _height) {
            width = _width;
            height = _height;
            dcChart.width(width).height(height);
            container.width(width).height(height);
        // .dimension(fluctuation)
        // .group(fluctuationGroup)
        // .elasticY(true)
            return container;
        };
        container.plot = function(_method) {
            method = _method;
            container.empty();
        };

        container.css('background', '#FFF');

        
        var corpusId = 13410;
        var series = [];
        var keywordsList = ['bee,bees', 'brain,virus'];
        var dimensions;

        // generate data
        for (var i=0; i<keywordsList.length; i++) {
            keywords = keywordsList[i];
            // get data from server
            var data;
            $.ajax('/api/corpus/' + corpusId + '/data', {
                async: false,
                success: function(response) {data = response;},
                data: {
                    mesured:    'documents.count',
                    parameters: ['metadata.publication_date'],
                    filters:    ['ngram.terms|' + keywords],
                    format:     'json',
                },
            });
            dimensions = data.dimensions;
            // add to the series
            series.push({
                name: keywords,
                data: data.list,
            });
        }
        
        

        var grouping = groupings.datetime.year;

        // generate associative data
        var associativeData = {};
        for (var s=0; s<series.length; s++) {
            var data = series[s].data;
            for (var d=0; d<data.length; d++) {
                var row = data[d];
                var x = grouping.truncate(row[0]);
                var y = row[1];
                if (!associativeData[x]) {
                    associativeData[x] = new Array(series.length);
                    for (var i=0; i<series.length; i++) {
                        associativeData[x][i] = 0;
                    }
                }
                associativeData[x][s] += y;
            }
        };

        // now, flatten this
        var linearData = [];
        for (var x in associativeData) {
            var row = associativeData[x];
            row.unshift(x);
            linearData.push(row);
        }

        // extrema retrieval & scalar data formatting
        for (var d=0; d<dimensions.length; d++) {
            dimensions[d].extrema = {};
        }
        var keys = {};
        for (var r=0; r<linearData.length; r++) {
            var row = linearData[r];
            for (var d=0; d<dimensions.length; d++) {
                var value = row[d];
                var dimension = dimensions[d];
                switch (dimension.type) {
                    case 'datetime':
                        value += '2000-01-01 00:00:00'.substr(value.length);
                        value = new Date(value.replace(' ', 'T') + '.000Z');
                        break;
                    case 'numeric':
                        value = +value;
                        break;
                }
                if (dimension.extrema.min == undefined || value < dimension.extrema.min) {
                    dimension.extrema.min = value;
                }
                if (dimension.extrema.max == undefined || value > dimension.extrema.max) {
                    dimension.extrema.max = value;
                }
                row[d] = value;
            }
            keys[row[0]] = true;
        }

        // interpolation
        var xMin = dimensions[0].extrema.min;
        var xMax = dimensions[0].extrema.max;
        for (var x=xMin; x<xMax; x=grouping.next(x)) {
            if (!keys[x]) {
                // TODO: this below is just WRONG
                var row = [x, 0, 0];
                linearData.push(row);
            }
        }
        linearData.sort(function(row1, row2) {
            return row1[0] > row2[0];
        });


        // do the graph!
        var labels = [dimensions[0].key];
        for (var k=0; k<keywordsList.length; k++) {
            labels.push(keywordsList[k]);
        }
        // var _chartObject = new Dygraph(container[0], linearData);
        chartObject = new Dygraph(container[0], linearData, {
            // legends
            legend: 'always',
            xlabel: dimensions[0].key,
            ylabel: dimensions[1].key,
            labels: labels,
            axisLabelColor: 'black',

            // appearance
            fillGraph: true,

            // smoothing
            showRoller: false,
            rollPeriod: 5,
        });

        // console.log(associativeData);
        console.log(linearData);
        console.log(dimensions);


        return container;
    };

})(jQuery);




var selectProject = $('<select>').appendTo('.visualization');
var selectCorpus = $('<select>').appendTo('.visualization');
var divFilter = $('<div>').appendTo('.visualization');

// Load projects
$.get('/api/nodes', {type:'Project'}, function(collection) {
    selectProject.empty();
    for (var i=0; i<collection.length; i++) {
        var node = collection[i];
        $('<option>').val(node.id).text(node.text).appendTo(selectProject);
    }
    selectProject.change();
});

// Load corpora
selectProject.change(function() {
    var projectId = selectProject.val();
    selectCorpus.empty();
    $.get('/api/nodes', {type:'Corpus', parent:projectId}, function(collection) {
        $.each(collection, function(i, node) {
            $('<option>').val(node.id).text(node.text).appendTo(selectCorpus);
        });
        selectCorpus.change();
    });
});

// Load metadata
selectCorpus.change(function() {
    var corpusId = selectCorpus.val();
    // alert(corpusId);
    divFilter.empty();
    //
    $.get('/api/corpus/' + corpusId + '/metadata', function(collection) {
        var selectType = $('<select>').appendTo(divFilter);
        //
        $('<option>').text('ngrams').appendTo(selectType);
        var spanNgrams = $('<span>').appendTo(divFilter).hide();
        var inputNgrams = $('<input>').appendTo(spanNgrams);
        //
        $('<option>').text('metadata').appendTo(selectType);
        var spanMetadata = $('<span>').appendTo(divFilter).hide();
        var selectMetadata = $('<select>').appendTo(spanMetadata);
        var spanMetadataValue = $('<span>').appendTo(spanMetadata);
        $.each(collection, function(i, metadata) {
            $('<option>')
                .data(metadata)
                .text(metadata.text)
                .appendTo(selectMetadata);
        });
        //
        selectMetadata.change(function() {
            var metadata = selectMetadata.find(':selected').data();
            spanMetadataValue.empty();
            if (metadata.type == 'datetime') {
                $('<span>').text(' between: ').appendTo(spanMetadataValue);
                $('<input>').appendTo(spanMetadataValue)
                    .blur(function() {
                        var input = $(this);
                        var date = input.val();
                        date += '2000-01-01'.substr(date.length);
                        input.val(date);
                    }).datepicker({dateFormat: 'yy-mm-dd'});
                $('<span>').text(' and: ').appendTo(spanMetadataValue);
                $('<input>').appendTo(spanMetadataValue)
                    .blur(function() {
                        var input = $(this);
                        var date = input.val();
                        date += '2000-01-01'.substr(date.length);
                        input.val(date);
                    }).datepicker({dateFormat: 'yy-mm-dd'});
            } else if (metadata.values) {
                $('<span>').text(' is: ').appendTo(spanMetadataValue);
                var selectMetadataValue = $('<select>').appendTo(spanMetadataValue);
                $.each(metadata.values, function(i, value) {
                    $('<option>').text(value).appendTo(selectMetadataValue);
                });
                selectMetadataValue.change().focus();
            } else {
                $('<span>').text(' contains: ').appendTo(spanMetadataValue);
                $('<input>').appendTo(spanMetadataValue).focus();
            }
        });
        //
        selectType.change(function() {
            divFilter.children().filter('span').hide();
            switch (selectType.val()) {
                case 'ngrams':
                    spanNgrams.show();
                    break;
                case 'metadata':
                    spanMetadata.show();
                    break;
            }
        }).change();
    });
});






// $('.tree').jstree({
//     'core' : {
//         'data' : {
//             'url' : function(node) {
//                 var url = '/api/nodes?' + ((node.id === '#')
//                     ? 'type=Project'
//                     : ('parent=' + node.id)
//                 );
//                 console.log(url);
//                 return url;
//             },
//         },
//     },
//     "plugins" : ["types"],
//     "types" : {
//         "#" : {
//           "max_children" : 1, 
//           "max_depth" : 4, 
//           "valid_children" : ["root"]
//         },
//         "Project" : {
//           "icon" : "http://www.jstree.com/static/3.0.8/assets/images/tree_icon.png",
//           "valid_children" : ["default"]
//         },
//         "Corpus" : {
//           "valid_children" : ["default","file"]
//         },
//         "Document" : {
//           "icon" : "glyphicon glyphicon-file",
//           "valid_children" : []
//         }
//   },
// });

// var graph = $('.graph-it').graphIt(640, 480);