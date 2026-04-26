"""
Tourist Explorer - Travel data queries for visitors.

Provides utilities to explore airports and routes for trip planning.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psycopg
from utils.env import load_dotenv

DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"


def get_db() -> psycopg.Connection:
    """Get a database connection."""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    import os
    dsn = os.getenv("FLIGHT_PIPELINE_DB_DSN", DEFAULT_DSN)
    return psycopg.connect(dsn)


# =============================================================================
# Airport Explorer
# =============================================================================

def get_airports_by_country(country_code: str, limit: int = 50) -> list[dict]:
    """
    Get all airports in a given country.
    
    Args:
        country_code: ISO 2-letter country code (e.g., "US", "FR", "JP")
        limit: Maximum number of results
    
    Returns:
        List of airport records with name, city, codes, and coordinates
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    airport_name,
                    iata_code,
                    icao_code,
                    municipality,
                    country_code,
                    latitude_deg,
                    longitude_deg
                FROM airports
                WHERE country_code = %s
                ORDER BY municipality, airport_name
                LIMIT %s
            """, (country_code.upper(), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "name": r[0],
                    "iata": r[1],
                    "icao": r[2],
                    "city": r[3],
                    "country": r[4],
                    "lat": r[5],
                    "lon": r[6],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_airports_by_city(city_name: str, limit: int = 20) -> list[dict]:
    """
    Get airports in or near a specific city.
    
    Args:
        city_name: City/municipality name (partial match)
        limit: Maximum number of results
    
    Returns:
        List of matching airports
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    airport_name,
                    iata_code,
                    icao_code,
                    municipality,
                    country_code,
                    latitude_deg,
                    longitude_deg
                FROM airports
                WHERE municipality ILIKE %s
                ORDER BY airport_name
                LIMIT %s
            """, (f"%{city_name}%", limit))
            
            rows = cur.fetchall()
            return [
                {
                    "name": r[0],
                    "iata": r[1],
                    "icao": r[2],
                    "city": r[3],
                    "country": r[4],
                    "lat": r[5],
                    "lon": r[6],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_airport_by_code(iata_code: str) -> Optional[dict]:
    """
    Get a specific airport by IATA code.
    
    Args:
        iata_code: 3-letter IATA airport code (e.g., "JFK", "LHR")
    
    Returns:
        Airport record or None if not found
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    airport_name,
                    iata_code,
                    icao_code,
                    municipality,
                    country_code,
                    latitude_deg,
                    longitude_deg
                FROM airports
                WHERE iata_code = %s
            """, (iata_code.upper(),))
            
            row = cur.fetchone()
            if row:
                return {
                    "name": row[0],
                    "iata": row[1],
                    "icao": row[2],
                    "city": row[3],
                    "country": row[4],
                    "lat": row[5],
                    "lon": row[6],
                }
            return None
    finally:
        conn.close()


def get_countries_with_airports() -> list[dict]:
    """
    Get list of countries that have airports in the database.
    
    Returns:
        List of countries with airport counts
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    country_code,
                    COUNT(*) as airport_count
                FROM airports
                WHERE country_code IS NOT NULL
                GROUP BY country_code
                ORDER BY airport_count DESC
            """)
            
            rows = cur.fetchall()
            return [
                {"country_code": r[0], "airport_count": r[1]}
                for r in rows
            ]
    finally:
        conn.close()


# =============================================================================
# Route Finder
# =============================================================================

def get_routes_from_airport(iata_code: str, limit: int = 100) -> list[dict]:
    """
    Get all routes departing from a specific airport.
    
    Args:
        iata_code: 3-letter IATA airport code
        limit: Maximum number of results
    
    Returns:
        List of routes with destination info
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.source_airport_code,
                    r.destination_airport_code,
                    r.airline_code,
                    r.stops,
                    r.equipment,
                    a.airline_name,
                    dest.airport_name as dest_name,
                    dest.municipality as dest_city,
                    dest.country_code as dest_country
                FROM routes r
                LEFT JOIN airlines a ON r.airline_code = a.iata_code
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE r.source_airport_code = %s
                ORDER BY r.destination_airport_code
                LIMIT %s
            """, (iata_code.upper(), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "from": r[0],
                    "to": r[1],
                    "airline_code": r[2],
                    "airline": r[5],
                    "stops": r[3],
                    "equipment": r[4],
                    "dest_name": r[6],
                    "dest_city": r[7],
                    "dest_country": r[8],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_routes_to_country(country_code: str, limit: int = 100) -> list[dict]:
    """
    Get all routes entering a specific country.
    
    Args:
        country_code: ISO 2-letter country code
        limit: Maximum number of results
    
    Returns:
        List of routes with origin info
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.source_airport_code,
                    r.destination_airport_code,
                    r.airline_code,
                    r.stops,
                    r.equipment,
                    a.airline_name,
                    orig.airport_name as orig_name,
                    orig.municipality as orig_city,
                    orig.country_code as orig_country
                FROM routes r
                LEFT JOIN airlines a ON r.airline_code = a.iata_code
                JOIN airports orig ON r.source_airport_code = orig.iata_code
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE dest.country_code = %s
                ORDER BY r.source_airport_code
                LIMIT %s
            """, (country_code.upper(), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "from": r[0],
                    "to": r[1],
                    "airline_code": r[2],
                    "airline": r[5],
                    "stops": r[3],
                    "equipment": r[4],
                    "orig_name": r[6],
                    "orig_city": r[7],
                    "orig_country": r[8],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_connectivity_from_airport(iata_code: str) -> dict:
    """
    Get comprehensive connectivity info for an airport.
    
    Args:
        iata_code: 3-letter IATA airport code
    
    Returns:
        Summary of destinations, countries, and airlines served
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Get unique destinations
            cur.execute("""
                SELECT COUNT(DISTINCT destination_airport_code), 
                       COUNT(DISTINCT dest.country_code),
                       COUNT(DISTINCT r.airline_code)
                FROM routes r
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE r.source_airport_code = %s
            """, (iata_code.upper(),))
            
            row = cur.fetchone()
            dest_count = row[0] or 0
            country_count = row[1] or 0
            airline_count = row[2] or 0
            
            # Get top destinations
            cur.execute("""
                SELECT r.destination_airport_code, 
                       dest.airport_name,
                       dest.municipality,
                       dest.country_code,
                       COUNT(*) as route_count
                FROM routes r
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE r.source_airport_code = %s
                GROUP BY r.destination_airport_code, dest.airport_name, 
                         dest.municipality, dest.country_code
                ORDER BY route_count DESC
                LIMIT 10
            """, (iata_code.upper(),))
            
            top_dests = [
                {
                    "iata": r[0],
                    "name": r[1],
                    "city": r[2],
                    "country": r[3],
                    "routes": r[4],
                }
                for r in cur.fetchall()
            ]
            
            return {
                "airport": iata_code.upper(),
                "destinations": dest_count,
                "countries": country_count,
                "airlines": airline_count,
                "top_destinations": top_dests,
            }
    finally:
        conn.close()


