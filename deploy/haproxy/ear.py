#!/usr/bin/python
import os
import socket
import sys
import argparse

import consul
import dict_tools
import ansible

from subprocess import call
from distutils.version import LooseVersion
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader

# Import ansible filters
if LooseVersion(ansible.__version__) < "2.0.0":
    from ansible.runner.filter_plugins.core import FilterModule
else:
    from ansible.plugins.filter.core import FilterModule


HAPROXY_TEMPLATE = os.environ.get('HAPROXY_TEMPLATE') or '/etc/haproxy/haproxy.conf.j2'
HAPROXY_CONFIG = os.environ.get('HAPROXY_CONFIG') or '/etc/haproxy.conf'
CONSUL_HOST = os.environ.get('CONSUL_HOST') or '172.17.0.1'
CONSUL_PORT = int(os.environ.get('CONSUL_PORT') or 8500)


jinja_env = Environment(loader=FileSystemLoader('/'))
jinja_env.filters.update(FilterModule().filters())


parser = argparse.ArgumentParser\
    ( description='Listen to Consul.'
    , )
parser.add_argument\
    ( '-l', '--listen'
    , action='store_true'
    , help='Listen mode, waits for consul changes and updates haproxy config'
    )
parser.add_argument\
    ( '-t', '--tag'
    , action='append'
    , help='Filter by tags'
    )
parser.add_argument\
    ( '-ch', '--consul-host'
    , type=lambda value: socket.inet_aton(value) and value
    , nargs='?'
    , help='Consul ip address'
    , default=CONSUL_HOST
    )
parser.add_argument\
    ( '-cp', '--consul-port'
    , nargs='?'
    , type=int
    , help='Consul port number'
    , default=CONSUL_PORT
    )
parser.add_argument\
    ( '-hc', '--haproxy-config'
    , nargs='?'
    , help='Haroxy config file path'
    , default=HAPROXY_CONFIG
    )
parser.add_argument\
    ( '-ht', '--haproxy-template'
    , nargs='?'
    , help='Haroxy template file path'
    , default=HAPROXY_TEMPLATE
    )


def consul_kv_to_dict(data):
    result = dict()
    if data:
        for item in data:
            key = item['Key']
            value = item['Value']
            result = dict_tools.merge\
                ( result
                , dict_tools.expand
                  ( *key.split('/')
                  , value=value
                ) )
    return result


def update_haproxy(args, client, services):
    filter_by_tags = set(args.tag)

    context = \
        { 'haproxy': {}
        , 'services': []
        , 'env': dict(os.environ)
        }

    for service_id, tags in services.iteritems():
        if filter_by_tags and len(set(tags) & filter_by_tags) == 0:
            continue

        # Get service data
        index, service = client.catalog.service(service_id)
        service = service[0]
        # Get data
        path = 'catalog/%s/' % service_id
        index, data = client.kv.get(path, recurse=True)
        data = dict_tools.get\
            ( consul_kv_to_dict(data)
            , 'catalog', service_id
            )
        if data:
            # Here we can override any data from KV storage in Service storage
            service = dict_tools.merge(service, data)
        # service['Domain'] = (client.kv.get('catalog/%s' % service['ServiceID'])[1] or {}).get('Value')
        # Store in context
        context['services'].append(service)

    template = jinja_env.get_template(args.haproxy_template)
    result = template.render(context)

    # print json.dumps(context, ensure_ascii=False, indent=2)
    # print ''
    # print '----'
    # print ''
    #
    # print result

    try:
        handler = open(args.haproxy_config, mode='r')
        old_config = handler.read()
        handler.close()
    except Exception as e:
        old_config = ''

    if old_config != result:
        handler = open(args.haproxy_config, mode='w')
        handler.write(result)
        handler.close()
        call(["/etc/haproxy/reload.sh"])


def main():
    args = parser.parse_args()
    client = consul.Consul(args.consul_host, args.consul_port)

    # Preload haproxy config
    index, services = client.catalog.services()
    update_haproxy(args, client, services)

    if not args.listen:
        return

    # @todo: async
    # @todo: check for race
    index = None
    while True:
        try:
            index, services = client.catalog.services(index)
            try:
                update_haproxy(args, client, services)
            except Exception as e:
                if os.environ.get('DEBUG'):
                    raise e
        except KeyboardInterrupt:
            sys.exit()


if __name__ == '__main__':
    main()
