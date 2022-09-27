import click
import requests
from tqdm import tqdm
import time
import datetime
import sqlite3
from yoyo import read_migrations, get_backend


exec_start = datetime.datetime.utcnow()


def datestr_to_timestamp(datestr: str):
    try:
        return datetime.datetime(*map(int, datestr.split("-")))  # type: ignore
    except:
        return None


def snake_case(d: dict):
    return {k.replace("-", "_"): v for (k, v) in d.items()}


def ensure_keys(d: dict, ks):
    return {k: d.get(k) for k in ks}


def get_manual_or_mapped(listen, mbid_type: str):
    meta = listen["track_metadata"]
    manually_submitted = meta.get("additional_info", {}).get(mbid_type)
    if manually_submitted:
        return manually_submitted
    else:
        return meta.get("mbid_mapping", {}).get(mbid_type)


def upsert_recording(db, mbid, always_update):
    should_update = "recordings" in always_update
    recording = db.execute(
        "SELECT * FROM recordings WHERE mbid = :mbid"
        + (" AND updated_at > :ts" if should_update else ""),
        {"mbid": mbid, "ts": exec_start},
    )
    if not recording.fetchone():
        time.sleep(1)
        mb_recording = requests.get(
            f"https://musicbrainz.org/ws/2/recording/{mbid}?fmt=json"
        ).json()
        mb_recording["first-release-date"] = datestr_to_timestamp(
            mb_recording.get("first-release-date")
        )

        # sometimes mbids change and musicbrainz silently redirects; we need to
        # make sure we can still detect existing entries
        mb_recording["id"] = mbid
        db.execute(
            """
            INSERT INTO recordings
            VALUES ( :id, :title, :disambiguation, :first_release_date, :length, NULL )
            ON CONFLICT ( mbid )
            DO UPDATE SET
              title = :title, disambiguation = :disambiguation,
              first_release_date = :first_release_date, length = :length
            """,
            ensure_keys(
                snake_case(mb_recording),
                ["id", "title", "disambiguation", "first_release_date", "length"],
            ),
        )


def upsert_artist(db, artist_mbid, always_update):
    should_update = "artists" in always_update
    artist = db.execute(
        "SELECT * FROM artists WHERE mbid = :mbid"
        + (" AND updated_at > :ts" if should_update else ""),
        {"mbid": artist_mbid, "ts": exec_start},
    )
    if not artist.fetchone():
        time.sleep(1)  # be nice
        mb_artist = requests.get(
            f"https://musicbrainz.org/ws/2/artist/{artist_mbid}?fmt=json"
        ).json()
        mb_artist["id"] = artist_mbid
        try:
            db.execute(
                """
                INSERT INTO artists VALUES (
                  :id, :name, :sort_name, :country,
                  :disambiguation, :gender, :gender_id,
                  :type, :type_id, NULL
                )
                ON CONFLICT ( mbid )
                DO UPDATE SET
                  name = :name, sort_name = :sort_name, country = :country,
                  disambiguation = :disambiguation, gender = :gender, gender_id = :gender_id,
                  type = :type, type_id = :type_id
                """,
                ensure_keys(
                    snake_case(mb_artist),
                    [
                        "id",
                        "name",
                        "sort_name",
                        "country",
                        "disambiguation",
                        "gender",
                        "gender_id",
                        "type",
                        "type_id",
                    ],
                ),
            )
        except InterruptedError:
            pass
        except:
            tqdm.write(f"artist response: {mb_artist}")
            raise


def upsert_recording_artists(db, artist_mbids, recording_mbid, always_update):
    for artist_mbid in artist_mbids:
        upsert_artist(db, artist_mbid, always_update)

        db.execute(
            "INSERT OR IGNORE INTO recording_artists VALUES ( ?, ?, NULL )",
            [artist_mbid, recording_mbid],
        )
    params = ",".join(["?" for _ in artist_mbids])
    db.execute(
        f"DELETE FROM recording_artists WHERE recording_mbid = ? AND artist_mbid NOT IN ({params})",
        [recording_mbid, *artist_mbids],
    )


