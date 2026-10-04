"""Step 1: pick an unseen verse, render a 1080x1080 image, write caption.txt and meta.json."""
import json, subprocess, textwrap, sys
import requests, arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

API = "https://ummahapi.com/api/quran/random?translation=en"
SIZE = 1080


def pick_verse():
    posted = json.load(open("posted.json"))
    for _ in range(20):
        d = requests.get(API, timeout=30).json()["data"]
        key = d["verse"]["verse_key"]
        if key not in posted:
            return {
                "key": key,
                "surah": d["surah"]["name_english"],
                "surah_translation": d["surah"]["name_translation"],
                "arabic": d["verse"]["arabic"],
                "english": d["verse"]["translations"]["sahih_international"],
            }, posted
    sys.exit("No unseen verse found")


def find_font(name):
    out = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True).stdout
    return out


def gradient():
    img = Image.new("RGB", (SIZE, SIZE))
    px = img.load()
    top, bottom = (12, 38, 51), (28, 92, 94)
    for y in range(SIZE):
        t = y / SIZE
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(SIZE):
            px[x, y] = c
    return img


def fit_arabic(draw, text, max_w, max_h):
    shaped = get_display(arabic_reshaper.reshape(text))
    path = find_font("Amiri") or find_font("Noto Naskh Arabic")
    for size in range(96, 36, -4):
        font = ImageFont.truetype(path, size)
        words, lines, line = shaped.split(" "), [], ""
        # shaped text is visually reversed; wrap on the logical text instead
        logical = text.split(" ")
        cur = []
        lines_logical = []
        for w in logical:
            test = " ".join(cur + [w])
            vis = get_display(arabic_reshaper.reshape(test))
            if draw.textlength(vis, font=font) <= max_w:
                cur.append(w)
            else:
                lines_logical.append(" ".join(cur)); cur = [w]
        lines_logical.append(" ".join(cur))
        h = len(lines_logical) * int(size * 1.7)
        if h <= max_h:
            return font, [get_display(arabic_reshaper.reshape(l)) for l in lines_logical], int(size * 1.7)
    return font, [get_display(arabic_reshaper.reshape(l)) for l in lines_logical], int(size * 1.7)


def render(v):
    img = gradient()
    d = ImageDraw.Draw(img)
    margin = 110
    ar_font, ar_lines, ar_lh = fit_arabic(d, v["arabic"], SIZE - 2 * margin, 430)
    en_font = ImageFont.truetype(find_font("DejaVu Sans") or find_font("sans"), 36)
    ref_font = ImageFont.truetype(find_font("DejaVu Sans") or find_font("sans"), 28)

    en_lines = textwrap.wrap(v["english"], 42)
    block_h = len(ar_lines) * ar_lh + 50 + len(en_lines) * 52 + 70
    y = (SIZE - block_h) // 2
    for l in ar_lines:
        w = d.textlength(l, font=ar_font)
        d.text(((SIZE - w) / 2, y), l, font=ar_font, fill=(255, 255, 255))
        y += ar_lh
    y += 50
    for l in en_lines:
        w = d.textlength(l, font=en_font)
        d.text(((SIZE - w) / 2, y), l, font=en_font, fill=(225, 238, 238))
        y += 52
    ref = f"Surah {v['surah']} {v['key']}"
    w = d.textlength(ref, font=ref_font)
    d.text(((SIZE - w) / 2, y + 30), ref, font=ref_font, fill=(190, 215, 215))
    path = f"images/{v['key'].replace(':', '_')}.png"
    img.save(path)
    return path


if __name__ == "__main__":
    v, posted = pick_verse()
    path = render(v)
    caption = (
        f"{v['english']}\n\n— Surah {v['surah']} ({v['surah_translation']}) {v['key']}\n\n"
        "Pause and reflect on this verse today.\n\n"
        "#Quran #QuranVerses #Islam #Muslim #Reminder #DailyReminder"
    )
    open("caption.txt", "w").write(caption)
    json.dump({"image_path": path, "key": v["key"]}, open("meta.json", "w"))
    posted.append(v["key"])
    json.dump(posted, open("posted.json", "w"))
    print("Rendered", path)
