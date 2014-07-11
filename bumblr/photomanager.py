import os
import multiprocessing
from multiprocessing.pool import ThreadPool

import transaction
import requests

from bumblr.database import TumblrPhotoUrl
from bumblr.database import TumblrPostPhoto
from bumblr.filerepos import FileExistsError, FileRepos

class PhotoExistsError(Exception):
    pass


class TumblrPhotoManager(object):
    def __init__(self, session):
        self.session = session
        self.model = TumblrPhotoUrl
        self.repos = None
        
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
            elif r.status_code == 400:
                print "%s bad query" % url
            else:
                msg = "Tumblr returned %d for %s" 
                raise RuntimeError, msg % (r.status_code, url)
        else:
            with self.repos.open_file(basename, 'wb') as output:
                for chunk in r.iter_content(chunk_size=512):
                    output.write(chunk)
        with transaction.manager:
            dbobj.status = r.status_code
            self.session.add(dbobj)
            


    def update_photo(self, url):
        pass

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
        urls = self._query().all()
        params = [u.id for u in urls]
        pool = ThreadPool(processes=5)
        output = pool.map(self._update_photo, params)
        
    def update_all_photosOrig(self, localdir=None):
        for turl in self._query():
            url = turl.url
            if not self.photo_exists(url):
                if turl.status in [403, 400]:
                    print "Skipping forbidden url", url
                    continue
                basename = os.path.basename(url)
                if localdir is not None:
                    local_filename = os.path.join(localdir, basename)
                    if os.path.isfile(local_filename):
                        print "found", local_filename
                        self.repos.store_local_file(local_filename)
                    else:
                        #print "Downloading", basename
                        #self.download_photo(url, turl)
                        pass
                else:
                    print "Downloading", basename
                    self.download_photo(url, turl)
            else:
                if turl.status != 200:
                    turl.status = 200
                    
