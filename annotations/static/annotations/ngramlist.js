(function () {
  'use strict';

  var annotationsAppNgramList = angular.module('annotationsAppNgramList', ['annotationsAppHttp']);

  /*
  * Controls one Ngram displayed in the flat lists (called "extra-text")
  */
  annotationsAppNgramList.controller('NgramController',
    ['$scope', '$rootScope', 'MainApiChangeNgramHttpService', 'NgramListHttpService',
    function ($scope, $rootScope, MainApiChangeNgramHttpService, NgramListHttpService) {
      /*
      * Click on the 'delete' cross button
      * (NB: we have different delete consequences depending on list)
      */
      $scope.onDeleteClick = function () {
          var listName = $scope.keyword.listName
          var thisListId = $scope.keyword.list_id
          var thisNgramId = $scope.keyword.uuid
          var crudActions = [] ;

          if (listName == 'MAPLIST') {
              crudActions = [
                  ["delete", thisListId]
              ]
          }
          else if (listName == 'MAINLIST') {
              crudActions = [
                  ["delete", thisListId],
                  ["put", $rootScope.listIds.STOPLIST],
              ]
          }
          else if (listName == 'STOPLIST') {
              crudActions = [
                  ["delete", thisListId],
                  ["put", $rootScope.listIds.MAINLIST],
              ]
          }

          // using recursion to make chained calls,
          // todo factorize with highlight.js

          var lastCallback = function() {
              // Refresh the annotationss
              NgramListHttpService.get(
                {'corpusId': $rootScope.corpusId,
                  'docId': $rootScope.docId},
                function(data) {
                  // $rootScope.annotations
                  // ----------------------
                  // is the union of all lists, one being later "active"
                  // (then used for left-side flatlist AND inline annots)
                  $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
                  // TODO £NEW : lookup obj[list_id][term_text] = {terminfo}
                  // $rootScope.lookup =
                  $rootScope.refreshDisplay();
                },
                function(data) {
                  console.error("unable to refresh the list of ngrams");
                }
              );
          }

          // chained recursion to do several actions then callback (eg refresh)
          function makeChainedCalls (i, listOfActions, finalCallback) {
            // each action couple has 2 elts
            var action = listOfActions[i][0]
            var listId = listOfActions[i][1]

            MainApiChangeNgramHttpService[action](
                    {'listId': thisListId,
                     'ngramIdList': thisNgramId},

                     // on success
                     function(data) {
                        // case NEXT
                        //      ----
                        // when chained actions
                        if (listOfActions.length > i+1) {
                            console.log("calling next action ("+(i+1)+")")

                            // ==============================================
                            makeChainedCalls(i+1, listOfActions, finalCallback)
                            // ==============================================

                        }
                        // case LAST
                        //     ------
                        // when last action
                        else {
                            finalCallback()
                        }
                    },
                    // on error
                    function(data) {
                      console.error("unable to edit the Ngram \""+ngramText+"\""
                                   +"(ngramId "+ngramId+")"+"at crud no "+i
                                   +" ("+action+" on list "+listId+")");
                    }
            );
          }

          // run the loop by calling the initial recursion step
          makeChainedCalls(0, crudActions, lastCallback)
      };
    }]);

  /*
  * Controller for the list panel displaying extra-text ngram
  */
  annotationsAppNgramList.controller('NgramListPaginationController',
    ['$scope', '$rootScope', function ($scope, $rootScope) {

    $rootScope.$watchCollection('ngramsInPanel', function (newValue, oldValue) {
      $scope.currentListPage = 0;
      $scope.pageSize = 15;

      $scope.nextListPage = function() {
        $scope.currentListPage = $scope.currentListPage + 1;
      };

      $scope.previousListPage = function() {
        $scope.currentListPage = $scope.currentListPage - 1;
      };

      $scope.totalListPages = function(listId) {
        if ($rootScope.ngramsInPanel[listId] === undefined) return 0;
        return Math.ceil($rootScope.ngramsInPanel[listId].length / $scope.pageSize);
      };
    });
  }]);

  /*
  * Template of the ngram element displayed in the flat lists
  */
  annotationsAppNgramList.directive('keywordTemplate', function () {
    return {
      templateUrl: function ($element, $attributes) {
        return S + 'annotations/keyword_tpl.html';
      }
    };
  });
  /*
  * new NGram from the user input
  */
  annotationsAppNgramList.controller('NgramInputController',
    ['$scope', '$rootScope', '$element', 'NgramListHttpService',
    function ($scope, $rootScope, $element, NgramListHttpService) {
    /*
    * Add a new NGram from the user input in the extra-text list
    */
    $scope.onListSubmit = function ($event, listId) {
      var inputEltId = "#"+ listId +"-input";
      if ($event.keyCode !== undefined && $event.keyCode != 13) return;

      var value = angular.element(inputEltId).val().trim();
      if (value === "") return;

      // £TEST locally check if already in annotations NodeNgrams ------

      // $rootScope.annotations = array of ngram objects like:
      // {"list_id":805,"occurrences":2,"uuid":9386,"text":"petit échantillon"}

      console.log('looking for "' + value + '" in list:' + listId)
      var already_in_list = false ;
      angular.forEach($rootScope.annotations, function(annot,i) {
        // console.log(i + ' => ' + annot.text + ',' + annot.list_id) ;
        if (value == annot.text && listId == annot.list_id) {
          console.log('the term "' + value + '" was already present in list')
          // no creation
          already_in_list = true ;
        }
      }
      );
      if (already_in_list) { return ; }
      // ---------------------------------------------------------------

      // will check if there's a preexisting ngramId for this value
      // TODO: reconnect separately from list addition
      // TODO: if maplist => also add to miam
    //   NgramHttpService.post(
    //     {
    //       'listId': listId,
    //       'ngramId': 'create'
    //     },
    //     {
    //       'text': value
    //     },
    //     function(data) {
    //       console.warn("refresh attempt");
    //       // on success
    //       if (data) {
    //         angular.element(inputEltId).val("");
    //         // Refresh the annotationss
    //         NgramListHttpService.get(
    //           {
    //             'corpusId': $rootScope.corpusId,
    //             'docId': $rootScope.docId
    //           },
    //           function(data) {
    //             $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
      //
    //             // TODO £NEW : lookup obj[list_id][term_text] = {terminfo}
    //             // $rootScope.lookup =
      //
      //
    //             $rootScope.refreshDisplay();
    //           },
    //           function(data) {
    //             console.error("unable to get the list of ngrams");
    //           }
    //         );
    //       }
    //     }, function(data) {
    //       // on error
    //       angular.element(inputEltId).parent().addClass("has-error");
    //       console.error("error adding Ngram "+ value);
    //     }
    //   );
    };
  }]);

})(window);
