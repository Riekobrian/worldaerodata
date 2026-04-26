# Flight Data Pipeline: Schema-First Declarative ETL

> A production-ready, extensible data ingestion platform for aviation data. Demonstrates best practices in data engineering: declarative configuration, idempotent loading, canonical data models, validation, and operational observability.

---

## ✅ What Is This Project?

This is a **data engineering reference implementation** showcasing how to build scalable, maintainable data pipelines that handle real-world complexity:

- **Real Data Sources** - Integrates public aviation datasets (85K+ airports, 6K+ airlines, 67K+ routes)
- **Production Patterns** - Uses patterns you'll see in enterprise data platforms (Stitch, Fivetran, dbt, Dagster)
- **Extensible by Design** - Add new sources with YAML configuration only, zero code changes to pipeline
- **Data Quality First** - Validates all records before DB write, captures failures for investigation
- **Observable** - Run metrics, quarantine tracking, and audit logs baked in
- **Performant** - Ingests 159K records in ~40 seconds using batch writes, not row-by-row SQL

**Who should use this?**
- Data engineers learning pipeline architecture patterns
- Teams building custom data platforms
- Anyone needing to ingest/normalize aviation data
- Interview portfolio project showcasing practical DE skills

---

## 🎯 Why Data Engineers Should Care

### 1. **Declarative Configuration (YAML-Driven)**
Instead of hardcoding data source logic, sources are configured in YAML. Add a new API, CSV, or database table without touching Python code:
```yaml
sources:
  my_new_api:
    connector: custom_api      # Python class to fetch data
    mapper: custom_api_mapper  # Python class to transform
    dataset_url: "https://..."
```

**Why it matters**: Production systems handle dozens of sources. Declarative config = faster onboarding, fewer bugs, clear separation of concerns.

### 2. **Canonical Data Models (Pydantic)**
All records normalized to strongly-typed models before persistence. Every Airport, Airline, Route has a guaranteed schema:
```python
class AirportCanonical(BaseModel):
    source: str
    source_record_id: str        # For idempotency
    airport_name: str
    country_code: str
    latitude_deg: Optional[float]
    # ... validation rules, defaults, type hints
```

**Why it matters**: Downstream teams (analytics, ML) trust the schema. Type hints catch bugs early.

### 3. **Idempotent Upserts (No Duplicate Data)**
PostgreSQL UNIQUE constraint on (source, source_record_id) ensures safe re-runs:
```python
# Can run this 100 times - result is identical
python pipelines/run_ingestion.py --source all
```

**Why it matters**: Data pipelines fail mid-run. You need to re-run safely without creating duplicates or corrupting existing records.

### 4. **Quarantine Pattern (Observability)**
Records that fail validation aren't silently dropped. They go to `quarantine_records` table:
```
source_name: openflights_airlines
source_record_id: 42
error_reason: "Missing required field: airline_name"
created_at: 2024-01-15 10:30:00
```

**Why it matters**: Failed records are a signal. Something changed in the source format, or validation rules are too strict. This data is gold for improving pipelines.

### 5. **Connector/Mapper Abstraction**
- **Connector**: Fetches raw data (HTTP API, CSV file, database query)
- **Mapper**: Transforms raw → canonical model
- **Validator**: Pydantic checks type safety and business rules
- **Persistence**: Batch upserts to database

This separation means:
- Test mappers without hitting APIs
- Reuse mappers across different orchestration frameworks
- Swap connectors (CSV → API → Kafka) without changing mapper code

### 6. **Run Tracking & Metrics**
Every pipeline execution is logged with success/failure trends:
```sql
SELECT source_name, status, records_in, records_ok, finished_at
FROM pipeline_runs
ORDER BY finished_at DESC
LIMIT 10;
```

**Why it matters**: In production, you need SLAs. This data tracks them.

---

## 🏗️ Architecture & Data Engineering Patterns

### Source Abstraction (Connector Pattern)
```python
# Sources define themselves in YAML
sources:
  ourairports:
    connector: ourairports        # Connector class reference
    mapper: ourairports_airport   # Mapper class reference
    dataset_url: "..."            # Source-specific config
```

