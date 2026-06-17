const sampleText = `黄昏时分，破败的古庙里只剩摇晃的烛光。
苏晚站在佛像前，月白色襦裙被夜风吹起，她握紧玉佩，指节发白，眼底压着隐忍的愤怒。
萧寒从阴影中走出，银色长发掠过肩头，低声说：“把玉佩交出来。”

下一刻，庙门被狂风撞开。苏晚猛然转身，将玉佩藏进袖中，萧寒抬手拦住她的去路。`;

const platformNames = {
  jimeng: "即梦",
  kling: "可灵",
  runway: "Runway",
  liblibai: "LiblibAI",
  oiioii: "OiiOii",
};

let currentResult = null;
let activePlatform = "jimeng";

const novelInput = document.querySelector("#novelInput");
const generateBtn = document.querySelector("#generateBtn");
const regenerateBtn = document.querySelector("#regenerateBtn");
const loadSampleBtn = document.querySelector("#loadSampleBtn");
const copyJsonBtn = document.querySelector("#copyJsonBtn");
const timeline = document.querySelector("#timeline");
const platformTabs = document.querySelector("#platformTabs");
const promptCards = document.querySelector("#promptCards");

novelInput.value = sampleText;
generateBtn.addEventListener("click", generate);
regenerateBtn.addEventListener("click", generate);
loadSampleBtn.addEventListener("click", () => {
  novelInput.value = sampleText;
});
copyJsonBtn.addEventListener("click", () => {
  if (currentResult) copyText(JSON.stringify(currentResult, null, 2));
});

async function generate() {
  const platforms = [...document.querySelectorAll("input[name='platform']:checked")].map((item) => item.value);
  if (!platforms.length) return renderError("至少选择一个平台。");
  generateBtn.disabled = true;
  generateBtn.textContent = "生成中";
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: novelInput.value, platforms }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "生成失败");
    }
    currentResult = await response.json();
    activePlatform = platforms[0];
    renderTimeline(currentResult.storyboard || []);
    renderTabs(Object.keys(currentResult.platform_prompts || {}));
    renderPromptCards();
  } catch (error) {
    renderError(error.message);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "生成";
  }
}

function renderTimeline(storyboard) {
  if (!storyboard.length) {
    timeline.className = "timeline empty-state";
    timeline.textContent = "暂无分镜";
    return;
  }
  timeline.className = "timeline";
  timeline.innerHTML = storyboard
    .map(
      (shot) => `
        <article class="shot">
          <div class="shot-header">
            <span class="shot-number">镜头 ${escapeHtml(shot.shot_no)}</span>
            <span class="shot-duration">${escapeHtml(shot.duration)}</span>
          </div>
          <p>${escapeHtml(shot.screen_content)}</p>
          <p>${escapeHtml(shot.transition)} · ${escapeHtml(shot.sound)}</p>
          <p>${escapeHtml(shot.subtitle)}</p>
        </article>
      `,
    )
    .join("");
}

function renderTabs(platforms) {
  platformTabs.innerHTML = platforms
    .map(
      (platform) => `
        <button class="tab ${platform === activePlatform ? "active" : ""}" data-platform="${platform}">
          ${platformNames[platform] || platform}
        </button>
      `,
    )
    .join("");
  platformTabs.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      activePlatform = button.dataset.platform;
      renderTabs(platforms);
      renderPromptCards();
    });
  });
}

function renderPromptCards() {
  const prompts = currentResult?.platform_prompts?.[activePlatform] || [];
  if (!prompts.length) {
    promptCards.className = "prompt-list empty-state";
    promptCards.textContent = "暂无 Prompt";
    return;
  }
  promptCards.className = "prompt-list";
  promptCards.innerHTML = prompts
    .map(
      (prompt, index) => `
        <article class="prompt-card">
          <div class="prompt-card-header">
            <h3>镜头 ${escapeHtml(prompt.scene_id || String(index + 1))}</h3>
            <button data-copy="${index}">复制</button>
          </div>
          <pre>${escapeHtml(prompt.positive_prompt)}</pre>
          <div class="meta">
            <span>负面：${escapeHtml(prompt.negative_prompt)}</span>
            <span>参数：${escapeHtml(prompt.parameter_suggestion)}</span>
            <span>${escapeHtml(prompt.aspect_ratio)} · ${escapeHtml(prompt.duration)}</span>
          </div>
        </article>
      `,
    )
    .join("");
  promptCards.querySelectorAll("button[data-copy]").forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = prompts[Number(button.dataset.copy)];
      const text = [
        prompt.positive_prompt,
        "",
        "Negative:",
        prompt.negative_prompt,
        "",
        "Parameters:",
        prompt.parameter_suggestion,
      ].join("\n");
      copyText(text);
    });
  });
}

function renderError(message) {
  promptCards.className = "prompt-list empty-state error";
  promptCards.textContent = message;
}

async function copyText(text) {
  await navigator.clipboard.writeText(text);
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
