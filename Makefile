install:
	python setup.py install

uninstall:
	pip uninstall blackhole

travis:
	install
	easy_install nose