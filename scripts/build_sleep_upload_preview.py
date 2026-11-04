"""Connect the iPhone-tested collector to an API payload preview; no network.

Single-run review artifact for an iPhone using Asia/Seoul. Not daily automation:
the current collector still uses a rolling 24-hour window and does not union
overlapping sources. Preview must be reviewed before any production upload.
"""
import copy
import importlib.util
import plistlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('collector', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
wf = copy.deepcopy(b.workflow)
original = copy.deepcopy(b.actions)
b.actions = []
for action in original:
    if action['WFWorkflowActionIdentifier'].endswith('.showresult') and not b.actions[-1]['WFWorkflowActionIdentifier'].endswith('.conditional'):
        now = b.action('date', WFDateActionMode='Current Date')
        day = b.action('format.date', WFDate=b.text(b.output(now, 'Date')),
                       WFDateFormatStyle='Custom', WFDateFormat='yyyy-MM-dd', WFLocale='en_US_POSIX')
        collected = b.action('format.date', WFDate=b.text(b.output(now, 'Date')),
                            WFDateFormatStyle='ISO 8601', WFISO8601IncludeTime=True)
        payload = b.action('gettext', WFTextActionText=b.text(
            '{"schema_version":1,"timezone":"Asia/Seoul","record_date":"',
            b.output(day, 'Formatted Date'), '","collected_at":"',
            b.output(collected, 'Formatted Date'), '","summary":{"sleep_hours":',
            b.output(b.hours, 'Calculation Result'), '}}'))
        # Parse locally before displaying; invalid JSON must fail before transport.
        parsed = b.action('detect.dictionary', WFInput=b.attachment(b.output(payload, 'Text')))
        b.action('showresult', Text=b.text(
            'GK21 전송 내용 미리보기 — 서버 전송 없음\n'
            '한국 시간대 기기에서 오늘 수면을 확인하는 초안입니다.\n',
            b.output(parsed, 'Dictionary')))
    else:
        b.actions.append(action)
wf.update(WFWorkflowName='GK21 수면 전송 미리보기', WFWorkflowActions=b.actions)
(b.OUT / 'GK21-Sleep-Upload-Preview.unsigned.shortcut').write_bytes(plistlib.dumps(wf))
print('Built collection → dated JSON → local parse → preview; no network')
