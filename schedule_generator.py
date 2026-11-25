import io
import calendar
from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Indonesian day abbreviations (Senin=0 .. Minggu=6)
DAY_NAMES_ID = ['Sn', 'Sl', 'Rb', 'Km', 'Jm', 'Sb', 'Mg']
MONTH_NAMES_ID = [
    '', 'JANUARI', 'FEBRUARI', 'MARET', 'APRIL', 'MEI', 'JUNI',
    'JULI', 'AGUSTUS', 'SEPTEMBER', 'OKTOBER', 'NOVEMBER', 'DESEMBER'
]

# Baseline date anchor: 1 November 2026 (Minggu / Sunday)
BASELINE_DATE = date(2026, 11, 1)
# First Saturday of November 2026: 7 November 2026
BASELINE_FIRST_SATURDAY = date(2026, 11, 7)

# 8-Day Shift Cycle
# Order: P, P, S, S, M, M, OFF, OFF
# Index: 0=P, 1=P, 2=S, 3=S, 4=M, 5=M, 6=OFF, 7=OFF
SHIFT_CYCLE = ['P', 'P', 'S', 'S', 'M', 'M', 'OFF', 'OFF']

# GreatDay Shift Code Mappings
GREATDAY_SHIFT_MAP = {
    'P': 'Shift 3',
    'S': 'Shift 41',
    'M': 'Shift 52',
    'OFF': 'OFF',
    'R1': 'Shift 14',
    'R3': 'Shift 12',
    'R4': 'R4',
    'CT': 'CT',
}

# Helper to evaluate Saturday piket for a regular staff member
def is_piket_day(rule, week_num):
    if rule in ('none', False, None):
        return False
    if rule == 'all':
        return True
    if rule in ('even', True):
        return (week_num % 2 == 0)
    if rule == 'odd':
        return (week_num % 2 == 1)
    if rule == 'even_plus_14':
        return week_num in (0, 1, 2)
    if isinstance(rule, (list, tuple)):
        return week_num in rule
    return False


