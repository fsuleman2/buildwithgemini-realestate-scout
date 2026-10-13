#!/usr/bin/env python3
"""Seed script for RealEstate Scout Firestore backend."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-f9029d637c52"
COLLECTION_NAME = "properties"

PROPERTIES = [
    {
        "id": "prop-001",
        "title": "Sunlit Mission District Loft",
        "neighborhood": "Mission District",
        "city": "San Francisco",
        "price": 3200,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "sqft": 780,
        "pet_friendly": True,
        "amenities": ["in-unit laundry", "hardwood floors", "dishwasher", "balcony"],
        "description": "Spacious top-floor loft with exposed brick, abundant natural light, and modern kitchen finishes.",
        "tour_available": True,
    },
    {
        "id": "prop-002",
        "title": "Cozy Pacific Heights Victorian Flat",
        "neighborhood": "Pacific Heights",
        "city": "San Francisco",
        "price": 4100,
        "bedrooms": 2,
        "bathrooms": 1.5,
        "sqft": 1100,
        "pet_friendly": False,
        "amenities": ["in-unit laundry", "fireplace", "garage parking", "bay windows"],
        "description": "Charming 2-bedroom in a classic Victorian building with high ceilings, crown molding, and dedicated parking.",
        "tour_available": True,
    },
    {
        "id": "prop-003",
        "title": "Modern SOMA High-Rise 1BR",
        "neighborhood": "SOMA",
        "city": "San Francisco",
        "price": 3450,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "sqft": 720,
        "pet_friendly": True,
        "amenities": ["fitness center", "rooftop deck", "in-unit laundry", "concierge", "dishwasher"],
        "description": "Luxury living near tech hubs and transit with panoramic skyline views and full-service amenities.",
        "tour_available": True,
    },
    {
        "id": "prop-004",
        "title": "Quiet Sunset District Garden Flat",
        "neighborhood": "Sunset",
        "city": "San Francisco",
        "price": 2700,
        "bedrooms": 2,
        "bathrooms": 1.0,
        "sqft": 950,
        "pet_friendly": True,
        "amenities": ["shared garden", "dishwasher", "hardwood floors", "walk-in closet"],
        "description": "Peaceful 2-bedroom garden apartment blocks from Golden Gate Park and N-Judah Muni line.",
        "tour_available": False,
    },
    {
        "id": "prop-005",
        "title": "Hayes Valley Boutique Studio",
        "neighborhood": "Hayes Valley",
        "city": "San Francisco",
        "price": 2350,
        "bedrooms": 0,
        "bathrooms": 1.0,
        "sqft": 480,
        "pet_friendly": False,
        "amenities": ["in-unit laundry", "stainless appliances", "bike storage"],
        "description": "Efficient and stylish studio nestled in the heart of Hayes Valley cafes, boutiques, and world-class dining.",
        "tour_available": True,
    },
    {
        "id": "prop-006",
        "title": "Marina Waterfront 2BR Condo",
        "neighborhood": "Marina",
        "city": "San Francisco",
        "price": 4800,
        "bedrooms": 2,
        "bathrooms": 2.0,
        "sqft": 1250,
        "pet_friendly": True,
        "amenities": ["in-unit laundry", "garage parking", "balcony", "dishwasher", "wine cooler"],
        "description": "Stunning 2BR/2BA condo with Golden Gate Bridge glimpses, private balcony, and deeded garage parking.",
        "tour_available": True,
    },
]


def seed_properties():
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    batch = db.batch()

    for prop in PROPERTIES:
        doc_id = prop["id"]
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        batch.set(doc_ref, prop)
        print(f"Queued property: {doc_id} - {prop['title']}")

    batch.commit()
    print(f"Successfully seeded {len(PROPERTIES)} properties into '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    seed_properties()
