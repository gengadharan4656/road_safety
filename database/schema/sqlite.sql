CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT NOT NULL, points INTEGER NOT NULL, safety_score INTEGER NOT NULL, streak_days INTEGER NOT NULL, total_safe_km REAL NOT NULL);
CREATE TABLE preferences (profile_id INTEGER PRIMARY KEY, language TEXT NOT NULL DEFAULT 'en', voice_enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE trips (id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id INTEGER NOT NULL, started_at TEXT NOT NULL, duration_seconds INTEGER NOT NULL, distance_km REAL NOT NULL, average_speed_kmh REAL NOT NULL, safe_events INTEGER NOT NULL, points_earned INTEGER NOT NULL);
