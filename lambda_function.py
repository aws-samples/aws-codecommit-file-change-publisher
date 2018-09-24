# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os

# Define the environment variables for repository branch name and region
REGION = os.getenv('AWS_REGION')
MAIN_BRANCH_NAME = os.getenv('MAIN_BRANCH_NAME')
REPOSITORY_NAME = os.getenv('REPOSITORY_NAME')

codecommit = boto3.client('codecommit')

def publish(repository, message):
  SNSTopicArn = os.getenv('SNS_TOPIC_ARN')
  SNSClient = boto3.client('sns', region_name=REGION)
  SNSClient.publish(
      TopicArn=SNSTopicArn,
      Subject = 'CodeCommit Update - Repository: {0}'.format(repository),
      Message = message
  )

def getFileDifferences(repository_name, lastCommitID, previousCommitID):
    response = None

    if previousCommitID != None:
        response = codecommit.get_differences(
            repositoryName=repository_name,
            beforeCommitSpecifier=previousCommitID,
            afterCommitSpecifier=lastCommitID
        )
    else:
        # The case of getting initial commit (Without beforeCommitSpecifier)
        response = codecommit.get_differences(
            repositoryName=repository_name,
            afterCommitSpecifier=lastCommitID
        )

    differences = []

    if response == None:
        return differences

    while "nextToken" in response:
        response = codecommit.get_differences(
            repositoryName=repository_name,
            beforeCommitSpecifier=previousCommitID,
            afterCommitSpecifier=lastCommitID,
            nextToken=response["nextToken"]
        )
        differences += response.get("differences", [])
    else:
        differences += response["differences"]

    return differences

def getDiffChangeTypeMessage(changeType):
    type = {
        'M': 'Modification',
        'D': 'Deletion',
        'A': 'Addition'
    }
    return type[changeType]

def getLastCommitID(repository, branch="master"):
    response = codecommit.get_branch(
        repositoryName=repository,
        branchName=branch
    )
    commitId = response['branch']['commitId']
    return commitId

def getLastCommitLog(repository, commitId):
    response = codecommit.get_commit(
        repositoryName=repository,
        commitId=commitId
    )
    return response['commit']


def getMessageText(differences, lastCommit):
    text = ''
    text += 'commit ID: {0}\n'.format(lastCommit['commitId'])
    text += 'author: {0} ({1}) - {2}\n'.format(lastCommit['author']['name'], lastCommit['author']['email'], lastCommit['author']['date'])
    text += 'message: {0}\n'.format(lastCommit['message'])
    for diff in differences:
        if 'afterBlob' in diff:
            text += 'File: {0} {1} - Blob ID: {2}\n'.format(diff['afterBlob']['path'], getDiffChangeTypeMessage(diff['changeType']), diff['afterBlob']['blobId'])
        if 'beforeBlob' in diff:
            text += 'File: {0} {1} - Blob ID: {2}\n'.format(diff['beforeBlob']['path'], getDiffChangeTypeMessage(diff['changeType']), diff['beforeBlob']['blobId'])

    return text

def lambda_handler(event, context):
    # Get the repository from the event and show its git clone URL
    # repository = event['Records'][0]['eventSourceARN'].split(':')[5]
    repository = REPOSITORY_NAME

    try:
        lastCommitID = getLastCommitID(repository, MAIN_BRANCH_NAME)
        lastCommit = getLastCommitLog(repository, lastCommitID)

        previousCommitID = None
        if len(lastCommit['parents']) > 0:
            previousCommitID = lastCommit['parents'][0]

        print('lastCommitID: {0} previousCommitID: {1}'.format(lastCommitID, previousCommitID))

        differences = getFileDifferences(repository, lastCommitID, previousCommitID)
        messageText = getMessageText(differences, lastCommit)

        return publish(repository, messageText)

    except Exception as e:
        print(e)
        print('Error getting repository {}. Make sure it exists and that your repository is in the same region as this function.'.format(repository))
        raise e
