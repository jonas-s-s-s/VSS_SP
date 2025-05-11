# Web Frameworks Benchmark

A benchmarking tool for various web frameworks, implemented mostly in Python. Uses docker-compose to deploy and run the testing infrastructure including the frameworks themselves.

The project consists of the following three parts:
- `./client`
  - A python app which acts as an HTTP client for the web frameworks
  - Uses [Bombardier](github.com/codesenberg/bombardier) HTTP benchmarking tool to perform the actual request-response part of the benchmark
    - Bombardier outputs metrics as JSON, this is processed and saved into the database
  - Uses `benchmark_config.json` to define the HTTP test cases
  - `config.env` contains IP of the server and InfluxDB credentials
  - `ApiClient.py` contains code for controlling the benchmark server's API


- `./data_collection`
  - `influxdb` subdirectory contains docker files used to start the InfluxDB database, this database is used for metrics collection
  - The `data_report_generator` subdirectory contains a python app that generates a static website by querying data from InfluxDB
    - Jinja2 templating engine is used, together with some frontend JS libraries
  

- `./server`
  - `./frameworks` contains code for each framework
  - `./src` contains the "server" python app, this controls which framework is currently running
    - the client app calls the API of this server, allowing it to switch frameworks on demand

---

## Overview

**Frameworks**:
- `asp_net_core`
- `astro_js`
- `django`
- `drogon`
- `laravel`
- `next_js`
- `ruby_on_rails`
- `spring_boot`

**Test Modes**:
- **SQL** – Includes database interactions
- **JSON** – Static JSON responses
- **Raw** – Raw HTTP response (lorem ipsum)

---

## Sample Output
- https://jonas-s-s-s.github.io/VSS_SP/ includes four auto-generated benchmark reports 