# Default Staff Template anchored to November 2026 (Taman Anggrek Residence)
DEFAULT_SCHEDULE_DATA = {
    'reguler': [
        {'title': 'Engineering Ast. Manager', 'name': 'Yafi Al- Hadi', 'saturday_piket': 'none'},
        {'title': 'Supervisor', 'name': 'Sandi Adi Putra', 'saturday_piket': 'even'},
        {'title': 'Supervisor Fit Out', 'name': 'Florentinus Frengky', 'saturday_piket': 'odd'},
        {'title': 'PM Estate Staff', 'name': 'Solehudin', 'saturday_piket': 'even'},
        {'title': 'Electronic', 'name': 'Tubagus Erwan N.', 'saturday_piket': 'odd'},
        {'title': 'Electronic', 'name': 'Iman Hanapi', 'saturday_piket': 'even'},
        {'title': 'Electronic', 'name': 'Ridho Hidayatullah', 'saturday_piket': 'odd'},
        {'title': 'Mechanical Plumbing Engineering', 'name': 'Muhammad Reza', 'saturday_piket': 'odd'},
        {'title': 'Mechanical Plumbing Engineering', 'name': 'Syahrul Romadhon', 'saturday_piket': 'odd'},
        {'title': 'Mechanical Plumbing Engineering', 'name': 'M. Nurhuda', 'saturday_piket': 'even'},
        {'title': 'Mechanical Plumbing Engineering', 'name': 'Eko Puji H.', 'saturday_piket': 'odd'},
        {'title': 'Mechanical Plumbing Engineering', 'name': 'Arif Rahman Hakim', 'saturday_piket': 'even'},
        {'title': 'Engineering Staff', 'name': 'Ahmad Faisal', 'saturday_piket': 'even_plus_14'},
        {'title': 'Engineering Staff', 'name': 'Resya', 'saturday_piket': 'all'},
        {'title': 'Civil Engineer', 'name': 'Diwan', 'saturday_piket': 'odd'},
        {'title': 'Civil Engineer', 'name': 'Abdurahman Zakaria', 'saturday_piket': 'even'},
        {'title': 'Civil Engineer', 'name': 'Bintang Firjatullah Ananto Tio', 'saturday_piket': 'odd'},
        {'title': 'Gondola', 'name': 'Agus', 'saturday_piket': 'odd', 'weekday_shift': 'P'},
        {'title': 'PIC Tower A', 'name': 'Reza Ardiansyah', 'saturday_piket': 'odd'},
        {'title': 'PIC Tower A', 'name': 'Anka Sutarma', 'saturday_piket': 'even'},
        {'title': 'PIC Tower B', 'name': 'Bagas Widiyanta', 'saturday_piket': 'even'},
        {'title': 'PIC Tower C', 'name': 'Fariz Marfadillah', 'saturday_piket': 'odd'},
        {'title': 'PIC Tower D', 'name': 'Angga Widodo', 'saturday_piket': 'even'},
        {'title': 'PIC Tower D', 'name': 'Arip Anggara', 'saturday_piket': 'odd'},
        {'title': 'PIC Tower E', 'name': 'Demas Yosep Maulana', 'saturday_piket': 'odd'},
        {'title': 'PIC Tower E', 'name': 'Tatang Sunarya', 'saturday_piket': 'even'},
        {'title': 'PIC Tower F', 'name': 'Wahyu Agung Satriya', 'saturday_piket': 'even'}
    ],
    'shift': [
        # Regu 1: Deri Kurniawan, Tarmidi (DW), Muhammad Chairil Hakim -> 1 Nov starts S|S (offset 2)
        {'title': 'Engineering Shift', 'name': 'Deri Kurniawan', 'pattern_offset': 2},
        {'title': 'Engineering Shift', 'name': 'Tarmidi (DW)', 'pattern_offset': 2},
        {'title': 'Engineering Shift', 'name': 'Muhammad Chairil Hakim', 'pattern_offset': 2},

        # Regu 2: M. Reza Pratama, Rizky Maulana Putra, Ayudi Usni Amri -> 1 Nov starts M|M (offset 4)
        {'title': 'Engineering Shift', 'name': 'M. Reza Pratama', 'pattern_offset': 4},
        {'title': 'Engineering Shift', 'name': 'Rizky Maulana Putra', 'pattern_offset': 4},
        {'title': 'Engineering Shift', 'name': 'Ayudi Usni Amri', 'pattern_offset': 4},

        # Regu 3: Ariz Kharisma, Ahmad Farhan, Irhandi Thaufan -> 1 Nov starts OFF|OFF (offset 6)
        {'title': 'Engineering Shift', 'name': 'Ariz Kharisma', 'pattern_offset': 6},
        {'title': 'Engineering Shift', 'name': 'Ahmad Farhan', 'pattern_offset': 6},
        {'title': 'Engineering Shift', 'name': 'Irhandi Thaufan', 'pattern_offset': 6},

        # Regu 4: Ichsan Agus S., Indra Kardiana, Eko Faishal (DW) -> 1 Nov starts P|P (offset 0)
        {'title': 'Engineering Shift', 'name': 'Ichsan Agus S.', 'pattern_offset': 0},
        {'title': 'Engineering Shift', 'name': 'Indra Kardiana', 'pattern_offset': 0},
        {
            'title': 'Engineering Shift',
            'name': 'Eko Faishal (DW)',
            'pattern_offset': 0,
            'custom_greatday_map': {'P': 'Shift 4', 'S': 'Shift 42', 'M': 'Shift 53', 'OFF': 'OFF'}
        }
    ],
    'daily_worker': [
        {'title': 'Daily Worker', 'name': 'Abdul Ibrahim', 'day_off': 3},
        {'title': 'Daily Worker', 'name': 'Suwarno', 'day_off': 3},
        {'title': 'Daily Worker', 'name': 'Subkhi', 'day_off': 3},
        {'title': 'Daily Worker', 'name': 'Adi', 'day_off': 3},
        {'title': 'Daily Worker', 'name': 'Hendi Suhendi', 'day_off': 3},
        {'title': 'PIC Tower F (DW)', 'name': 'Ridwan Maulana Surya', 'day_off': 3},
        {'title': 'PIC Tower C (DW)', 'name': 'Ris Amilin', 'day_off': 3},
        {'title': 'Daily Worker', 'name': 'Agus Arifin', 'day_off': 3},
        {'title': 'Daily Worker', 'name': 'Gunawan', 'day_off': 3},
        {'title': 'PIC Tower B (DW)', 'name': 'Subaidi', 'day_off': 3}
    ]
}


