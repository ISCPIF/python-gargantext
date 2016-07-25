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
                // only 'remove' is needed here
                {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                 'params' : {'listId':thisListId, 'ngramIdList': thisNgramId} }
              ]
          }
          else if (listName == 'MAINLIST') {
              crudActions = [
                // remove
                {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                 'params' : {'listId':thisListId, 'ngramIdList': thisNgramId} },
                // consequence: add to opposite list
                {'service': MainApiChangeNgramHttpService, 'action': 'put',
                 'params' : {'listId':$rootScope.listIds.STOPLIST, 'ngramIdList': thisNgramId} }
              ]
          }
          else if (listName == 'STOPLIST') {
              crudActions = [
                  // remove
                  {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                   'params' : {'listId':thisListId, 'ngramIdList': thisNgramId} },
                  // consequence: add to opposite list
                  {'service': MainApiChangeNgramHttpService, 'action': 'put',
                   'params' : {'listId':$rootScope.listIds.MAINLIST, 'ngramIdList': thisNgramId} }
                  ]
          }

          // console.log(crudActions)

          // using recursion to make chained calls,
          // run the loop by calling the initial recursion step
          $rootScope.makeChainedCalls(0,   crudActions,   $rootScope.refresh)
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
     'MainApiChangeNgramHttpService', 'MainApiAddNgramHttpService',
    function ($scope, $rootScope, $element, NgramListHttpService,
            MainApiChangeNgramHttpService, MainApiAddNgramHttpService) {
    /*
    * Add a new NGram from the user input in the extra-text list
    */
    $scope.onListSubmit = function ($event, tgtListId) {
      var inputEltId = "#"+ tgtListId +"-input";
      if ($event.keyCode !== undefined && $event.keyCode != 13) return;

      var value = angular.element(inputEltId).val().trim();
      if (value === "") return;

      // locally check if already in annotations NodeNgrams ------------

      // $rootScope.annotations = array of ngram objects like:
      // {"list_id":805,"occs":2,"uuid":9386,"text":"petit échantillon"}

      // TODO £NEW : lookup obj[list_id][term_text] = {terminfo}
      //             // $rootScope.lookup =

      console.log('looking for "' + value + '" in list:' + tgtListId)
      var already_in_list = false ;
      angular.forEach($rootScope.annotations, function(annot,i) {
        // console.log(i + ' => ' + annot.text + ',' + annot.list_id) ;
        if (value == annot.text && tgtListId == annot.list_id) {
          console.log('the term "' + value + '" was already present in list')
          // no creation
          already_in_list = true ;
        }
      }
      );
      if (already_in_list) { return ; }
      // ---------------------------------------------------------------

      var tgtListName = $rootScope.lists[tgtListId]
      // alert("ADDING TO listId: " + tgtListId +"\n listName: "+ tgtListName)

      var crudCallsToMake = []
      switch (tgtListName) {
          case "STOPLIST":
            crudCallsToMake = [
                {'service': MainApiAddNgramHttpService, 'action': 'put',
                'params' : {'ngramStr':value, corpusId: $rootScope.corpusId},
                'dataPropertiesToCache': ['id'] },
                {'service': MainApiChangeNgramHttpService, 'action': 'put',
                'params' : {'listId':tgtListId, 'ngramIdList': {'fromCache': 'id'} } }
            ];
            break;

          case "MAINLIST":
            crudCallsToMake = [
                {'service': MainApiAddNgramHttpService, 'action': 'put',
                 'params' : {'ngramStr':value, corpusId: $rootScope.corpusId},
                 'dataPropertiesToCache': ['id'] },
                {'service': MainApiChangeNgramHttpService, 'action': 'put',
                 'params' : {'listId':tgtListId, 'ngramIdList': {'fromCache': 'id'} } }
            ];
            break;

          case "MAPLIST":
            crudCallsToMake = [
                {'service': MainApiAddNgramHttpService, 'action': 'put',
                'params' : {'ngramStr':value, corpusId: $rootScope.corpusId},
                'dataPropertiesToCache': ['id'] },
                {'service': MainApiChangeNgramHttpService, 'action': 'put',
                 'params' : {'listId':$rootScope.listIds.MAINLIST, 'ngramIdList': {'fromCache': 'id'} } },
                {'service': MainApiChangeNgramHttpService, 'action': 'put',
                'params' : {'listId':tgtListId, 'ngramIdList': {'fromCache': 'id'} } }
            ];
            break;
      }
      // run the ajax calls in a recursive loop by calling the step n° 0
      $rootScope.makeChainedCalls(0, crudCallsToMake, $rootScope.refresh)

    };  // onListSubmit
  }]);

})(window);
