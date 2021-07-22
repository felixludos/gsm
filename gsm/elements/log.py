from termcolor import colored
from typing import Callable
from itertools import chain
from omnibelt import Packable, JSONABLE, get_printer, primitive
from string import Formatter
from termcolor import colored

from ..features import Writable, Typed
from ..errors import FormatException

from .containers import GameContainer, ContainerFormatter, ContainerSequence, ContainerGroup

prt = get_printer(__file__)
log_mirror = get_printer('GAME-LOG')

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
		                getattr(entry, 'delimiter', ' ').join((term if color is None else self.color_text(term, color))
		                                                       for term in super().draw_sequence(entry)),
		                getattr(entry, 'end', '')])


	def draw_group(self, group):
		return getattr(group, 'delimiter', '').join(super().draw_group(group))



def join_terms(objs, sep=', ', conjunction=None, info={}):
	terms = [objs[0]] + list(chain(*zip([sep]*(len(objs)-1), objs[1:])))
	if conjunction is not None:
		if len(objs) == 2:
			terms[1] = conjunction
		elif len(objs) > 2:
			terms.insert(-2, conjunction)
	return GameLogEntry(terms, **info)



class GameLogEntry(ContainerSequence):
	def __init__(self, terms=[], **info):
		super().__init__(**info)
		self.extend(terms)
	
	
	def to_string(self, formatter=None):
		if formatter is None:
			formatter = LogFormatter()
		return self.draw(formatter)
		
		
	def append(self, term):
		if isinstance(term, GameLogEntry):
			self.__dict__.update(term.__dict__)
			self.extend(term)
		else:
			super().append(term)
		
		
	def extend(self, terms):
		for term in terms:
			self.append(term)
	
	
	def __str__(self):
		return self.to_string()



class GameLog(ContainerGroup):
	def __init__(self, *args, pointers=None, mirror_log=True, **kwargs):
		if pointers is None:
			pointers = {}
		super().__init__(*args, **kwargs)
		self.pointers = pointers
		self.mirror_log = mirror_log
		
	
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
		line = self._process_line(objs, end=end, flag=flag, **info)
		if self.mirror_log:
			if flag == 'error':
				log_mirror.error(str(line))
			elif flag == 'warning':
				log_mirror.warning(str(line))
			elif flag == 'debug':
				log_mirror.debug(str(line))
			else:
				log_mirror.info(str(line))
		return self.append(line)
	
	
	def writef(self, txt, *objs, end='\n', flag=None, info={}, **kwobjs):
		
		line = []
		
		pos = 0
		
		if 'delimiter' not in info:
			info['delimiter'] = ''
		
		for pre, vals, spec, _ in FMT.parse(txt):
			
			line.append(pre)
			
			if vals is None:
				continue
			elif vals in kwobjs:
				obj = kwobjs[vals]
			else:
				try:
					obj = objs[int(vals)]
				except ValueError:
					if vals == '':
						obj = objs[pos]
						pos += 1
					else:
						raise FormatException(f'Unknown object info, type {type(vals)}: {vals}')
			
			if spec is not None and len(spec):
				obj = obj.__format__(spec)
			
			line.append(obj)
		
		return self.write(*line, end=end, flag=flag, info=info)


