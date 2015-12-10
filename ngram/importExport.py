import re
from admin.utils import PrintException

from gargantext_web.db import Node, Ngram, NodeNgram, NodeNodeNgram, NodeNgramNgram
from gargantext_web.db import cache, session, get_or_create_node, bulk_insert

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from ngram.tools import insert_ngrams
from analysis.lists import WeightedList, UnweightedList

from collections import defaultdict
from csv import writer, reader, QUOTE_MINIMAL


def get_id(ngram_terms):
    query = session.query(Ngram.id).filter(Ngram.terms==ngram_terms).first()
    return(query)


def exportNgramList(node,filename,delimiter="\t"):
    
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

    # pour la group_list on a des couples de ngram_ids
    # -------------------
    # ex: [(3544, 2353), (2787, 4032), ...]
    group_ngram_id_couples = [(nd_ng_ng.ngramx_id,nd_ng_ng.ngramy_id) for nd_ng_ng in group_node.node_nodengramngram_collection]

    # k couples comme set 
    # --------------------
    # [(a => x) (a => y)] => [a => {x,y}]
    grouped = defaultdict(set)

    for ngram in group_ngram_id_couples:
        # /!\     just in one direction      /!\
        #      a => {x} but not not x => {a}
        grouped[ngram[0]].add(ngram[1])
    
    
    # helper func
    def ngrams_to_csv_rows(ngram_ids, id_groupings={}, list_type=7):
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
        """
        # récupérer d'un coup les objets Ngram (avec terme)
        ng_objs = session.query(Ngram).filter(Ngram.id.in_(ngram_ids)).all()
        
        # les transcrire en tableau (liste de listes)
        csv_rows = list()
        for ng_obj in ng_objs:
            
            ng_id = ng_obj.id
            
            if ng_id in id_groupings.keys():
                this_grouped = "|".join(str(gid) for gid in id_groupings[ng_id])
            else:
                this_grouped = ""
            
            # transcription : 5 colonnes
            # ID , terme , n , type_de_liste , gid|gid|gid
            
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
    


def importNgramList(node,filename,delimiter="\t",modify_lists=[0,1,2]):
    '''
    Suppose une table CSV avec colonnes comme dans fonction export.
    
    /!\ efface et remplace les listes existantes  /!\
    /!\ (supprime leur collection de NodeNgrams)  /!\    
    
    '''
    
    list_types_shortcuts = {
        0: "StopList",
        1: "MiamList",
        2: "MapList",
    }
    
    # on supprime tous les NodeNgrams des listes à modifier
    # ------------------------------------------------------
    for list_shortcut in modify_lists:
        # find previous listnode id
        list_type = list_types_shortcuts[list_shortcut]
        list_node = get_or_create_node(nodetype=list_type, corpus=node)
        node_id = listnode.id
        
        # delete previous lists
        session.query(NodeNgram).filter(NodeNgram.node_id==list_node.id).delete()
        session.commit()
    
    
    # on lit le CSV
    # --------------
    ngrams_csv_rows = []
    
    with open(filename, "r") as f:
        ngrams_csv_rows = reader(f, 
                                 delimiter = delimiter,
                                 quoting   = QUOTE_MINIMAL
                                 )
    
    all_read_terms = list()
    
    for csv_row in ngrams_csv_rows:
        this_ng_id           = csv_row[0]
        this_ng_terms        = csv_row[1]
        this_ng_nlen         = csv_row[2]
        this_ng_list_type_id = csv_row[3]
        this_ng_grouped_ngs  = csv_row[4]
        
        # --- quelle liste cible ?
        
        # par ex: "MiamList"
        list_type = type_ids_cache[this_ng_list_type_id]
        
        tgt_list_node = get_or_create_node(nodetype=list_type, corpus=node)
            
        
        # --- test 1: forme existante dans node_ngram ?
        
        #preexisting = session.query(Ngram).filter(Ngram.terms == this_ng_terms).first()
        
        #if preexisting is None:
        #   # todo ajouter Ngram dans la table node_ngram
            #      avec un nouvel ID
        
        
        # --- test 2: forme déjà dans une liste ?
        
        #if preexisting is not None:
        #    # premier node de type "liste" mentionnant ce ngram_id
        #    #
        #    node_ngram = preexisting.node_node_ngram_collection[0]
        #    previous_list = node_ngram.node_id
        #
        
        # ---------------
        
        data[0] = tgt_list_node.id
        data[1] = this_ng_id          # on suppose le même ngram_id
        data[2] = 
    
    size = len(list(stop_words))

    
    
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])
    
    
    # bulk_insert(NodeNgramNgram, ['node_id', 'ngramx_id', 'ngramy_id', 'weight'], [d for d in data])
    
    
    # lecture des ngrams préexistants
    # ------------------



# Remarque quand on a un list_node li alors faire:
#     li.node_node_ngram_collection 
#  (donne tous les node_ngram)
#  (plus rapide que lancer une nouvelle session.query)
# 
# TODO utiliser carrément :
# [w.node_ngram for w in listnode.node_node_ngram_collection]

