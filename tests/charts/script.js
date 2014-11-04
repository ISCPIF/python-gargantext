/** 
 *
 *  (cf. http://bl.ocks.org/mbostock/1256572)
 *
 *  TODO:
 *
 *  +   change .plot().plot() into .feed([])
 *
 *  +   implement .view()
 *
 *  +   add legend, based on data.name
 *
 *  -   automatically identify if numeric/discrete,
 *  +   automatically generate a list of all the possible values
 *  +   automatically generate axis & grid
 *
 *  +   when 'data' is called, check if strings are encountered
 *      as the first member of points (or second?)
 *
 *  +   check if points have 2 or 3 members (number of dimension)
 *
 *  -   implement viewing modes for 2D data:
 *      -   sectors (only average)
 *      -   donuts
 *      +   histograms (with average & std)
 *      -   box plots
 *
 *      -   points
 *      +   lines
 *      -   curves
 *      -   areas
 *      -   stacked areas
 *
 *      -   bars
 *      -   stacked bars
 *
 *  -   implement viewing modes for 3D data:
 *      -   heatmaps
 *
 *  -   order axis by specific criteria
 *
**/


var dataList = [];
for (var i=0; i<4; i++) {
    var data = [];
    var y = 3 + 1.5 * Math.random();
    var dy = 0;
    for (var x=1964; x<2014; x++) {
        y += .1 * (Math.random() - .5);
        // dy += .01 * (Math.random() - .5);
        // y += dy;
        if (y < 0) {
            y = 0;
        }
        data.push([x, y]);
    }
    dataList.push(data);
}

var container = $('.graph');
var graph = new Graph(container[0], container.width(), container.height())
    .fill('#FFF')
    .feed([
        {name:'bees', data: dataList[0], options: {color:'#FC0', size:4}},
        {name:'honey', data: dataList[1], options: {color:'#CF0', size:4}}
    ])
    // .view('lines', ['Year of publication', 'Term frequency'])
    // .view('histograms', ['Term', 'Term frequency'])
    // .view('sectors', ['Terms occurences'])


$('select[name=view]').change(function(){
    var value = $(this).val();
    var options = {
        'histogram': ['Year of publication', 'Term frequency'],
        'line': ['Year of publication', 'Term frequency'],
    };
    graph.view(value, options[value])
}).change();

$(window).resize(function(){
    var width = container.width();
    var height = container.height();
    graph.size(width, height);
});
