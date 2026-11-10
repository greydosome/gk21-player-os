"""Private sleep transport using the previously device-tested union collector.

The server rounds collected hours into the existing diary's integer-hour field.
No paid app, invented adjustment, or zero overwrite when sleep is unavailable.
"""
import argparse
import copy
import importlib.util
from pathlib import Path
import plistlib

parser = argparse.ArgumentParser()
parser.add_argument('--token-file', type=Path, required=True)
args = parser.parse_args()
token = args.token_file.read_text().strip()
if len(token) < 24:
    raise ValueError('Upload token not configured')
spec = importlib.util.spec_from_file_location('collector', Path(__file__).with_name('build_sleep_union_shortcut.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
b = u.b
wf = copy.deepcopy(u.wf)
b.actions = []
headers = {'Value': {'WFDictionaryFieldValueItems': [
    {'WFItemType': 0, 'WFKey': b.text(k), 'WFValue': b.text(v)}
    for k, v in [('Authorization', 'Bearer ' + token), ('Content-Type', 'application/json')]
]}, 'WFSerializationType': 'WFDictionaryFieldValue'}
for action in wf['WFWorkflowActions']:
    name, params = action['WFWorkflowActionIdentifier'], action['WFWorkflowActionParameters']
    if name.endswith('.comment'):
        b.action('comment', WFCommentActionText=(
            '기상 날짜의 수면 시간을 GK21 기존 수면 칸에 저장합니다. '
            '겹친 수면 구간은 한 번만 합산하며 서버에서 정수 시간으로 반올림합니다. '
            '수면이 없으면 0으로 덮어쓰지 않습니다. 인증 키 포함: 공유 금지.'))
    elif name.endswith('.showresult'):
        if '오늘 기상한 수면' not in str(params):
            b.action('nothing')
            continue
        available = u.begin_if(u.var('Day Seconds'), 2, 0)
        hours = u.math(u.var('Day Seconds'), '÷', 3600)
        collected = u.out(b.action('format.date', WFDate=b.text(u.now),
                                 WFDateFormatStyle='ISO 8601', WFISO8601IncludeTime=True), 'Formatted Date')
        payload = b.action('gettext', WFTextActionText=b.text(
            '{"schema_version":1,"timezone":"Asia/Seoul","record_date":"', u.today,
            '","collected_at":"', collected, '","summary":{"sleep_hours":', hours, '}}'))
        b.action('detect.dictionary', WFInput=b.attachment(u.out(payload, 'Text')))
        response = u.out(b.action('downloadurl',
            WFURL='https://217.142.230.185/api/integrations/apple-health/daily',
            WFHTTPMethod='POST', WFHTTPBodyType='File', WFRequestVariable=b.attachment(u.out(payload, 'Text')),
            WFHTTPHeaders=headers), 'Contents of URL')
        success = u.out(b.action('getvalueforkey', WFInput=b.attachment(response),
                                WFDictionaryKey='success', WFGetDictionaryValueType='Value'), 'Dictionary Value')
        success['Aggrandizements'] = [{'Type': 'WFCoercionVariableAggrandizement', 'CoercionItemClass': 'WFNumberContentItem'}]
        ok = u.begin_if(success, 4, 1)
        b.action('nothing')
        b.action('conditional', GroupingIdentifier=ok, WFControlFlowMode=1)
        b.action('notification', WFNotificationActionBody=b.text('GK21 수면 저장 응답을 확인해주세요.\n', response))
        u.end_if(ok)
        u.end_if(available)
    else:
        b.actions.append(copy.deepcopy(action))
wf.update(WFWorkflowName='GK21 Sleep Auto', WFWorkflowActions=b.actions)
destination = b.OUT / 'GK21-Sleep-Auto.unsigned.shortcut'
destination.write_bytes(plistlib.dumps(wf))
destination.chmod(0o600)
print('Built private sleep upload; no request executed.')
