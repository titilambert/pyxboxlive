import asyncio
import argparse
import collections
import json
import sys

from pyxboxlive import XboxLiveClient, REQUESTS_TIMEOUT
from pyxboxlive.gamerprofile import GamerProfile


@asyncio.coroutine
def async_main(args):
    client = XboxLiveClient(args.username, args.password, args.timeout, loop=None)
    yield from client.authenticate()
    gamerprofile = yield from client.get_gamerprofile_from_gamertag(args.gamertag)
    gamerprofile2 = yield from client.get_gamerprofile_from_xuid(gamerprofile.xuid)
    yield from gamerprofile.update_devices()
    import ipdb;ipdb.set_trace()


def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        required=True, help='Xboxlibe username')
    parser.add_argument('-p', '--password',
                        required=True, help='Password')
    parser.add_argument('-l', '--list', action='store_true',
                        default=False, help='List phone numbers')
    parser.add_argument('-j', '--json', action='store_true',
                        default=False, help='Json output')
    parser.add_argument('-t', '--timeout',
                        default=REQUESTS_TIMEOUT, help='Request timeout')
    parser.add_argument('-x', '--xuid',
                        default=REQUESTS_TIMEOUT, help='Search for gamer profile using xuid')
    parser.add_argument('-g', '--gamertag',
                        default=REQUESTS_TIMEOUT, help='Search for gamer profile using gamertag')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    fut = asyncio.wait([async_main(args)])
    loop.run_until_complete(fut)


if __name__ == '__main__':
    sys.exit(main())
