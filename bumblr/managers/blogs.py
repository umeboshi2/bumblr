import os
from datetime import datetime
import random

import transaction
import requests
from sqlalchemy import not_
from sqlalchemy import exists
from sqlalchemy import func

from bumblr.database import Blog, BlogInfo
from bumblr.database import BlogProperty, BlogPropertyName
from bumblr.database import DEFAULT_BLOG_PROPERTIES
from bumblr.database import Post, BlogPost


from bumblr.managers.base import BaseManager
from bumblr.managers.posts import PostManager


BLOGINFOKEYS = ['name', 'title', 'url', 'description', 'posts',
            'followed', 'share_likes', 'ask', 'ask_page_title',
            'ask_anon', 'can_send_fan_mail', 'is_nsfw', 'updated',]


class PropertyManager(object):
    def __init__(self, session):
        self.session = session
        self.model = BlogPropertyName
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
        q = self.session.query(BlogProperty)
        tbp = q.get((blog_id, prop.id))
        if tbp is None:
            with transaction.manager:
                tbp = BlogProperty()
                tbp.blog_id = blog_id
                tbp.property_id = prop.id
                self.session.add(tbp)
            tbp = self.session.merge(tbp)
        return tbp
    

class BlogInfoManager(BaseManager):
    def __init__(self, session):
        super(BlogInfoManager, self).__init__(session, BlogInfo)

    def add_bloginfo_object(self, bloginfo, blog_id):
        with transaction.manager:
            b = self.model()
            for key in BLOGINFOKEYS:
                setattr(b, key, bloginfo[key])
            b.id = blog_id
            self.session.add(b)
        return self.session.merge(b)

    def get_remote_blog_info(self, blog_name):
        info = self.client.blog_info(blog_name)
        if 'blog' not in info:
            if info['meta']['status'] == 404:
                print "%s not found" % blog_name
                return None
        return info['blog']
    
    
    def _update_blog_info(self, blog_id, blogdata):
        object_updated = False
        with transaction.manager:
            b = self.get(blog_id)
            if b is None:
                raise RuntimeError, "No object to update"
            for key in BLOGINFOKEYS:
                value = blogdata[key]
                dbvalue = getattr(b, key)
                if value != dbvalue:
                    msg = "%s.%s has changed from %s ------> %s"
                    print msg % (b.name, key, dbvalue, value)
                    setattr(b, key, value)
                    object_updated = True
            self.session.add(b)
        if object_updated:
            return self.session.merge(b)

    def update_blog_info(self, blog_id):
        b = self.get(blog_id)
        bloginfo = self.get_remote_blog_info(b.name)
        return self._update_blog_info(b.id, bloginfo)
    