# =============================================================================
# Nearest Airport Finder
# =============================================================================

def get_nearest_airports(lat: float, lon: float, limit: int = 10) -> list[dict]:
    """
    Find nearest airports to a given coordinate using Haversine formula.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        limit: Number of results to return
    
    Returns:
        List of airports sorted by distance, with distance in km
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Use Haversine formula to calculate distance
            cur.execute("""
                SELECT 
                    airport_name,
                    iata_code,
                    icao_code,
                    municipality,
                    country_code,
                    latitude_deg,
                    longitude_deg,
                    (
                        6371 * acos(
                            cos(radians(%s)) * cos(radians(latitude_deg)) *
                            cos(radians(longitude_deg) - radians(%s)) +
                            sin(radians(%s)) * sin(radians(latitude_deg))
                        )
                    ) AS distance_km
                FROM airports
                WHERE latitude_deg IS NOT NULL 
                  AND longitude_deg IS NOT NULL
                  AND iata_code IS NOT NULL
                ORDER BY distance_km
                LIMIT %s
            """, (lat, lon, lat, limit))
            
            rows = cur.fetchall()
            return [
                {
                    "name": r[0],
                    "iata": r[1],
                    "icao": r[2],
                    "city": r[3],
                    "country": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "distance_km": round(r[7], 1) if r[7] else None,
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_nearest_airport(lat: float, lon: float) -> Optional[dict]:
    """
    Find the single nearest airport to a coordinate.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Nearest airport with distance
    """
    results = get_nearest_airports(lat, lon, limit=1)
    return results[0] if results else None


# =============================================================================
# Multi-City Trip Planner
# =============================================================================

def plan_trip_between_countries(
    origin_country: str, 
    destination_countries: list[str],
    max_stops: int = 2
) -> dict:
    """
    Plan a trip between countries - find routes from origin to multiple destinations.
    
    Args:
        origin_country: ISO country code of departure (e.g., "US")
        destination_countries: List of destination country codes (e.g., ["FR", "GB"])
        max_stops: Maximum number of stops allowed (0 = direct only)
    
    Returns:
        Trip plan with available routes
    """
    conn = get_db()
    try:
        results = {
            "origin": origin_country,
            "destinations": destination_countries,
            "routes_by_country": {},
            "summary": {
                "total_routes": 0,
                "direct_flights": 0,
                "multi_stop_flights": 0,
            }
        }
        
        for dest_country in destination_countries:
            # Get routes from any airport in origin country to any airport in destination
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        r.source_airport_code,
                        r.destination_airport_code,
                        r.airline_code,
                        r.stops,
                        r.equipment,
                        a.airline_name,
                        orig.airport_name as orig_name,
                        orig.municipality as orig_city,
                        orig.country_code as orig_country,
                        dest.airport_name as dest_name,
                        dest.municipality as dest_city,
                        dest.country_code as dest_country
                    FROM routes r
                    LEFT JOIN airlines a ON r.airline_code = a.iata_code
                    JOIN airports orig ON r.source_airport_code = orig.iata_code
                    JOIN airports dest ON r.destination_airport_code = dest.iata_code
                    WHERE orig.country_code = %s
                      AND dest.country_code = %s
                      AND r.stops <= %s
                    ORDER BY r.stops, r.source_airport_code, r.destination_airport_code
                    LIMIT 50
                """, (origin_country.upper(), dest_country.upper(), max_stops))
                
                routes = []
                for r in cur.fetchall():
                    routes.append({
                        "from": r[0],
                        "to": r[1],
                        "airline_code": r[2],
                        "airline": r[5],
                        "stops": r[3],
                        "equipment": r[4],
                        "orig_name": r[6],
                        "orig_city": r[7],
                        "dest_name": r[9],
                        "dest_city": r[10],
                    })
                    
                    results["summary"]["total_routes"] += 1
                    if r[3] == 0:
                        results["summary"]["direct_flights"] += 1
                    else:
                        results["summary"]["multi_stop_flights"] += 1
                
                results["routes_by_country"][dest_country.upper()] = routes
        
        return results
    finally:
        conn.close()


