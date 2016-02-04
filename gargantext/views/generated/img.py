from gargantext.util.http import *


def logo(request):
    template = get_template('generated/img/logo.svg')
    group = 'mines'
    #group = 'cnrs'
    if group == 'cnrs':
        color = '#093558'
    else:
        # color of the css adapted to the logo
        color = '#AE5C5C'
    svg_data = template.render(Context({\
            'color': color,\
            }))
    return HttpResponse(svg_data, content_type='image/svg+xml')
