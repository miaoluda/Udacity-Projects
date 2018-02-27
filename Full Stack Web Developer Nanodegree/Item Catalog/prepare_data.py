#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Catalog, BannedUser, AccessLog

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Need a real ROOT node
Catalogitem1 = Catalog(user_id=1, name="ROOT"  , id=1 , lvl=0
                    , description="Real Root( does not display)", slug="/")            
session.add(Catalogitem1)
session.commit()


Catalogitem1 = Catalog(user_id=1, name="Fruit", lvl=1
                   , parent_id=session.query(Catalog).filter_by(name="ROOT").one().id
                    , description="To eat", slug="fruit")            
session.add(Catalogitem1)
session.commit()

fruit_id = session.query(Catalog).filter_by(name="Fruit").one().id
print("fruit_id: ",fruit_id)

Catalogitem1 = Catalog(user_id=1, name="Meat" , lvl=1
                    , parent_id=session.query(Catalog).filter_by(name="ROOT").one().id
                    , description="Just a Catalog", slug="meat")            
session.add(Catalogitem1)
session.commit()

Catalogitem2 = Catalog(user_id=1, name="Red" , lvl=2
                    , description="Red fruit", slug="red"
                    , parent_id=fruit_id)                    

session.add(Catalogitem2)
session.commit()

Catalogitem2 = Catalog(user_id=1, name="Yellow" , lvl=2
                    , description="Yellow fruit", slug="yellow"
                    , parent_id=fruit_id)                    

session.add(Catalogitem2)
session.commit()

Catalogitem2 = Catalog(user_id=1, name="Blue" , lvl=2
                    , description="Blue fruit", slug="blue"
                    , parent_id=fruit_id)                    

session.add(Catalogitem2)
session.commit()

red_id = session.query(Catalog).filter_by(name="Red").one().id
print("red_id:", red_id)

Catalogitem3 = Catalog(user_id=1, name="Apple" , lvl=3
                    , description="An Apple A Day~", slug="apple"
                    , parent_id=red_id)                    

session.add(Catalogitem3)
session.commit()

Catalogitem3 = Catalog(user_id=1, name="Cherry" , lvl=3
                    , description="I like Cherry Coke!", slug="cherry"
                    , parent_id=red_id)                    

session.add(Catalogitem3)
session.commit()

Catalogitem4 = Catalog(user_id=1, name="Banana" , lvl=3
                    , description="Want a Banana?", slug="banana"
                    , parent_id=session.query(Catalog).filter_by(name="Yellow").one().id)                    
session.add(Catalogitem4)
session.commit()

Catalogitem4 = Catalog(user_id=1, name="Pineapple" , lvl=3
                    , description="Hawaiian!", slug="pineapple"
                    , parent_id=session.query(Catalog).filter_by(name="Yellow").one().id)                    
session.add(Catalogitem4)
session.commit()

Catalogitem4 = Catalog(user_id=1, name="Yellow Peach" , lvl=3
                    , description="Must be yellow to be yellow peach.", slug="yellow-peach"
                    , parent_id=session.query(Catalog).filter_by(name="Yellow").one().id)                    
session.add(Catalogitem4)
session.commit()

Catalogitem4 = Catalog(user_id=1, name="Blueberry" , lvl=3
                    , description="Now model of Cellphone", slug="blueberry"
                    , parent_id=session.query(Catalog).filter_by(name="Blue").one().id)                    
session.add(Catalogitem4)
session.commit()