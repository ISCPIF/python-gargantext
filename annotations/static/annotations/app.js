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
    // ex: projects/1/corpora/2/documents/9/
    // ex: projects/1/corpora/2/documents/9/focus=2677 (to highlight ngram 2677 more)
    var path = window.location.pathname.match(/\/projects\/(.*)\/corpora\/(.*)\/documents\/(.*)\/(?:focus=([0-9,]+))?/);
    $rootScope.projectId = path[1];
    $rootScope.corpusId = path[2];
    $rootScope.docId = path[3];
    $rootScope.focusNgram = path[4];

    // debug
    // console.log("==> $rootScope <==")
    // console.log($rootScope)
  });

})(window);
