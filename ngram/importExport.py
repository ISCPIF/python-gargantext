"""
Import and export all lists from a corpus node


TODO : FEAT GROUPED ITEMS ARE NOT HANDLED (synonyms)
            =======

TODO : REFACTOR 1) split list logic from corpus logic
                    => possibility to act on one list 

TODO : REFACTOR 2) improvements in ngram creation (?bulk like node_ngram links)
"""

from gargantext_web.db import Ngram, NodeNgram, NodeNodeNgram
from gargantext_web.db import cache, session, get_or_create_node, bulk_insert

# import sqlalchemy as sa
from sqlalchemy.sql import func, exists
# from sqlalchemy import desc, asc, or_, and_, Date, cast, select
#from sqlalchemy import literal_column
#from sqlalchemy.orm import aliased

#from ngram.tools import insert_ngrams
#from analysis.lists import WeightedList, UnweightedList

from collections import defaultdict
from csv import writer, reader, QUOTE_MINIMAL


def exportNgramLists(node,filename,delimiter="\t"):
    """
    export des 3 listes associées à un node corpus
           en combinaison locale avec les groupements
    """
    
    # the node arg has to be a corpus here
    if not hasattr(node, "type_id") or node.type_id != 4:
        raise TypeError("EXPORT: node argument must be a Corpus Node")
    
    # les nodes couvrant les listes
    # -----------------------------
    stop_node  = get_or_create_node(nodetype='StopList', corpus=node)
    miam_node  = get_or_create_node(nodetype='MiamList', corpus=node)
    map_node   = get_or_create_node(nodetype='MapList', corpus=node)
    group_node = get_or_create_node(nodetype='Group', corpus=node)


    # listes de ngram_ids correspondantes
    # ------------------------------------
    #~~ contenu: liste des ids [2562,...]
    stop_ngram_ids  = [stop_ngram.ngram_id for stop_ngram in stop_node.node_node_ngram_collection]
    
    # idem pour miam et map
    miam_ngram_ids  = [miam_ng.ngram_id for miam_ng in miam_node.node_node_ngram_collection]
    map_ngram_ids   = [map_ng.ngram_id for map_ng in map_node.node_node_ngram_collection]
    
    
    # pour debug ---------->8 --------------------
    #~ stop_ngram_ids = stop_ngram_ids[0:10]
    #~ miam_ngram_ids = stop_ngram_ids[0:10]
    #~ map_ngram_ids = map_ngram_ids[0:10]
    # --------------------->8 --------------------

    # pour la group_list on a des couples de ngram_ids
    # -------------------
    # ex: [(3544, 2353), (2787, 4032), ...]
    group_ngram_id_couples = [(nd_ng_ng.ngramx_id,nd_ng_ng.ngramy_id) for nd_ng_ng in group_node.node_nodengramngram_collection]
    
    
    # pour debug
    # group_ngram_id_couples = []
    

    # k couples comme set 
    # --------------------
    # [(a => x) (a => y)] => [a => {x,y}]
    grouped = defaultdict(set)

    for ngram in group_ngram_id_couples:
        # /!\     just in one direction      /!\
        #      a => {x} but not not x => {a}
        grouped[ngram[0]].add(ngram[1])
    
    
    # helper func
    def ngrams_to_csv_rows(ngram_ids, id_groupings={}, list_type=0):
        """
        Table d'infos basiques par ngram :
          (ng_id, forme du terme, poids, type_de_liste)
        avec une colonne supplémentaire optionnelle: 
            ngrams groupés avec cet id  ex: "4|42"
        
        Retourne une matrice csv_rows en liste de liste
                 [
                  [ligne1_colA, ligne1_colB..],
                  [ligne2_colA, ligne2_colB..],
                  ..
                 ]
        
        (ensuite par exemple csv.writer.writerows(csv_rows)
        
        list_type ici:
          0  <=> stopList
          1  <=> miamList
          2  <=> mapList
        """
        # récupérer d'un coup les objets Ngram (avec terme)
        if len(ngram_ids):
            ng_objs = session.query(Ngram).filter(Ngram.id.in_(ngram_ids)).all()
        else:
            ng_objs = []
        
        # les transcrire en tableau (liste de listes)
        csv_rows = list()
        for ng_obj in ng_objs:
            
            ng_id = ng_obj.id
            
            if ng_id in id_groupings.keys():
                this_grouped = "|".join(str(gid) for gid in id_groupings[ng_id])
            else:
                this_grouped = ""
            
            # transcription : 5 colonnes
            # ID , terme , n , type_de_liste , grouped_id|grouped_id...
            
            csv_rows.append(
                  [ng_id,ng_obj.terms,ng_obj.n,list_type,this_grouped]
                  )
        
        # csv_rows = [[ligne1_a, ligne1_b..],[ligne2_a, ligne2_b..],..]
        return csv_rows
    
    
    # on applique notre fonction ng_to_csv sur chaque liste
    # ------------------------------------------------------
    stop_csv_rows = ngrams_to_csv_rows(stop_ngram_ids, 
                                       id_groupings=grouped,
                                       list_type=0)
    
    # miam contient map donc il y a un préalable ici
    miam_without_map = [ng for ng in miam_ngram_ids if ng not in map_ngram_ids]
    miam_csv_rows = ngrams_to_csv_rows(miam_without_map, 
                                       id_groupings=grouped,
                                       list_type=1)
    
    map_csv_rows = ngrams_to_csv_rows(map_ngram_ids, 
                                       id_groupings=grouped,
                                       list_type=2)
    
    # all lists together now
    this_corpus_all_rows = stop_csv_rows + miam_csv_rows + map_csv_rows
    
    # output
    with open(filename, 'w') as out_file:
        
        # csv.writer()
        csv_wr = writer(out_file, 
                        delimiter=delimiter, 
                        quoting=QUOTE_MINIMAL)
        
        # write to outfile
        csv_wr.writerows(this_corpus_all_rows)
    


