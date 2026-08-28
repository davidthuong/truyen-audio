// App State
let currentScenes = [];
let isRendering = false;
let activeJobId = null;
let pollTimer = null;

// DOM Elements
const elements = {
    // Tabs
    tabAiGen: document.getElementById("tab-ai-gen"),
    tabCustomText: document.getElementById("tab-custom-text"),
    contentAiGen: document.getElementById("content-ai-gen"),
    contentCustomText: document.getElementById("content-custom-text"),
    
    // Inputs AI
    aiGenre: document.getElementById("ai-genre"),
    aiDuration: document.getElementById("ai-duration"),
    aiTopic: document.getElementById("ai-topic"),
    btnGenerateStory: document.getElementById("btn-generate-story"),
    
    // Inputs Custom
    customStoryText: document.getElementById("custom-story-text"),
    fileUploadInput: document.getElementById("file-upload-input"),
    btnParseStory: document.getElementById("btn-parse-story"),
    
    // Scene Container
    scenesContainer: document.getElementById("scenes-container"),
    sceneCounter: document.getElementById("scene-counter"),
    btnAddScene: document.getElementById("btn-add-scene"),
    
    // Video Config
    cfgTitle: document.getElementById("cfg-title"),
    cfgChannel: document.getElementById("cfg-channel"),
    cfgVoice: document.getElementById("cfg-voice"),
    cfgRate: document.getElementById("cfg-rate"),
    cfgPitch: document.getElementById("cfg-pitch"),
    cfgStyle: document.getElementById("cfg-style"),
    cfgAspectRatio: document.getElementById("cfg-aspect-ratio"),
    cfgBgm: document.getElementById("cfg-bgm"),
    cfgBgmVolume: document.getElementById("cfg-bgm-volume"),
    cfgEnableWaveform: document.getElementById("cfg-enable-waveform"),
    
    // Actions
    btnStartRender: document.getElementById("btn-start-render"),
    btnQuickThumb: document.getElementById("btn-quick-thumb"),
    btnQuickDesc: document.getElementById("btn-quick-desc"),
    btnRegenThumbAi: document.getElementById("btn-regen-thumb-ai"),
    btnRegenDesc: document.getElementById("btn-regen-desc"),
    btnCopyDesc: document.getElementById("btn-copy-desc"),
    btnOpenFolder: document.getElementById("btn-open-folder"),
    btnModalOpenFolder: document.getElementById("btn-modal-open-folder"),
    btnOpenSettings: document.getElementById("btn-open-settings"),
    
    // Settings Modal
    settingsModal: document.getElementById("settings-modal"),
    btnCloseSettingsModal: document.getElementById("btn-close-settings-modal"),
    btnSaveSettings: document.getElementById("btn-save-settings"),
    setApiKey: document.getElementById("set-api-key"),
    setBaseUrl: document.getElementById("set-base-url"),
    setChatModel: document.getElementById("set-chat-model"),
    setImageProvider: document.getElementById("set-image-provider"),
    setImageModel: document.getElementById("set-image-model"),
    groupDalleModel: document.getElementById("group-dalle-model"),
    setAuthUsername: document.getElementById("set-auth-username"),
    setAuthPassword: document.getElementById("set-auth-password"),
    setAuthEnabled: document.getElementById("set-auth-enabled"),
    setTtsProvider: document.getElementById("set-tts-provider"),
    setVivibeApiKey: document.getElementById("set-vivibe-api-key"),
    setVivibeVoiceId: document.getElementById("set-vivibe-voice-id"),
    selectVivibeVoice: document.getElementById("select-vivibe-voice"),
    btnFetchVivibeVoices: document.getElementById("btn-fetch-vivibe-voices"),
    groupVivibeConfig: document.getElementById("group-vivibe-config"),
    groupVivibeVoicesSelect: document.getElementById("group-vivibe-voices-select"),
    
    // Render Modal
    renderModal: document.getElementById("render-modal"),
    modalTitleText: document.getElementById("modal-title-text"),
    btnCloseModal: document.getElementById("btn-close-modal"),
    progressContainer: document.getElementById("progress-container"),
    progressStep: document.getElementById("progress-step"),
    progressPercent: document.getElementById("progress-percent"),
    progressFill: document.getElementById("progress-fill"),
    
    // Result
    resultContainer: document.getElementById("result-container"),
    finalVideoPlayer: document.getElementById("final-video-player"),
    finalThumbImg: document.getElementById("final-thumb-img"),
    finalDescText: document.getElementById("final-desc-text"),
    btnDownloadVideo: document.getElementById("btn-download-video"),
    btnDownloadThumb: document.getElementById("btn-download-thumb"),
    
    // Audio Player
    ttsPreviewPlayer: document.getElementById("tts-preview-player")
};

// Khởi chạy ứng dụng
document.addEventListener("DOMContentLoaded", async () => {
    initEvents();
    await loadInitialConfig();
    await loadSettingsData();
    renderScenesList(); // Chỉ hiển thị trạng thái ban đầu, KHÔNG tự động gọi API viết truyện
});

