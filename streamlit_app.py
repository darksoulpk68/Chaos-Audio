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

    return sub_db, model_list, prompts, amplifier_db, battery_electrical_db, headunits_processors_db

SUBWOOFER_DB, MODEL_LIST, PROMPTS, AMPLIFIER_DB, BATTERY_ELECTRICAL_DB, HEADUNITS_PROCESSORS_DB = load_data()

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
    if st.button("🎛️ Design Studio", use_container_width=True):
        st.session_state["page"] = "🎛️ Design Studio"
        
    if st.button("🧪 Gear Lab", use_container_width=True):
        st.session_state["page"] = "🧪 Gear Lab"
        
    if st.button("⚔️ Build Comparison", use_container_width=True):
        st.session_state["page"] = "⚔️ Build Comparison"
    
    # Optional: allow user to add a short extra prompt used by the simulator
    st.markdown("---")
    st.markdown("#### Prompt Addition (optional)")
    st.text_area("Add extra instructions for the simulator (optional)", key="add_prompt", height=80)
    # Ensure `add_prompt` exists in session state and mirror it to a local variable
    if 'add_prompt' not in st.session_state:
        st.session_state['add_prompt'] = ""
    add_prompt = st.session_state.get('add_prompt', "")

    # Pass the session state to the variable the rest of the app expects
    page = st.session_state["page"]

    st.markdown("---")
    
    # Dynamic Tip based on current page
    if page == "🎛️ Design Studio":
        st.info("💡 **Tip:** Use this mode for deep, single-vehicle simulation.")
    elif page == "🧪 Gear Lab":
        st.info("💡 **Tip:** Use the AI Recommender to find subs that fit your music style.")
    elif page == "⚔️ Build Comparison":
        st.info("💡 **Tip:** Great for deciding between two different subwoofer brands.")

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
            comments = st.text_area("Describe your goals or your actual build, giving as much information as possible", "e.g. 'Lithium bank, chasing hairtricks'")

        if st.button("🚀 INITIATE SIMULATION", type="primary", use_container_width=True):
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
            st.dataframe(SUBWOOFER_DB, use_container_width=True)

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
            st.dataframe(AMPLIFIER_DB, use_container_width=True)

    # Onglet Battery & Electrical
    with tabs[2]:
        st.subheader("Battery Setups & Electrical Requirements")
        col_bat, col_alt = st.columns([2, 1])
        with col_bat:
            st.markdown("### Battery Database")
            st.dataframe(BATTERY_ELECTRICAL_DB.get("batteries", []), use_container_width=True)
        with col_alt:
            st.markdown("### Alternator Database")
            st.dataframe(BATTERY_ELECTRICAL_DB.get("alternators", []), use_container_width=True)

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
            st.dataframe(HEADUNITS_PROCESSORS_DB.get("headunits", []), use_container_width=True)
        with col_proc:
            st.markdown("### Processor/LOC Database")
            st.dataframe(HEADUNITS_PROCESSORS_DB.get("processors", []), use_container_width=True)

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
        st.subheader("Wiring Guide: Tips & Tricks")

        # Tip 1: The Big Three
        st.markdown("#### 1. The 'Big Three' Upgrade")
        st.select_slider(
            "Installation Difficulty",
            options=["Begginer", "Intermediate", "Advanced", "Expert"],
            value="Begginer",
            disabled=True,
            key="diff_1"
        )
        with st.expander("What is the 'Big Three' and why do it? (Click to Expand)"):
            st.markdown("""
            The "Big Three" upgrade is a fundamental step for any car audio system that requires more power than the stock electrical system can handle. It involves upgrading three key cables:

            1.  **Alternator Positive to Battery Positive:** This allows the high-output current from your alternator to flow more efficiently to your battery.
            2.  **Battery Negative to Chassis Ground:** This improves the main ground connection for your entire vehicle's electrical system.
            3.  **Engine Block to Chassis Ground:** This ensures a solid ground path for the engine and alternator.

            **Why do it?**
            -   **Reduces Voltage Drop:** Prevents your headlights from dimming when the bass hits.
            -   **Improves Alternator Performance:** Allows your alternator to charge the battery more effectively.
            -   **Provides a Stable Foundation:** Essential before adding a high-output alternator or a second battery.

            **Materials:**
            -   1/0 AWG (or larger) Oxygen-Free Copper (OFC) wire.
            -   High-quality ring terminals.
            -   Hydraulic crimper and heat shrink for secure connections.
            """)

        st.divider()

        # Tip 2: Properly Setting Gains
        st.markdown("#### 2. Properly Setting Amplifier Gains")
        st.select_slider(
            "Installation Difficulty",
             options=["Begginer", "Intermediate", "Advanced", "Expert"],
            value="Begginer",
            disabled=True,
            key="diff_2"
        )
        with st.expander("Stop using your ears! Use a tool. (Click to Expand)"):
            st.markdown("""
            Setting your amplifier's gain is NOT a volume knob. Its purpose is to match the output voltage of your headunit to the input sensitivity of your amplifier. Setting it incorrectly is the #1 way to destroy subwoofers.

            **Why do it correctly?**
            -   **Prevents Clipping:** A clipped signal is a squared-off waveform that generates excessive heat in your subwoofer's voice coil, leading to failure.
            -   **Maximizes Clean Power:** Ensures you get the most clean, undistorted power from your amplifier.
            -   **Protects Your Investment:** Saves you from costly repairs or replacements.

            **How to do it (The Right Way):**
            1.  **Get the Tools:** You need a Digital Multi-Meter (DMM) that can read AC Voltage or an oscilloscope.
            2.  **Calculate Target Voltage:** Use the formula `sqrt(Power * Resistance) = Target Voltage`. For example, for a 1000W amp at 1-ohm, the target is `sqrt(1000 * 1) = 31.6V`.
            3.  **Use a Test Tone:** Download a 40Hz test tone (for subwoofers) recorded at 0dBFS.
            4.  **Disconnect Speakers:** Unplug your subwoofers from the amplifier.
            5.  **Set Headunit Volume:** Turn your headunit volume to about 75% of its maximum.
            6.  **Measure and Adjust:** Play the test tone. Connect your DMM to the amplifier's speaker outputs and adjust the gain knob until the voltage on the meter matches your calculated target voltage.
            7.  **You're Done!** Reconnect your speakers. Your gains are now set cleanly.
            """)

        st.divider()

        # Tip 3: Sound Deadening
        st.markdown("#### 3. Strategic Sound Deadening")
        st.select_slider(
            "Installation Difficulty",
             options=["Begginer", "Intermediate", "Advanced", "Expert"],
            value="Intermediate",
            disabled=True,
            key="diff_3"
        )
        with st.expander("It's more than just stopping rattles. (Click to Expand)"):
            st.markdown("""
            Sound deadening is often seen as just a way to stop annoying rattles, but it plays a crucial role in improving sound quality and overall system efficiency.

            **Why do it?**
            -   **Lowers Road Noise:** A quieter cabin means you don't have to turn the music up as loud, reducing distortion.
            -   **Improves Bass Response:** By controlling panel vibrations, you hear more of the actual bass from your subwoofers and less from the vibrating metal of your car. This is often called "free SPL."
            -   **Reduces Panel Flex:** Stiffens the metal panels of your car, making them less likely to flex and fatigue over time.

            **Levels of Treatment:**
            -   **Level 1 (The Basics):** Apply Constrained Layer Damper (CLD) tiles to large, flat metal surfaces like the outer door skin, inner door skin, and trunk lid. Aim for about 25-50% coverage.
            -   **Level 2 (The Full Monty):** After CLD, add a layer of Closed Cell Foam (CCF) on top to decouple rattling plastic panels from the metal chassis.
            -   **Level 3 (The Seal):** For ultimate performance, cover the CCF with a layer of Mass Loaded Vinyl (MLV) to block airborne sound waves. This is the most effective but also the most difficult and expensive step.

            **Pro Tip:** Don't forget the roof! It's a large, flat panel that can be a major source of unwanted vibrations.
            """)
                        
        st.divider()

        # Tip 4: Adding a Second Battery
        st.markdown("#### 4. Safely Adding a Second Battery")
        st.select_slider(
            "Installation Difficulty",
             options=["Begginer", "Intermediate", "Advanced", "Expert"],
            value="Expert",
            disabled=True,
            key="diff_4"
        )
        with st.expander("Isolators vs. Direct Connection (Click to Expand)"):
            st.markdown("""
            Adding a second battery (or a bank of batteries) is necessary for high-power systems that exceed the capacity of a single starting battery and alternator. However, doing it wrong is incredibly dangerous.

            **Why do it?**
            -   **Massive Current Reserve:** Provides the instant current your amplifiers need during heavy bass notes, preventing voltage drop.
            -   **System Stability:** Keeps voltage stable, which is critical for amplifier performance and longevity.
            -   **Play Longer:** Allows you to play the system with the engine off (if designed correctly).

            **The Great Debate: Isolator vs. No Isolator**
            -   **With an Isolator:** A battery isolator (a large relay) is placed on the positive power wire between your front battery and your rear battery bank. It automatically disconnects the rear bank when the vehicle is off, ensuring you never drain your starting battery. **This is the recommended method for 99% of users.**
            -   **Without an Isolator (Direct Connection):** This connects the batteries permanently in parallel. This is only safe if ALL batteries in the system are of the *exact same chemistry and age*. Mixing an AGM under the hood with a Lithium in the back without an isolator is a recipe for disaster, as they will constantly try to charge/discharge each other, leading to reduced lifespan and a potential fire risk.

            **Critical Safety Rules:**
            1.  **ALWAYS FUSE:** Every power wire run must be fused on BOTH ends, as close to the battery terminals as possible. If a wire shorts to ground, the fuse is the only thing preventing a major electrical fire.
            2.  **Match Chemistries or Isolate:** Never mix battery types without a proper isolator.
            3.  **Ground Securely:** Ensure your rear battery has a solid ground connection to the vehicle's frame, equal in size to the power wire.
            4.  **Ventilation:** If using non-sealed batteries (like some AGMs), ensure they are properly ventilated to the outside of the vehicle.
            """)

    # Onglet Other Accessories
    with tabs[5]:
        st.subheader("Other Accessories, Inputs, Distro Blocks, etc.")
        st.info("À compléter : Ajoutez ici la base de données des accessoires, connecteurs, distribution, etc.")

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