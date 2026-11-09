import http.server
import socketserver
import urllib.request
import urllib.parse
import os
import json
import time
import sqlite3
import shutil
import hashlib
import subprocess
import wave
import io
import base64
import uuid
import numpy as np

PORT = 8080
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'sms_data.json')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
SQLITE_BACKUP_DIR = os.path.join(DATA_DIR, 'backups', 'sqlite_db')
SQLITE_MASTER_FILE = os.path.join(DATA_DIR, 'sms_cambodia.db')
SQLITE_DATABASE_FILE = os.path.join(DATA_DIR, 'sms_database.db')
TTS_CACHE_DIR = os.path.join(DATA_DIR, 'tts_cache')
VOICE_TEMPLATES_FILE = os.path.join(DATA_DIR, 'voice_templates.json')
AI_STT_CONFIG_FILE = os.path.join(DATA_DIR, 'ai_stt_config.json')

KHMER_NUMBER_PROMPT = (
    "ពិន្ទុប្រឡង៖ សូន្យ មួយ ពីរ បី បួន ប្រាំ ប្រាំមួយ ប្រាំពីរ ប្រាំបី ប្រាំបួន "
    "ដប់ ម្ភៃ សាមសិប សាមសិបប្រាំ សាមសិបប្រាំបី សាមសិបប្រាំបួន សែសិប សែសិបប្រាំ "
    "ហាសិប ហុកសិប ចិតសិប ប៉ែតសិប កៅសិប មួយរយ កន្លះ អេ A 0 1 2 3 4 5 6 7 8 9 "
    "10 20 25 30 35 37 38 39 40 42 45 48 49 50"
)

KHMER_SPEECH_PHRASES = [
    "សូន្យ", "អេ", "មួយ", "ពីរ", "បី", "បួន", "ប្រាំ", "ប្រាំមួយ", "ប្រាំពីរ", "ប្រាំបី", "ប្រាំបួន",
    "ដប់", "ដប់មួយ", "ដប់ពីរ", "ដប់បី", "ដប់បួន", "ដប់ប្រាំ", "ដប់ប្រាំមួយ", "ដប់ប្រាំពីរ", "ដប់ប្រាំបី", "ដប់ប្រាំបួន",
    "ម្ភៃ", "ម្ភៃមួយ", "ម្ភៃពីរ", "ម្ភៃបី", "ម្ភៃបួន", "ម្ភៃប្រាំ", "ម្ភៃប្រាំមួយ", "ម្ភៃប្រាំពីរ", "ម្ភៃប្រាំបី", "ម្ភៃប្រាំបួន",
    "សាមសិប", "សាមសិបមួយ", "សាមសិបពីរ", "សាមសិបបី", "សាមសិបបួន", "សាមសិបប្រាំ", "សាមសិបប្រាំមួយ", "សាមសិបប្រាំពីរ", "សាមសិបប្រាំបី", "សាមសិបប្រាំបួន",
    "សែសិប", "សែសិបមួយ", "សែសិបពីរ", "សែសិបបី", "សែសិបបួន", "សែសិបប្រាំ", "សែសិបប្រាំមួយ", "សែសិបប្រាំពីរ", "សែសិបប្រាំបី", "សែសិបប្រាំបួន",
    "ហាសិប", "ហុកសិប", "ចិតសិប", "ប៉ែតសិប", "កៅសិប", "មួយរយ", "កន្លះ", "ពេញ", "រក្សាទុក", "បន្ទាប់", "ថយក្រោយ", "លុប"
]

_AI_STT_CONFIG_CACHE = None
_LOCAL_WHISPER_MODEL = None

