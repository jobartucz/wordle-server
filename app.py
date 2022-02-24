# app.py
import os
from random import choice
from re import S
from uuid import uuid4
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, request, jsonify
app = Flask(__name__)

# print()

# Load config from a .env file:
load_dotenv()

MONGODB_URI = os.environ['MONGODB_URI']
# print(MONGODB_URI)

# Connect to your MongoDB cluster:

client = MongoClient(MONGODB_URI)

wordledb = client['wordle']
words = wordledb['words']
info = wordledb['info']

allids = set()
userwords = {}
nicknameids = {}
nicknames = {}

for user in info.find():
    # print(f"adding: {user}")
    allids.add(user['userid'])
    userwords[user['userid']] = user['words']
    if user['nickname'] not in nicknameids:
        nicknameids[user['nickname']] = list()
    nicknameids[user['nickname']].append(user['userid'])
    nicknames[user['userid']] = user['nickname']

wordlist = words.find_one()
guesses = set(wordlist['guesses'])
answers = set(wordlist['answers'])
wordict = dict(wordlist['wordict'])


def reload():

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    userwords = {}
    nicknameids = {}
    nicknames = {}

    for user in info.find():
        # print(f"adding: {user}")
        allids.add(user['userid'])
        userwords[user['userid']] = user['words']
        if user['nickname'] not in nicknameids:
            nicknameids[user['nickname']] = list()
        nicknameids[user['nickname']].append(user['userid'])
        nicknames[user['userid']] = user['nickname']

    wordlist = words.find_one()
    guesses = set(wordlist['guesses'])
    answers = set(wordlist['answers'])
    wordict = dict(wordlist['wordict'])


def newid(nickname="NoNickname"):

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    newuser = {}

    newid = str(uuid4())
    print(f"------->>>> adding {newid} to {allids}")
    allids.add(newid)
    print(f"------->>>> result: {allids}")
    if nickname not in nicknameids:
        nicknameids[nickname] = []
    nicknameids[nickname].append(newid)
    nicknames[newid] = nickname

    newuser['userid'] = newid
    newuser['nickname'] = nickname
    newuser['words'] = {}

    print(f"------->>>> adding {newid} to {userwords.keys()}")
    userwords[newid] = {}
    print(f"------->>>> result: {userwords.keys()}")

    x = info.insert_one(newuser)

    # print(f"inserted: {x.inserted_id}")

    return {"userid": newid}


def getmyids(nickname):

    global nicknameids

    if nickname in nicknameids:
        return nicknameids[nickname]
    else:
        return []


def setnickname(id, nickname):

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    if id not in allids:
        print(f"* * * * ERROR: {id} a valid ID in {allids}")
        return {"ERROR": f"{id} is not a valid ID, please use the 'newid' command to generate a new id"}

    if nickname in nicknameids:
        if id in nicknameids[nickname]:
            print(
                f"This ID {id} is already connected to this Nickname {nickname}")
            return {"ERROR": "This ID is already connected to this Nickname"}
        else:
            nicknameids[nickname].append(id)
    nicknames[id] = nickname

    # change the user's nickname in the database
    u = info.find_one({"userid": id})  # find the user in the database
    u['nickname'] = nickname  # add the new wordid to the user's list
    newvalues = {"$set": u}
    info.update_one({"userid": id}, newvalues)

    return {"SUCCESS": nickname}


def newword(id):

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    if id not in allids:
        print(
            f"{id} is not a valid ID, please use the 'newid' command to generate a new id")
        for i in allids:
            print("---------->>>> ", i, id, type(i), type(id), i == id)
        return {"ERROR": f"{id} is not a valid ID, please use the 'newid' command to generate a new id {allids}"}

    choicelist = list(answers - set(userwords[user['userid']].keys()))
    if len(choicelist) == 0:
        print("no words left")
        return {"ERROR": "No words left"}

    newword = choice(choicelist)

    h = str(uuid4())  # hashing won't work for "closeness"
    # print(f"userid = {id}, newword = {newword}, wordid = {h}")

    # add the word to this user's list
    userwords[id][h] = [0, False]

    # add the word to this user's list in the database
    u = info.find_one({"userid": id})  # find the user in the database
    u['words'][h] = [0, False]  # add the new wordid to the user's list
    newvalues = {"$set": u}
    info.update_one({"userid": id}, newvalues)
    # u = info.find_one({"userid":id})
    # print(u)

    # add the word to the wordict
    wordict[h] = newword

    # add the word to the wordict in the database
    u = words.find_one()
    u['wordict'][h] = newword
    newvalues = {"$set": u}
    myquery = {"id": 1}
    words.update_one(myquery, newvalues)

    return {"wordid": h}


def getmywords(id):

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    if id not in allids:
        print(
            f"{id} is not a valid ID, please use the 'newid' command to generate a new id")
        return {"ERROR": f"{id} is not a valid ID, please use the 'newid' command to generate a new id"}

    return userwords[id]


