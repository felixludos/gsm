from typing import Union
from itertools import chain, product
from omnibelt import Packable, primitive, Hashable

from ..features import Named
from .containers import GameContainer, ContainerSequence, ContainerGroup, ContainerMultiGroup


class ActionElement(Hashable, GameContainer):
	pass



class GameAction(Hashable, ContainerSequence):
	_content_key = 'action'
	
	def __init__(self, terms, group=None):
		super().__init__(terms)
		self.group = group
		
		
	def __eq__(self, action):
		return len(self) == len(action) and all(a==b for a,b in zip(self, action))
	


class GameActionGroup(Named, ContainerGroup):
	def __init__(self, name, desc=None):
		super().__init__(name=name)
		self.desc = desc
	
	
	def find(self, idx=None, pick=None, **unused):
		if idx is None:
			for action in self:
				if pick == action:
					return action
		else:
			return self[idx]
		
	
	@staticmethod
	def _process_elements(obj):
		assert isinstance(obj, ActionElement) or isinstance(obj, primitive), f'invalid type: {type(obj)}'
		return obj
	
	
	def _process_action(self, terms):
		if isinstance(terms, GameAction):
			return terms
		return GameAction([self._process_elements(term) for term in terms], group=self)
	
	
	@staticmethod
	def _expand_actions(obj):
		def _expand(code):
			# if isinstance(code, (list, set)) and len(code) == 1:
			# 	return _expand(next(iter(code)))
			
			# if isinstance(code, (ActionElement, *primitive)):
			# 	return [code]
			
			# tuple case
			if isinstance(code, tuple):
				return list(product(*map(_expand, code)))
			if isinstance(code, (list, set)):
				return chain(*map(_expand, code))
			
			# base case
			return [code]
		
		def _flatten(bla):
			output = []
			for item in bla:
				output.extend(_flatten(item) if isinstance(item, list) else [item])
			return tuple(output)
		
		code = _expand(obj)
		return list(map(_flatten, code))
	
	
	def _process_group(self, actions):
		return [self._process_action(action) for action in self._expand_actions(actions)]
	
	
	def append(self, action):
		action = self._process_action(action)
		super().append(action)
		return self
	
	
	def extend(self, actions):
		actions = self._process_group(actions)
		super().extend(actions)
		return self



class GameController(ContainerMultiGroup):
	_content_key = 'groups'
	
	
	def new_group(self, name, desc=None):
		group = GameActionGroup(name=name, desc=desc)
		self.append(group)
		return group


	def _parse_pick(self, obj):
		
		if isinstance(obj, int):
			return {'idx': obj}
		if isinstance(obj, list):
			return {'pick': obj}
		return obj
	

	def find(self, obj):
		
		pick = self._parse_pick(obj)
		
		if 'group' in pick:
			name = pick['group']
			offset = 0
			for group in self:
				if group.name == name:
					if 'idx' in pick:
						pick['idx'] -= offset
					return group.find(**pick)
				offset += len(group)
			
			raise Exception(f'group {name} not found')
			
		elif 'idx' in pick:
			idx = pick['idx']
			for group in self:
				if idx < len(group):
					pick['idx'] = idx
					return group.find(**pick)
				idx -= len(group)
			i = pick['idx']
			raise Exception(f'action index {i} is invalid')
		
		else:
			for group in self:
				out = group.find(**pick)
				if out is not None:
					return out
			
			raise Exception(f'cannot resolve action: {pick}')
		



