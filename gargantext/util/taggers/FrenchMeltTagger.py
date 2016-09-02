from .MeltTagger import MeltTagger

def FrenchMeltTagger(*args, **kwargs):
    kwargs['language'] = 'fr'
    return MeltTagger(*args, **kwargs)
