"""Closed-loop instrument: a fork of RomanSlack/jev-drone (MIT) with one shared controller,
pluggable manoeuvre sources, seeded course randomisation, and outcome metrics.
Reuses the original's Pilot, Eye, Tactician and question definitions unchanged."""
import os, sys
JD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "third_party", "jev-drone")
JD = os.path.abspath(JD)
if JD not in sys.path: sys.path.insert(0, JD)
