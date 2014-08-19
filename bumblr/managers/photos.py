import os
import multiprocessing
from multiprocessing.pool import ThreadPool
import time
import hashlib

import transaction
import requests
from sqlalchemy import not_
from sqlalchemy import exists

from bumblr.database import Photo, PhotoUrl, PhotoSize

from bumblr.filerepos import FileExistsError, FileRepos
from bumblr.filerepos import UrlRepos

from bumblr.managers.base import BaseManager

from bumblr.managers.util import chunks, get_md5sum_from_tumblr_headers
from bumblr.managers.util import get_md5sum_for_file
from bumblr.managers.util import get_md5sum_with_head_request

class FileExistsError(Exception):
    pass

class PhotoExistsError(FileExistsError):
    pass

class BadRequestError(Exception):
    pass

def download_url(utuple):
    url, url_id, repos = utuple
    if repos.file_exists(url):
        # FIXME: need better method of doing this
        # status 777 means local file exists but
        # remains unverified
        return url_id, 777, None
    filename = repos.filename(url)
    print "Downloading %s" % url
    r = requests.get(url, stream=True)
    md5sum = None
    if r.ok:
        md5 = hashlib.md5()
        with repos.open_file(url, 'wb') as output:
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

        

def get_photo_sizes(photo):
    sizes = dict()
    sizes['alt'] = list()
    sizes['thumb'] = None
    sizes['orig'] = photo['original_size']
    for altsize in photo['alt_sizes']:
        if altsize['url'] == sizes['orig']['url']:
            #print "Orig", sizes['orig']
            #print "ALT", altsize
            continue
        width = altsize['width']
        #if width == sizes['orig']['width']:
        #    continue
        if width == 100:
            sizes['thumb'] = altsize
        elif width == 75:
            sizes['smallsquare'] = altsize
        else:
            sizes['alt'].append(altsize)
    return sizes


class PhotoManager(BaseManager):
    def __init__(self, session):
        super(PhotoManager, self).__init__(session, Photo)
        self.repos = None
        self.ignore_gifs = False
        self.get_thumbnail = True
        self.get_orig = False
        self.PhotoUrl = PhotoUrl
        self.PhotoSize = PhotoSize
        
    def set_local_path(self, dirname):
        self.repos = UrlRepos(dirname)
        

    def urlquery(self):
        return self.session.query(PhotoUrl)

    def get_photo_by_url(self, url):
        q = self.urlquery().filter_by(url=url)
        rows = q.all()
        if not len(rows):
            return None
        return rows.pop()

    def _add_size(self, photo, phototype, sizedata):
        pu = PhotoUrl()
        pu.phototype = phototype
        for key in ['url', 'width', 'height']:
            setattr(pu, key, sizedata[key])
        # database defaults to false
        if phototype == 'thumb' and self.get_thumbnail:
            pu.keep_local = True
        pu.filename = self.repos.relname(sizedata['url'])
        self.session.add(pu)
        pu = self.session.merge(pu)
        ps = PhotoSize()
        ps.photo_id = photo.id
        ps.url_id = pu.id
        self.session.add(ps)
            
    def add_photo(self, photo, altsizes=False):
        sizes = get_photo_sizes(photo)
        with transaction.manager:
            p = self.model()
            p.caption = photo['caption']
            if 'exif' in photo:
                p.exif = photo['exif']
            self.session.add(p)
            p = self.session.merge(p)
            for phototype in ['orig', 'thumb', 'smallsquare']:
                pudata = sizes[phototype]
                if pudata is not None:
                    pu = self.get_photo_by_url(pudata['url'])
                    if pu is None:
                        #print "Adding %s" % phototype
                        self._add_size(p, phototype, pudata)
            if altsizes:
                for pudata in sizes['alt']:
                    pu = self.get_photo_by_url(pudata['url'])
                    if pu is None:
                        self._add_size(p, 'alt', pudata)
        return self.session.merge(p)
    
