// -------------------------------------------------------
// MEDIQUEUE – Frontend API Bridge
// -------------------------------------------------------

const API = {
    async request(method, path, body) {
        const opts = {
            method,
            headers: { "Content-Type": "application/json" },
            credentials: "include",
        };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        return res.json();
    },
    get(path) { return this.request("GET", path); },
    post(path, body) { return this.request("POST", path, body); },
    put(path, body) { return this.request("PUT", path, body); },
    delete(path) { return this.request("DELETE", path); },
};

function showToast(message, isError = false) {
    const toast = document.createElement("div");
    toast.className = "functional-toast";
    const icon = isError ? "fa-circle-xmark" : "fa-circle-check";
    const color = isError ? "var(--danger-color)" : "var(--success-color)";
    toast.innerHTML = `<i class="fa-solid ${icon}" style="color:${color};"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => { toast.classList.remove("show"); setTimeout(() => toast.remove(), 300); }, 3500);
}
window.showToast = showToast;

function getInitials(name) {
    if (!name) return "?";
    return name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
}

function formatDate(str) {
    if (!str) return "-";
    return new Date(str).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function formatTime(str) {
    if (!str) return "-";
    const [h, m] = str.split(":");
    const hour = parseInt(h);
    return `${hour > 12 ? hour - 12 : hour}:${m} ${hour >= 12 ? "PM" : "AM"}`;
}

function statusBadge(status) {
    const map = {
        pending: "status-waiting",
        confirmed: "status-serving",
        completed: "status-completed",
        cancelled: "status-emergency",
        waiting: "status-waiting",
        in_progress: "status-serving",
        skipped: "status-emergency",
    };
    return `<span class="status-badge ${map[status] || ''}">${status}</span>`;
}

// -------------------------------------------------------
// TABS
// -------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const tabLinks = document.querySelectorAll(".nav-link[data-tab-target]");
    const tabContents = document.querySelectorAll(".tab-content");

    if (tabLinks.length > 0) {
        tabLinks[0].classList.add("active");
        document.getElementById(tabLinks[0].getAttribute("data-tab-target"))?.classList.add("active-content");
        tabLinks.forEach(link => {
            link.addEventListener("click", () => {
                tabLinks.forEach(l => l.classList.remove("active"));
                tabContents.forEach(c => c.classList.remove("active-content"));
                link.classList.add("active");
                document.getElementById(link.getAttribute("data-tab-target"))?.classList.add("active-content");
            });
        });
    }

    // Logout modal
    const logoutBtn = document.getElementById("btn-logout");
    const logoutModal = document.getElementById("logout-modal");
    const cancelLogoutBtn = document.getElementById("cancel-logout");
    const confirmLogoutBtn = document.getElementById("confirm-logout");
    if (logoutBtn && logoutModal) {
        logoutBtn.addEventListener("click", () => logoutModal.classList.add("show-modal"));
        cancelLogoutBtn?.addEventListener("click", () => logoutModal.classList.remove("show-modal"));
        confirmLogoutBtn?.addEventListener("click", async () => {
            await API.post("/api/logout");
            window.location.href = "login.html";
        });
    }

    // System clock
    const sysTimeEl = document.getElementById("sys-time");
    if (sysTimeEl) {
        setInterval(() => { sysTimeEl.textContent = new Date().toLocaleTimeString(); }, 1000);
        sysTimeEl.textContent = new Date().toLocaleTimeString();
    }

    // Route to the right page init
    const page = window.location.pathname.split("/").pop() || "index.html";
    if (page === "login.html") initLogin();
    else if (page === "register.html") initRegister();
    else if (page === "patient.html") initPatientDashboard();
    else if (page === "doctor.html") initDoctorDashboard();
    else if (page === "admin.html") initAdminDashboard();
});

// -------------------------------------------------------
// LOGIN
// -------------------------------------------------------
function initLogin() {
    // Role tabs
    const tabs = document.querySelectorAll(".login-tab");
    const roleInput = document.getElementById("selected-role");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            roleInput.value = tab.dataset.role;
        });
    });

    document.getElementById("login-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const role = document.getElementById("selected-role").value;
        const btn = document.getElementById("login-btn");
        const errorEl = document.getElementById("login-error");
        const errorText = document.getElementById("error-text");

        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Logging in...';
        errorEl.style.display = "none";

        const data = await API.post("/api/login", { email, password });
        btn.disabled = false;
        btn.innerHTML = 'Secure Login <i class="fa-solid fa-lock"></i>';

        if (data.error) {
            errorText.textContent = data.error;
            errorEl.style.display = "block";
            return;
        }

        if (data.user.role !== role) {
            errorText.textContent = `This account is registered as '${data.user.role}', not '${role}'.`;
            errorEl.style.display = "block";
            return;
        }

        window.location.href = `${data.user.role}.html`;
    });
}

// -------------------------------------------------------
// REGISTER
// -------------------------------------------------------
function initRegister() {
    const tabs = document.querySelectorAll(".login-tab");
    const roleInput = document.getElementById("selected-role");
    const patientFields = document.getElementById("patient-fields");
    const doctorFields = document.getElementById("doctor-fields");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const role = tab.dataset.role;
            roleInput.value = role;
            patientFields.style.display = role === "patient" ? "block" : "none";
            doctorFields.style.display = role === "doctor" ? "block" : "none";
        });
    });

    // Load departments for doctor registration
    API.get("/api/departments").then(data => {
        const sel = document.getElementById("reg-department");
        if (sel && data.departments) {
            sel.innerHTML = data.departments.map(d => `<option value="${d.id}">${d.name}</option>`).join("");
            if (!data.departments.length) sel.innerHTML = '<option value="">No departments yet</option>';
        }
    });

    document.getElementById("register-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const role = roleInput.value;
        const btn = document.getElementById("reg-btn");
        const errorEl = document.getElementById("reg-error");
        const errorText = document.getElementById("reg-error-text");

        const payload = {
            name: document.getElementById("reg-name").value.trim(),
            email: document.getElementById("reg-email").value.trim(),
            password: document.getElementById("reg-password").value,
            phone: document.getElementById("reg-phone").value.trim(),
            role,
        };

        if (role === "patient") {
            payload.date_of_birth = document.getElementById("reg-dob").value;
            payload.gender = document.getElementById("reg-gender").value;
            payload.blood_group = document.getElementById("reg-blood").value;
            payload.address = document.getElementById("reg-address").value;
        } else if (role === "doctor") {
            payload.department_id = document.getElementById("reg-department").value;
            payload.specialization = document.getElementById("reg-specialization").value;
            payload.qualification = document.getElementById("reg-qualification").value;
            payload.experience_years = parseInt(document.getElementById("reg-experience").value) || 0;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Creating account...';
        errorEl.style.display = "none";

        const data = await API.post("/api/register", payload);
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';

        if (data.error) {
            errorText.textContent = data.error;
            errorEl.style.display = "block";
            return;
        }

        showToast("Account created! Please log in.");
        setTimeout(() => window.location.href = "login.html", 1500);
    });
}

// -------------------------------------------------------
// PATIENT DASHBOARD
// -------------------------------------------------------
async function initPatientDashboard() {
    const meData = await API.get("/api/me");
    if (meData.error) { window.location.href = "login.html"; return; }
    if (meData.user.role !== "patient") { window.location.href = `${meData.user.role}.html`; return; }

    const name = meData.user.name;
    const hour = new Date().getHours();
    const greeting = hour < 12 ? "Good Morning" : hour < 18 ? "Good Afternoon" : "Good Evening";
    document.getElementById("greeting-text").textContent = `${greeting}, ${name.split(" ")[0]}`;
    document.getElementById("user-name-display").textContent = name;
    const av = document.getElementById("user-avatar");
    if (av) av.textContent = getInitials(name);

    await loadDepartments();
    await loadPatientBookings();
    await loadPatientQueue();
    await loadPatientAppointments();
    await loadPatientProfile();

    document.getElementById("book-dept").addEventListener("change", (e) => {
        const dept = e.target.options[e.target.selectedIndex];
        loadDoctorsByDept(dept.dataset.id);
    });

    document.getElementById("booking-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const docSel = document.getElementById("book-doc");
        const doctor_id = docSel.value;
        const appointment_date = document.getElementById("book-date").value;
        const appointment_time = document.getElementById("book-time").value;
        const reason = document.getElementById("book-symptoms").value;
        const btn = document.getElementById("book-appointment-btn");

        if (!appointment_date) { showToast("Please select a date.", true); return; }
        if (!doctor_id) { showToast("Please select a doctor.", true); return; }

        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Booking...';

        const data = await API.post("/api/appointments", { doctor_id: parseInt(doctor_id), appointment_date, appointment_time, reason });
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-regular fa-paper-plane"></i> Request Booking';

        if (data.error) { showToast(data.error, true); return; }

        showToast(`Appointment booked! Queue number: ${data.queue_number}`);
        await loadPatientBookings();
        await loadPatientQueue();
        await loadPatientAppointments();
    });

    document.getElementById("profile-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = await API.put("/api/patients/profile", {
            name: document.getElementById("profile-name").value,
            phone: document.getElementById("profile-phone").value,
            date_of_birth: document.getElementById("profile-dob").value,
            gender: document.getElementById("profile-gender").value,
            blood_group: document.getElementById("profile-blood").value,
            address: document.getElementById("profile-address").value,
            medical_history: document.getElementById("profile-history").value,
        });
        if (data.error) { showToast(data.error, true); return; }
        showToast("Profile updated successfully!");
    });
}

async function loadDepartments() {
    const data = await API.get("/api/departments");
    const sel = document.getElementById("book-dept");
    if (!sel) return;
    if (!data.departments || !data.departments.length) {
        sel.innerHTML = '<option value="">No departments available</option>';
        return;
    }
    sel.innerHTML = data.departments.map(d => `<option value="${d.name}" data-id="${d.id}">${d.name}</option>`).join("");
    const firstDept = sel.options[0];
    if (firstDept) loadDoctorsByDept(firstDept.dataset.id);
}

async function loadDoctorsByDept(deptId) {
    const sel = document.getElementById("book-doc");
    if (!sel) return;
    sel.innerHTML = '<option>Loading...</option>';
    const url = deptId ? `/api/doctors?department_id=${deptId}` : "/api/doctors";
    const data = await API.get(url);
    if (!data.doctors || !data.doctors.length) {
        sel.innerHTML = '<option value="">No doctors available</option>';
        return;
    }
    sel.innerHTML = data.doctors.map(d => `<option value="${d.id}">${d.name} – ${d.specialization || ''}</option>`).join("");
}

async function loadPatientBookings() {
    const data = await API.get("/api/patients/appointments");
    const container = document.getElementById("active-bookings-list");
    if (!container) return;
    const active = (data.appointments || []).filter(a => a.status === "pending" || a.status === "confirmed");
    if (!active.length) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 1rem;">No active bookings.</p>';
        return;
    }
    container.innerHTML = active.map(a => `
        <div class="queue-item" style="border: 1px solid rgba(50, 215, 75, 0.3);">
            <div class="queue-info">
                <div class="avatar" style="background: rgba(255,255,255,0.1); font-size: 0.9rem;"><i class="fa-solid fa-stethoscope"></i></div>
                <div class="patient-details">
                    <h4>${a.doctor_name || 'Doctor'}</h4>
                    <p>${a.department_name || ''} • ${formatDate(a.appointment_date)}, ${formatTime(a.appointment_time)}</p>
                </div>
            </div>
            <div style="display:flex; gap:0.5rem; align-items:center;">
                ${statusBadge(a.status)}
                ${a.status === 'pending' ? `<button class="btn btn-danger" style="padding:0.3rem 0.8rem; font-size:0.8rem;" onclick="cancelAppointment(${a.id})">Cancel</button>` : ''}
            </div>
        </div>
    `).join("");
}

window.cancelAppointment = async (id) => {
    const data = await API.put(`/api/appointments/${id}/cancel`);
    if (data.error) { showToast(data.error, true); return; }
    showToast("Appointment cancelled.");
    await loadPatientBookings();
    await loadPatientAppointments();
};

async function loadPatientQueue() {
    const data = await API.get("/api/queue/patient");
    const panel = document.getElementById("queue-status-panel");
    if (!panel) return;
    if (!data.queue || !data.queue.length) {
        panel.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No active queue entry for today.</p>';
        return;
    }
    const q = data.queue[0];
    panel.innerHTML = `
        <p style="text-align: center; color: var(--text-muted); font-size: 0.9rem;">${q.doctor_name} (${q.specialization || ''})</p>
        <div class="stat-card" style="margin: 2rem 0;">
            <div class="stat-label">Your Token</div>
            <div class="stat-value">T-${q.queue_number}</div>
        </div>
        <div class="dashboard-grid col-2" style="margin-top: 1rem; gap: 1rem;">
            <div class="stat-card" style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                <div class="stat-label" style="font-size: 0.7rem;">Status</div>
                <div style="margin-top:0.5rem;">${statusBadge(q.status)}</div>
            </div>
            <div class="stat-card" style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                <div class="stat-label" style="font-size: 0.7rem;">Patients Ahead</div>
                <div class="stat-value" style="font-size: 1.8rem; margin: 0.5rem 0;">${q.patients_ahead}</div>
            </div>
        </div>
        <div style="margin-top: 1.5rem; text-align: center;">
            ${q.status === 'waiting' ? '<span class="status-badge status-waiting" style="padding: 0.8rem 2rem;">Wait in Reception Area</span>' : ''}
            ${q.status === 'in_progress' ? '<span class="status-badge status-serving" style="padding: 0.8rem 2rem;">Please proceed to the doctor</span>' : ''}
        </div>
    `;
}

async function loadPatientAppointments() {
    const data = await API.get("/api/patients/appointments");
    const tbody = document.getElementById("appointments-table-body");
    if (!tbody) return;
    if (!data.appointments || !data.appointments.length) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">No appointments found.</td></tr>';
        return;
    }
    tbody.innerHTML = data.appointments.map(a => `
        <tr>
            <td>${formatDate(a.appointment_date)} – ${formatTime(a.appointment_time)}</td>
            <td>${a.doctor_name || '-'}</td>
            <td>${a.department_name || '-'}</td>
            <td>${statusBadge(a.status)}</td>
            <td>${a.notes ? `<span style="color:var(--text-muted);font-size:0.85rem;">${a.notes}</span>` : '-'}</td>
        </tr>
    `).join("");
}

async function loadPatientProfile() {
    const data = await API.get("/api/patients/profile");
    if (data.error) return;
    const p = data.patient;
    const f = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
    f("profile-name", p.name);
    f("profile-phone", p.phone);
    f("profile-dob", p.date_of_birth ? p.date_of_birth.split("T")[0] : "");
    f("profile-gender", p.gender);
    f("profile-blood", p.blood_group);
    f("profile-address", p.address);
    f("profile-history", p.medical_history);
    const pId = document.getElementById("patient-id-display");
    if (pId) pId.textContent = `Patient ID: #${p.id}-PT`;
}

