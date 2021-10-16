#!/usr/bin/env python3
import sqlite3


def setup_database(db_path):
    with sqlite3.Connection(db_path) as db:
        cur = db.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS listens (
                listened_at TIMESTAMP,
                user_name VARCHAR(255),
                recording_mbid CHAR(36),
                release_mbid CHAR(36)
            );
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS listens_listened_at ON listens ( listened_at );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS listens_user_name ON listens ( user_name );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS listens_track_recording_mbid ON listens ( recording_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS listens_track_release_mbid ON listens ( release_mbid );"
        )

        cur.execute(
            """
            -- A listen can have multiple artists
            CREATE TABLE IF NOT EXISTS listen_artists (
                listen_id INTEGER,
                artist_mbid CHAR(36)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS listen_artists_listen_id ON listen_artists ( listen_id );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS listen_artists_artist_mbid ON listen_artists ( artist_mbid );"
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS artists (
              mbid CHAR(36),
              name TEXT
            );
            """
        )
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS artists_mbid ON artists (mbid);")

        cur.execute(
            """
           CREATE TABLE IF NOT EXISTS recordings (
               mbid CHAR(36),
               name TEXT
           );
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS recordings_mbid ON recordings (mbid);"
        )

        cur.execute(
            """
           -- Use this to find out all of the artists performing in a recording
           CREATE TABLE IF NOT EXISTS artists_for_recordings (
               artist_mbid CHAR(36),
               recording_mbid CHAR(36)
           );
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS artists_for_recordings_mapping ON artists_for_recordings ( artist_mbid, recording_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS artists_for_recordings_by_artist ON artists_for_recordings ( artist_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS artists_for_recordings_by_recording ON artists_for_recordings ( recording_mbid );"
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS releases (
                mbid CHAR(36),
                name TEXT
            );
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS releases_mbid ON releases (mbid);"
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS recordings_on_releases (
                recording_mbid CHAR(36),
                release_mbid CHAR(36)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS recordings_on_releases_by_recording ON recordings_on_releases ( recording_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS recordings_on_releases_by_release ON recordings_on_releases ( release_mbid );"
        )
