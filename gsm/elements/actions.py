from typing import Union
import inspect
from itertools import chain, product
from omnibelt import Packable, primitive, Hashable, get_printer

from ..features import Named
from .containers import GameContainer, ActionElement, \
	ContainerSequence, ContainerGroup, ContainerMultiGroup, ContainerFormatter

prt = get_printer(__name__)


class GameAction(Hashable, ContainerSequence):
	_content_key = 'action'
	
	def __init__(self, *terms, group=None):
		super().__init__(terms)
		self.group = group
	
	
	def to_string(self, formatter=None):
		if formatter is None:
			formatter = ActionFormatter()
		return formatter.draw_sequence(self)
	
	
	def __str__(self):
		return self.to_string()
		
		
	def __eq__(self, action):
		return len(self) == len(action) and all(a==b for a,b in zip(self, action))
	


class GameActionGroup(Named, ContainerGroup):
	def __init__(self, name=None, desc=None):
		super().__init__(name=name)
		self.desc = desc
	
	
	def to_string(self, formatter=None):
		if formatter is None:
			formatter = ActionFormatter()
		return formatter.draw_group(self)
	
	
	def __str__(self):
		return self.to_string()
	
	
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
		return GameAction(*[self._process_elements(term) for term in terms], group=self)
	
	
	@staticmethod
	def _expand_actions(obj):
		def _expand(code):
			# tuple case
			if isinstance(code, tuple):
				return list(product(*map(_expand, code)))
			if isinstance(code, (list, set)):
				return list(map(_expand, code))
			
			# base case
			return [code, ]
		def _pre(bla):
			if isinstance(bla, (list, set)):
				return [_pre(b) for b in bla]
			if not isinstance(bla, tuple):
				bla = (bla,)
			return bla
		def _flatten(bla):
			if isinstance(bla, list):
				out = []
				for b in bla:
					if isinstance(b, list):
						out.extend(_flatten(b))
					else:
						out.append(_flatten(b))
				return out
			output = []
			for item in bla:
				output.extend(item if isinstance(item, list) else [item])
			return tuple(output)
		
		obj = _pre(obj)
		code = _expand(obj)
		return _flatten(code)
	
	
	def _process_group(self, actions):
		done = [action for action in actions if isinstance(action, GameAction)]
		todo = [action for action in actions if not isinstance(action, GameAction)]
		expanded = done + self._expand_actions(todo)
		# expanded = self._expand_actions(actions)
		return [self._process_action(action) for action in expanded]
	
	
	def add(self, *terms):
		self.append(terms)
		return self
		
	
	def append(self, action):
		self.extend([action])
		return self
	
	
	def extend(self, actions):
		# if inspect.isgeneratorfunction(actions):
		# 	print(actions)
		# 	actions = list(actions)
		actions = self._process_group(actions)
		super().extend(actions)
		return self



class ActionFormatter(ContainerFormatter):
	def draw_sequence(self, seq):
		return getattr(seq, 'delimiter', ' - ').join(super().draw_sequence(seq))
	
	
	def draw_group(self, group, index_offset=0):
		actions = [f'{action.idx:>4} : {msg}' for i, (action, msg) in enumerate(zip(group,
		                                                                            super().draw_group(group)))]
		title = f'{group.name}: {group.desc}'
		return '\n'.join([title, *actions])
	
	
	def draw_multigroup(self, multi):
		offset = 0
		groups = []
		for group in multi:
			groups.append(self.draw_group(group, index_offset=offset))
			offset += len(group)
		
		return getattr(multi, 'separator', _DEFAULT_GROUP_SEPARATOR).join(groups)



# _DEFAULT_GROUP_SEPARATOR = '\n' + '-'*20 + '\n'
_DEFAULT_GROUP_SEPARATOR = '\n'



class GameController(ContainerMultiGroup):
	_content_key = 'groups'
	
	def __send__(self, user, obj):
		
		
		
		total = obj.total_size()
		if total == 0:
			prt.error(f'Sending a game controller without any actions')
		
		idx = 0
		for group in obj:
			for action in group:
				action.idx = idx
				idx += 1
		
		# print(idx)
		
		return obj
	
	
	def total_size(self):
		return sum(map(len, self))
	
	
	def to_string(self, formatter=None):
		if formatter is None:
			formatter = ActionFormatter()
		return formatter.draw_multigroup(self)
	
	
	def __str__(self):
		return self.to_string()
	
	
	def add_group(self, name, desc=None, actions=None):
		group = self.new_group(name, desc=desc)
		if actions is not None:
			group.extend(actions)
		return self
	
	
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
		



