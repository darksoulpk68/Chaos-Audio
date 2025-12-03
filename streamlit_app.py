import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF

# --- CONFIGURATION ---
# Try/Except block to handle local vs cloud secrets safely
try:
    API_KEY = st.secrets["api"]
except:
    # Fallback for local testing if secrets.toml isn't found
    # You can also set an environment variable or hardcode for local dev
    API_KEY = "YOUR_FALLBACK_KEY_HERE" 

# --- APP LAYOUT CONFIG (Must be first) ---
st.set_page_config(page_title="AlphaAudio V4", page_icon="☢️", layout="wide")

# --- LOAD DATABASES ---
@st.cache_data # Cache this so it doesn't reload on every click
def load_data():
    try:
        with open("Subwoofer_db.json", "r") as f:
            sub_db = json.load(f)
    except:
        sub_db = []
    
    try:
        with open("models.json", "r") as f:
            model_list = json.load(f)
    except:
        # Fallback list if file missing
        model_list = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    
    return sub_db, model_list

SUBWOOFER_DB, MODEL_LIST = load_data()

# --- HELPER FUNCTIONS ---
def get_working_model():
    # Configure API first
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        st.error(f"API Key Error: {e}")
        return None

    for model_name in MODEL_LIST:
        try:
            model = genai.GenerativeModel(model_name)
            # Quick lightweight test
            model.generate_content("test")
            return model
        except:
            continue
    st.error("No working Gemini model found. Check API Key or Region.")
    return None

