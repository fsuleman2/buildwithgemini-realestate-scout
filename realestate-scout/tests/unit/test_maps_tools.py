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

"""Unit tests for Geocoding and Places tools."""

from unittest.mock import MagicMock, patch

from app.tools import _normalize_place_type, geocode_address, search_nearby_places


def test_normalize_place_type() -> None:
    assert _normalize_place_type("restaurants") == "restaurant"
    assert _normalize_place_type("cafe") == "cafe"
    assert _normalize_place_type("cafes") == "cafe"
    assert _normalize_place_type("coffee") == "cafe"
    assert _normalize_place_type("coffee shop") == "cafe"
    assert _normalize_place_type("parks") == "park"
    assert _normalize_place_type("transit") == "transit_station"
    assert _normalize_place_type("gyms") == "gym"


def test_geocode_address_mocked() -> None:
    fake_response = {
        "status": "OK",
        "results": [
            {
                "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
                "geometry": {
                    "location": {
                        "lat": 37.422,
                        "lng": -122.084,
                    }
                },
                "place_id": "ChIJF4Yf2Ry7j4AR__1AkytDyAE",
            }
        ],
    }

    mock_res = MagicMock()
    mock_res.json.return_value = fake_response

    with patch("requests.get", return_value=mock_res):
        res = geocode_address("1600 Amphitheatre Pkwy, Mountain View, CA")
        assert res["name"] == "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
        assert res["address"] == "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
        assert res["location"]["latitude"] == 37.422
        assert res["location"]["longitude"] == -122.084
        assert res["place_id"] == "ChIJF4Yf2Ry7j4AR__1AkytDyAE"


def test_search_nearby_places_mocked() -> None:
    fake_response = {
        "places": [
            {
                "displayName": {"text": "Blue Bottle Coffee", "languageCode": "en"},
                "formattedAddress": "123 Market St, San Francisco, CA 94105, USA",
                "location": {
                    "latitude": 37.79,
                    "longitude": -122.39,
                },
            }
        ]
    }

    mock_res = MagicMock()
    mock_res.json.return_value = fake_response

    with patch("requests.post", return_value=mock_res):
        places = search_nearby_places(
            latitude=37.79,
            longitude=-122.39,
            place_type="cafe",
        )
        assert isinstance(places, list)
        assert len(places) == 1
        assert places[0]["name"] == "Blue Bottle Coffee"
        assert places[0]["address"] == "123 Market St, San Francisco, CA 94105, USA"
        assert places[0]["location"] == {"latitude": 37.79, "longitude": -122.39}
