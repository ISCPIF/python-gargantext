
import subprocess

import sparql as s

def bool2sparql(query, count=False, limit=None):
    """
    bool2sparql :: String -> Bool -> Int -> String
    Translate a boolean query into a Sparql request
    You need to build bool2sparql binaries before
    See: https://github.com/delanoe/bool2sparql
    """

    bashCommand = ["./bool2sparql-exe","-q",query]

    if count is True :
        bashCommand.append("-c")
    else :
        for command in ["-l", str(limit)] :
            bashCommand.append(command)

    process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE)
    output, error = process.communicate()
    
    if error is not None :
        raise(error)
    else :
        return(output.decode("utf-8"))

def isidore(query, count=False, limit=None):
    """
    isidore :: String -> Bool -> Int -> Either (Dict String) Int
    use sparql-client either to search or to scan
    """

    query = bool2sparql(query, count, limit)
    print(query)
    go = s.Service("https://www.rechercheisidore.fr/sparql/", "utf-8", "GET")

    results = go.query(query)

    if count is False:
        for r in results:
            doc        = dict()
            doc_values = dict()
            doc["url"], doc["id"], doc["title"], doc["date"], doc["abstract"], doc["journal"] = r

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
    query = "ricoeur"
    limit = 2

    for d in isidore(query, limit=limit):
        print(d["abstract"])
    print([n for n in isidore(query, count=True)])

test()

