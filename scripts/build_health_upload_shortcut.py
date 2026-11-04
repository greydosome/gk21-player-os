"""Build a separate, disabled-by-default transport draft. Never embeds a secret.

Input is an already validated API dictionary, not raw Health samples. This keeps
the tested sleep checker unchanged while transport is independently verified.
The draft must not be enabled for daily automation until collection windows and
overlapping samples have been verified.
"""
import copy
import importlib.util
import plistlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('sleep_builder', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
workflow = copy.deepcopy(b.workflow)
b.actions = []
b.action('comment', WFCommentActionText=(
    'GK21 업로드 초안 — 기본값은 전송 안 함\n'
    '입력: 검증된 날짜별 건강 요약 사전. 건강 기록을 직접 조회하지 않습니다.\n'
    '서버 적용 및 별도 검증 후에만 사용합니다. 업로드 키를 넣은 파일은 공유하지 마세요.'
))
enabled = b.action('number', WFNumberActionNumber='0')
gate = b.uid()
b.action('conditional', GroupingIdentifier=gate, WFControlFlowMode=0,
         WFInput={'Type': 'Variable', 'Variable': b.attachment(b.output(enabled, 'Number'))},
         WFCondition=4, WFNumberValue='1')
token = b.action('gettext', WFTextActionText='UPLOAD_TOKEN_NOT_CONFIGURED')


def dictionary(items):
    return {'Value': {'WFDictionaryFieldValueItems': [
        {'WFItemType': 0, 'WFKey': b.text(key), 'WFValue': value}
        for key, value in items
    ]}, 'WFSerializationType': 'WFDictionaryFieldValue'}


response = b.action('downloadurl',
    WFURL='https://example.invalid/api/integrations/apple-health/daily',
    WFHTTPMethod='POST', WFHTTPBodyType='File',
    WFRequestVariable=b.attachment({'Type': 'ExtensionInput'}),
    WFHTTPHeaders=dictionary([
        ('Authorization', b.text('Bearer ', b.output(token, 'Text'))),
        ('Content-Type', b.text('application/json')),
    ]))
# Show the actual server response; never display an unconditional success claim.
b.action('showresult', Text=b.text('GK21 서버 응답\n', b.output(response, 'Contents of URL')))
b.action('conditional', GroupingIdentifier=gate, WFControlFlowMode=1)
b.action('showresult', Text=b.text(
    '업로드 초안입니다. 전송하지 않았습니다.\n'
    '서버 적용·주소·업로드 키 및 입력 검증이 완료될 때까지 비활성 상태로 유지합니다.'))
b.action('conditional', GroupingIdentifier=gate, WFControlFlowMode=2)
workflow.update(WFWorkflowName='GK21 업로드 초안', WFWorkflowActions=b.actions,
                WFWorkflowHasShortcutInputVariables=True)
destination = b.OUT / 'GK21-Upload-Draft.unsigned.shortcut'
destination.write_bytes(plistlib.dumps(workflow))
print(destination)
print('Disabled draft; placeholder URL/token; no production upload')
