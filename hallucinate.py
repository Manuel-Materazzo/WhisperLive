import json
import os
import sys
import pysrt

from whisper_live.client import TranscriptionClient

LANG_LIST = ["ha", "uk", "et", "fr", "vi", "ps", "ca", "as", "ms", "gu", "fa", "km", "bs", "am", "sq", "nl", "uz", "is",
             "ht", "su", "my", "gl", "sn", "lb", "mt", "hu", "no", "sa", "ln", "kk", "sv", "ru", "ml", "fi", "mn", "ja",
             "yi", "id", "ar", "mg", "cs", "fo", "te", "es", "sl", "mk", "si", "cy", "he", "ne", "pt", "kn", "bg", "la",
             "tr", "hr", "af", "lv", "de", "el", "hy", "nn", "bn", "hi", "tg", "ur", "sw", "ba", "tt", "mi", "it", "br",
             "jw", "pl", "eu", "mr", "so", "th", "haw", "ka", "oc", "en", "pa", "ko", "ta", "yue", "bo", "lo", "sd",
             "ro", "az", "lt", "yo", "be", "sk", "da", "tl", "sr", "zh", "tk"]

HALLUCINATIONS = {}

# for each supported language
for lang in LANG_LIST:
    try:
        # do a STT on empty audio
        hallucination_client = TranscriptionClient(
            "localhost",
            9090,
            lang=lang,
            translate=False,
            model="small",
            use_vad=False,
            save_output_recording=False
        )
        hallucination_client("assets/empty.mp3")

        # parse the srt file to extract hallucinations
        subs = pysrt.open("output.srt", 'utf-8')
        subs_text = []
        for sub in subs:
            subs_text.append(sub.text)

        HALLUCINATIONS[lang] = subs_text
        print(f"{lang}: {subs_text}")
    except Exception as e:
        print(f"{lang} Error: {e}")

print("Detected Hallucinations:")
print(HALLUCINATIONS)

# write an hallucinations file
with open("hallucinations.json", 'w', encoding="utf-8") as out_file:
    json.dump(HALLUCINATIONS, out_file, indent=2, ensure_ascii=False)
