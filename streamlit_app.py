import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF # type: ignore

# --- CONFIGURATION ---
# Try/Except block to handle local vs cloud secrets safely
try:
    API_KEY = st.secrets["api"]
except:
    # Fallback for local testing if secrets.toml isn't found
    # You can also set an environment variable or hardcode for local dev
    API_KEY = "YOUR_FALLBACK_KEY_HERE" 

# --- APP LAYOUT CONFIG (Must be first) ---
st.set_page_config(page_title="AlphaAudio", page_icon="☢️", layout="wide")

# --- LOAD DATABASES ---
# The try-except blocks are intentionally left empty to suppress error messages.
# If a JSON file fails to load, the app will continue to run with an empty list or dictionary.
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
        model_list = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]

    try:
        with open("design_prompts.json", "r") as f:
            prompts = json.load(f)
    except:
        prompts = {
            "ARCHITECT_PROMPT": "You are the AUDIO ARCHITECT. Design enclosure based on inputs. Output specs list.",
            "STRUCTURAL_PROMPT": "You are the STRUCTURAL ANALYST. Predict damage based on power/tolerance.",
            "THERMAL_PROMPT": "You are the THERMAL PHYSICIST. Predict coil meltdown and voltage issues.",
            "CORE_PROMPT": "You are ALPHAAUDIO CORE. Synthesize reports into a GO/NO-GO verdict.",
            "RECOMMENDER_PROMPT": "You are the GEAR LAB ASSISTANT.\nTask: Pick the BEST subwoofers from the provided DATABASE based on user needs.\nInput: User Preferences + Database List.\nOutput: The top 3 choices, explaining WHY they fit the goal.",
            "COMPARISON_PROMPT": "You are the COMPARISON ENGINE. Compare these builds side-by-side and declare a winner for the specific goal."
        }

    try:
        with open("amplifiers_db.json", "r") as f:
            amplifier_db = json.load(f)
    except:
        amplifier_db = []

    try:
        with open("battery_electrical_db.json", "r") as f:
            battery_electrical_db = json.load(f)
    except:
        battery_electrical_db = {"batteries":[],"alternators":[],"wiring_guides":[]}

    try:
        with open("headunits_processors_db.json", "r") as f:
            headunits_processors_db = json.load(f)
    except:
        headunits_processors_db = {"headunits":[],"processors":[]}

    try:
        with open("wiring_guide.json", "r") as f:
            wiring_guide_db = json.load(f)
    except:
        wiring_guide_db = {}

    return sub_db, model_list, prompts, amplifier_db, battery_electrical_db, headunits_processors_db, wiring_guide_db

SUBWOOFER_DB, MODEL_LIST, PROMPTS, AMPLIFIER_DB, BATTERY_ELECTRICAL_DB, HEADUNITS_PROCESSORS_DB, WIRING_GUIDE_DB = load_data()

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
if 'page' not in st.session_state: st.session_state['page'] = "welcome"

# --- PROMPTS ---
ARCHITECT_PROMPT = PROMPTS.get("ARCHITECT_PROMPT")
STRUCTURAL_PROMPT = PROMPTS.get("STRUCTURAL_PROMPT")
THERMAL_PROMPT = PROMPTS.get("THERMAL_PROMPT")
CORE_PROMPT = PROMPTS.get("CORE_PROMPT")
RECOMMENDER_PROMPT = PROMPTS.get("RECOMMENDER_PROMPT")
COMPARISON_PROMPT = PROMPTS.get("COMPARISON_PROMPT")

# ==============================================================================
# MAIN NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:

    # Barre du haut avec icône settings
    c_top = st.columns([10,1])
    with c_top[0]:
        st.title("☢️ AlphaAudio")
    # SUPPRESSION DU CODE DE CHARGEMENT DE FICHIERS EN DEHORS DE LA FONCTION
    st.markdown("#### Menu")
    if st.button("🎓 Beginner's Guide", use_container_width=True):
        st.session_state["page"] = "🎓 Beginner's Guide"
        st.rerun()
    
    if st.button("🧪 Gear Lab", use_container_width=True):
        st.session_state["page"] = "🧪 Gear Lab"
        st.rerun()
        
    if st.button("🎛️ Design Studio", use_container_width=True):
        st.session_state["page"] = "🎛️ Design Studio"
        st.rerun()

    if st.button("⚔️ Build Wars", use_container_width=True):
        st.session_state["page"] = "⚔️ Build Wars"
        st.rerun()
    
    # Optional: allow user to add a short extra prompt used by the simulator
    st.markdown("---")
    st.markdown("#### Prompt Addition (optional)")
    st.text_area("Add extra instructions for the simulator (optional)", key="add_prompt", height=80)
    # Ensure `add_prompt` exists in session state and mirror it to a local variable
    if 'add_prompt' not in st.session_state:
        st.session_state['add_prompt'] = ""
    add_prompt = st.session_state.get('add_prompt', "")

    st.markdown("---")
    
    # Dynamic Tip based on current page
    page = st.session_state.get("page", "welcome") # Get current page, default to welcome
    if page == "🎓 Beginner's Guide":
        st.info("💡 **Tip:** Fill out the questionnaire to get a personalized audio system recommendation.")
    elif page == "🧪 Gear Lab":
        st.info("💡 **Tip:** Use the AI Recommender to find subs that fit your music style.")
    elif page == "🎛️ Design Studio":
        st.info("💡 **Tip:** Use this mode for deep, single-vehicle simulation.")
    elif page == "⚔️ Build Wars":
        st.info("💡 **Tip:** Great for deciding between two different subwoofer brands.")
    elif page == "welcome":
        st.info("💡 **Tip:** Click a menu item to get started!")


