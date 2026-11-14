#!/usr/bin/env python3
"""Append timing and error events; report observations without inferring success."""
import argparse
import json
from pathlib import Path
import sys
import time

TOOLS = ('lang', 'Bison', 'ANTLR', 'Ohm', 'tree-sitter')
STATES = ('active', 'waiting')
ACTIVITIES = ('setup', 'authoring', 'build', 'evaluation', 'installation')


def check(value, message):
    if not value:
        raise ValueError(message)


def external(path):
    path = Path(path).resolve()
    root = Path(__file__).resolve().parents[2]
    check(path != root and root not in path.parents, 'events belong outside the checkout')
    return path


def summarize(events):
    check(events and events[0]['type'] == 'session', 'missing session header')
    header = events[0]['data']
    check(header['version'] == 1, 'unsupported event version')
    check(header['kind'] in ('automated', 'human'), 'unknown session kind')
    check(header['tool'] in TOOLS and header['participant'], 'missing participant or tool')
    experience = header['prior_experience']
    check(set(experience) == {'tool_hours', 'language_author_hours', 'seen_task'}, 'incomplete prior experience')
    for name in ('tool_hours', 'language_author_hours'):
        value = experience[name]
        check(value is None or (type(value) in (int, float) and 0 <= value < float('inf')), 'invalid experience hours')
        check(header['kind'] != 'human' or value is not None, 'human experience must be recorded')
    check(type(experience['seen_task']) is bool, 'seen_task must be boolean')
    check(len(header['task_sha256']) == 64, 'missing frozen task identity')
    state, activity = 'active', 'setup'
    totals = dict(active_ns=0, waiting_ns=0, installation_active_ns=0, installation_waiting_ns=0)
    previous = events[0]['t_ns']
    finished = False
    docs, code, errors, installs, receipts = [], {}, [], [], []
    for index, event in enumerate(events):
        check(event['seq'] == index and type(event['t_ns']) is int and event['t_ns'] >= previous,
              'event sequence or monotonic clock regressed')
        check(not finished, 'event after finish')
        delta = event['t_ns'] - previous
        totals[state + '_ns'] += delta
        if activity == 'installation':
            totals['installation_' + state + '_ns'] += delta
        previous = event['t_ns']
        kind, data = event['type'], event['data']
        if kind == 'session':
            check(index == 0, 'duplicate session')
        elif kind == 'state':
            check(data['mode'] in STATES and data['activity'] in ACTIVITIES, 'invalid timing state')
            state, activity = data['mode'], data['activity']
        elif kind == 'doc':
            check(data['uri'] and len(data['sha256']) == 64, 'doc needs URI and content hash')
            docs.append(data)
        elif kind == 'code':
            check(data['path'] and len(data['sha256']) == 64 and data['baseline_sha256'], 'code needs source identities')
            for name in ('authored_lines', 'generated_lines', 'compiler_core_edits'):
                check(type(data[name]) is int and data[name] >= 0, 'invalid code accounting')
            # Latest submission snapshot per path; attempts/errors remain in the event log.
            code[data['path']] = data
        elif kind == 'error':
            check(data['category'] in ('syntax', 'semantics', 'build', 'runtime', 'oracle', 'installation')
                  and data['message'], 'invalid error category or empty diagnostic')
            errors.append(data)
        elif kind == 'installation':
            check(data['tool'] and data['status'] in ('preinstalled', 'attempted', 'installed', 'failed'),
                  'invalid installation event')
            installs.append(data)
        elif kind == 'receipt':
            check(data['path'] and len(data['sha256']) == 64, 'receipt needs path and hash')
            receipts.append(data)
        elif kind == 'finish':
            finished = True
        else:
            raise ValueError('unknown event type: ' + kind)
    check(finished, 'unfinished session; do not silently omit its time')
    return dict(version=1, kind=header['kind'], participant=header['participant'], tool=header['tool'],
                prior_experience=experience, timing_seconds={k[:-3] + '_seconds': v / 1e9 for k, v in totals.items()},
                elapsed_seconds=(previous - events[0]['t_ns']) / 1e9,
                docs_used=docs, code=list(code.values()), errors=errors, installations=installs, receipts=receipts,
                authored_lines=sum(c['authored_lines'] for c in code.values()),
                generated_lines=sum(c['generated_lines'] for c in code.values()),
                compiler_core_edits=sum(c['compiler_core_edits'] for c in code.values()),
                human_results='not measured' if header['kind'] == 'automated' else 'pending independent adjudication')


class Recorder:
    def __init__(self, path):
        self.path = external(path)
        self.events = [json.loads(line) for line in self.path.read_text().splitlines()] if self.path.exists() else []

    def emit(self, event_type, **data):
        event = dict(seq=len(self.events), t_ns=time.monotonic_ns(), utc_ns=time.time_ns(), type=event_type, data=data)
        candidate = self.events + [event]
        # Validate the full prefix before writing. A temporary finish closes its timing interval.
        end = dict(seq=len(candidate), t_ns=event['t_ns'], type='finish', data={})
        summarize(candidate if event_type == 'finish' else candidate + [end])
        with self.path.open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')
        self.events = candidate

    @classmethod
    def start(cls, path, kind, participant, tool, prior_experience, task_sha256):
        path = external(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x'):
            pass
        recorder = cls(path)
        recorder.emit('session', version=1, kind=kind, participant=participant, tool=tool,
                      prior_experience=prior_experience, task_sha256=task_sha256)
        return recorder

    def summary(self):
        return summarize(self.events)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    start = sub.add_parser('start')
    start.add_argument('path', type=Path)
    start.add_argument('--kind', choices=['automated', 'human'], required=True)
    start.add_argument('--participant', required=True)
    start.add_argument('--tool', choices=TOOLS, required=True)
    start.add_argument('--experience', type=json.loads, required=True)
    start.add_argument('--task-sha256', required=True)
    event = sub.add_parser('event')
    event.add_argument('path', type=Path)
    event.add_argument('type', choices=['state', 'doc', 'code', 'error', 'installation', 'receipt', 'finish'])
    event.add_argument('--data', type=json.loads, default={})
    report = sub.add_parser('report')
    report.add_argument('path', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'start':
            Recorder.start(args.path, args.kind, args.participant, args.tool, args.experience, args.task_sha256)
        elif args.command == 'event':
            Recorder(args.path).emit(args.type, **args.data)
        else:
            print(json.dumps(Recorder(args.path).summary(), indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
