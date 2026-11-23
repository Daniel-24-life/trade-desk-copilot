<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/cover-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="docs/cover-light.svg" />
  <img src="docs/cover-light.svg" alt="Trade Desk Copilot" width="1280" />
</picture>

# 外贸询盘工作台

把分散在多轮对话中的需求整理成可检查的回复草稿与报价卡。

[查看演示](#demo) · [English](README.md) · [![CI](https://github.com/Daniel-24-life/trade-desk-copilot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Daniel-24-life/trade-desk-copilot/actions/workflows/ci.yml) · [MIT](LICENSE) · Python 3.10+

## Demo

<img src="docs/demo.gif" alt="外贸询盘工作台" width="800" />

真实终端运行后展示独立的样例报价卡，画面已裁掉联络栏和二维码。

## 要解决的问题

询盘往往分多轮补充。复核人需要同时看到已确认需求、待补字段和为回复提供支撑的目录条目。

## 实现

- 跟踪买家需求和待补充字段。
- 检索商品目录，为回复提供依据。
- 让操作员检查草稿并导出报价卡。

## 工作流程

```mermaid
flowchart LR
    A["买家询盘"] --> B["匹配目录证据"] --> C["复核草稿"]
```

## 快速运行

```sh
python -m pip install -r requirements.txt
python run_demo.py
python run_demo.py --card
```

终端提示后输入 2 复现演示。桌面窗口可运行 `python run_demo.py --gui`。

## 测试

实测 **14 项通过**。[通过的 GitHub Actions 运行](https://github.com/Daniel-24-life/trade-desk-copilot/actions/runs/45105812783)。

```sh
python -m pytest tests -q
```

## 仓库目录

| 路径 | 内容 |
| --- | --- |
| [`app/`](app/) | PyQt5 desktop workbench |
| [`core/`](core/) | Dialogue state, retrieval and quote rendering |
| [`corpus/`](corpus/) | Catalog and company fixtures |
| [`tests/`](tests/) | Inquiry, retrieval and card checks |

延伸阅读 · [architecture_overview.svg](assets/screenshots/architecture_overview.svg)

<sub>样例询盘和商品目录为合成数据。演示报价仅用于查看生成结果。</sub>
