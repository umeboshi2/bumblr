import os
from datetime import datetime

import transaction
import requests
from sqlalchemy import not_

from bumblr.database import TumblrPost, TumblrPostPhoto
from bumblr.database import TumblrBlog, TumblrBlogPost
from bumblr.database import TumblrLikedPost, TumblrPhotoUrl
from bumblr.database import TumblrThumbnailUrl, TumblrPostThumbnail

from bumblr.database import BlogProperty, TumblrBlogProperty
from bumblr.database import DEFAULT_BLOG_PROPERTIES
from bumblr.postmanager import TumblrPostManager

BLOGKEYS = ['name', 'title', 'url', 'description', 'posts',
            'followed', 'share_likes', 'ask', 'ask_page_title',
            'ask_anon', 'can_send_fan_mail', 'is_nsfw',]
# likes
#'facebook',
#            'facebook_opengraph_enabled', 'twitter_enabled',
#            'tweet', 'twitter_send']

class PropertyManager(object):
    def __init__(self, session):
        self.session = session
        self.model = BlogProperty
        if not len(self.session.query(self.model).all()):
            for prop in DEFAULT_BLOG_PROPERTIES:
                print "Adding default property %s" % prop
                self.add(prop)
                
    def _query(self):
        return self.session.query(self.model)
    
    def get(self, id):
        return self.session.query(self.model).get(id)

    def get_by_name(self, name):
        q = self._query().filter_by(name=name)
        rows = q.all()
        if not len(rows):
            return None
        return rows.pop()

    def add(self, name):
        p = self.get_by_name(name)
        if p is None:
            with transaction.manager:
                p = self.model()
                p.name = name
                self.session.add(p)
            p = self.session.merge(p)
        return p

    def tag_blog(self, blog_id, propname):
        prop = self.get_by_name(propname)
        q = self.session.query(TumblrBlogProperty)
        tbp = q.get((blog_id, prop.id))
        if tbp is None:
            with transaction.manager:
                tbp = TumblrBlogProperty()
                tbp.blog_id = blog_id
                tbp.property_id = prop.id
                self.session.add(tbp)
            tbp = self.session.merge(tbp)
        return tbp
    

