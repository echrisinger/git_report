Dependencies:

Install fswatch.
```
brew install fswatch
```

Source .env file

Listen on a file:
`fswatch -0 -t --format-time '%F %T %z' README.md | xargs -0 -n 1 -I{} python git_report/display_logs.py '{}'`

Create Dynamo table:
```
aws dynamodb create-table \
--table-name git_report_fswatch_events \
--attribute-definitions AttributeName=date,AttributeType=S AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=date,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
--billing-mode PAY_PER_REQUEST
```
