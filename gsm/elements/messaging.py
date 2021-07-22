from typing import Tuple, TypeVar
from omnibelt.packing import Packable, Packer

from .roles import User


T = TypeVar('T')
Message = Tuple[T]


class Sendable(Packable):
	def __recover__(self, obj: 'Sendable') -> 'Sendable':
		return obj
	
	
	def __send__(self, user: User, obj: 'Sendable') -> 'Sendable':
		return obj



class Messaging(Packer):
	def __init__(self):
		super().__init__()
		self.user = None
	
	
	def _dispatch_pack(self, entry, obj):
		if isinstance(obj, Sendable):
			obj = obj.__send__(self.user, obj)
		return super()._dispatch_pack(entry, obj)
	
	
	def _dispatch_unpack(self, entry, obj, data):
		obj = super()._dispatch_unpack(entry, obj, data)
		if isinstance(obj, Sendable):
			obj = obj.__recover__(obj)
		return obj
	
	
	def send(self, user: User, obj: T) -> Message[T]:
		self.user = user
		data = self.pack(obj)
		self.user = None
		return data
	
	
	def recover(self, data: Message[T]) -> T:
		obj = self.unpack(data)
		return obj



