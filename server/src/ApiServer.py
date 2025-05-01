from flask import Flask, jsonify, request, abort, make_response


class ApiServer:
    def __init__(self, host, port, controller):
        self.app = Flask(__name__)
        self.api_host = host
        self.api_port = port
        self.controller = controller
        # Define error handler and routes
        self._initialize_routes()

    def _initialize_routes(self):
        # Error handler
        self.app.errorhandler(400)(self.bad_request)

        # Routes
        self.app.route('/services', methods=['GET'])(self.list_services)
        self.app.route('/service', methods=['GET'])(self.get_current_service)
        self.app.route('/service', methods=['PUT'])(self.change_service)

    def bad_request(self, error):
        return make_response(jsonify({"error": error.description}), 400)

    def list_services(self):
        return jsonify({"services": self.controller.available_services})

    def list_modes(self):
        return jsonify({"modes": self.controller.available_modes})

    def get_current_service(self):
        return jsonify({"currentService": self.controller.current_service, "mode": self.controller.current_mode})

    def change_service(self):
        data = request.get_json()

        if not data or 'serviceName' not in data:
            abort(400, description="Missing serviceName in request body")

        if not data or 'mode' not in data:
            abort(400, description="Missing mode in request body")

        service_name = data['serviceName']
        mode = data['mode']

        if service_name not in self.controller.available_services:
            abort(400, description="Invalid service name")

        if mode not in self.controller.available_modes:
            abort(400, description="Invalid mode name")

        self.controller.switch_to_service(service_name, mode)

        return jsonify({"message": "Service changed successfully"})

    def run(self):
        self.app.run(host=self.api_host, port=self.api_port)
