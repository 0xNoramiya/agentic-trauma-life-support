# ElevenLabs dub pipeline

Two scripts (EN and ID), one multilingual voice, two narration MP3s, two final video renders. Optionally dub the live-demo recording for the ID version through ElevenLabs' Dubbing API.

## What you provide

```bash
# Add to /home/kudaliar/hackathon/atls/.env (this file is gitignored):
ELEVENLABS_API_KEY=sk_...your_key_here...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM   # default: "Rachel" (multilingual). Override with whichever voice you pick.
```

The default voice ID `21m00Tcm4TlvDq8ikWAM` is "Rachel" — a clear, calm, multilingual voice. Other clinical-feeling multilingual options:

| Voice | Voice ID | Notes |
|---|---|---|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | calm, female, multilingual |
| Adam | `pNInz6obpgDQGcFmaJgB` | grounded, male, multilingual |
| Antoni | `ErXwobaYiN019PkySvjV` | warm, male, multilingual |
| Bella | `EXAVITQu4vr4xnSDxMaL` | soft, female, multilingual |

You can browse and audition more at <https://elevenlabs.io/app/voice-library>. Pick one voice and use it for **both** EN and ID renders so the brand stays consistent.

## Step 1 — generate EN narration

After you confirm `video/SCRIPT_EN.md` is final, I'll run:

```bash
python video/scripts/tts.py \
  --script video/SCRIPT_EN.md \
  --lang en \
  --voice "$ELEVENLABS_VOICE_ID" \
  --out video/audio/narration_en.mp3
```

The script (which I'll also write) does:
1. Parse `SCRIPT_EN.md`, extract narration blocks per scene (skipping the live-demo block).
2. Join them with the right timing offsets — each scene's audio starts at the scene's `data-start` time, with silence padding between blocks so the dialogue lands on the visual cue.
3. Send each block to ElevenLabs `POST /v1/text-to-speech/{voice_id}` with `model_id=eleven_multilingual_v2` (handles both EN and ID with the same voice) and `voice_settings={stability: 0.5, similarity_boost: 0.75, style: 0.15}` — clinical/calm tuning.
4. Concatenate into a single timeline-aligned MP3 written to `video/audio/narration_en.mp3`.

Cost estimate: ~184 words ≈ 1100 characters. ElevenLabs TTS is ~$0.30 per 1k chars on the Creator tier → **~$0.33 for the EN narration**. Negligible.

## Step 2 — generate ID narration

After you fill in `video/SCRIPT_ID.md` (correcting my draft):

```bash
python video/scripts/tts.py \
  --script video/SCRIPT_ID.md \
  --lang id \
  --voice "$ELEVENLABS_VOICE_ID" \
  --out video/audio/narration_id.mp3
```

Same voice, same parameters, same timing layout — just the ID text. Cost ~$0.40 (Indonesian tends to use slightly more characters than English for the same content).

## Step 3 (optional) — dub the live-demo recording for ID version

If you decide to dub your screen-capture audio for the ID render (instead of leaving it in EN or muting it), use ElevenLabs' Dubbing API:

```bash
curl -X POST https://api.elevenlabs.io/v1/dubbing \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -F "file=@video/live_demo.mp4" \
  -F "source_lang=en" \
  -F "target_lang=id" \
  -F "num_speakers=1" \
  -F "watermark=false"
```

The endpoint returns a `dubbing_id`. Poll status:

```bash
curl https://api.elevenlabs.io/v1/dubbing/$DUBBING_ID \
  -H "xi-api-key: $ELEVENLABS_API_KEY"
```

When `status: dubbed`, fetch:

```bash
curl https://api.elevenlabs.io/v1/dubbing/$DUBBING_ID/audio/id \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -o video/live_demo_id.mp4
```

Cost: charged in dubbing-minutes. ~80 s of dubbing = ~$0.30–0.50 depending on tier.

The Dubbing API does **not** preserve your original voice unless you pre-clone it (Voice Cloning, separate workflow). It uses a default ID voice. If you want the dubbed version to sound like *you*, you'd clone your voice first via ElevenLabs Voice Lab → use that voice ID in the Dubbing call. That's an extra ~$0 (free tier supports one instant voice clone) + ~10 min of you reading a sample paragraph.

**Recommendation:** for the hackathon submission, skip cloning. The dubbed scene-4 audio in ID will be a consistent multilingual voice (the same `ELEVENLABS_VOICE_ID` you use for narration, if you pass it as `target_voice_ids` in the dubbing call). Your screen-capture audio in EN keeps your real voice → that's the version judges hear.

## Step 4 — render

After both audio tracks exist:

```bash
# EN render — your live demo audio + EN HyperFrames narration
npx hyperframes render video/index.html \
  --audio video/audio/narration_en.mp3 \
  --output video/demo_en.mp4

# ID render — dubbed live demo audio + ID HyperFrames narration  
npx hyperframes render video/index.html \
  --audio video/audio/narration_id.mp3 \
  --live-demo-override video/live_demo_id.mp4 \
  --output video/demo_id.mp4
```

(The exact `hyperframes render` flags depend on the skill's CLI — I'll wire the right invocation when we get there. The key point: same composition, swap the audio + scene-4 video clip per language.)

## What I need from you to start

1. **API key** — paste into `.env` (or share it in chat; I'll add it to `.env` and the file's gitignored).
2. **Voice ID** — confirm one of the four above, or paste a different ID from the voice library.
3. **Sign-off on `SCRIPT_EN.md`** — read it aloud once; tell me if any wording feels wrong before I generate the audio.
4. **Decision on scene-4 ID audio** (a/b/c — see `docs/VIDEO_PLAN.md`).

Once those are in, I write the TTS script, generate `narration_en.mp3`, and we're at "ready to render" pending the live-demo recording drop-in.
