from django.shortcuts import render
from django.db import connection

def index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, title FROM sample_data")
        rows = cursor.fetchall()

    context = {
        'rows': rows
    }
    return render(request, 'index.html', context)
