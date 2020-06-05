# Two examples of a in-memory key-value store

Two version of an in-memory key-value store. Both were designed to demonstrate `asyncio` and `threading` in Python 3. The latter should be thread-safe and makes use of a global lock, and separate locks for every key/value pair. Both examples can be used as follows.

First, start the respective server:

* For `asyncio` use:
```bash
python asyncio-example/main.py
```

* For `threading` use:
```bash
python threading-example/main.py
```

Second, make calls to the server in one or multiple separate terminal windows (by, for example, using netcat):
```bash
nc 127.0.0.1 4040
```

You can send the following messages/operations to the server:

* `set <key> <val>`: sets key/value pair
* `get <key>`: gets value based on key
* `mset <key1> <val1> <key2> <val2>`: sets multiple key/value pairs
* `mget <key1> <key2>`: gets multiple values based on keys
* `exists <key>`: returns whether key exists or not
* `setexists <key> <val2>`: sets key/value pair in case key exists
* `setnotexists <key3> <val>`: sets key/value pair in case key does not exist
* `cset <key> <old_val> <new_val>`: sets key/value pair only if value matches 
* `inc <key>`: increments existing key by 1 (value has to be of type int)
* `dec <key>`: decrements existing key by 1 (value has to be of type int)
* `incby <key> <n>`: increments existing key by *n* (value has to be of type int)
* `decby <key> <n>`: decrements existing key by *n* (value has to be of type int)
* `list`: shows available operations

Operation names are case-insensitive.

Close the server anytime by using `CTRL + C`.

## To do
* Split `main.py` into modules that could be used by both examples
* Split the `handle` functions into smaller functions