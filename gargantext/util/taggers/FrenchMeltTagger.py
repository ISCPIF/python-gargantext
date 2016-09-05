from .MeltTagger import MeltTagger, _tag_replacements

class FrenchMeltTagger(MeltTagger):
    def __init__(self, *args, **kwargs):
        MeltTagger.__init__(self, *args, **kwargs)
        self.language = 'fr'
        self._tag_replacements = _tag_replacements['fr']
