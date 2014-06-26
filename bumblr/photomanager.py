import os

import transaction
import requests

from bumblr.database import TumblrPhotoUrl

class PhotoExistsError(Exception):
    pass


class TumblrPhotoManager(object):
    def __init__(self, session):
        self.session = session
        self.dirname = None
        
    def set_local_path(self, dirname):
        self.dirname = dirname
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
            
    def _query(self):
        return self.session.query(TumblrPhotoUrl)
            
    def get(self, id):
        return self.session.query(TumblrPhotoUrl).get(id)
    
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
        return os.path.join(self.dirname, basename)        

    def photo_exists(self, url, filename=None):
        if filename is None:
            filename = self.url_photo_filename(url)
        return os.path.exists(filename)

    def download_photo(self, url):
        filename = self.url_photo_filename(url)
        if self.photo_exists(url, filename=filename):
            raise PhotoExistsError, "%s already exists." % filename
        r = requests.get(url, stream=True)
        if not r.ok:
            if r.status_code == 403:
                print "%s forbidden" % url
            else:
                msg = "Tumblr returned %d for %s" 
                raise RuntimeError, msg % (r.status_code, url)
            
        with file(filename, 'wb') as output:
            for chunk in r.iter_content(chunk_size=512):
                output.write(chunk)
        
