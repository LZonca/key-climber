<?php
// app/Models/GameScore.php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class GameScore extends Model
{
    use HasFactory;

    protected $table = 'game_scores';

    protected $fillable = [
        'name',
        'score',
        'difficulty'
    ];
}
