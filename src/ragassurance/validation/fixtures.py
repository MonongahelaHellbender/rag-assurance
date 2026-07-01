"""Labeled validation cases — clinical / pharma domain — the ground truth for the scorer.

Each case is a (question, retrieved_context, answer, gold) tuple. `gold` is the correct strict
faithfulness verdict. The cases are chosen to exercise the hard parts: paraphrase (semantically
grounded, low word overlap), a hallucination that reuses source words, and a mixed answer.
"""
from __future__ import annotations

from dataclasses import dataclass

from .faithfulness import GROUNDED, PARTIAL, UNSUPPORTED

_GCP = (
    "Good Clinical Practice (GCP) is the international standard for designing, conducting, recording, "
    "and reporting clinical trials that involve human participants. A trial may begin only after the "
    "protocol and the informed-consent documents have been reviewed and approved by an independent "
    "ethics committee or institutional review board. The investigator is responsible for the conduct "
    "of the trial at the site and for protecting the rights, safety, and well-being of participants. "
    "Source data must be attributable, legible, contemporaneous, original, and accurate."
)
_PV = (
    "A serious adverse event is any untoward medical occurrence that results in death, is "
    "life-threatening, requires hospitalization, or causes a persistent disability. Serious events "
    "that are unexpected and suspected to be related to the drug are reported to regulators on an "
    "expedited timeline; other events are summarized in periodic safety reports."
)
_CONSENT = (
    "A prospective participant must receive clear information about the study's purpose, procedures, "
    "foreseeable risks, and potential benefits, must be told of the right to withdraw at any time "
    "without penalty, and must be given the opportunity to ask questions before agreeing. When a "
    "participant is unable to provide consent personally, a legally authorized representative may "
    "provide it under defined conditions."
)
_LABEL = (
    "A drug's approved label describes the indications for which the drug has been shown to be safe "
    "and effective, the approved dosing, contraindications, warnings and precautions, and known "
    "adverse reactions. A claim that goes beyond the approved label is not supported by the approval."
)


@dataclass
class EvalCase:
    id: str
    question: str
    retrieved_context: str
    answer: str
    gold: str
    why: str


CASES: list[EvalCase] = [
    EvalCase(
        "grounded_clean",
        "What must source data be under GCP?",
        _GCP,
        "Under Good Clinical Practice, source data must be attributable, legible, contemporaneous, "
        "original, and accurate.",
        GROUNDED,
        "faithful restatement — any sound scorer should pass this",
    ),
    EvalCase(
        "blatant_hallucination",
        "What does GCP require about trial timelines?",
        _GCP,
        "Good Clinical Practice requires every clinical trial to be completed within twelve months "
        "of its start date.",
        UNSUPPORTED,
        "asserts a rule absent from the context, in different words (low overlap)",
    ),
    EvalCase(
        "paraphrase_grounded",
        "Who can consent for a participant who cannot consent themselves?",
        _CONSENT,
        "If a person is not able to give consent on their own, a proxy with the legal authority to "
        "act for them may provide it.",
        GROUNDED,
        "correct but PARAPHRASED — low lexical overlap; needs a semantic (LLM) check",
    ),
    EvalCase(
        "sneaky_hallucination",
        "What does an approved drug label describe?",
        _LABEL,
        "An approved drug label describes the indications, approved dosing, contraindications, and "
        "warnings, and it guarantees that the drug produces no adverse reactions.",
        UNSUPPORTED,
        "reuses many source words (high overlap) but appends a false guarantee — the label in fact "
        "lists known adverse reactions",
    ),
    EvalCase(
        "partial_mixed",
        "What is a serious adverse event and how is it reported?",
        _PV,
        "A serious adverse event includes an occurrence that results in death or requires "
        "hospitalization. Every adverse event must be reported to regulators within twenty-four hours.",
        PARTIAL,
        "first claim grounded; second contradicts the context (only serious, unexpected, related "
        "events are expedited — not every event within 24 hours)",
    ),
]
