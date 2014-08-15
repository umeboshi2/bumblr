import os

import transaction
import requests

from bumblr.database import TumblrPost, TumblrPostPhoto, TumblrPostThumbnail
from bumblr.database import TumblrLikedPost, TumblrMyLikedPost
from bumblr.database import TumblrBlogPost
from bumblr.database import TumblrPhotoUrl, TumblrThumbnailUrl

from bumblr.photomanager import TumblrPhotoManager


POSTKEYS = ['id', 'blog_name', 'post_url', 'type', 'timestamp',
            'date', 'format', 'liked']

def get_post_photo_urls(photos):
    photolist = list()
    for pdata in photos:
        url = pdata['original_size']['url']
        photolist.append(url)
    if not photolist:
        raise RuntimeError, "Something wrong with photos"
    return photolist

def get_post_photo_thumbnail_urls(photos):
    photolist = list()
    for pdata in photos:
        thumb = None
        for psize in pdata['alt_sizes']:
            if psize['width'] == 100:
                thumb = psize['url']
                break
        photolist.append(thumb)
    if not photolist:
        raise RuntimeError, "Something wrong with photos"
    return photolist
    
class TumblrPostManager(object):
    def __init__(self, session):
        self.session = session
        self.client = None
        self.client_info = None
        self.limit = 20
        self.model = TumblrPost
        self.photos = TumblrPhotoManager(self.session)
        
    def set_client(self, client):
        self.client = client
        self.client_info = self.client.info()

    def _query(self):
        return self.session.query(TumblrPost)

    def query(self):
        return self.session.query(TumblrPost)
    
    def blogname_query(self, name):
        return self._query().filter_by(blog_name=name)
    
    def get(self, id):
        return self.session.query(TumblrPost).get(id)

    def get_all_ids_query(self, with_blog_names=False, blog=None):
        qf = self.session.query
        if with_blog_names:
            q = qf(TumblrPost.id, TumblrPost.blog_name)
        else:
            q = qf(TumblrPost.id)
        q = q.order_by(TumblrPost.id)
        return q

    def get_all_ids(self, with_blog_names=False, blog=None):
        q = self.get_all_ids_query(with_blog_names=with_blog_names,
                                   blog=blog)
        return q.all()

    def get_post_photos_query(self, post_id, thumbs=False):
        urlclass = TumblrPhotoUrl
        if thumbs:
            urlclass = TumblrThumbnailUrl
        stmt = self.session.query(TumblrPostPhoto.photo_id)
        stmt = stmt.filter_by(post_id=post_id)
        post_photos = stmt.subquery('post_photos')
        q = self.session.query(urlclass)
        return q.filter(urlclass.id.in_(post_photos))

    def get_post_photos(self, post_id, thumbs=False):
        return self.get_post_photos_query(post_id, thumbs=thumbs).all()
    
    def add_post(self, post):
        if self.get(post['id']) is not None:
            msg = "Post %d for %s already in database."
            print msg  % (post['id'], post['blog_name'])
            return
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
        p = self.session.merge(p)
        self.update_photos(p.id, post=p)
        self.update_thumbnails(p.id, post=p)
        

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
                    blogpost_query = self.session.query(TumblrBlogPost)
                    blogpost = blogpost_query.get((blog_id, post['id']))
                    if blogpost is not None:
                        ignored_post_count += 1
                        #msg = "Ignoring this post %d %d" 
                        #print msg % (blog_id, post['id'])
                if batch_length == ignored_post_count:
                    print "We think we have it..... %d %d" % (len(these_posts), ignored_post_count)
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

    def update_photos(self, post_id, post=None):
        if post is None:
            post = self.get(post_id)
        if post is None:
            return
        if post.type != 'photo':
            return
        photos = get_post_photo_urls(post.content['photos'])
        for url in photos:
            if not self.photos.url_exists(url):
                print "Adding %s to photo urls." % url
                p = self.photos.add_url(url)
            else:
                p = self.photos.get_by_url(url)
            rel = self.session.query(TumblrPostPhoto).get((post.id, p.id))
            if rel is None:
                with transaction.manager:
                    tpp = TumblrPostPhoto()
                    tpp.post_id = post.id
                    tpp.photo_id = p.id
                    self.session.add(tpp)
                print "Added relation", post.id, p.id
            self.photos.update_photo(p.id)
            
                
            
    def update_thumbnails(self, post_id, post=None):
        if post is None:
            post = self.get(post_id)
        if post is None:
            return
        if post.type != 'photo':
            return
        photos = get_post_photo_thumbnail_urls(post.content['photos'])
        for url in photos:
            if url is None:
                continue
            if not self.photos.thumbnail_url_exists(url):
                print "Adding %s to thumbnail urls." % url
                p = self.photos.add_thumbnail_url(url)
            else:
                p = self.photos.get_thumbnail_by_url(url)
            if p is None:
                raise RuntimeError, "Wawsup?"
            rel = self.session.query(TumblrPostThumbnail).get((post.id, p.id))
            if rel is None:
                with transaction.manager:
                    tpp = TumblrPostThumbnail()
                    tpp.post_id = post.id
                    tpp.thumb_id = p.id
                    self.session.add(tpp)
                print "Added relation", post.id, p.id
            self.photos.update_thumbnail(p.id)
            
        
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
        if blog_name is None:
            return self.client.likes(offset=offset, limit=limit)
        else:
            return self.client.blog_likes(blog_name,
                                          offset=offset, limit=limit)
        
    def _set_liked_post(self, post_id, blog_id=None):
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
        return self._get_likes(total_desired=total_desired)

    def _get_blog_likes(self, blogname, total_desired=None):
        return self._get_likes(blog_name=blogname,
                                  total_desired=total_desired)
        
    def get_blog_likes(self, blogname, total_desired=None):
        return self._get_blog_likes(blogname, total_desired=total_desired)
    
                
    
    def update_posts(self, blogname):
        if self.client is None:
            raise RuntimeError, "Need to set client"
    
