from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
from gargantext.util.parsers import *
from collections import defaultdict, Counter
from re          import sub

def parse(corpus):
    try:
        documents_count = 0
        corpus.status('Docs', progress=0)
        #get the sources capabilities for a given corpus
        sources = [get_resource(resource["type"]) for resource in corpus.resources() if not 'extracted' in resource.keys() ]
        if len(sources) == 0:
            #>>> documents have already been parsed?????
            return
        if len(sources) > 0:
            #>>> necessairement 1 corpus = 1 source dans l'archi actuelle
            source = sources[0]
            if resource["parser"] is None:
                #corpus.status(error)
                raise ValueError("Resource '%s' has no Parser" %resource["name"])
            else:
                corpus.languages = defaultdict.from_keys(sources[0]["default_languages"], 0)
                corpus.skipped_docs = []
                #load the corresponding parser
                resource_parser = load_parser(source)
                skipped_languages = []
                # extract and insert documents from resource.path into database
                for hyperdata in resource_parser(resource["path"]):
                    # indexed text fields defined in constants
                    for k in DEFAULT_INDEX_FIELDS:
                        if k in hyperdata.keys():
                            try:
                                hyperdata[k] = normalize_chars(hyperdata[k])
                            except Exception as error :
                                hyperdata["error"] = "Error normalize_chars"

                    # a simple census to raise language info at corpus level
                    if "language_iso2" in hyperdata.keys():
                        try:
                            corpus.languages[hyperdata["language_iso2"]] += 1
                        except KeyError:
                            hyperdata["error"] = "Error: unsupported language"
                            skipped_languages.append(hyperdata["language_iso2"])
                    else:
                        hyperdata["error"] = "Error: no language found"
                # save as DB child
                # ----------------


                document = corpus.add_child(
                    typename = 'DOCUMENT',
                    name = hyperdata.get('title', '')[:255],
                    hyperdata = hyperdata,
                )
                session.add(document)
                if "error" in document.hyperdata.keys():
                    #document.status("error")
                    document.status('Parsing', error= document.hyperdata["error"])
                    #session.delete(document)
                    corpus.skipped_docs.append(document.id)


                # logging
                if documents_count % BATCH_PARSING_SIZE == 0:
                    corpus.status('Docs', progress=documents_count)
                    corpus.save_hyperdata()
                    session.commit()
                documents_count += 1
            # update info about the resource
            resource['extracted'] = True
        # add a corpus-level info about languages adding a __skipped__ info
        corpus.hyperdata['languages']['__skipped__'] = Counter(skipped_languages)
        # commit all changes
        corpus.status('Docs', progress=documents_count, complete=True)
        corpus.save_hyperdata()
        session.commit()
    except Exception as error:
        corpus.status('Docs', error=error)
        corpus.save_hyperdata()
        session.commit()
        raise error



