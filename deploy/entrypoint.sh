#!/bin/bash

# preload config
python /etc/haproxy/ear.py --tag haproxy;

# Normalize iptable
iptables -D INPUT -p tcp --dport 80 --syn -j DROP

# start supervisord
exec supervisord;