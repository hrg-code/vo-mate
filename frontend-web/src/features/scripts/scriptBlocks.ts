import type { ScriptBlock, ScriptBlockRole } from "../../types";

export const scriptBlockRoleOptions: Array<{ role: ScriptBlockRole; label: string; visualHint: string }> = [
  { role: "hook", label: "开头钩子", visualHint: "正面半身，第一句直接看镜头。" },
  { role: "pain", label: "痛点共鸣", visualHint: "切到评论/搜索词截图或表情特写。" },
  { role: "point", label: "核心观点", visualHint: "稳定口播，屏幕打出核心判断。" },
  { role: "proof", label: "案例/证据", visualHint: "补充历史案例、数据截图或经历画面。" },
  { role: "method", label: "方法论", visualHint: "用 2-3 个字幕条拆步骤。" },
  { role: "turn", label: "反转冲突", visualHint: "语速放慢，强调反常识判断。" },
  { role: "summary", label: "总结", visualHint: "回到正面口播，压缩成一句话。" },
  { role: "cta", label: "互动引导", visualHint: "看镜头，给出评论或下一条承诺。" }
];

const roleLabels = Object.fromEntries(scriptBlockRoleOptions.map((item) => [item.role, item.label])) as Record<ScriptBlockRole, string>;
const roleVisualHints = Object.fromEntries(scriptBlockRoleOptions.map((item) => [item.role, item.visualHint])) as Record<ScriptBlockRole, string>;
const fallbackRoles: ScriptBlockRole[] = ["hook", "point", "turn", "cta", "pain", "proof", "method", "summary"];

export function createScriptBlock(role: ScriptBlockRole, overrides: Partial<ScriptBlock> = {}): ScriptBlock {
  return {
    id: overrides.id ?? createBlockId(role),
    role,
    label: overrides.label ?? roleLabels[role],
    voiceover: overrides.voiceover ?? "",
    visualHint: overrides.visualHint ?? roleVisualHints[role],
    durationSeconds: overrides.durationSeconds,
    ...overrides
  };
}

export function createTemplateScriptBlocks(topic: string, durationSeconds = 60): ScriptBlock[] {
  const durations = splitDuration(durationSeconds, 4);
  return [
    createScriptBlock("hook", {
      voiceover: `如果你正在关注${topic}，先抓住这个关键判断。`,
      durationSeconds: durations[0]
    }),
    createScriptBlock("point", {
      voiceover: "问题不是信息不够，而是缺少一条能执行的路径。先拆清现状，再给出具体动作。",
      durationSeconds: durations[1]
    }),
    createScriptBlock("method", {
      voiceover: "第一步看清自己现在卡在哪个位置，第二步把经验整理成可迁移能力，第三步用一个小项目验证转向。",
      durationSeconds: durations[2]
    }),
    createScriptBlock("cta", {
      voiceover: "如果你想看下一步怎么做，我下一条继续拆。",
      durationSeconds: durations[3]
    })
  ];
}

export function normalizeScriptBlocks(blocks: ScriptBlock[] | undefined, body: string, durationSeconds?: number): ScriptBlock[] {
  if (blocks?.length) {
    return blocks.map((block) =>
      createScriptBlock(block.role, {
        ...block,
        label: block.label || roleLabels[block.role],
        visualHint: block.visualHint ?? roleVisualHints[block.role]
      })
    );
  }
  return createScriptBlocksFromBody(body, durationSeconds);
}

export function createScriptBlocksFromBody(body: string, durationSeconds?: number): ScriptBlock[] {
  const segments = body
    .trim()
    .split(/\n{2,}/)
    .map((segment) => segment.trim())
    .filter(Boolean);

  if (segments.length === 0) {
    return [createScriptBlock("hook", { durationSeconds })];
  }

  const durations = splitDuration(durationSeconds, segments.length);
  return segments.map((segment, index) => {
    const role = inferRole(segment, index);
    return createScriptBlock(role, {
      label: roleLabels[role],
      voiceover: stripSectionHeading(segment),
      visualHint: roleVisualHints[role],
      durationSeconds: durations[index]
    });
  });
}

export function composeScriptBody(blocks: ScriptBlock[]): string {
  return blocks
    .map((block) => {
      const voiceover = block.voiceover.trim();
      return voiceover ? `${block.label}：\n${voiceover}` : "";
    })
    .filter(Boolean)
    .join("\n\n");
}

export function serializeScriptBlocks(blocks: ScriptBlock[]): string {
  return JSON.stringify(
    blocks.map((block) => ({
      role: block.role,
      label: block.label,
      voiceover: block.voiceover,
      visualHint: block.visualHint ?? "",
      startSeconds: block.startSeconds ?? null,
      endSeconds: block.endSeconds ?? null,
      durationSeconds: block.durationSeconds ?? null
    }))
  );
}

function inferRole(segment: string, index: number): ScriptBlockRole {
  const heading = segment.split("\n", 1)[0];
  if (/开头|钩子|前\s*3\s*秒|hook/i.test(heading)) return "hook";
  if (/痛点|共鸣|问题/i.test(heading)) return "pain";
  if (/主体|观点|判断|核心/i.test(heading)) return "point";
  if (/案例|证据|经历|数据/i.test(heading)) return "proof";
  if (/方法|步骤|路线|路径/i.test(heading)) return "method";
  if (/转折|反转|冲突/i.test(heading)) return "turn";
  if (/总结|收束/i.test(heading)) return "summary";
  if (/结尾|CTA|互动|关注|评论/i.test(heading)) return "cta";
  return fallbackRoles[index] ?? "point";
}

function stripSectionHeading(segment: string): string {
  const lines = segment.split("\n");
  if (lines.length <= 1) return segment.replace(/^[^：:]{1,16}[：:]\s*/, "").trim();
  const firstLine = lines[0].trim();
  if (/^[^：:]{1,18}[：:]$/.test(firstLine) || /^[^：:]{1,18}[：:]\s*$/.test(firstLine)) {
    return lines.slice(1).join("\n").trim();
  }
  return segment.trim();
}

function splitDuration(durationSeconds: number | undefined, count: number): Array<number | undefined> {
  if (!durationSeconds || count <= 0) return Array.from({ length: count }, () => undefined);
  const base = Math.max(3, Math.floor(durationSeconds / count));
  const durations = Array.from({ length: count }, () => base);
  durations[count - 1] += Math.max(0, durationSeconds - base * count);
  return durations;
}

function createBlockId(role: ScriptBlockRole) {
  return `sb_${role}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
