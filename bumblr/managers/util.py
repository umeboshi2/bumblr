import hashlib

import requests

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def get_md5sum_from_tumblr_headers(headers):
    try:
        etag = headers['etag'][1:-1]
        if len(etag) != 32:
            print "ETAG is nonconforming: %s" % etag
            return None
        else:
            return etag
    except KeyError:
        return None

def get_md5sum_for_file(fileobj):
    m = hashlib.md5()
    block = fileobj.read(1024)
    while block:
        m.update(block)
        block = fileobj.read(1024)
    return m.hexdigest()

def get_md5sum_with_head_request(utuple):
    url, url_id = utuple
    r = requests.head(url)
    etag = None
    if r.ok:
        etag = get_md5sum_from_tumblr_headers(r.headers)
    return url_id, r.status_code, etag


