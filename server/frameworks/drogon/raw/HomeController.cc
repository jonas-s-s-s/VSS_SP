#include "HomeController.h"

void HomeController::asyncHandleHttpRequest(
    const drogon::HttpRequestPtr &req,
    std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
    auto resp = drogon::HttpResponse::newHttpResponse();
    resp->setContentTypeCode(drogon::CT_TEXT_HTML);
    resp->setBody("<p>Lorem ipsum</p>");
    callback(resp);
}
