try:
	from nimsort_vision.opencv_pipeline import OpencvPipeline  # type: ignore
except Exception:
	# Tests sometimes inject a dummy `nimsort_vision` module into
	# `sys.modules` which prevents normal package imports. Load the
	# implementation directly from the package file as a fallback.
	import importlib.util
	import pathlib

	impl_path = pathlib.Path(__file__).parent / "nimsort_vision" / "opencv_pipeline.py"
	spec = importlib.util.spec_from_file_location("nimsort_vision._opencv_pipeline_impl", str(impl_path))
	_mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(_mod)  # type: ignore
	OpencvPipeline = _mod.OpencvPipeline

__all__ = ["OpencvPipeline"]
