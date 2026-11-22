<?php

namespace App\Http\Controllers;

use App\Models\ChatLog;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\Response as ClientResponse;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Proxies the chat widget to the Python RAG microservice (Task 3.2) and
 * persists every answered question into `chat_logs` for the dashboard.
 */
class ChatController extends Controller
{
    /**
     * Handle one chat turn: validate, forward to FastAPI, log the result.
     */
    public function chat(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'question' => ['required', 'string', 'max:500'],
            'session_id' => ['nullable', 'string', 'max:100'],
            'config_code' => ['nullable', 'string', 'regex:/^E(0[1-9]|1[0-6])$/i'],
        ]);

        $question = trim($validated['question']);
        $configCode = isset($validated['config_code'])
            ? strtoupper($validated['config_code'])
            : (string) config('rag.default_config_code');
        $sessionId = $validated['session_id'] ?? null;

        try {
            $response = Http::acceptJson()
                ->timeout((int) config('rag.timeout'))
                ->post($this->askEndpoint(), [
                    'question' => $question,
                    'config_code' => $configCode,
                    'session_id' => $sessionId,
                ]);
        } catch (ConnectionException $exception) {
            Log::error('RAG service connection failed', [
                'exception' => $exception->getMessage(),
            ]);

            return response()->json([
                'message' => 'Layanan chatbot sedang tidak tersedia. Silakan coba beberapa saat lagi.',
            ], 503);
        }

        if ($response->failed()) {
            Log::error('RAG service returned an error', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return response()->json([
                'message' => $this->errorMessage($response),
            ], 502);
        }

        $data = $response->json() ?? [];
        $answer = (string) ($data['answer'] ?? '');
        $sources = array_values((array) ($data['sources'] ?? []));

        $log = ChatLog::create([
            'session_id' => $sessionId,
            'question' => $question,
            'answer' => $answer,
            'sources' => $sources,
            'retrieval_method' => $data['retrieval_method'] ?? null,
            'chunking_strategy' => $data['chunking_strategy'] ?? null,
            'latency_ms' => $data['latency_ms'] ?? null,
            'context_tokens' => $data['context_tokens'] ?? null,
        ]);

        return response()->json([
            'log_id' => $log->id,
            'session_id' => $log->session_id,
            'question' => $log->question,
            'answer' => $answer,
            'sources' => $sources,
            'is_refusal' => (bool) ($data['is_refusal'] ?? false),
            'experiment_code' => $data['experiment_code'] ?? $configCode,
            'retrieval_method' => $log->retrieval_method,
            'chunking_strategy' => $log->chunking_strategy,
            'latency_ms' => $log->latency_ms,
            'context_tokens' => $log->context_tokens,
        ]);
    }

    /**
     * Absolute URL of the FastAPI ask endpoint.
     */
    private function askEndpoint(): string
    {
        return rtrim((string) config('rag.base_url'), '/').'/api/ask';
    }

    /**
     * Surface the FastAPI `detail` message when present, else a generic one.
     */
    private function errorMessage(ClientResponse $response): string
    {
        $detail = $response->json('detail');

        if (is_string($detail) && $detail !== '') {
            return $detail;
        }

        return 'Terjadi kesalahan saat memproses pertanyaan Anda.';
    }
}
