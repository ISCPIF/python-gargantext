from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from sqlalchemy import text, distinct, or_,not_
from sqlalchemy.sql import func, desc
from sqlalchemy.orm import aliased

import datetime
import copy
import json

from gargantext_web.db import cache

from gargantext_web.validation import validate, ValidationException

from gargantext_web.db import session, Node, NodeNgram, NodeNgramNgram\
        , NodeNodeNgram, Ngram, Hyperdata, Node_Ngram, get_or_create_node


def DebugHttpResponse(data):
    return HttpResponse('<html><body style="background:#000;color:#FFF"><pre>%s</pre></body></html>' % (str(data), ))

import json
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()[:19] + 'Z'
        else:
            return super(self.__class__, self).default(obj)
json_encoder = JSONEncoder(indent=4)
def JsonHttpResponse(data, status=200):
    return HttpResponse(
        content      = json_encoder.encode(data),
        content_type = 'application/json; charset=utf-8',
        status       = status
    )
Http400 = SuspiciousOperation
Http403 = PermissionDenied

import csv
def CsvHttpResponse(data, headers=None, status=200):
    response = HttpResponse(
        content_type = "text/csv",
        status       = status
    )
    writer = csv.writer(response, delimiter=',')
    if headers:
        writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    return response

_ngrams_order_columns = {
    "frequency" : "-count",
    "alphabetical" : "terms"
}


from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import APIException as _APIException

class APIException(_APIException):
    def __init__(self, message, code=500):
        self.status_code = code
        self.detail = message


from rest_framework.decorators import api_view
#@login_required
# TODO how to secure REST ?


def get_occtfidf( ngrams , user_id , corpus_id , list_name):
    ngram_ids = {}
    corpus = session.query(Node).filter( Node.id==corpus_id ).first()
    nodes_ngrams = session.query(Ngram).filter(Ngram.id.in_( ngrams ) ).all()
    for ngram in nodes_ngrams:
        ngram_ids[ngram.id] = {
            "id": ngram.id,
            "name": ngram.terms,
            "scores": {}
        }

    # [ = = = = = = Get Uniq_Occs = = = = = = ]
    myamlist = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == cache.NodeType[list_name].id ).first()
    Miam = aliased(NodeNgram)
    ngrams_occs = (session.query(NodeNgram.ngram_id, func.sum(NodeNgram.weight))
                          .join(Node, Node.id == NodeNgram.node_id)
                          .join(Miam, Miam.ngram_id == NodeNgram.ngram_id)
                          .filter(Node.parent_id == corpus_id, Node.type_id==cache.NodeType['Document'].id)
                          .filter(Miam.node_id==myamlist.id)
                          .group_by(NodeNgram.ngram_id)
                          .all()
                  )

    for ngram in ngrams_occs:
        try:
            ngram_ids [ ngram[0] ]["scores"][ "occ_uniq" ] = ngram[1]
        except:
            pass
    for i in ngram_ids:
        if "occ_uniq" not in ngram_ids[i]["scores"]:
            ngram_ids[i]["scores"][ "occ_uniq" ] = 1
    # [ = = = = = = / Get Uniq_Occs = = = = = = ]

    group_by = []
    results   = ['id', 'terms']

    ngrams_query = (session
        .query(Ngram.id, Ngram.terms)
        .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
        .join(Node, Node.id == Node_Ngram.node_id)
    )
    Tfidf = aliased(NodeNodeNgram)
    tfidf_id = get_or_create_node(nodetype='Tfidf (global)', corpus=corpus).id
    ngrams_query = (ngrams_query.add_column(Tfidf.score.label('tfidf'))
                                .join(Tfidf, Tfidf.ngram_id == Ngram.id)
                                .filter(Tfidf.nodex_id == tfidf_id)
                    )
    group_by.append(Tfidf.score)
    results.append('tfidf')
    ngrams_query = (ngrams_query.filter(Node.parent_id == corpus_id)
            .group_by(Ngram.id, Ngram.terms, *group_by)
            )

    TheList = aliased(NodeNgram)
    list_id = get_or_create_node(nodetype=list_name, corpus=corpus).id
    ngrams_query = (ngrams_query.join(TheList, TheList.ngram_id == Ngram.id )
                                .filter(TheList.node_id == list_id)
                    )
    for ngram in ngrams_query:
        try:
            ngram_ids [ ngram[0] ]["scores"][ "tfidf" ] = ngram[2]
        except:
            pass
            
    for i in ngram_ids:
        if "tfidf" not in ngram_ids[i]["scores"]:
            ngram_ids[i]["scores"][ "tfidf" ] = 0.01

    return ngram_ids


