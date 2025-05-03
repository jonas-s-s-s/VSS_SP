<?php
namespace App\Http\Controllers;

use Illuminate\Support\Facades\DB;

class HomeController extends Controller
{
    public function index()
    {
        $data = DB::table('sample_data')->get();
        return view('home', ['data' => $data]);
    }
}
