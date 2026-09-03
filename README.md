# 🪐 NexusPulse: 自主科技情报中枢与混合检索平台
> **工业级技术定位**：面向全网技术趋势的自主情报系统 —— 结合 LangGraph 多智能体批判反思审查、pgvector 时效混合检索、Obsidian 双链图谱与赛博双人对抗播客多模态分发。

---

## 🎯 核心架构亮点 (Core Pillars)

1. **破局传统 RAG 缺陷（Garbage In, Garbage Out）**：
   - 数据摄取入库前强制经过 **LangGraph 多智能体审查流水线** (`TriageAgent` 初筛量化 $\to$ `ScoutAgent` 探针深度溯源 $\to$ `SynthesisAgent` 结构化撰写 $\to$ `CriticAgent` 对抗辩证审核)。
   - 过滤炒作噱头与营销软文，未达标触发条件回退重写（上限 3 次），仅沉淀高信噪比技术研报。

2. **带牛顿冷却时间衰减的时效混合检索**：
   - 结合稠密向量（`pgvector` HNSW）与稀疏全文检索（`pg_trgm` / BM25），引入牛顿冷却指数时间衰减算法：
   $$\text{HybridScore} = \left( \alpha \cdot \text{DenseScore} + (1-\alpha) \cdot \text{SparseScore} \right) \times e^{-\lambda \cdot \Delta t}$$
   - 实现技术情报“越新越准、经典保留”。

3. **生产级 FastMCP Server (Cursor / Claude Code 直连)**：
   - 遵循 Model Context Protocol 标准协议，向本地 IDE 暴露知识调阅工具端点 `search_tech_intel`。

4. **多模态赛博双人对抗播客 (RSS-to-Podcast)**：
   - 基于认知冲突 Prompt 编排双人对话剧本（Host A 科技探究者 vs Host B 毒舌架构师）。
   - 通过 `edge-tts` 进行异步并发分轨配音与混音输出标准 MP3 音频。

5. **Obsidian 自动化知识图谱双链沉淀**：
   - 自动提取技术实体，生成带 YAML Frontmatter 与 `[[Wikilink]]` 双向链接的标准 Markdown 研报。

---

## 📂 工程目录结构

```
nexuspulse/
├── nexuspulse/
│   ├── ingestion/       # 数据摄取与 SHA256 指纹去重
│   ├── agents/          # LangGraph 状态机与 Critic Loop 回环
│   ├── rag/             # 语义分块、时间衰减与混合检索
│   ├── exporters/       # Obsidian 双链 Markdown 自动生成
│   ├── distribution/    # FastMCP Server 与 Edge-TTS 播客管线
│   ├── config.py        # Pydantic Settings 配置
│   └── cli.py           # 原型演示一键启动器
├── tests/               # 自动化单元测试套件
├── pyproject.toml       # 依赖与打包规范
└── README.md
```

---

## 🚀 快速开始与演示

### 1. 激活运行环境
```bash
conda activate gemini
```

### 2. 运行端到端原型 Demo
```bash
python -m nexuspulse.cli
```
演示流程包含：
- 增量摄取技术流并识别过滤重复条目
- TriageAgent 识别并拦截低质营销软文
- LangGraph 驱动 Scout 与 Synthesis 产出研报初稿
- CriticAgent 对抗审查驳回初稿并要求修正落地隐患，第 2 轮修正通过
- 语义分块入库并演示带有牛顿冷却衰减的混合检索
- 自动生成 Obsidian 双链笔记至 `/Users/pluto/MyNotes/Projects/NexusPulse/`
- Edge-TTS 异步分轨合成双角色对抗播客 MP3 音频

### 3. 运行自动化测试
```bash
pytest tests/ -v
```

### 4. 启动 FastMCP 服务
```bash
python -m nexuspulse.distribution.mcp_server
```
