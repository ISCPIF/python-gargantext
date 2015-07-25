(function () {
  'use strict';

  var annotationsAppNgramList = angular.module('annotationsAppNgramList', ['annotationsAppHttp']);

  /*
  * Controls one Ngram displayed in the flat lists (called "extra-text")
  */
  annotationsAppNgramList.controller('NgramController',
    ['$scope', '$rootScope', '$element', 'NgramHttpService',
    function ($scope, $rootScope, $element, NgramHttpService) {
      /*
      * Click on the 'delete' cross button
      */
      $scope.onDeleteClick = function () {
        NgramHttpService.delete({
          'listId': $scope.keyword.list_id,
          'ngramId': $scope.keyword.uuid
        }, function(data) {
          $.each($rootScope.annotations, function(index, element) {
            if (element.list_id == $scope.keyword.list_id && element.uuid == $scope.keyword.uuid) {
              $rootScope.annotations.splice(index, 1);
              return false;
            }
          });
        }, function(data) {
          console.log(data);
          console.error("unable to delete the Ngram " + $scope.keyword.uuid);
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

      $scope.totalListPages = function (listId) {
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
})(window);
