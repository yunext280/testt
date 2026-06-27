import os, socket, json
from flask import Flask, request, abort, render_template, jsonify

app = Flask(__name__)
TOKEN = os.environ.get("TOKEN", "")

VERSION = "0"
try:
    with open(os.path.expanduser("~/version.md")) as f:
        VERSION = f.read().strip()
except:
    pass

@app.before_request
def check_token():
    if request.path.startswith("/static/"):
        return
    if request.args.get("token") != TOKEN:
        abort(403)

@app.route("/")
def index():
    return render_template("index.html", version=VERSION, token=TOKEN)

@app.route("/aviso")
def aviso():
    return render_template("aviso.html", version=VERSION)

@app.route("/seotime")
def seotime():
    return render_template("seotime.html", version=VERSION)

@app.route("/set_cookies", methods=["POST"])
def set_cookies():
    site = request.args.get("site", "unknown")
    try:
        data = request.get_json(force=True)
        path = os.path.expanduser(f"~/{site}_cookies.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    with open(os.path.expanduser("~/flask.port"), "w") as f:
        f.write(str(port))
    app.run(host="127.0.0.1", port=port)
