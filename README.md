# Unwetter
Automatically notify newsroom about weather warnings from DWD

## Deployment

### Scheduled Jobs
After deployment, run `heroku ps:scale clock=1` to make sure that no two schedulers are running 
at the same time.
