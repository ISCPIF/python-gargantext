(function () {
  'use strict';

  var annotationsAppNgramList = angular.module('annotationsAppNgramList', ['annotationsAppHttp']);

  /*
  * Controls one Ngram displayed in the flat lists (called "extra-text")
  */
  annotationsAppNgramList.controller('NgramController',
    ['$scope', '$rootScope', 'NgramHttpService', 'NgramListHttpService',
    function ($scope, $rootScope, NgramHttpService, NgramListHttpService) {
      /*
      * Click on the 'delete' cross button
      */
      $scope.onDeleteClick = function () {
        NgramHttpService.delete({
          'listId': $scope.keyword.list_id,
          'ngramId': $scope.keyword.uuid
        }, function(data) {
          // Refresh the annotationss
          NgramListHttpService.get(
            {
              'corpusId': $rootScope.corpusId,
              'docId': $rootScope.docId
            },
            function(data) {
              $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
              $rootScope.refreshDisplay();
            },
            function(data) {
              console.error("unable to refresh the list of ngrams");
            }
          );
        }, function(data) {
          console.error("unable to remove the Ngram " + $scope.keyword.text);
        });
      };
    }]);

  /*
  * Controller for the list panel displaying extra-text ngram
  */
  annotationsAppNgramList.controller('NgramListPaginationController',
    ['$scope', '$rootScope', function ($scope, $rootScope) {

    $rootScope.$watchCollection('extraNgramList', function (newValue, oldValue) {
      $scope.currentListPage = 0;
      $scope.pageSize = 15;

      $scope.nextListPage = function() {
        $scope.currentListPage = $scope.currentListPage + 1;
      };

      $scope.previousListPage = function() {
        $scope.currentListPage = $scope.currentListPage - 1;
      };

      $scope.totalListPages = function(listId) {
        if ($rootScope.extraNgramList[listId] === undefined) return 0;
        return Math.ceil($rootScope.extraNgramList[listId].length / $scope.pageSize);
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
    ['$scope', '$rootScope', '$element', 'NgramHttpService', 'NgramListHttpService',
    function ($scope, $rootScope, $element, NgramHttpService, NgramListHttpService) {
    /*
    * Add a new NGram from the user input in the extra-text list
    */
    $scope.onListSubmit = function ($event, listId) {
      var inputEltId = "#"+ listId +"-input";
      if ($event.keyCode !== undefined && $event.keyCode != 13) return;

      var value = angular.element(inputEltId).val().trim();
      if (value === "") return;

      NgramHttpService.post(
        {
          'listId': listId,
          'ngramId': 'create'
        },
        {
          'text': value
        },
        function(data) {
          // on success
          if (data) {
            angular.element(inputEltId).val("");
            // Refresh the annotationss
            NgramListHttpService.get(
              {
                'corpusId': $rootScope.corpusId,
                'docId': $rootScope.docId
              },
              function(data) {
                $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
                $rootScope.refreshDisplay();
              },
              function(data) {
                console.error("unable to get the list of ngrams");
              }
            );
          }
        }, function(data) {
          // on error
          angular.element(inputEltId).parent().addClass("has-error");
          console.error("error adding Ngram "+ value);
        }
      );
    };
  }]);

})(window);
