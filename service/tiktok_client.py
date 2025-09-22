from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, LikeEvent, GiftEvent
import threading
import asyncio
import random
import time
import utils
import re
import requests

latest_comments = {}
latest_actives = {}
enable_likes = {}
enable_comments = {}
enable_gifts = {}


lock = threading.Lock()

clients_threads = {}
clients_instances = {}  # Lưu client
client_loops = {}       # Lưu loop của client
clients_tasks = {}      # Lưu task chạy client.start()

love = ['yêu lắm luôn', 'moa moa moa', 'dễ thương quá trời ơi', 'cảm ơn rất nhiều', 'ôi trời ơi']

# def is_live_stream(username):
async def is_live_stream(username):
    client = TikTokLiveClient(unique_id=username)
    try:
        return await client.is_live()
    except:
        return False
    # headers = {
    #     "authority": "www.tiktok.com",
    #     "method": "GET",
    #     "scheme": "https",
    #     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    #     "priority": "u=0, i",
    #     "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-ch-ua-platform": '"macOS"',
    #     "sec-fetch-dest": "document",
    #     "sec-fetch-mode": "navigate",
    #     "sec-fetch-site": "none",
    #     "sec-fetch-user": "?1",
    #     "upgrade-insecure-requests": "1",
    #     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    # }
    # url = f'https://www.tiktok.com/@{username.replace("@","")}/live'
    # res = requests.get(url, headers=headers)
    # match = re.search(r'"roomId":"(\d+)"', res.text)
    # return match.group(1) if match else None

def start_client(username):
    if username in clients_threads:
        return

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client = TikTokLiveClient(unique_id=username)
        clients_instances[username] = client
        client_loops[username] = loop

        @client.on(ConnectEvent)
        async def on_connect(event):
            enable_likes[username] = True
            enable_comments[username] = True
            enable_gifts[username] = True

            print(f"✅ Kết nối tới @{username} (Room ID: {client.room_id})")

        @client.on(CommentEvent)
        async def on_comment(event):
            comment = event.comment
            with lock:
                if enable_comments[username]:
                    latest_comments[username] = f"{event.user.nickname} : {comment}"

        @client.on(LikeEvent)
        async def on_like(event):
            with lock:
                if enable_likes[username]:
                    latest_comments[username] = f"Cảm ơn {event.user.nickname} : đã thả tim!"

        @client.on(GiftEvent)
        async def on_gift(event):
            with lock:
                if enable_gifts[username]:
                    latest_comments[username] = f"Cảm ơn {event.user.nickname} đã tặng {utils.translate_text(event.gift.name)} cho mình ạ ..... {random.choice(love)}"

        async def main_task():
            try:
                await client.start()
            except Exception as e:
                print(f"❌ Lỗi ở client {username}: {e}")

        task = loop.create_task(main_task())
        clients_tasks[username] = task

        try:
            loop.run_forever()
        finally:
            loop.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    clients_threads[username] = thread

def stop_client(username):
    if username not in clients_instances:
        return

    client = clients_instances[username]
    loop = client_loops.get(username)

    if loop and client:
        print(f"🛑 Đang dừng client @{username}...")

        try:
            future = asyncio.run_coroutine_threadsafe(client.close(), loop)
            future.result(timeout=3)
        except Exception as e:
            # print(f"⚠️ Dừng client @{username} lỗi: {e}")
            pass
        # Dừng loop
        loop.call_soon_threadsafe(loop.stop)

    # Cleanup
    clients_instances.pop(username, None)
    clients_threads.pop(username, None)
    clients_tasks.pop(username, None)
    client_loops.pop(username, None)
    latest_comments.pop(username, None)
    latest_actives.pop(username, None)

def get_latest_comment(username):
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
        print(f"🛑 Tắt TikTok client cho @{username} vì không hoạt động > {timeout_seconds}s")
        stop_client(username)

def start_cleanup_thread(interval=15, timeout_seconds=60):
    def run():
        while True:
            cleanup_inactive_clients(timeout_seconds)
            time.sleep(interval)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
