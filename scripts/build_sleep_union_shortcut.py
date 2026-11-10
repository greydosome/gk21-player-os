"""Read-only free sleep checker: merge overlapping stages and group sleep sessions.

Sessions separated by more than 3 hours are attributed to their final wake date.
This is explicit session logic, not a claim to reproduce Apple's proprietary
source priority. Compare real-device results before enabling any upload.
"""
import copy
import importlib.util
import plistlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('base', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
wf = copy.deepcopy(b.workflow)
b.actions = []


def out(identifier, name='Calculation Result'):
    return b.output(identifier, name)


def var(name):
    return b.variable(name)


def setv(name, ref):
    b.set_variable(name, ref)


def zero(name):
    ref = b.action('number', WFNumberActionNumber='0')
    setv(name, out(ref, 'Number'))


def math(left, op, right):
    return out(b.action('math', WFInput=b.attachment(left), WFMathOperation=op,
                        WFMathOperand=b.attachment(right) if isinstance(right, dict) else right))


def begin_if(left, op, right):
    group = b.uid()
    b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=0,
             WFInput={'Type': 'Variable', 'Variable': b.attachment(left)}, WFCondition=op,
             WFNumberValue=b.text(right) if isinstance(right, dict) else str(right))
    return group


def end_if(group):
    b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=2)


def seconds(start, end):
    return out(b.action('gettimebetweendates', WFTimeUntilFromDate=b.text(start),
                        WFInput=b.text(end), WFTimeUntilUnit='Seconds'), 'Time Between Dates')


b.action('comment', WFCommentActionText=(
    '무료 수면 검증 · 업로드 없음\n'
    'Core/REM/Deep 및 단계 미지정 수면 구간을 시간순으로 정렬하고 겹친 시간은 한 번만 셉니다. '
    '3시간 넘게 떨어진 구간을 별도 수면으로 구분하고 마지막 기상 날짜에 귀속합니다. '
    '건강 앱의 출처 우선순위를 그대로 재현한다고 보장하지 않으므로 비교 검증용입니다.'))
zero('Has Samples')
for stage in ('Core', 'REM', 'Deep', 'Asleep', 'Unspecified'):
    b.action('nothing')
    source = next(a for a in wf['WFWorkflowActions'] if a['WFWorkflowActionIdentifier'].endswith('filter.health.quantity'))
    params = copy.deepcopy(source['WFWorkflowActionParameters'])
    params.pop('UUID')
    templates = params['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates']
    templates[1]['Values']['Number'] = '2'
    templates[2]['Values']['String'] = stage
    found = b.action('filter.health.quantity', **params)
    found_count = b.action('count', Input=b.attachment(out(found, 'Health Samples')), WFCountType='Items')
    nonempty = begin_if(out(found_count, 'Count'), 2, 0)
    b.action('appendvariable', WFVariableName='Sleep Samples', WFInput=b.attachment(out(found, 'Health Samples')))
    one = b.action('number', WFNumberActionNumber='1')
    setv('Has Samples', out(one, 'Number'))
    end_if(nonempty)

has_samples = begin_if(var('Has Samples'), 2, 0)
count = b.action('count', Input=b.attachment(var('Sleep Samples')), WFCountType='Items')
params = copy.deepcopy(params)
params['WFContentItemInputParameter'] = b.attachment(var('Sleep Samples'))
params['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates'] = templates[:2]
params.update(WFContentItemSortProperty='Start Date', WFContentItemSortOrder='Oldest First')
ordered = b.action('filter.health.quantity', **params)

now = out(b.action('date', WFDateActionMode='Current Date'), 'Date')
today = out(b.action('format.date', WFDate=b.text(now), WFDateFormatStyle='Custom',
                     WFDateFormat='yyyy-MM-dd', WFLocale='en_US_POSIX'), 'Formatted Date')
midnight = out(b.action('date', WFDateActionMode='Specified Date',
                       WFDateActionDate=b.text(today, 'T00:00:00+09:00')), 'Date')
epoch = out(b.action('date', WFDateActionMode='Specified Date',
                    WFDateActionDate='1970-01-01T00:00:00+00:00'), 'Date')
