"""
Selects a subset of corpus ngrams to use in the graph map.
"""

from gargantext.models.ngrams import Node, Ngram, NodeNgram, \
                                     NodeNgramNgram, NodeNodeNgram
from gargantext.util.db       import session, aliased, func
from gargantext.util.db_cache import cache
from gargantext.util.lists    import UnweightedList
from sqlalchemy               import desc, asc
from gargantext.constants     import DEFAULT_MAPLIST_MAX,\
                                     DEFAULT_MAPLIST_GENCLUSION_RATIO,\
                                     DEFAULT_MAPLIST_MONOGRAMS_RATIO

def do_maplist(corpus,
               overwrite_id = None,
               mainlist_id  = None,
               specclusion_id = None,
               genclusion_id = None,
               grouplist_id = None,
               limit=DEFAULT_MAPLIST_MAX,
               genclusion_part=DEFAULT_MAPLIST_GENCLUSION_RATIO,
               monograms_part=DEFAULT_MAPLIST_MONOGRAMS_RATIO
               ):
    '''
    According to Genericity/Specificity and mainlist

    Parameters:
      - mainlist_id (starting point, already cleaned of stoplist terms)
      - specclusion_id (inclusion by cooc specificity -- ranking factor)
      - genclusion_id (inclusion by cooc genericity -- ranking factor)
      - grouplist_id (filtering grouped ones)
      - overwrite_id: optional if preexisting MAPLIST node to overwrite

      + 2 constants to modulate the terms choice
        - limit for the amount of picked terms
        - monograms_part: a ratio of terms with only one lexical unit to keep
    '''

    if not (mainlist_id and specclusion_id and genclusion_id and grouplist_id):
        raise ValueError("Please provide mainlist_id, specclusion_id, genclusion_id and grouplist_id")

    monograms_limit = round(limit * monograms_part)
    multigrams_limit = limit - monograms_limit
    print("MAPLIST: monograms_limit =", monograms_limit)
    print("MAPLIST: multigrams_limit = ", multigrams_limit)

    #dbg = DebugTime('Corpus #%d - computing Miam' % corpus.id)

    MainlistTable = aliased(NodeNgram)

    IsSubform = (session
                            # we want only secondary terms (ngram2)
                            # to be able to filter them out
                            .query(NodeNgramNgram.ngram2_id)
                            .filter(NodeNgramNgram.node_id == grouplist_id)
                            .subquery()
                         )

    ScoreSpec=aliased(NodeNgram)

    # specificity-ranked
    query = (session.query(ScoreSpec.ngram_id)
                .join(Ngram, Ngram.id == ScoreSpec.ngram_id)
                .filter(ScoreSpec.node_id == specclusion_id)

                # we want only terms within mainlist
                .join(MainlistTable, Ngram.id == MainlistTable.ngram_id)
                .filter(MainlistTable.node_id == mainlist_id)

                # we remove all ngrams matching an ngram2_id from the synonyms
                .outerjoin(IsSubform,
                           IsSubform.c.ngram2_id == ScoreSpec.ngram_id)
                .filter(IsSubform.c.ngram2_id == None)
            )

    # TODO: move these 2 pools up to mainlist selection
    top_monograms = (query
                .filter(Ngram.n == 1)
                .order_by(desc(ScoreSpec.weight))
                .limit(monograms_limit)
                .all()
               )

    top_multigrams = (query
                .filter(Ngram.n >= 2)
                .order_by(desc(ScoreSpec.weight))
                .limit(multigrams_limit)
                .all()
               )
    obtained_mono  = len(top_monograms)
    obtained_multi = len(top_multigrams)
    obtained_total = obtained_mono + obtained_multi
    # print("MAPLIST: top_monograms =", obtained_mono)
    # print("MAPLIST: top_multigrams = ", obtained_multi)
    print("MAPLIST: kept %i ngrams in total " % obtained_total)

    # NEW MAPLIST NODE
    # -----------------
    # saving the parameters of the analysis in the Node JSON
    new_hyperdata = { 'corpus': corpus.id,
                      'limit' : limit,
                      'monograms_part' : monograms_part,
                     'monograms_result' : obtained_mono/obtained_total if obtained_total != 0 else 0
                    }
    if overwrite_id:
        # overwrite pre-existing node
        the_maplist = cache.Node[overwrite_id]
        the_maplist.hyperdata = new_hyperdata
        the_maplist.save_hyperdata()
        session.commit()
        the_id = overwrite_id
    else:
        # create a new maplist node
        the_maplist = corpus.add_child(
                        name="Maplist (in %i)" % corpus.id,
                        typename="MAPLIST",
                        hyperdata = new_hyperdata
                    )
        session.add(the_maplist)
        session.commit()
        the_id = the_maplist.id

    # create UnweightedList object and save (=> new NodeNgram rows)
    datalist = UnweightedList(
                   [res.ngram_id for res in top_monograms + top_multigrams]
               )

    # save
    datalist.save(the_id)

    # dbg.show('MapList computed')

    return the_id
