# Pelican

**Pelican** is a cybersecurity alert replay framework designed for SOC research, alert prioritization studies, workload reduction experiments, and security analytics testing.

Rather than requiring a live SIEM deployment, Pelican replays previously collected security alerts from exported datasets, allowing researchers and developers to build, test, and evaluate security analytics pipelines in a repeatable and reproducible manner.

Pelican was originally developed as part of research into **SOC Analyst Fatigue Reduction Framework**

---

# Why Pelican?

Building and maintaining a Security Operations Center (SOC) lab can be expensive, time consuming, complex or all of the above.

Most alert prioritization and enrichment research only needs realistic security alerts, not a permanently running SIEM environment. Pelican simplifies testing by providing a replay framework that can be used to replay alerts from a dataset after first generating it. 

Pelican enables a workflow where:

```text
Generate Alerts
        ↓
Export Dataset
        ↓
Replay Dataset
        ↓
Research & Evaluation
```

Once a dataset has been exported, the original SIEM, endpoints, and attack simulation environment are no longer required.

This makes experimentation:

* Reproducible
* Portable
* Easier to share
* Easier to benchmark
* Independent of vendor-specific infrastructure

---

# Core Features

## Replay Modes

### Sequential Replay

Alerts are replayed in chronological order without delays.

```text
Alert 1
Alert 2
Alert 3
...
```

Ideal for:

* Testing
* Development
* Unit testing
* Bulk processing

---

### Time-Preserved Replay

Original timing relationships are preserved.

```text
10:00:00
10:00:05
10:00:17
10:01:02
```

Ideal for:

* Realistic SOC simulations
* Queue behaviour testing
* Timing-sensitive analytics

---

### Accelerated Replay

Replay alerts faster than their original rate.

Examples:

```text
100 alerts/minute
500 alerts/minute
1000 alerts/minute
```

Ideal for:

* Stress testing
* Performance benchmarking
* Scalability testing

---

## Push-Based Processing

Pelican can automatically push alerts to:

* Callback functions
* Thread-safe queues
* Downstream processing pipelines

Features:

* Start
* Pause
* Resume
* Stop

---

## Pull-Based Processing

Pelican also supports synchronous iteration through datasets using Python generators.

Ideal for:

* Data science workflows
* Jupyter notebooks
* Batch processing

---

## Dataset Loading

Pelican can load:

```text
Single JSON File
```

or

```text
Directory of JSON Files
```

Files are automatically sorted chronologically before replay.

---

## Optional Ground Truth Support

Pelican supports attaching:

* Ground truth labels
* Execution logs
* Attack metadata
* Validation datasets

to replayed alerts.

This allows researchers to evaluate:

* Classification accuracy
* False positive reduction
* Prioritization effectiveness
* Analyst workload reduction

---

# High-Level Architecture

Pelican is intended to be the entry point for larger SOC analytics pipelines.

```text
Alert Dataset
      │
      ▼
Replay Engine
      │
      ▼
Alert Enrichment
      │
      ▼
Risk Scoring
      │
      ▼
Classification
      │
      ▼
Grouping
      │
      ▼
Prioritization
      │
      ▼
Analyst Evaluation
```

Pelican currently implements the Replay Engine component.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/AmshulVarikat/pelican.git
cd pelican
```

---

## Create Virtual Environment

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Quick Start

## Push-Based Processing

### 1. Definition

```python
from ReplayEngine import create_engine, ReplayMode

engine = create_engine(
    filepath="inputs",
    include_ground_truth=False,
    mode=ReplayMode.TIME_PRESERVED
)
```

### 2. Usage

**Using a Callback:**
```python
def process_alert(envelope):
    print(f"[{envelope['replay_time']}] Received alert: {envelope.get('alert', {})}")
    # Add your custom enrichment or routing logic here

engine.register_callback(process_alert)
engine.start()
```

**Using a Queue:**
```python
import queue

alert_queue = queue.Queue()
engine.register_queue(alert_queue)
engine.start()

# In a separate worker thread or process:
while True:
    try:
        alert = alert_queue.get(timeout=1)
        print(f"Processing alert: {alert}")
    except queue.Empty:
        # Handle empty queue or exit condition
        pass
```

### 3. Playback Controls

```python
# Start processing alerts
engine.start()

# Pause alert delivery
engine.pause()

# Resume alert delivery
engine.resume()

# Stop the engine completely
engine.stop()
```

---

## Pull-Based Processing

### 1. Definition

```python
from ReplayEngine import create_engine, ReplayMode

engine = create_engine(
    filepath="inputs",
    include_ground_truth=False,
    mode=ReplayMode.SEQUENTIAL
)
```

### 2. Usage

```python
# The replay() method returns a generator yielding alerts one by one
for envelope in engine.replay():
    print(f"Pulled alert: {envelope['replay_time']}")
    # Apply your own sequential analytics logic here
