import click
import requests
from tqdm import tqdm
import time
import datetime
import sqlite3
from .db import setup_database


def datestr_to_timestamp(datestr: str):
    try:
        dt = datetime.datetime(*map(int, datestr.split("-")))  # type: ignore
        return int(time.mktime(dt.utctimetuple()))
    except:
        return None


def snake_case(d: dict):
    return {k.replace("-", "_"): v for (k, v) in d.items()}


def upsert_recording(db, mbid):
    recording = db.execute("SELECT * FROM recordings WHERE mbid = ?", [mbid])
    if not recording.fetchone():
        time.sleep(1)
        mb_recording = requests.get(
            f"https://musicbrainz.org/ws/2/recording/{mbid}?fmt=json"
        ).json()
        mb_recording["first-release-date"] = datestr_to_timestamp(
            mb_recording.get("first-release-date")
        )
        db.execute(
            "INSERT INTO recordings VALUES ( :id, :title, :disambiguation, :first_release_date, :length )",
            snake_case(mb_recording),
        )


def upsert_artists_for_recording(db, artist_mbids, recording_mbid):
    for artist_mbid in artist_mbids:
        artist = db.execute("SELECT * FROM artists WHERE mbid = ?", [artist_mbid])
        if not artist.fetchone():
            time.sleep(1) # be nice
            mb_artist = requests.get(
                f"https://musicbrainz.org/ws/2/artist/{artist_mbid}?fmt=json"
            ).json()
            try:
                db.execute(
                    """
                    INSERT INTO artists VALUES (
                    :id, :name, :sort_name, :country,
                    :disambiguation, :gender, :gender_id,
                    :type, :type_id
                    )
                    """,
                    snake_case(mb_artist),
                )
            except:
                print(mb_artist)
                raise

        artist_on_recording = db.execute(
            """
            SELECT * FROM artists_for_recordings
            WHERE artist_mbid = ? AND recording_mbid = ?;
            """,
            [artist_mbid, recording_mbid],
        )
        if not artist_on_recording.fetchone():
            db.execute(
                "INSERT INTO artists_for_recordings VALUES ( ?, ? )",
                [artist_mbid, recording_mbid],
            )


def upsert_release_with_recording(db, release_mbid, recording_mbid):
    release = db.execute("SELECT * FROM releases WHERE mbid = ?;", [release_mbid])
    if not release.fetchone():
        time.sleep(1)
        mb_release = requests.get(
            f"https://musicbrainz.org/ws/2/release/{release_mbid}?fmt=json"
        ).json()
        mb_release["date"] = datestr_to_timestamp(mb_release.get("date"))
        try:
            db.execute(
                """
                INSERT INTO releases VALUES (
                :id, :title, :asin, :barcode, :country, :date,
                :disambiguation, :quality, :status, :status_id
                )
                """,
                snake_case(mb_release),
            )
        except:
            print(mb_release)
            raise

    recording_on_release = db.execute(
        """
        SELECT * FROM recordings_on_releases WHERE recording_mbid = ? AND release_mbid = ?;
        """,
        [recording_mbid, release_mbid],
    )
    if not recording_on_release.fetchone():
        db.execute(
            """
            INSERT INTO recordings_on_releases VALUES ( ?, ? );
            """,
            [recording_mbid, release_mbid],
        )


def upsert_listen(db, listen):
    imported_listen = db.execute(
        "SELECT * FROM listens WHERE listened_at = ?", [listen["listened_at"]]
    )
    if not imported_listen.fetchone():
        mbids = listen["track_metadata"]["mbid_mapping"]
        cur = db.execute(
            "INSERT INTO listens VALUES ( NULL, ?, ?, ?, ? )",
            [
                listen["listened_at"],
                listen["user_name"],
                mbids["recording_mbid"],
                mbids["release_mbid"],
            ],
        )

        db.executemany(
            "INSERT INTO listen_artists VALUES ( ?, ? )",
            [(cur.lastrowid, artist_mbid) for artist_mbid in mbids["artist_mbids"]],
        )


@click.command(
    help="Imports listenbrainz history of a single user with associated artists, releases, and recordings."
)
@click.option(
    "--user",
    required=True,
    help="The Listenbrainz username form which to import listens",
    type=str,
)
@click.option(
    "--max-results", help="Limit the maximum amount of fetched results.", type=int
)
@click.option(
    "--since",
    default=datetime.datetime(1970, 1, 1),
    help="Consider only listens more recent than this argument",
    type=click.DateTime(),
)
@click.option(
    "--until",
    default=datetime.datetime.now(),
    help="Consider only listens older than this argument",
    type=click.DateTime(),
)
def import_listens(user, max_results, since, until):
    setup_database("listenbrainz.db")
    with sqlite3.connect("listenbrainz.db") as con, tqdm(
        desc=f'Starting to fetch {max_results or "all"} listens from the listenbrainz API',
        unit=" listens",
    ) as pbar:
        con.isolation_level = None
        cur = con.cursor()

        num_results = 0

        min_ts = int(time.mktime(since.timetuple()))
        max_ts = int(time.mktime(until.timetuple()))

        while True:
            req = requests.get(
                f"https://api.listenbrainz.org/1/user/{user}/listens",
                {"min_ts": min_ts, "max_ts": max_ts},
            )
            if not req.ok:
                print("Something is wrong! aborting")
                print(f'{req.status_code}: {req.json()["error"]}')
                break

            body = req.json()["payload"]

            # insert all listens, artists, recordings, etc.
            for listen in body["listens"]:
                if not listen["track_metadata"].get("mbid_mapping"):
                    artist_name = listen["track_metadata"].get("artist_name", "")
                    track_name = listen["track_metadata"].get("track_name", "")
                    tqdm.write(
                        f"Skipping listen without mbid info: {artist_name} - {track_name}",
                    )
                    continue

                meta = listen["track_metadata"]
                upsert_recording(cur, meta["mbid_mapping"]["recording_mbid"])
                upsert_artists_for_recording(
                    cur,
                    meta["mbid_mapping"]["artist_mbids"],
                    meta["mbid_mapping"]["recording_mbid"],
                )
                upsert_release_with_recording(
                    cur,
                    meta["mbid_mapping"]["release_mbid"],
                    meta["mbid_mapping"]["recording_mbid"],
                )

                upsert_listen(cur, listen)

            num_results += body["count"]
            pbar.update(body["count"])

            min_ts = body["latest_listen_ts"]
            if (max_results and num_results >= max_results) or not body["listens"]:
                break

            con.commit()
            time.sleep(0.5)


if __name__ == "__main__":
    import_listens(auto_envar_prefix="LISTENBRAINZ_IMPORT")
