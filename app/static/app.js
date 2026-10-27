const form = document.getElementById("screen-form");
const jobInput = document.getElementById("job-description");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const fileList = document.getElementById("file-list");
const errorBox = document.getElementById("error");
const submitBtn = document.getElementById("submit-btn");
const resultsSection = document.getElementById("results");

const ALLOWED = [".pdf", ".docx", ".txt"];
const SAMPLE_RESUMES = ["priya_sharma.txt", "rahul_verma.txt", "neha_gupta.txt"];

let files = [];

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function addFiles(newFiles) {
  for (const file of newFiles) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    const duplicate = files.some((f) => f.name === file.name);
    if (ALLOWED.includes(ext) && !duplicate) files.push(file);
  }
  renderFileList();
}

function renderFileList() {
  fileList.innerHTML = files
    .map(
      (file, i) => `
      <li>
        <span>${escapeHtml(file.name)}</span>
        <button type="button" data-index="${i}" title="Remove">&times;</button>
      </li>`
    )
    .join("");
}

fileList.addEventListener("click", (event) => {
  const index = event.target.dataset.index;
  if (index === undefined) return;
  files.splice(Number(index), 1);
  renderFileList();
});

fileInput.addEventListener("change", () => {
  addFiles(fileInput.files);
  fileInput.value = "";
});

["dragenter", "dragover"].forEach((name) =>
  dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.add("active");
  })
);

["dragleave", "drop"].forEach((name) =>
  dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.remove("active");
  })
);

dropzone.addEventListener("drop", (event) => addFiles(event.dataTransfer.files));

document.getElementById("sample-btn").addEventListener("click", async () => {
  jobInput.value = await fetch("/static/samples/job_description.txt").then((r) => r.text());

  files = [];
  for (const name of SAMPLE_RESUMES) {
    const text = await fetch(`/static/samples/${name}`).then((r) => r.text());
    files.push(new File([text], name, { type: "text/plain" }));
  }
  renderFileList();
  document.getElementById("screen").scrollIntoView({ behavior: "smooth" });
});

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  submitBtn.querySelector(".spinner").hidden = !loading;
  submitBtn.querySelector(".btn-label").textContent = loading ? "Analyzing resumes..." : "Screen candidates";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");

  if (jobInput.value.trim().length < 30) return showError("Please paste a complete job description.");
  if (files.length === 0) return showError("Please add at least one resume.");

  const data = new FormData();
  data.append("job_description", jobInput.value);
  files.forEach((file) => data.append("resumes", file));

  setLoading(true);
  try {
    const response = await fetch("/api/screen", { method: "POST", body: data });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Something went wrong.");
    renderResults(body);
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

function scoreColor(score) {
  if (score >= 70) return "var(--green)";
  if (score >= 40) return "var(--amber)";
  return "var(--red)";
}

function chips(skills, type) {
  if (skills.length === 0) return `<span class="chip none">None</span>`;
  return skills.map((s) => `<span class="chip ${type}">${escapeHtml(s)}</span>`).join("");
}

function bar(label, value) {
  return `
    <div>
      <div class="bar-label"><span>${label}</span><span>${value}%</span></div>
      <div class="bar"><div style="width: ${value}%"></div></div>
    </div>`;
}

function renderResults({ weights, results }) {
  const avg = results.reduce((sum, r) => sum + r.score, 0) / results.length;
  const strong = results.filter((r) => r.verdict === "Strong Match").length;

  document.getElementById("weights").textContent =
    `Weights: skills ${weights.skills * 100}% · similarity ${weights.similarity * 100}% · experience ${weights.experience * 100}%`;

  document.getElementById("stats").innerHTML = `
    <div class="stat"><div class="stat-value">${results.length}</div><div class="stat-label">Candidates screened</div></div>
    <div class="stat"><div class="stat-value">${avg.toFixed(1)}</div><div class="stat-label">Average score</div></div>
    <div class="stat"><div class="stat-value">${strong}</div><div class="stat-label">Strong matches</div></div>`;

  document.getElementById("result-list").innerHTML = results
    .map((r, i) => {
      const badgeClass = r.verdict.split(" ")[0].toLowerCase();
      const meta = [r.email, `${r.years_experience} yr${r.years_experience === 1 ? "" : "s"} experience`, r.filename].filter(Boolean);
      return `
      <article class="card" style="animation-delay: ${i * 80}ms">
        <div class="score-ring" style="--value: ${r.score}; --color: ${scoreColor(r.score)}">
          <span>${Math.round(r.score)}</span>
        </div>
        <div>
          <div class="card-head">
            <div>
              <h3><span class="rank">#${i + 1}</span>${escapeHtml(r.candidate)}</h3>
              <p class="meta">${meta.map(escapeHtml).join(" · ")}</p>
            </div>
            <span class="badge ${badgeClass}">${r.verdict}</span>
          </div>
          <div class="bars">
            ${bar("Skill match", r.breakdown.skills)}
            ${bar("Content similarity", r.breakdown.similarity)}
            ${bar("Experience", r.breakdown.experience)}
          </div>
          <div class="skills-row"><strong>Matched skills</strong><div class="chips">${chips(r.matched_skills, "match")}</div></div>
          <div class="skills-row"><strong>Missing skills</strong><div class="chips">${chips(r.missing_skills, "missing")}</div></div>
        </div>
      </article>`;
    })
    .join("");

  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth" });
}
