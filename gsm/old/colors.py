
import webcolors

def process_color(raw):
	full = webcolors.html5_parse_legacy_color(raw)
	return webcolors.rgb_to_hex(full)

def greyit(color, pull=0.5, base=0.1):
	c = webcolors.html5_parse_legacy_color(color)
	
	vals = (c.red, c.green, c.blue)
	
	if base is not None:
		vals = [max(v,base) for v in vals]
	
	avg = sum(vals) / 3
	
	assert 0 < pull <= 1, pull
	
	vals = [max(0,min(int(pull*avg + (1-pull)*v),255)) for v in vals]
	
	return webcolors.rgb_to_hex(webcolors.HTML5SimpleColor(*vals))

def dimmer(color, dim=0.3):
	c = webcolors.html5_parse_legacy_color(color)
	
	vals = (c.red, c.green, c.blue)

	assert 0 < dim <= 1, dim
	
	vals = [int(v*(1-dim)) for v in vals]

	return webcolors.rgb_to_hex(webcolors.HTML5SimpleColor(*vals))
	

def light_shade(raw):
	return dimmer(raw, 0.2)

def dark_shade(raw):
	return dimmer(raw, 0.4)
