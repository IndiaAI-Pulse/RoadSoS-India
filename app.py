import math
import time
import json
from pathlib import Path
from datetime import datetime
from io import BytesIO
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

try:
    from streamlit_geolocation import streamlit_geolocation
    GEO_OK = True
except Exception:
    GEO_OK = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_OK = True
except Exception:
    AUTOREFRESH_OK = False

try:
    import speech_recognition as sr
    SR_OK = True
except Exception:
    SR_OK = False

st.set_page_config(page_title="RoadSoS India", layout="wide")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CONTACTS_FILE = DATA_DIR / "emergency_contacts.json"

EMERGENCY_NUMBERS = {
    "Unified emergency": "112",
    "Police": "100 / 112",
    "Ambulance": "108",
    "Fire": "101",
}

HIGH_SEVERITY = [
    "crash", "rollover", "unconscious", "not breathing", "bleeding",
    "heavy bleeding", "multiple injuries", "trapped", "fire", "explosion",
    "severe", "critical", "major accident", "major crash", "hit by truck",
    "hit by bus", "hit by car", "serious", "life threatening"
]

MEDIUM_SEVERITY = [
    "injury", "injured", "broken", "fracture", "pain", "cut", "wound",
    "dizziness", "headache", "concussion", "shortness of breath"
]

