from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user, AnonymousUserMixin
import bcrypt
import sqlite3
import os
import json
import threading
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static')
app.secret_key = 'L3SuIlcCQcOvo4_13vL_FcpqNIHuUtQfnc6SoT7oyaIsxnCgpz4pHrcrShT3BlbkFJgKD8eNjxGKbKJh2bE7hfDJShBVE6ebLyU6wASkIweZIlam_BzHXznZKDIA'
CORS(app)

# 定義檔案名稱
POSTS_FILE = 'posts.txt'
LOG_FILE = 'log.txt'
IP_LOG_FILE = 'ip_log.json'

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 資料庫路徑
DATABASE = 'user.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

# 使用者類
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

class Guest(AnonymousUserMixin):
    def __init__(self):
        self.username = "訪客"

login_manager.anonymous_user = Guest

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM user WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        conn = get_db()
        cursor = conn.cursor()
        # 檢查使用者名稱是否已經存在
        cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('該使用者名稱已被註冊，請選擇其他名稱。')
            return redirect(url_for('register'))

        # 如果名稱不存在，繼續進行註冊
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        cursor.execute('INSERT INTO user (username, password, role) VALUES (?, ?, ?)', 
                       (username, hashed_password.decode('utf-8'), 'user'))
        conn.commit()
        conn.close()

        flash('註冊成功！請登入。')
        return redirect(url_for('login'))

    return render_template('register.html')


# 登入功能
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password FROM user WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
            user_obj = User(id=user[0], username=user[1])
            login_user(user_obj)
            return redirect(url_for('chat'))
        else:
            flash('無效的使用者名稱或密碼')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    if current_user.role == 'guest':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user WHERE id = ?', (current_user.id,))
        conn.commit()
        conn.close()

    logout_user()
    return redirect(url_for('login'))


class User(UserMixin):
    def __init__(self, id, username, role='user'):  # 預設 role 為 'user'
        self.id = id
        self.username = username
        self.role = role


# 訪客登入功能
@app.route('/guest_login')
def guest_login():
    # 生成唯一的訪客名稱
    guest_username = "訪客" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    conn = get_db()
    cursor = conn.cursor()
    
    # 插入臨時帳號到資料庫，密碼可以留空
    cursor.execute('INSERT INTO user (username, password, role) VALUES (?, ?, ?)', 
                   (guest_username, '', 'guest'))
    conn.commit()
    cursor.execute('SELECT id FROM user WHERE username = ?', (guest_username,))
    guest_id = cursor.fetchone()[0]
    conn.close()

    # 使用臨時帳號登入
    guest_user = User(id=guest_id, username=guest_username)
    login_user(guest_user, remember=False)

    return redirect(url_for('chat'))

# 首頁引導頁面
@app.route('/')
def index():
    return render_template('login.html')

# 聊天室頁面
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


# 初始化檔案
if not os.path.exists(POSTS_FILE):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        f.write("")

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("")

if not os.path.exists(IP_LOG_FILE):
    with open(IP_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

current_users = set()

def clean_up_guests():
    conn = get_db()
    cursor = conn.cursor()
    
    # 設定過期時間，例如 1 小時前
    expiry_time = datetime.now() - timedelta(hours=1)
    cursor.execute('DELETE FROM user WHERE role = "guest" AND created_at < ?', (expiry_time,))
    conn.commit()
    conn.close()

    # 每 1 小時執行一次清理
    threading.Timer(900, clean_up_guests).start()

# 啟動清理任務
clean_up_guests()

def save_ip_logs():
    global current_users
    with open(IP_LOG_FILE, 'r+', encoding='utf-8') as f:
        try:
            existing_logs = json.load(f)
            if not isinstance(existing_logs, list):
                existing_logs = []
        except json.JSONDecodeError:
            existing_logs = []
        
        new_logs = list(current_users - set(existing_logs))
        if new_logs:
            existing_logs.extend(new_logs)
            f.seek(0)
            json.dump(existing_logs, f, ensure_ascii=False, indent=4)
            f.truncate()

    threading.Timer(60, save_ip_logs).start()

@app.before_request
def before_request():
    client_ip = request.remote_addr
    if client_ip not in current_users:
        current_users.add(client_ip)
        print(f"Recorded IP: {client_ip}")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 服務靜態文件
@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# 聊天訊息相關功能
@app.route('/posts', methods=['GET'])
def get_posts():
    with open(POSTS_FILE, 'r', encoding='utf-8') as f:
        posts = f.read()
    return posts

@app.route('/post', methods=['POST'])
def post_message():
    message = request.data.decode('utf-8').strip()

    # Use current_user.username for the nickname
    nickname = current_user.username
    msg = message

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM user WHERE username = ?', (nickname,))
    user_role = cursor.fetchone()
    conn.close()

    if user_role and user_role[0] == 'admin':  # If admin, show red name
        formatted_message = f"<span style='color: red;'>{nickname}: {msg}</span>"
    else:
        formatted_message = f"{nickname}: {msg}"

    with open(POSTS_FILE, 'a', encoding='utf-8') as f:
        f.write(formatted_message + '\x1E')

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(formatted_message + '\n')

    return jsonify(success=True)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/clear', methods=['POST'])
def clear_messages():
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        f.write("")
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("")
    return jsonify(success=True, message="Chat cleared")

@app.route('/user_count', methods=['GET'])
def user_count():
    return jsonify(current_users=len(current_users))

if __name__ == '__main__':
    import logging
    from logging.handlers import RotatingFileHandler

    if not os.path.exists('logs'):
        os.makedirs('logs')

    file_handler = RotatingFileHandler('logs/flask.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask startup')

    save_ip_logs()
    app.run(debug=True, host='0.0.0.0', port=5001)
