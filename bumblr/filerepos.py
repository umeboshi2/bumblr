import os
import hashlib
import uuid

FILE_EXTENSIONS = dict(jpg='jpg', png='png',
                       gif='gif')

FILE_EXTENSIONS = ['jpg', 'png', 'gif']

def _dirname_common(filename):
    m = hashlib.md5()
    m.update(filename)
    return m.hexdigest()


def dirname_top(filename):
    d = _dirname_common(filename)
    return d[:2]

def dirname_bottom(filename):
    d = _dirname_common(filename)
    return d[-2:]

class FileExistsError(Exception):
    pass

class FileRepos(object):
    def __init__(self, path):
        self.path = path

    def _repos_dir(self, filename):
        top = dirname_top(filename)
        bottom = dirname_bottom(filename)
        return os.path.join(self.path, top, bottom)

    def _repos_name(self, basename):
        return os.path.join(self._repos_dir(basename), basename)
    
    def _file_exists(self, basename, dirname):
        return os.path.isfile(os.path.join(dirname, basename))
        
    def file_exists(self, fullpath):
        basename = os.path.basename(fullpath)
        return os.path.isfile(self._repos_name(basename))

    def filename(self, basename):
        return self._repos_name(basename)
    
    def store_local_file(self, fullpath):
        basename = os.path.basename(fullpath)
        destname = self._repos_name(basename)
        if os.path.isfile(destname):
            raise FileExistsError, "%s already exists" % basename
        rdir = self._repos_dir(basename)
        if not os.path.isdir(rdir):
            os.makedirs(rdir)
        os.rename(fullpath, destname)

    def open_file(self, basename, mode='rb'):
        filename = self._repos_name(basename)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return file(filename, mode)
    
        
        
class UrlRepos(object):
    def __init__(self, path):
        self.path = path

    def get_uuid(self, url):
        return uuid.uuid5(uuid.NAMESPACE_URL, bytes(url))

    def _get_top_bottom(self, uuid):
        h = uuid.hex
        return tuple(h.split(h[2:-2]))
    
    def _repos_dir(self, url, uuid=None):
        if uuid is None:
            uuid = self.get_uuid(url)
        top, bottom = self._get_top_bottom(uuid)
        return os.path.join(self.path, top, bottom)

    def _basename(self, url, uuid):
        extension = None
        for e in FILE_EXTENSIONS:
            if url.endswith('.%s' % e):
                extension = e
                break
        if extension is None:
            print "Guessing filetype for %s" % url
            extension = 'jpg'
        return '%s.%s' % (uuid.hex, extension)
        
    def _repos_name(self, url):
        uuid = self.get_uuid(url)
        dirname = self._repos_dir(url, uuid)
        basename = self._basename(url, uuid)
        return os.path.join(dirname, basename)
    
    def relname(self, url):
        uuid = self.get_uuid(url)
        top, bottom = self._get_top_bottom(uuid)
        return os.path.join(top, bottom, self._basename(url, uuid))

    def file_exists(self, url):
        return os.path.isfile(self._repos_name(url))
    
    def filename(self, url):
        return self._repos_name(url)

        

    def open_file(self, url, mode='rb'):
        filename = self._repos_name(url)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return file(filename, mode)
        
