# Serverless Photo Application

A serverless application for uploading, storing, and retrieving photos using AWS services.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│   Browser   │────▶│  API Gateway│────▶│   Lambda    │────▶│     S3      │
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       ▲                                       │
       │                                       │
       │                                       ▼
       │                               ┌─────────────┐
       │                               │             │
       └───────────────────────────────│  DynamoDB   │
                                       │             │
                                       └─────────────┘
```

### Components

- **Frontend**: HTML/CSS/JavaScript web interface for uploading and viewing photos
- **API Gateway**: HTTP API with endpoints for uploading and retrieving photos
- **Lambda Functions**: 
  - `UploadPhotoFunction`: Handles photo uploads, stores in S3, and saves metadata to DynamoDB
  - `GetPhotoFunction`: Retrieves photo metadata from DynamoDB and generates pre-signed URLs for S3 objects
- **S3**: Stores the uploaded photos securely
- **DynamoDB**: Stores photo metadata (photoId, fileName, uploadTimestamp, s3Key)

## Setup Instructions

### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [AWS CDK](https://aws.amazon.com/cdk/) installed (`npm install -g aws-cdk`)
- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 14+](https://nodejs.org/)

### Deployment Steps

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd photo-app
   ```

2. **Install CDK dependencies**

   ```bash
   cd cdk
   pip install -r requirements.txt
   cd ..
   ```

3. **Bootstrap CDK (if not already done)**

   ```bash
   cdk bootstrap
   ```

4. **Deploy the application**

   ```bash
   cdk deploy
   ```

   Note the outputs from the deployment, including the API endpoint URL.

5. **Update the frontend configuration**

   Open `frontend/script.js` and update the `API_ENDPOINT` variable with the API endpoint URL from the deployment outputs.

### Local Development

#### Running the Frontend Locally

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. You can use any local web server to serve the frontend files. For example, with Python:

   ```bash
   python -m http.server 8000
   ```

   Then open your browser and navigate to `http://localhost:8000`.

#### Testing Lambda Functions Locally

You can use the AWS SAM CLI to test the Lambda functions locally:

1. Install AWS SAM CLI:

   ```bash
   pip install aws-sam-cli
   ```

2. Start the local API:

   ```bash
   sam local start-api
   ```

## API Reference

### Upload Photo

- **Endpoint**: POST /photos
- **Description**: Uploads a photo and stores its metadata
- **Request Body**:
  ```json
  {
    "photo": "base64-encoded-photo-data",
    "fileName": "example.jpg"
  }
  ```
- **Response**:
  ```json
  {
    "photoId": "uuid",
    "message": "Photo uploaded successfully"
  }
  ```

### Get Photo

- **Endpoint**: GET /photos/{photoId}
- **Description**: Retrieves photo metadata and a pre-signed URL for downloading
- **Response**:
  ```json
  {
    "photoId": "uuid",
    "fileName": "example.jpg",
    "uploadTimestamp": "2023-01-01T12:00:00",
    "downloadUrl": "https://presigned-url"
  }
  ```

## Project Structure

```
photo-app/
├── src/
│   ├── upload_photo/
│   │   ├── app.py              # Lambda function for uploading photos
│   │   └── requirements.txt    # Python dependencies for upload function
│   ├── get_photo/
│   │   ├── app.py              # Lambda function for retrieving photos
│   │   └── requirements.txt    # Python dependencies for get function
├── tests/
│   ├── unit/
│   │   ├── test_upload_photo.py # Unit tests for upload function
│   │   └── test_get_photo.py    # Unit tests for get function
├── frontend/
│   ├── index.html              # HTML frontend
│   ├── style.css               # CSS styles
│   └── script.js               # JavaScript for frontend functionality
├── cdk/
│   ├── app.py                  # CDK app entry point
│   ├── photo_app_stack.py      # CDK stack definition
│   └── requirements.txt        # CDK Python dependencies
├── template.yaml               # SAM template for local testing
└── README.md                   # Project documentation
```

## Security Considerations

- S3 bucket is configured with private access only
- Pre-signed URLs are used for secure, time-limited access to photos
- Least-privilege IAM permissions for Lambda functions
- CORS is configured on the API to allow browser access

## Assumptions

- Users authenticate through a separate system (not implemented in this demo)
- Photos are stored for up to one year before automatic deletion
- Maximum photo size is limited by API Gateway payload limits (10MB)
- Frontend stores photo IDs in local storage for demonstration purposes

## Future Enhancements

- User authentication and authorization
- Photo categorization and tagging
- Image resizing and thumbnail generation
- Support for photo albums
- Pagination for retrieving large numbers of photos

## License

This project is licensed under the MIT License - see the LICENSE file for details.