class TumblrBlogManager(object):
    def __init__(self, session):
        self.session = session
        self.client = None
        self.limit = 20
        self.model = TumblrBlog
        self.posts = TumblrPostManager(self.session)
        self.properties = PropertyManager(self.session)
        
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

    def get_by_property_query(self, propname):
        prop = self.properties.get_by_name(propname)
        

    def add_blog_object(self, blog):
        with transaction.manager:
            b = self.model()
            for key in BLOGKEYS:
                setattr(b, key, blog[key])
            b.updated_remote = datetime.fromtimestamp(blog['updated'])
            b.updated_local = datetime.now()
            self.session.add(b)
        return self.session.merge(b)
    
    def add_blog(self, blog_name):
        info = self.client.blog_info(blog_name)
        if 'blog' not in info:
            if info['meta']['status'] == 404:
                print "%s not found" % blog_name
                return None
        return self.add_blog_object(info['blog'])
            
    def update_posts_for_blog(self, name, blog_id=None):
        if blog_id is None:
            blog = self.get_by_name(name)
        else:
            blog = self.get(blog_id)
        if blog is None:
            raise RuntimeError, "No blog named %s" % name
        blogposts = self.session.query(TumblrBlogPost.post_id)
        blogposts = blogposts.filter_by(blog_id=blog.id).subquery('blogposts')
        
        q = self.session.query(TumblrPost).filter_by(blog_name=blog.name)
        q = q.filter(not_(TumblrPost.id.in_(blogposts)))
        posts = q.all()
        total = len(posts)
        print "total", total
        count = 0
        if not total:
            print "Nothing to update for", blog.name
        for post in posts:
            tbp = self.session.query(TumblrBlogPost).get((blog.id, post.id))
            count += 1
            if tbp is None:
                with transaction.manager:
                    tbp = TumblrBlogPost()
                    tbp.blog_id = blog.id
                    tbp.post_id = post.id
                    self.session.add(tbp)
                    print "Added %d for %s." % (post.id, blog.name)
            if not count % 100:
                remaining = total - count
                print "%d posts remaining for %s" % (remaining, blog.name)
                
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
            blog_name = blog['name']
            if self.get_by_name(blog_name) is None:
                print "Adding %s" % blog_name
                b = self.add_blog(blog_name)
                if b is not None:
                    self.properties.tag_blog(b.id, 'followed')
        while len(current_blogs):
            offset += limit
            blogs = self.client.following(offset=offset, limit=limit)
            current_blogs = blogs['blogs']
            for blog in current_blogs:
                blog_name = blog['name']
                if self.get_by_name(blog_name) is None:
                    print "Adding %s" % blog_name
                    b = self.add_blog(blog_name)
                    if b is not None:
                        self.properties.tag_blog(b.id, 'followed')
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
        
        
    def sample_blog_likes(self, amount):
        import random
        blogs = self._query().all()
        random.shuffle(blogs)
        for b in blogs:
            print "sampling %d likes from %s" % (amount, b.name)
            self.posts.get_blog_likes(b.name, amount)


    def make_blog_directory(self, blogname, blogpath):
        blog = self.get_by_name(blogname)
        if blog is None:
            raise RuntimeError, "%s doesn't exist." % blogname
        if not os.path.isdir(blogpath):
            os.makedirs(blogpath)
        current_blog_files = os.listdir(blogpath)
        repos = self.posts.photos.repos
        q = self.session.query(TumblrPost).join(TumblrBlogPost)
        q = q.filter(TumblrBlogPost.blog_id == blog.id)
        q = q.order_by(TumblrPost.id)
        for post in q:
            if post.type != 'photo':
                continue
            photoquery = self.session.query(TumblrPhotoUrl).join(TumblrPostPhoto).filter(TumblrPostPhoto.post_id == post.id)
            for tpu in photoquery:
                url = tpu.url
                basename = os.path.basename(url)
                if repos.file_exists(basename):
                    if len(basename.split('.')) == 2:
                        ext = basename.split('.')[1]
                    else:
                        print "WARNING! BAD GUESS"
                        ext = '.jpg'
                    filebase = '%d-%d.%s' % (post.id, tpu.id, ext)
                    filename = os.path.join(blogpath, filebase)
                    #if not os.path.isfile(filename):
                    if filebase not in current_blog_files:
                        print "Linking", filename
                        os.link(repos.filename(basename), filename)
                    
                
    def make_thumb_directory(self, blogname, blogpath):
        blog = self.get_by_name(blogname)
        if blog is None:
            raise RuntimeError, "%s doesn't exist." % blogname
        if not os.path.isdir(blogpath):
            os.makedirs(blogpath)
        current_blog_files = os.listdir(blogpath)
        repos = self.posts.photos.repos
        q = self.session.query(TumblrPost).join(TumblrBlogPost)
        q = q.filter(TumblrBlogPost.blog_id == blog.id)
        q = q.order_by(TumblrPost.id)
        for post in q:
            if post.type != 'photo':
                continue
            photoquery = self.session.query(TumblrThumbnailUrl).join(TumblrPostThumbnail).filter(TumblrPostThumbnail.post_id == post.id)
            for tpu in photoquery:
                url = tpu.url
                basename = os.path.basename(url)
                if repos.file_exists(basename):
                    if len(basename.split('.')) == 2:
                        ext = basename.split('.')[1]
                    else:
                        print "WARNING! BAD GUESS"
                        ext = '.jpg'
                    filebase = '%d-%d.%s' % (post.id, tpu.id, ext)
                    filename = os.path.join(blogpath, filebase)
                    #if not os.path.isfile(filename):
                    if filebase not in current_blog_files:
                        print "Linking", filename
                        os.link(repos.filename(basename), filename)
                    
                
            
    def foobar(self):
        pass
    
