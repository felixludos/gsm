from omnibelt import Packable, Hashable

from ..features import Named, Typed, Writable
from .manifest import Sanitizable



class GameContainer(Sanitizable, Packable):
	def __init__(self, **info):
		super().__init__()
		self.__dict__.update(info)


	def sanitize(self, player, manifest, sanitize):
		raise NotImplementedError



class GameSettings(GameContainer):
	pass



class GameObservation(GameContainer):
	pass



class FullGameObservation(GameObservation):
	def __init__(self, state=None, players=None, manifest=None, log=None):
		super().__init__(state=state, players=players, manifest=manifest, log=log)
		
		
	def sanitize(self, player, manifest, sanitize):
		raise NotImplementedError# TODO: make sure to pull manifest last so its fully uptodate



class GameObject(Writable, Typed, Hashable, GameContainer):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._reset_unique_ID()
		
		
	def _reset_unique_ID(self, seed=None):
		if seed is None:
			seed = id(self)
		self.ID = hex(hash(seed))[2:]
		return self.ID


	def get_text_val(self):
		return str(self)
	
	
	def get_text_type(self):
		return self.get_type()



class GamePlayer(Named, GameObject, obj_type='player'):
	
	def __init_subclass__(cls, obj_type='player', **kwargs):
		super().__init_subclass__(obj_type=obj_type, **kwargs)
		
	




