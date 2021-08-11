
from typing import Union, Dict, List, Any, Optional, NoReturn, NewType, TypeVar, Generic, Tuple
from collections import OrderedDict
from omnibelt import Named_Registry, Packable, get_printer, primitive, PRIMITIVE, pack, JSONABLE

from .roles import User, Player, Advisor, Spectator
from .messaging import Messaging, Message
from .game import Game
from .shelf import game_shelf
from .containers import GameObservation, GameContainer, GamePlayer, GameResult
from .log import GameLogEntry, GameLog
from .actions import GameController, GameAction

prt = get_printer(__file__)

T = TypeVar('T')


class GameAdvice(GameContainer):
	def __init__(self, action: GameAction, **info):
		super().__init__()
		self.action = action
		self.info = info



class GameStatus(GameContainer):
	def __init__(self, observation: GameObservation = None, log: GameLog = None,
	             actions: GameController = None, waiting_for: List[User] = None,
	             advice: Dict[User, GameAdvice] = None, **info):
		super().__init__()
		
		self.observation = observation
		self.log = log
		if actions is not None:
			self.actions = actions
		else:
			assert waiting_for is not None
			self.waiting_for = waiting_for
		if advice is None:
			advice = {}
		self.advice = advice
		
		self.info = info


	def update_advice(self, advisor: Advisor, action: GameAction, **info):
		self.advice[advisor] = GameAdvice(action, **info)


	def __str__(self):
		keys = ', '.join(sorted(self.__dict__.keys()))
		return f'{self.__class__.__name__}({keys})'



class GameTable(Packable):
	'''
	A "session" interface - each instance of a game being played should be managed and handled by a GameTable instance.
	Note that GameTable subclasses should be agnostic to the game being played, and instead focus on managing the
	participants of the game and the interface between the implemented game and the participants.
	'''
	def __init__(self):
		# region Users
		self._users = {}
		# endregion

		self._game_cls = None
		self._settings = {}
		
		self.reset()
	
	
	def reset(self):
		self._game = None
		self._game_result = None
		
		self._status = {}
		self._spectator_status = None
	
		self._players = None
		self._log = None
	
	
	# region Users
	def remove_user(self, user: str):
		if user not in self._users:
			return
		user = self._get_user(user)
		if isinstance(user, Player):
			for advisor in user.advisors:
				self.remove_user(advisor)
			if self._players is not None and user.get_obj() is not None:
				del self._players[user.get_obj()]
			prt.info(f'Removing player: {user}')
		
		if isinstance(user, Advisor):
			if user.player is not None:
				user.player.advisors.remove(user)
			prt.info(f'Removing advisor of {user.player}: {user}')
		
		if isinstance(user, Spectator):
			prt.info(f'Removing spectator {user}')
		
		del self._users[user]
	
	
	def add_player(self, user: str, **info) -> Player:
		self.remove_user(user)
		
		player = Player(user)
		self._users[user] = player
		if len(info):
			player.info = info.copy()
		return player
	
	
	def add_advisor(self, user: str, player: str) -> Advisor:
		assert player in self._users and isinstance(self._users[player], Player)
		self.remove_user(user)
		
		player = self._users[player]
		advisor = Advisor(user)
		
		self._users[user] = advisor
		advisor.player = player
		player.add_advisor(advisor)
		
		prt.info(f'Added adviser {advisor} to {player}')
		return advisor
	
	
	def add_spectator(self, user: str) -> Spectator:
		self.remove_user(user)
		self._users[user] = Spectator(user)
		prt.info(f'Added spectator {user}')
		return self._users[user]
	# endregion
	
	
	def get_available_games(self) -> List[str]:
		return list(game_shelf)
	
	
	def set_game(self, game: Union[str, Game]) -> Game:
		game = game_shelf.get(game, game)
		if not issubclass(game, Game):
			prt.warning(f'Selecting a game that\'s not a subclass of {Game}: {game}')
		self.reset()
		self._game_cls = game
		return game
	
	
	# region Optional
	def save_table(self, path):
		raise NotImplementedError
	
	
	def load_table(self, path):
		raise NotImplementedError
	# endregion


	# region Game
	def start_game(self):
		self.reset()
		game_cls = self._game_cls
		
		self._game = game_cls(**self._settings)
		
		self._log = self._game.set_log()
		players = self._game.process_players(OrderedDict((str(player), player.info) for player in self._users.values()
		                                                 if isinstance(player, Player)))
		for player, obj in players.items():
			player = self._get_user(player)
			player.set_obj(obj)
		self._players = OrderedDict((obj, self._get_user(player)) for player, obj in players.items())
		self._process_controllers(self._game.begin_game())
	
	
	def give_advice(self, user: str, action: Union[int, str, List[PRIMITIVE]], **info):
		
		user = self._get_user(user)
		assert isinstance(user, Advisor)
		
		player = user.player
		
		pick = self._process_action(player, action)
		self._status[player].update_advice(user, pick, **info)

	
	def take_action(self, user: str, action: Union[int, str, List[PRIMITIVE]]) -> Message[GameStatus]:
		
		user = self._get_user(user)
		assert isinstance(user, Player)
		
		pick = self._process_action(user, action)
		assert pick is not None # invalid action error
		
		self._process_controllers(self._game.take_action(user.get_obj(), pick))
		return self.get_status(user)

	
	def respond_to_advice(self, user: str, advisor: str, msg: Any):
		raise NotImplementedError

	
	def get_status(self, user: str) -> Message[Union[GameStatus, GameResult]]:
		user = self._get_user(user)
		
		if isinstance(user, Advisor):
			user = user.player
		
		if self._game_result is not None:
			return self._package_message(user, self._game_result)
		
		if user not in self._status:
			self._status[user] = self._create_status(user)
		return self._package_message(user, self._status[user])
		
		
	def end_game(self):
		self._game_result = self._game.end_game()
	
	
	def full_log(self, user: str = None) -> Message[GameLog]:
		if user is not None:
			user = self._get_user(user)
		return self._package_message(user, self._log.get_full(user))
	
	
	def cheat(self, player: str, code: str = None):
		raise NotImplementedError
	# endregion


	# region Status
	def _get_user(self, name: str) -> User:
		return self._users[name]
	
	
	def _get_player(self, player: GamePlayer) -> Player:
		return self._players[player]
	
	
	@staticmethod
	def _package_message(user: User, msg: T) -> Message[T]:
		return Messaging().send(user, msg)
	
	
	@staticmethod
	def recover_message(msg: Message[T]) -> T:
		return Messaging().recover(msg)
	
	
	def _process_controllers(self, actions: Dict[GamePlayer, GameController]) -> NoReturn:
		self._status.clear()
		if not len(actions):
			self.end_game()
		for player, controller in actions.items():
			user = self._get_player(player)
			self._status[user] = self._create_status(user, controller)
	
	
	def _process_action(self, user: Player, action: Union[int, str, List[PRIMITIVE]]) -> GameAction:
		return self._status[user].actions.find(action)
	
	
	def _log_update(self, user: Player) -> GameLog:
		return self._log.get_update(user.get_obj())
	
	
	def _create_status(self, user: Player, actions: GameController = None, **kwargs) -> GameStatus:
		if 'observation' not in kwargs:
			kwargs['observation'] = self._game.get_observation(user.get_obj())
		if 'log' not in kwargs:
			kwargs['log'] = self._log_update(user)
		if actions is None and 'waiting_for' not in kwargs:
			kwargs['waiting_for'] = [u for u, status in self._status.items() if status.actions is not None]
		return GameStatus(actions=actions, **kwargs)
	# endregion

	pass




