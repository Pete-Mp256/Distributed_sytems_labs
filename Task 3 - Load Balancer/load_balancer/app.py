"""
app.py

Load Balancer for ICS 4104 Assignment 1 - Task 3.

Endpoints:
  GET    /rep    -> status of managed replicas
  POST   /add    -> scale up
  DELETE /rm     -> scale down
  GET    /<path> -> routed to a replica via the consistent hash ring
"""

import os
import threading

from flask import Flask, request, jsonify, Response

from manager import ServerManager

app = Flask(__name__)
manager = ServerManager()

INITIAL_N = int(os.environ.get("INITIAL_N", "3"))

# Endpoints implemented by the Task 1 server image.
VALID_PATHS = {"home"}


def _bootstrap():
    default_hostnames = [f"Server-{i}" for i in range(1, INITIAL_N + 1)]
    manager.add_servers(INITIAL_N, default_hostnames)


@app.route("/rep", methods=["GET"])
def rep():
    replicas = manager.get_replicas()
    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful",
    }), 200


@app.route("/add", methods=["POST"])
def add():
    payload = request.get_json(silent=True) or {}
    n = payload.get("n")
    hostnames = payload.get("hostnames", [])

    if not isinstance(n, int) or n <= 0:
        return jsonify({
            "message": "<Error> 'n' must be a positive integer",
            "status": "failure",
        }), 400

    try:
        replicas = manager.add_servers(n, hostnames)
    except ValueError as exc:
        return jsonify({"message": f"<Error> {exc}", "status": "failure"}), 400
    except RuntimeError as exc:
        return jsonify({"message": f"<Error> {exc}", "status": "failure"}), 500

    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful",
    }), 200


@app.route("/rm", methods=["DELETE"])
def rm():
    payload = request.get_json(silent=True) or {}
    n = payload.get("n")
    hostnames = payload.get("hostnames", [])

    if not isinstance(n, int) or n <= 0:
        return jsonify({
            "message": "<Error> 'n' must be a positive integer",
            "status": "failure",
        }), 400

    try:
        replicas = manager.remove_servers(n, hostnames)
    except ValueError as exc:
        return jsonify({"message": f"<Error> {exc}", "status": "failure"}), 400

    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful",
    }), 200


@app.route("/<path:path>", methods=["GET"])
def route(path):
    if path not in VALID_PATHS:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure",
        }), 400

    resp, error = manager.route_request(path)
    if error:
        return jsonify({"message": f"<Error> {error}", "status": "failure"}), 503

    return Response(
        resp.content,
        status=resp.status_code,
        mimetype=resp.headers.get("Content-Type", "application/json"),
    )


if __name__ == "__main__":
    _bootstrap()
    threading.Thread(target=manager.health_check_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)
