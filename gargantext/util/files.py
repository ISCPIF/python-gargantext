from gargantext.constants   import *
from gargantext.util.digest import str_digest
from gargantext.util        import http


def save(contents, name='', basedir=''):
    digest = str_digest(contents[:4096] + contents[-4096:])
    path = basedir
    for i in range(2, 8, 2):
        path += '/' + digest[:i]
    if not os.path.exists(path):
        os.makedirs(path)
    # save file and return its path
    path = '%s/%s_%s' % (path, digest, name, )
    open(path, 'wb').write(contents)
    return path


def download(url, name=''):
    return save(
        contents = http.get(url),
        name = name,
        basedir = DOWNLOAD_DIRECTORY,
    )

def check_format(corpus_type, name):
    #~ if True:
    acc_formats = RESOURCETYPES[corpus_type]["accepted_formats"]
    if name.split(".")[-1].lower() not in acc_formats:
        raise TypeError('Uncorrect format of file. File must be a %s file' %" or ".join(acc_formats))


def upload(uploaded):

    if uploaded.size > UPLOAD_LIMIT:
        raise IOError('Uploaded file is bigger than allowed: %d > %d' % (
            uploaded.size,
            UPLOAD_LIMIT,
        ))

    return save(
        contents = uploaded.file.read(),
        name = uploaded.name,
        basedir = UPLOAD_DIRECTORY,
    )
