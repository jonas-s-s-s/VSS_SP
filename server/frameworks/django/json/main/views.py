from django.http import HttpResponse
from datetime import datetime
import random
import json

def index(request):
    new_object = {
        "message": "Hello World",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "randomNumber": random.randint(0, 999),
    }
    return HttpResponse(f"<pre>{json.dumps(new_object, indent=2)}</pre>", content_type="text/html; charset=utf-8")
