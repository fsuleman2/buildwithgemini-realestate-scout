# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import logging
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_property,
    calculate_move_in_costs,
    generate_property_tour_video,
    generate_virtual_staging_image,
    geocode_address,
    get_property_details,
    lookup_neighborhood_map_info,
    save_favorite_property,
    search_nearby_places,
    search_properties,
)

MODEL = "gemini-3.8-flash"

def _get_code_executor() -> AgentEngineSandboxCodeExecutor | None:
    """Resolve AgentEngineSandboxCodeExecutor from env or deployment_metadata.json."""
    sandbox_name = os.environ.get("AGENT_ENGINE_SANDBOX_RESOURCE_NAME") or os.environ.get("SANDBOX_RESOURCE_NAME")
    engine_name = os.environ.get("AGENT_ENGINE_RESOURCE_NAME") or os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")

    # Fall back to deployment_metadata.json if not in environment
    agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_path = os.path.join(agent_dir, "deployment_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                if not sandbox_name and "sandbox_resource_name" in meta:
                    sandbox_name = meta["sandbox_resource_name"]
                if not engine_name and "remote_agent_runtime_id" in meta:
                    engine_name = meta["remote_agent_runtime_id"]
        except Exception as e:
            logger.warning("Failed to load deployment_metadata.json: %s", e)

    if sandbox_name:
        return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_name)
    if engine_name:
        return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_name)
    return AgentEngineSandboxCodeExecutor()

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=(
        "You are RealEstate Scout, an intelligent apartment finding and real estate assistant. "
        "You help apartment hunters find, compare, evaluate, and virtually stage rental listings from the Firestore catalog.\n\n"
        "Your capabilities:\n"
        "1. Search and filter listings based on budget, neighborhood, bedrooms, pet policies using `search_properties`.\n"
        "2. Retrieve in-depth specifications for any property using `get_property_details`.\n"
        "3. Calculate upfront move-in costs and affordability using `calculate_move_in_costs`.\n"
        "4. Turn addresses or location names into coordinates using `geocode_address`.\n"
        "5. Find nearby amenities and places of interest (restaurants, cafes, transit, parks, groceries, etc.) using `search_nearby_places`.\n"
        "6. Look up geographic coordinates, postal codes, and map details using `lookup_neighborhood_map_info`.\n"
        "7. Generate virtual staging and interior design concepts using `generate_virtual_staging_image`.\n"
        "8. Save properties to the user's favorites list using `save_favorite_property`.\n"
        "9. Add new rental listings to the database using `add_property`.\n"
        "10. Generate cinematic video walkthrough tours for properties using `generate_property_tour_video`.\n"
        "11. Run safe Python code in an isolated cloud sandbox environment (Agent Platform Sandbox) for advanced financial modeling, complex affordability calculations, custom rent vs. buy comparisons, and data analysis."
    ),
    workflow_description="Analyze the user's request, invoke tools or execute sandboxed Python code as needed to fetch data, compute analytics, or generate images, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        search_properties,
        get_property_details,
        calculate_move_in_costs,
        geocode_address,
        search_nearby_places,
        lookup_neighborhood_map_info,
        generate_virtual_staging_image,
        generate_property_tour_video,
        save_favorite_property,
        add_property,
    ],
    code_executor=_get_code_executor(),
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
