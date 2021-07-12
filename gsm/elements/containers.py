from termcolor import colored
from omnibelt import Packable, Hashable, primitive

from ..features import Named, Typed, Writable
from .manifest import Sanitizable



class GameContainer(Sanitizable, Packable):
	def __init__(self, *args, **info):
		super().__init__(*args)
		self.__dict__.update(info)


	def sanitize(self, player, manifest, sanitize):
		
		
		
		raise NotImplementedError



class ActionElement(GameContainer):
	def verify_action(self, obj):
		raise NotImplementedError



class ContainerFormatter:
	def __init__(self, colors='default', prefixes='default'):
		super().__init__()
		if colors == 'default':
			colors = {'player': 'green'}
		self.colors = colors

		if prefixes == 'default':
			prefixes = {'player': 'PLYR'}
		self.prefixes = prefixes
	
	
	def draw_object(self, obj):
		if isinstance(obj, primitive):
			return str(obj)
		
		info = {}
		if isinstance(obj, Writable):
			try:
				return obj.to_string(self)
			except NotImplementedError:
				pass
			info = obj.get_text_info()
			typ = obj.get_text_type()
			val = obj.get_text_val()
		elif isinstance(obj, Typed):
			typ = obj.get_type()
			val = str(obj)
		else:
			typ = obj.__class__.__name__
			val = str(obj)
		
		color = info.get('color', self.colors.get(typ, 'blue'))
		
		prefixes = self.prefixes.get('prefixes', None)
		if prefixes is not None:
			val = f'{self.prefixes.get(typ, typ.upper())}:{val}'
		return str(val) if color is None else colored(val, color=color)
	
	
	def draw_sequence(self, seq):
		return [self.draw_object(obj) for obj in seq]
	
	
	def draw_group(self, group):
		return [self.draw_sequence(seq) for seq in group]
	
	
	def draw_multigroup(self, multi):
		return [self.draw_group(group) for group in multi]



class ContainerSequence(GameContainer, list):
	
	# region Packing
	
	_content_key = 'seq'
	_info_key = 'info'
	
	@classmethod
	def __create__(cls, data):
		return cls()
	
	
	def __pack__(self, pack_member):
		return {self._content_key: [pack_member(x) for x in self],
		        self._info_key: super().__pack__(pack_member)}
	
	
	def __unpack__(self, data, unpack_member):
		self.extend(unpack_member(x) for x in data.get(self._content_key, []))
		super().__unpack__(data.get(self._info_key, {}), unpack_member)
	
	# endregion

	def draw(self, formatter):
		return formatter.draw_sequence(self)
	
	
	def copy(self, part=None):
		if part is None:
			part = self
		return self.__class__(part, **self.__dict__)
	
	
	def __getitem__(self, item):
		value = super().__getitem__(item)
		if isinstance(item, slice):
			value = self.copy(value)
		return value



class ContainerGroup(ContainerSequence):

	_content_key = 'group'
	
	def draw(self, formatter):
		return formatter.draw_group(self)



class ContainerMultiGroup(ContainerSequence):

	_content_key = 'multi'
	
	def draw(self, formatter):
		return formatter.draw_multigroup(self)



class GameSettings(GameContainer):
	pass



class GameObservation(GameContainer):
	pass



class FullGameObservation(GameObservation):
	def __init__(self, state=None, players=None, manifest=None, log=None):
		super().__init__(state=state, players=players, manifest=manifest, log=log)
		
		
	def sanitize(self, player, manifest, sanitize):
		raise NotImplementedError# TODO: make sure to pull manifest last so its fully uptodate



class GameObject(Writable, Typed, ActionElement, GameContainer):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._reset_unique_ID()
		
		
	def _reset_unique_ID(self, seed=None):
		if seed is None:
			seed = id(self)
		self.ID = hex(hash(seed))[2:]
		return self.ID

	
	def __hash__(self):
		return hash(self.ID)
	
	
	def __eq__(self, other):
		return other.ID == self.ID


	def __str__(self):
		return self.ID


	def get_text_val(self):
		return str(self)
	
	
	def get_text_type(self):
		return self.get_type()



class GamePlayer(Named, GameObject, obj_type='player'):
	def __init_subclass__(cls, obj_type='player', **kwargs):
		super().__init_subclass__(obj_type=obj_type, **kwargs)
		
	




