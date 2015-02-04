from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context

import igraph, colorsys, struct, binascii



def hex2rgb(hex_color):
    return struct.unpack('BBB', hex_color.decode('hex'))

def rgb2hex(rgb_color):
    return binascii.hexlify(struct.pack('BBB', *rgb_color))

def round_tuple(data_tuple):
    return(tuple(map(lambda x: round(x * 255), data_tuple)))


def kamaieu(color_name, number=18, order=None):
    '''
    Order from dark to light
    Order from light to dark
    '''
    r, g, b = igraph.color_name_to_rgb(color_name)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    colors_hls = [(h, l/(1 + 1.9 / light), s) for light in range(1,number)]
    
    colors_rgb = [colorsys.hls_to_rgb(*color) for color in colors_hls]

    print(colors_rgb)
    colors_rgb_round = list(map(round_tuple, colors_rgb))
    print(colors_rgb_round)
    colors_hex = [rgb2hex(color) for color in colors_rgb_round]
    
    return(colors_hex)



def logo(request):
    template = get_template('logo.svg')
    group = "mines"
    #group = "cnrs"
    if group == "cnrs":
        color = "#093558"
    else:
        color = "#ff8080"
    svg_data = template.render(Context({\
            'color': color,\
            }))
    return HttpResponse(svg_data, mimetype="image/svg+xml")

def css(request):
    template = get_template('bootstrap.css')
    css = dict()
    group = "mines"
    group = "test"

    if group == "mines":
        css['color']                    = '#666666'
        css['background']               = '#f8f8f7'
        css['a']                        = '#bd2525'
        css['focus']                    = '#7d1818'
        css['hr']                       = '#eaafae'
        css['text']                     = '#a2a3a2'
        css['form']                     = '#a5817f'
        css['help']                     = '#a6a6a6'
        css['border']                   = '#a82121'
        css['button_background']        = '#9b1e1e'
        css['button_border']            = '#741717'
        css['navbar_inverse_background']= '#090a09'
        css['navbar_inverse_border']    = '#000000'
        css['list_group']               = '#f2bcbc'
        css['label_default']            = '#888a88'
        css['label_primary_focus']      = '#921d1d'
    elif group == "test":
        list_css = [
        'focus',
        'navbar_inverse_background',
        'navbar_inverse_border',
        'hr',                   # container background
        'a',                    # button primary
        'form',
        'help',
        'border',
        'button_background',
        'text',
        'background',           # background
        'button_border',
        'list_group',
        'label_default',
        'label_primary_focus',
        'color',                # color of text
                ]
        colors = kamaieu('pink', number=len(list_css))
        css    = { i[0]: '#' + i[1].decode('utf-8') for i in zip(list_css, colors)}
        print(css)
    
    else:
        css['color']                    = '#AA2E09' # color of text 
        css['background']               = '#93AA00' # background
        css['a']                        = '#093551' # button primary
        css['focus']                    = '#093551' #
        css['hr']                       = '#426A8A' # container background
        css['text']                     = '#214A6D'
        css['form']                     = '#093558'
        css['help']                     = '#093558'
        css['border']                   = css['color']
        css['button_background']        = css['hr']
        css['button_border']            = css['background']
        css['navbar_inverse_background']= css['a']
        css['navbar_inverse_border']    = css['text']
        css['list_group']               = css['background']
        css['label_default']            = css['background']
        css['label_primary_focus']      = css['background']

    css_data = template.render(Context({\
            'css': css,\
            }))
    return HttpResponse(css_data, mimetype="text/css")



