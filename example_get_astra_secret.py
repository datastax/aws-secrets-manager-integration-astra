# Copyright 2023 Datastax. All Rights Reserved.
# Derrived from works with the following Copyright
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import sys
from botocore.exceptions import ClientError

"""
This program takes in the "name" of an AWS Secrets Manager secret and
retrieves the secret from AWS Secrets Manager. It uses the boto3 library
to create a client for AWS Secrets Manager and then calls the
get_secret_value method of the client to retrieve the secret. If the
retrieval is successful, it decrypts the secret using the associated KMS key
and prints the secret. 
"""
# Syntax:
# python example_get_astra_secret.py <NAME>

# Example
# python example_get_astra_secret.py /astra/prod/app1


name = sys.argv[1]

def get_secret(name):

    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    print(secret)


get_secret(name)
