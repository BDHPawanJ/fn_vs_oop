"""
Root conftest.py — sets up sys.path for all three test suites.

  core_concepts/tests    imports from core_concepts/functional + oop
  advanced_concepts/tests imports from advanced_concepts/functional + oop
  shared_lib/tests       imports from shared_lib/functional + oop

Each test file sets its own sys.path.insert(0, "../../..") pointing
at its own package root, so the root conftest only needs to add the
project root itself for advanced_concepts imports.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
