var c = function(){
    console.log.apply(console, arguments);
};


var Graph = function(container, width, height) {
    
    var context = null;
    var contextType = 'none';
    var data;
    
    var __this__ = this;
    var __defaultoptions__ = {color:'#000', size:1, background:'rgba(0,0,0,0.5)', align:'center'};
    var __options__ = {};
    var __methods__ = {canvas:{}, raphael:{}};
    
    var cache = [];
    
    __methods__.canvas.size = function(width, height) {
        context.canvas.width = width;
        context.canvas.height = height;
        __options__.width = width;
        __options__.height = height;
    };
    __methods__.canvas.get = function() {
        return __options__;
    }
    __methods__.canvas.set = function(options) {
        options.color && (context.strokeStyle = options.color);
        options.color && (context.fillStyle = options.color);
        // options.size && 
    };
    __methods__.canvas.reset = function() {
    };
    __methods__.canvas.line = function(x1, y1, x2, y2, options) {
        options || (options = {});
        context.lineCap = 'round';
        context.lineWidth = getSize(options.size || __options__.size);
        context.strokeStyle = options.color || __options__.color;
        context.beginPath();
        context.moveTo(getX(x1), getY(y1));
        context.lineTo(getX(x2), getY(y2));
        context.stroke();
        return __this__;
    };
    __methods__.canvas.text = function(x, y, text, options) {
        options = options || {};
        var size = 20 * (options.size || __options__.size);
        if (scales && scales.size) {
            size *= scales.size;
        }
        size = Math.round(10 * size) / 10;
        context.font = size + 'px sans-serif';
        context.fillStyle = options.color || __options__.color;
        context.textAlign = options.align || __options__.align;
        context.textAlign = options.align || __options__.align;
        context.textBaseline = 'middle';
        context.fillText(text, getX(x), getY(y));
        return __this__;
    };
    __methods__.canvas.fill = function(background) {
        context.fillStyle = background || __options__.background;
        context.fillStyle = 'white';
        context.fillRect(0, 0, __options__.width, __options__.height);
    };
    __methods__.canvas.clear = function() {
        var emptyImage = context.createImageData(context.canvas.width, context.canvas.height);
        context.putImageData(emptyImage, 0, 0);
    };
    
    
    this.size = function(width, height) {
        container.style.width = width + 'px';
        container.style.height = height + 'px';
        __this__._size(width, height);
        __this__.draw();
        return __this__;
    };
    this.draw = function() {
        // clear the canvas
        __this__._clear();
        // redraw what is in the cache
        for (var i=0; i<cache.length; i++) {
            var item = cache[i];
            __this__['_' + item.method].apply(__this__, item.arguments);
        }
        return __this__;
    };
    this.clear = function(keepCaches) {
        if (!keepCaches) {
            cache = [];
        }
        __this__._clear();
    };
    
    var scales = [];
    var getX = function(x) {
        var scale = scales[0];
        switch (scale.type) {
            case 'numeric':
                return (x - scale.min) * __options__.width / scale.span;
            case 'discrete':
                return scale.values[x];
            default:
                return x;
        }
    };
    var getY = function(y) {
        var scale = scales[1];
        switch (scale.type) {
            case 'numeric':
                return (scale.max - y) * __options__.height / scale.span;
            case 'discrete':
                return scale.values[y];
            default:
                return y;
        }
    };
    var getSize = function(size) {
        return size * scales.size;
    };
    /*this.scale = function(left, top, right, bottom) {
        if (left === undefined) {
            // for clearing purpose
            scale = null;
        } else {
            // store new scaling
            scale = {
                left:   left,
                right:  right,
                width:  (right-left),
                top:    top,
                bottom: bottom,
                height: (bottom-top),
                size: Math.sqrt(width * height)
            };
        }
        // repaint everything
        __this__.draw();
        return __this__;
    };*/
    
    this.set = function(options) {
        cache.push({
            method: 'set',
            arguments: [options]
        });
        for (var key in options) {
            __options__[key] = options[key];
        }
        __this__._set(options);
        return __this__;
    };
    this.line = function(x1, y1, x2, y2, options) {
        cache.push({
            method: 'line',
            arguments: [x1, y1, x2, y2, options]
        });
        __this__._line(
            x1,
            y1,
            x2,
            y2,
            options
        );
        return __this__;
    };
    this.text = function(x, y, text, options) {
        cache.push({
            method: 'text',
            arguments: [x, y, text, options]
        });
        __this__._text(x, y, text, options);
        return __this__;
    };
    this.fill = function(background) {
        __this__.clear();
        cache.push({
            method: 'fill',
            arguments: [background]
        });
        __this__._fill(background);
        return __this__;
    };
    this.clear = function() {
        cache = [];
        plottingData = {
            extrema: {
                xMin:  +Number.MAX_VALUE,
                xMax:  -Number.MAX_VALUE,
                yMin:  +Number.MAX_VALUE,
                yMax:  -Number.MAX_VALUE,
            },
            datasets: []
        };
        __this__._clear();
        return __this__;
    };
    
    var __datasets__ = {};
    this.feed = function(datasets) {
        // get the dimensions & types
        __datasets__.dimensions = datasets[0].data[0].length;
        __datasets__.types = [];
        for (var k=0; k<__datasets__.dimensions; k++) {
            __datasets__.types.push(typeof(datasets[0].data[0][k]));
        }
        // extract values
        __datasets__.values = [];
        for (var k=0; k<__datasets__.dimensions; k++) {
            values = [];
            for (var i=0; i<datasets.length; i++) {
                var data = datasets[i].data;
                for (var j=0; j<data.length; j++) {
                    var value = data[j][k];
                    if (values.indexOf(value) == -1) {
                        values.push(value);
                    }
                }
            }
            __datasets__.values.push(values);
        }
        // sort values        
        for (var i=0; i<__datasets__.values.length; i++) {
            __datasets__.values[i].sort();
        }
        //
        __datasets__.list = datasets;
        return __this__;
    };
    this.axisX = function(label, grads) {
        var extrema = plottingData.extrema;
        var valuesX = __datasets__.values[0];
        var valuesY = __datasets__.values[1];
        // main components
        __this__.line(
            scales[0].min,
            valuesY[0],
            scales[0].max,
            valuesY[0],
            {size:1, color:'#000'}
        );
        __this__.text(
            scales[0].max - .0125*scales[0].span,
            valuesY[0] + .025*scales[1].span,
            label,
            {align:'right', size:1, color:'#000'}
        );
        // graduations
        for (var i=0; i<grads.length; i++) {
            var opacity = Math.pow(.5, i+1);
            var grad = grads[i];
            // extrema
            var min = valuesX[0];
            min -= min % grad;
            if (min < valuesX[0]) {
                min += grad;
            }
            var max = valuesX[valuesX.length - 1];
            max -= max % grad;
            while (max < valuesX[valuesX.length - 1]) {
                max += grad;
            }
            // draw
            for (var x=min; x<max; x+=grad) {
                __this__.line(
                    x,
                    valuesY[0] - .0125*scales[1].span,
                    x,
                    valuesY[0] + .0125*scales[1].span,
                    {size:1, color:'rgba(0,0,0,' + (2*opacity) + ')'}
                );
                __this__.line(
                    x,
                    valuesY[valuesY.length - 1],
                    x,
                    valuesY[0],
                    {size:1, color:'rgba(0,0,0,' + opacity + ')'}
                );
                if (i == 0) {
                    __this__.text(
                        x,
                        valuesY[0] - .05*scales[1].span,
                        x,
                        {align:'center', size:1, color:'#000'}
                    );
                }
            }
        }
    };
    this.axisY = function(label, grads) {
        var extrema = plottingData.extrema;
        var valuesX = __datasets__.values[0];
        var valuesY = __datasets__.values[1];
        // main components
        __this__.line(
            valuesX[0],
            scales[1].min,
            valuesX[0],
            scales[1].max,
            {size:1, color:'#000'}
        );
        __this__.text(
            valuesX[0] + .0125*scales[0].span,
            scales[1].max - .04*scales[1].span,
            label,
            {align:'left', size:1, color:'#000'}
        );
        // graduations
        for (var i=0; i<grads.length; i++) {
            var opacity = Math.pow(.5, i+1);
            var grad = grads[i];
            // extrema
            var min = valuesY[0];
            min -= min % grad;
            if (min < valuesY[0]) {
                min += grad;
            }
            var max = valuesY[valuesY.length - 1];
            max -= max % grad;
            while (max < valuesY[valuesY.length - 1]) {
                max += grad;
            }
            // draw
            for (var y=min; y<max; y+=grad) {
                __this__.line(
                    valuesX[0] - .0125*scales[0].span,
                    y,
                    valuesX[0] + .0125*scales[0].span,
                    y,
                    {size:1, color:'rgba(0,0,0,' + (2*opacity) + ')'}
                );
                __this__.line(
                    valuesX[0],
                    y,
                    valuesX[valuesX.length - 1],
                    y,
                    {size:1, color:'rgba(0,0,0,' + opacity + ')'}
                );
                if (i == 0) {
                    __this__.text(
                        valuesX[0] - .025*scales[0].span,
                        y,
                        y,
                        {align:'left', size:1, color:'#000'}
                    );
                }
            }
        }
    };
    
    this.viewLine = function(labels, options) {
        __this__.clear();
        // compute the scales
        scales = [];
        for (var i=0; i<__datasets__.dimensions; i++) {
            var values = __datasets__.values[i];
            if (__datasets__.types[i] == 'number') {
                var min = values[0];
                var max = values[values.length - 1];
                var span = max - min;
                scales.push({
                    type:   'numeric',
                    min:    min - .1 * span,
                    max:    max + .1 * span,
                    span:   1.2 * span
                });
            } else {
                var positions = {};
                for (var j=0; j<values.length; j++) {
                    positions[values[j]] = 0;
                }
                scales.push({
                    type:       'discrete',
                    positions:  positions
                });
            }
        }
        scales.size = Math.sqrt(__options__.width * __options__.height) / 800;
        // draw the things!
        for (var i=0; i<__datasets__.list.length; i++) {
            var dataset = __datasets__.list[i];
            var options = dataset.options;
            var previousPoint = dataset.data[0];
            for (var j=1; j<dataset.data.length; j++) {
                var point = dataset.data[j];
                __this__.line(
                    previousPoint[0],
                    previousPoint[1],
                    point[0],
                    point[1],
                    options
                );
                previousPoint = point;
            }
        }
        // Y axis
        var values = __datasets__.values[1];
        var grad = Math.log(values[values.length-1] - values[0]);
        grad /= Math.log(10);
        grad = Math.floor(grad);
        grad = Math.pow(10, grad);
        __this__.axisY(labels[1], [grad, .1*grad]);
        // X axis
        var values = __datasets__.values[0];
        var grad = values[values.length-1] - values[0];
        grad = Math.log(grad) / Math.log(10);
        grad = Math.floor(grad);
        grad = Math.pow(10, grad);
        __this__.axisX(labels[0], [grad, .1*grad]);
        
    };
    this.view = function(name, labels, options) {
        name = name
            .toLowerCase()
            .replace(/s+$/, '')
            .replace(/^\w/, function(match){return match.toUpperCase()});
        __this__['view' + name](labels);
        return __this__;
    };
    
    (function() {
        var canvas = document.createElement('canvas');
        var canvasContext = canvas.getContext && canvas.getContext('2d');
        if (!!canvasContext) {
            container.appendChild(canvas);
            contextType = 'canvas'; 
            context = canvasContext;
        } else {
            contextType = 'raphael'; 
            context = Raphael(container, width, height);
        }
        for (var key in __methods__[contextType]) {
            __this__['_' + key] = __methods__[contextType][key];
        }
        __this__.size(width, height);
        __this__.clear();
    })();
};


