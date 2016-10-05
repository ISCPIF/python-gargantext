"""
Tools to work with ngramlists (MAINLIST, MAPLIST, STOPLIST)

    - query_list(list_id) to retrieve ngrams
    - export_ngramlists(corpus_node)
    - import_ngramlists(corpus_node)
    - merge_ngramlists(new_lists, onto_corpus = corpus_node)
"""

from gargantext.util.group_tools import query_groups, group_union
from gargantext.util.db          import session, desc, func, \
                                        bulk_insert_ifnotexists
from gargantext.models           import Ngram, NodeNgram, NodeNodeNgram, \
                                        NodeNgramNgram, Node

from gargantext.util.lists       import UnweightedList, Translations

from gargantext.constants        import DEFAULT_CSV_DELIM, DEFAULT_CSV_DELIM_GROUP

# import will implement the same text cleaning procedures as toolchain
from gargantext.util.toolchain.parsing           import normalize_chars
from gargantext.util.toolchain.ngrams_extraction import normalize_forms

# merge will also index the new ngrams in the docs of the corpus
from gargantext.util.toolchain.ngrams_addition   import index_new_ngrams

from sqlalchemy.sql      import exists
from os                  import path
from csv                 import writer, reader, QUOTE_MINIMAL
from collections         import defaultdict
from re                  import match, findall
from io                  import StringIO # pseudo file to write CSV to memory

def query_list(list_id,
                pagination_limit=None, pagination_offset=None,
                details=False, scoring_metric_id=None, groupings_id=None
                ):
    """
    Paginated listing of ngram_ids in a NodeNgram lists.

    Works for a mainlist or stoplist or maplist (not grouplists!)

    Parameter:
      - pagination_limit, pagination_offset
      - details: if False, send just the array of ngram_ids
                 if True and no scoring,   send couples with (ngram_id, term)
                 if True and a scoring_id, send triples with (ngram_id, term, scoring)
      - scoring_metric_id: id of a scoring metric node   (TFIDF or OCCS)
                           (for details and sorting)
      - groupings_id: optional id of a list of grouping relations (synonyms)
                      (each synonym will be added to the list if not already in there)

    FIXME: subforms appended recently and not generalized enough
            => add a common part for all "if groupings_id"
            => provide the option also in combination with scoring
    """
    # simple contents
    if not details:
        query = session.query(NodeNgram.ngram_id).filter(NodeNgram.node_id == list_id)

        if groupings_id:
            subforms = (session.query(NodeNgramNgram.ngram2_id)
                               # subform ids...
                               .filter(NodeNgramNgram.node_id == groupings_id)
                               # .. that are connected to a mainform
                               .join(NodeNgram, NodeNgram.ngram_id == NodeNgramNgram.ngram1_id)
                               # .. which is in the list
                               .filter(NodeNgram.node_id == list_id)
                               )
            # union with the main q
            query = query.union(subforms)

    # detailed contents (id + terms)
    elif not scoring_metric_id:
        query = (session.query(Ngram.id, Ngram.terms, Ngram.n)
                        .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                        .filter(NodeNgram.node_id == list_id)
                        )
        if groupings_id:
            subforms = (session.query(Ngram.id, Ngram.terms, Ngram.n)
                               .join(NodeNgramNgram, NodeNgramNgram.ngram2_id == Ngram.id)
                               # subform ids...
                               .filter(NodeNgramNgram.node_id == groupings_id)
                               # .. that are connected to a mainform
                               .join(NodeNgram, NodeNgram.ngram_id == NodeNgramNgram.ngram1_id)
                               # .. which is in the list
                               .filter(NodeNgram.node_id == list_id)
                               )
            # union with the main q
            query = query.union(subforms)

    # detailed contents (id + terms) + score
    else:
        # NB: score can be undefined (eg ex-subform that now became free)
        #     ==> we need outerjoin
        #     and the filter needs to have scoring_metric_id so we do it before

        ScoresTable = (session
                        .query(NodeNodeNgram.score, NodeNodeNgram.ngram_id)
                        .filter(NodeNodeNgram.node1_id == scoring_metric_id)
                        .subquery()
                        )

        query = (session
                    .query(
                        NodeNgram.ngram_id,
                        Ngram.terms,
                        ScoresTable.c.score
                     )
                    .join(Ngram, NodeNgram.ngram_id == Ngram.id)

                    # main filter ----------------------
                    .filter(NodeNgram.node_id == list_id)

                    # scores if possible
                    .outerjoin(ScoresTable,
                               ScoresTable.c.ngram_id == NodeNgram.ngram_id)

                    .order_by(desc(ScoresTable.c.score))
                )

    if pagination_limit:
        query = query.limit(pagination_limit)

    if pagination_offset:
        query = query.offset(pagination_offsets)

    return query


