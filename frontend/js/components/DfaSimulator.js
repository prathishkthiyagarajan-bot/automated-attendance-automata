// Interactive DFA Sequence Tester & Automaton Simulator
import React, { useState } from 'https://esm.sh/react@18.2.0';
import { api } from '../api.js';

export const DfaSimulator = ({ onStepChange = null }) => {
    const [initialState, setInitialState] = useState('S0');
    const [sequence, setSequence] = useState(['P', 'F']);
    const [role, setRole] = useState('faculty');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const runSimulation = async (seq = sequence, init = initialState, r = role) => {
        setLoading(true);
        try {
            const data = await api.simulateDfa(init, seq, r);
            if (data.success) {
                setResult(data.simulation);
                if (onStepChange && data.simulation.final_state) {
                    onStepChange(data.simulation.final_state);
                }
            }
        } catch (err) {
            console.error('Simulation error', err);
        } finally {
            setLoading(false);
        }
    };

    const addSymbol = (sym) => {
        const next = [...sequence, sym];
        setSequence(next);
        runSimulation(next, initialState, role);
    };

    const clearSequence = () => {
        setSequence([]);
        runSimulation([], initialState, role);
    };

    const loadPreset = (presetSeq, presetRole = 'faculty', presetInit = 'S0') => {
        setInitialState(presetInit);
        setSequence(presetSeq);
        setRole(presetRole);
        runSimulation(presetSeq, presetInit, presetRole);
    };

    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-700 gap-4">
                <div>
                    <h3 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <span className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400">
                            <i className="fa-solid fa-flask-vial"></i>
                        </span>
                        Interactive DFA Automaton Simulator
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Test input strings against transition function <span className="font-mono text-indigo-600 dark:text-indigo-400 font-semibold">δ(q, σ)</span> to verify acceptance.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">Simulate Role:</label>
                    <select
                        value={role}
                        onChange={(e) => {
                            setRole(e.target.value);
                            runSimulation(sequence, initialState, e.target.value);
                        }}
                        className="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200"
                    >
                        <option value="faculty">Faculty User</option>
                        <option value="admin">Admin User</option>
                        <option value="student">Student User</option>
                    </select>
                </div>
            </div>

            {/* Quick Test Presets */}
            <div className="mt-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block mb-2">
                    Test Scenarios & Presets:
                </span>
                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={() => loadPreset(['P', 'F'], 'faculty')}
                        className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 font-medium text-slate-700 dark:text-slate-300"
                    >
                        ✓ Normal Flow: P → F
                    </button>
                    <button
                        onClick={() => loadPreset(['A', 'L', 'P', 'F'], 'faculty')}
                        className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 font-medium text-slate-700 dark:text-slate-300"
                    >
                        ✓ Corrections: A → L → P → F
                    </button>
                    <button
                        onClick={() => loadPreset(['F'], 'faculty')}
                        className="text-xs px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 font-medium border border-rose-200 dark:border-rose-900"
                    >
                        ✗ Invalid: S0 → F (Premature Finalization)
                    </button>
                    <button
                        onClick={() => loadPreset(['P', 'F', 'A'], 'faculty')}
                        className="text-xs px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 font-medium border border-rose-200 dark:border-rose-900"
                    >
                        ✗ Invalid: P → F → A (Edit Finalized S4)
                    </button>
                    <button
                        onClick={() => loadPreset(['P', 'F', 'R', 'P'], 'admin')}
                        className="text-xs px-3 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-400 font-medium border border-purple-200 dark:border-purple-900"
                    >
                        ✓ Admin Override: P → F → R → P
                    </button>
                </div>
            </div>

            {/* Input Sequence Builder */}
            <div className="mt-5 p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-600 dark:text-slate-300">Input String Σ*:</span>
                        <div className="flex items-center gap-1.5 flex-wrap min-h-[32px] p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-slate-300 dark:border-slate-700 font-mono text-sm">
                            {sequence.length === 0 ? (
                                <span className="text-slate-400 text-xs italic px-2">λ (Empty sequence)</span>
                            ) : (
                                sequence.map((sym, idx) => (
                                    <span
                                        key={idx}
                                        className={`px-2 py-0.5 rounded font-bold text-xs ${
                                            sym === 'P' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300' :
                                            sym === 'A' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300' :
                                            sym === 'L' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300' :
                                            sym === 'F' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300' :
                                            'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300'
                                        }`}
                                    >
                                        {sym}
                                    </span>
                                ))
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={clearSequence}
                            className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
                        >
                            <i className="fa-solid fa-trash-can mr-1"></i> Clear
                        </button>
                        <button
                            onClick={() => runSimulation()}
                            disabled={loading}
                            className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm"
                        >
                            {loading ? <i className="fa-solid fa-spinner fa-spin mr-1"></i> : <i className="fa-solid fa-play mr-1"></i>} Run DFA
                        </button>
                    </div>
                </div>

                {/* Alphabet Buttons */}
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Append Symbol:</span>
                    <button
                        onClick={() => addSymbol('P')}
                        className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold"
                    >
                        + P (Present)
                    </button>
                    <button
                        onClick={() => addSymbol('A')}
                        className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold"
                    >
                        + A (Absent)
                    </button>
                    <button
                        onClick={() => addSymbol('L')}
                        className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold"
                    >
                        + L (Late)
                    </button>
                    <button
                        onClick={() => addSymbol('F')}
                        className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold"
                    >
                        + F (Finalize)
                    </button>
                    <button
                        onClick={() => addSymbol('R')}
                        className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold"
                    >
                        + R (Reset)
                    </button>
                </div>
            </div>

            {/* Trace Output */}
            {result && (
                <div className="mt-5 space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-600 dark:text-slate-300">DFA Result:</span>
                            {result.is_accepted ? (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300">
                                    <i className="fa-solid fa-circle-check"></i> STRING ACCEPTED
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300">
                                    <i className="fa-solid fa-circle-xmark"></i> STRING REJECTED
                                </span>
                            )}
                        </div>
                        <div className="text-xs font-mono text-slate-500 dark:text-slate-400">
                            Final State: <span className="font-bold text-slate-800 dark:text-white">{result.final_state}</span>
                        </div>
                    </div>

                    {/* Step by Step Trace Table */}
                    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-700">
                                <tr>
                                    <th className="px-3 py-2">Step</th>
                                    <th className="px-3 py-2">Input Symbol</th>
                                    <th className="px-3 py-2">Resulting State</th>
                                    <th className="px-3 py-2">Status</th>
                                    <th className="px-3 py-2">Automaton Transition Details</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {result.trace.map((step, idx) => (
                                    <tr key={idx} className={step.valid ? 'bg-white dark:bg-slate-800' : 'bg-rose-50/50 dark:bg-rose-950/20'}>
                                        <td className="px-3 py-2 font-mono text-slate-500">#{step.step}</td>
                                        <td className="px-3 py-2 font-mono font-bold">
                                            {step.input ? (
                                                <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700">
                                                    {step.input}
                                                </span>
                                            ) : (
                                                <span className="text-slate-400">—</span>
                                            )}
                                        </td>
                                        <td className="px-3 py-2 font-mono font-bold">
                                            <span className={`px-2 py-0.5 rounded ${
                                                step.state === 'S1' ? 'badge-s1' :
                                                step.state === 'S2' ? 'badge-s2' :
                                                step.state === 'S3' ? 'badge-s3' :
                                                step.state === 'S4' ? 'badge-s4' : 'badge-s0'
                                            }`}>
                                                {step.state} ({step.state_name})
                                            </span>
                                        </td>
                                        <td className="px-3 py-2">
                                            {step.valid ? (
                                                <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                                                    <i className="fa-solid fa-check"></i> Valid
                                                </span>
                                            ) : (
                                                <span className="text-rose-600 dark:text-rose-400 font-semibold flex items-center gap-1">
                                                    <i className="fa-solid fa-times"></i> Rejected
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-3 py-2 text-slate-600 dark:text-slate-300">
                                            {step.message}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};
