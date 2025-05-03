#include "HomeController.h"
#include <drogon/utils/Utilities.h>
#include <json/json.h>
#include <random>
#include <chrono>
#include <iomanip>
#include <sstream>

void HomeController::asyncHandleHttpRequest(
    const drogon::HttpRequestPtr &req,
    std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
    
    Json::Value jsonData;
    jsonData["message"] = "Hello World";
    
    auto now = std::chrono::system_clock::now();
    auto in_time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::gmtime(&in_time_t), "%Y-%m-%dT%H:%M:%SZ");
    jsonData["timestamp"] = ss.str();
    
    std::random_device rd;
    std::mt19937 gen(rd());
    jsonData["randomNumber"] = std::uniform_int_distribution<>(0, 999)(gen);

    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = "  ";
    std::string jsonStr = Json::writeString(writerBuilder, jsonData);

    auto resp = drogon::HttpResponse::newHttpResponse();
    resp->setContentTypeCode(drogon::CT_TEXT_HTML);
    resp->setBody("<pre>" + jsonStr + "</pre>");
    callback(resp);
}
