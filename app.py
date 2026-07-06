import streamlit as st
from datetime import datetime, date
import math

# ─────────────────────────────────────────────
#  ENGINE
# ─────────────────────────────────────────────

def military_to_dec(x) -> float:
    """Convert military-time integer to decimal hours with 15-min rounding."""
    try:
        x = int(x)
    except (TypeError, ValueError):
        return 0.0
    if x <= 0:
        return 0.0
    h = x // 100
    m = x % 100
    if m > 59:
        return 0.0  # invalid minutes
    rem = m % 15
    m = m - rem if rem <= 7 else m + (15 - rem)
    if m >= 60:
        h += 1
        m = 0
    return h + (m / 60)


def format_mili_time(dec: float) -> str:
    """Convert decimal hours to HH:MM string."""
    if math.isinf(dec) or dec <= 0:
        return "00:00"
    h = math.floor(dec)
    m = round((dec - h) * 60)
    if m >= 60:
        h += 1
        m = 0
    return f"{int(h):02d}:{int(m):02d}"


def validate_military(val, field_name: str) -> tuple[float, str | None]:
    """Return (decimal_hours, error_message_or_None)."""
    try:
        v = int(val)
    except (TypeError, ValueError):
        return 0.0, f"{field_name}: must be a number (e.g. 0830)"
    if v < 0:
        return 0.0, f"{field_name}: cannot be negative"
    if v > 2359:
        return 0.0, f"{field_name}: cannot exceed 2359"
    mins = v % 100
    if mins > 59:
        return 0.0, f"{field_name}: minutes portion '{mins}' is invalid (00–59)"
    return military_to_dec(v), None


def calc_day_hours(s1, e1, s2, e2) -> tuple[float, list[str]]:
    """Calculate hours for one day; returns (hours, [errors])."""
    errors = []
    ds1, err = validate_military(s1, "Entry");        errors += [err] if err else []
    de1, err = validate_military(e1, "Break Start");  errors += [err] if err else []
    ds2, err = validate_military(s2, "Break End");    errors += [err] if err else []
    de2, err = validate_military(e2, "Exit");         errors += [err] if err else []

    if not errors:
        if de1 > 0 and ds1 > 0 and de1 < ds1:
            errors.append("Break Start cannot be before Entry")
        if ds2 > 0 and de1 > 0 and ds2 < de1:
            errors.append("Break End cannot be before Break Start")
        if de2 > 0 and ds1 > 0 and de2 < ds1:
            errors.append("Exit cannot be before Entry")

    if errors:
        return 0.0, errors

    if de1 == 0 and ds2 == 0 and de2 > ds1:
        return de2 - ds1, []
    return max(0, de1 - ds1) + max(0, de2 - ds2), []


# ─────────────────────────────────────────────
#  CREW CONFIGS
# ─────────────────────────────────────────────

CREW_CONFIGS = {
    "Mon–Thu": ["Mon", "Tue", "Wed", "Thu"],
    "Tue–Fri": ["Tue", "Wed", "Thu", "Fri"],
    "Mon–Fri": ["Mon", "Tue", "Wed", "Thu", "Fri"],
}

PACE_EXPECTED = {0: 10, 1: 20, 2: 30, 3: 40, 4: 40, 5: 40, 6: 40}

DAY_LABELS = {
    "Mon": "MONDAY", "Tue": "TUESDAY", "Wed": "WEDNESDAY",
    "Thu": "THURSDAY", "Fri": "FRIDAY"
}
DAY_ICONS = {
    "Mon": "🌑", "Tue": "🌒", "Wed": "🌓", "Thu": "🌔", "Fri": "🌕"
}

DEFAULT_START = 700

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="ENTROPY ZERO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────

if "crew" not in st.session_state:
    st.session_state["crew"] = "Mon–Thu"
if "reset_trigger" not in st.session_state:
    st.session_state["reset_trigger"] = 0

ALL_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

DEFAULT_E2 = {"Mon": 0, "Tue": 1700, "Wed": 1700, "Thu": 1700, "Fri": 0}


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

    st.session_state["crew"] = "Mon–ThU"
    st.session_state["reset_trigger"] = 0

    st.rerun()

# ─────────────────────────────────────────────
#  GLOBAL CSS  (stars + full styling)
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700;800&display=swap');

/* ── Reset & Base ─────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Orbitron', sans-serif;
    color: #e0e0e0;
}

/* ─────────────────────────────────────────────
   COSMIC NEBULA SCENE (FOCUSED VIEWPORT)
──────────────────────────────────────────── */

