import sys
# Python version (expected: 2.7 64 bit)
try:
	import platform
	version = platform.python_version()
	tokens = version.split('.')

	if len(tokens) < 2 or int(tokens[0]) != 2 or int(tokens[1]) != 7:
		print('ERROR: invalid Python version. Expected 2.7.x, got %s'%version)
		sys.exit(1)
	
	(bits,_) = platform.architecture()
	if bits != '64bit':
		print('ERROR: invalid architecture. Expected "64bit", got "%s"'%bits)
		sys.exit(1)
	
except:
	print('ERROR: could not determine the Python version')
	sys.exit(1)

# PySide 
try:
	import PySide
except:
	print('ERROR: could not import PySide')
	sys.exit(1)

# rpyc
try:
	import rpyc
except:
	print('ERROR: could not import rpyc')
	sys.exit(1)
	
print('SUCCESS: The Python interpreter is properly configured for Shotgun in Unity')