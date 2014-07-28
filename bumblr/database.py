from sqlalchemy import Sequence, Column, ForeignKey

# column types
from sqlalchemy import Integer, String, Unicode, UnicodeText
from sqlalchemy import BigInteger
from sqlalchemy import Boolean, Date, LargeBinary
from sqlalchemy import PickleType
from sqlalchemy import Enum
from sqlalchemy import DateTime

from sqlalchemy.orm import relationship, backref

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

####################################
## Data Types                     ##
####################################

_overthis = [
    'overten',
    'overtwenty',
    'overthirty',
    'overforty',
    'overfifty',
    'oversixty',
    'overseventy',
    'overeighty',
    'overninety',
    'overonehundred']


DEFAULT_BLOG_PROPERTIES = ['source',
                           'followed',
                           'follower',
                           'liked_by_followed',
                           'liked_by_follower',
                           'favorite',
                           'ignored',
                           'fulltrack']
DEFAULT_BLOG_PROPERTIES += _overthis
OVERTHIS_MAP = dict([(10*i,n) for i,n in enumerate(_overthis, 1)])
del _overthis


####################################
## Tables                         ##
####################################

class ExampleTable(Base):
    __tablename__ = 'example_table'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(200), unique=True)

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer,
                primary_key=True)
    http_info = Column(PickleType)
    content = Column(LargeBinary)
    link = Column(String)

    def __init__(self):
        self.id = None
        self.http_info = None
        self.content = None
        self.link = None
        
    def __repr__(self):
        return "<File:  id: %d>" % self.id

class BlogProperty(Base):
    __tablename__ = 'blog_properties'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(200))
    
    
class TumblrBlog(Base):
    __tablename__ = 'tumblr_blogs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(200), unique=True)
    title = Column(Unicode(500))
    url = Column(Unicode(500))
    description = Column(UnicodeText)
    posts = Column(BigInteger)
    likes = Column(BigInteger)
    followed = Column(Boolean)
    share_likes = Column(Boolean)
    updated_remote = Column(DateTime)
    updated_local = Column(DateTime)
    
    ask = Column(Boolean)
    ask_page_title = Column(Unicode(500))
    ask_anon = Column(Boolean)
    can_send_fan_mail = Column(Boolean)
    is_nsfw = Column(Boolean)
    facebook = Column(Unicode)
    facebook_opengraph_enabled = Column(Unicode)
    twitter_enabled = Column(Boolean)
    tweet = Column(Unicode)
    twitter_send = Column(Boolean)
    
class TumblrBlogProperty(Base):
    __tablename__ = 'tumblr_blog_properties'
    blog_id = Column(BigInteger, ForeignKey('tumblr_blogs.id'),
                     primary_key=True)
    property_id = Column(BigInteger, ForeignKey('blog_properties.id'),
                          primary_key=True)

    
class TumblrPhotoUrl(Base):
    __tablename__ = 'tumblr_photo_urls'
    id = Column(Integer, primary_key=True)
    url = Column(Unicode(500), unique=True)
    status = Column(Integer)

class TumblrThumbnailUrl(Base):
    __tablename__ = 'tumblr_thumbnail_photo_urls'
    id = Column(Integer, primary_key=True)
    url = Column(Unicode(500), unique=True)
    status = Column(Integer)
    
class TumblrPost(Base):
    __tablename__ = 'tumblr_posts'
    id = Column(BigInteger, primary_key=True)
    blog_name = Column(Unicode(200), index=True)
    post_url = Column(Unicode(500))
    type = Column(Unicode(50))
    timestamp = Column(Integer)
    date = Column(Unicode(50))
    format = Column(Unicode(50))
    
    source_url = Column(Unicode(500))
    source_title = Column(Unicode(500))
    liked = Column(Boolean)
    content = Column(PickleType)

class TumblrBlogPost(Base):
    __tablename__ = 'tumblr_blog_posts'
    blog_id = Column(BigInteger, ForeignKey('tumblr_blogs.id'),
                     primary_key=True)
    post_id = Column(BigInteger, ForeignKey('tumblr_posts.id'),
                     primary_key=True)

class TumblrLikedPost(Base):
    __tablename__ = 'tumblr_liked_posts'
    blog_id = Column(BigInteger, ForeignKey('tumblr_blogs.id'),
                     primary_key=True)
    post_id = Column(BigInteger, ForeignKey('tumblr_posts.id'),
                     primary_key=True)

class TumblrMyLikedPost(Base):
    __tablename__ = 'tumblr_my_liked_posts'
    post_id = Column(BigInteger, ForeignKey('tumblr_posts.id'),
                     primary_key=True)

    
class TumblrPostPhoto(Base):
    __tablename__ = 'tumblr_post_photos'
    post_id = Column(BigInteger, ForeignKey('tumblr_posts.id'),
                     primary_key=True)
    photo_id = Column(BigInteger, ForeignKey('tumblr_photo_urls.id'),
                          primary_key=True)
    
    
class TumblrPostThumbnail(Base):
    __tablename__ = 'tumblr_post_thumbnails'
    post_id = Column(BigInteger, ForeignKey('tumblr_posts.id'),
                     primary_key=True)
    thumb_id = Column(BigInteger, ForeignKey('tumblr_thumbnail_photo_urls.id'),
                          primary_key=True)
    
    
#######################################################
# relationships
#######################################################
