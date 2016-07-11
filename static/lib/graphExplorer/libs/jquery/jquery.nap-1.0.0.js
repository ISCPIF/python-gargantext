/*	
 *	jQuery nap 1.0.0
 *	www.frebsite.nl
 *	Copyright (c) 2010 Fred Heusschen
 *	Licensed under the MIT license.
 *	http://www.opensource.org/licenses/mit-license.php
 */


(function($) {
	$.fn.nap = function(fallAsleep, wakeUp, standbyTime) {
		if (typeof(standbyTime) == 'number' && standbyTime > 0) {
			$.fn.nap.standbyTime = standbyTime;
			
			if ($.fn.nap.readySetGo) {
				$.fn.nap.pressSnooze();
			}
		}
		
		if (!$.fn.nap.readySetGo) {
			$.fn.nap.readySetGo = true;

			$(window).mousemove(function() {
				$.fn.nap.interaction();
			});
			$(window).keyup(function() {
				$.fn.nap.interaction();
			});
			$(window).mousedown(function() {
				$.fn.nap.interaction();
			});

			$(window).scroll(function() {
				$.fn.nap.interaction();
			});

			$.fn.nap.pressSnooze();
		}
		
		return this.each(function() {
			$.fn.nap.fallAsleepFunctions.push({
				func: fallAsleep, 
				napr: $(this)
			});
			$.fn.nap.wakeUpFunctions.push({
				func: wakeUp, 
				napr: $(this)
			});		
		});
	}


	$.fn.nap.standbyTime 	= 60;
	$.fn.nap.isAwake		= true;
	$.fn.nap.readySetGo		= false;

	$.fn.nap.fallAsleepFunctions 	= new Array();
	$.fn.nap.wakeUpFunctions 		= new Array();
	
	$.fn.nap.fallAsleep = function() {
		$.fn.nap.isAwake = false;
		clearInterval($.fn.nap.alarmClock);
		$.fn.nap.callFunctions($.fn.nap.fallAsleepFunctions);
	};
	$.fn.nap.wakeUp = function() {	
		$.fn.nap.isAwake = true;
		$.fn.nap.callFunctions($.fn.nap.wakeUpFunctions);
	};
	$.fn.nap.pressSnooze = function() {
		clearInterval($.fn.nap.alarmClock);
		$.fn.nap.alarmClock = setInterval(function() {
			$.fn.nap.fallAsleep();
		}, $.fn.nap.standbyTime * 1000);
	}
	$.fn.nap.interaction = function() {
		if (!$.fn.nap.isAwake) {
			$.fn.nap.wakeUp();
		}
		$.fn.nap.pressSnooze();
	}
	$.fn.nap.callFunctions = function(f) {
		for (var i in f) {
			if (typeof(f[i].func) == 'function') {
				f[i].func();

			} else if (typeof(f[i].func) == 'string' && f[i].func.length > 0) {
				f[i].napr.trigger(f[i].func);

			} else if (typeof(f[i].func) == 'object') {
				for (var z in f[i].func) {
					f[i].napr.trigger(f[i].func[z]);
				}
			}
		}
	}
	
})(jQuery);