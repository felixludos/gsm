
import sys, os, time
import random
from itertools import chain
import numpy as np
from collections import OrderedDict
from .signals import LoadInitFailureError
from .mixins import Transactionable, Savable

# _primitives = (str, int, float, bool)

def pack_savable(obj):
	
	if isinstance(obj, Savable):
		return {'_type': type(obj).__name__, '_data': obj.__getstate__()}
	if isinstance(obj, np.ndarray):
		return {'_type': 'numpy.ndarray', '_data': obj.tolist(),
		        '_dtype': obj.dtype}
	
	if isinstance(obj, tuple):
		return {'_type':'tuple', '_entries':[pack_savable(o) for o in obj]}
	# if isinstance(obj, dict):
	# 	return {'_type': 'dict', '_pairs':{k:pack_savable(v) for k,v in obj.items()}}
	# if isinstance(obj, list):
	# 	return {'_type': 'list', '_entries':[pack_savable(o) for o in obj]}
	# if isinstance(obj, set):
	# 	return {'_type': 'set', '_elements':[pack_savable(o) for o in obj]}
	
	try:
		assert isinstance(obj,
		                  (type(None), str, int, float,bool)
		                  ), 'All objects must be Savable subclasses or numpy arrays, or primitives: {}'.format(type(obj))
	except Exception as e:
		print(obj)
		raise e
	return obj
	
	# try:
	# 	return {'_type': type(obj).__name__, '_data': obj.__getstate__()}
	# except AttributeError:
	# 	if isinstance(obj, np.ndarray):
	# 		return {'_type': 'numpy.ndarray', '_data': obj.tolist(),
	# 		        '_dtype': obj.dtype}
	# 	assert isinstance(obj, (
	# 	type(None), str, int, float, bool)), 'All objects must be Savable subclasses or numpy arrays, or primitives: {}'.format(type(obj))
	# 	return obj


def unpack_savable(data, init_fn=None):
	if isinstance(data, dict) and '_type' in data:
		if data['_type'] == 'numpy.ndarray':
			return np.array(data['_data'], dtype=data['_dtype'])
		
		if data['_type'] == 'tuple':
			return (unpack_savable(x) for x in data['_entries'])
		# if data['_type'] == 'dict':
		# 	return {k:unpack_savable(v) for k,v in data['_pairs'].items()}
		# if data['_type'] == 'list':
		# 	return [unpack_savable(x) for x in data['_entries']]
		# if data['_type'] == 'set':
		# 	return {unpack_savable(x) for x in data['_elements']}
		
		cls = Savable.get_cls(data['_type'])
		
		try:
			obj = cls() if init_fn is None else init_fn(cls)
		except TypeError:
			raise LoadInitFailureError(data['_type'])
		
		obj.__setstate__(data['_data'])
		return obj
	
	assert isinstance(data, (
		type(None), str, int, float, bool)), 'All objects must be Savable subclasses or numpy arrays, or primitives: {}'.format(data)
	
	return data

class Container(Transactionable, Savable):
	
	def deepcopy(self):
		copy = type(self)()
		copy.__setstate__(self.__getstate__())
		return copy


