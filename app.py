import os, socket, json, threading, time
from flask import Flask, request, abort, render_template, jsonify, send_file, Response
import selenium_bot

app = Flask(__name__)
TOKEN = os.environ.get("TOKEN", "")

latest_frame = None

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
    aviso_done = os.path.exists(os.path.expanduser("~/aviso_cookies.json"))
    yt_done = os.path.exists(os.path.expanduser("~/youtube_cookies.json"))
    bot_started = False
    sel_path = os.path.expanduser("~/sel_bot.json")
    if os.path.exists(sel_path):
        with open(sel_path) as f:
            data = json.load(f)
            bot_started = data.get("start", False)
    return render_template("aviso.html", version=VERSION,
                           aviso_done=aviso_done, yt_done=yt_done,
                           bot_started=bot_started,
                           token=TOKEN)

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

@app.route("/bot/start", methods=["POST"])
def bot_start():
    data = request.get_json(force=True)
    user_agent = data.get("user_agent", "")
    started = selenium_bot.start_bot(user_agent)
    sel_path = os.path.expanduser("~/sel_bot.json")
    with open(sel_path, "w") as f:
        json.dump({"start": started}, f)
    return jsonify({"status": "ok" if started else "already_running"})

@app.route("/bot/stop", methods=["POST"])
def bot_stop():
    global latest_frame
    selenium_bot.stop_bot()
    sel_path = os.path.expanduser("~/sel_bot.json")
    with open(sel_path, "w") as f:
        json.dump({"start": False}, f)
    latest_frame = None
    ss_path = os.path.expanduser("~/aviso_screenshot.png")
    if os.path.exists(ss_path):
        os.remove(ss_path)
    return jsonify({"status": "ok"})

@app.route("/screenshot/aviso")
def screenshot_aviso():
    path = os.path.expanduser("~/aviso_screenshot.png")
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return "", 404

def listen_udp():
    global latest_frame
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 9999))
    sock.settimeout(1)
    buf = b''
    while True:
        try:
            data, _ = sock.recvfrom(65535)
            if not data:
                continue
            if b'\xff\xd8' in data:
                buf = data[data.find(b'\xff\xd8'):]
            else:
                buf += data
            if b'\xff\xd9' in buf:
                latest_frame = buf[:buf.find(b'\xff\xd9')+2]
                buf = b''
        except socket.timeout:
            continue
        except:
            pass

@app.route("/video_feed")
def video_feed():
    def gen():
        global latest_frame
        while True:
            if latest_frame is not None:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
            time.sleep(0.04)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/stream_status")
def stream_status():
    return jsonify({"active": latest_frame is not None, "bot_running": selenium_bot.is_running()})

if __name__ == "__main__":
    threading.Thread(target=listen_udp, daemon=True).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    with open(os.path.expanduser("~/flask.port"), "w") as f:
        f.write(str(port))
    app.run(host="127.0.0.1", port=port, use_reloader=False)
