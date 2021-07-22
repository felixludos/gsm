import random
from .elements import Game, GameController, GameObject, GameResult, join_terms


class DummyGame(Game, name='dummy'):
	def __init__(self, include_objects=None, seed=None):
		if seed is None:
			seed = random.getrandbits(32)
		random.seed(seed)
		super().__init__(include_objects=include_objects, seed=seed)
		

	def _pick_num(self, t=None):
		if t is None:
			t = len(self.players)
		return random.randint(1,t)
		
		
	def _pick_active(self):
		return random.choices(self.players, k=self._pick_num())

		
	def _create_actions(self):
		# return {player:GameController().add_group('group1', desc='desc1', actions=[1,2,3]) for player in self.players}
		full = {}
		
		active = self._pick_active()
		active = self.players
		
		self.log.write('Active:', join_terms(active))
		
		# for player in self._pick_active():
		for player in active:
			full[player] = GameController()
			
			for i in range(self._pick_num()):
			# for i in range(3):
				group = full[player].new_group(f'group{i}', desc=f'description {i} ... 1 2 3')
				self._populate_actions(group, player)
				# group.extend(
				# 	[random.getrandbits(8) for _ in range(self._pick_num() * 2 + random.randint(0, 1))])
		
		return full
	
	def _populate_actions(self, group, player):
		# group.add(self.players, self.state.objs[:2])
		if random.randint(0,1):
			group.add(self.players, random.choices(self.state.objs, k=self._pick_num()))
		else:
			group.extend([random.getrandbits(8) for _ in range(self._pick_num() * 2 + random.randint(0, 1))])
	
	
	def begin_game(self):
		
		self.state.obj_cls = [type(f'Object{i}', (GameObject,), {}) for i in range(10)]
		self.state.objs = [random.choice(self.state.obj_cls)(name=f'obj{i}', **{f'key{j}': hex(random.getrandbits(32))
		                                                        for j in range(random.randint(2,5))})
		                   for i in range(10)]
		
		for player in self.players:
			player.score = 0
		
		self.log.writef('Starting game: player {}, obj {}', self.players[0], self.state.objs[0])
		
		return self._create_actions()
		
		
	def take_action(self, player, action):
		
		self.log.writef('{} played action {}', player, action)
		
		player = random.choice(self.players)
		player.score += random.randint(-10,10)
		
		return self._create_actions()
	
	
	def end_game(self):
		winner = random.choice(self.players)
		key = random.choice(self.state.objs)
		self.log.writef('{} wins because of {}', winner, key)
		return GameResult(winner=winner, scores={player:player.score for player in self.players}, key=key)










