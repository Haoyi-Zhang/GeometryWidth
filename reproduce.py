"""Rebuild and verify all finite evidence, with one process and bounded inputs."""

if not __debug__:
    raise RuntimeError("Optimized Python mode is intentionally unsupported for the retained audit.")

import argparse
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tests'))
from produce import generate
from check import validate
from test_certificates import run_tests
from check_references import validate as validate_references
from check_reference_external import validate as validate_external_references
from holdout_stress import generate as generate_holdout
from verify_holdout import verify as verify_holdout, mutation_tests as holdout_mutation_tests
from reviewer_audit import audit as reviewer_audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    start = time.perf_counter()
    cpu = time.process_time()
    stages = []
    def stage(name, function):
        a,b = time.perf_counter(),time.process_time()
        result = function()
        stages.append({'name':name,'wall_seconds':time.perf_counter()-a,
                       'cpu_seconds':time.process_time()-b})
        return result
    summary = stage('generate',lambda: generate(args.output))
    payload = json.loads((args.output/'certificates.json').read_text())
    checked = stage('independent-check',lambda: validate(payload))
    tested = stage('mutations-and-algebra',lambda: run_tests(payload))
    references = stage('reference-audit',lambda: validate_references(ROOT/'reference_audit.csv'))
    external_references = stage(
        'external-reference-audit',
        lambda: validate_external_references(ROOT/'reference_external_audit.csv'))
    holdout_path = args.output/'holdout-stress.json'
    stage('holdout-generate', lambda: generate_holdout(holdout_path))
    holdout_payload = json.loads(holdout_path.read_text())
    holdout = stage('holdout-independent-check', lambda: verify_holdout(holdout_payload))
    holdout['mutations'] = stage('holdout-mutations', lambda: holdout_mutation_tests(holdout_payload))
    holdout['targeted_mutations_rejected'] = sum(x['rejected'] for x in holdout['mutations'])
    source_audit = stage('static-source-audit', lambda: reviewer_audit(ROOT))
    for name, value in [('verification.json',checked),('tests.json',tested),
                        ('reference-audit.json',references),
                        ('reference-external-audit.json',external_references),
                        ('holdout-verification.json',holdout),
                        ('final-review-audit.json',source_audit)]:
        (args.output/name).write_text(json.dumps(value,indent=2)+'\n')
    metrics = {'completed':True,'workers':1,'child_processes':0,'stages':stages,
               'wall_seconds':time.perf_counter()-start,
               'cpu_seconds':time.process_time()-cpu,
               'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'timing_scope':'this reproduction command, not a general proof or performance benchmark'}
    (args.output/'execution.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps({'verification':checked,
                      'tests':{k:v for k,v in tested.items() if k!='mutations'},
                      'references':references, 'external_references':external_references,
                      'holdout':{k:v for k,v in holdout.items() if k!='mutations'},
                      'source_audit':source_audit, 'execution':metrics},indent=2))


if __name__ == '__main__':
    main()
