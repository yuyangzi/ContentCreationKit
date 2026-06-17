# API Configuration

## Stock Asset Search API Keys

Set as environment variables before running `fetch_assets.py`. All optional — the search gracefully degrades when keys are unset.

| Variable | Service | Free Tier | Get Key |
|---|---|---|---|
| `PEXELS_API_KEY` | Pexels | 200 req/hr | https://www.pexels.com/api/ |
| `PIXABAY_API_KEY` | Pixabay | 5000 req/hr | https://pixabay.com/api/docs/ |
| `UNSPLASH_ACCESS_KEY` | Unsplash | 50 req/hr | https://unsplash.com/developers |

Layer 3 (Bing image scraping) needs no API key but is brittle — Bing periodically changes HTML structure. The script retries 3× with 2s/5s backoff and emits a structured warning on stderr when `murl` regex yields 0 matches.

### Setting keys

```bash
# Temporary (current shell only)
export PEXELS_API_KEY="your-key"
export PIXABAY_API_KEY="your-key"
export UNSPLASH_ACCESS_KEY="your-key"

# Persistent (add to ~/.bashrc, ~/.zshrc, or project .env)
echo 'export PEXELS_API_KEY="your-key"' >> ~/.bashrc
```

### Search layer fallback behavior

Without any keys set and Bing blocked, `fetch_assets.py` emits:
```
⚠️ [search_all_layers] ZERO results for keywords '...'. Check: PEXELS_API_KEY, ...
```

The downstream `scenes_with_assets.json` will have empty `data.media` arrays. Remotion templates must handle the no-asset case gracefully (render gradient/color background instead).

## Edge-TTS Voice

Edge-TTS is free, requires **no API key**, and uses Microsoft Azure Speech Service under the hood.

### List all voices

```bash
.opencode/skills/video-generate/.venv/bin/python -m edge_tts --list-voices
```

### Common Chinese voices

| Voice ID | Gender | Style | Use case |
|---|---|---|---|
| `zh-CN-XiaoxiaoNeural` | Female | Warm, default | General narration (default) |
| `zh-CN-YunxiNeural` | Male | Conversational | Tech explainers |
| `zh-CN-YunjianNeural` | Male | News anchor | Formal tone |
| `zh-CN-XiaoyiNeural` | Female | Cheerful | Marketing / upbeat |

### Common English voices

| Voice ID | Gender | Style |
|---|---|---|
| `en-US-AriaNeural` | Female | General (default for EN) |
| `en-US-GuyNeural` | Male | News / professional |
| `en-GB-SoniaNeural` | Female | British accent |

### Voice selection tips

- Match voice to article tone: news → Yunjian, tutorial → Yunxi, marketing → Xiaoxiao
- For bilingual articles, stick with one voice for coherence
- Pass `--voice <ID>` to `generate_audio.py`

## System Packages

For `newspaper3k` (used in Layer 1 reference-link extraction):

```bash
# Ubuntu/Debian
sudo apt install libxml2-dev libxslt1-dev

# macOS
brew install libxml2 libxslt
```

`lxml` compiles native extensions. Missing headers cause cryptic C compiler errors during `pip install`.
