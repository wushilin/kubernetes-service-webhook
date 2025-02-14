import json
import base64
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/mutate', methods=['POST'])
def mutate():
    req = request.get_json()
    # Extract AdmissionReview request
    admission_request = req.get("request")
    if not admission_request:
        return jsonify({"error": "invalid request"}), 400

    service = req["request"]["object"]
    # Check for annotation "webhook-bypass: true"
    annotations = service.get("metadata", {}).get("annotations", {})
    if annotations.get("webhook-bypass") == "true":
        logging.info(f"Allowed bypass services")
        return jsonify({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": req["request"]["uid"],
                "allowed": True  # Allow creation without modification
            }
        })

    logging.info(f"Request: {admission_request}")
    obj = admission_request.get("object", {})
    metadata = obj.get("metadata", {})
    spec = obj.get("spec", {})

    # Check if it's a LoadBalancer Service
    if spec.get("type") == "LoadBalancer":
        logging.info(f"Mutating Service {metadata.get('name')} in {metadata.get('namespace')}")

        # JSONPatch to change type to ClusterIP
        patch = [
		        {"op": "replace", "path": "/spec/type", "value": "ClusterIP"}, 
                {"op": "remove", "path": "/spec/externalTrafficPolicy"},
                {"op": "remove", "path": "/spec/allocateLoadBalancerNodePorts"},
                {"op": "remove", "path": "/spec/internalTrafficPolicy"}
        ]       
        # ✅ Encode patch as Base64
        patch_b64 = base64.b64encode(json.dumps(patch).encode("utf-8")).decode("utf-8")

        response = {
	    "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": admission_request["uid"],
                "allowed": True,
                "patchType": "JSONPatch",
                "patch": patch_b64  # ✅ Now Base64-encoded
            }
        }
    else:
        logging.info(f"Skipping Service {metadata.get('name')}, not a LoadBalancer.")
        response = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": admission_request["uid"],
                "allowed": True
            }
        }

    return jsonify(response)

if __name__ == '__main__':
    cert_path = "/etc/webhook/certs/tls.crt"
    key_path = "/etc/webhook/certs/tls.key"

    logging.info("Starting Flask Webhook with TLS...")
    app.run(host='0.0.0.0', port=443, ssl_context=(cert_path, key_path))

