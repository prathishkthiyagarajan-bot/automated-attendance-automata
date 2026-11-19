// Interactive SVG Finite Automata (DFA) State Transition Diagram
import React, { useState } from 'https://esm.sh/react@18.2.0';

export const DfaDiagram = ({ activeState = null, onSelectState = null }) => {
    const [selectedState, setSelectedState] = useState(activeState || 'S0');

    // States layout coordinates in SVG viewBox (0 0 950 520)
    const states = [
        { id: 'S0', name: 'Not Marked', x: 120, y: 260, color: '#9ca3af', border: '#4b5563', isInitial: true, isFinal: false },
        { id: 'S1', name: 'Present', x: 420, y: 110, color: '#10b981', border: '#059669', isInitial: false, isFinal: false },
        { id: 'S2', name: 'Absent', x: 420, y: 410, color: '#ef4444', border: '#dc2626', isInitial: false, isFinal: false },
        { id: 'S3', name: 'Late', x: 420, y: 260, color: '#f59e0b', border: '#d97706', isInitial: false, isFinal: false },
        { id: 'S4', name: 'Finalized', x: 780, y: 260, color: '#3b82f6', border: '#2563eb', isInitial: false, isFinal: true }
    ];

    const stateDetails = {
        'S0': {
            title: 'S0: Not Marked (Initial State q0)',
            desc: 'Initial session state when student attendance has not yet been taken.',
            allowedInputs: ['P -> S1 (Present)', 'A -> S2 (Absent)', 'L -> S3 (Late)'],
            rejectedInputs: ['F (Finalize): REJECTED - Cannot finalize unmarked attendance!'],
            roles: 'Faculty, Administrator'
        },
        'S1': {
            title: 'S1: Present State',
            desc: 'Student is marked Present for this class session.',
            allowedInputs: ['P -> S1 (Idempotent)', 'A -> S2 (Correction)', 'L -> S3 (Correction)', 'F -> S4 (Finalize)'],
            rejectedInputs: ['R: Forbidden for faculty (Admin only)'],
            roles: 'Faculty, Administrator'
        },
        'S2': {
            title: 'S2: Absent State',
            desc: 'Student is recorded as Absent for this class session.',
            allowedInputs: ['A -> S2 (Idempotent)', 'P -> S1 (Correction)', 'L -> S3 (Correction)', 'F -> S4 (Finalize)'],
            rejectedInputs: ['R: Forbidden for faculty (Admin only)'],
            roles: 'Faculty, Administrator'
        },
        'S3': {
            title: 'S3: Late State',
            desc: 'Student arrived late to class but is present with late penalty flag.',
            allowedInputs: ['L -> S3 (Idempotent)', 'P -> S1 (Correction)', 'A -> S2 (Correction)', 'F -> S4 (Finalize)'],
            rejectedInputs: ['R: Forbidden for faculty (Admin only)'],
            roles: 'Faculty, Administrator'
        },
        'S4': {
            title: 'S4: Attendance Finalized (Accepting/Terminal State F)',
            desc: 'Session attendance has been approved and permanently locked. Record is immutable.',
            allowedInputs: ['R -> S0 (Authorized Admin Reset with audit reason only)'],
            rejectedInputs: ['P: REJECTED (Record locked)', 'A: REJECTED (Record locked)', 'L: REJECTED (Record locked)', 'F: REJECTED (Already finalized)'],
            roles: 'Administrator Only (via Symbol R)'
        }
    };

    const handleNodeClick = (id) => {
        setSelectedState(id);
        if (onSelectState) onSelectState(id);
    };

    const currInfo = stateDetails[selectedState] || stateDetails['S0'];
    const active = activeState || selectedState;

    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-6 overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-700 gap-4">
                <div>
                    <h3 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <span className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400">
                            <i className="fa-solid fa-diagram-project"></i>
                        </span>
                        Deterministic Finite Automaton (DFA) State Diagram
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Formally defined 5-tuple: <span className="font-mono text-blue-600 dark:text-blue-400 font-semibold">M = (Q, Σ, δ, q0, F)</span>
                    </p>
                </div>
                <div className="flex items-center gap-3 text-xs font-medium">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span> S0: Not Marked
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> S1: Present
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> S2: Absent
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> S3: Late
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400">
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-500 ring-2 ring-blue-300"></span> S4: Finalized (F)
                    </span>
                </div>
            </div>

            {/* SVG Canvas */}
            <div className="relative my-4 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-800 overflow-x-auto">
                <svg viewBox="0 0 950 520" className="w-full min-w-[750px] h-[400px]">
                    <defs>
                        {/* Arrowhead marker for normal transitions */}
                        <marker id="arrow" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                        </marker>
                        {/* Arrowhead for Finalization transitions */}
                        <marker id="arrow-blue" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
                        </marker>
                        {/* Arrowhead for Admin Reset */}
                        <marker id="arrow-purple" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6" />
                        </marker>
                    </defs>

                    {/* Start arrow into S0 */}
                    <g>
                        <line x1="30" y1="260" x2="80" y2="260" stroke="#475569" strokeWidth="2.5" markerEnd="url(#arrow)" />
                        <text x="35" y="248" fill="#64748b" fontSize="12" fontWeight="600">Start</text>
                    </g>

                    {/* Transitions from S0 to S1, S3, S2 */}
                    <path d="M 155 240 Q 250 140 375 125" fill="none" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrow)" />
                    <text x="245" y="170" fill="#059669" fontSize="13" fontWeight="bold">P (Present)</text>

                    <path d="M 165 260 L 375 260" fill="none" stroke="#f59e0b" strokeWidth="2" markerEnd="url(#arrow)" />
                    <text x="250" y="252" fill="#d97706" fontSize="13" fontWeight="bold">L (Late)</text>

                    <path d="M 155 280 Q 250 380 375 395" fill="none" stroke="#ef4444" strokeWidth="2" markerEnd="url(#arrow)" />
                    <text x="245" y="355" fill="#dc2626" fontSize="13" fontWeight="bold">A (Absent)</text>

                    {/* Intermediate bi-directional corrections */}
                    {/* S1 <-> S3 */}
                    <path d="M 410 155 L 410 215" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow)" />
                    <text x="390" y="190" fill="#64748b" fontSize="11" fontWeight="600">L</text>
                    <path d="M 430 215 L 430 155" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow)" />
                    <text x="436" y="190" fill="#64748b" fontSize="11" fontWeight="600">P</text>

                    {/* S3 <-> S2 */}
                    <path d="M 410 305 L 410 365" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow)" />
                    <text x="390" y="340" fill="#64748b" fontSize="11" fontWeight="600">A</text>
                    <path d="M 430 365 L 430 305" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow)" />
                    <text x="436" y="340" fill="#64748b" fontSize="11" fontWeight="600">L</text>

                    {/* S1 <-> S2 curved back */}
                    <path d="M 390 135 C 320 200 320 320 390 385" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="4,4" markerEnd="url(#arrow)" />
                    <text x="315" y="260" fill="#64748b" fontSize="11" fontWeight="bold">P / A</text>

                    {/* Finalization Transitions: S1, S3, S2 -> S4 */}
                    <path d="M 465 125 Q 600 140 735 240" fill="none" stroke="#3b82f6" strokeWidth="2.5" markerEnd="url(#arrow-blue)" />
                    <text x="590" y="170" fill="#2563eb" fontSize="13" fontWeight="bold">F (Finalize)</text>

                    <path d="M 465 260 L 735 260" fill="none" stroke="#3b82f6" strokeWidth="2.5" markerEnd="url(#arrow-blue)" />
                    <text x="580" y="252" fill="#2563eb" fontSize="13" fontWeight="bold">F (Finalize)</text>

                    <path d="M 465 395 Q 600 380 735 280" fill="none" stroke="#3b82f6" strokeWidth="2.5" markerEnd="url(#arrow-blue)" />
                    <text x="590" y="355" fill="#2563eb" fontSize="13" fontWeight="bold">F (Finalize)</text>

                    {/* Authorized Admin Reset Transition: S4 -> S0 (Curved over bottom) */}
                    <path d="M 760 305 C 720 490 200 490 140 305" fill="none" stroke="#8b5cf6" strokeWidth="2.5" strokeDasharray="6,4" markerEnd="url(#arrow-purple)" />
                    <text x="440" y="475" fill="#7c3aed" fontSize="13" fontWeight="bold" textAnchor="middle">
                        δ(S4, R) → S0 [Authorized Admin Reset with Audit Trail]
                    </text>

                    {/* Draw Nodes */}
                    {states.map(s => {
                        const isCurrent = (active === s.id);
                        const isClicked = (selectedState === s.id);

                        return (
                            <g
                                key={s.id}
                                className={`dfa-node ${isCurrent ? 'active-state' : ''}`}
                                onClick={() => handleNodeClick(s.id)}
                            >
                                {/* Outer double ring for Accepting/Final state S4 */}
                                {s.isFinal && (
                                    <circle
                                        cx={s.x}
                                        cy={s.y}
                                        r="52"
                                        fill="none"
                                        stroke={s.border}
                                        strokeWidth="2.5"
                                        strokeDasharray={isCurrent ? "none" : "none"}
                                    />
                                )}

                                {/* Main Node Circle */}
                                <circle
                                    cx={s.x}
                                    cy={s.y}
                                    r="44"
                                    fill={isCurrent ? s.color : (isClicked ? s.color + '33' : '#ffffff')}
                                    stroke={s.border}
                                    strokeWidth={isCurrent ? '4' : (isClicked ? '3' : '2')}
                                    className="transition-all duration-200"
                                />

                                {/* State ID */}
                                <text
                                    x={s.x}
                                    y={s.y - 4}
                                    fill={isCurrent ? '#ffffff' : (isClicked ? s.border : '#1e293b')}
                                    fontSize="18"
                                    fontWeight="bold"
                                    textAnchor="middle"
                                    dominantBaseline="middle"
                                >
                                    {s.id}
                                </text>

                                {/* State Name Subtitle */}
                                <text
                                    x={s.x}
                                    y={s.y + 16}
                                    fill={isCurrent ? '#f1f5f9' : '#64748b'}
                                    fontSize="11"
                                    fontWeight="600"
                                    textAnchor="middle"
                                    dominantBaseline="middle"
                                >
                                    {s.name}
                                </text>
                            </g>
                        );
                    })}
                </svg>
            </div>

            {/* State Inspector Card */}
            <div className="mt-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        State Inspector (Click any node to inspect)
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                        Selected: {selectedState}
                    </span>
                </div>
                <h4 className="text-base font-bold text-slate-800 dark:text-white">{currInfo.title}</h4>
                <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">{currInfo.desc}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 text-xs">
                    <div className="p-2.5 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40">
                        <span className="font-semibold text-emerald-800 dark:text-emerald-300 block mb-1">
                            <i className="fa-solid fa-check-circle mr-1"></i> Permitted Transitions:
                        </span>
                        <ul className="space-y-0.5 text-emerald-700 dark:text-emerald-400">
                            {currInfo.allowedInputs.map((inp, idx) => <li key={idx}>• {inp}</li>)}
                        </ul>
                    </div>
                    <div className="p-2.5 rounded-lg bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/40">
                        <span className="font-semibold text-rose-800 dark:text-rose-300 block mb-1">
                            <i className="fa-solid fa-ban mr-1"></i> Prohibited / Invalid Transitions:
                        </span>
                        <ul className="space-y-0.5 text-rose-700 dark:text-rose-400">
                            {currInfo.rejectedInputs.map((inp, idx) => <li key={idx}>• {inp}</li>)}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
