# EEG Analysis Interpretation Guide

A neuroscience explainer for understanding your Muse 2 EEG data visualizations.

---

## 📊 Plot 1: Raw EEG Time Series (`plot_raw_eeg`)

### What You're Looking At
This plot shows the raw electrical activity (in microvolts, µV) recorded from each of the 4 EEG electrodes over a short time window (typically 5-10 seconds). Each channel is offset vertically so you can see all traces without overlap.

### Channel Locations
- **TP9** (left temporal-parietal): Behind left ear
- **AF7** (left frontal): Left forehead
- **AF8** (right frontal): Right forehead
- **TP10** (right temporal-parietal): Behind right ear

### What to Look For

#### 1. **Signal Quality Indicators**

**Good signals:**
- Continuous oscillations without flat-lining
- Amplitude typically 20-100 µV
- Rhythmic patterns visible
- No excessive spikes (>200 µV)

**Bad signals (artifacts):**
- **Flat lines** = electrode not making contact
- **Huge spikes** (>200 µV) = movement, muscle tension, or loose connection
- **Very high frequency noise** = muscle activity (EMG contamination)
- **Slow drifts** = skin potential changes, sweating

#### 2. **Brain Rhythms You Might See**

Even in raw data, you can sometimes spot:
- **Alpha waves** (~10 Hz, ~0.1 second period): Relaxation, eyes closed
- **Beta waves** (~20 Hz, faster): Active thinking, focus
- **Theta waves** (~6 Hz, slower): Drowsiness, meditation

### Neuroscience Context
The raw EEG reflects **summed postsynaptic potentials** from millions of cortical pyramidal neurons firing in synchrony. What you see is NOT individual neurons, but rather the collective "hum" of neural populations.

---

## 📈 Plot 2: Power Spectral Density (`plot_psd`)

### What You're Looking At
This shows **how much power (energy)** is present at each frequency in your brain signals. Instead of looking at time, we've converted the signal to the **frequency domain** using the Welch method (averaging multiple FFTs).

### The Y-Axis (Power)
- Plotted on a **logarithmic scale** (each step = 10×)
- Units: µV²/Hz (power spectral density)
- Higher values = more neural activity at that frequency

### Key Frequency Bands (marked with vertical lines)

#### **Delta (0.5-4 Hz)**
- **What it means**: Deep sleep, unconscious processes
- **When you'll see it**: Probably not during music listening unless very drowsy
- **Cognitive state**: Non-REM sleep, very deep relaxation

#### **Theta (4-8 Hz)**
- **What it means**: Drowsiness, meditation, creative states, memory encoding
- **When you'll see it**: Deep relaxation, flow states, creative moments
- **Cognitive state**: Hypnagogic (between wake and sleep), meditative absorption
- **Music context**: Emotional engagement, "losing yourself" in music

#### **Alpha (8-12 Hz)** ⭐ Most Important for Music
- **What it means**: Wakeful relaxation, eyes closed, default mode network
- **When you'll see it**:
  - **Eyes closed**: Strong alpha (especially over occipital cortex)
  - **Relaxed listening**: Moderate alpha
  - **Peak moments**: Alpha may decrease (desynchronization)
- **Cognitive state**: Calm alertness, internalized attention
- **Music context**:
  - High alpha = passive, relaxed listening
  - Alpha suppression = active engagement, emotional arousal

#### **Beta (12-30 Hz)**
- **What it means**: Active thinking, focused attention, arousal
- **When you'll see it**:
  - Focused listening to lyrics
  - Analyzing the music
  - Active movement (dancing, tapping)
- **Cognitive state**: Active cognition, executive function
- **Music context**:
  - Low beta (12-15 Hz): Relaxed focus
  - High beta (20-30 Hz): Intense concentration, possible anxiety

#### **Gamma (>30 Hz)**
- **What it means**: Binding of sensory features, consciousness, "aha!" moments
- **When you'll see it**: Moments of insight, peak emotional experiences
- **Cognitive state**: Integrated perception, conscious awareness
- **Music context**: Musical "chills," peak aesthetic experiences
- **Caveat**: Hard to measure reliably with Muse 2; often contaminated by muscle activity

### What to Look For

1. **Alpha Peak**: Most people have a clear peak around 9-11 Hz
   - **Individual alpha frequency (IAF)**: Your brain's "natural frequency"
   - Correlates with processing speed and memory

2. **1/f Noise**: Power decreases as frequency increases
   - This is normal! Brain signals follow "pink noise" distribution
   - Reflects scale-free dynamics of cortical networks

