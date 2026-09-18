# 🛠 Python SNMP Discovery API Simulator (`snmp-simulator`)
## Implementation Plan & Architecture Specification

**Goal**: Build a Python-based simulator for `discovery-snmp-api` that replicates the SevOne integration API, multi-vendor SNMP OID polling (Cisco, Arista, Ciena, DriveNets, Nokia, SONiC), and Consul/Prometheus telemetry endpoints.

---

## 🏗 System Architecture & Components

```text
[ SevOne / REST Client ]
           │
           ▼ (HTTP POST /devices)
┌─────────────────────────────────────────────────────────────┐
│                 Python Simulator Engine                      │
│                                                             │
│  ┌────────────────────┐      ┌───────────────────────────┐  │
│  │  REST API Router   │      │   SNMP Engine Simulator   │  │
│  │  (Flask / FastApi) │ ───► │   (Mock MIB OID Walk &    │  │
│  │                    │      │    v2c/v3 Protocols)      │  │
│  └────────────────────┘      └─────────────┬─────────────┘  │
│                                            │                │
│                              ┌─────────────▼─────────────┐  │
│                              │  Vendor Driver Registry   │  │
│                              │ (Cisco, Arista, Ciena,    │  │
│                              │  DriveNets, Nokia, SONiC) │  │
│                              └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown:

1. **`app.py` (REST Transport Layer)**:
   - Hosts `POST /devices` and `POST /api/v1/discover` matching the exact JSON request/response contracts of `discovery-snmp-api`.
   - Domain Scope Gate validation (`.comcast.net`, `.ccp`, `.xcloud`).
   - Serves `/health` and `/metrics` (Prometheus telemetry).

2. **`snmp_engine.py` (Mock SNMP Engine)**:
   - Simulates UDP OID walks (`.1.3.6.1.2.1.1.2.0` sysObjectID, `IF-MIB`, `ENTITY-MIB`).
   - Configurable latency and packet loss simulation.

3. **`vendor_drivers.py` (Vendor Parser Strategy)**:
   - Implements Strategy Pattern for hardware vendors:
     * `.1.3.6.1.4.1.9.` $\rightarrow$ Cisco ASR / Catalyst
     * `.1.3.6.1.4.1.30065.` $\rightarrow$ Arista 7050 / Spine
     * `.1.3.6.1.4.1.1271.` $\rightarrow$ Ciena Waveserver
     * `.1.3.6.1.4.1.6527.` $\rightarrow$ Nokia SR-OS
     * `.1.3.6.1.4.1.27047.` $\rightarrow$ SONiC OS Switch

4. **`simulator_ui.py` / `templates/index.html` (Web UI Control Panel)**:
   - Sleek Dark Mode dashboard to trigger discovery requests, view simulated SNMP packet flows, and inspect generated JSON responses.

---

## 📁 Project Directory Structure

All code and related documents will be organized in one clean folder structure:

```text
Ai-lab/
└── snmp_simulator_docs/          # Consolidated Documentation & Diagrams
    ├── implementation_plan.md
    └── architecture_diagram.md
├── app.py                         # Simulator Flask Server
├── snmp_engine.py                 # Mock SNMP Engine & OID Walker
├── vendor_drivers.py              # Vendor Drivers (Cisco, Arista, etc.)
├── requirements.txt               # Dependencies (flask, requests)
├── templates/
│   └── index.html                 # Simulator Web Control Panel
└── static/
    ├── style.css                  # Dark Mode System Styling
    └── app.js                     # Interactive Control Panel Logic
```

---

## 🧪 Verification Plan

1. **API Testing**: Execute `curl` POST requests to `http://127.0.0.1:5050/devices` and verify valid JSON responses matching SevOne contracts.
2. **`gstack` Automation**: Use `.claude/skills/gstack/browse/dist/browse` to navigate to the simulator UI, trigger discovery jobs, and take DOM snapshots.
