# Cold-path Memory Invariant — Parquet Streaming

Story: MCT-163 (Phase 2)
Domain: parquet-streaming
Author: DomainAgent (MCT-163 Phase 0 context)
Date: 2026-05-14

## 개요

mctrader-data cold tier (L2/L3 compactor + DualWriter NAS upload) 의 메모리 invariant 패턴.

Hot path (collector WAL / L1 ParquetWriter, ADR-017 §D5) 는 별도 — 본 문서는 cold path 한정.

## Memory Invariant (INV-4)

| 컴포넌트 | 임계값 | 방식 | 결정 |
|---------|-------|------|------|
| DualWriter.write(Path) | peak RSS+TM delta ≤ 50 MB | put_streaming + upload_fileobj | MCT-163 D1=B, D3=A |
| L2Compactor.compact_hour | peak RSS+TM delta ≤ 256 MB | iter_batches(1024) + write_batch | MCT-163 D4=A, D5=A |
| L3Compactor.compact_day | peak RSS+TM delta ≤ 256 MB | iter_batches(1024) + write_batch (L2 동형) | MCT-163 D4=A, D5=A |

Delta-based 측정 (D6=C): `psutil.Process.memory_info().rss` + `tracemalloc` 동시 측정.

절대값 기준 X — 시작 직전 gc.collect() 후 delta만 측정.

## DualWriter streaming refactor (MCT-163 F3)

### Before (MCT-160 이전)

```python
# dual_writer.py write(data=Path) old path
payload = data.read_bytes()  # 전체 파일 메모리 로드 (F3 surface)
actual_sha256 = hashlib.sha256(payload).hexdigest()
nas_uploader.put(key, payload, sha256=actual_sha256)  # bytes → NAS
```

read_bytes() 2회 (sha256 + NAS body) = OOM risk (orderbookdepth 1GB 파일 시 2GB peak).

### After (MCT-163 F3)

```python
# dual_writer.py write(data=Path) new path — MCT-163 F3
# sha256 verify: open+iter (read_bytes 0)
sha256_obj = hashlib.sha256()
with data.open("rb") as fv:
    for chunk in iter(lambda: fv.read(8 * 1024 * 1024), b""):
        sha256_obj.update(chunk)
actual_sha256 = sha256_obj.hexdigest()

# local copy: shutil.copy2 streaming (read_bytes 0)
shutil.copy2(str(data), str(tmp_path))

# NAS upload: put_streaming → upload_fileobj (streaming, read_bytes 0)
nas_uploader.put_streaming(data, nas_key, sha256)
```

read_bytes() 0회 = 파일 크기 무관 일정 메모리 (8MB chunk 기준).

### NASUploader.put_streaming

```python
def put_streaming(self, local_path_or_fileobj, nas_key, sha256) -> PutResult:
    # D1=B: boto3 upload_fileobj + TransferConfig
    transfer_cfg = TransferConfig(
        multipart_threshold=8 * 1024 * 1024,  # 8 MB
        multipart_chunksize=8 * 1024 * 1024,  # 8 MB per part
        max_concurrency=1,                     # sequential (memory 최소화)
        use_threads=False,
    )
    with local_path_or_fileobj.open("rb") as fobj:
        client.upload_fileobj(fobj, bucket, nas_key,
                              ExtraArgs={"Metadata": {"sha256": sha256}},
                              Config=transfer_cfg)
```

기존 `put(key, data=bytes)` signature 보존 (INV-2 backward compat, retry_queue drain 정합).

## L2/L3 iter_batches streaming (MCT-163 F6)

### Before (MCT-160 이전)

```python
# l2.py / l3.py old path
for f in l1_files:
    tbl = pq.ParquetFile(str(f)).read()  # 파일 전체 로드 (F6 surface)
    writer.write_table(tbl)
```

orderbookdepth 1 GiB+ L1 파일 → OOM.

### After (MCT-163 F6)

```python
# l2.py / l3.py new path
for f in l1_files:
    pf = pq.ParquetFile(str(f))
    for batch in pf.iter_batches(batch_size=1024):  # D4=A
        # monotonic verify per batch
        ...
        writer.write_batch(batch)  # D5=A true streaming
```

per-batch 메모리: 1024 rows × ~600 bytes raw_json ≈ 600 KB (파일 크기 무관 일정).

batch_size=1024: OLAP standard (MCT-160 D3 정합, row_group_size=100,000과 별개).

### Schema 정합 (INV-5)

`iter_batches` → `write_batch` 는 batch 단위 write로 schema 유지.
`write_table` 대비 row_group 경계가 달라질 수 있으나 schema 필드는 동일.
`pq.ParquetWriter(schema=...)` 첫 파일에서 추출한 schema 고정 → INV-5 보장.

## sha256 SSOT (INV-3, D2=A)

- caller 가 단일 sha256 계산 후 DualWriter.write(sha256=...) 주입
- DualWriter → NASUploader.put_streaming(sha256=sha256) 전달
- NAS Metadata={"sha256": sha256} 저장 → HEAD 200 시 idempotency check
- multipart ETag ≠ sha256: ETag = parts hash (S3 multipart semantics), sha256 = content hash (별도)
- INV-3: sha256 SSOT = caller-side single computation (MCT-160 D6 R-EXTRA 정합)

## 측정 결과 (MCT-163 Phase 2.4, 2026-05-14)

| Target | 페이로드 | RSS delta | TM delta | PASS |
|--------|---------|-----------|----------|------|
| DualWriter (F3) | 105 MiB parquet | 0.2 MB | 0.0 MB | PASS |
| L2Compactor (F6) | 300k rows (~180 MB) | 0.0 MB | 0.3 MB | PASS |
| L3Compactor (F6) | 300k rows (~180 MB) | 0.0 MB | 0.3 MB | PASS |

## 관련 ADR

- ADR-017 §D5: Hot path 무영향 (collector WAL / L1 ParquetWriter latency 0)
- ADR-027 §D6: 7종 invariant per-file (sha256 ≠ multipart ETag)
- ADR-027 §D5: NAS unreachable 시 retry_queue fallback (hot path 차단 0)
- ADR-009 §D2.7: impl narrower (raw_json only nullable=True — MCT-163 F7)

## Cross-ref

- MCT-163 §4 AC-1/AC-3/INV-3/INV-4/INV-5
- MCT-160 F3+F6+F7 carry surface (origin)
- mctrader-data CLAUDE.md §streaming refactor
- `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` — MCT-189 LAND wiring invariant (DualWriter self-delete가 본 페이지 INV-3 sha256 SSOT — caller-side single computation, multipart ETag ≠ sha256 — 를 4중 HEAD verify primitive로 활용)
