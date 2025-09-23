from flask import Flask, request, jsonify, render_template, send_file, url_for, abort, Response
from service.tiktok_client import (start_client,
                                   get_latest_comment,
                                   start_cleanup_thread,
                                   is_live_stream,
                                   enable_likes,
                                   enable_comments,
                                   enable_gifts,
                                   latest_comments)
from service.youtube_client import start_client_yt, get_latest_comment_yt, start_cleanup_thread_yt, get_live_chat, latest_comments as lastest_comments_youtube
from service.facebook_client import start_client_fb, get_latest_comment_fb, start_cleanup_thread_fb, get_feedback_id, latest_comments as lastest_comments_facebook
import os
from threading import Lock
from utils import utils
import asyncio
from service import ai
from functools import wraps
app = Flask(__name__)

comment_lock_tiktok = Lock()
comment_lock_youtube = Lock()
comment_lock_facebook = Lock()
audio_dir_tiktok = "audio_files_tiktok"
audio_dir_youtube = "audio_files_youtube"
audio_dir_facebook = "audio_files_facebook"
os.makedirs(audio_dir_tiktok, exist_ok=True)
os.makedirs(audio_dir_youtube, exist_ok=True)
os.makedirs(audio_dir_facebook, exist_ok=True)

old_comment_tiktok = {}
old_comment_youtube = {}
old_comment_facebook = {}

ALLOWED_ORIGINS = ['https://livestreamvoice.com','http://localhost']
PATH_ALLOWED_ORIGINS = ['/', '/youtube', '/facebook', '']
PATH_STARTS_WITH_ORIGINS = ['/tiktok/check', '/facebook/check', '/youtube/check',
    '/tiktok/start', '/facebook/start', '/youtube/start',
    '/tiktok/widget/', '/youtube/widget/', '/facebook/widget/',
    '/tiktok/comment/widget/', '/youtube/comment/widget/', '/facebook/comment/widget/']


COUNTER_FILE = 'utils/counter.txt'

def read_counter():
    try:
        if not os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'w') as f:
                f.write('0')
        with open(COUNTER_FILE, 'r') as f:
            return int(f.read())
    except:
        return 0

def write_counter(count):
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(count))

def count_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        count = read_counter()
        count += 1
        write_counter(count)
        return func(*args, **kwargs)
    return wrapper


@app.before_request
def block_external_requests():
    if request.path in PATH_ALLOWED_ORIGINS or request.path.startswith(tuple(PATH_STARTS_WITH_ORIGINS)):
        return
    origin = request.headers.get('Origin')
    referer = request.headers.get('Referer')
    if origin and origin not in ALLOWED_ORIGINS:
        abort(403)

    if referer and not referer.startswith(tuple(ALLOWED_ORIGINS)):
        abort(403)


@app.route('/robots.txt')
def robots_txt():
    robots_content = "User-agent: *\nAllow: /\nSitemap: https://livestreamvoice.com/sitemap.xml"
    return Response(robots_content, mimetype='text/plain')
