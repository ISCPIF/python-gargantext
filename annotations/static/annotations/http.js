(function () {
  'use strict';

  var http = angular.module('annotationsAppHttp', ['ngResource', 'ngCookies']);

  http.config(['$httpProvider', function($httpProvider){
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
  }]);
  /*
  * DocumentHttpService: Read Document
  * ===================
  *
  * route: annotations/documents/@d_id
  * ------
  *
  * exemple:
  * --------
  * {
  *   "id": 556,
  *   "publication_date": "01/01/66",
  *   "title": "Megalithic astronomy: Indications in standing stones",
  *   "abstract_text": "An account is given of a number of surveys of
  *                   stone circles, alignments, etc., found in Britain.
  *                   The geometry of the rings is discussed in so far
  *                   as it affects the determination of the azimuths
  *                   to outliers and other circles.",
  *   "full_text": null,
  *   "journal": "Vistas in Astronomy",
  *   "authors": "A. Thom"
  * }
  *
  */
  http.factory('DocumentHttpService', function($resource) {
    return $resource(
      window.ANNOTATION_API_URL  + "documents/:docId/",
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
  * NgramListHttpService: Read all Ngrams
  * =====================
  *
  * route: annotations/corpora/@c_id/documents/@d_id
  * ------
  *
  * json return format:
  * -------------------
  *   corpus_id : {
  *                lists:   {(list_id:name)+}
  *                doc_id : [ngrams_objects]+,
  *               }
  *
  * exemple:
  * --------
  * "554": {
  *  "lists": { "558": "StopList",  "564": "MiamList",  "565": "MapList" }
  *  "556": [{ "uuid": 2368, "occurrences": 1.0, "text": "idea", "list_id": 564 },
  *          { "uuid": 5031, "occurrences": 1.0, "text": "indications", "list_id": 564},
  *          { "uuid": 5015, "occurrences": 3.0, "text": "star", "list_id": 565 },
  *           ... ],
  *   }
  */
  http.factory('NgramListHttpService', function ($resource) {
    return $resource(
      window.ANNOTATION_API_URL  + 'corpora/:corpusId/documents/:docId',
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
  * NgramHttpService: Create, modify or delete 1 Ngram
  * =================
  *
  * TODO REACTIVATE IN urls.py
  *
  * if new ngram:
  *   -> ngram_id will be "create"
  *   -> route: annotations/lists/@node_id/ngrams/create
  *   -> will land on views.NgramCreate
  *
  * else:
  *   -> ngram_id is a real ngram id
  *   -> route: annotations/lists/@node_id/ngrams/@ngram_id
  *   -> will land on views.NgramCreate
  *
  */
  http.factory('NgramHttpService', function ($resource) {
    return $resource(
      window.ANNOTATION_API_URL  + 'lists/:listId/ngrams/:ngramId',
    	{
        listId: '@listId',
        ngramId: '@id'
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
