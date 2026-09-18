# 🏛 C4 Architecture Model & Visual Diagrams
## Microservice: `discovery-snmp-api`
**Location**: `/Volumes/mobile/sevone/github/disc/discovery-snmp-api`

---

## 🎨 C4 Visual Architecture Diagram

![C4 Architecture Diagram Infographic](/Users/smoradi/.gemini/antigravity-ide/brain/dd04536a-0012-4190-81ca-aab3fe1b1b53/c4_architecture_diagram_1789684793684.jpg)

---

## 1. C4 Level 1: System Context Diagram

```mermaid
graph TD
    user["Network Engineer / SevOne Admin"]
    interrogation["Interrogation Service / Network Automation"]
    sevone["SevOne NMS Engine"]
    
    subgraph SystemBoundary ["System Boundary"]
        snmpApi["discovery-snmp-api Engine"]
    end

    vault["HashiCorp Vault"]
    consul["HashiCorp Consul"]
    prometheus["Prometheus"]
    devices["Physical and Virtual Network Devices"]

    user --> interrogation
    interrogation --> snmpApi
    sevone --> snmpApi

    snmpApi --> vault
    snmpApi --> consul
    snmpApi --> prometheus
    snmpApi --> devices

    devices --> snmpApi
    snmpApi --> interrogation
    snmpApi --> sevone
```

---

## 2. C4 Level 2: Container Diagram

```mermaid
graph TD
    subgraph UpstreamClients ["Upstream Clients"]
        InterrogationSvc["Interrogation Service Container"]
        SevOneNMS["SevOne Monitoring Container"]
    end

    subgraph HostServer ["Linux Server Host (10.142.241.98 Systemd)"]
        subgraph DiscoveryApp ["discovery-snmp-api Process"]
            GoBinary["Go Binary Executable"]
            HttpServer["Chi HTTP Server"]
            SnmpEngine["SNMP Engine and Pool Manager"]
        end
        ConfigStore["snmp_config.json Config"]
    end

    subgraph InfraServices ["Infrastructure Services"]
        VaultSvc["Vault Secret Storage"]
        ConsulCluster["Consul Service Mesh"]
        PrometheusServer["Prometheus Metrics Collector"]
    end

    subgraph HardwareFabric ["Datacenter Fabric"]
        NetworkHardware["Network Hardware UDP 161"]
    end

    InterrogationSvc --> HttpServer
    SevOneNMS --> HttpServer

    GoBinary --> ConfigStore
    GoBinary --> VaultSvc
    GoBinary --> ConsulCluster
    GoBinary --> PrometheusServer

    HttpServer --> SnmpEngine
    SnmpEngine --> NetworkHardware
```

---

## 3. C4 Level 3: Component Diagram

```mermaid
graph TD
    subgraph AppContainer ["discovery-snmp-api Go Application"]
        subgraph CmdPkg ["cmd Package"]
            CLI["cobra CLI and viper Config"]
        end

        subgraph ApiPkg ["api Package"]
            ChiRouter["Chi Router and Middleware"]
            DeviceHandler["fetchDeviceDetailsByFqdn Handler"]
            ConsulRegistrar["ConsulRegistrar Component"]
        end

        subgraph ServicePkg ["service Package"]
            DeviceAttrService["DeviceAttrService Component"]
            
            subgraph StrategyParsers ["Vendor Strategy Parsers"]
                CiscoDriver["Cisco Parser"]
                AristaDriver["Arista Parser"]
                CienaDriver["Ciena Parser"]
                DriveNetsDriver["DriveNets Parser"]
                GenericDriver["Generic MIB Fallback"]
            end
        end

        subgraph SnmpPkg ["snmp Package"]
            ApiService["SnmpApiService Interface"]
            ConnectionPool["ConnectionPool Workers"]
            CacheManager["Session Cache Manager"]
            v2cEngine["SNMP v2c Worker"]
            v3Engine["SNMP v3 Engine"]
        end

        subgraph ParserPkg ["parser Package"]
            DeviceOutputParser["DeviceOutputParser Component"]
        end
    end

    CLI --> ChiRouter
    ChiRouter --> DeviceHandler
    ChiRouter --> ConsulRegistrar
    DeviceHandler --> DeviceAttrService

    DeviceAttrService --> CiscoDriver
    DeviceAttrService --> AristaDriver
    DeviceAttrService --> CienaDriver
    DeviceAttrService --> DriveNetsDriver
    DeviceAttrService --> GenericDriver

    DeviceAttrService --> ApiService
    DeviceAttrService --> DeviceOutputParser

    ApiService --> ConnectionPool
    ConnectionPool --> CacheManager
    CacheManager --> v2cEngine
    CacheManager --> v3Engine
```

---

## 4. C4 Level 4: Code & Class Relationship Diagram

The C4 Level 4 diagram details Go structs, interfaces, methods, and their relationships across packages.

