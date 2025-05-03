<!-- resources/views/home.blade.php -->

<!DOCTYPE html>
<html>
<head>
    <title>Sample Data</title>
</head>
<body>
    <h1>Sample Data from Postgres:</h1>
    <ul>
        @foreach ($data as $row)
            <li>{{ $row->title }}</li>
        @endforeach
    </ul>
</body>
</html>
