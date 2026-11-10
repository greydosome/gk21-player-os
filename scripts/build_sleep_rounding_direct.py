"""Fixed-day rounding audit using scalar totals, without dictionary conversion."""
import copy
from datetime import datetime
import importlib.util
from pathlib import Path
import plistlib

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build_sleep_check_shortcut.py'))
b=importlib.util.module_from_spec(s); s.loader.exec_module(b)
wf=copy.deepcopy(b.workflow); b.actions=[]
b.action('comment',WFCommentActionText='11월 4일 수면 반올림 가설 검사. 원본 초와 구간별 반올림 분을 비교합니다. 건강 앱과 같다는 보장은 없으며 저장/전송하지 않습니다.')
results=[]
for stage in ('Core','REM','Deep'):
    for name in ('Raw','Rounded'):
        ident=b.action('number',WFNumberActionNumber='0'); b.set_variable(stage+' '+name,b.output(ident,'Number'))
    b.action('nothing')
    source=next(x for x in wf['WFWorkflowActions'] if x['WFWorkflowActionIdentifier'].endswith('filter.health.quantity'))
    p=copy.deepcopy(source['WFWorkflowActionParameters']); p.pop('UUID')
    templates=p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates']
    templates[1]={'Property':'Start Date','Operator':1003,'Bounded':True,'Removable':False,
        'Values':{'Date':datetime(2026,11,3,15),'AnotherDate':datetime(2026,11,4,15)}}
    templates[2]['Values']['String']=stage
    found=b.action('filter.health.quantity',**p)
    loop=b.uid(); b.action('repeat.each',GroupingIdentifier=loop,WFControlFlowMode=0,WFInput=b.attachment(b.output(found,'Health Samples')))
    start=b.output(b.action('properties.health.quantity',WFContentItemPropertyName='Start Date',WFInput=b.attachment(b.variable('Repeat Item'))),'Start Date')
    day=b.output(b.action('format.date',WFDate=b.text(start),WFDateFormatStyle='Custom',WFDateFormat='yyyy-MM-dd',WFLocale='en_US_POSIX'),'Formatted Date')
    group=b.uid(); b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=0,
        WFInput={'Type':'Variable','Variable':b.attachment(day)},WFCondition=4,WFConditionalActionString='2026-11-04')
    end=b.output(b.action('properties.health.quantity',WFContentItemPropertyName='End Date',WFInput=b.attachment(b.variable('Repeat Item'))),'End Date')
    seconds=b.output(b.action('gettimebetweendates',WFTimeUntilFromDate=b.text(start),WFInput=b.text(end),WFTimeUntilUnit='Seconds'),'Time Between Dates')
    minutes=b.output(b.action('math',WFInput=b.attachment(seconds),WFMathOperation='÷',WFMathOperand=60),'Calculation Result')
    rounded=b.output(b.action('round',WFInput=b.attachment(minutes),WFRoundTo='Ones Place',WFRoundMode='Normal'),'Rounded Number')
    for name,ref in [('Raw',seconds),('Rounded',rounded)]:
        summed=b.action('math',WFInput=b.attachment(b.variable(stage+' '+name)),WFMathOperation='+',WFMathOperand=b.attachment(ref))
        b.set_variable(stage+' '+name,b.output(summed,'Calculation Result'))
    b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=2)
    b.action('repeat.each',GroupingIdentifier=loop,WFControlFlowMode=2)
    results.extend([stage,': ',b.variable(stage+' Raw'),'초 / ',b.variable(stage+' Rounded'),'분\n'])
b.action('showresult',Text=b.text('2026-11-04 원본 초 / 구간별 반올림 분\n\n',*results,'\n서버 전송 없음. 반올림은 검사용입니다.'))
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Sleep Direct Nov4')
p=b.OUT/'GK21-Sleep-Direct-Nov4.unsigned.shortcut'; p.write_bytes(plistlib.dumps(wf)); print(p)
