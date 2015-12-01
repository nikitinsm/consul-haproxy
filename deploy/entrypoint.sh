#!/bin/bash

# preload config
exec /etc/haproxy/ear.py --tag haproxy;

# start supervisord
exec supervisord;