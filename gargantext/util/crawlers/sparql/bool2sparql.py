
import subprocess
import re
from .sparql import Service
from gargantext.settings import BOOL_TOOLS_PATH
#from sparql import Service

def bool2sparql(rawQuery, count=False, offset=None, limit=None):
    """
    bool2sparql :: String -> Bool -> Int -> String
    Translate a boolean query into a Sparql request
    You need to build bool2sparql binaries before
    See: https://github.com/delanoe/bool2sparql
    """
    query = re.sub("\"", "\'", rawQuery)
    bashCommand = [BOOL_TOOLS_PATH + "/bool2sparql-exe","-q",query]

    if count is True :
        bashCommand.append("-c")
    else :
        if offset is not None :
            for command in ["--offset", str(offset)] :
                bashCommand.append(command)
        
        if limit is not None :
            for command in ["--limit", str(limit)] :
                bashCommand.append(command)


    process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE)
    output, error = process.communicate()
    
    if error is not None :
        raise(error)
    else :
        print(output)
        return(output.decode("utf-8"))

def isidore(query, count=False, offset=None, limit=None):
    """
    isidore :: String -> Bool -> Int -> Either (Dict String) Int
    use sparql-client either to search or to scan
    """

    query = bool2sparql(query, count=count, offset=offset, limit=limit)
    
    go = Service("https://www.rechercheisidore.fr/sparql/", "utf-8", "GET")
    results = go.query(query)

    if count is False:
        for r in results:
            doc        = dict()
            doc_values = dict()
            doc["url"], doc["title"], doc["date"], doc["abstract"], doc["source"] = r
            
            for k in doc.keys():
                doc_values[k] = doc[k].value
            
            yield(doc_values)


    else :
        count = []
        for r in results:
            n, = r
            count.append(int(n.value))
        yield count[0]


def test():
    query = "delanoe"
    limit  = 100
    offset = 10

    for d in isidore(query, offset=offset, limit=limit):
        print(d["date"])
    #print([n for n in isidore(query, count=True)])

if __name__ == '__main__':
    test()
