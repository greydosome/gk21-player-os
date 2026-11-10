"""Build a one-record, read-only Actions workout check from an exported action."""
import copy
import importlib.util
from pathlib import Path
import plistlib

spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build_sleep_check_shortcut.py'))
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
# This descriptor was exported from the actual Actions Find Workout on the user's iPhone.
wf=copy.deepcopy(b.workflow)
b.actions=[]
b.action('comment',WFCommentActionText='무료 Actions 운동 조회 검사. 한 건만 읽어 화면에 표시하며 서버 전송·건강 기록 쓰기 동작은 없습니다. 최신 기록이라고 보장하지 않습니다.')
identifier=b.uid()
b.actions.append({'WFWorkflowActionIdentifier':'com.sindresorhus.Actions.WorkoutAppEntity','WFWorkflowActionParameters':{
    'UUID':identifier,
    'AppIntentDescriptor':{'TeamIdentifier':'YG56YK5RN5','BundleIdentifier':'com.sindresorhus.Actions',
        'Name':'Actions','AppIntentIdentifier':'WorkoutAppEntity','ActionRequiresAppInstallation':True},
    'WFContentItemLimitEnabled':True,'WFContentItemLimitNumber':1}})
found=b.output(identifier,'Workouts')
count=b.action('count',Input=b.attachment(found),WFCountType='Items')
group=b.uid()
b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=0,WFInput={'Type':'Variable','Variable':b.attachment(b.output(count,'Count'))},WFCondition=2,WFNumberValue='0')
b.action('showresult',Text=b.text('무료 운동 조회 · 1건\n',found,'\n\n읽기 전용. 서버에 전송하지 않았습니다.'))
b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=1)
b.action('showresult',Text=b.text('운동 기록을 읽지 못했습니다. 기록 없음 또는 읽기 권한을 확인해야 합니다. 저장하지 않았습니다.'))
b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=2)
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Free Workout Check')
p=b.OUT/'GK21-Free-Workout-Check.unsigned.shortcut'; p.write_bytes(plistlib.dumps(wf)); print(p)
