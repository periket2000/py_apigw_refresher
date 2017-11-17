from jinja2 import Template
import urllib3
import os
import json
import src.config as config

template = '''
##########################################################
# Application {{upstream}} on endpoint {{servername}}
##########################################################
upstream {{ upstream }} {
{% for serverip in servers %}
    server {{ serverip }} fail_timeout=10s;
{% endfor %}
    keepalive 16;
}

server {
        listen 80;
        server_name {{ servername }};
        rewrite ^ https://$host$request_uri? permanent;
}

server {
        listen 443 ssl;
        keepalive_timeout 70;

        ssl_certificate     /etc/nginx/server.crt;
        ssl_certificate_key /etc/nginx/server.key;
        ssl_protocols       TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers         HIGH:!aNULL:!MD5;

        root /usr/local/var/www/htdocs/app;
        index index.html index.htm;

        # should exist in /etc/hosts as 127.0.0.1 {{ servername }}
        server_name {{ servername }};

        error_page 404 /404.html;
        error_page 400 /400.html;

        # our endpoint would be http://{{ servername }}/api
        location ~ ^/(\/?)(.*)$ {
            {% if secured == "true" %}access_by_lua_file {{access_file}};{% endif %}
            # for relative calls from upstream servers
            proxy_set_header Host $http_host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-M-Secure "true";
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://{{ upstream }}/$2$is_args$args;
            # in case of failing server, go to the next one (404 not found or Bad gateway while microservice is deploying)
            proxy_next_upstream error timeout http_404 http_502;
            {% if debug_upstream == "true" %}add_header X-Upstream $upstream_addr always;{% endif %}
        }
}
'''

appfile = Template(template)


class Tasks:
    def __init__(self):
        self.scheme = os.getenv('MESOS_SCHEME', 'http://')
        self.masters = os.getenv('MESOS_MASTERS', '192.168.250.101,192.168.250.102,192.168.250.103')
        self.marathon_port = os.getenv('MARATHON_PORT', '8080')
        self.tasks_uri = os.getenv('TASKS_URI', '/v2/tasks')
        self.config_dir = config.config_dir
        self.apigw_config_dir = config.apigw_config_dir
        self.tmp_dir = config.tmp_dir
        self.apps = None
        try:
            with open(self.config_dir + '/' + config.config_fic, 'r') as f:
                self.config = json.load(f)
        except IOError:
            self.config = None

    def master(self):
        if self.masters:
            ms = self.masters.split(',')
            yield from ms
        else:
            yield None

    def masters_size(self):
        if self.masters:
            return len(self.masters.split(','))
        else:
            return 0

    def mappings(self):
        if self.config:
            return self.config.get('application_mapping', None)
        else:
            return None

    def app(self):
        if self.apps:
            for s in self.apps:
                yield s.strip().split('\t')
        else:
            yield None

    def tasks(self):
        http = urllib3.PoolManager()
        response = None
        heads = {'Accept': 'text/plain'}
        i = 0
        master = self.master()
        while i < self.masters_size() and not response:
            try:
                i+=1
                url = self.scheme + next(master) + ':' + self.marathon_port + self.tasks_uri
                response = http.request('GET', url, headers=heads)
                if response.status != 200:
                    response = None
            except Exception as e:
                pass
        if response:
            data = response.data.decode('utf-8').strip()
            if data:
                self.apps = data.split('\n')
                yield from self.app()

    def endpoints(self):
        generated = False
        ret = "# <application_name> : <endpoint> : <microservice locations>"
        try:
            for r in self.tasks():
                generated = True
                app = r[0]
                upstreams = r[2:]
                e = {"endpoints": upstreams}
                data = self.mappings().get(app)
                if data:
                    data.update(e)
                    ret = ret + "\n\n" + data.get('upstream') + " : " + data.get('appname') + " : " + str(data.get('endpoints'))
        except:
            generated = False
            return generated, ret
        return generated, ret

    def generate(self):
        generated = False
        ret = ""
        try:
            for r in self.tasks():
                generated = True
                app = r[0]
                upstreams = r[2:]
                e = {"endpoints": upstreams}
                data = self.mappings().get(app)
                if data:
                    data.update(e)
                    ret = ret + "\n\n" + appfile.render(servername=data.get('appname', None), 
                                                        upstream=data.get('upstream', None), 
                                                        secured=data.get('secured', 'false'), 
                                                        access_file=data.get('access_by_lua_file', None), 
                                                        servers=data.get('endpoints', None),
                                                        debug_upstream=data.get('debug', 'false'))
        except:
            generated = False
            return generated, ret
        return generated, ret

if __name__ == "__main__":
    t = Tasks()
    _, ret = t.generate()
    print(ret)
