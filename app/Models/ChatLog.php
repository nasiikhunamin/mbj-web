<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

/**
 * One answered question, stored for the evaluation dashboard (Task 3.6)
 * and the experiment logs.
 */
class ChatLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'session_id',
        'question',
        'answer',
        'sources',
        'retrieval_method',
        'chunking_strategy',
        'latency_ms',
        'context_tokens',
    ];

    protected $casts = [
        'sources' => 'array',
        'latency_ms' => 'float',
        'context_tokens' => 'integer',
    ];
}
