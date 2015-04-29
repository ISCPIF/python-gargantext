// General container
var container = $('.visualization');

// Graph container
var divChart = $('<div>').appendTo(container);

// Settings: ways to group data
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



var graphIt = function(corpusId, getDataCollection, groupingKey, smoothing) {

    divChart.empty();

    // Get data from server
    var dimensions;
    var series = [];
    $.each(getDataCollection, function(i, getData) {
        var responseData;
        $.ajax('/api/corpus/' + corpusId + '/data', {
            async: false,
            success: function(response) {responseData = response;},
            data: getData,
        });
        dimensions = responseData.dimensions;
        // add to the series
        series.push({
            name: '#' + i,
            data: responseData.list,
        });
    });

    var grouping = groupings.datetime[groupingKey];

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
    // var labels = [dimensions[0].key];
    // for (var k=0; k<keywordsList.length; k++) {
    //     labels.push(keywordsList[k]);
    // }
    // var _chartObject = new Dygraph(container[0], linearData);
    chartObject = new Dygraph(divChart[0], linearData, {
        // legends
        legend: 'always',
        xlabel: dimensions[0].key,
        ylabel: dimensions[1].key,
        // labels: labels,
        axisLabelColor: 'black',

        // appearance
        fillGraph: true,

        // smoothing
        showRoller: false,
        rollPeriod: +smoothing,

        // dimensions
        width: container.width(),
        height: container.width() / 3,
    });

    // console.log(associativeData);
    // console.log(linearData);
    // console.log(dimensions);

};



var ulDatasets = $('<ul>').prependTo(container);
var inputSmoothing = $('<input>').prependTo(container).blur(function() {
    var val = $(this).val();
    if (isNaN(val)) {
        val = 1;
    }
    val = Math.round(val);
    if (val < 1) {
        val = 1;
    }
    $(this).val(val);
}).val(1);
container.prepend(' with a smoothing of ');
var selectGrouping = $('<select>').prependTo(container);
container.prepend(', view by publication ');
var selectCorpus = $('<select>').prependTo(container);
container.prepend(', corpus ');
var selectProject = $('<select>').prependTo(container);
container.prepend('In the project ');

var hyperdataCollection;
var corpusId;

// how shall we group the data?
$.each(groupings.datetime, function(text, grouping) {
    $('<option>').text(text).val(text).appendTo(selectGrouping);
});
selectGrouping.val('year');


var emWait = $('<em>').text('Loading, please wait...').insertAfter(ulDatasets);
var buttonAddDataset = $('<button>').text('Add a dataset').insertAfter(ulDatasets).hide();
var buttonView = $('<button>').text('Graph it!').click(function(e) {
    var getDataCollection = [];
    ulDatasets.children().filter('li').each(function(i, liDataset) {
        liDataset = $(liDataset);
        var getData = {
            mesured:      liDataset.find('*[name]').first().val(),
            parameters:   ['hyperdata.publication_date'],
            filters:      [],
            format:       'json',
        };
        liDataset.find('li *[name]:visible').each(function(i, field){
            field = $(field);
            var filter = field.attr('name') + '.' + field.val();
            getData.filters.push(filter);
        });
        getDataCollection.push(getData);
    });
    graphIt(
        selectCorpus.val(),
        getDataCollection,
        selectGrouping.val(),
        inputSmoothing.val()
    );
}).insertAfter(ulDatasets).hide();