// Gán các sự kiện tương tác
function initEvents() {
    // Chuyển Tab
    elements.tabAiGen.addEventListener("click", () => switchTab("ai"));
    elements.tabCustomText.addEventListener("click", () => switchTab("custom"));
    
    // Tạo kịch bản AI
    elements.btnGenerateStory.addEventListener("click", generateAiStory);
    
    // Phân tích truyện tùy chỉnh
    elements.btnParseStory.addEventListener("click", parseCustomStory);
    
    // Upload file .txt
    elements.fileUploadInput.addEventListener("change", handleFileUpload);
    
    // Thêm cảnh thủ công
    elements.btnAddScene.addEventListener("click", addNewScene);
    
    // Đổi Style đồng bộ
    elements.aiGenre.addEventListener("change", (e) => {
        elements.cfgStyle.value = e.target.value;
    });
    
    // Bắt đầu Render
    elements.btnStartRender.addEventListener("click", startFullRender);
    
    // Tạo Thử Thumbnail AI Nhanh
    if (elements.btnQuickThumb) {
        elements.btnQuickThumb.addEventListener("click", quickGenerateAiThumbnail);
    }
    
    // Tạo lại Thumbnail AI từ trong Modal kết quả
    if (elements.btnRegenThumbAi) {
        elements.btnRegenThumbAi.addEventListener("click", quickGenerateAiThumbnail);
    }

    // Tạo Nhanh Mô Tả Video SEO
    if (elements.btnQuickDesc) {
        elements.btnQuickDesc.addEventListener("click", generateDescriptionAction);
    }

    // Viết Lại Mô Tả Trong Modal
    if (elements.btnRegenDesc) {
        elements.btnRegenDesc.addEventListener("click", generateDescriptionAction);
    }

    // Sao Chép Mô Tả 1-Click
    if (elements.btnCopyDesc) {
        elements.btnCopyDesc.addEventListener("click", copyDescriptionToClipboard);
    }
    
    // Modal Settings
    elements.btnOpenSettings.addEventListener("click", () => {
        elements.settingsModal.classList.remove("hidden");
    });
    elements.btnCloseSettingsModal.addEventListener("click", () => {
        elements.settingsModal.classList.add("hidden");
    });
    elements.btnSaveSettings.addEventListener("click", saveSettingsData);
    elements.setImageProvider.addEventListener("change", (e) => {
        if (e.target.value === "openai_dalle") {
            elements.groupDalleModel.classList.remove("hidden");
        } else {
            elements.groupDalleModel.classList.add("hidden");
        }
    });

    if (elements.setTtsProvider) {
        elements.setTtsProvider.addEventListener("change", (e) => {
            if (e.target.value === "vivibe") {
                elements.groupVivibeConfig.classList.remove("hidden");
            } else {
                elements.groupVivibeConfig.classList.add("hidden");
            }
        });
    }

    if (elements.selectVivibeVoice) {
        elements.selectVivibeVoice.addEventListener("change", (e) => {
            if (e.target.value) {
                elements.setVivibeVoiceId.value = e.target.value;
            }
        });
    }

    if (elements.btnFetchVivibeVoices) {
        elements.btnFetchVivibeVoices.addEventListener("click", () => fetchVivibeVoicesList());
    }
    
    // Modal Close
    elements.btnCloseModal.addEventListener("click", () => {
        elements.renderModal.classList.add("hidden");
    });
    
    // Mở thư mục
    elements.btnOpenFolder.addEventListener("click", openOutputFolder);
    elements.btnModalOpenFolder.addEventListener("click", openOutputFolder);
}

function switchTab(mode) {
    if (mode === "ai") {
        elements.tabAiGen.classList.add("active");
        elements.tabCustomText.classList.remove("active");
        elements.contentAiGen.classList.remove("hidden");
        elements.contentCustomText.classList.add("hidden");
    } else {
        elements.tabCustomText.classList.add("active");
        elements.tabAiGen.classList.remove("active");
        elements.contentCustomText.classList.remove("hidden");
        elements.contentAiGen.classList.add("hidden");
    }
}

// Tải danh sách Config từ Server
async function loadInitialConfig() {
    try {
        const resp = await fetch("/api/config");
        if (resp.ok) {
            const data = await resp.json();
            if (data.voices && elements.cfgVoice) {
                elements.cfgVoice.innerHTML = data.voices.map(v => 
                    `<option value="${v.id}" ${v.default ? 'selected' : ''}>${v.name}</option>`
                ).join("");
            }
        }
    } catch (err) {
        console.warn("Không thể tải config:", err);
    }
}

