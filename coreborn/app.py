import psycopg2.extras
import ipaddress
import os
import hashlib
import pydantic
from typing import Union
from fastapi import FastAPI, Request, Header, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from .database.postgresql import Database
from .config import config
from .models import Position, AuthRedirect
from .startup import init_data

app = FastAPI()

@app.exception_handler(pydantic.ValidationError)
async def validation_exception_handler(request: Request, exc: pydantic.ValidationError):
	print(exc.errors())
	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
		content=jsonable_encoder({"detail": exc.errors(), "Error": "Entity not permitted"}),
	)

db = Database(dbname=config.db.database, user=config.db.username, password=config.db.password, host=config.db.hostname)
db.init()

def validate_category(category):
	if category in init_data:
		return True

	raise ValueError(f"Resource category does not exist")

def validate_resource(resource, allow_wildcard=False):
	if resource == '*':
		return True

	for category in init_data:
		if resource in init_data[category]:
			return True

	raise ValueError(f"Resource does not exist in resource list")

def validate_resource_id(category, resource, identity):
	validate_category(category)
	validate_resource(resource)
	# TODO: Should probably add a strict check that the ID matches the above
	# category and resource type as well.
	if db.query("SELECT id FROM positions WHERE id=%s", (identity, )):
		return True

	raise ValueError(f"Resource ID does not exist")

@app.get("/api/resources/{resource}")
def get_resource(resource :Union[str, None] = None):
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
					SELECT positions.id, positions.x, positions.y FROM positions as positions, ip_addresses as ip_addresses, resources as resources
					WHERE (positions.resource=resources.id AND resources.name=%s)
					  AND (positions.ip=ip_addresses.id AND ip_addresses.blocked='f')
					  AND (positions.resource=resources.id AND resources.category=%s)""", (resource, category), force_list=True)
			}

	return result

@app.put("/api/resources/{resource}")
def add_resource(resource :str, pos :Position, request: Request, X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
		validate_resource(resource)
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	ip_hash = hashlib.sha256(bytes(request.client.host or X_Real_IP, 'UTF-8')).hexdigest()

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

@app.delete("/api/resources/{category}/{resource}/{identity}")
def add_resource(category :str, resource :str, identity :int, request: Request, X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
		validate_category(category)
		validate_resource(resource)
		validate_resource_id(category, resource, identity)
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	ip_hash = hashlib.sha256(bytes(request.client.host or X_Real_IP, 'UTF-8')).hexdigest()

	db.query("INSERT INTO ip_addresses (ip, blocked) VALUES(%s, false) ON CONFLICT DO NOTHING", (ip_hash, ))
	ip_info = db.query("SELECT id, blocked FROM ip_addresses WHERE ip=%s", (ip_hash, ))

	if not ip_info or ip_info.get('blocked'):
		return {'error': 'IP has been blocked due to spammish behavior'}

	db.query("""
		INSERT INTO node_removal (resource, ip)
		VALUES(
			(
				SELECT positions.id FROM resources, positions
				WHERE positions.resource=resources.id
				AND resources.name=%s
				AND resources.category=%s
				AND positions.id=%s
			),
			%s
		)""",
		(resource, category, identity, ip_info.get('id'))
	)

	if (result := db.query(
		"""
		SELECT node_removal.resource, resources.name, resources.category FROM node_removal, positions, resources
		WHERE node_removal.resource=(SELECT id FROM positions WHERE positions.id=%s)
		AND positions.id=%s
		AND resources.id=(SELECT positions.resource FROM positions WHERE positions.id=%s)
		""",
		(identity, identity, identity), force_list=True)
	):
		if len(result) >= 4 or (request.client.host or X_Real_IP) == '127.0.0.1':
			print(f"Removing resource because: Reports is {len(result) >= 4}>=4 or Admin=={(request.client.host or X_Real_IP) == '127.0.0.1'}")
			db.query("""
				DELETE FROM positions WHERE positions.id=%s
			""", (result[0]['resource'], ))
			return {
				"status": "resource deleted"
			}
		else:
			return {
				"status": "resource deletion added, waiting for moderator approval"
			}

	return {
		"status": "error"
	}


@app.get('/auth')
def get_resource(auth_redirect : AuthRedirect):
	print(auth_redirect)

	return result