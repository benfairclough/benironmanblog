# app.py
import os
import json
import time
import tempfile
from flask import Flask, request, jsonify, send_from_directory, abort

POSTS_DIR = os.environ.get("POSTS_DIR", "/data")
POSTS_FILE = os.path.join(POSTS_DIR, "posts.json")

def ensure_posts_file():
    os.makedirs(POSTS_DIR, exist_ok=True)
    if not os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def read_posts():
    ensure_posts_file()
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def write_posts_atomic(posts):
    ensure_posts_file()
    data = json.dumps(posts, ensure_ascii=False, indent=2)
    dirpath = os.path.dirname(POSTS_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix="posts-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(data)
        os.replace(tmp_path, POSTS_FILE)
    finally:
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass

app = Flask(__name__, static_folder="public", static_url_path="")

@app.route("/api/posts", methods=["GET"])
def api_get_posts():
    posts = read_posts()
    return jsonify(posts)

@app.route("/api/posts", methods=["POST"])
def api_create_post():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title or not body:
        return jsonify({"error": "title and body required"}), 400
    posts = read_posts()
    post = {
        "id": str(int(time.time() * 1000)),
        "title": title,
        "body": body,
        "created": int(time.time() * 1000),
        "comments": []
    }
    posts.append(post)
    write_posts_atomic(posts)
    return jsonify(post), 201

@app.route("/api/posts/<post_id>/comments", methods=["POST"])
def api_create_comment(post_id):
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    name = (data.get("name") or "Anonymous").strip()
    if not text:
        return jsonify({"error": "comment text required"}), 400
    posts = read_posts()
    for p in posts:
        if str(p.get("id")) == str(post_id):
            comment = {"name": name or "Anonymous", "text": text, "when": int(time.time() * 1000)}
            p.setdefault("comments", []).append(comment)
            write_posts_atomic(posts)
            return jsonify(p), 201
    return jsonify({"error": "post not found"}), 404

# Serve static files (index.html and assets) from public/
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def static_proxy(path):
    if path == "" or not os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, "index.html")
    return send_from_directory(app.static_folder, path)

# Simple health check
@app.route("/health")
def health():
    return jsonify({"ok": True})
