import streamlit as st
import numpy as np
import pandas as pd
import random
import os
import plotly.graph_objects as go
import plotly.express as px

try:
    import h5py
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import RepositoryNotFoundError, HfHubHTTPError, GatedRepoError
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

st.set_page_config(page_title="POMDP Smart Scan Scheduler", layout="wide", page_icon="")

# Initialize session state for caching run history
if 'run_history' not in st.session_state:
    st.session_state.run_history = []

# --- UI Enhancements: Custom CSS ---
st.markdown("""
<style>
.metric-box {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
.metric-title { font-size: 14px; color: #555; }
.metric-value { font-size: 24px; font-weight: bold; color: #1f77b4; }
</style>
""", unsafe_allow_html=True)

st.title("POMDP Belief-State Smart Scan Scheduler")
st.markdown("""
Welcome to the interactive demonstration for **SIH 26055: Smart Scan Strategy for Electronic Warfare**.
This application compares open-loop receiver scanning against an intelligent **Partially Observable Markov Decision Process (POMDP)** scheduler.
""")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Simulation Parameters")
    NUM_BANDS = st.slider("Number of Frequency Bands", 5, 100, 20, help="Total number of discrete frequency bands in the spectrum.")
    NUM_STEPS = st.slider("Simulation Time Steps", 100, 10000, 300, step=100)
    
    st.header("Receiver Hardware Limits")
    PD = st.slider("Probability of Detection (Pd)", 0.5, 1.0, 0.9, help="Likelihood of detecting a true signal.")
    PFA = st.slider("Probability of False Alarm (Pfa)", 0.0, 0.5, 0.05, help="Likelihood of detecting a signal when none exists.")

    st.header("Dataset / Environment")
    use_hf_dataset = st.checkbox("Use Turing Radar Dataset (HuggingFace)", value=True)
    hf_token = st.text_input("HF Access Token (Optional)", type="password", help="Enter your valid HF token to access the gated dataset.")
    
    st.header("Time-Forwarding (Warm-up)")
    WARMUP_STEPS = st.slider("AI Pre-training Steps (Simulate 1 hour of prior operation)", 0, 5000, 0, step=500, help="Allow the AI to run silently on the environment to build up its belief state before the visual simulation begins.")
    
    st.markdown("### Synthetic Emitter Settings (Fallback)")
    col1, col2 = st.columns(2)
    with col1:
        num_static = st.number_input("Static", 0, 10, 1)
        num_agile = st.number_input("Freq Agile", 0, 10, 1)
    with col2:
        num_periodic = st.number_input("Periodic", 0, 10, 1)
    
    if st.button("Clear Run History"):
        st.session_state.run_history = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("Developed for DRDO IDEX Problem 26055.")

