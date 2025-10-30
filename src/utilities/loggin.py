LOGGIN=r"""
[loggers]
keys=root

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=consoleFormatter,fileFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[handler_consoleHandler]
class=StreamHandler
formatter=consoleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
formatter=fileFormatter
args=('%(logfilepath)s','a', 'utf-8')

[formatter_consoleFormatter]
format=%(levelname)s - %(asctime)s - %(name)s - %(funcName)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_fileFormatter]
format=%(levelname)s - %(asctime)s - %(name)s - %(funcName)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
"""