# 🌐 Enterprise BGP Simulator v2.0

> **Sub-Second BFD Failover, Infrastructure Automation Code Viewer, SevOne SNMP Telemetry, Route Reflector Topologies & MP-BGP VRFs**

Enterprise BGP Simulator v2.0 is an interactive, full-stack BGP Control Plane Simulator and Decision Engine built with Python (Flask) and JavaScript. It provides real-time visualization of BGP finite state machine (FSM) transitions, 10-step path selection tie-breakers, sub-second BFD reconvergence, Ansible/RESTCONF automation payload generation, and SevOne SNMP trap ingestion.

---

## ✨ Enterprise Features

### ⚡ 1. BFD (Bidirectional Forwarding Detection) Integration
* **Sub-Second Failover (50ms)**: Bypasses slow BGP timers (60s keepalive, 180s hold timer).
* **Instant Re-convergence**: Toggling a link breaks the BFD echo session in <50ms, tearing down the BGP adjacency and forcing immediate route re-convergence.
* **Console Status**: `show ip bgp summary` tracks real-time BFD session health (`Up (50ms)` vs `Down`).

### 🛠 2. Infrastructure Automation Payload Viewer
* **GUI-to-Code Translation**: Click **"🛠 View Ansible & RESTCONF Code"** to see equivalent configuration code generated dynamically as policy values (Local Preference, AS-Path Prepend, Next-Hop-Self) change in the GUI.
* **Ansible Playbook (YAML)**: Generates production-ready `cisco.ios.ios_bgp_global` and `cisco.ios.ios_config` plays.
* **RESTCONF API Payload (JSON)**: Generates RFC 8040 / Native YANG JSON payloads (`Cisco-IOS-XE-bgp:bgp`).

### 📡 3. SevOne SNMP Traps & Telemetry Simulation
* **RFC 1657 `bgpBackwardTransition` Traps**: Simulates trap emission (`.1.3.6.1.2.1.15.0.2`) on state drops or fault injections (AS Mismatch, MD5 Auth Failure).
* **Telemetry Stream**: Live pane displays `CRITICAL` alerts simulating what monitoring platforms like **IBM SevOne** ingest during network events.

### 🔁 4. Route Reflector (RR) Topologies & Loop Avoidance
* **RR Cluster Architecture**: **R1** operates as Route Reflector (Cluster ID `1.1.1.1`) with **R4** and **R5** as iBGP Route Reflector Clients.
* **`Originator_ID` & `Cluster_List` Attributes**: Displays loop-prevention metadata in `show ip bgp` when the standard iBGP split-horizon rule is bypassed.

### 🏢 5. Multiprotocol BGP (MP-BGP) & VRFs
* **Address Family Selector**: Toggle between **IPv4 Unicast** and **VPNv4 MP-BGP (VRFs)**.
* **Route Isolation**: Supports Route Distinguishers (RD) and Route Targets (RT):
  * **`VRF_RED`**: RD `100:10`, RT `target:100:100`, Network `192.168.10.0/24`
  * **`VRF_BLUE`**: RD `100:20`, RT `target:100:200`, Network `192.168.20.0/24`

### 🔍 6. 10-Step Best-Path Decision Evaluator
* Interactive modal displaying side-by-side comparison of competing paths across Weight, Local Preference, AS-Path Length, Origin Type ($i < e < ?$), MED, eBGP vs iBGP, IGP metric, and Router ID.

---

## 🚀 Quick Start

### Prerequisites
* Python 3.9+

### Installation & Execution

```bash
# Clone repository
git clone https://github.com/smorad993/Enterprise-BGP-Simulator-v2.0.git
cd Enterprise-BGP-Simulator-v2.0

# Create virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Launch web simulator
python app.py
```

Open your browser and navigate to `http://localhost:5050`.

---

## 🛠 Project Structure

```
├── app.py                      # Flask REST API server (Port 5050)
├── bgp_engine.py               # Core BGP FSM, Decision Engine, BFD & VRF logic
├── snmp_engine.py              # SevOne SNMP discovery & trap engine
├── vendor_drivers.py           # Cisco/Juniper vendor drivers
├── requirements.txt            # Python dependencies
├── static/                     # CSS & Frontend JS Controller
│   ├── style.css
│   └── app.js
├── templates/                  # Single page application HTML template
│   └── index.html
└── bgp_simulator_docs/         # Documentation & Implementation Architecture
    ├── walkthrough.md
    ├── implementation_plan.md
    └── bgp_topology_diagram.md
```

---

## 📜 License

MIT License
