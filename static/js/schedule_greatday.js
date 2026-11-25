// JavaScript logic for Engineering Schedule GreatDay Format & Rolling Shifts
document.addEventListener('DOMContentLoaded', () => {
  const $ = (id) => document.getElementById(id);

  // State
  const now = new Date();
  let currentYear = $('inp-year') ? parseInt($('inp-year').value, 10) : 2026;
  let currentMonth = $('sel-month') ? parseInt($('sel-month').value, 10) : 11;
  let rotationStep = 0;
  let scheduleData = null;
  let staffConfig = null;
  let activeEditingCell = null;

  // Set selectors to current year and month if valid
  if ($('sel-month')) $('sel-month').value = String(currentMonth);
  if ($('inp-year')) $('inp-year').value = String(currentYear);

  // Set today date pill
  const todayOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const todayPill = $('today-pill');
  if (todayPill) {
    const textSpan = todayPill.querySelector('.today-text');
    const dateFormatted = now.toLocaleDateString('id-ID', todayOptions);
    if (textSpan) textSpan.textContent = dateFormatted;
    else todayPill.textContent = dateFormatted;
  }

  function showToast(message, isError = false) {
    const toast = $('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.style.background = isError ? '#991b1b' : '#0f172a';
    toast.hidden = false;
    setTimeout(() => { toast.hidden = true; }, 4000);
  }

  function getShiftClass(shift) {
    if (!shift) return '';
    const clean = String(shift).toLowerCase().trim().replace(/\s+/g, '-');
    return `shift-${clean}`;
  }

  function updateMetrics(data) {
    let regulerCount = 0;
    let shiftCount = 0;
    let dwCount = 0;
    if (data && data.groups) {
      data.groups.forEach(g => {
        if (g.group_key === 'reguler') regulerCount = g.rows.length;
        if (g.group_key === 'shift') shiftCount = g.rows.length;
        if (g.group_key === 'daily_worker') dwCount = g.rows.length;
      });
    }
    const total = regulerCount + shiftCount + dwCount;
    if ($('stat-total-staff')) $('stat-total-staff').textContent = total;
    if ($('stat-reguler')) $('stat-reguler').textContent = regulerCount;
    if ($('stat-shift')) $('stat-shift').textContent = shiftCount;
    if ($('stat-dw')) $('stat-dw').textContent = dwCount;
    if ($('stat-days')) $('stat-days').textContent = data.total_days || 30;
    if ($('stat-days-label')) $('stat-days-label').textContent = `${data.month_name} ${data.year}`;
  }

  // Load staff configuration from localStorage or backend defaults
  async function initStaffConfig() {
    const saved = localStorage.getItem('tar_engineering_staff_config_v3');
    if (saved) {
      try {
        staffConfig = JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved staff config:', e);
      }
    }

    if (!staffConfig) {
      try {
        const res = await fetch('/api/schedule/defaults');
        const json = await res.json();
        staffConfig = json.default_data;
        localStorage.setItem('tar_engineering_staff_config_v3', JSON.stringify(staffConfig));
      } catch (e) {
        showToast('Gagal memuat daftar staff: ' + e.message, true);
      }
    }
  }

  // Load and render schedule grid in GreatDay format
  async function loadSchedule() {
    if ($('sel-month')) currentMonth = parseInt($('sel-month').value, 10);
    if ($('inp-year')) currentYear = parseInt($('inp-year').value, 10);

    try {
      const res = await fetch('/api/schedule/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: currentYear,
          month: currentMonth,
          shift_rotation_step: rotationStep,
          format: 'greatday',
          staff_data: staffConfig
        })
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Gagal membuat jadwal.');

      scheduleData = json.data;
      renderScheduleTable(scheduleData);
      updateMetrics(scheduleData);

      if ($('schedule-table-title')) {
        $('schedule-table-title').textContent = `JADWAL KERJA ENGINEERING DEPARTMENT (GREATDAY) - BULAN ${scheduleData.month_name} ${scheduleData.year}`;
      }
      if ($('rotation-badge')) {
        $('rotation-badge').textContent = rotationStep === 0 ? 'Standar (0)' : `Rotasi: +${rotationStep} Hari`;
      }

      // Render Holidays Banner
      const holidayBanner = $('holidays-banner-container');
      if (holidayBanner) {
        if (scheduleData.holidays && scheduleData.holidays.length > 0) {
          holidayBanner.hidden = false;
          holidayBanner.className = 'holiday-banner';
          holidayBanner.innerHTML = `
            <span style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
              <svg viewBox="0 0 24 24" style="width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Hari Libur Nasional:
            </span>
            ${scheduleData.holidays.map(h => `
              <span class="holiday-badge" title="${h.day_name}, ${h.day} ${scheduleData.month_name}">
                <strong>${h.day} ${scheduleData.month_name}</strong>: ${escapeHtml(h.name)}
              </span>
            `).join('')}
          `;
        } else {
          holidayBanner.hidden = true;
          holidayBanner.innerHTML = '';
        }
      }
    } catch (err) {
      showToast(err.message, true);
    }
  }

  // Render Schedule Matrix Table for GreatDay
  function renderScheduleTable(data) {
    const thead = $('schedule-thead');
    const tbody = $('schedule-tbody');
    if (!thead || !tbody) return;

    thead.innerHTML = '';
    tbody.innerHTML = '';

    const days = data.days || [];

    // Header Row 1: NO, TITLE, NAME, Day Names (Sn, Sl, Rb, ...)
    const trHead1 = document.createElement('tr');
    trHead1.innerHTML = `
      <th style="width: 38px; min-width: 38px; text-align: center;" rowspan="2">NO</th>
      <th style="width: 170px; min-width: 170px; text-align: left; padding: 5px 8px;" rowspan="2">TITLE</th>
      <th style="width: 180px; min-width: 180px; text-align: left; padding: 5px 8px;" rowspan="2">NAME</th>
    `;
    days.forEach(d => {
      const th = document.createElement('th');
      th.className = d.is_holiday ? 'holiday-col' : (d.is_weekend ? 'weekend-col' : '');
      th.style.textAlign = 'center';
      th.style.padding = '5px 2px';
      th.style.fontSize = '10px';
      th.style.minWidth = '54px';
      th.style.width = '54px';
      th.textContent = d.day_name;
      if (d.is_holiday) {
        th.title = `Libur Nasional: ${d.holiday_name}`;
      } else if (d.is_weekend) {
        th.title = 'Akhir Pekan';
      }
      trHead1.appendChild(th);
    });
    thead.appendChild(trHead1);

    // Header Row 2: Dates (1, 2, 3, ...)
    const trHead2 = document.createElement('tr');
    days.forEach(d => {
      const th = document.createElement('th');
      th.className = d.is_holiday ? 'holiday-col' : (d.is_weekend ? 'weekend-col' : '');
      th.style.textAlign = 'center';
      th.style.padding = '5px 2px';
      th.style.fontSize = '11px';
      th.style.fontWeight = '700';
      th.style.minWidth = '54px';
      th.style.width = '54px';
      th.textContent = d.day;
      if (d.is_holiday) {
        th.title = `Libur Nasional: ${d.holiday_name}`;
      }
      trHead2.appendChild(th);
    });
    thead.appendChild(trHead2);

    // Body Rows per Group
    let globalIndex = 1;
    (data.groups || []).forEach((group, gIdx) => {
      // Group Header Separator Row
      const trGroup = document.createElement('tr');
      trGroup.className = 'group-header-row';
      trGroup.innerHTML = `
        <td colspan="${days.length + 3}">
          ${group.group_name} (${group.rows.length} Orang)
        </td>
      `;
      tbody.appendChild(trGroup);

      group.rows.forEach((person, pIdx) => {
        const tr = document.createElement('tr');
        tr.dataset.group = group.group_key;
        tr.dataset.pIdx = pIdx;

        tr.innerHTML = `
          <td>${globalIndex}</td>
          <td class="editable-cell editable-title-cell" contenteditable="true" spellcheck="false" data-group="${group.group_key}" data-pidx="${pIdx}" title="Klik untuk mengedit Title/Jabatan">${escapeHtml(person.title)}</td>
          <td class="editable-cell editable-name-cell" contenteditable="true" spellcheck="false" data-group="${group.group_key}" data-pidx="${pIdx}" title="Klik untuk mengedit Nama" style="font-weight: 700; color: #0f172a; white-space: nowrap;">${escapeHtml(person.name)}</td>
        `;

        person.schedule.forEach((shift, sIdx) => {
          const td = document.createElement('td');
          const dayInfo = days[sIdx] || {};
          const bgClass = dayInfo.is_holiday ? 'holiday-bg' : (dayInfo.is_weekend ? 'weekend-bg' : '');
          td.className = `shift-cell ${getShiftClass(shift)} ${bgClass}`;
          td.dataset.group = group.group_key;
          td.dataset.pIdx = pIdx;
          td.dataset.sIdx = sIdx;
          td.textContent = shift;
          td.style.minWidth = '54px';
          td.style.fontSize = '10px';
          td.style.whiteSpace = 'nowrap';
          td.title = `Klik untuk ubah shift (${person.name} - Tgl ${sIdx + 1}${dayInfo.is_holiday ? ' - ' + dayInfo.holiday_name : ''})`;
          tr.appendChild(td);
        });

        tbody.appendChild(tr);
        globalIndex++;
      });
    });

    // Attach Cell Click Event for interactive shift editing
    tbody.querySelectorAll('.shift-cell').forEach(td => {
      td.addEventListener('click', (e) => {
        openShiftPicker(td, e);
      });
    });

    // Attach Inline Edit Listener for Title
    tbody.querySelectorAll('.editable-title-cell').forEach(td => {
      td.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          td.blur();
        }
      });
      td.addEventListener('blur', () => {
        const newTitle = td.textContent.trim();
        const gKey = td.dataset.group;
        const pIdx = parseInt(td.dataset.pidx, 10);
        if (scheduleData && scheduleData.groups) {
          const groupObj = scheduleData.groups.find(g => g.group_key === gKey);
          if (groupObj && groupObj.rows[pIdx]) {
            groupObj.rows[pIdx].title = newTitle;
          }
        }
        if (staffConfig && staffConfig[gKey] && staffConfig[gKey][pIdx]) {
          staffConfig[gKey][pIdx].title = newTitle;
          localStorage.setItem('tar_engineering_staff_config_v3', JSON.stringify(staffConfig));
          showToast(`✓ Title diperbarui: "${newTitle}"`);
        }
      });
    });

    // Attach Inline Edit Listener for Name
    tbody.querySelectorAll('.editable-name-cell').forEach(td => {
      td.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          td.blur();
        }
      });
      td.addEventListener('blur', () => {
        const newName = td.textContent.trim();
        const gKey = td.dataset.group;
        const pIdx = parseInt(td.dataset.pidx, 10);
        if (!newName) {
          showToast('Nama tidak boleh kosong.', true);
          return;
        }
        if (scheduleData && scheduleData.groups) {
          const groupObj = scheduleData.groups.find(g => g.group_key === gKey);
          if (groupObj && groupObj.rows[pIdx]) {
            groupObj.rows[pIdx].name = newName;
          }
        }
        if (staffConfig && staffConfig[gKey] && staffConfig[gKey][pIdx]) {
          staffConfig[gKey][pIdx].name = newName;
          localStorage.setItem('tar_engineering_staff_config_v3', JSON.stringify(staffConfig));
          showToast(`✓ Nama diperbarui: "${newName}"`);
        }
      });
    });
  }

  // Quick Shift Picker Popup
  const picker = $('shift-picker-dialog');
  function openShiftPicker(td) {
    activeEditingCell = td;
    if (picker) picker.showModal();
  }

  // Close shift picker buttons
  if ($('btn-close-shift-picker')) {
    $('btn-close-shift-picker').addEventListener('click', () => picker && picker.close());
  }
  if ($('btn-cancel-shift-picker')) {
    $('btn-cancel-shift-picker').addEventListener('click', () => picker && picker.close());
  }

  if (picker) {
    picker.addEventListener('click', (e) => {
      const rect = picker.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
        picker.close();
      }
    });
  }

  if ($('shift-options-grid')) {
    $('shift-options-grid').querySelectorAll('.opt-shift-val').forEach(btn => {
      btn.addEventListener('click', () => {
        if (activeEditingCell && scheduleData) {
          const newVal = btn.dataset.val;
          const gKey = activeEditingCell.dataset.group;
          const pIdx = parseInt(activeEditingCell.dataset.pIdx, 10);
          const sIdx = parseInt(activeEditingCell.dataset.sIdx, 10);

          const groupObj = scheduleData.groups.find(g => g.group_key === gKey);
          if (groupObj && groupObj.rows[pIdx]) {
            groupObj.rows[pIdx].schedule[sIdx] = newVal;
            activeEditingCell.textContent = newVal;
            const dayInfo = (scheduleData.days && scheduleData.days[sIdx]) || {};
            const bgClass = dayInfo.is_holiday ? 'holiday-bg' : (dayInfo.is_weekend ? 'weekend-bg' : '');
            activeEditingCell.className = `shift-cell ${getShiftClass(newVal)} ${bgClass}`;
          }
        }
        if (picker) picker.close();
      });
    });
  }

  // Rolling Controls
  if ($('btn-roll-next')) {
    $('btn-roll-next').addEventListener('click', () => {
      rotationStep = (rotationStep + 1) % 8;
      loadSchedule();
    });
  }

  if ($('btn-roll-prev')) {
    $('btn-roll-prev').addEventListener('click', () => {
      rotationStep = (rotationStep - 1 + 8) % 8;
      loadSchedule();
    });
  }

  if ($('btn-reset-rotation')) {
    $('btn-reset-rotation').addEventListener('click', () => {
      rotationStep = 0;
      loadSchedule();
    });
  }

  if ($('sel-month')) $('sel-month').addEventListener('change', loadSchedule);
  if ($('inp-year')) $('inp-year').addEventListener('change', loadSchedule);

  // Quick Search Filter by Name or Title
  const searchInput = $('inp-filter-staff');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const term = searchInput.value.toLowerCase().trim();
      document.querySelectorAll('#schedule-tbody tr').forEach(row => {
        if (row.classList.contains('group-header-row')) {
          row.style.display = '';
          return;
        }
        const titleCell = row.querySelector('.editable-title-cell');
        const nameCell = row.querySelector('.editable-name-cell');
        const rowText = ((titleCell ? titleCell.textContent : '') + ' ' + (nameCell ? nameCell.textContent : '')).toLowerCase();
        row.style.display = (!term || rowText.includes(term)) ? '' : 'none';
      });
    });
  }

  // Copy GreatDay Schedule to Clipboard (TSV / HTML format for Excel)
  if ($('btn-copy-schedule')) {
    $('btn-copy-schedule').addEventListener('click', async () => {
      if (!scheduleData) return;

      const days = scheduleData.days || [];
      const tsvRows = [];

      // Header 1: Day names
      const head1 = ['', '', ''];
      days.forEach(d => head1.push(d.day_name));
      tsvRows.push(head1.join('\t'));

      // Header 2: Dates
      const head2 = ['NO', 'TITLE', 'NAME'];
      days.forEach(d => head2.push(d.day));
      tsvRows.push(head2.join('\t'));

      // Data rows
      let no = 1;
      (scheduleData.groups || []).forEach(g => {
        (g.rows || []).forEach(p => {
          const row = [no, p.title, p.name, ...p.schedule];
          tsvRows.push(row.join('\t'));
          no++;
        });
      });

      const tsvString = tsvRows.join('\n');

      try {
        await navigator.clipboard.writeText(tsvString);
        showToast('✓ Tabel jadwal GreatDay berhasil disalin! Buka Excel dan tekan Ctrl+V.');
      } catch (err) {
        showToast('Gagal menyalin: ' + err.message, true);
      }
    });
  }

  // Download Excel (.xlsx) for GreatDay
  if ($('btn-download-schedule-excel')) {
    $('btn-download-schedule-excel').addEventListener('click', async () => {
      if (!scheduleData) return;

      const btn = $('btn-download-schedule-excel');
      btn.disabled = true;
      btn.textContent = 'Membuat Excel...';

      try {
        const res = await fetch('/api/schedule/export-excel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ schedule_data: scheduleData })
        });

        if (!res.ok) throw new Error('Gagal mendownload Excel.');

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Jadwal_Kerja_GreatDay_${scheduleData.month_name}_${scheduleData.year}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        showToast('✓ File Excel Jadwal GreatDay berhasil didownload!');
      } catch (err) {
        showToast('Gagal download: ' + err.message, true);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg> Download Excel (.xlsx)`;
      }
    });
  }

  // Staff Management Modal Logic
  const staffDialog = $('staff-dialog');

  if ($('btn-manage-staff')) {
    $('btn-manage-staff').addEventListener('click', () => {
      renderStaffManagerList();
      if (staffDialog) staffDialog.showModal();
    });
  }

  if (staffDialog) {
    staffDialog.addEventListener('click', (e) => {
      const rect = staffDialog.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
        staffDialog.close();
      }
    });
  }

  function renderStaffManagerList() {
    const container = $('staff-list-container');
    if (!container || !staffConfig) return;
    container.innerHTML = '';

    const groupNames = {
      'reguler': 'Staff & Supervisor Reguler (Piket Sabtu)',
      'shift': 'Engineering Shift (24 Jam)',
      'daily_worker': 'Daily Worker (DW)'
    };

    ['reguler', 'shift', 'daily_worker'].forEach(gKey => {
      const list = staffConfig[gKey] || [];
      const section = document.createElement('div');
      section.style.marginBottom = '16px';

      section.innerHTML = `
        <div style="font-size: 12px; font-weight: 800; color: #1e293b; margin-bottom: 6px; display: flex; justify-content: space-between;">
          <span>${groupNames[gKey]}</span>
          <span style="color: #64748b; font-size: 11px;">${list.length} Personil</span>
        </div>
        <div style="max-height: 240px; overflow-y: auto; border: 1px solid var(--border); border-radius: var(--radius-md); background: #fff;">
          <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid var(--border);">
                <th style="width: 32px; text-align: center; padding: 6px 4px; font-size: 10px; color: #64748b;">NO</th>
                <th style="width: 170px; padding: 6px 8px; font-size: 10px; text-align: left; color: #64748b;">JABATAN / TITLE</th>
                <th style="padding: 6px 8px; font-size: 10px; text-align: left; color: #64748b;">NAMA LENGKAP</th>
                <th style="width: 160px; padding: 6px 8px; font-size: 10px; text-align: left; color: #64748b;">PENGATURAN</th>
                <th style="width: 40px; text-align: center; padding: 6px 4px; font-size: 10px; color: #64748b;">AKSI</th>
              </tr>
            </thead>
            <tbody>
              ${list.map((p, idx) => {
                let settingHtml = '';
                if (gKey === 'reguler') {
                  const piketVal = p.saturday_piket !== undefined ? String(p.saturday_piket) : 'even';
                  settingHtml = `
                    <select class="edit-staff-input edit-staff-setting-field" data-group="${gKey}" data-idx="${idx}" style="font-size: 10px; padding: 3px 4px;">
                      <option value="none" ${piketVal === 'none' || piketVal === 'false' ? 'selected' : ''}>Tidak Piket (OFF)</option>
                      <option value="even" ${piketVal === 'even' || piketVal === 'true' ? 'selected' : ''}>Piket Sabtu Genap (7 & 21)</option>
                      <option value="odd" ${piketVal === 'odd' ? 'selected' : ''}>Piket Sabtu Ganjil (14 & 28)</option>
                      <option value="even_plus_14" ${piketVal === 'even_plus_14' ? 'selected' : ''}>Piket 7, 14, 21 Nov</option>
                      <option value="all" ${piketVal === 'all' ? 'selected' : ''}>Piket Semua Sabtu</option>
                    </select>
                  `;
                } else if (gKey === 'shift') {
                  const offVal = p.pattern_offset !== undefined ? parseInt(p.pattern_offset, 10) : 0;
                  settingHtml = `
                    <select class="edit-staff-input edit-staff-setting-field" data-group="${gKey}" data-idx="${idx}" style="font-size: 10px; padding: 3px 4px;">
                      <option value="2" ${offVal === 2 ? 'selected' : ''}>Regu 1 (1 Nov: S)</option>
                      <option value="4" ${offVal === 4 ? 'selected' : ''}>Regu 2 (1 Nov: M)</option>
                      <option value="6" ${offVal === 6 ? 'selected' : ''}>Regu 3 (1 Nov: OFF)</option>
                      <option value="0" ${offVal === 0 ? 'selected' : ''}>Regu 4 (1 Nov: P)</option>
                    </select>
                  `;
                } else if (gKey === 'daily_worker') {
                  const dayOff = p.day_off !== undefined ? parseInt(p.day_off, 10) : 3;
                  settingHtml = `
                    <select class="edit-staff-input edit-staff-setting-field" data-group="${gKey}" data-idx="${idx}" style="font-size: 10px; padding: 3px 4px;">
                      <option value="3" ${dayOff === 3 ? 'selected' : ''}>Libur Kamis</option>
                      <option value="6" ${dayOff === 6 ? 'selected' : ''}>Libur Minggu</option>
                    </select>
                  `;
                }

                return `
                  <tr style="border-bottom: 1px solid #f1f5f2;">
                    <td style="width: 32px; text-align: center; color: #64748b;">${idx + 1}</td>
                    <td style="width: 170px; padding: 4px 6px;">
                      <input type="text" class="edit-staff-input edit-staff-title-field" data-group="${gKey}" data-idx="${idx}" value="${escapeHtml(p.title)}" placeholder="Jabatan">
                    </td>
                    <td style="padding: 4px 6px;">
                      <input type="text" class="edit-staff-input edit-staff-name-field" data-group="${gKey}" data-idx="${idx}" value="${escapeHtml(p.name)}" placeholder="Nama Lengkap">
                    </td>
                    <td style="width: 160px; padding: 4px 6px;">
                      ${settingHtml}
                    </td>
                    <td style="width: 40px; text-align: center;">
                      <button type="button" class="del-staff-btn" data-group="${gKey}" data-idx="${idx}" title="Hapus Personil">✕</button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
      container.appendChild(section);
    });

    container.querySelectorAll('.edit-staff-title-field').forEach(input => {
      input.addEventListener('change', () => {
        const gKey = input.dataset.group;
        const idx = parseInt(input.dataset.idx, 10);
        if (staffConfig[gKey] && staffConfig[gKey][idx]) {
          staffConfig[gKey][idx].title = input.value.trim();
        }
      });
    });

    container.querySelectorAll('.edit-staff-name-field').forEach(input => {
      input.addEventListener('change', () => {
        const gKey = input.dataset.group;
        const idx = parseInt(input.dataset.idx, 10);
        if (staffConfig[gKey] && staffConfig[gKey][idx]) {
          staffConfig[gKey][idx].name = input.value.trim();
        }
      });
    });

    container.querySelectorAll('.edit-staff-setting-field').forEach(select => {
      select.addEventListener('change', () => {
        const gKey = select.dataset.group;
        const idx = parseInt(select.dataset.idx, 10);
        if (staffConfig[gKey] && staffConfig[gKey][idx]) {
          if (gKey === 'reguler') {
            staffConfig[gKey][idx].saturday_piket = select.value;
          } else if (gKey === 'shift') {
            staffConfig[gKey][idx].pattern_offset = parseInt(select.value, 10);
          } else if (gKey === 'daily_worker') {
            staffConfig[gKey][idx].day_off = parseInt(select.value, 10);
          }
        }
      });
    });

    container.querySelectorAll('.del-staff-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        syncModalInputsToStaffConfig();
        const gKey = btn.dataset.group;
        const idx = parseInt(btn.dataset.idx, 10);
        staffConfig[gKey].splice(idx, 1);
        renderStaffManagerList();
      });
    });
  }

  function syncModalInputsToStaffConfig() {
    const container = $('staff-list-container');
    if (!container || !staffConfig) return;
    container.querySelectorAll('.edit-staff-title-field').forEach(input => {
      const gKey = input.dataset.group;
      const idx = parseInt(input.dataset.idx, 10);
      if (staffConfig[gKey] && staffConfig[gKey][idx]) {
        staffConfig[gKey][idx].title = input.value.trim();
      }
    });
    container.querySelectorAll('.edit-staff-name-field').forEach(input => {
      const gKey = input.dataset.group;
      const idx = parseInt(input.dataset.idx, 10);
      if (staffConfig[gKey] && staffConfig[gKey][idx]) {
        staffConfig[gKey][idx].name = input.value.trim();
      }
    });
    container.querySelectorAll('.edit-staff-setting-field').forEach(select => {
      const gKey = select.dataset.group;
      const idx = parseInt(select.dataset.idx, 10);
      if (staffConfig[gKey] && staffConfig[gKey][idx]) {
        if (gKey === 'reguler') {
          staffConfig[gKey][idx].saturday_piket = select.value;
        } else if (gKey === 'shift') {
          staffConfig[gKey][idx].pattern_offset = parseInt(select.value, 10);
        } else if (gKey === 'daily_worker') {
          staffConfig[gKey][idx].day_off = parseInt(select.value, 10);
        }
      }
    });
  }

  // Add New Staff Submit
  if ($('btn-add-staff-submit')) {
    $('btn-add-staff-submit').addEventListener('click', () => {
      syncModalInputsToStaffConfig();
      const group = $('new-staff-group').value;
      const title = $('new-staff-title').value.trim();
      const name = $('new-staff-name').value.trim();
      const offset = parseInt($('new-staff-offset').value, 10);

      if (!name) {
        showToast('Nama personil tidak boleh kosong.', true);
        return;
      }

      if (!staffConfig[group]) staffConfig[group] = [];

      const newPerson = {
        title: title || (group === 'daily_worker' ? 'Daily Worker' : (group === 'shift' ? 'Engineering Shift' : 'Staff')),
        name: name
      };

      if (group === 'shift') {
        newPerson.pattern_offset = offset;
      } else if (group === 'reguler') {
        newPerson.saturday_piket = (staffConfig[group].length % 2 === 1) ? 'odd' : 'even';
      } else if (group === 'daily_worker') {
        newPerson.day_off = 3;
      }

      staffConfig[group].push(newPerson);

      $('new-staff-name').value = '';
      $('new-staff-title').value = '';
      renderStaffManagerList();
      showToast(`✓ Personil ${name} berhasil ditambahkan!`);
    });
  }

  // Save changes & apply to schedule
  if ($('btn-save-staff-changes')) {
    $('btn-save-staff-changes').addEventListener('click', () => {
      syncModalInputsToStaffConfig();
      localStorage.setItem('tar_engineering_staff_config_v3', JSON.stringify(staffConfig));
      if (staffDialog) staffDialog.close();
      showToast('✓ Perubahan Nama, Title & Personil berhasil diterapkan!');
      loadSchedule();
    });
  }

  // Reset to default
  if ($('btn-reset-default-staff')) {
    $('btn-reset-default-staff').addEventListener('click', async () => {
      if (!confirm('Kembalikan ke susunan personil awal dari file Excel?')) return;
      localStorage.removeItem('tar_engineering_staff_config_v3');
      staffConfig = null;
      await initStaffConfig();
      renderStaffManagerList();
      showToast('Daftar personil dikembalikan ke default.');
      loadSchedule();
    });
  }

  function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }

  // Init
  initStaffConfig().then(() => {
    loadSchedule();
  });
});
