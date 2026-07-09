/**
 * aios_audit —— 审计日志库。
 *
 * 设计原则（参见 02-design-doc.md §6 + TASK-060）：
 *  - append-only：DB 层有触发器禁 UPDATE/DELETE（migration 0002）
 *  - hash 链：每条记录包含前一记录的 hash，防篡改
 *  - 写入异步、不阻塞主链路
 */

import { createHash } from 'node:crypto';

export interface AuditEntry {
  ts: string; // ISO 8601
  actor: string;
  action: string;
  datasource_id?: string | null;
  standard_ref?: string | null;
  flow_id?: string | null;
  run_id?: string | null;
  payload: Record<string, unknown>;
}

export interface AuditRow extends AuditEntry {
  /** 64 字符 sha256：包含 prev_hash + 本条内容 */
  hash_chain: string;
}

/** 计算一条审计记录的 hash。 */
export function computeHash(prevHash: string, entry: AuditEntry): string {
  const h = createHash('sha256');
  h.update(prevHash);
  h.update(entry.ts);
  h.update(entry.actor);
  h.update(entry.action);
  h.update(entry.datasource_id ?? '');
  h.update(entry.standard_ref ?? '');
  h.update(entry.flow_id ?? '');
  h.update(entry.run_id ?? '');
  h.update(JSON.stringify(entry.payload));
  return h.digest('hex');
}

/** 给一组记录加上 hash 链（按 ts 排序）。 */
export function chainHashes(entries: AuditEntry[], genesis = '0'.repeat(64)): AuditRow[] {
  let prev = genesis;
  return entries.map((e) => {
    const hash_chain = computeHash(prev, e);
    prev = hash_chain;
    return { ...e, hash_chain };
  });
}

/** 校验一组记录的 hash 链是否完好。 */
export function verifyChain(rows: AuditRow[], genesis = '0'.repeat(64)): {
  valid: boolean;
  broken_at: number | null;
} {
  let prev = genesis;
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (!row) continue;
    const expected = computeHash(prev, {
      ts: row.ts,
      actor: row.actor,
      action: row.action,
      datasource_id: row.datasource_id,
      standard_ref: row.standard_ref,
      flow_id: row.flow_id,
      run_id: row.run_id,
      payload: row.payload,
    });
    if (expected !== row.hash_chain) {
      return { valid: false, broken_at: i };
    }
    prev = row.hash_chain;
  }
  return { valid: true, broken_at: null };
}

export function _internal_for_tests() {
  return { genesis: '0'.repeat(64) };
}