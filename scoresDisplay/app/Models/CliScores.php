<?php
// app/Models/CliScore.php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class CliScores extends Model
{
    use HasFactory;

    protected $table = 'cli_scores';

    protected $fillable = [
        'name',
        'score',
        'letters',
        'avg_time'
    ];
}