// Tải danh sách giọng đọc từ ViVibe JSON-RPC API
async function fetchVivibeVoicesList(selectedVoiceId = "") {
    const key = elements.setVivibeApiKey ? elements.setVivibeApiKey.value.trim() : "";
    if (!key) {
        alert("Vui lòng nhập ViVibe API Key trước khi tải danh sách giọng!");
        return;
    }
    if (elements.btnFetchVivibeVoices) {
        elements.btnFetchVivibeVoices.disabled = true;
        elements.btnFetchVivibeVoices.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
    }
    try {
        const resp = await fetch(`/api/vivibe/voices?key=${encodeURIComponent(key)}`);
        const data = await resp.json();
        if (data.voices && data.voices.length > 0) {
            if (elements.selectVivibeVoice) {
                elements.selectVivibeVoice.innerHTML = `<option value="">-- Chọn giọng để tự động điền --</option>` + data.voices.map(v => 
                    `<option value="${v.raw_id}" ${v.raw_id === selectedVoiceId || v.id === selectedVoiceId ? 'selected' : ''}>${v.name} (${v.raw_id})</option>`
                ).join("");
            }
            if (elements.groupVivibeVoicesSelect) {
                elements.groupVivibeVoicesSelect.classList.remove("hidden");
            }
            if (selectedVoiceId && elements.setVivibeVoiceId) {
                elements.setVivibeVoiceId.value = selectedVoiceId;
            } else if (!elements.setVivibeVoiceId.value && data.voices[0]) {
                elements.setVivibeVoiceId.value = data.voices[0].raw_id;
            }
            alert(`Đã tìm thấy ${data.voices.length} giọng đọc trên ViVibe!`);
            return data.voices;
        } else {
            alert("Không tìm thấy giọng đọc nào trên tài khoản ViVibe hoặc API Key chưa đúng.");
        }
    } catch (err) {
        console.warn("Lỗi tải giọng ViVibe:", err);
    } finally {
        if (elements.btnFetchVivibeVoices) {
            elements.btnFetchVivibeVoices.disabled = false;
            elements.btnFetchVivibeVoices.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Tải Giọng Của Tôi`;
        }
    }
}

// Tải Settings từ Server
async function loadSettingsData() {
    try {
        const resp = await fetch("/api/settings");
        if (resp.ok) {
            const s = await resp.json();
            elements.setApiKey.value = s.api_key || "";
            elements.setBaseUrl.value = s.base_url || "https://api.openai.com/v1";
            elements.setChatModel.value = s.chat_model || "gpt-4o-mini";
            elements.setImageProvider.value = s.image_provider || "pollinations";
            elements.setImageModel.value = s.image_model || "dall-e-3";
            if (elements.setAuthUsername) elements.setAuthUsername.value = s.auth_username || "admin";
            if (elements.setAuthPassword) elements.setAuthPassword.value = s.auth_password || "admin123";
            if (elements.setAuthEnabled) elements.setAuthEnabled.checked = s.auth_enabled !== false;
            
            if (elements.setTtsProvider) elements.setTtsProvider.value = s.tts_provider || "edge_tts";
            if (elements.setVivibeApiKey) elements.setVivibeApiKey.value = s.vivibe_api_key || "";
            if (elements.setVivibeVoiceId) elements.setVivibeVoiceId.value = s.vivibe_voice_id || "";
            
            if (s.image_provider === "openai_dalle") {
                elements.groupDalleModel.classList.remove("hidden");
            } else {
                elements.groupDalleModel.classList.add("hidden");
            }

            if (s.tts_provider === "vivibe") {
                if (elements.groupVivibeConfig) elements.groupVivibeConfig.classList.remove("hidden");
            } else {
                if (elements.groupVivibeConfig) elements.groupVivibeConfig.classList.add("hidden");
            }

            if (s.vivibe_api_key) {
                await fetchVivibeVoicesList(s.vivibe_voice_id || "");
            }
        }
    } catch (err) {
        console.warn("Lỗi load settings:", err);
    }
}

// Lưu Settings vào Server
async function saveSettingsData() {
    elements.btnSaveSettings.disabled = true;
    elements.btnSaveSettings.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang lưu...`;

    const payload = {
        api_key: elements.setApiKey.value.trim(),
        base_url: elements.setBaseUrl.value.trim() || "https://api.openai.com/v1",
        chat_model: elements.setChatModel.value.trim() || "gpt-4o-mini",
        image_provider: elements.setImageProvider.value,
        image_model: elements.setImageModel.value.trim() || "dall-e-3",
        auth_enabled: elements.setAuthEnabled ? elements.setAuthEnabled.checked : true,
        auth_username: elements.setAuthUsername ? elements.setAuthUsername.value.trim() : "admin",
        auth_password: elements.setAuthPassword ? elements.setAuthPassword.value.trim() : "admin123",
        tts_provider: elements.setTtsProvider ? elements.setTtsProvider.value : "edge_tts",
        vivibe_api_key: elements.setVivibeApiKey ? elements.setVivibeApiKey.value.trim() : "",
        vivibe_voice_id: elements.setVivibeVoiceId ? elements.setVivibeVoiceId.value.trim() : ""
    };

    try {
        const resp = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (resp.ok) {
            alert("Đã lưu cấu hình API, ViVibe TTS & Bảo mật thành công!");
            elements.settingsModal.classList.add("hidden");
            await loadInitialConfig();
        }
    } catch (err) {
        alert("Lỗi lưu cấu hình: " + err.message);
    } finally {
        elements.btnSaveSettings.disabled = false;
        elements.btnSaveSettings.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Lưu Cấu Hình`;
    }
}

// Xử lý Upload File (.txt, .md)
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const resp = await fetch("/api/story/upload-file", {
            method: "POST",
            body: formData
        });
        const data = await resp.json();
        if (data.text) {
            elements.customStoryText.value = data.text;
            elements.cfgTitle.value = file.name.replace(/\.[^/.]+$/, "");
            alert(`Đã tải lên file '${file.name}' (${data.text.length} ký tự). Bấm 'Tự Động Phân Tách Cảnh' để xử lý!`);
        }
    } catch (err) {
        alert("Lỗi khi tải file: " + err.message);
    }
}

// Gọi API sinh kịch bản AI (hỗ trợ truyện dài 30-45p)
async function generateAiStory() {
    const genre = elements.aiGenre.value;
    const topic = elements.aiTopic.value.trim() || "Bí ẩn căn nhà gỗ cổ giữa rừng thông";
    const target_minutes = parseInt(elements.aiDuration.value) || 5;

    elements.btnGenerateStory.disabled = true;
    elements.btnGenerateStory.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang viết (${target_minutes}p)...`;

    try {
        const resp = await fetch("/api/story/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                genre: genre,
                topic: topic,
                target_minutes: target_minutes
            })
        });
        const data = await resp.json();
        if (data.scenes && data.scenes.length > 0) {
            currentScenes = data.scenes;
            renderScenesList();
            elements.cfgTitle.value = topic.length > 50 ? topic.substring(0, 50) : topic;
        }
    } catch (err) {
        alert("Lỗi khi tạo kịch bản AI: " + err.message);
    } finally {
        elements.btnGenerateStory.disabled = false;
        elements.btnGenerateStory.innerHTML = `<i class="fa-solid fa-sparkles"></i> AI Viết Truyện`;
    }
}

