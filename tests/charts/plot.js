// for debugging purpose only
var c = function(){
    console.log.apply(console, arguments);
};

// the main class!
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
        context.lineWidth = getSize(options.size || 1);
        context.strokeStyle = options.color || __options__.color;
        context.beginPath();
        context.moveTo(getX(x1), getY(y1));
        context.lineTo(getX(x2), getY(y2));
        context.stroke();
    };
    __methods__.canvas.rect = function(x1, y1, x2, y2, options) {
        options || (options = {});
        context.lineCap = 'round';
        context.lineWidth = getSize(options.size || __options__.size);
        context.fillStyle = options.color || __options__.color;
        context.fillRect(
            getX(x1),
            getY(y1),
            getX(x2)-getX(x1),
            getY(y2)-getY(y1)
        );
        return __this__;
    };
    __methods__.canvas.text = function(x, y, text, options) {
        options = options || {};
        var size = 16 * (options.size || __options__.size);
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
        __options__.width = width;
        __options__.height = height;
        __options__.size = Math.sqrt(__options__.width * __options__.height) / 800;
        // container.style.width = width + 'px';
        // container.style.height = height + 'px';
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
        return size * __options__.size;
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
    this.rect = function(x1, y1, x2, y2, options) {
        cache.push({
            method: 'rect',
            arguments: [x1, y1, x2, y2, options]
        });
        __this__._rect(x1, y1, x2, y2, options);
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
            __datasets__.values[i] = __datasets__.values[i].sort(function(a, b) {
                if (a < b)
                    return -1;
                if (a > b)
                    return 1;
                return 0;
            });
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
    this.axisY = function(label, grads, extrema) {
        extrema = extrema || {};
        var valuesX = __datasets__.values[0];
        var valuesY = __datasets__.values[1];
        var Xmin = (extrema.Xmin != undefined) ? extrema.Xmin : valuesX[0];
        var Xmax = (extrema.Xmax != undefined) ? extrema.Xmax : valuesX[valuesX.length - 1];
        var Ymin = (extrema.Ymin != undefined) ? extrema.Ymin : valuesY[0];
        var Ymax = (extrema.Ymax != undefined) ? extrema.Ymax : valuesY[valuesY.length - 1];
        // main components
        __this__.line(
            Xmin,
            scales[1].min,
            Xmin,
            scales[1].max,
            {size:1, color:'#000'}
        );
        __this__.text(
            Xmin + .0125*scales[0].span,
            scales[1].max - .04*scales[1].span,
            label,
            {align:'left', size:1, color:'#000'}
        );
        // graduations
        for (var i=0; i<grads.length; i++) {
            var opacity = Math.pow(.3, i+1);
            var grad = grads[i];
            // extrema
            var min = Ymin;
            min -= min % grad;
            if (min < valuesY[0]) {
                min += grad;
            }
            var max = Ymax + grads[grads.length - 1];
            // draw
            for (var y=min; y<max; y+=grad) {
                __this__.line(
                    Xmin - .0125*scales[0].span,
                    y,
                    Xmin + .0125*scales[0].span,
                    y,
                    {size:1, color:'rgba(0,0,0,' + (2*opacity) + ')'}
                );
                __this__.line(
                    Xmin,
                    y,
                    Xmax,
                    y,
                    {size:1, color:'rgba(0,0,0,' + opacity + ')'}
                );
                if (i == 0) {
                    var m = Math.max(Ymax/grad, -Ymin/grad);
                    var precision = Math.log(m) / Math.log(10);
                    precision = Math.ceil(precision)
                    __this__.text(
                        Xmin - .02*scales[0].span,
                        y,
                        y.toPrecision(precision),
                        {align:'right', size:1, color:'#000'}
                    );
                }
            }
        }
    };
    
    this.viewHistogram = function(labels, options) {// draw the things!
        // compute average & std
        var statistics = [];
        var min = 0;
        var max = 0;
        for (var i=0; i<__datasets__.list.length; i++) {
            var dataset = __datasets__.list[i];
            var options = dataset.options;
            var previousPoint = dataset.data[0];
            // compute average
            var average = 0;
            var k = __datasets__.dimensions - 1;
            for (var j=0; j<dataset.data.length; j++) {
                average += dataset.data[j][k];
            }
            average /= dataset.data.length;
            // compute standard deviation
            var k = __datasets__.dimensions - 1;
            var std = 0;
            for (var j=0; j<dataset.data.length; j++) {
                var value = average - dataset.data[j][k];
                std += value * value;
            }
            std = Math.sqrt(std);
            // store it for later
            statistics.push({
                average: average,
                std: std
            });
            var d1 = average - std;
            var d2 = average + std;
            if (average < 0) {
                min = Math.min(d1, min);
            } else {
                max = Math.max(d2, max);
            }
        }
        // compute the scales
        var span = max - min;
        scales = [{
            type:   'numeric',
            min:    -.5,
            max:    __datasets__.list.length + 1,
            span:   __datasets__.list.length + 1.5
        }, {
            type:   'numeric',
            min:    min - .1*span,
            max:    max + .1*span,
            span:   1.2 * span
        }];
        // graphs
        for (var i=0; i<__datasets__.list.length; i++) {
            var dataset = __datasets__.list[i];
            var average = statistics[i].average;
            var options = dataset.options;
            var std = statistics[i].std;
            __this__.rect(
                i + .7,
                0,
                i + 1.3,
                average,
                options
            );
            var y = (average>0) ? (average+std) : (average-std);
            __this__.line(
                i + 1,
                0,
                i + 1,
                y,
                options
            );
            __this__.line(
                i + .9,
                y,
                i + 1.1,
                y,
                options
            );
        }
        // X axis
        this.line(0, min, __datasets__.list.length + .5, min, {size:1, color:'rgba(0,0,0,.75)'});
        // Y axis
        var values = __datasets__.values[1];
        var grad = Math.log(max - min);
        grad /= Math.log(10);
        grad = Math.floor(grad);
        grad = Math.pow(10, grad);
        __this__.axisY(labels[1], [grad, .1*grad], {
            Xmin: 0,
            Xmax: __datasets__.list.length + .5,
            Ymin: min,
            Ymax: max,
        });
    };
    this.viewLine = function(labels, options) {
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
        // X axis
        var values = __datasets__.values[0];
        var grad = values[values.length-1] - values[0];
        grad = Math.log(grad) / Math.log(10);
        grad = Math.floor(grad);
        grad = Math.pow(10, grad);
        __this__.axisX(labels[0], [grad, .1*grad]);
        // Y axis
        var values = __datasets__.values[1];
        var grad = Math.log(values[values.length-1] - values[0]);
        grad /= Math.log(10);
        grad = Math.floor(grad);
        grad = Math.pow(10, grad);
        __this__.axisY(labels[1], [grad, .1*grad]);
            };
    this.view = function(name, labels, options) {
        name = name
            .toLowerCase()
            .replace(/s+$/, '')
            .replace(/^\w/, function(match){return match.toUpperCase()});
        __this__.clear();
        __this__['view' + name](labels);
        return __this__;
    };
    
    (function() {
        if (typeof(container) != 'object' || !container.style) {
            console.error('The first parameter of the Graph class constructor should be a valid DOM object.');
        }
        if (!width) {
            width = container.style.width;
        }
        if (!height) {
            height = container.style.height;
        }
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