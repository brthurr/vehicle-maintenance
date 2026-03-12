"""
database.py
-----------
SQLite database initialization and schema management for the
Vehicle Maintenance Tracker application.
"""

import sqlite3
import os

# Default database path — can be overridden via environment variable
DB_PATH = os.environ.get("DB_PATH", "maintenance.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Open and return a SQLite connection with row_factory set so
    rows behave like dictionaries.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """
    Create all tables if they do not already exist.

    Schema
    ------
    vehicles          – master list of vehicles
    maintenance_types – catalogue of service types (oil change, etc.)
    maintenance_logs  – individual service records linked to a vehicle
    receipts          – file attachments linked to a maintenance log
    """
    conn = get_connection(db_path)
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                make        TEXT    NOT NULL,
                model       TEXT    NOT NULL,
                year        INTEGER NOT NULL,
                vin         TEXT,
                mileage     INTEGER NOT NULL DEFAULT 0,
                vehicle_type TEXT   NOT NULL DEFAULT 'Car/Truck',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS maintenance_types (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                description TEXT,
                interval_miles  INTEGER,
                interval_months INTEGER
            );

            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id      INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                type_id         INTEGER NOT NULL REFERENCES maintenance_types(id),
                service_date    TEXT    NOT NULL,
                mileage_at_service INTEGER NOT NULL,
                notes           TEXT,
                cost            REAL,
                next_due_miles  INTEGER,
                next_due_date   TEXT,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS receipts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id      INTEGER NOT NULL REFERENCES maintenance_logs(id) ON DELETE CASCADE,
                filename    TEXT    NOT NULL,
                stored_name TEXT    NOT NULL,
                uploaded_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
    conn.close()


def seed_maintenance_types(db_path: str = DB_PATH) -> None:
    """
    Insert default maintenance type records if the table is empty.
    Covers common service intervals for all vehicle types.
    """
    defaults = [
        ("Oil Change",             "Engine oil and filter replacement",      5000,  6),
        ("Tire Rotation",          "Rotate tires to even wear",              7500,  6),
        ("Air Filter",             "Engine air filter replacement",          15000, 12),
        ("Cabin Air Filter",       "HVAC cabin filter replacement",          15000, 12),
        ("Brake Inspection",       "Inspect pads, rotors, and fluid",        20000, 12),
        ("Coolant Flush",          "Replace engine coolant",                 30000, 24),
        ("Transmission Fluid",     "Replace transmission fluid",             30000, 24),
        ("Spark Plugs",            "Replace spark plugs",                    30000, 24),
        ("Fuel Filter",            "Replace fuel filter",                    20000, 24),
        ("Battery Check",          "Test and inspect battery",               None,  12),
        ("Tire Replacement",       "Replace one or more tires",              None,  None),
        ("Chain/Belt Service",     "Inspect or replace drive chain/belt",    10000, 12),
        ("Differential Fluid",     "Replace front/rear differential fluid",  30000, 24),
        ("Transfer Case Fluid",    "Replace transfer case fluid",            30000, 24),
        ("Power Steering Fluid",   "Inspect/replace power steering fluid",   50000, 24),
        ("Brake Fluid",            "Flush and replace brake fluid",          20000, 24),
        ("General Inspection",     "Full vehicle walk-around inspection",    None,  12),
    ]

    conn = get_connection(db_path)
    with conn:
        for name, desc, miles, months in defaults:
            conn.execute(
                """INSERT OR IGNORE INTO maintenance_types
                   (name, description, interval_miles, interval_months)
                   VALUES (?, ?, ?, ?)""",
                (name, desc, miles, months),
            )
    conn.close()
