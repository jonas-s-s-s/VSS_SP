# Build stage
FROM ubuntu:22.04 as builder

RUN apt-get update && \
    apt-get install -y git cmake g++ libjsoncpp-dev uuid-dev zlib1g-dev libssl-dev make curl libpq-dev

WORKDIR /drogon

RUN git clone https://github.com/drogonframework/drogon.git && \
    cd drogon && \
    git checkout v1.9.10 && \
    git submodule update --init && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr && \
    make -j$(nproc) && \
    make install

COPY . /app
WORKDIR /app

RUN mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc)

# Runtime stage
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y libjsoncpp-dev libssl3 zlib1g uuid-runtime libpq5 && \
    apt-get clean

WORKDIR /app
COPY --from=builder /app/build/drogon_app .
COPY --from=builder /app/config.json .

EXPOSE 3000

CMD ["./drogon_app"]
