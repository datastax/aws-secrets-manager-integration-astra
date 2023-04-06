# AWS Secrets Manager Integration for Astra

## Overview
The DataStax Astra and AWS Secrets Manager Integration is a solution that enables the secure management of DataStax Astra API tokens. The integration provides a secure and automated way to manage and rotate secrets, ensuring that sensitive information is protected from unauthorized access.
This documentation will guide you through the installation and configuration of the integration, as well as provide an overview of its features.

## Features
The DataStax Astra and AWS Secrets Manager Integration provides the following features:
* Secure storage of Astra API tokens in AWS Secrets Manager
* Automation of the secret rotation process using a lambda function
* Ease of access to Astra tokens throughout the AWS ecosystem
* Integration of Astra tokens to the AWS IAM for access control

## Usage
This repository can be used in multiple ways.
1. Simply for the lambda rotation function
2. As a python library for Secrets Manager & Astra interaction
3. As a commandline toolset for creating, rotating, and deleting Astra API tokens in AWS Secret Manager.
4. As a development environment for enhancing the lambda function.

###  Rotation function
The `lambda_function.py` file is all that is necessary to simply rotate an astra API key stored in AWS secrets manager. See the **Creation of the root token** and **Installation of the lambda function** sections in this document for instructions on how to implement this capability.

### Python library for Secrets Manager & Astra interaction
The `lambda_function.py` and `secretsmanager_lib.py` files can be used as libraries to simplify python development. See the `exmaple_*` files for examples of how they are used.

### Commandline toolset
The provided `exmaple_*` python files can be used to provide a command line interface for interacting with Astra & Secrets Manager. Each file is documented with its respective usage in the python program.

### Development environment
Using the `launcher.py` python program, you can test the lamba function outside of the AWS lambda environment. This can allow for more intensive debugging through local python tools. In order to do that, the file must be updated with 3 fields to simulate a lambda execution from Secrets Manager.

|Field   |  Value |
| ------------ | ------------ |
|   ClientRequestToken| The UUID of the rotation job  |
|  SecretId | The ARN of the secret to rotate  |
|Step| The [step in the rotation process](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_turn-on-for-other.html "step in the rotation process") to test|