class List(APIView):

    def get(self, request, corpus_id , list_name ):
        corpus = session.query(Node).filter( Node.id==corpus_id ).first()
        list_name = list_name.title()+"List"
        node_list = get_or_create_node(nodetype=list_name, corpus=corpus )
        nodes_ngrams = session.query(NodeNgram).filter(NodeNgram.node_id==node_list.id ).all()

        ngram_ids = {}
        for node in nodes_ngrams:
            ngram_ids[node.ngram_id] = True
        ngrams = [int(i) for i in list(ngram_ids.keys())]

        ngram_ids = get_occtfidf( ngrams , request.user.id , corpus_id , list_name)

        return JsonHttpResponse(ngram_ids)


class Ngrams(APIView):
    '''
    REST application to manage ngrams

    '''
    def get(self, request, node_id):
        # query ngrams
        ParentNode = aliased(Node)
        corpus = session.query(Node).filter(Node.id==node_id).first()
        group_by = []
        results   = ['id', 'terms']

        ngrams_query = (session
            .query(Ngram.id, Ngram.terms)
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
        )

        the_score = "tfidf"
        if request.GET.get('score', False) != False:
            the_score = request.GET['score']
        # # get the scores
        # print( je peux pas prenez les ngrams occs avec l'aliased et get_or_create_node )
        # if 'occs' in the_score:
        #     print("OOOOOOOCCCSSSS:")
        #     miamlist = session.query(Node).filter(Node.user_id == request.user.id , Node.parent_id==node_id , Node.type_id == cache.NodeType['MiamList'].id ).first()
        #     print( miamlist )
        #     Miam = aliased(NodeNgram)
        #     ngrams_query = (  session.query(NodeNgram.ngram_id, func.sum(NodeNgram.weight))
        #                     .join(Node, Node.id == NodeNgram.node_id)
        #                     .join(Miam, Miam.ngram_id == NodeNgram.ngram_id)
        #                     .filter(Node.parent_id == node_id, Node.type_id==cache.NodeType['Document'].id)
        #                     .filter(Miam.node_id==miamlist.id)
        #                     .group_by(NodeNgram.ngram_id)
        #                     .all()
        #                 )
        #     for i in ngrams_query:
        #         print(i)

        if 'tfidf' in the_score:
            Tfidf = aliased(NodeNodeNgram)
            tfidf_id = get_or_create_node(nodetype='Tfidf (global)', corpus=corpus).id
            ngrams_query = (ngrams_query.add_column(Tfidf.score.label('tfidf'))
                                        .join(Tfidf, Tfidf.ngram_id == Ngram.id)
                                        .filter(Tfidf.nodex_id == tfidf_id)
                            )
            group_by.append(Tfidf.score)
            results.append('tfidf')

        if 'cvalue' in the_score:
            Cvalue = aliased(NodeNodeNgram)
            cvalue_id = get_or_create_node(nodetype='Cvalue', corpus=corpus).id
            ngrams_query = (ngrams_query.add_column(Cvalue.score.label('cvalue'))
                                        .join(Cvalue, Cvalue.ngram_id == Ngram.id)
                                        .filter(Cvalue.nodex_id == cvalue_id)
                            )
            group_by.append(Cvalue.score)
            results.append('cvalue')

        if 'specificity' in the_score:
            Spec = aliased(NodeNodeNgram)
            spec_id = get_or_create_node(nodetype='Specificity', corpus=corpus).id
            ngrams_query = (ngrams_query.add_column(Spec.score.label('specificity'))
                                        .join(Spec, Spec.ngram_id == Ngram.id)
                                        .filter(Spec.nodex_id == spec_id)
                            )
            group_by.append(Spec.score)
            results.append('specificity')

        order_query = request.GET.get('order', False)
        if order_query == 'cvalue':
            ngrams_query = ngrams_query.order_by(desc(Cvalue.score))
        elif order_query == 'tfidf':
            ngrams_query = ngrams_query.order_by(desc(Tfidf.score))
        elif order_query  == 'specificity':
            ngrams_query = ngrams_query.order_by(desc(Spec.score))

        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))

        ngrams_query = (ngrams_query.filter(Node.parent_id == node_id)
                        .group_by(Ngram.id, Ngram.terms, *group_by)
                        )

        if request.GET.get('ngram_id', False) != False:
            ngram_id = int(request.GET['ngram_id'])
            Group = aliased(NodeNgramNgram)
            group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
            ngrams_query = (ngrams_query.join(Group, Group.ngramx_id == ngram_id )
                                        .filter(Group.node_id == group_id)
                                        .filter(Group.ngramx_id == ngram_id)
                            )

        # filters by list type (soon list_id to factorize it in javascript)
        list_query = request.GET.get('list', 'miam')
        list_id = request.GET.get('list_id', False)
        if list_query == 'miam':
            Miam = aliased(NodeNgram)
            miam_id = get_or_create_node(nodetype='MiamList', corpus=corpus).id
            ngrams_query = (ngrams_query.join(Miam, Miam.ngram_id == Ngram.id )
                                        .filter(Miam.node_id == miam_id)
                            )
        elif list_query == 'stop':
            Stop = aliased(NodeNgram)
            stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id
            ngrams_query = (ngrams_query.join(Stop, Stop.ngram_id == Ngram.id )
                                        .filter(Stop.node_id == stop_id)
                            )
        elif list_query == 'map':
        # ngram could be in ngramx_id or ngramy_id
            CoocX = aliased(NodeNgramNgram)
            CoocY = aliased(NodeNgramNgram)
            cooc_id = get_or_create_node(nodetype='Cooccurrence', corpus=corpus).id
            ngrams_query = (ngrams_query.join(CoocX, CoocX.ngramx_id == Ngram.id )
                                        .join(CoocY, CoocY.ngramy_id == Ngram.id)
                                        .filter(CoocX.node_id == cooc_id)
                                        .filter(CoocY.node_id == cooc_id)
                            )
        elif list_id != False:
            list_id = int(list_id)
            node = session.query(Node).filter(Node.id==node_id).first()
            if node.type_id == cache.NodeType['StopList'].id or node.type_id == cache.NodeType['MiamList'].id:
                List = aliased(NodeNgram)
                ngrams_query = (ngrams_query.join(List, List.ngram_id == Ngram.id )
                                            .filter(List.node_id == node.id)
                                )
            elif node.type_id == cache.NodeType['Cooccurrence'].id:
                CoocX = aliased(NodeNgramNgram)
                CoocY = aliased(NodeNgramNgram)
                ngrams_query = (ngrams_query.join(CoocX, CoocX.ngramx_id == Ngram.id )
                                            .join(CoocY, CoocY.ngramy_id == Ngram.id)
                                            .filter(CoocX.node_id == node.id)
                                            .filter(CoocY.node_id == node.id)
                                )

        total = ngrams_query.count()

        output = []
        for ngram in ngrams_query[offset : offset+limit]:
            info = {}
            try: info["id"] = ngram.id
            except: pass
            try: info["terms"] = ngram.terms
            except: pass
            try: info["tfidf"] = ngram.tfidf
            except: pass
            try: info["cvalue"] = ngram.cvalue
            except: pass
            try: info["specificity"] = ngram.specificity
            except: pass

            output.append( info )


        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
                          },
            'data': output,
                               })

    def post(self , request , node_id ):
        return JsonHttpResponse(["POST","ok"])

    def delete(self , request , node_id ):
        print(node_id)
        return JsonHttpResponse(["DELETE","ok"])

