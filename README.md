# git_report

git_report - get low-overhead reports about your daily git repo activity delivered to your command line.

## Examples

```bash
(venv) evan: (update-readme) ~/Projects/git_report$ python bin/git-report.py --request-report
  ____ _ _     ____                       _
 / ___(_) |_  |  _ \ ___ _ __   ___  _ __| |_
| |  _| | __| | |_) / _ \ '_ \ / _ \| '__| __|
| |_| | | |_  |  _ <  __/ |_) | (_) | |  | |_
 \____|_|\__| |_| \_\___| .__/ \___/|_|   \__|
                        |_|



Counts:
[{'count': 1,
  'duration': '0:39:18.809865',
  'file_name': '/Users/evanchrisinger/Projects/git_report/README.md'},
 {'count': 8,
  'duration': '6:29:01.276450',
  'file_name': '/Users/evanchrisinger/Projects/git_report/bin'},
 {'count': 7,
  'duration': '5:34:43.252430',
  'file_name': '/Users/evanchrisinger/Projects/git_report/bin/git-report.py'},
 {'count': 3,
  'duration': '1:21:54.321998',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report'},
 {'count': 1,
  'duration': '0:41:00.702240',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/__pycache__'},
 {'count': 2,
  'duration': '1:22:01.343532',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/__pycache__/data_access.cpython-37.pyc'},
 {'count': 2,
  'duration': '0:40:57.595997',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/data_access.py'},
 {'count': 2,
  'duration': '1:21:54.129092',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/data_access.py.6adde4e63aab4ab04ae819b9e1d7f664.py'}]

Timeline:
[{'duration': '0:00:00',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/data_access.py'},
 {'duration': '0:00:00.079355',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report'},
 {'duration': '0:39:18.809865',
  'file_name': '/Users/evanchrisinger/Projects/git_report/README.md'},
 {'duration': '0:40:56.551063',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/data_access.py.6adde4e63aab4ab04ae819b9e1d7f664.py'},
 {'duration': '0:40:56.628911',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report'},
 {'duration': '0:40:57.578029',
  'file_name': '/Users/evanchrisinger/Projects/git_report/git_report/data_access.py.6adde4e63aab4ab04ae819b9e1d7f664.py'},
 {'duration': '0:40:57.595997',
 ...
```

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

python bin/git-report.py --observe-path root/observed/directory &
python bin/handler.py

# ...edit some files...

python bin/git-report.py --generate-report
```

Directions for installing via PyPI & running non-locally coming soon.

## How does it work?

[Watchdog](https://github.com/gorakhargosh/watchdog) observes your file system at & below the root directory or file, and sends all filesystem events to an SQS queue individually. This queue is then polled server-side. Events are stored in Dynamo, partitioned by date. Server-side, this allows a single machine to gracefully handle all edited files without accidentally grinding to a halt when a large edit on the file system occurs.

Report requests & generated reports are communicated to & from the server, also via SQS.

Server-side, we use [GEvent](https://github.com/gevent/gevent) to schedule polling for new report requests, and new file system events. This is done by running a beat thread per SQS queue on a second to sub-second interval. When a beat occurs, we poll the SQS queue, and handle any events that occurred.

Client-side, reports are displayed using pyfiglet for ASCII art & graphics.

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

Popular GEvent libraries such as [GUnicorn](https://gunicorn.org/) & Golang's [awesome concurrency](https://tour.golang.org/concurrency/5).


## License

Licensed under the MIT License.

Made by Evan Chrisinger.
