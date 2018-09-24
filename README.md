## AWS Codecommit File Change Publisher

AWS CodeCommit file change notification example by using AWS Lambda, Amazon SNS and CloudWatch Event

## Create Lambda deployment package

Once you change the Lambda function code, you can use the following command to create deployment package:

```bash
zip -r codecommit-sns-publisher.zip lambda_function.py
```

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.