# Pass the session state to the variable the rest of the app expects
page = st.session_state.get("page", "welcome")

# ==============================================================================
# WELCOME PAGE / TUTORIAL
# ==============================================================================
if page == "welcome":
    st.title("Welcome to AlphaAudio ☢️")
    st.markdown("Your personal AI-powered car audio system simulator and designer.")
    st.markdown("---")

    st.header("How it Works")
    st.markdown("""
    AlphaAudio uses a suite of specialized AI agents to simulate and design your car audio system. You provide the constraints, and the AI does the heavy lifting, providing you with detailed analysis and recommendations.
    """)

    st.header("How to Use AlphaAudio")
    st.markdown("""
    Use the menu in the sidebar to navigate between the different modes:

    ### 🎛️ Design Studio
    This is the core of AlphaAudio. Here you can simulate a complete car audio build.
    1.  **Enter Your Project Constraints**: Specify your vehicle, subwoofers, amplifier power, and your goals.
    2.  **Initiate Simulation**: The AI agents (Architect, Structural, and Thermal) will analyze your setup.
    3.  **Review and Refine**: Check the results from each agent. You can provide feedback and rerun the simulation for each part to refine the design.
    4.  **Synthesize Final Plan**: Once you are happy with the design, the CORE agent will provide a final verdict and a summary of the build.
    5.  **Export**: You can export the final build plan as a text summary or a PDF report.

    ### 🧪 Gear Lab
    Here you can find the right gear for your build.
    1.  **AI Recommender**: Get AI-powered recommendations for subwoofers, amplifiers, and more based on your budget and goals.
    2.  **Database**: Browse the curated databases of audio equipment.

    ### ⚔️ Build Comparison
    Compare different builds side-by-side to see which one comes out on top for your specific goals.
    1.  **Enter Builds**: Input the details for 2 to 4 different builds.
    2.  **FIGHT!**: The AI will simulate a "battle" between the builds and declare a winner.

    **To get started, select a mode from the sidebar.**
    """)

