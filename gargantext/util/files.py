from gargantext.constants import *
from gargantext.util.digest import str_digest
from gargantext.util import http


def save(contents, name='', basedir=''):
    digest = str_digest(contents)
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
    save(
        contents = http.get(url),
        name = name,
        basedir = DOWNLOAD_DIRECTORY,
    )


def upload(uploaded):
    if uploaded.size > UPLOAD_LIMIT:
        raise IOError('Uploaded file is bigger than allowed: %d > %d' % (
            uploaded.size,
            UPLOAD_LIMIT,
        ))
    save(
        contents = uploaded.file.read(),
        name = uploaded.name,
        basedir = UPLOAD_DIRECTORY,
    )
