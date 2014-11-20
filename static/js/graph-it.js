(function($) {


    $.fn.graphIt = function(_width, _height) {
        
        var container = this.first();
        var data;
        var method;
        var dcChart;


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
        dcChart = dc.barChart(container.get(0));
            .centerBar(true)
            .dimension(function(d){return d[0]})
            // .gap(1)
            // .round(dc.round.floor)
            // .alwaysUseRounding(true)
            // .x(d3.scale.linear().domain([-25, 25]))
            // .renderHorizontalGridLines(true)
            // .filterPrinter(function (filters) {
            //     var filter = filters[0], s = "";
            //     s += numberFormat(filter[0]) + "% -> " + numberFormat(filter[1]) + "%";
            //     return s;
            // });
        container.resize(_width, _height);
        return container;
    };

})(jQuery);



var graph = $('.graph-it').graphIt();