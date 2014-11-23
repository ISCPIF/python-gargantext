(function($) {


    $.fn.graphIt = function(_width, _height) {
        
        var container = $('<div>').addClass('graphit-container').appendTo( this.first() );
        var container2 = $('<div>').addClass('graphit-container-2').appendTo( this.first() );
        var data;
        var method;
        var _chartObject;

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
        
        // different types of grouping
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
        };

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
            labels.push(dimensions[1].key + ' (' + keywordsList[k] + ')');
        }
        // var _chartObject = new Dygraph(container[0], linearData);
        var _chartObject = new Dygraph(container[0], linearData, {
            labels: labels,
        });

        // console.log(associativeData);
        console.log(linearData);
        console.log(dimensions);


        return container;
    };

})(jQuery);



var graph = $('.graph-it').graphIt(640, 480);