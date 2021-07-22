from collections import OrderedDict
from typing import Union, Mapping, List, Any, Optional, NoReturn
from omnibelt import Packable, get_printer, json_pack, json_unpack, JSONABLE

from .roles import User, Player, Advisor, Spectator
from .containers import GameContainer, GameSettings, GameObservation, FullGameObservation, GamePlayer, GameResult
from .log import GameLog
from .actions import GameAction, GameController
from .shelf import register_game

prt = get_printer(__file__)



class Game(GameContainer):
	def __init__(self, **settings: Optional[Mapping[str, Any]]):
		super().__init__()
		# self.settings = self.get_component('settings')(**settings)
		#
		# self.state = self.get_component('state')
		# self.manifest = self.get_component('manifest')
		# self.log = self.get_component('log')
		
		self.log = None
		self.players = None
		self.settings = self.create_settings(**settings)
		self.state = self.create_state()
	
	
	# region Subclasses
	def __init_subclass__(cls, name=None, **kwargs):
		super().__init_subclass__(name=name)
		# cls._component_cls = dict(manifest=GameManifest, log=GameLog, state=GameContainer,
		#                           player=GamePlayer, settings=GameSettings)
		# cls._component_cls.update(**kwargs)
		
		cls._name = name
		if name is not None:
			register_game(name)(cls)
		
	# @classmethod
	# def get_component(cls, ident):
	# 	return cls._component_cls.get(ident, GameContainer)
	
	@classmethod
	def get_name(cls):
		return cls._name
	# endregion
	
	
	# region Setup
	@staticmethod
	def create_settings(*args, **settings: Mapping[str, Any]) -> GameSettings:
		return GameSettings(*args, **settings)
	
	
	@staticmethod
	def create_player(name: str, **kwargs) -> GamePlayer:
		return GamePlayer(name, **kwargs)
	
	
	@classmethod
	def create_players(cls, users: Mapping[str, Mapping[str, Any]]) -> List[GamePlayer]:
		return [cls.create_player(name=name, **info) for name, info in users.items()]
	
	
	@staticmethod
	def create_state(*args, **kwargs) -> GameContainer:
		return GameContainer(*args, **kwargs)
	
	
	@staticmethod
	def create_log(*args, **kwargs) -> GameLog:
		return GameLog(*args, **kwargs)
	
	
	def set_log(self, log: GameLog = None):
		if log is None:
			log = self.create_log()
		self.log = log
		return self.log
	
	
	def process_players(self, users: Mapping[User, Mapping[str, Any]]) -> Mapping[User, GamePlayer]:
		players = self.create_players(users)
		self.players = players
		return OrderedDict(zip(users, players))
	# endregion
	
	
	@staticmethod
	def load(data: str) -> 'Game':
		return json_unpack(data)
	
	
	def save(self) -> str:
		return json_pack(self)
	
	
	def begin_game(self) -> Mapping[GamePlayer, GameController]:
		raise NotImplementedError
	
	
	def end_game(self) -> GameResult:
		raise NotImplementedError
	
	
	def take_action(self, player: GamePlayer, action: GameAction) -> Mapping[GamePlayer, GameController]:
		raise NotImplementedError
		
	
	def get_observation(self, player: GamePlayer) -> GameObservation:
		return FullGameObservation(state=self.state, players=self.players)
	
	
	def get_settings(self, player: GamePlayer = None) -> GameContainer:
		return self.settings

	
	def get_log(self, player: GamePlayer = None) -> GameLog:
		return self.log.get_log(player)


	def get_log_update(self, player: GamePlayer = None) -> GameLog:
		return self.log.get_log(player)
	

	def cheat(self, player: GamePlayer, code: str = None) -> NoReturn:
		raise NotImplementedError



