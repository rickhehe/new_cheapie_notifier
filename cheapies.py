import appdaemon.plugins.hass.hassapi as hass

import re
from datetime import datetime
import csv

import requests
from bs4 import BeautifulSoup

URL = r'https://www.cheapies.nz/deals'

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}

HISTORY = '/config/appdaemon/apps/cheapies/history.csv'

INTETERESTED_PIECE = re.compile(
    r'''
    keyboard|mouse|ergonomic|ergodox|moonlander|logi
    |
    patagonia|black ?diamond|torpedo7
    |
    reolink|switch|makita|garmin|greenworks|hue
    |
    nespresso
    |
    gull|petrol|\Wfuel|gas|solar
    |
    dell|microsoft|data warehouse|earbuds|headphone
    ''',
    flags=re.I|re.X
)

NOT_INTETERESTED_PIECE = re.compile(
    r'''
    \[pc|ps[45]|\[steam|xbox|playstation
    |
    \[auckland
    |
    oppo|huawei|oneplus|anko|powerline|xiaomi
    |
    hello.?fresh|my ?food ?bag
    ''',
    flags=re.I|re.X
)

class Cheapies(hass.Hass):

    def initialize(self):

        self.log(f'{__name__} is live') 
        
        self.run_every(
            self.stream,
            'now',
            60
        )

    def get_response(self, url):

        return requests.get(
            url=url,
            headers=HEADERS
        )

    def get_soup(self, url):
        
        r = self.get_response(url)
        
        return BeautifulSoup(r.content, 'html.parser')

    def send_email_to(self, title='rickhehe', message=''):
        
        self.call_service(
            'notify/send_email_to_rick_notifier',
            message=message,
            title=title,
        )

    @property
    def anchor(self):
        
        # Don't be surprized if it's just one line.
        # Bottom line is the most recent line.
        try:
            with open(HISTORY, 'r', newline='') as f:

                reader = csv.DictReader(f)
                
                node_ids = [int(row['node_id']) for row in reader]

                return node_ids[-1]

        except Exception as e:

            print(f'error {e}')
            return 35650

    def set_anchor(self, a_record):
        
        # Append recorcd to HISTORY.
        with open(HISTORY, 'a', newline='') as f:

            fieldnames = ['node_id', 'subject', 'content', 'timestamp', 'url']
            writer =csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(a_record)

    def get_h2s(self):

        soup = self.get_soup(URL)

        h2s = soup.find_all('h2', class_='title')
    
        return h2s

    def get_content(self, link):

        try:
            soup = self.get_soup(link)

            content = soup.find('div', class_='content')
    
            return content.text.strip()

        except Exception as e:
            return e

    def stream(self, kwargs):

        h2s = self.get_h2s()

        # Iterate from the smallest number.
        for i,tem in enumerate(reversed(h2s)):
            
            node_id = int(tem.attrs['id'].replace('title',''))

            if node_id > self.anchor:

                self.log(f'Node ID {node_id} > anchor {self.anchor}')

                title = tem.text.strip()
                url = f'https://cheapies.nz/node/{node_id}'
                content = self.get_content(url) 

                self.set_anchor(
                    {
                        'node_id':node_id,
                        'subject':f'Cheapie {node_id} {title}',
                        'content':f'{content}',
                        'timestamp':datetime.now(),
                        'url':url
                    }
                )

                # If not interested, send a notification with different style.
                match = NOT_INTETERESTED_PIECE.findall(title)
                if match:
                    title= 'NOT INTERESTED'
                    x = '\n'.join(match)
                    content = f'{x}\n\n{content}'

                match = INTETERESTED_PIECE.findall(title)
                if match:
                    title = f'INTERESTED {title}'
                    x = '\n'.join(match)
                    content = f'{x}\n\n{content}'
                    
                    
                self.log(f'Anchor {self.anchor}, Cheapie {node_id}, sending notification')

                self.send_email_to(
                    title=f'Cheapie {node_id} {title}',
                    message=f'{url}\n\n{content}'
                )
