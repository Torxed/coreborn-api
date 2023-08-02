import json
import urllib.parse
import urllib.request
from fastapi import Query
from pydantic import BaseModel, validator, Field, root_validator
from pydantic.dataclasses import dataclass


class Position(BaseModel):
	x :float
	y :float
	access_token :str

	@validator('x', each_item=True)
	def validate_x(cls, v):
		if isinstance(v, float) and v > 0.0 and v < 1.0:
			return v
		raise ValueError(f"Position() is off the charts")

	@validator('y', each_item=True)
	def validate_y(cls, v):
		if isinstance(v, float) and v > 0.0 and v < 1.0:
			return v
		raise ValueError(f"Position() is off the charts")


@dataclass
class AuthRedirect:
	openid_ns :str = Query(..., alias="openid.ns")
	openid_mode :str = Query(..., alias="openid.mode")
	openid_op_endpoint :str = Query(..., alias="openid.op_endpoint")
	openid_claimed_id :str = Query(..., alias="openid.claimed_id")
	openid_identity :str = Query(..., alias="openid.identity")
	openid_return_to :str = Query(..., alias="openid.return_to")
	openid_response_nonce :str = Query(..., alias="openid.response_nonce")
	openid_assoc_handle :int = Query(..., alias="openid.assoc_handle")
	openid_signed :set = Query(..., alias="openid.signed")
	openid_sig :str = Query(..., alias="openid.sig")

	def __post_init__(self):
		if self.openid_signed and isinstance(self.openid_signed, set) and len(self.openid_signed) == 1:
			self.raw_signed = self.openid_signed.pop()
			self.openid_signed = set(self.raw_signed.split(','))

			self._valid = None

	@property
	def user_id(self):
		return self.openid_claimed_id.rsplit('/', 1)[1]

	@root_validator(pre=True)
	def validate_values(cls, values):
		"""
		We validate all the values sent back from a steam auth redirect,
		we also convert from the given alias to the valid python syntax for
		variable names.

		Ideally we should probably create AuthRedirect.openid.<variable> as a sub instance.
		"""
		if not (v := values.get('openid_ns')) or v != 'http://specs.openid.net/auth/2.0':
			raise ValueError('Invalid NS returned')
		else:
			values["openid.ns"] = v
		if not (v := values.get('openid_mode')): # or v != 'http://specs.openid.net/auth/2.0':
			raise ValueError('Invalid Mode returned')
		else:
			values["openid.mode"] = v
		if not (v := values.get('openid_op_endpoint')) or v != 'https://steamcommunity.com/openid/login':
			raise ValueError('Invalid OP Endpoint returned')
		else:
			values["openid.op_endpoint"] = v
		if not (v := values.get('openid_claimed_id')) or v.startswith('https://steamcommunity.com/openid/id/') is False:
			raise ValueError('Invalid Claimed ID returned')
		else:
			values["openid.claimed_id"] = v
		if not (v := values.get('openid_identity')) or v.startswith('https://steamcommunity.com/openid/id/') is False:
			raise ValueError('Invalid Identity returned')
		else:
			values["openid.identity"] = v
		if not (v := values.get('openid_return_to')) or v != 'https://staging.coreborn.app/api/auth':
			raise ValueError('Invalid Return To path returned')
		else:
			values["openid.return_to"] = v
		if not (v := values.get('openid_response_nonce')) or isinstance(v, str) is False:
			raise ValueError('Invalid Nonce returned')
		else:
			values["openid.response_nonce"] = v
		if not (v := values.get('openid_assoc_handle')) or isinstance(v, int) is False:
			raise ValueError('Invalid Associated Handle returned')
		else:
			values["openid.assoc_handle"] = v
		# Verify that the returned signed items are precent, and only those
		if not (v := values.get('openid_signed')) or v ^ {'signed', 'op_endpoint', 'claimed_id', 'identity', 'return_to', 'response_nonce', 'assoc_handle'}:
			raise ValueError('Invalid Signed returned')
		else:
			values["openid.signed"] = v
		if not (v := values.get('openid_sig')) or isinstance(v, str) is False:
			raise ValueError('Invalid Signature returned')
		else:
			values["openid.sig"] = v
		return values

	def validate(self):
		if self._valid is None:
			url = "https://steamcommunity.com/openid/login"
			query = urllib.parse.urlencode({
				'openid.ns' : self.openid_ns,
				'openid.mode' : "check_authentication",
				'openid.op_endpoint' : self.openid_op_endpoint,
				'openid.claimed_id' : self.openid_claimed_id,
				'openid.identity' : self.openid_identity,
				'openid.return_to' : self.openid_return_to,
				'openid.response_nonce' : self.openid_response_nonce,
				'openid.assoc_handle' : self.openid_assoc_handle,
				'openid.signed' : self.raw_signed,
				'openid.sig' : self.openid_sig,
			})

			response = {}
			with urllib.request.urlopen(f"{url}?{query}") as f:
				for item in f.read(300).split(b'\n'):
					if b':' in item:
						key, val = item.split(b':', 1)

						if key == b'is_valid':
							val = json.loads(val.decode(errors='replace'))
						else:
							val = val.decode(errors='replace')

						response[key.decode(errors='replace')] = val

			self._valid = response.get('is_valid')

		return self._valid


class UserInformation(BaseModel):
	key :str
	user_id :str
	avatar :str|None = None
	communityvisibilitystate :int|None = None
	profilestate :int|None = None
	personaname :str|None = None
	profileurl :str|None = None
	avatar :str|None = None
	avatarmedium :str|None = None
	avatarfull :str|None = None
	avatarhash :str|None = None
	lastlogoff :int|None = None
	personastate :int|None = None
	primaryclanid :str|None = None
	timecreated :int|None = None
	personastateflags :int|None = None
	loccountrycode :str|None = None

	def __init__(self, **initial_data):
		if not initial_data.get('key') or not initial_data.get('user_id'):
			raise KeyError(f"Need a Steam API key and User ID to get user information")

		url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
		query = urllib.parse.urlencode({
			'key' : initial_data.get('key'),
			'steamids' : initial_data.get('user_id')
		})

		
		with urllib.request.urlopen(f"{url}?{query}") as f:
			data = f.read()
			try:
				reply = json.loads(data)
			except json.decoder.JSONDecodeError:
				raise ValueError(f"Could not decode JSON response from Steam: {data}")

		if not reply.get('response') or not reply['response'].get('players') or len(reply['response']['players']) <= 0:
			raise ValueError(f"Invalid Steam User Information response: {reply}")

		super().__init__(**reply['response']['players'][0], **initial_data)


class DBConfig(BaseModel):
	password :str|None = None
	hostname :str = '127.0.01'
	username :str = 'coreborn'
	database :str = 'coreborn'


class Colors(BaseModel):
	heartwood :str = "#FF0000"
	blushbell :str = "#00FEB2"
	dornwood :str = "#0000FF"
	ellyonwood :str = "#D200FF"
	gold :str = "#FFD700"
	ambrosite :str = "#FFA500"
	royalite :str = "#008080"
	sulfur :str = "#f1dd38"
	iron :str = "#C2C2C2"
	coal :str = "#151716"


class Steam(BaseModel):
	key :str|None = None


class Configuration(BaseModel):
	db :DBConfig
	colors :Colors
	steam :Steam