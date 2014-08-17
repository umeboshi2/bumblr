from datetime import datetime

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

# http://stackoverflow.com/questions/4617291/how-do-i-get-a-raw-compiled-sql-query-from-a-sqlalchemy-expression
from sqlalchemy.sql import compiler
from psycopg2.extensions import adapt as sqlescape


def compile_query(query):
    dialect = query.session.bind.dialect
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    comp.compile()
    enc = dialect.encoding
    params = {}
    for k, v in comp.params.iteritems():
        if isinstance(v, unicode):
            v = v.encode(enc)
        params[k] = sqlescape(v)
    return (comp.string.encode(enc) % params).decode(enc)


# orig is original size
# thumb is width 100
# smallsquare is width 75, height 75
# alt is all other sizes for photo
PhotoType = Enum('orig', 'alt', 'thumb', 'smallsquare',
                 name='tumblr_photo_type_enum')

Base = declarative_base()


class SerialBase(object):
    def serialize(self):
        data = dict()
        table = self.__table__
        for column in table.columns:
            name = column.name
            try:
                pytype = column.type.python_type
            except NotImplementedError:
                print "NOTIMPLEMENTEDERROR", column, column.type
            value = getattr(self, name)
            if pytype is datetime:
                value = value.isoformat()
            data[name] = value
        return data
    

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



# properties
# source denotes blog with high source content
# followed denotes blog followed on client account
# follower denotes account following client account's blog
# liked_by_followed denotes blog followed by a 'followed'
# liked_by_follower denotes blog followed by a 'follower'
# favorite denotes a blog where posts are kept current
# ignored denotes a blog where posts are never gathered
# fulltrack denotes a blog where all posts are archived

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
class RowCount(Base, SerialBase):
    __table__ = 'rowcounts'
    table = Column(String, primary_key=True)
    total = Column(BigInteger)
    
class BlogProperty(Base, SerialBase):
    __tablename__ = 'blog_properties'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(200))
    
    
class Blog(Base, SerialBase):
    __tablename__ = 'bumblr_blogs'
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
    
class BlogProperty(Base, SerialBase):
    __tablename__ = 'bumblr_blog_properties'
    blog_id = Column(BigInteger, ForeignKey('bumblr_blogs.id'),
                     primary_key=True)
    property_id = Column(BigInteger, ForeignKey('blog_properties.id'),
                          primary_key=True)

class Photo(Base, SerialBase):
    __tablename__ = 'bumblr_photos'
    id = Column(Integer, primary_key=True)
    caption = Column(Unicode)
    exif = Column(PickleType)
    
class PhotoUrl(Base, SerialBase):
    __tablename__ = 'bumblr_photo_urls'
    photo_id = Column(Integer, ForeignKey('bumblr_photos.id'))
    phototype = Column(PhotoType, index=True)
    url = Column(Unicode(500), unique=True)
    width = Column(Integer)
    height = Column(Integer)
    md5sum = Column(String(32))
    request_status = Column(Integer)
    request_head = Column(PickleType)
    keep_local = Column(Boolean)
    filename = Column(String)
    
    
class Post(Base, SerialBase):
    __tablename__ = 'bumblr_posts'
    id = Column(BigInteger, primary_key=True)
    blog_name = Column(Unicode(200), index=True)
    post_url = Column(Unicode(500))
    type = Column(Unicode(50))
    timestamp = Column(Integer, index=True)
    date = Column(Unicode(50))
    source_url = Column(Unicode)
    source_title = Column(Unicode)
    liked = Column(Boolean, index=True)
    followed = Column(Boolean, index=True)
    content = Column(PickleType)

class BlogPost(Base, SerialBase):
    __tablename__ = 'bumblr_blog_posts'
    blog_id = Column(BigInteger, ForeignKey('bumblr_blogs.id'),
                     primary_key=True)
    post_id = Column(BigInteger, ForeignKey('bumblr_posts.id'),
                     primary_key=True)

class PostPhoto(Base, SerialBase):
    __tablename__ = 'bumblr_post_photos'
    post_id = Column(BigInteger, ForeignKey('bumblr_posts.id'),
                     primary_key=True)
    photo_id = Column(BigInteger, ForeignKey('bumblr_photos.id'),
                          primary_key=True)
    
class LikedPost(Base, SerialBase):
    __tablename__ = 'bumblr_liked_posts'
    blog_id = Column(BigInteger, ForeignKey('bumblr_blogs.id'),
                     primary_key=True)
    post_id = Column(BigInteger, ForeignKey('bumblr_posts.id'),
                     primary_key=True)

class TumblrMyLikedPost(Base, SerialBase):
    __tablename__ = 'bumblr_my_liked_posts'
    post_id = Column(BigInteger, ForeignKey('bumblr_posts.id'),
                     primary_key=True)

    

#######################################################
# relationships
#######################################################