# Indonesian Public Holidays database (Hari Libur Nasional Indonesia)
INDONESIAN_HOLIDAYS = {
    2024: {
        (1, 1): "Tahun Baru 2024 Masehi",
        (2, 8): "Isra Mikraj Nabi Muhammad SAW",
        (2, 10): "Tahun Baru Imlek 2575 Kongzili",
        (3, 11): "Hari Suci Nyepi (Tahun Baru Saka 1946)",
        (3, 29): "Wafat Yesus Kristus (Jumat Agung)",
        (3, 31): "Hari Paskah",
        (4, 10): "Hari Raya Idul Fitri 1445 H",
        (4, 11): "Hari Raya Idul Fitri 1445 H",
        (5, 1): "Hari Buruh Internasional",
        (5, 9): "Kenaikan Yesus Kristus",
        (5, 23): "Hari Raya Waisak 2568 BE",
        (6, 1): "Hari Lahir Pancasila",
        (6, 17): "Hari Raya Idul Adha 1445 H",
        (7, 7): "Tahun Baru Islam 1446 H",
        (8, 17): "Hari Kemerdekaan RI ke-79",
        (9, 16): "Maulid Nabi Muhammad SAW",
        (12, 25): "Hari Raya Natal",
    },
    2025: {
        (1, 1): "Tahun Baru 2025 Masehi",
        (1, 27): "Isra Mikraj Nabi Muhammad SAW",
        (1, 29): "Tahun Baru Imlek 2576 Kongzili",
        (3, 29): "Hari Suci Nyepi (Tahun Baru Saka 1947)",
        (3, 31): "Hari Raya Idul Fitri 1446 H",
        (4, 1): "Hari Raya Idul Fitri 1446 H",
        (4, 18): "Wafat Yesus Kristus",
        (4, 20): "Kebangkitan Yesus Kristus (Paskah)",
        (5, 1): "Hari Buruh Internasional",
        (5, 12): "Hari Raya Waisak 2569 BE",
        (5, 29): "Kenaikan Yesus Kristus",
        (6, 1): "Hari Lahir Pancasila",
        (6, 6): "Hari Raya Idul Adha 1446 H",
        (6, 27): "1 Muharram / Tahun Baru Islam 1447 H",
        (8, 17): "Proklamasi Kemerdekaan RI ke-80",
        (9, 5): "Maulid Nabi Muhammad SAW",
        (12, 25): "Kelahiran Yesus Kristus (Natal)",
    },
    2026: {
        (1, 1): "Tahun Baru 2026 Masehi",
        (1, 16): "Isra Mikraj Nabi Muhammad SAW",
        (2, 17): "Tahun Baru Imlek 2577 Kongzili",
        (3, 19): "Hari Suci Nyepi (Tahun Baru Saka 1948)",
        (3, 20): "Hari Raya Idul Fitri 1447 H",
        (3, 21): "Hari Raya Idul Fitri 1447 H",
        (4, 3): "Wafat Yesus Kristus (Jumat Agung)",
        (4, 5): "Hari Paskah",
        (5, 1): "Hari Buruh Internasional",
        (5, 14): "Kenaikan Yesus Kristus",
        (5, 27): "Hari Raya Idul Adha 1447 H",
        (5, 31): "Hari Raya Waisak 2570 BE",
        (6, 1): "Hari Lahir Pancasila",
        (6, 16): "Tahun Baru Islam 1448 H",
        (8, 17): "Hari Kemerdekaan RI ke-81",
        (8, 25): "Maulid Nabi Muhammad SAW",
        (12, 25): "Hari Raya Natal",
    },
    2027: {
        (1, 1): "Tahun Baru 2027 Masehi",
        (1, 6): "Isra Mikraj Nabi Muhammad SAW",
        (2, 6): "Tahun Baru Imlek 2578 Kongzili",
        (3, 9): "Hari Suci Nyepi (Tahun Baru Saka 1949)",
        (3, 10): "Hari Raya Idul Fitri 1448 H",
        (3, 11): "Hari Raya Idul Fitri 1448 H",
        (3, 26): "Wafat Yesus Kristus",
        (3, 28): "Hari Paskah",
        (5, 1): "Hari Buruh Internasional",
        (5, 6): "Kenaikan Yesus Kristus",
        (5, 16): "Hari Raya Idul Adha 1448 H",
        (5, 20): "Hari Raya Waisak 2571 BE",
        (6, 1): "Hari Lahir Pancasila",
        (6, 6): "Tahun Baru Islam 1449 H",
        (8, 15): "Maulid Nabi Muhammad SAW",
        (8, 17): "Hari Kemerdekaan RI ke-82",
        (12, 25): "Hari Raya Natal",
    },
    2028: {
        (1, 1): "Tahun Baru 2028 Masehi",
        (1, 25): "Isra Mikraj Nabi Muhammad SAW",
        (1, 26): "Tahun Baru Imlek 2579 Kongzili",
        (2, 27): "Hari Raya Idul Fitri 1449 H",
        (2, 28): "Hari Raya Idul Fitri 1449 H",
        (3, 26): "Hari Suci Nyepi (Tahun Baru Saka 1950)",
        (4, 14): "Wafat Yesus Kristus",
        (5, 1): "Hari Buruh Internasional",
        (5, 5): "Hari Raya Idul Adha 1449 H",
        (5, 9): "Hari Raya Waisak 2572 BE",
        (5, 25): "Kenaikan Yesus Kristus",
        (5, 25): "Tahun Baru Islam 1450 H",
        (6, 1): "Hari Lahir Pancasila",
        (8, 3): "Maulid Nabi Muhammad SAW",
        (8, 17): "Hari Kemerdekaan RI ke-83",
        (12, 25): "Hari Raya Natal",
    }
}

