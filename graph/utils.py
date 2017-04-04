
def compress_graph(graphdata):
    """
    graph data is usually a dict with 2 slots:
      "nodes": [{"id":4103, "type":"terms", "attributes":{"clust_default": 0}, "size":29, "label":"regard"},...]
      "links": [{"t": 998,"s": 768,"w": 0.0425531914893617},...]

    To send this data over the net, this function can reduce a lot of its size:
      - keep less decimals for float value of each link's weight
      - use shorter names for node properties (eg: s/clust_default/cl/)

    result format:
        "nodes": [{"id":4103, "at":{"cl": 0}, "s":29, "lb":"regard"},...]
        "links": [{"t": 998,"s": 768,"w": 0.042},...]
    """
    for link in graphdata['links']:
        link['w'] = format(link['w'], '.3f')   # keep only 3 decimals

    for node in graphdata['nodes']:
        node['lb'] = node['label']
        del node['label']
        
        #node['attributes']['growth'] = 0.8

        node['at'] = node['attributes']
        del node['attributes']

        node['at']['cl'] = node['at']['clust_default']
        del node['at']['clust_default']

        node['s'] = node['size']
        del node['size']

        if node['type'] == "terms":
            # its the default type for our format: so we don't need it
            del node['type']
        else:
            node['t'] = node['type']
            del node['type']

    return graphdata

def format_html(link):
    """
    Build an html link adapted to our json message format
    """
    return "<a class='msglink' href='%s'>%s</a>" % (link, link)


