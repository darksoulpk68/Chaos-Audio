import streamlit as st
import google.generativeai as genai
import json

# --- CONFIGURATION ---
API_KEY = st.secrets["api"]

# --- LOAD DATABASES ---
try:
    with open("Subwoofer_db.json", "r") as f:
        SUBWOOFER_DB = json.load(f)
except Exception as e:
    st.error(f"Error loading subwoofer database: {e}")
    SUBWOOFER_DB = []

try:
    with open("models.json", "r") as f:
        MODEL_LIST = json.load(f)
except Exception as e:
    st.error(f"Error loading model list: {e}")
    MODEL_LIST = []

# --- ROBUST MODEL FINDER ---
def get_working_model():
    for model_name in MODEL_LIST:
        try:
            model = genai.GenerativeModel(model_name)
            model.generate_content("test")
            return model
        except Exception as e:
            st.warning(f"Model {model_name} failed: {e}")
            continue
    st.error("No working model found.")
    return None

# Configure API
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"API Key Error: {e}")

# --- INITIALIZE SESSION STATE (Memory) ---
# This keeps data alive when you click buttons
if 'architect_out' not in st.session_state: st.session_state['architect_out'] = ""
if 'structural_out' not in st.session_state: st.session_state['structural_out'] = ""
if 'thermal_out' not in st.session_state: st.session_state['thermal_out'] = ""
if 'core_out' not in st.session_state: st.session_state['core_out'] = ""

# --- PROMPTS ---
ARCHITECT_PROMPT = "You are the AUDIO ARCHITECT. Design enclosure based on inputs. Output specs list."
STRUCTURAL_PROMPT = "You are the STRUCTURAL ANALYST. Predict damage based on power/tolerance."
THERMAL_PROMPT = "You are the THERMAL PHYSICIST. Predict coil meltdown and voltage issues."
CORE_PROMPT = "You are ALPHAAUDIO CORE. Synthesize reports into a GO/NO-GO verdict."
RECOMMENDER_PROMPT = """
You are the GEAR LAB ASSISTANT.
Task: Pick the BEST subwoofers from the provided DATABASE based on user needs.
Input: User Preferences + Database List.
Output: The top 3 choices, explaining WHY they fit the goal (e.g. 'The Zv6 is better for 20Hz wind').
"""

# --- APP LAYOUT ---
st.set_page_config(page_title="AlphaAudio V3", page_icon="☢️", layout="wide")
st.title("☢️ AlphaAudio: DeepMind Logic Engine")

# TABS
tab_sim, tab_gear = st.tabs(["🎛️ Design Studio (Simulation)", "🧪 Gear Lab (Database)"])

