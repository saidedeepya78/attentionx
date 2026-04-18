"""
AttentionX — Groq API integration (free, 14400 req/day, no credit card)
"""

import json
import re
import time
from groq import Groq


FALLBACK_KEYS: list[str] = []


def set_fallback_keys(keys: list[str]):
    global FALLBACK_KEYS
    FALLBACK_KEYS = [_clean_key(k) for k in keys if k and k.strip()]


def _clean_key(key: str) -> str:
    if not key:
        return ""
    return key.strip().replace("\n", "").replace("\r", "").replace(" ", "")


def test_api_key(api_key: str) -> tuple[bool, str]:
    try:
        client = Groq(api_key=_clean_key(api_key))
        chat   = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            max_tokens=10,
        )
        if chat.choices[0].message.content:
            return True, "Key is valid"
        return False, "Empty response"
    except Exception as e:
        return False, str(e)


def _call_groq(prompt: str, api_key: str) -> str:
    all_keys = [_clean_key(api_key)] + [_clean_key(k) for k in FALLBACK_KEYS if k]
    seen, unique_keys = set(), []
    for k in all_keys:
        if k and k not in seen:
            seen.add(k)
            unique_keys.append(k)

    if not unique_keys:
        raise Exception("no_key: No API key provided.")

    last_err = None
    for i, key in enumerate(unique_keys):
        try:
            client = Groq(api_key=key)
            chat   = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.7,
            )
            return chat.choices[0].message.content.strip()
        except Exception as e:
            err_str   = str(e)
            err_lower = err_str.lower()
            last_err  = err_str

            is_auth = (
                "401"             in err_str
                or "invalid api key" in err_lower
                or "authentication"  in err_lower
                or "403"          in err_str
            )
            is_quota = (
                "429"          in err_str
                or "rate limit"  in err_lower
                or "quota"       in err_lower
            )

            if is_auth:
                raise Exception(f"bad_key: {err_str}")
            if is_quota:
                if i < len(unique_keys) - 1:
                    time.sleep(2)
                    continue
                time.sleep(30)
                raise Exception(f"quota: {err_str}")
            raise Exception(f"unknown: {err_str}")

    raise Exception(f"unknown: {last_err}")


def _parse_json_safe(raw: str):
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$",          "", raw.strip())
    raw = raw.strip()

    arr_start = raw.find("[")
    obj_start = raw.find("{")
    arr_end   = raw.rfind("]")
    obj_end   = raw.rfind("}")

    if arr_start != -1 and arr_end != -1 and (obj_start == -1 or arr_start < obj_start):
        raw = raw[arr_start : arr_end + 1]
    elif obj_start != -1 and obj_end != -1:
        raw = raw[obj_start : obj_end + 1]

    return json.loads(raw)


MOMENT_PROMPT = """
You are an expert content strategist and viral marketing specialist.

Analyze the content below and find the TOP {num_moments} most attention-worthy moments.

Criteria — moments that:
- Contain a surprising insight, bold claim, or counterintuitive idea
- Have emotional weight (inspiring, shocking, funny, relatable)
- Could stand alone as a short-form post and still make sense
- Would make someone stop scrolling

Return ONLY a valid JSON array. No markdown. No explanation. Just the JSON.

[
  {{
    "id": 1,
    "moment_text": "The key insight in 2-3 sentences max",
    "timestamp_hint": "early | middle | near the end",
    "reason": "Why this moment grabs attention (1-2 sentences)",
    "emotion_tag": "Surprise | Inspiration | Curiosity | Relatability | Urgency",
    "virality_score": 8
  }}
]

CONTENT:
---
{content}
---

ONLY return the JSON array. Nothing else.
"""

HOOK_PROMPT = """
You are a world-class copywriter writing viral hooks for TikTok, Reels, and LinkedIn.

Write a scroll-stopping HOOK HEADLINE for this moment.

Rules:
- Max 12 words
- Creates instant curiosity or emotional pull
- Uses: bold claim, question, shocking stat, or contrarian take
- Does NOT reveal the full answer — leaves a curiosity gap

Moment: "{moment_text}"
Why it matters: "{reason}"
Emotion: "{emotion_tag}"

Return ONLY a valid JSON object. No markdown. No explanation.

{{
  "hook": "Your hook here",
  "hook_type": "bold_claim | curiosity_gap | shocking_stat | question | contrarian",
  "secondary_hook": "Alternative hook option"
}}
"""


def extract_moments(content: str, num_moments: int, api_key: str) -> list[dict]:
    prompt = MOMENT_PROMPT.format(content=content[:5000], num_moments=num_moments)
    raw    = _call_groq(prompt, api_key)
    result = _parse_json_safe(raw)
    if not isinstance(result, list):
        raise ValueError("json_parse: Did not return a JSON array.")
    return result


def generate_hook(moment: dict, api_key: str) -> dict:
    prompt = HOOK_PROMPT.format(
        moment_text=moment.get("moment_text", "")[:300],
        reason=moment.get("reason", "")[:200],
        emotion_tag=moment.get("emotion_tag", "Curiosity"),
    )
    raw    = _call_groq(prompt, api_key)
    result = _parse_json_safe(raw)
    if not isinstance(result, dict):
        raise ValueError("json_parse: Did not return a JSON object.")
    return {**moment, **result}


def process_content(content: str, num_moments: int, api_key: str) -> list[dict]:
    moments  = extract_moments(content, num_moments, api_key)
    enriched = []
    for m in moments:
        try:
            enriched.append(generate_hook(m, api_key))
        except Exception:
            m.setdefault("hook",           "Could not generate hook — retry.")
            m.setdefault("hook_type",      "unknown")
            m.setdefault("secondary_hook", "")
            enriched.append(m)
    return enriched