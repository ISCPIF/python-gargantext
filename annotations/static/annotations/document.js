(function () {
  'use strict';

  var annotationsAppDocument = angular.module('annotationsAppDocument', ['annotationsAppHttp']);


  annotationsAppDocument.controller('DocController',
    ['$scope', '$rootScope', '$timeout', 'NgramListHttpService', 'DocumentHttpService',
    function ($scope, $rootScope, $timeout, NgramListHttpService, DocumentHttpService) {
      $rootScope.documentResource = DocumentHttpService.get(
        {'docId': $rootScope.docId},
        function(data, responseHeaders) {
          $scope.authors = data.authors;
          $scope.journal = data.journal;
          $scope.publication_date = data.publication_date;
          //$scope.current_page_number = data.current_page_number;
          //$scope.last_page_number = data.last_page_number;
          $rootScope.title = data.title;
          $rootScope.docId = data.id;
          $rootScope.full_text = data.full_text;
          $rootScope.abstract_text = data.abstract_text;
          // GET the annotationss
          NgramListHttpService.get(
            {
              'corpusId': $rootScope.corpusId,
              'docId': $rootScope.docId
            },
            function(data) {
              $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
              $rootScope.lists = data[$rootScope.corpusId.toString()].lists;
            }
          );
      });
      // TODO setup article pagination
      $scope.onPreviousClick = function () {
        DocumentHttpService.get($scope.docId - 1);
      };
      $scope.onNextClick = function () {
        DocumentHttpService.get($scope.docId + 1);
      };
  }]);


})(window);
