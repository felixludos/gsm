
from typing import Union, Dict, List, Any, Optional, NoReturn, NewType, TypeVar, Generic
from collections import OrderedDict
from omnibelt import Named_Registry, Packable, get_printer, primitive, PRIMITIVE, pack, JSONABLE

from ..util import USER
from .game import Game
from .containers import GameObservation, GameContainer, GamePlayer
from .log import GameLogEntry, GameLog
from .actions import GameController, GameAction

prt = get_printer(__file__)



T = TypeVar('T')
Message = Generic[T]


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



class GameAdvice(GameContainer):
	def __init__(self, action: GameAction, **info):
		super().__init__()
		self.action = action
		self.info = info



class GameStatus(GameContainer):
	def __init__(self, observation: GameObservation = None, log: GameLog = None,
	             actions: GameController = None, waiting_for: List[USER] = None,
	             advice: Dict[USER, GameAdvice] = None, **info):
		super().__init__()
		
		self.observation = observation
		self.log = log
		if actions is None:
			self.actions = actions
		else:
			assert waiting_for is not None
			self.waiting_for = waiting_for
		if advice is None:
			advice = {}
		self.advice = advice
		
		self.info = info


	def update_advice(self, advisor: USER, action: GameAction, **info):
		self.advice[advisor] = GameAdvice(action, **info)



class GameTable(Packable):
	'''
	A "session" interface - each instance of a game being played should be managed and handled by a GameTable instance.
	Note that GameTable subclasses should be agnostic to the game being played, and instead focus on managing the
	participants of the game and the interface between the implemented game and the participants.
	'''
	def __init__(self):
		
		self._default_role = 'spectator'
		
		self.hard_reset()
	
	
	def hard_reset(self):
		
		# region Users
		self._users = {}
		self._players = OrderedDict()
		self._spectators = set()
		self._advisors = {}
		self._advised_players = {}
		# endregion

		self._game_entry = None
		self._settings = {}
		
		self.reset_game()
	
	
	def reset_game(self):
		self._game = None
		
		self._status = {}
		self._spectator_status = None
	
		self._player2user = None
		self._user2player = None
		self._log = None
	
	
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
		game = game_shelf.get(game, game)
		if not isinstance(game, Game):
			prt.warning(f'Selecting a game that\'s not a subclass of Game: {game}')
		self.reset_game()
		self._game_cls = game
	
	
	# region Optional
	def save_table(self, path):
		raise NotImplementedError
	
	
	def load_table(self, path):
		raise NotImplementedError
	# endregion


	# region Game
	def start_game(self):
		
		game_cls = self._game_cls
		
		self._game = game_cls(**self._settings)
		
		self._log = self._game.set_log()
		self._user2player = self._game.process_players(self._players)
		self._player2user = {val: key for key, val in self._user2player.items()}
		
		self._process_controllers(self._game.begin())

	
	def take_action(self, user: USER, action: Union[int, str, List[PRIMITIVE]], **info) -> Message[GameStatus]:
		
		pick = self._process_action(user, action)
		
		if user in self._advisors:
			player = self._advisors[user]
			self._status[player].update_advice(user, pick, **info)
		
		self._process_controllers(self._game.take_action(self._find_player(user), pick))
		return self.get_status(user)

	
	def get_status(self, user: USER) -> Message[GameStatus]:
		if user in self._advisors:
			user = self._advisors[user]
		
		if user not in self._status:
			self._status[user] = self._create_status(user)
		return self._package_message(user, self._status[user])
		
	
	def full_log(self, user: USER) -> Message[GameLog]:
		return self._package_message(user, self._log.get_full(self._find_player(user)))
	
	
	def cheat(self, player: USER, code: str = None):
		raise NotImplementedError
	# endregion


	# region Status
	def _package_message(self, user: USER, msg: T) -> Message[T]:
		return pack(msg)
	
	
	def _find_player(self, user: USER) -> GamePlayer:
		return self._user2player[user]
	
	
	def _find_user(self, player: GamePlayer) -> USER:
		return self._player2user[player]
	
	
	def _process_controllers(self, actions: Dict[GamePlayer, GameController]) -> NoReturn:
		self._status.clear()
		for player, controller in actions.items():
			user = self._find_user(player)
			self._status[user] = self._create_status(user, controller)
	
	
	def _process_action(self, user: USER, action: Union[int, str, List[PRIMITIVE]]) -> GameAction:
		return self._status[user].actions.find(action)
	
	
	def _log_update(self, user: USER) -> GameLog:
		return self._log.get_update(self._find_player(user))
	
	
	def _create_status(self, user: USER, actions: GameController = None, **kwargs) -> GameStatus:
		if 'observation' not in kwargs:
			kwargs['observation'] = self._game.get_observation(self._find_player(user))
		if 'log' not in kwargs:
			kwargs['log'] = self._log_update(user)
		if actions is None and 'waiting_for' not in kwargs:
			kwargs['waiting_for'] = [u for u, status in self._status.items() if status.actions is not None]
		return GameStatus(actions=actions, **kwargs)
	# endregion

	pass