// -------------------------------------------------------
// DOCTOR DASHBOARD
// -------------------------------------------------------
let currentQueueId = null;

async function initDoctorDashboard() {
    const meData = await API.get("/api/me");
    if (meData.error) { window.location.href = "login.html"; return; }
    if (meData.user.role !== "doctor") { window.location.href = `${meData.user.role}.html`; return; }

    const name = meData.user.name;
    document.getElementById("greeting-text").textContent = `Welcome, Dr. ${name.split(" ")[0]}`;
    document.getElementById("user-name-display").textContent = `Dr. ${name}`;
    const av = document.getElementById("user-avatar");
    if (av) av.textContent = getInitials(name);

    const profile = await API.get("/api/doctors/profile");
    if (profile.doctor) {
        const dept = document.getElementById("doctor-dept-display");
        if (dept) dept.textContent = `${profile.doctor.department_name || 'Department'} • Shift: 09:00 AM - 05:00 PM`;
    }

    await loadDoctorQueue();
    await loadDoctorAppointments();

    document.getElementById("next-token-btn")?.addEventListener("click", async () => {
        const firstWaiting = document.querySelector(".queue-item[data-queue-id][data-status='waiting']");
        if (!firstWaiting) { showToast("No patients waiting in queue."); return; }
        const qid = firstWaiting.dataset.queueId;
        const data = await API.put(`/api/queue/${qid}/next`);
        if (data.error) { showToast(data.error, true); return; }
        currentQueueId = parseInt(qid);
        showToast(`Now calling Token #${firstWaiting.dataset.queueNum}`);
        await loadDoctorQueue();
    });

    document.getElementById("skip-btn")?.addEventListener("click", async () => {
        const inProgress = document.querySelector(".queue-item[data-queue-id][data-status='waiting']");
        if (!inProgress && !currentQueueId) { showToast("No patient to skip."); return; }
        const targetId = currentQueueId || inProgress?.dataset.queueId;
        if (!targetId) return;
        const data = await API.put(`/api/queue/${targetId}/skip`);
        if (data.error) { showToast(data.error, true); return; }
        currentQueueId = null;
        showToast("Patient skipped.");
        await loadDoctorQueue();
    });

    document.getElementById("complete-btn")?.addEventListener("click", async () => {
        if (!currentQueueId) { showToast("No active patient to complete."); return; }
        const data = await API.put(`/api/queue/${currentQueueId}/complete`);
        if (data.error) { showToast(data.error, true); return; }
        currentQueueId = null;
        showToast("Patient visit completed!");
        await loadDoctorQueue();
    });

    document.getElementById("appointment-status-filter")?.addEventListener("change", () => loadDoctorAppointments());

    const scheduleDateFilter = document.getElementById("schedule-date-filter");
    if (scheduleDateFilter) {
        scheduleDateFilter.value = new Date().toISOString().split("T")[0];
        scheduleDateFilter.addEventListener("change", () => loadDoctorAppointments("schedule"));
        loadDoctorAppointments("schedule");
    }
}

