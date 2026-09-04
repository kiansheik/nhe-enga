#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PAGES_BUILD_DIR:-$ROOT_DIR/.pages-build}"
GRAMMAR_DIST="$ROOT_DIR/gramatica/docs/src/.vuepress/dist"

require_path() {
  local path="$1"
  if [[ ! -e "$ROOT_DIR/$path" ]]; then
    echo "Missing required Pages asset: $path" >&2
    exit 1
  fi
}

copy_path() {
  local path="$1"
  require_path "$path"
  mkdir -p "$(dirname "$BUILD_DIR/$path")"
  cp -R "$ROOT_DIR/$path" "$BUILD_DIR/$path"
}

copy_optional_path() {
  local path="$1"
  if [[ -e "$ROOT_DIR/$path" ]]; then
    mkdir -p "$(dirname "$BUILD_DIR/$path")"
    cp -R "$ROOT_DIR/$path" "$BUILD_DIR/$path"
  fi
}

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

for path in \
  index.html \
  sentence-builder.html \
  full.html \
  orthography_mapper_live_csv_learner_mvp.html \
  styles.css \
  manifest.json \
  favicon.ico \
  icon.png \
  pyodide.min.js \
  neologisms.csv \
  js \
  quiz \
  katu \
  mbya \
  neologisms \
  imgs \
  pronunciation
do
  copy_path "$path"
done

copy_path "translate/index.html"

for path in \
  docs/README.md \
  docs/all_nouns_verbs.json \
  docs/baby-names.csv \
  docs/citations.json \
  docs/dict-conjugated.json \
  docs/dict-conjugated.json.gz \
  docs/dooley_2006_mbya_dic.json \
  docs/dooley_2006_mbya_dic.json.gz \
  docs/extracted_entries_nheengatu.json \
  docs/extracted_entries_nheengatu.tar.gz \
  docs/tupi_dict_navarro.js \
  docs/tupi_dict_navarro.json \
  docs/primary_sources/index.html \
  docs/primary_sources/ancharte \
  docs/primary_sources/arcat1618 \
  docs/primary_sources/betcomp \
  docs/primary_sources/bettvulg \
  docs/primary_sources/cartas_portiguara \
  docs/primary_sources/lerhist \
  docs/primary_sources/vlb
do
  copy_path "$path"
done

for path in \
  docs/primary_sources/*.css \
  docs/primary_sources/*.js \
  docs/primary_sources/*.json
do
  copy_optional_path "$path"
done

make -C "$ROOT_DIR" grammar-build
mkdir -p "$BUILD_DIR/gramatica"
cp -R "$GRAMMAR_DIST/." "$BUILD_DIR/gramatica/"
rm -rf "$GRAMMAR_DIST"

touch "$BUILD_DIR/.nojekyll"
if [[ -n "${SITE_CNAME:-kiansheik.io}" ]]; then
  printf '%s\n' "${SITE_CNAME:-kiansheik.io}" > "$BUILD_DIR/CNAME"
fi

echo "Built GitHub Pages artifact at $BUILD_DIR"
