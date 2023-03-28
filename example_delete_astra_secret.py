# Copyright 2023 Datastax. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from botocore.exceptions import ClientError
import logging
import sys
from lambda_function import *
from secretsmanager_lib import *
import json
import botocore.session
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

logger = logging.getLogger(__name__)


"""
This Python code is used to delete a secret from AWS Secrets Manager and also delete an Astra token.
The script accepts a single argument name which is the name of the secret to delete.

The script sets up a Secrets Manager client using the boto3 library and sets a cache configuration.
Then it uses the SecretCache class from the aws_secretsmanager_caching library to get the secret value
associated with the provided name. The returned value is a JSON string that is loaded into a dictionary
using the json module.

The script then extracts the clientID and rootarn from the secret dictionary and uses them to get the root
secret configuration. From the root secret configuration, the script extracts the astraKey which is the
root Astra key. It then uses the delete_astra_token() function to delete the Astra token associated with
the provided clientID.

Finally, the script deletes the secret from Secrets Manager using the delete_secret() function and prints
the response as a JSON string.
"""
# Syntax:
# python example_delete_astra_secret.py <NAME>

# Example
#python example_delete_astra_secret.py /astra/prod/app1



name = sys.argv[1]


# Setup the client
service_client = boto3.client(
    'secretsmanager', endpoint_url=os.environ['SECRETS_MANAGER_ENDPOINT'])
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=service_client)


# Grab the secret

secret = cache.get_secret_string(name)
secret_dict = secret_dict = json.loads(secret)

# Get its clientID
clientID = secret_dict['clientID']
root_arn = secret_dict['rootarn']


# Get the root secret configuration
root_dict = get_secret_dict(
    service_client, root_arn, "AWSCURRENT", None, True)
# Get the root Astra key
root_key = root_dict['astraKey']

# Delete the Astra key
delete_astra_token(root_key, clientID)


# Delete the secrets manager secret
response = service_client.delete_secret(
    SecretId=name,
    # RecoveryWindowInDays=7,
    ForceDeleteWithoutRecovery=True
)


response_json = json.dumps(response, indent=4, sort_keys=True, default=str)

print(response_json)
