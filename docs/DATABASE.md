# Database

The local SQLite database persists only demo data: `profiles`, `trips`, and `preferences`. It is created and seeded at runtime to keep setup simple. The corresponding illustrative schema lives in `database/schema/sqlite.sql`.

Production would use PostgreSQL/PostGIS, encrypted secrets, audited retention controls, per-user authorization, and consent-driven telemetry processing.
