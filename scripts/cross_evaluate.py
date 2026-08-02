"""Does a vector tuned for one volatility level cost anything at another?

If not, there is nothing for a volatility-driven controller to gain.
"""
import glob, json
import numpy as np
from scipy import stats
from dynaswarm.config import BudgetCfg, Config, ControlCfg, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

VECTORS = {}
for f in sorted(glob.glob('multirun/*/*/*/best_fixed.json')):
    d = json.load(open(f))
    VECTORS[d['scenario']] = d['params']

CHURN = {'static': 0.0, 'moderate': 0.006, 'high': 0.015}
GRAPH = GraphCfg(model='geometric', n_nodes=200, density=0.04)
N = 12

def evaluate(params, churn):
    cfg = Config(graph=GRAPH, scenario=ScenarioCfg(name='x', churn=churn, timesteps=60),
                 experiment=ExperimentCfg(n_trials=N), budget=BudgetCfg(evaluations=300),
                 control=ControlCfg(fixed_params=params))
    out = []
    for t in range(N):
        rows = run_trial(cfg, t, ['aco']).steps
        v = [r.excess for r in rows if r.excess is not None]
        if v: out.append(float(np.mean(v)))
    return np.array(out)

print('CROSS-EVALUATION: rows = vector tuned for, columns = evaluated on')
print('(evaluation seeds, never seen by any tuning run)')
print()
names = ['static', 'moderate', 'high']
results = {}
for tuned_for in names:
    for run_on in names:
        results[(tuned_for, run_on)] = evaluate(VECTORS[tuned_for], CHURN[run_on])

print(f'{"tuned for":12s}' + ''.join(f'{n:>12s}' for n in names))
for tuned_for in names:
    row = ''.join(f'{results[(tuned_for, n)].mean():11.2%} ' for n in names)
    print(f'{tuned_for:12s}{row}')

print()
print('Does the matching vector beat the mismatched ones on each scenario?')
for run_on in names:
    native = results[(run_on, run_on)]
    for tuned_for in names:
        if tuned_for == run_on:
            continue
        other = results[(tuned_for, run_on)]
        try:
            _, p = stats.wilcoxon(native, other)
        except ValueError:
            p = float('nan')
        verdict = 'native better' if native.mean() < other.mean() else 'MISMATCHED BETTER'
        print(f'  on {run_on:9s}: native {native.mean():6.2%} vs {tuned_for:9s} {other.mean():6.2%}  '
              f'delta {native.mean()-other.mean():+6.2%}  p={p:.3f}  {verdict}')
