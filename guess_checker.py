while True:
    answer = input("answer: ")
    guess = input("guess: ")
    answerlist = []
    if answer == guess.lower():  # they guessed it
        found = True
        returnstring = "11111"
    else:
        returnstring = ['', '', '', '', '']
        for i, c in enumerate(guess.lower()):
            # print(i, c)
            if c.isalpha() == False:
                print(f"Hey, that's not a letter in guess: {guess}!")
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

    print(returnstring)
