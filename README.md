# Unwetter
Automatically notify newsroom about weather warnings from DWD

## Deployment

### Environment variables
```yaml
NVS_FTP_URL:                 # FTP host for Nachrichtenverteilsystem uploads
NVS_FTP_PASS:
NVS_FTP_USER:
SENTRY_DSN:                  # DSN for sentry.io for error tracking
SLACK_BOT_TOKEN:             # Bot token for sending messages to Slack
SLACK_CHANNEL:               # Channel ID to send updates to
TWITTER_ACCESS_TOKEN: 
TWITTER_ACCESS_TOKEN_SECRET:
TWITTER_CONSUMER_KEY:
TWITTER_CONSUMER_SECRET:
TWITTER_DEMO_HANDLE:         # Twitter handle that should be mentioned in demo tweets
WDR_PROJECT_INFO_URL:        https://unser.wdr.de/sites/DWDUnwetterwarnungen94e47adr/SitePages/Details%20Unwetterwarnungen.aspx
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
