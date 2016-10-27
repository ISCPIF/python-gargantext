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
        // keyword.romdebuginfo = "source = TextSelectionController" ;
        $scope.keyword = keyword;
      }

      // this onClick only works for existing annotations
      $scope.onClick = function(e) {
        $rootScope.$emit("toggleAnnotationMenu", $scope.keyword);
        $rootScope.$emit("positionAnnotationMenu", e.pageX, e.pageY);
        // $rootScope.$emit("toggleAnnotationMenu", {'uuid':42,'list_id':1,'text':'gotcha'});
        // console.log("EMIT toggleAnnotationMenu with \$scope.keyword: '" + $scope.keyword.text +"'")
        e.stopPropagation();
      };
  }]);

  /*
  * Controls the menu over the current mouse selection
  */
  annotationsAppHighlight.controller('TextSelectionMenuController',
    ['$scope', '$rootScope', '$element', '$timeout', 'MainApiChangeNgramHttpService', 'MainApiAddNgramHttpService', 'NgramListHttpService',
    function ($scope, $rootScope, $element, $timeout, MainApiChangeNgramHttpService, MainApiAddNgramHttpService, NgramListHttpService) {

      /*
      * Universal text selection
      *
      * "universal" <=> (Chrome, Firefox, IE, Safari, Opera...)
      *                 cf. quirksmode.org/dom/range_intro.html
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

      // £TODO extend "double click selection" on hyphen words
      //       and reduce it on apostrophe ones (except firefox)
      //       cf. stackoverflow.com/a/39005881/2489184
      //           jsfiddle.net/avvhsruu/

      // we only need one singleton at a time
      // (<=> is only created once per doc, but value of annotation changes)
      var selectionObj = getSelected();

      /*
      * Dynamically construct the selection menu scope
      * (actions are then interpreted in onMenuClick)
      */
      function toggleMenu(context, annotation) {
        $timeout(function() {
          $scope.$apply(function() {
            $scope.menuItems = []; // init empty menu

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
            // console.log("toggleMenu with context:", context) ;
            // console.log("toggleMenu with annotation: '" + JSON.stringify(annotation) +"'") ;
            // console.log("toggleMenu with \$scope.selection_text: '" + JSON.stringify($scope.selection_text) +"'") ;

            if (angular.isObject(annotation) && !$element.hasClass('menu-is-opened')) {
              // existing ngram
              var ngramId = annotation.uuid
              var mainformId = annotation.group

              var targetId = mainformId ? mainformId : ngramId

              // Context menu proposes 2 things for each item of list A
              //      - adding/moving to other lists B or C

              // ---------------------------------------------------------------
              // Because of logical dependencies b/w lists, user choices are "intentions"
              // the real CRUDs actions are deduced from intentions as a list...
              // * (see forge.iscpif.fr/projects/garg/wiki/Ngram_Lists)
              // * (see also InferCRUDFlags in lib/NGrams_dyna_chart_and_table)
              // ---------------------------------------------------------------

              // NB: remember that shown mainlist items are actually main 'without map'
              //     otherwise the menu for mainlist items can hide the menu for map items

              var sourceList = $rootScope.lists[annotation.list_id]

              if ( sourceList == "MAPLIST") {
                $scope.menuItems = [
                  {
                    // "tgtListName" is just used to render the GUI explanation
                    'tgtListName': 'STOPLIST',
                    // crudCalls is an array of rest/DB actions
                    // (consequences of the intention)
                    'crudCalls':[
                    {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                     'params' : {'listId':maplist_id, 'ngramIdList': targetId} },
                    {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                     'params' : {'listId':mainlist_id, 'ngramIdList': targetId} },
                    {'service': MainApiChangeNgramHttpService, 'action': 'put',
                     'params' : {'listId':stoplist_id, 'ngramIdList': targetId} }
                    ]
                  },
                  {
                    'tgtListName': 'MAINLIST',
                    'crudCalls':[
                    {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                     'params' : {'listId':maplist_id, 'ngramIdList': targetId} }
                    ]
                  }
                ];
              }

              else if (sourceList == "MAINLIST") {
                $scope.menuItems = [
                  {
                    'tgtListName': "STOPLIST",
                    'crudCalls':[
                    {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                     'params' : {'listId':mainlist_id, 'ngramIdList': targetId} },
                    {'service': MainApiChangeNgramHttpService, 'action': 'put',
                     'params' : {'listId':stoplist_id, 'ngramIdList': targetId} }
                    ]
                  },
                  {
                    'tgtListName': "MAPLIST",
                    'crudCalls':[
                    {'service': MainApiChangeNgramHttpService, 'action': 'put',
                     'params' : {'listId':maplist_id, 'ngramIdList': targetId} }
                    ]
                  }
                ];
              }

              else if (sourceList == "STOPLIST") {
                $scope.menuItems = [
                  {
                    'tgtListName': "MAINLIST",
                    'crudCalls':[
                    {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                     'params' : {'listId':stoplist_id, 'ngramIdList': targetId} },
                    {'service': MainApiChangeNgramHttpService, 'action': 'put',
                     'params' : {'listId':mainlist_id, 'ngramIdList': targetId} }
                    ]
                  },
                  {
                    'tgtListName': "MAPLIST",
                    'crudCalls':[
                    {'service': MainApiChangeNgramHttpService, 'action': 'delete',
                     'params' : {'listId':stoplist_id, 'ngramIdList': targetId} },
                    {'service': MainApiChangeNgramHttpService, 'action': 'put',
                     'params' : {'listId':mainlist_id, 'ngramIdList': targetId} },
                    {'service': MainApiChangeNgramHttpService, 'action': 'put',
                     'params' : {'listId':maplist_id, 'ngramIdList': targetId} }
                    ]
                  }
                ];
              }

              // show the menu
              $element.fadeIn(50);
              $element.addClass('menu-is-opened');
            }

            // "add" actions for non-existing ngram
            else if (annotation.trim() !== "" && ! context) {
              var newNgramText = annotation.trim()
              // new ngram (first call creates then like previous case for list)
              $scope.menuItems.push({
                      'comment'  : "Create and add to stop list",
                      'tgtListName': "STOPLIST",
                      'crudCalls':[
                      {'service': MainApiAddNgramHttpService, 'action': 'put',
                       'params' : {'ngramStr':newNgramText, corpusId: $rootScope.corpusId},
                       'dataPropertiesToCache': ['id', 'group'] },
                      {'service': MainApiChangeNgramHttpService, 'action': 'put',
                       'params' : {'listId':stoplist_id, 'ngramIdList': {'fromCacheIfElse': ['group','id']} } }
                      ]
                  }) ;
              $scope.menuItems.push({
                      'comment'  : "Create and add to candidate list",
                      'tgtListName': "MAINLIST",
                      'crudCalls':[
                      {'service': MainApiAddNgramHttpService, 'action': 'put',
                       'params' : {'ngramStr':newNgramText, corpusId: $rootScope.corpusId},
                       'dataPropertiesToCache': ['id', 'group'] },
                      {'service': MainApiChangeNgramHttpService, 'action': 'put',
                       'params' : {'listId':mainlist_id, 'ngramIdList': {'fromCacheIfElse': ['group','id']} } }
                      ]
                  }) ;
              $scope.menuItems.push({
                      'comment'  : "Create and add to map list",
                      'tgtListName': "MAPLIST",
                      'crudCalls':[
                      {'service': MainApiAddNgramHttpService, 'action': 'put',
                       'params' : {'ngramStr':newNgramText, corpusId: $rootScope.corpusId},
                       'dataPropertiesToCache': ['id', 'group'] },
                      {'service': MainApiChangeNgramHttpService, 'action': 'put',
                       'params' : {'listId':mainlist_id, 'ngramIdList': {'fromCacheIfElse': ['group','id']} } },
                      {'service': MainApiChangeNgramHttpService, 'action': 'put',
                       'params' : {'listId':maplist_id, 'ngramIdList': {'fromCacheIfElse': ['group','id']} } }
                      ]
                  }) ;

              // show the menu
              $element.fadeIn(50);
              $element.addClass('menu-is-opened');
              // console.warn("FADE IN menu", $element)
            }
            else {
              // console.warn("=> else")

              // close the menu
              $scope.menuItems = [];
              $element.fadeOut(50);
              $element.removeClass('menu-is-opened');
              // console.warn("FADE OUT menu", $element)
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
      * Toggle the menu when clicking on an existing ngram or a free selection
      */
      $(".text-container").mouseup(function(e){
        $(".text-container").unbind("mousemove", positionMenu);
        $rootScope.$emit("positionAnnotationMenu", e.pageX, e.pageY);

        positionMenu(e);
        // console.warn("calling toggleMenu from *mouseup*")
        toggleMenu(null, selectionObj.toString().trim());
      });

      $rootScope.$on("positionAnnotationMenu", positionElement);
      $rootScope.$on("toggleAnnotationMenu", toggleMenu);


      /*
      * Menu click actions
      * (1 intention => list of actions => MainApiChangeNgramHttpService CRUDs)
      *                  post/delete
      */
      $scope.onMenuClick = function($event, todoCrudCalls) {
        //   console.warn('in onMenuClick')
        //   console.warn('item.crudCalls', crudCalls)

        // run the loop by calling the initial recursion step
        $rootScope.makeChainedCalls(0,   todoCrudCalls,   $rootScope.refresh)
        // syntax: (step_to_run_first,   list_of_steps,     lastCallback)

        // hide the menu element
        $element.fadeOut(100);

        // the highlighted text hides itself when deselected
        // (thx to browser and css ::selection)
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
      function replaceAnchorByTemplate(text, ngram, template, pattern, cssclass) {

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
        // cssclass --- MAINLIST

        return text.replace(pattern, function(matched) {
          var tpl = angular.element(template);
          tpl.append(ngram.text);
          tpl.attr('title', "Click to add/remove");
          tpl.attr('uuid', ngram.uuid);
          /*
          * Add CSS class depending on the list the ngram is into
          */
          tpl.addClass(cssclass);
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
      * =====================================
      * main mechanism:
      * @param annotations is the list of ngrams with their info
      * @param textMapping is an object with text contents
      * @param $rootScope (global) to check activeLists and list names
      *
      * add-on mechanism:
      * @param focusNgrams: some ngram_ids to higlight more
      *        (it is assumed to be already in one of the active lists)
      */
      function compileNgramsHtml(annotations, textMapping, $rootScope, focusNgrams) {
        if (typeof $rootScope.activeLists == "undefined") return;
        if (_.keys($rootScope.activeLists).length === 0) return;
        var templateBegin = "<span ng-controller='TextSelectionController' ng-click='onClick($event)' class='keyword-inline'>";
        var templateEnd = "</span>";
        var template = templateBegin + templateEnd;
        var templateBeginRegexp = "<span ng-controller='TextSelectionController' ng-click='onClick\(\$event\)' class='keyword-inline'>";

        var startPattern = "(\\W|^)((?:"+templateBeginRegexp+")*";
        var middlePattern = "(?:<\/span>)*\\s(?:"+templateBeginRegexp+")*";
        var middlePattern = " ";
        var endPattern = "(?:<\/span>)*)(?=\\W|$)";

        // --------------------------------------------------------------------------------
        // Remarks about /\b/ and /(\W|^)/ and /(?=\W|$)/  etc.
        //
        // -----------------
        // 1) we need to match entire words only
        //
        //  ex: "the manifestation manifest".match(/manifest/g)
        //
        //      => not good because it would hilight the substr
        //         inside 2nd word "the manifestation manifest"
        //                              ^^^^^^^^      ^^^^^^^^
        //
        //   so in this situation one usually uses \b (boundary)
        //
        //  ex: "the manifestation manifest".match(/\bmanifest\b/g)
        //
        //       ok: now only 3rd word is highlighted:
        //               "the manifestation manifest"
        //                                  ^^^^^^^^
        // -----------------
        //
        // 2) but we can't really use boundary \b when we have accented chars
        // ex:
        //  no accent: "la moitié".match(/la/)         => ["la"]
        //             "la moitié".match(/\bla\b/)     => ["la"]
        //
        //  but      "la moitié".match(/moitié/)     => ["moitié"]
        //           "la moitié".match(/\bmoitié\b/) => []           <~~~ problem !
        //
        // cf. stackoverflow.com/questions/23458872/javascript-regex-word-boundary-b-issue
        //     stackoverflow.com/questions/2881445/utf-8-word-boundary-regex-in-javascript
        // -----------------
        //
        // 3) normally the typical replacement for \b would be:
        //      - at start of string: /(?<=\W|^)/  (lookbehind boundary)
        //      - at end  of string:  /(?=\W|$)/   (lookahead boundary)
        //
        //   ...
        //    but lookbehind not supported in js !! (sept 2016)
        //    cf. stackoverflow.com/questions/30118815
        // -----------------
        //
        // 4) so in conclusion we will use this strategy:
        //
        //      - at start of string:  /(\W|^)/        (boundary, may capture ' ' or '' into $1)
        //      - for the html+word:   /<aa>bla</aa>/  (same pattern as before)
        //      - at end  of string:   /(?=\W|$)/      (lookahead boundary)
        //      - in replacement:     $1+anchor
        //
        //  => This way if $1 was ' ' (or other non word char),
        //       then we re-add the char that we are replacing,
        //     and if $1 was '' (beginning of str)
        //       then we re-add nothing ;) )
        //
        // ex: "la moitié".replace(/(\s|^)moitié(?=\s|$)/, '$1hello') => "la hello"
        //     "moitié la".replace(/(\s|^)moitié(?=\s|$)/, '$1hello') => "hello la"
        // ---------------------------------------------------------------------------------

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
                      textMapping[eltId] = eltLongtext.replace(myPattern, "$1"+myAnchor);

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

        // a small lookup for possible focus items (they'll get different css)
        var checkFocusOn = {}
        if (focusNgrams) {
            for (var i in focusNgrams) {
                var focusNgramId = focusNgrams[i]
                checkFocusOn[focusNgramId] = true
            }
        }

        angular.forEach(sortedSizeAnnotations, function (annotation) {
          // again exclude ngrams that are into inactive lists
          if ($rootScope.activeLists[annotation.list_id] === undefined) return;

          // listName now used to setup css class
          var cssClass = $rootScope.lists[annotation.list_id];

          // except if uuid or group mainform is in FOCUS items
          if (focusNgrams &&
            (checkFocusOn[annotation.uuid] || checkFocusOn[annotation.group])) {
              cssClass = "FOCUS"
          }

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
                  anchorPattern,
                  cssClass);
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

        // console.log("$rootScope.annotations")
        // console.log($rootScope.annotations)

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
          $rootScope,
          $rootScope.focusNgrams // optional focus ngrams
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
