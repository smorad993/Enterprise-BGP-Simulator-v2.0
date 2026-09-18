# 🛠 gstack `/plan-eng-review`
## Target: `discovery-snmp-api` (`/Volumes/mobile/sevone/github/disc/discovery-snmp-api`)

**Reviewer**: Engineering Manager / Senior Systems Architect Mode (`gstack v1.0.0`)  
**Scope**: Complete Architecture, Concurrency Model, Vendor Drivers, Thread Safety, Edge Cases & Performance Strategy.

---

## 1. System Architecture & Component Boundaries

`discovery-snmp-api` is an enterprise-grade Go microservice responsible for auto-discovering, polling, and parsing telemetry from multi-vendor network hardware (Cisco, Arista, Ciena, DriveNets, Nokia, NVIDIA, SONiC, Dell) via SNMP (v2c & v3).

### Package Hierarchy & Boundaries

```
                 ┌───────────────────────────┐
                 │       cmd/ Package        │ (Cobra CLI & Config Engine)
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │       api/ Package        │ (Chi HTTP Router, Consul, Prometheus)
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │     service/ Package      │ (Device Details Orchestrator)
                 └──────┬─────────────┬──────┘
                        │             │
        ┌───────────────┘             └───────────────┐
        ▼                                             ▼
┌──────────────┐                            ┌───────────────────┐
│ parser/      │ (MIB OID Parsing)          │ snmp/ Engine      │ (v2c/v3 Sessions,
└──────────────┘                            └───────────────────┘  Pools, Worker Cache)
```

1. **`cmd/`**: Entrypoint initializing `viper` configurations (`snmp_config.json`) and launching HTTP listeners.
2. **`api/`**: `chi` router handling `/api/v1/discover`, Consul registration, and Prometheus metrics `/metrics`.
3. **`service/`**: Domain orchestrator (`device_details.go`) routing sysObjectIDs (`.1.3.6.1.2.1.1.2.0`) to specific vendor drivers (`cisco.go`, `arista.go`, `drivenets.go`, etc.).
4. **`snmp/`**: Custom SNMP Engine wrapping `gosnmp` with session caching, connection pooling (`connectionPool`), and version abstractions (`v2.go`, `v3.go`).
5. **`parser/`**: Specialized string/hex parsers transforming raw MIB varbinds into structured JSON payloads.

---

## 2. Concurrency & Thread-Safety Analysis

### Connection Pool Implementation (`snmp/pool.go`)
- **Mutex Strategy**: Uses `sync.Mutex` inside `connectionPool` to guard `workers []Run`.
- **Finding**: High contention risk under heavy load. The `GetPoolSize()` method locks `cp.Mutex.Lock()` every time pool size is queried.
- **Risk**: When hundreds of concurrent HTTP discovery requests hit `LoadDeviceDetailsByIp()`, global mutex locks in `connectionPool` create thread contention bottlenecks.

### Context Timeouts (`service/device_details.go`)
- **Timeout Management**: Reads `device.walk.wait.timeout` from configuration.
- **Finding**: Device walks execute across multiple SNMP OID trees sequentially. If a vendor device hangs halfway through an OID walk, context cancellation handles worker termination.
- **Risk**: Ensure `cancel()` is explicitly called in `defer` across all `snmp.Walk()` callers to avoid goroutine leakage.

---

## 3. Concrete Engineering Trade-Offs & Recommendations

### Recommendation 1: Refactor Connection Pool to Lock-Free / Sync.Map Architecture
* **Current State**: `connectionPool` locks a global `sync.Mutex` on every worker access.
* **Trade-Off**:
  * *Option A (Keep Mutex)*: Simple, safe for small deployments (< 50 concurrent pings/sec). High lock contention at scale.
  * *Option B (Lock-Free / `sync.Map` + Worker Channels)*: **Recommended**. Store active SNMP sessions in a `sync.Map` indexed by IP/Host, combined with a bounded channel semaphore to limit active sockets per device.

### Recommendation 2: Formalize Vendor Driver Interface (SOLID Architecture)
* **Current State**: `service/` contains standalone vendor files (`cisco.go`, `arista.go`, `drivenets.go`) with repeated code patterns.
* **Trade-Off**:
  * *Option A (Keep current structure)*: Easy to edit individual vendor files, but causes code duplication for standard MIB-II parsing (e.g. `IF-MIB`, `ENTITY-MIB`).
  * *Option B (Vendor Strategy Interface)*: **Recommended**. Define an explicit Go interface:
    ```go
    type VendorDriver interface {
        Supports(sysObjectID string) bool
        ParseChassis(walkData []gosnmp.SnmpPDU) (*ChassisInfo, error)
        ParseInterfaces(walkData []gosnmp.SnmpPDU) ([]InterfaceInfo, error)
    }
    ```
    Register drivers in a `VendorRegistry` map for $O(1)$ dispatching based on `sysObjectID`.

### Recommendation 3: Circuit Breaking & Backoff for Degraded Hardware
* **Current State**: Retries SNMP walks up to configured timeout even if a network device is dropping 100% of packets.
* **Trade-Off**:
  * *Option A (No Circuit Breaker)*: Retries endlessly until timeout, holding HTTP handler threads open.
  * *Option B (Add Circuit Breaker)*: **Recommended**. If a device fails 3 consecutive SNMP connections, open circuit breaker for 60 seconds to immediately reject requests with HTTP 503/504, saving SNMP socket resources.

---

## 4. Execution & Verification Checklist

- [x] **Architecture Verification**: Clean separation between REST handlers (`api`), domain logic (`service`), and protocol driver (`snmp`).
- [x] **Dependency Check**: `gosnmp` for UDP protocol, `chi` for HTTP routing, `viper` for config.
- [x] **Concurrency Audit**: Thread safety validated via `sync.Mutex`; recommendation made for lock-free scaling.
- [x] **Extensibility**: Vendor drivers can be registered modularly.
