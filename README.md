# ll · 技能库

按技能独立目录组织的个人技能库。每个技能包含自己的 `SKILL.md`、参考资料、脚本和必要素材，后续新技能继续添加到 `skills/` 下。

| 技能 | 用途 |
| --- | --- |
| [吴院公众号排版](skills/wjx-wechat-layout/SKILL.md) | 按栏目将 Word / Markdown / 图文稿转换为供 Z0 导入公众号后台的 HTML |

## 吴院公众号排版

- 10 个栏目分类、5 种基础视觉样式及可选科创分区版。
- 19 项用户提供的品牌与账号素材组件（含宣传部成稿页尾名片）。
- 保留正文、图片、图注、姓名加粗和原稿署名。
- 输出正文 HTML、手机预览、配图、结构稿和发布信息。
- 以 100 篇吴院官号原文和宣传培训材料作为参考。

首个科创速递实稿的本地排版效果已获用户认可；Z0 导入与公众号保存预览尚未实测。仓库不包含该测试 Word、完整文章网页或个人工作目录。

### 使用

将 `skills/wjx-wechat-layout` 安装到使用者的技能目录，或让支持技能的助手读取该目录下的 `SKILL.md`。

Python 依赖：

```sh
python -m pip install -r skills/wjx-wechat-layout/requirements.txt
```

示例请求：

> 使用吴院公众号排版技能，将这份 Word 按科创速递栏目排版，保留原文与图片，输出 HTML 和预览。

可独立运行的转换脚本：

```sh
python skills/wjx-wechat-layout/scripts/wechat_layout.py extract input.docx --out work/article.json
# 按技能说明复核栏目、结构与原文后，再生成输出
python skills/wjx-wechat-layout/scripts/wechat_layout.py render work/article.json --out output
```

图片须由 Z0 接收/上传，或映射为微信素材地址。本技能不自动登录、上传、写草稿或发布。

## 添加其他技能

```text
skills/
  wjx-wechat-layout/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
  another-skill/
    SKILL.md
```

每个技能放入独立子目录，并在上方索引登记。这里采用单仓库目录结构，不使用 Git submodule。
