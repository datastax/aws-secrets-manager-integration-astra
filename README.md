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
"roleID": "ROLE_UUID",
"engine": "AstraDB"
} 
```
6. Substitute the values for the information received in step 1. Note that “engine” must remain “AstraDB”.
7. Whats next??!?!?!?

## Obtaining the code
To install copy this rep, follow these steps:
1. Clone the GitHub repository using: `git clone https://github.com/datastax/aws-secrets-manager-integration-astra.git`

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
 2. Test steps necessary?!?!?!
3. Navigate to the “Configuration” tab and select the “Environment variables” subtab
 1. Add an environment variable for “SECRETS_MANAGER_ENDPOINT” and point it to the secrets manager endpoint in your region (e.g. https://secretsmanager.us-east-1.amazonaws.com/)
 2. Save the environment configuration.
4. Navigate to the “Permissions” subtab



## Usage
Once the integration is installed and configured, you can use it to manage and rotate your secrets in AWS Secrets Manager. Blah blah blah.

## Support
This integration is provided as an open source integration and is primarily community supported. . If you are a Datastax customer with a support contract and you encounter any issues with the integration or have questions about its usage, please contact our support team at support@datastax.com.

## Conclusion
The DataStax Astra and AWS Secrets Manager Integration provides a secure and automated way to manage and rotate secrets for your DataStax Astra resources. By leveraging the security and scalability of AWS Secrets Manager and the authentication mechanisms of DataStax Astra, this integration helps you protect your sensitive data and streamline your workflows. Try it today and discover how it can enhance your cloud security posture and simplify your secret management processes.