import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

#total url to parse
total_user = 10

#base url to parse
base_profile_url = 'http://vozforums.com/member.php?u=';

#host and port mongodb
host = 'localhost'
port = 27017


proxy_dict = {}
timeout = 12

def get_mongo_connection():
  client = MongoClient(host, port)
  #select database
  db = client['user_voz']
  return db

def get_password():
  return 123456789;

def get_proxy():
  global proxy_dict
  proxy_dict = {
    "http" : "http://" + proxies.pop()
  }
  return proxy_dict

def get_parsed_html(profile_url):
  try:
    #if proxy is not set, set proxy
    global proxy_dict
    global timeout
    if not proxy_dict:
      proxy_dict = get_proxy()

    print "Use proxy: " + str(proxy_dict)
    r = requests.get(profile_url, proxies=proxy_dict, timeout=timeout)
  except requests.exceptions.Timeout:
    raise Exception("Timeout")
  except requests.exceptions.RequestException as e:
    raise Exception("Error", e.args)
  else:
    return r.text
  

def get_all_username():
  print "Get mongodb connection"
  mongo_db = get_mongo_connection()
  #select collection
  mongo_collection = mongo_db['user']
  for x in xrange(mongo_collection.find().count(), total_user):
    profile_url = base_profile_url + str(x)
    #html = urllib2.urlopen(profile_url)
    print "Parsing url: " + profile_url
    html = ''
    #try to parse html
    while not html:
      try:
        html = get_parsed_html(profile_url)
      except Exception as e:
        print "Error: " + str(e.args)
        #remove proxy cannot use
        global proxy_dict
        proxy_dict = {}
    
    #parse html
    try:
      parsed_html = BeautifulSoup(html)
      username = parsed_html.body.find('div', {'id' : 'main_userinfo'}).find('h1').text.strip()
      print "Username parsed: " + username
      mongo_collection.insert({'username' : username})
    except:
      print "Error occured"
      print "Pass user id: " + str(x)
      pass

def main():
  get_all_username();

if __name__ == '__main__':
  main()


#payload = {
#  'do'                      : 'login',
#  'api_cookieuser'          : 0,
#  'securitytoken'           : 'guest',
#  'api_vb_login_md5password': '7de8482cdbb8177365a8c5d4b53a74cd',
#  'api_vb_login_md5password_utf' : '7de8482cdbb8177365a8c5d4b53a74cd',
#  'api_vb_login_password'   : 'bao123456',
#  'api_vb_login_username'   : 'nguyenhoaibao',
#  'api_salt'                : 'LCGHW3JFY6KNEN5O'
#}

#s = requests.session()

#r = s.post('http://vozforums.com/vbdev/login_api.php', data=payload)
#print r.text.encode('utf-8')

#res = r.json()

#if res['captcha']:
#  payload['api_captcha'] = res['captcha'];
#  r = s.post('http://vozforums.com/vbdev/login_api.php', data=payload)
#  res = r.json()
#  if res['userinfo']['userid']:
#    r = s.get('http://vozforums.com');
#    with open('login_response.txt', 'w') as f:
#      f.write(r.text.encode('utf-8'))