DATA = [
    {"country":"India","state":"Tamil Nadu","city":"Chennai","place_name":"Government Hospital of Thoracic Medicine","service_type":"Trauma Center","phone":"044 2538 3127","lat":13.0847,"lng":80.2707,"address":"Pattalam Chennai Tamil Nadu","trauma_capable":True},
    {"country":"India","state":"Tamil Nadu","city":"Chennai","place_name":"Rajiv Gandhi Government General Hospital","service_type":"Hospital","phone":"044 2538 1111","lat":13.0800,"lng":80.2777,"address":"Evans Rd Chennai Tamil Nadu","trauma_capable":True},
    {"country":"India","state":"Tamil Nadu","city":"Chennai","place_name":"Greater Chennai Police Control Room","service_type":"Police","phone":"100 / 112","lat":13.0827,"lng":80.2707,"address":"Chennai Tamil Nadu","trauma_capable":False},
    {"country":"India","state":"Tamil Nadu","city":"Chennai","place_name":"108 Tamil Nadu Ambulance","service_type":"Ambulance","phone":"108","lat":13.0827,"lng":80.2707,"address":"Chennai Tamil Nadu","trauma_capable":False},
    {"country":"India","state":"Tamil Nadu","city":"Chennai","place_name":"Chennai Roadside Towing","service_type":"Towing Service","phone":"+91 98840 00000","lat":13.0600,"lng":80.2500,"address":"Chennai Tamil Nadu","trauma_capable":False},
    {"country":"India","state":"Tamil Nadu","city":"Chennai","place_name":"Apollo Hospitals Greams Road","service_type":"Hospital","phone":"044 2829 0200","lat":13.0579,"lng":80.2589,"address":"Greams Road Chennai Tamil Nadu","trauma_capable":True},

    {"country":"India","state":"Tamil Nadu","city":"NH48 near Chennai","place_name":"NH48 Highway Patrol","service_type":"Police","phone":"100 / 112","lat":12.9400,"lng":80.1500,"address":"NH48 near Chennai","trauma_capable":False},
    {"country":"India","state":"Tamil Nadu","city":"NH48 near Chennai","place_name":"NH48 Accident Trauma Center","service_type":"Trauma Center","phone":"+91 44 2233 6789","lat":12.9450,"lng":80.1520,"address":"NH48 near Chennai","trauma_capable":True},
    {"country":"India","state":"Tamil Nadu","city":"NH48 near Chennai","place_name":"NH48 Quick Ambulance","service_type":"Ambulance","phone":"+91 44 2233 1234","lat":12.9480,"lng":80.1480,"address":"NH48 near Chennai","trauma_capable":False},
    {"country":"India","state":"Tamil Nadu","city":"NH48 near Chennai","place_name":"NH48 Tow & Rescue","service_type":"Towing Service","phone":"+91 44 2233 5678","lat":12.9520,"lng":80.1540,"address":"NH48 near Chennai","trauma_capable":False},
    {"country":"India","state":"Tamil Nadu","city":"NH48 near Chennai","place_name":"NH48 Puncture Stop","service_type":"Puncture Shop","phone":"+91 44 2233 8901","lat":12.9500,"lng":80.1510,"address":"NH48 near Chennai","trauma_capable":False},

    {"country":"India","state":"Karnataka","city":"Bengaluru","place_name":"Bengaluru Traffic Police","service_type":"Police","phone":"100 / 112","lat":12.9716,"lng":77.5946,"address":"Bengaluru Karnataka","trauma_capable":False},
    {"country":"India","state":"Karnataka","city":"Bengaluru","place_name":"Victoria Hospital Trauma Care","service_type":"Trauma Center","phone":"080 2670 1150","lat":12.9606,"lng":77.5759,"address":"Bengaluru Karnataka","trauma_capable":True},
    {"country":"India","state":"Karnataka","city":"Bengaluru","place_name":"108 Karnataka Ambulance","service_type":"Ambulance","phone":"108","lat":12.9716,"lng":77.5946,"address":"Bengaluru Karnataka","trauma_capable":False},
    {"country":"India","state":"Karnataka","city":"Bengaluru","place_name":"Bengaluru Towing Services","service_type":"Towing Service","phone":"+91 99000 11111","lat":12.9750,"lng":77.5800,"address":"Bengaluru Karnataka","trauma_capable":False},

    {"country":"India","state":"Karnataka","city":"Mysuru Road near Bengaluru","place_name":"Mysuru Road Traffic Police","service_type":"Police","phone":"100 / 112","lat":12.9050,"lng":77.4820,"address":"Mysuru Road near Bengaluru","trauma_capable":False},
    {"country":"India","state":"Karnataka","city":"Mysuru Road near Bengaluru","place_name":"Rajarajeswari Medical College Trauma Center","service_type":"Trauma Center","phone":"080 2843 7000","lat":12.9010,"lng":77.4790,"address":"Mysuru Road near Bengaluru","trauma_capable":True},
    {"country":"India","state":"Karnataka","city":"Mysuru Road near Bengaluru","place_name":"Mysuru Road Ambulance","service_type":"Ambulance","phone":"108","lat":12.9030,"lng":77.4800,"address":"Mysuru Road near Bengaluru","trauma_capable":False},

    {"country":"India","state":"Delhi","city":"Delhi","place_name":"Delhi Police Control Room","service_type":"Police","phone":"100 / 112","lat":28.6129,"lng":77.2295,"address":"New Delhi Delhi","trauma_capable":False},
    {"country":"India","state":"Delhi","city":"Delhi","place_name":"AIIMS Trauma Centre","service_type":"Trauma Center","phone":"011 2659 1744","lat":28.5672,"lng":77.2100,"address":"AIIMS New Delhi","trauma_capable":True},
    {"country":"India","state":"Delhi","city":"Delhi","place_name":"Delhi Emergency Ambulance","service_type":"Ambulance","phone":"108","lat":28.6129,"lng":77.2295,"address":"New Delhi Delhi","trauma_capable":False},
    {"country":"India","state":"Delhi","city":"Delhi","place_name":"Delhi Roadside Towing","service_type":"Towing Service","phone":"+91 98100 22222","lat":28.6200,"lng":77.2400,"address":"Delhi","trauma_capable":False},

    {"country":"India","state":"Maharashtra","city":"Mumbai","place_name":"Mumbai Police Control Room","service_type":"Police","phone":"100 / 112","lat":18.9322,"lng":72.8265,"address":"Mumbai Maharashtra","trauma_capable":False},
    {"country":"India","state":"Maharashtra","city":"Mumbai","place_name":"KEM Hospital Trauma Care","service_type":"Trauma Center","phone":"022 2413 6051","lat":18.9891,"lng":72.8407,"address":"Parel Mumbai","trauma_capable":True},
    {"country":"India","state":"Maharashtra","city":"Mumbai","place_name":"Mumbai 108 Ambulance","service_type":"Ambulance","phone":"108","lat":18.9322,"lng":72.8265,"address":"Mumbai Maharashtra","trauma_capable":False},
    {"country":"India","state":"Maharashtra","city":"Mumbai","place_name":"Mumbai Towing Service","service_type":"Towing Service","phone":"+91 98200 33333","lat":18.9500,"lng":72.8300,"address":"Mumbai Maharashtra","trauma_capable":False},

    {"country":"India","state":"Uttar Pradesh","city":"Ghaziabad","place_name":"Ghaziabad Police Control Room","service_type":"Police","phone":"100 / 112","lat":28.6692,"lng":77.4538,"address":"Ghaziabad Uttar Pradesh","trauma_capable":False},
    {"country":"India","state":"Uttar Pradesh","city":"Ghaziabad","place_name":"Yashoda Hospital Trauma Centre","service_type":"Hospital","phone":"0120 418 2000","lat":28.6333,"lng":77.4350,"address":"Kaushambi Ghaziabad","trauma_capable":True},
    {"country":"India","state":"Uttar Pradesh","city":"Ghaziabad","place_name":"Ghaziabad 108 Ambulance","service_type":"Ambulance","phone":"108","lat":28.6692,"lng":77.4538,"address":"Ghaziabad Uttar Pradesh","trauma_capable":False},
    {"country":"India","state":"Uttar Pradesh","city":"Ghaziabad","place_name":"Ghaziabad Tow & Rescue","service_type":"Towing Service","phone":"+91 98180 44444","lat":28.6600,"lng":77.4500,"address":"Ghaziabad Uttar Pradesh","trauma_capable":False},
]