// Load hyperdata
selectCorpus.change(function() {
    corpusId = selectCorpus.val();
    emWait.show();
    ulDatasets.empty();
    $.get('/api/corpus/' + corpusId + '/hyperdata', function(collection) {
        // Unleash the power of the filter!
        emWait.hide();
        buttonAddDataset.show();
        buttonView.show();
        hyperdataCollection = collection;
        buttonAddDataset.click();
    });
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

// Load projects
$.get('/api/nodes', {type:'Project'}, function(collection) {
    selectProject.empty();
    for (var i=0; i<collection.length; i++) {
        var node = collection[i];
        $('<option>').val(node.id).text(node.text).appendTo(selectProject);
    }
    selectProject.change();
});

// Add a dataset
buttonAddDataset.click(function() {

    var liDataset = $('<li>').appendTo(ulDatasets);
    // Can we remove this please?
    $('<button>').appendTo(liDataset).text('x').click(function() {
        liDataset.remove();
    });
    // What do we count?
    liDataset.append(' Count ');
    var selectCounted = $('<select>')
        .attr('name', 'mesured')
        .appendTo(liDataset);
    $('<option>')
        .text('documents')
        .val('documents.count')
        .appendTo(selectCounted);
    $('<option>')
        .text('ngrams')
        .val('ngrams.count')
        .appendTo(selectCounted);
    liDataset.append(' ');
    var buttonFilter = $('<button>')
        .text('(add a filter)')
        .appendTo(liDataset);
    // Add a filter when asked
    var ulFilters = $('<ul>').appendTo(liDataset);
    var addFilter = function(hyperdataCollection) {
        var liFilter = $('<li>').appendTo(ulFilters);
        liFilter.append('...where the ');
        // Type of filter: ngrams
        var selectType = $('<select>').appendTo(liFilter);
        $('<option>').text('ngrams').appendTo(selectType);
        var spanNgrams = $('<span>').appendTo(liFilter).hide();
        spanNgrams.append(' contain ');
        var inputNgrams = $('<input>')
            .attr('name', 'ngrams.in')
            .appendTo(spanNgrams);
        spanNgrams.append(' (comma-separated ngrams)')
        // Type of filter: hyperdata
        $('<option>').text('hyperdata').appendTo(selectType);
        var spanHyperdata = $('<span>').appendTo(liFilter).hide();
        var selectHyperdata = $('<select>').appendTo(spanHyperdata);
        var spanHyperdataValue = $('<span>').appendTo(spanHyperdata);
        $.each(hyperdataCollection, function(i, hyperdata) {
            $('<option>')
                .appendTo(selectHyperdata)
                .text(hyperdata.text)
                .data(hyperdata);
        });
        // How do we present the hyperdata?
        selectHyperdata.change(function() {
            var hyperdata = selectHyperdata.find(':selected').data();
            spanHyperdataValue.empty();
            if (hyperdata.type == 'datetime') {
                spanHyperdataValue.append(' is between ');
                $('<input>').appendTo(spanHyperdataValue)
                    .attr('name', 'hyperdata.' + hyperdata.key + '.gt')
                    .datepicker({dateFormat: 'yy-mm-dd'})
                    .blur(function() {
                        var input = $(this);
                        var date = input.val();
                        date += '2000-01-01'.substr(date.length);
                        input.val(date);
                    });
                spanHyperdataValue.append(' and ');
                $('<input>').appendTo(spanHyperdataValue)
                    .attr('name', 'hyperdata.' + hyperdata.key + '.lt')
                    .datepicker({dateFormat: 'yy-mm-dd'})
                    .blur(function() {
                        var input = $(this);
                        var date = input.val();
                        date += '2000-01-01'.substr(date.length);
                        input.val(date);
                    });
            } else if (hyperdata.values) {
                $('<span>').text(' is ').appendTo(spanHyperdataValue);
                var selectHyperdataValue = $('<select>')
                    .attr('name', 'hyperdata.' + hyperdata.key + '.eq')
                    .appendTo(spanHyperdataValue);
                $.each(hyperdata.values, function(i, value) {
                    $('<option>')
                        .text(value)
                        .appendTo(selectHyperdataValue);
                });
                selectHyperdataValue.change().focus();
            } else {
                spanHyperdataValue.append(' contains ');
                $('<input>')
                    .attr('name', 'hyperdata.' + hyperdata.key + '.contains')
                    .appendTo(spanHyperdataValue)
                    .focus();
            }
        }).change();
        // Ngram or hyperdata?
        selectType.change(function() {
            var spans = liFilter.children().filter('span').hide();
            switch (selectType.val()) {
                case 'ngrams':
                    spanNgrams.show().find('input').focus();
                    break;
                case 'hyperdata':
                    spanHyperdata.show();
                    break;
            }
        }).change();
    };

    buttonFilter.click(function(e) {
        addFilter(hyperdataCollection);
    });
});




/*
 $('.tree').jstree({
     'core' : {
         'data' : {
             'url' : function(node) {
                 var url = '/api/nodes?' + ((node.id === '#')
                     ? 'type=Project'
                     : ('parent=' + node.id)
                 );
                 console.log(url);
                 return url;
             },
         },
     },
     "plugins" : ["types"],
     "types" : {
         "#" : {
           "max_children" : 1, 
           "max_depth" : 4, 
           "valid_children" : ["root"]
         },
         "Project" : {
           "icon" : "http://www.jstree.com/static/3.0.8/assets/images/tree_icon.png",
           "valid_children" : ["default"]
         },
         "Corpus" : {
           "valid_children" : ["default","file"]
         },
         "Document" : {
           "icon" : "glyphicon glyphicon-file",
           "valid_children" : []
         }
   },
 });
*/
var graph = $('.graph-it').graphIt(640, 480);
