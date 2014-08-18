import time
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


def get_rows_in_chunks(query, rowfun, limit, params=None,
                       total=None,
                       report=False,
                       report_interval=1000):
    if params is None:
        params = dict()
    if total is None:
        total = query.count()
    count = 0
    offset = 0
    rows = query.offset(offset).limit(limit).all()
    while len(rows):
        row = rows.pop(0)
        if rowfun(row, **params) is not None:
            raise RuntimeError, "row function should return None"
        count += 1
        if report and not count % report_interval:
            msg = '%d rows remaining on %s'
            print msg % ((total - count), time.ctime())
        if count == total:
            break
        if not len(rows):
            offset += limit
            rows = query.offset(offset).limit(limit).all()
            