today_epoch = seconds(epoch, midnight)
window_start = math(today_epoch, '-', 21600)
window_end = math(today_epoch, '+', 64800)
for name in ('Day Seconds', 'Window Seconds', 'Session Seconds', 'Last End', 'Has Session', 'Raw Seconds', 'Union Seconds'):
    zero(name)


def finish_session():
    exists = begin_if(var('Has Session'), 2, 0)
    belongs = begin_if(var('Last End'), 3, today_epoch)
    setv('Day Seconds', math(var('Day Seconds'), '+', var('Session Seconds')))
    end_if(belongs)
    end_if(exists)


loop = b.uid()
b.action('repeat.each', GroupingIdentifier=loop, WFControlFlowMode=0,
         WFInput=b.attachment(out(ordered, 'Health Samples')))
start_date = out(b.action('properties.health.quantity', WFContentItemPropertyName='Start Date',
                         WFInput=b.attachment(var('Repeat Item'))), 'Start Date')
end_date = out(b.action('properties.health.quantity', WFContentItemPropertyName='End Date',
                       WFInput=b.attachment(var('Repeat Item'))), 'End Date')
start, end = seconds(epoch, start_date), seconds(epoch, end_date)
setv('Raw Seconds', math(var('Raw Seconds'), '+', math(end, '-', start)))
exists = begin_if(var('Has Session'), 2, 0)
gap = begin_if(math(start, '-', var('Last End')), 2, 10800)
finish_session()
zero('Session Seconds')
zero('Last End')
zero('Has Session')
end_if(gap)
end_if(exists)
setv('Effective Start', start)
overlap = begin_if(var('Last End'), 2, start)
setv('Effective Start', var('Last End'))
end_if(overlap)
delta = math(end, '-', var('Effective Start'))
extends = begin_if(delta, 2, 0)
setv('Session Seconds', math(var('Session Seconds'), '+', delta))
setv('Union Seconds', math(var('Union Seconds'), '+', delta))
setv('Window Start', var('Effective Start'))
clip_start = begin_if(window_start, 2, var('Window Start'))
setv('Window Start', window_start)
end_if(clip_start)
setv('Window End', end)
clip_end = begin_if(var('Window End'), 2, window_end)
setv('Window End', window_end)
end_if(clip_end)
window_delta = math(var('Window End'), '-', var('Window Start'))
in_window = begin_if(window_delta, 2, 0)
setv('Window Seconds', math(var('Window Seconds'), '+', window_delta))
end_if(in_window)
setv('Last End', end)
one = out(b.action('number', WFNumberActionNumber='1'), 'Number')
setv('Has Session', one)
end_if(extends)
b.action('repeat.each', GroupingIdentifier=loop, WFControlFlowMode=2)
finish_session()
day_minutes = math(var('Day Seconds'), '÷', 60)
window_minutes = math(var('Window Seconds'), '÷', 60)
raw_minutes = math(var('Raw Seconds'), '÷', 60)
union_minutes = math(var('Union Seconds'), '÷', 60)
b.action('showresult', Text=b.text(
    '오늘 기상한 수면 · 겹침 제거\n', today, '\n\n',
    '오늘 수면: ', day_minutes, '분\n',
    '오후 6시 기준: ', window_minutes, '분\n',
    '2일 원본 합계: ', raw_minutes, '분\n',
    '2일 겹침 제거: ', union_minutes, '분\n',
    '검사한 구간: ', out(count, 'Count'), '개\n\n',
    '비교 확인용입니다. 서버에 전송하지 않았습니다.'))
b.action('conditional', GroupingIdentifier=has_samples, WFControlFlowMode=1)
b.action('showresult', Text=b.text('수면 기록이 없습니다. 0시간으로 저장하지 않습니다.'))
end_if(has_samples)
wf.update(WFWorkflowName='GK21 무료 수면 검증', WFWorkflowActions=b.actions)
path = b.OUT / 'GK21-Sleep-Union-Check.unsigned.shortcut'
path.write_bytes(plistlib.dumps(wf))
print(path)
print(f'{len(b.actions)} actions; read-only union/session diagnostic')
