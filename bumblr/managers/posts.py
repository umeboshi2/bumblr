import os

import transaction
import requests

from bumblr.database2 import Post
from bumblr.database2 import BlogPost

from bumblr.managers.base import BaseManager



POSTKEYS = ['id', 'blog_name', 'post_url', 'type', 'timestamp',
            'date', 'source_url', 'source_title', 'liked',
            'followed']

class PostManager(BaseManager):
    def __init__(self, session):
        super(PostManager, self).__init__(session, Post)
        self.client = None
        self.client_info = None
        self.limit = 20
        # add photo manager

    def set_client(self, client):
        self.client = client
        self.client_info = self.client.info()
        # set photo manager client
        
    def blogname_query(self, name):
        return self.query().filter_by(blog_name=name)
    

    def get_post_photos_query(self, post_id, thumbs=False):
        raise NotImplemented, 'FIXME'
    
    def get_ranged_posts(self, start, end):
        raise NotImplemented, 'FIXME'
    
    def add_post(self, post):
        if self.get(post['id']) is not None:
            msg = "Post %d for %s already in database."
            print msg  % (post['id'], post['blog_name'])
            return
        with transaction.manager:
            p = Post()
            for key in POSTKEYS:
                if key in post:
                    setattr(p, key, post[key])
            p.content = post
            self.session.add(p)
        p = self.session.merge(p)
            
    def _get_all_posts(self, blogname, total_desired, offset, blog_id):
        limit = self.limit
        current_post_count = 0
        posts = self.client.posts(blogname, offset=offset, limit=limit)
        if 'total_posts' not in posts:
            return []
        total_post_count = posts['total_posts'] - offset
        if total_desired is not None:
            if total_desired > total_post_count:
                print 'too many posts desired.'
                total_desired = total_post_count
            total_post_count = total_desired
        all_posts = list()
        these_posts = posts['posts']
        if len(these_posts) != limit:
            if len(these_posts) != total_post_count:
                raise RuntimeError, "Too few posts %d" % len(these_posts)
        while current_post_count < total_post_count:
            ignored_post_count = 0
            batch_length = len(these_posts)
            while len(these_posts) and total_post_count:
                post = these_posts.pop()
                if blog_id is not None:
                    blogpost_query = self.session.query(BlogPost)
                    blogpost = blogpost_query.get((blog_id, post['id']))
                    if blogpost is not None:
                        ignored_post_count += 1
                        #msg = "Ignoring this post %d %d" 
                        #print msg % (blog_id, post['id'])
                if batch_length == ignored_post_count:
                    msg = "We think we have it..... %d %d"
                    print msg  % (len(these_posts), ignored_post_count)
                    # FIXME we need a better method to break
                    # away
                    total_post_count = 0
                current_post_count += 1
                if self.get(post['id']) is None:
                    self.add_post(post)
            offset += limit
            print "Getting from tumblr at offset %d" % offset
            posts = self.client.posts(blogname, offset=offset, limit=limit)
            these_posts = posts['posts']
            remaining = total_post_count - current_post_count
            print "%d posts remaining for %s." % (remaining, blogname)
            
    def get_all_posts(self, blogname, total_desired=None, offset=0,
                      blog_id=None):
        self._get_all_posts(blogname, total_desired, offset, blog_id)

    def get_dashboard_posts(self, limit=20, offset=0):
        if self.client is None:
            raise RuntimeError, "Need to set client"
        posts = self.client.dashboard(limit=limit, offset=offset)['posts']
        total_posts = len(posts)
        while posts:
            post = posts.pop()
            if self.get(post['id']) is None:
                self.add_post(post)
                print "added post from %s" % post['blog_name']
            print "%d processed." % (total_posts - len(posts))

    def _client_get_likes(self, offset, limit, blog_name=None):
        raise NotImplemented, 'FIXME'
        if blog_name is None:
            return self.client.likes(offset=offset, limit=limit)
        else:
            return self.client.blog_likes(blog_name,
                                          offset=offset, limit=limit)
        
    def _set_liked_post(self, post_id, blog_id=None):
        raise NotImplemented, 'FIXME'
        with transaction.manager:
            if blog_id is None:
                model = TumblrMyLikedPost()
            else:
                model = TumblrLikedPost()
                model.blog_id = blog_id
            model.post_id = post_id
            self.session.add(model)
        return self.session.merge(model)
    
    
    def _get_likes(self, blog_name=None, total_desired=None):
        raise NotImplemented, 'FIXME'
        if self.client is None:
            raise RuntimeError, "Need to set client"
        offset = 0
        limit = 50
        if blog_name is None:
            blog_id = None
        else:
            blog_id = None
        posts = self._client_get_likes(offset, limit, blog_name=blog_name)
        if 'liked_count' not in posts:
            return []
        total_post_count = posts['liked_count']
        if total_desired is not None:
            if total_desired > total_post_count:
                print "Too many posts desired."
                total_desired = total_post_count
            total_post_count = total_desired
        current_posts = posts['liked_posts']
        post_count = len(current_posts)
        for post in current_posts:
            if self.get(post['id']) is None:
                self.add_post(post)
        while post_count < total_post_count:
            offset += limit
            posts = self._client_get_likes(offset, limit,
                                           blog_name=blog_name)
            current_posts = posts['liked_posts']
            for post in current_posts:
                if self.get(post['id']) is None:
                    self.add_post(post)
            post_count += len(current_posts)
            remaining = total_post_count - post_count
            print "%d posts remaining." % remaining
            
    def get_my_likes(self, total_desired=None):
        raise NotImplemented, 'FIXME'
        return self._get_likes(total_desired=total_desired)

    def _get_blog_likes(self, blogname, total_desired=None):
        raise NotImplemented, 'FIXME'
        return self._get_likes(blog_name=blogname,
                                  total_desired=total_desired)
        
    def get_blog_likes(self, blogname, total_desired=None):
        raise NotImplemented, 'FIXME'
        return self._get_blog_likes(blogname, total_desired=total_desired)
    
