from flask import Flask, request

from models import db, Card

app = Flask(__name__)
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


@app.route('/card', methods=["POST", "GET", "DELETE", "PUT"])
def hello_world():
    if request.method == "GET":
        cards = Card.objects.to_json()
        return cards


@app.route('/')
def index():
    return "Hey cutie"



if __name__ == '__main__':
    app.run()