class tdict(Container, OrderedDict):
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.__dict__['_data'] = OrderedDict(*args, **kwargs)
		self.__dict__['_shadow'] = None
		
	def in_transaction(self):
		return self._shadow is not None
		
	def begin(self):
		if self.in_transaction():
			self.abort()
			
		self._shadow = self._data
		
		for child in chain(self.keys(), self.values()):
			if isinstance(child, Transactionable):
				child.begin()
		
		self._data = self._data.copy()
		
	def commit(self):
		if not self.in_transaction():
			return
		
		for child in chain(self.keys(), self.values()):
			if isinstance(child, Transactionable):
				child.commit()
				
		self._shadow = None
	
	def abort(self):
		if not self.in_transaction():
			return
		for child in chain(self.keys(), self.values()):
			if isinstance(child, Transactionable):
				child.abort()
		
		self._data = self._shadow
		
	def update(self, other):
		self._data.update(other)
	def fromkeys(self, keys, value=None):
		self._data.fromkeys(keys, value)
		
	def clear(self):
		self._data.clear()
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __len__(self):
		return len(self._data)
	
	def __hash__(self):
		return id(self)
	def __eq__(self, other):
		return id(self) == id(other)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	def __reversed__(self):
		return self._data.__reversed__()
	
	def __iter__(self):
		return iter(self._data)
	def keys(self):
		return self._data.keys()
	def values(self):
		return self._data.values()
	def items(self):
		return self._data.items()
	
	def pop(self, key):
		return self._data.pop(key)
	def popitem(self):
		return self._data.popitem()
	def move_to_end(self, key, last=True):
		self._data.move_to_end(key, last)
	
	def __getstate__(self):
		state = {}
		state['_pairs'] = {key:pack_savable(value)
		                  for key, value in self.items()}
		
		state['_order'] = list(iter(self))
		return state
	
	def __setstate__(self, state):
		self._data.clear()
		for key in state['_order']:
			self._data[key] = unpack_savable(state['_pairs'][key])
	
	def get(self, k):
		return self._data.get(k)
	def setdefault(self, key, default=None):
		self._data.setdefault(key, default)
	
	def __getitem__(self, item):
		return self._data[item]
	def __setitem__(self, key, value):
		self._data[key] = value
	def __delitem__(self, key):
		del self._data[key]
		
	def __getattr__(self, item):
		if item in self.__dict__:
			return super().__getattribute__(item)
		return self.__getitem__(item)
	def __setattr__(self, key, value):
		if key in self.__dict__:
			return super().__setattr__(key, value)
		return self.__setitem__(key, value)
	def __delattr__(self, item):
		if item in self.__dict__:
			# raise Exception('{} cannot be deleted'.format(item))
			return super().__delattr__(item)
		return self.__getitem__(item)
	
	def __str__(self):
		return 'tdict({})'.format(', '.join([str(key) for key in iter(self)]))
	def __repr__(self):
		return 'tdict({})'.format(', '.join(['{}:{}'.format(repr(key), repr(value)) for key, value in self.items()]))
	
class tlist(Container, list):

	def __init__(self, *args, **kwargs):
		super().__init__()
		self._data = list(*args, **kwargs)
		# self.extend(iterable)
		self._shadow = None
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			self.abort()
		
		self._shadow = self._data
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.begin()
		
		self._data = self._data.copy()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.commit()
		
		self._shadow = None
	
	def abort(self):
		if not self.in_transaction():
			return
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.abort()
		
		self._data = self._shadow
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __getstate__(self):
		state = [pack_savable(elm) for elm in iter(self)]
		return state
	
	def __setstate__(self, state):
		self._data.clear()
		self._data.extend(unpack_savable(elm) for elm in state)
	
	def __getitem__(self, item):
		return self._data[item]
	def __setitem__(self, key, value):
		self._data[key] = value
	def __delitem__(self, idx):
		del self._data[idx]
		
	def __hash__(self):
		return id(self)
	def __eq__(self, other):
		return id(self) == id(other)
		
	def count(self, object):
		return self._data.count(object)
	
	def append(self, item):
		return self._data.append(item)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	
	def extend(self, iterable):
		return self._data.extend(iterable)
		
	def insert(self, index, object):
		self._data.insert(index, object)
		
	def remove(self, value):
		self._data.remove(value)
		
	def __iter__(self):
		return iter(self._data)
	def __reversed__(self):
		return self._data.__reversed__()
	
	def reverse(self):
		self._data.reverse()
		
	def pop(self, index=None):
		if index is None:
			return self._data.pop()
		return self._data.pop(index)
		
	def __len__(self):
		return len(self._data)
		
	def clear(self):
		self._data.clear()
		
	def sort(self, key=None, reverse=False):
		self._data.sort(key, reverse)
		
	def index(self, object, start=None, stop=None):
		self._data.index(object, start, stop)
	
	def __mul__(self, other):
		return self._data.__mul__(other)
	def __rmul__(self, other):
		return self._data.__rmul__(other)
	def __add__(self, other):
		return self._data.__add__(other)
	def __iadd__(self, other):
		self._data.__iadd__(other)
	def __imul__(self, other):
		self._data.__imul__(other)
		
	def __repr__(self):
		return '[{}]'.format(', '.join(map(repr, self)))
	def __str__(self):
		return '[{}]'.format(', '.join(map(str, self)))
	
