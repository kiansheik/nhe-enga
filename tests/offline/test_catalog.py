import base64
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from fixture import build_offline as b, fixture


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.build = Path(self.tmp.name) / "site"
        self.catalog = fixture(self.build)

    def manifests(self, catalog):
        return {
            p["id"]: json.loads((self.build / p["url"]).read_bytes())
            for p in catalog["packs"]
        }

    def test_content_matches_final_bytes(self):
        for p in self.catalog["packs"]:
            data = (self.build / p["url"]).read_bytes()
            self.assertEqual(p["sha256"], b.digest(data))
            self.assertEqual(p["bytes"], len(data))
            files = json.loads(data)["files"]
            self.assertEqual(p["downloadBytes"], sum(f["bytes"] for f in files))
            for f in files:
                self.assertEqual(f["sha256"], b.file_hash(self.build / f["path"]))

    def test_make_discovers_local_signing_key_without_shell_configuration(self):
        home = Path(self.tmp.name) / "home"
        signing_dir = home / ".config/nhe-enga"
        signing_dir.mkdir(parents=True)
        key = signing_dir / "content-private.pem"
        key.touch()
        environment = os.environ.copy()
        for name in ("OFFLINE_SIGNING_KEY", "NHE_SIGNING_DIR"):
            environment.pop(name, None)
        environment["HOME"] = str(home)

        def configured_key(**overrides):
            result = subprocess.run(
                [
                    "make",
                    "--no-print-directory",
                    "-s",
                    "-f",
                    "Makefile",
                    "-f",
                    "-",
                    "print-signing-key",
                ],
                input='print-signing-key:\n\t@printf "%s" "$$OFFLINE_SIGNING_KEY"\n',
                cwd=b.ROOT,
                env={**environment, **overrides},
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout

        self.assertEqual(configured_key(), str(key))
        self.assertEqual(
            configured_key(OFFLINE_SIGNING_KEY="/explicit/content.pem"),
            "/explicit/content.pem",
        )
        custom = home / "custom-signing"
        custom.mkdir()
        (custom / "content-private.pem").touch()
        self.assertEqual(
            configured_key(NHE_SIGNING_DIR=str(custom)),
            str(custom / "content-private.pem"),
        )
        key.unlink()
        self.assertEqual(configured_key(), "")

    def test_direct_image_optimization_preserves_sources_and_output_bytes(self):
        spec = importlib.util.spec_from_file_location(
            "optimize_pages_images", b.ROOT / "scripts/optimize_pages_images.py"
        )
        optimizer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(optimizer)
        root = Path(self.tmp.name)
        source = root / "source.png"
        optimizer.Image.new("RGBA", (32, 48), (80, 120, 160, 128)).save(source)
        original = source.read_bytes()
        copied = root / "copied.png"
        shutil.copyfile(source, copied)
        legacy, _, _ = optimizer.optimize_image(copied, (16, 24), 82)
        destination = root / "artifact/vlb/scan.jpg"
        output, _, _ = optimizer.optimize_image(source, (16, 24), 82, destination)
        self.assertEqual(output, destination)
        self.assertEqual(output.read_bytes(), legacy.read_bytes())
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(source.with_suffix(".jpg").exists())

    def test_deterministic_and_delta(self):
        old = {p["id"]: p["sha256"] for p in self.catalog["packs"]}
        self.assertEqual(self.catalog, b.generate(self.build, 1))
        (self.build / "docs/primary_sources/vlb/1.png").write_bytes(
            b"new optimized scan"
        )
        new = {p["id"]: p["sha256"] for p in b.generate(self.build, 2)["packs"]}
        self.assertNotEqual(old["source-vlb"], new["source-vlb"])
        self.assertEqual(old["core"], new["core"])
        self.assertEqual(old["source-lerhist"], new["source-lerhist"])

    def test_no_sources_or_apk_in_core(self):
        (self.build / "downloads").mkdir()
        (self.build / "downloads/app.apk").write_bytes(b"not site content")
        catalog = b.generate(self.build, 2)
        files = self.manifests(catalog)
        self.assertFalse(
            any(f["path"].endswith((".png", ".apk")) for f in files["core"]["files"])
        )
        self.assertFalse(
            any(f["path"].endswith(".apk") for p in files.values() for f in p["files"])
        )

    def test_new_source_pack_names_and_provenance_routing(self):
        sources = {
            "anchteatro1954": ("Anchieta — Teatro p. 176 (cotejo Martins 1954)", [683]),
            "castilho1937": ("Castilho — Nomes (1937, páginas citadas)", [27, 28]),
            "figueira1878": ("Figueira — Arte (fac-símile de 1878)", [0, 1]),
        }
        for book, (_title, images) in sources.items():
            directory = self.build / "docs/primary_sources" / book
            directory.mkdir(parents=True)
            (directory / "source.json").write_text("{}")
            for image in images:
                (directory / f"{image}.jpg").write_bytes(b"synthetic scan")

        catalog = b.generate(self.build, 2)
        entries = {pack["id"]: pack for pack in catalog["packs"]}
        manifests = self.manifests(catalog)
        core_paths = {item["path"] for item in manifests["core"]["files"]}
        for book, (title, images) in sources.items():
            identifier = f"source-{book}"
            self.assertEqual(entries[identifier]["title"], title)
            self.assertEqual(entries[identifier]["count"], len(images))
            self.assertIn(f"docs/primary_sources/{book}/source.json", core_paths)
            self.assertEqual(
                {item["path"] for item in manifests[identifier]["files"]},
                {f"docs/primary_sources/{book}/{image}.jpg" for image in images},
            )

    def test_gzip_is_not_http_content_encoding(self):
        f = next(
            f
            for f in self.manifests(self.catalog)["core"]["files"]
            if f["path"].endswith(".gz")
        )
        self.assertEqual(f["mime"], "application/gzip")
        self.assertNotIn("encoding", f)

    def test_paths_and_missing_assets(self):
        for path in (
            "../a",
            "/a",
            "a/../b",
            "a//b",
            "a%2fb",
            "a?b",
            "a\\b",
            "a/./b",
            "",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                b.safe_path(path)
        (self.build / "js/pako.min.js").unlink()
        with self.assertRaises(ValueError):
            b.generate(self.build, 2)

    def test_symlink_rejected(self):
        (self.build / "outside").symlink_to(self.build / "index.html")
        with self.assertRaises(ValueError):
            b.generate(self.build, 2)

    def test_worker_scope_and_runtime_rewrite(self):
        self.assertTrue((self.build / "sw.js").is_file())
        self.assertIn("offline/register.js", (self.build / "index.html").read_text())
        p = self.build / "mbya/index.html"
        p.write_text(
            '<head><script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.0.3/pako.min.js"></script></head>'
        )
        b.prepare(self.build)
        self.assertNotIn("cdnjs.cloudflare", p.read_text())
        self.assertIn("/nhe-enga/js/pako.min.js", p.read_text())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL required")
    def test_signed_exact_bytes_and_tampering(self):
        root = Path(self.tmp.name)
        key = root / "private.pem"
        public = root / "public.pem"
        subprocess.run(
            [
                "openssl",
                "genpkey",
                "-algorithm",
                "RSA",
                "-pkeyopt",
                "rsa_keygen_bits:2048",
                "-out",
                str(key),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(public)],
            check=True,
            capture_output=True,
        )
        b.generate(self.build, 3, str(key))
        envelope = json.loads((self.build / "offline/catalog.json").read_bytes())
        payload = root / "payload"
        signature = root / "sig"
        payload.write_bytes(base64.b64decode(envelope["payload"]))
        signature.write_bytes(base64.b64decode(envelope["signature"]))
        args = [
            "openssl",
            "dgst",
            "-sha256",
            "-verify",
            str(public),
            "-signature",
            str(signature),
            str(payload),
        ]
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
        payload.write_bytes(payload.read_bytes() + b" ")
        self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
