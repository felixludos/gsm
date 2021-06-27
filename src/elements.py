

import omnifig as fig

from humpack import adict

from jp_doodle import dual_canvas

from .colors import process_color, light_shade, dark_shade

OBJ_EVENTS = {
	'click', 'dblclick', 'mouseover', 'mouseup', 'mouseout', 'mousedown',
}

GLOBAL_EVENTS = {'keydown', 'keypress'}

RESOLTIONS = {
    '720': (1260, 720),
    '1080': (1920, 1080),
    '1440': (2560, 1440),
    '768': (1024, 768),
    '480': (640, 480),
    '960': (1280, 960),
    '1200': (1600,1200),
}

CV = None

def get_CV():
	if CV is None:
		create_canvas(fig.get_config())
	return CV

def _make_event_fn(event_name, obj):
	def _event_fn(ctx):
		nonlocal event_name, obj
		for fn in obj.events[event_name]:
			fn(obj, ctx)
	return _event_fn

def _include_canvas_event_utils(obj):
	def _add_event(event_name, callback):
		
		fns = obj.events[event_name]
		fns.append(callback)
		
		if len(fns) == 1:
			obj.on_canvas_event(event_name, _make_event_fn(event_name, obj))
	
	obj.add_event = _add_event
	
	def _clear_events(event_name=None):
		
		if event_name is None:
			for event_name in obj.events:
				_clear_events(event_name)
		
		fns = obj.events[event_name]
		
		if len(fns):
			obj.off_canvas_event(event_name)
		
		fns.clear()
	
	obj.clear_events = _clear_events


def _include_event_utils(obj):
	def _add_event(event_name, callback):
		
		fns = obj.events[event_name]
		fns.append(callback)
		
		if len(fns) == 1:
			obj.on(event_name, _make_event_fn(event_name, obj))
	
	obj.add_event = _add_event
	
	def _clear_events(event_name=None):
		
		if event_name is None:
			for event_name in obj.events:
				_clear_events(event_name)
		
		fns = obj.events[event_name]
		
		if len(fns):
			obj.off(event_name)
		
		fns.clear()
	
	obj.clear_events = _clear_events



@fig.Component('canvas')
def create_canvas(A):
	
	resolution = A.pull('resolution', 768)
	
	if isinstance(resolution, int):
		resolution = str(resolution)
	
	if not (isinstance(resolution, (list, tuple)) and len(resolution) == 2):
		resolution = RESOLTIONS[resolution]
	
	W, H = resolution
	
	cv = dual_canvas.DualCanvasWidget(width=W, height=H)
	
	_include_canvas_event_utils(cv)
	
	cv.W, cv.H = W, H
	cv.events = adict({event_name:[] for event_name in GLOBAL_EVENTS})

	global CV
	CV = cv
	
	return cv
	

@fig.Component('rect')
def create_rect(A):
	
	cv = get_CV()
	
	
	x,y = A.pull('x', 0), A.pull('y', 0)
	
	size = A.pull('size', 100)
	w, h = A.pull('width', size), A.pull('height', size)
	
	color = A.pull('color', 'red')
	color = process_color(color)
	
	degrees = A.pull('degrees', 0)
	
	kwargs = A.pull('kwargs', {})
	
	info = {
		'x':x, 'y':y, 'w':w, 'h':h,
		'color': color,
		'degrees': degrees,
		
		'original_color': color,
		
		'name': True,
		
		**kwargs
	}
	
	rect = cv.rect(**info)
	
	rect.info = info
	
	conv_responsive(rect, A)
	return rect

@fig.Component('circ')
def create_circ(A):
	raise NotImplementedError


def conv_responsive(obj, A):
	
	# events
	
	obj.events = {ename:[] for ename in OBJ_EVENTS}
	
	_include_event_utils(obj)
	
	
	# active state
	
	obj.active = A.pull('active', True)
	
	obj.is_active = lambda: obj.active
	
	def _update(**items):
		
		if 'base_color' in items and 'color' not in items:
			items['color'] = items['base_color']
		
		obj.info.update(**items)
	
		if 'base_color' in items:
			del items['base_color']

		obj.change(**items)
	
	obj.update = _update
	
	def _activate():
		
		if not obj.is_active():
			for ename in obj.events:
				if len(obj.events[ename]):
					obj.on(ename)
		
		obj.update(color=obj.info['original_color'])
		obj.active = True
		
	obj.activate = _activate
	
	def _deactivate():
		
		if obj.is_active():
			for ename in obj.events:
				if len(obj.events[ename]):
					obj.off(ename)
		
		obj.update(color='#222222')
		obj.active = False
		
	obj.deactivate = _deactivate

	# button responsiveness
	
	is_button = A.pull('button', True)
	
	
	def _make_change_color(light=False, dark=False):
		
		def _action(obj, ctx):
			
			color = obj.info['base_color']
			
			if light:
				color = light_shade(color)
			if dark:
				color = dark_shade(color)
			
			obj.update(color=color)
		return _action
	
	if is_button:
		obj.add_event('mouseover', _make_change_color(light=True))
		obj.add_event('mousedown', _make_change_color(dark=True))
		obj.add_event('mouseup', _make_change_color(light=True))
		obj.add_event('mouseout', _make_change_color())
		
		
		pass
	
	
	pass


def make_button(obj, callback, params):
	
	
	
	pass


