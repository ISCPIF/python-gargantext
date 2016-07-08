/* 
Author: Samuel Castillo (github.com/pksm3)  samuel.castillo@iscpif.fr
This is a javascript implementation of the CPM overlapping-community detection algorithm, Palla et al. 2008 http://dx.doi.org/10.1007/978-3-540-69395-6_9
Based on 
 - http://sociograph.blogspot.fr/2011/11/clique-percolation-in-few-lines-of.html
 - https://networkx.github.io

 TODO: Apply WebWorkers!
*/

var CPM = function ( G ) {

    this.Graph = G;
    this.all_the_cliques = false;

    this.init = function () {
        print("hola mundo")
    }
    
    this.array_union = function (x, y) {
      var obj = {};
      for (var i = x.length-1; i >= 0; -- i)
         obj[x[i]] = x[i];
      for (var i = y.length-1; i >= 0; -- i)
         obj[y[i]] = y[i];
      var res = []
      for (var k in obj) {
        if (obj.hasOwnProperty(k)) { // <-- optional
            res.push(obj[k]);
        }
      }
      return res;
    }

    this.array_intersect = function (a, b) {
        var d = {};
        var results = [];
        for (var i = 0; i < b.length; i++) {
            d[b[i]] = true;
        }
        for (var j = 0; j < a.length; j++) {
            if (d[a[j]]) {
                results.push(a[j]);
            }
        }
        return results;
    }

    this.array_difference = function( a , b ) {
        return $(a).not(b).get();
    }

    this.compareNumbers = function (a, b) {
        return a - b;
    }

    //                            dictionary , dictionary
    this.get_adjacent_cliques = function (clique, membership_dict) {
        var adjacent_cliques = {}
        for( var c in clique) {
            var n = clique[c]
            for (var adj_clique in membership_dict[n]) {
                var adj_clique_str = membership_dict[n][adj_clique].map(Number).sort(this.compareNumbers).join(",")
                var clique_str = clique.map(Number).sort(this.compareNumbers).join(",")
                if( clique_str != adj_clique_str) {
                    adjacent_cliques[ adj_clique_str ] = true
                }
            }
        }
        return adjacent_cliques
    }

    this.find_cliques = function ( G ) {

        var RESULT = []

        var NodesIDs = Object.keys(G).map(Number).sort(this.compareNumbers)
        if ( NodesIDs.length == 0)
            return

        var adj = {}
        for (var u in G) {
            var tempdict = {}
            for(var v in G[u]) {
                if (G[u][v] != u) {
                    tempdict[G[u][v]] = true
                }
            }
            adj[u] = Object.keys( tempdict ).map(Number).sort(this.compareNumbers)
        }

        var Q = [false]

        
        var subg = NodesIDs
        var cand = NodesIDs


        // damn abstraction: 
        //      u = max(subg, key=lambda u: len(cand & adj[u]))
        var inter_max = -1
        var u = -1
        for(var s in subg) {
            var i = subg[s]
            var inter = this.array_intersect( adj[i] , cand )
            if (inter.length>inter_max) {
                inter_max = inter.length
                u = i
            }
        }

        var ext_u = this.array_difference (  cand , adj[u]  )
        var stack = []

        var cand_dict = {}
        for(var n in G) {
            cand_dict[n] = true
        }


        var iteration = 0
        try {
            while(true) {
                // console.log("iteration number: "+iteration)
                if (ext_u && ext_u.length>0) {

                    var q = ext_u.shift()
                    delete cand_dict[q]
                    Q[Q.length-1] = q 
                    var adj_q = adj[q]
                    subg_q = this.array_intersect( subg , adj_q )

                    if (!subg_q || subg_q.length==0) {
                        RESULT.push( Q.slice().sort(this.compareNumbers) );
                    } else {
                        cand_q = this.array_intersect( Object.keys(cand_dict).map(Number).sort(this.compareNumbers) , adj_q )
                        
                        if (cand_q && cand_q.length>0) {
                            stack.push( [subg, Object.keys(cand_dict).map(Number).sort(this.compareNumbers), ext_u] )
                            Q.push(false)
                            subg = subg_q
                            cand = cand_q

                            inter_max = -1
                            u = -1
                            for(var s in subg) {
                                var i = subg[s]
                                var inter = this.array_intersect( adj[i] , cand )
                                if (inter.length>inter_max) {
                                    inter_max = inter.length
                                    u = i
                                }
                            }
                            ext_u = this.array_difference (  cand , adj[u]  )

                            for(c in cand_dict)
                                delete cand_dict[c]
                            for(var i in cand)
                                cand_dict [ cand[i] ] = true;
                        }
                    }


                }  else {
                    Q.pop()
                    var apop = stack.pop()
                    subg = apop[0]
                    cand = apop[1]
                    ext_u  = apop[2]

                    for(c in cand_dict)
                        delete cand_dict[c]
                    for(var i in cand)
                        cand_dict [ cand[i] ] = true;

                }
                iteration++;
            }
        } catch(err) {
            console.log("\t END!!!!")

        }
        return RESULT
    }

    // Breadth First Search using adjacency list
    this.BFS = function (v, adjlist, visited) {
      var q = [];
      var current_group = [];
      var i, len, adjV, nextVertex;
      q.push(v);
      visited[v] = true;
      while (q.length > 0) {
        v = q.shift();
        current_group.push(v);
        // Go through adjacency list of vertex v, and push any unvisited
        // vertex onto the queue.
        // This is more efficient than our earlier approach of going
        // through an edge list.
        adjV = adjlist[v];
        for (i = 0, len = adjV.length; i < len; i += 1) {
          nextVertex = adjV[i];
          if (!visited[nextVertex]) {
            q.push(nextVertex);
            visited[nextVertex] = true;
          }
        }
      }
      return current_group;
    }

    this.k_clique_communities = function ( k ) {


        if (k < 2) {
            console.log( "k must be greater than 1." )
            return []
        }

        var Graph = this.Graph;
        var SuperClusters = []  // var to return!

        // Finding All the cliques!
        var all_the_cliques = []
        if(this.all_the_cliques==false) {
            all_the_cliques = this.find_cliques(Graph)
            this.all_the_cliques = all_the_cliques;
        } 

        // cliques = Consider just >=kcliques
        var cliques = []
        for(var c in this.all_the_cliques) {
            if( this.all_the_cliques[c].length>=k) {
                cliques.push(this.all_the_cliques[c])
            }
        }

        // for(var c in cliques) {
        //     console.log(cliques[c])
        // }
        // console.log("")
        // console.log(" = = = = = #cliques: "+cliques.length+" = = = = = = ")
        // console.log("")


        // membership_dict = Relation ( Node , Cliques )
        var membership_dict = {}
        for(var i in cliques) {
            var clique = cliques[i].sort(this.compareNumbers)
            for (var j in clique) {
                var node = clique[j]
                if (!membership_dict[node])
                    membership_dict[node] = []
                membership_dict[node].push(clique)
            }
        }

        
        // Building a Clique-Graph!:
        //    doing the source nodes
        var CliquesGraph = {}
        for(var i in cliques) {
            var clique = cliques[i].sort(this.compareNumbers).join(",")
            CliquesGraph[clique] = {}
        }
        //    doing the edges:
        for(var i in cliques) {
            var clique = cliques[i].sort(this.compareNumbers)
            var adj_cliques = this.get_adjacent_cliques(clique, membership_dict)
            for(var ac in adj_cliques) {
                var adj_clique = ac.split(",").map(Number).sort(this.compareNumbers)
                var intersection = this.array_intersect( clique , adj_clique )
                if (intersection.length >= (k - 1) ) {
                    var s = clique.join(",")
                    var t = adj_clique.join(",")
                    CliquesGraph[s][t] = true;
                }
            }
        }
        for(var s in CliquesGraph)
            CliquesGraph[s] = Object.keys(CliquesGraph[s])


        // For each clique, see which adjacent cliques percolate
        var groups = [];
        var visited = {};
        var v;
        for (v in CliquesGraph) {
          if (CliquesGraph.hasOwnProperty(v) && !visited[v]) {
            groups.push( this.BFS(v, CliquesGraph, visited) );
          }
        }

        // Calculating the nodes-union per agroupation.
        for (var i in groups) {
            var group = groups[i]
            var unique_array = []
            for(var j in group) {
                var cluster = group[j]
                var nodes = cluster.split(",").map(Number).sort(this.compareNumbers)
                unique_array = this.array_union ( unique_array , nodes ).sort(this.compareNumbers)
            }
            SuperClusters.push( unique_array.sort(this.compareNumbers) )
        }


        return SuperClusters;
    }

};


// self.addEventListener("message", function(e) {

//     var Graph = e.data.Graph;
//     var jCPM = new CPM( Graph )
//     var results = jCPM.k_clique_communities(4)

//     postMessage({
//         "groups":results,
//     });
    
// }, false);



// console.log( "Hello I'm CPM!" )

// var Graph = {}

// var CPM_instance = new CPM( Graph )
// var results = CPM_instance.k_clique_communities(4)

// console.log("Groups: "+results.length)
// for(var g in results) {
//     console.log(results[g])
// }

