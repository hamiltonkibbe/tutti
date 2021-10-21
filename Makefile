
dist:
	poetry build

publish: dist
	poetry publish

test:
	poetry run pytest

typecheck:
	poetry run mypy

doc-html:
	$(MAKE) -C docs html

doc-clean:
	@$(MAKE) -C docs clean

doc-autobuild:
	poetry run sphinx-autobuild docs docs/_build/html



clean: doc-clean
	@find . -name .mypy_cache -type d -exec rm -r {} +
	@find . -name .pytest_cache -type d -exec rm -r {} +
	@find . -name __pycache__ -type d -exec rm -r {} +

dist-clean: clean
	@find . -name dist -type d -exec rm -r {} +
