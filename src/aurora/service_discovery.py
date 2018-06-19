from kazoo.client import KazooClient
from kazoo import client
import time
import json
import os

zookeeper_hosts = os.getenv('ZOOKEEPER_HOSTS', 'm1.example.com:2181,m2.example.com:2181,m3.example.com:2181')
zookeeper_services = os.getenv('ZOOKEEPER_SERVICES', '/aurora/vagrant/test/docker-nginx,/aurora/vagrant/test/wont-show')

zk = KazooClient(hosts=zookeeper_hosts)
zk.start()

services = zookeeper_services.split(',')

node_data = {}
endpoints = []

def set_endpoint(endpoint):
    global endpoints
    endpoints.append(endpoint)

def set_service(service):
    global node_data
    node_data = service

def get_service_data(path=None, shard=None):
    @client.DataWatch(zk, path)
    def my_func(data, stat):
        result = json.loads(data)
        set_service(result)

def add_service_watch(path=None):
    @client.ChildrenWatch(zk, path)
    def my_func(stat):
        service_definition = [path, '<>']
        for node in stat:
            shard_data = path + "/" + node
            get_service_data(path=shard_data, shard=node)
            service_definition.append(node_data.get('serviceEndpoint').get('host')+':'+str(node_data.get('serviceEndpoint').get('port')))
        set_endpoint(service_definition)

def generate_endpoints(service):
    add_service_watch(service)

def get_endpoints(services=None):
    global endpoints
    endpoints = []
    for service in services:
        generate_endpoints(service)
    return endpoints

def get_endpoint(service=None):
    services = [service]
    return get_endpoints(services)

# get_endpoints(services=services)
# print(endpoints)
