import os
from datetime import datetime

import transaction
import requests
from sqlalchemy import not_
from sqlalchemy import exists
from sqlalchemy import func

class BaseManager(object):
    def __init__(self, session, model):
        self.session = session
        self.model = model
        self.client = None
        self.client_info = None
        self.limit = 20

    def get_engine(self):
        conn = self.session.connection()
        return conn.engine
    
    def query(self):
        return self.session.query(self.model)
    
    def get(self, id):
        return self.session.query(self.model).get(id)

    def _range_filter(self, query, field, start, end):
        dbfield = getattr(self.model, field)
        query = query.filter(dbfield >= start)
        return query.filter(dbfield <= end)

    def get_all_ids_query(self):
        return self.session.query(self.model.id).order_by(self.model.id)
    
    def get_all_ids(self, offset=None, limit=None):
        q = self.get_all_ids_query()
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def set_client(self, client):
        self.client = client
        if self.client_info is None:
            self.client_info = self.client.info()
    
    