var dataList = [];
for (var i=0; i<4; i++) {
    var data = [];
    var y = Math.random();
    for (var x=1964; x<2014; x++) {
        y += 1 * (Math.random() - .5);
        if (y < 0) {
            y = 0;
        }
        data.push([x, y]);
    }
    dataList.push(data);
}

var graph = (new Graph(document.getElementById('graph'), 800, 400))
    .fill('#FFF')
    .feed([
        {name:'bees', data: dataList[0], options: {color:'#FC0', size:4}},
        {name:'honey', data: dataList[1], options: {color:'#CF0', size:4}}
    ])
    .view('lines', ['Year of publication', 'Term frequency'])
    
    // .feed([
        // {name:'bees', data: [[2010,0.123], [2011,0.214], [2012,0.157]], options: {color:'#FC0', size:5}},
        // {name:'honey', data: [[2010,0.123], [2011,0.214], [2012,0.157]], options: {color:'#CF0', size:5}}
    // ])
    // .view('histograms', ['Year of publication', 'Term frequency'])
    
    // .feed([
        // {name:'bees', data: [[312]], options: {color:'#FC0', size:5}},
        // {name:'honey', data: [[564]], options: {color:'#CF0', size:5}}
    // ])
    // .view('sectors', ['Terms occurences'])
    
    // .grid(1, .2, {color:'rgba(0,0,0,.25)', size:1})
    // .grid(5, 1, {color:'rgba(0,0,0,.25)', size:1})
    // .axisX('Year of publication', 5, {color:'black', size:1})
    // .axisY('Term frequency', 1, {color:'black', size:1})
    // .view('histogram', [])
    
/**
 *
 *  TODO:
 *
 *  -   change .plot().plot() into .feed([])
 *
 *  -   implement .view()
 *
 *  -   add legend, based on data.name
 *
 *  -   automatically identify if numeric/discrete,
 *      automatically generate a list of all the possible keys
 *      automatically generate axis & grid
 *
 *  -   when 'data' is called, check if strings are encountered
 *      as the first member of points (or second?)
 *
 *  -   check if points have 2 or 3 members
 *
 *  -   implement viewing modes for 2D data:
 *      -   sectors (only average)
 *      -   histograms (with average & std)
 *
 *      -   points
 *      -   lines
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
 *  -   data can be:
 *      -   something rather histogrammy: [['bee', 1]], []
 *
**/