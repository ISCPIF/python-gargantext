(function () {
  'use strict';

  /*
  * Django STATIC_URL given to angular to load async resources
  */
  var S = window.STATIC_URL;

  window.annotationsApp = angular.module('annotationsApp', ['annotationsAppHttp',
      'annotationsAppNgramList', 'annotationsAppHighlight', 'annotationsAppDocument',
      'annotationsAppActiveLists', 'annotationsAppUtils']);

  /*
  * Angular Templates must not conflict with Django's
  */
  window.annotationsApp.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
    $interpolateProvider.endSymbol('}]}');
  });

  /*
  * Main function
  * GET the document node and all its ngrams
  */
  window.annotationsApp.run(function ($rootScope) {
    var path = window.location.pathname.match(/\/project\/(.*)\/corpus\/(.*)\/document\/(.*)\//);
    $rootScope.projectId = path[1];
    $rootScope.corpusId = path[2];
    $rootScope.docId = path[3];
  });

})(window);
