(function($) {


    $.fn.graphIt = function(_width, _height) {
        
        var container = $('<div>').addClass('graphit-container').appendTo( this.first() );
        var container2 = $('<div>').addClass('graphit-container-2').appendTo( this.first() );
        var data;
        var method;
        var dcChart, dcVolumeChart;

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


        // http://dygraphs.com/tutorial.html
        // http://dygraphs.com/data.html
        // http://dygraphs.com/tests/callback.html
        // http://dygraphs.com/legal.html

        
        var corpusId = 13410;
        var series = [];
        var keywordsList = ['bee,bees', 'brain,virus'];
        var dimensions;
        // create the series for future plotting        
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
            // format all data
            for (var j=0; j<data.dimensions.length; j++) {
                var dimension = data.dimensions[j];
                var key = dimension.key;
                var n = data.collection.length;
                for (k=0; k<n; k++) {
                    var value = data.list[k][j];
                    switch (dimension.type) {
                        case 'datetime':
                            value = Date(value.replace(' ', 'T'));
                            break;
                        case 'numeric':
                            value = +value;
                            break;
                    }
                    data.list[k][j] = value;
                    data.collection[k][key] = value;
                }
            }
            // add to the series
            series.push({
                name: keywords,
                data: data.list,
            });
        }
        
        // debugging only
        dbg = series;
        console.log(series);

        container.highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: 'Evolution of documents count over time'
            },
            subtitle: {
                text: 'the results are filtered by ngrams'
            },
            xAxis: {
                type: dimensions[0].type,
                // dateTimeLabelFormats: { // don't display the dummy year
                //     month: '%e. %b',
                //     year: '%b'
                // },
                title: {
                    text: 'Date'
                }
            },
            yAxis: {
                title: {
                    text: 'Documents count'
                },
                min: 0
            },
            tooltip: {
                headerFormat: '<b>{series.name}</b><br>',
                pointFormat: '{point.x:%e. %b}: {point.y:%d} m'
            },
            series: series
        });

        return container;
    };

})(jQuery);



var graph = $('.graph-it').graphIt(640, 480);