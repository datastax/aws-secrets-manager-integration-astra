# Using the AWS Secrets Manager Integration for DataStax Astra

Use the *AWS Secrets Manager Integration for DataStax Astra* to set up secure management of Astra API tokens in AWS. This integration provides a secure and automated way to manage and rotate secrets, ensuring that sensitive information is protected from unauthorized access. This topic guides you through the installation and configuration of the integration, and provides details about its features.

## Features

* Secure storage of Astra API tokens in [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
* Automation of the secret rotation process using a lambda function
* Ease of access to Astra tokens throughout the AWS ecosystem
* Integration of Astra tokens to the AWS IAM for access control

## Get the code

Clone this GitHub repo. HTTPS example:

```bash
git clone https://github.com/datastax/aws-secrets-manager-integration-astra.git
```

## Usage

You can use this GitHub repo in multiple ways.

1. Simply for the Lambda rotation function
2. As a Python library for AWS Secrets Manager &amp; Astra interaction
3. As a command-line tool set for creating, rotating, and deleting Astra API tokens in AWS Secret Manager
4. As a development environment for enhancing the lambda function

*NOTE:* You can use this AWS Secrets Manager Integration with DataStax Astra DB Serverless, Astra DB Classic, and Astra Streaming API tokens.

###  Rotation function

The [`lambda_function.py`](../lambda_function.py) file is all that is necessary to simply rotate an Astra API key stored in AWS secrets manager. 

See the [Create the root token](#create-the-root-token) and [Install the Lambda function](#install-the-lambda-function) sections below for instructions on how to implement this capability.

### Python library for AWS Secrets Manager &amp; Astra interaction

You can use the `lambda_function.py` and [`secretsmanager_lib.py`](../secretsmanager_lib.py) files as libraries to simplify Python development. For usage tips, refer to the `example_*` files in this [GitHub repo](https://github.com/datastax/aws-secrets-manager-integration-astra).

### Command line tool set

Use the `example_*` Python files as a CLI for interacting with Astra &amp; AWS Secrets Manager. Each file is documented with its respective usage in the Python code.

### Development environment

Use the [`launcher.py`](../launcher.py) Python program to test the lambda function outside of the AWS Lambda environment. This separation allows for more intensive debugging through local Python tools. In order to do that, the file must be updated with three fields to simulate a Lambda execution from AWS Secrets Manager:

| Field              |  Value                              |
| -------------------|  ---------------------------------- |
| ClientRequestToken | The UUID of the rotation job        |
| SecretId           | The ARN of the secret to rotate     |  
| Step               | The [step in the rotation process](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_turn-on-for-other.html) in the rotation process to test |

### Recommended debugging workflow

Logs are send to Amazon CloudWatch for the account for which the *Python boto3* environment is configured. The Lambda has a `debug = True` flag, which enables verbose details.

1. Install the function and execute. Ensure `debug = True` is set.

2. Check CloudWatch logs and look for an event message like the following:

```log
> [INFO]	2023-04-06T17:51:38.482Z	48224a7d-1234-4f34-1234-3b94b9b25dae 
event: {'ClientRequestToken': '4e62e336-1234-43d5-1234-0cc53fbeaaa4', 
'SecretId': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/b2287347-2222-1234-b68f-db0c5d104986/root-secret', 
'Step': 'createSecret'}
```
3. Configure the `launcher.py` using the `ClientRequestToken`, `SecretId`, &amp; `Step` from the log message.

4. Run `launcher.py` and utilize conventional Python debugging methods.

5. Adjust the `Step` field to test additional steps.


## Description of Python files in this repo

Here's a list of the Python files included in this [GitHub repo](https://github.com/datastax/aws-secrets-manager-integration-astra). Note that the example files are basic implementations and have minimal error handling and/or commenting.

1. [`example_delete_astra_secret.py`](../example_delete_astra_secret.py): A Python script that provides an example of how to delete a secret from AWS Secrets Manager along with the associated Astra API token utilizing a root token. The script uses the both the `secretsmanager_lib.py` and `lambda_function.py`files as a libraries.

2. [`example_get_astra_secret.py`](../example_get_astra_secret.py): A Python script that provides an example of how to retrieve a secret from AWS Secrets Manager utilizing a root token.

3. [`example_rotate_astra_secret.py`](../example_rotate_astra_secret.py): A Python script that provides an example of how to attache a rotation policy and rotate a secret in AWS Secrets Manager. The script uses the both the `secretsmanager_lib.py` and `lambda_function.py`files as a libraries.

4. [`example_new_astra_secret.py`](../example_new_astra_secret.py): A Python script that provides an example of how to create a new secret in Astra and store it in AWS Secrets Manager utilizing a root token. The script uses the both the `secretsmanager_lib.py` and `lambda_function.py`files as a libraries.

5. [`lambda_function.py`](../lambda_function.py): A Python script that defines an AWS Lambda function that can be used to handle rotation of Astra API tokens in AWS Secrets Manager utilizing a root token. It is also used as a library by the example files.

6. [`launcher.py`](../launcher.py): A Python wrapper to assist with running the `lambda_function.py` outside of the AWS Lambda environment for local debugging

7. [`secretsmanager_lib.py`](../secretsmanager_lib.py): A Python module that provides helper functions for interacting with AWS Secrets Manager and parsing the JSON-formatted secret values.


## Create the root token

1. [Create a new Astra token](https://docs.datastax.com/en/astra-serverless/docs/manage/org/manage-tokens.html) with sufficient privileges to create tokens with the roles and permissions for any future tokens that it will generate. A token cannot create new tokens with higher permissions than it has.

Make note of the information provided when the token is create. It will only be displayed once.

2. [Open AWS Secrets Manager](https://console.aws.amazon.com/secretsmanager/) and create a new secret.

3. Choose *Store a new secret*.

4. Choose *Other type of secret*.

5. Under *Key/value pairs*, select *Plain Text* and paste the following code:

```json
{
"astraKey": "TOKEN",
"clientID": "CLEINT_ID",
"clientSecret": "CLIENT_SECRET",
"rootarn": "ROOT_ARN",
"engine": "Astra"
} 
```
   - Substitute the `astraKey`, `clientID`, and `clientSecret`  values for the information received in step 1. 
   - Set the `rootarn` value to the Secret ARN of this secret. This value indicates (for future rotations) which secret to use for "root" access.
   - The “engine” field remain “Astra”.

6. Choose your encryption key.

7. Click *Next*

8. On the *Configure Secret* screen, give the secret a name that will help you easily identify the purpose of the secret.

9. Add any tags &amp; permissions necessary to make the secret accessible to your apps.

10. Configure replication if desired.

11. Click *Next*.

12. On the *Configure rotation* screen, you will not be able to enable rotation of the root secret until you've created the Lambda function. In the last box on the page, there is the option to select or create a function. If you create the function from here, a new tab will open allowing you to install a new function. Use the steps below to do so, then come back to the tab and complete the creation of the root secret.

## Install the Lambda function

To install the integration, follow these steps:

1. Create a [new Lambda function](https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html).
  - Choose the *Author from scratch* option.
  - Give the function a name.
  - Choose *Python 3.9* for the runtime environment.
  - Choose *x86_64* as an architecture.
  - Click *Create Function*.

2. Once the function is created you'll be taken to the function editor.
  - Copy the contents of the lambda_function.py from the repository into the code editor for the file of the same name, then deploy the function.

3. Navigate to the *Configuration* tab and select the *Environment variables* subtab
  - Add an environment variable for `SECRETS_MANAGER_ENDPOINT` and point it to the secrets manager endpoint in your AWS region. Example: 
    <div style="display: inline">https://secretsmanager.us-east-1.amazonaws.com/</div>
  - Save the environment configuration.

4. Navigate to the *Permissions* tab, and in the *Resource-based policy statements* section, add a new policy granting Secrets manager the ability to call the Lambda function.

5. You'll also need to create a new IAM policy to provide the necessary permissions for the Lambda function to access Secrets Manager. 
Here's an example policy, which allows any Lambda function to access any secret in Secrets Manager. 
You can find more details on the IAM requirements [here](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets-required-permissions-function.html#rotating-secrets-required-permissions-function-example).

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

Also, see this [YouTube video](https://youtu.be/7wkpf0u34Qs) for a helpful visual demonstration of how to set up a secret, create a Lambda function, a configure the policies, so that they can all interact.

## Support

AWS Secrets Manager Integration for DataStax Astra is provided as open-source software, and is community supported. If you are a Datastax customer with a Support contract, and you encounter any issues with the integration or have questions about its usage, you may contact our [Support team](https://support.datastax.com/s/). Any assistance through Datastax Support for this code is on a best-effort basis.
