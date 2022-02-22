import datetime   # This will be needed later
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from uuid import uuid4
from random import choice

print()

# Load config from a .env file:
load_dotenv()

MONGODB_URI = os.environ['MONGODB_URI']
# print(MONGODB_URI)

# Connect to your MongoDB cluster:

client = MongoClient(MONGODB_URI)

wordledb = client['wordle']
words = wordledb['words']
info = wordledb['info']

ids = set()
userwords = {}
nicknames = {}
for user in info.find():
    # print(f"adding: {user}")
    ids.add(user['userid'])
    userwords[user['userid']] = user['words']
    if user['nickname'] not in nicknames:
        nicknames[user['nickname']] = list()
    nicknames[user['nickname']].append(user['userid'])


wordlist = words.find_one()
guesses = set(wordlist['guesses'])
answers = set(wordlist['answers'])
wordict = dict(wordlist['wordict'])

# print(len(guesses), len(answers))


def newid(nickname="Nickname"):

    newuser = {}

    newid = str(uuid4())
    print(newid)
    ids.add(newid)
    if nickname not in nicknames:
        nicknames[nickname] = []
    nicknames[nickname].append(newid)

    newuser['userid'] = newid
    newuser['nickname'] = nickname
    newuser['words'] = {}

    x = info.insert_one(newuser)

    print(f"inserted: {x.inserted_id}")

    return newid


def getmyids(nickname):

    if nickname in nicknames:
        return nicknames[nickname]
    else:
        return []


def setnickname(id, nickname):
    if id not in ids:
        print("Not a valid ID, please use the 'newid' command to generate a new id")
        return -1

    if nickname in nicknames:
        if id in nicknames[nickname]:
            print("This ID is already connected to this Nickname")
        else:
            nicknames[nickname].append(id)

    # change the user's nickname in the database
    u = info.find_one({"userid": id})  # find the user in the database
    u['nickname'] = nickname  # add the new wordid to the user's list
    newvalues = {"$set": u}
    info.update_one({"userid": id}, newvalues)


def newword(id):

    if id not in ids:
        print("Not a valid ID, please use the 'newid' command to generate a new id")
        return -1

    choicelist = list(answers - set(userwords[user['userid']].keys()))
    if len(choicelist) == 0:
        print("no words left")
        return NULL

    newword = choice(choicelist)

    print(f"userid = {id}, newword = {newword}")
    h = str(uuid4())  # hashing won't work for "closeness"

    # add the word to this user's list
    userwords[user['userid']][h] = newword

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

    return h


def getmywords(id):

    if id not in ids:
        print("Not a valid ID, please use the 'newid' command to generate a new id")
        return -1

    return userwords[id]


def guess(userid, wordid, guess):

    print(f"guessing {userid} {wordid} {guess}")

    if wordid not in userwords[userid].keys():
        print("Hey, that's not your word! Use newword to get a new word, or getmywords to see your existing words")
        return 0

    if len(guess) != 5:
        print("Hey, that's not a 5-letter word!")
        return 0

    numguesses, found = userwords[userid][wordid]
    # print(f"{numguesses}, {found}")
    if found == True:
        print("Hey, you already found this word!")
        return numguesses
    else:
        numguesses += 1

    answer = wordict[wordid]
    if answer == guess.lower():  # they guessed it
        found = True
        returnstring = "11111"
    else:
        returnstring = ""
        for i, c in enumerate(guess.lower()):
            # print(i, c)
            if c.isalpha() == False:
                print("Hey, that's not a letter!")
                return 0
            # print(i, c, answer[i])
            if c == answer[i]:
                returnstring += "1"
            elif c in answer:
                returnstring += "2"
            else:
                returnstring += "3"

    # add the guess to this user's list in the database
    u = info.find_one({"userid": userid})  # find the user in the database
    # print(f"{numguesses}, {found}")
    # add the new wordid to the user's list
    u['words'][wordid] = [numguesses, found]
    newvalues = {"$set": u}
    info.update_one({"userid": userid}, newvalues)

    return returnstring


# print(newword("JAB"))
print(guess("JAB", '2', "timer"))
# print(getmyids('Mr. B'))
# setnickname("JAB", "Mr. Bartucz")
# print(newid("jobartucz"))
