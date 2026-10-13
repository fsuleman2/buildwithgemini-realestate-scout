# RealEstate Scout 🏠🔍

> An intelligent apartment finding and real estate assistant powered by **Gemini 3.8 Flash**, the **Agent Development Kit (ADK)**, and **Google Cloud**.

RealEstate Scout helps apartment hunters search, compare, evaluate, and virtually stage rental properties. Grounded in a real Google Cloud Firestore property catalog, it combines real-time criteria filtering, geospatial exploration with Google Maps, move-in affordability calculations, AI-powered virtual staging using Gemini image generation, and rich visual cards via the Agent-to-User Interface (A2UI) specification.

---

## 🌟 What RealEstate Scout Does

RealEstate Scout moves beyond traditional keyword search engines by acting as an end-to-end rental concierge. Through conversational natural language or structured cards, users can:

- **Filter & Discover Listings**: Search available apartments across San Francisco by monthly rent ceiling, bedroom count, specific neighborhoods, and pet friendliness.
- **Inspect Deep Unit Specs**: Pull comprehensive specifications including square footage, bathrooms, amenities lists, building descriptions, and in-person tour availability.
- **Assess Move-In Costs & Affordability**: Calculate upfront cash requirements (first month's rent, security deposit, pet deposit), estimated monthly utility expenses, and evaluate applicant gross income against the standard 3x rent affordability threshold.
- **Explore Neighborhoods & Amenities**: Geocode addresses with the Google Maps Geocoding API and discover nearby points of interest (transit stations, cafes, restaurants, grocery stores, parks, gyms) using the Google Maps Places API (New).
- **Visualize Virtual Staging**: Generate high-fidelity interior design and virtual staging concepts for unfurnished or staged rooms using Vertex AI image generation (`gemini-3.1-flash-lite-image`), hosted directly on Google Cloud Storage.
- **Save Favorites**: Bookmark favorite rental listings with custom user notes in Firestore.
- **Interact via Agent-First UI (A2UI)**: Receive structured response cards featuring rich layouts and inline images rather than plain-text walls of text.

---

## ☁️ Google Cloud Services & Tools Wired Up

The agent's capabilities are backed by real Google Cloud services and Python tools defined in `realestate-scout/app/tools.py` and `realestate-scout/app/agent.py`:

| Service / Capability | Implementation Details | Active Tools / Components |
|---|---|---|
| **Google Cloud Firestore** | NoSQL database hosting the live rental catalog and user bookmarks. | `search_properties`: Filters units by price, beds, neighborhood, pets.<br/>`get_property_details`: Fetches full unit specifications by ID.<br/>`add_property`: Creates new property listings.<br/>`save_favorite_property`: Saves properties and notes to `saved_favorites`. |
| **Vertex AI Image Generation** | Generates photorealistic virtual room stagings and decor styles using `gemini-3.1-flash-lite-image`. | `generate_virtual_staging_image`: Generates interior design concepts grounded in property context and records ADK session artifacts. |
| **Google Cloud Storage (GCS)** | Public cloud storage bucket (`realestate-scout-assets`) for hosting generated media. | Automatically uploads generated staging images directly to Cloud Storage and returns public HTTPS URLs for rendering. |
| **Agent-to-User Interface (A2UI)** | Emits structured JSON surfaces following the A2UI v0.8 Basic Catalog. | `a2ui_callback` in `app/a2ui_utils.py` validates components (`Card`, `Column`, `Row`, `Text`, `Image`) and rewraps payloads for native rendering. |
| **Google Maps Geocoding API** | Converts street addresses into geographic coordinates. | `geocode_address`: Direct REST client converting address strings to latitude/longitude. |
| **Google Maps Places API (New)** | Nearby search using spatial circle restrictions and field masks. | `search_nearby_places`: Finds nearby transit, groceries, gyms, and dining within a radius. |
| **OpenStreetMap Nominatim API** | Boundary and postal code lookup for neighborhoods. | `lookup_neighborhood_map_info`: Retrieves postal codes, bounding boxes, and map links. |
| **Financial Affordability Calculator** | Python computation tool for tenant qualification. | `calculate_move_in_costs`: Calculates upfront cash needs, monthly expenses, and rent-to-income ratios. |

---

## 📋 Planned vs. Implemented Capabilities

To maintain full transparency between the initial design in `project_brief.md` and the actual codebase:

| Feature | Brief Status | Codebase Status | Notes |
|---|---|---|---|
| **Firestore Rental Catalog** | Planned | ✅ **Implemented** | Active in `app/tools.py` with multi-field search and detail lookups. |
| **Cloud Storage Asset Hosting** | Planned | ✅ **Implemented** | Active in `app/tools.py` uploading to `realestate-scout-assets`. |
| **Virtual Staging Image Gen** | Planned | ✅ **Implemented** | Active via Vertex AI `gemini-3.1-flash-lite-image`. |
| **A2UI Rich UI Cards** | Planned | ✅ **Implemented** | Active via `a2ui_callback` and rendered in the web frontend. |
| **Google Maps & Places APIs** | Planned (stretch) | ✅ **Implemented** | Active via `geocode_address` and `search_nearby_places`. |
| **Affordability Calculations** | Planned | ✅ **Implemented** | Implemented as a deterministic Python function tool (`calculate_move_in_costs`). |
| **Agent Platform Code Sandbox** | Planned | ⏳ *Planned, not yet implemented* | Financial calculations currently run via a native Python function tool rather than an isolated Agent Platform code sandbox. |
| **Vertex AI Memory Bank** | Planned | ⏳ *Planned, not yet implemented* | Favorites and notes are saved directly to the Firestore `saved_favorites` collection; cross-session semantic extraction via Vertex AI Memory Bank is not yet wired up. |
| **Lease Document RAG Engine** | Planned (stretch) | ⏳ *Planned, not yet implemented* | Grounded document parsing over PDF lease agreements was identified as an optional stretch goal and is not yet implemented. |

---

## 🏗️ Architecture & Project Structure

```text
BuildWithGemini/
├── frontend/
│   ├── Dockerfile                 # Containerfile for Cloud Run deployment
│   ├── main.py                    # FastAPI proxy communicating via A2A protocol
│   ├── requirements.txt           # Frontend dependencies (fastapi, a2a-sdk, httpx)
│   └── static/
│       └── index.html             # Responsive chat UI with native A2UI mini-renderer
├── project_brief.md               # Initial design brief and tool-coverage checklist
└── realestate-scout/
    ├── agents-cli-manifest.yaml   # Agent manifest configuration (acli 1.4.0, A2A enabled)
    ├── pyproject.toml             # Python project dependencies (google-adk, a2ui, firestore)
    ├── seed_firestore.py          # Seeding script for sample SF rental listings
    ├── app/
    │   ├── agent.py               # Core ADK root_agent definition with Gemini 3.8 Flash
    │   ├── tools.py               # Firestore, Cloud Storage, Maps, and Image Gen tools
    │   ├── a2ui_utils.py          # After-model callback for A2UI schema wrapping & sanitization
    │   ├── fast_api_app.py        # Local FastAPI agent runtime server with A2A routes
    │   └── app_utils/             # Service registry, A2A routes, and adapter utilities
    ├── deployment/                # Terraform deployment configurations
    └── tests/                     # Unit and integration test suites
```

---

## 🚀 Local Setup & Running Instructions

Follow these steps to run RealEstate Scout locally on your development machine.

### Prerequisites

- **Python 3.11+** installed
- **uv** (recommended) or **pip**
- **Google Cloud SDK (`gcloud`)** installed and authenticated:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project <YOUR_GCP_PROJECT_ID>
  ```
- Enabled Google Cloud APIs: Vertex AI, Cloud Storage, Firestore, and Google Maps Platform (Geocoding API & Places API New).

---

### 1. Environment Configuration

In `realestate-scout/`, create a `.env` file based on `.env.example`:

```bash
cd realestate-scout
cp .env.example .env
```

Ensure the following variables are set:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

---

### 2. Install Dependencies & Seed Firestore

From the `realestate-scout` directory:

```bash
# Install dependencies with uv
uv sync

# Seed the Firestore database with sample San Francisco rental properties
uv run python seed_firestore.py
```

---

### 3. Run the Agent Locally

You can run the agent in development mode using `agents-cli`:

```bash
# Launch the local ADK developer environment
agents-cli playground
```

Or run the agent backend directly via uvicorn:

```bash
uv run python -m app.fast_api_app
```

The agent backend will start on port `8000`.

---

### 4. Run the Web Chat Frontend (A2A Proxy)

In a separate terminal, start the FastAPI chat frontend:

```bash
cd frontend
pip install -r requirements.txt

# Specify the agent directory (defaults to 'app')
export AGENT_DIRECTORY="app"

# Start the frontend server
python main.py
```

The frontend proxy will start on port `8080`.

Open your web browser and navigate to `localhost:8080` (or `localhost:8000/dev-ui/?app=app` for the ADK dev UI) to interact with RealEstate Scout!

---

## 🧪 Testing

To run the unit and integration test suites:

```bash
cd realestate-scout
uv run pytest tests/unit tests/integration
```

To run code quality and lint checks:

```bash
agents-cli lint
```
