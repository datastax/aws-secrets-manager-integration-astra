# Copyright 2023 Datastax. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


# This is a wrapper which allows for running the lambda_function.py without modification. Simplifying the process
# of running and troublshooting the lambda function locally

from lambda_function import *
ClientRequestToken = '979cd45d-59e4-44c0-b1ff-dkas93dac2054'
SecretId = 'arn:aws:secretsmanager:us-east-1:389143091461:secret:/astra/prod/astra-XhB9oF'
Step = 'testSecret'


event = {'ClientRequestToken': ClientRequestToken,
         'SecretId': SecretId, 'Step': Step}

context = None

lambda_handler(event, context)
