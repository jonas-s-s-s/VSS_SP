using Microsoft.AspNetCore.Mvc;
using Npgsql;
using System.Text;

namespace aspnet_core.Controllers
{
    [ApiController]
    public class HomeController : Controller
    {
        [HttpGet("/")]
        public IActionResult Index()
        {
            var connString = Environment.GetEnvironmentVariable("DATABASE_URL")
                             ?? throw new InvalidOperationException("DATABASE_URL not set");
            var sb = new StringBuilder();
            sb.AppendLine("<h1>Sample Data from Postgres:</h1>");
            sb.AppendLine("<ul>");

            using var conn = new NpgsqlConnection(connString);
            conn.Open();
            using var cmd = new NpgsqlCommand("SELECT id, title FROM sample_data", conn);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                var title = reader.GetString(1);
                sb.AppendLine($"<li>{System.Net.WebUtility.HtmlEncode(title)}</li>");
            }

            sb.AppendLine("</ul>");
            return Content(sb.ToString(), "text/html; charset=utf-8");
        }
    }
}
