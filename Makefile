build:
	mpy-cross src/httpd.py -o mpy/httpd.mpy
	mpy-cross src/isomorp_utils.py -o mpy/isomorp_utils.mpy
	mpy-cross src/mime_types.py -o mpy/mime_types.mpy
	mpy-cross src/mws.py -o mpy/mws.mpy

test:
	pytest tests/*