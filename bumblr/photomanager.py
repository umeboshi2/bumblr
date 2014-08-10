import os
import multiprocessing
from multiprocessing.pool import ThreadPool
import time
import hashlib

import transaction
import requests
from sqlalchemy import not_
from sqlalchemy import exists

from bumblr.database import TumblrPhotoUrl, TumblrThumbnailUrl
from bumblr.database import TumblrPostPhoto
from bumblr.database import TumblrPhotoUrlMd5sum
from bumblr.database import TumblrThumbnailUrlMd5sum

from bumblr.filerepos import FileExistsError, FileRepos

MD5CLASSMAP = { TumblrPhotoUrl : TumblrPhotoUrlMd5sum,
                TumblrThumbnailUrl : TumblrThumbnailUrlMd5sum }


class FileExistsError(Exception):
    pass

class PhotoExistsError(FileExistsError):
    pass

class BadRequestError(Exception):
    pass

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


def get_md5sums_for_urls(session, objs, chunksize=20, processes=5,
                         thumb_urls=False):
    paramlist = [(o.url, o.id) for o in objs]
    grouped = chunks(paramlist, chunksize)
    pool = ThreadPool(processes=processes)
    count = 0
    for group in grouped:
        output = pool.map(get_md5sum_with_head_request, group)
        with transaction.manager:
            model = TumblrPhotoUrl
            md5model = TumblrPhotoUrlMd5sum
            if thumb_urls:
                model = TumblrThumbnailUrl
                md5model = TumblrThumbnailUrlMd5sum
            for url_id, status, md5sum in output:
                tpu = session.query(model).get(url_id)
                tpu.status = status
                session.add(tpu)
                #if md5sum is None:
                #    print "Skipping md5sum for status %d" % status
                #    continue
                md = session.query(md5model).get(url_id)
                if md is None:
                    #print "md is None", md5sum, url_id
                    md = md5model()
                    md.id = url_id
                    md.md5sum = md5sum
                    session.add(md)
                elif md5sum is not None:
                    #print "MD is %s" % md
                    md.md5sum = md5sum
                    session.add(md)
                else:
                    raise RuntimeError, "Something went wrong"
                
        count += 1
        print "Group %d processed." % count
        print "Sleeping for 0.1 second."
        time.sleep(0.1)
        
# download a url to a FileRepos
def download_url(utuple):
    url, url_id, repos = utuple
    if repos.file_exists(url):
        return url_id, 777, None
        #print "File exists for url_id %d" % url_id
        r = requests.head(url)
        if r.ok:
            basename = os.path.basename(url)
            etag = get_md5sum_from_tumblr_headers(r.headers)
            lfile = repos.open_file(basename)
            md5sum = get_md5sum_for_file(lfile)
            if etag != md5sum and etag is not None:
                print "Bad md5sum found for %s" % url
                os.remove(repos.filename(basename))
            else:
                print 'local copy of %s is OK' % url
                return url_id, 200, etag
    basename = os.path.basename(url)
    filename = repos.filename(basename)
    print "Downloading %s" % url
    r = requests.get(url, stream=True)
    md5sum = None
    if r.ok:
        md5 = hashlib.md5()
        with repos.open_file(basename, 'wb') as output:
            for chunk in r.iter_content(chunk_size=512):
                output.write(chunk)
                md5.update(chunk)
        etag = get_md5sum_from_tumblr_headers(r.headers)
        md5sum = md5.hexdigest()
        if md5sum != etag and etag is not None:
            os.remove(filename)
            print etag, 'etag'
            print md5sum, 'md5sum'
            raise RuntimeError, "Bad checksum with %s" % url
        elif etag is None:
            print "checksum of %s is unavailable" % url
    return url_id, r.status_code, md5sum

    

