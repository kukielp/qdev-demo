import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')
URL_EXPIRATION = int(os.environ.get('URL_EXPIRATION', '3600'))  # Default to 1 hour

def lambda_handler(event, context):
    """
    Lambda function to handle photo retrieval.
    
    This function:
    1. Receives a photo ID from the path parameter
    2. Retrieves the photo metadata from DynamoDB
    3. Generates a pre-signed URL for the photo in S3
    4. Returns the pre-signed URL and metadata
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with pre-signed URL and metadata
    """
    try:
        # Extract photo ID from path parameters
        photo_id = event.get('pathParameters', {}).get('photoId')
        
        if not photo_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing photoId parameter'})
            }
        
        # Get photo metadata from DynamoDB
        table = dynamodb.Table(PHOTOS_TABLE)
        response = table.get_item(
            Key={
                'photoId': photo_id
            }
        )
        
        # Check if photo exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Photo not found'})
            }
        
        # Get photo metadata
        photo_metadata = response['Item']
        s3_key = photo_metadata['s3Key']
        
        # Generate pre-signed URL
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=URL_EXPIRATION
            )
        except ClientError as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Error generating pre-signed URL: {str(e)}'})
            }
        
        # Return success response with pre-signed URL and metadata
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'photoId': photo_metadata['photoId'],
                'fileName': photo_metadata['fileName'],
                'uploadTimestamp': photo_metadata['uploadTimestamp'],
                'downloadUrl': presigned_url
            })
        }
        
    except Exception as e:
        # Log the error
        print(f"Error: {str(e)}")
        
        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }