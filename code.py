#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import web, bcrypt, redis, json, requests, dns.resolver, re, M2Crypto, cgi
from urlparse import urlsplit
from zbase62 import zbase62
web.config.debug = False
r_server = redis.Redis('localhost')
urls = (
  '/', 'index',
  '/check', 'check',
  '/logout', 'logout',
  '/register', 'register'
)
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'))
render = web.template.render('templates/', base='layout',)

proxies = {
  "http": "http://localhost:8118",
  "https": "http://localhost:8118",
}
checkstr = [
  u'Запрашиваемая страница заблокирована на основании <br> Постановления Правительства от 26.10.2012 №1101 <br>',
  u'<h1><strong>Уважаемые пользователи!<br/><br/>Мы приносим свои извинения, но&nbsp;доступ к&nbsp;запрашиваемому ресурсу ограничен.</strong></h1>',
  u'<p>Уважаемый абонент,<br /> Вы хотите перейти по адресу, который внесён в единый реестр запрещённых сайтов или доступ к нему <span id="more">заблокирован</span> судебным решением.</p>',
  u'<div style="font-size: 13px; margin-top: 25px; font-weight: normal;">Адрес сайта Единого реестра доменных имен, указателей, страниц сайтов в сети "Интернет" и сетевых адресов, позволяющих идентифицировать сайты</br> в сети "Интернет", содержащие информацию, распространение которой в Российской Федерации запрещено: <a href="http://zapret-info.gov.ru/" target="_blank">zapret-info.gov.ru</a></br>Адрес Реестра нарушителей авторских прав: <a href="http://nap.rkn.gov.ru/reestr/" target="_blank">http://nap.rkn.gov.ru/reestr/</a>',
  u'<img src="http://212.1.224.79/stop.jpg" width="672" height="180" alt="Внимание!" />',
  u'<p>Access control configuration prevents your request from being allowed at this time. Please contact your service provider if you feel this is incorrect.</p>',
  u'<p>Сайт, который вы хотите посетить, внесен в <u><a href="http://eais.rkn.gov.ru" style="color:#FF6600">единый',
  u'либо в <a href="http://eais.rkn.gov.ru/" target="_blank">едином реестре</a>',
  u'<p>Доступ к запрашиваемому Вами Интернет-ресурсу ограничен в соответствии с требованиями законодательства. Дополнительную информацию можно получить на сайте <a href="http://www.zapret-info.gov.ru./">www.zapret-info.gov.ru</a>.</p>',
  u'материалов</a>, доступ к нему закрыт на основании решения суда РФ.',
  u'<p>В соответствии с требованиями законодательства доступ к запрашиваемому Интернет-ресурсу <br>закрыт.</p>',
  u'<p><b>В соответствии с требованиями законодательства Российской Федерации доступ к запрашиваемому Интернет-ресурсу',
  u'<h5>Ссылка заблокирована по решению суда</h5><br><br><a href=\'http://ttk.ru/\'>ЗАО "Компания ТрансТелеКом"</a>'
  u'Причину блокировки можно посмотреть в <a href="http://eais.rkn.gov.ru/">Едином Реестре</a>',
  u':80/f/accept/\' not found...',
  u'<a href="http://zapret-info.gov.ru"/><b>Постановление Правительства Российской Федерации от 26 октября 2012 г. N 1101</b>',
  u'<p>Your cache administrator is <a href="mailto:webmaster?subject=CacheErrorInfo%20-%20ERR_CONNECT_FAIL&amp;body=CacheHost%3A%20atel76.ru%0D%0AErrPage%3A%20ERR_CONNECT_FAIL%0D%0AErr%3A%20(110)%20Connection%20timed%20out%0D%0A',
  u'<h5><a href=\'http://eais.rkn.gov.ru/\'>Ссылка заблокирована <br>в соответствии с законодательством РФ</a></h5><br><br><a href=\'http://ttk.ru/\'>ЗАО "Компания ТрансТелеКом"</a>',
  u'<div class="section">\n          Доступ к запрашиваемому вами интернет-ресурсу ограничен в \n          соответствии с требованиями Законодательства Российской Федерации.',
  u'<p>Доступ к запрашиваемому Вами Интернет-ресурсу ограничен по требованию правоохранительных органов в соответствии с законодательством и/или на основании решения суда.</p>',
  u'<p>Доступ к запрашиваемому Вами Интернет-ресурсу ограничен в соответствии с требованиями законодательства. Дополнительную информацию можно получить на сайте <a href="/PDATransfer.axd?next_url=http%3a%2f%2fwww.zapret-info.gov.ru.%2f">www.zapret-info.gov.ru</a>.</p>'
]