def download_urlobjs(session, objs, repos, chunksize=20, processes=5,
                     ignore_gifs=True, thumb_urls=False):
    #urllist = [o.url for o in objs]
    paramlist = [(o.url, o.id, repos) for o in objs if \
                     not o.url.endswith('.gif')]
    giflist = [o for o in objs if o.url.endswith('.gif')]
    with transaction.manager:
        print "Ignoring %d gifs" % len(giflist)
        for o in giflist:
            o.status = 404
            session.add(o)
    grouped = chunks(paramlist, chunksize)
    pool = ThreadPool(processes=processes)
    count = 0
    for group in grouped:
        output = pool.map(download_url, group)
        with transaction.manager:
            model = TumblrPhotoUrl
            md5model = TumblrPhotoUrlMd5sum
            if thumb_urls:
                model = TumblrThumbnailUrl
                md5model = TumblrThumbnailUrlMd5sum
            for url_id, status, md5sum in output:
                tpu = session.query(model).get(url_id)
                tpu.status = status
                session.add(tpu)
                if md5sum is None:
                    print "Skipping md5sum for status %d" % status
                    continue
                md = session.query(md5model).get(url_id)
                if md is None:
                    #print "md is None", md5sum, url_id
                    md = md5model()
                    md.id = url_id
                    md.md5sum = md5sum
                    session.add(md)
                else:
                    #print "MD is %s" % md
                    md.md5sum = md5sum
                    session.add(md)
        count += 1
        print "Group %d processed." % count
        print "Sleeping for 0.1 second."
        time.sleep(0.1)
    