def guess(userid, wordid, guess):

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    # print(f"guessing {userid} {wordid} {guess}")

    if wordid not in userwords[userid].keys():
        # print(wordid)
        # print(userwords[userid].keys())
        print(
            f"* * * * ERROR Hey, {wordid} is not {userid}'s word! Use newword to get a new word, or getmywords to see your existing words")
        return {"ERROR": "Hey, that's not your word! Use newword to get a new word, or getmywords to see your existing words"}

    if len(guess) != 5:
        print("Hey, that's not a 5-letter word!")
        return {"ERROR": "Hey, that's not a 5-letter word!"}

    numguesses, found = userwords[userid][wordid]
    # print(f"{numguesses}, {found}")
    if found == True:
        print("Hey, you already found this word!")
        return numguesses
    else:
        numguesses += 1

    answer = wordict[wordid]
    # print(F"answer: {answer}, guess: {guess}")
    if answer == guess.lower():  # they guessed it
        found = True
        returnstring = "11111"
    else:
        returnstring = ""
        for i, c in enumerate(guess.lower()):
            # print(i, c)
            if c.isalpha() == False:
                print(f"Hey, that's not a letter in guess: {guess}!")
                return {"ERROR": "Hey, that's not a letter!"}
            # print(i, c, answer[i])
            if c == answer[i]:
                returnstring += "1"
            elif c in answer:
                returnstring += "2"
            else:
                returnstring += "3"
    # print(f"returnstring: {returnstring}, found: {found}")

    # add the guess to this user's list in the database
    u = info.find_one({"userid": userid})  # find the user in the database
    # print(f"{numguesses}, {found}")
    # add the new wordid to the user's list
    u['words'][wordid] = [numguesses, found]
    newvalues = {"$set": u}
    info.update_one({"userid": userid}, newvalues)

    userwords[userid][wordid] = [numguesses, found]
    # print(f"updated {userid} with {newvalues}")

    return {"wordid": wordid,
            "guess": guess.lower(),
            "result": returnstring}


def stats(userid):

    global allids, userwords, nicknameids, nicknames, guesses, answers, wordict

    userstats = {}

    numsolved = 0
    totalguesses = 0
    for wordid, status in userwords[userid].items():
        if status[1] == True:
            numsolved += 1
            totalguesses += status[0]

    if numsolved == 0:
        userstats['numsolved'] = 0
        userstats['average'] = 0
    else:
        userstats['numsolved'] = numsolved
        userstats['average'] = totalguesses / numsolved

    return userstats


def reset():
    # delete the wordid->word dictionary
    u = words.find_one({"id": 1})  # find the user in the database
    u['wordict'] = dict()  # add the new wordid to the user's list
    newvalues = {"$set": u}
    words.update_one({"id": 1}, newvalues)

    # Delete all guesses
    x = info.delete_many({})
    print(x.deleted_count, " documents deleted.")
    return {"DELETED": x.deleted_count}


commands = set(["newid", "getmyids", "setnickname",
                "newword", "getmywords", "guess",
                "stats", "allstats", "allwords", "reload", "reset"])


@app.route('/', methods=['POST'])
def post_command():
    rj = request.get_json()
    # print(rj)
    command = rj.get('command')
    if command not in commands:
        return jsonify({
            "ERROR": "please send a valid command."
        })

    print(f"COMMAND: {command}")
    if command == "reload":
        print("reloading")
        reload()
        return jsonify({"status": "reloaded"})

    if command == "newid":
        return jsonify(newid(rj.get('nickname')))

    if command == "allstats":
        allstats = {}
        for u in info.find():
            allstats[u['userid']] = {}
            allstats[u['userid']]['nickname'] = u['nickname']
            allstats[u['userid']]['words'] = u['words']

        return jsonify(allstats)

    if command == "allwords":
        return jsonify({"answers": list(answers)})

    if command == "reset":
        return jsonify(reset())

    # the rest of the commands all require a userid
    userid = rj.get('userid')
    if not userid:
        return jsonify({
            "ERROR": "please send a valid userid."
        })
    print(f"    userid: {userid}")

    if command == "getmyids":
        nn = rj.get("nickname")
        if not nn:
            return jsonify({
                "ERROR": "please send a valid nickname."
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
    homepage = "<h1>Welcome to the CTECH wordle server!!</h1>\n"
    homepage += "<h2>This API takes JSON-formatted post requests only (and returns JSON docs)</h2>\n"
    homepage += "<h2>All items must contain one of the following commands as a 'command' item:</h2>\n"
    homepage += "<h2>Commands</h2>\n"
    homepage += "<ul>\n"
    homepage += "<li><strong>newid</strong> takes an optional 'nickname' argument, returns a new unique 'userid'</li>\n"
    homepage += "<li><strong>newword</strong> takes only a valid 'userid' and returns a unique 'wordid' to use when guessing</li>\n"
    homepage += "<li><strong>guess</strong> takes a 'userid', a 'wordid', and a 'guess'. Returns a 5-digit 'result' where each digit is '1' - correct letter in correct position, '2' - correct letter in wrong position, '3' - letter not in word</li>\n"
    homepage += "<li><strong>setnickname</strong> takes a 'userid' and a 'nickname'</li>\n"
    homepage += "<li><strong>getmyids</strong> takes only a 'nickname' argument and returns a list of all userids that have this nickname</li>\n"
    homepage += "<li><strong>getmywords</strong> takes only a 'userid' and returns the list of wordids, number of guesses, and whether they have been solved</li>\n"
    homepage += "<li><strong>stats</strong> takes a 'userid' and returns the average number of guesses for words completed</li>\n"
    homepage += "<li><strong>allstats</strong> returns all users' nicknames, wordids, # of guesses and whether word was found</li>\n"
    homepage += "<li><strong>allwords</strong> returns a list of all possible words</li>\n"
    homepage += "</ul>\n"

    homepage += "<h2>Leaderboard</h2>\n"
    homepage += "<ul>\n"
    for i in allids:
        # print(i, nicknames[i])
        s = stats(i)
        if s['numsolved'] > 0:
            homepage += f"<li><strong>{nicknames[i]}</strong> has solved {s['numsolved']} with an average of {s['average']}</li>\n"
    homepage += "</ul>\n"

    return homepage


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