def load_contacts():
    if CONTACTS_FILE.exists():
        try:
            data = json.loads(CONTACTS_FILE.read_text())
            if isinstance(data, list):
                cleaned = []
                for x in data[:4]:
                    if isinstance(x, dict):
                        cleaned.append({"name": x.get("name", ""), "phone": x.get("phone", "")})
                while len(cleaned) < 4:
                    cleaned.append({"name": "", "phone": ""})
                return cleaned
        except Exception:
            pass
    return [{"name": "", "phone": ""} for _ in range(4)]

def save_contacts(contacts):
    CONTACTS_FILE.write_text(json.dumps(contacts, indent=2, ensure_ascii=False))

def make_df():
    df = pd.DataFrame(DATA)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df["trauma_capable"] = df["trauma_capable"].astype(bool)
    return df.dropna(subset=["lat", "lng"]).copy()

def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def classify(text):
    t = (text or "").lower()
    if any(k in t for k in HIGH_SEVERITY):
        return "high"
    if any(k in t for k in MEDIUM_SEVERITY):
        return "medium"
    return "low"

def traffic_multiplier(lat, lng):
    hubs = [(13.0827, 80.2707), (12.9716, 77.5946), (28.6129, 77.2295), (18.9322, 72.8265), (28.6692, 77.4538)]
    for hlat, hlng in hubs:
        if haversine(lat, lng, hlat, hlng) < 12:
            return 1.35
    return 1.0

def eta_minutes(distance_km, mult=1.0):
    speed_kmh = 28
    return max(1, round((distance_km / speed_kmh) * 60 * mult, 1))

def get_location():
    if GEO_OK:
        loc = streamlit_geolocation()
        if isinstance(loc, dict) and loc.get("latitude") and loc.get("longitude"):
            return float(loc["latitude"]), float(loc["longitude"]), True
    return 13.0827, 80.2707, False

def transcribe_voice(audio_bytes, lang_code):
    if not SR_OK or audio_bytes is None:
        return ""
    recognizer = sr.Recognizer()
    audio_file = BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language=lang_code)
    except Exception:
        return ""

def gmaps_directions_url(olat, olng, dlat, dlng, travelmode="driving"):
    params = {
        "api": 1,
        "origin": f"{olat},{olng}",
        "destination": f"{dlat},{dlng}",
        "travelmode": travelmode,
    }
    return "https://www.google.com/maps/dir/?" + urlencode(params)

def build_sos_message(lat, lng, accident, top_rows, contacts):
    lines = [
        "ROADSOS SOS",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Location: {lat:.6f}, {lng:.6f}",
        f"Description: {accident or 'No description entered'}",
        ""
    ]
    for label, row in top_rows:
        if row is not None:
            lines.append(f"{label}: {row['place_name']} | {row['phone']} | {row['address']}")
    if contacts:
        lines.append("")
        lines.append("Emergency Contacts:")
        for c in contacts:
            if c["name"].strip() or c["phone"].strip():
                lines.append(f"{c['name']} | {c['phone']}")
    lines.append("Emergency Number: 112")
    return "\n".join(lines)