// Phân tách truyện dán vào
async function parseCustomStory() {
    const text = elements.customStoryText.value.trim();
    if (!text) {
        alert("Vui lòng dán nội dung truyện trước.");
        return;
    }

    elements.btnParseStory.disabled = true;
    elements.btnParseStory.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang phân tích...`;

    try {
        const resp = await fetch("/api/story/parse", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text,
                style: elements.cfgStyle.value
            })
        });
        const data = await resp.json();
        if (data.scenes) {
            currentScenes = data.scenes;
            renderScenesList();
        }
    } catch (err) {
        alert("Lỗi khi phân tích truyện: " + err.message);
    } finally {
        elements.btnParseStory.disabled = false;
        elements.btnParseStory.innerHTML = `<i class="fa-solid fa-scissors"></i> Tự Động Phân Tách Cảnh & Tạo Prompt Ảnh`;
    }
}

// Render danh sách các Scene ra HTML
function renderScenesList() {
    elements.sceneCounter.innerText = currentScenes.length;
    elements.scenesContainer.innerHTML = "";

    if (currentScenes.length === 0) {
        elements.scenesContainer.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #94a3b8; border: 1px dashed rgba(255,255,255,0.15); border-radius: 8px;">
                <i class="fa-solid fa-film" style="font-size: 2.2rem; margin-bottom: 12px; color: #38bdf8; display: block;"></i>
                <p style="margin: 0; font-size: 1rem; font-weight: 500;">Chưa có phân cảnh nào</p>
                <p style="margin: 6px 0 0; font-size: 0.85rem; color: #64748b;">
                    Hãy nhập ý tưởng và bấm <strong>"AI Viết Truyện"</strong> hoặc chuyển sang tab <strong>"Dán Truyện Tùy Chỉnh"</strong> để bắt đầu!
                </p>
            </div>
        `;
        return;
    }

    currentScenes.forEach((sc, index) => {
        const card = document.createElement("div");
        card.className = "scene-card";
        card.dataset.index = index;

        card.innerHTML = `
            <div class="scene-card-header">
                <div class="scene-badge">
                    <i class="fa-solid fa-clapperboard"></i> Cảnh ${index + 1}
                </div>
                <div class="scene-actions">
                    <button class="btn btn-sm btn-outline btn-preview-tts" data-index="${index}" title="Nghe thử giọng đọc cảnh này">
                        <i class="fa-solid fa-volume-high"></i> Nghe thử
                    </button>
                    <button class="btn btn-sm btn-outline btn-preview-img" data-index="${index}" title="Tạo thử ảnh AI cảnh này">
                        <i class="fa-solid fa-image"></i> Xem ảnh
                    </button>
                    <button class="btn btn-sm btn-secondary btn-delete-scene" data-index="${index}" title="Xóa cảnh này">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="scene-body">
                <div class="scene-inputs">
                    <textarea class="form-control scene-text-input" rows="2" placeholder="Lời dẫn / kể chuyện cho cảnh này...">${sc.text}</textarea>
                    <input type="text" class="form-control scene-prompt-input" value="${sc.image_prompt}" placeholder="Prompt mô tả bối cảnh hình ảnh (English)...">
                </div>
                <div class="scene-thumb-preview" id="thumb-preview-${index}" data-index="${index}" title="Bấm để tạo lại ảnh">
                    ${sc.preview_image_url ? `<img src="${sc.preview_image_url}" alt="Scene Preview">` : `
                        <div class="scene-thumb-placeholder">
                            <i class="fa-solid fa-wand-magic"></i>
                            <span>Bấm tạo ảnh</span>
                        </div>
                    `}
                </div>
            </div>
        `;

        // Event sửa text
        const textInput = card.querySelector(".scene-text-input");
        textInput.addEventListener("input", (e) => {
            currentScenes[index].text = e.target.value;
        });

        // Event sửa prompt
        const promptInput = card.querySelector(".scene-prompt-input");
        promptInput.addEventListener("input", (e) => {
            currentScenes[index].image_prompt = e.target.value;
        });

        // Event Nghe thử TTS
        const btnTts = card.querySelector(".btn-preview-tts");
        btnTts.addEventListener("click", () => previewSceneTTS(index, btnTts));

        // Event Tạo ảnh
        const btnImg = card.querySelector(".btn-preview-img");
        const thumbBox = card.querySelector(".scene-thumb-preview");
        btnImg.addEventListener("click", () => previewSceneImage(index, btnImg));
        thumbBox.addEventListener("click", () => previewSceneImage(index, btnImg));

        // Event Xóa cảnh
        const btnDel = card.querySelector(".btn-delete-scene");
        btnDel.addEventListener("click", () => deleteScene(index));

        elements.scenesContainer.appendChild(card);
    });
}

// Thêm cảnh mới
function addNewScene() {
    currentScenes.push({
        scene: currentScenes.length + 1,
        text: "Một diễn biến mới tiếp tục mở ra...",
        image_prompt: "cinematic mysterious landscape, atmospheric lighting, high detail"
    });
    renderScenesList();
}

// Xóa cảnh
function deleteScene(index) {
    if (currentScenes.length <= 1) {
        alert("Cần giữ lại ít nhất 1 cảnh.");
        return;
    }
    currentScenes.splice(index, 1);
    currentScenes.forEach((s, idx) => s.scene = idx + 1);
    renderScenesList();
}

// Nghe thử TTS từng cảnh
async function previewSceneTTS(index, button) {
    const sc = currentScenes[index];
    if (!sc.text.trim()) return;

    button.disabled = true;
    button.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang tải...`;

    try {
        const resp = await fetch("/api/preview/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: sc.text,
                voice: elements.cfgVoice.value,
                rate: elements.cfgRate.value,
                pitch: elements.cfgPitch.value
            })
        });
        const data = await resp.json();
        if (data.audio_url) {
            elements.ttsPreviewPlayer.src = data.audio_url + "?t=" + Date.now();
            elements.ttsPreviewPlayer.play();
        }
    } catch (err) {
        alert("Lỗi khi nghe thử TTS: " + err.message);
    } finally {
        button.disabled = false;
        button.innerHTML = `<i class="fa-solid fa-volume-high"></i> Nghe thử`;
    }
}

// Tạo & xem trước ảnh AI từng cảnh (DALL-E 3 hoặc Flux)
async function previewSceneImage(index, button) {
    const sc = currentScenes[index];
    const thumbBox = document.getElementById(`thumb-preview-${index}`);
    
    if (button) {
        button.disabled = true;
        button.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang tạo...`;
    }
    thumbBox.innerHTML = `<div class="scene-thumb-placeholder"><i class="fa-solid fa-spinner fa-spin"></i><span>Đang tạo ảnh AI...</span></div>`;

    try {
        const resp = await fetch("/api/preview/image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: sc.image_prompt,
                style: elements.cfgStyle.value,
                aspect_ratio: elements.cfgAspectRatio.value
            })
        });
        const data = await resp.json();
        if (data.image_url) {
            sc.preview_image_url = data.image_url + "?t=" + Date.now();
            thumbBox.innerHTML = `<img src="${sc.preview_image_url}" alt="Scene Preview">`;
        }
    } catch (err) {
        alert("Lỗi khi tạo ảnh AI: " + err.message);
        thumbBox.innerHTML = `<div class="scene-thumb-placeholder"><i class="fa-solid fa-triangle-exclamation"></i><span>Lỗi tạo ảnh</span></div>`;
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = `<i class="fa-solid fa-image"></i> Xem ảnh`;
        }
    }
}

