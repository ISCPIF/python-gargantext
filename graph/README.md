Module Graph Explorer: from text to graph
=========================================

Maintainer: If you see bugs, please report to team@gargantext.org

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
