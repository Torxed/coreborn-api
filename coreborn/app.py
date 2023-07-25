import psycopg2.extras
import ipaddress
import os
import hashlib
from typing import Union
from fastapi import FastAPI, Request

from .database.postgresql import Database
from .config import config
from .models import Position
from .startup import init_data

app = FastAPI()

db = Database(dbname=config.db.database, user=config.db.username, password=config.db.password, host=config.db.hostname)
db.init()

def validate_resource(resource, allow_wildcard=False):
	if resource == '*':
		return True

	for category in init_data:
		if resource in init_data[category]:
			return True

	raise ValueError(f"Resource does not exist in resource list")

@app.get("/api/resources/{resource}")
def read_root(resource :Union[str, None] = None):
	try:
		validate_resource(resource, allow_wildcard=True)
	except ValueError:
		return {'error': 'Invalid data sent to server'}

	result = {}
	for category in {row['category'] for row in db.query("SELECT DISTINCT(category) FROM resources")}:
		result[category] = {}

		for resource in init_data[category]:
			result[category][resource] = {
				'icon' : None,
				'color' : getattr(config.colors, resource, '#F444FF'),
				'visible' : True,
				'positions' : db.query("""
					SELECT positions.x, positions.y FROM positions as positions, ip_addresses as ip_addresses, resources as resources
					WHERE (positions.resource=resources.id AND resources.name=%s)
					  AND (positions.ip=ip_addresses.id AND ip_addresses.blocked='f')
					  AND (positions.resource=resources.id AND resources.category=%s)""", (resource, category), force_list=True)
			}

	return result

@app.put("/api/resources/{resource}")
def read_item(resource :str, pos :Position, request: Request):
	try:
		ipaddress.ip_address(request.client.host)
		validate_resource(resource)
	except ValueError:
		return {'error': 'Invalid data sent to server'}

	ip_hash = hashlib.sha256(bytes(request.client.host, 'UTF-8')).hexdigest()

	db.query("INSERT INTO ip_addresses (ip, blocked) VALUES(%s, false) ON CONFLICT DO NOTHING", (ip_hash, ))
	ip_info = db.query("SELECT id, blocked FROM ip_addresses WHERE ip=%s", (ip_hash, ))

	if not ip_info or ip_info.get('blocked'):
		return {'error': 'IP has been blocked due to spammish behavior'}

	db.query("INSERT INTO positions (resource, x, y, ip) VALUES((SELECT id FROM resources WHERE name=%s), %s, %s, %s)", (resource, pos.x, pos.y, ip_info.get('id')))
	
	return {
		resource : {
			'icon' : None,
			'positions' : db.query("SELECT x, y FROM positions WHERE resource = (SELECT id FROM resources WHERE name=%s)", (resource, ), force_list=True)
		}
	}