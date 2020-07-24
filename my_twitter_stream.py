import os
import requests
import json
import time
from pprint import pprint
from requests.auth import AuthBase
from requests.auth import HTTPBasicAuth
import socket

stream_url = "https://api.twitter.com/labs/1/tweets/stream/filter"
rules_url = "https://api.twitter.com/labs/1/tweets/stream/filter/rules"

twitter_keys = json.load(open('info/application_keys.json'))['dwstream']
consumer_key = twitter_keys['API_key']
consumer_secret = twitter_keys['API_secret']

class BearerTokenAuth(AuthBase):
    
	def __init__(self, consumer_key, consumer_secret):
		self.bearer_token_url = "https://api.twitter.com/oauth2/token"
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.bearer_token = self.get_bearer_token()

	def get_bearer_token(self):
        	response = requests.post( self.bearer_token_url, \
                           auth=(self.consumer_key, self.consumer_secret), \
                           data={'grant_type': 'client_credentials'}, \
                           headers={'User-Agent': 'TwitterDevFilteredStreamQuickStartPython'});

        	if response.status_code is not 200:
            		raise Exception(f"Cannot get a Bearer token (HTTP %d): %s" % (response.status_code, response.text))

        	body = response.json()
        	return body['access_token']

	def __call__(self, r):
        	r.headers['Authorization'] = f"Bearer %s" % self.bearer_token
        	r.headers['User-Agent'] = 'TwitterDevFilteredStreamQuickStartPython'
        	return r
        
def get_all_rules(auth):
	response = requests.get(rules_url, auth=auth)

	if response.status_code is not 200:
		raise Exception(f"Cannot get rules (HTTP %d): %s" % (response.status_code, response.text))

	return response.json()
    
def delete_all_rules(rules, auth):
	if rules is None or 'data' not in rules: return None

	ids = list(map(lambda rule: rule['id'], rules['data']))

	payload = {
		'delete': {
        		'ids': ids
        	}
    	}

	response = requests.post(rules_url, auth=auth, json=payload)

	if response.status_code is not 200:
        	raise Exception(f"Cannot delete rules (HTTP %d): %s" % (response.status_code, response.text))
        
def set_rules(rules, auth):
	if rules is None: return

	payload = {
		'add': rules
	}

	response = requests.post(rules_url, auth=auth, json=payload)

	if response.status_code is not 201:
        	raise Exception(f"Cannot create rules (HTTP %d): %s" % (response.status_code, response.text))
	return
 
def stream_connect(auth,json_name,wait_seconds=30):
	tweets = []
	print("Reading existing data")
	with open(json_name,'r') as rfile:
		tweets = json.load(rfile)
	try:        
		print("Gathering")
		response = requests.get(stream_url, auth=auth, stream=True)
    
		for response_line in response.iter_lines():
			if response_line:
				tweet=json.loads(response_line)
				tweets.append(tweet)
				if len(tweets) > 1000000:
					raise ValueError()
	except KeyboardInterrupt:
		print("Saving to json")
		with open(json_name,"w") as fwrite:
			json.dump(tweets,fwrite,indent=1)
        	#print('end')
		return 'end'
        	
	except requests.exceptions.ConnectionError:
		#print('Connection error')
		print("Saving to json")
		with open(json_name,"w") as fwrite:
			json.dump(tweets,fwrite,indent=1)
		return 'connection error'
        	
	except socket.timeout:
		#print('Download error')
		print("Saving to json")
		with open(json_name,"w") as fwrite:
			json.dump(tweets,fwrite,indent=1)
		return 'download error'
		
	except ValueError:
		print("Saving to json")
		with open(json_name,"w") as fwrite:
			json.dump(tweets,fwrite,indent=1)
		return 'toolong'
		
	except:
		print("Saving to json")
		with open(json_name,"w") as fwrite:
			json.dump(tweets,fwrite,indent=1)
		return 'unexpected error'
		
	print("Saving to Sjson")
	with open(json_name,"w") as fwrite:
        	json.dump(tweets,fwrite,indent=1)	
	return 'closed'

def setup_rules(auth,rules):
	current_rules = get_all_rules(auth)
	delete_all_rules(current_rules, auth)
	set_rules(rules, auth)
