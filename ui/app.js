(() => {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const chat = $("#chat");
  const input = $("#input");
  const sendBtn = $("#send");
  const stopBtn = $("#stop");
  const notice = $("#notice");
  const historyPanel = $("#historyPanel");
  const historyBackdrop = $("#historyBackdrop");
  const historyList = $("#historyList");
  const modeButtons = [...document.querySelectorAll(".mode")];
  const calibrationPanel = $("#calibrationPanel");
  const calibrationBackdrop = $("#calibrationBackdrop");
  const maintenancePanel = $("#maintenancePanel");
  const maintenanceBackdrop = $("#maintenanceBackdrop");
  const fileInput = $("#fileInput");
  const fileList = $("#fileList");
  const attachBtn = $("#attachBtn");
  const composer = $("#composer");

  let messages = [];
  let generating = false;
  let stopRequested = false;   // interrompe o auto-continuar (botão Parar)
  const AUTO_CONTINUE_MAX = 5; // continuações automáticas por resposta
  let currentStatus = null;
  let currentSessionId = null;
  let currentSessionTitle = "Nova conversa";
  let calibrationTimer = null;
  let calibrationMandatory = false;
  let attachedFiles = [];
  let uploadingFile = false;

  function showNotice(text) {
    notice.textContent = text || "";
    notice.classList.toggle("hidden", !text);
  }

  function setGenerating(value) {
    generating = value;
    sendBtn.disabled = value;
    stopBtn.classList.toggle("hidden", !value);
    modeButtons.forEach(b => b.disabled = value);
  }

  function renderMessages() {
    chat.innerHTML = "";
    if (!messages.length) {
      chat.innerHTML = `
        <div class="welcome">
          <h1>Como posso ajudar?</h1>
          <p>IA local. Conversas salvas somente neste dispositivo.</p>
        </div>`;
      return;
    }
    for (const msg of messages) addMessage(msg.role, msg.content, false);
    chat.scrollTop = chat.scrollHeight;
    if (typeof updateBaixar === "function") updateBaixar();
  }

  function addMessage(role, content = "", scroll = true) {
    const welcome = chat.querySelector(".welcome");
    if (welcome) welcome.remove();

    const wrap = document.createElement("div");
    wrap.className = `message ${role}`;

    const label = document.createElement("div");
    label.className = "role";
    label.textContent = role === "user" ? "VOCÊ" : "NÚCLEO";

    const body = document.createElement("div");
    body.className = "content";
    body.textContent = content;

    wrap.append(label, body);
    chat.appendChild(wrap);
    if (scroll) chat.scrollTop = chat.scrollHeight;
    return body;
  }

  function setModeButton(requested) {
    modeButtons.forEach(b => b.classList.toggle("active", b.dataset.mode === requested));
  }

  function formatStatus(s) {
    const ready = s.status === "ready";
    $("#readyDot").classList.toggle("ready", ready);
    const labels = {
      needs_calibration: "CALIBRAÇÃO NECESSÁRIA",
      calibrating: "CALIBRANDO",
      starting: "INICIANDO",
      stopped: "PARADO",
      error: "ERRO"
    };
    $("#readyText").textContent = ready ? "IA PRONTA" : (labels[s.status] || s.status.toUpperCase());
    setModeButton(s.requested_mode || "auto");
    sendBtn.disabled = !ready || generating;
    input.disabled = !ready;
    modeButtons.forEach(b => b.disabled = !ready || generating);

    let modeText = "";
    if (s.requested_mode === "auto" && s.active_mode_name) {
      modeText = `AUTO selecionou ${s.active_mode_name}`;
    } else if (s.active_mode_name) {
      modeText = s.active_mode_name;
    }
    $("#modeHint").textContent = modeText;

    const tps = s.last_tps || s.reference_tps;
    const tpsLabel = tps ? ` • ${tps} t/s${s.last_tps ? "" : " ref."}` : "";
    const backendPolicy = s.backend_policy === "cpu_forced" ? " • CPU forçada" : "";
    $("#engineInfo").textContent =
      `${s.model || "Sem modelo"} • ${(s.backend || "—").toUpperCase()}${backendPolicy}${tpsLabel}`;

    $("#dModel").textContent = s.model || "—";
    $("#dBackend").textContent = (s.backend || "—").toUpperCase();
    $("#dThreads").textContent = s.threads ?? "—";
    $("#dLayers").textContent = s.gpu_layers ?? "—";
    $("#dContext").textContent = s.context_size ?? "—";
    $("#dMachine").textContent = s.machine_id || "—";
    $("#dVram").textContent = s.vram_total_mib != null
      ? `${Math.round(s.vram_used_mib)} / ${Math.round(s.vram_total_mib)} MiB`
      : "—";

    if (s.error && s.status !== "needs_calibration") showNotice(s.error);
    currentStatus = s;

    if (!s.profile_available && s.status === "needs_calibration") {
      calibrationMandatory = true;
      openCalibration(true);
    }

  }

  async function refreshStatus() {
    try {
      const r = await fetch("/api/status", {cache: "no-store"});
      const j = await r.json();
      if (j.ok) formatStatus(j.data);
    } catch (_) {
      showNotice("A interface perdeu comunicação com o NÚCLEO.");
    }
  }


  function formatBytes(bytes) {
    const n = Number(bytes || 0);
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  }

  function fileMetaText(item) {
    const s = item.summary || {};
    if (s.type === "xlsx") {
      return `${s.sheet_count || 0} abas • ${s.row_count || 0} linhas • ${s.formula_count || 0} fórmulas`;
    }
    if (s.type === "pdf") {
      const pc = s.page_count || 0, wt = s.pages_with_text || 0;
      return `PDF • ${pc} pág.${wt < pc ? ` (${wt} c/ texto)` : ""} • ${s.word_count || 0} palavras`;
    }
    if (s.type === "docx") {
      return `DOCX • ${s.paragraph_count || 0} parágrafos • ${s.table_count || 0} tabelas • ${s.word_count || 0} palavras`;
    }
    if (s.row_count != null) {
      return `${s.row_count} linhas • ${s.column_count || 0} colunas`;
    }
    if (s.word_count != null) return `${s.word_count} palavras`;
    if (s.json_shape) return `JSON ${s.json_shape}`;
    return formatBytes(item.size);
  }

  function renderFiles() {
    fileList.innerHTML = "";
    fileList.classList.toggle("hidden", !attachedFiles.length);
    for (const item of attachedFiles) {
      const chip = document.createElement("div");
      chip.className = "fileChip";

      const name = document.createElement("span");
      name.className = "fileChipName";
      name.textContent = item.name;
      name.title = item.name;

      const meta = document.createElement("span");
      meta.className = "fileChipMeta";
      meta.textContent = fileMetaText(item);

      const remove = document.createElement("button");
      remove.className = "fileChipRemove";
      remove.textContent = "×";
      remove.title = "Remover arquivo";
      remove.addEventListener("click", () => removeFile(item.id));

      chip.append(name, meta, remove);
      fileList.appendChild(chip);
    }
  }

  async function refreshFiles() {
    if (!currentSessionId) {
      attachedFiles = [];
      renderFiles();
      return;
    }
    try {
      const r = await fetch(`/api/files/${currentSessionId}`, {cache: "no-store"});
      const j = await r.json();
      if (!j.ok) throw new Error(j.error?.message || "Falha ao carregar arquivos.");
      attachedFiles = Array.isArray(j.data) ? j.data : [];
      renderFiles();
    } catch (e) {
      showNotice(e.message);
    }
  }

  async function uploadOne(file) {
    if (!currentSessionId) await createSession();
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      throw new Error(`${file.name}: excede 50 MB.`);
    }
    const allowed = [".xlsx", ".csv", ".txt", ".md", ".json", ".pdf", ".docx"];
    const lower = file.name.toLowerCase();
    if (lower.endsWith(".doc") && !lower.endsWith(".docx")) {
      throw new Error(`${file.name}: .doc antigo não suportado — salve como .docx e reenvie.`);
    }
    if (!allowed.some(ext => lower.endsWith(ext))) {
      throw new Error(`${file.name}: formato não suportado.`);
    }

    const url = `/api/files/${currentSessionId}?name=${encodeURIComponent(file.name)}`;
    const r = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/octet-stream"},
      body: file
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error?.message || `Falha ao anexar ${file.name}.`);
    attachedFiles.push(j.data);
    renderFiles();
  }

  async function uploadFiles(fileCollection) {
    if (uploadingFile) return;
    const files = [...(fileCollection || [])];
    if (!files.length) return;
    uploadingFile = true;
    attachBtn.disabled = true;
    showNotice("Analisando arquivo localmente...");
    try {
      for (const file of files.slice(0, 5)) {
        await uploadOne(file);
      }
      showNotice("");
      input.focus();
    } catch (e) {
      showNotice(e.message);
    } finally {
      uploadingFile = false;
      attachBtn.disabled = false;
      fileInput.value = "";
    }
  }

  async function removeFile(fileId) {
    if (!currentSessionId || generating || uploadingFile) return;
    const r = await fetch(`/api/files/${currentSessionId}/${fileId}`, {method: "DELETE"});
    const j = await r.json();
    if (!j.ok) {
      showNotice(j.error?.message || "Falha ao remover arquivo.");
      return;
    }
    attachedFiles = attachedFiles.filter(x => x.id !== fileId);
    renderFiles();
  }

  async function createSession() {
    const r = await fetch("/api/session/new", {method: "POST"});
    const j = await r.json();
    if (!j.ok) throw new Error(j.error?.message || "Falha ao criar conversa.");
    currentSessionId = j.data.id;
    currentSessionTitle = j.data.title || "Nova conversa";
    messages = [];
    attachedFiles = [];
    renderMessages();
    renderFiles();
    return j.data;
  }

  async function saveSession() {
    if (!currentSessionId) await createSession();
    const r = await fetch(`/api/session/${currentSessionId}/save`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        messages,
        mode: currentStatus?.requested_mode || "auto"
      })
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error?.message || "Falha ao salvar conversa.");
    currentSessionTitle = j.data.title || currentSessionTitle;
    return j.data;
  }

  async function loadSession(sessionId) {
    if (generating) return;
    const r = await fetch(`/api/session/${sessionId}`, {cache: "no-store"});
    const j = await r.json();
    if (!j.ok) throw new Error(j.error?.message || "Conversa não encontrada.");
    currentSessionId = j.data.id;
    currentSessionTitle = j.data.title || "Nova conversa";
    messages = Array.isArray(j.data.messages) ? j.data.messages : [];
    renderMessages();
    await refreshFiles();
    showNotice("");
    closeHistory();
    input.focus();
  }

  function prettyDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit",
      hour: "2-digit", minute: "2-digit"
    });
  }

  async function refreshHistory() {
    historyList.innerHTML = '<p class="historyEmpty">Carregando...</p>';
    try {
      const r = await fetch("/api/sessions?limit=20", {cache: "no-store"});
      const j = await r.json();
      if (!j.ok) throw new Error(j.error?.message || "Falha ao carregar histórico.");

      const items = j.data || [];
      historyList.innerHTML = "";
      if (!items.length) {
        historyList.innerHTML = '<p class="historyEmpty">Nenhuma conversa salva.</p>';
        return;
      }

      for (const item of items) {
        const row = document.createElement("div");
        row.className = "historyItem" + (item.id === currentSessionId ? " active" : "");
        row.dataset.id = item.id;

        const title = document.createElement("div");
        title.className = "historyTitle";
        title.textContent = item.title || "Nova conversa";

        const meta = document.createElement("div");
        meta.className = "historyMeta";
        meta.textContent = `${prettyDate(item.updated_at)} • ${item.message_count} msgs`;

        const del = document.createElement("button");
        del.className = "historyDelete";
        del.title = "Excluir conversa";
        del.textContent = "×";
        del.addEventListener("click", async (e) => {
          e.stopPropagation();
          if (!confirm(`Excluir "${item.title || "Nova conversa"}"?`)) return;
          const rr = await fetch(`/api/session/${item.id}`, {method: "DELETE"});
          const jj = await rr.json();
          if (!jj.ok) {
            showNotice(jj.error?.message || "Falha ao excluir conversa.");
            return;
          }
          if (item.id === currentSessionId) await newConversation();
          await refreshHistory();
        });

        row.append(title, meta, del);
        row.addEventListener("click", () => loadSession(item.id).catch(e => showNotice(e.message)));
        historyList.appendChild(row);
      }
    } catch (e) {
      historyList.innerHTML = '<p class="historyEmpty">Não foi possível carregar o histórico.</p>';
      showNotice(e.message);
    }
  }

  function openHistory() {
    historyPanel.classList.remove("hidden");
    historyBackdrop.classList.remove("hidden");
    refreshHistory();
  }

  function closeHistory() {
    historyPanel.classList.add("hidden");
    historyBackdrop.classList.add("hidden");
  }

  async function newConversation() {
    if (generating) return;
    await createSession();
    showNotice("");
    closeHistory();
    input.focus();
  }

  async function restoreLastSession() {
    try {
      const r = await fetch("/api/session/last", {cache: "no-store"});
      const j = await r.json();
      if (j.ok && j.data && j.data.id) {
        currentSessionId = j.data.id;
        currentSessionTitle = j.data.title || "Nova conversa";
        messages = Array.isArray(j.data.messages) ? j.data.messages : [];
        renderMessages();
        await refreshFiles();
      } else {
        await createSession();
      }
    } catch (_) {
      await createSession();
    }
  }

  async function changeMode(mode) {
    if (generating) return;
    if (!currentStatus?.profile_available) { openCalibration(true); return; }
    showNotice("");
    modeButtons.forEach(b => b.disabled = true);
    $("#readyText").textContent = "TROCANDO MODO";
    $("#readyDot").classList.remove("ready");

    try {
      const r = await fetch("/api/mode", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({mode})
      });
      const j = await r.json();
      if (!j.ok) throw new Error(j.error?.message || "Falha ao trocar modo.");
      formatStatus(j.data);
      if (messages.length) await saveSession();
    } catch (e) {
      showNotice(e.message);
      await refreshStatus();
    } finally {
      modeButtons.forEach(b => b.disabled = generating);
    }
  }


  function setCalibrationView(view) {
    $("#calIntro").classList.toggle("hidden", view !== "intro");
    $("#calRunning").classList.toggle("hidden", view !== "running");
    $("#calFinished").classList.toggle("hidden", view !== "finished");
    $("#calError").classList.toggle("hidden", view !== "error");
  }

  function hardwareHTML(s) {
    const rows = [
      ["CPU", s.cpu || "—"],
      ["RAM", s.ram_total_gb != null ? `${s.ram_total_gb} GB` : "—"],
      ["GPU", s.gpu || "Sem NVIDIA detectada"],
      ["Machine ID", s.machine_id || "—"]
    ];
    return rows.map(([a,b]) => `<span>${escapeHTML(a)}</span><strong>${escapeHTML(String(b))}</strong>`).join("");
  }

  function escapeHTML(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function openCalibration(mandatory = false) {
    calibrationMandatory = mandatory || !currentStatus?.profile_available;
    calibrationPanel.classList.remove("hidden");
    calibrationBackdrop.classList.remove("hidden");
    $("#calClose").classList.toggle("hidden", calibrationMandatory);
    $("#calErrorClose").classList.toggle("hidden", calibrationMandatory);

    $("#calTitle").textContent = calibrationMandatory
      ? "Novo computador detectado"
      : "Recalibrar computador";
    $("#calSubtitle").textContent = calibrationMandatory
      ? "O NÚCLEO ainda não possui um perfil para esta máquina."
      : "O NÚCLEO medirá novamente CPU, GPU e estabilidade de VRAM.";

    $("#calHardware").innerHTML = hardwareHTML(currentStatus || {});
    setCalibrationView("intro");
    pollCalibrationOnce();
  }

  function closeCalibration() {
    if (calibrationMandatory) return;
    calibrationPanel.classList.add("hidden");
    calibrationBackdrop.classList.add("hidden");
    if (calibrationTimer) {
      clearInterval(calibrationTimer);
      calibrationTimer = null;
    }
  }

  function formatDuration(seconds) {
    const n = Math.max(0, Number(seconds) || 0);
    const m = Math.floor(n / 60);
    const s = Math.floor(n % 60);
    return m > 0 ? `${m}m ${String(s).padStart(2, "0")}s` : `${s}s`;
  }

  function renderCalibration(data) {
    if (!data) return;

    if (data.state === "running") {
      setCalibrationView("running");
      const p = Math.max(0, Math.min(100, Number(data.progress) || 0));
      $("#calProgress").style.width = `${p}%`;
      $("#calPercent").textContent = `${p}%`;
      $("#calMessage").textContent = data.message || "Calibrando...";
      const total = formatDuration(data.elapsed_seconds);
      const stage = formatDuration(data.stage_elapsed_seconds);
      const quiet = Number(data.last_activity_seconds || 0);
      const activeText = quiet >= 8
        ? `Teste em andamento • etapa ${stage} • total ${total} • aguardando conclusão da sonda`
        : `Teste em andamento • etapa ${stage} • total ${total}`;
      $("#calHeartbeat").textContent = activeText;
      $("#readyText").textContent = "CALIBRANDO";
      sendBtn.disabled = true;
      input.disabled = true;
      return;
    }

    if (data.state === "finished") {
      setCalibrationView("finished");
      const modes = data.result?.modes || {};
      const fast = modes.fast;
      const quality = modes.quality;
      const recommended = data.result?.recommended === "quality" ? "QUALIDADE" : "RÁPIDO";

      const lines = [
        "<strong>Configuração concluída.</strong>",
        fast ? `RÁPIDO — ${escapeHTML(fast.model)} — ~${escapeHTML(fast.reference_tps ?? "—")} t/s` : "",
        quality ? `QUALIDADE — ${escapeHTML(quality.model)} — ~${escapeHTML(quality.reference_tps ?? "—")} t/s` : "",
        `AUTO recomenda: <strong>${recommended}</strong>`
      ].filter(Boolean);
      $("#calResult").innerHTML = lines.join("<br>");
      if (calibrationTimer) {
        clearInterval(calibrationTimer);
        calibrationTimer = null;
      }
      calibrationMandatory = false;
      $("#calClose").classList.remove("hidden");
      $("#calErrorClose").classList.remove("hidden");
      refreshStatus();
      return;
    }

    if (data.state === "error" || data.state === "cancelled") {
      setCalibrationView("error");
      $("#calErrorText").textContent = data.state === "cancelled"
        ? "A calibração foi cancelada."
        : (data.error || "Não foi possível concluir a calibração.");
      $("#calOutput").textContent = (data.output_tail || []).join("\n");
      if (calibrationTimer) {
        clearInterval(calibrationTimer);
        calibrationTimer = null;
      }
      refreshStatus();
      return;
    }

    setCalibrationView("intro");
  }

  async function pollCalibrationOnce() {
    try {
      const r = await fetch("/api/calibrate/status", {cache: "no-store"});
      const j = await r.json();
      if (j.ok) renderCalibration(j.data);
    } catch (_) {}
  }

  function startCalibrationPolling() {
    if (calibrationTimer) clearInterval(calibrationTimer);
    calibrationTimer = setInterval(pollCalibrationOnce, 1000);
  }

  async function startCalibration() {
    setCalibrationView("running");
    $("#calProgress").style.width = "5%";
    $("#calPercent").textContent = "5%";
    $("#calMessage").textContent = "Preparando a calibração...";
    try {
      const r = await fetch("/api/calibrate", {method: "POST"});
      const j = await r.json();
      if (!j.ok) throw new Error(j.error?.message || "Não foi possível iniciar a calibração.");
      renderCalibration(j.data);
      startCalibrationPolling();
    } catch (e) {
      setCalibrationView("error");
      $("#calErrorText").textContent = e.message;
      $("#calOutput").textContent = "";
    }
  }

  async function cancelCalibration() {
    try {
      await fetch("/api/calibrate/cancel", {method: "POST"});
    } catch (_) {}
    await pollCalibrationOnce();
  }


  function stateLabel(obj) {
    if (!obj) return "—";
    if (obj.ok) return "OK";
    if (obj.state === "unreadable") return "Ilegível";
    return "Ausente";
  }

  function setMaintenanceBusy(busy, text = "") {
    for (const id of [
      "repairCuda", "repairCpu", "maintenanceRestart",
      "maintenanceCpu", "maintenanceProfile"
    ]) {
      const el = $("#" + id);
      if (el) el.disabled = busy || el.dataset.unavailable === "1";
    }
    const box = $("#maintenanceMessage");
    if (text) {
      box.textContent = text;
      box.classList.remove("hidden");
    } else if (!busy) {
      box.classList.add("hidden");
    }
  }

  async function refreshMaintenance() {
    const r = await fetch("/api/maintenance/status", {cache: "no-store"});
    const j = await r.json();
    if (!j.ok) throw new Error(j.error?.message || "Falha no diagnóstico.");

    const d = j.data;
    const summary = $("#maintenanceSummary");
    summary.className = `maintenanceSummary ${d.overall || ""}`;
    summary.textContent = d.message || "Diagnóstico concluído.";

    $("#mCuda").textContent = stateLabel(d.cuda);
    $("#mCpu").textContent = stateLabel(d.cpu);
    $("#mModels").textContent = d.models?.ok ? "OK" : "Atenção";

    const policy = d.engine?.backend_policy === "cpu_forced" ? " • CPU forçada" : "";
    $("#mBackend").textContent =
      `${(d.engine?.backend || "—").toUpperCase()}${policy}`;

    const buttons = {
      repairCuda: d.actions?.can_repair_cuda && !d.cuda?.ok,
      repairCpu: d.actions?.can_repair_cpu && !d.cpu?.ok,
      maintenanceRestart: d.actions?.can_restart,
      maintenanceCpu: d.actions?.can_use_cpu && d.engine?.backend_policy !== "cpu_forced",
      maintenanceProfile: d.actions?.can_restore_profile_backend
        && (d.engine?.backend_policy === "cpu_forced" || d.engine?.backend === "cpu")
    };
    for (const [id, enabled] of Object.entries(buttons)) {
      const el = $("#" + id);
      el.dataset.unavailable = enabled ? "0" : "1";
      el.disabled = !enabled;
    }
    return d;
  }

  async function openMaintenance() {
    maintenancePanel.classList.remove("hidden");
    maintenanceBackdrop.classList.remove("hidden");
    $("#maintenanceMessage").classList.add("hidden");
    $("#maintenanceSummary").textContent = "Verificando...";
    try {
      await refreshMaintenance();
    } catch (e) {
      $("#maintenanceSummary").textContent = e.message;
      $("#maintenanceSummary").className = "maintenanceSummary error";
    }
  }

  function closeMaintenance() {
    maintenancePanel.classList.add("hidden");
    maintenanceBackdrop.classList.add("hidden");
  }

  async function maintenanceAction(endpoint, body = null, busyText = "Executando...") {
    setMaintenanceBusy(true, busyText);
    try {
      const opts = {method: "POST"};
      if (body) {
        opts.headers = {"Content-Type": "application/json"};
        opts.body = JSON.stringify(body);
      }
      const r = await fetch(endpoint, opts);
      const j = await r.json();
      if (!j.ok) throw new Error(j.error?.message || "A operação falhou.");
      $("#maintenanceMessage").textContent = "Operação concluída.";
      $("#maintenanceMessage").classList.remove("hidden");
      await refreshStatus();
      await refreshMaintenance();
      return j.data;
    } catch (e) {
      $("#maintenanceMessage").textContent = e.message;
      $("#maintenanceMessage").classList.remove("hidden");
      await refreshMaintenance().catch(() => {});
      throw e;
    } finally {
      setMaintenanceBusy(false);
    }
  }

  async function loadMaintenanceLogs() {
    const pre = $("#maintenanceLogText");
    pre.textContent = "Carregando...";
    try {
      const r = await fetch("/api/maintenance/logs", {cache: "no-store"});
      const j = await r.json();
      if (!j.ok) throw new Error(j.error?.message || "Falha ao carregar logs.");
      const d = j.data;
      const parts = [];
      if (d.engine_tail?.length) {
        parts.push(`=== ${d.engine_log || "llama-server.log"} ===\n${d.engine_tail.join("\n")}`);
      }
      if (d.calibration_tail?.length) {
        parts.push(`=== ${d.calibration_log || "calibration.log"} ===\n${d.calibration_tail.join("\n")}`);
      }
      if (d.maintenance_tail?.length) {
        parts.push(`=== ${d.maintenance_log} ===\n${d.maintenance_tail.join("\n")}`);
      }
      pre.textContent = parts.join("\n\n") || "Nenhum log recente.";
    } catch (e) {
      pre.textContent = e.message;
    }
  }

  function parseSSE(buffer, onEvent) {
    let split;
    while ((split = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      for (const line of block.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const raw = line.slice(5).trim();
        try { onEvent(JSON.parse(raw)); } catch (_) {}
      }
    }
    return buffer;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text || generating) return;

    showNotice("");
    if (!currentSessionId) await createSession();

    messages.push({role: "user", content: text});
    addMessage("user", text);
    input.value = "";

    // Save the user prompt before generation, so it survives an engine failure.
    try { await saveSession(); } catch (e) { showNotice(e.message); }

    const assistantBody = addMessage("assistant", "");
    let assistantText = "";
    setGenerating(true);
    stopRequested = false;
    const autoOn = (document.getElementById("autoContinuar") || {}).checked !== false;

    // um passe de streaming: envia payloadMessages, anexa deltas ao mesmo balão,
    // devolve true se a resposta foi cortada no limite (finish_reason=length).
    async function streamPass(payloadMessages) {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({messages: payloadMessages, session_id: currentSessionId})
      });
      if (!r.ok) {
        const j = await r.json().catch(() => null);
        throw new Error(j?.error?.message || `Erro HTTP ${r.status}`);
      }
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let truncated = false;
      while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, {stream: true});
        buffer = parseSSE(buffer, (evt) => {
          if (evt.type === "delta") {
            assistantText += evt.text;
            assistantBody.textContent = assistantText;
            chat.scrollTop = chat.scrollHeight;
          } else if (evt.type === "error") {
            showNotice(evt.message || "Erro durante a geração.");
          } else if (evt.type === "done") {
            if (evt.tps && currentStatus) {
              currentStatus.last_tps = evt.tps;
              formatStatus(currentStatus);
            }
            if (evt.truncated) truncated = true;
          }
        });
      }
      return truncated;
    }

    try {
      let truncated = await streamPass(messages);
      // auto-continuar: reenvia "continue" e emenda no mesmo balão, com teto e Parar
      let auto = 0;
      while (truncated && autoOn && !stopRequested && auto < AUTO_CONTINUE_MAX) {
        auto++;
        showNotice(`↳ continuando automaticamente (${auto}/${AUTO_CONTINUE_MAX})… clique Parar para interromper.`);
        const cont = messages.concat([
          {role: "assistant", content: assistantText},
          {role: "user", content: "Continue exatamente de onde você parou, sem repetir nada do que já escreveu e sem qualquer preâmbulo."}
        ]);
        truncated = await streamPass(cont);
      }
      if (truncated && !stopRequested) {
        showNotice(autoOn
          ? `Ainda incompleto após ${AUTO_CONTINUE_MAX} continuações automáticas. Digite 'continuar' para seguir.`
          : "A resposta atingiu o limite de geração. Peça 'continue' ou faça uma pergunta mais específica.");
      } else if (notice.textContent.startsWith("↳")) {
        showNotice("");  // limpa o aviso "continuando…"; preserva avisos de erro
      }

      if (assistantText.trim()) {
        messages.push({role: "assistant", content: assistantText});
      } else if (!notice.textContent) {
        assistantBody.textContent = "[geração interrompida]";
      }

      try { await saveSession(); } catch (e) { showNotice(e.message); }
    } catch (e) {
      showNotice(e.message);
      if (assistantText.trim()) {
        messages.push({role: "assistant", content: assistantText}); // preserva o parcial
      } else {
        assistantBody.textContent = "[falha na geração]";
      }
      try { await saveSession(); } catch (_) {}
    } finally {
      setGenerating(false);
      stopRequested = false;
      refreshStatus();
      input.focus();
      updateBaixar();
    }
  }

  // ----- exportar conversa / resultado da análise (.md/.txt/.csv), 100% local -----
  function _download(name, text, mime) {
    try {
      const blob = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    } catch (e) { showNotice("Não foi possível baixar: " + e.message); }
  }
  // .docx/.xlsx são gerados no servidor (/api/export) e baixados como binário.
  async function _exportServer(formato, content, base, titulo) {
    if (!content || !content.trim()) { showNotice("Nada para exportar."); return; }
    try {
      const r = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ formato, content, titulo: titulo || base }),
      });
      const ctype = r.headers.get("Content-Type") || "";
      if (!r.ok || ctype.includes("application/json")) {
        let msg = "falha na exportação (" + r.status + ")";
        try { const j = await r.json(); msg = (j.error && j.error.message) || msg; } catch (_) {}
        showNotice("Export: " + msg); return;
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = base + "." + formato;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    } catch (e) { showNotice("Não foi possível exportar: " + e.message); }
  }
  function _stamp() {
    const d = new Date(), p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}`;
  }
  function _baseName() {
    const t = (currentSessionTitle || "conversa").replace(/[^\wÀ-ÿ -]/g, "").trim().replace(/\s+/g, "-").toLowerCase();
    return (t || "conversa") + "_" + _stamp();
  }
  function _convToMd() {
    return messages.map(m => `## ${m.role === "user" ? "Você" : "NÚCLEO"}\n\n${m.content}`).join("\n\n");
  }
  function _convToTxt() {
    return messages.map(m => `[${m.role === "user" ? "VOCÊ" : "NÚCLEO"}]\n${m.content}`).join("\n\n----\n\n");
  }
  function _lastAssistant() {
    for (let i = messages.length - 1; i >= 0; i--) if (messages[i].role === "assistant") return messages[i].content;
    return "";
  }
  // 1ª tabela markdown contígua -> CSV
  function _mdTableToCsv(text) {
    const lines = String(text).split(/\r?\n/);
    const rows = []; let inTable = false;
    for (const ln of lines) {
      const isRow = /^\s*\|.*\|\s*$/.test(ln);
      const isSep = isRow && /^[\s:|-]+$/.test(ln.replace(/\|/g, "")) && ln.includes("-");
      if (isRow && !isSep) {
        rows.push(ln.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(c => c.trim()));
        inTable = true;
      } else if (inTable && !isRow) { break; }  // pula a linha separadora (|---|); só encerra em linha fora da tabela
    }
    if (!rows.length) return "";
    const esc = (c) => /[",\n;]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c;
    return rows.map(r => r.map(esc).join(",")).join("\r\n");
  }
  function _hasTable() {
    return messages.some(m => m.role === "assistant" && /^\s*\|.*\|\s*$/m.test(m.content));
  }
  const baixarBtn = $("#baixarBtn"), baixarMenu = $("#baixarMenu");
  function updateBaixar() {
    const btn = document.getElementById("baixarBtn");
    const csv = document.getElementById("baixarCsv");
    const xlsx = document.getElementById("baixarXlsx");
    const menu = document.getElementById("baixarMenu");
    if (btn) btn.disabled = !messages.length;
    const temTabela = _hasTable();
    if (csv) csv.classList.toggle("hidden", !temTabela);
    if (xlsx) xlsx.classList.toggle("hidden", !temTabela);
    if (!messages.length && menu) menu.classList.add("hidden");
  }
  function closeBaixar() { if (baixarMenu) baixarMenu.classList.add("hidden"); }
  if (baixarBtn) baixarBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (baixarBtn.disabled) return;
    updateBaixar();
    baixarMenu.classList.toggle("hidden");
  });
  if (baixarMenu) baixarMenu.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-exp]"); if (!b) return;
    const kind = b.dataset.exp, base = _baseName();
    if (kind === "conv-md") _download(base + ".md", _convToMd(), "text/markdown");
    else if (kind === "conv-txt") _download(base + ".txt", _convToTxt(), "text/plain");
    else if (kind === "conv-docx") _exportServer("docx", _convToMd(), base, currentSessionTitle || "Conversa");
    else if (kind === "last-md" || kind === "last-txt") {
      const t = _lastAssistant();
      if (!t.trim()) { showNotice("Ainda não há resposta da IA para baixar."); }
      else _download(base + "_resposta." + (kind === "last-md" ? "md" : "txt"), t,
                     kind === "last-md" ? "text/markdown" : "text/plain");
    } else if (kind === "last-docx") {
      const t = _lastAssistant();
      if (!t.trim()) showNotice("Ainda não há resposta da IA para baixar.");
      else _exportServer("docx", t, base + "_resposta", currentSessionTitle || "Resposta");
    } else if (kind === "csv") {
      const csv = _mdTableToCsv(_lastAssistant()) || _mdTableToCsv(_convToMd());
      if (!csv) showNotice("Nenhuma tabela encontrada na resposta.");
      else _download(base + ".csv", csv, "text/csv");
    } else if (kind === "xlsx") {
      const t = _lastAssistant();
      if (!/^\s*\|.*\|\s*$/m.test(t)) showNotice("Nenhuma tabela encontrada na resposta.");
      else _exportServer("xlsx", t, base, currentSessionTitle || "Tabela");
    }
    closeBaixar();
  });
  document.addEventListener("click", (e) => {
    if (baixarMenu && !baixarMenu.classList.contains("hidden") && !e.target.closest("#baixarWrap")) closeBaixar();
  });

  attachBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => uploadFiles(fileInput.files));

  for (const eventName of ["dragenter", "dragover"]) {
    composer.addEventListener(eventName, (e) => {
      e.preventDefault();
      composer.classList.add("dragging");
    });
  }
  for (const eventName of ["dragleave", "drop"]) {
    composer.addEventListener(eventName, (e) => {
      e.preventDefault();
      composer.classList.remove("dragging");
    });
  }
  composer.addEventListener("drop", (e) => uploadFiles(e.dataTransfer?.files));

  sendBtn.addEventListener("click", () => sendMessage().catch(e => showNotice(e.message)));

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage().catch(err => showNotice(err.message));
    }
  });

  stopBtn.addEventListener("click", async () => {
    stopRequested = true;   // interrompe o laço de auto-continuar
    try { await fetch("/api/stop", {method: "POST"}); } catch (_) {}
  });

  $("#newChat").addEventListener("click", () => newConversation().catch(e => showNotice(e.message)));
  $("#historyNew").addEventListener("click", () => newConversation().catch(e => showNotice(e.message)));
  $("#historyBtn").addEventListener("click", openHistory);
  $("#closeHistory").addEventListener("click", closeHistory);
  historyBackdrop.addEventListener("click", closeHistory);

  $("#detailsBtn").addEventListener("click", () => {
    $("#details").classList.toggle("hidden");
    refreshStatus();
  });

  $("#calibrateBtn").addEventListener("click", () => openCalibration(false));
  $("#calClose").addEventListener("click", closeCalibration);
  $("#calErrorClose").addEventListener("click", closeCalibration);
  $("#calDone").addEventListener("click", () => {
    calibrationMandatory = false;
    closeCalibration();
    refreshStatus();
    input.focus();
  });
  $("#calStart").addEventListener("click", startCalibration);
  $("#calRetry").addEventListener("click", startCalibration);
  $("#calCancel").addEventListener("click", cancelCalibration);
  calibrationBackdrop.addEventListener("click", () => {
    if (!calibrationMandatory) closeCalibration();
  });

  $("#maintenanceBtn").addEventListener("click", openMaintenance);
  $("#maintenanceDetailsBtn").addEventListener("click", openMaintenance);
  $("#maintenanceClose").addEventListener("click", closeMaintenance);
  maintenanceBackdrop.addEventListener("click", closeMaintenance);

  $("#maintenanceRestart").addEventListener("click", () =>
    maintenanceAction("/api/maintenance/restart", null, "Reiniciando motor...")
      .catch(() => {})
  );
  $("#maintenanceCpu").addEventListener("click", () =>
    maintenanceAction("/api/maintenance/use-cpu", null, "Iniciando motor em CPU...")
      .catch(() => {})
  );
  $("#maintenanceProfile").addEventListener("click", () =>
    maintenanceAction("/api/maintenance/profile-backend", null, "Restaurando backend do perfil...")
      .catch(() => {})
  );

  $("#repairCuda").addEventListener("click", () => {
    if (!confirm("Reparar o motor CUDA usando os arquivos já existentes no cache? A pasta atual será preservada.")) return;
    maintenanceAction(
      "/api/maintenance/repair",
      {backend: "cuda"},
      "Reparando motor CUDA. Aguarde..."
    ).catch(() => {});
  });

  $("#repairCpu").addEventListener("click", () => {
    if (!confirm("Reparar o motor CPU usando os arquivos já existentes no cache? A pasta atual será preservada.")) return;
    maintenanceAction(
      "/api/maintenance/repair",
      {backend: "cpu"},
      "Reparando motor CPU. Aguarde..."
    ).catch(() => {});
  });

  $("#maintenanceLogs").addEventListener("toggle", () => {
    if ($("#maintenanceLogs").open) loadMaintenanceLogs();
  });

  modeButtons.forEach(b => b.addEventListener("click", () => changeMode(b.dataset.mode)));

  // Esconde o botão CÓDIGO em máquinas onde o modo 'code' não foi calibrado
  // (ex.: cópia portátil numa máquina nova só tem fast/quality auto-calibrados).
  async function gateModeButtons() {
    try {
      const r = await fetch("/api/modes", { cache: "no-store" });
      const j = await r.json();
      const modes = (j.ok && j.data && j.data.modes) || {};
      const codeBtn = modeButtons.find(b => b.dataset.mode === "code");
      if (codeBtn) codeBtn.classList.toggle("hidden", !modes.code);
    } catch (_) {}
  }

  // ===== V0.9.7: navegação por views (Chat / Escrever Livros / Análise) =====
  const navItems = [...document.querySelectorAll(".navItem")];
  function switchView(view) {
    navItems.forEach(b => b.classList.toggle("active", b.dataset.view === view));
    for (const v of ["chat", "livros", "analise", "forja", "diagnostico"]) {
      const el = document.getElementById("view-" + v);
      if (el) el.classList.toggle("hidden", v !== view);
    }
    if (view === "livros") { showBrowse(); loadLivros(); }
    if (view === "forja" && typeof window.__mountForja === "function") window.__mountForja();
  }
  navItems.forEach(b => b.addEventListener("click", () => switchView(b.dataset.view)));

  // ===== Diagnóstico da máquina (consultor GGUF) =====
  let diagRelatorio = "";
  const diagRodarBtn = document.getElementById("diagRodar");
  const diagBaixarBtn = document.getElementById("diagBaixar");
  function _diagGrupo(titulo, cls, itens) {
    if (!itens || !itens.length)
      return `<div class="diagGrupo ${cls}"><h3>${titulo}</h3><p class="muted">— nenhum —</p></div>`;
    const linhas = itens.map(m => {
      const nucleo = m.nucleo ? `<span class="diagNucleo">NÚCLEO · ${m.nucleo}</span>` : "";
      const tag = m.tag ? `<span class="diagTag">${m.tag}</span>` : "";
      return `<li><span class="diagNome">${m.nome}</span> <span class="muted">${m.params} · ${m.quant} · ~${m.size_gb} GB</span> ${tag}${nucleo}<br><span class="diagGpu">${m.gpu}</span></li>`;
    }).join("");
    return `<div class="diagGrupo ${cls}"><h3>${titulo} <span class="diagCount">(${itens.length})</span></h3><ul>${linhas}</ul></div>`;
  }
  function renderDiag(d) {
    const hw = d.hardware || {}, g = d.gguf || {}, grp = g.grupos || {};
    const cont = document.getElementById("diagResultado");
    const hwHtml = `<div class="diagHw">
      <div><b>CPU</b><br>${hw.cpu || "?"} · ${hw.physical_cores || "?"}c/${hw.logical_threads || "?"}t</div>
      <div><b>RAM</b><br>${_nf(hw.ram_total_gb)} GB total · ${_nf(hw.ram_available_gb)} GB livre agora</div>
      <div><b>GPU</b><br>${hw.gpu_nome || "—"} · ${_nf(g.vram_gb)} GB VRAM</div>
      <div><b>RAM útil p/ modelo</b><br>~${_nf(g.ram_util_estimada_gb)} GB (reserva SO ${g.reserva_so_gb} GB)</div>
    </div>`;
    cont.innerHTML = hwHtml
      + _diagGrupo("✅ Roda com folga", "folga", grp.folga)
      + _diagGrupo("⚠️ Roda no limite", "limite", grp.limite)
      + _diagGrupo("⛔ Não roda", "nao_roda", grp.nao_roda)
      + `<p class="muted diagNota">Estimativas conservadoras (llama.cpp usa mmap). Contexto longo, quantização e nº de camadas na GPU alteram o consumo. "Não roda" ainda pode caber com quantização mais agressiva (IQ3/IQ2) e contexto mínimo.</p>`;
  }
  async function rodarDiag() {
    const msg = document.getElementById("diagMsg");
    if (diagRodarBtn) diagRodarBtn.disabled = true;
    if (msg) msg.textContent = "Detectando hardware… (alguns segundos)";
    try {
      const r = await fetch("/api/hardware/diagnostico", { cache: "no-store" });
      const j = await r.json();
      if (!j.ok) throw new Error((j.error && j.error.message) || "falha");
      renderDiag(j.data);
      diagRelatorio = j.data.relatorio_txt || "";
      if (diagBaixarBtn) diagBaixarBtn.classList.toggle("hidden", !diagRelatorio);
      if (msg) msg.textContent = "Concluído ✓";
    } catch (e) {
      if (msg) msg.textContent = "Falha ao diagnosticar (o NÚCLEO está rodando?).";
    } finally {
      if (diagRodarBtn) diagRodarBtn.disabled = false;
    }
  }
  if (diagRodarBtn) diagRodarBtn.addEventListener("click", () => rodarDiag());
  if (diagBaixarBtn) diagBaixarBtn.addEventListener("click", () => {
    if (diagRelatorio) _download("diagnostico_hardware_" + _stamp() + ".txt", diagRelatorio, "text/plain");
  });

  async function loadLivros() {
    const list = document.getElementById("livrosList");
    if (!list) return;
    list.innerHTML = '<p class="muted">Carregando…</p>';
    try {
      const r = await fetch("/api/livros", {cache: "no-store"});
      const j = await r.json();
      const books = (j && j.data) || [];
      if (!books.length) {
        list.innerHTML = '<p class="muted">Nenhum livro em workspace/livros ainda. Crie um com CRIAR_LIVRO.bat.</p>';
        return;
      }
      list.innerHTML = "";
      for (const b of books) {
        const card = document.createElement("div");
        card.className = "livroCard clickable";
        card.addEventListener("click", () => openLivro(b.slug));
        const w = (b.written_words || 0).toLocaleString("pt-BR");
        const meta = b.target_words
          ? `${w} / ${b.target_words.toLocaleString("pt-BR")} palavras · ${b.chapters_written} cap.`
          : `${w} palavras · ${b.chapters_written} cap.`;
        const tags = [];
        if (b.has_docx) tags.push('<span class="livroTag">DOCX</span>');
        if (b.has_epub) tags.push('<span class="livroTag">EPUB</span>');
        card.innerHTML =
          '<div class="livroTop"><span class="livroTitle"></span>' +
          (b.genre ? '<span class="livroGenre"></span>' : "") + "</div>" +
          '<div class="livroMeta">' + meta + "</div>" +
          '<div class="livroBar"><div class="livroBarFill"></div></div>' +
          (tags.length ? '<div class="livroTags">' + tags.join("") + "</div>" : "");
        card.querySelector(".livroTitle").textContent = b.title || b.slug;
        if (b.genre) card.querySelector(".livroGenre").textContent = b.genre;
        const fill = card.querySelector(".livroBarFill");
        if (fill) fill.style.width = (b.progress_pct || 0) + "%";
        list.appendChild(card);
      }
    } catch (e) {
      list.innerHTML = '<p class="muted">Não foi possível listar os livros agora. O NÚCLEO está iniciando ou foi fechado? Rode INICIAR_NUCLEO_IA e clique em <strong>Atualizar</strong>.</p>';
    }
  }
  const livrosRefresh = document.getElementById("livrosRefresh");
  if (livrosRefresh) livrosRefresh.addEventListener("click", loadLivros);

  // ----- criar livro no painel (só scaffolder, sem IA) -----
  let generosCache = null;
  async function ensureGeneros() {
    const sel = document.getElementById("nvGenero");
    if (!sel || generosCache) return;
    try {
      const r = await fetch("/api/livros/generos", {cache: "no-store"});
      const j = await r.json();
      generosCache = (j && j.data) || [];
    } catch (e) { generosCache = []; }
    sel.innerHTML = "";
    const groups = { ficcao: [], tecnico: [] };
    for (const g of generosCache) (groups[g.family] || (groups[g.family] = [])).push(g);
    const labels = { ficcao: "Ficção", tecnico: "Técnico / Não-ficção" };
    for (const fam of ["ficcao", "tecnico"]) {
      if (!groups[fam] || !groups[fam].length) continue;
      const og = document.createElement("optgroup");
      og.label = labels[fam] || fam;
      for (const g of groups[fam]) {
        const o = document.createElement("option");
        o.value = g.id; o.textContent = g.id;
        og.appendChild(o);
      }
      sel.appendChild(og);
    }
    applyGeneroFamilia();
  }
  function familiaDoGenero(id) {
    if (!generosCache) return null;
    const g = generosCache.find((x) => x.id === id);
    return g ? g.family : null;
  }
  function applyGeneroFamilia() {
    const sel = document.getElementById("nvGenero");
    const fam = sel ? familiaDoGenero(sel.value) : null;
    const gf = document.getElementById("grpFiccao");
    const gt = document.getElementById("grpTecnico");
    if (gf) gf.classList.toggle("hidden", fam !== "ficcao");
    if (gt) gt.classList.toggle("hidden", fam !== "tecnico");
  }
  const livroNovoBtn = document.getElementById("livroNovoBtn");
  const livroNovoForm = document.getElementById("livroNovoForm");
  function toggleNovo(show) {
    if (!livroNovoForm) return;
    const willShow = show === undefined ? livroNovoForm.classList.contains("hidden") : show;
    livroNovoForm.classList.toggle("hidden", !willShow);
    if (willShow) {
      ensureGeneros();
      document.getElementById("nvMsg").textContent = "";
      document.getElementById("nvTitulo").focus();
    }
  }
  if (livroNovoBtn) livroNovoBtn.addEventListener("click", () => toggleNovo());
  const nvGeneroSel = document.getElementById("nvGenero");
  if (nvGeneroSel) nvGeneroSel.addEventListener("change", applyGeneroFamilia);
  const nvCancelar = document.getElementById("nvCancelar");
  if (nvCancelar) nvCancelar.addEventListener("click", () => toggleNovo(false));
  // campos de fundação: chave do meta -> id do elemento, por grupo
  const NV_COMUM = {
    premissa: "nvPremissa", promessa: "nvPromessa", publico: "nvPublico",
    tema: "nvTema", tom: "nvTom", estrutura: "nvEstrutura",
    voz_narrador: "nvVozNarrador", voz_tique: "nvVozTique",
    banidos: "nvBanidos", tetos: "nvTetos", tamanho: "nvTamanho",
  };
  const NV_FICCAO = {
    subgenero: "nvSubgenero", epoca: "nvEpoca", pov: "nvPov",
    protagonista: "nvProtagonista", conflito: "nvConflito",
    personagens_chave: "nvPersonagensChave", personagens: "nvPersonagens",
  };
  const NV_TECNICO = {
    tipo: "nvTipo", assunto: "nvAssunto", nivel: "nvNivel", ferramenta: "nvFerramenta",
  };
  function nvValId(id) {
    const el = document.getElementById(id);
    return el ? String(el.value).trim() : "";
  }
  function limparFundacao() {
    for (const m of [NV_COMUM, NV_FICCAO, NV_TECNICO]) {
      for (const id of Object.values(m)) {
        const el = document.getElementById(id);
        if (!el) continue;
        if (el.tagName === "SELECT") el.selectedIndex = 0; else el.value = "";
      }
    }
  }
  if (livroNovoForm) livroNovoForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("nvMsg");
    const titulo = document.getElementById("nvTitulo").value.trim();
    const autor = document.getElementById("nvAutor").value.trim();
    const genero = document.getElementById("nvGenero").value;
    const slug = document.getElementById("nvSlug").value.trim();
    if (!titulo && !slug) { msg.textContent = "Informe ao menos um título."; return; }
    if (!genero) { msg.textContent = "Escolha um gênero."; return; }
    // monta o meta conforme a família do gênero
    const fam = familiaDoGenero(genero);
    const grupo = Object.assign({}, NV_COMUM,
      fam === "ficcao" ? NV_FICCAO : fam === "tecnico" ? NV_TECNICO : {});
    const meta = {};
    for (const k of Object.keys(grupo)) { const v = nvValId(grupo[k]); if (v) meta[k] = v; }
    msg.textContent = "Criando…";
    try {
      const r = await fetch("/api/livros/criar", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titulo, autor, genero, slug, meta }),
      });
      const j = await r.json();
      if (!j.ok) { msg.textContent = (j.error && j.error.message) || "Falha ao criar."; return; }
      document.getElementById("nvTitulo").value = "";
      document.getElementById("nvAutor").value = "";
      document.getElementById("nvSlug").value = "";
      limparFundacao();
      toggleNovo(false);
      await loadLivros();
      if (j.data && j.data.slug) openLivro(j.data.slug);
    } catch (err) {
      msg.textContent = "Não foi possível criar (o NÚCLEO está rodando?).";
    }
  });

  // ----- detalhe do livro (leitura, read-only) -----
  let currentBookSlug = null;
  function showBrowse() {
    document.getElementById("livrosBrowse").classList.remove("hidden");
    document.getElementById("livroDetalhe").classList.add("hidden");
    const nf = document.getElementById("livroNovoForm");
    if (nf) nf.classList.add("hidden");
  }
  const livroVoltar = document.getElementById("livroVoltar");
  if (livroVoltar) livroVoltar.addEventListener("click", showBrowse);

  async function livroAcao(kind, label) {
    if (!currentBookSlug) return;
    const slug = currentBookSlug;
    const msg = document.getElementById("livroAcaoMsg");
    const btns = [document.getElementById("livroRevisar"), document.getElementById("livroPublicar")];
    btns.forEach(b => { if (b) b.disabled = true; });
    msg.textContent = label + "…";
    let final = "";
    try {
      const r = await fetch("/api/livros/" + encodeURIComponent(slug) + "/" + kind, { method: "POST" });
      const j = await r.json();
      if (!j.ok) { final = (j.error && j.error.message) || ("Falha: " + label); return; }
      if (kind === "revisar") final = "Revisado ✓ — manuscrito e relatórios atualizados.";
      else final = "Publicado ✓ — " + [j.data.docx, j.data.epub].filter(Boolean).join(" + ");
      await openLivro(slug);
    } catch (e) {
      final = "Não foi possível (o NÚCLEO está rodando?).";
    } finally {
      btns.forEach(b => { if (b) b.disabled = false; });
      const m2 = document.getElementById("livroAcaoMsg");
      if (m2) m2.textContent = final;
    }
  }
  const btnRevisar = document.getElementById("livroRevisar");
  if (btnRevisar) btnRevisar.addEventListener("click", () => livroAcao("revisar", "Revisando"));
  const btnPublicar = document.getElementById("livroPublicar");
  if (btnPublicar) btnPublicar.addEventListener("click", () => livroAcao("publicar", "Publicando"));

  // ----- escrita via IA (OUTLINE/ESCREVER) com streaming SSE -----
  let runES = null;
  function setRunning(on) {
    ["runOutline", "runEscrever", "livroRevisar", "livroPublicar"].forEach(id => {
      const b = document.getElementById(id); if (b) b.disabled = on;
    });
    const parar = document.getElementById("runParar"); if (parar) parar.classList.toggle("hidden", !on);
  }
  function _nf(x) { return (x || 0).toLocaleString("pt-BR"); }
  function updateRunProg(p) {
    const wrap = document.getElementById("runProgWrap");
    const fill = document.getElementById("runBarFill");
    const label = document.getElementById("runProgLabel");
    if (!wrap || !fill || !label) return;
    wrap.classList.remove("hidden");
    const target = p.target || 0;
    let pct = target ? Math.min(100, Math.round(100 * (p.words || 0) / target)) : 0;
    let txt = "";
    if (p.phase === "inicio") { pct = 0; txt = `Iniciando… (alvo ${_nf(target)} palavras)`; }
    else if (p.phase === "cena") { txt = `Cena ${p.scene}${p.partes ? "/" + p.partes : ""} · ${_nf(p.words)}/${_nf(target)} palavras (${pct}%)`; }
    else if (p.phase === "expansao") { txt = `Expansão ${p.scene} · ${_nf(p.words)}/${_nf(target)} palavras (${pct}%)`; }
    else if (p.phase === "resumo") { pct = Math.max(pct, 96); txt = "Gerando resumo do capítulo…"; }
    else if (p.phase === "fim") { pct = 100; txt = `Concluído · ${_nf(p.words)} palavras`; }
    fill.style.width = pct + "%";
    label.textContent = txt;
  }
  function hideRunProg() { const w = document.getElementById("runProgWrap"); if (w) w.classList.add("hidden"); }
  function resetRunProg() {
    const f = document.getElementById("runBarFill"); if (f) f.style.width = "0%";
    const l = document.getElementById("runProgLabel"); if (l) l.textContent = "Preparando…";
    const w = document.getElementById("runProgWrap"); if (w) w.classList.remove("hidden");
  }
  function runBook(acao) {
    if (!currentBookSlug || runES) return;
    const slug = currentBookSlug;
    const modo = (document.getElementById("runModo") || {}).value || "advanced";
    // capítulo escolhido (só na escrita): "" = próximo pendente
    let capN = "";
    if (acao === "escrever") {
      const capSel = document.getElementById("runCapSel");
      capN = capSel ? capSel.value : "";
      if (capN) {
        const opt = capSel.options[capSel.selectedIndex];
        if (opt && opt.dataset.status === "escrito" &&
            !window.confirm(`O capítulo ${capN} já foi escrito. Reescrever? Isso substitui o texto atual.`)) {
          return;
        }
      }
    }
    const con = document.getElementById("runConsole");
    const msg = document.getElementById("runMsg");
    con.classList.remove("hidden"); con.textContent = "";
    const alvoCap = acao === "escrever" ? (capN ? ("capítulo " + capN) : "próximo capítulo pendente") : "";
    msg.textContent = (acao === "outline" ? "Gerando outline" : "Escrevendo " + alvoCap) + "… (pode levar minutos)";
    setRunning(true);
    if (acao === "escrever") resetRunProg(); else hideRunProg();
    let finished = false;
    const append = (s) => { con.textContent += s + "\n"; con.scrollTop = con.scrollHeight; };
    const cleanup = (finalMsg) => {
      finished = true;
      try { runES.close(); } catch (_) {}
      runES = null; setRunning(false);
      openLivro(slug).then(() => { const m = document.getElementById("runMsg"); if (m) m.textContent = finalMsg || ""; });
    };
    let url = "/api/livros/" + encodeURIComponent(slug) + "/run?acao=" + encodeURIComponent(acao) + "&modo=" + encodeURIComponent(modo);
    if (capN) url += "&n=" + encodeURIComponent(capN);
    const es = new EventSource(url);
    runES = es;
    es.onmessage = (ev) => {
      let o; try { o = JSON.parse(ev.data); } catch (_) { return; }
      if (o.type === "log") {
        if (typeof o.line === "string" && o.line.startsWith("::PROG:: ")) {
          try { updateRunProg(JSON.parse(o.line.slice(9))); } catch (_) {}
        } else {
          append(o.line);
        }
      }
      else if (o.type === "start") append("▶ " + o.acao + " · modo " + o.modo);
      else if (o.type === "error") append("✗ " + o.message);
      else if (o.type === "done") {
        append(o.code === 0 ? "✓ concluído." : ("terminou com código " + o.code + "."));
        cleanup(o.code === 0 ? "Concluído ✓ — motor do chat religando…" : "Terminou com erro/parada — motor religando.");
      }
    };
    es.onerror = () => { if (!finished) { append("✗ conexão interrompida."); cleanup("Interrompido (conexão perdida)."); } };
  }
  const btnOutline = document.getElementById("runOutline");
  if (btnOutline) btnOutline.addEventListener("click", () => runBook("outline"));
  const btnEscrever = document.getElementById("runEscrever");
  if (btnEscrever) btnEscrever.addEventListener("click", () => runBook("escrever"));
  const btnParar = document.getElementById("runParar");
  if (btnParar) btnParar.addEventListener("click", async () => {
    const m = document.getElementById("runMsg"); if (m) m.textContent = "Parando…";
    try { await fetch("/api/livros/run/stop", { method: "POST" }); } catch (_) {}
  });

  async function openLivro(slug) {
    currentBookSlug = slug;
    let d;
    try {
      const r = await fetch("/api/livros/" + encodeURIComponent(slug), {cache: "no-store"});
      const j = await r.json();
      if (!j.ok) throw new Error((j.error && j.error.message) || "falha");
      d = j.data;
    } catch (e) { showNotice("Não foi possível abrir o livro (o NÚCLEO está rodando?)."); return; }

    document.getElementById("livrosBrowse").classList.add("hidden");
    document.getElementById("livroDetalhe").classList.remove("hidden");
    document.getElementById("livroTitulo").textContent = d.title || d.slug;
    const gen = document.getElementById("livroGenero");
    gen.textContent = d.genre || "";
    gen.style.display = d.genre ? "" : "none";
    const w = (d.written_words || 0).toLocaleString("pt-BR");
    document.getElementById("livroProg").textContent = d.target_words
      ? `${w} / ${d.target_words.toLocaleString("pt-BR")} palavras · ${d.chapters.length} capítulo(s) · ${d.progress_pct}%`
      : `${w} palavras · ${d.chapters.length} capítulo(s)`;

    const caps = document.getElementById("livroCaps");
    caps.innerHTML = "";
    if (!d.chapters.length) {
      caps.innerHTML = '<p class="muted">Nenhum capítulo escrito ainda.</p>';
    } else {
      for (const c of d.chapters) {
        const row = document.createElement("button");
        row.className = "capRow";
        row.innerHTML = '<span class="capTit"></span><span class="capWords"></span>';
        row.querySelector(".capTit").textContent = c.title || ("Cap " + c.n);
        row.querySelector(".capWords").textContent = (c.words || 0).toLocaleString("pt-BR") + " pal.";
        row.addEventListener("click", () => openBookFile(slug, c.rel, c.title || ("Capítulo " + c.n), row));
        caps.appendChild(row);
      }
    }

    const docs = document.getElementById("livroDocs");
    docs.innerHTML = "";
    const present = d.docs.filter(x => x.exists);
    if (!present.length) {
      docs.innerHTML = '<p class="muted">Sem documentos ainda.</p>';
    } else {
      for (const doc of present) {
        const row = document.createElement("button");
        row.className = "docRow";
        row.textContent = doc.label;
        row.addEventListener("click", () => openBookFile(slug, doc.rel, doc.label, row));
        docs.appendChild(row);
      }
    }

    // seletor de capítulo para escrita (plano completo: pendente/escrito)
    const capSel = document.getElementById("runCapSel");
    if (capSel) {
      const plan = d.plan || [];
      capSel.innerHTML = '<option value="">Próximo pendente</option>';
      for (const c of plan) {
        const opt = document.createElement("option");
        opt.value = String(c.n);
        let t = c.title || ("Capítulo " + c.n);
        if (t.length > 40) t = t.slice(0, 39) + "…";
        opt.textContent = `Cap ${c.n} — ${t} ${c.status === "escrito" ? "✓" : "○"}`;
        opt.dataset.status = c.status;
        capSel.appendChild(opt);
      }
    }

    document.getElementById("readerTitle").textContent = "Selecione um capítulo ou documento para ler.";
    document.getElementById("reader").textContent = "";
  }

  // render markdown seguro: escapa HTML ANTES, depois monta blocos/inline
  function mdEsc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function mdInline(s) {
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");
    return s;
  }
  function renderMarkdown(md) {
    md = (md || "").replace(/<!--[\s\S]*?-->/g, "");
    const lines = md.split(/\r?\n/);
    const out = [];
    let inCode = false, code = [], listType = null, listItems = [], para = [];
    const flushPara = () => { if (para.length) { out.push("<p>" + mdInline(mdEsc(para.join(" "))) + "</p>"); para = []; } };
    const flushList = () => { if (listType) { out.push("<" + listType + ">" + listItems.join("") + "</" + listType + ">"); listType = null; listItems = []; } };
    for (const line of lines) {
      if (line.trim().startsWith("```")) {
        if (inCode) { out.push('<pre class="mdcode">' + mdEsc(code.join("\n")) + "</pre>"); code = []; inCode = false; }
        else { flushPara(); flushList(); inCode = true; }
        continue;
      }
      if (inCode) { code.push(line); continue; }
      const t = line.trim();
      if (!t) { flushPara(); flushList(); continue; }
      const h = t.match(/^(#{1,6})\s+(.*)$/);
      if (h) { flushPara(); flushList(); const lvl = Math.min(h[1].length, 3); out.push("<h" + lvl + ' class="mdh">' + mdInline(mdEsc(h[2].replace(/#+\s*$/, ""))) + "</h" + lvl + ">"); continue; }
      if (/^([-*_])\1{2,}$/.test(t)) { flushPara(); flushList(); out.push("<hr>"); continue; }
      const ul = t.match(/^[-*+]\s+(.*)$/);
      if (ul) { flushPara(); if (listType !== "ul") { flushList(); listType = "ul"; } listItems.push("<li>" + mdInline(mdEsc(ul[1])) + "</li>"); continue; }
      const ol = t.match(/^\d+[.)]\s+(.*)$/);
      if (ol) { flushPara(); if (listType !== "ol") { flushList(); listType = "ol"; } listItems.push("<li>" + mdInline(mdEsc(ol[1])) + "</li>"); continue; }
      if (t.startsWith(">")) { flushPara(); flushList(); out.push("<blockquote>" + mdInline(mdEsc(t.replace(/^>\s?/, ""))) + "</blockquote>"); continue; }
      para.push(t);
    }
    flushPara(); flushList();
    if (inCode && code.length) out.push('<pre class="mdcode">' + mdEsc(code.join("\n")) + "</pre>");
    return out.join("\n");
  }

  async function openBookFile(slug, rel, label, rowEl) {
    const reader = document.getElementById("reader");
    const title = document.getElementById("readerTitle");
    title.textContent = label + " — carregando…";
    reader.textContent = "";
    document.querySelectorAll(".capRow.active, .docRow.active").forEach(e => e.classList.remove("active"));
    if (rowEl) rowEl.classList.add("active");
    try {
      const r = await fetch("/api/livros/" + encodeURIComponent(slug) + "/file?rel=" + encodeURIComponent(rel), {cache: "no-store"});
      const j = await r.json();
      if (!j.ok) throw new Error((j.error && j.error.message) || "falha");
      title.textContent = label + (j.data.truncated ? " (truncado)" : "");
      const content = j.data.content || "";
      if (rel.toLowerCase().endsWith(".md")) {
        reader.innerHTML = renderMarkdown(content) || "<p>(vazio)</p>";
      } else {
        reader.innerHTML = "";
        const pre = document.createElement("pre");
        pre.className = "mdcode";
        pre.style.whiteSpace = "pre-wrap";
        pre.textContent = content || "(vazio)";
        reader.appendChild(pre);
      }
      reader.scrollTop = 0;
    } catch (e) {
      title.textContent = label;
      reader.textContent = "Não foi possível ler este arquivo.";
    }
  }

  const analiseAttach = document.getElementById("analiseAttach");
  if (analiseAttach) analiseAttach.addEventListener("click", () => {
    switchView("chat");
    fileInput.click();
  });

  (async () => {
    await refreshStatus();
    await gateModeButtons();
    await restoreLastSession();
    await pollCalibrationOnce();
    setInterval(() => {
      if (!generating) refreshStatus();
    }, 2500);
    input.focus();
  })();
})();
