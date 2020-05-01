Feature ideation:
Organization shares a single table across multiple users.
- Follow up: Events associated with identities, or not.

Source .env file

Create Dynamo table:
```
aws dynamodb create-table \
--table-name git_report_fswatch_events \
--attribute-definitions AttributeName=date,AttributeType=S AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=date,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
--billing-mode PAY_PER_REQUEST
```