# Fixed annual national holidays fallback for any other year
FIXED_ANNUAL_HOLIDAYS = {
    (1, 1): "Tahun Baru Masehi",
    (5, 1): "Hari Buruh Internasional",
    (6, 1): "Hari Lahir Pancasila",
    (8, 17): "Hari Kemerdekaan RI",
    (12, 25): "Hari Raya Natal"
}


def get_holiday_name(year, month, day):
    """
    Returns the national holiday name if (year, month, day) is a public holiday, else None.
    """
    if year in INDONESIAN_HOLIDAYS:
        if (month, day) in INDONESIAN_HOLIDAYS[year]:
            return INDONESIAN_HOLIDAYS[year][(month, day)]
    return FIXED_ANNUAL_HOLIDAYS.get((month, day), None)


def get_month_days_info(year, month):
    """
    Returns list of day dicts for the specified year and month:
    [{ day: 1, date_obj: date(..), day_name: 'Sl', weekday: 1, is_weekend: False, is_holiday: False, holiday_name: None, is_red_day: False }, ...]
    """
    num_days = calendar.monthrange(year, month)[1]
    days = []
    for d in range(1, num_days + 1):
        dt = date(year, month, d)
        weekday = dt.weekday()  # 0=Monday .. 6=Sunday
        holiday = get_holiday_name(year, month, d)
        is_holiday = holiday is not None
        is_saturday = weekday == 5
        is_sunday = weekday == 6
        is_weekend = weekday in (5, 6)

        days.append({
            'day': d,
            'date_obj': dt,
            'day_name': DAY_NAMES_ID[weekday],
            'weekday': weekday,
            'is_saturday': is_saturday,
            'is_sunday': is_sunday,
            'is_weekend': is_weekend,
            'is_holiday': is_holiday,
            'holiday_name': holiday,
            'is_red_day': is_weekend or is_holiday
        })
    return days


