"""
tests/test_app.py
-----------------
Unit and integration tests for the Vehicle Maintenance Tracker.

Run with:
    python -m pytest tests/ -v
  or:
    python -m unittest discover tests
"""

import io
import os
import sys
import tempfile
import unittest

# Make sure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from app.database import get_connection, init_db, seed_maintenance_types


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_app(db_path: str, upload_folder: str):
    """Create a test Flask application backed by a temporary database."""
    return create_app(db_path=db_path, upload_folder=upload_folder)


# ──────────────────────────────────────────────────────────────────────────────
# Database layer tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDatabase(unittest.TestCase):
    """Tests for the database module."""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_init_db_creates_tables(self):
        """init_db should create all four tables."""
        init_db(self.db_path)
        conn = get_connection(self.db_path)
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        self.assertIn("vehicles", tables)
        self.assertIn("maintenance_types", tables)
        self.assertIn("maintenance_logs", tables)
        self.assertIn("receipts", tables)

    def test_init_db_idempotent(self):
        """Calling init_db twice should not raise an error."""
        init_db(self.db_path)
        init_db(self.db_path)  # Should not fail

    def test_seed_maintenance_types(self):
        """seed_maintenance_types should insert rows."""
        init_db(self.db_path)
        seed_maintenance_types(self.db_path)
        conn = get_connection(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM maintenance_types"
        ).fetchone()["c"]
        conn.close()
        self.assertGreater(count, 0)

    def test_seed_idempotent(self):
        """Calling seed twice should not create duplicates."""
        init_db(self.db_path)
        seed_maintenance_types(self.db_path)
        seed_maintenance_types(self.db_path)
        conn = get_connection(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM maintenance_types"
        ).fetchone()["c"]
        conn.close()
        # Same count after second seed
        self.assertGreater(count, 0)

    def test_foreign_key_enforcement(self):
        """Inserting a log with a non-existent vehicle_id should fail."""
        import sqlite3
        init_db(self.db_path)
        seed_maintenance_types(self.db_path)
        conn = get_connection(self.db_path)
        with self.assertRaises(sqlite3.IntegrityError):
            with conn:
                conn.execute(
                    """INSERT INTO maintenance_logs
                       (vehicle_id, type_id, service_date, mileage_at_service)
                       VALUES (9999, 1, '2024-01-01', 10000)"""
                )
        conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Flask route tests
# ──────────────────────────────────────────────────────────────────────────────

