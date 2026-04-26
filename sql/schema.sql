CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    dry_run BOOLEAN NOT NULL DEFAULT FALSE,
    records_in INTEGER NOT NULL DEFAULT 0,
    records_ok INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS quarantine_records (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    source_record_id TEXT,
    raw_payload JSONB NOT NULL,
    error_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS airports (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    ident TEXT NOT NULL,
    iata_code TEXT,
    icao_code TEXT,
    airport_name TEXT NOT NULL,
    municipality TEXT,
    country_code TEXT,
    latitude_deg DOUBLE PRECISION,
    longitude_deg DOUBLE PRECISION,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_record_id)
);

CREATE TABLE IF NOT EXISTS airlines (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    airline_name TEXT NOT NULL,
    iata_code TEXT,
    icao_code TEXT,
    callsign TEXT,
    country_name TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_record_id)
);

CREATE TABLE IF NOT EXISTS routes (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    airline_code TEXT,
    source_airport_code TEXT NOT NULL,
    destination_airport_code TEXT NOT NULL,
    stops INTEGER NOT NULL DEFAULT 0,
    equipment TEXT,
    codeshare BOOLEAN NOT NULL DEFAULT FALSE,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_record_id)
);

CREATE TABLE IF NOT EXISTS flight_states (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    callsign TEXT,
    icao24 TEXT,
    latitude_deg DOUBLE PRECISION,
    longitude_deg DOUBLE PRECISION,
    baro_altitude_m DOUBLE PRECISION,
    velocity_m_s DOUBLE PRECISION,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_record_id, observed_at)
);

CREATE TABLE IF NOT EXISTS flight_offers (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    offer_id TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_at TIMESTAMPTZ NOT NULL,
    total_price DOUBLE PRECISION NOT NULL,
    currency TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_record_id)
);