.stApp {
    background: radial-gradient(ellipse at bottom, #02030a 0%, #000000 100%);
    overflow: hidden;
}

/* ── Nebula haze layer (purple / blue / orange) ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: -20%;
    background:
        radial-gradient(circle at 30% 40%, rgba(140, 0, 255, 0.18), transparent 45%),
        radial-gradient(circle at 60% 30%, rgba(0, 180, 255, 0.14), transparent 50%),
        radial-gradient(circle at 55% 70%, rgba(255, 120, 0, 0.10), transparent 55%),
        radial-gradient(circle at 40% 60%, rgba(255, 255, 255, 0.05), transparent 60%);
    filter: blur(40px);
    opacity: 0.9;
    animation: nebulaPulse 12s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

@keyframes nebulaPulse {
    0%   { transform: scale(1) translateY(0px); opacity: 0.75; }
    50%  { transform: scale(1.05) translateY(-10px); opacity: 0.95; }
    100% { transform: scale(1.02) translateY(5px); opacity: 0.85; }
}

/* ── Star field (subtle shimmer) ── */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        radial-gradient(1px 1px at 15% 20%, rgba(255,255,255,0.9), transparent 60%),
        radial-gradient(1px 1px at 25% 70%, rgba(180,220,255,0.7), transparent 60%),
        radial-gradient(1px 1px at 40% 30%, rgba(255,255,255,0.6), transparent 60%),
        radial-gradient(1px 1px at 65% 60%, rgba(200,180,255,0.7), transparent 60%),
        radial-gradient(1px 1px at 80% 25%, rgba(255,255,255,0.5), transparent 60%),
        radial-gradient(1px 1px at 90% 80%, rgba(255,255,255,0.8), transparent 60%);
    opacity: 0.55;
    animation: starTwinkle 6s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

@keyframes starTwinkle {
    0%   { opacity: 0.35; filter: brightness(0.9); }
    50%  { opacity: 0.7;  filter: brightness(1.3); }
    100% { opacity: 0.5; }
}

/* ── Individual shimmering stars layer ── */
.star-pulse {
    position: fixed;
    width: 2px;
    height: 2px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(255,255,255,0.8);
    animation: pulseStar 3s ease-in-out infinite;
    z-index: 0;
}

@keyframes pulseStar {
    0%   { transform: scale(0.8); opacity: 0.4; }
    50%  { transform: scale(1.6); opacity: 1; }
    100% { transform: scale(0.9); opacity: 0.5; }
}

.stars-upper-right {
    position: fixed;
    top: 0;
    right: 0;
    width: 55vw;
    height: 55vh;
    pointer-events: none;
    z-index: 0;

    background:
    /* subtle dark void base tint */
    radial-gradient(circle at 20% 25%, rgba(10,10,20,0.35), transparent 60%),

    /* small star shapes (≤20px) */
    radial-gradient(12px 12px at 12% 18%, rgba(255,255,255,0.9), transparent 70%),
    radial-gradient(10px 10px at 28% 32%, rgba(180,220,255,0.75), transparent 70%),
    radial-gradient(14px 14px at 42% 20%, rgba(200,180,255,0.6), transparent 75%),
    radial-gradient(8px 8px at 55% 38%, rgba(255,255,255,0.7), transparent 70%),
    radial-gradient(10px 10px at 70% 22%, rgba(170,200,255,0.6), transparent 72%),
    radial-gradient(6px 6px at 82% 45%, rgba(255,255,255,0.8), transparent 70%),

    /* faint color hints (kept dark, no glow expansion) */
    radial-gradient(18px 18px at 25% 55%, rgba(90,0,160,0.10), transparent 80%),
    radial-gradient(16px 16px at 60% 60%, rgba(0,120,200,0.08), transparent 82%),
    radial-gradient(14px 14px at 75% 30%, rgba(255,120,0,0.06), transparent 85%);

    opacity: 0.75;
    animation: starTwinkle 5s ease-in-out infinite alternate;
}

/* ── Shooting stars (rare, diagonal sweep) ── */
.shooting-star {
    position: fixed;
    top: 10%;
    left: -20%;
    width: 2px;
    height: 2px;
    background: linear-gradient(90deg, white, rgba(255,255,255,0));
    box-shadow: 0 0 12px white, 0 0 25px rgba(120,180,255,0.8);
    transform: rotate(25deg);
    animation: shootAcross 10s linear infinite;
    opacity: 0;
    z-index: 0;
}

.shooting-star:nth-child(1) { animation-delay: 3s; top: 20%; }
.shooting-star:nth-child(2) { animation-delay: 8s; top: 35%; }
.shooting-star:nth-child(3) { animation-delay: 14s; top: 15%; }

@keyframes shootAcross {
    0%   { transform: translate(0,0) rotate(25deg); opacity: 0; }
    5%   { opacity: 1; }
    100% { transform: translate(140vw, 60vh) rotate(25deg); opacity: 0; }
}

/* ── Faint moon horizon ── */
.moon {
    position: fixed;

    /* move it much lower so it only peeks in */
    bottom: -420px;
    left: -420px;

    width: 900px;
    height: 900px;

    border-radius: 50%;
    z-index: 0;

    /* no scaling tricks anymore */
    transform: none;

    /* muted lunar base (no orange/yellow) */
    background:
        radial-gradient(circle at 35% 30%,
            rgba(235,235,235,0.95) 0%,
            rgba(200,200,200,0.85) 18%,
            rgba(150,150,150,0.55) 40%,
            rgba(90,90,90,0.35) 65%,
            rgba(0,0,0,0) 100%);

    filter: contrast(1.1) brightness(0.95);

    box-shadow:
        0 0 120px rgba(180,180,180,0.08),
        0 0 240px rgba(120,120,120,0.05);
}

/* subtle mare + crater shading (low contrast, no “dots”) */
.moon::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 50%;

    background:
        radial-gradient(circle at 28% 40%, rgba(80,80,80,0.35), transparent 35%),
        radial-gradient(circle at 60% 55%, rgba(70,70,70,0.30), transparent 40%),
        radial-gradient(circle at 70% 30%, rgba(90,90,90,0.28), transparent 38%),
        radial-gradient(circle at 45% 65%, rgba(60,60,60,0.25), transparent 45%),
        radial-gradient(circle at 55% 35%, rgba(100,100,100,0.18), transparent 40%);

    opacity: 0.75;
    mix-blend-mode: multiply;
}

