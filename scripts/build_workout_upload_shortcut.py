"""Build a private one-workout transport from the device-validated preview.

The output contains an upload credential. Never commit, share, or print it.
This first transport intentionally reads one record, not a complete sync.
"""
import argparse
import copy
import importlib.util
from pathlib import Path
import plistlib

parser=argparse.ArgumentParser()
parser.add_argument('--token-file', type=Path, required=True)
args=parser.parse_args()
token=args.token_file.read_text().strip()
if len(token)<24: raise ValueError('Upload token not configured')
s=importlib.util.spec_from_file_location('preview',Path(__file__).with_name('build_workout_payload_preview.py'))
p=importlib.util.module_from_spec(s); s.loader.exec_module(p); b=p.b
wf=copy.deepcopy(p.wf); b.actions=[]
for a in wf['WFWorkflowActions']:
    params=a['WFWorkflowActionParameters']
    if a['WFWorkflowActionIdentifier'].endswith('.showresult') and '전송 형식 검사' in str(params):
        # The preceding parse action is a fail-closed check; send the exact text
        # that it successfully parsed, without Shortcuts' pretty-print display.
        payload=next(x for x in reversed(b.actions) if x['WFWorkflowActionIdentifier'].endswith('.gettext'))
        headers={'Value':{'WFDictionaryFieldValueItems':[
            {'WFItemType':0,'WFKey':b.text(k),'WFValue':b.text(v)}
            for k,v in [('Authorization','Bearer '+token),('Content-Type','application/json')]
        ]},'WFSerializationType':'WFDictionaryFieldValue'}
        response=b.output(b.action('downloadurl',WFURL='https://217.142.230.185/api/integrations/apple-health/export',
            WFHTTPMethod='POST',WFHTTPBodyType='File',
            WFRequestVariable=b.attachment(b.output(payload['WFWorkflowActionParameters']['UUID'],'Text')),
            WFHTTPHeaders=headers),'Contents of URL')
        b.action('showresult',Text=b.text('GK21 운동 저장 · 실제 서버 응답\n',response))
    else:
        b.actions.append(copy.deepcopy(a))
wf.update(WFWorkflowActions=b.actions,WFWorkflowName='GK21 Workout Save')
out=b.OUT/'GK21-Workout-Save.unsigned.shortcut'
out.write_bytes(plistlib.dumps(wf)); out.chmod(0o600)
print('Built private one-workout upload for GK21; no request executed.')
