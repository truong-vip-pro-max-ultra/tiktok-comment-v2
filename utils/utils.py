from deep_translator import GoogleTranslator
import soundfile as sf
import scipy.signal as signal
import re
import asyncio
import edge_tts
import base64
import json
import re
def translate_text(text):
    return GoogleTranslator(source='auto', target='vi').translate(text)

def change_speed(input_file, output_file, speed_factor):
    # audio, sample_rate = sf.read(input_file)
    #
    # adjusted_audio = signal.resample(audio, int(len(audio) / speed_factor))
    #
    # sf.write(output_file, adjusted_audio, sample_rate)
    pass

def convert_url_to_username(url):
    url = re.sub(r'\W+', '', url)
    return url
def cut_string(string, start, end):
    try:
        return string.split(start)[1].split(end)[0]
    except:
        return ''

def cut_string_head(string, key):
    try:
        return string.split(key)[0]
    except:
        return ''
def cut_string_last(string, key):
    try:
        return string.split(key)[1]
    except:
        return ''

def save_speech(text: str, filename: str = "output.mp3", voice: str = "vi-VN-HoaiMyNeural"):
    async def _save():
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(filename)
    asyncio.run(_save())

def base64UrlDecode(encoded_url):
    try:
        padding = '=' * (-len(encoded_url) % 4)
        decoded_url = base64.urlsafe_b64decode(encoded_url + padding).decode()
        return decoded_url
    except:
        return ''
def fix_utf8(text):
    return text.encode('latin1').decode('utf-8')
def merge_text(input_data):
    lines = input_data.strip().splitlines()
    fixed_parts = []

    for line in lines:
        if line.startswith("data: "):
            try:
                obj = json.loads(line[6:])
                body = obj.get("body", "")
                fixed_parts.append(fix_utf8(body))
            except Exception as e:
                print("Lỗi xử lý:", e)
    return ''.join(fixed_parts)


def text_to_base64(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")