/* limb shadow = realism (space-side fade) */
.moon::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 50%;

    background: radial-gradient(circle at 35% 40%,
        transparent 50%,
        rgba(0,0,0,0.55) 100%);

    opacity: 0.7;
}

/* ── Streamlit chrome removal ─────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    position: relative;
    z-index: 1;
}

/* ── Main title ─────────────────────────── */
.main-title {
    font-family: 'Orbitron', sans-serif;
    background: linear-gradient(180deg, #ffffff 0%, #00F2FF 45%, #7000FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 900;
    font-size: clamp(3rem, 8vw, 5.5rem);
    letter-spacing: -3px;
    margin: 0;
    text-align: center;
    filter: drop-shadow(0 0 30px rgba(0,242,255,0.5));
    line-height: 1;
}
.sub-title {
    text-align: center;
    letter-spacing: 8px;
    color: #ffffff;
    font-size: 0.7rem;
    font-weight: bold;
    margin-top: 0.4rem;
    margin-bottom: 0.25rem;
    font-family: 'JetBrains Mono', monospace;
}
.title-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,242,255,0.4), transparent);
    margin: 1rem auto 1.5rem auto;
    width: 60%;
}

/* ── Crew selector buttons ─────────────── */
.crew-btn-row {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-bottom: 1.5rem;
}

