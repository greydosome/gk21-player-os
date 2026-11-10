"""Read-only comparison of midnight and noon sleep query windows.

This diagnoses date grouping; neither window is asserted to match Health.
No network requests, Health writes, credentials, or production setting changes.
"""
import argparse
import copy
from datetime import datetime, time, timedelta, timezone
import importlib.util
from pathlib import Path
import plistlib
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser()
parser.add_argument('--day', type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
                    default=datetime(2026, 11, 4).date())
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('base', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
workflow = copy.deepcopy(b.workflow)
source = next(a for a in b.actions if a['WFWorkflowActionIdentifier'].endswith('filter.health.quantity'))
b.actions = []
zone = ZoneInfo('Asia/Seoul')
midnight = datetime.combine(args.day, time(), zone)
windows = [('자정 기준', midnight, midnight + timedelta(days=1)),
           ('전날 정오부터', midnight - timedelta(hours=12), midnight + timedelta(hours=12))]
parts = [f'{args.day} 수면 날짜 범위 검사\n단위: 초 / 표본 수\n']
b.action('comment', WFCommentActionText='읽기 전용 날짜 범위 비교. 전날 저녁 수면 누락 여부를 검사합니다. 출처 중복 병합/건강 앱 집계 재현/서버 전송은 하지 않습니다.')
for label, lower, upper in windows:
    parts.append('\n' + label + '\n')
    for stage in ('Core', 'REM', 'Deep'):
        zero = b.action('number', WFNumberActionNumber='0')
        total_name = label + stage
        b.set_variable(total_name, b.output(zero, 'Number'))
        b.set_variable(total_name + ' Count', b.output(zero, 'Number'))
        b.set_variable(total_name + ' Minute Boundaries', b.output(zero, 'Number'))
        empty = b.action('gettext', WFTextActionText='없음')
        b.set_variable(total_name + ' Last', b.output(empty, 'Text'))
        b.action('nothing')
        p = copy.deepcopy(source['WFWorkflowActionParameters'])
        p.pop('UUID')
        templates = p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates']
        templates[1] = {'Property': 'Start Date', 'Operator': 1003, 'Bounded': True,
                        'Removable': False, 'Values': {
                            'Date': (lower - timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None),
                            'AnotherDate': (upper + timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None)}}
        templates[2]['Values']['String'] = stage
        found = b.action('filter.health.quantity', **p)
        loop = b.uid()
        b.action('repeat.each', GroupingIdentifier=loop, WFControlFlowMode=0,
                 WFInput=b.attachment(b.output(found, 'Health Samples')))
        dates = {}
        for prop in ('Start Date', 'End Date'):
            dates[prop] = b.output(b.action('properties.health.quantity', WFContentItemPropertyName=prop,
                                    WFInput=b.attachment(b.variable('Repeat Item'))), prop)
        stamp = b.output(b.action('format.date', WFDate=b.text(dates['Start Date']),
                                 WFDateFormatStyle='Custom', WFDateFormat='yyyyMMddHHmmss',
                                 WFLocale='en_US_POSIX'), 'Formatted Date')
        stamp = b.output(b.action('math', WFInput=b.attachment(stamp), WFMathOperation='÷',
                                 WFMathOperand=1), 'Calculation Result')
        inside, after = b.uid(), b.uid()
        for group, limit in ((inside, lower), (after, upper)):
            b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=0,
                     WFInput={'Type':'Variable','Variable':b.attachment(stamp)},
                     WFCondition=2, WFNumberValue=str(int(limit.strftime('%Y%m%d%H%M%S')) - 1))
            if group == after:
                b.action('nothing')
                b.action('conditional', GroupingIdentifier=after, WFControlFlowMode=1)
        seconds = b.output(b.action('gettimebetweendates', WFTimeUntilFromDate=b.text(dates['Start Date']),
                                   WFInput=b.text(dates['End Date']), WFTimeUntilUnit='Seconds'), 'Time Between Dates')
        summed = b.output(b.action('math', WFInput=b.attachment(b.variable(total_name)),
                                  WFMathOperation='+', WFMathOperand=b.attachment(seconds)), 'Calculation Result')
        b.set_variable(total_name, summed)
        # Separately diagnose display rounding without changing raw elapsed time.
        minute_dates = {}
        for prop in ('Start Date', 'End Date'):
            minute_dates[prop] = b.output(b.action('format.date', WFDate=b.text(dates[prop]),
                WFDateFormatStyle='Custom', WFDateFormat="yyyy-MM-dd'T'HH:mm:00XXX",
                WFLocale='en_US_POSIX'), 'Formatted Date')
        minute_seconds = b.output(b.action('gettimebetweendates',
            WFTimeUntilFromDate=b.text(minute_dates['Start Date']),
            WFInput=b.text(minute_dates['End Date']), WFTimeUntilUnit='Seconds'), 'Time Between Dates')
        boundary_sum = b.output(b.action('math', WFInput=b.attachment(b.variable(total_name + ' Minute Boundaries')),
            WFMathOperation='+', WFMathOperand=b.attachment(minute_seconds)), 'Calculation Result')
        b.set_variable(total_name + ' Minute Boundaries', boundary_sum)
        counted = b.output(b.action('math', WFInput=b.attachment(b.variable(total_name + ' Count')),
                                   WFMathOperation='+', WFMathOperand=1), 'Calculation Result')
        b.set_variable(total_name + ' Count', counted)
        last = b.action('format.date', WFDate=b.text(dates['Start Date']), WFDateFormatStyle='Custom',
                        WFDateFormat='MM-dd HH:mm:ss', WFLocale='en_US_POSIX')
        b.set_variable(total_name + ' Last', b.output(last, 'Formatted Date'))
        for group in (after, inside):
            b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=2)
        b.action('repeat.each', GroupingIdentifier=loop, WFControlFlowMode=2)
        boundary_minutes = b.output(b.action('math', WFInput=b.attachment(b.variable(total_name + ' Minute Boundaries')),
            WFMathOperation='÷', WFMathOperand=60), 'Calculation Result')
        parts.extend([stage + ': ', b.variable(total_name), ' / ', b.variable(total_name + ' Count'),
                      '\n분 경계 차이 ', boundary_minutes, '분',
                      '\n마지막 표본 ', b.variable(total_name + ' Last'), '\n'])
parts.append('\n확인용입니다. 저장·전송하지 않았습니다.')
b.action('showresult', Text=b.text(*parts))
workflow.update(WFWorkflowActions=b.actions, WFWorkflowName='GK21 Sleep Window Check')
path = b.OUT / 'GK21-Sleep-Window-Check.unsigned.shortcut'
path.write_bytes(plistlib.dumps(workflow))
print(path)
