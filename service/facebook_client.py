import requests
import threading
import time
import utils
latest_comments = {}
latest_actives = {}
lock = threading.Lock()

clients_threads = {}
clients_instances = {}  # Lưu client
client_loops = {}       # Lưu loop của client
clients_tasks = {}      # Lưu task chạy client.start()
stop_events = {}

def get_feedback_id(url):
    headers = {
        "authority": "www.facebook.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "vi-VN,vi;q=0.9",
        "cookie": "datr=qw40aPityb2Z1Dcn5DSFcumM; sb=qw40aDBni959088Tt4jVi2aI; wd=737x760; ps_l=1; ps_n=1",
        "dpr": "2",
        "priority": "u=0, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"135.0.7049.116\", \"Not-A.Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"135.0.7049.116\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "macOS",
        "sec-ch-ua-platform-version": "15.3.1",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "viewport-width": "737"
    }
    response = requests.get(url, headers=headers)
    feedback_id = utils.cut_string(response.text, ',"feedback":{"id":"', '"')
    if feedback_id == '':
        post_id = utils.cut_string(response.text, 'story_fbid%3D', '%26')
        feedback_id = utils.text_to_base64('feedback:'+post_id)
    return feedback_id
#
# def get_new_comment(post_url, feedback_id):
#     url = "https://www.facebook.com/api/graphql/"
#     headers = {
#         'authority': 'www.facebook.com',
#         'method': 'POST',
#         'path': '/api/graphql/',
#         'scheme': 'https',
#         'accept': '*/*',
#         'accept-language': 'vi-VN,vi;q=0.9',
#         'content-length': '2229',
#         'content-type': 'application/x-www-form-urlencoded',
#         # 'cookie': 'datr=qw40aPityb2Z1Dcn5DSFcumM; sb=qw40aDBni959088Tt4jVi2aI; wd=1113x760',
#         'origin': 'https://www.facebook.com',
#         'priority': 'u=1, i',
#         # 'referer': 'https://www.facebook.com/phimtruongtvt/videos/676349631968827/',
#         'sec-ch-prefers-color-scheme': 'light',
#         'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
#         'sec-ch-ua-full-version-list': '"Google Chrome";v="135.0.7049.116", "Not-A.Brand";v="8.0.0.0", "Chromium";v="135.0.7049.116"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-model': '""',
#         'sec-ch-ua-platform': '"macOS"',
#         'sec-ch-ua-platform-version': '"15.3.1"',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-origin',
#         'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
#         'x-asbd-id': '359341',
#         'x-fb-friendly-name': 'CommentListComponentsRootQuery',
#         'x-fb-lsd': 'AVrcEwleAeM'
#     }
#     payload = {
#         'av': '0',
#         '__aaid': '0',
#         '__user': '0',
#         '__a': '1',
#         '__req': 'v',
#         # '__hs': '20234.HYP:comet_loggedout_pkg.2.1...0',
#         # 'dpr': '2',
#         # '__ccg': 'GOOD',
#         # '__rev': '1023185243',
#         # '__s': 'pdow8k:2561i2:m7kjpo',
#         # '__hsi': '7508643256989200318',
#         # '__dyn': '7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q322aew9G2S0zU20xi3y4o11U1lVE4W0qafw9q0yE462mcwfG12wOx62G3i0Bo7O2l0Fwqob82kw9O1lwlE-U2exi4UaEW0Lobrwh8lw8Xxmu3W3q1OBwxw4BwWwLyES0QEcU2ZwhEa8dUcobUak0KU566E6C13G1-wkEaFqwIxW1owmU3ywo8',
#         # '__csr': 'g8AndfdfEuxIQyA8xh5h7YKQRdriaKh99biFQmm8AlrG8jKepHBRGHG-mp2VWDnhBrQ4UG8KQLAyEF4iHAhkXG9nhUgAuql5x6-XGi6qyeqcglyF9k4edFeEC4oJ124FUCbzU-F8GESby-6rw6am0sW1Xw4Nw4byo0Ci0uC0JU0zG04XSnc0caw4JxD_w4GxN059U7Omam0qK05kEtU9olxC0IQ0jC08AweW0j20gi1YwEQu6l_U0gby4U1G9ES4pE0_201Thg0i0g7qcw0FkWg0o9a0bDe0mi3m3oaj3FO1y8F0o8rwES3iy0qUeE2CwNwOxgVU7S9y20eC2i0qC5yk3t0SwmEBjwso0Qa2K0y84e2xo3bwam0Eofywae1GwVpb_BL81VwmBwhU2Eo6q0LQ2i0OC0CU10Uc81EU760V85u3-1cyEJ3sk0ZU1U81e82Owp8vwSyk4A4Q1NK4oK1exK2le6EswZw9xhd0gUHh2Axq13wqpoqwyx_9UTBoa84K6o5u2KhS7FywiV898OezU1sU3nxml381FoS0qe3uEaEro4yayC0VVyw2FV3Q1uho5S1QwiEpwoUgU4C0z842m0zO0i8bo2G6hm6WgCc7AOwlUlwh6m7_9AgBgFouy203X-1Aa0tK0bBw1-208wyU2zxK0d8Ag5S04N41BwTxq0jG2i0nGewpo0P60oa7F84-0No7CkMYe2gw6-0kCU3yw-osg0BW0TEbo2dw2TEkxC885Arw6nws8twXHwEg3mwbO2C9xm9xW13xy',
#         # '__hsdp': 'g-j4eYZgwzgqgV10zwg5H8F13mA6Eh4Mvzb29HgNdW3Ewc8xaj88aAsgU82wm22P38kzN8y4Abyonxvl0uoyq4Xg4Z2o8102nwlEpAzQ3UwB681tG3q6U9UW0EXws8KawHwFw4owdm0mi8U2xy8rxq3K6Ekw4ey8mw4Tw2uUOewko2EwXwEG12wbC1mw_Cw9KU17U3-w6HwsU',
#         # '__hblp': '0vo2wwVwlE4q5EkADCCxu3K1Vxi10BK0HEgxeQ3q2e0Uo2HwroeorxudUW0EXG1JyUGewgokAw43wbK6o1cEcoy0EUyez8mwXxG583vwDwCwfi3qbwcii0Wk0zUaEJ2UWew4DxGdF0god86u8yVU5y3-i1tyUcrw4vwnUrw8a48qwzxiaBglwGwRwWw-wgU6ubw',
#         # '__comet_req': '15',
#         # 'lsd': 'AVrcEwleAeM',
#         # 'jazoest': '21004',
#         # '__spin_r': '1023185243',
#         # '__spin_b': 'trunk',
#         # '__spin_t': '1748242242',
#         # '__crn': 'comet.fbweb.CometVideoHomeLOEVideoPermalinkRoute',
#         # 'fb_api_caller_class': 'RelayModern',
#         # 'fb_api_req_friendly_name': 'CommentListComponentsRootQuery',
#         'variables': '{"commentsIntentToken":"RECENT_ACTIVITY_INTENT_V1","feedLocation":"TAHOE","feedbackSource":41,"focusCommentID":null,"scale":2,"useDefaultActor":false,"id":"'+feedback_id+'","__relay_internal__pv__IsWorkUserrelayprovider":false}',
#         'server_timestamps': 'true',
#         'doc_id': '9732969490153950'
#     }
#     try:
#         response = requests.post(url, data=payload, headers=headers)
#         node = response.json()['data']['node']['comment_rendering_instance_for_feed_location']['comments']['edges'][0]['node']
#         author = node['author']['name']
#         comment = node['preferred_body']['text']
#         return author+' : '+comment
#     except:
#         return 'init'


