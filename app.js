(function() {
  'use strict';

  // ── DOM refs ──
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileName = document.getElementById('fileName');
  const jobDesc = document.getElementById('jobDesc');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const btnText = analyzeBtn.querySelector('.btn-text');
  const btnLoading = analyzeBtn.querySelector('.btn-loading');
  const errorMsg = document.getElementById('errorMsg');
  const resultPanel = document.getElementById('resultPanel');
  const cachedBadge = document.getElementById('cachedBadge');
  const apiBaseUrl = document.getElementById('apiBaseUrl');

  let selectedFile = null;

  // ── File selection ──
  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
  });

  function handleFile(file) {
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      showError('仅支持 PDF 格式的文件');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showError('文件大小不能超过 10MB');
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    errorMsg.hidden = true;
    updateButton();
  }

  function updateButton() {
    analyzeBtn.disabled = !selectedFile;
  }

  // ── Tab switching ──
  document.querySelector('.tabs').addEventListener('click', (e) => {
    if (!e.target.classList.contains('tab')) return;
    document.querySelectorAll('.tab, .tab-pane').forEach(el => el.classList.remove('active'));
    e.target.classList.add('active');
    const target = document.getElementById('tab' + e.target.dataset.tab.charAt(0).toUpperCase() + e.target.dataset.tab.slice(1));
    if (target) target.classList.add('active');
  });

  // ── Analyze ──
  analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    setLoading(true);
    errorMsg.hidden = true;
    resultPanel.hidden = true;

    try {
      const baseUrl = apiBaseUrl.value.trim() || 'http://localhost:8000';
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('job_description', jobDesc.value.trim());

      const res = await fetch(`${baseUrl}/api/v1/resume/upload`, {
        method: 'POST',
        body: formData,
      });

      const json = await res.json();

      if (!json.success) {
        showError(json.error || '分析失败，请稍后重试');
        return;
      }

      renderResult(json);
      resultPanel.hidden = false;
      resultPanel.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showError('网络错误：无法连接到后端服务，请检查 API 地址是否正确');
    } finally {
      setLoading(false);
    }
  });

  function setLoading(loading) {
    btnText.hidden = loading;
    btnLoading.hidden = !loading;
    analyzeBtn.disabled = loading;
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.hidden = false;
  }

  // ── Render ──
  function renderResult(json) {
    const data = json.data;
    cachedBadge.hidden = !json.cached;

    // Basic info
    document.getElementById('basicInfoGrid').innerHTML = renderInfoGrid([
      ['姓名', data.basic_info?.name],
      ['电话', data.basic_info?.phone],
      ['邮箱', data.basic_info?.email],
      ['地址', data.basic_info?.address],
    ]);

    // Job info
    document.getElementById('jobInfoGrid').innerHTML = renderInfoGrid([
      ['求职意向', data.job_intent?.position],
      ['期望薪资', data.job_intent?.expected_salary],
      ['工作年限', data.background?.work_years],
      ['学历背景', data.background?.education],
    ]);

    // Projects
    const projects = data.background?.projects || [];
    const projectsSection = document.getElementById('projectsSection');
    const projectsList = document.getElementById('projectsList');
    if (projects.length > 0) {
      projectsSection.hidden = false;
      projectsList.innerHTML = projects.map(p => `<li>${escapeHtml(p)}</li>`).join('');
    } else {
      projectsSection.hidden = true;
    }

    // Match result
    const matchTab = document.getElementById('matchTab');
    if (data.match_result) {
      matchTab.hidden = false;
      renderMatchResult(data.match_result);
    } else {
      matchTab.hidden = true;
    }

    // Raw text
    document.getElementById('rawText').textContent = data.raw_text || '';

    // Reset to first tab
    document.querySelectorAll('.tab, .tab-pane').forEach(el => el.classList.remove('active'));
    const firstTab = document.querySelector('.tab');
    if (firstTab) firstTab.classList.add('active');
    document.getElementById('tabBasic').classList.add('active');
  }

  function renderInfoGrid(items) {
    return items.map(([label, value]) => {
      const display = value || value === 0 ? escapeHtml(String(value)) : '<span class="empty">未填写</span>';
      return `<div class="info-item"><div class="info-label">${label}</div><div class="info-value${value ? '' : ' empty'}">${display}</div></div>`;
    }).join('');
  }

  function renderMatchResult(match) {
    document.getElementById('scoreNumber').textContent = match.overall_score ?? '-';
    document.getElementById('matchDetails').innerHTML = `
      <div class="match-stat">
        <div class="match-stat-value">${formatPercent(match.skill_match_rate)}</div>
        <div class="match-stat-label">技能匹配率</div>
      </div>
      <div class="match-stat">
        <div class="match-stat-value">${formatPercent(match.experience_relevance)}</div>
        <div class="match-stat-label">经验相关性</div>
      </div>
    `;

    // Keywords
    const matched = match.keywords_matched || [];
    const missing = match.keywords_missing || [];
    let kwHtml = '';
    if (matched.length > 0) {
      kwHtml += `<div class="section"><h3>已匹配关键词</h3><div class="keyword-tags">${matched.map(k => `<span class="tag matched">${escapeHtml(k)}</span>`).join('')}</div></div>`;
    }
    if (missing.length > 0) {
      kwHtml += `<div class="section"><h3>缺失关键词</h3><div class="keyword-tags">${missing.map(k => `<span class="tag missing">${escapeHtml(k)}</span>`).join('')}</div></div>`;
    }
    document.getElementById('matchDetails').innerHTML += kwHtml;

    // Analysis
    const analysisEl = document.getElementById('matchAnalysis');
    const analysisText = document.getElementById('analysisText');
    if (match.analysis) {
      analysisEl.hidden = false;
      analysisText.textContent = match.analysis;
    } else {
      analysisEl.hidden = true;
    }
  }

  function formatPercent(val) {
    if (val === null || val === undefined) return '-';
    return Math.round(val * 100) + '%';
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
})();