3. **Line Noise Spike at 60 Hz** (or 50 Hz in Europe)
   - Electrical interference from power lines
   - Should be filtered out in cleaned data

4. **Band Ratios**:
   - **Theta/Beta ratio**: High = drowsiness or ADHD-like state
   - **Alpha/Beta ratio**: High = relaxation, Low = arousal/stress

### Comparing Channels

- **Frontal (AF7/AF8)**: More susceptible to eye blinks, facial muscle noise
- **Temporal (TP9/TP10)**: Cleaner alpha, less artifact-prone
- **Asymmetry**:
  - Left > Right frontal = approach motivation, positive affect
  - Right > Left frontal = withdrawal, negative affect

---

## 🎨 Plot 3: Spectrogram (`plot_spectrogram`)

### What You're Looking At
A **time-frequency heatmap** showing how the power at each frequency band changes over time throughout the song. This is like a "movie" of your PSD.

### How to Read It

- **X-axis**: Time since track started (seconds)
- **Y-axis**: Frequency (Hz)
- **Color**: Power in dB (brighter/warmer = more power)

### What to Look For

#### 1. **Musical Event-Related Changes**

**Beat drops, chorus entries:**
- Sudden increase in beta power (arousal, attention)
- Possible decrease in alpha (cortical activation)

**Quiet intros, ambient sections:**
- Increased alpha (relaxation)
- Steady theta (absorption)

**Rhythmic sections:**
- Look for **phase-locking**: power oscillations at the tempo frequency
- Example: 120 BPM song = 2 Hz modulation in the spectrogram

#### 2. **Cognitive State Transitions**

**Engagement fluctuations:**
- **Alpha bursts** = mind-wandering, internal focus
- **Alpha suppression** = external attention, engagement

**Emotional peaks:**
- **Sudden broadband power increase** = arousal, chills
- **Gamma bursts** (if visible) = peak aesthetic moments

#### 3. **Temporal Patterns**

**Beginning of song:**
- Often see **orienting response**: brief beta increase, alpha decrease
- Reflects attention capture

**Middle of song:**
- May see **habituation**: gradual alpha increase
- Or **sustained engagement**: stable beta

**End of song:**
- **Anticipatory activity**: beta increase as you expect the ending

### Advanced Patterns

**Interfrequency coupling:**
- Theta phase modulating gamma amplitude = memory encoding
- Hard to see in raw spectrogram but hints: simultaneous theta & gamma power

**Hemispheric asymmetry over time:**
- Compare AF7 (left) vs AF8 (right)
- Emotional valence shifts during different song sections

---

## 📉 Plot 4: Band Power Time Course (`plot_bandpower_timecourse`)

### What You're Looking At
The **total power within a specific frequency band** (e.g., alpha 8-12 Hz) plotted over time. This reduces the spectrogram to a single line per channel, making trends easier to see.

### What to Look For

#### For Alpha Band (8-12 Hz) - Default Visualization

**High alpha power:**
- Relaxed, internally-focused state
- Eyes closed moments (if you closed eyes)
- Passive, non-analytical listening

**Low alpha power (suppression):**
- Active attention, arousal
- Emotional engagement
- Visual or motor activity

**Alpha fluctuations:**
- **~0.1 Hz oscillations** (10-second cycles) = normal cortical dynamics
- **Sudden drops** = attentional capture by salient musical events
- **Gradual increase** = relaxation, habituation

#### For Theta Band (4-8 Hz)

**Increased theta:**
- Deep relaxation, trance-like states
- Emotional processing
- Memory encoding of musical content

**Frontal midline theta (Fz, between AF7/AF8):**
- Correlates with sustained attention and cognitive control
- May increase during challenging listening (complex music)

#### For Beta Band (12-30 Hz)

**Increased beta:**
- Active cognition, planning
- Motor preparation (tapping, dancing)
- Anxiety or stress (if very high)

**Beta burst patterns:**
- Correlate with decision points in music
- Rhythmic entrainment to beat

### Comparing Channels

Plot all 4 channels (TP9, AF7, AF8, TP10) together:

**Coherent changes across channels:**
- Global state change (e.g., all alpha drops = arousal)

**Channel-specific changes:**
- Local processing (e.g., left frontal beta = language/speech)

**Hemispheric asymmetry:**
- Left (TP9, AF7) vs Right (TP10, AF8)
- Left frontal > right = positive emotion, approach
- Right frontal > left = negative emotion, withdrawal

### Temporal Dynamics

**Cross-correlate with song structure:**
- Export your Spotify timestamp markers
- Align alpha dips with beat drops, chorus entries
- Quantify brain-music coupling

---