// Bắt đầu Render Full Video (1-Click Pipeline)
async function startFullRender() {
    if (currentScenes.length === 0) {
        alert("Vui lòng tạo ít nhất 1 phân cảnh trước khi dựng video.");
        return;
    }

    const payload = {
        title: elements.cfgTitle.value.trim() || "Truyện Audio Đặc Sắc",
        channel_name: elements.cfgChannel.value.trim() || "@TruyenAudioAI",
        scenes: currentScenes,
        voice: elements.cfgVoice.value,
        rate: elements.cfgRate.value,
        pitch: elements.cfgPitch.value,
        style: elements.cfgStyle.value,
        aspect_ratio: elements.cfgAspectRatio.value,
        bgm_name: elements.cfgBgm.value || null,
        bgm_volume: parseFloat(elements.cfgBgmVolume.value) || 0.15,
        enable_waveform: elements.cfgEnableWaveform.checked
    };

    // Hiển thị Modal tiến trình
    elements.renderModal.classList.remove("hidden");
    elements.progressContainer.classList.remove("hidden");
    elements.resultContainer.classList.add("hidden");
    elements.modalTitleText.innerText = "Đang Dựng Video Truyện Audio...";
    updateProgress(5, "Đang khởi tạo quy trình kết xuất...");
    resetStepIndicators();

    try {
        const resp = await fetch("/api/render", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (data.job_id) {
            activeJobId = data.job_id;
            startPollingJob(activeJobId);
        }
    } catch (err) {
        alert("Lỗi khi gửi yêu cầu render: " + err.message);
        elements.renderModal.classList.add("hidden");
    }
}

// Theo dõi tiến trình render (Polling Job Status)
function startPollingJob(jobId) {
    if (pollTimer) clearInterval(pollTimer);

    pollTimer = setInterval(async () => {
        try {
            const resp = await fetch(`/api/jobs/${jobId}`);
            if (!resp.ok) return;

            const job = await resp.json();
            updateProgress(job.progress, job.step);
            highlightStep(job.progress);

            if (job.status === "completed") {
                clearInterval(pollTimer);
                showRenderResult(job);
            } else if (job.status === "error") {
                clearInterval(pollTimer);
                alert("Đã xảy ra lỗi trong quá trình render: " + (job.error || "Không xác định"));
                elements.modalTitleText.innerText = "Lỗi Khi Render Video!";
            }
        } catch (err) {
            console.error("Polling error:", err);
        }
    }, 1200);
}

function updateProgress(percent, stepText) {
    elements.progressPercent.innerText = `${percent}%`;
    elements.progressFill.style.width = `${percent}%`;
    elements.progressStep.innerText = stepText;
}

function resetStepIndicators() {
    const steps = ["step-tts", "step-img", "step-motion", "step-mix", "step-render"];
    steps.forEach(id => {
        const el = document.getElementById(id);
        el.className = "step-item";
    });
}

function highlightStep(percent) {
    const stepMap = [
        { id: "step-tts", min: 10, max: 35 },
        { id: "step-img", min: 35, max: 55 },
        { id: "step-motion", min: 55, max: 70 },
        { id: "step-mix", min: 70, max: 85 },
        { id: "step-render", min: 85, max: 100 }
    ];

    stepMap.forEach(s => {
        const el = document.getElementById(s.id);
        if (percent > s.max) {
            el.className = "step-item done";
        } else if (percent >= s.min && percent <= s.max) {
            el.className = "step-item active";
        } else {
            el.className = "step-item";
        }
    });
}

// Hiển thị kết quả hoàn thành
function showRenderResult(job) {
    elements.modalTitleText.innerText = "🎉 Video, Thumbnail AI & Mô Tả SEO Đã Sẵn Sàng!";
    elements.progressContainer.classList.add("hidden");
    elements.resultContainer.classList.remove("hidden");

    if (job.video_url) {
        elements.finalVideoPlayer.src = job.video_url + "?t=" + Date.now();
        elements.btnDownloadVideo.href = job.video_url;
    }
    if (job.thumbnail_url) {
        const thumbUrlWithTs = job.thumbnail_url + "?t=" + Date.now();
        elements.btnDownloadThumb.href = job.thumbnail_url;
        if (elements.finalThumbImg) {
            elements.finalThumbImg.src = thumbUrlWithTs;
        }
    }
    if (elements.finalDescText) {
        elements.finalDescText.value = job.description?.full_formatted_description || "";
    }
}

// Tạo Thumbnail AI Nhanh / Tạo Lại Độc Lập
async function quickGenerateAiThumbnail() {
    const title = elements.cfgTitle.value.trim() || "5 NĂM SAU, TÔI TRỞ VỀ THÂU TÓM CÔNG TY CỦA KẺ PHẢN BỘI";
    const style = elements.cfgStyle.value || "dark_mystery";
    const topic = elements.aiTopic.value.trim() || title;

    if (elements.btnRegenThumbAi) {
        elements.btnRegenThumbAi.disabled = true;
        elements.btnRegenThumbAi.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang vẽ lại Thumbnail AI...`;
    }
    if (elements.btnQuickThumb) {
        elements.btnQuickThumb.disabled = true;
        elements.btnQuickThumb.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang tạo AI Thumbnail...`;
    }

    try {
        const resp = await fetch("/api/thumbnail/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: title,
                genre: style,
                topic: topic,
                style: style,
                aspect_ratio: elements.cfgAspectRatio.value || "16:9"
            })
        });

        const data = await resp.json();
        if (data.status === "ok" && data.thumbnail_url) {
            const finalThumbUrl = data.thumbnail_url + "?t=" + Date.now();
            
            // Cập nhật modal
            elements.renderModal.classList.remove("hidden");
            elements.progressContainer.classList.add("hidden");
            elements.resultContainer.classList.remove("hidden");
            elements.modalTitleText.innerText = "🎨 Thumbnail AI Đã Được Tạo Thành Công!";
            
            if (elements.finalThumbImg) {
                elements.finalThumbImg.src = finalThumbUrl;
            }
            if (elements.btnDownloadThumb) {
                elements.btnDownloadThumb.href = data.thumbnail_url;
            }
        } else {
            alert("Không thể tạo Thumbnail AI. Vui lòng kiểm tra lại API Settings.");
        }
    } catch (err) {
        alert("Lỗi khi tạo Thumbnail AI: " + err.message);
    } finally {
        if (elements.btnRegenThumbAi) {
            elements.btnRegenThumbAi.disabled = false;
            elements.btnRegenThumbAi.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Tạo Lại Thumbnail AI Khác`;
        }
        if (elements.btnQuickThumb) {
            elements.btnQuickThumb.disabled = false;
            elements.btnQuickThumb.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> 🎨 Tạo Thử Thumbnail AI`;
        }
    }
}

