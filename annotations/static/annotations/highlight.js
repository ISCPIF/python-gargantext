(function () {
  'use strict';

  var annotationsAppHighlight = angular.module('annotationsAppHighlight', ['annotationsAppHttp']);

  /*
  * Controls the mouse selection on the text
  */
  annotationsAppHighlight.controller('TextSelectionController',
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
  * Controls the menu over the current mouse selection
  */
  annotationsAppHighlight.controller('TextSelectionMenuController',
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
            var miamlist_id = _.invert($rootScope.lists).MiamList;
            var stoplist_id = _.invert($rootScope.lists).StopList;
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
                  'listName': $rootScope.lists[miamlist_id]
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
          // action on an existing Ngram
          NgramHttpService[action]({
              'listId': listId,
              'ngramId': $scope.selection_text.uuid
            }, function(data) {
              $.each($rootScope.annotations, function(index, element) {
                if (element.list_id == listId && element.uuid == $scope.selection_text.uuid) {
                  $rootScope.annotations.splice(index, 1);
                  return false;
                }
              });
            }, function(data) {
              console.log(data);
              console.error("unable to edit the Ngram " + $scope.selection_text);
            }
          );

        } else if ($scope.selection_text.trim() !== "") {
          // new annotation from selection
          NgramHttpService.post(
            {
              'listId': listId,
              'ngramId': 'new'
            },
            {
              'annotation' : {'text': $scope.selection_text.trim()}
            }, function(data) {
              $rootScope.annotations.push(data);
            }, function(data) {
              console.log(data);
              console.error("unable to edit the Ngram " + $scope.selection_text);
            }
          );
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
  annotationsAppHighlight.controller('NGramHighlightController',
    ['$scope', '$rootScope', '$compile', 'NgramHttpService',
    function ($scope, $rootScope, $compile, NgramHttpService) {
      var counter = 0;
      /*
      * Replace the text by an html template for ngram keywords
      */
      function replaceTextByTemplate(text, ngram, template, pattern) {
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
        if ($rootScope.activeLists === undefined) return;
        if (_.keys($rootScope.activeLists).length === 0) return;

        // TODO remove this debug counter
        counter = 0;
        var templateBegin = "<span ng-controller='TextSelectionController' ng-click='onClick($event)' class='keyword-inline'>";
        var templateBeginRegexp = "<span ng-controller='TextSelectionController' ng-click='onClick\(\$event\)' class='keyword-inline'>";

        var templateEnd = "</span>";
        var template = templateBegin + templateEnd;

        var startPattern = "\\b((?:"+templateBeginRegexp+")*";
        var middlePattern = "(?:<\/span>)*\\s(?:"+templateBeginRegexp+")*";
        var endPattern = "(?:<\/span>)*)\\b";

        var sortedSizeAnnotations = lengthSort(annotations, "text"),
            extraNgramList = angular.copy($rootScope.extraNgramList);

        // reinitialize an empty list
        extraNgramList = angular.forEach(extraNgramList, function(name, id) {
          extraNgramList[id] = [];
        });

        angular.forEach(sortedSizeAnnotations, function (annotation) {
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
              textMapping[eltId] = replaceTextByTemplate(text, annotation, template, pattern);
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
              extraNgramList[annotation.list_id] = extraNgramList[annotation.list_id].concat(annotation);
            }
          }
        });
        // update extraNgramList
        $rootScope.extraNgramList = angular.forEach(extraNgramList, function(name, id) {
          extraNgramList[id] = lengthSort(extraNgramList[id], 'text');
        });
        // return the object of element ID with the corresponding HTML
        return textMapping;
      }

      function refreshDisplay() {
        if ($rootScope.annotations === undefined) return;
        if ($rootScope.activeLists === undefined) return;
        if (_.keys($rootScope.activeLists).length === 0) return;

        // initialize extraNgramList
        var extraNgramList = {};
        $rootScope.extraNgramList = angular.forEach($rootScope.activeLists, function(name, id) {
          this[id] = [];
        }, extraNgramList);
        $rootScope.extraNgramList = extraNgramList;

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
        angular.element('.text-container').find('[ng-controller=TextSelectionController]').each(function(idx, elt) {
          angular.element(elt).replaceWith($compile(elt)($rootScope.$new(true)));
        });
      }
      /*
      * Listen changes on the ngram data
      */
      // $rootScope.$watchCollection('annotations', function (newValue, oldValue) {
      //   refreshDisplay();
      // });
      $rootScope.$watchCollection('activeLists', function (newValue, oldValue) {
        refreshDisplay();
      });
      /*
      * Add a new NGram from the user input in the extra-text list
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
            }
          }, function(data) {
            // on error
            $(inputEltId).parent().addClass("has-error");
            console.error("error adding Ngram "+ value);
          }
        );
      };

    }
  ]);
})(window);