async function loadDoctorQueue() {
    const data = await API.get("/api/queue/doctor");
    const container = document.getElementById("doctor-queue-list");
    if (!container) return;

    if (!data.queue || !data.queue.length) {
        container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem;">Queue is empty today.</p>';
        updateDoctorStats(0, 0, 0);
        resetActivePatientPanel();
        return;
    }

    const total = data.queue.length;
    const completed = data.queue.filter(q => q.status === "completed").length;
    const waiting = data.queue.filter(q => q.status === "waiting").length;
    updateDoctorStats(total, completed, waiting);

    container.innerHTML = data.queue.map(q => {
        let borderStyle = "";
        let badgeClass = "status-waiting";
        if (q.status === "in_progress") { borderStyle = "border-color: var(--accent-color); background: rgba(0,240,255,0.05);"; badgeClass = "status-serving"; }
        else if (q.status === "completed") { borderStyle = "border-color: rgba(50,215,75,0.3);"; badgeClass = "status-completed"; }
        else if (q.status === "skipped") { borderStyle = "border-color: rgba(255,59,48,0.3);"; badgeClass = "status-emergency"; }
        return `
            <div class="queue-item ${q.status === "in_progress" ? "active" : ""}" data-queue-id="${q.id}" data-status="${q.status}" data-queue-num="${q.queue_number}" style="${borderStyle}; flex-direction:column; align-items:flex-start; gap:0.5rem;">
                <div style="display:flex; justify-content:space-between; width:100%;">
                    <span class="token-badge">T-${q.queue_number}</span>
                    <span class="status-badge ${badgeClass}">${q.status === "in_progress" ? "Active" : q.status}</span>
                </div>
                <div class="patient-details">
                    <h4>${q.patient_name}</h4>
                    <p>${q.reason || 'General consultation'} • ${formatTime(q.appointment_time)}</p>
                </div>
            </div>
        `;
    }).join("");

    const active = data.queue.find(q => q.status === "in_progress");
    if (active) {
        currentQueueId = active.id;
        updateActivePatientPanel(active);
    } else {
        resetActivePatientPanel();
    }
}

