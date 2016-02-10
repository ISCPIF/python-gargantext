from django.contrib.auth import models
from gargantext.util.db import *


__all__ = ['User']


class User(Base):

    # Do not change!
    # The properties below are a reflection of Django's auth module's models.
    __tablename__ = 'auth_user'
    id = Column(Integer, primary_key=True)
    password = Column(String(128))
    last_login = DateTime(timezone=False)
    is_superuser = Column(Boolean(), default=False)
    username = Column(String(30))
    first_name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String(75))
    is_staff = Column(Boolean())
    is_active = Column(Boolean())
    date_joined = DateTime(timezone=False)

    def get_contacts(self):
        """get all contacts in relation with the user"""
        Friend = aliased(User)
        query = (session
            .query(Friend)
            .join(Contact, Contact.user2_id == Friend.id)
            .filter(Contact.user1_id == self.id)
        )
        return query.all()

    def get_nodes(self, nodetype=None):
        """get all nodes belonging to the user"""
        from .nodes import Node
        query = (session
            .query(Node)
            .filter(Node.user_id == self.id)
            .order_by(Node.date)
        )
        if nodetype is not None:
            query = query.filter(Node.type_id == nodetype.id)
        return query.all()

    def owns(user, node):
        """check if a given node is owned by the user"""
        return True


class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, primary_key=True)
    user2_id = Column(Integer, primary_key=True)
    is_blocked = Column(Boolean())
    date_creation = DateTime(timezone=False)

    __table_args__ = (UniqueConstraint('user1_id', 'user2_id'), )
