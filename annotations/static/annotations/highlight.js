(function () {
  'use strict';

  var annotationsAppHighlight = angular.module('annotationsAppHighlight', ['annotationsAppHttp']);

  /*
  * Controls the mouse selection on the text
  */
  annotationsAppHighlight.controller('TextSelectionController',
    ['$scope', '$rootScope', '$element',
      function ($scope, $rootScope, $element) {

      // dbg: apparently no data sent throught local scope, just using $element[0] attribute uuid to attach
      // console.log('TextSelectionController $scope.$id: ' + $scope.$id)
      // grand parent should be the rootscope
      //console.log($scope.$parent.$parent.$id)


      // (prepared once, after highlight)
      // (then used when onClick event)
      // retrieve corresponding ngram using element attr uuid in <span uuid="42">
      // FIXME maybe use angular.copy of the annotation
      var keyword = _.find(
        $rootScope.annotations,
        function(annotation) { return annotation.uuid.toString() === $element[0].getAttribute('uuid').toString(); }
      );

      // attach the annotation scope dynamically
      if (keyword) {
        // console.log('TextSelectionController found highlighted keyword annotation: ' + keyword.text)
        keyword.romdebuginfo = "source = TextSelectionController" ;
        $scope.keyword = keyword;
      }

      $scope.onClick = function(e) {
        $rootScope.$emit("positionAnnotationMenu", e.pageX, e.pageY);
        $rootScope.$emit("toggleAnnotationMenu", $scope.keyword);
        // $rootScope.$emit("toggleAnnotationMenu", {'uuid':42,'list_id':1,'text':'gotcha'});
        console.log("EMIT toggleAnnotationMenu with \$scope.keyword: '" + $scope.keyword.text +"'")
        e.stopPropagation();
      };
  }]);

  /*
  * Controls the menu over the current mouse selection
  */
  annotationsAppHighlight.controller('TextSelectionMenuController',
    ['$scope', '$rootScope', '$element', '$timeout', 'NgramHttpService', 'NgramListHttpService',
    function ($scope, $rootScope, $element, $timeout, NgramHttpService, NgramListHttpService) {
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
        if (text.trim() !== "" && !$element.hasClass('menu-is-opened')) {
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
	  // £TODO check
            var miamlist_id = _.invert($rootScope.lists).MAINLIST;
            var stoplist_id = _.invert($rootScope.lists).STOPLIST;
            var maplist_id = _.invert($rootScope.lists).MAPLIST;

            // if called from highlighted span
            //    - annotation has full {ngram}
            //    - context has properties:
            //        name,targetScope,currentScope, ...

            // if called from new selected text
            //    - annotation has just a string
            //    - context is null

            // variable used in onClick
            $scope.selection_text = angular.copy(annotation);

            // debug
            // console.log("toggleMenu with \$scope.selection_text: '" + JSON.stringify($scope.selection_text) +"'") ;
            if (angular.isObject(annotation) && !$element.hasClass('menu-is-opened')) {
              // existing ngram

              console.log("toggleMenu.annotation: '" + JSON.stringify(annotation) +"'")

              // Delete from the current list
              $scope.menuItems = [
                {
                  'action': 'delete',
                  'listId': annotation.list_id,
                  'verb': 'Delete from',
                  'listName': $rootScope.lists[annotation.list_id]
                }
              ];


              // Context menu proposes 3 things for each item of list A
              //      - deletion from A
              //      - adding/moving to other lists B or C
              // Because of logical dependencies b/w lists, these
              // menu actions will also trigger todo_other_actions
              // cf. forge.iscpif.fr/projects/garg/wiki/Ngram_Lists

              // TODO  disambiguate annotation.list_id for highlighted MapList items
              //       -------------------------------------------------------------
              //       Because MapList annotations are also MiamList,
              //       we should ensure that list_id is indeed "MapList"
              //       (ie that it was added last in CompileNgramsHtml)
              //       otherwise the "if" here will propose MiamList's options

              if ($rootScope.lists[annotation.list_id] == "MAPLIST") {
                // Add to the other lists
                $scope.menuItems.push({
                    'action': 'post',
                    'listId': stoplist_id,
                    'verb': 'Move to',
                    'listName': $rootScope.lists[stoplist_id]
                  });
              } else if ($rootScope.lists[annotation.list_id] == "STOPLIST") {
                // Add to the alternative list
                $scope.menuItems.push({
                    'action': 'post',
                    'listId': miamlist_id,
                    'verb': 'Move to',
                    'listName': $rootScope.lists[miamlist_id]
                  });
              }
              // show the menu
              $element.fadeIn(100);
              $element.addClass('menu-is-opened');
            } else if (annotation.trim() !== "" && !$element.hasClass('menu-is-opened')) {
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
              $element.addClass('menu-is-opened');
            } else {
              $scope.menuItems = [];
              // close the menu
              $element.fadeOut(100);
              $element.removeClass('menu-is-opened');
            }
          });
        });
      }











      // £TODO CHECK
                    // if ($rootScope.lists[annotation.list_id] == "MiamList") {
                    //   // Add to the other lists
                    //   $scope.menuItems.push({
                    //       'action': 'post',
                    //       'listId': maplist_id,
                    //       // "Add" because copy into MapList
                    //       'verb': 'Add to',
                    //       'listName': $rootScope.lists[maplist_id]
                    //     },
                    //     {
                    //       'action': 'post',
                    //       'listId': stoplist_id,
                    //       // "Move"
                    //       // £dbg: TODO for instance pass conditional dependancy as info
                    //       // 'todo_other_actions': 'remove from miam',
                    //       'verb': 'Move to',
                    //       'listName': $rootScope.lists[stoplist_id]
                    //     });
                    // } else if ($rootScope.lists[annotation.list_id] == "StopList") {
                    //   // Move from stop to the "positive" lists
                    //   $scope.menuItems.push({
                    //       'action': 'post',
                    //       'listId': miamlist_id,
                    //       // 'todo_other_actions': 'remove from stop',
                    //       'verb': 'Move to',
                    //       'listName': $rootScope.lists[miamlist_id]
                    //     },
                    //     {
                    //       'action': 'post',
                    //       'listId': maplist_id,
                    //       // 'todo_other_actions': 'remove from stop, add to miam',
                    //       'verb': 'Move to',
                    //       'listName': $rootScope.lists[maplist_id]
                    //     });
                    // } else if ($rootScope.lists[annotation.list_id] == "MapList") {
                    //   // No need to add to miam, just possible to move to stop
                    //   $scope.menuItems.push({
                    //       'action': 'post',
                    //       'listId': stoplist_id,
                    //       // 'todo_other_actions': 'remove from miam and from map'
                    //       'verb': 'Move to',
                    //       'listName': $rootScope.lists[stoplist_id]
                    //     });
                    // }
                    //
                    //
                    //
















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
      *
      *  £TODO test: apparently this is never used ?
      *  (superseded by TextSelectionController.onClick)
      */
      $(".text-container").delegate(':not("#selection")', "click", function(e) {
        // if ($(e.target).hasClass("keyword-inline")) return;
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

        // TODO interpret context menu chosen actions
        //      as implicit API+DB actions
        //      ex: add to map (+ add to miam + delete from stop)

        if (angular.isObject($scope.selection_text)) {
          console.log("requested action: " + action + "on scope.sel: '" + $scope.selection_text + "'")

          // action on an existing Ngram
          NgramHttpService[action]({
              'listId': listId,
              'ngramId': $scope.selection_text.uuid
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
                  console.error("unable to get the list of ngrams");
                }
              );
            }, function(data) {
              console.error("unable to edit the Ngram " + $scope.selection_text.text);
            }
          );

        } else if ($scope.selection_text.trim() !== "") {
          // new annotation from selection
          NgramHttpService.post(
            {
              'listId': listId,
              'ngramId': 'create'
            },
            {
              'text': $scope.selection_text.trim()
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
                  console.error("unable to get the list of ngrams");
                }
              );
            }, function(data) {
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
    ['$scope', '$rootScope', '$compile',
    function ($scope, $rootScope, $compile) {

      /*
      * Replace the any ad hoc anchor by an html template
      */
      function replaceAnchorByTemplate(text, ngram, template, pattern) {

        // exemple args:
        // =============
        // text ------- "Background Few previous studies have examined
        //               non-wealth-based inequalities etc etc etc"
        // ngram  ----- {uuid: 1846, occurrences: 1, list_id: 3689,
        //               text: "previous studies", listName: "MAINLIST"}
        // template --- "<span ng-controller='TextSelectionController'
        //                     ng-click='onClick($event)'
        //                     class='keyword-inline'></span>"
        // pattern ---- RegExp(/#\(#MAINLIST-10007#\)#/gm)

        return text.replace(pattern, function(matched) {
          var tpl = angular.element(template);
          tpl.append(ngram.text);
          tpl.attr('title', "Click to add/remove");
          tpl.attr('uuid', ngram.uuid);
          /*
          * Add CSS class depending on the list the ngram is into
          */
          tpl.addClass(ngram.listName);
          return tpl.get(0).outerHTML;
        });
      }


      /* Escape text before it's inserted in regexp (aka quotemeta)
       * ex: "c++"  => "c\+\+"
       *     so the '+' won't act as regexp operator
       */
      function escapeRegExp(string){
        return string.replace(/([.*+?^${}()|\[\]\/\\])/g, "\\$1");
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
        var templateBegin = "<span ng-controller='TextSelectionController' ng-click='onClick($event)' class='keyword-inline'>";
        var templateEnd = "</span>";
        var template = templateBegin + templateEnd;
        var templateBeginRegexp = "<span ng-controller='TextSelectionController' ng-click='onClick\(\$event\)' class='keyword-inline'>";

        var startPattern = "\\b((?:"+templateBeginRegexp+")*";
        var middlePattern = "(?:<\/span>)*\\s(?:"+templateBeginRegexp+")*";
        var middlePattern = " ";
        var endPattern = "(?:<\/span>)*)\\b";

        console.log("highlight annotations length: " + annotations.length)

        var sortedSizeAnnotations = lengthSort(annotations, "text"),
            extraNgramList = angular.copy($rootScope.extraNgramList);

        // reinitialize an empty list
        extraNgramList = angular.forEach(extraNgramList, function(name, id) {
          extraNgramList[id] = [];
        });

        // rl: £dbg counters
        var i = 0 ;
        var j = 0 ;
        var k = 0 ;
        var l = 0 ;

        // first pass for anchors
        // ======================
        angular.forEach(sortedSizeAnnotations, function (annotation) {
          // ex annotation  --- {uuid: 1846, occurrences: 1, list_id: 3689,
          //                     text: "previous studies", listName: "MAINLIST"}
          i ++ ;
          // console.log('----------------\n')
          // console.log('sortedSizeAnnotations n° ' + i + ': \n  ' + JSON.stringify(annotation) +'\n')

          // exclude ngrams that are into inactive lists
          if ($rootScope.activeLists[annotation.list_id] === undefined) return;

          // count within activ list
          j ++ ;

          // used to setup anchor
          annotation.listName = $rootScope.lists[annotation.list_id];

          // used as unique placeholder for str.replace
          //        (anchor avoids side effects of multiple replacements
          //         like new results inside old replacement's result)
          var myAnchor = '#(#'+annotation.listName+'-'+annotation.uuid+'#)#' ;

          // £WIP simpler text regexp
          // regexps (with escaped content)
          //  var myPattern = new RegExp("\\b"+escapeRegExp(annotation.text)+"\\b", 'igm');
          // previously:
              var words = annotation.text.split(" ").map(escapeRegExp);
              var myPattern = new RegExp(startPattern + words.join(middlePattern) + endPattern, 'gmi');


          // -------------------------------------------
          // replace in text: matched annots by anchors
          // -------------------------------------------
          // text content taken in argument textMapping:
          //     eltID           eltLongtext
          //       |                  |
          //  {'#title':         'some text',
          //   '#abstract-text': 'some text',
          //   '#full-text':     'some text' }
          //
          angular.forEach(textMapping, function(eltLongtext, eltId) {
              if(eltLongtext) {
                  // ------------------------------------------------------------
                  // £dbgcount here unnecessary nbMatches (can go straight to ICI)
                  var matches = eltLongtext.match(myPattern)
                  var nbMatches = matches ? eltLongtext.match(myPattern).length : 0
                  if (nbMatches > 0) {
                      k += nbMatches ;
                      l ++ ;
                  // ------------------------------------------------------------
                      // ICI we update each time
                      textMapping[eltId] = eltLongtext.replace(myPattern, myAnchor);

                      // ex longtext -- "Background Few previous studies have
                      //                 examined non-wealth-based inequalities etc"

                      // ex result ---- "Background Few #(#MAINLIST-1846#)# have
                      //                 examined non-wealth-based inequalities etc"
                  }
              }
          });
        });
        // rl: £dbgcount
        console.log('---- compileNgramsHtml created '
                     + k + ' anchors ('
                     + l + ' distinct ngrams) from '
                     + j + ' ngrams in activeLists (of ' + i + ' ngrams total) ----\n')



        // 2nd pass for result html
        // =========================

        // first pass for anchors
        // ======================
        angular.forEach(sortedSizeAnnotations, function (annotation) {
          // again exclude ngrams that are into inactive lists
          if ($rootScope.activeLists[annotation.list_id] === undefined) return;

          // now used to setup css class
          annotation.listName = $rootScope.lists[annotation.list_id];

          // used as unique placeholder for str.replace
          //        (anchor avoids side effects of multiple replacements
          //         like new results inside old replacement's result)
          var myAnchor = '#(#'+annotation.listName+'-'+annotation.uuid+'#)#' ;

          var anchorPattern = new RegExp(escapeRegExp(myAnchor), 'gm');

          // highlight anchors as html spans
          // -------------------------------
          angular.forEach(textMapping, function(text, eltId) {
            //   console.log(anchorPattern)
            if(text) {
              textMapping[eltId] = replaceAnchorByTemplate(
                  text,
                  annotation,
                  template,
                  anchorPattern);
            }
          });

          // rloth: for now let's show *all* ngrams of the active list
          //        in the left side
          extraNgramList[annotation.list_id] = extraNgramList[annotation.list_id].concat(annotation);
        });





































        // update extraNgramList
        $rootScope.extraNgramList = angular.forEach(extraNgramList, function(name, id) {
          extraNgramList[id] = lengthSort(extraNgramList[id], 'text');
        });
        // return the object of element ID with the corresponding HTML
        return textMapping;
      }

      $rootScope.refreshDisplay = function() {
        console.log("annotations.highlight.refreshDisplay()")
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
      $rootScope.$watchCollection('activeLists', function (newValue, oldValue) {
        $rootScope.refreshDisplay();
      });


    }
  ]);
})(window);