Each connector handles the specific details of fetching from its source (CSV HTTP, JSON API, file, etc.), returning raw records. The pipeline handles everything else uniformly.

### Data Transformation (Mapper Pattern)
Mappers transform heterogeneous source formats into canonical models:
```python
# Raw CSV row → FlightPosition or Airport or Airline
mapper.map(raw_row) → AirportCanonical
```

This separation ensures:
- Mappers are testable and reusable
- Mapping logic is isolated from connectivity
- Easy to add fallback/LLM extraction for malformed records

### Canonical Models (Pydantic)
All records validated against strongly-typed Pydantic models before DB write:
```python
class AirportCanonical(BaseModel):
    source: str
    source_record_id: str        # For idempotency
    airport_name: str
    country_code: str
    latitude_deg: Optional[float]
    # ... validation rules, defaults, etc.
```

### Idempotent Upserts
PostgreSQL UNIQUE constraint on (source, source_record_id) prevents duplicates:
```sql
UNIQUE (source, source_record_id)
```

Safe to re-run the entire pipeline at any time. Supports:
- Re-processing failed batches
- Schema migrations (clear + re-ingest)
- Catch-up after downtime

### Quarantine Handling
Records that fail validation aren't skipped—they're captured for investigation:
```
quarantine_records:
  - source_name: openflights_airlines
  - source_record_id: 123
  - error_reason: "Missing required field: airline_name"
```

Later, you can improve mappers/rules and reprocess.

### Batch Upserts vs Row-by-Row
Performance comparison on 159K records:
- **Before**: Row-by-row inserts → ~300+ seconds
- **After**: Batch upserts (2000 rows/batch) → ~40 seconds

Implementation:
```python
# Batch writes
db.bulk_upsert_airports(buffer)  # Single transaction
db.bulk_upsert_airlines(buffer)
db.commit()
```

### Run Tracking
Every pipeline execution is logged:
```sql
pipeline_runs(
  id, source_name, status,
  records_in, records_ok, records_failed,
  started_at, finished_at
)
```

Enables:
- Success/failure trend analysis
- Performance monitoring
- Audit trail

---

## 🔧 Data Tech Stack Explained

### What Each Tool Does

#### **PostgreSQL + SQL** (Persistent Storage)
- Canonical source of truth for normalized aviation data
- ACID transactions ensure data consistency
- UNIQUE constraints enable idempotent upserts
- Full-text search for airport/airline queries

#### **Pydantic v2** (Data Contracts & Validation)
- Type-safe schemas for all entities (Airport, Airline, Route)
- Validates data BEFORE database write (fail-fast principle)
- Auto-generates documentation
- Built-in serialization (JSON, dict)

#### **Python 3.11+** (Orchestration)
- Click/Argparse for CLI commands
- Psycopg (PostgreSQL driver) for database I/O
- Requests for HTTP APIs
- Standard library for CSV/JSONL parsing

#### **YAML** (Declarative Configuration)
- Source registry defines all data sources
- Human-readable, version-controllable
- No code changes needed to add sources

#### **Pytest** (Quality Assurance)
- 14 unit tests covering mappers, validators, connectors
- Tests are documentation of expected behavior
- Fast feedback loop during development

#### **GitHub Actions** (CI/CD)
- Automated lint (Ruff) on every push
- Test suite runs before merge
- Sample ingestion validates end-to-end flow

### Data Sources Explained

| Source | Type | Records | Why It Matters |
|--------|------|---------|----------------|
| **OurAirports** | Public API (CSV/HTTP) | 85,231 airports | Authoritative global airport database |
| **OpenFlights** | Public API (CSV/HTTP) | 6,162 airlines + 67,663 routes | Historical airline/route network |
| **Mock Partner** | Local JSONL file | 2 offers | Example of custom data source integration |
| **OpenSky** | Real-time REST API | Live flight states | Demonstrates streaming/real-time patterns |

### How Data Flows Through The Pipeline

