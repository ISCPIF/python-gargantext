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
      - specclusion_id (ngram inclusion by cooc specificity -- ranking factor)
      - genclusion_id (ngram inclusion by cooc genericity -- ranking factor)
      - grouplist_id (filtering grouped ones)
      - overwrite_id: optional if preexisting MAPLIST node to overwrite

      + 3 params to modulate the terms choice
        - limit for the amount of picked terms
        - monograms_part: a ratio of terms with only one lexical unit to keep
                          (multigrams quota = limit * (1-monograms_part))
        - genclusion_part: a ratio of terms with only one lexical unit to keep
                           (speclusion quota = limit * (1-genclusion_part))
    '''

    if not (mainlist_id and specclusion_id and genclusion_id and grouplist_id):
        raise ValueError("Please provide mainlist_id, specclusion_id, genclusion_id and grouplist_id")

    quotas = {'topgen':{}, 'topspec':{}}
    genclusion_limit = round(limit * genclusion_part)
    speclusion_limit = limit - genclusion_limit
    quotas['topgen']['monograms'] = round(genclusion_limit * monograms_part)
    quotas['topgen']['multigrams'] = genclusion_limit - quotas['topgen']['monograms']
    quotas['topspec']['monograms'] = round(speclusion_limit * monograms_part)
    quotas['topspec']['multigrams'] = speclusion_limit - quotas['topspec']['monograms']

    print("MAPLIST quotas:", quotas)

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
    ScoreGen=aliased(NodeNgram)

    # ngram with both ranking factors spec and gen
    query = (session.query(
                        ScoreSpec.ngram_id,
                        ScoreSpec.weight,
                        ScoreGen.weight,
                        Ngram.n
                        )
                .join(Ngram, Ngram.id == ScoreSpec.ngram_id)
                .join(ScoreGen, ScoreGen.ngram_id == ScoreSpec.ngram_id)
                .filter(ScoreSpec.node_id == specclusion_id)
                .filter(ScoreGen.node_id == genclusion_id)

                # we want only terms within mainlist
                .join(MainlistTable, Ngram.id == MainlistTable.ngram_id)
                .filter(MainlistTable.node_id == mainlist_id)

                # we remove all ngrams matching an ngram2_id from the synonyms
                .outerjoin(IsSubform,
                           IsSubform.c.ngram2_id == ScoreSpec.ngram_id)
                .filter(IsSubform.c.ngram2_id == None)

                # specificity-ranked
                .order_by(desc(ScoreSpec.weight))
            )

    # format in scored_ngrams array:
    # -------------------------------
    # [(37723,    8.428, 14.239,   3    ),   etc]
    #   ngramid   wspec   wgen    nwords
    scored_ngrams = query.all()
    n_ngrams = len(scored_ngrams)

    if n_ngrams == 0:
        raise ValueError("No ngrams in cooc table ?")
        #return
    # results, with same structure as quotas
    chosen_ngrams = {
                     'topgen':{'monograms':[], 'multigrams':[]},
                     'topspec':{'monograms':[], 'multigrams':[]}
                     }

    # specificity and genericity are rather reverse-correlated
    # but occasionally they can have common ngrams (same ngram well ranked in both)
    # => we'll use a lookup table to check if we didn't already get it
    already_gotten_ngramids = {}

    # 2 loops to fill spec-clusion then gen-clusion quotas
    #   (1st loop uses order from DB, 2nd loop uses our own sort at end of 1st)
    for rkr in ['topspec', 'topgen']:
        got_enough_mono = False
        got_enough_multi = False
        all_done = False
        i = -1
        while((not all_done) and (not (got_enough_mono and got_enough_multi))):
            # retrieve sorted ngram n° i
            i += 1
            (ng_id, wspec, wgen, nwords) = scored_ngrams[i]

            # before any continue case, we check the next i for max reached
            all_done = (i+1 >= n_ngrams)

            if ng_id in already_gotten_ngramids:
                continue

            # NB: nwords could be replaced by a simple search on r' '
            if nwords == 1:
                if got_enough_mono:
                    continue
                else:
                    # add ngram to results and lookup
                    chosen_ngrams[rkr]['monograms'].append(ng_id)
                    already_gotten_ngramids[ng_id] = True
            # multi
            else:
                if got_enough_multi:
                    continue
                else:
                    # add ngram to results and lookup
                    chosen_ngrams[rkr]['multigrams'].append(ng_id)
                    already_gotten_ngramids[ng_id] = True

            got_enough_mono = (len(chosen_ngrams[rkr]['monograms']) >= quotas[rkr]['monograms'])
            got_enough_multi = (len(chosen_ngrams[rkr]['multigrams']) >= quotas[rkr]['multigrams'])

        # at the end of the first loop we just need to sort all by the second ranker (gen)
        scored_ngrams = sorted(scored_ngrams, key=lambda ng_infos: ng_infos[2], reverse=True)

    obtained_spec_mono = len(chosen_ngrams['topspec']['monograms'])
    obtained_spec_multi = len(chosen_ngrams['topspec']['multigrams'])
    obtained_gen_mono = len(chosen_ngrams['topgen']['monograms'])
    obtained_gen_multi = len(chosen_ngrams['topgen']['multigrams'])
    obtained_total = obtained_spec_mono   \
                    + obtained_spec_multi \
                    + obtained_gen_mono   \
                    + obtained_gen_multi
    print("MAPLIST: top_spec_monograms =",  obtained_spec_mono)
    print("MAPLIST: top_spec_multigrams =", obtained_spec_multi)
    print("MAPLIST: top_gen_monograms =",   obtained_gen_mono)
    print("MAPLIST: top_gen_multigrams =",  obtained_gen_multi)
    print("MAPLIST: kept %i ngrams in total " % obtained_total)

    obtained_data = chosen_ngrams['topspec']['monograms']      \
                    + chosen_ngrams['topspec']['multigrams']   \
                    + chosen_ngrams['topgen']['monograms']     \
                    + chosen_ngrams['topgen']['multigrams']

    # NEW MAPLIST NODE
    # -----------------
    # saving the parameters of the analysis in the Node JSON
    new_hyperdata = { 'corpus': corpus.id,
                      'limit' : limit,
                      'monograms_part' :  monograms_part,
                      'genclusion_part' : genclusion_part,
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
    datalist = UnweightedList(obtained_data)

    # save
    datalist.save(the_id)

    # dbg.show('MapList computed')

    return the_id
