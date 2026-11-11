"""Run isolated comparison cases and build the local HTML report."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import queue
import signal
import statistics
import subprocess
import sys
import threading
import time
import uuid

import numpy as np
from PIL import Image
import psutil

from image_preparation import clean_png_bytes, sha256, validate_clean_png, write_new_or_identical
from static_renderers import StaticRenderer, blurred_backdrop, glass_maps, rectangle
from comparison_report import write_report

ENGINE = Path(__file__).resolve().parents[1]
SHELF = ENGINE / 'tool-package-shelf'
RESULTS = ENGINE / 'results/build-n-compare-0.0.1'
DOCS = ENGINE / 'plan-docs/build-n-compare-0.0.1'
MEMORY_LIMIT = 36 * 2**30
SAMPLE_SECONDS = .1
LOW_MEMORY_SECONDS = 2


def emit(event, **values):
    print(json.dumps({'event': event, **values}), flush=True)


def checked_frame(scene, photo):
    if scene.size != (1920, 1080):
        raise ValueError('Scene dimensions must be 1920x1080')
    x, y, w, h = rectangle(photo)
    frame = scene.convert('RGB')
    frame.paste(photo, (x, y))
    if frame.crop((x, y, x+w, y+h)).tobytes() != photo.tobytes():
        raise ValueError('Protected foreground differs')
    return frame


def pixel_difference(first, second, photo):
    a, b = np.asarray(first).astype(np.int16), np.asarray(second).astype(np.int16)
    x, y, w, h = rectangle(photo)
    mask = np.ones(a.shape[:2], dtype=bool)
    mask[y:y+h, x:x+w] = False
    difference = np.abs(a-b)[mask]
    return {'changed_pixels': int(np.count_nonzero(np.any(difference, axis=1))),
            'maximum_channel_difference': int(difference.max()),
            'mean_absolute_channel_difference': float(difference.mean())}


def worker(spec_path):
    start = time.perf_counter()
    spec = json.loads(spec_path.read_text())
    folder = Path(spec['work'])
    photo = Image.open(spec['prepared']).convert('RGB')
    renderer = None
    try:
        if spec['tool'].startswith('D'):
            from browser_renderer import BrowserRenderer
            renderer = BrowserRenderer(spec, photo)
        else:
            renderer = StaticRenderer(spec, photo)
        emit('ready', initialization_seconds=time.perf_counter()-start)
        frames, timings, hashes = [], [], []
        for index in range(4):
            emit('render_started', stage='warmup' if index == 0 else f'measured-{index}')
            begin = time.perf_counter()
            scene = renderer.render()
            rendered = time.perf_counter()
            frame = checked_frame(scene, photo)
            encoded = clean_png_bytes(frame)
            destination = folder / f'render-{index}.png'
            write_new_or_identical(destination, encoded)
            exported = time.perf_counter()
            if index:
                frames.append(frame)
                timings.append({'render_seconds': rendered-begin, 'export_seconds': exported-rendered,
                                'total_seconds': exported-begin})
                hashes.append(sha256(frame.tobytes()))
        baseline = frames[0]
        repeat = [pixel_difference(baseline, other, photo) for other in frames[1:]]
        activity = {}
        if spec['method'] == 'glass':
            for kind in ('off', 'refraction-off'):
                emit('render_started', stage=kind)
                diagnostic = checked_frame(renderer.render(kind), photo)
                write_new_or_identical(Path(spec['diagnostics']) / f"{spec['case_id']}__{kind}.png", clean_png_bytes(diagnostic))
                activity[kind] = pixel_difference(baseline, diagnostic, photo)
        emit('render_started', stage='final verification and thumbnail')
        final_path = Path(spec['output'])
        write_new_or_identical(final_path, (folder / 'render-1.png').read_bytes())
        thumbnail = baseline.resize((480, 270), Image.Resampling.LANCZOS)
        write_new_or_identical(Path(spec['thumbnail']), clean_png_bytes(thumbnail))
        repeatable = len(set(hashes)) == 1
        active = not activity or all(value['changed_pixels'] > 0 for value in activity.values())
        result = {key: spec[key] for key in ('case_id', 'input_id', 'method', 'tool', 'preset')}
        result.update(status='passed' if repeatable and active else 'warning', eligible=repeatable and active,
                      image=str(final_path), thumbnail=spec['thumbnail'], settings=renderer.settings,
                      backend=renderer.backend, source_revision=spec.get('source_revision', 'project implementation'),
                      initialization_seconds=time.perf_counter()-start if not timings else None,
                      measured_runs=timings, median_warm_seconds=statistics.median(v['total_seconds'] for v in timings),
                      median_render_seconds=statistics.median(v['render_seconds'] for v in timings),
                      median_export_seconds=statistics.median(v['export_seconds'] for v in timings),
                      pixel_hashes=hashes, repeatable=repeatable, repeat_differences=repeat,
                      glass_activity=activity, foreground_exact=True, dimensions=[1920,1080],
                      png_structure=validate_clean_png(final_path.read_bytes(), (1920,1080)),
                      png_sha256=sha256(final_path.read_bytes()))
        if not repeatable or not active:
            result['warning'] = 'Repeatability or glass activity check did not pass; review diagnostics.'
        (folder / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
        emit('done')
        return 0
    except Exception as error:
        emit('failed', error=f'{type(error).__name__}: {str(error)[:1400]}')
        return 1
    finally:
        if renderer is not None and hasattr(renderer, 'close'):
            renderer.close()


def stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def supervise(spec_path):
    spec = json.loads(spec_path.read_text())
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(spec_path)],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    messages = queue.Queue()
    def read():
        for line in process.stdout:
            messages.put(line)
    thread = threading.Thread(target=read, daemon=True)
    thread.start()
    started = time.monotonic()
    deadline = started + 120
    low_since = None
    peak = 0
    init = None
    reason = None
    logs = []
    done = False
    try:
        while process.poll() is None or not messages.empty():
            while not messages.empty():
                line = messages.get_nowait()
                logs.append(line)
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event = message.get('event')
                if event == 'ready':
                    init = time.monotonic()-started  # Includes interpreter/import/startup cost.
                    deadline = time.monotonic()+60
                elif event == 'render_started':
                    deadline = time.monotonic()+60
                elif event == 'failed':
                    reason = message['error']
                elif event == 'done':
                    done = True
            if process.poll() is not None:
                break
            rss = 0
            try:
                parent = psutil.Process(process.pid)
                for member in [parent, *parent.children(recursive=True)]:
                    try:
                        rss += member.memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
                    except (psutil.AccessDenied, PermissionError):
                        reason = 'Process memory monitoring is not permitted'
            except psutil.NoSuchProcess:
                pass
            except (psutil.AccessDenied, PermissionError):
                reason = 'Process-tree monitoring is not permitted'
            peak = max(peak, rss)
            memory = psutil.virtual_memory()
            now = time.monotonic()
            low_since = (low_since if low_since is not None else now) if memory.available/memory.total < .2 else None
            if rss > MEMORY_LIMIT:
                reason = 'Process-tree memory exceeded 36 GiB'
            elif low_since is not None and now-low_since >= LOW_MEMORY_SECONDS:
                reason = 'System available memory stayed below 20% for 2 seconds'
            elif now > deadline:
                reason = 'Initialization timeout (120 s)' if init is None else 'Render/export timeout (60 s)'
            if reason:
                stop_process(process)
                break
            time.sleep(SAMPLE_SECONDS)
        process.wait(timeout=5)
    except BaseException:
        stop_process(process)
        raise
    finally:
        thread.join(timeout=1)
        while not messages.empty():
            logs.append(messages.get_nowait())
        (Path(spec['work'])/'worker.log').write_text(''.join(logs))
    path = Path(spec['work'])/'result.json'
    if process.returncode == 0 and path.exists() and not reason:
        result = json.loads(path.read_text())
    else:
        result = {key: spec[key] for key in ('case_id','input_id','method','tool','preset')}
        result.update(status='failed', eligible=False, error=reason or f'Worker exited with code {process.returncode}')
    result.update(initialization_seconds=init, peak_process_tree_bytes=peak,
                  memory_sampling_seconds=SAMPLE_SECONDS, memory_limit_gib=36,
                  memory_note='Sum of sampled process RSS, including browser children; shared pages may be counted more than once; GPU allocations are not fully measured')
    return result


def preparation_inputs():
    records = {}
    for path in sorted((RESULTS/'runs').glob('preparation-*.json')):
        report = json.loads(path.read_text())
        for item in report['images']:
            records[item['input_id']] = item
    if set(records) != {'portrait-01', 'landscape-01'}:
        raise ValueError('Prepare both photos before running the comparison')
    for key, item in records.items():
        path = RESULTS / item['output_file']
        data = path.read_bytes()
        if sha256(data) != item['png_sha256'] or item['status'] != 'passed':
            raise ValueError('Prepared photo does not match its verification record')
        validate_clean_png(data, tuple(item['prepared_size']))
        source = ENGINE.parent/'data/WallPaper_v0.1_2026-10-28'/item['source_file']
        if sha256(source.read_bytes()) != item['source_sha256_before']:
            raise ValueError('Original source hash changed')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--case', action='append', default=[], help='Run selected matrix case IDs; all other positions remain visible')
    parser.add_argument('--resume', help='Resume failed/planned cases in a run with the same code and inputs')
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    if RESULTS.resolve() != RESULTS:
        raise ValueError('Results must not be redirected through a symlink')
    subprocess.run([sys.executable, str(SHELF/'acquire_sources.py'), '--verify-only'], check=True)
    subprocess.run(['node', str(SHELF/'build-adapters.mjs')], check=True)
    prepared = preparation_inputs()
    sources = json.loads((SHELF/'source-manifest.json').read_text())
    revisions = {s['id']:s['revision'] for s in sources['sources']}
    fingerprint = hashlib.sha256()
    for path in sorted(list((ENGINE/'code').glob('*.py')) + list((SHELF/'adapters').glob('*')) +
                       [SHELF/'build-adapters.mjs',SHELF/'package-lock.json',SHELF/'requirements.lock',SHELF/'source-manifest.json']):
        fingerprint.update(path.read_bytes())
    for item in prepared.values():
        fingerprint.update(item['png_sha256'].encode())
    signature = fingerprint.hexdigest()
    run_id = args.resume or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in run_id):
        raise ValueError('Invalid run ID')
    run_dir = RESULTS/'runs'/run_id
    matrix = list(csv.DictReader((DOCS/'comparison-matrix.csv').open()))
    if set(args.case)-{r['case_id'] for r in matrix}:
        raise ValueError('Unknown matrix case ID')
    if args.resume:
        manifest = json.loads((run_dir/'manifest.json').read_text())
        if manifest['run']['code_and_input_sha256'] != signature:
            raise ValueError('Code or inputs changed; start a new run instead of resuming')
        cases = manifest['cases']
        run = manifest['run']
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        cases = [{**row, 'status':'planned'} for row in matrix]
        run = {'id':run_id, 'code_and_input_sha256':signature,
               'started_utc':datetime.now(timezone.utc).isoformat(), 'source_revisions':revisions,
               'rules':{'canvas':[1920,1080],'warmup_runs':1,'measured_warm_runs':3,'threads':12,
                        'initialization_timeout_s':120,'render_export_timeout_s':60,'memory_limit_gib':36,
                        'system_available_memory_minimum':.2,'sustained_low_memory_s':2,'sample_interval_s':.1},
               'timing_scope':'Initialization includes worker startup, decoding, imports, maps and browser setup. Warm time includes native rendering, capture, foreground restore, clean PNG encode, validation and fsync. Shared preparation/maps are excluded and timed separately.',
               'prepared':{k:{'size':v['prepared_size'],'source_sha256':v['source_sha256_before']} for k,v in prepared.items()}}
    shared_begin = time.perf_counter()
    common = run_dir/'common';common.mkdir(exist_ok=True)
    for key, item in prepared.items():
        photo = Image.open(RESULTS/item['output_file']).convert('RGB')
        write_new_or_identical(common/f'{key}-backdrop.png', clean_png_bytes(blurred_backdrop(photo)))
        for preset in ('clear','frosted','strong-edge'):
            path=common/f'{key}-{preset}-maps.npz'
            if not path.exists():
                np.savez(path, **glass_maps(photo,preset))
    run['shared_preparation_seconds'] = time.perf_counter()-shared_begin
    def save():
        (run_dir/'manifest.json').write_text(json.dumps({'run':run,'cases':cases},indent=2)+'\n')
        write_report(run,cases,DOCS/'index.html',RESULTS/'prepared')
    save()
    # Use the requested tool order. Keep display order from the 54-position matrix.
    order={'S1':0,'D1':1,'D2':2,'D3':3,'S2':4}
    for row in sorted(matrix,key=lambda r:order[r['tool']]):
        index=next(i for i,r in enumerate(cases) if r['case_id']==row['case_id'])
        if args.case and row['case_id'] not in args.case:
            continue
        if args.resume and cases[index]['status']=='passed':
            continue
        key=row['input_id'];work=run_dir/'cases'/row['case_id'];work.mkdir(parents=True,exist_ok=True)
        backdrop=common/f'{key}-backdrop.png'
        maps=common/f"{key}-{row['preset']}-maps.npz"
        spec={**row,'prepared':str(RESULTS/prepared[key]['output_file']),'work':str(work),
              'output':str(RESULTS/'outputs'/run_id/(row['case_id']+'.png')),
              'thumbnail':str(RESULTS/'thumbnails'/run_id/(row['case_id']+'.png')),
              'diagnostics':str(RESULTS/'diagnostics'/run_id),
              'backdrop':str(backdrop),'backdrop_sha256':sha256(backdrop.read_bytes()),
              'maps':str(maps),'maps_sha256':sha256(maps.read_bytes()) if maps.exists() else None,
              'source_revision':revisions.get(row['tool'],'project implementation')}
        spec_path=work/'spec.json';spec_path.write_text(json.dumps(spec,indent=2)+'\n')
        print(f"RUN {row['case_id']}",flush=True)
        result=supervise(spec_path)
        cases[index]=result
        print(f"  {result['status']}"+(f" — {result['error']}" if result.get('error') else ''),flush=True)
        save()
    # Compare static pairs on decoded pixels outside the protected foreground.
    for row in cases:
        if row['tool']!='S2' or not row.get('image'):
            continue
        first=next(r for r in cases if r['input_id']==row['input_id'] and r['method']==row['method'] and r['preset']==row['preset'] and r['tool']=='S1')
        if first.get('image'):
            photo=Image.open(RESULTS/prepared[row['input_id']]['output_file']).convert('RGB')
            row['difference_from_S1']=pixel_difference(Image.open(first['image']).convert('RGB'),Image.open(row['image']).convert('RGB'),photo)
    run['originals_unchanged']=all(sha256((ENGINE.parent/'data/WallPaper_v0.1_2026-10-28'/item['source_file']).read_bytes())==item['source_sha256_before'] for item in prepared.values())
    if not run['originals_unchanged']:
        for row in cases:
            row['eligible']=False
            if row['status']=='passed':row['status']='warning'
    run['completed_utc']=datetime.now(timezone.utc).isoformat()
    save()
    if not args.case:
        with (DOCS/'comparison-matrix.csv').open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=['case_id','input_id','method','tool','preset','status'],lineterminator='\n')
            writer.writeheader()
            writer.writerows({k:row[k] for k in writer.fieldnames} for row in cases)
    print(f"Report: {DOCS/'index.html'}",flush=True)
    print(f"Run record: {run_dir/'manifest.json'}",flush=True)
    return 0 if run['originals_unchanged'] and not any(r['status']=='failed' for r in cases) else 1


if __name__ == '__main__':
    raise SystemExit(main())