```
INGESTION LAYER
├─ Connector
│  ├─ OurAirports HTTP → CSV rows
│  ├─ OpenFlights HTTP → DAT format
│  ├─ MockSource → JSONL file
│  └─ OpenSky API → JSON objects
│
TRANSFORMATION LAYER
├─ Mapper
│  ├─ CSV row → AirportCanonical
│  ├─ DAT row → AirlineCanonical / RouteCanonical
│  ├─ JSON → FlightOfferCanonical
│  └─ Flight position → FlightPositionCanonical
│
VALIDATION LAYER
├─ Pydantic Models
│  ├─ Type checking (e.g., latitude must be float -90..90)
│  ├─ Required fields (airport_name cannot be NULL)
│  ├─ Business rules (airline_code must be 2 chars)
│  └─ Custom validators
│
PERSISTENCE LAYER
├─ Batch Buffer (accumulate 2000 records)
├─ UPSERT BATCH (single transaction)
│  ├─ INSERT new records
│  ├─ UPDATE existing (by source + source_record_id)
│  └─ Log success/failure
│
OBSERVABILITY LAYER
├─ Pipeline Runs Table
│  ├─ source_name, status, records_in/ok/failed
│  ├─ started_at, finished_at (for SLA tracking)
│  └─ error message if failed
│
├─ Quarantine Table
│  ├─ source_name, source_record_id
│  ├─ error_reason, created_at
│  └─ For investigation and model improvement
```

---

## 📈 Data Metrics & Performance

### Latest Dry-Run Results (159K records)
```
OurAirports:        85,231 in  → 85,231 valid (100.0%)
OpenFlights Airlines: 6,162 in  → 6,158 valid (99.9%)  [4 failed]
OpenFlights Routes:  67,663 in  → 67,662 valid (99.9%)  [1 failed]
Mock Partner:            2 in  → 2 valid (100.0%)
─────────────────────────────────────────────────
TOTAL:             159,058 in  → 159,053 valid (99.997%)
```

**Performance**: 159K records processed in **6.5 seconds** (dry-run)

### Data Quality
- **Quarantine rate**: 0.003% (5 failures out of 159,058)
- **Source pass rates**: 99.9% - 100%
- **Canonical model validation**: 100% (failures caught before DB)

---

## 🚀 How to Use This Project

### For Data Engineers & Pipeline Builders

This project serves as a **reference implementation** for building scalable data ingestion pipelines. Use it to learn patterns and adapt them to your own data scenarios.

#### Quick Start: Process All Sources
```bash
# Install (one-time)
pip install -e ".[dev]"

# Initialize database (first time only)
python pipelines/run_ingestion.py --init-db

# Validate data without writing to DB (safe for exploring)
python pipelines/run_ingestion.py --source all --dry-run

# Run full ingestion pipeline with DB persistence
python pipelines/run_ingestion.py --source all
```

#### Single Source Ingestion
```bash
# Process only OurAirports data
python pipelines/run_ingestion.py --source ourairports

# Process only OpenFlights airlines and routes
python pipelines/run_ingestion.py --source openflights_airlines
python pipelines/run_ingestion.py --source openflights_routes
```

#### Performance Tuning
```bash
# Increase batch size for faster writes (trade memory for speed)
python pipelines/run_ingestion.py --source all --batch-size 5000

# Enable debug logging to observe data transformations
python pipelines/run_ingestion.py --source all --log-level DEBUG

# Progress updates every 10K records
python pipelines/run_ingestion.py --source all --log-every 10000
```

#### Data Quality & Monitoring
```bash
# Check quarantine records (failed validations)
python -c "
from utils.db import get_db_connection
import psycopg
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('SELECT source_name, error_reason, COUNT(*) FROM quarantine_records GROUP BY source_name, error_reason')
    for row in cur.fetchall():
        print(f'{row[0]}: {row[1]} ({row[2]} failures)')
conn.close()
"

# View pipeline execution history
python -c "
from utils.db import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('SELECT source_name, status, records_in, records_ok, finished_at FROM pipeline_runs ORDER BY finished_at DESC LIMIT 10')
    for row in cur.fetchall():
        print(f'{row[0]:25s} | {row[1]:6s} | In: {row[2]:6d} | Valid: {row[3]:6d} | {row[4]}')
conn.close()
"
```

