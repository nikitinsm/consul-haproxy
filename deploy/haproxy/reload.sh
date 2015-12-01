iptables -I INPUT -p tcp --dport 80 --syn -j DROP
sleep 1
supervisorctl -u login -p pass restart haproxy:*
iptables -D INPUT -p tcp --dport 3213 --syn -j DROP