FROM haproxy:1.6

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python-pip iptables git && \
    pip install -U pip

# Prepare python
COPY ./requirements.pip /srv/requirements.pip
RUN pip install -r /srv/requirements.pip

# Prepare FS
ENV APP_NAME="/haproxy"
ENV APP_ROOT="/opt${APP_NAME}"
ENV APP_REPOSITORY="${APP_ROOT}/repository"

# Prepare supervisord
COPY ./deploy/supervisord/supervisord.conf /etc/supervisord.conf

# Prepare haproxy
COPY ./deploy/haproxy /etc/haproxy
RUN chmod 770 /etc/haproxy/ear.py

# Prepare initial
COPY ./deploy/entrypoint.sh /bin/entrypoint.sh
RUN chmod 700 /bin/entrypoint.sh

# Prepare ports
EXPOSE 80
EXPOSE 443

CMD ["supervisord"]