/* ── Cards ─────────────────────────────── */
.ez-card {
    background: rgba(2, 10, 22, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(0,242,255,0.12);
    border-radius: 16px;
    box-shadow:
        0 8px 40px rgba(0,0,0,0.7),
        inset 0 1px 0 rgba(0,242,255,0.08),
        inset 0 0 20px rgba(0,242,255,0.03);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.ez-card-header {
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 3px;
    font-size: 0.65rem;
    font-weight: 900;
    border-bottom: 1px solid rgba(0,242,255,0.1);
    padding-bottom: 0.6rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Big departure time ─────────────────── */
.big-time-wrapper {
    text-align: center;
    padding: 1rem 0;
    position: relative;
}
.big-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: clamp(4rem, 10vw, 7rem);
    font-weight: 800;
    color: #00F2FF;
    text-shadow:
        0 0 30px rgba(0,242,255,0.9),
        0 0 80px rgba(0,242,255,0.4),
        0 0 120px rgba(0,242,255,0.2);
    line-height: 1;
    letter-spacing: -2px;
}
.big-time-label {
    font-size: 0.6rem;
    color: #ffffff;
    letter-spacing: 4px;
    margin-top: 6px;
}

/* ── Nerd stats ─────────────────────────── */
.stat-card {
    background: rgba(0,5,15,0.6);
    border: 1px solid rgba(0,242,255,0.1);
    border-radius: 12px;
    padding: 1rem 0.75rem;
    text-align: center;
    transition: border-color 0.3s ease;
}
.stat-card:hover { border-color: rgba(0,242,255,0.3); }
.nerd-label {
    font-size: 0.58rem;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
}
.nerd-val {
    font-family: 'JetBrains Mono', monospace;
    color: #FF00E5;
    font-size: 1.15rem;
    font-weight: 800;
    text-shadow: 0 0 15px rgba(255,0,229,0.5);
    line-height: 1.2;
}
.nerd-val-cyan {
    font-family: 'JetBrains Mono', monospace;
    color: #00F2FF;
    font-size: 1.15rem;
    font-weight: 800;
    text-shadow: 0 0 15px rgba(0,242,255,0.5);
}
.nerd-val-green {
    font-family: 'JetBrains Mono', monospace;
    color: #00FF88;
    font-size: 1.15rem;
    font-weight: 800;
    text-shadow: 0 0 15px rgba(0,255,136,0.5);
}
.nerd-val-warn {
    font-family: 'JetBrains Mono', monospace;
    color: #FFC107;
    font-size: 1.0rem;
    font-weight: 800;
    text-shadow: 0 0 15px rgba(255,193,7,0.5);
}

/* ── Banners ────────────────────────────── */
.banner-active {
    background: linear-gradient(90deg, #7000FF 0%, #FFC107 50%, #7000FF 100%);
    background-size: 200% auto;
    animation: shine 3s linear infinite;
    padding: 22px 30px;
    border-radius: 14px;
    text-align: center;
    color: #000;
    font-weight: 900;
    font-size: 1.4rem;
    letter-spacing: 2px;
    box-shadow: 0 0 50px rgba(255,193,7,0.3), 0 0 100px rgba(112,0,255,0.2);
    margin-bottom: 1.2rem;
}
@keyframes shine { to { background-position: 200% center; } }

.status-box {
    background: rgba(0,242,255,0.03);
    padding: 16px 24px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 1.2rem;
    border: 1px dashed rgba(0,242,255,0.2);
    color: #00F2FF;
    text-shadow: 0 0 10px rgba(0,242,255,0.4);
    font-size: 0.8rem;
    letter-spacing: 3px;
}

/* ── Error / warning boxes ──────────────── */
.error-box {
    background: rgba(220,53,69,0.1);
    border: 1px solid rgba(220,53,69,0.4);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.7rem;
    color: #ff6b7a;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.5px;
}
.warning-box {
    background: rgba(255,193,7,0.08);
    border: 1px solid rgba(255,193,7,0.3);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.7rem;
    color: #FFC107;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Progress ───────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #00F2FF, #7000FF) !important;
    box-shadow: 0 0 20px rgba(0,242,255,0.6);
    border-radius: 10px !important;
}
.stProgress > div > div {
    background: rgba(0,0,0,0.5) !important;
    border: 1px solid rgba(0,242,255,0.15);
    border-radius: 10px !important;
    height: 12px !important;
}

/* Over-target animations */
@keyframes high-voltage-sheen {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes neon-surge {
    0%   { box-shadow: 0 0 10px #ff0000, inset 0 0 5px #7a0000; }
    50%  { box-shadow: 0 0 50px #ff3333, inset 0 0 20px #ff0000; filter: brightness(1.3); }
    100% { box-shadow: 0 0 10px #ff0000, inset 0 0 5px #7a0000; }
}
.progress-over .stProgress > div > div {
    animation: neon-surge 2s ease-in-out infinite !important;
    background: #150000 !important;
    border: 1px solid #ff0000 !important;
}
.progress-over .stProgress > div > div > div > div {
    background: linear-gradient(90deg, #7a0000 0%, #ff0000 45%, #ffcccc 50%, #ff0000 55%, #7a0000 100%) !important;
    background-size: 400% 400% !important;
    animation: high-voltage-sheen 2.5s linear infinite !important;
    box-shadow: none !important;
}

/* ── Inputs ─────────────────────────────── */
input[type="number"] {
    background: rgba(0,242,255,0.04) !important;
    border: 1px solid rgba(0,242,255,0.15) !important;
    border-radius: 8px !important;
    color: #c8e8ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
input[type="number"]:focus {
    border-color: rgba(0,242,255,0.5) !important;
    box-shadow: 0 0 12px rgba(0,242,255,0.2) !important;
}
.stTextInput input, .stNumberInput input {
    background: rgba(0,242,255,0.04) !important;
}
label {
    font-size: 0.62rem !important;
    letter-spacing: 2px !important;
    color: #ffffff !important;
    text-transform: uppercase !important;
}

/* ── Expanders ───────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(0,242,255,0.06) !important;
    border: 1px solid rgba(255,193,7,0.15) !important;
    border-radius: 10px !important;
    font-size: 0.75rem !important;
    letter-spacing: 2px !important;
    color: #FFC107 !important;
    font-family: 'Orbitron', sans-serif !important;
    transition: background 0.2s ease !important;
}
.streamlit-expanderHeader:hover {
    background: rgba(0,242,255,0.1) !important;
}
.streamlit-expanderContent {
    background: rgba(0,8,18,0.5) !important;
    border: 1px solid rgba(255,193,7,0.1) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 0.75rem !important;
}

/* ── Buttons ─────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid rgba(220,53,69,0.5) !important;
    color: #ff6b7a !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.65rem !important;
    letter-spacing: 3px !important;
    width: 100% !important;
    border-radius: 10px !important;
    padding: 0.6rem !important;
    transition: all 0.25s ease !important;
}
.stButton > button:hover {
    background: rgba(220,53,69,0.12) !important;
    box-shadow: 0 0 25px rgba(220,53,69,0.3) !important;
    border-color: rgba(220,53,69,0.8) !important;
}

/* Crew buttons */
.crew-button-active > button {
    background: rgba(0,242,255,0.15) !important;
    border-color: #00F2FF !important;
    color: #00F2FF !important;
    box-shadow: 0 0 20px rgba(0,242,255,0.3) !important;
}

/* ── Radio ───────────────────────────────── */
div[role="radiogroup"] {
    gap: 8px !important;
}
div[role="radiogroup"] label {
    background: rgba(0,242,255,0.05) !important;
    border: 1px solid rgba(0,242,255,0.15) !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    color: #FFC107 !important;
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}
div[role="radiogroup"] label:has(input:checked) {
    background: rgba(255,193,7,0.15) !important;
    border-color: #FFC107 !important;
    box-shadow: 0 0 12px rgba(255,193,7,0.2) !important;
}

/* ── Checkbox ─────────────────────────────── */
.stCheckbox label {
    color: #a0b0c0 !important;
    font-size: 0.68rem !important;
    letter-spacing: 1px !important;
    text-transform: none !important;
}

/* ── Scrollbar ─────────────────────────────  */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #020408; }
::-webkit-scrollbar-thumb { background: #1a2040; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #00F2FF; }

/* ── Selectbox ─────────────────────────────  */
.stSelectbox > div > div {
    background: rgba(0,242,255,0.05) !important;
    border: 1px solid rgba(0,242,255,0.15) !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
}
</style>

<!-- Nebula orbs -->
<div class="nebula-orb"></div>
<div class="nebula-orb2"></div>
<div class="shooting-star"></div>
<div class="shooting-star"></div>
<div class="shooting-star"></div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="moon"></div>

<div class="shooting-star"></div>
<div class="shooting-star"></div>
<div class="shooting-star"></div>

<div class="star-pulse" style="top:20%; left:30%;"></div>
<div class="star-pulse" style="top:35%; left:60%;"></div>
<div class="star-pulse" style="top:55%; left:40%;"></div>
<div class="star-pulse" style="top:70%; left:75%;"></div>
""", unsafe_allow_html=True)

st.markdown('<div class="stars-upper-right"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────

st.markdown('<h1 class="main-title">ENTROPY ZERO</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">◈ TEMPORAL LOGISTICS SYSTEM v5.0 ◈ TARGET: 40.00H ◈</p>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="title-divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CREW SELECTOR  (centered above columns)
# ─────────────────────────────────────────────

st.markdown(
    '<div style="text-align:center; font-size:0.6rem; color:#ffffff; letter-spacing:4px; '
    'margin-bottom:0.5rem;">SELECT CREW SCHEDULE</div>',
    unsafe_allow_html=True,
)

crew_cols = st.columns([2, 1, 1, 1, 2])
with crew_cols[1]:
    if st.button("🌟  MON – THU", key="btn_monthy"):
        st.session_state["crew"] = "Mon–Thu"
        st.rerun()
with crew_cols[2]:
    if st.button("🌏  MON – FRI", key="btn_monfri"):
        st.session_state["crew"] = "Mon–Fri"
        st.rerun()
with crew_cols[3]:
    if st.button("🌜  TUE – FRI", key="btn_tuefri"):
        st.session_state["crew"] = "Tue–Fri"
        st.rerun()

crew = st.session_state["crew"]
active_days = CREW_CONFIGS[crew]
target_hours = 40.0
work_days_count = len(active_days)
target_per_day = target_hours / work_days_count

# Show active crew badge
crew_color = {"Mon–Thu": "#7000FF", "Mon–Fri": "#00F2FF", "Tue–Fri": "#FFC107"}[crew]
st.markdown(
    f'<div style="text-align:center; margin-bottom:1.2rem;">'
    f'<span style="background:rgba({",".join(str(int(crew_color.lstrip("#")[i:i+2],16)) for i in (0,2,4))},0.15); '
    f'border:1px solid {crew_color}; border-radius:20px; padding:4px 18px; '
    f'font-size:0.65rem; letter-spacing:3px; color:{crew_color}; '
    f'text-shadow:0 0 10px {crew_color};">'
    f'◈ ACTIVE CREW: {crew} ◈ {work_days_count}×{target_per_day:.1f}H SCHEDULE</span></div>',
    unsafe_allow_html=True,
)

st.markdown("<hr style='border-color:rgba(0,242,255,0.06); margin-bottom:1.2rem;'>",
            unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TWO-COLUMN LAYOUT
# ─────────────────────────────────────────────

left_col, right_col = st.columns([1, 1], gap="large")


# ══════════════════════════════════════════════
#  LEFT — INPUT COMMAND CENTER
# ══════════════════════════════════════════════

with left_col:
    st.markdown(
        '<div class="ez-card-header" style="font-size:0.65rem; color:#00F2FF; '
        'letter-spacing:3px; text-transform:uppercase; margin-bottom:1rem;">'
        '⚙ INPUT COMMAND CENTER</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "mode",
        options=["Daily Logs", "Master Total"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown(
        "<hr style='border-color:rgba(0,242,255,0.08); margin:0.75rem 0;'>",
        unsafe_allow_html=True,
    )

    all_errors: dict[str, list[str]] = {}

    # ── DAILY LOGS ─────────────────────────────
    if mode == "Daily Logs":
        today_abbr = date.today().strftime("%a")

        st.markdown(
            f'<div style="font-size:0.58rem; color:#ffffff; letter-spacing:3px; '
            f'text-align:center; margin-bottom:0.75rem;">'
            f'ENTER TIMES IN MILITARY FORMAT  (e.g. 0830, 1700)</div>',
            unsafe_allow_html=True,
        )

        day_hours: dict[str, float] = {}

        for d in active_days:
            is_today = d == today_abbr
            icon = DAY_ICONS.get(d, "⬡")
            label_str = DAY_LABELS.get(d, d)
            expand_label = f"{icon}  {label_str}" + ("  ← TODAY" if is_today else "")

            with st.expander(expand_label, expanded=is_today):
                c1, c2 = st.columns(2)
                with c1:
                    # enforce sane default start time
                    if st.session_state.get(f"{d}_s1", 0) == 0:
                        st.session_state[f"{d}_s1"] = DEFAULT_START

                    s1 = st.number_input(
                        "Entry",
                        value=int(st.session_state.get(f"{d}_s1", DEFAULT_START)),
                        step=100, min_value=0, max_value=2359,
                        key=f"{d}_s1",
                    )
                    s2 = st.number_input(
                        "Break End",
                        value=int(st.session_state.get(f"{d}_s2", 0)),
                        step=100, min_value=0, max_value=2359,
                        key=f"{d}_s2",
                    )
                with c2:
                    e1 = st.number_input(
                        "Break Start",
                        value=int(st.session_state.get(f"{d}_e1", 0)),
                        step=100, min_value=0, max_value=2359,
                        key=f"{d}_e1",
                    )
                    default_exit = DEFAULT_E2.get(d, 1700)
                    if d == active_days[-1]:
                        default_exit = 0
                    e2 = st.number_input(
                        "Exit",
                        value=int(st.session_state.get(f"{d}_e2", default_exit)),
                        step=100, min_value=0, max_value=2359,
                        key=f"{d}_e2",
                    )

                hrs, errs = calc_day_hours(s1, e1, s2, e2)
                day_hours[d] = hrs

                if errs:
                    all_errors[d] = errs
                    for e in errs:
                        st.markdown(
                            f'<div class="error-box">⚠ {e}</div>',
                            unsafe_allow_html=True,
                        )
                elif hrs > 0:
                    st.markdown(
                        f'<div style="text-align:right; font-family:JetBrains Mono; '
                        f'font-size:0.75rem; color:#00FF88; margin-top:4px; '
                        f'text-shadow:0 0 8px rgba(0,255,136,0.4);">'
                        f'✓  {hrs:.2f} H logged</div>',
                        unsafe_allow_html=True,
                    )

        # Days not in active schedule get 0
        for d in ALL_DAYS:
            if d not in active_days:
                day_hours[d] = 0.0

        running_total = sum(day_hours[d] for d in active_days)

        # Friday / last-day exit projection
        last_day = active_days[-1]
        earlier_days = active_days[:-1]
        earlier_total = sum(day_hours[d] for d in earlier_days)
        needed_last = target_hours - earlier_total

        ls1 = st.session_state.get(f"{last_day}_s1", 0)
        le1 = st.session_state.get(f"{last_day}_e1", 0)
        ls2 = st.session_state.get(f"{last_day}_s2", 0)
        fds1 = military_to_dec(ls1)
        fde1 = military_to_dec(le1)
        fds2 = military_to_dec(ls2)
        gap = (fds2 - fde1) if (fds2 > fde1 and fde1 > 0) else 0
        leave_time = format_mili_time(fds1 + needed_last + gap)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("☢ SYSTEM WIPE — CLEAR ALL"):
            st.session_state.clear()
            st.session_state["crew"] = "Mon–Fri"
            st.session_state["reset_trigger"] = 0
            st.rerun()

    # ── MASTER TOTAL ───────────────────────────
    else:
        st.markdown(
            '<div style="font-size:0.58rem; color:#444; letter-spacing:3px; '
            'text-align:center; margin-bottom:1rem;">QUICK CALCULATION MODE</div>',
            unsafe_allow_html=True,
        )

        total_so_far = st.number_input(
            "Prior Logged Hours",
            value=float(st.session_state.get("total_so_far_qt", 30.0)),
            min_value=0.0,
            max_value=80.0,
            step=0.25,
            key="total_so_far_qt",
            help="Total hours logged Mon–Thu (or Mon–Wed for 4-day crews)",
        )

        # Validate total
        if total_so_far < 0:
            st.markdown(
                '<div class="error-box">⚠ Hours cannot be negative</div>',
                unsafe_allow_html=True,
            )
        elif total_so_far > target_hours:
            st.markdown(
                '<div class="warning-box">⚡ Already at or over target hours</div>',
                unsafe_allow_html=True,
            )

        fri_start = st.number_input(
            "Last Day Start (Military Time)",
            value=int(st.session_state.get("fri_start_qt", 700)),
            min_value=0,
            max_value=2359,
            step=100,
            key="fri_start_qt",
            help="e.g. 0700 for 7:00 AM",
        )

        # Validate fri_start
        fs_err = None
        mins_check = fri_start % 100
        if mins_check > 59:
            fs_err = f"Invalid time: minutes '{mins_check}' must be 00–59"
            st.markdown(f'<div class="error-box">⚠ {fs_err}</div>', unsafe_allow_html=True)

        fri_lunch = st.checkbox(
            "Deduct 0.5H Lunch Break",
            value=st.session_state.get("fri_lunch_qt", False),
            key="fri_lunch_qt",
        )

        running_total = max(0.0, total_so_far)
        needed = max(0.0, target_hours - total_so_far)
        start_dec = military_to_dec(fri_start) if not fs_err else 0.0
        lunch = 0.5 if fri_lunch else 0
        leave_time = format_mili_time(start_dec + needed + lunch) if not fs_err else "??:??"

        day_hours = {d: 0.0 for d in ALL_DAYS}
        if work_days_count >= 3:
            per = total_so_far / max(work_days_count - 1, 1)
            for d in active_days[:-1]:
                day_hours[d] = per


# ══════════════════════════════════════════════
#  COMPUTED STATS
# ══════════════════════════════════════════════

hours_left = max(0, target_hours - running_total)
pct = (running_total / target_hours) * 100
pct_capped = min(pct, 100)
is_overage = pct > 100

today_wd = date.today().weekday()
expected_by_now = PACE_EXPECTED.get(today_wd, 40)
actual_diff = (expected_by_now - running_total) - 20
if actual_diff > 0.05:
    pace_str = f"{actual_diff:.1f}H BEHIND"
    pace_class = "nerd-val-warn"
elif actual_diff < -0.05:
    pace_str = f"{abs(actual_diff):.1f}H EARLY"
    pace_class = "nerd-val-green"
else:
    pace_str = "OPTIMAL"
    pace_class = "nerd-val-cyan"


# ══════════════════════════════════════════════
#  RIGHT — ANALYTICS HUD
# ══════════════════════════════════════════════

with right_col:

    # ── Banner ─────────────────────────────────
    today_name = date.today().strftime("%A").upper()
    last_day_of_week = active_days[-1]
    is_last_day = date.today().strftime("%a") == last_day_of_week

    if is_last_day:
        st.markdown(
            f'<div class="banner-active">'
            f'🔥 &nbsp; {last_day_of_week.upper()} EXODUS: DEPART AT {leave_time}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        days_remaining = sum(
            1 for d in active_days
            if ALL_DAYS.index(d) >= today_wd and not is_last_day
        )
        st.markdown(
            f'<div class="status-box">'
            f'🛡 &nbsp; SYSTEM ACTIVE &nbsp;/&nbsp; {today_name} &nbsp;/&nbsp; '
            f'CREW: {crew}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Exit Vector Card ───────────────────────
    st.markdown(
        '<div class="ez-card">'
        '<div class="ez-card-header">🚀 STRATEGIC EXIT VECTOR</div>'
        '<div class="big-time-wrapper">'
        f'<div class="big-time">{leave_time}</div>'
        f'<div class="big-time-label">PROJECTED DEPARTURE // {last_day_of_week.upper()}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Progress bar
    overage_class = "progress-over" if is_overage else ""
    st.markdown(f'<div class="{overage_class}" style="margin:0.5rem 0;">', unsafe_allow_html=True)
    pct_label = f"{pct:.1f}% {'⚡ OVERLOAD' if is_overage else 'complete'}"
    st.progress(pct_capped / 100, text=pct_label)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:0.55rem; color:#ffffff; letter-spacing:2px; '
        'text-align:center; margin-top:4px; margin-bottom:0.5rem;">'
        'ⓘ &nbsp; PROJECTION BASED ON 15-MINUTE ROUNDING ENGINE'
        '</div>'
        '</div>',  # close ez-card
        unsafe_allow_html=True,
    )

    # ── Stat Cards ─────────────────────────────
    s1c, s2c, s3c = st.columns(3)

    with s1c:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="nerd-label">⚡ LOAD</div>'
            f'<div class="nerd-val-cyan">{running_total:.2f} H</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with s2c:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="nerd-label">🕐 REMAINING</div>'
            f'<div class="nerd-val">{hours_left:.2f} H</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with s3c:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="nerd-label">🎯 PACE</div>'
            f'<div class="{pace_class}">{pace_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Error Summary ──────────────────────────
    if all_errors:
        st.markdown(
            '<div class="ez-card">'
            '<div class="ez-card-header" style="color:#ff6b7a;">⚠ INPUT ERRORS DETECTED</div>',
            unsafe_allow_html=True,
        )
        for day_name, errs in all_errors.items():
            for e in errs:
                st.markdown(
                    f'<div class="error-box">[ {day_name.upper()} ] {e}</div>',
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Load Distribution Chart Section (Unified) ────────────────
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import numpy as np
        import io
        import base64

        # 1. Create the Figure
        matplotlib.rcParams["font.family"] = "monospace"
        fig, ax = plt.subplots(figsize=(7, 3.8))
        fig.patch.set_alpha(0)
        ax.set_facecolor((0, 0, 0, 0))

        # Plotting Data
        plot_days = active_days
        vals = [day_hours.get(d, 0) for d in plot_days]
        x = np.arange(len(plot_days))
        bar_w = 0.55

        # Logic for colors
        per_day_target = target_per_day
        bar_colors = []
        for day, hours in zip(plot_days, vals):
        # 8 hours for Mon-Fri schedule, 10 hours for 4-day schedules
            daily_limit = 8 if crew == "Mon–Fri" else 10
        
            if hours < daily_limit:
                color = (0.20, 0.75, 0.85)       # cyan (at or under target)
            elif hours > daily_limit:
                color = (0.95, 0.20, 0.20)      # red (over target)
            else:
                color = (0.15, 0.18, 0.22)    # gray
            bar_colors.append(color)

        # Draw Bars
        ax.bar(x, vals, width=bar_w + 0.15, color="#00F2FF", alpha=0.05) # Glow
        bars = ax.bar(x, vals, width=bar_w, color=bar_colors,
                  edgecolor=bar_colors, linewidth=1.2, alpha=0.9)

        # Value labels - updated to pure white
        for bar, v in zip(bars, vals):
            if v > 0.1:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.08,
                    f"{v:.1f}",
                    ha="center", va="bottom",
                    color="#FFFFFF",  # Pure White text
                    fontsize=8,
                    fontweight="bold" # Added a bit of weight for readability
                )

        # Target line - maybe make this white/grey to stay neutral
        ax.axhline(y=per_day_target, linestyle="--", color="#FFFFFF", alpha=0.4, linewidth=1.0)
       
        # Axis labels - updated to white/cyan for high contrast
        ax.set_xticklabels(
            [DAY_LABELS.get(d, d) for d in plot_days],
            color="#FFFFFF", fontsize=8
        )

        ax.axhline(y=per_day_target, linestyle="--", color="#FEFFC9", alpha=0.7, linewidth=1.2)
        ax.set_xticks(x)
        ax.set_xticklabels([DAY_LABELS.get(d, d) for d in plot_days], color="#00F2FF", fontsize=8)
        ax.set_ylim(0, max(per_day_target * 1.3, max(vals) * 1.15 if vals else 12))
       
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.yaxis.grid(True, color="#0a1520", linewidth=0.8, alpha=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(colors="#334455", length=0)
       
        plt.tight_layout(pad=0.4)

        # 2. Convert Plot to Base64 String
        buf = io.BytesIO()
        fig.savefig(buf, format="png", transparent=True, bbox_inches='tight', dpi=150)
        img_str = base64.b64encode(buf.getvalue()).decode()
        plt.close(fig)

        # 3. Render EVERYTHING inside the HTML Card
        st.markdown(
            f'''
            <div class="ez-card">
                <div class="ez-card-header">〜 LOAD DISTRIBUTION PROFILE</div>
                <div style="display: flex; justify-content: center; padding: 10px 0;">
                    <img src="data:image/png;base64,{img_str}" style="width: 100%; max-width: 650px;">
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    except Exception as chart_err:
        st.markdown(
            f'<div class="ez-card"><div class="warning-box">Chart Error: {chart_err}</div></div>',
            unsafe_allow_html=True
        )

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────

st.markdown(
    '<div style="text-align:center; margin-top:2rem; font-size:0.55rem; '
    'color:#222; letter-spacing:4px; font-family:JetBrains Mono, monospace;">'
    f'ENTROPY ZERO v5.0 &nbsp;◈&nbsp; {date.today().strftime("%Y.%m.%d")} &nbsp;◈&nbsp; '
    f'CREW {crew} &nbsp;◈&nbsp; TARGET {target_hours:.0f}H'
    '</div>',
    unsafe_allow_html=True,
)
