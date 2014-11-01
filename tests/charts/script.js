// Dummy response
var response = {
    xAxis: "Publication year",
    xMin: +Number.MAX_VALUE,
    xMax: -Number.MAX_VALUE,
    yAxis: "Tf",
    yMin: +Number.MAX_VALUE,
    yMax: -Number.MAX_VALUE,
    data: {
        length: 0,
        x: [],
        y: [
            [],
            []
        ]
    }
};
// Dummy data for dummy response
for (var year=1964; year<2014; year++) {
    response.data.length++;
    response.data.x.push(year);
    response.data.y[0].push(.05 + .10 * Math.random());
    response.data.y[1].push(.05 + .10 * Math.random());
}
// Dummy extrema
for (var i=0; i<response.data.length; i++) {
    var x = response.data.x[i];
    if (response.xMin > x) {
        response.xMin = x;
    }
    if (response.xMax < x) {
        response.xMax = x;
    }
    for (var j=0; j<response.data.y.length; j++) {
        var y = response.data.y[j][i];
        if (response.yMin > y) {
            response.yMin = y;
        }
        if (response.yMax < y) {
            response.yMax = y;
        }
    }
}


// Initialize gRaphael
var holder = $('<div>').width(820).height(410).addClass('chartholder').appendTo('body');
var paper = Raphael(holder.get(0));

// Inititalize data for the chart
// graphsHolder.linechart(10, 10, 300, 220, response.data.x, [response.data.y]);
var chart = paper.linechart(
    0, 0, 800, 400,
    response.data.x, response.data.y,
    {   axis : '0 0 1 1'
    }
);

chart.hoverColumn(function() {
    console.log(this);
    this.tags = paper.set();
    for (var i=0, ii = this.y.length; i<ii; i++) {
        this.tags.push(
            paper.tag(this.x, this.y[i], this.values[i], 160, 10)
                .insertBefore(this)
                .attr([
                    { fill: chart.lines[i].attrs.stroke },
                    { fill: '#FFF', fontWeight: 'bold' }
                ])
        );
    }
    this.tags.attr('opacity', .75);
}, function() {
    this.tags && this.tags.remove();
});