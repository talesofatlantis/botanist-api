import math
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
# Synonym map — direct word replacements
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
    "silent":   ["still", "absent", "hollow", "muted"],
    "loud":     ["resonant", "saturated", "dense", "overwhelming"],
    "empty":    ["hollow", "absent", "void", "bare"],
    "full":     ["saturated", "dense", "heavy", "complete"],
    # common everyday words
    "dog":      ["creature", "shadow", "form", "presence"],
    "cat":      ["shadow", "form", "trace", "presence"],
    "man":      ["figure", "silhouette", "form", "presence"],
    "woman":    ["figure", "silhouette", "form", "presence"],
    "child":    ["figure", "echo", "trace", "form"],
    "grass":    ["growth", "field", "expanse", "overgrowth"],
    "field":    ["expanse", "void", "plain", "surface"],
    "sun":      ["light", "heat", "glow", "brightness"],
    "moon":     ["reflection", "pale disc", "shadow", "coldness"],
    "star":     ["point", "signal", "distance", "absence"],
    "fire":     ["ember", "heat", "trace", "glow"],
    "smoke":    ["residue", "drift", "vapour", "trace"],
    "stone":    ["mass", "weight", "form", "structure"],
    "wall":     ["boundary", "surface", "edge", "barrier"],
    "floor":    ["surface", "ground", "plane", "base"],
    "hand":     ["trace", "form", "presence", "touch"],
    "eye":      ["aperture", "void", "opening", "depth"],
    "face":     ["surface", "form", "membrane", "presence"],
    "body":     ["form", "mass", "structure", "vessel"],
    "city":     ["structure", "expanse", "labyrinth", "density"],
    "street":   ["passage", "line", "threshold", "trace"],
    "car":      ["form", "vessel", "shell", "mass"],
    "book":     ["vessel", "trace", "structure", "surface"],
    "table":    ["surface", "plane", "structure", "form"],
    "chair":    ["form", "structure", "shell", "presence"],
    "bed":      ["surface", "enclosure", "stillness", "warmth"],
    "food":     ["substance", "residue", "matter", "form"],
    "air":      ["expanse", "void", "absence", "current"],
    "earth":    ["mass", "depth", "surface", "weight"],
    "sea":      ["expanse", "depth", "current", "void"],
    "river":    ["current", "passage", "flow", "drift"],
    "mountain": ["mass", "form", "weight", "structure"],
    "path":     ["trace", "line", "passage", "threshold"],
    "bridge":   ["threshold", "passage", "connection", "span"],
    "flower":   ["form", "bloom", "trace", "opening"],
    "leaf":     ["fragment", "trace", "surface", "form"],
    "branch":   ["extension", "trace", "form", "arm"],
    "root":     ["depth", "trace", "anchor", "base"],
    "shadow":   ["absence", "trace", "projection", "void"],
    "colour":   ["frequency", "signal", "wavelength", "hue"],
    "color":    ["frequency", "signal", "wavelength", "hue"],
    "music":    ["frequency", "resonance", "vibration", "signal"],
    "voice":    ["frequency", "resonance", "trace", "signal"],
    "words":    ["signals", "traces", "residue", "echoes"],
    "word":     ["signal", "trace", "residue", "echo"],
    "name":     ["signal", "trace", "mark", "echo"],
    "place":    ["coordinate", "threshold", "point", "location"],
    "home":     ["vessel", "shell", "enclosure", "origin"],
    "love":     ["resonance", "gravity", "trace", "weight"],
    "fear":     ["absence", "weight", "static", "distance"],
    "dream":    ["residue", "echo", "signal", "collapse"],
    "lay":      ["rest", "collapse", "settle", "dissolve"],
    "laying":   ["resting", "collapsing", "settling", "dissolving"],
    "lying":    ["resting", "collapsing", "settling", "dissolving"],
    "walking":  ["drifting", "passing", "tracing", "moving"],
    "walk":     ["drift", "pass", "trace", "move"],
    "run":      ["escape", "trace", "pass", "dissolve"],
    "running":  ["escaping", "tracing", "passing", "dissolving"],
    "standing": ["suspended", "fixed", "present", "remaining"],
    "sitting":  ["suspended", "fixed", "present", "remaining"],
    "looking":  ["scanning", "tracing", "searching", "observing"],
    "seeing":   ["tracing", "receiving", "observing", "scanning"],
    "hearing":  ["receiving", "tracing", "sensing", "detecting"],
    "feeling":  ["sensing", "receiving", "tracing", "detecting"],
    "thinking": ["processing", "drifting", "tracing", "collapsing"],
    "big":      ["vast", "expanded", "overwhelming", "dense"],
    "little":   ["faint", "diminished", "reduced", "barely"],
    "new":      ["emergent", "unformed", "threshold", "beginning"],
    "good":     ["resonant", "aligned", "stable", "present"],
    "bad":      ["fractured", "misaligned", "scattered", "absent"],
    "beautiful":["resonant", "coherent", "radiant", "luminous"],
    "quiet":    ["still", "absent", "hollow", "muted"],
    "slow":     ["drawn", "extended", "gradual", "fading"],
    "fast":     ["sudden", "collapsed", "brief", "sharp"],
    "open":     ["exposed", "unbound", "expanded", "threshold"],
    "closed":   ["sealed", "contained", "bounded", "compressed"],
}

