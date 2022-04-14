import boto3

import re
from datetime import datetime
import json

import requests
from bs4 import BeautifulSoup

URL = r'https://www.cheapies.nz/deals'

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}

EMAILER = 'TBC'

# Haven't started use filters yet.
INTETERESTED_PIECE = re.compile(
    r'''
    ''',
    flags=re.I|re.X
)
 
client_lambda = boto3.client('lambda')

client_dynamodb = boto3.client('dynamodb')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('cheapies')

class Cheapies():

    def __init__(self, anchor):

        self.anchor = anchor

    def get_response(self, url):

        return requests.get(
            url=url,
            headers=HEADERS
        )

    def get_soup(self, url):
        
        r = self.get_response(url)
        
        return BeautifulSoup(r.content, 'html.parser')

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

    def stream(self):

        h2s = self.get_h2s()

        for i,tem in enumerate(reversed(h2s)):
            
            node_id = int(tem.attrs['id'].replace('title',''))

            if node_id > self.anchor:

                title = tem.text.strip()
                url = f'https://cheapies.nz/node/{node_id}'
                content = self.get_content(url)

                data = {
                    'node_id':node_id,
                    'subject':f'Cheapie {node_id} {title}',
                    'content':f'{url}\n\n{content}',
                    'url':url,
                }
                
                yield data

def get_anchor():

    # There must be a better way.
    
    data = client_dynamodb.scan(
        TableName='cheapies',
        AttributesToGet=['node_id'],
    )

    node_ids = [
        int(v)
        for item in data['Items']
        for _,v in item['node_id'].items()
    ]
    
    anchor = max(node_ids)
    
    return anchor

def lambda_handler(event,context):
 
    anchor = get_anchor()

    c = Cheapies(anchor)
    
    for x in c.stream():
        
        table.put_item(Item=x)
        
        x.pop('node_id')
        x.pop('url')
        x['to']='rick.notifier@gmail.com'
        
        y = json.dumps(x, default=str)

        response = client_lambda.invoke(
            FunctionName=EMAILER,
            InvocationType='RequestResponse',
            Payload=y
        )
