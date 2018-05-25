(function () {
  'use strict';

  var http = angular.module('annotationsAppHttp', ['ngResource', 'ngCookies']);

  http.config(['$httpProvider', function($httpProvider){
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
  }]);

  function url(path) {
    // adding explicit "http[s]://" -- for cross origin requests
    return location.protocol + '//' + window.GARG_ROOT_URL + path;
  }

  /*
  * DocumentHttpService: Read Document
  * ===================
  *
  * route: annotations/documents/@d_id
  * ------
  * TODO use external: api/nodes/@d_id?fields[]=hyperdata
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
  *  "556": [{ "uuid": 2368, "occs": 1.0, "text": "idea", "list_id": 564 },
  *          { "uuid": 5031, "occs": 1.0, "text": "indications", "list_id": 564},
  *          { "uuid": 5015, "occs": 3.0, "text": "star", "list_id": 565 },
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
  * MainApiAddNgramHttpService: Create and index a new ngram
  * ===========================
  * route: PUT api/ngrams?text=mynewngramstring&corpus=corpus_id
  *
  * NB it also checks if ngram exists (returns the preexisting id)
  *    and if it has a mainform/group (via 'testgroup' option)
  *                                   (useful if we add it to a list afterwards)
  *
  */
  http.factory('MainApiAddNgramHttpService', function($resource) {
    return $resource(
      url("/api/ngrams?text=:ngramStr&corpus=:corpusId&testgroup"),
      {
        ngramStr: '@ngramStr',
        corpusId: '@corpusId',
      },
      {
        put: {
          method: 'PUT',
          params: {listId: '@listId', ngramIdList: '@ngramIdList'}
        }
      }
    );
  });


  /*
  * MainApiChangeNgramHttpService: Add/remove ngrams from lists
  * =============================
  * route: api/ngramlists/change?list=LISTID&ngrams=ID1,ID2...
  *
  * (same route used in ngrams table)
  *
  * /!\ for this route we reach out of this annotation module
  *     and send directly to the gargantext api route for list change
  *     (cross origin request with http protocol scheme)
  * ------
  *
  */

  http.factory('MainApiChangeNgramHttpService', function($resource) {
    return $resource(
      url("/api/ngramlists/change?list=:listId&ngrams=:ngramIdList"),
      {
        listId: '@listId',
        ngramIdList: '@ngramIdList'  // list in str form (sep=","): "12,25,30"
                                     // (usually in this app just 1 id): "12"
      },
      {
        put: {
          method: 'PUT',
          params: {listId: '@listId', ngramIdList: '@ngramIdList'}
        },
        delete: {
          method: 'DELETE',
          params: {listId: '@listId', ngramIdList: '@ngramIdList'}
        }
      }
    );
  });

  /*
  * MainApiFavoritesHttpService: Check/Add/Del Document in favorites
  * ============================
  * route: api/nodes/574/favorites?docs=576
  * /!\ for this route we reach out of this annotation module
  *     and send directly to the gargantext api route for favs
  *     (cross origin request with http protocol scheme)
  * ------
  *
  * exemple:
  * --------
  * {
  *  "favdocs": [576]        // <== if doc is among favs
  *  "missing": []           // <== if doc is not in favs
  * }
  *
  */
  http.factory('MainApiFavoritesHttpService', function($resource) {
    return $resource(
      url("/api/nodes/:corpusId/favorites?docs=:docId"),
      {
        corpusId: '@corpusId',
        docId: '@docId'
      },
      {
        get: {
          method: 'GET',
          params: {corpusId: '@corpusId', docId: '@docId'}
        },
        put: {
          method: 'PUT',
          params: {corpusId: '@corpusId', docId: '@docId'}
        },
        delete: {
          method: 'DELETE',
          params: {corpusId: '@corpusId', docId: '@docId'}
        }
      }
    );
  });



})(window);
