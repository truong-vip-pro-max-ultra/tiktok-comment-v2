import requests
import threading
import time

latest_comments = {}
latest_actives = {}
lock = threading.Lock()

clients_threads = {}
clients_instances = {}  # Lưu client
client_loops = {}       # Lưu loop của client
clients_tasks = {}      # Lưu task chạy client.start()
stop_events = {}
class Comment:
    def __init__(self, comment_id, author, content):
        self.comment_id = comment_id
        self.author = author
        self.content = content


def cut_string(string, key, choice):
    index = string.find(key)
    if choice:
        string = string[index + len(key):]
    else:
        string = string[0:index]
    return string


def get_live_chat(url):
    key = '"continuation":{"reloadContinuationData":{"continuation":"'
    try:
        data = requests.get(url).text
        if key not in data:
            return ''
        data = cut_string(data, key, True)
        data = cut_string(data, '"', False)
        return 'https://www.youtube.com/live_chat?continuation=' + data
    except:
        return ''


def get_new_comment(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    data = requests.get(url, headers=headers).text
    arr_data = data.split('{"liveChatTextMessageRenderer":{"message":{"runs":[{"text":"')
    arr_data = arr_data[len(arr_data) - 1]

    content = cut_string(arr_data, '"', False)

    arr_data = cut_string(arr_data, '"authorName":{"simpleText":"', True)

    author = cut_string(arr_data, '"', False)

    arr_data = cut_string(arr_data, '"clientId":"', True)

    comment_id = cut_string(arr_data, '"', False)

    return Comment(comment_id, author, content)


def start_client_yt(username):
    if username in clients_threads:
        return

    stop_event = threading.Event()
    stop_events[username] = stop_event  # Ghi lại để dùng khi cần dừng

    def run():
        url_live_chat = get_live_chat(username)
        old_cmt_id = ''

        while not stop_event.is_set():
            try:
                new_cmt = get_new_comment(url_live_chat)
                if old_cmt_id != new_cmt.comment_id:
                    # print(f"[{username}] {new_cmt.author} : {new_cmt.content}")
                    old_cmt_id = new_cmt.comment_id
                    with lock:
                        latest_comments[username] = f"{new_cmt.author}: {new_cmt.content}"
                        # latest_actives[username] = time.time()
                time.sleep(1)  # Tránh spam request
            except Exception as e:
                print(f"⚠️ Lỗi trong client {username}: {e}")
                time.sleep(3)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    clients_threads[username] = thread

def stop_client(username):
    if username not in clients_threads:
        return

    print(f"🛑 Đang dừng client {username}...")

    # Báo dừng vòng lặp
    if username in stop_events:
        stop_events[username].set()
        stop_events.pop(username, None)

    # Đợi thread kết thúc nếu cần
    thread = clients_threads.pop(username, None)
    if thread:
        thread.join(timeout=3)

    # Cleanup
    clients_instances.pop(username, None)
    client_loops.pop(username, None)
    clients_tasks.pop(username, None)
    latest_comments.pop(username, None)
    latest_actives.pop(username, None)

    print(f"🛑 Dừng thành công client {username}")


def get_latest_comment_yt(username):
    with lock:
        latest_actives[username] = time.time()
        return latest_comments.get(username, "")

def cleanup_inactive_clients(timeout_seconds=10):
    now = time.time()
    to_stop = []

    with lock:
        for username in list(latest_actives.keys()):
            if now - latest_actives[username] > timeout_seconds:
                to_stop.append(username)

    for username in to_stop:
        print(f"🛑 Tắt Youtube client cho {username} vì không hoạt động > {timeout_seconds}s")
        stop_client(username)

def start_cleanup_thread_yt(interval=20, timeout_seconds=60):
    def run():
        while True:
            cleanup_inactive_clients(timeout_seconds)
            time.sleep(interval)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
