"""Read-only daily stage audit, before applying any sleep-value filters."""
import copy
import importlib.util
from pathlib import Path
import plistlib

spec = importlib.util.spec_from_file_location('base', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
wf = copy.deepcopy(b.workflow)
b.actions = []
o = b.output
v = b.variable

def condition(ref, code, value=None):
    group = b.uid()
    params = dict(GroupingIdentifier=group, WFControlFlowMode=0,
                  WFInput={'Type': 'Variable', 'Variable': b.attachment(ref)}, WFCondition=code)
    if value is not None:
        params['WFNumberValue'] = str(value)
    b.action('conditional', **params)
    return group

def end(group):
    b.action('conditional', GroupingIdentifier=group, WFControlFlowMode=2)

b.action('comment', WFCommentActionText='읽기 전용. 오늘 시작한 모든 수면 표본을 값별로 합산합니다. 날짜·출처 집계 비교용이며 저장/전송하지 않습니다.')
b.action('nothing')
source = next(a for a in wf['WFWorkflowActions'] if a['WFWorkflowActionIdentifier'].endswith('filter.health.quantity'))
p = copy.deepcopy(source['WFWorkflowActionParameters'])
p.pop('UUID')
t = p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates']
p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates'] = [t[0], {
    'Property':'Start Date', 'Operator':1002, 'Bounded':True, 'Removable':False, 'Values':{}}]
found = b.action('filter.health.quantity', **p)
count = b.action('count', Input=b.attachment(o(found,'Health Samples')), WFCountType='Items')
has = condition(o(count,'Count'),2,0)
empty = b.action('gettext',WFTextActionText='{}')
dictionary = b.action('detect.dictionary', WFInput=b.attachment(o(empty,'Text')))
b.set_variable('Stage Totals', o(dictionary,'Dictionary'))
loop = b.uid()
b.action('repeat.each',GroupingIdentifier=loop,WFControlFlowMode=0,WFInput=b.attachment(o(found,'Health Samples')))
refs = {}
for prop in ('Value','Start Date','End Date'):
    refs[prop] = o(b.action('properties.health.quantity', WFContentItemPropertyName=prop,
                           WFInput=b.attachment(v('Repeat Item'))),prop)
key = o(b.action('gettext', WFTextActionText=b.text(refs['Value'])),'Text')
duration = o(b.action('gettimebetweendates',WFTimeUntilFromDate=b.text(refs['Start Date']),
                     WFInput=b.text(refs['End Date']),WFTimeUntilUnit='Seconds'),'Time Between Dates')
previous = o(b.action('getvalueforkey',WFGetDictionaryValueType='Value',WFDictionaryKey=b.text(key),
                     WFInput=b.attachment(v('Stage Totals'))),'Dictionary Value')
zero = o(b.action('number',WFNumberActionNumber='0'),'Number')
b.set_variable('Previous Seconds',zero)
exists = condition(previous,100)
b.set_variable('Previous Seconds',previous)
end(exists)
summed = o(b.action('math', WFInput=b.attachment(v('Previous Seconds')), WFMathOperation='+',
                     WFMathOperand=b.attachment(duration)),'Calculation Result')
updated = b.action('setvalueforkey',WFDictionaryKey=b.text(key),WFDictionaryValue=b.text(summed),
                   WFDictionary=b.attachment(v('Stage Totals')))
b.set_variable('Stage Totals',o(updated,'Dictionary'))
b.action('repeat.each',GroupingIdentifier=loop,WFControlFlowMode=2)
b.action('showresult',Text=b.text('오늘 전체 수면 값 · 초\n',v('Stage Totals'),'\n\n표본 수: ',o(count,'Count'),
    '\n읽기 전용. 서버 전송 없음.'))
b.action('conditional',GroupingIdentifier=has,WFControlFlowMode=1)
b.action('showresult',Text=b.text('오늘 수면 표본 없음. 저장하지 않습니다.'))
end(has)
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Sleep Stage Audit')
path=b.OUT/'GK21-Sleep-Stage-Audit.unsigned.shortcut'
path.write_bytes(plistlib.dumps(wf))
print(path)
