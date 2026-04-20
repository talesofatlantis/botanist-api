import math
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

app = FastAPI(title="Botanist Qiskit Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Synonym map — expanded to cover common memory language
# ---------------------------------------------------------------------------
SYNONYMS: dict[str, list[str]] = {
    "light":    ["glow", "luminescence", "haze", "shimmer"],
    "dark":     ["shadow", "void", "absence", "depth"],
    "darkness": ["shadow", "void", "absence", "depth"],
    "garden":   ["overgrowth", "ruin", "thicket", "bloom"],
    "memory":   ["residue", "echo", "trace", "imprint"],
    "sound":    ["frequency", "vibration", "resonance", "noise"],
    "old":      ["decayed", "ancient", "eroded", "worn"],
    "smell":    ["scent", "vapour", "trace", "drift"],
    "house":    ["structure", "ruin", "vessel", "shell"],
    "room":     ["chamber", "void", "enclosure", "space"],
    "water":    ["current", "stillness", "reflection", "depth"],
    "rain":     ["vapour", "descent", "static", "weight"],
    "sky":      ["expanse", "membrane", "canopy", "void"],
    "forest":   ["overgrowth", "labyrinth", "thicket", "shade"],
    "tree":     ["form", "silhouette", "structure", "growth"],
    "road":     ["passage", "line", "threshold", "trace"],
    "door":     ["threshold", "opening", "boundary", "frame"],
    "window":   ["aperture", "boundary", "membrane", "opening"],
    "white":    ["blank", "bleached", "pale", "erased"],
    "black":    ["void", "absence", "depth", "shadow"],
    "red":      ["ember", "stain", "rust", "signal"],
    "blue":     ["coldness", "distance", "depth", "still"],
    "green":    ["growth", "decay", "moss", "overgrowth"],
    "yellow":   ["faded", "amber", "dust", "age"],
    "cold":     ["stillness", "absence", "distance", "frost"],
    "warm":     ["embers", "glow", "residue", "heat"],
    "summer":   ["haze", "bloom", "saturation", "weight"],
    "winter":   ["absence", "stillness", "frost", "erosion"],
    "autumn":   ["decay", "residue", "descent", "ochre"],
    "spring":   ["emergence", "threshold", "bloom", "beginning"],
    "morning":  ["threshold", "pale light", "onset", "stillness"],
    "evening":  ["descent", "amber", "fading", "closing"],
    "night":    ["absence", "depth", "silence", "shadow"],
    "time":     ["erosion", "residue", "drift", "collapse"],
    "long":     ["extended", "drawn", "stretched", "enduring"],
    "small":    ["faint", "diminished", "reduced", "barely"],
    "large":    ["vast", "expanded", "overwhelming", "open"],
    "far":      ["distant", "beyond", "unreachable", "faint"],
    "near":     ["close", "adjacent", "within reach", "present"],
    "alone":    ["isolated", "singular", "absent", "still"],
    "together": ["overlapping", "merged", "entangled", "shared"],
    "lost":     ["dissolved", "erased", "untethered", "absent"],
    "found":    ["returned", "resurfaced", "recovered", "present"],
    "broken":   ["fractured", "dissolved", "collapsed", "worn"],
    "silent":   ["still", "absent", "hollow", "muted"],
    "loud":     ["resonant", "saturated", "dense", "overwhelming"],
    "empty":    ["hollow", "absent", "void", "bare"],
    "full":     ["saturated", "dense", "heavy", "complete"],
}


class PromptRequest(BaseModel):
    prompt: str


class TransformResponse(BaseModel):
    original: str
    mutated: str
    bitstring: str
    qubits_used: int
    mutations: int


def build_circuit(prompt: str) -> tuple[QuantumCircuit, int]:
    """Encode prompt characters as qubit rotation angles."""
    n = min(len(prompt.replace(" ", "")), 16)
    n = max(n, 4)
    chars = [c for c in prompt if c.strip()][:n]

    qc = QuantumCircuit(n, n)
    for i, char in enumerate(chars):
        angle = (ord(char) / 128) * math.pi
        qc.h(i)
        qc.ry(angle, i)
        # Entangle neighbouring qubits for cross-word interference
        if i > 0:
            qc.cx(i - 1, i)
    qc.measure(range(n), range(n))
    return qc, n


def mutate_prompt(prompt: str, bitstring: str) -> tuple[str, int]:
    """Use measurement bitstring to stochastically mutate the prompt."""
    words = prompt.split()
    result = []
    mutations = 0

    for i, word in enumerate(words):
        bit = int(bitstring[i % len(bitstring)])
        # Strip punctuation for lookup, preserve it after
        punct = ""
        clean = word.lower()
        if clean and clean[-1] in ".,;:!?":
            punct = clean[-1]
            clean = clean[:-1]

        if bit == 1 and clean in SYNONYMS:
            options = SYNONYMS[clean]
            # Use two bits to pick from the synonym list deterministically
            idx_bits = bitstring[(i + 1) % len(bitstring)] + bitstring[(i + 2) % len(bitstring)]
            idx = int(idx_bits, 2) % len(options)
            result.append(options[idx] + punct)
            mutations += 1
        else:
            result.append(word)

    return " ".join(result), mutations


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transform", response_model=TransformResponse)
def transform(req: PromptRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    qc, n = build_circuit(req.prompt)
    sim = AerSimulator()
    job = sim.run(qc, shots=1)
    result = job.result()
    bitstring = list(result.get_counts())[0].replace(" ", "")

    mutated, mutations = mutate_prompt(req.prompt, bitstring)

    return TransformResponse(
        original=req.prompt,
        mutated=mutated,
        bitstring=bitstring,
        qubits_used=n,
        mutations=mutations,
    )