@app.route('/sitemap.xml')
def sitemap():
    robots_content = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://livestreamvoice.com/</loc><priority>1.00</priority></url>
      <url><loc>https://livestreamvoice.com/static/page/privacy.html</loc><priority>0.2</priority></url>
      <url><loc>https://livestreamvoice.com/static/page/terms.html</loc><priority>0.2</priority></url>
      <url><loc>https://livestreamvoice.com/static/page/about.html</loc><priority>0.2</priority></url>
    </urlset>
    """
    return Response(robots_content, mimetype='application/xml')
@app.route('/ads.txt')
def ads_txt():
    ads_content = "google.com, pub-5742059082599160, DIRECT, f08c47fec0942fa0"
    return Response(ads_content, mimetype='text/plain')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html")
@app.route("/")
@count_request
def index():
    return render_template("index.html", counter_requests = read_counter())
@app.route("/youtube")
@count_request
def youtube():
    return render_template("youtube.html")
@app.route("/facebook")
@count_request
def facebook():
    return render_template("facebook.html")
@app.route("/tiktok/check/<username>", methods=["GET"])
@count_request
def check_is_live_stream(username):
    if not username:
        return jsonify({"error": "Missing username"}), 400
    check = asyncio.run(is_live_stream(username))
    if check:
        return jsonify({"message": f"Started TikTok client for {username}"}), 200
    return jsonify({"error": f"{username} not live"}), 400

    # if not username:
    #     return jsonify({"error": "Missing username"}), 400
    # check = is_live_stream(username)
    # if check:
    #     return jsonify({"message": f"Started TikTok client for {username}"}), 200
    # return jsonify({"error": f"{username} not live"}), 400

@app.route("/tiktok/start", methods=["POST"])
@count_request
def start():
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400

    start_client(username)
    utils.send_mess(username)
    return jsonify({"message": f"Started TikTok client for {username}"}), 200

@app.route("/tiktok/comment/<username>", methods=["POST"])
def get_comment(username):
    reply = request.form.get("reply")

    for key, store in [("like", enable_likes), ("cmt", enable_comments), ("gift", enable_gifts)]:
        store[username] = bool(request.form.get(key))

    if reply:
        enable_likes[username] = False

    has_new_comment = False
    comment = get_latest_comment(username)
    audio_url = url_for('get_audio_tiktok', username=username)

    if comment:
        if username in old_comment_tiktok.keys():
            if old_comment_tiktok[username] != comment:
                old_comment_tiktok[username] = comment
                has_new_comment = True
        else:
            old_comment_tiktok[username] = comment

        if has_new_comment:
            with comment_lock_tiktok:
                mp3_path = os.path.join(audio_dir_tiktok, f"{username}.wav")
                if reply:
                    if not comment.lower().startswith('cảm ơn'):
                        name = utils.cut_string_head(comment, ' : ')
                        content = utils.cut_string_last(comment, ' : ')
                        # try:
                        #     result_ai = ai.copilot(name, content)
                        # except:
                        #     result_ai = ai.process_v2(name, content)
                        try:
                            result_ai = ai.process_v2(name, content)
                        except:
                            result_ai = ''
                        answer = comment + " . . . " + result_ai
                        utils.save_speech(answer, mp3_path)
                    else:
                        comment = old_comment_tiktok[username]
                else:
                    utils.save_speech(comment, mp3_path)
        else:
            comment = old_comment_tiktok[username]

    return jsonify({"username": username, "latest_comment": comment, "audio_url": audio_url})

@app.route("/tiktok/comment/widget/<username>")
def get_comment_widget(username):
    try:
        comment = latest_comments[username]
        return jsonify({"username": username, "latest_comment": comment, "audio_url": ''})
    except:
        return jsonify({"username": username, "latest_comment": 'Đang khởi tạo'})


@app.route("/tiktok/audio/<username>")
def get_audio_tiktok(username):
    # mp3_path = os.path.join(audio_dir_tiktok, f"{username}.mp3")
    mp3_path = os.path.join(audio_dir_tiktok, f"{username}.wav")
    if os.path.exists(mp3_path):
        utils.change_speed(mp3_path,mp3_path, 1.3)
        # return send_file(mp3_path, mimetype="audio/mpeg")
        return send_file(mp3_path, mimetype="audio/wav")
    return jsonify({"error": "No audio found"}), 404

@app.route("/tiktok/widget/<username>")
def tiktok_widget(username):
    return render_template("tiktok_widget.html", username = username)

## yt
@app.route("/youtube/check/<url_encode>", methods=["GET"])
@count_request
def check_is_live_stream_youtube(url_encode):
    url = utils.base64UrlDecode(url_encode)
    if not url:
        return jsonify({"error": "Missing url"}), 400
    check = get_live_chat(url)
    if check != '':
        return jsonify({"message": f"Started Youtube client for {url}"}), 200
    return jsonify({"error": f"{url} not live"}), 400

@app.route("/youtube/start", methods=["POST"])
@count_request
def start_youtube():
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400

    start_client_yt(username)
    utils.send_mess(username)
    return jsonify({"message": f"Started Youtube client for {username}"}), 200

@app.route("/youtube/comment/<url_encode>", methods=["POST"])
def get_comment_youtube(url_encode):
    reply = request.form.get("reply")

    url = utils.base64UrlDecode(url_encode)
    if not url:
        return jsonify({"error": "Missing username"}), 400

    has_new_comment = False

    comment = get_latest_comment_yt(url)
    audio_url = url_for('get_audio_youtube', url_encode=url_encode)
    # filename = utils.convert_username_youtube(username) + ".mp3"
    filename = utils.convert_url_to_username(url) + ".wav"
    if comment:
        if url in old_comment_youtube.keys():
            if old_comment_youtube[url] != comment:
                old_comment_youtube[url] = comment
                has_new_comment = True
        else:
            old_comment_youtube[url] = comment

        if has_new_comment:
            with comment_lock_youtube:
                mp3_path = os.path.join(audio_dir_youtube, filename)
                # utils.save_speech(comment, mp3_path)
                if reply:
                    name = utils.cut_string_head(comment, ' : ')
                    content = utils.cut_string_last(comment, ' : ')
                    # try:
                    #     result_ai = ai.copilot(name, content)
                    # except:
                    #     result_ai = ai.process_v2(name, content)
                    try:
                        result_ai = ai.process_v2(name, content)
                    except:
                        result_ai = ''
                    answer = comment + " . . . " + result_ai
                    utils.save_speech(answer, mp3_path)
                else:
                    utils.save_speech(comment, mp3_path)
        else:
            # comment = ''
            comment = old_comment_youtube[url]
        # with comment_lock:
        #     mp3_path = os.path.join(audio_dir_youtube, filename)
        #     # tts = gTTS(comment, lang='vi')
        #     # tts.save(mp3_path)
        #     utils.save_speech(comment, mp3_path)

    return jsonify({"username": url, "latest_comment": comment, "audio_url": audio_url})

@app.route("/youtube/comment/widget/<url_encode>")
def get_comment_widget_youtube(url_encode):
    url = utils.base64UrlDecode(url_encode)
    try:
        comment = lastest_comments_youtube[url]
        return jsonify({"username": url, "latest_comment": comment, "audio_url": ''})
    except:
        return jsonify({"username": url, "latest_comment": 'Đang khởi tạo'})
@app.route("/youtube/audio/<url_encode>")
def get_audio_youtube(url_encode):
    url = utils.base64UrlDecode(url_encode)
    # filename = utils.convert_username_youtube(username) + ".mp3"
    filename = utils.convert_url_to_username(url) + ".wav"
    mp3_path = os.path.join(audio_dir_youtube, filename)
    if os.path.exists(mp3_path):
        utils.change_speed(mp3_path,mp3_path, 1.3)
        # return send_file(mp3_path, mimetype="audio/mpeg")
        return send_file(mp3_path, mimetype="audio/wav")
    return jsonify({"error": "No audio found"}), 404


@app.route("/youtube/widget/<url_encode>")
def youtube_widget(url_encode):
    url = utils.base64UrlDecode(url_encode)
    return render_template("youtube_widget.html", url = url)


## fb
@app.route("/facebook/check/<url_encode>", methods=["GET"])
@count_request
def check_is_live_stream_facebook(url_encode):
    url = utils.base64UrlDecode(url_encode)
    if not url:
        return jsonify({"error": "Missing url"}), 400
    check = get_feedback_id(url)
    if check != '':
        return jsonify({"message": f"Started Facebook client for {url}"}), 200
    return jsonify({"error": f"{url} not live"}), 400

@app.route("/facebook/start", methods=["POST"])
@count_request
def start_facebook():
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400

    start_client_fb(username)
    utils.send_mess(username)
    return jsonify({"message": f"Started Facebook client for {username}"}), 200

@app.route("/facebook/comment/<url_encode>", methods=["POST"])
def get_comment_facebook(url_encode):
    reply = request.form.get("reply")

    url = utils.base64UrlDecode(url_encode)
    if not url:
        return jsonify({"error": "Missing username"}), 400

    has_new_comment = False

    comment = get_latest_comment_fb(url)
    audio_url = url_for('get_audio_facebook', url_encode=url_encode)
    filename = utils.convert_url_to_username(url) + ".wav"
    if comment:
        if url in old_comment_facebook.keys():
            if old_comment_facebook[url] != comment and comment != 'null':
                old_comment_facebook[url] = comment
                has_new_comment = True
        else:
            old_comment_facebook[url] = comment

        if has_new_comment:
            with comment_lock_facebook:
                mp3_path = os.path.join(audio_dir_facebook, filename)
                # utils.save_speech(comment, mp3_path)
                if reply:
                    name = utils.cut_string_head(comment, ' : ')
                    content = utils.cut_string_last(comment, ' : ')
                    # try:
                    #     result_ai = ai.copilot(name, content)
                    # except:
                    #     result_ai = ai.process_v2(name, content)
                    try:
                        result_ai = ai.process_v2(name, content)
                    except:
                        result_ai = ''
                    answer = comment + " . . . " + result_ai
                    utils.save_speech(answer, mp3_path)
                else:
                    utils.save_speech(comment, mp3_path)
        else:
            comment = old_comment_facebook[url]

    return jsonify({"username": url, "latest_comment": comment, "audio_url": audio_url})

@app.route("/facebook/comment/widget/<url_encode>")
def get_comment_widget_facebook(url_encode):
    url = utils.base64UrlDecode(url_encode)
    try:
        comment = lastest_comments_facebook[url]
        return jsonify({"username": url, "latest_comment": comment, "audio_url": ''})
    except:
        return jsonify({"username": url, "latest_comment": 'Đang khởi tạo'})
@app.route("/facebook/audio/<url_encode>")
def get_audio_facebook(url_encode):
    url = utils.base64UrlDecode(url_encode)
    filename = utils.convert_url_to_username(url) + ".wav"
    mp3_path = os.path.join(audio_dir_facebook, filename)
    if os.path.exists(mp3_path):
        utils.change_speed(mp3_path,mp3_path, 1.3)
        return send_file(mp3_path, mimetype="audio/wav")
    return jsonify({"error": "No audio found"}), 404

@app.route("/facebook/widget/<url_encode>")
def facebook_widget(url_encode):
    url = utils.base64UrlDecode(url_encode)
    return render_template("facebook_widget.html", url = url)

if __name__ == "__main__":
    start_cleanup_thread()
    start_cleanup_thread_yt()
    start_cleanup_thread_fb()
    app.run(debug=True, host='0.0.0.0', port=80)
