#!/usr/bin/env python3
"""Diagnostic: eight workers, before/after local embedder initialization.

Run between indexing sizes, in the same image and environment. This does
not replace the indexing benchmark. Anonymous local-embedding memory is
estimated by the private-page increment; shared code comes from main-run
mapping samples. Keep workers alive at each barrier to count shared pages
proportionally across all eight rather than multiplying a single RSS value.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def snapshot():
    result = {}
    for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
        if line.startswith(('Pss:', 'Private_Clean:', 'Private_Dirty:')):
            key, value = line.split(':', 1)
            result[key] = int(value.split()[0])
    embedding_pss = embedding_private = 0
    embedding = False
    for line in Path('/proc/self/smaps').read_text().splitlines():
        parts = line.split()
        if parts and '-' in parts[0] and ':' not in parts[0]:
            path = parts[-1] if len(parts) >= 6 else ''
            embedding = any(part in path for part in
                ('/torch/', '/nvidia/', '/triton/', '/sentence_transformers/',
                 '/tokenizers/', '/safetensors/',
                 '/models--sentence-transformers--static-retrieval-mrl-en-v1/'))
        elif embedding and line.startswith('Pss:'):
            embedding_pss += int(parts[1])
        elif embedding and line.startswith(('Private_Clean:', 'Private_Dirty:')):
            embedding_private += int(parts[1])
    result['embedding_shared_kb'] = max(0, embedding_pss - embedding_private)
    return result


def worker(rank, directory, config):
    # Match modules used by the actual indexer before constructing the model.
    import yaml
    from pathway.xpacks.llm import embedders  # noqa: F401

    from serviette.config.schema import EmbedderConfig, SplitterConfig
    from serviette.indexer.graph import ParserRegistry, build_xpack_embedder, build_xpack_splitter
    settings = yaml.safe_load(config.read_text())
    cfg = EmbedderConfig(**settings['embedder'])
    # These remain necessary with a remote embedder. Include their lazy
    # imports and tokenizer allocations in the pre-embedder baseline.
    parser = ParserRegistry()
    splitter = build_xpack_splitter(SplitterConfig(**settings['splitter']))
    text = 'Wikipedia articles describe history, science and geography. ' * 70
    parsed = parser.parse(text.encode(), '.txt')
    assert splitter.chunk(parsed)
    stages = ['baseline', 'runtime', 'model_warm', 'model_released']
    for stage in stages:
        while not (directory / f'{stage}.go').exists():
            time.sleep(0.05)
        if stage == 'runtime':
            import sentence_transformers  # noqa: F401
        elif stage == 'model_warm':
            embedder = build_xpack_embedder(cfg)
            for _ in range(3):
                vectors = embedder.__wrapped__([text] * cfg.batch_size)
                assert len(vectors[0]) == 256
            del vectors
        elif stage == 'model_released':
            del embedder
        gc.collect()
        # Let background purging settle, without changing allocator settings.
        time.sleep(2)
        (directory / f'{stage}.{rank}.ready').write_text('ready')
        while not (directory / f'{stage}.sample').exists():
            time.sleep(0.05)
        (directory / f'{stage}.{rank}.json').write_text(json.dumps(snapshot()))
    while not (directory / 'finish').exists():
        time.sleep(0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=int)
    parser.add_argument('--directory', type=Path, default=Path('/tmp/embedder-calibration'))
    parser.add_argument('--config', type=Path, default=Path('/bench/config.yaml'))
    args = parser.parse_args()
    if args.worker is not None:
        worker(args.worker, args.directory, args.config)
        return
    args.directory.mkdir()
    children = [subprocess.Popen([sys.executable, __file__, '--worker', str(rank),
                                 '--directory', str(args.directory), '--config', str(args.config)],
                                env={**os.environ, 'PATHWAY_PROCESS_ID': str(rank)},
                                stdout=sys.stderr) for rank in range(8)]
    result = {'description': __doc__, 'workers': 8,
              'baseline_includes': 'graph imports, UTF-8 parser, initialized and warmed configured splitter',
              'jemalloc_conf': os.environ.get('_RJEM_MALLOC_CONF'),
              'omp_threads': os.environ.get('OMP_NUM_THREADS'), 'stages': {}}
    try:
        for stage in ['baseline', 'runtime', 'model_warm', 'model_released']:
            (args.directory / f'{stage}.go').touch()
            for suffix in ['ready', 'json']:
                deadline = time.monotonic() + 180
                while not all((args.directory / f'{stage}.{rank}.{suffix}').exists() for rank in range(8)):
                    if any(child.poll() is not None for child in children):
                        raise RuntimeError('Diagnostic worker exited')
                    if time.monotonic() > deadline:
                        raise TimeoutError(stage)
                    time.sleep(0.1)
                if suffix == 'ready':
                    (args.directory / f'{stage}.sample').touch()
            result['stages'][stage] = [json.loads((args.directory / f'{stage}.{rank}.json').read_text()) for rank in range(8)]
        print(json.dumps(result, indent=2))
    finally:
        (args.directory / 'finish').touch()
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            child.wait()


if __name__ == '__main__':
    main()
