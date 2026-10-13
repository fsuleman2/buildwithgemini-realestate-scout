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

"""Firestore tools for RealEstate Scout agent."""

import datetime
import json
import os
import urllib.parse
import urllib.request
import uuid
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types
import requests

load_dotenv()

# Hardcode project ID and bucket name as strings
PROJECT_ID = "qwiklabs-gcp-04-f9029d637c52"
BUCKET_NAME = "realestate-scout-assets"
COLLECTION_PROPERTIES = "properties"
COLLECTION_FAVORITES = "saved_favorites"

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def search_properties(
    max_price: int | None = None,
    min_beds: int | None = None,
    neighborhood: str | None = None,
    pet_friendly: bool | None = None,
) -> list[dict[str, Any]]:
    """Search and filter rental properties from the Firestore database.

    Args:
        max_price: Optional maximum monthly rent in USD (e.g. 3500).
        min_beds: Optional minimum number of bedrooms (0 for studio, 1, 2, etc.).
        neighborhood: Optional neighborhood name (e.g. "Mission District", "SOMA", "Sunset").
        pet_friendly: Optional boolean filter for pet-friendly units (True or False).

    Returns:
        A list of matching property dictionaries.
    """
    props_ref = db.collection(COLLECTION_PROPERTIES)
    docs = props_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Apply in-memory filtering for flexible search criteria
        if max_price is not None and data.get("price", 0) > max_price:
            continue
        if min_beds is not None and data.get("bedrooms", 0) < min_beds:
            continue
        if neighborhood and neighborhood.lower() not in data.get("neighborhood", "").lower():
            continue
        if pet_friendly is not None and data.get("pet_friendly") != pet_friendly:
            continue

        results.append(data)

    return results