### For Data Analysts & Business Users

Use the interactive explorer to discover flights, airports, and routes:

```bash
# Launch interactive data explorer (default - opens menu)
python explorers/tourist_explorer.py

# Run non-interactive demo (automated queries showing data capabilities)
python explorers/tourist_explorer.py --demo
```

**Explorer Features:**
- 🏢 **Airport Explorer** - Find airports by country, city, or code
- 🛩️ **Route Finder** - Discover flight routes from any airport
- 📍 **Nearest Airport** - Find airports near coordinates (e.g., landmarks)
- 🗺️ **Trip Planner** - Plan multi-country routes
- ✈️ **Airline Search** - Browse airlines and their networks
- 💰 **Flight Offers** - Search available flight prices
- 🤝 **Common Destinations** - Find airports reachable from multiple cities
- 🛰️ **Live Flights** - Stream real-time flight data from OpenSky

**Example Queries:**
```python
# Find all airports in France
from explorers.tourist_explorer import get_airports_by_country
airports = get_airports_by_country("FR", limit=50)

# Get nearest airports to Paris (lat=48.8584, lon=2.2945)
from explorers.tourist_explorer import get_nearest_airports
nearby = get_nearest_airports(48.8584, 2.2945, limit=5)

# Find destinations reachable from both JFK and LAX
from explorers.tourist_explorer import find_common_destinations
common = find_common_destinations(["JFK", "LAX"])

# Search for airlines
from explorers.tourist_explorer import search_airlines
airlines = search_airlines("Delta", limit=10)
```

---

## 📁 Project Structure (Data Engineering Layout)

