touch .env
# Dynamo
aws dynamodb create-table \
--table-name git_report_git_events \
--attribute-definitions AttributeName=date,AttributeType=S AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=date,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
--billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
--table-name git_report_report_requested_events \
--attribute-definitions AttributeName=timestamp,AttributeType=S \
--key-schema AttributeName=timestamp,KeyType=HASH \
--billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
--table-name git_report_reports \
--attribute-definitions AttributeName=date,AttributeType=S AttributeName=uuid,AttributeType=S \
--key-schema AttributeName=date,KeyType=HASH AttributeName=uuid,KeyType=RANGE \
--billing-mode PAY_PER_REQUEST

# SQS
aws sqs create-queue --queue-name git_report_git_events
aws sqs create-queue --queue-name git_report_report_requested_events
aws sqs create-queue --queue-name git_report_report_events
