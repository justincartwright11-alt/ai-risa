# test_stderr.py
import sys
print("STDOUT_OK")
print("STDERR_OK", file=sys.stderr)
sys.stdout.flush()
sys.stderr.flush()
