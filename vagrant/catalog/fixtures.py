from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///itemcatalogwithusers.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

User1 = User(name="Udacity FWD Nanodegree", email="fullstack.nanodegree@gmail.com",
             picture='https://lh3.googleusercontent.com/-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg')
session.add(User1)
session.commit()

category1 = Category(user_id=1, name="Snowboarding")

session.add(category1)
session.commit()

item1 = Item(user_id=1, name="Snowboard", description="Best for any terrain conditions.",
                     price="$399.99", category=category1)

session.add(item1)
session.commit()

print "Some items added!"