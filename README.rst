######
Pyxbix
######

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

    pyfido -h
    usage: pyfido [-h] -u USERNAME [-n NUMBER] -p PASSWORD [-l] [-j] [-t TIMEOUT]

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            Fido username
      -n NUMBER, --number NUMBER
                            Fido phone number
      -p PASSWORD, --password PASSWORD
                            Password
      -l, --list            List phone numbers
      -j, --json            Json output
      -t TIMEOUT, --timeout TIMEOUT
                            Request timeout

Dev env
#######

::

    virtualenv -p /usr/bin/python3.5 env
    pip install -r requirements.txt 
