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
        var size = (options.size || __options__.size) / 45;
        if (scale) {
            size *= scale.size;
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
    
    var scale = null;
    var getX = function(x) {
        if (scale) {
            return (x - scale.left) * __options__.width / scale.width;
        } else {
            return x;
        }
    };
    var getY = function(y) {
        if (scale) {
            return (y - scale.top) * __options__.height / scale.height;
        } else {
            return y;
        }
    };
    var getSize = function(size) {
        return size * scale.size / 1000;
    };
    this.scale = function(left, top, right, bottom) {
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
    };
    
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
        _options = {};
        for (var key in options) {
            _options[key] = options[key];
        }
        cache.push({
            method: 'text',
            arguments: [x, y, text, _options]
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
    
    var plottingData = null;
    var plotMethods = {
        'segments': function(point, previousPoint, options) {
            if (previousPoint) {
                __this__.line(
                    previousPoint[0],
                    previousPoint[1],
                    point[0],
                    point[1],
                    options
                );
            }
        }
    };
    this.plot = function(data, options) {
        // find extremas
        var extrema = plottingData.extrema;
        for (var i=0; i<data.length; i++) {
            var point = data[i];
            var x = point[0];
            var y = point[1];
            if (extrema.xMax < x) {
                extrema.xMax = x;
            }
            if (extrema.xMin > x) {
                extrema.xMin = x;
            }
            if (extrema.yMax < y) {
                extrema.yMax = y;
            }
            if (extrema.yMin > y) {
                extrema.yMin = y;
            }
        }
        // rescale
        extrema.xStep = .2 * (extrema.xMax - extrema.xMin);
        extrema.yStep = .2 * (extrema.yMax - extrema.yMin);
        __this__.scale(
            extrema.xMin - extrema.xStep,
            extrema.yMax + extrema.yStep,
            extrema.xMax + extrema.xStep,
            extrema.yMin - extrema.yStep
        );
        // add to existing datasets
        plottingData.datasets.push({
            data: data,
            options: options
        });
        // initialize options
        options || (options = {});
        options.method || (options.method = 'segments');
        options.color || (options.color = __options__.color)
        // show the points
        var datasets = plottingData.datasets;
        var plotMethod = plotMethods[options.method];
        for (var i=0; i<datasets.length; i++) {
            var dataset = datasets[i];
            var data = dataset.data;
            var options = dataset.options;
            var previousPoint = null;
            for (var j=0; j<data.length; j++) {
                var point = data[j];
                plotMethod(point, previousPoint, options);
                previousPoint = point;
            }
        }
        return __this__;
    };
    this.axisX = function(label, xGrad, options) {
        var extrema = plottingData.extrema;
        options.align = 'right';
        this.text(
            extrema.xMax + .85*extrema.xStep,
            extrema.yMin - .15*extrema.yStep,
            label,
            options
        );
        this.line(
            extrema.xMin - .5*extrema.xStep,
            extrema.yMin - extrema.yStep,
            extrema.xMin - .5*extrema.xStep,
            extrema.yMax + extrema.yStep,
            options
        );
        var xMin = extrema.xMin;
        xMin -= xMin % xGrad;
        if (xMin < extrema.xMin) {
            xMin += xGrad;
        }
        var xMax = extrema.xMax;
        xMax -= xMax % xGrad;
        while (xMax < extrema.xMax) {
            xMax += xGrad;
        }
        options.align = 'center';
        for (var x=xMin; x<=xMax; x+=xGrad) {
            __this__.line(
                x,
                extrema.yMin - .6*extrema.yStep,
                x,
                extrema.yMin - .4*extrema.yStep,
                options
            );
            __this__.text(
                x,
                extrema.yMin - .75*extrema.yStep,
                x,
                options
            );
        }
        return __this__;
    };
    this.axisY = function(label, yGrad, options) {
        var extrema = plottingData.extrema;
        options.align = 'left';
        this.text(
            extrema.xMin - .45*extrema.xStep,
            extrema.yMax + .85*extrema.yStep,
            label,
            options
        );
        __this__.line(
            extrema.xMin - extrema.xStep,
            extrema.yMin - .5*extrema.yStep,
            extrema.xMax + extrema.xStep,
            extrema.yMin - .5*extrema.yStep,
            options
        );
        var yMin = extrema.yMin;
        yMin -= yMin % yGrad;
        if (yMin < extrema.yMin) {
            yMin += yGrad;
        }
        var yMax = extrema.yMax;
        yMax -= yMax % yGrad;
        while (yMax < extrema.yMax) {
            yMax += yGrad;
        }
        options.align = 'right';
        for (var y=yMin; y<=yMax; y+=yGrad) {
            __this__.line(
                extrema.xMin - .4*extrema.xStep,
                y,
                extrema.xMin - .6*extrema.xStep,
                y,
                options
            );
            __this__.text(
                extrema.xMin - .6*extrema.xStep,
                y,
                yGrad * Math.round(y / yGrad),
                options
            );
        }
        return __this__;
    };
    this.grid = function(xGrad, yGrad, options) {
        var extrema = plottingData.extrema;
        //
        var xMin = extrema.xMin;
        xMin -= xMin % xGrad;
        if (xMin < extrema.xMin) {
            xMin += xGrad;
        }
        var xMax = extrema.xMax;
        xMax -= xMax % xGrad;
        while (xMax < extrema.xMax) {
            xMax += xGrad;
        }
        var yMin = extrema.yMin;
        yMin -= yMin % yGrad;
        if (yMin < extrema.yMin) {
            yMin += yGrad;
        }
        var yMax = extrema.yMax;
        yMax -= yMax % yGrad;
        while (yMax < extrema.yMax) {
            yMax += yGrad;
        }
        //
        for (var y=yMin; y<yMax; y+=yGrad) {
            __this__.line(
                extrema.yMin - extrema.xStep,
                y,
                scale.right,
                y,
                options
            );
        }
        for (var x=xMin; x<xMax; x+=xGrad) {
            __this__.line(
                x,
                scale.top,
                x,
                scale.bottom,
                options
            );
        }
        return __this__;
    };
    this.axis = function(xGrad, yGrad, options) {
        return __this__.axisX(xGrad, options).axisY(yGrad, options);
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
    .plot(dataList[0], {color:'#FC0', size:5})
    .plot(dataList[1], {color:'#CF0', size:5})
    .grid(1, .2, {color:'rgba(0,0,0,.25)', size:1})
    .grid(5, 1, {color:'rgba(0,0,0,.25)', size:1})
    .axisX('Year of publication', 5, {color:'black', size:1})
    .axisY('Term frequency', 1, {color:'black', size:1})
    .draw()
    