class TumblrPhotoManager(object):
    def __init__(self, session):
        self.session = session
        self.model = TumblrPhotoUrl
        self.repos = None
        self.ignore_gifs = False
        self.immediate_download = True
        self.get_thumbnail = True
        
    def set_local_path(self, dirname):
        self.repos = FileRepos(dirname)
            
    def _query(self):
        return self.session.query(TumblrPhotoUrl)

    def _thumb_query(self):
        return self.session.query(TumblrThumbnailUrl)
    
    def get(self, id):
        return self.session.query(TumblrPhotoUrl).get(id)

    def get_all_ids_query(self):
        qf = self.session.query
        q = qf(TumblrPhotoUrl.id)
        q = q.order_by(TumblrPhotoUrl.id)
        return q

    def get_all_ids(self):
        return self.get_all_ids_query().all()

    def get_all_thumb_ids_query(self):
        qf = self.session.query
        q = qf(TumblrThumbnailUrl.id)
        q = q.order_by(TumblrThumbnailUrl.id)
        return q

    def get_all_thumb_ids(self):
        return self.get_all_ids_query().all()

    
    def get_by_url(self, url):
        q = self._query()
        q = q.filter_by(url=url)
        objects = q.all()
        if not len(objects):
            return None
        if not len(objects) == 1:
            raise RuntimeError, "Too many"
        return objects.pop()
    
    def get_thumbnail_by_url(self, url):
        q = self._thumb_query()
        q = q.filter_by(url=url)
        objects = q.all()
        if not len(objects):
            return None
        if not len(objects) == 1:
            raise RuntimeError, "Too many"
        return objects.pop()
    
    def add_url(self, url):
        with transaction.manager:
            turl = TumblrPhotoUrl()
            turl.url = url
            self.session.add(turl)
        return self.session.merge(turl)

    def restore_url(self, data):
        with transaction.manager:
            turl = TumblrPhotoUrl()
            for key in ['id', 'url', 'status']:
                setattr(turl, key, data[key])
            self.session.add(turl)
        return self.session.merge(turl)

    def add_thumbnail_url(self, url):
        with transaction.manager:
            turl = TumblrThumbnailUrl()
            turl.url = url
            self.session.add(turl)
        return self.session.merge(turl)

    def url_exists(self, url):
        q = self.session.query(TumblrPhotoUrl).filter_by(url=url)
        return len(q.all())
    
    def thumbnail_url_exists(self, url):
        q = self.session.query(TumblrThumbnailUrl).filter_by(url=url)
        return len(q.all())
    
    def basename(self, url):
        return os.path.basename(url)

    def url_photo_filename(self, url):
        basename = os.path.basename(url)
        return self.repos.filename(basename)

    def photo_exists(self, url, filename=None):
        return self.repos.file_exists(url)

    def download_photo(self, url, dbobj):
        if url.endswith('.gif'):
            print "Skipping gif...", url
            return
        filename = self.url_photo_filename(url)
        basename = os.path.basename(url)
        if self.photo_exists(url, filename=filename):
            raise PhotoExistsError, "%s already exists." % filename
        r = requests.get(url, stream=True)
        if not r.ok:
            if r.status_code == 403:
                print "%s forbidden" % url
            elif r.status_code == 404:
                print "%s not available" % url
            elif r.status_code in [400, 500]:
                print "%s bad query" % url
            else:
                msg = "Tumblr returned %d for %s" 
                raise RuntimeError, msg % (r.status_code, url)
        else:
            with self.repos.open_file(basename, 'wb') as output:
                for chunk in r.iter_content(chunk_size=512):
                    output.write(chunk)
        #with transaction.manager:
        #    dbobj.status = r.status_code
        #    self.session.add(dbobj)
        with transaction.manager:
            turl = self.get_by_url(url)
            if turl is None:
                raise RuntimeError, "URL not in db"
            turl.status = r.status_code
            self.session.add(turl)
            turl = self.get_by_url(url)
            if turl.status != r.status_code:
                raise RuntimeError, "DB didn't take it %s" % turl.id
        return self.session.merge(turl)
            

    def update_photo(self, url_id):
        if not self.immediate_download:
            print "Skipping immediate update of %d" % url_id
            return
        self._update_photo(url_id)
        
    def update_thumbnail(self, url_id):
        if not self.immediate_download:
            print "Skipping immediate update of %d" % url_id
            return
        raise RuntimeError, 'not ready'
        self._update_photo(url_id)
        

    def _update_photo(self, url_id, localdir=None):
        turl = self.get(url_id)
        url = turl.url
        if not self.photo_exists(url):
            if turl.status in [403, 400]:
                print "Skipping forbidden url", url
                return
            basename = os.path.basename(url)
            if localdir is not None:
                local_filename = os.path.join(localdir, basename)
                if os.path.isfile(local_filename):
                    print "found", local_filename
                    self.repos.store_local_file(local_filename)
                else:
                    print "Downloading", basename
                    self.download_photo(url, turl)
                    pass
            else:
                print "Downloading", basename
                self.download_photo(url, turl)
        else:
            if turl.status != 200:
                turl.status = 200
        
    def update_photos(self, urls):
        download_urlobjs(self.session, urls, self.repos)
        

    def _make_md5queryOrig(self, urlclass, md5class):
        current_sums = self.session.query(md5class.id)
        current_sums = current_sums.subquery('current_sums')
        q = self.session.query(urlclass)
        q = q.filter(not_(urlclass.id.in_(current_sums)))
        for errorstatus in [400, 403, 404]:
            q = q.filter(urlclass.status != errorstatus)
        return q
    
    def _make_md5query(self, urlclass, md5class):
        stmt = ~exists().where(urlclass.id==md5class.id)
        q = self.session.query(urlclass)
        q = q.filter(stmt)
        for errorstatus in [400, 403, 404, 302]:
            q = q.filter(urlclass.status != errorstatus)
        return q
    
    def _get_all_remote_md5sums(self, urlclass, md5class):
        thumb_urls = False
        if urlclass is TumblrThumbnailUrl:
            print "WE have thumbs"
            thumb_urls = True
        q = self._make_md5query(urlclass, md5class)
        total = q.count()
        print "%d sums remaining" % total
        count = 0
        offset = 0
        limit = 10000
        q = q.offset(offset).limit(limit)
        rows = q.all()
        while len(rows):
            get_md5sums_for_urls(self.session, rows, thumb_urls=thumb_urls,
                                 chunksize=300, processes=8)
            count += 1
            offset += limit
            if not count % 1000:
                remaining = total - count
                print "%de urls remaining." % remaining
            q = self._make_md5query(urlclass, md5class)
            q = q.offset(offset).limit(limit)
            rows = q.all()
            
            
    def get_all_remote_photo_md5sums(self):
        self._get_all_remote_md5sums(TumblrPhotoUrl, TumblrPhotoUrlMd5sum)
            
    def get_all_remote_thumbnail_md5sums(self):
        self._get_all_remote_md5sums(TumblrThumbnailUrl,
                                     TumblrThumbnailUrlMd5sum)
        
    def _update_all_photos(self, thumbs=False):
        chunksize = 20
        processes = 5
        qfun = self._query
        urlclass = TumblrPhotoUrl
        if thumbs:
            chunksize = 300
            processes = 10
            qfun = self._thumb_query
            urlclass = TumblrThumbnailUrl
        limit = 10000
        offset = 0
        count = 0
        q = qfun().filter_by(status=None)
        q = q.order_by(urlclass.id)
        q = q.offset(offset).limit(limit)
        urls = q.all()
        while len(urls):
            download_urlobjs(self.session, urls, self.repos,
                             chunksize=chunksize, processes=processes,
                             thumb_urls=thumbs)
            count += 1
            offset += limit
            q = qfun().filter_by(status=None)
            q = q.order_by(urlclass.id)
            q = q.offset(offset).limit(limit)
            urls = q.all()
            print "Round %d finished." % count
            
    def update_all_thumbnails(self):
        self._update_all_photos(thumbs=True)
        
    def update_all_photos(self, localdir=None):
        self._update_all_photos(thumbs=False)