## 🌀 Plot 5: Strange Attractor / Takens Embedding (`plot_psd_and_attractors_all_channels`)

### What You're Looking At
A **3D trajectory** created by plotting the EEG signal against time-delayed copies of itself:
- X-axis: Signal at time `t`
- Y-axis: Signal at time `t + τ` (e.g., 10 ms later)
- Z-axis: Signal at time `t + 2τ` (e.g., 20 ms later)

This is called a **Takens embedding** and reveals the **hidden geometry** of the brain's dynamics.

### Why This Matters: Chaos Theory & Brain Dynamics

Your brain is a **complex, nonlinear dynamical system**. Traditional linear methods (like PSD) miss the intricate temporal structure. Strange attractors reveal:

1. **Deterministic chaos**: Brain dynamics that are complex but not random
2. **Dimensionality**: How many independent degrees of freedom drive neural activity
3. **Recurrence patterns**: Self-similar structures in brain states

### What to Look For

#### 1. **Attractor Shape**

**Circular/elliptical torus:**
- **Periodic oscillations** (e.g., strong alpha rhythm)
- Healthy, rhythmic brain state
- Clean, organized dynamics
- Example: Eyes-closed resting state

**Complex, filled-in cloud:**
- **Broadband, complex activity**
- Active cognitive processing
- Less dominated by single frequency
- Example: Active listening, problem-solving

**Sparse, noisy scatter:**
- **Poor signal quality** or high noise
- Movement artifacts, muscle contamination
- May need better preprocessing

**Low-dimensional manifold (sheet-like):**
- Activity constrained to a few dimensions
- Strongly coupled oscillators
- Example: Deep meditation, flow states

#### 2. **Temporal Structure**

Watch the **animated version** to see:

**Smooth, flowing trajectory:**
- Predictable, stable brain state
- Good signal quality
- Coherent neural synchronization

**Jumpy, erratic trajectory:**
- State transitions, attentional shifts
- Artifacts (eye blinks, swallows)
- Noisy data

**Recurring loops:**
- Brain returns to similar states
- Metastable dynamics (oscillations between states)

#### 3. **Channel Differences**

**Frontal channels (AF7, AF8):**
- Often more complex attractors
- More contaminated by artifacts (eyes, facial muscles)
- Reflect executive function, attention

**Temporal channels (TP9, TP10):**
- Cleaner, more organized attractors
- Strong alpha oscillations → circular shapes
- Reflect sensory processing, memory

#### 4. **Filter Effects**

**Broadband (1-40 Hz):**
- Complex attractor, many interacting rhythms
- Reflects "full" brain dynamics

**Alpha-only (8-12 Hz):**
- Beautiful, clean ring or torus
- Shows pure oscillatory dynamics
- **Expected**: Very regular, predictable

**Theta-only (4-8 Hz):**
- Slower, larger loops
- Meditative, emotional states

### Neuroscience Interpretation

#### **Lyapunov Exponents** (not calculated here, but implied):
- Positive = chaos (trajectories diverge)
- Zero = periodic oscillation
- Negative = stable fixed point

Brain attractors typically have **small positive Lyapunov exponents**:
- Sensitive to initial conditions (chaos)
- But bounded (attractor)
- = **Flexible yet stable** dynamics

#### **Correlation Dimension**:
- Estimates the "true" dimensionality of the attractor
- Healthy brain: ~5-9 dimensions
- Too low (<3) = overly synchronized, epileptic-like
- Too high (>12) = noisy, fragmented

#### **Recurrence Quantification Analysis** (RQA):
- Not shown, but can be computed
- Measures how often brain returns to similar states
- **Determinism**: % of recurrent points on diagonals
- **Laminarity**: How long brain stays in metastable states

### Musical Context

**During peak emotional moments:**
- Attractor may show **sudden expansion** (increased dimensionality)
- Reflects cortical desynchronization
- Increased flexibility, novel state exploration

**During repetitive, rhythmic sections:**
- Attractor becomes more **periodic, ring-like**
- Brain entrained to musical meter
- Predictable, groove-locked state

**During quiet, ambient sections:**
- Attractor may **contract** to simpler geometry
- Dominated by intrinsic alpha rhythm
- Default mode network activity

---

## 🎵 Putting It All Together: A Music Neuroscience Workflow

### Step 1: Quality Check (Raw EEG)
- Look for artifacts, bad channels
- Ensure data is clean before analysis

### Step 2: Overall Spectral Profile (PSD)
- Identify dominant rhythms
- Check for individual alpha frequency
- Assess arousal (beta) vs relaxation (alpha)

