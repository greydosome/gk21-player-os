"""Build an iPhone-only, read-only sleep-check shortcut (sign with Apple's CLI).

Only reads Health and displays a result. No network, writes, tokens, or uploads.
The three independent queries mirror the stage-by-stage checks performed on iPhone.
"""
from pathlib import Path
import plistlib
import uuid

OUT = Path(__file__).resolve().parents[1] / 'artifacts' / 'shortcuts'
actions = []


def uid():
    return str(uuid.uuid4()).upper()


def action(name, **params):
    identifier = params.setdefault('UUID', uid())
    actions.append({'WFWorkflowActionIdentifier': 'is.workflow.actions.' + name,
                    'WFWorkflowActionParameters': params})
    return identifier


def output(identifier, name):
    return {'Type': 'ActionOutput', 'OutputUUID': identifier, 'OutputName': name}


def variable(name):
    return {'Type': 'Variable', 'VariableName': name}


def attachment(value):
    return {'Value': value, 'WFSerializationType': 'WFTextTokenAttachment'}


def text(*parts):
    string = ''
    ranges = {}
    for part in parts:
        if isinstance(part, dict):
            # Shortcuts ranges use UTF-16 code units, not Python code points.
            ranges['{%d, 1}' % (len(string.encode('utf-16-le')) // 2)] = part
            string += '\ufffc'
        else:
            string += part
    return {'Value': {'string': string, 'attachmentsByRange': ranges},
            'WFSerializationType': 'WFTextTokenString'}


def set_variable(name, value):
    action('setvariable', WFVariableName=name, WFInput=attachment(value))


action('comment', WFCommentActionText=(
    'GK21 수면 확인 · 아이폰에서 실행\n'
    '최근 24시간 안에 시작한 Core / REM / Deep 기록을 각각 조회합니다. '
    '구간마다 초로 계산한 뒤 합산합니다.\n'
    '건강 읽기 및 결과 표시만 수행하며 업로드하지 않습니다. '
    '서로 다른 출처의 겹친 기록을 병합하거나 건강 앱의 우선순위를 재현하지는 않습니다.'
))
stage_outputs = []
for stage in ('Core', 'REM', 'Deep'):
    zero = action('number', WFNumberActionNumber='0')
    set_variable('Stage Seconds', output(zero, 'Number'))
    # No upstream content may be passed into a Find action as its filter input.
    action('nothing')
    predicates = [
        {'Property': 'Type', 'Operator': 4, 'Bounded': True, 'Removable': False,
         'Values': {'Enumeration': {'Value': 'Sleep',
                                   'WFSerializationType': 'WFStringSubstitutableState'}}},
        {'Property': 'Start Date', 'Operator': 1001, 'Bounded': True,
         # NSCalendarUnit.day = 16, confirmed against the user's iPhone export.
         'Removable': False, 'Values': {'Number': '1', 'Unit': 16}},
        {'Property': 'Value', 'Operator': 4, 'Removable': True,
         'Values': {'String': stage}},
    ]
    found = action('filter.health.quantity', WFContentItemFilter={
        'Value': {'WFActionParameterFilterPrefix': 1,
                  'WFContentPredicateBoundedDate': False,
                  'WFActionParameterFilterTemplates': predicates},
        'WFSerializationType': 'WFContentPredicateTableTemplate'},
        WFContentItemLimitEnabled=False, WFContentItemInputParameter='')
    loop_group = uid()
    action('repeat.each', GroupingIdentifier=loop_group, WFControlFlowMode=0,
           WFInput=attachment(output(found, 'Health Samples')))
    start = action('properties.health.quantity', WFContentItemPropertyName='Start Date',
                   WFInput=attachment(variable('Repeat Item')))
    end = action('properties.health.quantity', WFContentItemPropertyName='End Date',
                 WFInput=attachment(variable('Repeat Item')))
    seconds = action('gettimebetweendates',
                     WFTimeUntilFromDate=text(output(start, 'Start Date')),
                     WFInput=text(output(end, 'End Date')), WFTimeUntilUnit='Seconds')
    summed = action('math', WFInput=attachment(variable('Stage Seconds')),
                    WFMathOperation='+', WFMathOperand=attachment(output(seconds, 'Time Between Dates')))
    set_variable('Stage Seconds', output(summed, 'Calculation Result'))
    action('repeat.each', GroupingIdentifier=loop_group, WFControlFlowMode=2)
    set_variable(stage + ' Seconds', variable('Stage Seconds'))
    minutes = action('math', WFInput=attachment(variable(stage + ' Seconds')),
                     WFMathOperation='÷', WFMathOperand=60)
    stage_outputs.append(output(minutes, 'Calculation Result'))

added = action('math', WFInput=attachment(variable('Core Seconds')),
               WFMathOperation='+', WFMathOperand=attachment(variable('REM Seconds')))
total = action('math', WFInput=attachment(output(added, 'Calculation Result')),
               WFMathOperation='+', WFMathOperand=attachment(variable('Deep Seconds')))
condition_group = uid()
action('conditional', GroupingIdentifier=condition_group, WFControlFlowMode=0,
       WFInput={'Type': 'Variable', 'Variable': attachment(output(total, 'Calculation Result'))},
       WFCondition=2, WFNumberValue='0')
minutes = action('math', WFInput=attachment(output(total, 'Calculation Result')),
                 WFMathOperation='÷', WFMathOperand=60)
hours = action('math', WFInput=attachment(output(total, 'Calculation Result')),
               WFMathOperation='÷', WFMathOperand=3600)
action('showresult', Text=text(
    'GK21 수면 확인\n최근 24시간 안에 시작한 기록\n\n',
    '코어: ', stage_outputs[0], '분\n',
    'REM: ', stage_outputs[1], '분\n',
    '깊은 수면: ', stage_outputs[2], '분\n\n',
    '합계: ', output(minutes, 'Calculation Result'), '분\n',
    '앱 전송용 시간 값: ', output(hours, 'Calculation Result'), '시간\n\n',
    '확인용 결과입니다. 서버에 전송하지 않았습니다.'))
action('conditional', GroupingIdentifier=condition_group, WFControlFlowMode=1)
action('showresult', Text=text(
    '최근 24시간 안에 시작한 코어·REM·깊은 수면 기록을 찾지 못했습니다.\n'
    '수면 0시간으로 저장하거나 전송하지 않습니다. '
    '건강 앱의 기록 및 단축어 읽기 권한을 확인해 주세요.'))
action('conditional', GroupingIdentifier=condition_group, WFControlFlowMode=2)

workflow = {
    'WFWorkflowName': 'GK21 수면 확인',
    'WFWorkflowClientVersion': '4040.0.4',
    'WFWorkflowClientRelease': '26.0',
    'WFWorkflowMinimumClientVersion': 900,
    'WFWorkflowMinimumClientVersionString': '900',
    'WFWorkflowIcon': {'WFWorkflowIconStartColor': 2071128575,
                       'WFWorkflowIconGlyphNumber': 59511},
    'WFWorkflowTypes': [], 'WFWorkflowInputContentItemClasses': [],
    'WFWorkflowActions': actions, 'WFWorkflowImportQuestions': [],
    'WFQuickActionSurfaces': [], 'WFWorkflowHasShortcutInputVariables': False,
}
OUT.mkdir(parents=True, exist_ok=True)
destination = OUT / 'GK21-Sleep-Check.unsigned.shortcut'
destination.write_bytes(plistlib.dumps(workflow, fmt=plistlib.FMT_XML))
print(destination)
print(f'{len(actions)} actions; no network or Health writes')
