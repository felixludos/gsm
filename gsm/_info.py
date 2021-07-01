

name = 'gsm'
long_name = 'Game-Set-Match'

version = '0.1'
url = 'https://github.com/felixludos/gsm'

description = 'AI-centric interface for turn-based games'

author = 'Felix Leeb'
author_email = 'felixludos.info@gmail.com'

license = 'GPL3'

readme = 'README.md'

packages = ['gsm']

import os
try:
	with open(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'requirements.txt'), 'r') as f:
		install_requires = f.readlines()
except:
	install_requires = ['pyyaml',  'omnibelt'] # 'flask', 'flask_cors', 'requests',
del os


