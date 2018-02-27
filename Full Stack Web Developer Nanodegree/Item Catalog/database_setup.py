#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    create_time = Column(DateTime, default=datetime.datetime.now)
    user_group = Column(Integer)  # TODO: user group


class Catalog(Base):
    __tablename__ = 'catalog_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    description = Column(String(2000))
    slug = Column(String(250), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    create_time = Column(DateTime, default=datetime.datetime.now)
    lvl = Column(Integer)
    lft = Column(Integer)
    rgt = Column(Integer)

    parent_id = Column(Integer, ForeignKey('catalog_item.id'))
    parent = relationship('Catalog', remote_side=[id])
    children = relationship("Catalog")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'parent_id': self.parent_id,
            'slug': self.slug,
            'level': self.lvl
        }


class BannedUser(Base):
    """
    TODO: User management
    """
    __tablename__ = 'banned_user'

    banned_id = Column(Integer, primary_key=True)
    banned_by = Column(Integer)
    create_time = Column(DateTime, default=datetime.datetime.now)
    reason = Column(String(250))

# # TODO: Access Log
# class AccessLog(Base):
#     __tablename__ = 'access_log'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     path = Column(String(2048))
#     visit_time = Column(DateTime, default=datetime.datetime.now)
#     visitor_ip = Column(String(16))
#     method = Column(String(32))
#     status = Column(String(200))
#     user_id = Column(Integer, ForeignKey('user.id'))
#     user = relationship(User)


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