```
flight_pipeline/                  # Root package
│
├── connectors/                    # DATA EXTRACTION LAYER
│   ├── base.py                   # Abstract base class defining connector interface
│   ├── ourairports.py            # CSV over HTTP connector (85K airports)
│   ├── openflights.py            # DAT format CSV connector (airlines, routes)
│   ├── opensky.py                # REST API connector with rate limiting (live flights)
│   └── mocksource.py             # Local JSONL file connector (demo data)
│   
│   ➜ Why separate connectors?
│     - Each source has different fetch logic (HTTP, file I/O, API pagination)
│     - Testable independently (mock responses)
│     - Reusable across multiple pipelines
│
├── mappers/                       # DATA TRANSFORMATION LAYER
│   ├── base.py                   # Abstract mapper interface
│   ├── ourairports.py            # CSV row → AirportCanonical
│   ├── openflights.py            # DAT row → AirlineCanonical / RouteCanonical
│   ├── opensky.py                # JSON state → FlightPositionCanonical
│   └── mocksource.py             # JSONL → FlightOfferCanonical
│   
│   ➜ Why separate mappers?
│     - Heterogeneous source formats (CSV, JSON, DAT)
│     - Each has different field names, data types, edge cases
│     - Mapper logic is data transformation only (no IO, no validation)
│     - Easy to test with sample data
│
├── models/                        # DATA CONTRACTS (Pydantic)
│   ├── canonical.py              # AirportCanonical, AirlineCanonical, RouteCanonical, FlightOfferCanonical
│   └── flight_position.py        # FlightPositionCanonical (OpenSky real-time)
│   
│   ➜ Canonical models define:
│     - Required vs optional fields
│     - Type constraints (e.g., country_code: str with len=2)
│     - Default values
│     - Custom validators (e.g., lat must be -90..90)
│     - Used for validation BEFORE persistence
│
├── pipelines/                     # ETL ORCHESTRATION
│   └── run_ingestion.py          # Main orchestration engine
│       ├─ Parse command-line args (--source, --dry-run, --batch-size)
│       ├─ Load source registry from YAML
│       ├─ For each source:
│       │  ├─ Instantiate connector
│       │  ├─ Fetch raw records
│       │  ├─ Instantiate mapper
│       │  ├─ Transform to canonical
│       │  ├─ Validate with Pydantic
│       │  ├─ Buffer valid records
│       │  ├─ Quarantine failures
│       │  ├─ Batch upsert when buffer full
│       │  └─ Log metrics
│       └─ Return summary (in/ok/failed counts)
│
├── utils/                         # SUPPORT UTILITIES
│   ├── db.py                      # Database connection pooling, bulk_upsert functions
│   ├── env.py                     # Environment variable loading (secrets mgmt)
│   └── generate_dashboard.py      # Query and visualize run metrics
│
├── sql/                           # SCHEMA DEFINITIONS
│   └── schema.sql                 # CREATE TABLE statements:
│       ├─ airports (normalized aviation data)
│       ├─ airlines
│       ├─ routes
│       ├─ flight_offers
│       ├─ flight_positions
│       ├─ pipeline_runs (execution metrics)
│       └─ quarantine_records (failed validations)
│
├── registry/                      # CONFIGURATION
│   └── sources.yaml              # Declarative source registry
│       Example:
│       sources:
│         ourairports:
│           connector: ourairports
│           mapper: ourairports_airport
│           dataset_url: "https://..."
│
├── tests/                         # AUTOMATED QUALITY ASSURANCE
│   ├── test_mappers.py           # 4 tests - mapper transformations
│   ├── test_validation.py        # 8 tests - Pydantic model validation
│   └── test_opensky.py           # 2 tests - API connector + mapper
│   
│   ➜ Test coverage ensures:
│     - Edge cases (empty fields, malformed data)
│     - Valid data passes validation
│     - Invalid data fails with clear errors
│     - Transformations are deterministic
│
├── explorers/                     # DATA EXPLORATION (OPTIONAL)
│   └── tourist_explorer.py       # Interactive data queries
│       ├─ run(interactive_menu()) for interactive mode
│       ├─ run(demo()) for non-interactive demo
│       └─ Functions for: airports by country, routes, nearest airport, etc.
│
├── samples/                       # TEST DATA
│   └── mock_partner_offers.jsonl # Example JSONL for testing custom source
│
├── .github/workflows/             # CI/CD
│   └── ci.yml                    # GitHub Actions:
│       ├─ Lint: ruff check flight_pipeline/
│       ├─ Test: pytest tests/ -v
│       └─ Ingest: python pipelines/run_ingestion.py --source all --dry-run
│
├── pyproject.toml                # Package metadata & dependencies
│   └─ Declares: pytest, pydantic, psycopg, requests, ruff, click
│
├── .env.example                  # Template for secrets
│   └─ FLIGHT_PIPELINE_DB_DSN (PostgreSQL connection string)
│
├── .gitignore                    # What NOT to commit
│   ├─ Virtual envs (declaflights/)
│   ├─ Secrets (.env)
│   ├─ Build artifacts (__pycache__, *.egg-info)
│   └─ Logs, cache, IDE config
│
└── README.md                      # This file
```

**Design Principles Embedded:**
- **Separation of Concerns**: Connectors ≠ Mappers ≠ Validators ≠ Persistence
- **Testability**: Each layer testable independently
- **Extensibility**: Add sources by editing YAML + creating mapper (no core changes)
- **Observability**: Every execution logged with success/failure metrics
- **Safety**: Idempotent upserts + validation before DB write

---

## 🔄 Data Flow (End-to-End)

```
1. SOURCE REGISTRY (sources.yaml)
   └─ Defines what to load, how to load it
   
2. CONNECTOR (connectors/*.py)
   └─ Fetches raw data (CSV rows, JSON objects, etc.)
   
3. MAPPER (mappers/*.py)
   └─ Transforms raw → FlightPosition, Airport, Airline, Route
   
4. PYDANTIC VALIDATION (models/canonical.py)
   └─ Type check, required fields, business rules
   └─ If fails → quarantine_records
   
5. BATCH BUFFER
   └─ Accumulate valid records
   
6. UPSERT BATCH (utils/db.py)
   └─ Insert/update using (source, source_record_id) key
   └─ Single transaction per batch
   
7. PIPELINE METRICS (pipeline_runs table)
   └─ Log: source_name, status, records_in/ok/failed, timestamps
   
8. DASHBOARD (utils/generate_dashboard.py)
   └─ Visualize trends and run success/failure rates
```

