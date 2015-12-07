#!/usr/bin/env bash
iptables -I INPUT -p tcp --dport 80 --syn -j DROP
sleep 1
supervisorctl restart haproxy
iptables -D INPUT -p tcp --dport 80 --syn -j DROP