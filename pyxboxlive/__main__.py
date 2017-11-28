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
def async_authenticate(client):
    yield from client.authenticate()

@asyncio.coroutine
def async_search(client, future, gamertag):
    gamer_profile = yield from client.get_gamerprofile_from_gamertag(gamertag)
    future.set_result(gamer_profile)

@asyncio.coroutine
def async_send_message(client, future, gamertags, message):
    xuids = []
    for gamertag in gamertags:
        gamerprofile = yield from client.get_gamerprofile_from_gamertag(gamertag)
        xuids.append(gamerprofile.xuid)
    yield from client.send_message(xuids, message)

@click.group()
@click.option('--username', '-u',
              required=True,
              help='Xboxlive username')
@click.option('--password', '-p',
              required=True,
              help='Xboxlive password')
@click.option('--timeout', '-t',
              type=int,
              default=REQUESTS_TIMEOUT,
              help='Request Timeout')
@click.pass_context
def main(ctx, username, password, timeout):
    if ctx.obj is None:
        ctx.obj = {}
    client = XboxLiveClient(username, password, timeout, loop=None)
    try:
        loop = asyncio.get_event_loop()
        fut = asyncio.wait([async_authenticate(client)])
        loop.run_until_complete(fut)
        ctx.obj['client'] = client
    except OSError as exp:
        ctx.obj['client'].close()
        raise exp

@main.command()
@click.argument('gamertag', nargs=1,
              required=True,
              )
@click.pass_context
def search(ctx, gamertag):
    try:
        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        fut = asyncio.wait([async_search(ctx.obj['client'], future, gamertag)])
        loop.run_until_complete(fut)
        print(future.result())
    finally:
        ctx.obj['client'].close()
   

@main.command()
@click.argument('gamertags', nargs=-1,
                required=True,
                )
@click.argument('message', nargs=1,
                required=True,
                )
@click.pass_context
def send_message(ctx, gamertags, message):
    try:
        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        fut = asyncio.wait([async_send_message(ctx.obj['client'], future, gamertags, message)])
        loop.run_until_complete(fut)
    finally:
        ctx.obj['client'].close()


if __name__ == '__main__':
    main(obj={})
