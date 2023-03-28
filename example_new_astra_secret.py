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
This Python code retrieves values from command line arguments and AWS Secrets Manager,
creates a new Astra token using those values, and saves the new token as a new secret
in AWS Secrets Manager.

The code starts by importing required libraries and retrieving command line arguments
name, roles, and root_arn. It then sets up an AWS Secrets Manager client.

Next, it calls a function get_secret_dict to retrieve the current root Astra key from
the root secret. It then calls the function create_astra_token to create a new Astra
token using the root Astra key and the roles argument. If the token creation is
successful, the function creates a new secret in AWS Secrets Manager with the new token.

The new secret is created using the new astraKey, clientID, clientSecret, returned from
Astra.
"""
# Syntax:
# python example_new_astra_secret.py <NAME> <ASTRA ROLE UUID> <ROOT ARN>

# Example
# python example_new_astra_secret.py /astra/prod/app1 b08e981a-f84f-4562-8220-ebd3ce210aba arn:aws:secretsmanager:us-east-1:388318891461:secret:/astra/prod/rootkey-g1NqFK


name = sys.argv[1]
roles = [sys.argv[2]]
root_arn = sys.argv[3]


# Setup the client
service_client = boto3.client(
    'secretsmanager', endpoint_url=os.environ['SECRETS_MANAGER_ENDPOINT'])


# Get the root secret configuration
root_dict = get_secret_dict(
    service_client, root_arn, "AWSCURRENT", None, True)
# Get the root Astra key
root_key = root_dict['astraKey']

# Create a new Astra token using the root key, which mirrors the AWSCURRENT secret configuration
try:
    new_clientId, new_secret, new_token = create_astra_token(
        root_key, roles)
    print(
        f"Sucessfully created token with clientID {new_clientId}")
except Exception:
    raise Exception("Unable to create replacement token")


template = {'astraKey': new_token,
            'clientID': new_clientId,
            'clientSecret': new_secret,
            'engine': 'AstraDB',
            'rootarn': root_arn}

jsonTemplate = json.dumps(template)


secret = SecretsManagerSecret(boto3.client('secretsmanager'))
secret.create(name, jsonTemplate)
