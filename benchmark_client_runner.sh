#!/bin/bash

JSON_FILE="./client/benchmark_config.json"
CLIENT_COMPOSE_FILE=$(realpath "./client/docker-compose.yml")
LOG_FILE="./benchmark_log.txt"

##### FUNCTION FOR RUNNING CLIENT BENCHMARK #####
run_test() {
  local test_json="$1"
  local test_name="$2"

  echo "STARTED $test_name" >> "$LOG_FILE"
  echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

  # Run the benchmark
  echo "$test_json" > "$JSON_FILE"
  docker compose -f "$CLIENT_COMPOSE_FILE" up --build

  echo "FINISHED $test_name" >> "$LOG_FILE"
  echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  echo "========================================================="

  docker compose -f "$CLIENT_COMPOSE_FILE" down

  # Wait 5 min
  sleep 300
}

##### DEFINE BENCHMARK CONFIGS #####
T1_JSON='
{
  "TestCases": [
    {
      "id": "HTTP1_C50_R10K",
      "connection_count": 50,
      "requests_count": 10000,
      "http_type": "http1"
    },
    {
      "id": "HTTP2_C50_R10K",
      "connection_count": 50,
      "requests_count": 10000,
      "http_type": "http2"
    }
  ]
}
'

T2_JSON='
{
  "TestCases": [
    {
      "id": "HTTP1_C50_R10K",
      "connection_count": 50,
      "requests_count": 10000,
      "http_type": "http1"
    }
  ]
}
'

T3_JSON='
{
  "TestCases": [
    {
      "id": "HTTP2_C50_R10K",
      "connection_count": 50,
      "requests_count": 10000,
      "http_type": "http2"
    }
  ]
}
'

T4_JSON='
{
  "TestCases": [
    {
      "id": "HTTP1_C100_R50K",
      "connection_count": 100,
      "requests_count": 50000,
      "http_type": "http1"
    },
    {
      "id": "HTTP2_C100_R50K",
      "connection_count": 100,
      "requests_count": 50000,
      "http_type": "http2"
    }
  ]
}
'

##### RUN CLIENT BENCHMARKS #####
run_test "$T1_JSON" "T1"
run_test "$T2_JSON" "T2"
run_test "$T3_JSON" "T3"
run_test "$T4_JSON" "T4"
