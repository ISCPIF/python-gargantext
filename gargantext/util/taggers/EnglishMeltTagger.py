from .MeltTagger import MeltTagger, _tag_replacements

class EnglishMeltTagger(MeltTagger):
    def __init__(self, *args, **kwargs):
        MeltTagger.__init__(self, *args, **kwargs)
        self.language = 'en'
        self._tag_replacements = _tag_replacements['en']
