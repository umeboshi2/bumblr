import os
import multiprocessing
from multiprocessing.pool import ThreadPool
import time

import transaction
import requests

from bumblr.database import TumblrPhotoUrl, TumblrThumbnailUrl
from bumblr.database import TumblrPostPhoto
from bumblr.filerepos import FileExistsError, FileRepos

class FileExistsError(Exception):
    pass
class PhotoExistsError(FileExistsError):
    pass

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


# download a url to a FileRepos
def download_url(utuple):
    url, url_id, repos = utuple
    if repos.file_exists(url):
        #raise FileExistsError, "%s already in repository." % url
        return url_id, 200
    basename = os.path.basename(url)
    filename = repos.filename(basename)
    print "Downloading %s" % url
    r = requests.get(url, stream=True)
    if r.ok:
        with repos.open_file(basename, 'wb') as output:
            for chunk in r.iter_content(chunk_size=512):
                output.write(chunk)
    return url_id, r.status_code

    

def download_urlobjs(session, objs, repos, chunksize=20, processes=5,
                     ignore_gifs=True):
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
            for url_id, status in output:
                tpu = session.query(TumblrPhotoUrl).get(url_id)
                tpu.status = status
                session.add(tpu)
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
            
    def get(self, id):
        return self.session.query(TumblrPhotoUrl).get(id)

    def get_by_url(self, url):
        q = self._query()
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

    def url_exists(self, url):
        q = self.session.query(TumblrPhotoUrl).filter_by(url=url)
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
        
    def update_all_photos(self, localdir=None):
        q = self._query().filter_by(status=None)
        urls = q.all()
        download_urlobjs(self.session, urls, self.repos)
            
    def update_photos(self, urls):
        download_urlobjs(self.session, urls, self.repos)
        
