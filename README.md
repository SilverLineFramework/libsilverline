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

## Usage

```libsilverline``` provides a simple client for interfacing with the orchestrator (launching modules, stopping modules, sending messages, etc.). It includes the following scripts:

- ```list.py```: list runtimes and modules for each runtime.
    ```sh
    python3 list.py --config config.json --style short
    ```

- ```run.py```: launch module(s).
    ```sh
    python3 run.py --config config.json --runtime test --path wasm/tests/helloworld.wasm --name test_helloworld
    ```

- ```stop_runtimes.py```: Issue exit request to specified runtimes.
    ```sh
    python3 stop_runtimes.py --config config.json --runtime test_1 test_2
    ```

- ```stop_modules.py```: Issue exit request to specified modules.
    ```sh
    python3 stop_modules.py --config config.json --modules module_1
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

## Example

We assume that we have set up mosquitto, the orchestrator, and the runtime according to the [local testing guide](https://github.com/SilverLineFramework/silverline/wiki/Local-Testing-Guide).

1. List runtimes:
    ```
    $ python3 libsilverline/list.py
    uuid:name  modules
    1788:test  --
    ```

2. Start module: we specify the runtime using the last 4 hex characters of the UUID.
    ```sh
    python3 run.py --path aot/polybench/small/2mm.aot --runtime 1788
    ```

    The runtime shows:
    ```
    [14:21:37] [Modules:INF] Creating Module: module
    [14:21:37] [Modules:NOT] Launching Module: benchmarks/aot/polybench/small/2mm.aot
    [14:21:37] [Modules:NOT] Env len: 0 | Dir len: 1
    [14:21:37] [Modules:INF] Initializing WAMR environment
    [14:21:37] [Modules:INF] Scheduler Class: CFS
    [14:21:37] [Modules:ERR] sh: 1: cannot create /sys/fs/cgroup/cpuset/cfs-partition/tasks: Directory nonexistent
    [00:21:31:441 - 7F1203FFF700]: warning: wasm_runtime_malloc with size zero

    [14:21:37] [Modules:INF] Running main: aot/polybench/small/2mm.aot | argc: 1
    [14:21:37] [MQTT:INF] Subscribe: benchmark/in/ef93868e-917e-4c60-97b2-c11e9be897b0
    ```

3. List modules:
    ```
    $ python3 list.py
    uuid:name  modules
    1788:test  97b0:module
    ```

4. Stop module:
    ```sh
    python3 stop_modules.py --module 97b0
    ```

    The runtime shows:
    ```
    [14:21:55] [Modules:INF] DELETE_MODULE Request: ef93868e-917e-4c60-97b2-c11e9be897b0
    [14:21:55] [Modules:INF] DELETE_MODULE serviced: ef93868e-917e-4c60-97b2-c11e9be897b0 (#: 1)
    [14:21:55] [MQTT:INF] Unsubscribe: benchmark/in/ef93868e-917e-4c60-97b2-c11e9be897b0
    ```

5. Stop runtime:
    ```sh
    python3 stop_runtimes.py --runtime 1788
    ```

    The runtime shows:
    ```
    [14:22:09] [Runtime:NOT] Exiting...
    ```