def upsert_release_with_recording(db, release_mbid, recording_mbid, always_update):
    should_update = "releases" in always_update
    release = db.execute(
        "SELECT * FROM releases WHERE mbid = :mbid"
        + (" AND updated_at > :ts" if should_update else ""),
        {"mbid": release_mbid, "ts": exec_start},
    )
    if not release.fetchone():
        time.sleep(1)
        mb_release = requests.get(
            f"https://musicbrainz.org/ws/2/release/{release_mbid}?fmt=json&inc=artists"
        ).json()
        mb_release["id"] = release_mbid
        mb_release["date"] = datestr_to_timestamp(mb_release.get("date"))
        try:
            db.execute(
                """
                INSERT INTO releases VALUES (
                  :id, :title, :asin, :barcode, :country, :date,
                  :disambiguation, :quality, :status, :status_id,
                  NULL
                )
                ON CONFLICT
                DO UPDATE SET
                  title = :title, asin = :asin, barcode = :barcode, country = :country, date = :date,
                  disambiguation = :disambiguation, quality = :quality, status = :status, status_id = :status_id
                """,
                ensure_keys(
                    snake_case(mb_release),
                    [
                        "id",
                        "title",
                        "asin",
                        "barcode",
                        "country",
                        "date",
                        "disambiguation",
                        "quality",
                        "status",
                        "status_id",
                    ],
                ),
            )
        except InterruptedError:
            pass
        except:
            tqdm.write(f"release response: {mb_release}")
            raise

        try:
            for artist_credit in mb_release["artist-credit"]:
                # TODO: This is not ideal becaue
                # a) we're using musicbrainz mbids and might have the previous problem of mbid drift
                # b) we're refetching information we already have due to how upsert_artist is written
                upsert_artist(db, artist_credit["artist"]["id"], always_update)
                release_artist = db.execute(
                    "SELECT * FROM release_artists WHERE release_mbid = ? AND artist_mbid = ?",
                    [mb_release["id"], artist_credit["artist"]["id"]],
                )
                if not release_artist.fetchone():
                    db.execute(
                        """
                        INSERT OR IGNORE
                        INTO release_artists
                        VALUES ( :release_mbid, :artist_mbid, :joinphrase, :name, NULL )
                        """,
                        {
                            "release_mbid": mb_release["id"],
                            "artist_mbid": artist_credit["artist"]["id"],
                            "joinphrase": artist_credit["joinphrase"],
                            "name": artist_credit["name"],
                        },
                    )
        except:
            tqdm.write(f"response: {mb_release}")
            raise

    # TODO: Delete recordings if they're not on the release anymore
    db.execute(
        """
        INSERT OR IGNORE INTO release_recordings VALUES ( ?, ?, NULL )
        """,
        [recording_mbid, release_mbid],
    )


def upsert_listen(db, listen):
    listened_at = datetime.datetime.fromtimestamp(listen["listened_at"])
    imported_listen = db.execute(
        "SELECT * FROM listens WHERE listened_at = ?", [listened_at]
    )
    if not imported_listen.fetchone():
        cur = db.execute(
            "INSERT INTO listens VALUES ( NULL, ?, ?, ?, ?, NULL )",
            [
                listened_at,
                listen["user_name"],
                get_manual_or_mapped(listen, "recording_mbid"),
                get_manual_or_mapped(listen, "release_mbid"),
            ],
        )

        db.executemany(
            "INSERT INTO listen_artists VALUES ( ?, ?, NULL )",
            [
                (cur.lastrowid, artist_mbid)
                for artist_mbid in get_manual_or_mapped(listen, "artist_mbids")
            ],
        )


now = datetime.datetime.now()


