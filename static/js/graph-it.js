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
            container.width(width).height(height);
            return container;
        };
        container.plot = function(_method) {
            method = _method;
            container.empty();
        };

        container.css('background', '#FFF').text("graphIt");
        container.resize(_width, _height);
        var dcChart = dc.barChart(container.get(0));
        return container;
    };

})(jQuery);



var graph = $('.graph-it').graphIt();