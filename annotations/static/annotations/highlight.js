(function () {
  'use strict';

  var annotationsAppHighlight = angular.module('annotationsAppHighlight', ['annotationsAppHttp', 'annotationsAppUtils']);

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
    ['$scope', '$rootScope', '$element', '$timeout', 'MainApiChangeNgramHttpService', 'NgramListHttpService',
    function ($scope, $rootScope, $element, $timeout, MainApiChangeNgramHttpService, NgramListHttpService) {
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
      * (actions are then interpreted in onMenuClick)
      */
      function toggleMenu(context, annotation) {
        $timeout(function() {
          $scope.$apply(function() {
            var mainlist_id = $rootScope.listIds.MAINLIST;
            var stoplist_id = $rootScope.listIds.STOPLIST;
            var maplist_id = $rootScope.listIds.MAPLIST;

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

              // Context menu proposes 2 things for each item of list A
              //      - adding/moving to other lists B or C

              // ---------------------------------------------------------------
              // Because of logical dependencies b/w lists, user choices are "intentions"
              // the real CRUDs actions are deduced from intentions as a list...
              // * (see forge.iscpif.fr/projects/garg/wiki/Ngram_Lists)
              // * (see also InferCRUDFlags in lib/NGrams_dyna_chart_and_table)
              // ---------------------------------------------------------------

              // TODO  disambiguate annotation.list_id for highlighted MapList items
              //       -------------------------------------------------------------
              //       Because MapList annotations are also MiamList,
              //       we should ensure that list_id is indeed "MapList"
              //       (ie that it was added last in CompileNgramsHtml)
              //       otherwise the "if" here will propose MiamList's options

              if ($rootScope.lists[annotation.list_id] == "MAPLIST") {
                $scope.menuItems.push({
                    // "tgtListName" is just used to render the GUI explanation
                    'tgtListName': 'STOPLIST',
                    // crudActions is an array of rest/DB actions
                    // (consequences of the intention)
                    'crudActions':[
                                ["delete", maplist_id],
                                ["delete", mainlist_id],
                                ["put",   stoplist_id]
                    ]
                  });
                $scope.menuItems.push({
                    'tgtListName': 'MAINLIST',
                    'crudActions':[
                                ["delete", maplist_id]
                            ]
                  });
              }

              else if ($rootScope.lists[annotation.list_id] == "MAINLIST") {
                $scope.menuItems.push({
                    'tgtListName': "STOPLIST",
                    'crudActions':[
                                ["delete", mainlist_id],
                                ["put",   stoplist_id]
                    ]
                  });
                $scope.menuItems.push({
                    'tgtListName': "MAPLIST",
                    'crudActions':[
                                ["put",   maplist_id]
                    ]
                });
              }

              else if ($rootScope.lists[annotation.list_id] == "STOPLIST") {
                $scope.menuItems.push({
                    'tgtListName': "MAINLIST",
                    'crudActions':[
                                ["delete", stoplist_id],
                                ["put",   mainlist_id]
                    ]
                });
                $scope.menuItems.push({
                    'tgtListName': "MAPLIST",
                    'crudActions':[
                                ["delete", stoplist_id],
                                ["put",   mainlist_id],
                                ["put",    maplist_id]
                    ]
                });
              }

              // show the menu
              $element.fadeIn(100);
              $element.addClass('menu-is-opened');
            }

            // -------8<------ "add" actions for non-existing ngram ------
            // else if (annotation.trim() !== "" && !$element.hasClass('menu-is-opened')) {
            //   // new ngram
            //   $scope.menuItems = [
            //     {
            //       'action': 'post',
            //       'listId': miamlist_id,
            //       'verb': 'Add to',
            //       'listName': $rootScope.lists[miamlist_id]
            //     }
            //   ];
            //   // show the menu
            //   $element.fadeIn(100);
            //   $element.addClass('menu-is-opened');
            // }
            // -------8<--------------------------------------------------
            else {
              $scope.menuItems = [];
              // close the menu
              $element.fadeOut(100);
              $element.removeClass('menu-is-opened');
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
      * Menu click actions
      * (1 intention => list of actions => MainApiChangeNgramHttpService CRUDs)
      *                  post/delete
      */
      $scope.onMenuClick = function($event, crudActions) {
          console.warn('in onMenuClick')
          console.warn('item.crudActions')
          console.warn(crudActions)

        if (angular.isObject($scope.selection_text)) {

            var ngramId = $scope.selection_text.uuid
            var ngramText = $scope.selection_text.text

            var lastCallback = function() {
                // Refresh the annotationss
                NgramListHttpService.get(
                  {'corpusId': $rootScope.corpusId,
                    'docId': $rootScope.docId},
                  function(data) {
                    $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
                    $rootScope.refreshDisplay();
                  },
                  function(data) {
                    console.error("unable to get the list of ngrams");
                  }
                );
            }

            // chained recursion to do several actions then callback (eg refresh)
            function makeChainedCalls (i, listOfActions, finalCallback) {
              // each action couple has 2 elts
              var action = listOfActions[i][0]
              var listId = listOfActions[i][1]

              console.log("===>"+action+"<===")

              MainApiChangeNgramHttpService[action](
                      {'listId': listId,
                       'ngramIdList': ngramId},

                       // on success
                       function(data) {
                          // case NEXT
                          //      ----
                          // when chained actions
                          if (listOfActions.length > i+1) {
                              console.log("calling next action ("+(i+1)+")")

                              // ==============================================
                              makeChainedCalls(i+1, listOfActions, finalCallback)
                              // ==============================================

                          }
                          // case LAST
                          //     ------
                          // when last action
                          else {
                              finalCallback()
                          }
                      },
                      // on error
                      function(data) {
                        console.error("unable to edit the Ngram \""+ngramText+"\""
                                     +"(ngramId "+ngramId+")"+"at crud no "+i
                                     +" ("+action+" on list "+listId+")");
                      }
              );
            }

            // run the loop by calling the initial recursion step
            makeChainedCalls(0, crudActions, lastCallback)
        }

        // TODO: first action creates then like previous case

        // else if ($scope.selection_text.trim() !== "") {
        //   // new annotation from selection
        //   NgramHttpService.post(
        //     {
        //       'listId': listId,
        //       'ngramId': 'create'
        //     },
        //     {
        //       'text': $scope.selection_text.trim()
        //     }, function(data) {
        //       // Refresh the annotationss
        //       NgramListHttpService.get(
        //         {
        //           'corpusId': $rootScope.corpusId,
        //           'docId': $rootScope.docId
        //         },
        //         function(data) {
        //           $rootScope.annotations = data[$rootScope.corpusId.toString()][$rootScope.docId.toString()];
        //           $rootScope.refreshDisplay();
        //         },
        //         function(data) {
        //           console.error("unable to get the list of ngrams");
        //         }
        //       );
        //     }, function(data) {
        //       console.error("unable to edit the Ngram " + $scope.selection_text);
        //     }
        //   );
        // }

        // hide the highlighted text and the menu element
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
        // ngram  ----- {uuid: 1846, occs: 1, list_id: 3689,
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

        // hash of flags filled in first pass loop : (== did annotation i match ?)
        var isDisplayedIntraText = {};

        console.log("highlight annotations length: " + annotations.length)

        var sortedSizeAnnotations = lengthSort(annotations, "text")

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

                      // remember that this annotation.text matched
                      isDisplayedIntraText[annotation.uuid] = annotation
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
          angular.forEach(textMapping, function(textContent, eltId) {
            //   console.log(anchorPattern)
            if(textContent) {
              textMapping[eltId] = replaceAnchorByTemplate(
                  textContent,
                  annotation,
                  template,
                  anchorPattern);
            }
          });
        });

        // let's show just the ngrams that matched
        //        in the left side
        var sortedDisplayedKeys = Object.keys(isDisplayedIntraText).sort()
                                                        // sorts on ngram_id

        // new update ngramsInPanel
        angular.forEach(sortedDisplayedKeys, function(id) {
          var the_annot = isDisplayedIntraText[id] ;
          var the_list_id = the_annot.list_id ;
          $rootScope.ngramsInPanel[the_list_id].push(the_annot)
        });

        // debug
        //console.warn("$rootScope.ngramsInPanel :")
        //console.warn($rootScope.ngramsInPanel)

        // return the object of element ID with the corresponding HTML
        return textMapping;
      }


      /*
      * main refresh
      */
      $rootScope.refreshDisplay = function() {
        console.log("annotations.highlight.refreshDisplay()")
        if ($rootScope.annotations === undefined) return;
        if ($rootScope.activeLists === undefined) return;
        if (_.keys($rootScope.activeLists).length === 0) return;

        // initialize ngramsInPanel
        // ------------------------
        //  $rootScope.ngramsInPanel = {
        //    activelist1_id : [
        //            annotation_a,
        //            annotation_b,
        //            annotation_c
        //    ] ,
        //    activelist2_id : [
        //            annotation_x,
        //            annotation_y,
        //            annotation_z
        //    ] ,
        //      ....
        //    }
        //
        var ngramsInPanel = {};
        $rootScope.ngramsInPanel = angular.forEach($rootScope.activeLists, function(name, list_id) {
          this[list_id] = [];
        }, ngramsInPanel);
        $rootScope.ngramsInPanel = ngramsInPanel;

        /*
        * Transform text into HTML with higlighted ngrams via compileNgramsHtml
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