class Group(APIView):
    '''
    REST API to manage groups of Ngrams
    Groups can be synonyms, a cathegory or ngrams groups with stems or lems.
    '''
    def get_group_id(self , node_id):
        node_id = int(node_id)
        corpus = session.query(Node).filter(Node.id==node_id).first()
        group = get_or_create_node(corpus=corpus, nodetype='Group')
        return(group.id)

    def get(self, request, corpus_id):
        # query ngrams
        group_id = self.get_group_id(corpus_id)
        #api/node/$corpus_id/ngrams?ngram_id=12
        # ngram_id = 1 #request.GET.get('ngram_id', False)
        # ngram_id = int(node_id)
        
        # #api/node/$corpus_id/ngrams?all=True
        # all_option = request.GET.get('all', False)
        # all_option = 1 #int(all_option)
        

        # IMPORTANT: Algorithm for getting the groups:
        #   1. pairs_list <- Get all pairs from get_group_id()
        #   2. G  <- Do a non-directed graph of pairs_list
        #   3. DG <- Do a directed graph of pairs_list
        #   4. cliques_list <- find_cliques of G
        #   5. groups <- Iterate in sinonims_cliques and set the mainNode per each clique: take the highest max_outdegree-node of each clique, using DG
        
        import networkx as nx
        G = nx.Graph()
        DG = nx.DiGraph()
        ngrams_ngrams = (session
                .query(NodeNgramNgram)
                .filter(NodeNgramNgram.node_id==group_id)
            )
        # ngramy_id=476996, score=1.0, node_id=75081, id=1282846, ngramx_id=493431
        for ng in ngrams_ngrams:
            # n_x = ( session.query(Ngram).filter(Ngram.id==ng.ngramx_id) ).first()
            # n_y = ( session.query(Ngram).filter(Ngram.id==ng.ngramy_id) ).first()
            G.add_edge( ng.ngramx_id , ng.ngramy_id )
            DG.add_edge( ng.ngramx_id , ng.ngramy_id )  

        # group = dict(list())
        sinonims_cliques = nx.find_cliques( G )
        # for nn in ngrams_ngrams.all():
        #     group[nn.ngramx_id] = group.get(nn.ngramx_id, []) + [nn.ngramy_id]
        
        groups = { "nodes": {} , "links": {} }
        for clique in sinonims_cliques:
            max_deg = -1
            mainNode = -1
            mainNode_sinonims = []
            for node in clique:
                groups["nodes"][node] = False
                node_outdeg = DG.out_degree(node)
                if node_outdeg>max_deg:
                    max_deg = node_outdeg
                    mainNode = node
            for node in clique:
                if mainNode!=node:
                    mainNode_sinonims.append( node )
            groups["links"][ mainNode ] = mainNode_sinonims

        # for i in groups["nodes"]:
        #     print(i)
        ngrams = [int(i) for i in list(groups["nodes"].keys())]

        groups["nodes"] = get_occtfidf( ngrams , request.user.id , corpus_id , "Group")
        
        return JsonHttpResponse(groups)
   
    def post(self, request, node_id):
        return JsonHttpResponse( ["hola" , "mundo"] )

    def delete(self, request, corpus_id):
        
        # input validation
        input = validate(request.DATA, {'data' : {'source': int, 'target': list}})
        
        group_id = get_group_id(corpus_id)

        for data in input['data']:

            if data['source'] > 0 and len(data['target']) > 0:
                for target_id in data['target']:
                    (session.query(NodeNgramNgram)
                            .filter(NodeNgramNgram.node_id==group_id)
                            .filter(NodeNgramNgram.ngramx_id==data['source'])
                            .delete()
                    )
                return JsonHttpResponse(True, 201)
            else:
                raise APIException('Missing parameter: "{\'data\' : [\'source\': Int, \'target\': [Int]}"', 400)

    def put(self , request , corpus_id ):

        group_rawreq = dict(request.data)
        
        GDict = []
        group_new = {}
        for g in group_rawreq:
            gdict = []
            mainform = int(g.replace("[]",""))
            gdict.append(mainform)
            group_new[mainform] = list(map(int, group_rawreq[g]))
            for subform in group_new[mainform]:
                gdict.append(subform)
            GDict.append( gdict )
        existing_group_id = self.get_group_id(corpus_id)
        grouped_ngrams = (session
                .query(NodeNgramNgram)
                .filter(NodeNgramNgram.node_id==existing_group_id)
            )
 

        # [ - - - new group = old clique + new clique - - - ] #
        NewGroups = {}
        Rels_2_delete = {}
        for ng in grouped_ngrams:
            print(ng)
            for i in range(len(GDict)):
                clique_i = GDict[i]
                neighbours = {}
                for node in clique_i:
                    if node==ng.ngramx_id:
                        neighbours[ng.ngramy_id] = True
                    if node==ng.ngramy_id:
                        neighbours[ng.ngramx_id] = True
                if len(list(neighbours.keys()))>0:
                    voisinage = {}
                    for node_ in clique_i:
                        voisinage[node_] = True
                    for node_ in neighbours:
                        voisinage[node_] = True
                    clique_i = list(voisinage.keys())
                    Rels_2_delete[ng.id] = True

                if i not in NewGroups:
                    NewGroups[i] = {}
                for node in clique_i:
                    NewGroups[i][node] = True

        for i in NewGroups:
            NewGroups[i] = list(NewGroups[i].keys())
        # [ - - - / new group = old clique + new clique - - - ] #

        # [ - - - considering main form of the query - - - ] #
        for i in range(len(GDict)):
            ordered = []
            for j in range(len(NewGroups[i])):
                if NewGroups[i][j]!=GDict[i][0]:
                    ordered.append( NewGroups[i][j] )
            NewGroups[i] = [ GDict[i][0] ] + ordered
        # [ - - - / considering main form of the query - - - ] #



        # [ - - - deleting old clique - - - ] #
        for rel_id in Rels_2_delete:
            session.query(NodeNgramNgram).filter(NodeNgramNgram.id==rel_id ).delete()
        session.commit()
        # [ - - - / deleting old clique - - - ] #


        # [ - - - doing links of new clique and adding to DB - - - ] #
        from itertools import combinations
        for i in NewGroups:
            edges = combinations(NewGroups[i], 2)
            for n in edges:
                n1=n[0]
                n2=n[1]
                nodengramngram = NodeNgramNgram(node_id=existing_group_id, ngramx_id=n1 , ngramy_id=n2, score=1.0)
                session.add(nodengramngram)
        session.commit()
        # [ - - - / doing links of new clique and adding to DB - - - ] #


        # import networkx as nx
        # G = nx.Graph()
        # DG = nx.DiGraph()

        # for ng in grouped_ngrams:
        #     n_x = ( session.query(Ngram).filter(Ngram.id==ng.ngramx_id) ).first()
        #     n_y = ( session.query(Ngram).filter(Ngram.id==ng.ngramy_id) ).first()
        #     G.add_edge( str(ng.ngramx_id)+" "+n_x.terms , str(ng.ngramy_id)+" "+n_y.terms  )
        #     DG.add_edge( str(ng.ngramx_id)+" "+n_x.terms , str(ng.ngramy_id)+" "+n_y.terms  ) 

        # # group = dict(list())
        # sinonims_cliques = nx.find_cliques( G )
        # # for nn in ngrams_ngrams.all():
        # #     group[nn.ngramx_id] = group.get(nn.ngramx_id, []) + [nn.ngramy_id]
        
        # groups = { "nodes": {} , "links": {} }
        # for clique in sinonims_cliques:
        #     max_deg = -1
        #     mainNode = -1
        #     mainNode_sinonims = []
        #     for node in clique:
        #         groups["nodes"][node] = False
        #         node_outdeg = DG.out_degree(node)
        #         if node_outdeg>max_deg:
        #             max_deg = node_outdeg
        #             mainNode = node
        #     for node in clique:
        #         if mainNode!=node:
        #             mainNode_sinonims.append( node )
        #     groups["links"][ mainNode ] = mainNode_sinonims
        
        # import pprint
        # print("GDict:")
        # pprint.pprint( GDict )
        # print("")
        # print("NewGroups:")
        # pprint.pprint( NewGroups )
        # print("")
        # print("Ids to delete:")
        # pprint.pprint( Rels_2_delete )
        # print("")
        # print('groups["links"]:')
        # pprint.pprint( groups["links"] )
        # print("")


        return JsonHttpResponse(True, 201)

