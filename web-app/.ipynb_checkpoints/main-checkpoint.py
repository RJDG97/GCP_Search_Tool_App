# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Flask Web Server"""

import base64
import os
import re
from urllib.parse import urlparse

from consts import (
    CUSTOM_UI_DATASTORE_IDS,
    LOCATION,
    PROJECT_ID,
    SUMMARY_MODELS,
    VALID_LANGUAGES,
    WIDGET_CONFIGS,
)
from flask import Flask, render_template, request
from genappbuilder_utils import (
    list_documents,
    recommend_personalize,
    search_enterprise_search,
)
from google.api_core.exceptions import ResourceExhausted
import requests
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Set maximum upload size to 16MB

FORM_OPTIONS = {
    "language_list": VALID_LANGUAGES,
    "default_language": VALID_LANGUAGES[0],
}

CUSTOM_UI_SEARCH_ENGINES = [d["name"] for d in CUSTOM_UI_DATASTORE_IDS]

NAV_LINKS = [
    {"link": "/", "name": "Widgets", "icon": "widgets"},
    {
        "link": "/search",
        "name": "Custom UI",
        "icon": "build",
    },
    {
        "link": "https://github.com/GoogleCloudPlatform/generative-ai/tree/main/search/web-app",
        "name": "Source Code",
        "icon": "code",
    },
]

@app.route("/", methods=["GET"])
@app.route("/finance", methods=["GET"])
def index() -> str:
    """
    Web Server, Homepage for Widgets
    """

    return render_template(
        "index.html",
        title=NAV_LINKS[0]["name"],
        nav_links=NAV_LINKS,
        search_engine_options=WIDGET_CONFIGS,
    )


@app.route("/search", methods=["GET"])
def search() -> str:
    """
    Web Server, Homepage for Search - Custom UI
    """

    return render_template(
        "search.html",
        title=NAV_LINKS[1]["name"],
        nav_links=NAV_LINKS,
        search_engines=CUSTOM_UI_SEARCH_ENGINES,
        summary_models=SUMMARY_MODELS,
    )


@app.route("/search_genappbuilder", methods=["POST"])
def search_genappbuilder() -> str:
    """
    Handle Search Vertex AI Search Request
    """
    search_query = request.form.get("search_query", "")

    # Check if POST Request includes search query
    if not search_query:
        return render_template(
            "search.html",
            title=NAV_LINKS[1]["name"],
            nav_links=NAV_LINKS,
            search_engines=CUSTOM_UI_SEARCH_ENGINES,
            summary_models=SUMMARY_MODELS,
            message_error="No query provided",
        )

    search_engine = request.form.get("search_engine", "")

    if not search_engine:
        return render_template(
            "search.html",
            title=NAV_LINKS[1]["name"],
            nav_links=NAV_LINKS,
            search_engines=CUSTOM_UI_SEARCH_ENGINES,
            summary_models=SUMMARY_MODELS,
            message_error="No search engine selected",
        )

    summary_model = request.form.get("summary_model")
    summary_preamble = request.form.get("summary_preamble")

    results, summary, request_url, raw_request, raw_response = search_enterprise_search(
        project_id=PROJECT_ID,
        location=LOCATION,
        engine_id=CUSTOM_UI_DATASTORE_IDS[int(search_engine)]["engine_id"],
        search_query=search_query,
        summary_model=summary_model,
        summary_preamble=summary_preamble,
    )

    return render_template(
        "search.html",
        title=NAV_LINKS[1]["name"],
        nav_links=NAV_LINKS,
        search_engines=CUSTOM_UI_SEARCH_ENGINES,
        summary_models=SUMMARY_MODELS,
        message_success=search_query,
        results=results,
        summary=summary,
        request_url=request_url,
        raw_request=raw_request,
        raw_response=raw_response,
    )

@app.errorhandler(Exception)
def handle_exception(ex: Exception):
    """
    Handle Application Exceptions
    """
    message_error = "An Unknown Error Occurred"

    # Pass through HTTP errors
    if isinstance(ex, HTTPException):
        message_error = ex.get_description()
    elif isinstance(ex, ResourceExhausted):
        message_error = ex.message
    else:
        message_error = str(ex)

    return render_template(
        "search.html",
        title=NAV_LINKS[1]["name"],
        form_options=FORM_OPTIONS,
        nav_links=NAV_LINKS,
        search_engines=CUSTOM_UI_SEARCH_ENGINES,
        summary_models=SUMMARY_MODELS,
        message_error=message_error,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
