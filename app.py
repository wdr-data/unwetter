#!/user/bin/env python3.6

import os
from io import BytesIO
from datetime import datetime, timezone

import pytz
from feedgen.feed import FeedGenerator
from flask import Flask, Response, request, json, send_file, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from unwetter import db, generate, wina as wina_gen, slack, map, sentry
from unwetter.config import SEVERITY_FILTER, STATES_FILTER, URGENCY_FILTER
from unwetter.generate import urls


sentry.init()
app = Flask(__name__, static_folder="website/build")
auth = HTTPBasicAuth()

users = {
    "wdr": generate_password_hash(os.environ.get("BASIC_AUTH_PASSWORD", "")),
    "uwa": generate_password_hash(os.environ.get("BASIC_AUTH_PASSWORD", "")),
}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username


@app.route("/feed.rss")
def feed():
    fg = FeedGenerator()
    fg.id(urls.URL_BASE)
    fg.title("Unwetter Testfeed")
    fg.link(
        href="https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html",
        rel="alternate",
    )
    fg.subtitle("This is a test feed!")
    fg.link(href=f"{urls.URL_BASE}feed.rss", rel="self")
    fg.language("de")

    # Iterate over the most recent 5 events matching filter
    for event in db.load_published(limit=10):
        fe = fg.add_entry(order="append")
        fe.id(event["id"])
        fe.title(generate.title(event, variant="wina_headline"))
        fe.link(href=urls.wina(event))
        fe.published(event["sent"].replace(tzinfo=pytz.UTC))
        fe.description(generate.description(event).replace("\n", "<br>"))

    r = Response(fg.rss_str(pretty=True), mimetype="application/rss+xml")
    r.headers["Content-Type"] = "text/xml; charset=utf-8"
    return r


@app.route("/wina/<id>")
def wina(id):
    r = Response(wina_gen.from_id(id), mimetype="application/xml")
    r.headers["Content-Type"] = "text/xml; charset=iso-8859-1"

    return r


def send_pil(img):
    bio = BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)

    return send_file(bio, "image/png")


@app.route("/map/<id>.png")
def map_single(id):
    img = map.generate_map([db.by_id(id)])
    return send_pil(img)


@app.route("/map")
@auth.login_required
def map_multi():
    ids = request.args.getlist("id")
    disabled_ids = request.args.getlist("disabled")

    mode = request.args.get("mode", "square")

    title = request.args.get("title")
    title_size = int(request.args.get("titleSize", 130))
    subtitle = request.args.get("subtitle")
    subtitle_size = int(request.args.get("subtitleSize", 110))

    img = map.generate_map(
        list(db.by_ids(ids)),
        mode=map.Mode(mode),
        disabled_events=list(db.by_ids(disabled_ids)),
        title=title,
        title_size=title_size,
        subtitle=subtitle,
        subtitle_size=subtitle_size,
    )
    return send_pil(img)


@app.route("/basemap")
def map_base_square():
    img = map.generate_base_map(mode=map.Mode.SQUARE)
    return send_pil(img)


@app.route("/basemap_wide")
def map_base_wide():
    img = map.generate_base_map(mode=map.Mode.WIDE)
    return send_pil(img)


@app.route("/slack/event", methods=["GET", "POST"])
def slack_event():
    data = request.json or request.form

    if not data:
        return ""

    if data.get("challenge"):
        return data.get("challenge")

    payload = data.get("payload")

    if payload:
        data = json.loads(payload)

    print(data)

    actions = data.get("actions")

    for action in actions:
        id = data["callback_id"]
        channel_id = data["channel"]["id"]
        user_id = data["user"]["id"]
        event = db.by_id(id)
        response = None

        if action["name"] == "twitter":
            response = "*Vorschlag Tweet*:\n" + generate.tweet(event)
        elif action["name"] == "radio":
            response = "*Vorschlag Radionachrichten*:\n" + generate.radio(event)
        elif action["name"] == "crawl":
            response = "*Vorschlag TV-Crawl:*\n" + generate.crawl(event)
        elif action["name"] == "dwd":
            response = "Offizielle Meldung des DWD:\n" + event["description"]
        elif action["name"] == "info":
            if "references" in event:
                references = f'Referenzen: {", ".join(event["references"])}'
            else:
                references = ""

            response = f"""
Diese Meldung basiert auf offiziellen Informationen des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html

Die Bereitstellung dieser Information ist ein Projekt des Digitalen Wandels und wird aktiv weiterentwickelt.
Informationen und Kontakt: {os.environ["WDR_PROJECT_INFO_URL"]}

Event ID: {data["callback_id"]}

{references}
            """.strip()

        if response:
            slack.post_message(
                response,
                mrkdwn=True,
                private=user_id,
                channel=channel_id,
                thread_ts=data["original_message"]["thread_ts"],
            )

    return ""


@app.route("/slack/command/show", methods=["POST"])
def slack_command_show():
    data = request.form

    if not data:
        print("No Data :(")
        return ""

    event = db.by_id(data["text"])

    if not event:
        return f'No event found with ID {data["text"]}'

    slack.post_message(f'Sending test event with ID {data["text"]}')
    slack.post_event(event)

    return f'Sent event with ID {data["text"]}'


@app.route("/test")
def test():
    return "OK"


@app.route("/error")
def error():
    raise Exception("AHHHHHHHH")


@app.route("/api/v1/events/current", methods=["GET"])
def api_v1_current_events():
    at = request.args.get("at")

    if at:
        at = datetime.utcfromtimestamp(int(at))

    current_events = db.current_events(at=at, all_severities=True)
    filtered_events = []

    for event in current_events:
        if event["severity"] == "Minor":
            continue

        del event["_id"]
        del event["geometry"]
        for field in ("sent", "effective", "onset", "expires"):
            event[field] = event[field].replace(tzinfo=timezone.utc).timestamp()

        filtered_events.append(event)

    return json.dumps(sorted(filtered_events, key=map.severity_key, reverse=True))


# Serve React App
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
@auth.login_required
def serve(path):
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run()