# helper func for exports
def ngrams_to_csv_rows(ngram_objs, ngram_dico={}, group_infos={},
                        list_type="", groupings_delim=DEFAULT_CSV_DELIM_GROUP):
    """
    @param: ngram_objs
            an array of ngrams (eg: from a db query.all())

    @param: optional group_infos as links and subs
            ginfos{links} = a dict of sets
                            {mainform_id : {subform_idA, subform_idB, etc}}
            ginfos{subs}  = a reverse map
                            {subform_idA:mainform_id, subform_idB:mainform_id, etc}}

    @param: list_type (a str 'map','main' or 'stop' to fill in col 4)

    Outputs a condensed info table per ngram
      (list_type, "term string")

      with an optional 3rd column of grouped subforms
        ex: "othertermstring|yetanothertermstring"

    Returns format is a csv_rows matrix (as a list of lists)
             [
              [row1_colA, row1_colB..],
              [row2_colA, row2_colB..],
              ..
             ]

    (to be used for instance like: csv.writer.writerows(csv_rows)

    list_type ici:
      0  <=> stop
      1  <=> miam
      2  <=> map
    """
    # transcribe ngram objects to a table (array of row-arrays)
    csv_rows = list()
    for ng_obj in ngram_objs:
        ng_id = ng_obj.id

        # only mainforms will get their own row
        if ng_id not in group_infos['subs']:

            # if has subforms
            if ng_id in group_infos['links']:
                this_grouped_terms = groupings_delim.join(
                                # we replace grouped_ids by their terms string
                                [ngram_dico[subf_id] for subf_id in group_infos['links'][ng_id]]
                                )
            # if no subforms
            else:
                this_grouped_terms = ""

            # transcription :
            # 3 columns = |status,         |  mainform, |  forms
            #             (type_of_list)    ( term )     ( subterm1|&|subterm2 )

            csv_rows.append(
                  [list_type,ng_obj.terms,this_grouped_terms]
                  )

    return csv_rows



