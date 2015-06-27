(function () {
  'use strict';

  var S = window.STATIC_URL;

  window.annotationsApp = angular.module('annotationsApp', ['annotationsAppHttp']);

  window.annotationsApp.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
    $interpolateProvider.endSymbol('}]}');
  });

  /*
  * Template of the ngram element displayed in the flat lists (called "extra-text")
  */
  window.annotationsApp.directive('keywordTemplate', function () {
    return {
      templateUrl: function ($element, $attributes) {
        return S + 'annotations/keyword_tpl.html';
      }
    };
  });

  /*
  * For ngram elements displayed in the flat lists (called "extra-text")
  */
  window.annotationsApp.controller('ExtraAnnotationController',
    ['$scope', '$rootScope', '$element', 'NgramHttpService',
    function ($scope, $rootScope, $element, NgramHttpService) {
      // TODO use the tooltip ?
      $scope.onDeleteClick = function () {
        NgramHttpService.delete({
          'listId': $scope.keyword.list_id,
          'ngramId': $scope.keyword.uuid
        }).$promise.then(function(data) {
          $.each($rootScope.annotations, function(index, element) {
            if (element.list_id == $scope.keyword.list_id && element.uuid == $scope.keyword.uuid) {
              $rootScope.annotations.splice(index, 1);
              return false;
            }
          });
        });
      };
    }]);

  /*
  * For mouse selection on the text
  */
  window.annotationsApp.controller('AnnotationController',
    ['$scope', '$rootScope', '$element',
      function ($scope, $rootScope, $element) {
      // FIXME maybe use angular.copy of the annotation
      var keyword = _.find(
        $rootScope.annotations,
        function(annotation) { return annotation.uuid.toString() === $element[0].getAttribute('uuid').toString(); }
      );
      // attach the annotation scope dynamically
      if (keyword) {
        $scope.keyword = keyword;
      }

      $scope.onClick = function(e) {
        $rootScope.$emit("positionAnnotationMenu", e.pageX, e.pageY);
        $rootScope.$emit("toggleAnnotationMenu", $scope.keyword);
        e.stopPropagation();
      };
  }]);

  /*
  * Controller of the menu over the current mouse selection
  */
  window.annotationsApp.controller('AnnotationMenuController',
    ['$scope', '$rootScope', '$element', '$timeout', 'NgramHttpService',
    function ($scope, $rootScope, $element, $timeout, NgramHttpService) {
      /*
      * Universal text selection
      */
      function getSelected() {
          if (window.getSelection) {
              return window.getSelection();
          }
          else if (document.getSelection) {
              return document.getSelection();
          }
          else {
              var selection = document.selection && document.selection.createRange();
              if (selection.text) {
                  return selection.text;
              }
              return false;
          }
          return false;
      }
      // we only need one singleton at a time
      var selection = getSelected();

      /*
      * When mouse selection is started, we highlight it
      */
      function toggleSelectionHighlight(text) {
        if (text.trim() !== "") {
          $(".text-panel").addClass("selection");
        } else {
          $(".text-panel").removeClass("selection");
        }
      }

      /*
      * Dynamically construct the selection menu scope
      */
      function toggleMenu(context, annotation) {
        $timeout(function() {
          $scope.$apply(function() {
            var miamlist_id = _.invert($rootScope.activeLists).MiamList;
            var stoplist_id = _.invert($rootScope.activeLists).StopList;
            // variable used in onClick
            $scope.selection_text = angular.copy(annotation);

            if (angular.isObject(annotation)) {
              // existing ngram
              // Delete from the current list
              $scope.menuItems = [
                {
                  'action': 'delete',
                  'listId': annotation.list_id,
                  'verb': 'Delete from',
                  'listName': $rootScope.lists[annotation.list_id]
                }
              ];
              if ($rootScope.lists[annotation.list_id] == "MiamList") {
                // Add to the alternative list
                $scope.menuItems.push({
                    'action': 'post',
                    'listId': stoplist_id,
                    'verb': 'Add to',
                    'listName': $rootScope.lists[stoplist_id]
                  });
              } else if ($rootScope.lists[annotation.list_id] == "StopList") {
                // Add to the alternative list
                $scope.menuItems.push({
                    'action': 'post',
                    'listId': miamlist_id,
                    'verb': 'Add to',
                    'listName': $rootScope.lists[miamlist_id]
                  });
              }
              // show the menu
              $element.fadeIn(100);
            } else if (annotation.trim() !== "") {
              // new ngram
              $scope.menuItems = [
                {
                  'action': 'post',
                  'listId': miamlist_id,
                  'verb': 'Add to',
                  'listName': $rootScope.activeLists[miamlist_id]
                }
              ];
              // show the menu
              $element.fadeIn(100);
            } else {
              $scope.menuItems = [];
              // close the menu
              $element.fadeOut(100);
            }
          });
        });
      }

      var pos = $(".text-panel").position();

      function positionElement(context, x, y) {
        // todo try bootstrap popover component
        $element.css('left', x + 10);
        $element.css('top', y + 10);
      }

      function positionMenu(e) {
        positionElement(null, e.pageX, e.pageY);
      }

      /*
      * Dynamically position the menu
      */
      $(".text-container").mousedown(function(){
        $(".text-container").mousemove(positionMenu);
      });

      /*
      * Finish positioning the menu then display the menu
      */
      $(".text-container").mouseup(function(){
        $(".text-container").unbind("mousemove", positionMenu);
        toggleSelectionHighlight(selection.toString().trim());
        toggleMenu(null, selection.toString().trim());
      });

      /*
      * Toggle the menu when clicking on an existing ngram keyword
      */
      $(".text-container").delegate(':not("#selection")', "click", function(e) {
        if ($(e.target).hasClass("keyword-inline")) return;
        positionMenu(e);
        toggleSelectionHighlight(selection.toString().trim());
        toggleMenu(null, selection.toString().trim());
      });

      $rootScope.$on("positionAnnotationMenu", positionElement);
      $rootScope.$on("toggleAnnotationMenu", toggleMenu);

      /*
      * Menu click action
      */
      $scope.onMenuClick = function($event, action, listId) {
        if (angular.isObject($scope.selection_text)) {
          // delete from the current list
          NgramHttpService[action]({
              'listId': listId,
              'ngramId': $scope.selection_text.uuid
            }).$promise.then(function(data) {
              $.each($rootScope.annotations, function(index, element) {
                if (element.list_id == listId && element.uuid == $scope.selection_text.uuid) {
                  $rootScope.annotations.splice(index, 1);
                  return false;
                }
              });
          });

        } else if ($scope.selection_text.trim() !== "") {
          // new annotation from selection
          NgramHttpService.post(
            {
              'listId': listId
            },
            {'annotation' : {'text': $scope.selection_text.trim()}}
          ).$promise.then(function(data) {
            $rootScope.annotations.push(data);
          });
        }
        // hide the highlighted text the the menu
        $(".text-panel").removeClass("selection");
        $element.fadeOut(100);
      };
    }
  ]);

  /*
  * Text highlighting controller
  */
  window.annotationsApp.controller('IntraTextController',
    ['$scope', '$rootScope', '$compile', 'NgramHttpService',
    function ($scope, $rootScope, $compile, NgramHttpService) {

      $scope.extraNgramList = {};
      $scope.currentListPage = angular.forEach($rootScope.activeLists, function(name, id) {
        this[id] = 0;
      }, {});

      $scope.pageSize = 15;
      var counter = 0;

      /*
      * Replace the text by an html template for ngram keywords
      */
      function replaceTextByTemplate(text, ngram, template, pattern, lists) {
        return text.replace(pattern, function(matched) {
          var tpl = angular.element(template);
          tpl.append(matched);
          tpl.attr('title', ngram.tooltip_content);
          tpl.attr('uuid', ngram.uuid);
          /*
          * Add CSS class depending on the list the ngram is into
          * FIXME Lists names and css classes are fixed, can do better
          */
          tpl.addClass(ngram.listName);
          return tpl.get(0).outerHTML;
        });
      }

      /*
       * Sorts annotations on the number of words
       * Required for overlapping ngrams
       */
      function lengthSort(listitems, valuekey) {
          listitems.sort(function(a, b) {
              var compA = a[valuekey].split(" ").length;
              var compB = b[valuekey].split(" ").length;
              return (compA > compB) ? -1 : (compA <= compB) ? 1 : 0;
          });
          return listitems;
      }
      /*
      * Match and replace Ngram into the text
      */
      function compileNgramsHtml(annotations, textMapping, $rootScope) {
        // TODO remove debug counter
        counter = 0;
        var templateBegin = "<span ng-controller='AnnotationController' ng-click='onClick($event)' class='keyword-inline'>";
        var templateBeginRegexp = "<span ng-controller='AnnotationController' ng-click='onClick\(\$event\)' class='keyword-inline'>";

        var templateEnd = "</span>";
        var template = templateBegin + templateEnd;

        var startPattern = "\\b((?:"+templateBeginRegexp+")*";
        var middlePattern = "(?:<\/span>)*\\s(?:"+templateBeginRegexp+")*";
        var endPattern = "(?:<\/span>)*)\\b";

        var sortedSizeAnnotations = lengthSort(annotations, "text"),

            extraNgramList = angular.copy($scope.extraNgramList);

        extraNgramList = angular.forEach(extraNgramList, function(name, id) {
          extraNgramList[id] = [];
        });


        _.each(sortedSizeAnnotations, function (annotation) {
          // exclude ngrams that are into inactive lists
          if ($rootScope.activeLists[annotation.list_id] === undefined) return;
          // used to setup css class
          annotation.listName = $rootScope.lists[annotation.list_id];
          // regexps
          var words = annotation.text.split(" ");
          var pattern = new RegExp(startPattern + words.join(middlePattern) + endPattern, 'gmi');
          var textRegexp = new RegExp("\\b"+annotation.text+"\\b", 'igm');
          var isDisplayedIntraText = false;
          // highlight text as html
          angular.forEach(textMapping, function(text, eltId) {
            if (pattern.test(text) === true) {
              textMapping[eltId] = replaceTextByTemplate(text, annotation, template, pattern, $rootScope.lists);
              // TODO remove debug
              counter++;
              isDisplayedIntraText = true;
            }
          });

          if (!isDisplayedIntraText) {
            // add extra-text ngrams that are not already displayed
            if ($.inArray(annotation.uuid, extraNgramList[annotation.list_id].map(function (item) {
                return item.uuid;
              })) == -1) {
              // push the ngram and sort
              extraNgramList[annotation.list_id] = lengthSort(extraNgramList[annotation.list_id].concat(annotation), "text");
            }
          }
        });
        // update extraNgramList
        $scope.extraNgramList = extraNgramList;
        // return the object of element ID with the corresponding HTML
        return textMapping;
      }

      /*
      * Listen changes on the ngram data
      */
      $rootScope.$watchCollection('annotations', function (newValue, oldValue) {
        if ($rootScope.annotations === undefined) return;
        if (angular.equals(newValue, oldValue)) return;

        // initialize extraNgramList
        $scope.extraNgramList = angular.copy($rootScope.activeLists);
        $scope.extraNgramList = angular.forEach($scope.extraNgramList, function(name, id) {
          $scope.extraNgramList[id] = [];
        });
        /*
        * Transform text into HTML with higlighted ngrams
        */
        var result = compileNgramsHtml(
          $rootScope.annotations,
          {
            '#full-text': angular.copy($rootScope.full_text),
            '#abstract-text': angular.copy($rootScope.abstract_text),
            '#title': angular.copy($rootScope.title)
          },
          $rootScope
        );
        // inject highlighted HTML
        angular.forEach(result, function(html, eltId) {
          angular.element(eltId).html(html);
        });
        // inject one Angular controller on every highlighted text element
        angular.element('.text-container').find('[ng-controller=AnnotationController]').each(function(idx, elt) {
          angular.element(elt).replaceWith($compile(elt)($rootScope.$new(true)));
        });
      });

      /*
      * Add a new NGram from the free user input in the extra-text list
      */
      $scope.onListSubmit = function ($event, listId) {
        var inputEltId = "#"+ listId +"-input";
        if ($event.keyCode !== undefined && $event.keyCode != 13) return;

        var value = $(inputEltId).val().trim();
        if (value === "") return;

        NgramHttpService.post(
          {
            'listId': listId,
            'ngramId': 'new'
          },
          {
            'annotation' : {'text': value}
          },
          function(data) {
            // on success
            if (data) {
              $rootScope.annotations.push(data);
              $(inputEltId).val("");
            } else {
              $(inputEltId).addClass("error");
            }
          }, function(data) {
            // on error
            $(inputEltId).addClass("error");
          }
        );
      };

      $scope.totalListPages = function (listId) {
        if ($scope.extraNgramList[listId] === undefined) return 0;
        return Math.ceil($scope.extraNgramList[listId].length / $scope.pageSize);
      };

      $scope.nextListPage = function(listId) {
        $scope.currentListPage[listId] = $scope.currentListPage[listId] + 1;
      };

      $scope.previousListPage = function(list) {
        $scope.currentListPage[listId] = $scope.currentListPage[listId] - 1;
      };
    }
  ]);

  /*
  * Filter used in Ngram flat lists pagination (extra-text panel)
  */
  window.annotationsApp.filter('startFrom', function () {
    return function (input, start) {
      if (input === undefined) return;
      start = +start; //parse to int
      return input.slice(start);
    };
  });

  window.annotationsApp.controller('DocController',
    ['$scope', '$rootScope', 'NgramListHttpService', 'DocumentHttpService',
    function ($scope, $rootScope, NgramListHttpService, DocumentHttpService) {
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
          $rootScope.annotationsResource = NgramListHttpService.get(
            {
              'corpusId': $rootScope.corpusId,
              'docId': $rootScope.docId
            }
          ).$promise.then(function(data) {
            $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
            $rootScope.lists = data[$rootScope.corpusId.toString()].lists;
            // TODO active list selection controller
            $rootScope.activeLists = $rootScope.lists;
            $rootScope.mainListId = _.invert($rootScope.activeLists).MiamList;
          });
      });

    // TODO setup article pagination
    $scope.onPreviousClick = function () {
      DocumentHttpService.get($scope.docId - 1);
    };
    $scope.onNextClick = function () {
      DocumentHttpService.get($scope.docId + 1);
    };
  }]);

  /*
  * Main function
  * GET the document node and all its ngrams
  */
  window.annotationsApp.run(function ($rootScope) {
    var path = window.location.pathname.match(/\/project\/(.*)\/corpus\/(.*)\/document\/(.*)\//);
    $rootScope.projectId = path[1];
    $rootScope.corpusId = path[2];
    $rootScope.docId = path[3];
  });

})(window);