@click.command(
    help="Imports listenbrainz history of a single user with associated artists, releases, and recordings."
)
@click.option(
    "--user",
    required=True,
    help="The Listenbrainz username for which to import listens.",
    type=str,
)
@click.option(
    "--max-results", "-n", help="Limit the maximum amount of fetched results.", type=int
)
@click.option(
    "--since",
    "-s",
    default=datetime.datetime(1970, 1, 1, 1, 0),
    help="Consider only listens more recent than this argument. Defaults to the most recent listen saved in the database.",
    type=click.DateTime(),
)
@click.option(
    "--until",
    "-t",
    default=now,
    help="Consider only listens older than this argument.",
    type=click.DateTime(),
)
@click.option(
    "--update",
    "-u",
    "always_update",
    help="Fetch information from Musicbrainz even if it already exists locally. Setting this argument to '*' will re-fetch all information. Use this flag multiple times to update multiple resource types.",
    multiple=True,
    type=click.Choice(["artists", "recordings", "releases", "*"]),
)
def import_listens(user, max_results, since, until, always_update):
    backend = get_backend("sqlite:///listenbrainz.db")
    migrations = read_migrations("./listenbrainz_to_sqlite/migrations")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    with sqlite3.connect("listenbrainz.db", 100, sqlite3.PARSE_DECLTYPES) as con, tqdm(
        desc=f"Importing listens from the Listenbrainz API", unit="listen(s)"
    ) as pbar:
        con.isolation_level = None
        cur = con.cursor()

        if not since and until == now:
            res = cur.execute(
                "SELECT listened_at FROM listens ORDER BY listened_at LIMIT 1"
            ).fetchone()
            since = res and res[0] or datetime.datetime(1970, 1, 1, 1, 0)

        num_results = 0

        min_ts = int(time.mktime(since.timetuple()))
        max_ts = int(time.mktime(until.timetuple()))

        if "*" in always_update:
            always_update = ("artists", "recordings", "releases")

        while True:
            max_dt = datetime.datetime.fromtimestamp(max_ts)
            pbar.set_description_str(
                f'Importing @ {max_dt.strftime("%Y-%m-%d %H:%M:%S")}'
            )
            req = requests.get(
                f"https://api.listenbrainz.org/1/user/{user}/listens",
                {"max_ts": max_ts, "count": 100},
            )
            if not req.ok:
                tqdm.write(f"Something went wrong while requesting {req.url}, aborting")
                tqdm.write(f'{req.status_code}: {req.json()["error"]}')
                break

            body = req.json()["payload"]

            # insert all listens, artists, recordings, etc.
            for listen in body["listens"]:
                pbar.update()

                artist_mbids = get_manual_or_mapped(listen, "artist_mbids")
                recording_mbid = get_manual_or_mapped(listen, "recording_mbid")
                release_mbid = get_manual_or_mapped(listen, "release_mbid")

                if not (artist_mbids and recording_mbid and release_mbid):
                    meta = listen["track_metadata"]
                    artist_name = meta.get("artist_name", "")
                    track_name = meta.get("track_name", "")
                    tqdm.write(
                        f"Skipping listen without mbid info: {artist_name} - {track_name}",
                    )
                    continue

                try:
                    upsert_recording(cur, recording_mbid, always_update)
                    upsert_recording_artists(
                        cur, artist_mbids, recording_mbid, always_update
                    )
                    upsert_release_with_recording(
                        cur, release_mbid, recording_mbid, always_update
                    )
                    upsert_listen(cur, listen)
                except:
                    tqdm.write(
                        f"Something went wrong while requesting {req.url}, aborting"
                    )
                    tqdm.write(f"listen: {listen}")
                    raise

            try:
                max_ts = min([l["listened_at"] for l in body.get("listens", [])])
            except ValueError:
                # empty list for listens
                break

            num_results += body["count"]
            if (max_results and num_results >= max_results) or max_ts <= min_ts:
                break

            time.sleep(1)


if __name__ == "__main__":
    import_listens(auto_envar_prefix="LISTENBRAINZ_IMPORT")
