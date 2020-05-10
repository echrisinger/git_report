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
--table-name git_report_report_events \
--attribute-definitions AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=timestamp,KeyType=HASH \
--billing-mode PAY_PER_REQUEST
```

SQS:
```
aws sqs create-queue --queue-name git_report_report_events
aws sqs create-queue --queue-name git_report_git_events
aws sqs create-queue --queue-name git_report_reports
```

Source .env file

Make a virtual environment (optional): `python3 -m venv venv`
Activate virtual environment `. ./venv/bin/activate`
Run `pip install -e .[dev]`
Throw the handler up on EC2: TODO instructions
Start the observer script on startup via systemd, launchd

Testing:
Edit some files
Generate a report