---

## 🧪 Testing & Quality

### Test Suite (14 tests)
```bash
pytest tests/ -v
# test_mappers.py (4)      - Each mapper transforms correctly
# test_validation.py (8)   - Valid/invalid records caught
# test_opensky.py (2)      - API connector + mapper work
```

### CI Pipeline (GitHub Actions)
```yaml
lint   → ruff check flight_pipeline/    [Non-blocking]
test   → pytest tests/ -v               [Blocking]
ingest → Sample dry-run with all sources [Non-blocking]
```

Runs on: Push, PR, Daily 2 AM UTC

---

## 🔐 Security & Data Protection

### Secrets Management
- `.env` file (gitignored) - Database credentials safe locally
- No hardcoded passwords or API keys in code
- Environment variable loading via `load_dotenv()`

### Data Privacy
- Failed records in quarantine for debugging (not exposed externally)
- Pipeline run logs can be sanitized before sharing

### Validation Safety
- All records validated before DB write
- Malformed inputs captured, not silently dropped
- Full audit trail via pipeline_runs table

---

## 📊 Example Data Queries

Once loaded, you can explore with SQL:

```sql
-- How many airports per country?
SELECT country_code, COUNT(*) 
FROM airports 
GROUP BY country_code 
ORDER BY COUNT(*) DESC;

-- Which airlines fly from JFK?
SELECT DISTINCT a.airline_name
FROM routes r
JOIN airlines a ON r.source = a.source AND r.airline_id = a.source_record_id
WHERE r.origin_airport = 'JFK'
LIMIT 10;

-- Route coverage from Heathrow (LHR)?
SELECT COUNT(DISTINCT destination_airport)
FROM routes
WHERE origin_airport = 'LHR';

-- Failed records in quarantine?
SELECT source_name, error_reason, COUNT(*)
FROM quarantine_records
GROUP BY source_name, error_reason;
```

Or use the interactive explorer:
```bash
python explorers/tourist_explorer.py
```

---

## 🎯 Use Cases & Why This Matters

### 1. **Learning Data Engineering Patterns**
This project is a working implementation of patterns you'd encounter in:
- **Stitch** (cloud ETL platform)
- **Fivetran** (data integration)
- **dbt** (data transformation)
- **Dataflow/Apache Beam** (distributed batch processing)
- **Enterprise data warehouses**

**What you learn:**
- ✅ Schema-first design (models before code)
- ✅ Declarative configuration (YAML-driven sources)
- ✅ Connector abstraction (swap APIs/files/DBs easily)
- ✅ Canonical data modeling (enforce data contracts)
- ✅ Idempotent ingestion (safe re-runs, no duplicates)
- ✅ Batch processing (performance optimization)
- ✅ Error handling (quarantine pattern)
- ✅ Observability (run tracking, metrics logging)
- ✅ Testing strategies (mapper/validator unit tests)
- ✅ CI/CD for data (GitHub Actions integration)

### 2. **Building Production Pipelines**
This architecture scales:
- **Extensible**: Add new sources with YAML config only
- **Maintainable**: Mappers, validators, connectors separated
- **Safe**: Validation before DB write, idempotent upserts
- **Observable**: Know what succeeded, what failed, why
- **Performant**: Batch writes instead of row-by-row (7.5x speedup)
- **Testable**: Each layer tested independently

**Real-world example**: A company ingests data from 50+ sources (APIs, databases, files). Instead of 50 custom pipelines, they use this architecture:
- Connector library handles HTTP/SQL/S3
- Mappers normalize heterogeneous formats
- Canonical models enforce consistency
- Batch upserts scale to millions of records
- Quarantine table alerts on data quality issues

### 3. **Aviation Data Analytics**
This project provides ready-to-query data:
- **85K+ airports globally** with IATA codes, coordinates, countries
- **6K+ airlines** with metadata and status (active/inactive)
- **67K+ routes** with origin, destination, airline, stops, equipment
- **Flight prices** from sample partner data
- **Real-time flights** via OpenSky (optional, requires API credentials)

