#!/usr/bin/env python3
"""Independent numerical acceptance checks for the native Hamiltonian compiler.

The derivatives below are handwritten. This module never reads generated ASTs,
emitted force code, or the Lang solver implementation. All variables are
nondimensional. Only Python's standard library is needed.

    python3 test/hamiltonian_reference.py calibrate --output out/calibration.json
    python3 test/hamiltonian_reference.py verify manifest.json --output report.json
    python3 test/hamiltonian_reference.py reference quartic --output reference.csv

Manifest keys: harmonic (three CSV paths), long_harmonic (two CSV paths),
quartic (CSV path), double_well (optional CSV path), reversal (CSV path),
gradients ([O0 gradient CSV, O2 gradient CSV]),
optimization_pairs ([[O0 trajectory CSV, O2 trajectory CSV], ...]).
An optional quartic_changed trajectory edits only b from .4 to .9; it uses the
same frozen tolerances and a separately evaluated handwritten RK4 oracle.
Trajectory columns: step,time,q_x,q_y,p_x,p_y,energy. Gradient columns:
model,x,y,force_x,force_y,potential. Model names: harmonic,quartic,double_well.
Reversal CSV contains its initial and returned states after N forward steps,
flipping both momenta, N forward steps, and flipping both momenta again.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Sequence


MASS = 1.3
SPRING = 0.8
QUARTIC = 0.6
COUPLING = 0.4
CHANGED_COUPLING = 0.9
INITIAL = (0.7, -0.4, 0.2, 0.3)  # q_x, q_y, p_x, p_y
FINAL_TIME = 3.68
HARMONIC_STEPS = (0.04, 0.02, 0.01)
LONG_TIME = 1000.0
REFERENCE_STEPS = (0.01, 0.005, 0.0025)
GRADIENT_POINTS = ((0.0, 0.0), (0.7, -0.4), (-1.2, 0.3),
                   (0.25, -0.9), (1.1, 1.3))
SOURCES = {
    "Hamiltonian equations": "https://www.unige.ch/~hairer/poly_geoint/week1.pdf",
    "Störmer–Verlet splitting and order": "https://www.unige.ch/~hairer/poly_geoint/week2.pdf",
}

# Frozen before any generated trajectory is inspected. These bounds concern
# this experiment and its steps/horizons, not all Hamiltonian systems.
TOLERANCES = {
    "gradient_absolute": 5e-13,
    "gradient_relative": 5e-13,
    "energy_formula_absolute": 5e-13,
    "energy_formula_relative": 5e-13,
    "harmonic_state_error_per_h2": 0.5,
    "harmonic_convergence_ratio_min": 3.7,
    "harmonic_convergence_ratio_max": 4.3,
    "harmonic_energy_bound_roundoff": 5e-11,
    "long_energy_convergence_ratio_min": 3.7,
    "long_energy_convergence_ratio_max": 4.3,
    "nonlinear_state_error_per_h2": 1.0,
    "nonlinear_relative_energy_error_per_h2": 2.0,
    "rk4_refinement_difference_max": 1e-9,
    "rk4_refinement_ratio_min": 12.0,
    "rk4_refinement_ratio_max": 20.0,
    "reversal_absolute": 5e-10,
    "optimization_absolute": 5e-11,
    "optimization_relative": 5e-11,
    "time_absolute": 2e-10,
}

State = tuple[float, float, float, float]


def potential(model: str, x: float, y: float) -> float:
    if model == "harmonic":
        return SPRING * (x*x + y*y) / 2
    if model in ("quartic", "quartic_changed"):
        coupling = COUPLING if model == "quartic" else CHANGED_COUPLING
        return (SPRING * (x*x + y*y) / 2
                + QUARTIC * (x**4 + y**4) / 4
                + coupling * x*x*y*y / 2)
    if model == "double_well":
        return 0.25*(x*x-1)**2 + 0.375*y*y + 0.1*x*y + 0.05*y**4
    raise ValueError(f"unknown oracle model: {model}")


def force(model: str, x: float, y: float) -> tuple[float, float]:
    if model == "harmonic":
        return -SPRING*x, -SPRING*y
    if model in ("quartic", "quartic_changed"):
        coupling = COUPLING if model == "quartic" else CHANGED_COUPLING
        # Independently differentiated on paper, not obtained from the reader.
        return (-SPRING*x-QUARTIC*x**3-coupling*x*y*y,
                -SPRING*y-QUARTIC*y**3-coupling*x*x*y)
    if model == "double_well":
        return x-x**3-0.1*y, -0.75*y-0.1*x-0.2*y**3
    raise ValueError(f"unknown oracle model: {model}")


def energy(model: str, state: Sequence[float]) -> float:
    x, y, px, py = state
    return (px*px + py*py) / (2*MASS) + potential(model, x, y)


def harmonic_exact(time: float, initial: State = INITIAL) -> State:
    omega = math.sqrt(SPRING/MASS)
    c, s = math.cos(omega*time), math.sin(omega*time)
    x, y, px, py = initial
    return (x*c + px*s/(MASS*omega), y*c + py*s/(MASS*omega),
            px*c - MASS*omega*x*s, py*c - MASS*omega*y*s)


def rhs(model: str, state: State) -> State:
    x, y, px, py = state
    fx, fy = force(model, x, y)
    return px/MASS, py/MASS, fx, fy


def shifted(state: State, deriv: State, scale: float) -> State:
    return tuple(x + scale*dx for x, dx in zip(state, deriv))


def rk4_step(model: str, state: State, step: float) -> State:
    k1 = rhs(model, state)
    k2 = rhs(model, shifted(state, k1, step/2))
    k3 = rhs(model, shifted(state, k2, step/2))
    k4 = rhs(model, shifted(state, k3, step))
    return tuple(x + step*(a + 2*b + 2*c + d)/6
                 for x, a, b, c, d in zip(state, k1, k2, k3, k4))


def integrate_rk4(model: str, step: float, time: float = FINAL_TIME,
                  initial: State = INITIAL) -> State:
    count = round(time/step)
    if abs(count*step-time) > 1e-12:
        raise ValueError("reference time must be an integer number of steps")
    state = initial
    for _ in range(count):
        state = rk4_step(model, state, step)
    return state


def max_difference(a: Sequence[float], b: Sequence[float]) -> float:
    return max(abs(x-y) for x, y in zip(a, b))


def reference_refinement(model: str) -> dict:
    states = [integrate_rk4(model, h) for h in REFERENCE_STEPS]
    differences = [max_difference(states[i], states[i+1]) for i in range(2)]
    ratio = differences[0]/differences[1]
    passed = (differences[1] <= TOLERANCES["rk4_refinement_difference_max"]
              and TOLERANCES["rk4_refinement_ratio_min"] <= ratio
              <= TOLERANCES["rk4_refinement_ratio_max"])
    result = {"model": model, "steps": REFERENCE_STEPS, "final_time": FINAL_TIME,
              "states": states, "successive_differences": differences,
              "refinement_ratio": ratio,
              "estimated_fine_error": differences[1]/15,
              "passed": passed}
    if model == "harmonic":
        result["analytic_errors"] = [max_difference(s, harmonic_exact(FINAL_TIME))
                                      for s in states]
    return result


def finite_difference_sweep() -> dict:
    """Supplemental central differences; handwritten derivatives remain primary."""
    results = []
    for delta in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7):
        maximum = 0.0
        for model in ("harmonic", "quartic", "double_well"):
            for x, y in GRADIENT_POINTS:
                numerical = (-(potential(model, x+delta, y)-potential(model, x-delta, y))/(2*delta),
                             -(potential(model, x, y+delta)-potential(model, x, y-delta))/(2*delta))
                maximum = max(maximum, max_difference(numerical, force(model, x, y)))
        results.append({"perturbation": delta, "maximum_force_error": maximum})
    return {"method": "central differences of independently handwritten potential",
            "sweep": results, "role": "supplemental; no acceptance based solely on differences"}


def verlet_reference_step(model: str, state: State, step: float) -> State:
    """Calibration only; generated nonlinear results are checked against RK4."""
    x, y, px, py = state
    fx, fy = force(model, x, y)
    pxh, pyh = px + step*fx/2, py + step*fy/2
    xn, yn = x + step*pxh/MASS, y + step*pyh/MASS
    fxn, fyn = force(model, xn, yn)
    return xn, yn, pxh + step*fxn/2, pyh + step*fyn/2


def integrate_verlet(model: str, step: float, time: float) -> State:
    state = INITIAL
    for _ in range(round(time/step)):
        state = verlet_reference_step(model, state, step)
    return state


def harmonic_energy_bound(step: float, initial: State = INITIAL) -> float:
    """Bound from the exact quadratic invariant of the Verlet recurrence.

    H_tilde = p^2/(2m) + k/2*(1-h^2*k/(4m))*q^2 is invariant in exact
    arithmetic. Therefore |H_n-H_0| <= z*H_tilde/(4*(1-z/4)), z=h^2*k/m.
    This is an experiment-specific analytic bound, with a roundoff allowance.
    """
    z = step*step*SPRING/MASS
    if not 0 < z < 4:
        raise ValueError("harmonic step is outside the Verlet stability interval")
    x, y, px, py = initial
    modified = ((px*px+py*py)/(2*MASS)
                + SPRING*(1-z/4)*(x*x+y*y)/2)
    return z*modified/(4*(1-z/4))


def calibration() -> dict:
    errors = [max_difference(integrate_verlet("harmonic", h, FINAL_TIME),
                             harmonic_exact(FINAL_TIME)) for h in HARMONIC_STEPS]
    long = []
    for h in HARMONIC_STEPS[:2]:
        state, e0, maximum = INITIAL, energy("harmonic", INITIAL), 0.0
        for _ in range(round(LONG_TIME/h)):
            state = verlet_reference_step("harmonic", state, h)
            maximum = max(maximum, abs(energy("harmonic", state)-e0))
        long.append({"step": h, "horizon": LONG_TIME,
                     "maximum_absolute_energy_error": maximum,
                     "analytic_bound": harmonic_energy_bound(h)})
    return {
        "contract": "frozen before generated native trajectories",
        "method_references": SOURCES,
        "variables": "nondimensional canonical q_x,q_y,p_x,p_y",
        "constants": {"m": MASS, "k": SPRING, "a": QUARTIC, "b": COUPLING},
        "initial_state": INITIAL, "final_time": FINAL_TIME,
        "tolerances": TOLERANCES,
        "gradient_samples": [{"model": model, "x": x, "y": y,
                              "force": force(model, x, y),
                              "potential": potential(model, x, y)}
                             for model in ("harmonic", "quartic", "double_well")
                             for x, y in GRADIENT_POINTS],
        "harmonic_calibration": {"steps": HARMONIC_STEPS, "errors": errors,
                                 "ratios": [errors[i]/errors[i+1] for i in range(2)]},
        "long_harmonic_calibration": long,
        "finite_difference_sweep": finite_difference_sweep(),
        "rk4_references": {model: reference_refinement(model)
                           for model in ("harmonic", "quartic", "double_well")},
    }


def read_trajectory(path: str | Path) -> list[dict]:
    with open(path, newline="") as file:
        reader = csv.DictReader(file)
        required = ("step", "time", "q_x", "q_y", "p_x", "p_y", "energy")
        if not reader.fieldnames or any(k not in reader.fieldnames for k in required):
            raise ValueError(f"{path}: required columns are {','.join(required)}")
        rows = []
        for index, row in enumerate(reader, 2):
            data = {key: float(row[key]) for key in required}
            if not all(math.isfinite(value) for value in data.values()):
                raise ValueError(f"{path}:{index}: nonfinite trajectory value")
            if data["step"] != int(data["step"]):
                raise ValueError(f"{path}:{index}: noninteger step index")
            rows.append(data)
    if len(rows) < 2:
        raise ValueError(f"{path}: trajectory needs at least initial and final rows")
    return rows


def row_state(row: dict) -> State:
    return tuple(row[key] for key in ("q_x", "q_y", "p_x", "p_y"))


def near(a: float, b: float, absolute: float, relative: float = 0.0) -> bool:
    return abs(a-b) <= absolute + relative*max(abs(a), abs(b))


def trajectory_metadata(rows: list[dict], model: str) -> dict:
    first, last = rows[0], rows[-1]
    delta_step = last["step"]-first["step"]
    if delta_step <= 0:
        raise ValueError("trajectory step indices must increase")
    h = (last["time"]-first["time"])/delta_step
    if h <= 0 or not math.isfinite(h):
        raise ValueError("trajectory needs a positive finite step")
    chronological = all(a["step"] < b["step"] and a["time"] < b["time"]
                        for a, b in zip(rows, rows[1:]))
    times_match = all(near(row["time"], first["time"]+(row["step"]-first["step"])*h,
                           TOLERANCES["time_absolute"]) for row in rows)
    energy_errors = [abs(row["energy"]-energy(model, row_state(row))) for row in rows]
    energy_formula_pass = all(near(row["energy"], energy(model, row_state(row)),
                                   TOLERANCES["energy_formula_absolute"],
                                   TOLERANCES["energy_formula_relative"]) for row in rows)
    initial_ok = (first["step"] == 0 and abs(first["time"]) <= 1e-15
                  and max_difference(row_state(first), INITIAL) <= 1e-15)
    e0 = energy(model, INITIAL)
    maximum = max(abs(energy(model, row_state(row))-e0) for row in rows)
    return {"step": h, "horizon": last["time"], "rows": len(rows),
            "initial_state_matches": initial_ok,
            "chronological": chronological, "times_match_steps": times_match,
            "maximum_energy_formula_error": max(energy_errors),
            "energy_formula_pass": energy_formula_pass,
            "maximum_absolute_energy_error": maximum,
            "maximum_relative_energy_error": maximum/abs(e0),
            "passed": initial_ok and chronological and times_match and energy_formula_pass}


def analyze_harmonic(paths: Sequence[str]) -> dict:
    runs = []
    for path in paths:
        rows = read_trajectory(path)
        result = trajectory_metadata(rows, "harmonic")
        error = max_difference(row_state(rows[-1]), harmonic_exact(FINAL_TIME))
        all_errors = [max_difference(row_state(row), harmonic_exact(row["time"]))
                      for row in rows]
        result.update(path=str(path), endpoint_error=error,
                      maximum_sampled_state_error=max(all_errors))
        result["passed"] = (result["passed"]
                            and near(result["horizon"], FINAL_TIME,
                                     TOLERANCES["time_absolute"])
                            and max(all_errors) <= result["step"]**2
                            * TOLERANCES["harmonic_state_error_per_h2"])
        runs.append(result)
    runs.sort(key=lambda r: r["step"], reverse=True)
    ratios = [runs[i]["endpoint_error"]/runs[i+1]["endpoint_error"]
              for i in range(len(runs)-1)]
    steps_match = (len(runs) == 3 and all(near(r["step"], h, 1e-14)
                                        for r, h in zip(runs, HARMONIC_STEPS)))
    passed = (steps_match and all(r["passed"] for r in runs)
              and all(TOLERANCES["harmonic_convergence_ratio_min"] <= r
                      <= TOLERANCES["harmonic_convergence_ratio_max"] for r in ratios))
    return {"runs": runs, "endpoint_error_ratios": ratios, "passed": passed}


def analyze_long_harmonic(paths: Sequence[str]) -> dict:
    runs = []
    for path in paths:
        rows = read_trajectory(path)
        result = trajectory_metadata(rows, "harmonic")
        bound = harmonic_energy_bound(result["step"])
        result.update(path=str(path), analytic_energy_error_bound=bound,
                      energy_error_per_h2=result["maximum_absolute_energy_error"]
                      / result["step"]**2)
        result["passed"] = (result["passed"]
                            and near(result["horizon"], LONG_TIME,
                                     TOLERANCES["time_absolute"])
                            and result["maximum_absolute_energy_error"] <= bound
                            + TOLERANCES["harmonic_energy_bound_roundoff"])
        runs.append(result)
    runs.sort(key=lambda r: r["step"], reverse=True)
    ratio = (runs[0]["maximum_absolute_energy_error"]
             / runs[1]["maximum_absolute_energy_error"]) if len(runs) == 2 else None
    steps_match = (len(runs) == 2 and all(near(r["step"], h, 1e-14)
                                        for r, h in zip(runs, HARMONIC_STEPS[:2])))
    passed = (steps_match and all(r["passed"] for r in runs)
              and TOLERANCES["long_energy_convergence_ratio_min"] <= ratio
              <= TOLERANCES["long_energy_convergence_ratio_max"])
    return {"runs": runs, "maximum_energy_error_ratio": ratio, "passed": passed,
            "interpretation": "bounded sampled energy error; not exact conservation"}


def analyze_nonlinear(path: str, model: str) -> dict:
    rows = read_trajectory(path)
    result = trajectory_metadata(rows, model)
    refinement = reference_refinement(model)
    # Independently recompute a fine RK4 state at every exported time. Advancing
    # one shared reference state avoids O(number_of_rows * total_steps) work.
    state, reference_time, maximum = INITIAL, 0.0, 0.0
    fine_step = REFERENCE_STEPS[-1]
    for row in rows:
        count = round((row["time"]-reference_time)/fine_step)
        if abs(reference_time+count*fine_step-row["time"]) > TOLERANCES["time_absolute"]:
            raise ValueError("nonlinear output times must align with reference h=.0025")
        for _ in range(count):
            state = rk4_step(model, state, fine_step)
        reference_time = row["time"]
        maximum = max(maximum, max_difference(row_state(row), state))
    result.update(path=str(path), model=model, rk4_reference=refinement,
                  endpoint_error=max_difference(row_state(rows[-1]), state),
                  maximum_sampled_state_error=maximum)
    result["passed"] = (result["passed"] and refinement["passed"]
                        and near(result["horizon"], FINAL_TIME, TOLERANCES["time_absolute"])
                        and maximum <= TOLERANCES["nonlinear_state_error_per_h2"]*result["step"]**2
                        and result["maximum_relative_energy_error"]
                        <= TOLERANCES["nonlinear_relative_energy_error_per_h2"]*result["step"]**2)
    return result


def analyze_reversal(path: str) -> dict:
    rows = read_trajectory(path)
    error = max_difference(row_state(rows[0]), row_state(rows[-1]))
    initial_ok = max_difference(row_state(rows[0]), INITIAL) <= 1e-15
    elapsed = rows[-1]["time"]-rows[0]["time"]
    advances = rows[-1]["step"] > rows[0]["step"]
    horizon_ok = near(elapsed, 2*FINAL_TIME, TOLERANCES["time_absolute"])
    return {"path": str(path), "initial_state": row_state(rows[0]),
            "returned_state": row_state(rows[-1]), "maximum_state_error": error,
            "elapsed_time": elapsed, "horizon_matches_two_legs": horizon_ok,
            "protocol": "N steps; flip both p; N steps; flip both p again",
            "passed": initial_ok and advances and horizon_ok
            and error <= TOLERANCES["reversal_absolute"]}


def analyze_coupling_variation(original: str, changed: str) -> dict:
    """Describe component energy exchange using an explicit decomposition.

    Ex and Ey exclude interaction energy Eb=b*x^2*y^2/2. They are not separately
    conserved. Their ranges describe this sampled run, not a conservation or
    chaos claim. RK4/energy checks separately validate both trajectories.
    """
    runs = []
    trajectories = [read_trajectory(path) for path in (original, changed)]
    for path, rows, b in zip((original, changed), trajectories, (COUPLING, CHANGED_COUPLING)):
        components = []
        for row in rows:
            x, y, px, py = row_state(row)
            components.append((px*px/(2*MASS)+SPRING*x*x/2+QUARTIC*x**4/4,
                               py*py/(2*MASS)+SPRING*y*y/2+QUARTIC*y**4/4,
                               b*x*x*y*y/2))
        discrepancy = max(abs(sum(parts)-row['energy']) for parts, row in zip(components, rows))
        runs.append({'path': path, 'coupling': b, 'horizon': rows[-1]['time'],
                     'component_definitions': ['Ex=px^2/(2m)+k*x^2/2+a*x^4/4',
                                               'Ey=py^2/(2m)+k*y^2/2+a*y^4/4',
                                               'Eb=b*x^2*y^2/2'],
                     'sampled_component_ranges': [max(c[i] for c in components)-min(c[i] for c in components) for i in range(3)],
                     'maximum_component_sum_discrepancy': discrepancy})
    same_times = [r['time'] for r in trajectories[0]] == [r['time'] for r in trajectories[1]]
    separation = max(max_difference(row_state(a), row_state(b)) for a, b in zip(*trajectories))
    return {'runs': runs, 'maximum_sampled_state_separation': separation,
            'interpretation': 'sampled changes in a stated energy decomposition; no separate conservation claim',
            'passed': same_times and separation > 0 and all(
                r['maximum_component_sum_discrepancy'] <= TOLERANCES['energy_formula_absolute'] for r in runs)}


def analyze_gradients(path: str) -> dict:
    with open(path, newline="") as file:
        rows = list(csv.DictReader(file))
    samples, observed = [], set()
    for row in rows:
        model = row["model"]
        x, y = float(row["x"]), float(row["y"])
        expected = (*force(model, x, y), potential(model, x, y))
        actual = tuple(float(row[key]) for key in ("force_x", "force_y", "potential"))
        finite = all(math.isfinite(v) for v in (x, y, *actual))
        passed = finite and all(near(a, b, TOLERANCES["gradient_absolute"],
                                    TOLERANCES["gradient_relative"])
                                for a, b in zip(actual, expected))
        samples.append({"model": model, "point": (x, y), "actual": actual,
                        "expected": expected, "maximum_error": max_difference(actual, expected),
                        "passed": passed})
        observed.add((model, x, y))
    required = {(model, x, y) for model in ("harmonic", "quartic", "double_well")
                for x, y in GRADIENT_POINTS}
    if any(model == "quartic_changed" for model, _, _ in observed):
        required |= {("quartic_changed", x, y) for x, y in GRADIENT_POINTS}
    return {"path": str(path), "samples": samples,
            "missing_required_samples": sorted(required-observed),
            "passed": not (required-observed) and all(s["passed"] for s in samples)}


def analyze_optimization(pair: Sequence[str]) -> dict:
    left, right = map(read_trajectory, pair)
    same_rows = len(left) == len(right)
    maximum, passed = 0.0, same_rows
    for a, b in zip(left, right):
        passed = passed and a["step"] == b["step"]
        for key in ("time", "q_x", "q_y", "p_x", "p_y", "energy"):
            maximum = max(maximum, abs(a[key]-b[key]))
            passed = passed and near(a[key], b[key], TOLERANCES["optimization_absolute"],
                                     TOLERANCES["optimization_relative"])
    return {"paths": list(map(str, pair)), "maximum_difference": maximum,
            "same_row_count": same_rows, "passed": passed}


def analyze_gradient_optimizations(paths: Sequence[str] | str) -> dict:
    if isinstance(paths, str):
        paths = [paths]
    runs = [analyze_gradients(path) for path in paths]
    compared, maximum = False, 0.0
    if len(runs) >= 2:
        left = {(s["model"], *s["point"]): s["actual"] for s in runs[0]["samples"]}
        right = {(s["model"], *s["point"]): s["actual"] for s in runs[1]["samples"]}
        compared = left.keys() == right.keys()
        if compared:
            for key in left:
                maximum = max(maximum, max_difference(left[key], right[key]))
                compared = compared and all(near(a, b, TOLERANCES["optimization_absolute"],
                                                  TOLERANCES["optimization_relative"])
                                            for a, b in zip(left[key], right[key]))
    return {"runs": runs, "maximum_O0_O2_difference": maximum,
            "two_optimization_receipts_present": len(runs) >= 2,
            "passed": compared and all(run["passed"] for run in runs)}


def verify(manifest: dict) -> dict:
    required = ("harmonic", "long_harmonic", "quartic", "reversal",
                "gradients", "optimization_pairs")
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ValueError(f"manifest is missing {', '.join(missing)}")
    checks = {
        "harmonic": analyze_harmonic(manifest["harmonic"]),
        "long_harmonic": analyze_long_harmonic(manifest["long_harmonic"]),
        "quartic": analyze_nonlinear(manifest["quartic"], "quartic"),
        "reversal": analyze_reversal(manifest["reversal"]),
        "gradients": analyze_gradient_optimizations(manifest["gradients"]),
        "optimization": {"pairs": [analyze_optimization(pair)
                                     for pair in manifest["optimization_pairs"]]},
    }
    checks["optimization"]["passed"] = (bool(checks["optimization"]["pairs"])
                                         and all(pair["passed"] for pair
                                                 in checks["optimization"]["pairs"]))
    if "double_well" in manifest:
        checks["double_well"] = analyze_nonlinear(manifest["double_well"], "double_well")
    if "quartic_changed" in manifest:
        checks["quartic_changed"] = analyze_nonlinear(manifest["quartic_changed"], "quartic_changed")
        checks["coupling_variation"] = analyze_coupling_variation(manifest["quartic"], manifest["quartic_changed"])
    return {"tolerances": TOLERANCES, "checks": checks, "method_references": SOURCES,
            "finite_difference_sweep": finite_difference_sweep(),
            "passed": all(check["passed"] for check in checks.values())}


def write_result(result: dict, output: str | None) -> None:
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(encoded)
    else:
        print(encoded, end="")


def export_reference(model: str, step: float, time: float, output: str) -> None:
    if not math.isfinite(step) or step <= 0 or not math.isfinite(time) or time <= 0:
        raise ValueError("reference step and time must be positive finite numbers")
    ratio = time/step
    if not math.isfinite(ratio) or ratio > 1_000_000:
        raise ValueError("reference export is limited to one million steps")
    count = round(ratio)
    if abs(count*step-time) > 1e-12:
        raise ValueError("reference time must be an integer number of steps")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("step", "time", "q_x", "q_y", "p_x", "p_y", "energy"))
        state = INITIAL
        for n in range(count+1):
            writer.writerow((n, *(format(v, ".17g") for v in
                                  (n*step, *state, energy(model, state)))))
            if n < count:
                state = rk4_step(model, state, step)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    calibration_parser = subparsers.add_parser("calibrate")
    calibration_parser.add_argument("--output")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("manifest")
    verify_parser.add_argument("--output")
    reference_parser = subparsers.add_parser("reference")
    reference_parser.add_argument("model", choices=("harmonic", "quartic", "double_well", "quartic_changed"))
    reference_parser.add_argument("--step", type=float, default=REFERENCE_STEPS[-1])
    reference_parser.add_argument("--time", type=float, default=FINAL_TIME)
    reference_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "reference":
            export_reference(args.model, args.step, args.time, args.output)
            return 0
        if args.command == "calibrate":
            result = calibration()
            passed = all(reference["passed"] for reference in result["rk4_references"].values())
            result["passed"] = passed
        else:
            result = verify(json.loads(Path(args.manifest).read_text()))
            passed = result["passed"]
        write_result(result, args.output)
        return 0 if passed else 1
    except (ValueError, KeyError, OSError, ZeroDivisionError) as error:
        write_result({"passed": False, "error": str(error)}, args.output)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
