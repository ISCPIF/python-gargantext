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

        $.get('/api/corpus/13410/data?mesured=ngrams.count&parameters[]=metadata.publication_date&filters[]=ngram.terms|bee,bees&format=json', function(data) {
            
            var dateFormat = d3.time.format('%Y-%m-%d %H:%M:%S');
            var numberFormat = d3.format('.2f');

            var unit = 'month';

            // format all data
            for (var i=0; i<data.dimensions.length; i++) {
                var dimension = data.dimensions[i];
                var key = dimension.key;
                var otherKey;
                if (dimension.type == 'date') {
                    otherKey = key.replace(/_date$/, '_' + unit);
                }
                data.collection.forEach(function(element) {
                    switch (dimension.type) {
                        case 'date':
                            element[key] = dateFormat.parse(element[key]);
                            break;
                        case 'numeric':
                            element[key] = +element[key];
                            break;
                    }
                });
            }

            // organize data
            var ndx = crossfilter(data.collection);
            var all = ndx.groupAll();

            // define accessors for every dimension
            for (var i=0; i<data.dimensions.length; i++) {
                var dimension = data.dimensions[i];
                dimension.accessor = ndx.dimension(function(element) {
                    return element[otherKey];
                });
            }

            var monthlyMoveGroup = data.dimensions[0].accessor.group().reduceSum(function (d) {
                return d.volume;
                //return Math.abs(+d.close - +d.open);
            });

            var volumeByMonthGroup = data.dimensions[0].accessor.group().reduceSum(function (d) {
                return d.volume / 500000;
            });

            var indexAvgByMonthGroup = data.dimensions[0].accessor.group().reduce(
                function(p, v) {
                    ++p.days;
                    p.total += (+v.open + +v.close) / 2;
                    p.avg = Math.round(p.total / p.days);
                    return p;
                },
                function(p, v) {
                    --p.days;
                    p.total -= (+v.open + +v.close) / 2;
                    p.avg = p.days == 0 ? 0 : Math.round(p.total / p.days);
                    return p;
                },
                function() {
                    return {days: 0, total: 0, avg: 0};
                }
            );

            var moveChart = dc.compositeChart(".graphit-container"); 
            moveChart.width(800)
                    .height(150)
                    .transitionDuration(1000)
                    .margins({top: 10, right: 50, bottom: 25, left: 40})
                    .dimension(data.dimensions[0].accessor)
                    .group(indexAvgByMonthGroup)
                    .valueAccessor(function (d) {
                        return d.value.avg;
                    })
                    .x(d3.time.scale().domain([new Date(1950,01,01), new Date(2014,12,31)]))
                    .round(d3.time.month.round)
                    .xUnits(d3.time.months)
                    .elasticY(true)
                    .renderHorizontalGridLines(true)
                    .renderVerticalGridLines(true)
                    .brushOn(false)
                    .compose([
                        dc.lineChart(moveChart)
                            .group(indexAvgByMonthGroup)
                            .valueAccessor(function (d) {
                                return d.value.avg;
                            })
                            .renderArea(true)
                            .stack(monthlyMoveGroup, function (d) {
                                return d.value;
                            })
                            .title(function (d) {
                                var value = d.value.avg ? d.value.avg : d.value;
                                if (isNaN(value)) value = 0;
                                return dateFormat(d.key) + "\n" + numberFormat(value);
                            })
                    ])
                    .xAxis();

            var volumeChart = dc.barChart(".graphit-container-2");
            volumeChart
                .width(800)
                .height(100)
                .margins({top: 0, right: 50, bottom: 20, left: 40})
                .dimension(data.dimensions[0].accessor)
                .group(volumeByMonthGroup)
                .centerBar(true)
                .gap(0)
                .x(d3.time.scale().domain([new Date(1950,01,01), new Date(2014,12,31)]))
                .round(d3.time.month.round)
                .xUnits(d3.time.months)
                .renderlet(function (chart) {
                    chart.select("g.y").style("display", "none");
                    moveChart.filter(chart.filter());
                })
                .on("filtered", function (chart) {
                    dc.events.trigger(function () {
                        moveChart.focus(chart.filter());
                    });
                });

            dc.renderAll();
        });

        return;


        // d3.csv('/static/tests/morley.csv', function(error, experiments) {
        d3.csv('/api/corpus/13410/data?mesured=ngrams.count&parameters[]=metadata.publication_year&filters[]=ngram.terms|bee,bees&format=csv', function(error, data) {

            // DATA PARSING

            data.forEach(function(x) {
                x.publication_year = +x.publication_year;
                x.count = +x.count;
            });

            var ndx                 = crossfilter(data),
                x = ndx.dimension(function(d) {return +d['metadata.publication_year'];}),
                y = [
                    x.group().reduceSum(function(d) {return +d['ngrams.count'];}),
                    x.group().reduceSum(function(d) {return +d['ngrams.count'] * 2;})
                ]

            // WHAT'S UNDER THE GRAPH?
            
            // dcVolumeChart = dc.barChart('.graphit-container-2');

            // THAT'S THE GRAPH!

            dcChart = dc.lineChart('.graphit-container');
            // dcChart = dc.barChart('.graphit-container');


            dcChart
                .width(_width)
                .height(_height)
                .x(d3.scale.linear())
                .elasticX(true)
                .elasticY(true)
                .renderArea(true)

                // .brushOn(false)
                // .rangeChart(dcVolumeChart)

                .legend(dc.legend().x(.75 * _width).y(.125 * _height).itemHeight(13).gap(5))
                // .title(function (d) {
                //     var value = d.value.avg ? d.value.avg : d.value;
                //     if (isNaN(value)) value = 0;
                //     return d.key + "\n" + value;
                // })

                .renderVerticalGridLines(true)
                .renderHorizontalGridLines(true)

                // .mouseZoomable(true)


                .dimension(x)
                .group(y[0], 'Test 1')
                .stack(y[1], 'Test 2')

                // .renderlet(function(chart) {
                //     dcChart.selectAll('rect').on("click", function(d) {
                //         alert('Boo!');
                //     });
                // });

            // SERIOUSLY, WHAT'S UNDER THE GRAPH?
            
            // dcVolumeChart
            //     .width(width)
            //     .height(.25 * height)
            //     .dimension(x)
            //     .group(y[0])
            //     .stack(y[1])
            //     .centerBar(true)
            //     // .gap(1)
            //     .x(d3.scale.linear())
            //     // .x(d3.time.scale());
            
            dcChart.render();
        });

        return container;
    };

})(jQuery);



var graph = $('.graph-it').graphIt(640, 480);