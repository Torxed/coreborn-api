import psycopg2
import psycopg2.extras
import dataclasses
import hashlib

from ..startup import init_data

@dataclasses.dataclass
class Database:
	dbname :str
	user :str
	password :str = None
	host :str = '127.0.0.1'
	port :int = 5432
	connection :psycopg2.extensions.connection = None

	def __post_init__(self):
		if self.connection is None:
			self.reconnect()

	def reconnect(self):
		if self.connection:
			try:
				self.connection.close()
			except:
				pass

		self.connection = psycopg2.connect(
			dbname=self.dbname,
			user=self.user,
			password=self.password,
			host=self.host,
			port=self.port,
			connect_timeout=3
		)
		self.connection.autocommit = True

	@property
	def connected(self):
		if self.connection is not None and self.connection.closed == 0:
			return True

		return False

	def query(self, query, values=None, force_list=False):
		#print(query, values)
		if not self.connected:
			self.reconnect()

		with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
			cur.execute(query, values)

			if cur.rowcount:
				try:
					data = [dict(item) for item in cur.fetchall()]
					if cur.rowcount == 1 and force_list is False:
						return data[0]
					else:
						return data
				except psycopg2.ProgrammingError:
					# INSERT etc will trigger a rowcount (good), but won't have any results to return (good)
					return True

		return None

	def init(self):
		"""
		This is a helper function to spawn the tables and starting entries.
		IP addresses are obfuscated and cleared out after a short period of time to confirm with legal requirements.
		"""
		self.query("""CREATE TABLE IF NOT EXISTS ip_addresses (
			id BIGSERIAL,
			ip VARCHAR(64) NOT NULL UNIQUE,
			blocked BOOL,
			added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
		)""")
		self.query("""CREATE TABLE IF NOT EXISTS resources (
			id SERIAL,
			name VARCHAR NOT NULL UNIQUE,
			category VARCHAR NOT NULL,
			icon VARCHAR,
			added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
		)""")
		self.query("""CREATE TABLE IF NOT EXISTS positions (
			id BIGSERIAL,
			resource BIGINT NOT NULL,
			x DOUBLE PRECISION NOT NULL,
			y DOUBLE PRECISION NOT NULL,
			ip BIGINT NOT NULL,
			added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
			UNIQUE(resource, x, y)
		)""")

		self.query("""INSERT INTO ip_addresses (ip, blocked) 
					VALUES(%s, false) ON CONFLICT DO NOTHING""",
			(hashlib.sha256(b'127.0.0.1').hexdigest(), )
		)

		with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
			for category in init_data:
				for resource, values in init_data[category].items():
					self.query("""INSERT INTO resources (name, category)
								VALUES(%s, %s) ON CONFLICT DO NOTHING""",
						(resource, category)
					)

					cur.executemany(
						f"""
						INSERT INTO positions (resource, x, y, ip)
						VALUES(
							(SELECT id FROM resources WHERE name='{resource}'), %s, %s, %s
						) ON CONFLICT DO NOTHING""",
						values['positions']
					)

# @dataclasses.dataclass
# class Transaction:
# 	session :Database
# 	cursor :psycopg2.extras.RealDictCursor = None

# 	def __enter__(self):
# 		self.session.connection.autocommit = False
# 		self.cursor = self.session.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
# 		return self

# 	def __exit__(self, *args):
# 		self.session.connection.commit()
# 		self.cursor.close()
# 		self.session.connection.autocommit = True

# 	def query(self, query, values=None, force_list=False):
# 		if not self.session.connected:
# 			self.session.reconnect()

# 		self.cursor.execute(query, values)

# 		if self.cursor.rowcount:
# 			try:
# 				data = [dict(item) for item in self.cursor.fetchall()]
# 				if self.cursor.rowcount == 1 and force_list is False:
# 					return data[0]
# 				else:
# 					return data
# 			except psycopg2.ProgrammingError:
# 				# INSERT etc will trigger a rowcount (good), but won't have any results to return (good)
# 				return True