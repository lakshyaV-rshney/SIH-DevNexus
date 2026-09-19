# POMDP Belief-State Smart Scan Scheduler (SIH 26055)

### Watch the Demo
<video src="Demo.mp4" controls="controls" style="max-width: 100%;">
  <a href="Demo.mp4">View Demo Video</a>
</video>

## Overview
This repository contains the implementation of a Machine Learning-based Electronic Support (ES) receiver scheduler software. Developed for the **Defence Research and Development Organisation (DRDO)** under **SIH Problem Statement 26055**, this system replaces conventional open-loop scanning strategies with an intelligent, adaptive scheduler.

The core of the architecture is a **Partially Observable Markov Decision Process (POMDP)**. Unlike traditional systems that blindly sweep across frequency bands regardless of emitter activity, this system continuously updates a mathematical belief state based on real-time observations (hits and misses) to intelligently decide which frequency band to scan next.

## Architecture
The system consists of the following primary modules:
1. **RF Environment Simulator**: Capable of ingesting actual radar datasets (e.g., Turing Synthetic Radar Dataset) or falling back to a synthetic generator mimicking periodic, frequency-agile, and static emitters.
2. **Receiver Model**: Simulates realistic hardware constraints including Probability of Detection (Pd) and Probability of False Alarm (Pfa).
3. **ML Scheduler (POMDP)**: Implements online Bayesian learning to update target probabilities and a policy function balancing exploitation (known active bands) and exploration (uncertainty and time since last scan).
4. **Performance Evaluation Engine**: Calculates crucial figures of merit including Interception Rate, Total Reward, True Detections, and False Alarms.

## Installation and Execution

### Local Development
To run this application locally on your machine, follow these steps:

1. **Clone the repository:**

2. **Install dependencies:**
   Ensure you have Python 3.8+ installed. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Authenticate with Hugging Face (Optional but Recommended):**
   If you intend to use the gated Turing Synthetic Radar Dataset, authenticate your terminal session:
   ```bash
   hf auth login
   ```
   Provide your Hugging Face Access Token when prompted.

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```
   The application will launch in your default web browser (typically at `http://localhost:8501`).

## Deployment (Streamlit Community Cloud)
This application is designed to be easily deployed to Streamlit Community Cloud for public demonstration without requiring any credit card or paid infrastructure.

1. Ensure your repository is pushed to GitHub.
2. Navigate to [Streamlit Community Cloud](https://share.streamlit.io/) and authenticate with your GitHub account.
3. Select **"New app"** and point it to your repository and `app.py`.
4. **Important Configuration:** Before clicking deploy, access **Advanced Settings** and navigate to the **Secrets** section. If utilizing gated datasets, input your token as follows:
   ```toml
   HF_TOKEN = "your_access_token_here"
   ```
5. Deploy the application.

## Scientific Merit and Extensibility
This codebase demonstrates that a statistically grounded online learner (Belief-State Update) significantly outperforms sequential open-loop sweeps in dynamically changing Electronic Warfare environments. 

For advanced integrations, the `POMDPScheduler` class in `app.py` is fully modular. It can be directly replaced with a Deep Reinforcement Learning (DRL) agent (such as PPO or DQN trained via Stable Baselines3) without requiring modifications to the simulation loop or the user interface.
