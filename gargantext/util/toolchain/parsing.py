"""
Deserialize an external document collection with a parserbot
then transfer it to our DB as document nodes within a corpus
"""
from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
#from gargantext.util.parsers import *
from collections import defaultdict, Counter
from re          import sub
from gargantext.util.languages import languages, detect_lang


def add_lang(hyperdata, observed_languages, skipped_languages):
    '''utility to gather corpus-level lang information
       and also detect unknown languages (if constants.DETECT_LANG is true)
    1. on language_iso2
    2. on other format language_%f
    3. on text from concatenation  of DEFAULT_INDEX_FIELDS

    TODO factorize with _Parser.format_hyperdata_languages()
    '''

    # this will be our return value
    lang_result = {
             # the 2 global counts to update
            'observed': observed_languages,
            'skipped': skipped_languages,

            # optional new value for doc
            'doc_prediction': None,   # tuple with (iso2, iso3, name)

            # optional error for doc
            'doc_error': None         # str
        }

    if "language_iso2" in hyperdata and hyperdata["language_iso2"]:
        lang = hyperdata["language_iso2"]
        if lang not in LANGUAGES.keys():
            lang_result['skipped'].append(lang)   # FIXME: perhaps better to do this at ngrams_extraction
        else:
            lang_result['observed'].append(lang)

    elif "language_iso3" in hyperdata and hyperdata["language_iso3"]:
        #convert
        try:
            lang =  languages[hyperdata["language_iso3"]].iso2
            if lang not in LANGUAGES.keys():
                lang_result['skipped'].append(lang)   # idem
            else:
                lang_result['observed'].append(lang)

        except KeyError:
            print ("LANG not referenced", hyperdata["language_iso3"])
            lang_result['skipped'].append(hyperdata["language_iso3"])

    elif "language_name" in hyperdata and hyperdata["language_name"]:
        try:
            #convert
            lang = languages[hyperdata["language_name"]].iso2
            if lang not in LANGUAGES.keys():
                lang_result['skipped'].append(lang)   # idem
            else:
                lang_result['observed'].append(lang)

        except KeyError:
            print ("LANG Not referenced", hyperdata["language_name"])
            lang_result['skipped'].append(hyperdata["language_name"])

    else:
        # print("WARNING no language_* found in document [parsing.py] => "
        #        + ("(detecting)" if DETECT_LANG else "(using default)"))

        if DETECT_LANG:
            #no language have been indexed
            #detectlang by joining on the DEFAULT_INDEX_FIELDS
            text_fields = list(set(DEFAULT_INDEX_FIELDS) & set(hyperdata.keys()))

            text = " ".join([hyperdata[k] for k in text_fields])
            if len(text) < 10:
                lang_result["doc_error"] = "Error: not enough text to index"
            else:
                # detect_lang return object o with o.iso2, o.iso3 ...
                lang = detect_lang(text)
                lang_result["doc_prediction"] = (getattr(lang, k) for k in ["iso2", "iso3", "name"])
                if lang.iso2 not in LANGUAGES.keys():
                    lang_result['skipped'].append(lang.iso2)    # idem
                else:
                    lang_result['observed'].append(lang.iso2)
    #print(lang_result)
    return lang_result


def parse(corpus):
    try:
        print("PARSING")
        # print("DETECT_LANG?", DETECT_LANG)
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

        # print(parserbot)

        #observed languages in default languages
        observed_languages = []
        #skipped_languages
        skipped_languages = []
        #skipped docs to remember for later processing
        pending_add_error_stats = False
        skipped_docs = []

        documents_count = 0
        #BY RESOURCE
        for i,resource in enumerate(resources):
            if resource["extracted"] is True:
                continue
            else:
                # BY documents (cf. _Parser.__iter__)
                for hyperdata in parserbot(resource["path"]):
                    # indexed text fields defined in CONSTANTS
                    for k in DEFAULT_INDEX_FIELDS:
                        if k in hyperdata.keys():
                            try:
                                hyperdata[k] = normalize_chars(hyperdata[k])
                            except Exception as error :
                                hyperdata["error"] = "Error normalize_chars"

                    # adding lang into record hyperdata JUST if not declared
                    lang_infos = add_lang(hyperdata, observed_languages, skipped_languages)

                    # update document
                    if lang_infos['doc_error']:
                        hyperdata['warning'] = lang_infos['doc_error']

                    if lang_infos['doc_prediction']:
                        prediction = lang_infos['doc_prediction']
                        hyperdata['language_iso2'] = prediction[0]
                        hyperdata['language_iso3'] = prediction[1]
                        hyperdata['language_name'] = prediction[2]
                        del prediction

                    # update stats
                    observed_languages = lang_infos['observed']
                    skipped_languages = lang_infos['skipped']

                    del lang_infos

                    # init statuses
                    hyperdata['statuses'] = []

                    # only parsing errors can be written straight to doc statuses
                    # because it's a new hyperdata for the DB
                    if "error" in hyperdata.keys():
                        hyperdata['statuses'].append({
                            'action':'Parsing',
                            'error': hyperdata['error']
                            })
                        pending_add_error_stats = True

                    # -----------------------
                    # save as corpus DB child
                    # -----------------------
                    document = corpus.add_child(
                        typename = 'DOCUMENT',
                        name = hyperdata.get('title', '')[:255],
                        hyperdata = hyperdata,
                    )
                    session.add(document)
                    session.commit()
                    documents_count += 1

                    if pending_add_error_stats:
                        #adding skipped_docs for later processing if error in parsing
                        skipped_docs.append(document.id)
                        pending_add_error_stats = False

                    #BATCH_PARSING_SIZE
                    if documents_count % BATCH_PARSING_SIZE == 0:
                        corpus.status('Docs', progress=documents_count)
                        corpus.save_hyperdata()
                        session.add(corpus)
                        session.commit()

                # update info about the resource
                resource['extracted'] = True
                #print( "resource n°",i, ":", d, "docs inside this file")

        # mark *corpus-level* status as complete !
        corpus.status('Docs', progress=documents_count+1, complete=True)
        corpus.save_hyperdata()

        # end of parsing

        #STORING AGREGATIONS INFO (STATS)

        # skipped_docs (ie docs to be skipped in next steps)
        print(len(skipped_docs), "docs skipped")
        corpus.hyperdata["skipped_docs"] = list(skipped_docs)
        corpus.save_hyperdata()

        # documents info
        docs = corpus.children("DOCUMENT").count()
        if docs == 0:
            print("[ERROR] PARSING FAILED!!!!!")
            corpus.status('Docs', error= "No documents parsed")
        print(docs, "parsed")

        # language stats
        #les langues pas belles
        skipped_langs = dict(Counter(skipped_languages))      # idem
        #les jolis iso2
        observed_langs = dict(Counter(observed_languages))

        # print("#LANGAGES OK")
        # print(observed_langs)
        # print("#LANGUAGES UNKNOWN")
        # print(skipped_langs)

        top_langs = sorted(observed_langs.items(), key = lambda x: x[1], reverse=True)
        if len(top_langs) > 0:
            corpus.hyperdata["language_id"] = top_langs[0][0]
        else:
            corpus.hyperdata["language_id"] = "__unknown__"
        print("#MAIN language of the CORPUS", corpus.hyperdata["language_id"])

        corpus.hyperdata["languages"] = observed_langs
        corpus.hyperdata["languages"]["__unknown__"] = list(skipped_langs.keys())
        corpus.save_hyperdata()


    except Exception as error:
        corpus.status('Docs', error=error)
        corpus.save_hyperdata()
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
