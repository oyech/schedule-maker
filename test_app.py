import unittest
from datetime import date
from schedule_generator import generate_schedule_grid, export_schedule_to_excel, DEFAULT_SCHEDULE_DATA
from app import app
import openpyxl

class TestScheduleApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_routes(self):
        # / redirects to /schedule
        res_root = self.client.get('/')
        self.assertEqual(res_root.status_code, 302)
        self.assertIn('/schedule', res_root.headers.get('Location', ''))

        # /schedule returns 200
        res_sched = self.client.get('/schedule')
        self.assertEqual(res_sched.status_code, 200)

        # /schedule-greatday returns 200
        res_gd = self.client.get('/schedule-greatday')
        self.assertEqual(res_gd.status_code, 200)

        # defaults API
        res_def = self.client.get('/api/schedule/defaults')
        self.assertEqual(res_def.status_code, 200)
        data = res_def.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['default_data']['reguler']), 27)
        self.assertEqual(len(data['default_data']['shift']), 12)
        self.assertEqual(len(data['default_data']['daily_worker']), 10)

    def test_november_2026_schedule(self):
        # November 2026: 30 days
        grid_nov = generate_schedule_grid(year=2026, month=11)
        self.assertEqual(grid_nov['total_days'], 30)
        self.assertEqual(grid_nov['month_name'], 'NOVEMBER')

        # 1. Reguler staff checks
        reguler_rows = grid_nov['groups'][0]['rows']
        self.assertEqual(len(reguler_rows), 27)

        # Yafi Al- Hadi: Ast Manager, all Saturdays OFF
        yafi = reguler_rows[0]
        self.assertEqual(yafi['name'], 'Yafi Al- Hadi')
        for sat_idx in [6, 13, 20, 27]: # 7, 14, 21, 28 Nov
            self.assertEqual(yafi['schedule'][sat_idx], 'OFF')

        # Sandi Adi Putra: piket even (7 & 21 Nov)
        sandi = reguler_rows[1]
        self.assertEqual(sandi['name'], 'Sandi Adi Putra')
        self.assertEqual(sandi['schedule'][6], 'R3')   # 7 Nov
        self.assertEqual(sandi['schedule'][13], 'OFF') # 14 Nov
        self.assertEqual(sandi['schedule'][20], 'R3')  # 21 Nov
        self.assertEqual(sandi['schedule'][27], 'OFF') # 28 Nov

        # Florentinus Frengky: piket odd (14 & 28 Nov)
        frengky = reguler_rows[2]
        self.assertEqual(frengky['name'], 'Florentinus Frengky')
        self.assertEqual(frengky['schedule'][6], 'OFF')  # 7 Nov
        self.assertEqual(frengky['schedule'][13], 'R3')  # 14 Nov
        self.assertEqual(frengky['schedule'][20], 'OFF') # 21 Nov
        self.assertEqual(frengky['schedule'][27], 'R3')  # 28 Nov

        # Resya: piket all 4 Saturdays
        resya = next(r for r in reguler_rows if r['name'] == 'Resya')
        self.assertEqual(resya['schedule'][6], 'R3')
        self.assertEqual(resya['schedule'][13], 'R3')
        self.assertEqual(resya['schedule'][20], 'R3')
        self.assertEqual(resya['schedule'][27], 'R3')

        # Agus Gondola: weekdays P, piket odd (14 & 28 Nov)
        agus = next(r for r in reguler_rows if r['name'] == 'Agus')
        self.assertEqual(agus['schedule'][1], 'P')     # 2 Nov (Mon) -> P
        self.assertEqual(agus['schedule'][6], 'OFF')   # 7 Nov -> OFF
        self.assertEqual(agus['schedule'][13], 'R3')   # 14 Nov -> R3

        # 2. Shift checks (Continuous 8-day cycle from 1 Nov 2026)
        shift_rows = grid_nov['groups'][1]['rows']
        self.assertEqual(len(shift_rows), 12)

        # Regu 1 (Deri Kurniawan): starts Nov 1 with S|S
        deri = shift_rows[0]
        self.assertEqual(deri['schedule'][0], 'S')    # 1 Nov
        self.assertEqual(deri['schedule'][1], 'S')    # 2 Nov
        self.assertEqual(deri['schedule'][2], 'M')    # 3 Nov
        self.assertEqual(deri['schedule'][3], 'M')    # 4 Nov
        self.assertEqual(deri['schedule'][4], 'OFF')  # 5 Nov
        self.assertEqual(deri['schedule'][5], 'OFF')  # 6 Nov
        self.assertEqual(deri['schedule'][6], 'P')    # 7 Nov
        self.assertEqual(deri['schedule'][7], 'P')    # 8 Nov

        # Regu 4 (Ichsan Agus S.): starts Nov 1 with P|P
        ichsan = next(r for r in shift_rows if r['name'] == 'Ichsan Agus S.')
        self.assertEqual(ichsan['schedule'][0], 'P')
        self.assertEqual(ichsan['schedule'][1], 'P')
        self.assertEqual(ichsan['schedule'][2], 'S')
        self.assertEqual(ichsan['schedule'][3], 'S')
        self.assertEqual(ichsan['schedule'][4], 'M')
        self.assertEqual(ichsan['schedule'][5], 'M')
        self.assertEqual(ichsan['schedule'][6], 'OFF')
        self.assertEqual(ichsan['schedule'][7], 'OFF')

        # 3. Daily Worker checks
        dw_rows = grid_nov['groups'][2]['rows']
        self.assertEqual(len(dw_rows), 10)
        abdul = dw_rows[0]
        self.assertEqual(abdul['schedule'][0], 'R4')   # Sun 1 Nov -> R4
        self.assertEqual(abdul['schedule'][4], 'OFF')  # Thu 5 Nov -> OFF
        self.assertEqual(abdul['schedule'][11], 'OFF') # Thu 12 Nov -> OFF
        self.assertEqual(abdul['schedule'][18], 'OFF') # Thu 19 Nov -> OFF
        self.assertEqual(abdul['schedule'][25], 'OFF') # Thu 26 Nov -> OFF

    def test_greatday_format_and_custom_shifts(self):
        grid_gd = generate_schedule_grid(year=2026, month=11, format='greatday')
        self.assertEqual(grid_gd['format'], 'greatday')

        # Deri Kurniawan (Shift 41, 52, Shift 3)
        deri = grid_gd['groups'][1]['rows'][0]
        self.assertEqual(deri['schedule'][0], 'Shift 41') # 1 Nov (S)
        self.assertEqual(deri['schedule'][2], 'Shift 52') # 3 Nov (M)
        self.assertEqual(deri['schedule'][4], 'OFF')      # 5 Nov (OFF)
        self.assertEqual(deri['schedule'][6], 'Shift 3')  # 7 Nov (P)

        # Eko Faishal (DW in shift): uses Shift 4, 42, 53
        eko = next(r for r in grid_gd['groups'][1]['rows'] if 'Eko Faishal' in r['name'])
        self.assertEqual(eko['schedule'][0], 'Shift 4')   # 1 Nov (P)
        self.assertEqual(eko['schedule'][2], 'Shift 42')  # 3 Nov (S)
        self.assertEqual(eko['schedule'][4], 'Shift 53')  # 5 Nov (M)
        self.assertEqual(eko['schedule'][6], 'OFF')       # 7 Nov (OFF)

        # Reguler in GreatDay: Sandi Adi Putra
        sandi = grid_gd['groups'][0]['rows'][1]
        self.assertEqual(sandi['schedule'][0], 'OFF')       # 1 Nov (Sun)
        self.assertEqual(sandi['schedule'][1], 'Shift 14')  # 2 Nov (Mon)
        self.assertEqual(sandi['schedule'][6], 'Shift 12')  # 7 Nov (Sat piket)

        # Daily Worker in GreatDay: R4, OFF on Thu
        abdul = grid_gd['groups'][2]['rows'][0]
        self.assertEqual(abdul['schedule'][0], 'R4')
        self.assertEqual(abdul['schedule'][4], 'OFF')

    def test_excel_export_structure(self):
        grid_nov = generate_schedule_grid(year=2026, month=11, format='greatday')
        stream = export_schedule_to_excel(grid_nov)
        wb = openpyxl.load_workbook(stream)
        ws = wb.active
        self.assertEqual(ws.title, "JADWAL NOV 2026")

        # Check title & header
        self.assertIn("JADWAL KERJA ENGINEERING DEPARTMENT", ws['B2'].value)
        self.assertEqual(ws['G2'].value, "Off=3")
        self.assertEqual(ws['G3'].value, "Shift 12= 2")

        # Check Signatures: Solehudin, Sandi Adi Putra, Yafi Al Hadi, Bobby Firdaus
        signers = [ws['G66'].value, ws['L66'].value, ws['S66'].value, ws['AA66'].value]
        self.assertIn("Solehudin", signers)
        self.assertIn("Sandi Adi Putra", signers)
        self.assertIn("Yafi Al Hadi", signers)
        self.assertIn("Bobby Firdaus", signers)

if __name__ == '__main__':
    unittest.main()
