# Copyright 2023 Datastax. All Rights Reserved.
# Derrived from works with the following Copyright
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import json
import logging
import os
import http.client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

debug = True



astraAPIhost = "api.astra.datastax.com"


def lambda_handler(event, context):
    """Secrets Manager Datastax API Tokens

    This handler uses the root-user rotation scheme to rotate an Astra API Token. During the first rotation, this
    scheme connects the the API with the root key, and does stuff... Once the secret is in this state, every subsequent rotation
    simply creates a new secret with the AWSPREVIOUS user credentials, changes that user's password, and then marks the
    latest secret as AWSCURRENT.

    The Secret SecretString is expected to be a JSON string with the following format:
    {
        "astraKey": <required: the Astra API key>
        "clientID": <required: the Astra API client ID>
        "clientSecret": <required: the Astra API Client Secret>
        "engine": <required: must be set to 'Astra'>
        "rootarn": <required when not requesting a root ARN: must be set to the ARN which contains the root key>
    }

    Args:
        event (dict): Lambda dictionary of event parameters. These keys must include the following:
            - SecretId: The secret ARN or identifier
            - ClientRequestToken: The ClientRequestToken of the secret version
            - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

        context (LambdaContext): The Lambda runtime information

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not properly configured for rotation

        KeyError: If the secret json does not contain the expected keys

    """

    if debug:
        logger.info(f"event: {event}")
        logger.info(f"context: {context}")

    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # Setup the client
    service_client = boto3.client(
        'secretsmanager', endpoint_url=os.environ['SECRETS_MANAGER_ENDPOINT'])

    # Make sure the version is staged correctly
    metadata = service_client.describe_secret(SecretId=arn)
    if "RotationEnabled" in metadata and not metadata['RotationEnabled']:
        logger.error("Secret %s is not enabled for rotation" % arn)
        raise ValueError("Secret %s is not enabled for rotation" % arn)
    versions = metadata['VersionIdsToStages']
    if token not in versions:
        logger.error(
            "Secret version %s has no stage for rotation of secret %s." % (token, arn))
        raise ValueError(
            "Secret version %s has no stage for rotation of secret %s." % (token, arn))
    if "AWSCURRENT" in versions[token]:
        logger.info(
            "Secret version %s already set as AWSCURRENT for secret %s." % (token, arn))
        return
    elif "AWSPENDING" not in versions[token]:
        logger.error(
            "Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))
        raise ValueError(
            "Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))


    # Call the appropriate step
    if step == "createSecret":
        create_secret(service_client, arn, token)

    elif step == "setSecret":
        set_secret(service_client, arn, token)

    elif step == "testSecret":
        test_secret(service_client, arn, token)

    elif step == "finishSecret":
        finish_secret(service_client, arn, token)

    else:
        logger.error(
            "lambda_handler: Invalid step parameter %s for secret %s" % (step, arn))
        raise ValueError(
            "Invalid step parameter %s for secret %s" % (step, arn))


def create_secret(service_client, arn, token):
    """Generate a new Astra token

    This method first checks for the existence of a secret for the passed in token. If one does not exist, it will generate a
    new Astra token and save it using a duplcated configuration from the passed in token.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ValueError: If the current secret is not valid JSON

        KeyError: If the secret json does not contain the expected keys

    """
    # Get the current secret configuration
    current_dict = get_secret_dict(service_client, arn, "AWSCURRENT")
    # Find the defined root arn
    root_arn = current_dict['rootarn']
    # Get the root secret configuration
    root_dict = get_secret_dict(
        service_client, root_arn, "AWSCURRENT", None, True)
    # Get the root Astra key
    root_key = root_dict['astraKey']
    # Get the client ID for the current secret
    current_clientID = current_dict['clientID']

    # Now try to get the secret version, if that fails, put a new secret
    try:
        get_secret_dict(service_client, arn, "AWSPENDING", token)
        logger.info(f"createSecret: Successfully retrieved secret for {arn}.")
    except service_client.exceptions.ResourceNotFoundException:
        # Get the roles for the AWSCURRENT configuration directly from Astra
        roles = get_token_roles(root_key, current_clientID)
        # Create a new Astra token using the root key, which mirrors the AWSCURRENT secret configuration
        try:
            new_clientId, new_secret, new_token = create_astra_token(
                root_key, roles)
            logger.info(
                f"Sucessfully created token with clientID {new_clientId} to replace {current_clientID}")
        except Exception:
            raise Exception(f"Unable to create replacement token for {current_clientID}")
        
        # Create a new configuration based on the current one, then populate the new configuraiton items
        new_dict = current_dict
        new_dict['clientID'] = new_clientId
        new_dict['clientSecret'] = new_secret
        new_dict['astraKey'] = new_token
        # Put the secret
        service_client.put_secret_value(SecretId=arn, ClientRequestToken=token, SecretString=json.dumps(current_dict), VersionStages=['AWSPENDING'])
        logger.info(f"createSecret: Successfully put secret for ARN {arn} and version {token}.")


def set_secret(service_client, arn, token):
    # This stage is unused
    pass

    


def test_secret(service_client, arn, token):
    """Test the pending Astra token

    This method uses the newly created token that was storred in the AWSPENDING version from the create_secret
    step to make a test API call to Astra.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON or pending credentials could not be used to login to the database

        KeyError: If the secret json does not contain the expected keys

    """

    # Get the current secret configuration
    pending_dict = get_secret_dict(service_client, arn, "AWSPENDING")
    # Find the defined root arn
    pending_token = pending_dict['astraKey']

    # Now try to get the secret version, if that fails, put a new secret
    try:
        status, reason, headers, data = make_API_request(pending_token, "GET", "/v2/currentOrg", body=None)

        if status != 200:
            raise Exception(f"Token test failed. Failure detail: {data}")
        else:
            logger.info(f"Successfully tested new secret for {arn}.")

    except Exception:
        raise Exception("Token test failed with no details.")



def finish_secret(service_client, arn, token):
    """Finish the rotation by marking the pending secret as current

    This method moves the secret from the AWSPENDING stage to the AWSCURRENT stage.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

    """

    ###### Delete the old Astra Token 
    # First getting current secret configuration
    current_dict = get_secret_dict(service_client, arn, "AWSCURRENT")
    # Grab the root ARN
    root_arn = current_dict['rootarn']
    # Get the root secret configuration
    root_dict = get_secret_dict(
        service_client, root_arn, "AWSCURRENT", None, True)
    # Get the root Astra key
    root_key = root_dict['astraKey']
    # Get the clientID to delete
    clientID = current_dict['clientID']
    # And finally delete it

    status = delete_astra_token(root_key, clientID)
    if status not in [200, 204]:
        raise Exception(f"Failed to delete old token {clientID}. Recieved status {status}")
    else:
        logger.info(f"Successfully deleted old token {clientID}")



    ###### Now we can set the pending version to current 
    # First describe the secret to get the current version
    metadata = service_client.describe_secret(SecretId=arn)
    current_version = None
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info("finishSecret: Version %s already marked as AWSCURRENT for %s" % (version, arn))
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    service_client.update_secret_version_stage(SecretId=arn, VersionStage="AWSCURRENT", MoveToVersionId=token, RemoveFromVersionId=current_version)
    logger.info("finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s." % (token, arn))






def get_secret_dict(service_client, arn, stage, token=None, root_secret=False):
    """Gets the secret dictionary corresponding for the secret arn, stage, and token
    This helper function gets credentials for the arn and stage passed in and returns the dictionary by parsing the JSON string
    Args:
        service_client (client): The secrets manager service client
        arn (string): The secret ARN or other identifier
        stage (string): The stage identifying the secret version
        token (string): The ClientRequestToken associated with the secret version, or None if no validation is desired
        root_secret (boolean): A flag that indicates if we are getting a root secret.
    Returns:
        SecretDictionary: Secret dictionary
    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist
        ValueError: If the secret is not valid JSON    
    """

    required_fields = ['astraKey', 'clientID',
                       'clientSecret', 'engine']

    # Only do VersionId validation against the stage if a token is passed in
    if token:
        secret = service_client.get_secret_value(
            SecretId=arn, VersionId=token, VersionStage=stage)
        
    else:
        secret = service_client.get_secret_value(
            SecretId=arn, VersionStage=stage)
    plaintext = secret['SecretString']
    secret_dict = json.loads(plaintext)

    # If not a root secret, require the arn for the root secret
    if not root_secret:
        required_fields.append('rootarn')

    for field in required_fields:
        if field not in secret_dict:
            raise KeyError("%s key is missing from secret JSON" % field)

    if secret_dict['engine'] != 'Astra':
        raise KeyError(
            "Database engine must be set to 'Astra' in order to use this rotation lambda")

    # Parse and return the secret JSON string
    return secret_dict


def delete_astra_token(root_key, clientID):
    """The delete_astra_token function is used to delete a token associated 
    with a particular client ID in Astra. The function takes two arguments:

    Args:
        root_key: a string representing the root key used for authentication with the Astra API.
        clientID: a string representing the ID of the client whose token needs to be deleted.
    
    The function first establishes an HTTPS connection to the Astra API using the 
    api.astra.datastax.com endpoint. It then constructs the API endpoint for deleting
    the client's token by appending the clientID to the base path /v2/clientIdSecrets/.

    The response from the make_API_request function is then unpacked into four variables:
    status, reason, headers, and data. 

    Returns:
        status: Represents the HTTP status code returned by the API, indicating whether the 
        token deletion was successful or not.

    """
    conn = http.client.HTTPSConnection("api.astra.datastax.com")
    payload = ''
    endpoint = f"/v2/clientIdSecrets/{clientID}"
    status, reason, headers, data = make_API_request(
        root_key, "DELETE", endpoint, payload
    )

    return status



def create_astra_token(root_key, roles):
    """The create_astra_token function is used to create an authentication token in Astra
    
    Args:
        root_key: a string representing the root key used for authentication with the Astra API.
        roles: a list of strings representing the roles that the token should be granted access to.

    The function begins by establishing an HTTPS connection to the Astra API using the 
    api.astra.datastax.com endpoint. The payload variable is then defined, which contains a JSON
    object representing the roles that the token should be granted access to.

    The make_API_request function is called with the root_key, "POST" HTTP method,
    /v2/clientIdSecrets endpoint, and payload as arguments. The response from the 
    make_API_request function is then unpacked into four variables: status, reason, headers, and data.


    Returns:
        a tuple containing the clientId, secret, and token values as its output. These values can be used 
        to authenticate with the Astra API and perform authorized actions on the platform.
    """
    conn = http.client.HTTPSConnection("api.astra.datastax.com")
    payload = json.dumps({
        "roles":
        roles
    })

    status, reason, headers, data = make_API_request(
        root_key, "POST", "/v2/clientIdSecrets", payload)

    return data["clientId"], data["secret"], data["token"]


def get_token_roles(root_key, clientID):
    """ The get_token_roles function is used to retrieve the roles associated with a specific authentication
    token in Astra.

    Args:
        root_key: a string representing the root key used for authentication with the Astra API.
        clientID: a string representing the ID of the client whose roles need to be retrieved.

    The function first calls the make_API_request function with the root_key, "GET" HTTP method
    /v2/clientIdSecrets endpoint, and None as the request body.

    The response from the make_API_request function is then unpacked into four variables:
    status, reason, headers, and data. The data variable contains a dictionary with a key
    clients that represents a list of all client IDs and their associated roles.

    The function then loops through the list of clients to find the one with the matching clientID.
    Once the client is found, the roles associated with that client are extracted and stored in a variable.

    Finally, the function returns the roles associated with the specified clientID. 
    """
    # Make the API call to get the list of secrets
    status, reason, headers, data = make_API_request(
        root_key, "GET", "/v2/clientIdSecrets", body=None)
    # find and return the roles for the given clientId
    for client in data['clients']:
        if client['clientId'] == clientID:
            roles = client['roles']
            break
    return roles


def make_API_request(root_key, method, path, body=None):
    """The make_API_request function is a helper function used to make HTTP requests to the Astra API. 
    
    Args:

        root_key: a string representing the root key used for authentication with the Astra API.
        method: a string representing the HTTP method to be used for the request (e.g. "GET", "POST", "PUT", "DELETE").
        path: a string representing the path to the endpoint being requested (e.g. /v2/clientIdSecrets).
        body: an optional parameter that can be used to include a JSON payload in the request.

    The function begins by defining the headers for the HTTP request. These headers include the Content-Type
    and Authorization headers, where the Authorization header includes the root_key for authentication.

    The function then establishes an HTTPS connection to the Astra API using the astraAPIhost endpoint.
    The HTTP request is made with the specified method, path, body, and headers.

    Once the response is received, the function retrieves the HTTP status code, reason phrase, headers,
    and response body. If the response body contains data, it is loaded into a Python dictionary using 
    the json.loads method. If the response body is empty, the data variable is set to an empty string.

    Finally, the HTTPS connection is closed and the function returns a tuple containing the 
    status, reason, headers, and data variables as its output. This function can be used as a helper
    function for making HTTP requests to the Astra API from other functions.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {root_key}',
    }
    conn = http.client.HTTPSConnection(astraAPIhost)
    conn.request(method, path, body, headers)
    response = conn.getresponse()
    status = response.status
    reason = response.reason
    headers = response.getheaders()
    content = response.read()
    if content:
        data = json.loads(content.decode("utf-8"))
    else:
        data = ''
    conn.close()
    return status, reason, headers, data
