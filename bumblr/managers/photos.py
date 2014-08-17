import os
import multiprocessing
from multiprocessing.pool import ThreadPool
import time
import hashlib

import transaction
import requests
from sqlalchemy import not_
from sqlalchemy import exists

from bumblr.database2 import Photo, PhotoUrl, PhotoSize

from bumblr.filerepos import FileExistsError, FileRepos
from bumblr.filerepos import UrlRepos

from bumblr.managers.base import BaseManager


class FileExistsError(Exception):
    pass

class PhotoExistsError(FileExistsError):
    pass

class BadRequestError(Exception):
    pass

def get_photo_sizes(photo):
    sizes = dict()
    sizes['alt'] = list()
    sizes['orig'] = photo['original_size']
    for altsize in photo['alt_sizes']:
        width = altsize['width']
        if width == sizes['orig']['width']:
            continue
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
        
    def set_local_path(self, dirname):
        self.repos = FileRepos(dirname)
            

    def add_photo(self, photo):
        
    
