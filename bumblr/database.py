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
    
    
class TumblrBlog(object):
    __tablename__ = 'tumblr_blogs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(200))
    title = Column(Unicode(500))
    url = Column(Unicode(500))
    description = Column(UnicodeText)
    updated_remote = Column(DateTime)
    updated_local = Column(DateTime)
    
    

class TumblrPhotoUrl(Base):
    __tablename__ = 'tumblr_photo_urls'
    id = Column(Integer, primary_key=True)
    url = Column(Unicode(500), unique=True)
    status = Column(Integer)

class TumblrPost(Base):
    __tablename__ = 'tumblr_posts'
    id = Column(BigInteger, primary_key=True)
    blog_name = Column(Unicode(200))
    post_url = Column(Unicode(500))
    type = Column(Unicode(50))
    timestamp = Column(Integer)
    date = Column(Unicode(50))
    format = Column(Unicode(50))
    
    source_url = Column(Unicode(500))
    source_title = Column(Unicode(500))
    liked = Column(Boolean)
    content = Column(PickleType)

class TumblrPostPhoto(Base):
    __tablename__ = 'tumblr_post_photos'
    post_id = Column(BigInteger, ForeignKey('tumblr_posts.id'),
                     primary_key=True)
    photo_id = Column(BigInteger, ForeignKey('tumblr_photo_urls.id'),
                          primary_key=True)
    
    
#######################################################
# relationships
#######################################################