class BlogManager(BaseManager):
    def __init__(self, session):
        super(BlogManager, self).__init__(session, Blog)
        self.info = BlogInfoManager(self.session)
        self.posts = PostManager(self.session)
        self.properties = PropertyManager(self.session)
        
    def set_client(self, client):
        super(BlogManager, self).set_client(client)
        for manager in [self.info, self.posts]:
            manager.client = client
            manager.client_info = self.client_info
        
    def _range_filter(self, query, start, end):
        query = query.filter(self.model.updated_remote >= start)
        query = query.filter(self.model.updated_remote <= end)
        return query
    
    # we are certain name is unique
    def get_by_name(self, name):
        q = self.query().join(BlogInfo).filter(BlogInfo.name == name)
        rows = q.all()
        if not len(rows):
            return None
        return rows.pop()
    

    def get_ranged_blogs(self, start, end, timestamps=False):
        if timestamps:
            start, end = convert_range_to_datetime(start, end)
        q = self.session.query(self.model)
        q = self._range_filter(q, start, end)
        return q.all()
    
    def get_by_property_query(self, propname):
        prop = self.properties.get_by_name(propname)
        
    def get_blog_posts_query(self, name, blog=None, type=None):
        if blog is None:
            blog = self.get_by_name(name)
        q = self.session.query(Post).join(BlogPost)
        q = q.filter(BlogPost.blog_id==blog.id)
        if type is not None:
            q = q.filter_by(type=type)
        q = q.order_by(Post.id)
        return q
            
    def get_blog_posts(self, name, offset=0, limit=20, blog=None, type=None):
        q = self.get_blog_posts_query(name, blog=blog, type=type)
        q = q.offset(offset).limit(limit)
        return q.all()

    def add_blog_object(self, blog):
        dbobj = self.get_by_name(blog['name'])
        if dbobj is not None:
            raise RuntimeError, '%s already in database' % blog['name']
        with transaction.manager:
            b = Blog()
            self.session.add(b)
        b = self.session.merge(b)
        bloginfo = self.info.add_bloginfo_object(blog, b.id)
        with transaction.manager:
            b.updated_remote = datetime.fromtimestamp(bloginfo.updated)
            b.updated_local = datetime.now()
            self.session.add(b)
        return self.session.merge(b)
    
    def add_blog(self, blog_name):
        bloginfo = self.info.get_remote_blog_info(blog_name)
        return self.add_blog_object(bloginfo)


    def _update_blog(self, blogobj):
        newinfo = self.info.update_blog_info(blogobj.id)
        
    def _update_blog(self, blog_id):
        b = self.get(blog_id)
        bloginfo = self.info.update_blog_info(b.id)
        if bloginfo is not None:
            b.updated_remote = datetime.fromtimestamp(bloginfo.updated)
            b.updated_local = datetime.now()
            with transaction.manager:
                self.session.add(b)
            return self.session.merge(b)

    def update_blog(self, name, blog_id=None):
        if blog_id is not None:
            return self._update_blog(blog_id)
        b = self.get_by_name(name)
        return self._update_blog(b.id)
    
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

    def sample_blogs(self, amount, update_first=False):
        blogs = self.query().all()
        random.shuffle(blogs)
        for b in blogs:
            if update_first:
                print "updating posts for %s" % b.info.name
                self.update_posts_for_blog('ignore', blog_id=b.id)
            blog = self.update_blog(b.info.name)
            if blog is not None:
                b = blog
                print "Blog %s updated" % b.info.name
                q = self.session.query(BlogPost)
                q = q.filter_by(blog_id=b.id)
                print "sampling %d posts from %s" % (amount, b.info.name)
                self.posts.get_all_posts(b.info.name, amount, blog_id=b.id)
                self.update_posts_for_blog('ignore', blog_id=b.id)
            else:
                print "Skipping", b.info.name
                
        
    def update_posts_for_blog(self, name, blog_id=None, blog=None):
        if blog is None:
            if blog_id is None:
                blog = self.get_by_name(name)
            else:
                blog = self.get(blog_id)
        if blog is None:
            raise RuntimeError, "No blog named %s" % name
        q = self.session.query(Post).filter_by(blog_name=blog.info.name)
        stmt = ~exists().where(BlogPost.post_id==Post.id)
        q = q.filter(stmt)

        posts = q.all()
        total = len(posts)
        print "total for %s: %d" % (blog.info.name, total)
        count = 0
        if not total:
            print "Nothing to update for", blog.info.name
        for post in posts:
            tbp = self.session.query(BlogPost).get((blog.id, post.id))
            count += 1
            if tbp is None:
                with transaction.manager:
                    tbp = BlogPost()
                    tbp.blog_id = blog.id
                    tbp.post_id = post.id
                    self.session.add(tbp)
                    #print "Added %d for %s." % (post.id, blog.name)
            if not count % 100:
                remaining = total - count
                print "%d posts remaining for %s" % (remaining, blog.info.name)

    def update_all_posts(self):
        for b in self.query():
            self.update_posts_for_blog(b.info.name, blog=b)
            
    def _make_blog_directory(self, blogname, blogpath, thumbnails=False):
        raise NotImplemented, 'FIXME'
    def make_blog_directory(self, blogname, blogpath):
        raise NotImplemented, 'FIXME'
        self._make_blog_directory(blogname, blogpath, thumbnails=False)
    def sample_blog_likes(self, amount):
        raise NotImplemented, 'FIXME'
    def get_post_photos(self, post_id, thumbs=False):
        raise NotImplemented, 'FIXME'
        return self.posts.get_post_photos(post_id, thumbs=thumbs)
    def get_post_photos_and_paths(self, post_id, thumbs=False):
        raise NotImplemented, 'FIXME'
        photos = self.get_post_photos(post_id, thumbs=thumbs)
        repos = self.posts.photos.repos
        for photo in photos:
            basename = os.path.basename(photo.url)
            photo.filename = repos.filename(basename)
        return photos
    def _photoquery(self, post_id, thumbnails=False):
        raise NotImplemented, 'FIXME'
        urlmodel = TumblrPhotoUrl
        postmodel = TumblrPostPhoto
        if thumbnails:
            urlmodel = TumblrThumbnailUrl
            postmodel = TumblrPostThumbnail
        q = self.session.query(urlmodel).join(postmodel)
        return q.filter(postmodel.post_id == post_id)
    def sample_blog_likes(self, amount):
        raise NotImplemented, 'FIXME'
        blogs = self._query().all()
        random.shuffle(blogs)
        for b in blogs:
            print "sampling %d likes from %s" % (amount, b.name)
            self.posts.get_blog_likes(b.name, amount)





        
dropit = "DROP TABLE bumblr_blog_properties  ; DROP TABLE bumblr_blog_info ; DROP TABLE bumblr_blog_posts  ; DROP TABLE bumblr_liked_posts  ; DROP TABLE bumblr_blogs ;"
