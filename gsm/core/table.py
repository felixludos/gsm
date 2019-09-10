
from ..structures import Transactionable
from ..containers import tdict, tset, tlist
from ..signals import MissingTypeError, MissingValueError, MissingObjectError

from .object import GameObject
from .. import util

class GameTable(Transactionable):
	
	def __init__(self, players):
		super().__init__()
		
		self.players = players
		self._in_transaction = False
		self.obj_types = tdict()
		
		self.reset()
	
	def reset(self):
		self.table = tdict()
		self.ID_counter = 0
	
	def in_transaction(self):
		return self._in_transaction
	
	def begin(self):
		if self.in_transaction():
			self.abort()
		
		self._in_transaction = True
		self.table.begin()
	
	def commit(self):
		if not self.in_transaction():
			return
		self.table.commit()
	
	def abort(self):
		if not self.in_transaction():
			return
		self.table.abort()
		
	# IMPORTANT: user can optionally register their own defined subclasses of GameObject here for them to be used
	def register_obj_type(self, cls=None, name=None, required=None, visible=None):
		if cls is None:
			assert name is not None, 'Must provide either a name or class'
			cls = GameObject
		elif name is None:
			name = cls.__class__.__name__
		self.obj_types[name] = tdict(cls=cls,
		                             reqs=required, # props required for creating object
		                             visible=visible) # props visible to all players always (regardless of obj.visible)
		
	def _get_type_info(self, obj_type):
		if obj_type not in self.obj_types:
			raise MissingObjectError(obj_type)
		return self.obj_types[obj_type]
		
	# IMPORTANT: used to check whether object is still valid
	def check(self, key):
		return key in self.table
		
	# IMPORTANT: user should use this function to create new all game objects
	def create(self, obj_type, visible=None, ID=None, **props):
		
		if visible is None: # by default visible to all players
			visible = tset(self.players)
		
		info = self._get_type(obj_type)
		
		if info.reqs is not None:
			for req in info.reqs:
				if req not in props:
					raise MissingValueError(obj_type, req, *info.reqs)
		
		if ID is None:
			ID = self.ID_counter
			self.ID_counter += 1
		
		obj = info.cls(ID=ID, obj_type=obj_type, visible=visible, **props)
		
		self.table[obj._id] = obj
		
		return obj
	
	# this function should usually be called automatically
	def update(self, key, value):
		self.table[key] = value
	
	# IMPORTANT: user should use this function to create remove any game object
	def remove(self, key):
		del self.table[key]
	
	def get_types(self):
		return self.obj_types.keys()
	
	def pull(self, player=None): # returns jsonified obj
		tbl = util.jsonify(self.table)
		if player is not None:
			self._privatize(tbl, player)
		return tbl
	def _privatize(self, tbl, player): # tbl must be a deep copy of self.table
		
		for ID, obj in tbl:
			for k, v in obj.items():
				allowed = self._get_type_info(k['obj_type']).visible
				if k != 'obj_type' and k != 'visible' and player not in obj['visible'] and (allowed is None or k not in allowed):
					del obj[k] # remove information not permitted
	
	def __getstate__(self):
		
		data = {}
		
		data['obj_types'] = list(self.obj_types.keys())
		data['ID_counter'] = self.ID_counter
		data['table'] = {}
		
		for k, v in self.table.items():
			data[k] = v.obj_type, v.__getstate__()
		
		return data
	
	def __setstate__(self, state):
		for obj_type in state['obj_types']:
			if obj_type not in self.obj_types:
				raise MissingType(self, obj_type)
		
		self.reset()
		
		for k, (t, x) in state['table'].items():
			self.table[k] = self.create(t)
			self.table[k].__setstate__(x)
			
		self.ID_counter = state['ID_counter']
	
	def __getitem__(self, item):
		return self.table[item]
	
	def __setitem__(self, key, value):
		self.table[key] = value
	
	def __delitem__(self, key):
		del self.table[key]
		
	def __contains__(self, item):
		return item in self.table

