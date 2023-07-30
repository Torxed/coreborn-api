from pydantic import BaseModel, validator

class Position(BaseModel):
	x :float
	y :float

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

class AuthRedirect(BaseModel):
	openid_ns :str
	openid_mode :str
	openid_op_endpoint :str
	openid_claimed_id :str
	openid_identity :str
	openid_return_to :str
	openid_response_nonce :str
	openid_assoc_handle :int
	openid_signed :set
	openid_sig :str

	@validator('openid_ns', each_item=True)
	def validate_ns(cls, v):
		if v != 'http://specs.openid.net/auth/2.0':
			raise ValueError('Invalid NS returned')
		return v

	@validator('openid_mode', each_item=True)
	def validate_mode(cls, v):
		#if v != 'http://specs.openid.net/auth/2.0':
		#	raise ValueError('Invalid NS returned')
		print('mode:', v)
		return v

	@validator('openid_op_endpoint', each_item=True)
	def validate_op_endpoint(cls, v):
		if v != 'https://steamcommunity.com/openid/login':
			raise ValueError('Invalid OP Endpoint returned')
		return v

	@validator('openid_claimed_id', each_item=True)
	def validate_claimed_id(cls, v):
		if not v.startswith('https://steamcommunity.com/openid/id/'):
			raise ValueError('Invalid Claim ID returned')
		return v

	@validator('openid_identity', each_item=True)
	def validate_identity(cls, v):
		if not v.startswith('https://steamcommunity.com/openid/id/'):
			raise ValueError('Invalid Identity path returned')
		return v

	@validator('openid_return_to', each_item=True)
	def validate_return_to(cls, v):
		if v != 'http://beta.coreborn.app/auth':
			raise ValueError('Invalid Return path returned')
		return v

	@validator('openid_response_nonce', each_item=True)
	def validate_response_nonce(cls, v):
		if not instanceof(v, str):
			raise ValueError('Invalid nonce returned')
		return v

	@validator('openid_assoc_handle', each_item=True)
	def validate_assoc_handle(cls, v):
		if not instanceof(v, int):
			raise ValueError('Invalid associated handle returned')
		return v

	@validator('openid_signed', each_item=True)
	def validate_signed(cls, v):
		items = set(v.split(','))
		# Verify that the returned signed items are precent, and only those
		if items ^ {'signed', 'op_endpoint', 'claimed_id', 'identity', 'return_to', 'response_nonce', 'assoc_handle'}:
			raise ValueError('Invalid signed returned')
		return v

	@validator('openid_sig', each_item=True)
	def validate_sig(cls, v):
		if not instanceof(v, str):
			raise ValueError('Invalid signature returned')
		return v


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


class Configuration(BaseModel):
	db :DBConfig
	colors :Colors
