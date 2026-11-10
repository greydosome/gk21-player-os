"""Native Shortcuts fixture: replace only Actions I/O; retain serialization flow."""
import copy
import importlib.util
from pathlib import Path
import plistlib
s=importlib.util.spec_from_file_location('preview',Path(__file__).with_name('build_workout_payload_preview.py'))
p=importlib.util.module_from_spec(s); s.loader.exec_module(p); b=p.b
wf=copy.deepcopy(p.wf)
query=next(a for a in wf['WFWorkflowActions'] if a['WFWorkflowActionIdentifier']=='com.sindresorhus.Actions.WorkoutAppEntity')
query_id=query['WFWorkflowActionParameters']['UUID']; b.actions=[]
refs={}
for key,value in {'':'Strength "test" \\ sample','startDate':'2000-01-01T23:59:00+09:00',
                  'endDate':'2000-01-02T00:13:34+09:00','duration':'873.84초'}.items():
    refs[key]=b.output(b.action('gettext',WFTextActionText=value),'Text')
def replace(v):
    if isinstance(v,dict):
        if v.get('Type')=='ActionOutput' and v.get('OutputUUID')==query_id:
            key=next((a.get('PropertyName') for a in v.get('Aggrandizements',[]) if a.get('Type')=='WFPropertyVariableAggrandizement'),'')
            return copy.deepcopy(refs[key])
        return {k:replace(x) for k,x in v.items()}
    if isinstance(v,list): return [replace(x) for x in v]
    return v
for a in wf['WFWorkflowActions']:
    if a is query: continue
    a=replace(a)
    if a['WFWorkflowActionIdentifier'].endswith('.showresult'):
        a['WFWorkflowActionIdentifier']='is.workflow.actions.gettext'
        a['WFWorkflowActionParameters']['WFTextActionText']=a['WFWorkflowActionParameters'].pop('Text')
    b.actions.append(a)
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Workout Payload Test')
p=b.OUT/'GK21-Workout-Payload-Test.unsigned.shortcut'; p.write_bytes(plistlib.dumps(wf)); print(p)
