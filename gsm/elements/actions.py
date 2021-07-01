from typing import Union
from omnibelt import Packable

from .manifest import Sanitizable


class GameActions(Sanitizable, Packable, list):
	def process(self, action: Union['GameAction', int]) -> 'GameAction':
		raise NotImplementedError


	def _expand_actions(self):
		raise NotImplementedError



class GameAction(Sanitizable, Packable):
	pass