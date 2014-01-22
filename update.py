#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json, requests, redis, csv
exp = 3600
r_server = redis.Redis('localhost')
session = requests.session()

i = 0
r = session.get('https://onionoo.torproject.org/details?running=true&country=ru&flag=exit&type=relay')
relays = json.loads(r.text)['relays']
for value in r_server.keys('as:*'):
  r_server.delete(value)
for value in r_server.keys('relay:*'):
  r_server.delete(value)
for relay in relays:
  if 'as_number' in relay:  
    r_server.sadd('as:' + relay['as_number'], relay['fingerprint'])
    db = {'latitude': relay['latitude'], 'longitude': relay['longitude'], 'as_name': relay['as_name']}
    r_server.hmset('relay:' + relay['fingerprint'], db)
    i = i + 1
print 'Updated. ' + str(i) + ' exit nodes.'

i = 0
for value in r_server.keys('registry:*'):
  r_server.delete(value)
registry = session.get('https://raw.github.com/zapret-info/z-i/master/dump.csv')
registry.encoding = 'cp1251'
reg = '\n'.join(registry.text.split('\n')[1:-1]).split('\n')
for line in reg:
  splited = line.split(';')
  db = {'authority': splited[3], 'base': splited[4], 'date': splited[5]}
  if ' | ' in splited[0]:
    db['url'] = []
    for url in splited[2].split(' | '):
      db['url'].append(url)
  else:
    db['url'] = splited[2]
  if ' | ' in splited[0]:
    db['ip'] = []
    for ip in splited[0].split(' | '):
      db['ip'].append(ip)
      r_server.sadd('registry:' + ip, i)
  else:
    db['ip'] = splited[0]
    r_server.sadd('registry:' + splited[0], i)
  r_server.sadd('registry:' + splited[1], i)
  db['ip'] = json.dumps(db['ip'])
  db['url'] = json.dumps(db['url'])
  r_server.hmset('registry:' + str(i), db)
  i = i + 1
  
print 'Updated registry. ' + str(i) + ' records'
