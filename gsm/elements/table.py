
from omnibelt import Named_Registry, Packable, get_printer

prt = get_printer(__file__)



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



class GameTable:
	'''
	A "session" interface - each instance of a game being played should be managed and handled by a GameTable instance.
	Note that GameTable subclasses should be agnostic to the game being played, and instead focus on managing the
	participants of the game and the interface between the implemented game and the participants.
	'''
	def __init__(self, game=None):
		
		self._default_role = 'spectator'
		
		self._game = game
		
		# region Users
		self._users = {}
		self._players = {}
		self._spectators = set()
		self._advisors = {}
		self._advised_players = {}
		# endregion
	
		pass
	
	# region Users
	
	def remove_user(self, user):
		if user not in self._users:
			return
		
		if self._users[user] == 'player':
			del self._players[user]
			for adviser in self._advised_players.get(user, []):
				self.remove_user(adviser)
				
			prt.info(f'Removing player: {user}')
		
		if self._users[user] == 'advisor':
			self._advised_players[self._advisors[user]].remove(user)
			prt.info(f'Removing advisor of {self._advisors[user]}: {user}')
			del self._advisors[user]
			
		if self._users[user] == 'spectators':
			self._spectators.remove(user)
			prt.info(f'Removing spectator {user}')
		
		del self._users[user]
	
	def add_player(self, user, **info):
		self.remove_user(user)
		self._players[user] = info
		self._users[user] = 'player'
	
	def add_advisor(self, user, player):
		assert player in self._players, f'Unknown player: {player}'
		self.remove_user(user)
		
		if player not in self._advised_players:
			self._advised_players[player] = set()
		self._advised_players[player].add(user)
		
		self._advisors[user] = player
		self._users[user] = 'advisor'
		
		prt.info(f'Added adviser {user} to {player}')
	
	def add_spectator(self, user):
		self.remove_user(user)
		
		self._spectators.add(user)
		self._users[user] = 'spectator'
	
	# endregion
	
	def set_game(self, game):
		self._game = game
	
	# region Optional
	
	def save_table(self, path):
		pass
	
	def load_table(self, path):
		pass
	
	def save_game(self, path):
		pass
	
	def load_game(self, path):
		pass
	
	def cheat(self, code=None):
		raise NotImplementedError

	# endregion

	pass



class GameStatus(Packable):
	def __init__(self, observation=None, actions=None, advice=None):
		super().__init__()
		
		self.observation = observation
		self.actions = actions
		self.advice = advice


