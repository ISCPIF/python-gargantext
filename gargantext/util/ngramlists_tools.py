"""
Tools to work with ngramlists (MAINLIST, MAPLIST, STOPLIST)

    - query_list(list_id) to retrieve ngrams
    - export_ngramlists(corpus_id)
"""

from gargantext.util.group_tools import query_groups, group_union
from gargantext.util.db          import session, desc, func, \
                                        bulk_insert_ifnotexists
from gargantext.models           import Ngram, NodeNgram, NodeNodeNgram, \
                                        NodeNgramNgram

from gargantext.util.lists       import UnweightedList, Translations

from sqlalchemy.sql      import exists
from os                  import path
from csv                 import writer, reader, QUOTE_MINIMAL
from collections         import defaultdict
from re                  import match
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
def ngrams_to_csv_rows(ngram_objs, id_groupings={}, list_type=""):
    """
    @param: ngram_objs
            an array of ngrams (eg: from a db query.all())

    @param: optional id_groupings
            a dict of sets {mainform_id : {subform_idA, subform_idB, etc}}

    @param: list_type (a str 'map','main' or 'stop' to fill in col 4)

    Outputs a basic info table per ngram
      (ng_id, term string, term size, list_type)

      with an optional 5th column of grouped subforms  ex: "4|42"

    Returns format is a csv_rows matrix (as a list of lists)
             [
              [ligne1_colA, ligne1_colB..],
              [ligne2_colA, ligne2_colB..],
              ..
             ]

    (to be used for instance like: csv.writer.writerows(csv_rows)

    list_type ici:
      0  <=> stopList
      1  <=> miamList
      2  <=> mapList
    """
    # transcrire les objets ngrammes en tableau (liste de listes)
    csv_rows = list()
    for ng_obj in ngram_objs:
        ng_id = ng_obj.id

        if ng_id in id_groupings.keys():
            this_grouped = "|".join(str(gid) for gid in id_groupings[ng_id])
        else:
            this_grouped = ""

        # transcription : 5 columns
        # ID , terme , n , type_de_liste , grouped_id|grouped_id...

        csv_rows.append(
              [ng_id,ng_obj.terms,ng_obj.n,list_type,this_grouped]
              )

    return csv_rows