```mermaid
classDiagram
    namespace web {
        class Request {
            +string Fqdn
            +string Ipv4
            +string Ipv6
            +string SnmpString
            +int SnmpPort
            +int IdRefActivity
            +int IdDevice
        }

        class Response {
            +Vendor Make
            +string Model
            +string Ip
            +string Ipv6
            +string Fqdn
            +string DeviceId
            +deviceSoftwareType DeviceType
            +string OSVersion
            +Send(w ResponseWriter)
        }

        class Transformer {
            <<interface>>
            +Transform(r Request) (*snmp.Device, error)
        }

        class requestTransformer {
            +Transform(r Request) (*snmp.Device, error)
        }
    }

    namespace api {
        class ServiceMonitoring {
            <<interface>>
            +RegisterAndListen(service Service) Observer
        }

        class consulRegistrar {
            -client *consul.Client
            +RegisterAndListen(service Service) Observer
        }

        class Server {
            +http.Server Server
            -observers *ServerObservers
        }
    }

    namespace service {
        class deviceService {
            <<interface>>
            +LoadDeviceDetailsByFqdn(r web.Request) (*web.Response, error)
            +LoadDeviceDetailsByIp(r web.Request) (*web.Response, error)
        }

        class deviceAttrService {
            -api snmp.SnmpApiService
            -outputParser parser.DeviceOutputParser
            -oids *config.OIDsConfig
            +LoadDeviceDetailsByFqdn(r web.Request) (*web.Response, error)
            +LoadDeviceDetailsByIp(r web.Request) (*web.Response, error)
        }
    }

    namespace snmp {
        class Device {
            +string Fqdn
            +string Ipv4
            +string Ipv6
            +uint16 Port
            +string Secret
        }

        class SnmpApiService {
            <<interface>>
            +WalkAndFind(handler, oid, targetValue) (string, error)
            +WalkForType(handler, oid, targetType) ([]gosnmp.SnmpPDU, error)
            +GetOne(handler, oid) (string, error)
            +BulkGet(handler, oids) (map[string]string, error)
        }

        class snmpService {
            +WalkAndFind(handler, oid, targetValue) (string, error)
            +GetOne(handler, oid) (string, error)
        }

        class pool {
            <<interface>>
            +GetActiveWorkers() []Run
            +GetPoolSize() int
            +Lock()
            +Unlock()
        }

        class connectionPool {
            -Mutex sync.Mutex
            -workers []Run
            +GetActiveWorkers() []Run
            +GetPoolSize() int
        }

        class ConnectionHandler {
            +Connection *gosnmp.GoSNMP
        }
    }

    namespace parser {
        class DeviceOutputParser {
            <<interface>>
            +ParseChassis(pdu) Chassis
            +ParseInterfaces(pdu) []Interface
        }

        class outputParser {
            +ParseChassis(pdu) Chassis
        }
    }

    Transformer <|.. requestTransformer : Implements
    ServiceMonitoring <|.. consulRegistrar : Implements
    deviceService <|.. deviceAttrService : Implements
    SnmpApiService <|.. snmpService : Implements
    pool <|.. connectionPool : Implements
    DeviceOutputParser <|.. outputParser : Implements

    deviceAttrService --> SnmpApiService : Uses
    deviceAttrService --> DeviceOutputParser : Uses
    deviceAttrService --> Request : Processes
    deviceAttrService --> Response : Produces
    snmpService --> ConnectionHandler : Executes Walks
    connectionPool --> ConnectionHandler : Manages
    requestTransformer --> Device : Constructs
```

---

## 5. C4 Level 4: Execution Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Interrogation as Interrogation Service
    participant Handler as api.fetchDeviceDetailsByFqdn
    participant Validator as Domain Scope Gate
    participant Service as service.DeviceAttrService
    participant SNMP as snmp.SnmpApiService
    participant Pool as snmp.ConnectionPool
    participant Hardware as Physical Network Router

    Interrogation->>Handler: POST /devices
    Handler->>Validator: Validate FQDN Domain Suffix
    
    alt Invalid Domain
        Validator-->>Handler: Reject Request
        Handler-->>Interrogation: HTTP 400 Bad Request
    else Valid Domain
        Validator-->>Handler: Domain Valid
        Handler->>Service: LoadDeviceDetailsByFqdn
        
        Service->>SNMP: GetOne sysObjectID
        SNMP->>Pool: GetConnection
        Pool->>Hardware: SNMP GET sysObjectID
        Hardware-->>Pool: Return sysObjectID PDU
        Pool-->>SNMP: sysObjectID PDU
        
        Service->>Service: Resolve Vendor (Cisco/Arista/Ciena)
        Service->>SNMP: BulkWalk IF-MIB and EntityMIB
        SNMP->>Hardware: Concurrent UDP BulkWalk
        Hardware-->>SNMP: Return Varbind Array
        
        SNMP-->>Service: Varbind Payload
        Service->>Service: Construct Response JSON
        Service-->>Handler: web.Response Object
        Handler-->>Interrogation: HTTP 200 OK JSON
    end
```
