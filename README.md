 # Welcome to the wordle server!!
    
 ### there is an example client here:  https://replit.com/@JohnBartucz/Wordle-Client#main.py
    
 ## This API takes JSON-formatted POST only
 ## All items must contain one of the following commands as a 'command' item:
    
 ### Commands
    
- newid takes an optional 'nickname' argument, returns a new unique 'userid'
- newword takes only a valid 'userid' and returns a unique 'wordid' to use when guessing
- guess takes a 'userid', a 'wordid', and a 'guess'. Returns a 5-digit 'result' where each digit is:
  - '1' - correct letter in correct position, 
  - '2' - correct letter in wrong position, 
  - '3' - letter not in word
- setnickname takes a 'userid' and a 'nickname'
- getmyids takes only a 'nickname' argument and returns a list of all userids that have this nickname
- getmywords takes only a 'userid' and returns the list of wordids, number of guesses, and whether they have been solved
- stats takes a 'userid' and returns the average number of guesses for words completed
- allstats returns all users' nicknames, wordids, # of guesses and whether word was found
- allguesses returns a list of all possible words you are allowed to guess
- allanswers returns a list of all possible words that could be an answer (a subset of allguesses)
