from termcolor import colored
from typing import Callable
from omnibelt import Packable, JSONABLE
from string import Formatter

from omnibelt import primitive

from ..features import Writable

from .manifest import Sanitizable
from .containers import GamePlayer

FMT = Formatter()


def _process_obj(obj):
	if isinstance(obj, primitive):
		return obj
	info = {}
	if isinstance(obj, Writable):
		info.update(obj.get_text_info())
		info['type'] = obj.get_text_type()
		info['val'] = obj.get_text_val()
	# elif isinstance(obj, Typed):
	# 	info['type'] = obj.get_type()
	# 	info['val'] = str(obj)
	else:
		info['type'] = obj.__class__.__name__
		info['val'] = str(obj)
	
	return info


def write(*objs, end=None, indent_level=None):
	if end is not None and len(end):
		objs = list(objs)
		objs.append(end)
	
	line = {'line': [_process_obj(obj) for obj in objs]}
	
	if indent_level is not None:
		line['level'] = indent_level
	
	return line


def writef(txt, *objs, end=None, indent_level=None, **kwobjs):
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
					raise FormatException('Unknown object info, type {}: {}'.format(type(info), info))
		
		if spec is not None and len(spec):
			obj = obj.__format__(spec)
		
		line.append(obj)
	
	return write(*line, end=end, indent_level=indent_level)


class GameLog(Sanitizable, Packable):
	
	
	def sanitize(self, player, manifest, sanitize):
		raise NotImplementedError
	
	def _add_line(self, line):
		targets = self.targets
		if self.targets is not None and len(self.targets):
			line['targets'] = [(t.name if isinstance(t, GamePlayer) else t) for t in targets]
		self.log.append(line)
		for update in self.update.values():
			update.append(line)
		self.targets = None
	
	def write(self, *objs, end=None, indent_level=None):
		if end is None:
			end = self.end
		if indent_level is None:
			indent_level = self.indent_level
		
		line = write(*objs, end=end, indent_level=indent_level)
		return self._add_line(line)
	
	def writef(self, txt, *objs, end=None, indent_level=None, **kwobjs):
		
		if end is None:
			end = self.end
		if indent_level is None:
			indent_level = self.indent_level
		
		line = writef(txt, *objs, end=end, indent_level=indent_level, **kwobjs)
		return self._add_line(line)


