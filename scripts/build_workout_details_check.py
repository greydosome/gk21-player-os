"""Read-only, one-workout property probe. Property support must be device-verified."""
import copy
import importlib.util
from pathlib import Path
import plistlib
s=importlib.util.spec_from_file_location('check',Path(__file__).with_name('build_free_workout_check.py'))
c=importlib.util.module_from_spec(s); s.loader.exec_module(c); b=c.b
wf=copy.deepcopy(c.wf)
query=copy.deepcopy(next(a for a in wf['WFWorkflowActions'] if a['WFWorkflowActionIdentifier']=='com.sindresorhus.Actions.WorkoutAppEntity'))
b.actions=[]
b.action('comment',WFCommentActionText='운동 1건의 속성 확인. 읽기 전용이며 전송하지 않습니다. duration/endDate 키는 실제 출력으로 지원 여부와 단위를 확인해야 합니다. 경과시간을 실제 운동시간 대신 저장하지 않습니다.')
b.actions.append(query)
base=b.output(query['WFWorkflowActionParameters']['UUID'],'Workouts')
def prop(name):
    ref=copy.deepcopy(base)
    ref['Aggrandizements']=[{'Type':'WFPropertyVariableAggrandizement','PropertyName':name,
        'PropertyUserInfo':{'WFLinkEntityContentPropertyUserInfoPropertyIdentifier':name}}]
    return ref
def begin(ref, condition, number=None):
    group=b.uid()
    p={'GroupingIdentifier':group,'WFControlFlowMode':0,
       'WFInput':{'Type':'Variable','Variable':b.attachment(ref)},'WFCondition':condition}
    if number is not None:
        p['WFNumberValue']=str(number)
    b.action('conditional',**p)
    return group
def otherwise_end(group,message):
    b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=1)
    b.action('showresult',Text=b.text(message))
    b.action('conditional',GroupingIdentifier=group,WFControlFlowMode=2)
count=b.output(b.action('count',Input=b.attachment(base),WFCountType='Items'),'Count')
has_record=begin(count,2,0)
# A missing date must never fall back to Format Date's current-date default.
guards=[(name,begin(prop(name),100)) for name in ('startDate','endDate','duration')]
formatted=[]
for name in ('startDate','endDate'):
    formatted.append(b.output(b.action('format.date',WFDate=b.text(prop(name)),WFDateFormatStyle='Custom',
        WFDateFormat="yyyy-MM-dd'T'HH:mm:ssXXX",WFLocale='en_US_POSIX'),'Formatted Date'))
b.action('showresult',Text=b.text('운동 속성 확인 · 1건\n종류: ',base,'\n시작: ',formatted[0],
    '\n종료: ',formatted[1],'\nduration 원본: ',prop('duration'),'\n\n서버 전송 없음.'))
for name,group in reversed(guards):
    otherwise_end(group,name+' 값을 읽지 못했습니다. 날짜나 시간을 추정하지 않고 중단했습니다. 서버 전송 없음.')
otherwise_end(has_record,'운동 기록을 읽지 못했습니다. 날짜나 시간을 추정하지 않습니다. 서버 전송 없음.')
wf['WFWorkflowActions']=b.actions
p=b.OUT/'GK21-Workout-Details-Check.unsigned.shortcut'; p.write_bytes(plistlib.dumps(wf)); print(p)
