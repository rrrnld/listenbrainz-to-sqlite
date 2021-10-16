#!/usr/bin/env python3
import sqlite3


def setup_database(db_path):
    with sqlite3.Connection(db_path) as db:
        cur = db.cursor()

        cur.execute("PRAGMA foreign_keys = ON;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS artists (
              mbid CHAR(36) PRIMARY KEY,
              name TEXT,
              sort_name TEXT,
              country CHAR(2),
              disambiguation TEXT,
              gender VARCHAR(255),
              gender_id CHAR(36),
              type VARCHAR(255),
              type_id CHAR(36)
            );
            """
        )

        cur.execute(
            """
           CREATE TABLE IF NOT EXISTS recordings (
               mbid CHAR(36) PRIMARY KEY,
               title TEXT,
               disambiguation TEXT,
               first_release_date TIMESTAMP,
               length INTEGER
           );
            """
        )

        cur.execute(
            """
            -- Use this to find out all of the artists performing in a recording
            CREATE TABLE IF NOT EXISTS recording_artists (
                artist_mbid CHAR(36),
                recording_mbid CHAR(36),
                FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid ),
                FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid )
            );
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS recording_artists_mapping ON recording_artists ( artist_mbid, recording_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS recording_artists_by_artist ON recording_artists ( artist_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS recording_artists_by_recording ON recording_artists ( recording_mbid );"
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS releases (
                mbid CHAR(36) PRIMARY KEY,
                title TEXT,
                asin VARCHAR(255),
                barcode VARCHAR(255),
                country CHAR(2),
                date TIMESTAMP,
                disambiguation TEXT,
                quality VARCHAR(255),
                status VARCHAR(255),
                status_id CHAR(36)
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS release_artists (
                release_mbid CHAR(36),
                artist_mbid CHAR(36),
                joinphrase VARCHAR(255),
                name TEXT,
                FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid ),
                FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid )
            )
            """
        )
        cur.execute(
            """
            CREATE VIEW IF NOT EXISTS release_artists_label AS
               SELECT release_mbid, group_concat(name || joinphrase, "") release_artists
               FROM release_artists
               GROUP BY release_mbid
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS release_artists_mapping ON release_artists ( release_mbid, artist_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS release_artists_by_release ON release_artists ( release_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS release_artists_by_artist ON release_artists ( artist_mbid );"
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS listens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listened_at TIMESTAMP,
                user_name VARCHAR(255),
                recording_mbid CHAR(36),
                release_mbid CHAR(36),
                FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid ),
                FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid )
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
                artist_mbid CHAR(36),
                FOREIGN KEY ( listen_id ) REFERENCES listens ( id ),
                FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid )
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
            CREATE TABLE IF NOT EXISTS release_recordings (
                recording_mbid CHAR(36),
                release_mbid CHAR(36),
                FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid ),
                FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid )
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS release_recordings_by_recording ON release_recordings ( recording_mbid );"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS release_recordings_by_release ON release_recordings ( release_mbid );"
        )
