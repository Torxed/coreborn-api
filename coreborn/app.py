import psycopg2.extras
import ipaddress
import os
import hashlib
import pydantic
from typing import Union
from fastapi import FastAPI, Request, Header, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder

from .database.postgresql import Database
from .config import config
from .models import Position, AuthRedirect, UserInformation
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

def validate_access_token(access_token):
	if not isinstance(access_token, str):
		raise ValueError(f"Access token is not a string")
	if not len(access_token) == 64:
		raise ValueError(f"Access token is not of a valid length")
	if set(access_token) - set('abcdef0123456789'):
		raise ValueError(f"Access token contains illegal characters")

	if db.query("SELECT sessions.id FROM sessions, steam_users WHERE sessions.steam_user=steam_users.id AND sessions.access_token=%s AND steam_users.blocked='f'", (access_token, )):
		return True

	raise ValueError(f"Access token is not in database")

def is_blocked(user_id):
	if db.query("SELECT * FROM blocks WHERE steam_id=%s", (hashlib.sha256(user_id.encode()).hexdigest(), )):
		return True
	return False


def has_role(access_token, role):
	if db.query("""
		SELECT role FROM permissions
		WHERE role=%s AND steam_user=(
			SELECT id FROM steam_users WHERE blocked='f' AND id=(
				SELECT steam_user FROM sessions WHERE access_token=%s
			)
		)""",
		[
			role,
			access_token
		],
		force_list=True
	):
		return True

	return False


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
					SELECT positions.id, positions.x, positions.y FROM positions as positions, steam_users as steam_users, resources as resources
					WHERE (positions.resource=resources.id AND resources.name=%s)
					  AND (positions.steam_user=steam_users.id AND steam_users.blocked='f')
					  AND (positions.resource=resources.id AND resources.category=%s)""", (resource, category), force_list=True)
			}

	return result

@app.put("/api/resources/{resource}")
def add_resource(resource :str, pos :Position, request: Request, X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
		validate_resource(resource)
		validate_access_token(pos.access_token)
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	db.query("""
		INSERT INTO positions (resource, steam_user, x, y)
		VALUES (
			(
				SELECT id FROM resources WHERE name=%s
			),
			(
				SELECT steam_users.id FROM steam_users, sessions WHERE sessions.steam_user=steam_users.id AND sessions.access_token=%s AND steam_users.blocked='f'
			), %s, %s)""", (resource, pos.access_token, pos.x, pos.y))
	
	return {
		resource : {
			'icon' : None,
			'positions' : db.query("SELECT x, y FROM positions WHERE resource = (SELECT id FROM resources WHERE name=%s)", (resource, ), force_list=True)
		}
	}

@app.delete("/api/resources/{category}/{resource}/{identity}")
def add_resource(category :str, resource :str, identity :int, access_token :str, request: Request, X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
		validate_category(category)
		validate_resource(resource)
		validate_resource_id(category, resource, identity)
		validate_access_token(access_token)
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	ip_hash = hashlib.sha256(bytes(request.client.host or X_Real_IP, 'UTF-8')).hexdigest()

	db.query("""
		INSERT INTO node_removal (resource, steam_user)
		VALUES(
			(
				SELECT positions.id FROM resources, positions
				WHERE positions.resource=resources.id
				AND resources.name=%s
				AND resources.category=%s
				AND positions.id=%s
			),
			(
				SELECT steam_users.id FROM steam_users, sessions WHERE sessions.steam_user=steam_users.id AND sessions.access_token=%s AND steam_users.blocked='f'
			)
		)""",
		(resource, category, identity, access_token)
	)

	if (result := db.query(
		"""
		SELECT node_removal.id, node_removal.resource, resources.name, resources.category FROM node_removal, positions, resources
		WHERE node_removal.resource=(SELECT id FROM positions WHERE positions.id=%s)
		AND positions.id=%s
		AND resources.id=(SELECT positions.resource FROM positions WHERE positions.id=%s)
		""",
		(identity, identity, identity), force_list=True)
	):
		if len(result) >= 4 or (admin := has_role(access_token, 'admin')):
			print(f"Removing resource because: Reports is len({len(result) >= 4})>=4 or Admin=={admin}")
			db.query("""DELETE FROM positions WHERE positions.id=%s""", (result[0]['resource'], ))
			db.query("""DELETE FROM node_removal WHERE id=%s""", (result[0]['id'], ))

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


def hashsum(length=64):
	return hashlib.sha256(os.urandom(length)).hexdigest()


@app.get('/api/auth')
def get_resource(request: Request, auth_redirect :AuthRedirect = Depends(), X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	ip_hash = hashlib.sha256(bytes(request.client.host or X_Real_IP, 'UTF-8')).hexdigest()

	if auth_redirect.validate():
		user = UserInformation(key=config.steam.key, user_id=auth_redirect.user_id)
		access_token = hashsum()

		if is_blocked(auth_redirect.user_id):
			print(f"The steam user {user} is blocked")
			return {"status": "error", "message": "Could not validate steam claim"}

		db.query("""
			INSERT INTO steam_users (steam_id, displayname, avatar, avatarhash, primaryclanid)
			VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""", [
				auth_redirect.user_id,
				user.personaname,
				user.avatarfull,
				user.avatarhash,
				user.primaryclanid
			]
		)

		if db_info := db.query("SELECT id FROM steam_users WHERE steam_id=%s", (auth_redirect.user_id, )):
			if result := db.query("""
				INSERT INTO sessions (steam_user, ip, access_token)
				VALUES (%s, %s, %s) RETURNING access_token""", [
					db_info['id'],
					ip_hash,
					access_token
				]
			):
				return RedirectResponse(f"https://staging.coreborn.app/?access_token={result['access_token']}")


	return {"status": "error", "message": "Could not validate steam claim"}


@app.get('/api/whoami')
def get_resource(request: Request, access_token :str, X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
		assert type(access_token) is str
		assert len(access_token) == 64
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	if db_info := db.query("""
		SELECT steam_users.displayname, steam_users.avatar
		FROM steam_users, sessions WHERE sessions.steam_user=steam_users.id AND sessions.access_token=%s AND steam_users.blocked='f'""",
		(access_token,)
	):
		return db_info

	return {"status": "error", "message": "You are nobody at the moment, but you could be someone!"}


@app.get('/api/logout')
def get_resource(request: Request, access_token :str, X_Real_IP: str|None = Header(None)):
	try:
		ipaddress.ip_address(request.client.host or X_Real_IP)
		assert type(access_token) is str
		assert len(access_token) == 64
	except ValueError as error:
		print(error)
		return {'error': 'Invalid data sent to server'}

	db.query("DELETE FROM sessions WHERE access_token=%s", (access_token,))
	return {"status" : "logout"}