def init_state():
    if "accident_text" not in st.session_state:
        st.session_state["accident_text"] = ""
    if "last_activity" not in st.session_state:
        st.session_state["last_activity"] = time.time()
    if "last_audio_sig" not in st.session_state:
        st.session_state["last_audio_sig"] = None
    if "contacts" not in st.session_state:
        st.session_state["contacts"] = load_contacts()
    if "last_sos_state" not in st.session_state:
        st.session_state["last_sos_state"] = None

init_state()
df = make_df()

if AUTOREFRESH_OK:
    st_autorefresh(interval=5000, key="roadsos_refresh")

st.title("🚑 RoadSoS India")
st.caption("From accident to assistance in seconds—share live location, route, and emergency support instantly.")

with st.sidebar:
    st.header("Controls")
    use_gps = st.checkbox("Use browser location", value=True)
    lang = st.radio("Voice language", ["English", "Hindi"], horizontal=True)
    auto_sos = st.toggle("Auto-SOS after 60 seconds of inactivity", value=True)
    consent = st.checkbox("Consent to alert prep", value=False)
    st.markdown("---")
    st.markdown("### Emergency numbers")
    for k, v in EMERGENCY_NUMBERS.items():
        st.write(f"{k}: {v}")

with st.expander("Emergency contacts", expanded=True):
    cols = st.columns(2)
    for i in range(4):
        c1, c2 = st.columns(2)
        st.session_state["contacts"][i]["name"] = c1.text_input(
            f"Contact {i+1} name",
            value=st.session_state["contacts"][i]["name"],
            key=f"contact_name_{i}"
        )
        st.session_state["contacts"][i]["phone"] = c2.text_input(
            f"Contact {i+1} phone",
            value=st.session_state["contacts"][i]["phone"],
            key=f"contact_phone_{i}"
        )
    save_cols = st.columns([1, 4])
    if save_cols[0].button("Save contacts locally"):
        save_contacts(st.session_state["contacts"])
        st.success("Contacts saved locally.")

if use_gps:
    user_lat, user_lng, gps_ok = get_location()
    if gps_ok:
        st.success(f"Location detected: {user_lat:.6f}, {user_lng:.6f}")
    else:
        st.warning("Browser location not available. Using fallback coordinates.")
else:
    user_lat = st.number_input("User latitude", value=13.0827, format="%.6f")
    user_lng = st.number_input("User longitude", value=80.2707, format="%.6f")

st.subheader("Accident description")
current_text = st.text_area(
    "Describe the accident",
    value=st.session_state["accident_text"],
    height=140,
    placeholder="Type here or use voice input below"
)
if current_text != st.session_state["accident_text"]:
    st.session_state["accident_text"] = current_text
    st.session_state["last_activity"] = time.time()

st.markdown("### Voice input")
audio = st.audio_input("Record a voice message")

if audio is not None:
    audio_bytes = audio.getvalue()
    audio_sig = hash(audio_bytes)

    if audio_sig != st.session_state["last_audio_sig"]:
        lang_code = "hi-IN" if lang == "Hindi" else "en-IN"
        transcript = transcribe_voice(audio_bytes, lang_code)

        if transcript:
            base = st.session_state["accident_text"].strip()
            merged = f"{base} {transcript}".strip() if base else transcript
            st.session_state["accident_text"] = merged
            st.session_state["last_audio_sig"] = audio_sig
            st.session_state["last_activity"] = time.time()
            st.success(f"Voice transcript added: {transcript}")
            st.rerun()
        else:
            st.warning("Could not transcribe voice. Please type the message.")

accident = st.session_state["accident_text"]
sev = classify(accident)

if sev == "high":
    st.error("High severity detected: prioritize trauma, ambulance, hospital, and police.")
elif sev == "medium":
    st.warning("Medium severity detected: urgent medical support recommended.")
else:
    st.info("Low severity detected.")

filtered = df.copy()
filtered["distance_km"] = filtered.apply(
    lambda r: round(haversine(user_lat, user_lng, float(r["lat"]), float(r["lng"])), 2), axis=1
)
filtered["traffic_factor"] = filtered.apply(
    lambda r: traffic_multiplier(float(r["lat"]), float(r["lng"])), axis=1
)
filtered["eta_min"] = filtered.apply(
    lambda r: eta_minutes(float(r["distance_km"]), float(r["traffic_factor"])), axis=1
)
filtered = filtered[filtered["eta_min"] <= 120].copy()

