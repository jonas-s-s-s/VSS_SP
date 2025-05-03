<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function index()
    {
        $newObject = [
            'message' => 'Hello World',
            'timestamp' => now()->toISOString(),
            'randomNumber' => rand(0, 1000),
        ];

        return view('home', compact('newObject'));
    }
}
