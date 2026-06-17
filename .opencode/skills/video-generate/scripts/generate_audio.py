#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import re
import sys


async def generate_voice(text: str, voice: str, output_path: str, srt_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    sub_maker = edge_tts.SubMaker()
    with open(output_path, 'wb') as mp3_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                sub_maker.feed(chunk)
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(sub_maker.get_srt())
    return sub_maker


RETRY_DELAYS = [5, 15, 45]
MAX_RETRIES = 3


async def generate_voice_with_retry(text: str, voice: str, output_path: str, srt_path: str):
    for attempt in range(MAX_RETRIES):
        try:
            return await generate_voice(text, voice, output_path, srt_path)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_DELAYS[attempt]
            print(f"⚠️ Edge-TTS attempt {attempt + 1} failed: {e}. "
                  f"Retrying in {delay}s...", file=sys.stderr)
            await asyncio.sleep(delay)


def parse_srt_timestamps(srt_path: str):
    entries = []
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        ts_match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', lines[1])
        if not ts_match:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, ts_match.groups())
        start_ms = ((h1 * 3600 + m1 * 60 + s1) * 1000) + ms1
        end_ms = ((h2 * 3600 + m2 * 60 + s2) * 1000) + ms2
        text = '\n'.join(lines[2:]).strip()
        entries.append({'text': text, 'start_ms': start_ms, 'end_ms': end_ms})
    return entries


def match_scene_timestamps(scenes: list, srt_entries: list, full_text: str):
    if not scenes or not srt_entries:
        return

    scene_ends = []
    pos = 0
    for scene in scenes:
        pos += len(scene["narration"]["text"])
        scene_ends.append(pos)

    srt_idx = 0
    for i, end_pos in enumerate(scene_ends):
        nar = scenes[i]["narration"]
        prev_end = scene_ends[i - 1] if i > 0 else 0
        scene_char_len = end_pos - prev_end

        if srt_idx < len(srt_entries):
            nar["voice_start_ms"] = srt_entries[srt_idx]["start_ms"]
        else:
            nar["voice_start_ms"] = 0
            nar["voice_end_ms"] = 0
            continue

        consumed = 0
        while srt_idx < len(srt_entries) and consumed < scene_char_len:
            consumed += len(srt_entries[srt_idx]["text"])
            if consumed >= scene_char_len:
                nar["voice_end_ms"] = srt_entries[srt_idx]["end_ms"]
            srt_idx += 1

        if consumed < scene_char_len and srt_entries:
            nar["voice_end_ms"] = srt_entries[-1]["end_ms"]


def build_word_timestamps(srt_entries: list, full_text: str):
    words = []
    for entry in srt_entries:
        text = entry["text"]
        words.append({
            "word": text,
            "start_ms": entry["start_ms"],
            "end_ms": entry["end_ms"]
        })
    return words


async def main_async(scenes_path: str, outdir: str, voice: str):
    with open(scenes_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    full_text = "".join(s["narration"]["text"] for s in data["scenes"])

    voice_path = os.path.join(outdir, "voice.mp3")
    srt_path = os.path.join(outdir, "temp.srt")

    sub_maker = await generate_voice_with_retry(full_text, voice, voice_path, srt_path)

    srt_entries = parse_srt_timestamps(srt_path)
    if not srt_entries:
        print("⚠️ Warning: SRT parsing returned 0 entries. "
              "Edge-TTS may have produced non-standard timestamp format.",
              file=sys.stderr)

    match_scene_timestamps(data["scenes"], srt_entries, full_text)

    word_ts = build_word_timestamps(srt_entries, full_text)

    scene_boundaries = []
    cumulative = 0
    for scene in data["scenes"]:
        cumulative += len(scene["narration"]["text"])
        scene_boundaries.append(cumulative)

    scene_words_map = {i: [] for i in range(len(data["scenes"]))}
    scene_idx = 0
    chars_in_srt = 0
    for w in word_ts:
        entry_len = len(w["word"])
        while scene_idx < len(scene_boundaries) - 1 and chars_in_srt >= scene_boundaries[scene_idx]:
            scene_idx += 1
        scene_words_map[scene_idx].append(w)
        chars_in_srt += entry_len

    for i, scene in enumerate(data["scenes"]):
        scene["narration"]["timestamps"] = scene_words_map[i]

    if srt_entries:
        data["meta"]["total_duration_ms"] = srt_entries[-1]["end_ms"]
        data["meta"]["total_duration_seconds"] = round(srt_entries[-1]["end_ms"] / 1000)
        data["meta"]["total_duration_frames"] = int(srt_entries[-1]["end_ms"] * data["meta"]["fps"] / 1000)

    MIN_DURATION_FRAMES = 30
    total_frames = data["meta"]["total_duration_frames"]
    char_lens = [len(scene["narration"]["text"]) for scene in data["scenes"]]
    total_chars = sum(char_lens)
    if total_chars > 0:
        accumulated = 0
        for i, scene in enumerate(data["scenes"]):
            if i == len(data["scenes"]) - 1:
                scene["duration_frames"] = max(
                    MIN_DURATION_FRAMES, total_frames - accumulated
                )
            else:
                scene["duration_frames"] = max(
                    MIN_DURATION_FRAMES,
                    int(total_frames * char_lens[i] / total_chars)
                )
                accumulated += scene["duration_frames"]

    ts_path = os.path.join(outdir, "timestamps.json")
    complete_path = os.path.join(outdir, "scenes_complete.json")
    with open(ts_path, 'w', encoding='utf-8') as f:
        json.dump(word_ts, f, ensure_ascii=False)
    with open(complete_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.remove(srt_path)
    print(f"✅ voice.mp3 → {voice_path}")
    print(f"✅ timestamps.json → {ts_path}")
    print(f"✅ scenes_complete.json → {complete_path}")
    print(f"   Duration: {data['meta']['total_duration_seconds']}s")


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio from scenes.json")
    parser.add_argument("scenes_path", help="Path to scenes.json")
    parser.add_argument("--outdir", default=None,
                       help="Output directory (default: same dir as scenes.json)")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural",
                       help="Edge-TTS voice name (default: zh-CN-XiaoxiaoNeural)")
    args = parser.parse_args()

    if args.outdir is None:
        args.outdir = os.path.dirname(os.path.abspath(args.scenes_path))
    os.makedirs(args.outdir, exist_ok=True)

    asyncio.run(main_async(args.scenes_path, args.outdir, args.voice))


if __name__ == "__main__":
    main()