# ==============================================================================
# PAGE 1: DESIGN STUDIO (The Simulator)
# ==============================================================================
elif page == "🎛️ Design Studio":
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
            comments = st.text_area("Describe your goals or your actual build, giving as much information as possible", "e.g. 'Lithium bank, chasing hairtricks'")

        if st.button("🚀 INITIATE SIMULATION", type="primary", width="stretch"):
            model = get_working_model()
            if model:
                # 1. ARCHITECT
                with st.spinner("📐 Architect is calculating box volume..."):
                    proj_data = f"Car: {car_model}, Sub: {subwoofer}, Power: {power}, Fs: {Fs}, Tolerance: {tolerance}, Notes: {comments}"
                    # Ajout du matériel de prompt additionnel si pertinent
                    extra = add_prompt.strip()
                    if extra:
                        full_prompt = f"{ARCHITECT_PROMPT}\nDATA: {proj_data}\nUSER ADDITION: {extra}"
                    else:
                        full_prompt = f"{ARCHITECT_PROMPT}\nDATA: {proj_data}"
                    res1 = model.generate_content(full_prompt)
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

    # Onglets pour naviguer entre les catégories
    tab_labels = [
        "Subwoofers",
        "Amplifiers",
        "Battery & Electrical",
        "Headunits & Processors",
        "Wiring Guide",
        "Other Accessories"
    ]
    tabs = st.tabs(tab_labels)

    # Onglet Subwoofers
    with tabs[0]:
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
            st.subheader("📦 Subwoofer Database")
            st.dataframe(SUBWOOFER_DB, width="stretch")

    # Onglet Amplifiers
    with tabs[1]:
        st.subheader("Amplifiers Shopping & Database")
        col_l, col_r = st.columns([1, 2])
        with col_l:
            st.markdown("### AI Amplifier Recommender")
            with st.form("amp_recommender_form"):
                amp_budget = st.text_input("Budget ($)", "1000")
                desired_rms = st.text_input("Desired RMS per channel (e.g. 500)", "500")
                channels = st.selectbox("Channel Count", [1, 2, 4, 5, 6, 8], index=2)
                amp_class = st.selectbox("Preferred Class", ["Any", "D", "AB"], index=0)
                amp_notes = st.text_area("Installation Constraints / Notes (optional)", "")
                amp_submit = st.form_submit_button("🔎 Recommend Amplifiers")

                if amp_submit:
                    model = get_working_model()
                    if model:
                        with st.spinner("Analyzing amplifier database..."):
                            reqs = f"Budget: {amp_budget}, DesiredRMS: {desired_rms}, Channels: {channels}, Class: {amp_class}, Notes: {amp_notes}"
                            amp_db_string = str(AMPLIFIER_DB)
                            amp_prompt = PROMPTS.get("AMPLIFIER_RECOMMENDER_PROMPT", "You are the Amplifier Selection Specialist.")
                            response = model.generate_content(f"{amp_prompt}\n\nUSER REQS: {reqs}\n\nDATABASE: {amp_db_string}")
                            st.markdown(response.text)
        with col_r:
            st.subheader("📦 Amplifier Database")
            st.dataframe(AMPLIFIER_DB, width="stretch")

    # Onglet Battery & Electrical
    with tabs[2]:
        st.subheader("Battery Setups & Electrical Requirements")
        col_bat, col_alt = st.columns([2, 1])
        with col_bat:
            st.markdown("### Battery Database")
            st.dataframe(BATTERY_ELECTRICAL_DB.get("batteries", []), width="stretch")
        with col_alt:
            st.markdown("### Alternator Database")
            st.dataframe(BATTERY_ELECTRICAL_DB.get("alternators", []), width="stretch")

        st.markdown("---")
        st.markdown("### Wiring Guides & Tips")
        for guide in BATTERY_ELECTRICAL_DB.get("wiring_guides", []):
            st.markdown(f"**{guide['topic']}**: {guide['details']}")

        st.markdown("---")
        st.markdown("### AI Battery/Electrical Recommender")
        with st.form("battery_recommender_form"):
            bat_budget = st.text_input("Budget ($)", "1000")
            bat_type = st.selectbox("Preferred Chemistry", ["Any", "LifePo4", "LTO", "AGM", "Sodium", "Li-ion", "SCiB"], index=0)
            bat_capacity = st.text_input("Minimum Capacity (Ah)", "40")
            alt_needed = st.text_input("Required Alternator Amps", "320")
            install_notes = st.text_area("Installation Constraints / Notes (optional)", "")
            bat_submit = st.form_submit_button("🔎 Recommend Battery/Electrical Setup")

            if bat_submit:
                model = get_working_model()
                if model:
                    with st.spinner("Analyzing battery/electrical database..."):
                        reqs = f"Budget: {bat_budget}, Chemistry: {bat_type}, MinCapacity: {bat_capacity}, AltAmps: {alt_needed}, Notes: {install_notes}"
                        bat_db_string = str(BATTERY_ELECTRICAL_DB)
                        bat_prompt = PROMPTS.get("BATTERY_RECOMMENDER_PROMPT", "You are the Battery/Electrical Selection Specialist.")
                        response = model.generate_content(f"{bat_prompt}\n\nUSER REQS: {reqs}\n\nDATABASE: {bat_db_string}")
                        st.markdown(response.text)

    # Onglet Headunits & Processors
    with tabs[3]:
        st.subheader("Headunits & Processors Shopping")
        col_hu, col_proc = st.columns([2, 2])
        with col_hu:
            st.markdown("### Headunit Database")
            st.dataframe(HEADUNITS_PROCESSORS_DB.get("headunits", []), width="stretch")
        with col_proc:
            st.markdown("### Processor/LOC Database")
            st.dataframe(HEADUNITS_PROCESSORS_DB.get("processors", []), width="stretch")

        st.markdown("---")
        st.markdown("### AI Headunit Recommender")
        with st.form("headunit_recommender_form"):
            hu_budget = st.text_input("Budget ($)", "600")
            chassis_type = st.selectbox("Chassis Type", ["Any", "Single DIN", "Double DIN", "Floating", "External", "Custom"], index=0)
            min_preout = st.text_input("Minimum Pre-out Voltage (V)", "4")
            eq_needed = st.selectbox("Internal EQ Needed", ["Any", "Yes", "No"], index=0)
            data_integration = st.selectbox("Data Integration", ["Any", "Yes", "No"], index=0)
            hu_notes = st.text_area("Features/Notes (Bluetooth, CarPlay, etc.)", "")
            hu_submit = st.form_submit_button("🔎 Recommend Headunits")
            if hu_submit:
                model = get_working_model()
                if model:
                    with st.spinner("Analyzing headunit database..."):
                        reqs = f"Budget: {hu_budget}, Chassis: {chassis_type}, MinPreout: {min_preout}, EQ: {eq_needed}, Data: {data_integration}, Notes: {hu_notes}"
                        hu_db_string = str(HEADUNITS_PROCESSORS_DB.get("headunits", []))
                        hu_prompt = PROMPTS.get("HEADUNIT_RECOMMENDER_PROMPT", "You are the Headunit Selection Specialist.")
                        response = model.generate_content(f"{hu_prompt}\n\nUSER REQS: {reqs}\n\nDATABASE: {hu_db_string}")
                        st.markdown(response.text)

        st.markdown("---")
        st.markdown("### AI Processor/LOC Recommender")
        with st.form("processor_recommender_form"):
            proc_budget = st.text_input("Budget ($)", "400")
            input_topology = st.selectbox("Input Topology", ["Any", "Analog RCA", "High/Low Level", "Optical", "LOC"], index=0)
            channels_in = st.text_input("Channels In", "2")
            channels_out = st.text_input("Channels Out", "4")
            active_needed = st.selectbox("Active DSP Needed", ["Any", "Yes", "No"], index=0)
            tuning = st.text_area("Tuning Needs/Notes", "")
            proc_submit = st.form_submit_button("🔎 Recommend Processor/LOC")
            if proc_submit:
                model = get_working_model()
                if model:
                    with st.spinner("Analyzing processor/LOC database..."):
                        reqs = f"Budget: {proc_budget}, Input: {input_topology}, ChannelsIn: {channels_in}, ChannelsOut: {channels_out}, Active: {active_needed}, Tuning: {tuning}"
                        proc_db_string = str(HEADUNITS_PROCESSORS_DB.get("processors", []))
                        proc_prompt = PROMPTS.get("PROCESSOR_RECOMMENDER_PROMPT", "You are the Processor/LOC Selection Specialist.")
                        response = model.generate_content(f"{proc_prompt}\n\nUSER REQS: {reqs}\n\nDATABASE: {proc_db_string}")
                        st.markdown(response.text)

    # Onglet Wiring Guide
    with tabs[4]:
        wiring_guide = WIRING_GUIDE_DB.get("wiring_guide", {})
        st.header(wiring_guide.get("title", "Wiring & Installation Master Guide"))

        # Create two columns
        col1, col2 = st.columns(2, gap="large")

        # ==========================================
        # COLUMN 1: INSTALLATION ESSENTIALS
        # ==========================================
        with col1:
            essentials = wiring_guide.get("installation_essentials", {})
            st.subheader(essentials.get("title", "🛠️ Installation Essentials"))
            st.info(essentials.get("description", "The mandatory steps for a safe, functional system."))

            for i, guide in enumerate(essentials.get("guides", [])):
                st.markdown(f"#### {guide.get('title', 'Untitled Guide')}")
                st.select_slider(
                    "Difficulty Level",
                    options=["Beginner", "Intermediate", "Advanced", "Expert"],
                    value=guide.get("difficulty", "Beginner"),
                    disabled=True,
                    key=f"essential_diff_{i}"
                )
                with st.expander(guide.get("details", {}).get("summary", "Click to Expand")):
                    st.markdown(guide.get("details", {}).get("content", ""))
                st.divider()

        # ==========================================
        # COLUMN 2: PRO TIPS & TRICKS
        # ==========================================
        with col2:
            pro_tips = wiring_guide.get("pro_tips_and_tricks", {})
            st.subheader(pro_tips.get("title", "💡 Pro Tips & Tricks"))
            st.info(pro_tips.get("description", "Hacks to make your install look and perform like a pro."))

            for i, guide in enumerate(pro_tips.get("guides", [])):
                st.markdown(f"#### {guide.get('title', 'Untitled Guide')}")
                st.select_slider(
                    "Difficulty Level",
                    options=["Beginner", "Intermediate", "Advanced", "Expert"],
                    value=guide.get("difficulty", "Beginner"),
                    disabled=True,
                    key=f"pro_tip_diff_{i}"
                )
                with st.expander(guide.get("details", {}).get("summary", "Click to Expand")):
                    st.markdown(guide.get("details", {}).get("content", ""))
                st.divider()

    # Onglet Other Accessories
    with tabs[5]:
        st.subheader("Other Accessories, Inputs, Distro Blocks, etc.")
        st.info("À compléter : Ajoutez ici la base de données des accessoires, connecteurs, distribution, etc.")

