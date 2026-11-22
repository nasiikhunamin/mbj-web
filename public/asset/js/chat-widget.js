/*
 * Floating RAG chat widget behaviour (Task 3.5).
 *
 * Vanilla JavaScript, no dependencies. The matching markup lives in
 * resources/views/components/chat-widget.blade.php and the styles in
 * public/asset/css/chat-widget.css.
 *
 * Responsibilities:
 *   - open/close the chat drawer (button, close icon, Escape)
 *   - keep one session id per browser tab in sessionStorage
 *   - POST the question to /api/chat and render the answer
 *   - show source-document badges and the typing indicator
 *   - handle offline / timeout / error responses without breaking the page
 */
(function () {
    'use strict';

    var root = document.getElementById('mbj-chat-widget');
    if (!root) {
        return;
    }

    var toggleButton = document.getElementById('mbj-chat-toggle');
    var panel = document.getElementById('mbj-chat-panel');
    var closeButton = document.getElementById('mbj-chat-close');
    var form = document.getElementById('mbj-chat-form');
    var input = document.getElementById('mbj-chat-input');
    var sendButton = form ? form.querySelector('.mbj-chat-send') : null;
    var messages = document.getElementById('mbj-chat-messages');
    var typing = document.getElementById('mbj-chat-typing');
    var sourceTemplate = document.getElementById('mbj-chat-source-template');

    if (!toggleButton || !panel || !form || !input || !messages) {
        return;
    }

    var endpoint = root.getAttribute('data-endpoint') || '/api/chat';
    var sessionKey = 'mbj_chat_session_id';
    var requestTimeoutMs = 90000;
    var fallbackError = 'Maaf, koneksi ke asisten terputus. Silakan coba lagi sebentar lagi.';

    var pending = false;

    /** Return the tab-scoped session id, creating it on first use. */
    function sessionId() {
        var id = null;
        try {
            id = window.sessionStorage.getItem(sessionKey);
        } catch (error) {
            id = null;
        }

        if (!id) {
            id = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
            try {
                window.sessionStorage.setItem(sessionKey, id);
            } catch (error) {
                /* sessionStorage blocked (private mode): keep the id in memory only */
            }
        }

        return id;
    }

    function element(tag, className) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        return node;
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, function (character) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[character];
        });
    }

    /** Minimal, safe inline formatting: **bold** and `code`. */
    function formatInline(escapedText) {
        return escapedText
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    /** Render plain text as paragraphs, escaping everything first. */
    function fillText(container, text) {
        var blocks = String(text === null || text === undefined ? '' : text).trim().split(/\n{2,}/);

        if (!blocks.length) {
            blocks = [''];
        }

        blocks.forEach(function (block) {
            var paragraph = element('p', 'mbj-chat-text');
            paragraph.innerHTML = formatInline(escapeHtml(block)).replace(/\n/g, '<br>');
            container.appendChild(paragraph);
        });
    }

    function botAvatar() {
        var avatar = element('span', 'mbj-chat-avatar mbj-chat-avatar--sm');
        avatar.setAttribute('aria-hidden', 'true');
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        return avatar;
    }

    function sourceBadge(name) {
        var badge = null;

        if (sourceTemplate && sourceTemplate.content && sourceTemplate.content.firstElementChild) {
            badge = sourceTemplate.content.firstElementChild.cloneNode(true);
            var label = badge.querySelector('.mbj-chat-source__label');
            if (label) {
                label.textContent = name;
            }
        } else {
            badge = element('span', 'mbj-chat-source');
            badge.textContent = name;
        }

        return badge;
    }

    function scrollToEnd() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addUserMessage(text) {
        var row = element('div', 'mbj-chat-row mbj-chat-row--user');
        var bubble = element('div', 'mbj-chat-bubble mbj-chat-bubble--user');
        fillText(bubble, text);
        row.appendChild(bubble);
        messages.appendChild(row);
        scrollToEnd();
    }

    function addBotMessage(text, sources) {
        var row = element('div', 'mbj-chat-row mbj-chat-row--bot');
        var bubble = element('div', 'mbj-chat-bubble mbj-chat-bubble--bot');
        fillText(bubble, text);

        if (sources && sources.length) {
            var list = element('div', 'mbj-chat-sources');
            sources.forEach(function (source) {
                if (source) {
                    list.appendChild(sourceBadge(source));
                }
            });
            if (list.childNodes.length) {
                bubble.appendChild(list);
            }
        }

        row.appendChild(botAvatar());
        row.appendChild(bubble);
        messages.appendChild(row);
        scrollToEnd();
    }

    function setPending(isPending) {
        pending = isPending;
        if (sendButton) {
            sendButton.disabled = isPending;
        }
        if (typing) {
            typing.hidden = !isPending;
        }
        if (isPending) {
            scrollToEnd();
        }
    }

    function isOpen() {
        return root.classList.contains('is-open');
    }

    function setOpen(isOpen) {
        root.classList.toggle('is-open', isOpen);
        panel.hidden = !isOpen;
        toggleButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');

        if (isOpen) {
            input.focus();
            scrollToEnd();
        }
    }

    function ask(question) {
        var controller = typeof AbortController === 'function' ? new AbortController() : null;
        var timer = window.setTimeout(function () {
            if (controller) {
                controller.abort();
            }
        }, requestTimeoutMs);

        function finish() {
            window.clearTimeout(timer);
            setPending(false);
        }

        return window
            .fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId()
                }),
                signal: controller ? controller.signal : undefined
            })
            .then(function (response) {
                return response
                    .json()
                    .catch(function () {
                        return {};
                    })
                    .then(function (data) {
                        if (!response.ok) {
                            throw new Error((data && data.message) || 'HTTP ' + response.status);
                        }
                        return data;
                    });
            })
            .then(function (data) {
                addBotMessage(data.answer || fallbackError, data.sources || []);
            })
            .catch(function (error) {
                if (error && error.name === 'AbortError') {
                    addBotMessage('Maaf, asisten terlalu lama merespons. Silakan coba lagi.', []);
                    return;
                }
                addBotMessage((error && error.message) || fallbackError, []);
            })
            .then(finish, finish);
    }

    toggleButton.addEventListener('click', function () {
        setOpen(!isOpen());
    });

    if (closeButton) {
        closeButton.addEventListener('click', function () {
            setOpen(false);
            toggleButton.focus();
        });
    }

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen()) {
            setOpen(false);
            toggleButton.focus();
        }
    });

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        var question = input.value.trim();
        if (!question || pending) {
            return;
        }

        addUserMessage(question);
        input.value = '';
        setPending(true);
        ask(question);
    });
})();
