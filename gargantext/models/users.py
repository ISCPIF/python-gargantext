from django.contrib.auth import models
from gargantext.util.db import *

from datetime import datetime

__all__ = ['User', 'Contact']

class User(Base):
    # The properties below are a reflection of Django's auth module's models.
    __tablename__ = models.User._meta.db_table
    id           = Column(Integer, primary_key=True)
    password     = Column(String(128))
    is_superuser = Column(Boolean(), default=False)
    is_staff     = Column(Boolean(), default=False)
    username     = Column(String(30))
    first_name   = Column(String(30), default="")
    last_name    = Column(String(30), default="")
    email        = Column(String(75))
    is_active    = Column(Boolean(), default=True)
    last_login   = Column(DateTime(timezone=False))
    date_joined  = Column(DateTime(timezone=False), default=datetime.now)

    def contacts(self):
        """get all contacts in relation with the user"""
        Friend = aliased(User)
        query = (session
            .query(Friend)
            .join(Contact, Contact.user2_id == Friend.id)
            .filter(Contact.user1_id == self.id)
        )
        return query.all()

    def nodes(self, typename=None, order=None):
        """get all nodes belonging to the user"""
        from .nodes import Node
        query = (session
            .query(Node)
            .filter(Node.user_id == self.id)
        )
        if typename is not None:
            query = query.filter(Node.typename == typename)

        if order is not None:
            query = query.order_by(Node.name)

        return query

    def contacts_nodes(self, typename=None):
        from .nodes import Node
        for contact in self.contacts():
            contact_nodes = (session
                .query(Node)
                .filter(Node.user_id == contact.id)
                .filter(Node.typename == typename)
                .order_by(Node.date)
            ).all()
            yield contact, contact_nodes

    def owns(self, node):
        """check if a given node is owned by the user"""
        return (node.user_id == self.id) or \
                node.id in (contact.id for contact in self.contacts())
    
    def get_params(self, username=None):
        print(self.__dict__.items())
        return self.hyperdata

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user1_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    user2_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    is_blocked = Column(Boolean(), default=False)
    date_creation = Column(DateTime(timezone=False))

    __table_args__ = (UniqueConstraint('user1_id', 'user2_id'), )
