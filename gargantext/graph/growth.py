"""
Computes ngram growth on periods
"""

from gargantext.models   import Node, NodeNgram, NodeNodeNgram, NodeNgramNgram
from gargantext.util.db_cache  import cache
from gargantext.util.db  import session, bulk_insert, aliased, \
                                func, get_engine # = sqlalchemy.func like sum() or count()
from datetime             import datetime


def timeframes(start, end):
    """
    timeframes :: String -> String -> (UTCTime, UTCTime, UTCTime)
    """
    
    start = datetime.strptime (str(start), "%Y-%m-%d")
    end   = datetime.strptime (str(end), "%Y-%m-%d")

    date_0 = start - (end - start)
    date_1 = start
    date_2 = end

    return (date_0, date_1, date_2)



def compute_growth(corpus_id, groupList_id, mapList_id, start, end):
    """
    compute_graph :: Int -> UTCTime -> UTCTime -> Int -> Int 
                   -> [(Int, Numeric)]
    
    this function uses SQL function in 
    /srv/gargantext/install/gargamelle/sqlFunctions.sql

    First compute occurrences of ngrams in mapList (with groups) on the first
    period, then on the second and finally returns growth.

    Directly computed with Postgres Database (C) for optimization.
    """
    connection = get_engine()
    
    (date_0, date_1, date_2) = timeframes(start, end)
    
    query = """SELECT * FROM OCC_HIST( {corpus_id}
                                     , {groupList_id}
                                     , {mapList_id}
                                     , '{date_0}'
                                     , '{date_1}'
                                     , '{date_2}'
                                     )
            """.format( corpus_id    = corpus_id
                      , groupList_id = groupList_id
                      , mapList_id   = mapList_id
                      , date_0       = date_0
                      , date_1       = date_1
                      , date_2       = date_2
                      )
    return(connection.execute(query))