def load_ai_stt_config():
    global _AI_STT_CONFIG_CACHE
    if _AI_STT_CONFIG_CACHE is not None:
        return _AI_STT_CONFIG_CACHE
    default_cfg = {
        "engine": "hybrid",  # "hybrid" | "whisper_api" | "google_cloud" | "local_whisper" | "offline"
        "whisperProvider": "groq",  # "groq" (whisper-large-v3) or "openai" (whisper-1)
        "whisperModel": "whisper-large-v3",
        "openaiApiKey": os.environ.get("OPENAI_API_KEY", ""),
        "groqApiKey": os.environ.get("GROQ_API_KEY", ""),
        "googleApiKey": os.environ.get("GOOGLE_SPEECH_API_KEY", "")
    }
    if os.path.exists(AI_STT_CONFIG_FILE):
        try:
            with open(AI_STT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    default_cfg.update(saved)
        except Exception:
            pass
    _AI_STT_CONFIG_CACHE = default_cfg
    return _AI_STT_CONFIG_CACHE

def save_ai_stt_config(new_cfg):
    global _AI_STT_CONFIG_CACHE
    cfg = load_ai_stt_config().copy()
    if isinstance(new_cfg, dict):
        cfg.update(new_cfg)
    _AI_STT_CONFIG_CACHE = cfg
    try:
        with open(AI_STT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return cfg

def samples_to_wav_bytes(samples, sr=16000):
    arr = np.asarray(samples, dtype=np.float32)
    arr = arr - np.mean(arr)
    peak = float(np.max(np.abs(arr))) if len(arr) > 0 else 0.0
    if peak > 0.01:
        arr = np.clip(arr / peak * 0.92, -1.0, 1.0)
    pcm16 = (arr * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sr))
        wf.writeframes(pcm16.tobytes())
    return buf.getvalue(), pcm16.tobytes()

def audio_blob_to_wav_bytes(audio_bytes, ext='webm', target_sr=16000):
    """Converts a browser-recorded WebM/WAV/OGG audio blob into 16kHz 16-bit mono WAV using macOS afconvert or ffmpeg."""
    if len(audio_bytes) >= 44 and audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                if wf.getnchannels() == 1 and wf.getsampwidth() == 2 and wf.getframerate() == target_sr:
                    pcm_bytes = wf.readframes(wf.getnframes())
                    samples = (np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0).tolist()
                    return audio_bytes, pcm_bytes, samples
        except Exception:
            pass
    tmp_id = uuid.uuid4().hex[:10]
    in_path = os.path.join('/tmp', f'sms_stt_{tmp_id}.{ext}')
    out_path = os.path.join('/tmp', f'sms_stt_{tmp_id}.wav')
    try:
        with open(in_path, 'wb') as f:
            f.write(audio_bytes)
        for cmd in [
            ['/usr/bin/afconvert', '-f', 'WAVE', '-d', f'LEI16@{target_sr}', '-c', '1', in_path, out_path],
            ['ffmpeg', '-y', '-i', in_path, '-ar', str(target_sr), '-ac', '1', '-f', 'wav', out_path]
        ]:
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                    break
            except Exception:
                pass
        if os.path.exists(out_path):
            with open(out_path, 'rb') as rf:
                wav_bytes = rf.read()
            with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                pcm_bytes = wf.readframes(wf.getnframes())
            samples = (np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0).tolist()
            return wav_bytes, pcm_bytes, samples
    finally:
        for p in (in_path, out_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
    return b'', b'', []

def transcribe_with_whisper_api(wav_bytes, cfg):
    """Calls OpenAI Whisper (whisper-1) or Groq Whisper (whisper-large-v3) via multipart/form-data."""
    provider = cfg.get('whisperProvider', 'groq')
    groq_key = (cfg.get('groqApiKey') or '').strip()
    openai_key = (cfg.get('openaiApiKey') or '').strip()

    if provider == 'groq' and groq_key:
        api_url = 'https://api.groq.com/openai/v1/audio/transcriptions'
        api_key = groq_key
        model = cfg.get('whisperModel') or 'whisper-large-v3'
    elif openai_key:
        api_url = 'https://api.openai.com/v1/audio/transcriptions'
        api_key = openai_key
        model = 'whisper-1'
    elif groq_key:
        api_url = 'https://api.groq.com/openai/v1/audio/transcriptions'
        api_key = groq_key
        model = 'whisper-large-v3'
    else:
        return None, 'no_whisper_api_key'

    boundary = '----SMSWhisperBoundary' + uuid.uuid4().hex
    parts = []
    def add_field(name, val):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode('utf-8'))

    add_field('model', model)
    add_field('language', 'km')
    add_field('temperature', '0')
    add_field('response_format', 'json')
    add_field('prompt', KHMER_NUMBER_PROMPT)

    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="score.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode('utf-8')
        + wav_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    )
    body = b''.join(parts)
    req = urllib.request.Request(api_url, data=body, method='POST', headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': 'SMS-Cambodia-VoiceEngine/1.0'
    })
    with urllib.request.urlopen(req, timeout=6) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        text = (data.get('text') or '').strip()
        if text:
            return [text], f'whisper_api:{model}'
    return None, 'empty_whisper_response'

def transcribe_with_local_whisper(wav_bytes):
    """Runs local Whisper (mlx_whisper / faster_whisper / whisper) if installed on the server."""
    global _LOCAL_WHISPER_MODEL
    tmp_wav = os.path.join('/tmp', f'sms_local_whisper_{uuid.uuid4().hex[:8]}.wav')
    try:
        with open(tmp_wav, 'wb') as f:
            f.write(wav_bytes)
        try:
            import mlx_whisper
            res = mlx_whisper.transcribe(tmp_wav, language='km', initial_prompt=KHMER_NUMBER_PROMPT)
            txt = (res.get('text') or '').strip()
            if txt:
                return [txt], 'local_mlx_whisper'
        except ImportError:
            pass
        try:
            from faster_whisper import WhisperModel
            if _LOCAL_WHISPER_MODEL is None:
                _LOCAL_WHISPER_MODEL = WhisperModel('medium', device='auto', compute_type='int8')
            segments, _ = _LOCAL_WHISPER_MODEL.transcribe(tmp_wav, language='km', initial_prompt=KHMER_NUMBER_PROMPT, beam_size=5)
            txt = ' '.join(seg.text for seg in segments).strip()
            if txt:
                return [txt], 'local_faster_whisper'
        except ImportError:
            pass
        try:
            import whisper
            if _LOCAL_WHISPER_MODEL is None:
                _LOCAL_WHISPER_MODEL = whisper.load_model('base')
            res = _LOCAL_WHISPER_MODEL.transcribe(tmp_wav, language='km', initial_prompt=KHMER_NUMBER_PROMPT)
            txt = (res.get('text') or '').strip()
            if txt:
                return [txt], 'local_openai_whisper'
        except ImportError:
            pass
    except Exception:
        pass
    finally:
        try:
            if os.path.exists(tmp_wav):
                os.remove(tmp_wav)
        except Exception:
            pass
    return None, 'local_whisper_unavailable'

