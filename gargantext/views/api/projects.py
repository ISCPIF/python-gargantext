from .api import * #notamment APIView, check_rights, format_response
from gargantext.util.http import *
from django.core.exceptions import *
from collections import defaultdict
from gargantext.util.toolchain import  *
import copy
from gargantext.util.db import session
from gargantext.models import UserNode

class ProjectList(APIView):
    '''API endpoint that represent a list of projects owned by a user'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    def get(self, request):
        '''GET the projects of a given user'''
        user = cache.User[request.user.id]
        projects = session.query(Node).filter(Node.typename=="PROJECT", Node.user_id== user.id).all()
        if len(projects) == 0:
            return Response({"detail":"No projects Found for this user"}, status=HTTP_404_NOT_FOUND)
        context = format_response(user, projects)
        return Response(context)


    def post(self, request):
        '''CREATE a new project for a given user'''
        user = cache.User[request.user.id]
        try:
            #corpus name
            name = request.data["name"]
        except AttributeError:
            return Response({"detail":"Invalid POST method: \"name\" field is required "}, status = HTTP_406_NOT_ACCEPTABLE)

        if name == "":
            return Response({"detail":"Invalid POST method: \"name\" field is empty "}, status = HTTP_406_NOT_ACCEPTABLE)
        else:
            project = session.query(Node).filter(Node.typename=="PROJECT", Node.name==name).first()
            if project is not None:
                return Response({"detail":"Project with this name already exists", "url":"/projects/%s" %str(project.id)}, status = HTTP_409_CONFLICT)

            else:
                user_node = session.query(UserNode).filter_by(user_id=request.user.id).one_or_none()

                if user_node is None:
                    print("??? Can't find UserNode for %r to create ProjectNode with name %r ???" % (request.user, name))

                new_project = Node(
                    user_id = request.user.id,
                    typename = 'PROJECT',
                    name = name,
                    parent_id = user_node and user_node.id,
                )

                session.add(new_project)
                session.commit()
                return Response({"detail": "Created", "url":"/projects/%s" %str(new_project.id)}, status= HTTP_201_CREATED)

    def delete(self, request):
        ''' DELETE the projects of a given user'''
        user = cache.User[request.user.id]
        projects = session.query(Node).filter(Node.typename=="PROJECT", Node.user_id== user.id).all()
        #for project in projects:
        #    project = check_rights(request, project)
        uids = []
        for node in projects:
            session.delete(node)
            session.commit()
            uids.append(node.id)
        return Response({"detail":"Deleted %i projects" %len(uids)}, status=HTTP_204_NO_CONTENT)


    def put(self, request):
        '''UPDATE EVERY projects of a given user'''
        user = cache.User[request.user.id]
        query = session.query(Node).filter(Node.typename=="PROJECT", Node.user_id== request.user.id).all()
        uids = []
        for node in query:
            for key, val in request.data.items():
                #here verify that key is in accepted modified keys
                if key in ["name", "date", "username"]:
                    if key == "username":
                        #changement de propriétaire
                        user = session.query(Node).filter(Node.typename=="PROJECT", Node.username== username).first()
                        set(node, user_id, user.id)
                    else:
                        setattr(node, key, val)


            #node.name = request.data["name"]
            session.add(node)
            session.commit()
            uids.append(node.id)
        return Response({"detail":"Updated %s projects" %len(uids)}, status=HTTP_202_ACCEPTED)

class ProjectView(APIView):
    '''API endpoint that represent project detail'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    def get(self, request, project_id):
        ''' GET  /api/projects/<project_id> the list of corpora given a project '''
        project = session.query(Node).filter(Node.id == project_id).first()
        if project is None:
            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = HTTP_404_NOT_FOUND)
        check_rights(request, project_id)
        corpus_list = project.children('CORPUS', order=True).all()
        if len(corpus_list) == 0:
            return Response({'detail' : "No corpora found for Project Node #%s" %(project_id) },
                                  status = HTTP_404_NOT_FOUND)
        # resource_list = [(n["name"], n["type"], n["id"]) for n in corpus_list[0].children('RESOURCE', order=True).all()]
        # print(resource_list)
        context = format_response(project, corpus_list)
        return Response(context)

    def delete(self, request, project_id):
        '''DELETE project'''
        node = session.query(Node).filter(Node.id == project_id).first()

        if node is None:

            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = HTTP_404_NOT_FOUND)
        else:
            try:
                check_rights(request, project_id)
            except Exception as e:
                return Response({'detail' : "Unauthorized" %(project_id) },
                                      status= 403)
            session.delete(node)
            session.commit()
            return Response({"detail": "Successfully deleted Node #%s" %project_id}, status= 204)

    def put(self, request, project_id):
        '''UPDATE project '''
        project = session.query(Node).filter(Node.id == project_id).first()

        if project is None:
            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = HTTP_404_NOT_FOUND)
        check_rights(request, project_id)
        params = get_parameters(request)
        # print(params)
        #u_project = deepcopy(project)
        for key, val in params.items():
            if len(val) == 0:
                return Response({"detail":"Invalid POST method: \"%s\" field is empty " %key}, status = HTTP_406_NOT_ACCEPTABLE)
            if key in ["name", "date", "username"]:
                if key == "username":
                    #change ownership
                    #find user
                    #user = session.query(Node).filter(Node.username == username, Node.typename="USER").first()
                    #if user.id
                    pass
                elif key == "name":
                    other = session.query(Node).filter(Node.name == val ).count()
                    if other == 0:
                        setattr(project, key, val)
                    else:
                        return Response({"detail":"Project with this name already exists"}, status = HTTP_409_CONFLICT)
                else:
                    setattr(project, key, val)
        session.add(project)
        session.commit()
        return Response({"detail":"Updated PROJECT #%s" %str(project_id)}, status=HTTP_206_PARTIAL_CONTENT)

    def post(self, request, project_id):
        '''CREATE corpus'''
        project = session.query(Node).filter(Node.id == project_id).first()
        if project is None:
            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = HTTP_404_NOT_FOUND)
        project = check_rights(request, project_id)
        #controling form data
        if not "name" in request.data.keys():
            return Response({'detail' : "CORPUS Node: field name is mandatory" },
                                  status = HTTP_406_NOT_ACCEPTABLE)
        if not "source" in request.data.keys():
            return Response({'detail' : "CORPUS Node: field source is mandatory"},
                                  status = HTTP_406_NOT_ACCEPTABLE)
        corpus_name = request.data["name"]
        corpus_source = request.data["source"]
        if  corpus_name == "":
            return Response({'detail' : "CORPUS Node name can't be empty" },
                                  status = HTTP_406_NOT_ACCEPTABLE)
        corpus = session.query(Node).filter(Node.name == corpus_name, Node.typename == "CORPUS").first()
        if corpus is not None:
            return Response({'detail' : "CORPUS Node with name '%s' already exists" %(corpus_name) },
                                  status = HTTP_409_CONFLICT)

        if  corpus_source == "" or corpus_source == 0  or corpus_source == None:
            return Response({'detail' : "CORPUS Node source can't be empty"},status=HTTP_406_NOT_ACCEPTABLE)

        params = get_parameters(request)
        if "method" not in params.keys():
        #if "method" not in request.data.keys():
            return Response({'detail' : "CORPUS Node has not 'method' parameter"},
                                  status = HTTP_405_METHOD_NOT_ALLOWED)
        #method = request.data["method"]
        method = params["method"]
        if method not in ["parse", "scan", "copy"]:
            return Response({'detail' : "CORPUS Node only parse, scan and copy 'method' are allowed" },
                                  status = HTTP_405_METHOD_NOT_ALLOWED)
        if method == "copy":
            corpus = session.query(Node).filter(Node.id == corpus_source, Node.typename == "CORPUS").first()
            if corpus is None:
                return Response({'detail' : "CORPUS Node #%s doesn't exist. Fail to copy" %(str(corpus_source)) },
                                      status = HTTP_404_NOT_FOUND)
            else:
                #cloned_corpus = {k:v for k,v in corpus if k not in ["user_id", "id", "parent_id"]}
                cloned_corpus = copy.deepcopy(corpus)
                del cloned_corpus.id
                cloned_corpus.parent_id = project_id
                cloned_corpus.user_id = request.user.id
                for child in corpus.get_children():
                    #{k:getattr(corpus, k) for k in ["name", "date", "source", "hyperdata"] }
                    cloned_child = copy.deepcopy(child)
                    del cloned_child["id"]
                    cloned_child["parent_id"] = new_corpus.id

                    cloned_corpus["user_id"] = request.user.id
                    cloned_corpus.add_child(cloned_child)
                session.add(cloned_corpus)
                session.commit()
        #RESOURCE
        source = get_resource(int(corpus_source))
        if source is None:
            return Response({'detail' : "CORPUS Node sourcetype unknown"},
                                  status = HTTP_406_NOT_ACCEPTABLE)
        if method == "parse":
            print('PARSING')
            if not "file" in  request.FILES.keys():
                return Response({'detail' : "CORPUS Node need a file to parse" },
                                      status = HTTP_405_METHOD_NOT_ALLOWED)
            corpus_file = request.FILES['file']
            if "parser" in source.keys():
                corpus = project.add_child(
                    name = request.data["name"],
                    typename = 'CORPUS',
                    #path = corpus_file,
                )
                print("CORPUS #", corpus.id)
                session.add(corpus)
                session.commit()
                resource = Node(
                    name = source["name"],
                    typename = 'RESOURCE',
                    parent_id = corpus.id,
                    hyperdata = {"type": source["type"],
                                "method": method,
                                "file": upload(corpus_file),
                                "query": None}
                )
                session.add(resource)
                session.commit()
                return Response({"detail":"Parsing corpus #%s of type #%s" %(str(corpus.id), resource.name)}, 200)
            else:
                return Response({"detail":"No Parser found for this corpus #%s of type %s" %(str(corpus.id), resource.name)}, 405)
        elif method =="scan":
            if "crawler" in source.keys():
                if not "query" in  request.data.keys():
                    #corpus_file = request.FILES['file']
                    return Response({'detail' : "CORPUS Node need a query to scan" },
                                          status = HTTP_405_METHOD_NOT_ALLOWED)
                query = request.data['query']
                corpus = project.add_child(
                    name = request.data["name"],
                    typename = 'CORPUS',
                )
                resource = Node(
                    name = source["name"],
                    typename = 'RESOURCE',
                    parent_id = corpus.id,
                    user_id = request.user_id,
                    hyperdata = {"type": source["type"],
                                "method": method,
                                "file": None,
                                "query": query}
                )
                session.add(resource)
                session.commit()


                return Response({'detail': "CORPUS #%s created" %corpus.id}, status = HTTP_201_CREATED)
        else:
            return Response({'detail' : "CORPUS Node only parse, scan and copy 'method' are allowed" },
                                  status = HTTP_405_METHOD_NOT_ALLOWED)


    def old_post(self, request, project_id):
        form = self._validate_form(request)
        #get params

        method = form["method"]
        if method in ["parse", "scan", "copy"]:
            #Le corpus et la resource n'existent pas
            # [HACK]
            # creation d'un corpus
            corpus = Node(    typename = 'CORPUS',
                          user_id = request.user_id,
                          parent_id = project.id,
                          name = form["name"],
                        )
            session.add(corpus)
            session.commit()
            # creation d'une resource
            try:
                if method == "parse":
                    form["file"] = request.FILES['file']

                action = getattr(self, "_"+method)
                #toutes les actions sauf scan suppriment la resource?
                #et remontent l'info dans corpus
                if action(corpus, form):

                    # transferer les infos resource dans le corpus
                    documents = session.query(Node).filter(Node.typename=="DOCUMENT", Node.user_id== user.id, Node.parent_id==corpus.id).all()
                    response_data = {
                        "records": format_records(documents),
                        "resource": format_records([resource]),
                        "parent": format_parent(project),
                        "count":len(documents)
                    }
                    return Response(response_data, 200)
                else:
                    raise APIException("Error with ", method)

            except Exception as e:
                raise APIException(e)

        else:

                #Le corpus existe et la resource doit être mise à jour
                corpus = session.query(Node).filter(Node.typename=="CORPUS", Node.parent_id== project.id, Node.name == form["corpus_name"]).first()
                source = get_resource(form["source"])
                if corpus is None:
                    return Response("CORPUS not found", 404)
                #[HACK] one corpus one resource by Resourcetype_name

                resource = session.query(Node).filter(Node.typename=="RESOURCE",
                                                        Node.parent_id== corpus.id,
                                                        Node.corpus_name == form["corpus_name"],
                                                        Node.name == source["name"]
                                                    ).first()
                action = getattr(self, "_"+method)
                if action(resource):
                    # transferer les infos resource dans le corpus
                    if method == "fetch":
                        corpus.sources[resource["name"]].append(resource)
                        session.delete(resource)
                        session.add(corpus)
                        session.commit()
                    else:
                        session.add(resource)
                        session.commit()
                    return Response({"log": "Created", "uids":[corpus.id]}, 200)
                else:
                    session.delete(resource)
                    session.delete(corpus)
                    session.commit()
                    return Response({"log": method+": Error"}, 500)

    def _check_method(self, request):
        METHODS = ["scan", "parse", "sample", "fetch", "copy"]
        try:
            method = get_parameters(request)["method"]
        except AttributeError:
            raise APIException("Precondition failed : You must specify a method", 412)
        if method not in METHODS:
            raise APIException("Method not allowed", 405)
        else:
            return method

    def _validate_form(self, request):
        '''basic validation of the step given each method

        '''
        params = {}
        method = self._check_method(request)
        #parsing a file
        if method == "parse":
            fields = ['source', 'name', "file"]
        #scanning a query => results_nb
        elif method == "scan":
            fields = ['source', 'name', "query"]
        #sampling checking results_nb =>  ids
        #~ elif method == "sample":
            #~ fields = ['source', 'name', "results_nb"]
        #~ #fetching ids => NewParser
        #~ elif method == "fetch":
            #~ fields = ['source', 'name', "ids"]

        #cloning a corpus_id => Corpus
        elif method == "copy":
            fields = ['source', 'name', "corpus_id"]
        for k in fields:
            try:
                if request.data[k] != "" or request.data[k] is not None:
                    params[k] = request.data[k]
                else:
                    raise APIException("Mandatory value %s can't be empty "%str(k), 400)
            except AttributeError:
                raise APIException("Value %s is mandatory" %str(k), 400)

        if len(params) > 0:
            params["method"] = method
            return params
        else:
            raise APIException("Form is empty: %s" %str(k), 404)

    def _sample(self, resource):
        resource = self._find_resource_hyperdata(corpus, form)
        crawlbot = eval(resource.crawler)(resource)
        records = crawlbot.sample()
        #resource.status.insert(0,"sampled")
        resource.ids = records
        corpus.status(action="sample", progress=1, complete=True)
        session.add(corpus)
        session.commit()
        return Response({"uids": [corpus.id]}, status= HTTP_200_OK)

    def _fetch(self, resource):
        '''internal method to fetch from a corpus  the resource.urls >>> resource._parser(urls)'''
        resource = self._find_resource_hyperdata(corpus, form)
        resource.status(action="fetch", progress=1, complete=False)
        crawlbot = eval(resource.typecrawler)(resource)
        #send job to celery
        scheduled(crawlbot.fetch())
        corpus.status(action="fetch", progress=1, complete=True)
        session.add(corpus)
        session.commit()
        return Response({"uids": [corpus.id]}, 200)

    def _copy(self, corpus, form):
        #find the target corpus
        new_corpus = session.query(Node).filter(Node.typename=="CORPUS", Node.corpus_id == form["corpus_id"]).first()
        #get the resource of this corpus and copy it two
        new_resource = self._find_resource_hyperdata(new_corpus, form)
        #copy new_corpus to previously created corpus
        new_resouce.method = "cloned CORPUS #%i" %(new_corpus.id)
        new_corpus.id = corpus.id
        # change new_corpus ownership
        new_corpus.parent_id = corpus.parent_id
        new_corpus.user_id = corpus.user_id
        #get the documents of the existing corpus
        for doc in new_corpus.get_children():
            doc.parent_id = new_corpus.parent_id
            doc.user_id = new_corpus.id
            #store it into corpus
            new_doc = corpus.add_child(doc)
            for ngrams in doc.get_children():
                new_ngrams.parent_id = new_doc.id
                new_ngrams.user_id = new_corpus.user_id
                #store it into corpus
                new_doc.add_child(new_ngrams)
        #save the corpus
        corpus.status(action="copy", progress=1, complete=True)
        session.add(corpus)
        session.commit()
        return Response({"log": "Corpus created", "uids":[corpus.id]}, 202)
    def _scan(self, corpus, form):
        '''internal method to scan a query >> add results_nb to resource as a corpus hyperdata'''
        resource = self._find_resource_hyperdata(corpus, form)
        #corpus_query = check_query(form["query")
        ressource.query = form["query"]
        corpus.status(action="scan", progress=1, complete=False)
        session.add(corpus)
        session.commit()

        crawlbot = eval(resource.crawler)(corpus.id)
        corpus.status(action="scan", progress=2, complete=False)
        session.add(corpus)
        session.commit()

        results_nb = crawlbot.scan_results()
        resource.results_nb = results_nb
        corpus.status(action="scan", progress=2, complete=True)
        code = 200
        session.add(corpus)
        session.commit()
        return Response({"log": "Corpus created", "uids":[corpus.id]}, 200)

    def _parse(self, corpus, form):
        '''internal method to parse a corpus >> resource >> corpus >> docs
        corpus  >> resource (method + file params + parser   )
            ^   >> docs (resource.defaultlang <--------|     )
            |   >> ngrams
            |------- le tout rappatrié dans corpus
        '''
        #1. creating a resource
        resource = {}
        resource = Node(
                                user_id = corpus.user_id,
                                parent_id = corpus.id,
                                typename = "RESOURCE",
                                #corpus_name = form["name"],
                                )
        resource.method = form["method"]
        resource.path = upload(form['file'])
        #mapping the default attribute of a given source from constant RESOURCETYPE
        for k, v in get_resource(int(form["source"])).items():
            setattr(resource, k, v)
        resource.status(action="parse", progress=1, complete=False)
        session.add(resource)
        session.commit()
        try:
            workflow(resource)
        except Exception as e:
            print("=======except dans _parse===========")
            print(e)
            from traceback import print_tb
            print_tb(e.__traceback__)
            print("====================================")
        return True
