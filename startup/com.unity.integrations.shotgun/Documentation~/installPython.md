# Bring your own Python

The Shotgun integration for Unity requires that you have Python installed with specific packages available.

## Windows
* Install Python 2.7 x64 (2.7.15 recommended, preferably under c:\Python27)
https://www.python.org/ftp/python/2.7.15/python-2.7.15.amd64.msi

The Python interpreter should be in a location listed in the PATH environment variable.
* Install PySide and rpyc
    * In a command prompt, go to c:\Python27\Scripts
    * pip.exe install PySide
    * pip.exe install rpyc

## Mac and Linux TBD

## Validation
To verify that your Python interpreter is properly configured, follow these steps:
* Launch a command prompt/shell
* Type "python"

The Python interpreter should launch. It should report a 64-bit version of Python 2.7

Run this [Python script](Python/validate_python.py):
* In the interpreter, use "execfile" to execute the script
* In a command prompt/shell, pass the script to the interpreter

