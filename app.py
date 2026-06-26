import os, socket
from flask import Flask, request, abort

app = Flask(__name__)
TOKEN = os.environ.get("TOKEN", "")

@app.before_request
def check_token():
    if request.args.get("token") != TOKEN:
        abort(403)

@app.route("/")
def index():
    return "Flask is running"

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    with open(os.path.expanduser("~/flask.port"), "w") as f:
        f.write(str(port))
    app.run(host="127.0.0.1", port=port)
