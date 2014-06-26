from sqlalchemy import Sequence, Column, ForeignKey

# column types
from sqlalchemy import Integer, String, Unicode
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


FileType = Enum('agenda', 'minutes', 'attachment',
                name='file_type_enum')

AgendaItemType = Enum('presentation', 'policy', 'routine', 'unknown',
                      name='agenda_item_type_enum')

VoteType = Enum('Yea', 'Nay', 'Abstain', 'Absent', 'Present',
                name='vote_type_enum')

AgendaItemTypeMap = dict(V='presentation', VI='policy',
                         VII='routine')

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
    
    

class TumblrPhotoUrl(Base):
    __tablename__ = 'tumblr_photo_urls'
    id = Column(Integer, primary_key=True)
    url = Column(Unicode(500), unique=True)


class TumblrPost(Base):
    __tablename__ = 'tumblr_posts'
    id = Column(Integer, primary_key=True)
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
    
    
#######################################################
# relationships
#######################################################
