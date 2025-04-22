FROM python:3.13-alpine

COPY . /app
WORKDIR /app

RUN apk add --no-cache git make musl-dev go

# Configure Go
ENV GOROOT /usr/lib/go
ENV GOPATH /go
ENV PATH /go/bin:$PATH
RUN mkdir -p ${GOPATH}/src ${GOPATH}/bin

# Install Bombardier HTTP benchmark
RUN go install github.com/codesenberg/bombardier@latest

RUN pip install -r /app/src/requirements.txt

CMD ["python3", "-u", "/app/src/main.py"]