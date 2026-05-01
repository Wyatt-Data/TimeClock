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
