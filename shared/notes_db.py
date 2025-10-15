"""
Notes Database Manager - SQLite database for lookup dictionaries
Handles initialization and queries for static lookup data like zones, deities, etc.
"""
import sqlite3
import os


class NotesDBManager:
    """Manage the notes.db SQLite database for lookup data"""

    def __init__(self, db_path="notes.db"):
        """Initialize the notes database manager"""
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to the notes database"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.conn

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def table_exists(self, table_name):
        """Check if a table exists in the database"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None

    def get_table_columns(self, table_name):
        """Return set of column names for a table."""
        if not self.table_exists(table_name):
            return set()
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row['name'] for row in cursor.fetchall()}

    def initialize_database(self):
        """Initialize the database with all required tables if they don't exist"""
        from lookup_data import (
            zone_lookup,
            tradeskill_lookup,
            container_lookup,
            race_lookup,
            class_lookup,
            deity_lookup,
            aa_category_lookup,
            aa_type_lookup,
            expansion_lookup,
            spell_effect_lookup,
        )

        conn = self.connect()
        cursor = conn.cursor()

        # Create zone_lookup table if it doesn't exist
        if not self.table_exists('zone_lookup'):
            print("Creating zone_lookup table...")
            cursor.execute("""
                CREATE TABLE zone_lookup (
                    short_name TEXT PRIMARY KEY,
                    id INTEGER,
                    long_name TEXT,
                    era TEXT,
                    notes TEXT
                )
            """)

            # Populate zone_lookup table
            print(f"Populating zone_lookup with {len(zone_lookup)} zones...")
            for short_name, data in zone_lookup.items():
                cursor.execute("""
                    INSERT INTO zone_lookup (short_name, id, long_name, era, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (short_name, data['id'], data['long_name'], data['era'], data.get('notes', '')))

            conn.commit()
            print("zone_lookup table created and populated successfully!")
        else:
            print("zone_lookup table already exists, skipping initialization.")

        # Ensure deity_lookup table has bit_value column and drop deprecated bitmask table
        if self.table_exists('deity_bitmask_lookup'):
            print("Dropping deprecated deity_bitmask_lookup table...")
            cursor.execute("DROP TABLE deity_bitmask_lookup")
            conn.commit()

        if 'bit_value' not in self.get_table_columns('deity_lookup'):
            if self.table_exists('deity_lookup'):
                print("Updating deity_lookup schema to include bit_value...")
                cursor.execute("DROP TABLE deity_lookup")
                conn.commit()

        if not self.table_exists('deity_lookup'):
            print("Creating deity_lookup table...")
            cursor.execute("""
                CREATE TABLE deity_lookup (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    bit_value INTEGER NOT NULL
                )
            """)
            cursor.executemany(
                "INSERT INTO deity_lookup (id, name, bit_value) VALUES (?, ?, ?)",
                [
                    (deity_id, data['name'], data['bit_value'])
                    for deity_id, data in sorted(deity_lookup.items())
                ],
            )
            conn.commit()
            print("deity_lookup table created and populated successfully!")
        else:
            print("deity_lookup table already up-to-date.")

        # Create tradeskill_lookup table if it doesn't exist
        if not self.table_exists('tradeskill_lookup'):
            print("Creating tradeskill_lookup table...")
            cursor.execute("""
                CREATE TABLE tradeskill_lookup (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            cursor.executemany(
                "INSERT INTO tradeskill_lookup (id, name) VALUES (?, ?)",
                [(ts_id, name) for ts_id, name in sorted(tradeskill_lookup.items())]
            )
            conn.commit()
            print("tradeskill_lookup table created and populated successfully!")
        else:
            print("tradeskill_lookup table already exists, skipping initialization.")

        # Create container_lookup table if it doesn't exist
        if not self.table_exists('container_lookup'):
            print("Creating container_lookup table...")
            cursor.execute("""
                CREATE TABLE container_lookup (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            cursor.executemany(
                "INSERT INTO container_lookup (id, name) VALUES (?, ?)",
                [
                    (container_id, name)
                    for container_id, name in sorted(container_lookup.items())
                ]
            )
            conn.commit()
            print("container_lookup table created and populated successfully!")
        else:
            print("container_lookup table already exists, skipping initialization.")

        # Ensure race_lookup schema and drop deprecated table
        if self.table_exists('race_bitmask_lookup'):
            print("Dropping deprecated race_bitmask_lookup table...")
            cursor.execute("DROP TABLE race_bitmask_lookup")
            conn.commit()

        expected_race_columns = {"id", "name", "bit_value", "abbr"}
        if not expected_race_columns.issubset(self.get_table_columns('race_lookup')):
            if self.table_exists('race_lookup'):
                print("Updating race_lookup table schema...")
                cursor.execute("DROP TABLE race_lookup")
                conn.commit()

        if not self.table_exists('race_lookup'):
            print("Creating race_lookup table...")
            cursor.execute("""
                CREATE TABLE race_lookup (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    bit_value INTEGER NOT NULL,
                    abbr TEXT
                )
            """)
            cursor.executemany(
                """
                INSERT INTO race_lookup (id, name, bit_value, abbr)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (race_id, data['name'], data['bit_value'], data.get('abbr'))
                    for race_id, data in sorted(race_lookup.items())
                ],
            )
            conn.commit()
            print("race_lookup table created and populated successfully!")
        else:
            print("race_lookup table already up-to-date.")

        # Ensure class_lookup schema and drop deprecated table
        if self.table_exists('class_bitmask_lookup'):
            print("Dropping deprecated class_bitmask_lookup table...")
            cursor.execute("DROP TABLE class_bitmask_lookup")
            conn.commit()

        expected_class_columns = {"id", "name", "bit_value", "abbr"}
        if not expected_class_columns.issubset(self.get_table_columns('class_lookup')):
            if self.table_exists('class_lookup'):
                print("Updating class_lookup table schema...")
                cursor.execute("DROP TABLE class_lookup")
                conn.commit()

        if not self.table_exists('class_lookup'):
            print("Creating class_lookup table...")
            cursor.execute("""
                CREATE TABLE class_lookup (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    bit_value INTEGER NOT NULL,
                    abbr TEXT
                )
            """)
            cursor.executemany(
                """
                INSERT INTO class_lookup (id, name, bit_value, abbr)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (class_id, data['name'], data['bit_value'], data.get('abbr'))
                    for class_id, data in sorted(class_lookup.items())
                ],
            )
            conn.commit()
            print("class_lookup table created and populated successfully!")
        else:
            print("class_lookup table already up-to-date.")

        # Create aa_category_lookup table if it doesn't exist
        if not self.table_exists('aa_category_lookup'):
            print("Creating aa_category_lookup table...")
            cursor.execute("""
                CREATE TABLE aa_category_lookup (
                    value TEXT PRIMARY KEY,
                    label TEXT NOT NULL
                )
            """)
            cursor.executemany(
                "INSERT INTO aa_category_lookup (value, label) VALUES (?, ?)",
                [(entry['value'], entry['label']) for entry in aa_category_lookup],
            )
            conn.commit()
            print("aa_category_lookup table created and populated successfully!")
        else:
            print("aa_category_lookup table already exists, skipping initialization.")

        # Create aa_type_lookup table if it doesn't exist
        if not self.table_exists('aa_type_lookup'):
            print("Creating aa_type_lookup table...")
            cursor.execute("""
                CREATE TABLE aa_type_lookup (
                    value TEXT PRIMARY KEY,
                    label TEXT NOT NULL
                )
            """)
            cursor.executemany(
                "INSERT INTO aa_type_lookup (value, label) VALUES (?, ?)",
                [(entry['value'], entry['label']) for entry in aa_type_lookup],
            )
            conn.commit()
            print("aa_type_lookup table created and populated successfully!")
        else:
            print("aa_type_lookup table already exists, skipping initialization.")

        # Create expansion_lookup table if it doesn't exist
        if not self.table_exists('expansion_lookup'):
            print("Creating expansion_lookup table...")
            cursor.execute("""
                CREATE TABLE expansion_lookup (
                    value INTEGER PRIMARY KEY,
                    label TEXT NOT NULL
                )
            """)
            cursor.executemany(
                "INSERT INTO expansion_lookup (value, label) VALUES (?, ?)",
                [(entry['value'], entry['label']) for entry in expansion_lookup],
            )
            conn.commit()
            print("expansion_lookup table created and populated successfully!")
        else:
            print("expansion_lookup table already exists, skipping initialization.")

        # Ensure spell_effects_details is the canonical spell effect table
        if self.table_exists('spell_effect_lookup'):
            print("Dropping deprecated spell_effect_lookup table...")
            cursor.execute("DROP TABLE spell_effect_lookup")
            conn.commit()

        if not self.table_exists('spell_effects_details'):
            print("Creating spell_effects_details table...")
            cursor.execute("""
                CREATE TABLE spell_effects_details (
                    id INTEGER PRIMARY KEY,
                    spa_name TEXT,
                    display_name TEXT,
                    description TEXT,
                    base1_description TEXT,
                    base2_description TEXT,
                    max_description TEXT,
                    notes TEXT
                )
            """)
            conn.commit()
        else:
            print("spell_effects_details table already exists, leaving schema unchanged.")

        cursor.execute("SELECT COUNT(1) AS count FROM spell_effects_details")
        row = cursor.fetchone()
        seed_count = row[0] if row else 0
        if seed_count == 0:
            print(f"Seeding spell_effects_details with {len(spell_effect_lookup)} effects...")
            cursor.executemany(
                """
                INSERT INTO spell_effects_details (
                    id, spa_name, display_name, description,
                    base1_description, base2_description, max_description, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (effect_id, '', name, '', '', '', '', '')
                    for effect_id, name in sorted(spell_effect_lookup.items())
                ],
            )
            conn.commit()
            print("spell_effects_details table seeded successfully!")
        else:
            print("spell_effects_details table already populated, skipping seed.")

    def get_zone_by_id(self, zone_id):
        """Get zone information by zone ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM zone_lookup WHERE id = ?
        """, (zone_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_zone_by_short_name(self, short_name):
        """Get zone information by short name"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM zone_lookup WHERE short_name = ?
        """, (short_name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_zones(self):
        """Get all zones"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM zone_lookup ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]

    def get_deity_by_id(self, deity_id):
        """Get deity name by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM deity_lookup WHERE id = ?
        """, (deity_id,))
        row = cursor.fetchone()
        return row['name'] if row else None

    def get_all_deities(self):
        """Get all deities"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deity_lookup ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]

    def get_tradeskill_by_id(self, tradeskill_id):
        """Get tradeskill name by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM tradeskill_lookup WHERE id = ?
        """, (tradeskill_id,))
        row = cursor.fetchone()
        return row['name'] if row else None

    def get_all_tradeskills(self):
        """Get all tradeskills"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM tradeskill_lookup ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]

    def get_container_by_id(self, container_id):
        """Get container name by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM container_lookup WHERE id = ?
        """, (container_id,))
        row = cursor.fetchone()
        return row['name'] if row else None

    def get_all_containers(self):
        """Get all containers"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM container_lookup ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]

    def get_race_bitmasks(self):
        """Get race bitmask lookup data"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, bit_value, abbr
            FROM race_lookup
            ORDER BY bit_value
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_class_bitmasks(self):
        """Get class bitmask lookup data"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, bit_value, abbr
            FROM class_lookup
            ORDER BY bit_value
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_deity_bitmasks(self):
        """Get deity bitmask lookup data"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, bit_value
            FROM deity_lookup
            ORDER BY bit_value
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_aa_categories(self):
        """Get AA category options"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value, label
            FROM aa_category_lookup
            ORDER BY CAST(value AS INTEGER)
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_aa_types(self):
        """Get AA type options"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value, label
            FROM aa_type_lookup
            ORDER BY CAST(value AS INTEGER)
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_expansions(self):
        """Get expansion options"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value, label
            FROM expansion_lookup
            ORDER BY value
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_spell_effect_name(self, effect_id):
        """Get spell effect name by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT display_name FROM spell_effects_details WHERE id = ?
        """, (effect_id,))
        row = cursor.fetchone()
        if row:
            return row['display_name']
        return None

    def get_all_spell_effects(self):
        """Get all spell effects"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, display_name
            FROM spell_effects_details
            ORDER BY id
        """)
        return [
            {'id': row['id'], 'name': row['display_name']}
            for row in cursor.fetchall()
        ]
