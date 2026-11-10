"""Free, read-only check of Apple's daily Exercise Minutes (not workout sessions)."""
import copy
import importlib.util
from pathlib import Path
import plistlib

spec = importlib.util.spec_from_file_location('base', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
wf = copy.deepcopy(b.workflow)
b.actions = []
b.action('comment', WFCommentActionText=(
    '무료 운동 링 시간 확인. 운동 세션의 종목별 시간과는 다른 활동 지표입니다. '
    '오늘의 Exercise Minutes를 일별 그룹으로 조회하며 전송/저장하지 않습니다.'))
b.action('nothing')
found = b.action('filter.health.quantity', WFContentItemFilter={
    'WFSerializationType': 'WFContentPredicateTableTemplate', 'Value': {
        'WFActionParameterFilterPrefix': 1, 'WFContentPredicateBoundedDate': False,
        'WFActionParameterFilterTemplates': [
            {'Property': 'Type', 'Operator': 4, 'Bounded': True, 'Removable': False,
             'Values': {'Enumeration': {'Value': 'Exercise Minutes', 'WFSerializationType': 'WFStringSubstitutableState'}}},
            {'Property': 'Start Date', 'Operator': 1002, 'Bounded': True, 'Removable': False, 'Values': {}},
        ]}}, WFContentItemInputParameter='', WFContentItemLimitEnabled=False,
    WFHKSampleFilteringGroupBy='Day', WFHKSampleFilteringFillMissing=False)
count = b.action('count', Input=b.attachment(b.output(found, 'Health Samples')), WFCountType='Items')
group = b.uid()
b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=0,
         WFInput={'Type': 'Variable', 'Variable': b.attachment(b.output(count, 'Count'))},
         WFCondition=2, WFNumberValue='0')
value = b.action('properties.health.quantity', WFContentItemPropertyName='Value',
                 WFInput=b.attachment(b.output(found, 'Health Samples')))
total = b.action('statistics', WFStatisticsOperation='Sum', Input=b.attachment(b.output(value, 'Value')))
b.action('showresult', Text=b.text('오늘 운동 링 시간: ', b.output(total, 'Statistics'),
    '분\n\n종목별 운동 기록이 아닌 Apple 운동 링 지표입니다.\n서버에 전송하지 않았습니다.'))
b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=1)
b.action('showresult', Text=b.text('오늘 운동 링 시간 표본이 없습니다. 0분으로 저장하지 않습니다.'))
b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=2)
wf.update(WFWorkflowName='GK21 무료 운동 시간 확인', WFWorkflowActions=b.actions)
path = b.OUT / 'GK21-Exercise-Minutes-Check.unsigned.shortcut'
path.write_bytes(plistlib.dumps(wf))
print(path)
