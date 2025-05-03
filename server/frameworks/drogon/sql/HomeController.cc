#include "HomeController.h"
#include <drogon/drogon.h>
#include <drogon/orm/DbClient.h>
#include <drogon/HttpResponse.h>
#include <memory>

using namespace drogon;
using namespace drogon::orm;

DbClientPtr HomeController::dbClient = nullptr;

void HomeController::asyncHandleHttpRequest(
    const HttpRequestPtr &req,
    std::function<void(const HttpResponsePtr &)> &&callback) {

    if (!dbClient) {
        const char* dbUrl = std::getenv("DATABASE_URL");
        if (!dbUrl) {
            auto resp = HttpResponse::newHttpResponse();
            resp->setStatusCode(k500InternalServerError);
            resp->setBody("DATABASE_URL environment variable not set");
            callback(resp);
            return;
        }
        dbClient = DbClient::newPgClient(dbUrl, 4);
    }

    dbClient->execSqlAsync(
        "SELECT id, title FROM sample_data ORDER BY id",
        [callback](const Result &result) {
            std::string html = "<div><h1>Sample Data from Postgres:</h1><ul>";
            for (const auto &row : result) {
                html += "<li>" + row["title"].as<std::string>() + "</li>";
            }
            html += "</ul></div>";

            auto resp = HttpResponse::newHttpResponse();
            resp->setContentTypeCode(CT_TEXT_HTML);
            resp->setBody(html);
            callback(resp);
        },
        [callback](const DrogonDbException &e) {
            auto resp = HttpResponse::newHttpResponse();
            resp->setStatusCode(k500InternalServerError);
            resp->setBody("Database error: " + std::string(e.base().what()));
            callback(resp);
        }
    );
}