# --- INITIALIZE SESSION STATE ---
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
Output: The top 3 choices, explaining WHY they fit the goal.
"""
COMPARISON_PROMPT = "You are the COMPARISON ENGINE. Compare these builds side-by-side and declare a winner for the specific goal."

# ==============================================================================
# MAIN NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:
    st.title("☢️ AlphaAudio")
    st.markdown("### DeepMind Logic Engine")
    st.markdown("---")
    
    # Navigation Menu
    page = st.radio("Select Tool", ["🎛️ Design Studio", "🧪 Gear Lab", "⚔️ Build Comparison"])
    
    st.markdown("---")
    st.info("💡 **Tip:** Use 'Design Studio' for deep simulation of a single setup.")

# ==============================================================================
# PAGE 1: DESIGN STUDIO (The Simulator)
# ==============================================================================
if page == "🎛️ Design Studio":
    st.header("🎛️ Design Studio: Iterative Simulation")
    
    # --- INPUT SECTION (Now on Main Page) ---
    with st.expander("🛠️ Project Constraints (Click to Edit)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            car_model = st.text_input("Vehicle Model", "2010 Honda Civic")
            subwoofer = st.text_input("Subwoofer(s)", "2x Sundown Zv6 15")
            power = st.text_input("Amplifier Power (RMS)", "5000W")
        with c2:
            Fs = st.slider("Desired Frequency (Hz)", 15, 75, 32)
            tolerance = st.select_slider("Destruction Tolerance", options=["Zero", "Rattles", "Flex", "Breakage", "TERMINATION"])
            comments = st.text_area("Specific Goals / Electrical Mods", "e.g. 'Lithium bank, chasing hairtricks'")

        if st.button("🚀 INITIATE SIMULATION", type="primary", use_container_width=True):
            model = get_working_model()
            if model:
                # 1. ARCHITECT
                with st.spinner("📐 Architect is calculating box volume..."):
                    proj_data = f"Car: {car_model}, Sub: {subwoofer}, Power: {power}, Fs: {Fs}, Tolerance: {tolerance}, Notes: {comments}"
                    res1 = model.generate_content(f"{ARCHITECT_PROMPT}\nDATA: {proj_data}")
                    st.session_state['architect_out'] = res1.text
                
                # 2. STRUCTURAL
                with st.spinner("🔨 Structural is analyzing flex..."):
                    res2 = model.generate_content(f"{STRUCTURAL_PROMPT}\nDATA: {proj_data}\nARCHITECT: {res1.text}")
                    st.session_state['structural_out'] = res2.text
                    
                # 3. THERMAL
                with st.spinner("🔥 Thermal is calculating heat soak..."):
                    res3 = model.generate_content(f"{THERMAL_PROMPT}\nDATA: {proj_data}\nARCHITECT: {res1.text}")
                    st.session_state['thermal_out'] = res3.text
                
                st.rerun()

    # --- RESULTS SECTION ---
    if st.session_state['architect_out']:
        st.divider()
        st.subheader("📊 Simulation Results")
        
        col1, col2, col3 = st.columns(3)
        model = get_working_model()

        # ARCHITECT COLUMN
        with col1:
            st.markdown("#### 📐 Architect")
            st.info(st.session_state['architect_out'])
            feedback = st.text_input("Refine Architect", key="arch_fb")
            if st.button("Retune Architect"):
                with st.spinner("Retuning..."):
                    new_res = model.generate_content(f"{ARCHITECT_PROMPT}\nORIGINAL: {st.session_state['architect_out']}\nFEEDBACK: {feedback}")
                    st.session_state['architect_out'] = new_res.text
                    st.rerun()

        # STRUCTURAL COLUMN
        with col2:
            st.markdown("#### 🔨 Structural")
            st.warning(st.session_state['structural_out'])
            feedback = st.text_input("Refine Structural", key="struct_fb")
            if st.button("Re-Test Structural"):
                with st.spinner("Re-testing..."):
                    new_res = model.generate_content(f"{STRUCTURAL_PROMPT}\nORIGINAL: {st.session_state['structural_out']}\nFEEDBACK: {feedback}")
                    st.session_state['structural_out'] = new_res.text
                    st.rerun()

        # THERMAL COLUMN
        with col3:
            st.markdown("#### 🔥 Thermal")
            st.error(st.session_state['thermal_out'])
            feedback = st.text_input("Refine Thermal", key="therm_fb")
            if st.button("Re-Check Thermal"):
                with st.spinner("Re-checking..."):
                    new_res = model.generate_content(f"{THERMAL_PROMPT}\nORIGINAL: {st.session_state['thermal_out']}\nFEEDBACK: {feedback}")
                    st.session_state['thermal_out'] = new_res.text
                    st.rerun()

        # CORE VERDICT SECTION
        st.divider()
        c_btn, c_res = st.columns([1, 4])
        with c_btn:
            if st.button("🏁 Synthesize Final Plan", type="primary"):
                with st.spinner("Synthesizing Master Plan..."):
                    final_data = f"ARCH: {st.session_state['architect_out']}\nSTRUCT: {st.session_state['structural_out']}\nTHERM: {st.session_state['thermal_out']}"
                    core_res = model.generate_content(f"{CORE_PROMPT}\nDATA: {final_data}")
                    st.session_state['core_out'] = core_res.text
                    st.rerun()
        
        with c_res:
            if st.session_state['core_out']:
                st.success(f"**CORE VERDICT:**\n\n{st.session_state['core_out']}")

    # --- SHARE SECTION (HIDDEN UNTIL DONE) ---
    if st.session_state['core_out']:
        st.divider()
        st.header("📤 Export & Share")
        
        build_summary = f"""
        VEHICLE: {car_model}
        SUBWOOFER: {subwoofer}
        POWER: {power}
        TOLERANCE: {tolerance}
        
        -- ARCHITECT --
        {st.session_state['architect_out']}
        
        -- STRUCTURAL --
        {st.session_state['structural_out']}
        
        -- THERMAL --
        {st.session_state['thermal_out']}
        
        -- CORE VERDICT --
        {st.session_state['core_out']}
        """
        
        col_pdf, col_txt = st.columns(2)
        with col_txt:
            st.text_area("Raw Text Summary", build_summary, height=150)
            
        with col_pdf:
            if st.button("📄 Generate PDF Report"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                # Simple PDF generation (ascii safe)
                safe_text = build_summary.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, safe_text)
                
                pdf_output = pdf.output(dest="S").encode("latin-1")
                st.download_button(
                    label="Download PDF",
                    data=pdf_output,
                    file_name="AlphaAudio_Build.pdf",
                    mime="application/pdf"
                )

# ==============================================================================
# PAGE 2: GEAR LAB (Database)
# ==============================================================================
elif page == "🧪 Gear Lab":
    st.header("🧪 Gear Laboratory")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("AI Recommender")
        with st.form("recommender_form"):
            user_budget = st.text_input("Budget ($)", "1500")
            music_style = st.selectbox("Music Style", ["Decaf (20-30Hz)", "Rap (30-40Hz)", "EDM (40Hz+)", "Metal"])
            goal = st.radio("Goal", ["Wind/Hairtricks", "SPL Score", "Sound Quality"])
            submitted = st.form_submit_button("🤖 Find My Subwoofer")
            
            if submitted:
                model = get_working_model()
                if model:
                    with st.spinner("Analyzing Database..."):
                        reqs = f"Budget: {user_budget}, Music: {music_style}, Goal: {goal}"
                        db_string = str(SUBWOOFER_DB) 
                        response = model.generate_content(f"{RECOMMENDER_PROMPT}\n\nUSER REQS: {reqs}\n\nDATABASE: {db_string}")
                        st.markdown(response.text)
    
    with col_b:
        st.subheader("📦 Component Database")
        st.dataframe(SUBWOOFER_DB, use_container_width=True)

# ==============================================================================
# PAGE 3: BUILD COMPARISON
# ==============================================================================
elif page == "⚔️ Build Comparison":
    st.header("⚔️ Build Arena: Compare Setups")
    
    num_builds = st.slider("How many builds?", 2, 4, 2)
    
    # Dynamic Columns for Inputs
    cols = st.columns(num_builds)
    build_data = []
    
    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Build #{i+1}")
            c_model = st.text_input(f"Car #{i+1}", key=f"c{i}")
            c_sub = st.text_input(f"Sub #{i+1}", key=f"s{i}")
            c_pwr = st.text_input(f"Power #{i+1}", key=f"p{i}")
            build_data.append(f"Build {i+1}: {c_model}, {c_sub}, {c_pwr}")

    if st.button("🚀 FIGHT!", type="primary", use_container_width=True):
        model = get_working_model()
        if model:
            with st.spinner("Simulating Battle..."):
                combined_data = "\n".join(build_data)
                response = model.generate_content(f"{COMPARISON_PROMPT}\n\nDATA:\n{combined_data}")
                st.success(response.text)