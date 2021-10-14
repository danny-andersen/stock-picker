
#virtualenv env_stockpicker
source env_stockpicker/bin/activate
mkdir -p libs
pip install -t libs -r libraries.txt
zip -r lib.zip libs/*
