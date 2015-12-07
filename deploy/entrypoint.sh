#!/bin/bash

# preload config
python /etc/haproxy/ear.py --tag haproxy;

# start supervisord
exec supervisord;