def generate_schedule_grid(year, month, staff_data=None, shift_rotation_step=0, format='standard'):
    """
    Generates a full month schedule matrix seamlessly rolling from November 2026.
    Ensures that 4 24-hour shift groups rotate continuously through [P, P, S, S, M, M, OFF, OFF].
    Supports format='greatday' to map shifts to GreatDay shift names.
    """
    days = get_month_days_info(year, month)
    data = staff_data or DEFAULT_SCHEDULE_DATA

    month_holidays = [d for d in days if d.get('is_holiday')]
    result = {
        'year': year,
        'month': month,
        'month_name': MONTH_NAMES_ID[month],
        'days': days,
        'total_days': len(days),
        'holidays': [{'day': d['day'], 'name': d['holiday_name'], 'day_name': d['day_name']} for d in month_holidays],
        'format': format,
        'groups': []
    }

    # 1. Reguler Group (R1 on weekdays, alternating Saturday piket R3 vs OFF, OFF on Sundays & National Holidays)
    reguler_rows = []
    for person in data.get('reguler', []):
        schedule = []
        piket_rule = person.get('saturday_piket', 'even')
        weekday_shift = person.get('weekday_shift', 'R1')

        for d in days:
            dt = d['date_obj']
            if d['is_sunday'] or d.get('is_holiday'):
                schedule.append('OFF')
            elif d['is_saturday']:
                delta_days_sat = (dt - BASELINE_FIRST_SATURDAY).days
                week_num = delta_days_sat // 7
                if is_piket_day(piket_rule, week_num):
                    schedule.append('R3')
                else:
                    schedule.append('OFF')
            else:
                schedule.append(weekday_shift)

        reguler_rows.append({
            'title': person.get('title', 'Staff'),
            'name': person.get('name', ''),
            'schedule': schedule,
            'group_type': 'reguler',
            'saturday_piket': piket_rule,
            'weekday_shift': weekday_shift
        })

    result['groups'].append({
        'group_name': 'Staff & Supervisor (Reguler)',
        'group_key': 'reguler',
        'rows': reguler_rows
    })

    # 2. 24-Hour Engineering Shift Group (Continuous Rollover from 1 November 2026)
    shift_rows = []
    for person in data.get('shift', []):
        base_offset = person.get('pattern_offset', 0)

        schedule = []
        for d in days:
            dt = d['date_obj']
            # Calculate absolute days elapsed since 1 November 2026
            elapsed_days = (dt - BASELINE_DATE).days
            shift_idx = (base_offset + elapsed_days + shift_rotation_step) % len(SHIFT_CYCLE)
            schedule.append(SHIFT_CYCLE[shift_idx])

        row_data = {
            'title': person.get('title', 'Engineering Shift'),
            'name': person.get('name', ''),
            'schedule': schedule,
            'group_type': 'shift',
            'pattern_offset': base_offset
        }
        if 'custom_greatday_map' in person:
            row_data['custom_greatday_map'] = person['custom_greatday_map']

        shift_rows.append(row_data)

    result['groups'].append({
        'group_name': 'Engineering Shift (24 Jam)',
        'group_key': 'shift',
        'rows': shift_rows
    })

    # 3. Daily Worker Group (R4, default day off on Thursday/Kamis, or configured day_off)
    dw_rows = []
    for person in data.get('daily_worker', []):
        schedule = []
        day_off = person.get('day_off', 3)  # 3 = Kamis (Thursday)
        for d in days:
            if d['weekday'] == day_off or d.get('is_holiday'):
                schedule.append('OFF')
            else:
                schedule.append('R4')

        dw_rows.append({
            'title': person.get('title', 'Daily Worker'),
            'name': person.get('name', ''),
            'schedule': schedule,
            'group_type': 'daily_worker',
            'day_off': day_off
        })

    result['groups'].append({
        'group_name': 'Daily Worker (DW)',
        'group_key': 'daily_worker',
        'rows': dw_rows
    })

    # If GreatDay format is requested, convert all shift codes to GreatDay names
    if format == 'greatday':
        for group in result['groups']:
            for row in group.get('rows', []):
                cmap = row.get('custom_greatday_map') or GREATDAY_SHIFT_MAP
                row['schedule'] = [cmap.get(s, s) for s in row['schedule']]

    return result


