<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class ChatControllerTest extends TestCase
{
    use RefreshDatabase;

    /**
     * Representative FastAPI `/api/ask` response.
     */
    private function askPayload(): array
    {
        return [
            'experiment_code' => 'E16',
            'question' => 'Apa syarat usia program magang?',
            'answer' => 'Syarat usia calon peserta magang adalah 18 hingga 30 tahun.',
            'sources' => ['Panduan_Pendaftaran.pdf'],
            'retrieved_sources' => ['Panduan_Pendaftaran.pdf'],
            'retrieval_method' => 'hybrid_rerank',
            'chunking_strategy' => 'structure_aware',
            'latency_ms' => 1234.5,
            'context_tokens' => 512,
            'is_refusal' => false,
        ];
    }

    public function test_it_proxies_a_question_and_logs_the_answer(): void
    {
        Http::fake([
            '*/api/ask' => Http::response($this->askPayload(), 200),
        ]);

        $response = $this->postJson('/api/chat', [
            'question' => 'Apa syarat usia program magang?',
            'session_id' => 'sess-123',
        ]);

        $response->assertOk()
            ->assertJson([
                'answer' => 'Syarat usia calon peserta magang adalah 18 hingga 30 tahun.',
                'sources' => ['Panduan_Pendaftaran.pdf'],
                'is_refusal' => false,
                'experiment_code' => 'E16',
                'chunking_strategy' => 'structure_aware',
            ]);

        $this->assertDatabaseHas('chat_logs', [
            'session_id' => 'sess-123',
            'question' => 'Apa syarat usia program magang?',
            'retrieval_method' => 'hybrid_rerank',
            'chunking_strategy' => 'structure_aware',
        ]);
    }

    public function test_it_defaults_to_the_locked_experiment_config(): void
    {
        Http::fake([
            '*/api/ask' => Http::response($this->askPayload(), 200),
        ]);

        $this->postJson('/api/chat', ['question' => 'Halo'])->assertOk();

        Http::assertSent(function ($request) {
            return $request['config_code'] === config('rag.default_config_code');
        });
    }

    public function test_it_rejects_a_question_longer_than_500_characters(): void
    {
        Http::fake();

        $this->postJson('/api/chat', ['question' => str_repeat('a', 501)])
            ->assertStatus(422)
            ->assertJsonValidationErrors('question');

        Http::assertNothingSent();
        $this->assertDatabaseCount('chat_logs', 0);
    }

    public function test_it_rejects_an_invalid_config_code(): void
    {
        Http::fake();

        $this->postJson('/api/chat', [
            'question' => 'Halo',
            'config_code' => 'E99',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('config_code');

        Http::assertNothingSent();
    }

    public function test_it_returns_503_when_the_rag_service_is_unreachable(): void
    {
        Http::fake(function () {
            throw new ConnectionException('Connection refused');
        });

        $this->postJson('/api/chat', ['question' => 'Halo'])
            ->assertStatus(503)
            ->assertJsonStructure(['message']);

        $this->assertDatabaseCount('chat_logs', 0);
    }

    public function test_it_returns_502_when_the_rag_service_fails(): void
    {
        Http::fake([
            '*/api/ask' => Http::response([
                'detail' => 'Layanan generator sedang tidak tersedia.',
            ], 503),
        ]);

        $this->postJson('/api/chat', ['question' => 'Halo'])
            ->assertStatus(502)
            ->assertJson(['message' => 'Layanan generator sedang tidak tersedia.']);

        $this->assertDatabaseCount('chat_logs', 0);
    }
}
