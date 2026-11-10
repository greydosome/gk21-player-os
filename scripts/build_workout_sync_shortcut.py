"""Private bounded workout sync, derived from the iPhone-validated transport.

Queries up to 100 workouts and uploads records ending in the past seven days.
No success dialogs; only invalid-data/server-failure notifications. The query's
ordering and locked-phone behavior must be validated before claiming full sync.
"""
import argparse
import copy
import importlib.util
from pathlib import Path
import plistlib

parser=argparse.ArgumentParser(); parser.add_argument('--token-file',type=Path,required=True)
args=parser.parse_args(); token=args.token_file.read_text().strip()
if len(token)<24: raise ValueError('Upload token not configured')
s=importlib.util.spec_from_file_location('preview',Path(__file__).with_name('build_workout_payload_preview.py'))
p=importlib.util.module_from_spec(s); s.loader.exec_module(p); b=p.b
wf=copy.deepcopy(p.wf)
query=next(a for a in wf['WFWorkflowActions'] if a['WFWorkflowActionIdentifier']=='com.sindresorhus.Actions.WorkoutAppEntity')
query['WFWorkflowActionParameters']['WFContentItemLimitNumber']=100
query_id=query['WFWorkflowActionParameters']['UUID']
def item(v):
    if isinstance(v,dict):
        if v.get('Type')=='ActionOutput' and v.get('OutputUUID')==query_id:
            ref={'Type':'Variable','VariableName':'Repeat Item'}
            if 'Aggrandizements' in v: ref['Aggrandizements']=copy.deepcopy(v['Aggrandizements'])
            return ref
        return {k:item(x) for k,x in v.items()}
    if isinstance(v,list): return [item(x) for x in v]
    return v
b.actions=[]
b.action('comment',WFCommentActionText='최근 조회 100건 중 종료 후 7일 이내 운동을 GK21에 저장. 수면/경로/심박 전송 없음. 인증 키 포함: 공유 금지. 자동 실행은 기기 권한과 자동화 설정이 필요합니다.')
b.actions.append(query)
loop=b.uid(); b.action('repeat.each',GroupingIdentifier=loop,WFControlFlowMode=0,WFInput=b.attachment(b.output(query_id,'Workouts')))
headers={'Value':{'WFDictionaryFieldValueItems':[
    {'WFItemType':0,'WFKey':b.text(k),'WFValue':b.text(v)} for k,v in
    [('Authorization','Bearer '+token),('Content-Type','application/json')]
]},'WFSerializationType':'WFDictionaryFieldValue'}
for a in wf['WFWorkflowActions'][wf['WFWorkflowActions'].index(query)+1:]:
    a=item(a); params=a['WFWorkflowActionParameters']
    if a['WFWorkflowActionIdentifier'].endswith('.showresult'):
        if '전송 형식 검사' in str(params):
            payload=next(x for x in reversed(b.actions) if x['WFWorkflowActionIdentifier'].endswith('.gettext'))
            now=b.output(b.action('date',WFDateActionMode='Current Date'),'Date')
            age=b.output(b.action('gettimebetweendates',WFTimeUntilFromDate=b.text(item(p.d.prop('endDate'))),WFInput=b.text(now),WFTimeUntilUnit='Minutes'),'Time Between Dates')
            age=b.output(b.action('math',WFInput=b.attachment(age),WFMathOperation='÷',WFMathOperand=1),'Calculation Result')
            old=b.uid(); b.action('conditional',GroupingIdentifier=old,WFControlFlowMode=0,
                WFInput={'Type':'Variable','Variable':b.attachment(age)},WFCondition=2,WFNumberValue='10080')
            b.action('nothing')
            b.action('conditional',GroupingIdentifier=old,WFControlFlowMode=1)
            response=b.output(b.action('downloadurl',WFURL='https://217.142.230.185/api/integrations/apple-health/export',WFHTTPMethod='POST',WFHTTPBodyType='File',WFRequestVariable=b.attachment(b.output(payload['WFWorkflowActionParameters']['UUID'],'Text')),WFHTTPHeaders=headers),'Contents of URL')
            success=b.output(b.action('getvalueforkey',WFInput=b.attachment(response),WFDictionaryKey='success',WFGetDictionaryValueType='Value'),'Dictionary Value')
            success['Aggrandizements']=[{'Type':'WFCoercionVariableAggrandizement','CoercionItemClass':'WFNumberContentItem'}]
            ok=b.uid(); b.action('conditional',GroupingIdentifier=ok,WFControlFlowMode=0,WFInput={'Type':'Variable','Variable':b.attachment(success)},WFCondition=4,WFNumberValue='1')
            b.action('nothing')
            b.action('conditional',GroupingIdentifier=ok,WFControlFlowMode=1)
            b.action('notification',WFNotificationActionBody=b.text('GK21 운동 저장 응답을 확인해야 합니다.\n',response))
            b.action('conditional',GroupingIdentifier=ok,WFControlFlowMode=2)
            b.action('conditional',GroupingIdentifier=old,WFControlFlowMode=2)
        else:
            b.action('notification',WFNotificationActionBody=params['Text'])
    else: b.actions.append(a)
b.action('repeat.each',GroupingIdentifier=loop,WFControlFlowMode=2)
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Workout Auto')
out=b.OUT/'GK21-Workout-Auto.unsigned.shortcut'; out.write_bytes(plistlib.dumps(wf)); out.chmod(0o600)
print('Built private bounded workout sync. No request executed; device batch/automation not yet verified.')