# --- Environment & Dataset Simulation ---
@st.cache_data
def generate_ground_truth(steps, bands, n_stat, n_per, n_agi):
    gt = np.zeros((steps, bands), dtype=int)
    for _ in range(n_stat):
        b = random.randint(0, bands-1)
        gt[:, b] = 1
    for _ in range(n_per):
        b = random.randint(0, bands-1)
        period = random.randint(5, 20)
        phase = random.randint(0, period-1)
        for t in range(steps):
            if (t + phase) % period < (period // 3):
                gt[t, b] = 1
    for _ in range(n_agi):
        current_b = random.randint(0, bands-1)
        for t in range(steps):
            gt[t, current_b] = 1
            if random.random() < 0.1:
                current_b = random.randint(0, bands-1)
    return gt

def get_hf_token():
    if hf_token: return hf_token
    if "HF_TOKEN" in st.secrets: return st.secrets["HF_TOKEN"]
    return None

@st.cache_data
def load_turing_dataset(steps, bands, token):
    try:
        path = hf_hub_download(
            repo_id='alan-turing-institute/turing-synthetic-radar-dataset', 
            filename='archive/train/train_0.h5', 
            repo_type='dataset',
            token=token
        )
        with h5py.File(path, 'r') as f:
            data = f['data'][:] 
        times = data[:, 0]
        rfs = data[:, 1]
        sorted_indices = np.argsort(times)
        rfs = rfs[sorted_indices]
        rf_min, rf_max = np.min(rfs), np.max(rfs)
        if rf_max > rf_min:
            discrete_bands = ((rfs - rf_min) / (rf_max - rf_min) * (bands - 1)).astype(int)
        else:
            discrete_bands = np.zeros(len(rfs), dtype=int)
        gt = np.zeros((steps, bands), dtype=int)
        for i in range(steps):
            # Crude looping: if steps > 6503, loop back to the start of the file
            data_idx = i % len(discrete_bands)
            band_idx = discrete_bands[data_idx]
            gt[i, band_idx] = 1
        return gt, True
    except GatedRepoError:
        return None, "ACCESS_DENIED"
    except HfHubHTTPError as e:
        if e.response.status_code == 401:
            return None, "INVALID_TOKEN"
        return None, str(e)
    except Exception as e:
        return None, str(e)

def load_or_generate_data():
    if use_hf_dataset and HAS_H5PY:
        with st.spinner("Connecting to Turing Synthetic Radar Dataset..."):
            token = get_hf_token()
            gt, status = load_turing_dataset(NUM_STEPS, NUM_BANDS, token)
            if gt is not None:
                st.success("Successfully loaded real radar data from Hugging Face!")
                return gt
            elif status == "ACCESS_DENIED" or status == "INVALID_TOKEN":
                st.error("Authentication Failed: The API Token you entered is invalid or does not have access to this gated dataset. Please check your token.")
                st.warning("Using synthetic fallback data instead.")
                return generate_ground_truth(NUM_STEPS, NUM_BANDS, num_static, num_periodic, num_agile)
            else:
                st.warning(f"Failed to load dataset: {status}. Using synthetic fallback.")
                return generate_ground_truth(NUM_STEPS, NUM_BANDS, num_static, num_periodic, num_agile)
    else:
        return generate_ground_truth(NUM_STEPS, NUM_BANDS, num_static, num_periodic, num_agile)

ground_truth = load_or_generate_data()

# --- Receiver Model ---
def receiver_scan(band, true_state, pd, pfa):
    if true_state[band] == 1:
        return 1 if random.random() < pd else 0
    else:
        return 1 if random.random() < pfa else 0

# --- Schedulers ---
class SequentialScheduler:
    def __init__(self, num_bands):
        self.num_bands = num_bands
        self.idx = 0
    def get_action(self):
        a = self.idx
        self.idx = (self.idx + 1) % self.num_bands
        return a
    def update(self, action, observation):
        pass

class RandomScheduler:
    def __init__(self, num_bands):
        self.num_bands = num_bands
    def get_action(self):
        return random.randint(0, self.num_bands - 1)
    def update(self, action, observation):
        pass

class POMDPScheduler:
    def __init__(self, num_bands):
        self.num_bands = num_bands
        self.beliefs = np.ones(num_bands) / num_bands
        self.time_since_last_scan = np.zeros(num_bands)
        self.current_time = 0
        self.hit_history = [[] for _ in range(num_bands)]
        self.period_estimates = np.zeros(num_bands)
        
    def get_action(self):
        alpha, beta, gamma, delta_weight = 1.0, 0.5, 0.1, 1.5
        uncertainty = self.beliefs * (1 - self.beliefs)
        normalized_freshness = np.clip(self.time_since_last_scan / (self.num_bands * 2), 0, 1.0)
        
        # Periodicity Prediction Score (Level 4 ARD)
        periodicity_score = np.zeros(self.num_bands)
        for b in range(self.num_bands):
            if self.period_estimates[b] > 0 and len(self.hit_history[b]) > 0:
                time_since_last_hit = self.current_time - self.hit_history[b][-1]
                # If we are right at the expected period window, spike the score to intercept it!
                if time_since_last_hit > 0 and abs(time_since_last_hit - self.period_estimates[b]) <= 1:
                    periodicity_score[b] = 1.0
                    
        scores = (alpha * self.beliefs) + (beta * uncertainty) + (gamma * normalized_freshness) + (delta_weight * periodicity_score)
        return np.argmax(scores)
        
    def update(self, action, observation):
        self.current_time += 1
        self.time_since_last_scan += 1
        self.time_since_last_scan[action] = 0
        
        persistence, activation = 0.9, 0.05
        predicted_beliefs = self.beliefs * persistence + (1 - self.beliefs) * activation
        
        if observation == 1:
            predicted_beliefs[action] = min(0.99, predicted_beliefs[action] + 0.3)
            # Record hit for periodicity tracking
            self.hit_history[action].append(self.current_time)
            if len(self.hit_history[action]) > 3:
                self.hit_history[action].pop(0)
            # Estimate period if we have at least 2 hits
            if len(self.hit_history[action]) >= 2:
                delta = self.hit_history[action][-1] - self.hit_history[action][-2]
                self.period_estimates[action] = delta
        else:
            predicted_beliefs[action] = max(0.01, predicted_beliefs[action] - 0.3)
            
        self.beliefs = predicted_beliefs

# --- Run Simulation ---
tab1, tab2, tab3 = st.tabs(["Simulation Dashboard", "Advanced Analytics", "How the AI Works"])

with tab1:
    st.header("Simulation Results")
    
    if st.button("Run Smart Scan Simulation", type="primary", use_container_width=True):
        schedulers = {
            "Sequential (Baseline)": SequentialScheduler(NUM_BANDS),
            "Random (Baseline)": RandomScheduler(NUM_BANDS),
            "POMDP (Smart AI)": POMDPScheduler(NUM_BANDS)
        }
        
        results = {}
        
        # --- Live Progress Bar ---
        progress_bar = st.progress(0, text="Initializing simulation...")
        total_operations = len(schedulers) * NUM_STEPS
        current_op = 0
        
        for name, agent in schedulers.items():
            # --- Time-Forwarding (Warm-up Phase) ---
            # If the user wants to simulate how the AI acts after an hour of implementation,
            # we run it silently here so it can build its mathematical belief state.
            if WARMUP_STEPS > 0 and name == "POMDP (Smart AI)":
                for w in range(WARMUP_STEPS):
                    data_idx = w % len(ground_truth)
                    true_state = ground_truth[data_idx]
                    action = agent.get_action()
                    obs = receiver_scan(action, true_state, PD, PFA)
                    agent.update(action, obs)

            detections, false_alarms, missed_opportunities = 0, 0, 0
            scans_history = []
            
            for t in range(NUM_STEPS):
                # Update progress bar every ~5% of the total loop to avoid slowing down execution
                if current_op % max(1, total_operations // 20) == 0:
                    progress_bar.progress(current_op / total_operations, text=f"Simulating {name}... (Step {t}/{NUM_STEPS})")
                current_op += 1
                
                true_state = ground_truth[t]
                action = agent.get_action()
                obs = receiver_scan(action, true_state, PD, PFA)
                agent.update(action, obs)
                scans_history.append(action)
                
                if true_state[action] == 1 and obs == 1: detections += 1
                elif true_state[action] == 0 and obs == 1: false_alarms += 1
                
                if len(np.where(true_state == 1)[0]) > 0 and true_state[action] == 0:
                    missed_opportunities += 1
                    
            interception_rate = detections / max(1, np.sum(ground_truth))
            reward = (detections * 10) - (false_alarms * 2) - (missed_opportunities * 5)
            
            results[name] = {
                "Interception Rate": interception_rate,
                "True Detections": detections,
                "False Alarms": false_alarms,
                "Reward": reward,
                "History": scans_history
            }
        
        progress_bar.empty() # Remove progress bar when done
        
        # --- Caching to Run History ---
        run_record = {
            "Run ID": len(st.session_state.run_history) + 1,
            "Total Steps": NUM_STEPS,
            "Bands": NUM_BANDS,
            "Smart AI Rate": f"{results['POMDP (Smart AI)']['Interception Rate']:.1%}",
            "Seq Rate (Baseline)": f"{results['Sequential (Baseline)']['Interception Rate']:.1%}",
            "Smart AI Reward": results['POMDP (Smart AI)']['Reward'],
            "Seq Reward (Baseline)": results['Sequential (Baseline)']['Reward'],
        }
        st.session_state.run_history.insert(0, run_record) # Insert at top
        if len(st.session_state.run_history) > 3:
            st.session_state.run_history.pop() # Keep only last 3 runs
            
        smart_res = results["POMDP (Smart AI)"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Interception Rate", f"{smart_res['Interception Rate']:.1%}", 
                    f"{smart_res['Interception Rate'] - results['Sequential (Baseline)']['Interception Rate']:.1%} vs Seq")
        col2.metric("True Detections", smart_res['True Detections'])
        col3.metric("False Alarms", smart_res['False Alarms'])
        col4.metric("Total Reward", smart_res['Reward'], smart_res['Reward'] - results['Sequential (Baseline)']['Reward'])
        
        st.subheader("Interactive Environment Scan Log")
        t_true, b_true = np.where(ground_truth == 1)
        
        # Create a highly efficient scatter plot for thousands of points
        fig = go.Figure()
        
        # Plotting optimization for massive steps: Use Scattergl for WebGL rendering if steps > 5000
        scatter_mode = go.Scattergl if NUM_STEPS > 3000 else go.Scatter
        
        fig.add_trace(scatter_mode(
            x=t_true, y=b_true,
            mode='markers',
            marker=dict(symbol='square', size=8, color='rgba(150, 150, 150, 0.5)'),
            name='Actual Emitter Activity (Hidden Truth)'
        ))
        fig.add_trace(scatter_mode(
            x=list(range(NUM_STEPS)), y=smart_res['History'],
            mode='markers',
            marker=dict(symbol='circle', size=6, color='red'),
            name='Smart AI Scan Actions'
        ))
        
        fig.update_layout(
            xaxis_title="Time Step (Chronological Pulse Index)",
            yaxis_title="Frequency Band (Scaled from RF)",
            hovermode="closest",
            legend=dict(yanchor="top", y=1.1, xanchor="left", x=0.01, orientation="h"),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Comparative Analytics & Cache History")
    
    # Display the Run History Cache
    if st.session_state.run_history:
        st.subheader("Last 3 Runs Cache")
        st.dataframe(pd.DataFrame(st.session_state.run_history).set_index("Run ID"), use_container_width=True)
    else:
        st.info("Run a simulation to populate the cache history!")
        
    st.markdown("---")
    
    st.subheader("Strategy Comparison (Latest Run)")
    if 'results' in locals():
        df_plot = pd.DataFrame({
            "Strategy": list(results.keys()),
            "Interception Rate": [res["Interception Rate"] for res in results.values()],
            "Total Reward": [res["Reward"] for res in results.values()]
        })
        
        c1, c2 = st.columns(2)
        with c1:
            fig_bar1 = px.bar(df_plot, x='Strategy', y='Interception Rate', color='Strategy', title="Interception Rate by Strategy")
            st.plotly_chart(fig_bar1, use_container_width=True)
        with c2:
            fig_bar2 = px.bar(df_plot, x='Strategy', y='Total Reward', color='Strategy', title="Total Reward by Strategy")
            st.plotly_chart(fig_bar2, use_container_width=True)
    else:
        st.warning("Run the simulation in the Dashboard tab to see advanced analytics.")

with tab3:
    st.header("How the SmartScan AI is 'Trained'")
    st.markdown("""
    ### Online Learning via Bayesian Belief Updates
    In this application, the AI does not require pre-training on a massive supercomputer using offline Neural Networks. Instead, it uses **Online Learning** through a **Belief-State POMDP** (Partially Observable Markov Decision Process).
    
    This is highly advantageous for Electronic Warfare because the environment changes rapidly.
    
    1. **The Belief State:** The AI maintains a probability (0.0 to 1.0) for every single frequency band, representing its belief that the band contains a hostile emitter.
    2. **Learning from Hits and Misses:**
       - **Hit (Detection):** If the AI scans a band and detects a signal, it drastically increases its "belief" that this band is active.
       - **Miss (No Signal):** If the AI scans a band and finds nothing, it decreases its belief, signaling to the policy that it should look elsewhere.
    3. **The Policy (Decision Making):** To choose where to look next, it calculates a **Score** for every band:
       $$ Score = (\\alpha \\times Belief) + (\\beta \\times Uncertainty) + (\\gamma \\times Freshness) $$
       It balances **Exploitation** (scanning bands we know are active) with **Exploration** (scanning bands we haven't looked at in a while).
    """)
