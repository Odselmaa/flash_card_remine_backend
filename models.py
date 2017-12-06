import datetime

from bson import ObjectId
from flask_mongoengine import MongoEngine
from mongoengine import *

db = MongoEngine()


class Card(Document):
    # _id = StringField(primary_key=True)
    translation = StringField(required=True)
    original = StringField(required=True)

class Collection(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    cards = ListField(ReferenceField(Card))
    cover = StringField()


class User(Document):
    name = StringField(required=True)
    password = StringField()
    email = EmailField(required=True)
    favorites = ListField(ReferenceField(Collection))
    collections = ListField(ReferenceField(Collection))


