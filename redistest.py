import os
from random import choice
from re import S
from uuid import uuid4
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from html import escape
import redis  # for cacheing pymongo
from bson.json_util import dumps
import json

app = Flask(__name__)

MONGODB_URI = 'mongodb+srv://mrbartucz:MONGODB7gud3U!@cluster0.wyhau.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'
REDIS_URL = 'redis://:pc55ed34c62b32d1a44e0c21db60423039d4ce6d2882f9cd31286b50e7b83dd48@ec2-54-225-230-219.compute-1.amazonaws.com:12449'


# print()

# Load config from a .env file:
load_dotenv()

client = MongoClient(MONGODB_URI)
redisdb = redis.from_url(REDIS_URL, decode_responses=True)

# cut here

wordledb = client['wordle']
info = wordledb['info']
words = wordledb['words']
wordict = words.find_one()['wordict']

allowedanswers = set(words.find_one()['answers'])
allowedguesses = set(words.find_one()['guesses'])

# set up the wordict in redis
serializedObj = dumps(wordict)  # serialize object for the set redis.
# set serialized object to redis server.
result = redisdb.set('wordict', serializedObj)

# set up the user info in redis
userList = info.find()  # collection name in 'DummyDb' database
serializedObj = dumps(userList)  # serialize object for the set redis.
# set serialized object to redis server.
result = redisdb.set('info', serializedObj)

info = json.loads(redisdb.get('info'))
wordict = json.loads(redisdb.get('wordict'))

for u in info:
    print(u['userid'])