# ==============================================================================
# TAB 1: DESIGN STUDIO (The Iterative Simulator)
# ==============================================================================
with tab_sim:
    # Sidebar for Simulation
    with st.sidebar:
        st.header("1. Project Constraints")
        car_model = st.text_input("Vehicle Model", "2010 Honda Civic")
        subwoofer = st.text_input("Subwoofer(s)", "2x Sundown Zv6 15")
        power = st.text_input("Amplifier(s) power (RMS, total)", "5000W")
        Fs = st.slider("Desired Frequency (Hz)", 15, 75, 32)
        tolerance = st.select_slider("Destruction Tolerance", options=["Zero", "Rattles", "Flex", "Breakage", "TERMINATION"])
        comments = st.text_area("Describe your setup or your goal", "e.g. 'I have 80Ah lithium' or 'I want a windy setup'")
        
        st.header("2. Control")
        if st.button("🚀 RUN FULL SIMULATION", type="primary"):
            model = get_working_model()
            if model:
                # 1. ARCHITECT
                with st.spinner("Architect is working..."):
                    proj_data = f"Car: {car_model}, Sub: {subwoofer}, Power: {power}, Fs = {Fs}, Tolerance: {tolerance}, comments: {comments}"
                    res1 = model.generate_content(f"{ARCHITECT_PROMPT}\nDATA: {proj_data}")
                    st.session_state['architect_out'] = res1.text
                
                # 2. STRUCTURAL (Needs Architect Data)
                with st.spinner("Structural is stressing..."):
                    res2 = model.generate_content(f"{STRUCTURAL_PROMPT}\nDATA: {proj_data}\nARCHITECT: {res1.text}")
                    st.session_state['structural_out'] = res2.text
                    
                # 3. THERMAL (Needs Architect Data)
                with st.spinner("Thermal is heating up..."):
                    res3 = model.generate_content(f"{THERMAL_PROMPT}\nDATA: {proj_data}\nARCHITECT: {res1.text}")
                    st.session_state['thermal_out'] = res3.text
                    
                st.rerun() # Refresh page to show results

    # Main Display Area
    if st.session_state['architect_out']:
        col1, col2, col3 = st.columns(3)
        model = get_working_model()

        # --- COLUMN 1: ARCHITECT ---
        with col1:
            st.subheader("📐 Architect")
            st.info(st.session_state['architect_out'])
            
            # ITERATION LOOP
            arch_feedback = st.text_area("Refine Architect:", placeholder="e.g. 'Make the box smaller'")
            if st.button("Retune Architect"):
                new_prompt = f"ORIGINAL DATA: {st.session_state['architect_out']}\nUSER FEEDBACK: {arch_feedback}\nRE-CALCULATE:"
                with st.spinner("Retuning..."):
                    new_res = model.generate_content(f"{ARCHITECT_PROMPT}\n{new_prompt}")
                    st.session_state['architect_out'] = new_res.text
                    st.rerun()

        # --- COLUMN 2: STRUCTURAL ---
        with col2:
            st.subheader("🔨 Structural")
            st.warning(st.session_state['structural_out'])
            
            # ITERATION LOOP
            struct_feedback = st.text_area("Refine Structural:", placeholder="e.g. 'I have a sunroof'")
            if st.button("Re-Test Structural"):
                new_prompt = f"ORIGINAL DATA: {st.session_state['structural_out']}\nUSER FEEDBACK: {struct_feedback}\nRE-CALCULATE:"
                with st.spinner("Re-testing..."):
                    new_res = model.generate_content(f"{STRUCTURAL_PROMPT}\n{new_prompt}")
                    st.session_state['structural_out'] = new_res.text
                    st.rerun()

        # --- COLUMN 3: THERMAL ---
        with col3:
            st.subheader("🔥 Thermal")
            st.error(st.session_state['thermal_out'])
            
            # ITERATION LOOP
            therm_feedback = st.text_area("Refine Thermal:", placeholder="e.g. 'I have lithium batts'")
            if st.button("Re-Check Thermal"):
                new_prompt = f"ORIGINAL DATA: {st.session_state['thermal_out']}\nUSER FEEDBACK: {therm_feedback}\nRE-CALCULATE:"
                with st.spinner("Re-checking..."):
                    new_res = model.generate_content(f"{THERMAL_PROMPT}\n{new_prompt}")
                    st.session_state['thermal_out'] = new_res.text
                    st.rerun()
        
        # --- CORE VERDICT ---
        st.divider()
        st.header("🏁 Core Verdict")
        if st.button("Synthesize Final Plan"):
            with st.spinner("Core is thinking..."):
                final_data = f"ARCH: {st.session_state['architect_out']}\nSTRUCT: {st.session_state['structural_out']}\nTHERM: {st.session_state['thermal_out']}"
                core_res = model.generate_content(f"{CORE_PROMPT}\nDATA: {final_data}")
                st.success(core_res.text)

# ==============================================================================
# TAB 2: GEAR LAB (Database & Recommender)
# ==============================================================================
with tab_gear:
    st.header("🧪 The Gear Laboratory")
    st.write("Browse the database or ask the AI to pick for you.")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("AI Recommender")
        user_budget = st.text_input("Budget ($)", "1500")
        music_style = st.selectbox("Music Style", ["Decaf / Slowed (20-30Hz)", "Rap / HipHop (30-40Hz)", "EDM / Punchy (40Hz+)", "Rock / Metal"])
        goal = st.radio("Primary Goal", ["Violent Wind (Hairtricks)", "Score (SPL Numbers)", "Sound Quality"])
        
        if st.button("🤖 Find My Subwoofer"):
            model = get_working_model()
            if model:
                with st.spinner("Scanning Database..."):
                    reqs = f"Budget: {user_budget}, Music: {music_style}, Goal: {goal}"
                    # We pass the WHOLE database string to the AI
                    db_string = str(SUBWOOFER_DB) 
                    response = model.generate_content(f"{RECOMMENDER_PROMPT}\n\nUSER REQS: {reqs}\n\nDATABASE: {db_string}")
                    st.markdown(response.text)
    
    with col_b:
        st.subheader("📦 Component Database")
        # Display the Raw Database nicely
        st.dataframe(SUBWOOFER_DB)
