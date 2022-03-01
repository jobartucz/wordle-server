# app.py

# todo:
# delete solved words

import json
from bson.json_util import dumps
import os
from random import choice
from re import S
from uuid import uuid4
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask import render_template
from html import escape
import redis  # for cacheing pymongo
from bson.json_util import dumps
import json
import mongo_tasks
import threading
from queue import Queue


app = Flask(__name__)
# print()

thread_queue = Queue(maxsize=0)
thread = threading.Thread(target=mongo_tasks.worker_thread, args=(thread_queue,))
thread.daemon = True
thread.start()

# Load config from a .env file:
load_dotenv()

print("--- Loading MongoDB ---")
if 'MONGODB_URI' not in os.environ:
    print(f"os.environ: {os.environ} does not contain MONGODB_URI")
    os.abort()

MONGODB_URI = os.environ['MONGODB_URI']
mongodb = MongoClient(MONGODB_URI)


print("--- Loading RedisDB ---")
REDIS_URL = os.environ.get("REDIS_URL")
redisdbg = redis.from_url(REDIS_URL, decode_responses=True)
redisdbg.flushall()

# cut here

wordledb = mongodb['wordle']
print("--- loading info collection ---")
info_col = wordledb['info']
print("--- loading words collection ---")
words_col = wordledb['words']
print("--- loading wordict collection ---")
wordict_col = wordledb['wordict']

print("--- setting answer sets ---")
allowedanswers = set(words_col.find_one()['answers'])
allowedguesses = set(words_col.find_one()['guesses'])


def loadredis():

    global info_col, wordict_col

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)
    redisdb.flushall()

    print("--- loading wordict into redis ---")
    # redis db will include a key / val for each wordid to word
    for w in wordict_col.find():
        # print(w['wordid'])
        redisdb.set(w['wordid'], w['word'])

    # redis db will have a set of all user ids
    # redis db will have a hash of userids to nicknames
    # redis db will have a set for userid:words of all words for that userid
    # redis db will have a hash of userid:wordid to number of guesses and 0/1 whether it's found
    print("--- loading users into redisdb ---")
    for u in info_col.find():
        # print("  >> setting up userid: " + u['userid'])
        redisdb.sadd('alluserids', u['userid'])
        redisdb.sadd(u['nickname'], u['userid'])  # add this userid to the set associated with this nickname
        redisdb.hset(u['userid'], 'nickname', u['nickname'])
        # print("    >> adding words: ")
        for wid in u['words'].keys():
            # print(f"      >> wordid: {wid}")
            redisdb.sadd(u['userid']+':words', wid)  # add this wordid to the set of this user's wordids
            redisdb.hset(u['userid']+':'+wid, 'guesses', u['words'][wid]['guesses'])  # add the number of guesses
            if u['words'][wid]['found']:
                redisdb.hset(u['userid']+':'+wid, 'found', 1)  # set the word to found
            else:
                redisdb.hset(u['userid']+':'+wid, 'found', 0)  # set the word to not found
    print("--- done loading redisdb ---")


def newid(nickname="NoNickname"):

    global thread_queue

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    if nickname == None:
        nickname = "NoNickname"

    newid = str(uuid4())

    # add the new user into redis
    redisdb.sadd('alluserids', newid)
    redisdb.hset(newid, 'nickname', nickname)

    # add the new user to the mongo db
    thread_queue.put(('newuser', info_col, newid, nickname))

    return {"userid": newid}


def getmyids(nickname):

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    return redisdb.smembers(nickname)


def setnickname(userid, nickname):

    global thread_queue

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    redisdb.sadd(nickname, userid)
    redisdb.hset(userid, 'nickname', nickname)

    # change the user's nickname in the database
    # add the word to the database

    thread_queue.put(("setnickname", info_col, userid, nickname))

    return {"SUCCESS": nickname}


def newword(userid):

    global thread_queue

    global allowedanswers, wordict_col, info_col

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    alluserids = redisdb.smembers('alluserids')

    if userid not in alluserids:
        print(
            f"* * * * ERROR {userid} is not in the list of users.")
        return {"ERROR": f"{userid} is not in the list of users."}

    if len(redisdb.smembers(userid + ":words")) >= 1000:
        print(
            f"* * * * ERROR {userid} already has 1000 words assigned. If you haven't solved all of them, use getmywords to see them.")
        return {"ERROR": f"{userid} already has 1000 words assigned. If you haven't solved all of them, use getmywords to see them."}

    choicelist = list(allowedanswers)
    nw = choice(choicelist)  # the new word
    wordid = str(uuid4())  # the new wordid

    # print(f"### NEWWORD ### userid: {userid} nw: {nw} wordid: {wordid}")

    # add the word to redis
    x = redisdb.set(wordid, nw)
    x = redisdb.sadd(userid + ':words', wordid)  # add this wordid to the set of this user's wordids
    x = redisdb.hset(userid+':'+wordid, 'guesses', 0)  # add the number of guesses
    x = redisdb.hset(userid+':'+wordid, 'found', 0)

    # print(f"added '{nw}' as {wordid} to this user's {userid} words: {redisdb.smembers(userid + ':words')}")

    # add the word to the database
    thread_queue.put(("newword", info_col, wordict_col, userid, wordid, nw))

    print("wordid: ", wordid)
    return {"wordid": wordid}


