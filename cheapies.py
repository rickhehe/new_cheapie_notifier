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
        .
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
        try:
            with open(HISTORY, 'r', newline='') as f:

                reader = csv.DictReader(f)

                node_ids = [int(row['node']) for row in reader]
                return int(node_ids[-1])

        except Exception as e:

            print(f'error {e}')
            return 30240

    def set_anchor(self, a_record):
        
        with open(HISTORY, 'a', newline='') as f:
            fieldnames = ['node', 'timestamp']
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

        for i in reversed(h2s):
            
            node = int(i.attrs['id'].replace('title',''))

            if node > self.anchor:

                self.call_service(
                    'tts/google_translate_say',
                    entity_id='media_player.dummy',
                    message='just buy it'
                )

                self.log(f'node {node} > anchor {self.anchor}')
 
                self.set_anchor(  # append might be a better verb here
                    {'node':node, 'timestamp':datetime.now()}
                )

                title = i.text.strip()
                link = f'https://cheapies.nz/node/{node}'
                message = self.get_content(link)

                self.send_email_to(
                    title=f'Cheapies {node} {title}',
                    message=message
                )
        
