import asyncio
import logging
from typing import Awaitable, Optional, List, Union
from asyncio import StreamReader, StreamWriter

logging.basicConfig(level=logging.DEBUG)
HOST = "127.0.0.1"
PORT = 4040
NUM_TRIES = 1

mem = dict()


def _log(name: str) -> str:
    """Returns a string with the input argument"""
    return f"Currently executing {name}"


async def handle_echo(reader: StreamReader, writer: StreamWriter) -> Optional[Awaitable[None]]:
    """Handles incoming data and returns"""
    while True:
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        # TODO implement function calls based on message

        print(f"Send: {data!r}")
        writer.write(data)
        await writer.drain()
    else:
        print("Close the connection")
        writer.close()


def set_(key: Union[int, str], val: Union[int, str]) -> str:
    """Will set a key-value pair in our database. If the key is already present the value will be overwritten. If the
    key is not present, the key-value pair will be inserted."""
    logging.debug(_log(set_.__name__))
    mem[key] = val
    return "OK"


def get_(key: Union[int, str]) -> Union[int, str, None]:
    """Will return the value paired up with the requested key. If the key does not exists, null is returned."""
    logging.debug(_log(get_.__name__))
    return mem.get(key)


async def mset_(*args: Union[int, str]) -> str:
    """Variations of get and set, where we work with a set of key-value pairs."""
    logging.debug(_log(mset_.__name__))
    if len(args) % 2 != 0 or len(args) == 0:
        logging.info("missing key/value pair")
        return "ERROR"
    for key, val in zip(args[0::2], args[1::2]):
        logging.debug(f"received: {{{key}: {val}}}")
        for i in range(0, NUM_TRIES):
            while True:
                try:
                    set_(key, val)
                except Exception as e:
                    logging.error(e)
                finally:
                    break
    return "OK"


async def mget_(*args: Union[int, str]) -> List[Union[int, str]]:
    """Variations of get and set, where we work with a set of key-value pairs."""
    logging.debug(_log(mget_.__name__))
    lst = list()
    for key in args:
        for i in range(0, NUM_TRIES):
            while True:
                try:
                    lst.append(get_(key))
                except Exception as e:
                    logging.error(e)
                finally:
                    break
    logging.debug(f"received: {lst}")
    return lst


async def exists_(key: Union[int, str]) -> bool:
    """Boolean operator that checks if the key is in our database."""
    logging.debug(_log(exists_.__name__))
    return key in mem


async def setnotexists_(key: Union[int, str], val: Union[int, str]) -> str:
    """Insert a key value pair only if the key is not already in our database."""
    logging.debug(_log(setnotexists_.__name__))
    if not await exists_(key):
        return set_(key, val)
    return "Key already exists"


async def setexists_(key: Union[int, str], val: Union[int, str]) -> str:
    """Update a key value pair only if the key is already there."""
    logging.debug(_log(setexists_.__name__))
    if await exists_(key):
        return set_(key, val)
    return "Key does not exist"


async def cset_(key: Union[int, str], old_val: Union[int, str], new_val: Union[int, str]) -> Union[int, str, None]:
    """Set the new value only if the old one is equal with a given value."""
    logging.debug(_log(cset_.__name__))
    if get_(key) == old_val:
        return set_(key, new_val)
    return None


# inc, dec, incby, decby
async def inc_(key: Union[int, str], n: int = 1) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string. If the value
    can not be parsed as integer, null is returned. If the operation is successful the old and new value is returned."""
    val = get_(key)
    try:
        val += n
        return set_(key, val)
    except TypeError as e:
        logging.exception(e)
        return None


async def dec_(key: Union[int, str], n: int = 1) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string. If the value
    can not be parsed as integer, null is returned. If the operation is successful the old and new value is returned."""
    return await inc_(key, -n)


async def incby_(key: Union[int, str], n: int) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string. If the value
    can not be parsed as integer, null is returned. If the operation is successful the old and new value is returned."""
    return await inc_(key, n)


async def decby_(key: Union[int, str], n: int) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string. If the value
    can not be parsed as integer, null is returned. If the operation is successful the old and new value is returned."""
    return await inc_(key, -n)


async def main():
    # commands such as below could be used for running above functions without a server
    # logging.info(await set_('foo', 0))
    # logging.info(await setnotexists_('fooz', 'bar'))
    # logging.info(await setnotexists_('foo', 'bar'))
    # logging.info(await setexists_('foo', 'bar'))
    # await mset_('key1', 'val1', 'key2')
    # await mset_('key1', 'val1', 'key2', 'val2')
    # await mget_('key1', 'key2')
    # logging.info(await exists_('nothing'))
    # logging.info(await cset_('foo', 'bar', 'baz'))
    # logging.info(await cset_('foo', 'bar', 'ba'))
    # logging.info(await inc_('foo'))
    # logging.info(await get_('foo'))
    # logging.info(await dec_('foo'))
    # logging.info(await get_('foo'))
    # logging.info(await incby_('foo', 5))
    # logging.info(await get_('foo'))
    # logging.info(await decby_('foo', 3))
    # logging.info(await get_('foo'))

    server = await asyncio.start_server(handle_echo, host=HOST, port=PORT)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