def get_new_comment(post_url, feedback_id):
    url = "https://www.facebook.com/api/graphql/"
    headers = {
        "authority": "www.facebook.com",
        "method": "POST",
        "path": "/api/graphql/",
        "scheme": "https",
        "accept": "*/*",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "content-length": "1911",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": "datr=UKI4aNGoDKwOvTdqJJZ4GO_f; sb=UKI4aFeES_VYkka-XsgQ31dE; wd=1218x783",
        "origin": "https://www.facebook.com",
        "priority": "u=1, i",
        "referer": "https://www.facebook.com/phimtruongtvt/videos/1015017393697161/",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-full-version-list": '"Chromium";v="136.0.7103.114", "Google Chrome";v="136.0.7103.114", "Not.A/Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"12.0.0"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-asbd-id": "359341",
        "x-fb-friendly-name": "CommentListComponentsRootQuery",
        "x-fb-lsd": "AVplF2mIX1g"
    }

    payload = {
        "av": "0",
        "__aaid": "0",
        "__user": "0",
        "__a": "1",
        "__req": "o",
        "__hs": "20237.HYP:comet_loggedout_pkg.2.1...0",
        "dpr": "1",
        "__ccg": "EXCELLENT",
        "__rev": "1023299319",
        "__s": "2ck90n:gbsbmg:5tgmtq",
        "__hsi": "7509932523469720288",
        "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q322aew9G2S0zU20xi3y4o11U1lVE4W0qafw9q0yE462mcwfG12wOx62G3i0Bo7O2l0Fwqob82kw9O1lwlE-U2exi4UaEW0Lobrwh8lw8Xxm16wSwsFo8o19oeEbUGdwda3e0Lo4q2y3u362-2B0bK1hxG1FwgWwvE5a2GmEb8uwm85K0UE62",
        "__csr": "g9Qy6NdGAxcoBbdqHivmQBjEJehfAHF9QBmBViK4bhuhd4DK8DFaauUKnx14gGAtaqVUSqqdDAAAx2iHGaz8gGFGHKiAiEdei8h9aGqmeBxW4oOqXx24lh8-azVVRDDx22258yewIxe8w6Do1c40atwa6azo0OGl5hK6U9U3rw6Tw1wBw2X40j6686G5e0zuq0oPw2HE0ioKE6i1-U9EG6o0Pq0AE0w20zE886y2m04C7w5AwwxSmu00ZjUiw6qw2E454dyE2Ay7c0epw6nwJw2-U7a2qczoB07Ew6Dyk1KwfO0vG0bKwAw56G0agA81hwbC08qg6W1Egf8kxC6F3w8u0GoasE4C2yeiw6Qw8K0gi07EpS0Wpo0KKbw8Yw0mrylg0dGE29wDw5Xw2sV8rwiU7e0dfg3yg3dwj80ES5UC0YU0JO3W1Bw43c4o1ZU0w2dyE0Oy1Aw9O0yU0gbwiy07cwb2E2qxq",
        "__hsdp": "gg5fha4EuwL3Y2kU4QwCiu7pgay4Byxip6zz4oO643F26zmQawry6cewJADCx11JkUrDwiQEix-1fwC52U3gwM88xli161hwNixi6oG1Xw4qwY85A0Ho8U6W1kwv81hE1qUaoaE5a0nm1Xxa2C1rwzG7oc82Hw20o7W58jwmE2QwiofEbocQ0U8ow2n8jwWBw2mE6-",
        "__hblp": "0aW2C0wUkwtEb8ohECdx-0xU46441PxZa4E2gxG0oC3C58hxa1Xw4qyEaVopgO0E88U6i9wl87O0kq0lu4U5i0VE7a3m3y1Xxa2C1rwzG0-E6a0m10YwiawOUixe0xU3hwLBy8bk39w9ibUf83Jwzwwwt8O0MEhwZG6o6e1vxOdxy68aEtwbu7E6-",
        "__comet_req": "15",
        "lsd": "AVplF2mIX1g",
        "jazoest": "2913",
        "__spin_r": "1023299319",
        "__spin_b": "trunk",
        "__spin_t": "1748542423",
        "__crn": "comet.fbweb.CometVideoHomeLOEVideoPermalinkRoute",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "CommentListComponentsRootQuery",
        'variables': '{"commentsIntentToken":"RECENT_ACTIVITY_INTENT_V1","feedLocation":"TAHOE","feedbackSource":41,"focusCommentID":null,"scale":2,"useDefaultActor":false,"id":"'+feedback_id+'","__relay_internal__pv__IsWorkUserrelayprovider":false}',
        "server_timestamps": "true",
        "doc_id": "9732969490153950"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        # print(response.text)
        node = response.json()['data']['node']['comment_rendering_instance_for_feed_location']['comments']['edges'][0]['node']
        author = node['author']['name']
        comment = node['preferred_body']['text']
        return author+' : '+comment
    except:
        return 'init'

def start_client_fb(username):
    if username in clients_threads:
        return

    stop_event = threading.Event()
    stop_events[username] = stop_event  # Ghi lại để dùng khi cần dừng

    def run():
        feedback_id = get_feedback_id(username)
        old_cmt = ''
        while not stop_event.is_set():
            try:
                new_cmt = get_new_comment(username, feedback_id)
                if old_cmt != new_cmt:
                    old_cmt = new_cmt
                    with lock:
                        latest_comments[username] = new_cmt
                time.sleep(3)  # Tránh spam request
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


def get_latest_comment_fb(username):
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
        print(f"🛑 Tắt Facebook client cho {username} vì không hoạt động > {timeout_seconds}s")
        stop_client(username)

def start_cleanup_thread_fb(interval=25, timeout_seconds=60):
    def run():
        while True:
            cleanup_inactive_clients(timeout_seconds)
            time.sleep(interval)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# feedback_id = get_feedback_id("https://www.facebook.com/phimtruongtvt/videos/1015017393697161/")
# print(feedback_id)
# cmt = get_new_comment(feedback_id, feedback_id)
# print(cmt)
# u = 'https://www.facebook.com/share/v/1AQTUZJT9e/?mibextid=wwXIfr'
# f = get_feedback_id(u)
# print(f)