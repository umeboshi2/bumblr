import os
import hashlib

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

