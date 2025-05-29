# Serverless Photo Application

A serverless application for uploading and retrieving photos using AWS services. This application allows users to upload photos, store them in S3, and retrieve them via pre-signed URLs.

## Architecture

![Architecture Diagram](https://via.placeholder.com/800x400?text=Serverless+Photo+App+Architecture)

### Components

- **Frontend**: Simple HTML/CSS/JavaScript interface for uploading and retrieving photos
- **API Gateway**: HTTP API with two endpoints:
  - `POST /photos`: Upload photo and metadata
  - `GET /photos/{photoId}`: Download photo via pre-signed URL
- **Lambda Functions**:
  - `UploadPhotoFunction`: Handles photo uploads, stores in S3, and saves metadata to DynamoDB
  - `GetPhotoFunction`: Retrieves photo metadata from DynamoDB and generates pre-signed URLs for S3 objects
- **S3**: Private bucket for storing photos
- **DynamoDB**: Table for storing photo metadata with the following attributes:
  - `photoId` (Partition Key): Unique identifier for the photo
  - `fileName`: Original file name of the photo
  - `uploadTimestamp`: Timestamp when the photo was uploaded
  - `s3Key`: Key used to store the photo in S3

## Prerequisites

- [AWS Account](https://aws.amazon.com/)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.9+](https://www.python.org/downloads/)

## Setup and Deployment

### Local Development

1. Clone the repository:
   ```
   git clone <repository-url>
   cd photo-app
   ```

2. Install dependencies:
   ```
   pip install -r src/upload_photo/requirements.txt
   pip install -r src/get_photo/requirements.txt
   ```

3. Run tests:
   ```
   python -m pytest tests/unit/
   ```

### Deploy to AWS

1. Build the application:
   ```
   sam build
   ```

2. Deploy the application:
   ```
   sam deploy --guided
   ```
   Follow the prompts to deploy the application to your AWS account.

3. Note the API Gateway endpoint URL from the deployment outputs:
   ```
   PhotosApiEndpoint: https://xxxxxxxxxx.execute-api.region.amazonaws.com/Prod
   ```

### Configure the Frontend

1. Open `frontend/index.html` in a text editor
2. Update the `API_ENDPOINT` variable with your API Gateway endpoint URL:
   ```javascript
   const API_ENDPOINT = 'https://xxxxxxxxxx.execute-api.region.amazonaws.com/Prod';
   ```

3. Open the HTML file in a web browser to use the application

## Testing the Application

### Local Testing

Run unit tests:
```
python -m pytest tests/unit/
```

### Manual Testing

1. Open the frontend in a web browser
2. Upload a photo using the "Upload Photo" section
3. Copy the Photo ID from the response
4. Use the "Get Photo" section to retrieve the photo using its ID

## Security Considerations

- The S3 bucket is configured as private, and photos are only accessible via pre-signed URLs
- Lambda functions follow the principle of least privilege with specific IAM permissions
- API Gateway endpoints can be further secured with authentication mechanisms (not implemented in this demo)

## Optimizations

- Lambda package sizes are kept minimal by only including required dependencies
- DynamoDB is configured with on-demand capacity for cost optimization
- S3 lifecycle rules can be configured to delete old photos automatically

## Assumptions

- Photos are assumed to be in common image formats (JPEG, PNG, etc.)
- The frontend is a simple demonstration and would need enhancements for production use
- No user authentication is implemented in this demo version
- The application assumes moderate usage and may need scaling considerations for high traffic

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.