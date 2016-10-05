"""
Creates a filtering list for corpus ngrams.
(implementation: regexp + "master" stoplist)
"""

from gargantext.models        import User, Node, Ngram, NodeNgram
from gargantext.util.db       import session, func
from gargantext.constants     import LISTTYPES
from re                       import compile
from sqlalchemy               import desc

def is_stop_word(ngram, stop_words=None):
    '''
    ngram :: (Int, String) => (ngram_id, ngram_terms)
    stop_words :: Set of String
    (to avoid SQL query each time is_stop_word is invoked, get in as parameter)
    '''
    word = ngram[1]

    if word in stop_words:
        return(True)

    compiled_regexes = []   # to compile them only once
    for regex in [
              "^.{1,2}$"
            , "(.*)\d(.*)"
            # , "(.*)(\.)(.*)"         trop fort (enlève les sigles !)
            , "(.*)(\,)(.*)"
            , "(.*)(< ?/?p ?>)(.*)"       # marques de paragraphes
            , "(.*)\b(xx|xi|xv)\b(.*)"
            , "(.*)(result)(.*)"
            , "(.*)(year|année|nombre|moitié)(.*)"
            , "(.*)(temps)(.*)"
            , "(.*)(%)(.*)"
            , "(.*)(\{)(.*)"
            , "(.*)(terme)(.*)"
            , "(.*)(différent)(.*)"
            , "(.*)(travers)(.*)"
            # academic stamps
            , ".*elsevier.*"
            , ".*wiley.*"
            , ".*springer.*"
            , ".*university press.*"
            # academic terms when alone ~~> usually not informative
            , "hypothes[ie]s$"
            , "analys[ie]s$"
            , "bas[ie]s$"
            , "online$"
            , "importance$"
            , "uses?$"
            , "cases?$"
            , "effects?$"
            , "times?$"
            , "methods?$"
            , "types?$"
            , "evidences?$"
            , "findings?$"
            , "relations?$"
            , "terms?$"
            , "procedures?$"
            , "factors?$"
            , "reports?$"
            , "changes?$"
            , "facts?$"
            , "others?$"
            , "applications?$"
            , "periods?$"
            , "investigations?$"
            , "orders?$"
            , "forms?$"
            , "conditions?$"
            , "situations?$"
            , "papers?$"
            , "relationships?$"
            , "values?$"
            , "areas?$"
            , "techniques?$"
            , "means?$"
            , "conclusions?$"
            , "comparisons?$"
            , "parts?$"
            , "amounts?$"
            , "aims?$"
            , "lacks?$"
            , "issues?$"
            , "ways?$"
            , "ranges?$"
            , "models?$"
            , "articles?$"
            , "series?$"
            , "totals?$"
            , "influences?$"
            , "journals?$"
            , "rules?$"
            , "persons?$"
            , "abstracts?$"
            , "(?:book)? reviews?$"
            , "process(?:es)?$"
            , "approach(?:es)?$"
            , "theor(?:y|ies)?$"
            , "methodolog(?:y|ies)?$"
            , "similarit(?:y|ies)?$"
            , "possibilit(?:y|ies)?$"
            , "stud(?:y|ies)?$"
            # non-thematic or non-NP expressions
            , "none$"
            , "other(?: hand)?$"
            , "whereas$"
            , "usually$"
            , "and$"
            # , "vol$"
            , "eds?$"
            , "ltd$"
            , "copyright$"
            , "e-?mails?$"
            , ".*="
            , "=.*"
            , "further(?:more)?$"
            , "(.*)(:|\|)(.*)"
            ] :
        compiled_regexes.append(compile(regex))

    for format_regex in compiled_regexes:
        if format_regex.match(word):
            # print("STOPLIST += '%s' (regex: %s)" % (word, format_regex.pattern))
            return(True)

    return False

def create_gargantua_resources():
    gargantua_id = session.query(User.id).filter(User.username=="gargantua").first()
    project = Node(
            name="Resources",
            user_id=gargantua_id,
            typename="PROJECT")
    stopList = Node(name="STOPLIST", parent_id=project.id, user_id=gargantua_id, typename="STOPLIST")
    session.add(project)
    session.add(stopList)
    session.commit()

def do_stoplist(corpus, overwrite_id=None):
    '''
    Create list of stop words.
    TODO do a function to get all stop words with social scores

    Parameters:
        - overwrite_id: optional preexisting STOPLIST node to overwrite
    '''

    # Get preexisting StopList if provided in overwrite_id param
    if overwrite_id:
        stoplist_id = overwrite_id
    # At this step of development, a new StopList should be created
    else:
        stoplist = corpus.add_child(
                    name="Stoplist (in:%s)" % corpus.id,
                    typename="STOPLIST"
                   )
        session.add(stoplist)
        session.commit()
        stoplist_id = stoplist.id

    # Get common resources, all common StopWords on the platform
    ## First get the id of the StopList of Gargantua super user
    gargantua_id = session.query(User.id).filter(User.username=="gargantua").first()
    rootStopList_id = session.query(Node.id).filter(
            Node.user_id  == gargantua_id,
            Node.typename == "STOPLIST"
            ).first()
    ## Then get all the stop words
    ## stop_words :: [String]
    stop_words = (session.query(Ngram.terms)
                         .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                         .filter(NodeNgram.node_id == rootStopList_id)
                         .all()
                 )

    # print([n for n in stop_words])

    ## Get the ngrams
    ## ngrams :: [(Int, String, Int)]
    ngrams = (session.query( Ngram.id, Ngram.terms)
            .join( NodeNgram, NodeNgram.ngram_id == Ngram.id )
            .join( Node, Node.id == NodeNgram.node_id )
            .filter( Node.parent_id == corpus.id,
                     Node.typename == "DOCUMENT")
            .group_by( Ngram.id )
            #.limit(limit)
            .all()
            )

    ngrams_to_stop = filter(
            lambda x: is_stop_word(x,stop_words=stop_words), ngrams
        )

    # print([n for n in ngrams_to_stop])

    stop = LISTTYPES["STOPLIST"]({ n[0] : -1 for n in ngrams_to_stop})
    # stop = LISTTYPES["STOPLIST"]([n[0] for n in ngrams_to_stop])
    stop.save(stoplist_id)
    return stoplist_id
