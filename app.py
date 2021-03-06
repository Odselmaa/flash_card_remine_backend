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


@app.route('/collection/trending', methods=[GET])
def collection_trending():
    if request.method == GET:
        limit = int(request.args.get("limit", None))
        user_id = request.args.get("user_id", None)
        if limit is not None:
            trending_collection = Collection.objects.order_by("-likes").limit(limit).exclude("cards")
            response = []
            for collection in trending_collection:
                tmp = json.loads(collection.to_json())
                tmp["_id"] = tmp["_id"]["$oid"]
                user = User.objects(id=ObjectId(collection.user_id)).only("name").exclude("favorites").first()
                user = json.loads(user.to_json())
                user["_id"] = user["_id"]["$oid"]
                tmp["user"] = user
                response.append(tmp)

            return jsonify({"response": response})
        else:
            return jsonify({"error": "Bad keyword!"})
 

@app.route('/collection', methods=[POST, GET, DELETE, PUT])
def collection():
    if request.method == GET:

        search_keyword = request.args.get("search_text", None)
        user_id = request.args.get("user_id", None)
        remote_id = request.args.get("remote_id", None)
        favorite = request.args.get("favorite", None)
        limit = request.args.get("limit", None)

        if search_keyword != None and user_id != None:
            response = []
            collections = Collection.objects(user_id__ne=user_id).search_text(search_keyword)
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



        # elif favorite != None and limit != None and user_id != None:
        #     collection_ids = User.objects(id=ObjectId)

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

            tmp["remote_id"] = str(collection.pk)
            tmp["cards"] = card_list
            response.append(tmp)
        return jsonify(response)

    elif request.method == PUT:
        data = request.json
        if "collections" in data:
            user_id = data["user_id"]
            items = data["collections"]
            response = []
            added_cards = {}
            for item in items:
                collection = item["collection"]
                cards = item["cards"]
                collection = Collection.objects(id=ObjectId(collection["remote_id"])).update(**collection)
                
                for card_item in cards:
                    if "remote_id" in card:
                        card = Card.objects(id=ObjectId(card["remote_id"])).update(**card)
                    else:
                        card = Card(**json)
                        added_cards[card["id"]] = str(card.pk)


            return jsonify({"test":"test"})

        elif "favorite" in data and "user_id" in data:
            favorites = data["favorite"]
            user_id = data["user_id"]
            user = User.objects(id=ObjectId(user_id)).first()

            for coll in user.favorites:
                if coll not in favorites:
                    Collection.objects(id=ObjectId(coll)).update_one(dec__likes=1)
                



            updated_collection = {}
            for favorite in favorites:
                if favorite not in user.favorites:
                    collection = Collection.objects(id=ObjectId(favorite)).first()
                    collection.likes += 1
                    collection.save() 
                    updated_collection[favorite] = collection.likes

            user.favorites = favorites
            user.save()
            return jsonify({"test":updated_collection})



def is_valid_email(email):
    if len(email) > 7:
        if re.match("^.+@([?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$)", email) != None:
            return True
    return False

def convert_collection(collections, trending=False, favorited=False):
    response = []
    for collection in collections:
        tmp = json.loads(collection.to_json())
        tmp["_id"] = tmp["_id"]["$oid"]
        tmp["cards"] = collection.cards
        tmp["favorited"] = trending
        tmp["trending"] = favorited
        response.append(tmp)
    return response



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
                collections = Collection.objects(user_id=str(user.id)).exclude("user_id")
                response = []

                for collection in collections:
                    tmp = json.loads(collection.to_json())
                    tmp["_id"] = tmp["_id"]["$oid"]
                    tmp["cards"] = collection.cards
                    tmp["favorited"] = False
                    response.append(tmp)

                # favorite_ids = user.favorites
                # for favorite_id in favorite_ids:
                #     collection = Collection.objects(id=ObjectId(favorite_id)).first()
                #     tmp = json.loads(collection.to_json())
                #     tmp["_id"] = tmp["_id"]["$oid"]
                #     tmp["cards"] = collection.cards

                #     tmp["favorited"] = True
                #     response.append(tmp)

                # trending_collection = Collection.objects.order_by("-likes").limit(10)
                # for collection in trending_collection:
                #     tmp = json.loads(collection.to_json())
                #     tmp["_id"] = tmp["_id"]["$oid"]
                #     tmp["favorited"] = False
                #     tmp["trending"] = True
                #     tmp["cards"] = collection.cards
                #     response.append(tmp)

                return jsonify({"success": "Successfully, logged", 
                                "user_id": str(user.pk), 
                                "user": user, 
                                "collection": response})
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
