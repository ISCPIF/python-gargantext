(function () {
  'use strict';

  var annotationsAppActiveLists = angular.module('annotationsAppActiveLists', []);

  annotationsAppActiveLists.controller('ActiveListsController',
    ['$scope', '$rootScope', '$timeout',
    function ($scope, $rootScope, $timeout) {

      $scope.activeListsChange = function() {
        var selected = $('.selectpicker option:selected').val();
        var newActive = {};
        $('.selectpicker option:selected').each(function(item, value) {
          var id = value.id.split("---", 2)[1];
          newActive[id] = value.value;
        });
        $rootScope.activeLists = newActive;
      };

      $rootScope.$watchCollection('activeLists', function (newValue, oldValue) {
        if (newValue === undefined) return;
        $timeout(function() {
          $('.selectpicker').selectpicker();
          $('.selectpicker').selectpicker('val', ['MiamList']);
          $('.selectpicker').selectpicker('refresh');
        });
      });

      $rootScope.$watchCollection('lists', function (newValue, oldValue) {
        if (newValue === undefined) return;
        var allListsSelect = [];
        angular.forEach($rootScope.lists, function(value, key) {
          this.push({
            'id': key,
            'label': value
          });
          if (value == 'MiamList') {
            $rootScope.activeLists = {};
            $rootScope.activeLists[key] = value;
          }
        }, allListsSelect);
        $rootScope.allListsSelect = allListsSelect;

        $timeout(function() {
          $('.selectpicker').selectpicker();
        });
        console.log($rootScope.allListsSelect);
      });

    }]);


})(window);
