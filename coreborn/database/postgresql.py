import psycopg2
import psycopg2.extras
import dataclasses

@dataclasses.dataclass
class Database:
	dbname :str
	user: str
	password :str = None
	host: str = '127.0.0.1'
	port: int = 5432
	connection: psycopg2.extensions.connection = None

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

@dataclasses.dataclass
class Transaction:
	session :Database
	cursor :psycopg2.extras.RealDictCursor = None

	def __enter__(self):
		self.session.connection.autocommit = False
		self.cursor = self.session.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		return self

	def __exit__(self, *args):
		self.session.connection.commit()
		self.cursor.close()
		self.session.connection.autocommit = True

	def query(self, query, values=None, force_list=False):
		if not self.session.connected:
			self.session.reconnect()

		self.cursor.execute(query, values)

		if self.cursor.rowcount:
			try:
				data = [dict(item) for item in self.cursor.fetchall()]
				if self.cursor.rowcount == 1 and force_list is False:
					return data[0]
				else:
					return data
			except psycopg2.ProgrammingError:
				# INSERT etc will trigger a rowcount (good), but won't have any results to return (good)
				return True