def normalize_chars(my_str):
    """
    Simplification des chaînes de caractères en entrée de la BDD
    ("les caractères qu'on voudrait ne jamais voir")
       - normalisation
            > espaces
            > tirets
            > guillemets
       - déligatures

    NB: cette normalisation du texte en entrée ne va pas enlever les ponctuations
     mais les transcoder en une forme plus canonique pour réduire leur diversité

      (autres traitements plus invasifs, comme enlever les guillemets
       ou passer en lowercase, seront à placer plutôt *après* le tagger,
            cf. toolchain.ngrams_extraction.normalize_forms)
    """
    # print('normalize_chars  IN: "%s"' % my_str)
    # --------------
    # E S P A C E S
    # --------------
    # tous les caractères de contrôle (dont \t = \x{0009}, \n = \x{000A} et \r = \x{000D}) --> espace
    my_str = sub(r'[\u0000\u0001\u0002\u0003\u0004\u0005\u0006\u0007\u0008\u0009\u000A\u000B\u000C\u000D\u000E\u000F\u0010\u0011\u0012\u0013\u0014\u0015\u0016\u0017\u0018\u0019\u001A\u001B\u001C\u001D\u001E\u001F\u007F]', ' ', my_str)

    # Line separator
    my_str = sub(r'\u2028',' ', my_str)
    my_str = sub(r'\u2029',' ', my_str)

    # U+0092: parfois quote parfois cara de contrôle
    my_str = sub(r'\u0092', ' ', my_str)

    # tous les espaces alternatifs --> espace
    my_str = sub(r'[\u00A0\u1680\u180E\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u202F\u205F\u3000\uFEFF]', ' ' , my_str)

    # pour finir on enlève les espaces en trop
    # (dits "trailing spaces")
    my_str = sub(r'\s+', ' ', my_str)
    my_str = sub(r'^\s', '', my_str)
    my_str = sub(r'\s$', '', my_str)

    # ------------------------
    # P O N C T U A T I O N S
    # ------------------------
    # la plupart des tirets alternatifs --> tiret normal (dit "du 6")
    # (dans l'ordre U+002D U+2010 U+2011 U+2012 U+2013 U+2014 U+2015 U+2212 U+FE63)
    my_str = sub(r'[‐‑‒–—―−﹣]','-', my_str)

    # le macron aussi parfois comme tiret
    my_str = sub(r'\u00af','-', my_str)

    # Guillemets
    # ----------
    # la plupart des quotes simples --> ' APOSTROPHE
    my_str = sub(r"[‘’‚`‛]", "'", my_str) # U+2018 U+2019 U+201a U+201b
    my_str = sub(r'‹ ?',"'", my_str)    # U+2039 plus espace éventuel après
    my_str = sub(r' ?›',"'", my_str)    # U+203A plus espace éventuel avant

    # la plupart des quotes doubles --> " QUOTATION MARK
    my_str = sub(r'[“”„‟]', '"', my_str)  # U+201C U+201D U+201E U+201F
    my_str = sub(r'« ?', '"', my_str)   # U+20AB plus espace éventuel après
    my_str = sub(r' ?»', '"', my_str)   # U+20AB plus espace éventuel avant

    # deux quotes simples (préparées ci-dessus) => une double
    my_str = sub(r"''", '"', my_str)

    # Autres
    # -------
    my_str = sub(r'…', '...', my_str)
    # paragraph separator utilisé parfois comme '...'
    my_str = sub(r'\u0085', '...', my_str)
    my_str = sub(r'€', 'EUR', my_str)

    # quelques puces courantes (bullets)
    my_str = sub(r'▪', '*', my_str)
    my_str = sub(r'►', '*', my_str)
    my_str = sub(r'●', '*', my_str)
    my_str = sub(r'◘', '*', my_str)
    my_str = sub(r'→', '*', my_str)
    my_str = sub(r'•', '*', my_str)
    my_str = sub(r'·', '*', my_str)

    # ------------------
    # L I G A T U R E S
    # ------------------
    my_str = sub(r'Ꜳ', 'AA', my_str)
    my_str = sub(r'ꜳ', 'aa', my_str)
    my_str = sub(r'Æ', 'AE', my_str)
    my_str = sub(r'æ', 'ae', my_str)
    my_str = sub(r'Ǳ', 'DZ', my_str)
    my_str = sub(r'ǲ', 'Dz', my_str)
    my_str = sub(r'ǳ', 'dz', my_str)
    my_str = sub(r'ﬃ', 'ffi', my_str)
    my_str = sub(r'ﬀ', 'ff', my_str)
    my_str = sub(r'ﬁ', 'fi', my_str)
    my_str = sub(r'ﬄ', 'ffl', my_str)
    my_str = sub(r'ﬂ', 'fl', my_str)
    my_str = sub(r'ﬅ', 'ft', my_str)
    my_str = sub(r'Ĳ', 'IJ', my_str)
    my_str = sub(r'ĳ', 'ij', my_str)
    my_str = sub(r'Ǉ', 'LJ', my_str)
    my_str = sub(r'ǉ', 'lj', my_str)
    my_str = sub(r'Ǌ', 'NJ', my_str)
    my_str = sub(r'ǌ', 'nj', my_str)
    my_str = sub(r'Œ', 'OE', my_str)
    my_str = sub(r'œ', 'oe', my_str)
    my_str = sub(r'\u009C', 'oe', my_str)   # U+009C (cara contrôle vu comme oe)
    my_str = sub(r'ﬆ', 'st', my_str)
    my_str = sub(r'Ꜩ', 'Tz', my_str)
    my_str = sub(r'ꜩ', 'tz', my_str)

    # print('normalize_chars OUT: "%s"' % my_str)

    return my_str
