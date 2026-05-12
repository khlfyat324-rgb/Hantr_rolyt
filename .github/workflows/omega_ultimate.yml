name: Omega UltimateX 24/7

on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install telethon
      - name: بدء المحرك
        env:
          API_ID_1: ${{ secrets.API_ID_1 }}
          API_HASH_1: ${{ secrets.API_HASH_1 }}
          SESSION_1: ${{ secrets.SESSION_1 }}
          API_ID_2: ${{ secrets.API_ID_2 }}
          API_HASH_2: ${{ secrets.API_HASH_2 }}
          SESSION_2: ${{ secrets.SESSION_2 }}
          ADMIN_ID: ${{ secrets.ADMIN_ID }}
        run: python omega_ultimate.py
