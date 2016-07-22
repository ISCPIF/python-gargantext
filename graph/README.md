Module Graph Explorer: from text to graph
=========================================

## How to contribute ?
Some solutions:
1) please report to dev@gargantext.org
2) fix with git repo and pull request

## Graph Explorer main 
0) All urls.py of the Graph Explorer
1) Main view of the graph explorer:  views.py
2) Data are retrieved as REST: rest.py
3) Graph is generated (graph.py) through different steps
    a) check the constraints (graph_constraints) in gargantext/constants.py
    b) Cooccurences are computed (in live or asynchronously): cooccurrences.py
    c) Thresold and distances : distances.py
    d) clustering: louvain.py
    c) links between communities: bridgeness.py

4) Additional features:
    a) intersection of graphs: intersection.py


## TODO
1) save parameters in hyperdata
2) graph explorer: 
    * save current graph
2) myGraphs view:
    * progress bar
    * show parameters
    * copy / paste and change some parameters to generate new graph