def importNgramLists(node,filename,delimiter="\t", del_lists=[]):
    '''
    Suppose une table CSV avec colonnes comme dans fonction export.
    
    
    del_lists : int[]
    
    /!\  si del_lists contient un ou plusieurs    /!\
    /!\  types de listes (array parmi [0,1,2])    /!\
    /!\ on efface et remplace la liste existante  /!\
    /!\ (supprime leur collection de NodeNgrams)  /!\
    
    par exemple 
    del_lists = [0,1] => effacera la stopList (aka 0)
                               et la miamList (aka 1)
                         mais pas la mapList (aka 2)
    
    
    TODO: 
      - import "group cliques joining" from rest_v1_0.ngrams.Group
        (and ideally add its logic to analysis.lists.Translations)
    
    '''
    
    # the node arg has to be a corpus here
    if not hasattr(node, "type_id") or node.type_id != 4:
        raise TypeError("IMPORT: node argument must be a Corpus Node")
    
    # for stats
    added_nd_ng = 0   # number of added list elements
    added_ng = 0      # number of added unknown ngrams
    
    
    # our list shortcuts will be 0,1,2
    our_ls = [
       {'name':"StopList", 'weight':-1.0,  'node': None,   'add_data':[]},
       {'name':"MiamList", 'weight':1.0,   'node': None,   'add_data':[]},
       {'name':"MapList",  'weight':2.0,   'node': None,   'add_data':[]}
        #   ^^^^^^^^^^^^^^^^^^^^^^^^^       ^^^^^^^^^^      ^^^^^^^^^^
        #        paramètres                  "cibles"        résultats
    ]
    
    # on mettra dans add_data les termes avec le ngram_id retrouvé/créé
    
    # find previous list node objects
    # (les 3 listes où on va écrire)
    for ltype in [0,1,2]:
        our_ls[ltype]['node'] = get_or_create_node(
                                   nodetype=our_ls[ltype]['name'], 
                                   corpus=node
                                )
        
    # si del_lists, on supprime tous les NodeNgrams des listes
    # --------------------------------------------------------
    for ltype in del_lists:
        this_list_id = our_ls[ltype]['node'].id
        
        # DELETE contents of previous lists
        session.query(NodeNgram).filter(NodeNgram.node_id==this_list_id).delete()
        session.commit()
        # todo garbage collect terms ?
    
    
    
    # also find group node
    group = get_or_create_node(nodetype='Group', corpus=node)
    
    # it will be fusionned at the end with the imported_groups dict
    imported_groups = defaultdict(set)
    
    
    # --------------
    # on lit le CSV
    # --------------
    ngrams_csv_rows = []
    
    with open(filename, "r") as f:
        ngrams_csv_rows = reader(f, 
                                 delimiter = delimiter,
                                 quoting   = QUOTE_MINIMAL
                                 )
        
        # vérifications initiales (version naïve terme par terme)
        #   ==> existence ?
        #       sinon création ngram
        #   ==> stockage dans add_data pour bulk_insert
        for i, csv_row in enumerate(ngrams_csv_rows):
            this_ng_id           = csv_row[0]
            this_ng_terms        = csv_row[1]
            this_ng_nlen         = int(csv_row[2])
            this_ltype           = int(csv_row[3])
            this_ng_group        = csv_row[4]
            
            # --- vérif terme
            if not len(this_ng_terms) > 0:
                print("WARNING: (skip line) empty term at CSV %s:l.%i" % (filename, i))
                continue
            
            # === quelle liste cible ?
            if this_ltype in [0,1,2]:
                # par ex: "MiamList"
                list_type = our_ls[this_ltype]['name']
                tgt_list_node = our_ls[this_ltype]['node']
            else:
                print("WARNING: (skip line) wrong list_type at CSV %s:l.%i" % (filename, i))
                continue
            
            
            print("IMPORT '%s' >> %s" % (this_ng_terms,list_type))
            
            # --- test 1: forme existante dans node_ngram ?
            
            preexisting = session.query(Ngram).filter(Ngram.terms == this_ng_terms).first()
            
            if preexisting is None:
                # ajout ngram dans la table node_ngram
                new_ng = Ngram(terms = this_ng_terms,
                                  n  = this_ng_nlen)
                
                # INSERT INTO node_ngram
                # ======================
                session.add(new_ng)
                session.commit()
                added_ng += 1
                
                # avec un nouvel ID
                our_ls[ltype]['add_data'].append(
                          [tgt_list_node.id, new_ng.id, our_ls[ltype]['weight']]
                         )
                
                # £TODO ici indexation dans les docs
                # => Occurrences
                # node_ngram = NodeNgram(node_id=list_id, ngram_id=ngram_id, weight=1.0)
            
            
            # cas ngram existant
            else:
                add_ng_id = preexisting.id
                
                # --- test 2: forme déjà dans la même liste ? 
                # (sauf si delete)
                if not this_ltype in del_lists:
                    # méthode traditionnelle
                    # session.query(NodeNgram)
                    #    .filter(NodeNgram.node_id == my_miam.id)
                    #    .filter(NodeNgram.ngram_id == preexisting.id)
                    
                    
                    # méthode avec exists() (car on n'a pas besoin de récupérer l'objet)
                    already_flag = session.query(
                           exists().where(
                              (NodeNgram.node_id == tgt_list_node.id) 
                              & (NodeNgram.ngram_id == preexisting.id)
                            )
                         ).scalar()
                    
                    if already_flag:
                        print("INFO: (skip line) already got %s in this list %s" %(this_ng_terms, list_type))
                        continue
                    
                    # --- TODO test 3 : forme dans une autre liste ?
                    #    par ex: conflit SI forme dans stop ET ajoutée à map
                
                    else:
                        # append to results
                        our_ls[ltype]['add_data'].append(
                            [tgt_list_node.id, preexisting.id, our_ls[ltype]['weight']]
                         )
                
                # si c'est une liste à effacer on ajoute toujours
                else:
                    # append to results
                    our_ls[ltype]['add_data'].append(
                        [tgt_list_node.id, preexisting.id, our_ls[ltype]['weight']]
                     )
        
            
            # --- TODO éléments groupés
            
            # grouped synonyms set (if any)
            if len(this_ng_group) != 0:
                imported_groups[this_ng_id] = set(
                    [int(ng_id) for ng_id in this_ng_group.split('|')]
                    )
    
    
    # INSERT INTO node_node_ngram
    # ============================
    for list_type in [0,1,2]:
        bulk_insert(
           NodeNgram, 
           ['node_id', 'ngram_id', 'weight'],
           [d for d in our_ls[list_type]['add_data']]
        )
        
        added_nd_ng += len(our_ls[list_type]['add_data'])
    
    # synonyms set unions
    #
    # original arcs (directed couples)
    old_arcs = session.query(NodeNgramNgram.ngramx_id, NodeNgramNgram.ngramy_id).filter(NodeNgramNgram.node_id == group.id).all()
    
    # TODO groupes: correspondance entre les IDS_source et les nouveaux IDS
    
    # TODO groupes: factoriser le code de fusion de groupes
    #               depuis rest_v1_0.ngrams.Group.get
    #               ou la remplacer par une agrégation sql + sets
    #               cf. long commentaire en bas
    
    # INSERT INTO node_nodengramngram
    # ===============================
    
    print("INFO: added %i elements in the lists indices" % added_nd_ng)
    print("INFO: added %i new ngrams in the lexicon" % added_ng)
    





