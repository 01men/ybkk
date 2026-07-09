import { describe, it, expect } from 'vitest';
import { chainHashes, verifyChain, computeHash } from '../src';

const baseEntry = {
  ts: '2026-07-08T10:00:00.000Z',
  actor: 'admin',
  action: 'datasource.create',
  datasource_id: 'ds-001',
  payload: { foo: 'bar' },
};

describe('chainHashes + verifyChain', () => {
  it('produces deterministic hash chain', () => {
    const rows = chainHashes([baseEntry, { ...baseEntry, ts: '2026-07-08T10:01:00.000Z', action: 'flow.run' }]);
    expect(rows[0]!.hash_chain).toHaveLength(64);
    expect(rows[1]!.hash_chain).toHaveLength(64);
    // 不同 entry → 不同 hash
    expect(rows[0]!.hash_chain).not.toBe(rows[1]!.hash_chain);
  });

  it('chains include prev hash', () => {
    const rows = chainHashes([baseEntry]);
    const expected = computeHash('0'.repeat(64), baseEntry);
    expect(rows[0]!.hash_chain).toBe(expected);
  });

  it('verifyChain returns valid for intact chain', () => {
    const rows = chainHashes([baseEntry, { ...baseEntry, action: 'flow.run' }]);
    const result = verifyChain(rows);
    expect(result.valid).toBe(true);
    expect(result.broken_at).toBe(null);
  });

  it('verifyChain detects tampered entry', () => {
    const rows = chainHashes([baseEntry, { ...baseEntry, action: 'flow.run' }]);
    // 篡改第二条的 payload
    rows[1]!.payload = { foo: 'TAMPERED' };
    const result = verifyChain(rows);
    expect(result.valid).toBe(false);
    expect(result.broken_at).toBe(1);
  });

  it('verifyChain detects swapped order', () => {
    const e1 = { ...baseEntry, ts: '2026-07-08T10:00:00.000Z' };
    const e2 = { ...baseEntry, ts: '2026-07-08T10:01:00.000Z' };
    const rows = chainHashes([e1, e2]);
    // 交换顺序
    const swapped = [rows[1]!, rows[0]!];
    const result = verifyChain(swapped);
    expect(result.valid).toBe(false);
  });

  it('empty chain is valid', () => {
    const result = verifyChain([]);
    expect(result.valid).toBe(true);
  });
});

describe('hash determinism', () => {
  it('same inputs produce same hash', () => {
    const h1 = computeHash('prev', baseEntry);
    const h2 = computeHash('prev', baseEntry);
    expect(h1).toBe(h2);
  });

  it('different prev produces different hash', () => {
    const h1 = computeHash('prev1', baseEntry);
    const h2 = computeHash('prev2', baseEntry);
    expect(h1).not.toBe(h2);
  });

  it('different payload produces different hash', () => {
    const h1 = computeHash('prev', baseEntry);
    const h2 = computeHash('prev', { ...baseEntry, payload: { foo: 'different' } });
    expect(h1).not.toBe(h2);
  });
});