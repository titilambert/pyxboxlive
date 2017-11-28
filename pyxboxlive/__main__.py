import asyncio
import argparse
import collections
import json
import sys

import click

from pyxboxlive import XboxLiveClient, REQUESTS_TIMEOUT
from pyxboxlive.gamerprofile import GamerProfile

def print_output(gamer_profile):

    print(gamer_profile)

@asyncio.coroutine
def async_main(args):
    client = XboxLiveClient(args.username, args.password, args.timeout, loop=None)
    yield from client.authenticate()
    gamer_profile = yield from client.get_gamerprofile_from_gamertag(args.gamertag)
    gamer_profile2 = yield from client.get_gamerprofile_from_xuid(2533274900896326)
    yield from gamer_profile.update_devices()
    response = yield from client.send_message([gamer_profile.xuid, client.user_xid], "test")
    text = yield from response.text()
    import ipdb;ipdb.set_trace()
    client.close()
    print_output(gamer_profile)

@asyncio.coroutine
def sync_authenticate(client):
    yield from client.authenticate()

@asyncio.coroutine
def sync_search(client, gamertag):
    gamer_profile = yield from client.get_gamerprofile_from_gamertag(gamertag)
    return gamer_profile

@click.group()
@click.option('--username', prompt='Username',
              help='Xboxlive username')
@click.option('--password', prompt='Password',
              help='Xboxlive password')
@click.option('--timeout', prompt='Timeout',
              required=False,
              type=int,
              default=REQUESTS_TIMEOUT,
              help='Request Timeout')
@click.pass_context
def main(ctx, username, password, timeout):
    if ctx.obj is None:
        ctx.obj = {}
    client = XboxLiveClient(username, password, timeout, loop=None)
    loop = asyncio.get_event_loop()
    fut = asyncio.wait([sync_authenticate(client)])
    loop.run_until_complete(fut)
    ctx.obj['client'] = client

#    loop = asyncio.get_event_loop()
#    fut = asyncio.wait([async_main(args)])
#    loop.run_until_complete(fut)


@main.command()
@click.option('--gamertag', prompt='Gamertag',
              help='Gamertag')
@click.pass_context
def search(ctx, gamertag):
    loop = asyncio.get_event_loop()
    fut = asyncio.wait([sync_search(ctx.obj['client'], gamertag)])
    loop.run_until_complete(fut)
   

if __name__ == '__main__':
    main(obj={})
