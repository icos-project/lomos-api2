# lomos-api2
# Copyright © 2022-2024 XLAB d.o.o. All rights reserved.

# The lomos-api2 is released under the commercial license.
# Redistribution and use in source and binary forms is not permitted without prior written permission.

import logging
import sys
import base64
import binascii
import os
import flask
import flask_login
from flask import Flask, jsonify
import json
from . import views_summary

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def config_to_dict(config: flask.Config) -> dict:
    def _to_json_or_str(vv):
        if isinstance(vv, (int, float, str, bool)):
            return vv
        try:
            return json.dumps(vv)
        except TypeError:
            return str(vv)
    resp = {
        kk: _to_json_or_str(config[kk])
        for kk in config.keys()
    }
    return resp


class User(flask_login.UserMixin):
    def __init__(self, username, password, api_key):
        self.id = username
        self.username = username
        self.password = password
        self.tokens = []
        self.api_key = api_key


_all_users = {"api_user": User("api_user", "", os.environ["FLASK_LOMOS_API_USER_API_KEY"])}
# _all_users = {"api_user": User("api_user", "pp", "ttrt")}


def setup_app(app: Flask) -> None:
    app.config.from_object('lomos_api2.default_settings')
    app.config.from_prefixed_env()
    # print(f"app.config={json.dumps(config_to_dict(app.config), indent=4)}")
    config_keys = [
        "LOMOS_OPENSEARCH_API_URL",
        "LOMOS_INDEX_NAME",
    ]
    for key in config_keys:
        print(f"app.config {key}={app.config[key]}")
    sys.stdout.flush()


app = Flask(__name__)
setup_app(app)
app.register_blueprint(views_summary.summary_api, url_prefix='/api')
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


# @login_manager.user_loader
# def user_loader(id):
#     return users.get(id)


@login_manager.request_loader
def load_user_from_request(request):
    auth_header = request.headers.get('Authorization')
    # logger.debug(f"auth_header={auth_header}")
    if auth_header and auth_header.startswith("Bearer "):
        api_key_b64 = auth_header.replace("Bearer ", "", 1)
        try:
            api_key_bytes = base64.b64decode(api_key_b64)
        except (binascii.Error, ValueError) as ex:
            logger.error(f"Invalid token ex={ex}")
            return None
        try:
            api_key = api_key_bytes.decode("utf-8")
        except UnicodeDecodeError as ex:
            logger.error(f"Invalid token ex={ex}")
            return None
        # logger.debug(f"api_key={api_key}")

        # user = User.query.filter_by(api_key=api_key).first()
        users = [uu for uu in _all_users.values() if api_key == uu.api_key]
        if not users:
            return None
        if len(users) > 1:
            return None
        user = users[0]
        # logger.debug(f"user username={user.username} {user.api_key}")
        return user
    return None


# @app.post("/auth/login")
# def login():
#     # username = flask.request.form["username"]
#     # password = flask.request.form["password"]
#     username = flask.request.json["username"]
#     password = flask.request.json["password"]
#     user = _all_users.get(username)
#     if user is None or not user.password or user.password != password:
#         return flask.redirect(flask.url_for("login"))
#     flask_login.login_user(user)
#     return flask.redirect(flask.url_for("whoami"))


@app.route('/auth/whoami')
@flask_login.login_required
def whoami():
    user = flask_login.current_user
    data = dict(
        username=user.username,
    )
    return jsonify(dict(data))


@app.route("/")
def main_page():
    return "<p>The lomos-api2 app</p>"
    # return f"app.config={json.dumps(config_to_dict(app.config), indent=4)}"
