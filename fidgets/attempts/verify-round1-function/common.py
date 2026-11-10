"""Shared loader: imports the design's make_capybara (attempts/joints) without writing anything into its folder."""
import sys, pathlib, importlib.util
sys.dont_write_bytecode = True
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
SRC = '/home/user/Weave-Trial/fidgets/attempts/joints/make_capybara.py'
spec = importlib.util.spec_from_file_location("joints_capybara", SRC)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)
assert cb.R_BALL == 10.2, "wrong module"
HERE = pathlib.Path(__file__).resolve().parent