def find_common_destinations(iata_codes: list[str], limit: int = 20) -> list[dict]:
    """
    Find airports reachable from ALL given origin airports.
    Useful for finding meeting points or common destinations.
    
    Args:
        iata_codes: List of origin IATA codes
        limit: Maximum results
    
    Returns:
        Common destinations with route counts
    """
    conn = get_db()
    try:
        placeholders = ",".join(["%s"] * len(iata_codes))
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT 
                    r.destination_airport_code,
                    dest.airport_name,
                    dest.municipality,
                    dest.country_code,
                    COUNT(DISTINCT r.source_airport_code) as origins_count,
                    COUNT(*) as route_count
                FROM routes r
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE r.source_airport_code IN ({placeholders})
                GROUP BY r.destination_airport_code, dest.airport_name, 
                         dest.municipality, dest.country_code
                HAVING COUNT(DISTINCT r.source_airport_code) = %s
                ORDER BY route_count DESC
                LIMIT %s
            """, (*[c.upper() for c in iata_codes], len(iata_codes), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "iata": r[0],
                    "name": r[1],
                    "city": r[2],
                    "country": r[3],
                    "reachable_from": r[4],
                    "route_options": r[5],
                }
                for r in rows
            ]
    finally:
        conn.close()


# =============================================================================
# Flight Offers / Price Search
# =============================================================================

def search_flight_offers(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 50
) -> list[dict]:
    """
    Search flight offers by origin, destination, or max price.
    
    Args:
        origin: Origin IATA code (optional)
        destination: Destination IATA code (optional)
        max_price: Maximum price filter (optional)
        limit: Maximum results
    
    Returns:
        List of flight offers
    """
    conn = get_db()
    try:
        conditions = []
        params = []
        
        if origin:
            conditions.append("origin = %s")
            params.append(origin.upper())
        if destination:
            conditions.append("destination = %s")
            params.append(destination.upper())
        if max_price:
            conditions.append("total_price <= %s")
            params.append(max_price)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT 
                    offer_id,
                    origin,
                    destination,
                    departure_at,
                    total_price,
                    currency,
                    source
                FROM flight_offers
                WHERE {where_clause}
                ORDER BY total_price, departure_at
                LIMIT %s
            """, params)
            
            rows = cur.fetchall()
            return [
                {
                    "offer_id": r[0],
                    "origin": r[1],
                    "destination": r[2],
                    "departure_at": r[3].isoformat() if r[3] else None,
                    "price": r[4],
                    "currency": r[5],
                    "source": r[6],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_cheapest_routes(origin: str, destination: str, limit: int = 10) -> list[dict]:
    """
    Find cheapest flight offers between two airports.
    
    Args:
        origin: Origin IATA code
        destination: Destination IATA code
        limit: Maximum results
    
    Returns:
        Cheapest flight offers
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    offer_id,
                    origin,
                    destination,
                    departure_at,
                    total_price,
                    currency,
                    source
                FROM flight_offers
                WHERE origin = %s AND destination = %s
                ORDER BY total_price
                LIMIT %s
            """, (origin.upper(), destination.upper(), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "offer_id": r[0],
                    "origin": r[1],
                    "destination": r[2],
                    "departure_at": r[3].isoformat() if r[3] else None,
                    "price": r[4],
                    "currency": r[5],
                    "source": r[6],
                }
                for r in rows
            ]
    finally:
        conn.close()


# =============================================================================
# Airline Search
# =============================================================================

def search_airlines(name_or_code: str, limit: int = 20) -> list[dict]:
    """
    Search airlines by name or IATA/ICAO code.
    
    Args:
        name_or_code: Airline name or code (partial match)
        limit: Maximum results
    
    Returns:
        Matching airlines
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    airline_name,
                    iata_code,
                    icao_code,
                    callsign,
                    country_name,
                    active
                FROM airlines
                WHERE airline_name ILIKE %s
                   OR iata_code = %s
                   OR icao_code = %s
                ORDER BY airline_name
                LIMIT %s
            """, (f"%{name_or_code}%", name_or_code.upper(), name_or_code.upper(), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "name": r[0],
                    "iata": r[1],
                    "icao": r[2],
                    "callsign": r[3],
                    "country": r[4],
                    "active": r[5],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_airline_routes(iata_code: str, limit: int = 50) -> list[dict]:
    """
    Get all routes operated by a specific airline.
    
    Args:
        iata_code: Airline IATA code (e.g., "AA", "BA", "AF")
        limit: Maximum results
    
    Returns:
        Routes operated by the airline
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.source_airport_code,
                    r.destination_airport_code,
                    r.stops,
                    r.equipment,
                    orig.airport_name as orig_name,
                    orig.municipality as orig_city,
                    orig.country_code as orig_country,
                    dest.airport_name as dest_name,
                    dest.municipality as dest_city,
                    dest.country_code as dest_country
                FROM routes r
                JOIN airports orig ON r.source_airport_code = orig.iata_code
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE r.airline_code = %s
                ORDER BY r.source_airport_code, r.destination_airport_code
                LIMIT %s
            """, (iata_code.upper(), limit))
            
            rows = cur.fetchall()
            return [
                {
                    "from": r[0],
                    "to": r[1],
                    "stops": r[2],
                    "equipment": r[3],
                    "orig_name": r[4],
                    "orig_city": r[5],
                    "orig_country": r[6],
                    "dest_name": r[7],
                    "dest_city": r[8],
                    "dest_country": r[9],
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_airline_destination_count(iata_code: str) -> dict:
    """
    Get summary of airline's network.
    
    Args:
        iata_code: Airline IATA code
    
    Returns:
        Summary with destinations, countries, and airports served
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Get airline info
            cur.execute("""
                SELECT airline_name, country_name
                FROM airlines
                WHERE iata_code = %s
            """, (iata_code.upper(),))
            airline_row = cur.fetchone()
            
            if not airline_row:
                return {"error": "Airline not found"}
            
            # Get network stats
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT destination_airport_code) as destinations,
                    COUNT(DISTINCT dest.country_code) as countries,
                    COUNT(DISTINCT source_airport_code) as origin_airports,
                    COUNT(*) as total_routes
                FROM routes r
                JOIN airports dest ON r.destination_airport_code = dest.iata_code
                WHERE r.airline_code = %s
            """, (iata_code.upper(),))
            
            stats = cur.fetchone()
            
            return {
                "airline": airline_row[0],
                "country": airline_row[1],
                "destinations": stats[0] or 0,
                "countries": stats[1] or 0,
                "origin_airports": stats[2] or 0,
                "total_routes": stats[3] or 0,
            }
    finally:
        conn.close()


# =============================================================================
# Demo / CLI
# =============================================================================

def demo():
    """Run demo queries to showcase the explorer."""
    print("=" * 60)
    print("🛫 TOURIST EXPLORER DEMO")
    print("=" * 60)
    
    # Show available countries
    print("\n📍 Countries with airports in database:")
    countries = get_countries_with_airports()
    print(f"   Total: {len(countries)} countries")
    for c in countries[:10]:
        print(f"   {c['country_code']}: {c['airport_count']} airports")
    if len(countries) > 10:
        print(f"   ... and {len(countries) - 10} more")
    
    # Airport Explorer demo
    print("\n" + "-" * 60)
    print("🏢 AIRPORT EXPLORER: France (FR)")
    print("-" * 60)
    airports = get_airports_by_country("FR", limit=10)
    for a in airports:
        iata = a['iata'] or 'N/A'
        print(f"   {iata:3s} | {a['name'][:35]:35s} | {a['city'] or 'N/A'}")
    
    # Route Finder demo
    print("\n" + "-" * 60)
    print("🛩️ ROUTE FINDER: From JFK (New York)")
    print("-" * 60)
    routes = get_routes_from_airport("JFK", limit=10)
    for r in routes:
        print(f"   {r['from']} → {r['to']} | {r['airline'] or r['airline_code'] or 'N/A':20s} | {r['dest_city'] or 'N/A'}")
    
    # Connectivity demo
    print("\n" + "-" * 60)
    print("🌐 CONNECTIVITY: LHR (London Heathrow)")
    print("-" * 60)
    conn = get_connectivity_from_airport("LHR")
    print(f"   Destinations: {conn['destinations']}")
    print(f"   Countries:    {conn['countries']}")
    print(f"   Airlines:     {conn['airlines']}")
    print("   Top destinations:")
    for d in conn['top_destinations'][:5]:
        print(f"      {d['iata']} - {d['name'][:25]} ({d['city']}, {d['country']})")
    
    # Nearest Airport demo
    print("\n" + "-" * 60)
    print("📍 NEAREST AIRPORT: Near Eiffel Tower (Paris)")
    print("-" * 60)
    # Paris coordinates: 48.8584, 2.2945
    nearest = get_nearest_airports(48.8584, 2.2945, limit=5)
    for n in nearest:
        print(f"   {n['iata']:3s} | {n['name'][:30]:30s} | {n['city'] or 'N/A':15s} | {n['distance_km']:>6.1f} km")
    
    # Trip Planner demo
    print("\n" + "-" * 60)
    print("🗺️  TRIP PLANNER: US → France & UK")
    print("-" * 60)
    trip = plan_trip_between_countries("US", ["FR", "GB"], max_stops=1)
    print(f"   Total routes: {trip['summary']['total_routes']}")
    print(f"   Direct flights: {trip['summary']['direct_flights']}")
    print(f"   1-stop flights: {trip['summary']['multi_stop_flights']}")
    print("   Sample routes to France:")
    fr_routes = trip['routes_by_country'].get('FR', [])[:5]
    for r in fr_routes:
        stops_str = "direct" if r['stops'] == 0 else f"{r['stops']} stop(s)"
        print(f"      {r['from']} → {r['to']} | {r['airline'] or 'N/A':20s} | {stops_str}")
    
    # Common Destinations demo
    print("\n" + "-" * 60)
    print("🤝 COMMON DESTINATIONS: From JFK & LAX")
    print("-" * 60)
    common = find_common_destinations(["JFK", "LAX"], limit=10)
    print(f"   Destinations reachable from both JFK and LAX:")
    for c in common[:8]:
        print(f"      {c['iata']} - {c['name'][:30]} ({c['city']}, {c['country']}) - {c['route_options']} routes")
    
    # Flight Offers demo
    print("\n" + "-" * 60)
    print("💰 FLIGHT OFFERS: From JFK")
    print("-" * 60)
    offers = search_flight_offers(origin="JFK", limit=10)
    if offers:
        for o in offers[:8]:
            print(f"   {o['origin']} → {o['destination']} | ${o['price']:.2f} {o['currency']} | {o['departure_at'][:10]}")
    else:
        print("   (No flight offers in database - run ingestion with mock source)")
    
    # Airline Search demo
    print("\n" + "-" * 60)
    print("✈️  AIRLINE SEARCH: 'Delta'")
    print("-" * 60)
    airlines = search_airlines("Delta", limit=5)
    for al in airlines:
        status = "✅ active" if al['active'] else "❌ inactive"
        iata = al['iata'] or 'N/A'
        country = al['country'] or 'N/A'
        print(f"   {iata:2s} | {al['name'][:35]:35s} | {country:20s} | {status}")
    
    # Airline Routes demo
    print("\n" + "-" * 60)
    print("🛫 AIRLINE ROUTES: BA (British Airways)")
    print("-" * 60)
    network = get_airline_destination_count("BA")
    if "error" not in network:
        print(f"   Airline: {network['airline']} ({network['country']})")
        print(f"   Destinations: {network['destinations']} airports in {network['countries']} countries")
        print(f"   Total routes: {network['total_routes']}")
    
    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)


# =============================================================================
# Interactive CLI
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def interactive_menu() -> None:
    """Interactive CLI menu for tourist explorer."""
    print("\n" + "🌍" * 20)
    print("   🛫 TOURIST EXPLORER - Interactive Mode")
    print("   Type 'quit' or 'exit' to leave")
    print("🌍" * 20)
    
    while True:
        print("\n" + "-" * 40)
        print("📋 MAIN MENU - Choose a category:")
        print("-" * 40)
        print("  1. 🏢 Airport Explorer")
        print("  2. 🛩️  Route Finder")
        print("  3. 📍 Nearest Airport")
        print("  4. 🗺️  Trip Planner")
        print("  5. ✈️  Airline Search")
        print("  6. 💰 Flight Offers")
        print("  7. 🤝 Common Destinations")
        print("  8. 🛰️  Live Flights (OpenSky)")
        print("  0. ❌ Exit")

        choice = input("\n👉 Enter choice (0-8): ").strip()

        if choice in ("0", "quit", "exit"):
            print("\n👋 Thanks for using Tourist Explorer! Safe travels! ✈️\n")
            break

        if choice == "1":
            airport_explorer_menu()
        elif choice == "2":
            route_finder_menu()
        elif choice == "3":
            nearest_airport_menu()
        elif choice == "4":
            trip_planner_menu()
        elif choice == "5":
            airline_search_menu()
        elif choice == "6":
            flight_offers_menu()
        elif choice == "7":
            common_destinations_menu()
        elif choice == "8":
            live_flights_opensky_menu()
        else:
            print("❌ Invalid choice. Please try again.")
from connectors.opensky import OpenSkyConnector
from mappers.opensky import OpenSkyStateMapper
import os

def live_flights_opensky_menu() -> None:
    print_header("🛰️  LIVE FLIGHTS (OpenSky)")
    print("  Fetch and display live flight positions from OpenSky Network API.")
    print("  (Requires OpenSky credentials set as OPENSKY_CLIENT_ID and OPENSKY_CLIENT_SECRET in .env)")

    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("❌ OpenSky credentials not found in environment. Please set OPENSKY_CLIENT_ID and OPENSKY_CLIENT_SECRET in your .env file.")
        return

    try:
        connector = OpenSkyConnector(client_id, client_secret)
        print("\nFetching live flight data from OpenSky...")
        states = connector.fetch_states()
        print(f"  ✅ Received {len(states)} live flights.")
        if not states:
            print("  (No live flights returned by OpenSky API)")
            return

        print("\nSample flights:")
        for state in states[:10]:
            flight = OpenSkyStateMapper.map(state, source="opensky")
            print(f"   Callsign: {flight.callsign or '-':10s} | Country: {flight.origin_country or '-':15s} | Lat: {flight.latitude or '-':8} | Lon: {flight.longitude or '-':8} | Alt: {flight.baro_altitude or '-':8} | Vel: {flight.velocity or '-':8}")
        print("\n  ... (showing up to 10 flights)")
    except Exception as e:
        print(f"❌ Error fetching OpenSky data: {e}")


def airport_explorer_menu() -> None:
    """Airport Explorer submenu."""
    print_header("🏢 AIRPORT EXPLORER")
    print("  1. Search by country code (e.g., FR, US, JP)")
    print("  2. Search by city name")
    print("  3. Search by IATA code (e.g., JFK, LHR)")
    print("  4. List all countries with airports")
    
    choice = input("\n👉 Enter choice (1-4): ").strip()
    
    if choice == "1":
        code = input("  Country code (2 letters): ").strip().upper()
        if len(code) == 2:
            airports = get_airports_by_country(code, limit=20)
            print(f"\n📍 Found {len(airports)} airports in {code}:")
            for a in airports:
                iata = a['iata'] or 'N/A'
                print(f"   {iata:3s} | {a['name'][:40]} | {a['city'] or 'N/A'}")
        else:
            print("❌ Invalid country code")
    
    elif choice == "2":
        city = input("  City name: ").strip()
        if city:
            airports = get_airports_by_city(city, limit=20)
            print(f"\n📍 Found {len(airports)} airports near '{city}':")
            for a in airports:
                iata = a['iata'] or 'N/A'
                print(f"   {iata:3s} | {a['name'][:40]} | {a['city'] or 'N/A'}")
    
    elif choice == "3":
        code = input("  IATA code (3 letters): ").strip().upper()
        if len(code) == 3:
            airport = get_airport_by_code(code)
            if airport:
                print(f"\n✈️  {airport['name']}")
                print(f"   IATA: {airport['iata']} | ICAO: {airport['icao'] or 'N/A'}")
                print(f"   City: {airport['city'] or 'N/A'}")
                print(f"   Country: {airport['country']}")
                print(f"   Coordinates: {airport['lat']}, {airport['lon']}")
            else:
                print("❌ Airport not found")
        else:
            print("❌ Invalid IATA code")
    
    elif choice == "4":
        countries = get_countries_with_airports()
        print(f"\n📍 {len(countries)} countries with airports:")
        for c in countries[:30]:
            print(f"   {c['country_code']}: {c['airport_count']} airports")
        if len(countries) > 30:
            print(f"   ... and {len(countries) - 30} more")


def route_finder_menu() -> None:
    """Route Finder submenu."""
    print_header("🛩️ ROUTE FINDER")
    print("  1. Routes FROM an airport")
    print("  2. Routes TO a country")
    print("  3. Connectivity summary for an airport")
    
    choice = input("\n👉 Enter choice (1-3): ").strip()
    
    if choice == "1":
        code = input("  Origin IATA code: ").strip().upper()
        if len(code) >= 2:
            routes = get_routes_from_airport(code, limit=20)
            print(f"\n🛫 {len(routes)} routes from {code}:")
            for r in routes:
                print(f"   {r['from']} → {r['to']} | {r['airline'] or 'N/A':20s} | {r['dest_city'] or 'N/A'}")
        else:
            print("❌ Invalid airport code")
    
    elif choice == "2":
        code = input("  Destination country code: ").strip().upper()
        if len(code) == 2:
            routes = get_routes_to_country(code, limit=20)
            print(f"\n🛬 {len(routes)} routes to {code}:")
            for r in routes:
                print(f"   {r['from']} → {r['to']} | {r['airline'] or 'N/A':20s} | {r['orig_city'] or 'N/A'}")
        else:
            print("❌ Invalid country code")
    
    elif choice == "3":
        code = input("  Airport IATA code: ").strip().upper()
        if len(code) >= 2:
            conn = get_connectivity_from_airport(code)
            print(f"\n🌐 Connectivity from {code}:")
            print(f"   Destinations: {conn['destinations']}")
            print(f"   Countries:    {conn['countries']}")
            print(f"   Airlines:     {conn['airlines']}")
            print("   Top destinations:")
            for d in conn['top_destinations'][:5]:
                print(f"      {d['iata']} - {d['name'][:30]} ({d['city']}, {d['country']})")
        else:
            print("❌ Invalid airport code")


def nearest_airport_menu() -> None:
    """Nearest Airport submenu."""
    print_header("📍 NEAREST AIRPORT")
    print("  Enter your coordinates to find nearby airports")
    
    try:
        lat_input = input("  Latitude (e.g., 48.8584): ").strip()
        lon_input = input("  Longitude (e.g., 2.2945): ").strip()
        
        lat = float(lat_input)
        lon = float(lon_input)
        
        airports = get_nearest_airports(lat, lon, limit=10)
        print(f"\n📍 Nearest airports to ({lat}, {lon}):")
        for a in airports:
            iata = a['iata'] or 'N/A'
            print(f"   {iata:3s} | {a['name'][:35]:35s} | {a['city'] or 'N/A':15s} | {a['distance_km']:>6.1f} km")
    except ValueError:
        print("❌ Invalid coordinates. Please enter valid numbers.")


def trip_planner_menu() -> None:
    """Trip Planner submenu."""
    print_header("🗺️ TRIP PLANNER")
    print("  Plan routes between countries")
    
    origin = input("  Origin country code (e.g., US): ").strip().upper()
    dest_input = input("  Destination countries (comma-separated, e.g., FR,GB): ").strip().upper()
    destinations = [d.strip() for d in dest_input.split(",") if d.strip()]
    
    if len(origin) == 2 and destinations:
        trip = plan_trip_between_countries(origin, destinations, max_stops=1)
        print(f"\n🗺️ Trip from {origin} to {destinations}:")
        print(f"   Total routes: {trip['summary']['total_routes']}")
        print(f"   Direct flights: {trip['summary']['direct_flights']}")
        
        for dest in destinations:
            routes = trip['routes_by_country'].get(dest, [])
            print(f"\n   Routes to {dest} ({len(routes)} total):")
            for r in routes[:5]:
                stops_str = "direct" if r['stops'] == 0 else f"{r['stops']} stop(s)"
                print(f"      {r['from']} → {r['to']} | {r['airline'] or 'N/A':20s} | {stops_str}")
    else:
        print("❌ Invalid input. Use 2-letter country codes.")


def airline_search_menu() -> None:
    """Airline Search submenu."""
    print_header("✈️ AIRLINE SEARCH")
    print("  1. Search by name or code")
    print("  2. View airline network")
    
    choice = input("\n👉 Enter choice (1-2): ").strip()
    
    if choice == "1":
        query = input("  Airline name or code: ").strip()
        if query:
            airlines = search_airlines(query, limit=10)
            print(f"\n✈️  Found {len(airlines)} airlines:")
            for al in airlines:
                iata = al['iata'] or 'N/A'
                status = "✅" if al['active'] else "❌"
                print(f"   {iata:2s} | {al['name'][:40]} | {al['country'] or 'N/A'} {status}")
    
    elif choice == "2":
        code = input("  Airline IATA code (e.g., BA, AA, DL): ").strip().upper()
        if len(code) >= 2:
            network = get_airline_destination_count(code)
            if "error" not in network:
                print(f"\n✈️  {network['airline']} ({network['country']})")
                print(f"   Destinations: {network['destinations']} airports")
                print(f"   Countries:    {network['countries']}")
                print(f"   Routes:       {network['total_routes']}")
                
                routes = get_airline_routes(code, limit=10)
                print(f"\n   Sample routes:")
                for r in routes[:10]:
                    print(f"      {r['from']} → {r['to']} | {r['dest_city']}, {r['dest_country']}")
            else:
                print("❌ Airline not found")
        else:
            print("❌ Invalid airline code")


def flight_offers_menu() -> None:
    """Flight Offers submenu."""
    print_header("💰 FLIGHT OFFERS")
    print("  1. Search by origin")
    print("  2. Search by destination")
    print("  3. Search by max price")
    
    origin = input("  Origin IATA (or Enter for any): ").strip().upper()
    dest = input("  Destination IATA (or Enter for any): ").strip().upper()
    price_input = input("  Max price (or Enter for any): ").strip()
    
    max_price = None
    if price_input:
        try:
            max_price = float(price_input)
        except ValueError:
            print("❌ Invalid price")
            return
    
    offers = search_flight_offers(
        origin=origin if origin else None,
        destination=dest if dest else None,
        max_price=max_price,
        limit=20
    )
    
    print(f"\n💰 Found {len(offers)} flight offers:")
    for o in offers:
        print(f"   {o['origin']} → {o['destination']} | ${o['price']:.2f} {o['currency']} | {o['departure_at'][:10]}")


def common_destinations_menu() -> None:
    """Common Destinations submenu."""
    print_header("🤝 COMMON DESTINATIONS")
    print("  Find destinations reachable from multiple airports")
    
    codes_input = input("  IATA codes (comma-separated, e.g., JFK,LAX): ").strip().upper()
    codes = [c.strip() for c in codes_input.split(",") if c.strip()]
    
    if len(codes) >= 2:
        common = find_common_destinations(codes, limit=15)
        print(f"\n🤝 Destinations reachable from ALL {len(codes)} airports:")
        for c in common:
            print(f"   {c['iata']:3s} | {c['name'][:35]:35s} | {c['city'] or 'N/A':15s} | {c['route_options']} routes")
    else:
        print("❌ Please enter at least 2 airport codes")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        interactive_menu()