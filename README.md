    Welcome to the wordle server!!
    This API takes JSON-formatted post only
    All items must contain one of the following commands as a 'command' item:
    
    Commands
    
    newid takes an optional 'nickname' argument, returns a new unique userid
    setnickname takes a 'userid' and a 'nickname'
    getmyids takes only a 'userid' argument and returns a list of all userids that have this nickname
    newword takes only a 'userid' and returns a unique wordid to use when guessing
    getmywords takes only a 'userid' and returns the list of wordids, number of guesses, and whether they have been solved
    guess takes a 'userid', a 'wordid', and a 'guess'. Returns a 5-digit 'result' where each digit is '1' - correct letter in correct position, '2' - correct letter in wrong position, '3' - letter not in word
    stats takes a 'userid' and returns your average number of guesses for words you have completed
