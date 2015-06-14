(function () {
  'use strict';

  var http = angular.module('annotationsAppHttp', ['ngResource', 'ngCookies']);

  http.config(['$httpProvider', function($httpProvider){
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
  }]);
  /*
  * Read Document
  */
  http.factory('DocumentHttpService', function($resource) {
    return $resource(
      window.ANNOTATION_API_URL  + "document/:docId/",
      {
        docId: '@docId'
      },
      {
        get: {
          method: 'GET',
          params: {docId: '@docId'}
        }
      }
    );
  });

  /*
  * Read all Ngrams
  */
  http.factory('NgramListHttpService', function ($resource) {
    return $resource(
      window.ANNOTATION_API_URL  + 'corpus/:corpusId/document/:docId',
    	{
        corpusId: '@corpusId',
        docId: '@docId'
      },
			{
        get: {
    			method: 'GET',
    			params: {}
    		}
      }
    );
  });

  /*
  * Create, modify or delete 1 Ngram
  */
  http.factory('NgramHttpService', function ($resource) {
    return $resource(
      window.ANNOTATION_API_URL  + 'lists/:listId/ngrams/:ngramId/',
    	{
        listId: '@listId',
        ngramId: '@ngramId'
      },
			{
        post: {
          method: 'POST',
          params: {'listId': '@listId', 'ngramId': '@ngramId'}
        },
        delete: {
          method: 'DELETE',
          params: {'listId': '@listId', 'ngramId': '@ngramId'}
        }
      }
    );
  });
})(window);
