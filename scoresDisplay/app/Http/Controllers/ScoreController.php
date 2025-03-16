<?php
// app/Http/Controllers/ScoreController.php

namespace App\Http\Controllers;

use App\Models\GameScore;
use App\Models\CliScores;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class ScoreController extends Controller
{

    public function getGameScores()
    {
        $scores = GameScore::orderBy('score', 'desc')->limit(10)->get();
        return response()->json($scores);
    }

    public function getCliScores()
    {
        $scores = CliScores::orderBy('score', 'desc')->limit(10)->get();
        return response()->json($scores);
    }

    public function storeGameScore(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:100',
            'score' => 'required|integer|min:0',
            'difficulty' => 'nullable|string|max:50',
        ]);

        if ($validator->fails()) {
            return response()->json(['errors' => $validator->errors()], 422);
        }

        $score = GameScore::create([
            'name' => $request->name,
            'score' => $request->score,
            'difficulty' => $request->difficulty ?? 'normal'
        ]);

        return response()->json($score, 201);
    }

    public function storeCliScore(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:100',
            'score' => 'required|integer|min:0',
            'letters' => 'nullable|integer|min:0',
            'avg_time' => 'nullable|numeric|min:0',
        ]);

        if ($validator->fails()) {
            return response()->json(['errors' => $validator->errors()], 422);
        }

        $score = CliScores::create([
            'name' => $request->name,
            'score' => $request->score,
            'letters' => $request->letters ?? 0,
            'avg_time' => $request->avg_time ?? 0
        ]);

        return response()->json($score, 201);
    }
}
