# OpenSplit

## Local Server

To run a local instance of the service (**without persistent data!!**) you can use the following commands.

A docker container based on the currently checked out working tree will be build (and named `opensplit-backend:latest`). You can then start the server by invoking the second command. The `config.py.example` file will be used in the below command. Replace that part with your custom config file, if needed.

```
docker build -t opensplit-backend .
docker run --rm -v $(pwd)/config.py.example:/code/config.py:ro -p 5000:5000 -it opensplit-backend:latest
```