def transcribe_with_google_cloud_stt(pcm_bytes, sr=16000, api_key=''):
    """Calls Google Cloud Speech-to-Text API (km-KH) with Khmer number speechContexts boost."""
    api_key = (api_key or '').strip()
    if api_key:
        url = f'https://speech.googleapis.com/v1/speech:recognize?key={urllib.parse.quote(api_key)}'
        payload = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": int(sr),
                "languageCode": "km-KH",
                "maxAlternatives": 10,
                "profanityFilter": False,
                "enableAutomaticPunctuation": False,
                "speechContexts": [{
                    "phrases": KHMER_SPEECH_PHRASES,
                    "boost": 20.0
                }]
            },
            "audio": {
                "content": base64.b64encode(pcm_bytes).decode('ascii')
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            alts = []
            for r in data.get('results', []):
                for alt in r.get('alternatives', []):
                    t = (alt.get('transcript') or '').strip()
                    if t:
                        alts.append(t)
            if alts:
                return alts, 'google_cloud_stt_km_kh'
    return None, 'no_google_api_key'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(SQLITE_BACKUP_DIR, exist_ok=True)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

_VOICE_TEMPLATES_CACHE = None

def load_voice_templates():
    global _VOICE_TEMPLATES_CACHE
    if _VOICE_TEMPLATES_CACHE is not None:
        return _VOICE_TEMPLATES_CACHE
    if os.path.exists(VOICE_TEMPLATES_FILE):
        try:
            with open(VOICE_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                _VOICE_TEMPLATES_CACHE = json.load(f)
                return _VOICE_TEMPLATES_CACHE
        except Exception:
            pass
    _VOICE_TEMPLATES_CACHE = {}
    return _VOICE_TEMPLATES_CACHE

def save_voice_templates(templates):
    global _VOICE_TEMPLATES_CACHE
    _VOICE_TEMPLATES_CACHE = templates
    try:
        with open(VOICE_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False)
    except Exception:
        pass

def is_human_speech(samples, sr=16000):
    arr = np.asarray(samples, dtype=np.float32)
    if len(arr) < int(sr * 0.13):
        return False, 'too_short'
    arr = arr - np.mean(arr)
    rms = float(np.sqrt(np.mean(arr ** 2)))
    peak = float(np.max(np.abs(arr)))
    if rms < 0.016 or peak < 0.055:
        return False, 'too_quiet'
    n_fft = 512
    hop = 160
    num_frames = (len(arr) - n_fft) // hop
    if num_frames < 4:
        return False, 'too_few_frames'
    idx = np.tile(np.arange(n_fft), (num_frames, 1)) + np.tile(np.arange(num_frames) * hop, (n_fft, 1)).T
    frames = arr[idx] * np.hamming(n_fft)
    frame_rms = np.sqrt(np.mean(frames ** 2, axis=1))
    max_frms = float(np.max(frame_rms))
    voiced_candidates = frames[frame_rms > max_frms * 0.25]
    if len(voiced_candidates) < 3:
        return False, 'no_active_frames'
    # Check human vocal cord periodicity via normalized autocorrelation in lags 38..215 (74Hz..420Hz, covering deep male to female voices)
    ac_peaks = []
    for fr in voiced_candidates:
        fr_z = fr - np.mean(fr)
        e = float(np.sum(fr_z ** 2)) + 1e-8
        ac = np.correlate(fr_z, fr_z, mode='full')[len(fr_z)-1:] / e
        ac_peaks.append(float(np.max(ac[38:215])))
    ac_peaks.sort(reverse=True)
    top_ac = float(np.mean(ac_peaks[:min(5, len(ac_peaks))]))
    if top_ac < 0.42:
        return False, 'wind_or_noise'
    return True, 'ok'

def compute_mfcc_features(samples, sr=16000, n_mfcc=13, n_fft=512, hop=160, n_mels=26, target_frames=24, freq_warp=1.0, check_speech=True):
    if check_speech:
        ok, _ = is_human_speech(samples, sr=sr)
        if not ok:
            return []
    arr = np.asarray(samples, dtype=np.float32)
    arr = arr - np.mean(arr)
    peak = float(np.max(np.abs(arr)))
    if peak < 1e-6:
        return []
    arr = arr / peak
    arr = np.append(arr[0], arr[1:] - 0.97 * arr[:-1])
    num_frames = 1 + max(0, (len(arr) - n_fft) // hop)
    if num_frames < 4:
        return []
    idx = np.tile(np.arange(n_fft), (num_frames, 1)) + np.tile(np.arange(num_frames) * hop, (n_fft, 1)).T
    frames = arr[np.minimum(idx, len(arr) - 1)] * np.hamming(n_fft)
    mag = np.abs(np.fft.rfft(frames, n=n_fft))
    pow_frames = (1.0 / n_fft) * (mag ** 2)
    frame_energy = np.sum(pow_frames, axis=1)
    max_e = float(np.max(frame_energy))
    active = np.where(frame_energy > max_e * 0.07)[0]
    if len(active) < 4:
        return []
    pow_frames = pow_frames[active[0]:active[-1] + 1]
    low_mel = 2595.0 * np.log10(1.0 + (120.0 * freq_warp) / 700.0)
    high_mel = 2595.0 * np.log10(1.0 + min(sr * 0.48, 3800.0 * freq_warp) / 700.0)
    mel_pts = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_pts = 700.0 * (10.0 ** (mel_pts / 2595.0) - 1.0)
    bins = np.floor((n_fft + 1) * hz_pts / sr).astype(int)
    fbank = np.zeros((n_mels, int(n_fft // 2 + 1)), dtype=np.float32)
    for m in range(1, n_mels + 1):
        f_m_minus, f_m, f_m_plus = bins[m - 1], bins[m], bins[m + 1]
        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - f_m_minus) / max(1, f_m - f_m_minus)
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (f_m_plus - k) / max(1, f_m_plus - f_m)
    filter_banks = np.dot(pow_frames, fbank.T)
    filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)
    log_mel = np.log(filter_banks)
    # DCT-II matrix to extract C1..C12 (removes glottal pitch F0 and overall loudness C0)
    k = np.arange(1, n_mfcc)[:, None]
    n = np.arange(n_mels)[None, :]
    dct = np.cos(np.pi * k * (2 * n + 1) / (2.0 * n_mels))
    mfcc = np.dot(log_mel, dct.T)
    lift = 1.0 + (22.0 / 2.0) * np.sin(np.pi * np.arange(1, n_mfcc) / 22.0)
    mfcc = mfcc * lift
    indices = np.linspace(0, len(mfcc) - 1, target_frames).astype(int)
    mfcc = mfcc[indices]
    mfcc = (mfcc - np.mean(mfcc)) / (float(np.std(mfcc)) + 1e-6)
    return np.round(mfcc, 3).tolist()

def dtw_distance(s1, s2):
    a = np.asarray(s1, dtype=np.float32)
    b = np.asarray(s2, dtype=np.float32)
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 999.0
    diff = a[:, None, :] - b[None, :, :]
    cost = np.sqrt(np.sum(diff * diff, axis=2)) / np.sqrt(a.shape[1])
    dp = np.full((n + 1, m + 1), np.inf, dtype=np.float32)
    dp[0, 0] = 0.0
    band = max(4, abs(n - m) + 4)
    for i in range(1, n + 1):
        j_start = max(1, i - band)
        j_end = min(m + 1, i + band + 1)
        for j in range(j_start, j_end):
            c = cost[i - 1, j - 1]
            dp[i, j] = c + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return float(dp[n, m] / (n + m))

def _match_single_feat(feat, templates, max_score=100.0, allowed_labels=None):
    if not feat or not templates:
        return None, 999.0, 0.0
    query = np.asarray(feat, dtype=np.float32)
    q_norm = float(np.linalg.norm(query)) + 1e-8
    candidates = []
    for label, tpl_list in templates.items():
        if label.startswith('_'):
            continue
        if allowed_labels is not None and label not in allowed_labels:
            continue
        if label not in ['next', 'back', 'clear', 'save']:
            try:
                num_val = float(label)
                if num_val < 0 or num_val > max_score:
                    continue
            except Exception:
                continue
        for tpl in (tpl_list or []):
            t_arr = np.asarray(tpl, dtype=np.float32)
            if t_arr.shape == query.shape:
                cos_sim = float(np.sum(query * t_arr) / (q_norm * float(np.linalg.norm(t_arr)) + 1e-8))
                if cos_sim >= 0.45:
                    candidates.append((cos_sim, label, t_arr))
    if not candidates:
        return None, 999.0, 0.0
    candidates.sort(key=lambda x: -x[0])
    best_label = None
    best_dist = 999.0
    best_cos = 0.0
    for cos_sim, label, t_arr in candidates[:8]:
        d = dtw_distance(query, t_arr)
        if d < best_dist:
            best_dist = d
            best_label = label
            best_cos = cos_sim
    if best_cos < 0.50 or best_dist > 0.85:
        return None, best_dist, best_cos
    return best_label, best_dist, best_cos

def match_offline_voice(samples, sr=16000, max_score=100.0):
    templates = load_voice_templates()
    if not templates:
        return None, 999.0
    feat = compute_mfcc_features(samples, sr=sr)
    if not feat:
        return None, 999.0
    # 1. Try matching against user-recorded templates first (highest accuracy for this speaker)
    user_keys = set(templates.get('_user_recorded', []))
    if user_keys:
        u_label, u_dist, u_cos = _match_single_feat(feat, templates, max_score=max_score, allowed_labels=user_keys)
        if u_label is not None and u_cos >= 0.58 and u_dist <= 0.76:
            return u_label, round(u_dist, 3)
    # 2. Match against all templates (including VTLN built-in Khmer templates)
    best_label, best_dist, _ = _match_single_feat(feat, templates, max_score=max_score)
    return best_label, round(best_dist, 3)

def seed_default_khmer_voice_templates():
    templates = {}
    warps = [0.74, 0.82, 0.90, 0.98, 1.05]
    if os.path.exists(TTS_CACHE_DIR):
        for fname in sorted(os.listdir(TTS_CACHE_DIR)):
            if fname.startswith('kh_') and fname.endswith('.mp3'):
                label = fname[3:-4]
                mp3_path = os.path.join(TTS_CACHE_DIR, fname)
                wav_path = mp3_path + '.seed.wav'
                try:
                    subprocess.run(['/usr/bin/afconvert', '-f', 'WAVE', '-d', 'LEI16@16000', '-c', '1', mp3_path, wav_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                    if os.path.exists(wav_path):
                        with wave.open(wav_path, 'rb') as wf:
                            raw_frames = wf.readframes(wf.getnframes())
                            samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
                        try: os.remove(wav_path)
                        except: pass
                        tpl_list = []
                        for w in warps:
                            feat = compute_mfcc_features(samples, sr=16000, freq_warp=w, check_speech=False)
                            if feat:
                                tpl_list.append(feat)
                        if tpl_list:
                            templates[label] = tpl_list
                except Exception:
                    pass
    templates['_user_recorded'] = []
    save_voice_templates(templates)
    return templates

def extract_mfcc_from_mp3(mp3_path, label):
    try:
        wav_path = mp3_path + '.wav'
        subprocess.run(['/usr/bin/afconvert', '-f', 'WAVE', '-d', 'LEI16@16000', '-c', '1', mp3_path, wav_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        if os.path.exists(wav_path):
            with wave.open(wav_path, 'rb') as wf:
                raw_frames = wf.readframes(wf.getnframes())
                samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
            try: os.remove(wav_path)
            except: pass
            feat = compute_mfcc_features(samples, sr=16000, check_speech=False)
            if feat:
                templates = load_voice_templates()
                if label not in templates or not templates[label]:
                    templates[label] = [feat]
                    save_voice_templates(templates)
    except Exception:
        pass

def export_to_sqlite(data_dict, db_path):
    """Creates a comprehensive SQLite database (.db) from the data dictionary."""
    tmp_db = db_path + '.tmp'
    if os.path.exists(tmp_db):
        try: os.remove(tmp_db)
        except: pass

    conn = sqlite3.connect(tmp_db)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            khmer_name TEXT NOT NULL,
            latin_name TEXT,
            gender TEXT,
            dob TEXT,
            class TEXT,
            class_type TEXT,
            phone TEXT,
            guardian TEXT,
            address TEXT,
            province_code TEXT,
            district_code TEXT,
            commune_code TEXT,
            village_code TEXT
        );
        CREATE TABLE IF NOT EXISTS subjects (
            code TEXT PRIMARY KEY,
            name TEXT,
            max_score REAL,
            coefficient REAL,
            is_enabled INTEGER
        );
        CREATE TABLE IF NOT EXISTS scores (
            student_id TEXT,
            period_key TEXT,
            subject_code TEXT,
            score REAL,
            PRIMARY KEY (student_id, period_key, subject_code)
        );
        CREATE TABLE IF NOT EXISTS exam_arrangements (
            student_id TEXT PRIMARY KEY,
            khmer_name TEXT,
            room_number TEXT,
            desk_number TEXT,
            secret_code TEXT,
            grade TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS room_subject_secrets (
            grade_key TEXT,
            room_number TEXT,
            subject_code TEXT,
            secret_code TEXT,
            PRIMARY KEY (grade_key, room_number, subject_code)
        );
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')

    students = data_dict.get('students', [])
    stu_rows = [
        (
            str(s.get('id', '')),
            str(s.get('khmerName', '')),
            str(s.get('latinName', '')),
            str(s.get('gender', '')),
            str(s.get('dob', '')),
            str(s.get('class', '')),
            str(s.get('classType', '')),
            str(s.get('phone', '')),
            str(s.get('guardian', '')),
            str(s.get('address', '')),
            str(s.get('provinceCode', '')),
            str(s.get('districtCode', '')),
            str(s.get('communeCode', '')),
            str(s.get('villageCode', ''))
        )
        for s in students if s and s.get('id')
    ]
    if stu_rows:
        c.executemany('INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', stu_rows)

    subjects = data_dict.get('subjects', [])
    sub_rows = [
        (
            str(s.get('code', '')),
            str(s.get('name', '')),
            float(s.get('maxScore', 100) or 100),
            float(s.get('coef', 1) or 1),
            1 if s.get('enabled', True) else 0
        )
        for s in subjects if s and s.get('code')
    ]
    if sub_rows:
        c.executemany('INSERT OR REPLACE INTO subjects VALUES (?,?,?,?,?)', sub_rows)

    scores = data_dict.get('scores', {})
    score_rows = []
    for sid, pdict in scores.items():
        if isinstance(pdict, dict):
            for p, subs in pdict.items():
                if isinstance(subs, dict):
                    for sub, val in subs.items():
                        if val not in [None, '']:
                            try:
                                score_rows.append((str(sid), str(p), str(sub), float(val)))
                            except:
                                pass
    if score_rows:
        c.executemany('INSERT OR REPLACE INTO scores VALUES (?,?,?,?)', score_rows)

    arr = data_dict.get('examArrangements', [])
    arr_rows = [
        (
            str(a.get('studentId', '')),
            str(a.get('khmerName', '')),
            str(a.get('roomNumber', '')),
            str(a.get('deskNumber', '')),
            str(a.get('secretCode', '')),
            str(a.get('grade', '')),
            str(a.get('status', ''))
        )
        for a in arr if a and a.get('studentId')
    ]
    if arr_rows:
        c.executemany('INSERT OR REPLACE INTO exam_arrangements VALUES (?,?,?,?,?,?,?)', arr_rows)

    rss = data_dict.get('roomSubjectSecrets', {})
    rss_rows = []
    if isinstance(rss, dict):
        for g_key, rooms in rss.items():
            if isinstance(rooms, dict):
                for r_key, subs in rooms.items():
                    if isinstance(subs, dict):
                        for sub_code, sec_code in subs.items():
                            if sec_code:
                                rss_rows.append((str(g_key), str(r_key), str(sub_code), str(sec_code)))
    if rss_rows:
        c.executemany('INSERT OR REPLACE INTO room_subject_secrets VALUES (?,?,?,?)', rss_rows)

    c.execute('INSERT OR REPLACE INTO app_state VALUES (?, ?)', ('full_state', json.dumps(data_dict, ensure_ascii=False)))
    c.execute('INSERT OR REPLACE INTO app_state VALUES (?, ?)', ('room_subject_secrets', json.dumps(rss, ensure_ascii=False)))
    conn.commit()
    conn.close()

    os.replace(tmp_db, db_path)

def create_auto_sqlite_backup(data_dict):
    """Automatically backs up to a specific folder: data/backups/sqlite_db/"""
    try:
        ts = time.strftime('%Y%m%d_%H%M%S')
        sqlite_file = os.path.join(SQLITE_BACKUP_DIR, f"sms_backup_{ts}.db")
        export_to_sqlite(data_dict, sqlite_file)
        
        # Also maintain primary sms_cambodia.db and sms_database.db
        shutil.copyfile(sqlite_file, SQLITE_MASTER_FILE)
        shutil.copyfile(sqlite_file, SQLITE_DATABASE_FILE)

        # Rotate: keep latest 30 .db files
        db_files = sorted([os.path.join(SQLITE_BACKUP_DIR, f) for f in os.listdir(SQLITE_BACKUP_DIR) if f.endswith('.db')])
        if len(db_files) > 30:
            for old_f in db_files[:-30]:
                try: os.remove(old_f)
                except: pass
        return sqlite_file
    except Exception as e:
        print(f"Auto SQLite backup error: {e}")
        return None

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_cors_headers(self, status=200, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()

    def do_OPTIONS(self):
        self.end_cors_headers(204)

    def handle_api_data(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/supabase-config':
            cfg_file = os.path.join(DATA_DIR, 'supabase_config.json')
            if os.path.exists(cfg_file):
                try:
                    with open(cfg_file, 'rb') as f:
                        content = f.read()
                    self.end_cors_headers(200, 'application/json; charset=utf-8')
                    self.wfile.write(content)
                    return True
                except Exception as e:
                    self.send_error(500, f"Read config error: {e}")
                    return True
            else:
                default_cfg = {
                    "url": "https://ztyqyvogvvkgaduwdjoy.supabase.co",
                    "key": "",
                    "teacherName": "teacher_mobile"
                }
                self.end_cors_headers(200, 'application/json; charset=utf-8')
                self.wfile.write(json.dumps(default_cfg).encode('utf-8'))
                return True

        if parsed.path == '/api/data':
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, 'rb') as f:
                        content = f.read()
                    self.end_cors_headers(200, 'application/json; charset=utf-8')
                    self.wfile.write(content)
                    return True
                except Exception as e:
                    self.send_error(500, f"Read error: {e}")
                    return True
            else:
                self.end_cors_headers(404)
                self.wfile.write(b'{"status": "not_found"}')
                return True
        return False

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/supabase-config':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                cfg = json.loads(body.decode('utf-8'))
                cfg_file = os.path.join(DATA_DIR, 'supabase_config.json')
                with open(cfg_file, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self.end_cors_headers(200)
                self.wfile.write(b'{"status": "ok"}')
            except Exception as e:
                self.send_error(500, f"Save supabase config error: {e}")
            return

        if parsed.path == '/api/mobile-scores':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                updated_count = 0
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r', encoding='utf-8') as f:
                        curr_data = json.load(f)
                    if 'scores' not in curr_data or not isinstance(curr_data['scores'], dict):
                        curr_data['scores'] = {}

                    scores_list = payload.get('scores', [])
                    p_key = payload.get('periodKey')
                    sub_code = payload.get('subjectCode')

                    for item in scores_list:
                        s_id = str(item.get('student_id') or item.get('studentId') or '')
                        score_val = item.get('score')
                        item_sub = item.get('subject_code') or item.get('subjectCode') or sub_code
                        item_p = item.get('period_key') or item.get('periodKey') or p_key
                        if not s_id or not item_p or not item_sub or score_val is None:
                            continue
                        if s_id not in curr_data['scores']:
                            curr_data['scores'][s_id] = {}
                        if item_p not in curr_data['scores'][s_id]:
                            curr_data['scores'][s_id][item_p] = {}
                        curr_data['scores'][s_id][item_p][item_sub] = score_val
                        updated_count += 1

                    tmp_file = DATA_FILE + '.tmp'
                    with open(tmp_file, 'w', encoding='utf-8') as f:
                        json.dump(curr_data, f, ensure_ascii=False, indent=2)
                    os.replace(tmp_file, DATA_FILE)
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({"status": "ok", "updatedCount": updated_count}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Save mobile scores error: {e}")
            return

        if parsed.path == '/api/data':
            try:
                length = int(self.headers.get('Content-Length', 0))
                if length <= 0:
                    self.send_error(400, "Empty payload")
                    return
                body = self.rfile.read(length)
                parsed_json = json.loads(body.decode('utf-8'))

                # Protect restored original roomSubjectSecrets against stale unrefreshed browser tabs
                restored_secrets_path = os.path.join(BACKUP_DIR, 'sms_restored_original_secrets.json')
                if isinstance(parsed_json, dict):
                    if parsed_json.pop('_explicitSecretMatrixSave', False):
                        if parsed_json.get('roomSubjectSecrets'):
                            with open(restored_secrets_path, 'w', encoding='utf-8') as rf:
                                json.dump(parsed_json['roomSubjectSecrets'], rf, ensure_ascii=False, indent=2)
                    elif os.path.exists(restored_secrets_path):
                        try:
                            with open(restored_secrets_path, 'r', encoding='utf-8') as rf:
                                locked_secrets = json.load(rf)
                            if isinstance(locked_secrets, dict) and locked_secrets:
                                parsed_json['roomSubjectSecrets'] = locked_secrets
                        except Exception:
                            pass
                    g10_order = [
                        'ភាសាខ្មែរ', 'គណិតវិទ្យា', 'រូបវិទ្យា', 'គីមីវិទ្យា', 'ជីវវិទ្យា',
                        'ប្រវត្តិវិទ្យា', 'សីល-ពលរដ្ឋ', 'ផែនដីវិទ្យា', 'ភូមិវិទ្យា', 'ភាសាបរទេស'
                    ]
                    if not isinstance(parsed_json.get('examSubjectOrders'), dict):
                        parsed_json['examSubjectOrders'] = {}
                    for gk in ['grade_11_sci', 'grade_11_soc', 'grade_12_sci', 'grade_12_soc']:
                        if len(parsed_json['examSubjectOrders'].get(gk, [])) < 10:
                            parsed_json['examSubjectOrders'][gk] = list(g10_order)
                    body = json.dumps(parsed_json, ensure_ascii=False).encode('utf-8')

                # Write atomically to data/sms_data.json
                tmp_file = DATA_FILE + '.tmp'
                with open(tmp_file, 'wb') as f:
                    f.write(body)
                os.replace(tmp_file, DATA_FILE)

                # Periodic automatic disk backup (throttled to at most once every 90s to keep score entry instant)
                now_ts = time.time()
                force_backup = isinstance(parsed_json, dict) and bool(parsed_json.pop('_forceBackup', False))
                last_backup_ts = getattr(AppHandler, '_last_auto_backup_ts', 0.0)
                if isinstance(parsed_json, dict) and parsed_json.get('students') and (force_backup or (now_ts - last_backup_ts >= 90.0)):
                    AppHandler._last_auto_backup_ts = now_ts
                    ts = time.strftime('%Y%m%d_%H%M%S')
                    backup_file = os.path.join(BACKUP_DIR, f"backup_{ts}.json")
                    if not os.path.exists(backup_file):
                        with open(backup_file, 'wb') as f:
                            f.write(body)
                        backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith('backup_')])
                        if len(backups) > 25:
                            for old_b in backups[:-25]:
                                try: os.remove(old_b)
                                except: pass
                    # Automatic SQLite .db backup into dedicated folder (data/backups/sqlite_db/)
                    create_auto_sqlite_backup(parsed_json)

                self.end_cors_headers(200)
                resp_payload = {
                    "status": "ok",
                    "saved": true_val if (true_val := True) else True,
                    "roomSubjectSecrets": parsed_json.get('roomSubjectSecrets', {}) if isinstance(parsed_json, dict) else {}
                }
                self.wfile.write(json.dumps(resp_payload, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Save error: {e}")
            return

        if parsed.path == '/api/sqlite/backup-now':
            try:
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r', encoding='utf-8') as f:
                        curr_data = json.load(f)
                    created_file = create_auto_sqlite_backup(curr_data)
                    self.end_cors_headers(200)
                    resp = {
                        "status": "ok",
                        "file": os.path.basename(created_file) if created_file else "",
                        "folder": SQLITE_BACKUP_DIR,
                        "path": created_file or ""
                    }
                    self.wfile.write(json.dumps(resp).encode('utf-8'))
                else:
                    self.send_error(404, "No data file found")
            except Exception as e:
                self.send_error(500, f"SQLite backup error: {e}")
            return

        if parsed.path == '/api/offline-stt/reset':
            try:
                templates = seed_default_khmer_voice_templates()
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({"status": "ok", "totalLabels": len([k for k in templates if not k.startswith('_')])}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Reset error: {e}")
            return

        if parsed.path == '/api/offline-stt/learn':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                label = str(payload.get('label', '')).strip()
                samples = payload.get('samples', [])
                sr = int(payload.get('sampleRate', 16000) or 16000)
                if not label or not samples:
                    self.send_error(400, "Missing label or samples")
                    return
                ok, _ = is_human_speech(samples, sr=sr)
                learned = False
                if ok:
                    new_feats = []
                    for w in [1.0, 0.92, 1.08]:
                        f_w = compute_mfcc_features(samples, sr=sr, freq_warp=w, check_speech=False)
                        if f_w:
                            new_feats.append(f_w)
                    if new_feats:
                        templates = load_voice_templates()
                        user_rec = list(templates.get('_user_recorded', []))
                        if label not in user_rec:
                            user_rec.append(label)
                            templates['_user_recorded'] = user_rec
                        existing = templates.get(label, [])
                        templates[label] = (new_feats + existing)[:8]
                        save_voice_templates(templates)
                        learned = True
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "learned": learned,
                    "label": label,
                    "templatesCount": len(load_voice_templates().get(label, [])),
                    "totalLabels": len([k for k in load_voice_templates() if not k.startswith('_')])
                }).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Learn error: {e}")
            return

        if parsed.path == '/api/offline-stt':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                samples = payload.get('samples', [])
                sr = int(payload.get('sampleRate', 16000) or 16000)
                max_score = float(payload.get('maxScore', 100) or 100)
                ok, reason = is_human_speech(samples, sr=sr)
                if not ok:
                    self.end_cors_headers(200)
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "matched": False,
                        "reason": reason,
                        "distance": 999.0
                    }).encode('utf-8'))
                    return
                label, dist = match_offline_voice(samples, sr=sr, max_score=max_score)
                self.end_cors_headers(200)
                if label is not None and dist <= 0.85:
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "matched": True,
                        "label": label,
                        "distance": dist
                    }).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "matched": False,
                        "reason": "no_match",
                        "distance": dist
                    }).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Offline STT error: {e}")
            return

        if parsed.path == '/api/ai-stt/config':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length > 0 else b'{}'
                payload = json.loads(body.decode('utf-8'))
                cfg = save_ai_stt_config(payload)
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "engine": cfg.get("engine", "hybrid"),
                    "whisperProvider": cfg.get("whisperProvider", "groq"),
                    "whisperModel": cfg.get("whisperModel", "whisper-large-v3"),
                    "hasGroqKey": bool(cfg.get("groqApiKey")),
                    "hasOpenaiKey": bool(cfg.get("openaiApiKey")),
                    "hasGoogleKey": bool(cfg.get("googleApiKey"))
                }).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"AI STT config error: {e}")
            return

        if parsed.path == '/api/ai-stt':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                sr = int(payload.get('sampleRate', 16000) or 16000)
                max_score = float(payload.get('maxScore', 100) or 100)
                samples = payload.get('samples', [])
                audio_b64 = payload.get('audioBase64', '')
                audio_ext = payload.get('audioFormat', 'webm')

                wav_bytes = b''
                pcm_bytes = b''
                if audio_b64:
                    raw_blob = base64.b64decode(audio_b64)
                    wav_bytes, pcm_bytes, samples = audio_blob_to_wav_bytes(raw_blob, ext=audio_ext, target_sr=sr)
                elif samples:
                    ok, reason = is_human_speech(samples, sr=sr)
                    if not ok:
                        self.end_cors_headers(200)
                        self.wfile.write(json.dumps({"status": "ok", "matched": False, "reason": reason}).encode('utf-8'))
                        return
                    wav_bytes, pcm_bytes = samples_to_wav_bytes(samples, sr=sr)

                if not wav_bytes:
                    self.end_cors_headers(200)
                    self.wfile.write(json.dumps({"status": "ok", "matched": False, "reason": "empty_audio"}).encode('utf-8'))
                    return

                cfg = load_ai_stt_config().copy()
                # Allow inline overrides from frontend request
                for k in ('engine', 'whisperProvider', 'whisperModel', 'openaiApiKey', 'groqApiKey', 'googleApiKey'):
                    if payload.get(k):
                        cfg[k] = payload[k]

                engine = cfg.get('engine', 'hybrid')
                transcripts = None
                used_engine = None

                # 1. Google Cloud Speech-to-Text API (km-KH) if selected or in hybrid mode with Google key
                if engine in ('google_cloud', 'hybrid') and cfg.get('googleApiKey'):
                    try:
                        transcripts, used_engine = transcribe_with_google_cloud_stt(pcm_bytes, sr=sr, api_key=cfg.get('googleApiKey'))
                    except Exception:
                        pass

                # 2. OpenAI Whisper / Groq Whisper Large-v3 API
                if not transcripts and engine in ('whisper_api', 'hybrid') and (cfg.get('groqApiKey') or cfg.get('openaiApiKey')):
                    try:
                        transcripts, used_engine = transcribe_with_whisper_api(wav_bytes, cfg)
                    except Exception:
                        pass

                # 3. Local Whisper on Server (mlx_whisper / faster_whisper / openai-whisper)
                if not transcripts and engine in ('local_whisper', 'whisper_api', 'hybrid'):
                    try:
                        transcripts, used_engine = transcribe_with_local_whisper(wav_bytes)
                    except Exception:
                        pass

                # 4. Built-in Offline MFCC + DTW Khmer Voice Classifier fallback
                if not transcripts and samples:
                    label, dist = match_offline_voice(samples, sr=sr, max_score=max_score)
                    if label is not None and dist <= 0.85:
                        transcripts = [str(label)]
                        used_engine = f'offline_dtw:{dist}'

                self.end_cors_headers(200)
                if transcripts:
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "matched": True,
                        "transcript": transcripts[0],
                        "alternatives": transcripts,
                        "engine": used_engine
                    }, ensure_ascii=False).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "matched": False,
                        "reason": "no_match"
                    }).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"AI STT error: {e}")
            return
        
        if parsed.path == '/api/handwriting':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                
                ink = payload.get('ink', [])
                width = int(payload.get('width', 400) or 400)
                height = int(payload.get('height', 300) or 300)
                lang = payload.get('language', 'en') or 'en'
                
                g_req = {
                    'options': 'enable_pre_space',
                    'requests': [{
                        'writing_guide': {'writing_area_width': width, 'writing_area_height': height},
                        'ink': ink,
                        'language': lang
                    }]
                }
                req_data = json.dumps(g_req).encode('utf-8')
                g_url = 'https://www.google.com/inputtools/request?ime=handwriting&app=mobilesearch'
                req = urllib.request.Request(g_url, data=req_data, headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
                })
                candidates = []
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp_data = resp.read().decode('utf-8')
                    parsed_res = json.loads(resp_data)
                    if isinstance(parsed_res, list) and len(parsed_res) > 1:
                        if parsed_res[0] == 'SUCCESS' and isinstance(parsed_res[1], list) and len(parsed_res[1]) > 0:
                            candidates = parsed_res[1][0][1]
                
                # If no digit found in english, try khmer
                has_digit = any(any(c in item for c in '0123456789') for item in candidates)
                if not has_digit:
                    try:
                        g_req['requests'][0]['language'] = 'km'
                        req_data = json.dumps(g_req).encode('utf-8')
                        req_km = urllib.request.Request(g_url, data=req_data, headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
                        })
                        with urllib.request.urlopen(req_km, timeout=3) as resp_km:
                            parsed_km = json.loads(resp_km.read().decode('utf-8'))
                            if isinstance(parsed_km, list) and len(parsed_km) > 1 and parsed_km[0] == 'SUCCESS':
                                km_candidates = parsed_km[1][0][1]
                                for c in km_candidates:
                                    if c not in candidates:
                                        candidates.append(c)
                    except Exception:
                        pass
                
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({'status': 'ok', 'candidates': candidates}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e), 'candidates': []}).encode('utf-8'))
            return

        self.send_error(404, "Not Found")

    def handle_sqlite_api(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/ai-stt/config':
            cfg = load_ai_stt_config()
            self.end_cors_headers(200)
            self.wfile.write(json.dumps({
                "status": "ok",
                "engine": cfg.get("engine", "hybrid"),
                "whisperProvider": cfg.get("whisperProvider", "groq"),
                "whisperModel": cfg.get("whisperModel", "whisper-large-v3"),
                "hasGroqKey": bool(cfg.get("groqApiKey")),
                "hasOpenaiKey": bool(cfg.get("openaiApiKey")),
                "hasGoogleKey": bool(cfg.get("googleApiKey"))
            }).encode('utf-8'))
            return True
        if parsed.path == '/api/offline-stt/status':
            templates = load_voice_templates()
            user_rec = set(templates.get('_user_recorded', []))
            summary = {k: len(v) for k, v in templates.items() if not k.startswith('_')}
            self.end_cors_headers(200)
            self.wfile.write(json.dumps({
                "status": "ok",
                "totalLabels": len(summary),
                "userRecorded": list(user_rec),
                "labels": summary
            }).encode('utf-8'))
            return True
        if parsed.path == '/api/sqlite/backups':
            try:
                files = []
                if os.path.exists(SQLITE_BACKUP_DIR):
                    for fname in sorted(os.listdir(SQLITE_BACKUP_DIR), reverse=True):
                        if fname.endswith('.db'):
                            fpath = os.path.join(SQLITE_BACKUP_DIR, fname)
                            st = os.stat(fpath)
                            files.append({
                                "filename": fname,
                                "size_bytes": st.st_size,
                                "size_kb": round(st.st_size / 1024, 1),
                                "size_mb": round(st.st_size / (1024 * 1024), 2),
                                "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
                                "mtime": st.st_mtime
                            })
                self.end_cors_headers(200)
                self.wfile.write(json.dumps({"status": "ok", "folder": SQLITE_BACKUP_DIR, "backups": files}).encode('utf-8'))
                return True
            except Exception as e:
                self.send_error(500, f"Error listing SQLite backups: {e}")
                return True

        if parsed.path == '/api/sqlite/download':
            try:
                params = urllib.parse.parse_qs(parsed.query)
                fname = params.get('file', [''])[0]
                fname = os.path.basename(fname)
                fpath = os.path.join(SQLITE_BACKUP_DIR, fname)
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-sqlite3')
                    self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
                    self.send_header('Content-Length', str(len(data)))
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(data)
                    return True
                else:
                    self.send_error(404, "File not found")
                    return True
            except Exception as e:
                self.send_error(500, f"Download error: {e}")
                return True
        return False

    def handle_tts(self, is_head=False):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/tts':
            params = urllib.parse.parse_qs(parsed.query)
            text = params.get('text', params.get('q', ['']))[0].strip()
            if not text:
                self.send_error(400, "Missing text parameter")
                return True
            cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
            cache_file = os.path.join(TTS_CACHE_DIR, f"{cache_key}.mp3")
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100:
                try:
                    with open(cache_file, 'rb') as cf:
                        content = cf.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.send_header('Content-Length', str(len(content)))
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Cache-Control', 'public, max-age=86400')
                    self.end_headers()
                    if not is_head:
                        self.wfile.write(content)
                    return True
                except Exception:
                    pass
            try:
                tts_url = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=km&client=gtx&q=' + urllib.parse.quote(text)
                req = urllib.request.Request(tts_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                with urllib.request.urlopen(req, timeout=5) as resp:
                    content = resp.read()
                    if content and len(content) > 100:
                        try:
                            with open(cache_file, 'wb') as cf:
                                cf.write(content)
                            try:
                                float(text)
                                extract_mfcc_from_mp3(cache_file, text)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.send_header('Content-Length', str(len(content)))
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Cache-Control', 'public, max-age=86400')
                    self.end_headers()
                    if not is_head:
                        self.wfile.write(content)
            except Exception as e:
                self.send_error(503, f"Offline TTS fallback: {e}")
            return True
        return False

    def do_GET(self):
        req_path = self.path.split('?')[0]
        if req_path in ('/mobile', '/mobile/'):
            self.path = '/mobile.html'
        if self.handle_api_data():
            return
        if self.handle_sqlite_api():
            return
        if not self.handle_tts(is_head=False):
            return super().do_GET()

    def do_HEAD(self):
        if not self.handle_tts(is_head=True):
            return super().do_HEAD()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    with socketserver.ThreadingTCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"SMS Server running on http://localhost:{PORT}")
        httpd.serve_forever()