def getmywords(userid):

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    # return this user's list of words and if they are solved
    wordlist = {}
    for wordid in redisdb.smembers(userid + ":words"):
        wordlist[wordid] = redisdb.hget(userid+":"+wordid, 'found') == '1'

    return {"words": wordlist}


def guess(userid, wordid, guess):

    global thread_queue

    global allowedguesses, info_col, wordict_col

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)
    # print(f"guessing {userid} {wordid} {guess}")

    if guess not in allowedguesses:
        print(
            f"* * * * ERROR Hey, {guess} is not in the list of allowed words. Use the allguesses command to get the list of allowed words")
        return {"ERROR": f"Hey, {guess} is not in the list of allowed words. Use the allguesses command to get the list of allowed words"}

    if len(guess) != 5:
        print("Hey, that's not a 5-letter word!")
        return {"ERROR": "Hey, that's not a 5-letter word!"}

    if wordid not in redisdb.smembers(userid + ":words"):
        print(
            f"* * * * ERROR Hey, {wordid} is not {userid}'s word! Use newword to get a new word, or getmywords to see your existing words")
        print(f" here is that user's wordlist: {redisdb.smembers(userid + ':words')}")
        return {"ERROR": "Hey, that's not your word! Use newword to get a new word, or getmywords to see your existing words"}

    # print(f"{numguesses}, {found}")
    if int(redisdb.hget(userid+':'+wordid, 'found')) == 1:
        print("Hey, you already found this word!")
        return redisdb.hget(userid+':'+wordid, 'guesses')
    else:
        redisdb.hincrby(userid+':'+wordid, 'guesses', 1)

    if False:  # I don't have a test for this, do I need one?
        print(
            f"* * * * ERROR Hey, {wordid} is not a valid word id! Use newword to get a new word, or getmywords to see your existing words")
        return {"ERROR": f"Hey, {wordid} not a valid word id! Use newword to get a new word, or getmywords to see your existing words"}

    answer = redisdb.get(wordid)
    answerlist = []
    found = False
    if answer == guess.lower():  # they guessed it
        found = True
        redisdb.hset(userid+':'+wordid, 'found', 1)
        returnstring = "11111"
    else:
        returnstring = ['', '', '', '', '']
        for i, c in enumerate(guess.lower()):
            # print(i, c)
            if c.isalpha() == False:
                print(f"Hey, that's not a letter in guess: {guess}!")
                return {"ERROR": f"Hey, that's not a letter in guess: {guess}!"}
            else:
                answerlist.append(answer[i])
            # print(i, c, answer[i])

        # we need multiplt passes because of repeated letters in guess that aren't repeated in answer
        for i, c in enumerate(guess.lower()):
            if c == answer[i]:
                returnstring[i] = "1"
                answerlist[i] = ''
            elif c not in answer:
                returnstring[i] = "3"

        for i, c in enumerate(guess.lower()):
            if returnstring[i] == '':
                if c in answerlist:
                    returnstring[i] = "2"
                    answerlist.remove(c)
                else:
                    returnstring[i] = "3"

    # print(f"returnstring: {returnstring}, numguesses: {guess}, found: {found}")

    # add the guess to this user's list in the database
    thread_queue.put(("guess", info_col, wordict_col, userid, wordid,
                      redisdb.hget(userid+':'+wordid, 'guesses'), found))

    return {"wordid": wordid,
            "guess": guess.lower(),
            "result": returnstring}


def stats(userid):

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    userstats = {}

    numsolved = 0
    totalguesses = 0
    for wordid in redisdb.smembers(userid + ":words"):
        # print(f"STATS: wordid: {wordid} found: {redisdb.hget(userid+':'+wordid, 'found')}")
        if int(redisdb.hget(userid+':'+wordid, 'found')) == 1:
            numsolved += 1
            totalguesses += int(redisdb.hget(userid+':'+wordid, 'guesses'))
            # print(f"STATS: {numsolved} {totalguesses}")

    # print(f"STATS: numsolved {numsolved} totalguesses {totalguesses}")
    if numsolved == 0:
        userstats['numsolved'] = 0
        userstats['average'] = 0
    else:
        userstats['numsolved'] = numsolved
        userstats['average'] = totalguesses / numsolved

    return userstats


