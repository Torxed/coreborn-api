from pydantic import BaseModel, validator

class Position(BaseModel):
	x: float
	y: float

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
