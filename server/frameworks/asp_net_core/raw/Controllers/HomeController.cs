using Microsoft.AspNetCore.Mvc;

namespace aspnet_core.Controllers
{
    public class HomeController : Controller
    {
        [HttpGet("/")]
        public IActionResult Index()
        {
            return Content("<p>Lorem ipsum</p>", "text/html");
        }
    }
}
