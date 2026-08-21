# 黄油脆丝棒 Skill 与知识库 QA 更新

本仓库保存 2026-08-21 达尔顿黄油脆丝棒短视频改款工作流的 Skill、产品知识库、纠错记忆、QA 审计脚本和回归证据。

## 本次修复

- `PRODUCT_CROSS_SECTION_ROUNDED`：阻断产品端面/棒体圆柱化。
- `PRODUCT_THICKNESS_COLLAPSED`：阻断产品 Z 轴厚度塌缩。
- `PACKAGE_PRINT_IDENTITY_MISMATCH`：阻断品牌、品名、字形和包装版式漂移。
- `PACKAGE_SCALE_MISMATCH`：阻断同规格外盒尺寸不一致。
- `PACKAGE_DEPTH_COLLAPSED`：阻断 15 × 15 × 4.5 cm 外盒纸片化。

## 目录

- `skills/director-skill/`：导演工作流入口、逐对象 QA 规范、审计脚本和产品配置。
- `skills/extract-skill/`：黄油脆丝棒产品知识规范更新。
- `knowledge-base/butter-crisp-stick/`：通用产品规范、知识索引和纠错记忆。
- `docs/`：回归测试结果。

## 验证

- 新增 QA 回归测试：6/6 通过。
- `director-skill` 和 `extract-skill` 的 `quick_validate.py` 均通过。
- `director-skill/scripts/self_test.py` 通过。
- 圆柱化、产品薄片化、生成式包装文字和盒厚塌缩四类回归用例均被正确阻断。

## 素材边界

本仓库是公开仓库，因此不包含人物图片、产品照片、包装照片、视频或其他用户素材。配置中的参考资产路径使用仓库相对路径；实际运行前需把已获授权的参考素材放入对应本地资产目录。

详细规则见 [`skills/director-skill/references/butter-crisp-stick-pixel-qa.md`](skills/director-skill/references/butter-crisp-stick-pixel-qa.md)。
