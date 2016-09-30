Module Graph Explorer: from text to graph
=========================================


## Graph Explorer main 
0) All urls.py of the Graph Explorer

1) Main view of the graph explorer:  views.py
    -> Graph Explorer
    -> My graph View
    -> REST API to get Data

2) Graph is generated (graph.py) through different steps
    a) check the constraints (graph_constraints) in gargantext/constants.py
    b) Data are retrieved as REST
            rest.py: check REST parameters
    c) graph.py:
        get_graph: check Graph parameters
        compute_graph: compute graph
            1) Cooccurences are computed (in live or asynchronously): cooccurrences.py
            2) Thresold and distances : distances.py
            3) clustering: louvain.py
            4) links between communities: bridgeness.py
    d) compress graph before returning it: utils.py

4) Additional features:
    a) intersection of graphs: intersection.py


## How to contribute ?
Some solutions:
1) please report to dev@gargantext.org
2) fix with git repo and pull request

## TODO
myGraphs view:
    * progress bar
    * Show already computed graphs vs to be computed with parameters
    * show parameters
    * copy / paste and change some parameters to generate new graph



















































