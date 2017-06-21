import os

import transaction
import requests

from bumblr.database import Post, PostContent
from bumblr.database import BlogPost, PostPhoto

from bumblr.managers.base import BaseManager
from bumblr.managers.photos import PhotoManager


POSTKEYS = ['id', 'blog_name', 'post_url', 'type', 'timestamp',
            'date', 'source_url', 'source_title', 'liked',
            'followed']

class PostManager(BaseManager):
    def __init__(self, session):
        super(PostManager, self).__init__(session, Post)
        # add photo manager
        self.photos = PhotoManager(self.session)

    def blogname_query(self, name):
        return self.query().filter_by(blog_name=name)
    

    def _get_post_pictures_query(self, post_id, phototype):
        photoclass = self.photos.model
        urlclass = self.photos.PhotoUrl
        sizeclass = self.photos.PhotoSize
        q = self.session.query(urlclass, sizeclass, photoclass)
        q = q.join(sizeclass).join(photoclass).join(PostPhoto)
        q = q.filter(PostPhoto.post_id == post_id)
        q = q.filter(urlclass.phototype == phototype)
        return q
        
    def get_post_thumbs_query(self, post_id):
        return self._get_post_pictures_query(post_id, 'thumb')

    def get_post_photos_query(self, post_id):
        return self._get_post_pictures_query(post_id, 'orig')

    def get_post_thumbs(self, post_id):
        return self.get_post_thumbs_query(post_id).all()
        
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
            self.session.add(p)
            p = self.session.merge(p)
            pc = PostContent()
            pc.id = p.id
            pc.content = post
            self.session.add(pc)
        p = self.session.merge(p)
        if post['type'] == 'photo':
            for photo in post['photos']:
                #print "PHOTO is", photo
                ph = self.photos.add_photo(p.id, photo)
                print "photo %d for post %d" % (ph.id, p.id)
        
            
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
    
