from jinja2 import Template

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
        listen 443 default_server ssl;
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

apps = {
    'app1.mesos.local': {
        'upstream': 'py_docker',
        'servers': ['192.168.250.104:34180','192.168.250.106:38111']
    },
    'app2.mesos.local': {
        'upstream': 'scala_docker',
        'servers': ['192.168.250.105:34777','192.168.250.106:32999']
    }
}

for app, config in sorted(apps.items()):
    with open('./{}.conf'.format(app), 'w+') as f:
        f.write(appfile.render(servername=app, upstream=config.get('upstream'), servers=config.get('servers')))
