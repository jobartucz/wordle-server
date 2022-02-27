

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

    # print(" * * * * * GUESS: ", info_col, userid, wordid, numguesses, found)

    user = info_col.find_one({"userid": userid})
    if wordid not in user['words']:
        user['words'][wordid] = {}
    user['words'][wordid]['guesses'] = int(numguesses)
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


def cleanup(info_col, wordict_col):

    info = info_col.find()

    wordids_to_false = set()

    for user in info:
        for wordid in user['words'].keys():
            if user['words'][wordid]['found'] == 0 or user['words'][wordid]['found'] == '0' or user['words'][wordid]['found'] == False:
                wordids_to_false.add(wordid)

    info = info_col.find()
    for user in info:
        for wordid in user['words'].keys():
            if wordid in wordids_to_false:
                user['words'][wordid]['found'] = False
            else:
                user['words'][wordid]['found'] = True
        newvalues = {"$set": user}
        info_col.update_one({"userid": user['userid']}, newvalues)

    do_delete = False
    if do_delete:
        wordids_with_guesses = set()
        userids_to_delete = set()

        for user in info:
            wordids_to_delete = set()
            for wordid in user['words'].keys():
                if user['words'][wordid]['guesses'] == 0:
                    wordids_to_delete.add(wordid)
                else:
                    wordids_with_guesses.add(wordid)

            for wordid in wordids_to_delete:
                del user['words'][wordid]
                newvalues = {"$set": user}
                info_col.update_one({"userid": user['userid']}, newvalues)

            if len(user['words'].keys()) < 2:
                userids_to_delete.add(user['userid'])

        for userid in userids_to_delete:
            myquery = {"userid": userid}
            print(f"Deleting userid: {userid}")
            info_col.delete_one(myquery)
        print(f"Deleted {len(userids_to_delete)} users...")

        print(f"Found {len(wordids_with_guesses)} words to save")

        counter = 0
        wordict = wordict_col.find()
        for word in wordict:
            if word['wordid'] not in wordids_with_guesses:
                # print(f"deleting {word['word']}, {word['wordid']}")
                counter += 1
                myquery = {"wordid": wordid}
                info_col.delete_one(myquery)

        print(f"Deleted {counter} unused words")
    return
