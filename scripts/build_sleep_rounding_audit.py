"""Fixed-date, read-only rounding comparison; nonblocking notification output."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import plistlib

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('build_sleep_stage_audit.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
b = a.b
wf = copy.deepcopy(a.wf)
actions = []
# Exact historical day: 2026-11-04 00:00 KST through 2026-11-05 00:00 KST.
start = datetime(2026, 11, 3, 15, tzinfo=timezone.utc).replace(tzinfo=None)
finish = start + timedelta(days=1)
for action in wf['WFWorkflowActions']:
    name, p = action['WFWorkflowActionIdentifier'], action['WFWorkflowActionParameters']
    if name.endswith('filter.health.quantity'):
        templates = p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates']
        templates[1] = {'Property':'Start Date','Operator':1003,'Bounded':True,'Removable':False,
                        'Values':{'Date':start,'AnotherDate':finish}}
    if name.endswith('comment'):
        p['WFCommentActionText'] = '2026-11-04의 읽기 전용 반올림 비교. 반올림 합계는 가설 검사용이며 건강 앱과 같은 계산법이라고 보장하지 않습니다. 저장/전송 없음.'
    if name.endswith('showresult'):
        action = {'WFWorkflowActionIdentifier':'is.workflow.actions.notification',
                  'WFWorkflowActionParameters':{'UUID':p['UUID'],'WFNotificationActionTitle':'GK21 11월 4일 검사',
                    'WFNotificationActionBody':b.text('초/구간별 반올림 분: ',b.variable('Stage Totals')),
                    'WFNotificationActionSound':False}}
        # Avoid claiming a result exists on the no-record branch.
        if '오늘 수면 표본 없음' in str(p):
            action['WFWorkflowActionParameters']['WFNotificationActionBody'] = '11월 4일 표본 없음. 저장하지 않았습니다.'
    actions.append(action)
    if name.endswith('setvariable') and p.get('WFVariableName') == 'Stage Totals' and any(
            x['WFWorkflowActionIdentifier'].endswith('repeat.each') and
            x['WFWorkflowActionParameters'].get('WFControlFlowMode') == 0 for x in actions):
        # After raw seconds are updated, add rounded-per-segment minutes in separate dictionary keys.
        b.actions = []
        minutes = b.output(b.action('math',WFInput=b.attachment(a.duration),WFMathOperation='÷',WFMathOperand=60),'Calculation Result')
        rounded = b.output(b.action('round',WFInput=b.attachment(minutes),WFRoundTo='Ones Place',WFRoundMode='Normal'),'Rounded Number')
        key = b.output(b.action('gettext',WFTextActionText=b.text(a.key,' rounded')),'Text')
        previous = b.output(b.action('getvalueforkey',WFGetDictionaryValueType='Value',WFDictionaryKey=b.text(key),WFInput=b.attachment(b.variable('Stage Totals'))),'Dictionary Value')
        zero = b.output(b.action('number',WFNumberActionNumber='0'),'Number')
        b.set_variable('Previous Rounded',zero)
        exists=a.condition(previous,100)
        b.set_variable('Previous Rounded',previous)
        a.end(exists)
        total=b.output(b.action('math',WFInput=b.attachment(b.variable('Previous Rounded')),WFMathOperation='+',WFMathOperand=b.attachment(rounded)),'Calculation Result')
        updated=b.output(b.action('setvalueforkey',WFDictionaryKey=b.text(key),WFDictionaryValue=b.text(total),WFDictionary=b.attachment(b.variable('Stage Totals'))),'Dictionary')
        b.set_variable('Stage Totals',updated)
        actions.extend(b.actions)
wf.update(WFWorkflowActions=actions,WFWorkflowName='GK21 Sleep Rounding Nov4')
path=b.OUT/'GK21-Sleep-Rounding-Nov4.unsigned.shortcut'
path.write_bytes(plistlib.dumps(wf))
print(path)