def export_schedule_to_excel(schedule_data):
    """
    Creates an Excel spreadsheet (.xlsx) matching the user's template.
    """
    year = schedule_data.get('year', 2026)
    month = schedule_data.get('month', 11)
    month_name = schedule_data.get('month_name', MONTH_NAMES_ID[month])
    days = schedule_data.get('days', get_month_days_info(year, month))
    groups = schedule_data.get('groups', [])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"JADWAL {month_name[:3]} {year}"

    # Base Fonts & Styles
    title_font = Font(name="Calibri", size=13, bold=True, color="000000")
    header_font = Font(name="Calibri", size=10, bold=True, color="000000")
    data_font = Font(name="Calibri", size=9, color="000000")
    bold_data_font = Font(name="Calibri", size=9, bold=True, color="000000")
    small_font = Font(name="Calibri", size=8, color="444444")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    is_greatday = (schedule_data.get('format') == 'greatday') or any(
        any('Shift' in str(v) for v in p.get('schedule', []))
        for g in groups for p in g.get('rows', [])
    )

    # Shift Fills (Supports standard & GreatDay shift codes)
    shift_fills = {
        'P': PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid"),
        'Shift 3': PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid"),
        'Shift 4': PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid"),
        'S': PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
        'Shift 41': PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
        'Shift 42': PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
        'M': PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),
        'Shift 52': PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),
        'Shift 53': PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),
        'OFF': PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),
        'R1': PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid"),
        'Shift 14': PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid"),
        'R3': PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid"),
        'Shift 12': PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid"),
        'R4': PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid"),
        'CT': PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid"),
        'Cuti': PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid"),
    }

    # 1. Company / Department Header
    ws['B2'] = "JADWAL KERJA ENGINEERING DEPARTMENT (GREATDAY)" if is_greatday else "JADWAL KERJA ENGINEERING DEPARTMENT"
    ws['B2'].font = title_font
    ws['B3'] = "TAMAN ANGGREK RESIDENCE"
    ws['B3'].font = Font(name="Calibri", size=11, bold=True)
    ws['B4'] = "Tanjung Duren Timur II, RT.12/RW.1, Grogol Petamburan, Jakarta Barat, Daerah Khusus Ibukota Jakarta 11470."
    ws['B4'].font = small_font

    ws['G2'] = "Off=3"
    ws['G2'].font = header_font
    ws['G3'] = "Shift 12= 2" if is_greatday else "R3= 2"
    ws['G3'].font = header_font

    ws['A5'] = f"BULAN {month_name} {year}"
    ws['A5'].font = Font(name="Calibri", size=11, bold=True)

    # 2. Table Headers
    ws['A6'] = "NO"
    ws['B6'] = "TITLE"
    ws['C6'] = "NAME"

    for col_name in ['A', 'B', 'C']:
        ws[f'{col_name}6'].font = header_font
        ws[f'{col_name}6'].alignment = center_align
        ws[f'{col_name}6'].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        ws[f'{col_name}6'].border = cell_border
        ws[f'{col_name}7'].border = cell_border

    # Fill Dates Header
    for idx, d in enumerate(days, start=4):
        col_letter = get_column_letter(idx)
        # Row 6: Day Name (Sn, Sl, Rb, ...)
        cell_day = ws[f'{col_letter}6']
        cell_day.value = d['day_name']
        cell_day.font = header_font
        cell_day.alignment = center_align
        cell_day.border = cell_border
        if d.get('is_red_day') or d.get('is_weekend') or d.get('is_holiday'):
            cell_day.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        else:
            cell_day.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        # Row 7: Date Number (1, 2, 3, ...)
        cell_date = ws[f'{col_letter}7']
        cell_date.value = d['day']
        cell_date.font = header_font
        cell_date.alignment = center_align
        cell_date.border = cell_border
        if d.get('is_red_day') or d.get('is_weekend') or d.get('is_holiday'):
            cell_date.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        else:
            cell_date.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # 3. Table Rows Data
    current_row = 8
    global_no = 1

    for group_idx, g in enumerate(groups):
        rows = g.get('rows', [])
        for person in rows:
            ws[f'A{current_row}'] = global_no
            ws[f'A{current_row}'].font = bold_data_font
            ws[f'A{current_row}'].alignment = center_align
            ws[f'A{current_row}'].border = cell_border

            ws[f'B{current_row}'] = person.get('title', '')
            ws[f'B{current_row}'].font = data_font
            ws[f'B{current_row}'].alignment = left_align
            ws[f'B{current_row}'].border = cell_border

            ws[f'C{current_row}'] = person.get('name', '')
            ws[f'C{current_row}'].font = bold_data_font
            ws[f'C{current_row}'].alignment = left_align
            ws[f'C{current_row}'].border = cell_border

            sched = person.get('schedule', [])
            for idx, val in enumerate(sched, start=4):
                col_letter = get_column_letter(idx)
                cell_s = ws[f'{col_letter}{current_row}']
                cell_s.value = val
                cell_s.font = bold_data_font if val in ('OFF', 'R3', 'M', 'Shift 52', 'Shift 53', 'Shift 12', 'CT', 'Cuti') else data_font
                cell_s.alignment = center_align
                cell_s.border = cell_border

                if val in shift_fills:
                    cell_s.fill = shift_fills[val]

            current_row += 1
            global_no += 1

        if group_idx < len(groups) - 1:
            current_row += 1

    # 4. Footer Note & Signatures
    note_row = max(current_row + 1, 60)
    ws[f'B{note_row}'] = "Note :"
    ws[f'B{note_row}'].font = Font(name="Calibri", size=10, bold=True)

    sig_row_title = max(note_row + 6, 66)
    sig_row_role = sig_row_title + 1
    current_row = sig_row_title

    legend = [
        ("Kode", "Jam"),
        ("Shift 3 (P)" if not is_greatday else "Shift 3", "07:00 - 15:00"),
        ("Shift 41 (S)" if not is_greatday else "Shift 41", "15:00 - 23:00"),
        ("Shift 52 (M)" if not is_greatday else "Shift 52", "23:00 - 07:00"),
        ("Shift 12 (R3)" if not is_greatday else "Shift 12", "08:30 - 13:30"),
        ("Shift 14 (R1)" if not is_greatday else "Shift 14", "08:30 - 17:00"),
        ("Shift 25", "10:00 - 19:00"),
        ("R4", "08:30 - 17:30")
    ]

    for l_idx, (code, hours) in enumerate(legend):
        r = current_row + l_idx
        ws[f'B{r}'] = code
        ws[f'B{r}'].font = bold_data_font if l_idx == 0 else data_font
        ws[f'C{r}'] = hours
        ws[f'C{r}'].font = bold_data_font if l_idx == 0 else data_font

    signatures = [
        ("G", "Solehudin", "Admin"),
        ("L", "Sandi Adi Putra", "Supervisor"),
        ("S", "Yafi Al Hadi", "Engineering Asst. Manager"),
        ("AA", "Bobby Firdaus", "Property Manager")
    ]

    for col, name, role in signatures:
        ws[f'{col}{sig_row_title}'] = name
        ws[f'{col}{sig_row_title}'].font = Font(name="Calibri", size=9, bold=True)
        ws[f'{col}{sig_row_title}'].alignment = center_align

        ws[f'{col}{sig_row_role}'] = role
        ws[f'{col}{sig_row_role}'].font = small_font
        ws[f'{col}{sig_row_role}'].alignment = center_align

    # Column Widths
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 24
    ws.column_dimensions['C'].width = 24
    for idx in range(4, len(days) + 4):
        col_letter = get_column_letter(idx)
        ws.column_dimensions[col_letter].width = 9.5 if is_greatday else 4.2

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream
