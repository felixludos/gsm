from typing import NewType

from omnibelt import Hashable
from ..features import Named

# class User(Named, Hashable):
#
# 	def __eq__(self, other):
# 		return other == self.name
#
# 	def __hash__(self):
# 		return hash(self.name)
#
# 	def __str__(self):
# 		return self.name
#
# 	pass

class User(str):
	pass


class Player(User):
	def __init__(self, *args, **kwargs):
		# print(args, kwargs)
		# super().__init__(*args, **kwargs)
		self.info = {}
		self.player_obj = None
		self.advisors = set()
	
	# def __str__(self):
	# 	return repr(self)
	
	def __repr__(self):
		return super().__repr__() + f'[{self.get_obj()}]'
	
	def add_advisor(self, user: 'Advisor'):
		self.advisors.add(user)

	def set_obj(self, obj):
		self.player_obj = obj
	
	def get_obj(self):
		return self.player_obj



class Advisor(User):
	def __init__(self, *args, **kwargs):
		# super().__init__(*args, **kwargs)
		self.player = None
	def set_player(self, player: Player = None):
		self.player = player
	def get_player(self):
		return self.player



class Spectator(User):
	pass


