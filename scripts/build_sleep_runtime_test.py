"""Build a native Shortcuts test: replace only unavailable Health I/O with fixtures.

Date arithmetic, repeat loops, mutable variables, division, and branches remain
the production actions. The final display is replaced with Text for CLI capture.
"""
import copy
import datetime as dt
import importlib.util
import plistlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('builder', Path(__file__).with_name('build_sleep_check_shortcut.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
start = dt.datetime(2026, 11, 2, 20, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
# Split durations exercise multiple loop iterations and sub-minute precision.
cases = {
    'normal': {'Core': [38 * 60 + 24, 242 * 60], 'REM': [22 * 60, 32 * 60 + 12], 'Deep': [49 * 60 + 9]},
    'empty': {'Core': [], 'REM': [], 'Deep': []},
}
for label, stages in cases.items():
    wf = copy.deepcopy(b.workflow)
    wf['WFWorkflowName'] = 'GK21 Runtime Test ' + label
    for a in wf['WFWorkflowActions']:
        name = a['WFWorkflowActionIdentifier']
        p = a['WFWorkflowActionParameters']
        identifier = p['UUID']
        if name.endswith('filter.health.quantity'):
            stage = p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates'][-1]['Values']['String']
            a['WFWorkflowActionIdentifier'] = 'is.workflow.actions.list'
            a['WFWorkflowActionParameters'] = {'UUID': identifier, 'WFItems': [
                (start + dt.timedelta(seconds=s)).isoformat() for s in stages[stage]]}
        elif name.endswith('properties.health.quantity'):
            value = start.isoformat() if p['WFContentItemPropertyName'] == 'Start Date' else b.text(b.variable('Repeat Item'))
            a['WFWorkflowActionIdentifier'] = 'is.workflow.actions.date'
            a['WFWorkflowActionParameters'] = {'UUID': identifier, 'WFDateActionMode': 'Specified Date', 'WFDateActionDate': value}
        elif name.endswith('showresult'):
            a['WFWorkflowActionIdentifier'] = 'is.workflow.actions.gettext'
            a['WFWorkflowActionParameters'] = {'UUID': identifier, 'WFTextActionText': p['Text']}
    path = b.OUT / ('GK21-Runtime-Test-' + label + '.unsigned.shortcut')
    path.write_bytes(plistlib.dumps(wf))
    print(path)
