from flask import Flask, jsonify, request, abort, make_response
import control_logic
app = Flask(__name__)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({"error": error.description}), 400)

@app.route('/services', methods=['GET'])
def list_services():
    return jsonify({"services": control_logic.available_services})

@app.route('/service', methods=['GET'])
def get_current_service():
    return jsonify({"currentService": control_logic.current_service})

@app.route('/service', methods=['PUT'])
def change_service():
    data = request.get_json()

    if not data or 'serviceName' not in data:
        abort(400, description="Missing serviceName in request body")

    service_name = data['serviceName']

    if service_name not in control_logic.available_services:
        abort(400, description="Invalid service name")

    control_logic.switch_to_service(service_name)

    return jsonify({"message": "Service changed successfully"})

def run_api_server(api_host, api_port):
    app.run(host=api_host, port=api_port)