from gargantext.util.http import *


def bootstrap(request):
    template = get_template('generated/css/bootstrap.css')
    css = dict()
    group = "mines"
    #group = "cnrs"

    if group == "mines":
        css['color']        = '#666666'
        css['background']   = '#f8f8f7'
        css['a']            = '#bd2525'
        css['focus']        = '#7d1818'
        css['hr']           = '#eaafae'
        css['text']         = '#a2a3a2'
        css['form']         = '#a5817f'
        css['help']         = '#a6a6a6'
    else:
        css['color']        = '#E2E7EB'
        css['background']   = '#8C9DAD' #container background
        css['a']            = '#093558'
        css['focus']        = '#556F86'
        css['hr']           = '#426A8A'
        css['text']         = '#214A6D'
        css['form']         = '#093558'
        css['help']         = '#093558'

    css_data = template.render({
        'css': css,
    })
    return HttpResponse(css_data, content_type="text/css")