# à chronométrer:
# [w.node_ngram for w in listnode.node_node_ngram_collection]






##################################
#    essais fusion de groupes
##################################
# # tentative pour refaire le code de Samuel (dans rest_v1_0.ngrams.Group.get)
# # qui fait les cliques de synonymes, directement en sql
# 
# select ngramx_id as root, ngramy_id as kid 
#  into temporary tempo_1 
#  from node_nodengramngram 
#  where node_id = 199 
#  and ngramx_id != ngramy_id ;
#  
# --  root | kid  
# -- ------+------
# --  3447 | 3443
# --  3456 | 3462
# --  3455 | 3462
# --  3455 | 3456
# --  3441 | 3448
# --  3452 | 3446
# --  3452 | 3444
# 
# puis parcours récursif cf http://stackoverflow.com/questions/28758058/
# 
# with recursive mes_cliques as (
#   select root as root_id, root, kid
#   from tempo_1
#   union all
#   select p.root_id, c.root, c.kid
#   from tempo_1 as c
#     join mes_cliques p on p.kid = c.root
# )
# select root_id, array_agg(kid) as edges_in_group
# from mes_cliques
# group by root_id;
# 
# RESULTAT
# -- root_id |  edges_in_group  
# -- --------+------------------
# --    3441 | {3448}
# --    3456 | {3462}
# --    3452 | {3446,3444}
# --    3447 | {3443}
# --    3455 | {3462,3456,3462}
# 
# 

# # autre résultat plus direct avec agrégat simple
# # -----------------------------------------------
# select ngramx_id as root, array_agg(ngramy_id) as kids 
#  from node_nodengramngram
#  where node_id = 199
#  and ngramx_id != ngramy_id
# group by ngramx_id ;
# 
# --  root |    kids     
# -- ------+-------------
# --  3441 | {3448}
# --  3452 | {3446,3444}
# --  3455 | {3462,3456}
# --  3447 | {3443}
# --  3456 | {3462}