# ---------------------------------------------------------------------------
# Quantum-derived descriptors — injected when no synonym exists
# These are grouped by measurement basis (00, 01, 10, 11)
# ---------------------------------------------------------------------------
QUANTUM_MODIFIERS = [
    # 00 — decoherence / erosion
    ["dissolving", "eroded", "fractured", "scattered", "decayed",
     "fading", "hollow", "worn", "collapsed", "bleached"],
    # 01 — superposition / multiplicity
    ["superposed", "branching", "parallel", "overlapping", "entangled",
     "suspended", "uncertain", "doubled", "bifurcating", "spectral"],
    # 10 — measurement / collapse
    ["collapsed", "fixed", "observed", "crystallised", "determined",
     "resolved", "reduced", "singular", "pinned", "locked"],
    # 11 — interference / distortion
    ["phase-shifted", "distorted", "refracted", "inverted", "displaced",
     "warped", "interfering", "oscillating", "diffuse", "scattered"],
]

# Words we skip entirely (articles, prepositions, conjunctions)
SKIP_WORDS = {"a", "an", "the", "in", "on", "at", "to", "of", "and",
              "or", "but", "for", "with", "by", "from", "as", "is",
              "was", "are", "were", "be", "been", "it", "its", "this",
              "that", "i", "my", "your", "his", "her", "our", "their"}


class PromptRequest(BaseModel):
    prompt: str


class WordTrace(BaseModel):
    original: str
    output: str
    bit: str
    angle: float
    operation: str  # "skip" | "synonym" | "modifier" | "unchanged"
    qubit: int


class TransformResponse(BaseModel):
    original: str
    mutated: str
    bitstring: str
    qubits_used: int
    mutations: int
    trace: list[WordTrace]
    angles: list[float]


def build_circuit(prompt: str) -> tuple[QuantumCircuit, int, list[float]]:
    """Encode prompt characters as qubit rotation angles."""
    n = min(len(prompt.replace(" ", "")), 16)
    n = max(n, 4)
    chars = [c for c in prompt if c.strip()][:n]
    angles = []

    qc = QuantumCircuit(n, n)
    for i, char in enumerate(chars):
        angle = (ord(char) / 128) * math.pi
        angles.append(angle)
        qc.h(i)
        qc.ry(angle, i)
        if i > 0:
            qc.cx(i - 1, i)
    qc.measure(range(n), range(n))
    return qc, n, angles


def mutate_prompt(prompt: str, bitstring: str, angles: list[float]) -> tuple[str, int, list[WordTrace]]:
    """
    Use measurement bitstring + qubit angles to transform every
    meaningful word in the prompt.

    Strategy:
      - Skip articles/prepositions (SKIP_WORDS)
      - If bit=1 AND word is in SYNONYMS → replace with synonym
      - If bit=1 AND word NOT in SYNONYMS → inject a quantum modifier
        before the word, chosen from QUANTUM_MODIFIERS using the
        next two bits as a 2-bit index (00–11 → one of 4 groups)
      - If bit=0 → keep the word unchanged
    """
    words = prompt.split()
    result = []
    mutations = 0
    trace: list[WordTrace] = []
    qubit_idx = 0

    for i, word in enumerate(words):
        bit_char = bitstring[i % len(bitstring)]
        bit = int(bit_char)
        angle = angles[i % len(angles)] if angles else 1.0
        punct = ""
        clean = word.lower()
        if clean and clean[-1] in ".,;:!?":
            punct = clean[-1]
            clean = clean[:-1]

        # Always keep skip words unchanged
        if clean in SKIP_WORDS:
            result.append(word)
            trace.append(WordTrace(
                original=word,
                output=word,
                bit=bit_char,
                angle=round(angle, 4),
                operation="skip",
                qubit=qubit_idx % 16,
            ))
            qubit_idx += 1
            continue

        if bit == 1:
            if clean in SYNONYMS:
                # Direct synonym replacement
                options = SYNONYMS[clean]
                idx_bits = bitstring[(i + 1) % len(bitstring)] + bitstring[(i + 2) % len(bitstring)]
                idx = int(idx_bits, 2) % len(options)
                output = options[idx] + punct
                result.append(output)
                mutations += 1
                trace.append(WordTrace(
                    original=word,
                    output=output,
                    bit=bit_char,
                    angle=round(angle, 4),
                    operation="synonym",
                    qubit=qubit_idx % 16,
                ))
            else:
                # Inject quantum modifier derived from the 2-bit group index
                group_bits = bitstring[(i + 1) % len(bitstring)] + bitstring[(i + 2) % len(bitstring)]
                group = int(group_bits, 2) % len(QUANTUM_MODIFIERS)
                mod_idx = int((angle / math.pi) * len(QUANTUM_MODIFIERS[group])) % len(QUANTUM_MODIFIERS[group])
                modifier = QUANTUM_MODIFIERS[group][mod_idx]
                output = modifier + " " + word
                result.append(output)
                mutations += 1
                trace.append(WordTrace(
                    original=word,
                    output=output,
                    bit=bit_char,
                    angle=round(angle, 4),
                    operation="modifier",
                    qubit=qubit_idx % 16,
                ))
        else:
            result.append(word)
            trace.append(WordTrace(
                original=word,
                output=word,
                bit=bit_char,
                angle=round(angle, 4),
                operation="unchanged",
                qubit=qubit_idx % 16,
            ))

        qubit_idx += 1

    return " ".join(result), mutations, trace


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transform", response_model=TransformResponse)
def transform(req: PromptRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    qc, n, angles = build_circuit(req.prompt)
    sim = AerSimulator()
    result = sim.run(qc, shots=1).result()
    bitstring = list(result.get_counts())[0].replace(" ", "")

    mutated, mutations, trace = mutate_prompt(req.prompt, bitstring, angles)

    return TransformResponse(
        original=req.prompt,
        mutated=mutated,
        bitstring=bitstring,
        qubits_used=n,
        mutations=mutations,
        trace=trace,
        angles=[round(a, 4) for a in angles],
    )
