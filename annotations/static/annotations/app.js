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

    // shared vars -------------------
    $rootScope.projectId = path[1];
    $rootScope.corpusId = path[2];
    $rootScope.docId = path[3];
    $rootScope.focusNgram = path[4];
    // -------------------------------

    // shared toolbox (functions useful for several modules) -------------------
    $rootScope.mafonction = function (bidule) {console.warn(bidule)}

    // chained recursion to do several AJAX actions and then a callback (eg refresh)
    $rootScope.makeChainedCalls =
    function (i, listOfCalls, finalCallback, lastCache) {

      var callDetails = listOfCalls[i]

      console.log(">> calling ajax call ("+(i+1)+"/"+listOfCalls.length+")")

      // each callDetails object describes the Ajax call
      // and passes the required functions and arguments
      // via 3 properties: service, action, params
      // ex: callDetails = {
      //        'service' : MainApiChangeNgramHttpService,
      //        'action'  : 'delete'
      //        'params'  : { 'listId': ..., 'ngramIdList':...}

      // there is an optional 4th slot: the dataPropertiesToCache directive
      //
      //        'dataPropertiesToCache' : ['id']  <== means that on call success
      //                                              we will store data.id into
      //                                              cache.id for next calls
      //     }

      var service = callDetails['service']
      var params  = callDetails['params']
      var action  = callDetails['action']

      // cache if we need to store properties of data response for next calls
      var cache = {}
      if (lastCache) cache = lastCache

      // and interpolation of params with this current cache
      for (var key in params) {
          var val = params[key]
          if (typeof val == "object" && val["fromCache"]) {
            var propToRead = val["fromCache"]
            // console.log("reading from cache: response data property "
            //             +propToRead+" ("+cache[propToRead]+")")
            params[key] = cache[propToRead]
          }
      }

      // Now we run the call
      // ex:
      //                 service                  action
      //                 vvvvv                     vvvv
      //           MainApiChangeNgramHttpService["delete"](
      //   params >>>     {'listId': listId, 'ngramIdList': ngramId},
      //                       onsuccess(), onfailure() )
      service[action](
            params,
            // on success
            function(data) {
              // console.log("SUCCESS:" + action)
              // console.log("listOfCalls.length:" + listOfCalls.length)
              // console.log("i+1:" + i+1)

              // case NEXT
              //      ----
              // when chained actions
              if (listOfCalls.length > i+1) {

                  // if we need to store anything it's the right moment
                  for (var k in callDetails['dataPropertiesToCache']) {
                      var prop = callDetails['dataPropertiesToCache'][k]
                      //  console.log("storing in cache: response data property "
                      //              +prop+" ("+data[prop]+")")
                      cache[prop] = data[prop]
                  }

                  // =======  recursive call for next action in list ================
                  $rootScope.makeChainedCalls(i+1, listOfCalls, finalCallback, cache)
                  // ================================================================
              }
              // case LAST
              //     ------
              // when last action
              else {
                  console.log(">> calling refresh")
                  finalCallback()
              }
            },
            // on error
            function(data) {
              console.error("unable to call ajax no "+i+" with service "+service.name+
                            " (http "+action+" with args "+JSON.stringify(params)+")");
            }
      );
    }
    // -------------------------------------------------------------------------

    // debug
    // console.log("==> $rootScope <==")
    // console.log($rootScope)
  });

})(window);
