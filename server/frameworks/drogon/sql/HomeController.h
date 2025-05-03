#pragma once
#include <drogon/HttpSimpleController.h>
#include <drogon/orm/DbClient.h>

class HomeController : public drogon::HttpSimpleController<HomeController> {
  public:
    void asyncHandleHttpRequest(
        const drogon::HttpRequestPtr &req,
        std::function<void(const drogon::HttpResponsePtr &)> &&callback) override;

    PATH_LIST_BEGIN
    PATH_ADD("/", drogon::Get);
    PATH_LIST_END

  private:
    static drogon::orm::DbClientPtr dbClient;
};
