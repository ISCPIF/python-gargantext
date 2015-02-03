from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context


def logo(request):
    template = get_template('logo.svg')
    group = "mines"
    group = "cnrs"
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
    group = "cnrs"

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



