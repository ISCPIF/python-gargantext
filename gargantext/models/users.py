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

    def get_params(self, username=None):
        return self.__dict__.items()

    def nodes(self, typename=None, order=None):
        """get all nodes belonging to the user
           TODO : add NodeUser rights management
        """
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
    
    
    def invite(self, username=None, block=False, notification=True):
        if username is None:
            raise ValueError('if you contact someone give his username please.')
        
        if username is self.username:
            raise ValueError('Why self contact should be implemented ?')
        
        maybeFriend = session.query(User).filter(User.username == username).first()
        
        if maybeFriend is None:
            raise ValueError('username unknown in database.')


        relation = (session.query(Contact)
                           .filter( user1_id == self.id
                                  , user2_id == maybeFriend.id
                                  )
                           .first()
                   )
        
        if relation is not None:
            if relation.is_blocked != block:
                relation.is_blocked = block
                session.add(relation)
                session.commit()
                print('Link does exist already and updated')
            else:
                print('Link does exist already and not updated')

        else :
            relation = Contact()
            relation.user1_id = self.id
            relation.user2_id = maybeFriend.id
            relation.is_blocked = False
            session.add(relation)
            session.commit()
            print('Relation is created in one direction only')
            
            if notification is True:
                print('TODO Create notification')
            
            return relation

    def accept(self, username=None, notification=False):
        self.invite(username=username, block=False, notification=notification)

    def refuse(self, username=None, notification=False):
        self.invite(username=username, block=True, notification=notification)

    def contacts(self):
        """get all contacts in one-relation with the user"""
        Friend = aliased(User)
        query = (session
            .query(Friend)
            .join(Contact, Contact.user2_id == Friend.id)
            .filter(Contact.user1_id == self.id, Contact.is_blocked==False)
        )
        return query.all()


    def friends(self):
        """get all contacts in bidirectional-relation 
        (both parties accepted to be linked) with the user"""
        
        Friend = aliased(User)
        Contact1 = aliased(Contact)
        Contact2 = aliased(Contact)

        query = (session
            .query(Friend)
            .join(Contact1, Contact1.user2_id == Friend.id)
            .join(Contact2, Contact2.user1_id == Friend.id)
            .filter(Contact1.user1_id == self.id, Contact1.is_blocked == False)
            .filter(Contact2.user2_id == self.id, Contact2.is_blocked == False)
        )
        return query.all()


########################################################################


    def owns(self, node):
        """check if a given node is owned by the user"""
        return (node.user_id == self.id)
    
#    def owns(self, node):
#        """check if a given node is owned by the user"""
#        return (node.user_id == self.id) or \
#                node.id in (contact.id for contact in self.friends())


# Deprecated
#    def contacts_nodes(self, typename=None):
#        from .nodes import Node
#        for contact in self.contacts():
#            contact_nodes = (session
#                .query(Node)
#                .filter(Node.user_id == contact.id)
#                .filter(Node.typename == typename)
#                .order_by(Node.date)
#            ).all()
#            yield contact, contact_nodes



class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user1_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    user2_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    is_blocked = Column(Boolean(), default=False)
    date_creation = Column(DateTime(timezone=False))

    __table_args__ = (UniqueConstraint('user1_id', 'user2_id'), )



