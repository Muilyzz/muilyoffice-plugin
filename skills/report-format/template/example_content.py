# Minimal example: python3 make_report.py example_content.py 보고-예시_검토보고서.pdf
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.path.dirname(os.path.abspath(sys.argv[0])))
from make_report import *
URL = 'https://example.com/review'
body = (
  summary(['예시 기능을 추가함.', 'CI 통과. 차단 사유 없음.'])
  + chg(['이전 동작 설명'], ['새 동작 설명'])
  + section('1. 개요', table(['구분', '내용'], [['대상', f'<a href="{URL}">예시</a>'], ['CI', 'CircleCI <code>build-and-test</code> 통과']], widths=['24mm', None]))
  + section('2. 배경', ul(['배경 1', ('배경 2', ['세부 사항'])]))
  + section('3. 변경 내용', ul(['변경 1']), note('참고 사항.'))
  + section('4. 검증 결과', table(['항목', '결과'], [['테스트', '<span class="ok">통과</span>']]))
  + section('5. 위험 요소', table(['항목', '내용'], [['위험', '설명']], widths=['44mm', None]))
  + section('6. 판정', verdict('ok', URL, ['차단 사유 없음.'], order=['<b>① 첫째</b> → ② 둘째']))
)
HTML = document(header='PR #n 검토 보고', body=body, kind='검 토 보 고 서', title='예시 기능 검토',
                date='2026-11-01', author='기안자', url=URL, target='예시 저장소', approver='결재자', approver_note='merge 대기')
