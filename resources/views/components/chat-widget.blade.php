{{--
    Floating AI chat widget (Task 3.3) — presentation only.
    Behaviour (fetch to /api/chat, sessionStorage id, typing state) is wired
    in Task 3.5: public/asset/js/chat-widget.js.
--}}
<div id="mbj-chat-widget"
     class="mbj-chat-widget"
     data-endpoint="{{ url('/api/chat') }}">

    {{-- Floating action button --}}
    <button type="button"
            id="mbj-chat-toggle"
            class="mbj-chat-fab"
            aria-controls="mbj-chat-panel"
            aria-expanded="false"
            aria-label="Buka obrolan asisten LPK MBJ">
        <i class="fas fa-comments mbj-chat-fab__icon mbj-chat-fab__icon--open" aria-hidden="true"></i>
        <i class="fas fa-times mbj-chat-fab__icon mbj-chat-fab__icon--close" aria-hidden="true"></i>
    </button>

    {{-- Chat drawer --}}
    <section id="mbj-chat-panel"
             class="mbj-chat-panel"
             role="dialog"
             aria-modal="false"
             aria-labelledby="mbj-chat-title"
             hidden>

        <header class="mbj-chat-header">
            <div class="mbj-chat-header__identity">
                <span class="mbj-chat-avatar" aria-hidden="true"><i class="fas fa-robot"></i></span>
                <div class="mbj-chat-header__text">
                    <h2 id="mbj-chat-title" class="mbj-chat-title">Asisten Resmi LPK MBJ</h2>
                    <p class="mbj-chat-subtitle">Magang, SSW, silabus &amp; biaya</p>
                </div>
            </div>
            <button type="button" id="mbj-chat-close" class="mbj-chat-close" aria-label="Tutup obrolan">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
        </header>

        <div id="mbj-chat-messages"
             class="mbj-chat-messages"
             role="log"
             aria-live="polite"
             aria-relevant="additions">

            <div class="mbj-chat-row mbj-chat-row--bot">
                <span class="mbj-chat-avatar mbj-chat-avatar--sm" aria-hidden="true"><i class="fas fa-robot"></i></span>
                <div class="mbj-chat-bubble mbj-chat-bubble--bot">
                    <p class="mbj-chat-text">Halo! Tanyakan seputar program magang, SSW, silabus &amp; biaya.</p>
                </div>
            </div>
        </div>

        {{-- Typing indicator (hidden until Task 3.5 toggles it) --}}
        <div id="mbj-chat-typing" class="mbj-chat-row mbj-chat-row--bot mbj-chat-typing" hidden>
            <span class="mbj-chat-avatar mbj-chat-avatar--sm" aria-hidden="true"><i class="fas fa-robot"></i></span>
            <div class="mbj-chat-bubble mbj-chat-bubble--bot" aria-label="Asisten sedang mengetik">
                <span class="mbj-chat-typing-dot"></span>
                <span class="mbj-chat-typing-dot"></span>
                <span class="mbj-chat-typing-dot"></span>
            </div>
        </div>

        <form id="mbj-chat-form" class="mbj-chat-form" autocomplete="off">
            <label class="visually-hidden" for="mbj-chat-input">Ketik pertanyaan Anda</label>
            <input id="mbj-chat-input"
                   name="question"
                   type="text"
                   class="mbj-chat-input"
                   placeholder="Ketik pertanyaan Anda..."
                   maxlength="500"
                   required>
            <button type="submit" class="mbj-chat-send" aria-label="Kirim pertanyaan">
                <i class="fas fa-paper-plane" aria-hidden="true"></i>
            </button>
        </form>

        <p class="mbj-chat-disclaimer">Jawaban bersumber dari dokumen publik LPK MBJ Indonesia.</p>
    </section>

    {{-- Source badge template (cloned per source by Task 3.5) --}}
    <template id="mbj-chat-source-template">
        <span class="mbj-chat-source">
            <i class="fas fa-file-alt" aria-hidden="true"></i>
            <span class="mbj-chat-source__label"></span>
        </span>
    </template>
</div>
