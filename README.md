# git-report

git-report - get reports about your daily project activity delivered to your command line.

## Examples

![insert gif here](my_gif)

## Usage

```bash
git clone git@github.com:echrisinger/git_report.git
cd git_report

# install in a virtual environment
python3 -m venv venv
. ./venv/bin/activate
pip3 install -e .

# setup AWS ENV, and place necessary environment vars into .env, source file
./setup_aws_env.sh

python bin/git_report.py --observe-path root/observed/directory &
python bin/handler.py

# ...edit some files...

python bin/git_report.py --generate-report
```

Directions for installing via PyPI & running non-locally coming soon.

## How does it work?

[Watchdog](https://github.com/gorakhargosh/watchdog) observes your file system at & below the root directory or file, and sends all filesystem events to an SQS queue individually. This queue is then polled server-side. Events are stored in Dynamo, partitioned by date. Server-side, this allows a single machine to gracefully handle all edited files without accidentally grinding to a halt when a large edit on the file system occurs.

Report requests & generated reports are communicated to & from the server, also via SQS.

Server-side, [GEvent](https://github.com/gevent/gevent), a Python coroutine-based concurrency library polls for new report requests, and new file system events. This is done by running a beat thread per SQS queue on a second to sub-second interval. When a heartbeat occurs, we poll the SQS queue, and handle any events that occurred.

## Development

Contributions are welcome.

[Feature ideation doc](https://docs.google.com/document/d/1MgF9ue0OLyWcX8eFxcVfgZqpj2vQ8yj2gHU4CI-rPjc/edit?usp=sharing)

[Technical backlog doc](https://docs.google.com/document/d/1bQMwvc8blh39XJ30Up_9MDYFCPIzCJtQgj1QB06cCxE/edit?usp=sharing)

#### Code Style & Tool Usage


A lot of style is influenced by [Clean Architecture](https://www.amazon.com/gp/your-account/order-history/ref=ppx_yo_dt_b_search?opt=ab&search=architecture), which I'm in the midst of reading. Personally I find introducing a ton of interfaces & patterns to be a little overkill for a personal project, but it was a fun mental exercise. Reflecting on some projects that I've worked on in industry, the emergent patterns begin to make sense. The end result, in this repository, is that many stylistic decisions are intentionally unpythonic. There are a lot of single method classes, some unnecessary interfaces, etc.



#### Instructions

Install the package with developer dependencies (linting & formatting).
```
python3 -m venv venv # construct a virtual environment
pip3 install -e .[dev] # install project & development dependencies
```

## Inspiration

Popular GEvent libraries such as [GUnicorn]() & Golang's [awesome concurrency](https://tour.golang.org/concurrency/5).


## License

Licensed under the MIT License.

Made by Evan Chrisinger.