def get_property_details(property_id: str) -> dict[str, Any]:
    """Retrieve detailed specifications for a specific property listing by its ID.

    Args:
        property_id: The ID of the property to retrieve (e.g. "prop-001").

    Returns:
        A dictionary containing the property's detailed specifications or an error message.
    """
    doc_ref = db.collection(COLLECTION_PROPERTIES).document(property_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Property listing with ID '{property_id}' was not found."}

    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_property(
    title: str,
    neighborhood: str,
    price: int,
    bedrooms: int,
    bathrooms: float,
    sqft: int,
    pet_friendly: bool,
    amenities: list[str],
    description: str,
    city: str = "San Francisco",
    tour_available: bool = True,
) -> dict[str, Any]:
    """Add a new property rental listing to the Firestore database.

    Args:
        title: Title of the property listing (e.g. "Bright Bernal Heights 1BR").
        neighborhood: Neighborhood name (e.g. "Bernal Heights").
        price: Monthly rent in USD (e.g. 3100).
        bedrooms: Number of bedrooms (0 for studio, 1, 2, etc.).
        bathrooms: Number of bathrooms (e.g. 1.0, 1.5).
        sqft: Approximate square footage (e.g. 750).
        pet_friendly: Whether pets are allowed.
        amenities: List of amenities (e.g. ["in-unit laundry", "balcony", "dishwasher"]).
        description: Detailed description of the rental unit.
        city: City name (defaults to "San Francisco").
        tour_available: Whether in-person tours are available (defaults to True).

    Returns:
        A dictionary confirming creation with the new property ID and details.
    """
    short_id = f"prop-{uuid.uuid4().hex[:6]}"
    property_data = {
        "id": short_id,
        "title": title,
        "neighborhood": neighborhood,
        "city": city,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft": sqft,
        "pet_friendly": pet_friendly,
        "amenities": amenities,
        "description": description,
        "tour_available": tour_available,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    doc_ref = db.collection(COLLECTION_PROPERTIES).document(short_id)
    doc_ref.set(property_data)

    return {
        "status": "success",
        "message": f"Successfully created property listing '{title}' with ID {short_id}.",
        "property": property_data,
    }


def save_favorite_property(property_id: str, notes: str = "") -> dict[str, Any]:
    """Save a property listing to the user's saved favorites list in Firestore.

    Args:
        property_id: The ID of the property to save as favorite (e.g. "prop-001").
        notes: Optional personal notes regarding the property.

    Returns:
        A dictionary confirming that the property was added to saved favorites.
    """
    # Check if the property exists
    prop_doc = db.collection(COLLECTION_PROPERTIES).document(property_id).get()
    if not prop_doc.exists:
        return {"error": f"Cannot favorite non-existent property with ID '{property_id}'."}

    prop_data = prop_doc.to_dict()
    fav_data = {
        "property_id": property_id,
        "title": prop_data.get("title", ""),
        "price": prop_data.get("price", 0),
        "neighborhood": prop_data.get("neighborhood", ""),
        "notes": notes,
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    fav_ref = db.collection(COLLECTION_FAVORITES).document(property_id)
    fav_ref.set(fav_data)

    return {
        "status": "success",
        "message": f"Property '{prop_data.get('title')}' ({property_id}) saved to favorites.",
        "favorite": fav_data,
    }


def calculate_move_in_costs(
    property_id: str,
    monthly_income: float | None = None,
    has_pet: bool = False,
) -> dict[str, Any]:
    """Calculate upfront move-in costs and monthly affordability for a property.

    Args:
        property_id: The ID of the property listing (e.g. "prop-001").
        monthly_income: Optional applicant gross monthly income in USD to evaluate affordability.
        has_pet: Whether the applicant plans to live with a pet (adds a $500 pet deposit if pet-friendly).

    Returns:
        A dictionary breakdown of upfront costs, monthly estimates, and income qualification.
    """
    doc_ref = db.collection(COLLECTION_PROPERTIES).document(property_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Property listing with ID '{property_id}' was not found."}

    data = doc.to_dict()
    rent = data.get("price", 0)
    title = data.get("title", property_id)
    pet_friendly = data.get("pet_friendly", False)

    security_deposit = rent
    pet_deposit = 500 if (has_pet and pet_friendly) else 0
    total_upfront = rent + security_deposit + pet_deposit
    estimated_utilities = 180
    recommended_income = rent * 3

    result: dict[str, Any] = {
        "property_id": property_id,
        "title": title,
        "monthly_rent": rent,
        "upfront_costs": {
            "first_month_rent": rent,
            "security_deposit": security_deposit,
            "pet_deposit": pet_deposit,
            "total_upfront_cash": total_upfront,
        },
        "estimated_monthly_expenses": {
            "rent": rent,
            "utilities": estimated_utilities,
            "total": rent + estimated_utilities,
        },
        "recommended_minimum_monthly_income": recommended_income,
    }

    if monthly_income is not None and monthly_income > 0:
        ratio = round((rent / monthly_income) * 100, 1)
        result["income_evaluation"] = {
            "monthly_income": monthly_income,
            "rent_to_income_ratio_percent": ratio,
            "meets_3x_rule": monthly_income >= recommended_income,
            "affordable": ratio <= 33.3,
        }

    return result


def lookup_neighborhood_map_info(
    neighborhood_or_address: str,
    city: str = "San Francisco",
) -> dict[str, Any]:
    """Look up real-world geographic coordinates, postal code, and map details for a neighborhood or address.

    Uses the public OpenStreetMap Nominatim API (from public-apis). Reads optional NOMINATIM_API_KEY from environment.

    Args:
        neighborhood_or_address: Name of the neighborhood or street address (e.g. "Pacific Heights" or "Sunset District").
        city: City name to scope the location search (defaults to "San Francisco").

    Returns:
        A dictionary with latitude, longitude, postal code, formatted display address, and OpenStreetMap URL.
    """
    query = f"{neighborhood_or_address}, {city}"
    encoded = urllib.parse.quote(query)

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("NOMINATIM_API_KEY")
    url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&addressdetails=1&limit=1"
    if api_key:
        url += f"&key={urllib.parse.quote(api_key)}"

    headers = {
        "User-Agent": "RealEstateScoutApp/1.0"
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if not data:
                return {
                    "error": f"No location data found for '{neighborhood_or_address}' in {city}."
                }

            item = data[0]
            address = item.get("address", {})
            return {
                "query": query,
                "display_name": item.get("display_name"),
                "latitude": float(item.get("lat", 0.0)),
                "longitude": float(item.get("lon", 0.0)),
                "neighborhood": address.get("neighbourhood") or address.get("suburb") or neighborhood_or_address,
                "postcode": address.get("postcode"),
                "city": address.get("city") or address.get("town") or city,
                "bounding_box": item.get("boundingbox"),
                "osm_url": f"https://www.openstreetmap.org/#map=16/{item.get('lat')}/{item.get('lon')}",
            }
    except Exception as e:
        return {"error": f"Failed to fetch map data: {str(e)}"}


def _normalize_place_type(place_type: str) -> str:
    """Normalize user or model place type string to supported Places API (New) Table A type."""
    clean = place_type.lower().strip().replace("-", "_").replace(" ", "_")
    type_map = {
        "restaurants": "restaurant",
        "food": "restaurant",
        "dining": "restaurant",
        "cafes": "cafe",
        "coffee": "cafe",
        "coffee_shop": "cafe",
        "coffee_shops": "cafe",
        "bars": "bar",
        "parks": "park",
        "gyms": "gym",
        "fitness": "gym",
        "fitness_center": "fitness_center",
        "schools": "school",
        "supermarkets": "supermarket",
        "groceries": "grocery_store",
        "grocery": "grocery_store",
        "grocery_store": "grocery_store",
        "grocery_stores": "grocery_store",
        "transit": "transit_station",
        "transit_stations": "transit_station",
        "subway": "subway_station",
        "subways": "subway_station",
        "train": "train_station",
        "trains": "train_station",
        "bus": "bus_station",
        "buses": "bus_station",
        "hospitals": "hospital",
        "pharmacies": "pharmacy",
        "banks": "bank",
        "libraries": "library",
        "shops": "store",
        "shopping": "shopping_mall",
    }
    if clean in type_map:
        return type_map[clean]
    if clean.endswith("s") and not clean.endswith("ss") and not clean.endswith("gas"):
        return clean[:-1]
    return clean


def geocode_address(address: str) -> dict[str, Any]:
    """Turn a street address or location name into geographic coordinates using the Google Maps Geocoding API.

    Calls the Geocoding API REST endpoint directly to convert an address string
    into latitude and longitude coordinates, returning the key fields (name, address, location).

    Args:
        address: The street address or location to geocode (e.g. "1600 Amphitheatre Pkwy, Mountain View, CA" or "Mission District, San Francisco, CA").

    Returns:
        A dictionary with the key fields:
        - "name": Formatted address or place description.
        - "address": The formatted street address.
        - "location": {"latitude": float, "longitude": float}
        - "place_id": Google Maps Place ID.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key,
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            error_message = (
                data.get("error_message")
                or f"No geocoding results found for '{address}' (status: {data.get('status')})."
            )
            return {"error": error_message}

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        geometry_loc = result.get("geometry", {}).get("location", {})
        latitude = geometry_loc.get("lat")
        longitude = geometry_loc.get("lng")
        place_id = result.get("place_id", "")

        return {
            "name": formatted_address,
            "address": formatted_address,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "place_id": place_id,
        }
    except Exception as e:
        return {"error": f"Failed to call Geocoding API: {str(e)}"}


def search_nearby_places(
    latitude: float | None = None,
    longitude: float | None = None,
    place_type: str = "restaurant",
    address: str | None = None,
    radius: float = 1000.0,
    max_results: int = 5,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Find nearby places of a given type around coordinates using the Google Maps Places API (New).

    Calls the Places API (New) searchNearby REST endpoint directly using POST
    with the X-Goog-Api-Key and X-Goog-FieldMask headers, and returns key fields (name, address, location).

    Args:
        latitude: Latitude coordinate of the center search location.
        longitude: Longitude coordinate of the center search location.
        place_type: Type of place to find (e.g. "restaurant", "cafe", "park", "transit_station", "supermarket", "gym", "school").
        address: Optional address to geocode if latitude and longitude are not provided.
        radius: Search radius in meters (defaults to 1000.0 meters, max 50000.0).
        max_results: Maximum number of places to return (defaults to 5, max 20).

    Returns:
        A list of dictionaries for matching places, each containing key fields:
        - "name": Display name of the place.
        - "address": Formatted address of the place.
        - "location": {"latitude": float, "longitude": float}
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    # Resolve coordinates if address is supplied and coords are missing
    if latitude is None or longitude is None:
        if address:
            geo = geocode_address(address)
            if "error" in geo:
                return {"error": f"Failed to geocode address '{address}' for nearby search: {geo['error']}"}
            latitude = geo["location"]["latitude"]
            longitude = geo["location"]["longitude"]
        else:
            return {"error": "Either latitude and longitude coordinates OR an address must be provided."}

    # Normalize place_type to match Table A supported types
    normalized_type = _normalize_place_type(place_type)

    endpoint = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": [normalized_type],
        "maxResultCount": max(1, min(int(max_results), 20)),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius),
            }
        },
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        data = response.json()

        if "error" in data:
            error_details = data["error"].get("message", "Unknown error from Places API")
            return {"error": f"Places API error: {error_details}"}

        places = []
        for p in data.get("places", []):
            places.append({
                "name": p.get("displayName", {}).get("text", ""),
                "address": p.get("formattedAddress", ""),
                "location": p.get("location", {}),
            })
        return places
    except Exception as e:
        return {"error": f"Failed to call Places API: {str(e)}"}


async def generate_virtual_staging_image(
    prompt: str,
    property_id: str = "",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Generate a virtual staging, interior design, or neighborhood visualization image.

    Uses gemini-3.1-flash-lite-image in the global region.
    Saves the image artifact to the session using tool_context.save_artifact,
    and uploads the image bytes directly to the public Cloud Storage bucket.

    Args:
        prompt: Description of the room staging or decor concept (e.g. "Modern minimalist staged living room with cream sofa and wood floors").
        property_id: Optional property ID (e.g. "prop-001") to associate with the staging image.
        tool_context: ToolContext injected by the framework to record artifacts for the Playground.

    Returns:
        A dictionary with the public Cloud Storage HTTPS URL, artifact filename, and status.
    """
    full_prompt = prompt
    if property_id:
        try:
            prop_doc = db.collection(COLLECTION_PROPERTIES).document(property_id).get()
            if prop_doc.exists:
                prop_data = prop_doc.to_dict()
                full_prompt = (
                    f"Interior design virtual staging for {prop_data.get('title', property_id)} in {prop_data.get('neighborhood', 'San Francisco')}: "
                    f"{prompt}. High-end interior architectural photography, beautiful staging, natural lighting."
                )
        except Exception:
            pass

    try:
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
    except Exception as e:
        return {"error": f"Failed to generate image: {str(e)}"}

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "Image generation completed but no image bytes were returned."}

    ext = "jpg" if "jpeg" in mime_type else "png"
    prefix = f"{property_id}_" if property_id else "staging_"
    filename = f"{prefix}{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact to tool_context if available (appears in Playground Artifacts panel)
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception:
            pass

    # 2. Upload bytes directly to public Cloud Storage bucket (without writing to a local file)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "prompt": prompt,
        "filename": filename,
        "image_url": public_url,
        "message": f"Successfully generated image and uploaded to {public_url}",
    }



