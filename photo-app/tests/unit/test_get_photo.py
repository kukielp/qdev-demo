import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from botocore.exceptions import ClientError

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/get_photo'))

# Import the Lambda function
import app

class TestGetPhotoFunction(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_successful_get_photo(self, mock_table, mock_s3):
        """Test successful photo retrieval"""
        # Mock DynamoDB response
        mock_ddb_table = MagicMock()
        mock_table.return_value = mock_ddb_table
        mock_ddb_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test.jpg'
            }
        }
        
        # Mock S3 presigned URL
        mock_s3.generate_presigned_url.return_value = 'https://test-bucket.s3.amazonaws.com/test-photo-id/test.jpg?signature'
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET_NAME'] = 'test-bucket'
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        os.environ['PRESIGNED_URL_EXPIRATION'] = '3600'
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], 'test-photo-id')
        self.assertEqual(response_body['fileName'], 'test.jpg')
        self.assertEqual(response_body['uploadTimestamp'], '2023-01-01T12:00:00')
        self.assertEqual(response_body['downloadUrl'], 'https://test-bucket.s3.amazonaws.com/test-photo-id/test.jpg?signature')
        
        # Verify DynamoDB get_item was called correctly
        mock_ddb_table.get_item.assert_called_once_with(Key={'photoId': 'test-photo-id'})
        
        # Verify S3 generate_presigned_url was called correctly
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': 'test-bucket',
                'Key': 'test-photo-id/test.jpg'
            },
            ExpiresIn=3600
        )

    @patch('app.dynamodb.Table')
    def test_missing_photo_id(self, mock_table):
        """Test handling of missing photoId parameter"""
        # Set environment variables
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event with missing photoId
        test_event = {
            'pathParameters': None
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify DynamoDB was not called
        mock_table.return_value.get_item.assert_not_called()

    @patch('app.dynamodb.Table')
    def test_photo_not_found(self, mock_table):
        """Test handling of photo not found in DynamoDB"""
        # Mock DynamoDB response for item not found
        mock_ddb_table = MagicMock()
        mock_table.return_value = mock_ddb_table
        mock_ddb_table.get_item.return_value = {}  # No Item in response
        
        # Set environment variables
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'non-existent-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 404)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Photo not found')

    @patch('app.dynamodb.Table')
    def test_dynamodb_error(self, mock_table):
        """Test handling of DynamoDB error"""
        # Mock DynamoDB to raise an exception
        mock_ddb_table = MagicMock()
        mock_table.return_value = mock_ddb_table
        mock_ddb_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'DynamoDB error'}},
            'GetItem'
        )
        
        # Set environment variables
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_s3_presigned_url_error(self, mock_table, mock_s3):
        """Test handling of S3 presigned URL generation error"""
        # Mock DynamoDB response
        mock_ddb_table = MagicMock()
        mock_table.return_value = mock_ddb_table
        mock_ddb_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test.jpg'
            }
        }
        
        # Mock S3 to raise an exception
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'S3 error'}},
            'GeneratePresignedUrl'
        )
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET_NAME'] = 'test-bucket'
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)

if __name__ == '__main__':
    unittest.main()