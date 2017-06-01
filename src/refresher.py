from jinja2 import Template
import urllib3
import os
import json

template = '''
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
            # for relative calls from upstream servers
            proxy_set_header Host $http_host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-M-Secure "true";
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://{{ upstream }}/$2$is_args$args;
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
        self.config_dir = os.getenv('CONFIG_DIR', os.path.dirname(os.path.realpath(__file__)))
        self.apigw_config_dir = os.getenv('APIGW_CONFIG_DIR', self.config_dir)
        self.tmp_dir = os.getenv('TMP_DIR', '/tmp')
        self.apps = None
        try:
            with open(self.config_dir + '/config.json', 'r') as f:
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
                print("getting ... " + url)
                response = http.request('GET', url, headers=heads)
            except Exception as e:
                pass
        if response:
            self.apps = response.data.decode('utf-8').strip().split('\n')
            yield from self.app()
        else:
            yield None

    def generate(self):
        for r in self.tasks():
            app = r[0]
            upstreams = r[2:]
            e = {"endpoints": upstreams}
            data = t.mappings().get(app)
            if data:
                data.update(e)
                print(app + ': ' + str(data))
                with open(self.tmp_dir+'/{}.conf'.format(data.get('appname')), 'w+') as f:
                    f.write(appfile.render(servername=data.get('appname'), upstream=data.get('upstream'), servers=data.get('endpoints')))
                os.rename(self.tmp_dir+'/{}.conf'.format(data.get('appname')), self.apigw_config_dir+'/{}.conf'.format(data.get('appname')))

if __name__ == "__main__":
    t = Tasks()
    t.generate()    
