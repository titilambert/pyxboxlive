import asyncio
import argparse
import collections
import json
import sys

import click

from pyxboxlive import XboxLiveClient, REQUESTS_TIMEOUT
from pyxboxlive.gamerprofile import GamerProfile


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
def cli(ctx, username, password, timeout):
    if ctx.obj is None:
        ctx.obj = {}
    client = XboxLiveClient(username, password, timeout, loop=None)
    loop = asyncio.get_event_loop()
    fut = asyncio.wait([async_authenticate(client)])
    loop.run_until_complete(fut)
    ctx.obj['client'] = client


@cli.group(invoke_without_command=True)
@click.argument('gamertag', nargs=1,
              required=True,
              )
@click.pass_context
def gamerprofile(ctx, gamertag):
    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    fut = asyncio.wait([async_search(ctx.obj['client'], future, gamertag)])
    loop.run_until_complete(fut)
    ctx.obj['gamerprofile'] = future.result()
    print("Gamertag: {}".format(ctx.obj['gamerprofile'].gamertag))
    print("    XUID: {}".format(ctx.obj['gamerprofile'].xuid))


@gamerprofile.command()
@click.pass_context
def devices(ctx):
    loop = asyncio.get_event_loop()
    fut = asyncio.wait([ctx.obj['gamerprofile'].update_devices()])
    loop.run_until_complete(fut)
    print("Devices:")
    for device in ctx.obj['gamerprofile'].devices:
        print("    - {}".format(device.type_))
        for title in device.titles:
            print("        * {} - {} - {}".format(title.name, title.state, title.placement))


@cli.command()
@click.argument('gamertags', nargs=-1,
                required=True,
                )
@click.argument('message', nargs=1,
                required=True,
                )
@click.pass_context
def send_message(ctx, gamertags, message):
    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    fut = asyncio.wait([async_send_message(ctx.obj['client'], future, gamertags, message)])
    loop.run_until_complete(fut)
    print("Message sent")


def main():
    obj = {}
    try:
        cli(obj=obj)
        print("FFF")
    finally:
        obj['client'].close()


if __name__ == '__main__':
    main()
