MONGODB_URI=`heroku config:get MONGODB_URI -a uwa` pipenv run jupyter notebook --notebook-dir=.
