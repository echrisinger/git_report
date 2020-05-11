Real README coming soon.

----------------------------------------------------------------------
Feature ideation:
Organization shares a single table across multiple users.
- Follow up: Events associated with identities, or not.

Setup AWS Resources:

Create Dynamo tables:
```
aws dynamodb create-table \
--table-name git_report_git_events \
--attribute-definitions AttributeName=date,AttributeType=S AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=date,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
--billing-mode PAY_PER_REQUEST
```

```
aws dynamodb create-table \
--table-name git_report_report_requested_events \
--attribute-definitions AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=timestamp,KeyType=HASH \
--billing-mode PAY_PER_REQUEST
```

```
aws dynamodb create-table \
--table-name git_report_reports \
--attribute-definitions AttributeName=date,AttributeType=S AttributeName=uuid,AttributeType=S \
--key-schema AttributeName=date,KeyType=HASH AttributeName=uuid,KeyType=RANGE \
--billing-mode PAY_PER_REQUEST
```

SQS:
```
aws sqs create-queue --queue-name git_report_git_events
aws sqs create-queue --queue-name git_report_report_requested_events
aws sqs create-queue --queue-name git_report_report_events
```

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