class Keep(APIView):
    """
    Actions on one existing Ngram in one list
    """
    renderer_classes = (JSONRenderer,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)

    def get (self, request, corpus_id):
        # list_id = session.query(Node).filter(Node.id==list_id).first()
        corpus = session.query(Node).filter( Node.id==corpus_id ).first()
        node_mapList = get_or_create_node(nodetype='MapList', corpus=corpus )
        nodes_in_map = session.query(NodeNgram).filter(NodeNgram.node_id==node_mapList.id ).all()
        results = {}
        for node in nodes_in_map:
            results[node.ngram_id] = True
        return JsonHttpResponse(results)
    
    def put (self, request, corpus_id):
        """
        Add ngrams to map list
        """
        group_rawreq = dict(request.data)
        ngram_2add = [int(i) for i in list(group_rawreq.keys())]
        corpus = session.query(Node).filter( Node.id==corpus_id ).first()
        node_mapList = get_or_create_node(nodetype='MapList', corpus=corpus )
        for ngram_id in ngram_2add:
            map_node = Node_Ngram( weight=1.0, ngram_id=ngram_id , node_id=node_mapList.id)
            session.add(map_node)
            session.commit()
        return JsonHttpResponse(True, 201)

    def delete (self, request, corpus_id):
        """
        Delete ngrams from the map list
        """
        group_rawreq = dict(request.data)
        ngram_2del = [int(i) for i in list(group_rawreq.keys())]
        corpus = session.query(Node).filter( Node.id==corpus_id ).first()
        node_mapList = get_or_create_node(nodetype='MapList', corpus=corpus )
        ngram_2del = session.query(NodeNgram).filter(NodeNgram.node_id==node_mapList.id , NodeNgram.ngram_id.in_(ngram_2del) ).all()
        for map_node in ngram_2del:
            try:
                session.delete(map_node)
                session.commit()
            except:
                pass
        

        return JsonHttpResponse(True, 201)