# ==============================================================================
# PAGE 3: BUILD COMPARISON
# ==============================================================================
# PAGE 4: BUILD WARS
# ==============================================================================
elif page == "⚔️ Build Wars":
    st.header("⚔️ Build Wars: The Arena")
    
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

    if st.button("🚀 FIGHT!", type="primary", width="stretch"):
        model = get_working_model()
        if model:
            with st.spinner("Simulating Battle..."):
                combined_data = "\n".join(build_data)
                response = model.generate_content(f"{COMPARISON_PROMPT}\n\nDATA:\n{combined_data}")
                st.success(response.text)

# ==============================================================================
# PAGE 4: BEGINNER'S GUIDE
# ==============================================================================
elif page == "🎓 Beginner's Guide":
    st.header("🎓 Beginner's Guide: System Questionnaire")
    st.write("Configure your preferences below. The package prices will update in real-time based on your choices. Finally, select a package and build your plan.")

    # --- TUTORIAL SYSTEM INITIALIZATION ---
    if 'tutorial_mode' not in st.session_state:
        st.session_state.tutorial_mode = False
    if 'tutorial_step' not in st.session_state:
        st.session_state.tutorial_step = 0

    

    # Tutorial steps definition
    TUTORIAL_STEPS = [
        {
            "title": "📖 Welcome to Beginner's Guide!",
            "description": "This guide will help you configure your perfect car audio system. Let's start by understanding what you need.",
            "target": "music_genres"
        },
        {
            "title": "🎵 Music Genres",
            "description": "Select the music genres you listen to most. This helps the AI recommend components that match your listening style. For example, electronic music benefits from deeper bass, while classical music needs clarity.",
            "target": "music_genres"
        },
        {
            "title": "🔊 Sound Preference",
            "description": "Choose what's most important to you:\n• Balance: All-around good sound\n• Bass: Deep, powerful lows\n• Clarity: Crisp, detailed highs and vocals",
            "target": "sound_preference"
        },
        {
            "title": "🚗 Vehicle Information",
            "description": "Enter your car's details (Make, Model, Year). This helps determine available space and power limitations for your system.",
            "target": "car_info"
        },
        {
            "title": "📦 Current Setup",
            "description": "Tell us what audio equipment you already have:\n• Stock: Factory system\n• Aftermarket HU: Already have an aftermarket headunit\n• Aftermarket Speakers: Already have upgraded speakers",
            "target": "current_setup"
        },
        {
            "title": "📈 Loudness Goal",
            "description": "How loud do you want your system?\n• Subtle: Just above factory\n• Lively: Good for everyday driving\n• Loud/Very Loud: Requires significant power upgrades\n• Competition: Maximum output for contests",
            "target": "loudness_preference"
        },
        {
            "title": "🔧 Installation Plan",
            "description": "Choose your installation method:\n• DIY: You install it yourself (saves money)\n• Professional: Expert installation (adds cost but ensures quality)",
            "target": "installation_plan"
        },
        {
            "title": "🎯 Audio Goal",
            "description": "Define your primary audio goal:\n• Audiophile (SQ): Pure sound quality\n• SPL (Bass): Maximum loudness\n• SQL (Balanced): Mix of quality and loudness",
            "target": "goal_point"
        },
        {
            "title": "✨ Aesthetic Goal",
            "description": "Choose your installation style:\n• Function over form: Basic, hidden installation\n• Luxury/Beauty: Custom fabrication and premium materials (higher cost)",
            "target": "aesthetic_focus"
        },
        {
            "title": "🎚️ Enclosure Type",
            "description": "Select your subwoofer enclosure design:\n• Sealed: Accurate, tight bass\n• Ported: Louder, boomy bass\n• Bandpass: Extreme SPL output\n• No Wall: Maximum flex and power\n• Wall Setups: Space-efficient designs",
            "target": "enclosure_type"
        },
        {
            "title": "💰 Component Strategy",
            "description": "How should we allocate your budget?\n• Balanced: Equal across amp, sub, enclosure\n• Amp & Enclosure Focus: Save on sub, maximize SPL\n• Speaker Quality Focus: Budget amp, premium subs",
            "target": "component_strategy"
        },
        {
            "title": "💎 Project Tier",
            "description": "Select your budget tier:\n• Budget SPL: Maximum loudness on a budget\n• Essential: Great starter system\n• Enhanced: Powerful and clear\n• Audiophile: Premium components\n• Competition: Top-tier everything",
            "target": "tier_selection"
        },
        {
            "title": "✅ Ready to Go!",
            "description": "You've completed the guide! Now select your tier and click 'Build My Plan' to get AI-powered recommendations tailored to your preferences.",
            "target": None
        }
    ]

    

    # Tutorial CSS for spotlight effect and smart bubble positioning
    tutorial_css = """
    <style>
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .tutorial-spotlight {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        z-index: 998;
        pointer-events: none;
    }
    
    .tutorial-highlight {
        position: fixed;
        border: 3px solid #FF6B35;
        border-radius: 8px;
        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7);
        z-index: 999;
        pointer-events: none;
    }
    
    .tutorial-bubble {
        position: fixed;
        background: white;
        border: 2px solid #FF6B35;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
        z-index: 1000;
        max-width: 350px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        animation: slideIn 0.3s ease-out;
    }
    
    .tutorial-bubble h3 {
        margin: 0 0 12px 0;
        color: #FF6B35;
        font-size: 18px;
        font-weight: 600;
    }
    
    .tutorial-bubble p {
        margin: 0 0 16px 0;
        color: #333;
        line-height: 1.5;
        font-size: 14px;
        white-space: pre-wrap;
    }
    
    .tutorial-bubble-arrow {
        position: absolute;
        width: 0;
        height: 0;
        border-style: solid;
    }
    
    .tutorial-bubble-arrow.arrow-left {
        left: -12px;
        top: 30px;
        border-width: 8px 12px 8px 0;
        border-color: transparent white transparent transparent;
    }
    
    .tutorial-bubble-arrow.arrow-right {
        right: -12px;
        top: 30px;
        border-width: 8px 0 8px 12px;
        border-color: transparent transparent transparent white;
    }
    
    .tutorial-bubble-arrow.arrow-top {
        top: -12px;
        left: 30px;
        border-width: 0 8px 12px 8px;
        border-color: transparent transparent white transparent;
    }
    
    .tutorial-bubble-arrow.arrow-bottom {
        bottom: -12px;
        left: 30px;
        border-width: 12px 8px 0 8px;
        border-color: white transparent transparent transparent;
    }
    
    .tutorial-progress {
        margin: 12px 0 0 0;
        padding-top: 12px;
        border-top: 1px solid #eee;
        text-align: center;
        color: #999;
        font-size: 12px;
        font-weight: 500;
    }
    
    .tutorial-buttons-container {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        margin-top: 16px;
    }
    </style>
    """

    # Display tutorial controls in header
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col2:
        if st.button("📚 Start Tutorial", key="tutorial_start"):
            st.session_state.tutorial_mode = True
            st.session_state.tutorial_step = 0
            st.rerun()
    
    with header_col3:
        if st.session_state.tutorial_mode and st.button("✕ Close Tutorial", key="tutorial_close"):
            st.session_state.tutorial_mode = False
            st.rerun()

    # Render tutorial if active
    if st.session_state.tutorial_mode:
        st.markdown(tutorial_css, unsafe_allow_html=True)
        st.markdown("""<div class="tutorial-spotlight"></div>""", unsafe_allow_html=True)
        
        current_step = st.session_state.tutorial_step
        if current_step < len(TUTORIAL_STEPS):
            step_data = TUTORIAL_STEPS[current_step]
            
            # Determine bubble position based on step
            # Position: right side by default, left if on right side, bottom if on form
            bubble_position = "right"
            arrow_direction = "arrow-left"
            top_offset = "30%"
            left_offset = "55%"
            
            # Adjust position based on which section we're in
            if current_step < 3:
                top_offset = "18%"
                left_offset = "68%"
                arrow_direction = "arrow-left"
            elif current_step < 6:
                top_offset = "40%"
                left_offset = "68%"
                arrow_direction = "arrow-left"
            elif current_step < 9:
                top_offset = "55%"
                left_offset = "20%"
                arrow_direction = "arrow-right"
            elif current_step < 12:
                top_offset = "70%"
                left_offset = "68%"
                arrow_direction = "arrow-left"
            else:
                top_offset = "12%"
                left_offset = "50%"
                arrow_direction = "arrow-bottom"
            
            # Create arrow HTML
            arrow_html = f'<div class="tutorial-bubble-arrow {arrow_direction}"></div>'

            # Highlight coordinates per step (top, left, width, height)
            HIGHLIGHTS = {
                0: ("6%","6%","30%","12%"),
                1: ("6%","6%","30%","12%"),
                2: ("6%","6%","30%","12%"),
                3: ("22%","6%","30%","14%"),
                4: ("22%","6%","30%","14%"),
                5: ("38%","6%","30%","14%"),
                6: ("38%","6%","30%","14%"),
                7: ("52%","6%","30%","14%"),
                8: ("52%","6%","30%","14%"),
                9: ("68%","6%","30%","14%"),
                10: ("68%","6%","30%","14%"),
                11: ("68%","6%","30%","14%"),
                12: ("10%","40%","20%","10%")
            }

            hl_top, hl_left, hl_w, hl_h = HIGHLIGHTS.get(current_step, ("40%","6%","30%","14%"))
            highlight_html = f"""
            <div class="tutorial-highlight" style="top: {hl_top}; left: {hl_left}; width: {hl_w}; height: {hl_h};"></div>
            """

            # Create tutorial bubble HTML with action links (change query params)
            prev_link = f"?tutorial_action=prev&step={current_step}"
            next_link = f"?tutorial_action=next&step={current_step}"
            close_link = f"?tutorial_action=close&step={current_step}"

            buttons_html = ""
            if current_step > 0:
                buttons_html += f'<a href="{prev_link}" class="tutorial-btn" style="background:#e0e0e0;color:#333;padding:8px 12px;border-radius:6px;text-decoration:none;margin-right:6px;">← Prev</a>'
            if current_step < len(TUTORIAL_STEPS) - 1:
                buttons_html += f'<a href="{next_link}" class="tutorial-btn" style="background:#FF6B35;color:white;padding:8px 12px;border-radius:6px;text-decoration:none;margin-right:6px;">Next →</a>'
            else:
                buttons_html += f'<a href="{next_link}" class="tutorial-btn" style="background:#4CAF50;color:white;padding:8px 12px;border-radius:6px;text-decoration:none;margin-right:6px;">Done! ✓</a>'
            buttons_html += f'<a href="{close_link}" class="tutorial-btn" style="background:#999;color:white;padding:8px 10px;border-radius:6px;text-decoration:none;">✕</a>'

            bubble_html = f"""
            {highlight_html}
            <div class="tutorial-bubble" style="top: {top_offset}; left: {left_offset};">
                {arrow_html}
                <h3>{step_data['title']}</h3>
                <p>{step_data['description']}</p>
                <div class="tutorial-buttons-container">
                    {buttons_html}
                </div>
                <div class="tutorial-progress">Step {current_step + 1} of {len(TUTORIAL_STEPS)}</div>
            </div>
            """
            st.markdown(bubble_html, unsafe_allow_html=True)

    # --- INITIALIZE SESSION STATE FOR SELECTIONS ---
    if 'bg_selected_tier' not in st.session_state:
        st.session_state.bg_selected_tier = "Enhanced" # Default selection

    # --- TIER AND MODIFIER DEFINITIONS ---
    TIERS = {
        "Budget SPL": {"name": "Budget SPL Warrior", "base_min": 800, "base_max": 2000, "desc": "Entry-level setup: Budget-friendly amp (e.g., Taramps), affordable subwoofer(s), and enclosure. Maximize loudness without premium component costs."},
        "Essential": {"name": "Essential Sound", "base_min": 400, "base_max": 800, "desc": "Upgrades main speakers and adds a compact amp. A great step up from factory sound."},
        "Enhanced": {"name": "Enhanced Fidelity", "base_min": 1000, "base_max": 2500, "desc": "Aftermarket headunit, component speakers, amplifier, and a dedicated subwoofer. Powerful, clear sound with deep bass."},
        "Audiophile": {"name": "Audiophile Experience", "base_min": 2500, "base_max": 5000, "desc": "High-end speakers, multiple amps, DSP for precise tuning, and sound deadening. Ultimate clarity and impact."},
        "Competition": {"name": "Competition Grade", "base_min": 5000, "base_max": 15000, "desc": "Top-of-the-line everything, custom fabrication, and major electrical upgrades. For winning competitions."}
    }
    MODIFIERS = {
        "pro_install_percent": 0.25,
        "simple_install_discount_percent": -0.05,
        "luxury_percent": 0.40,
        "aftermarket_radio_cost": 400,
        "audiophile_percent": 0.30,
        "spl_percent": 0.15,
        "sql_percent": 0.20
    }

    # --- INTERACTIVE CONTROLS (OUTSIDE THE FORM) ---
    st.subheader("Your Listening Style & Vehicle")
    c1, c2, c3 = st.columns(3)
    with c1:
        music_genres = st.multiselect(
            "Music Genres",
            ["Rock", "Pop", "Hip-Hop / Rap", "Electronic (EDM)", "Country", "Jazz / Classical", "Metal", "Other"],
            key="bg_music_genres",
            help="Select the music you listen to most. This helps the AI choose components (like subwoofers and speakers) that are best suited for your taste."
        )
        sound_preference = st.radio(
            "Sound Preference",
            ("Balance", "Bass", "Clarity"),
            key="bg_sound_preference", horizontal=True,
            help="Tell us what's most important to you. 'Balance' for an all-around system. 'Bass' for deep, powerful lows. 'Clarity' for crisp, detailed highs and vocals."
        )
    with c2:
        car_info = st.text_input("Make, Model, Year", key="bg_car_info", placeholder="e.g., 2015 Ford F-150", help="Enter your vehicle's details. This helps determine available space, and potential need for specific integrations (like a new headunit or processor).")
        current_setup = st.radio(
            "Current Setup",
            ("Stock", "Aftermarket HU", "Aftermarket Speakers"),
            key="bg_current_setup", horizontal=True,
            help="Let us know what's already in your car. 'Stock' means no changes. If you have an 'Aftermarket HU' (Headunit/Radio) or 'Speakers', the AI will factor that into the plan."
        )
    with c3:
        loudness_preference = st.select_slider("Loudness Goal", options=["Subtle", "Lively", "Loud", "Very Loud", "Competition"], key="bg_loudness", help="How loud do you want it? 'Subtle' is just above stock. 'Lively' is for spirited driving. 'Loud' and 'Very Loud' require significant power and component upgrades. 'Competition' is for extreme performance.")


    st.subheader("Installation & Aesthetics")
    c4, c5, c6 = st.columns(3)
    with c4:
        installation_plan = st.radio(
            "Installation Plan",
            ("DIY (Do-It-Yourself)", "Professional Install"),
            key="bg_installation_plan",
            help="Choose 'DIY' if you plan to install the system yourself. Choose 'Professional Install' to have an expert do it, which will add a significant cost percentage to the final estimate."
        )
        goal_point = st.radio(
            "Goal Point",
            ("Audiophile (SQ)", "SPL (Bass)", "SQL (Balanced)"),
            key="bg_goal_point",
            help="Define your primary audio goal. 'Audiophile' focuses on pristine sound quality. 'SPL' focuses on maximum loudness and bass. 'SQL' provides a mix of quality and loudness."
        )

    with c5:
        aesthetic_focus = st.radio(
            "Aesthetic Goal",
            ("Function over form", "Luxury/Beauty Finish"),
            key="bg_aesthetic_focus",
            help="Choose 'Function over form' for a basic, hidden installation. Choose 'Luxury/Beauty Finish' for custom fabrication, lighting, and premium materials, which increases the cost."
        )
    
    with c6:
        decibel_goal = st.text_input(
            "Decibel Goal (dB)",
            key="bg_decibel_goal",
            placeholder="e.g., 140 (Optional)",
            help="Enter a specific decibel number you want to achieve. Leave empty if you want the AI to recommend a level based on your other choices. This will influence component selection."
        )
        install_complexity = st.checkbox(
            "Keep the install simple?",
            key="bg_install_complexity",
            value=True,
            help="Check this to prioritize components and designs that are easier to install, avoiding complex custom fabrication like fiberglass or welded metal racks."
        )

    st.subheader("Subwoofer Enclosure & Component Strategy")
    c7, c8 = st.columns(2)
    with c7:
        enclosure_type = st.selectbox(
            "Enclosure Type",
            ("Sealed", "Ported (Vented)", "4th Order Bandpass", "6th Order Bandpass", "No Wall (Free Air)", "Trunk Wall (Reflected)", "B-Pillar/C-Pillar Wall"),
            key="bg_enclosure_type",
            help="Choose the enclosure design based on your vehicle and sound goals. Sealed = accurate, tight bass. Ported = louder, boomy bass. Bandpass = extreme SPL. No Wall = flex and power. Wall setups = space efficiency."
        )
    with c8:
        component_strategy = st.selectbox(
            "Component Budget Strategy",
            ("Balanced", "Amp & Enclosure Focus (Budget Parts)", "Speaker Quality Focus (Economy Amp)"),
            key="bg_component_strategy",
            help="'Balanced' = equal budget across amp, sub, enclosure. 'Amp & Enclosure Focus' = save on sub quality, invest in amp & enclosure for extreme SPL. 'Speaker Quality Focus' = budget amp, invest in high-quality subwoofers and processing."
        )
    st.divider()

    # --- DYNAMIC PACKAGE CARDS ---
    st.subheader("Select Your Project Tier")

    def calculate_price(base_min, base_max, tier_name, goal_point):
        min_price, max_price = base_min, base_max
        
        # Apply goal point modifier
        if goal_point == "Audiophile (SQ)":
            min_price *= (1 + MODIFIERS["audiophile_percent"])
            max_price *= (1 + MODIFIERS["audiophile_percent"])
        elif goal_point == "SPL (Bass)":
            min_price *= (1 + MODIFIERS["spl_percent"])
            max_price *= (1 + MODIFIERS["spl_percent"])
        elif goal_point == "SQL (Balanced)":
            min_price *= (1 + MODIFIERS["sql_percent"])
            max_price *= (1 + MODIFIERS["sql_percent"])

        # For Budget SPL tier, no additional headunit cost
        if tier_name == "Budget SPL":
            pass  # Budget tier is minimal
        # Add headunit cost if needed for other tiers
        elif current_setup == "Stock" and tier_name in ["Enhanced", "Audiophile", "Competition"]:
            min_price += MODIFIERS["aftermarket_radio_cost"]
            max_price += MODIFIERS["aftermarket_radio_cost"]

        # Pro install cost
        if installation_plan == "Professional Install":
            install_mod = MODIFIERS["pro_install_percent"]
            if install_complexity:
                 install_mod += MODIFIERS["simple_install_discount_percent"]
            min_price *= (1 + install_mod)
            max_price *= (1 + install_mod)

        # Luxury finish cost
        if aesthetic_focus == "Luxury/Beauty Finish":
            min_price *= (1 + MODIFIERS["luxury_percent"])
            max_price *= (1 + MODIFIERS["luxury_percent"])
            
        return f"${int(min_price):,} - ${int(max_price):,}"

    card_cols = st.columns(len(TIERS))

    for i, (tier_key, tier_info) in enumerate(TIERS.items()):
        with card_cols[i]:
            is_selected = (st.session_state.bg_selected_tier == tier_key)
            with st.container(border=True):
                st.markdown(f"#### {tier_info['name']}")
                price_range = calculate_price(tier_info['base_min'], tier_info['base_max'], tier_key, goal_point)
                st.markdown(f"**Price Range:** {price_range}")
                st.markdown(f"<small>{tier_info['desc']}</small>", unsafe_allow_html=True)
                
                # Use a callback to set the selected tier
                if st.button(f"Select {tier_key}", key=f"select_{tier_key}", type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state.bg_selected_tier = tier_key
                    st.rerun() # Rerun to update the button styles
    st.divider()

    # --- SUBMISSION FORM ---
    with st.form("beginner_submission"):
        st.info(f"**Selected Package:** {st.session_state.bg_selected_tier}")
        submitted = st.form_submit_button("Build My Plan", use_container_width=True, type="primary")

        if submitted:
            # Re-fetch values from session state for clarity
            selected_tier_info = TIERS[st.session_state.bg_selected_tier]
            final_price_range = calculate_price(selected_tier_info['base_min'], selected_tier_info['base_max'], st.session_state.bg_selected_tier, st.session_state.bg_goal_point)

            model = get_working_model()
            if model:
                with st.spinner("Searching Gear Lab and building two systems for you..."):
                    # Consolidate user questionnaire data
                    questionnaire_data = (
                        f"Music Genres: {', '.join(st.session_state.bg_music_genres)}\n"
                        f"Sound Preference: {st.session_state.bg_sound_preference}\n"
                        f"Loudness Preference: {st.session_state.bg_loudness}\n"
                        f"Vehicle: {st.session_state.bg_car_info}\n"
                        f"Current Setup: {st.session_state.bg_current_setup}\n"
                        f"Selected Tier: {selected_tier_info['name']}\n"
                        f"Estimated Final Price Range: {final_price_range}\n"
                        f"Installation Plan: {st.session_state.bg_installation_plan}\n"
                        f"Keep Install Simple: {'Yes' if st.session_state.bg_install_complexity else 'No'}\n"
                        f"Aesthetic Goal: {st.session_state.bg_aesthetic_focus}\n"
                        f"Goal Point: {st.session_state.bg_goal_point}\n"
                        f"Decibel Goal: {st.session_state.bg_decibel_goal if st.session_state.bg_decibel_goal else 'Not Specified'}\n"
                        f"Enclosure Type: {st.session_state.bg_enclosure_type}\n"
                        f"Component Budget Strategy: {st.session_state.bg_component_strategy}"
                    )

                    # Create the new detailed prompt that includes the databases
                    beginner_prompt = f"""
You are a world-class car audio system designer for beginners. Your task is to create two complete, distinct car audio systems based on the user's preferences and budget, using the provided equipment databases.

**CRITICAL INSTRUCTIONS:**
1.  **Use Provided Databases:** You MUST select specific components (subwoofers, amplifiers, headunits, processors) from the JSON databases provided below. Do not invent components.
2.  **Create Two Distinct Builds:** Design two different system options that fit the user's goals. For example, one focused more on sound quality (SQ) and one on loudness/bass (SPL), or two different brands. Give each build a descriptive name (e.g., "The Clarity Build," "The Budget Basshead Build").
3.  **Respect Enclosure & Strategy:** The user has specified an enclosure type (e.g., sealed, ported, bandpass, no-wall, trunk-wall) and a component budget strategy. Use these to guide your recommendations:
    - If "Amp & Enclosure Focus": Prioritize affordable but powerful amps (like Taramps) and excellent enclosure design. Sub quality is secondary.
    - If "Speaker Quality Focus": Recommend high-quality subwoofers with a quality amp, but an economy-grade amplifier.
    - If "Balanced": Spread the budget equally across amp, sub, and enclosure quality.
4.  **Stay Within Budget:** The total cost of the components for each build MUST fall within the user's "Estimated Final Price Range". You must show the estimated total price for each build.
5.  **Explain Your Choices:** For each component in each build, briefly explain WHY you chose it and how it fits the user's goals (music taste, loudness, budget, enclosure type, strategy, etc.).
6.  **Handle Missing Components:** The databases may not include all necessary parts (like door speakers or wiring kits). If a required component is not in the database, you must:
    a. Recommend a *type* and *size* of component (e.g., "6.5-inch Component Speakers").
    b. Suggest a reasonable estimated price for that missing item.
    c. Include this estimated price in the build's total cost.
7.  **Output Format:** Present the two builds clearly and separately. Use Markdown for formatting (e.g., headers, bold text, lists).

**USER'S QUESTIONNAIRE:**
---
{questionnaire_data}
---

**COMPONENT DATABASES (GEAR LAB):**
---
**Subwoofers:**
{json.dumps(SUBWOOFER_DB, indent=2)}

**Amplifiers:**
{json.dumps(AMPLIFIER_DB, indent=2)}

**Headunits and Processors:**
{json.dumps(HEADUNITS_PROCESSORS_DB, indent=2)}
---
"""
                    
                    # Generate the recommendation
                    response = model.generate_content(beginner_prompt)
                    st.markdown(response.text)