"""Read one real workout and preview a minimal export; never uploads.

Workout property keys/date formatting were verified on the user's iPhone.
Number extraction and final JSON still require native runtime/device validation.
"""
import copy
import importlib.util
from pathlib import Path
import plistlib
s=importlib.util.spec_from_file_location('details',Path(__file__).with_name('build_workout_details_check.py'))
d=importlib.util.module_from_spec(s); s.loader.exec_module(d); b=d.b
wf=copy.deepcopy(d.wf)
actions=wf['WFWorkflowActions']; b.actions=[]
for a in actions:
    p=a['WFWorkflowActionParameters']
    if a['WFWorkflowActionIdentifier'].endswith('.showresult') and 'duration 원본' in str(p):
        unit=b.output(b.action('text.match',text=b.text(d.prop('duration')),WFMatchTextPattern=r'(?i)\d\s*(?:초|seconds?|secs?|s)\s*$'),'Matches')
        unit_count=b.output(b.action('count',Input=b.attachment(unit),WFCountType='Items'),'Count')
        seconds_only=d.begin(unit_count,2,0)
        numeric=b.output(b.action('detect.number',WFInput=b.text(d.prop('duration'))),'Numbers')
        count=b.output(b.action('count',Input=b.attachment(numeric),WFCountType='Items'),'Count')
        valid=d.begin(count,4,1)
        # Enum workout names cannot be user-edited, but still JSON-escape them.
        name=b.output(b.action('gettext',WFTextActionText=b.text(d.base)),'Text')
        for old,new in [('\\','\\\\'),('"','\\"'),('\n','\\n'),('\r','\\r'),('\t','\\t')]:
            name=b.output(b.action('text.replace',WFInput=b.text(name),WFReplaceTextFind=old,
                WFReplaceTextReplace=new,WFReplaceTextRegularExpression=False),'Updated Text')
        payload=b.output(b.action('gettext',WFTextActionText=b.text(
            '{"workouts":[{"id":"actions:',d.formatted[0],'|',d.formatted[1],
            '","name":"',name,'","start":"',d.formatted[0],'","end":"',d.formatted[1],
            '","duration":',numeric,'}]}')),'Text')
        parsed=b.output(b.action('detect.dictionary',WFInput=b.attachment(payload)),'Dictionary')
        b.action('showresult',Text=b.text('운동 전송 형식 검사 · 서버 전송 없음\n',parsed))
        d.otherwise_end(valid,'운동 시간을 숫자 한 개로 읽지 못했습니다. 전송하지 않았습니다.')
        d.otherwise_end(seconds_only,'운동 시간 단위가 초가 아니어서 저장하지 않았습니다. 단위 변환 확인이 필요합니다.')
    else:
        b.actions.append(copy.deepcopy(a))
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Workout Payload Preview')
p=b.OUT/'GK21-Workout-Payload-Preview.unsigned.shortcut'; p.write_bytes(plistlib.dumps(wf)); print(p)
