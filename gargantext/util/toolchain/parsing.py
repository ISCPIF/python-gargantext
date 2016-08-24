from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
#from gargantext.util.parsers import *
from collections import defaultdict, Counter
from re          import sub
from gargantext.util.languages import languages, detect_lang

def add_lang(languages, hyperdata, skipped_languages):
    '''utility to add lang information
    1. on language_iso2
    2. on other format language_%f
    3. on text from concatenation  of DEFAULT_INDEX_FIELDS
    '''

    if "language_iso2" in hyperdata.keys():
        try:
            languages[hyperdata["language_iso2"]] +=1
            return languages,hyperdata, skipped_languages
        except KeyError:
            hyperdata["error"] = "Error: unsupported language %s" %hyperdata["language_iso2"]
            skipped_languages.append(hyperdata["language_iso2"])
            return languages,hyperdata, skipped_languages
    # this should be the responsability of the parserbot
    elif "language_iso3" in hyperdata.keys():
        #convert
        try:
            lang =  languages[hyperdata["language_iso3"]].iso2
            try:
                corpus.languages[lang] +=1
                return languages,hyperdata, skipped_languages
            except KeyError:
                hyperdata["error"] = "Error: unsupported language %s" %lang
                skipped_languages.append(lang)
                return languages,hyperdata, skipped_languages
        except KeyError:
            print ("LANG not referenced", (hyperdata["language_iso3"]))
            #skipped_languages.append(hyperdata["language_iso3"])
            #hyperdata["error"] = "Error: unsupported language '%s'" %hyperdata["language_fullname"]
            return languages,hyperdata, skipped_languages

    elif "language_fullname" in hyperdata.keys():

        try:
            #convert
            lang = languages[hyperdata["language_fullname"]].iso2

            try:
                corpus.languages[lang] +=1
                return corpus, hyperdata, skipped_languages
            except KeyError:
                hyperdata["error"] = "Error: unsupported language %s" %lang
                skipped_languages.append(lang)
                return languages,hyperdata, skipped_languages
        except KeyError:
            print ("LANG Not referenced", (hyperdata["language_fullname"]))
            #hyperdata["error"] = "Error: unsupported language '%s'" %hyperdata["language_fullname"]
            return languages,hyperdata, skipped_languages


    else:
        print("[WARNING] no language_* found in document [parsing.py]")
        #no language have been indexed
        #detectlang by index_fields

        text = " ".join([getattr(hyperdata, k) for k in DEFAULT_INDEX_FIELDS])
        if len(text) < 10:
            hyperdata["error"] = "Error: no TEXT fields to index"
            skipped_languages.append("__unknown__")
            return languages,hyperdata, skipped_languages
        #detect_lang return iso2
        lang = detect_lang(text)
        try:
            languages[lang] += 1
            return languages,hyperdata, skipped_languages
        except KeyError:
            hyperdata["error"] = "Error: unsupported language '%s'" %lang
            skipped_languages.append(lang)
            return languages,hyperdata, skipped_languages


def parse(corpus):
    try:
        print("PARSING")

        corpus.status('Docs', progress=0)
        #1 corpus => 1 or multi resources.path (for crawlers)
        resources = corpus.resources()
        if len(resources) == 0:
            return
        #all the resources are of the same type for now
        source = get_resource(resources[0]["type"])
        #get the sources capabilities for a given corpus resource
        #load the corresponding parserbot
        if source["parser"] is None:
            #corpus.status(error)
            raise ValueError("Resource '%s' has no Parser" %resource["name"])
        parserbot = load_parser(source)
        #observed languages in default languages
        languages = defaultdict.fromkeys(source["default_languages"], 0)

        #skipped_languages
        skipped_languages = []
        #skipped docs to remember for later processing
        skipped_docs = []


        #BY RESOURCE
        for i,resource in enumerate(resources):
            if resource["extracted"] is True:
                continue
            else:
                # BY documents
                d = 0
                for hyperdata in parserbot(resource["path"]):
                    # indexed text fields defined in CONSTANTS
                    for k in DEFAULT_INDEX_FIELDS:
                        if k in hyperdata.keys():
                            try:
                                hyperdata[k] = normalize_chars(hyperdata[k])
                            except Exception as error :
                                hyperdata["error"] = "Error normalize_chars"
                        #else:
                            #print("[WARNING] No %s field found in hyperdata at parsing.py" %k)
                        #    continue
                    #adding lang into  record hyperdata
                    languages, hyperdata, skipped_languages = add_lang(languages, hyperdata, skipped_languages)
                    # save as DB child
                    # ----------------
                    d += 1
                    #print ("INSERT", d)
                    document = corpus.add_child(
                        typename = 'DOCUMENT',
                        name = hyperdata.get('title', '')[:255],
                        hyperdata = hyperdata,
                    )
                    #corpus.save_hyperdata()
                    session.add(document)
                    session.commit()

                    if "error" in hyperdata.keys():
                        #document.status("error")
                        document.status('Parsing', error= document.hyperdata["error"])
                        document.save_hyperdata()
                        session.add(document)
                        session.commit()
                        #adding skipped_docs for later processsing
                        skipped_docs.append(document.id)





                #documents for this resources


                session.add(corpus)
                session.commit()
                # update info about the resource
                resource['extracted'] = True
                #print( "resource n°",i, ":", d, "docs inside this file")


        # add a corpus-level info about languages adding a __skipped__ info
        print(len(skipped_docs), "docs skipped")
        print(corpus.children("DOCUMENT").count(), "docs parsed")
        #main language of the corpus
        print(languages.items())
        corpus.language_id = sorted(languages.items(), key = lambda x: x[1], reverse=True)[0][0]
        print(corpus.language_id)
        languages['__skipped__'] = dict(Counter(skipped_languages))
        corpus.languages = languages
        corpus.skipped_docs = list(set(skipped_docs))
        corpus.save_hyperdata()
        session.commit()
        if len(corpus.skipped_docs) > 0:
            print (sum(languages["__skipped__"].values()), "docs with unsupported lang")
            #assign main lang of the corpus to unsupported languages docs
            # for d_id in corpus.skipped_docs:
            #     document = session.query(Node).filter(Node.id == d_id, Node.typename == "DOCUMENT").first()
            #     if document.hyperdata["error"].startswith("Error: unsupported language"):
            #         print(document.hyperdata["language_iso2"])
            #     document.hyperdata["language_iso2"] = corpus.language_id
            #     document.save_hyperdata()
            #     session.commit()



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
