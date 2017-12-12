from bson import ObjectId
from flask import Flask, request, jsonify
from flask import json
from mongoengine import FieldDoesNotExist
from werkzeug.exceptions import InternalServerError, BadRequest

from models import db, Card, Collection, User
import requests
import re
import jwt
import uuid
app = Flask(__name__)
POST = "POST"
GET = "GET"
DELETE = "DELETE"
PUT = "PUT"
#
# app.config["MONGODB_SETTINGS"] = {"MONGODB_DB": "Portal",
#                                   "MONGODB_HOST": "mongodb://admin_odko:WinniePooh@portalinternational-shard-00-00-3b6lw.mongodb.net:27017,"
#                                                   "portalinternational-shard-00-01-3b6lw.mongodb.net:27017,"
#                                                   "portalinternational-shard-00-02-3b6lw.mongodb.net:27017/test?ssl=true&replicaSet=PortalInternational"
#                                                   "-shard-0&authSource=admin",
#                                   "MONGODB_USERNAME": "admin_odko",
#                                   "MONGODB_PASSWORD": "WinniePooh"
#                                   }

app.config["MONGODB_DB"] = "RemineMe"
app.config[
    "MONGODB_HOST"] = "mongodb://admin_remine:WinniePooh8@remineme-shard-00-00-h4vdb.mongodb.net:27017,remineme-shard-00-01-h4vdb.mongodb.net:27017,remineme-shard-00-02-h4vdb.mongodb.net:27017/RemineMe?ssl=true&replicaSet=RemineMe-shard-0&authSource=admin"
app.config["MONGODB_USERNAME"] = "admin_remine"
app.config["MONGODB_PASSWORD"] = "WinniePooh8"

db.init_app(app)


def add_card(cards):
    cards_id = []
    for item in cards:
        card = Card(**item).save()
        cards_id.append(card.pk)
    return cards_id


@app.route('/card', methods=[POST, GET, DELETE, PUT])
def card():
    if request.method == GET:
        cards = Card.objects.to_json()
        return cards
    elif request.method == POST:
        json = request.json
        cards_id = add_card(json)
        return jsonify(cards_id)


@app.route('/collection', methods=[POST, GET, DELETE, PUT])
def collection():
    if request.method == GET:

        search_keyword = request.args.get("search_text", None)
        user_id = request.args.get("user_id", None)
        remote_id = request.args.get("remote_id", None)
        response = []
        if search_keyword != None and user_id != None:
            collections = Collection.objects(user_id__ne=user_id).search_text(search_keyword)
            # print(collection.to_json())
            for collection in collections:
                tmp = json.loads(collection.to_json())
                tmp["_id"] = tmp["_id"]["$oid"]
                tmp["cards"] = len(collection.cards)
                collection.cards = None

                user = User.objects(id=ObjectId(collection.user_id)).only("name").exclude("favorites").first()
                user = json.loads(user.to_json())
                user["_id"] = user["_id"]["$oid"]
                tmp["user"] = user
                response.append(tmp)
            return jsonify({"collections": response})

        elif remote_id != None:
            collection = Collection.objects(id=ObjectId(remote_id)).first()
            cards = collection.cards
            return jsonify({"cards": cards})
        else:
            raise jsonify({"error": "Bad keyword!"})

    elif request.method == POST:
        data = request.json
        user_id = data["user_id"]
        items = data["collections"]
        response = []
        for item in items:
            collection = item["collection"]
            cards = item["cards"]

            card_ids = [int(card.pop("id")) for card in cards]
            card_remote_ids = add_card(cards)
            card_list = dict(zip(card_ids, [str(_id) for _id in card_remote_ids]))

            tmp = {"coll_id": collection.pop("id")}

            collection = Collection(**collection)
            collection.cards = card_remote_ids
            collection.user_id = user_id
            collection = collection.save()

            # updated = User.objects(id=user_id).update_one(push__collections=collection.pk)

            tmp["remote_id"] = str(collection.pk)
            tmp["cards"] = card_list
            response.append(tmp)
        # cards = data['cards']
        # collection.cards = card_ids
        # collection.save()

        # user_id = data["user_id"]
        # updated = User.objects(id=ObjectId(user_id)).update_one(push__collections=collection.pk)
        # return jsonify({"collection_id": str(collection.pk), "update": updated})
        return jsonify(response)


def is_valid_email(email):
    if len(email) > 7:
        if re.match("^.+@([?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$)", email) != None:
            return True
    return False

    # if isValidEmail("my.email@gmail.com") == True:
    #     print
    #     "This is a valid email address"
    # else:
    #     print
    #     "This is not a valid email address"


@app.route('/user', methods=[POST, GET])
def user():
    if request.method == POST:
        encoded_jwt = request.json["data"]
        user_json = jwt.decode(encoded_jwt, 'ISHERLOCKED', algorithms=['HS256'])

        if len(User.objects(email=user_json["email"])) == 0:
            user_json["access_token"] = jwt.encode({'access_token': str(uuid.uuid4())}, 'ISHERLOCKED', algorithm='HS256').decode("utf-8")
            user = User(**user_json)
            user.save()
            return jsonify({"user_id": str(user.pk), "success": "Successfully", "access_token": user_json["access_token"]})
        else:
            return jsonify({"error": "User is already registered"})
    elif request.method == "GET":
        user_or_name = request.args.get("email")
        # password = request.args.get("password")
        if is_valid_email(user_or_name):
            user = User.objects(email=user_or_name).first()
            if user == None:
                return jsonify({"error": "User not found, check your information"})
            else:
                return jsonify({"success": "Successfully, logged", "user_id": str(user.pk), "user": user.to_json()})
        else:
            return jsonify({"error": "User not found, check your information"})


def send_request(URL, method, json):
    result = {}
    if method == GET:
        result = requests.get(URL, json=json).json()
    elif method == POST:
        result = requests.post(URL, json=json).json()
    elif method == PUT:
        result = requests.put(URL, json=json).json()
    elif method == DELETE:
        result = requests.delete(URL, json=json).json()
    return result


def str2objectid(id_list):
    for i, item in enumerate(id_list):
        id_list[i] = ObjectId(item)
    return id_list


@app.errorhandler(InternalServerError)
def global_handler_500(e):
    return jsonify({"error": 500, "message": str(e)}), 500


@app.errorhandler(FieldDoesNotExist)
def global_handler_file_doesnt_exist(e):
    return jsonify({"error": 400, "message": str(e)}), 400


@app.errorhandler(BadRequest)
def global_handler_bad_request(e):
    return jsonify({"error": 401, "message": str(e)}), 401


@app.errorhandler(Exception)
def global_handler_exception(e):
    return jsonify({"error": "error", "message": str(e)}), 500


@app.route('/')
def index():
    return "Hey cutie"


if __name__ == '__main__':
    app.run()
