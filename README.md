# git-report

git-report - get reports about your git directory activity delivered to your command line. Learn about how you're spending your time.

## Examples

![insert gif here](my_gif)

## Usage

```bash
git clone git@github.com:echrisinger/git_report.git
cd git_report
pip3 install -e .

# setup AWS ENV, and place necessary environment vars into .env, source file
./setup_aws_env.sh

python bin/git_report.py --observe-path path_to_root_observed_directory &
python bin/handler.py
```

Directions for installing via PyPI & running non-locally coming soon.



## Development

Install the package with developer dependencies (linting & formatting).
```
python3 -m venv venv # construct a virtual environment
pip3 install -e .[dev] # install project & development dependencies
```

Feature ideation:
Organization shares a single table across multiple users.
- Follow up: Events associated with identities, or not.
- Setup resources via terraform

Setup:

Source .env file

Make a virtual environment (optional): `python3 -m venv venv`
Activate virtual environment `. ./venv/bin/activate`
Run `pip3 install -e .`
Throw the handler up on EC2: TODO instructions
Start the observer script on startup via systemd, launchd

Testing:
Edit some files
Generate a report

Programming Style: Java style, more OOP'ey & high-level than necessary,
but just expiremnting with some concepts I've been reading about in
[Clean Architecture](https://www.amazon.com/gp/your-account/order-history/ref=ppx_yo_dt_b_search?opt=ab&search=architecture). Once you get used to reading this style of code, it actually starts to make a lot of sense. It does require some initial overhead to read though, though.


Development:
Follow the same steps as above, but run `pip3 install -e .[dev]` to install
formatters, linting tools.
