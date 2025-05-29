import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from botocore.exceptions import ClientError

# Add the src directory to the path so we can import the app module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/get_photo'))

# Import the app module
import app

class TestGetPhoto(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('app.s3_client.generate_presigned_url')
    @patch('app.dynamodb.Table')
    def test_successful_get_photo(self, mock_table, mock_generate_presigned_url):
        """Test successful photo retrieval"""
        # Mock DynamoDB get_item response
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test_photo.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test_photo.jpg'
            }
        }
        
        # Mock S3 presigned URL
        mock_presigned_url = 'https://example.com/presigned-url'
        mock_generate_presigned_url.return_value = mock_presigned_url
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the lambda handler
        response = app.lambda_handler(test_event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 200)
        
        # Parse response body
        response_body = json.loads(response['body'])
        
        # Assert response body
        self.assertEqual(response_body['photoId'], 'test-photo-id')
        self.assertEqual(response_body['fileName'], 'test_photo.jpg')
        self.assertEqual(response_body['uploadTimestamp'], '2023-01-01T12:00:00')
        self.assertEqual(response_body['downloadUrl'], mock_presigned_url)
        
        # Assert DynamoDB get_item was called correctly
        mock_table_instance.get_item.assert_called_once_with(
            Key={
                'photoId': 'test-photo-id'
            }
        )
        
        # Assert S3 generate_presigned_url was called correctly
        mock_generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': app.BUCKET_NAME,
                'Key': 'test-photo-id/test_photo.jpg'
            },
            ExpiresIn=app.URL_EXPIRATION
        )

    def test_missing_photo_id(self):
        """Test error handling when photo ID is missing"""
        # Test with missing photoId
        test_event_missing_photo_id = {
            'pathParameters': {}
        }
        
        response = app.lambda_handler(test_event_missing_photo_id, {})
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Missing photoId parameter', json.loads(response['body'])['error'])
        
        # Test with no pathParameters
        test_event_no_path_params = {}
        
        response = app.lambda_handler(test_event_no_path_params, {})
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Missing photoId parameter', json.loads(response['body'])['error'])

    @patch('app.dynamodb.Table')
    def test_photo_not_found(self, mock_table):
        """Test error handling when photo is not found in DynamoDB"""
        # Mock DynamoDB get_item response with no Item
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {}
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'non-existent-photo-id'
            }
        }
        
        # Call the lambda handler
        response = app.lambda_handler(test_event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body'])['error'], 'Photo not found')

    @patch('app.dynamodb.Table')
    @patch('app.s3_client.generate_presigned_url')
    def test_s3_presigned_url_error(self, mock_generate_presigned_url, mock_table):
        """Test error handling when generating presigned URL fails"""
        # Mock DynamoDB get_item response
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test_photo.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test_photo.jpg'
            }
        }
        
        # Mock S3 generate_presigned_url to raise an exception
        mock_generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'InvalidBucketName', 'Message': 'The specified bucket is not valid'}},
            'generate_presigned_url'
        )
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the lambda handler
        response = app.lambda_handler(test_event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error generating pre-signed URL', json.loads(response['body'])['error'])

if __name__ == '__main__':
    unittest.main()