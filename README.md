# Silverline Python Library

## Quick Start

1. Make sure you have python3 installed.
2. Install requirements:
```sh
pip install -r requirements.txt
```
3. Start module:
```
python3 run.py --runtime test --path wasm/tests/helloworld.wasm
```

## ```sl.client```: SilverLine testing client

Simple client for interfacing with the orchestrator (launching modules, stopping modules, sending messages, etc.).

Includes the following scripts:

- ```run.py```: launch module(s).
```sh
python3 run.py --config config.json --runtime test --path wasm/tests/helloworld.wasm --name test_helloworld
```

- ```stop_runtimes.py```: Issue exit request to specified runtimes.
```sh
python3 stop_runtimes.py --config config.json --runtime test_1 test_2
```

- ```echo.py```: Send echo instruction to orchestrator, and wait for response; useful for checking if the orchestrator MQTT message queue has cleared.
```sh
python3 echo.py --config config.json --timeout 10
```

- ```plot.py```: Generate plots from collected data.
```sh
python3 plot.py path/to/data --keys wall_time cpu_time --save out.png
```

- ```stats.py```: Generate statistics .npz file for collected data.
```sh
python3 stats.py path/to/data
```

For all scripts, run ```python3 {script}.py --help``` for full instructions.

## ```sl.data```: SilverLine profiling data

Data loader for profiling data. Usage:

```python
from libsilverline import data as sl

data = sl.Session(["path/to/data"])
trace = data.get("file/name").filter(runtime="test")
```

<!-- ## ```sl.runtime```: Virtual Runtime

The ``virtual runtime'' is a python module which allows a python program to register with the SilverLine framework as a runtime with pre-specified APIs (being able to perform specific functions instead of execute arbitrary WebAssembly modules).

This module is not yet functional. -->
