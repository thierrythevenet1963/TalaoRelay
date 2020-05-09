import environment
import multiprocessing


bind = '127.0.0.1:4000'
workers = 4
#workers = multiprocessing.cpu_count()*2+1


loglevel = 'info'
# errorlog = os.path.join(_VAR, 'log/api-error.log')
# accesslog = os.path.join(_VAR, 'log/api-access.log')
errorlog = "-"
accesslog = "-"

timeout = 3 * 60  # 3 minutes
keepalive = 24 * 60 * 60  # 1 day
capture_output = True
