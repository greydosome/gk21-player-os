"""Native batch fixture: no Health reads, HTTP, credentials, or DB writes."""
import copy
import importlib.util
import json
from datetime import datetime, timedelta
from pathlib import Path
import plistlib
from zoneinfo import ZoneInfo
s=importlib.util.spec_from_file_location('sync',Path(__file__).with_name('build_workout_sync_shortcut.py'))
sync=importlib.util.module_from_spec(s); s.loader.exec_module(sync); b=sync.b
wf=copy.deepcopy(sync.wf); b.actions=[]
now=datetime.now(ZoneInfo('Asia/Seoul')).replace(microsecond=0)
rows=[]
for label,days,duration in [('Recent A',0,873.84),('Old B',8,200),('Paused C',1,100),('Hour D',0,3600)]:
    end=now-timedelta(days=days,minutes=5)
    rows.append(dict(name=label,startDate=(end-timedelta(seconds=1000)).isoformat(),endDate=end.isoformat(),duration='1 h' if label=='Hour D' else f'{duration}초'))
zero=b.output(b.action('number',WFNumberActionNumber='0'),'Number'); b.set_variable('Fixture Uploads',zero)
refs={}
def rewrite(v):
    if isinstance(v,dict):
        if v.get('Type')=='Variable' and v.get('VariableName')=='Repeat Item':
            key=next((a.get('PropertyName') for a in v.get('Aggrandizements',[]) if a.get('Type')=='WFPropertyVariableAggrandizement'),'name')
            return copy.deepcopy(refs[key])
        return {k:rewrite(x) for k,x in v.items()}
    if isinstance(v,list): return [rewrite(x) for x in v]
    return v
for original in wf['WFWorkflowActions']:
    name=original['WFWorkflowActionIdentifier']; params=original['WFWorkflowActionParameters']; ident=params['UUID']
    if name=='com.sindresorhus.Actions.WorkoutAppEntity':
        b.actions.append({'WFWorkflowActionIdentifier':'is.workflow.actions.list','WFWorkflowActionParameters':{'UUID':ident,'WFItems':[json.dumps(r) for r in rows]}})
    elif name.endswith('repeat.each') and params['WFControlFlowMode']==0:
        b.actions.append(copy.deepcopy(original))
        parsed=b.output(b.action('detect.dictionary',WFInput=b.attachment(b.variable('Repeat Item'))),'Dictionary')
        for key in ('name','startDate','endDate','duration'):
            refs[key]=b.output(b.action('getvalueforkey',WFInput=b.attachment(parsed),WFGetDictionaryValueType='Value',WFDictionaryKey=key),'Dictionary Value')
    elif name.endswith('downloadurl'):
        params=rewrite(params)
        b.action('appendvariable',WFVariableName='Fixture Uploads',WFInput=params['WFRequestVariable'])
        fake=b.output(b.action('gettext',WFTextActionText='{"success":true}'),'Text')
        b.actions.append({'WFWorkflowActionIdentifier':'is.workflow.actions.detect.dictionary','WFWorkflowActionParameters':{'UUID':ident,'WFInput':b.attachment(fake)}})
    elif name.endswith('notification'):
        message=b.output(b.action('gettext',WFTextActionText=rewrite(params['WFNotificationActionBody'])),'Text')
        b.action('appendvariable',WFVariableName='Fixture Uploads',WFInput=b.attachment(message))
    else:
        b.actions.append(rewrite(copy.deepcopy(original)))
b.action('gettext',WFTextActionText=b.text(b.variable('Fixture Uploads')))
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Workout Sync Test')
out=b.OUT/'GK21-Workout-Sync-Test.unsigned.shortcut'; out.write_bytes(plistlib.dumps(wf))
assert not any(a['WFWorkflowActionIdentifier'].endswith('downloadurl') for a in b.actions)
assert 'Bearer ' not in str(wf)
print('Built batch fixture: expect Recent A and Paused C only, preserving active seconds.')