### Step 3: Temporal Dynamics (Spectrogram)
- Find moments of engagement, mind-wandering
- Correlate with musical structure
- Look for event-related changes

### Step 4: Isolate Key Bands (Band Power Time Course)
- Track alpha (relaxation), beta (attention), theta (emotion)
- Compare channels for asymmetry
- Quantify state transitions

### Step 5: Nonlinear Dynamics (Strange Attractors)
- Reveal hidden temporal structure
- Assess complexity and dimensionality
- Visualize brain state geometry

---

## 🧠 Advanced Interpretations

### Hemispheric Asymmetry & Emotion

**Left frontal activation (AF7 > AF8):**
- Approach motivation
- Positive emotional valence
- Engagement, interest

**Right frontal activation (AF8 > AF7):**
- Withdrawal motivation
- Negative emotional valence (or intense, mixed emotions)
- Avoidance, contemplation

**Measure**: Alpha power asymmetry
- Right alpha > Left alpha = Left cortex more active (approach)
- Left alpha > Right alpha = Right cortex more active (withdrawal)

### Flow States & Musical Absorption

**Characteristics:**
- Moderate alpha (not too high, not too low)
- Increased frontal midline theta
- Reduced self-referential activity (DMN)
- Beta locked to musical tempo

### Musical Chills (Frisson)

**EEG signatures:**
- Sudden gamma burst (if detectable)
- Broadband power increase
- Possible theta increase (emotional arousal)
- Autonomic response (heart rate, skin conductance)

### Prediction & Surprise

**Predictable musical events:**
- Pre-stimulus beta increase (motor preparation)
- Alpha desynchronization (attention)

**Surprising events:**
- Post-stimulus theta (prediction error)
- Broadband gamma (novelty detection)

---

## 📚 Further Reading

### Essential Papers

1. **Alpha oscillations**: Klimesch, W. (2012). "Alpha-band oscillations, attention, and controlled access to stored information." *Trends in Cognitive Sciences*.

2. **Music & EEG**: Fujioka, T., et al. (2012). "Beta and gamma rhythms in human auditory cortex during musical beat processing." *Annals of the New York Academy of Sciences*.

3. **Chaos in EEG**: Stam, C. J. (2005). "Nonlinear dynamical analysis of EEG and MEG: Review of an emerging field." *Clinical Neurophysiology*.

4. **Musical emotion**: Koelsch, S. (2014). "Brain correlates of music-evoked emotions." *Nature Reviews Neuroscience*.

### Books

- **"Rhythms of the Brain"** by György Buzsáki
- **"Music, Language, and the Brain"** by Aniruddh Patel
- **"The Neuroscience of Bach's Music"** series (open access)

---

## ⚠️ Important Caveats

### What Muse 2 Can and Cannot Do

**Can do:**
- Measure alpha, theta, beta rhythms reliably
- Track relative changes in power over time
- Detect major state changes (relaxation vs arousal)
- Provide insight into musical engagement

**Cannot do:**
- Precise source localization (only 4 channels)
- Reliable gamma measurement (limited sampling, artifact-prone)
- Replace medical/clinical EEG
- Decode specific thoughts or emotions

### Artifact Awareness

**Always consider:**
- Eye blinks, saccades (frontal channels)
- Jaw clenching, chewing (temporal channels)
- Head movement (all channels)
- Electrode contact quality

**Best practices:**
- Minimize movement during recording
- Relax facial muscles
- Keep eyes gently closed or fixed on a point
- Ensure good electrode contact (wet hair problematic)

---

## 🎯 Quick Reference: What Each Plot Tells You

| Plot | Primary Question | Key Insight |
|------|-----------------|-------------|
| **Raw EEG** | Is my data clean? | Signal quality, artifacts |
| **PSD** | What rhythms dominate? | Overall brain state, frequency content |
| **Spectrogram** | How do rhythms change over time? | Dynamics, event-related changes |
| **Band Power** | When am I relaxed/focused? | State transitions, engagement |
| **Attractor** | What is the hidden structure? | Complexity, chaos, dimensionality |

---

## 🚀 Next Steps

1. **Correlate with subjective experience**: Did high alpha moments correspond to relaxation?
2. **Compare songs/genres**: Do different musical styles produce different patterns?
3. **Test interventions**: Does eyes-closed listening increase alpha?
4. **Explore lateralization**: Are emotional songs more right-lateralized?
5. **Build predictive models**: Can you predict your emotional rating from EEG?

---

*Happy brain-hacking! Remember: the brain is the most complex object in the known universe. These tools give you a glimpse, but there's always more to discover.* 🧠✨
