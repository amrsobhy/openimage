"""SQLite-based caching system for API responses."""

import sqlite3
import json
import hashlib
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta


class ImageCache:
    """Cache for image search results using SQLite."""

    def __init__(self, db_path: str = "data/image_cache.db", ttl_days: int = 30):
        """Initialize the cache.

        Args:
            db_path: Path to the SQLite database file
            ttl_days: Time-to-live for cached entries in days (default: 30)
        """
        self.db_path = db_path
        self.ttl_days = ttl_days

        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_cache (
                cache_key TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        ''')

        # Create face detection cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_detection_cache (
                image_url TEXT PRIMARY KEY,
                has_face INTEGER NOT NULL,
                face_count INTEGER NOT NULL,
                detected_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            )
        ''')

        # Create gender classification cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gender_classification_cache (
                image_url TEXT PRIMARY KEY,
                gender TEXT NOT NULL,
                classified_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            )
        ''')

        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_query_entity
            ON image_cache(query, entity_type)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires
            ON image_cache(expires_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_face_expires
            ON face_detection_cache(expires_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_gender_expires
            ON gender_classification_cache(expires_at)
        ''')

        conn.commit()
        conn.close()

    def _generate_cache_key(self, query: str, entity_type: str, source: str) -> str:
        """Generate a unique cache key.

        Args:
            query: Search query
            entity_type: Type of entity
            source: Image source name

        Returns:
            MD5 hash as cache key
        """
        key_string = f"{query.lower()}:{entity_type.lower()}:{source.lower()}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, query: str, entity_type: str, source: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached results if available and not expired.

        Args:
            query: Search query
            entity_type: Type of entity
            source: Image source name

        Returns:
            List of cached results or None if not found/expired
        """
        cache_key = self._generate_cache_key(query, entity_type, source)
        current_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT results, hit_count FROM image_cache
            WHERE cache_key = ? AND expires_at > ?
        ''', (cache_key, current_time))

        row = cursor.fetchone()

        if row:
            results_json, hit_count = row

            # Increment hit count
            cursor.execute('''
                UPDATE image_cache
                SET hit_count = ?
                WHERE cache_key = ?
            ''', (hit_count + 1, cache_key))

            conn.commit()
            conn.close()

            # Deserialize results
            return json.loads(results_json)

        conn.close()
        return None

    def set(self, query: str, entity_type: str, source: str, results: List[Dict[str, Any]]):
        """Cache search results.

        Args:
            query: Search query
            entity_type: Type of entity
            source: Image source name
            results: List of image results to cache
        """
        cache_key = self._generate_cache_key(query, entity_type, source)
        current_time = int(time.time())
        expires_at = current_time + (self.ttl_days * 24 * 60 * 60)

        # Serialize results
        results_json = json.dumps(results)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert or replace cache entry
        cursor.execute('''
            INSERT OR REPLACE INTO image_cache
            (cache_key, query, entity_type, source, results, created_at, expires_at, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        ''', (cache_key, query, entity_type, source, results_json, current_time, expires_at))

        conn.commit()
        conn.close()

    def clear_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        current_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM image_cache WHERE expires_at <= ?', (current_time,))
        image_deleted_count = cursor.rowcount

        cursor.execute('DELETE FROM face_detection_cache WHERE expires_at <= ?', (current_time,))
        face_deleted_count = cursor.rowcount

        cursor.execute('DELETE FROM gender_classification_cache WHERE expires_at <= ?', (current_time,))
        gender_deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return image_deleted_count + face_deleted_count + gender_deleted_count

    def clear_all(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries removed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM image_cache')
        image_deleted_count = cursor.rowcount

        cursor.execute('DELETE FROM face_detection_cache')
        face_deleted_count = cursor.rowcount

        cursor.execute('DELETE FROM gender_classification_cache')
        gender_deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return image_deleted_count + face_deleted_count + gender_deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total entries
        cursor.execute('SELECT COUNT(*) FROM image_cache')
        total_entries = cursor.fetchone()[0]

        # Active (non-expired) entries
        cursor.execute('SELECT COUNT(*) FROM image_cache WHERE expires_at > ?', (current_time,))
        active_entries = cursor.fetchone()[0]

        # Expired entries
        expired_entries = total_entries - active_entries

        # Total hit count
        cursor.execute('SELECT SUM(hit_count) FROM image_cache WHERE expires_at > ?', (current_time,))
        total_hits = cursor.fetchone()[0] or 0

        # Most popular queries
        cursor.execute('''
            SELECT query, entity_type, source, hit_count
            FROM image_cache
            WHERE expires_at > ?
            ORDER BY hit_count DESC
            LIMIT 10
        ''', (current_time,))
        popular_queries = [
            {
                'query': row[0],
                'entity_type': row[1],
                'source': row[2],
                'hits': row[3]
            }
            for row in cursor.fetchall()
        ]

        # Face detection cache stats
        cursor.execute('SELECT COUNT(*) FROM face_detection_cache WHERE expires_at > ?', (current_time,))
        face_cache_entries = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM face_detection_cache WHERE has_face = 1 AND expires_at > ?', (current_time,))
        faces_detected_count = cursor.fetchone()[0]

        # Database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size_bytes = cursor.fetchone()[0]

        conn.close()

        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'total_hits': total_hits,
            'cache_hit_rate': f"{(total_hits / max(active_entries, 1)):.2f}",
            'popular_queries': popular_queries,
            'face_detection_cache': {
                'total_images': face_cache_entries,
                'images_with_faces': faces_detected_count,
                'images_without_faces': face_cache_entries - faces_detected_count
            },
            'db_size_mb': round(db_size_bytes / (1024 * 1024), 2),
            'ttl_days': self.ttl_days
        }

    def search_cache(self, query_pattern: str) -> List[Dict[str, Any]]:
        """Search for cached entries matching a query pattern.

        Args:
            query_pattern: SQL LIKE pattern for query search

        Returns:
            List of matching cache entries
        """
        current_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT query, entity_type, source, created_at, expires_at, hit_count
            FROM image_cache
            WHERE query LIKE ? AND expires_at > ?
            ORDER BY hit_count DESC
        ''', (f'%{query_pattern}%', current_time))

        entries = [
            {
                'query': row[0],
                'entity_type': row[1],
                'source': row[2],
                'created_at': datetime.fromtimestamp(row[3]).isoformat(),
                'expires_at': datetime.fromtimestamp(row[4]).isoformat(),
                'hit_count': row[5]
            }
            for row in cursor.fetchall()
        ]

        conn.close()
        return entries

    def get_face_detection(self, image_url: str) -> Optional[tuple[bool, int]]:
        """Get cached face detection result for an image URL.

        Args:
            image_url: URL of the image

        Returns:
            Tuple of (has_face, face_count) or None if not cached/expired
        """
        current_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT has_face, face_count FROM face_detection_cache
            WHERE image_url = ? AND expires_at > ?
        ''', (image_url, current_time))

        row = cursor.fetchone()
        conn.close()

        if row:
            has_face = bool(row[0])
            face_count = row[1]
            return has_face, face_count

        return None

    def set_face_detection(self, image_url: str, has_face: bool, face_count: int):
        """Cache face detection result for an image URL.

        Args:
            image_url: URL of the image
            has_face: Whether a face was detected
            face_count: Number of faces detected
        """
        current_time = int(time.time())
        expires_at = current_time + (self.ttl_days * 24 * 60 * 60)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO face_detection_cache
            (image_url, has_face, face_count, detected_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (image_url, int(has_face), face_count, current_time, expires_at))

        conn.commit()
        conn.close()

    def get_gender_classification(self, image_url: str) -> Optional[str]:
        """Get cached gender classification result for an image URL.

        Args:
            image_url: URL of the image

        Returns:
            'male', 'female', or None if not cached/expired
        """
        current_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT gender FROM gender_classification_cache
            WHERE image_url = ? AND expires_at > ?
        ''', (image_url, current_time))

        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]

        return None

    def set_gender_classification(self, image_url: str, gender: str):
        """Cache gender classification result for an image URL.

        Args:
            image_url: URL of the image
            gender: Detected gender ('male' or 'female')
        """
        current_time = int(time.time())
        expires_at = current_time + (self.ttl_days * 24 * 60 * 60)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO gender_classification_cache
            (image_url, gender, classified_at, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (image_url, gender, current_time, expires_at))

        conn.commit()
        conn.close()