def reset():
    print("*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!* RESET *!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*")
    mongo_tasks.reset()


def cleanup():
    print("*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!* CLEANUP *!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*")
    global info_col, wordict_col
    # deletes words not solved from wordict and words
    # deletes users who have solved 1 or 0 words
    mongo_tasks.cleanup(info_col, wordict_col)


def recalcstats():

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    statlist1000 = list()
    statlist100 = list()
    statlist10 = list()
    statlist1 = list()

    # calculate all stats
    for userid in redisdb.smembers('alluserids'):
        numwords = 0
        numguesses = 0
        for wordid in redisdb.smembers(userid + ":words"):
            r = redisdb.hgetall(userid+":"+wordid)
            if r['found'] == '1':
                numwords += 1
                numguesses += int(r['guesses'])

        if numwords >= 1000:
            # print("1000: ", redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords)
            statlist1000.append((redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords))
        elif numwords >= 100:
            # print("100: ", redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords)
            statlist100.append((redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords))
        elif numwords >= 10:
            # print("10: ", redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords)
            statlist10.append((redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords))
        elif numwords >= 1:
            # print("1: ", redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords)
            statlist1.append((redisdb.hget(userid, 'nickname'), numwords, numguesses/numwords))

    statlist1000.sort(key=lambda item: item[2])
    statlist1000.sort(key=lambda item: item[2])
    statlist1000.sort(key=lambda item: item[2])
    statlist1000.sort(key=lambda item: item[2])
    return (statlist1000, statlist100, statlist10, statlist1)


commands = set(["newid", "getmyids", "setnickname",
                "newword", "getmywords", "guess", "cleanup",
                "stats", "allstats", "allguesses", "allanswers", "reset"])


@app.route('/', methods=['POST'])
def post_command():

    redisdb = redis.from_url(REDIS_URL, decode_responses=True)

    global allowedguesses, allowedanswers, incof_col

    rj = request.get_json()
    # print(f"POST REQUEST: {rj}")

    command = rj.get('command')
    if command not in commands:
        return jsonify({
            "ERROR": "please send a valid command."
        })

    if command == "newid":
        return jsonify(newid(rj.get('nickname')))

    if command == "allstats":
        allstats = {}
        for u in info_col.find():
            allstats[u['userid']] = {}
            allstats[u['userid']]['nickname'] = u['nickname']
            allstats[u['userid']]['words'] = u['words']

        return jsonify(allstats)

    if command == "allguesses":
        return jsonify({"allguesses": list(allowedguesses)})

    if command == "allanswers":
        return jsonify({"allanswers": list(allowedanswers)})

    if command == "reset":
        return jsonify(reset())

    if command == "cleanup":
        return jsonify(cleanup())

    # the rest of the commands all require a userid
    userid = rj.get('userid')
    if not userid:
        return jsonify({
            "ERROR": "please send a userid."
        })
    if userid not in redisdb.smembers('alluserids'):
        print(f"* * * * * ERROR: {userid} not in list of all userids. Please send a valid userid.")
        return jsonify({
            "ERROR": f"{userid} not in list of all userids. Please send a valid userid."
        })
    # print(f"    userid: {userid}")

    if command == "getmyids":
        nn = rj.get("nickname")
        if not nn:
            return jsonify({
                "ERROR": "please send a nickname."
            })
        else:
            return jsonify(getmyids(nn))

    if command == "setnickname":
        nn = rj.get("nickname")
        if not nn:
            return jsonify({
                "ERROR": "please send a valid nickname."
            })
        else:
            return jsonify(setnickname(userid, nn))

    if command == "newword":
        return jsonify(newword(userid))

    if command == "getmywords":
        return jsonify(getmywords(userid))

    if command == "guess":
        wordid = rj.get("wordid")
        if not wordid:
            return jsonify({
                "ERROR": "please send a valid word id."
            })
        guessword = rj.get("guess")
        if not guessword:
            return jsonify({
                "ERROR": "please send a guess."
            })
        return jsonify(guess(userid, wordid, guessword))

    if command == "stats":
        return jsonify(stats(userid))


@app.route('/')
def index():

    (statlist1000, statlist100, statlist10, statlist1) = recalcstats()

    return render_template('index.html',
                           len1000=len(statlist1000),
                           len100=len(statlist100),
                           len10=len(statlist10),
                           len1=len(statlist1),
                           statlist1000=statlist1000,
                           statlist100=statlist100,
                           statlist10=statlist10,
                           statlist1=statlist1)


loadredis()

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=False, port=5000)
