import os
from datetime import datetime

import transaction
import requests

from bumblr.database import TumblrPost, TumblrPostPhoto
from bumblr.database import TumblrBlog
from bumblr.postmanager import TumblrPostManager

BLOGKEYS = ['name', 'title', 'url', 'description']

class TumblrBlogManager(object):
    def __init__(self, session):
        self.session = session
        self.client = None
        self.limit = 20
        self.model = TumblrBlog
        self.posts = TumblrPostManager(self.session)
        
    def set_client(self, client):
        self.client = client
        self.posts.set_client(client)
        self.client_info = client.info()
        
    def _query(self):
        return self.session.query(self.model)
    
    def get(self, id):
        return self.session.query(self.model).get(id)

    # we are certain name is unique
    def get_by_name(self, name):
        q = self._query().filter_by(name=name)
        rows = q.all()
        if not len(rows):
            return None
        return rows.pop()
    
    def get_all_ids_query(self):
        return self.session.query(self.model.id)
    
    def get_all_ids(self):
        q = self.get_all_ids_query()
        return q.all()
    
    def add_blog(self, blog):
        with transaction.manager:
            b = self.model()
            for key in BLOGKEYS:
                setattr(b, key, blog[key])
            b.updated_remote = datetime.fromtimestamp(blog['updated'])
            b.updated_local = datetime.now()
            self.session.add(b)
        return self.session.merge(b)

    def get_followed_blogs(self):
        if self.client is None:
            raise RuntimeError, "Need to set client"
        offset = 0
        limit = self.limit
        blogs = self.client.following(offset=offset, limit=limit)
        total_blog_count = blogs['total_blogs']
        current_blogs = blogs['blogs']
        blog_count = len(current_blogs)
        for blog in current_blogs:
            if self.get_by_name(blog['name']) is None:
                print "Adding %s" % blog
                self.add_blog(blog)
        while len(current_blogs):
            offset += limit
            blogs = self.client.following(offset=offset, limit=limit)
            current_blogs = blogs['blogs']
            for blog in current_blogs:
                if self.get_by_name(blog['name']) is None:
                    print "Adding %s" % blog['name']
                    self.add_blog(blog)
            blog_count += len(current_blogs)
            remaining = total_blog_count - blog_count
            print '%d blogs remaining.' % remaining

    def sample_blogs(self, amount):
        import random
        blogs = self._query().all()
        random.shuffle(blogs)
        for b in blogs:
            print "sampling %d posts from %s" % (amount, b.name)
            self.posts.get_all_posts(b.name, amount)
        
        
    