class tset(Container, set):
	
	def __init__(self, iterable=[]):
		super().__init__()
		self._data = OrderedDict()
		for x in iterable:
			self.add(x)
		self._shadow = None
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			self.abort()
		
		self._shadow = self._data
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.begin()
		
		self._data = self._data.copy()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.commit()
		
		self._shadow = None
	
	def abort(self):
		if not self.in_transaction():
			return
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.abort()
		
		self._data = self._shadow
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __getstate__(self):
		state = [pack_savable(elm) for elm in iter(self)]
		return state
	
	def __setstate__(self, state):
		self._data.clear()
		self._data.update(unpack_savable(elm) for elm in state)

	def __hash__(self):
		return id(self)
	def __eq__(self, other):
		return id(self) == id(other)
	
	def __and__(self, other):
		copy = self.copy()
		for x in self:
			if x in other:
				copy.add(x)
			else:
				copy.remove(x)
		return copy
	def __or__(self, other):
		copy = self.copy()
		copy.update(other)
		return copy
	def __xor__(self, other):
		copy = self.copy()
		for x in list(other):
			if x in other:
				copy.add(x)
			else:
				copy.remove(x)
		return copy
	def __sub__(self, other):
		copy = self.copy()
		for x in other:
			copy.discard(x)
		return copy
	
	def __rand__(self, other):
		return self & other
	def __ror__(self, other):
		return self | other
	def __rxor__(self, other):
		return self ^ other
	def __rsub__(self, other):
		copy = other.copy()
		for x in self:
			copy.discard(x)
		return copy
	
	def difference_update(self, other):
		self -= other
	def intersection_update(self, other):
		self &= other
	def union_update(self, other):
		self |= other
	def symmetric_difference_update(self, other):
		self ^= other
	
	def symmetric_difference(self, other):
		return self ^ other
	def union(self, other):
		return self | other
	def intersection(self, other):
		return self & other
	def difference(self, other):
		return self - other
	
	def issubset(self, other):
		for x in self:
			if x not in other:
				return False
		return True
	def issuperset(self, other):
		for x in other:
			if x not in self:
				return False
		return True
	def isdisjoint(self, other):
		return not self.issubset(other) and not self.issuperset(other)
		
	def __iand__(self, other):
		for x in list(self):
			if x not in other:
				self.remove(x)
	def __ior__(self, other):
		self.update(other)
	def __ixor__(self, other):
		for x in other:
			if x in self:
				self.remove(x)
			else:
				self.add(x)
	def __isub__(self, other):
		for x in other:
			if x in self:
				self.remove(x)
	
	def pop(self):
		return self._data.popitem()[0]
	
	def remove(self, item):
		del self._data[item]
		
	def discard(self, item):
		if item in self._data:
			self.remove(item)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	
	def __len__(self):
		return len(self._data)
	
	def __iter__(self):
		return iter(self._data)
	
	def clear(self):
		return self._data.clear()
	
	def update(self, other):
		for x in other:
			self.add(x)
	
	def add(self, item):
		self._data[item] = None
		
	def __repr__(self):
		return '{' + ', '.join([repr(x) for x in self]) + '}'

	def __str__(self):
		return '{' + ', '.join([str(x) for x in self]) + '}'


