(function () {
  'use strict';

  var annotationsAppUtils = angular.module('annotationsAppUtils', []);

  /*
  * Filter used in lists pagination (extra-text panel)
  */
  annotationsAppUtils.filter('startFrom', function () {
    return function (input, start) {
      if (input === undefined) return;
      start = +start; //parse to int
      return input.slice(start);
    };
  });

})(window);