def export_ngramlists(node,fname=None,delimiter="\t",titles=False):
    """
    export of the 3 lists under a corpus node (MAP, MAIN, STOP)
           with local combination of groups

    @param node: the corpus node

    @param fname:     optional filename to write the CSV
                      (if absent, returns a str with CSV contents)

    @param delimiter: optional column separator in the CSV
                      (if absent defaults to tabulation)

    @param titles:    optional flag to print or not a first line with headers

    # ID  , term , nwords , list_type , grouped_id|grouped_id...
    1622	textile	1	main 1623|3397
    3397	textile production	2	main
    3410	possibility	1	stop

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

    # pour la group_list on a des couples de ngram_ids
    # -------------------
    # ex: [(3544, 2353), (2787, 4032), ...]
    group_ngram_id_couples = query_groups(group_node.id).all()

    # k couples comme set
    # --------------------
    # [(x => y1), (x => y2)] >~~~~~~~> [x => {y1,y2}]
    grouped = defaultdict(set)
    for ngram in group_ngram_id_couples:
        grouped[ngram[0]].add(ngram[1])

    # on applique notre fonction ng_to_csv sur chaque liste
    # ------------------------------------------------------
    map_csv_rows = ngrams_to_csv_rows(map_ngrams,
                                       id_groupings=grouped,
                                       list_type="map")

    stop_csv_rows = ngrams_to_csv_rows(stop_ngrams,
                                       id_groupings=grouped,
                                       list_type="stop")

    # miam contient map donc il y a un préalable ici
    map_ngram_ids = {ng.id for ng in map_ngrams}
    main_without_map = [ng for ng in main_ngrams if ng.id not in map_ngram_ids]
    miam_csv_rows = ngrams_to_csv_rows(main_without_map,
                                       id_groupings=grouped,
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
        csv_wr.writerow(["oldid","term","nwords","listtype","subforms"])

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



def import_ngramlists(fname, delimiter='\t', group_delimiter='|'):
    '''
    This function reads a CSV of an ngrams table for a Corpus,
    then it converts old ngram_ids to those of the current DB
    then recreates an equivalent set of MAINLIST, MAPLIST, STOPLIST + GROUPS

    Input example:
        oldid  | term          |nwords| ltype  |group_oldids
        -------+---------------+------+--------+---------------
        3842     water table        2    map      3724
        3724     water tables       2    map
        4277     water supply       2    map      190362|13415
        13415    water supplies     2    map
        190362   water-supply       1    map
        20489    wastewater         1    map

    Output:  3 x UnweightedList + 1 x Translations

    @param fname            a filename
    @param delimiter        a character used as separator in the CSV
    @param group_delimiter  a character used as grouped subforms separator
                            (in the last column)

    The conversion of old_id to ngram_id works in 2 steps:
        => look up each term str in the DB with bulk_insert_ifnotexists
           (creates absent ngrams if necessary)
        => use the new ids to map the relations involving the old ones

    NB: the creation of MAINLIST also adds all elements from the MAPLIST

    NB: To merge the imported lists into a corpus node's lists,
        chain this function with merge_ngramlists()
    '''
    # --------------
    #   READ CSV
    # --------------

    # main storage for the ngrams by list
    import_nodes_ngrams = {'stop':[], 'main':[], 'map':[]}

    # separate storage for the term's couples  [(term str, nwords int),...]
    imported_ngrams_dbdata = []

    # and all the old ids, by term (for id lookup after dbdata bulk_insert)
    imported_ngrams_oldids = {}

    # and for the imported_grouping list of couples [(x1,y1),(x1,y2),(x2,y3),..]
    imported_groupings = []

    # /!\ imported_grouping contains only external ids (aka oldids)
    #     (ie imported ids.. that will have to be translated
    #      to target db ids)

    fh = open(fname, "r")
    ngrams_csv_rows = reader(fh,
                             delimiter = delimiter,
                             quoting   = QUOTE_MINIMAL
                             )

    # for stats
    n_read_lines = 0
    n_total_ng = 0
    n_added_ng = 0
    n_group_relations = 0

    # load CSV + initial checks
    for i, csv_row in enumerate(ngrams_csv_rows):
        # fyi
        n_read_lines +=1
        # print("---------------READ LINE %i" % i)
        try:
            this_ng_oldid        = str(csv_row[0])
            this_ng_term         = str(csv_row[1])
            this_ng_nwords       = int(csv_row[2])
            this_list_type       = str(csv_row[3])
            this_ng_group        = str(csv_row[4])

        except:
            if i == 0:
                print("WARN: (skip line) probable header line at CSV %s:l.0" % fname)
                continue

        # --- term checking
        if not len(this_ng_term) > 0:
            print("WARN: (skip line) empty term at CSV %s:l.%i" % (fname, i))
            continue

        # --- check before any old ID retrieve
        if not match("\d+$", this_ng_oldid):
            print("WARN: (skip line) bad ID at CSV %s:l.%i" % (fname, i))
            continue
        else:
            this_ng_oldid = int(this_ng_oldid)

        # --- check correct list type
        if not this_list_type in ['stop','main','map']:
            print("WARN: (skip line) wrong list type at CSV %s:l.%i" % (fname, i))
            continue

        # ================= Store the data ====================
        # the ngram data
        imported_ngrams_dbdata.append([this_ng_term, this_ng_nwords])
        imported_ngrams_oldids[this_ng_term] = this_ng_oldid

        # and the "list to ngram" relation
        import_nodes_ngrams[this_list_type].append(this_ng_oldid)

        # ====== Store synonyms from the import (if any) ======
        if len(this_ng_group) != 0:
            group_as_external_ids = this_ng_group.split('|')

            for external_subform_id in group_as_external_ids:
                external_subform_id = int(external_subform_id)
                imported_groupings.append(
                  (this_ng_oldid,external_subform_id)
                  )

    # end of CSV read
    fh.close()

    # ======== ngram save + id lookup =========
    n_total_ng = len(imported_ngrams_dbdata)

    # returns a dict {term => id} and a count of inserted ones
    (new_ngrams_ids, n_added_ng) = bulk_insert_ifnotexists(
        model = Ngram,
        uniquekey = 'terms',
        fields = ('terms', 'n'),
        data = imported_ngrams_dbdata,
        do_stats = True
    )
    del imported_ngrams_dbdata

    # loop on old ngrams and create direct mapping old_id => new_id
    old_to_new_id_map = {}
    for term, oldid in imported_ngrams_oldids.items():
        old_to_new_id_map[oldid] = new_ngrams_ids[term]
    del new_ngrams_ids
    del imported_ngrams_oldids

    # print(old_to_new_id_map)
    # print(import_nodes_ngrams)
    # ======== Import into lists =========

    # 3 x abstract lists + 1 translations
    result = {
         'map':  UnweightedList(),
         'main': UnweightedList(),
         'stop': UnweightedList(),
         'groupings' : Translations()
         }

    for list_type in import_nodes_ngrams:
        for old_id in import_nodes_ngrams[list_type]:
            new_id = old_to_new_id_map[old_id]
            # add to the abstract list
            result[list_type].items.add(new_id)

        # for main also add map elements
        if list_type == 'main':
            for old_id in import_nodes_ngrams['map']:
                new_id = old_to_new_id_map[old_id]
                result['main'].items.add(new_id)

    # ======== Synonyms =========
    for (x,y) in imported_groupings:
        new_mainform_id = old_to_new_id_map[x]
        new_subform_id  = old_to_new_id_map[y]

        # /!\ Translations use (subform => mainform) order
        result['groupings'].items[new_subform_id] = new_mainform_id
        n_group_relations += 1

    # ------------------------------------------------------------------
    print("IMPORT: read %i lines from the CSV" % n_read_lines)
    print("IMPORT: read %i terms (%i added and %i already existing)"
                % (n_total_ng, n_added_ng, n_total_ng-n_added_ng) )
    print("IMPORT: read %i grouping relations" % n_group_relations)

    return result