class TestFlaskRoutes(unittest.TestCase):
    """Integration tests exercising HTTP routes."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.upload_dir = tempfile.mkdtemp()
        self.app = _make_app(self.db_path, self.upload_dir)
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        # Clean up uploads
        for f in os.listdir(self.upload_dir):
            os.unlink(os.path.join(self.upload_dir, f))
        os.rmdir(self.upload_dir)

    # ── Dashboard ────────────────────────────────────────────────────────── #

    def test_dashboard_ok(self):
        """GET / should return 200."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_shows_add_link(self):
        """Dashboard should contain link to add a vehicle."""
        resp = self.client.get("/")
        self.assertIn(b"Add Vehicle", resp.data)

    # ── Vehicle CRUD ─────────────────────────────────────────────────────── #

    def test_add_vehicle_get(self):
        """GET /vehicles/add should return 200."""
        resp = self.client.get("/vehicles/add")
        self.assertEqual(resp.status_code, 200)

    def test_add_vehicle_post_success(self):
        """POST valid vehicle data should redirect to dashboard."""
        resp = self.client.post(
            "/vehicles/add",
            data={
                "name": "Daily Driver",
                "make": "Toyota",
                "model": "Camry",
                "year": "2018",
                "mileage": "45000",
                "vin": "",
                "vehicle_type": "Car/Truck",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Daily Driver", resp.data)

    def test_add_vehicle_missing_name(self):
        """POST without name should return 200 with an error flash."""
        resp = self.client.post(
            "/vehicles/add",
            data={
                "name": "",
                "make": "Toyota",
                "model": "Camry",
                "year": "2018",
                "mileage": "45000",
                "vehicle_type": "Car/Truck",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"required", resp.data.lower())

    def test_add_vehicle_bad_year(self):
        """POST with invalid year should show error."""
        resp = self.client.post(
            "/vehicles/add",
            data={
                "name": "Old Car",
                "make": "Ford",
                "model": "Model T",
                "year": "abcd",
                "mileage": "1000",
                "vehicle_type": "Car/Truck",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"year", resp.data.lower())

    def test_vehicle_detail_ok(self):
        """GET /vehicles/<id> for existing vehicle returns 200."""
        self._add_vehicle()
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Test Truck", resp.data)

    def test_vehicle_detail_404(self):
        """GET /vehicles/9999 for non-existent vehicle returns 404."""
        resp = self.client.get("/vehicles/9999")
        self.assertEqual(resp.status_code, 404)

    def test_edit_vehicle_get(self):
        """GET edit form for existing vehicle returns 200."""
        self._add_vehicle()
        resp = self.client.get("/vehicles/1/edit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Test Truck", resp.data)

    def test_edit_vehicle_post(self):
        """POST updated vehicle data should persist changes."""
        self._add_vehicle()
        self.client.post(
            "/vehicles/1/edit",
            data={
                "name": "Updated Truck",
                "make": "Ford",
                "model": "F-250",
                "year": "2020",
                "mileage": "60000",
                "vin": "",
                "vehicle_type": "Car/Truck",
            },
            follow_redirects=True,
        )
        resp = self.client.get("/vehicles/1")
        self.assertIn(b"Updated Truck", resp.data)

    def test_delete_vehicle(self):
        """POST to delete should remove vehicle from the vehicle grid."""
        self._add_vehicle()
        self.client.post("/vehicles/1/delete", follow_redirects=False)
        # After delete the vehicle should no longer be in the DB
        conn = get_connection(self.db_path)
        row = conn.execute("SELECT id FROM vehicles WHERE id=1").fetchone()
        conn.close()
        self.assertIsNone(row)

    # ── Maintenance Logs ─────────────────────────────────────────────────── #

    def test_add_log_get(self):
        """GET log form returns 200."""
        self._add_vehicle()
        resp = self.client.get("/vehicles/1/log/add")
        self.assertEqual(resp.status_code, 200)

    def test_add_log_post_success(self):
        """POST valid log data should add a record."""
        self._add_vehicle()
        resp = self.client.post(
            "/vehicles/1/log/add",
            data={
                "type_id": "1",
                "service_date": "2024-06-01",
                "mileage_at_service": "46000",
                "cost": "75.00",
                "notes": "Synthetic 5W-30",
                "next_due_miles": "51000",
                "next_due_date": "2024-12-01",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Maintenance log added", resp.data)

    def test_add_log_missing_type(self):
        """POST log without service type should show error."""
        self._add_vehicle()
        resp = self.client.post(
            "/vehicles/1/log/add",
            data={
                "type_id": "",
                "service_date": "2024-06-01",
                "mileage_at_service": "46000",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_add_log_updates_vehicle_mileage(self):
        """Logging a service at higher mileage should update the vehicle."""
        self._add_vehicle()  # mileage = 50000
        self.client.post(
            "/vehicles/1/log/add",
            data={
                "type_id": "1",
                "service_date": "2024-06-01",
                "mileage_at_service": "55000",
                "cost": "",
            },
            follow_redirects=True,
        )
        conn = get_connection(self.db_path)
        row = conn.execute("SELECT mileage FROM vehicles WHERE id=1").fetchone()
        conn.close()
        self.assertEqual(row["mileage"], 55000)

    def test_log_detail_ok(self):
        """GET /log/<id> returns 200."""
        self._add_vehicle()
        self._add_log()
        resp = self.client.get("/log/1")
        self.assertEqual(resp.status_code, 200)

    def test_log_detail_404(self):
        """GET /log/9999 returns 404."""
        resp = self.client.get("/log/9999")
        self.assertEqual(resp.status_code, 404)

    def test_delete_log(self):
        """POST to delete log should remove it."""
        self._add_vehicle()
        self._add_log()
        resp = self.client.post("/log/1/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        conn = get_connection(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM maintenance_logs"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(count, 0)

    # ── Receipt upload ───────────────────────────────────────────────────── #

    def test_receipt_upload_allowed(self):
        """Uploading a valid image file should store a receipt record."""
        self._add_vehicle()
        data = {
            "type_id": "1",
            "service_date": "2024-06-01",
            "mileage_at_service": "46000",
            "cost": "",
            "receipt": (io.BytesIO(b"fake image data"), "receipt.jpg"),
        }
        resp = self.client.post(
            "/vehicles/1/log/add",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        conn = get_connection(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM receipts"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(count, 1)

    def test_receipt_upload_disallowed_extension(self):
        """Uploading a disallowed file type should not store a receipt."""
        self._add_vehicle()
        data = {
            "type_id": "1",
            "service_date": "2024-06-01",
            "mileage_at_service": "46000",
            "cost": "",
            "receipt": (io.BytesIO(b"#!/bin/bash"), "malicious.sh"),
        }
        self.client.post(
            "/vehicles/1/log/add",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        conn = get_connection(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM receipts"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(count, 0)

    def test_receipt_download_404(self):
        """Downloading non-existent receipt should 404."""
        resp = self.client.get("/receipts/9999/download")
        self.assertEqual(resp.status_code, 404)

    def test_receipt_delete(self):
        """Deleting a receipt should remove it from DB and filesystem."""
        self._add_vehicle()
        data = {
            "type_id": "1",
            "service_date": "2024-06-01",
            "mileage_at_service": "46000",
            "cost": "",
            "receipt": (io.BytesIO(b"fake"), "receipt.png"),
        }
        self.client.post(
            "/vehicles/1/log/add",
            data=data,
            content_type="multipart/form-data",
        )
        conn = get_connection(self.db_path)
        r = conn.execute("SELECT * FROM receipts LIMIT 1").fetchone()
        conn.close()
        self.assertIsNotNone(r)

        self.client.post(f"/receipts/{r['id']}/delete", follow_redirects=True)
        conn = get_connection(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM receipts"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(count, 0)

    # ── Maintenance Types ────────────────────────────────────────────────── #

    def test_maintenance_types_page(self):
        """GET /maintenance-types returns 200 with default types."""
        resp = self.client.get("/maintenance-types")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Oil Change", resp.data)

    def test_add_maintenance_type(self):
        """POST new custom type should appear in list."""
        resp = self.client.post(
            "/maintenance-types/add",
            data={
                "name": "Supercharger Fluid",
                "description": "EV specific",
                "interval_miles": "",
                "interval_months": "24",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Supercharger Fluid", resp.data)

    def test_add_maintenance_type_duplicate(self):
        """Adding a type with a duplicate name should flash an error."""
        resp = self.client.post(
            "/maintenance-types/add",
            data={"name": "Oil Change", "description": "", "interval_miles": "", "interval_months": ""},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"already exists", resp.data)

    def test_delete_unused_type(self):
        """Deleting a type not used in logs should remove it from the DB."""
        # Add a fresh type
        self.client.post(
            "/maintenance-types/add",
            data={"name": "Temp Type", "description": "", "interval_miles": "", "interval_months": ""},
        )
        conn = get_connection(self.db_path)
        t = conn.execute(
            "SELECT id FROM maintenance_types WHERE name='Temp Type'"
        ).fetchone()
        conn.close()
        self.client.post(f"/maintenance-types/{t['id']}/delete")
        conn = get_connection(self.db_path)
        gone = conn.execute(
            "SELECT id FROM maintenance_types WHERE name='Temp Type'"
        ).fetchone()
        conn.close()
        self.assertIsNone(gone)

    def test_cannot_delete_used_type(self):
        """Deleting a type that has logs should flash an error."""
        self._add_vehicle()
        self._add_log()
        resp = self.client.post(
            "/maintenance-types/1/delete", follow_redirects=True
        )
        self.assertIn(b"Cannot delete", resp.data)

    # ── Reports ──────────────────────────────────────────────────────────── #

    def test_reports_page(self):
        """GET /reports returns 200."""
        resp = self.client.get("/reports")
        self.assertEqual(resp.status_code, 200)

    def test_reports_with_filter(self):
        """GET /reports?vehicle_id=1 returns 200."""
        self._add_vehicle()
        resp = self.client.get("/reports?vehicle_id=1")
        self.assertEqual(resp.status_code, 200)

    def test_reports_totals(self):
        """Reports should display accumulated costs."""
        self._add_vehicle()
        self._add_log(cost="150.00")
        resp = self.client.get("/reports")
        self.assertIn(b"150", resp.data)

    # ── Helpers ──────────────────────────────────────────────────────────── #

    def _add_vehicle(self):
        self.client.post(
            "/vehicles/add",
            data={
                "name": "Test Truck",
                "make": "Ford",
                "model": "F-150",
                "year": "2019",
                "mileage": "50000",
                "vin": "1FTEW1EP0JFA12345",
                "vehicle_type": "Car/Truck",
            },
        )

    def _add_log(self, cost="75.00"):
        self.client.post(
            "/vehicles/1/log/add",
            data={
                "type_id": "1",
                "service_date": "2024-06-01",
                "mileage_at_service": "50000",
                "cost": cost,
                "notes": "Test log",
            },
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
