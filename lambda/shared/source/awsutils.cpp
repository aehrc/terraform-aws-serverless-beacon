#include "awsutils.hpp"

Aws::String awsutils::getMessageString(aws::lambda_runtime::invocation_request const& req) {
    Aws::Utils::Json::JsonValue json(req.payload);
    return json.View().GetArray("Records").GetItem(0).GetObject("Sns").GetString("Message");
}

vector<string> awsutils::retrieveBucketObjectKeys(Aws::String bucket, Aws::S3::S3Client const& client) {
    cout << "Retrieving bucket objects from : " << bucket << endl;
    vector<string> bucketObjectKeys;
    Aws::S3::Model::ListObjectsV2Request request;
    request.WithBucket(bucket);
    auto response = client.ListObjectsV2(request);
    if (response.IsSuccess()) {
        Aws::Vector<Aws::S3::Model::Object> objects = response.GetResult().GetContents();
        for (Aws::S3::Model::Object& object : objects) {
            bucketObjectKeys.push_back(object.GetKey());
        }
    } else {
        cout << "ERROR Failed with error: " << response.GetError() << endl;
        throw response.GetError();
    }
    return bucketObjectKeys;
}

Aws::S3::Model::GetObjectOutcome awsutils::getS3Object(Aws::String bucket, Aws::String key, Aws::S3::S3Client client) {
    Aws::S3::Model::GetObjectRequest request;
    request.WithBucket(bucket).WithKey(key);
    cout << "calling S3.getObject with bucket: " << bucket << " and key: " << key << endl;
    auto response = client.GetObject(request);
    if (!response.IsSuccess() && response.GetError().ShouldRetry()) {
        response = client.GetObject(request);
        cout << "S3 request retry" << endl;
    }
    if (response.IsSuccess()) {
        size_t totalBytes = response.GetResult().GetContentLength();
        cout << "getS3Object complete: " << bucket << "/" << key << ", received " << totalBytes << " bytes." << endl;
        return response;
    } else {
        std::cout << "ERROR getS3Object Failed with error: " << response.GetError() << std::endl;
        throw response.GetError();
    }
}

void awsutils::publishSnsRequest(
    Aws::SNS::SNSClient const& snsClient,
    const char * topicArn,
     Aws::Utils::Json::JsonValue message
) {

    Aws::SNS::Model::PublishRequest request;
    request.SetTopicArn(getenv(topicArn));
    request.SetMessage(message.View().WriteCompact());

    std::cout << "Calling sns::Publish with TopicArn=\"" << request.GetTopicArn() << "\" and message=\"" << request.GetMessage() << "\"" << std::endl;
    Aws::SNS::Model::PublishOutcome result = snsClient.Publish(request);
    if (result.IsSuccess()) {
        std::cout << "Successfully published" << std::endl;
    } else {
        const Aws::SNS::SNSError error = result.GetError();
        std::cout << "Publish was not successful, received error: " << error.GetMessage() << std::endl;
        if (error.ShouldRetry()) {
            std::cout << "Retrying after 1 second..." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(1));
        } else {
            std::cout << "Not Retrying." << std::endl;
        }
    }
}
