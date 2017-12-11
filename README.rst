##########
PyXboxlive
##########

References
##########
* https://github.com/dustinrue/PHP-XboxLiveClient
* https://github.com/Microsoft/xbox-live-trace-analyzer/blob/master/Source/XboxLiveTraceAnalyzer.APIMap.csv
* https://github.com/oakesja/xbox-live-api 
* https://github.com/titilambert/xbox-live-api
* https://github.com/joealcorn/xbox

TODO
####

* Add clips
* Add games
* 

Installation
############

::

    pip install pyxboxlive


Usage
#####

Print your current data

::

    pyxboxlive -u USERNAME -p PASSWORD


Print help

::

    pyxboxlive --help
    Usage: pyxboxlive [OPTIONS] COMMAND [ARGS]...

    Options:
      -u, --username TEXT    Xboxlive username  [required]
      -p, --password TEXT    Xboxlive password  [required]
      -t, --timeout INTEGER  Request Timeout
      --help                 Show this message and exit.

    Commands:
      gamerprofile
      send_message

Dev env
#######

::

    virtualenv -p /usr/bin/python3 env
    pip install -r requirements.txt 