// Soạn Thảo Mô Tả Video & SEO YouTube
async function generateDescriptionAction() {
    const title = elements.cfgTitle.value.trim() || "5 NĂM SAU, TÔI TRỞ VỀ THÂU TÓM CÔNG TY CỦA KẺ PHẢN BỘI";
    const style = elements.cfgStyle.value || "dark_mystery";
    const topic = elements.aiTopic.value.trim() || title;

    if (elements.btnQuickDesc) {
        elements.btnQuickDesc.disabled = true;
        elements.btnQuickDesc.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang soạn mô tả...`;
    }
    if (elements.btnRegenDesc) {
        elements.btnRegenDesc.disabled = true;
        elements.btnRegenDesc.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang viết lại...`;
    }

    try {
        const resp = await fetch("/api/story/description", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: title,
                genre: style,
                topic: topic,
                scenes: currentScenes
            })
        });

        const data = await resp.json();
        if (data.status === "ok" && data.description) {
            elements.renderModal.classList.remove("hidden");
            elements.progressContainer.classList.add("hidden");
            elements.resultContainer.classList.remove("hidden");
            elements.modalTitleText.innerText = "📝 Mô Tả Video YouTube & SEO Đã Sẵn Sàng!";

            if (elements.finalDescText) {
                elements.finalDescText.value = data.description.full_formatted_description;
            }
        }
    } catch (err) {
        alert("Lỗi khi soạn thảo mô tả video: " + err.message);
    } finally {
        if (elements.btnQuickDesc) {
            elements.btnQuickDesc.disabled = false;
            elements.btnQuickDesc.innerHTML = `<i class="fa-solid fa-file-lines"></i> 📝 Soạn Thảo Mô Tả SEO`;
        }
        if (elements.btnRegenDesc) {
            elements.btnRegenDesc.disabled = false;
            elements.btnRegenDesc.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Viết Lại Mô Tả`;
        }
    }
}

// Sao Chép Mô Tả Vào Clipboard (1-Click)
async function copyDescriptionToClipboard() {
    if (!elements.finalDescText || !elements.finalDescText.value.trim()) {
        alert("Chưa có nội dung mô tả để sao chép.");
        return;
    }

    try {
        await navigator.clipboard.writeText(elements.finalDescText.value);
        const originalText = elements.btnCopyDesc.innerHTML;
        elements.btnCopyDesc.innerHTML = `<i class="fa-solid fa-check"></i> Đã Sao Chép!`;
        elements.btnCopyDesc.classList.remove("btn-success");
        elements.btnCopyDesc.classList.add("btn-primary");
        
        setTimeout(() => {
            elements.btnCopyDesc.innerHTML = originalText;
            elements.btnCopyDesc.classList.remove("btn-primary");
            elements.btnCopyDesc.classList.add("btn-success");
        }, 2000);
    } catch (err) {
        elements.finalDescText.select();
        document.execCommand("copy");
        alert("Đã sao chép nội dung mô tả vào Clipboard!");
    }
}

// Mở thư mục chứa video trên Windows
async function openOutputFolder() {
    try {
        await fetch("/api/open-folder", { method: "POST" });
    } catch (err) {
        console.warn("Không thể mở thư mục:", err);
    }
}

// ==========================================
// ⏰ LÊN LỊCH TỰ ĐỘNG & AUTO YOUTUBE (SCHEDULER)
// ==========================================

// Khởi tạo sự kiện cho Lên Lịch & YouTube
function initSchedulerAndYouTube() {
    // 1. Chuyển đổi Tab chính (Studio <-> Lên Lịch)
    const btnStudio = document.getElementById("nav-btn-studio");
    const btnScheduler = document.getElementById("nav-btn-scheduler");
    const viewStudio = document.getElementById("view-studio");
    const viewScheduler = document.getElementById("view-scheduler");

    if (btnStudio && btnScheduler) {
        btnStudio.addEventListener("click", () => {
            btnStudio.classList.add("active");
            btnScheduler.classList.remove("active");
            viewStudio.classList.remove("hidden");
            viewScheduler.classList.add("hidden");
        });

        btnScheduler.addEventListener("click", () => {
            btnScheduler.classList.add("active");
            btnStudio.classList.remove("active");
            viewScheduler.classList.remove("hidden");
            viewStudio.classList.add("hidden");
            loadSchedulerConfig();
            checkYouTubeStatus();
            loadSchedulerHistory();
        });
    }

    // 2. Chế độ Hàng đợi Ý tưởng (AI Tự Nghĩ vs Hàng Đợi)
    const tabModeAi = document.getElementById("tab-mode-ai");
    const tabModeQueue = document.getElementById("tab-mode-queue");
    if (tabModeAi && tabModeQueue) {
        tabModeAi.addEventListener("click", () => {
            tabModeAi.classList.add("active");
            tabModeQueue.classList.remove("active");
        });
        tabModeQueue.addEventListener("click", () => {
            tabModeQueue.classList.add("active");
            tabModeAi.classList.remove("active");
        });
    }

    // 3. YouTube Modal & Actions
    const ytModal = document.getElementById("youtube-modal");
    const btnYtConnect = document.getElementById("btn-yt-connect");
    const btnCloseYtModal = document.getElementById("btn-close-yt-modal");
    const btnYtGetAuthUrl = document.getElementById("btn-yt-get-auth-url");
    const btnYtConfirmCode = document.getElementById("btn-yt-confirm-code");
    const btnYtDisconnect = document.getElementById("btn-yt-disconnect");

    if (btnYtConnect) {
        btnYtConnect.addEventListener("click", async () => {
            ytModal.classList.remove("hidden");
            try {
                const resp = await fetch("/api/youtube/credentials");
                const creds = await resp.json();
                if (creds.client_id) {
                    document.getElementById("yt-client-id").value = creds.client_id;
                }
            } catch (e) {}
        });
    }

    if (btnCloseYtModal) {
        btnCloseYtModal.addEventListener("click", () => {
            ytModal.classList.add("hidden");
        });
    }

    if (btnYtGetAuthUrl) {
        btnYtGetAuthUrl.addEventListener("click", async () => {
            const clientId = document.getElementById("yt-client-id").value.trim();
            const clientSecret = document.getElementById("yt-client-secret").value.trim();

            if (!clientId) {
                alert("Vui lòng nhập Google Client ID.");
                return;
            }

            try {
                if (clientSecret) {
                    await fetch("/api/youtube/credentials", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ client_id: clientId, client_secret: clientSecret })
                    });
                }

                const resp = await fetch("/api/youtube/auth-url");
                const data = await resp.json();
                if (data.auth_url) {
                    const authWin = window.open(data.auth_url, "_blank", "width=600,height=700");
                    
                    // Tự động kiểm tra trạng thái liên kết mỗi 2 giây
                    const checkInterval = setInterval(async () => {
                        try {
                            const statusResp = await fetch("/api/youtube/status");
                            const statusData = await statusResp.json();
                            if (statusData.connected) {
                                clearInterval(checkInterval);
                                ytModal.classList.add("hidden");
                                checkYouTubeStatus();
                            }
                        } catch (e) {}
                    }, 2000);

                    setTimeout(() => clearInterval(checkInterval), 180000); // Dừng sau 3 phút
                } else {
                    alert("Không thể lấy URL ủy quyền. Vui lòng kiểm tra lại Client ID.");
                }
            } catch (err) {
                alert("Lỗi khi mở trang Google OAuth: " + err.message);
            }
        });
    }

    if (btnYtConfirmCode) {
        btnYtConfirmCode.addEventListener("click", async () => {
            const code = document.getElementById("yt-auth-code").value.trim();
            if (!code) {
                alert("Vui lòng dán Authorization Code nhận được từ Google.");
                return;
            }

            btnYtConfirmCode.disabled = true;
            btnYtConfirmCode.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang xác thực...`;

            try {
                const resp = await fetch("/api/youtube/auth-code", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ auth_code: code })
                });
                const data = await resp.json();
                if (data.status === "ok") {
                    alert("Liên kết Kênh YouTube thành công!");
                    ytModal.classList.add("hidden");
                    checkYouTubeStatus();
                } else {
                    alert("Lỗi xác thực: " + (data.detail || "Không thành công"));
                }
            } catch (err) {
                alert("Lỗi kết nối: " + err.message);
            } finally {
                btnYtConfirmCode.disabled = false;
                btnYtConfirmCode.innerHTML = `<i class="fa-solid fa-check"></i> 2. Xác Nhận & Kết Nối Kênh`;
            }
        });
    }

    if (btnYtDisconnect) {
        btnYtDisconnect.addEventListener("click", async () => {
            if (confirm("Anh có chắc muốn hủy liên kết kênh YouTube hiện tại?")) {
                await fetch("/api/youtube/disconnect", { method: "POST" });
                checkYouTubeStatus();
            }
        });
    }

    // 4. Lưu Cấu Hình Lên Lịch
    const btnSaveSched = document.getElementById("btn-save-scheduler");
    if (btnSaveSched) {
        btnSaveSched.addEventListener("click", saveSchedulerConfig);
    }

    // 5. Chạy Thử Ngay (Trigger Now)
    const btnTriggerNow = document.getElementById("btn-trigger-sched-now");
    if (btnTriggerNow) {
        btnTriggerNow.addEventListener("click", triggerSchedulerNow);
    }

    // 6. Làm mới Lịch sử
    const btnRefreshHistory = document.getElementById("btn-refresh-history");
    if (btnRefreshHistory) {
        btnRefreshHistory.addEventListener("click", loadSchedulerHistory);
    }
}