def export_ngramlists(node,fname=None,delimiter=DEFAULT_CSV_DELIM,titles=True):
    """
    export of the 3 lists under a corpus node (MAP, MAIN, STOP)
           with local combination of groups

    @param node: the corpus node

    @param fname:     optional filename to write the CSV
                      (if absent, returns a str with CSV contents)

    @param delimiter: optional column separator in the CSV
                      (if absent defaults to tabulation)

    @param titles:    optional flag to print or not a first line with headers

    status     label               forms
    map        textile             textiles|&|textile production
    stop       possibility

    TODO : REFACTOR split list logic from corpus logic
                    => possibility to act on one list
    """

    # the node arg has to be a corpus here
    if not hasattr(node, "typename") or node.typename != "CORPUS":
        raise TypeError("EXPORT: node argument must be a Corpus Node")

    # les nodes couvrant les listes
    # -----------------------------
    stoplist_node  = node.children("STOPLIST").first()
    mainlist_node  = node.children("MAINLIST").first()
    maplist_node   = node.children("MAPLIST").first()

    # et les groupes de synonymes
    group_node = node.children("GROUPLIST").first()

    # listes de ngram_ids correspondantes
    # ------------------------------------
    # contenu: liste des objets ngrammes [(2562,"monterme",1),...]
    stop_ngrams  = query_list(stoplist_node.id, details=True, groupings_id=group_node.id).all()
    main_ngrams  = query_list(mainlist_node.id, details=True, groupings_id=group_node.id).all()
    map_ngrams  = query_list(maplist_node.id, details=True, groupings_id=group_node.id).all()

    # pour debug ---------->8 --------------------
    #~ stop_ngrams = stop_ngrams[0:10]
    #~ main_ngrams = main_ngrams[0:10]
    #~ map_ngrams  = map_ngrams[0:10]
    # --------------------->8 --------------------

    # preloop to fill a local copy of dictionary  ng_id => ng_term_str
    dico = {}
    for li in [stop_ngrams, main_ngrams, map_ngrams]:
        for (ngid, ngterm, ignored) in li:
            dico[ngid] = ngterm

    # for the groups we got couples of ids in the DB
    # -------------------
    # ex: [(3544, 2353), (2787, 4032), ...]
    group_ngram_id_couples = query_groups(group_node.id).all()

    # we expend this to double structure for groups lookup
    # 1) g['links'] = k couples (x,y_i) as a set   [x => {y1,y2}]

    # 2) g['subs']  = reverse map like translations    [(y1 => x), (y2 => x)]

    g = {
        "links":defaultdict(set),
        "subs":defaultdict(int)
        }
    for ngram in group_ngram_id_couples:
        x = int(ngram[0])
        y = int(ngram[1])
        g['links'][x].add(y)
        g['subs'][y] = x

    # on applique notre fonction ng_to_csv sur chaque liste
    # ------------------------------------------------------
    map_csv_rows = ngrams_to_csv_rows(map_ngrams,
                                       ngram_dico=dico,
                                       group_infos=g,
                                       list_type="map")

    stop_csv_rows = ngrams_to_csv_rows(stop_ngrams,
                                       ngram_dico=dico,
                                       group_infos=g,
                                       list_type="stop")

    # miam contient map donc il y a un préalable ici
    map_ngram_ids = {ng.id for ng in map_ngrams}
    main_without_map = [ng for ng in main_ngrams if ng.id not in map_ngram_ids]
    miam_csv_rows = ngrams_to_csv_rows(main_without_map,
                                       ngram_dico=dico,
                                       group_infos=g,
                                       list_type="main")

    # all lists together now
    this_corpus_all_rows = map_csv_rows + miam_csv_rows + stop_csv_rows

    # choice of output: file or string
    if fname == None:
        out_file = StringIO()
    elif type(fname) == str:
        out_file = open(fname, 'w')
    else:
        straight_to_handle = True
        out_file = fname

    # csv.writer()
    csv_wr = writer(out_file,
                    delimiter=delimiter,
                    quoting=QUOTE_MINIMAL)

    if titles:
        csv_wr.writerow(["status","label","forms"])

    # write to outfile
    csv_wr.writerows(this_corpus_all_rows)

    if fname == None:
        # return output as a string
        print("EXPORT: wrote %i ngrams to CSV string"
               % len(this_corpus_all_rows))
        return out_file.getvalue()
    elif straight_to_handle:
        print("EXPORT: wrote %i ngrams to CSV response handle"
               % len(this_corpus_all_rows))
    else:
        # just close output file
        out_file.close()
        print("EXPORT: wrote %i ngrams to CSV file '%s'"
               % (len(this_corpus_all_rows), path.abspath(fname)))



