from .MeltTagger import MeltTagger

def EnglishMeltTagger(*args, **kwargs):
    kwargs['language'] = 'en'
    return MeltTagger(*args, **kwargs)
