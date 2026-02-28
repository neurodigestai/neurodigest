"""Keyword lists for hard filtering and neuroscience relevance scoring."""

# ------------------------------------------------------------------ #
# Hard Rejection Keywords (case-insensitive match)
# ------------------------------------------------------------------ #

# Job / Advertisement
JOB_KEYWORDS = [
    "phd position",
    "postdoc",
    "hiring",
    "we are recruiting",
    "job opening",
    "faculty position",
    "apply now",
    "internship",
    "career opportunity",
]

# Conference Logistics
CONFERENCE_KEYWORDS = [
    "registration open",
    "submission deadline",
    "early bird fee",
    "call for papers",
    "deadline extended",
    "workshop registration",
    "conference venue",
]

# Non-Relevant ML Topics
IRRELEVANT_ML_KEYWORDS = [
    "image classification dataset",
    "imagenet benchmark",
    "speech recognition benchmark",
    "advertising recommendation",
    "cryptocurrency prediction",
    "stock market prediction",
    "marketing analytics",
    "customer segmentation",
    "self-driving dataset",
]

REJECTION_KEYWORDS: list[str] = (
    JOB_KEYWORDS + CONFERENCE_KEYWORDS + IRRELEVANT_ML_KEYWORDS
)


# ------------------------------------------------------------------ #
# Neuroscience Relevance Score (NRS) keywords
# ------------------------------------------------------------------ #

# Strong neuro indicators → +3 each
STRONG_NEURO: list[tuple[str, int]] = [
    ("neuron", 3),
    ("spiking", 3),
    ("spike train", 3),
    ("hippocampus", 3),
    ("cortex", 3),
    ("cortical", 3),
    ("synapse", 3),
    ("synaptic", 3),
    ("eeg", 3),
    ("meg", 3),
    ("fmri", 3),
    ("calcium imaging", 3),
    ("brain activity", 3),
    ("brain signals", 3),
    ("bci", 3),
    ("brain-computer interface", 3),
    ("neural decoding", 3),
    ("place cells", 3),
    ("grid cells", 3),
    ("connectome", 3),
]

# Neuro-AI indicators → +2 each
NEURO_AI: list[tuple[str, int]] = [
    ("predictive coding", 2),
    ("neuromorphic", 2),
    ("spiking neural network", 2),
    ("hebbian learning", 2),
    ("biologically inspired learning", 2),
    ("cognitive model", 2),
    ("working memory model", 2),
    ("decision making brain", 2),
    ("perception model", 2),
    ("computational psychiatry", 2),
]

# General brain science → +1 each
GENERAL_BRAIN: list[tuple[str, int]] = [
    ("behavior", 1),
    ("learning", 1),
    ("memory", 1),
    ("attention", 1),
    ("motor control", 1),
    ("visual cortex", 1),
    ("sensory processing", 1),
]

# Combined list for scoring
ALL_NRS_KEYWORDS: list[tuple[str, int]] = (
    STRONG_NEURO + NEURO_AI + GENERAL_BRAIN
)