def import_ngramlists(the_file, delimiter=DEFAULT_CSV_DELIM,
                             group_delimiter=DEFAULT_CSV_DELIM_GROUP):
    '''
    This function reads a CSV of an ngrams table for a Corpus,
    then it converts old ngram_ids to those of the current DB
       (and adds to DB any unknown ngrams)
    then recreates an equivalent set of MAINLIST, MAPLIST, STOPLIST + GROUPS

    Input example:
        status  | label         |forms
        --------+---------------+---------------------
        map      water table     water tables
        map      water supply    water-supply|&|water supplies
        stop     wastewater

    The title line is mandatory.
    The label will correspond to our DB mainform type.

    Variants:
    ----------
    For user accessibility, we allow different formats using equivalence rules:

    1) It is implicit that the label string is also one of the forms
       therefore the input example table is equivalent to this "verbose" table:

        status  | label         |forms
        --------+---------------+---------------------
        map      water table     water table|&|water tables
        map      water supply    water supply|&|water-supply|&|water supplies
        stop     wastewater      wastewater


    2) The default status is map and the status column is optional
       thus, if we ignore "wastewater", the input table is also equivalent to:

         label         |forms
        ---------------+---------------------
        water table     water tables
        water supply    water-supply|&|water supplies


    3) From DB point of view, both "forms that are labels" and "other forms" are
       finally saved just as ngrams. So the input table is also equivalent to:

        status  | label         |forms
        --------+---------------+---------------------
        map      water table     water tables
        map      water tables
        map      water supply    water-supply|&|water supplies
        map      water supplies
        map      water-supply
        stop     wastewater


    Output:
    -------
        3 x UnweightedList + 1 x Translations

    @param the_file         a local filename or file contents or a filehandle-like
    @param delimiter        a character used as separator in the CSV
    @param group_delimiter  a character used as grouped subforms separator
                            (in the last column)

    The retrieval of ngram_ids works in 2 steps:
        => look up each term str in the DB with bulk_insert_ifnotexists
           (creates absent ngrams if necessary)
        => use the new ids to map the relations involving the old ones

    NB: the creation of MAINLIST also adds all elements from the MAPLIST

    NB: To merge the imported lists into a corpus node's lists,
        chain this function with merge_ngramlists()
    '''
    # ---------------
    #  ngram storage
    # ---------------

    # main storage for the ngrams by list
    imported_nodes_ngrams = {'stop':[], 'main':[], 'map':[]}

    # and all the terms (for unique and for dbdata bulk_insert)
    imported_unique_ngramstrs = {}

    # and for the imported_grouping list of couples [(str1,str1),(str1,str2)..]
    imported_groupings = []

    # /!\ imported_grouping contains the subforms' terms themselves
    #     (that will have to be translated to ngram_ids for the target db)

    # =============== READ CSV ===============

    if isinstance(the_file, list):
        fname = 'imported_file'
        contents = the_file
    else:
        if isinstance(the_file, str):
            fh = open(the_file, "r")
            fname = the_file
        elif callable(getattr(the_file, "read", None)):
            fh = the_file
            fname = the_file
        else:
            raise TypeError("IMPORT: the_file argument has unknown type %s" % type(the_file))


        # reading all directly b/c csv.reader takes only lines or a real fh in bytes
        # and we usually have a "false" fh (uploadedfile.InMemoryUploadedFile) in strings
        # (but we checked its size before!)
        contents = fh.read().decode("UTF-8").split("\n")

        # end of CSV read
        fh.close()

    # <class 'django.core.files.uploadedfile.InMemoryUploadedFile'>

    ngrams_csv_rows = reader(contents,
                             delimiter = delimiter,
                             quoting   = QUOTE_MINIMAL
                             )

    # for stats
    n_read_lines = 0
    n_total_ng = 0
    n_added_ng = 0
    n_group_relations = 0

    # columntype => int
    columns = {}

    # load CSV + initial checks
    for i, csv_row in enumerate(ngrams_csv_rows):
        # fyi
        n_read_lines +=1
        # print("---------------READ LINE %i" % i)

        # headers
        if i == 0:
            n_cols = len(csv_row)
            for j, colname in enumerate(csv_row):
                if colname in ['label', 'status', 'forms']:
                    columns[colname] = j
                # skip empty columns
                elif match(r'^\s*$',colname):
                    pass
                else:
                    raise ValueError('Wrong header "%s" on line %i (only possible headers are "label", "forms" and "status")' % (colname, n_read_lines))
            if 'label' not in columns:
                raise ValueError('CSV must contain at least one column with the header "label"')

        if not len(csv_row):
            continue

        # try:
        # mandatory column
        this_row_label     = str(csv_row[columns['label']])

        # other columns or their default values
        if 'status' in columns:
            this_list_type = str(csv_row[columns['status']])
        else:
            this_list_type = 'map'

        if 'forms' in columns:
            this_row_forms = str(csv_row[columns['forms']])
        else:
            this_row_forms = ''

        # string normalizations
        this_row_label = normalize_forms(normalize_chars(this_row_label))

        # except:
        #     if i == 0:
        #         print("IMPORT WARN: (skip line) probable header line at CSV %s:l.0" % fname)
        #         continue
        #     else:
        #         raise ValueError("Error on CSV read line %i" % i)

        # --- term checking
        if not len(this_row_label) > 0:
            print("IMPORT WARN: (skip line) empty term at CSV %s:l.%i" % (fname, i))
            continue

        # --- check correct list type
        if not this_list_type in ['stop','main','map']:
            print("IMPORT WARN: (skip line) wrong list type at CSV %s:l.%i" % (fname, i))
            continue

        # subforms can be duplicated (in forms and another label)
        # but we must take care of unwanted other duplicates too
        if this_row_label in imported_unique_ngramstrs:
            print("TODO IMPORT DUPL: (skip line) term appears more than once at CSV %s:l.%i"
                    % (fname, i))

        # ================= Store the data ====================
        # the ngram census
        imported_unique_ngramstrs[this_row_label] = True

        # and the "list to ngram" relation
        imported_nodes_ngrams[this_list_type].append(this_row_label)

        # ====== Store synonyms from the import (if any) ======
        if len(this_row_forms) != 0:
            other_terms = []
            for raw_term_str in this_row_forms.split(group_delimiter):

                # each subform is also like an ngram declaration
                term_str = normalize_forms(normalize_chars(raw_term_str))
                imported_unique_ngramstrs[term_str] = True
                imported_nodes_ngrams[this_list_type].append(term_str)

                # the optional repeated mainform doesn't interest us
                # because we already have it via the label
                if term_str != this_row_label:

                    # save links
                    imported_groupings.append(
                        (this_row_label, term_str)
                        )

    # ======== ngram save + id lookup =========
    n_total_ng = len(imported_unique_ngramstrs)

    # prepare data format
    imported_ngrams_dbdata = []
    for ngram_str in imported_unique_ngramstrs:
        # DB needs the number of separate words
        n_words = 1 + len(findall(r' ', ngram_str))
        imported_ngrams_dbdata.append((ngram_str, n_words))

    # returns a dict {term => id} and a count of inserted ones
    #                             -------------------------
    (new_ngrams_ids, n_added_ng) = bulk_insert_ifnotexists(
    #                             -------------------------
        model = Ngram,
        uniquekey = 'terms',
        fields = ('terms', 'n'),
        data = imported_ngrams_dbdata,
        do_stats = True
    )
    del imported_ngrams_dbdata

    # new_ngrams_ids contains a direct mapping ng_str => new_id
    del imported_unique_ngramstrs

    # print(new_ngrams_ids)
    # print(imported_nodes_ngrams)

    # ======== Import into lists =========

    # 3 x abstract lists + 1 translations
    result = {
         'map':  UnweightedList(),
         'main': UnweightedList(),
         'stop': UnweightedList(),
         'groupings' : Translations()
         }

    for list_type in imported_nodes_ngrams:
        for ng_str in imported_nodes_ngrams[list_type]:
            new_id = new_ngrams_ids[ng_str]
            # add to the abstract list
            result[list_type].items.add(new_id)

        # for main also add map elements
        if list_type == 'main':
            for ng_str in imported_nodes_ngrams['map']:
                new_id = new_ngrams_ids[ng_str]
                result['main'].items.add(new_id)

    # ======== Synonyms =========
    for (x_str,y_str) in imported_groupings:
        new_mainform_id = new_ngrams_ids[x_str]
        new_subform_id  = new_ngrams_ids[y_str]

        # /!\ Translations use (subform => mainform) order
        result['groupings'].items[new_subform_id] = new_mainform_id
        n_group_relations += 1

    # ------------------------------------------------------------------
    print("IMPORT: read %i lines from the CSV" % n_read_lines)
    print("IMPORT: read %i terms (%i added and %i already existing)"
                % (n_total_ng, n_added_ng, n_total_ng-n_added_ng) )
    print("IMPORT: read %i grouping relations" % n_group_relations)

    # print("IMPORT RESULT", result)
    return result