// Kiểm tra trạng thái Kênh YouTube
async function checkYouTubeStatus() {
    try {
        const resp = await fetch("/api/youtube/status");
        const data = await resp.json();

        const channelCard = document.getElementById("yt-channel-card");
        const channelName = document.getElementById("yt-channel-name");
        const channelSub = document.getElementById("yt-channel-sub");
        const channelAvatar = document.getElementById("yt-channel-avatar");
        const btnConnect = document.getElementById("btn-yt-connect");
        const btnDisconnect = document.getElementById("btn-yt-disconnect");
        const connectBtnText = document.getElementById("yt-connect-btn-text");

        if (data.connected) {
            channelName.innerText = data.title || "Kênh YouTube Đã Kết Nối";
            channelSub.innerText = `${data.subscriber_count || 0} người đăng ký • ${data.video_count || 0} video`;
            if (data.avatar_url) channelAvatar.src = data.avatar_url;
            connectBtnText.innerText = "Đổi Tài Khoản Khác";
            btnDisconnect.classList.remove("hidden");
        } else {
            channelName.innerText = "Chưa Kết Nối Kênh YouTube";
            channelSub.innerText = "Đăng nhập tài khoản Google để tự động đăng tải Video & Thumbnail AI";
            channelAvatar.src = "https://www.youtube.com/s/desktop/d743f786/img/favicon_144x144.png";
            connectBtnText.innerText = "🔗 Liên Kết Kênh YouTube";
            btnDisconnect.classList.add("hidden");
        }
    } catch (e) {
        console.warn("Lỗi khi kiểm tra kênh YouTube:", e);
    }
}

