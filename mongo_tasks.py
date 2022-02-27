

def newuser(info_col, newid, nickname):

    newuser = {}
    newuser['userid'] = newid
    newuser['nickname'] = nickname
    newuser['words'] = {}
    x = info_col.insert_one(newuser)

    # print(f"inserted new user into mongodb: {x.inserted_id}")


def newword(info_col, wordict_col, userid, wordid, word):

    user = info_col.find_one({"userid": userid})
    # add the word to this user's list in the database
    # u = info.find_one({"userid": id})  # find the user in the database
    # add the new wordid to the user's list
    user['words'][wordid] = {"guesses": 0, "found": False}
    newvalues = {"$set": user}
    info_col.update_one({"userid": userid}, newvalues)

    # add the word to the wordict in the database
    x = wordict_col.insert_one({"word": word, "wordid": wordid})

    # print(f"inserted new word into mongodb. word: {word} with id {wordid}: {x.inserted_id}")


def guess(info_col, userid, wordid, numguesses, found):

    user = info_col.find_one({"userid": userid})
    user['words'][wordid]['guesses'] = numguesses
    user['words'][wordid]['found'] = found
    newvalues = {"$set": user}
    info_col.update_one({"userid": userid}, newvalues)


def setnickname(info_col, userid, nickname):

    u = info_col.find_one({"userid": userid})  # find the user in the database
    u['nickname'] = nickname  # add the new wordid to the user's list
    newvalues = {"$set": u}
    info_col.update_one({"userid": id}, newvalues)


def reset():
    return
