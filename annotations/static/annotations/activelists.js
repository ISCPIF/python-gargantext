(function () {
  'use strict';

  var annotationsAppActiveLists = angular.module('annotationsAppActiveLists', []);

  annotationsAppActiveLists.controller('ActiveListsController',
    ['$scope', '$rootScope', '$timeout',
    function ($scope, $rootScope, $timeout) {
      //Lists change
      $scope.activeListsChange = function() {
        var selected = $('.selectpicker option:selected').val();
        var newActive = {};
        $('.selectpicker option:selected').each(function(item, opt) {
          console.log(opt)
          // ex opt:
          // <option id="list---748" value="MAINLIST">MAINLIST</option>
          var id = opt.id.split("---", 2)[1];
          if(opt.value == 'map list'){
            var name = "map list"
            var value = "MAPLIST"
          }
          else if (opt.value == "stop list"){
            var name = "stop list"
            var value = "STOPLIST"
          }
          else {
            var name = "candidate list"
            var value = "MAINLIST"
          }
          newActive[id] = {"value":value, "name":name};
        });

        // ex: {745: "MAINLIST", 748: "MAPLIST"}
        $rootScope.activeLists = newActive;
      };

      $rootScope.$watchCollection('activeLists', function (newValue, oldValue) {
        if (newValue === undefined) return;
        $timeout(function() {
          $('.selectpicker').selectpicker('refresh');
        });
      });


      // FIXME: est-ce qu'on ne pourrait pas directement utiliser lists
      // au lieu  de recopier dans allListsSelect ?
      $rootScope.$watchCollection('lists', function (newValue, oldValue) {
        console.log(">>>CHANGE", newValue, oldValue)
        if (newValue === undefined) return;
        // reformat lists to allListsSelect
        var allListsSelect = [];
        // console.log($rootScope.lists)
        angular.forEach($rootScope.lists, function(value, key) {
          //console.log(value, key)
          if (value == "MAPLIST"){
            var name = "map list"
          }
          else if (value == "STOPLIST"){
            var name = "stop list"
          }
          else{
            var name = "candidate list"
          }

          allListsSelect.push({
            'id': key,
            'label': value,
            'name':  name,
          });
          // initialize activeLists with the MAPLIST by default
          if (value == 'MAPLIST') {
            $rootScope.activeLists = {};
            $rootScope.activeLists[key] = {"value":value, "name":"map terms"};
          }
        }, allListsSelect);

        $rootScope.allListsSelect = allListsSelect;

        $timeout(function() {
          $('.selectpicker').selectpicker();
          $('.selectpicker').selectpicker('val', ['MAPLIST']);
        });
      });

    }]);


})(window);
