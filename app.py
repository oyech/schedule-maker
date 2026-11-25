import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect

from schedule_generator import (
    generate_schedule_grid,
    export_schedule_to_excel,
    DEFAULT_SCHEDULE_DATA,
    MONTH_NAMES_ID
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tar-engineering-schedule-tool'


# ---------------------------------------------------------
# Web Page Navigation Routes
# ---------------------------------------------------------

@app.route('/')
def index():
    """Root redirects directly to the main Schedule page."""
    return redirect('/schedule')


@app.route('/schedule')
def schedule_page():
    """Main Engineering 24-Hour Shift Schedule page."""
    return render_template('schedule.html')


@app.route('/schedule-greatday')
def schedule_greatday_page():
    """Schedule GreatDay HRIS format page."""
    return render_template('schedule_greatday.html')


# ---------------------------------------------------------
# Schedule API Routes
# ---------------------------------------------------------

@app.get('/api/schedule/defaults')
def api_schedule_defaults():
    """Returns default staff members and shift patterns."""
    return jsonify(
        success=True,
        default_data=DEFAULT_SCHEDULE_DATA,
        month_names=MONTH_NAMES_ID
    )


@app.post('/api/schedule/generate')
def api_schedule_generate():
    """
    Generates monthly schedule grid with rolling shift support.
    Supports format='standard' or format='greatday'.
    """
    data = request.get_json(silent=True) or {}
    now = datetime.now()
    year = int(data.get('year', now.year))
    month = int(data.get('month', now.month))
    shift_rotation_step = int(data.get('shift_rotation_step', 0))
    format_type = data.get('format', 'standard')
    staff_data = data.get('staff_data')

    grid = generate_schedule_grid(
        year=year,
        month=month,
        staff_data=staff_data,
        shift_rotation_step=shift_rotation_step,
        format=format_type
    )

    return jsonify(success=True, data=grid)


@app.post('/api/schedule/export-excel')
def api_schedule_export_excel():
    """
    Generates and downloads the Excel schedule spreadsheet matching user's template.
    """
    data = request.get_json(silent=True) or {}
    schedule_data = data.get('schedule_data')

    if not schedule_data:
        now = datetime.now()
        schedule_data = generate_schedule_grid(year=now.year, month=now.month)

    stream = export_schedule_to_excel(schedule_data)

    month_name = schedule_data.get('month_name', 'BULAN')
    year = schedule_data.get('year', 2026)
    is_greatday = (schedule_data.get('format') == 'greatday') or any(
        any('Shift' in str(v) for v in p.get('schedule', []))
        for g in schedule_data.get('groups', []) for p in g.get('rows', [])
    )
    prefix = "Jadwal_Kerja_GreatDay" if is_greatday else "Jadwal_Kerja_Engineering"

    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{prefix}_{month_name}_{year}.xlsx"
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5006))
    app.run(host='0.0.0.0', port=port, debug=True)
