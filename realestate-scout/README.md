# RealEstate Scout Agent 🏠🔍

> Intelligent apartment finding and real estate assistant powered by **Gemini 3.8 Flash**, the **Agent Development Kit (ADK)**, and **Google Cloud**.

This directory contains the ADK agent implementation for RealEstate Scout.

---

## 🌟 Capabilities & Tools

- **Firestore Search & Details**: `search_properties`, `get_property_details`, `add_property`, and `save_favorite_property` interfacing directly with Google Cloud Firestore collections (`properties` and `saved_favorites`).
- **Virtual Staging & Image Generation**: `generate_virtual_staging_image` using Vertex AI's `gemini-3.1-flash-lite-image`, with automatic upload of generated assets to Google Cloud Storage (`realestate-scout-assets`) and public HTTPS URL serving.
- **Agent-to-User Interface (A2UI)**: Native A2UI v0.8 Basic Catalog integration via `a2ui_callback` in `app/a2ui_utils.py`, emitting structured Cards, Columns, Rows, and Images.
- **Geocoding & Places Discovery**: `geocode_address` via Google Maps Geocoding API and `search_nearby_places` via Google Maps Places API (New).
- **Affordability Analysis**: `calculate_move_in_costs` computing upfront cash requirements, estimated monthly expenses, and rent-to-income affordability ratios.
- **Agent Platform Code Sandbox**: Safe Python code execution in an isolated Vertex AI Agent Engine sandbox using `AgentEngineSandboxCodeExecutor` for complex financial modeling, custom amortizations, and rent-vs-buy data analysis.

---

## 📋 Planned vs. Implemented

- **Firestore Catalog & Favorites**: ✅ Implemented
- **Cloud Storage Asset Hosting**: ✅ Implemented
- **Virtual Staging Image Gen**: ✅ Implemented
- **A2UI Rich UI Surfaces**: ✅ Implemented
- **Google Maps & Places APIs**: ✅ Implemented
- **Affordability Calculator**: ✅ Implemented (as deterministic Python function tool)
- **Agent Platform Code Sandbox**: ✅ Implemented (`AgentEngineSandboxCodeExecutor` backed by Vertex AI Agent Engine Sandbox)
- **Vertex AI Memory Bank**: ⏳ *Planned, not yet implemented* (Favorites and notes persist via Firestore `saved_favorites`)
- **Lease Document RAG Engine**: ⏳ *Planned, not yet implemented*

---

## 🚀 Local Development

### 1. Install Dependencies

```bash
uv sync
```

### 2. Seed Firestore Data

```bash
uv run python seed_firestore.py
```

### 3. Launch Local Playground

```bash
agents-cli playground
```

Or run via uvicorn directly:

```bash
uv run python -m app.fast_api_app
```

### 4. Tests & Quality Checks

```bash
# Run unit and integration tests
uv run pytest tests/unit tests/integration

# Run linting
agents-cli lint
```
