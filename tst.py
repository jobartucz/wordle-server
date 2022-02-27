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

mongodb = MongoClient(MONGODB_URI)
# redisdb = redis.from_url(REDIS_URL, decode_responses=True)
redisdb = redis.StrictRedis(
    host='127.0.0.1', port=6379, db=0, decode_responses=True)
redisdb.flushall()

print("-- 1 --")

# cut here

wordledb = mongodb['wordle']
info_col = wordledb['info']
words_col = wordledb['words']
wordict_col = wordledb['wordict']

allowedanswers = set(words_col.find_one()['answers'])
allowedguesses = set(words_col.find_one()['guesses'])


# redis db will include a key / val for each wordid to word
for w in wordict_col.find():
    # print(w['wordid'])
    redisdb.set(w['wordid'], w['word'])

# redis db will have a set of all user ids
# redis db will have a hash of userids to nicknames
# redis db will have a set for userid:words of all words for that userid
# redis db will have a hash of userid:wordid to number of guesses and 0/1 whether it's found


print("--- setting up redisdb ---")
for u in info_col.find():

    # print(">>" + u['userid'])
    if redisdb.exists(u['userid']):
        print("* * * * * ERROR!")
    redisdb.sadd('alluserids', u['userid'])
    redisdb.sadd(u['nickname'], u['userid'])  # add this userid to the set associated with this nickname
    redisdb.hset(u['userid'], 'nickname', u['nickname'])  # set this nickname in the user's hash
    for wid in u['words'].keys():
        redisdb.sadd(u['userid']+':words', wid)  # add this wordid to the set of this user's wordids
        redisdb.hset(u['userid']+':'+wid, 'guesses', u['words'][wid]['guesses'])  # add the number of guesses
        if u['words'][wid]['found']:
            redisdb.hset(u['userid']+':'+wid, 'found', 1)
        else:
            redisdb.hset(u['userid']+':'+wid, 'found', 0)


print(redisdb.smembers('alluserids'))  # the set of all userids
userid = redisdb.spop('alluserids')  # get a random userid
print(redisdb.hgetall(userid))  # get everything from the userid hash (just nickname now)

print(redisdb.smembers(userid + ":words"))  # get the set of wordids associated with this userid
wid = redisdb.spop(userid + ":words")  # get a random wordid
print(redisdb.hgetall(userid+":"+wid))  # get the hash (num guesses and whether found)  for this userid/wordid
print(f"getting word for {wid}")
print(redisdb.get(wid))  # get the word for this wordid

# end cut here


# print(type(redisdb.hgetall(info[0]['userid'])))