#### Debugging
Logs are send to cloudwatch for the account for which the pythong boto3 environment is configured. The lambda has a `debug = True`flag which enables verbose details.
##### Recommended flow for debugging
1. Install the function and execute. Ensrure `debug = True` is set
2. Check cloudwatch logs and look for an event message like the following
> [INFO]	2023-04-06T17:51:38.482Z	48224a7d-1234-4f34-1234-3b94b9b25dae	event: {'ClientRequestToken': '4e62e336-1234-43d5-1234-0cc53fbeaaa4', 'SecretId': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/b2287347-2222-1234-b68f-db0c5d104986/root-secret', 'Step': 'createSecret'}
3. Configuring the `launcher.py` using the ClientRequestToken, SecretId, & Step from the message
4. Run `launcher.py` & utilize conventional Python debugging methods.
5. Adjust the "step" field to test additional steps



## Description of Python Files in this Repository

Below is a list of the python files included in this repository. Note that the example files are basic examples and have minial error handling and/or commenting.

1. `example_delete_astra_secret.py`: A Python script that provides an example of how to delete a secret from AWS Secrets Manager along with the associated Astra API token utilizing a root token. The script uses the both the `secretsmanager_lib.py` and `lambda_function.py`files as a libraries.

2. `example_get_astra_secret.py`: A Python script that provides an example of how to retrienve a secret from AWS Secrets Manager utilizing a root token.

3. `example_rotate_astra_secret.py`: A Python script that provides an example of how to attache a rotation policy and rotate a secret in AWS Secrets Manager. The script uses the both the `secretsmanager_lib.py` and `lambda_function.py`files as a libraries.

4. `example_new_astra_secret.py`: A Python script that provides an example of how to create a new secret in Astra and store it in AWS Secrets Manager utilizing a root token. The script uses the both the `secretsmanager_lib.py` and `lambda_function.py`files as a libraries.

5. `lambda_function.py`: A Python script that defines an AWS Lambda function that can be used to handle rotation of Astra API tokens in AWS Secrets Manager utilizing a root token. It is also used as a library by the example files.

6. `launcher.py`: A wrapper to assist with running the `lambda_function.py` outside of the AWS Lambda environment for local debugging

7. `secretsmanager_lib.py`: A Python module that provides helper functions for interacting with AWS Secrets Manager and parsing the JSON-formatted secret values.


## Obtaining the code
To donwload a copy this repo, clone the GitHub repository using: `git clone https://github.com/datastax/aws-secrets-manager-integration-astra.git`


## Creation of the root token
1. [Create a new Astra token](https://docs.datastax.com/en/astra-serverless/docs/manage/org/manage-tokens.html) with sufficient privileges to create tokens with the roles and permissions for any future tokens that it will generate. A token cannot create new tokens with higher permissions than it has.

Make note of the information provided when the token is create. It will only be displayed once.
2. [Open Secrets Manager](https://console.aws.amazon.com/secretsmanager/) and create a new secret.
3. Choose “Store a new secret”.
4. Chose “Other type of secret”
5. Under “Key/value pairs” select “Plain Text” and paste the following code
```json
{
"astraKey": "TOKEN",
"clientID": "CLEINT_ID",
"clientSecret": "CLIENT_SECRET",
"rootarn": ROOT_ARN"
"engine": "AstraDB"
} 
```
   1. Substitute the astraKey, clientID, & clientSecret  values for the information received in step 1. 
   2. rootarn must be set to the Secret ARN of this secret. This is indicate for future rotations on which secret to use for "root" access.
   3. The “engine” field remain “AstraDB”.
7. Chose your encryption key
8. Click "Next"
9. On the "Configure Secret" screen give the secret a name that will help you easily identify the purpose of the secret.
10. Add any tags & permissions necessary to make the secret accessible to your apps
11. Configure replication if desired.
12. Click "Next"
13. On the "Configure rotation" screen, you will not be able to enable rotation of the root secret until you've created the Lambda function. In the last box on the page there is the option to select or create a function. If you create the function from here, a new tab will open allowing you to install a new funcion. Use the steps below to do so, then come back to the tab and complete the creation of the root secret.



## Installation of the lambda function
To install the integration, follow these steps:
1. Create a [new lambda function](https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html)
  1. Chose the “Author from scratch” option
  2. Give the function a name
  3. Choose “Python 3.9” for the runtime environment
  4. Chose “x86_64” as an architecture
  5. Click “Create Function”
2. Once the function is created you’ll be taken to the function editor.
  1. Copy the contents of the lambda_function.py from the repository into the code editor for the file of the same name, then deploy the function.
3. Navigate to the “Configuration” tab and select the “Environment variables” subtab
  1. Add an environment variable for “SECRETS_MANAGER_ENDPOINT” and point it to the secrets manager endpoint in your region (e.g. https://secretsmanager.us-east-1.amazonaws.com/)
 2. Save the environment configuration.
4. Navigate to the "permissions" tab, and in the "Resource-based policy statements" section, add a new policy granting Secrets manager the ability to call the lambda fucntion.
5. A new IAM policy will also need to be created to provide the necessary permissions for the lambda function to access Secrets Manager.
 Below is an example policy which allows any lambda function to access any secret in Secrets Manager. More details on the IAM requirements can be found [here](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets-required-permissions-function.html#rotating-secrets-required-permissions-function-example "here").
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:DescribeSecret",
                "secretsmanager:GetSecretValue",
                "secretsmanager:PutSecretValue",
                "secretsmanager:UpdateSecretVersionStage"
            ],
            "Resource": "arn:aws:secretsmanager:*:123456789012:secret:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetRandomPassword"
            ],
            "Resource": "*"
        },
        {
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DetachNetworkInterface"
            ],
            "Resource": "*",
            "Effect": "Allow"
        }
    ]
}
```

A great visual demonstration on how to set up a secret, create a lambda function, a configure the policies so that they can interract can be found in [this youtube video](https://youtu.be/7wkpf0u34Qs "this youtube video").


## Support
This integration is provided as an open source integration (as is) and is community supported. If you are a Datastax customer with a support contract and you encounter any issues with the integration or have questions about its usage, you may contact our support team. Any assistance through Datastax support for this code is on a best-effort basis.

## Conclusion
The DataStax Astra and AWS Secrets Manager Integration provides a secure and automated way to manage and rotate secrets for your DataStax Astra resources. By leveraging the security and scalability of AWS Secrets Manager and the authentication mechanisms of DataStax Astra, this integration helps you protect your sensitive data and streamline your workflows. Try it today and discover how it can enhance your cloud security posture and simplify your secret management processes.