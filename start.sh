#!/usr/bin/zsh

cd /home/ydethe/photomanagement
source /opt/conda/etc/profile.d/conda.sh
conda activate pmg
# gunicorn --workers 4 --bind 127.0.0.1:3999 -m 007 PhotoManagement.wsgi:application
gunicorn --workers 4 --bind 127.0.0.1:3999 -m 007 PhotoManagement:app