function updateDoctorStats(total, completed, remaining) {
    const t = document.getElementById("stat-total");
    const c = document.getElementById("stat-completed");
    const r = document.getElementById("stat-remaining");
    if (t) t.textContent = total;
    if (c) c.textContent = completed;
    if (r) r.textContent = remaining;
}

function updateActivePatientPanel(q) {
    const panel = document.getElementById("active-patient-panel");
    if (!panel) return;
    panel.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <h1 style="color:var(--accent-color); font-size:1.8rem;">${q.patient_name} (T-${q.queue_number})</h1>
                <p style="color:var(--text-muted);">Check-in: ${new Date(q.check_in_time).toLocaleTimeString()}</p>
                <p style="color:var(--text-muted); margin-top:0.5rem;">Reason: ${q.reason || 'General consultation'}</p>
            </div>
            <span class="status-badge status-serving">Currently Serving</span>
        </div>
    `;
}

function resetActivePatientPanel() {
    const panel = document.getElementById("active-patient-panel");
    if (panel) panel.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem;">No active patient. Call next token to begin.</p>';
}

async function loadDoctorAppointments(mode = "list") {
    const statusFilter = document.getElementById("appointment-status-filter")?.value;
    const dateFilter = document.getElementById("schedule-date-filter")?.value;
    let url = "/api/doctors/appointments";
    const params = [];
    if (statusFilter && mode === "list") params.push(`status=${statusFilter}`);
    if (dateFilter && mode === "schedule") params.push(`date=${dateFilter}`);
    if (params.length) url += "?" + params.join("&");

    const data = await API.get(url);

    if (mode === "schedule") {
        const tbody = document.getElementById("schedule-body");
        if (!tbody) return;
        if (!data.appointments || !data.appointments.length) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">No appointments for this date.</td></tr>';
            return;
        }
        tbody.innerHTML = data.appointments.map(a => `
            <tr>
                <td>${formatTime(a.appointment_time)}</td>
                <td>${a.patient_name}</td>
                <td>${a.reason || '-'}</td>
                <td>${statusBadge(a.status)}</td>
            </tr>
        `).join("");
    } else {
        const tbody = document.getElementById("doctor-appointments-body");
        if (!tbody) return;
        if (!data.appointments || !data.appointments.length) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">No appointments found.</td></tr>';
            return;
        }
        tbody.innerHTML = data.appointments.map(a => `
            <tr>
                <td>${a.patient_name}</td>
                <td>${formatDate(a.appointment_date)}, ${formatTime(a.appointment_time)}</td>
                <td>${a.reason || '-'}</td>
                <td>${statusBadge(a.status)}</td>
                <td>
                    ${a.status === "pending" ? `<button class="btn btn-secondary" style="padding:0.3rem 0.8rem;font-size:0.8rem;" onclick="updateAppointmentStatus(${a.id},'confirmed')">Confirm</button>` : ''}
                    ${a.status !== "completed" && a.status !== "cancelled" ? `<button class="btn btn-danger" style="padding:0.3rem 0.8rem;font-size:0.8rem;" onclick="updateAppointmentStatus(${a.id},'cancelled')">Cancel</button>` : ''}
                </td>
            </tr>
        `).join("");
    }
}

window.updateAppointmentStatus = async (id, status) => {
    const data = await API.put(`/api/doctors/appointments/${id}/status`, { status });
    if (data.error) { showToast(data.error, true); return; }
    showToast(`Appointment ${status}.`);
    await loadDoctorAppointments();
};

// -------------------------------------------------------
// ADMIN DASHBOARD
// -------------------------------------------------------
async function initAdminDashboard() {
    const meData = await API.get("/api/me");
    if (meData.error) { window.location.href = "login.html"; return; }
    if (meData.user.role !== "admin") { window.location.href = `${meData.user.role}.html`; return; }

    const name = meData.user.name;
    document.getElementById("user-name-display").textContent = name;
    const av = document.getElementById("user-avatar");
    if (av) av.textContent = getInitials(name);

    await adminLoadStats();
    await adminLoadDoctors();
    await adminLoadAppointments();
    await adminLoadQueue();

    document.getElementById("search-doctor")?.addEventListener("input", (e) => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll("#doctor-roster-table tbody tr").forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? "" : "none";
        });
    });

    document.getElementById("admin-apt-date")?.addEventListener("change", adminLoadAppointments);
    document.getElementById("admin-apt-status")?.addEventListener("change", adminLoadAppointments);
}

window.adminLoadStats = async function() {
    const data = await API.get("/api/admin/stats");
    if (data.error) return;
    const s = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    s("stat-total-patients", data.total_patients);
    s("stat-total-doctors", data.total_doctors);
    s("stat-today-appointments", data.today_appointments);
    s("stat-active-queue", data.active_queue);
};

async function adminLoadDoctors() {
    const data = await API.get("/api/admin/doctors");
    const tbody = document.getElementById("doctor-roster-body");
    if (!tbody) return;
    if (!data.doctors || !data.doctors.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No doctors registered.</td></tr>';
        return;
    }
    tbody.innerHTML = data.doctors.map(d => `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:0.8rem;">
                    <div class="avatar" style="width:30px;height:30px;font-size:0.9rem;">${getInitials(d.name)}</div>
                    <strong>${d.name}</strong>
                </div>
            </td>
            <td>${d.department_name || '-'}</td>
            <td>${d.specialization || '-'}</td>
            <td>${d.experience_years || 0} yrs</td>
            <td>${d.available ? '<span class="status-badge status-completed">Active</span>' : '<span class="status-badge status-emergency">Inactive</span>'}</td>
            <td>
                <button class="btn btn-danger" style="padding:0.4rem;border:none;" onclick="adminDeleteDoctor(${d.id})"><i class="fa-solid fa-trash"></i></button>
            </td>
        </tr>
    `).join("");
}

window.adminDeleteDoctor = async (id) => {
    if (!confirm("Are you sure you want to remove this doctor?")) return;
    const data = await API.delete(`/api/admin/doctors/${id}`);
    if (data.error) { showToast(data.error, true); return; }
    showToast("Doctor removed.");
    await adminLoadDoctors();
    await adminLoadStats();
};

async function adminLoadAppointments() {
    const date = document.getElementById("admin-apt-date")?.value || "";
    const status = document.getElementById("admin-apt-status")?.value || "";
    let url = "/api/admin/appointments";
    const params = [];
    if (date) params.push(`date=${date}`);
    if (status) params.push(`status=${status}`);
    if (params.length) url += "?" + params.join("&");

    const data = await API.get(url);
    const tbody = document.getElementById("admin-appointments-body");
    if (!tbody) return;
    if (!data.appointments || !data.appointments.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No appointments found.</td></tr>';
        return;
    }
    tbody.innerHTML = data.appointments.map(a => `
        <tr>
            <td>${a.patient_name}</td>
            <td>${a.doctor_name}</td>
            <td>${a.department_name || '-'}</td>
            <td>${formatDate(a.appointment_date)}, ${formatTime(a.appointment_time)}</td>
            <td>${a.reason || '-'}</td>
            <td>${statusBadge(a.status)}</td>
        </tr>
    `).join("");
}

window.adminLoadQueue = async function() {
    const data = await API.get("/api/admin/queue");
    const tbody = document.getElementById("admin-queue-body");
    if (!tbody) return;
    if (!data.queue || !data.queue.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No queue entries for today.</td></tr>';
        return;
    }
    tbody.innerHTML = data.queue.map(q => `
        <tr>
            <td><span class="token-badge" style="font-size:0.9rem;">T-${q.queue_number}</span></td>
            <td>${q.patient_name}</td>
            <td>${q.doctor_name}</td>
            <td>${q.department_name || '-'}</td>
            <td>${statusBadge(q.status)}</td>
            <td>${q.check_in_time ? new Date(q.check_in_time).toLocaleTimeString() : '-'}</td>
        </tr>
    `).join("");
};