def merge_ngramlists(new_lists={}, onto_corpus=None, del_originals=[]):
    """
    Integrates an external terms table to the current one:
       - merges groups (using group_union() function)
       - resolves conflicts if terms belong in different lists
          > map wins over both other types
          > main wins over stop
          > stop never wins   £TODO STOP wins over candidates from main

    @param new_lists:     a dict of *new* imported lists with format:
                                {'stop':     UnweightedList,
                                 'main':     UnweightedList,
                                 'map':      UnweightedList,
                                 'groupings': Translations }

                   if any of those lists is absent it is considered empty

    @param onto_corpus:   a corpus node to get the *old* lists

    @param del_originals: an array of original wordlists to ignore
                          and delete during the merge
                          possible values : ['stop','main','map']

            par exemple
            del_originals = ['stop','main'] => effacera la stoplist
                                                 et la mainlist
                                          mais pas la maplist qui sera fusionnée
                                         (les éléments de la map list
                                          seront remis dans la main à la fin)

    NB: Uses group_tools.group_union() to merge the synonym links.
        Uses ngrams_addition.index_new_ngrams() to also add new ngrams to the docs
    """
    # log to send back to client-side (lines will be joined)
    my_log = []

    # the tgt node arg has to be a corpus here
    if not hasattr(onto_corpus, "typename") or onto_corpus.typename != "CORPUS":
        raise TypeError("IMPORT: 'onto_corpus' argument must be a Corpus Node")

    # for stats
    added_nd_ng = 0   # number of added list elements


    # our list shortcuts will be 0,1,2 (aka lid)
    # by order of precedence
    linfos = [
       {'key': 'stop', 'name':"STOPLIST"},    # lid = 0
       {'key': 'main', 'name':"MAINLIST"},    # lid = 1
       {'key': 'map',  'name':"MAPLIST"}      # lid = 2
    ]


    # ======== Index the new ngrams in the docs =========
    all_possibly_new_ngram_ids = []
    collect = all_possibly_new_ngram_ids.append
    for lid, info in enumerate(linfos):
        list_type = info['key']
        if list_type in new_lists:
            for ng_id in new_lists[list_type].items:
                collect(ng_id)

    from gargantext.util.toolchain.main import t
    print("MERGE DEBUG: starting index_new_ngrams", t())
    n_added = index_new_ngrams(all_possibly_new_ngram_ids, onto_corpus)
    print("MERGE DEBUG: finished index_new_ngrams", t())

    my_log.append("MERGE: added %i new ngram occurrences in docs" % n_added)

    # ======== Get the old lists =========
    old_lists = {}

    # DB nodes stored with same indices 0,1,2 (resp. stop, miam and map)
    # find target ids of the list node objects
    tgt_nodeids = [
                    onto_corpus.children("STOPLIST").first().id,    # £todo via parent project?
                    onto_corpus.children("MAINLIST").first().id,
                    onto_corpus.children("MAPLIST").first().id
                ]

    old_group_id = onto_corpus.children("GROUPLIST").first().id

    # retrieve old data into old_lists[list_type]...
    # ----------------------------------------------
    for lid, linfo in enumerate(linfos):
        list_type = linfo['key']
        if list_type not in del_originals:

            # NB can't use UnweightedList(tgt_nodeids[lid])
            # because we need to include out-of-list subforms
            list_ngrams_q  = query_list(tgt_nodeids[lid],
                                        groupings_id=old_group_id)
            old_lists[list_type] = UnweightedList(list_ngrams_q.all())
        else:
            # ...or use empty objects if replacing old list
            # ----------------------------------------------
            old_lists[list_type] = UnweightedList()
            msg = "MERGE: ignoring old %s which will be overwritten" % linfo['name']
            print(msg)
            my_log.append(msg)

    # ======== Merging all involved ngrams =========

    # all memberships with resolved conflicts of interfering memberships
    resolved_memberships = {}

    for list_set in [old_lists, new_lists]:
        for lid, info in enumerate(linfos):
            list_type = info['key']
            # if you don't want to merge one list just don't put it in new_lists
            if list_type in list_set:
                # we use the fact that lids are ordered ints...
                for ng_id in list_set[list_type].items:
                    if ng_id not in resolved_memberships:
                        resolved_memberships[ng_id] = lid
                    else:
                        # ...now resolving is simply taking the max
                        # stop < main < map
                        resolved_memberships[ng_id] = max(
                                                            lid,
                                                            resolved_memberships[ng_id]
                                                        )
            # now each ngram is only in its most important list
            # -------------------------------------------------
            # NB temporarily map items are not in main anymore
            #    but we'll copy it at the end
            # NB temporarily all subforms were treated separately
            #    from mainforms but we'll force them into same list
            #    after we merge the groups

    del old_lists

    # ======== Merging old and new groups =========
    # get the arcs already in the target DB (directed couples)
    previous_links = session.query(
       NodeNgramNgram.ngram1_id,
       NodeNgramNgram.ngram2_id
      ).filter(
         NodeNgramNgram.node_id == old_group_id
       ).all()

    n_links_previous = len(previous_links)

    # same format for the new arcs (Translations ~~~> array of couples)
    translated_imported_links = []
    add_link = translated_imported_links.append
    n_links_added = 0
    for (y,x) in new_lists['groupings'].items.items():
        add_link((x,y))
        n_links_added += 1
    del new_lists

    # group_union: joins 2 different synonym-links lists into 1 new list
    new_links = group_union(previous_links, translated_imported_links)
    del previous_links
    del translated_imported_links

    n_links_after = len(new_links)

    merged_group = Translations([(y,x) for (x,y) in new_links])
    del new_links

    # ======== Overwrite old data with new =========

    merged_group.save(old_group_id)

    msg = "MERGE: groupings %i updated (links before/added/after: %i/%i/%i)" % (old_group_id, n_links_previous, n_links_added, n_links_after)
    my_log.append(msg)
    print(msg)

    # ======== Target list(s) append data =========
    # if list 2 => write in both tgt_data_lists [1,2]
    # lists 0 or 1 => straightforward targets [0] or [1]

    merged_results = {
        'stop': UnweightedList(),
        'main': UnweightedList(),
        'map':  UnweightedList()
    }

    for (ng_id, winner_lid) in resolved_memberships.items():

        ## 1) using the new groups
        # normal case if not a subform
        if ng_id not in merged_group.items:
            target_lid = winner_lid
        # inherit case if is a subform
        else:
            mainform_id = merged_group.items[ng_id]
            # inherited winner
            try:
                target_lid = resolved_memberships[mainform_id]
            except KeyError:
                target_lid = winner_lid
                print("MERGE: WARN ng_id %i has incorrect mainform %i ?" % (ng_id, mainform_id))

        ## 2) map => map + main
        if target_lid == 2:
            todo_lids = [1,2]
        else:
            todo_lids = [target_lid]

        ## 3) storage
        for lid in todo_lids:
            list_type = linfos[lid]['key']
            merged_results[list_type].items.add(ng_id)

    # print("IMPORT: added %i elements in the lists indices" % added_nd_ng)

    # ======== Overwrite old data with new =========
    for lid, info in enumerate(linfos):
        tgt_id = tgt_nodeids[lid]
        list_type = info['key']
        result = merged_results[list_type]
        result.save(tgt_id)

        msg = "MERGE: %s %i updated (new size: %i)" % (info['name'],tgt_id, len(merged_results[list_type].items))
        my_log.append(msg)
        print(msg)

    # return a log
    return("\n".join(my_log))

def import_and_merge_ngramlists(file_contents, onto_corpus_id):
    """
    A single function to run import_ngramlists and merge_ngramlists together
    """
    new_lists = import_ngramlists(file_contents)

    corpus_node = session.query(Node).filter(Node.id == onto_corpus_id).first()

    # merge the new_lists onto those of the target corpus
    log_msg = merge_ngramlists(new_lists, onto_corpus=corpus_node)

    return log_msg
