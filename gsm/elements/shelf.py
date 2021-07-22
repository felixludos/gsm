
from omnibelt import Named_Registry


class GameShelf(Named_Registry):
	pass
game_shelf = GameShelf()



def register_game(name=None):
	def _reg_game(cls):
		nonlocal name
		if name is None:
			name = cls.get_name()
		game_shelf.new(name, cls)
		return cls
	return _reg_game

