import asyncio
import functools
import logging
from typing import Awaitable, Callable, Optional, List, Union

logging.basicConfig(level=logging.INFO)
HOST = "127.0.0.1"
PORT = 4040
NUM_TRIES = 3

mem = dict()
lock = asyncio.Lock()


def _log(name: str) -> str:
    """Returns a string with the input argument"""
    return f"Currently executing function '{name}'"


def log_name(func: Callable) -> Callable:
    """Decorator that logs the name of the function being executed"""
    @functools.wraps(func)
    def wrapper(*args: Union[int, str], **kwargs: Union[int, str]):
        logging.debug(_log(func.__name__))
        return func(*args, **kwargs)
    return wrapper


async def handle_echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Optional[Awaitable[None]]:
    """Handles incoming data and returns"""
    dispatch = get_dispatch()
    while True:
        data = await reader.read(100)
        message = data.decode().rstrip(' \n')
        address = writer.get_extra_info('peername')
        logging.info(f"Received {message!r} from {address!r}")

        func_name, *args = message.split(' ')
        logging.debug(f"Received following function name and arguments: {func_name} and {args}")

        res_func = dispatch.get(func_name.lower())
        try:
            result = await res_func(*args)
        except TypeError as t:
            logging.exception(t)
            if res_func is not None:
                logging.error("User did not provide correct number of arguments")
                result = "Incorrect number of arguments provided, please try again"
            else:
                logging.error("User requested unknown function")
                result = f"Function '{func_name}' not available, provide 'list' to see which functions are available"
        except ValueError as v:
            logging.exception(v)
            result = "Incorrect argument type(s) provided, please try again"

        writer.write(f"{result}\n".encode('UTF-8'))
        logging.info(f"Sent: {result!r}")
        await writer.drain()


@log_name
async def set_(key: Union[int, str], val: Union[int, str]) -> str:
    """Will set a key-value pair in our database. If the key is already present the value will be overwritten. If the
    key is not present, the key-value pair will be inserted."""
    async with lock:
        mem[key] = val
    return "OK"


@log_name
async def get_(key: Union[int, str]) -> Union[int, str, None]:
    """Will return the value paired up with the requested key. If the key does not exists, null is returned"""
    async with lock:
        result = mem.get(key)
    return result


# @log_name
async def mset_(*args: Union[int, str]) -> str:
    """Variations of get and set, where we work with a set of key-value pairs."""
    if len(args) % 2 != 0 or len(args) == 0:
        logging.info("Missing key/value pair")
        return "ERROR"
    for key, val in zip(args[0::2], args[1::2]):
        logging.debug(f"Received the following: {{{key}: {val}}}")
        for i in range(0, NUM_TRIES):
            while True:
                try:
                    await set_(key, val)
                except Exception as e:
                    logging.error(e)
                finally:
                    break
    return "OK"


@log_name
async def mget_(*args: Union[int, str]) -> List[Union[int, str]]:
    """Variations of get and set, where we work with a set of key-value pairs."""
    lst = list()
    for key in args:
        for i in range(0, NUM_TRIES):
            try:
                lst.append(await get_(key))
            except Exception as e:
                logging.error(e)
            finally:
                break
    logging.debug(f"received: {lst}")
    return lst


@log_name
async def exists_(key: Union[int, str]) -> bool:
    """Boolean operator that checks if the key is in our database."""
    async with lock:
        result = key in mem
    return result


@log_name
async def setnotexists_(key: Union[int, str], val: Union[int, str]) -> str:
    """Insert a key value pair only if the key is not already in our database."""
    if not await exists_(key):
        return await set_(key, val)
    return "Key already exists"


@log_name
async def setexists_(key: Union[int, str], val: Union[int, str]) -> str:
    """Update a key value pair only if the key is already there."""
    if await exists_(key):
        return await set_(key, val)
    return "Key does not exist"


@log_name
async def cset_(key: Union[int, str], old_val: Union[int, str], new_val: Union[int, str]) -> Union[int, str, None]:
    """Set the new value only if the old one is equal with a given value"""
    if await get_(key) == old_val:
        return await set_(key, new_val)
    return "Key does not exist or value does not match, please try again"


@log_name
async def inc_(key: Union[int, str], n: int = 1) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string."""
    val = await get_(key)
    try:
        val = int(val) + int(n)
        return await set_(key, val)
    except TypeError as e:
        logging.exception(e)
        return "Key does not exist, please try again"


@log_name
async def dec_(key: Union[int, str], n: int = 1) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string."""
    n = int(n)
    return await inc_(key, -n)


@log_name
async def incby_(key: Union[int, str], n: int) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string."""
    return await inc_(key, n)


@log_name
async def decby_(key: Union[int, str], n: int) -> Union[str, None]:
    """This operations are defined only on integer values. When the query is executed, the database will need to
    parse the string value into a integer, do the math operation and insert back the result as string."""
    n = int(n)
    return await inc_(key, -n)


def get_dispatch():
    return {
        'set': set_,
        'get': get_,
        'mset': mset_,
        'mget': mget_,
        'exists': exists_,
        'setexists': setexists_,
        'setnotexists': setnotexists_,
        'cset': cset_,
        'inc': inc_,
        'dec': dec_,
        'incby': incby_,
        'decby': decby_,
        'list': _list,
    }


@log_name
async def _list():
    """Returns a list of available functions"""
    return f"Available functions are: {list(get_dispatch().keys())}"


async def main():
    server = await asyncio.start_server(handle_echo, host=HOST, port=PORT)

    address = server.sockets[0].getsockname()
    logging.info(f'Serving on {address}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
