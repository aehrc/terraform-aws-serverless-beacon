FROM --platform=x86_64 public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# TODO remove after replacing pyorc with PyArrow
RUN dnf install -y gcc gcc-c++ cmake

# Install the specified packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# Copy function code
COPY *.py ${LAMBDA_TASK_ROOT}/
ADD shared ${LAMBDA_TASK_ROOT}/shared

# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ]

# DOCS: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions
# build using: docker build  -t docker-image:test .
# run using: docker run --rm -p 9000:8080 docker-image:test
# test using: curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{<BODY>}'