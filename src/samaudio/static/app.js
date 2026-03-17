const speakerForm = document.getElementById("speaker-form");
const meetingForm = document.getElementById("meeting-form");
const speakerList = document.getElementById("speaker-list");
const reportsList = document.getElementById("reports-list");
const speakerCount = document.getElementById("speaker-count");
const speakerFeedback = document.getElementById("speaker-feedback");
const meetingFeedback = document.getElementById("meeting-feedback");
const jobStatus = document.getElementById("job-status");
const refreshReportsButton = document.getElementById("refresh-reports");

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = "Request failed";
    try {
      const payload = await response.json();
      message = payload.detail || JSON.stringify(payload);
    } catch (_error) {
      message = await response.text();
    }
    throw new Error(message);
  }
  return response.json();
}

function renderSpeakers(speakers) {
  speakerCount.textContent = `${speakers.length} speakers`;
  if (!speakers.length) {
    speakerList.innerHTML = `<div class="speaker-item"><strong>まだ登録されていません</strong><div class="meta">まずは話者サンプルを登録してください。</div></div>`;
    return;
  }

  speakerList.innerHTML = speakers
    .map(
      (speaker) => `
        <div class="speaker-item">
          <strong>${speaker.display_name}</strong>
          <div class="meta">ID: ${speaker.speaker_id}</div>
          <div class="meta">サンプル数: ${speaker.sample_count}</div>
        </div>
      `,
    )
    .join("");
}

function renderReports(reports) {
  if (!reports.length) {
    reportsList.innerHTML = `<div class="report-item"><strong>まだ解析結果がありません</strong><div class="meta">会議音声をアップロードするとここに表示されます。</div></div>`;
    return;
  }

  reportsList.innerHTML = reports
    .map((report) => {
      const previewSegments = report.segments.slice(0, 4);
      const segmentHtml = previewSegments
        .map(
          (segment) => `
            <div class="segment">
              <strong>${segment.speaker_label}</strong>
              <div class="meta">${segment.start_ts} - ${segment.end_ts}</div>
              <div>${segment.text || "(no speech recognized)"}</div>
            </div>
          `,
        )
        .join("");

      return `
        <div class="report-item">
          <strong>${report.id}</strong>
          <div class="meta">元音声: ${report.meeting_audio}</div>
          <div class="meta">生成日時: ${report.generated_at}</div>
          <div class="meta">区間数: ${report.segment_count}</div>
          <div class="segments">${segmentHtml}</div>
        </div>
      `;
    })
    .join("");
}

async function loadSpeakers() {
  const speakers = await fetchJson("/api/speakers");
  renderSpeakers(speakers);
}

async function loadReports() {
  const reports = await fetchJson("/api/reports");
  renderReports(reports);
}

async function pollJob(jobId) {
  jobStatus.textContent = "解析ジョブを開始しました。";
  while (true) {
    const job = await fetchJson(`/api/jobs/${jobId}`);
    if (job.status === "queued") {
      jobStatus.textContent = `待機中: ${job.filename}`;
    } else if (job.status === "running") {
      jobStatus.textContent = `解析中: ${job.filename}`;
    } else if (job.status === "completed") {
      jobStatus.textContent = `完了: ${job.filename} (${job.segment_count} 区間)`;
      await loadReports();
      break;
    } else if (job.status === "failed") {
      jobStatus.textContent = `失敗: ${job.error}`;
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 3000));
  }
}

speakerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  speakerFeedback.textContent = "登録中です...";
  const formData = new FormData(speakerForm);
  try {
    const result = await fetchJson("/api/speakers", {
      method: "POST",
      body: formData,
    });
    speakerFeedback.textContent = `${result.display_name} を登録しました。`;
    speakerForm.reset();
    await loadSpeakers();
  } catch (error) {
    speakerFeedback.textContent = `登録に失敗しました: ${error.message}`;
  }
});

meetingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  meetingFeedback.textContent = "アップロード中です...";
  jobStatus.textContent = "";
  const formData = new FormData(meetingForm);
  try {
    const result = await fetchJson("/api/meetings", {
      method: "POST",
      body: formData,
    });
    meetingFeedback.textContent = `受付完了: ${result.job_id}`;
    meetingForm.reset();
    await pollJob(result.job_id);
  } catch (error) {
    meetingFeedback.textContent = `解析を開始できませんでした: ${error.message}`;
  }
});

refreshReportsButton.addEventListener("click", async () => {
  await loadReports();
});

window.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadSpeakers(), loadReports()]);
});
