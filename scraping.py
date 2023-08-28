
import requests , re , random , os ,time
import asyncio
import codecs
import json
import logging
from bs4 import BeautifulSoup
from requests.exceptions import TooManyRedirects, ProxyError, ReadTimeout

class Scraping:
    def __init__(self , 
                data_file = 'helper.json', 
                pubproxy = 'http://pubproxy.com/api/proxy?port=8080,3128,3129,51200,8811,8089,33746,8880,32302,80,8118,8081',
                proxyscrape = 'https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=elite' ,
                free_p_l = 'https://free-proxy-list.net/',
                proxy_geonode = 'https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc',
                show_logs = False):

        self.data_file = data_file
        self.pubproxy = pubproxy
        self.proxyscrape = proxyscrape
        self.free_p_l = free_p_l
        self.proxy_geonode = proxy_geonode
        self.show_logs = show_logs
        self.init_logger()

        

        if not os.path.exists(data_file):
            self.init_all()
        else:
            # Check if the file is older than 1 day (to refresh proxies)
            file_time = os.path.getmtime(data_file)
            now = time.time()
            if (now - file_time) > 86400:
                os.remove(data_file)
                self.init_all()

        try:
            self.data = json.load(open(os.path.abspath(self.data_file) , 'r'))
        except:
            self.init_all()

    def init_all(self):
        self.init_helper()
        self.init_user_agents()
        self.init_proxies()
        self.save_data()
            
    # Initial helper data
    def init_helper(self):
        data = {}
        data['user_agents_links'] = [
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/windows/',
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/windows/2',
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/linux/',
        'https://developers.whatismybrowser.com/useragents/explore/software_name/safari/',
        'https://developers.whatismybrowser.com/useragents/explore/software_name/opera/',
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/chrome-os/',
        'https://developers.whatismybrowser.com/useragents/explore/hardware_type_specific/mobile/',
        'https://developers.whatismybrowser.com/useragents/explore/operating_platform_string/redmi/',
        'https://developers.whatismybrowser.com/useragents/explore/software_name/instagram/',
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/android/',
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/ios/',
        'https://developers.whatismybrowser.com/useragents/explore/operating_system_name/mac-os-x/'
        ]
        data['referrer'] = [
            "https://duckduckgo.com/",
            "https://www.google.com/",
            "http://www.bing.com/",
            "https://in.yahoo.com/",
            "https://www.azlyrics.com/",
            "https://www.dogpile.com/",
            "http://www.yippy.com",
            "https://yandex.com/"
            ]
            
        data['user_agents_scrap'] = []
        data['proxies'] = []
        data['working_proxies'] = []
        self.data = data
        self.save_data()

    # Scrap User Agents from List provided in JSON file
    def init_user_agents(self):
        for link in self.data['user_agents_links']:
            try:
                site=requests.get(link)
                if site.status_code == requests.codes.ok:
                    self.log(logging.INFO, 'Successfully got Link -> {}'.format(link))
                    html_soup = BeautifulSoup(site.text , 'html.parser')
                    response = html_soup.find_all('tr')
                    for res in response[1:]:
                        self.data['user_agents_scrap'].append(res.td.a.text)
                else:
                    self.log(logging.DEBUG, 'Status Code Mismatch -> {}'.format(link))
                time.sleep(random.randint(0,10))
            except Exception as E:
                self.log(logging.WARNING, 'Error Occured -> {} with Exception {}'.format(link,E))

    # Scrap proxies and filter duplicated proxies
    def init_proxies(self):
        self.data['proxies'] = self.get_pubproxy()
        self.data['proxies'] += self.get_proxyscrape()
        self.data['proxies'] += self.get_free_p_l()
        self.data['proxies'] += self.get_geonode()
        
        self.data['proxies'] = list(filter(None , self.data['proxies']))
    
    # Definign Logger for this class
    def init_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s : %(filename)s : %(funcName)s : %(levelname)s : %(message)s')
        self.file_handler = logging.FileHandler(os.path.abspath('proxies.log'))
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
    
    # Function to return Header when called
    def return_header(self):
        header = {
                'user-agent':self.data['user_agents_scrap'][random.randint(0,len(self.data['user_agents_scrap'])-1)] , 
                'referer':self.data['referrer'][random.randint(0,len(self.data['referrer'])-1)],
                'Upgrade-Insecure-Requests': '0' , 
                'DNT':'1' , 
                'Connection':'keep-alive',
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate, br','Accept-Language':'en-US,en;q=0.5'
        }
        return header

    # Function to return Proxy from list of working Proxies
    def return_proxy(self):
        try:
            if len(self.data['working_proxies'])>=5:
                return self.data['working_proxies'][random.randint(0,len(self.data['working_proxies'])-1)]
            return self.data['proxies'][random.randint(0,len(self.data['proxies'])-1)]
        except:
            # Return my rxternal IP
            return requests.get('https://api.ipify.org').content.decode('utf8')


    
    # Get proxies from Pubproxy
    def get_pubproxy(self , limit = 20):
        self.log(logging.INFO, 'Gettting Proxy from Pubproxy .. ')
        proxies = []
        for i in range(limit):
            try:
                proxy = requests.get(self.pubproxy).json()['data'][0]['ipPort']
                if proxy not in proxies:
                    proxies.append(proxy)
            except Exception as E:
                self.log(logging.ERROR, 'Something Went Wrong in Extracting from PubProxy .. ')
        self.log(logging.INFO, 'Called {} number of Proxies from PubProxy'.format(len(proxies)))
        return proxies

    # Get proxies from ProxyScrape
    def get_proxyscrape(self):
        try:
            response = requests.get(self.proxyscrape)
            if response.status_code == requests.codes.ok:
                proxies = response.text.split('\r\n')
                self.log(logging.INFO, 'Called {} number of Proxies from ProxyScrape'.format(len(proxies)))
                return proxies
            else:
                self.log(logging.ERROR, 'Status Code Mismatch From ProxyScrape .. ')
                return '0'
        except Exception as E:
            self.log(logging.ERROR, 'Something went Wrong in Extracting from ProxyScape .. -> {}'.format(E))
            return '0'

    # Get proxies from Free Proxy List
    def get_free_p_l(self):
            try:
                response = requests.get(self.free_p_l)
                if response.status_code==requests.codes.ok:
                    page_soup = BeautifulSoup(response.text, "html.parser")
                    textarea = page_soup.find('textarea').text
                    proxies = re.findall('\d+\.\d+\.\d+\.\d+\:\d+',textarea)
                    self.log(logging.INFO, 'Called {} number of Proxies from free-proxy-list'.format(len(proxies)))
                    return proxies
                else:
                    self.log(logging.ERROR, 'Status Code Mismatch From free-proxy-list .. ')
                    return '0'
            except Exception as E:
                self.log(logging.ERROR, 'Something went Wrong in Extracting from free-proxy-list .. -> {}'.format(E))
                return '0'

    # Get proxies from getnode
    def get_geonode(self):
        proxies = []
        try:
            response = requests.get(self.proxy_geonode)
            if response.status_code == requests.codes.ok:
                data = response.json()['data']
                for item in data:
                    proxies.append(item['ip'] + ':' + item['port'])
                self.log(logging.INFO, 'Called {} number of Proxies from GeoNode'.format(len(proxies)))
            else:
                self.log(logging.ERROR, 'Status Code Mismatch From GeoNode .. ')
        except Exception as E:
            self.log(logging.ERROR, 'Something went Wrong in Extracting from GeoNode .. -> {}'.format(E))
        return proxies

    # Update list of working proxies
    def update_proxies(self, proxy, ok):
        if ok:
            if proxy not in self.data['working_proxies']:
                self.data['working_proxies'].append(proxy)
        else:
            try:
                self.data['proxies'].remove(proxy)
            except:
                pass
            try:
                self.data['working_proxies'].remove(proxy)
            except:
                pass

    # To save json data in disk
    def save_data(self):
        try:
            with open(self.data_file, 'w') as outfile:
                json.dump(self.data, outfile, indent=4)
        except Exception as e:
            print("save_data", e)

    # Add log line
    def log(self, level, message):
        self.logger.log(level=level, msg=message)
        if self.show_logs:
            print(message)

    # Get response using proxy and user agents
    def get_page(self, url, raw_response = False):
        good_proxy = False
        send_proxy = None
        while not good_proxy:
            try:
                send_proxy = self.return_proxy()
                send_header = self.return_header()    

                response = requests.get(url, headers = send_header, proxies = {'http':send_proxy,'https':send_proxy}, timeout = 60)

                if response.status_code == requests.codes.ok:
                    good_proxy = True
                    self.update_proxies(send_proxy, True)
                    self.log(logging.INFO, 'Response {}.\t\t\t\tProxy: {}.\tURL: {}'.format(response.status_code, send_proxy, url))
                    if raw_response:
                        return response
                    else:
                        return BeautifulSoup(response.text,"html5lib")
                else:
                    self.log(logging.INFO, 'Response {}.\t\t\t\tProxy: {}.\tURL: {}'.format(response.status_code, send_proxy, url))
            except (ProxyError, TooManyRedirects, ReadTimeout):
                self.update_proxies(send_proxy, False)
                self.log(logging.ERROR, 'Proxy not working. Trying again...\tProxy: {}.\tURL: {}'.format(send_proxy, url))
            except Exception as e2:
                print("Exception Type:", type(e2))
                self.log(logging.ERROR, 'Error {}'.format(e2))
            finally:
                self.save_data()

        