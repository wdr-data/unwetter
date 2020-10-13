# Unwetter

Automatically notify newsroom about weather warnings from DWD

## Map generation

The WDR Sans fonts, map design and source images are proprietary and not licensed under the MIT license. To make your own design, do the following steps:

1. Optional: Edit `config.yaml` to select the desired state(s)
2. Start a local development Flask instance using `FLASK_APP=app FLASK_ENV=development pipenv run flask run`
3. Navigate to http://127.0.0.1:5000/basemap to get a black/white map template
4. Use the template to create your own map design
5. Replace the files in `assets/images`
6. Replace the WDR Sans fonts in `assets/fonts`
7. Update the font import and drawing in `src/unwetter/map.py:draw_text`

## Deployment

### Database

We use the ObjectRocket MongoDB Heroku Add-On. Provision the Add-On and create a database called `uwa` with the user `uwa`.

### Environment variables

```yaml
NVS_FTP_URL: # FTP host for Nachrichtenverteilsystem uploads
NVS_FTP_PASS:
NVS_FTP_USER:
SENTRY_DSN: # DSN for sentry.io for error tracking
SLACK_BOT_TOKEN: # Bot token for sending messages to Slack
SLACK_CHANNEL: # Channel ID to send updates to
TWITTER_ACCESS_TOKEN:
TWITTER_ACCESS_TOKEN_SECRET:
TWITTER_CONSUMER_KEY:
TWITTER_CONSUMER_SECRET:
TWITTER_DEMO_HANDLE: # Twitter handle that should be mentioned in demo tweets
WDR_PROJECT_INFO_URL: https://unser.wdr.de/sites/DWDUnwetterwarnungen94e47adr/SitePages/Details%20Unwetterwarnungen.aspx
ORMONGO_PASSWORD: # The password you set for the MongoDB database
```

### Heroku Labs

- Runtime dyno metadata for linking releases to sentry
  - `heroku labs:enable runtime-dyno-metadata -a <appname>`

### Scheduled Jobs

After deployment, run `heroku ps:scale clock=1` to make sure that no two schedulers are running
at the same time.

### Heroku release tracking in Sentry

Follow [this guide](https://blog.sentry.io/2017/05/15/heroku-commits) to connect Heroku and Sentry
for better release tracking.
