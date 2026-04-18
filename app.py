"""
AttentionX — Main Streamlit Application
"""

import streamlit as st
import time
import os

from utils import (
    process_content,
    clean_text,
    get_hook_type_label,
    format_word_count,
)
from utils.gemini import test_api_key, set_fallback_keys

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AttentionX — Viral Moment Extractor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in {
    "content":    "",
    "results":    [],
    "last_error": "",
    "elapsed":    0,
    "key_tested": False,
    "key_valid":  False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sample content ────────────────────────────────────────────────────────────
SAMPLE = """Most people think success is about working harder. They wake up at 5 AM, grind for 16 hours, and wonder why they burn out. But here is what nobody tells you: the top 1% don't work harder — they work on fundamentally different things.

I've spent the last decade studying performance across 200+ high achievers — from Olympic athletes to startup founders — and the pattern that emerged shocked me. The single biggest predictor of long-term success isn't intelligence, isn't discipline, and it definitely isn't passion. It's your ability to identify and ruthlessly eliminate the 90% of activities that feel productive but produce almost nothing.

Cal Newport calls this shallow work. I call it the productivity trap. We fill our days with emails, meetings, and status updates and we call it work. But none of it compounds. None of it builds something that will matter in 10 years.

The uncomfortable truth about habits is that most self-help advice is designed to sell books, not change behavior. Neuroscience tells us that habits are built through emotional significance, not repetition. Your brain tags experiences with dopamine when they connect to something you deeply care about. So if you cannot stick to a habit, the problem is not willpower — it is that the habit is not connected to anything that actually matters to you.

Here is what changed everything for me: I stopped asking how do I be more productive and started asking what would I regret not doing at 80? That question destroyed my to-do list. Three tasks survived. Everything else was noise I was mistaking for signal.

The most underrated skill in the modern economy is not coding or leadership. It is the ability to be comfortable with long periods of no visible progress while trusting that compounding is working in the background. Every meaningful result in my life came from a 3-to-5-year investment that looked like failure for the first 2 years.

We are in the attention economy now. Your focus is literally the most valuable thing you own. Every app and notification has been engineered by the smartest people in the world to capture as much of it as possible. The people winning right now are the ones who built a fortress around their attention while everyone else surrendered theirs for free."""

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
#MainMenu,footer,.stDeployButton{visibility:hidden}
.stApp{background:linear-gradient(135deg,#0A0A0F,#0D0D1A,#0A0F1A)}

.stButton>button{
  background:linear-gradient(135deg,#7C3AED,#4F46E5)!important;
  color:#fff!important;border:none!important;border-radius:10px!important;
  font-weight:600!important;font-size:14px!important;width:100%!important;
  transition:all .2s!important;
}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 8px 25px rgba(124,58,237,.4)!important}

.stTextArea textarea{
  background:rgba(255,255,255,.04)!important;
  border:1px solid rgba(255,255,255,.1)!important;
  border-radius:12px!important;color:#E2E8F0!important;
  font-size:14px!important;line-height:1.6!important;
}
.stTextArea textarea:focus{border-color:rgba(139,92,246,.5)!important;box-shadow:0 0 0 3px rgba(139,92,246,.1)!important}

.stTextInput input{
  background:rgba(255,255,255,.04)!important;
  border:1px solid rgba(255,255,255,.1)!important;
  border-radius:10px!important;color:#E2E8F0!important;font-size:13px!important;
}

[data-testid="stSidebar"]{background:rgba(8,8,18,.97)!important;border-right:1px solid rgba(255,255,255,.06)!important}
label{color:#94A3B8!important;font-size:13px!important;font-weight:500!important}
.stSlider [data-baseweb="slider"] [data-testid="stThumb"]{background:#7C3AED!important}

.moment-card{
  background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-radius:16px;padding:1.5rem;margin-bottom:1.25rem;
  position:relative;overflow:hidden;transition:border-color .2s,transform .2s;
}
.moment-card:hover{border-color:rgba(139,92,246,.4);transform:translateY(-2px)}
.moment-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#7C3AED,#4F46E5,#60A5FA);opacity:.7;
}
.hook-headline{
  font-size:1.15rem;font-weight:700;line-height:1.35;
  background:linear-gradient(135deg,#F8FAFC,#A78BFA);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;margin-bottom:.75rem;padding-bottom:.75rem;
  border-bottom:1px solid rgba(255,255,255,.07);
}
.hook-badge{
  display:inline-block;font-size:10px;font-weight:600;
  text-transform:uppercase;letter-spacing:.07em;
  padding:3px 9px;border-radius:20px;
  background:rgba(139,92,246,.15);border:1px solid rgba(139,92,246,.35);
  color:#A78BFA;margin-bottom:8px;
}
.alt-hook{font-size:12px;color:#475569;font-style:italic;margin-top:4px}
.moment-quote{
  font-size:14px;line-height:1.7;color:#CBD5E1;
  padding:.75rem 1rem;background:rgba(255,255,255,.03);
  border-left:3px solid rgba(139,92,246,.5);border-radius:0 8px 8px 0;margin:.75rem 0;
}
.reason-box{
  background:rgba(96,165,250,.05);border:1px solid rgba(96,165,250,.12);
  border-radius:10px;padding:.75rem 1rem;margin:.75rem 0;
}
.reason-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#60A5FA;margin-bottom:5px}
.reason-text{font-size:13px;line-height:1.6;color:#94A3B8}
.emotion-pill{
  display:inline-block;font-size:12px;font-weight:600;
  padding:4px 12px;border-radius:20px;
  background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.25);color:#A78BFA;
}
.vbar-row{display:flex;align-items:center;gap:10px;margin-top:.75rem}
.vbar-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#475569;min-width:90px}
.vbar-outer{flex:1;height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden}
.vbar-inner{height:100%;border-radius:3px;background:linear-gradient(90deg,#7C3AED,#A78BFA)}
.vbar-val{font-size:12px;font-weight:700;color:#A78BFA;min-width:28px;text-align:right}
.card-num{position:absolute;top:1.2rem;right:1.2rem;font-size:11px;font-weight:700;color:rgba(167,139,250,.3)}
.ts-hint{display:inline-block;font-size:11px;color:#475569;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);padding:2px 9px;border-radius:6px;margin-bottom:.5rem}

.results-hdr{text-align:center;margin:2rem 0 1.5rem}
.results-title{font-size:1.5rem;font-weight:700;color:#F1F5F9;margin-bottom:6px}
.results-sub{font-size:13px;color:#64748B}

.err-box{background:rgba(220,38,38,.08);border:1px solid rgba(220,38,38,.25);border-radius:10px;padding:1rem 1.25rem;color:#FCA5A5;font-size:14px;margin:1rem 0}
.info-box{background:rgba(96,165,250,.07);border:1px solid rgba(96,165,250,.2);border-radius:10px;padding:1rem 1.25rem;color:#93C5FD;font-size:14px;margin:1rem 0}
.ok-box{background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.25);border-radius:10px;padding:.75rem 1.25rem;color:#6EE7B7;font-size:13px;margin:.5rem 0}

hr{border:none;border-top:1px solid rgba(255,255,255,.06);margin:1.5rem 0}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 .5rem">
      <div style="font-size:2rem">⚡</div>
      <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9">AttentionX</div>
      <div style="font-size:11px;color:#4B5563;margin-top:2px">AI Moment Extractor</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    env_key     = os.environ.get("GROQ_API_KEY", "")
    api_key_raw = st.text_input(
        "Groq API Key",
        value=env_key,
        type="password",
        placeholder="Paste your Groq key here",
        help="Free key from console.groq.com — no credit card needed",
    )
    api_key = api_key_raw.strip().replace(" ", "").replace("\n", "").replace("\r", "")

    if api_key:
        st.markdown(
            f'<div style="font-size:12px;color:#6B7280;margin-top:2px">'
            f'Key length: {len(api_key)} chars</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Paste your Groq API key above", icon="⚠️")
        st.markdown("[Get free key → console.groq.com](https://console.groq.com)")

    # ── Backup key ──
    api_key2_raw = st.text_input(
        "Backup Groq Key (optional)",
        value="",
        type="password",
        placeholder="2nd key for quota fallback",
        help="Auto-used if primary key hits rate limit",
    )
    api_key2 = api_key2_raw.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    set_fallback_keys([api_key2] if api_key2 else [])
    if api_key2:
        st.markdown(
            f'<div style="font-size:12px;color:#6B7280;margin-top:2px">'
            f'Backup key loaded ({len(api_key2)} chars) ✓</div>',
            unsafe_allow_html=True,
        )

    # ── Test Key button ──
    if api_key:
        if st.button("🔍 Test API Key", use_container_width=True):
            with st.spinner("Testing key..."):
                valid, msg = test_api_key(api_key)
                st.session_state.key_tested = True
                st.session_state.key_valid  = valid
                st.session_state.key_msg    = msg

        if st.session_state.key_tested:
            if st.session_state.key_valid:
                st.markdown('<div class="ok-box">✅ Key works perfectly!</div>', unsafe_allow_html=True)
            else:
                msg = st.session_state.get("key_msg", "")
                if "429" in msg or "rate limit" in msg.lower():
                    st.markdown('<div class="err-box">⏳ Key valid but rate limited. Add a backup key below.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="err-box">❌ Key failed: {msg[:120]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    num_moments = st.slider("Moments to extract", 1, 5, 3, help="3 is ideal for speed")
    st.markdown("---")
    st.markdown("""
    <div style="font-size:12px;color:#374151;line-height:1.8">
      <b style="color:#6B7280">How it works:</b><br>
      1. Paste any long content<br>
      2. Groq AI finds the best moments<br>
      3. AI writes hook headlines<br>
      4. Copy and post!
    </div>""", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 1rem 1rem">
  <div style="display:inline-block;background:rgba(139,92,246,.15);border:1px solid rgba(139,92,246,.4);
  color:#A78BFA;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  padding:4px 14px;border-radius:20px;margin-bottom:14px">⚡ Powered by Groq + LLaMA 3.1</div>
  <div style="font-size:clamp(2rem,5vw,3.2rem);font-weight:700;
  background:linear-gradient(135deg,#FFF,#A78BFA,#60A5FA);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;line-height:1.2;margin-bottom:10px">
    Find Your Viral Moments.<br>Instantly.
  </div>
  <div style="font-size:1rem;color:#94A3B8;max-width:500px;margin:0 auto;line-height:1.6">
    Paste any lecture, podcast, or article.
    Get scroll-stopping hook headlines in under 10 seconds.
  </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")


# ── Input area ────────────────────────────────────────────────────────────────
col_text, col_btns = st.columns([3, 1])

with col_btns:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("📋 Load Sample", use_container_width=True):
        st.session_state.content    = SAMPLE
        st.session_state.results    = []
        st.session_state.last_error = ""
        st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.content    = ""
        st.session_state.results    = []
        st.session_state.last_error = ""
        st.session_state.key_tested = False
        st.rerun()

    if st.session_state.content:
        n  = len(st.session_state.content)
        wc = format_word_count(st.session_state.content)
        c  = "#34D399" if n >= 200 else "#FCA5A5"
        st.markdown(
            f"<div style='font-size:11px;color:{c};margin-top:10px;line-height:1.7'>"
            f"📝 {wc}<br>{n:,} chars"
            f"{'  ✓' if n >= 200 else '  (need 200+)'}</div>",
            unsafe_allow_html=True,
        )

with col_text:
    new_text = st.text_area(
        "Content",
        value=st.session_state.content,
        height=250,
        placeholder="Paste a lecture, podcast transcript, article, or any long text (min 200 characters)...",
        label_visibility="collapsed",
    )
    st.session_state.content = new_text


# ── Extract button ────────────────────────────────────────────────────────────
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
btn_col, _ = st.columns([1, 2])
with btn_col:
    extract_clicked = st.button("⚡ Extract Moments", use_container_width=True)


# ── Processing ────────────────────────────────────────────────────────────────
if extract_clicked:
    st.session_state.results    = []
    st.session_state.last_error = ""
    content = st.session_state.content.strip()

    if not content:
        st.session_state.last_error = "no_content"
    elif not api_key:
        st.session_state.last_error = "no_key"
    elif len(content) < 200:
        st.session_state.last_error = f"too_short:{len(content)}"
    else:
        cleaned   = clean_text(content)
        prog_slot = st.empty()
        bar_slot  = st.empty()

        steps = [
            "Reading content...",
            "Connecting to Groq AI...",
            "Finding emotional peaks...",
            "Extracting top moments...",
            "Generating hook headlines...",
            "Almost done...",
        ]

        try:
            bar = bar_slot.progress(0)
            for i, s in enumerate(steps[:3]):
                prog_slot.markdown(
                    f"<div style='text-align:center;color:#94A3B8;font-size:14px;padding:.5rem'>"
                    f"⚙️ {s}</div>", unsafe_allow_html=True)
                bar.progress(int((i + 1) / len(steps) * 100))
                time.sleep(0.3)

            t0      = time.time()
            results = process_content(cleaned, num_moments, api_key)
            elapsed = round(time.time() - t0, 1)

            for i, s in enumerate(steps[3:], 3):
                prog_slot.markdown(
                    f"<div style='text-align:center;color:#A78BFA;font-size:14px;padding:.5rem'>"
                    f"✨ {s}</div>", unsafe_allow_html=True)
                bar.progress(int((i + 1) / len(steps) * 100))
                time.sleep(0.2)

            prog_slot.empty()
            bar_slot.empty()

            st.session_state.results    = results
            st.session_state.elapsed    = elapsed
            st.session_state.last_error = ""

        except Exception as e:
            prog_slot.empty()
            bar_slot.empty()
            raw_err = str(e)

            if raw_err.startswith("bad_key:"):
                st.session_state.last_error = "bad_key"
            elif raw_err.startswith("quota:"):
                st.session_state.last_error = "quota"
            elif raw_err.startswith("no_key:"):
                st.session_state.last_error = "no_key"
            elif "json_parse" in raw_err or "json" in raw_err.lower():
                st.session_state.last_error = "json_parse"
            else:
                st.session_state.last_error = f"generic:{raw_err}"


# ── Error display ─────────────────────────────────────────────────────────────
ERR = st.session_state.last_error
if ERR:
    if ERR == "no_content":
        st.markdown("""<div class="info-box">
          💡 <b>No content yet.</b> Click <b>📋 Load Sample</b> to try the demo,
          or paste your own text in the box.
        </div>""", unsafe_allow_html=True)

    elif ERR == "no_key":
        st.markdown("""<div class="err-box">
          🔑 <b>No API key.</b> Paste your Groq key in the sidebar.<br>
          <a href="https://console.groq.com" style="color:#FCA5A5">
          Get a free key at console.groq.com →</a>
        </div>""", unsafe_allow_html=True)

    elif ERR.startswith("too_short"):
        n = ERR.split(":")[1]
        st.markdown(f"""<div class="err-box">
          📏 <b>Too short</b> ({n} chars). Need at least 200.<br>
          Try <b>📋 Load Sample</b> to see it working.
        </div>""", unsafe_allow_html=True)

    elif ERR == "bad_key":
        st.markdown("""<div class="err-box">
          🔑 <b>API key rejected.</b><br><br>
          Steps to fix:<br>
          &nbsp;&nbsp;1. Go to <a href="https://console.groq.com" style="color:#FCA5A5">console.groq.com</a><br>
          &nbsp;&nbsp;2. Click <b>API Keys → Create API Key</b><br>
          &nbsp;&nbsp;3. Copy the full key and paste fresh in the sidebar<br>
          &nbsp;&nbsp;4. Click <b>🔍 Test API Key</b> to verify
        </div>""", unsafe_allow_html=True)

    elif ERR == "quota":
        st.markdown("""<div class="err-box">
          ⏳ <b>Rate limit hit.</b><br><br>
          Quick fixes:<br>
          &nbsp;&nbsp;• Wait 30 seconds and click Extract again<br>
          &nbsp;&nbsp;• Add a <b>Backup Groq Key</b> in the sidebar<br>
          &nbsp;&nbsp;• <a href="https://console.groq.com" style="color:#FCA5A5">
            Create a new key</a> at console.groq.com<br>
          &nbsp;&nbsp;• Reduce "Moments to extract" to 2
        </div>""", unsafe_allow_html=True)

    elif ERR == "json_parse":
        st.markdown("""<div class="err-box">
          🔄 <b>Unexpected response format.</b>
          Click <b>⚡ Extract Moments</b> again — usually works on retry.
        </div>""", unsafe_allow_html=True)

    else:
        detail = ERR.replace("generic:", "")
        st.markdown(f"""<div class="err-box">
          ❌ <b>Error:</b> {detail[:300]}<br>
          Try again or reload the page (F5).
        </div>""", unsafe_allow_html=True)


# ── Results ───────────────────────────────────────────────────────────────────
def render_card(m: dict, idx: int):
    virality = m.get("virality_score", 7)
    emotion  = m.get("emotion_tag", "Curiosity")
    hook     = m.get("hook", "Hook not generated.")
    alt      = m.get("secondary_hook", "")
    htype    = get_hook_type_label(m.get("hook_type", "unknown"))
    text     = m.get("moment_text", "")
    reason   = m.get("reason", "")
    ts       = m.get("timestamp_hint", "").title()
    pct      = int(virality * 10)

    st.markdown(f"""
    <div class="moment-card">
      <span class="card-num">#{idx:02d}</span>
      <div><span class="ts-hint">📍 {ts}</span></div>
      <div><span class="hook-badge">{htype}</span></div>
      <div class="hook-headline">"{hook}"</div>
      {f'<div class="alt-hook">Alt: &quot;{alt}&quot;</div>' if alt else ''}
      <div class="moment-quote">{text}</div>
      <div class="reason-box">
        <div class="reason-label">🔍 Why this works</div>
        <div class="reason-text">{reason}</div>
      </div>
      <div style="margin-top:.75rem"><span class="emotion-pill">✦ {emotion}</span></div>
      <div class="vbar-row">
        <span class="vbar-label">Virality Score</span>
        <div class="vbar-outer"><div class="vbar-inner" style="width:{pct}%"></div></div>
        <span class="vbar-val">{virality}/10</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


if st.session_state.results:
    results  = st.session_state.results
    elapsed  = st.session_state.elapsed
    avg_v    = round(sum(m.get("virality_score", 7) for m in results) / len(results), 1)
    sorted_r = sorted(results, key=lambda x: x.get("virality_score", 0), reverse=True)

    st.markdown(f"""
    <div class="results-hdr">
      <div class="results-title">✦ {len(results)} Attention-Worthy Moments Found</div>
      <div class="results-sub">Completed in {elapsed}s · Sorted by virality score</div>
    </div>""", unsafe_allow_html=True)

    for pair in [sorted_r[i:i+2] for i in range(0, len(sorted_r), 2)]:
        cols = st.columns(len(pair))
        for col, moment in zip(cols, pair):
            with col:
                render_card(moment, moment.get("id", 1))

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    for col, val, lbl, clr in [
        (c1, avg_v,         "Avg Virality",  "#A78BFA"),
        (c2, len(results),  "Moments Found", "#60A5FA"),
        (c3, f"{elapsed}s", "Total Time",    "#34D399"),
    ]:
        with col:
            st.markdown(f"""
            <div style="text-align:center;background:rgba(255,255,255,.03);
            border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
              <div style="font-size:1.5rem;font-weight:700;color:{clr}">{val}</div>
              <div style="font-size:11px;color:#374151;text-transform:uppercase;
              letter-spacing:.06em;margin-top:2px">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    with st.expander("📋 Copy-ready hooks"):
        st.code("\n\n".join([
            f"#{i+1} | {m.get('emotion_tag','')} | {m.get('virality_score','')}/10\n"
            f"HOOK:  {m.get('hook','')}\n"
            f"ALT:   {m.get('secondary_hook','')}\n"
            f"WHY:   {m.get('reason','')}"
            for i, m in enumerate(sorted_r)
        ]), language=None)

    if st.button("🔄 Start Over"):
        st.session_state.results    = []
        st.session_state.content    = ""
        st.session_state.last_error = ""
        st.rerun()

elif not ERR:
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem">
      <div style="font-size:3rem;margin-bottom:1rem">⚡</div>
      <div style="font-size:1rem;font-weight:600;color:#334155;margin-bottom:8px">
        Ready to find your viral moments
      </div>
      <div style="font-size:13px;color:#1E293B;max-width:360px;margin:0 auto;line-height:1.7">
        Click <b style="color:#7C3AED">📋 Load Sample</b> to try the demo,
        or paste your own text and hit
        <b style="color:#7C3AED">⚡ Extract Moments</b>.
      </div>
    </div>""", unsafe_allow_html=True)