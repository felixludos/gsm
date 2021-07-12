from termcolor import colored
from typing import Callable
from omnibelt import Packable, JSONABLE
from string import Formatter
from termcolor import colored

from omnibelt import primitive

from ..features import Writable, Typed
from ..errors import FormatException

from .manifest import Sanitizable
from .containers import GameContainer, ContainerFormatter, ContainerSequence, ContainerGroup

FMT = Formatter()


class LogFormatter(ContainerFormatter):
	
	def __init__(self, flags='default', **other):
		super().__init__(**other)
		
		if flags == 'default':
			flags = {'error':'red', 'debug':'grey', 'warning':'yellow'}
		self.flags = flags
	
	
	def draw_sequence(self, entry):
		color = self.flags.get(getattr(entry, 'flag', None), None)
		return ''.join([getattr(entry, 'indent_unit', '  ')*getattr(entry, 'indent', 0),
		                getattr(entry, 'delimiter', ' ').join((term if color is None else colored(term, color))
		                                                       for term in super().draw_sequence(entry)),
		                getattr(entry, 'end', '')])


	def draw_group(self, group):
		return getattr(group, 'delimiter', '').join(super().draw_group(group))



class GameLogEntry(ContainerSequence):
	
	def to_string(self, formatter=None):
		if formatter is None:
			formatter = LogFormatter()
		return self.draw(formatter)
		
	
	def __str__(self):
		return self.to_string()



class GameLog(ContainerGroup):
	def __init__(self, *args, pointers=None, **kwargs):
		if pointers is None:
			pointers = {}
		super().__init__(*args, **kwargs)
		self.pointers = pointers
		
	
	def get_update(self, player: 'GamePlayer') -> 'GameLog':
		ref = self.pointers.get(player, 0)
		update = self[ref:]
		
		self.pointers[player] = len(self)
		
		return update
	
	
	def get_full(self, player: 'GamePlayer' = None) -> 'GameLog':
		return self
	
	
	def to_string(self, log=None, player=None, formatter=None):
		if log is None:
			log = self.get_full(player=player)
		
		if formatter is None:
			formatter = LogFormatter()
		
		return formatter.draw_group(log)
		
		
	def __str__(self):
		return self.to_string()
	
	
	@classmethod
	def _process_line(cls, objs, end='\n', flag=None, **info):
		return GameLogEntry(objs, end=end, flag=flag, **info)
	
	
	def debug(self, *objs, end='\n'):
		return self.write(*objs, end=end, flag='debug')

	
	def error(self, *objs, end='\n'):
		return self.write(*objs, end=end, flag='error')
	
	
	def warning(self, *objs, end='\n'):
		return self.write(*objs, end=end, flag='warning')
	
	
	def write(self, *objs, end='\n', flag=None, info={}):
		return self.append(self._process_line(objs, end=end, flag=flag, **info))
	
	
	def writef(self, txt, *objs, end='\n', flag=None, info={}, **kwobjs):
		
		line = []
		
		pos = 0
		
		for pre, info, spec, _ in FMT.parse(txt):
			
			line.append(pre)
			
			if info is None:
				continue
			elif info in kwobjs:
				obj = kwobjs[info]
			else:
				try:
					obj = objs[int(info)]
				except ValueError:
					if info == '':
						obj = objs[pos]
						pos += 1
					else:
						raise FormatException(f'Unknown object info, type {type(info)}: {info}')
			
			if spec is not None and len(spec):
				obj = obj.__format__(spec)
			
			line.append(obj)
		
		return self.append(self._process_line(line, end=end, flag=flag, **info))


