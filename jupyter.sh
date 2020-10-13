ORMONGO_RS_URL=`heroku config:get ORMONGO_RS_URL -a uwa` ORMONGO_PASSWORD=`heroku config:get ORMONGO_PASSWORD -a uwa` pipenv run jupyter notebook --notebook-dir=.
