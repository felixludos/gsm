import sys
import traceback

# general

class UnknownElementError(Exception):
	'''
	Error thrown when trying to jsonify/unjsonify and an unknown object is found
	A common solution for custom objects is to make them :ref gsm.util.Jsonable.
	'''
	def __init__(self, obj):
		super().__init__('Cannot un/jsonify {}: {}'.format(type(obj), obj))

# Control flow Exceptions

class GameOver(Exception):
	'''
	Flag to be raised anywhere in a GamePhase or GameObject to end a game.
	'''
	pass

class PhaseComplete(Exception):
	'''
	Flag to be raised anywhere in a GamePhase or GameObject to end phase and move on to the next one in the GameStack.
	'''
	def __init__(self, transfer=False): # transfer action to next phase
		'''
		
		:param transfer: if true then the current action will be sent to the next phase (default: False)
		'''
		super().__init__()
		self.transfer = transfer
		
	def transfer_action(self):
		'''
		Says whether the action should be transferred
		:return: bool whether or not the action should be sent to the next phase
		'''
		return self.transfer

class SwitchPhase(Exception): # possibly can include an action and player
	'''
	Flag to be raised anywhere in a GamePhase or GameObject to switch the current phase
	'''
	def __init__(self, phase, stack=True, send_action=False, **kwargs):
		'''
		
		:param phase: name of a registered phase or an instance of a registered phase to switch to
		:type phase: str or GamePhase
		:param stack: Add current phase back to phase stack so the game will return to the current phase after this
		new one is complete
		:type stack: bool
		:param send_action: Pass current action into the new phase
		:type: send_action: bool
		:param kwargs: optional kwargs to be passed into new phase if it is just the name of a phase
		:type kwargs: any other keyword arguments
		'''
		super().__init__()
		self.phase = phase
		self.stack = stack
		self.send_action = send_action
		self.kwargs = kwargs
		
	def transfer_action(self):
		'''
		
		:return: flag whether the action should be copied to the new phase
		:rtype: bool
		'''
		return self.send_action
		
	def stacks(self):
		'''
		
		:return: flag whether the current phase should be added back to the stack before beingging the new phase
		:rtype: bool
		'''
		return self.stack
		
	def get_phase(self):
		'''
		
		:return: new phase to switch to
		'''
		return self.phase
	
	def get_phase_kwargs(self):
		'''
		
		:return: keyword arguments for new phase (only used if it must be created)
		'''
		return self.kwargs

# Controller errors

class InvalidKeyError(Exception):
	'''
	Error if a key is not found in a dict like object
	'''
	pass

class InvalidPlayerError(Exception):
	'''
	Error if an unregistered player is referenced
	'''
	def __init__(self, player):
		super().__init__('Invalid player: {}'.format(player))

# Controller registry errors

class ClosedRegistryError(Exception):
	'''
	The registries close after the game begins, so no new players, phases types, game object types,
	or config files can be registered.
	'''
	pass

class RegistryCollisionError(Exception):
	'''
	When registering a new key (in any registry), this error is thrown if such a key is already in the register.
	'''
	def __init__(self, key):
		super().__init__('The key {} has already been registered'.format(key))

class MissingTypeError(Exception):
	'''
	When using an object, if the object is not registered but should be, this error is thrown.
	'''
	def __init__(self, obj, *typs):
		super().__init__('Before loading {} you must register: {}'.format(obj.__class__.__name__, ', '.join(typs)))

class MissingObjectError(Exception):
	'''
	When creating a GameObject this error is thrown if the obj_type of the GameObject has not been registered.
	'''
	def __init__(self, name):
		super().__init__('{} is not a recognized GameObject type, have you registered it?'.format(name))

class NoActiveGameError(Exception):
	'''
	Error thrown when GameController.step() is called before calling GameController.reset() (to start a game)
	'''
	pass

# host errors

class InvalidValueError(Exception):
	'''Unknown value given to the host'''
	def __init__(self, name):
		super().__init__('Unknown value: {}'.format(name))

class UnknownUserError(Exception):
	'''
	Users must be registered before they call host methods
	'''
	pass
class UnknownPlayerError(Exception):
	'''
	Players must be registered in the host.
	'''
	pass

class UnknownGameError(Exception):
	'''
	Error thrown if a game is selected that has not been registered to the host.
	'''
	pass
class UnknownInterfaceError(Exception):
	'''
	Error thrown if an unknown interface is used in the GameHost
	'''
	pass

# class LoadConsistencyError(Exception):
# 	'''
#
# 	'''
# 	pass

class WrappedException(Exception):
	'''
	Exception wrapper used for passing exceptions thrown in a parallel process to be thrown in the main process.
	'''
	def __init__(self, etype, emsg, where=None):
		super().__init__('')
		self.etype = etype
		self.emsg = emsg
		self.where = where

class ExceptionWrapper(object):
	r"""Wraps an exception plus traceback to communicate across threads"""
	def __init__(self, interface=None):
		# It is important that we don't store exc_info, see
		# NOTE [ Python Traceback Reference Cycle Problem ]
		exc_info = sys.exc_info()
		self.exc_type = exc_info[0]
		self.exc_msg = "".join(traceback.format_exception(*exc_info))
		self.where = interface

	def reraise(self):
		r"""Reraises the wrapped exception in the current thread"""
		# Format a message such as: "Caught ValueError in DataLoader worker
		# process 2. Original Traceback:", followed by the traceback.
		# msg = "Caught {} {}.\nOriginal {}".format(
		# 	self.exc_type.__name__, self.where, self.exc_msg)
		raise WrappedException(self.exc_type, self.exc_msg, self.where)

# action errors
		
class InvalidActionError(Exception):
	'''Error thrown if the action is not recognized'''
	def __init__(self, action):
		super().__init__('{} is an invalid action'.format(str(action)))
		
class ActionMismatch(Exception):
	'''Flag thrown by an ActionTuple if any element doesn't match (used while trying to match the received action
	to the possible ones).'''
	pass

class UnknownActionElement(Exception):
	'''Error thrown if no possible action recognizes a certain element'''
	def __init__(self, obj):
		super().__init__('Unknown action element: {}, type: {}'.format(str(obj), type(obj)))
		self.obj = obj

# object errors

class InvalidInitializationError(Exception):
	'''GameObjects and phases should be created through the GameController using GameController.create_obj
	and GameController.create_phase.'''
	def __init__(self):
		super().__init__('All GameObjects Must be created through the GameTable.create')

class MissingValueError(Exception):
	'''This error is thrown when a GameObject or GamePlayer is created without a required property
	(required properties are specified when registering)'''
	def __init__(self, typ, missing, *reqs):
		super().__init__('{} is missing {}, requires a value for: {}'.format(typ, missing, ', '.join(reqs)))


# game table errors

class ObjectIDCollisionError(Exception):
	'''Error thrown when specifying a GameObject's ID when creating it, and the ID already exists'''
	def __init__(self, ID):
		super().__init__('A GameObject with ID {} already exists'.format(ID))

# class ZombieObjectException(Exception): # gets thrown when a SETTER is called from a GameObject even after it was removed from the game table
# 	def __init__(self, obj):
# 		super().__init__('{} has already beem removed from the GameTable'.format(repr(obj)))

# logging

class FormatException(Exception):
	'''Unknown formatting information'''
	pass

# wrapper for multiprocessing