// Tải Cấu Hình Lên Lịch
async function loadSchedulerConfig() {
    try {
        const resp = await fetch("/api/scheduler/config");
        const config = await resp.json();

        document.getElementById("sched-enable").checked = !!config.enabled;
        document.getElementById("sched-times").value = (config.scheduled_times || ["08:00", "12:30", "19:30"]).join(", ");
        document.getElementById("sched-genre").value = config.genre || "dark_mystery";
        document.getElementById("sched-duration").value = config.duration || 5;
        document.getElementById("sched-voice").value = config.voice || "vi-VN-HoaiMyNeural";
        document.getElementById("sched-auto-yt").value = config.auto_upload_youtube ? "true" : "false";
        document.getElementById("sched-privacy").value = config.privacy_status || "unlisted";

        const tabModeAi = document.getElementById("tab-mode-ai");
        const tabModeQueue = document.getElementById("tab-mode-queue");
        if (config.mode === "queue") {
            tabModeQueue.classList.add("active");
            tabModeAi.classList.remove("active");
        } else {
            tabModeAi.classList.add("active");
            tabModeQueue.classList.remove("active");
        }

        if (config.topic_queue && Array.isArray(config.topic_queue)) {
            document.getElementById("sched-topic-queue").value = config.topic_queue.join("\n");
        }

        // Tải danh sách BGM vào select
        const bgmSelect = document.getElementById("sched-bgm");
        if (bgmSelect && bgmSelect.options.length <= 1) {
            const cfgResp = await fetch("/api/config");
            const appCfg = await cfgResp.json();
            if (appCfg.bgm_list) {
                appCfg.bgm_list.forEach(bgm => {
                    const opt = document.createElement("option");
                    opt.value = bgm;
                    opt.innerText = bgm.replace(".mp3", "").replace("_", " ").toUpperCase();
                    bgmSelect.appendChild(opt);
                });
            }
        }
    } catch (e) {
        console.warn("Lỗi tải cấu hình Lên lịch:", e);
    }
}

// Lưu Cấu Hình Lên Lịch
async function saveSchedulerConfig() {
    const rawTimes = document.getElementById("sched-times").value;
    const times = rawTimes.split(",").map(t => t.trim()).filter(t => t.length > 0);
    const rawQueue = document.getElementById("sched-topic-queue").value;
    const topicQueue = rawQueue.split("\n").map(q => q.trim()).filter(q => q.length > 0);
    const mode = document.getElementById("tab-mode-queue").classList.contains("active") ? "queue" : "ai_auto";

    const payload = {
        enabled: document.getElementById("sched-enable").checked,
        scheduled_times: times,
        mode: mode,
        topic_queue: topicQueue,
        genre: document.getElementById("sched-genre").value,
        duration: parseInt(document.getElementById("sched-duration").value) || 5,
        voice: document.getElementById("sched-voice").value,
        rate: "+0%",
        pitch: "+0Hz",
        bgm_name: document.getElementById("sched-bgm").value,
        bgm_volume: 0.15,
        aspect_ratio: "16:9",
        enable_waveform: true,
        auto_upload_youtube: document.getElementById("sched-auto-yt").value === "true",
        privacy_status: document.getElementById("sched-privacy").value
    };

    try {
        const resp = await fetch("/api/scheduler/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (data.status === "ok") {
            alert("Đã lưu cấu hình Lên lịch Auto-Pilot thành công!");
        }
    } catch (err) {
        alert("Lỗi khi lưu cấu hình: " + err.message);
    }
}

// Chạy Thử Ngay (Trigger Now)
async function triggerSchedulerNow() {
    if (!confirm("Bắt đầu chạy ngay 1 quy trình sản xuất trọn gói theo cấu hình hiện tại?")) return;

    const btn = document.getElementById("btn-trigger-sched-now");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang chạy...`;

    try {
        const resp = await fetch("/api/scheduler/trigger-now", { method: "POST" });
        const data = await resp.json();
        if (data.status === "started") {
            alert("Đã khởi chạy quy trình Auto-Pilot ngầm! Anh có thể theo dõi trong Bảng Nhật Ký Lịch Sử.");
            setTimeout(loadSchedulerHistory, 3000);
        } else {
            alert("Thông báo: " + (data.detail || data.message));
        }
    } catch (err) {
        alert("Lỗi khi kích hoạt: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-bolt"></i> ⚡ Chạy Thử Ngay`;
    }
}

// Tải Nhật Ký & Lịch Sử Upload
async function loadSchedulerHistory() {
    try {
        const resp = await fetch("/api/scheduler/history");
        const history = await resp.json();
        const tbody = document.getElementById("sched-history-tbody");
        if (!tbody) return;

        if (!history || history.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-sub); padding: 24px;">Chưa có lịch sử sản xuất. Hãy lưu cấu hình hoặc bấm "Chạy Thử Ngay".</td></tr>`;
            return;
        }

        tbody.innerHTML = history.map(item => {
            let statusBadge = `<span class="badge-tag badge-warning"><i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý</span>`;
            if (item.status === "completed") {
                statusBadge = `<span class="badge-tag badge-success"><i class="fa-solid fa-check"></i> Hoàn thành</span>`;
            } else if (item.status === "error") {
                statusBadge = `<span class="badge-tag badge-danger" title="${item.error || ''}"><i class="fa-solid fa-triangle-exclamation"></i> Lỗi</span>`;
            }

            let ytCell = `<span style="color: var(--text-sub); font-size: 0.8rem;">Chưa bật upload</span>`;
            if (item.youtube_url) {
                ytCell = `<a href="${item.youtube_url}" target="_blank" class="btn btn-sm btn-outline" style="color: #ef4444; border-color: #ef4444; padding: 4px 10px; font-size: 0.8rem;">
                    <i class="fa-brands fa-youtube"></i> Xem Trên YouTube
                </a>`;
            } else if (item.youtube_status === "failed") {
                ytCell = `<span class="badge-tag badge-danger" title="${item.error || ''}">Lỗi Upload</span>`;
            }

            return `
                <tr>
                    <td style="white-space: nowrap; font-size: 0.8rem; color: var(--text-muted);">${item.created_at || "Vừa xong"}</td>
                    <td style="font-weight: 600;">${item.title || "Truyện Audio Tự Động"}</td>
                    <td><span class="badge-tag badge-info">${item.genre || "dark_mystery"}</span></td>
                    <td>${statusBadge}</td>
                    <td>${ytCell}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.warn("Lỗi tải lịch sử:", e);
    }
}

// Khởi tạo Lên lịch & YouTube khi trang tải xong
document.addEventListener("DOMContentLoaded", () => {
    initSchedulerAndYouTube();
});

