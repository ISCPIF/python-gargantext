(function () {
  'use strict';

  var S = window.STATIC_URL;

  window.annotationsApp = angular.module('annotationsApp', ['annotationsAppHttp']);

  window.annotationsApp.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
    $interpolateProvider.endSymbol('}]}');
  });

  window.annotationsApp.directive('keywordTemplate', function () {
    return {
      templateUrl: function ($element, $attributes) {
        return S + 'annotations/keyword_tpl.html';
      }
    };
  });

  window.annotationsApp.controller('ExtraAnnotationController',
    ['$scope', '$rootScope', '$element', 'NgramHttpService',
    function ($scope, $rootScope, $element, NgramHttpService) {
      // TODO use the tooltip ?
      $scope.onDeleteClick = function () {
        NgramHttpService.delete({
            'listId': $scope.keyword.list_id,
            'ngramId': $scope.keyword.uuid
          }).$promise.then(function(data) {
            NgramListHttpService.get(
              {'corpusId': $rootScope.corpusId, 'docId': $rootScope.docId}
            ).$promise.then(function(data) {
              $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
              $rootScope.lists = data[$rootScope.corpusId.toString()]['lists'];
            });
        });
      };
  }]);

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

  window.annotationsApp.directive('selectionTemplate', function () {
    return {
      templateUrl: function ($element, $attributes) {
        return S + 'annotations/selection_tpl.html';
      }
    };
  });

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

      var selection = getSelected();

      function toggleSelectionHighlight(text) {
        if (text.trim() !== "") {
          $(".text-panel").addClass("selection");
        } else {
          $(".text-panel").removeClass("selection");
        }
      }

      function toggleMenu(context, annotation) {
        $timeout(function() {
          $scope.$apply(function() {

            if (angular.isObject(annotation)) {
              $scope.level = angular.copy(annotation.level || 'global');
              $scope.category = $rootScope.lists[annotation.list_id].toLowerCase();
              $scope.listId = angular.copy(annotation.list_id);
              // used in onClick
              $scope.selection_text = angular.copy(annotation);

              if ($scope.category == "miamlist") {
                $scope.local_miamlist = false;
                $scope.global_stoplist = true;
                $scope.local_stoplist = true;
              } else if ($scope.category == "stoplist") {

                if ($scope.level == "local") {
                  $scope.local_stoplist = false;
                  $scope.global_stoplist = true;
                }
                if ($scope.level == "global") {
                  $scope.global_stoplist = false;
                  $scope.local_stoplist = true;
                }
                $scope.local_miamlist = true;
              }
              // show menu
              $element.fadeIn(100);
            }
            else if (annotation.trim() !== "") {
              $scope.selection_text = angular.copy(annotation);
              $scope.level = "New Ngram from selection";
              $scope.category = null;
              $scope.local_miamlist = true;
              $scope.local_stoplist = true;
              $scope.global_stoplist = true;
              // show menu
              $element.fadeIn(100);
            } else {
              // close menu
              $element.fadeOut(100);
            }
          });
        });
      }
      var elt = $(".text-panel")[0];
      var pos = $(".text-panel").position();

      function positionElement(context, x, y) {
        // todo try bootstrap popover component
        $element.css('left', x + 10);
        $element.css('top', y + 10);
      }

      function positionMenu(e) {
        positionElement(null, e.pageX, e.pageY);
      }

      // TODO is mousedown necessary ?
      $(".text-panel").mousedown(function(){
        $(".text-panel").mousemove(positionMenu);
      });

      $(".text-panel").mouseup(function(){
        $(".text-panel").unbind("mousemove", positionMenu);
        toggleSelectionHighlight(selection.toString().trim());
        toggleMenu(null, selection.toString().trim());
      });

      $(".text-panel").delegate(':not("#selection")', "click", function(e) {
        if ($(e.target).hasClass("keyword-inline")) return;
        positionMenu(e);
        toggleSelectionHighlight(selection.toString().trim());
        toggleMenu(null, selection.toString().trim());
      });

      $rootScope.$on("positionAnnotationMenu", positionElement);
      $rootScope.$on("toggleAnnotationMenu", toggleMenu);

      $scope.onClick = function($event, action, listId, level) {
        if (angular.isObject($scope.selection_text)) {
          // delete from the current list
          NgramHttpService[action]({
              'listId': listId,
              'ngramId': $scope.selection_text.uuid
            }).$promise.then(function(data) {
              // push to $rootScope.annotations
              if (data && data.uuid && data.text && data.list_id) {
                // new annotation is returned and added to the $rootScope
                $rootScope.annotations.push(data);
              } else {
                // refresh all annotations
                NgramListHttpService.get(
                  {'corpusId': $rootScope.corpusId, 'docId': $rootScope.docId}
                ).$promise.then(function(data) {
                  $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
                  $rootScope.lists = data[$rootScope.corpusId.toString()]['lists'];
                });
              }
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
        // hide selection highlighted text and the menu
        $(".text-panel").removeClass("selection");
        $element.fadeOut(100);
      };
    }
  ]);

  window.annotationsApp.controller('IntraTextController',
    ['$scope', '$rootScope', '$compile', 'NgramHttpService',
    function ($scope, $rootScope, $compile, NgramHttpService) {

      $scope.extra_stoplist = [];
      $scope.extra_miamlist = [];
      $scope.currentStopPage = 0;
      $scope.currentMiamPage = 0;
      $scope.pageSize = 15;
      var counter = 0;

      /*
      * Replace the text by and html template
      */
      function replaceTextByTemplate(text, annotation, template, pattern, lists) {
        return text.replace(pattern, function(matched) {
          var tpl = angular.element(template);
          tpl.append(matched);
          tpl.attr('title', annotation.tooltip_content);
          tpl.attr('uuid', annotation.uuid);

          if ('MiamList' == lists[annotation.list_id]) tpl.addClass("miamword");
          if ('StopList' == lists[annotation.list_id]) tpl.addClass("stopword");
          //if (annotation.category == 'stoplist' && annotation.level == 'global') tpl.addClass("global-stopword");

          return tpl.get(0).outerHTML;
        });
      }

      function compileText(annotations, fullText, abstractText, $rootScope) {
        counter = 0;
        var templateBegin = "<span ng-controller='AnnotationController' ng-click='onClick($event)' class='keyword-inline'>";
        var templateBeginRegexp = "<span ng-controller='AnnotationController' ng-click='onClick\(\$event\)' class='keyword-inline'>";

        var templateEnd = "</span>";
        var template = templateBegin + templateEnd;

        var startPattern = "\\b((?:"+templateBeginRegexp+")*";
        var middlePattern = "(?:<\/span>)*\\s(?:"+templateBeginRegexp+")*";
        var endPattern = "(?:<\/span>)*)\\b";
        /*
         * Sorts annotations on the number of words
         */
        function lengthSort(listitems, valuekey) {
            listitems.sort(function(a, b) {
                var compA = a[valuekey].split(" ").length;
                var compB = b[valuekey].split(" ").length;
                return (compA > compB) ? -1 : (compA <= compB) ? 1 : 0;
            });
            return listitems;
        }

        var sortedSizeAnnotations = lengthSort(annotations, "text");
        var extra_stoplist = [],
            extra_miamlist = [];

        _.each(sortedSizeAnnotations, function (annotation) {
          // TODO better split to manage two-words with minus sign
          annotation.category = $rootScope.lists[annotation.list_id].toLowerCase();
          var words = annotation.text.split(" ");
          var pattern = new RegExp(startPattern + words.join(middlePattern) + endPattern, 'gmi');
          var textRegexp = new RegExp("\\b"+annotation.text+"\\b", 'igm');

          if (pattern.test(fullText) === true) {
            fullText = replaceTextByTemplate(fullText, annotation, template, pattern, $rootScope.lists);
            // TODO remove debug
            counter++;
          } else if (pattern.test(abstractText) === true) {
            abstractText = replaceTextByTemplate(abstractText, annotation, template, pattern, $rootScope.lists);
            counter++;
          } else if (!textRegexp.test($rootScope.full_text) && !textRegexp.test($rootScope.abstract_text)) {
            if (annotation.category == "stoplist") {
              // Deactivated stoplist for the moment
              // if ($.inArray(annotation.uuid, $scope.extra_stoplist.map(function (item) {
              //      return item.uuid;
              //    })) == -1) {
              //   extra_stoplist = lengthSort(extra_stoplist.concat(annotation), "text");
              // }
            } else if (annotation.category == "miamlist") {
              if ($.inArray(annotation.uuid, $scope.extra_miamlist.map(function (item) {
                  return item.uuid;
                })) == -1) {
                extra_miamlist = lengthSort(extra_miamlist.concat(annotation), "text");
              }
            }
          }
        });
        $scope.extra_stoplist = extra_stoplist;
        $scope.extra_miamlist = extra_miamlist;

        return {
          'fullTextHtml': fullText,
          'abstractTextHtml': abstractText
        };
      }

      $rootScope.$watchCollection('annotations', function (newValue, oldValue) {
        if ($rootScope.annotations === undefined) return;
        if (angular.equals(newValue, oldValue)) return;

        $rootScope.miamListId = _.invert($rootScope.lists)['MiamList'];
        $rootScope.stopListId = _.invert($rootScope.lists)['StopList'];

        $scope.extra_stoplist = [];
        $scope.extra_miamlist = [];

        var result = compileText(
          $rootScope.annotations,
          angular.copy($rootScope.full_text),
          angular.copy($rootScope.abstract_text),
          $rootScope
        );

        console.log($rootScope.annotations.length);
        console.log(counter);

        angular.element('#full-text').html(result.fullTextHtml);
        angular.element('#abstract-text').html(result.abstractTextHtml);

        angular.element('.text-container').find('[ng-controller=AnnotationController]').each(function(idx, elt) {
          angular.element(elt).replaceWith($compile(elt)($rootScope.$new(true)));
        });
      });

      function submitNewAnnotation($event, inputEltId, listId) {
        if ($event.keyCode !== undefined && $event.keyCode != 13) return;
        var value = $(inputEltId).val().trim();
        if (value === "") return;

        NgramHttpService.post(
          {
            'listId': listId,
            'ngramId': 'new'
          },
          {'annotation' : {'text': value}},
          function(data) {
            // on success
            if (data) {
              $rootScope.annotations.push(data);
            }
        });

        $(inputEltId).val("");
      }

      $scope.onMiamlistSubmit = function ($event) {
        submitNewAnnotation($event, "#miamlist-input", _.invert($rootScope.lists)['MiamList']);
      };
      // TODO refactor
      $scope.onStoplistSubmit = function ($event) {
        submitNewAnnotation($event, "#stoplist-input", _.invert($rootScope.lists)['MiamList']);
      };
      $scope.numStopPages = function () {
        if ($scope.extra_stoplist === undefined) return 0;
        return Math.ceil($scope.extra_stoplist.length / $scope.pageSize);
      };
      $scope.numMiamPages = function () {
        if ($scope.extra_miamlist === undefined) return 0;
        return Math.ceil($scope.extra_miamlist.length / $scope.pageSize);
      };
      $scope.nextMiamPage = function() {
        $scope.currentMiamPage = $scope.currentMiamPage + 1;
      };
      $scope.previousMiamPage = function() {
        $scope.currentMiamPage = $scope.currentMiamPage - 1;
      };
      $scope.nextStopPage = function() {
        $scope.currentStopPage = $scope.currentStopPage + 1;
      };
      $scope.previousStopPage = function() {
        $scope.currentStopPage = $scope.currentStopPage - 1;
      };
    }
  ]);

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
          $scope.title = data.title;
          $scope.authors = data.authors;
          $scope.journal = data.journal;
          $scope.publication_date = data.publication_date;
          // TODO this data have to be deleted
          //$scope.current_page_number = data.current_page_number;
          //$scope.last_page_number = data.last_page_number;
          // put in rootScope because used by many components
          $rootScope.docId = data.id;
          $rootScope.full_text = data.full_text;
          $rootScope.abstract_text = data.abstract_text;
          // GET the annotations
          // TODO
          $rootScope.annotationsResource = NgramListHttpService.get(
            {'corpusId': $rootScope.corpusId, 'docId': $rootScope.docId}
          ).$promise.then(function(data) {
            $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
            $rootScope.lists = data[$rootScope.corpusId.toString()]['lists'];
          });
      });

    // TODO setup pagination client-side
    $scope.onPreviousClick = function () {
      DocumentHttpService.get($scope.docId - 1);
    };
    $scope.onNextClick = function () {
      DocumentHttpService.get($scope.docId + 1);
    };
  }]);

  window.annotationsApp.run(function ($rootScope) {
    /* GET the document node and all the annotations in the list associated */
    var path = window.location.pathname.match(/\/project\/(.*)\/corpus\/(.*)\/document\/(.*)\//);
    $rootScope.projectId = path[1];
    $rootScope.corpusId = path[2];
    $rootScope.docId = path[3];
  });

})(window);
