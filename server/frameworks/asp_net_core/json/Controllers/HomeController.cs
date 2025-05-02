using Microsoft.AspNetCore.Mvc;
using System;

namespace aspnet_core.Controllers
{
    public class HomeController : Controller
    {
        [HttpGet("/")]
        public IActionResult Index()
        {
            var newObject = new
            {
                message = "Hello World",
                timestamp = DateTime.UtcNow.ToString("o"),
                randomNumber = new Random().Next(1000)
            };

            return Content($"<pre>{System.Text.Json.JsonSerializer.Serialize(newObject, new System.Text.Json.JsonSerializerOptions { WriteIndented = true })}</pre>", "text/html");
        }
    }
}