```

---

# Replay Output Format

Each replayed item is wrapped in an envelope.

## RAW Mode

```json
{
  "alert": {
    "...": "..."
  },
  "replay_time": "2026-06-12T00:00:00Z"
}
```

---

## TEST Mode

```json
{
  "alert": {
    "...": "..."
  },
  "replay_time": "2026-06-12T00:00:00Z",
  "source_dataset": "dataset_01",
  "ground_truth": {
    "label": "malicious"
  }
}
```

---

# Recommended Dataset Structure

```text
datasets/
│
├── alerts/
│   ├── alerts_001.json
│   ├── alerts_002.json
│   └── alerts_003.json
│
├── ground_truth/
│   └── labels.json
│
└── metadata/
    └── dataset_info.json
```

---

# Typical Research Workflow

## Step 1

Generate realistic security alerts.

Possible sources:

* Wazuh
* Splunk
* Elastic
* Microsoft Sentinel
* Security Onion
* Custom SIEM platforms

---

## Step 2

Export alerts.

Example:

```text
alerts.json
```

---

## Step 3

Replay alerts using Pelican.

---

## Step 4

Build enrichment and analytics layers.

Examples:

* Asset enrichment
* Threat intelligence enrichment
* Risk scoring
* Alert classification
* Alert grouping
* Prioritization

---

## Step 5

Measure improvements.

Examples:

* False positive reduction
* Analyst workload reduction
* Prioritization accuracy
* Investigation completeness

---

# Generating Your Own Datasets

Pelican does not require a specific SIEM.

Any platform capable of exporting alerts as JSON can be used.

Common options include:

* Wazuh
* Splunk
* Elastic
* Microsoft Sentinel
* Security Onion

---

# Recommended SOC Research Lab

The recommended lab architecture is:

```text
Windows Endpoint
      │
      ▼
Sysmon
      │
      ▼
Wazuh Agent
      │
      ▼
Wazuh Manager
      │
      ▼
Alert Dataset
      │
      ▼
Pelican
```

This provides realistic security alerts while remaining relatively easy to deploy.

---

# Lab Setup Guide

The following section provides a generic deployment guide.

---

# Option A — Wazuh Lab (Recommended)

## Components

### Linux Server

Install:

* Ubuntu
* Debian
* Rocky Linux
* AlmaLinux
* RHEL

Required Components:

* Wazuh Manager
* Wazuh Dashboard
* Wazuh Indexer

---

### Windows Endpoint

Install:

* Windows 10
* Windows 11
* Windows Server

Recommended Components:

* Sysmon
* Wazuh Agent
* Atomic Red Team

---

### Attack Simulation

Recommended:

* Atomic Red Team
* Caldera
* Prelude Operator
* Manual ATT&CK simulations

---

### Dataset Generation

Generate:

* Discovery activity
* PowerShell activity
* Persistence activity
* Credential access activity
* Administrative activity
* Normal user activity

Export resulting alerts as JSON.

---

# Option B — Elastic Lab

Components:

* Elasticsearch
* Kibana
* Elastic Agent

Workflow:

```text
Telemetry
     ↓
Elastic
     ↓
Detections
     ↓
Alert Export
     ↓
Pelican
```

---

# Option C — Splunk Lab

Components:

* Splunk Enterprise
* Universal Forwarder

Workflow:

```text
Logs
   ↓
Splunk
   ↓
Correlation Searches
   ↓
Alerts
   ↓
Export
   ↓
Pelican
```

---

# Option D — Existing Production Data

If historical alerts already exist:

```text
Export
   ↓
Sanitize
   ↓
Replay
```

No lab deployment is required.

---

# Supported Operating Systems

## Windows

Recommended for:

* Sysmon
* Endpoint telemetry
* Attack simulation

Supported:

* Windows 10
* Windows 11
* Windows Server 2019
* Windows Server 2022

---

## Linux

Recommended for:

* Wazuh
* Elastic
* Splunk
* Development

Supported:

* Ubuntu
* Debian
* Rocky Linux
* AlmaLinux
* Fedora
* RHEL

---

## macOS

Recommended for:

* Development
* Replay execution
* Virtualization host

Supported virtualization platforms:

* Parallels
* VMware Fusion
* UTM
* VirtualBox

---

# Companion Repositories

Repositories include lab setup scripts will be published once available. 

---

# Roadmap

## Current

* Replay Engine
* Sequential Replay
* Time-Preserved Replay
* Accelerated Replay
* Push-Based Processing
* Pull-Based Processing

---

# License
---

# Disclaimer

This project is intended for cybersecurity research, education, testing, and defensive security purposes.

Users are responsible for complying with all applicable laws, regulations, and organizational policies when generating datasets or conducting security testing.
