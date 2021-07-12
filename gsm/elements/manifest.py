from typing import Callable
from omnibelt import JSONABLE, Packable

from .containers import GameContainer, GameObject, GamePlayer


class Sanitizable(object):
	def sanitize(self, player: GamePlayer, sanitize: Callable) -> JSONABLE:
		raise NotImplementedError



class GameGuardian(object):
	def __init__(self, manifest, player=None):
		self.manifest = manifest
		self.player = player

	
	def __enter__(self):
		return self

	
	def __exit__(self, exc_type, exc_val, exc_tb):
		raise NotImplementedError  # compare new manifest with original, and possibly update

	
	def __call__(self, obj):
		raise NotImplementedError



class GameManifest(GameContainer):
	def sanitize(self, player: GamePlayer) -> JSONABLE:
		raise NotImplementedError


	def sanitizer(self, player: GamePlayer) -> GameGuardian:
		return GameGuardian(player, self)