class index:
    def GET(self):
      if session.get('login', False):
        return render.index()
      else:
        return render.login('')
    def POST(self):
      data = web.input()
      if not all(x in data for x in ('username', 'password')):
        raise web.seeother('/')
      if 'login' not in session:
        session.login = 0
      hashed = r_server.get('user:' + data.username)
      if hashed is None:
        session.login = 0
        return render.login('No such user')
      if bcrypt.hashpw(data.password.encode('utf-8'), hashed) == hashed:
        session.login = 1
        return render.index()
      else:
        session.login = 0
        return render.login('Wrong password')

class logout:
  def GET(self):
    session.login = 0
    raise web.seeother('/')

class check:
  def GET(self):
    if not session.get('login', False):
      raise web.seeother('/')
    data = web.input()
    if not 'url' in data:
      return 'Wrong parameters'
    results = {}
    results['results'] = []
    try:
      url = urlsplit(data.url)
    except:
      return 'Not a valid URL'
    s = requests.Session()
    s.proxies=proxies
    results['ip'] = []
    try:
      answers = dns.resolver.query(url.hostname, 'A')
    except:
      return 'Can\'t get A records of hostname'
    results['registry'] = []
    regnumbers = []
    for rdata in answers:
      results['ip'].append(rdata.address)
      regcheck = r_server.smembers('registry:' + rdata.address)
      if regcheck:
        regnumbers = regnumbers + list(regcheck)
    regcheck = r_server.smembers('registry:' + url.hostname)
    if regcheck:
      regnumbers = regnumbers + list(regcheck)
    for value in list(set(regnumbers)):
      info = r_server.hgetall('registry:' + value)
      results['registry'].append({
        'ip': json.loads(info['ip']),
        'url': json.loads(info['url']),
        'authority': info['authority'],
        'base': info['base'],
        'date': info['date']
      })
    for value in r_server.keys('as:*'):
      fingerprint = r_server.srandmember(value).replace('relay:','')
      s.headers.update({'host': url.hostname})
      as_id = value.replace('as:','')
      try:
        r = s.get(url.scheme + '://' + url.hostname + '.' + fingerprint + '.exit' + url.path + '?' + url.query, verify=False)
        print as_id
        status = r.status_code
        if status == 200:
          if any(x in r.text for x in checkstr):
            blocked = 'yes'
          else:
            blocked = 'no'
          r.text
        else:
          blocked = 'maybe'
      except:
        status = 'fail'
        blocked = 'dunno'
      info = r_server.hgetall('relay:' + fingerprint)
      results['results'].append({
        'blocked': blocked,
        'status': status,
        'fingerprint': fingerprint,
        'as_name': info['as_name'],
        'lat': info['latitude'],
        'lon': info['longitude']
      })
    
    return json.dumps(results)

class register:
  def GET(self):
    data = web.input()
    if not 'email' in data:
      return 'Wrong parameters'
    if not re.match(r'[^@]+@[^@]+\.[^@]+', data.email):
      return 'This is not email'
    if r_server.sismember('nonregistred',data.email):
      password = zbase62.b2a(M2Crypto.m2.rand_bytes(20))
      hashed = bcrypt.hashpw(password, bcrypt.gensalt())
      r_server.set('user:' + data.email,hashed)
      r_server.srem('nonregistred',data.email)
      return render.register(password,cgi.escape(data.email))
    else: 
      return 'No such email'

if __name__ == "__main__":
  app.run()