if sev == "high":
    trauma = filtered[filtered["service_type"] == "Trauma Center"].sort_values("eta_min")
    ambulance = filtered[filtered["service_type"] == "Ambulance"].sort_values("eta_min")
    police = filtered[filtered["service_type"] == "Police"].sort_values("eta_min")
    hospital = filtered[filtered["service_type"] == "Hospital"].sort_values("eta_min")
    others = filtered[
        ~filtered["service_type"].isin(["Trauma Center", "Ambulance", "Police", "Hospital"])
    ].sort_values(["eta_min", "distance_km"])
    trauma["priority"] = "CRITICAL TRAUMA"
    ambulance["priority"] = "CRITICAL AMBULANCE"
    police["priority"] = "CRITICAL POLICE"
    hospital["priority"] = "CRITICAL HOSPITAL"
    others["priority"] = ""
    filtered = pd.concat([trauma, ambulance, police, hospital, others], ignore_index=True)
else:
    filtered["priority"] = ""
    filtered = filtered.sort_values(["eta_min", "distance_km"])

st.subheader("Services within about 1–2 hours")
filtered = filtered.reset_index(drop=True)
filtered.insert(0, "Select", False)

edited = st.data_editor(
    filtered[
        ["Select", "priority", "service_type", "place_name", "phone", "address", "distance_km", "eta_min", "trauma_capable", "lat", "lng"]
    ].rename(columns={
        "priority": "Priority",
        "service_type": "Service",
        "place_name": "Name",
        "distance_km": "Distance km",
        "eta_min": "ETA min",
        "trauma_capable": "Trauma capable",
        "lat": "Lat",
        "lng": "Lng",
    }),
    hide_index=True,
    use_container_width=True,
    key="services_editor",
)

selected_row = None
selected_rows = edited[edited["Select"] == True]
if not selected_rows.empty:
    selected_row = selected_rows.iloc[0]

st.subheader("Map")
map_df = pd.DataFrame({"latitude": [user_lat], "longitude": [user_lng]})
pts = filtered.head(12).rename(columns={"lat": "latitude", "lng": "longitude"})[["latitude", "longitude"]]
map_df = pd.concat([map_df, pts], ignore_index=True)
st.map(map_df)

if selected_row is not None:
    st.markdown("### Selected route")
    route_url = gmaps_directions_url(user_lat, user_lng, float(selected_row["Lat"]), float(selected_row["Lng"]))
    st.link_button(f"Open route to {selected_row['Name']}", route_url)

def get_top(service_type):
    x = filtered[filtered["service_type"] == service_type].head(1)
    return x.iloc[0] if not x.empty else None

def top_four_payload():
    return [
        ("Nearest Trauma Center", get_top("Trauma Center")),
        ("Nearest Ambulance", get_top("Ambulance")),
        ("Nearest Police", get_top("Police")),
        ("Nearest Hospital", get_top("Hospital")),
    ]

def get_contacts_for_sos():
    return [c for c in st.session_state["contacts"] if c["name"].strip() or c["phone"].strip()]

def maybe_sos_message():
    return build_sos_message(user_lat, user_lng, accident, top_four_payload(), get_contacts_for_sos())

col1, col2 = st.columns(2)

with col1:
    if st.button("📢 Send SOS now"):
        msg = maybe_sos_message()
        st.error("SOS prepared below.")
        st.code(msg)

with col2:
    st.write("")

if auto_sos:
    elapsed = time.time() - st.session_state["last_activity"]
    if elapsed < 60:
        st.caption(f"Inactivity monitor: {int(60 - elapsed)} seconds until auto-SOS countdown starts.")
    else:
        countdown_left = max(0, 60 - int(elapsed - 60))
        if countdown_left > 0:
            st.warning(f"Auto-SOS countdown: {countdown_left} seconds")
        else:
            if consent and st.session_state["last_sos_state"] != "triggered":
                st.session_state["last_sos_state"] = "triggered"
                msg = maybe_sos_message()
                st.error("Auto-SOS triggered due to inactivity. Prepared emergency message below.")
                st.code(msg)
            elif not consent:
                st.warning("Auto-SOS ready, but consent is not enabled.")

st.caption("Contacts are saved locally in data/emergency_contacts.json when you click Save contacts locally.")