**Analytics use cases:**
- Route density (busiest airports/airlines)
- Coverage analysis (which countries have airports?)
- Network effects (airlines' reach by country)
- Travel planning (shortest path, cheapest routes)
- Real-time tracking (live flight position)

### 4. **Interview & Portfolio Project**
Demonstrates:
- **Architecture thinking**: Why separate connectors/mappers/validators?
- **Data engineering depth**: Idempotency, canonical models, batch processing
- **Production readiness**: Testing, logging, error handling, CI/CD
- **Communication**: Clear code, documentation, patterns
- **Real-world scope**: Handles 159K+ records, multiple sources, validation failures

**Interview talking points:**
- "I designed this pipeline to be schema-first. Sources are configured in YAML, and data passes through standardized mappers before validation."
- "I optimized batch writes to cut runtime from 300s to 40s for 159K records."
- "Failed records go to quarantine, not silently dropped. This lets us investigate data quality issues."
- "Every run is logged to pipeline_runs table. We track what succeeded, what failed, and why."

### 5. **Starting Point for Your Own Platform**
Fork/adapt this for:
- **E-commerce**: Ingest product catalogs from multiple suppliers
- **Finance**: Load ticker data from different APIs, normalize to common schema
- **Healthcare**: Integrate patient records from multiple EMR systems
- **IoT**: Collect sensor data from heterogeneous devices
- **Real estate**: Aggregate property listings from multiple sources

The pattern is the same:
1. Fetch from diverse sources (connectors)
2. Transform to canonical schema (mappers)
3. Validate strictly (Pydantic)
4. Load safely (idempotent upserts)
5. Observe everything (run tracking)

---

## 📈 Performance & Scalability

### Measured Performance
| Metric | Value |
|--------|-------|
| Records processed per second | ~25K/sec (dry-run) |
| DB batch insert time (2K rows) | ~50-100ms |
| Full 159K pipeline runtime | ~6.5s (dry-run), ~40s (DB) |
| Memory usage | <200MB for 159K records |

### Scaling Considerations
- **Larger batches** → Faster writes, more memory
- **Parallel sources** → Future enhancement (threading/multiprocessing)
- **Streaming** → Replace batch upserts with Kafka/event streaming
- **Incremental** → Track last-run timestamp, only fetch deltas

---

## 🛠️ Development & Contributing

### Setup
```bash
python -m venv declaflights
.\declaflights\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Add a New Source
1. Create connector in `connectors/newsource.py`
2. Create mapper in `mappers/newsource.py`
3. Add to `registry/sources.yaml`
4. Write tests in `tests/test_newsource.py`
5. Update docs

### Lint & Test
```bash
ruff check flight_pipeline/
pytest tests/ -v
```

---

## 📚 Documentation

- **DEPLOYMENT_GUIDE.md** - Setup & deployment steps
- **DEPLOYMENT_FIXES.md** - Troubleshooting & fixes
- **RESUME_SHOWCASE_REPORT.md** - Portfolio bullets (not in git)
- **IMPLEMENTATION_COMPLETE.md** - What was built

---

## 📜 License & Data Attribution

**Code**: Available for learning and reference  
**Data**:
- **OurAirports** (CC0) - Public domain airport data
- **OpenFlights** (CC-BY-SA) - Airline/route data
- **OpenSky Network** - Real-time flight data (research license)

---

## 🎓 Learning Outcomes

By studying this project, you'll learn:

✅ Declarative ETL design (YAML-driven configuration)  
✅ Data validation patterns (Pydantic + custom rules)  
✅ Connector abstraction (pluggable data sources)  
✅ Canonical modeling (unified data contracts)  
✅ Idempotent loading (safe re-runs)  
✅ Batch processing (performance optimization)  
✅ Error handling (quarantine pattern)  
✅ Testing strategies (mappers, validators, connectors)  
✅ Operational observability (run tracking, metrics)  
✅ CI/CD integration (GitHub Actions)  

---

**Built with Python, PostgreSQL, and a focus on data engineering best practices.**