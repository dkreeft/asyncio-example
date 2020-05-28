# asyncio-example

Small example small in-memory key-value store to demonstrate asyncio. It can be used as follows.

Start the server:
```bash
python main.py
```

Make calls to the server (by, for example, using netcat):
```bash
nc 127.0.0.1 4040
```

After executing the command, you can type messages that upon sending will be returned by the server. (see [Todo](#todo) below for future extension)

Close the server anytime by using `CTRL + C`.

## <a name="todo">Todo</a>
* Many functions are included to create, read, and update (delete could still be implemented for CRUD) the key-value store. Allow the clients to execute these functions by sending requests.