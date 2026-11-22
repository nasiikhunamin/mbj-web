<?php

return [

    /*
    |--------------------------------------------------------------------------
    | RAG Microservice (FastAPI)
    |--------------------------------------------------------------------------
    |
    | Base URL of the Python RAG backend that the ChatController proxies to.
    | The backend exposes `POST /api/ask` and `GET /api/health`.
    |
    */

    'base_url' => env('RAG_SERVICE_URL', 'http://127.0.0.1:8001'),

    // Seconds before the proxy gives up on the Python service. The pipeline
    // loads embedding models on first call, so this must be generous.
    'timeout' => (int) env('RAG_SERVICE_TIMEOUT', 60),

    // Experiment configuration used when the widget does not pick one.
    // Locked default is E16 (structure-aware + hybrid RRF + rerank).
    'default_config_code' => env('RAG_CONFIG_CODE', 'E16'),

];
