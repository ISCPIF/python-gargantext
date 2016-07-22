/**
 * Created by tuanchauict on 3/24/14.
 */

(function($){
    /**
     * options.range = true or false, [default: false]
     * options.onchange = callback function when slider caret changed, onchange(low, high) for ranged, and onchange(value) for unranged
     * options.min = minimum of value [default: 0]
     * options.max = maximum of value [default: 100]
     * options.step [default: 1]
     * options.unit = the unit which be shown, [default: none]
     * options.enabled = true / false. [default: true]
     * options.value = number if count = 1 , or 2 elements array contains low and high value if count = 2
     * options.text = true or false, [default: true]
     * @param options
     * @returns {$.fn}
     */
    $.fn.freshslider = function(options){
        var me = this;
        var range = typeof options.range == 'undefined'? false : options.range,
            isSingle = !range,
            bgcolor = options.bgcolor,//"#27c470",
            min = options.min || 0,
            max = options.max || 100,
            gap = max - min,
            step = options.step || 1,
            unit = options.unit || '',
            enabled = typeof options.enabled == 'undefined'? true: options.enabled,
            values = [0, 1],
            text = typeof options.text == 'undefined' ? true:options.text,
            view = null;

        if(gap < 0){
            throw new Error();
        }

        var isFunction = function(object){
            return object && Object.prototype.toString.call(object) == '[object Function]';
        };

        var updateCallback = null;

        if(isFunction(options.onchange) == true){
            updateCallback = options.onchange;
        }

        var strStep = '' + step;
        var countPoint = 0;
        if(strStep.indexOf('.') >= 0){
            countPoint = strStep.length - strStep.indexOf('.') - 1;
        }

        if(options.hasOwnProperty('value')){
            if(!isSingle){
                if(options.value.length && options.value.length == 2){
                    values[0] = (options.value[0] - min) / gap;
                    values[1] = (options.value[1] - min) / gap;
                }
            }
            else{
                values[1] = (options.value - min) / gap;
            }
        }
        else{
            if(isSingle){
                values[1] = 0.5;
            }
        }



        if(range){
            view = this.html("<div class='fsslider'><div class='fsfull-value'></div>" +
                "<div class='fssel-value'></div><div class='fscaret fss-left'></div>" +
                "<div class='fscaret fss-right'></div></div>").find('.fsslider');
        }
        else{
            view = this.html("<div class='fsslider'><div class='fsfull-value'></div>" +
                "<div class='fssel-value'></div><div class='fscaret'></div></div>")
                .find('.fsslider');
        }

        var caretLeft = $(this.find('.fscaret')[0]);
        var caretRight = isSingle? caretLeft:$(this.find('.fscaret')[1]);
        var selVal = this.find('.fssel-value');

        var round = function(val){
            return step * Math.round(val/step);
        };

        var num2Text = function(number){
            return number.toFixed(countPoint);
        };

        var updateCarets = function(){
            if(text){
                caretRight.text((round(values[1] * gap) + min).toFixed(countPoint) + unit);
                if(!isSingle){
                    caretLeft.text((round(values[0] * gap) + min).toFixed(countPoint) + unit);
                }
            }

            var sliderWidth = me.width(),
                caretLeftWidth = caretLeft.outerWidth(),
                caretRightWidth = caretRight.outerWidth(),
                realWidth = sliderWidth - (caretLeftWidth + caretRightWidth) / 2;

            selVal.css({
                left:values[0] * sliderWidth,
                width:(values[1] - values[0]) * sliderWidth,
                background:bgcolor
            });

            caretLeft.css({
                left:values[0] * realWidth + caretLeftWidth/2,
                "margin-left": -(caretLeftWidth/2),
                'z-index':isRight?0:1
            });

            caretRight.css({
                left:values[1] * realWidth + caretRightWidth / 2,
                "margin-left": -(caretRightWidth/2),
                'z-index':isRight?1:0
            });

            if(updateCallback){
                if(isSingle){
                    updateCallback(round(values[1] * gap) + min);
                }
                else{
                    updateCallback(round(values[0] * gap) + min, round(values[1] * gap ) + min);
                }
            }

        };

        var isRight = true;
        var isDown = false;

        this.mousedown(function(e){
            if(!enabled){
                return;
            }

            isDown =true;
            var sliderWidth = me.width(),
                caretLeftWidth = caretLeft.outerWidth(),
                caretRightWidth = caretRight.outerWidth(),
                realWidth = sliderWidth - (caretLeftWidth + caretRightWidth) / 2;

            var target = e.target;
            var cls = target.className;

            var x = e.pageX - me.offset().left;

            var realX = x - caretLeftWidth/2;
            realX = realX < 0? 0:realX > realWidth ? realWidth:realX;

            if(isSingle){
                values[1] = realX / realWidth;
                isRight = true;
            }
            else{
                switch (cls){
                    case 'fscaret fss-left':
                        isRight = false;
                        values[0] = realX/realWidth;
                        break;
                    case 'fscaret fss-right':
                        isRight = true;
                        values[1] = realX/realWidth;
                        break;
                    default:
                        if(realX < (values[0] + values[1])/2 * realWidth){
                            isRight = false;
                            values[0] = realX / realWidth;
                        }
                        else{
                            isRight = true;
                            values[1] = realX / realWidth;
                        }

                }
            }

            updateCarets();
            if(event.preventDefault){
                    event.preventDefault();
            }
            else{
                return false;
            }
        });

        var onMouseUp = function(){
            if(!enabled){
                return;
            }
            isDown = false;
            values[1] = round(values[1] * gap) / gap;
            if(!isSingle){
                values[0] = round(values[0] * gap) / gap;
            }

            updateCarets();
        };

        $(document).mouseup(function(e){
            if(isDown)
                onMouseUp();
        });

        this.mousemove(function(e){
            if(!enabled){
                return;
            }
            if(isDown){
                var sliderWidth = me.width(),
                    caretLeftWidth = caretLeft.outerWidth(),
                    caretRightWidth = caretRight.outerWidth(),
                    realWidth = sliderWidth - (caretLeftWidth + caretRightWidth) / 2;

                var target = e.target;
                var cls = target.className;
                var x = e.pageX - me.offset().left;

                var realX = x - caretLeftWidth/2;
                realX = realX < 0? 0:realX > realWidth ? realWidth:realX;
                if(isSingle){
                    values[1] = realX / realWidth;
                    isRight = true;
                }
                else{
                    if(isRight){
                        values[1] = realX / realWidth;
                        if(values[1] < values[0]){
                            values[1] = values[0];
                        }
                    }
                    else{
                        values[0] = realX / realWidth;
                        if(values[0] > values[1]){
                            values[0] = values[1];
                        }
                    }
                }
                updateCarets();
            }
            if(event.preventDefault){
                event.preventDefault();
            }
            else{
                return false;
            }
        });





        this.getValue = function(){
            if(isSingle){
                return [values[1] * gap + min];
            }
            else{
                return [values[0] * gap + min, values[1] * gap + min];
            }
        };

        this.setValue = function(){

            if(!isSingle){
                if(arguments.length >= 2){
                    values[0] = (options.value[0] - min) / gap;
                    values[1] = (options.value[1] - min) / gap;

                    updateCarets();
                }
            }
            else{
                values[1] = (arguments[0] - min) / gap;
                updateCarets();
            }
        };

        this.setEnabled = function(_enable){
            enabled = typeof _enable == 'undefined' ? true:_enable;
            if(enabled){
                view.removeClass('fsdisabled');
            }
            else{
                view.addClass('fsdisabled');
            }
        };

        this.setEnabled(enabled);
        updateCarets();

        return this;
    }
}(jQuery));