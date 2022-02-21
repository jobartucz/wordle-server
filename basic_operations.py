import datetime   # This will be needed later
import os
from dotenv import load_dotenv
from pymysql import NULL
from pymongo import MongoClient
from uuid import uuid4
from random import choice

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
   print(f"adding: {user}")
   ids.add(user['userid'])
   userwords[user['userid']] = user['words']
   if user['nickname'] not in nicknames:
      nicknames[user['nickname']] = list()
   nicknames[user['nickname']].append(user['userid'])


wordlist = words.find_one()
guesses = set(wordlist['guesses'])
answers = set(wordlist['answers'])
wordict = dict(wordlist['wordict'])

print(len(guesses), len(answers))


def newid(nickname = "Nickname"):
   
   newid = uuid4()
   ids.add(newid)
   print(newid)
   return newid

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
   h = uuid4() # hashing won't work for "closeness"

   # add the word to this user's list
   u = info.find_one({"userid":id})
   # print(u)
   u['words'][newword] = []
   newvalues = { "$set": u }
   info.update_one({"userid":id}, newvalues)
   # u = info.find_one({"userid":id})
   # print(u)
   return h


def getmywords(id):

   if id not in ids:
      print("Not a valid ID, please use the 'newid' command to generate a new id")
      return -1
   
   return userwords[id]

def guess(userid, wordid, guess):

   if wordid not in userwords[userid].keys():
      print("Hey, that's not your word!")
      return 0

   if len(guess) != 5:
      print("Hey, that's not a 5-letter word!")
      return 0

   returnstring = ""
   answer = wordict[wordid]
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

   return returnstring

def getmyids(nickname):

   if nickname in nicknames:
      return nicknames[nickname]
   else:
      return []


print(getmywords("JAB"))
print(guess("JAB",'1',"mower"))
print(getmyids('Mr. B'))