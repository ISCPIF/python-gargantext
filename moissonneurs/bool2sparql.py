
import sparql as s

import subprocess

query = "bourdieu OR habitus"

#def bool2sparql(query, count=False, limit=None):

countCommand = ["./bool2sparql-exe","-q",query,"-c"]
getCommand   = ["./bool2sparql-exe","-q",query,"-l", "100"]

process = subprocess.Popen(countCommand, stdout=subprocess.PIPE)
output, error = process.communicate()

sparqlQuery = output.decode("utf-8")

print(sparqlQuery)


c = s.Service("https://www.rechercheisidore.fr/sparql/", "utf-8", "GET")


# count:
count = []
for r in result:
    (n,) = r
    count.append(n.value)
    #print(n.split('\"')[1])
    #print(r)
print(count[0])
