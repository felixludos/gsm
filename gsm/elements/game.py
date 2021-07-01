
from typing import Union, Dict, List, Any, Optional, NoReturn
from omnibelt import Packable, get_printer, json_pack, json_unpack, JSONABLE

from .containers import GameContainer, GameSettings, GameObservation, FullGameObservation, GamePlayer
from .manifest import GameManifest
from .log import GameLog
from .actions import GameAction, GameActions
from .table import register_game

prt = get_printer(__file__)

class Game(Packable):
	
	# region Subclasses
	
	def __init_subclass__(cls, name=None, **kwargs):
		super().__init_subclass__(name=name)
		cls._component_cls = dict(manifest=GameManifest, log=GameLog, state=GameContainer,
		                          player=GamePlayer, settings=GameSettings)
		cls._component_cls.update(**kwargs)
		
		cls._name = name
		if name is not None:
			register_game(name)(cls)
		
		
	@classmethod
	def get_name(cls):
		return cls._name
		
		
	@classmethod
	def get_component(cls, ident):
		return cls._component_cls.get(ident, GameContainer)
	
	# endregion
	
	def __init__(self, players: Union[List[GamePlayer], Dict[str, Union[GamePlayer, Dict[str,Any]]]],
	             **settings: Optional[Dict[str, Any]]):
		super().__init__()
		self.settings = self.get_component('settings')(**settings)
		
		self.state = self.get_component('state')
		self.manifest = self.get_component('manifest')
		self.log = self.get_component('log')
		
		self.players = self._process_players(players)
	
	
	def _process_players(self, players: Union[List[GamePlayer], Dict[str, Union[GamePlayer, Dict[str,Any]]]])\
			-> Dict[str, GamePlayer]:
		if isinstance(players, list):
			return {player.name: player for player in players}
		return {key: (value if isinstance(value, GamePlayer) else self.get_component('player')(name=key, **value))
		        for key, value in players.items()}
	
	
	@staticmethod
	def load(data: str) -> 'Game':
		return json_unpack(data)
	
	
	def save(self) -> str:
		return json_pack(self)
	
	
	def verify_players(self, users: Dict[str, Dict[str, Any]]) -> bool:
		return True
	
	
	def take_action(self, player: Union[str,GamePlayer], action: GameAction) \
			-> Dict['GamePlayer', JSONABLE]:
		
		if player in self.players:
			player = self.players[player]
		
		return {player.name: actions.pull(player)
		        for player, actions in self._take_action(player, action)}
		
	
	def get_observation(self, player: Union[str, GamePlayer]) -> JSONABLE:
		
		if player in self.players:
			player = self.players[player]
		
		with self.manifest.sanitizer(player) as sanitize:
			return sanitize(self._get_observation(player))
	
	
	def _take_action(self, player: GamePlayer, action: GameAction) -> Dict[GamePlayer, GameActions]:
		raise NotImplementedError
	
	
	def _get_observation(self, player: GamePlayer) -> GameObservation:
		return FullGameObservation(state=self.state, players=self.players, manifest=self.manifest, log=self.log)


	def get_settings(self, player: GamePlayer = None) -> JSONABLE:
		with self.manifest.sanitizer(player) as sanitize:
			return sanitize(self.settings)


	def cheat(self, code: str = None) -> NoReturn:
		raise NotImplementedError



