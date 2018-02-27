#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
 Some Utility Functions.
"""

from flask import redirect, url_for
from database_setup import Base, Catalog, BannedUser, User  # , AccessLog
import re


def get_node_to_root(node):
    """
    input a node in catalog,
    return id --> root path in a list[(id, name, slug)].
    """
    item = node
    rst = [(node.id, node.name, node.slug)]
    while item.parent.id > 1:
        rst.append((item.parent_id, item.parent.name, item.parent.slug))
        item = item.parent
    return list(reversed(rst))


def subtree(item, catalog, max_depth=10):
    """ get subtree of catalog, from node item.
        input:
            item: root node of the subtree
            catalog: whole tree
            max_depth: max level of search
        output:
            sub tree in a list
    """
    rst = []
    rst.append(item)
    to_crawl = [item]
    current_level = 0

    if item.children:
        while to_crawl and current_level < max_depth:
            c = to_crawl.pop()
            for i in c.children:
                rst.append(i)
                to_crawl.append(i)
            current_level = current_level + 1

    return rst


def create_user(login_session, session):
    user = session.query(User).filter_by(email=login_session['email']).first()
    if user:
        print(u"Existing User %s Logged in" % user.name)
        print(login_session)
    else:
        User1 = User(name=login_session['username'],
                     email=login_session['email'],
                     picture=login_session['picture'])
        session.add(User1)
        session.commit()


def valid_item(item, session, catalog):
    """
    new item:
    0 add item and flush (get id)
    1 slug is unique
    2 parent is valid (cannot be itself)

    edit item:
    1 slug is unique
    2 parent is valid (cannot be it self, or its own children)
    """
    rst = True

    existing_parent, existing_slug = {}, {}
    if item.id == item.parent_id:
        return False  # Circular dependency
    for i in catalog:
        existing_parent[i.id] = i.parent_id
        existing_slug[i.id] = i.slug

    if item.id:  # edit item:
        if item.slug != existing_slug[item.id]:
            # if slug changed
            if item.slug in existing_slug.values():
                return False  # "slug must be unique"

        if item.parent_id != existing_parent[item.id]:
            # if item moved
            all_children = subtree(item, catalog)
            for i in all_children:
                if item.parent_id == i.id:
                    return False  # "Parent cannot be children"
    else:
        # new item
        if item.slug in existing_slug.values():
            return False  # , "slug must be unique"
        if item.parent_id > max(existing_slug):
            return False  # ,  "non-existing parent"
    return rst


def slugify(text):
    """server side slugify"""
    text = re.sub(u"\s+", '-', text)
    text = re.sub(u'[\\\\/:,，"*?<>|~`!\'@#$%^&()_|+=—…（）‘’“”：、·！？]+', '', text)
    text = re.sub(u"\-\-+", '-', text)
    return text
