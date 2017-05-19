
import subprocess

from .sparql import Service
#from sparql import Service

def bool2sparql(query, count=False, offset=None, limit=None):
    """
    bool2sparql :: String -> Bool -> Int -> String
    Translate a boolean query into a Sparql request
    You need to build bool2sparql binaries before
    See: https://github.com/delanoe/bool2sparql
    """

    bashCommand = ["/srv/gargantext/gargantext/util/crawlers/sparql/bool2sparql-exe","-q",query]

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
        return(output.decode("utf-8"))

def isidore(query, count=False, offset=None, limit=None):
    """
    isidore :: String -> Bool -> Int -> Either (Dict String) Int
    use sparql-client either to search or to scan
    """

    query = bool2sparql(query, count=count, offset=offset, limit=limit)
    print(query)
    
    go = Service("https://www.rechercheisidore.fr/sparql/", "utf-8", "GET")
    results = go.query(query)

    if count is False:
        for r in results:
            doc        = dict()
            doc_values = dict()
            doc["url"], doc["id"], doc["title"], doc["date"], doc["abstract"], doc["source"] = r
            
            print(doc)
            for k in doc.keys():
                doc_values[k] = doc[k].value
            print(doc_values)
            
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
