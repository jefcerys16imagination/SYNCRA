"""
Jalankan sekali: python fix_db.py
Setelah itu hapus file ini.
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.db")
c = sqlite3.connect(DB)

# Lihat struktur lama
info = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='recurring_skips'").fetchone()
print("Struktur lama:", info[0] if info else "tidak ada")

# Recreate dengan UNIQUE constraint yang benar pada date_key
c.executescript("""
    CREATE TABLE IF NOT EXISTS recurring_skips_new (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        recurring_id INTEGER NOT NULL,
        date_key     TEXT NOT NULL DEFAULT '',
        done         INTEGER DEFAULT 0,
        UNIQUE(recurring_id, date_key)
    );
    DROP TABLE IF EXISTS recurring_skips;
    ALTER TABLE recurring_skips_new RENAME TO recurring_skips;
""")
c.commit()

info2 = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='recurring_skips'").fetchone()
print("Struktur baru:", info2[0])
print("\nSelesai! Sekarang jalankan: python app.py")
c.close()
