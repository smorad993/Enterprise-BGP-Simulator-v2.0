"""
Flask Server for Enterprise BGP Simulator v2.0
"""

from flask import Flask, jsonify, render_template, request
from bgp_engine import bgp_engine

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/bgp/state", methods=["GET"])
def get_bgp_state():
    bgp_engine.generate_keepalive()
    return jsonify({
        "routers": {k: v.to_dict() for k, v in bgp_engine.routers.items()},
        "links": bgp_engine.links,
        "packets": bgp_engine.packet_stream[:20],
        "snmp_traps": bgp_engine.snmp_trap_stream[:10]
    })

@app.route("/api/bgp/automation", methods=["GET"])
def get_automation_code():
    router_name = request.args.get("router", "R1")
    payloads = bgp_engine.get_automation_payload(router_name)
    return jsonify(payloads)

@app.route("/api/bgp/policy", methods=["POST"])
def set_policy():
    data = request.get_json() or {}
    router_name = data.get("router_name", "R1")
    policy_type = data.get("policy_type")
    value = data.get("value")

    if not policy_type:
        return jsonify({"error": "policy_type is required"}), 400

    success = bgp_engine.set_policy(router_name, policy_type, value)
    if not success:
        return jsonify({"error": "Failed to set policy"}), 400

    return jsonify({
        "message": f"Policy {policy_type}={value} applied to {router_name}",
        "policies": bgp_engine.routers[router_name].policies
    })

@app.route("/api/bgp/fault", methods=["POST"])
def inject_fault():
    data = request.get_json() or {}
    link_name = data.get("link_name", "R1-R2")
    fault_type = data.get("fault_type", "AS_MISMATCH")

    success = bgp_engine.inject_fault(link_name, fault_type)
    if not success:
        return jsonify({"error": "Failed to inject fault"}), 400

    return jsonify({
        "message": f"Fault {fault_type} injected on link {link_name}",
        "links": bgp_engine.links
    })

@app.route("/api/bgp/link/toggle", methods=["POST"])
def toggle_link():
    data = request.get_json() or {}
    link_name = data.get("link_name")
    if not link_name:
        return jsonify({"error": "link_name is required"}), 400

    success = bgp_engine.toggle_link(link_name)
    if not success:
        return jsonify({"error": "Invalid link name"}), 400

    return jsonify({
        "message": f"Link {link_name} toggled",
        "links": bgp_engine.links
    })

@app.route("/api/bgp/reset", methods=["POST"])
def reset_bgp():
    bgp_engine.reset_topology()
    return jsonify({"message": "BGP Topology Reset Completed"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
