# Copyright 2023 Datastax. All Rights Reserved.
# Derrived from works with the following Copyright
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Purpose

Shows how to use the AWS SDK for Python (Boto3) with AWS Secrets Manager to
create and manage secrets, and how to use a secret that contains database credentials
to access an Amazon Aurora database cluster.
"""

import argparse
import base64
import json
import logging
from pprint import pprint
import time
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# snippet-start:[python.example_code.secrets-manager.SecretsManagerSecret]
class SecretsManagerSecret:
    """Encapsulates Secrets Manager functions."""
    def __init__(self, secretsmanager_client):
        """
        :param secretsmanager_client: A Boto3 Secrets Manager client.
        """
        self.secretsmanager_client = secretsmanager_client
        self.name = None
# snippet-end:[python.example_code.secrets-manager.SecretsManagerSecret]

    def _clear(self):
        self.name = None

# snippet-start:[python.example_code.secrets-manager.CreateSecret]
    def create(self, name, secret_value):
        """
        Creates a new secret. The secret value can be a string or bytes.

        :param name: The name of the secret to create.
        :param secret_value: The value of the secret.
        :return: Metadata about the newly created secret.
        """
        self._clear()
        try:
            kwargs = {'Name': name}
            if isinstance(secret_value, str):
                kwargs['SecretString'] = secret_value
            elif isinstance(secret_value, bytes):
                kwargs['SecretBinary'] = secret_value
            response = self.secretsmanager_client.create_secret(**kwargs)
            self.name = name
            logger.info("Created secret %s.", name)
        except ClientError:
            logger.exception("Couldn't get secret %s.", name)
            raise
        else:
            return response
# snippet-end:[python.example_code.secrets-manager.CreateSecret]

# snippet-start:[python.example_code.secrets-manager.DescribeSecret]
    def describe(self, name=None):
        """
        Gets metadata about a secret.

        :param name: The name of the secret to load. If `name` is None, metadata about
                     the current secret is retrieved.
        :return: Metadata about the secret.
        """
        if self.name is None and name is None:
            raise ValueError
        if name is None:
            name = self.name
        self._clear()
        try:
            response = self.secretsmanager_client.describe_secret(SecretId=name)
            self.name = name
            logger.info("Got secret metadata for %s.", name)
        except ClientError:
            logger.exception("Couldn't get secret metadata for %s.", name)
            raise
        else:
            return response
# snippet-end:[python.example_code.secrets-manager.DescribeSecret]

# snippet-start:[python.example_code.secrets-manager.GetSecretValue]
    def get_value(self, stage=None):
        """
        Gets the value of a secret.

        :param stage: The stage of the secret to retrieve. If this is None, the
                      current stage is retrieved.
        :return: The value of the secret. When the secret is a string, the value is
                 contained in the `SecretString` field. When the secret is bytes,
                 it is contained in the `SecretBinary` field.
        """
        if self.name is None:
            raise ValueError

        try:
            kwargs = {'SecretId': self.name}
            if stage is not None:
                kwargs['VersionStage'] = stage
            response = self.secretsmanager_client.get_secret_value(**kwargs)
            logger.info("Got value for secret %s.", self.name)
        except ClientError:
            logger.exception("Couldn't get value for secret %s.", self.name)
            raise
        else:
            return response
# snippet-end:[python.example_code.secrets-manager.GetSecretValue]

# snippet-start:[python.example_code.secrets-manager.GetRandomPassword]
    def get_random_password(self, pw_length):
        """
        Gets a randomly generated password.

        :param pw_length: The length of the password.
        :return: The generated password.
        """
        try:
            response = self.secretsmanager_client.get_random_password(
                PasswordLength=pw_length)
            password = response['RandomPassword']
            logger.info("Got random password.")
        except ClientError:
            logger.exception("Couldn't get random password.")
            raise
        else:
            return password
# snippet-end:[python.example_code.secrets-manager.GetRandomPassword]

# snippet-start:[python.example_code.secrets-manager.PutSecretValue]
    def put_value(self, secret_value, stages=None):
        """
        Puts a value into an existing secret. When no stages are specified, the
        value is set as the current ('AWSCURRENT') stage and the previous value is
        moved to the 'AWSPREVIOUS' stage. When a stage is specified that already
        exists, the stage is associated with the new value and removed from the old
        value.

        :param secret_value: The value to add to the secret.
        :param stages: The stages to associate with the secret.
        :return: Metadata about the secret.
        """
        if self.name is None:
            raise ValueError

        try:
            kwargs = {'SecretId': self.name}
            if isinstance(secret_value, str):
                kwargs['SecretString'] = secret_value
            elif isinstance(secret_value, bytes):
                kwargs['SecretBinary'] = secret_value
            if stages is not None:
                kwargs['VersionStages'] = stages
            response = self.secretsmanager_client.put_secret_value(**kwargs)
            logger.info("Value put in secret %s.", self.name)
        except ClientError:
            logger.exception("Couldn't put value in secret %s.", self.name)
            raise
        else:
            return response
# snippet-end:[python.example_code.secrets-manager.PutSecretValue]

# snippet-start:[python.example_code.secrets-manager.UpdateSecretVersionStage]
    def update_version_stage(self, stage, remove_from, move_to):
        """
        Updates the stage associated with a version of the secret.

        :param stage: The stage to update.
        :param remove_from: The ID of the version to remove the stage from.
        :param move_to: The ID of the version to add the stage to.
        :return: Metadata about the secret.
        """
        if self.name is None:
            raise ValueError

        try:
            response = self.secretsmanager_client.update_secret_version_stage(
                SecretId=self.name, VersionStage=stage, RemoveFromVersionId=remove_from,
                MoveToVersionId=move_to)
            logger.info("Updated version stage %s for secret %s.", stage, self.name)
        except ClientError:
            logger.exception(
                "Couldn't update version stage %s for secret %s.", stage, self.name)
            raise
        else:
            return response
# snippet-end:[python.example_code.secrets-manager.UpdateSecretVersionStage]

# snippet-start:[python.example_code.secrets-manager.DeleteSecret]
    def delete(self, without_recovery):
        """
        Deletes the secret.

        :param without_recovery: Permanently deletes the secret immediately when True;
                                 otherwise, the deleted secret can be restored within
                                 the recovery window. The default recovery window is
                                 30 days.
        """
        if self.name is None:
            raise ValueError

        try:
            self.secretsmanager_client.delete_secret(
                SecretId=self.name, ForceDeleteWithoutRecovery=without_recovery)
            logger.info("Deleted secret %s.", self.name)
            self._clear()
        except ClientError:
            logger.exception("Deleted secret %s.", self.name)
            raise
# snippet-end:[python.example_code.secrets-manager.DeleteSecret]

# snippet-start:[python.example_code.secrets-manager.ListSecrets]
    def list(self, max_results):
        """
        Lists secrets for the current account.

        :param max_results: The maximum number of results to return.
        :return: Yields secrets one at a time.
        """
        try:
            paginator = self.secretsmanager_client.get_paginator('list_secrets')
            for page in paginator.paginate(
                    PaginationConfig={'MaxItems': max_results}):
                for secret in page['SecretList']:
                    yield secret
        except ClientError:
            logger.exception("Couldn't list secrets.")
            raise
# snippet-end:[python.example_code.secrets-manager.ListSecrets]