# Included by the repository Makefile. Content deployment never depends on apk.
.PHONY: apk apk-release offline-manifest offline-test offline-native-test offline-browser-test offline-fixture offline-help

offline-help:
	@printf '%s\n' 'make apk                 Build content-free Android debug shell (JDK 17+, SDK 35).' \
	  'make apk-release         Build/sign/verify release shell; signing environment required.' \
	  'make offline-test        Run catalog and service-worker protocol regressions.' \
	  'make offline-native-test Run the actual streaming downloader on the host JVM.' \
	  'make offline-browser-test Run real Chromium offline smoke tests (Playwright required).' \
	  'make offline-fixture     Create tiny synthetic site at dist/offline-fixture/nhe-enga.'

apk:
	./android/gradlew :app:assembleDebug

apk-release:
	./android/gradlew :app:assembleRelease
	python3 scripts/stage_android.py --package

offline-manifest:
	python3 scripts/build_offline.py "$(PAGES_BUILD_DIR)" --prepare

offline-test:
	python3 -m unittest discover -s tests/offline -p 'test_*.py' -v
	node tests/offline/service_worker_smoke.cjs

offline-native-test:
	bash scripts/test_offline_native.sh

offline-browser-test:
	python3 tests/offline/browser_smoke.py

offline-fixture:
	python3 tests/offline/fixture.py dist/offline-fixture/nhe-enga
