# Copyright 2023 Datastax. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from botocore.exceptions import ClientError
import logging
import sys
from lambda_function import *
from secretsmanager_lib import *
import json

logger = logging.getLogger(__name__)


"""
This program reads two arguments, name and lambdaARN, from the command
line. It sets up a client to access the AWS Secrets Manager service using
the Boto3 library. Then it calls the rotate_secret method on the service
client to rotate the secret specified by name.

The rotate_secret method rotates the secret with the specified name and
returns a response object. The RotationLambdaARN parameter specifies the
ARN of the AWS Lambda function to use for the rotation process, and the
RotationRules parameter specifies the duration and schedule of the rotation.
The response object is then converted to JSON format and printed to the console.
"""
# Syntax:
# python example_new_astra_secret.py <NAME> <LAMBDA ARN>

# Example
#python example_rotate_astra_secret.py /astra/prod/app1 arn:aws:lambda:us-east-1:388533891461:function:rotateAstraToken


# Read Arguments
name = sys.argv[1]
lambdaARN = sys.argv[2]



# Setup the client
service_client = boto3.client(
    'secretsmanager', endpoint_url=os.environ['SECRETS_MANAGER_ENDPOINT'])

# Rotate the secret
response = service_client.rotate_secret(
    RotationLambdaARN=lambdaARN,
    RotationRules={
        'Duration': '2h',
        'ScheduleExpression': 'cron(0 16 1,15 * ? *)',
    },
    SecretId=name,
)

response_json = json.dumps(response)

print(response_json)
