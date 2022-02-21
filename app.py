# app.py
from flask import Flask, request, jsonify
app = Flask(__name__)

commands = set(["newid", "getmyids", "setnickname", "newword", "getmywords", "guess"])


@app.route('/post/', methods=['POST'])
def post_something():
    rj = request.get_json()
    print(rj)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    command = rj.get('command')
    if command in commands:
        return jsonify({
            "Message": f"Welcome {command} to our awesome platform!!",
            # Add this option to distinct the POST request
            "METHOD" : "POST"
        })
    else:
        return rj
        return jsonify({
            "ERROR": "no valid command found, please send a valid command."
        })

# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to the wordle server!!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
