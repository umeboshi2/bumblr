import os

import transaction
import requests

from bumblr.database import TumblrPost

POSTKEYS = ['id', 'blog_name', 'post_url', 'type', 'timestamp',
            'date', 'format', 'liked']


class BaseManager(object):
    def __init__(self, client, session, info=None):
        self.client = client
        self.session = session
        self.client_info = info
        if self.client_info is None:
            self.client_info = client.info()
        self.limit = 50

    def set_client(self, client):
        self.client = client
        self.client_info = client.info()
        
        

class DashboardManager(object):
    def __init__(self, session):
        self.session = session
        self.client = None
        self.client_info = None
        self.limit = 50
        
        
    def set_client(self, client):
        self.client = client
        self.client_info = client.info()
        
    def _query(self):
        return self.session.query(TumblrPost)
    
    def get(self, id):
        return self.session.query(TumblrPost).get(id)
    
    def add_post(self, post):
        with transaction.manager:
            p = TumblrPost()
            for key in POSTKEYS:
                setattr(p, key, post[key])
            if False:
                for key in ['source_url', 'source_title']:
                    if key in post:
                        setattr(p, key, post[key])
            p.content = post
            self.session.add(p)
        return self.session.merge(p)

    def get_posts(self):
        posts = self.client.dashboard()['posts']
        total_posts = len(posts)
        while posts:
            post = posts.pop()
            if self.get(post['id']) is None:
                self.add_post(post)
                print "added post from %s" % post['blog_name']
            print "%d processed." % (total_posts - len(posts))
            
            
class BaseBlogManager(object):
    def __init__(self, session):
        self.session = session
        self.client = None
        self.limit = 50
        
        
    def set_client(self, client):
        self.client = client

    def _query(self):
        return self.session.query(TumblrPost)
    
    def get(self, id):
        return self.session.query(TumblrPost).get(id)

    def add_post(self, post):
        with transaction.manager:
            p = TumblrPost()
            for key in POSTKEYS:
                setattr(p, key, post[key])
            if False:
                for key in ['source_url', 'source_title']:
                    if key in post:
                        setattr(p, key, post[key])
            p.content = post
            self.session.add(p)
        return self.session.merge(p)

    def _get_all_posts(self, blogname):
        offset = 0
        limit = self.limit
        posts = self.client.posts(blogname, offset=offset, limit=limit)
        if 'total_posts' not in posts:
            return []
        total_post_count = posts['total_posts']
        all_posts = list()
        these_posts = posts['posts']
        these_posts = posts['posts']
        if len(these_posts) != limit:
            raise RuntimeError, "Too few posts %d" % len(these_posts)
        all_posts += posts['posts']
        while len(all_posts) < total_post_count:
            offset += limit
            print "Getting from %d" % offset
            posts = self.client.posts(blogname, offset=offset, limit=limit)
            plist = posts['posts']
            all_posts += plist
            num_posts_left = total_post_count - len(all_posts)
            print "%d posts remaining." % num_posts_left
        return all_posts

    def get_all_posts(self, blogname):
        all_posts = self._get_all_posts(blogname)
        for post in all_posts:
            if self.get(post['id']) is None:
                self.add_post(post)
                
                                  
    def update_posts(self, blogname):
        pass
    
